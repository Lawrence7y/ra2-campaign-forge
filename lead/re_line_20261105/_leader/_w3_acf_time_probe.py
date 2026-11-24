# -*- coding: utf-8 -*-
"""W3 预检探针 2：把帧间隔自相关**按墙钟时间重标定**，消除帧率不同导致的 ACF 不可比。

动机（本节纪律，引自台账 §549）：ACF 是"每帧"口径；快窗 32ms/帧、慢窗 183ms/帧，
同一个 1 秒尺度的底层过程，在两种帧率下 lag-1 的 ACF 必然不同 ⇒ **跨窗比 ACF 必须先换到时间轴**。

做法：给定时间滞后 tau（毫秒），取 |t_j - t_i - tau| 最小的一对点计乘积，
用全部点对做加权平均（最大滞后 2000ms）。零写入只读。
"""
import glob
import json
import os
import statistics as S

BASE = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
TAUS = [50, 100, 200, 400, 800, 1600]


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
        # 以每个推进帧的**时刻**为样本点，值为"该帧耗时"（到下一帧的间隔）
        t = [x[1] for x in fe[:-1]]
        v = [(fe[i + 1][1] - fe[i][1]) * 1000 for i in range(len(fe) - 1)]
        rows.append(dict(trip=os.path.basename(os.path.dirname(p)), win=d.get("window"),
                         p50=st["frame_ms_p50"], t=t, v=v,
                         map8=(d.get("map_sha256") or "")[:8],
                         units0=(d.get("gate") or {}).get("units0"),
                         tick_miss=st.get("tick_miss")))
    return rows


def acf_time(t, v, tau_ms):
    """时间重标定 ACF：只取 |dt - tau| <= tol 的点对，tol = 半个 tau 或 40ms 取大。"""
    n = len(v)
    m = S.mean(v)
    var = sum((x - m) ** 2 for x in v) / n
    if var <= 0:
        return None
    tol = max(tau_ms * 0.25, 40.0)
    num = 0.0
    cnt = 0
    for i in range(n):
        for j in range(i + 1, n):
            dt = (t[j] - t[i]) * 1000.0
            if dt > tau_ms + tol:
                break
            if abs(dt - tau_ms) <= tol:
                num += (v[i] - m) * (v[j] - m)
                cnt += 1
    if cnt == 0:
        return None
    return num / cnt / var


def main():
    rows = load()
    print("windows: %d" % len(rows))
    print("\n=== 时间重标定 ACF（tau=50/100/200/400/800/1600 ms）===")
    print("%-18s %-3s %-7s %-7s %s" % ("trip", "w", "p50", "tickM", "  ".join("t=%dms" % x for x in TAUS)))
    out = {}
    for r in rows:
        vals = [acf_time(r["t"], r["v"], tau) for tau in TAUS]
        out[(r["trip"], r["win"])] = (r["p50"], vals)
        print("%-18s %-3s %-7.1f %-7s %s" % (
            r["trip"], r["win"], r["p50"], r["tick_miss"],
            "  ".join("   --  " if x is None else "%7.3f" % x for x in vals)))

    print("\n=== 分组汇总（按 p50 档）===")
    groups = {"快 <35ms": [], "中 35-70ms": [], "慢 70-120ms": [], "极慢 >120ms": []}
    for r in rows:
        key = ("快 <35ms" if r["p50"] < 35 else
               "中 35-70ms" if r["p50"] < 70 else
               "慢 70-120ms" if r["p50"] < 120 else "极慢 >120ms")
        groups[key].append(out[(r["trip"], r["win"])])
    for k, vs in groups.items():
        if not vs:
            continue
        print("\n%s  (n=%d)" % (k, len(vs)))
        for i, tau in enumerate(TAUS):
            col = [v[1][i] for v in vs if v[1][i] is not None]
            if col:
                print("  tau=%4dms  median=%7.3f  min=%7.3f  max=%7.3f  (n=%d)"
                      % (tau, S.median(col), min(col), max(col), len(col)))


if __name__ == "__main__":
    main()
