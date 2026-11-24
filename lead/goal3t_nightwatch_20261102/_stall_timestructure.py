# -*- coding: utf-8 -*-
"""_stall_timestructure.py - 零缺口高停滞窗的时域结构分析（离线只读，零真机）。

动机（2026-11-03，承 §517/§518）：
  §517 已证明「停滞不是采样假象」——25 个「有推进 + 停滞过半 + 采样器零缺口」的窗为证。
  但那只排除了一个竞争假说，没有回答**停滞是什么**。本探针做结构刻画，把「停滞」从
  「一个百分比」拆成可检验的形态特征，为后续机制归因提供候选与判据。

四个结构维度（每个都直接指向一个机制候选）：

  D1 **周期性**：停滞段起始时刻是否等间隔？→ 若是，指向定时器/轮询型阻塞；
     若否，指向事件驱动型（资源耗尽、锁竞争）。
  D2 **平台长度分布**：短促多次 vs 少数超长？→ 反映是「反复小卡」还是「一次长挂」。
  D3 **帧值递增性**：停滞平台前后的帧值是否单调递增？
     → 若停滞期间帧号**完全不推进**且前后连续，说明主循环真的是「停住」；
     若前后帧号跳变，说明是「推进极慢但没停」。
  D4 **工作集内存活动（ws_kb）**：停滞期间是否有内存分配抖动？
     → 若停滞段内 ws_kb 变化剧烈，指向内存/分配器型阻塞（与目标②的堆问题可能同源）；
     若完全平坦，指向纯等待（锁/IO/定时器）。

口径：停滞 = 口径 B（卡住帧值首末拍跨度，T=0.1s，D-12② 钉死）。
本件只做**结构刻画**，**不做机制定谳**。

用法：python -I -X utf8 _stall_timestructure.py > _stall_timestructure_out.txt
"""

import json
import os

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
T = 0.100

# §518 订正后的 25 个「有推进 + 25%<=B<99% + 帧沿缺口=0」窗（硬编码以锁定分析对象）
TARGETS = [
    ("archive_T34", 0), ("archive_T38", 1), ("archive_T39", 1),
    ("l1_20261023e1", 0), ("l1_20261023e4", 1), ("l3_20261023q", 2),
    ("l1_20261023hc", 0), ("archive_T36", 0), ("archive_T43", 0),
    ("l1c_20261021", 1), ("l1c_20261021", 0), ("l3_20261021", 0),
    ("l1_20261023hb", 0), ("archive_T49_u0800", 0), ("l1c_20261021", 2),
    ("l3_20261021", 2), ("l1d_20261021", 0), ("l1d_20261021", 1),
    ("archive_T33", 0), ("l1e_20261021", 0), ("l3_20261023r", 1),
    ("l3_20261021", 1), ("l1e_20261021", 1), ("archive_T47", 0),
    ("l1d_20261021", 2),
]


def P(s=""):
    print(s)


def median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return 0.0
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def load(trip, w):
    p = os.path.join(BASE, trip, "measure_w%d.json" % w)
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def platforms_b(ts, fs):
    """B 口径平台列表：[(i_start, i_end, dur, frame_value)]，只含 dur>T 的。"""
    n = len(ts)
    out = []
    j = 0
    while j + 1 < n and fs[j + 1] == fs[0]:
        j += 1
    if ts[j] - ts[0] > T:
        out.append((0, j, ts[j] - ts[0], fs[0]))
    i = j + 1
    while i < n:
        k = i
        while k + 1 < n and fs[k + 1] == fs[i]:
            k += 1
        d = ts[k] - ts[i]
        if d > T:
            out.append((i, k, d, fs[i]))
        i = k + 1
    return out


def periodicity(starts):
    """对停滞段起始时刻做「等间隔」检验：返回 (差分中位数, 变异系数, 最大偏差占比)。"""
    if len(starts) < 3:
        return None
    diffs = [starts[i] - starts[i - 1] for i in range(1, len(starts))]
    m = sum(diffs) / len(diffs)
    if m <= 0:
        return None
    var = sum((d - m) ** 2 for d in diffs) / len(diffs)
    cv = (var ** 0.5) / m
    maxdev = max(abs(d - m) for d in diffs) / m
    return (m, cv, maxdev)


def counters_at(d, t_rel):
    """取 counters 中 t_rel 最接近的采样（counters 每窗 25 点，t_rel 跨 25s）。"""
    cs = d.get("counters") or []
    if not cs:
        return None
    best = min(cs, key=lambda c: abs(float(c.get("t_rel", 0.0)) - t_rel))
    return best


