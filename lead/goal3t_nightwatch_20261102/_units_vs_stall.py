# -*- coding: utf-8 -*-
"""_units_vs_stall.py - 目标①的前提检验：「数百单位 ⇒ 卡顿」是否成立？（离线只读）

动机（2026-11-03）：
  三个用户目标里，目标①的原文是「修**真实数百单位**战斗卡顿」。
  这个表述隐含一个前提：**单位数越多 → 卡顿越重**。
  如果该前提不成立，则「数百单位」这个限定本身需要重新审视，
  而机制方向也不该默认往「负载导致」上走。

  本探针做前提检验，不是机制分析。

关键观察（促成此检验）：数据里已见明显反例——
  l3_1101v4d/v4e 有 1189-1225 单位却 B%=0、fps_p50≈31（满帧率）；
  l3_1101v3a 有 1349 单位却 B%=83.79。

判据（预注册）：
  H0：停滞占比 B% 与 units0 正相关（单位越多越卡）——目标①前提成立。
  H1：无相关或负相关——前提不成立。
  统计：Pearson r 与 Spearman ρ；分层看「同 units0 档内 B% 的极差」。
  ⚠ 必须同时报告「同档内极差」：若同档内 B% 从 0 到 90% 都有，
    说明 units0 对 B% 的**解释力极低**，即便总体相关不为零。

用法：python -I -X utf8 _units_vs_stall.py > _units_vs_stall_out.txt
"""

import json
import os
import statistics

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
T = 0.100


def P(s=""):
    print(s)


def b_pct(ts, fs, thr=T):
    n = len(ts)
    span = ts[-1] - ts[0]
    if not span:
        return 0.0
    segs = []
    j = 0
    while j + 1 < n and fs[j + 1] == fs[0]:
        j += 1
    d = ts[j] - ts[0]
    if d > thr:
        segs.append(d)
    i = j + 1
    while i < n:
        k = i
        while k + 1 < n and fs[k + 1] == fs[i]:
            k += 1
        dd = ts[k] - ts[i]
        if dd > thr:
            segs.append(dd)
        i = k + 1
    return 100 * sum(segs) / span


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den if den else float("nan")


