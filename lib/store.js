// Shared storage helpers (ES module, used by background, popup, options, reclaimed).
import "./sites.js";
import "./validate.js";
import "./sessions.js";
import "./stats.js";
const V = globalThis.ReclaimValidate;
const S = globalThis.ReclaimSites;

export const DEFAULT_SETTINGS = Object.freeze(Object.assign({}, V.DEFAULTS));
export const DEFAULT_DONATION = Object.freeze({ asked: [], lastAskAt: 0, dontAskAgain: false });
export const KEYS = ["settings", "sites", "days", "totals", "intentions", "sessions", "pausedUntil", "lastLeave", "donation", "supporter", "rating"];

// Reads everything with defaults applied and sanitized (fresh install safe).
export async function getAll() {
  const d = await chrome.storage.local.get(KEYS);
  return {
    settings: V.sanitizeSettings(d.settings),
    sites: V.sanitizeSites(d.sites, S.DEFAULT_SITES),
    days: V.sanitizeDays(d.days),
    totals: V.sanitizeTotals(d.totals),
    intentions: V.sanitizeIntentions(d.intentions),
    sessions: V.sanitizeSessions(d.sessions),
    pausedUntil: V.sanitizePausedUntil(d.pausedUntil),
    lastLeave: V.sanitizeLastLeave(d.lastLeave),
    donation: V.sanitizeDonation(d.donation),
    supporter: d.supporter === true,
    rating: V.sanitizeRating(d.rating),
  };
}

// Serializes read-modify-write operations within one context.
let chain = Promise.resolve();
export function mutate(fn) {
  const p = chain.then(fn);
  chain = p.catch(() => {});
  return p;
}
