# -*- coding: utf-8 -*-
"""_cev_adjudicate.py -- final per-file adjudication of all 44 diffs, plus
independent verification of the orchestrator rule's 4 defect classes."""
import ast
import json
import os
import sys
from collections import Counter, defaultdict

sys.dont_write_bytecode = True
ROOT = r"D:/Project/ra2-campaign-forge"
WD = os.path.join(ROOT, "lead", "const_exit_20261109")
sys.path.insert(0, WD)
os.chdir(ROOT)
from _cev_classifier import func_defs, own_returns, collect_sites  # noqa: E402

orch_raw = json.load(open(os.path.join(WD, "_ce_orchestrator_raw.json"), encoding="utf-8"))
orch_cls, orch_sites = {}, {}
for r in orch_raw["const_or_noexit"]:
    orch_cls[r["rel"]] = r["cls"]
    orch_sites[r["rel"]] = r["sites"]
for r in orch_raw["conditional"]:
    orch_cls[r["rel"]] = "CONDITIONAL_EXIT"
    orch_sites[r["rel"]] = []
agent = json.load(open(os.path.join(WD, "_ce_final_out.json"), encoding="utf-8"))
agent_cls = {r["rel"]: r["cls"] for r in agent["rows"]}
my = json.load(open(os.path.join(WD, "_cev_batch_out.json"), encoding="utf-8"))
my_rows = {r["rel"]: r for r in my["rows"]}

# ---- defect statistics (independent AST measurement) ----------------------
def facts(rel):
    raw = open(rel, "rb").read()
    t = ast.parse(raw.decode("utf-8-sig", errors="replace"))
    sites, parents = collect_sites(t)
    fdefs = func_defs(t)
    # main's OWN literal returns (distinct values)
    main_vals = []
    for fn in fdefs.get("main", []):
        for r in own_returns(fn):
            if isinstance(r.value, ast.Constant) and isinstance(r.value.value, (int, bool)):
                main_vals.append(int(r.value.value))
    all_vals = []
    for fns in fdefs.values():
        for fn in fns:
            for r in own_returns(fn):
                if isinstance(r.value, ast.Constant) and isinstance(r.value.value, (int, bool)):
                    all_vals.append(int(r.value.value))
    n_raise = sum(1 for s in sites if s["kind"].startswith("raise"))
    n_call = sum(1 for s in sites if s["kind"].startswith("call"))
    # nested-function returns that the orchestrator would wrongly count for main
    nested = 0
    for fn in fdefs.get("main", []):
        for n in ast.walk(fn):
            if n is not fn and isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nested += sum(1 for x in ast.walk(n) if isinstance(x, ast.Return))
    return dict(main_lit_returns=sorted(set(main_vals)),
                all_distinct_lit_returns=sorted(set(all_vals)),
                n_raise_systemexit=n_raise, n_exit_call=n_call,
                n_nested_returns_in_main=nested,
                n_sites=len(sites))

D = [(r, orch_cls[r], agent_cls[r], my_rows[r]["cls"]) for r in sorted(orch_cls)
     if orch_cls[r] != my_rows[r]["cls"]]
rows = []
for rel, o, a, m in D:
    f = facts(rel)
    osite = orch_sites.get(rel, [])
    # human/AST reasoning
    why = []
    if f["n_raise_systemexit"] and not osite:
        why.append("orchestrator rule ignores `raise SystemExit` (no ast.Call), so sites()=[]; AST shows a real exit site")
    if len(f["main_lit_returns"]) >= 2 and o == "CONSTANT_EXIT":
        why.append("main() own returns carry >=2 distinct literal statuses %s -> attainable set has >=2, not constant" % f["main_lit_returns"])
    if f["n_nested_returns_in_main"] and o == "CONDITIONAL_EXIT":
        why.append("ast.walk(fn) counted %d nested-function returns as main's -> false CONDITIONAL" % f["n_nested_returns_in_main"])
    if f["n_raise_systemexit"] and f["n_exit_call"] and o == "CONSTANT_EXIT":
        why.append("mixed raise+call: orchestrator kept only the sys.exit Call and ignored the raise site")
    if o == "CONSTANT_EXIT" and osite and not why:
        # nonzero literal exit inside a conditional -> 0 also attainable
        why.append("conditional nonzero literal exit also leaves normal-termination 0 -> >=2 statuses")
    rows.append(dict(rel=rel, orch=o, agent_final=a, my_mechanical=m,
                     agree_agent_final=(a == m), ast_facts=f,
                     orch_sites=[[x[0], x[1], x[2]] for x in osite],
                     human_basis="; ".join(why) if why else "see ast_facts / orch_sites"))

# ---- global defect counts over the 413 ------------------------------------
stats = dict(
    noexit_with_raise_systemexit=0,
    const_with_multi_distinct_lit_returns=0,
    const_reported_lineno_is_toplevel_not_call=0,
    orch_conditional_but_only_own_lit0=0,
    mixed_raise_and_call=0,
)
for rel, r in my_rows.items():
    f = facts(rel)
    o = orch_cls[rel]
    if o == "NO_EXIT_AT_ALL" and f["n_raise_systemexit"]:
        stats["noexit_with_raise_systemexit"] += 1
    if o == "CONSTANT_EXIT" and len(f["main_lit_returns"]) >= 2:
        stats["const_with_multi_distinct_lit_returns"] += 1
    if o == "CONDITIONAL_EXIT" and f["n_nested_returns_in_main"]:
        stats["orch_conditional_but_only_own_lit0"] += 1
    if f["n_raise_systemexit"] and f["n_exit_call"]:
        stats["mixed_raise_and_call"] += 1
    # lineno check: reported top-level stmt lineno != call lineno
    for ln, tag, cls, desc in orch_sites.get(rel, []):
        if any(s["line"] != ln for s in r["sites"]):
            stats["const_reported_lineno_is_toplevel_not_call"] += 1
            break

out = dict(n_diff=len(rows), diffs=rows,
           diff_pairs=dict(Counter("%s -> %s" % (r["orch"], r["my_mechanical"]) for r in rows)),
           stats=stats,
           agent_stats=json.load(open(os.path.join(WD, "_ce_rule_audit_out.json"),
                                      encoding="utf-8"))["stats"])
with open(os.path.join(WD, "_cev_adjudicate_out.json"), "w", encoding="utf-8") as fo:
    json.dump(out, fp=fo, ensure_ascii=False, indent=1)

print("n_diff", len(rows), out["diff_pairs"])
print("my independent stats:", stats)
print("agent-rule-audit stats:", out["agent_stats"])
print("\nper-file (orch -> agent_final / my_mechanical | AST basis):")
for r in rows:
    print("  %s\n     %-18s -> %-18s / %-18s | %s" %
          (r["rel"], r["orch"], r["agent_final"], r["my_mechanical"],
           r["human_basis"][:200]))
