# -*- coding: utf-8 -*-
"""Collect all 103 measure files and associated metadata."""
import datetime
import glob
import json
import os

TRIP_BASE = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

sub_files = sorted(glob.glob(TRIP_BASE + "/*/measure_w*.json"))
root_files = sorted(glob.glob(TRIP_BASE + "/measure_w*.json"))
all_files = sub_files + root_files

records = []

for p in all_files:
    rel_path = os.path.relpath(p, TRIP_BASE).replace("\\", "/")
    parent_dir = os.path.dirname(p)
    trip_dir_name = os.path.basename(parent_dir) if parent_dir != TRIP_BASE else "."
    
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    
    trip_id = d.get("trip_id") or trip_dir_name
    window = d.get("window")
    map_sha256 = d.get("map_sha256")
    gamemd_sha256 = d.get("gamemd_sha256")
    schema = d.get("schema")
    verdict = d.get("verdict")
    span_s = d.get("span_s")
    settle_s = d.get("settle_s")
    t_abs0 = d.get("t_abs0")
    dt_str = datetime.datetime.fromtimestamp(t_abs0).strftime("%Y-%m-%d %H:%M:%S") if t_abs0 else None
    
    gate = d.get("gate") or {}
    units0 = gate.get("units0")
    pre_fps15 = gate.get("pre_fps15")
    gate_ok = gate.get("ok")
    
    stats = d.get("stats") or {}
    fps_avg = stats.get("fps_avg")
    fps_p50 = stats.get("fps_p50")
    
    edges = d.get("frame_edges") or []
    n_edges = len(edges)
    
    live_fps = None
    f0, f1, df = None, None, None
    t0_edge, t1_edge, dt_edge = None, None, None
    if n_edges >= 2:
        f0 = edges[0][0]
        f1 = edges[-1][0]
        df = f1 - f0
        t0_edge = edges[0][1]
        t1_edge = edges[-1][1]
        dt_edge = t1_edge - t0_edge
        if dt_edge > 0 and df > 0:
            live_fps = df / dt_edge
        elif df == 0:
            live_fps = 0.0
    elif n_edges == 1:
        f0 = edges[0][0]
        f1 = edges[0][0]
        df = 0
        live_fps = 0.0
    
    # Check harness info in measure json or trip dir
    harness_sha16 = d.get("harness_sha16") or d.get("h8", {}).get("sha16")
    argv = None
    carriers_count = None
    
    # Try finding in parent_dir
    lr_path = os.path.join(parent_dir, "_launch_result.json")
    if os.path.exists(lr_path):
        try:
            with open(lr_path, "r", encoding="utf-8") as lrf:
                lrd = json.load(lrf)
            if not harness_sha16:
                harness_sha16 = lrd.get("harness_sha16") or lrd.get("harness_sha")
            argv = lrd.get("argv")
        except Exception:
            pass
            
    qf_path = os.path.join(parent_dir, "qc151_fields.json")
    if os.path.exists(qf_path):
        try:
            with open(qf_path, "r", encoding="utf-8") as qff:
                qfd = json.load(qff)
            if isinstance(qfd, list):
                for item in qfd:
                    if item.get("key") == "harness_sha16" and not harness_sha16:
                        harness_sha16 = item.get("value")
                    if item.get("key") == "harness" and not harness_sha16:
                        harness_sha16 = item.get("value")
                    if item.get("key") == "ts" and not dt_str:
                        dt_str = item.get("value")
            elif isinstance(qfd, dict):
                if not harness_sha16:
                    harness_sha16 = qfd.get("harness_sha16")
        except Exception:
            pass

    # Check carriers manifest
    cm_path = os.path.join(parent_dir, "carrier_manifest_pre_delete.json")
    if os.path.exists(cm_path):
        try:
            with open(cm_path, "r", encoding="utf-8") as cmf:
                cmd = json.load(cmf)
            if isinstance(cmd, list):
                carriers_count = len(cmd)
            elif isinstance(cmd, dict):
                carriers_count = len(cmd.get("carriers", cmd.get("files", [])))
        except Exception:
            pass

    rec = {
        "rel_path": rel_path,
        "trip_dir": trip_dir_name,
        "trip_id": trip_id,
        "window": window,
        "t_abs0": t_abs0,
        "dt_str": dt_str,
        "map_sha256": map_sha256,
        "units0": units0,
        "pre_fps15": pre_fps15,
        "gate_ok": gate_ok,
        "fps_avg": fps_avg,
        "fps_p50": fps_p50,
        "live_fps": live_fps,
        "n_edges": n_edges,
        "f0": f0,
        "f1": f1,
        "df": df,
        "dt_edge": dt_edge,
        "harness_sha16": harness_sha16,
        "argv_harness": argv[0] if argv else None,
        "carriers_count": carriers_count,
        "verdict": verdict,
        "schema": schema,
    }
    records.append(rec)

out_json = r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V2/all_windows.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

print(f"Collected {len(records)} records saved to {out_json}")
