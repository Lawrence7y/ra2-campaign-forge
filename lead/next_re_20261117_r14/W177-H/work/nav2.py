#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Menu navigation v2: raw SetCursorPos + mouse_event, NO force_foreground between clicks.
Launch detached, screenshots after each step, all in one process."""
import os, sys, time, ctypes, subprocess
from ctypes import wintypes as wt
from PIL import ImageGrab
import w177_core as W

GAME = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CWD  = r"D:\Project\ra2-campaign-forge\ra2youli"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "EVIDENCE")
u32 = ctypes.windll.user32
u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.mouse_event.argtypes=[wt.DWORD,wt.DWORD,wt.DWORD,wt.DWORD,ctypes.c_size_t]

def shot(tag, bbox=(0,0,830,610)):
    img = ImageGrab.grab(bbox=bbox, all_screens=False)
    p=os.path.join(EVID,tag+".png"); img.save(p); return p

def click(x,y,dwell=0.3):
    u32.SetCursorPos(int(x),int(y)); time.sleep(0.2)
    u32.mouse_event(0x0002,0,0,0,0); time.sleep(0.08); u32.mouse_event(0x0004,0,0,0,0)
    time.sleep(dwell)

def state(tag):
    pid=W.pid_of()
    if not pid: print(tag,"DEAD",flush=True); return None
    m=W.Mem(pid); r=(m.u32(W.A_MODE),m.u32(W.A_FRAME),m.u32(W.A_ABSTRACT)); m.close()
    print(tag,"pid",pid,"mode/frame/obj",r,flush=True); return pid

def main():
    det = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    p = subprocess.Popen([GAME],cwd=CWD,close_fds=True,creationflags=det)
    open(os.path.join(HERE,"game.pid"),"w").write(str(p.pid))
    print("launched",p.pid,flush=True)
    time.sleep(7); state("t7"); shot("nv2_main")
    # main menu -> single player
    click(720,219,0.4); time.sleep(1.5); state("t_sp"); shot("nv2_sp")
    # single player submenu -> skirmish (遭遇戰 y~304 from earlier full-text screenshot)
    click(720,304,0.4); time.sleep(2.0); state("t_sk"); shot("nv2_sk"); shot("nv2_sk_full",(0,0,2560,1440))
    print("poll",p.poll(),flush=True)
    return 0

if __name__=='__main__': sys.exit(main())
