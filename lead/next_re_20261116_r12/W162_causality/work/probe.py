# -*- coding: utf-8 -*-
"""W162 probe: 用前先确认语义。
1) schema A 的 `mode` 与 schema B 的 `mode_A8B238` 取值分布（两者是不是同一个东西？）
2) win_cpu_ms_delta 的取值网格（15.625 ms 量化？）
3) g1..g4 / A8E9A0 / ABCD58 / 87E8E0 的取值分布
4) win_tid 是否每趟唯一；win_cpu_ms 是否 0 回退
5) W15/W18/W19/W20 的 sum_all_threads_cpu_ms vs win_cpu_ms（线程 vs 全进程）
"""
import json, os, collections

FILES = [l.strip() for l in open(
    os.path.join(os.path.dirname(__file__), "run_files.txt"), encoding="utf-8") if l.strip()]

SAMPLE = [
    # (tag, path-fragment)
    ("A_carrier2", r"W110_crash\out\_archive_carrier2\trip_carrier2_r1"),
    ("A_ctrl_orig", r"W110_crash\out\_archive_ctrl_orig\trip_ctrl_orig_r1"),
    ("A_range1", r"W110_crash\out\_archive_range1\trip_range1_r1"),
    ("B_W15", r"r02\W15_tick_cpu"),
    ("B_W20", r"r02\W20_combat"),
    ("B_W13", r"r02\W13_longrun_drift"),
    ("A_W94c2", r"W94_batchrun\EVIDENCE\out\trip_c2_r1"),
]


def pick(frag):
    for p in FILES:
        if frag in p:
            return p
    return None


def quant_hist(vals, grid, tol=1e-6):
    """值相对 grid 的整数倍偏离"""
    c = collections.Counter()
    bad = 0
    for v in vals:
        if v <= 0:
            continue
        k = round(v / grid)
        if abs(v - k * grid) <= tol:
            c[k] += 1
        else:
            bad += 1
    return c, bad


def main():
    for tag, frag in SAMPLE:
        p = pick(frag)
        if not p:
            print(f"!! not found {frag}")
            continue
        n = 0
        modes = collections.Counter()
        deltas = []
        ctr = collections.defaultdict(list)
        tids = set()
        cpu = []
        prev = None
        regress = 0
        sumall = []
        nthreads = set()
        for line in open(p, "r", encoding="utf-8", buffering=1 << 20):
            line = line.strip()
            if not line:
                continue
            n += 1
            o = json.loads(line)
            if "mode" in o and o["mode"] is not None:
                modes["mode=%s" % o["mode"]] += 1
            if "mode_A8B238" in o and o["mode_A8B238"] is not None:
                modes["A8B238=%s" % o["mode_A8B238"]] += 1
            d = o.get("win_cpu_ms_delta")
            if isinstance(d, (int, float)):
                deltas.append(d)
            for k in ("A8ED50", "B0CE88", "A8E9A0", "87E8E0", "X87E8E0",
                      "ABCD58", "g1", "g2", "g3", "g4"):
                v = o.get(k)
                if isinstance(v, (int, float)):
                    ctr[k].append(v)
            if o.get("win_tid") is not None:
                tids.add(o["win_tid"])
            c = o.get("win_cpu_ms")
            if isinstance(c, (int, float)):
                cpu.append(c)
                if prev is not None and c < prev:
                    regress += 1
                prev = c
            if isinstance(o.get("sum_all_threads_cpu_ms"), (int, float)):
                sumall.append(o["sum_all_threads_cpu_ms"])
            if o.get("n_threads") is not None:
                nthreads.add(o["n_threads"])

        print(f"\n===== {tag}  n={n}")
        print(f"  path = {p}")
        print(f"  mode keys: {dict(modes)}")
        print(f"  win_tid set = {sorted(tids)[:5]} (|set|={len(tids)})")
        if cpu:
            print(f"  win_cpu_ms: first={cpu[0]} last={cpu[-1]} regressions={regress}")
        if deltas:
            nz = [d for d in deltas if d > 0]
            c, bad = quant_hist(nz, 15.625, tol=1e-4)
            print(f"  delta: n={len(deltas)} nonzero={len(nz)} zero={len(deltas)-len(nz)}")
            print(f"  delta 非零值 -> 15.625*k 网格：k 分布 {dict(sorted(c.items()))}  off_grid={bad}")
            print(f"  delta sum = {round(sum(deltas),3)}")
        if cpu and deltas:
            print(f"  check |cum_diff - sum(delta)| = "
                  f"{abs((cpu[-1]-cpu[0]) - sum(deltas)):.6f}")
        for k, v in ctr.items():
            sv = sorted(v)
            nz = sum(1 for x in v if x)
            print(f"  {k:8s} n={len(v):6d} nonzero={nz:6d} ({100.0*nz/len(v):5.1f}%) "
                  f"min={sv[0]} med={sv[len(sv)//2]} max={sv[-1]} distinct={len(set(v))}")
        if sumall:
            print(f"  sum_all_threads_cpu_ms: first={sumall[0]} last={sumall[-1]} n={len(sumall)}")
            if cpu:
                i_first = None
                print(f"  win_cpu_ms first={cpu[0]} last={cpu[-1]}")
                print(f"  => 全进程/窗线程 比 = {(sumall[-1]-sumall[0])/max(1e-9,(cpu[-1]-cpu[0])):.3f}")
            print(f"  n_threads = {sorted(nthreads)[:6]} (|set|={len(nthreads)})")


if __name__ == "__main__":
    main()
