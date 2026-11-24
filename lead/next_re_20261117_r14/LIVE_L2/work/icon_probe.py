#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Interactive step probe: click NAPOWR icon, log memory state after each step."""
import os, sys, time, json, ctypes, struct
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D
from w177_click import click_client, game_hwnd, force_foreground

PID = 41892
ICON = (2336, 472)
u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
HOVER = 0x88095C
b4 = ctypes.create_string_buffer(4); got = ctypes.c_size_t(0)
def rd(m, va):
    if k32.ReadProcessMemory(m.h, ctypes.c_void_p(va), b4, 4, ctypes.byref(got)) and got.value == 4:
        return struct.unpack('<I', b4.raw)[0]
    return None
def hcell(m):
    v = rd(m, HOVER); return (v & 0xFFFF, (v >> 16) & 0xFFFF) if v else (None, None)

def state(tag):
    m = W.Mem(PID); ph = P.player_house(m)
    nap = []
    for i, obj in P.enumerate_buildings(m)[2]:
        b = P.one_building(m, i, obj)
        if b["owner_21C"] == ph and b["type"] in ("NAPOWR",) or (b["type"] != "NACNST" and b["owner_21C"] == ph):
            c = b["cell"]
            nap.append({"type": b["type"], "o1": b["o1_81"], "o2": b["o2_74"],
                        "cell": [c["cellX"], c["cellY"]], "valid": c["valid"]})
    out = {"tag": tag, "credit": rd(m, ph + 0x30C), "frame": m.u32(W.A_FRAME),
           "build_types": C.all_player_building_types(m, ph), "nobld": nap,
           "hover": hcell(m)}
    m.close(); print(json.dumps(out, ensure_ascii=False), flush=True); return out

state("initial")
# verify window geometry / click target
force_foreground(game_hwnd(PID), 0.4)
ok, info = click_client(PID, ICON[0], ICON[1], "left", settle=0.3, verify=True)
print("CLICK1", ok, info, flush=True)
state("after_click1_0s")
time.sleep(1.5); state("after_click1_1.5s")
time.sleep(4.0); state("after_click1_5.5s")
# second click (pickup?)
force_foreground(game_hwnd(PID), 0.3)
ok, info = click_client(PID, ICON[0], ICON[1], "left", settle=0.3, verify=True)
print("CLICK2", ok, info, flush=True)
state("after_click2_0s")
time.sleep(1.0); state("after_click2_1s")
