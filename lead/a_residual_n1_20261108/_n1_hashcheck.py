# -*- coding: utf-8 -*-
"""N-1 残余引用核对：上游指纹实算比对（只读，零真机，零采样代码）。"""
import hashlib
import os

BASE = r"D:\Project\ra2-campaign-forge"

EXPECTED = {
    "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md": (
        "c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c", 27225),
    "lead/re_line_20261105/A1_ERRATA_MAP/A1_ERRATA_MAP.md": (
        "d00979943bc6f26a2550340631e2d126a5b410d99a73190e1eebfcfc44e3ac13", 48180),
    "lead/re_line_20261105/A1_ERRATA_MAP/ERRATA_W8.md": (
        "660a9ecec48cabe86e8b7b8689465ff418c92b104ffa0eb1075b3ad7d96a4f05", 28443),
    "lead/re_line_20261105/D24_RULING/RULING_D24.md": (
        "56167a5e869540d7e14a7f13d29a2ed9d780d0c6352635e6e12b36cd633dcdf5", 15301),
    "lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md": (
        "20e4eeac49254b274a8382e94505525a614ec5bf24ccb89316fcd8f914406262", 26485),
}

for rel, (want_sha, want_bytes) in EXPECTED.items():
    fp = os.path.join(BASE, rel)
    with open(fp, "rb") as f:
        data = f.read()
    got_sha = hashlib.sha256(data).hexdigest()
    got_bytes = len(data)
    verdict = "MATCH" if (got_sha == want_sha and got_bytes == want_bytes) else "MISMATCH"
    print(f"{verdict}\t{got_sha}\t{got_bytes}\t{rel}")
