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

MSV_BINDINGS = json.loads('[["merged", [{"declared": "553f8577939f2d4350cf8c898b25f4dc201857bebf3bad0a0d3312c3968020d2", "path": null, "match": true, "tier": "SAMEDOC_LINK_EQ", "samedoc_link": {"scope": "same-document", "problems": [], "binding_hex": "553f8577939f2d4350cf8c898b25f4dc201857bebf3bad0a0d3312c3968020d2", "bytes_decl": 45, "anchors": [{"key": "d:\\\\project\\\\ra2-campaign-forge\\\\lead\\\\merged_safety_20261109\\\\_msv_fixtures\\\\_msv_alpha.dat", "path": "D:\\\\Project\\\\ra2-campaign-forge\\\\lead\\\\merged_safety_20261109\\\\_msv_fixtures\\\\_msv_alpha.dat", "sha": "553f8577939f2d4350cf8c898b25f4dc201857bebf3bad0a0d3312c3968020d2", "size": 45, "tokens": [{"token": "_msv_fixtures/_msv_alpha.dat", "origin": "backtick", "lines": [5, 6], "used_variant": "_msv_fixtures/_msv_alpha.dat", "tried": ["D:\\\\Project\\\\ra2-campaign-forge\\\\lead\\\\merged_safety_20261109\\\\_msv_fixtures\\\\_msv_alpha.dat"]}]}, {"key": "d:\\\\project\\\\ra2-campaign-forge\\\\lead\\\\merged_safety_20261109\\\\_msv_fixtures\\\\_msv_beta.dat", "path": "D:\\\\Project\\\\ra2-campaign-forge\\\\lead\\\\merged_safety_20261109\\\\_msv_fixtures\\\\_msv_beta.dat", "sha": "553f8577939f2d4350cf8c898b25f4dc201857bebf3bad0a0d3312c3968020d2", "size": 45, "tokens": [{"token": "_msv_fixtures/_msv_beta.dat", "origin": "backtick", "lines": [5, 6], "used_variant": "_msv_fixtures/_msv_beta.dat", "tried": ["D:\\\\Project\\\\ra2-campaign-forge\\\\lead\\\\merged_safety_20261109\\\\_msv_fixtures\\\\_msv_beta.dat"]}]}], "reverify": null, "declared_but_mismatched": [], "stats": {"tokens_distinct": 2, "resolved_files": 2, "unresolved_tokens": 0, "unresolved_samples": []}, "verdict": "merged", "warning": "同文档联查多命中 → 等价类合并（warning 级）：同文档第 6 行存在溯源声明（复制自/复制为/COPY_IDENTICAL=True），全部 2 个同 hash 现盘文件的锚定 token 在该(些)行同现，机器逐字节核实同值 → 合并为同一内容的声明背书副本群；未做单一对象主张（path=None），角色归属留人工判定，禁止由 merged 推导任何授权结论。成员：D:\\\\Project\\\\ra2-campaign-forge\\\\lead\\\\merged_safety_20261109\\\\_msv_fixtures\\\\_msv_alpha.dat；D:\\\\Project\\\\ra2-campaign-forge\\\\lead\\\\merged_safety_20261109\\\\_msv_fixtures\\\\_msv_beta.dat", "eq": {"rule": "J4 same-doc provenance-declared byte-identical copy class", "decl_vocab": "复制自|复制为|COPY_IDENTICAL\\\\s*=\\\\s*True", "decl_lines": [6], "decl_hits": [{"line": 6, "covers": ["d:\\\\project\\\\ra2-campaign-forge\\\\lead\\\\merged_safety_20261109\\\\_msv_fixtures\\\\_msv_alpha.dat", "d:\\\\project\\\\ra2-campaign-forge\\\\lead\\\\merged_safety_20261109\\\\_msv_fixtures\\\\_msv_beta.dat"], "text": "`_msv_fixtures/_msv_beta.dat` 复制自 `_msv_fixtures/_msv_alpha.dat`。"}], "members": [{"path": "D:\\\\Project\\\\ra2-campaign-forge\\\\lead\\\\merged_safety_20261109\\\\_msv_fixtures\\\\_msv_alpha.dat", "sha": "553f8577939f2d4350cf8c898b25f4dc201857bebf3bad0a0d3312c3968020d2", "bytes": 45}, {"path": "D:\\\\Project\\\\ra2-campaign-forge\\\\lead\\\\merged_safety_20261109\\\\_msv_fixtures\\\\_msv_beta.dat", "sha": "553f8577939f2d4350cf8c898b25f4dc201857bebf3bad0a0d3312c3968020d2", "bytes": 45}]}}, "members": [{"path": "D:\\\\Project\\\\ra2-campaign-forge\\\\lead\\\\merged_safety_20261109\\\\_msv_fixtures\\\\_msv_alpha.dat", "sha": "553f8577939f2d4350cf8c898b25f4dc201857bebf3bad0a0d3312c3968020d2", "bytes": 45}, {"path": "D:\\\\Project\\\\ra2-campaign-forge\\\\lead\\\\merged_safety_20261109\\\\_msv_fixtures\\\\_msv_beta.dat", "sha": "553f8577939f2d4350cf8c898b25f4dc201857bebf3bad0a0d3312c3968020d2", "bytes": 45}], "decl_lines": [6]}]]]')
n = 0
for i, (CASE_NAME, pb) in enumerate(MSV_BINDINGS):
    print("CASE %d %s" % (i, CASE_NAME))
    text = ""
    pp, pw = [], []
    for k, b in enumerate(pb):
        if b.get("match") is not True:
            continue
        src = b.get("alt") or b
        vp = Path(src.get("verified_path") or src.get("path"))
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
