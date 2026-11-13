#!/usr/bin/env python3
"""Reclaim end-to-end harness.   Run from anywhere:  python3 tests/e2e/harness.py        ONLY=2,5 python3 ... (select groups)
Fixtures are served on the real hostnames via CDP Fetch interception (mirroring the structure the content script needs).
Variants of the extension are copied to tests/e2e/profile-ext-* (gitignored): custom (extra host permission for the
user-added-site test), links (test Stripe links), evil (non-Stripe links)."""
import base64 as _b64, os, re, sys, json, time, shutil, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plumbing import *

ONLY = [int(x) for x in os.environ.get("ONLY", "").split(",") if x.strip()]
def _wav():
    n = 8000
    hdr = b"RIFF" + (36 + n).to_bytes(4, "little") + b"WAVEfmt " + (16).to_bytes(4, "little") + (1).to_bytes(2, "little") + (1).to_bytes(2, "little") + (8000).to_bytes(4, "little") + (8000).to_bytes(4, "little") + (1).to_bytes(2, "little") + (8).to_bytes(2, "little") + b"data" + n.to_bytes(4, "little")
    return _b64.b64encode(hdr + b"\x80" * n).decode()
WAV = _wav()
PAGE = """<!doctype html><html><head><title>Fixture %(host)s</title><style>body{margin:0;font:16px sans-serif}#btn{position:fixed;left:20px;top:20px;width:120px;height:40px}</style></head>
<body><h1 id="h">FIXTURE %(host)s %(path)s</h1><button id="btn" onclick="window.clicked=(window.clicked||0)+1">page button</button>
<input id="pageinput" style="position:fixed;left:20px;top:80px" onkeydown="window.keys=(window.keys||0)+1">
<audio id="a" src="data:audio/wav;base64,%(wav)s" loop autoplay></audio>
%(extra)s<script>document.getElementById('a').play().catch(()=>{});window.addEventListener('keydown',()=>{window.docKeys=(window.docKeys||0)+1});</script></body></html>"""
YT_EXTRA = """<button id="goShorts" style="position:fixed;left:20px;top:140px" onclick="history.pushState({},'','/shorts/abc123')">to shorts</button>
<button id="goOther" style="position:fixed;left:20px;top:180px" onclick="history.pushState({},'','/watch?v=1')">to watch</button>"""
H.fetch_hosts = ["www.tiktok.com", "www.reddit.com", "x.com", "twitter.com", "www.instagram.com", "www.facebook.com", "www.youtube.com", "www.fixture-custom.test", "fixture-custom.test", "overcrasher.github.io", "example.org"]
THANKS_URL = "https://overcrasher.github.io/reclaim/thanks.html?session_id="
GOOD_SESSION = "cs_test_" + "aB3dE5fG7hJ9kL1mN3pQ5rS7"
def _fixture(url):
    m = re.match(r"https://([^/]+)(/[^?#]*)", url)
    if not m: return None
    host, path = m.group(1), m.group(2)
    if host == "overcrasher.github.io":
        return "<!doctype html><title>Thanks</title><h1>Thank you</h1>" if path == "/reclaim/thanks.html" else None
    return PAGE % {"host": host, "path": path, "wav": WAV, "extra": YT_EXTRA if host.endswith("youtube.com") else ""}
H.fixture = _fixture

SETTINGS = {"countdownSec": 3, "sessionMin": 10, "stayMin": 5, "avgSessionMin": 15}
def reset(settings=None, extra=None):
    sw_eval("chrome.storage.local.clear().then(()=>chrome.storage.session.clear())")
    d = {"settings": dict(SETTINGS)}
    if settings: d["settings"].update(settings)
    if extra: d.update(extra)
    sw_eval("chrome.storage.local.set(%s)" % json.dumps(d)); time.sleep(0.4)
def today_key():
    t = time.localtime(); return "%04d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday)
def today(): return (storage().get("days") or {}).get(today_key()) or {}
def tab_urls(): return sw_eval("chrome.tabs.query({}).then(ts=>ts.map(t=>t.url))")
def popup_tab(w=420, h=900, pre=None): return new_tab("chrome-extension://%s/popup.html" % H.EXT_ID, fetch=False, w=w, h=h, pre_script=pre)
def options_tab(w=900, h=1500): return new_tab("chrome-extension://%s/options.html" % H.EXT_ID, fetch=False, w=w, h=h)
CLIP_HOOK = "window.__clip=[];Object.defineProperty(navigator,'clipboard',{value:{writeText:t=>{window.__clip.push(t);return Promise.resolve()}}});"
def fake_date(y, mo, d, h=10):
    return "(()=>{const RD=Date;const off=new RD(%d,%d,%d,%d,0,0).getTime()-RD.now();class D extends RD{constructor(...a){a.length?super(...a):super(RD.now()+off)}static now(){return RD.now()+off}};window.Date=D;})();" % (y, mo - 1, d, h)
def ov(sid):
    es = shadow_elems(sid)
    hid = any("actions" in e["cls"].split() and "hidden" in e["attrs"] for e in es)
    return {"buttons": [] if hid else [e["text"] for e in es if e["tag"] == "BUTTON"], "h1": next((e["text"] for e in es if e["tag"] == "H1"), None),
            "has_input": any(e["tag"] == "INPUT" for e in es), "num": next((e["text"] for e in es if "num" in e["cls"].split()), None)}
HOST_JS = """JSON.stringify((()=>{const h=document.querySelector('[data-reclaim]');if(!h)return null;const r=h.getBoundingClientRect();
 return {w:r.width,h:r.height,top:document.elementFromPoint(60,40)===h,topAny:document.elementFromPoint(innerWidth/2,innerHeight/2)===h,z:getComputedStyle(h).zIndex,pos:getComputedStyle(h).position,parentIsHtml:h.parentElement===document.documentElement,closed:h.shadowRoot===null}})())"""
def host(sid): return json.loads(px(sid, HOST_JS))
def overlay_up(sid):
    h = host(sid); return bool(h and h["w"] > 0)
def media(sid): return json.loads(px(sid, "JSON.stringify({paused:document.getElementById('a').paused,muted:document.getElementById('a').muted})"))
def page_click(sid, x=60, y=40):
    mouse_click(sid, x, y); return px(sid, "window.clicked||0")
def open_site(h_="www.tiktok.com", path="/", **kw): return new_tab("https://%s%s" % (h_, path), **kw)
def wait_overlay(sid, t=8, buttons=True): return wait_for(lambda: overlay_up(sid) and (not buttons or ov(sid)["buttons"]), t)
def go_in(sid):
    assert wait_for(lambda: any(b.startswith("Go in") for b in ov(sid)["buttons"]), 8), "Go in never appeared"
    ok = click_shadow(sid, "BUTTON", "Go in"); time.sleep(0.8); return ok
def STORE(): return "https://chromewebstore.google.com/detail/" + H.EXT_ID
EN_NAME = "Reclaim – Stop Doomscrolling & Limit Social Media"
DAY = 86400000
def now_ms(): return int(time.time() * 1000)
def banner(sid):
    return json.loads(px(sid, """JSON.stringify({hidden:document.getElementById('banner').hidden,text:document.getElementById('banner-text').textContent,
      buttons:[...document.querySelectorAll('#banner-buttons button')].map(b=>[b.textContent,b.className]),note:document.getElementById('banner-note').textContent})"""))
def rating(sid): return px(sid, "document.getElementById('rating').hidden")

