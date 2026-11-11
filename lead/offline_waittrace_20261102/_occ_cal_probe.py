# -*- coding: utf-8 -*-
"""_occ_cal_probe.py - occ_a 口径定义甄别（离线、只读 measure 窗、零真机）。

动机：§505 采纳 occ_a 为「标准度量」，而 §513 已实证等待轨迹侧的停滞时长存在
A/B/C 三定义分叉。本探针回答两个问题：

  Q1 `_xva_p01_stall.py` 的 occ_a 到底属于哪种定义？
  Q2 换成 V4D_RECOMPUTE 钉死的「首末拍跨度」后，各窗读数差多少？

定义（battle/窗口坐标，样本索引 i..k 为同一帧值平台）：
  B = ts[k] - ts[i]                       首见→末见（V4D_RECOMPUTE 钉死）
  C = ts[k+1] - ts[i]                     持续到下一帧首见（= 到下一推进拍）
  occ_a 实现：head=trans[0]-ts[0]；interior= tb - ta（相邻 trans 时刻差）；tail=ts[-1]-trans[-1]
  ⇒ interior 用的正是 C；边缘段 head/tail 天然是 B 型。

stdout 由 Bash 重定向落盘。
用法：python -I -X utf8 _occ_cal_probe.py > _occ_cal_probe_out.txt
"""

import json
import os

ROOT = r"D:\Project\ra2-campaign-forge"
BASE = os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003",
                    "lead", "qc161_u0400_trip")
T = 0.1

# 与 _xva_p01_stall.py 同一趟表，另加 v4c/v4d（本轮关注）
TRIPS = [
    ("l3_1101v3a", [0, 1, 2]), ("l3_1101v3b", [0, 1, 2]),
    ("l3_20261031ha", [0]), ("l3_20261031hb", [0, 1, 2]),
    ("l3_20261023q", [0, 1, 2]), ("l3_20261023r", [0, 1, 2]),
    ("l1c_20261021", [0, 1, 2]), ("l1a_20261020", [0, 1, 2]),
    ("t55k_20261020", [0, 1, 2]), ("l1_20261023e4", [0, 1, 2]),
    ("l3_1101v4c", [0, 1, 2]), ("l3_1101v4d", [0, 1, 2]),
]


def P(s=""):
    print(s)


def occ_a_impl(ts, fs):
    """逐字复刻 _xva_p01_stall.py L154-196 的段构造与合计。"""
    n = len(ts)
    span = ts[-1] - ts[0]
    trans = [(fs[i], ts[i]) for i in range(1, n) if fs[i] != fs[i - 1]]
    segs = []
    if trans:
        head = trans[0][1] - ts[0]
        if head > T:
            segs.append(("head", head))
        for (fa, ta), (fb, tb) in zip(trans, trans[1:]):
            if tb - ta > T:                      # ← interior = C 定义
                segs.append(("interior", tb - ta))
        tail = ts[-1] - trans[-1][1]
        if tail > T:
            segs.append(("tail", tail))
    else:
        if span > T:
            segs.append(("head", span))
    return segs, span, len(trans)


def occ_b(ts, fs):
    """同一批段，但把 interior 改成「首见→末见」（B 定义）。"""
    n = len(ts)
    span = ts[-1] - ts[0]
    if n < 2:
        return [], span, 0
    segs = []
    i = 0
    # head：首帧值从 ts[0] 持续到最后一次出现
    j = 0
    while j + 1 < n and fs[j + 1] == fs[0]:
        j += 1
    head = ts[j] - ts[0]
    if head > T:
        segs.append(("head", head))
    i = j + 1
    while i < n:
        k = i
        while k + 1 < n and fs[k + 1] == fs[i]:
            k += 1
        dur = ts[k] - ts[i]
        if dur > T:
            segs.append(("tail" if k == n - 1 else "interior", dur))
        i = k + 1
    return segs, span, sum(1 for x in range(1, n) if fs[x] != fs[x - 1])


def pct(segs, span):
    if not span:
        return 0.0
    return 100.0 * sum(s[1] for s in segs) / span


rows = []
P("=" * 100)
P("%-16s %2s %8s %10s %10s %10s %8s" % ("trip", "w", "span_s", "occ_a%", "occ_B%", "diff_pp", "n_trans"))
P("=" * 100)
for trip, wins in TRIPS:
    for w in wins:
        path = os.path.join(BASE, trip, "measure_w%d.json" % w)
        if not os.path.isfile(path):
            P("%-16s %2d  !! 缺文件" % (trip, w))
            continue
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        ts = d["samples"]["t"]
        fs = d["samples"]["f"]
        if len(ts) < 2:
            P("%-16s %2d  (空窗, verdict=%s)" % (trip, w, d.get("verdict")))
            continue
        sa, span, ntr = occ_a_impl(ts, fs)
        sb, _, _ = occ_b(ts, fs)
        pa, pb = pct(sa, span), pct(sb, span)
        kinds_a = {}
        for k, v in sa:
            kinds_a[k] = kinds_a.get(k, 0) + 1
        P("%-16s %2d %8.3f %10.4f %10.4f %+10.4f %8d   A段=%s"
          % (trip, w, span, pa, pb, pa - pb, ntr,
             ",".join("%s×%d" % (k, v) for k, v in sorted(kinds_a.items())) or "-"))
        rows.append((trip, w, pa, pb, sa, sb))

P()
P("=" * 100)
P("## 汇总")
if rows:
    tot_a = sum(r[2] for r in rows) / len(rows)
    tot_b = sum(r[3] for r in rows) / len(rows)
    P("   窗数=%d  occ_a 算术均值=%.4f%%  occ_B 算术均值=%.4f%%  均值差=%+.4f pp"
      % (len(rows), tot_a, tot_b, tot_a - tot_b))
    diff = [r[2] - r[3] for r in rows]
    P("   逐窗差 max=%+.4fpp min=%+.4fpp  非零窗=%d/%d"
      % (max(diff), min(diff), sum(1 for x in diff if abs(x) > 1e-9), len(diff)))
    worst = max(rows, key=lambda r: abs(r[2] - r[3]))
    P("   最大差窗=%s w%d  occ_a=%.4f%% occ_B=%.4f%% 差=%+.4fpp"
      % (worst[0], worst[1], worst[2], worst[3], worst[2] - worst[3]))
    P()
    P("   ★ 判定：occ_a 的 interior 用 tb-ta（相邻 trans 时刻差）⇒ 属 C 定义；")
    P("     B 定义下同一批窗的读数见上表。两者是否同判据由 D-12② 裁决，本探针只报数值。")
