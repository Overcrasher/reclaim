"""CDP plumbing for the Reclaim E2E harness: Chrome over --remote-debugging-pipe, Extensions.loadUnpacked,
Fetch fixtures on real hostnames, closed-shadow inspection via DOM.getDocument(pierce), real mouse input, screenshots."""
import fcntl, re, os, sys, json, time, base64, shutil, subprocess, threading, queue, traceback, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "shots"); os.makedirs(SHOTS, exist_ok=True)
EXT = os.path.dirname(os.path.dirname(HERE))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HEADED = "--headed" in sys.argv
PROFILE = [None]

class CDP:
    def __init__(self):
        r1, w1 = os.pipe(); r2, w2 = os.pipe()
        r1, w1, r2, w2 = [fcntl.fcntl(f, fcntl.F_DUPFD_CLOEXEC, 20) for f in (r1, w1, r2, w2)]
        def pre():
            os.dup2(r1, 3, inheritable=True); os.dup2(w2, 4, inheritable=True)
        PROFILE[0] = tempfile.mkdtemp(prefix="reclaim-profile-")
        args = [CHROME, "--enable-unsafe-extension-debugging", "--remote-debugging-pipe", "--user-data-dir=" + PROFILE[0],
                "--no-first-run", "--no-default-browser-check", "--window-size=1100,900", "--autoplay-policy=no-user-gesture-required", "about:blank"]
        if not HEADED: args.insert(1, "--headless=new")
        self.proc = subprocess.Popen(args, preexec_fn=pre, close_fds=False, stdout=subprocess.DEVNULL, stderr=open(os.path.join(HERE, "chrome.err"), "w"))
        os.close(r1); os.close(w2)
        self.wfd, self.rfd = w1, r2
        self.id = 0; self.lock = threading.Lock(); self.waiters = {}
        self.events = queue.Queue(); self.listeners = []
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=self._dispatch, daemon=True).start()
    def _read(self):
        buf = b""
        while True:
            try: d = os.read(self.rfd, 65536)
            except OSError: return
            if not d: return
            buf += d
            while b"\0" in buf:
                m, buf = buf.split(b"\0", 1)
                try: msg = json.loads(m)
                except Exception: continue
                if "id" in msg:
                    w = self.waiters.pop(msg["id"], None)
                    if w: w[1].update(msg); w[0].set()
                else: self.events.put(msg)
    def _dispatch(self):
        while True:
            e = self.events.get()
            for l in self.listeners:
                try: l(e)
                except Exception: traceback.print_exc()
    def send(self, method, params=None, sid=None, timeout=30):
        with self.lock:
            self.id += 1; i = self.id
        ev_ = threading.Event(); res = {}
        self.waiters[i] = (ev_, res)
        m = {"id": i, "method": method, "params": params or {}}
        if sid: m["sessionId"] = sid
        os.write(self.wfd, json.dumps(m).encode() + b"\0")
        if not ev_.wait(timeout): raise TimeoutError(method)
        if "error" in res: raise RuntimeError(method + ": " + json.dumps(res["error"]))
        return res.get("result", {})
    def close(self):
        try: self.proc.kill()
        except Exception: pass
        if PROFILE[0]:
            subprocess.run(["pkill", "-f", "user-data-dir=" + PROFILE[0]], capture_output=True)
            time.sleep(0.5); shutil.rmtree(PROFILE[0], ignore_errors=True)

class H:  # shared mutable state
    cdp = None; EXT_ID = None; fixture = staticmethod(lambda url: None); fetch_hosts = []
LOGS = []; TABS_SEEN = []; labels = {}; ISO = {}; sw = {"sid": None, "tid": None}
RESULTS = {}; CUR = [0]

def check(name, ok, ev_=""):
    RESULTS.setdefault(CUR[0], []).append((name, bool(ok), str(ev_)))
    print(("  PASS " if ok else "  FAIL ") + name + ("  | " + str(ev_)[:300] if ev_ != "" else ""), flush=True)

