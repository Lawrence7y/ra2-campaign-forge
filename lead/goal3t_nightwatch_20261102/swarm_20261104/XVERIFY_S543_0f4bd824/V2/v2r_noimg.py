"""For every FRZ window WITHOUT an end png: what did the harness itself record?
(capture_ok / capture_wh / forensics_png / empty_window). Read-only."""
import os, glob, json

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
SUB = sorted(glob.glob(os.path.join(R, "*", "measure_w*.json")))
ROOT = sorted(glob.glob(os.path.join(R, "measure_w*.json")))
disk = {os.path.relpath(q, R).replace("\\", "/") for q in glob.glob(os.path.join(R, "*", "measure_w*_end_*.png"))} | \
       {os.path.basename(q) for q in glob.glob(os.path.join(R, "measure_w*_end_*.png"))}


def cls(d):
    fe = d.get("frame_edges") or []
    if not fe:
        return "NO_EDGES", None
    f0, f1 = fe[0][0], fe[-1][0]
    df = f1 - f0
    return ("ADV" if df > 0 else ("LOAD" if f0 == 0 and df == 0 else ("FRZ" if df == 0 else "BACK"))), f0


print("[N1] FRZ windows with no end_x png on disk -> what the fields log says")
for p in SUB + ROOT:
    d = json.load(open(p, encoding="utf-8"))
    rel = os.path.relpath(p, R).replace("\\", "/")
    k, f0 = cls(d)
    if k != "FRZ":
        continue
    pngrel = rel.replace(".json", "").replace("measure_w", "measure_w") + "_end_x.png"
    base = rel.split("/")[-1]
    on_disk = pngrel in disk or base.replace(".json", "_end_x.png") in disk
    if on_disk:
        continue
    dr = "." if p in ROOT else rel.split("/")[0]
    fp = os.path.join(R, *(dr.split("/")), "qc151_fields.json") if dr != "." else os.path.join(R, "qc151_fields.json")
    rec = None
    if os.path.exists(fp):
        j = json.loads(open(fp, encoding="utf-8").read())
        hits = []

        def walk(o):
            if isinstance(o, dict):
                if "empty_window" in o and o.get("window") == d.get("window"):
                    hits.append(o)
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(j)
        rec = hits[0] if hits else "NO_MATCHING_RECORD"
    print(f"    {rel:36s} f0={f0:6d} png_on_disk={on_disk}")
    print(f"        fields: {json.dumps(rec, ensure_ascii=False)[:300] if rec else 'fields file missing'}")
    # what files DO exist for that window in that dir
    dd = os.path.dirname(p)
    print("        files in dir matching measure_w*:", sorted(os.path.basename(x) for x in glob.glob(os.path.join(dd, "measure_w*"))))

print("\n[N2] every distinct capture of the score-screen backdrop: is the 4-way image the SAME backdrop")
print("     as the score screens with the table removed? (whole-image diff localization)")
import numpy as np
from PIL import Image
ref_score = np.asarray(Image.open(os.path.join(R, "archive_T33", "measure_w1_end_x.png")).convert("RGB")).astype(np.int16)
ref_back = np.asarray(Image.open(os.path.join(R, "archive_T33", "measure_w2_end_x.png")).convert("RGB")).astype(np.int16)
dif = np.abs(ref_score - ref_back).max(axis=2)
for y0 in range(0, 600, 25):
    band = (dif[y0:y0 + 25] > 24).sum()
    print(f"    y {y0:3d}-{y0+24:3d}: differing px in band = {band:7d}")
cols = (dif > 24).sum(axis=0)
print("    cols>100 diff px:", [int(x) for x in np.where(cols > 100)[0]][:12], "...",
      [int(x) for x in np.where(cols > 100)[0]][-12:])
