# -*- coding: utf-8 -*-
"""_kd_detect.py -- semantic (AST + dataflow) k->1bit detector.

Read-only over the repository; writes ONLY into lead/k1bit_detect_20261109/.

Semantic definition (NOT "uses any()"):
  A self-test has k>=2 HOMOGENEOUS INPUTS (needles / keywords / patterns /
  cases) whose joint validity should be proven (forall i: input_i alive).  The
  code instead observes only  exists i: match(input_i, x)  and compresses that
  observation into ONE BIT (PASS / FAIL / ok / a single scalar position),
  retaining NO per-input attribution (no hits=[...], no per-needle print).
  => "input_1 dead but every sample hit by input_{j!=1}" is observationally
     equivalent to "all k alive".  Per-input attributability = NO.

  DISTINGUISHABLE_PASS = AND_k(REAL per-input self-test)   [CHECK_MASKING_INJECT.md:450]

Operational predicate, four structural/dataflow signals:
  S1 KSOURCE   : a literal collection of >=2 string tokens, OR a requirements
                 table row carrying such a collection, OR an argparse
                 action="append" accumulator.  Dataflow propagates these into
                 names (assignments, for-unpacking, function parameters).
  S2 COLLAPSE  : an EXISTENTIAL / lossy reduction whose quantified variable
                 ranges over that k-token collection and whose element is a
                 match test on that variable:
                   any(GeneratorExp/ListComp), any(Name) where Name is bound
                   to such a comprehension, IfExp OR/AND ternary, min()/max()
                   argmin over tokens (reverse masking), ok &= good / AND-fold.
  S3 ONEBIT    : one aggregate PASS/SELF_TEST exit, return 0/1 or exit(main()),
                 with NO per-TOKEN print loop and NO retained hits[].
  S4 LEGAL     : all() over the k tokens (requires ALL => no OR loss), OR
                 existential quantification over SAMPLES/BODIES with a single
                 fixed literal predicate (a genuine "does any document contain
                 this one token" check), OR count-preserving reduction
                 (sum/len/counter), OR per-token attribution present.
                 LEGAL suppresses the finding.

Usage:
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/k1bit_detect_20261109/_kd_detect.py D:/Project/ra2-campaign-forge
  python -I -X utf8 .../_kd_detect.py D:/Project/ra2-campaign-forge --one path/to/file.py
"""
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

WD_NAME = "lead/k1bit_detect_20261109"
TOKENISH = re.compile(
    r"(word|keyword|needle|token|pattern|case|kw|tok|hit|offset|exclude)", re.I)
SAMPLEISH = re.compile(
    r"(bod|sect|line|file|doc|text|content|error|item|row|sample|match|"
    r"carrier|case|check|head|para|record|entry|result|unverified|fail)", re.I)


# ---------------------------------------------------------------- helpers
def str_consts(node):
    return [e.value for e in ast.walk(node)
            if isinstance(e, ast.Constant) and isinstance(e.value, str)]


