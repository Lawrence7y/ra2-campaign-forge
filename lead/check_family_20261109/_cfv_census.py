"""Independent full-repository census of check_*.py (verification only).

Usage: python -I -X utf8 <this> <ROOT> <OUT.json> <ORCH.json> <LIST.txt>
Independent implementation: own AST feature extractor, own code-level family
predicate. The all-repository file list is produced separately by an
independent `find -type f -name 'check_*.py'` (see LIST.txt), so we do NOT
re-walk the pathological self-nested directory tree here. Reads only;
writes only OUT.json.
"""
import ast
import difflib
import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()

# ---------- file list from an independent `find` (not our own walker) ----------
LIST = Path(sys.argv[4]).resolve()
files = []
for line in LIST.read_text(encoding="utf-8").splitlines():
    rel = line.strip()
    if rel:
        files.append(ROOT / rel)
files.sort(key=lambda p: p.relative_to(ROOT).as_posix())


def shape(node):
    """AST dump with identifiers/constants stripped: a pure node-type signature."""
    class Strip(ast.NodeTransformer):
        def visit_Name(self, n):
            return ast.copy_location(ast.Name(id="_", ctx=ast.Load()), n)
        def visit_Constant(self, n):
            return ast.copy_location(ast.Constant(value="<C>"), n)
        def visit_Attribute(self, n):
            return self.generic_visit(n)
    try:
        return ast.dump(ast.fix_missing_locations(Strip().visit(ast.parse(ast.unparse(node)))))
    except Exception:
        return ast.dump(node)


def call_name(call):
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return ""


def arg_has_pass(call):
    for a in call.args:
        t = ""
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            t = a.value
        elif isinstance(a, ast.JoinedStr):
            t = "".join(v.value for v in a.values
                        if isinstance(v, ast.Constant) and isinstance(v.value, str))
        elif isinstance(a, ast.BinOp):
            t = ast.unparse(a)
        if "PASS" in t.upper():
            return True
    return False


