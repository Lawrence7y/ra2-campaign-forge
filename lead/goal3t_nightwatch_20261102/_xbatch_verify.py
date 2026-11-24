#!/usr/bin/env python -I -X utf8
# -*- coding: utf-8 -*-
"""异族独立核验器：只读 measure_w*.json，自行实现 Pearson/Spearman/口径B。"""
import json
import math
import os

ROOT = "D:\\Project\\ra2-campaign-forge\\out\\re_work\\work_chain\\CONTINUE_20261003\\lead\\qc161_u0400_trip"
T = 0.1


def pearson(x, y):
    n = len(x)
    if n < 2:
        return float("nan")
    mx = sum(x) / n
    my = sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    if sxx <= 0 or syy <= 0:
        return float("nan")
    return sxy / math.sqrt(sxx * syy)


def rankdata(v):
    n = len(v)
    order = sorted(range(n), key=lambda i: v[i])
    r = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(x, y):
    if len(x) < 2:
        return float("nan")
    return pearson(rankdata(x), rankdata(y))


def analyze(t, f):
    span = t[-1] - t[0]
    n = len(t)
    segs = []
    i = 0
    while i < n:
        j = i
        while j + 1 < n and f[j + 1] == f[i]:
            j += 1
        segs.append((i, j))
        i = j + 1
    counted = []
    for (i, j) in segs:
        d = t[j] - t[i]
        if d > T:
            counted.append(d)
    stall_sum = sum(counted)
    Bpct = 100.0 * stall_sum / span if span > 0 else float("nan")
    edges = [k for k in range(1, n) if f[k] != f[k - 1]]
    moving = len(edges) > 0
    lastEdge = edges[-1] if edges else None
    freezeStart = (t[lastEdge] - t[0]) if lastEdge is not None else None
    longest = max(counted) if counted else 0.0
    longest_share = (longest / stall_sum) if stall_sum > 0 else float("nan")
    single_dom = bool(len(counted) > 0 and longest_share > 0.80 and Bpct >= 25.0)
    gap = 0.0
    for k in edges:
        d = t[k] - t[k - 1]
        if d > 0.010:
            gap += d
    gap_pct = 100.0 * gap / span if span > 0 else float("nan")
    df = (f[lastEdge] - f[0]) if lastEdge is not None else None
    fps_pre = (df / freezeStart) if (lastEdge is not None and freezeStart and freezeStart > 0) else float("nan")
    return dict(span=span, n=n, nsegs=len(segs), ncounted=len(counted), stall_sum=stall_sum,
                Bpct=Bpct, moving=moving, lastEdge=lastEdge, freezeStart=freezeStart,
                longest=longest, longest_share=longest_share, single_dom=single_dom,
                gap_pct=gap_pct, df=df, fps_pre=fps_pre, edges=edges)


def counter_nearest(counters, t_target, field):
    if not counters:
        return None
    best = min(counters, key=lambda c: abs(float(c.get("t_rel", 0.0)) - t_target))
    return best.get(field)


def collect_files(root):
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for fn in sorted(filenames):
            if fn.startswith("measure_w") and fn.endswith(".json"):
                found.append(os.path.join(dirpath, fn))
    return sorted(found)


