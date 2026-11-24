# -*- coding: utf-8 -*-
"""N-8 收尾：§603 汇总声明复算 + 语料标准口径（帧内 maxgap、正确配对、edge 时长）下 §604 汇总复算。
只读；唯一写域 = 本目录 _n8_s603_summary_out.txt。零真机、零采样。
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


wins = []
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
    wn = re.search(r"measure_w(\d+)\.json$", os.path.basename(p)).group(1)
    wins.append((os.path.basename(os.path.dirname(p)) + "/w" + wn, p, d))

rows = []
for tag, p, d in wins:
    s = d["samples"]
    f, t = s["f"], s["t"]
    g = collections.defaultdict(list)
    for fi, ti in zip(f, t):
        g[fi].append(ti)
    spans, mgs = [], []
    edge_t = {int(e[0]): e[1] for e in d["frame_edges"]}
    fk = sorted(g)
    edur = {}
    for i, k in enumerate(fk):
        if i + 1 < len(fk) and k in edge_t and fk[i + 1] in edge_t:
            edur[k] = (edge_t[fk[i + 1]] - edge_t[k]) * 1000.0
    for k in fk:
        ts = sorted(g[k])
        if len(ts) < 3:
            continue
        gaps = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]
        spans.append((ts[-1] - ts[0]) * 1000.0)
        mgs.append(max(gaps) * 1000.0)
    p50 = (d.get("stats") or {}).get("frame_ms_p50")
    rp = sorted(a / b for a, b in zip(mgs, spans) if b > 0)
    rows.append(dict(tag=tag, p50=p50, frames=len(spans),
                     r_p50=statistics.median([a / b for a, b in zip(mgs, spans) if b > 0]),
                     r_p95=rp[int(0.95 * len(rp)) - 1], r_max=max(rp),
                     edur=edur, mgs=dict(zip([k for k in fk if len(g[k]) >= 3], mgs))))

P("=" * 100)
P("[1] §603 汇总声明复算（对照台账 :9624-9633、:9652、census out [2]）")
P("=" * 100)
slow = [r for r in rows if r["p50"] > 60]
fast = [r for r in rows if r["p50"] <= 60]
P("慢窗(p50>60)=%d 快窗(<=60)=%d（台账 :9630-9633 称 12/3）" % (len(slow), len(fast)))
for name, grp in (("慢窗", slow), ("快窗", fast), ("全部", rows)):
    rp50 = [r["r_p50"] for r in grp]
    rp95 = [r["r_p95"] for r in grp]
    rmax = [r["r_max"] for r in grp]
    P("%s: ratio_p50 中位=%.4f（范围 %.4f–%.4f）｜ratio_p95 最大=%.4f｜ratio_max 最大=%.4f"
      % (name, statistics.median(rp50), min(rp50), max(rp50), max(rp95), max(rmax)))
P("15/15 窗 ratio_p95<0.30 = %s（台账 :9626）" % all(r["r_p95"] < 0.30 for r in rows))
P("慢窗 frames 范围 = %d–%d，快窗 = %d–%d（台账 :9652/:9690 称 220–366 / 782–783）"
  % (min(r["frames"] for r in slow), max(r["frames"] for r in slow),
     min(r["frames"] for r in fast), max(r["frames"] for r in fast)))

P("")
P("=" * 100)
P("[2] 语料标准口径（帧内 maxgap、正确配对）+ edge 帧时长 下 §604 汇总复算")
P("=" * 100)
ratios, gds = [], []
per = []
for r in rows:
    keys = sorted(k for k in r["edur"] if k in r["mgs"])
    items = sorted((r["edur"][k], r["mgs"][k]) for k in keys)
    k = len(items) // 3
    fd = statistics.median([x[0] for x in items[:k]])
    sd = statistics.median([x[0] for x in items[len(items) - k:]])
    fg = statistics.median([x[1] for x in items[:k]])
    sg = statistics.median([x[1] for x in items[len(items) - k:]])
    ratios.append(sd / fd)
    gds.append(sg - fg)
    per.append((r["tag"], fd, fg, sd, sg, sd / fd, sg - fg))
P("倍率中位 = %.4f（台账 :9723 称 2.19）" % statistics.median(ratios))
P("倍率最大窗 = %s = %.4f（台账 :9723 括号称「最大 l3/w0 = 2.14 倍」→ 倍率读法不成立）"
  % (max(per, key=lambda x: x[5])[0], max(ratios)))
P("慢1/3时长绝对值最大窗 = %s = %.1f ms（「最大」唯一自洽读法；l3/w0 = %.1f ms）"
  % (max(per, key=lambda x: x[3])[0], max(x[3] for x in per),
     [x[3] for x in per if x[0] == "l3_20261021/w0"][0]))
P("空档差（慢1/3−快1/3）: 中位=%+.4f 范围=%+.4f..%+.4f 负值窗数=%d/15"
  % (statistics.median(gds), min(gds), max(gds), sum(1 for x in gds if x < 0)))
P("（台账 :9724 称 +0.003~+0.049、:9725 称 3 窗为负列举 4 窗——两处均与表值及本复算不符）")
P("「帧内最大空档只差 0.02 ms 量级」（:9729）→ 本口径复算为中位 %+.3f ms、最大 %+.3f ms（量级为 0.0x–0.1x ms）"
  % (statistics.median(gds), max(gds)))
P("★ 定性结论方向不变：空档差 ≤0.114 ms，对 ~2.7 ms 空档与 2.2 倍帧时差仍是微护城河 ⇒ "
  "「慢=单点长阻塞(≥3ms)」仍被否证；但 :9725 的负值窗与 :9724 的区间数值不可复现、不得原样引用。")
P("")
P("N8_S603_SUMMARY DONE")

io.open(os.path.join(HERE, "_n8_s603_summary_out.txt"), "w", encoding="utf-8").write("\n".join(OUT) + "\n")
print("\n".join(OUT))
