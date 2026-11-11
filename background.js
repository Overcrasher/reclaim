// Service worker (module). Owns every mutation of sessions / stats / intentions / supporter.
import { getAll, mutate } from "./lib/store.js";

const V = globalThis.ReclaimValidate;
const S = globalThis.ReclaimSites;
const SS = globalThis.ReclaimSessions;
const ST = globalThis.ReclaimStats;
const FAIL = { ok: false };
const CONTENT_JS = ["lib/mascot.js", "content.js"]; // keep in sync with manifest.json content_scripts[0]
const LEAVE_GAP_MS = 1500;
const lastLeaveByTab = new Map();

// Content scripts must not read or write storage: only trusted extension pages and this worker.
async function lockStorage() {
  for (const area of [chrome.storage.local, chrome.storage.session]) {
    try { await area.setAccessLevel({ accessLevel: "TRUSTED_CONTEXTS" }); }
    catch (e) { console.warn("Reclaim: setAccessLevel failed", e); }
  }
}
lockStorage();

// ---- housekeeping ----
async function purgeIntentions() {
  await mutate(async () => {
    const { intentions } = await getAll();
    const next = SS.purgeIntentions(intentions, Date.now());
    if (next.length !== intentions.length) await chrome.storage.local.set({ intentions: next });
  });
}

// Keeps the dynamically registered content scripts in line with the user-added sites.
let syncChain = Promise.resolve();
function syncScripts() {
  const p = syncChain.then(doSyncScripts);
  syncChain = p.catch(() => {});
  return p;
}
async function doSyncScripts() {
  const { sites } = await getAll();
  const want = new Map();
  for (const r of sites) {
    if (S.coveredByDefault(r)) continue; // already covered by the static content script
    let granted = false;
    try { granted = await chrome.permissions.contains({ origins: S.originPatterns(r) }); } catch (e) { /* ignore */ }
    if (granted) want.set(S.scriptId(r), { id: S.scriptId(r), matches: S.originPatterns(r) });
  }
  const have = (await chrome.scripting.getRegisteredContentScripts()).filter((s) => s.id.startsWith("site-"));
  const stale = have.filter((s) => !want.has(s.id) || JSON.stringify(s.matches) !== JSON.stringify(want.get(s.id).matches)).map((s) => s.id);
  if (stale.length) await chrome.scripting.unregisterContentScripts({ ids: stale });
  const haveIds = new Set(have.map((s) => s.id).filter((id) => !stale.includes(id)));
  const add = [...want.values()].filter((w) => !haveIds.has(w.id)).map((w) => ({
    id: w.id, matches: w.matches, js: CONTENT_JS, runAt: "document_start", allFrames: false, persistAcrossSessions: true,
  }));
  if (add.length) await chrome.scripting.registerContentScripts(add);
}

// Also on every worker wake-up (cheap, and covers browsers that skip onStartup after a crash).
setTimeout(() => purgeIntentions().catch(() => {}), 0);

function setup() {
  lockStorage();
  purgeIntentions();
  syncScripts().catch((e) => console.warn("Reclaim: script sync failed", e));
  chrome.alarms.get("purge").then((a) => { if (!a) chrome.alarms.create("purge", { delayInMinutes: 60, periodInMinutes: 24 * 60 }); });
}
chrome.runtime.onInstalled.addListener((details) => {
  setup();
  // Welcome page on a fresh install only, never on update/browser update.
  if (details && details.reason === "install") chrome.tabs.create({ url: chrome.runtime.getURL("welcome.html") });
});
chrome.runtime.onStartup.addListener(setup);

// ---- tell open tabs to re-check ----
async function broadcastRecheck(exceptTabId) {
  try {
    const { sites } = await getAll();
    const tabs = await chrome.tabs.query({});
    for (const t of tabs) {
      if (t.id == null || t.id === exceptTabId || !S.hostOnlyMatch(t.url, sites)) continue;
      chrome.tabs.sendMessage(t.id, { type: "recheck" }).catch(() => {});
    }
  } catch (e) { /* ignore */ }
}
chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== "local") return;
  if ("sites" in changes) syncScripts().catch((e) => console.warn("Reclaim: script sync failed", e));
  if ("sites" in changes || "pausedUntil" in changes || "settings" in changes) broadcastRecheck();
});
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "purge") purgeIntentions();
  else if (alarm.name.startsWith("exp:")) broadcastRecheck();
});
const setExpiry = (key, until) => chrome.alarms.create("exp:" + key, { when: until + 500 });

