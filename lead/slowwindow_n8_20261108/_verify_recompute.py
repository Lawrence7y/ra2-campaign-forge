# -*- coding: utf-8 -*-
"""N-8 独立复核（默认怀疑）：从原始 JSON/TSV 自行重算，不复用 _n8_* 实现。
只读既有语料；唯一写域 = 本目录 _verify_recompute_out.txt。
零真机、零采样代码、不 commit、不 push。
"""
import collections
import glob
import io
import json
import os
import statistics
import hashlib

ROOT = r"D:\Project\ra2-campaign-forge"
HERE = os.path.join(ROOT, "lead", "slowwindow_n8_20261108")
LOG = []


def P(*a):
    LOG.append(" ".join(str(x) for x in a))


def load_qual():
    """独立门禁：与 §602 census 相同条件，但自行枚举并按 (dir, w) 建索引。"""
    out = {}
    for p in glob.glob(os.path.join(ROOT, "lead", "**", "measure_w*.json"), recursive=True):
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        if d.get("verdict") != "ok":
            continue
        if (d.get("stats") or {}).get("hz_effective", 0) < 100:
            continue
        # 用父目录名 + wN 作 key（不依赖 basename 切片技巧）
        key = os.path.basename(os.path.dirname(p)) + "/" + os.path.splitext(os.path.basename(p))[0].replace("measure_", "")
        out[key] = d
    return out


QUAL = load_qual()
P("=" * 96)
P("[V0] 合格窗独立枚举 = %d，keys = %s" % (len(QUAL), sorted(QUAL)))
P("=" * 96)


def per_frame(d):
    """逐帧：按 f 分组，帧内相邻 t 间隔；span=首末差，maxgap=最大间隔，medgap=中位间隔。
    这是 §602/_intra_frame_census.py 的定义（我实读其 :analyze，独立重写）。
    """
    s = d["samples"]
    grp = collections.defaultdict(list)
    for fi, ti in zip(s["f"], s["t"]):
        grp[fi].append(ti)
    rec = {}
    for fi, ts in grp.items():
        ts = sorted(ts)
        if len(ts) < 3:
            continue
        gaps = [b - a for a, b in zip(ts, ts[1:])]
        rec[fi] = dict(span=(ts[-1] - ts[0]) * 1000.0,
                       maxgap=max(gaps) * 1000.0,
                       medgap=statistics.median(gaps) * 1000.0,
                       nreads=len(ts))
    return rec


# 单调性自检（独立算）
def mono(d):
    f = d["samples"]["f"]
    back = sum(1 for a, b in zip(f, f[1:]) if b < a)
    jump = sum(1 for a, b in zip(f, f[1:]) if b - a > 1)
    return back, jump


