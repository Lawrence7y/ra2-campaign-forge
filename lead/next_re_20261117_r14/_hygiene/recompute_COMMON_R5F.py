#!/usr/bin/env python3
"""COMMON-R5F one-pass disk recomputation for R14_COMMON.md sections 9.0/11."""
from __future__ import annotations
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
COVERAGE = BASE / "COVERAGE" / "coverage.tsv"
ATLAS = Path("D:/Project/ra2-campaign-forge/lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv")
OUT = Path(__file__).with_suffix(".json")
TZ = timezone(timedelta(hours=8), "Asia/Shanghai")

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_tsv(path: Path):
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(text.splitlines(), delimiter="\t")
    return raw, list(reader)

snapshot_at = datetime.now(TZ).replace(microsecond=0)
cov_raw, cov_rows = read_tsv(COVERAGE)
atlas_raw, atlas_rows = read_tsv(ATLAS)
read_done_at = datetime.now(TZ).replace(microsecond=0)

atlas_entries = {str(r["entry"]).strip().upper() for r in atlas_rows if str(r.get("entry", "")).strip()}
grade_counts = Counter(str(r.get("grade", "")).strip() for r in cov_rows)

class_sub = re.compile(r"::SUB_[0-9A-F]{8}$", re.I)
slot_name = re.compile(r"::(?:V?SLOT)[0-9]+$", re.I)

def named_flags(name: str) -> tuple[bool, bool, bool]:
    n = (name or "").strip()
    u = n.upper()
    named_l = bool(n) and not u.startswith("SUB_")
    named_s_r14 = named_l and not bool(class_sub.search(u))
    named_s_strict = named_s_r14 and not bool(slot_name.search(u))
    return named_l, named_s_r14, named_s_strict

def subsystem_metrics(sub: str) -> dict:
    rows = [
        r for r in cov_rows
        if str(r.get("subsystem", "")).strip().upper() == sub.upper()
        and str(r.get("entry", "")).strip().upper() in atlas_entries
    ]
    flags = [named_flags(str(r.get("name", ""))) for r in rows]
    proved = sum(1 for r in rows if str(r.get("grade", "")).strip() == "[已证]")
    n = len(rows)
    return {
        "atlas_n": n,
        "named_L": sum(f[0] for f in flags),
        "named_S_R14": sum(f[1] for f in flags),
        "named_S_strict": sum(f[2] for f in flags),
        "proved": proved,
    }

subs = {f"S{i:02d}": subsystem_metrics(f"S{i:02d}") for i in range(1, 23)}
result = {
    "snapshot_at": snapshot_at.isoformat(),
    "read_done_at": read_done_at.isoformat(),
    "inputs": {
        "coverage.tsv": {"path": str(COVERAGE), "bytes": len(cov_raw), "sha256": sha256(cov_raw)},
        "function_atlas.tsv": {"path": str(ATLAS), "bytes": len(atlas_raw), "sha256": sha256(atlas_raw)},
    },
    "definitions": {
        "join": "coverage.entry uppercased == function_atlas.entry uppercased; one coverage row counted once",
        "named_L": "name non-empty and name.upper() does not start with SUB_",
        "named_S_R14": "named_L minus Class::sub_XXXXXXXX (regex ::SUB_[0-9A-F]{8}$)",
        "named_S_strict": "named_S_R14 minus Class::slotN / Class::vslotN (regex ::(?:V?SLOT)[0-9]+$)",
        "proved": "grade == [已证] within the same coverage∩atlas rows",
        "denominator": "atlas_n = coverage∩atlas row count for the subsystem",
    },
    "whole_table": {
        "coverage_data_rows": len(cov_rows),
        "atlas_data_rows": len(atlas_rows),
        "coverage_grades": dict(sorted(grade_counts.items())),
    },
    "S10": subs["S10"],
    "S11": subs["S11"],
    "all_subsystems": subs,
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: result[k] for k in ("snapshot_at", "read_done_at", "inputs", "whole_table", "S10", "S11")}, ensure_ascii=False, indent=2))
print("output", OUT)
