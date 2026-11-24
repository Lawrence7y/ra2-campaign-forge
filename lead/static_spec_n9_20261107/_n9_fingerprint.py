# -*- coding: utf-8 -*-
"""N-9 指纹核验：上游五件 SHA256 + 字节数，实跑核对编排方给定指纹。只读，不写任何母本。"""
import hashlib
import os

UPSTREAM = [
    r"D:\Project\ra2-campaign-forge\lead\nextstep_plan_20261106\NEXT_STEPS_20261106.md",
    r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\W8_STATIC_LOCATE\W8_STATIC_LOCATE.md",
    r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\A1_ERRATA_MAP\ERRATA_W8.md",
    r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\GOAL_RE_CONTINUOUS.md",
    r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md",
]

EXPECTED = {
    "NEXT_STEPS_20261106.md": ("c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c", 27225),
    "W8_STATIC_LOCATE.md": ("20e4eeac49254b274a8382e94505525a614ec5bf24ccb89316fcd8f914406262", 26485),
    "ERRATA_W8.md": ("660a9ecec48cabe86e8b7b8689465ff418c92b104ffa0eb1075b3ad7d96a4f05", 28443),
    "GOAL_RE_CONTINUOUS.md": ("890deedd04f3b28d001737b31f6290bdca2978251f8854dc23312bc78edb7a19", 186828),
    "GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

def main():
    ok = True
    for p in UPSTREAM:
        with open(p, "rb") as f:
            data = f.read()
        h = hashlib.sha256(data).hexdigest()
        n = os.path.getsize(p)
        name = os.path.basename(p)
        exp_hash, exp_bytes = EXPECTED[name]
        match = (h == exp_hash and n == exp_bytes)
        ok = ok and match
        print(f"{name}\n  SHA256 = {h}\n  bytes  = {n}\n  expect = {exp_hash} / {exp_bytes}\n  match  = {match}")
    print("ALL_MATCH =", ok)

if __name__ == "__main__":
    main()
