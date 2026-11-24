# -*- coding: utf-8 -*-
"""N-11 分流前置：上游四件指纹实算（Python hashlib）。只读；零真机；零采样代码。
预期值来源：本任务任务书【上游指纹】块。"""
import hashlib
import os

BASE = r"D:\Project\ra2-campaign-forge"
ITEMS = [
    ("lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md",
     "c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c", 27225),
    ("lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
     "e7c29e06f48b2380d5bec3f99e08ac2a4ce90d94da27b48b98d5eb2113a75d60", 23707),
    ("lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md",
     "5b933fe2fcb3cc35c5026cb57b45f29da29c90b67a618346af248744ed3ccdb9", 32281),
    ("lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]


def main():
    all_match = True
    for rel, exp_sha, exp_bytes in ITEMS:
        p = os.path.join(BASE, rel.replace("/", os.sep))
        h = hashlib.sha256()
        n = 0
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
                n += len(chunk)
        got = h.hexdigest()
        ok = (got == exp_sha) and (n == exp_bytes)
        all_match = all_match and ok
        print("[%s] %s" % ("MATCH" if ok else "MISMATCH", rel))
        print("  sha256 = %s" % got)
        print("  bytes  = %d  (expected %d)" % (n, exp_bytes))
    print("ALL_MATCH = %s" % all_match)


if __name__ == "__main__":
    main()
