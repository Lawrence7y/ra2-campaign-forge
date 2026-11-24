#!/usr/bin/env python3
"""W123e: identify what objects live in container 0xA8ED3C.
READ-ONLY. Resolves vtable -> COL -> TypeDescriptor name (MSVC RTTI)."""
import ctypes, struct, sys, time
from ctypes import wintypes as wt
CB=0x00A8ED3C; FRAME=0x00A8ED84
IB=0x400000
# .rdata / .data absolute ranges (for sanity)
RD_LO,RD_HI=0x7E1000,0x812000
DA_LO,DA_HI=0x812000,0xB79BE4
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
def cstr(b):
    if not b: return None
    z=b.find(b"\x00")
    try: return b[:z if z>=0 else len(b)].decode("ascii", "replace")
    except: return None
def class_of_vtable(m,v):
    """vtable[-4] = COL ; COL+0x0C = pTypeDescriptor ; TD+0x08 = name"""
    if not v or not (RD_LO<=v<RD_HI): return None
    col=m.u32(v-4)
    if not col or not (0x7E1000<=col<DA_HI): return None
    if m.u32(col)!=0: return None
    td=m.u32(col+0xC)
    if not td or not (0x7E1000<=td<DA_HI): return None
    return cstr(m.rd(td+8,96))
def main(pid,secs):
    m=Mem(pid); t0=time.time()
    while time.time()-t0<180:
        if m.u32(FRAME): break
        time.sleep(0.3)
    print("pid=%d  watching container 0x%08X"%(pid,CB))
    best=0; bestbuf=0
    ts=time.time()
    while time.time()-ts<secs:
        c=m.u32(CB+0x14) or 0
        if c>best:
            best=c; bestbuf=m.u32(CB+0x08) or 0
            print("  new max count=%d buf=0x%08X"%(best,bestbuf))
        if best>20: break
        time.sleep(0.1)
    if best==0:
        print("container stayed empty -> cannot identify"); return 2
    buf=m.u32(CB+0x08)
    n=m.u32(CB+0x14)
    print("\n=== elements (count=%d, buf=0x%08X) ==="%(n,buf or 0))
    seen={}
    for i in range(min(n,24)):
        e=buf+i*8
        obj=m.u32(e); slot=m.u32(e+4)
        v=m.u32(obj) if obj else None
        cls=class_of_vtable(m,v)
        print("  [%2d] obj=0x%08X vt=0x%08X  %s"%(i,obj or 0,v or 0,cls or "<unknown>"))
        if cls: seen[cls]=seen.get(cls,0)+1
    print("\nclass histogram (first 24):")
    for k,c in sorted(seen.items(), key=lambda kv:-kv[1]):
        print("   %-40s %d"%(k,c))
    return 0
if __name__=="__main__":
    a=sys.argv
    sys.exit(main(int(a[1]), float(a[2]) if len(a)>2 else 120.0))