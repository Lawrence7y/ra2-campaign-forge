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

j = json.loads((REPO / "lead" / "gate_r9r12_20261109" / "_g9_regression_out.json").read_text(encoding="utf-8"))
n = 0
for i, r in enumerate(j["results_30"]):
    p = REPO / r["rel"]
    text = p.read_text(encoding="utf-8")
    pp, pw, pb = plus.r11_scan_plus(text, p.parent, root=REPO)
    for k, b in enumerate(pb):
        if b.get("match") is not True:
            continue
        if b.get("tier") == "SAMEDOC_LINK_EQ":
            items = [(m.get("path"), m.get("bytes")) for m in (b.get("members") or [])]
        elif (b.get("alt") or b).get("path"):
            src = b.get("alt") or b
            items = [(src.get("verified_path") or src.get("path"), src.get("bytes"))]
        else:
            items = []
        if not items:
            n += 1
            print("SKIP#%d #%d bind#%d tier=%s 无单一回验路径且无 members（multi：不主张 path）" % (n, i, k + 1, b.get("tier")))
            continue
        for vp, bytes_decl in items:
            vp = Path(vp) if vp else None
            data = vp.read_bytes() if vp else b""
            sha = hashlib.sha256(data).hexdigest()
            size = len(data)
            ok_sha = sha == (b.get("declared") or "").lower()
            ok_bytes = size == bytes_decl
            n += 1
            print("MATCH#%d #%d bind#%d tier=%s alt=%s %s" % (n, i, k + 1, b.get("tier"), bool(b.get("alt")), vp))
            print("   declared=%s" % (b.get("declared") or ""))
            print("   mine   =%s sha_ok=%s" % (sha, ok_sha))
            print("   bytes declared=%s mine=%d bytes_ok=%s" % (bytes_decl, size, ok_bytes))
            if not (ok_sha and ok_bytes):
                print("   *** MISMATCH ***")
print("checked", n)
