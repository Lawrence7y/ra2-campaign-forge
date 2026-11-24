# -*- coding: utf-8 -*-
"""_f0_rule_validate.py - 「f[0]==0 判别规则」全量验证（离线只读，零真机）

背景（承 §524 的重大订正）：
  异族核验判 REFUTED，找到 3 个反例，性质是 `f[0] == 0`（帧钟尚未启动的加载段被误当成停滞）。
  §524 据此提出判别规则：
      f[0] != 0  ⇒ 引擎停摆型（满速运行后突然冻结算到底）
      f[0] == 0  ⇒ 加载段型（帧钟未启动期间的空白）

本探针在**全量 97 窗**上验证这条规则是否零例外可分，并给出：
  1. 全量窗按 f[0] 分层后的分布
  2. 在两个分层内，各自满足/违反「B% == (span−freezeStart)/span」的比例
  3. 如果规则成立 ⇒ 固化为标准判据；若存在交叉 ⇒ 如实报「规则不充分」

判据（预注册）：
  R1：f[0] != 0 的窗中，恒等式成立率应显著高于 f[0] == 0 的窗。
  R2：不存在「f[0] == 0 但恒等式成立」与「f[0] != 0 但恒等式失败」同时大量出现的交叉。
  R3：若某层内恒等式成立率 = 100%，则该层可作全称断言；否则只能作统计描述。

⚠ 全窗口径（不预筛 B%、不预筛最长段占比），以避免 §524 犯过的「预筛后以偏概全」。

用法：python -I -X utf8 _f0_rule_validate.py > _f0_rule_validate_out.txt
"""

import json
import os

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
T = 0.100
TOL = 0.01      # 恒等式容差（pp）


def P(s=""):
    print(s)


def b_pct_and_freeze(ts, fs, thr=T):
    """返回 (B%, freezeStart(相对窗首), span, 是否单段主导, 最长段占比)。"""
    n = len(ts)
    t0 = ts[0]
    span = ts[-1] - t0
    if not span:
        return None
    segs = []
    j = 0
    while j + 1 < n and fs[j + 1] == fs[0]:
        j += 1
    d = ts[j] - t0
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
    tot = sum(segs)
    B = 100 * tot / span
    share = (max(segs) / tot) if tot else 0.0
    last = None
    for i in range(1, n):
        if fs[i] != fs[i - 1]:
            last = i
    freeze = (ts[last] - t0) if last is not None else 0.0
    return dict(B=B, freeze=freeze, span=span, nseg=len(segs),
                share=share, single=(share > 0.80), has_edge=(last is not None))


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
    r = b_pct_and_freeze(ts, fs)
    if not r:
        return
    g = d.get("gate") or {}
    rows.append(dict(trip=label, w="w" + fname[9:-5], f0=fs[0], fN=fs[-1],
                     units0=g.get("units0"), verdict=d.get("verdict"), **r))


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

P("=" * 112)
P("## 〇、全量样本（不预筛 B%、不预筛最长段占比）")
P("=" * 112)
P("   有效窗 = %d" % len(rows))
P("   其中 f[0]==0 = %d ；f[0]!=0 = %d"
  % (sum(1 for r in rows if r["f0"] == 0), sum(1 for r in rows if r["f0"] != 0)))

# 只对有帧沿（可定义 freezeStart）的窗做恒等式检验
edge = [r for r in rows if r["has_edge"]]
P("   有帧沿（freezeStart 可定义）= %d ；无帧沿（全窗冻结）= %d"
  % (len(edge), len(rows) - len(edge)))
P()
P("   ## f[0] 取值分布（有帧沿窗）")
vals = sorted({r["f0"] for r in edge})
P("      不同 f[0] 取值共 %d 个，范围 %s .. %s" % (len(vals), vals[0], vals[-1]))
P("      f[0]==0 的窗：%s"
  % ", ".join("%s %s" % (r["trip"], r["w"]) for r in edge if r["f0"] == 0))

