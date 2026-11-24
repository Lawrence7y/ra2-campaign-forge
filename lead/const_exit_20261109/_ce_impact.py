# -*- coding: utf-8 -*-
"""_ce_impact.py -- impact surface for EXIT=0 registrations.

Read-only over repo; writes only _ce_* in lead/const_exit_20261109/.
No checked script or checked gate is executed.
"""
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

pat = re.compile(r"([A-Za-z0-9_./\-]+\.py)")
mark = re.compile(r"PASS|exit\s*=\s*0|EXIT=0|SELF_TEST")
# basename is the subject of an exit=0 claim?  heuristics on line text
EXIT_CLAIM = re.compile(r"exit\s*=\s*0|EXIT\s*=\s*0|CL_EXIT=0|LINK_EXIT=0", re.I)

final = json.load(open(WD / "_ce_final_out.json", encoding="utf-8"))
orch = json.load(open(WD / "_ce_orchestrator_raw.json", encoding="utf-8"))
final_bybase = {}
for r in final["rows"]:
    final_bybase.setdefault(r["basename"], r["cls"])
orch_bybase = {}
for r in orch["const_or_noexit"]:
    orch_bybase.setdefault(os.path.basename(r["rel"]), r["cls"])
for r in orch["conditional"]:
    orch_bybase.setdefault(os.path.basename(r["rel"]), "CONDITIONAL_EXIT")


def basenames(line):
    return [os.path.basename(m.group(1).replace("\\", "/"))
            for m in pat.finditer(line)]


def exit_subject(line):
    """Which basename in the line is the SUBJECT of the EXIT=0 claim.
    Prefer the basename nearest to an exit-token, else the first basename.
    Returns None when no explicit exit=0 token."""
    if not EXIT_CLAIM.search(line):
        return None
    bs = basenames(line)
    if not bs:
        return None
    hits = [(m.start(), m.group(0)) for m in EXIT_CLAIM.finditer(line)]
    # nearest basename occurrence to the first exit token
    x = hits[0][0]
    best, dist = None, 10 ** 9
    for m in pat.finditer(line):
        d = abs(m.start() - x)
        if d < dist:
            dist, best = d, os.path.basename(m.group(1).replace("\\", "/"))
    return best


def scan(paths, label):
    rows = []
    for p in paths:
        if not p.is_file():
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for i, l in enumerate(t.split("\n"), 1):
            if not mark.search(l):
                continue
            bs = basenames(l)
            if not bs:
                continue
            rows.append(dict(file=p.as_posix().replace(str(ROOT).replace("\\", "/") + "/", ""),
                             line=i, basenames=bs,
                             exit_subject=exit_subject(l),
                             text=l.strip()[:220],
                             sha256=hashlib.sha256(l.encode("utf-8")).hexdigest()[:12]))
    return rows


