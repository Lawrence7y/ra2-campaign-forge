#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T2 三层判据下单（只读内存 + 合成点击，前台校验）。
L1 credits 降低；L2 owner=player 且 type=NAPOWR 的 limbo Building 出现；L3 tile 像素变化。
三步缺一不可；L3 不成立就停、不去点地图。
所有点击走 w177_click.click_client（GetForegroundWindow==hwnd + WindowFromPoint owner==pid）。
"""
import os, sys, time, json, ctypes
from PIL import Image, ImageChops, ImageGrab
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D
from w177_click import click_client, game_hwnd, force_foreground

CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-I"
EVID = os.path.join(CARD, "EVIDENCE")
GRID = json.load(open(os.path.join(EVID, "sidebar_grid.json"), encoding="utf-8"))
ICON = tuple(GRID["chosen"]["center"])   # (2336,472) 像素定位结果
BBOX = tuple(GRID["chosen"]["bbox"])     # tile bbox 用于 L3 像素差

u32 = ctypes.windll.user32
try: u32.SetProcessDPIAware()
except Exception: pass


def snap_state(m, ph):
    """当前 credits / player NAPOWR limbo 对象 / frame / 全部 player 建筑类型。"""
    types = C.all_player_building_types(m, ph)
    nap = C.napowr_objects(m, ph)   # 只列 type=NAPOWR；is_player 标记
    player_nap = [n for n in nap if n.get("is_player")]
    return {
        "frame": m.u32(W.A_FRAME),
        "credits": m.u32(ph + 0x30C),
        "player_building_types": types,
        "player_napowr_count": len(player_nap),
        "player_napowr": player_nap,
        "building_array_count": W.building_array(m)[1],
        "cam": [m.u32(0x886FA0), m.u32(0x886FA4)],
    }


def tile_diff(path_a, path_b, bbox):
    a = Image.open(path_a).convert("RGB").crop(bbox)
    b = Image.open(path_b).convert("RGB").crop(bbox)
    diff = ImageChops.difference(a, b)
    # 统计差异像素（任一通道差>18）
    px = diff.load(); w, h = diff.size
    changed = 0; total = 0; maxd = 0
    for y in range(h):
        for x in range(w):
            r, g, bl = px[x, y]
            md = max(r, g, bl); maxd = max(maxd, md)
            if md > 18: changed += 1
            total += 1
    return {"changed_px": changed, "total_px": total,
            "changed_frac": round(changed/total, 4) if total else 0, "max_diff": maxd}


def main():
    pid = W.pid_of()
    if not pid:
        print("no gamemd"); return 2
    m = W.Mem(pid); ph = P.player_house(m)
    rec = {"pid": pid, "icon": ICON, "bbox": BBOX, "grid_src": GRID["src"]}

    # --- 前台校验 + Esc 清空选中（避免地图点击歧义；对侧栏点击无碍但更干净）---
    hwnd = game_hwnd(pid)
    fg = force_foreground(hwnd, 0.5) if hwnd else False
    rec["foreground_ready"] = fg
    print("foreground_ready", fg, flush=True)
    if not fg:
        print("ABORT foreground failed"); m.close(); return 3

    # --- BEFORE 快照 + tile 截图 ---
    pre = snap_state(m, ph)
    rec["before"] = pre
    shot_before = os.path.join(EVID, "t2_tile_before.png")
    ImageGrab.grab(all_screens=False).save(shot_before)
    print("BEFORE credits", pre["credits"], "player_nap", pre["player_napowr_count"], flush=True)

    # --- 点击图标（唯一一次，点中心，前台已校验）---
    ok, info = click_client(pid, ICON[0], ICON[1], "left", settle=0.35, verify=True)
    rec["click"] = {"ok": ok, "info": info}
    print("click ok", ok, info, flush=True)
    if not ok:
        m.close(); return 3

    # --- 轮询 L1/L2（≤3s，每 100ms）---
    poll = []
    t0 = time.perf_counter()
    l1 = l2 = False
    first_credits_drop = None
    first_player_nap = None
    while time.perf_counter() - t0 < 3.0:
        s = snap_state(m, ph)
        poll.append({"t": round(time.perf_counter()-t0, 3), "frame": s["frame"],
                     "credits": s["credits"], "player_napowr_count": s["player_napowr_count"],
                     "player_building_types": s["player_building_types"]})
        if s["credits"] < pre["credits"]:
            l1 = True
            if first_credits_drop is None:
                first_credits_drop = {"t": round(time.perf_counter()-t0,3), "credits": s["credits"]}
        if s["player_napowr_count"] > pre["player_napowr_count"]:
            l2 = True
            if first_player_nap is None:
                first_player_nap = {"t": round(time.perf_counter()-t0,3), "count": s["player_napowr_count"]}
        time.sleep(0.1)
    rec["poll"] = poll
    rec["L1"] = {"pass": l1, "before": pre["credits"], "first_drop": first_credits_drop,
                 "after": snap_state(m, ph)["credits"]}
    rec["L2"] = {"pass": l2, "before": pre["player_napowr_count"],
                 "first_appear": first_player_nap, "after": snap_state(m, ph)["player_napowr_count"]}

    # --- AFTER 快照 + tile 截图 + L3 像素差 ---
    after = snap_state(m, ph)
    rec["after"] = after
    shot_after = os.path.join(EVID, "t2_tile_after.png")
    ImageGrab.grab(all_screens=False).save(shot_after)
    rec["L3"] = {"pass": None, "diff": tile_diff(shot_before, shot_after, BBOX)}
    rec["L3"]["pass"] = rec["L3"]["diff"]["changed_frac"] > 0.02

    rec["ALL_THREE"] = bool(l1 and l2 and rec["L3"]["pass"])
    # 若 L2 出现，补一个清晰的 limbo 对象详情
    if l2:
        napnow = C.napowr_objects(m, ph)
        rec["player_napowr_detail"] = [n for n in napnow if n.get("is_player")]

    m.close()
    p = os.path.join(EVID, "t2_order.json")
    json.dump(rec, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("L1", rec["L1"], flush=True)
    print("L2", rec["L2"], flush=True)
    print("L3", rec["L3"], flush=True)
    print("ALL_THREE", rec["ALL_THREE"], "saved", p, flush=True)
    return 0 if rec["ALL_THREE"] else 4

if __name__ == "__main__":
    sys.exit(main())
