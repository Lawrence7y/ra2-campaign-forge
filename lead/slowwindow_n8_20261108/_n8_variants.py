# -*- coding: utf-8 -*-
"""N-8 附加：§604 三分位表的口径搜索——哪种「帧时长/帧内最大空档」定义能复现台账 :9706-9720。

只读 15 个合格窗 measure_w*.json；唯一写域 = 本目录 _n8_variants_out.txt。零真机、零采样。
台账表值（GOAL :9706-9720，硬编码作对照）：
  窗口: 快1/3时长 快1/3空档 慢1/3时长 慢1/3空档
"""
import collections
import glob
import io
import json
import os
import re
import statistics

ROOT = r"D:\Project\ra2-campaign-forge"
HERE = os.path.join(ROOT, "lead", "slowwindow_n8_20261108")
OUT = []


def P(*a):
    OUT.append(" ".join(str(x) for x in a))


LED = {
    "l1c_20261021/w0": (65.8, 2.70, 147.9, 2.73),
    "l1c_20261021/w1": (64.3, 2.68, 154.8, 2.71),
    "l1c_20261021/w2": (62.8, 2.67, 138.3, 2.70),
    "l1d_20261021/w0": (60.2, 2.66, 132.0, 2.71),
    "l1d_20261021/w1": (58.1, 2.65, 136.1, 2.67),
    "l1d_20261021/w2": (39.9, 2.64, 99.3, 2.66),
    "l1e_20261021/w0": (55.1, 2.65, 116.4, 2.65),
    "l1e_20261021/w1": (52.8, 2.63, 115.6, 2.66),
    "l1e_20261021/w2": (39.9, 2.63, 97.8, 2.64),
    "l3_20261021/w0": (73.2, 2.75, 156.6, 2.75),
    "l3_20261021/w1": (50.1, 2.68, 117.5, 2.72),
    "l3_20261021/w2": (62.3, 2.71, 134.9, 2.71),
    "t55k_20261020/w0": (28.9, 2.62, 35.2, 2.60),
    "t55k_20261020/w1": (29.6, 2.61, 34.9, 2.60),
    "t55k_20261020/w2": (29.6, 2.61, 34.8, 2.61),
}

paths = sorted(glob.glob(os.path.join(ROOT, "lead", "**", "measure_w*.json"), recursive=True))
wins = []
for p in paths:
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        continue
    if d.get("verdict") != "ok":
        continue
    hz = (d.get("stats") or {}).get("hz_effective")
    if not hz or hz < 100:
        continue
    wn = re.search(r"measure_w(\d+)\.json$", os.path.basename(p)).group(1)
    tag = os.path.basename(os.path.dirname(p)) + "/w" + wn
    wins.append((tag, d))

# 每窗预计算：f 组首末时间、组内 gaps、edge 时间映射
CACHE = {}
for tag, d in wins:
    s = d["samples"]
    f, t = s["f"], s["t"]
    g = collections.defaultdict(list)
    for fi, ti in zip(f, t):
        g[fi].append(ti)
    fkeys = sorted(g)
    first = {k: min(g[k]) for k in fkeys}
    last = {k: max(g[k]) for k in fkeys}
    within = {k: max(b - a for a, b in zip(sorted(g[k]), sorted(g[k])[1:])) * 1000.0 for k in fkeys}
    nreads = {k: len(g[k]) for k in fkeys}
    edge_t = {int(e[0]): e[1] for e in d["frame_edges"]}
    CACHE[tag] = dict(fkeys=fkeys, first=first, last=last, within=within,
                      nreads=nreads, edge_t=edge_t)


def dur_series(tag, kind):
    c = CACHE[tag]
    fk = c["fkeys"]
    out = {}
    for i, k in enumerate(fk):
        if kind == "span":
            out[k] = (c["last"][k] - c["first"][k]) * 1000.0
        elif kind == "edge":
            if i + 1 < len(fk) and fk[i] in c["edge_t"] and fk[i + 1] in c["edge_t"]:
                out[k] = (c["edge_t"][fk[i + 1]] - c["edge_t"][fk[i]]) * 1000.0
        elif kind == "f2f":
            if i + 1 < len(fk):
                out[k] = (c["first"][fk[i + 1]] - c["first"][k]) * 1000.0
        elif kind == "l2l":
            if i + 1 < len(fk):
                out[k] = (c["last"][fk[i + 1]] - c["last"][k]) * 1000.0
    return out


def gap_series(tag, kind, minreads):
    c = CACHE[tag]
    fk = c["fkeys"]
    out = {}
    for i, k in enumerate(fk):
        if c["nreads"][k] < minreads:
            continue
        g = c["within"][k]
        if kind == "endb" and i + 1 < len(fk):
            g = max(g, (c["first"][fk[i + 1]] - c["last"][k]) * 1000.0)
        elif kind == "startb" and i > 0:
            g = max(g, (c["first"][k] - c["last"][fk[i - 1]]) * 1000.0)
        out[k] = g
    return out


