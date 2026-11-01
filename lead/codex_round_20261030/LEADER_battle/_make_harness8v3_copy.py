# -*- coding: utf-8 -*-
"""_make_harness8v3_copy.py — harness8 v2（dd5459fe，字节冻结）→ v3 候选 逐字节复制。

★ v2 零改动（C-R5 冻结维持）；v3=同目录新文件 qc151_trip.harness8_v3.py，增量补丁另行经 Edit 门施加。
"""

import hashlib
import shutil

SRC = r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8.py"
DST = r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v3.py"
SRC_EXPECT16 = "dd5459fe0cf3461c"


def _sha16(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def main():
    src16 = _sha16(SRC)
    if src16 != SRC_EXPECT16:
        raise SystemExit("V2 FROZEN MISMATCH: %s != %s" % (src16, SRC_EXPECT16))
    shutil.copyfile(SRC, DST)
    print("copied ->", DST)
    print("v2 sha16=%s  v3 sha16=%s" % (_sha16(SRC), _sha16(DST)))
    assert _sha16(SRC) == _sha16(DST)
    print("BYTE_EXACT_OK")


if __name__ == "__main__":
    main()
