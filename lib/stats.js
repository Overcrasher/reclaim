// Pure statistics, week buckets, summary phrases, mascot state and share text.
// Classic script: attaches ReclaimStats to globalThis (needs lib/sessions.js loaded first).
(function (root) {
  "use strict";

  const SS = root.ReclaimSessions;
  const DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  // Local Monday 00:00 of the week containing `ms`. offsetWeeks shifts whole weeks (DST-safe: calendar maths).
  function weekStart(ms, offsetWeeks) {
    const d = new Date(ms);
    const back = (d.getDay() + 6) % 7;
    return new Date(d.getFullYear(), d.getMonth(), d.getDate() - back + 7 * (offsetWeeks || 0)).getTime();
  }
  // Seven "YYYY-MM-DD" keys, Monday first.
  function weekKeys(ms, offsetWeeks) {
    const d = new Date(weekStart(ms, offsetWeeks));
    const out = [];
    for (let i = 0; i < 7; i++) out.push(SS.dayKey(new Date(d.getFullYear(), d.getMonth(), d.getDate() + i).getTime()));
    return out;
  }
  // [{ key, label, spentMin, reclaimedMin, isToday }] x 7
  function weekBuckets(days, now, offsetWeeks) {
    const today = SS.dayKey(now);
    return weekKeys(now, offsetWeeks).map((key, i) => {
      const d = (days && days[key]) || {};
      return {
        key, label: DOW[i], isToday: key === today,
        spentMin: (d.spentSec || 0) / 60, reclaimedMin: d.reclaimedMin || 0,
      };
    });
  }
  function weekTotals(buckets) {
    let spentMin = 0, reclaimedMin = 0;
    for (const b of buckets) { spentMin += b.spentMin; reclaimedMin += b.reclaimedMin; }
    return { spentMin, reclaimedMin };
  }
  function todayStats(days, now) {
    const d = (days && days[SS.dayKey(now)]) || {};
    return { spentMin: (d.spentSec || 0) / 60, reclaimedMin: d.reclaimedMin || 0 };
  }

  // 45 -> "45m", 200 -> "3h 20m", 120 -> "2h", 0 -> "0m"
  function formatMin(m) {
    m = Math.round(typeof m === "number" && isFinite(m) ? m : 0);
    if (m <= 0) return "0m";
    if (m < 60) return m + "m";
    const h = Math.floor(m / 60), r = m % 60;
    return r ? h + "h " + r + "m" : h + "h";
  }

  // Thresholds in minutes, ascending; the largest one not above the total wins.
  const PHRASES = [
    { min: 10, text: "about a coffee break" },
    { min: 30, text: "about one good book chapter" },
    { min: 60, text: "about a long walk" },
    { min: 100, text: "about one movie's worth" },
    { min: 240, text: "about a whole evening" },
  ];
  function summaryPhrase(minutes) {
    let out = "";
    for (const p of PHRASES) if (minutes >= p.min) out = p.text;
    return out;
  }
  function summaryText(minutes, period) {
    const base = "You reclaimed " + formatMin(minutes) + " " + period;
    const ph = summaryPhrase(Math.round(minutes));
    return base + (ph ? ", " + ph : "") + ".";
  }
  // Sunday: this week. Monday: the week that just ended. Other days: null. Nothing reclaimed: null.
  function weeklySummary(now, days) {
    const dow = new Date(now).getDay();
    if (dow !== 0 && dow !== 1) return null;
    const offset = dow === 0 ? 0 : -1;
    const period = dow === 0 ? "this week" : "last week";
    const minutes = weekTotals(weekBuckets(days, now, offset)).reclaimedMin;
    if (!(minutes > 0)) return null;
    return { period, minutes, text: summaryText(minutes, period) };
  }

  // 0 wilted, 1 droopy, 2 sprout (neutral), 3 growing, 4 blooming. Pure function of this week's minutes.
  function mascotState(reclaimedMin, spentMin) {
    const r = Math.max(0, Number(reclaimedMin) || 0), s = Math.max(0, Number(spentMin) || 0);
    if (r >= 240 && r >= s) return 4;
    if (r >= 60 && r * 2 >= s) return 3;
    if (s >= 420 && r < s / 4) return 0;
    if (s >= 180 && r < s / 2) return 1;
    return 2;
  }

  function shareText(minutes, shareUrl, period) {
    return "I reclaimed " + formatMin(minutes) + " from doomscrolling " + (period || "this week") + ". #Reclaim " + shareUrl;
  }

  root.ReclaimStats = {
    DOW, PHRASES, weekStart, weekKeys, weekBuckets, weekTotals, todayStats, formatMin, summaryPhrase, summaryText,
    weeklySummary, mascotState, shareText,
  };
})(globalThis);
