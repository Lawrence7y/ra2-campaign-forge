#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB-INDEX independent verifier. Reads ONLY the generated index + ledger (read-only)
and recomputes the 3 core numbers. Does not import build_index.py (no shared code),
so an auditor can run it standalone:

    python verify_index.py

Expected (2026-11-17, snapshot=截止 §973): routes=433 / sxx=292 / cross=141 / dep=21
                        cells ✅7 ⚠️48 ❌75 —2 (total 132)
                        missing Sxx KB files = 0 (=> 22 subsystems without KB)
                        §737 must be S13, §821 must be S02 (audit fix)
"""
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
INDEX = ROOT / "re_atlas" / "kb" / "00_INDEX.md"
KBDIR = ROOT / "re_atlas" / "kb"
LEDGER = ROOT / "lead" / "GOAL_THREE_TARGETS_20261018.md"

SNAPSHOT = HERE / "ledger_sections.tsv"

text = INDEX.read_text(encoding="utf-8-sig")
lines = text.splitlines()

# 1) frozen snapshot count (433 sections through §973; captured after §973 ledgered)
snapshot_secs = [l for l in SNAPSHOT.read_text(encoding="utf-8-sig").splitlines()[1:] if "\t" in l]
# live ledger count for provenance only (append-only; may grow past §973 later)
ledger_secs = [l for l in LEDGER.read_text(encoding="utf-8-sig").splitlines()
               if re.match(r"^## §\d+", l)]

# 2) routing table rows in §C
routes = [l for l in lines if re.match(r"^\| §\d", l)]
cross = 0
for l in routes:
    cells = l.split("|")
    if len(cells) > 3 and cells[3].strip() == "跨子系统":
        cross += 1
dep = sum(1 for l in routes if "已作废" in l)

# 2b) audit-fix checks: §737 -> S13, §821 -> S02 (must NOT be 跨子系统)
r737 = next((l for l in routes if l.startswith("| §737 ")), "")
r821 = next((l for l in routes if l.startswith("| §821 ")), "")
fix737 = ",S13" in r737 or r737.split("|")[3].strip() == "S13"
fix821 = ",S02" in r821 or r821.split("|")[3].strip() == "S02"

# 3) DoD matrix cells: 22 rows starting '| **SNN** |'
matrix = "\n".join(l for l in lines if re.match(r"^\| \*\*S\d\d\*\* \|", l))
counts = {s: len(re.findall(re.escape(s), matrix)) for s in ("✅", "⚠️", "❌", "—")}

# 4) no Sxx KB file created
sxx_files = list(KBDIR.glob("S??_*.md"))

print(f"frozen snapshot sections    : {len(snapshot_secs)}  (live ledger now {len(ledger_secs)})")
print(f"§C route rows              : {len(routes)}")
print(f"  routed to ≥1 Sxx         : {len(routes) - cross}")
print(f"  cross-only               : {cross}")
print(f"  已作废 flags             : {dep}")
print(f"§B cells ✅/⚠️/❌/—     : {counts['✅']}/{counts['⚠️']}/{counts['❌']}/{counts['—']} (total {sum(counts.values())})")
missing = [f"S{i:02d}" for i in range(1, 23) if not list(KBDIR.glob(f"S{i:02d}_*.md"))]
print(f"KB\\Sxx_*.md files          : {len(sxx_files)}  => subsystems missing KB = {len(missing)} ({','.join(missing)})")

print(f"§737 -> S13 : {fix737}  | §821 -> S02 : {fix821}")

ok = (len(snapshot_secs) == 433 and len(routes) == 433 and len(routes) - cross == 292
      and cross == 141 and dep == 21 and fix737 and fix821
      and counts == {"✅": 7, "⚠️": 48, "❌": 75, "—": 2} and len(missing) == 22)
print("VERDICT:", "PASS" if ok else "FAIL")
