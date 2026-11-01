# -*- coding: utf-8 -*-
"""_make_harness8v4_copy.py — harness8 v3（37a7c9cd）→ v4 候选 逐字节复制。"""

import hashlib
import shutil

SRC = r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v3.py"
DST = r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py"
SRC_EXPECT16 = "37a7c9cdf2ca97e3"


def _sha16(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


shutil.copyfile(SRC, DST)
print("v3 sha16=%s  v4 sha16=%s" % (_sha16(SRC), _sha16(DST)))
assert _sha16(SRC) == _sha16(DST)
print("BYTE_EXACT_OK")