# ---------------------------------------------------------- [V1] §603 逐窗 + 汇总
P("")
P("=" * 96)
P("[V1] §603 逐窗普查独立复算（对台账 :9601-9615 逐值）")
P("=" * 96)
LED603 = {  # 从台账 :9601-9615 抄录：p50 frames span maxgap medgap 每帧读数 r_p50 r_p95 r_max
    "t55k_20261020/w0": (32.2, 782, 29.8, 2.6, 2.49, 16.0, 0.089, 0.113, 0.334),
    "t55k_20261020/w2": (32.2 if False else 32.3, 782, 29.8, 2.6, 2.49, 16.0, 0.089, 0.108, 0.250),
    "t55k_20261020/w1": (32.4, 783, 29.9, 2.6, 2.49, 16.0, 0.089, 0.107, 0.983),
    "l1e_20261021/w2": (60.6, 366, 58.0, 2.6, 2.50, 30.0, 0.045, 0.076, 0.212),
    "l1d_20261021/w2": (69.6, 343, 66.9, 2.6, 2.50, 34.0, 0.042, 0.079, 0.263),
    "l3_20261021/w1": (72.9, 300, 70.3, 2.7, 2.50, 36.0, 0.038, 0.066, 0.090),
    "l1e_20261021/w1": (75.7, 311, 73.1, 2.6, 2.50, 38.0, 0.036, 0.080, 0.499),
    "l1e_20261021/w0": (78.0, 292, 75.5, 2.7, 2.50, 39.0, 0.035, 0.075, 0.092),
    "l1d_20261021/w0": (90.3, 257, 87.4, 2.7, 2.50, 45.0, 0.031, 0.070, 0.133),
    "l3_20261021/w2": (92.3, 256, 89.6, 2.7, 2.50, 46.0, 0.031, 0.063, 0.098),
    "l1c_20261021/w2": (92.4, 251, 89.3, 2.7, 2.50, 46.0, 0.030, 0.070, 0.155),
    "l1d_20261021/w1": (95.2, 257, 92.5, 2.7, 2.50, 48.0, 0.029, 0.072, 0.081),
    "l1c_20261021/w0": (103.2, 230, 100.8, 2.7, 2.50, 52.0, 0.028, 0.057, 0.081),
    "l3_20261021/w0": (105.2, 220, 102.6, 2.8, 2.50, 52.0, 0.027, 0.049, 0.064),
    "l1c_20261021/w1": (110.4, 229, 107.7, 2.7, 2.50, 55.0, 0.026, 0.065, 0.083),
}
allrows = {}
mism = []
for tag, d in QUAL.items():
    rec = per_frame(d)
    spans = [r["span"] for r in rec.values()]
    mgaps = [r["maxgap"] for r in rec.values()]
    medg = [r["medgap"] for r in rec.values()]
    nr = [r["nreads"] for r in rec.values()]
    ratios = sorted(g / s for g, s in zip(mgaps, spans) if s > 0)
    p50 = (d.get("stats") or {}).get("frame_ms_p50")
    r = dict(p50=p50, frames=len(rec),
             span=statistics.median(spans), maxgap=statistics.median(mgaps),
             medgap=statistics.median(medg), nreads=statistics.median(nr),
             r_p50=statistics.median(ratios),
             r_p95=ratios[int(0.95 * len(ratios)) - 1],
             r_max=ratios[-1])
    allrows[tag] = (r, rec, d)
    # 逐值比对（按台账打印精度）
    got = (round(r["p50"], 1), r["frames"], round(r["span"], 1), round(r["maxgap"], 1),
           round(r["medgap"], 2), round(r["nreads"], 1), round(r["r_p50"], 3),
           round(r["r_p95"], 3), round(r["r_max"], 3))
    exp = LED603.get(tag)
    ok = exp is not None and all(abs(a - b) < 1e-9 for a, b in zip(got, exp))
    P("%-22s got=%s exp=%s %s" % (tag, got, exp, "MATCH" if ok else "MISMATCH"))
    if not ok:
        mism.append(tag)
P("§603 逐窗 15 行全值吻合 = %s（MISMATCH=%s）" % (not mism, mism))

# §603 汇总
slow = [r for r, _, _ in allrows.values() if r["p50"] > 60]
fast = [r for r, _, _ in allrows.values() if r["p50"] <= 60]
P("")
P("慢窗=%d 快窗=%d | 全部 ratio_p50 中位=%.4f | 慢窗中位=%.4f 快窗中位=%.4f" %
  (len(slow), len(fast), statistics.median([r["r_p50"] for r, _, _ in allrows.values()]),
   statistics.median([r["r_p50"] for r in slow]), statistics.median([r["r_p50"] for r in fast])))
P("ratio_p95 最大=%.4f | ratio_max 最大=%.4f | 15/15 r_p95<0.30=%s" %
  (max(r["r_p95"] for r, _, _ in allrows.values()),
   max(r["r_max"] for r, _, _ in allrows.values()),
   all(r["r_p95"] < 0.30 for r, _, _ in allrows.values())))
P("慢窗 frames=%d..%d 快窗 frames=%d..%d" %
  (min(r["frames"] for r in slow), max(r["frames"] for r in slow),
   min(r["frames"] for r in fast), max(r["frames"] for r in fast)))
P("f 单调：back/jump 非 0 的窗 = %s" %
  [(t, mono(d)) for t, (r, rec, d) in allrows.items() if mono(d) != (0, 0)])

# ---------------------------------------------------------- [V2] §560 矩阵
P("")
P("=" * 96)
P("[V2] §560 矩阵独立复算")
P("=" * 96)
mtsv = os.path.join(ROOT, "lead", "re_line_20261105", "W2_FRAMETIME_ATTRIB", "_w2_matrix.tsv")
raw = io.open(mtsv, encoding="utf-8").read().splitlines()
hdr = raw[0].split("\t")
col = {c: i for i, c in enumerate(hdr)}
rows = [l.split("\t") for l in raw[1:] if l.strip()]
P("数据行=%d（台账 :6017 称 87）; distinct trip=%d（称 29）" %
  (len(rows), len(set(x[col["trip"]] for x in rows))))
good = [x for x in rows if x[col["frame_ms_p50"]] not in ("None", "")]
P("p50 有效行=%d None 行=%d" % (len(good), len(rows) - len(good)))
bymap = collections.defaultdict(list)
for x in good:
    bymap[x[col["map_sha8"]]].append(float(x[col["frame_ms_p50"]]))
