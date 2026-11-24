# -*- coding: utf-8 -*-
"""N-8 慢窗核对：台账 7 锚点（GOAL_THREE_TARGETS_20261018.md :5996/:9723/:9725/:9735/:9741/:9745/:9756）
的「汇总值 vs 逐窗值」一致性复算。

只读既有语料；唯一写域 = 本脚本同目录 _n8_recompute_out.txt。
零真机、零采样代码、不 commit、不 push。
逐窗旧输出 = lead/**/measure_w*.json（15 个合格窗）+ lead/re_line_20261105/W2_FRAMETIME_ATTRIB/_w2_matrix.tsv。
"""
import collections
import glob
import hashlib
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


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- [A] 上游指纹
UP = {
    "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md":
        "c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c",
    "lead/GOAL_THREE_TARGETS_20261018.md":
        "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede",
    "lead/re_line_20261105/D24_RULING/RULING_D24.md":
        "56167a5e869540d7e14a7f13d29a2ed9d780d0c6352635e6e12b36cd633dcdf5",
    "lead/slowframe_round2_20261107/SLOWFRAME_PROXY.md":
        "5fe880595965de4e0b39639c0d4a80d626476a9715f1cae5efd7361a0c8985d3",
    "lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md":
        "e492ce0d00828b60198a3b9583845fc408fc37d1556958b306bf965f02a55c12",
}
P("=" * 100)
P("[A] 上游指纹核验（编排方给值 vs 本机 hashlib.sha256 实算）")
P("=" * 100)
for rel in sorted(UP):
    p = os.path.join(ROOT, rel)
    b = open(p, "rb").read()
    h = hashlib.sha256(b).hexdigest()
    P("%s  %s  bytes=%d  %s" % ("MATCH  " if h == UP[rel] else "MISMATCH", rel, len(b), h))

# ------------------------------------------------- [B] 15 合格窗门禁（同 _intra_frame_census.py:92-104）
paths = sorted(glob.glob(os.path.join(ROOT, "lead", "**", "measure_w*.json"), recursive=True))
P("")
P("=" * 100)
P("[B] 逐窗语料盘点：lead/**/measure_w*.json 候选=%d" % len(paths))
P("=" * 100)
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
P("合格窗（verdict=ok 且 hz_effective>=100）=%d  跳过=%s" % (len(qual), dict(skip)))
for p, d in qual:
    wn = re.search(r"measure_w(\d+)\.json$", os.path.basename(p)).group(1)
    tag = os.path.basename(os.path.dirname(p)) + "/w" + wn
    hz = (d.get("stats") or {}).get("hz_effective")
    P("  %-24s trip_id=%-18s hz_effective=%.1f  sha256=%s" % (tag, d.get("trip_id"), hz, sha256_file(p)))


# ------------------------------------------------- [C] 逐帧统计 + §604 三分位复算
def frame_stats(d):
    s = d["samples"]
    f, t = s["f"], s["t"]
    back = sum(1 for i in range(1, len(f)) if f[i] < f[i - 1])
    jumps = sum(1 for i in range(1, len(f)) if f[i] - f[i - 1] > 1)
    g = collections.defaultdict(list)
    for fi, ti in zip(f, t):
        g[fi].append(ti)
    fr = []
    for fi in sorted(g):
        ts = sorted(g[fi])
        if len(ts) < 3:
            continue
        gaps = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]
        fr.append(((ts[-1] - ts[0]) * 1000.0, max(gaps) * 1000.0,
                   statistics.median(gaps) * 1000.0, len(ts)))
    return back, jumps, fr


