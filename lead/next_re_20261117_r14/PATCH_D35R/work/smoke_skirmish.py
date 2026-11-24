# -*- coding: utf-8 -*-
"""PATCH-D35R: skirmish-attempt GUI driver with per-step read-only counter sampling.
Reads counter after each input. Any nonzero last_call_ret identifies the wired
site that fired (ret addr == site VA + 5).
"""
import os, subprocess, time, ctypes, json
from ctypes import wintypes

RUN=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35R\work\run"
EXE=os.path.join(RUN,"gamemd.exe")
LOGD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35R\EVIDENCE"
CTR_LAST,CTR_COUNT=0x9F5000,0x9F5004
k32=ctypes.windll.kernel32
k32.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k32.OpenProcess.restype=wintypes.HANDLE
k32.ReadProcessMemory.argtypes=[wintypes.HANDLE,wintypes.LPCVOID,wintypes.LPVOID,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
u32=ctypes.windll.user32

def rp(pid,a):
    h=k32.OpenProcess(0x10|0x400,False,pid)
    if not h: return None
    try:
        b=ctypes.c_uint32(0);n=ctypes.c_size_t(0)
        return b.value if k32.ReadProcessMemory(h,ctypes.c_void_p(a),ctypes.byref(b),4,ctypes.byref(n)) else None
    finally:k32.CloseHandle(h)

def find_hwnd(pid):
    r=[];WND=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    def cb(h,l):
        p=wintypes.DWORD();u32.GetWindowThreadProcessId(h,ctypes.byref(p))
        if p.value==pid and u32.IsWindowVisible(h): r.append(h)
        return True
    u32.EnumWindows(WND(cb),0);return r[0] if r else None

def rect(h):
    r=wintypes.RECT();u32.GetWindowRect(h,ctypes.byref(r));return (r.left,r.top,r.right,r.bottom)

def key(vk):
    u32.keybd_event(vk,0,0,0);time.sleep(.05);u32.keybd_event(vk,0,2,0);time.sleep(.12)

def click(x,y):
    u32.SetCursorPos(x,y);time.sleep(.05);u32.mouse_event(2,0,0,0,0);time.sleep(.04);u32.mouse_event(4,0,0,0,0);time.sleep(.15)

def title(pid):
    return subprocess.run(["powershell","-NoProfile","-Command",f"(Get-Process -Id {pid}).MainWindowTitle"],capture_output=True,text=True).stdout.strip()

def main():
    p=subprocess.Popen([EXE],cwd=RUN,close_fds=True);time.sleep(5)
    if p.poll() is not None: print("early exit",p.poll());return
    h=find_hwnd(p.pid);u32.ShowWindow(h,9);u32.SetForegroundWindow(h);time.sleep(.8)
    L,T,R,B=rect(h);W,RR=R-L,B-T
    steps=[]
    def log(name):
        steps.append({"step":name,"title":title(p.pid),
                      "hit_count":rp(p.pid,CTR_COUNT),"last_ret":rp(p.pid,CTR_LAST),
                      "rect":[L,T,R,B]})
    log("menu_after_fg")
    # RA2/YR main menu: click around center-left column where buttons live; sample each
    seq=[
        ("click_1",  lambda:click(L+int(W*0.30),T+int(RR*0.42))),
        ("click_2",  lambda:click(L+int(W*0.30),T+int(RR*0.50))),
        ("enter_1",  lambda:key(0x0D)),
        ("down",     lambda:key(0x28)),
        ("enter_2",  lambda:key(0x0D)),
        ("click_3",  lambda:click(L+int(W*0.50),T+int(RR*0.60))),
        ("enter_3",  lambda:key(0x0D)),
        ("down2",    lambda:key(0x28)),
        ("enter_4",  lambda:key(0x0D)),
        ("click_ctr",lambda:click(L+int(W*0.50),T+int(RR*0.50))),
        ("enter_5",  lambda:key(0x0D)),
        ("esc_1",    lambda:key(0x1B)),
    ]
    for name,fn in seq:
        if p.poll() is not None:
            steps.append({"step":name,"process_exited":p.poll()});break
        u32.SetForegroundWindow(h);time.sleep(.2)
        try: fn()
        except Exception as e: steps.append({"step":name,"err":str(e)});continue
        time.sleep(.8);log(name)
    alive=p.poll() is None
    res={"pid":p.pid,"rect":[L,T,R,B],"alive":alive,"rc":p.poll(),"steps":steps}
    if alive:
        p.terminate()
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.kill();p.wait()
    res["final_count"]=subprocess.run(["powershell","-NoProfile","-Command","(Get-Process gamemd -EA SilentlyContinue | Measure-Object).Count"],capture_output=True,text=True).stdout.strip()
    with open(os.path.join(LOGD,"smoke_r2_skirmish.json"),"w",encoding="utf-8") as f:
        f.write(json.dumps(res,ensure_ascii=False,indent=1)+"\n")
    print(json.dumps(res,ensure_ascii=False))

if __name__=="__main__":main()
