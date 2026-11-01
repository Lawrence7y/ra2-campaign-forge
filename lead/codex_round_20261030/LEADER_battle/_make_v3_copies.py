# -*- coding: utf-8 -*-
"""_make_v3_copies.py — 发射器/判档器 v2 副本 → v3 副本 逐字节复制（编辑另行经 Edit 门）。"""

import hashlib
import shutil

PAIRS = [
    (r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\_launch_h8_20261031.py",
     r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\_launch_h8v3_20261101.py"),
    (r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\_judge_h8_20261031.py",
     r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\_judge_h8v3_20261101.py"),
]


def _sha16(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


for src, dst in PAIRS:
    shutil.copyfile(src, dst)
    print("copied %s -> %s (sha16 %s)" % (src.split("\\")[-1], dst.split("\\")[-1], _sha16(dst)))
print("OK")
