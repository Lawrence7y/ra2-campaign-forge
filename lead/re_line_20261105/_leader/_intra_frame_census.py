# -*- coding: utf-8 -*-
"""§602 补全：15 个 500 Hz 窗口的**帧内结构**全量普查。

问题：一帧慢的时候，是整帧均匀慢，还是某个瞬间卡住？

指标（每窗）：
  span     = 帧内首末读数时间差（ms）
  maxgap   = 帧内相邻读数间隔的最大值（ms）  ← 「最长无读数空档」
  ratio    = maxgap / span                   ← ★ 关键指标
  medgap   = 帧内读数间隔中位数（ms）        ← 应接近 2.0 ms（500 Hz）
  nreads   = 每帧读数个数

判读：
  ratio 小（<0.2）  ⇒ 均匀慢（没有单点长阻塞）
  ratio 大（>0.5）  ⇒ 存在单点长阻塞（某一瞬间卡住）

零真机、零注入；只读既有 measure_w*.json。
"""
import collections
import glob
import io
import json
import os
import statistics

ROOT = r"D:\Project\ra2-campaign-forge"
OUT = []


def P(*a):
    s = " ".join(str(x) for x in a)
    OUT.append(s)
    print(s)


def analyze(path):
    d = json.load(io.open(path, encoding="utf-8"))
    s = d["samples"]
    f, t = s["f"], s["t"]
    # 单调性自检
    back = sum(1 for i in range(1, len(f)) if f[i] < f[i - 1])
    jumps = sum(1 for i in range(1, len(f)) if f[i] - f[i - 1] > 1)
    groups = collections.defaultdict(list)
    for fi, ti in zip(f, t):
        groups[fi].append(ti)
    spans, maxgaps, medgaps, nreads = [], [], [], []
    for fi in sorted(groups):
        ts = sorted(groups[fi])
        if len(ts) < 3:
            continue
        gaps = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]
        spans.append((ts[-1] - ts[0]) * 1000.0)
        maxgaps.append(max(gaps) * 1000.0)
        medgaps.append(statistics.median(gaps) * 1000.0)
        nreads.append(len(ts))
    return {
        "path": path,
        "p50": (d.get("stats") or {}).get("frame_ms_p50"),
        "n_reads": len(f),
        "back": back,
        "jumps": jumps,
        "frames": len(spans),
        "span": statistics.median(spans) if spans else None,
        "maxgap": statistics.median(maxgaps) if maxgaps else None,
        "medgap": statistics.median(medgaps) if medgaps else None,
        "nreads": statistics.median(nreads) if nreads else None,
        "ratio": (statistics.median(maxgaps) / statistics.median(spans))
        if spans and maxgaps and statistics.median(spans) > 0
        else None,
        # 逐帧 ratio 的分布（不只看中位）
        "ratio_p50": statistics.median(
            [(g / sp) for g, sp in zip(maxgaps, spans) if sp > 0]
        )
        if spans
        else None,
        "ratio_p95": sorted(
            [(g / sp) for g, sp in zip(maxgaps, spans) if sp > 0]
        )[int(0.95 * len(spans)) - 1]
        if spans
        else None,
        "ratio_max": max([(g / sp) for g, sp in zip(maxgaps, spans) if sp > 0])
        if spans
        else None,
    }


P("=" * 100)
P("§602 补全：15 个 500 Hz 窗口的帧内结构全量普查")
P("=" * 100)

rows = []
for p in sorted(glob.glob(os.path.join(ROOT, "lead", "**", "measure_w*.json"), recursive=True)):
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        continue
    if d.get("verdict") != "ok":
        continue
    hz = (d.get("stats") or {}).get("hz_effective")
    if not hz or hz < 100:
        continue
    r = analyze(p)
    r["hz"] = hz
    rows.append(r)

P("\n[0] 合格窗口 = %d 个" % len(rows))

