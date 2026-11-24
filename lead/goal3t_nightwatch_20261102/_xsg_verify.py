# -*- coding: utf-8 -*-
# 独立核验员（异族）自写实现：停滞(B%) vs 帧沿缺口(edge_gap) 可分性检验
# 口径严格照任务书：
#   平台 = f 相同的连续样本；平台时长 = 平台末样本t - 平台首样本t；只计 > 0.1s；
#   B% = 100 * Σ(计入平台时长) / (t[-1]-t[0])
#   帧沿缺口: 仅在 f[i]!=f[i-1] 处取 dt=t[i]-t[i-1]，只累加 > 10ms 的；
#   edge_gap% = 100 * edge_gap_s / (t[-1]-t[0])
#   注意：平台中间的相邻间隔掉拍不计入 edge_gap。
import json
import math
import re
import sys
from pathlib import Path

PROJ = Path(r"D:\Project\ra2-campaign-forge")
DATA = PROJ / "out" / "re_work" / "work_chain" / "CONTINUE_20261003" / "lead" / "qc161_u0400_trip"
OUT_TXT = PROJ / "lead" / "goal3t_nightwatch_20261102" / "_xsg_verify_out.txt"

T_PLATEAU = 0.1      # 平台计入阈值（秒），严格 >
T_EDGE = 0.010       # 帧沿缺口计入阈值（秒），严格 >

FNAME_RE = re.compile(r"^measure_w(.+)\.json$")


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx <= 0 or syy <= 0:
        return float("nan")
    return sxy / math.sqrt(sxx * syy)


def analyze_window(t, f):
    """返回 (B_pct, edge_gap_s, edge_gap_pct, n_frame_changes, n_plateaus_counted, anomalies)"""
    an = []
    n = len(t)
    span = t[-1] - t[0]
    # t 单调性检查
    for i in range(1, n):
        if t[i] <= t[i - 1]:
            an.append("t_non_monotonic@%d" % i)
            break
    # 平台（f 相同的连续样本）
    b_sum = 0.0
    n_pl = 0
    i = 0
    while i < n:
        j = i
        while j + 1 < n and f[j + 1] == f[i]:
            j += 1
        dur = t[j] - t[i]
        if dur > T_PLATEAU:
            b_sum += dur
            n_pl += 1
        i = j + 1
    # 帧沿缺口：只在 f 变化点取 dt
    edge = 0.0
    n_chg = 0
    for i in range(1, n):
        if f[i] != f[i - 1]:
            n_chg += 1
            dt = t[i] - t[i - 1]
            if dt > T_EDGE:
                edge += dt
    B = 100.0 * b_sum / span if span > 0 else float("nan")
    EG = 100.0 * edge / span if span > 0 else float("nan")
    if span <= 0:
        an.append("span<=0")
    return B, edge, EG, n_chg, n_pl, an


