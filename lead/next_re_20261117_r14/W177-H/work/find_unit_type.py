#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan player UnitClass objects for their type-id pointer: look for dword in obj whose
target+0x24 holds an ASCII short name (RA2 TypeClass layout). Identify MCV."""
import ctypes
import w177_core as W, wb_probe as P, dsnap as D

def name_at(m,va,n=20):
    raw=b''
    for i in range(n):
        v=m.u8(va+i)
        if v is None or v==0 or not (0x20<=v<=0x7e): break
        raw+=bytes([v])
    return raw.decode('latin-1') if raw else None

def main():
    m=W.Mem(W.pid_of()); ph=P.player_house(m)
    ai=m.u32(P.A_ABSTRACT_ITEMS); ac=m.u32(P.A_ABSTRACT)
    for i in range(ac):
        p=m.u32(ai+4*i)
        if not p or (p&3): continue
        if m.u32(p+0x21C)!=ph: continue
        nm,_=D.rtti_name(m,p)
        if not nm or 'UnitClass' not in nm: continue
        lx=m.u32(p+0x9C); ly=m.u32(p+0xA0)
        print("unit %s cell=(%d,%d)"%(hex(p),lx>>8,ly>>8))
        hits=[]
        for off in range(0,0x700,4):
            v=m.u32(p+off)
            if not v or not (0x400000<=v<=0x900000): continue
            nm2=name_at(m,v+0x24)
            if nm2 and len(nm2)>=2:
                hits.append((hex(off),hex(v),nm2))
        for h in hits[:12]: print("   off=%s -> %s name=%s"%h)
    m.close()

if __name__=='__main__':main()