// ---- active-time heartbeats ----
// lastAt per tab lives in storage.session (survives worker restarts, never reaches content scripts).
async function readHb() {
  const d = await chrome.storage.session.get("hb");
  return d.hb && typeof d.hb === "object" ? d.hb : {};
}
async function creditSpent(siteKey, sec) {
  if (!(sec > 0)) return;
  await mutate(async () => {
    const st = await getAll();
    const next = SS.recordSpent({ days: st.days, totals: st.totals }, Date.now(), siteKey, sec);
    await chrome.storage.local.set({ days: next.days, totals: next.totals });
  });
}
// Credits what is owed to the given tabs (all if none) and forgets them, e.g. when focus moves away.
async function flushHb(tabIds) {
  await mutate(async () => {
    const hb = await readHb();
    const now = Date.now();
    const keep = {};
    const owed = {};
    for (const id of Object.keys(hb)) {
      if (tabIds && !tabIds.includes(Number(id))) { keep[id] = hb[id]; continue; }
      const sec = SS.heartbeatCredit(hb[id].at, now);
      if (sec > 0 && hb[id].key) owed[hb[id].key] = (owed[hb[id].key] || 0) + sec;
    }
    await chrome.storage.session.set({ hb: keep });
    const st = Object.keys(owed).length ? await getAll() : null;
    if (st) {
      let cur = { days: st.days, totals: st.totals };
      for (const k of Object.keys(owed)) cur = SS.recordSpent(cur, now, k, owed[k]);
      await chrome.storage.local.set({ days: cur.days, totals: cur.totals });
    }
  });
}
chrome.windows.onFocusChanged.addListener(() => { flushHb().catch(() => {}); });
chrome.tabs.onActivated.addListener(async (info) => {
  try {
    const others = (await chrome.tabs.query({ windowId: info.windowId })).filter((t) => t.id !== info.tabId).map((t) => t.id);
    await flushHb(others);
  } catch (e) { /* ignore */ }
});
chrome.tabs.onRemoved.addListener((id) => { lastLeaveByTab.delete(id); flushHb([id]).catch(() => {}); });

async function heartbeat(msg, ctx, rule, st) {
  const now = Date.now();
  const kind = msg.kind;
  if (kind !== "start" && kind !== "beat" && kind !== "stop") return FAIL;
  const key = S.siteKey(rule);
  const counting = st.pausedUntil > now || SS.sessionState(st.sessions[key], now) === "active";
  const tabKey = String(ctx.tab.id);
  let sec = 0;
  await mutate(async () => {
    const hb = await readHb();
    const prev = hb[tabKey];
    if (counting && (kind === "beat" || kind === "stop") && prev && prev.key === key) sec = SS.heartbeatCredit(prev.at, now);
    if (kind === "stop" || !counting) delete hb[tabKey];
    else hb[tabKey] = { at: now, key };
    await chrome.storage.session.set({ hb });
  });
  await creditSpent(key, sec);
  return { ok: true };
}

// ---- sessions ----
async function stateFor(ctx) {
  const st = await getAll();
  const now = Date.now();
  const rule = S.matchRule(ctx.tabUrl, st.sites);
  return { st, now, rule };
}

async function handleCheck(ctx) {
  const { st, now, rule } = await stateFor(ctx);
  const base = { ok: true, url: ctx.tabUrl };
  if (!rule) return Object.assign(base, { track: false, count: false });
  if (st.pausedUntil > now) return Object.assign(base, { track: false, paused: true, count: true });
  const key = S.siteKey(rule);
  const state = SS.sessionState(st.sessions[key], now);
  const w = ST.weekTotals(ST.weekBuckets(st.days, now, 0));
  return Object.assign(base, {
    track: true, count: state === "active", state: state === "none" ? "intro" : state, key,
    until: state === "none" ? 0 : st.sessions[key].until,
    countdownSec: st.settings.countdownSec, sessionMin: st.settings.sessionMin, stayMin: st.settings.stayMin,
    mascot: ST.mascotState(w.reclaimedMin, w.spentMin),
  });
}

