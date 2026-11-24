# -*- coding: utf-8 -*-
# _eqv_lines.py — 批量抽取指定 file:line 原文（只读）。参数 mode:
#   audit   — TAUTOLOGY_AUDIT.md 判据段
#   anchors — 三关/抽样引用的锚点行
import sys, pathlib, json

ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")

RANGES = {
    "audit": [("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md", [(254, 271), (314, 318), (437, 461), (534, 551), (563, 572), (605, 612), (690, 704), (726, 732), (756, 764), (366, 372), (474, 476)])],
    "anchors": [
        ("lead/layer_identity_20261109/LAYER_IDENTITY.md", [(13, 13), (104, 104), (122, 122), (126, 128), (189, 189), (267, 267), (338, 338), (365, 365), (376, 376), (384, 384), (393, 393), (223, 223), (242, 242)]),
        ("lead/layer_identity_20261109/_li_LAYER_IDENTITY_PROOF_20261109.md", [(78, 78), (125, 125), (146, 146)]),
        ("lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", [(21, 21), (104, 106), (107, 108), (126, 126)]),
        ("lead/keff_calc_20261109/KEFF_CALC.md", [(262, 262), (314, 314), (340, 340), (432, 440)]),
        ("lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md", [(149, 149), (294, 294), (302, 302)]),
        ("lead/score_decomp_20261109/SCORE_DECOMP.md", [(235, 235)]),
        ("lead/comparability_20261109/COMPARABILITY_AUDIT.md", [(158, 158)]),
        ("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md", [(356, 356), (366, 366)]),
    ],
}

mode = sys.argv[1] if len(sys.argv) > 1 else "anchors"
for rel, ranges in RANGES[mode]:
    p = ROOT / rel
    lines = p.read_bytes().decode("utf-8", errors="replace").split("\n")
    print(f"===== {rel} (n_lines={len(lines)})")
    for a, b in ranges:
        for n in range(a, b + 1):
            if 1 <= n <= len(lines):
                print(f"{rel}:{n}\t{lines[n-1]}")
            else:
                print(f"{rel}:{n}\t<OUT OF RANGE file has {len(lines)} lines>")
        if b > a:
            print("---")
