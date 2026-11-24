# -*- coding: utf-8 -*-
"""_v12v_fp.py — V1/V2 分界复核员独立指纹实算（① + ⑦ 零改动佐证）。
只读：对编排方指纹清单 9 件逐件 hashlib 实算 sha256/bytes，并与基线对比。
零真机、零采样、零写只读域。python -I -X utf8 + 绝对路径运行。"""
import hashlib
import json
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")

# 编排方给定材料（本 ask 的「编排方指纹」字段），逐字抄录，不采信撰写人结论
BASELINE = {
    "lead/c07_slot_20261109/C07_IDENTITY_SLOT.md": ("05ecdfca451476bb80d84281068fcd9c59d1364b2247cb5482943de6417781fc", 20651),
    "lead/c07_truth_protocol_20260909/C07_TRUTH_PROTOCOL.md": ("MISSING", 0),
    "lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md": ("5102beae1ecf4952862d4ff1319283df816c53a49bdc81bae38d9709bef974e3", 38232),
    "lead/c07_truth_protocol_20261109/_tp_C07_TRUTH_PROTOCOL.md": ("68395681bbfd6b348a91664ec8c0dfafe1b9aa22a939691d0683414071f96547", 25630),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/gate_r9r12_20261109/_g9_gate.py": ("a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6", 11623),
    "lead/gate_doc_name_fix_20261109/_dn_regate_out.json": ("0d129e409ca5ab744891abccd85a0c0ca0c164ddea8620de634de5079fa8f096", 22133),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

print("[FP-9] 独立实算九件指纹（hashlib.sha256(read_bytes())）")
all_ok = True
rows = []
for rel, (exp_sha, exp_bytes) in BASELINE.items():
    p = ROOT / rel
    if not p.is_file():
        got_sha, got_bytes, exists = "MISSING", 0, False
    else:
        b = p.read_bytes()
        got_sha, got_bytes, exists = hashlib.sha256(b).hexdigest(), len(b), True
    match = (got_sha == exp_sha and got_bytes == exp_bytes)
    if not match:
        all_ok = False
    rows.append({"file": rel, "exists": exists, "sha256": got_sha, "bytes": got_bytes,
                 "expected": exp_sha, "expected_bytes": exp_bytes, "MATCH": match})
    print("  %-72s exists=%-5s sha256=%s bytes=%d MATCH=%s"
          % (rel, exists, got_sha, got_bytes, match))
    if not match:
        print("      EXPECTED sha256=%s bytes=%d" % (exp_sha, exp_bytes))
print("[FP-9] ALL_BASELINE_MATCH =", all_ok, " ; count =", len(rows))

# 写域自身清单（只读视角，供越界检查用）
wd = ROOT / "lead" / "gate_v1v2_20261109"
print("[WRITE-DOMAIN] path =", wd)
for p in sorted(wd.iterdir()):
    if p.is_file():
        b = p.read_bytes()
        print("  file %-40s bytes=%d sha256=%s" % (p.name, len(b), hashlib.sha256(b).hexdigest()))
print("[FP-9-END]")