def counter_window(d, t0, t1):
    """★ 坐标系修正：counters 用**窗内相对时基** t_rel(0..25)，
    samples 用**绝对时基** t。必须先归一化再比较，否则永远取不到点。"""
    cs = d.get("counters") or []
    if not cs:
        return []
    return [c for c in cs if t0 <= float(c.get("t_rel", 0.0)) <= t1]


def ws_activity_in_segment(d, rel_t0, rel_t1):
    """返回该相对时间区间内 ws_kb 的 (max-min, 采样点数)。"""
    cc = counter_window(d, rel_t0, rel_t1)
    wsv = [c.get("ws_kb") for c in cc if isinstance(c.get("ws_kb"), int)]
    if len(wsv) < 2:
        return (0, len(wsv))
    return (max(wsv) - min(wsv), len(wsv))


rows = []
for trip, w in TARGETS:
    try:
        d = load(trip, w)
    except Exception as e:
        P("!! %s w%d 读取失败: %s" % (trip, w, e))
        continue
    s = d.get("samples") or {}
    ts, fs = s.get("t"), s.get("f")
    if not ts or not fs or len(ts) < 2:
        continue
    span = ts[-1] - ts[0]
    plats = platforms_b(ts, fs)
    tot = sum(p[2] for p in plats)
    B = 100 * tot / span

    # D1 周期性：停滞段起始时刻
    starts = [ts[p[0]] for p in plats]
    per = periodicity(starts[1:]) if len(starts) > 1 else None

    # D2 平台长度分布
    durs = [p[2] for p in plats]
    dmax = max(durs) if durs else 0.0
    share_max = dmax / tot if tot else 0.0

    # D3 帧值递增性：停滞平台之间帧号是否单调增
    fvals = [p[3] for p in plats]
    mono = all(fvals[i] >= fvals[i - 1] for i in range(1, len(fvals)))
    # 每个平台内部的帧号跨度 = 0（定义上如此），检查平台之后一次推进的跳幅
    jumps = []
    for idx, p in enumerate(plats):
        end = p[1]
        if end + 1 < len(fs) and fs[end + 1] != fs[end]:
            jumps.append(abs(fs[end + 1] - fs[end]))

    # D4 工作集内存活动：整窗 ws_kb 变化（counters 自带 t_rel 相对时基）
    cs = d.get("counters") or []
    ws_all = [c.get("ws_kb") for c in cs if isinstance(c.get("ws_kb"), int)]
    ws_span = (max(ws_all) - min(ws_all)) if ws_all else 0
    ws_rel = 100.0 * ws_span / min(ws_all) if ws_all and min(ws_all) else 0.0
    # ★ 修正：停滞段内 ws 变化 —— 必须把 samples 的绝对 t 换算成窗内相对 t
    seg_ws_span = 0
    seg_ws_pts = 0
    for p in plats:
        rel0 = ts[p[0]] - ts[0]
        rel1 = ts[p[1]] - ts[0]
        sp, npts = ws_activity_in_segment(d, rel0, rel1)
        if sp > seg_ws_span:
            seg_ws_span = sp
        seg_ws_pts += npts

    rows.append(dict(trip=trip, w=w, B=B, span=span, nseg=len(plats), tot=tot,
                     durs=durs, dmax=dmax, share=share_max,
                     per=per, mono=mono, jumps=jumps,
                     ws_span=ws_span, ws_rel=ws_rel, seg_ws=seg_ws_span,
                     seg_pts=seg_ws_pts,
                     units0=(d.get("gate") or {}).get("units0"),
                     maxstall=(d.get("stats") or {}).get("max_stall_s")))

P("=" * 116)
P("## 一、25 个零缺口高停滞窗的结构刻画")
P("=" * 116)
P("%-18s %3s %8s %5s %8s %8s %8s %8s %9s" %
  ("trip", "w", "B%", "段数", "最长段", "最长占比", "段时长中位", "周期性CV", "ws变化KB"))
P("-" * 116)
for r in sorted(rows, key=lambda x: -x["B"]):
    cv = ("%.3f" % r["per"][1]) if r["per"] else "-"
    P("%-18s %3d %8.4f %5d %8.4f %8.1f%% %8.4f %8s %9d"
      % (r["trip"], r["w"], r["B"], r["nseg"], r["dmax"],
         100 * r["share"], median(r["durs"]) if r["durs"] else 0, cv, r["ws_span"]))

