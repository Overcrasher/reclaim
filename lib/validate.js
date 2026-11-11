// Pure validators / sanitizers. Classic script: attaches ReclaimValidate to globalThis.
// Used by the service worker (via lib/store.js), the extension pages and the jsc tests.
(function (root) {
  "use strict";

  const SESSION_RE = /^cs_(live|test)_[A-Za-z0-9]{20,}$/;
  const THANKS_PAGE = "https://overcrasher.github.io/reclaim/thanks.html";
  const MAX_INTENTION = 140, MAX_URL = 2048, MAX_INTENTIONS = 200, MAX_SITES = 60, KEEP_DAYS = 60;
  const SESSION_MINUTES = [5, 10, 15, 20, 30];
  const STAY_MINUTES = [5, 10, 15];
  const DEFAULTS = { countdownSec: 5, sessionMin: 10, stayMin: 5, avgSessionMin: 15 };
  const DAY_RE = /^\d{4}-\d{2}-\d{2}$/;
  const HOST_RE = /^(?=.{4,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+([a-z]{2,24}|xn--[a-z0-9-]{2,20})$/;
  const PATH_RE = /^\/[A-Za-z0-9._~%\/-]{0,99}$/;
  // Control chars, line/paragraph separators, zero-width and bidi override characters.
  const BAD_CHARS = /[\u0000-\u001f\u007f-\u009f\u2028\u2029\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]/g;

  const isObj = (o) => !!o && typeof o === "object" && !Array.isArray(o);
  const isNum = (n) => typeof n === "number" && isFinite(n);
  const isInt = (n) => isNum(n) && Math.floor(n) === n;
  const nonNeg = (n, max) => (isNum(n) && n >= 0 ? Math.min(n, max) : 0);

  function cleanIntention(s) {
    if (typeof s !== "string") return "";
    return s.replace(BAD_CHARS, " ").replace(/\s+/g, " ").trim().slice(0, MAX_INTENTION).trim();
  }
  const validSession = (s) => typeof s === "string" && SESSION_RE.test(s);

  function parseHttps(u) {
    if (typeof u !== "string" || u.length > MAX_URL) return null;
    try {
      if (typeof URL === "function") {
        const x = new URL(u);
        return x.protocol === "https:" ? { origin: x.origin, pathname: x.pathname } : null;
      }
      const m = /^https:\/\/([^\/?#:@\s]+)(:\d+)?(\/[^?#\s]*)?(\?[^#\s]*)?(#\S*)?$/i.exec(u);
      return m ? { origin: "https://" + m[1].toLowerCase() + (m[2] || ""), pathname: m[3] || "/" } : null;
    } catch (e) { return null; }
  }
  function isThanksUrl(u) {
    const x = parseHttps(u);
    return !!x && x.origin + x.pathname === THANKS_PAGE;
  }

  // ---- site rules
  const validHost = (h) => typeof h === "string" && HOST_RE.test(h);
  // "/shorts/" -> "/shorts"; "/" or "" -> ""; invalid -> "".
  function cleanPathPrefix(p) {
    if (typeof p !== "string") return "";
    let t = p.trim().toLowerCase();
    while (t.length > 1 && t.endsWith("/")) t = t.slice(0, -1);
    if (t === "/" || t === "") return "";
    return PATH_RE.test(t) ? t : "";
  }
  function siteRule(r) {
    if (!isObj(r)) return null;
    const host = typeof r.host === "string" ? r.host.toLowerCase() : "";
    if (!validHost(host)) return null;
    const p = cleanPathPrefix(r.pathPrefix);
    return p ? { host, pathPrefix: p } : { host };
  }
  // Free-form user input ("https://www.Example.com/news?x=1", "example.com/news") -> rule or null.
  function parseSiteInput(text) {
    if (typeof text !== "string") return null;
    let t = text.trim().toLowerCase();
    if (!t || t.length > 200 || /\s/.test(t)) return null;
    t = t.replace(/^https?:\/\//, "");
    if (/^[a-z][a-z0-9+.-]*:/.test(t)) return null; // other scheme, or a port
    t = t.split(/[?#]/)[0];
    const i = t.indexOf("/");
    let host = i < 0 ? t : t.slice(0, i);
    const path = i < 0 ? "" : t.slice(i);
    if (host.indexOf("@") >= 0) return null;
    host = host.replace(/^www\./, "").replace(/\.$/, "");
    if (!validHost(host)) return null;
    const p = cleanPathPrefix(path);
    if (path && path !== "/" && !p) return null;
    return p ? { host, pathPrefix: p } : { host };
  }
  // Valid, de-duplicated rules (max 60). Not an array -> copy of defaults.
  function sanitizeSites(list, defaults) {
    if (!Array.isArray(list)) return (defaults || []).map((r) => Object.assign({}, r));
    const seen = new Set(), out = [];
    for (const r of list) {
      const x = siteRule(r);
      if (!x) continue;
      const k = x.host + (x.pathPrefix || "");
      if (seen.has(k)) continue;
      seen.add(k); out.push(x);
      if (out.length >= MAX_SITES) break;
    }
    return out;
  }

  // ---- settings
  function sanitizeSettings(s) {
    s = isObj(s) ? s : {};
    return {
      countdownSec: isInt(s.countdownSec) && s.countdownSec >= 3 && s.countdownSec <= 30 ? s.countdownSec : DEFAULTS.countdownSec,
      sessionMin: SESSION_MINUTES.includes(s.sessionMin) ? s.sessionMin : DEFAULTS.sessionMin,
      stayMin: STAY_MINUTES.includes(s.stayMin) ? s.stayMin : DEFAULTS.stayMin,
      avgSessionMin: isInt(s.avgSessionMin) && s.avgSessionMin >= 5 && s.avgSessionMin <= 120 ? s.avgSessionMin : DEFAULTS.avgSessionMin,
    };
  }

  // ---- stats
  const emptyDay = () => ({ spentSec: 0, reclaimedMin: 0, leaves: 0, goIns: 0, sites: {} });
  function dayRecord(d) {
    d = isObj(d) ? d : {};
    const sites = {};
    if (isObj(d.sites)) {
      for (const k of Object.keys(d.sites).slice(0, MAX_SITES)) {
        if (k.length <= 120 && isNum(d.sites[k]) && d.sites[k] >= 0) sites[k] = Math.min(d.sites[k], 86400);
      }
    }
    return {
      spentSec: nonNeg(d.spentSec, 86400), reclaimedMin: nonNeg(d.reclaimedMin, 100000),
      leaves: Math.floor(nonNeg(d.leaves, 100000)), goIns: Math.floor(nonNeg(d.goIns, 100000)), sites,
    };
  }
  // { "YYYY-MM-DD": record } for the newest 60 valid days.
  function sanitizeDays(days) {
    if (!isObj(days)) return {};
    const keys = Object.keys(days).filter((k) => DAY_RE.test(k)).sort().slice(-KEEP_DAYS);
    const out = {};
    for (const k of keys) out[k] = dayRecord(days[k]);
    return out;
  }
  function sanitizeTotals(t) {
    t = isObj(t) ? t : {};
    return {
      reclaimedMin: nonNeg(t.reclaimedMin, 1e9), leaves: Math.floor(nonNeg(t.leaves, 1e9)),
      goIns: Math.floor(nonNeg(t.goIns, 1e9)), spentSec: nonNeg(t.spentSec, 1e10),
    };
  }
  function sanitizeIntentions(list) {
    const out = [];
    for (const i of Array.isArray(list) ? list : []) {
      if (!isObj(i)) continue;
      const text = cleanIntention(i.text);
      if (!text || !isNum(i.at) || i.at <= 0) continue;
      out.push({ text, site: typeof i.site === "string" ? i.site.slice(0, 120) : "", at: i.at });
    }
    return out.slice(-MAX_INTENTIONS);
  }
  function sanitizeSessions(s) {
    if (!isObj(s)) return {};
    const out = {};
    for (const k of Object.keys(s).slice(0, MAX_SITES)) {
      const v = s[k];
      if (k.length <= 120 && isObj(v) && isNum(v.until) && v.until > 0) {
        out[k] = { startedAt: isNum(v.startedAt) && v.startedAt > 0 ? v.startedAt : v.until, until: v.until };
      }
    }
    return out;
  }
  const sanitizePausedUntil = (n) => (isNum(n) && n > 0 ? n : 0);
  function sanitizeLastLeave(l) {
    l = isObj(l) ? l : {};
    return isNum(l.at) && l.at > 0 && isNum(l.min) && l.min > 0 ? { at: l.at, min: Math.min(l.min, 120) } : { at: 0, min: 0 };
  }
  function sanitizeDonation(d) {
    d = isObj(d) ? d : {};
    return {
      asked: Array.isArray(d.asked) ? d.asked.filter((n) => isNum(n) && n > 0) : [],
      lastAskAt: isNum(d.lastAskAt) && d.lastAskAt > 0 ? d.lastAskAt : 0,
      dontAskAgain: d.dontAskAgain === true,
    };
  }
  function sanitizeRating(d) {
    d = isObj(d) ? d : {};
    return d.shown === true ? { shown: true, at: isNum(d.at) && d.at > 0 ? d.at : 0 } : { shown: false, at: 0 };
  }

  root.ReclaimValidate = {
    SESSION_RE, THANKS_PAGE, MAX_INTENTION, MAX_INTENTIONS, MAX_SITES, KEEP_DAYS, SESSION_MINUTES, STAY_MINUTES, DEFAULTS,
    cleanIntention, validSession, isThanksUrl, validHost, cleanPathPrefix, siteRule, parseSiteInput, sanitizeSites,
    sanitizeSettings, emptyDay, dayRecord, sanitizeDays, sanitizeTotals, sanitizeIntentions, sanitizeSessions,
    sanitizePausedUntil, sanitizeLastLeave, sanitizeDonation, sanitizeRating,
  };
})(globalThis);
