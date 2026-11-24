# -*- coding: utf-8 -*-
"""
_xocc_verify.py — 独立复算核验：measure 窗「停滞占比」口径影响普查（口径 occ_a vs 口径 B）

独立实现声明：
  * 本脚本由异族核验员（GLM-5.3-flash）独立编写，仅依据任务书给出的两条口径定义实现。
  * 不读取被核验方任何实现/输出文件（lead/goal3t_nightwatch_20261102/_occ_census_all.py、
    _occ_census_all_out.txt 等），保持完全独立。
  * 纯离线只读：只读 out/re_work/.../qc161_u0400_trip/ 下 measure_w*.json；
    写域仅本目录 _xocc_verify_out.txt。不启动游戏、不部署、不改台账或数据文件。

口径（T=0.1 秒，严格大于才计入；占比 = 100*Σ保留段/span，span=t[-1]-t[0]）：
  occ_a（既有实装）：trans = 每个 f 值变更点的样本时刻（即 f[i]!=f[i-1] 时的 t[i]）；
    段 = head(trans[0]-t[0]) + interior(相邻 trans 之差) + tail(t[-1]-trans[-1])；
    trans 为空则整段算 head。
  B（对比口径）：每个平台（极大连续同值段）取 末样本t - 首样本t；head=首平台、
    interior=中间平台、tail=末平台。

运行： python -I -X utf8 _xocc_verify.py
"""
import json
import math
import re
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip")
OUT = Path(r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\_xocc_verify_out.txt")
T = 0.1          # 段计入阈值（秒），严格大于
GAP10 = 0.010    # 采样缺口阈值（秒）

L = []
def P(s=""):
    L.append(s)

def f4(x):
    return f"{x:.4f}"

def f6(x):
    return f"{x:.6f}"


# ---------- 口径实现 ----------

def occ_a_segments(ts, fs):
    """口径 occ_a 的段列表与 trans 集合。"""
    n = len(ts)
    trans = [ts[i] for i in range(1, n) if fs[i] != fs[i - 1]]
    if not trans:
        return [ts[-1] - ts[0]], trans
    segs = [trans[0] - ts[0]]
    for k in range(len(trans) - 1):
        segs.append(trans[k + 1] - trans[k])
    segs.append(ts[-1] - trans[-1])
    return segs, trans


def occ_b_segments(ts, fs):
    """口径 B 的段列表与各平台 (i0,i1) 闭区间索引。"""
    n = len(ts)
    segs = []
    bounds = []
    i = 0
    while i < n:
        j = i
        while j + 1 < n and fs[j + 1] == fs[i]:
            j += 1
        segs.append(ts[j] - ts[i])
        bounds.append((i, j))
        i = j + 1
    return segs, bounds


def load_window(path):
    """读一个 measure_w*.json；返回 (ts, fs, obj, err)。"""
    try:
        with open(path, encoding="utf-8") as fh:
            obj = json.load(fh)
    except Exception as e:
        return None, None, None, f"JSON解析失败: {type(e).__name__}: {e}"
    if not isinstance(obj, dict):
        return None, None, None, "顶层非JSON对象"
    smp = obj.get("samples")
    if not isinstance(smp, dict) or "t" not in smp or "f" not in smp:
        return None, None, None, "缺少 samples.t/f"
    t, f = smp["t"], smp["f"]
    if not isinstance(t, list) or not isinstance(f, list):
        return None, None, None, "samples.t/f 非数组"
    if len(t) != len(f):
        return None, None, None, f"t/f 长度不一致 {len(t)} vs {len(f)}"
    n = len(t)
    if n < 2:
        return None, None, None, f"样本数 {n} < 2"
    try:
        ts = [float(x) for x in t]
    except Exception as e:
        return None, None, None, f"t 含非数值: {type(e).__name__}"
    for x in f:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            return None, None, None, "f 含非数值样本"
    for i in range(n - 1):
        if ts[i + 1] < ts[i]:
            return None, None, None, f"t 非单调递增 @i={i} ({ts[i]!r} -> {ts[i+1]!r})"
    span = ts[-1] - ts[0]
    if span <= 0:
        return None, None, None, f"span={span!r} <= 0"
    return ts, f, obj, None


def compute_window(ts, fs):
    """对一个窗算两条口径 + 采样缺口统计 + Δ 的精确分解。"""
    n = len(ts)
    span = ts[-1] - ts[0]
    A_segs, trans = occ_a_segments(ts, fs)
    B_segs, bounds = occ_b_segments(ts, fs)
    A_sum = sum(s for s in A_segs if s > T)
    B_sum = sum(s for s in B_segs if s > T)
    occA = 100.0 * A_sum / span
    occB = 100.0 * B_sum / span

    # 采样间隔与缺口（>10ms）
    dts = [ts[i + 1] - ts[i] for i in range(n - 1)]
    g10 = [d for d in dts if d > GAP10]
    n_g10, s_g10 = len(g10), sum(g10)

    # 帧值变更点与 gap_out（上一平台末样本 -> 新平台首样本）
    ch = [i for i in range(1, n) if fs[i] != fs[i - 1]]
    gap_out = [ts[i] - ts[i - 1] for i in ch]
    n_ch = len(gap_out)
    s_go = sum(gap_out)
    go10 = [g for g in gap_out if g > GAP10]
    n_go10, s_go10 = len(go10), sum(go10)

    # Δ 的精确分解（k=0..m-2 段：A_k = B_k + gap_k；tail 段两者相等）：
    #   Δsum = part1(Σ 被 occ_a 保留段吸收的 gap_k) + part2(仅 occ_a 保留段的 B_k, 各<=T)
    m = len(B_segs)
    part1 = part2 = p1s = p1n = 0.0
    n_flipseg = n_fseg10 = n_fsegn = 0
    p2b10 = p2bn = 0.0
    for k in range(m - 1):
        if A_segs[k] > T:
            g = ts[bounds[k + 1][0]] - ts[bounds[k][1]]
            part1 += g
            if g > GAP10:
                p1s += g
            else:
                p1n += g
            if B_segs[k] <= T:
                part2 += B_segs[k]
                n_flipseg += 1
                if g > GAP10:
                    n_fseg10 += 1
                    p2b10 += B_segs[k]
                else:
                    n_fsegn += 1
                    p2bn += B_segs[k]
    resid = (A_sum - B_sum) - (part1 + part2)

    return dict(
        n=n, span=span, occA=occA, occB=occB, dpp=occA - occB,
        m_plat=m, n_trans=n_ch, n_g10=n_g10, s_g10=s_g10,
        s_go=s_go, n_go10=n_go10, s_go10=s_go10,
        part1=part1, p1s=p1s, p1n=p1n, part2=part2, n_flipseg=n_flipseg,
        n_fseg10=n_fseg10, n_fsegn=n_fsegn, p2b10=p2b10, p2bn=p2bn,
        resid=resid,
    )


def pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return float("nan")
    return sxy / math.sqrt(sxx * syy)


# ---------- 主流程 ----------

def main():
    P("=" * 100)
    P("独立复算核验：measure 窗「停滞占比」口径影响普查（occ_a vs 口径B）")
    P(f"实现者：异族核验员（GLM-5.3-flash），独立实现，未读取被核验方实现/输出文件")
    P(f"命令：python -I -X utf8 {Path(sys.argv[0]).name}")
    P(f"数据根：{ROOT}")
    P(f"T={T}s（严格大于计入），缺口阈值 GAP10={GAP10}s，占比=100*Σ保留段/span")
    P("=" * 100)

    files = sorted(ROOT.rglob("measure_w*.json"))
    P(f"\n[枚举] rglob('measure_w*.json') 共 {len(files)} 个文件")

    rows = []       # 趟子目录内的有效窗
    skipped = []    # (相对路径, 原因)
    strays = []     # (相对路径, w) 根目录散件（不属于任何趟子目录）
    trips = set()
    depth_gt1 = []

    for p in files:
        rel = p.relative_to(ROOT)
        m = re.fullmatch(r"measure_w(\d+)\.json", p.name)
        if not m:
            skipped.append((str(rel), "文件名不匹配 measure_w<数字>.json"))
            continue
        w = int(m.group(1))
        if len(rel.parts) < 2:
            strays.append((str(rel), w))
            continue
        trip = rel.parts[0]
        if len(rel.parts) > 2:
            depth_gt1.append(str(rel))
        trips.add(trip)
        ts, fs, obj, err = load_window(p)
        if err:
            skipped.append((str(rel), err))
            continue
        r = compute_window(ts, fs)
        r["trip"] = trip
        r["w"] = w
        r["rel"] = str(rel)
        rows.append(r)

    rows.sort(key=lambda r: (r["trip"], r["w"]))
    P(f"[枚举] 趟子目录数（含 measure_w*.json）= {len(trips)}")
    P(f"[枚举] 趟子目录清单（按名排序）：")
    for tp in sorted(trips):
        nw = sum(1 for r in rows if r["trip"] == tp)
        P(f"       {tp:24s} 有效窗 {nw}")
    P(f"[枚举] 根目录散件（不在任何趟子目录，不入全量统计，另行单独列出）= {len(strays)}")
    for s, w in strays:
        P(f"       {s}  (w{w})")
    if depth_gt1:
        P(f"[枚举] 注意：存在嵌套深度>1 的 measure 文件 {len(depth_gt1)} 个：{depth_gt1}")
    P(f"[枚举] 跳过窗 = {len(skipped)}")

    N = len(rows)
    P(f"\n[全量] 有效窗数 N = {N}")

    # ---- 全量统计 ----
    occAMean = sum(r["occA"] for r in rows) / N
    occBMean = sum(r["occB"] for r in rows) / N
    diffPp = occAMean - occBMean
    meanDpp = sum(r["dpp"] for r in rows) / N
    ident = [r for r in rows if abs(r["dpp"]) <= 1e-9]
    differ = [r for r in rows if abs(r["dpp"]) > 1e-9]
    grades = OrderedDict()
    boundsG = [(0.0, 0.1), (0.1, 1.0), (1.0, 5.0), (5.0, 15.0), (15.0, float("inf"))]
    namesG = ["<=0.1", "0.1-1", "1-5", "5-15", ">15"]
    for (lo, hi), nm in zip(boundsG, namesG):
        if lo == 0.0:
            grades[nm] = sum(1 for r in rows if abs(r["dpp"]) <= hi)
        elif hi == float("inf"):
            grades[nm] = sum(1 for r in rows if abs(r["dpp"]) > lo)
        else:
            grades[nm] = sum(1 for r in rows if lo < abs(r["dpp"]) <= hi)
    flips = [r for r in rows if (r["occA"] >= 50.0) != (r["occB"] >= 50.0)]
    top10 = sorted(rows, key=lambda r: (-abs(r["dpp"]), r["trip"], r["w"]))[:10]

    P(f"[全量] occ_a 均值 = {f4(occAMean)} %  （全精度 {occAMean!r}）")
    P(f"[全量] 口径B 均值 = {f4(occBMean)} %  （全精度 {occBMean!r}）")
    P(f"[全量] 差值 diffPp = occA均值 - B均值 = {f4(diffPp)} pp （全精度 {diffPp!r}）")
    P(f"[全量] 交叉核对：逐窗 dpp 的均值 = {f4(meanDpp)} pp（与上者应在 fp 误差内一致）")
    P(f"[全量] 完全相同窗（|Δ|<=1e-9）= {len(ident)}；有差异窗 = {len(differ)}")
    P(f"[全量] 逐窗 Δpp 范围：min={min(r['dpp'] for r in rows):+.6f}  max={max(r['dpp'] for r in rows):+.6f}（occ_a>=B 应恒成立）")
    P(f"[全量] 按 |Δpp| 分级（左闭右开，首桶含端点）：")
    P(f"       " + "; ".join(f"{nm}:{grades[nm]}" for nm in namesG))
    P(f"[全量] 跨50%线定性翻转窗（occ_a 与 B 分居 50% 两侧，判定 (a>=50)!=(b>=50)）= {len(flips)}")
    for r in flips:
        P(f"       flip: trip {r['trip']} w{r['w']} occ_a={f4(r['occA'])} B={f4(r['occB'])} Δ={f4(r['dpp'])}")

    P(f"\n[Top10] |Δpp| 最大的 10 窗：")
    for r in top10:
        P(f"       trip {r['trip']:24s} w{r['w']}  occ_a={f6(r['occA'])}  B={f6(r['occB'])}  Δ={f6(r['dpp'])} pp"
          f"  span={r['span']:.3f}s  n={r['n']}")

    # ---- 逐窗明细（主表 + 缺口/分解表）----
    P(f"\n[明细1] 逐窗两口径（{N} 行，按 trip,w 排序）：")
    P("       " + f"{'trip':24s} {'w':>2s} {'n':>7s} {'span_s':>10s} {'occ_a%':>10s} {'B%':>10s} {'Δpp':>10s} {'平台数':>6s}")
    for r in rows:
        P("       " + f"{r['trip']:24s} {r['w']:2d} {r['n']:7d} {r['span']:10.3f} {r['occA']:10.4f} {r['occB']:10.4f} {r['dpp']:10.4f} {r['m_plat']:6d}")
    P(f"\n[明细2] 逐窗采样缺口与 Δ 精确分解：")
    P("       " + f"{'trip':24s} {'w':>2s} {'n_g10ms':>7s} {'Σg10ms_s':>10s} {'n_ch':>6s} {'Σgap_out_s':>10s} {'n_go10':>6s} {'Σgo10_s':>9s}"
      f" {'part1_s':>9s} {'p1>10ms':>9s} {'p1<=10m':>9s} {'part2_s':>9s} {'n_fseg':>6s} {'resid':>9s}")
    for r in rows:
        P("       " + f"{r['trip']:24s} {r['w']:2d} {r['n_g10']:7d} {r['s_g10']:10.4f} {r['n_trans']:6d} {r['s_go']:10.4f} {r['n_go10']:6d} {r['s_go10']:9.4f}"
          f" {r['part1']:9.4f} {r['p1s']:9.4f} {r['p1n']:9.4f} {r['part2']:9.4f} {r['n_flipseg']:6d} {r['resid']:9.2e}")
    max_resid = max(abs(r["resid"]) for r in rows)
    P(f"[明细2] 分解核对：max |(A_sum-B_sum)-(part1+part2)| = {max_resid:.3e} s（应≈0，fp 误差级）")

    # ---- 跳过窗 ----
    P(f"\n[跳过] 共 {len(skipped)} 项：")
    for s, why in skipped:
        extra = ""
        try:
            with open(ROOT / s, encoding="utf-8") as fh:
                oj = json.load(fh)
            if isinstance(oj, dict):
                extra = f" | verdict={oj.get('verdict')!r} error={oj.get('error')!r} window={oj.get('window')!r}"
        except Exception:
            pass
        P(f"       {s}: {why}{extra}")
    if not skipped:
        P("       （无）")

    # ---- 根目录散件（信息性，不入全量；另给「若计入」的敏感性变体）----
    stray_rows = []
    if strays:
        P(f"\n[散件] 根目录 measure_w*.json（不属于任何趟子目录，未计入全量统计；单独计算供参考）：")
        for s, w in strays:
            ts, fs, obj, err = load_window(ROOT / s)
            if err:
                P(f"       {s}: 读取失败 {err}")
                continue
            r = compute_window(ts, fs)
            r["trip"] = "(root)"
            r["w"] = w
            stray_rows.append(r)
            P(f"       {s}: n={r['n']} span={r['span']:.3f}s occ_a={f4(r['occA'])}% B={f4(r['occB'])}% Δ={f4(r['dpp'])}pp"
              f" n_g10={r['n_g10']} Σg10={r['s_g10']:.4f}s Σgap_out={r['s_go']:.4f}s")
        N2 = N + len(stray_rows)
        a2 = (sum(r["occA"] for r in rows) + sum(r["occA"] for r in stray_rows)) / N2
        b2 = (sum(r["occB"] for r in rows) + sum(r["occB"] for r in stray_rows)) / N2
        P(f"[散件] 敏感性变体：若把 {len(stray_rows)} 个散件计入（N={N2}）："
          f"occ_a 均值={f4(a2)}%，B 均值={f4(b2)}%，Δ={f4(a2-b2)}pp（仅参考，主口径仍为趟子目录 91 窗）")

    # ---- 子集自校验 ----
    SUBSET = OrderedDict([
        ("l3_1101v3a", [0, 1, 2]), ("l3_1101v3b", [0, 1, 2]), ("l3_20261031ha", [0]),
        ("l3_20261031hb", [0, 1, 2]), ("l3_20261023q", [0, 1, 2]), ("l3_20261023r", [0, 1, 2]),
        ("l1c_20261021", [0, 1, 2]), ("l1a_20261020", [0, 1, 2]), ("t55k_20261020", [0, 1, 2]),
        ("l1_20261023e4", [0, 1, 2]), ("l3_1101v4c", [0, 1, 2]), ("l3_1101v4d", [0, 1, 2]),
    ])
    idx = {(r["trip"], r["w"]): r for r in rows}
    sub = []
    missing = []
    for trip, ws in SUBSET.items():
        for w in ws:
            r = idx.get((trip, w))
            if r is None:
                missing.append((trip, w))
            else:
                sub.append(r)
    P(f"\n[子集自校验] 指定 12 趟/34 窗：")
    P("       " + f"{'trip':24s} {'w':>2s} {'occ_a%':>10s} {'B%':>10s} {'Δpp':>10s}")
    for r in sorted(sub, key=lambda r: (r["trip"], r["w"])):
        P("       " + f"{r['trip']:24s} {r['w']:2d} {r['occA']:10.4f} {r['occB']:10.4f} {r['dpp']:10.4f}")
    expA, expB, expD = 34.4184, 31.6474, 2.7710
    if missing:
        P(f"[子集自校验] 缺失窗：{missing}")
    subN = len(sub)
    subA = sum(r["occA"] for r in sub) / subN
    subB = sum(r["occB"] for r in sub) / subN
    subD = subA - subB
    # 备用口径：span 加权（仅诊断，不作为 PASS 判据）
    wA = sum(r["occA"] * r["span"] for r in sub) / sum(r["span"] for r in sub)
    wB = sum(r["occB"] * r["span"] for r in sub) / sum(r["span"] for r in sub)
    okA = abs(subA - expA) <= 2e-4
    okB = abs(subB - expB) <= 2e-4
    okD = abs(subD - expD) <= 2e-4
    P(f"[子集自校验] 子集窗数 = {subN}（应 34），缺失 = {len(missing)}")
    P(f"[子集自校验] occ_a 等权均值 = {f6(subA)}  期望 34.4184  |偏差|={abs(subA-expA):.6f} {'PASS' if okA else 'FAIL'}")
    P(f"[子集自校验] B    等权均值 = {f6(subB)}  期望 31.6474  |偏差|={abs(subB-expB):.6f} {'PASS' if okB else 'FAIL'}")
    P(f"[子集自校验] 差值        = {f6(subD)}  期望 +2.7710  |偏差|={abs(subD-expD):.6f} {'PASS' if okD else 'FAIL'}")
    P(f"[子集自校验] （诊断备用：span 加权 occ_a={f6(wA)} B={f6(wB)} Δ={f6(wA-wB)}，不作判据）")
    subPass = (subN == 34) and (not missing) and okA and okB and okD
    P(f"[子集自校验] 总判定 = {'PASS' if subPass else 'FAIL'}（容差 ±0.0002，等权均值）")

    # ---- 逐趟聚合（采样缺口 vs |Δpp|）----
    P(f"\n[逐趟] 采样缺口与差值聚合（趟内各窗求和；均值窗数等权）：")
    P("       " + f"{'trip':24s} {'nw':>3s} {'n_g10ms':>7s} {'Σg10ms_s':>10s} {'Σgap_out_s':>10s} {'Σgo10_s':>9s} {'Σspan_s':>9s}"
      f" {'go%':>7s} {'g10%':>7s} {'occ_a%':>9s} {'B%':>9s} {'Δpp':>9s} {'max|Δ|':>8s}")
    bytrip = OrderedDict()
    for r in rows:
        bytrip.setdefault(r["trip"], []).append(r)
    for tp in sorted(bytrip):
        rs = bytrip[tp]
        nw = len(rs)
        s_g10 = sum(r["s_g10"] for r in rs)
        s_go = sum(r["s_go"] for r in rs)
        s_go10 = sum(r["s_go10"] for r in rs)
        sp = sum(r["span"] for r in rs)
        mA = sum(r["occA"] for r in rs) / nw
        mB = sum(r["occB"] for r in rs) / nw
        mD = mA - mB
        mx = max(abs(r["dpp"]) for r in rs)
        P("       " + f"{tp:24s} {nw:3d} {sum(r['n_g10'] for r in rs):7d} {s_g10:10.4f} {s_go:10.4f} {s_go10:9.4f} {sp:9.3f}"
          f" {100*s_go/sp:7.3f} {100*s_g10/sp:7.3f} {mA:9.4f} {mB:9.4f} {mD:9.4f} {mx:8.4f}")

    # ---- 相关性分析 ----
    P(f"\n[相关] 逐窗 Pearson 相关（N={N}）：")
    xs_go = [100.0 * r["s_go"] / r["span"] for r in rows]        # gap_out 合计占 span %
    xs_g10 = [100.0 * r["s_g10"] / r["span"] for r in rows]      # 全部>10ms缺口合计占 span %
    xs_go10 = [100.0 * r["s_go10"] / r["span"] for r in rows]    # 变更处>10ms gap_out 占 span %
    xs_ng10 = [float(r["n_g10"]) for r in rows]
    xs_p1s = [100.0 * r["p1s"] / r["span"] for r in rows]        # 被保留段吸收的>10ms gap 占 span %
    xs_p1n = [100.0 * r["p1n"] / r["span"] for r in rows]        # 被保留段吸收的<=10ms gap 占 span %
    ys_d = [r["dpp"] for r in rows]
    ys_ad = [abs(r["dpp"]) for r in rows]
    for nm, xs, use_abs in [("Δpp ~ Σgap_out%/span", xs_go, False), ("|Δpp| ~ Σgap_out%/span", xs_go, True),
                            ("Δpp ~ 全部>10ms缺口%/span", xs_g10, False), ("Δpp ~ 变更处>10ms gap%/span", xs_go10, False),
                            ("|Δpp| ~ 变更处>10ms gap%/span", xs_go10, True),
                            ("Δpp ~ >10ms缺口个数", xs_ng10, False),
                            ("Δpp ~ part1(>10ms部分)%/span", xs_p1s, False), ("Δpp ~ part1(<=10ms部分)%/span", xs_p1n, False)]:
        yy = ys_ad if use_abs else ys_d
        P(f"       r({nm:34s}, {'|Δpp|' if use_abs else 'Δpp'}) = {pearson(xs, yy):+.4f}")

    # ---- 汇总份额分析（Δ 的构成）----
    Sspan = sum(r["span"] for r in rows)
    Sgo = sum(r["s_go"] for r in rows)
    Sg10 = sum(r["s_g10"] for r in rows)
    Sgo10 = sum(r["s_go10"] for r in rows)
    Sp1 = sum(r["part1"] for r in rows)
    Sp1s = sum(r["p1s"] for r in rows)
    Sp1n = sum(r["p1n"] for r in rows)
    Sp2 = sum(r["part2"] for r in rows)
    Sp2b10 = sum(r["p2b10"] for r in rows)
    Sp2bn = sum(r["p2bn"] for r in rows)
    Sdsum = sum(r["dpp"] * r["span"] / 100.0 for r in rows)
    P(f"\n[构成] 全量合计（Σspan={Sspan:.3f}s）：")
    P(f"       Σgap_out（全部变更处间隙）= {Sgo:.4f}s -> 占 Σspan {100*Sgo/Sspan:.4f}%")
    P(f"         其中变更处 gap>10ms     = {Sgo10:.4f}s -> {100*Sgo10/Sspan:.4f}%；<=10ms = {100*(Sgo-Sgo10)/Sspan:.4f}%")
    P(f"       Σ全部>10ms采样缺口       = {Sg10:.4f}s -> 占 Σspan {100*Sg10/Sspan:.4f}%（共 {sum(r['n_g10'] for r in rows)} 处）")
    P(f"       part1（被 occ_a 保留段吸收的 gap）= {Sp1:.4f}s -> {100*Sp1/Sspan:.4f}%")
    P(f"         其中 >10ms（饥饿性缺口）= {Sp1s:.4f}s -> {100*Sp1s/Sspan:.4f}%")
    P(f"         其中 <=10ms（正常采样距）= {Sp1n:.4f}s -> {100*Sp1n/Sspan:.4f}%")
    P(f"       part2（仅 occ_a 过阈值的平台体, 各<=0.1s）= {Sp2:.4f}s -> {100*Sp2/Sspan:.4f}%（共 {sum(r['n_flipseg'] for r in rows)} 段）")
    P(f"         其尾随 gap>10ms 的段 {sum(r['n_fseg10'] for r in rows)} 个（体合计 {Sp2b10:.4f}s），"
      f"<=10ms 的段 {sum(r['n_fsegn'] for r in rows)} 个（体合计 {Sp2bn:.4f}s）")
    P(f"       span 加权 Δ = Σ(dpp*span)/Σspan*100 = {100*Sdsum/Sspan:.4f} pp；等权 Δpp = {f4(diffPp)} pp")
    P(f"       核对：100*(Σpart1+Σpart2)/Σspan = {100*(Sp1+Sp2)/Sspan:.4f}% 应≈上者")
    tw = 100 * Sdsum / Sspan
    P(f"       span 加权 Δ 的构成份额：饥饿缺口(part1>10ms)={100*Sp1s/Sspan/tw*100:.1f}%、"
      f"正常采样距(part1<=10ms)={100*Sp1n/Sspan/tw*100:.1f}%、"
      f"阈值并段体(其中尾gap>10ms)={100*Sp2b10/Sspan/tw*100:.1f}%、"
      f"阈值并段体(尾gap<=10ms)={100*Sp2bn/Sspan/tw*100:.1f}%")

    # ---- 结论提示（数字口径）----
    P(f"\n[结论要点]")
    P(f"       全量 {N} 窗：occ_a 均值 {f4(occAMean)}%，B 均值 {f4(occBMean)}%，差 {f4(diffPp)}pp；"
      f"相同窗 {len(ident)}，差异窗 {len(differ)}，翻转 {len(flips)}。")
    P(f"       子集自校验：{'PASS' if subPass else 'FAIL'}（occ_a={f6(subA)} vs 34.4184；B={f6(subB)} vs 31.6474；Δ={f6(subD)} vs +2.7710）")
    hi = sum(1 for r in rows if r["p1s"] > 0)
    P(f"       Δ 分解：part1(>10ms 饥饿缺口)={100*Sp1s/Sspan:.4f}%，part1(<=10ms 正常采样距)={100*Sp1n/Sspan:.4f}%，part2(阈值翻转)={100*Sp2/Sspan:.4f}%")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"DONE -> {OUT}  rows={N} skipped={len(skipped)} strays={len(strays)} subset={'PASS' if subPass else 'FAIL'}")
    print(f"occA={f4(occAMean)} occB={f4(occBMean)} diff={f4(diffPp)} ident={len(ident)} differ={len(differ)} flips={len(flips)}")


if __name__ == "__main__":
    main()
