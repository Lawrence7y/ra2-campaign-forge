# -*- coding: utf-8 -*-
"""V2 数据面独立核验全量计算脚本
严格零真机、零改动母本、仅写入本脚本所在目录。
"""
import glob
import json
import os
import sys

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUTPUT_DIR = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0a451d0b\V2"

all_files = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json")))

records = []
skipped = []

for p in all_files:
    trip = os.path.basename(os.path.dirname(p))
    fname = os.path.basename(p)
    try:
        with open(p, "r", encoding="utf-8") as f:
            j = json.load(f)
    except Exception as e:
        skipped.append((trip, fname, str(e)))
        continue

    ed = j.get("frame_edges") or []
    if not ed:
        skipped.append((trip, fname, f"empty frame_edges (len={len(ed)})"))
        continue

    f0 = ed[0][0]
    f1 = ed[-1][0]
    df = f1 - f0
    t0 = ed[0][1]
    t1 = ed[-1][1]
    dur = t1 - t0

    w = j.get("window")
    span_s = j.get("span_s") or 0.0
    stats = j.get("stats") or {}
    fps_avg = stats.get("fps_avg")
    logic_frames = stats.get("logic_frames")
    max_stall_s = stats.get("max_stall_s")

    gate = j.get("gate") or {}
    pre_fps15 = gate.get("pre_fps15")
    gate_ok = gate.get("ok")

    counters = j.get("counters") or []

    records.append({
        "path": p,
        "trip": trip,
        "fname": fname,
        "window": w,
        "f0": f0,
        "f1": f1,
        "df": df,
        "dur": dur,
        "span_s": span_s,
        "fps_avg": fps_avg,
        "logic_frames": logic_frames,
        "max_stall_s": max_stall_s,
        "pre_fps15": pre_fps15,
        "gate_ok": gate_ok,
        "counters": counters,
        "raw_json": j
    })

# --- 1. 全量重算窗分类 ---
adv = [r for r in records if r["df"] > 0]
frz = [r for r in records if r["df"] == 0 and r["f0"] != 0]
loadfrz = [r for r in records if r["df"] == 0 and r["f0"] == 0]
neg = [r for r in records if r["df"] < 0]

trips_all = sorted(list({r["trip"] for r in records}))

print(f"=== 1. 窗分类重算 ===")
print(f"总文件数: {len(all_files)}, 跳过文件数: {len(skipped)}, 有效窗数: {len(records)}, 涵盖趟数: {len(trips_all)}")
print(f"  有推进 (df > 0): {len(adv)}")
print(f"  战斗段冻结 (df == 0 and f0 != 0): {len(frz)}")
print(f"  加载段冻结 (df == 0 and f0 == 0): {len(loadfrz)}")
print(f"  帧号回退 (df < 0): {len(neg)}")

# --- 2. 有推进窗按 fps_avg 分档 ---
healthy = [r for r in adv if (r["fps_avg"] or 0) >= 28.0]
slow = [r for r in adv if (r["fps_avg"] or 0) < 28.0]

print(f"\n=== 2. 有推进窗 fps_avg 分档 ===")
print(f"  fps_avg >= 28.0 (健康/贴帽): {len(healthy)}")
print(f"  fps_avg < 28.0 (慢/卡/可用样本候选): {len(slow)}")

# --- 3. 29 个冻结窗详细反证检查 ---
print(f"\n=== 4. 29 冻结窗反证核查 ===")
frz_by_trip = {}
for r in frz:
    frz_by_trip.setdefault(r["trip"], []).append(r)

print(f"冻结窗覆盖趟数: {len(frz_by_trip)} (本线报 17 趟)")
# Check each frozen window
counter_anomalies = []
gate_anomalies = []
stall_anomalies = []

for r in frz:
    trip = r["trip"]
    w = r["window"]
    span = r["span_s"]
    max_stall = r["max_stall_s"]
    logic_f = r["logic_frames"]
    pre_fps = r["pre_fps15"]
    gate_ok = r["gate_ok"]
    cnts = r["counters"]

    # check gate
    # expectation: pre_fps15 is high (>25) while logic_frames == 0
    # or is pre_fps15 zero/low?
    if pre_fps is None or pre_fps < 25.0:
        gate_anomalies.append((trip, w, pre_fps, gate_ok, logic_f))

    # check stall: max_stall_s ≈ span_s
    # let's see delta
    stall_diff = abs((max_stall or 0.0) - span)
    if stall_diff > 0.01:
        stall_anomalies.append((trip, w, max_stall, span, stall_diff))

    # check counters: units, g, b
    # Check if counters are non-empty and whether they vary across time in this frozen window
    if cnts:
        units_set = {c.get("units") for c in cnts if isinstance(c, dict)}
        g_set = {c.get("g") for c in cnts if isinstance(c, dict)}
        b_set = {c.get("b") for c in cnts if isinstance(c, dict)}
        infantry_set = {c.get("infantry") for c in cnts if isinstance(c, dict)}
        techno_set = {c.get("techno") for c in cnts if isinstance(c, dict)}
        ws_set = {c.get("ws_kb") for c in cnts if isinstance(c, dict)}
        
        # Are units/g/b completely unchanged?
        if len(units_set) > 1 or len(g_set) > 1 or len(b_set) > 1:
            counter_anomalies.append((trip, w, "counters_changed", {
                "units": list(units_set), "g": list(g_set), "b": list(b_set)
            }))
    else:
        counter_anomalies.append((trip, w, "counters_empty", None))

print(f"反证核查结果:")
print(f"  gate.pre_fps15 异常数 (<25 或 None): {len(gate_anomalies)}")
for ga in gate_anomalies:
    print(f"    {ga[0]} w{ga[1]}: pre_fps15={ga[2]}, gate_ok={ga[3]}, logic_frames={ga[4]}")

print(f"  max_stall_s != span_s (差 > 0.01s): {len(stall_anomalies)}")
for sa in stall_anomalies:
    print(f"    {sa[0]} w{sa[1]}: max_stall={sa[2]}, span={sa[3]}, diff={sa[4]}")

print(f"  counters 变化/异常数: {len(counter_anomalies)}")
for ca in counter_anomalies:
    print(f"    {ca[0]} w{ca[1]}: {ca[2]} -> {ca[3]}")