def thirds(tag, dur, gap, kmul):
    keys = [k for k in dur if k in gap]
    items = sorted(((dur[k], gap[k]) for k in keys), key=lambda x: x[0])
    n = len(items)
    k = int(n * kmul) if kmul < 1 else kmul
    fast, slow = items[:k], items[n - k:]
    fd = statistics.median([x[0] for x in fast])
    sd = statistics.median([x[0] for x in slow])
    fg = statistics.median([x[1] for x in fast])
    sg = statistics.median([x[1] for x in slow])
    return fd, fg, sd, sg


P("=" * 110)
P("口径搜索：行 = 定义组合；match = 15 窗 × 4 值在对账容差内的命中数（满分 60）")
P("容差：时长 ±0.05 ms（表值 1 位小数）、空档 ±0.005 ms（表值 2 位小数）")
P("=" * 110)
best = None
for dkind in ("span", "edge", "f2f", "l2l"):
    for gkind in ("within", "endb", "startb"):
        for minreads in (3, 1):
            for kmul in (1 / 3,):
                hit = 0
                details = {}
                for tag in LED:
                    dur = dur_series(tag, dkind)
                    gap = gap_series(tag, gkind, minreads)
                    fd, fg, sd, sg = thirds(tag, dur, gap, kmul)
                    L = LED[tag]
                    ok = (abs(fd - L[0]) <= 0.05 + 1e-9 and abs(fg - L[1]) <= 0.005 + 1e-9 and
                          abs(sd - L[2]) <= 0.05 + 1e-9 and abs(sg - L[3]) <= 0.005 + 1e-9)
                    hit += sum([abs(fd - L[0]) <= 0.05 + 1e-9, abs(fg - L[1]) <= 0.005 + 1e-9,
                                abs(sd - L[2]) <= 0.05 + 1e-9, abs(sg - L[3]) <= 0.005 + 1e-9])
                    details[tag] = (fd, fg, sd, sg)
                label = "dur=%-5s gap=%-7s minreads>=%d k=n//3" % (dkind, gkind, minreads)
                P("%-34s hit=%2d/60  %s" % (label, hit, "<<< FULL MATCH" if hit == 60 else ""))
                if best is None or hit > best[0]:
                    best = (hit, label, details)

P("")
P("=" * 110)
P("最优口径逐窗明细（hit=%d/60, %s）" % (best[0], best[1]))
P("=" * 110)
P("%-22s %18s %18s %10s %10s" % ("window", "实算 快/慢时长", "实算 快/慢空档", "台账时长", "台账空档"))
ratios = []
gds = []
for tag in LED:
    fd, fg, sd, sg = best[2][tag]
    L = LED[tag]
    ratios.append(sd / fd)
    gds.append(sg - fg)
    P("%-22s %8.1f/%8.1f %8.3f/%8.3f %8.1f/%6.1f %6.2f/%5.2f" %
      (tag, fd, sd, fg, sg, L[0], L[2], L[1], L[3]))
P("")
P("最优口径下：倍率中位 = %.4f（台账 :9723 称 2.19）" % statistics.median(ratios))
P("最优口径下：倍率最大窗 = %.4f；慢1/3时长绝对值最大 = %.1f ms" %
  (max(ratios), max(best[2][t][2] for t in LED)))
P("最优口径下：空档差<0 窗数 = %d；范围 = %+.4f .. %+.4f（台账 :9724 称 +0.003~+0.049、:9725 称 3 窗为负）"
  % (sum(1 for x in gds if x < 0), min(gds), max(gds)))

# 台账表自身口径（直接用表值复算汇总）
tr = [LED[t][2] / LED[t][0] for t in LED]
tg = [LED[t][3] - LED[t][1] for t in LED]
P("")
P("直接用台账表值复算：倍率中位 = %.4f；倍率最大 = %s = %.4f；空档差范围 = %+.3f..%+.3f；负值窗数 = %d"
  % (statistics.median(tr),
     max(LED, key=lambda t: LED[t][2] / LED[t][0]), max(tr),
     min(tg), max(tg), sum(1 for x in tg if x < 0)))
P("（台账 :9723 括号称「最大 l3/w0 = 2.14 倍」：l3/w0 表值比 = %.4f，确非最大；"
  "但 l3/w0 慢1/3 时长 %.1f ms 确为全表慢1/3时长最大——「最大」一词两读，倍率读法自相矛盾）"
  % (LED["l3_20261021/w0"][2] / LED["l3_20261021/w0"][0], LED["l3_20261021/w0"][2]))
P("")
P("N8_VARIANTS DONE")

io.open(os.path.join(HERE, "_n8_variants_out.txt"), "w", encoding="utf-8").write("\n".join(OUT) + "\n")
print("\n".join(OUT))
