# -*- coding: utf-8 -*-
"""N-4 指纹核对：只读计算 SHA256 与字节数，不修改任何文件。"""
import hashlib

FILES = [
    r"D:\Project\ra2-campaign-forge\lead\nextstep_plan_20261106\NEXT_STEPS_20261106.md",
    r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\B1_HARNESS_PATCH\B2_FIX_DESIGN.md",
    r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\D24_RULING\RULING_D24.md",
    r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py",
    r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py",
]

for p in FILES:
    with open(p, "rb") as f:
        data = f.read()
    print(p)
    print("  SHA256 = %s" % hashlib.sha256(data).hexdigest())
    print("  bytes  = %d" % len(data))
