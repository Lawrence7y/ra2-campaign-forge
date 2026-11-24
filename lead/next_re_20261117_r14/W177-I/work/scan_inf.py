#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描玩家步兵所在格（RTTI=InfantryClass），给 T3 选目标格 T。只读内存。"""
import os, json, sys
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D

def main():
    pid = W.pid_of()
    m = W.Mem(pid)
    ph = P.player_house(m)
    # 通过 AbstractClass::Array + vtable 分类步兵/单位
    inf_cells = {}
    aitems = m.u32(P.A_ABSTRACT_ITEMS); acount = m.u32(P.A_ABSTRACT)
    for i in range(acount):
        p = m.u32(aitems + 4*i)
        if not p or (p & 3): continue
        if m.u32(p + 0x21C) != ph: continue  # 只玩家
        nm, _ = D.rtti_name(m, p)
        if not nm or 'InfantryClass' not in nm: continue
        lx = m.u32(p + 0x9C); ly = m.u32(p + 0xA0)
        if lx is None or ly is None: continue
        cx, cy = (lx >> 8) & 0xFFFFFFFF, (ly >> 8) & 0xFFFFFFFF
        # signed shift for safety (cells are small positive here)
        if lx & 0x80000000: cx = ((lx & 0xFFFFFFFF) - 0x100000000) >> 8
        if ly & 0x80000000: cy = ((ly & 0xFFFFFFFF) - 0x100000000) >> 8
        inf_cells.setdefault((cx, cy), []).append(hex(p))
    # 每格读 [+0xE4] 链详情
    out = []
    for (cx, cy), thises in sorted(inf_cells.items()):
        d = D.cell_detail(m, cx, cy)
        out.append({"cell": [cx, cy], "inf_count": len(thises), "inf_this": thises,
                    "lenA": d.get("lenA"), "lenB": d.get("lenB"),
                    "rttiA": [n.get("rtti_name") for n in d.get("nodesA", [])]})
    snap = {"frame": m.u32(W.A_FRAME), "credits": m.u32(ph+0x30C),
            "playerHouse": hex(ph), "inf_cells": out}
    m.close()
    print(json.dumps(snap, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
