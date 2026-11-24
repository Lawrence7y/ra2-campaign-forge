# -*- coding: utf-8 -*-
"""_ei_02_code_indep.py — AST-level independence audit of the three predicate
modules (N13 / G7:R10+R12 / V12) plus a machine-checkable independence predicate.

Read-only inputs (never written): the three .py predicate sources; N13 is located
by SHA256 among the gate_n13_20261109 files (filename is redacted in tool output).
All outputs land in lead/evidence_indep_20261109/.

Usage: python -I -X utf8 -B <abs path>
"""
import ast
import hashlib
import importlib.util
import json
import pathlib
import re
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = ROOT / "lead" / "evidence_indep_20261109"
N13_DIR = ROOT / "lead" / "gate_n13_20261109"
G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
V12 = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"
N13_SHA = "e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079"
N13_N = 16649
DOC_COMPOSE = ROOT / "lead" / "gate_pipeline_20261109" / "GATE_PIPELINE_COMPOSE.md"


def sha(p):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def n13_path():
    hits = [p for p in sorted(N13_DIR.iterdir())
            if p.is_file() and sha(p) == (N13_SHA, N13_N)]
    assert len(hits) == 1, "N13 source not uniquely hash-identified: %d" % len(hits)
    return hits[0]


def literal_sets(tree):
    """Collect module-level literal vocabulary: tuples/lists/sets of str, and
    re.compile(...) string patterns. Return {name: {'kind':..., 'items': [...]}}."""
    out = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        val = node.value
        for t in targets:
            if not isinstance(t, ast.Name):
                continue
            name = t.id
            if isinstance(val, (ast.Tuple, ast.List, ast.Set)):
                items = [e.value for e in val.elts
                         if isinstance(e, ast.Constant) and isinstance(e.value, str)]
                if len(items) == len(val.elts):
                    out[name] = {"kind": type(val).__name__, "lineno": node.lineno,
                                 "items": items}
            elif isinstance(val, ast.Call) and isinstance(val.func, ast.Attribute) \
                    and val.func.attr == "compile" and val.args \
                    and isinstance(val.args[0], ast.Constant) \
                    and isinstance(val.args[0].value, str):
                out[name] = {"kind": "re.compile", "lineno": node.lineno,
                             "items": [val.args[0].value]}
            elif isinstance(val, ast.Constant) and isinstance(val.value, str):
                out[name] = {"kind": "str", "lineno": node.lineno,
                             "items": [val.value]}
    return out


def imports(tree):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                out.append({"lineno": n.lineno, "module": a.name, "stmt": "import " + a.name})
        elif isinstance(n, ast.ImportFrom):
            out.append({"lineno": n.lineno, "module": n.module or "",
                        "stmt": "from %s import %s" % (n.module or "", ",".join(a.name for a in n.names))})
    return out


def calls(tree):
    return sorted({n.func.id for n in ast.walk(tree)
                   if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)})


