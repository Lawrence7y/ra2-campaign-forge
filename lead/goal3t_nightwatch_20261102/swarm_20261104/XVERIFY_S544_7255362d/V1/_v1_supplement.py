# -*- coding: utf-8 -*-
"""V1 补充：活段长度 / p50 样本量 / 尾停后是否永不再推进（跨窗核对）/ 计数器在停摆段是否变化。"""
import glob
import json
import os

TRIP = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
files = sorted(glob.glob(os.path.join(TRIP, "*", "measure_w*.json")))
files += sorted(glob.glob(os.path.join(TRIP, "measure_w*.json")))

TH = 28.0
print("=== [A] 被 §544 判「假慢」的窗：活段到底多长、p50 有几个样本 ===")
print("%-26s %7s %7s %8s %8s %7s %6s %6s %6s" %
      ("name", "fps_avg", "live", "p50", "live_s", "tail_s", "n_gap", "logic", "adv%"))
rows = []
for p in files:
    rel = os.path.relpath(p, TRIP).replace("\\", "/")
    d = json.load(open(p, encoding="utf-8"))
    st = d["stats"]
    s = d["samples"]
    t, f = s["t"], s["f"]
    ej = d.get("frame_edges") or []
    if not ej:
        continue
    e0, e1 = ej[0], ej[-1]
    live_s = e1[1] - e0[1]
    ngap = sum(1 for (fa, ta), (fb, tb) in zip(ej, ej[1:]) if fb - fa == 1)
    span = t[-1] - t[0]
    fa_ = st.get("fps_avg")
    fp_ = st.get("fps_p50")
    rows.append((rel, fa_, fp_, live_s, t[-1] - e1[1], ngap, st.get("logic_frames"), span, d))
    if fa_ is not None and fa_ < TH and (fp_ or 0) >= TH:
        lv = (e1[0] - e0[0]) / live_s if live_s > 0 else float("nan")
        print("%-26s %7.2f %7.2f %8.2f %8.3f %7.2f %6d %6d %5.1f%%" %
              (rel, fa_, lv, fp_,
               live_s, t[-1] - e1[1], ngap, st.get("logic_frames"), 100 * live_s / span))

print("\n  活段 < 1s 的（上表内）: %d" % sum(
    1 for rel, fa_, fp_, live_s, tail, ngap, lg, span, d in rows
    if fa_ is not None and fa_ < TH and (fp_ or 0) >= TH and live_s < 1.0))
print("  活段 < 5s 的（上表内）: %d" % sum(
    1 for rel, fa_, fp_, live_s, tail, ngap, lg, span, d in rows
    if fa_ is not None and fa_ < TH and (fp_ or 0) >= TH and live_s < 5.0))

print("\n=== [B] 全库：喂给 frame_ms_p50 的 df==1 沿间隔个数（样本量） ===")
small = [(rel, ngap, fa_, fp_) for rel, fa_, fp_, live_s, tail, ngap, lg, span, d in rows
         if fa_ is not None]
small.sort(key=lambda x: x[1])
print("  n_gap<20 的窗: %d ; n_gap<50: %d ; 有推进窗总数: %d" % (
    sum(1 for x in small if x[1] < 20), sum(1 for x in small if x[1] < 50), len(small)))
for x in small[:16]:
    print("    %-26s n_gap=%4d fps_avg=%7.2f fps_p50=%7.2f" % x)

print("\n=== [C] 尾停摆窗：同趟后续窗是否也不推进（帧号是否续上） ===")
import collections
bytrip = collections.defaultdict(dict)
for p in files:
    rel = os.path.relpath(p, TRIP).replace("\\", "/")
    d = json.load(open(p, encoding="utf-8"))
    ej = d.get("frame_edges") or []
    f = (d["samples"]["f"] or [])
    bytrip[d.get("trip_id")][d.get("window")] = dict(
        name=rel, edges=len(ej), f0=(int(ej[0][0]) if ej else None),
        f1=(int(ej[-1][0]) if ej else None), logic=d["stats"].get("logic_frames"),
        fps_avg=d["stats"].get("fps_avg"), span=d["span_s"],
        last_t=(d["samples"]["t"][-1] - d["samples"]["t"][0]) if f else None,
        verdict=d.get("verdict"))
for trip, ws in sorted(bytrip.items()):
    tot_logic = None
    line = []
    for k in sorted(ws):
        w = ws[k]
        line.append("w%s:%s->%s(%s e,%s)" % (k, w["f0"], w["f1"], w["edges"], w["fps_avg"] if w["fps_avg"] is None else round(w["fps_avg"], 2)))
    taildom = any(w["logic"] not in (0, None) and (w["fps_avg"] or 1e9) < 28 for w in ws.values())
    if taildom:
        print("  %-32s %s" % (trip, " | ".join(line)))

print("\n=== [D] 停摆段内计数器是否变化（units 序列）——取 3 个代表窗 ===")
for relWant in ["archive_T34/measure_w0.json", "archive_T32/measure_w0.json", "l3_20261023q/measure_w2.json"]:
    p = os.path.join(TRIP, *relWant.split("/"))
    d = json.load(open(p, encoding="utf-8"))
    ej = d["frame_edges"]
    t = d["samples"]["t"]
    stop_t = ej[-1][1] - t[0]
    print("  %s  帧沿停在 t_rel=%.3fs；counters 序列（t_rel:units/infantry/g/b）:" % (relWant, stop_t))
    seq = [(c["t_rel"], c.get("units"), c.get("infantry"), c.get("g"), c.get("b")) for c in d["counters"]]
    print("    " + " ".join("%.0f:%s/%s/%s/%s" % x for x in seq))
    print("    units 值集合: %s ; g 值变化次数: %d" % (
        sorted(set(x[1] for x in seq)), sum(1 for a, b in zip(seq, seq[1:]) if a[3] != b[3])))