P("distinct map=%d" % len(bymap))
for m in sorted(bymap, key=lambda m: statistics.median(bymap[m])):
    P("  map %s n=%2d 中位=%.2f min=%.2f max=%.2f" %
      (m, len(bymap[m]), statistics.median(bymap[m]), min(bymap[m]), max(bymap[m])))
stable_maps = [m for m in bymap if m not in ("f3bb0a4e", "0add791d")]
win_vals = [v for m in stable_maps for v in bymap[m]]
map_meds = [statistics.median(bymap[m]) for m in stable_maps]
P("★ 其余 7 图 窗级读法（全部有效 p50 行）: min=%.2f max=%.2f 极差=%.2f" %
  (min(win_vals), max(win_vals), max(win_vals) - min(win_vals)))
P("★ 其余 7 图 图中位读法: min=%.2f max=%.2f 极差=%.2f" %
  (min(map_meds), max(map_meds), max(map_meds) - min(map_meds)))
P("台账 :6020 称 31.64–32.38 → 端点差 32.38-31.64=%.2f" % (32.38 - 31.64))
P("核对回件 evidence [E] 称「窗级读法复现（极差 0.74<1ms✓）」——0.74 是否等于窗级实算？")

# 对子（独立实现：max-based / min-based / 临界）
n = len(good)
pmax = pmin = 0
for i in range(n):
    for j in range(i + 1, n):
        a, b = good[i], good[j]
        if a[col["map_sha8"]] != b[col["map_sha8"]]:
            continue
        p1, p2 = float(a[col["frame_ms_p50"]]), float(b[col["frame_ms_p50"]])
        if max(p1, p2) / min(p1, p2) <= 1.5:
            continue
        u1, u2 = float(a[col["units0"]]), float(b[col["units0"]])
        dmax = abs(u1 - u2) / max(u1, u2)
        dmin = abs(u1 - u2) / min(u1, u2)
        pmax += dmax <= 0.10
        pmin += dmin <= 0.10
P("对子 max-based=%d min-based=%d 临界=%d（台账 :6018 称 107/82/25）" %
  (pmax, pmin, pmax - pmin))

# 15 合格窗 JSON p50 ↔ TSV（独立：按 trip=目录名 + window 精确匹配）
hit = 0
for tag, (r, rec, d) in allrows.items():
    dr, wn = tag.split("/")
    for x in good:
        if x[col["trip"]] == dr and x[col["window"]] == wn:
            if abs(float(x[col["frame_ms_p50"]]) - r["p50"]) < 5e-4:
                hit += 1
                break
P("15 合格窗 JSON p50 ↔ TSV 精确匹配 = %d/15" % hit)