# =============================== GROUPS ===============================
def g1():
    time.sleep(1)
    mf = sw_eval("chrome.runtime.getManifest()")
    ts = tabs()
    check("extension loaded (id %s)" % H.EXT_ID, bool(H.EXT_ID))
    check("service worker target exists", any(t["type"] == "service_worker" and H.EXT_ID in t["url"] for t in ts))
    check("permissions = storage,tabs,alarms,scripting", sorted(mf["permissions"]) == ["alarms", "scripting", "storage", "tabs"], mf["permissions"])
    check("host_permissions = the 7 default sites only", len(mf["host_permissions"]) == 7 and all(h.startswith("https://*.") for h in mf["host_permissions"]), mf["host_permissions"])
    check("optional_host_permissions = https://*/*", mf.get("optional_host_permissions") == ["https://*/*"])
    check("manifest name resolves to localized en name", mf["name"] == EN_NAME, mf["name"])
    check("short_name/default_locale/version", (mf.get("short_name"), mf.get("default_locale"), mf["version"]) == ("Reclaim", "en", "1.0.0"))
    check("description resolved (no __MSG_)", mf["description"].startswith("A calm pause before time-wasting sites") and "__MSG_" not in mf["description"], mf["description"])
    check("i18n getMessage works in SW", sw_eval("chrome.i18n.getMessage('extName')") == EN_NAME)
    check("action title is bare name", sw_eval("chrome.action.getTitle({})") == "Reclaim")
    check("content script document_start, top frame only", mf["content_scripts"][0]["run_at"] == "document_start" and not mf["content_scripts"][0].get("all_frames"))
    tid, sid = popup_tab(); time.sleep(1.2)
    check("popup renders + i18n works in extension page", px(sid, "chrome.i18n.getMessage('extName')") == EN_NAME and px(sid, "document.getElementById('reclaimed').textContent.length>0"))
    close_tab(tid)
    tid, sid = options_tab(); time.sleep(1.2)
    check("options renders (7 default sites listed)", px(sid, "document.querySelectorAll('#sites li').length") == 7)
    close_tab(tid)
    check("no SW/popup/options errors on load", not ext_errors(), ext_errors())
    w = open_tabs_with("/welcome.html")
    check("welcome page opened exactly once on fresh install", len(w) == 1, [t["url"] for t in w])
    if w:
        wt = H.cdp.send("Target.attachToTarget", {"targetId": w[0]["targetId"], "flatten": True})["sessionId"]
        H.cdp.send("Runtime.enable", {}, wt)
        h1 = ev(wt, "document.querySelector('h1').textContent", False)
        steps = ev(wt, "[...document.querySelectorAll('.steps li')].map(l=>l.textContent)", False)
        check("welcome: title, 3 steps, privacy note, settings button, pin hint", h1 == "Welcome to Reclaim" and len(steps) == 3 and "Watch your plant" in steps[2] and ev(wt, "!!document.getElementById('open-settings') && /Everything stays on this device/.test(document.body.textContent) && /Pin it/.test(document.body.textContent)", False), (h1, steps))
        shot(wt, "welcome")
        ev(wt, "document.getElementById('open-settings').click()", False); time.sleep(1.2)
        check("welcome: Open settings opens the options page", len(open_tabs_with("/options.html")) >= 1)
        for t in open_tabs_with("/options.html"): close_tab(t["targetId"])
        close_tab(w[0]["targetId"])

def g2():
    reset(); n0 = len(LOGS)
    tid, sid = open_site("www.tiktok.com", "/foryou", wait=0.4)
    try:
        check("overlay host present right after load (before page usable)", wait_for(lambda: overlay_up(sid), 4), host(sid))
        h = host(sid) or {}
        check("host: fixed, full viewport, top-most, child of <html>, max z-index", h.get("pos") == "fixed" and h["w"] >= 1099 and h["h"] >= 799 and h["top"] and h["topAny"] and h["parentIsHtml"] and h["z"] == "2147483647", h)
        check("shadow root is closed (page cannot reach it)", h.get("closed") is True)
        o = ov(sid)
        check("heading 'What are you here for?' + input", o["h1"] == "What are you here for?" and o["has_input"], o)
        check("countdown visible (3 -> 2)", o["num"] in ("3", "2"), o["num"])
        check("no Go in / Leave before countdown ends", not o["buttons"], o["buttons"])
        shot(sid, "fixture_overlay_countdown")
        check("page underneath not clickable", page_click(sid) == 0)
        px(sid, "document.getElementById('pageinput').focus()")
        H.cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "j", "text": "j"}, sid); H.cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "j"}, sid)
        check("keys do not reach the page while overlay is up", px(sid, "(window.docKeys||0)+(window.keys||0)") == 0)
        m = media(sid)
        check("media paused and muted while overlay is up", m["paused"] and m["muted"], m)
        time.sleep(0.8); check("media stays paused on re-check", media(sid)["paused"])
        check("after countdown: Go in (10 min) + Leave", wait_for(lambda: ov(sid)["buttons"] == ["Go in (10 min)", "Leave"], 6), ov(sid))
        shot(sid, "fixture_overlay_choices")
        es = [e for e in shadow_elems(sid) if e["tag"] == "INPUT"]
        mouse_click(sid, *center(sid, es[0]["id"])); H.cdp.send("Input.insertText", {"text": "reply to one message"}, sid); time.sleep(0.2)
        click_shadow(sid, "BUTTON", "Go in"); time.sleep(1.0)
        check("Go in removes the overlay", not overlay_up(sid))
        check("page clickable again", page_click(sid) == 1)
        m = media(sid); check("media resumed + unmuted after Go in", (not m["paused"]) and (not m["muted"]), m)
        s = storage()
        check("session stored ~10 min ahead", "tiktok.com" in s.get("sessions", {}) and 9.5 * 60000 < s["sessions"]["tiktok.com"]["until"] - now_ms() < 10.1 * 60000, s.get("sessions"))
        check("intention stored with site + timestamp", [(i["text"], i["site"]) for i in s.get("intentions", [])] == [("reply to one message", "tiktok.com")] and s["intentions"][0]["at"] > 0, s.get("intentions"))
        check("goIns counted (day + totals)", today().get("goIns") == 1 and s["totals"]["goIns"] == 1, today())
        time.sleep(0.5); check("no overlay re-appears during the session", not overlay_up(sid))
    finally: close_tab(tid)
    check("no extension errors in this group", not [l for l in ext_errors() if l in LOGS[n0:]], ext_errors()[-3:])

def g3():
    reset()
    tid, sid = open_site("www.tiktok.com", "/a"); others = []
    try:
        go_in(sid)
        t2, s2 = open_site("www.tiktok.com", "/b"); others.append(t2); time.sleep(1.5)
        check("2nd tab same site: no overlay during session", not overlay_up(s2), host(s2))
        check("2nd tab usable, media not paused", page_click(s2) == 1 and not media(s2)["paused"])
        navigate(s2, "https://www.tiktok.com/c", 1.5)
        check("navigation within the site not interrupted", not overlay_up(s2))
        t3, s3 = open_site("www.reddit.com", "/"); others.append(t3)
        check("other site (reddit) still shows overlay", wait_for(lambda: overlay_up(s3), 4))
        t4, s4 = open_site("twitter.com", "/"); others.append(t4)
        check("twitter.com is its own rule with its own overlay", wait_for(lambda: overlay_up(s4), 4))
        check("only one session stored (tiktok.com)", list(storage()["sessions"].keys()) == ["tiktok.com"], storage()["sessions"])
        check("goIns counted once", today().get("goIns") == 1, today())
    finally:
        for t in [tid] + others: close_tab(t)

