# -*- coding: utf-8 -*-
"""N-8 残项收口 · 第 3 项：ratio_max = 0.9831 那帧的读数个数（GOAL :9673/:9680 自标未验）。

算法镜像 lead/slowwindow_n8_20261108/_n8_recompute.py:88-132（不 import、独立重写）：
  合格窗 = measure_w*.json 且 verdict==ok 且 stats.hz_effective>=100；
  逐帧（按 f 分组，读数<3 的帧跳过）：span=(末读数-首读数)*1000 ms，
  maxgap=相邻读数最大间隔*1000 ms，ratio=maxgap/span；
  窗 r_max = max(ratio)；全局 ratio_max = max(窗 r_max)。
另按任务书字面定义「每帧读数个数/帧时长」复算一版作对照。
只读；唯一写域 = 本脚本同目录 _n8r_item3_ratiomax_out.txt。零真机、零采样代码。
"""
import collections
import glob
import hashlib
import io
import json
import os
import re

ROOT = r"D:\Project\ra2-campaign-forge"
HERE = os.path.join(ROOT, "lead", "n8_residual_20261108")
OUT = []


def P(*a):
    OUT.append(" ".join(str(x) for x in a))


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


paths = sorted(glob.glob(os.path.join(ROOT, "lead", "**", "measure_w*.json"), recursive=True))
P("[G] lead/**/measure_w*.json 候选 = %d" % len(paths))
qual = []
skip = collections.Counter()
for p in paths:
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        skip["unreadable"] += 1
        continue
    if d.get("verdict") != "ok":
        skip["verdict!=ok"] += 1
        continue
    hz = (d.get("stats") or {}).get("hz_effective")
    if not hz or hz < 100:
        skip["hz<100"] += 1
        continue
    qual.append((p, d))
P("合格窗（verdict=ok 且 hz_effective>=100）= %d  跳过 = %s" % (len(qual), dict(skip)))

frames_rows = []  # (tag, fi, nreads, span, maxgap, ratio, raw_ts)
win_rows = []     # (tag, len(fr), distinct_f, skipped_small, r_max)
for p, d in qual:
    wn = re.search(r"measure_w(\d+)\.json$", os.path.basename(p)).group(1)
    tag = os.path.basename(os.path.dirname(p)) + "/w" + wn
    s = d["samples"]
    f, t = s["f"], s["t"]
    g = collections.defaultdict(list)
    for fi, ti in zip(f, t):
        g[fi].append(ti)
    nsmall = 0
    fr = []
    for fi in sorted(g):
        ts = sorted(g[fi])
        if len(ts) < 3:
            nsmall += 1
            continue
        gaps = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]
        span = (ts[-1] - ts[0]) * 1000.0
        mg = max(gaps) * 1000.0
        fr.append((fi, len(ts), span, mg, mg / span if span > 0 else None, ts))
    ratios = [x[4] for x in fr if x[4] is not None]
    rmax_w = max(ratios) if ratios else None
    win_rows.append((tag, len(fr), len(g), nsmall, rmax_w))
    for x in fr:
        frames_rows.append((tag,) + x[:5] + (x[5],))

P("")
P("[T] 15 窗 r_max（算法镜像 _n8_recompute.py：ratio = 帧内最大空档/帧时长）")
P("%-22s %8s %9s %8s %10s" % ("window", "帧数(>=3读)", "distinct_f", "小帧跳过", "r_max"))
for tag, nf, nd, ns, rm in sorted(win_rows):
    P("%-22s %8d %9d %8d %10.4f" % (tag, nf, nd, ns, rm))

gmax = max(win_rows, key=lambda x: x[4])
P("")
P("[M] 全局 ratio_max = %.6f  @ %s（round4 = %.4f）" % (gmax[4], gmax[0], round(gmax[4], 4)))
# 全语料中与 0.9831 相差 <1e-4 的帧（防并列遗漏）
near = [r for r in frames_rows if r[5] is not None and abs(r[5] - 0.9831) < 1e-4]
P("[M] 与 0.9831 差 <1e-4 的帧（全 15 窗）= %d 个：" % len(near))
for r in sorted(near, key=lambda x: -x[5]):
    P("    %s  f=%d  读数=%d  span=%.4f ms  maxgap=%.4f ms  ratio=%.6f" %
      (r[0], r[1], r[2], r[3], r[4], r[5]))

P("")
P("[F] 该帧原始读数（t 序列，秒）：")
for p, d in qual:
    wn = re.search(r"measure_w(\d+)\.json$", os.path.basename(p)).group(1)
    tag = os.path.basename(os.path.dirname(p)) + "/w" + wn
    if tag != gmax[0]:
        continue
    s = d["samples"]
    g = collections.defaultdict(list)
    for fi, ti in zip(s["f"], s["t"]):
        g[fi].append(ti)
    best_fi, best_ratio = None, -1.0
    for fi in sorted(g):
        ts = sorted(g[fi])
        if len(ts) < 3:
            continue
        gaps = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]
        span = (ts[-1] - ts[0]) * 1000.0
        ratio = max(gaps) * 1000.0 / span
        if ratio > best_ratio:
            best_ratio, best_fi = ratio, fi
    ts = sorted(g[best_fi])
    P("    窗 = %s  帧号 f = %d  读数个数 = %d" % (tag, best_fi, len(ts)))
    P("    span = %.4f ms  maxgap = %.4f ms  ratio = %.6f" %
      ((ts[-1] - ts[0]) * 1000.0, max(ts[i + 1] - ts[i] for i in range(len(ts) - 1)) * 1000.0,
       best_ratio))
    P("    t 序列 = %s  （相邻间隔 ms = %s）" %
      (["%.6f" % x for x in ts],
       ["%.4f" % ((ts[i + 1] - ts[i]) * 1000.0) for i in range(len(ts) - 1)]))
    wf = [x for x in win_rows if x[0] == tag][0]
    P("    该窗帧数（读数>=3 口径）= %d；distinct_f 总数 = %d；其中读数<3 跳过 = %d" %
      (wf[1], wf[2], wf[3]))
    P("    窗 p50(stats.frame_ms_p50) = %s ms  hz_effective = %s" %
      (d["stats"].get("frame_ms_p50"), d["stats"].get("hz_effective")))

# 对照：任务书字面定义（每帧读数个数/帧时长）
P("")
P("[A] 对照：任务书字面口径 ratio' = 每帧读数个数 / 帧时长(span ms)")
lit = [(r[0], r[1], r[2], r[3], r[2] / r[3]) for r in frames_rows if r[3] > 0]
lw = collections.defaultdict(float)
for tag, fi, nr, sp, _ in lit:
    lw[tag] = max(lw[tag], nr / sp)
for tag in sorted(lw):
    P("    %-22s 字面口径窗最大 = %.6f 读数/ms" % (tag, lw[tag]))
glt = max(lw.items(), key=lambda x: x[1])
P("    字面口径全局最大 = %.6f（窗 %s）→ %s 0.9831" %
  (glt[1], glt[0], "等于" if abs(glt[1] - 0.9831) < 5e-5 else "不等于"))

# 被核对象指纹
P("")
P("[H] 被核对象指纹（15 合格窗 measure JSON，hashlib 实算）")
for p, d in qual:
    P("    %s  bytes=%d" % (sha256_file(p), os.path.getsize(p)))

P("")
P("N8R_ITEM3 DONE")

io.open(os.path.join(HERE, "_n8r_item3_ratiomax_out.txt"), "w", encoding="utf-8").write(
    "\n".join(OUT) + "\n")
print("\n".join(OUT))
