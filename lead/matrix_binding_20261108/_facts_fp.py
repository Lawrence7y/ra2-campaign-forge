# -*- coding: utf-8 -*-
# _facts_fp.py · 核证报告撰写员 · 2026-11-08
# 目的：为 MATRIX_BINDING_FACTS.md 的落盘做本会话独立实算——
#   1) 编排方 7 件 + 关键证据件 + 5 件主产出 的 SHA256/字节数；
#   2) 5 件主产出按文件名升序拼接的聚合指纹（绑定复核回件 sha256Line）；
#   3) _m_rebuild_out.txt 的行结构（复核回件「行号错位」认定的独立确认）；
#   4) _verify_rerun_m_rebuild.txt 与 _m_rebuild_out.txt 逐字节相等检查；
#   5) 甲 :137 absent_both 字面量在位检查（解释复核 §G verdict(5) 的正则口径）。
# 方法：只读既有件；只打印；零真机、零采样；运行 python -I -X utf8 + 绝对路径。
import hashlib
import os

R = "D:/Project/ra2-campaign-forge/"


def fp(rel):
    b = open(R + rel, "rb").read()
    return hashlib.sha256(b).hexdigest(), len(b)


print("== A. 编排方派发 7 件（对照本 ask 派发指纹）==")
DISPATCH = {
    "lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md":
        ("deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f", 11638),
    "lead/b2b_design_20261106/B2B_DESIGN.md":
        ("565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735),
    "lead/b2b_design_20261106/STATE_MATRIX.json":
        ("1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558),
    "lead/b2b_preaudit_20261106/B2B_PREAUDIT.md":
        ("3f97f3a4664981961b72a91a60053fe8c867fa9d8e25442e7159c3046ccbf69f", 20615),
    "lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md":
        ("96071dd9d58e30a54966a2a1e16f4af918c2f8dd5825363510e8ced8bc6a8fea", 24661),
    "lead/bexec_n4_20261108/B_EXECUTION_SPEC.md":
        ("be73333541ddef9a9782aff2ae2f98e657d50d254c50dad5acdf8052ebc25358", 32183),
    "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md":
        ("c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c", 27225),
}
all_ok = True
for rel, (eh, en) in DISPATCH.items():
    h, n = fp(rel)
    ok = (h == eh and n == en)
    all_ok = all_ok and ok
    print("%-52s %s %8d 命中=%s" % (os.path.basename(rel), h, n, ok))
print("DISPATCH_7_ALL_MATCH = %s" % all_ok)

print("\n== B. 其余证据件 ==")
for rel in [
    "lead/b2_preaudit_20261106/B2_PREAUDIT.md",
    "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py",
    "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py",
    "lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff",
    "lead/b2b_candidate_20261106/qc151_trip.candidate.py",
]:
    h, n = fp(rel)
    print("%-52s %s %8d" % (os.path.basename(rel), h, n))

print("\n== C. 5 件主产出（写域内）单件指纹 ==")
PROD = ["_m_CHAIN_VERIFY_20261108.md", "_m_DECISION_POINTS_20261108.md",
        "_m_MATRIX_DIFF_20261108.md", "_m_rebuild.py", "_m_rebuild_out.txt"]
DIRR = "lead/matrix_binding_20261108/"
blobs = []
for name in sorted(PROD):
    h, n = fp(DIRR + name)
    blobs.append(open(R + DIRR + name, "rb").read())
    print("%-32s %s %6d" % (name, h, n))
agg = b"".join(blobs)
print("聚合（按文件名升序拼接）: SHA256=%s bytes=%d" % (hashlib.sha256(agg).hexdigest(), len(agg)))

print("\n== D. _m_rebuild_out.txt 行结构（复核回件行号错位认定的独立确认）==")
ob = open(R + DIRR + "_m_rebuild_out.txt", "rb").read()
lines = ob.decode("utf-8").split("\n")
if lines and lines[-1] == "":
    lines = lines[:-1]
print("bytes=%d CR=%d 物理行=%d 非空行=%d" % (len(ob), ob.count(b"\r"), ob.decode('utf-8').count('\n') + (0 if ob.endswith(b'\n') else 1), len(lines)))
for i, ln in enumerate(lines, 1):
    if any(k in ln for k in ("FINAL", "路径① ```diff", "路径① 母本", "路径② CANDIDATE_LF.diff hunk",
                             "路径② 母本", "CR 检查", "行数:", "链④")):
        print("  :%d %s" % (i, ln[:78]))
fp_lines = [i for i, ln in enumerate(lines, 1) if ln.startswith("FP ")]
print("  FP 打头行（派发+母本/候选/diff 指纹）= %s" % fp_lines)
conf_line = [i for i, ln in enumerate(lines, 1) if ln.startswith("乙 confidence")]
verd_line = [i for i, ln in enumerate(lines, 1) if ln.startswith("乙 verdict")]
rows_line = [i for i, ln in enumerate(lines, 1) if ln.startswith("STATE_MATRIX.json 行数")]
print("  confidence 值域行 = %s ; verdict 值域行 = %s ; 矩阵行数行 = %s" % (conf_line, verd_line, rows_line))

print("\n== E. 复核员重跑输出与原件逐字节比对 ==")
a = open(R + DIRR + "_m_rebuild_out.txt", "rb").read()
b = open(R + DIRR + "_verify_rerun_m_rebuild.txt", "rb").read()
h, n = fp(DIRR + "_verify_rerun_m_rebuild.txt")
print("_verify_rerun_m_rebuild.txt: SHA256=%s bytes=%d 与 _m_rebuild_out.txt 逐字节相等=%s" % (h, n, a == b))

print("\n== F. 甲 :137 absent_both 在位检查（解释 _verify_hy4 §G verdict(5) 的正则口径）==")
jia = open(R + "lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md", "rb").read().decode("utf-8").split("\n")
l137 = jia[136]
print("甲:137 = %r" % l137)
print('  "absent_both" in 甲:137 = %s ; "vanished" in 甲:137 = %s' % ('"absent_both"' in l137, '"vanished"' in l137))
