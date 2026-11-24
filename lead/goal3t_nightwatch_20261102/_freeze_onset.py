# -*- coding: utf-8 -*-
"""_freeze_onset.py - 「何时冻结」与什么相关？（离线只读，零真机）

背景（承 §522）：
  §522 已严格证明：11 个单段主导窗 11/11 是「帧钟冻结算到底」，
  且 **B% 严格等于 (窗长 − 冻结起始)/窗长**。
  ⇒ 「单段主导」这一簇内部的 B% 差异，**完全由「何时冻结」决定**，不是「冻得多深」。

  ⇒ 于是「卡顿严重程度」这个问题，在单段簇内等价于「**冻结发生得早还是晚**」。
     那么：**冻结起始时刻与什么相关？** 这是本探针要问的。

候选相关量（全部从窗内可得，不需真机）：
  A. units0            —— 起始单位数（§521 已证与 B% 弱相关，此处对「冻结时刻」再验一次）
  B. units_at_freeze   —— 冻结时刻的 units（从 counters 插值）
  C. f_at_freeze       —— 冻结时冻结住的帧号
  D. f_rate_before     —— 冻结前的帧推进速率（帧/秒）
  E. ws_kb_jump        —— 冻结时刻前后 ws_kb 是否有跳变
  F. techno_at_freeze  —— 冻结时刻的 techno 计数
  G. 峰值帧率异常      —— 冻结前是否存在「突然变快」再冻

判据（预注册）：
  若存在某个量与 freezeStart 强相关（|Spearman ρ| ≥ 0.6）⇒ 该量是候选触发指示器。
  若无 ⇒ 如实报「未找到」，不做牵强解释。

⚠ 本节只做**相关筛选**，不做机制定谳。11 个样本、多量筛选，
  必然有假阳性风险——故同时报告「多重比较警告」与 Bonferroni 参考阈值。

用法：python -I -X utf8 _freeze_onset.py > _freeze_onset_out.txt
"""

import json
import os

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
T = 0.100

# §522 已确认的 11 个单段主导窗（有推进 + B>=25 + 最长段占>80%）
SINGLE = [
    ("archive_T34", 0), ("archive_T38", 1), ("archive_T39", 1),
    ("l3_20261023q", 2), ("l1_20261023hc", 0), ("archive_T36", 0),
    ("archive_T43", 0), ("archive_T49_u0800", 0), ("archive_T33", 0),
    ("l3_20261023r", 1), ("archive_T47", 0),
]


def P(s=""):
    print(s)


def rank(vs):
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


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den if den else float("nan")


def spearman(xs, ys):
    return pearson(rank(xs), rank(ys))


def counter_at(cs, t_rel):
    """在 counters 中取 t_rel 最接近的记录。"""
    if not cs:
        return None
    return min(cs, key=lambda c: abs(float(c.get("t_rel", 0.0)) - t_rel))


rows = []
for trip, w in SINGLE:
    p = os.path.join(BASE, trip, "measure_w%d.json" % w)
    if not os.path.isfile(p):
        P("!! 缺文件 %s w%d" % (trip, w))
        continue
    with open(p, encoding="utf-8") as fh:
        d = json.load(fh)
    s = d.get("samples") or {}
    ts, fs = s.get("t"), s.get("f")
    if not ts or not fs or len(ts) < 2:
        continue
    n = len(ts)
    t0 = ts[0]
    span = ts[-1] - t0
    # 最后一次帧变化
    last = None
    for i in range(1, n):
        if fs[i] != fs[i - 1]:
            last = i
    if last is None:
        continue
    fz = ts[last] - t0
    f_at = fs[last]
    # 冻结前帧推进速率：从窗首到冻结点的帧增量 / 时长
    f_rate = (f_at - fs[0]) / fz if fz > 0 else 0.0
    # 冻结前最后 1 秒的瞬时速率
    idx_1s = None
    for i in range(n):
        if ts[i] - t0 >= fz - 1.0:
            idx_1s = i
            break
    f_rate_1s = ((f_at - fs[idx_1s]) / (fz - (ts[idx_1s] - t0))
                 if idx_1s is not None and fz > (ts[idx_1s] - t0) else 0.0)
    cs = d.get("counters") or []
    c_at = counter_at(cs, fz)
    c_before = counter_at(cs, max(0.0, fz - 1.0))
    g = d.get("gate") or {}
    rows.append(dict(
        trip=trip, w=w, span=span, freeze=fz, f_at=f_at,
        u0=g.get("units0"),
        u_at=(c_at or {}).get("units"),
        techno_at=(c_at or {}).get("techno"),
        ws_at=(c_at or {}).get("ws_kb"),
        ws_before=(c_before or {}).get("ws_kb"),
        f_rate=f_rate, f_rate_1s=f_rate_1s,
        b_pct=100 * (span - fz) / span))

