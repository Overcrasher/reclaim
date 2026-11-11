// Pure site-rule logic. Classic script: attaches ReclaimSites to globalThis.
// A rule is { host, pathPrefix? }; a host rule matches the host and all its subdomains.
(function (root) {
  "use strict";

  const DEFAULT_SITES = Object.freeze([
    Object.freeze({ host: "youtube.com", pathPrefix: "/shorts" }),
    Object.freeze({ host: "tiktok.com" }),
    Object.freeze({ host: "reddit.com" }),
    Object.freeze({ host: "x.com" }),
    Object.freeze({ host: "twitter.com" }),
    Object.freeze({ host: "instagram.com" }),
    Object.freeze({ host: "facebook.com" }),
  ]);

  const hostMatches = (hostname, ruleHost) =>
    typeof hostname === "string" && typeof ruleHost === "string" && ruleHost !== "" &&
    (hostname === ruleHost || hostname.endsWith("." + ruleHost));

  // Segment-aware: "/shorts" matches "/shorts" and "/shorts/abc" but not "/shortsfoo".
  function pathMatches(pathname, prefix) {
    if (!prefix) return true;
    if (typeof pathname !== "string") return false;
    const p = pathname.toLowerCase();
    return p === prefix || p.startsWith(prefix + "/");
  }

  function parseHttps(u) {
    if (typeof u !== "string" || u.length > 2048) return null;
    try {
      if (typeof URL === "function") {
        const x = new URL(u);
        return x.protocol === "https:" ? { hostname: x.hostname.toLowerCase(), pathname: x.pathname } : null;
      }
      const m = /^https:\/\/([^\/?#:@\s]+)(:\d+)?(\/[^?#\s]*)?(\?[^#\s]*)?(#\S*)?$/i.exec(u);
      return m ? { hostname: m[1].toLowerCase(), pathname: m[3] || "/" } : null;
    } catch (e) { return null; }
  }

  // The most specific matching rule (longest path prefix, then longest host), or null.
  function matchRule(url, rules) {
    const x = parseHttps(url);
    if (!x || !Array.isArray(rules)) return null;
    let best = null, bestScore = -1;
    for (const r of rules) {
      if (!r || !hostMatches(x.hostname, r.host) || !pathMatches(x.pathname, r.pathPrefix)) continue;
      const score = (r.pathPrefix ? r.pathPrefix.length : 0) * 1000 + r.host.length;
      if (score > bestScore) { best = r; bestScore = score; }
    }
    return best;
  }

  // True if the URL's host is covered by any rule host (path ignored).
  function hostOnlyMatch(url, rules) {
    const x = parseHttps(url);
    return !!x && Array.isArray(rules) && rules.some((r) => r && hostMatches(x.hostname, r.host));
  }

  const siteKey = (r) => r.host + (r.pathPrefix || "");
  const isDefault = (r) => DEFAULT_SITES.some((d) => d.host === r.host && (d.pathPrefix || "") === (r.pathPrefix || ""));
  // A rule whose host is already covered by a default (statically injected) host needs no dynamic script.
  const coveredByDefault = (r) => DEFAULT_SITES.some((d) => hostMatches(r.host, d.host));
  const scriptId = (r) => "site-" + siteKey(r).replace(/[^a-z0-9]/g, "-");
  const originPatterns = (r) => ["https://" + r.host + "/*", "https://*." + r.host + "/*"];
  const label = (r) => r.host + (r.pathPrefix || "");

  root.ReclaimSites = {
    DEFAULT_SITES, hostMatches, pathMatches, matchRule, hostOnlyMatch, siteKey, isDefault, coveredByDefault,
    scriptId, originPatterns, label,
  };
})(globalThis);
