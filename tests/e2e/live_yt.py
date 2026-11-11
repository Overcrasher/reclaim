#!/usr/bin/env python3
"""Live YouTube: home -> real in-page navigation to Shorts (SPA), then back. Records consent-wall behaviour."""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plumbing import *
H.fetch_hosts = []
start(EXT); time.sleep(1)
sw_eval("chrome.storage.local.set({settings:{countdownSec:3,sessionMin:10,stayMin:5,avgSessionMin:15}})")
for w in open_tabs_with("welcome.html"): close_tab(w["targetId"])
tid, sid = new_tab("about:blank", fetch=False)
OV = "!!document.querySelector('[data-reclaim]')"
H.cdp.send("Page.navigate", {"url": "https://www.youtube.com/"}, sid); time.sleep(7)
r = {"url": ev(sid, "location.href", False), "title": ev(sid, "document.title", False), "overlay_on_home": ev(sid, OV, False)}
shot(sid, "live_youtube_home")
r["shorts_links"] = ev(sid, "[...document.querySelectorAll('a[href^=\"/shorts\"]')].length", False)
r["clicked"] = ev(sid, "(()=>{const a=document.querySelector('a[href^=\"/shorts\"]')||document.querySelector('a[title=\"Shorts\"]');if(a){a.click();return a.getAttribute('href')}return null})()", False)
time.sleep(4)
r["url_after_click"] = ev(sid, "location.href", False)
r["overlay_after_spa_into_shorts"] = ev(sid, OV, False)
try: r["media"] = json.loads(ev(sid, "JSON.stringify([...document.querySelectorAll('video')].map(v=>({paused:v.paused,muted:v.muted})))", False))
except Exception: pass
shot(sid, "live_youtube_spa_shorts")
if r["overlay_after_spa_into_shorts"]:
    click_shadow(sid, "BUTTON", "Go in"); time.sleep(1.5)
    r["overlay_after_go_in"] = ev(sid, OV, False)
    r["media_after_go_in"] = json.loads(ev(sid, "JSON.stringify([...document.querySelectorAll('video')].map(v=>({paused:v.paused,muted:v.muted})))", False))
    shot(sid, "live_youtube_shorts_after_go_in")
    ev(sid, "history.back()", False); time.sleep(3)
    r["url_after_back"] = ev(sid, "location.href", False); r["overlay_after_back_to_home"] = ev(sid, OV, False)
print(json.dumps(r)); print("EXTENSION ERRORS:", ext_errors())
H.cdp.close()
