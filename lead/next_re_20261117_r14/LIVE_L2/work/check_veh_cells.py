#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check current chain state of the known vehicle cells."""
import json
import w177_core as W, wb_probe as P
import l2_probe_lib as L
L.PID=41892; PID=41892
m=W.Mem(PID); ph=P.player_house(m)
for cell in [(105,55),(105,59),(113,59),(113,63)]:
    ch=L.chain_at(m,*cell)
    print(cell,"lenA",ch.get("lenA"),"rtti",ch.get("rttiA"),"valid",ch.get("valid"),flush=True)
print("credit",L.rd(m,ph+0x30C),"ghost",[o for o in L.napowr(m,ph) if o["o1"]==1],flush=True)
m.close()
