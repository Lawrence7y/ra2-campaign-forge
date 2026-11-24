# -*- coding: utf-8 -*-
"""_ce_final.py -- FINAL adjudication classifier (my own, v2).

Read-only over the repo except _ce_* files in lead/const_exit_20261109/.
Pure AST; never executes a checked script or a checked gate.

Key semantic correction vs. the orchestrator's sites() rule:

  The object of interest is the SET OF ATTAINABLE PROCESS EXIT STATUSES,
  not the syntactic shape of one exit expression.

  * `if bad: return 1` / `return 0`  -> statuses {0,1} -> CONDITIONAL.
    (orchestrator: "all returns are literals" -> CONSTANT_EXIT, WRONG)
  * `if fails: sys.exit(1)` with an implicit fall-through -> statuses {0,1}
    -> CONDITIONAL.  (orchestrator: "字面量 1" -> CONSTANT_EXIT, WRONG)
  * `raise SystemExit(main())` -> a real exit site, invisible to a rule that
    only looks at ast.Call.  (orchestrator: NO_EXIT_AT_ALL, WRONG)
  * `sys.exit(main())` where main has helper functions with `return x`:
    only main's OWN returns count.  (orchestrator counts nested returns,
    producing false CONDITIONAL_EXIT)
  * The reported lineno `n.lineno` is the *top-level statement* line, not the
    call's line: VERIFY_A8.py reports 799 but sys.exit is at line 800.

Three final states:
  NO_EXIT_AT_ALL  : no exit site; normal termination => 0
  CONSTANT_EXIT   : exactly one attainable exit status (in practice 0)
  CONDITIONAL_EXIT: >=2 attainable statuses, or a data-dependent status
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

EXIT_NAMES = {"sys.exit", "exit", "quit", "os._exit"}


def dotted(n):
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Attribute):
        p = dotted(n.value)
        return p + "." + n.attr if p else n.attr
    return ""


def status_of_const(v):
    """Normalize a literal SystemExit argument to a POSIX-ish status."""
    if v is None:
        return 0
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, int):
        return v
    return 1                     # str / anything else -> status 1


def is_data_expr(e):
    """Does this expression's value depend on runtime data?"""
    if e is None or isinstance(e, ast.Constant):
        return False
    if isinstance(e, ast.IfExp):
        return is_data_expr(e.test) or is_data_expr(e.body) or is_data_expr(e.orelse)
    if isinstance(e, ast.BoolOp):
        return any(is_data_expr(v) for v in e.values)
    if isinstance(e, ast.UnaryOp):
        return is_data_expr(e.operand)
    if isinstance(e, ast.NamedExpr):
        return is_data_expr(e.value)
    if isinstance(e, ast.Tuple) or isinstance(e, ast.List):
        return any(is_data_expr(v) for v in e.elts)
    return True


def const_status(e):
    """Return (is_const, status)."""
    if e is None:
        return True, 0
    if isinstance(e, ast.Constant):
        return True, status_of_const(e.value)
    if isinstance(e, ast.IfExp):
        if is_data_expr(e.test):
            return False, None
        a = const_status(e.body); b = const_status(e.orelse)
        if a[0] and b[0]:
            return True, a[1]     # both arms reached via constant test; keep one
        return False, None
    if isinstance(e, ast.UnaryOp):
        return const_status(e.operand)
    if isinstance(e, ast.NamedExpr):
        return const_status(e.value)
    return False, None


def own_returns(fn):
    nested = set()
    for n in ast.walk(fn):
        if n is not fn and isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                          ast.Lambda)):
            for sub in ast.walk(n):
                nested.add(id(sub))
    return [n for n in ast.walk(fn)
            if isinstance(n, ast.Return) and id(n) not in nested]


def func_defs(tree):
    d = {}
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            d.setdefault(n.name, []).append(n)
    return d