def literal_str_collection(node):
    """A Tuple/List whose direct elements are >= 1 string constants."""
    if isinstance(node, (ast.Tuple, ast.List)) and node.elts:
        ss = [e.value for e in node.elts
              if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        if len(ss) == len(node.elts) and ss:
            return ss
    return None


def table_rows(expr):
    """Return the rows of a literal tuple/list-of-tuples requirements table."""
    if isinstance(expr, (ast.Tuple, ast.List)) and expr.elts and all(
            isinstance(e, (ast.Tuple, ast.List)) for e in expr.elts):
        return list(expr.elts)
    return []


def target_names(node):
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        out = []
        for e in node.elts:
            out.extend(target_names(e))
        return out
    return []


def name_ids(node):
    return [n.id for n in ast.walk(node) if isinstance(n, ast.Name)]


def is_in_compare(node):
    return isinstance(node, ast.Compare) and any(
        isinstance(op, (ast.In, ast.NotIn)) for op in node.ops)


def is_passish(call):
    """A POSITIVE aggregate verdict print.  Exclude pure FAIL/RESULT: FAIL."""
    seg = " ".join(str_consts(call))
    return bool(re.search(r"\bPASS\b|SELF_TEST|\bOK\b", seg, re.I))


def is_print(call):
    return (isinstance(call.func, ast.Name) and call.func.id == "print") or (
        isinstance(call.func, ast.Name) and call.func.id == "P")


# ------------------------------------------------- S1: dataflow of k-sources
def build_bindings(tree):
    """name -> list of (lineno, value_expr).  Module-wide, source-ordered."""
    b = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    b.setdefault(t.id, []).append((n.lineno, n.value))
                elif isinstance(t, ast.Tuple):
                    vals = n.value.elts if isinstance(n.value, (ast.Tuple, ast.List)) else []
                    for i, e in enumerate(t.elts):
                        if isinstance(e, ast.Name) and i < len(vals):
                            b.setdefault(e.id, []).append((n.lineno, vals[i]))
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value:
            b.setdefault(n.target.id, []).append((n.lineno, n.value))
    for k in b:
        b[k].sort(key=lambda x: x[0])
    return b


def resolve(name, bindings):
    return [v for _, v in bindings.get(name, [])]


def collect_ksources(tree, bindings):
    """Return {token_name: {'k': int|'runtime', 'why': str, 'line': int}}."""
    tok = {}

    def mark(name, k, why, line):
        if not name:
            return
        old = tok.get(name)
        if old is None or (old["k"] != "runtime" and (k == "runtime" or
                           isinstance(k, int) and isinstance(old["k"], int) and k > old["k"])):
            tok[name] = dict(k=k, why=why, line=line)

    # (1) direct assignment to a literal string collection
    for name, vals in bindings.items():
        for v in vals:
            ss = literal_str_collection(v)
            if ss and len(ss) >= 2:
                mark(name, len(ss), "assign_literal_str_collection", getattr(v, "lineno", 0))
            rows = table_rows(v)
            if rows:
                for r in rows:
                    for e in r.elts:
                        ss = literal_str_collection(e)
                        if ss and len(ss) >= 2:
                            mark(name, len(ss), "requirements_table_row", getattr(v, "lineno", 0))

    # (2) for-unpacking from a literal requirements table (assigned or inline)
    for n in ast.walk(tree):
        if not isinstance(n, ast.For):
            continue
        srcs = [n.iter]
        if isinstance(n.iter, ast.Name):
            srcs += resolve(n.iter.id, bindings)
        rows = []
        for s in srcs:
            rows += table_rows(s)
        if not rows or not isinstance(n.target, (ast.Tuple, ast.List)):
            continue
        tnames = target_names(n.target)
        maxk = 0
        for r in rows:
            for i, e in enumerate(r.elts):
                ss = literal_str_collection(e)
                if ss:
                    maxk = max(maxk, len(ss))
        if maxk < 2:
            continue
        for r in rows:
            for i, e in enumerate(r.elts):
                ss = literal_str_collection(e)
                if ss and i < len(tnames):
                    mark(tnames[i], maxk, "for_unpack_token_row", n.lineno)

    # (3) argparse action="append" accumulators (needles at runtime, k>=2)
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call) or not isinstance(n.func, ast.Attribute):
            continue
        if n.func.attr != "add_argument":
            continue
        kw = {k.arg: k.value for k in n.keywords}
        act = kw.get("action")
        if not (isinstance(act, ast.Constant) and act.value == "append"):
            continue
        opt = n.args[0] if n.args else None
        if isinstance(opt, ast.Constant) and isinstance(opt.value, str):
            dest = opt.value.lstrip("-").replace("-", "_")
            mark(dest, "runtime", "argparse_action_append", n.lineno)
            # also record <namespace>.<dest> via attribute attr matching below

    # (4) interprocedural: map function parameters to token-ish arguments
    funcs = {f.name: f for f in ast.walk(tree) if isinstance(f, ast.FunctionDef)}
    for _ in range(2):  # two passes for simple call chains
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in funcs:
                f = funcs[n.func.id]
                params = [a.arg for a in f.args.args]
                for p, arg in zip(params, n.args):
                    an = arg.id if isinstance(arg, ast.Name) else (
                        arg.attr if isinstance(arg, ast.Attribute) else None)
                    if an in tok:
                        mark(p, tok[an]["k"], "param_from_" + tok[an]["why"], n.lineno)
    return tok


def is_token_source(expr, tokens):
    """Is this comprehension iterable a k-token collection?"""
    if isinstance(expr, ast.Name) and expr.id in tokens:
        return True, expr.id
    if isinstance(expr, ast.Attribute) and expr.attr in tokens:
        return True, expr.attr
    if isinstance(expr, (ast.Name, ast.Attribute)):
        nm = expr.id if isinstance(expr, ast.Name) else expr.attr
        if TOKENISH.search(nm):
            return True, nm
    ss = literal_str_collection(expr)
    if ss and len(ss) >= 2:
        return True, "<literal>"
    return False, None


