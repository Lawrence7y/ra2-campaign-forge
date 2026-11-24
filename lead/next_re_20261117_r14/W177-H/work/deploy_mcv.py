#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Select all units via box drag, press D (deploy) to deploy MCV if present,
then check whether a NACNST building appeared for player house."""
import os,sys,time,ctypes
from PIL import ImageGrab
import w177_core as W, wb_probe as P, dsnap as D
from w177_click import game_hwnd,force_foreground

EVID=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-H\EVIDENCE"
u32=ctypes.windll.user32; u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.mouse_event.argtypes=[ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_size_t]
u32.keybd_event.argtypes=[ctypes.c_ubyte,ctypes.c_ubyte,ctypes.c_uint,ctypes.c_size_t]

def drag(x1,y1,x2,y2):
    u32.SetCursorPos(x1,y1); time.sleep(0.2)
    u32.mouse_event(2,0,0,0,0); time.sleep(0.2)
    # move in steps
    steps=12
    for i in range(1,steps+1):
        x=x1+(x2-x1)*i//steps; y=y1+(y2-y1)*i//steps
        u32.SetCursorPos(x,y); time.sleep(0.04)
    time.sleep(0.2); u32.mouse_event(4,0,0,0,0); time.sleep(0.4)

def snapshot(tag):
    m=W.Mem(W.pid_of()); ph=P.player_house(m)
    blds=[]
    for i,obj in P.enumerate_buildings(m)[2]:
        b=P.one_building(m,i,obj)
        if b['owner_21C']==ph:
            blds.append((b['type'],hex(obj),(b['cell']['cellX'],b['cell']['cellY'])))
    print(tag,"player blds",blds,"credits",m.u32(ph+0x30C),flush=True)
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,tag+".png"))
    m.close(); return blds

def main():
    pid=W.pid_of(); force_foreground(game_hwnd(pid),0.5)
    snapshot("deploy_before")
    # box select whole visible unit area (safe, within map)
    drag(700,350,1900,1000)
    snapshot("deploy_selected")
    # press D
    u32.keybd_event(0x44,0,0,0); time.sleep(0.1); u32.keybd_event(0x44,0,2,0)
    time.sleep(2.0)
    b=snapshot("deploy_after")
    if any('NACNST' in x[0] for x in b): print("MCV DEPLOYED OK",flush=True)
    else: print("NO NACNST - no MCV selected or deploy failed",flush=True)

if __name__=='__main__':sys.exit(main())
