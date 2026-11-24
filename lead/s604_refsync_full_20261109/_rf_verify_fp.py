# -*- coding: utf-8 -*-
"""_rf_verify_fp.py — 只读 hashlib 指纹复核（全量清单补齐员，本会话实跑）
用法: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/s604_refsync_full_20261109/_rf_verify_fp.py
零真机 / 零采样代码：本脚本仅 open(...,'rb') + hashlib.sha256，无任何进程/内存/注入操作。
"""
import hashlib
import os

ROOT = "D:/Project/ra2-campaign-forge/"

# 编排方实跑指纹基线（任务书所给 6 件），逐件核对
BASELINE = [
    ("lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md",
     "1e4ceb37187cd12601ad03cdc02f0cf2ee624d1f6870c03c0e35d84cbcb40cfc", 36097),
    ("lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md",
     "058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec", 18980),
    ("lead/s604_refsync_20261109/S604_REFSYNC_DRAFT.md",
     "cbadcb872c696c7a39af50764ecc0b276d42e9a89afd73caead0a8d703338841", 38819),
    ("lead/s604_refsync_20261109/_rs_REFSYNC_DRAFT.md",
     "7477a869f1d8436b7641b3b5ba09dac778ed078228adbabc0469d5665419d572", 33869),
    ("lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]

# §4.2 的 13 件（43 处所在件）
TARGETS = [
    "lead/slowframe_r3_20261108/S604_GAP_RECHECK.md",
    "lead/s604_attribution_20261108/S604_ATTRIBUTION.md",
    "lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md",
    "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
    "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",
    "lead/ledger_appendix_20261108/_lad_tpl.md",
    "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",
    "lead/s604_script_gap_20261109/_sg_FINDINGS.md",
    "lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md",
    "lead/s604_exclusive_20261109/_ex_EXCLUSIVITY.md",
    "lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
    "lead/direction_ruling_20261108/RULING_DIRECTION.md",
    "lead/direction_ruling_20261108/_dr_RULING.md",
]


def fp(rel):
    p = os.path.join(ROOT, rel)
    with open(p, "rb") as f:
        b = f.read()
    return hashlib.sha256(b).hexdigest(), len(b)


print("== A 段：编排方基线 6 件逐件核对 ==")
ok = 0
for rel, sha, size in BASELINE:
    got_sha, got_size = fp(rel)
    match = (got_sha == sha and got_size == size)
    ok += 1 if match else 0
    print("%s|%s|%d|%s" % (rel, got_sha, got_size, "MATCH" if match else "MISMATCH"))
print("A 段结论: %d/%d MATCH" % (ok, len(BASELINE)))

print("")
print("== B 段：被核对象绑定行（§4.2 43 处清单载体） ==")
sha, size = fp(BASELINE[0][0])
print("被核对象 SHA256 = %s，字节数 = %d" % (sha, size))

print("")
print("== C 段：§4.2 的 13 件当前指纹（hashlib 实算） ==")
for rel in TARGETS:
    s, n = fp(rel)
    print("%s|%s|%d" % (rel, s, n))

print("")
print("== D 段：同文对逐字比对（只读） ==")


def line(rel, n):
    p = os.path.join(ROOT, rel)
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()[n - 1]


pairs = [
    ("LEDGER:215 ≡ _lad_tpl:151",
     ("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 215),
     ("lead/ledger_appendix_20261108/_lad_tpl.md", 151)),
    ("LEDGER:123 ≡ _la_draft3:25",
     ("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 123),
     ("lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 25)),
    ("ATTRIBUTION:136 ≡ _sa:90",
     ("lead/s604_attribution_20261108/S604_ATTRIBUTION.md", 136),
     ("lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md", 90)),
]
for name, a, b in pairs:
    la, lb = line(*a), line(*b)
    print("%s : %s" % (name, "IDENTICAL" if la == lb else "DIFFERENT"))
    print("  A[%s:%d] %r" % (a[0], a[1], la))
    print("  B[%s:%d] %r" % (b[0], b[1], lb))
