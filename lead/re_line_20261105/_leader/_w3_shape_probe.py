# -*- coding: utf-8 -*-
"""W3 预检探针：慢窗帧间隔的形态学（分布形状 / 自相关 / 与单位数的窗内关系）。

只读 measure_w*.json，零写入判定逻辑；输出到 stdout 由调用方重定向。
纪律：python -I -X utf8；不启动游戏；不写采样代码。
"""
import glob
import json
import os
import statistics as S

BASE = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"


def load():
    rows = []
    for p in sorted(glob.glob(BASE + "/*/measure_w*.json")):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if d.get("schema") != "MEASURE_V1":
            continue
        if (d.get("span_s") or 0) < 20:
            continue
        fe = d.get("frame_edges") or []
        st = d.get("stats") or {}
        if len(fe) < 40 or not st.get("frame_ms_p50"):
            continue
        iv = [(fe[i + 1][1] - fe[i][1]) * 1000 for i in range(len(fe) - 1)]
        rows.append(dict(
            trip=os.path.basename(os.path.dirname(p)),
            win=d.get("window"),
            p50=st["frame_ms_p50"],
            iv=iv,
            edges=fe,
            counters=d.get("counters") or [],
            units0=(d.get("gate") or {}).get("units0"),
            map8=(d.get("map_sha256") or "")[:8],
            lf=st.get("logic_frames"),
        ))
    return rows


def acf(x, lag):
    m = S.mean(x)
    v = sum((a - m) ** 2 for a in x)
    if v == 0:
        return 0.0
    return sum((x[i] - m) * (x[i + lag] - m) for i in range(len(x) - lag)) / v


def main():
    rows = load()
    print("windows with >=40 edges: %d" % len(rows))

    print("\n=== A. 慢窗形态学（p50>45ms）：p50 / mean / CV / ACF@1..8 ===")
    print("%-18s %-3s %-7s %-7s %-6s %s" % ("trip", "w", "p50", "mean", "CV", "ACF lag1..8"))
    for r in rows:
        if r["p50"] <= 45:
            continue
        iv = r["iv"]
        m = S.mean(iv)
        cv = S.pstdev(iv) / m if m else 0
        a = [round(acf(iv, k), 3) for k in range(1, 9)]
        print("%-18s %-3s %-7.1f %-7.1f %-6.2f %s" % (r["trip"], r["win"], r["p50"], m, cv, a))

    print("\n=== B. 快窗对照（p50<35ms）的 ACF，确认基线本身无周期 ===")
    print("%-18s %-3s %-7s %-6s %s" % ("trip", "w", "p50", "CV", "ACF lag1..8"))
    for r in rows:
        if r["p50"] >= 35:
            continue
        iv = r["iv"]
        m = S.mean(iv)
        cv = S.pstdev(iv) / m if m else 0
        a = [round(acf(iv, k), 3) for k in range(1, 9)]
        print("%-18s %-3s %-7.1f %-6.2f %s" % (r["trip"], r["win"], r["p50"], cv, a))

    print("\n=== C. 窗内：每秒帧时 vs 单位数（1Hz counters），找「单位数下降是否同步帧时下降」 ===")
    for r in rows:
        if r["p50"] <= 45 and r["p50"] >= 35:
            continue
        if not r["counters"]:
            continue
        t0 = r["edges"][0][1]
        per = {}
        for i in range(len(r["edges"]) - 1):
            sec = int(r["edges"][i][1] - t0)
            per.setdefault(sec, []).append(r["iv"][i])
        secs = sorted(per)
        sec_ms = [(s, S.median(per[s]), len(per[s])) for s in secs if len(per[s]) >= 3]
        if len(sec_ms) < 8:
            continue
        units = [(c.get("t_rel"), c.get("units")) for c in r["counters"] if c.get("units") is not None]
        head = sec_ms[:3]
        tail = sec_ms[-3:]
        print("%-18s w%-2s p50=%6.1f | 首3秒med=%s | 末3秒med=%s | units %s->%s"
              % (r["trip"], r["win"], r["p50"],
                 [round(x[1], 1) for x in head], [round(x[1], 1) for x in tail],
                 units[0][1] if units else "?", units[-1][1] if units else "?"))


if __name__ == "__main__":
    main()