def on_event(e):
    cdp = H.cdp
    m, p, sid = e.get("method"), e.get("params", {}), e.get("sessionId")
    lab = labels.get(sid, sid)
    if m == "Fetch.requestPaused":
        url = p["request"]["url"]; body = H.fixture(url)
        try:
            if body is not None:
                cdp.send("Fetch.fulfillRequest", {"requestId": p["requestId"], "responseCode": 200,
                    "responseHeaders": [{"name": "Content-Type", "value": "text/html; charset=utf-8"}], "body": base64.b64encode(body.encode()).decode()}, sid)
            else:
                cdp.send("Fetch.fulfillRequest", {"requestId": p["requestId"], "responseCode": 404,
                    "responseHeaders": [{"name": "Content-Type", "value": "text/plain"}], "body": base64.b64encode(b"nf").decode()}, sid)
        except Exception as ex: print("fetch err", ex)
    elif m in ("Target.targetCreated", "Target.targetInfoChanged"):
        TABS_SEEN.append(p["targetInfo"].get("url", ""))
    elif m == "Runtime.executionContextCreated":
        c = p["context"]
        if c.get("auxData", {}).get("type") == "isolated":
            ISO.setdefault(sid, []).append((c["id"], c.get("origin", ""), c.get("name", "")))
    elif m == "Runtime.executionContextsCleared":
        ISO[sid] = []
    elif m == "Runtime.exceptionThrown":
        d = p["exceptionDetails"]
        LOGS.append((lab, "exception", d.get("text", "") + " " + json.dumps(d.get("exception", {}).get("description", ""))[:300] + " " + d.get("url", "")))
    elif m == "Runtime.consoleAPICalled" and p["type"] in ("error", "warning", "assert"):
        LOGS.append((lab, "console." + p["type"], " ".join(str(a.get("value", a.get("description", ""))) for a in p["args"])))
    elif m == "Log.entryAdded" and p["entry"]["level"] in ("error", "warning"):
        LOGS.append((lab, "log." + p["entry"]["level"], p["entry"]["text"] + " " + p["entry"].get("url", "")))
    elif m == "Target.attachedToTarget":
        ti = p["targetInfo"]
        if ti["type"] == "service_worker":
            s = p["sessionId"]; labels[s] = "SW"; sw["sid"] = s; sw["tid"] = ti["targetId"]
            for meth in ("Runtime.enable", "Log.enable"):
                try: cdp.send(meth, {}, s)
                except Exception as ex: print("sw enable", ex)
            try: cdp.send("Runtime.runIfWaitingForDebugger", {}, s)
            except Exception: pass

def start(ext_path):
    H.cdp = CDP(); cdp = H.cdp; cdp.listeners.append(on_event)
    time.sleep(2)
    cdp.send("Target.setAutoAttach", {"autoAttach": True, "waitForDebuggerOnStart": True, "flatten": True, "filter": [{"type": "service_worker"}, {"exclude": True}]})
    cdp.send("Target.setDiscoverTargets", {"discover": True})
    r = cdp.send("Extensions.loadUnpacked", {"path": ext_path}); H.EXT_ID = r["id"]
    return r

def get_sw():
    cdp = H.cdp
    for _ in range(30):
        ts = cdp.send("Target.getTargets")["targetInfos"]
        s = [t for t in ts if t["type"] == "service_worker" and H.EXT_ID in t["url"]]
        if s:
            if sw["tid"] != s[0]["targetId"] or not sw["sid"]:
                sid = cdp.send("Target.attachToTarget", {"targetId": s[0]["targetId"], "flatten": True})["sessionId"]
                labels[sid] = "SW"; sw["sid"] = sid; sw["tid"] = s[0]["targetId"]
                cdp.send("Runtime.enable", {}, sid); cdp.send("Log.enable", {}, sid)
            return sw["sid"]
        time.sleep(0.5)
    raise RuntimeError("no service worker target")

def ev(sid, expr, await_=True, **kw):
    p = {"expression": expr, "awaitPromise": await_, "returnByValue": True}; p.update(kw)
    r = H.cdp.send("Runtime.evaluate", p, sid, timeout=60)
    if "exceptionDetails" in r: raise RuntimeError("eval: " + json.dumps(r["exceptionDetails"])[:400])
    return r["result"].get("value")
px = lambda sid, expr: ev(sid, expr, False)

def sw_eval(expr):
    for i in range(6):
        try: return ev(get_sw(), expr)
        except Exception as e:
            m = str(e)
            if i < 5 and ("Session" in m or "not found" in m or "closed" in m or "chrome is not defined" in m or "Cannot find context" in m):
                sw["sid"] = None; time.sleep(1.2); continue
            raise
def storage(): return sw_eval("chrome.storage.local.get(null)")

