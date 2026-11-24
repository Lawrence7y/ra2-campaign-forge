# -*- coding: utf-8 -*-
"""§542 Leader 亲算: 冻结起点 vs working-set 跳变（新通道，此前未单独统计）。

只读 measure_w*.json。零真机、零写入母本。
判据:
  freeze_t  = 该窗最后一个帧沿相对窗首的秒数（df>0 时才有意义）
  jump      = counters 中相邻 1s 采样 ws_kb/pf_kb 的最大正增量，及其首次出现时刻
  滞后区间  = (prev_sample_t - freeze_t, jump_t - freeze_t]
"""
import glob
import json
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

rows = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json"))):
    try:
        j = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    ed = j.get("frame_edges") or []
    cs = j.get("counters") or []
    if not ed or len(cs) < 3:
        continue
    trip = os.path.basename(os.path.dirname(p))
    w = j.get("window")
    f0, f1 = ed[0][0], ed[-1][0]
    df = f1 - f0
    span = j.get("span_s") or 0.0
    freeze = (ed[-1][1] - ed[0][1]) if df else None
    ser = [(c["t_rel"], c["ws_kb"] or 0, c["pf_kb"] or 0) for c in cs]
    best = (0, None, None, 0, 0)  # dWS, t_of_new_sample, t_of_prev_sample, dPF, ws_at
    for a, b in zip(ser, ser[1:]):
        d = b[1] - a[1]
        if d > best[0]:
            best = (d, b[0], a[0], b[2] - a[2], b[1])
    rows.append(dict(trip=trip, w=w, f0=f0, f1=f1, df=df, span=span, freeze=freeze,
                     dws=best[0], t_new=best[1], t_prev=best[2], dpf=best[3], ws_at=best[4],
                     ws0=ser[0][1]))

print("=== A. 有推进窗：冻结起点 vs 最大 ws 跳变 ===")
print("%-18s %2s %6s %7s %7s %7s %8s %8s %14s" % (
    "trip", "w", "df", "freeze", "jump@", "lag", "dWS_kb", "dPF_kb", "lag区间"))
hits = []
for r in rows:
    if r["df"] == 0 or r["dws"] < 500:
        continue
    lo = r["t_prev"] - r["freeze"]
    hi = r["t_new"] - r["freeze"]
    print("%-18s %2d %6d %7.2f %7.2f %+7.2f %8d %8d   (%+.2f, %+.2f]" % (
        r["trip"], r["w"], r["df"], r["freeze"], r["t_new"], r["t_new"] - r["freeze"],
        r["dws"], r["dpf"], lo, hi))
    hits.append((r, lo, hi))

print()
print("=== B. 冻结窗（df==0 但 f0!=0）与同趟跳变的归属 ===")
frozen = [r for r in rows if r["df"] == 0 and r["f0"] != 0]
trips_with_frozen = {r["trip"] for r in frozen}
print("冻结窗 %d 个，分布在 %d 趟" % (len(frozen), len(trips_with_frozen)))
for t in sorted(trips_with_frozen):
    ws = [r for r in rows if r["trip"] == t]
    big = [r for r in ws if r["dws"] >= 500]
    print("  %-18s 窗数=%d 大跳变出现在窗 %s" % (
        t, len(ws), [(r["w"], r["dws"], r["t_new"]) for r in big]))

print()
print("=== C. 全部「有推进」窗中 dWS 分布（看 2.3MB 量级是否只属冻结趟）===")
adv = [r for r in rows if r["df"] > 0]
adv.sort(key=lambda r: -r["dws"])
print("%-18s %2s %6s %7s %8s %8s %s" % ("trip", "w", "df", "freeze", "dWS_kb", "jump@", "后续是否冻结"))
for r in adv[:20]:
    nxt = [x for x in rows if x["trip"] == r["trip"] and x["w"] is not None and r["w"] is not None
           and x["w"] > r["w"] and x["df"] == 0 and x["f0"] != 0]
    print("%-18s %2d %6d %7.2f %8d %7.2f  %s" % (
        r["trip"], r["w"], r["df"], r["freeze"], r["dws"], r["t_new"],
        "YES(w%s)" % ",".join(str(x["w"]) for x in nxt) if nxt else "-"))

print()
print("=== D. 量级统计：dWS>=1500 的窗，按「同趟后续是否冻结」分组 ===")
hi_big = [r for r in rows if r["dws"] >= 1500]
print("dWS>=1500 的窗共 %d 个" % len(hi_big))
for r in hi_big:
    nxt = [x for x in rows if x["trip"] == r["trip"] and r["w"] is not None and x["w"] is not None
           and x["w"] > r["w"] and x["df"] == 0 and x["f0"] != 0]
    print("   %-18s w%s df=%-5d dWS=%-5d @%.2f  后续冻结=%s" % (
        r["trip"], r["w"], r["df"], r["dws"], r["t_new"], "YES" if nxt else "no"))
