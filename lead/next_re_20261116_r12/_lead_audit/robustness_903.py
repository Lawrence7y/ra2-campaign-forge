"""§903 的稳健性自检：换窗口长度 / 最小样本数 / 最大 ms 门限，
看 "range1（低子弹）CPU 反而高于 c2_near（高子弹）" 这个结论是否稳定。
"""
import json
import statistics as st

FILES = {
    "range1":  r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out\_archive_range1\trip_range1_r1\run.ndjson",
    "c2_near": r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out\_archive_c2\trip_c2_near_r1\run.ndjson",
}


def load(path):
    rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"sample"' not in line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("kind") != "sample" or o.get("read_status") != "ok":
                continue
            t = o.get("t_perf_ns") or o.get("t_mono_ns")
            if t is None:
                ts = o.get("t_monotonic")
                t = int(round(float(ts) * 1e9)) if ts is not None else None
            if t is None:
                continue
            rows.append((int(t), o.get("frame"), o.get("A8ED50"), o.get("win_cpu_ms")))
    rows.sort(key=lambda r: r[0])
    return rows


def windows(rows, ws, mn, mx):
    if not rows:
        return []
    span = ws * 1e9
    out = []
    i, n = 0, len(rows)
    while i < n:
        j = i
        base = rows[i][0]
        while j < n and rows[j][0] - base < span:
            j += 1
        c = rows[i:j]
        i = j if j > i else i + 1
        if len(c) < mn:
            continue
        df = c[-1][1] - c[0][1]
        if df <= 0:
            continue
        dt = (c[-1][0] - c[0][0]) / 1e6
        ms = dt / df
        if ms > mx:
            continue
        cpu = (c[-1][3] - c[0][3]) if (c[-1][3] is not None and c[0][3] is not None) else None
        out.append(dict(ms=ms, b=st.mean(x[2] for x in c), cpu=(cpu / df if cpu else None)))
    return out


def first_n_cpu(ws, mn, mx, n=1):
    res = {}
    for label, p in FILES.items():
        w = windows(load(p), ws, mn, mx)
        res[label] = (w[:n], len(w))
    return res


def main():
    print("稳健性：range1(低弹) vs c2_near(高弹) 的前 N 个窗 CPU/帧")
    print("%-22s %-28s %-28s %s" % ("口径", "range1 (b, cpu)", "c2_near (b, cpu)", "range1 更高?"))
    for ws in (5.0, 10.0, 20.0):
        for mn in (4, 30, 100):
            for mx in (200.0, 10000.0):
                r = first_n_cpu(ws, mn, mx, n=1)
                w1, n1 = r["range1"]
                w2, n2 = r["c2_near"]
                if not w1 or not w2:
                    print("%-22s %-28s %-28s %s" % ("ws=%.0f mn=%d mx=%.0f" % (ws, mn, mx), "(no win n=%d)" % n1, "(no win n=%d)" % n2, "-"))
                    continue
                a, b = w1[0], w2[0]
                hi = a["cpu"] > b["cpu"] if (a["cpu"] and b["cpu"]) else None
                print("%-22s %-28s %-28s %s"
                      % ("ws=%.0f mn=%-3d mx=%-5.0f" % (ws, mn, mx),
                         "(%.1f, %s)" % (a["b"], "%.2f" % a["cpu"] if a["cpu"] else "-"),
                         "(%.1f, %s)" % (b["b"], "%.2f" % b["cpu"] if b["cpu"] else "-"),
                         "YES" if hi else ("no" if hi is False else "?")))

    print()
    print("=== 全窗中位（ws=10, mn=4, mx=200）===")
    for label, p in FILES.items():
        w = windows(load(p), 10.0, 4, 200.0)
        cpus = [x["cpu"] for x in w if x["cpu"]]
        bs = [x["b"] for x in w]
        print("  %-8s n_win=%-3d b: min %.2f med %.2f max %.2f | cpu/f: min %.2f med %.2f max %.2f"
              % (label, len(w), min(bs), st.median(bs), max(bs),
                 min(cpus), st.median(cpus), max(cpus)))


if __name__ == "__main__":
    main()
