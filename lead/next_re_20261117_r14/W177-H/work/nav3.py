#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Careful navigation from current menu: Main Menu -> Single Player -> Skirmish -> Start.
Screenshot after each step. Reports spawn if ingame."""
import os,sys,time,ctypes
from PIL import ImageGrab
import w177_core as W, wb_probe as P, dsnap as D
from w177_click import game_hwnd,force_foreground

HERE=os.path.dirname(os.path.abspath(__file__)); EVID=os.path.join(os.path.dirname(HERE),"EVIDENCE")
u32=ctypes.windll.user32; u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.mouse_event.argtypes=[ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_size_t]

def click(x,y):
    u32.SetCursorPos(x,y); time.sleep(0.3); u32.mouse_event(2,0,0,0,0); time.sleep(0.1); u32.mouse_event(4,0,0,0,0)

def shot(tag):
    p=os.path.join(EVID,tag+".png"); ImageGrab.grab(all_screens=False).save(p); print("shot",tag,os.path.getsize(p),flush=True)

def state(tag):
    pid=W.pid_of()
    if not pid: print(tag,"DEAD"); return None
    m=W.Mem(pid); r=(m.u32(W.A_FRAME),m.u32(W.A_MODE),hex(P.player_house(m)),m.u32(W.A_ABSTRACT)); m.close()
    print(tag,"frame/mode/ph/obj",r,flush=True); return r

def main():
    pid=W.pid_of(); h=game_hwnd(pid)
    print("fg",force_foreground(h,0.5),flush=True)
    state("start")
    click(730,555); time.sleep(2.0); shot("nav3_main"); state("main")
    click(720,219); time.sleep(3.0); shot("nav3_sp"); state("sp")
    click(720,303); time.sleep(3.0); shot("nav3_setup"); state("setup")
    click(730,263); print("clicked start",flush=True)
    for i in range(15):
        time.sleep(1.2); pid=W.pid_of()
        if not pid: print("DEAD"); return 2
        m=W.Mem(pid); fr=m.u32(W.A_FRAME); m.close()
        print("wait",i,"frame",fr,flush=True)
        if fr>5: break
    time.sleep(2)
    shot("nav3_ingame"); r=state("ingame")
    if r and r[3]>100:
        m=W.Mem(W.pid_of()); ph=P.player_house(m)
        ac=m.u32(P.A_ABSTRACT); ai=m.u32(P.A_ABSTRACT_ITEMS)
        units=[];blds=[];inf=[]
        for i in range(ac):
            p=m.u32(ai+4*i)
            if not p or (p&3) or m.u32(p+0x21C)!=ph: continue
            nm,_=D.rtti_name(m,p)
            if not nm: continue
            lx=m.u32(p+0x9C); ly=m.u32(p+0xA0); cell=(lx>>8,ly>>8) if lx is not None else None
            if 'UnitClass' in nm: units.append((hex(p),cell))
            elif 'InfantryClass' in nm: inf.append(cell)
            elif 'BuildingClass' in nm: blds.append((hex(p),cell))
        m.close()
        print("SPAWN units",units,"blds",blds,"inf",sorted(set(inf)),flush=True)
    return 0

if __name__=='__main__':sys.exit(main())
