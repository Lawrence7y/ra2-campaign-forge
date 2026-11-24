# -*- coding: utf-8 -*-
"""RECHECK sample A: provenance of every window-end PNG, computed from bytes.

For each measure_w*_end_*.png: file sha256, pixel sha256, mtime, and the mtime of
the paired measure_w{k}.json in the SAME directory. Flag |delta| > 2s.
Also dump the harness forensics record (qc151_fields.json) for archive_T38 w1/w2
and archive_T36 w1/w2: empty_window / forensics_png / logic_frames / n_edges.
Read-only.
"""
import glob
import hashlib
import json
import os
import time

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
try:
    from PIL import Image
except Exception as e:
    Image = None
    print("PIL unavailable:", e)

pngs = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png"))) + \
       sorted(glob.glob(os.path.join(BASE, "measure_w*_end_*.png")))
pngs = sorted(set(pngs))
print("window-end pngs:", len(pngs))

by_sha = {}
by_pix = {}
rows = []
for p in pngs:
    raw = open(p, "rb").read()
    fh = hashlib.sha256(raw).hexdigest()
    ph = ""
    if Image:
        im = Image.open(p)
        im.load()
        ph = hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()
    pj = os.path.join(os.path.dirname(p), "measure_w%s.png" % p.split("measure_w")[1].split("_")[0])
    pj = pj.replace(".png", ".json")
    jm = os.path.getmtime(pj) if os.path.exists(pj) else None
    pm = os.path.getmtime(p)
    delta = (pm - jm) if jm is not None else None
    trip = os.path.basename(os.path.dirname(p)) or "<root>"
    if trip == os.path.basename(BASE):
        trip = "<root>"
    rows.append((trip, os.path.basename(p), fh[:10], ph[:10] if ph else "-", pm, delta))
    by_sha.setdefault(fh, []).append(trip + "/" + os.path.basename(p))
    if ph:
        by_pix.setdefault(ph, []).append(trip + "/" + os.path.basename(p))

print("\n%-20s %-24s %-11s %-11s %-20s %s" % ("trip", "png", "filesha", "pixsha", "png mtime", "delta vs own json"))
for t, n, fh, ph, pm, d in sorted(rows):
    print("%-20s %-24s %-11s %-11s %-20s %s" % (t, n, fh, ph, time.strftime("%m-%d %H:%M:%S", time.localtime(pm)),
          ("%+.0fs" % d) if d is not None else "NO JSON"))

bad = [r for r in rows if r[5] is not None and abs(r[5]) > 2]
norec = [r for r in rows if r[5] is None]
print("\n|delta|>2s :", len(bad))
for r in bad:
    print("   ", r, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r[4])))
print("json missing for:", len(norec), norec)

print("\n=== file-sha duplicate groups (size>1) ===")
for k, v in by_sha.items():
    if len(v) > 1:
        print("  %s n=%d : %s" % (k[:10], len(v), v))
print("=== pixel-sha duplicate groups (size>1) ===")
for k, v in by_pix.items():
    if len(v) > 1:
        print("  %s n=%d : %s" % (k[:10], len(v), v))

print("\n=== harness records: archive_T36 / archive_T38 ===")
for t in ("archive_T36", "archive_T38"):
    fp = os.path.join(BASE, t, "qc151_fields.json")
    if not os.path.exists(fp):
        print(" no fields file:", fp)
        continue
    d = json.load(open(fp, encoding="utf-8"))
    print(" %s top keys: %s" % (t, list(d)[:12]))
    for k, v in d.items():
        if "forensic" in k.lower() or "MEASURE" in k.upper():
            s = json.dumps(v, ensure_ascii=False)
            print("   key=%s -> %s" % (k, s[:900]))
    for line in (d.get("lines") or d.get("rows") or []):
        s = json.dumps(line, ensure_ascii=False)
        if "forensic" in s or "empty_window" in s:
            print("   LINE", s[:900])
