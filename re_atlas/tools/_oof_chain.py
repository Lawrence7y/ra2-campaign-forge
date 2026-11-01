# -*- coding: utf-8 -*-
"""OOF freeze-chain reconciliation (independent of C report).

  (a) suite CASES literal (AST-extracted, NOT executed) vs manifest (case,mut,red)
  (b) run1 log vs manifest: case set, EXACT counts, tally fields, EXIT=0
  (c) --dump vs CHAIN literal (already in _oof_recon.py C6)
  (d) calibration output embedded JSON vs manifest
"""
import ast
import json
import re
import sys

ROOT = r"D:\Project\ra2-campaign-forge"


def literals(path):
    src = open(path, "r", encoding="utf-8").read()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "CASES":
                    return ast.literal_eval(node.value)
    raise SystemExit("CASES not found in " + path)


def norm_red(r):
    return sorted(r)


print("== (a) suite CASES literal vs manifest ==")
for tag, suitep, manp in (
        ("R-061", ROOT + r"\re_atlas\tools\mutate_r061_gate.py", ROOT + r"\out\_r061_freeze5.json"),
        ("R-062", ROOT + r"\re_atlas\tools\mutate_r062_gate.py", ROOT + r"\out\_r062_freeze.json")):
    C = literals(suitep)
    M = json.load(open(manp))
    mc = M["cases"] if isinstance(M.get("cases"), list) else M["rows"]
    print("  %s: suite cases=%d manifest cases=%d" % (tag, len(C), len(mc)))
    def norm_mut(m):
        return {int(k, 16) if isinstance(k, str) else int(k): int(v)
                for k, v in m.items()}
    md = {}
    for row in mc:
        md[row["case"]] = (norm_mut(row["mut"]), norm_red(row["red"]))
    sd = {}
    for name, mut, red in C:
        sd[name] = (norm_mut(mut), norm_red(red))
    print("    case-name sets equal:", set(sd) == set(md))
    probs = 0
    for k in sorted(set(sd) & set(md)):
        if sd[k][0] != md[k][0]:
            probs += 1
            print("    MUT DIFF", k, sd[k][0], md[k][0])
        if sd[k][1] != md[k][1]:
            probs += 1
            print("    RED DIFF", k, sd[k][1], md[k][1])
    print("    three-field problems:", probs)
    print("    total mutation bytes:", sum(len(m) for m in sd.values()))

print("\n== (b) run1 log vs manifest ==")
for tag, runp, manp in (
        ("R-061", ROOT + r"\out\_r061_freeze_run1.txt", ROOT + r"\out\_r061_freeze5.json"),
        ("R-062", ROOT + r"\out\_r062_freeze_run1.txt", ROOT + r"\out\_r062_freeze.json")):
    log = open(runp, "r", encoding="utf-8", errors="replace").read()
    M = json.load(open(manp))
    names_in_log = re.findall(r"^(\S+)\s+(?:[\d.]+s\s+)?EXACT", log, re.M)
    man_names = [c["case"] for c in (M["cases"] if isinstance(M.get("cases"), list) else M["rows"])]
    exact_n = len(names_in_log)
    print("  %s: EXACT lines=%d manifest cases=%d  set-equal=%s" %
          (tag, exact_n, len(man_names), set(names_in_log) == set(man_names)))
    print("    bracket-consistency:", all(("'%s'" % n) in log for n in man_names) or "n/a")
    for key in ("survived", "exc", "splice-mismatch", "full-mismatch"):
        pass
    m = re.search(r"cases=(\d+) exact=(\d+) survived=(\d+) exc=(\d+) splice-mismatch=(\d+) full-mismatch=(\d+)", log)
    print("    tally line:", m.group(0) if m else "MISSING")
    m2 = re.search(r"labels=(\d+) covered-by-literals=(\d+) uncovered=(\d+) phantom-expectations=(\d+)", log)
    print("    label line:", m2.group(0) if m2 else "MISSING")
    print("    EXIT=0 present:", "EXIT=0" in log.splitlines()[-1] or "EXIT=0" in log)

print("\n== (d) calibration embedded JSON vs manifest ==")
import os
for tag, calp, manp in (
        ("R-061", ROOT + r"\out\_r061_mut_calib5.txt", ROOT + r"\out\_r061_freeze5.json"),
        ("R-062", ROOT + r"\out\_r062_mut_calib2.txt", ROOT + r"\out\_r062_freeze.json")):
    if not os.path.exists(calp):
        print("  %s: %s MISSING" % (tag, calp))
        continue
    txt = open(calp, "r", encoding="utf-8", errors="replace").read()
    i = txt.find("JSON_MANIFEST")
    print("  %s: calib %d B, JSON_MANIFEST marker at %s" % (tag, len(txt), i))
    if i >= 0:
        j = txt.find("{", i)
        # find matching brace
        depth = 0
        for k in range(j, len(txt)):
            if txt[k] == "{":
                depth += 1
            elif txt[k] == "}":
                depth -= 1
                if depth == 0:
                    blob = txt[j:k + 1]
                    break
        try:
            cm = json.loads(blob)
            mm = json.load(open(manp))
            same = json.dumps(cm, sort_keys=True) == json.dumps(mm, sort_keys=True)
            print("    embedded parse OK; byte-identical to manifest:", same)
            if not same:
                ks = set(cm) | set(mm)
                for k2 in sorted(ks):
                    if cm.get(k2) != mm.get(k2):
                        print("      field differs:", k2, repr(cm.get(k2))[:90], "vs", repr(mm.get(k2))[:90])
        except Exception as ex:
            print("    parse failed:", ex)
