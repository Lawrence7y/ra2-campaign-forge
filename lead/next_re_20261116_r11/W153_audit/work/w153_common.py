# -*- coding: utf-8 -*-
"""W153 独立复核：通用读取层（我自己实现，不引用既有中间脚本）

口径决定（本文件定义，后续所有脚本共享）：
  - 时间源：t_perf_ns（ns 整数，高分辨率）；t_monotonic 只用于交叉比对（我发现它精度更粗）。
  - 全部按流式逐行 json 解析，不整文件读入。
"""
import json
import os
import glob

ROOT = r"D:\Project\ra2-campaign-forge\lead"
WORK = os.path.dirname(os.path.abspath(__file__))
CARD = os.path.dirname(WORK)
EVID = os.path.join(CARD, "EVIDENCE")

FIELDS = ("seq", "t_perf_ns", "t_monotonic", "frame", "A8ED50", "B0CE88",
          "X87E8E0", "mode", "step", "read_status", "interval_ms_actual",
          "elapsed_ingame_s")


def all_files():
    pat = os.path.join(ROOT, "**", "run.ndjson")
    fs = glob.glob(pat, recursive=True)
    return sorted(fs)


def trip_name(path):
    """out/trip_xxx/run.ndjson -> trip_xxx ; 其它用父目录链尾两段"""
    d = os.path.dirname(path)
    base = os.path.basename(d)
    if base == "out":
        return os.path.basename(os.path.dirname(path))
    return base


def trip_rel(path):
    return os.path.relpath(path, ROOT)


def iter_samples(path, fields=FIELDS, want_kind=None):
    """流式产出 dict（只取需要的字段）。跳过非 sample 行（若指定 want_kind）。"""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                yield {"_parse_error": True}
                continue
            if want_kind is not None and o.get("kind") != want_kind:
                continue
            d = {}
            for k in fields:
                d[k] = o.get(k)
            d["_kind"] = o.get("kind")
            yield d


def load_series(path):
    """读一趟，返回 (rows, meta)。rows 按 t_perf_ns 升序，只留 read_status=='ok' 的采样。"""
    rows = []
    n_total = 0
    n_ok = 0
    n_bad = 0
    n_parse = 0
    kinds = {}
    for s in iter_samples(path):
        if s.get("_parse_error"):
            n_parse += 1
            continue
        n_total += 1
        kinds[s.get("_kind")] = kinds.get(s.get("_kind"), 0) + 1
        if s.get("_kind") != "sample":
            continue
        if s.get("read_status") != "ok":
            n_bad += 1
            continue
        t = s.get("t_perf_ns")
        fr = s.get("frame")
        if t is None or fr is None:
            n_bad += 1
            continue
        s["t"] = t * 1e-9          # 秒（由 ns 换算，双精度足够：1.25e5 s → 分辨率 ~1e-11 s）
        s["t_ms"] = t * 1e-6       # 毫秒
        rows.append(s)
        n_ok += 1
    rows.sort(key=lambda r: (r["t_perf_ns"], r["seq"] or 0))
    meta = dict(path=path, trip=trip_name(path), rel=trip_rel(path),
                n_total=n_total, n_ok=n_ok, n_bad=n_bad, n_parse=n_parse,
                kinds=kinds, n=len(rows))
    if rows:
        meta["t0_s"] = rows[0]["t"]
        meta["t1_s"] = rows[-1]["t"]
        meta["dur_s"] = rows[-1]["t"] - rows[0]["t"]
        meta["frame0"] = rows[0]["frame"]
        meta["frame1"] = rows[-1]["frame"]
    return rows, meta


def median(xs):
    """中位（偶数个取均值）——与 numpy.median 同口径"""
    xs = sorted(x for x in xs if x is not None)
    n = len(xs)
    if n == 0:
        return None
    if n % 2:
        return xs[n // 2]
    return 0.5 * (xs[n // 2 - 1] + xs[n // 2])


def quantile(xs, q):
    """线性插值分位（numpy 默认口径），用于 p10/p90 复算"""
    xs = sorted(x for x in xs if x is not None)
    n = len(xs)
    if n == 0:
        return None
    if n == 1:
        return xs[0]
    pos = (n - 1) * q
    lo = int(pos)
    hi = min(lo + 1, n - 1)
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def pearson(xs, ys):
    pts = [(a, b) for a, b in zip(xs, ys) if a is not None and b is not None]
    n = len(pts)
    if n < 2:
        return None, n
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    syy = sum((p[1] - my) ** 2 for p in pts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    if sxx == 0 or syy == 0:
        return None, n
    return sxy / (sxx ** 0.5 * syy ** 0.5), n


def ols(xs, ys):
    """最小二乘 y = a*x + b，返回 (a, b, rmse, n)"""
    pts = [(a, b) for a, b in zip(xs, ys) if a is not None and b is not None]
    n = len(pts)
    if n < 2:
        return None, None, None, n
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    a = sxy / sxx
    b = my - a * mx
    sse = sum((p[1] - (a * p[0] + b)) ** 2 for p in pts)
    return a, b, (sse / n) ** 0.5, n


def write_evidence(name, text):
    p = os.path.join(EVID, name)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)
    return p
