# -*- coding: utf-8 -*-
"""
_xst_verify.py — 异族独立核验（相对 DeepSeek-V4.1-flash）
核验对象：lead/goal3t_nightwatch_20261102/_stall_timestructure*.py/.txt 的三结论 A/B/C。
本脚本不读取任何被核验件；全部指标按任务书定义独立实现；纯只读数据，唯一输出 _xst_verify_out.txt。

口径 B（停滞占比 B%）：
  平台 = f 相同的连续样本（极大游程）；平台停滞时长 = 平台最后样本 t 减第一个样本 t；
  只计时长 > T 的平台；B% = 100 * Σ(计入平台时长) / (t[-1] - t[0])。
帧沿缺口%：
  对每处 f[i] != f[i-1]，取 dt = t[i]-t[i-1]，累加其中 > 10ms 者，
  gap% = 100 * Σ / (t[-1]-t[0])。
目标批：窗内 f 至少变化一次 且 25 <= B%(T=0.1) < 99 且 帧沿缺口累计 == 0。
分型（T=0.1）：最长段/总停滞 > 80% 为 single；< 40% 为 multi；其余 mid。
"""
import json, re
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip").resolve()
OUTPATH = Path(r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\_xst_verify_out.txt").resolve()
ALLOW_WRITE_DIR = OUTPATH.parent

THS = [0.05, 0.075, 0.10, 0.15, 0.20]
EDGE = 0.010

out_lines = []
def P(s=""):
    out_lines.append(str(s))

def runs_of(t, f):
    """极大等值游程: [dur, fval, i0, i1]；dur = t[i1] 减 t[i0]"""
    n = len(t); i = 0; runs = []
    while i < n:
        j = i
        while j + 1 < n and f[j+1] == f[i]:
            j += 1
        runs.append([t[j] - t[i], f[i], i, j])
        i = j + 1
    return runs

def b_pct(span, runs, T):
    if span <= 0:
        return float('nan')
    return 100.0 * sum(r[0] for r in runs if r[0] > T) / span

def seg_count(runs, T):
    return sum(1 for r in runs if r[0] > T)

def main():
    # ============ 枚举（rglob + relative_to 越界校验） ============
    files, loose = [], []
    for p in sorted(ROOT.rglob("measure_w*.json")):
        try:
            rel = p.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            continue  # 越界即弃
        files.append((rel, p))
        if "/" not in rel:
            loose.append(rel)
    files.sort()
    P("== 枚举 ==")
    P("measure_w*.json（rglob 全深度）总数: %d" % len(files))
    P("数据根目录直属散件数: %d -> %s" % (len(loose), loose))
    deep = [rel for rel, _ in files if rel.count("/") > 1]
    P("嵌套深度大于 1 的 measure 文件数: %d %s" % (len(deep), deep))
    nonstd = [rel for rel, _ in files if not re.fullmatch(r"measure_w\d+\.json", Path(rel).name)]
    P("不符合 measure_w数字.json 命名的文件: %d %s" % (len(nonstd), nonstd))

    windows, invalid = [], []
    for rel, p in files:
        try:
            with open(p, "r", encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception as e:
            invalid.append((rel, "parse_error %r" % (e,))); continue
        s = d.get("samples") or {}
        t = s.get("t"); f = s.get("f")
        if not isinstance(t, list) or len(t) < 2:
            invalid.append((rel, "samples 缺失或 len(t)<2 (len_t=%r)" % (len(t) if isinstance(t, list) else None,))); continue
        if not isinstance(f, list) or len(f) != len(t):
            invalid.append((rel, "f 缺失或 len(f)!=len(t)")); continue
        m = re.fullmatch(r"measure_w(\d+)\.json", Path(rel).name)
        wn = int(m.group(1)) if m else -1
        trip = rel.split("/")[0] if "/" in rel else ""
        windows.append({
            "rel": rel, "trip": trip, "wn": wn,
            "label": ("%s w%d" % (trip, wn)) if trip else ("ROOT w%d" % wn),
            "verdict": d.get("verdict"),
            "t": t, "f": f,
        })
    P("有效窗（samples 存在且 len(t)>=2）: %d；无效: %d" % (len(windows), len(invalid)))
    for rel, why in invalid:
        P("  INVALID %s : %s" % (rel, why))
    P("有效窗 verdict 分布: %s" % dict(Counter(w["verdict"] for w in windows)))

    # ============ 指标 ============
    for w in windows:
        t, f = w["t"], w["f"]
        w["n"] = len(t)
        w["mono_strict"] = all(t[i] > t[i-1] for i in range(1, len(t)))
        span = t[-1] - t[0]
        w["span"] = span
        w["runs"] = runs_of(t, f)
        w["B"] = {T: b_pct(span, w["runs"], T) for T in THS}
        gsum = 0.0; n_edges = 0; n_big = 0; n_knife = 0
        for i in range(1, len(t)):
            if f[i] != f[i-1]:
                dt = t[i] - t[i-1]; n_edges = n_edges + 1
                if dt > EDGE:
                    gsum += dt; n_big = n_big + 1
                elif dt > EDGE - 0.0005:
                    n_knife = n_knife + 1
        w["gap_sum"] = gsum
        w["gap_pct"] = (100.0 * gsum / span) if span > 0 else float('nan')
        w["n_edges"] = n_edges; w["n_big_edges"] = n_big; w["n_knife_edges"] = n_knife
        w["changed"] = n_edges > 0
        segs = [r[0] for r in w["runs"] if r[0] > 0.10]
        tot = sum(segs)
        w["segs010_n"] = len(segs)
        w["stall_total010"] = tot
        w["share"] = (max(segs) / tot) if segs and tot > 0 else None
        allsum = sum(r[0] for r in w["runs"])
        w["share_alt"] = (max(segs) / allsum) if segs and allsum > 0 else None
        if w["share"] is not None:
            w["type"] = "single" if w["share"] > 0.80 else ("multi" if w["share"] < 0.40 else "mid")
        else:
            w["type"] = None
        if w["share_alt"] is not None:
            w["type_alt"] = "single" if w["share_alt"] > 0.80 else ("multi" if w["share_alt"] < 0.40 else "mid")
        else:
            w["type_alt"] = None
        w["segn"] = {T: seg_count(w["runs"], T) for T in THS}

    bad_mono = [w["rel"] for w in windows if not w["mono_strict"]]
    P("t 严格递增违例窗: %d %s" % (len(bad_mono), bad_mono[:5]))

    # ============ 目标批 ============
    def reason(w):
        rs = []
        if not w["changed"]: rs.append("no_change")
        if not (25.0 <= w["B"][0.10] < 99.0):
            rs.append("B<25" if w["B"][0.10] < 25.0 else "B>=99")
        if w["gap_sum"] != 0.0: rs.append("gap>0")
        return rs

    target = [w for w in windows if w["changed"] and 25.0 <= w["B"][0.10] < 99.0 and w["gap_sum"] == 0.0]
    P("")
    P("== 目标批筛选 ==")
    P("目标批（changed & 25<=B(0.1)<99 & gap==0）窗数: %d（任务书预期 25）" % len(target))
    P("有效窗剔除瀑布（条件可重叠）: no_change=%d, changed&B<25=%d, changed&B>=99=%d, changed&gap>0=%d" % (
        sum(1 for w in windows if not w["changed"]),
        sum(1 for w in windows if w["changed"] and w["B"][0.10] < 25.0),
        sum(1 for w in windows if w["changed"] and w["B"][0.10] >= 99.0),
        sum(1 for w in windows if w["changed"] and w["gap_sum"] != 0.0)))
    P("各窗剔除原因明细:")
    for w in windows:
        rs = reason(w)
        if rs:
            P("  EXCL %-40s verdict=%-12s B010=%.4f gap_sum=%.6f reasons=%s" % (
                w["label"], w["verdict"], w["B"][0.10], w["gap_sum"], ",".join(rs)))

    P("")
    P("== 目标批逐窗明细（全部 5 阈值） ==")
    P("%-40s %-12s %7s %8s | %5s %5s %5s %5s %5s | %7s %7s %4s %4s | %s" % (
        "window", "verdict", "span_s", "B010", "T.05", "T.075", "T.10", "T.15", "T.20",
        "share", "sh_alt", "bigE", "knif", "type"))
    for w in sorted(target, key=lambda x: (x["trip"], x["wn"])):
        P("%-40s %-12s %7.3f %8.4f | %5d %5d %5d %5d %5d | %7.4f %7.4f %4d %4d | %s" % (
            w["label"], w["verdict"], w["span"], w["B"][0.10],
            w["segn"][0.05], w["segn"][0.075], w["segn"][0.10], w["segn"][0.15], w["segn"][0.20],
            w["share"], w["share_alt"], w["n_big_edges"], w["n_knife_edges"], w["type"]))

    # 边界敏感窗
    P("")
    P("== 边界敏感点 ==")
    n_sens = 0
    for w in windows:
        B = w["B"][0.10]
        msgs = []
        if w["changed"] and not (25.0 <= B < 99.0) and 24.0 <= B < 25.5:
            msgs.append("B010 贴下界外 %.4f" % B)
        if w["changed"] and not (25.0 <= B < 99.0) and 98.5 <= B < 99.5:
            msgs.append("B010 贴上界外 %.4f" % B)
        if w["changed"] and 25.0 <= B < 25.5:
            msgs.append("B010 贴下界内 %.4f" % B)
        if w["changed"] and 98.5 <= B < 99.0:
            msgs.append("B010 贴上界内 %.4f" % B)
        if 0 < w["gap_sum"] <= 0.2:
            msgs.append("gap_sum 微小 %.6f" % w["gap_sum"])
        if w["n_knife_edges"] > 0:
            msgs.append("有 %d 个 9.5ms 到 10ms 边沿" % w["n_knife_edges"])
        if w["share"] is not None and 0.38 <= w["share"] <= 0.42:
            msgs.append("share 贴 0.40: %.4f" % w["share"])
        if w["share"] is not None and 0.78 <= w["share"] <= 0.82:
            msgs.append("share 贴 0.80: %.4f" % w["share"])
        if w["type"] != w["type_alt"]:
            msgs.append("分型对分母口径敏感: share=%.4f share_alt=%.4f (%s 改判 %s)" % (
                w["share"], w["share_alt"], w["type"], w["type_alt"]))
        if msgs:
            n_sens = n_sens + 1
            P("  SENS %-40s in_target=%s : %s" % (w["label"], w in target, "; ".join(msgs)))
    P("（无输出行即无边界敏感点）n_sens=%d" % n_sens)

    # ============ 结论 A ============
    P("")
    P("== 结论 A 核验 ==")
    cnt = Counter(w["type"] for w in target)
    P("目标批分型计数: single(share>0.80)=%d  multi(share<0.40)=%d  mid(0.40<=share<=0.80)=%d  合计=%d" % (
        cnt.get("single", 0), cnt.get("multi", 0), cnt.get("mid", 0), len(target)))
    P("任务书预期: single=13, multi=11（合计 24，另 1 窗应落于中段 40%~80%）")
    for w in sorted(target, key=lambda x: x["share"] if x["share"] is not None else -1):
        P("  %-40s share=%.4f type=%s segs010=%d" % (w["label"], w["share"], w["type"], w["segs010_n"]))

    # ============ 结论 B ============
    P("")
    P("== 结论 B 阈值扫描 ==")
    P("单段簇（single）逐窗段数:")
    P("%-40s %6s %6s %6s %6s %6s" % ("window", "T05", "T075", "T10", "T15", "T20"))
    single_max = 0; single_by_T = defaultdict(list)
    for w in sorted([x for x in target if x["type"] == "single"], key=lambda x: (x["trip"], x["wn"])):
        P("%-40s %6d %6d %6d %6d %6d" % (w["label"], w["segn"][0.05], w["segn"][0.075],
                                          w["segn"][0.10], w["segn"][0.15], w["segn"][0.20]))
        for T in THS:
            single_by_T[T].append(w["segn"][T]); single_max = max(single_max, w["segn"][T])
    P("单段簇段数最大值(全阈值): %d" % single_max)
    P("单段簇各阈值段数(min,max): %s" % {("%.3f" % T): (min(v), max(v)) for T, v in sorted(single_by_T.items())})

    P("")
    P("多次簇（multi）逐窗段数:")
    multi_by_T = defaultdict(list)
    for w in sorted([x for x in target if x["type"] == "multi"], key=lambda x: (x["trip"], x["wn"])):
        P("%-40s %6d %6d %6d %6d %6d" % (w["label"], w["segn"][0.05], w["segn"][0.075],
                                          w["segn"][0.10], w["segn"][0.15], w["segn"][0.20]))
        for T in THS:
            multi_by_T[T].append(w["segn"][T])
    P("多次簇各阈值段数(min,max): %s" % {("%.3f" % T): (min(v), max(v)) for T, v in sorted(multi_by_T.items())})
    P("任务书预期: multi 簇 T=0.05 约 211-267 段；T=0.20 塌成 0-5 段甚至归零。")

    if any(x["type"] == "mid" for x in target):
        P("")
        P("中段窗（mid）逐窗段数:")
        for w in sorted([x for x in target if x["type"] == "mid"], key=lambda x: (x["trip"], x["wn"])):
            P("%-40s %6d %6d %6d %6d %6d  share=%.4f" % (w["label"], w["segn"][0.05], w["segn"][0.075],
                w["segn"][0.10], w["segn"][0.15], w["segn"][0.20], w["share"]))

    # 机制侧检：multi 窗计入段的 f 值序列特征（振荡/单调）
    P("")
    P("== multi 窗机制侧检（T=0.1 计入段的 f 序列） ==")
    for w in sorted([x for x in target if x["type"] == "multi"], key=lambda x: (x["trip"], x["wn"])):
        big = [r for r in w["runs"] if r[0] > 0.10]
        fvals = [r[1] for r in big]
        dsc = sum(1 for i in range(1, len(fvals)) if fvals[i] < fvals[i-1])
        asc = sum(1 for i in range(1, len(fvals)) if fvals[i] > fvals[i-1])
        eqv = sum(1 for i in range(1, len(fvals)) if fvals[i] == fvals[i-1])
        P("  %-40s nseg=%d distinct_f=%d min=%s max=%s asc=%d desc=%d eq=%d head=%s" % (
            w["label"], len(big), len(set(fvals)), min(fvals), max(fvals), asc, dsc, eqv,
            [int(v) for v in fvals[:16]]))

    # ============ 结论 C ============
    P("")
    P("== 结论 C 共线性核验 ==")
    by_trip = defaultdict(list)
    for w in target:
        by_trip[w["trip"]].append(w)
    P("目标批覆盖趟数: %d（任务书预期 18）" % len(by_trip))
    single_trips = sorted({w["trip"] for w in target if w["type"] == "single"})
    multi_trips = sorted({w["trip"] for w in target if w["type"] == "multi"})
    mid_trips = sorted({w["trip"] for w in target if w["type"] == "mid"})
    P("single 簇趟数: %d -> %s" % (len(single_trips), single_trips))
    P("multi  簇趟数: %d -> %s" % (len(multi_trips), multi_trips))
    P("mid    簇趟数: %d -> %s" % (len(mid_trips), mid_trips))
    inter_sm = sorted(set(single_trips) & set(multi_trips))
    P("single 与 multi 趟交集: %s" % (inter_sm if inter_sm else "空（两簇不共享任何趟）"))
    one_per = all(sum(1 for w in by_trip[tp] if w["type"] == "single") == 1 for tp in single_trips)
    P("single 簇每趟恰 1 窗: %s" % one_per)
    mixed = []
    for tp in sorted(by_trip):
        types = sorted({w["type"] for w in by_trip[tp]})
        tag = "MIXED!" if len(types) > 1 else ""
        P("  趟 %-24s 窗数=%d 分型=%s %s" % (tp if tp else "(ROOT)", len(by_trip[tp]), types, tag))
        if len(types) > 1:
            mixed.append(tp)
    P("混型趟（同一趟内分型不一致）: %s" % (mixed if mixed else "无（零例外）"))

    # ============ 汇总 ============
    P("")
    P("== 汇总判定（脚本自动行） ==")
    single_stable = all(max(v) <= 6 for v in single_by_T.values()) if single_by_T else False
    multi_collapse = False
    if multi_by_T:
        v20 = multi_by_T[0.20]
        multi_collapse = sum(1 for c in v20 if c <= 5) >= 0.5 * len(v20)
    P("SINGLE_CLUSTER_STABLE=%s (max_segs_all_T=%d)" % (single_stable, single_max))
    if multi_by_T:
        P("MULTI_T005_MIN=%d MULTI_T005_MAX=%d" % (min(multi_by_T[0.05]), max(multi_by_T[0.05])))
        P("MULTI_T020_MIN=%d MULTI_T020_MAX=%d LE5_AT_T020=%d OF %d" % (
            min(multi_by_T[0.20]), max(multi_by_T[0.20]),
            sum(1 for c in multi_by_T[0.20] if c <= 5), len(multi_by_T[0.20])))
        P("MULTI_T015_MIN=%d MULTI_T015_MAX=%d" % (min(multi_by_T[0.15]), max(multi_by_T[0.15])))
    P("SINGLE_N=%d MULTI_N=%d MID_N=%d TARGET_N=%d VALID_N=%d" % (
        cnt.get("single", 0), cnt.get("multi", 0), cnt.get("mid", 0), len(target), len(windows)))
    P("TRIPS_TOTAL=%d SINGLE_TRIPS=%d MULTI_TRIPS=%d MID_TRIPS=%d MIXED=%s INTERSECTION=%s" % (
        len(by_trip), len(single_trips), len(multi_trips), len(mid_trips),
        mixed if mixed else "无", inter_sm if inter_sm else "空"))

    # 唯一写出点：限定在允许目录内
    resolved_out = OUTPATH.resolve()
    resolved_out.relative_to(ALLOW_WRITE_DIR)
    with open(resolved_out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out_lines) + "\n")
    print("written:", resolved_out)

if __name__ == "__main__":
    main()
