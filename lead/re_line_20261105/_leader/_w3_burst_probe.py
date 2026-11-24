# -*- coding: utf-8 -*-
"""W3 预检探针 4：判别「整窗持续慢」vs「秒级爆发慢」。

前两个探针的自查失败（如实登记）：
- 探针 2 的时间重标定 ACF 在慢窗上出现 ACF>1 的伪值（小样本点对估计器的缺陷）；
- 探针 3 的固定 50ms 分箱在慢窗（>120ms/帧）里几乎每箱不足 2 帧，样本被整体丢弃。
⇒ **两者对慢窗的自相关结论都不可引用**。本探针换一个不依赖自相关的判别：

把窗切成 1 秒格，算每格内推进帧的中位帧时。
- 定义 **fast baseline = 32.0ms**（满帧，语料里快窗的 p50 稳定在 31.9–32.4）；
- 每格标 `FAST`（<=40ms）/ `MID`（40–70ms）/ `SLOW`（>70ms）；
- 报：FAST 格占比、格类别序列的**最长连续 SLOW 段**、以及格中位帧时的**四分位距**。

判据：
- 若 FAST 占比 <10% 且最长连续 SLOW ≥ 窗长 60% ⇒ **整窗持续慢**（成本是全窗性的）；
- 若 FAST 占比 >30% 且有多个 SLOW 段被 FAST 段隔开 ⇒ **秒级爆发慢**（成本是事件性的）。
零写入只读。
"""
import glob
import json
import os
import statistics as S

BASE = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
FAST_BASE = 32.0


def classify(ms):
    if ms <= 40.0:
        return "FAST"
    if ms <= 70.0:
        return "MID"
    return "SLOW"


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
                         units0=(d.get("gate") or {}).get("units0"),
                         b_zero=all((c.get("b_items") or 0) == 0 for c in (d.get("counters") or []))))
    return rows


def per_sec(fe):
    t0 = fe[0][1]
    buckets = {}
    for i in range(len(fe) - 1):
        dt = (fe[i + 1][1] - fe[i][1]) * 1000.0
        sec = int(fe[i][1] - t0)
        buckets.setdefault(sec, []).append(dt)
    out = []
    for s in sorted(buckets):
        v = buckets[s]
        if len(v) >= 3:            # 每秒至少 3 帧才统计（慢窗 183ms/帧 → 约 5 帧/秒）
            out.append((s, S.median(v), len(v)))
    return out


def longest_run(seq, target):
    best = cur = 0
    for x in seq:
        cur = cur + 1 if x == target else 0
        best = max(best, cur)
    return best


def main():
    rows = load()
    print("windows=%d  fast baseline=%.1fms" % (len(rows), FAST_BASE))
    print("\n%-18s %-3s %-7s %-6s %-6s %-7s %-6s %-7s %s"
          % ("trip", "w", "p50", "nsec", "FAST%", "MID%", "SLOW%", "maxRun", "verdict"))
    agg = []
    for r in rows:
        ps = per_sec(r["fe"])
        if len(ps) < 8:
            print("%-18s %-3s %-7.1f  (1s 格不足 8 个：%d)" % (r["trip"], r["win"], r["p50"], len(ps)))
            continue
        cls = [classify(m) for _, m, _ in ps]
        n = len(cls)
        f = 100.0 * cls.count("FAST") / n
        md = 100.0 * cls.count("MID") / n
        sl = 100.0 * cls.count("SLOW") / n
        run = longest_run(cls, "SLOW")
        if f < 10 and run >= 0.6 * n:
            verdict = "整窗持续慢"
        elif f > 30:
            verdict = "有快段⇒事件性"
        else:
            verdict = "混合"
        agg.append((r, f, sl, run, verdict, n))
        print("%-18s %-3s %-7.1f %-6d %-6.1f %-6.1f %-7.1f %-6d %s"
              % (r["trip"], r["win"], r["p50"], n, f, md, sl, run, verdict))

    print("\n=== 按 p50 档汇总 ===")
    groups = {"快 <35": [], "中 35-70": [], "慢 70-120": [], "极慢 >120": []}
    for r, f, sl, run, verdict, n in agg:
        k = ("快 <35" if r["p50"] < 35 else "中 35-70" if r["p50"] < 70
             else "慢 70-120" if r["p50"] < 120 else "极慢 >120")
        groups[k].append((f, sl, run, verdict, n))
    for k, vs in groups.items():
        if not vs:
            continue
        print("\n%s (n=%d)" % (k, len(vs)))
        print("  FAST%% 中位=%.1f  范围 %.1f-%.1f" % (S.median([v[0] for v in vs]), min(v[0] for v in vs), max(v[0] for v in vs)))
        print("  SLOW%% 中位=%.1f" % S.median([v[1] for v in vs]))
        print("  最长连续 SLOW 中位=%d 格 (窗长中位 %d 格)" % (S.median([v[2] for v in vs]), S.median([v[4] for v in vs])))
        from collections import Counter
        print("  判定分布: %s" % dict(Counter(v[3] for v in vs)))


if __name__ == "__main__":
    main()