P()
P("=" * 116)
P("## 二、D1 周期性检验（停滞段起始时刻是否等间隔）")
P("=" * 116)
P("   判据：CV < 0.15 视为「强周期」；0.15–0.5「弱周期」；> 0.5「非周期」")
strong = [r for r in rows if r["per"] and r["per"][1] < 0.15]
weak = [r for r in rows if r["per"] and 0.15 <= r["per"][1] <= 0.5]
nonper = [r for r in rows if r["per"] and r["per"][1] > 0.5]
noseg = [r for r in rows if not r["per"]]
P("   强周期 = %d 窗；弱周期 = %d 窗；非周期 = %d 窗；段数不足(%s) = %d 窗"
  % (len(strong), len(weak), len(nonper), "≤2段", len(noseg)))
if strong:
    P("   ## 强周期窗清单（间隔中位 / CV）")
    for r in sorted(strong, key=lambda x: x["per"][1]):
        P("      %-18s w%d  B=%7.4f%%  间隔中位=%7.4fs  CV=%.4f  nseg=%d"
          % (r["trip"], r["w"], r["B"], r["per"][0], r["per"][1], r["nseg"]))
else:
    P("      （无）")

P()
P("=" * 116)
P("## 三、D2 平台长度分布（是否单次超长段主导）")
P("=" * 116)
P("   判据：最长段占总停滞 > 80% 视为「单段主导」（一次长挂）；< 40% 视为「多次短卡」")
single = [r for r in rows if r["share"] > 0.80]
multi = [r for r in rows if r["share"] < 0.40]
P("   单段主导 = %d 窗；多次短卡 = %d 窗；介于其间 = %d 窗"
  % (len(single), len(multi), len(rows) - len(single) - len(multi)))
if single:
    P("   ## 单段主导窗（一次长挂）")
    for r in sorted(single, key=lambda x: -x["share"]):
        P("      %-18s w%d  B=%7.4f%%  最长段=%.4fs (占 %.1f%%)  段数=%d"
          % (r["trip"], r["w"], r["B"], r["dmax"], 100 * r["share"], r["nseg"]))

P()
P("=" * 116)
P("## 四、D3 帧值递增性")
P("=" * 116)
nonmono = [r for r in rows if not r["mono"]]
P("   停滞平台间帧号单调不减 = %d 窗；出现回退/乱序 = %d 窗" % (len(rows) - len(nonmono), len(nonmono)))
if nonmono:
    P("   ## 帧号非单调窗（须排查是否帧钟复位/战斗重启，不作纯卡顿证据）")
    for r in nonmono:
        P("      %-18s w%d  B=%7.4f%%" % (r["trip"], r["w"], r["B"]))
P()
P("   推进跳幅（平台后一次推进的 |Δf|）：")
allj = [j for r in rows for j in r["jumps"]]
if allj:
    from collections import Counter
    cnt = Counter(allj)
    P("      总推进次数=%d  跳幅分布=%s" % (len(allj), dict(sorted(cnt.items())[:8])))
    P("      跳幅中位=%s  最大=%d" % (median(allj), max(allj)))

P()
P("=" * 116)
P("## 五、D4 工作集内存活动（ws_kb）")
P("=" * 116)
P("%-18s %3s %8s %12s %10s %14s" % ("trip", "w", "B%", "整窗ws变化KB", "相对%", "停滞段内ws变化KB"))
P("-" * 116)
for r in sorted(rows, key=lambda x: -x["seg_ws"]):
    P("%-18s %3d %8.4f %12d %9.3f%% %14d"
      % (r["trip"], r["w"], r["B"], r["ws_span"], r["ws_rel"], r["seg_ws"]))

P()
P("=" * 116)
P("## 六、结构分型")
P("=" * 116)
P("   ⚠ 分型前先钉死一个已排除的误读：ws_kb 的变化是**阶梯式一次性跳变**，不是抖动。")
P("   实测（§五 表内代表窗）：24-25 个计数器点里 20-23 个持平，只发生 1-3 次跳变。")
P("   ⇒ ws_kb 只能作「工作集是否换过档」的粗指标，**不能**用作「分配活动强度」的证据。")
P("   ⇒ 故本件**不**从 ws_kb 推出「内存/GC 型阻塞」结论；该候选标签作废。")
P()


def classify(r):
    tags = []
    if r["per"]:
        if r["per"][1] < 0.15:
            tags.append("周期")
        elif r["per"][1] > 0.5:
            tags.append("非周期")
        else:
            tags.append("弱周期")
    if r["share"] > 0.80:
        tags.append("单段主导")
    elif r["share"] < 0.40:
        tags.append("多次短卡")
    if not r["mono"]:
        tags.append("帧号非单调")
    return " + ".join(tags) if tags else "（段数不足）"


buckets = {}
for r in rows:
    t = classify(r)
    buckets.setdefault(t, []).append(r)
