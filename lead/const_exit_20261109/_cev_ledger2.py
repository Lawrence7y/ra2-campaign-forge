# -*- coding: utf-8 -*-
"""_cev_ledger2.py -- supplementary ledger checks:
  (1) exact raw count of marked lines / basename occurrences
  (2) all 18 CONSTANT_EXIT basenames searched across the FULL two ledgers,
      reporting every line where they appear (marked or not).
  (3) all 263 NO_EXIT basenames likewise -> per-line list.
"""
import json
import os
import re
import sys
from collections import defaultdict

sys.dont_write_bytecode = True
ROOT = r"D:/Project/ra2-campaign-forge"
WD = os.path.join(ROOT, "lead", "const_exit_20261109")
os.chdir(ROOT)
LEDGERS = ["lead/PENDING_DECISIONS.md", "lead/GOAL_THREE_TARGETS_20261018.md"]
PAT_PY = re.compile(r"([A-Za-z0-9_./\-]+\.py)")
MARK = re.compile(r"PASS|exit\s*=\s*0|EXIT=0|SELF_TEST")

mybatch = json.load(open(os.path.join(WD, "_cev_batch_out.json"), encoding="utf-8"))
const_bs = sorted({r["basename"] for r in mybatch["rows"] if r["cls"] == "CONSTANT_EXIT"})
noexit_bs = sorted({r["basename"] for r in mybatch["rows"] if r["cls"] == "NO_EXIT_AT_ALL"})
print("n_const_basenames", len(const_bs), "n_noexit_basenames", len(noexit_bs))

raw_marked, raw_occ, marked_with_py = 0, 0, 0
appear = defaultdict(list)   # (ledger, cls) -> list of (line, basename, text)
for name in LEDGERS:
    t = open(name, encoding="utf-8", errors="replace").read()
    for i, l in enumerate(t.split("\n"), 1):
        if MARK.search(l):
            raw_marked += 1
            bs = [os.path.basename(m.group(1).replace("\\", "/")) for m in PAT_PY.finditer(l)]
            raw_occ += len(bs)
            if bs:
                marked_with_py += 1
        # full-line scan (marked or not)
        for m in PAT_PY.finditer(l):
            b = os.path.basename(m.group(1).replace("\\", "/"))
            if b in const_bs:
                appear[(name, "CONSTANT_EXIT")].append((i, b, l.strip()[:200]))
            elif b in noexit_bs:
                appear[(name, "NO_EXIT_AT_ALL")].append((i, b, l.strip()[:200]))

print("raw_marked_lines", raw_marked, "raw_basename_occurrences", raw_occ,
      "marked_lines_with_py", marked_with_py)
for key in sorted(appear):
    print("\n==", key[0], key[1], "n_lines", len(appear[key]))
    for ln, b, txt in appear[key]:
        print("  %5d | %-28s | %s" % (ln, b, txt))

out = dict(n_const_basenames=len(const_bs), const_basenames=const_bs,
           n_noexit_basenames=len(noexit_bs),
           raw_marked_lines=raw_marked, raw_basename_occurrences=raw_occ,
           marked_lines_with_py=marked_with_py,
           appearances={"%s|%s" % k: v for k, v in appear.items()})
with open(os.path.join(WD, "_cev_ledger2_out.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
