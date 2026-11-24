# -*- coding: utf-8 -*-
"""_gv_fp_check.py — 复核员独立指纹核对（只读）。
① 被核对象 = 形式化回件原文（_gv_subject.json，逐字来自 ask）
② 编排方清单 9 件保护件
③ 作者三件核心工件（predicates/reverse_validate/patch）
"""
import hashlib, pathlib, sys

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead/gate_fp7_20261108"

def sha(p):
    b = pathlib.Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)

EXPECT = {
    "lead/gate_template_20261108/GATE_TEMPLATE_FIXED.py.txt": ("543e79184258f9f96517fdc8d61d42e46a7cd544f11ce0ab3b78d9fd505e9abe", 28128),
    "lead/gate_template_20261108/GATE_FALSE_POSITIVES.md": ("2011cb866e8a6e857c7c3fcd08e7270e0cc062f8eed47610fa025bf15b5f3244", 25841),
    "lead/gate_validate_20261108/GATE_TEMPLATE_REGRESSION.md": ("c9093cab4f708d3f2bfd721095e9d8458818dd9d36019d996fd952b24e1a5a19", 31507),
    "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md": ("1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b", 23129),
    "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md": ("724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e", 45719),
    "lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md": ("c0dfb0d17edab4d0d89c43dc48bce4b84354fd13bd89cae7277aa15e82cf65f2", 54351),
    "lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md": ("6d88fc9241e31e0d6ed7af4988ab712c8e0f4e4caa9d3d92e4f736bf23f46395", 21690),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
WORK = [
    "lead/gate_fp7_20261108/_g7_predicates.py",
    "lead/gate_fp7_20261108/_g7_reverse_validate.py",
    "lead/gate_fp7_20261108/_g7_patch.md",
]

n_ok = n_bad = 0
print("== 被核对象（形式化回件原文 _gv_subject.json）==")
h, n = sha(WD / "_gv_subject.json")
print("SHA256 = %s  bytes = %d" % (h, n))
print()
print("== 编排方清单 9 件保护件（期望零漂移）==")
for rel, (eh, en) in sorted(EXPECT.items()):
    h, n = sha(ROOT / rel)
    ok = (h, n) == (eh, en)
    n_ok += ok; n_bad += (not ok)
    print("%s  %s  %d  expected=%s/%d  %s" % ("MATCH" if ok else "DRIFT!", h, n, eh[:12], en, rel))
print()
print("== 作者三件核心工件（实测值）==")
for rel in WORK:
    h, n = sha(ROOT / rel)
    print("SHA256 = %s  bytes = %d  %s" % (h, n, rel))
print()
print("protect_ok=%d protect_bad=%d" % (n_ok, n_bad))
sys.exit(1 if n_bad else 0)
