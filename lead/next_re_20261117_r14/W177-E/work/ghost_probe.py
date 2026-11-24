#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拿起 ghost（裸 mouse_event，不夺焦）-> 移到目标 -> 校验光标位置 -> 截图 -> 读足迹颜色。全在一进程。"""
import sys, os, time, ctypes, json
from ctypes import wintypes as wt
from PIL import ImageGrab
import w177_core as W
import wb_probe as P

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
u32 = ctypes.windll.user32
u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.GetCursorPos.argtypes = [ctypes.POINTER(wt.POINT)]
u32.mouse_event.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD, wt.DWORD, ctypes.c_size_t]
LEFTDOWN, LEFTUP = 0x0002, 0x0004

def cursor():
    pt = wt.POINT(); u32.GetCursorPos(ctypes.byref(pt)); return (pt.x, pt.y)

def click_bare(x, y):
    u32.SetCursorPos(x, y); time.sleep(0.15)
    u32.mouse_event(LEFTDOWN, 0, 0, 0, 0); time.sleep(0.08)
    u32.mouse_event(LEFTUP, 0, 0, 0, 0); time.sleep(0.15)

def footprint_colors(img, sx, sy, rad=90):
    im = img.convert('RGB'); px = im.load(); w,h = im.size
    red=green=yellow=0
    for y in range(max(0,sy-rad),min(h,sy+rad)):
        for x in range(max(0,sx-rad),min(w,sx+rad)):
            R,G,B = px[x,y]
            if R>150 and G<90 and B<90: red+=1
            if G>140 and R<120 and B<120: green+=1
            if R>180 and G>180 and B<80: yellow+=1
    return red,green,yellow

def main():
    tx = int(sys.argv[1]); ty = int(sys.argv[2])
    do_pickup = "--pickup" in sys.argv
    tag = sys.argv[3] if len(sys.argv)>3 and not sys.argv[3].startswith("--") else "ghost_probe"
    pid = W.pid_of(); m = W.Mem(pid); ph = P.player_house(m)
    print("pid=%d start cursor=%s frame=%d credit=%d" % (pid, cursor(), m.u32(W.A_FRAME), m.u32(ph+0x30C)))
    if do_pickup:
        click_bare(2328, 480)
        print("pickup clicked cursor=%s frame=%d" % (cursor(), m.u32(W.A_FRAME)))
        time.sleep(0.4)
    u32.SetCursorPos(tx, ty); time.sleep(0.5)
    print("moved cursor=%s (target %d,%d)" % (cursor(), tx, ty))
    img = ImageGrab.grab(all_screens=False)
    img.save(os.path.join(EVID, tag + ".png"))
    r,g,y = footprint_colors(img, tx, ty)
    print("footprint colors at target red=%d green=%d yellow=%d" % (r,g,y))
    # crop for visual
    img.crop((max(0,tx-250),max(0,ty-200),min(2560,tx+250),min(1440,ty+200))).save(os.path.join(EVID, tag+"_crop.png"))
    return 0

if __name__ == "__main__":
    sys.exit(main())
