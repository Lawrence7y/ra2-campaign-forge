# -*- coding: utf-8 -*-
"""_crev_ (R-061/R-062 independent review) -- reconciliation:
(1) suite CASES literals (AST-extracted, suite not executed) vs freeze manifests:
    full (case, mut, red) three-field comparison, 194 + 112 rows.
(2) freeze run1 records vs manifests: case-set equality, EXACT counts, tally.
Independent reviewer script; reads only; writes nothing.
"""
import ast
import json
import re
import sys

ROOT = r"D:\Project\ra2-campaign-forge"


def cases_from_suite(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "CASES":
                    return ast.literal_eval(node.value)
    raise SystemExit("CASES not found in " + path)


def norm_red(r):
    return sorted(r)


def cmp_manifest(suite_cases, manifest, tag):
    rows = manifest.get("rows") or manifest.get("cases")
    assert len(rows) == len(suite_cases), (tag, len(rows), len(suite_cases))
    m_by_case = {}
    for r in rows:
        m_by_case[r["case"]] = r
    problems = []
    names = [c[0] for c in suite_cases]
    if len(set(names)) != len(names):
        problems.append("duplicate case names in suite")
    for name, mut, red in suite_cases:
        r = m_by_case.get(name)
        if r is None:
            problems.append("%s missing in manifest" % name)
            continue
        m1 = {k if isinstance(k, int) else int(k, 0): v for k, v in mut.items()}
        m2 = {k if isinstance(k, int) else int(k, 0): v
              for k, v in r["mut"].items()}
        if m1 != m2:
            problems.append("%s MUT diff suite=%s manifest=%s" % (name, m1, m2))
        if norm_red(red) != norm_red(r["red"]):
            problems.append("%s RED diff suite=%s manifest=%s" % (name, red, r["red"]))
    print("[%s] suite-vs-manifest: %d/%d three-field MATCH, problems=%d"
          % (tag, len(suite_cases) - len(problems), len(suite_cases), len(problems)))
    for p in problems[:20]:
        print("   !", p)
    return problems


def check_run1(run1_path, manifest, tag, printed_exp):
    txt = open(run1_path, encoding="utf-8", errors="replace").read()
    lines = [l.rstrip("\r") for l in txt.split("\n")]
    rows = manifest.get("rows") or manifest.get("cases")
    cases = {r["case"] for r in rows}
    exact_lines = []
    for l in lines:
        mm = re.match(r"^(\S+)\s+(?:[\d.]+s\s+)?EXACT(?:\s+(.*))?$", l.strip())
        if mm:
            exact_lines.append((mm.group(1), mm.group(2)))
    exact_names = [e[0] for e in exact_lines]
    n_exact = len(exact_names)
    problems = []
    if set(exact_names) != cases:
        problems.append("case-set diff: run1-only=%s manifest-only=%s"
                        % (sorted(set(exact_names) - cases)[:5],
                           sorted(cases - set(exact_names))[:5]))
    if n_exact != len(cases):
        problems.append("EXACT count %d != %d" % (n_exact, len(cases)))
    if printed_exp:
        for nm, exp in exact_lines:
            if exp is None:
                problems.append("%s: no exp printed" % nm)
                continue
            want = sorted(rows[[r["case"] for r in rows].index(nm)]["red"])
            try:
                got = sorted(ast.literal_eval(exp.strip()))
            except Exception:
                problems.append("%s: exp not a literal: %r" % (nm, exp))
                continue
            if got != want:
                problems.append("%s printed-exp %s != manifest red %s"
                                % (nm, got, want))
    # tally block
    tal = re.search(r"cases=(\d+) exact=(\d+) survived=(\d+) exc=(\d+) "
                    r"splice-mismatch=(\d+) full-mismatch=(\d+)", txt)
    if not tal:
        problems.append("tally block not found")
    else:
        c_, e_, s_, x_, sm, fm = map(int, tal.groups())
        man = {"cases": len(rows),
               "killed": manifest.get("killed", manifest.get("tally", {}).get("killed")),
               "survived": manifest.get("survived", manifest.get("tally", {}).get("survived")),
               "exc": manifest.get("exc", manifest.get("tally", {}).get("exc")),
               "mismatch": manifest.get("mismatch", manifest.get("tally", {}).get("mismatch"))}
        if (c_, e_, s_, x_) != (man["cases"], man["killed"], man["survived"], man["exc"]):
            problems.append("tally run1=(%d,%d,%d,%d) manifest=%s"
                            % (c_, e_, s_, x_, man))
        if sm + fm != man["mismatch"]:
            problems.append("mismatch fields sm+fm=%d manifest mismatch=%d"
                            % (sm + fm, man["mismatch"]))
    if "EXIT=0" not in txt:
        problems.append("EXIT=0 line missing")
    unc = re.search(r"uncovered=(\d+) phantom-expectations=(\d+)", txt)
    if unc and (int(unc.group(1)), int(unc.group(2))) != (0, 0):
        problems.append("uncovered/phantom nonzero: %s" % (unc.groups(),))
    print("[%s] run1-vs-manifest: EXACT=%d manifest-cases=%d problems=%d"
          % (tag, n_exact, len(cases), len(problems)))
    for p in problems[:20]:
        print("   !", p)
    return problems


def main():
    m61 = json.load(open(ROOT + r"\out\_r061_freeze5.json"))
    m62 = json.load(open(ROOT + r"\out\_r062_freeze.json"))
    # provenance self-consistency of manifests
    import hashlib
    gate61 = hashlib.sha256(open(ROOT + r"\re_atlas\tools\r061_witness_this_contract.py", "rb").read()).hexdigest()
    gate62 = hashlib.sha256(open(ROOT + r"\re_atlas\tools\r062_upward_trace_contract.py", "rb").read()).hexdigest()
    img = hashlib.sha256(open(ROOT + r"\ra2youli\gamemd.exe", "rb").read()).hexdigest()
    print("manifest-embedded hashes: r61 gate ok=%s image ok=%s | r62 gate ok=%s image ok=%s"
          % (m61["gate_sha256"] == gate61, m61["image_sha256"] == img,
             m62["gate_sha256"] == gate62, m62["image_sha256"] == img))
    p1 = cmp_manifest(cases_from_suite(ROOT + r"\re_atlas\tools\mutate_r061_gate.py"), m61, "R61")
    p2 = cmp_manifest(cases_from_suite(ROOT + r"\re_atlas\tools\mutate_r062_gate.py"), m62, "R62")
    p3 = check_run1(ROOT + r"\out\_r061_freeze_run1.txt", m61, "R61", printed_exp=True)
    p4 = check_run1(ROOT + r"\out\_r062_freeze_run1.txt", m62, "R62", printed_exp=False)
    tot = len(p1) + len(p2) + len(p3) + len(p4)
    print("TOTAL PROBLEMS:", tot)
    sys.exit(1 if tot else 0)


if __name__ == "__main__":
    main()