def load_windows(root):
    paths = collect_files(root)
    wins = []
    skipped = []
    for p in paths:
        rel = os.path.basename(os.path.dirname(p)) + "/" + os.path.basename(p)
        try:
            with open(p, "r", encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception as e:
            skipped.append((rel, "parse:%s" % e))
            continue
        s = d.get("samples")
        if not isinstance(s, dict) or "t" not in s or "f" not in s:
            skipped.append((rel, "no samples"))
            continue
        t, f = s["t"], s["f"]
        if len(t) < 2 or len(f) < 2:
            skipped.append((rel, "len t=%d f=%d" % (len(t), len(f))))
            continue
        if len(t) != len(f):
            skipped.append((rel, "len mismatch t=%d f=%d" % (len(t), len(f))))
            continue
        wins.append(dict(rel=rel, window=d.get("window"), units0=(d.get("gate") or {}).get("units0"),
                         counters=d.get("counters") or [],
                         t=[float(x) for x in t], f=[int(x) for x in f]))
    return wins, skipped, paths


def main():
    wins, skipped, paths = load_windows(ROOT)
    out = []
    P = out.append
    P("=" * 78)
    P("BATCH XVERIFY - 异族独立复算")
    P("=" * 78)
    P("数据根: " + ROOT)
    P("命中文件数(measure_w*.json) = %d" % len(paths))
    P("有效窗(samples 存在且 len(t)>=2) = %d" % len(wins))
    P("剔除件 = %d" % len(skipped))
    for s in skipped:
        P("   - %s  (%s)" % s)

    for w in wins:
        w["m"] = analyze(w["t"], w["f"])
    moving = [w for w in wins if w["m"]["moving"]]
    P("")
    P("有推进窗(moving) = %d / %d" % (len(moving), len(wins)))

    P("")
    P("-" * 78)
    P("C1  units0 vs B%  (moving 窗)")
    P("-" * 78)
    xs = [float(w["units0"]) for w in moving if w["units0"] is not None]
    ys = [w["m"]["Bpct"] for w in moving if w["units0"] is not None]
    c1p = pearson(xs, ys)
    c1s = spearman(xs, ys)
    P("n=%d  Pearson r = %.6f   Spearman rho = %.6f" % (len(xs), c1p, c1s))
    P("申诉值: r=-0.2005  rho=-0.1706")
    c1_ok = (abs(c1p + 0.2005) <= 5e-4) and (abs(c1s + 0.1706) <= 5e-4)
    P("偏差: dr=%+.6f  drho=%+.6f" % (c1p + 0.2005, c1s + 0.1706))
    P("判定: %s" % ("MATCH" if c1_ok else "MISMATCH"))

    P("")
    P("-" * 78)
    P("C2  时间相位 vs B%")
    P("-" * 78)
    c2 = {}
    for label, sub in (("moving 主报", moving), ("all-valid 参考", wins)):
        wv = [float(w["window"]) for w in sub if w["window"] is not None]
        bv = [w["m"]["Bpct"] for w in sub if w["window"] is not None]
        tv = [w["t"][0] for w in sub if w["window"] is not None]
        bb = [w["m"]["Bpct"] for w in sub if w["window"] is not None]
        a = spearman(wv, bv)
        b = spearman(tv, bb)
        c2[label] = (a, b)
        P("[%s] n=%d  rho(window,B%%) = %.6f   rho(t[0],B%%) = %.6f" % (label, len(wv), a, b))
    c2ph, c2up = c2["moving 主报"]
    c2_ok = (abs(c2ph + 0.0403) <= 5e-4) and (abs(c2up - 0.0395) <= 5e-4)
    P("申诉值: rho(window)=-0.0403  rho(t0)=+0.0395")
    P("偏差: dwindow=%+.6f  dt0=%+.6f" % (c2ph + 0.0403, c2up - 0.0395))
    P("判定: %s" % ("MATCH" if c2_ok else "MISMATCH"))

    sd = [w for w in moving if w["m"]["single_dom"]]
    sd_n0 = [w for w in sd if w["f"][0] != 0]
    sd_z0 = [w for w in sd if w["f"][0] == 0]
    P("")
    P("-" * 78)
    P("单段主导子集 = %d   (f[0]!=0: %d ; f[0]==0: %d)" % (len(sd), len(sd_n0), len(sd_z0)))
    P("-" * 78)
    for w in sd:
        P("   %-40s w=%s f0=%-6d fLast=%-6d span=%8.3f B%%=%8.4f fs=%8.5f share=%.5f ncount=%d"
          % (w["rel"], w["window"], w["f"][0], w["f"][-1], w["m"]["span"], w["m"]["Bpct"],
             w["m"]["freezeStart"], w["m"]["longest_share"], w["m"]["ncounted"]))

    P("")
    P("-" * 78)
    P("C3  冻结前帧率=(f[lastEdge]-f[0])/freezeStart ; rho(freezeStart, df)")
    P("-" * 78)
    rates = []
    for w in sd_n0:
        r = w["m"]["fps_pre"]
        rates.append((r, w))
        flag = "" if (31.1 <= r <= 34.0) else "   <<< OUT OF [31.1,34.0]"
        P("   %-40s w=%s  df=%-6s fs=%8.5f  rate=%.6f%s"
          % (w["rel"], w["window"], w["m"]["df"], w["m"]["freezeStart"], r, flag))
    rmin = min(r for r, _ in rates) if rates else float("nan")
    rmax = max(r for r, _ in rates) if rates else float("nan")
    P("rate min=%.6f  max=%.6f  n=%d" % (rmin, rmax, len(rates)))
    out_of = [(w["rel"], r) for r, w in rates if not (31.1 <= r <= 34.0)]
    P("超界窗数 = %d" % len(out_of))
    for rel, r in out_of:
        P("   OUT: %s rate=%.6f" % (rel, r))
    fs_list = [w["m"]["freezeStart"] for w in sd_n0]
    df_list = [w["m"]["df"] for w in sd_n0]
    c3rho = spearman(fs_list, df_list)
    P("rho(freezeStart, df) = %.8f  n=%d" % (c3rho, len(fs_list)))
    pairs = sorted(zip(fs_list, df_list))
    P("按 freezeStart 升序的 (fs, df):")
    for a, b in pairs:
        P("   %10.6f -> %s" % (a, b))
    nondec = all(pairs[i][1] <= pairs[i + 1][1] for i in range(len(pairs) - 1))
    noninc = all(pairs[i][1] >= pairs[i + 1][1] for i in range(len(pairs) - 1))
    P("非降=%s  非增=%s  => 单调=%s" % (nondec, noninc, nondec or noninc))
    strict = all(pairs[i][1] < pairs[i + 1][1] for i in range(len(pairs) - 1)) or \
             all(pairs[i][1] > pairs[i + 1][1] for i in range(len(pairs) - 1))
    P("严格单调=%s" % strict)
    breaks = [(pairs[i], pairs[i + 1]) for i in range(len(pairs) - 1)
              if (pairs[i][1] < pairs[i + 1][1]) and (pairs[i + 1][1] < pairs[i][1])]
    P("单调破坏对 = %d" % len(breaks))
    for b in breaks:
        P("   BREAK %s -> %s" % (b[0], b[1]))
    c3_ok = (len(out_of) == 0) and (abs(c3rho - 1.0) <= 1e-9)
    P("判定: %s" % ("MATCH" if c3_ok else "MISMATCH"))

    P("")
    P("-" * 78)
    P("C4  freezeStart 与候选量 Spearman (f[0]!=0 单段主导, n=%d)" % len(sd_n0))
    P("-" * 78)
    rows = []
    for w in sd_n0:
        c = w["counters"]
        fs = w["m"]["freezeStart"]
        t_end = w["t"][-1]
        idx = None
        for k in range(len(w["t"]) - 1, -1, -1):
            if w["t"][k] <= t_end - 1.0:
                idx = k
                break
        if idx is None:
            rate1 = None
        else:
            dt = t_end - w["t"][idx]
            rate1 = (w["f"][-1] - w["f"][idx]) / dt if dt > 0 else None
        wsf = counter_nearest(c, fs, "ws_kb")
        ws0 = counter_nearest(c, 0.0, "ws_kb")
        rows.append(dict(rel=w["rel"], w=w["window"], freezeStart=fs,
                         units0=float(w["units0"]) if w["units0"] is not None else None,
                         units_at_freeze=counter_nearest(c, fs, "units"),
                         techno_at_freeze=counter_nearest(c, fs, "techno"),
                         f_at_freeze=w["f"][w["m"]["lastEdge"]],
                         f_rate_last1s=rate1,
                         ws_at_freeze=wsf,
                         ws_delta_freeze=(wsf - ws0) if (wsf is not None and ws0 is not None) else None))
    CANDS = ["units0", "units_at_freeze", "techno_at_freeze", "f_at_freeze",
             "f_rate_last1s", "ws_at_freeze", "ws_delta_freeze"]
    strong = []
    P("   %-20s %12s %6s" % ("candidate", "rho", "n"))
    for cn in CANDS:
        pr = [(r[cn], r["freezeStart"]) for r in rows if r.get(cn) is not None]
        if len(pr) < 3:
            P("   %-20s %12s %6d  (样本不足)" % (cn, "n/a", len(pr)))
            continue
        rho = spearman([a for a, _ in pr], [b for _, b in pr])
        P("   %-20s %12.6f %6d" % (cn, rho, len(pr)))
        if abs(rho) >= 0.6:
            strong.append((cn, round(rho, 6)))
    P("   |rho|>=0.6 的候选量 = %s" % (strong if strong else "NONE"))
    c4_ok = (len(strong) == 0)
    P("判定: %s" % ("MATCH" if c4_ok else "MISMATCH"))

    P("")
    P("-" * 78)
    P("C5  |B% - 100*(span-freezeStart)/span| < 0.01")
    P("-" * 78)
    fnz_ok = fnz_tot = 0
    fz_ok = fz_tot = 0
    c5_bad = []
    for w in sd:
        m = w["m"]
        pred = 100.0 * (m["span"] - m["freezeStart"]) / m["span"]
        dev = abs(m["Bpct"] - pred)
        ok = dev < 0.01
        if w["f"][0] != 0:
            fnz_tot += 1
            if ok:
                fnz_ok += 1
            else:
                c5_bad.append((w["rel"], w["window"], m["Bpct"], pred, dev, "f0!=0 应成立却不成立"))
            P("   f0!=0 %-38s w=%s  B%%=%10.5f  pred=%10.5f  dev=%.6f  %s"
              % (w["rel"], w["window"], m["Bpct"], pred, dev, "OK" if ok else "FAIL"))
        else:
            fz_tot += 1
            if ok:
                fz_ok += 1
                c5_bad.append((w["rel"], w["window"], m["Bpct"], pred, dev, "f0==0 应不成立却成立"))
            P("   f0==0 %-38s w=%s  B%%=%10.5f  pred=%10.5f  dev=%.6f  %s"
              % (w["rel"], w["window"], m["Bpct"], pred, dev, "HOLDS(!)" if ok else "not-hold"))
    P("f[0]!=0 成立 %d/%d   f[0]==0 成立 %d/%d (期望 0)" % (fnz_ok, fnz_tot, fz_ok, fz_tot))
    c5_ok = (fnz_ok == 12) and (fnz_tot == 12) and (fz_ok == 0) and (fz_tot == 3)
    P("判定: %s" % ("MATCH" if c5_ok else "MISMATCH"))

    P("")
    P("=" * 78)
    P("SUMMARY  C1=%s C2=%s C3=%s C4=%s C5=%s" % (
        "MATCH" if c1_ok else "MISMATCH", "MATCH" if c2_ok else "MISMATCH",
        "MATCH" if c3_ok else "MISMATCH", "MATCH" if c4_ok else "MISMATCH",
        "MATCH" if c5_ok else "MISMATCH"))
    P("validWindows=%d movingWindows=%d singleDomain=%d" % (len(wins), len(moving), len(sd)))
    P("=" * 78)
    print("\n".join(out))


if __name__ == "__main__":
    main()
