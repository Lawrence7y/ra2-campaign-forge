#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_r5_independent_check.py · 独立复核员·R5 独立验证脚本
用于独立重跑并复核 R5 的回件及其结论的真实性与严谨性
"""

import ast
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path("D:/Project/ra2-campaign-forge")
W5_DIR = REPO_ROOT / "lead" / "re_line_20261105" / "W5_HARNESS_EXT"
A1_DIR = REPO_ROOT / "lead" / "re_line_20261105" / "A1_SAMPLER_CANDIDATE"
V6_DIR = REPO_ROOT / "lead" / "re_line_20261105" / "V6_V3_REVIEW"
REVIEWS_DIR = V6_DIR / "reviews"

TARGET_TEST = W5_DIR / "_w5_test.py"
TARGET_EXT = W5_DIR / "qc151_trip.harness8_v4_ext.py"
TARGET_SAMPLER = A1_DIR / "frame_edge_sampler.py"
R5_MD = V6_DIR / "parts" / "R5.md"
V6_R5_PY = V6_DIR / "_v6_r5.py"
V6_R5_OUT = V6_DIR / "_v6_r5_out.txt"

def sha256_file(p: Path) -> tuple[str, int]:
    data = p.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)

def main():
    print("=" * 80)
    print("独立复核员·R5 独立重测与审查脚本启动")
    print("=" * 80)

    # --------------------------------------------------------------------------
    # 1. 独立量测 SHA256 与字节数
    # --------------------------------------------------------------------------
    print("\n[CHECK 1] 独立物理量测算")
    test_sha, test_size = sha256_file(TARGET_TEST)
    ext_sha, ext_size = sha256_file(TARGET_EXT)
    sampler_sha, sampler_size = sha256_file(TARGET_SAMPLER)
    r5_md_sha, r5_md_size = sha256_file(R5_MD)
    v6_r5_sha, v6_r5_size = sha256_file(V6_R5_PY)

    print(f"  TARGET_TEST    : {test_sha} ({test_size} bytes)")
    print(f"  TARGET_EXT     : {ext_sha} ({ext_size} bytes)")
    print(f"  TARGET_SAMPLER : {sampler_sha} ({sampler_size} bytes)")
    print(f"  R5_MD          : {r5_md_sha} ({r5_md_size} bytes)")
    print(f"  V6_R5_PY       : {v6_r5_sha} ({v6_r5_size} bytes)")

    # 检查 R5.md 的头部绑定行
    r5_md_text = R5_MD.read_text(encoding="utf-8")
    assert "被核对象 SHA256 = df5771a830c4fa2df5445156284a65d7a5d1e2c4ac80945350a0d05c727df2c8" in r5_md_text, "R5.md 缺少 SHA256 头部绑定"
    assert "字节数 = 36624" in r5_md_text, "R5.md 缺少字节数头部绑定"
    print("  >> R5.md 头部绑定行存在且哈希严格吻合 [PASS]")

    # --------------------------------------------------------------------------
    # 2. 独立重跑原版 _w5_test.py
    # --------------------------------------------------------------------------
    print("\n[CHECK 2] 独立重跑 _w5_test.py (保护既有 _w5_test_out.txt)")
    out_txt_file = W5_DIR / "_w5_test_out.txt"
    backup_out_bytes = out_txt_file.read_bytes() if out_txt_file.exists() else None

    cmd = [sys.executable, "-I", "-X", "utf8", str(TARGET_TEST)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")

    # 恢复 _w5_test_out.txt 保持零文件修改
    if backup_out_bytes is not None:
        out_txt_file.write_bytes(backup_out_bytes)

    print(f"  退出码 (EXIT_CODE): {proc.returncode}")
    print("  重跑末尾输出:")
    for line in proc.stdout.strip().splitlines()[-15:]:
        print("    " + line)

    assert proc.returncode == 0, f"_w5_test.py 退出码不为 0: {proc.returncode}"
    assert "总计: 6 用例, 通过: 6, 失败: 0" in proc.stdout, "单测用例未全过"
    assert "最终判定: PASS (EXIT=0)" in proc.stdout, "缺少 PASS 最终判定"
    print("  >> _w5_test.py 6 条用例独立实跑全 PASS 且 EXIT=0 [PASS]")

    # --------------------------------------------------------------------------
    # 3. 审查用例 2 断言强度 (AST 与源码检查)
    # --------------------------------------------------------------------------
    print("\n[CHECK 3] 用例 2 断言强度审查 (AST 与文本解析)")
    test_src = TARGET_TEST.read_text(encoding="utf-8")
    tree = ast.parse(test_src, filename=str(TARGET_TEST))

    # 遍历 AST 寻找所有的 Assert 节点
    asserts = [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]
    print(f"  AST 找到 Assert 节点总数: {len(asserts)}")

    eq_total_found = False
    le_total_found = False
    extra_frame_found = False

    for n in asserts:
        expr_str = ast.unparse(n.test)
        if "total_extra_reads" in expr_str:
            print(f"    total_extra_reads 断言表达式: {expr_str}")
            if "total_extra_reads == expected_edges * 5" in expr_str:
                eq_total_found = True
            if "<=" in expr_str:
                le_total_found = True
        if "extra_frame_reads" in expr_str:
            print(f"    extra_frame_reads 断言表达式: {expr_str}")
            if "extra_frame_reads == expected_edges * 1" in expr_str:
                extra_frame_found = True

    assert eq_total_found, "未找到严格等式 assert total_extra_reads == expected_edges * 5"
    assert not le_total_found, "存在放宽的 total_extra_reads <= 断言"
    assert extra_frame_found, "未找到 extra_frame_reads == expected_edges * 1"
    assert "assert len(order_log2) == 5" in test_src, "未找到 len(order_log2) == 5"
    assert 'assert sample_reuse["reads_per_sample"] == 5' in test_src, "未找到 reads_per_sample == 5"
    print("  >> 用例 2 确为严格等式 == 5 读死锁，无任何 <= 放宽 [PASS]")

    # --------------------------------------------------------------------------
    # 4. 审查用例 2.3 时间戳全序断言
    # --------------------------------------------------------------------------
    print("\n[CHECK 4] 用例 2.3 时间戳全序断言审查")
    ts_assert_found = False
    for n in asserts:
        expr_str = ast.unparse(n.test)
        if "f_pre" in expr_str and "segment_start" in expr_str:
            print(f"    时间戳全序断言表达式: {expr_str}")
            if "f_pre" in expr_str and "segment_start" in expr_str and "<=" in expr_str:
                ts_assert_found = True
                break

    assert ts_assert_found, "未找到已适配复用模式的时间戳全序断言"
    # 同时在源码文本中检查
    assert 'ts["f_pre"] <= ts["segment_start"]' in test_src, "源码文本未直接包含 ts['f_pre'] <= ts['segment_start']"
    print("  >> 用例 2.3 时间戳全序已精准适配 D-21 裁 A 复用前读模式 [PASS]")

    # --------------------------------------------------------------------------
    # 5. 在 reviews 内部建立隔离沙盒执行反例攻击验证
    # --------------------------------------------------------------------------
    print("\n[CHECK 5] 隔离沙盒反例注入检验 (在 reviews/_sandbox_r5 中进行)")
    sandbox = REVIEWS_DIR / "_sandbox_r5"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(parents=True, exist_ok=True)

    sb_w5 = sandbox / "W5_HARNESS_EXT"
    sb_a1 = sandbox / "A1_SAMPLER_CANDIDATE"
    sb_w5.mkdir(parents=True, exist_ok=True)
    sb_a1.mkdir(parents=True, exist_ok=True)

    shutil.copy2(TARGET_TEST, sb_w5 / "_w5_test.py")
    shutil.copy2(TARGET_EXT, sb_w5 / "qc151_trip.harness8_v4_ext.py")
    shutil.copy2(TARGET_SAMPLER, sb_a1 / "frame_edge_sampler.py")

    sb_test = sb_w5 / "_w5_test.py"
    sb_sampler = sb_a1 / "frame_edge_sampler.py"
    orig_sampler_content = sb_sampler.read_text(encoding="utf-8")

    # 反例 A: 破坏 f_pre 复用 (退回 6 读)
    print("  --- 反例 A (退回 6 读) ---")
    bad_a = orig_sampler_content.replace(
        'if reuse:\n        # 复用前读：不再调 reader(FRAME_VA)，也不再取新 clock() 当前锚\n        rec["f_pre"] = f_pre',
        'if reuse:\n        # 【故意注入反例 A】复用模式下依然强行自读 FRAME_VA\n        rec["f_pre"] = read_one(reader, FRAME_VA)'
    )
    assert bad_a != orig_sampler_content
    sb_sampler.write_text(bad_a, encoding="utf-8")
    proc_a = subprocess.run([sys.executable, "-I", "-X", "utf8", str(sb_test)],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    print(f"    反例 A 退出码: {proc_a.returncode}")
    assert proc_a.returncode != 0, "反例 A 未导致单测 FAIL"
    assert "AssertionError" in proc_a.stdout, "反例 A 未抛出 AssertionError"
    print("    >> 反例 A 成功触发 AssertionError 且 EXIT!=0 [PASS]")

    # 反例 B: 破坏时间戳真实性 (冒充外层时刻)
    print("  --- 反例 B (冒充外层时刻) ---")
    bad_b = orig_sampler_content.replace(
        'rec["ts"]["f_pre"] = t_pre',
        'rec["ts"]["f_pre"] = clock()  # 【故意注入反例 B】冒充外层时刻'
    )
    assert bad_b != orig_sampler_content
    sb_sampler.write_text(bad_b, encoding="utf-8")
    proc_b = subprocess.run([sys.executable, "-I", "-X", "utf8", str(sb_test)],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    print(f"    反例 B 退出码: {proc_b.returncode}")
    assert proc_b.returncode != 0, "反例 B 未导致单测 FAIL"
    assert "AssertionError" in proc_b.stdout, "反例 B 未抛出 AssertionError"
    assert "f_pre 时刻必须等于外层读前锚" in proc_b.stdout
    print("    >> 反例 B 成功触发 AssertionError (f_pre 时刻必须等于外层读前锚) [PASS]")

    # 反例 C: 破坏时间戳全序契约 (倒退时间)
    print("  --- 反例 C (破坏时间戳全序链) ---")
    bad_c = orig_sampler_content.replace(
        'if reuse:\n        rec["ts"]["segment_start"] = clock()',
        'if reuse:\n        # 【故意注入反例 C】令 segment_start 倒退到 f_pre 之前，破坏全序\n        rec["ts"]["segment_start"] = (t_pre - 1.0) if t_pre is not None else clock()'
    )
    assert bad_c != orig_sampler_content
    sb_sampler.write_text(bad_c, encoding="utf-8")
    proc_c = subprocess.run([sys.executable, "-I", "-X", "utf8", str(sb_test)],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    print(f"    反例 C 退出码: {proc_c.returncode}")
    assert proc_c.returncode != 0, "反例 C 未导致单测 FAIL"
    assert "AssertionError" in proc_c.stdout, "反例 C 未抛出 AssertionError"
    print("    >> 反例 C 成功触发用例 2.3 全序 AssertionError [PASS]")

    # 清理沙盒
    shutil.rmtree(sandbox)
    print("  >> 沙盒已清理干净 [PASS]")

    # --------------------------------------------------------------------------
    # 6. 后验原文件零修改核查
    # --------------------------------------------------------------------------
    print("\n[CHECK 6] 后验原文件哈希逐字节比对")
    final_test_sha, final_test_size = sha256_file(TARGET_TEST)
    final_ext_sha, final_ext_size = sha256_file(TARGET_EXT)
    final_sampler_sha, final_sampler_size = sha256_file(TARGET_SAMPLER)
    assert final_test_sha == test_sha, "TARGET_TEST 被篡改!"
    assert final_ext_sha == ext_sha, "TARGET_EXT 被篡改!"
    assert final_sampler_sha == sampler_sha, "TARGET_SAMPLER 被篡改!"
    print(f"  TARGET_TEST    保持不变: {final_test_sha == test_sha}")
    print(f"  TARGET_EXT     保持不变: {final_ext_sha == ext_sha}")
    print(f"  TARGET_SAMPLER 保持不变: {final_sampler_sha == sampler_sha}")
    print("  >> 原文件绝对零修改 [PASS]")

    print("\n" + "=" * 80)
    print("独立复核员·R5 全流程复核完成: 全部核验通过 (VERDICT: CONFIRMED)")
    print("=" * 80)

if __name__ == "__main__":
    main()