async function goIn(msg, ctx) {
  return mutate(async () => {
    const { st, now, rule } = await stateFor(ctx);
    if (!rule || st.pausedUntil > now) return FAIL;
    const key = S.siteKey(rule);
    const cur = st.sessions[key];
    if (SS.sessionState(cur, now) === "active") return { ok: true, until: cur.until, state: "active" };
    const sess = SS.startSession(now, st.settings.sessionMin);
    const next = SS.recordGoIn({ days: st.days, totals: st.totals }, now);
    const patch = { sessions: Object.assign({}, st.sessions, { [key]: sess }), days: next.days, totals: next.totals };
    const text = V.cleanIntention(msg.intention);
    if (text) patch.intentions = st.intentions.concat({ text, site: S.label(rule), at: now }).slice(-V.MAX_INTENTIONS);
    await chrome.storage.local.set(patch);
    setExpiry(key, sess.until);
    return { ok: true, until: sess.until, state: "active" };
  });
}

async function extend(ctx) {
  return mutate(async () => {
    const { st, now, rule } = await stateFor(ctx);
    if (!rule) return FAIL;
    const key = S.siteKey(rule);
    if (SS.sessionState(st.sessions[key], now) !== "expired") return FAIL;
    const sess = SS.extendSession(st.sessions[key], now, st.settings.stayMin);
    await chrome.storage.local.set({ sessions: Object.assign({}, st.sessions, { [key]: sess }) });
    setExpiry(key, sess.until);
    return { ok: true, until: sess.until, state: "active" };
  });
}

async function leave(ctx) {
  const tabId = ctx.tab.id;
  const prev = lastLeaveByTab.get(tabId);
  const now0 = Date.now();
  if (prev && now0 - prev < LEAVE_GAP_MS) return { ok: true, counted: false };
  lastLeaveByTab.set(tabId, now0);
  const res = await mutate(async () => {
    const { st, now, rule } = await stateFor(ctx);
    if (!rule) return FAIL;
    const key = S.siteKey(rule);
    const sessions = Object.assign({}, st.sessions);
    delete sessions[key];
    const next = SS.recordLeave({ days: st.days, totals: st.totals }, now, st.settings.avgSessionMin);
    await chrome.storage.local.set({
      sessions, days: next.days, totals: next.totals, lastLeave: { at: now, min: st.settings.avgSessionMin },
    });
    chrome.alarms.clear("exp:" + key);
    return { ok: true, counted: true };
  });
  if (res.ok) {
    await flushHb([tabId]);
    chrome.tabs.update(tabId, { url: chrome.runtime.getURL("reclaimed.html") }).catch(() => {});
    broadcastRecheck(tabId);
  }
  return res;
}

// ---- messages ----
// Sender classes: "extension" (our own pages) and "content" (content scripts: sender.tab set, web url, top frame).
function classify(sender) {
  if (!sender || sender.id !== chrome.runtime.id) return null;
  if (typeof sender.url === "string" && sender.url.startsWith("chrome-extension://" + chrome.runtime.id + "/")) return { kind: "extension" };
  if (sender.tab && typeof sender.tab.url === "string" && sender.frameId === 0 && typeof sender.tab.id === "number") {
    return { kind: "content", tab: sender.tab, tabUrl: sender.tab.url };
  }
  return null;
}

async function handleContent(msg, ctx) {
  if (msg.type === "supporter") {
    // Cosmetic flag, honour system: only from the real thank-you page with a Stripe-shaped session id.
    if (!V.isThanksUrl(ctx.tabUrl) || !V.validSession(msg.sessionId)) return FAIL;
    await mutate(() => chrome.storage.local.set({ supporter: true }));
    return { ok: true };
  }
  // The site always comes from the sender's tab URL, never from the message.
  switch (msg.type) {
    case "check": return handleCheck(ctx);
    case "goIn": return goIn(msg, ctx);
    case "extend": return extend(ctx);
    case "leave": return leave(ctx);
    case "hb": {
      const { st, rule } = await stateFor(ctx);
      return rule ? heartbeat(msg, ctx, rule, st) : FAIL;
    }
    default: return FAIL;
  }
}

async function handle(msg, sender) {
  const ctx = classify(sender);
  if (!ctx || !msg || typeof msg !== "object" || typeof msg.type !== "string") return FAIL;
  return ctx.kind === "content" ? handleContent(msg, ctx) : FAIL; // extension pages use lib/store.js directly
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  handle(msg, sender).then(sendResponse).catch(() => sendResponse(FAIL));
  return true;
});
