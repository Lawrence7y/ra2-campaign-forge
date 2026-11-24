#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动放置：点建造图标 → 移动鼠标到候选格 → 用像素检测绿色合法 ghost → click_client 点击 →
紧邻采样额度 + before/after 建筑快照 + 多重佐证。全程 click_client（前台+归属校验）。"""
import argparse
import json
import os
import sys
import time

import ctypes
from PIL import ImageGrab

import w177_core as W
import wb_probe as P
from w177_click import click_client, move_client
import shot

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
CREDIT_OFF = 0x30C
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass


def hx(v):
    return hex(v) if isinstance(v, int) and v else (None if not v else v)


def snap(m):
    ph = P.player_house(m)
    aitems, acount, bl = P.enumerate_buildings(m)
    blds = {}
    for i, obj in bl:
        b = P.one_building(m, i, obj)
        blds[obj] = b
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "frame": m.u32(W.A_FRAME),
            "credit": m.u32(ph + CREDIT_OFF) if ph else None,
            "playerHouse": hx(ph), "objects": m.u32(W.A_ABSTRACT),
            "n_buildings": len(bl), "abstractCount": acount,
            "_objs": blds,
            "b": {hex(k): v for k, v in blds.items()}}


def _greenish(r, g, b):
    # placement tile is bright saturated green (~0,230,0); grass is darker (g~140)
    return g > 175 and r < 105 and b < 105


def detect_green(img, xmax=2200):
    """找 placement 绿色菱形：逐行找连续 >=22px 的绿色 run（排除细血条），取这些 run 中点质心。"""
    im = img.convert("RGB"); w, h = im.size
    px = im.load()
    runs = []
    for y in range(0, h, 2):
        x = 0
        while x < min(xmax, w):
            if _greenish(*px[x, y]):
                x0 = x
                while x < min(xmax, w) and _greenish(*px[x, y]):
                    x += 1
                if x - x0 >= 22:
                    runs.append(((x0 + x) // 2, y, x - x0))
            else:
                x += 1
    if len(runs) < 3:
        return None
    xs = [r[0] for r in runs]; ys = [r[1] for r in runs]
    return (int(sum(xs) / len(xs)), int(sum(ys) / len(ys)), len(runs))


def detect_red(img, xmax=2200):
    im = img.convert("RGB"); w, h = im.size; px = im.load(); runs = []
    for y in range(0, h, 2):
        x = 0
        while x < min(xmax, w):
            r, g, b = px[x, y]
            if r > 175 and g < 95 and b < 95:
                x0 = x
                while x < min(xmax, w):
                    rr, gg, bb = px[x, y]
                    if not (rr > 175 and gg < 95 and bb < 95):
                        break
                    x += 1
                if x - x0 >= 22:
                    runs.append(((x0 + x) // 2, y))
            else:
                x += 1
    if len(runs) < 3:
        return None
    return (int(sum(p[0] for p in runs) / len(runs)),
            int(sum(p[1] for p in runs) / len(runs)), len(runs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--icon-x", type=int, default=2315)
    ap.add_argument("--icon-y", type=int, default=480)
    ap.add_argument("--candidates", default=None,
                    help="semicolon x,y candidates; default grid")
    ap.add_argument("--post", type=float, default=0.8)
    a = ap.parse_args()
    pid = W.pid_of()
    if not pid:
        print("no gamemd"); return 2
    m = W.Mem(pid)
    ph = P.player_house(m)
    rec = {"tag": a.tag, "pid": pid, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "icon": [a.icon_x, a.icon_y], "credit_off": hex(CREDIT_OFF)}
    before = snap(m)
    rec["before"] = before["b"]
    rec["before_credit"] = before["credit"]
    rec["before_frame"] = before["frame"]

    # 1) click build icon
    oki, infoi = click_client(pid, a.icon_x, a.icon_y, "left")
    rec["icon_click"] = {"ok": oki, "info": infoi}
    print("icon ok=%s" % oki)
    time.sleep(0.35)

    if a.candidates:
        cands = [tuple(int(v) for v in c.split(",")) for c in a.candidates.split(";")]
    else:
        cands = [(900, 700), (1100, 750), (700, 750), (1300, 700),
                 (1000, 550), (800, 900), (1200, 900), (600, 600),
                 (1400, 850), (1000, 950), (500, 750), (1500, 600)]

    # 2) move to candidates, detect green ghost
    target = None
    for (cx, cy) in cands:
        move_client(pid, cx, cy)
        time.sleep(0.28)
        img = ImageGrab.grab(all_screens=False)
        g = detect_green(img)
        r = detect_red(img)
        rec.setdefault("probe", []).append({"xy": [cx, cy], "green": g, "red": r})
        if g and (not r or g[2] >= r[2]):
            target = (g[0], g[1], cx, cy)
            print("GREEN at hover (%d,%d) -> tile (%d,%d) n=%d" % (cx, cy, g[0], g[1], g[2]))
            break
    if target is None:
        print("NO GREEN TILE found; abort placement")
        shot.save(a.tag + "_nogreen", full=True, scale=(1600, 900))
        json.dump(rec, open(os.path.join(EVID, a.tag + ".json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2, default=str)
        return 4
    gx, gy, hx_, hy_ = target
    rec["green_target"] = {"tile_center": [gx, gy], "hover_was": [hx_, hy_]}
    shot.save(a.tag + "_green", full=True, scale=(1600, 900))

    # 3) click the green tile center (immediately, minimal camera drift)
    ok, info = click_client(pid, gx, gy, "left")
    rec["target_click"] = {"ok": ok, "info": info}
    print("target click ok=%s at (%d,%d)" % (ok, gx, gy))
    if not ok:
        json.dump(rec, open(os.path.join(EVID, a.tag + ".json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2, default=str)
        return 3

    # 4) tight credit samples + after snapshot
    rec["credit_post_samples"] = []
    for _ in range(10):
        rec["credit_post_samples"].append(m.u32(ph + CREDIT_OFF))
        time.sleep(0.08)
    time.sleep(a.post)
    after = snap(m)
    rec["after"] = after["b"]
    rec["after_credit"] = after["credit"]
    rec["after_frame"] = after["frame"]
    rec["credit_delta"] = after["credit"] - before["credit"] if (before["credit"] is not None and after["credit"] is not None) else None

    bset = set(before["_objs"].keys()); aset = set(after["_objs"].keys())
    new = sorted(aset - bset); gone = sorted(bset - aset)
    rec["diff"] = {"new": new, "gone": gone,
                   "new_details": [after["_objs"].get(o) for o in new],
                   "gone_details": [before["_objs"].get(o) for o in gone]}
    def napowr_owned(s):
        return sorted(b["obj_hex"] for b in s["_objs"].values()
                      if b["type"] == "NAPOWR" and b["owner_21C"] == ph)
    rec["napowr_before"] = napowr_owned(before)
    rec["napowr_after"] = napowr_owned(after)
    shot.save(a.tag + "_after", full=True, scale=(1600, 900))
    json.dump(rec, open(os.path.join(EVID, a.tag + ".json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2, default=str)
    print(json.dumps({"before_credit": rec["before_credit"], "after_credit": rec["after_credit"],
                      "delta": rec["credit_delta"], "new": new, "gone": gone,
                      "napowr_before": rec["napowr_before"], "napowr_after": rec["napowr_after"]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
