#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单次放置：紧邻采样额度(before/after)+完整建筑快照+screenshot，用 click_client 点击。
用法：place_one.py --tag p01 --cx <screen> --cy <screen> [--icon-x --icon-y]
若 --icon-x/y 给出，先点建造图标进入放置模式，再点目标格。
"""
import argparse
import json
import os
import sys
import time

import w177_core as W
import wb_probe as P
from w177_click import click_client
import shot

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
CREDIT_OFF = 0x30C


def hx(v):
    return hex(v) if isinstance(v, int) and v else (None if not v else v)


def snap(pid, m):
    ph = P.player_house(m)
    credit = m.u32(ph + CREDIT_OFF) if ph else None
    frame = m.u32(W.A_FRAME)
    aitems, acount, bl = P.enumerate_buildings(m)
    blds = {}
    for i, obj in bl:
        b = P.one_building(m, i, obj)
        blds[obj] = b
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "frame": frame,
            "credit": credit, "playerHouse": hx(ph),
            "objects": m.u32(W.A_ABSTRACT),
            "n_buildings": len(bl), "abstractCount": acount,
            "buildings": {hex(k): v for k, v in blds.items()},
            "_objs": blds}


def sample_credit(m, ph, n=8, dt=0.12):
    out = []
    for _ in range(n):
        out.append(m.u32(ph + CREDIT_OFF))
        time.sleep(dt)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--cx", type=int, required=True)
    ap.add_argument("--cy", type=int, required=True)
    ap.add_argument("--icon-x", type=int, default=None)
    ap.add_argument("--icon-y", type=int, default=None)
    ap.add_argument("--bbox", default=None)
    ap.add_argument("--post", type=float, default=1.2)
    a = ap.parse_args()
    pid = W.pid_of()
    if not pid:
        print("no gamemd"); return 2
    m = W.Mem(pid)
    ph = P.player_house(m)

    rec = {"tag": a.tag, "pid": pid, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "target_screen": [a.cx, a.cy], "credit_off": hex(CREDIT_OFF)}
    # BEFORE
    before = snap(pid, m)
    rec["before"] = {k: v for k, v in before.items() if k != "_objs"}
    # pre-credit tight samples
    rec["credit_pre_samples"] = sample_credit(m, ph, n=5, dt=0.10)
    before2 = snap(pid, m)   # refresh immediately before click
    rec["before_credit"] = before2["credit"]

    # ICON click (enter placement mode) if requested
    if a.icon_x is not None and a.icon_y is not None:
        ok_i, info_i = click_client(pid, a.icon_x, a.icon_y, "left")
        rec["icon_click"] = {"ok": ok_i, "info": info_i, "xy": [a.icon_x, a.icon_y]}
        print("icon click ok=%s" % ok_i)
        time.sleep(0.5)
        # capture placement preview screenshot (full, scaled)
        shot.save(a.tag + "_ghost", full=True, scale=(1600, 900))

    # TARGET click
    ok, info = click_client(pid, a.cx, a.cy, "left")
    rec["target_click"] = {"ok": ok, "info": info}
    print("target click ok=%s %s" % (ok, info))
    if not ok:
        json.dump(rec, open(os.path.join(EVID, a.tag + ".json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        return 3

    # POST credit tight samples (catch the discrete -600 step)
    rec["credit_post_samples"] = sample_credit(m, ph, n=10, dt=0.10)
    time.sleep(a.post)
    after = snap(pid, m)
    rec["after"] = {k: v for k, v in after.items() if k != "_objs"}
    rec["after_credit"] = after["credit"]
    rec["credit_delta"] = (after["credit"] - before2["credit"]) if (after["credit"] is not None and before2["credit"] is not None) else None

    # DIFF new buildings (player-owned NAPOWR)
    bset = set(before2["_objs"].keys())
    aset = set(after["_objs"].keys())
    new = sorted(aset - bset)
    gone = sorted(bset - aset)
    rec["diff"] = {"new": new, "gone": gone,
                   "new_details": [after["_objs"].get(o) for o in new],
                   "gone_details": [before2["_objs"].get(o) for o in gone]}
    # NAPOWR count diff by player
    def napowr_owned(rec_snap):
        out = []
        for b in rec_snap["_objs"].values():
            if b["type"] == "NAPOWR" and b["owner_21C"] == P.player_house(m):
                out.append(b["obj_hex"])
        return sorted(out)
    rec["napowr_player_before"] = napowr_owned(before2)
    rec["napowr_player_after"] = napowr_owned(after)

    shot.save(a.tag + "_after", full=True, scale=(1600, 900))
    if a.bbox:
        shot.save(a.tag + "_after_bbox", bbox=tuple(int(x) for x in a.bbox.split(",")))
    path = os.path.join(EVID, a.tag + ".json")
    json.dump(rec, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)
    print("saved %s" % path)
    print(json.dumps({"before_credit": rec["before_credit"], "after_credit": rec["after_credit"],
                      "delta": rec["credit_delta"],
                      "new": new, "gone": gone,
                      "napowr_before": rec["napowr_player_before"],
                      "napowr_after": rec["napowr_player_after"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
