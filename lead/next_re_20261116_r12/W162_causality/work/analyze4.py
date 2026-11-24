# -*- coding: utf-8 -*-
"""W162 第四阶段：cpu/帧 跟"窗序（趟内相位）"还是跟"子弹数"？
纯计数，不报 p。"""
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

    sect("D1 · 相邻窗对：cpu/帧 与 b 同号 vs cpu/帧 随窗序下降，谁更一致？")
    print("（只看 win>=2 的相邻对；纯计数。末行加幅度门，避免把尾段 0↔3 发的抖动当信号）")
    print(f"{'scope':30s} {'pairs':>6s} {'cpu↓':>7s} {'b↓':>7s} {'b↑&cpu↓':>8s} "
          f"{'同号':>7s} {'反向':>7s} {'同号占比':>9s}")
    for scope, minwin, minabs in (
            ("win>=2 全部相邻对", 2, 0.0),
            ("win>=2 |Δb|>=5 发", 2, 5.0),
            ("win>=2 |Δb|>=10 发", 2, 10.0),
            ("全部窗体 |Δb|>=5 发", 0, 5.0)):
        n = cpu_dn = b_dn = agree = cross = up_down = 0
        for trip in by_trip:
            g = [r for r in by_trip[trip] if r["win"] >= minwin
                 and r["b_mean"] is not None and r["cpu_per_frame"] is not None]
            for i in range(1, len(g)):
                db = g[i]["b_mean"] - g[i - 1]["b_mean"]
                dc = g[i]["cpu_per_frame"] - g[i - 1]["cpu_per_frame"]
                if abs(db) < minabs:
                    continue
                n += 1
                if dc < 0:
                    cpu_dn += 1
                if db < 0:
                    b_dn += 1
                if db != 0 and dc != 0:
                    if (db > 0) == (dc > 0):
                        agree += 1
                    else:
                        cross += 1
                        if db > 0 and dc < 0:
                            up_down += 1
        print(f"{scope:30s} {n:6d} {cpu_dn:7d} {b_dn:7d} {up_down:8d} "
              f"{agree:7d} {cross:7d} {100.0*agree/max(1,agree+cross):8.1f}%")

    sect("D2 · 每趟的 'ms/发' 在两种对照下的差别（range1 是反例）")
    print(f"{'trip':32s} {'b_win0':>7s} {'b_win14':>7s} {'cpu_win0':>8s} {'cpu_win14':>9s} "
          f"{'dB':>7s} {'dCPU':>8s} {'ms/发 端点':>10s}")
    for trip in ("trip_carrier2_r1", "trip_scan_near_r1", "trip_range1_r1",
                 "trip_m4_slow_player_r1", "trip_c2_near_r2"):
        g = by_trip.get(trip)
        if not g:
            continue
        a, b = g[0], g[-1]
        if a["cpu_per_frame"] is None or b["cpu_per_frame"] is None:
            continue
        db = a["b_mean"] - b["b_mean"]
        dc = a["cpu_per_frame"] - b["cpu_per_frame"]
        print(f"{trip:32s} {a['b_mean']:7.2f} {b['b_mean']:7.2f} {a['cpu_per_frame']:8.2f} "
              f"{b['cpu_per_frame']:9.2f} {db:7.2f} {dc:8.2f} "
              f"{(dc/db if db>0 else float('nan')):10.3f}")

    sect("D3 · 楼板段：cpu/帧 在 [10,31.9] 与 [<10] 的墙钟差（决定性）")
    cand = [r for r in rows if r["cpu_per_frame"] is not None and r["cpu_per_frame"] <= 31.9]
    bins = [(0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, 31.9)]
    print(f"{'cpu/帧 区间':>14s} {'n':>5s} {'wall 中位':>10s} {'wall 极差':>20s} {'duty 中位':>9s}")
    for lo, hi in bins:
        g = [r for r in cand if lo <= r["cpu_per_frame"] < hi]
        if not g:
            continue
        v = [r["ms"] for r in g]
        print(f"{lo:5.0f}-{hi:<8.1f} {len(g):5d} {med(v):10.3f} "
              f"{min(v):9.3f}~{max(v):9.3f} {med([r['duty'] for r in g]):9.4f}")
    print("\n读法：cpu/帧 从 <5 涨到 31.9（6 倍）而 wall 中位几乎不动 ⇒ 该区间墙钟被地板钉住。")

    sect("D4 · 超过地板后：wall 与 cpu/帧 的比值")
    above = [r for r in rows if r["cpu_per_frame"] is not None and r["cpu_per_frame"] > 31.9]
    print(f"cpu/帧 > 31.9 的窗 = {len(above)}")
    if above:
        rat = [r["ms"] / r["cpu_per_frame"] for r in above]
        print(f"  wall/(cpu/帧) 中位 = {med(rat):.4f}；极差 {min(rat):.4f} ~ {max(rat):.4f}")
        d = [r["ms"] - r["cpu_per_frame"] for r in above]
        print(f"  wall - cpu/帧 中位 = {med(d):+.3f} ms；极差 {min(d):+.3f} ~ {max(d):+.3f}")
        print(f"  其中 wall < cpu/帧（比值<1）的窗 = {sum(1 for x in rat if x < 1)}")
        gc = sorted(above, key=lambda r: r["cpu_per_frame"])
        print("\n  逐段（按 cpu/帧 排序，每 1/10 取一点）：")
        print(f"  {'cpu/帧':>8s} {'wall':>8s} {'duty':>7s} {'wall-cpu':>9s} {'b':>7s}  trip")
        for i in range(0, len(gc), max(1, len(gc) // 12)):
            r = gc[i]
            print(f"  {r['cpu_per_frame']:8.2f} {r['ms']:8.2f} {r['duty']:7.4f} "
                  f"{r['ms']-r['cpu_per_frame']:+9.2f} {r['b_mean']:7.1f}  {r['trip']}")


if __name__ == "__main__":
    main()