# ------------------------------------------------------- S2: collapse sites
def token_clauses(comp, tokens):
    """Yield (target_var_names, source_name, k) for each token-quantified clause."""
    out = []
    for g in comp.generators:
        ok, src = is_token_source(g.iter, tokens)
        if ok:
            tv = set(target_names(g.target))
            if tv:
                k = tokens.get(src, {}).get("k", "?") if src in tokens else "?"
                out.append((tv, src, k))
    return out


def elt_matches_token(elt, tvars):
    """Is the comprehension element a match test ON the token variable?"""
    if elt is None:
        return False
    if isinstance(elt, ast.Compare) and is_in_compare(elt):
        return bool(set(name_ids(elt)) & tvars)
    if isinstance(elt, ast.BoolOp):
        return any(elt_matches_token(v, tvars) for v in elt.values)
    if isinstance(elt, ast.UnaryOp):
        return elt_matches_token(elt.operand, tvars)
    if isinstance(elt, ast.IfExp):
        return (elt_matches_token(elt.body, tvars) or
                elt_matches_token(elt.orelse, tvars))
    if isinstance(elt, ast.Call):
        if isinstance(elt.func, ast.Name) and elt.func.id in ("any", "all"):
            return any(comp_matches_token(a, tvars) for a in elt.args
                       if isinstance(a, (ast.GeneratorExp, ast.ListComp)))
        # line.find(n) / re.search(n, ...) : token var used as the probe
        if set(name_ids(elt)) & tvars:
            return True
    return False


def comp_matches_token(comp, tvars):
    if not isinstance(comp, (ast.GeneratorExp, ast.ListComp)):
        return False
    if elt_matches_token(comp.elt, tvars):
        return True
    # nested comprehension in the element (d29/d30 matches = [IfExp(...) ...])
    for sub in ast.walk(comp.elt):
        if isinstance(sub, (ast.GeneratorExp, ast.ListComp)) and sub is not comp:
            if elt_matches_token(sub.elt, tvars | set(
                    target_names(sub.generators[0].target) if sub.generators else [])):
                return True
    return False


