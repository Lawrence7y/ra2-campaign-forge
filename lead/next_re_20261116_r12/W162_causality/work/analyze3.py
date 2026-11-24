# -*- coding: utf-8 -*-
"""W162 第三阶段：107.5 ms 第二模态 / 去掉开局两窗后关系是否还在 / 稳健性。"""
import os, statistics, collections

HERE = os.path.dirname(os.path.abspath(__file__))


def med(v):
    return statistics.median(v) if v else None


def sect(t):
    print("\n" + "=" * 78)
    print("## " + t)
    print("=" * 78)


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


def main():
    rows = load()
    by_trip = collections.defaultdict(list)
    for r in rows:
        by_trip[r["trip"]].append(r)
    for t in by_trip:
        by_trip[t].sort(key=lambda r: r["win"])

    sect("C1 · 墙钟的第二个固定模态（~107.5 ms）：是算还是等？")
    g = [r for r in rows if 106.0 <= r["ms"] <= 110.0]
    print(f"ms∈[106,110] 的窗 = {len(g)}  （占全部 {100.0*len(g)/len(rows):.2f}%）")
    pertrip = collections.Counter(r["trip"] for r in g)
    for t, c in pertrip.most_common():
        gg = [r for r in g if r["trip"] == t]
        cp = med([r["cpu_per_frame"] for r in gg if r["cpu_per_frame"] is not None])
        du = med([r["duty"] for r in gg if r["duty"] is not None])
        print(f"  {t:32s} n={c:3d}  ms极差 {min(r['ms'] for r in gg):7.2f}~{max(r['ms'] for r in gg):7.2f} "
              f" cpu/f 中位 {cp if cp is not None else float('nan'):6.2f}"
              f"  duty 中位 {du if du is not None else float('nan'):6.4f}"
              f"  b 中位 {med([r['b_mean'] for r in gg]):5.2f}")
    print("\n读法：多个**互相独立的趟**在同一 ~107.5 ms 上取值，且 cpu/帧 只有它的一半 ⇒ 固定节拍（在等），不是算出来的。")

    sect("C2 · 去掉开局两窗（win 0,1）后，b 与 cpu 的关系还在不在")
    print("A1 已证 hi 窗恒在 win 0–1。若把 win 0–1 全删，剩下的 win>=2 里 b 与 cpu/帧")
    print("是否仍然同向变动？（相邻窗口对的符号一致率，纯计数，不报 p）")
    print(f"\n{'trip':40s} {'n_pairs':>7s} {'符号一致':>8s} {'不一致':>7s} {'同向率':>7s}")
    tot_ok = tot_n = 0
    all_pairs = []
    for trip in sorted(by_trip):
        g2 = [r for r in by_trip[trip] if r["win"] >= 2 and r["b_mean"] is not None
              and r["cpu_per_frame"] is not None]
        ok = bad = 0
        for i in range(1, len(g2)):
            db = g2[i]["b_mean"] - g2[i - 1]["b_mean"]
            dc = g2[i]["cpu_per_frame"] - g2[i - 1]["cpu_per_frame"]
            if db == 0 or dc == 0:
                continue
            if (db > 0) == (dc > 0):
                ok += 1
            else:
                bad += 1
        if ok + bad == 0:
            continue
        tot_ok += ok
        tot_n += ok + bad
        all_pairs.append((trip, ok, bad))
        print(f"{trip:40s} {ok+bad:7d} {ok:8d} {bad:7d} {100.0*ok/(ok+bad):6.1f}%")
    print(f"\n合计：相邻窗对 {tot_n}；b 与 cpu 符号一致 {tot_ok} ({100.0*tot_ok/max(1,tot_n):.1f}%)")

    sect("C3 · 每发的 CPU 增量在全语料的分布（不用均值）")
    print("逐趟取 'b>=75 的窗' 与 'b<25 的窗' 的 cpu/帧 差 / b 差，得到每趟的 ms/发")
    vals = []
    for trip in sorted(by_trip):
        h = [r for r in by_trip[trip] if r["b_mean"] is not None and r["b_mean"] >= 75
             and r["cpu_per_frame"] is not None]
        l = [r for r in by_trip[trip] if r["b_mean"] is not None and r["b_mean"] < 25
             and r["cpu_per_frame"] is not None]
        if not h or not l:
            continue
        db = med([r["b_mean"] for r in h]) - med([r["b_mean"] for r in l])
        dc = med([r["cpu_per_frame"] for r in h]) - med([r["cpu_per_frame"] for r in l])
        if db <= 0:
            continue
        vals.append(dc / db)
    print(f"n={len(vals)} 中位={med(vals):.4f} 极差={min(vals):.4f}~{max(vals):.4f}")
    print("逐值（升序）: " + ", ".join("%.3f" % v for v in sorted(vals)))

    sect("C4 · 稳健性：换口径后分桶是否还成立")
    variants = {
        "P  (全部合格窗)": rows,
        "P1 (剔 ms>110 的挂起/固定节拍窗)": [r for r in rows if r["ms"] <= 110],
        "P2 (剔 mode=2 的 6 个 W94 趟)": [r for r in rows if not r["cpu_src"] == "delta"],
        "P3 (剔 trip_range1_r1)": [r for r in rows if r["trip"] != "trip_range1_r1"],
        "P4 (只留 cpu>=3 ms/帧 的窗)": [r for r in rows
                                       if r["cpu_per_frame"] is None or r["cpu_per_frame"] >= 3],
    }
    BUCK = [(0, 25), (25, 50), (50, 75), (75, 100), (100, 125)]
    print(f"{'variant':36s} {'n':>5s} " + " ".join(f"{('%d-%d' % b):>8s}" for b in BUCK)
          + f" {'ratio':>7s}")
    for name, rs in variants.items():
        cells = []
        for lo, hi in BUCK:
            g3 = [r for r in rs if r["b_mean"] is not None and lo <= r["b_mean"] < hi]
            cells.append(f"{len(g3):5d}/{med([r['ms'] for r in g3]) if g3 else 0:5.2f}")
        a = med([r["ms"] for r in rs if r["b_mean"] is not None and 0 <= r["b_mean"] < 25])
        b = med([r["ms"] for r in rs if r["b_mean"] is not None and 100 <= r["b_mean"] < 125])
        print(f"{name:36s} {len(rs):5d} " + " ".join(f"{c:>8s}" for c in cells)
              + (f" {b/a:7.3f}" if a and b else "      -"))

    sect("C5 · CPU 分桶表的稳健性（剔挂起窗后）")
    for name, rs in variants.items():
        cells = []
        for lo, hi in BUCK:
            g3 = [r for r in rs if r["b_mean"] is not None and lo <= r["b_mean"] < hi
                  and r["cpu_per_frame"] is not None]
            cells.append(f"{len(g3):4d}/{med([r['cpu_per_frame'] for r in g3]) if g3 else 0:6.2f}"
                         f"/{med([r['duty'] for r in g3]) if g3 else 0:.3f}")
        print(f"{name:36s} " + "  ".join(cells))
    print("（格式 n/cpu中位/duty中位）")


if __name__ == "__main__":
    main()
