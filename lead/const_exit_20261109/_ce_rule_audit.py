# -*- coding: utf-8 -*-
"""_ce_rule_audit.py -- quantify the orchestrator sites() rule's blind spots.

Read-only over repo (writes only _ce_*.json in lead/const_exit_20261109/).
Runs no checked script and no checked gate.  Pure AST reads.
"""
import ast
import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "const_exit_20261109"
os.chdir(ROOT)


def dotted(n):
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Attribute):
        p = dotted(n.value)
        return p + "." + n.attr if p else n.attr
    return ""


def main_returns(tree, name="main"):
    """Returns belonging to main itself (excluding nested funcs), plus all
    returns ast.walk sees (what the orchestrator counts)."""
    mains = [n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
             and n.name == name]
    own, allr = [], []
    for m in mains:
        nested = set()
        for n in ast.walk(m):
            if n is not m and isinstance(n, (ast.FunctionDef,
                                             ast.AsyncFunctionDef, ast.Lambda)):
                for sub in ast.walk(n):
                    nested.add(id(sub))
        for n in ast.walk(m):
            if isinstance(n, ast.Return) and id(n) not in nested:
                own.append(n)
        for n in ast.walk(m):
            if isinstance(n, ast.Return):
                allr.append(n)
    return own, allr


def lit_vals(returns):
    vals = []
    for r in returns:
        if r.value is None:
            vals.append(None)
        elif isinstance(r.value, ast.Constant):
            vals.append(r.value.value)
        else:
            vals.append("<expr>")
    return vals


def scan_file(rel):
    raw = Path(rel).read_bytes()
    tree = ast.parse(raw.decode("utf-8-sig", errors="replace"))
    calls, raises = [], []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and dotted(n.func) in (
                "sys.exit", "exit", "quit", "os._exit"):
            calls.append(dict(line=n.lineno, func=dotted(n.func),
                              arg=ast.unparse(n.args[0]) if n.args else None))
        if isinstance(n, ast.Raise) and n.exc is not None:
            e = n.exc
            if (isinstance(e, ast.Call) and dotted(e.func) in
                    ("SystemExit", "builtins.SystemExit")) or \
               dotted(e) in ("SystemExit", "builtins.SystemExit"):
                arg = e.args[0] if isinstance(e, ast.Call) and e.args else None
                raises.append(dict(line=n.lineno,
                                   arg=ast.unparse(arg) if arg else None))
    own, allr = main_returns(tree)
    nested_extra = len(allr) - len(own)
    distinct_lits = set(v for v in lit_vals(own) if v != "<expr>")
    # top-level stmt lineno vs actual call lineno (orchestrator artefact)
    off = []
    for c in calls:
        for top in tree.body:
            if any(sub is c for sub in []):
                pass
            for sub in ast.walk(top):
                if isinstance(sub, ast.Call) and sub.lineno == c["line"]:
                    if top.lineno != c["line"]:
                        off.append((top.lineno, c["line"]))
                    break
    return dict(rel=rel, sha256=hashlib.sha256(raw).hexdigest(),
                bytes=len(raw), n_calls=len(calls), calls=calls,
                n_raises=len(raises), raises=raises,
                n_own_returns=len(own), own_vals=lit_vals(own),
                n_all_returns=len(allr), nested_extra=nested_extra,
                n_distinct_lit_returns=len(distinct_lits),
                distinct_lits=sorted(map(str, distinct_lits)),
                top_line_vs_call_line=off[:3])


