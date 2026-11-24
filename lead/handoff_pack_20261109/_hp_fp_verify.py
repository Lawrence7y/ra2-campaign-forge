# -*- coding: utf-8 -*-
# _hp_fp_verify.py — 批准包整编员：对编排方指纹逐件实跑 hashlib 核验
# 只读不写源域；输出到 stdout。运行: python -I -X utf8 _hp_fp_verify.py
import hashlib, os, sys

ROOT = r"D:\Project\ra2-campaign-forge"
EXPECT = {
    "lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md": ("b1231ccb8b80c5200e2ff33b15e09ae52b0452a1481dfc7989730f7da16eda5b", 22048),
    "lead/v2_precision_fix_20261108/_pf2_findings_20261109.md": ("4aef8957094008262d980640836ab0aec3e797f892b25fe8ff02b6aa87957fe4", 7966),
    "lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md": ("6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8", 29818),
    "lead/w2_samecause_20261109/W2_SAME_CAUSE.md": ("75a0369b97f72f9d615ced86c580c6e63bfcce4f29de1c86bd74e8542aa5c895", 19552),
    "lead/text_fix_unified_20261109/_uf_UNIFIED_FIX_LIST_20261109.md": ("441b073a39a2ac195d90d43e3ba85f3c2202d5fafce31bec9c96e000a01e0923", 25095),
    "lead/u5u6_mirror_20261109/_m5_cells.json": ("ce89f6463d1b2fb64deae55f869db4d94086bcb4bce868cec3870317b2c63bf3", 2525),
    "lead/u5u6_mirror_20261109/U5U6_MIRROR_TEXTS.md": ("f320a80110806e6b57281988085d40776b43e719123db29cdb6564fe68c6c545", 24897),
    "lead/counterpart_fix_20261109/COUNTERPART_FIX.md": ("MISSING", 0),
    "lead/strict_exposure_20261109/STRICT_EXPOSURE.md": ("3a4b1bb7cf7f0bd501b3e99d575c4907dd0e17f5557dd0b8826e5fb07fe2bdc8", 23798),
    "lead/b2b_design_20261106/STATE_MATRIX.json": ("1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558),
    "lead/b2b_design_20261106/B2B_DESIGN.md": ("565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735),
    "lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md": ("c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801", 28897),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

rows = []
for rel, (exp_sha, exp_n) in EXPECT.items():
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.exists(p):
        rows.append((rel, "ABSENT", "-", "-"))
        continue
    n = os.path.getsize(p)
    sha = sha256_file(p)
    ok = "OK" if (exp_sha != "MISSING" and sha == exp_sha and n == exp_n) else ("MISSING_AS_EXPECTED" if exp_sha == "MISSING" else "MISMATCH")
    rows.append((rel, ok, sha, str(n)))

w = max(len(r[0]) for r in rows)
for rel, ok, sha, n in rows:
    print(f"{ok:16s} {rel:{w}s} sha256={sha} bytes={n}")

# 附带核验 U8/U9 目标件（不在编排方指纹表内，仅登记）
extra = r"D:\Project\ra2-campaign-forge\lead\matrix_reach_20261109\MATRIX_DEFECT_REACHABILITY.md"
if os.path.exists(extra):
    print(f"EXTRA_OK        {extra} sha256={sha256_file(extra)} bytes={os.path.getsize(extra)}")
else:
    print("EXTRA_ABSENT    MATRIX_DEFECT_REACHABILITY.md")
