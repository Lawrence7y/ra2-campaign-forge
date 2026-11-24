#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对指定的稳定格做逐秒 atomic 快照（含 RTTI/owner/layer），写 JSONL。验证>=3s稳定。只读。"""
import sys, time, json
import w177_core as W
import wb_probe as P
import dsnap as D

CELLS = [(50,87),(50,88),(51,87)]
pid = W.pid_of()
m = W.Mem(pid)
ph = P.player_house(m)
print(json.dumps({"note":"stable cell verification","playerHouse":hex(ph),"bypass":D.bypass_globals(m)}))
for it in range(8):  # ~8 scans over ~4s game-time
    rec = {"iter":it,"frame":m.u32(W.A_FRAME),"ts":time.strftime("%H:%M:%S"),"cells":{}}
    for (cx,cy) in CELLS:
        cd = D.cell_detail(m,cx,cy)
        rec["cells"]["%d,%d"%(cx,cy)] = {
            "cell":cd.get("cell"),"lenA":cd.get("lenA"),"lenB":cd.get("lenB"),
            "nodesA":[{"this":n["this"],"rtti":n["rtti_name"],"owner":n["owner_hex"],
                       "layer_94":n["layer_94"],"o1":n["o1_81"],"o2":n["o2_74"],
                       "chainbit_8C":n.get("chainbit_8C")} for n in cd.get("nodesA",[])],
            "nodesB":[{"this":n["this"],"rtti":n["rtti_name"],"owner":n["owner_hex"],
                       "layer_94":n["layer_94"]} for n in cd.get("nodesB",[])],
        }
    print(json.dumps(rec,ensure_ascii=False))
    time.sleep(0.5)
