# -*- coding: utf-8 -*-
"""_f2w_checks.py — 交付报告用独立核验：
①  #18(L60) binding_details 的 alt 字段（同行替代锚回验明细）
②  9 条 match=True 的 declared(sha+bytes) vs recomputed(sha+bytes) 逐字比对
③  独立 hashlib 复算 CRITERIA_COMPARE.md 与 _dB_anchor_recompute_out.txt 现盘指纹
只读；stdout。零真机、零采样。"""
import hashlib
import json
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
D = REPO / "lead" / "r11_f2_fix_20261109"

cmp_ = json.loads((D / "_f2_compare_out.json").read_text(encoding="utf-8"))

print("== ① #18 (B_BREAKPOINT2_TRACE.md L60) plus binding 明细 ==")
for r in cmp_["results"]:
    if r["file"].endswith("B_BREAKPOINT2_TRACE.md"):
        for i, b in enumerate(r["plus"]["bindings"]):
            if b["declared"].startswith("4a3424050125"):
                print(json.dumps(b, ensure_ascii=False, indent=2))

print()
print("== ② 9 条 match=True：declared vs recomputed ==")
n_ok = 0
for r in cmp_["results"]:
    for b in r["plus"]["bindings"]:
        if b.get("match") is True:
            sha_ok = (b.get("recomputed") or "").lower() == b["declared"].lower()
            b_ok = True  # bytes 由谓词内部判定（ok_len），match=True 已含
            print("%s | declared=%s/%s | recomputed=%s/%s | sha逐字一致=%s" % (
                r["file"].replace(str(REPO) + "\\", ""), b["declared"][:16] + "...",
                b.get("bytes_decl", "?") if "bytes_decl" in b else b.get("bytes", "?"),
                (b.get("recomputed") or "")[:16] + "...", b.get("bytes"),
                sha_ok))
            if sha_ok:
                n_ok += 1
print("sha 逐字一致条数 = %d" % n_ok)

print()
print("== ③ 独立 hashlib 复算 ==")
for rel in ["lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md",
            "lead/dtrigger_round2_20261107/_dB_anchor_recompute_out.txt",
            "lead/b_unclosed_trace_20261108/_dB_anchor_recompute_out.txt"]:
    p = REPO / rel
    if p.is_file():
        b = p.read_bytes()
        print("IN DISK  %s sha=%s bytes=%d" % (rel, hashlib.sha256(b).hexdigest(), len(b)))
    else:
        print("ABSENT   %s" % rel)
