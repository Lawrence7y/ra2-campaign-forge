# -*- coding: utf-8 -*-
"""Pre-change record for R16-MERGE-EVID9. Read-only on target files."""
import hashlib, os, sys, json, time
sys.stdout.reconfigure(encoding="utf-8")

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(R14, "COVERAGE", "PANEL.md")
OUT = os.path.join(R14, "R16_MERGE_EVID9")

ENTRIES = ["004E0E80", "006B6EA0", "006B6FA0",
           "004DF320", "004DF3A0", "004DFB70", "004DFCB0", "004DFE00", "006F4960"]

def sha(b):
    return hashlib.sha256(b).hexdigest().upper()

def stat(path):
    with open(path, "rb") as f:
        b = f.read()
    st = os.stat(path)
    return {
        "path": path,
        "mtime": st.st_mtime,
        "mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(st.st_mtime)),
        "bytes": len(b),
        "sha256": sha(b),
        "line_count_lf": b.count(b"\n"),
        "crlf_count": b.count(b"\r\n"),
        "bom_utf8": b.startswith(b"\xef\xbb\xbf"),
    }

cov = stat(COV)
pan = stat(PANEL)
print("COVERAGE:", json.dumps(cov, ensure_ascii=False))
print("PANEL   :", json.dumps(pan, ensure_ascii=False))

raw = open(COV, "rb").read()
# detect line endings
print("CRLF count:", raw.count(b"\r\n"), " bare LF:", raw.count(b"\n") - raw.count(b"\r\n"))
print("first 200 bytes repr:", repr(raw[:200]))

lines = raw.split(b"\n")
print("split lines count (incl trailing):", len(lines))

# Parse: header uses comma, data uses tab (per resolve.py)
hdr = lines[0].rstrip(b"\r").decode("utf-8").split(",")
print("header cols:", hdr)

# index rows by entry (col 0) using tab split, strip trailing \r from last col only
from collections import Counter
entry_count = Counter()
rows = {}
for i, ln in enumerate(lines[1:], start=2):
    s = ln.rstrip(b"\r")
    if not s.strip():
        continue
    cols = s.split(b"\t")
    if len(cols) != 8:
        continue
    e = cols[0].decode("utf-8", "replace")
    entry_count[e] += 1
    if e in ENTRIES:
        rows[e] = {"line_no": i, "line_index_0based": i-1,
                   "cols": [c.decode("utf-8", "replace") for c in cols],
                   "raw_line": ln}

for e in ENTRIES:
    r = rows.get(e)
    if not r:
        print("ENTRY", e, "NOT FOUND")
        continue
    print("ENTRY", e, "line", r["line_no"], "col6:", r["cols"][5])
    print("     full cols:", json.dumps(r["cols"], ensure_ascii=False))

# baseline stats: data rows, [已证], col-count distribution
data_rows = 0
proved = 0
col_dist = Counter()
for i, ln in enumerate(lines[1:], start=2):
    s = ln.rstrip(b"\r")
    if not s.strip():
        continue
    cols = s.split(b"\t")
    col_dist[len(cols)] += 1
    if len(cols) == 8:
        data_rows += 1
        if cols[4].decode("utf-8", "replace").strip() == "[已证]":
            proved += 1
print("data_rows:", data_rows, "proved:", proved, "col_dist:", dict(col_dist))
print("duplicate target entries:", {e: c for e, c in entry_count.items() if e in ENTRIES and c != 1})

state = {"coverage": cov, "panel": pan,
         "target_rows": {e: rows[e] for e in ENTRIES if e in rows},
         "baseline": {"data_rows": data_rows, "proved": proved,
                      "col_dist": {str(k): v for k, v in col_dist.items()}}}
with open(os.path.join(OUT, "before_state.json"), "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=1)
print("wrote before_state.json")
