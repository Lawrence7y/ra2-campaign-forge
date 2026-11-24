# -*- coding: utf-8 -*-
"""_ce_audit.py -- INDEPENDENT exit-code-qualification auditor.

Read-only over the repository except for files written into
lead/const_exit_20261109/ (all prefixed _ce_).

Purpose: do NOT reuse the orchestrator's sites() rule.  Independently enumerate
every construct that can determine a process exit status, then classify each
cited script by "is the exit code a function of the check results?".

Exit-status-affecting constructs considered here (superset of orchestrator):
  E1  sys.exit(x) / exit(x) / quit(x) / os._exit(x)          (Call)
  E2  raise SystemExit(x) / raise SystemExit                (Raise)
  E3  return x  inside a function called by an E1/E2 site   (interprocedural)
  E4  bare `raise` / assert  (uncaught exception -> nonzero) [flagged, not a
      "check result" function unless the assertion reads a check result]
  E5  atexit.register(f) whose f calls E1/E2                 [flagged]
  E6  top-level `if __name__ == "__main__":` guard reachability
  E7  `os.environ` / file writes carrying the verdict but never read back
      into an exit site                                      [flagged]

Classification (independent):
  NO_EXIT_AT_ALL    no E1/E2/E3 site anywhere; normal termination => 0
  CONSTANT_EXIT     every exit site resolves to a literal / None / implicit 0
  CONDITIONAL_EXIT  at least one exit site resolves to a data-dependent expr

Extra flags on each row (fifth-form hunting):
  RAISE_SYSTEMEXIT, NESTED_FUNC_EXIT, EXIT_IN_NONMAIN_FUNC, IFEXP_RETURN,
  CONST_COND_EXIT, FILE_ONLY_VERDICT, ASSERT_ONLY, MIXED_RAISE_AND_EXIT,
  SITE_LINE_IS_TOPLEVEL_ONLY (orchestrator artefact)
"""
import ast
import builtins
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

EXIT_FUNCS = {"sys.exit": "sys.exit", "exit": "exit", "quit": "quit",
              "os._exit": "os._exit"}


def dotted(n):
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Attribute):
        p = dotted(n.value)
        return p + "." + n.attr if p else n.attr
    return ""


def is_systemexit_raise(n):
    if not isinstance(n, ast.Raise):
        return False
    e = n.exc
    if e is None:
        return False                       # bare raise, handled separately
    if isinstance(e, ast.Call):
        return dotted(e.func) in ("SystemExit", "builtins.SystemExit")
    return dotted(e) in ("SystemExit", "builtins.SystemExit")


def func_defs(tree):
    """name -> list of FunctionDef (keep ALL, unlike orchestrator's last-wins)."""
    d = {}
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            d.setdefault(n.name, []).append(n)
    return d


def own_returns(fn):
    """Return expressions belonging to fn itself, NOT to nested functions."""
    out = []
    nested = set()
    for n in ast.walk(fn):
        if n is not fn and isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                          ast.Lambda)):
            for sub in ast.walk(n):
                nested.add(id(sub))
    for n in ast.walk(fn):
        if isinstance(n, ast.Return) and id(n) not in nested:
            out.append(n)
    return out


def expr_kind(e):
    """Classify an exit-code expression."""
    if e is None:
        return "const"                     # implicit None -> status 0
    if isinstance(e, ast.Constant):
        return "const"
    if isinstance(e, ast.IfExp):
        # An IfExp is data-dependent if EITHER its test OR any arm is
        # data-dependent.  `0 if ok else 1` has constant arms but a live test.
        if expr_kind(e.test) != "const":
            return "data"
        a, b = expr_kind(e.body), expr_kind(e.orelse)
        return "const" if a == b == "const" else "data"
    if isinstance(e, ast.BoolOp):
        ks = [expr_kind(v) for v in e.values]
        return "data" if "data" in ks else ks[0]
    if isinstance(e, ast.UnaryOp):
        return expr_kind(e.operand)
    if isinstance(e, ast.NamedExpr):
        return expr_kind(e.value)
    if isinstance(e, ast.Call) and isinstance(e.func, ast.Name):
        return "func:" + e.func.id
    return "data"


