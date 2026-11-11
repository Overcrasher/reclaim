#!/usr/bin/env python3
"""Live verification on the REAL public sites (no login). Writes screenshots to tests/e2e/shots/live_*.png.
Per site: load, overlay present (closed shadow), covers viewport, page not clickable, media paused, Go in removes it, Leave -> reclaimed.html."""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plumbing import *
H.fetch_hosts = []
HOST_JS = """JSON.stringify((()=>{const h=document.querySelector('[data-reclaim]');if(!h)return null;const r=h.getBoundingClientRect();
 return {w:r.width,h:r.height,top:document.elementFromPoint(innerWidth/2,innerHeight/2)===h,z:getComputedStyle(h).zIndex}})())"""
MEDIA_JS = "JSON.stringify([...document.querySelectorAll('video,audio')].map(m=>({paused:m.paused,muted:m.muted,rs:m.readyState})))"
SITES = [("tiktok", "https://www.tiktok.com/"), ("reddit", "https://www.reddit.com/"), ("x", "https://x.com/"),
         ("instagram", "https://www.instagram.com/"), ("facebook", "https://www.facebook.com/"), ("youtube_shorts", "https://www.youtube.com/shorts/")]
def ov():
    pass
def run():
    start(EXT)
    time.sleep(1)
    sw_eval("chrome.storage.local.set({settings:{countdownSec:3,sessionMin:10,stayMin:5,avgSessionMin:15}})")
    for w in open_tabs_with("welcome.html"): close_tab(w["targetId"])
    rows = []
    for name, url in SITES:
        r = {"site": name, "url": url}
        sw_eval("chrome.storage.local.remove(['sessions'])")
        tid, sid = new_tab("about:blank", fetch=False)
        try:
            H.cdp.send("Page.navigate", {"url": url}, sid)
            t0 = time.time(); h = None
            while time.time() - t0 < 20:
                try: h = json.loads(ev(sid, HOST_JS, False))
                except Exception: h = None
                if h: break
                time.sleep(0.25)
            r["overlay_after_s"] = round(time.time() - t0, 2) if h else None
            r["host"] = h
            try: r["final_url"] = ev(sid, "location.href", False); r["title"] = ev(sid, "document.title", False)
            except Exception as e: r["final_url"] = str(e)
            time.sleep(3.5)
            try: r["media"] = json.loads(ev(sid, MEDIA_JS, False))
            except Exception: r["media"] = None
            try: r["overlay_hit"] = json.loads(ev(sid, HOST_JS, False))
            except Exception: r["overlay_hit"] = None
            shot(sid, "live_%s_overlay" % name)
            try: es = shadow_elems(sid); r["buttons"] = [e["text"] for e in es if e["tag"] == "BUTTON"]; r["h1"] = next((e["text"] for e in es if e["tag"] == "H1"), None)
            except Exception as e: r["buttons"] = str(e)
            ok = click_shadow(sid, "BUTTON", "Go in")
            time.sleep(1.2)
            try: r["after_go_in_overlay"] = json.loads(ev(sid, HOST_JS, False))
            except Exception: r["after_go_in_overlay"] = "?"
            r["go_in_clicked"] = ok
            r["session"] = list((storage().get("sessions") or {}).keys())
            shot(sid, "live_%s_after_go_in" % name)
            try: r["media_after"] = json.loads(ev(sid, MEDIA_JS, False))
            except Exception: r["media_after"] = None
        except Exception as e: r["error"] = "%s: %s" % (type(e).__name__, e)
        finally: close_tab(tid)
        # Leave path
        sw_eval("chrome.storage.local.remove(['sessions'])")
        tid, sid = new_tab("about:blank", fetch=False)
        try:
            H.cdp.send("Page.navigate", {"url": url}, sid)
            wait_for(lambda: json.loads(ev(sid, HOST_JS, False)), 20); time.sleep(4)
            click_shadow(sid, "BUTTON", "Leave"); time.sleep(2)
            r["leave_ok"] = bool(open_tabs_with("reclaimed.html"))
            for x in open_tabs_with("reclaimed.html"): close_tab(x["targetId"])
        except Exception as e: r["leave_error"] = "%s: %s" % (type(e).__name__, e)
        finally:
            try: close_tab(tid)
            except Exception: pass
        rows.append(r); print(json.dumps(r, default=str), flush=True)
    # YouTube home -> shorts SPA
    r = {"site": "youtube_home_spa"}
    sw_eval("chrome.storage.local.remove(['sessions'])")
    tid, sid = new_tab("about:blank", fetch=False)
    try:
        H.cdp.send("Page.navigate", {"url": "https://www.youtube.com/"}, sid); time.sleep(6)
        r["url"] = ev(sid, "location.href", False); r["title"] = ev(sid, "document.title", False)
        r["overlay_on_home"] = ev(sid, "!!document.querySelector('[data-reclaim]')", False)
        r["consent_page"] = "consent" in r["url"]
        shot(sid, "live_youtube_home")
        ev(sid, "history.pushState({},'','/shorts/'); window.dispatchEvent(new Event('popstate'))", False); time.sleep(2.5)
        r["overlay_after_spa_into_shorts"] = ev(sid, "!!document.querySelector('[data-reclaim]')", False)
        shot(sid, "live_youtube_spa_shorts")
        ev(sid, "history.pushState({},'','/'); window.dispatchEvent(new Event('popstate'))", False); time.sleep(2.5)
        r["overlay_after_spa_out"] = ev(sid, "!!document.querySelector('[data-reclaim]')", False)
    except Exception as e: r["error"] = str(e)
    finally: close_tab(tid)
    rows.append(r); print(json.dumps(r, default=str), flush=True)
    print("EXTENSION ERRORS:", ext_errors())
    H.cdp.close()
if __name__ == "__main__": run()
