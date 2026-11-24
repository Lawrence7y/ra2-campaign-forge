# -*- coding: utf-8 -*-
"""_oc_ledger_scan.py : independent read-only scan of both ledgers for the four gate names."""
import json, os

ROOT = r"D:\Project\ra2-campaign-forge"
FILES = ["lead/PENDING_DECISIONS.md", "lead/GOAL_THREE_TARGETS_20261018.md"]
NAMES = ["check_d27.py", "check_d28.py", "check_d29.py", "check_d30.py",
         "_rs_carrier_scan.py", "carrier_scan", "REFSYNC_SCOPE_FIX"]

out = {}
for rel in FILES:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    lines = open(p, encoding="utf-8").read().splitlines()
    per = {}
    for nm in NAMES:
        per[nm] = [i + 1 for i, L in enumerate(lines) if nm in L]
    gate_lines = [i + 1 for i, L in enumerate(lines)
                  if ("门禁" in L and "exit=0" in L)]
    out[rel] = {"lines_splitlines": len(lines),
                "per_name": per,
                "gate_exit0_lines": gate_lines}
print(json.dumps(out, ensure_ascii=False, indent=2))