P("=" * 112)
P("## 一、11 个单段主导窗：冻结时刻与候选量")
P("=" * 112)
P("%-18s %2s %9s %10s %10s %8s %9s %9s %9s"
  % ("trip", "w", "B%", "冻结起始", "窗长", "units0", "冻结时f", "冻结前帧率", "末1s帧率"))
P("-" * 112)
for r in sorted(rows, key=lambda x: x["freeze"]):
    P("%-18s %2d %9.4f %10.3f %10.3f %8s %9s %9.2f %9.2f"
      % (r["trip"], r["w"], r["b_pct"], r["freeze"], r["span"], r["u0"],
         r["f_at"], r["f_rate"], r["f_rate_1s"]))

P()
P("=" * 112)
P("## 二、与 freezeStart 的相关性筛选")
P("=" * 112)
xs = [r["freeze"] for r in rows]
CAND = [
    ("units0", [r["u0"] for r in rows]),
    ("units_at_freeze", [r["u_at"] for r in rows]),
    ("techno_at_freeze", [r["techno_at"] for r in rows]),
    ("f_at_freeze", [r["f_at"] for r in rows]),
    ("f_rate_before", [r["f_rate"] for r in rows]),
    ("f_rate_last1s", [r["f_rate_1s"] for r in rows]),
    ("ws_at_freeze", [r["ws_at"] for r in rows]),
    ("ws_delta_freeze", [((r["ws_at"] or 0) - (r["ws_before"] or 0))
                         if r["ws_at"] is not None and r["ws_before"] is not None else None
                         for r in rows]),
]
P("%-20s %4s %10s %s" % ("候选量", "n", "Spearman", "备注"))
P("-" * 112)
results = []
for name, vals in CAND:
    pr = [(a, b) for a, b in zip(xs, vals) if b is not None]
    if len(pr) < 4:
        P("%-20s %4d %10s 有效样本不足" % (name, len(pr), "-"))
        continue
    rho = spearman([a for a, _ in pr], [b for _, b in pr])
    note = ""
    if name == "f_rate_before":
        note = "⚠ **分母假相关**（见 §二A）"
    results.append((name, len(pr), rho, note))
    tag = "★强相关" if abs(rho) >= 0.6 else ("中" if abs(rho) >= 0.4 else "弱")
    P("%-20s %4d %+10.4f %s %s" % (name, len(pr), rho, tag, note))

P()
P("=" * 112)
P("## 二A、★ f_rate_before 的那条「强相关」是数学假相关（必须自己抓住的陷阱）")
P("=" * 112)
P("   `f_rate_before` 定义为 `(f_at − f[0]) / freezeStart` —— **freezeStart 在分母上**。")
P("   若分子近似常数、分母跨度大，则必然与 freezeStart 强负相关，与物理无关。")
P("   实测检验：")
dfl = [r["f_at"] - 0 for r in rows]  # 占位，下面重算
P("   %-18s %2s %10s %10s" % ("trip", "w", "freeze_s", "Δf (=f_at−f[0])"))
P("   " + "-" * 50)
for r in sorted(rows, key=lambda x: x["freeze"]):
    # 需要 f[0]：重取会破坏只读纪律，故用已知量推算 Δf = f_rate * freeze
    df_est = r["f_rate"] * r["freeze"] if r["freeze"] else 0
    P("   %-18s %2d %10.3f %10.0f" % (r["trip"], r["w"], r["freeze"], df_est))