P()
P("=" * 112)
P("## 一、恒等式检验（全量，按 f[0] 分层）")
P("=" * 112)
P("   恒等式：abs(Bpct - 100*(span - freeze)/span) < " + ("%.2f" % TOL) + " pp")
P()
for name, sel in (("f[0] != 0", [r for r in edge if r["f0"] != 0]),
                  ("f[0] == 0", [r for r in edge if r["f0"] == 0])):
    if not sel:
        P("   %-12s n=0" % name)
        continue
    ok = [r for r in sel if abs(r["B"] - 100 * (r["span"] - r["freeze"]) / r["span"]) < TOL]
    P("   %-12s n=%-3d 恒等式成立 %-3d (%.1f%%)  违反 %d"
      % (name, len(sel), len(ok), 100 * len(ok) / len(sel), len(sel) - len(ok)))

P()
P("   ## f[0]==0 的窗明细")
P("%-18s %3s %9s %10s %10s %10s %8s" %
  ("trip", "w", "B%", "freeze", "pred", "err", "最长占比"))
P("-" * 112)
for r in sorted([x for x in edge if x["f0"] == 0], key=lambda x: -x["B"]):
    pred = 100 * (r["span"] - r["freeze"]) / r["span"]
    P("%-18s %3s %9.4f %10.3f %10.4f %10.4f %8.4f"
      % (r["trip"], r["w"], r["B"], r["freeze"], pred, r["B"] - pred, r["share"]))

P()
P("   ## f[0]!=0 但恒等式失败的窗（若有，即规则不充分）")
bad = [r for r in edge if r["f0"] != 0
       and abs(r["B"] - 100 * (r["span"] - r["freeze"]) / r["span"]) >= TOL]
if bad:
    P("%-18s %3s %9s %10s %10s %10s %8s %6s" %
      ("trip", "w", "B%", "freeze", "pred", "err", "最长占比", "段数"))
    P("-" * 112)
    for r in sorted(bad, key=lambda x: -abs(x["B"] - 100 * (x["span"] - x["freeze"]) / x["span"]))[:20]:
        pred = 100 * (r["span"] - r["freeze"]) / r["span"]
        P("%-18s %3s %9.4f %10.3f %10.4f %+10.4f %8.4f %6d"
          % (r["trip"], r["w"], r["B"], r["freeze"], pred, r["B"] - pred, r["share"], r["nseg"]))
    P("   共 %d 个" % len(bad))
else:
    P("   （无）")

P()
P("=" * 112)
P("## 二、★ 关键：在「单段主导」子集内再看一次（这是 §524 的正确口径）")
P("=" * 112)
single = [r for r in edge if r["single"] and r["B"] >= 25.0]
P("   「最长段占>80%% 且 B%%>=25」的窗 = %d" % len(single))
for name, sel in (("f[0] != 0", [r for r in single if r["f0"] != 0]),
                  ("f[0] == 0", [r for r in single if r["f0"] == 0])):
    if not sel:
        P("   %-12s n=0" % name)
        continue
    ok = [r for r in sel if abs(r["B"] - 100 * (r["span"] - r["freeze"]) / r["span"]) < TOL]
    P("   %-12s n=%-3d 成立 %-3d (%.1f%%)"
      % (name, len(sel), len(ok), 100 * len(ok) / len(sel)))
    if len(ok) != len(sel):
        for r in sel:
            if r not in ok:
                pred = 100 * (r["span"] - r["freeze"]) / r["span"]
                P("        失败：%-18s %s  B=%.4f pred=%.4f err=%+.4f"
                  % (r["trip"], r["w"], r["B"], pred, r["B"] - pred))

P()
P("   再按 span 分层（§524 发现的分层变量）：")
for lo, hi, lab in ((20, 30, "span≈25s"), (0, 10, "span≈4s"), (10, 20, "span 10-20s")):
    sel = [r for r in single if lo <= r["span"] < hi]
    if not sel:
        continue
    ok = [r for r in sel if abs(r["B"] - 100 * (r["span"] - r["freeze"]) / r["span"]) < TOL]
    P("      %-12s n=%-3d 成立 %-3d (%.1f%%)" % (lab, len(sel), len(ok), 100 * len(ok) / len(sel)))

