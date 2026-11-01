# -*- coding: utf-8 -*-
"""_make_judge_h8_copy.py — 判档器母本 → harness8 判档器副本 逐字节复制（XVERIFY_H8 Y-1 接入）。"""

import hashlib
import shutil

SRC = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\_judge_l1_20261023.py"
DST = r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\_judge_h8_20261031.py"


def _sha16(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


shutil.copyfile(SRC, DST)
print("copied ->", DST)
print("src sha16=%s dst sha16=%s" % (_sha16(SRC), _sha16(DST)))
assert _sha16(SRC) == _sha16(DST)
print("BYTE_EXACT_OK")
