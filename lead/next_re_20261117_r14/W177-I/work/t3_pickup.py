#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3-step1：拾取 NAPOWR ghost（第2次点图标，前台校验），截图确认 ghost 举起。
不写内存/不注入；只读 RPM + 合成点击。"""
import os, json, time
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D
from w177_click import click_client, game_hwnd, force_foreground

CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-I"
EVID = os.path.join(CARD, "EVIDENCE")
GRID = json.load(open(os.path.join(EVID, "sidebar_grid.json"), encoding="utf-8"))
ICON = tuple(GRID["chosen"]["center"])

def main():
    pid = W.pid_of()
    if not pid: print("no gamemd"); return 2
    m = W.Mem(pid); ph = P.player_house(m)
    rec = {"icon": ICON, "before": {"frame": m.u32(W.A_FRAME),
           "credits": m.u32(ph+0x30C), "nap": C.napowr_objects(m,ph)}}
    # 前台校验（不按 Esc：Esc 会弹出暂停菜单，ghost 的地图点击不可能成为移动命令，无需清选中）
    hwnd = game_hwnd(pid)
    fg = force_foreground(hwnd, 0.5) if hwnd else False
    rec["foreground_ready"] = fg
    print("fg", fg, flush=True)
    if not fg: m.close(); return 3
    # 第2次点图标 = 拾取 ghost
    ok, info = click_client(pid, ICON[0], ICON[1], "left", settle=0.3, verify=True)
    rec["click"] = {"ok": ok, "info": info}
    print("pickup click ok", ok, info, flush=True)
    time.sleep(0.4)
    shot = os.path.join(EVID, "t3_ghost_picked.png")
    ImageGrab.grab(all_screens=False).save(shot)
    rec["after"] = {"frame": m.u32(W.A_FRAME), "credits": m.u32(ph+0x30C),
                    "nap": C.napowr_objects(m,ph)}
    rec["shot"] = shot
    m.close()
    json.dump(rec, open(os.path.join(EVID,"t3_pickup.json"),"w",encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("saved; credits", rec["before"]["credits"], "->", rec["after"]["credits"], flush=True)
    return 0 if ok else 3

if __name__ == "__main__":
    main()
