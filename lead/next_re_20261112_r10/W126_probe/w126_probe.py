#!/usr/bin/env python3
"""W126: sample frame + target-scan call counter (0xA8EC34) + bullet count (0xA8ED50).
READ-ONLY. Purpose: decide whether per-frame cost tracks target scans or bullets.
Uses the harness-independent engine counters."""
import ctypes, struct, sys, time, statistics
from ctypes import wintypes as wt
FRAME=0x00A8ED84; SCAN=0x00A8EC34; BULLET=0x00A8ED50
k32=ctypes.WinDLL("kernel32",use_last_error=True); k32.OpenProcess.restype=wt.HANDLE
class Mem:
    def __init__(self,pid):
        self.h=k32.OpenProcess(0x0010|0x1000,False,pid)
        if not self.h: raise OSError("OpenProcess")
    def rd(self,va,n):
        b=ctypes.create_string_buffer(n); g=ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(self.h,ctypes.c_void_p(va),b,n,ctypes.byref(g)) or g.value!=n: return None
        return b.raw
    def u32(self,va):
        b=self.rd(va,4); return None if b is None else struct.unpack("<I",b)[0]
def main(pid,secs,out):
    m=Mem(pid); t0=time.time()
    while time.time()-t0<180:
        if m.u32(FRAME): break
        time.sleep(0.3)
    f=open(out,"w",encoding="utf-8") if out else None
    if f: f.write("t\tframe\tscan\tbullet\n")
    t0s=time.perf_counter()
    n=0
    while time.perf_counter()-t0s<secs:
        fr=m.u32(FRAME); sc=m.u32(SCAN); bu=m.u32(BULLET)
        if None not in (fr,sc,bu):
            if f: f.write("%.4f\t%d\t%d\t%d\n"%(time.perf_counter()-t0s,fr,sc,bu))
            n+=1
        time.sleep(0.05)
    if f: f.close()
    print("samples=%d over %.1fs"%(n,secs))
    return 0
if __name__=="__main__":
    a=sys.argv
    sys.exit(main(int(a[1]), float(a[2]) if len(a)>2 else 90.0, a[3] if len(a)>3 else None))