def resolve_expr(e, fdefs, seen=None):
    """Resolve 'const' / 'data' / 'unresolved' for an exit argument."""
    seen = seen or set()
    k = expr_kind(e)
    if k in ("const", "data"):
        return k
    if k.startswith("func:"):
        name = k[5:]
        if name in seen:
            return "unresolved"
        seen.add(name)
        results = []
        for fn in fdefs.get(name, []):
            rs = own_returns(fn)
            if not rs:
                results.append("const")    # no return -> None -> 0
            for r in rs:
                results.append(resolve_expr(r.value, fdefs, seen))
        if not results:
            return "unresolved"            # external function: unknown
        if all(x == "const" for x in results):
            return "const"
        if any(x == "data" for x in results):
            return "data"
        return "unresolved"
    return "data"


def top_level_owner(tree, node):
    """Which top-level statement encloses node (orchestrator reports its lineno)."""
    for top in tree.body:
        if any(sub is node for sub in ast.walk(top)):
            return top
    return None


def analyse(rel, raw):
    text = raw.decode("utf-8-sig", errors="replace")
    tree = ast.parse(text)
    fdefs = func_defs(tree)
    parents = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            parents[id(c)] = n

    def enclosing_func(n):
        p = parents.get(id(n))
        while p is not None:
            if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                return p
            p = parents.get(id(p))
        return None

    sites = []
    for n in ast.walk(tree):
        # E1: exit() family
        if isinstance(n, ast.Call):
            nm = dotted(n.func)
            if nm in EXIT_FUNCS:
                arg = n.args[0] if n.args else None
                sites.append(dict(line=n.lineno, kind="E1:" + nm,
                                  expr=ast.unparse(arg) if arg else "None",
                                  resolved=resolve_expr(arg, fdefs),
                                  in_func=(enclosing_func(n).name
                                           if enclosing_func(n) else None)))
        # E2: raise SystemExit
        if is_systemexit_raise(n):
            e = n.exc
            arg = e.args[0] if (isinstance(e, ast.Call) and e.args) else None
            sites.append(dict(line=n.lineno, kind="E2:raise SystemExit",
                              expr=ast.unparse(arg) if arg else "None",
                              resolved=resolve_expr(arg, fdefs),
                              in_func=(enclosing_func(n).name
                                       if enclosing_func(n) else None)))

    flags = []
    if any(s["kind"].startswith("E2:") for s in sites):
        flags.append("RAISE_SYSTEMEXIT")
    if any(s["kind"].startswith("E1:") for s in sites) and any(
            s["kind"].startswith("E2:") for s in sites):
        flags.append("MIXED_RAISE_AND_EXIT")
    if any(s["in_func"] for s in sites):
        flags.append("EXIT_IN_NONMAIN_FUNC")
    for fnlist in fdefs.values():
        for fn in fnlist:
            if any(isinstance(r.value, ast.IfExp) for r in own_returns(fn)
                   if r.value is not None):
                if "IFEXP_RETURN" not in flags:
                    flags.append("IFEXP_RETURN")
    # constant-condition exits: `if True:` / `if 1:` enclosing an exit site
    for n in ast.walk(tree):
        if isinstance(n, ast.If) and isinstance(n.test, ast.Constant):
            for s in sites:
                if n.lineno <= s["line"] <= getattr(n, "end_lineno", n.lineno):
                    if "CONST_COND_EXIT" not in flags:
                        flags.append("CONST_COND_EXIT")
    # bare raise / assert with no E1/E2
    has_assert = any(isinstance(n, ast.Assert) for n in ast.walk(tree))
    bare_raise = any(isinstance(n, ast.Raise) and n.exc is None
                    for n in ast.walk(tree))
    if has_assert and not sites:
        flags.append("ASSERT_ONLY")
    if bare_raise:
        flags.append("BARE_RAISE")
    if any(isinstance(n, ast.Call) and dotted(n.func) == "atexit.register"
           for n in ast.walk(tree)):
        flags.append("ATEXIT")
    # verdict written to a file but no exit site (fifth form)
    writes = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and (
        (isinstance(n.func, ast.Attribute) and n.func.attr in
         ("write_text", "write", "dump")) or
        (isinstance(n.func, ast.Name) and n.func.id in ("open",)))]
    if not sites and writes:
        flags.append("FILE_ONLY_VERDICT")

    # independent classification
    if not sites:
        cls = "NO_EXIT_AT_ALL"
    elif any(s["resolved"] == "data" for s in sites):
        cls = "CONDITIONAL_EXIT"
    elif any(s["resolved"] == "unresolved" for s in sites):
        cls = "UNRESOLVED_EXIT"
    else:
        cls = "CONSTANT_EXIT"

    # orchestrator artefact: which lineno would it report for the first site
    top_lines = []
    for s in sites[:1]:
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and dotted(n.func) in EXIT_FUNCS \
                    and n.lineno == s["line"]:
                t = top_level_owner(tree, n)
                top_lines.append((s["line"], t.lineno if t else None))
                break

    return dict(rel=rel, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                cls=cls, n_sites=len(sites), sites=sites, flags=flags,
                top_line_map=top_lines,
                n_funcs=sum(len(v) for v in fdefs.values()),
                dup_func_names=sorted(k for k, v in fdefs.items() if len(v) > 1))


