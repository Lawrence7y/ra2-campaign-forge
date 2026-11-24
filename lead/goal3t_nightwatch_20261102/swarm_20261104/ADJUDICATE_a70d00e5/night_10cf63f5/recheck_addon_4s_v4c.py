# -*- coding: utf-8 -*-
# D15/D13 复核 · 补充核查 A：5 个 4 秒门控窗逐行值（对照候选件 §2.1 表）
#                 补充核查 B：l3_1101v4c 三窗 fps_avg（存储字段）与派生 live_fps（复查 R2）
import json
from pathlib import Path

ROOT = Path(r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")

print("== A: 4s gated windows (span_s==4.0, advanceable by frame_edges) ==")
for p in sorted(ROOT.glob("*/measure_w*.json")):
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    fe = d.get("frame_edges") if isinstance(d.get("frame_edges"), list) else []
    df = fe[-1][0] - fe[0][0] if len(fe) >= 2 else None
    if d.get("span_s") == 4.0 and df is not None and df > 0:
        st = d.get("stats") or {}
        g = d.get("gate") or {}
        print("%s | trip=%s span=%r df=%d avg=%r p50=%r stall=%r gate.ok=%r verdict=%r" % (
            p.as_posix().split("/qc161_u0400_trip/")[-1], d.get("trip_id"), d.get("span_s"),
            df, st.get("fps_avg"), st.get("fps_p50"), st.get("max_stall_s"),
            g.get("ok"), d.get("verdict")))

print("== B: l3_1101v4c w0/w1/w2 fps_avg (stored) vs derived live_fps (frame_edges endpoints) ==")
for w in range(3):
    p = ROOT / "l3_1101v4c" / ("measure_w%d.json" % w)
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    fe = d["frame_edges"]
    live = (fe[-1][0] - fe[0][0]) / (fe[-1][1] - fe[0][1])
    st = d["stats"]
    print("%s | stored fps_avg=%r | derived live_fps=%r | has_stored_live_fps=%s" % (
        p.name, st.get("fps_avg"), live, ("live_fps" in d) or ("live_fps" in st)))
