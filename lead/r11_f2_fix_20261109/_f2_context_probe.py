# -*- coding: utf-8 -*-
"""_f2_context_probe.py — 形态核对探针（第一步补充）：只读。
1) 关键对象现盘存在性+指纹（绑定行声明的对象到底在不在盘、hash 是否吻合）；
2) 6 份含绑定行文档的关键行全文（不被截断）与相邻 ±4 行；
3) 每份文档全文内全部反引号路径形跨度清单（判断路径是否存在于 ±1 行之外）。
"""
import hashlib
import json
import re
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
OUT = REPO / "lead" / "r11_f2_fix_20261109" / "_f2_context_probe_out.txt"
P = re.compile(r"`([^`\n]{1,200})`")

def sha(p):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)

lines_out = []
def w(s=""):
    lines_out.append(s)

w("== A. 关键对象现盘指纹 ==")
probes = [
    ("lead/b_unclosed_trace_20261108/_dB_anchor_recompute_out.txt", "4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b8e0a1a"),
    ("lead/b_unclosed_trace_20261108/CRITERIA_COMPARE.md", None),
    ("lead/a_dim_reduced_20261108/_ar_out.txt", "28cd3794a571d0ac8958b2fa98bc7906e61414f749111fc18f02de4294642a72"),
    ("lead/b2b_isolated_20261107/qc151_trip.isolated.py", "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2"),
    ("lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md", "cb4f3011a75f616032524814cba9c05e055ca41636836f7e3a15d6d876e8d306"),
    ("lead/r2_unclosed_b_20261108/B_BREAKPOINTS_2_6.md", "3aad3bddda087e171d9add1977849b70c01f7ddb5dff23b575186dfb517403ae"),
    ("lead/r2_final_grade_20261108/R2_FINAL_GRADE.md", "7ce09812f7bd905a95114a2cc2cea56b3dc3dbaef3d8e0d14c58685762ecab24"),
    ("lead/dtrigger_round2_20261107/_verify_B_out.txt", "4ee6a6b78d80a336c3431a6f71d9f5a77fec93ef65b7a4c642a49b669368c107"),
    ("lead/b_unclosed_trace_20261108/_bt_B崩点2_尾串追溯_20261108.md", "793e06d278456cf08f7df6b76d21c64bb9b419a3ebc1ca37dcb2d47135b559ea"),
]
for rel, expect in probes:
    p = REPO / rel
    if p.is_file():
        h, n = sha(p)
        mark = "MATCH" if (expect is None or h == expect) else "MISMATCH(声明=%s)" % expect[:12]
        w("  在盘 %s  sha=%s bytes=%d  vs声明: %s" % (rel, h, n, mark))
    else:
        w("  不在盘 %s" % rel)

docs = [
    ("lead/a_dim_reduced_20261108/A_REDUCED_FORM.md", [93], 2),
    ("lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md", [130], 6),
    ("lead/b2b_isolated_20261107/INTEGRATION_REPORT.md", [31, 147], 3),
    ("lead/b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md", [5], 4),
    ("lead/bexec_n4_20261108/B_EXECUTION_SPEC.md", [51, 52, 53, 227, 228, 229], 3),
    ("lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md", [28, 29], 3),
    ("lead/b_unclosed_trace_20261108/B_BREAKPOINT2_TRACE.md", [5, 6, 7, 8, 59, 60, 61, 64], 2),
]
w("")
w("== B. 关键行全文与相邻行 ==")
for rel, lnos, ctx in docs:
    p = REPO / rel
    ls = p.read_text(encoding="utf-8").split("\n")
    w("--- %s (共 %d 行) ---" % (rel, len(ls)))
    show = set()
    for ln in lnos:
        for d in range(-ctx, ctx + 1):
            i = ln - 1 + d
            if 0 <= i < len(ls):
                show.add(i)
    for i in sorted(show):
        mark = " <<<" if (i + 1) in lnos else ""
        w("  L%4d%s| %s" % (i + 1, mark, ls[i]))

w("")
w("== C. 各文档全文反引号跨度（含路径形判断） ==")
PATHY = re.compile(r"([^`\n]*[/\\][^`\n]*|[^`\n]*\.(?:md|txt|py|json|log)[^`\n]*)")
for rel, lnos, ctx in docs:
    p = REPO / rel
    ls = p.read_text(encoding="utf-8").split("\n")
    w("--- %s ---" % rel)
    for i, line in enumerate(ls):
        for m in P.finditer(line):
            c = m.group(1)
            if PATHY.fullmatch(c):
                w("  L%4d  `%s`" % (i + 1, c))

OUT.write_text("\n".join(lines_out), encoding="utf-8")
print("已写 %s（%d 行）" % (OUT, len(lines_out)))
