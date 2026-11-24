# -*- coding: utf-8 -*-
"""_oev_4.py -- V1 earliest DB mention + full ctime pattern library-wide stat.
Read-only over forbidden domains; writes _oev_4_out.json only."""
from __future__ import annotations
import json, os, sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "ordering_evidence_20261109"
TZ = timezone(timedelta(hours=8))
def loc(ms): return datetime.fromtimestamp(ms / 1000, TZ).isoformat()
DB = "C:/Users/Administrator/.zcode/cli/db/db.sqlite"
con = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=10)
OUT = {}
for rid in [619829, 620123, 635245, 635250, 635535, 635544, 635552]:
    r = con.execute("select rowid,time_created,data from part where rowid=?", (rid,)).fetchone()
    if not r:
        OUT[rid] = {"exists": False}; continue
    d = json.loads(r[2]); inp = d.get("state", {}).get("input", {})
    OUT[rid] = {"exists": True, "local": loc(r[1]), "tool": d.get("tool"),
                "file_path": inp.get("file_path", "")[:170],
                "command": inp.get("command", "")[:220],
                "content_has_gp_regression_out": "_gp_regression_out.json" in inp.get("content", ""),
                "content_head": inp.get("content", "")[:200].replace("\n", " "),
                "output_tail": d.get("state", {}).get("output", "")[-260:].replace("\n", " ")}
con.close()
# distribution of mtime-ctime across lead/, plus how many are > 328.701807
buckets = {"gt_0": 0, "gt_60": 0, "gt_300": 0, "gt_328_7": 0, "total": 0}
seal_like = []
for dirpath, dirnames, filenames in os.walk(ROOT / "lead"):
    for fn in filenames:
        p = Path(dirpath) / fn
        try: st = p.stat()
        except OSError: continue
        buckets["total"] += 1
        d = st.st_mtime - st.st_ctime
        if d > 0: buckets["gt_0"] += 1
        if d > 60: buckets["gt_60"] += 1
        if d > 300: buckets["gt_300"] += 1
        if d > 328.701807:
            buckets["gt_328_7"] += 1
            if len(seal_like) < 8:
                seal_like.append({"rel": str(p.relative_to(ROOT)).replace("\\", "/"),
                                  "delta": round(d, 3)})
OUT["mtime_minus_ctime_distribution"] = buckets
OUT["files_exceeding_seal_delta_examples"] = seal_like
OUT["seal_delta_is_unusual"] = buckets["gt_328_7"] <= 5
with (WDIR / "_oev_4_out.json").open("w", encoding="utf-8") as f:
    json.dump(OUT, f, ensure_ascii=False, indent=2)
print("=== _oev_4.py ===")
print(json.dumps(OUT, ensure_ascii=False, indent=1))
print("WROTE _oev_4_out.json")
