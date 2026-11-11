import { getAll, mutate, DEFAULT_SETTINGS } from "./lib/store.js";
import { renderDonateButtons } from "./lib/support.js";

const $ = (id) => document.getElementById(id);
const V = globalThis.ReclaimValidate;
const S = globalThis.ReclaimSites;
const G = globalThis.ReclaimGrowth;
const ID = chrome.runtime.id;
let sites = [];
let savedTimer, numTimer, clearTimers = {};

// Only allow-listed store and sibling URLs are ever opened from here.
function bindLink(a, url, allowed) {
  a.href = url;
  a.addEventListener("click", (e) => { e.preventDefault(); if (allowed(url)) chrome.tabs.create({ url }); });
}

function flashSaved() {
  const el = $("saved");
  el.classList.add("show");
  clearTimeout(savedTimer);
  savedTimer = setTimeout(() => el.classList.remove("show"), 1400);
}
async function saveSettings(patch) {
  await mutate(async () => {
    const { settings } = await getAll();
    await chrome.storage.local.set({ settings: Object.assign({}, DEFAULT_SETTINGS, settings, patch) });
  });
  flashSaved();
}
const debounce = (fn) => { clearTimeout(numTimer); numTimer = setTimeout(fn, 400); };

// ---- sites ----
async function writeSites(next) {
  sites = next;
  await mutate(() => chrome.storage.local.set({ sites: next }));
  renderSites(); flashSaved();
}
function renderSites() {
  const ul = $("sites");
  ul.textContent = "";
  if (!sites.length) { const li = document.createElement("li"); li.className = "empty"; li.textContent = "No sites. Reclaim is idle until you add one."; ul.appendChild(li); }
  for (const r of sites) {
    const li = document.createElement("li");
    const name = document.createElement("span"); name.className = "site-name"; name.textContent = S.label(r);
    li.appendChild(name);
    if (!S.isDefault(r)) { const t = document.createElement("span"); t.className = "tag"; t.textContent = "added by you"; li.appendChild(t); }
    const b = document.createElement("button");
    b.type = "button"; b.className = "secondary"; b.textContent = "Remove"; b.setAttribute("aria-label", "Remove " + S.label(r));
    b.addEventListener("click", () => removeSite(r));
    li.appendChild(b);
    ul.appendChild(li);
  }
}
async function removeSite(r) {
  const next = sites.filter((x) => S.siteKey(x) !== S.siteKey(r));
  await writeSites(next);
  // Drop the host permission of a user-added site once no rule needs that host any more.
  if (!S.coveredByDefault(r) && !next.some((x) => x.host === r.host)) {
    try { await chrome.permissions.remove({ origins: S.originPatterns(r) }); } catch (e) { /* e.g. required permission */ }
  }
}
// Must start its permission request synchronously inside the click handler (user gesture).
function addSite() {
  $("siteErr").textContent = "";
  const rule = V.parseSiteInput($("newSite").value);
  if (!rule) { $("siteErr").textContent = "Enter a site like example.com or example.com/section."; return; }
  if (sites.some((x) => S.siteKey(x) === S.siteKey(rule))) { $("siteErr").textContent = "That site is already in the list."; return; }
  const finish = async (granted) => {
    if (!granted) { $("siteErr").textContent = "Permission not granted, so Reclaim cannot run on that site."; return; }
    $("newSite").value = "";
    await writeSites(sites.concat(rule));
  };
  if (S.coveredByDefault(rule)) { finish(true); return; } // host access already granted at install
  chrome.permissions.request({ origins: S.originPatterns(rule) }).then(finish, () => finish(false));
}

// ---- numbers ----
function bindNumber(id, errId, min, max, key) {
  $(id).addEventListener("input", () => {
    const raw = $(id).value, v = Number(raw);
    const ok = raw !== "" && Number.isInteger(v) && v >= min && v <= max;
    $(id).setAttribute("aria-invalid", String(!ok));
    $(errId).textContent = ok ? "" : "Enter a whole number between " + min + " and " + max + ".";
    if (ok) debounce(() => saveSettings({ [key]: v }));
  });
}
function fillSelect(id, values, current, fmt) {
  const sel = $(id);
  for (const v of values) { const o = document.createElement("option"); o.value = String(v); o.textContent = fmt(v); sel.appendChild(o); }
  sel.value = String(current);
}
// Two-click confirmation for destructive buttons.
function armed(id, label, action) {
  const b = $(id);
  b.addEventListener("click", async () => {
    if (!b.classList.contains("armed")) {
      b.classList.add("armed"); b.textContent = "Click again to confirm";
      clearTimers[id] = setTimeout(() => { b.classList.remove("armed"); b.textContent = label; }, 5000);
      return;
    }
    clearTimeout(clearTimers[id]); b.classList.remove("armed"); b.textContent = label;
    await action();
  });
}
async function refreshIntentCount() {
  const { intentions } = await getAll();
  $("intentCount").textContent = intentions.length + " stored on this device";
}

async function init() {
  const st = await getAll();
  sites = st.sites;
  renderSites();
  $("newSite").addEventListener("keydown", (e) => { if (e.key === "Enter") addSite(); });
  $("addSite").addEventListener("click", addSite);
  $("restore").addEventListener("click", () => {
    const have = new Set(sites.map(S.siteKey));
    writeSites(sites.concat(S.DEFAULT_SITES.filter((d) => !have.has(S.siteKey(d))).map((d) => Object.assign({}, d))));
  });

  $("countdownSec").value = String(st.settings.countdownSec);
  $("avgSessionMin").value = String(st.settings.avgSessionMin);
  fillSelect("sessionMin", V.SESSION_MINUTES, st.settings.sessionMin, (v) => v + " minutes");
  fillSelect("stayMin", V.STAY_MINUTES, st.settings.stayMin, (v) => v + " minutes");
  bindNumber("countdownSec", "countdownErr", 3, 30, "countdownSec");
  bindNumber("avgSessionMin", "avgErr", 5, 120, "avgSessionMin");
  $("sessionMin").addEventListener("change", () => saveSettings({ sessionMin: Number($("sessionMin").value) }));
  $("stayMin").addEventListener("change", () => saveSettings({ stayMin: Number($("stayMin").value) }));

  await refreshIntentCount();
  armed("clearIntent", "Delete stored intentions", async () => {
    await mutate(() => chrome.storage.local.set({ intentions: [] }));
    await refreshIntentCount();
  });
  armed("resetStats", "Reset all statistics", async () => {
    await mutate(() => chrome.storage.local.set({ days: {}, totals: { reclaimedMin: 0, leaves: 0, goIns: 0, spentSec: 0 }, lastLeave: { at: 0, min: 0 } }));
    $("resetNote").textContent = "Statistics reset.";
  });

  $("thanks").hidden = !st.supporter;
  const shown = renderDonateButtons($("donate"), $("donate-note"));
  if (!shown) $("donate-note").textContent = "Donation links not configured yet";
  bindLink($("rate-link"), G.storeUrl(ID), (u) => G.isAllowedLink(u, ID));
  const ul = $("siblings");
  for (const s of G.SIBLINGS) {
    const li = document.createElement("li");
    const a = document.createElement("a"); a.textContent = s.name; a.id = "sib-" + s.name.toLowerCase().replace(/[^a-z0-9]/g, "");
    bindLink(a, s.url, (u) => G.isAllowedLink(u, ID));
    li.append(a, " — " + s.blurb);
    ul.appendChild(li);
  }
}
init();
