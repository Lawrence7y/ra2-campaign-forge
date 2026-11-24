# -*- coding: utf-8 -*-
"""_dt_leak.py -- independent 'missed A-level' check.

Enumerates every check_*.py / *_scan.py basename appearing in the two ledgers,
maps each to the detector's 173-row verdict (and to the --one carrier result),
and reports any registered production gate not in the CONFIRMED 40.
Read-only outside the write domain.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
WD = ROOT / "lead/detect_triage_20261109"
kd = json.loads((ROOT / "lead/k1bit_detect_20261109/_kd_detect_out.json")
                .read_text(encoding="utf-8"))
cf = json.loads((ROOT / "lead/check_family_20261109/_cf_detect_out.json")
                .read_text(encoding="utf-8"))
scope = json.loads((WD / "_dt_scope_out.json").read_text(encoding="utf-8"))
repro = json.loads((WD / "_dt_repro_out.json").read_text(encoding="utf-8"))

ledgers = [ROOT / "lead/PENDING_DECISIONS.md",
           ROOT / "lead/GOAL_THREE_TARGETS_20261018.md"]
text = "\n".join(p.read_text(encoding="utf-8") for p in ledgers)

names = sorted(set(re.findall(r"[A-Za-z0-9_]+\.py", text)))
byrel = {r["rel"]: r for r in kd["rows"]}
confirmed = set(repro["kd"]["confirmed"])

rows = []
for nm in names:
    if not (nm.startswith("check_") or "scan" in nm):
        continue
    matches = [r for r in kd["rows"] if r["rel"].endswith("/" + nm)]
    v = {}
    for r in matches:
        v[r["rel"]] = r["verdict"]
    lines = []
    for p in ledgers:
        for i, s in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if nm in s and ("exit=0" in s or "PASS" in s or "门禁" in s):
                lines.append("%s:%d" % (p.name, i))
    rows.append(dict(name=nm, verdicts=v,
                     n_in_census=len(matches),
                     in_confirmed_40=any(r["rel"] in confirmed for r in matches),
                     ledger_pass_lines=lines))

# any production-registered gate NOT confirmed?
reg_gates = [r for r in rows if r["ledger_pass_lines"]]
missed = [r for r in reg_gates if not r["in_confirmed_40"]]

# also check the deliverable-only carrier
carrier = scope["carrier_one"]
out = dict(
    n_names_in_ledgers=len(names),
    n_candidate_gates=len(rows),
    rows=rows,
    registered_gates=reg_gates,
    registered_not_confirmed=missed,
    carrier_one=dict(rel=carrier["rel"], verdict=carrier["verdict"],
                     in_confirmed_40=carrier["in_confirmed_40"],
                     in_kd_rows_173=carrier["in_kd_rows_173"],
                     deliverable_citations=[
                         "lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md:251",
                         "lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md:252",
                         "lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md:253"]),
    cf_suspect=cf["suspect"],
    kd_suspect=kd["suspect"],
)
(WD / "_dt_leak_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
print("names in ledgers:", len(names), "candidate gates:", len(rows))
print("=== registered gates (basename + ledger PASS line) ===")
for r in reg_gates:
    print(" ", r["name"], r["ledger_pass_lines"],
          "verdicts=", r["verdicts"], "in40=", r["in_confirmed_40"])
print("=== registered but NOT in CONFIRMED 40 ===")
for r in missed:
    print(" ", r["name"], r["verdicts"], r["ledger_pass_lines"])
print("=== carrier one-off ===")
print(json.dumps(out["carrier_one"], ensure_ascii=False))
print("WROTE", (WD / "_dt_leak_out.json").as_posix())