def main():
    files = sorted(DATA.rglob("measure_w*.json"))
    rows = []          # 每有效窗一条
    bad = []           # 无效/坏件
    seen_key = {}
    for p in files:
        rel = p.relative_to(DATA)
        trip = "(root)" if len(rel.parts) == 1 else rel.parts[0]
        m = FNAME_RE.match(p.name)
        wlabel = "w" + m.group(1) if m else p.name
        key = (trip, wlabel)
        if key in seen_key:
            bad.append((rel, "duplicate (trip,w)"))
            continue
        seen_key[key] = True
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            bad.append((rel, "json_error:%s" % e))
            continue
        s = d.get("samples")
        if not isinstance(s, dict) or "t" not in s or "f" not in s:
            bad.append((rel, "no_samples"))
            continue
        t, f = s["t"], s["f"]
        if not isinstance(t, list) or not isinstance(f, list) or len(t) != len(f):
            bad.append((rel, "bad_samples_len"))
            continue
        if len(t) < 2:
            bad.append((rel, "len<2"))
            continue
        try:
            t = [float(x) for x in t]
            f = [int(x) for x in f]
        except Exception as e:
            bad.append((rel, "coerce_error:%s" % e))
            continue
        B, edge, EG, nchg, npl, an = analyze_window(t, f)
        verdict = d.get("verdict")
        rows.append({
            "trip": trip, "w": wlabel, "rel": str(rel), "n": len(t),
            "span": t[-1] - t[0], "B": B, "edge": edge, "EG": EG,
            "nchg": nchg, "npl": npl, "verdict": verdict, "an": an,
        })

    valid = [r for r in rows if not math.isnan(r["B"])]
    nanB = [r for r in rows if math.isnan(r["B"])]

    # 全量 Pearson(B%, edge_gap%)，仅取 B 有限的窗
    xs = [r["B"] for r in valid]
    ys = [r["EG"] for r in valid]
    r_all = pearson(xs, ys)

    # 关键子集
    zero_gap = sorted(
        (r for r in valid if r["nchg"] >= 1 and 25.0 <= r["B"] < 99.0 and r["edge"] == 0.0),
        key=lambda r: -r["B"])
    has_gap = sorted(
        (r for r in valid if r["nchg"] >= 1 and 25.0 <= r["B"] < 99.0 and r["edge"] > 0.0),
        key=lambda r: -r["B"])
    fast = [r for r in valid if r["B"] < 2.0]
    fast_edge_sum = sum(r["edge"] for r in fast)

    # 子集内相关（补充证据）
    r_zero = pearson(
        [r["B"] for r in valid if r["nchg"] >= 1 and 25.0 <= r["B"] < 99.0 and r["edge"] == 0.0],
        [r["EG"] for r in valid if r["nchg"] >= 1 and 25.0 <= r["B"] < 99.0 and r["edge"] == 0.0])

    lines = []
    A = lines.append
    A("=== XSG verify (independent re-impl, ikan-verifier) %s ===" % "")
    A("data root: %s" % DATA)
    A("found measure_w*.json (rglob): %d" % len(files))
    A("valid windows (has samples & len>=2 & finite B): %d" % len(valid))
    A("parsed-but-nonfinite-B: %d ; bad/invalid files: %d" % (len(nanB), len(bad)))
    for rel, why in bad:
        A("  BAD: %s -> %s" % (rel, why))
    for r in nanB:
        A("  NAN-B: %s (span=%r)" % (r["rel"], r["span"]))
    A("")
    A("Pearson(B%%, edge_gap%%) over all %d valid windows: %.4f" % (len(valid), r_all))
    A("")
    A("zeroGapMovingHighStall (nchg>=1 & 25<=B<99 & edge_gap_s==0): %d" % len(zero_gap))
    for r in zero_gap:
        A("  %s %s B=%.4f%%" % (r["trip"], r["w"], r["B"]))
    A("")
    A("gapMovingHighStall (nchg>=1 & 25<=B<99 & edge_gap_s>0): %d" % len(has_gap))
    for r in has_gap:
        A("  %s %s B=%.4f%% edge=%.3f s" % (r["trip"], r["w"], r["B"], r["edge"]))
    A("")
    A("fastWindows (B<2%%): %d ; their edge_gap_s sum = %.6f s" % (len(fast), fast_edge_sum))
    A("")
    A("supplementary: Pearson(B%%,edge_gap%%) within zero-gap-high-stall subset: %s"
      % ("n/a" if math.isnan(r_zero) else "%.4f" % r_zero))
    A("")
    A("--- full table (trip w n span_s B% edge_s edge% nchg nplt verdict anomalies) ---")
    for r in sorted(valid, key=lambda r: (r["trip"], r["w"])):
        A("%s %s n=%d span=%.4f B=%.4f edge=%.6f EG=%.4f nchg=%d nplt=%d verdict=%s %s"
          % (r["trip"], r["w"], r["n"], r["span"], r["B"], r["edge"], r["EG"],
             r["nchg"], r["npl"], r["verdict"], ("ANOM:" + ",".join(r["an"])) if r["an"] else ""))
    txt = "\n".join(lines) + "\n"
    OUT_TXT.write_text(txt, encoding="utf-8")
    # stdout 摘要
    sys.stdout.write("\n".join(lines[:len(lines) - len(valid)]) + "\n")
    sys.stdout.write("full table lines: %d -> %s\n" % (len(valid), OUT_TXT))
    # 供主控读取的机器可读行
    print("SUMMARY_JSON=" + json.dumps({
        "files": len(files), "valid": len(valid), "bad": len(bad),
        "pearsonAll": round(r_all, 4) if not math.isnan(r_all) else None,
        "zeroGapMovingHighStall": len(zero_gap),
        "gapMovingHighStall": len(has_gap),
        "fastWindows": len(fast),
        "fastEdgeGapSum": round(fast_edge_sum, 6),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
