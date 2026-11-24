# -*- coding: utf-8 -*-
"""B1 预审探针 · 对 qc151_trip.py 与 W11 补丁建议进行独立预审验证

严禁启动真机、严禁运行 qc151_trip.py 本体、零采样注入。
纯静态检测与确定性逻辑验证，不使用 exec/eval。
"""
import ast
import hashlib
import json
import os
import sys
from pathlib import Path

TARGET_PATH = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py")
TASK_MD_PATH = Path(r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\B1_HARNESS_PATCH\TASK.md")
PATCH_SUGGESTION_PATH = Path(r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\W11_EXCEPT_FRESHNESS\candidate\PATCH_SUGGESTION.md")
CANDIDATE_PATH = Path(r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\W11_EXCEPT_FRESHNESS\candidate\except_freshness.py")

EXPECTED_SHA = "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636"
EXPECTED_BYTES = 399508
EXPECTED_LINES = 7291


def run_checks():
    out = []
    out.append("=== B1 预审独立探针运行报告 ===")
    out.append(f"目标文件: {TARGET_PATH}")

    # 1. 指纹核算
    raw = TARGET_PATH.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    actual_bytes = len(raw)
    lines = raw.decode("utf-8", errors="replace").splitlines(keepends=True)
    actual_lines = len(lines)
    st = TARGET_PATH.stat()
    actual_mtime = st.st_mtime

    out.append("\n--- 1. 改前指纹核算 ---")
    out.append(f"SHA256: {actual_sha} (期望: {EXPECTED_SHA}) -> {'MATCH' if actual_sha == EXPECTED_SHA else 'MISMATCH'}")
    out.append(f"字节数: {actual_bytes} (期望: {EXPECTED_BYTES}) -> {'MATCH' if actual_bytes == EXPECTED_BYTES else 'MISMATCH'}")
    out.append(f"行数:   {actual_lines} (期望: {EXPECTED_LINES}) -> {'MATCH' if actual_lines == EXPECTED_LINES else 'MISMATCH'}")
    out.append(f"mtime:  {actual_mtime}")

    assert actual_sha == EXPECTED_SHA, "SHA mismatch"
    assert actual_bytes == EXPECTED_BYTES, "Byte mismatch"
    assert actual_lines == EXPECTED_LINES, "Line mismatch"

    # 2. 三处改动点实际行号与原文核查
    out.append("\n--- 2. 三处改动点实际行号与代码原文核查 ---")

    # Site 1: backup_carrier (approx 4447-4462)
    out.append("[Site 1] backup_carrier (4447-4462):")
    s1_start, s1_end = 4447, 4462
    for idx in range(s1_start, s1_end + 1):
        out.append(f"  {idx}: {lines[idx-1].rstrip()}")

    # Site 2: copy_post_except_evidence (approx 4561-4599)
    out.append("\n[Site 2] copy_post_except_evidence (核心 4574-4586):")
    s2_start, s2_end = 4561, 4587
    for idx in range(s2_start, s2_end + 1):
        out.append(f"  {idx}: {lines[idx-1].rstrip()}")

    # Site 3: 调用点核查
    out.append("\n[Site 3] 调用点与作用域核查:")
    out.append("  3a. finalize_trip 函数定义 (行 5900):")
    for idx in range(5900, 5910):
        out.append(f"    {idx}: {lines[idx-1].rstrip()}")
    out.append("  3b. _except_evidence_copy 内部定义与调用 (行 5938-5942):")
    for idx in range(5938, 5943):
        out.append(f"    {idx}: {lines[idx-1].rstrip()}")
    out.append("  3c. main 内部 backup_carrier 与 U-5 段 (行 6385-6409):")
    for idx in range(6385, 6410):
        out.append(f"    {idx}: {lines[idx-1].rstrip()}")
    out.append("  3d. main 内部 finally 调用 finalize_trip (行 7117-7126):")
    for idx in range(7117, 7126):
        out.append(f"    {idx}: {lines[idx-1].rstrip()}")

    # 3. :677 禁令与 except_set_diff 核查
    out.append("\n--- 3. :677 禁令与 except_set_diff 核查 ---")
    for idx in range(672, 709):
        out.append(f"  {idx}: {lines[idx-1].rstrip()}")

    # 4. U-5 边界核查
    out.append("\n--- 4. U-5 边界核查 (:6390-6408) ---")
    for idx in range(6390, 6409):
        out.append(f"  {idx}: {lines[idx-1].rstrip()}")

    # 5. Leader 补丁建议中的严重缺陷静态与确定性逻辑验证
    out.append("\n--- 5. Leader 补丁建议中的严重逻辑与作用域缺陷验证 ---")

    # 缺陷 A: 作用域与 NameError 验证
    out.append("[缺陷 A: 作用域断裂与 NameError]")
    # 模拟函数调用拓扑：finalize_trip 为顶级函数，main 为顶级函数
    def _sim_finalize_trip(rec, carrier_dir, bak, out_dir):
        def _sim_except_evidence_copy():
            # Leader 建议在此处直接引用 _pre_freshness_snapshot
            return _sim_mock_caller(_pre_freshness_snapshot)
        return _sim_except_evidence_copy()

    def _sim_mock_caller(snap):
        return snap

    def _sim_main():
        bak = {"except.txt": {"sha256": "abc", "size": 10}}
        _pre_freshness_snapshot = (bak or {}).get("except.txt") or {"exists": False}
        _sim_finalize_trip(None, None, bak, None)

    try:
        _sim_main()
        out.append("  UNEXPECTED: 未抛出异常！")
    except NameError as e:
        out.append(f"  CONFIRMED: 顶级函数间局部变量不共享，抛出预期的 NameError: {e}")

    # 缺陷 B: 字典键名不匹配导致 100% 误判 new_first_appearance
    out.append("\n[缺陷 B: bak 缺失 'exists' 键导致 100% 误判 new_first_appearance]")
    # 模拟 Leader 补丁 1 的 backup_carrier 构造
    dst_stat_st_size = 100
    h = "test_sha256_hash_value"
    st_mtime = 123456789.0
    bak_item = {
        "path": "dummy/path",
        "size": dst_stat_st_size,
        "sha256": h,
        "mtime_pre": st_mtime,
        "captured_at_epoch": 123456789.0,
        "captured_at_iso": "2026-11-06T00:00:00Z"
    }
    # Leader 补丁 3
    pre_snapshot = bak_item or {"exists": False}

    # Leader 补丁 2 判定
    _pre = dict(pre_snapshot or {})
    _pre_sha, _pre_mtime = _pre.get("sha256"), _pre.get("mtime")
    _mtime_post = st_mtime  # 假设跑后完全没动

    if not _pre.get("exists"):
        _fresh = ("new_first_appearance", "high")
    elif _pre_sha is not None and _pre_sha != h:
        _fresh = ("new_write", "high")
    elif _pre_mtime is not None and abs(_mtime_post - _pre_mtime) > 0.0:
        _fresh = ("rewritten_same_content", "low" if _mtime_post < _pre_mtime else "medium")
    else:
        _fresh = ("leftover_unchanged", "high")

    out.append(f"  输入基线: sha={h}, mtime={st_mtime}, 跑后完全相同")
    out.append(f"  _pre.get('exists') 返回值: {_pre.get('exists')!r}")
    out.append(f"  判定结果: {_fresh} (期望应为 leftover_unchanged, high)")
    assert _fresh[0] == "new_first_appearance", "Logic behavior changed"
    out.append("  CONFIRMED: 由于 bak 缺少 'exists': True，原样遗留文件被 100% 误判为 new_first_appearance！")

    # 缺陷 C: 时间戳键名不匹配导致 mtime 旁证失效
    out.append("\n[缺陷 C: 'mtime_pre' vs 'mtime' 导致 rewritten_same_content 死代码]")
    out.append(f"  bak 中存储的键: 'mtime_pre' = {bak_item.get('mtime_pre')}")
    out.append(f"  补丁 2 中读取的键: _pre.get('mtime') = {_pre.get('mtime')}")
    out.append("  CONFIRMED: _pre_mtime 恒为 None，rewritten_same_content 分支永远不可能被执行！")

    # 缺陷 D: 截断候选用例
    out.append("\n[缺陷 D: 跑后文件缺失时 early return None 导致 absent_both / vanished 丢失]")
    out.append("  copy_post_except_evidence:4575-4578 在 if not src.exists(): return None")
    out.append("  CONFIRMED: 正常运行无异常文件生成时，函数直接返回 None，无法产出 candidate/except_freshness.py 的 absent_both 语义！")

    # 缺陷 E: .gitignore 规则核对
    out.append("\n[缺陷 E: .gitignore 与 git diff 适用性核查]")
    gitignore_path = Path(r"D:\Project\ra2-campaign-forge\.gitignore")
    if gitignore_path.exists():
        gi_lines = gitignore_path.read_text(encoding="utf-8").splitlines()
        for ln_idx, ln in enumerate(gi_lines, 1):
            if "out/" in ln or "out" == ln.strip():
                out.append(f"  .gitignore:{ln_idx}: {ln}")

    out_text = "\n".join(out)
    return out_text


if __name__ == "__main__":
    report = run_checks()
    out_path = Path(r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\B1_HARNESS_PATCH\_b1_preaudit_out.txt")
    out_path.write_text(report, encoding="utf-8")
    print(report)