def analyze(p: Path):
    raw = p.read_bytes()
    text = raw.decode("utf-8-sig")
    lines = text.splitlines()
    rec = {
        "rel": p.relative_to(ROOT).as_posix(),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "lines": len(lines),
        "mtime_ns": p.stat().st_mtime_ns,
    }
    rec["any_calls"] = [i + 1 for i, l in enumerate(lines)
                        if re.search(r"\bany\s*\(", l)]
    rec["all_calls"] = [i + 1 for i, l in enumerate(lines)
                        if re.search(r"\ball\s*\(", l)]
    rec["require_all_lines"] = [i + 1 for i, l in enumerate(lines)
                                if "require_all" in l]
    rec["pass_print_lines"] = [i + 1 for i, l in enumerate(lines)
                               if re.match(r"^\s*print\s*\(.*PASS", l, re.I)]
    rec["pass_fstring_lines"] = [i + 1 for i, l in enumerate(lines)
                                 if re.match(r'^\s*print\s*\(\s*f["\x27].*PASS', l, re.I)]
    rec["return0_lines"] = [i + 1 for i, l in enumerate(lines)
                            if re.match(r"^\s*return\s+0\b|raise SystemExit\(main\(\)\)", l)]
    rec["requirements_assign"] = [i + 1 for i, l in enumerate(lines)
                                  if re.match(r"^\s*requirements\s*=", l)]
    try:
        tree = ast.parse(text)
        rec["parse_ok"] = True
    except SyntaxError as exc:
        rec["parse_ok"] = False
        rec["parse_err"] = f"{exc.msg}@{exc.lineno}"
        return rec

    # AST-level any() classification
    any_gen_in = 0
    any_name_arg = 0
    any_other = 0
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and call_name(n) == "any"):
            continue
        if not n.args:
            any_other += 1
            continue
        a = n.args[0]
        if isinstance(a, ast.GeneratorExp):
            elt = a.elt
            if isinstance(elt, ast.Compare) and any(isinstance(o, ast.In) for o in elt.ops):
                any_gen_in += 1
            else:
                any_other += 1
        elif isinstance(a, ast.Name):
            any_name_arg += 1
        elif isinstance(a, (ast.ListComp, ast.SetComp, ast.List, ast.Tuple)):
            any_other += 1
        else:
            any_other += 1
    rec["ast_any_gen_in"] = any_gen_in
    rec["ast_any_name_arg"] = any_name_arg
    rec["ast_any_other"] = any_other
    rec["ast_n_any"] = any_gen_in + any_name_arg + any_other
    rec["ast_n_all"] = sum(1 for n in ast.walk(tree)
                           if isinstance(n, ast.Call) and call_name(n) == "all")

    # multi-word literal OR tuple: tuple of >=2 str constants that is
    # iterated by a destructuring For whose body calls any()/all()
    multiword = 0
    multiword_lines = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Tuple) and len(n.elts) >= 2 and all(
                isinstance(e, ast.Constant) and isinstance(e.value, str) for e in n.elts):
            multiword += 1
            multiword_lines.append(n.lineno)
    rec["multiword_str_tuples"] = multiword
    rec["multiword_str_tuple_lines"] = sorted(set(multiword_lines))

    # destructuring For loops + pure-shape signature of their body
    loop_shapes = []
    for n in ast.walk(tree):
        if isinstance(n, ast.For) and isinstance(n.target, ast.Tuple):
            body_src = "\n".join(ast.unparse(s) for s in n.body)
            try:
                sh = shape(ast.parse(body_src))
            except Exception:
                sh = body_src
            loop_shapes.append({
                "line": n.lineno,
                "target_len": len(n.target.elts),
                "body_shape_sha16": hashlib.sha256(sh.encode()).hexdigest()[:16],
                "body_shape_len": len(sh),
                "has_any": "any(" in body_src,
                "has_all": "all(" in body_src,
            })
    rec["destructuring_for_loops"] = loop_shapes

    # PASS prints: count, location (inside For?), joined/constant
    pass_prints = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and call_name(n) == "print" and arg_has_pass(n):
            pass_prints.append({"line": n.lineno,
                                "arg": ast.unparse(n.args[0])[:120] if n.args else ""})
    rec["ast_pass_prints"] = pass_prints
    rec["ast_n_pass"] = len(pass_prints)

    # prints inside any For loop (per-item attribution candidate)
    per_item = []
    for n in ast.walk(tree):
        if isinstance(n, ast.For):
            for sub in ast.walk(n):
                if isinstance(sub, ast.Call) and call_name(sub) == "print":
                    a = ast.unparse(sub.args[0])[:120] if sub.args else ""
                    per_item.append({"line": sub.lineno, "arg": a})
    rec["ast_prints_inside_for"] = per_item
    rec["ast_n_print_in_for"] = len(per_item)

    # section-body extractor functions
    extractors = []
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            src = ast.unparse(n)
            if ("splitlines" in src or "HEADING" in src) and (
                    "bodies" in src or "result" in src or "sections" in src.lower()):
                extractors.append({"name": n.name, "line": n.lineno,
                                   "sha16": hashlib.sha256(src.encode()).hexdigest()[:16],
                                   "nlines": len(src.splitlines())})
    rec["section_extractors"] = extractors

    # explicit per-word attribution markers
    rec["attribution_markers"] = [i + 1 for i, l in enumerate(lines)
                                  if re.search(r"HIT|DEAD|PER_NEEDLE|per[_-]?word|逐词|逐项|each_word|needle", l, re.I)]

    # golden/negative regression hard gates (anti-masking)
    rec["golden_markers"] = [i + 1 for i, l in enumerate(lines)
                             if re.search(r"GOLDEN_POS|GOLDEN_NEG|NAIVE_FLOOR|BAD_NEEDLE|DISTINGUISHABLE|哨兵|坏针", l, re.I)]
    return rec


rows = [analyze(p) for p in files]


