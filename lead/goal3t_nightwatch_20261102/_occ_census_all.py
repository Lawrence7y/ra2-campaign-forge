# -*- coding: utf-8 -*-
"""_occ_census_all.py - occ_a 口径影响全量普查（离线、只读、零真机）。

动机：D-12② 的选项 (B)「口径 B 为准并回溯重算全部历史含停滞数字的批次」至今
没有量级评估——§514 只甄别了 34 窗/12 趟（`_occ_cal_probe.py` 的 TRIPS 表是手工
挑的子集），而盘上实有 95 窗/39 趟。本探针把这 95 窗全部按三定义算一遍，给出
「若采纳 B 口径，历史上多少条读数会变、变多少」的完整清单。

定义（沿用 §514 / `_occ_cal_probe.py`，样本索引 i..k 为同一帧值平台）：
  B = ts[k] - ts[i]             首见→末见（V4D_RECOMPUTE 钉死）
  C = ts[k+1] - ts[i]           持续到下一帧首见（= occ_a interior 实装口径）
  occ_a 实装：head=trans[0]-ts[0]；interior= tb-ta（相邻 trans 时刻差）；tail=ts[-1]-trans[-1]
  ⇒ interior=C 型、head/tail=B 型（同函数混用，§514 已定谳）

输出：逐窗表 + 变化分级汇总 + 差异最大的窗排序。
用法：python -I -X utf8 _occ_census_all.py > _occ_census_all_out.txt
"""

import json
import os

ROOT = r"D:\Project\ra2-campaign-forge"
BASE = os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003",
                    "lead", "qc161_u0400_trip")
T = 0.1


def P(s=""):
    print(s)


def occ_a_impl(ts, fs):
    """逐字复刻 _xva_p01_stall.py L154-196（interior 用 C 定义）。"""
    n = len(ts)
    span = ts[-1] - ts[0]
    trans = [(fs[i], ts[i]) for i in range(1, n) if fs[i] != fs[i - 1]]
    segs = []
    if trans:
        head = trans[0][1] - ts[0]
        if head > T:
            segs.append(("head", head))
        for (fa, ta), (fb, tb) in zip(trans, trans[1:]):
            if tb - ta > T:                      # ← interior = C
                segs.append(("interior", tb - ta))
        tail = ts[-1] - trans[-1][1]
        if tail > T:
            segs.append(("tail", tail))
    else:
        if span > T:
            segs.append(("head", span))
    return segs, span, len(trans)


def occ_b(ts, fs):
    """全段改「首见→末见」（B 定义），段分类与 occ_a 对齐以便逐段比对。"""
    n = len(ts)
    span = ts[-1] - ts[0]
    if n < 2:
        return [], span, 0
    segs = []
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


# ---- 全量枚举：所有含 measure_w*.json 的趟目录 ----
trips = []
for name in sorted(os.listdir(BASE)):
    d = os.path.join(BASE, name)
    if not os.path.isdir(d):
        continue
    wins = sorted(int(f[9:-5]) for f in os.listdir(d)
                  if f.startswith("measure_w") and f.endswith(".json"))
    if wins:
        trips.append((name, wins))

rows = []
skipped = []
P("=" * 118)
P("%-18s %2s %3s %9s %10s %10s %10s %9s %10s  %s"
  % ("trip", "w", "n", "span_s", "verdict", "occ_a%", "occ_B%", "diff_pp", "rel%", "A段型"))
