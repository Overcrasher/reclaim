# Privacy Policy – Reclaim

**No data leaves your device.**

Reclaim stores everything (your settings, your list of sites, daily time totals for the last 60 days, short-lived intentions and donation state) in your browser's local extension storage (`chrome.storage.local`).

- No analytics, no tracking, no ads, no accounts.
- No server is contacted by the extension. It makes no network requests of its own.
- On the sites in your list, Reclaim reads only the page address (host and path), to decide whether to show the pause screen, and it counts active time: a signal every 15 seconds while the tab is visible and focused. It does not read page text. It pauses and mutes media on those pages while the pause screen is up.
- Intentions: if you type what you are there for, the text is saved with the time and the site, only on your device. Intentions are deleted automatically after 7 days (a daily clean-up and a check at browser startup).
- Daily totals (kept for the last 60 days): time spent per day, estimated time reclaimed, and how many times you chose "Go in" or "Leave". "Time reclaimed" is an estimate calculated locally from an average session length you can change; it is not a measurement.
- Permissions: `storage` (settings and totals), `tabs` (to know which tab is on a listed site and focused, so only active time is counted, and to open the "reclaimed" page when you leave), `alarms` (session timers and the daily clean-up) and `scripting` (to register the pause screen for sites you add yourself).
- Site access: the built-in sites are listed in the extension's manifest and granted at install. A site you add is requested through Chrome's own permission prompt when you click "Add" in Options; removing the site removes the permission.
- Donation links open in a normal browser tab, at your request. Payments are handled entirely by Stripe on their own page; the extension never sees payment details.
- The optional thank-you page only lets the extension mark you as a supporter locally (a flag stored on your device). It is hosted on GitHub Pages, so visiting it contacts GitHub (their privacy policy applies). The extension itself still sends nothing.

You can erase all data at any time by removing the extension.

Questions: open an issue at https://github.com/Overcrasher/reclaim/issues.

Publisher: Quantumbyte Labs.
