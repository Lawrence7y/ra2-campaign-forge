#!/usr/bin/env python3
"""Find AITrigger/Rules INI key strings and atlas-independent xrefs."""
from __future__ import annotations
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import wbase

OUT = Path(__file__).resolve().parents[1] / "EVIDENCE"
TERMS = [
    "AITrigger", "AITriggers", "ConditionType", "Comparator", "Amount",
    "Team1", "Team2", "InitialWeight", "MinimumWeight", "MaximumWeight",
    "Probability", "AITriggerControl", "SuccessWeightDelta", "FailureWeightDelta",
    "TrackRecordCoefficient", "BuildSpeed", "Credits", "Refinery", "Harvester",
]

p = wbase.pe()
data = p.__data__
hits = []
for m in re.finditer(rb"[ -~]{4,}", data):
    s = m.group().decode("ascii", "replace")
    if any(t.lower() in s.lower() for t in TERMS):
        try:
            va = wbase.off_to_va(m.start())
        except ValueError:
            continue
        hits.append((va, m.start(), s))

lines = [f"string_hits={len(hits)} terms={','.join(TERMS)}"]
for va, off, s in sorted(hits):
    xrefs = wbase.scan_imm32_refs(va)
    lines.append(f"\nVA={va:#08x} OFF={off:#08x} STR={s!r} IMM32_XREFS={len(xrefs)}")
    for site, text in xrefs:
        lines.append(f"  {site:08X}  {text}")

(OUT / "E08_ai_ini_key_xrefs.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("wrote", OUT / "E08_ai_ini_key_xrefs.txt", "hits", len(hits))
