# -*- coding: utf-8 -*-
"""A2 规模量化：全 87 个 25 s 窗里，有多少被 harness 的
「logic_frames<=0 ⇒ 整窗弃统」误杀（实际有可用 df=1 沿）？

只读既有 JSON。零真机。
"""
import glob
import io
import json

GLOB = r'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/*/measure_w*.json'

files = sorted(glob.glob(GLOB))
print("files:", len(files))

rows = []
for p in files:
    d = json.load(io.open(p, encoding="utf-8"))
    st = d.get("stats") or {}
    if d.get("span_s") != 25.0 or (st.get("samples") or 0) == 0:
        continue
    fe = d.get("frame_edges") or []
    ms = []
    gaps = 0
    for (fa, ta), (fb, tb) in zip(fe, fe[1:]):
        df = fb - fa
        if df == 1:
            ms.append((tb - ta) * 1000.0)
        elif df > 1:
            gaps += 1
    rows.append({
        "trip": d.get("trip_id"),
        "w": d.get("window"),
        "logic": st.get("logic_frames"),
        "p50": st.get("frame_ms_p50"),
        "note": st.get("note"),
        "n_edges": st.get("n_edges"),
        "n_multi": st.get("n_multi_advance"),
        "usable_df1": len(ms),
        "ms": ms,
    })

print("25s windows:", len(rows))

null_p50 = [r for r in rows if r["p50"] is None]
print("\n=== harness 报 p50=None 的窗 ===")
print("  数量 = %d / %d" % (len(null_p50), len(rows)))

rescued = [r for r in null_p50 if r["usable_df1"] >= 10]
print("\n=== ★ 其中「实际有 ≥10 个可用 df=1 沿」的（= 被误杀）===")
print("  数量 = %d" % len(rescued))
tot_extra = sum(r["usable_df1"] for r in rescued)
print("  这些窗合计可救回帧时样本 = %d" % tot_extra)

for r in sorted(rescued, key=lambda x: -x["usable_df1"]):
    ms = sorted(r["ms"])

    def pct(v, q):
        k = (len(v) - 1) * q
        lo = int(k)
        hi = min(lo + 1, len(v) - 1)
        return v[lo] + (v[hi] - v[lo]) * (k - lo)

    print("    %-32s w%s logic=%-7s edges=%-4s usable=%-4d p50=%.2fms p90=%.2fms"
          % (str(r["trip"])[:32], r["w"], r["logic"], r["n_edges"],
             r["usable_df1"], pct(ms, .5), pct(ms, .9)))

print("\n=== 对照：p50=None 且确实无可用沿的（真·帧不推进）===")
truly = [r for r in null_p50 if r["usable_df1"] < 10]
print("  数量 = %d" % len(truly))
for r in truly[:12]:
    print("    %-32s w%s logic=%-8s edges=%-4s usable=%d"
          % (str(r["trip"])[:32], r["w"], r["logic"], r["n_edges"], r["usable_df1"]))

# 有 p50 的窗里，是否也有 frame_edges 丢失（df>1）
print("\n=== 有 p50 的窗里 df>1 情况 ===")
has_p50 = [r for r in rows if r["p50"] is not None]
m = [r for r in has_p50 if (r["n_multi"] or 0) > 0]
print("  有 p50 的窗 = %d，其中含 df>1 = %d" % (len(has_p50), len(m)))
for r in m:
    print("    %-32s w%s p50=%.2f n_multi=%s"
          % (str(r["trip"])[:32], r["w"], r["p50"], r["n_multi"]))

print("\nDONE")
