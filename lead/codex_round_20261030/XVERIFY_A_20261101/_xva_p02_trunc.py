#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""XVERIFY_A_20261101 探针 p02：首尾截断 + 跨窗连续性 + 洞内推进 + 特窗分期。只读，零写盘。"""
import json, io, sys, os, statistics

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

def load(trip, w):
    p = os.path.join(BASE, trip, "measure_w%d.json" % w)
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)

def p01(trip, w):
    d = load(trip, w)
    ts = d["samples"]["t"]; fs = d["samples"]["f"]
    n = len(ts)
    trans = [(fs[i], ts[i]) for i in range(1, n) if fs[i] != fs[i - 1]]
    dts = [ts[i + 1] - ts[i] for i in range(n - 1)]
    return d, ts, fs, trans, dts

print("== A. 跨窗连续性（同趟相邻窗：帧号衔接 / 窗间未测时长 / 跨窗冻结下界）")
for trip, wins in TRIPS:
    for a, b in zip(wins, wins[1:]):
        da, tsa, fsa, tra, _ = p01(trip, a)
        db, tsb, fsb, trb, _ = p01(trip, b)
        t_end_a = da["t_abs0"] + tsa[-1]
        t_beg_b = db["t_abs0"] + tsb[0]
        gap_t = t_beg_b - t_end_a
        dF = fsb[0] - fsa[-1]
        tail_a = tsa[-1] - tra[-1][1] if tra else tsa[-1] - tsa[0]
        # 跨窗冻结：w_a 尾帧==w_b 首帧 且 两侧均冻结 -> 连续冻结下界 = tail_a + gap_t + head_b(窗内已冻部分)
        frozen_a = tail_a > T_STALL
        head_b = (trb[0][1] - tsb[0]) if trb else (tsb[-1] - tsb[0])
        frozen_b = head_b > T_STALL
        note = ""
        lb = None
        if frozen_a and frozen_b and fsa[-1] == trb[0][0] if trb else False:
            pass
        if tra and trb and fsa[-1] == fsb[0] and tail_a > T_STALL and head_b > T_STALL:
            lb = tail_a + gap_t + head_b
            note = "两侧同帧冻结"
        print("  %s w%d->w%d: 帧号 %d->%d (dF=%+d) 窗间未测=%.2fs tailA=%.3fs headB=%.3fs %s%s" % (
            trip, a, b, fsa[-1], fsb[0], dF, gap_t, tail_a, head_b,
            note, (" 跨窗冻结下界=%.2fs" % lb) if lb else ""))

print()
print("== B. 到拍洞内推进审计（>10ms 洞，洞两侧 f 是否推进；n_multi 明细）")
for trip, wins in TRIPS:
    for w in wins:
        d, ts, fs, trans, dts = p01(trip, w)
        holes = 0
        holes_adv = 0
        max_hole_adv = 0.0
        multis = []
        for i in range(len(dts)):
            df = fs[i + 1] - fs[i]
            if df > 1:
                multis.append((round(dts[i] * 1000, 1), fs[i], fs[i + 1]))
            if dts[i] > 0.010:
                holes += 1
                if fs[i + 1] > fs[i]:
                    holes_adv += 1
                    max_hole_adv = max(max_hole_adv, dts[i])
        nm = len(multis)
        flag = " <-- 洞内推进!" if holes_adv else ""
        extra = (" multi明细(t_ms,f0,f1)=%s" % multis[:5]) if nm else ""
        if holes or nm:
            print("  %s w%d: >10ms洞=%d 洞内推进=%d 最大洞内推进洞=%.3fs%s%s" % (
                trip, w, holes, holes_adv, max_hole_adv, flag, extra))

print()
print("== C. 特窗分期（q w2 / r w1 / r w2 / e4 w1 / e4 w2 / l1a w2 / ha w0）")
def phases(trip, w, label):
    d, ts, fs, trans, dts = p01(trip, w)
    t0 = ts[0]
    print("  -- %s %s w%d" % (label, trip, w))
    if not trans:
        u = [c.get("units") for c in (d.get("counters") or [])]
        print("     全窗零帧沿: f=%d 恒定 采样健康=%s 中位拍=%.3fms >10ms拍=%d units轨迹=%s" % (
            fs[0], max(dts) < 0.010, statistics.median(dts) * 1000,
            sum(1 for g in dts if g > 0.010), u))
        return
    # 相邻帧沿间隔中位（活跃期）
    eg = [b - a for (fa, a), (fb, b) in zip(trans, trans[1:]) if b - a <= T_STALL]
    if eg:
        print("     帧沿活跃间隔(<=0.1s): n=%d 中位=%.1fms p90=%.1fms" % (
            len(eg), statistics.median(eg) * 1000,
            sorted(eg)[int(0.9 * (len(eg) - 1))] * 1000))
    else:
        print("     帧沿活跃间隔(<=0.1s): 无（全部帧沿间隔>0.1s）")
    u0 = [c.get("units") for c in (d.get("counters") or [])]
    print("     units 1Hz 轨迹: %s" % u0)
    big = [(round(a - t0, 3), round(b - a, 3), fa) for (fa, a), (fb, b) in zip(trans, trans[1:]) if b - a > T_STALL]
    tail = ts[-1] - trans[-1][1]
    head = trans[0][1] - ts[0]
    print("     大冻结段(interior): %s" % big)
    print("     head=%.3fs tail=%.3fs 首帧沿=%.3fs 末帧沿=%.3fs" % (head, tail, trans[0][1] - t0, trans[-1][1] - t0))

phases("l3_20261023q", 2, "低fps零停滞待解释")
phases("l3_20261023r", 1, "census快窗复核")
phases("l3_20261023r", 2, "census帧沿不足复核")
phases("l1_20261023e4", 1, "census 0%复核")
phases("l1_20261023e4", 2, "census帧沿不足复核")
phases("l1a_20261020", 2, "快窗尾部复核")
phases("l3_20261031ha", 0, "短窗复核")

print()
print("== D. §500 逐秒口径假设核查：v3a w0 桶1（去 head 后 interior-only 是否≈86%）")
d, ts, fs, trans, dts = p01("l3_1101v3a", 0)
t0 = ts[0]
inter = [(a, b) for (fa, a), (fb, b) in zip(trans, trans[1:]) if b - a > T_STALL]
frozen1 = sum(max(0.0, min(b, t0 + 1) - max(a, t0)) for a, b in inter)
head = trans[0][1] - t0
print("  v3a w0 桶[0,1s): interior-only=%.1f%%  interior+head=%.1f%%  head=%.3fs" % (
    100 * frozen1, 100 * (frozen1 + head), head))
