#!/usr/bin/env python3
"""Generates store/images/* for the Chrome Web Store (1280x800 screenshots, promo tiles, store icon).
Real UI is captured from the unpacked extension in headless Chrome (CDP, same plumbing as tests/e2e), then composed on
branded backgrounds by tools/store_common.py layouts. Usage:  python3 tools/store_images.py [capture] [compose]   (default: both)
Raw captures go to tools/store_raw/ (gitignored); final PNGs to store/images/. Throwaway Chrome profiles live in /tmp."""
import os, sys, json, time, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from store_common import *

RAW = os.path.join(HERE, "store_raw"); OUT = os.path.join(ROOT, "store", "images")
os.makedirs(RAW, exist_ok=True); os.makedirs(OUT, exist_ok=True)
ICON = os.path.join(ROOT, "icons", "icon128.png")
P = dict(bg="#F7F4EC", ink="#2F3A33", muted="#6A766E", bar="#D9825B", accent="#4F7C5A", dark="#2F6B47", hi="#F4C9A8", soft="#E3EEE3",
         rowb="#E3DECF", d1="#5E8F69", d2="#2F5139", glow="rgba(255,255,255,.22)", glow2="rgba(127,182,133,.28)")
NAME = "Reclaim"

FEED = """<!doctype html><html><head><meta charset="utf-8"><title>Feedloop</title><style>
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,"Helvetica Neue",Arial,sans-serif;background:#F1F3F6;color:#1D2430}
.top{height:58px;background:#fff;border-bottom:1px solid #E2E6EB;display:flex;align-items:center;padding:0 28px;gap:28px}
.logo{width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#6C7BFF,#C26BFF)}.nm{font-weight:800;font-size:19px}
.nav{display:flex;gap:22px;color:#5C6675;font-weight:600;font-size:15px}.nav b{color:#1D2430}.sr{margin-left:auto;width:280px;height:34px;border-radius:17px;background:#EEF0F4}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;padding:24px 28px}
.c{background:#fff;border-radius:16px;overflow:hidden;border:1px solid #E5E8EE}.m{height:190px}
.b{padding:14px 16px}.u{display:flex;align-items:center;gap:10px;font-weight:700;font-size:14px}.av{width:30px;height:30px;border-radius:50%}
.t{margin-top:10px;font-size:15px;line-height:1.4}.f{margin-top:12px;display:flex;gap:18px;color:#6B7585;font-size:13px}
</style></head><body><div class="top"><div class="logo"></div><div class="nm">Feedloop</div><div class="nav"><b>For you</b><span>Trending</span><span>Friends</span><span>Saved</span></div><div class="sr"></div></div>
<div class="grid">@@CARDS@@</div></body></html>"""
def _card(i):
    g = [("#FF9A8B","#FF6A88"),("#84FAB0","#8FD3F4"),("#FDCB82","#F6A5C0"),("#A18CD1","#FBC2EB"),("#FCCF31","#F55555"),("#43C6AC","#191654")][i % 6]
    txt = ["Ten things I learned this week", "You will not believe this sunset", "Quick breakfast ideas, part 4", "New desk setup finally done", "Morning run, 5 km at dawn", "Why everyone is talking about this"][i % 6]
    return '<div class="c"><div class="m" style="background:linear-gradient(135deg,%s,%s)"></div><div class="b"><div class="u"><div class="av" style="background:%s"></div>@creator%d</div><div class="t">%s</div><div class="f"><span>%dk likes</span><span>%d comments</span><span>Share</span></div></div></div>' % (g[0], g[1], g[1], i + 1, txt, 12 + i * 7, 240 + i * 31)
FEED_HTML = FEED.replace("@@CARDS@@", "".join(_card(i) for i in range(6)))
def fixture(url): return FEED_HTML if url.startswith("https://www.reddit.com/") else None

DAYMS = 86400000
def seed_days():
    # Mon 9 .. Fri 13 Nov 2026 (the popup tab runs with a fixed fake date): spent seconds / reclaimed minutes
    d = {}
    for key, spent, rec, leaves in [("2026-11-09", 52, 45, 3), ("2026-11-10", 38, 60, 4), ("2026-11-11", 61, 30, 2), ("2026-11-12", 27, 75, 5), ("2026-11-13", 14, 45, 3)]:
        d[key] = {"date": key, "spentSec": spent * 60, "reclaimedMin": rec, "leaves": leaves, "goIns": leaves + 1}
    return d
def fake_date(y, mo, d, h=10):
    return "(()=>{const RD=Date;const off=new RD(%d,%d,%d,%d,0,0).getTime()-RD.now();class D extends RD{constructor(...a){a.length?super(...a):super(RD.now()+off)}static now(){return RD.now()+off}};window.Date=D;})();" % (y, mo - 1, d, h)
