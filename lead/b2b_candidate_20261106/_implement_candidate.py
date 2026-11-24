# -*- coding: utf-8 -*-
"""
_implement_candidate.py
Realize the 9 hunks from B2B_DESIGN.md into qc151_trip.candidate.py
Generate CANDIDATE.diff and verify all 9 hunks match.
Strictly zero-touch mother file qc151_trip.py.
"""
import ast
import difflib
import hashlib
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path("D:/Project/ra2-campaign-forge")
MOTHER_PATH = PROJECT_ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"
DESIGN_PATH = PROJECT_ROOT / "lead/b2b_design_20261106/B2B_DESIGN.md"
PREAUDIT_PATH = PROJECT_ROOT / "lead/b2b_preaudit_20261106/B2B_PREAUDIT.md"

CANDIDATE_DIR = PROJECT_ROOT / "lead/b2b_candidate_20261106"
CANDIDATE_PATH = CANDIDATE_DIR / "qc151_trip.candidate.py"
DIFF_PATH = CANDIDATE_DIR / "CANDIDATE.diff"

EXPECTED_MOTHER_SHA256 = "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636"
EXPECTED_MOTHER_BYTES = 399508

EXPECTED_DESIGN_SHA256 = "565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf"
EXPECTED_DESIGN_BYTES = 66735


def compute_file_stats(path: Path):
    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    length = len(data)
    lines = data.splitlines()
    return sha, length, len(lines)


