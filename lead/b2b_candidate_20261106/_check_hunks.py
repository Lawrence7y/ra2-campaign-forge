# -*- coding: utf-8 -*-
"""
_check_hunks.py
Comprehensive self-audit of candidate implementation:
- Verifies mother file integrity
- Verifies candidate file stats and ast.parse
- Verifies each of the 9 hunks in design, candidate, and diff
"""
import ast
import hashlib
from pathlib import Path

PROJECT_ROOT = Path("D:/Project/ra2-campaign-forge")
MOTHER_PATH = PROJECT_ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"
DESIGN_PATH = PROJECT_ROOT / "lead/b2b_design_20261106/B2B_DESIGN.md"
CANDIDATE_PATH = PROJECT_ROOT / "lead/b2b_candidate_20261106/qc151_trip.candidate.py"
DIFF_PATH = PROJECT_ROOT / "lead/b2b_candidate_20261106/CANDIDATE.diff"

EXPECTED_MOTHER_SHA256 = "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636"
EXPECTED_MOTHER_BYTES = 399508


def main():
    print("=" * 80)
    print("候选实现自核报告")
    print("=" * 80)

    # 1. 母本只读验证
    m_data = MOTHER_PATH.read_bytes()
    m_sha = hashlib.sha256(m_data).hexdigest()
    m_bytes = len(m_data)
    m_lines = len(m_data.splitlines())
    print(f"[1] 母本指纹验证:")
    print(f"    路径: {MOTHER_PATH}")
    print(f"    SHA256: {m_sha}")
    print(f"    字节数: {m_bytes}")
    print(f"    行数: {m_lines}")
    assert m_sha == EXPECTED_MOTHER_SHA256, "母本 SHA256 发生改变！"
    assert m_bytes == EXPECTED_MOTHER_BYTES, "母本字节数发生改变！"
    print("    母本只读验证: 100% PASS (零漂移，未修改任何字节)")

    # 2. 候选副本文件验证
    c_data = CANDIDATE_PATH.read_bytes()
    c_sha = hashlib.sha256(c_data).hexdigest()
    c_bytes = len(c_data)
    c_lines = len(c_data.splitlines())
    print(f"\n[2] 候选副本文件统计:")
    print(f"    路径: {CANDIDATE_PATH}")
    print(f"    SHA256: {c_sha}")
    print(f"    字节数: {c_bytes} B (较母本净增 +{c_bytes - m_bytes} B)")
    print(f"    行数: {c_lines} lines (较母本净增 +{c_lines - m_lines} lines)")
    assert c_bytes > m_bytes, "候选副本字节数必须大于母本！"
    assert c_lines == 7533, f"候选副本行数预期 7533，实际 {c_lines}"

    # 3. ast.parse 语法核验
    print(f"\n[3] ast.parse 语法核验:")
    c_text = c_data.decode("utf-8")
    tree = ast.parse(c_text, filename=str(CANDIDATE_PATH))
    func_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    print(f"    AST 解析状态: SUCCESS (0 errors)")
    print(f"    函数定义总数: {len(func_names)}")
    required_funcs = [
        "make_pre_freshness_snapshot",
        "classify_except_freshness",
        "copy_post_except_evidence",
        "finalize_trip",
        "main",
    ]
    for rf in required_funcs:
        assert rf in func_names, f"关键函数缺失: {rf}"
        print(f"    - {rf}: PASS")

    # 4. CANDIDATE.diff 验证与 9 个 hunk 定位
    print(f"\n[4] CANDIDATE.diff 验证与 9 个 hunk 定位:")
    diff_data = DIFF_PATH.read_bytes()
    diff_sha = hashlib.sha256(diff_data).hexdigest()
    diff_bytes = len(diff_data)
    diff_lines = diff_data.decode("utf-8").splitlines()
    print(f"    路径: {DIFF_PATH}")
    print(f"    SHA256: {diff_sha}")
    print(f"    字节数: {diff_bytes} B")
    print(f"    行数: {len(diff_lines)} lines")

    expected_hunks = [
        ("H1", "@@ -212,6 +212,21 @@", 212, 21, "模块顶层注入 5 个 F 命名空间常量"),
        ("H2", "@@ -4458,6 +4473,10 @@", 4473, 10, "backup_carrier 记 RESTORE.backup_mtime_pre，保持 bak[name] 三键"),
        ("H3", "@@ -4558,8 +4577,131 @@", 4577, 131, "前置定义快照构造 + 新鲜性判定函数；签名加 pre_snapshot=None"),
        ("H4", "@@ -4572,20 +4714,105 @@", 4714, 105, "copy_post_except_evidence 三出口全量落盘 7 个 FRESHNESS + 12 键 info"),
        ("H5", "@@ -5906,7 +6133,8 @@", 6133, 8, "finalize_trip 末尾追加 pre_freshness_snapshot: dict | None = None"),
        ("H6", "@@ -5936,7 +6164,8 @@", 6164, 8, ":5939 调用点显式传参 pre_freshness_snapshot"),
        ("H7", "@@ -6294,6 +6523,9 @@", 6523, 9, "main 内 try 之前预初始化 _pre_freshness_snapshot = None"),
        ("H8", "@@ -6386,6 +6618,15 @@", 6618, 15, "备份后(:6388)、进程启动前构造快照并落盘 captured_at_iso_pre"),
        ("H9", "@@ -7122,7 +7363,8 @@", 7363, 8, "finally 里把快照传入 finalize_trip"),
    ]

    diff_headers = [l for l in diff_lines if l.startswith("@@ ")]
    print(f"    CANDIDATE.diff 包含 @@ 头数量: {len(diff_headers)}")
    assert len(diff_headers) == 9, f"diff 中 hunk 数量 ({len(diff_headers)}) 必须恰好为 9！"

    cand_all_lines = c_text.splitlines()

    print("\n    逐 hunk 定位对账:")
    for i, (hid, header, cand_start, cand_count, desc) in enumerate(expected_hunks):
        actual_diff_header = diff_headers[i]
        assert actual_diff_header == header, f"{hid} header 不匹配: {actual_diff_header} != {header}"
        
        # 验证候选文件中的对应行区间
        slice_lines = cand_all_lines[cand_start - 1 : cand_start - 1 + cand_count]
        assert len(slice_lines) == cand_count, f"{hid} 候选切片行数不匹配"
        
        print(f"    [{hid}] {header} -> 找到 (CANDIDATE.diff hunk #{i+1}, 候选行 L{cand_start}..L{cand_start + cand_count - 1})")
        print(f"         内容说明: {desc}")
        print(f"         候选首行: {slice_lines[0][:60]}")
        print(f"         候选末行: {slice_lines[-1][:60]}")

    print("\n    结论: 9/9 hunks 全部在 CANDIDATE.diff 与 qc151_trip.candidate.py 中定位成功！")

    # 5. 校验 CANDIDATE.diff 与 B2B_DESIGN.md 中 9 个 hunk 逐行内容是否完全相等
    print("\n[5] 校验 CANDIDATE.diff 与 B2B_DESIGN.md 逐 hunk 逐行比对:")
    import re
    design_text = DESIGN_PATH.read_text(encoding="utf-8")
    diff_blocks = re.findall(r"```diff\s*\n(.*?)```", design_text, re.DOTALL)
    assert len(diff_blocks) == 9

    # CANDIDATE.diff 忽略前两行（--- qc151_trip.py\n+++ qc151_trip.candidate.py）
    cand_hunk_blocks = []
    curr_block = []
    for line in diff_lines[2:]:
        if line.startswith("@@ "):
            if curr_block:
                cand_hunk_blocks.append(curr_block)
            curr_block = [line]
        elif curr_block:
            curr_block.append(line)
    if curr_block:
        cand_hunk_blocks.append(curr_block)

    assert len(cand_hunk_blocks) == 9, f"CANDIDATE.diff 提取到 {len(cand_hunk_blocks)} 块"

    for i in range(9):
        d_lines = [l.rstrip() for l in diff_blocks[i].splitlines() if l.strip()]
        c_lines = [l.rstrip() for l in cand_hunk_blocks[i] if l.strip()]
        assert len(d_lines) == len(c_lines), f"Hunk #{i+1} 行数不一致: design {len(d_lines)} vs cand {len(c_lines)}"
        for line_idx, (dl, cl) in enumerate(zip(d_lines, c_lines)):
            assert dl == cl, f"Hunk #{i+1} 行 {line_idx+1} 不一致: dl={dl!r} != cl={cl!r}"
        print(f"    Hunk #{i+1} ({expected_hunks[i][0]}): {len(d_lines)} 行逐行逐字与 B2B_DESIGN.md 100% 相同 -> PASS")

    print("\n全量验证结果: ALL PASS!")


if __name__ == "__main__":
    main()
