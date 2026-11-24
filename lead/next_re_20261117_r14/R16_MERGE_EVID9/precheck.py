# -*- coding: utf-8 -*-
"""Pre-check: verify new evidence paths exist, compute atlas proved stats, fix before_state.json."""
import hashlib, os, sys, json
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
R14 = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(R14, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUT = os.path.join(R14, "R16_MERGE_EVID9")

# 1. verify new paths (relative to r14 base, as resolve.py does)
newpaths = [
    r"S10_K8\EVIDENCE\OWNERSHIP_004E0E80.txt",
    r"S10_K8\EVIDENCE\SPAWNMANAGER_CTORS.txt",
    r"S10_K8F\EVIDENCE\QUEUE_DISPATCH_AND_FALSE_KILLS.txt",
]
for rel in newpaths:
    p = os.path.join(R14, rel.replace("\\", os.sep))
    print("isfile", os.path.isfile(p), "bytes", (os.path.getsize(p) if os.path.isfile(p) else "-"), rel)

# 2. atlas proved stats (mirror strict_panel.py normalization)
def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i, line in enumerate(f):
        if i == 0:
            continue
        p = line.rstrip("\r\n").split("\t")
        if p and p[0].strip():
            atlas.add(ne(p[0]))
print("atlas entries:", len(atlas))

import csv
with open(COV, encoding="utf-8-sig", newline="") as f:
    cov = list(csv.reader(f, delimiter="\t"))[1:]
proved_all = [r for r in cov if len(r) >= 8 and r[4].strip() == "[已证]"]
proved_in = [r for r in proved_all if ne(r[0]) in atlas]
proved_out = [r for r in proved_all if ne(r[0]) not in atlas]
print("proved all:", len(proved_all), "atlas in:", len(proved_in), "atlas out:", len(proved_out))
print("atlas-out proved entries:", [r[0] for r in proved_out])

# target rows in/out atlas
TARGETS = ["004E0E80","006B6EA0","006B6FA0","004DF320","004DF3A0","004DFB70","004DFCB0","004DFE00","006F4960"]
print("targets atlas membership:", {e: (ne(e) in atlas) for e in TARGETS})

# 3. fix before_state.json from pre_record data (store col6 strings, not bytes)
def sha(b):
    return hashlib.sha256(b).hexdigest().upper()

import time
def stat(path):
    b = open(path, "rb").read()
    st = os.stat(path)
    return {"path": path, "mtime": st.st_mtime,
            "mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(st.st_mtime)),
            "bytes": len(b), "sha256": sha(b),
            "line_count_lf": b.count(b"\n"), "crlf_count": b.count(b"\r\n"),
            "bom_utf8": b.startswith(b"\xef\xbb\xbf")}

covst, panst = stat(COV), stat(PANEL)
raw = open(COV, "rb").read()
lines = raw.split(b"\n")
target_rows = {}
for i, ln in enumerate(lines[1:], start=2):
    s = ln.rstrip(b"\r")
    if not s.strip():
        continue
    cols = s.split(b"\t")
    if len(cols) != 8:
        continue
    e = cols[0].decode("utf-8")
    if e in TARGETS:
        target_rows[e] = {"line_no_1based": i, "col6": cols[5].decode("utf-8"),
                          "cols": [c.decode("utf-8") for c in cols]}
state = {"coverage": covst, "panel": panst, "target_rows": target_rows,
         "baseline": {"data_rows": len(cov), "proved": len(proved_all),
                      "proved_atlas_in": len(proved_in), "proved_atlas_out": len(proved_out),
                      "col_dist": {"8": len(cov)}, "file_trailing_newline": raw.endswith(b"\n"),
                      "atlas_total_entries": len(atlas)}}
with open(os.path.join(OUT, "before_state.json"), "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=1)
print("wrote before_state.json OK")
