# -*- coding: utf-8 -*-
# _verify_hy4.py · 矩阵复核员 hy4 · 独立复核（不复用 _m_rebuild.py 的任何实现）
# 只读既有件；唯一写域 lead/matrix_binding_20261108/ 且本脚本前缀 _verify_。
# 运行: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/matrix_binding_20261108/_verify_hy4.py
import hashlib
import json
import re

R = "D:/Project/ra2-campaign-forge/"

MOTHER = R + "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"
CAND = R + "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"
DESIGN = R + "lead/b2b_design_20261106/B2B_DESIGN.md"
MATRIX = R + "lead/b2b_design_20261106/STATE_MATRIX.json"
CDIFF = R + "lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff"
JIA = R + "lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md"
PREAUDIT = R + "lead/b2b_preaudit_20261106/B2B_PREAUDIT.md"
R3 = R + "lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md"
SPEC = R + "lead/bexec_n4_20261108/B_EXECUTION_SPEC.md"
NEXT = R + "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md"

# 编排方派发指纹（7 件），逐项比对
DISPATCH = {
    JIA:      ("deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f", 11638),
    DESIGN:   ("565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735),
    MATRIX:   ("1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558),
    PREAUDIT: ("3f97f3a4664981961b72a91a60053fe8c867fa9d8e25442e7159c3046ccbf69f", 20615),
    R3:       ("96071dd9d58e30a54966a2a1e16f4af918c2f8dd5825363510e8ced8bc6a8fea", 24661),
    SPEC:     ("be73333541ddef9a9782aff2ae2f98e657d50d254c50dad5acdf8052ebc25358", 32183),
    NEXT:     ("c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c", 27225),
}

def fp(path):
    d = open(path, "rb").read()
    return hashlib.sha256(d).hexdigest(), len(d), d

print("=== A. 编排方 7 件指纹逐项独立实算 ===")
all_ok = True
for p, (eh, en) in DISPATCH.items():
    h, n, _ = fp(p)
    ok = (h == eh and n == en)
    all_ok &= ok
    print("%s  sha=%s bytes=%d  命中=%s" % (p.split("/")[-1], h, n, ok))
print("DISPATCH_7_ALL_MATCH = %s" % all_ok)

print("\n=== B. 其余 5 件指纹独立实算 ===")
for name, p in [("母本", MOTHER), ("候选", CAND), ("CANDIDATE_LF.diff", CDIFF),
                ("甲B2_FIX_DESIGN", JIA), ("乙B2B_DESIGN", DESIGN)]:
    h, n, _ = fp(p)
    print("%-20s sha=%s bytes=%d" % (name, h, n))

# ---- 独立 unified diff 解析（自己实现，不同于 _m_rebuild.py 的游标计数法）----
HDR = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

def parse_diff_text(text):
    """返回 [(old_start, old_count, old_lines, new_lines)]；以老/新计数双界停止。"""
    lines = text.split("\n")
    out = []
    k = 0
    while k < len(lines):
        m = HDR.match(lines[k])
        if not m:
            k += 1
            continue
        os = int(m.group(1)); oc = int(m.group(2)) if m.group(2) is not None else 1
        nc = int(m.group(4)) if m.group(4) is not None else 1
        k += 1
        body = []
        seen_o = seen_n = 0
        while k < len(lines) and (seen_o < oc or seen_n < nc):
            row = lines[k]
            if row.startswith("\\"):
                k += 1
                continue
            if row == "":
                tag = " "
            else:
                tag = row[0]
            if tag == " ":
                seen_o += 1; seen_n += 1
            elif tag == "-":
                seen_o += 1
            elif tag == "+":
                seen_n += 1
            else:
                break
            body.append(row)
            k += 1
        old_lines = [x[1:] if x else "" for x in body if (x == "" or x[0] in " -")]
        new_lines = [x[1:] if x else "" for x in body if (x == "" or x[0] in " +")]
        out.append((os, oc, old_lines, new_lines, seen_o, seen_n))
    return out

def rebuild(mother_lines, hunks, label):
    """按 1-based 老锚点拼接；断言 -/上下文行与母本逐行相等。"""
    res = []
    cur = 1  # 1-based 下一个未消费母本行
    for (os, oc, old_lines, new_lines, so, sn) in hunks:
        assert so == oc and sn == len(new_lines), "%s hunk 计数不符 so=%d oc=%d sn=%d" % (label, so, oc, sn)
        if os < cur:
            raise AssertionError("%s 锚点回退 os=%d cur=%d" % (label, os, cur))
        res.extend(mother_lines[cur - 1: os - 1])  # 未改动区间
        seg = mother_lines[os - 1: os - 1 + len(old_lines)]
        if seg != old_lines:
            raise AssertionError("%s 上下文/-行不匹配 @%d" % (label, os))
        res.extend(new_lines)
        cur = os + len(old_lines)
    res.extend(mother_lines[cur - 1:])
    return res

mother_h, mother_n, mother_b = fp(MOTHER)
cand_h, cand_n, cand_b = fp(CAND)
assert b"\r" not in mother_b and b"\r" not in cand_b, "CR 出现"
mother_lines = mother_b.decode("utf-8").split("\n")
cand_lines = cand_b.decode("utf-8").split("\n")
print("\n=== C. 字节前提 === 母本CR=%d 候选CR=%d 母本行(split)=%d 候选行(split)=%d" % (
    mother_b.count(b"\r"), cand_b.count(b"\r"), len(mother_lines), len(cand_lines)))

# 路径①：B2B_DESIGN.md 中 ```diff 代码块
dtext = open(DESIGN, "rb").read().decode("utf-8")
blocks = []
buf = None
for row in dtext.split("\n"):
    if buf is None and row.strip() == "```diff":
        buf = []
    elif buf is not None and row.strip() == "```":
        blocks.append("\n".join(buf)); buf = None
    elif buf is not None:
        buf.append(row)
print("\n=== D. 路径① 设计 ```diff 块 = %d（预期 9）===" % len(blocks))
h1 = []
for i, b in enumerate(blocks, 1):
    hs = parse_diff_text(b)
    assert len(hs) == 1, "设计块#%d hunk 数=%d（预期1）" % (i, len(hs))
    h1.append(hs[0])
rb1 = rebuild(mother_lines, h1, "设计§4")
rb1_b = "\n".join(rb1).encode("utf-8")
eq1 = rb1_b == cand_b
print("路径① 重建 sha=%s bytes=%d ==候选逐字节:%s" % (hashlib.sha256(rb1_b).hexdigest(), len(rb1_b), eq1))

# 路径②：CANDIDATE_LF.diff
ctext = open(CDIFF, "rb").read().decode("utf-8")
h2 = parse_diff_text(ctext)
print("\n=== E. 路径② CANDIDATE_LF.diff hunk 数 = %d（预期 9）===" % len(h2))
rb2 = rebuild(mother_lines, h2, "CANDIDATE_LF.diff")
rb2_b = "\n".join(rb2).encode("utf-8")
eq2 = rb2_b == cand_b
print("路径② 重建 sha=%s bytes=%d ==候选逐字节:%s" % (hashlib.sha256(rb2_b).hexdigest(), len(rb2_b), eq2))

# 乙值域独立统计
rows = json.load(open(MATRIX, "r", encoding="utf-8"))
confs = sorted(set(r["confidence"] for r in rows))
verds = sorted(set(r["verdict"] for r in rows))
print("\n=== F. STATE_MATRIX.json 独立统计 === 行数=%d confidence=%s verdict(%d)=%s" % (
    len(rows), confs, len(verds), verds))

# 甲判定矩阵 confidence/verdict 字面量（从 :127-165 区间抽取）
jia_lines = open(JIA, "r", encoding="utf-8").read().split("\n")
seg = "\n".join(jia_lines[126:165])
jia_conf = sorted(set(re.findall(r'"(n/a|high|medium|low|none)"', seg)))
jia_verd = sorted(set(re.findall(r'\("(absent_both|vanished|new_first_appearance|new_write|rewritten_same_content|leftover_unchanged)"', seg)))
print("=== G. 甲 :127-165 实码字面量 === confidence=%s verdict(%d)=%s" % (jia_conf, len(jia_verd), jia_verd))

print("\n=== FINAL === REBUILD_BOTH_PASS=%s DISPATCH_ALL=%s BLOCKS9=%s HUNKS9=%s ROWS14=%s" % (
    eq1 and eq2, all_ok, len(blocks) == 9, len(h2) == 9, len(rows) == 14))
