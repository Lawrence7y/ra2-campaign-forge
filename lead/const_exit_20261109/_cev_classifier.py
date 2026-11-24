# -*- coding: utf-8 -*-
"""_cev_classifier.py -- INDEPENDENT exit-status classifier for the review.

Written from scratch for the "常量出口复核员" task.  It deliberately does NOT
reuse _ce_repro.py / _ce_final.py / _ce_rule_audit.py logic from the audited
agent.  Design:

  1. Re-enumerate the cited-basename batch from lead/**.md with the same
     textual definition given in the task (mark regex + .py token regex),
     resolve via a fresh filesystem index, exclude the kd census basenames.

  2. For each file, build an AST and collect *all* process-exit sites:
       - Call to sys.exit / exit / quit / os._exit (any dotted tail)
       - Raise whose exception is SystemExit(...) / bare SystemExit
     Sites are collected with their own lineno (not the top-level stmt line).

  3. For each site, compute the set of ATTAINABLE EXIT STATUSES with a
     constant-propagation evaluator (constants, constant IfExp/BoolOp/
     UnaryOp/Tuple, Name resolved from a per-scope constant map, Call to a
     local function resolved from that function's OWN returns only).  A
     data-dependent expression yields the DATA marker.

  4. Control-flow: a conditionally-reached nonzero site adds status 0
     (the fall-through / normal-termination path).  Unconditional sites do
     not.  A site inside try/except that catches SystemExit/BaseException is
     recorded as a swallowed-site caveat.

  5. Three-way verdict from the attainable status set:
       no site                -> NO_EXIT_AT_ALL
       DATA or >=2 statuses   -> CONDITIONAL_EXIT
       exactly 1 status       -> CONSTANT_EXIT

  Mechanical verdicts are reported as-is; the human/AST adjudication for
  any disagreement is done separately in the review text.

Read-only over the repo: only writes files in lead/const_exit_20261109/ with
the _cev_ prefix.  Never executes a checked script or a checked gate.
"""
import ast
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.dont_write_bytecode = True
ROOT = r"D:/Project/ra2-campaign-forge"
WD = os.path.join(ROOT, "lead", "const_exit_20261109")
os.chdir(ROOT)

# ---------------------------------------------------------------- batch ----
PAT_PY = re.compile(r"([A-Za-z0-9_./\-]+\.py)")
MARK = re.compile(r"PASS|exit\s*=\s*0|EXIT=0|SELF_TEST")


def build_index():
    idx = defaultdict(list)
    for base, lim in (("lead", 99), ("out", 3)):
        for dp, dn, fn in os.walk(base):
            dn[:] = [d for d in dn if d not in ("__pycache__", ".git")]
            rel = os.path.relpath(dp, base)
            depth = 0 if rel == "." else rel.count(os.sep) + 1
            if depth >= lim:
                dn[:] = []
            for f in fn:
                if f.endswith(".py"):
                    idx[f].append(os.path.join(dp, f).replace("\\", "/"))
    return idx


def build_cited():
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
                if not MARK.search(l):
                    continue
                for m in PAT_PY.finditer(l):
                    b = os.path.basename(m.group(1).replace("\\", "/"))
                    e = cited.setdefault(b, {"files": set(), "n": 0})
                    e["files"].add(p)
                    e["n"] += 1
    return cited


# ------------------------------------------------------------------ AST ----
EXIT_CALL_TAILS = {"exit", "quit", "_exit"}
RAISE_NAMES = {"SystemExit", "builtins.SystemExit"}
DATA = "__DATA__"


def dotted(n):
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Attribute):
        p = dotted(n.value)
        return (p + "." + n.attr) if p else n.attr
    return ""


def status_of_const(v):
    if v is None:
        return 0
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, int):
        return v
    return 1  # str / bytes / anything else -> shell shows 1


class OwnReturns(ast.NodeVisitor):
    """Return statements belonging to THIS function only (skip nested defs)."""

    def __init__(self, root):
        self.root = root
        self.out = []

    def visit_Return(self, node):
        self.out.append(node)

    def visit_FunctionDef(self, node):
        if node is not self.root:
            return

    def visit_AsyncFunctionDef(self, node):
        if node is not self.root:
            return

    def visit_Lambda(self, node):
        return

    def generic_visit(self, node):
        for c in ast.iter_child_nodes(node):
            self.visit(c)


def own_returns(fn):
    v = OwnReturns(fn)
    for stmt in fn.body:
        v.visit(stmt)
    return v.out


