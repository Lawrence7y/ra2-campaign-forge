# -*- coding: utf-8 -*-
"""_cew_evidence.py -- my own read-only evidence CLASSIFIER for the writer task.

Pure AST + text enumeration.  Never executes any checked script or gate.
Reads only; writes only _cew_* inside lead/const_exit_20261109/.

Produces per-item file:line evidence for all 413 archived rows, plus a
recomputed text-layer magnitude for lead/**.md (incl. / excl. the 2 ledgers).
"""
import ast
import hashlib
import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "const_exit_20261109"
os.chdir(ROOT)


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


def scan_py(rel):
    p = ROOT / rel
    raw = p.read_bytes()
    tree = ast.parse(raw.decode("utf-8-sig", errors="replace"))
    n_lines = len(raw.decode("utf-8-sig", errors="replace").split("\n"))
    sites = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and callee(n) in ("exit", "quit", "_exit"):
            e = n.args[0] if n.args else None
            sites.append(dict(line=n.lineno, tag="call:" + callee(n),
                              expr=ast.unparse(e) if e else "None"))
        elif isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call) \
                and callee(n.exc) == "SystemExit":
            e = n.exc.args[0] if n.exc.args else None
            sites.append(dict(line=n.lineno, tag="raise:SystemExit",
                              expr=ast.unparse(e) if e else "None"))
    sites.sort(key=lambda s: s["line"])
    fnrets = []
    for f in ast.walk(tree):
        if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)):
            rs = own_returns(f)
            fnrets.append(dict(func=f.name, line=f.lineno,
                               returns=[[r.lineno, ast.unparse(r.value) if r.value else "None"]
                                        for r in rs]))
    return dict(rel=rel, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                n_lines=n_lines, n_sites=len(sites), sites=sites,
                func_returns=fnrets)


def main():
    final = json.load(open(WD / "_ce_final_out.json", encoding="utf-8"))
    rows = final["rows"]
    ev = {}
    for r in rows:
        ev[r["rel"]] = scan_py(r["rel"])
    by_cls = {}
    for r in rows:
        by_cls.setdefault(r["cls"], []).append(r["rel"])
    # sanity: my own AST site count vs archived n_sites
    mism = [(r["rel"], r["n_sites"], ev[r["rel"]]["n_sites"])
            for r in rows if r["n_sites"] != ev[r["rel"]]["n_sites"]]

    pat = re.compile(r"([A-Za-z0-9_./\-]+\.py)")
    mark = re.compile(r"PASS|exit\s*=\s*0|EXIT=0|SELF_TEST")
    exit_claim = re.compile(r"exit\s*=\s*0|EXIT\s*=\s*0|CL_EXIT=0|LINK_EXIT=0", re.I)
    final_bybase = {}
    for r in rows:
        final_bybase.setdefault(r["basename"], r["cls"])
    orch = json.load(open(WD / "_ce_orchestrator_raw.json", encoding="utf-8"))
    orch_bybase = {}
    for r in orch["const_or_noexit"]:
        orch_bybase.setdefault(os.path.basename(r["rel"]), r["cls"])
    for r in orch["conditional"]:
        orch_bybase.setdefault(r["basename"], "CONDITIONAL_EXIT")

    LEDGERS = {"lead/PENDING_DECISIONS.md", "lead/GOAL_THREE_TARGETS_20261018.md"}
    md_files = []
    for dp, dn, fn in os.walk("lead"):
        dn[:] = [d for d in dn if d not in ("__pycache__", ".git")]
        if dp.count(os.sep) > 5:
            dn[:] = []
        for f in fn:
            if f.endswith(".md"):
                md_files.append(Path(dp.replace("\\", "/")) / f)
    md_files = [p for p in md_files
                if "lead/const_exit_20261109" not in p.as_posix()]

    def subject(line):
        if not exit_claim.search(line):
            return None
        ms = list(pat.finditer(line))
        if not ms:
            return None
        x = list(exit_claim.finditer(line))[0].start()
        best = min(ms, key=lambda m: abs(m.start() - x))
        return os.path.basename(best.group(1).replace("\\", "/"))

    marked = []
    for p in md_files:
        t = p.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(t.split("\n"), 1):
            if not mark.search(line):
                continue
            bs = [os.path.basename(m.group(1).replace("\\", "/"))
                  for m in pat.finditer(line)]
            if not bs:
                continue
            rel = p.as_posix()
            s = subject(line)
            fs = {b: final_bybase.get(b, "NOT_IN_413") for b in bs}
            os_ = {b: orch_bybase.get(b, "NOT_IN_413") for b in bs}
            marked.append(dict(file=rel, line=i, basenames=bs, subject=s,
                               flat_final=any(v in ("NO_EXIT_AT_ALL", "CONSTANT_EXIT")
                                              for v in fs.values()),
                               flat_orch=any(v in ("NO_EXIT_AT_ALL", "CONSTANT_EXIT")
                                             for v in os_.values()),
                               subj_cls=final_bybase.get(s, "NOT_IN_413") if s else None,
                               text=line.strip()[:200]))
    subj_vac = lambda r: r["subj_cls"] in ("NO_EXIT_AT_ALL", "CONSTANT_EXIT")
    stats = dict(
        n_md=len(md_files),
        all=dict(n_marked=len(marked),
                 n_flat_final=sum(r["flat_final"] for r in marked),
                 n_flat_orch=sum(r["flat_orch"] for r in marked),
                 n_subject_vac=sum(subj_vac(r) for r in marked),
                 n_files_flat_final=len({r["file"] for r in marked if r["flat_final"]}),
                 n_files_subject_vac=len({r["file"] for r in marked if subj_vac(r)})),
        excl_ledgers=dict(
            n_marked=sum(r["file"] not in LEDGERS for r in marked),
            n_flat_final=sum(r["flat_final"] and r["file"] not in LEDGERS for r in marked),
            n_flat_orch=sum(r["flat_orch"] and r["file"] not in LEDGERS for r in marked),
            n_subject_vac=sum(subj_vac(r) and r["file"] not in LEDGERS for r in marked),
            n_files_flat_final=len({r["file"] for r in marked
                                    if r["flat_final"] and r["file"] not in LEDGERS}),
            n_files_subject_vac=len({r["file"] for r in marked
                                     if subj_vac(r) and r["file"] not in LEDGERS})),
        ledgers=dict(
            n_marked=sum(r["file"] in LEDGERS for r in marked),
            n_flat_final=sum(r["flat_final"] and r["file"] in LEDGERS for r in marked),
            n_flat_orch=sum(r["flat_orch"] and r["file"] in LEDGERS for r in marked),
            n_subject_vac=sum(subj_vac(r) and r["file"] in LEDGERS for r in marked)),
    )
    out = dict(n_rows=len(rows), by_cls={k: len(v) for k, v in by_cls.items()},
               n_site_count_mismatch=len(mism), site_count_mismatch=mism[:20],
               evidence=ev, text_stats=stats,
               text_lines_ledger=[r for r in marked if r["file"] in LEDGERS],
               text_lines_subject_vac=[dict(file=r["file"], line=r["line"],
                                            subject=r["subject"], cls=r["subj_cls"],
                                            text=r["text"])
                                       for r in marked if subj_vac(r)])
    (WD / "_cew_evidence_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(dict(n_rows=len(rows), by_cls={k: len(v) for k, v in by_cls.items()},
                          n_site_count_mismatch=len(mism), text_stats=stats),
                     ensure_ascii=False, indent=1))
    print("WROTE", (WD / "_cew_evidence_out.json").as_posix())


if __name__ == "__main__":
    main()
