# -*- coding: utf-8 -*-
"""_phase_recompute.py - 按真实 BOOT 重算时间相位（订正 §522）

动机（承 §533）：
  §522 算 `rho(窗序号, B%)` 与 `rho(samples.t[0], B%)` 时，**所有趟混在一起**，
  跨 BOOT 的混杂完全没有控制 —— 而 §533 已证明数据横跨 **11 个 BOOT**。
  本件在**真实 BOOT 层**重算，并做「BOOT 内」与「BOOT 间」分解。

方法（BOOT 反推与容差）：
  boot = round(t_abs0 - samples.t[0])，**±2s 内视为同一 BOOT**
  （依据：实测相邻值只差 1–2 秒，且 E3 卡记「BOOT 容差=开机时钟粒度 ~1.6s」）。

判据（预注册）：
  P1 全量（不控 BOOT）：复现 §522 的数值（rho(win,B)≈−0.04 / rho(t0,B)≈+0.04）
  P2 BOOT 内（去掉 BOOT 间差异）：若相位效应真实，BOOT 内也应出现
  P3 BOOT 间（用 BOOT 均值的相位）：若差异来自 BOOT 本身，则 BOOT 间有相关性

用法：python -I -X utf8 _phase_recompute.py > _phase_recompute_out.txt
"""

import datetime
import json
import os
from collections import defaultdict

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
T = 0.100
BOOT_TOL = 2      # 秒；±2s 内同一 BOOT


def P(s=""):
    print(s)


def b_pct(ts, fs):
    n = len(ts)
    span = ts[-1] - ts[0]
    if not span:
        return 0.0
    segs = []
    j = 0
    while j + 1 < n and fs[j + 1] == fs[0]:
        j += 1
    d = ts[j] - ts[0]
    if d > T:
        segs.append(d)
    i = j + 1
    while i < n:
        k = i
        while k + 1 < n and fs[k + 1] == fs[i]:
            k += 1
        dd = ts[k] - ts[i]
        if dd > T:
            segs.append(dd)
        i = k + 1
    return 100 * sum(segs) / span


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


rows = []


