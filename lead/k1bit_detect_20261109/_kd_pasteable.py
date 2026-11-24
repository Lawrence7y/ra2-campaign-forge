# -*- coding: utf-8 -*-
"""_kd_pasteable.py -- corrected, self-contained AST/dataflow k->1bit detector.

This is the pasteable implementation discussed in K1BIT_DETECTOR.md section 3.

It repairs the four holes the review of _kd_detect.py found (verdict=partial):
  (1) S1 direct-assignment branch unpacks (lineno, expr) pairs -> no longer dead;
  (2) is_token_source uses DATAFLOW-derived tokens only (no TOKENISH name regex),
      with ROLE INFERENCE: a literal string collection is a k-token source only
      when its loop variable is used as the varying PROBE (left operand of
      `in`, or argument of find/search), not when it is the sample being searched;
      the membership test is DIRECTIONAL (`token in body` vs `"FIXED" in body`);
  (3) has_k is required for EVERY verdict, including BIT_ACCUM-only files;
  (4) attribution = real indexed store / per-token PASS print whose loop var is
      a probe variable; a scalar merely NAMED `hits` does not count.

Read-only outside its own write domain; never executes inspected scripts.
"""
import ast
import hashlib
import json
import re
import sys
from pathlib import Path


def strs(node):
    return [e.value for e in ast.walk(node)
            if isinstance(e, ast.Constant) and isinstance(e.value, str)]


def lit_strs(node):
    if isinstance(node, (ast.Tuple, ast.List)) and node.elts:
        ss = [e.value for e in node.elts
              if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        if len(ss) == len(node.elts) and ss:
            return ss
    return None


def rows_of(expr):
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


def is_print(call):
    return isinstance(call.func, ast.Name) and call.func.id in ("print", "P")


def is_passish(call):
    return bool(re.search(r"\bPASS\b|SELF_TEST|\bOK\b", " ".join(strs(call)), re.I))


def src_name(expr):
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        return expr.attr
    return None


PROBE_FUNCS = {"find", "index", "count", "search", "match", "fullmatch",
               "startswith", "endswith", "contains"}


def probe_uses(tree):
    """Names used as the VARYING PROBE, not as the searched sample."""
    pv = set()
    for n in ast.walk(tree):
        if is_in_compare(n) and isinstance(n.left, ast.Name):
            pv.add(n.left.id)
        if isinstance(n, ast.Call):
            fn = n.func.id if isinstance(n.func, ast.Name) else (
                n.func.attr if isinstance(n.func, ast.Attribute) else "")
            if fn in PROBE_FUNCS:
                for a in n.args:
                    if isinstance(a, ast.Name):
                        pv.add(a.id)
    return pv


# ------------------------------------------------------------- S1 KSOURCE
def build_bindings(tree):
    b = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    b.setdefault(t.id, []).append((n.lineno, n.value))
                elif isinstance(t, (ast.Tuple, ast.List)) and isinstance(
                        n.value, (ast.Tuple, ast.List)):
                    for i, e in enumerate(t.elts):
                        if isinstance(e, ast.Name) and i < len(n.value.elts):
                            b.setdefault(e.id, []).append((n.lineno, n.value.elts[i]))
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value:
            b.setdefault(n.target.id, []).append((n.lineno, n.value))
    for k in b:
        b[k].sort(key=lambda x: x[0])
    return b


def resolve(name, b):
    return [v for _, v in b.get(name, [])]


def collect_ksources(tree, b):
    """{token_name: {k, why, line}} -- k>=2 homogeneous inputs, ROLE-checked."""
    cand = {}

    def mark(name, k, why, line):
        if not name:
            return
        old = cand.get(name)
        if old is None or (old["k"] != "runtime" and
                           (k == "runtime" or
                            (isinstance(k, int) and isinstance(old["k"], int) and k > old["k"]))):
            cand[name] = dict(k=k, why=why, line=line)

    # (1) direct assignment to a literal string collection (FIX: unpack pair)
    for name, vals in b.items():
        for _, v in vals:
            ss = lit_strs(v)
            if ss and len(ss) >= 2:
                mark(name, len(ss), "assign_literal_str_collection", getattr(v, "lineno", 0))

    for n in ast.walk(tree):
        if not isinstance(n, ast.For):
            continue
        srcs = [n.iter] + (resolve(n.iter.id, b) if isinstance(n.iter, ast.Name) else [])
        # (2) for-unpacking a literal requirements table: only the ROW SLOT that
        # holds the >=2-string token collection is a k-source.
        rows = []
        for s in srcs:
            rows += rows_of(s)
        if rows and isinstance(n.target, (ast.Tuple, ast.List)):
            tnames = target_names(n.target)
            maxk = 0
            for r in rows:
                for e in r.elts:
                    ss = lit_strs(e)
                    if ss:
                        maxk = max(maxk, len(ss))
            if maxk >= 2:
                for r in rows:
                    for i, e in enumerate(r.elts):
                        ss = lit_strs(e)
                        if ss and len(ss) == maxk and i < len(tnames):
                            mark(tnames[i], maxk, "for_unpack_token_row", n.lineno)
        # (2b) for directly over a literal k-token tuple
        ss = lit_strs(n.iter)
        if ss and len(ss) >= 2:
            for t in target_names(n.target):
                mark(t, len(ss), "for_literal_token_tuple", n.lineno)

    # (3) argparse action="append" (runtime k)
    for n in ast.walk(tree):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "add_argument"):
            kw = {k.arg: k.value for k in n.keywords}
            act = kw.get("action")
            if (isinstance(act, ast.Constant) and act.value == "append"
                    and n.args and isinstance(n.args[0], ast.Constant)
                    and isinstance(n.args[0].value, str)):
                dest = n.args[0].value.lstrip("-").replace("-", "_")
                mark(dest, "runtime", "argparse_action_append", n.lineno)

    # (4) interprocedural: parameter <- token-ish argument (two passes)
    funcs = {f.name: f for f in ast.walk(tree) if isinstance(f, ast.FunctionDef)}
    for _ in range(2):
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in funcs:
                f = funcs[n.func.id]
                for p, arg in zip([a.arg for a in f.args.args], n.args):
                    an = src_name(arg)
                    if an in cand:
                        mark(p, cand[an]["k"], "param_from_" + cand[an]["why"], n.lineno)

    # ROLE INFERENCE: keep a candidate only if it is used as a probe iterable,
    # or is an established runtime/parameter source.  This is what separates
    # k tokens from SAMPLES (e.g. cases=["doc1","doc2"] with "FIXED" in case).
    probes = probe_uses(tree)
    used = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.GeneratorExp, ast.ListComp)):
            for g in n.generators:
                if set(target_names(g.target)) & probes:
                    nm = src_name(g.iter)
                    if nm:
                        used.add(nm)
        elif isinstance(n, ast.For):
            if set(target_names(n.target)) & probes:
                nm = src_name(n.iter)
                if nm:
                    used.add(nm)
    return {k: v for k, v in cand.items()
            if v["k"] == "runtime" or v["why"].startswith("param_from_") or k in used}


