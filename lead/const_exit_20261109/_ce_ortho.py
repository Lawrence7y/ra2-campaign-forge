# -*- coding: utf-8 -*-
"""_ce_ortho.py -- step 4(b) + 2(c) + 5(a) probes.

Read-only over repo (writes only _ce_* in my write domain).
Imports the two existing DETECTORS as pure AST functions (analyse / analyze);
never executes any checked script or checked gate.
"""
import ast
import importlib.util
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


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, str(ROOT / rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def cited_and_idx():
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
    return idx, cited


def conjunction_facts(rel):
    """Does the exit branch read a CONJUNCTION of k check results?

    AST evidence categories:
      CONJUNCTION  : all(...) / `ok = ok and x` fold / `not fails` over a
                     collection of check results / a counter == k
      SINGLE_VAR   : a single boolean or a single scalar comparison
      EXISTENCE    : os.path.exists / is_file / Path(...).exists -- checks
                     presence of an artifact, not its content correctness
      EXTERNAL     : exit status imported from a subprocess / env / file
      NONE         : nothing data-dependent read
    """
    raw = Path(rel).read_bytes()
    t = ast.parse(raw.decode("utf-8-sig", errors="replace"))
    ev = []
    for n in ast.walk(t):
        # exit args
        args = []
        if isinstance(n, ast.Call) and ((isinstance(n.func, ast.Attribute) and
                n.func.attr == "exit") or (isinstance(n.func, ast.Name) and
                n.func.id in ("exit", "quit"))):
            args = list(n.args)
        elif isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call) and \
                isinstance(n.exc.func, ast.Name) and \
                n.exc.func.id == "SystemExit":
            args = list(n.exc.args)
        for a in args:
            s = ast.unparse(a)
            if re.search(r"\ball\s*\(|all_ok|not\s+\w*fail|len\(\w*fail", s):
                ev.append(("CONJUNCTION", n.lineno, s[:110]))
            elif re.search(r"exists|is_file|is_dir|stat\(\)|Path\(", s):
                ev.append(("EXISTENCE", n.lineno, s[:110]))
            elif re.search(r"environ|getenv|popen|subprocess|returncode|"
                           r"read_text|read_bytes|json\.load", s):
                ev.append(("EXTERNAL", n.lineno, s[:110]))
            elif isinstance(a, ast.IfExp) or isinstance(a, ast.BoolOp):
                ev.append(("SINGLE_VAR", n.lineno, s[:110]))
            elif isinstance(a, ast.Constant):
                ev.append(("NONE", n.lineno, s[:110]))
            elif isinstance(a, ast.Call) and isinstance(a.func, ast.Name):
                # resolve main()'s own returns
                f = next((x for x in ast.walk(t)
                          if isinstance(x, ast.FunctionDef) and
                          x.name == a.func.id), None)
                if f:
                    nested = set()
                    for x in ast.walk(f):
                        if x is not f and isinstance(x, (ast.FunctionDef,
                                ast.AsyncFunctionDef, ast.Lambda)):
                            for z in ast.walk(x):
                                nested.add(id(z))
                    for r in ast.walk(f):
                        if isinstance(r, ast.Return) and id(r) not in nested \
                                and r.value is not None:
                            s2 = ast.unparse(r.value)
                            if re.search(r"\ball\s*\(|all_ok|not\s+\w*fail|"
                                         r"len\(\w*fail", s2):
                                ev.append(("CONJUNCTION", r.lineno, s2[:110]))
                            elif isinstance(r.value, ast.IfExp) or \
                                    isinstance(r.value, ast.BoolOp):
                                ev.append(("SINGLE_VAR", r.lineno, s2[:110]))
                            elif isinstance(r.value, ast.Constant):
                                # distinct literal returns in branches: the
                                # branch condition reads the check results
                                ev.append(("BRANCHED_LITERAL", r.lineno,
                                           s2[:110]))
                            else:
                                ev.append(("SINGLE_VAR", r.lineno, s2[:110]))
                else:
                    ev.append(("SINGLE_VAR", n.lineno, s[:110]))
            else:
                ev.append(("SINGLE_VAR", n.lineno, s[:110]))
    # ok &= good fold over >=2 checks is a conjunction, but a 1-bit fold
    folds = [n.lineno for n in ast.walk(t)
             if isinstance(n, ast.AugAssign) and
             isinstance(n.op, (ast.BitAnd,))]
    if folds:
        ev.append(("BIT_ACCUM_FOLD", folds[0],
                   "%d folds" % len(folds)))
    return ev


