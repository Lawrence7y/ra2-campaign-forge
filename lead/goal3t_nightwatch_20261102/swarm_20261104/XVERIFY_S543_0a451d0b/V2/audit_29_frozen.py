# -*- coding: utf-8 -*-
import glob
import json
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

all_files = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json")))

frz_records = []
for p in all_files:
    try:
        with open(p, "r", encoding="utf-8") as f:
            j = json.load(f)
    except Exception:
        continue
    ed = j.get("frame_edges") or []
    if not ed:
        continue
    f0, f1 = ed[0][0], ed[-1][0]
    df = f1 - f0
    if df == 0 and f0 != 0:
        trip = os.path.basename(os.path.dirname(p))
        w = j.get("window")
        span_s = j.get("span_s") or 0.0
        stats = j.get("stats") or {}
        gate = j.get("gate") or {}
        cnts = j.get("counters") or []
        frz_records.append({
            "trip": trip,
            "window": w,
            "f0": f0,
            "f1": f1,
            "span_s": span_s,
            "max_stall_s": stats.get("max_stall_s"),
            "logic_frames": stats.get("logic_frames"),
            "pre_fps15": gate.get("pre_fps15"),
            "gate_ok": gate.get("ok"),
            "counters": cnts
        })

print(f"Total frozen windows: {len(frz_records)}")

print(f"{'No.':<4} {'Trip':<20} {'Win':<4} {'f0':<6} {'logic_f':<8} {'pre_fps15':<10} {'gate_ok':<8} {'max_stall':<10} {'span':<6} {'u_set':<6} {'g_set':<6} {'b_set':<6} {'ws_kb_range'}")
for idx, r in enumerate(frz_records, 1):
    cnts = r["counters"]
    u_vals = {c.get("units") for c in cnts if isinstance(c, dict)}
    g_vals = {c.get("g") for c in cnts if isinstance(c, dict)}
    b_vals = {c.get("b") for c in cnts if isinstance(c, dict)}
    ws_vals = [c.get("ws_kb") for c in cnts if isinstance(c, dict) and c.get("ws_kb") is not None]
    ws_str = f"{min(ws_vals)}..{max(ws_vals)}" if ws_vals else "N/A"
    
    pre_str = f"{r['pre_fps15']:.3f}" if r['pre_fps15'] is not None else "None"
    stall_str = f"{r['max_stall_s']:.3f}" if r['max_stall_s'] is not None else "None"
    print(f"{idx:<4} {r['trip']:<20} w{r['window']:<3} {r['f0']:<6} {str(r['logic_frames']):<8} {pre_str:<10} {str(r['gate_ok']):<8} {stall_str:<10} {r['span_s']:<6} {len(u_vals):<6} {len(g_vals):<6} {len(b_vals):<6} {ws_str}")
