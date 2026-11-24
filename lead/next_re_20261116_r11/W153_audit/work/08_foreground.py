# -*- coding: utf-8 -*-
"""步骤8：混杂因素溯源
- win_foreground 与 ms/frame 的关系（含"零子弹慢趟" W94_batchrun 的专项检查）
- 采样间隔 interval_ms_actual 是否在那些趟里变了（若变了，Δt/Δframe 本身仍对，但对象状态不同）
"""
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w153_common as C

OUT = []
FIELDS = ("seq", "t_perf_ns", "frame", "A8ED50", "B0CE88", "X87E8E0", "mode", "step",
          "read_status", "interval_ms_actual", "win_foreground", "win_cpu_ms", "win_tid")


def main():
    files = C.all_files()
    per_trip = {}
    for p in files:
        rows = []
        n_total = 0
        fg = Counter()
        ima = []
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                if o.get("kind") != "sample":
                    continue
                n_total += 1
                fg[o.get("win_foreground")] += 1
                if o.get("interval_ms_actual") is not None:
                    ima.append(o["interval_ms_actual"])
                if len(rows) < 10 ** 9 and o.get("t_perf_ns") and o.get("frame") is not None:
                    rows.append((o["t_perf_ns"] * 1e-9, o["frame"], o.get("A8ED50"),
                                 o.get("win_foreground"), o.get("mode")))
        if len(rows) < 100:
            continue
        rows.sort()
        t0 = rows[0][0]
        # 按 10 s 窗口 + 前景状态分组
        buck = defaultdict(list)
        for t, fr, a8, f, mo in rows:
            buck[int((t - t0) // 10.0)].append((t, fr, a8, f, mo))
        w = []
        for k in sorted(buck):
            seg = buck[k]
            if len(seg) < 2:
                continue
            dt = (seg[-1][0] - seg[0][0]) * 1000.0
            df = seg[-1][1] - seg[0][1]
            if df <= 0 or dt < 9000:
                continue
            fg_true = sum(1 for s in seg if s[3] is True)
            w.append(dict(win=k, ms=dt / df, a8=C.mean([s[2] for s in seg if s[2] is not None]) or 0,
                          fg_frac=fg_true / len(seg), dframe=df, mode=seg[0][4]))
        per_trip[C.trip_name(p)] = dict(
            rel=C.trip_rel(p), n=n_total,
            fg_none=(fg.get(None, 0) / n_total if n_total else None),
            fg_false=(fg.get(False, 0) / n_total if n_total else None),
            fg_true=(fg.get(True, 0) / n_total if n_total else None),
            ima_med=C.median(ima), ima_p10=C.quantile(ima, 0.1), ima_p90=C.quantile(ima, 0.9),
            wins=w)

    OUT.append("=== A. 全部趟的 win_foreground 覆盖与采样间隔 ===")
    OUT.append("  %-34s %7s %9s %9s %9s %8s" % ("trip", "n样本", "fg=True%", "fg=False%", "无fg字段%", "ima中位"))
    for t in sorted(per_trip):
        d = per_trip[t]
        OUT.append("  %-34s %7d %8s %8s %8s %8.2f" % (
            t[:34], d["n"],
            ("%.1f" % (100 * d["fg_true"])) if d["fg_true"] is not None else "-",
            ("%.1f" % (100 * d["fg_false"])) if d["fg_false"] is not None else "-",
            ("%.1f" % (100 * d["fg_none"])) if d["fg_none"] is not None else "-",
            d["ima_med"] if d["ima_med"] else -1))

    OUT.append("")
    OUT.append("=== B. 按'窗口内前景占比'分组的 ms/frame（只看有 fg 字段的趟）===")
    groups = defaultdict(list)
    for t, d in per_trip.items():
        for w in d["wins"]:
            if d["fg_none"] and d["fg_none"] > 0.5:
                continue
            if w["fg_frac"] >= 0.999:
                g = "100% 前景"
            elif w["fg_frac"] >= 0.5:
                g = "50-99% 前景"
            else:
                g = "<50% 前景"
            groups[g].append((w["ms"], w["a8"], t))
    for g in ("100% 前景", "50-99% 前景", "<50% 前景"):
        v = groups.get(g, [])
        if not v:
            continue
        ms = [x[0] for x in v]
        OUT.append("  %-14s 窗口数=%4d  ms/frame: 中位=%8.2f p90=%8.2f max=%8.2f  其中子弹<25 的窗口 ms 中位=%8s" % (
            g, len(v), C.median(ms), C.quantile(ms, 0.9), max(ms),
            ("%.2f" % C.median([x[0] for x in v if x[1] < 25])) if any(x[1] < 25 for x in v) else "-"))

    OUT.append("")
    OUT.append("=== C. '零子弹慢趟'（W94_batchrun: trip_c1_r1..c4_r*）专项 ===")
    for t in sorted(per_trip):
        if not t.startswith("trip_c") or "_" in t.replace("trip_", "", 1).split("_")[0]:
            continue
        if t.strip("trip_c0123456789_r").strip() not in ("",):
            pass
    targets = [t for t in per_trip if t.startswith("trip_c") and t[6:7].isdigit()]
    for t in sorted(targets):
        d = per_trip[t]
        OUT.append("  %-16s n=%6d fgTrue=%8s fgFalse=%8s fgNone=%8s ima中位=%7.2f 窗口ms中位=%8s" % (
            t, d["n"],
            ("%.1f%%" % (100 * d["fg_true"])) if d["fg_true"] is not None else "-",
            ("%.1f%%" % (100 * d["fg_false"])) if d["fg_false"] is not None else "-",
            ("%.1f%%" % (100 * d["fg_none"])) if d["fg_none"] is not None else "-",
            d["ima_med"] or -1,
            ("%.2f" % C.median([w["ms"] for w in d["wins"]])) if d["wins"] else "-"))

    txt = "\n".join(OUT)
    print(txt)
    C.write_evidence("08_foreground.txt", txt)

    cols = ["trip", "rel", "n", "fg_true", "fg_false", "fg_none", "ima_med", "ima_p10", "ima_p90"]
    p = os.path.join(C.EVID, "fg_per_trip.tsv")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("\t".join(cols) + "\n")
        for t, d in sorted(per_trip.items()):
            fh.write("\t".join(str(d.get(c)) if d.get(c) is not None else "" for c in cols) + "\n")


if __name__ == "__main__":
    main()
