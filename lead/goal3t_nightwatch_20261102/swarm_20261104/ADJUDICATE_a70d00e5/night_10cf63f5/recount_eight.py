# -*- coding: utf-8 -*-
# D15/D13 复核 · 独立复算八字数（判据写死于本脚本，不引用任何候选件的分类代码）
# 只读原始 JSON；判据：
#   可推进: len(frame_edges)>=2 且 (末沿帧号 - 首沿帧号) > 0
#   25秒窗: span_s == 25.0 ; 4秒门控窗: span_s == 4.0
#   对照: 25s 且 stats.fps_avg >= 28
#   持续低速: 25s 且 stats.fps_avg < 28 且 stats.fps_p50 < 28
#   停摆主导: 25s 且 stats.fps_avg < 28 且 stats.fps_p50 >= 28
#   不可算: frame_edges 为空或不满足可推进
import json
from pathlib import Path

ROOT = Path(r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")

root_files = sorted(ROOT.glob("measure_w*.json"))
child_files = sorted(ROOT.glob("*/measure_w*.json"))
deeper_files = sorted(ROOT.glob("*/*/measure_w*.json"))


def rec(p, layer):
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    fe = d.get("frame_edges")
    fe = fe if isinstance(fe, list) else []
    df_edges = None
    if len(fe) >= 2:
        try:
            df_edges = fe[-1][0] - fe[0][0]  # 末沿帧号 - 首沿帧号
        except Exception:
            df_edges = None
    sm = d.get("samples") if isinstance(d.get("samples"), dict) else {}
    tf, ff = sm.get("t") or [], sm.get("f") or []
    df_samples = (ff[-1] - ff[0]) if len(ff) >= 2 and len(tf) == len(ff) else None
    st = d.get("stats") if isinstance(d.get("stats"), dict) else {}
    return {
        "path": p.as_posix(), "layer": layer,
        "trip": d.get("trip_id"), "span": d.get("span_s"),
        "n_edges": len(fe), "df_edges": df_edges, "df_samples": df_samples,
        "avg": st.get("fps_avg"), "p50": st.get("fps_p50"), "stall": st.get("max_stall_s"),
    }


recs, errs = [], []
for layer, files in (("root", root_files), ("child", child_files), ("deeper", deeper_files)):
    for p in files:
        try:
            recs.append(rec(p, layer))
        except Exception as ex:
            errs.append((p.as_posix(), repr(ex)))

adv = [r for r in recs if r["df_edges"] is not None and r["df_edges"] > 0]
noncalc = [r for r in recs if r not in adv]
w25 = [r for r in adv if r["span"] == 25.0]
w4 = [r for r in adv if r["span"] == 4.0]
wother = [r for r in adv if r["span"] != 25.0 and r["span"] != 4.0]
control = [r for r in w25 if r["avg"] is not None and r["avg"] >= 28.0]
steady = [r for r in w25 if r["avg"] is not None and r["avg"] < 28.0
          and r["p50"] is not None and r["p50"] < 28.0]
stalled = [r for r in w25 if r["avg"] is not None and r["avg"] < 28.0
           and r["p50"] is not None and r["p50"] >= 28.0]
uncls = [r for r in w25 if r not in control and r not in steady and r not in stalled]

adv_by_samples = [r for r in recs if r["df_samples"] is not None and r["df_samples"] > 0]
disagree = [r for r in recs if (r["df_edges"] is None) != (r["df_samples"] is None)
            or (r["df_edges"] is not None and r["df_samples"] is not None
                and (r["df_edges"] > 0) != (r["df_samples"] > 0))]

spans = sorted({repr(r["span"]) for r in recs})
st_trips = sorted({r["trip"] for r in steady})
sp_trips = sorted({r["trip"] for r in stalled})
ov = sorted(set(st_trips) & set(sp_trips))
stalls = [r["stall"] for r in steady if r["stall"] is not None]

all_lt28 = [r for r in recs if r["avg"] is not None and r["avg"] < 28.0]
s25_lt28 = [r for r in w25 if r["avg"] is not None and r["avg"] < 28.0]
s4_lt28 = [r for r in w4 if r["avg"] is not None and r["avg"] < 28.0]
both_lt28 = [r for r in s25_lt28 if r["p50"] is not None and r["p50"] < 28.0]
avg_null_adv = [r for r in adv if r["avg"] is None]
p50_null_adv = [r for r in adv if r["p50"] is None]

print("LAYERS root=%d child=%d deeper=%d parse_errors=%d" % (
    len(root_files), len(child_files), len(deeper_files), len(errs)))
for e in errs:
    print("  ERR", e)
print("DISTINCT span_s values:", spans)
print("[1] total_json          = %d" % len(recs))
print("[2] advanceable         = %d" % len(adv))
print("[3] positive_25s        = %d" % len(w25))
print("[4] control avg>=28     = %d" % len(control))
print("[5] steady  both<28     = %d" % len(steady))
print("[6] stalled avg<28,p50>=28 = %d" % len(stalled))
print("[7] positive_4s         = %d" % len(w4))
print("[8] noncalculable       = %d" % len(noncalc))
print("control+steady+stalled = %d ; unclassified_25s=%d ; other_span_adv=%d" % (
    len(control) + len(steady) + len(stalled), len(uncls), len(wother)))
for r in uncls:
    print("  UNCLASSIFIED", r["path"], r["span"], r["avg"], r["p50"])
for r in wother:
    print("  OTHER-SPAN", r["path"], r["span"])
print("steady_trip_ids = %d -> %s" % (len(st_trips), st_trips))
print("stopped_trip_ids = %d ; overlap_with_steady = %d" % (len(sp_trips), len(ov)))
print("steady max_stall min=%r max=%r n_ge_1s=%d" % (
    min(stalls) if stalls else None, max(stalls) if stalls else None,
    sum(1 for v in stalls if v >= 1.0)))
print("cross: all_avg_lt28=%d  span25_avg_lt28=%d  span4_avg_lt28=%d  span25_both_lt28=%d" % (
    len(all_lt28), len(s25_lt28), len(s4_lt28), len(both_lt28)))
print("cross: 33==steady+stalled -> %s ; 38==span25lt28+span4lt28 -> %s" % (
    len(s25_lt28) == len(steady) + len(stalled),
    len(all_lt28) == len(s25_lt28) + len(s4_lt28)))
print("cross: advanceable by frame_edges=%d by samples.f=%d disagree=%d" % (
    len(adv), len(adv_by_samples), len(disagree)))
for r in disagree:
    print("  DISAGREE", r["path"], r["df_edges"], r["df_samples"])
print("cross: advanceable-but-avg-null=%d p50-null=%d" % (len(avg_null_adv), len(p50_null_adv)))
print("== steady windows (my own list) ==")
for i, r in enumerate(steady, 1):
    print("%2d %s | %s | span=%r avg=%r p50=%r stall=%r" % (
        i, r["path"].split("/qc161_u0400_trip/")[-1], r["trip"], r["span"], r["avg"], r["p50"], r["stall"]))
print("== control windows (my own list) ==")
for i, r in enumerate(control, 1):
    print("%2d %s | %s | avg=%r p50=%r stall=%r" % (
        i, r["path"].split("/qc161_u0400_trip/")[-1], r["trip"], r["avg"], r["p50"], r["stall"]))
print("== stalled windows (my own list) ==")
for i, r in enumerate(stalled, 1):
    print("%2d %s | %s | avg=%r p50=%r stall=%r" % (
        i, r["path"].split("/qc161_u0400_trip/")[-1], r["trip"], r["avg"], r["p50"], r["stall"]))
