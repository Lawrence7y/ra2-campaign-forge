# -*- coding: utf-8 -*-
"""
Corpus Survey & Factual Verification Script
Author: 语料勘查员
Scope: lead/early_trigger_feasibility_20261106/
Strictly read-only for corpus & event files.
"""

import glob
import json
import math
import os
import sys

def calc_median(arr):
    """
    Explicitly exclude None and NaN.
    For even n: average of two central values (arr[n//2 - 1] + arr[n//2]) / 2.0.
    For odd n: central value arr[n//2].
    Returns (median, n_valid).
    """
    clean = [x for x in arr if x is not None and not math.isnan(x)]
    clean.sort()
    n = len(clean)
    if n == 0:
        return None, 0
    if n % 2 == 1:
        med = clean[n // 2]
    else:
        med = (clean[n // 2 - 1] + clean[n // 2]) / 2.0
    return med, n

def main():
    base_dir = os.path.abspath(r"D:\Project\ra2-campaign-forge")
    corpus_pattern = os.path.join(
        base_dir, "out", "re_work", "work_chain", "CONTINUE_20261003",
        "lead", "qc161_u0400_trip", "**", "measure_w*.json"
    )
    stall_events_path = os.path.join(
        base_dir, "lead", "stall_event_def_20261106", "STALL_EVENTS.json"
    )

    print("================================================================================")
    print("1. GLOB COUNT: measure_w*.json")
    print("================================================================================")
    files = sorted(glob.glob(corpus_pattern, recursive=True))
    print(f"Glob pattern : {corpus_pattern}")
    print(f"Matched files: {len(files)}")

    print("\n================================================================================")
    print("2. INSPECTION OF 3 SAMPLE FILES")
    print("================================================================================")
    # Pick 3 representative files: first (index 0), middle (index 52), last (index 103)
    sample_indices = [0, len(files) // 2, len(files) - 1]
    sample_files = [(i, files[i]) for i in sample_indices]

    for rank, (idx, fpath) in enumerate(sample_files, 1):
        rel_path = os.path.relpath(fpath, base_dir)
        with open(fpath, "r", encoding="utf-8") as f:
            d = json.load(f)
        hz = d.get("hz")
        st = d.get("samples", {}).get("t", [])
        sf = d.get("samples", {}).get("f", [])
        span = (st[-1] - st[0]) if len(st) > 1 else 0.0
        diffs = [st[i+1] - st[i] for i in range(len(st)-1)] if len(st) > 1 else []
        med_diff, n_diff = calc_median(diffs)
        mean_diff = (sum(diffs) / len(diffs)) if diffs else 0.0

        print(f"Sample #{rank} (Index {idx}): {rel_path}")
        print(f"  hz: {hz} (expected 500)")
        print(f"  len(samples.t): {len(st)}")
        print(f"  len(samples.f): {len(sf)}")
        print(f"  samples.t == samples.f length: {len(st) == len(sf)}")
        print(f"  t[0]: {st[0] if st else None:.6f}, t[-1]: {st[-1] if st else None:.6f}")
        print(f"  Time span: {span:.6f} s")
        print(f"  Adjacent interval median: {med_diff:.6f} s ({med_diff*1000:.4f} ms, n={n_diff})")
        print(f"  Adjacent interval mean  : {mean_diff:.6f} s ({mean_diff*1000:.4f} ms)")

    print("\n================================================================================")
    print("3. AGGREGATE SAMPLE POINTS ACROSS ALL 104 FILES")
    print("================================================================================")
    total_t = 0
    total_f = 0
    all_hz = set()
    length_dist = {}
    zero_files = []
    file_spans = []
    all_diffs = []

    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            d = json.load(f)
        hz = d.get("hz")
        all_hz.add(hz)
        st = d.get("samples", {}).get("t", [])
        sf = d.get("samples", {}).get("f", [])
        lt = len(st)
        lf = len(sf)
        total_t += lt
        total_f += lf
        length_dist[lt] = length_dist.get(lt, 0) + 1

        if lt <= 1:
            zero_files.append((os.path.relpath(fpath, base_dir), lt, d.get("verdict"), d.get("error")))
        else:
            file_spans.append(st[-1] - st[0])
            for i in range(lt - 1):
                all_diffs.append(st[i+1] - st[i])

    print(f"Total files surveyed: {len(files)}")
    print(f"All hz values present in files: {sorted(list(all_hz))} (all 104 files == 500: {all_hz == {500}})")
    print(f"Total samples.t points across all files: {total_t}")
    print(f"Total samples.f points across all files: {total_f}")
    print(f"Equality check (total_t == total_f): {total_t == total_f}")
    print("\nDistribution of sample lengths per file:")
    for length in sorted(length_dist.keys()):
        print(f"  len={length:5d} : {length_dist[length]:2d} files")
    print(f"\nFiles with len <= 1 (Total: {len(zero_files)}):")
    for zpath, zlen, zverdict, zerr in zero_files:
        print(f"  - {zpath}: len={zlen}, verdict={zverdict}, error={zerr}")

    print("\n================================================================================")
    print("4. STALL_EVENTS.json BREAKDOWN")
    print("================================================================================")
    with open(stall_events_path, "r", encoding="utf-8") as f:
        events = json.load(f)

    total_events = len(events)
    real_events = [e for e in events if e.get("isRealMatch") is True]
    non_real_events = [e for e in events if e.get("isRealMatch") is not True]

    print(f"Total events in JSON: {total_events}")
    print(f"isRealMatch == True : {len(real_events)}")
    print(f"isRealMatch != True : {len(non_real_events)}")

    # Check NaN / None
    dur_real = [e.get("durationMs") for e in real_events]
    nan_count = sum(1 for d in dur_real if d is None or math.isnan(d))
    print(f"\nNaN / Missing value handling for real events (durationMs):")
    print(f"  Total real items: {len(dur_real)}")
    print(f"  NaN / None items: {nan_count}")
    print(f"  Valid items for statistical calculation: {len(dur_real) - nan_count}")

    # Buckets: 0-100 / 100-200 / 200-500 / 500-1000 / >=1000
    # Left-closed, right-open [a, b) standard:
    b0_100 = [d for d in dur_real if d is not None and not math.isnan(d) and 0 <= d < 100]
    b100_200 = [d for d in dur_real if d is not None and not math.isnan(d) and 100 <= d < 200]
    b200_500 = [d for d in dur_real if d is not None and not math.isnan(d) and 200 <= d < 500]
    b500_1000 = [d for d in dur_real if d is not None and not math.isnan(d) and 500 <= d < 1000]
    bge_1000 = [d for d in dur_real if d is not None and not math.isnan(d) and d >= 1000]

    print("\nDuration Buckets for Real Events (interval [a, b)):")
    print(f"  [0, 100) ms   : {len(b0_100):4d}")
    print(f"  [100, 200) ms : {len(b100_200):4d}")
    print(f"  [200, 500) ms : {len(b200_500):4d}")
    print(f"  [500, 1000) ms: {len(b500_1000):4d}")
    print(f"  >= 1000 ms    : {len(bge_1000):4d}")
    print(f"  Bucket sum    : {len(b0_100) + len(b100_200) + len(b200_500) + len(b500_1000) + len(bge_1000)}")

    # Boundary hits
    exact_100 = sum(1 for d in dur_real if d == 100.0)
    print(f"  Exact hits at boundary 100.0 ms: {exact_100}")
    print(f"  (Note: if defined as (0, 100] and (100, 200], then (0, 100] has 1, (100, 200] has 1519)")

    # Median
    med_real, n_real = calc_median(dur_real)
    print(f"\nReal Events durationMs Statistics (n={n_real}):")
    print(f"  Min   : {min(dur_real):.4f} ms")
    print(f"  Max   : {max(dur_real):.4f} ms")
    print(f"  Median: {med_real:.4f} ms")
    print(f"  Median calculation rule: n={n_real} (odd), central index {n_real // 2}, value={sorted(dur_real)[n_real // 2]:.4f} ms")

    print("\n================================================================================")
    print("5. TIME SPAN AND ADJACENT INTERVAL MEDIAN OF samples.t")
    print("================================================================================")
    print("A. Across 3 sampled files individually:")
    for rank, (idx, fpath) in enumerate(sample_files, 1):
        rel_path = os.path.relpath(fpath, base_dir)
        with open(fpath, "r", encoding="utf-8") as f:
            d = json.load(f)
        st = d.get("samples", {}).get("t", [])
        span = (st[-1] - st[0]) if len(st) > 1 else 0.0
        diffs = [st[i+1] - st[i] for i in range(len(st)-1)] if len(st) > 1 else []
        med_diff, n_diff = calc_median(diffs)
        mean_diff = (sum(diffs) / len(diffs)) if diffs else 0.0
        print(f"  Sample #{rank} ({rel_path}):")
        print(f"    samples count            : {len(st)}")
        print(f"    Time span                : {span:.6f} s")
        print(f"    Adjacent intervals count : n={n_diff}")
        print(f"    Adjacent interval median : {med_diff:.6f} s ({med_diff*1000:.4f} ms)")
        print(f"    Adjacent interval mean   : {mean_diff:.6f} s ({mean_diff*1000:.4f} ms)")

    print("\nB. Across all files with valid samples:")
    med_span, n_span = calc_median(file_spans)
    mean_span = sum(file_spans) / len(file_spans) if file_spans else 0.0
    print(f"  Per-file time span (n={n_span} files with samples > 1, 5 empty files excluded):")
    print(f"    Min span   : {min(file_spans):.6f} s")
    print(f"    Max span   : {max(file_spans):.6f} s")
    print(f"    Median span: {med_span:.6f} s (central value of sorted spans)")
    print(f"    Mean span  : {mean_span:.6f} s")
    print(f"    Total cumulative span (sum): {sum(file_spans):.6f} s")

    med_all_diffs, n_all_diffs = calc_median(all_diffs)
    mean_all_diffs = sum(all_diffs) / len(all_diffs) if all_diffs else 0.0
    print(f"\n  Adjacent intervals across all files combined (n={n_all_diffs} intervals):")
    print(f"    Min interval   : {min(all_diffs):.6f} s ({min(all_diffs)*1000:.4f} ms)")
    print(f"    Max interval   : {max(all_diffs):.6f} s ({max(all_diffs)*1000:.4f} ms)")
    print(f"    Median interval: {med_all_diffs:.6f} s ({med_all_diffs*1000:.4f} ms)")
    print(f"    Mean interval  : {mean_all_diffs:.6f} s ({mean_all_diffs*1000:.4f} ms)")
    print(f"    Median calculation rule: n={n_all_diffs} (odd), central index {n_all_diffs // 2}, value={med_all_diffs:.6f} s")
    print("================================================================================")

if __name__ == "__main__":
    main()
