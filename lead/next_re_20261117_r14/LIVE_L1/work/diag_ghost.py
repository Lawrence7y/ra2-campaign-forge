#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIVE-L1 diag_ghost: report current NAPOWR limbo state + credits; optionally click icon once
to (re)pickup, then hover a known-reachable cell and capture footprint colors."""
import os, sys, time, ctypes, json, struct
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D
from w177_click import click_client, game_hwnd, force_foreground

CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_L1"
EVID = os.path.join(CARD, "EVIDENCE")
HOVER=0x88095C
u32=ctypes.windll.user32; k32=ctypes.windll.kernel32
try: u32.SetProcessDPIAware()
except Exception: pass
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
b4=ctypes.create_string_buffer(4); got=ctypes.c_size_t(0)
def rd(m,va):
    if k32.ReadProcessMemory(m.h,ctypes.c_void_p(va),b4,4,ctypes.byref(got)) and got.value==4:
        return struct.unpack('<I',b4.raw)[0]
    return None
def hcell(m):
    v=rd(m,HOVER); return (v&0xFFFF,(v>>16)&0xFFFF) if v else (None,None)
def cols(sx,sy,rad=110):
    im=ImageGrab.grab(bbox=(int(sx-rad),int(sy-rad),int(sx+rad),int(sy+rad)),all_screens=False).convert("RGB")
    px=im.load(); w,h=im.size; g=r=0
    for y in range(h):
        for x in range(w):
            R,G,B=px[x,y]
            if G>180 and R<90 and B<90: g+=1
            elif R>180 and G<90 and B<90: r+=1
    return {"green":g,"red":r,"total":w*h}

def napowr(m,ph):
    out=[]
    for i,obj in P.enumerate_buildings(m)[2]:
        b=P.one_building(m,i,obj)
        if b["owner_21C"]!=ph or b["type"]!="NAPOWR": continue
        c=b["cell"]
        out.append({"obj":hex(obj),"o1":b["o1_81"],"o2":b["o2_74"],"cell":[c["cellX"],c["cellY"]],
                    "valid":c["valid"],"lenA":b["chains"]["lenA"]})
    return out

def main():
    mode=sys.argv[1] if len(sys.argv)>1 else "report"
    pid=W.pid_of()
    if not pid: print("no gamemd"); return 2
    force_foreground(game_hwnd(pid),0.5)
    m=W.Mem(pid); ph=P.player_house(m)
    print("frame",m.u32(W.A_FRAME),"mode",m.u32(W.A_MODE),"credits",rd(m,ph+0x30C),"hover",hcell(m))
    print("napowr",json.dumps(napowr(m,ph),ensure_ascii=False))
    m.close()
    if mode=="pickup":
        icon=(2336,472)
        force_foreground(game_hwnd(pid),0.5)
        ok,info=click_client(pid,icon[0],icon[1],"left",settle=0.4,verify=True)
        print("pickup click",ok,info)
        time.sleep(0.5)
        m=W.Mem(pid); ph=P.player_house(m)
        print("after pickup credits",rd(m,ph+0x30C),"napowr",json.dumps(napowr(m,ph)))
        m.close()
        # hover a known reachable cell (105,59 center ~ screen 1344,~?); use closed-loop-ish
        for sx,sy in [(1350,520),(1400,560),(1160,400)]:
            u32.SetCursorPos(sx,sy); time.sleep(0.35)
            m=W.Mem(pid); hc=hcell(m); m.close()
            c=cols(sx,sy)
            print("hover screen",(sx,sy),"cell",hc,"colors",c)
        ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"diag_pickup.png"))
    return 0

if __name__=="__main__": sys.exit(main())
