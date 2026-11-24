# -*- coding: utf-8 -*-
# 独立复核：11 件编排方基线指纹 hashlib 实算，绝不使用被核方脚本
import hashlib, os, json, sys

ROOT = r"D:\Project\ra2-campaign-forge"
BASE = {
 "lead/s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md": ("d9b9c5acd0077060fe7ab0a064c263aa609881bfdc1736407d66d5eec890e1f3", 55331, 338),
 "lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md": ("8ccf9866ebd7860f03d71e939960e018fd0cfbbe6b94add04dd50f7004c11ac5", 61819, 366),
 "lead/s604_attribution_20261108/S604_ATTRIBUTION.md": ("8e9a606752ce2fd4c3d279ba5bb4a54eba99bc83f8974921f3f5601aa1008237", 27182, 196),
 "lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md": ("7241026122978426838d6c8ccaa8ea3335fe6213adef6bae10ab9c7aa83df2f2", 17272, 129),
 "lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md": ("823476680c4c7aab7ead279a3f47724dbd1b2fed977087ae86c35a4eef36258c", 30536, 267),
 "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md": ("d5dc8f979503a65573bcf542fdd28dbf43f13e54dcf0d98229106db43b2f24a6", 7703, 41),
 "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md": ("724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e", 45719, 237),
 "lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md": ("058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec", 18980, 83),
 "lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md": ("1e4ceb37187cd12601ad03cdc02f0cf2ee624d1f6870c03c0e35d84cbcb40cfc", 36097, 171),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518, 9758),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419, 382),
}
print("ROOT =", ROOT)
print("== A. 11 件 SHA256 / 字节数 / 行数（本会话独立 hashlib 实算） ==")
allsha = True
allb = True
for rel, (sha0, b0, lines0) in BASE.items():
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    with open(p, "rb") as f:
        b = f.read()
    sha = hashlib.sha256(b).hexdigest()
    n = len(b)
    nl = b.count(b"\n")
    sl = len(b.decode("utf-8", "replace").splitlines())
    ends = b.endswith(b"\n")
    oksha = (sha == sha0)
    okb = (n == b0)
    allsha &= oksha
    allb &= okb
    print(f"{rel}\n  sha256 = {sha}\n  MATCH_SHA = {oksha} (expected {sha0})\n  bytes = {n} MATCH_BYTES = {okb} (expected {b0})\n  newline_count = {nl}  splitlines = {sl}  ends_with_newline = {ends}  orchestrator_lines = {lines0}  lines_diff = {lines0 - nl}")
print(f"ALL_SHA_MATCH = {allsha}   ALL_BYTES_MATCH = {allb}")
print("== B. 被核对象绑定行复算 ==")
p = os.path.join(ROOT, "lead", "s604_refsync_full_20261109", "S604_REFSYNC_FULL.md")
b = open(p, "rb").read()
print("被核对象 SHA256 = " + hashlib.sha256(b).hexdigest() + "，字节数 = " + str(len(b)))
print("== C. 额外件（被核回件引用的关键件）指纹 ==")
EXTRA = [
 "lead/minhard_check_20261109/_mh_MINHARD_CHECK.md",
 "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md",
 "lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md",
 "lead/ledger_bound_20261109/_lb2_TEMPLATE.md",
 "lead/ledger_appendix_20261108/_lad_tpl.md",
 "lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
 "lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md",
]
for rel in EXTRA:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    b = open(p, "rb").read()
    print(f"{rel} sha256={hashlib.sha256(b).hexdigest()} bytes={len(b)} newlines={b.count(chr(10).encode())}")
