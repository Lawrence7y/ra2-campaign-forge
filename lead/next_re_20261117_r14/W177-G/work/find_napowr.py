#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find all player NAPOWR buildings and their occupied cells (footprint), to derive
hover-cell -> footprint-origin offset."""
import ctypes
import w177_core as W
import wb_probe as P
import dsnap as D

def main():
    m=W.Mem(W.pid_of()); ph=P.player_house(m)
    base=m.u32(P.CELL_ARRAY); mapc=P.MAP_SINGLETON
    w=m.u32(mapc+0x14C); h=m.u32(mapc+0x150)
    # find NAPOWR objects
    aitems=m.u32(P.A_ABSTRACT_ITEMS); acount=m.u32(P.A_ABSTRACT)
    napowrs=[]
    for i in range(acount):
        p=m.u32(aitems+4*i)
        if not p or (p&3): continue
        nm,_=D.rtti_name(m,p)
        if not nm or 'BuildingClass' not in nm: continue
        if m.u32(p+0x21C)!=ph: continue
        tp=m.u32(p+0x520)
        short=P.ascii_at(m,tp+0x24,12) if tp and tp!=0xffffffff else '?'
        if short=='NAPOWR':
            lx=m.u32(p+0x9C); ly=m.u32(p+0xA0)
            napowrs.append((p,lx>>8,ly>>8,m.u8(p+0x81),m.u8(p+0x74)))
    print("player NAPOWR count",len(napowrs))
    for p,cx,cy,o1,o2 in napowrs:
        print("  obj=%s Location=(%d,%d) o1=%s o2=%s"%(hex(p),cx,cy,o1,o2))
    # for each NAPOWR, scan cells for chains containing it
    for p,cx,cy,o1,o2 in napowrs:
        hits=[]
        for yy in range(h):
            rb=base+((yy<<9))*4; buf=ctypes.create_string_buffer(w*4); got=ctypes.c_size_t(0)
            if not W.k32.ReadProcessMemory(m.h,ctypes.c_void_p(rb),buf,w*4,ctypes.byref(got)):continue
            for xx in range(w):
                cell=int.from_bytes(buf.raw[xx*4:xx*4+4],'little')
                if not cell or cell==P.INVALID_CELL:continue
                head=m.u32(cell+0xE4); seen=set(); q=head
                while q and q not in seen and len(seen)<16:
                    seen.add(q)
                    if q==p: hits.append((xx,yy)); break
                    q=m.u32(q+0x30)
        print("  obj=%s footprint cells (%d): %s"%(hex(p),len(hits),sorted(hits)))
    m.close()

if __name__=='__main__':main()
