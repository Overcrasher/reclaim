// Content script (document_start, top frame only). Shows the pause overlay on tracked sites.
// It never touches storage: every decision comes from the service worker, which derives the site
// from the sender tab URL. The overlay is a closed Shadow DOM with !important-hardened host styles.
(() => {
  "use strict";
  if (globalThis.__reclaimLoaded) return; // static + dynamic registration may both match one page
  globalThis.__reclaimLoaded = true;
  if (window.top !== window) return;

  const HB_MS = 15000;
  const POLL_MS = 1000;
  const M = globalThis.ReclaimMascot;

  const CSS = `
:host { all: initial; }
* { box-sizing: border-box; }
.scrim { position: fixed; inset: 0; display: flex; align-items: center; justify-content: center; padding: 24px;
  background: #F7F4EC; color: #2F3A33; font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  overflow: auto; }
.scrim.pending { opacity: 0; animation: reveal 0s linear 150ms forwards; }
@keyframes reveal { to { opacity: 1; } }
.scrim.soft { background: rgba(247, 244, 236, .94); backdrop-filter: blur(6px); }
.panel { width: min(440px, 100%); text-align: center; }
.mascot { display: flex; justify-content: center; margin-bottom: 6px; }
h1 { margin: 0 0 6px; font-size: 26px; line-height: 1.2; font-weight: 700; letter-spacing: -.01em; color: #2F3A33; }
.sub { margin: 0 0 16px; color: #5B685F; }
.intent { width: 100%; font: inherit; color: #2F3A33; background: #fff; border: 1.5px solid #D9D3C3; border-radius: 12px; padding: 11px 14px; text-align: center; }
.intent:focus { outline: 2px solid #4F7C5A; outline-offset: 2px; border-color: #4F7C5A; }
.count { margin: 22px auto 6px; width: 92px; height: 92px; position: relative; }
.count svg { display: block; transform: rotate(-90deg); }
.num { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 30px; font-weight: 700; color: #4F7C5A; font-variant-numeric: tabular-nums; }
.hint { margin: 0; color: #5B685F; font-size: 14px; min-height: 21px; }
.actions { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-top: 18px; }
button { font: inherit; font-weight: 600; cursor: pointer; border-radius: 12px; padding: 11px 20px; border: 1.5px solid #4F7C5A; }
.go { background: #4F7C5A; color: #fff; }
.go:hover { background: #456E4F; }
.leave { background: #fff; color: #4F7C5A; }
.leave:hover { background: #EEF4EE; }
button:focus-visible { outline: 2px solid #D9825B; outline-offset: 2px; }
.est { margin: 16px 0 0; font-size: 12.5px; color: #7A857D; }
[hidden] { display: none !important; }
@media (prefers-reduced-motion: reduce) { .scrim.pending { animation-duration: 0s; } }
`;

  let host = null, root = null, scrim = null, ui = null;
  let mode = "off";            // off | pending | intro | expired | active
  let overlayKey = "";         // key+state of the rendered overlay
  let seq = 0;                 // check sequence, stale answers are ignored
  let expiryTimer = 0, countdownTimer = 0, hbTimer = 0, mediaTimer = 0, retryTimer = 0;
  let counting = false, hbOn = false, lastUrl = location.href;
  let cfg = { countdownSec: 5, sessionMin: 10, stayMin: 5, mascot: 2 };

  function send(msg) {
    try { return chrome.runtime.sendMessage(msg).then((r) => r || null, () => null); }
    catch (e) { return Promise.resolve(null); }
  }

  // ---------- media: pause and mute while the overlay is up ----------
  const pausedByUs = new Set(), mutedByUs = new Set();
  function sweepMedia() {
    for (const m of document.querySelectorAll("video, audio")) {
      try {
        if (!m.paused) { m.pause(); pausedByUs.add(m); }
        if (!m.muted) { m.muted = true; mutedByUs.add(m); }
      } catch (e) { /* ignore */ }
    }
  }
  const onPlay = (e) => {
    const t = e.target;
    if (t && (t.tagName === "VIDEO" || t.tagName === "AUDIO")) { try { t.pause(); pausedByUs.add(t); if (!t.muted) { t.muted = true; mutedByUs.add(t); } } catch (err) { /* ignore */ } }
  };
  function mediaGuard(on) {
    if (on) {
      if (mediaTimer) return;
      sweepMedia();
      document.addEventListener("play", onPlay, true);
      mediaTimer = setInterval(sweepMedia, 250);
    } else {
      if (!mediaTimer) return;
      clearInterval(mediaTimer); mediaTimer = 0;
      document.removeEventListener("play", onPlay, true);
      for (const m of mutedByUs) { try { m.muted = false; } catch (e) { /* ignore */ } }
      for (const m of pausedByUs) { try { const p = m.play(); if (p && p.catch) p.catch(() => {}); } catch (e) { /* ignore */ } }
      mutedByUs.clear(); pausedByUs.clear();
    }
  }

  // ---------- page scroll lock (removes the page's scrollbar gutter so the overlay covers the full viewport) ----------
  let scrollSaved = null;
  function scrollLock(on) {
    const de = document.documentElement;
    if (!de) return;
    if (on && !scrollSaved) {
      scrollSaved = { v: de.style.getPropertyValue("overflow"), p: de.style.getPropertyPriority("overflow") };
      de.style.setProperty("overflow", "hidden", "important");
    } else if (!on && scrollSaved) {
      if (scrollSaved.v) de.style.setProperty("overflow", scrollSaved.v, scrollSaved.p); else de.style.removeProperty("overflow");
      scrollSaved = null;
    }
  }

  // ---------- host + overlay ----------
  const HOST_STYLE = {
    all: "initial", position: "fixed", inset: "0", width: "100vw", height: "100vh", "z-index": "2147483647", display: "block",
    visibility: "visible", opacity: "1", "pointer-events": "auto", transform: "none", margin: "0", padding: "0", border: "0",
    "max-width": "none", "max-height": "none", "min-width": "0", "min-height": "0", filter: "none", "clip-path": "none", contain: "none",
  };
  function applyHostStyle() {
    for (const k of Object.keys(HOST_STYLE)) host.style.setProperty(k, HOST_STYLE[k], "important");
  }
  const stopKeys = (e) => { e.stopPropagation(); };
  function ensureHost() {
    if (host) {
      if (!host.isConnected) (document.documentElement || document).appendChild(host);
      applyHostStyle();
      return;
    }
    host = document.createElement("div");
    host.setAttribute("data-reclaim", "");
    applyHostStyle();
    root = host.attachShadow({ mode: "closed" });
    try {
      const sheet = new CSSStyleSheet();
      sheet.replaceSync(CSS);
      root.adoptedStyleSheets = [sheet];
    } catch (e) {
      const st = document.createElement("style");
      st.textContent = CSS;
      root.appendChild(st);
    }
    // Keep scrolling and typing inside the overlay from reaching the page underneath.
    for (const t of ["wheel", "touchmove"]) host.addEventListener(t, (e) => e.preventDefault(), { passive: false });
    for (const t of ["keydown", "keyup", "keypress"]) host.addEventListener(t, stopKeys);
    (document.documentElement || document).appendChild(host);
  }
  // Keys that did not originate inside the overlay never reach the page while it is up.
  function blockPageKeys(e) {
    if (mode === "off" || !host || e.target === host) return;
    e.stopImmediatePropagation(); e.preventDefault();
  }
  for (const t of ["keydown", "keyup", "keypress"]) window.addEventListener(t, blockPageKeys, true);

  // If the page rips the host out of the document while the overlay is up, put it back.
  const guard = new MutationObserver(() => { if (mode !== "off" && host && !host.isConnected && document.documentElement) ensureHost(); });
  function watchHost() { try { guard.observe(document, { childList: true, subtree: false }); guard.observe(document.documentElement, { childList: true }); } catch (e) { /* ignore */ } }

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function clearUi() {
    clearInterval(countdownTimer); countdownTimer = 0;
    if (scrim) { scrim.remove(); scrim = null; }
    ui = null;
  }

  function showPending() {
    if (mode !== "off") return;
    ensureHost(); clearUi();
    scrim = el("div", "scrim pending");
    root.appendChild(scrim);
    mode = "pending"; overlayKey = "";
    scrollLock(true); mediaGuard(true);
  }

  function ring(sec) {
    const NS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", "0 0 92 92"); svg.setAttribute("width", "92"); svg.setAttribute("height", "92"); svg.setAttribute("aria-hidden", "true");
    const mk = (stroke) => {
      const c = document.createElementNS(NS, "circle");
      c.setAttribute("cx", "46"); c.setAttribute("cy", "46"); c.setAttribute("r", "40"); c.setAttribute("fill", "none");
      c.setAttribute("stroke", stroke); c.setAttribute("stroke-width", "7"); c.setAttribute("stroke-linecap", "round");
      svg.appendChild(c); return c;
    };
    mk("#E3DECF");
    const arc = mk("#7FB685");
    const len = 2 * Math.PI * 40;
    arc.setAttribute("stroke-dasharray", String(len));
    arc.setAttribute("stroke-dashoffset", "0");
    return { svg, set(frac) { arc.setAttribute("stroke-dashoffset", String(len * (1 - frac))); } };
  }

  function buildPanel(kind) {
    const panel = el("div", "panel");
    panel.setAttribute("role", "dialog"); panel.setAttribute("aria-modal", "true");
    const mascot = el("div", "mascot");
    if (M) mascot.appendChild(M.draw(document, cfg.mascot, 96));
    panel.appendChild(mascot);
    const h = el("h1", "", kind === "intro" ? "What are you here for?" : "Your " + cfg.sessionMin + " minutes are up.");
    h.id = "t"; panel.setAttribute("aria-labelledby", "t");
    panel.appendChild(h);
    return panel;
  }

  function showOverlay(kind) {
    const key = kind + "|" + cfg.sessionMin + "|" + cfg.countdownSec;
    if (mode === kind && overlayKey === key && scrim && host && host.isConnected) return;
    ensureHost(); clearUi();
    mode = kind; overlayKey = key;
    scrim = el("div", "scrim" + (kind === "expired" ? " soft" : ""));
    const panel = buildPanel(kind);
    ui = {};
    if (kind === "intro") {
      panel.appendChild(el("p", "sub", "Optional: name the one thing you came to do."));
      const input = el("input", "intent");
      input.type = "text"; input.maxLength = 140; input.placeholder = "e.g. reply to one message";
      input.setAttribute("aria-label", "What are you here for? (optional)");
      input.autocomplete = "off"; input.spellcheck = false;
      ui.input = input;
      panel.appendChild(input);
      const c = el("div", "count");
      const r = ring(cfg.countdownSec);
      c.appendChild(r.svg);
      ui.num = el("div", "num", String(cfg.countdownSec));
      c.appendChild(ui.num);
      panel.appendChild(c);
      ui.hint = el("p", "hint", "Take a breath. Your choices appear in a moment.");
      panel.appendChild(ui.hint);
      ui.actions = el("div", "actions");
      ui.actions.hidden = true;
      ui.go = el("button", "go", "Go in (" + cfg.sessionMin + " min)"); ui.go.type = "button";
      ui.leave = el("button", "leave", "Leave"); ui.leave.type = "button";
      ui.actions.append(ui.go, ui.leave);
      panel.appendChild(ui.actions);
      ui.go.addEventListener("click", onGoIn);
      ui.leave.addEventListener("click", onLeave);
      const t0 = performance.now(), total = cfg.countdownSec * 1000;
      countdownTimer = setInterval(() => {
        const left = Math.max(0, total - (performance.now() - t0));
        r.set(left / total);
        ui.num.textContent = String(Math.ceil(left / 1000));
        if (left <= 0) {
          clearInterval(countdownTimer); countdownTimer = 0;
          c.hidden = true; ui.hint.textContent = "Whenever you are ready.";
          ui.actions.hidden = false;
        }
      }, 100);
      scrim.appendChild(panel);
      root.appendChild(scrim);
      setTimeout(() => { try { input.focus({ preventScroll: true }); } catch (e) { /* ignore */ } }, 0);
    } else {
      panel.appendChild(el("p", "sub", "Take a breath, then choose."));
      const actions = el("div", "actions");
      ui.stay = el("button", "go", "Stay " + cfg.stayMin + " more"); ui.stay.type = "button";
      ui.leave = el("button", "leave", "Leave"); ui.leave.type = "button";
      actions.append(ui.stay, ui.leave);
      panel.appendChild(actions);
      ui.stay.addEventListener("click", onStay);
      ui.leave.addEventListener("click", onLeave);
      scrim.appendChild(panel);
      root.appendChild(scrim);
      setTimeout(() => { try { ui.stay.focus({ preventScroll: true }); } catch (e) { /* ignore */ } }, 0);
    }
    scrollLock(true); mediaGuard(true);
  }

  function hideOverlay() {
    clearUi();
    if (host) host.remove();
    mode = "off"; overlayKey = "";
    scrollLock(false); mediaGuard(false);
  }

  // ---------- actions ----------
  let busy = false;
  async function act(fn) {
    if (busy) return;
    busy = true;
    try { await fn(); } finally { busy = false; }
  }
  const onGoIn = () => act(async () => {
    const text = ui && ui.input ? ui.input.value : "";
    const r = await send({ type: "goIn", intention: text });
    if (r && r.ok) apply({ ok: true, track: true, state: "active", until: r.until, count: true }); else check();
  });
  const onStay = () => act(async () => {
    const r = await send({ type: "extend" });
    if (r && r.ok) apply({ ok: true, track: true, state: "active", until: r.until, count: true }); else check();
  });
  const onLeave = () => act(async () => {
    const r = await send({ type: "leave" });
    if (!r || !r.ok) { hideOverlay(); } // never trap the user; the worker navigates the tab on success
  });

  // ---------- state machine ----------
  function setCounting(on) { counting = on; syncActivity(); }
  function scheduleExpiry(until) {
    clearTimeout(expiryTimer);
    if (!until) return;
    expiryTimer = setTimeout(check, Math.max(0, until - Date.now()) + 100);
  }
  function apply(r) {
    clearTimeout(expiryTimer);
    if (!r || !r.ok) { hideOverlay(); setCounting(false); return; } // fail open
    if (!r.track) { hideOverlay(); setCounting(!!r.count); return; }
    if (r.countdownSec) cfg = { countdownSec: r.countdownSec, sessionMin: r.sessionMin, stayMin: r.stayMin, mascot: r.mascot };
    if (r.state === "active") {
      hideOverlay(); setCounting(true); scheduleExpiry(r.until);
    } else {
      setCounting(false);
      showOverlay(r.state === "expired" ? "expired" : "intro");
    }
  }
  async function check(attempt) {
    const my = ++seq;
    const r = await send({ type: "check" });
    if (my !== seq) return;
    // The worker derives the URL from the tab; during SPA navigation it can lag a moment behind.
    if (r && r.ok && r.url && (attempt || 0) < 4) {
      let p = "";
      try { p = new URL(r.url).pathname; } catch (e) { /* ignore */ }
      if (p && p !== location.pathname) { clearTimeout(retryTimer); retryTimer = setTimeout(() => check((attempt || 0) + 1), 250); return; }
    }
    apply(r);
  }

  // ---------- active time ----------
  const active = () => counting && mode === "off" && document.visibilityState === "visible" && document.hasFocus();
  function syncActivity() {
    const on = active();
    if (on && !hbOn) { hbOn = true; send({ type: "hb", kind: "start" }); }
    else if (!on && hbOn) { hbOn = false; send({ type: "hb", kind: "stop" }); }
  }
  hbTimer = setInterval(() => { syncActivity(); if (hbOn) send({ type: "hb", kind: "beat" }); }, HB_MS);
  for (const t of ["visibilitychange"]) document.addEventListener(t, syncActivity);
  window.addEventListener("focus", syncActivity);
  window.addEventListener("blur", syncActivity);
  window.addEventListener("pagehide", () => { if (hbOn) { hbOn = false; send({ type: "hb", kind: "stop" }); } });

  // ---------- navigation (SPA) ----------
  function onNav() {
    if (location.href === lastUrl) return;
    lastUrl = location.href;
    check();
  }
  for (const t of ["yt-navigate-finish", "popstate", "hashchange"]) { document.addEventListener(t, onNav); window.addEventListener(t, onNav); }
  try { if (window.navigation) { window.navigation.addEventListener("navigatesuccess", onNav); window.navigation.addEventListener("currententrychange", onNav); } } catch (e) { /* ignore */ }
  setInterval(onNav, POLL_MS); // fallback

  try {
    chrome.runtime.onMessage.addListener((msg, sender) => {
      if (sender && sender.id === chrome.runtime.id && msg && msg.type === "recheck") check();
    });
  } catch (e) { /* extension context gone */ }

  // ---------- go ----------
  watchHost();
  showPending();
  check();
})();
