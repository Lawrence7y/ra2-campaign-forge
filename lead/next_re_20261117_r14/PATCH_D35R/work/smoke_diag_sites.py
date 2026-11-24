# -*- coding: utf-8 -*-
"""DIAG: continuous background sampling of counter while driving GUI."""
import os, subprocess, time, ctypes, json, threading
from ctypes import wintypes
RUN=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35R\work\run"
EXE=os.path.join(RUN,"gamemd.exe")
LOGD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35R\EVIDENCE"
CTR_LAST,CTR_COUNT=0x9F5000,0x9F5004
ALL_SITES=[0x6D1632,0x6D09FA,0x640427,0x6D059B,0x6D0634,0x6D1293,0x6D0940,0x4A8B75]
RET2SITE={s+5:s for s in ALL_SITES}
k32=ctypes.windll.kernel32
k32.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k32.OpenProcess.restype=wintypes.HANDLE
k32.ReadProcessMemory.argtypes=[wintypes.HANDLE,wintypes.LPCVOID,wintypes.LPVOID,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
u32=ctypes.windll.user32
def rp(pid,a):
    h=k32.OpenProcess(0x10|0x400,False,pid)
    if not h:return None
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
def key(vk):u32.keybd_event(vk,0,0,0);time.sleep(.03);u32.keybd_event(vk,0,2,0);time.sleep(.09)
def click(x,y):u32.SetCursorPos(x,y);time.sleep(.02);u32.mouse_event(2,0,0,0,0);time.sleep(.02);u32.mouse_event(4,0,0,0,0);time.sleep(.09)
def main():
    p=subprocess.Popen([EXE],cwd=RUN,close_fds=True);time.sleep(5)
    if p.poll() is not None:print("early exit",p.poll());return
    h=find_hwnd(p.pid);u32.ShowWindow(h,9);u32.SetForegroundWindow(h);time.sleep(.5)
    stop=threading.Event();samples=[];lock=threading.Lock();maxhit=[0]
    def sampler():
        while not stop.is_set():
            c=rp(p.pid,CTR_COUNT);lr=rp(p.pid,CTR_LAST)
            with lock:
                if c is not None:maxhit[0]=max(maxhit[0],c)
                samples.append((c,lr))
            time.sleep(.04)
    t=threading.Thread(target=sampler,daemon=True);t.start()
    for x,y in [(512,403),(512,480),(853,576),(300,300),(900,500),(700,400),(1100,600),(500,700)]:
        if p.poll() is not None:break
        u32.SetForegroundWindow(h);click(x,y);time.sleep(.5)
    for _ in range(3):
        for vk in [0x0D,0x28,0x26,0x25,0x27,0x0D,0x1B]:
            if p.poll() is not None:break
            u32.SetForegroundWindow(h);key(vk);time.sleep(.25)
    for yy in [300,420,540,660,780]:
        for xx in [250,450,650,850,1050,1250,1450]:
            if p.poll() is not None:break
            u32.SetForegroundWindow(h);click(xx,yy);time.sleep(.15)
    time.sleep(3)
    stop.set();t.join(timeout=2)
    with lock:
        uniq=sorted({lr for c,lr in samples if lr})
        hit_sites=sorted({RET2SITE.get(lr) for lr in uniq if lr in RET2SITE})
        unknown=sorted({lr for lr in uniq if lr not in RET2SITE})
        maxc=maxhit[0]
    alive=p.poll() is None
    res={"pid":p.pid,"alive":alive,"max_hit_count":maxc,
         "distinct_last_rets":[hex(x) for x in uniq],
         "hit_sites":[f'{s:06X}' for s in hit_sites],
         "unknown_rets":[hex(x) for x in unknown],"n_samples":len(samples)}
    if alive:
        p.terminate()
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.kill();p.wait()
    with open(os.path.join(LOGD,"smoke_r2_diag_sites.json"),"w",encoding="utf-8") as f:
        f.write(json.dumps(res,ensure_ascii=False,indent=1)+"\n")
    print(json.dumps(res,ensure_ascii=False))

if __name__=="__main__":main()
