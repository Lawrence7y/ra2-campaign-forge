#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""综合追踪：6 次扫描（每次 ~1s），每次记录所有 chain>=2 格的完整节点详情；
结束时判定同一格同一节点集合连续 >=3 次的稳定实例，输出其最后一次的完整详情。只读。"""
import sys, time, json
import w177_core as W
import wb_probe as P
import dsnap as D

pid = W.pid_of()
m = W.Mem(pid)
ph = P.player_house(m)
base = m.u32(P.CELL_ARRAY); mapc = P.MAP_SINGLETON
w = m.u32(mapc+0x14C); h = m.u32(mapc+0x150)
aitems = m.u32(P.A_ABSTRACT_ITEMS); acnt = m.u32(P.A_ABSTRACT)

def scan():
    # 用对象 location 建 cell->objs，只检查候选格
    cellobjs = {}
    for i in range(acnt):
        p = m.u32(aitems+4*i)
        if not p or not (0x20000 < p < 0x70000000): continue
        x = m.u32(p+0x9C); y = m.u32(p+0xA0)
        if x is None or y is None: continue
        sx = x-0x100000000 if x & 0x80000000 else x
        sy = y-0x100000000 if y & 0x80000000 else y
        cx, cy = sx>>8, sy>>8
        cellobjs.setdefault((cx,cy),[]).append(p)
    out = {}
    for (cx,cy),objs in cellobjs.items():
        if len(objs) < 2 or not (0<=cx<w and 0<=cy<h): continue
        cell = m.u32(base+((cy<<9)+cx)*4)
        if not cell or cell == P.INVALID_CELL: continue
        cd = D.cell_detail(m,cx,cy)
        if cd.get("lenA",0) >= 2 or cd.get("lenB",0) >= 2:
            out[(cx,cy)] = cd
    return out

hist = []
last_detail = {}
for it in range(6):
    s = scan()
    hist.append({c: tuple(sorted([n["this"] for n in cd.get("nodesA",[])+cd.get("nodesB",[])])) for c,cd in s.items()})
    last_detail = s
    print(json.dumps({"iter":it,"frame":m.u32(W.A_FRAME),"ts":time.strftime("%H:%M:%S"),
                      "n_cells":len(s),"cells":{("%d,%d"%c):{"lenA":cd.get("lenA"),"lenB":cd.get("lenB")} for c,cd in s.items()}}))
    time.sleep(1)

# 判定稳定：同一 cell 同一节点集合连续 >=3 次
allc = set()
for hmap in hist: allc |= set(hmap)
print("=== STABLE (same cell & same node-set >=3 consecutive scans) with full detail ===")
for c in sorted(allc):
    seq = [hist[i].get(c) for i in range(len(hist))]
    best = 0; cur = 0; curset=None
    for s in seq:
        if s and s == curset: cur += 1
        elif s: cur = 1; curset = s
        else: cur = 0; curset = None
        best = max(best,cur)
    if best >= 3 and c in last_detail:
        cd = last_detail[c]
        nodes = cd.get("nodesA",[])+cd.get("nodesB",[])
        print(json.dumps({"cell":"%d,%d"%c,"stable_scans":best,"cellptr":cd.get("cell"),
                          "lenA":cd.get("lenA"),"lenB":cd.get("lenB"),
                          "nodes":[{"this":n["this"],"rtti":n["rtti_name"],"owner":n["owner_hex"],
                                    "is_player":(n["owner_21C"]==ph),"layer_94":n["layer_94"],
                                    "o1":n["o1_81"],"o2":n["o2_74"],"chainbit_8C":n.get("chainbit_8C")}
                                   for n in nodes]},ensure_ascii=False))