def main():
    ledgers = [ROOT / "lead/PENDING_DECISIONS.md",
               ROOT / "lead/GOAL_THREE_TARGETS_20261018.md"]
    ledger_rows = scan(ledgers, "ledgers")

    md_files = []
    for dp, dn, fn in os.walk("lead"):
        dn[:] = [d for d in dn if d not in ("__pycache__", ".git")]
        if dp.count(os.sep) > 5:
            dn[:] = []
        for f in fn:
            if f.endswith(".md"):
                md_files.append(Path(dp.replace("\\", "/")) / f)
    # exclude my own write domain
    md_files = [p for p in md_files
                if "lead/const_exit_20261109" not in p.as_posix()]
    deliverable_rows = scan(md_files, "deliverables")

    def enrich(rows):
        out = []
        for r in rows:
            r = dict(r)
            r["orch_classes"] = {b: orch_bybase.get(b, "NOT_IN_413")
                                 for b in r["basenames"]}
            r["final_classes"] = {b: final_bybase.get(b, "NOT_IN_413")
                                  for b in r["basenames"]}
            r["orch_hit_flat"] = any(
                v in ("NO_EXIT_AT_ALL", "CONSTANT_EXIT")
                for v in r["orch_classes"].values())
            r["final_hit_flat"] = any(
                v in ("NO_EXIT_AT_ALL", "CONSTANT_EXIT")
                for v in r["final_classes"].values())
            r["exit_subject_final"] = (final_bybase.get(r["exit_subject"],
                                       "NOT_IN_413") if r["exit_subject"] else None)
            r["exit_subject_orch"] = (orch_bybase.get(r["exit_subject"],
                                      "NOT_IN_413") if r["exit_subject"] else None)
            out.append(r)
        return out

    ledger_rows = enrich(ledger_rows)
    deliverable_rows = enrich(deliverable_rows)

    ledger_vac_orch = [r for r in ledger_rows if r["orch_hit_flat"]]
    ledger_vac_final = [r for r in ledger_rows if r["final_hit_flat"]]
    deliv_vac_orch = [r for r in deliverable_rows if r["orch_hit_flat"]]
    deliv_vac_final = [r for r in deliverable_rows if r["final_hit_flat"]]

    # subject-level (true) zero-information EXIT=0 registrations
    ledger_subject_vac = [r for r in ledger_rows
                          if r["exit_subject_final"] in
                          ("NO_EXIT_AT_ALL", "CONSTANT_EXIT")]
    deliv_subject_vac = [r for r in deliverable_rows
                         if r["exit_subject_final"] in
                         ("NO_EXIT_AT_ALL", "CONSTANT_EXIT")]

    out = dict(
        n_md_scanned=len(md_files),
        ledger=dict(n_marked_lines=len(ledger_rows),
                    n_orch_vacuous_flat=len(ledger_vac_orch),
                    n_final_vacuous_flat=len(ledger_vac_final),
                    n_subject_vacuous=len(ledger_subject_vac),
                    lines=ledger_rows,
                    orch_vacuous=[dict(file=r["file"], line=r["line"],
                                       basenames=r["basenames"],
                                       classes=r["orch_classes"],
                                       text=r["text"])
                                  for r in ledger_vac_orch],
                    final_vacuous=[dict(file=r["file"], line=r["line"],
                                        basenames=r["basenames"],
                                        classes=r["final_classes"],
                                        text=r["text"])
                                   for r in ledger_vac_final],
                    subject_vacuous=[dict(file=r["file"], line=r["line"],
                                          subject=r["exit_subject"],
                                          cls=r["exit_subject_final"],
                                          text=r["text"])
                                     for r in ledger_subject_vac]),
        deliverables=dict(n_marked_lines=len(deliverable_rows),
                          n_orch_vacuous_flat=len(deliv_vac_orch),
                          n_final_vacuous_flat=len(deliv_vac_final),
                          n_subject_vacuous=len(deliv_subject_vac),
                          files_with_vacuous=len(set(
                              r["file"] for r in deliv_vac_final)),
                          by_file=Counter(r["file"] for r in deliv_vac_final)
                                  .most_common(25),
                          sample_subject_vacuous=[dict(
                              file=r["file"], line=r["line"],
                              subject=r["exit_subject"],
                              cls=r["exit_subject_final"],
                              text=r["text"])
                              for r in deliv_subject_vac[:25]]),
    )
    (WD / "_ce_impact_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(dict(
        n_md_scanned=len(md_files),
        ledger_n_lines=len(ledger_rows),
        ledger_orch_vac=len(ledger_vac_orch),
        ledger_final_vac_flat=len(ledger_vac_final),
        ledger_subject_vac=len(ledger_subject_vac),
        deliverable_n_lines=len(deliverable_rows),
        deliverable_orch_vac=len(deliv_vac_orch),
        deliverable_final_vac_flat=len(deliv_vac_final),
        deliverable_files_with_vac=out["deliverables"]["files_with_vacuous"],
        deliverable_subject_vac=len(deliv_subject_vac)),
        ensure_ascii=False, indent=1))
    print("WROTE", (WD / "_ce_impact_out.json").as_posix())


if __name__ == "__main__":
    main()
