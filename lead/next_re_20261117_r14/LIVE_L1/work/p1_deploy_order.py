#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIVE-L1 phase1: hold foreground; deploy MCV -> order NAPOWR -> wait build -> pickup ghost.
Read-only RPM + synthesized input. Game already running; no launch here."""
import os, sys, time, ctypes, json, struct, subprocess
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D
from w177_click import click_client, game_hwnd, force_foreground

CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_L1"
EVID = os.path.join(CARD, "EVIDENCE")
WDIR = os.path.join(CARD, "work")
HOVER = 0x88095C
u32 = ctypes.windll.user32; k32 = ctypes.windll.kernel32
try:
    u32.SetProcessDPIAware()
except Exception:
    pass
class PNT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
u32.GetCursorPos.argtypes = [ctypes.POINTER(PNT)]
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.mouse_event.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_size_t]
b4 = ctypes.create_string_buffer(4); got = ctypes.c_size_t(0)

def rd(m, va):
    if k32.ReadProcessMemory(m.h, ctypes.c_void_p(va), b4, 4, ctypes.byref(got)) and got.value == 4:
        return struct.unpack('<I', b4.raw)[0]
    return None

def hcell(m):
    v = rd(m, HOVER)
    return (v & 0xFFFF, (v >> 16) & 0xFFFF) if v else (None, None)

def shot(tag):
    p = os.path.join(EVID, tag + ".png")
    im = ImageGrab.grab(all_screens=False)
    im.save(p)
    return p

def click_synth(x, y, dwell=0.3):
    u32.SetCursorPos(int(x), int(y)); time.sleep(0.15)
    u32.mouse_event(2, 0, 0, 0, 0); time.sleep(0.08); u32.mouse_event(4, 0, 0, 0, 0); time.sleep(dwell)

def key_tap(vk):
    u32.keybd_event(vk, 0, 0, 0); time.sleep(0.08); u32.keybd_event(vk, 0, 2, 0); time.sleep(0.15)

def player_types(m, ph):
    return C.all_player_building_types(m, ph)

def cell_to_screen(cx, cy):
    # anchor from W177-I: (111,60)->(1400,600); JX=(55.6,25.9) JY=(-55.6,25.9)
    return (1400 + 55.6*(cx-111) - 55.6*(cy-60), 600 + 25.9*(cx-111) + 25.9*(cy-60))

def main():
    log = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    pid = W.pid_of()
    if not pid:
        print("no gamemd"); return 2
    log["pid"] = pid
    hwnd = game_hwnd(pid)
    ff = force_foreground(hwnd, 0.8)
    log["initial_foreground"] = ff
    print("pid", pid, "hwnd", hex(hwnd), "foreground", ff, "curfg", hex(u32.GetForegroundWindow()), flush=True)
    if not ff:
        print("ABORT foreground failed"); return 3
    # snapshot before
    m = W.Mem(pid); ph = P.player_house(m)
    log["before"] = {"frame": m.u32(W.A_FRAME), "mode": m.u32(W.A_MODE),
                     "credits": rd(m, ph+0x30C), "player_types": player_types(m, ph)}
    m.close()
    print("before", log["before"], flush=True)
    if "NACNST" not in log["before"]["player_types"]:
        # find MCV cell via memory
        m = W.Mem(pid)
        aitems = m.u32(P.A_ABSTRACT_ITEMS); acount = m.u32(P.A_ABSTRACT)
        mcv = None
        for i in range(acount):
            q = m.u32(aitems + 4*i)
            if not q or (q & 3): continue
            if m.u32(q+0x21C) != ph: continue
            nm, _ = D.rtti_name(m, q)
            if nm and 'UnitClass' in nm:
                lx = m.u32(q+0x9C); ly = m.u32(q+0xA0)
                if lx and ly:
                    mcv = (lx >> 8, ly >> 8)
                    break
        m.close()
        log["mcv_cell"] = mcv
        if mcv:
            sx, sy = cell_to_screen(*mcv)
        else:
            sx, sy = 1350, 485
        # click MCV then press D to deploy (keystrokes land on foreground game)
        click_synth(sx, sy, 0.4)
        key_tap(0x44)  # 'D'
        time.sleep(2.5)
        m = W.Mem(pid); ph = P.player_house(m)
        log["after_deploy"] = {"frame": m.u32(W.A_FRAME), "credits": rd(m, ph+0x30C),
                               "player_types": player_types(m, ph)}
        m.close()
        print("after deploy", log["after_deploy"], flush=True)
        shot("p1_after_deploy")
        if "NACNST" not in log["after_deploy"]["player_types"]:
            log["abort"] = "no construction yard after deploy"
            json.dump(log, open(os.path.join(EVID, "p1_result.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            return 4
    # locate NAPOWR icon via pixel analysis on a fresh in-game shot
    shot("p1_before_icon")
    subprocess.run([sys.executable, os.path.join(WDIR, "sidebar_locate.py"),
                    os.path.join(EVID, "p1_before_icon.png")], cwd=WDIR, capture_output=True, text=True)
    grid = json.load(open(os.path.join(EVID, "sidebar_grid.json"), encoding="utf-8"))
    icon = tuple(grid["chosen"]["center"])
    log["icon"] = icon
    log["icon_bbox"] = grid["chosen"]["bbox"]
    print("icon", icon, "bbox", grid["chosen"]["bbox"], flush=True)
    # ensure foreground then order (click icon once)
    force_foreground(game_hwnd(pid), 0.5)
    m = W.Mem(pid); ph = P.player_house(m)
    pre = rd(m, ph+0x30C); m.close()
    ok, info = click_client(pid, icon[0], icon[1], "left", settle=0.35, verify=True)
    log["order_click"] = {"ok": ok, "info": info, "pre_credits": pre}
    print("order click", ok, info, "pre", pre, flush=True)
    time.sleep(0.6)
    m = W.Mem(pid); ph = P.player_house(m)
    post = rd(m, ph+0x30C); m.close()
    log["order_post_credits"] = post
    print("post credits", post, flush=True)
    # wait build complete (NAPOWR ~600); credits stop dropping near pre-600
    target = pre - 600
    built_credits = None
    for i in range(80):
        time.sleep(0.5)
        m = W.Mem(pid); ph = P.player_house(m); cr = rd(m, ph+0x30C); m.close()
        if cr <= target + 20:
            built_credits = cr
            break
    log["built_credits"] = built_credits
    print("build done credits", built_credits, flush=True)
    time.sleep(1.0)
    # pickup ghost: click icon once
    force_foreground(game_hwnd(pid), 0.5)
    ok2, info2 = click_client(pid, icon[0], icon[1], "left", settle=0.35, verify=True)
    log["pickup_click"] = {"ok": ok2, "info": info2}
    print("pickup", ok2, flush=True)
    time.sleep(0.4)
    shot("p1_ghost")
    m = W.Mem(pid); ph = P.player_house(m)
    log["after_pickup"] = {"frame": m.u32(W.A_FRAME), "credits": rd(m, ph+0x30C),
                           "player_types": player_types(m, ph), "hover": hcell(m),
                           "cam": (rd(m, 0x886FA0), rd(m, 0x886FA4))}
    m.close()
    print("after pickup", log["after_pickup"], flush=True)
    json.dump(log, open(os.path.join(EVID, "p1_result.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("SAVED p1_result.json", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
