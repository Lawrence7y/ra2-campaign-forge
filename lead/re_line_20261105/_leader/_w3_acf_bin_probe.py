# -*- coding: utf-8 -*-
"""W3 预检探针 3：用**固定时间分箱**重算时间尺度自相关，修掉探针 2 的小样本 ACF>1 伪值。

探针 2 的缺陷（自查）：它在 tau 邻域内取点对求平均，再除以 (点对数 × 总体方差)，
当邻域内点对很少且恰好同号时，结果可 >1 —— 这不是自相关，是估计器伪值。
本探针改为标准做法：
  1) 把 [0, span) 切成 BIN_MS 的等宽箱；
  2) 每箱取该箱内推进帧的**中位帧时**（不足 2 帧的箱丢弃）；
  3) 对这条等间隔序列做标准 ACF（滞后 k 箱）；
  4) 报 lag1..8（= 50..400ms，BIN_MS=50）与 lag20/40（= 1s/2s）。
箱宽固定 ⇒ 不同帧率的窗**在同一时间尺度上可比**。
零写入只读。
"""
import glob
import json
import os
import statistics as S

BASE = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
BIN_MS = 50.0
LAGS = [1, 2, 3, 4, 6, 8, 20, 40]


def load():
    rows = []
    for p in sorted(glob.glob(BASE + "/*/measure_w*.json")):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if d.get("schema") != "MEASURE_V1" or (d.get("span_s") or 0) < 20:
            continue
        fe = d.get("frame_edges") or []
        st = d.get("stats") or {}
        if len(fe) < 40 or not st.get("frame_ms_p50"):
            continue
        rows.append(dict(trip=os.path.basename(os.path.dirname(p)), win=d.get("window"),
                         p50=st["frame_ms_p50"], fe=fe,
                         map8=(d.get("map_sha256") or "")[:8],
                         units0=(d.get("gate") or {}).get("units0")))
    return rows


def binned(fe):
    t0 = fe[0][1]
    bins = {}
    for i in range(len(fe) - 1):
        dt = (fe[i + 1][1] - fe[i][1]) * 1000.0
        b = int((fe[i][1] - t0) * 1000.0 / BIN_MS)
        bins.setdefault(b, []).append(dt)
    keys = sorted(bins)
    if not keys:
        return []
    series = []
    for b in range(keys[0], keys[-1] + 1):
        vals = bins.get(b)
        if vals and len(vals) >= 2:
            series.append(S.median(vals))
    return series


def acf_series(x, lag):
    n = len(x)
    if n - lag < 10:
        return None
    m = S.mean(x)
    var = sum((a - m) ** 2 for a in x)
    if var <= 0:
        return None
    num = sum((x[i] - m) * (x[i + lag] - m) for i in range(n - lag))
    # 有限样本归一：用各自子集长度校正，避免两端截断造成的偏置
    return (num / (n - lag)) / (var / n)


def main():
    rows = load()
    print("bin=%.0fms  windows=%d" % (BIN_MS, len(rows)))
    print("\n=== 分箱时间尺度 ACF ===")
    hdr = "  ".join("lag%-3d" % k for k in LAGS)
    print("%-18s %-3s %-7s %-5s %s" % ("trip", "w", "p50", "nbins", hdr))
    rec = {}
    for r in rows:
        ser = binned(r["fe"])
        vals = [acf_series(ser, k) for k in LAGS]
        rec[(r["trip"], r["win"])] = (r["p50"], len(ser), vals)
        print("%-18s %-3s %-7.1f %-5d %s" % (
            r["trip"], r["win"], r["p50"], len(ser),
            "  ".join("  --  " if v is None else "%6.3f" % v for v in vals)))

    print("\n=== 按 p50 档汇总（中位）===")
    groups = {"快 <35": [], "中 35-70": [], "慢 70-120": [], "极慢 >120": []}
    for r in rows:
        k = ("快 <35" if r["p50"] < 35 else "中 35-70" if r["p50"] < 70
             else "慢 70-120" if r["p50"] < 120 else "极慢 >120")
        groups[k].append(rec[(r["trip"], r["win"])])
    for k, vs in groups.items():
        if not vs:
            continue
        print("\n%s (n=%d)" % (k, len(vs)))
        for i, lag in enumerate(LAGS):
            col = [v[2][i] for v in vs if v[2][i] is not None]
            if col:
                print("  lag%-3d (%4dms)  median=%6.3f  min=%6.3f  max=%6.3f  n=%d"
                      % (lag, int(lag * BIN_MS), S.median(col), min(col), max(col), len(col)))


if __name__ == "__main__":
    main()