P("=" * 118)
for trip, wins in trips:
    for w in wins:
        path = os.path.join(BASE, trip, "measure_w%d.json" % w)
        try:
            with open(path, encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception as e:
            skipped.append((trip, w, "read_error:%s" % type(e).__name__))
            continue
        s = d.get("samples") or {}
        ts, fs = s.get("t"), s.get("f")
        if not ts or not fs or len(ts) < 2:
            skipped.append((trip, w, "empty_or_short(n=%s)" % (len(ts) if ts else 0)))
            P("%-18s %2d %3s %9s %10s  (跳过: %s)"
              % (trip, w, len(ts) if ts else 0, "-",
                 str(d.get("verdict"))[:10], skipped[-1][2]))
            continue
        sa, span, ntr = occ_a_impl(ts, fs)
        sb, _, _ = occ_b(ts, fs)
        pa, pb = pct(sa, span), pct(sb, span)
        kinds = {}
        for k, v in sa:
            kinds[k] = kinds.get(k, 0) + 1
        rel = (pa - pb) / pb * 100.0 if pb > 0 else float("inf")
        P("%-18s %2d %3d %9.3f %10s %10.4f %10.4f %+9.4f %9s  %s"
          % (trip, w, len(ts), span, str(d.get("verdict"))[:10], pa, pb, pa - pb,
             ("%.1f" % rel) if pb > 0 else "inf",
             ",".join("%s×%d" % (k, v) for k, v in sorted(kinds.items())) or "-"))
        rows.append(dict(trip=trip, w=w, n=len(ts), span=span, pa=pa, pb=pb,
                         d=pa - pb, ntr=ntr,
                         kinds=kinds, verdict=d.get("verdict")))

P()
P("=" * 118)
P("## 汇总")
P("   趟数=%d  窗数=%d  （§514 只覆盖 34 窗/12 趟，本普查为全量）"
  % (len(trips), len(rows)))
if rows:
    pa_mean = sum(r["pa"] for r in rows) / len(rows)
    pb_mean = sum(r["pb"] for r in rows) / len(rows)
    P("   全部窗算术均值：occ_a=%.4f%%  occ_B=%.4f%%  差 %+.4f pp"
      % (pa_mean, pb_mean, pa_mean - pb_mean))

    eps = 1e-9
    same = [r for r in rows if abs(r["d"]) <= eps]
    diff = [r for r in rows if abs(r["d"]) > eps]
    P("   完全相同窗=%d  有差异窗=%d  差异占比=%.1f%%"
      % (len(same), len(diff), 100.0 * len(diff) / len(rows)))

    # 变化分级（按 pp）
    grades = [(0.0, 0.1, "≤0.1pp"), (0.1, 1.0, "0.1–1pp"),
              (1.0, 5.0, "1–5pp"), (5.0, 15.0, "5–15pp"), (15.0, 1e9, ">15pp")]
    P()
    P("   ## 变化分级（|Δpp|）")
    for lo, hi, label in grades:
        sel = [r for r in diff if lo < abs(r["d"]) <= hi]
        P("     %-10s %3d 窗%s" % (label, len(sel),
                                  "：" + ", ".join("%s w%d" % (r["trip"], r["w"]) for r in sel)
                                  if 0 < len(sel) <= 12 else ""))

    # 结论翻转探测：occ_a >=50% 而 occ_B <50%（或反之）= 定性句变化
    flips = [r for r in rows if (r["pa"] >= 50.0) != (r["pb"] >= 50.0)]
    P()
    P("   ## 定性翻转（跨 50%% 线：occ_a 与 occ_B 分别落在两侧）＝ %d 窗" % len(flips))
    for r in flips:
        P("     %-18s w%d  occ_a=%.4f%% → occ_B=%.4f%%  (%+.4fpp)"
          % (r["trip"], r["w"], r["pa"], r["pb"], r["d"]))
    if not flips:
        P("     （无）")

    # 最大差排序
    P()
    P("   ## |Δpp| 最大 10 窗")
    for r in sorted(rows, key=lambda x: -abs(x["d"]))[:10]:
        P("     %-18s w%d  occ_a=%9.4f%%  occ_B=%9.4f%%  Δ=%+9.4fpp  span=%.3fs  A段=%s"
          % (r["trip"], r["w"], r["pa"], r["pb"], r["d"], r["span"],
             ",".join("%s×%d" % (k, v) for k, v in sorted(r["kinds"].items())) or "-"))

    # 逐趟聚合（供台账引用）
    P()
    P("   ## 逐趟聚合（窗均）")
    agg = {}
    for r in rows:
        a = agg.setdefault(r["trip"], [0, 0.0, 0.0, 0.0])
        a[0] += 1
        a[1] += r["pa"]
        a[2] += r["pb"]
        a[3] = max(a[3], abs(r["d"]))
    P("     %-18s %3s %11s %11s %11s %11s"
      % ("trip", "n", "occ_a均", "occ_B均", "Δpp均", "max|Δ|"))
    for trip in sorted(agg):
        n, sa_, sb_, mx = agg[trip]
        P("     %-18s %3d %10.4f%% %10.4f%% %+10.4f %10.4f"
          % (trip, n, sa_ / n, sb_ / n, (sa_ - sb_) / n, mx))

P()
P("   跳过的窗=%d" % len(skipped))
for t, w, why in skipped:
    P("     %-18s w%d  %s" % (t, w, why))
P()
P("   ## 判读边界")
P("   - occ_a 实装口径（C 型 interior + B 型 head/tail）为既有台帐数字来源，本普查不改任何文件。")
P("   - 本表只回答「若改采 B 口径，历史数字变动面有多大」，不构成对 occ_a 的否决（D-12② 待裁）。")
P("   - 与等待轨迹侧（h8_wait_trace，B 口径钉死）跨线比较前须先统一口径。")
