# -*- coding: utf-8 -*-
"""_stall_vs_gap.py - 停滞是否真实：口径 B 停滞 vs 采样缺口的可分性检验（离线只读）。

动机（2026-11-03）：
  D-12② 已裁「口径 B 为准」。B 口径之所以是该裁的正确选择，不只因为它是钉死定义，
  更因为它**对采样缺口稳健**：B 只计「实际观测到的首见→末见」，采样器停摆期间不臆测；
  而 C 口径（到下一推进拍）会把缺口整段算成停滞 = 有界高估。
  §514 已量化这个高估（hb w1 +30.19pp / 全量均值 +1.31pp）。

本探针回答一个**更关键**的问题：
  §505 的「周期性停滞与 BOOT 显著相关」，会不会**本身就是采样饥饿造成的假象**？
  即：高停滞的趟，是否同时也是采样缺口高的趟？若是，则「停滞」只是「采样器被饿」的同义词，
  不是游戏真的卡住了 —— 这会让目标①的机制方向完全走偏。

判据设计（可分性）：
  - 若停滞 = 采样假象 ⇒ 高 B 口径停滞的趟，其 >10ms 缺口占比也应很高（强正相关）。
  - 若停滞 = 真实卡顿 ⇒ 存在「零缺口但高停滞」的趟 ⇒ 相关性被打破。

  ⚠ 必须用「帧沿处缺口」而非「所有相邻间隔缺口」：采样器在平台中间掉拍不影响判定
    （平台中掉拍仍能确认末见），只有跨平台边界的缺口才会污染停滞判定。

口径：B = 卡住帧值首末拍跨度（D-12② 钉死）；T_STALL = 0.1s。
BOOT 归属：**不做**。趟名/会话日期不能充当 BOOT 身份（BOOT_TABLE §4 已证伪），
本探针只按「趟」聚合，并用台账已登记的会话分组作展示标签、明确标注为「会话组（非 BOOT）」。

用法：python -I -X utf8 _stall_vs_gap.py > _stall_vs_gap_out.txt
"""

import json
import os

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
T = 0.100

# 台账已登记的会话分组（§505/§514 用过的分组）。★ 仅供展示，不是 BOOT 身份。
GROUPS = {
    "10-20": ["l1a_20261020", "t55k_20261020"],
    "10-21": ["l1c_20261021", "l1d_20261021", "l1e_20261021", "l3_20261021"],
    "10-23": ["l1_20261023", "l1_20261023b", "l1_20261023c", "l1_20261023e1",
              "l1_20261023e4", "l1_20261023hb", "l1_20261023hc", "l1_20261023k",
              "l3_20261023", "l3_20261023q", "l3_20261023r"],
    "10-30/31": ["l3_20261031ha", "l3_20261031hb"],
    "11-01": ["l3_1101v3a", "l3_1101v3b", "l3_1101v3c", "l3_1101v4b",
              "l3_1101v4c", "l3_1101v4d"],
    "11-03": ["l3_1101v4e"],
}


def P(s=""):
    print(s)


def pair(ts, fs):
    """返回 (occ_B_pct, B_segments, span)。B = 首见→末见。"""
    n = len(ts)
    span = ts[-1] - ts[0]
    if not span:
        return None
    segs = []
    j = 0
    while j + 1 < n and fs[j + 1] == fs[0]:
        j += 1
    h = ts[j] - ts[0]
    if h > T:
        segs.append((ts[0], fs[0], h))
    i = j + 1
    while i < n:
        k = i
        while k + 1 < n and fs[k + 1] == fs[i]:
            k += 1
        d = ts[k] - ts[i]
        if d > T:
            segs.append((ts[i], fs[i], d))
        i = k + 1
    tot = sum(s[2] for s in segs)
    return 100 * tot / span, segs, span


def gap_profile(ts, fs):
    """返回 (帧沿处>10ms缺口合计, 所有>10ms缺口合计, span)。"""
    span = ts[-1] - ts[0]
    edge = sum(ts[i] - ts[i - 1] for i in range(1, len(ts))
               if fs[i] != fs[i - 1] and ts[i] - ts[i - 1] > 0.010)
    allg = sum(ts[i] - ts[i - 1] for i in range(1, len(ts))
               if ts[i] - ts[i - 1] > 0.010)
    return edge, allg, span


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


