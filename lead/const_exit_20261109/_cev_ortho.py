# -*- coding: utf-8 -*-
"""_cev_ortho.py -- step ⑤: is the kd detector's verdict orthogonal to
exit-constantness?  Pure static check + cross-tab, no gate re-runs."""
import ast
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.dont_write_bytecode = True
ROOT = r"D:/Project/ra2-campaign-forge"
WD = os.path.join(ROOT, "lead", "const_exit_20261109")
sys.path.insert(0, WD)
os.chdir(ROOT)
from _cev_classifier import analyse  # noqa: E402

kd = json.load(open("lead/k1bit_detect_20261109/_kd_detect_out.json", encoding="utf-8"))
src = open("lead/k1bit_detect_20261109/_kd_detect.py", encoding="utf-8").read()
tree = ast.parse(src)

# (a) Does the detector's analyse() mention any of the exit-constant concepts?
# Look at the whole source for exit-related tokens and at the verdict block.
exit_tokens = ["sys.exit", "SystemExit", "CONSTANT_EXIT", "attainable",
               "exit_status", "exit_code", "returncode"]
hits = {t: [i + 1 for i, l in enumerate(src.split("\n")) if t in l] for t in exit_tokens}

# verdict lines are 474-487; check what variables they read
verdict_src = "\n".join(src.split("\n")[473:487])
verdict_vars = sorted(set(re.findall(r"\b[a-zA-Z_]\w*\b", verdict_src)))

# (b) Cross-tab: for every kd row (173) resolved to disk, compute MY exit class.
cross = defaultdict(Counter)
per_verdict_examples = defaultdict(list)
for r in kd["rows"]:
    rel = r["rel"]
    if not os.path.exists(rel):
        cross[r["verdict"]]["MISSING_FILE"] += 1
        continue
    try:
        cls = analyse(rel)["cls"]
    except Exception as ex:
        cls = "ANALYSE_ERROR:" + type(ex).__name__
    cross[r["verdict"]][cls] += 1
    if len(per_verdict_examples[(r["verdict"], cls)]) < 6:
        per_verdict_examples[(r["verdict"], cls)].append(rel)

focus = ["lead/refsync_scope_20261109/_rs_carrier_scan.py",
         "lead/goal1_a8_fix_20261022/VERIFY_A8.py",
         "lead/masking_effect_20261109/_me_auditcheck.py",
         "lead/stale_pass_20261109/_sp_sandbox/d29/_w_d29_A.py"]
focus_rows = []
for rel in focus:
    a = analyse(rel)
    kdrow = next((r for r in kd["rows"] if r["rel"] == rel), None)
    focus_rows.append(dict(rel=rel, my_cls=a["cls"], statuses=a["statuses"],
                           kd_verdict=(kdrow or {}).get("verdict", "NOT_IN_KD_173"),
                           kd_onebit=(kdrow or {}).get("onebit_exit"),
                           sites=[(s["line"], s["kind"], s["expr"]) for s in a["sites"]]))

out = dict(detector_source="lead/k1bit_detect_20261109/_kd_detect.py",
           detector_nlines=len(src.split("\n")),
           exit_token_hits=hits,
           verdict_block_vars=verdict_vars,
           cross_tab={k: dict(v) for k, v in cross.items()},
           focus_files=focus_rows,
           counterexamples=[
               dict(rel=x["rel"], kd_verdict=x["kd_verdict"], my_cls=x["my_cls"])
               for x in focus_rows])
with open(os.path.join(WD, "_cev_ortho_out.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("detector exit-token hits:", {k: v for k, v in hits.items() if v})
print("verdict block identifiers:", verdict_vars)
print("\ncross-tab kd verdict x my exit class (173 census files):")
for v in sorted(cross):
    print("  %-20s %s" % (v, dict(cross[v])))
print("\nfocus files:")
for x in focus_rows:
    print("  %-70s kd=%-18s my=%-18s sts=%s" %
          (x["rel"], x["kd_verdict"], x["my_cls"], x["statuses"]))
