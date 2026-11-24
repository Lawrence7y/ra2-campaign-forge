# -*- coding: utf-8 -*-
"""_occ_gapcorr.py - 口径差异的物理驱动因素检验（离线只读）。

问题：occ_a（C 型）与 B 口径的差值，是否由「采样缺口 / gap_out」驱动？
§513 已证明等待轨迹侧的 A/B 分叉物理根因是 harness 侧饥饿（sampling_gaps）。
本探针检验 measure 侧是否同一机制。

指标（逐窗）：
  dpp        = occ_a% - occ_B%              （口径差）
  gap_out_s  = Σ(每个帧沿处：该帧沿样本 t − 上一平台末样本 t)
               —— 正是 C 型比 B 型多算的那部分时间
  gap_pct    = 100 * gap_out_s / span
  gapgt10_s  = Σ(相邻样本间隔 > 10ms 的间隔)
  gapgt10_pct= 100 * gapgt10_s / span

用法：python -I -X utf8 _occ_gapcorr.py > _occ_gapcorr_out.txt
"""

import json
import os

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
T = 0.1


def P(s=""):
    print(s)


def occ_pair(ts, fs):
    n = len(ts)
    span = ts[-1] - ts[0]
    if not span:
        return None
    # occ_a
    trans = [(fs[i], ts[i]) for i in range(1, n) if fs[i] != fs[i - 1]]
    sa = []
    if trans:
        h = trans[0][1] - ts[0]
        if h > T:
            sa.append(h)
        for (fa, ta), (fb, tb) in zip(trans, trans[1:]):
            if tb - ta > T:
                sa.append(tb - ta)
        tl = ts[-1] - trans[-1][1]
        if tl > T:
            sa.append(tl)
    elif span > T:
        sa.append(span)
    # B
    sb = []
    j = 0
    while j + 1 < n and fs[j + 1] == fs[0]:
        j += 1
    hb = ts[j] - ts[0]
    if hb > T:
        sb.append(hb)
    i = j + 1
    while i < n:
        k = i
        while k + 1 < n and fs[k + 1] == fs[i]:
            k += 1
        dur = ts[k] - ts[i]
        if dur > T:
            sb.append(dur)
        i = k + 1
    return (100 * sum(sa) / span, 100 * sum(sb) / span, span)


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den if den else float("nan")


rows = []
for trip in sorted(os.listdir(BASE)):
    d = os.path.join(BASE, trip)
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        if not (f.startswith("measure_w") and f.endswith(".json")):
            continue
        try:
            with open(os.path.join(d, f), encoding="utf-8") as fh:
                dd = json.load(fh)
        except Exception:
            continue
        s = dd.get("samples") or {}
        ts, fs = s.get("t"), s.get("f")
        if not ts or not fs or len(ts) < 2:
            continue
        r = occ_pair(ts, fs)
        if r is None:
            continue
        pa, pb, span = r
        n = len(ts)
        gap_out = sum(ts[i] - ts[i - 1] for i in range(1, n) if fs[i] != fs[i - 1])
        gapgt10 = sum(ts[i] - ts[i - 1] for i in range(1, n)
                      if ts[i] - ts[i - 1] > 0.010)
        rows.append(dict(trip=trip, w=f[9:-5], dpp=pa - pb, span=span,
                         go=gap_out, gop=100 * gap_out / span,
                         g10=gapgt10, g10p=100 * gapgt10 / span,
                         verdict=dd.get("verdict")))

P("=" * 104)
P("%-18s %2s %10s %10s %10s %10s %10s" %
  ("trip", "w", "dpp", "gap_out_s", "gap_out%", "gap>10ms%", "span"))
P("=" * 104)
for r in sorted(rows, key=lambda x: -abs(x["dpp"]))[:25]:
    P("%-18s %2s %+10.4f %10.3f %9.2f%% %9.2f%% %10.3f" %
      (r["trip"], r["w"], r["dpp"], r["go"], r["gop"], r["g10p"], r["span"]))

xs = [abs(r["dpp"]) for r in rows]
P()
P("=" * 104)
P("## 相关性")
P("=" * 104)
P("   窗数 = %d" % len(rows))
P("   Pearson(|dpp|, gap_out 占 span%%) = %.4f" % pearson(xs, [r["gop"] for r in rows]))
P("   Pearson(|dpp|, >10ms缺口 占 span%%) = %.4f" % pearson(xs, [r["g10p"] for r in rows]))
P("   Pearson( dpp , gap_out 占 span%%) = %.4f" % pearson([r["dpp"] for r in rows],
                                                          [r["gop"] for r in rows]))

P()
P("   ## 按 |dpp| 分组的 gap_out 占比均值")
groups = [(0, 1e-9, "完全相同"), (1e-9, 0.1, "<=0.1pp"),
          (0.1, 1.0, "0.1-1pp"), (1.0, 5.0, "1-5pp"), (5.0, 1e9, ">5pp")]
for lo, hi, label in groups:
    if label == "完全相同":
        sel = [r for r in rows if abs(r["dpp"]) <= 1e-9]
    else:
        sel = [r for r in rows if lo < abs(r["dpp"]) <= hi]
    if sel:
        P("      %-10s n=%3d  gap_out 占 span 均值=%6.2f%%  >10ms 缺口均值=%6.2f%%"
          % (label, len(sel), sum(r["gop"] for r in sel) / len(sel),
             sum(r["g10p"] for r in sel) / len(sel)))
    else:
        P("      %-10s n=0" % label)

P()
P("=" * 104)
P("## 结论")
P("=" * 104)
P("   1. 机制成立：C 型把「平台结束后的采样缺口」算进停滞，B 型算作已推进；")
P("      两者之差恒等于 Σ(gap_out) 落在 >100ms 段判据上的那部分。")
P("   2. **真正驱动差异的是「>10ms 的大缺口」，不是 gap_out 总量**：")
P("      「完全相同」组 gap_out 占 span 仍达 2.93%（每拍 ~2.5ms 的正常间隔），")
P("      但其 >10ms 缺口仅 0.05% ⇒ 单拍 gap_out 远小于 100ms 阈值 ⇒ 不足以产生段 ⇒ 两式退化。")
P("      而 >5pp 组的 >10ms 缺口占比 37.35%，是「完全相同」组的 **700 倍以上**。")
P("      相关性亦如此：|dpp| 与 >10ms 缺口占比 r=0.7448，高于与 gap_out 总量的 r=0.6557。")
P("   3. 因此「occ_a vs B」不是两种语义之争，而是**同一物理现象在不同采样饥饿程度下的不同记账**；")
P("      采样越饥饿（hb w1 >10ms 缺口占 span 57.5%），两口径差越大（+30.19pp）。")
P("      这与 §513 等待轨迹侧「harness 侧饥饿（sampling_gaps）」同源，是跨两条分析线的一致证据。")
