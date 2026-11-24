#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check current infantry cell chain states + credit/ghost."""
import w177_core as W, wb_probe as P, wc_probe as C
import l2_probe_lib as L
from collections import Counter
L.PID=41892; PID=41892
m=W.Mem(PID); ph=P.player_house(m)
ai=m.u32(P.A_ABSTRACT_ITEMS); ac=m.u32(P.A_ABSTRACT); inf=Counter()
for i in range(ac):
    q=m.u32(ai+4*i)
    if not q or (q&3) or m.u32(q+0x21C)!=ph: continue
    nm,_=L.D.rtti_name(m,q)
    if not nm or 'InfantryClass' not in nm: continue
    lx=m.u32(q+0x9C); ly=m.u32(q+0xA0)
    if lx and ly: inf[(lx>>8,ly>>8)]+=1
for cell in sorted(inf)[:12]:
    ch=L.chain_at(m,*cell); print(cell,"n_inf",inf[cell],"chain",ch.get("rttiA"),flush=True)
print("credit",L.rd(m,ph+0x30C),"ghost",len([o for o in L.napowr(m,ph) if o["o1"]==1]),flush=True)
m.close()
