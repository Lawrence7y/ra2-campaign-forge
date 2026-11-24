# -*- coding: utf-8 -*-
"""
Independent sample verification script for V3 RECHECK.
Zero real machine, read-only on raw data.
"""
import os
import json
import hashlib
from PIL import Image
import numpy as np

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

def audit_sample_t34():
    print("==================================================")
    print("SAMPLE 1: archive_T34 (Standard Frozen Candidate)")
    print("==================================================")
    trip_dir = os.path.join(BASE, "archive_T34")
    # 1. Read JSONs
    for w in [0, 1, 2]:
        p = os.path.join(trip_dir, f"measure_w{w}.json")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            edges = d.get("frame_edges", [])
            f0 = edges[0][0] if edges else None
            f1 = edges[-1][0] if edges else None
            df = f1 - f0 if edges else None
            span = d.get("span_s")
            max_stall = d.get("stats", {}).get("max_stall_s")
            fps_avg = d.get("stats", {}).get("fps_avg")
            print(f"  w{w}: edges={len(edges)} f0={f0} f1={f1} df={df} span={span} max_stall={max_stall} fps_avg={fps_avg}")

    # 2. Check qc151_fields.json
    qpath = os.path.join(trip_dir, "qc151_fields.json")
    with open(qpath, "r", encoding="utf-8") as f:
        qdata = json.load(f)
    for row in qdata:
        if "measure_forensics" in row.get("key", ""):
            print(f"  forensics: {row['key']} -> {row.get('value') or row.get('payload')}")

    # 3. Check PNGs
    p_w1 = os.path.join(trip_dir, "measure_w1_end_x.png")
    p_w2 = os.path.join(trip_dir, "measure_w2_end_x.png")
    im1 = Image.open(p_w1).convert("RGB")
    im2 = Image.open(p_w2).convert("RGB")
    arr1 = np.array(im1)
    arr2 = np.array(im2)
    raw1 = hashlib.sha256(open(p_w1, "rb").read()).hexdigest()
    raw2 = hashlib.sha256(open(p_w2, "rb").read()).hexdigest()
    px1 = hashlib.sha256(im1.tobytes()).hexdigest()
    px2 = hashlib.sha256(im2.tobytes()).hexdigest()
    print(f"  w1 PNG: size={im1.size} raw_sha={raw1[:16]} px_sha={px1[:16]}")
    print(f"  w2 PNG: size={im2.size} raw_sha={raw2[:16]} px_sha={px2[:16]}")
    
    # Check timer region (approx (430,118) to (640,150) or exact coords)
    # Let's inspect where yellow timer text is located in w1/w2:
    # Yellow text has high R, high G, low B
    timer_crop1 = arr1[120:150, 480:600]
    timer_crop2 = arr2[120:150, 480:600]
    diff = np.abs(timer_crop1.astype(int) - timer_crop2.astype(int))
    print(f"  Timer crop (120:150, 480:600) max diff: {diff.max()}")

def audit_sample_t38():
    print("==================================================")
    print("SAMPLE 2: archive_T38 (Advance vs Freeze Dispute)")
    print("==================================================")
    trip_dir = os.path.join(BASE, "archive_T38")
    for w in [0, 1, 2]:
        p = os.path.join(trip_dir, f"measure_w{w}.json")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            edges = d.get("frame_edges", [])
            f0 = edges[0][0] if edges else None
            f1 = edges[-1][0] if edges else None
            df = f1 - f0 if edges else None
            span = d.get("span_s")
            max_stall = d.get("stats", {}).get("max_stall_s")
            fps_avg = d.get("stats", {}).get("fps_avg")
            print(f"  w{w}: edges={len(edges)} f0={f0} f1={f1} df={df} span={span} max_stall={max_stall} fps_avg={fps_avg}")

    qpath = os.path.join(trip_dir, "qc151_fields.json")
    with open(qpath, "r", encoding="utf-8") as f:
        qdata = json.load(f)
    for row in qdata:
        if "measure_forensics" in row.get("key", ""):
            print(f"  forensics: {row['key']} -> {row.get('value') or row.get('payload')}")

    p_w1 = os.path.join(trip_dir, "measure_w1_end_x.png")
    p_w2 = os.path.join(trip_dir, "measure_w2_end_x.png")
    p_t36_w1 = os.path.join(BASE, "archive_T36", "measure_w1_end_x.png")

    raw_t38_w1 = hashlib.sha256(open(p_w1, "rb").read()).hexdigest()
    raw_t36_w1 = hashlib.sha256(open(p_t36_w1, "rb").read()).hexdigest()
    m_t38_w1 = os.path.getmtime(p_w1)
    m_t36_w1 = os.path.getmtime(p_t36_w1)
    print(f"  T38/w1 vs T36/w1 raw sha match: {raw_t38_w1 == raw_t36_w1}")
    print(f"  T38/w1 mtime: {m_t38_w1}, T36/w1 mtime: {m_t36_w1}, diff: {m_t38_w1 - m_t36_w1}")

    # Inspect w2 timer
    im2 = Image.open(p_w2).convert("RGB")
    arr2 = np.array(im2)
    raw2 = hashlib.sha256(open(p_w2, "rb").read()).hexdigest()
    print(f"  T38/w2 PNG raw sha: {raw2[:16]}")
    # Let's inspect the timer in w2
    # In S543, Leader claimed w2 is 00:00:30 in Table 2, but 00:00:32 in text
    # Let's print bitmap of digits in w2 timer!
    print("  T38 w2 timer bitmap inspection (y: 125..145, x: 545..585):")
    # Coordinates of last two digits '32'
    crop_timer = arr2[125:145, 490:585]
    for r in range(crop_timer.shape[0]):
        line = ""
        for c in range(crop_timer.shape[1]):
            px = crop_timer[r, c]
            # Yellow digits: high R, high G, low B
            if px[0] > 180 and px[1] > 180 and px[2] < 80:
                line += "#"
            elif px[0] > 100 and px[1] > 100 and px[2] < 60:
                line += "."
            else:
                line += " "
        if "#" in line or "." in line:
            print(f"    {125+r:3d}: {line}")

