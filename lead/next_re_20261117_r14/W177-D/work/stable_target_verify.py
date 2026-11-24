#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对当前观测到的 chain>=2 格做 6 次 ~0.6s 间隔的定点验证，输出每次完整节点集合，
用于判定同一格同一节点集合稳定>=3s。只读。"""
import sys,time,json
import w177_core as W
import wb_probe as P
import dsnap as D

CELLS=[(48,88),(48,89),(48,90),(37,67)]
pid=W.pid_of(); m=W.Mem(pid); ph=P.player_house(m)
print(json.dumps({"note":"targeted stable verify","playerHouse":hex(ph),"cells":CELLS,"bypass":D.bypass_globals(m)}))
hist={c:[] for c in CELLS}
for it in range(7):
    frame=m.u32(W.A_FRAME); ts=time.strftime("%H:%M:%S")
    for c in CELLS:
        cd=D.cell_detail(m,*c)
        nodes=cd.get("nodesA",[])+cd.get("nodesB",[])
        keys=tuple(sorted(n["this"] for n in nodes))
        hist[c].append(keys)
        print(json.dumps({"iter":it,"frame":frame,"ts":ts,"cell":"%d,%d"%c,
            "lenA":cd.get("lenA"),"lenB":cd.get("lenB"),
            "nodes":[{"this":n["this"],"rtti":n["rtti_name"],"owner":n["owner_hex"],
                      "is_player":(n["owner_21C"]==ph),"layer_94":n["layer_94"],
                      "o1":n["o1_81"],"o2":n["o2_74"]} for n in nodes]},ensure_ascii=False))
    time.sleep(0.6)
print("=== stability summary: max run of identical node-set per cell ===")
for c in CELLS:
    seq=hist[c]; best=0;cur=0;prev=None
    for s in seq:
        if s and s==prev: cur+=1
        elif s: cur=1; prev=s
        else: cur=0;prev=None
        best=max(best,cur)
    print(json.dumps({"cell":"%d,%d"%c,"max_identical_run_scans":best,"seq_lens":[len(x) for x in seq]}))