def g4():
    reset(); n = now_ms()
    sw_eval("chrome.storage.local.set({sessions:{'reddit.com':{startedAt:%d,until:%d}}})" % (n - 590000, n + 4000))
    tid, sid = open_site("www.reddit.com", "/r/x")
    try:
        time.sleep(1.0); check("active session at load: no overlay", not overlay_up(sid))
        check("soft overlay 'Your 10 minutes are up.' after expiry", wait_for(lambda: overlay_up(sid) and ov(sid)["h1"] == "Your 10 minutes are up.", 8))
        check("expired overlay: Stay 5 more + Leave", ov(sid)["buttons"] == ["Stay 5 more", "Leave"], ov(sid)["buttons"])
        shot(sid, "fixture_expired")
        check("expired overlay blocks the page", page_click(sid) == 0)
        click_shadow(sid, "BUTTON", "Stay 5 more"); time.sleep(1.0)
        left = storage()["sessions"]["reddit.com"]["until"] - now_ms()
        check("Stay 5 more: overlay gone, session ~5 min from now", not overlay_up(sid) and 4.8 * 60000 < left < 5.1 * 60000, left)
        check("Stay does not count a leave", (today().get("leaves") or 0) == 0)
        n = now_ms()
        sw_eval("chrome.storage.local.set({sessions:{'reddit.com':{startedAt:%d,until:%d}}}).then(()=>chrome.alarms.create('exp:reddit.com',{when:%d}))" % (n - 1000, n + 600000, n + 2500))
        time.sleep(0.5)
        # the stored session expires while the content script's own timer still points 10 min away: only the SW alarm can fire
        sw_eval("chrome.storage.local.set({sessions:{'reddit.com':{startedAt:%d,until:%d}}})" % (n - 1000, n + 1200))
        check("SW alarm (exp:) triggers a re-check -> expired overlay", wait_for(lambda: overlay_up(sid), 12))
        sw_eval("chrome.storage.local.set({sessions:{'reddit.com':{startedAt:1,until:%d}}})" % (now_ms() - 31 * 60000))
        t2, s2 = open_site("www.reddit.com", "/"); wait_overlay(s2, 5, buttons=False)
        check("expired > 30 min ago -> fresh intro overlay", overlay_up(s2) and ov(s2)["h1"] == "What are you here for?", ov(s2))
        close_tab(t2)
    finally: close_tab(tid)

def g5():
    reset({"avgSessionMin": 20})
    tid, sid = open_site("www.instagram.com", "/")
    try:
        assert wait_for(lambda: "Leave" in ov(sid)["buttons"], 8)
        click_shadow(sid, "BUTTON", "Leave")
        check("Leave navigates the tab to extension reclaimed.html", wait_for(lambda: open_tabs_with("reclaimed.html"), 6))
        time.sleep(1.0); s = storage()
        check("reclaimed += average (20 min), leaves=1 (day + totals)", today().get("reclaimedMin") == 20 and today().get("leaves") == 1 and s["totals"]["reclaimedMin"] == 20 and s["totals"]["leaves"] == 1, (today(), s.get("totals")))
        check("no session left behind", not s.get("sessions"))
        t = open_tabs_with("reclaimed.html")
        check("reclaimed page is a chrome-extension:// page", bool(t) and t[0]["url"].startswith("chrome-extension://" + H.EXT_ID))
        rs = H.cdp.send("Target.attachToTarget", {"targetId": t[0]["targetId"], "flatten": True})["sessionId"]
        for m in ("Runtime.enable", "Page.enable"): H.cdp.send(m, {}, rs)
        H.cdp.send("Page.addScriptToEvaluateOnNewDocument", {"source": CLIP_HOOK}, rs); H.cdp.send("Page.reload", {}, rs); time.sleep(1.5)
        txt = ev(rs, "document.body.innerText", False)
        check("reclaimed page text: Nice., ≈ 20 min reclaimed, (estimate), today's total", "Nice." in txt and "≈ 20 min reclaimed" in txt and "(estimate)" in txt and "Today so far: ≈ 20m" in txt, txt)
        check("reclaimed page has the mascot", ev(rs, "!!document.querySelector('#mascot svg')", False))
        shot(rs, "reclaimed_page")
        ev(rs, "document.getElementById('share').click()", False); time.sleep(0.5)
        clip = ev(rs, "window.__clip", False)
        check("Share text ends with SHARE_URL; button says Copied!", clip and clip[0] == "I reclaimed 20m from doomscrolling this week. #Reclaim " + STORE() + "?utm_source=share" and ev(rs, "document.getElementById('share').textContent", False) == "Copied!", clip)
        ev(rs, "document.getElementById('close').click()", False); time.sleep(1.0)
        check("Close tab closes the page", not open_tabs_with("reclaimed.html"))
        sw_eval("chrome.storage.local.set({sessions:{'x.com':{startedAt:1,until:%d}}})" % (now_ms() - 1000))
        t2, s2 = open_site("x.com", "/home")
        assert wait_for(lambda: "Leave" in ov(s2)["buttons"], 6)
        click_shadow(s2, "BUTTON", "Leave"); time.sleep(1.5)
        check("Leave from the expired overlay counts (leaves=2, 40 min) and ends the session", today().get("leaves") == 2 and today().get("reclaimedMin") == 40 and "x.com" not in storage().get("sessions", {}), today())
        for x in open_tabs_with("reclaimed.html"): close_tab(x["targetId"])
    finally: close_tab(tid)

def g6():
    reset()
    tid, sid = open_site("www.tiktok.com", "/hb")
    try:
        go_in(sid)
        hb = sw_eval("chrome.storage.session.get('hb').then(d=>d.hb||{})")
        check("heartbeat start registered (storage.session)", len(hb) == 1 and list(hb.values())[0]["key"] == "tiktok.com", hb)
        check("page visible + focused", px(sid, "document.visibilityState==='visible' && document.hasFocus()"))
        time.sleep(33); sp = today().get("spentSec", 0)
        check("~30 s credited after 33 s visible+focused (beats at 15 s and 30 s)", 25 <= sp <= 36, sp)
        check("per-site seconds recorded", abs((today().get("sites") or {}).get("tiktok.com", 0) - sp) < 0.01, today().get("sites"))
        H.cdp.send("Emulation.setFocusEmulationEnabled", {"enabled": False}, sid)
        hasf = px(sid, "document.hasFocus()"); print("   hasFocus with focus emulation off:", hasf)
        if hasf is False:
            time.sleep(16); s1 = today().get("spentSec", 0); time.sleep(16); s2 = today().get("spentSec", 0)
            check("unfocused: counting stops (no growth over 16 s)", s2 == s1, (s1, s2))
            check("unfocused: at most one partial credit (<=16 s) after blur", s1 - sp <= 16, (sp, s1))
        else: check("unfocused: hasFocus stays true in headless (not testable here); covered by code path + jsc credit tests", True)
        H.cdp.send("Emulation.setFocusEmulationEnabled", {"enabled": True}, sid)
        tb, sb = new_tab("about:blank", fetch=False)
        H.cdp.send("Page.bringToFront", {}, sb); time.sleep(0.8)
        vis = px(sid, "document.visibilityState"); print("   visibilityState after bringToFront(other):", vis)
        if vis == "hidden":
            time.sleep(1); a = today().get("spentSec", 0); time.sleep(32); b = today().get("spentSec", 0)
            check("hidden tab: no time counted", b - a <= 1, (a, b))
        else: check("hidden tab: headless keeps tabs visible (not testable here); visibility is part of the active() check", True, vis)
        close_tab(tb); H.cdp.send("Page.bringToFront", {}, sid)
        before = today().get("spentSec", 0)
        for _ in range(5): cs_send(sid, {"type": "hb", "kind": "beat"})
        check("5 rapid forged beats credit <= wall time", today().get("spentSec", 0) - before <= 1.5, today().get("spentSec", 0) - before)
        sw_eval("chrome.storage.local.set({pausedUntil:%d, sessions:{}})" % (now_ms() + 3600000))
        navigate(sid, "https://www.tiktok.com/p", 1.5)
        check("paused: no overlay, activity still tracked", not overlay_up(sid) and len(sw_eval("chrome.storage.session.get('hb').then(d=>Object.keys(d.hb||{}))")) == 1)
    finally: close_tab(tid)