# ---------------------------------------------------------- [V3] §604 汇总
P("")
P("=" * 96)
P("[V3] §604 独立复算：edge 帧时长 + 帧内 maxgap + 正确配对（k=frames//3）")
P("=" * 96)
LED604 = {  # :9706-9720 快时长 快空档 慢时长 慢空档
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
ORD = ["l1c_20261021", "l1d_20261021", "l1e_20261021", "l3_20261021", "t55k_20261020"]
ratios, gds = [], []
dur_hit = gap_hit = 0
for dr in ORD:
    for wi in range(3):
        tag = dr + "/w" + str(wi)
        r, rec, d = allrows[tag]
        edge = {int(e[0]): e[1] for e in d["frame_edges"]}
        fk = sorted(rec)
        # 帧时长 = 相邻 frame_edges 时刻差（edge 口径）
        pairs = []
        for idx, k in enumerate(fk):
            if idx + 1 < len(fk) and k in edge and fk[idx + 1] in edge:
                pairs.append(((edge[fk[idx + 1]] - edge[k]) * 1000.0, rec[k]["maxgap"]))
        pairs.sort()
        k = len(pairs) // 3
        lo, hi = pairs[:k], pairs[len(pairs) - k:]
        fd, fg = statistics.median(x[0] for x in lo), statistics.median(x[1] for x in lo)
        sd, sg = statistics.median(x[0] for x in hi), statistics.median(x[1] for x in hi)
        ratios.append(sd / fd)
        gds.append(sg - fg)
        L = LED604[tag]
        dh = (abs(fd - L[0]) <= 0.05 and abs(sd - L[2]) <= 0.05)
        gh = (abs(fg - L[1]) <= 0.005 and abs(sg - L[3]) <= 0.005)
        dur_hit += 2 if dh else 0
        gap_hit += 2 if gh else 0
        P("%-22s 快%.1f/%.3f 慢%.1f/%.3f | 台账 %.1f/%.2f %.1f/%.2f | 时长%s 空档%s" %
          (tag, fd, fg, sd, sg, L[0], L[1], L[2], L[3],
           "✓" if dh else "✗", "✓" if gh else "✗"))
P("时长列命中 = %d/30  空档列命中 = %d/30" % (dur_hit, gap_hit))
P("倍率中位=%.4f（台账 :9723 称 2.19） 倍率最大=%.4f" %
  (statistics.median(ratios), max(ratios)))
P("空档差 中位=%+.4f 范围=%+.4f..%+.4f 负值窗=%d/15" %
  (statistics.median(gds), min(gds), max(gds), sum(1 for x in gds if x < 0)))

# :9723/:9724/:9725 内部一致性（纯表值，独立于口径）
tr = [LED604[t][2] / LED604[t][0] for t in LED604]
tg = [LED604[t][3] - LED604[t][1] for t in LED604]
P("")
P("台账表值直接复算：倍率中位=%.4f 倍率最大=%s=%.4f 空档差范围=%+.3f..%+.3f 负值窗=%d" %
  (statistics.median(tr), max(LED604, key=lambda t: LED604[t][2] / LED604[t][0]),
   max(tr), min(tg), max(tg), sum(1 for x in tg if x < 0)))
P(":9723 括号「最大 l3/w0=2.14 倍」→ 表内 l3/w0 比=%.4f，全表倍率最大=%.4f（l1d/w2）" %
  (LED604["l3_20261021/w0"][2] / LED604["l3_20261021/w0"][0], max(tr)))
P(":9725 称「3 窗为负」却列 4 窗（l3/w0,t55k/w0,t55k/w1,t55k/w2）；其中 -0.000 按严格 <0 不计负")
P(":9724 称「+0.003~+0.049」与表值 空档差集合=%s 不符" % [round(x, 3) for x in sorted(tg)])

# ---------------------------------------------------------- [V4] 四类量字段
P("")
P("=" * 96)
P("[V4] 四类量可识别性：全量键并集独立盘点")
P("=" * 96)
top, samp, cnt, stt = set(), set(), set(), set()
nctr = set()
trel = []
for tag, (r, rec, d) in allrows.items():
    top |= set(d.keys())
    samp |= set(d["samples"].keys())
    stt |= set(d["stats"].keys())
    nctr.add(len(d["counters"]))
    for c in d["counters"]:
        cnt |= set(c.keys())
        trel.append(c.get("t_rel"))
P("顶层键=%s" % sorted(top))
P("samples 键=%s  frame_edges 元素=%s" %
  (sorted(samp), [tuple(sorted(type(z).__name__ for z in e)) for e in d["frame_edges"][:1]]))
P("counters 每窗条数=%s  t_rel 范围=%.6g..%.6g" % (sorted(nctr), min(trel), max(trel)))
P("counters 键并集=%s" % sorted(cnt))
P("stats 键=%s" % sorted(stt))
KEYSET = top | samp | cnt | stt
for word in ("node", "call", "path", "phase", "stage", "dijkstra", "target", "frame_unit", "units_frame"):
    P("  含 %-12s 的键 = %s" % (word, [k for k in KEYSET if word in k.lower()] or "无"))
P("W2 矩阵列=%s" % hdr)

# ---------------------------------------------------------- [V5] 指纹 + 写域
P("")
P("=" * 96)
P("[V5] 写域清单 + 上游指纹")
P("=" * 96)
for f in sorted(os.listdir(HERE)):
    fp = os.path.join(HERE, f)
    if os.path.isfile(fp):
        b = open(fp, "rb").read()
        P("  %s  %d  %s" % (hashlib.sha256(b).hexdigest()[:16], len(b), f))
UP = {
    "lead/GOAL_THREE_TARGETS_20261018.md": "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede",
    "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md": "c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c",
    "lead/slowframe_round2_20261107/SLOWFRAME_PROXY.md": "5fe880595965de4e0b39639c0d4a80d626476a9715f1cae5efd7361a0c8985d3",
}
for rel, exp in UP.items():
    b = open(os.path.join(ROOT, rel), "rb").read()
    P("  %s %s bytes=%d" % ("MATCH" if hashlib.sha256(b).hexdigest() == exp else "MISMATCH", rel, len(b)))

P("")
P("VERIFY DONE")
io.open(os.path.join(HERE, "_verify_recompute_out.txt"), "w", encoding="utf-8").write("\n".join(LOG) + "\n")
print("\n".join(LOG))
