from __future__ import annotations
import os, time
from collections import Counter
from datetime import datetime, timezone, timedelta
from k14_image import EXE, COV, ATL, sha256, now

def rows(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = [x.rstrip("\r\n") for x in f if x.strip()]
    # This coverage snapshot has a comma header but tab rows. Normalize only header shape.
    out = []
    for ln in lines:
        cols = ln.split("\t")
        if len(cols) < 8:
            cols = ln.split(",")
        out.append(cols)
    return out[0], out[1:]

ch, cr = rows(COV)
ah, ar = rows(ATL)
atlas = {r[0].lower() for r in ar if r}
s10 = [r for r in cr if len(r) >= 8 and r[1] == "S10"]
s10_in = [r for r in s10 if r[0].lower() in atlas]
s10_out = [r for r in s10 if r[0].lower() not in atlas]
grades = Counter(r[4] for r in s10_in)  # grade is fifth column only
named = [r for r in s10_in if not r[2].lower().startswith("sub_")]
proved = grades.get("[已证]", 0)
threshold = 263
lines = [
    "S10_K14 BASELINE (fresh read, independent script)",
    f"TIME={now()}",
    f"EXE={EXE} size={os.path.getsize(EXE)} sha={sha256(EXE)}",
    f"COV={COV} size={os.path.getsize(COV)} sha={sha256(COV)} mtime={datetime.fromtimestamp(os.path.getmtime(COV), timezone(timedelta(hours=8))).isoformat(timespec='microseconds')}",
    f"ATL={ATL} size={os.path.getsize(ATL)} sha={sha256(ATL)}",
    f"COV_ROWS={len(cr)} COV_HEADER={ch}",
    f"ATL_ROWS={len(ar)} ATL_HEADER={ah}",
    f"S10_ROWS={len(s10)} S10_IN_ATLAS={len(s10_in)} S10_OUTSIDE={len(s10_out)}",
    f"GRADE_5TH_COL={dict(grades)}",
    f"PROVED={proved} PROVED_PCT={proved/len(s10_in)*100:.4f} THRESHOLD={threshold} GAP={threshold-proved}",
    f"NAMED_L={len(named)} NAMED_L_PCT={len(named)/len(s10_in)*100:.4f}",
    f"S10_OUTSIDE_ENTRIES={[r[0] for r in s10_out]}",
    "GRADE_SOURCE=coverage.tsv field index 4 only; keys normalized with .lower()",
]
print("\n".join(lines))
open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K14\EVIDENCE\BASELINE.txt","w",encoding="utf-8").write("\n".join(lines)+"\n")
