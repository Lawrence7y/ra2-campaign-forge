# -*- coding: utf-8 -*-
"""_ce_minimal.py -- MINIMAL pasteable AST predicate for CONSTANT_EXIT.

Step 4(c) deliverable.  This is the smallest rule that catches
"k checks are computed but the process exit status does not depend on them".

    python -I -X utf8 D:/Project/ra2-campaign-forge/lead/const_exit_20261109/_ce_minimal.py <file.py> [<file.py> ...]

Pure AST: parses files, never executes them.

PREDICATE (copy/paste into any classifier):

  Let SITES = all ast.Call nodes whose callee ends in `exit`/`quit`/`_exit`,
              PLUS all ast.Raise nodes whose exc is SystemExit(...).
  For each site, resolve its status argument to a SET of attainable statuses:
    - no arg / None / numeric literal           -> {that status}
    - f() where f is a local FunctionDef        -> union over f's OWN
      `return` expressions (excluding nested functions), recursively
    - a data-dependent expression (Name / IfExp with live test / BoolOp /
      BinOp / Compare / Attribute / Subscript / Call to unknown fn)
                                               -> DATA
    - a literal str                            -> {1} (SystemExit(str) => 1)
  Add 0 to the attainable set if a nonzero exit site sits inside a conditional
  (there is an implicit normal-termination path).

  CONSTANT_EXIT  <=>  SITES is non-empty AND no site is DATA AND
                      the attainable status set has exactly one member.
  NO_EXIT_AT_ALL <=>  SITES is empty.
  CONDITIONAL_EXIT <=> otherwise.

Contrast with the orchestrator's rule, which only looks at sys.exit/exit Calls,
treats "all of main()'s returns are literals" as CONSTANT (WRONG: 0/1/2 are
three attainable statuses), counts nested-function returns as main's, and
ignores raise SystemExit entirely.
"""
import ast
import hashlib
import json
import sys
from pathlib import Path

EXITS = {"exit", "quit", "_exit", "SystemExit"}


def callee(n):
    f = n.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return ""


def own_returns(fn):
    nested = set()
    for x in ast.walk(fn):
        if x is not fn and isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef,
                                          ast.Lambda)):
            for z in ast.walk(x):
                nested.add(id(z))
    return [r for r in ast.walk(fn)
            if isinstance(r, ast.Return) and id(r) not in nested]


def funcs(tree):
    return {n.name: n for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def statuses(e, F, seen=None):
    """Return (set_of_literal_statuses, is_data_dependent)."""
    seen = seen or frozenset()
    if e is None:
        return {0}, False
    if isinstance(e, ast.Constant):
        v = e.value
        return ({v} if isinstance(v, int) and not isinstance(v, bool)
                else {int(v)} if isinstance(v, bool) else {1}), False
    if isinstance(e, ast.IfExp):
        a, da = statuses(e.body, F, seen)
        b, db = statuses(e.orelse, F, seen)
        from collections import ChainMap
        test_data = not isinstance(e.test, ast.Constant)
        return a | b, da or db or test_data
    if isinstance(e, ast.Call) and isinstance(e.func, ast.Name) \
            and e.func.id in F and e.func.id not in seen:
        out, data = set(), False
        rs = own_returns(F[e.func.id])
        if not rs:
            out.add(0)
        for r in rs:
            s, d = statuses(r.value, F, seen | {e.func.id})
            out |= s
            data |= d
        return out, data
    if isinstance(e, ast.Call) and isinstance(e.func, ast.Name) \
            and e.func.id not in F:
        return set(), True
    if isinstance(e, (ast.Name, ast.Attribute, ast.Subscript, ast.Compare,
                      ast.BinOp, ast.BoolOp, ast.UnaryOp, ast.ListComp,
                      ast.GeneratorExp, ast.JoinedStr, ast.Call)):
        return set(), True
    return set(), True


def classify(path):
    raw = Path(path).read_bytes()
    tree = ast.parse(raw.decode("utf-8-sig", errors="replace"))
    F = funcs(tree)
    parents = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            parents[id(c)] = n
    sites = []
    for n in ast.walk(tree):
        arg, tag = None, None
        if isinstance(n, ast.Call) and callee(n) in ("exit", "quit", "_exit"):
            tag, arg = "call:" + callee(n), (n.args[0] if n.args else None)
        elif isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call) \
                and callee(n.exc) == "SystemExit":
            tag, arg = "raise:SystemExit", (n.exc.args[0]
                                             if n.exc.args else None)
        if tag is None:
            continue
        st, data = statuses(arg, F)
        # conditional reach => implicit normal path => 0
        p, cond = parents.get(id(n)), False
        while p is not None:
            if isinstance(p, (ast.If, ast.Try, ast.For, ast.While, ast.With)):
                cond = True
                break
            p = parents.get(id(p))
        if cond and any(v != 0 for v in st):
            st = st | {0}
        sites.append(dict(line=n.lineno, tag=tag,
                          expr=ast.unparse(arg) if arg else "None",
                          statuses=sorted(st), data=data, conditional=cond))
    if not sites:
        cls = "NO_EXIT_AT_ALL"
    elif any(s["data"] for s in sites) or len(
            set(v for s in sites for v in s["statuses"])) > 1:
        cls = "CONDITIONAL_EXIT"
    else:
        cls = "CONSTANT_EXIT"
    return dict(rel=str(path).replace("\\", "/"),
                sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                cls=cls, sites=sites)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    print(json.dumps([classify(p) for p in sys.argv[1:]],
                     ensure_ascii=False, indent=1))