rows = []
for p, d in qual:
    wn = re.search(r"measure_w(\d+)\.json$", os.path.basename(p)).group(1)
    tag = os.path.basename(os.path.dirname(p)) + "/w" + wn
    back, jumps, fr = frame_stats(d)
    spans = [x[0] for x in fr]
    mgs = [x[1] for x in fr]
    p50 = (d.get("stats") or {}).get("frame_ms_p50")
    rp = sorted(g / sp for sp, g in zip(spans, mgs) if sp > 0)
    r_p95 = rp[int(0.95 * len(rp)) - 1] if rp else None
    k = len(fr) // 3
    srt = sorted(fr)  # 按 span 升序
    fast, slow = srt[:k], srt[len(srt) - k:]
    fmed = statistics.median([x[0] for x in fast])
    smed = statistics.median([x[0] for x in slow])
    fgap = statistics.median([x[1] for x in fast])
    sgap = statistics.median([x[1] for x in slow])
    rows.append(dict(
        tag=tag, p=p, p50=p50, frames=len(fr), span_med=statistics.median(spans),
        maxgap_med=statistics.median(mgs),
        medgap_med=statistics.median([x[2] for x in fr]),
        nreads=statistics.median([x[3] for x in fr]),
        r_p50=statistics.median([g / sp for sp, g in zip(spans, mgs) if sp > 0]),
        r_p95=r_p95, r_max=max(g / sp for sp, g in zip(spans, mgs) if sp > 0),
        back=back, jumps=jumps, k=k, fmed=fmed, smed=smed, fgap=fgap, sgap=sgap,
        ratio=(smed / fmed if fmed > 0 else None), gapdiff=sgap - fgap))

P("")
P("=" * 100)
P("[C1] §603 逐窗普查复算（应逐值对上台账 :9601-9615 与 _intra_frame_census_out.txt）")
P("=" * 100)
P("%-24s %8s %7s %8s %8s %8s %8s %7s %7s %6s %5s %5s" %
  ("window", "p50(ms)", "frames", "span", "maxgap", "medgap", "每帧读数", "r_p50", "r_p95", "r_max", "back", "jump"))
for r in sorted(rows, key=lambda x: x["p50"] or 0):
    P("%-24s %8.1f %7d %8.1f %8.1f %8.2f %8.1f %7.3f %7.3f %6.3f %5d %5d" %
      (r["tag"], r["p50"], r["frames"], r["span_med"], r["maxgap_med"],
       r["medgap_med"], r["nreads"], r["r_p50"], r["r_p95"], r["r_max"],
       r["back"], r["jumps"]))

P("")
P("=" * 100)
P("[C2] §604 快1/3 vs 慢1/3 复算（帧按 span 升序，k=frames//3；应逐值对上台账 :9706-9720）")
P("=" * 100)
P("%-24s %4s %10s %10s %10s %10s %10s %9s %9s" %
  ("window", "k", "快1/3时长", "快1/3空档", "慢1/3时长", "慢1/3空档", "空档差", "倍率", "(慢/快)"))
order = {t + "/w" + str(i): (ti, i) for ti, t in enumerate(["l1c_20261021", "l1d_20261021",
          "l1e_20261021", "l3_20261021", "t55k_20261020"]) for i in range(3)}
for r in sorted(rows, key=lambda x: order.get(x["tag"], (99, 99))):
    P("%-24s %4d %10.1f %10.2f %10.1f %10.2f %10.3f %9.4f" %
      (r["tag"], r["k"], r["fmed"], r["fgap"], r["smed"], r["sgap"], r["gapdiff"], r["ratio"]))

P("")
P("=" * 100)
P("[D] §604 汇总声明复算（对照台账 :9723/:9724/:9725）")
P("=" * 100)
ratios = [r["ratio"] for r in rows]
P("慢1/3/快1/3 倍率中位 = %.4f   （台账 :9723 声称「中位 2.19 倍」）" % statistics.median(ratios))
rmax = max(rows, key=lambda r: r["ratio"])
P("倍率最大窗 = %s = %.4f   （台账 :9723 括号称「最大 l3/w0：73.2→156.6 = 2.14 倍」）" % (rmax["tag"], rmax["ratio"]))
l3w0 = [r for r in rows if r["tag"] == "l3_20261021/w0"][0]
P("l3/w0 实算 = %.1f→%.1f = %.4f 倍（慢1/3时长绝对值最大窗另算：%s = %.1f ms）" %
  (l3w0["fmed"], l3w0["smed"], l3w0["ratio"], rmax["tag"], rmax["smed"]))
