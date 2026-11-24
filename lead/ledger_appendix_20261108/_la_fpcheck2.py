# _la_fpcheck2.py — 入账核对员·GLM 第二轮指纹核对（只读；覆盖四笔上游件自报的关键绑定指纹）
# 运行：python -I -X utf8 D:\Project\ra2-campaign-forge\lead\ledger_appendix_20261108\_la_fpcheck2.py
import hashlib
import os

# (期望 sha256 前 8 位, 期望字节, 绝对路径)
EXPECT = [
    # 第四笔 乙替代甲 §4 绑定表 11 件
    ("517889c6", 399508, r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py"),
    ("ca23c116", 412759, r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py"),
    ("72b10802", 18454, r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\CANDIDATE_LF.diff"),
    ("565771d8", 66735, r"D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\B2B_DESIGN.md"),
    ("1d4ccc93", 3558, r"D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\STATE_MATRIX.json"),
    ("deacab49", 11638, r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\B1_HARNESS_PATCH\B2_FIX_DESIGN.md"),
    ("a108a6e4", 28410, r"D:\Project\ra2-campaign-forge\lead\b2_preaudit_20261106\B2_PREAUDIT.md"),
    ("3f97f3a4", 20615, r"D:\Project\ra2-campaign-forge\lead\b2b_preaudit_20261106\B2B_PREAUDIT.md"),
    ("96071dd9", 24661, r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_review3_20261107\CANDIDATE_SEMANTIC_REVIEW_R3.md"),
    ("be733335", 32183, r"D:\Project\ra2-campaign-forge\lead\bexec_n4_20261108\B_EXECUTION_SPEC.md"),
    ("0ebd68dd", 16514, r"D:\Project\ra2-campaign-forge\lead\direction_ruling_20261108\RULING_DIRECTION.md"),
    # 第二笔 O1-O4 被核对象与写域产物
    ("bb61eedb", 18262, r"D:\Project\ra2-campaign-forge\lead\dtrigger_round2_20261107\_dD_PHYSICAL_S_ALIGNMENT.md"),
    ("c64d9e89", 4594, r"D:\Project\ra2-campaign-forge\lead\d_o1o4_necessity_20261108\_d14_ARITHMETIC_FIX.md"),
    ("95c0434b", 6248, r"D:\Project\ra2-campaign-forge\lead\d_o1o4_necessity_20261108\_d14_recompute.py"),
    ("9270cbb8", 2456, r"D:\Project\ra2-campaign-forge\lead\d_o1o4_necessity_20261108\_d14_recompute_out.txt"),
    # 第三笔 604 复算链
    ("e7c29e06", 23707, r"D:\Project\ra2-campaign-forge\lead\slowwindow_n8_20261108\SLOW_WINDOW_LIMITS.md"),
    ("9e274952", 12659, r"D:\Project\ra2-campaign-forge\lead\slowframe_r3_20261108\_r3_recompute_gapdiff.py"),
    ("f1f55791", 9494, r"D:\Project\ra2-campaign-forge\lead\slowframe_r3_20261108\_r3_recompute_out.txt"),
    ("253afec0", 9811, r"D:\Project\ra2-campaign-forge\lead\slowframe_r3_20261108\_verify_r3_gapdiff.py"),
    ("0062bb41", 6477, r"D:\Project\ra2-campaign-forge\lead\slowframe_r3_20261108\_verify_r3_out.txt"),
    ("98cd612f", 11215, r"D:\Project\ra2-campaign-forge\lead\slowframe_r3_20261108\_r3_GAPDIFF_RECHECK.md"),
    ("5d1b0ecc", 19291, r"D:\Project\ra2-campaign-forge\lead\slowframe_r3_20261108\S604_GAP_RECHECK.md"),
    # 第一笔 勘误件
    ("41479540", 15794, r"D:\Project\ra2-campaign-forge\lead\n9_erratum_20261108\_er_N9_205_P6_B0CD48_ERRATUM.md"),
]

ok = 0
for pre, exp_bytes, path in EXPECT:
    if not os.path.exists(path):
        print("MISSING\texp=%s/%d\t%s" % (pre, exp_bytes, path))
        continue
    data = open(path, "rb").read()
    digest = hashlib.sha256(data).hexdigest()
    m = (digest.startswith(pre) and len(data) == exp_bytes)
    ok += m
    print("%s\texp=%s/%d\tgot=%s/%d\t%s" % ("MATCH" if m else "MISMATCH", pre, exp_bytes, digest[:8], len(data), path))
print("SUMMARY %d/%d MATCH" % (ok, len(EXPECT)))
