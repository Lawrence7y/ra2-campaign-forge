# -*- coding: utf-8 -*-
"""Task 1: Group by units0, check 1180-1360 comparison."""
import json
from collections import defaultdict

with open(r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V2/all_windows.json", "r", encoding="utf-8") as f:
    records = json.load(f)

print(f"Total windows: {len(records)}")

computable = [r for r in records if r["live_fps"] is not None and r["live_fps"] > 0 and r["units0"] is not None]
print(f"Computable windows with live_fps > 0 and units0 is not None: {len(computable)}")

computable_all = [r for r in records if r["live_fps"] is not None and r["units0"] is not None]
print(f"Computable windows with live_fps (including 0.0) and units0 is not None: {len(computable_all)}")

# Group by units0
by_units = defaultdict(list)
for r in computable:
    by_units[r["units0"]].append(r)

print(f"Total unique units0 values: {len(by_units)}")
print("\n=== Units0 groups with >= 3 occurrences ===")
for u in sorted(by_units.keys()):
    group = by_units[u]
    if len(group) >= 3:
        print(f"\nunits0 = {u} (count = {len(group)}):")
        for r in sorted(group, key=lambda x: x["dt_str"] or ""):
            print(f"  {r['dt_str']} | live_fps: {r['live_fps']:6.2f} (fps_avg: {r['fps_avg'] if r['fps_avg'] is not None else -1:6.2f}, fps_p50: {r['fps_p50'] if r['fps_p50'] is not None else -1:6.2f}) | trip: {r['trip_id']} ({r['trip_dir']}) | {r['rel_path']}")

print("\n" + "="*80)
print("=== Key Comparison: units0 in [1180, 1360] ===")
comp_group = [r for r in records if r["units0"] is not None and 1180 <= r["units0"] <= 1360]
print(f"Count of windows with units0 in [1180, 1360]: {len(comp_group)}")
for r in sorted(comp_group, key=lambda x: x["dt_str"] or ""):
    print(f"  units0: {r['units0']} | {r['dt_str']} | live_fps: {r['live_fps'] if r['live_fps'] is not None else 'None':>6} | fps_avg: {r['fps_avg'] if r['fps_avg'] is not None else 'None':>6} | trip: {r['trip_id']} ({r['trip_dir']}) | win: {r['window']} | path: {r['rel_path']}")
