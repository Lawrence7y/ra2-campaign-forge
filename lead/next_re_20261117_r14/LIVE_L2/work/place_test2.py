#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate placement with force_foreground before click."""
import time, json
import w177_core as W, wb_probe as P, wc_probe as C
from w177_click import game_hwnd, force_foreground
import l2_probe_lib as L
L.PID=41892; PID=41892

force_foreground(game_hwnd(PID), 0.5)
m=W.Mem(PID); ph=P.player_house(m)
pre=[o for o in L.napowr(m,ph) if o["o1"]==0 and o["valid"]]; pre_addrs={o["addr"] for o in pre}
target=(113,62)
print("BEFORE ghost",[o for o in L.napowr(m,ph) if o["o1"]==1],"fg",L.u32.GetForegroundWindow()==game_hwnd(PID),flush=True)
m.close()
ok,cur,s,tr=L.aim((target[0]+1,target[1]))
force_foreground(game_hwnd(PID), 0.3)  # re-assert foreground before click
m=W.Mem(PID)
print("aim",ok,cur,[round(z,1) for z in s],"hover",L.hcell(m),"cols",L.cols(s[0],s[1]),"fg",L.u32.GetForegroundWindow()==game_hwnd(PID),flush=True)
fb,fa=L.click_here(dwell=0.9)
time.sleep(0.6)
post=[o for o in L.napowr(m,ph) if o["o1"]==0 and o["valid"]]
new=[o for o in post if o["addr"] not in pre_addrs]
ca=L.chain_at(m,*target)
print("AFTER credit",L.rd(m,ph+0x30C),"frame",fb,fa,"new",json.dumps(new,ensure_ascii=False),flush=True)
print("AFTER chain",json.dumps(ca,ensure_ascii=False),flush=True)
print("napowr_all",json.dumps(L.napowr(m,ph),ensure_ascii=False),flush=True)
m.close()
