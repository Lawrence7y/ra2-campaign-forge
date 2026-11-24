# -*- coding: utf-8 -*-
"""_verify_fp.py — 独立实算指纹（hashlib），核对编排方三件、回件报告、
新证据件、data.json/脚本/out.txt 等，并核验 b6f95763794 归属与 26f3fb 摘要命中。
只读。运行: python -I -X utf8 <abs path>/_verify_fp.py
"""
import hashlib, os, sys

ROOT = r"D:\Project\ra2-campaign-forge"
REL = [
    r"lead\r2_unclosed_b_20261108\B_BREAKPOINTS_2_6.md",
    r"lead\r2_final_grade_20261108\R2_FINAL_GRADE.md",
    r"lead\dtrigger_round2_20261107\_verify_B_out.txt",
    r"lead\b_unclosed_trace_20261108\_bt_B崩点2_尾串追溯_20261108.md",
    r"lead\b_unclosed_trace_20261108\_bt_scan_raw.txt",
    r"lead\b_unclosed_trace_20261108\_bt_repo_scan_raw.txt",
    r".zcode\workflow-drafts\B崩点2回件追溯.dwf.ts",
    r".zcode\workflow-drafts\R2维度B崩点补证.dwf.ts",
    r"lead\gate_validate_20261108\_verify_gates\a7c7b5f9.py",
    r".zcode\workflow-runs\dwfrun-a05ccb49-e10b-4004-8ce6-5f5b48d7820e.mjs",
    r".zcode\workflow-runs\dwfrun-a7c7b5f9-25d5-400a-bd45-6f32a262430b.mjs",
    r".zcode\workflow-runs\dwfrun-1c93b364-e57c-405d-a271-66cd59e4b850.mjs",
    r"lead\dtrigger_round2_20261107\_dB_anchor_recompute.py",
    r"lead\dtrigger_round2_20261107\_dB_anchor_recompute_out.txt",
    r"lead\dtrigger_round2_20261107\_dB_anchor_recompute_data.json",
    r"lead\dtrigger_round2_20261107\_verify_B_recompute.py",
    r"lead\dtrigger_round2_20261107\CRITERIA_ROUND2.md",
    r"lead\criteria_r3_verify_20261108\R2_BREAKPOINTS_CLOSURE.md",
    r"lead\dtrigger_compare_20261107\CRITERIA_COMPARE.md",
]
EXPECTED = {
    r"lead\r2_unclosed_b_20261108\B_BREAKPOINTS_2_6.md": ("3aad3bddda087e171d9add1977849b70c01f7ddb5dff23b575186dfb517403ae", 19527),
    r"lead\r2_final_grade_20261108\R2_FINAL_GRADE.md": ("7ce09812f7bd905a95114a2cc2cea56b3dc3dbaef3d8e0d14c58685762ecab24", 30140),
    r"lead\dtrigger_round2_20261107\_verify_B_out.txt": ("4ee6a6b78d80a336c3431a6f71d9f5a77fec93ef65b7a4c642a49b669368c107", 7229),
}
TAIL_A = "26f3fb61829756dfeecf"
TAIL_B = "b6f95763794"

for rel in REL:
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        print(f"MISSING\t{rel}")
        continue
    d = open(p, "rb").read()
    h = hashlib.sha256(d).hexdigest()
    n = len(d)
    tag = ""
    if rel in EXPECTED:
        eh, en = EXPECTED[rel]
        tag = "\tMATCH" if (h == eh and n == en) else f"\tMISMATCH exp={eh}/{en}"
    own = ""
    if h.endswith(TAIL_B):
        own = f"\tENDSWITH_{TAIL_B}"
    if TAIL_A in h:
        own += f"\tCONTAINS_{TAIL_A}"
    if TAIL_B in h and not h.endswith(TAIL_B):
        own += f"\tCONTAINS_{TAIL_B}"
    print(f"{h}\t{n}\t{rel}{tag}{own}")

# check the DOC named in the workflow payload
p = os.path.join(ROOT, r"lead\b_unclosed_trace_20261108\B_BREAKPOINT2_TRACE.md")
print(f"\nB_BREAKPOINT2_TRACE.md exists = {os.path.isfile(p)}")
sys.stdout.flush()