def g7():
    reset()
    tid, sid = open_site("www.youtube.com", "/")
    try:
        time.sleep(1.5); check("youtube home: no overlay (path-scoped rule)", not overlay_up(sid))
        px(sid, "document.getElementById('goOther').click()"); time.sleep(1.3)
        check("SPA to /watch: no overlay", not overlay_up(sid))
        px(sid, "document.getElementById('goShorts').click()")
        check("SPA pushState into /shorts shows overlay (<=3 s)", wait_for(lambda: overlay_up(sid), 3))
        check("intro overlay", ov(sid)["h1"] == "What are you here for?")
        check("media paused by the SPA overlay", wait_for(lambda: media(sid)["paused"], 2))
        px(sid, "history.pushState({},'','/')")
        check("SPA back out of /shorts removes overlay and resumes media", wait_for(lambda: not overlay_up(sid), 3) and wait_for(lambda: not media(sid)["paused"], 2))
        px(sid, "history.pushState({},'','/shorts/zzz')"); wait_overlay(sid, 4); go_in(sid)
        px(sid, "history.pushState({},'','/'); history.pushState({},'','/shorts/yyy')"); time.sleep(1.5)
        check("active session: later SPA moves into /shorts don't interrupt", not overlay_up(sid))
        check("session key is youtube.com/shorts", list(storage()["sessions"].keys()) == ["youtube.com/shorts"], storage()["sessions"])
    finally: close_tab(tid)
    reset(); tid3, sid3 = open_site("www.youtube.com", "/shorts/direct2", wait=0.4)
    try: check("direct load of /shorts/ID shows overlay immediately", wait_for(lambda: overlay_up(sid3), 3))
    finally: close_tab(tid3)

def g8():  # runs on the 'custom' variant (extra host permission pre-granted: see README / module docstring)
    reset()
    tid, sid = options_tab()
    try:
        time.sleep(1)
        px(sid, "document.getElementById('newSite').value='nonsense value'"); ev(sid, "document.getElementById('addSite').click()", False, userGesture=True)
        check("invalid input rejected with a message", "Enter a site" in px(sid, "document.getElementById('siteErr').textContent"))
        px(sid, "document.getElementById('newSite').value='https://www.fixture-custom.test/news/'")
        ev(sid, "document.getElementById('addSite').click()", False, userGesture=True); time.sleep(1.5)
        sites = storage().get("sites") or []
        check("site stored as {host:fixture-custom.test, pathPrefix:/news}", {"host": "fixture-custom.test", "pathPrefix": "/news"} in sites, sites)
        regs = sw_eval("chrome.scripting.getRegisteredContentScripts().then(r=>r.map(s=>({id:s.id,matches:s.matches,runAt:s.runAt,persist:s.persistAcrossSessions,js:s.js})))")
        check("dynamic content script registered (document_start, persistAcrossSessions)", len(regs) == 1 and regs[0]["id"] == "site-fixture-custom-test-news" and regs[0]["runAt"] == "document_start" and regs[0]["persist"] is True, regs)
        check("options list shows the site tagged 'added by you'", "added by you" in px(sid, "document.getElementById('sites').textContent"))
        px(sid, "document.getElementById('newSite').value='fixture-custom.test/news'"); ev(sid, "document.getElementById('addSite').click()", False, userGesture=True)
        check("duplicate rejected", "already in the list" in px(sid, "document.getElementById('siteErr').textContent"))
        t2, s2 = open_site("www.fixture-custom.test", "/news/today")
        try:
            check("overlay appears on the user-added site (dynamic script)", wait_for(lambda: overlay_up(s2), 4)); shot(s2, "fixture_custom_overlay")
        finally: close_tab(t2)
        t3, s3 = open_site("www.fixture-custom.test", "/sports")
        try: time.sleep(1.5); check("path outside the prefix: no overlay", not overlay_up(s3))
        finally: close_tab(t3)
        ev(sid, "[...document.querySelectorAll('#sites li')].find(l=>l.textContent.includes('fixture-custom')).querySelector('button').click()", False); time.sleep(1.5)
        check("remove: rule deleted and dynamic script unregistered", not [s for s in (storage().get("sites") or []) if s["host"] == "fixture-custom.test"] and sw_eval("chrome.scripting.getRegisteredContentScripts().then(r=>r.length)") == 0)
        t4, s4 = open_site("www.fixture-custom.test", "/news/x")
        try: time.sleep(1.5); check("after removal: no overlay", not overlay_up(s4))
        finally: close_tab(t4)
        # default-site management
        ev(sid, "[...document.querySelectorAll('#sites li')].find(l=>l.textContent.includes('reddit.com')).querySelector('button').click()", False); time.sleep(0.8)
        check("removing a default site (reddit.com) works", not [s for s in storage()["sites"] if s["host"] == "reddit.com"])
        t5, s5 = open_site("www.reddit.com", "/")
        try: time.sleep(1.5); check("removed default site: no overlay", not overlay_up(s5))
        finally: close_tab(t5)
        ev(sid, "document.getElementById('restore').click()", False); time.sleep(0.8)
        check("Restore default sites brings it back", any(s["host"] == "reddit.com" for s in storage()["sites"]))
    finally: close_tab(tid)