def resolve_call_status(e, fdefs, seen=None):
    """Resolve sys.exit(f()) to a SET of attainable statuses + data flag."""
    seen = seen or set()
    if e is None:
        return {0}, False
    if isinstance(e, ast.Call) and isinstance(e.func, ast.Name) \
            and e.func.id in fdefs and e.func.id not in seen:
        seen = seen | {e.func.id}
        statuses, data = set(), False
        for fn in fdefs[e.func.id]:
            rs = own_returns(fn)
            if not rs:
                statuses.add(0)
            for r in rs:
                s, d = resolve_call_status(r.value, fdefs, seen)
                statuses |= s
                data |= d
        return statuses, data
    if isinstance(e, ast.Call) and isinstance(e.func, ast.Name) \
            and e.func.id not in fdefs:
        return set(), True        # unknown external function
    ok, st = const_status(e)
    if ok:
        return {st}, False
    return set(), True


def enclosing_control(tree, node, parents):
    """Is the node inside an if/try/for/while/with (conditional reachability)?"""
    p = parents.get(id(node))
    kinds = []
    while p is not None:
        if isinstance(p, (ast.If, ast.Try, ast.For, ast.AsyncFor, ast.While,
                          ast.With, ast.AsyncWith, ast.IfExp)):
            kinds.append(type(p).__name__)
        p = parents.get(id(p))
    return kinds


def analyse(rel, raw):
    tree = ast.parse(raw.decode("utf-8-sig", errors="replace"))
    fdefs = func_defs(tree)
    parents = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            parents[id(c)] = n

    sites = []
    for n in ast.walk(tree):
        arg, kind = None, None
        if isinstance(n, ast.Call) and dotted(n.func) in EXIT_NAMES:
            kind = "E1:" + dotted(n.func)
            arg = n.args[0] if n.args else None
        elif isinstance(n, ast.Raise) and n.exc is not None:
            e = n.exc
            is_se = (isinstance(e, ast.Call) and dotted(e.func) in
                     ("SystemExit", "builtins.SystemExit")) or \
                    dotted(e) in ("SystemExit", "builtins.SystemExit")
            if is_se:
                kind = "E2:raise SystemExit"
                arg = e.args[0] if (isinstance(e, ast.Call) and e.args) else None
        if kind is None:
            continue
        sts, data = resolve_call_status(arg, fdefs)
        ctrl = enclosing_control(tree, n, parents)
        sites.append(dict(line=n.lineno, kind=kind,
                          expr=ast.unparse(arg) if arg else "None",
                          statuses=sorted(sts), data=data,
                          controls=ctrl,
                          conditional_reach=bool(ctrl)))

    # implicit nonzero exit via uncaught exception at module level
    implicit = []
    for top in tree.body:
        for n in ast.walk(top):
            if isinstance(n, (ast.Assert, ast.Raise)):
                # only top-level / not inside a function counts as a process-level
                # uncaught-exception channel
                p = parents.get(id(n))
                inside_func = False
                while p is not None:
                    if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        inside_func = True; break
                    p = parents.get(id(p))
                if not inside_func:
                    implicit.append((n.lineno, type(n).__name__))
    has_bare_raise = any(isinstance(n, ast.Raise) and n.exc is None
                         for n in ast.walk(tree))
    has_assert = any(isinstance(n, ast.Assert) for n in ast.walk(tree))
    atexit = any(isinstance(n, ast.Call) and dotted(n.func) == "atexit.register"
                 for n in ast.walk(tree))

    # attainable status set
    status_set, any_data = set(), False
    for s in sites:
        status_set |= set(s["statuses"])
        any_data |= s["data"]
    # A nonzero literal exit site inside a conditional also leaves an implicit
    # normal-termination path => status 0 is attainable too.
    for s in sites:
        if s["conditional_reach"] and any(v != 0 for v in s["statuses"]):
            status_set.add(0)
    # sites with a data-dependent expression may take 0 or nonzero
    if any_data:
        status_set |= {0, 1}

    if not sites:
        cls = "NO_EXIT_AT_ALL"
    elif any_data or len(status_set) > 1:
        cls = "CONDITIONAL_EXIT"
    else:
        cls = "CONSTANT_EXIT"

    # conjunction-of-k subclass: does any exit expression read all()/and/not fails?
    reads_conj, reads_single = False, False
    for s in sites:
        a = s["expr"] or ""
        if re.search(r"\ball\s*\(|not\s+\w*fail|\bok\b|all_ok|passed", a):
            reads_conj = True
        if re.search(r"\bany\s*\(|\bexists\b|is_file\(\)|path\.exists|"
                     r"\bor\b|\|\|", a):
            reads_single = True

    flags = []
    if any(s["kind"].startswith("E2:") for s in sites): flags.append("RAISE_SYSTEMEXIT")
    if any(s["kind"].startswith("E1:") for s in sites) and any(
            s["kind"].startswith("E2:") for s in sites): flags.append("MIXED")
    if implicit: flags.append("IMPLICIT_EXCEPTION_CHANNEL")
    if has_bare_raise: flags.append("BARE_RAISE")
    if has_assert: flags.append("ASSERT")
    if atexit: flags.append("ATEXIT")
    if not sites and has_assert: flags.append("VERDICT_VIA_ASSERT_ONLY")
    if not sites and any(isinstance(n, ast.Call) and (
            (isinstance(n.func, ast.Attribute) and n.func.attr in
             ("write_text", "write", "dump")) or
            (isinstance(n.func, ast.Name) and n.func.id in ("open",)))
            for n in ast.walk(tree)):
        flags.append("FILE_OR_STDOUT_ONLY_VERDICT")

    return dict(rel=rel, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                cls=cls, attainable_statuses=sorted(status_set),
                any_data=any_data, n_sites=len(sites), sites=sites,
                implicit_exception=implicit[:6], flags=flags,
                reads_conjunction=reads_conj, reads_single=reads_single,
                dup_func_names=sorted(k for k, v in fdefs.items() if len(v) > 1))


