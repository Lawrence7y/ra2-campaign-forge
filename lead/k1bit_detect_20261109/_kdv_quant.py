# -*- coding: utf-8 -*-
"""_kdv_quant.py -- quantify name-level vs dataflow-level behavior of _kd_detect.py.

Read-only; writes only _kdv_quant_out.json in the write domain.

Q1 How many CONFIRMED files derive S1 k from real dataflow (collect_ksources)
   vs. rely on TOKENISH name heuristics in is_token_source?
Q2 Is collect_ksources' direct-assignment branch (lines 148-160) dead because
   bindings values are (lineno, expr) pairs rather than expr nodes?
Q3 Verify the reply's all()/any() overlap counts on the 173-file list.
Q4 Does BIT_ACCUM alone ever produce CONFIRMED_K1BIT?
"""
import ast
import importlib.util
import json
import re
import sys
from pathlib import Path

WD = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("D:/Project/ra2-campaign-forge")
LIST = ROOT / "lead/check_family_20261109/_cf_filelist.txt"
spec = importlib.util.spec_from_file_location("_kd_q", WD / "_kd_detect.py")
kd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kd)

rels = [ln.strip()[2:] if ln.strip().startswith("./") else ln.strip()
        for ln in LIST.read_text(encoding="utf-8").splitlines() if ln.strip()]
out = json.loads((WD / "_kd_detect_out.json").read_text(encoding="utf-8"))
by = {r["rel"]: r for r in out["rows"]}

tok_reasons = {}
confirmed = out["confirmed"]
for rel in confirmed:
    r = by[rel]
    for k, v in r.get("tokens", {}).items():
        tok_reasons[v["why"]] = tok_reasons.get(v["why"], 0) + 1

# Q2: count files with a direct literal string collection assignment that
# collect_ksources fails to mark as a k-source.
dead_branch = []
for rel in rels:
    raw = (ROOT / rel).read_bytes()
    try:
        t = ast.parse(raw.decode("utf-8-sig", errors="replace"))
    except SyntaxError:
        continue
    b = kd.build_bindings(t)
    tok = kd.collect_ksources(t, b)
    for n in ast.walk(t):
        if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) for x in n.targets):
            ss = kd.literal_str_collection(n.value)
            if ss and len(ss) >= 2:
                names = [x.id for x in n.targets if isinstance(x, ast.Name)]
                not_marked = [x for x in names if x not in tok]
                if not_marked:
                    dead_branch.append(dict(rel=rel, line=n.lineno,
                                            names=not_marked, n_tokens=len(ss)))
                break

# Q3 all()/any() overlap, computed independently from raw bytes
all_files, any_files, both, all_only = set(), set(), set(), set()
for rel in rels:
    text = (ROOT / rel).read_bytes().decode("utf-8-sig", errors="replace")
    tree = ast.parse(text)
    fs = {n.func.id for n in ast.walk(tree)
          if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    if "all" in fs:
        all_files.add(rel)
    if "any" in fs:
        any_files.add(rel)
    if "all" in fs and "any" in fs:
        both.add(rel)
    if "all" in fs and "any" not in fs:
        all_only.add(rel)

verdict_of_both = {}
for rel in sorted(both):
    v = by[rel]["verdict"]
    verdict_of_both.setdefault(v, []).append(rel)

# Q4 BIT_ACCUM present without any real collapse in confirmed/legal files
accum_only = []
for rel in rels:
    r = by[rel]
    kinds = [c["kind"] for c in r.get("collapse", [])]
    if any(k.startswith("BIT_ACCUM") for k in kinds) and not any(
            k.startswith(("OR_COLLAPSE", "TERNARY_OR", "ARGMIN")) for k in kinds):
        accum_only.append(dict(rel=rel, verdict=r["verdict"], kinds=kinds))

res = dict(
    n=len(rels),
    n_confirmed=len(confirmed),
    token_reason_counts=tok_reasons,
    confirmed_with_empty_tokens=[r for r in confirmed if not by[r].get("tokens")],
    dead_direct_assignment_branch=dict(
        n_files_affected=len(dead_branch),
        sample=dead_branch[:12],
        explanation="collect_ksources iterates `for v in vals` where vals are "
                    "(lineno, expr) PAIRS; literal_str_collection(v) therefore "
                    "always returns None because v is a python tuple, not an AST node."),
    all_any=dict(n_all=len(all_files), n_any=len(any_files),
                 n_both=len(both), n_all_only=len(all_only),
                 all_only=sorted(all_only),
                 all_only_verdicts={r: by[r]["verdict"] for r in sorted(all_only)},
                 both_by_verdict={k: len(v) for k, v in verdict_of_both.items()},
                 both_confirmed_and_has_AND_legal=sum(
                     1 for rel in verdict_of_both.get("CONFIRMED_K1BIT", [])
                     if any(c["kind"] == "AND_aggregate" for c in by[rel].get("legal", []))),
                 both_confirmed_n=len(verdict_of_both.get("CONFIRMED_K1BIT", []))),
    accum_only=dict(n=len(accum_only), rows=accum_only[:10],
                    confirmed_n=sum(1 for x in accum_only
                                    if x["verdict"] == "CONFIRMED_K1BIT")),
)
(WD / "_kdv_quant_out.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("n=%d confirmed=%d" % (res["n"], res["n_confirmed"]))
print("token_reason_counts=", json.dumps(tok_reasons, ensure_ascii=False))
print("confirmed_with_empty_tokens=", res["confirmed_with_empty_tokens"])
print("dead_branch_files=", len(dead_branch), "sample=", json.dumps(dead_branch[:4], ensure_ascii=False))
print("all_any=", json.dumps(res["all_any"], ensure_ascii=False))
print("accum_only=", json.dumps(res["accum_only"], ensure_ascii=False))
print("WROTE", (WD / "_kdv_quant_out.json").as_posix())