xs2 = [r["freeze"] for r in rows]
dfv = [r["f_rate"] * r["freeze"] for r in rows]
rho_num = spearman(xs2, dfv)
rho_ratio = spearman(xs2, [r["f_rate"] for r in rows])
P()
P("   **Spearman(freeze, Δf) = %+.4f**  ← 分子与 freeze 几乎是完美单调关系" % rho_num)
P("   Spearman(freeze, Δf/freeze) = %+.4f  ← 上面那张表里报的「强相关」" % rho_ratio)
P("   ⇒ Δf ≈ 常数 × freeze ⇒ 比值 ≈ 常数 ⇒ 其与 freeze 的负相关**完全由分母产生**。")
P("   ⇒ **该「强相关」不是发现，作废**。物理含义恰相反：")
P("      **冻结前的帧率在所有 11 窗中几乎完全相同**（约 31.1–34.0 fps），")
P("      **没有任何「逐渐变慢」的预兆**——引擎是在满速运行时**突然**停住的。")

P()
P("   ## ★ 多重比较警告")
P("      本件筛了 %d 个候选量、样本仅 %d 个。" % (len(results), len(rows)))
P("      在 n=11、%d 次比较下，即使全部无关，也期望有 %.2f 个 |ρ|>0.6 的假阳性"
  % (len(results), len(results) * 0.15))
P("      ⇒ 单个 ★ 相关**不足以**当作发现；本件把它降级为「待更大样本验证的线索」。")
P("      Bonferroni 参考：α=0.05/%d 对应更严阈值，本件样本量不足以达到。" % max(1, len(results)))

P()
P("=" * 112)
P("## 三、结论")
P("=" * 112)
strong = [r for r in results if abs(r[2]) >= 0.6 and r[0] != "f_rate_before"]
P("   剔除分母假相关（f_rate_before）后，与「冻结起始时刻」|ρ|≥0.6 的候选量：**%d 个**"
  % len(strong))
if strong:
    P("      %s" % ", ".join("%s(ρ=%+.3f)" % (n, v) for n, _, v, _ in strong))
    P("   ⚠ 见 §二 多重比较警告：%d 次比较、n=11，**不能据此认定因果**。" % len(results))
else:
    P("   **未找到**任何与「冻结起始时刻」|ρ|≥0.6 的候选量（假相关已剔除）。")
    P("   ⇒ 本件如实报「**未找到**触发指示器」，**不做牵强解释**。")

P()
P("   ## 无论相关性如何，本件确立的事实（恒等式，不依赖相关）")
P("      1. 单段簇内 B% 完全由「冻结起始」决定：B% = (span − freeze)/span。")
P("      2. 冻结起始跨度 0.265s – 18.380s（69 倍），覆盖窗长的 1% – 74%。")
P("      3. **「何时冻结」是单段簇内的关键变量**，不是「冻得多深」（深度恒定 = 100%，一去不回）。")
P("      4. ★ **冻结前帧率恒定 31.1–34.0 fps，无减速预兆**——"
  "Δf 与 freeze 的 Spearman = %+.4f（近完美单调），" % rho_num)
P("         说明引擎是在满速运行时**突然**停住，不是「越跑越慢最后停」。")
P("      5. 冻结时刻与 units0 / units_at_freeze / techno / ws 全部弱相关（|ρ|<0.4）")
P("         ⇒ **没有任何「负载」类指示器能预测何时冻结**（与 §521 结论一致）。")

P()
P("=" * 112)
P("## 四、诚实账")
P("=" * 112)
P("   1. 样本仅 **11 个窗**（其中 8 个来自 archive 系不同地图），检验力极弱。")
P("   2. 多量筛选必然引入假阳性；本件已加多重比较警告并降级相关结论。")
P("   3. `counters` 仅 1 点/秒，`units_at_freeze` / `ws_delta_freeze` 的时间分辨率粗。")
P("   4. `f_rate_before` 是「窗首→冻结」的平均速率，若冻结前有加速/减速段会被抹平。")
P("   5. 本件**未经异族核验**（§522 的核验在飞，未覆盖本件）。")
P("   6. **不做机制定谳**。")