neg = [r for r in rows if r["gapdiff"] < 0]
P("空档差<0 的窗数 = %d ：%s" % (len(neg), ", ".join("%s(%+.4f)" % (r["tag"], r["gapdiff"]) for r in
                                                    sorted(neg, key=lambda x: x["gapdiff"]))))
P("（台账 :9725 声称「其中 3 窗为负」却列出 4 个窗：l3/w0 −0.002、t55k/w0 −0.013、t55k/w1 −0.006、t55k/w2 −0.000）")
gds = [r["gapdiff"] for r in rows]
P("空档差全范围 = %+.4f .. %+.4f   （台账 :9724 声称「+0.003 ~ +0.049 ms」）" % (min(gds), max(gds)))

# ------------------------------------------------- [E] W2 矩阵（§560 :6016-6020）
P("")
P("=" * 100)
P("[E] §560 :6016-6020 汇总复算（_w2_matrix.tsv）")
P("=" * 100)
mtsv = os.path.join(ROOT, "lead", "re_line_20261105", "W2_FRAMETIME_ATTRIB", "_w2_matrix.tsv")
P("文件 sha256 = %s  bytes=%d" % (sha256_file(mtsv), os.path.getsize(mtsv)))
lines = io.open(mtsv, encoding="utf-8").read().splitlines()
hdr = lines[0].split("\t")
data = [l.split("\t") for l in lines[1:] if l.strip()]
ix = {c: i for i, c in enumerate(hdr)}
P("列 = %s" % hdr)
P("数据行 = %d（台账 :6017 声称 N=87，29 趟×3 窗）；distinct trip = %d"
  % (len(data), len(set(r[ix["trip"]] for r in data))))
valid = [r for r in data if r[ix["frame_ms_p50"]] not in ("None", "")]
none_rows = [r for r in data if r[ix["frame_ms_p50"]] in ("None", "")]
P("p50 有效行 = %d；p50=None（logic_frames<=0/冻结/菜单）行 = %d（台账 :6017 称排除 15 份 4s/0s 短窗）"
  % (len(valid), len(none_rows)))
maps = collections.defaultdict(list)
for r in valid:
    maps[r[ix["map_sha8"]]].append(float(r[ix["frame_ms_p50"]]))
P("distinct map_sha8 = %d（台账 :6019-6020 称 2 慢 + 7 稳定 = 9 张图）" % len(maps))
med = {m: statistics.median(v) for m, v in maps.items()}
for m in sorted(med, key=lambda m: med[m]):
    P("  map %s  n=%2d  p50中位=%.2f ms  min=%.2f max=%.2f" % (m, len(maps[m]), med[m],
                                                              min(maps[m]), max(maps[m])))
stable = [v for m, v in med.items() if m not in ("f3bb0a4e", "0add791d")]
P("除 f3bb0a4e/0add791d 外 %d 张图中位范围 = %.2f–%.2f（极差 %.2f ms；台账称其余 7 张 31.64–32.38 极差<1ms）"
  % (len(stable), min(stable), max(stable), max(stable) - min(stable)))

# 对子复算（镜像 _w2_probe.py:175-220）
pairs_max = pairs_min = 0
boundary = 0
for i in range(len(valid)):
    for j in range(i + 1, len(valid)):
        r1, r2 = valid[i], valid[j]
        if r1[ix["map_sha8"]] != r2[ix["map_sha8"]]:
            continue
        p1, p2 = float(r1[ix["frame_ms_p50"]]), float(r2[ix["frame_ms_p50"]])
        if max(p1, p2) / min(p1, p2) <= 1.5:
            continue
        u1, u2 = float(r1[ix["units0"]]), float(r2[ix["units0"]])
        if abs(u1 - u2) / max(u1, u2) <= 0.10:
            pairs_max += 1
            if abs(u1 - u2) / min(u1, u2) > 0.10:
                boundary += 1
        if abs(u1 - u2) / min(u1, u2) <= 0.10:
            pairs_min += 1