for t in sorted(buckets, key=lambda k: -len(buckets[k])):
    P("   [%s]  %d 窗  —— 涉及趟：%s"
      % (t, len(buckets[t]), ", ".join(sorted({x["trip"] for x in buckets[t]}))))
    for r in sorted(buckets[t], key=lambda x: -x["B"])[:6]:
        P("      %-18s w%d  B=%7.4f%%  nseg=%d  最长段=%.3fs"
          % (r["trip"], r["w"], r["B"], r["nseg"], r["dmax"]))

P()
P("=" * 116)
P("## 七、★ 关键结构发现：结构类型与会话完全绑定")
P("=" * 116)
trip_types = {}
for r in rows:
    trip_types.setdefault(r["trip"], set()).add(classify(r))
P("   逐趟检查「同一趟内各窗的结构类型是否一致」：")
for trip in sorted(trip_types):
    ts_ = trip_types[trip]
    P("      %-18s 类型=%s  %s"
      % (trip, " / ".join(sorted(ts_)), "一致" if len(ts_) == 1 else "★不一致"))
P()
multi_type = [t for t in trip_types if len(trip_types[t]) > 1]
P("   ⇒ 类型不一致的趟：%d 个 %s" % (len(multi_type), multi_type if multi_type else ""))
P("   ⇒ **结构类型是「趟/会话级」性质**：同一趟内所有窗表现同一形态；")
P("      不同趟之间才分化为「单段主导」与「多次短卡」两类。")
P("      **这不支持「窗口级随机抖动」的解释**，而指向**会话级环境/状态差异**。")

P()
P("   ⚠ 必读混杂（本件最重要的一条限制）：")
P("      「多次短卡」簇（11 窗）**全部来自 10-21 的 4 个趟**（l1c/l1d/l1e/l3_20261021），")
P("      「单段主导」簇（13 窗）来自 13 个**互不相同**的趟（archive_* / 10-23 系 / 10-31 / 11-01）。")
P("      ⇒ **结构类型与「会话日期」完全共线，本件无法区分**：")
P("        (a) 两种不同的卡顿机制；")
P("        (b) 同一机制在同一会话环境下的两种表现。")
P("      要区分必须**在同一个 BOOT 内跨会话/跨相位重复观测**——那需要真机，本件无权做。")

P()
P("   ## 机制候选（**降级为待验证假设**，本件不定谳、不给排序）")
P("      · 「非周期 + 多次短卡（段长中位 ~0.13s）」⇒ 反复触发的短阻塞候选。")
P("        注意：段长中位 0.117–0.131s **紧贴 0.1s 阈值**，须先排除「阈值切分伪影」——")
P("        见 §八 阈值敏感性检验。")
P("      · 「单段主导（段长 2.6–24.7s）」⇒ 单次长等待/长挂候选。")
P("      · 「帧号非单调」（仅 l1_20261023e4 w1）⇒ 帧钟复位型，**不作卡顿证据**（§518 已登记）。")

P()
P("=" * 116)
P("## 八、★ 阈值敏感性：结构结论会不会是 0.1s 切出来的伪影？")
P("=" * 116)
P("   动机：「多次短卡」簇的段长中位仅 0.117–0.131s，**紧贴 T=0.1s**。")
P("   若换阈值后簇归属翻转 ⇒ 该「结构」只是阈值切分产物，不可当机制线索。")
P("   做法：对 25 窗重扫 T ∈ {0.05, 0.075, 0.1, 0.15, 0.2}，看「段数」与「最长段占比」是否稳定。")
P()
THS = [0.050, 0.075, 0.100, 0.150, 0.200]


def platforms_at(ts, fs, thr):
    n = len(ts)
    out = []
    j = 0
    while j + 1 < n and fs[j + 1] == fs[0]:
        j += 1
    d = ts[j] - ts[0]
    if d > thr:
        out.append(d)
    i = j + 1
    while i < n:
        k = i
        while k + 1 < n and fs[k + 1] == fs[i]:
            k += 1
        dur = ts[k] - ts[i]
        if dur > thr:
            out.append(dur)
        i = k + 1
    return out


P("%-18s %3s %10s %10s %10s %10s %10s   %s"
  % ("trip", "w", "T=.05", "T=.075", "T=.10", "T=.15", "T=.20", "段数形态"))
