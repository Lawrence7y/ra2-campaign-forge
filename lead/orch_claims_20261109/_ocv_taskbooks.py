# -*- coding: utf-8 -*-
"""_ocv_taskbooks.py - inspect archived .mjs task books for literal claim contexts.
Decodes payload.lowered, prints matching lines with file:line-ish context.
Read-only."""
import json, os, sys, glob

DIR = "D:/Project/ra2-campaign-forge/.zcode/workflow-runs/"
KEYS = sys.argv[1:] if len(sys.argv) > 1 else ["16384", "挑错中稿", "脚本缺陷", "0.8599", "32768"]
FILES = sorted(glob.glob(DIR + "*.mjs"))

for p in FILES:
    src = open(p, encoding="utf-8").read()
    i = src.find("export const payload = ")
    if i < 0:
        continue
    try:
        payload, _ = json.JSONDecoder().raw_decode(src[i + len("export const payload = "):])
        lowered = payload.get("lowered", "")
    except Exception:
        continue
    if not isinstance(lowered, str):
        continue
    lines = lowered.splitlines()
    for k in KEYS:
        for n, L in enumerate(lines, 1):
            if k in L:
                print(f"[{os.path.basename(p)}] lowered:{n} key={k}")
                print("   " + L[:400].replace("\t", " "))
