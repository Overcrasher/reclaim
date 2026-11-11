import { getAll } from "./lib/store.js";
import { renderDonateButtons, hasDonateLinks } from "./lib/support.js";

const $ = (id) => document.getElementById(id);
const ST = globalThis.ReclaimStats;
const D = globalThis.ReclaimDonation;
const G = globalThis.ReclaimGrowth;
const M = globalThis.ReclaimMascot;
const NS = "http://www.w3.org/2000/svg";
let state = null;
let bannerShown = false;
let ratingShown = false;

function svgEl(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k of Object.keys(attrs || {})) e.setAttribute(k, String(attrs[k]));
  if (parent) parent.appendChild(e);
  return e;
}

// 7 days x (spent, reclaimed) bars, inline SVG with an accessible text alternative.
function drawChart(buckets) {
  const W = 328, H = 128, padB = 18, padT = 6, bw = 14, gap = 3;
  const max = Math.max(30, ...buckets.map((b) => Math.max(b.spentMin, b.reclaimedMin)));
  const svg = svgEl("svg", { viewBox: "0 0 " + W + " " + H, role: "img" }, null);
  const desc = buckets.map((b) => b.label + ": " + ST.formatMin(b.spentMin) + " spent, " + ST.formatMin(b.reclaimedMin) + " reclaimed (estimate)").join(". ");
  svg.setAttribute("aria-label", "Bar chart for this week. " + desc);
  svgEl("title", {}, svg).textContent = "This week: spent vs reclaimed (estimate)";
  const plotH = H - padB - padT, slot = W / 7;
  svgEl("line", { x1: 0, y1: H - padB, x2: W, y2: H - padB, class: "axis" }, svg);
  buckets.forEach((b, i) => {
    const x0 = slot * i + slot / 2 - bw - gap / 2;
    const hs = (b.spentMin / max) * plotH, hr = (b.reclaimedMin / max) * plotH;
    svgEl("rect", { class: "bar-s", x: x0, y: H - padB - hs, width: bw, height: Math.max(hs, b.spentMin > 0 ? 2 : 0), rx: 3 }, svg);
    svgEl("rect", { class: "bar-r", x: x0 + bw + gap, y: H - padB - hr, width: bw, height: Math.max(hr, b.reclaimedMin > 0 ? 2 : 0), rx: 3 }, svg);
    const t = svgEl("text", { x: slot * i + slot / 2, y: H - 4, "text-anchor": "middle", class: b.isToday ? "today" : "" }, svg);
    t.textContent = b.label;
  });
  return svg;
}

function render() {
  const s = state, now = Date.now();
  $("supporter").hidden = !s.supporter;
  const buckets = ST.weekBuckets(s.days, now, 0);
  const wk = ST.weekTotals(buckets);
  const today = ST.todayStats(s.days, now);
  $("reclaimed").textContent = "≈ " + ST.formatMin(today.reclaimedMin);
  $("spent").textContent = ST.formatMin(today.spentMin) + " spent on these sites";
  $("mascot").textContent = "";
  $("mascot").appendChild(M.draw(document, ST.mascotState(wk.reclaimedMin, wk.spentMin), 96));
  $("chart").textContent = "";
  $("chart").appendChild(drawChart(buckets));
  $("weekTotals").textContent = ST.formatMin(wk.spentMin) + " spent · ≈ " + ST.formatMin(wk.reclaimedMin) + " reclaimed (estimate)";

  const summary = ST.weeklySummary(now, s.days);
  $("weekly").hidden = !summary;
  if (summary) $("weekly-text").textContent = summary.text;

  const paused = s.pausedUntil > now;
  $("pause").classList.toggle("on", paused);
  $("pause").textContent = paused ? "Resume Reclaim" : "Pause Reclaim for 1 hour";
  $("pauseNote").hidden = !paused;
  if (paused) $("pauseNote").textContent = "Paused until " + new Date(s.pausedUntil).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" }) + ". Reclaim is not interrupting you.";
  $("share").hidden = !(wk.reclaimedMin >= 1);
}

async function maybeShowBanner() {
  if (bannerShown || ratingShown || state.supporter) return;
  const now = Date.now();
  const hours = state.totals.reclaimedMin / 60;
  const dstate = Object.assign({}, state.donation, { supporter: state.supporter });
  const milestone = D.pickAsk(dstate, hours, now);
  if (!milestone) return;
  if (!hasDonateLinks()) return; // unconfigured build: don't burn the milestone
  bannerShown = true;
  const next = D.applyAsk(state.donation, milestone, now);
  state.donation = next;
  await chrome.storage.local.set({ donation: next });
  $("banner-text").textContent = D.bannerText(hours);
  renderDonateButtons($("banner-buttons"), $("banner-note"));
  $("banner").hidden = false;
}

// One-time, quieter than the donation banner, and never in the same render as it.
async function maybeShowRating() {
  if (ratingShown || bannerShown) return;
  if (!G.shouldAskRating(state.rating, state.totals.leaves, G.RATING_THRESHOLD)) return;
  ratingShown = true;
  const rating = { shown: true, at: Date.now() };
  state.rating = rating;
  await chrome.storage.local.set({ rating });
  $("rating").hidden = false;
}

async function refresh() {
  state = await getAll();
  render();
  await maybeShowBanner();
  await maybeShowRating();
}

async function share() {
  const wk = ST.weekTotals(ST.weekBuckets(state.days, Date.now(), 0));
  const text = ST.shareText(wk.reclaimedMin, G.shareUrl(chrome.runtime.id), "this week");
  try { await navigator.clipboard.writeText(text); $("share").textContent = "Copied!"; }
  catch (e) { $("share").textContent = "Copy failed"; }
  setTimeout(() => { $("share").textContent = "Share"; }, 1800);
}

function init() {
  $("banner-close").addEventListener("click", () => { $("banner").hidden = true; });
  $("banner-dismiss").addEventListener("click", () => { $("banner").hidden = true; });
  $("banner-never").addEventListener("click", async () => {
    const donation = Object.assign({}, state.donation, { dontAskAgain: true });
    state.donation = donation;
    await chrome.storage.local.set({ donation });
    $("banner").hidden = true;
  });
  $("rating-go").addEventListener("click", () => { chrome.tabs.create({ url: G.reviewsUrl(chrome.runtime.id) }); $("rating").hidden = true; });
  $("rating-no").addEventListener("click", () => { $("rating").hidden = true; });
  $("optionsLink").addEventListener("click", () => { chrome.runtime.openOptionsPage(); window.close(); });
  $("pause").addEventListener("click", async () => {
    const paused = state.pausedUntil > Date.now();
    const pausedUntil = paused ? 0 : Date.now() + 60 * 60 * 1000;
    state.pausedUntil = pausedUntil;
    await chrome.storage.local.set({ pausedUntil });
    render();
  });
  $("share").addEventListener("click", share);
  chrome.storage.onChanged.addListener((changes, area) => { if (area === "local") refresh(); });
  refresh();
}
init();
