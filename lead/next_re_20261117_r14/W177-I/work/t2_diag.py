#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T2 诊断：当前 credits / 玩家建筑列表(vtable分类) / NAPOWR 对象 / 目标格链 / frame。
只读内存。用于下单前基线。"""
import os, json, sys
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D

def main():
    pid = W.pid_of()
    if not pid:
        print("no gamemd"); return 2
    m = W.Mem(pid)
    ph = P.player_house(m)
    rec = {
        "pid": pid, "frame": m.u32(W.A_FRAME), "mode": m.u32(W.A_MODE),
        "playerHouse": hex(ph), "credits_30C": m.u32(ph+0x30C),
        "player_building_types": C.all_player_building_types(m, ph),
        "napowr": C.napowr_objects(m, ph),
        "building_array_count": W.building_array(m)[1],
        "cam": C.cam_origin(m),
    }
    # 所有 BuildingClass 简表（this/type/owner/limbo/cell）
    blds = []
    for i, obj in P.enumerate_buildings(m)[2]:
        b = P.one_building(m, i, obj)
        nm, _ = D.rtti_name(m, obj)
        blds.append({"idx": i, "this": b["obj_hex"], "type": b["type"],
                     "owner": b["owner_hex"], "is_player": b["owner_21C"]==ph,
                     "o1_81": b["o1_81"], "o2_74": b["o2_74"], "o3_80": b["o3_80"],
                     "cell": [b["cell"]["cellX"], b["cell"]["cellY"]],
                     "cell_valid": b["cell"]["valid"],
                     "rtti": nm})
    rec["all_buildings"] = blds
    m.close()
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