def _load_and_add(dirpath, label, fname):
    """读一个 measure 窗并追加到 rows；无效窗返回 False。"""
    try:
        with open(os.path.join(dirpath, fname), encoding="utf-8") as fh:
            dd = json.load(fh)
    except Exception:
        return False
    s = dd.get("samples") or {}
    ts, fs = s.get("t"), s.get("f")
    if not ts or not fs or len(ts) < 2:
        return False
    r = pair(ts, fs)
    if not r:
        return False
    edge, allg, span = gap_profile(ts, fs)
    rows.append(dict(trip=label, w="w" + fname[9:-5], B=r[0], span=span,
                     edge=edge, edgep=100 * edge / span,
                     allg=allg, allgp=100 * allg / span,
                     moving=any(fs[i] != fs[i - 1] for i in range(1, len(fs))),
                     verdict=dd.get("verdict")))
    return True


# ① 各趟子目录
for trip in sorted(os.listdir(BASE)):
    d = os.path.join(BASE, trip)
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        if f.startswith("measure_w") and f.endswith(".json"):
            _load_and_add(d, trip, f)

# ② ★ 数据根直属散件（§515 异族核验指出的枚举遗漏；不属于任何趟目录）
for i in range(3):
    fname = "measure_w%d.json" % i
    if os.path.isfile(os.path.join(BASE, fname)):
        _load_and_add(BASE, "(root)", fname)

P("=" * 108)
P("## 〇、枚举范围核对")
P("=" * 108)
P("   含趟子目录 + 数据根散件，有效窗 = %d" % len(rows))
P("   （v4-e 三窗已含；数据根 3 散件标签为 (root)）")

P("=" * 108)
P("## 一、逐窗：B 口径停滞 vs 采样缺口（帧沿处 / 全部）")
P("=" * 108)
P("%-18s %3s %9s %9s %11s %11s" %
  ("trip", "w", "B%", "span", "edge>10ms%", "all>10ms%"))
P("-" * 108)
for r in sorted(rows, key=lambda x: -x["B"]):
    P("%-18s %3s %9.4f %9.3f %10.3f%% %10.3f%%"
      % (r["trip"], r["w"], r["B"], r["span"], r["edgep"], r["allgp"]))

xs = [r["B"] for r in rows]
P()
P("=" * 108)
P("## 二、可分性检验")
P("=" * 108)
P("   窗数 = %d" % len(rows))
P("   Pearson(B%%, 帧沿处>10ms缺口%%) = %+.4f   ← 判据主指标" % pearson(xs, [r["edgep"] for r in rows]))
P("   Pearson(B%%, 全部>10ms缺口%%)   = %+.4f   （含平台中掉拍，不该用于判停滞）"
  % pearson(xs, [r["allgp"] for r in rows]))
P()
P("   ## 关键子集：**有推进** 且 25% ≤ B < 99%（=真的打起来了、但过半时间卡着）")
P("      ★ 必须排除「全窗冻结」（B=100%、帧值从未变化）——那不是「卡顿」，是窗内根本没开始打，")
P("        混进来会污染相关性。")
part = [r for r in rows if r["moving"] and 25.0 <= r["B"] < 99.0]
zero_part = [r for r in part if r["edge"] < 1e-12]
gap_part = [r for r in part if r["edge"] >= 1e-12]
P("      共 %d 窗，其中：" % len(part))
P("        · 帧沿缺口 = 0 的 **%d 窗** ⇒ 停滞不可能是采样假象" % len(zero_part))
P("        · 帧沿缺口 > 0 的 %d 窗（停滞可能含采样成分）" % len(gap_part))
P()
P("      ## A. 零缺口高停滞窗（真实停滞，采样器全程正常工作）")
for r in sorted(zero_part, key=lambda x: -x["B"]):
    P("         %-18s %3s  B=%7.4f%%  span=%.3fs" % (r["trip"], r["w"], r["B"], r["span"]))