def main():
    orch = json.load(open(WD / "_ce_orchestrator_raw.json", encoding="utf-8"))
    ocls = {}
    osites = {}
    for r in orch["const_or_noexit"]:
        ocls[r["rel"]] = r["cls"]; osites[r["rel"]] = r["sites"]
        ocls[r["rel"] + "|cites"] = r["cites"]
    for r in orch["conditional"]:
        ocls[r["rel"]] = "CONDITIONAL_EXIT"; osites[r["rel"]] = []

    rows = []
    for rel in sorted(ocls):
        if rel.endswith("|cites"):
            continue
        rows.append(dict(basename=os.path.basename(rel),
                         orchestrator_cls=ocls[rel],
                         orchestrator_sites=osites.get(rel, []),
                         cites=ocls.get(rel + "|cites", 0),
                         **analyse(rel, Path(rel).read_bytes())))

    diffs = [r for r in rows if r["orchestrator_cls"] != r["cls"]]
    conj = [r for r in rows if r["cls"] == "CONDITIONAL_EXIT"
            and r["reads_conjunction"]]
    nonconj = [r for r in rows if r["cls"] == "CONDITIONAL_EXIT"
               and not r["reads_conjunction"]]
    out = dict(n=len(rows),
               orchestrator_classes=dict(Counter(r["orchestrator_cls"] for r in rows)),
               final_classes=dict(Counter(r["cls"] for r in rows)),
               diff_pairs={"%s -> %s" % k: v for k, v in
                           Counter((r["orchestrator_cls"], r["cls"])
                                   for r in diffs).items()},
               n_diff=len(diffs),
               flag_counts=dict(Counter(f for r in rows for f in r["flags"])),
               conditional_reads_conjunction=len(conj),
               conditional_not_conjunction=len(nonconj),
               zero_information=dict(Counter(r["cls"] for r in rows
                                            if r["cls"] in
                                            ("NO_EXIT_AT_ALL", "CONSTANT_EXIT"))),
               rows=rows, diffs=[r["rel"] for r in diffs])
    (WD / "_ce_final_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("rows", "diffs")}, ensure_ascii=False, indent=1))
    print("WROTE", (WD / "_ce_final_out.json").as_posix())


if __name__ == "__main__":
    main()
