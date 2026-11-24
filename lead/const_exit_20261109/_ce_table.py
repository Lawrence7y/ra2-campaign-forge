# -*- coding: utf-8 -*-
"""_ce_table.py -- per-item adjudication table (step 2(b)).

Read-only; writes only _ce_* in lead/const_exit_20261109/.
Produces the full CONSTANT_EXIT / NO_EXIT_AT_ALL list with AST facts,
plus CONDITIONAL_EXIT representatives, plus the ledger line list.
"""
import ast
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "const_exit_20261109"
os.chdir(ROOT)


def ast_fact(rel):
    raw = Path(rel).read_bytes()
    t = ast.parse(raw.decode("utf-8-sig", errors="replace"))
    fdefs = {}
    for n in ast.walk(t):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fdefs.setdefault(n.name, []).append(n)
    sites = []
    for n in ast.walk(t):
        if isinstance(n, ast.Call):
            nm = (n.func.attr if isinstance(n.func, ast.Attribute) else
                  n.func.id if isinstance(n.func, ast.Name) else "")
            if nm in ("exit", "_exit"):
                sites.append((n.lineno, "sys.exit(%s)" % (
                    ast.unparse(n.args[0]) if n.args else "None")))
        if isinstance(n, ast.Raise) and n.exc is not None:
            e = n.exc
            if (isinstance(e, ast.Call) and isinstance(e.func, ast.Name) and
                    e.func.id == "SystemExit"):
                sites.append((n.lineno, "raise SystemExit(%s)" % (
                    ast.unparse(e.args[0]) if e.args else "None")))
    mains = []
    for nm, fns in fdefs.items():
        for f in fns:
            nested = set()
            for x in ast.walk(f):
                if x is not f and isinstance(x, (ast.FunctionDef,
                        ast.AsyncFunctionDef, ast.Lambda)):
                    for z in ast.walk(x):
                        nested.add(id(z))
            rs = [(r.lineno, ast.unparse(r.value) if r.value else None)
                  for r in ast.walk(f)
                  if isinstance(r, ast.Return) and id(r) not in nested]
            if nm in ("main", "run", "_main_wrapper") or rs:
                mains.append(dict(func=nm, line=f.lineno, returns=rs))
    return dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                exit_sites=sites[:8], n_exit_sites=len(sites),
                func_returns=mains[:6])


def main():
    orch = json.load(open(WD / "_ce_orchestrator_raw.json", encoding="utf-8"))
    fin = json.load(open(WD / "_ce_final_out.json", encoding="utf-8"))
    impact = json.load(open(WD / "_ce_impact_out.json", encoding="utf-8"))
    rows = fin["rows"]
    byrel = {r["rel"]: r for r in rows}

    constant, noexit, cond_reps = [], [], []
    for r in rows:
        f = ast_fact(r["rel"])
        e = dict(rel=r["rel"], basename=r["basename"],
                 orchestrator_cls=r["orchestrator_cls"],
                 orchestrator_sites=r["orchestrator_sites"],
                 final_cls=r["cls"],
                 attainable_statuses=r["attainable_statuses"],
                 cites=r["cites"], flags=r["flags"], **f)
        if r["cls"] == "CONSTANT_EXIT":
            constant.append(e)
        elif r["cls"] == "NO_EXIT_AT_ALL":
            noexit.append(e)
        elif r["cls"] == "CONDITIONAL_EXIT":
            cond_reps.append(e)

    # write a compact human-readable table too
    lines = []
    lines.append("# _ce_table.md — 逐件归属（自动表，非交付成件）")
    lines.append("")
    lines.append("## CONSTANT_EXIT (%d 件，全部)" % len(constant))
    lines.append("")
    lines.append("| rel | 编排方 verdict | 最终 | 可达状态 | 出口 site | cites |")
    lines.append("|---|---|---|---|---|---|")
    for r in constant:
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            r["rel"], r["orchestrator_cls"], r["final_cls"],
            ",".join(map(str, r["attainable_statuses"])),
            "; ".join("%d:%s" % (a, b) for a, b in r["exit_sites"]) or "(none)",
            r["cites"]))
    lines.append("")
    lines.append("## NO_EXIT_AT_ALL (%d 件，全部)" % len(noexit))
    lines.append("")
    lines.append("| rel | 编排方 verdict | 最终 | 出口 site 数 | cites |")
    lines.append("|---|---|---|---|---|")
    for r in noexit:
        lines.append("| %s | %s | %s | %d | %s |" % (
            r["rel"], r["orchestrator_cls"], r["final_cls"],
            r["n_exit_sites"], r["cites"]))
    (WD / "_ce_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    out = dict(n_constant=len(constant), n_noexit=len(noexit),
               n_conditional=len(cond_reps),
               constant=constant, noexit=noexit,
               conditional_representatives=cond_reps[:15],
               ledger_vacuous_orch=impact["ledger"]["orch_vacuous"],
               ledger_subject_vacuous=impact["ledger"]["subject_vacuous"],
               ledger_all_lines=impact["ledger"]["lines"])
    (WD / "_ce_table_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(dict(n_constant=len(constant), n_noexit=len(noexit),
                          n_conditional=len(cond_reps),
                          n_ledger_orch_vac=len(out["ledger_vacuous_orch"]),
                          n_ledger_subject_vac=len(
                              out["ledger_subject_vacuous"])),
                     ensure_ascii=False))
    print("WROTE", (WD / "_ce_table.md").as_posix(),
          "and", (WD / "_ce_table_out.json").as_posix())


if __name__ == "__main__":
    main()