def audit_sample_t42():
    print("==================================================")
    print("SAMPLE 3: archive_T42 (Art Background Mystery)")
    print("==================================================")
    trip_dir = os.path.join(BASE, "archive_T42")
    for w in [0, 1, 2]:
        p = os.path.join(trip_dir, f"measure_w{w}.json")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            edges = d.get("frame_edges", [])
            f0 = edges[0][0] if edges else None
            f1 = edges[-1][0] if edges else None
            df = f1 - f0 if edges else None
            span = d.get("span_s")
            max_stall = d.get("stats", {}).get("max_stall_s")
            fps_avg = d.get("stats", {}).get("fps_avg")
            print(f"  w{w}: edges={len(edges)} f0={f0} f1={f1} df={df} span={span} max_stall={max_stall} fps_avg={fps_avg}")

    qpath = os.path.join(trip_dir, "qc151_fields.json")
    with open(qpath, "r", encoding="utf-8") as f:
        qdata = json.load(f)
    for row in qdata:
        if "measure_forensics" in row.get("key", ""):
            print(f"  forensics: {row['key']} -> {row.get('value') or row.get('payload')}")

    p_w1 = os.path.join(trip_dir, "measure_w1_end_x.png")
    p_w2 = os.path.join(trip_dir, "measure_w2_end_x.png")
    im1 = Image.open(p_w1).convert("RGB")
    im2 = Image.open(p_w2).convert("RGB")
    raw1 = hashlib.sha256(open(p_w1, "rb").read()).hexdigest()
    raw2 = hashlib.sha256(open(p_w2, "rb").read()).hexdigest()
    px1 = hashlib.sha256(im1.tobytes()).hexdigest()
    px2 = hashlib.sha256(im2.tobytes()).hexdigest()
    print(f"  w1 raw_sha={raw1[:16]} px_sha={px1[:16]}")
    print(f"  w2 raw_sha={raw2[:16]} px_sha={px2[:16]}")
    print(f"  w1 == w2 raw: {raw1 == raw2}, px: {px1 == px2}")

    # Cross-check with T33/w2 and T45/w2
    p_t33_w2 = os.path.join(BASE, "archive_T33", "measure_w2_end_x.png")
    p_t45_w2 = os.path.join(BASE, "archive_T45", "measure_w2_end_x.png")
    raw_t33 = hashlib.sha256(open(p_t33_w2, "rb").read()).hexdigest()
    raw_t45 = hashlib.sha256(open(p_t45_w2, "rb").read()).hexdigest()
    print(f"  T33/w2 raw_sha={raw_t33[:16]} == T42/w1? {raw_t33 == raw1}")
    print(f"  T45/w2 raw_sha={raw_t45[:16]} == T42/w1? {raw_t45 == raw1}")

    # Inspect image content
    arr = np.array(im1)
    # Check if there is sidebar or text
    # In RA2, right sidebar is x: 640..800
    sidebar = arr[:, 640:]
    radar_area = arr[0:160, 640:800]
    print(f"  Radar area mean RGB: {radar_area.mean(axis=(0,1))}")
    # Center area
    center = arr[100:500, 150:600]
    print(f"  Center area mean RGB: {center.mean(axis=(0,1))}")

if __name__ == "__main__":
    audit_sample_t34()
    audit_sample_t38()
    audit_sample_t42()