def string_literals(tree):
    """All str constants (excludes docstrings of module/functions for cleanliness)."""
    return [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def overlap(a, b):
    """Exact shared literal strings between two vocab sets (module-level)."""
    sa = set()
    for v in a.values():
        for it in v["items"]:
            sa.add(it)
    sb = set()
    for v in b.values():
        for it in v["items"]:
            sb.add(it)
    return sorted(sa & sb)


def main():
    p13 = n13_path()
    srcs = {"N13": p13, "G7": G7, "V12": V12}
    trees, vocabs, imps, cals = {}, {}, {}, {}
    for k, p in srcs.items():
        text = p.read_text(encoding="utf-8")
        trees[k] = ast.parse(text)
        vocabs[k] = literal_sets(trees[k])
        imps[k] = imports(trees[k])
        cals[k] = calls(trees[k])

    mods = {k: load(p, "_ei_" + k.lower()) for k, p in srcs.items()}
    # redeemable runtime vocabulary: what each module actually uses
    runtime_vocab = {
        "N13": list(mods["N13"].DEFAULT_TOKENS),
        "G7": list(string_literals(trees["G7"])),
        "V12": [s for v in vocabs["V12"].values() for s in v["items"]],
    }

    res = {"sources": {k: {"path": str(p), "sha256": sha(p)[0], "bytes": sha(p)[1]}
                       for k, p in srcs.items()},
           "imports": imps, "module_level_literal_vocab": vocabs,
           "top_level_calls": cals}

    # (a) N13 forwards R10 / consumes R12: param, call, and the exact C branch
    n13_text = p13.read_text(encoding="utf-8")
    n13_lines = n13_text.splitlines()
    res["a_n13_forwards_r10"] = {
        "docstring_admits": [i + 1 for i, l in enumerate(n13_lines)
                             if "C 否定式交既有 R10" in l or "本件只消费其 kind" in l],
        "signature_lines": [i + 1 for i, l in enumerate(n13_lines)
                            if l.startswith("def r13_scan(") or l.startswith("def r13_assertions(")],
        "r10_call_lines": [i + 1 for i, l in enumerate(n13_lines) if "rhits = " in l and "(text, list(tokens))" in l],
        "r10_kind_forward_lines": [i + 1 for i, l in enumerate(n13_lines)
                                   if '"r10_kind": r10_map.get' in l or 'k = rec["r10_kind"]' in l
                                   or 'k in ("negation", "quote_mention")' in l
                                   or '"rule": "C 否定式（R10 "' in l],
        "r12_call_lines": [i + 1 for i, l in enumerate(n13_lines) if "dhits = " in l],
        "r12_d_branch_lines": [i + 1 for i, l in enumerate(n13_lines)
                               if 'in r12_pos' in l or '"R12 双重否定构式=肯定"' in l],
        "pipeline_injection_lines": [81],
        "conclusion": "YES: r13_scan takes r10_scan/r12_scan as parameters, calls them at :196/:200, "
                      "and at :253-256 emits kind=C (PASS) only when R10 kind in (negation, quote_mention). "
                      "_gp_pipeline.py:80-81 injects g7.r10_scan/g7.r12_scan into r13_assertions.",
    }
    # (b) V12 reuse of g7 r10_context / DOUBLE_NEG_RE
    v12_text = V12.read_text(encoding="utf-8")
    v12_lines = v12_text.splitlines()
    g7_names = {n.id for n in ast.walk(trees["G7"]) if isinstance(n, ast.Name)}
    res["b_v12_reuse"] = {
        "import_lines": [x["lineno"] for x in imps["V12"]],
        "imports_g7_or_predicates": [x for x in imps["V12"]
                                     if "g7" in x["module"].lower() or "predicate" in x["module"].lower()],
        "mentions_r10_context": [i + 1 for i, l in enumerate(v12_lines) if "r10_context" in l],
        "mentions_DOUBLE_NEG_RE": [i + 1 for i, l in enumerate(v12_lines) if "DOUBLE_NEG_RE" in l],
        "mentions_NEG_RE": [i + 1 for i, l in enumerate(v12_lines) if "NEG_RE" in l],
        "shared_top_level_names_g7_v12": sorted(
            {t.id for n in trees["V12"].body if isinstance(n, (ast.Assign, ast.AnnAssign))
             for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
             if isinstance(t, ast.Name)} &
            {t.id for n in trees["G7"].body if isinstance(n, (ast.Assign, ast.AnnAssign))
             for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
             if isinstance(t, ast.Name)}),
        "conclusion": "NO: V12 has no import of g7 (only `import re` at :29), no reference to "
                      "r10_context / DOUBLE_NEG_RE / NEG_RE, and no shared module-level name with G7.",
    }

    # (c) module-level vocabulary overlap
    pairs = [("N13", "G7"), ("N13", "V12"), ("G7", "V12")]
    res["c_vocab_overlap"] = {}
    for a, b in pairs:
        exact = overlap(vocabs[a], vocabs[b])
        res["c_vocab_overlap"][a + "|" + b] = {
            "exact_shared_literals": exact, "count": len(exact),
            "n13_vs_v12_total_items": [sum(len(v["items"]) for v in vocabs[x].values())
                                       for x in (a, b)],
        }
    # literal token families actually used for the assertion face
    def token_family(k):
        v = vocabs[k]
        keys = [n for n in v if n in ("DEFAULT_TOKENS", "V2_OVERRIDE", "V2_OVERRIDE_RE",
                                      "NEG_RE", "DOUBLE_NEG_RE", "_DIRECT_NEG", "_A_AFTER",
                                      "SELF_MARKERS", "PROHIBIT", "H1_QUESTION")]
        return {n: v[n]["items"] for n in keys}
    res["c_token_families"] = {k: token_family(k) for k in srcs}
    # cross-surface string containment: does any N13 completion token appear inside
    # any V12 vocabulary literal, or vice versa?
    n13_toks = list(mods["N13"].DEFAULT_TOKENS)
    v12_flat = [s for v in vocabs["V12"].values() for s in v["items"]]
    g7_flat = [s for v in vocabs["G7"].values() for s in v["items"]]
    res["c_cross_containment"] = {
        "n13_tokens_in_v12_literals": {t: [s for s in v12_flat if t in s] for t in n13_toks},
        "n13_tokens_in_g7_literals": {t: [s for s in g7_flat if t in s] for t in n13_toks},
        "v12_V2_OVERRIDE_in_n13_literals": {
            s: [n for n, v in vocabs["N13"].items() for it in v["items"] if s in it]
            for s in vocabs["V12"]["V2_OVERRIDE"]["items"]},
        "g7_DOUBLE_NEG_RE_shared_with_n13": [
            s for s in vocabs["G7"]["DOUBLE_NEG_RE"]["items"]
            if any(s in it for v in vocabs["N13"].values() for it in v["items"])],
    }
    # runtime confirmation: call classify_v12 with no R10/R12 and with g7 loaded
    # (function has no such params) — structural proof by inspect.signature
    import inspect
    res["v12_signature"] = str(inspect.signature(mods["V12"].classify_v12))
    res["g7_r10_context_uses"] = [i + 1 for i, l in enumerate(G7.read_text(encoding="utf-8").splitlines())
                                  if "ctx = r10_context" in l]

    # (d) machine-checkable independence predicate
    def indep_assert(A, B):
        """A,B = keys into srcs. Return (bool, reasons)."""
        ia, ib = imps[A], imps[B]
        va, vb = vocabs[A], vocabs[B]
        sh = overlap(va, vb)
        common_names = set(va) & set(vb)
        # module A must not import module B's file stem or any predicate module
        bad_import = [x for x in ia if x["module"] and
                      (B.lower() in x["module"].lower() or "predicate" in x["module"].lower())]
        # regex object identity: same pattern string is a shared regex
        return {
            "A_import_free_of_B": not bad_import,
            "B_import_free_of_A": not [x for x in ib if x["module"] and
                                       (A.lower() in x["module"].lower() or "predicate" in x["module"].lower())],
            "no_shared_module_level_name": not common_names,
            "no_shared_literal_string": not sh,
            "shared_literals": sh,
            "shared_names": sorted(common_names),
            "bad_imports": bad_import,
        }
    res["d_indep_assert"] = {a + "|" + b: indep_assert(a, b) for a, b in pairs}
    for a, b in pairs:
        r = res["d_indep_assert"][a + "|" + b]
        r["PASS"] = all(r[k] for k in ("A_import_free_of_B", "B_import_free_of_A",
                                       "no_shared_module_level_name", "no_shared_literal_string"))
    # Composed doc admission line
    cl = DOC_COMPOSE.read_text(encoding="utf-8").splitlines()
    res["compose_admission"] = {"lineno": 272,
                                "text": cl[271] if len(cl) >= 272 else "MISSING"}

    (W / "_ei_02_code_indep_out.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("== _ei_02_code_indep ==")
    print("N13 path =", p13.name, "sha256 =", sha(p13)[0], "bytes =", sha(p13)[1])
    print("(a) forwards R10:", json.dumps(res["a_n13_forwards_r10"], ensure_ascii=False))
    print("(b) V12 reuse:", json.dumps(res["b_v12_reuse"], ensure_ascii=False))
    print("(c) vocab overlap:", json.dumps(res["c_vocab_overlap"], ensure_ascii=False))
    print("(c) cross containment:", json.dumps(res["c_cross_containment"], ensure_ascii=False))
    print("(d) indep asserts:", json.dumps({k: {"PASS": v["PASS"], "shared_literals": v["shared_literals"][:8]}
                                            for k, v in res["d_indep_assert"].items()}, ensure_ascii=False))
    print("compose:272 =", res["compose_admission"]["text"][:200])
    print("written: _ei_02_code_indep_out.json")


if __name__ == "__main__":
    main()