def main():
    # same enumeration as orchestrator, for comparability
    idx = {}
    for base, lim in (("lead", 99), ("out", 3)):
        for dp, dn, fn in os.walk(base):
            dn[:] = [d for d in dn if d not in ("__pycache__", ".git")]
            rel = os.path.relpath(dp, base)
            d = 0 if rel == "." else rel.count(os.sep) + 1
            if d >= lim:
                dn[:] = []
            for f in fn:
                if f.endswith(".py"):
                    idx.setdefault(f, []).append(
                        os.path.join(dp, f).replace("\\", "/"))
    pat = re.compile(r"([A-Za-z0-9_./\-]+\.py)")
    mark = re.compile(r"PASS|exit\s*=\s*0|EXIT=0|SELF_TEST")
    cited = {}
    for dp, dn, fn in os.walk("lead"):
        dn[:] = [d for d in dn if d not in ("__pycache__", ".git")]
        if dp.count(os.sep) > 5:
            dn[:] = []
        for f in fn:
            if not f.endswith(".md"):
                continue
            p = os.path.join(dp, f).replace("\\", "/")
            try:
                t = open(p, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            for i, l in enumerate(t.split("\n"), 1):
                if not mark.search(l):
                    continue
                for m in pat.finditer(l):
                    b = os.path.basename(m.group(1).replace("\\", "/"))
                    e = cited.setdefault(b, {"files": set(), "n": 0})
                    e["files"].add(p)
                    e["n"] += 1
    kd = json.load(open("lead/k1bit_detect_20261109/_kd_detect_out.json",
                        encoding="utf-8"))
    census = {os.path.basename(r["rel"]) for r in kd["rows"]}
    targets = sorted(b for b in cited if b in idx and b not in census)

    rows, errs = [], []
    for b in targets:
        p = idx[b][0]
        try:
            rows.append(dict(basename=b, **analyse(p, Path(p).read_bytes())))
        except Exception as ex:
            errs.append((b, p, type(ex).__name__, str(ex)[:120]))

    orch = json.load(open(WD / "_ce_orchestrator_raw.json", encoding="utf-8"))
    ocls = {}
    for r in orch["const_or_noexit"]:
        ocls[r["rel"]] = r["cls"]
    for r in orch["conditional"]:
        ocls[r["rel"]] = "CONDITIONAL_EXIT"

    diffs = []
    for r in rows:
        o = ocls.get(r["rel"])
        if o != r["cls"]:
            diffs.append(dict(rel=r["rel"], orchestrator=o, independent=r["cls"],
                              flags=r["flags"], sites=r["sites"][:4],
                              dup_func_names=r["dup_func_names"]))
    out = dict(n_targets=len(targets), n_rows=len(rows), n_errs=len(errs),
               errors=errs,
               classes=dict(Counter(r["cls"] for r in rows)),
               flag_counts=dict(Counter(f for r in rows for f in r["flags"])),
               n_diff=len(diffs), diffs=diffs, rows=rows)
    (WD / "_ce_audit_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(dict(n_targets=len(targets), n_rows=len(rows),
                          n_errs=len(errs), errors=errs,
                          classes=out["classes"],
                          flag_counts=out["flag_counts"],
                          n_diff=len(diffs)), ensure_ascii=False, indent=1))
    print("WROTE", (WD / "_ce_audit_out.json").as_posix())


if __name__ == "__main__":
    main()