def cdp_text_into_shadow_input(x, sid, text):
    c = x.cdp; root = c.send("DOM.getDocument", {"depth": -1, "pierce": True}, sid)["root"]; found = []
    def rec(n):
        if n["nodeType"] == 1 and n["nodeName"] == "INPUT": found.append(n["nodeId"])
        for k in n.get("children", []) or []: rec(k)
        for k in n.get("shadowRoots", []) or []: rec(k)
    rec(root); c.send("DOM.focus", {"nodeId": found[0]}, sid); c.send("Input.insertText", {"text": text}, sid)
def overlay_text(x, sid):
    c = x.cdp; root = c.send("DOM.getDocument", {"depth": -1, "pierce": True}, sid)["root"]; out = []
    def tx(n): return n.get("nodeValue", "") if n["nodeType"] == 3 else "".join(tx(k) for k in n.get("children", []) or [])
    def rec(n, ins):
        if ins and n["nodeType"] == 1 and n["nodeName"] in ("H1", "BUTTON"): out.append(tx(n))
        for k in n.get("children", []) or []: rec(k, ins)
        for k in n.get("shadowRoots", []) or []: rec(k, True)
    rec(root, False); return out

def capture():
    x = Ext(ROOT, "reclaim-store", fixture, ["www.reddit.com"])
    try:
        time.sleep(1.5)
        for t in x.cdp.send("Target.getTargets")["targetInfos"]:
            if "/welcome.html" in t["url"]: x.close_tab(t["targetId"])
        def reset(extra, settings):
            x.sw_eval("chrome.storage.local.clear().then(()=>chrome.storage.session.clear())")
            d = {"settings": dict({"countdownSec": 30, "sessionMin": 10, "stayMin": 5, "avgSessionMin": 15}, **settings)}; d.update(extra)
            x.sw_eval("chrome.storage.local.set(%s)" % json.dumps(d)); time.sleep(0.5)
        VW, VH = 1120, 572
        # 1: pause overlay mid-countdown with an intention typed
        reset({}, {"countdownSec": 30})
        tid, sid = x.new_tab("https://www.reddit.com/", VW, VH, dpr=2, wait=2.0)
        assert wait_for(lambda: overlay_text(x, sid), 8), "no overlay"
        cdp_text_into_shadow_input(x, sid, "Reply to one message"); time.sleep(2.0)
        x.shot(sid, os.path.join(RAW, "overlay-pause.png")); x.close_tab(tid)
        # 3: time-is-up overlay
        n = int(time.time() * 1000)
        reset({"sessions": {"reddit.com": {"startedAt": n - 597000, "until": n + 3000}}}, {"countdownSec": 5})
        tid, sid = x.new_tab("https://www.reddit.com/", VW, VH, dpr=2, wait=1.0)
        assert wait_for(lambda: "Your 10 minutes are up." in overlay_text(x, sid), 12), "no expiry overlay"
        time.sleep(1.0); x.shot(sid, os.path.join(RAW, "overlay-expired.png")); x.close_tab(tid)
        # 2: popup (fixed fake date: Fri 13 Nov 2026)
        n = int(time.time() * 1000)
        intents = [{"text": t, "site": "reddit.com", "at": n - i * 3600000} for i, t in enumerate(["Reply to one message", "Check the weekend plans", "Find one recipe"])]
        reset({"days": seed_days(), "totals": {"reclaimedMin": 255, "leaves": 17, "goIns": 21, "spentSec": 192 * 60}, "intentions": intents,
               "sites": [{"host": "youtube.com", "pathPrefix": "/shorts"}, {"host": "tiktok.com"}, {"host": "reddit.com"}, {"host": "x.com"}, {"host": "twitter.com"}, {"host": "instagram.com"}, {"host": "facebook.com"}, {"host": "feed.example.com"}],
               "rating": {"shown": True, "at": n}, "donation": {"asked": [], "lastAskAt": n, "dontAskAgain": True}}, {"countdownSec": 10, "sessionMin": 15, "avgSessionMin": 15})
        tid, sid = x.new_tab("chrome-extension://%s/popup.html" % x.id, 360, 700, dpr=2, fetch=False, pre_script=fake_date(2026, 11, 13), wait=2.0)
        h = x.ev(sid, "Math.ceil(document.body.getBoundingClientRect().height)", False)
        x.shot(sid, os.path.join(RAW, "popup.png"), clip={"x": 0, "y": 0, "width": 360, "height": h}); json.dump({"popup": [360, h]}, open(os.path.join(RAW, "sizes.json"), "w"))
        x.close_tab(tid)
        # 4/5: options
        tid, sid = x.new_tab("chrome-extension://%s/options.html" % x.id, 640, 1500, dpr=2, fetch=False, wait=2.0)
        r = json.loads(x.ev(sid, """JSON.stringify([...document.querySelectorAll('.card')].map(c=>{const r=c.getBoundingClientRect();return [r.left,r.top,r.width,r.height]}))""", False))
        sizes = json.load(open(os.path.join(RAW, "sizes.json")))
        for i, nm in ((0, "options-sites"), (1, "options-timing")):
            c_ = r[i]; x.shot(sid, os.path.join(RAW, nm + ".png"), clip={"x": c_[0] - 6, "y": c_[1] - 6, "width": c_[2] + 12, "height": c_[3] + 12}); sizes[nm] = [c_[2] + 12, c_[3] + 12]
        x.close_tab(tid)
        tid, sid = x.new_tab("chrome-extension://%s/options.html" % x.id, 440, 1500, dpr=3, fetch=False, wait=2.0)
        r = json.loads(x.ev(sid, """JSON.stringify([...document.querySelectorAll('.card')].map(c=>{const r=c.getBoundingClientRect();return [r.left,r.top,r.width,r.height]}))""", False))
        pr = r[2]; x.shot(sid, os.path.join(RAW, "privacy-card.png"), clip={"x": pr[0] - 12, "y": pr[1] - 12, "width": pr[2] + 24, "height": pr[3] + 24}); sizes["privacy"] = [pr[2] + 24, pr[3] + 24]
        json.dump(sizes, open(os.path.join(RAW, "sizes.json"), "w")); x.close_tab(tid)
        print("captured:", sizes)
    finally:
        x.close()

