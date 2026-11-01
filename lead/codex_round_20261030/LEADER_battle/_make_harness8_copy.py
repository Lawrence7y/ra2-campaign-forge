# -*- coding: utf-8 -*-
"""_make_harness8_copy.py — harness7 母本 → harness8 候选 逐字节复制。

★ 常量路径；shutil.copyfile 逐字节；复制后双 sha256 对账。
★ 补丁另行经 Edit 门以加性块施加（见 HARNESS8_FRAME_BOUND_DESIGN_20261031.md §2）。
"""

import hashlib
import os
import shutil

SRC = r"D:\Project\ra2-campaign-forge\lead\goal1_harness7_20261023\qc151_trip.harness7.py"
DST = r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8.py"
SRC_EXPECT16 = "d019e8beecfb5fd8"


def _sha16(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def main():
    src16 = _sha16(SRC)
    if src16 != SRC_EXPECT16:
        raise SystemExit("FROZEN MASTER MISMATCH: %s != %s" % (src16, SRC_EXPECT16))
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    shutil.copyfile(SRC, DST)
    print("copied %s -> %s" % (SRC, DST))
    print("src sha16=%s" % _sha16(SRC))
    print("dst sha16=%s" % _sha16(DST))
    assert _sha16(SRC) == _sha16(DST), "copy not byte-exact"
    print("BYTE_EXACT_OK")


if __name__ == "__main__":
    main()
