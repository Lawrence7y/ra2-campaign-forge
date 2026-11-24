# -*- coding: utf-8 -*-
"""_bt_hashcheck.py — 只读核对编排方给定的三件 SHA256/字节数（hashlib 实算）。
运行: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/b_unclosed_trace_20261108/_bt_hashcheck.py
"""
import hashlib
import os
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
TARGETS = [
    r"lead\r2_unclosed_b_20261108\B_BREAKPOINTS_2_6.md",
    r"lead\r2_final_grade_20261108\R2_FINAL_GRADE.md",
    r"lead\dtrigger_round2_20261107\_verify_B_out.txt",
]

for rel in TARGETS:
    p = os.path.join(ROOT, rel)
    try:
        with open(p, "rb") as f:
            data = f.read()
    except OSError as e:
        print(f"{rel}\tREAD_FAIL\t{e}")
        continue
    h = hashlib.sha256(data).hexdigest()
    print(f"{rel}\tsha256={h}\tbytes={len(data)}\tsys_size={os.path.getsize(p)}")
sys.stdout.flush()
