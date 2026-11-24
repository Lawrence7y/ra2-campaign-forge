# -*- coding: utf-8 -*-
# _m_rebuild.py · 矩阵核证员 GLM · 2026-11-08
# 目的：独立复核 R3:32-34 两条重建路径（链③）与候选/母本指纹（链④）。
# 方法：只读既有件；在本写域内重建，不写任何既有文件；零真机、零采样。
# 运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/matrix_binding_20261108/_m_rebuild.py
import hashlib
import json
import re
import sys

ROOT = r"D:/Project/ra2-campaign-forge"

MOTHER = ROOT + r"/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"
CANDIDATE = ROOT + r"/lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"
DESIGN = ROOT + r"/lead/b2b_design_20261106/B2B_DESIGN.md"
MATRIX_JSON = ROOT + r"/lead/b2b_design_20261106/STATE_MATRIX.json"
CAND_DIFF = ROOT + r"/lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff"

FILES = {
    "甲 B2_FIX_DESIGN.md": ROOT + r"/lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md",
    "乙 B2B_DESIGN.md": DESIGN,
    "STATE_MATRIX.json": MATRIX_JSON,
    "B2B_PREAUDIT.md": ROOT + r"/lead/b2b_preaudit_20261106/B2B_PREAUDIT.md",
    "R3 判定书": ROOT + r"/lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md",
    "B_EXECUTION_SPEC.md": ROOT + r"/lead/bexec_n4_20261108/B_EXECUTION_SPEC.md",
    "NEXT_STEPS_20261106.md": ROOT + r"/lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md",
    "母本 qc151_trip.py": MOTHER,
    "候选 candidate_lf.py": CANDIDATE,
    "CANDIDATE_LF.diff": CAND_DIFF,
}


def sha_bytes(p):
    b = open(p, "rb").read()
    return hashlib.sha256(b).hexdigest(), len(b), b


def decode_lf(b):
    # 母本/候选已核 CR=0；若出现 CR 则如实报错退出，不做静默归一。
    if b"\r" in b:
        print("FATAL: CR 字节出现（预期 LF-only）")
        sys.exit(2)
    return b.decode("utf-8")


HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def parse_unified(text, one_hunk_per_block):
    """解析 unified diff 文本 → [ (old_start, old_lines, new_lines, header) ]。
    空"" 行按空上下文行处理（标准 patch 容错）。"""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    hunks = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("@@ ") and HUNK_RE.match(ln):
            m = HUNK_RE.match(ln)
            old_start = int(m.group(1))
            old_n = int(m.group(2)) if m.group(2) is not None else 1
            body = []
            i += 1
            new_n = int(m.group(4)) if m.group(4) is not None else 1
            o_cnt = n_cnt = 0
            o_cnt = n_cnt = 0
            while i < len(lines) and (o_cnt < old_n or n_cnt < new_n):
                bl = lines[i]
                if bl.startswith("\\"):
                    body.append(bl)
                    i += 1
                    continue
                if bl == "":
                    tag = " "
                else:
                    tag = bl[0]
                if tag == " ":
                    body.append(bl)
                    o_cnt += 1
                    n_cnt += 1
                elif tag == "-":
                    body.append(bl)
                    o_cnt += 1
                elif tag == "+":
                    body.append(bl)
                    n_cnt += 1
                else:
                    print("FATAL: 非 diff 行混入 hunk 体: %r @%d" % (bl[:60], i))
                    sys.exit(2)
                i += 1
            old_lines = [x[1:] if x != "" else "" for x in body if x == "" or x[0] in (" ", "-")]
            new_lines = [x[1:] if x != "" else "" for x in body if x == "" or x[0] in (" ", "+")]
            hunks.append((old_start, old_lines, new_lines, ln))
        else:
            i += 1
    if one_hunk_per_block:
        pass
    return hunks


def apply_hunks(mother_lines, hunks, label):
    out = []
    src = 0  # 0-based 已消费游标
    for idx, (old_start, old_lines, new_lines, header) in enumerate(hunks, 1):
        pos = old_start - 1  # 0-based
        if pos < src:
            print("FATAL [%s] hunk#%d 锚点回退: pos=%d < src=%d" % (label, idx, pos, src))
            sys.exit(2)
        out.extend(mother_lines[src:pos])
        seg = mother_lines[pos : pos + len(old_lines)]
        if seg != old_lines:
            print("FATAL [%s] hunk#%d 上下文/-行与母本不匹配 @母本行%d" % (label, idx, old_start))
            for k in range(min(len(seg), len(old_lines))):
                if seg[k] != old_lines[k]:
                    print("  首个差异 @seg[%d]: 母本=%r  hunk=%r" % (k, seg[k][:70], old_lines[k][:70]))
                    break
            sys.exit(2)
        out.extend(new_lines)
        src = pos + len(old_lines)
    out.extend(mother_lines[src:])
    return out