def is_token_source(expr, tokens):
    """FIX: dataflow-derived tokens only; no TOKENISH name regex."""
    nm = src_name(expr)
    if nm is not None and nm in tokens:
        return True, nm
    ss = lit_strs(expr)
    if ss and len(ss) >= 2:
        return True, "<literal>"
    return False, None


def token_loop_vars(tree, probes, tokens):
    """Loop targets that are probe variables AND range over a k-source."""
    return {t for n in ast.walk(tree)
            if isinstance(n, (ast.For, ast.AsyncFor))
            and (is_token_source(n.iter, tokens)[0] or
                 (isinstance(n.iter, ast.Name) and src_name(n.iter) in tokens))
            for t in set(target_names(n.target)) & probes}


def token_clauses(comp, tokens):
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
    """FIX: DIRECTIONAL membership test on the token variable itself."""
    if elt is None:
        return False
    if is_in_compare(elt):
        return bool(set(name_ids(elt.left)) & tvars)
    if isinstance(elt, ast.BoolOp):
        return any(elt_matches_token(v, tvars) for v in elt.values)
    if isinstance(elt, ast.UnaryOp):
        return elt_matches_token(elt.operand, tvars)
    if isinstance(elt, ast.IfExp):
        return (elt_matches_token(elt.body, tvars) or
                elt_matches_token(elt.orelse, tvars))
    if isinstance(elt, ast.Call):
        fn = elt.func.id if isinstance(elt.func, ast.Name) else (
            elt.func.attr if isinstance(elt.func, ast.Attribute) else "")
        if fn in PROBE_FUNCS and any(set(name_ids(a)) & tvars for a in elt.args):
            return True
        if isinstance(elt.func, ast.Name) and elt.func.id in ("any", "all"):
            return any(comp_matches_token(a, tvars) for a in elt.args
                       if isinstance(a, (ast.GeneratorExp, ast.ListComp)))
        return False
    return False


