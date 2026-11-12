import ctypes, ctypes.wintypes as wt, importlib.util, sys, time
from pathlib import Path
BASE=Path(r"D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112")
PID=int(sys.argv[1])
u=ctypes.WinDLL("user32",use_last_error=True); k=ctypes.WinDLL("kernel32",use_last_error=True)
u.GetWindowThreadProcessId.restype=wt.DWORD; u.GetWindowThreadProcessId.argtypes=[wt.HWND,ctypes.POINTER(wt.DWORD)]
u.GetClassNameW.restype=ctypes.c_int; u.GetClassNameW.argtypes=[wt.HWND,wt.LPWSTR,ctypes.c_int]
u.EnumWindows.restype=wt.BOOL; u.EnumWindows.argtypes=[ctypes.c_void_p,wt.LPARAM]
k.OpenProcess.restype=wt.HANDLE; k.OpenProcess.argtypes=[wt.DWORD,wt.BOOL,wt.DWORD]
k.CloseHandle.argtypes=[wt.HANDLE]
ENUM=ctypes.WINFUNCTYPE(wt.BOOL,wt.HWND,wt.LPARAM)
def wcls(h):
    b=ctypes.create_unicode_buffer(256); u.GetClassNameW(h,b,256); return b.value
hw=[] 
def cb(h,l):
    q=wt.DWORD(0); u.GetWindowThreadProcessId(h,ctypes.byref(q))
    if q.value==PID and wcls(h)=="Yuri's Revenge": hw.append(h)
    return True
u.EnumWindows(ENUM(cb),0)
if not hw: print("!! 无游戏窗口"); sys.exit(3)
# ★ GetWindowThreadProcessId 的**返回值**是线程 id；lpdwProcessId 输出的是进程 id
_pout=wt.DWORD(0)
_real_tid=u.GetWindowThreadProcessId(hw[0],ctypes.byref(_pout))
print("游戏窗口: 线程 tid=%d  进程 pid=%d (API 返回线程id)"%(int(_real_tid),_pout.value))
tid=_real_tid

spec=importlib.util.spec_from_file_location("cand",str(BASE/"e3_stack_sampler_candidate.py"))
cand=importlib.util.module_from_spec(spec); sys.argv=["x"]
try: spec.loader.exec_module(cand)
except SystemExit: pass
cand.bind_real_ops()
hproc=cand.OPS["open_process"](0x0010|0x0400,PID)
is32=bool(cand.OPS["is_wow64"](hproc))
s=cand.StackSampler(budget_ms=400.0); s._target_is32=is32
ok,err=cand.attach_stackwalker(s,hproc,PID,is32)
print("StackWalker=%s %s"%(ok,err or ""))
print()
print("=== 单线程采样 × 6 次，测量耗时 ===")
costs=[]
for i in range(6):
    t=time.monotonic()
    r=s.sample_one_thread(int(_real_tid))
    c=(time.monotonic()-t)*1000.0
    costs.append(c)
    fr=r.get("frames") or []
    print("  #%d cost=%6.2f ms  frames=%d  tid=%s prev=%s"%(i,c,len(fr),r.get("tid"),r.get("prev")))
    if fr and i==0:
        for j,f in enumerate(fr):
            print("       #%d %s"%(j, f.get("name") if isinstance(f,dict) else f))
print()
import statistics
print("耗时: min=%.2f 中位=%.2f max=%.2f ms"%(min(costs),statistics.median(costs),max(costs)))
print("[PASS] 全部 <=50ms" if max(costs)<=50 else "[WARN] 有超 50ms 的样本")
print("resume_errors=%s"%(getattr(s,"_resume_errors",None),))
try:
    if ok: s.stack_walker.cleanup()
except Exception: pass
cand.OPS["close_handle"](hproc)
