# -*- coding: utf-8 -*-
"""F2V-01: 独立实算 6 个保护件/基线件指纹 + 被核对象(补丁模块)指纹。只读。"""
import hashlib
import os
import sys

REPO = r"D:\Project\ra2-campaign-forge"
TARGETS = [
    (r"lead\gate_fp7_20261108\_g7_predicates.py", "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    (r"lead\gate_r9r12_20261109\_g9_gate.py", "a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6", 11623),
    (r"lead\gate_r9r12_20261109\_g9_regression_out.json", "7f16da217dba02008546d643bb51c0100d7126939df947ad0c46a4fd478f11d8", 123691),
    (r"lead\gate_r9r12_20261109\GATE_R9R12_REGRESSION.md", "dc222c2409db9a63c1e2cd95b979069a16b5067585bd8a46d7a9d40657fe27c0", 37578),
    (r"lead\PENDING_DECISIONS.md", "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    (r"lead\GOAL_THREE_TARGETS_20261018.md", "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    # 被核对象：修补回件的补丁模块
    (r"lead\r11_f2_fix_20261109\_f2_r11plus.py", "83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75", 15723),
    (r"lead\r11_f2_fix_20261109\_f2_F2_PATCH_REPORT.md", "0b10d1d0b6d2e86bef6cb40918bd17f625c8880d973adb9b99cb172e1727aab5", 17451),
]

for rel, exp_sha, exp_bytes in TARGETS:
    p = os.path.join(REPO, rel)
    try:
        data = open(p, "rb").read()
    except OSError as e:
        print("MISSING", rel, e)
        continue
    sha = hashlib.sha256(data).hexdigest()
    n = len(data)
    ok_sha = "OK" if sha == exp_sha else "MISMATCH"
    ok_bytes = "OK" if n == exp_bytes else "MISMATCH"
    print(f"{rel}\n  sha256={sha} [{ok_sha}]\n  bytes={n} [{ok_bytes}]")
print("done")
