# -*- coding: utf-8 -*-
"""PATCH-D35 bounded smoke runner.
Each run: launch the PATCHED COPY from PATCH_D35/work/run (never ra2youli\),
apply a bounded GUI input sequence, observe crash/liveness/except.txt, then close.
No memory writes, no injection, no breakpoints. Read-only observation + GUI input only.
"""
import os, sys, subprocess, time, hashlib, ctypes, json

RUN  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35\work\run"
EXE  = os.path.join(RUN, "gamemd.exe")
EXCEPT = os.path.join(RUN, "except.txt")
LOGD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35\EVIDENCE"

u32 = ctypes.windll.user32
VK_RETURN, VK_ESCAPE = 0x0D, 0x1B
VK_LEFT, VK_RIGHT, VK_UP, VK_DOWN = 0x25, 0x27, 0x26, 0x28
KEYEVENTF_KEYUP = 0x2

def key(vk):
    u32.keybd_event(vk, 0, 0, 0); time.sleep(0.05)
    u32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0); time.sleep(0.15)

def click(x, y):
    u32.SetCursorPos(x, y); time.sleep(0.1)
    u32.mouse_event(0x2, 0, 0, 0, 0); time.sleep(0.05)   # LEFTDOWN
    u32.mouse_event(0x4, 0, 0, 0, 0); time.sleep(0.15)   # LEFTUP

def sha(p):
    if not os.path.exists(p): return None
    return hashlib.sha256(open(p,"rb").read()).hexdigest().upper()

def gamemd_count():
    out = subprocess.run(["powershell","-NoProfile","-Command",
        "(Get-Process gamemd -ErrorAction SilentlyContinue | Measure-Object).Count"],
        capture_output=True, text=True).stdout.strip()
    try: return int(out)
    except ValueError: return -1

def wintitle(pid):
    out = subprocess.run(["powershell","-NoProfile","-Command",
        f"(Get-Process -Id {pid} -EA SilentlyContinue).MainWindowTitle"],
        capture_output=True, text=True).stdout.strip()
    return out

SCENARIOS = {
    "boot":       lambda: None,
    "enter":      lambda: (key(VK_RETURN),),
    "menu_nav":   lambda: (key(VK_RETURN), key(VK_DOWN), key(VK_RETURN)),
    "click_ctr":  lambda: (key(VK_RETURN), click(640,360), click(500,400), key(VK_RETURN)),
    "enter_esc":  lambda: (key(VK_RETURN), key(VK_ESCAPE), key(VK_RETURN)),
    "arrows":     lambda: (key(VK_RETURN), key(VK_UP), key(VK_DOWN), key(VK_LEFT), key(VK_RIGHT), key(VK_RETURN)),
    "multi_enter":lambda: (key(VK_RETURN), key(VK_RETURN), key(VK_RETURN), key(VK_RETURN)),
    "click_multi":lambda: (click(300,300), click(640,360), click(900,500), key(VK_RETURN), click(640,400)),
}

def main():
    tag = sys.argv[1] if len(sys.argv)>1 else "boot"
    observe = int(sys.argv[2]) if len(sys.argv)>2 else 12
    before_cnt = gamemd_count()
    if before_cnt != 0:
        print(json.dumps({"tag":tag,"error":"existing gamemd=%d"%before_cnt})); sys.exit(2)
    be = (os.path.getsize(EXCEPT), sha(EXCEPT)) if os.path.exists(EXCEPT) else (None,None)
    p = subprocess.Popen([EXE], cwd=RUN, close_fds=True)
    time.sleep(3)                      # let window come up
    title = wintitle(p.pid)
    try:
        SCENARIOS.get(tag, SCENARIOS["boot"])()
    except Exception as e:
        print("input error:", e)
    exited=None
    for i in range(observe):
        time.sleep(1)
        if p.poll() is not None:
            exited=p.poll(); break
    alive = (p.poll() is None)
    ae = (os.path.getsize(EXCEPT), sha(EXCEPT)) if os.path.exists(EXCEPT) else (None,None)
    changed = be != ae
    appended=""
    if changed and os.path.exists(EXCEPT):
        data=open(EXCEPT,"rb").read()
        if be[0] is not None and len(data)>be[0]:
            appended=data[be[0]:].decode("latin1","replace")[-2000:]
    res={"tag":tag,"pid":p.pid,"window_title":title,"observe_s":observe,
         "exited":exited,"alive_at_end":alive,"except_before":be,"except_after":ae,
         "except_changed":changed,"except_appended":appended}
    if alive:
        try:
            p.terminate()
            try: p.wait(timeout=5)
            except subprocess.TimeoutExpired: p.kill(); p.wait()
        except Exception as e: res["term_error"]=str(e)
    res["final_gamemd_count"]=gamemd_count()
    line=json.dumps(res,ensure_ascii=False)
    print(line)
    with open(os.path.join(LOGD,"smoke_%s.json"%tag),"w",encoding="utf-8") as f:
        f.write(line+"\n")

if __name__=="__main__":
    main()
