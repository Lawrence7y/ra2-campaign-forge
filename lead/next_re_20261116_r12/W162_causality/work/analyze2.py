# -*- coding: utf-8 -*-
"""W162 第二阶段：时间混淆 / 反例 / X87E8E0 性质 / B0CE88 均值口径对账。

A 段只读 out/windows.tsv（快）。
B 段对有配对的 19 趟做样本级二次扫描（B0CE88 窗内均值、X87E8E0 窗内均值与时间序列）。
"""
import json, os, math, statistics, collections

HERE = os.path.dirname(os.path.abspath(__file__))
WIN = 10.0
FILES = [l.strip() for l in open(os.path.join(HERE, "run_files.txt"), encoding="utf-8") if l.strip()]


def med(v):
    return statistics.median(v) if v else None


def load_windows():
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
                    try:
                        r[k] = float(v)
                    except ValueError:
                        r[k] = None
            rows.append(r)
    return rows


def sect(t):
    print("\n" + "=" * 78)
    print("## " + t)
    print("=" * 78)


# ---------------- A. 时间混淆 ----------------
def part_A(rows):
    by_trip = collections.defaultdict(list)
    for r in rows:
        by_trip[r["trip"]].append(r)
    for t in by_trip:
        by_trip[t].sort(key=lambda r: r["win"])

    sect("A1 · hi / lo 窗在趟内的位置（检验'高子弹窗只是更早'这一替代解释）")
    print("对每个有配对的趟，列出 hi(b>=75) 与 lo(b<25) 的窗口序号，并给")
    print("「hi 窗是否全部早于 lo 窗中位」与「hi 与 lo 是否在时间上交错」。")
    print(f"\n{'trip':40s} {'n_win':>5s} {'hi_wins':>16s} {'lo_win 范围':>14s} {'交错?':>6s}")
    interleave = 0
    npair = 0
    for trip in sorted(by_trip):
        g = by_trip[trip]
        h = [r["win"] for r in g if r["b_mean"] is not None and r["b_mean"] >= 75]
        l = [r["win"] for r in g if r["b_mean"] is not None and r["b_mean"] < 25]
        if not h or not l:
            continue
        npair += 1
        # 交错 = 存在 lo 窗晚于最小 hi 窗 且早于最大 hi 窗；或 hi 与 lo 的时间范围重叠
        overlap = not (max(h) < min(l) or max(l) < min(h))
        if overlap:
            interleave += 1
        print(f"{trip:40s} {len(g):5d} {str(h):>16s} {('%d..%d' % (min(l), max(l))):>14s} "
              f"{'是' if overlap else '否':>6s}")
    print(f"\n有配对趟 = {npair}；hi 与 lo 时间范围重叠（交错）的趟 = {interleave}")

    sect("A2 · 反例：子弹少但 CPU 高（'子弹是必要条件'的反证）")
    sub = [r for r in rows if r["b_mean"] is not None and r["cpu_per_frame"] is not None
           and r["b_mean"] < 25]
    print(f"lo 档（b<25）窗数 = {len(sub)}")
    base = med([r["cpu_per_frame"] for r in sub])
    print(f"这些窗的 cpu_ms/帧 中位 = {base:.3f}")
    for thr in (15, 20, 25, 30, 40, 50):
        g = [r for r in sub if r["cpu_per_frame"] >= thr]
        print(f"  cpu_ms/帧 >= {thr:2d} 的窗 = {len(g):4d}  ({100.0*len(g)/len(sub):5.2f}% of lo 档)"
              + (f"   涉及趟 = {sorted(set(x['trip'] for x in g))[:6]}" if g else ""))
    print("\n最极端的 12 个（b<25 但 cpu/帧 最高）：")
    print(f"{'trip':40s} {'win':>4s} {'b_mean':>7s} {'b_max':>6s} {'wall':>8s} {'cpu/f':>8s} {'duty':>7s}")
    for r in sorted(sub, key=lambda r: -r["cpu_per_frame"])[:12]:
        print(f"{r['trip']:40s} {int(r['win']):4d} {r['b_mean']:7.2f} {(r['b_max'] or 0):6.0f} "
              f"{r['ms']:8.2f} {r['cpu_per_frame']:8.2f} {r['duty']:7.4f}")

    sect("A3 · 高子弹窗里 CPU 是否总高于 lo 档（同向性）")
    hi = [r for r in rows if r["b_mean"] is not None and r["b_mean"] >= 75
          and r["cpu_per_frame"] is not None]
    lo_thr = med([r["cpu_per_frame"] for r in sub])
    print(f"hi(b>=75) 窗 = {len(hi)}；其中 cpu/帧 低于 lo 档中位({lo_thr:.2f}) 的 = "
          f"{sum(1 for r in hi if r['cpu_per_frame'] < lo_thr)}")
    print(f"  hi 档 cpu/帧 极差 = {min(r['cpu_per_frame'] for r in hi):.2f} ~ "
          f"{max(r['cpu_per_frame'] for r in hi):.2f}")

    sect("A4 · 分桶局部斜率（cpu/帧 与 wall 对 b 的斜率，逐档）")
    BUCKETS = [(0, 25), (25, 50), (50, 75), (75, 100), (100, 125)]
    prev = None
    print(f"{'bucket':>10s} {'n':>5s} {'b_med':>7s} {'cpu_med':>8s} {'wall_med':>8s} "
          f"{'dcpu/25发':>10s} {'dwall/25发':>10s}")
    pts = []
    for lo_, hi_ in BUCKETS:
        g = [r for r in rows if r["b_mean"] is not None and lo_ <= r["b_mean"] < hi_
             and r["cpu_per_frame"] is not None]
        if not g:
            continue
        pt = (lo_, med([r["b_mean"] for r in g]), med([r["cpu_per_frame"] for r in g]),
              med([r["ms"] for r in g]))
        pts.append(pt)
        s1 = s2 = ""
        if prev:
            s1 = f"{(pt[2]-prev[2]):+10.2f}"
            s2 = f"{(pt[3]-prev[3]):+10.2f}"
        print(f"{lo_:5d}-{hi_:<4d} {len(g):5d} {pt[1]:7.2f} {pt[2]:8.2f} {pt[3]:8.2f} {s1} {s2}")
        prev = pt
    print("\n局部斜率（相邻桶差 / 子弹中位差）：")
    for i in range(1, len(pts)):
        db = pts[i][1] - pts[i - 1][1]
        if abs(db) < 1e-9:
            continue
        print(f"  桶 {pts[i-1][0]:3d}->{pts[i][0]:3d}: dcpu/db = {(pts[i][2]-pts[i-1][2])/db:+.4f} ms/发 ; "
              f"dwall/db = {(pts[i][3]-pts[i-1][3])/db:+.4f} ms/发")

    sect("A5 · 墙钟是否被 32 ms 地板挡住（两段式模型的直接检验）")
    print("若 wall = max(地板, f(cpu))，则 cpu<=地板时应看到 wall≈32 且与 cpu 无关。")
    cand = [r for r in rows if r["cpu_per_frame"] is not None and r["cpu_per_frame"] <= 31.9]
    print(f"cpu/帧 <= 31.9 的窗 = {len(cand)}")
    if cand:
        v = [r["ms"] for r in cand]
        print(f"  这些窗的 wall：min={min(v):.3f} med={med(v):.3f} p90={sorted(v)[9*len(v)//10]:.3f} max={max(v):.3f}")
        print(f"  其中 wall 仍 > 40 ms 的 = {sum(1 for x in v if x > 40)}")
        cc = [r["cpu_per_frame"] for r in cand]
        print(f"  这些窗的 cpu/帧：min={min(cc):.2f} med={med(cc):.2f} max={max(cc):.2f}")
        # 相关性方向：cpu 与 wall 在"地板以下"区间是否脱钩
        low = [r for r in cand if r["cpu_per_frame"] < 10]
        mid = [r for r in cand if 10 <= r["cpu_per_frame"] <= 31.9]
        if low and mid:
            print(f"  cpu/帧<10 (n={len(low)}): wall 中位 {med([r['ms'] for r in low]):.3f}")
            print(f"  10<=cpu/帧<=31.9 (n={len(mid)}): wall 中位 {med([r['ms'] for r in mid]):.3f}")
            print("  ⇒ 两者 wall 中位差 = %.3f ms" % (med([r['ms'] for r in mid]) - med([r['ms'] for r in low])))

    sect("A6 · 墙钟 > 40 ms 的窗里，cpu/帧 与 wall 的关系")
    above = [r for r in rows if r["cpu_per_frame"] is not None and r["ms"] > 40]
    print(f"n={len(above)}")
    if above:
        q = sorted(above, key=lambda r: r["cpu_per_frame"])
        for i in range(0, len(q), max(1, len(q) // 10)):
            r = q[i]
            print(f"  cpu/f={r['cpu_per_frame']:7.2f}  wall={r['ms']:8.2f}  b={r['b_mean']:6.1f}  "
                  f"duty={r['duty']:.3f}  {r['trip']} win{int(r['win'])}")
        d = [r["ms"] - r["cpu_per_frame"] for r in above]
        print(f"  (wall - cpu/帧) 中位 = {med(d):+.2f} ms ；极差 {min(d):+.2f} ~ {max(d):+.2f}")


# ---------------- B. 样本级：B0CE88 均值口径 / X87E8E0 性质 ----------------
def part_B(rows):
    by_trip = collections.defaultdict(list)
    for r in rows:
        by_trip[r["trip"]].append(r)
    fmap = {}
    for r in rows:
        fmap[r["trip"]] = None
    # 用 windows.tsv 里的 trip 名反查文件
    import hashlib
    name2file = {}
    for p in FILES:
        name2file.setdefault(os.path.basename(os.path.dirname(p)), p)

    sect("B1 · B0CE88 的窗内均值（与中位对照）——解释与 Lead §900-5 的口径差")
    print(f"{'trip':40s} {'b_hi':>6s} {'b_lo':>6s} {'mean_hi':>8s} {'mean_lo':>8s} {'d_mean':>8s} "
          f"{'med_hi':>7s} {'med_lo':>7s}")
    ds = []
    for trip in sorted(by_trip):
        p = name2file.get(trip)
        if not p:
            continue
        g = by_trip[trip]
        if not any(r["b_mean"] is not None and r["b_mean"] >= 75 for r in g):
            continue
        if not any(r["b_mean"] is not None and r["b_mean"] < 25 for r in g):
            continue
        # 二次扫描该文件
        acc = collections.defaultdict(lambda: {"b": [], "d": [], "g": []})
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
            if "_t0" not in acc:
                acc["_t0"] = t
            k = int(math.floor((t - acc["_t0"]) / WIN))
            a = acc[k]
            if isinstance(o.get("A8ED50"), (int, float)):
                a["b"].append(o["A8ED50"])
            if isinstance(o.get("B0CE88"), (int, float)):
                a["d"].append(o["B0CE88"])
            gv = o.get("X87E8E0")
            if isinstance(gv, (int, float)):
                a["g"].append(gv)
        hi_d, lo_d = [], []
        hi_m, lo_m = [], []
        for k, a in acc.items():
            if k == "_t0" or len(a["b"]) < 30:
                continue
            bm = sum(a["b"]) / len(a["b"])
            if not a["d"]:
                continue
            dm = sum(a["d"]) / len(a["d"])
            if bm >= 75:
                hi_d.append(dm)
                hi_m.append(statistics.median(a["d"]))
            elif bm < 25:
                lo_d.append(dm)
                lo_m.append(statistics.median(a["d"]))
        if not hi_d or not lo_d:
            continue
        dh = statistics.median(hi_d) - statistics.median(lo_d)
        ds.append(dh)
        print(f"{trip:40s} {'':>6s} {'':>6s} {statistics.median(hi_d):8.3f} "
              f"{statistics.median(lo_d):8.3f} {dh:+8.3f} {statistics.median(hi_m):7.1f} "
              f"{statistics.median(lo_m):7.1f}")
    if ds:
        print(f"\nB0CE88 窗内均值：配对趟 {len(ds)}；d 中位 {med(ds):+.4f}；"
              f"正/负 {sum(1 for v in ds if v>0)}/{sum(1 for v in ds if v<0)}；"
              f"极差 {min(ds):+.4f} ~ {max(ds):+.4f}")

    sect("B2 · X87E8E0 是什么？（时间序列 + 与 b 的关系）")
    for trip in ("trip_carrier2_r1", "trip_scan_near_r1"):
        p = name2file.get(trip)
        if not p:
            continue
        g = sorted(by_trip[trip], key=lambda r: r["win"])
        print(f"\n--- {trip}（windows.tsv 里的 m_X87E8E0 = 窗内中位）")
        print(f"{'win':>4s} {'b_mean':>7s} {'wall':>8s} {'cpu/f':>8s} {'m_X87E8E0':>11s}")
        for r in g:
            print(f"{int(r['win']):4d} {(r['b_mean'] or 0):7.2f} {r['ms']:8.2f} "
                  f"{(r['cpu_per_frame'] or 0):8.2f} "
                  + (f"{r['m_X87E8E0']:11.0f}" if r["m_X87E8E0"] is not None else f"{'-':>11s}"))

    sect("B3 · 87E8E0 / X87E8E0 的 0xFFFFFFFF 计数（读失败哨兵）")
    cnt_bad = collections.Counter()
    cnt_tot = collections.Counter()
    for p in FILES:
        name = os.path.basename(os.path.dirname(p))
        for line in open(p, "r", encoding="utf-8", buffering=1 << 20):
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            for key in ("87E8E0", "X87E8E0"):
                v = o.get(key)
                if isinstance(v, (int, float)):
                    cnt_tot[key] += 1
                    if v == 4294967295:
                        cnt_bad[key] += 1
    for key in ("87E8E0", "X87E8E0"):
        print(f"  {key:9s} n={cnt_tot[key]:9d}  ==0xFFFFFFFF 的 = {cnt_bad[key]:8d} "
              f"({100.0*cnt_bad[key]/max(1,cnt_tot[key]):5.2f}%)")


def main():
    rows = load_windows()
    part_A(rows)
    part_B(rows)


if __name__ == "__main__":
    main()