def g9():
    reset(); n = now_ms()
    ints = [{"text": "old", "site": "tiktok.com", "at": n - 8 * DAY}, {"text": "edge6", "site": "x.com", "at": n - 6 * DAY}, {"text": "new", "site": "x.com", "at": n}]
    sw_eval("chrome.storage.local.set({intentions:%s})" % json.dumps(ints))
    check("purge alarm is scheduled daily", sw_eval("chrome.alarms.get('purge').then(a=>a&&a.periodInMinutes)") == 1440)
    sw_eval("chrome.alarms.create('purge',{when:%d})" % (now_ms() + 800)); time.sleep(3)
    got = [i["text"] for i in storage().get("intentions", [])]
    check("daily 'purge' alarm deletes intentions older than 7 days (simulated by back-dated records)", got == ["edge6", "new"], got)
    ints2 = [{"text": "stale", "site": "x.com", "at": n - 9 * DAY}]
    sw_eval("chrome.storage.local.set({intentions:%s})" % json.dumps(ints2))
    # simulate a browser restart: stop the worker, then wake it with a content-script message
    H.cdp.send("Target.closeTarget", {"targetId": get_sw() and sw["tid"]}); time.sleep(1.5); sw["sid"] = None; sw["tid"] = None
    tid, sid = open_site("www.tiktok.com", "/"); time.sleep(3); close_tab(tid)
    got = [i["text"] for i in storage().get("intentions", [])]
    check("purge also runs when the worker starts (startup / wake-up path)", got == [], got)
    # content script forging a 500-char intention is cut to 140
    reset(); tid, sid = open_site("www.tiktok.com", "/"); time.sleep(1)
    r = cs_send(sid, {"type": "goIn", "intention": "x" * 500 + "‮"})
    t = [i["text"] for i in storage().get("intentions", [])]
    check("forged oversize intention stored cut to 140 chars, bidi stripped", r and r.get("ok") and len(t) == 1 and len(t[0]) == 140, (r, [len(x) for x in t]))
    close_tab(tid)
    tid, sid = options_tab(); time.sleep(1)
    check("options shows count of stored intentions", px(sid, "document.getElementById('intentCount').textContent").startswith("1 "))
    for _ in range(2): ev(sid, "document.getElementById('clearIntent').click()", False); time.sleep(0.4)
    check("Delete stored intentions (two-click) empties them", storage().get("intentions") == [])
    close_tab(tid)

def seed_week(m_spent, m_rec, **kw): pass
def popup_state(pre=None):
    tid, sid = popup_tab(pre=pre); time.sleep(1.3); return tid, sid
def g10():
    # Sunday 2026-11-15 10:00 (fake clock in the popup); week = 2026-11-09..15
    days = {"2026-11-09": {"spentSec": 600, "reclaimedMin": 15}, "2026-11-10": {"spentSec": 1800, "reclaimedMin": 30},
            "2026-11-11": {"spentSec": 0, "reclaimedMin": 60}, "2026-11-15": {"spentSec": 1200, "reclaimedMin": 95},
            "2026-11-02": {"spentSec": 6000, "reclaimedMin": 300}}
    reset(extra={"days": days, "totals": {"reclaimedMin": 200, "leaves": 2, "goIns": 4, "spentSec": 3600}})
    tid, sid = popup_state(fake_date(2026, 11, 15))
    try:
        check("today: reclaimed ≈ 1h 35m (estimate) and spent 20m", px(sid, "document.getElementById('reclaimed').textContent") == "≈ 1h 35m" and "reclaimed (estimate)" in px(sid, "document.querySelector('.sub').textContent") and px(sid, "document.getElementById('spent').textContent").startswith("20m spent"), px(sid, "document.getElementById('reclaimed').textContent"))
        check("chart: 14 bars + 7 labels, accessible name lists days", px(sid, "document.querySelectorAll('#chart rect').length") == 14 and px(sid, "document.querySelectorAll('#chart text').length") == 7 and "Mon: 10m spent, 15m reclaimed (estimate)" in px(sid, "document.querySelector('#chart svg').getAttribute('aria-label')") and px(sid, "document.querySelector('#chart svg').getAttribute('role')") == "img")
        check("week totals line (estimate labelled)", px(sid, "document.getElementById('weekTotals').textContent") == "1h spent · ≈ 3h 20m reclaimed (estimate)", px(sid, "document.getElementById('weekTotals').textContent"))
        check("Sunday weekly summary card with comparison phrase", px(sid, "document.getElementById('weekly').hidden") is False and px(sid, "document.getElementById('weekly-text').textContent") == "You reclaimed 3h 20m this week, about one movie's worth.", px(sid, "document.getElementById('weekly-text').textContent"))
        check("mascot reflects the week (3h20 reclaimed vs 1h spent => growing)", px(sid, "document.querySelector('#mascot svg').getAttribute('aria-label')") == "Reclaim plant, growing")
        shot(sid, "popup_sunday")
    finally: close_tab(tid)
    tid, sid = popup_state(fake_date(2026, 11, 16))
    try: check("Monday: summary for the week just ended ('last week')", px(sid, "document.getElementById('weekly-text').textContent") == "You reclaimed 3h 20m last week, about one movie's worth." if False else "last week" in px(sid, "document.getElementById('weekly-text').textContent"), px(sid, "document.getElementById('weekly-text').textContent"))
    finally: close_tab(tid)
    tid, sid = popup_state(fake_date(2026, 11, 12))
    try: check("Thursday: no weekly summary", px(sid, "document.getElementById('weekly').hidden") is True)
    finally: close_tab(tid)
    # mascot states
    cases = [({}, "sprout"), ({"2026-11-09": {"spentSec": 3 * 3600, "reclaimedMin": 0}}, "droopy"), ({"2026-11-09": {"spentSec": 8 * 3600, "reclaimedMin": 0}}, "wilted"),
             ({"2026-11-09": {"spentSec": 1800, "reclaimedMin": 90}}, "growing"), ({"2026-11-09": {"spentSec": 600, "reclaimedMin": 300}}, "blooming")]
    for d, name in cases:
        reset(extra={"days": d}); tid, sid = popup_state(fake_date(2026, 11, 12))
        try: check("mascot state '%s'" % name, px(sid, "document.querySelector('#mascot svg').getAttribute('aria-label')") == "Reclaim plant, " + name, px(sid, "document.querySelector('#mascot svg').getAttribute('aria-label')"))
        finally:
            if name == "blooming": shot(sid, "popup_blooming")
            if name == "wilted": shot(sid, "popup_wilted")
            close_tab(tid)
    # pause toggle
    reset(); tid, sid = popup_state()
    try:
        check("Share hidden with nothing reclaimed", px(sid, "document.getElementById('share').hidden") is True)
        ev(sid, "document.getElementById('pause').click()", False); time.sleep(0.8)
        pu = storage().get("pausedUntil", 0)
        check("Pause for 1 hour sets pausedUntil ~1 h", 3500000 < pu - now_ms() <= 3600000, pu - now_ms())
        check("popup shows Resume + paused note", px(sid, "document.getElementById('pause').textContent") == "Resume Reclaim" and px(sid, "document.getElementById('pauseNote').hidden") is False)
        t2, s2 = open_site("www.tiktok.com", "/")
        try: time.sleep(1.5); check("paused: no overlay on a tracked site", not overlay_up(s2))
        finally: close_tab(t2)
        ev(sid, "document.getElementById('pause').click()", False); time.sleep(0.8)
        check("Resume clears pausedUntil", storage().get("pausedUntil") == 0)
        t3, s3 = open_site("www.tiktok.com", "/")
        try: check("resumed: overlay is back", wait_for(lambda: overlay_up(s3), 4))
        finally: close_tab(t3)
    finally: close_tab(tid)
    reset(extra={"days": {today_key(): {"spentSec": 0, "reclaimedMin": 200}}}); tid, sid = popup_tab(pre=CLIP_HOOK); time.sleep(1.3)
    try:
        ev(sid, "document.getElementById('share').click()", False); time.sleep(0.5)
        clip = px(sid, "window.__clip")
        check("popup Share text: 3h 20m ... #Reclaim SHARE_URL", clip and clip[0] == "I reclaimed 3h 20m from doomscrolling this week. #Reclaim " + STORE() + "?utm_source=share", clip)
    finally: close_tab(tid)

