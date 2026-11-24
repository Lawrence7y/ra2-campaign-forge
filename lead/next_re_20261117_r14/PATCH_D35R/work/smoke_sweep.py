# -*- coding: utf-8 -*-
"""PATCH-D35R: broad GUI sweep, frequent read-only counter sampling.
Records every distinct (hit_count, last_ret) transition. A last_ret equal to
(site VA + 5) proves the stub executed at that wired site.
"""
import os, subprocess, time, ctypes, json
from ctypes import wintypes

RUN=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35R\work\run"
EXE=os.path.join(RUN,"gamemd.exe")
LOGD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35R\EVIDENCE"
CTR_LAST,CTR_COUNT=0x9F5000,0x9F5004
SITE_RETS={0x6D1632+5:'006D1632',0x6D09FA+5:'006D09FA',0x640427+5:'00640427',
           0x6D059B+5:'006D059B',0x6D0634+5:'006D0634',0x6D1293+5:'006D1293',
           0x6D0940+5:'006D0940',0x6D1308+5:'006D1308'}
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
    r=[];W=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    def cb(h,l):
        p=wintypes.DWORD();u32.GetWindowThreadProcessId(h,ctypes.byref(p))
        if p.value==pid and u32.IsWindowVisible(h):r.append(h)
        return True
    u32.EnumWindows(W(cb),0);return r[0] if r else None

def key(vk):u32.keybd_event(vk,0,0,0);time.sleep(.04);u32.keybd_event(vk,0,2,0);time.sleep(.1)
def click(x,y):u32.SetCursorPos(x,y);time.sleep(.03);u32.mouse_event(2,0,0,0,0);time.sleep(.03);u32.mouse_event(4,0,0,0,0);time.sleep(.1)
def title(pid):return subprocess.run(["powershell","-NoProfile","-Command",f"(Get-Process -Id {pid}).MainWindowTitle"],capture_output=True,text=True).stdout.strip()

def main():
    p=subprocess.Popen([EXE],cwd=RUN,close_fds=True);time.sleep(5)
    if p.poll() is not None: print("early exit",p.poll());return
    h=find_hwnd(p.pid);u32.ShowWindow(h,9);u32.SetForegroundWindow(h);time.sleep(.6)
    events=[];seen=set();maxhit=0;observed_sites=set()
    def poll(n=3,dt=.15):
        nonlocal maxhit
        for _ in range(n):
            if p.poll() is not None:return
            c=rp(p.pid,CTR_COUNT);lr=rp(p.pid,CTR_LAST)
            if c is not None: maxhit=max(maxhit,c)
            key=(c,lr)
            if lr and (c,lr) not in seen:
                seen.add((c,lr))
                site=SITE_RETS.get(lr,"UNKNOWN")
                if site!="UNKNOWN": observed_sites.add(site)
                events.append({"hit_count":c,"last_ret":lr,"last_ret_hex":hex(lr),"site":site,"title":title(p.pid)})
            time.sleep(dt)
    poll(3)
    # reproduce the earlier successful path to menu state
    u32.SetForegroundWindow(h);click(512,403);poll(2)
    u32.SetForegroundWindow(h);click(512,480);poll(2)
    u32.SetForegroundWindow(h);key(0x0D);poll(2)
    u32.SetForegroundWindow(h);key(0x28);poll(2)
    u32.SetForegroundWindow(h);key(0x0D);poll(2)
    u32.SetForegroundWindow(h);click(853,576);poll(6)  # this hit 0x640427 last run
    # broad sweep: grid of clicks + keys, poll frequently
    for yy in [300,400,500,600,700,800]:
        for xx in [300,500,700,900,1100,1300]:
            if p.poll() is not None: break
            u32.SetForegroundWindow(h);click(xx,yy);poll(2)
    for vk in [0x0D,0x28,0x26,0x25,0x27,0x0D,0x1B,0x0D]:
        if p.poll() is not None: break
        u32.SetForegroundWindow(h);key(vk);poll(3)
    # long idle observe (in-game sidebar functions fire continuously if in game)
    for _ in range(20): poll(2)
    alive=p.poll() is None
    res={"pid":p.pid,"alive":alive,"rc":p.poll(),"max_hit_count":maxhit,
         "observed_sites":sorted(observed_sites),"events":events}
    if alive:
        p.terminate()
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.kill();p.wait()
    res["final_count"]=subprocess.run(["powershell","-NoProfile","-Command","(Get-Process gamemd -EA SilentlyContinue | Measure-Object).Count"],capture_output=True,text=True).stdout.strip()
    with open(os.path.join(LOGD,"smoke_r2_sweep.json"),"w",encoding="utf-8") as f:
        f.write(json.dumps(res,ensure_ascii=False,indent=1)+"\n")
    print(json.dumps({"pid":p.pid,"alive":alive,"rc":p.poll(),"max_hit_count":maxhit,"observed_sites":sorted(observed_sites),"n_events":len(events),"final_count":res["final_count"]},ensure_ascii=False))

if __name__=="__main__":main()
