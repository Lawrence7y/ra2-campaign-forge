#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIVE-L1 ghost_state: robustly determine/force ghost-in-hand by probing footprint colors.
No right-click ever. Uses icon click to order/pickup. Read-only RPM + synthesized input."""
import os, sys, time, ctypes, json, struct
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D
from w177_click import click_client, game_hwnd, force_foreground

CARD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_L1"
EVID=os.path.join(CARD,"EVIDENCE"); HOVER=0x88095C
u32=ctypes.windll.user32; k32=ctypes.windll.kernel32
try: u32.SetProcessDPIAware()
except Exception: pass
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
b4=ctypes.create_string_buffer(4); got=ctypes.c_size_t(0)
def rd(m,va):
    if k32.ReadProcessMemory(m.h,ctypes.c_void_p(va),b4,4,ctypes.byref(got)) and got.value==4:
        return struct.unpack('<I',b4.raw)[0]
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

def wait_credits_stable(m,ph,rounds=6,dt=0.5,tol=3):
    seq=[]
    for i in range(rounds):
        time.sleep(dt); seq.append(rd(m,ph+0x30C))
    return seq, (max(seq)-min(seq)<=tol)

def main():
    pid=W.pid_of()
    if not pid: print("no gamemd"); return 2
    force_foreground(game_hwnd(pid),0.6)
    m=W.Mem(pid); ph=P.player_house(m)
    cr0=rd(m,ph+0x30C)
    seq,stable=wait_credits_stable(m,ph)
    print("credits start",cr0,"seq",seq,"stable",stable)
    m.close()
    # If a build is in progress (not stable), wait more
    if not stable:
        for i in range(60):
            time.sleep(0.5)
            m=W.Mem(pid); s,_=wait_credits_stable(m,ph,rounds=3,dt=0.4); m.close()
            if max(s)-min(s)<=3:
                print("build settled at",s[-1]); break
    # Now click icon once: either picks up ready building OR orders a new one
    icon=(2336,472)
    force_foreground(game_hwnd(pid),0.5)
    ok,info=click_client(pid,icon[0],icon[1],"left",settle=0.4,verify=True)
    print("icon click",ok,info)
    time.sleep(0.5)
    m=W.Mem(pid); ph=P.player_house(m); cr1=rd(m,ph+0x30C); m.close()
    print("credits after icon click",cr1)
    # If credits started dropping (ordered new), wait for build complete
    if cr1 < cr0-5 or not stable:
        for i in range(90):
            time.sleep(0.4)
            m=W.Mem(pid); s,st=wait_credits_stable(m,ph,rounds=3,dt=0.3,tol=3); m.close()
            if st:
                print("ordered build settled at",s[-1]); break
        # click icon again to pickup
        force_foreground(game_hwnd(pid),0.5)
        ok2,info2=click_client(pid,icon[0],icon[1],"left",settle=0.4,verify=True)
        print("pickup click",ok2,info2)
        time.sleep(0.5)
    # probe footprint at several known reachable screen positions
    for sx,sy in [(1180,395),(1176,590),(1040,499),(1405,695),(1350,520),(1605,520)]:
        u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.35)
        m=W.Mem(pid); hc=hcell(m); m.close()
        c=cols(sx,sy)
        print("probe",(sx,sy),"cell",hc,"G",c["green"],"R",c["red"])
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"ghost_state_probe.png"))
    return 0

if __name__=="__main__": sys.exit(main())
