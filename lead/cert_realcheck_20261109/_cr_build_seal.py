# -*- coding: utf-8 -*-
"""_cr_build_seal.py -- phase 1 of a PRE-REGISTERED seal for the real verifier.

Reads ONLY read-only deliverable files (never modifies them), computes their
hashlib.sha256 + byte counts, and writes a single seal JSON into this task's
write domain.  Phase 2 (_cr_real_verify.py) hard-codes the resulting seal hash
as a constant and re-reads/re-hashes everything at verification time.

Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_cr_build_seal.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "cert_realcheck_20261109"

# Verbatim quotes were read from these exact lines of the on-disk deliverables.
# (See _cr_real_verify.py's REAL_CERTS and the run log.)
ITEMS = [
    {
        "item": ["lead/matrix_ab_ruling_20261109/", "需谁批准"],
        "anchor": "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md:108",
        "quote": "批准人一律 = **乙设计责任人**",
        "evidence_lines": [108, 108],
        "roles": {"批准人角色头": "批准人", "赋值算子": "一律 =",
                  "具体施事值": "乙设计责任人"},
        "oracle": {"truth": True, "author": "independent_blind_adjudicator",
                   "predicate_author": "author_of_V1"},
    },
    {
        "item": ["lead/matrix_reach_20261109/", "实跑输出"],
        "anchor": "lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md:69",
        "quote": "verdict='post_read_error' conf='none' is_new=None pre_state='unknown'",
        "evidence_lines": [65, 72],
        "roles": {"实跑事件": "16/16 格实跑",
                  "输出载荷(带具体值的 key=value 数据行)":
                      "verdict='post_read_error' conf='none'"},
        "oracle": {"truth": True, "author": "independent_blind_adjudicator",
                   "predicate_author": "author_of_V1"},
    },
    {
        "item": ["lead/n11_wording_fix_20261108/", "改前改后"],
        "anchor": "lead/n11_wording_fix_20261108/N11_WORDING_FIX.md:81",
        "quote": "【改前】本件按 **13 项分写**，与裁决列名一一对应",
        "evidence_lines": [81, 83],
        "roles": {"改前标签+实值": "【改前】本件按 **13 项分写**",
                  "改后标签+实值": "【改后】本件按 **13 项分写**",
                  "对照算子": "逐项对应"},
        "oracle": {"truth": True, "author": "independent_blind_adjudicator",
                   "predicate_author": "author_of_V1"},
    },
    {
        "item": ["lead/s604_script_gap_20261109/", "脚本存在性"],
        "anchor": "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md:71",
        "quote": "§604 生成脚本【不存在且从未落盘】",
        "evidence_lines": [40, 72],
        "roles": {"脚本对象": "§604 生成脚本",
                  "存在性谓词": "不存在且从未落盘",
                  "判定算子": "逐路结论",
                  "已决断极性": "【不存在且从未落盘】"},
        "oracle": {"truth": True, "author": "independent_blind_adjudicator",
                   "predicate_author": "author_of_V1"},
    },
    {
        "item": ["lead/s604_script_gap_20261109/", "可重建"],
        "anchor": "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md:87",
        "quote": "**判定：正确算法【可唯一重建】。**",
        "evidence_lines": [87, 87],
        "roles": {"重建动作": "可唯一重建",
                  "肯定情态": "判定：正确算法",
                  "确定性证据": "四重独立实现逐位一致"},
        "oracle": {"truth": True, "author": "independent_blind_adjudicator",
                   "predicate_author": "author_of_V1"},
    },
]


def main():
    WDIR.mkdir(parents=True, exist_ok=True)
    seal = {"seal_version": "cr-1", "items": []}
    print("=== PHASE 1: computing pre-registered artifact hashes (real disk reads) ===")
    for it in ITEMS:
        rel = it["anchor"].rsplit(":", 1)[0]
        p = ROOT / rel
        b = p.read_bytes()                      # <-- REAL disk read
        h = hashlib.sha256(b).hexdigest()       # <-- REAL hash recomputation
        rec = dict(it)
        rec["file_sha256"] = h
        rec["bytes"] = len(b)
        all_lines = b.decode("utf-8").splitlines()
        rec["n_lines"] = len(all_lines)
        # exact certified-span hash: detects same-byte-count edits anywhere
        # inside the evidence window, even outside the quoted substring.
        lo, hi = rec["evidence_lines"]
        span = "\n".join(all_lines[lo - 1:hi]) + "\n"
        rec["evidence_span_sha256"] = hashlib.sha256(
            span.encode("utf-8")).hexdigest()
        seal["items"].append(rec)
        print("  %s  sha256=%s  bytes=%d  lines=%d  span_sha256=%s"
              % (rel, h, len(b), rec["n_lines"],
                 rec["evidence_span_sha256"]))
    blob = json.dumps(seal, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    out = WDIR / "_cr_seal.json"
    out.write_bytes(blob.encode("utf-8"))
    print("=== SEAL WRITTEN (write domain only) ===")
    print("  path   =", out)
    print("  bytes  =", len(blob.encode("utf-8")))
    print("  sha256 =", hashlib.sha256(blob.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()