P("\n[1] 逐窗结果（按 frame_ms_p50 升序 = 从快到慢）")
P(
    "  %-40s %8s %7s %8s %8s %8s %8s  %7s %7s %6s"
    % ("window", "p50(ms)", "frames", "span", "maxgap", "medgap", "每帧读数", "r_p50", "r_p95", "r_max")
)
for r in sorted(rows, key=lambda x: x["p50"] or 0):
    tag = os.path.basename(os.path.dirname(r["path"])) + "/" + os.path.basename(r["path"])[9:12]
    P(
        "  %-40s %8.1f %7d %8.1f %8.1f %8.2f %8.1f  %7.3f %7.3f %6.3f"
        % (
            tag, r["p50"], r["frames"], r["span"], r["maxgap"], r["medgap"],
            r["nreads"], r["ratio_p50"], r["ratio_p95"], r["ratio_max"],
        )
    )

P("\n[2] 汇总统计")
slow = [r for r in rows if r["p50"] and r["p50"] > 60]
fast = [r for r in rows if r["p50"] and r["p50"] <= 60]
P("  慢窗（p50 > 60ms）= %d 个；快窗（<= 60ms）= %d 个" % (len(slow), len(fast)))
for name, grp in (("慢窗", slow), ("快窗", fast), ("全部", rows)):
    if not grp:
        continue
    rp50 = [r["ratio_p50"] for r in grp]
    rp95 = [r["ratio_p95"] for r in grp]
    rmax = [r["ratio_max"] for r in grp]
    P(
        "  %s: ratio_p50 中位=%.4f（范围 %.4f–%.4f）｜ratio_p95 最大=%.4f｜ratio_max 最大=%.4f"
        % (name, statistics.median(rp50), min(rp50), max(rp50), max(rp95), max(rmax))
    )

P("\n[3] 单调性自检（f 是否每读 +1、从不回退）")
bad = [r for r in rows if r["back"] != 0 or r["jumps"] != 0]
P("  回退或跳变的窗口数 = %d / %d" % (len(bad), len(rows)))
for r in bad:
    P("    %s back=%d jumps=%d" % (r["path"], r["back"], r["jumps"]))

P("\n[4] 读数间隔中位（应接近 2.0 ms = 500 Hz）")
mg = [r["medgap"] for r in rows]
P("  全窗 medgap：中位=%.3f ms，范围 %.3f–%.3f ms" % (statistics.median(mg), min(mg), max(mg)))

P("\n" + "=" * 100)
P("判定")
P("=" * 100)
overall_p95 = max(r["ratio_p95"] for r in rows)
overall_max = max(r["ratio_max"] for r in rows)
P("  全部 15 窗：ratio_p50 的中位 = %.4f" % statistics.median([r["ratio_p50"] for r in rows]))
P("  最坏的 ratio_p95 = %.4f ；最坏的 ratio_max（单帧）= %.4f" % (overall_p95, overall_max))
if overall_p95 < 0.30:
    P("  ⇒ **15/15 窗口的 ratio_p95 都 < 0.30** ⇒ 「慢帧是单点长阻塞」在**全部合格语料上不成立**")
    P("  ⇒ 慢帧形态 = **均匀慢**（工作均匀铺满整帧）")
else:
    P("  ⇒ 存在 ratio_p95 >= 0.30 的窗口，需逐个看是否单点阻塞")
P("")
P("  ⚠ 分辨率边界：500 Hz ⇒ 只能排除 >= ~3 ms 量级的单次阻塞，排除不了亚毫秒级高频小阻塞。")
P("  ⚠ 已排除 < 3 帧的窗口（无法算间隔中位）。")
P("  ⚠ `t` 是采样线程读计数器的时间，不是引擎内部时间。")

io.open(os.path.join(ROOT, r"lead\re_line_20261105\_leader\_intra_frame_census_out.txt"),
        "w", encoding="utf-8").write("\n".join(OUT) + "\n")
P("\nDONE")
