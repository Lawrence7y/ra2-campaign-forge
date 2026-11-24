# -*- coding: utf-8 -*-
"""F2-d 复核员独立指纹核对（只读）：编排方基线 9 件 + 证据 5 件 + ROOTCAUSE + r1 候选 + 绑定对象。"""
import hashlib, os

BASE = r"D:\Project\ra2-campaign-forge"

def fp(rel):
    p = os.path.join(BASE, rel)
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest(), n

# (relpath, expected_full_hex_or_prefix, expected_bytes, label)
ITEMS = [
    # --- 编排方基线 9 件 ---
    (r"lead\r11_f2_fix_20261109\R11_F2_COVERAGE_FIX.md",
     "99ba9f979018df66f39a996859e24ed207b566b15f6bcdec7055b85a1f379435", 25282, "baseline"),
    (r"lead\r11_f2_fix_20261109\_f2_r11plus.py",
     "83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75", 15723, "baseline"),
    (r"lead\r11_f2_fix_20261109\_f2_repro_out.json",
     "3bc0ed8b26f90e235888ed1c386ee0f3179cdcc54bf9092b6ca167dda2ecfa72", 28386, "baseline"),
    (r"lead\r11_f2_fix_20261109\_f2_compare_out.json",
     "148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1", 44958, "baseline"),
    (r"lead\r11_f2_fix_20261109\_f2_context_probe_out.txt",
     "e48e15469c28508303c4eb2c733e44d0129191107a5700a7beeed36e7cc89580", 44054, "baseline"),
    (r"lead\gate_fp7_20261108\_g7_predicates.py",
     "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743, "baseline"),
    (r"lead\gate_r9r12_20261109\GATE_R9R12_REGRESSION.md",
     "dc222c2409db9a63c1e2cd95b979069a16b5067585bd8a46d7a9d40657fe27c0", 37578, "baseline"),
    (r"lead\PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419, "baseline"),
    (r"lead\GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518, "baseline"),
    # --- 回件证据 5 件（前缀+字节数比对） ---
    (r"lead\a_residual_n1_20261108\A_RESIDUAL_REFERENCES.md", "1209ca4c", 33431, "prefix"),
    (r"lead\b2b_isolated_20261107\INTEGRATION_REPORT.md", "65463431", 24022, "prefix"),
    (r"lead\b2b_isolated_20261107\_integ_INTEGRATION_REPORT.md", "9742f2cc", 15179, "prefix"),
    (r"lead\bexec_n4_20261108\B_EXECUTION_SPEC.md", "be733335", 32183, "prefix"),
    (r"lead\bexec_n4_20261108\_n4_SPEC_N4_B2B_MATRIX.md", "cb4f3011", 22136, "prefix"),
    # --- 被核产出件（回件自称 d12efd85…/21424） ---
    (r"lead\f2d_rootcause_20261109\_f2d_ROOTCAUSE.md",
     "d12efd856c0aebe5dc8a882cb7cbd486154c7bb8602028e83a6f3ef290668b05", 21424, "baseline"),
    # --- r1 磁盘候选（回件称两处同名件均非 r1=3343cfbe…/26435） ---
    (r"lead\a_residual_20261106\A_RESIDUAL_REFERENCES.md", "746b66d4", 28384, "prefix"),
    (r"lead\a_residual_20261106\review\A_RESIDUAL_REVIEW.md", None, None, "record"),
    # --- 10 条绑定行的对象（9/10 在盘且 MATCH 之说） ---
    (r"lead\b2b_isolated_20261107\qc151_trip.isolated.py", "ca23c116", 412759, "prefix"),
    (r"lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py", "ca23c116", 412759, "prefix"),
    (r"out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py", "517889c6", 399508, "prefix"),
    (r"lead\bexec_n4_20261108\_n4_SPEC_N4_B2B_MATRIX.md", "cb4f3011", 22136, "prefix-dup"),
]

print("== _f2dv_fpcheck.py（F2-d 复核员独立实算，hashlib）==")
ok = bad = 0
for rel, exp, expb, kind in ITEMS:
    try:
        d, n = fp(rel)
    except FileNotFoundError:
        print("MISSING\t%s" % rel)
        continue
    if kind == "baseline":
        good = (d == exp and n == expb)
    else:
        good = True if exp is None else (d.startswith(exp) and n == expb)
    tag = "MATCH" if good else "MISMATCH"
    if exp is None:
        print("%s\t%s\t%s\t%d" % ("RECORD", rel, d, n))
    else:
        print("%s\t%s\t%s\t%d\texpected=%s/%s" % (tag, rel, d, n, exp, expb))
        ok += 1 if good else 0
        bad += 0 if good else 1
print("== baseline/prefix 比对小结: MATCH=%d MISMATCH=%d ==" % (ok, bad))
