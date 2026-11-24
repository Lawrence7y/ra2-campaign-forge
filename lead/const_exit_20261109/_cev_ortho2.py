# -*- coding: utf-8 -*-
"""_cev_ortho2.py -- step ⑤ strict: run the kd detector's PURE analyse()
function (no main(), no gate re-run, no file writes) on the 4 named focus
files, cross-tab its verdict against MY exit classification, and check whether
the detector's verdict is a function of exit-constantness.

This calls a pure AST analysis function from a read-only protected script.  It
does NOT execute a checked gate or a checked script.
"""
import ast
import importlib.util
import json
import os
import sys

sys.dont_write_bytecode = True
ROOT = r"D:/Project/ra2-campaign-forge"
WD = os.path.join(ROOT, "lead", "const_exit_20261109")
sys.path.insert(0, WD)
os.chdir(ROOT)
from _cev_classifier import analyse as my_analyse  # noqa: E402

KD = "lead/k1bit_detect_20261109/_kd_detect.py"
spec = importlib.util.spec_from_file_location("_cev_kdmod", os.path.join(ROOT, KD))
kdmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kdmod)          # main() is guarded by __name__

FOCUS = [
    "lead/goal1_a8_fix_20261022/VERIFY_A8.py",
    "lead/refsync_scope_20261109/_rs_carrier_scan.py",
    "lead/masking_effect_20261109/_me_auditcheck.py",
    "lead/stale_pass_20261109/_sp_sandbox/d29/_w_d29_A.py",
    "lead/d27_ruling_20261106/check_d27.py",
    "lead/d28_ruling_20261106/check_d28.py",
    "lead/d29_ruling_20261106/check_d29.py",
    "lead/d30_ruling_20261106/check_d30.py",
]

rows = []
for rel in FOCUS:
    raw = open(rel, "rb").read()
    k = kdmod.analyse(rel, raw)          # pure AST analysis
    m = my_analyse(rel)
    rows.append(dict(rel=rel, kd_verdict=k["verdict"], kd_has_k=k["has_k"],
                     kd_onebit_exit=k["onebit_exit"], kd_onebit=k["output"]["onebit"],
                     kd_n_accum=k["n_accum"], kd_n_real_collapse=k["n_real_collapse"],
                     kd_attribution=k["attribution"],
                     my_cls=m["cls"], my_statuses=m["statuses"],
                     my_data=m["any_data"], my_sites=[(s["line"], s["kind"], s["expr"])
                                                      for s in m["sites"]]))

# cross-tab over the FULL 173 census + the 4 out-of-census focus files
kdout = json.load(open("lead/k1bit_detect_20261109/_kd_detect_out.json", encoding="utf-8"))
from collections import Counter, defaultdict
cross = defaultdict(Counter)
for r in kdout["rows"]:
    rel = r["rel"]
    if not os.path.exists(rel):
        cross[r["verdict"]]["MISSING"] += 1
        continue
    try:
        c = my_analyse(rel)["cls"]
    except Exception as ex:
        c = "ERR:" + type(ex).__name__
    cross[r["verdict"]][c] += 1

out = dict(detector_source=KD,
           note="kdmod.analyse() is a pure AST function; main() NOT called; no checked gate executed",
           focus_rows=rows,
           cross_tab_173={k: dict(v) for k, v in cross.items()})
with open(os.path.join(WD, "_cev_ortho2_out.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

for r in rows:
    print("%-72s kd=%-18s onebit=%-5s n_accum=%-3d | my=%-18s sts=%s" %
          (r["rel"], r["kd_verdict"], r["kd_onebit_exit"], r["kd_n_accum"],
           r["my_cls"], r["my_statuses"]))
print("\ncross-tab (173 census files) kd verdict x my exit class:")
for k in sorted(cross):
    print("  %-20s %s" % (k, dict(cross[k])))
