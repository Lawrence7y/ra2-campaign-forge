# -*- coding: utf-8 -*-
"""_confound_probe.py - 「结构类型与会话共线」能否被现有数据解开？（离线只读）

背景（§519 结的死结）：
  「多次短卡」形态 100% 来自 10-21 的 4 个趟，「单段主导」来自 13 个互不相同的趟，
  两簇不共享任何趟 ⇒ 结构类型与「趟/会话」完全共线，无法区分
  (a) 两种卡顿机制； (b) 同一机制在同一会话环境下的两种表现。

本探针不是要「硬解」这个死结（那需要真机同 BOOT 对照），而是做一个**可判定的侧面检验**：

  如果 10-21 那 4 趟除了「多次短卡」之外，在**不相关指标**上也系统性异于其它趟，
  那么「共线」更可能反映**会话级环境差异**，而不是「卡顿机制不同」。
  反之，若它们只在停滞形态上异、其它指标与别趟无异，
  则「机制不同」的解释权重上升。

检验指标（都与停滞形态**定义上独立**）：
  1. fps_avg / fps_p50          —— 帧率本身
  2. frame_ms_p50 / p90         —— 单帧耗时分布
  3. units0                     —— 参战规模
  4. hz_effective               —— 采样率
  5. tick_miss                  —— 逻辑帧丢失计数
  6. span_s / settle_s          —— 窗长参数（协议量，应恒定）
  7. B%(T=0.2)                  —— **不同于分型指标**：高阈值下的停滞占比
     （若 10-21 在 T=0.2 下 B% 也显著低，说明它的停滞确实是「浅而密」，
       与「深而少」的单段型是**量级不同的现象**）

判据（预注册，先写后跑）：
  - 若 10-21 组在 ≥3 个独立指标上与其它组显著分离 ⇒ 「会话环境差异」解释权重大
  - 若仅 1-2 个（且都属帧率族，可能只是同一现象的不同投影）⇒ 证据不足，保持 UNDECIDABLE
  - 显著分离的定义：两组的均值差 > 1.5 倍组内标准差（简易效应量），或范围完全不重叠

用法：python -I -X utf8 _confound_probe.py > _confound_probe_out.txt
"""

import json
import os
import statistics

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
T = 0.100
T_HI = 0.200

# 10-21 的 4 趟（多次型簇的全部来源）
GROUP_MULTI = {"l1c_20261021", "l1d_20261021", "l1e_20261021", "l3_20261021"}


def P(s=""):
    print(s)


def b_pct(ts, fs, thr):
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


