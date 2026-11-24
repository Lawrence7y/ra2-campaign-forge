#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate BEFORE_AFTER.txt from the on-disk backup and current PANEL.md."""
import sys
from pathlib import Path
ART = Path(__file__).resolve().parent
sys.path.insert(0, str(ART))
import apply_edit as ae

before = ae.BACKUP.read_text(encoding="utf-8").split("\n")
after = (ae.ART.parent / "COVERAGE" / "PANEL.md").read_text(encoding="utf-8").split("\n")

out = []
out.append("R16-FIX-PANEL-M86 :: M86 block BEFORE / AFTER")
out.append("=" * 60)
out.append("")
out.append("--- BEFORE : COVERAGE/PANEL.md lines 214..221 (8 lines) ---")
for i, ln in enumerate(before[213:221], start=214):
    out.append("%3d | %s" % (i, ln))
out.append("")
out.append("--- AFTER : COVERAGE/PANEL.md lines 214..223 (10 lines) ---")
for i, ln in enumerate(after[213:223], start=214):
    out.append("%3d | %s" % (i, ln))
out.append("")
out.append("=" * 60)
out.append("Verbatim before/after of the two edited/inserted lines (no line numbers):")
out.append("")
out.append("[BEFORE line 219]")
out.append(before[218])
out.append("[AFTER line 219]")
out.append(after[218])
out.append("[AFTER line 220]  (newly inserted: +15 vs +9 disclosure)")
out.append(after[219])
out.append("[AFTER line 221]  (newly inserted: 口径 A heterogeneity disclosure)")
out.append(after[220])
out.append("[BEFORE line 220 -> AFTER line 222]  (unchanged)")
out.append(after[221])
out.append("[BEFORE line 221 -> AFTER line 223]  (unchanged)")
out.append(after[222])

(ART / "BEFORE_AFTER.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("WROTE", ART / "BEFORE_AFTER.txt")
