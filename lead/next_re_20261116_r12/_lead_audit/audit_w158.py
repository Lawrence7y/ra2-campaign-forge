"""Lead 抽验 W158 的 LEAD_AUDIT A-1/A-3/A-4/A-6/A-7。全部用自己的实现。

A-1  trip_c2_near_r2 的 A8ED50 max = 258；>250 计 10；>=250 计 23
A-3  纳入趟/段 = 82 / 1161（段规则见下）
A-4  总行数 2,714,525，文件 137
A-6  "A8EC" 子串在 137 个文件里 0 次
A-7  us_hi_n1770 / us_lo_n1230 的 design units 数都是 1500

A-3 的段规则（照 W158 描述，我独立实现）：
  每个 10 s 窗：ms = Δt_ms/Δframe；b = mean(A8ED50)；
  留 span>=9.0s、Δframe>=1、n>=30、ms<=200、整窗 mode==0；
  趟名不含 "crash_step2"
  "段" = 合格窗。
"""
import json
import os
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
LIST = os.path.join(ROOT, r"lead\next_re_20261116_r12\_lead_audit\run_files.txt")


def load(files):
    out = []
    for p in files:
        rows = []
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                if '"sample"' not in line:
                    continue
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                if o.get("kind") != "sample" or o.get("read_status") != "ok":
                    continue
                t = o.get("t_mono_ns")
                if t is None:
                    ts = o.get("t_monotonic")
                    t = int(round(float(ts) * 1e9)) if ts is not None else o.get("t_perf_ns")
                if t is None:
                    continue
                mode = o.get("mode_A8B238")
                if mode is None:
                    mode = o.get("mode")
                rows.append((int(t), o.get("frame"), o.get("A8ED50"), mode))
        rows.sort(key=lambda r: r[0])
        if rows:
            out.append((p, rows))
    return out


def segments(rows, window_s=10.0):
    if not rows:
        return []
    base = rows[0][0]
    span = window_s * 1e9
    res = []
    i = 0
    n = len(rows)
    while i < n:
        j = i
        b0 = rows[i][0]
        while j < n and rows[j][0] - b0 < span:
            j += 1
        c = rows[i:j]
        i = j if j > i else i + 1
        if len(c) < 30:
            continue
        t_span = (c[-1][0] - c[0][0]) / 1e9
        if t_span < 9.0:
            continue
        df = (c[-1][1] - c[0][1]) if isinstance(c[-1][1], int) and isinstance(c[0][1], int) else 0
        if df < 1:
            continue
        ms = (c[-1][0] - c[0][0]) / 1e6 / df
        if ms > 200:
            continue
        modes = {x[3] for x in c}
        if modes != {0}:
            continue
        bmean = sum(x[2] for x in c) / len(c)
        res.append(dict(ms=ms, b=bmean))
    return res


def main():
    files = [ln.strip() for ln in open(LIST, encoding="utf-8") if ln.strip()]
    print("files = %d" % len(files))

    # A-1
    p1 = os.path.join(ROOT, r"lead\next_re_20261112_r10\W110_crash\out\_archive_c2\trip_c2_near_r2\run.ndjson")
    mx = -1
    gt250 = ge250 = 0
    with open(p1, encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"sample"' not in line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("kind") != "sample":
                continue
            b = o.get("A8ED50")
            if b is None:
                continue
            mx = max(mx, b)
            if b > 250:
                gt250 += 1
            if b >= 250:
                ge250 += 1
    print("A-1  A8ED50 max=%d  >250=%d  >=250=%d   (want 258 / 10 / 23)" % (mx, gt250, ge250))

    # A-4
    total_lines = 0
    for p in files:
        try:
            with open(p, "rb") as f:
                total_lines += sum(1 for ln in f if ln.strip())
        except Exception:
            pass
    print("A-4  total non-empty lines = %d  files=%d   (want 2714525 / 137)" % (total_lines, len(files)))

    # A-6
    hit = 0
    for p in files:
        with open(p, "rb") as f:
            hit += f.read().count(b"A8EC") + f.read().count(b"A8EC")
    # 上面写法重复读，改为一次
    hit = 0
    for p in files:
        with open(p, "rb") as f:
            hit += f.read().count(b"A8EC")
    print("A-6  'A8EC' byte hits = %d   (want 0)" % hit)

    # A-3
    loaded = load(files)
    n_trip = 0
    n_seg = 0
    for p, rows in loaded:
        if "crash_step2" in p:
            continue
        s = segments(rows)
        if s:
            n_trip += 1
            n_seg += len(s)
    print("A-3  included trips=%d segments=%d   (want 82 / 1161)" % (n_trip, n_seg))

    # A-7
    print("A-7  design units:")
    for pat in ("trip_us_hi_n1770_r1", "trip_us_lo_n1230_r1"):
        d = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W110_crash", "out", "_archive_us2", pat)
        found = []
        for dirpath, _, fnames in os.walk(d):
            for fn in fnames:
                if fn.startswith("w94_design") and fn.endswith(".json"):
                    fp = os.path.join(dirpath, fn)
                    try:
                        doc = json.load(open(fp, encoding="utf-8"))
                        nu = len(doc["missions"][0]["units"])
                        found.append((fp, nu))
                    except Exception as e:
                        found.append((fp, "ERR:%s" % e))
        print("     %s -> %s" % (pat, found))


if __name__ == "__main__":
    main()
