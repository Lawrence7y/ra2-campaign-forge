#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hover-color probe: move cursor to given client pixels (ghost assumed in hand),
capture screenshot, count red/green footprint pixels near cursor. Read-only screen + synthetic move."""
import sys, os, time, ctypes
from PIL import ImageGrab
import w177_core as W
from w177_click import game_hwnd, force_foreground

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
u32 = ctypes.windll.user32; u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]

def colors(img, sx, sy, rad=140):
    px = img.convert("RGB").load()
    red=green=0
    for y in range(max(0,sy-rad), min(1440,sy+rad)):
        for x in range(max(0,sx-rad), min(2560,sx+rad)):
            R,G,B = px[x,y]
            if R>150 and G<90 and B<90: red+=1
            if G>140 and R<120 and B<120: green+=1
    return red,green

def main():
    pts = []
    for a in sys.argv[1:]:
        x,y = a.split(","); pts.append((int(x),int(y)))
    pid = W.pid_of(); h = game_hwnd(pid); force_foreground(h, 0.3)
    out=[]
    for i,(x,y) in enumerate(pts):
        u32.SetCursorPos(x,y); time.sleep(0.5)
        img = ImageGrab.grab(all_screens=False)
        r,g = colors(img,x,y)
        tag = "hover_%d_%d_%d" % (x,y,i)
        img.crop((max(0,x-260),max(0,y-220),min(2560,x+260),min(1440,y+220))).save(os.path.join(EVID,tag+".png"))
        out.append({"screen":[x,y],"red":r,"green":g})
        print("%d (%d,%d) red=%d green=%d" % (i,x,y,r,g))
    import json
    with open(os.path.join(EVID,"hover_probe.json"),"a",encoding="utf-8") as f:
        f.write(json.dumps({"ts":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"points":out},ensure_ascii=False)+"\n")
    return 0

if __name__=="__main__": sys.exit(main())