def load_all():
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
        st = d.get("stats") or {}
        g = d.get("gate") or {}
        rows.append(dict(
            trip=label, w="w" + fname[9:-5],
            fps_avg=st.get("fps_avg"), fps_p50=st.get("fps_p50"),
            fm_p50=st.get("frame_ms_p50"), fm_p90=st.get("frame_ms_p90"),
            units0=g.get("units0"), hz=st.get("hz_effective"),
            tick_miss=st.get("tick_miss"), span=d.get("span_s"),
            settle=d.get("settle_s"),
            B10=b_pct(ts, fs, T), B20=b_pct(ts, fs, T_HI),
            edge=sum(ts[i] - ts[i - 1] for i in range(1, len(ts))
                     if fs[i] != fs[i - 1] and ts[i] - ts[i - 1] > 0.010),
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
    return rows


rows = load_all()

# 目标批：有推进 且 25<=B10<99 且 帧沿缺口=0（与 §519 同）
target = [r for r in rows if r["moving"] and 25 <= r["B10"] < 99 and r["edge"] < 1e-12]
gA = [r for r in target if r["trip"] not in GROUP_MULTI]
gB = [r for r in target if r["trip"] in GROUP_MULTI]

P("=" * 104)
P("## 〇、批次核对")
P("=" * 104)
P("   全量有效窗 = %d" % len(rows))
P("   目标批（有推进 + 25<=B<99 + 零帧沿缺口）= %d 窗" % len(target))
P("     其中 10-21 组（多次型来源）= %d 窗 / 趟=%d" % (len(gB), len({r["trip"] for r in gB})))
P("     其它趟组（单段主导来源）= %d 窗 / 趟=%d" % (len(gA), len({r["trip"] for r in gA})))


def summarize(vals):
    vals = [v for v in vals if isinstance(v, (int, float))]
    if not vals:
        return None
    return (len(vals), statistics.mean(vals),
            statistics.pstdev(vals) if len(vals) > 1 else 0.0,
            min(vals), max(vals))


P()
P("=" * 104)
P("## 一、两组在「与停滞形态定义上独立」的指标上是否分离")
P("=" * 104)
P("%-16s %-26s %-26s %8s %8s %s" %
  ("指标", "10-21 组 (n/均值±sd/范围)", "其它趟组 (n/均值±sd/范围)", "均值差", "效应量", "判定"))
P("-" * 104)

METRICS = [
    ("fps_avg", "fps_avg"),
    ("fps_p50", "fps_p50"),
    ("frame_ms_p50", "fm_p50"),
    ("frame_ms_p90", "fm_p90"),
    ("units0", "units0"),
    ("hz_effective", "hz"),
    ("tick_miss", "tick_miss"),
    ("span_s", "span"),
    ("settle_s", "settle"),
    ("B%(T=0.2)", "B20"),
]

verdicts = []
for label, key in METRICS:
    a = summarize([r[key] for r in gB])
    b = summarize([r[key] for r in gA])
    if not a or not b:
        P("%-16s %-26s %-26s %8s %8s %s" % (label, "（无数据）", "（无数据）", "-", "-", "跳过"))
        continue
    na, ma, sa, loa, hia = a
    nb, mb, sb, lob, hib = b
    d = ma - mb
    pooled = ((sa ** 2 + sb ** 2) / 2) ** 0.5
    eff = (d / pooled) if pooled > 0 else (float("inf") if d else 0.0)
    #
    sep = abs(eff) > 1.5
    # 范围完全不重叠也算强分离
    no_overlap = (hia < lob) or (hib < loa)
    tag = "★分离" if (sep or no_overlap) else ("弱" if abs(eff) > 0.8 else "无")
    verdicts.append((label, tag, eff, no_overlap))
    P("%-16s %-26s %-26s %+8.3f %8.2f %s"
      % (label,
         "%d/%.3f±%.3f/%.2f..%.2f" % (na, ma, sa, loa, hia),
         "%d/%.3f±%.3f/%.2f..%.2f" % (nb, mb, sb, lob, hib),
         d, eff, tag + ("(无重叠)" if no_overlap else "")))

P()
P("=" * 104)
P("## 二、预注册判据核对")
P("=" * 104)
sep_list = [v for v in verdicts if v[1].startswith("★")]
P("   预注册判据：")
P("     · ≥3 个独立指标显著分离 ⇒ 「会话环境差异」解释权重大")
P("     · 仅 1-2 个（且都属帧率族）⇒ 证据不足，保持 UNDECIDABLE")
P()
P("   实测显著分离指标 = %d 个：%s"
  % (len(sep_list), ", ".join(v[0] for v in sep_list) if sep_list else "（无）"))
P()

# 帧率族归类
FPS_FAMILY = {"fps_avg", "fps_p50", "frame_ms_p50", "frame_ms_p90"}
fps_sep = [v for v in sep_list if v[0] in FPS_FAMILY]
other_sep = [v for v in sep_list if v[0] not in FPS_FAMILY]
P("   其中：帧率族 %d 个 %s；非帧率族 %d 个 %s"
  % (len(fps_sep), [v[0] for v in fps_sep],
     len(other_sep), [v[0] for v in other_sep]))
P()

if len(sep_list) >= 3 and len(other_sep) >= 1:
    conclusion = ("**会话环境差异解释权重上升**：两组在 %d 个指标上分离，"
                  "其中 %d 个不属帧率族（%s）。"
                  % (len(sep_list), len(other_sep), ", ".join(v[0] for v in other_sep)))
elif len(sep_list) >= 3 and len(other_sep) == 0:
    conclusion = ("**分离集中在帧率族**：%d 个分离指标全属帧率/帧耗时族，"
                  "可能只是同一现象的不同投影，不足以独立支撑「会话环境差异」。"
                  % len(sep_list))
else:
    conclusion = ("**证据不足**：仅 %d 个指标分离 ⇒ 维持 §519 的死结判定（UNDECIDABLE）。"
                  % len(sep_list))
P("   ⇒ " + conclusion)

P()
P("=" * 104)
P("## 三、关键单指标细看：B%(T=0.2)")
P("=" * 104)
P("   理由：这是**唯一直接刻画停滞本身、但不等同于分型指标**的量。")
P("   若 10-21 组在 T=0.2 下 B% 也显著更低，则其停滞确实是「浅而密」，")
P("   与「深而少」的单段型是**量级不同的现象**——这本身就支持「两种形态」而非「同一形态的阈值切分」。")
P()
P("%-18s %3s %10s %10s" % ("trip", "w", "B%(T=.1)", "B%(T=.2)"))
P("-" * 46)
for r in sorted(target, key=lambda x: (-(x["trip"] in GROUP_MULTI), -x["B10"])):
    mark = " [10-21]" if r["trip"] in GROUP_MULTI else ""
    P("%-18s %3s %10.4f %10.4f%s" % (r["trip"], r["w"], r["B10"], r["B20"], mark))

P()
P("   ## 分组均值")
for name, g in (("10-21 组（多次型）", gB), ("其它趟组（单段主导）", gA)):
    if g:
        P("      %-22s B(T=.1) 均=%.4f%%   B(T=.2) 均=%.4f%%   降幅=%.4fpp"
          % (name,
             statistics.mean([x["B10"] for x in g]),
             statistics.mean([x["B20"] for x in g]),
             statistics.mean([x["B10"] - x["B20"] for x in g])))

P()
P("=" * 104)
P("## 四、诚实账")
P("=" * 104)
P("   1. 本探针仍**不能解开**死结：它只提高/降低「会话环境差异」解释的权重，")
P("      不能替代「同一 BOOT 内跨会话对照」这一唯一决定性实验。")
P("   2. 组样本极小（10-21 组 4 趟 / 11 窗），统计检验力弱；效应量是简易估计，非正式检验。")
P("   3. 各指标并非真正独立：fps / frame_ms / 停滞三者本就相关，")
P("      「≥3 个分离」在指标相关性下会**高估**独立证据数。故本件同时报「非帧率族分离数」。")
P("   4. `tick_miss` 等计数型指标存在大量 0 值，均值/标准差意义有限。")
P("   5. 本件纯描述，不含机制定谳。")
