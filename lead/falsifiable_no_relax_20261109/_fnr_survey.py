# -*- coding: utf-8 -*-
r"""_fnr_survey.py -- UTF-8-clean survey of "X did not Y" assertions in lead/.

READ-ONLY scan. Writes only into the sole write domain.
"""
from __future__ import annotations
import json, os, re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "falsifiable_no_relax_20261109"
PAT = re.compile(r"no_relaxation|no_regression|没有引入新漏报|无新漏报|没放松|"
                 r"未放宽|不放宽|不扩散|unchanged|零改动|未变|训练集\s*=\s*测试集|"
                 r"结构性恒|白名单外\s*0|不另下结论(?!.*样本)")

# limit to the recent audit domains + the two ledgers (no _dnv/_dnw sandbox dupes)
SCAN_DIRS = [
    "lead/gate_r9sem_20261109", "lead/whitelist_audit_20261109",
    "lead/gate_pipeline_20261109", "lead/chain_vs_single_20261109",
    "lead/gate_n13_20261109", "lead/gate_v1v2_20261109",
    "lead/gate_fp7_20261108", "lead/gate_postmortem_20261109",
    "lead/count_invariant_20261109", "lead/check_masking_20261109",
    "lead/evidence_indep_20261109", "lead/c07_hardening_20261109",
    "lead/c07_protocol_attacks_20261109",
]

def main():
    rows = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in (".md", ".py", ".json", ".txt"):
                continue
            if "_dnv_sandbox" in str(p) or "_dnw_sandbox" in str(p):
                continue
            try:
                ls = p.read_text(encoding="utf-8", errors="replace").split("\n")
            except Exception:
                continue
            for i, l in enumerate(ls, 1):
                if PAT.search(l):
                    rows.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"),
                                 "line": i, "text": l.strip()[:230]})
    print("TOTAL MATCH LINES =", len(rows))
    # group by directory
    by = {}
    for r in rows:
        k = "/".join(r["path"].split("/")[:2])
        by.setdefault(k, []).append(r)
    for k in sorted(by):
        print("\n### %s  (%d lines)" % (k, len(by[k])))
        for r in by[k][:12]:
            print("  %s:%d | %s" % (r["path"], r["line"], r["text"]))
        if len(by[k]) > 12:
            print("  ... +%d more" % (len(by[k]) - 12))
    (WDIR / "_fnr_survey_out.json").write_text(
        json.dumps({"n_lines": len(rows), "by_dir": {k: len(v) for k, v in by.items()},
                    "rows": rows}, ensure_ascii=False, indent=1),
        encoding="utf-8", newline="\n")
    print("\nWROTE _fnr_survey_out.json")

if __name__ == "__main__":
    main()
