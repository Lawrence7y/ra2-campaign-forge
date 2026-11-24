#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time, json, ctypes
import w177_core as W, wb_probe as P
from w177_click import game_hwnd, force_foreground, click_client
from PIL import ImageGrab
import l2_probe_lib as L
L.PID=41892; PID=41892
u32=L.u32
VK_LBUTTON=0x01
print("LBUTTON state", hex(u32.GetAsyncKeyState(VK_LBUTTON)&0xffff), flush=True)
force_foreground(game_hwnd(PID),0.5)
m=W.Mem(PID); ph=P.player_house(m)
pre_addrs={o["addr"] for o in L.napowr(m,ph) if o["o1"]==0 and o["valid"]}
m.close()
ok,cur,s,tr=L.aim((114,62))
print("aim",ok,cur,[round(z,1) for z in s],flush=True)
ImageGrab.grab(all_screens=False).save(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_L2\EVIDENCE\footprint_diag.png")
print("saved footprint_diag.png",flush=True)
force_foreground(game_hwnd(PID),0.3)
okc,info=click_client(PID,int(s[0]),int(s[1]),"left",settle=0.3,verify=True)
print("click_client",okc,info,flush=True)
time.sleep(0.8)
m=W.Mem(PID)
post=[o for o in L.napowr(m,ph) if o["o1"]==0 and o["valid"]]
new=[o for o in post if o["addr"] not in pre_addrs]
print("new",json.dumps(new,ensure_ascii=False),"napowr",json.dumps(L.napowr(m,ph),ensure_ascii=False),"credit",L.rd(m,ph+0x30C),flush=True)
print("LBUTTON state after", hex(u32.GetAsyncKeyState(VK_LBUTTON)&0xffff),flush=True)
ImageGrab.grab(all_screens=False).save(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_L2\EVIDENCE\after_click_diag.png")
m.close()
