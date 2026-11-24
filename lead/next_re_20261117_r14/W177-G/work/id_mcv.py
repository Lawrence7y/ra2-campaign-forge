#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump type pointer region for player units to identify MCV; and read hover cell at candidate screen points."""
import ctypes,time
from ctypes import wintypes as wt
import w177_core as W
import wb_probe as P
u32=ctypes.windll.user32; u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.GetCursorPos.argtypes=[ctypes.POINTER(wt.POINT)]
HOVER=0x0088095C

def ascii_run(m,va,n=64):
    raw=b''
    for i in range(n):
        v=m.u8(va+i)
        if v is None: break
        if 0x20<=v<=0x7e: raw+=bytes([v])
        else: raw+=b'.'
    return raw.decode('latin1')

def main():
    m=W.Mem(W.pid_of()); ph=P.player_house(m)
    aitems=m.u32(P.A_ABSTRACT_ITEMS); acount=m.u32(P.A_ABSTRACT)
    import dsnap as D
    for i in range(acount):
        p=m.u32(aitems+4*i)
        if not p or (p&3): continue
        nm,_=D.rtti_name(m,p)
        if not nm or 'UnitClass' not in nm: continue
        if m.u32(p+0x21C)!=ph: continue
        tp=m.u32(p+0x520)
        lx=m.u32(p+0x9C); ly=m.u32(p+0xA0)
        print("unit this=%s cell=(%d,%d) typeptr=%s"%(hex(p),lx>>8,ly>>8,hex(tp)))
        if tp:
            print("   tp+0x00..0x40: %s"%ascii_run(m,tp,64))
        # read what's at +0x24 as pointer
        print("   [tp+0x24]=%s"%hex(m.u32(tp+0x24)))
    # hover at candidate screen points for the truck seen near physical (660,420)
    for (sx,sy) in [(660,420),(700,460),(620,400),(760,500)]:
        u32.SetCursorPos(sx,sy); time.sleep(0.25)
        v=m.u32(HOVER)
        print("screen (%d,%d) -> cell (%d,%d)"%(sx,sy,v&0xFFFF,(v>>16)&0xFFFF))
    m.close()

if __name__=='__main__':main()