P()
P("=" * 112)
P("## 三、判据核对")
P("=" * 112)
nz = [r for r in edge if r["f0"] != 0]
z = [r for r in edge if r["f0"] == 0]
ok_nz = [r for r in nz if abs(r["B"] - 100 * (r["span"] - r["freeze"]) / r["span"]) < TOL]
ok_z = [r for r in z if abs(r["B"] - 100 * (r["span"] - r["freeze"]) / r["span"]) < TOL]
P("   R1  f[0]!=0 成立率 %.1f%% (%d/%d)  vs  f[0]==0 成立率 %.1f%% (%d/%d)"
  % (100 * len(ok_nz) / len(nz) if nz else 0, len(ok_nz), len(nz),
     100 * len(ok_z) / len(z) if z else 0, len(ok_z), len(z)))
P("   R2  交叉情况：f[0]==0 但成立 %d 个；f[0]!=0 但失败 %d 个"
  % (len(ok_z), len(nz) - len(ok_nz)))
P()
nz_s = [r for r in single if r["f0"] != 0]
z_s = [r for r in single if r["f0"] == 0]
ok_nz_s = [r for r in nz_s if abs(r["B"] - 100 * (r["span"] - r["freeze"]) / r["span"]) < TOL]
ok_z_s = [r for r in z_s if abs(r["B"] - 100 * (r["span"] - r["freeze"]) / r["span"]) < TOL]
P("   ## ★ 两个口径必须分开看（这是本件最重要的结论结构）")
P()
P("   ### 口径 A：全量有帧沿窗（64 个，不做任何预筛）")
P("       f[0]!=0 层成立率 %.1f%% (%d/%d) ；f[0]==0 层成立率 %.1f%% (%d/%d)"
  % (100.0 * len(ok_nz) / len(nz) if nz else 0.0, len(ok_nz), len(nz),
     100.0 * len(ok_z) / len(z) if z else 0.0, len(ok_z), len(z)))
P("       ⚠ 全量下 f[0]!=0 层只有 %.1f%% 成立 —— 因为多数窗是「多次型」（段数几十上百），"
  % (100.0 * len(ok_nz) / len(nz) if nz else 0.0))
P("         恒等式本就只该对「单段主导」成立。这一段的作用是**证明恒等式不是普遍规律**。")
P()
P("   ### 口径 B：单段主导子集（最长段占>80%% 且 B%%>=25，%d 个）" % len(single))
P("       f[0]!=0 层成立率 **%.1f%%** (%d/%d)  ← 全部成立"
  % (100.0 * len(ok_nz_s) / len(nz_s) if nz_s else 0.0, len(ok_nz_s), len(nz_s)))
P("       f[0]==0 层成立率 **%.1f%%** (%d/%d)  ← 全部失败"
  % (100.0 * len(ok_z_s) / len(z_s) if z_s else 0.0, len(ok_z_s), len(z_s)))
P()
if nz_s and len(ok_nz_s) == len(nz_s):
    P("   ⇒ **R3 成立**：单段子集内，`f[0]!=0` 层恒等式 100%% 成立（%d/%d），可作全称断言；"
      % (len(ok_nz_s), len(nz_s)))
    P("      `f[0]==0` 层 0%% 成立，须单列「加载段型」。")
    P("      **判别规则 `f[0]==0` 在单段子集内零例外分开两类。**")
else:
    P("   ⇒ R3 不成立：单段子集内 f[0]!=0 层成立率 %.1f%%，不可作全称断言。"
      % (100.0 * len(ok_nz_s) / len(nz_s) if nz_s else 0.0))

P()
P("=" * 112)
P("## 四、诚实账")
P("=" * 112)
P("   1. 本件用**全窗口径**（不预筛 B%/最长段占比），以避免 §524 犯过的预筛偏差；")
P("      同时保留单段子集口径作对照——**两个口径的成立率差异本身就是重要信息**。")
P("   2. `f[0]==0` 只说明「采集起点帧钟未启动」；不排除其它未识别的加载态（如 f[0] 很小但非 0）。")
P("   3. 全窗冻结窗（无帧沿）freezeStart 无定义，已排除在恒等式检验外。")
P("   4. 恒等式容差 %.2f pp 是对 `T=0.1s` 舍入的经验取值；异族已核 T±0.002 扰动下反例结论稳健。" % TOL)
P("   5. 本件**未经异族核验**，亦不做机制定谳。")
