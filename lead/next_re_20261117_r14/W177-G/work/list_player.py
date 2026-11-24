#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enumerate player units/buildings with proper short type names at +0x520+0x24."""
import w177_core as W
import wb_probe as P
import dsnap as D

def main():
    m=W.Mem(W.pid_of()); ph=P.player_house(m)
    aitems=m.u32(P.A_ABSTRACT_ITEMS); acount=m.u32(P.A_ABSTRACT)
    for i in range(acount):
        p=m.u32(aitems+4*i)
        if not p or (p&3): continue
        nm,d=D.rtti_name(m,p)
        if not nm: continue
        owner=m.u32(p+0x21C)
        if owner!=ph: continue
        lx=m.u32(p+0x9C); ly=m.u32(p+0xA0)
        cx=(lx>>8) if lx else None; cy=(ly>>8) if ly else None
        tp=m.u32(p+0x520)
        short=P.ascii_at(m,tp+0x24,12) if tp else None
        print("%-28s short=%-10s cell=(%s,%s) this=%s o1=%s o2=%s"%(
            nm.replace('.?AV','').replace('@@',''),short,cx,cy,hex(p),m.u8(p+0x81),m.u8(p+0x74)))
    m.close()

if __name__=='__main__':main()
