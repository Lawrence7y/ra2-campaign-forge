#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""XVERIFY_A_20261101 探针 p04：全量停滞段清单（每窗每段：时长/起始帧/起始墙钟/t_rel/kind）。
stdout 打印完整清单（>0.1s，head/interior/tail 全部），重定向落盘 _xva_p04_out.txt。
"""
import json, io, sys, os
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = r"D:\Project\ra2-campaign-forge"
BASE = os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003",
                    "lead", "qc161_u0400_trip")
T_STALL = 0.1

TRIPS = [
    ("l3_1101v3a", [0, 1, 2]), ("l3_1101v3b", [0, 1, 2]),
    ("l3_20261031ha", [0]), ("l3_20261031hb", [0, 1, 2]),
    ("l3_20261023q", [0, 1, 2]), ("l3_20261023r", [0, 1, 2]),
    ("l1c_20261021", [0, 1, 2]), ("l1a_20261020", [0, 1, 2]),
    ("t55k_20261020", [0, 1, 2]), ("l1_20261023e4", [0, 1, 2]),
]

for trip, wins in TRIPS:
    for w in wins:
        p = os.path.join(BASE, trip, "measure_w%d.json" % w)
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        ts = d["samples"]["t"]; fs = d["samples"]["f"]
        t_abs0 = d.get("t_abs0")
        n = len(ts)
        trans = [(fs[i], ts[i]) for i in range(1, n) if fs[i] != fs[i - 1]]
        segs = []
        if trans:
            head = trans[0][1] - ts[0]
            if head > T_STALL:
                segs.append(("head", ts[0], head, fs[0]))
            for (fa, a), (fb, b) in zip(trans, trans[1:]):
                if b - a > T_STALL:
                    segs.append(("int", a, b - a, fa))
            tail = ts[-1] - trans[-1][1]
            if tail > T_STALL:
                segs.append(("tail", trans[-1][1], tail, trans[-1][0]))
        else:
            segs.append(("head", ts[0], ts[-1] - ts[0], fs[0]))
        segs.sort(key=lambda s: s[1])
        w0 = datetime.fromtimestamp(t_abs0 + ts[0]).strftime("%H:%M:%S.%f")[:-3]
        print("== %s w%d 窗起墙钟=%s 段数=%d 合计=%.3fs" % (
            trip, w, w0, len(segs), sum(s[2] for s in segs)))
        for kind, a, dur, fa in segs:
            wall = datetime.fromtimestamp(t_abs0 + a).strftime("%H:%M:%S.%f")[:-3]
            print("   %-5s dur=%.3fs 起始帧=%d 起始t=%.3fs 墙钟=%s" % (
                kind, dur, fa, a - ts[0], wall))