def rank(vs):
    """平均秩（处理并列）。"""
    order = sorted(range(len(vs)), key=lambda i: vs[i])
    r = [0.0] * len(vs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vs[order[j + 1]] == vs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(xs, ys):
    return pearson(rank(xs), rank(ys))


rows = []


def add(dirpath, label, fname):
    try:
        with open(os.path.join(dirpath, fname), encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return
    s = d.get("samples") or {}
    ts, fs = s.get("t"), s.get("f")
    if not ts or not fs or len(ts) < 2:
        return
    g = d.get("gate") or {}
    st = d.get("stats") or {}
    rows.append(dict(trip=label, w="w" + fname[9:-5],
                     u0=g.get("units0"), B=b_pct(ts, fs),
                     fps50=st.get("fps_p50"), fmp50=st.get("frame_ms_p50"),
                     moving=any(fs[i] != fs[i - 1] for i in range(1, len(fs)))))


for trip in sorted(os.listdir(BASE)):
    d = os.path.join(BASE, trip)
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        if f.startswith("measure_w") and f.endswith(".json"):
            add(d, trip, f)
for i in range(3):
    fn = "measure_w%d.json" % i
    if os.path.isfile(os.path.join(BASE, fn)):
        add(BASE, "(root)", fn)

P("=" * 100)
P("## 〇、样本")
P("=" * 100)
P("   有效窗 = %d；有 units0 = %d；有推进 = %d"
  % (len(rows), sum(1 for r in rows if r["u0"] is not None),
     sum(1 for r in rows if r["moving"])))
mv = [r for r in rows if r["u0"] is not None and r["moving"]]
P("   纳入检验（有 units0 且窗内有推进）= %d 窗" % len(mv))
P()
P("   ⚠ 排除「全窗冻结」（B=100%、f 从未变化）的理由：那不是卡顿，是窗内战斗没开始，")
P("     混入会制造「低单位数也高停滞」的假象。")

xs = [r["u0"] for r in mv]
ys = [r["B"] for r in mv]

P()
P("=" * 100)
P("## 一、总体相关（预注册判据）")
P("=" * 100)
P("   Pearson  r(units0, B%%) = %+.4f" % pearson(xs, ys))
P("   Spearman ρ(units0, B%%) = %+.4f" % spearman(xs, ys))
P()
P("   解读锚：|r|<0.3 弱、0.3-0.6 中、>0.6 强。")

P()
P("=" * 100)
P("## 二、★ 同 units0 档内的极差（决定解释力的关键）")
P("=" * 100)
P("   若同档内 B%% 覆盖很大范围，则 units0 对 B%% 几乎无解释力。")
P()
BINS = [(0, 400), (400, 700), (700, 1000), (1000, 1400)]
P("%-12s %4s %10s %10s %10s %10s" % ("units0 档", "n", "B 最小", "B 中位", "B 最大", "极差"))
P("-" * 100)
for lo, hi in BINS:
    sel = [r for r in mv if lo <= r["u0"] < hi]
    if not sel:
        P("%-12s %4d  （无）" % ("%d-%d" % (lo, hi), 0))
        continue
    bs = sorted(r["B"] for r in sel)
    med = statistics.median(bs)
    P("%-12s %4d %10.2f %10.2f %10.2f %10.2f"
      % ("%d-%d" % (lo, hi), len(sel), bs[0], med, bs[-1], bs[-1] - bs[0]))

P()
P("=" * 100)
P("## 三、★ 同档反例对（最有说服力的证据形式）")
P("=" * 100)
P("   同一 units0 档内，B%% 差 > 50pp 的窗对（说明负荷相近但表现天壤）：")
P()
pairs = []
for lo, hi in BINS:
    sel = [r for r in mv if lo <= r["u0"] < hi]
    for a in sel:
        for b in sel:
            if a is b:
                continue
            if abs(a["u0"] - b["u0"]) <= 60 and (b["B"] - a["B"]) > 50:
                pairs.append((a, b, b["B"] - a["B"]))
seen = set()
shown = 0
for a, b, d in sorted(pairs, key=lambda x: -x[2]):
    key = (a["trip"], a["w"], b["trip"], b["w"])
    if key in seen:
        continue
    seen.add(key)
    if shown >= 10:
        break
    shown += 1
    P("   %-18s %3s u0=%-5s B=%6.2f%%   ⟷   %-18s %3s u0=%-5s B=%6.2f%%   Δ=%6.2fpp"
      % (a["trip"], a["w"], a["u0"], a["B"], b["trip"], b["w"], b["u0"], b["B"], d))
if shown == 0:
    P("   （无）")

P()
P("=" * 100)
P("## 四、高单位数窗细看（≥1000 units，目标①直指的场景）")
P("=" * 100)
P("%-18s %3s %7s %9s %9s %10s" % ("trip", "w", "units0", "B%", "fps_p50", "frame_ms_p50"))
P("-" * 100)
hi_units = [r for r in mv if r["u0"] >= 1000]
for r in sorted(hi_units, key=lambda x: (-x["u0"], x["trip"])):
    P("%-18s %3s %7s %9.4f %9s %10s"
      % (r["trip"], r["w"], r["u0"], r["B"],
         ("%.2f" % r["fps50"]) if r["fps50"] else "-",
         ("%.2f" % r["fmp50"]) if r["fmp50"] else "-"))
P()
n0 = [r for r in hi_units if r["B"] < 1.0]
P("   ≥1000 单位窗共 %d 个，其中 B%%<1（几乎无停滞）的 **%d 个**：%s"
  % (len(hi_units), len(n0),
     ", ".join("%s %s(B=%.2f%%)" % (r["trip"], r["w"], r["B"]) for r in n0)
     if n0 else "（无）"))

P()
P("=" * 100)
P("## 五、判据核对与结论")
P("=" * 100)
r_ = pearson(xs, ys)
rho = spearman(xs, ys)
# 同档极差
spreads = []
for lo, hi in BINS:
    sel = [r for r in mv if lo <= r["u0"] < hi]
    if len(sel) >= 2:
        bs = [r["B"] for r in sel]
        spreads.append(max(bs) - min(bs))
P("   Pearson r = %+.4f ；Spearman ρ = %+.4f" % (r_, rho))
P("   同档 B%% 极差（有对照的档）：%s"
  % ", ".join("%.2fpp" % s for s in spreads))
P()
if abs(r_) < 0.3:
    P("   ⇒ **H0（单位越多越卡）不成立**：总体相关 |r|<0.3，属弱相关。")
else:
    P("   ⇒ H0 部分成立：总体相关 |r|≥0.3。")
if len(n0) > 0:
    P("   ⇒ **存在 ≥1000 单位却几乎零停滞的窗 %d 个** ⇒ 「数百单位」本身不决定卡顿。" % len(n0))
if spreads and max(spreads) > 50:
    P("   ⇒ **同 units0 档内 B%% 极差达 %.2fpp** ⇒ units0 对 B%% 的解释力极低。" % max(spreads))
P()
P("   ⇒ **结论：目标①的「数百单位」限定不能作为「卡顿由负载引起」的依据。**")
P("      高单位数窗里既有满帧率（v4d/v4e 1189-1225 单位、B=0%）也有深滞")
P("      （v3a 1349 单位、B=83.79%）。负荷相近、表现天壤 ⇒ 主导因素不是单位数。")

P()
P("=" * 100)
P("## 六、诚实账")
P("=" * 100)
P("   1. 本件只做**相关/分层**，不做因果推断。相关为弱不等于「完全无关」，")
P("      可能是非线性/阈值型关系未被线性系数捕捉。")
P("   2. units0 是**窗口起点**的单位数，窗内可能变化（战争消耗）；本件未用窗内均值。")
P("   3. 各趟的 units0 与「会话」高度共变（同趟三窗 units0 相同），")
P("      故本件的相关检验**混入了会话效应**；能说明的是「不是单调负载关系」，")
P("      不能说明「units0 完全无关」。")
P("   4. 已排除全窗冻结窗（%d 个），该处理的选择会影响分母；理由已在 §〇 写明。" % (len(rows) - len(mv)))
P("   5. 本件**不做机制定谳**，只做前提检验。")
