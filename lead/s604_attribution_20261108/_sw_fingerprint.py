# -*- coding: utf-8 -*-
"""_sw_fingerprint.py — 归属撰写员自算指纹（只读，不修改任何被测件）。
九件上游 + 台账 + PENDING + 写域既有件。输出 SHA256 / bytes / 行数 / mtime。"""
import hashlib, os, sys

BASE = r"D:\Project\ra2-campaign-forge"
FILES = [
    r"lead\GOAL_THREE_TARGETS_20261018.md",
    r"lead\PENDING_DECISIONS.md",
    r"lead\slowframe_r3_20261108\S604_GAP_RECHECK.md",
    r"lead\slowframe_r3_20261108\_r3_GAPDIFF_RECHECK.md",
    r"lead\slowframe_r3_20261108\_r3_recompute_gapdiff.py",
    r"lead\slowframe_r3_20261108\_r3_recompute_out.txt",
    r"lead\slowframe_r3_20261108\_verify_r3_gapdiff.py",
    r"lead\slowframe_r3_20261108\_verify_r3_out.txt",
    r"lead\slowwindow_n8_20261108\SLOW_WINDOW_LIMITS.md",
    r"lead\s604_attribution_20261108\_sa_ATTRIBUTION_S604.md",
    r"lead\s604_attribution_20261108\_sa_probe.py",
    r"lead\s604_attribution_20261108\_sa_probe_out.txt",
    r"lead\s604_attribution_20261108\_sv_fingerprint.py",
    r"lead\s604_attribution_20261108\_sv_numcheck.py",
    r"lead\s604_attribution_20261108\_sv_scan.py",
]

for rel in FILES:
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        print(f"[MISS] {rel}")
        continue
    h = hashlib.sha256()
    nlines = 0
    with open(p, "rb") as f:
        data = f.read()
    h.update(data)
    nlines = data.count(b"\n")
    # 尾行无换行时补计
    if data and not data.endswith(b"\n"):
        nlines += 1
    mt = os.stat(p).st_mtime
    import datetime
    mts = datetime.datetime.fromtimestamp(mt).strftime("%Y-%m-%d %H:%M:%S")
    print(f"{rel}\n  SHA256 = {h.hexdigest()}\n  bytes = {len(data)}  lines = {nlines}  mtime = {mts}")
print("[done] _sw_fingerprint")
