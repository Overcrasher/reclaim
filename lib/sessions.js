// Pure session / time-tracking math. Classic script: attaches ReclaimSessions to globalThis.
(function (root) {
  "use strict";

  const MIN = 60 * 1000;
  const GRACE_MS = 30 * MIN;            // an expired session nobody answered is forgotten after this
  const HB_CAP_MS = 20 * 1000;          // max credit per heartbeat
  const HB_STALE_MS = 40 * 1000;        // gap after which a heartbeat is treated as the first one
  const INTENTION_TTL_MS = 7 * 24 * 60 * MIN;
  const KEEP_DAYS = 60;

  const isNum = (n) => typeof n === "number" && isFinite(n);
  const isObj = (o) => !!o && typeof o === "object" && !Array.isArray(o);

  // sess: { startedAt, until } or undefined -> "none" | "active" | "expired"
  function sessionState(sess, now) {
    if (!isObj(sess) || !isNum(sess.until) || !isNum(now)) return "none";
    if (now < sess.until) return "active";
    return now - sess.until <= GRACE_MS ? "expired" : "none";
  }
  const startSession = (now, minutes) => ({ startedAt: now, until: now + minutes * MIN });
  // Extends from NOW (an expired session has no time left to add to).
  const extendSession = (sess, now, minutes) =>
    ({ startedAt: isObj(sess) && isNum(sess.startedAt) ? sess.startedAt : now, until: now + minutes * MIN });
  const remainingMs = (sess, now) => (isObj(sess) && isNum(sess.until) ? Math.max(0, sess.until - now) : 0);

  // Local calendar day "YYYY-MM-DD".
  function dayKey(ms) {
    const d = new Date(ms);
    const p = (n) => (n < 10 ? "0" : "") + n;
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate());
  }

  function pruneDays(days, keep) {
    const keys = Object.keys(days).sort();
    const out = {};
    for (const k of keys.slice(-(keep || KEEP_DAYS))) out[k] = days[k];
    return out;
  }

  const zeroDay = () => ({ spentSec: 0, reclaimedMin: 0, leaves: 0, goIns: 0, sites: {} });
  const zeroTotals = () => ({ reclaimedMin: 0, leaves: 0, goIns: 0, spentSec: 0 });

  // state: { days, totals }; patch: numeric deltas + optional site:{key,sec}. Returns a NEW state.
  function bump(state, now, patch) {
    const key = dayKey(now);
    const day = Object.assign(zeroDay(), (state.days || {})[key]);
    day.sites = Object.assign({}, day.sites);
    const t = Object.assign(zeroTotals(), state.totals);
    for (const f of ["spentSec", "reclaimedMin", "leaves", "goIns"]) {
      const v = patch[f];
      if (isNum(v) && v > 0) { day[f] += v; t[f] += v; }
    }
    if (patch.site && isNum(patch.site.sec) && patch.site.sec > 0) {
      day.sites[patch.site.key] = (day.sites[patch.site.key] || 0) + patch.site.sec;
    }
    const days = Object.assign({}, state.days, { [key]: day });
    return { days: pruneDays(days, KEEP_DAYS), totals: t };
  }
  const recordGoIn = (state, now) => bump(state, now, { goIns: 1 });
  const recordLeave = (state, now, avgMin) => bump(state, now, { leaves: 1, reclaimedMin: avgMin });
  const recordSpent = (state, now, siteKey, sec) => bump(state, now, { spentSec: sec, site: { key: siteKey, sec } });

  // Seconds to credit for a heartbeat. lastAt: previous heartbeat time (ms) of the same tab, or falsy.
  // Never more than the real elapsed time, never more than the 20 s cap, 0 for a first/stale heartbeat.
  function heartbeatCredit(lastAt, now) {
    if (!isNum(lastAt) || lastAt <= 0 || !isNum(now)) return 0;
    const d = now - lastAt;
    if (d <= 0 || d > HB_STALE_MS) return 0;
    return Math.min(d, HB_CAP_MS) / 1000;
  }

  // Intentions older than 7 days are dropped (boundary: exactly 7 days is kept).
  function purgeIntentions(list, now, ttl) {
    const t = isNum(ttl) ? ttl : INTENTION_TTL_MS;
    return (Array.isArray(list) ? list : []).filter((i) => isObj(i) && isNum(i.at) && now - i.at <= t);
  }

  root.ReclaimSessions = {
    MIN, GRACE_MS, HB_CAP_MS, HB_STALE_MS, INTENTION_TTL_MS, KEEP_DAYS,
    sessionState, startSession, extendSession, remainingMs, dayKey, pruneDays, bump, recordGoIn, recordLeave,
    recordSpent, heartbeatCredit, purgeIntentions,
  };
})(globalThis);