def analyse_calls(tree, tokens, bindings):
    """Return (collapse_sites, legal_sites)."""
    coll, legal = [], []

    def record(kind, n, expr, quant, k):
        coll.append(dict(line=n.lineno, kind=kind, quantifies=quant, k=k,
                         expr=ast.unparse(expr)[:180]))

    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            fn = n.func.id
            a = n.args[0] if n.args else None
            # ---- any()
            if fn == "any":
                if isinstance(a, (ast.GeneratorExp, ast.ListComp)):
                    cls = token_clauses(a, tokens)
                    hit = [(tv, src, k) for tv, src, k in cls
                           if comp_matches_token(a, tv)]
                    if hit:
                        record("OR_COLLAPSE_gen", n, n,
                               "k_tokens", hit[0][2])
                    else:
                        legal.append(dict(line=n.lineno, kind="any_over_samples",
                                          expr=ast.unparse(n)[:140],
                                          why="quantifies over samples/bodies with a "
                                              "fixed predicate, not over k inputs"))
                elif isinstance(a, ast.Name):
                    resolved = resolve(a.id, bindings)
                    hit = False
                    for v in resolved:
                        if isinstance(v, ast.ListComp):
                            cls = token_clauses(v, tokens)
                            for tv, src, k in cls:
                                if comp_matches_token(v, tv):
                                    record("OR_COLLAPSE_bound_list", n, n,
                                           "k_tokens(via %s)" % a.id, k)
                                    hit = True
                                    break
                        # d29/d30: matches = [ IfExp(all(...), any(...)) for body ]
                        if isinstance(v, ast.ListComp):
                            for sub in ast.walk(v.elt):
                                if (isinstance(sub, ast.Call) and
                                        isinstance(sub.func, ast.Name) and
                                        sub.func.id == "any" and sub.args and
                                        isinstance(sub.args[0],
                                                   (ast.GeneratorExp, ast.ListComp))):
                                    sc = token_clauses(sub.args[0], tokens)
                                    for tv, src, k in sc:
                                        if elt_matches_token(sub.args[0].elt, tv):
                                            record("OR_COLLAPSE_ternary_list", n, n,
                                                   "k_tokens(via %s)" % a.id, k)
                                            hit = True
                                            break
                    if not hit:
                        legal.append(dict(line=n.lineno, kind="any_over_name",
                                          expr=ast.unparse(n)[:140],
                                          why="bound name is not a k-token match list"))
                else:
                    legal.append(dict(line=n.lineno, kind="any_other",
                                      expr=ast.unparse(n)[:140], why="unresolved arg"))
            # ---- all(): LEGAL (requires every input, no OR loss)
            elif fn == "all":
                legal.append(dict(line=n.lineno, kind="AND_aggregate",
                                  expr=ast.unparse(n)[:140],
                                  why="all() requires every input => AND_k, no OR loss"))
            # ---- min()/max() argmin over k tokens = reverse masking
            elif fn in ("min", "max"):
                if isinstance(a, (ast.GeneratorExp, ast.ListComp)):
                    cls = token_clauses(a, tokens)
                    for tv, src, k in cls:
                        if elt_matches_token(a.elt, tv):
                            record("ARGMIN_REVERSE_MASK", n, n, "k_tokens", k)
                            break
                else:
                    legal.append(dict(line=n.lineno, kind="minmax_scalar",
                                      expr=ast.unparse(n)[:140], why="no token generator"))
            # ---- count-preserving reductions
            elif fn in ("sum", "len", "sorted"):
                legal.append(dict(line=n.lineno, kind="count_preserving",
                                  expr=ast.unparse(n)[:100],
                                  why="cardinality/order retained, not 1 bit"))

        # ---- ternary OR/AND mixed: all(present) if require_all else any(present)
        if isinstance(n, ast.IfExp):
            for branch, tag in ((n.body, "if"), (n.orelse, "else")):
                if (isinstance(branch, ast.Call) and isinstance(branch.func, ast.Name)
                        and branch.func.id == "any" and branch.args
                        and isinstance(branch.args[0], ast.Name)):
                    nm = branch.args[0].id
                    for v in resolve(nm, bindings):
                        if isinstance(v, ast.ListComp) and token_clauses(v, tokens):
                            coll.append(dict(line=n.lineno,
                                             kind="TERNARY_OR_BRANCH",
                                             quantifies="k_tokens(via %s)" % nm,
                                             k=token_clauses(v, tokens)[0][2],
                                             expr=ast.unparse(n)[:180]))

        # ---- ok &= good / ok = ok and good : 1-bit accumulation
        if isinstance(n, ast.AugAssign) and isinstance(n.op, (ast.BitAnd,)):
            coll.append(dict(line=n.lineno, kind="BIT_ACCUM_AugAssign_BitAnd",
                             quantifies="aggregate_cases", k="?",
                             expr=ast.unparse(n)[:120]))
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.BoolOp) and isinstance(
                n.value.op, ast.And):
            if any(isinstance(t, ast.Name) and t.id in ("ok", "all_ok", "passed")
                   for t in n.targets if isinstance(t, ast.Name)):
                coll.append(dict(line=n.lineno, kind="BIT_ACCUM_bool_and",
                                 quantifies="aggregate_cases", k="?",
                                 expr=ast.unparse(n)[:120]))
    return coll, legal


# -------------------------------------------- S3/S4: one bit + attribution
def analyse_output(tree, tokens):
    loop_nodes = [n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While, ast.AsyncFor))]
    parent_loop = {}
    for lp in loop_nodes:
        for sub in ast.walk(lp):
            if sub is not lp:
                parent_loop.setdefault(id(sub), []).append(lp)

    agg_pass, per_token_print, per_any_print = [], [], []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and is_print(n) and is_passish(n):
            lps = parent_loop.get(id(n), [])
            tv_loops = []
            for lp in lps:
                if isinstance(lp, (ast.For, ast.AsyncFor)):
                    tv = set(target_names(lp.target))
                    # per-TOKEN print only if loop variable is a token var
                    if tv & set(tokens) or any(TOKENISH.search(x) for x in tv):
                        tv_loops.append((lp.lineno, sorted(tv)))
            if tv_loops:
                per_token_print.append(dict(line=n.lineno, loops=tv_loops))
            elif lps:
                per_any_print.append(n.lineno)
            else:
                agg_pass.append(n.lineno)

    # retained per-input attribution: hits / hit_set / per_needle structure
    hits_retained = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and re.search(
                        r"^(hits|hit_set|hitset|matched_needles|per_needle|"
                        r"hitmap|hit_list|which_needle|argmin)$", t.id, re.I):
                    hits_retained.append(dict(line=n.lineno, name=t.id))
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name):
            if re.search(r"hits|hit_set|per_needle|hitmap", n.value.id, re.I):
                hits_retained.append(dict(line=n.lineno, name=n.value.id + "[]"))

    onebit = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Return) and n.value is not None:
            s = ast.unparse(n.value)
            if re.search(r"0\s+if\s+\w+\s+else\s+1|1\s+if\s+not\s+\w+|"
                         r"^\s*[01]\s*$|ok\s+else", s):
                onebit.append(dict(line=n.lineno, expr=s[:100]))
        if isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call):
            s = ast.unparse(n.exc)
            if "exit" in s or "main" in s:
                onebit.append(dict(line=n.lineno, expr=s[:100]))
    return dict(agg_pass=agg_pass, per_token_print=per_token_print,
                per_any_print=per_any_print, hits_retained=hits_retained,
                onebit=onebit)