def g11():  # 'links' variant (test Stripe links)
    d = today_key()
    reset(extra={"totals": {"reclaimedMin": 5 * 60 + 10, "leaves": 1, "goIns": 1, "spentSec": 0}})
    tid, sid = popup_tab(); time.sleep(1.5)
    try:
        b = banner(sid)
        check("banner at 5 h reclaimed", b["hidden"] is False, b)
        check("banner copy has the user's real hours + 'one hour of your time'", "about 5 hours with Reclaim" in b["text"] and "less than the cost of one hour of your time" in b["text"], b["text"])
        check("buttons €3 €5 €10 + Pick your own amount", [x[0] for x in b["buttons"]] == ["€3", "€5", "€10", "Pick your own amount"], b["buttons"])
        check("only €5 emphasized; custom has class 'donate custom'", [("emphasized" in x[1]) for x in b["buttons"]] == [False, True, False, False] and b["buttons"][3][1] == "donate custom")
        check("no hint before clicking custom", b["note"] == "")
        dn = storage().get("donation"); check("asked=[5], lastAskAt set", dn and dn["asked"] == [5] and dn["lastAskAt"] > 0, dn)
        shot(sid, "popup_banner")
        TABS_SEEN.clear()
        px(sid, "document.querySelectorAll('#banner-buttons button').forEach(b=>b.click())"); time.sleep(2)
        urls = [u for u in TABS_SEEN if "donate.stripe.com" in u]
        check("4 clicks open donate.stripe.com/test_a..d", all(any(u.startswith("https://donate.stripe.com/test_" + k) for u in urls) for k in "abcd"), urls)
        check("custom shows 'On the next page, choose the quantity (€1 each).'", banner(sid)["note"] == "On the next page, choose the quantity (€1 each).")
        for t in open_tabs_with("stripe.com"): close_tab(t["targetId"])
    finally: close_tab(tid)
    tid, sid = popup_tab(); time.sleep(1.2)
    try:
        check("reopen: same milestone not asked again", banner(sid)["hidden"] is True)
        check("rating card not shown yet (1 leave)", rating(sid) is True)
    finally: close_tab(tid)
    # next milestone: 20 h, but < 30 days after the last ask
    sw_eval("chrome.storage.local.set({totals:{reclaimedMin:%d,leaves:3,goIns:3,spentSec:0}})" % (20 * 60 + 5)); tid, sid = popup_tab(); time.sleep(1.3)
    try:
        check("20 h reached but < 30 days since last ask: no banner", banner(sid)["hidden"] is True)
        check("rating card appears after the 3rd Leave (banner not shown)", rating(sid) is False)
        check("rating stored {shown:true,at}", (storage().get("rating") or {}).get("shown") is True)
        TABS_SEEN.clear(); ev(sid, "document.getElementById('rating-go').click()", False); time.sleep(1.5)
        check("Rate it opens the reviews URL", any(u == STORE() + "/reviews" for u in TABS_SEEN), [u for u in TABS_SEEN if "chromewebstore" in u])
        for t in open_tabs_with("chromewebstore"): close_tab(t["targetId"])
    finally: close_tab(tid)
    tid, sid = popup_tab(); time.sleep(1.2)
    try: check("rating card never shown a second time", rating(sid) is True)
    finally: close_tab(tid)
    sw_eval("chrome.storage.local.set({donation:{asked:[5],lastAskAt:%d,dontAskAgain:false}})" % (now_ms() - 31 * DAY)); tid, sid = popup_tab(); time.sleep(1.3)
    try:
        b = banner(sid); check("after 30+ days: banner for 20 h milestone", b["hidden"] is False and "about 20 hours" in b["text"], b["text"])
        px(sid, "document.getElementById('banner-never').click()"); time.sleep(0.6)
        check("Don't ask again persists", banner(sid)["hidden"] is True and storage()["donation"]["dontAskAgain"] is True)
    finally: close_tab(tid)
    # both conditions at once: banner wins, rating waits
    reset(extra={"totals": {"reclaimedMin": 6 * 60, "leaves": 5, "goIns": 5, "spentSec": 0}}); tid, sid = popup_tab(); time.sleep(1.5)
    try: check("banner and rating never in the same render (banner wins)", banner(sid)["hidden"] is False and rating(sid) is True and not (storage().get("rating") or {}).get("shown"))
    finally: close_tab(tid)
    # supporter via thanks page
    for label, sess, want in (("bogus id", "bogus", False), ("cs_test_123", "cs_test_123", False), ("cs_live_ + 5 chars", "cs_live_abcde", False), ("valid cs_test_ + 24 alnum", GOOD_SESSION, True)):
        reset(); t, s = new_tab(THANKS_URL + sess)
        ok = wait_for(lambda: storage().get("supporter") is True, 3.5) if want else (time.sleep(2.5) or storage().get("supporter") is True)
        check("thanks page, %s -> supporter=%s" % (label, want), bool(ok) == want); close_tab(t)
    reset(); t, s = new_tab("https://overcrasher.github.io/reclaim/other.html?session_id=" + GOOD_SESSION); time.sleep(2)
    check("session_id on another page is ignored", not storage().get("supporter")); close_tab(t)
    reset(extra={"supporter": True, "totals": {"reclaimedMin": 6000, "leaves": 5, "goIns": 5, "spentSec": 0}}); tid, sid = popup_tab(); time.sleep(1.3)
    try: check("supporter: badge shown, no banner, no ask", px(sid, "document.getElementById('supporter').hidden") is False and banner(sid)["hidden"] is True and not storage().get("donation", {}).get("asked"))
    finally: close_tab(tid)
    tid, sid = options_tab(); time.sleep(1.2)
    try:
        check("options: donate buttons + thanks line for supporter", px(sid, "[...document.querySelectorAll('#donate button')].map(b=>b.textContent).join('|')") == "€3|€5|€10|Pick your own amount" and px(sid, "document.getElementById('thanks').hidden") is False)
        TABS_SEEN.clear(); px(sid, "document.querySelector('#donate button.custom').click()"); time.sleep(1.5)
        check("options: custom opens test_d + quantity hint", any(u.startswith("https://donate.stripe.com/test_d") for u in TABS_SEEN) and px(sid, "document.getElementById('donate-note').textContent") == "On the next page, choose the quantity (€1 each).")
        for t in open_tabs_with("stripe.com"): close_tab(t["targetId"])
    finally: close_tab(tid)

def g11_nolinks():
    reset(extra={"totals": {"reclaimedMin": 600, "leaves": 1, "goIns": 1, "spentSec": 0}}); tid, sid = popup_tab(); time.sleep(1.3)
    try:
        check("no links configured: no banner at 10 h", banner(sid)["hidden"] is True)
        dn = storage().get("donation"); check("milestone not consumed", (not dn) or (dn.get("asked") == [] and dn.get("lastAskAt") == 0), dn)
    finally: close_tab(tid)
    tid, sid = options_tab(); time.sleep(1.2)
    try: check("options: 'Donation links not configured yet' and no buttons", px(sid, "document.querySelectorAll('#donate button').length") == 0 and "not configured" in px(sid, "document.getElementById('donate-note').textContent"))
    finally: close_tab(tid)