P("对子复算：max-based=%d / min-based=%d / 临界(max<=10%% 且 min>10%%)=%d"
  % (pairs_max, pairs_min, boundary))
P("（台账 :6018 声称 107 对大者基准含 25 对临界 / 82 对小者基准；_w2_probe_out.txt:31-33 同值）")

# TSV 行 vs measure JSON 抽查
P("")
P("[E2] 矩阵行 vs 15 个 measure JSON 抽查（window 标签 + p50 差<0.005 视为同窗）")
hit = 0
for r in rows:
    best = None
    for dr in data:
        if dr[ix["window"]] != "w" + r["tag"].split("/w")[1]:
            continue
        v = dr[ix["frame_ms_p50"]]
        if v in ("None", ""):
            continue
        if abs(float(v) - r["p50"]) < 0.005:
            best = dr
            break
    if best:
        hit += 1
        if hit <= 5:
            P("  %-22s json p50=%.4f units0(gate)=%s  <-> tsv %s/%s p50=%s units0=%s" %
              (r["tag"], r["p50"],
               json.load(io.open(r["p"], encoding="utf-8"))["gate"]["units0"],
               best[ix["trip"]], best[ix["window"]], best[ix["frame_ms_p50"]], best[ix["units0"]]))
P("15 窗中在矩阵中找到同窗同行（p50 吻合）= %d" % hit)

# ------------------------------------------------- [F] 四类量字段存在性
P("")
P("=" * 100)
P("[F] 四类量的字段存在性（15 窗全量键清单）")
P("=" * 100)
top_keys = set()
sample_keys = set()
counter_keys = set()
stats_keys = set()
edge_shapes = set()
n_counters = set()
trel_span = []
for p, d in qual:
    top_keys |= set(d.keys())
    sample_keys |= set((d.get("samples") or {}).keys())
    cs = d.get("counters") or []
    n_counters.add(len(cs))
    for c in cs:
        counter_keys |= set(c.keys())
        trel_span.append((c.get("t_rel"), c.get("t_rel")))
    stats_keys |= set((d.get("stats") or {}).keys())
    for e in (d.get("frame_edges") or [])[:3]:
        edge_shapes.add(tuple(sorted(type(x).__name__ for x in e)))
P("measure JSON 顶层键 = %s" % sorted(top_keys))
P("samples 键 = %s   frame_edges 元素类型 = %s" % (sorted(sample_keys), sorted(edge_shapes)))
P("counters 每窗条数 = %s（25 s 窗 => 秒级）; 全部 counters 条目键并集 = %s" % (sorted(n_counters), sorted(counter_keys)))
P("stats 键 = %s" % sorted(stats_keys))
susp = [k for k in top_keys | sample_keys | counter_keys | stats_keys
        if any(w in k.lower() for w in ("node", "call", "path", "phase", "stage", "dijkstra", "target"))]
P("含 node/call/path/phase/stage/dijkstra/target 字样的键 = %s" % (susp if susp else "无"))
mtsv_cols = hdr
P("W2 矩阵列（窗口级） = %s" % mtsv_cols)
P("（§560 :6069：500 Hz 帧沿物理上无法拆解 FrameTime=T_Dijkstra+T_Targeting+T_Physics+T_Render+T_Other）")
P("")
P("N8_RECOMPUTE DONE")

io.open(os.path.join(HERE, "_n8_recompute_out.txt"), "w", encoding="utf-8").write("\n".join(OUT) + "\n")
print("\n".join(OUT))