def func_defs(tree):
    d = defaultdict(list)
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            d[n.name].append(n)
    return d


def module_const_map(tree):
    """Conservative module-level constant propagation: only simple literal
    assignments that are never re-assigned to a non-literal anywhere."""
    m = {}
    assigned_nonconst = set()
    for top in tree.body:
        if isinstance(top, (ast.Assign, ast.AnnAssign)):
            tgts = top.targets if isinstance(top, ast.Assign) else [top.target]
            val = top.value
            for t in tgts:
                if isinstance(t, ast.Name):
                    if isinstance(val, ast.Constant):
                        m.setdefault(t.id, val)
                    else:
                        assigned_nonconst.add(t.id)
        # any other binding of the name invalidates it
        for n in ast.walk(top):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                if not (isinstance(top, (ast.Assign, ast.AnnAssign)) and
                        isinstance(top.value, ast.Constant)):
                    assigned_nonconst.add(n.id)
    def safe(v):
        return v if isinstance(v, (int, float, bool, str, type(None))) else repr(v)
    return {k: safe(v.value) for k, v in m.items() if k not in assigned_nonconst}


def eval_status(e, fdefs, cmap, seen=None):
    """Return (set_of_statuses, has_data).  Independent constant evaluator."""
    seen = set() if seen is None else set(seen)
    if e is None:
        return {0}, False
    if isinstance(e, ast.Constant):
        return {status_of_const(e.value)}, False
    if isinstance(e, ast.Name):
        if e.id in cmap:
            return {status_of_const(cmap[e.id])}, False
        return set(), True
    if isinstance(e, ast.UnaryOp) and isinstance(e.op, (ast.USub, ast.UAdd, ast.Invert)):
        s, d = eval_status(e.operand, fdefs, cmap, seen)
        if d:
            return set(), True
        return {(-v if isinstance(e.op, ast.USub) else
                 (+v if isinstance(e.op, ast.UAdd) else ~v)) for v in s}, False
    if isinstance(e, ast.IfExp):
        ts, td = eval_status(e.test, fdefs, cmap, seen)
        bs, bd = eval_status(e.body, fdefs, cmap, seen)
        os_, od = eval_status(e.orelse, fdefs, cmap, seen)
        if td or bd or od:
            return set(), True
        # constant test: Python truthiness decides the arm
        arm = bs if all(v != 0 for v in ts) else os_
        return arm, False
    if isinstance(e, ast.BoolOp):
        parts = [eval_status(v, fdefs, cmap, seen) for v in e.values]
        if any(d for _, d in parts):
            return set(), True
        vals = set()
        for s, _ in parts:
            vals |= s
        # short-circuit: result can be one of the operand values
        return vals, False
    if isinstance(e, (ast.Tuple, ast.List)):
        # SystemExit(tuple) -> status 1 with a message; still a literal
        return {1}, False
    if isinstance(e, ast.Call) and isinstance(e.func, ast.Name):
        name = e.func.id
        if name in ("int", "str", "bool") and e.args:
            return eval_status(e.args[0], fdefs, cmap, seen)
        if name in fdefs and name not in seen:
            seen = seen | {name}
            sts, data = set(), False
            for fn in fdefs[name]:
                rs = own_returns(fn)
                if not rs:
                    sts.add(0)
                for r in rs:
                    s, d = eval_status(r.value, fdefs, cmap, seen)
                    sts |= s
                    data |= d
            return sts, data
        return set(), True
    return set(), True


def collect_sites(tree):
    """All exit sites with their own lineno, expression and parents."""
    parents = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            parents[id(c)] = n
    sites = []
    for n in ast.walk(tree):
        kind, arg = None, None
        if isinstance(n, ast.Call):
            d = dotted(n.func)
            tail = d.rsplit(".", 1)[-1]
            if tail in EXIT_CALL_TAILS and (d in ("sys.exit", "exit", "quit", "os._exit") or
                                            d.startswith("sys.") or d.startswith("os.")):
                kind = "call:" + d
                arg = n.args[0] if n.args else None
        elif isinstance(n, ast.Raise) and n.exc is not None:
            e = n.exc
            if isinstance(e, ast.Call) and dotted(e.func) in RAISE_NAMES:
                kind = "raise:SystemExit(...)"
                arg = e.args[0] if e.args else None
            elif dotted(e) in RAISE_NAMES:
                kind = "raise:SystemExit"
                arg = None
        if kind is None:
            continue
        # conditional reachability: any controlling ancestor
        ctrl, p = [], parents.get(id(n))
        swallowed = False
        while p is not None:
            if isinstance(p, (ast.If, ast.Try, ast.For, ast.AsyncFor, ast.While,
                              ast.With, ast.AsyncWith, ast.IfExp, ast.BoolOp)):
                ctrl.append(type(p).__name__)
            if isinstance(p, ast.ExceptHandler):
                swallowed = True
            if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                ctrl.append("IN_FUNC:" + getattr(p, "name", "<lambda>"))
            p = parents.get(id(p))
        sites.append(dict(line=n.lineno, kind=kind,
                          expr=ast.unparse(arg) if arg is not None else "None",
                          arg=arg, controls=ctrl, swallowed=swallowed))
    return sites, parents