def comp_matches_token(comp, tvars):
    if not isinstance(comp, (ast.GeneratorExp, ast.ListComp)):
        return False
    if elt_matches_token(comp.elt, tvars):
        return True
    for sub in ast.walk(comp.elt):
        if isinstance(sub, (ast.GeneratorExp, ast.ListComp)) and sub is not comp:
            extra = set(target_names(sub.generators[0].target)) if sub.generators else set()
            if elt_matches_token(sub.elt, tvars | extra):
                return True
    return False


# ----------------------------------------------------------- S2 COLLAPSE
def analyse_calls(tree, tokens, b):
    coll, legal = [], []

    def record(kind, n, quant, k, expr):
        coll.append(dict(line=n.lineno, kind=kind, quantifies=quant, k=k,
                         expr=ast.unparse(expr)[:180]))

    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            fn = n.func.id
            a = n.args[0] if n.args else None
            if fn == "any":
                if isinstance(a, (ast.GeneratorExp, ast.ListComp)):
                    hit = [(tv, k) for tv, src, k in token_clauses(a, tokens)
                           if comp_matches_token(a, tv)]
                    if hit:
                        record("OR_COLLAPSE_gen", n, "k_tokens", hit[0][1], n)
                    else:
                        legal.append(dict(line=n.lineno, kind="any_over_samples"))
                elif isinstance(a, ast.Name):
                    hit = False
                    for v in resolve(a.id, b):
                        if not isinstance(v, ast.ListComp):
                            continue
                        cls = token_clauses(v, tokens)
                        for tv, src, k in cls:
                            if comp_matches_token(v, tv):
                                record("OR_COLLAPSE_bound_list", n,
                                       "k_tokens(via %s)" % a.id, k, n)
                                hit = True
                                break
                        if hit:
                            break
                        for sub in ast.walk(v.elt):
                            if (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
                                    and sub.func.id == "any" and sub.args
                                    and isinstance(sub.args[0], (ast.GeneratorExp, ast.ListComp))):
                                for tv, src, k in token_clauses(sub.args[0], tokens):
                                    if elt_matches_token(sub.args[0].elt, tv):
                                        record("OR_COLLAPSE_ternary_list", n,
                                               "k_tokens(via %s)" % a.id, k, n)
                                        hit = True
                                        break
                                if hit:
                                    break
                        if hit:
                            break
                    if not hit:
                        legal.append(dict(line=n.lineno, kind="any_over_name"))
                else:
                    legal.append(dict(line=n.lineno, kind="any_other"))
            elif fn == "all":
                legal.append(dict(line=n.lineno, kind="AND_aggregate"))
            elif fn in ("min", "max"):
                if isinstance(a, (ast.GeneratorExp, ast.ListComp)):
                    for tv, src, k in token_clauses(a, tokens):
                        if elt_matches_token(a.elt, tv):
                            record("ARGMIN_REVERSE_MASK", n, "k_tokens", k, n)
                            break
            elif fn in ("sum", "len", "sorted"):
                legal.append(dict(line=n.lineno, kind="count_preserving"))

        if isinstance(n, ast.IfExp):
            for br in (n.body, n.orelse):
                if (isinstance(br, ast.Call) and isinstance(br.func, ast.Name)
                        and br.func.id == "any" and br.args
                        and isinstance(br.args[0], ast.Name)):
                    nm = br.args[0].id
                    for v in resolve(nm, b):
                        cls = token_clauses(v, tokens) if isinstance(v, ast.ListComp) else []
                        if cls:
                            record("TERNARY_OR_BRANCH", n, "k_tokens(via %s)" % nm,
                                   cls[0][2], n)
                            break

        # `present[0] or present[1]` -- OR without the any() token
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            for val in n.values:
                if isinstance(val, ast.Subscript) and isinstance(val.value, ast.Name):
                    nm = val.value.id
                    for v in resolve(nm, b):
                        if isinstance(v, ast.ListComp) and any(
                                comp_matches_token(v, tv)
                                for tv, src, k in token_clauses(v, tokens)):
                            record("OR_COLLAPSE_bound_or", n, "k_tokens(via %s)" % nm,
                                   token_clauses(v, tokens)[0][2], n)
                            break

        if isinstance(n, ast.AugAssign) and isinstance(n.op, ast.BitAnd):
            record("BIT_ACCUM_AugAssign_BitAnd", n, "aggregate_cases", "?", n)
        if (isinstance(n, ast.Assign) and isinstance(n.value, ast.BoolOp)
                and isinstance(n.value.op, ast.And)):
            if any(isinstance(t, ast.Name) and t.id in ("ok", "all_ok", "passed")
                   for t in n.targets):
                record("BIT_ACCUM_bool_and", n, "aggregate_cases", "?", n)
    return coll, legal


