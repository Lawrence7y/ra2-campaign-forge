#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rapid menu navigation: launch -> main menu -> single player -> skirmish -> start.
Keeps Popen handle so we can detect exit code. Screenshots after each step."""
import os, sys, time, ctypes, subprocess
from ctypes import wintypes as wt
from PIL import ImageGrab
import w177_core as W
from w177_click import click_client, game_hwnd, force_foreground

GAME = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CWD  = r"D:\Project\ra2-campaign-forge\ra2youli"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "EVIDENCE")

def shot(tag, bbox=(0,0,900,700)):
    img = ImageGrab.grab(bbox=bbox, all_screens=False)
    p = os.path.join(EVID, tag+".png"); img.save(p); return p

def state(tag):
    pid = W.pid_of()
    line = "%s pid=%s"%(tag,pid)
    if pid:
        m=W.Mem(pid)
        line += " mode=%s frame=%s obj=%s"%(m.u32(W.A_MODE),m.u32(W.A_FRAME),m.u32(W.A_ABSTRACT))
        m.close()
    print(line, flush=True)
    return pid

def main():
    residual = subprocess.run(["powershell","-NoProfile","-Command",
        "@(Get-Process gamemd -ErrorAction SilentlyContinue).Count"],capture_output=True,text=True).stdout.strip()
    if residual != "0":
        print("ABORT residual", residual); return 2
    p = subprocess.Popen([GAME], cwd=CWD, close_fds=True)
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"game.pid"),"w").write(str(p.pid))
    print("launched pid",p.pid,flush=True)
    # wait for main menu
    for i in range(10):
        time.sleep(0.8)
        if state("boot"+str(i)): break
    time.sleep(1.0)
    shot("nav_main")
    # click single player
    ok,info=click_client(p.pid,720,219,'left',settle=0.4)
    print("singleplayer click",ok,info,flush=True)
    time.sleep(1.2); state("after_sp"); shot("nav_sp")
    # click skirmish
    ok,info=click_client(p.pid,720,304,'left',settle=0.4)
    print("skirmish click",ok,info,flush=True)
    time.sleep(1.5); state("after_sk"); shot("nav_sk")
    # screenshot full for setup screen
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"nav_sk_full.png"))
    print("p.poll",p.poll(),flush=True)
    return 0

if __name__=='__main__': sys.exit(main())