def top_level_exception_channels(tree):
    """Report (not fold) module-level assert / bare-raise channels."""
    out = []
    for top in tree.body:
        for n in ast.walk(top):
            if isinstance(n, (ast.Assert, ast.Raise)):
                # only those not inside a function definition
                inside = False
                for q in ast.walk(top):
                    if isinstance(q, (ast.FunctionDef, ast.AsyncFunctionDef)) and q is not n:
                        # cheap check via nesting is done by caller; keep coarse
                        pass
                out.append((n.lineno, type(n).__name__))
    return out


def analyse(rel):
    raw = open(rel, "rb").read()
    tree = ast.parse(raw.decode("utf-8-sig", errors="replace"))
    fdefs = func_defs(tree)
    cmap = module_const_map(tree)
    sites, parents = collect_sites(tree)
    status_set, any_data = set(), False
    site_detail = []
    for s in sites:
        sts, d = eval_status(s["arg"], fdefs, cmap)
        any_data |= d
        status_set |= sts
        cond = any(c and not c.startswith("IN_FUNC") for c in s["controls"])
        if cond and any(v != 0 for v in sts):
            status_set.add(0)
        site_detail.append({k: s[k] for k in ("line", "kind", "expr", "controls", "swallowed")}
                           | {"statuses": sorted(sts), "data": d, "conditional_reach": cond})
    if any_data:
        status_set |= {0, 1}
    if not sites:
        cls = "NO_EXIT_AT_ALL"
    elif any_data or len(status_set) > 1:
        cls = "CONDITIONAL_EXIT"
    else:
        cls = "CONSTANT_EXIT"
    return dict(rel=rel, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                cls=cls, statuses=sorted(status_set), any_data=any_data,
                n_sites=len(sites), sites=site_detail,
                const_map=cmap,
                n_funcdefs=sum(len(v) for v in fdefs.values()))


def main():
    # --batch: classify EXACTLY the 413 rels of the orchestrator's run (read
    # from the archived raw JSON), so the "same batch" comparison is fair even
    # though the repo's .md corpus has grown since that run.
    exact = "--batch" in sys.argv
    idx = build_index()
    cited = build_cited()
    kd = json.load(open("lead/k1bit_detect_20261109/_kd_detect_out.json", encoding="utf-8"))
    census = {os.path.basename(r["rel"]) for r in kd["rows"]}
    if exact:
        o = json.load(open(os.path.join(WD, "_ce_orchestrator_raw.json"), encoding="utf-8"))
        rels = sorted(set([r["rel"] for r in o["const_or_noexit"]] +
                          [r["rel"] for r in o["conditional"]]))
        todo = [(os.path.basename(r), r) for r in rels]
    else:
        todo = [(b, idx[b][0]) for b in sorted(cited)
                if b in idx and b not in census]
    batch = []
    unread, unparse = [], []
    for b, rel in todo:
        try:
            r = analyse(rel)
        except SyntaxError as ex:
            unparse.append([b, rel, str(ex)[:100]])
            continue
        except Exception as ex:
            unread.append([b, rel, repr(ex)[:100]])
            continue
        r["basename"] = b
        r["cites"] = cited[b]["n"]
        batch.append(r)
    out = dict(n_cited_basenames=len(cited), n_batch=len(batch),
               n_unread=len(unread), n_unparseable=len(unparse),
               unread=unread, unparseable=unparse,
               classes=dict(Counter(r["cls"] for r in batch)),
               rows=batch)
    with open(os.path.join(WD, "_cev_batch_out.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("n_cited_basenames", len(cited), "n_batch", len(batch),
          "unread", len(unread), "unparseable", len(unparse),
          "classes", out["classes"])


if __name__ == "__main__":
    main()
