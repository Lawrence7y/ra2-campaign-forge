# -*- coding: utf-8 -*-
r"""_v12w_fpcheck.py -- 分界撰写员本轮独立实跑：9 件上游指纹 + 两域 9 处命中回算 + 两条绑定行。
零真机、零采样；只用 hashlib / re / Path.read_bytes；绝对路径；不写只读域。
"""
import sys
sys.dont_write_bytecode = True
import hashlib
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")

BASELINE = [
    ("lead/c07_slot_20261109/C07_IDENTITY_SLOT.md", "05ecdfca451476bb80d84281068fcd9c59d1364b2247cb5482943de6417781fc", 20651),
    ("lead/c07_truth_protocol_20260909/C07_TRUTH_PROTOCOL.md", "MISSING", 0),
    ("lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md", "5102beae1ecf4952862d4ff1319283df816c53a49bdc81bae38d9709bef974e3", 38232),
    ("lead/c07_truth_protocol_20261109/_tp_C07_TRUTH_PROTOCOL.md", "68395681bbfd6b348a91664ec8c0dfafe1b9aa22a939691d0683414071f96547", 25630),
    ("lead/gate_fp7_20261108/_g7_predicates.py", "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    ("lead/gate_r9r12_20261109/_g9_gate.py", "a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6", 11623),
    ("lead/gate_doc_name_fix_20261109/_dn_regate_out.json", "0d129e409ca5ab744891abccd85a0c0ca0c164ddea8620de634de5079fa8f096", 22133),
    ("lead/PENDING_DECISIONS.md", "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md", "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]

print("[FP-9] 本轮独立实算九件上游指纹 (hashlib.sha256) / 绝对路径")
all_match = True
for rel, sha0, n0 in BASELINE:
    p = ROOT / rel
    if not p.exists():
        ok = (sha0 == "MISSING" and n0 == 0)
        print("  %-64s exists=False sha256=MISSING bytes=0 MATCH=%s" % (rel, ok))
        all_match &= ok
        continue
    b = p.read_bytes()
    sha, n = hashlib.sha256(b).hexdigest(), len(b)
    ok = (sha == sha0 and n == n0)
    all_match &= ok
    print("  %-64s exists=True  sha256=%s bytes=%d MATCH=%s" % (rel, sha, n, ok))
print("[FP-9] ALL_BASELINE_MATCH = %s ; count = %d" % (all_match, len(BASELINE)))

DOCS = [
    ("c07_slot_20261109", ROOT / "lead" / "c07_slot_20261109" / "C07_IDENTITY_SLOT.md",
     ["已补登", "已填入", "已填", "已代填"]),
    ("c07_truth_protocol_20261109", ROOT / "lead" / "c07_truth_protocol_20261109" / "C07_TRUTH_SELF_PROOF.md",
     ["已填", "已代填", "已提交"]),
]
print("\n[HITS] 两域逐 token 字面命中回算（行号 = text.count(chr(10),0,pos)+1）")
grand = 0
for name, path, bans in DOCS:
    text = path.read_bytes().decode("utf-8")
    rows = []
    for tok in bans:
        for m in re.finditer(re.escape(tok), text):
            ln = text.count("\n", 0, m.start()) + 1
            ls = text.rfind("\n", 0, m.start()) + 1
            le = text.find("\n", m.end())
            if le == -1:
                le = len(text)
            rows.append((m.start(), ln, tok, text[ls:le]))
    rows.sort()
    print("  --- %s : raw occurrences = %d ---" % (name, len(rows)))
    for pos, ln, tok, orig in rows:
        grand += 1
        print("  pos=%-6d L%-4d tok=%-6s | %s" % (pos, ln, tok, orig))
print("[HITS] 两域合计 = %d" % grand)

print("\n[BINDING] 两条绑定行（被核对象 = 两域主件）")
for rel, sha0, n0 in BASELINE:
    if rel.endswith("C07_IDENTITY_SLOT.md") or rel.endswith("C07_TRUTH_SELF_PROOF.md"):
        p = ROOT / rel
        b = p.read_bytes()
        print("被核对象 SHA256 = %s，字节数 = %d" % (hashlib.sha256(b).hexdigest(), len(b)))
print("[V12W-FPCHECK-END]")