# ------------------------------------------------------- S3 ONEBIT / S4 LEGAL
def analyse_output(tree, tlv):
    loop_parent = {}
    for lp in ast.walk(tree):
        if isinstance(lp, (ast.For, ast.While, ast.AsyncFor)):
            for sub in ast.walk(lp):
                if sub is not lp:
                    loop_parent.setdefault(id(sub), []).append(lp)

    def in_token_loop(n):
        return any(isinstance(lp, (ast.For, ast.AsyncFor)) and
                   (set(target_names(lp.target)) & tlv)
                   for lp in loop_parent.get(id(n), []))

    agg_pass, per_token_print = [], []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and is_print(n) and is_passish(n):
            (per_token_print if in_token_loop(n) else agg_pass).append(n.lineno)

    # FIX: attribution = indexed STORE keyed by a token loop var, or per-token print.
    hits_retained = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Assign) or not in_token_loop(n):
            continue
        for t in n.targets:
            if isinstance(t, ast.Subscript) and set(name_ids(t.slice)) & tlv:
                hits_retained.append(dict(line=n.lineno, name=ast.unparse(t)[:60]))

    onebit = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Return) and n.value is not None:
            s = ast.unparse(n.value)
            if re.search(r"0\s+if\s+\w+\s+else\s+1|1\s+if\s+not\s+\w+|"
                         r"^\s*[01]\s*$|ok\s+else", s):
                onebit.append(dict(line=n.lineno, expr=s[:100]))
    return dict(agg_pass=agg_pass, per_token_print=per_token_print,
                hits_retained=hits_retained, onebit=onebit)


def analyse(rel, raw):
    text = raw.decode("utf-8-sig", errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return dict(rel=rel, verdict="UNPARSEABLE", error=str(exc))
    b = build_bindings(tree)
    tokens = collect_ksources(tree, b)
    tlv = token_loop_vars(tree, probe_uses(tree), tokens)
    coll, legal = analyse_calls(tree, tokens, b)
    out = analyse_output(tree, tlv)
    real = [c for c in coll if c["kind"].startswith(
        ("OR_COLLAPSE", "TERNARY_OR", "ARGMIN_REVERSE_MASK"))]
    accum = [c for c in coll if c["kind"].startswith("BIT_ACCUM")]
    has_k = any(t["k"] == "runtime" or (isinstance(t["k"], int) and t["k"] >= 2)
                for t in tokens.values())
    attribution = bool(out["per_token_print"] or out["hits_retained"])
    onebit = bool(out["agg_pass"] or out["onebit"])
    if attribution:
        v = "LEGAL_AGGREGATE"
    elif not real and not accum:
        v = "LEGAL_AGGREGATE" if (legal or onebit) else "NO_SELFTEST"
    elif not onebit:
        v = "SUSPECT"
    elif not has_k:                       # FIX: no &= bypass of k>=2
        v = "LEGAL_AGGREGATE"
    else:
        v = "CONFIRMED_K1BIT"
    return dict(rel=rel, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                verdict=v, tokens=tokens, token_loop_vars=sorted(tlv),
                collapse=coll, legal=legal, output=out,
                has_k=has_k, attribution=attribution, onebit_exit=onebit,
                n_real_collapse=len(real), n_accum=len(accum))


def main():
    root = Path(sys.argv[1]).resolve()
    if "--one" in sys.argv:
        rel = sys.argv[sys.argv.index("--one") + 1]
        p = Path(rel) if Path(rel).is_absolute() else root / rel
        print(json.dumps(analyse(rel, p.read_bytes()), ensure_ascii=False, indent=1))
        return
    rels = []
    for ln in (root / "lead/check_family_20261109/_cf_filelist.txt").read_text(
            encoding="utf-8").splitlines():
        t = ln.strip()
        if t:
            rels.append(t[2:] if t.startswith("./") else t)
    rows = [analyse(rel, (root / rel).read_bytes()) for rel in rels
            if (root / rel).is_file()]
    from collections import Counter
    cnt = Counter(r["verdict"] for r in rows)
    conf = [r["rel"] for r in rows if r["verdict"] == "CONFIRMED_K1BIT"]
    print(json.dumps(dict(n=len(rows), counts=dict(cnt),
                          n_confirmed=len(conf), confirmed=conf),
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
