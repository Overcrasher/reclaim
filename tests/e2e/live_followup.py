#!/usr/bin/env python3
"""Follow-up live checks: scrollbar strip (IG/FB), YouTube Shorts after pre-answering the consent wall (test profile only),
X.com retry.  Usage: python3 live_followup.py [scroll|yt|x] [--headed] [--ua]"""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plumbing import *
H.fetch_hosts = []
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36"
HJ = "JSON.stringify((()=>{const h=document.querySelector('[data-reclaim]');if(!h)return null;const r=h.getBoundingClientRect();return {w:r.width,h:r.height,iw:innerWidth,ih:innerHeight,top:document.elementFromPoint(innerWidth-3,innerHeight/2)===h,htmlOverflowInline:document.documentElement.style.overflow}})())"
OV = "!!document.querySelector('[data-reclaim]')"
MJ = "JSON.stringify([...document.querySelectorAll('video')].map(v=>({paused:v.paused,muted:v.muted})))"
def setup():
    start(EXT); time.sleep(1)
    sw_eval("chrome.storage.local.set({settings:{countdownSec:3,sessionMin:10,stayMin:5,avgSessionMin:15}})")
    for w in open_tabs_with("welcome.html"): close_tab(w["targetId"])
def tab(url, ua=False):
    tid, sid = new_tab("about:blank", fetch=False)
    if ua: H.cdp.send("Emulation.setUserAgentOverride", {"userAgent": UA}, sid)
    H.cdp.send("Page.navigate", {"url": url}, sid); return tid, sid
def scroll():
    for name, url in (("instagram", "https://www.instagram.com/"), ("facebook", "https://www.facebook.com/")):
        sw_eval("chrome.storage.local.remove(['sessions'])")
        tid, sid = tab(url); r = {"site": name}
        wait_for(lambda: ev(sid, OV, False), 20); time.sleep(4.5)
        r["overlay"] = json.loads(ev(sid, HJ, False)); shot(sid, "live2_%s_overlay" % name)
        r["strip_gone"] = bool(r["overlay"] and r["overlay"]["w"] == r["overlay"]["iw"])
        click_shadow(sid, "BUTTON", "Go in"); time.sleep(1.2)
        r["overlay_after"] = ev(sid, OV, False)
        r["html_overflow_inline_after"] = ev(sid, "document.documentElement.style.overflow", False)
        r["scrollable"] = ev(sid, "(()=>{const y0=scrollY;scrollTo(0,300);const ok=scrollY>y0||document.documentElement.scrollHeight<=innerHeight;scrollTo(0,0);return {ok,sh:document.documentElement.scrollHeight,ih:innerHeight,cs:getComputedStyle(document.documentElement).overflow}})()", False)
        shot(sid, "live2_%s_after_go_in" % name); print(json.dumps(r), flush=True); close_tab(tid)
def yt():
    tid, sid = tab("https://www.youtube.com/shorts/"); time.sleep(6)
    r = {"first_url": ev(sid, "location.href", False)}
    if "consent." in r["first_url"]:
        r["rejected"] = ev(sid, "(()=>{const b=[...document.querySelectorAll('button')].find(b=>/reject all/i.test(b.textContent));if(b){b.click();return true}return false})()", False)
        time.sleep(7); r["after_reject_url"] = ev(sid, "location.href", False)
    sw_eval("chrome.storage.local.remove(['sessions'])")
    H.cdp.send("Page.navigate", {"url": "https://www.youtube.com/shorts/"}, sid)
    wait_for(lambda: ev(sid, OV, False), 20); time.sleep(4.5)
    r["direct_url"] = ev(sid, "location.href", False); r["direct_overlay"] = ev(sid, OV, False)
    try: r["direct_overlay_geom"] = json.loads(ev(sid, HJ, False)); r["media"] = json.loads(ev(sid, MJ, False))
    except Exception as e: r["geom_err"] = str(e)
    shot(sid, "live2_youtube_shorts_direct")
    r["cookies"] = [c["name"] for c in H.cdp.send("Network.getCookies", {"urls": ["https://www.youtube.com/"]}, sid).get("cookies", [])] if H.cdp.send("Network.enable", {}, sid) is not None else []
    click_shadow(sid, "BUTTON", "Go in"); time.sleep(1.5)
    r["direct_after_go_in_overlay"] = ev(sid, OV, False); r["media_after"] = json.loads(ev(sid, MJ, False)); shot(sid, "live2_youtube_shorts_after_go_in")
    sw_eval("chrome.storage.local.remove(['sessions'])")
    H.cdp.send("Page.navigate", {"url": "https://www.youtube.com/"}, sid); time.sleep(7)
    r["home_url"] = ev(sid, "location.href", False); r["home_overlay"] = ev(sid, OV, False); shot(sid, "live2_youtube_home")
    r["clicked"] = ev(sid, "(()=>{const a=document.querySelector('a[href^=\"/shorts\"]');if(a){a.click();return a.getAttribute('href')}return null})()", False); time.sleep(4)
    r["spa_url"] = ev(sid, "location.href", False); r["spa_overlay"] = ev(sid, OV, False)
    try: r["spa_media"] = json.loads(ev(sid, MJ, False))
    except Exception: pass
    shot(sid, "live2_youtube_spa_shorts")
    if r["spa_overlay"]:
        click_shadow(sid, "BUTTON", "Go in"); time.sleep(1.5)
        ev(sid, "history.back()", False); time.sleep(3)
        r["back_url"] = ev(sid, "location.href", False); r["back_overlay"] = ev(sid, OV, False)
    print(json.dumps(r), flush=True); close_tab(tid)
def x():
    tid, sid = tab("https://x.com/", ua="--ua" in sys.argv); time.sleep(10)
    r = {"headed": HEADED, "ua": "--ua" in sys.argv, "url": ev(sid, "location.href", False)}
    try: r["title"] = ev(sid, "document.title", False); r["overlay"] = ev(sid, OV, False)
    except Exception as e: r["err"] = str(e)
    shot(sid, "live2_x_%s%s" % ("headed" if HEADED else "headless", "_ua" if "--ua" in sys.argv else ""))
    if r.get("overlay"):
        time.sleep(4); click_shadow(sid, "BUTTON", "Go in"); time.sleep(1.2); r["after_go_in"] = ev(sid, OV, False)
    print(json.dumps(r), flush=True); close_tab(tid)
if __name__ == "__main__":
    setup()
    try: {"scroll": scroll, "yt": yt, "x": x}[sys.argv[1]]()
    finally:
        print("EXTENSION ERRORS:", ext_errors()); H.cdp.close()
