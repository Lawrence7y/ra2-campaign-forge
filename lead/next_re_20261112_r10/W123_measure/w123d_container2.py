#!/usr/bin/env python3
"""W123d: sample frame + container 0xA8ED3C count (0xA8ED50). READ-ONLY."""
import ctypes, struct, sys, time, statistics
from ctypes import wintypes as wt
FRAME=0x00A8ED84; CB=0x00A8ED3C
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
    print("pid=%d sampling %ds"%(pid,secs))
    f=open(out,"w",encoding="utf-8") if out else None
    if f: f.write("t_wall\tframe\tcount\tbuf\tthr\n")
    last=m.u32(FRAME); prev=time.perf_counter()
    samples=[]; cur=0; n=0; lastc=0.0
    cs=[]; bufs=[]; thrs=[]
    t_start=time.perf_counter()
    while time.perf_counter()-t_start<secs:
        fr=m.u32(FRAME); nown=time.perf_counter()
        if nown-lastc>0.05:
            c=m.u32(CB+0x14); b=m.u32(CB+0x08); th=m.u32(CB+0x0C)
            if c is not None: cur=c; cs.append(c)
            if b is not None: bufs.append(b)
            if th is not None: thrs.append(th)
            lastc=nown
        if fr is not None and last is not None and fr!=last:
            dt=(nown-prev)*1000.0
            samples.append((dt,cur)); prev=nown; last=fr; n+=1
            if f: f.write("%.4f\t%d\t%d\t%d\t%d\n"%(time.time(),fr,cur,m.u32(CB+0x08) or 0,m.u32(CB+0x0C) or 0))
        time.sleep(0.002)
    if f: f.close()
    print("frame advances: %d"%n)
    if cs:
        print("container count: min=%d max=%d median=%d last=%d"%(min(cs),max(cs),int(statistics.median(cs)),cs[-1]))
        print("buffer base uniq=%s  threshold uniq=%s"%(sorted(set(bufs))[:3], sorted(set(thrs))[:3]))
    if samples:
        ds=sorted(d for d,_ in samples)
        print("interval: med=%.2f p90=%.2f  >36ms=%.2f%%"%(statistics.median(ds), ds[int(len(ds)*.9)], 100*sum(1 for d in ds if d>36)/len(ds)))
    return 0
if __name__=="__main__":
    a=sys.argv
    sys.exit(main(int(a[1]), float(a[2]) if len(a)>2 else 90.0, a[3] if len(a)>3 else None))