"""Read the harness's own per-window forensics payload for every frozen/advancing window of the
trips I picked as samples, plus capture_ok / capture_wh / game_title / fg_title — the harness's
own record of what it captured. Also finish the timer reads for the remaining crops."""
import os, glob, json
import numpy as np
from PIL import Image

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

for dr in ["archive_T38", "archive_T36", "archive_T42", "archive_T47", "l3_20261023r", "archive_T33"]:
    fp = os.path.join(R, dr, "qc151_fields.json")
    j = json.loads(open(fp, encoding="utf-8").read())
    print("=" * 100)
    print("[F]", dr, "| top keys:", list(j)[:12] if isinstance(j, dict) else type(j))
    hits = []

    def walk(o, path=""):
        if isinstance(o, dict):
            if "forensics_png" in o or "empty_window" in o:
                hits.append((path, o))
            for k, v in o.items():
                walk(v, path + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, path + f"[{i}]")

    walk(j)
    for path, o in hits:
        png = o.get("forensics_png")
        exists = os.path.exists(os.path.join(R, dr, png)) if png else None
        print(f"    {path[-40:]:40s} w={o.get('window')} empty={o.get('empty_window')} png={png} "
              f"on_disk={exists} capture_ok={o.get('capture_ok')} capture_wh={o.get('capture_wh')} "
              f"focus_ok={o.get('focus_ok')} frame={o.get('current_frame')}")
        if o.get("game_title") is not None:
            print(f"        game_title={o.get('game_title')!r} fg_title={o.get('fg_title')!r} fg_hwnd={o.get('fg_hwnd')} game_hwnd={o.get('game_hwnd')}")

print("\n[T] timer digits written earlier, re-listed for the record")
OUT = r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V2/pix"
for i, (rel, f0) in enumerate([("archive_T38/measure_w2_end_x.png", 940), ("archive_T40/measure_w1_end_x.png", 908),
                               ("archive_T49_u0800/measure_w1_end_x.png", 448), ("measure_w1_end_x.png", 373),
                               ("archive_T45/measure_w1_end_x.png", 845), ("archive_T36/measure_w1_end_x.png", 310)]):
    print(f"    digits_{i}.png <- {rel} f0={f0}  f0/31.2={f0/31.2:.2f}s  f0/30.0={f0/30.0:.2f}s")

print("\n[G] T47 forensics: does the harness itself say the capture succeeded?")
fp = os.path.join(R, "archive_T47", "qc151_fields.json")
raw = open(fp, encoding="utf-8").read()
j = json.loads(raw)
for i, rec in enumerate(j if isinstance(j, list) else []):
    if isinstance(rec, dict) and "measure_forensics" in str(rec.get("kind", "")) + str(rec.get("name", "")):
        print("    ", i, json.dumps(rec, ensure_ascii=False)[:400])
print("    type of top-level json:", type(j), "len" , len(j) if hasattr(j, "__len__") else "")
