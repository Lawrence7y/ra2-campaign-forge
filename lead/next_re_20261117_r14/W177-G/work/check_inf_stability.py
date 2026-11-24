#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check stability of player infantry cells across a few seconds (read-only)."""
import time, ctypes
import w177_core as W
import wb_probe as P
import dsnap as D

def scan_inf(m):
    ph=P.player_house(m)
    base=m.u32(P.CELL_ARRAY); mapc=P.MAP_SINGLETON
    w=m.u32(mapc+0x14C); h=m.u32(mapc+0x150)
    out={}
    for cy in range(h):
        rb=base+((cy<<9))*4; buf=ctypes.create_string_buffer(w*4); got=ctypes.c_size_t(0)
        if not W.k32.ReadProcessMemory(m.h,ctypes.c_void_p(rb),buf,w*4,ctypes.byref(got)):continue
        for cx in range(w):
            cell=int.from_bytes(buf.raw[cx*4:cx*4+4],'little')
            if not cell or cell==P.INVALID_CELL:continue
            head=m.u32(cell+0xE4); nodes=[]; seen=set(); p=head
            while p and p not in seen and len(nodes)<12:
                seen.add(p)
                nm,_=D.rtti_name(m,p)
                owner=m.u32(p+0x21C)
                if nm and 'InfantryClass' in nm and owner==ph:
                    nodes.append(p)
                p=m.u32(p+0x30)
            if nodes: out[(cx,cy)]=len(nodes)
    return out

def main():
    m=W.Mem(W.pid_of())
    print("frame0",m.u32(W.A_FRAME))
    s1=scan_inf(m)
    print("t0 cells",sorted(s1.keys()))
    time.sleep(3.0)
    s2=scan_inf(m)
    print("t3 cells",sorted(s2.keys()))
    print("stable", s1==s2)
    m.close()

if __name__=='__main__':main()
