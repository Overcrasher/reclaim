import { getAll } from "./lib/store.js";

const $ = (id) => document.getElementById(id);
const ST = globalThis.ReclaimStats;
const G = globalThis.ReclaimGrowth;

async function init() {
  const s = await getAll();
  const now = Date.now();
  const recent = s.lastLeave.at && now - s.lastLeave.at < 10 * 60 * 1000;
  const min = recent ? s.lastLeave.min : s.settings.avgSessionMin;
  $("minutes").textContent = "≈ " + min + " min reclaimed";
  const today = ST.todayStats(s.days, now);
  $("today").textContent = "Today so far: ≈ " + ST.formatMin(today.reclaimedMin) + " reclaimed (estimate)";
  const wk = ST.weekTotals(ST.weekBuckets(s.days, now, 0));
  $("mascot").appendChild(globalThis.ReclaimMascot.draw(document, ST.mascotState(wk.reclaimedMin, wk.spentMin), 120));
  $("share").addEventListener("click", async () => {
    const text = ST.shareText(wk.reclaimedMin, G.shareUrl(chrome.runtime.id), "this week");
    try { await navigator.clipboard.writeText(text); $("share").textContent = "Copied!"; } catch (e) { $("share").textContent = "Copy failed"; }
    setTimeout(() => { $("share").textContent = "Share"; }, 1800);
  });
  $("close").addEventListener("click", async () => {
    try { const t = await chrome.tabs.getCurrent(); if (t && t.id != null) { await chrome.tabs.remove(t.id); return; } } catch (e) { /* fall through */ }
    window.close();
  });
}
init();
