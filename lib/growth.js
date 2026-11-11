// Pure growth helpers: store URLs, rating prompt, allow-listed links. Classic script: ReclaimGrowth on globalThis.
(function (root) {
  "use strict";

  const RATING_THRESHOLD = 3; // "Leave" clicks before the one-time rating card
  const ID_RE = /^[a-p]{32}$/;
  const STORE_BASE = "https://chromewebstore.google.com/detail/";
  const SIBLINGS = Object.freeze([
    Object.freeze({ name: "Wait 24h", url: "https://chromewebstore.google.com/detail/wait-24h/pkgdjohoemjkejcbfbkfobbbjcpdabme", blurb: "a pause before impulse buys" }),
    Object.freeze({ name: "Meeting Meter", url: "https://chromewebstore.google.com/detail/meeting-meter/ffkniocclnaojfdcoofnjkfnihnpgnlb", blurb: "see what your meetings cost" }),
  ]);

  // The id is a parameter so jsc can test these (in the extension: chrome.runtime.id).
  const storeUrl = (id) => (typeof id === "string" && ID_RE.test(id) ? STORE_BASE + id : "");
  const reviewsUrl = (id) => (storeUrl(id) ? storeUrl(id) + "/reviews" : "");
  const shareUrl = (id) => (storeUrl(id) ? storeUrl(id) + "?utm_source=share" : "");
  // Only these URLs are ever opened from the options/popup links.
  function allowedLinks(id) {
    return [storeUrl(id), reviewsUrl(id)].filter(Boolean).concat(SIBLINGS.map((s) => s.url));
  }
  const isAllowedLink = (url, id) => typeof url === "string" && allowedLinks(id).includes(url);

  // state: stored rating object ({ shown, at }) or undefined; count: leaves so far; threshold: number.
  function shouldAskRating(state, count, threshold) {
    if (state !== null && typeof state === "object" && state.shown === true) return false;
    if (typeof count !== "number" || !isFinite(count) || typeof threshold !== "number" || !isFinite(threshold)) return false;
    return count >= threshold;
  }

  root.ReclaimGrowth = { RATING_THRESHOLD, SIBLINGS, storeUrl, reviewsUrl, shareUrl, allowedLinks, isAllowedLink, shouldAskRating };
})(globalThis);