def main():
    print("=" * 80)
    print("B2b 候选副本实现与验证")
    print("=" * 80)

    # 1. 验证上游指纹
    mother_sha, mother_bytes, mother_line_cnt = compute_file_stats(MOTHER_PATH)
    print(f"母本 SHA256: {mother_sha} ({mother_bytes} B, {mother_line_cnt} lines)")
    assert mother_sha == EXPECTED_MOTHER_SHA256, f"母本 SHA256 漂移: {mother_sha}"
    assert mother_bytes == EXPECTED_MOTHER_BYTES, f"母本 字节数漂移: {mother_bytes}"

    design_sha, design_bytes, design_line_cnt = compute_file_stats(DESIGN_PATH)
    print(f"设计 SHA256: {design_sha} ({design_bytes} B, {design_line_cnt} lines)")
    assert design_sha == EXPECTED_DESIGN_SHA256, f"设计 SHA256 漂移: {design_sha}"
    assert design_bytes == EXPECTED_DESIGN_BYTES, f"设计 字节数漂移: {design_bytes}"

    mother_text = MOTHER_PATH.read_text(encoding="utf-8")
    mother_lines = mother_text.splitlines()

    design_text = DESIGN_PATH.read_text(encoding="utf-8")

    # 2. 从设计稿解析 9 个 diff hunk
    diff_blocks = re.findall(r"```diff\s*\n(.*?)```", design_text, re.DOTALL)
    print(f"从设计稿提取到 diff 代码块: {len(diff_blocks)} 个")
    assert len(diff_blocks) == 9, f"预期 9 个 diff 块，实际提取到 {len(diff_blocks)}"

    header_pattern = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
    parsed_hunks = []

    for idx, block in enumerate(diff_blocks):
        block_lines = block.splitlines()
        hdr = block_lines[0]
        m = header_pattern.match(hdr)
        assert m, f"无法解析 hunk #{idx+1} 头部: {hdr}"

        old_start = int(m.group(1))
        old_count = int(m.group(2)) if m.group(2) else 1
        new_start = int(m.group(3))
        new_count = int(m.group(4)) if m.group(4) else 1

        context_lines = []
        minus_lines = []
        plus_lines = []
        expected_minus = []
        applied_plus = []

        for l in block_lines[1:]:
            if l.startswith("+++") or l.startswith("---"):
                continue
            if l.startswith(" "):
                context_lines.append(l[1:])
                expected_minus.append(l[1:])
                applied_plus.append(l[1:])
            elif l.startswith("-"):
                minus_lines.append(l[1:])
                expected_minus.append(l[1:])
            elif l.startswith("+"):
                plus_lines.append(l[1:])
                applied_plus.append(l[1:])
            elif l == "":
                context_lines.append("")
                expected_minus.append("")
                applied_plus.append("")
            else:
                raise ValueError(f"Hunk #{idx+1} 出现未知前缀: {l!r}")

        assert len(expected_minus) == old_count, (
            f"Hunk #{idx+1} - 侧头部声明({old_count}) 与提取行数({len(expected_minus)}) 不符"
        )
        assert len(applied_plus) == new_count, (
            f"Hunk #{idx+1} + 侧头部声明({new_count}) 与提取行数({len(applied_plus)}) 不符"
        )

        parsed_hunks.append({
            "index": idx + 1,
            "header": hdr,
            "old_start": old_start,
            "old_count": old_count,
            "old_end": old_start + old_count - 1,
            "new_start": new_start,
            "new_count": new_count,
            "new_end": new_start + new_count - 1,
            "delta": new_count - old_count,
            "context_count": len(context_lines),
            "minus_count": len(minus_lines),
            "plus_count": len(plus_lines),
            "expected_minus": expected_minus,
            "applied_plus": applied_plus,
            "raw_plus_only": plus_lines,
        })
        print(f"Hunk #{idx+1}: {hdr} (old: {old_count} lines, new: {new_count} lines, delta: {new_count - old_count:+d})")

    # 3. 逐 hunk 比对母本 - 侧区间
    print("\n--- 逐 hunk 比对母本 - 侧内容 ---")
    cumulative_delta = 0
    for h in parsed_hunks:
        idx = h["index"]
        o_start, o_end = h["old_start"], h["old_end"]
        mother_slice = mother_lines[o_start - 1 : o_end]
        assert len(mother_slice) == len(h["expected_minus"]), f"Hunk #{idx} 切片长度不符"
        for line_idx, (act, exp) in enumerate(zip(mother_slice, h["expected_minus"])):
            assert act == exp, f"Hunk #{idx} 行 {o_start + line_idx} 失配: act={act!r} != exp={exp!r}"

        # 检查累积行号偏移
        expected_new_start = o_start + cumulative_delta
        assert expected_new_start == h["new_start"], (
            f"Hunk #{idx} 累积偏移计算出的 + 侧起始行 {expected_new_start} != 声明的 {h['new_start']}"
        )
        cumulative_delta += h["delta"]
        print(f"Hunk #{idx} - 侧匹配完全一致; + 侧起始行声明对齐: L{h['new_start']} (delta={h['delta']:+d}, total delta={cumulative_delta:+d})")

    # 4. 实现候选文件：按内容与区间拼接完整候选
    print("\n--- 生成候选副本 ---")
    candidate_lines = []
    curr_orig_line = 1
    for h in parsed_hunks:
        o_start, o_end = h["old_start"], h["old_end"]
        if o_start > curr_orig_line:
            candidate_lines.extend(mother_lines[curr_orig_line - 1 : o_start - 1])
        candidate_lines.extend(h["applied_plus"])
        curr_orig_line = o_end + 1

    if curr_orig_line <= len(mother_lines):
        candidate_lines.extend(mother_lines[curr_orig_line - 1 :])

    candidate_text = "\n".join(candidate_lines) + "\n"
    CANDIDATE_PATH.write_text(candidate_text, encoding="utf-8")
    print(f"写入候选文件: {CANDIDATE_PATH}")

    # 自核：候选文件统计
    cand_sha, cand_bytes, cand_lines = compute_file_stats(CANDIDATE_PATH)
    print(f"候选 SHA256: {cand_sha}")
    print(f"候选 字节数: {cand_bytes} B (母本 399508 B, 净增 {cand_bytes - 399508} B)")
    print(f"候选 行数: {cand_lines} lines (母本 7291 lines, 净增 {cand_lines - 7291} lines)")
    assert cand_lines == len(mother_lines) + cumulative_delta, "候选行数与预期不符"

    # 自核：每个 hunk 在候选里的 + 侧行内容与设计一致
    print("\n--- 自核：验证候选文件中 9 个 hunk 的 + 侧内容与行号 ---")
    for h in parsed_hunks:
        idx = h["index"]
        n_start = h["new_start"]
        n_count = h["new_count"]
        cand_slice = candidate_lines[n_start - 1 : n_start - 1 + n_count]
        assert len(cand_slice) == len(h["applied_plus"]), f"Hunk #{idx} 候选切片行数不符"
        for line_idx, (act, exp) in enumerate(zip(cand_slice, h["applied_plus"])):
            assert act == exp, f"Hunk #{idx} 候选行 {n_start + line_idx} 失配: act={act!r} != exp={exp!r}"
        print(f"Hunk #{idx} 候选 L{n_start}..L{n_start + n_count - 1} ({n_count} 行) 与设计稿 + 侧逐行逐字完全一致 -> PASS")

    # 5. 语法检查：ast.parse
    print("\n--- ast.parse 语法解析 ---")
    parsed_ast = ast.parse(candidate_text, filename=str(CANDIDATE_PATH))
    func_names = [n.name for n in ast.walk(parsed_ast) if isinstance(n, ast.FunctionDef)]
    print(f"ast.parse: SUCCESS (函数定义总数: {len(func_names)})")
    for fn in ["make_pre_freshness_snapshot", "classify_except_freshness", "copy_post_except_evidence", "finalize_trip", "main"]:
        assert fn in func_names, f"关键函数 {fn} 未在 AST 中找到"
        print(f"  函数 {fn} -> FOUND")

    # 6. 生成 CANDIDATE.diff
    print("\n--- 生成 CANDIDATE.diff ---")
    diff_gen = difflib.unified_diff(
        mother_lines,
        candidate_lines,
        fromfile="qc151_trip.py",
        tofile="qc151_trip.candidate.py",
        lineterm=""
    )
    diff_lines = list(diff_gen)
    diff_text = "\n".join(diff_lines) + "\n"
    DIFF_PATH.write_text(diff_text, encoding="utf-8")
    diff_sha, diff_bytes, diff_line_cnt = compute_file_stats(DIFF_PATH)
    print(f"写入 diff 文件: {DIFF_PATH} ({diff_bytes} B, {diff_line_cnt} lines)")

    # 7. 在 CANDIDATE.diff 里定位 9 个 hunk
    print("\n--- 在 CANDIDATE.diff 中定位 9 个 hunk ---")
    diff_hunk_headers = [l for l in diff_lines if l.startswith("@@ ")]
    print(f"CANDIDATE.diff 中共包含 {len(diff_hunk_headers)} 个 @@ hunk")
    for i, h in enumerate(diff_hunk_headers):
        print(f"  Diff hunk #{i+1}: {h}")

    assert len(diff_hunk_headers) == 9, f"CANDIDATE.diff 中 hunk 数为 {len(diff_hunk_headers)}，预期 9"
    for idx, (dh, ph) in enumerate(zip(diff_hunk_headers, parsed_hunks)):
        expected_header = ph["header"]
        print(f"  Hunk #{idx+1}: 预期 {expected_header} vs 实际 {dh}")
        assert dh == expected_header, f"Hunk #{idx+1} header 不匹配: act={dh} != exp={expected_header}"
    print("9/9 hunk 全部在 CANDIDATE.diff 中精确匹配！")

    # 8. 再次核验母本指纹
    mother_sha_after, mother_bytes_after, _ = compute_file_stats(MOTHER_PATH)
    assert mother_sha_after == EXPECTED_MOTHER_SHA256, "CRITICAL: 母本被修改！"
    assert mother_bytes_after == EXPECTED_MOTHER_BYTES, "CRITICAL: 母本字节数被修改！"
    print("\n母本安全性校验: 100% 确认母本 qc151_trip.py 未发生任何修改 (SHA256 与 字节数均一致) -> PASS")


if __name__ == "__main__":
    main()
