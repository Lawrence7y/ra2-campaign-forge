#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find a MEMORY signature of 'ready ghost in hand' by comparing object fields."""
import time, json, ctypes, struct
import w177_core as W
import wb_probe as P
import wc_probe as C
from w177_click import click_client, game_hwnd, force_foreground

PID = 41892; ICON = (2336,472); PROBE=(1400,560)
u32=ctypes.windll.user32; k32=ctypes.windll.kernel32
HOVER=0x88095C; b4=ctypes.create_string_buffer(4); got=ctypes.c_size_t(0)
def rd(m,va):
    if k32.ReadProcessMemory(m.h,ctypes.c_void_p(va),b4,4,ctypes.byref(got)) and got.value==4:
        return struct.unpack('<I',b4.raw)[0]
def napobj(m,ph):
    out=[]
    for i,o in P.enumerate_buildings(m)[2]:
        b=P.one_building(m,i,o)
        if b["owner_21C"]==ph and b["type"]=="NAPOWR":
            out.append({"addr":hex(o),"o1_81":b["o1_81"],"o2_74":b["o2_74"],"o3_80":b["o3_80"],
                        "chainbit_8C":m.u8(o+0x8C),"layer_94":m.u32(o+0x94),
                        "canplace_1AC_u8":m.u8(o+0x1AC),"canplace_1AC_u32":m.u32(o+0x1AC),
                        "cell":[b["cell"]["cellX"],b["cell"]["cellY"]],"valid":b["cell"]["valid"]})
    return out
def snap(tag):
    m=W.Mem(PID); ph=P.player_house(m)
    o={"tag":tag,"credit":rd(m,ph+0x30C),"frame":m.u32(W.A_FRAME),"nap":napobj(m,ph)}
    m.close(); print(json.dumps(o,ensure_ascii=False),flush=True); return o

# wait for credit to stabilize (construction complete)
prev=None; stable=0
for i in range(80):
    m=W.Mem(PID); ph=P.player_house(m); cr=rd(m,ph+0x30C); m.close()
    if prev is not None and cr==prev: stable+=1
    else: stable=0
    prev=cr
    if stable>=5: break
    time.sleep(0.5)
print("STABLE credit",prev,"iters",i,flush=True)
snap("before_pickup")
# click icon to pick up ghost
force_foreground(game_hwnd(PID),0.3)
ok,info=click_client(PID,ICON[0],ICON[1],"left",settle=0.3,verify=True)
print("PICKUP click",ok,flush=True)
time.sleep(0.6); snap("after_pickup_0.6s")
# move cursor to a probe cell and see if object fields change with cursor
u32.SetCursorPos(*PROBE); time.sleep(0.4); snap("probe_moved")
u32.SetCursorPos(PROBE[0]+90,PROBE[1]+40); time.sleep(0.4); snap("probe_moved2")
