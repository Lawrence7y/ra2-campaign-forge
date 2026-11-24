#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find mouse/hover-cell global by differential read-only memory scan.
Snapshot a region, move cursor, snapshot again, report changed dwords.
Reads only; synthetic mouse move. Usage: find_mouse_global.py <base_hex> <size_hex> x1,y1 x2,y2
"""
import sys, time, ctypes, struct
import w177_core as W
from w177_click import game_hwnd, force_foreground

u32 = ctypes.windll.user32; u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.GetCursorPos.argtypes=[ctypes.POINTER(ctypes.wintypes.POINT)]

def snap(m, base, size):
    buf = ctypes.create_string_buffer(size); got = ctypes.c_size_t(0)
    if not W.k32.ReadProcessMemory(m.h, ctypes.c_void_p(base), buf, size, ctypes.byref(got)) or got.value != size:
        return None
    return buf.raw

def main():
    base=int(sys.argv[1],0); size=int(sys.argv[2],0)
    p1=tuple(int(v) for v in sys.argv[3].split(','))
    p2=tuple(int(v) for v in sys.argv[4].split(','))
    pid=W.pid_of(); m=W.Mem(pid)
    h=game_hwnd(pid); force_foreground(h,0.3)
    # dwell at p1
    u32.SetCursorPos(*p1); time.sleep(0.8)
    a=snap(m,base,size)
    u32.SetCursorPos(*p2); time.sleep(0.8)
    b=snap(m,base,size)
    if a is None or b is None:
        print("READ FAILED"); return 1
    changes=[]
    for off in range(0,size-3,4):
        va=struct.unpack_from('<I',a,off)[0]; vb=struct.unpack_from('<I',b,off)[0]
        if va!=vb:
            changes.append((base+off,va,vb))
    print("region %X..%X size=%X changes=%d"%(base,base+size,size,len(changes)))
    # Show changes where either value looks like plausible cell coord / packed coord / pixel coord
    def interesting(va,vb):
        for v in (va,vb):
            if not v or v>0x7fffffff: continue
            lo=v&0xFFFF; hi=(v>>16)&0xFFFF
            # packed cell (x=lo,y=hi) in map range
            if 0<lo<512 and 0<hi<512: return True
            # plain small coordinate
            if 0<v<2560: return True
        return False
    filt=[c for c in changes if interesting(c[1],c[2])]
    print("interesting=%d"%len(filt))
    for addr,va,vb in filt[:200]:
        print("%08X  %08X -> %08X  (lo %d/%d hi %d/%d)"%(addr,va,vb,va&0xFFFF,vb&0xFFFF,(va>>16)&0xFFFF,(vb>>16)&0xFFFF))
    # save all changes
    import json,os
    out=os.path.join(os.path.dirname(os.path.abspath(__file__)),'mouse_scan_changes.json')
    with open(out,'w') as f:
        json.dump({'base':hex(base),'size':hex(size),'p1':p1,'p2':p2,
                   'changes':[[hex(a),hex(v1),hex(v2)] for a,v1,v2 in changes]},f)
    print("saved",out)
    m.close(); return 0

if __name__=='__main__': main()
