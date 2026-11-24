# -*- coding: utf-8 -*-
# 本会话实算：11 件编排方派发指纹（只读 hashlib 全字节），并生成严格格式绑定行
import hashlib, os

ROOT = "D:/Project/ra2-campaign-forge"
BASE = {
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

print("== §FP 11 件实算 ==")
allok = True
for rel, (exp_sha, exp_bytes) in BASE.items():
    p = os.path.join(ROOT, rel)
    with open(p, "rb") as f:
        b = f.read()
    got_sha = hashlib.sha256(b).hexdigest()
    got_bytes = len(b)
    ok = (got_sha == exp_sha and got_bytes == exp_bytes)
    allok = allok and ok
    print("%s  MATCH=%s  sha256=%s  bytes=%d" % (rel, ok, got_sha, got_bytes))
    print("被核对象 SHA256 = %s，字节数 = %d" % (got_sha, got_bytes))
print("ALL_MATCH = %s COUNT = %d" % (allok, len(BASE)))