def main():
    idx, cited = cited_and_idx()
    kd = json.load(open("lead/k1bit_detect_20261109/_kd_detect_out.json",
                        encoding="utf-8"))
    census = {os.path.basename(r["rel"]) for r in kd["rows"]}
    resolvable = sorted(b for b in cited if b in idx)

    # ---- step 4(b): detectors vs VERIFY_A8.py
    a8 = "lead/goal1_a8_fix_20261022/VERIFY_A8.py"
    kdmod = load("kdmod", "lead/k1bit_detect_20261109/_kd_detect.py")
    # _cf_detect.py reads sys.argv[1] at import time (ROOT path only); supply it
    # so we can call its pure analyze() function.  main() is NOT called.
    argv0 = sys.argv[:]
    sys.argv = [str(ROOT / "lead/check_family_20261109/_cf_detect.py"),
                str(ROOT)]
    cfmod = load("cfmod", "lead/check_family_20261109/_cf_detect.py")
    sys.argv = argv0
    raw = Path(a8).read_bytes()
    kdres = kdmod.analyse(a8, raw)
    cfres = cfmod.analyze(a8, raw.decode("utf-8-sig", errors="replace"))
    # "various literal filters": the classic `return 0` / `exit(0)` grep
    txt = raw.decode("utf-8-sig", errors="replace")
    literal_filters = dict(
        has_literal_return0=bool(re.search(r"^\s*return 0\s*$",
                                           txt, re.M)),
        has_exit0=bool(re.search(r"sys\.exit\(\s*0\s*\)", txt)),
        has_pass_print=bool(re.search(r"print\(.*PASS", txt)),
    )
    ortho = dict(kd_verdict=kdres["verdict"],
                 kd_onebit=kdres["output"]["onebit"],
                 kd_n_accum=kdres["n_accum"],
                 kd_n_real_collapse=kdres["n_real_collapse"],
                 cf_verdict=cfres["verdict"], cf_flags=cfres["flags"],
                 literal_filters=literal_filters)

    # ---- step 2(c): conjunction subclass across final CONDITIONAL rows
    fin = json.load(open(WD / "_ce_final_out.json", encoding="utf-8"))
    cond = [r for r in fin["rows"] if r["cls"] == "CONDITIONAL_EXIT"]
    conj_rows = []
    for r in cond:
        ev = conjunction_facts(r["rel"])
        cats = Counter(c for c, _, _ in ev)
        is_conj = ("CONJUNCTION" in cats or
                   (cats.get("BIT_ACCUM_FOLD", 0) >= 2 and
                    cats.get("BRANCHED_LITERAL", 0) >= 2))
        conj_rows.append(dict(rel=r["rel"], categories=dict(cats),
                              is_conjunction=is_conj,
                              evidence=ev[:6]))
    n_c = sum(1 for r in conj_rows if r["is_conjunction"])

    # ---- step 5(a): full inventory = ALL cited, resolvable .py (incl. census)
    # reuse my final classifier's analyse() on the whole set
    finalmod = load("finalmod", WD / "_ce_final.py")
    full = []
    for b in resolvable:
        p = idx[b][0]
        try:
            r = finalmod.analyse(p, Path(p).read_bytes())
            full.append(dict(basename=b, in_census=b in census,
                             cls=r["cls"], statuses=r["attainable_statuses"],
                             flags=r["flags"]))
        except Exception as ex:
            full.append(dict(basename=b, in_census=b in census,
                             cls="ANALYSE_ERROR", error=str(ex)[:100]))
    zi = [r for r in full if r["cls"] in
          ("NO_EXIT_AT_ALL", "CONSTANT_EXIT")]

    out = dict(
        n_cited_basenames=len(cited),
        n_resolvable=len(resolvable),
        n_in_census_and_cited=sum(1 for r in full if r["in_census"]),
        n_out_of_census=sum(1 for r in full if not r["in_census"]),
        full_classes=dict(Counter(r["cls"] for r in full)),
        full_zero_information=len(zi),
        full_zero_information_by_class=dict(Counter(r["cls"] for r in zi)),
        out_of_census_classes=dict(Counter(
            r["cls"] for r in full if not r["in_census"])),
        out_of_census_zero_information=sum(
            1 for r in full if not r["in_census"] and
            r["cls"] in ("NO_EXIT_AT_ALL", "CONSTANT_EXIT")),
        step4b_orthogonality=ortho,
        step2c=dict(n_conditional=len(cond), n_conjunction=n_c,
                    n_not_conjunction=len(cond) - n_c,
                    category_counts=dict(Counter(
                        c for r in conj_rows for c in r["categories"])),
                    conjunction_examples=[r for r in conj_rows
                                          if r["is_conjunction"]][:12],
                    nonconjunction_examples=[r for r in conj_rows
                                             if not r["is_conjunction"]][:12],
                    rows=conj_rows),
        full=full,
    )
    (WD / "_ce_ortho_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("full", "step2c") or k == "step2c" and False},
                     ensure_ascii=False, indent=1)[:6000])
    print("WROTE", (WD / "_ce_ortho_out.json").as_posix())


if __name__ == "__main__":
    main()