def main():
    orch = json.load(open(WD / "_ce_orchestrator_raw.json", encoding="utf-8"))
    audit = json.load(open(WD / "_ce_audit_out.json", encoding="utf-8"))
    byrel = {r["rel"]: r for r in audit["rows"]}
    out = dict(orchestrator_const=[], orchestrator_noexit=[],
               orchestrator_conditional=[], gates=[])
    stats = Counter()

    # CONSTANT_EXIT: does main() actually have >1 distinct literal return?
    for r in orch["const_or_noexit"]:
        if r["cls"] != "CONSTANT_EXIT":
            continue
        s = scan_file(r["rel"])
        s["orchestrator_sites"] = r["sites"]
        s["independent_cls"] = byrel[r["rel"]]["cls"]
        out["orchestrator_const"].append(s)
        if s["n_distinct_lit_returns"] > 1:
            stats["const_multi_distinct_lit_returns"] += 1
        if s["nested_extra"] > 0:
            stats["const_nested_return_contamination"] += 1
        if s["n_raises"] > 0:
            stats["const_with_raise_systemexit"] += 1
        if s["top_line_vs_call_line"]:
            stats["const_reported_lineno_is_toplevel_not_call"] += 1

    # NO_EXIT_AT_ALL: does it have raise SystemExit (missed site)?
    for r in orch["const_or_noexit"]:
        if r["cls"] != "NO_EXIT_AT_ALL":
            continue
        s = scan_file(r["rel"])
        s["independent_cls"] = byrel[r["rel"]]["cls"]
        out["orchestrator_noexit"].append(s)
        if s["n_raises"] > 0:
            stats["noexit_with_raise_systemexit"] += 1
        if s["n_calls"] > 0:
            stats["noexit_with_exit_call"] += 1
        if s["n_own_returns"] > 1 and s["n_distinct_lit_returns"] > 1:
            stats["noexit_main_multi_distinct_lit"] += 1

    # CONDITIONAL_EXIT: what does the exit branch read?
    for r in orch["conditional"]:
        s = scan_file(r["rel"])
        args = [c["arg"] for c in s["calls"] if c["arg"]] + \
               [x["arg"] for x in s["raises"] if x["arg"]]
        s["exit_args"] = args[:6]
        s["reads_conjunction"] = any(
            a and re.search(r"\ball\s*\(|\.all\b|and\b|&&|not fails|"
                            r"len\(.*fail|sum\(", a) for a in args)
        s["reads_single_or_exists"] = any(
            a and re.search(r"\bany\s*\(|\bor\b|\|\||exists|is_file|"
                            r"os\.path\.exists|len\(.*\)==0", a) for a in args)
        s["exit_arg_is_main_call"] = any(
            a and a.strip() in ("main()", "main(sys.argv)", "main(sys.argv[1:])")
            for a in args)
        out["orchestrator_conditional"].append(s)

    # four production gates (NOT in the 413; in 173-census)
    for rel in ["lead/d27_ruling_20261106/check_d27.py",
                "lead/d28_ruling_20261106/check_d28.py",
                "lead/d29_ruling_20261106/check_d29.py",
                "lead/d30_ruling_20261106/check_d30.py"]:
        s = scan_file(rel)
        # what would orchestrator sites() say?
        out["gates"].append(s)
        stats["gates_in_census"] += 1

    # synthetic cases for rule semantics
    synths = {
        "branch_literals": "import sys\ndef main():\n    if bad: return 1\n    return 0\nif __name__=='__main__': sys.exit(main())\n",
        "ifexp": "import sys\ndef main():\n    return 0 if ok else 1\nif __name__=='__main__': sys.exit(main())\n",
        "raise_only": "import sys\ndef main():\n    return 0 if ok else 1\nif __name__=='__main__': raise SystemExit(main())\n",
        "mixed": "import sys\ndef main():\n    return 0\nif True: raise SystemExit(2)\nif __name__=='__main__': sys.exit(main())\n",
        "nested": "import sys\ndef main():\n    def h(): return x\n    return 0\nif __name__=='__main__': sys.exit(main())\n",
    }
    out["synthetic"] = {}
    for k, src in synths.items():
        t = ast.parse(src)
        funcs = {x.name: x for x in ast.walk(t) if isinstance(x, ast.FunctionDef)}
        calls = []
        for n in t.body:
            for c in ast.walk(n):
                if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) \
                        and c.func.attr == "exit" and \
                        isinstance(c.func.value, ast.Name) and \
                        c.func.value.id == "sys":
                    calls.append((n.lineno, c.lineno,
                                  c.args[0] if c.args else None))
        rows = []
        for top_ln, call_ln, arg in calls:
            if arg is None:
                rows.append((top_ln, call_ln, "CONSTANT_EXIT", "no arg"))
            elif isinstance(arg, ast.Constant):
                rows.append((top_ln, call_ln, "CONSTANT_EXIT", "literal"))
            elif isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) \
                    and arg.func.id in funcs:
                fn = funcs[arg.func.id]
                rs = [x.value for x in ast.walk(fn) if isinstance(x, ast.Return)]
                kinds = set()
                for r in rs:
                    if r is None:
                        kinds.add("none")
                    elif isinstance(r, ast.Constant):
                        kinds.add("const")
                    else:
                        kinds.add("expr")
                rows.append((top_ln, call_ln,
                             "CONSTANT_EXIT" if (not rs or kinds <= {"const", "none"})
                             else "CONDITIONAL_EXIT",
                             "returns=%s" % [ast.unparse(x) if x else None for x in rs]))
        raises = [(n.lineno, ast.unparse(n.exc)) for n in ast.walk(t)
                  if isinstance(n, ast.Raise) and n.exc is not None]
        out["synthetic"][k] = dict(orchestrator_sites=rows,
                                   raise_statements=raises,
                                   orchestrator_sees_raise=any(
                                       "SystemExit" in x[1] for x in raises) and
                                   "assumed_no" if False else False)
        # explicitly: orchestrator's site list contains only Call sites
        out["synthetic"][k]["orchestrator_ignores_raise"] = bool(raises)

    out["stats"] = dict(stats)
    (WD / "_ce_rule_audit_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(dict(stats=dict(stats),
                          n_const=len(out["orchestrator_const"]),
                          n_noexit=len(out["orchestrator_noexit"]),
                          n_cond=len(out["orchestrator_conditional"]),
                          synthetic=out["synthetic"]),
                     ensure_ascii=False, indent=1))
    print("WROTE", (WD / "_ce_rule_audit_out.json").as_posix())


if __name__ == "__main__":
    main()