def new_tab(url, fetch=True, w=1100, h=800, pre_script=None, focus=True, wait=1.2):
    cdp = H.cdp
    tid = cdp.send("Target.createTarget", {"url": "about:blank"})["targetId"]
    sid = cdp.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
    labels[sid] = "page:" + url[:60]
    for m in ("Runtime.enable", "Log.enable", "Page.enable", "DOM.enable"): cdp.send(m, {}, sid)
    if fetch: cdp.send("Fetch.enable", {"patterns": [{"urlPattern": "https://%s/*" % x} for x in H.fetch_hosts]}, sid)
    cdp.send("Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False}, sid)
    cdp.send("Emulation.setEmulatedMedia", {"features": [{"name": "prefers-color-scheme", "value": "light"}]}, sid)
    if focus:
        try: cdp.send("Emulation.setFocusEmulationEnabled", {"enabled": True}, sid)
        except Exception: pass
    if pre_script: cdp.send("Page.addScriptToEvaluateOnNewDocument", {"source": pre_script}, sid)
    if url != "about:blank":
        cdp.send("Page.navigate", {"url": url}, sid); time.sleep(wait)
    return tid, sid
def navigate(sid, url, wait=2.0):
    H.cdp.send("Page.navigate", {"url": url}, sid); time.sleep(wait)
def close_tab(tid):
    try: H.cdp.send("Target.closeTarget", {"targetId": tid})
    except Exception: pass
    time.sleep(0.5)
def tabs(): return H.cdp.send("Target.getTargets")["targetInfos"]
def open_tabs_with(sub): return [t for t in tabs() if sub in t["url"]]
def shot(sid, name):
    d = H.cdp.send("Page.captureScreenshot", {"format": "png"}, sid)["data"]
    path = os.path.join(SHOTS, name + ".png"); open(path, "wb").write(base64.b64decode(d)); return path
def wait_for(fn, t=8):
    end = time.time() + t
    while time.time() < end:
        try:
            v = fn()
            if v: return v
        except Exception: pass
        time.sleep(0.3)
    return False

def mouse(sid, t, x, y, buttons=0):
    H.cdp.send("Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": "left" if buttons or t == "mouseReleased" else "none",
               "buttons": buttons, "clickCount": 0 if t == "mouseMoved" else 1}, sid)
def mouse_click(sid, x, y):
    mouse(sid, "mouseMoved", x, y); mouse(sid, "mousePressed", x, y, 1); mouse(sid, "mouseReleased", x, y); time.sleep(0.6)

def full_text(n):
    if n["nodeType"] == 3: return n.get("nodeValue", "")
    return "".join(full_text(c) for c in n.get("children", []) or [])
def shadow_elems(sid):
    root = H.cdp.send("DOM.getDocument", {"depth": -1, "pierce": True}, sid)["root"]; out = []
    def rec(n, ins):
        if n["nodeType"] == 1 and ins and n["nodeName"] != "STYLE":
            a = n.get("attributes", []); at = dict(zip(a[0::2], a[1::2]))
            out.append({"tag": n["nodeName"], "cls": at.get("class", ""), "text": full_text(n), "id": n["nodeId"], "attrs": at})
        for c in n.get("children", []) or []: rec(c, ins)
        for c in n.get("shadowRoots", []) or []: rec(c, True)
        if n.get("contentDocument"): rec(n["contentDocument"], ins)
    rec(root, False); return out
def center(sid, nid):
    q = H.cdp.send("DOM.getContentQuads", {"nodeId": nid}, sid)["quads"][0]
    return sum(q[0::2]) / 4, sum(q[1::2]) / 4
def click_shadow(sid, tag, prefix):
    for e in shadow_elems(sid):
        if e["tag"] == tag and e["text"].startswith(prefix):
            mouse_click(sid, *center(sid, e["id"])); return True
    return False

def iso_ctx(sid):
    for _ in range(24):
        c = [x for x in ISO.get(sid, []) if H.EXT_ID in x[1]]
        if c: return c[-1][0]
        time.sleep(0.25)
    return None
def cs_eval(sid, expr):
    r = H.cdp.send("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True, "contextId": iso_ctx(sid)}, sid, timeout=60)
    if "exceptionDetails" in r: raise RuntimeError("cs eval: " + json.dumps(r["exceptionDetails"])[:300])
    return r["result"].get("value")
def cs_send(sid, msg):
    return cs_eval(sid, "chrome.runtime.sendMessage(%s).then(r=>r,e=>({threw:String(e)}))" % json.dumps(msg))
def ext_errors():
    return [l for l in LOGS if (l[0] == "SW" or "chrome-extension" in str(l[0])) and (l[1] == "exception" or l[1].endswith("error")) and "Failed to load resource" not in l[2]]
