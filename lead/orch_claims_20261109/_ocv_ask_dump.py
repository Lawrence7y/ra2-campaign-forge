# -*- coding: utf-8 -*-
"""_ocv_ask_dump.py - dump selected archived ASK_ANALYST strings verbatim
with line numbers inside payload.lowered, to verify 'misdirected downstream'
and the 'independent verification' discipline. Read-only."""
import json, os

DIR = "D:/Project/ra2-campaign-forge/.zcode/workflow-runs/"
FILES = [
 "dwfrun-02fe73a6-9571-45d9-9009-af96720a48c5.mjs",
 "dwfrun-868215ce-ea87-4e41-a54b-5a0af3c441dd.mjs",
 "dwfrun-5876dbf3-36f9-4f9c-8ec3-8a7fefb07395.mjs",
 "dwfrun-b52cb76a-50a8-48ee-90c0-9dc264a22743.mjs",
 "dwfrun-89df48db-a7c0-4905-85b8-68da3f294695.mjs",
]
KEYS = ["92,105,129", "三件", "10 个域", "5 个域", "四条问题", "四条",
        "不得采信", "独立核对", "以你的为准", "你要独立", "可以插", "修好 H5",
        "4 件", "最小", "必现要素", "交付"]

for f in FILES:
    p = DIR + f
    src = open(p, encoding="utf-8").read()
    i = src.find("export const payload = ")
    payload, _ = json.JSONDecoder().raw_decode(src[i + len("export const payload = "):])
    lowered = payload.get("lowered", "")
    print("=" * 25, f, "lowered_chars =", len(lowered), "=" * 25)
    lines = lowered.splitlines()
    for n, L in enumerate(lines, 1):
        if any(k in L for k in KEYS):
            print(f"lowered:{n}: {L[:500]}")