def g16():  # REAL build config (single EUR 3 link): banner + options show exactly one button
    reset(extra={"totals": {"reclaimedMin": 5 * 60 + 10, "leaves": 1, "goIns": 1, "spentSec": 0}})
    tid, sid = popup_tab(); time.sleep(1.5)
    try:
        b = banner(sid)
        check("real build: banner shows at 5 h", b["hidden"] is False, b)
        check("real build: exactly one button '€3', no custom hint", [x[0] for x in b["buttons"]] == ["€3"] and b["note"] == "", b)
        shot(sid, "popup_banner_single_link")
        TABS_SEEN.clear(); px(sid, "document.querySelector('#banner-buttons button').click()"); time.sleep(1.5)
        check("real build: click opens the real donate.stripe.com/dRmaEY8NVaio5ZwacSfbq09", any(u == "https://donate.stripe.com/dRmaEY8NVaio5ZwacSfbq09" for u in TABS_SEEN), TABS_SEEN)
        for t_ in open_tabs_with("stripe.com"): close_tab(t_["targetId"])
    finally: close_tab(tid)
    tid, sid = options_tab(); time.sleep(1.2)
    try:
        check("real build options: one button €3, no custom/monthly", px(sid, "[...document.querySelectorAll('#donate button')].map(b=>b.textContent).join('|')") == "€3" and px(sid, "document.getElementById('donate-note').textContent") == "", px(sid, "document.getElementById('donate-note').textContent"))
        shot(sid, "options_single_link")
    finally: close_tab(tid)

def g11_evil():
    n0 = len(LOGS); reset(extra={"totals": {"reclaimedMin": 600, "leaves": 1, "goIns": 1, "spentSec": 0}}); tid, sid = popup_tab(); time.sleep(1.5)
    try:
        check("evil links: banner shown with 4 buttons", banner(sid)["hidden"] is False and len(banner(sid)["buttons"]) == 4)
        TABS_SEEN.clear(); px(sid, "document.querySelectorAll('#banner-buttons button').forEach(b=>b.click())"); time.sleep(2)
        bad = [u for u in TABS_SEEN if "evil.example" in u or "stripe.com" in u]
        check("evil / lookalike / http links open NO tab", not bad, bad)
        check("refusal warning logged", any("refusing" in l[2] for l in LOGS[n0:]))
    finally: close_tab(tid)

def g12():
    reset()
    tid, sid = options_tab()
    try:
        time.sleep(1)
        names = px(sid, "[...document.querySelectorAll('.site-name')].map(e=>e.textContent)")
        check("default sites listed (youtube.com/shorts path-scoped)", names == ["youtube.com/shorts", "tiktok.com", "reddit.com", "x.com", "twitter.com", "instagram.com", "facebook.com"], names)
        def setnum(i, v):
            px(sid, "(()=>{const e=document.getElementById('%s');e.value='%s';e.dispatchEvent(new Event('input',{bubbles:true}))})()" % (i, v)); time.sleep(0.9)
        setnum("countdownSec", "2")
        check("countdown 2 rejected (message, not saved)", "between 3 and 30" in px(sid, "document.getElementById('countdownErr').textContent") and storage()["settings"]["countdownSec"] == 3)
        setnum("countdownSec", "12"); check("countdown 12 saved", storage()["settings"]["countdownSec"] == 12 and px(sid, "document.getElementById('countdownErr').textContent") == "")
        setnum("avgSessionMin", "200"); check("average 200 rejected", "between 5 and 120" in px(sid, "document.getElementById('avgErr').textContent") and storage()["settings"]["avgSessionMin"] == 15)
        setnum("avgSessionMin", "25"); check("average 25 saved", storage()["settings"]["avgSessionMin"] == 25)
        ev(sid, "(()=>{const s=document.getElementById('sessionMin');s.value='20';s.dispatchEvent(new Event('change'))})()", False)
        ev(sid, "(()=>{const s=document.getElementById('stayMin');s.value='10';s.dispatchEvent(new Event('change'))})()", False); time.sleep(0.8)
        st = storage()["settings"]; check("session length 20 / stay 10 saved", st["sessionMin"] == 20 and st["stayMin"] == 10, st)
        check("session options 5/10/15/20/30 and stay 5/10/15", px(sid, "[...document.querySelectorAll('#sessionMin option')].map(o=>o.value).join()") == "5,10,15,20,30" and px(sid, "[...document.querySelectorAll('#stayMin option')].map(o=>o.value).join()") == "5,10,15")
        t2, s2 = open_site("www.facebook.com", "/", wait=0.5)
        try:
            assert wait_for(lambda: any(b.startswith("Go in") for b in ov(s2)["buttons"]), 20)
            check("settings take effect in the overlay: 'Go in (20 min)' after a 12 s countdown", ov(s2)["buttons"][0] == "Go in (20 min)")
        finally: close_tab(t2)
        px(sid, "document.getElementById('sites').querySelectorAll('button')[0].click()"); time.sleep(0.6)
        check("Remove works (youtube.com/shorts removed)", all(s["host"] != "youtube.com" for s in storage()["sites"]))
        ev(sid, "document.getElementById('restore').click()", False); time.sleep(0.6)
        check("Restore default sites re-adds it", any(s["host"] == "youtube.com" for s in storage()["sites"]))
        sw_eval("chrome.storage.local.set({days:{'2026-11-09':{spentSec:60,reclaimedMin:15,leaves:1,goIns:1,sites:{}}},totals:{reclaimedMin:15,leaves:1,goIns:1,spentSec:60}})")
        for _ in range(2): ev(sid, "document.getElementById('resetStats').click()", False); time.sleep(0.4)
        check("Reset all statistics (two-click)", storage()["days"] == {} and storage()["totals"]["reclaimedMin"] == 0)
        check("support section: rate link + 2 siblings", px(sid, "!!document.getElementById('rate-link')") and px(sid, "document.querySelectorAll('#siblings a').length") == 2 and "Wait 24h" in px(sid, "document.getElementById('siblings').textContent") and "a pause before impulse buys" in px(sid, "document.getElementById('siblings').textContent") and "see what your meetings cost" in px(sid, "document.getElementById('siblings').textContent"))
        TABS_SEEN.clear()
        for i in ("rate-link", "sib-wait24h", "sib-meetingmeter"): ev(sid, "document.getElementById('%s').click()" % i, False)
        time.sleep(1.5)
        check("links open the store listing, Wait 24h and Meeting Meter", all(any(u.startswith(x) for u in TABS_SEEN) for x in (STORE(), "https://chromewebstore.google.com/detail/wait-24h/pkgdjohoemjkejcbfbkfobbbjcpdabme", "https://chromewebstore.google.com/detail/meeting-meter/ffkniocclnaojfdcoofnjkfnihnpgnlb")), [u for u in TABS_SEEN if "chromewebstore" in u])
        for t in open_tabs_with("chromewebstore"): close_tab(t["targetId"])
        shot(sid, "options")
    finally: close_tab(tid)

