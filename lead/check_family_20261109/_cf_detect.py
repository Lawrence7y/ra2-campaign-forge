"""_cf_detect.py -- AST-level k->1bit family detector (design for step 3(c)).

Usage:
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_family_20261109/_cf_detect.py D:/Project/ra2-campaign-forge

Read-only over the repo; writes ONLY to lead/check_family_20261109/_cf_detect_out.json.

Predicate (code-level, not name-level):
  P1  a literal tuple table (requirements/keywords) with a row holding k>=2
      string tokens AND an OR branch (require_all False / no require_all)
  P2  an any(...) call collapsing that k-word OR into ONE boolean
      (GeneratorExp / ListComp of `x in body`, OR a bare boolean-list Name
       bound from `[w in body for w in words]`, OR `any(matches)` where
       matches is a list-comp of any/all over words)
  P3  exactly ONE aggregate PASS print in main(), followed by return/exit 0,
      and NO per-input (per-word) print loop
  P4  a section-body extractor feeding the word tests
"""
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
WD = ROOT / "lead" / "check_family_20261109"
LIST = WD / "_cf_filelist.txt"
OUT = WD / "_cf_detect_out.json"


def strs(node):
    return [e.value for e in ast.walk(node)
            if isinstance(e, ast.Constant) and isinstance(e.value, str)]


def is_membership_compare(e):
    return isinstance(e, ast.Compare) and any(
        isinstance(op, ast.In) for op in e.ops)


def analyze(rel, text):
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return dict(rel=rel, parse_error=str(exc), verdict="UNPARSEABLE")
    P = dict(P1=False, P2=False, P3=False, P4=False)
    detail = dict(or_rows=[], any_calls=[], bool_list_bind=[], pass_prints=[],
                  per_input_prints=[], extractors=[], exits=[])

    # P4: section extractor defs
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and (
                n.name in ("sections", "section_bodies", "section_body",
                           "exact_h2_body") or "section" in n.name):
            detail["extractors"].append((n.name, n.lineno))
    P["P4"] = bool(detail["extractors"])

    # P1: literal tuple/list of tuple rows, each row with >=2 strings
    for n in ast.walk(tree):
        if isinstance(n, (ast.Tuple, ast.List)) and any(
                isinstance(e, (ast.Tuple, ast.List)) for e in n.elts):
            for row in n.elts:
                if isinstance(row, (ast.Tuple, ast.List)):
                    ss = strs(row)
                    has_false = any(isinstance(e, ast.Constant) and e.value is False
                                    for e in row.elts)
                    # OR row: >=2 quoted tokens and (explicit False flag, or
                    # no require_all flag at all => d27-style 3-tuple OR)
                    if len(ss) >= 2:
                        if has_false or len(row.elts) == 3:
                            detail["or_rows"].append(dict(line=n.lineno,
                                                          tokens=ss, n=len(ss)))
    P["P1"] = bool(detail["or_rows"])

    # P2a: any(GeneratorExp/ListComp) whose element is a membership test
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "any":
            a = n.args[0] if n.args else None
            kind = None
            if isinstance(a, (ast.GeneratorExp, ast.ListComp)):
                if is_membership_compare(a.elt) or (
                        isinstance(a.elt, ast.Call) and isinstance(a.elt.func, ast.Name)
                        and a.elt.func.id in ("all", "any")):
                    kind = "gen_membership"
            elif isinstance(a, ast.Name):
                kind = "bool_list_name"
            detail["any_calls"].append(dict(line=n.lineno, kind=kind,
                                            arg=ast.dump(a)[:120] if a else ""))
    # P2b: boolean-list binding `[w in body for w in words]`
    for n in ast.walk(tree):
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            v = n.value
            if isinstance(v, ast.ListComp) and is_membership_compare(v.elt):
                detail["bool_list_bind"].append(n.lineno)
    P["P2"] = (any(x["kind"] in ("gen_membership", "bool_list_name")
                   for x in detail["any_calls"]) and
               (bool(detail["bool_list_bind"]) or
                any(x["kind"] == "gen_membership" for x in detail["any_calls"])))

    # P3: aggregate PASS print(s) + exit, and per-input print detection
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "print":
            # collect string literals including f-strings (JoinedStr constants)
            seg = " ".join(
                e.value for e in ast.walk(ast.Module(body=[n], type_ignores=[]))
                if isinstance(e, ast.Constant) and isinstance(e.value, str))
            if "PASS" in seg:
                # is it inside a for-loop? (per-item print)
                inside_loop = False
                for parent in ast.walk(tree):
                    if isinstance(parent, (ast.For, ast.While)) and n in list(ast.walk(parent)):
                        inside_loop = True
                        break
                (detail["per_input_prints"] if inside_loop else
                 detail["pass_prints"]).append(n.lineno)
        if isinstance(n, ast.Return) and isinstance(n.value, ast.Constant) and n.value.value == 0:
            detail["exits"].append(("return0", n.lineno))
    P["P3"] = (len(detail["pass_prints"]) >= 1 and bool(detail["exits"])
               and not detail["per_input_prints"])

    verdict = ("CONFIRMED" if all(P.values()) else
               "SUSPECT" if P["P2"] and P["P3"] else "NOT_FAMILY")
    return dict(rel=rel, flags=P, detail=detail, verdict=verdict)


def main():
    rels = []
    for ln in LIST.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            t = ln.strip()
            rels.append(t[2:] if t.startswith("./") else t)
    out = []
    for rel in rels:
        p = ROOT / rel
        if not p.is_file():
            continue
        data = p.read_bytes()
        out.append(dict(sha256=hashlib.sha256(data).hexdigest(),
                        **analyze(rel, data.decode("utf-8-sig", errors="replace"))))
    conf = [r["rel"] for r in out if r["verdict"] == "CONFIRMED"]
    susp = [r["rel"] for r in out if r["verdict"] == "SUSPECT"]
    # original four (production gates)
    four = ["lead/d27_ruling_20261106/check_d27.py",
            "lead/d28_ruling_20261106/check_d28.py",
            "lead/d29_ruling_20261106/check_d29.py",
            "lead/d30_ruling_20261106/check_d30.py"]
    by = {r["rel"]: r for r in out}
    out4 = [r for r in conf if "_ruling_" in r and re.match(r".*/d\d+_ruling_", r)]
    OUT.write_text(json.dumps(dict(n=len(out), confirmed=conf, suspect=susp,
                                   four={f: dict(verdict=by[f]["verdict"],
                                                 flags=by[f]["flags"]) for f in four},
                                   rows=out), ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(json.dumps(dict(n=len(out), n_confirmed=len(conf), n_suspect=len(susp),
                          four={f: by[f]["verdict"] for f in four},
                          four_flags={f: by[f]["flags"] for f in four},
                          confirmed_originals=out4,
                          suspect=susp), ensure_ascii=False, indent=1))
    print("WROTE", OUT.as_posix())


if __name__ == "__main__":
    main()
