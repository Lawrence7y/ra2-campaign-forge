#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enumerate all objects with RTTI names, report BuildingClass + UnitClass (MCV)."""
import ctypes
import w177_core as W
import wb_probe as P
import dsnap as D

def main():
    m=W.Mem(W.pid_of()); ph=P.player_house(m)
    aitems=m.u32(P.A_ABSTRACT_ITEMS); acount=m.u32(P.A_ABSTRACT)
    print("abstract count",acount,"playerHouse",hex(ph))
    bld=[]; units=[]
    HOVER=0x0088095C
    v=m.u32(HOVER); hx=v&0xFFFF; hy=(v>>16)&0xFFFF
    print("hover cell",(hx,hy))
    for i in range(acount):
        p=m.u32(aitems+4*i)
        if not p or (p&3): continue
        nm,_=D.rtti_name(m,p)
        if not nm: continue
        if 'BuildingClass' in nm or 'UnitClass' in nm:
            owner=m.u32(p+0x21C)
            lx=m.u32(p+0x9C); ly=m.u32(p+0xA0)
            cx=(lx>>8) if lx is not None else None
            cy=(ly>>8) if ly is not None else None
            rec={"this":hex(p),"type":nm.split('.')[-2] if '.' in nm else nm,"owner":hex(owner),
                 "is_player":owner==ph,"cell":(cx,cy)}
            if 'BuildingClass' in nm:
                rec["btype"]=P.ascii_at(m,m.u32(p+0x520)+0x24,12)
                bld.append(rec)
            else:
                units.append(rec)
    print("\n=== buildings (%d) ==="%len(bld))
    for b in bld:
        if b['is_player']: print(" ",b)
    print("\n=== units (%d), player ones ==="%len(units))
    for u in units:
        if u['is_player']: print(" ",u)
    m.close()

if __name__=='__main__':main()
