#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launch detached, wait for main menu, click Single Player, wait for full render, screenshot.
Stops there so we can inspect before next click."""
import os, sys, time, ctypes, subprocess
from PIL import ImageGrab
import w177_core as W

GAME=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CWD=r"D:\Project\ra2-campaign-forge\ra2youli"
HERE=os.path.dirname(os.path.abspath(__file__)); EVID=os.path.join(os.path.dirname(HERE),"EVIDENCE")
u32=ctypes.windll.user32; u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.mouse_event.argtypes=[ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_size_t]

def click(x,y):
    u32.SetCursorPos(x,y); time.sleep(0.25)
    u32.mouse_event(2,0,0,0,0); time.sleep(0.09); u32.mouse_event(4,0,0,0,0)

def shot(tag,bbox=(0,0,830,610)):
    ImageGrab.grab(bbox=bbox,all_screens=False).save(os.path.join(EVID,tag+".png"))

def state(tag):
    pid=W.pid_of()
    if not pid: print(tag,"DEAD"); return None
    m=W.Mem(pid); print(tag,"pid",pid,"mode",m.u32(W.A_MODE),"frame",m.u32(W.A_FRAME)); m.close(); return pid

def main():
    det=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP
    p=subprocess.Popen([GAME],cwd=CWD,close_fds=True,creationflags=det)
    open(os.path.join(HERE,"game.pid"),"w").write(str(p.pid))
    print("launched",p.pid,flush=True)
    time.sleep(8)
    state("main"); shot("step_main")
    click(720,219)   # single player
    print("clicked single player",flush=True)
    time.sleep(4)
    state("sp"); shot("step_sp")
    return 0

if __name__=='__main__':sys.exit(main())