def compose():
    sizes = json.load(open(os.path.join(RAW, "sizes.json"))); icon = data_uri(ICON)
    U = lambda n: data_uri(os.path.join(RAW, n)); c = Composer()
    try:
        R = lambda html, w, h, name, **k: c.render(html, w, h, os.path.join(OUT, name), **k)
        R(wide(P, "A calm pause before the scroll.", browser(U("overlay-pause.png"), "feed.example.com"), icon), 1280, 800, "screenshot-1-pause.png")
        pw, ph = sizes["popup"]; R(side(P, "See the time you took back.", U("popup.png"), pw, ph, NAME, icon), 1280, 800, "screenshot-2-popup.png")
        R(wide(P, "Ten minutes, then a gentle check-in.", browser(U("overlay-expired.png"), "feed.example.com"), icon), 1280, 800, "screenshot-3-checkin.png")
        sw_, sh_ = sizes["options-sites"]; tw_, th_ = sizes["options-timing"]; k = 0.84
        two = ('<div style="width:1120px;height:610px;border-radius:26px;background:linear-gradient(160deg,#5E8F69,#2F5139);position:relative">'
               '<div style="position:absolute;left:%dpx;top:%dpx;width:%dpx;height:%dpx;border-radius:18px;overflow:hidden;box-shadow:0 22px 50px rgba(0,0,0,.35)"><img src="%s" style="width:100%%;height:100%%"></div>'
               '<div style="position:absolute;left:%dpx;top:%dpx;width:%dpx;height:%dpx;border-radius:18px;overflow:hidden;box-shadow:0 22px 50px rgba(0,0,0,.35)"><img src="%s" style="width:100%%;height:100%%"></div></div>') % (
            40, (610 - sh_ * k) / 2, sw_ * k, sh_ * k, U("options-sites.png"), 40 + sw_ * k + 36, (610 - th_ * k) / 2, tw_ * k, th_ * k, U("options-timing.png"))
        R(wide(P, "Your sites, your rules.", two, icon), 1280, 800, "screenshot-4-options.png")
        qw, qh = sizes["privacy"]
        R(privacy(P, "Your intentions stay on your device, and disappear after 7 days.", [("lock", "Stored only on this device"), ("clock", "Intentions deleted after 7 days"), ("ban", "No accounts, no ads, no tracking")], U("privacy-card.png"), qw, qh, icon, NAME), 1280, 800, "screenshot-5-privacy.png")
        R(promo_small(P, NAME, "Stop doomscrolling", "Take your time back.", icon), 440, 280, "promo-small-440x280.png")
        R(promo_marquee(P, NAME, "Stop doomscrolling", "Take your time back.", icon, U("popup.png"), pw, ph), 1400, 560, "promo-marquee-1400x560.png")
        R(store_icon(icon), 128, 128, "store-icon-128.png", transparent=True)
    finally:
        c.close()
    print("\n".join(finish_check(OUT)))

if __name__ == "__main__":
    a = [x for x in sys.argv[1:]] or ["capture", "compose"]
    if "capture" in a: capture()
    if "compose" in a: compose()
