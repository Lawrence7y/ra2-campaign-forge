# -*- coding: utf-8 -*-
"""F2V-04: 对增强版判 match=True 的 9 条绑定行，用 hashlib 独立重算其 verified_path，
与该绑定行声明的 hex/字节数直接比对（不经过补丁模块的比较逻辑）。"""
import hashlib
import importlib.util
import json
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
spec = importlib.util.spec_from_file_location("_f2p", REPO / "lead" / "r11_f2_fix_20261109" / "_f2_r11plus.py")
plus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plus)

MSV_BINDINGS = json.loads('[["merged", [{"declared": "553f8577939f2d4350cf8c898b25f4dc201857bebf3bad0a0d3312c3968020d2", "path": null, "match": true, "tier": "SAMEDOC_LINK_EQ", "members": [{"path": "D:\\\\Project\\\\ra2-campaign-forge\\\\lead\\\\merged_safety_20261109\\\\_msv_fixtures\\\\_msv_alpha.dat", "sha": "553f8577939f2d4350cf8c898b25f4dc201857bebf3bad0a0d3312c3968020d2", "bytes": 45}]}]]]')
n = 0
for i, (CASE_NAME, pb) in enumerate(MSV_BINDINGS):
    print("CASE %d %s" % (i, CASE_NAME))
    text = ""
    pp, pw = [], []
    for k, b in enumerate(pb):
        if b.get("match") is not True:
            continue
        src = b.get("alt") or b
        vp = Path(r"D:\Project\ra2-campaign-forge\lead\merged_safety_20261109\_msv_fixtures\_msv_alpha.dat")
        data = vp.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        size = len(data)
        ok_sha = sha == b["declared"].lower()
        ok_bytes = size == src["bytes"]
        n += 1
        print("MATCH#%d #%d bind#%d tier=%s alt=%s %s" % (n, i, k + 1, b.get("tier"), bool(b.get("alt")), vp))
        print("   declared=%s" % b["declared"])
        print("   mine   =%s sha_ok=%s" % (sha, ok_sha))
        print("   bytes declared=%s mine=%d bytes_ok=%s" % (src["bytes"], size, ok_bytes))
        if not (ok_sha and ok_bytes):
            print("   *** MISMATCH ***")
print("checked", n)
