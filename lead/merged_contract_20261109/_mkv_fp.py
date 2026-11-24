# -*- coding: utf-8 -*-
"""独立复核①：实算十一件指纹，与编排方派发基线逐件比对。只读，不写任何既有件。"""
import hashlib
import os
import sys

ROOT = r"D:/Project/ra2-campaign-forge"
BASELINE = {
    "lead/r11_f2_fix_20261109/_f2_r11plus.py": ("83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75", 15723),
    "lead/r11_f2_fix_20261109/_f2_compare.py": ("12e55acf42441aca846986a2447abffef77d774ee694cedf56a012c1c8907106", 4821),
    "lead/r11_f2_fix_20261109/_f2_compare_out.json": ("148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1", 44958),
    "lead/r11_f2_fix_20261109/_f2w_checks.py": ("23c5eebb77b43e9e187be6b4736fe1f0b3f5d8eb7f46a9ee2f8af1bbbce53514", 2189),
    "lead/r11_f2_fix_20261109/_f2w_extract.py": ("1eb22164c78330e825d053f665934e9ef1e4eba14e2b101c884de68a91aad701", 1564),
    "lead/r11_f2_fix_20261109/_f2_selftest.py": ("625704697e412c30a278c616cf8be594b8b870a2734df2219aa0607aa74a19bd", 8579),
    "lead/r33e_merge_20261109/_re_linked.py": ("7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52", 19481),
    "lead/merged_consumer_audit_20261109/_mc_AUDIT.md": ("8b0be4a59bd3e88ffd908a234e9c8382a724478d93409fddf3814d5bb5aa3367", 33762),
    "lead/merged_safety_20261109/_ms_DESIGN.md": ("bc5eb5d0d13e1fbe8a67451141476c7f077ec49e0d8e9a6bbab34bc569110c44", 34299),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

print("=== §1 十一件 SHA256/字节数 实算 (hashlib, 全字节) ===")
all_ok = True
for rel, (want_sha, want_bytes) in BASELINE.items():
    p = os.path.join(ROOT, rel)
    with open(p, "rb") as f:
        b = f.read()
    got_sha = hashlib.sha256(b).hexdigest()
    got_bytes = len(b)
    ok = (got_sha == want_sha and got_bytes == want_bytes)
    all_ok = all_ok and ok
    print("被核对象 SHA256 = %s，字节数 = %d  [%s]  %s" % (got_sha, got_bytes, "MATCH" if ok else "MISMATCH", rel))
    if not ok:
        print("   EXPECT sha=%s bytes=%d" % (want_sha, want_bytes))
print("ALL_MATCH =", all_ok, " COUNT =", len(BASELINE))
