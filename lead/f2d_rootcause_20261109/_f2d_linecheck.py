# -*- coding: utf-8 -*-
"""F2-d 调查：10 条候选行原文提取 + 所在文件指纹（只读）"""
import hashlib, json, os

ROOT = r"D:\Project\ra2-campaign-forge"
FILES = {
    "F1": "lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md",
    "F2": "lead/b2b_isolated_20261107/INTEGRATION_REPORT.md",
    "F3": "lead/b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md",
    "F4": "lead/bexec_n4_20261108/B_EXECUTION_SPEC.md",
    "F5": "lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md",
}
LINES = {
    "F1": [130],
    "F2": [31, 147, 148],
    "F3": [5],
    "F4": [51, 52, 53, 228, 229],
    "F5": [28, 29],
}
W = 2  # ±2 行

out = {}
for k, rel in FILES.items():
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    b = open(p, "rb").read()
    sha = hashlib.sha256(b).hexdigest()
    text = b.decode("utf-8")
    nl = text.splitlines()
    out[k] = {"path": rel, "sha256": sha, "bytes": len(b), "total_lines": len(nl), "lines": {}}
    for ln in LINES[k]:
        lo, hi = max(1, ln - W), min(len(nl), ln + W)
        out[k]["lines"][ln] = {
            "%d" % i: nl[i - 1] for i in range(lo, hi + 1)
        }

print(json.dumps(out, ensure_ascii=False, indent=1))