def main():
    print("== _m_rebuild 独立重建核证 ==")
    # 1) 指纹
    fps = {}
    for name, p in FILES.items():
        h, n, _b = sha_bytes(p)
        fps[name] = (h, n)
        print("FP %-24s SHA256=%s bytes=%d" % (name, h, n))

    # 2) 候选/母本 CR=0 自证
    mother_b = open(MOTHER, "rb").read()
    cand_b = open(CANDIDATE, "rb").read()
    print("CR 检查: 母本 CR=%d  候选 CR=%d" % (mother_b.count(b"\r"), cand_b.count(b"\r")))

    mother_lines = decode_lf(mother_b).split("\n")
    cand_lines = decode_lf(cand_b).split("\n")
    print("行数: 母本=%d 候选=%d" % (len(mother_lines), len(cand_lines)))

    # 3) 路径①：B2B_DESIGN.md 的 ```diff 块（恰 9 块 9 hunk）
    design_text = open(DESIGN, "rb").read().decode("utf-8")
    dlines = design_text.split("\n")
    blocks = []
    inside = False
    cur = []
    for ln in dlines:
        if not inside and ln.strip() == "```diff":
            inside = True
            cur = []
        elif inside and ln.strip() == "```":
            inside = False
            blocks.append("\n".join(cur))
        elif inside:
            cur.append(ln)
    print("路径① ```diff 块数 = %d（预期 9）" % len(blocks))
    hunks1 = []
    for bi, blk in enumerate(blocks, 1):
        hk = parse_unified(blk, True)
        if len(hk) != 1:
            print("FATAL: 设计块#%d hunk 数=%d（预期 1）" % (bi, len(hk)))
            sys.exit(2)
        hunks1.append(hk[0])
    rebuilt1 = apply_hunks(mother_lines, hunks1, "设计§4九块")
    r1_bytes = "\n".join(rebuilt1).encode("utf-8")
    h1 = hashlib.sha256(r1_bytes).hexdigest()
    eq1 = r1_bytes == cand_b
    print("路径① 母本+设计§4九hunk -> SHA256=%s bytes=%d  ==候选:%s" % (h1, len(r1_bytes), eq1))

    # 4) 路径②：CANDIDATE_LF.diff（9 个 @@ 头）
    cd_text = open(CAND_DIFF, "rb").read().decode("utf-8")
    hunks2 = parse_unified(cd_text, False)
    print("路径② CANDIDATE_LF.diff hunk 数 = %d（预期 9）" % len(hunks2))
    rebuilt2 = apply_hunks(mother_lines, hunks2, "CANDIDATE_LF.diff")
    r2_bytes = "\n".join(rebuilt2).encode("utf-8")
    h2 = hashlib.sha256(r2_bytes).hexdigest()
    eq2 = r2_bytes == cand_b
    print("路径② 母本+CANDIDATE_LF.diff -> SHA256=%s bytes=%d  ==候选:%s" % (h2, len(r2_bytes), eq2))

    # 5) 候选/母本既有指纹核对（链④）
    exp_cand = "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2"
    exp_mother = "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636"
    h_cand, n_cand, _ = sha_bytes(CANDIDATE)
    h_mother, n_mother, _ = sha_bytes(MOTHER)
    print("链④ 候选 %s/%d（预期 %s/412759 -> %s）" % (h_cand, n_cand, exp_cand[:8], h_cand == exp_cand and n_cand == 412759))
    print("链④ 母本 %s/%d（预期 %s/399508 -> %s）" % (h_mother, n_mother, exp_mother[:8], h_mother == exp_mother and n_mother == 399508))

    # 6) STATE_MATRIX.json 行数
    with open(MATRIX_JSON, "r", encoding="utf-8") as fh:
        rows = json.load(fh)
    print("STATE_MATRIX.json 行数 = %d（预期 14）" % len(rows))
    confs = sorted(set(r["confidence"] for r in rows))
    verd = sorted(set(r["verdict"] for r in rows))
    print("乙 confidence 值域 = %s" % confs)
    print("乙 verdict 值域(%d) = %s" % (len(verd), verd))

    verdict = "ALL_REBUILD_PASS" if (eq1 and eq2 and len(blocks) == 9 and len(hunks2) == 9 and len(rows) == 14) else "MISMATCH"
    print("FINAL: %s" % verdict)


if __name__ == "__main__":
    main()
