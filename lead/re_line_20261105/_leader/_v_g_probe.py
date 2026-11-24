# -*- coding: utf-8 -*-
"""领队独立核验 W2 的核心反证：慢组 g 是否显著大于快组。

W2 的 Q2Q3 声称：
  g_items = 256,152,480 只是堆指针（VA 0x008A0394 = MapClass::ObjectsInLayers[2]），
  真正的地面层对象计数是 g（0x008A03A0），且慢组 g(1828~1832) 显著大于快组(1589)。
若成立，则我上一轮「g_items 快组更大 ⇒ g 不是成本源」的推理是错的。

本探针只读 measure_w*.json，零写入业务逻辑。
"""
import glob
import json
import os
import statistics as S

BASE = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
SLOW_TRIPS = {"l3_1101v3a", "l3_1101v3b", "l3_20261031hb", "l1c_20261021",
              "l1d_20261021", "l1e_20261021", "l3_20261021"}
FAST_TRIPS = {"l3_1101v4d", "l3_1101v4e", "t55k_20261020", "l3_20261023q", "l3_20261023r"}


def rows():
    out = []
    for p in sorted(glob.glob(BASE + "/*/measure_w*.json")):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if d.get("schema") != "MEASURE_V1" or (d.get("span_s") or 0) < 20:
            continue
        st = d.get("stats") or {}
        cs = d.get("counters") or []
        if not st.get("frame_ms_p50") or not cs:
            continue
        gs = [c.get("g") for c in cs if isinstance(c.get("g"), int)]
        gi = [c.get("g_items") for c in cs if isinstance(c.get("g_items"), int)]
        out.append(dict(
            trip=os.path.basename(os.path.dirname(p)), win=d.get("window"),
            p50=st["frame_ms_p50"],
            g_mean=round(S.mean(gs), 1) if gs else None,
            g_max=max(gs) if gs else None,
            gi_first=gi[0] if gi else None,
            units0=(d.get("gate") or {}).get("units0"),
        ))
    return out


def main():
    rs = rows()
    print("windows=%d" % len(rs))
    print("\n%-18s %-3s %-7s %-8s %-7s %-12s %s"
          % ("trip", "w", "p50", "g_mean", "g_max", "g_items_first", "group"))
    slow_g, fast_g = [], []
    for r in rs:
        grp = ("SLOW" if r["trip"] in SLOW_TRIPS
               else "FAST" if r["trip"] in FAST_TRIPS else "-")
        print("%-18s %-3s %-7.1f %-8s %-7s %-12s %s"
              % (r["trip"], r["win"], r["p50"], r["g_mean"], r["g_max"],
                 r["gi_first"], grp))
        if r["g_mean"] is not None:
            (slow_g if grp == "SLOW" else fast_g if grp == "FAST" else []).append(r["g_mean"])

    print("\n=== 关键检验：g（地面层对象数）慢组 vs 快组 ===")
    if slow_g:
        print("SLOW n=%d  g_mean: median=%.1f  min=%.1f  max=%.1f"
              % (len(slow_g), S.median(slow_g), min(slow_g), max(slow_g)))
    if fast_g:
        print("FAST n=%d  g_mean: median=%.1f  min=%.1f  max=%.1f"
              % (len(fast_g), S.median(fast_g), min(fast_g), max(fast_g)))
    if slow_g and fast_g:
        sm, fm = S.median(slow_g), S.median(fast_g)
        print("慢组/快组 中位比 = %.3f  ⇒ W2 的『慢组 g 显著更大』%s"
              % (sm / fm, "成立" if sm > fm * 1.10 else "**不成立**"))


if __name__ == "__main__":
    main()
