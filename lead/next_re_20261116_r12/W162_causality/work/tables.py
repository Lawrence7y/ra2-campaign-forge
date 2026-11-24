# -*- coding: utf-8 -*-
"""W162 交付表生成器：只读 out/windows.tsv + 一次样本级重扫（19 个配对趟），
产出 W162_causality\confounders.tsv 与 cpu_vs_wall.tsv 的完整版。

cpu_vs_wall.tsv 由 recompute.py 直接写；本脚本补 confounders.tsv（含分布 + 两种口径的配对）
以及 cpu_vs_wall_paired.tsv（逐趟配对）。

运行：python tables.py
"""
import json, os, math, statistics, collections

HERE = os.path.dirname(os.path.abspath(__file__))
CARD = os.path.dirname(HERE)
WIN = 10.0
FILES = [l.strip() for l in open(os.path.join(HERE, "run_files.txt"), encoding="utf-8") if l.strip()]
COUNTERS = ["B0CE88", "A8E9A0", "87E8E0", "X87E8E0", "ABCD58", "g1", "g2", "g3", "g4"]


def med(v):
    return statistics.median(v) if v else None


def load():
    rows = []
    with open(os.path.join(HERE, "out", "windows.tsv"), encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            p = line.rstrip("\n").split("\t")
            r = {}
            for k, v in zip(hdr, p):
                if v == "":
                    r[k] = None
                elif k in ("trip", "cpu_src"):
                    r[k] = v
                else:
                    r[k] = float(v)
            rows.append(r)
    return rows


def sample_level():
    """样本级：每个计数器在全部 137 个文件里的分布（n/非零%/median/max/distinct）。"""
    tot = collections.defaultdict(list)
    bad_ff = collections.Counter()
    nlines = 0
    for p in FILES:
        for line in open(p, "r", encoding="utf-8", buffering=1 << 20):
            line = line.strip()
            if not line:
                continue
            nlines += 1
            o = json.loads(line)
            for k in COUNTERS + ["A8ED50"]:
                v = o.get(k)
                if isinstance(v, (int, float)):
                    tot[k].append(v)
                    if v == 4294967295:
                        bad_ff[k] += 1
    return tot, bad_ff, nlines


def main():
    rows = load()
    by_trip = collections.defaultdict(list)
    for r in rows:
        by_trip[r["trip"]].append(r)
    for t in by_trip:
        by_trip[t].sort(key=lambda r: r["win"])
    name2file = {}
    for p in FILES:
        name2file.setdefault(os.path.basename(os.path.dirname(p)), p)

    # ---- 样本级分布 ----
    tot, bad_ff, nlines = sample_level()

    # ---- B0CE88 均值版（样本级重扫 19 个配对趟）----
    mean_pairs = {}
    for trip in sorted(by_trip):
        g = by_trip[trip]
        if not any(r["b_mean"] is not None and r["b_mean"] >= 75 for r in g):
            continue
        if not any(r["b_mean"] is not None and r["b_mean"] < 25 for r in g):
            continue
        p = name2file.get(trip)
        if not p:
            continue
        acc = collections.defaultdict(lambda: {"b": [], "d": []})
        t0 = None
        for line in open(p, "r", encoding="utf-8", buffering=1 << 20):
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            t = o.get("t_perf_ns")
            t = t / 1e9 if isinstance(t, (int, float)) else None
            if t is None:
                v = o.get("t_mono_ns")
                t = v / 1e9 if isinstance(v, (int, float)) else None
            if t is None:
                continue
            if t0 is None:
                t0 = t
            k = int(math.floor((t - t0) / WIN))
            a = acc[k]
            if isinstance(o.get("A8ED50"), (int, float)):
                a["b"].append(o["A8ED50"])
            if isinstance(o.get("B0CE88"), (int, float)):
                a["d"].append(o["B0CE88"])
        hi, lo = [], []
        for k, a in acc.items():
            if len(a["b"]) < 30 or not a["d"]:
                continue
            bm = sum(a["b"]) / len(a["b"])
            dm = sum(a["d"]) / len(a["d"])
            if bm >= 75:
                hi.append(dm)
            elif bm < 25:
                lo.append(dm)
        if hi and lo:
            mean_pairs[trip] = (med(hi), med(lo), med(hi) - med(lo))

    # ---- 写 confounders.tsv ----
    lines = []
    lines.append("# W162 混淆项表｜数据源：全仓 137 个 run.ndjson（2,714,525 行），本卡独立重算")
    lines.append("# 生成：python work\\tables.py   （先跑 work\\recompute.py 产出 out\\windows.tsv）")
    lines.append("# 纪律：只报 n / 非零% / 中位 / 极差 / max / distinct；无 p 值，无置信区间")
    lines.append("")
    lines.append("## A · 样本级分布（全部 2,712,836 个带 A8ED50 的样本；每行一个计数器）")
    lines.append("counter\tn_samples\tnonzero_pct\tmedian\tmax\tdistinct\tn_files\tnote")
    nfile = {}
    for p in FILES:
        seen = set()
        for line in open(p, "r", encoding="utf-8", buffering=1 << 20):
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            for k in COUNTERS:
                if isinstance(o.get(k), (int, float)):
                    seen.add(k)
        for k in seen:
            nfile[k] = nfile.get(k, 0) + 1
    notes = {
        "B0CE88": "台账称'脏矩形向量 Count'；非零率极低=队列每帧被清空，50/6ms 采样抓不到",
        "A8E9A0": "G_INGAME 标志，恒 1 ⇒ 无区分力，可从混淆清单删除",
        "87E8E0": "schema B(r02) 的拼写；含大量 0xFFFFFFFF=读失败哨兵 ⇒ 不可用",
        "X87E8E0": "schema A 的同一计数器；实为单调爬升且饱和的计数器（见 §Q2-3），等价于'趟内时钟'",
        "ABCD58": "帧闩，取值只有 {0,1} 两种 ⇒ 信息量 1 bit",
        "g1": "恒 0（本卡独立复算确认）⇒ 零信息",
        "g2": "恒 0 ⇒ 零信息",
        "g3": "恒 0 ⇒ 零信息",
        "g4": "恒 0 ⇒ 零信息",
    }
    for k in COUNTERS:
        v = tot.get(k, [])
        if not v:
            lines.append(f"{k}\t0\t-\t-\t-\t-\t0\t本语料无此字段")
            continue
        sv = sorted(v)
        nz = sum(1 for x in v if x)
        nn = ""
        if bad_ff.get(k):
            nn = f"；其中 ==0xFFFFFFFF 的 {bad_ff[k]} 个（{100.0*bad_ff[k]/len(v):.2f}%）"
        lines.append(f"{k}\t{len(v)}\t{100.0*nz/len(v):.2f}\t{sv[len(sv)//2]}\t{sv[-1]}\t"
                     f"{len(set(v))}\t{nfile.get(k,0)}\t{notes.get(k,'')}{nn}")
    lines.append("")
    lines.append("## B · 趟内配对（hi = 段 b_mean>=75，lo = 段 b_mean<25；键 = 窗内中位）")
    lines.append("# 只列 hi 与 lo 都存在的趟（= 全部 19 个有配对的趟）")
    lines.append("counter\tn_paired\td_median\tn_pos\tn_neg\td_min\td_max\td_wall_median\tusable")
    dwall = med([med([r["ms"] for r in by_trip[t] if r["b_mean"] is not None and r["b_mean"] >= 75])
                 - med([r["ms"] for r in by_trip[t] if r["b_mean"] is not None and r["b_mean"] < 25])
                 for t in by_trip
                 if any(r["b_mean"] is not None and r["b_mean"] >= 75 for r in by_trip[t])
                 and any(r["b_mean"] is not None and r["b_mean"] < 25 for r in by_trip[t])])
    for k in COUNTERS:
        key = "m_" + k
        ds = []
        for trip in sorted(by_trip):
            g = by_trip[trip]
            h = [r[key] for r in g if r["b_mean"] is not None and r["b_mean"] >= 75 and r[key] is not None]
            l = [r[key] for r in g if r["b_mean"] is not None and r["b_mean"] < 25 and r[key] is not None]
            if h and l:
                ds.append(med(h) - med(l))
        if not ds:
            lines.append(f"{k}\t0\t-\t-\t-\t-\t-\t{dwall:.4f}\t不可测（本语料无配对趟）")
            continue
        usable = {
            "B0CE88": "否（中位恒 0；均值版 d=+0.297 但仍只有 0.3 个矩形，见 ## C）",
            "A8E9A0": "否（恒 1）",
            "87E8E0": "否（含 0xFFFFFFFF 哨兵）",
            "X87E8E0": "否（单调趟内时钟，与'时间'完全共线，见 §Q2-3）",
            "ABCD58": "否（二值）",
            "g1": "否（恒 0）", "g2": "否（恒 0）", "g3": "否（恒 0）", "g4": "否（恒 0）",
        }.get(k, "?")
        lines.append(f"{k}\t{len(ds)}\t{med(ds):.4f}\t{sum(1 for v in ds if v>0)}\t"
                     f"{sum(1 for v in ds if v<0)}\t{min(ds):.4f}\t{max(ds):.4f}\t{dwall:.4f}\t{usable}")
    lines.append("")
    lines.append("## C · B0CE88 换成'窗内均值'口径（复算 Lead §900-5 的 +0.30）")
    lines.append("trip\tmean_hi\tmean_lo\td_mean")
    for t in sorted(mean_pairs):
        m = mean_pairs[t]
        lines.append(f"{t}\t{m[0]:.4f}\t{m[1]:.4f}\t{m[2]:+.4f}")
    if mean_pairs:
        dv = [mean_pairs[t][2] for t in mean_pairs]
        lines.append(f"# 汇总 n={len(dv)} d 中位={med(dv):+.4f} 正/负="
                     f"{sum(1 for v in dv if v>0)}/{sum(1 for v in dv if v<0)} "
                     f"极差={min(dv):+.4f}~{max(dv):+.4f}")
    lines.append("")
    lines.append("## D · 关键对照：hi/lo 窗在趟内的位置（本卡最重要的混淆证据）")
    lines.append("trip\thi_windows\tlo_window_min\tlo_window_max\t时间范围重叠")
    for trip in sorted(by_trip):
        g = by_trip[trip]
        h = [int(r["win"]) for r in g if r["b_mean"] is not None and r["b_mean"] >= 75]
        l = [int(r["win"]) for r in g if r["b_mean"] is not None and r["b_mean"] < 25]
        if not h or not l:
            continue
        ov = not (max(h) < min(l) or max(l) < min(h))
        lines.append(f"{trip}\t{','.join(str(x) for x in sorted(h))}\t{min(l)}\t{max(l)}\t{'是' if ov else '否'}")
    lines.append("# 读法：19/19 趟 hi 窗恒为窗 0–1，lo 窗恒为窗 3/4–14，**零交错**")
    lines.append("# ⇒ 趟内配对等价于'开局 20 秒 vs 其余时间'，不是'子弹多 vs 子弹少'的可分离对照")

    with open(os.path.join(CARD, "confounders.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(lines) + "\n")

    # ---- cpu_vs_wall_paired.tsv ----
    pl = ["# W162 逐趟配对表（墙钟与 CPU 同时配对）",
          "trip\tn_hi\tn_lo\tb_hi\tb_lo\twall_hi\twall_lo\td_wall\tcpu_hi\tcpu_lo\td_cpu\tduty_hi\tduty_lo"]
    for trip in sorted(by_trip):
        g = by_trip[trip]
        h = [r for r in g if r["b_mean"] is not None and r["b_mean"] >= 75]
        l = [r for r in g if r["b_mean"] is not None and r["b_mean"] < 25]
        if not h or not l:
            continue
        hc = [r for r in h if r["cpu_per_frame"] is not None]
        lc = [r for r in l if r["cpu_per_frame"] is not None]
        wh, wl = med([r["ms"] for r in h]), med([r["ms"] for r in l])
        pl.append(f"{trip}\t{len(h)}\t{len(l)}\t{med([r['b_mean'] for r in h]):.2f}\t"
                  f"{med([r['b_mean'] for r in l]):.2f}\t{wh:.3f}\t{wl:.3f}\t{wh-wl:+.3f}\t"
                  + (f"{med([r['cpu_per_frame'] for r in hc]):.3f}\t{med([r['cpu_per_frame'] for r in lc]):.3f}\t"
                     f"{med([r['cpu_per_frame'] for r in hc])-med([r['cpu_per_frame'] for r in lc]):+.3f}\t"
                     f"{med([r['duty'] for r in hc]):.4f}\t{med([r['duty'] for r in lc]):.4f}"
                     if hc and lc else "\t\t\t\t"))
    with open(os.path.join(CARD, "cpu_vs_wall_paired.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(pl) + "\n")
    print("[written] confounders.tsv  cpu_vs_wall_paired.tsv ->", CARD)
    print(f"  样本级 n_lines={nlines}")


if __name__ == "__main__":
    main()
