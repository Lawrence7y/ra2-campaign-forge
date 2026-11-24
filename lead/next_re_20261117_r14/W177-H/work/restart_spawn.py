#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Restart skirmish quickly; report whether player house has an MCV / construction yard.
Kills ONLY the game we launched (pid from game.pid)."""
import os,sys,time,ctypes,subprocess
import w177_core as W, wb_probe as P, dsnap as D
from w177_click import game_hwnd,force_foreground

GAME=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"; CWD=r"D:\Project\ra2-campaign-forge\ra2youli"
HERE=os.path.dirname(os.path.abspath(__file__)); PIDF=os.path.join(HERE,"game.pid")
u32=ctypes.windll.user32; u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.mouse_event.argtypes=[ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_size_t]

def click(x,y):
    u32.SetCursorPos(x,y); time.sleep(0.25); u32.mouse_event(2,0,0,0,0); time.sleep(0.09); u32.mouse_event(4,0,0,0,0)

def report(tag):
    m=W.Mem(W.pid_of()); ph=P.player_house(m)
    ac=m.u32(P.A_ABSTRACT); ai=m.u32(P.A_ABSTRACT_ITEMS)
    units=[]; blds=[]; inf=[]
    for i in range(ac):
        p=m.u32(ai+4*i)
        if not p or (p&3): continue
        if m.u32(p+0x21C)!=ph: continue
        nm,_=D.rtti_name(m,p)
        if not nm: continue
        lx=m.u32(p+0x9C); ly=m.u32(p+0xA0); cell=(lx>>8,ly>>8) if lx is not None else None
        if 'UnitClass' in nm: units.append((hex(p),cell))
        elif 'InfantryClass' in nm: inf.append(cell)
        elif 'BuildingClass' in nm: blds.append((hex(p),cell))
    print('%s ph=%s units=%s blds=%s infantry_cells=%s'%(tag,hex(ph),units,blds,sorted(set(inf))),flush=True)
    m.close(); return units,blds,inf

def main():
    old=open(PIDF).read().strip() if os.path.exists(PIDF) else None
    if old:
        subprocess.run(['powershell','-NoProfile','-Command','Stop-Process -Id %s -Force -ErrorAction SilentlyContinue'%old])
        time.sleep(1)
    det=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP
    p=subprocess.Popen([GAME],cwd=CWD,close_fds=True,creationflags=det)
    open(PIDF,'w').write(str(p.pid)); print('launched',p.pid,flush=True)
    time.sleep(8)
    h=game_hwnd(p.pid); force_foreground(h,0.5)
    click(720,219); time.sleep(2.5)    # single player
    click(720,303); time.sleep(2.5)    # skirmish
    click(730,263); print('clicked start',flush=True)  # start game
    # wait for frame to advance
    for i in range(15):
        time.sleep(1.2)
        pid=W.pid_of()
        if not pid: print('DEAD'); return 2
        m=W.Mem(pid); fr=m.u32(W.A_FRAME); obj=m.u32(W.A_ABSTRACT); m.close()
        if fr>5: print('ingame frame',fr,'obj',obj,flush=True); break
    time.sleep(2)
    units,blds,inf=report('SPAWN')
    # has MCV? heuristic: player buildings include NACNST (deployed) or a unit whose cell we can inspect further
    return 0

if __name__=='__main__':sys.exit(main())