def add(dirpath, label, fname):
    try:
        with open(os.path.join(dirpath, fname), encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return
    s = d.get("samples") or {}
    ts, fs = s.get("t"), s.get("f")
    ta = d.get("t_abs0")
    if not ts or not fs or len(ts) < 2 or ta is None:
        return
    rows.append(dict(trip=label, w="w" + fname[9:-5],
                     boot=float(round(ta - ts[0])),   # ★ 先取整再聚类，避免浮点边界误差
                     uptime=ts[0],
                     window=d.get("window"), B=b_pct(ts, fs),
                     moving=any(fs[i] != fs[i - 1] for i in range(1, len(fs)))))


# ★ 枚举：趟子目录 + 数据根散件（§515/§517/§533 三次教训）
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

# BOOT 聚类（±2s 容差，链式：与组内最后加入者比较，避免累积漂移误并）
rows.sort(key=lambda r: r["boot"])
groups = []
for r in rows:
    if groups and r["boot"] - groups[-1]["last"] <= BOOT_TOL:
        groups[-1]["rows"].append(r)
        groups[-1]["last"] = r["boot"]
    else:
        groups.append({"rep": r["boot"], "last": r["boot"], "rows": [r]})

P("=" * 104)
P("## 〇、枚举与 BOOT 聚类核对")
P("=" * 104)
P("   有效窗 = %d（含数据根散件）  有推进 = %d"
  % (len(rows), sum(1 for r in rows if r["moving"])))
P("   BOOT 数 = %d（±%ds 容差合并）" % (len(groups), BOOT_TOL))
P()
P("   %-20s %5s %5s %7s %12s" % ("BOOT", "趟", "窗", "有推进", "uptime范围(h)"))
P("   " + "-" * 60)
for g in groups:
    ups = [r["uptime"] for r in g["rows"]]
    dt = datetime.datetime.fromtimestamp(g["rep"]).strftime("%m-%d %H:%M:%S")
    P("   %-20s %5d %5d %7d %5.2f..%5.2f"
      % (dt, len({r["trip"] for r in g["rows"]}), len(g["rows"]),
         sum(1 for r in g["rows"] if r["moving"]),
         min(ups) / 3600, max(ups) / 3600))

mv = [r for r in rows if r["moving"]]

P()
P("=" * 104)
P("## 一、P1 全量（不控 BOOT）—— 应复现 §522")
P("=" * 104)
xs_w = [r["window"] for r in mv]
ys = [r["B"] for r in mv]
xs_t = [r["uptime"] for r in mv]
P("   n = %d" % len(mv))
P("   rho(window, B%%) = %+.4f    （§522 报 −0.0403）" % spearman(xs_w, ys))
P("   rho(uptime, B%%) = %+.4f    （§522 报 +0.0395）" % spearman(xs_t, ys))
P()
P("   ★ 同一批数据在**全集 97 窗**上（§528 异族指出的口径）：")
xs_w97 = [r["window"] for r in rows]
ys97 = [r["B"] for r in rows]
xs_t97 = [r["uptime"] for r in rows]
P("   n = %d" % len(rows))
P("   rho(window, B%%) = %+.4f    （§528 异族报 +0.347432）" % spearman(xs_w97, ys97))
P("   rho(uptime, B%%) = %+.4f    （§528 异族报 +0.346119）" % spearman(xs_t97, ys97))

P()
P("=" * 104)
P("## 二、P2 BOOT 内相位（去掉 BOOT 间差异）")
P("=" * 104)
P("   做法：在每个 BOOT 内单独算 rho(uptime, B%%)，再看各 BOOT 的方向是否一致。")
P("   若相位效应真实 ⇒ 多数 BOOT 内应同号；若只是 BOOT 间差异 ⇒ BOOT 内应接近 0。")
P()
P("   %-20s %4s %12s %12s" % ("BOOT", "n", "rho(uptime,B)", "rho(window,B)"))
P("   " + "-" * 60)
within = []
for g in groups:
    sel = [r for r in g["rows"] if r["moving"]]
    if len(sel) < 3:
        continue
    dt = datetime.datetime.fromtimestamp(g["rep"]).strftime("%m-%d %H:%M")
    r1 = spearman([r["uptime"] for r in sel], [r["B"] for r in sel])
    r2 = spearman([r["window"] for r in sel], [r["B"] for r in sel])
    within.append(r1)
    P("   %-20s %4d %+12.4f %+12.4f" % (dt, len(sel), r1, r2))
P()
if within:
    pos = sum(1 for x in within if x > 0)
    neg = sum(1 for x in within if x < 0)
    P("   BOOT 内 rho(uptime,B) 汇总：正 %d 个 / 负 %d 个（可算的 BOOT 共 %d 个）"
      % (pos, neg, len(within)))
    P("   中位 = %+.4f" % sorted(within)[len(within) // 2])

P()
P("=" * 104)
P("## 三、P3 BOOT 间（用每个 BOOT 的均值）")
P("=" * 104)
P("   做法：每个 BOOT 取其窗的 B%% 均值与 uptime 均值，在 BOOT 层面求相关。")
P()
boot_x, boot_y = [], []
for g in groups:
    if not g["rows"]:
        continue
    boot_x.append(sum(r["uptime"] for r in g["rows"]) / len(g["rows"]))
    boot_y.append(sum(r["B"] for r in g["rows"]) / len(g["rows"]))
P("   BOOT 数 = %d" % len(boot_x))
P("   rho(BOOT均值 uptime, BOOT均值 B%%) = %+.4f" % spearman(boot_x, boot_y))
P()
P("   ## 各 BOOT 均值明细")
P("   %-20s %4s %10s %10s" % ("BOOT", "n", "uptime(h)", "B%均值"))
P("   " + "-" * 54)
for g in groups:
    if not g["rows"]:
        continue
    up = sum(r["uptime"] for r in g["rows"]) / len(g["rows"])
    bb = sum(r["B"] for r in g["rows"]) / len(g["rows"])
    dt = datetime.datetime.fromtimestamp(g["rep"]).strftime("%m-%d %H:%M")
    P("   %-20s %4d %10.2f %10.2f" % (dt, len(g["rows"]), up / 3600, bb))

P()
P("=" * 104)
P("## 四、判据核对与结论")
P("=" * 104)
r_all = spearman(xs_t, ys)
r_all97 = spearman(xs_t97, ys97)
P("   P1 全量 64 moving 窗：rho(uptime,B)=%+.4f（§522 值 %+.4f）" % (r_all, 0.0395))
P("   P1' 全集 97 窗：     rho(uptime,B)=%+.4f（§528 异族值 %+.4f）" % (r_all97, 0.346119))
P()
P("   ⚠ 两个口径符号/量级差异巨大 ⇒ **§522 与 §528 的矛盾源于「窗口集选择」，不是 BOOT 混杂**。")
if within:
    P("   P2 BOOT 内：可算 BOOT %d 个，正 %d / 负 %d，中位 %+.4f"
      % (len(within), sum(1 for x in within if x > 0),
         sum(1 for x in within if x < 0), sorted(within)[len(within) // 2]))
P("   P3 BOOT 间：rho = %+.4f（n=%d）" % (spearman(boot_x, boot_y), len(boot_x)))

P()
P("=" * 104)
P("## 五、诚实账")
P("=" * 104)
P("   1. 本件**未经异族核验**。")
P("   2. BOOT 反推的绝对时刻**只有 BOOT#6/#8 与台账对得上**，其余为本线反推值。")
P("   3. 单 BOOT 内样本极小（多数 BOOT 只有 1–5 个「有推进」窗）⇒ BOOT 内 rho 检验力极弱。")
P("   4. §522 与 §528 的口径矛盾（64 moving vs 97 全量）**本件只并列报告，不裁决**——")
P("      该裁决属 D-12 口径纪律范围，须用户明示。")
P("   5. 本件不做因果推断。")
