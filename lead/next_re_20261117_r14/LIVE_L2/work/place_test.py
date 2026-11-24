#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decisive test: with ghost in hand, click empty cell; read memory chain after."""
import time, json
import w177_core as W, wb_probe as P
import l2_probe_lib as L
L.PID = 41892
PID = 41892
m=W.Mem(PID); ph=P.player_house(m)
pre = [o for o in L.napowr(m,ph) if o["o1"]==0 and o["valid"]]
pre_addrs = {o["addr"] for o in pre}
target=(113,62)
cb=L.chain_at(m,*target)
print("BEFORE credit",L.rd(m,ph+0x30C),"chain",json.dumps(cb,ensure_ascii=False),"napowr",L.napowr(m,ph),flush=True)
m.close()
ok,cur,s,trace=L.aim((target[0]+1,target[1]))
m=W.Mem(PID); print("aim",ok,cur,[round(z,1) for z in s],"hover",L.hcell(m),"cols",L.cols(s[0],s[1]),flush=True)
fb,fa=L.click_here(dwell=0.8)
time.sleep(0.5)
post=[o for o in L.napowr(m,ph) if o["o1"]==0 and o["valid"]]
new=[o for o in post if o["addr"] not in pre_addrs]
ca=L.chain_at(m,*target)
print("AFTER credit",L.rd(m,ph+0x30C),"frame",fb,fa,"new",json.dumps(new,ensure_ascii=False),flush=True)
print("AFTER chain",json.dumps(ca,ensure_ascii=False),flush=True)
m.close()