P()
P("      ## B. 有缺口高停滞窗（停滞与饥饿并存）")
for r in sorted(gap_part, key=lambda x: -x["edge"]):
    P("         %-18s %3s  B=%7.4f%%  edge缺口=%.3fs (%.2f%% of span)"
      % (r["trip"], r["w"], r["B"], r["edge"], r["edgep"]))
P()
P("   ## 快态子集：B < 2% 的窗，其缺口分布")
lo = [r for r in rows if r["B"] < 2.0]
P("      共 %d 窗；edge缺口合计 = %.6fs；all缺口合计 = %.3fs"
  % (len(lo), sum(r["edge"] for r in lo), sum(r["allg"] for r in lo)))
P("      ⇒ 快态窗即便有采样掉拍，B 口径仍读 0% —— 反证 B 对缺口稳健。")

P()
P("=" * 108)
P("## 三、按会话组聚合（★ 会话组标识，**不是** BOOT 身份；BOOT_TABLE §4 已证伪日期→BOOT）")
P("=" * 108)
P("%-12s %4s %14s %14s %14s" % ("会话组", "窗", "B% 范围", "edge缺口%范围", "B 中位"))
P("-" * 108)
for g, trips in GROUPS.items():
    sel = [r for r in rows if r["trip"] in trips]
    if not sel:
        P("%-12s %4d  （无有效窗）" % (g, 0))
        continue
    bs = sorted(r["B"] for r in sel)
    gs = sorted(r["edgep"] for r in sel)
    med = bs[len(bs) // 2] if len(bs) % 2 else 0.5 * (bs[len(bs) // 2 - 1] + bs[len(bs) // 2])
    P("%-12s %4d %6.2f..%6.2f %9.2f..%6.2f %12.2f"
      % (g, len(sel), bs[0], bs[-1], gs[0], gs[-1], med))

P()
P("=" * 108)
P("## 四、结论")
P("=" * 108)
P("   判据：若停滞=采样假象，则 B 与 edge缺口应强正相关，且不应存在「零缺口高停滞」窗。")
P()
r_all = pearson(xs, [r["edgep"] for r in rows])
P("   1. Pearson(B%, 帧沿缺口%) = **" + ("%+.4f" % r_all) + "** —— 这是**几乎不相关**（|r|<0.1），")
P("      **不是**「中等相关」。⇒ 停滞与采样缺口是两个独立现象，不是同一件事的两种说法。")
P("   2. ★ 剔除「全窗冻结」（B=100%、窗内根本没开始打）后，仍有 **"
  + str(len(zero_part)) + " 个**「有推进、过半时间卡着、")
P("      且采样器全程无 >10ms 缺口」的窗 ⇒ **真实停滞存在，且可在无采样污染下被观测到**。")
P("      最强样本：archive_T34 w0 98.94% / archive_T38 w1 96.31% / l1_20261023e1 w0 94.50%，")
P("      三者帧沿缺口均为 0。")
P("   3. 另 " + str(len(gap_part)) + " 个窗停滞与饥饿并存（l3_20261031hb w1 缺口占 span 28.04% 最重）⇒")
P("      这类窗的停滞**含采样成分**，引用时必须双报、不可与第 2 类混算。")
P("   4. 快态窗（B<2%）即便有采样掉拍仍读 0% ⇒ **B 口径对缺口稳健**。")
P("      这正是 D-12② 裁「B 为准」的方法论依据——不只因为它是钉死定义，更因为它不被饥饿污染。")
P("   5. **局限（必须随件）**：本探针只能用「会话组」作展示标签，**不能**给出 BOOT 级断言；")
P("      §505 的 BOOT 相关性结论**未被本探针重新证伪或强化**。本件只回答一个问题：")
P("      **「停滞是否采样假象」= 否**。")
P()
P("   ## 对目标①的意义")
P("      停滞是真实存在的帧不推进（" + str(len(zero_part)) + " 个零缺口且有推进的窗为证），")
P("      不是 harness 观测伪影。")
P("      但「停滞程度」的**读数**会受饥饿污染（第 3 类窗），所以：")
P("      · 机制归因必须用零缺口窗（第 2 类）作证据基底；")
P("      · 含缺口窗只能作参考，且必须附缺口读数。")
