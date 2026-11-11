# Reclaim

A Manifest V3 Chrome extension that adds a calm pause before time-wasting sites. Open a tracked site and a full-screen
overlay asks "What are you here for?", runs a short countdown, then offers **Go in** (a timed session) or **Leave**.
When the session ends a soft overlay offers **Stay 5 more** or **Leave**. Leaving adds an *estimated* amount of
"time reclaimed". A small plant in the popup grows as your weeks go well. Plain JavaScript, no build step, no libraries,
no network requests.

**Install:** from the Chrome Web Store (link will appear on <https://overcrasher.github.io/reclaim/> once published).
For development: `chrome://extensions` -> Developer mode -> **Load unpacked** -> pick this `reclaim` folder.

## How it works

1. A content script runs at `document_start` (top frame only) on tracked pages and immediately covers the viewport with a
   closed Shadow DOM overlay. Playing media is paused and muted (re-checked every 250 ms, restored on "Go in").
   Keyboard and wheel input cannot reach the page underneath. If the service worker cannot be reached the overlay is removed (fail open).
2. Overlay: mascot, optional intention (max 140 chars), calm countdown ring (default 5 s, 3 to 30), then **Go in (10 min)** / **Leave**.
3. **Go in** starts a per-site session (5/10/15/20/30 min). Other tabs and navigations on that site are not interrupted.
   A service-worker alarm plus the content script's own timer show the "time is up" overlay; **Stay 5 more** extends the session from now (5/10/15 min).
4. **Leave** adds the average session length (default 15 min, configurable) to "time reclaimed" - always labelled as an *estimate* - and navigates the tab to the extension page `reclaimed.html` (today's total, Share, Close tab).
5. Active time = tab visible AND window focused on a tracked site while a session is active (or while paused). The content script sends `start`/`beat`/`stop` heartbeats (every 15 s); the worker credits at most `min(elapsed, 20 s)` per beat, never more than wall time, and also flushes on `windows.onFocusChanged` / `tabs.onActivated` / `tabs.onRemoved`.
6. SPA navigation (YouTube moves between pages without reloading): path-scoped rules run on the whole host and re-check on `yt-navigate-finish`, `popstate`, `hashchange`, the Navigation API events and a 1 s URL poll. The overlay appears when the path enters the prefix and disappears when it leaves. (Content scripts live in an isolated world, so `history.pushState` wrappers would not see page calls; the Navigation API and the poll cover that.)

Default sites: youtube.com/shorts (path-scoped), tiktok.com, reddit.com, x.com, twitter.com, instagram.com, facebook.com.
Add or remove sites in Options.

### Data (all local, `chrome.storage.local`)
Per day for the last 60 days `{ spentSec, reclaimedMin, leaves, goIns, sites }`, lifetime totals, settings, site list, sessions,
and intentions `[{ text, site, at }]` which are deleted after 7 days by a daily alarm (and on every extension start). Intentions never leave the device.

## Permissions (and why)

| Permission | Why |
|---|---|
| `storage` | settings, statistics, sessions (local only) |
| `tabs` | open the welcome / reclaimed / store pages, navigate the tab on "Leave", find open tabs on tracked sites to refresh or expire overlays |
| `alarms` | session expiry, daily intention purge |
| `scripting` | `chrome.scripting.registerContentScripts` for sites the user adds at runtime (persisted across sessions) |
| `host_permissions` | the seven default sites, granted at install, so the overlay can run at `document_start` |
| `optional_host_permissions: https://*/*` | requested with `chrome.permissions.request` from the Options click handler only when the user adds a site; removed again when the site is removed |

No `activeTab`, no `webRequest`, no `<all_urls>` at install, no remote code.

## Security model

- `chrome.storage.local` and `chrome.storage.session` are set to `TRUSTED_CONTEXTS`: content scripts never read or write storage; they message the worker.
- The worker classifies every sender (own extension page vs top-frame content script) and derives the site from `sender.tab.url`, never from the message. Intentions are cleaned (control/bidi characters removed, 140 chars), heartbeat kinds and all stored data are re-validated on read.
- `supporter` is accepted only from the exact thank-you page with a `^cs_(live|test)_[A-Za-z0-9]{20,}$` id (cosmetic, honour system).
- Injected UI: closed Shadow DOM, `!important`-hardened host styles, never `innerHTML`; only allow-listed URLs (the store listing, its reviews page, the two sibling extensions, Stripe Payment Links) are ever opened.
- Strict extension-page CSP (`default-src 'self'`, no inline scripts, no remote code).
- Best effort only: a hostile page can still outpace the overlay (e.g. its own top-layer `<dialog>`); Reclaim is a self-control aid, not a security control.

## Stripe setup and supporter detection

Create four Payment Links in EUR (and optionally the same four in USD): 3, 5 (emphasized), 10, and a 1 EUR product with
"Let customers adjust quantity" for "Pick your own amount". Put them in `config.js` (`DONATE_LINKS`, `DONATE_LINKS_USD`; `monthly` is unused here).
Amounts shown on the buttons come from `DONATE_AMOUNTS`. Redirect every link to
`https://overcrasher.github.io/reclaim/thanks.html?session_id={CHECKOUT_SESSION_ID}`. If the repo/username changes, update `THANKS_URL`
in `config.js`, the match in `manifest.json` and `lib/validate.js`, then run `python3 tools/check_release.py`.

Asks happen only in the popup, at 5 / 20 / 50 / 100 hours reclaimed (estimate), once per milestone, at least 30 days apart, never for supporters or after "Don't ask again". With no links configured nothing is shown and the milestone is not consumed.
A one-time rating card appears after the 3rd "Leave" (never in the same render as the donation banner).

## Tests

- Unit: `/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc tests/run.js` (from this folder).
- End to end (Chrome 157, CDP over a pipe, `Extensions.loadUnpacked`, fixtures on real hostnames via Fetch): `python3 tests/e2e/harness.py` (`ONLY=2,5` selects groups); real-site check: `python3 tests/e2e/live.py`. Screenshots go to `tests/e2e/shots/` (gitignored).
- The user-added-site test cannot click Chrome's permission prompt, so it runs on a temporary copy of the extension whose `host_permissions` already include the fixture host; `permissions.request` then resolves immediately and the real Options -> registration flow is exercised.
- Release: `python3 tools/check_release.py [--release]`, then `python3 tools/package.py` (`--skip-release-check` for test builds) -> `dist/reclaim-1.0.0.zip`.

## Changes

- 1.0.0: first release.
