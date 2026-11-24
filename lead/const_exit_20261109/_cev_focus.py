# -*- coding: utf-8 -*-
"""_cev_focus.py -- step ③ focus check: 4 production gates + 4 K1BIT-cited.

For each file: my classifier's mechanical verdict, the orchestrator's
mechanical verdict (from the archived raw output / kd census), the agent-final
verdict, and the human/AST evidence (own return statements / exit sites with
file:line).  Also answers: was any BRANCHED gate misjudged as CONSTANT_EXIT?
"""
import ast
import json
import os
import sys
from collections import Counter

sys.dont_write_bytecode = True
ROOT = r"D:/Project/ra2-campaign-forge"
WD = os.path.join(ROOT, "lead", "const_exit_20261109")
sys.path.insert(0, WD)
os.chdir(ROOT)
from _cev_classifier import analyse, func_defs, own_returns, collect_sites  # noqa: E402

GATES = [
    "lead/d27_ruling_20261106/check_d27.py",
    "lead/d28_ruling_20261106/check_d28.py",
    "lead/d29_ruling_20261106/check_d29.py",
    "lead/d30_ruling_20261106/check_d30.py",
]
K1BIT = [
    "lead/refsync_scope_20261109/_rs_carrier_scan.py",
    "lead/goal1_a8_fix_20261022/VERIFY_A8.py",
    "lead/masking_effect_20261109/_me_auditcheck.py",
    "lead/stale_pass_20261109/_sp_sandbox/d29/_w_d29_A.py",
]

orch_raw = json.load(open(os.path.join(WD, "_ce_orchestrator_raw.json"), encoding="utf-8"))
orch_cls = {}
for r in orch_raw["const_or_noexit"]:
    orch_cls[r["rel"]] = r["cls"]
for r in orch_raw["conditional"]:
    orch_cls[r["rel"]] = "CONDITIONAL_EXIT"
agent = json.load(open(os.path.join(WD, "_ce_final_out.json"), encoding="utf-8"))
agent_cls = {r["rel"]: r["cls"] for r in agent["rows"]}
mybatch = json.load(open(os.path.join(WD, "_cev_batch_out.json"), encoding="utf-8"))
my_cls = {r["rel"]: r["cls"] for r in mybatch["rows"]}
kd = json.load(open("lead/k1bit_detect_20261109/_kd_detect_out.json", encoding="utf-8"))
kd_cls = {r["rel"]: r["verdict"] for r in kd["rows"]}
census = {os.path.basename(r["rel"]) for r in kd["rows"]}


def human_evidence(rel):
    raw = open(rel, "rb").read()
    tree = ast.parse(raw.decode("utf-8-sig", errors="replace"))
    fdefs = func_defs(tree)
    sites, _ = collect_sites(tree)
    ret = []
    for name, fns in fdefs.items():
        for fn in fns:
            rs = own_returns(fn)
            ret.append(dict(func=name, line=fn.lineno,
                            own_returns=[[r.lineno, ast.unparse(r.value) if r.value else "None"]
                                         for r in rs]))
    ss = [dict(line=s["line"], kind=s["kind"], expr=s["expr"],
               controls=s["controls"]) for s in sites]
    return dict(sha256=__import__("hashlib").sha256(raw).hexdigest(),
                bytes=len(raw), in_kd_census=os.path.basename(rel) in census,
                kd_verdict=kd_cls.get(rel, "NOT_IN_KD_173"),
                exit_sites=ss, func_returns=ret)


def main():
    out = {}
    for label, group in (("gates", GATES), ("k1bit_cited", K1BIT)):
        rows = []
        for rel in group:
            a = analyse(rel)
            ev = human_evidence(rel)
            rows.append(dict(rel=rel,
                             my_cls=a["cls"], my_statuses=a["statuses"],
                             my_data=a["any_data"],
                             my_sites=a["sites"],
                             orchestrator_cls=orch_cls.get(rel, "NOT_IN_413"),
                             agent_final_cls=agent_cls.get(rel, "NOT_IN_413"),
                             kd_verdict=ev["kd_verdict"],
                             human_evidence=ev))
        out[label] = rows

    # ---- Was any branched gate misjudged as CONSTANT_EXIT? -----------------
    # For the 4 gates: independent check of "does main() have >=2 distinct
    # literal return values".  Also scan the whole 413 batch for
    # orchestrator CONSTANT_EXIT rows whose own main returns >=2 distinct
    # literal values -> those are misjudged branched gates.
    bad = []
    for r in mybatch["rows"]:
        if orch_cls.get(r["rel"]) != "CONSTANT_EXIT":
            continue
        rel = r["rel"]
        try:
            tree = ast.parse(open(rel, "rb").read().decode("utf-8-sig", errors="replace"))
        except Exception:
            continue
        fdefs = func_defs(tree)
        # main-or-exit-called function: collect all distinct literal returns
        vals = set()
        for name, fns in fdefs.items():
            for fn in fns:
                for rt in own_returns(fn):
                    if isinstance(rt.value, ast.Constant) and isinstance(rt.value.value, int):
                        vals.add(rt.value.value)
        if len(vals) >= 2:
            bad.append(dict(rel=rel, distinct_literal_returns=sorted(vals),
                            my_cls=r["cls"]))
    out["orch_const_with_multiple_distinct_literal_returns"] = bad
    out["n_orch_const_with_multiple_distinct_literal_returns"] = len(bad)

    with open(os.path.join(WD, "_cev_focus_out.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    for label in ("gates", "k1bit_cited"):
        print("==", label)
        for r in out[label]:
            print("  %s\n     orch=%-18s agent=%-18s mine=%-18s sts=%s data=%s kd=%s" %
                  (r["rel"], r["orchestrator_cls"], r["agent_final_cls"],
                   r["my_cls"], r["my_statuses"], r["my_data"], r["kd_verdict"]))
            for s in r["human_evidence"]["exit_sites"]:
                print("       site :%s %s (%s) ctrl=%s" %
                      (s["line"], s["kind"], s["expr"], s["controls"]))
            for fr in r["human_evidence"]["func_returns"]:
                if fr["func"] == "main" or fr["own_returns"]:
                    print("       func %s :%s own_returns=%s" %
                          (fr["func"], fr["line"], fr["own_returns"][:8]))
    print("== orchestrator CONSTANT_EXIT rows with >=2 distinct literal returns (misjudged branched gates):",
          out["n_orch_const_with_multiple_distinct_literal_returns"])
    for b in bad:
        print("   ", b["rel"], b["distinct_literal_returns"], "-> my", b["my_cls"])


if __name__ == "__main__":
    main()