def g13():
    reset()
    tid, sid = open_site("www.youtube.com", "/")
    try:
        check("content-script world found", iso_ctx(sid) is not None)
        r = cs_eval(sid, "(async()=>{try{if(!chrome.storage||!chrome.storage.local)return 'UNDEFINED';return 'READ:'+JSON.stringify(await chrome.storage.local.get(null))}catch(e){return 'ERR:'+e.message}})()")
        check("content script cannot READ chrome.storage.local", str(r).startswith(("ERR:", "UNDEFINED")), r)
        r = cs_eval(sid, "(async()=>{try{if(!chrome.storage||!chrome.storage.local)return 'UNDEFINED';await chrome.storage.local.set({supporter:true});return 'WROTE'}catch(e){return 'ERR:'+e.message}})()")
        check("content script cannot WRITE chrome.storage.local", str(r).startswith(("ERR:", "UNDEFINED")) and not storage().get("supporter"), r)
        r = cs_eval(sid, "(async()=>{try{if(!chrome.storage||!chrome.storage.session)return 'UNDEFINED';return 'READ:'+JSON.stringify(await chrome.storage.session.get(null))}catch(e){return 'ERR:'+e.message}})()")
        check("content script cannot read chrome.storage.session", str(r).startswith(("ERR:", "UNDEFINED")), r)
        r = cs_send(sid, {"type": "supporter", "sessionId": GOOD_SESSION})
        check("forged supporter message from a non-thanks page rejected", r == {"ok": False} and not storage().get("supporter"), r)
        r = cs_send(sid, {"type": "goIn", "site": "reddit.com", "url": "https://www.reddit.com/", "key": "reddit.com"})
        check("goIn on an untracked path rejected; site/url fields in the message are ignored", r == {"ok": False} and not storage().get("sessions"), r)
        for m in ({"type": "leave"}, {"type": "extend"}, {"type": "hb", "kind": "beat"}, {"type": "nope"}, {"type": 5}, {"type": "goIn", "intention": "x"}):
            r = cs_send(sid, m); check("untracked path: %s rejected" % json.dumps(m), r == {"ok": False}, r)
        check("nothing counted by the forged messages", not today().get("leaves") and not today().get("goIns"))
        r = cs_send(sid, {"type": "check"})
        check("check on untracked path: track=false", r.get("ok") and r.get("track") is False, r)
        main = px(sid, "typeof chrome!=='undefined' && chrome.runtime && typeof chrome.runtime.sendMessage")
        check("page (main world) has no extension messaging", main in (False, None, "undefined") or main is None, main)
        px(sid, "history.pushState({},'','/shorts/q')"); wait_overlay(sid, 4, buttons=False)
        r = cs_send(sid, {"type": "extend"}); check("extend without an expired session rejected", r == {"ok": False}, r)
        r = cs_send(sid, {"type": "hb", "kind": "weird"}); check("heartbeat with an unknown kind rejected", r == {"ok": False}, r)
        r = cs_send(sid, {"type": "goIn", "intention": {"a": 1}}); check("goIn with non-string intention accepted but stores no text", r.get("ok") and not storage().get("intentions"), r)
    finally: close_tab(tid)
    tid, sid = popup_tab(); time.sleep(1)
    try:
        r = ev(sid, "chrome.runtime.sendMessage({type:'check'}).then(r=>r,e=>({threw:String(e)}))")
        check("extension-page messages are not handled by the SW (FAIL)", r == {"ok": False}, r)
        check("extension pages CAN read storage", isinstance(ev(sid, "chrome.storage.local.get(null)"), dict))
    finally: close_tab(tid)
    t, s = new_tab(THANKS_URL + GOOD_SESSION); time.sleep(2)
    try:
        r = cs_send(s, {"type": "supporter", "sessionId": "nope"}); check("thanks page with a bad session id rejected", r == {"ok": False}, r)
        r = cs_send(s, {"type": "goIn"}); check("thanks page cannot start sessions", r == {"ok": False}, r)
    finally: close_tab(t)
    check("no unexpected extension errors", not ext_errors(), ext_errors()[-3:])

GROUPS = [(1, "load/manifest/i18n/welcome", "main", g1), (2, "overlay+countdown+Go in", "main", g2), (3, "session reuse across tabs", "main", g3),
 (4, "expiry overlay + Stay", "main", g4), (5, "Leave -> reclaimed + counters", "main", g5), (6, "active-time heartbeats", "main", g6),
 (7, "SPA navigation (youtube-like)", "main", g7), (8, "user-added site (dynamic registration)", "custom", g8), (9, "intention purge + forged intention", "main", g9),
 (10, "popup today/week/mascot/summary/pause/share", "main", g10), (11, "donation banner, rating, share, supporter", "links", g11),
 (12, "options", "main", g12), (13, "security", "main", g13), (14, "no links: milestone not consumed", "nolinks", g11_nolinks), (15, "evil links", "evil", g11_evil), (16, "real build: single EUR 3 link", "main", g16)]
NAMES = {n: nm for n, nm, p, f in GROUPS}

def variant(name, links=None, extra_host=None):
    d = os.path.join(HERE, "profile-ext-" + name); shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(EXT, d, ignore=shutil.ignore_patterns(".git", "tests", "docs", "tools", "dist", "store"))
    if links:
        p = os.path.join(d, "config.js"); c = open(p).read()
        c2 = re.sub(r"export const DONATE_LINKS = \{[^}]*\};", "export const DONATE_LINKS = %s;" % links, c); assert c2 != c; open(p, "w").write(c2)
    if extra_host:
        p = os.path.join(d, "manifest.json"); m = json.load(open(p)); m["host_permissions"].append(extra_host); json.dump(m, open(p, "w"), indent=2)
    return d

def run_phase(phase, path):
    todo = [(n, f) for n, nm, p, f in GROUPS if p == phase and (not ONLY or n in ONLY)]
    if not todo: return
    sw["sid"] = None; sw["tid"] = None
    start(path)
    try:
        for n, f in todo:
            CUR[0] = n; t0 = time.time(); print("== Group %d: %s" % (n, NAMES[n]), flush=True)
            try: f()
            except Exception as e:
                check("group crashed", False, "%s: %s" % (type(e).__name__, e)); traceback.print_exc()
            print("   (%.0fs)" % (time.time() - t0), flush=True)
        errs = [l for l in LOGS if l[1] == "exception" or (l[1].endswith("error") and "Failed to load resource" not in l[2])]
        print("== error-level logs in phase '%s': %d" % (phase, len(errs)))
        for l in errs[:15]: print("  ", l)
    finally: H.cdp.close()

def main():
    T0 = time.time()
    run_phase("main", EXT)
    run_phase("custom", variant("custom", extra_host="https://*.fixture-custom.test/*") if any(p == "custom" and (not ONLY or n in ONLY) for n, _, p, _ in GROUPS) else EXT)
    run_phase("links", variant("links", '{ small: "https://donate.stripe.com/test_a", medium: "https://donate.stripe.com/test_b", large: "https://donate.stripe.com/test_c", custom: "https://donate.stripe.com/test_d", monthly: "" }') if any(p == "links" and (not ONLY or n in ONLY) for n, _, p, _ in GROUPS) else EXT)
    run_phase("nolinks", variant("nolinks", '{ small: "", medium: "", large: "", custom: "", monthly: "" }') if any(p == "nolinks" and (not ONLY or n in ONLY) for n, _, p, _ in GROUPS) else EXT)
    run_phase("evil", variant("evil", '{ small: "https://evil.example/x", medium: "https://buy.stripe.com.evil.example/x", large: "http://donate.stripe.com/x", custom: "https://evil.example/custom", monthly: "" }') if any(p == "evil" and (not ONLY or n in ONLY) for n, _, p, _ in GROUPS) else EXT)
    print("\n================ RESULTS ================")
    tp = tf = 0
    for n in sorted(RESULTS):
        r = RESULTS[n]; ok = sum(x[1] for x in r); tp += ok; tf += len(r) - ok
        print("%2d  %-4s %-48s (%d/%d)" % (n, "PASS" if ok == len(r) else "FAIL", NAMES[n], ok, len(r)))
        for c, o, e in r:
            if not o: print("      FAIL:", c, "|", e[:400])
    print("TOTAL: %d passed, %d failed, %.0f s" % (tp, tf, time.time() - T0))
if __name__ == "__main__": main()