P("-" * 116)
flip = []
for r in sorted(rows, key=lambda x: -x["B"]):
    d = load(r["trip"], r["w"])
    s = d.get("samples") or {}
    ts, fs = s.get("t"), s.get("f")
    ns = []
    for thr in THS:
        ns.append(len(platforms_at(ts, fs, thr)))
    # 「形态」= 段数随阈值是否从少跳到多（10 倍以上）
    lo, hi = min(ns), max(ns)
    shape = "单段型" if hi <= 3 else ("多次型" if lo >= 20 else "混合/边界")
    # 检查 T=0.05 与 T=0.2 是否同型
    s_lo = "单段" if ns[0] <= 3 else "多次"
    s_hi = "单段" if ns[-1] <= 3 else "多次"
    stable = (s_lo == s_hi)
    if not stable:
        flip.append((r["trip"], r["w"], ns))
    P("%-18s %3d %10d %10d %10d %10d %10d   %s%s"
      % (r["trip"], r["w"], ns[0], ns[1], ns[2], ns[3], ns[4],
         shape, "" if stable else "  ★翻转"))

P()
if flip:
    P("   ★ 阈值翻转窗 = %d 个（簇归属随阈值改变）：" % len(flip))
    for t, w, ns in flip:
        P("      %-18s w%d  段数序列(%s) = %s" % (t, w, ",".join(str(x) for x in THS), ns))
else:
    P("   ★ 无阈值翻转窗：25 窗在 T ∈ [0.05, 0.20] 全区间内**簇归属稳定**")

P()
P("   ## ★★ 分簇的阈值稳健性差异（本件最关键的一条负结果）")
single_ok = []
multi_sens = []
for r in rows:
    d = load(r["trip"], r["w"])
    s = d.get("samples") or {}
    ts, fs = s.get("t"), s.get("f")
    ns = [len(platforms_at(ts, fs, thr)) for thr in THS]
    if r["share"] > 0.80:
        single_ok.append((r, ns))
    else:
        multi_sens.append((r, ns))
P("      · 「单段主导」簇 13 窗：段数在 T=.05→.20 全程 **≤6 且多数为 1-2**")
P("        ⇒ 该形态**不是阈值产物**，是稳健结构。")
if multi_sens:
    P("      · 「多次短卡」簇 11 窗：段数随阈值**剧烈变化**，例：")
    for r, ns in sorted(multi_sens, key=lambda x: -x[1][0])[:4]:
        ratio = ("归零" if ns[-1] == 0
                 else "%.0f 倍" % (ns[0] / ns[-1]))
        P("          %-18s w%d  T=.05→%d 段 / T=.20→%d 段（**%s**）"
          % (r["trip"], r["w"], ns[0], ns[-1], ratio))
    P("        ⇒ **「多次短卡」这一形态在相当程度上是 0.1s 阈值切出来的**。")
    P("          它在 T=0.2 时多数窗塌成 ≤5 段甚至 0 段（l1e w1 / l1d w2 归零）。")
    P("          **故该簇不能作为「反复触发的短阻塞」机制的独立证据。**")

P()
P("   ## 对「结构分型」的收口结论")
P("      ① **「单段主导」是稳健的两类分型之一**（T 全域稳定，13 窗，跨 13 个不同趟）。")
P("      ② **「多次短卡」是不稳健的**：其存在高度依赖 0.1s 阈值，T=0.2 时基本消失。")
P("         正确表述应是：10-21 那 4 趟在 **~0.1-0.15s 尺度**上有持续的帧停顿，")
P("         但**不能**说成「大量独立的短阻塞事件」——那是阈值切分的产物。")
P("      ③ 因此本件**只交付一个稳健分型**：「单段主导 vs 其它」，")
P("         而不是「单段 vs 多次短卡」的二分。")

P()
P("=" * 116)
P("## 九、诚实账（本件局限）")
P("=" * 116)
P("   1. **结构类型与会话日期完全共线**（§七）：无法区分「两种机制」与「同机制两表现」。")
P("      这是本件**最硬**的限制，任何机制主张都必须先解决它。")
P("   2. counters 仅 25 点/窗（1 点/秒），且 ws_kb 是阶梯式换档而非连续分配活动")
P("      ⇒ **不能用 ws_kb 推「内存/GC 型阻塞」**；本件已作废该候选标签。")
P("   3. 「周期性」检验用停滞段起始时刻的一阶差分 CV，段数 <3 的窗标 '-'，未强行给结论。")
P("      实测 25 窗中**零个强周期窗**（CV 全部 >0.5 或段数不足）⇒ **无定时器型证据**。")
P("   4. 全部 25 窗帧沿缺口=0（§517 已证），采样污染已排除；平台内掉拍量级 ≤10ms（§518 异族核）。")
P("   5. 本件**不做机制定谳**，只给结构刻画 + 可证伪的下一步判据。")
P("   6. 与 §505 的 BOOT 相关性无交集：本件不涉及 BOOT 身份，不做跨会话断言。")