def analyse(rel, raw):
    text = raw.decode("utf-8-sig", errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return dict(rel=rel, verdict="UNPARSEABLE", error=str(exc))
    bindings = build_bindings(tree)
    tokens = collect_ksources(tree, bindings)
    coll, legal = analyse_calls(tree, tokens, bindings)
    out = analyse_output(tree, tokens)

    real_collapse = [c for c in coll if c["kind"].startswith(
        ("OR_COLLAPSE", "TERNARY_OR", "ARGMIN_REVERSE_MASK"))]
    accum = [c for c in coll if c["kind"].startswith("BIT_ACCUM")]
    has_k = any(tok["k"] == "runtime" or (isinstance(tok["k"], int) and tok["k"] >= 2)
                for tok in tokens.values())
    attribution = bool(out["per_token_print"] or out["hits_retained"])
    onebit_exit = bool(out["agg_pass"] or out["onebit"])

    if attribution:
        verdict = "LEGAL_AGGREGATE"          # per-input attribution retained
    elif not real_collapse:
        # A PASS exit with no OR/argmin collapse is a LEGITIMATE verdict state:
        # either a legal aggregate (all()/sum()/len()) or a plain single-input
        # self-test.  Only a file with no verdict exit at all is NO_SELFTEST.
        verdict = ("LEGAL_AGGREGATE" if (legal or onebit_exit)
                   else "NO_SELFTEST")
    elif not onebit_exit:
        verdict = "SUSPECT"                  # collapse but no clean 1-bit exit
    elif not has_k and not accum:
        verdict = "SUSPECT"                  # k not statically established
    else:
        verdict = "CONFIRMED_K1BIT"
    return dict(rel=rel, sha256=hashlib.sha256(raw).hexdigest(),
                bytes=len(raw), verdict=verdict,
                tokens=tokens, collapse=coll, legal=legal, output=out,
                n_real_collapse=len(real_collapse), n_accum=len(accum),
                has_k=has_k, attribution=attribution, onebit_exit=onebit_exit)


def main():
    root = Path(sys.argv[1]).resolve()
    wd = root / WD_NAME
    wd.mkdir(parents=True, exist_ok=True)
    if "--one" in sys.argv:
        rel = sys.argv[sys.argv.index("--one") + 1]
        p = Path(rel) if Path(rel).is_absolute() else root / rel
        r = analyse(rel, p.read_bytes())
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return
    listfile = root / "lead/check_family_20261109/_cf_filelist.txt"
    rels = []
    for ln in listfile.read_text(encoding="utf-8").splitlines():
        t = ln.strip()
        if t:
            rels.append(t[2:] if t.startswith("./") else t)
    rows = []
    for rel in rels:
        p = root / rel
        rows.append(analyse(rel, p.read_bytes()) if p.is_file()
                    else dict(rel=rel, verdict="MISSING"))
    from collections import Counter
    cnt = Counter(r["verdict"] for r in rows)
    conf = [r["rel"] for r in rows if r["verdict"] == "CONFIRMED_K1BIT"]
    susp = [r["rel"] for r in rows if r["verdict"] == "SUSPECT"]
    out = dict(n=len(rows), counts=dict(cnt), confirmed=conf, suspect=susp, rows=rows)
    (wd / "_kd_detect_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(dict(n=len(rows), counts=dict(cnt),
                          n_confirmed=len(conf), n_suspect=len(susp),
                          suspect=susp), ensure_ascii=False, indent=1))
    print("WROTE", (wd / "_kd_detect_out.json").as_posix())


if __name__ == "__main__":
    main()