# ---------- my own code-level family predicate ----------
def my_family(r):
    """CONFIRMED requires all four structural facts, checked from AST features."""
    if not r.get("parse_ok"):
        return "PARSE_ERR", {}
    f1 = r["multiword_str_tuples"] >= 1          # k>=2 literal OR word list exists
    f2 = r["ast_any_gen_in"] >= 1 or r["ast_any_name_arg"] >= 1  # any() collapses
    # a single aggregate PASS print, NOT inside a For loop
    agg = [pp for pp in r["ast_pass_prints"]
           if pp["line"] not in {q["line"] for q in r["ast_prints_inside_for"]}]
    f3 = len(agg) >= 1 and len(r["ast_pass_prints"]) == len(agg)
    f4 = len(r["section_extractors"]) >= 1       # body extractor feeds word test
    no_attr = len(r["attribution_markers"]) == 0
    golden = len(r["golden_markers"]) > 0
    flags = {"F1_multiword_tuple": f1, "F2_any_collapse": f2,
             "F3_single_aggregate_PASS": f3, "F4_section_extractor": f4,
             "no_attribution": no_attr, "golden_gate": golden}
    if golden:
        return "SUSPECT_ANTI_MASKING", flags
    if f1 and f2 and f3 and f4 and no_attr:
        return "CONFIRMED", flags
    if f1 and f2:
        return "SUSPECT", flags
    return "NOT_FAMILY", flags


for r in rows:
    v, fl = my_family(r)
    r["my_verdict"] = v
    r["my_flags"] = fl

# ---------- reproduce the literal "any()+PASS" screen ----------
def literal_screen(r):
    return bool(r["any_calls"]) and bool(r["pass_print_lines"])

for r in rows:
    r["literal_any_plus_PASS"] = literal_screen(r)

# ---------- orchestrator 25-row field verification ----------
ORCH = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8")) if len(sys.argv) > 3 else None
orch_check = None
if ORCH:
    by_rel = {r["rel"]: r for r in rows}
    mism = []
    missing = []
    for o in ORCH["files"]:
        rel = o["rel"]
        if rel not in by_rel:
            missing.append(rel)
            continue
        r = by_rel[rel]
        if r["bytes"] != o["bytes"]:
            mism.append({"rel": rel, "field": "bytes", "orch": o["bytes"], "mine": r["bytes"]})
        if r["sha256"][:16] != o["sha256"]:
            mism.append({"rel": rel, "field": "sha16", "orch": o["sha256"], "mine": r["sha256"][:16]})
        if r["any_calls"] != o["any"]:
            mism.append({"rel": rel, "field": "any", "orch": o["any"], "mine": r["any_calls"]})
        if r["require_all_lines"] != o["require_all"]:
            mism.append({"rel": rel, "field": "require_all", "orch": o["require_all"],
                         "mine": r["require_all_lines"]})
        if r["pass_print_lines"] != o["pass"]:
            mism.append({"rel": rel, "field": "pass", "orch": o["pass"],
                         "mine": r["pass_print_lines"]})
    orch_check = {"n_orch": len(ORCH["files"]), "missing": missing,
                  "field_mismatches": mism}

summary = Counter(r["my_verdict"] for r in rows)
out = {
    "root": ROOT.as_posix(),
    "total": len(rows),
    "my_verdict_counts": dict(summary),
    "n_literal_any_plus_PASS": sum(1 for r in rows if r["literal_any_plus_PASS"]),
    "literal_screen_misses_confirmed": [r["rel"] for r in rows
                                        if r["my_verdict"] == "CONFIRMED" and not r["literal_any_plus_PASS"]],
    "confirmed": [r["rel"] for r in rows if r["my_verdict"] == "CONFIRMED"],
    "suspect": [{"rel": r["rel"], "verdict": r["my_verdict"], "flags": r["my_flags"]}
                for r in rows if r["my_verdict"].startswith("SUSPECT")],
    "orch_check": orch_check,
    "all_files": rows,
}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"total={out['total']}")
print(f"my_verdict_counts={out['my_verdict_counts']}")
print(f"n_literal_any_plus_PASS={out['n_literal_any_plus_PASS']}")
print(f"literal_screen_misses_confirmed={out['literal_screen_misses_confirmed']}")
print(f"orch_check={json.dumps(orch_check, ensure_ascii=False)[:2000]}")
