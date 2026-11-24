# -*- coding: utf-8 -*-
"""PATCH-D35R bounded smoke v2: foreground the game window before input.

Read-only counter sampling via ReadProcessMemory (VM_READ). No writes/injection.
Screenshots captured while game is alive for state evidence.
"""
import os, sys, subprocess, time, hashlib, ctypes, json
from ctypes import wintypes

RUN  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35R\work\run"
EXE  = os.path.join(RUN, "gamemd.exe")
EXCEPT = os.path.join(RUN, "except.txt")
LOGD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35R\EVIDENCE"
CTR_LAST, CTR_COUNT = 0x009F5000, 0x009F5004
PROCESS_VM_READ, PROCESS_QUERY_INFORMATION = 0x0010, 0x0400

k32 = ctypes.windll.kernel32
k32.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]; k32.OpenProcess.restype=wintypes.HANDLE
k32.ReadProcessMemory.argtypes=[wintypes.HANDLE,wintypes.LPCVOID,wintypes.LPVOID,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
k32.ReadProcessMemory.restype=wintypes.BOOL
u32=ctypes.windll.user32
VK_RETURN,VK_ESCAPE=0x0D,0x1B

def read_u32(pid,addr):
    h=k32.OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION,False,pid)
    if not h: return {"ok":False,"err":"OpenProcess"}
    try:
        b=ctypes.c_uint32(0); n=ctypes.c_size_t(0)
        ok=k32.ReadProcessMemory(h,ctypes.c_void_p(addr),ctypes.byref(b),4,ctypes.byref(n))
        return {"ok":bool(ok),"value":b.value if ok else None,"hex":hex(b.value) if ok else None}
    finally: k32.CloseHandle(h)

def sample(pid,label):
    return {"label":label,"last_call_ret":read_u32(pid,CTR_LAST),"hit_count":read_u32(pid,CTR_COUNT)}

def foreground(hwnd):
    try:
        u32.ShowWindow(hwnd,9)   # SW_RESTORE
        u32.SetForegroundWindow(hwnd); time.sleep(0.5)
        return u32.GetForegroundWindow()==hwnd
    except Exception as e:
        return False

def key(vk):
    u32.keybd_event(vk,0,0,0); time.sleep(0.06)
    u32.keybd_event(vk,0,2,0); time.sleep(0.15)

def shot(path):
    ps=("Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
        "$b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
        "$bmp=New-Object System.Drawing.Bitmap($b.Width,$b.Height); "
        "$g=[System.Drawing.Graphics]::FromImage($bmp); "
        "$g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size); "
        f"$bmp.Save('{path}',[System.Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()")
    subprocess.run(["powershell","-NoProfile","-Command",ps],capture_output=True,text=True)

def find_hwnd(pid):
    r=[]
    WNDENUMPROC=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    def cb(h,l):
        p=wintypes.DWORD(); u32.GetWindowThreadProcessId(h,ctypes.byref(p))
        if p.value==pid and u32.IsWindowVisible(h): r.append(h)
        return True
    u32.EnumWindows(WNDENUMPROC(cb),0)
    return r[0] if r else None

def main():
    tag=sys.argv[1] if len(sys.argv)>1 else "boot"
    obs=int(sys.argv[2]) if len(sys.argv)>2 else 6
    p=subprocess.Popen([EXE],cwd=RUN,close_fds=True)
    time.sleep(4)
    if p.poll() is not None:
        print(json.dumps({"tag":tag,"error":"early_exit","rc":p.poll()})); return
    hwnd=find_hwnd(p.pid)
    fg=foreground(hwnd) if hwnd else False
    title=subprocess.run(["powershell","-NoProfile","-Command",f"(Get-Process -Id {p.pid}).MainWindowTitle"],capture_output=True,text=True).stdout.strip()
    shot(os.path.join(LOGD,f"smoke_r2_{tag}_fg.png"))
    s1=sample(p.pid,"after_foreground")
    # input only if foreground succeeded
    if fg:
        if tag=="enter": key(VK_RETURN)
        elif tag=="menu_nav": key(VK_RETURN); time.sleep(.3); key(VK_RETURN)
        elif tag=="arrows":
            for vk in (VK_RETURN,0x26,0x28,0x25,0x27,VK_RETURN): key(vk)
        elif tag=="enter_esc": key(VK_RETURN); time.sleep(.3); key(VK_ESCAPE)
        elif tag=="multi_enter":
            for _ in range(4): key(VK_RETURN); time.sleep(.2)
        elif tag=="click_ctr":
            u32.SetCursorPos(640,360); u32.mouse_event(2,0,0,0,0); u32.mouse_event(4,0,0,0,0); time.sleep(.2)
            key(VK_RETURN)
        elif tag=="click_multi":
            for x,y in [(300,300),(640,360),(900,500)]:
                u32.SetCursorPos(x,y); u32.mouse_event(2,0,0,0,0); u32.mouse_event(4,0,0,0,0); time.sleep(.15)
            key(VK_RETURN)
    time.sleep(1.0)
    s2=sample(p.pid,"after_input")
    shot(os.path.join(LOGD,f"smoke_r2_{tag}_after.png"))
    exited=None
    for i in range(obs):
        time.sleep(1)
        if p.poll() is not None: exited=p.poll(); break
    alive=(p.poll() is None)
    s3=sample(p.pid,"after_observe") if alive else {"label":"exited","rc":exited}
    res={"tag":tag,"pid":p.pid,"hwnd":hwnd,"foreground_ok":fg,"window_title":title,
         "exited":exited,"alive_at_end":alive,"samples":[s1,s2,s3]}
    if alive:
        p.terminate()
        try: p.wait(timeout=5)
        except subprocess.TimeoutExpired: p.kill(); p.wait()
    with open(os.path.join(LOGD,f"smoke_r2v2_{tag}.json"),"w",encoding="utf-8") as f:
        f.write(json.dumps(res,ensure_ascii=False)+"\n")
    print(json.dumps(res,ensure_ascii=False))

if __name__=="__main__": main()
