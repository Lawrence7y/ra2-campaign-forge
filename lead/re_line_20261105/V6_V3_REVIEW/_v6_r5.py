#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_v6_r5.py - V6_V3_REVIEW R5 独立复核探针
复核目标: W5 扩项单测套件 (_w5_test.py) 在 D-21 裁 A 后的 V3 状态断言强度与覆盖真实性
验证项:
  1. 被核对象 SHA256 与字节数实算与绑定
  2. 重跑 _w5_test.py 确认 6 条全 PASS 且 EXIT=0
  3. 审查用例 2 断言强度: 是否严格断言 total_extra_reads == edges * 5 (而非 <=)
  4. 审查用例 2.3 时间戳全序断言: 是否已适配复用模式 (ts["f_pre"] <= ts["segment_start"])
  5. 反例验证: 在 V6_V3_REVIEW 隔离副本中故意改坏 f_pre 处理，证明单测确会 FAIL 且退出码为 1
  6. 绝不动原文件核验: 对比原件 SHA256，证明原文件零修改
"""

import os
import sys
import shutil
import hashlib
import subprocess
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent.parent

W5_DIR = REPO_ROOT / "lead" / "re_line_20261105" / "W5_HARNESS_EXT"
A1_DIR = REPO_ROOT / "lead" / "re_line_20261105" / "A1_SAMPLER_CANDIDATE"

TARGET_TEST = W5_DIR / "_w5_test.py"
TARGET_EXT = W5_DIR / "qc151_trip.harness8_v4_ext.py"
TARGET_SAMPLER = A1_DIR / "frame_edge_sampler.py"

OUT_TXT_PATH = BASE_DIR / "_v6_r5_out.txt"

# 任务书参照值
REF_SHA256 = {
    "_w5_test.py": "df5771a830c4fa2df5445156284a65d7a5d1e2c4ac80945350a0d05c727df2c8",
    "qc151_trip.harness8_v4_ext.py": "5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161",
    "frame_edge_sampler.py": "b382e893bafc6a7f38d08572affaa663eaef56a8de7c3f361eea38cc34185f3e",
}

REF_SIZE = {
    "_w5_test.py": 36624,
    "qc151_trip.harness8_v4_ext.py": 499047,
    "frame_edge_sampler.py": 21411,
}

lines_out = []

def log(msg: str = ""):
    print(msg)
    lines_out.append(msg)

def sha256_file(p: Path) -> tuple[str, int]:
    data = p.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def main():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log("=" * 80)
    log("V6_V3_REVIEW R5 独立复核探针 (_v6_r5.py)")
    log(f"执行时刻: {now_str}")
    log("=" * 80)

    # --------------------------------------------------------------------------
    # 1. 被核对象 SHA256 与文件大小实算绑定
    # --------------------------------------------------------------------------
    log("\n[1. 被核对象 SHA256 与字节数实算绑定]")
    log("-" * 80)

    test_sha, test_size = sha256_file(TARGET_TEST)
    ext_sha, ext_size = sha256_file(TARGET_EXT)
    sampler_sha, sampler_size = sha256_file(TARGET_SAMPLER)

    log(f"被核对象路径: {TARGET_TEST.resolve()}")
    log(f"实算 SHA256 : {test_sha}")
    log(f"实算字节数   : {test_size} 字节")
    log(f"参照 SHA256 : {REF_SHA256['_w5_test.py']}")
    log(f"参照字节数   : {REF_SIZE['_w5_test.py']} 字节")
    assert test_sha == REF_SHA256["_w5_test.py"], "被核对象 _w5_test.py SHA256 不匹配!"
    assert test_size == REF_SIZE["_w5_test.py"], "被核对象 _w5_test.py 字节数不匹配!"
    log(">> _w5_test.py SHA256 与字节数校验: 严格吻合 [PASS]")

    log(f"\n配套扩展件路径: {TARGET_EXT.resolve()}")
    log(f"实算 SHA256   : {ext_sha}")
    log(f"实算字节数     : {ext_size} 字节")
    assert ext_sha == REF_SHA256["qc151_trip.harness8_v4_ext.py"]
    log(">> qc151_trip.harness8_v4_ext.py SHA256 校验: 严格吻合 [PASS]")

    log(f"\n配套采样件路径: {TARGET_SAMPLER.resolve()}")
    log(f"实算 SHA256   : {sampler_sha}")
    log(f"实算字节数     : {sampler_size} 字节")
    assert sampler_sha == REF_SHA256["frame_edge_sampler.py"]
    log(">> frame_edge_sampler.py SHA256 校验: 严格吻合 [PASS]")

    # --------------------------------------------------------------------------
    # 2. 原版 _w5_test.py 完整重跑与 6 条用例判定
    # --------------------------------------------------------------------------
    log("\n[2. 原版 _w5_test.py 独立重跑 (python -I -X utf8)]")
    log("-" * 80)
    cmd = [sys.executable, "-I", "-X", "utf8", str(TARGET_TEST.resolve())]
    log(f"执行命令: {' '.join(cmd)}")
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    log(f"进程退出码 (EXIT_CODE): {proc.returncode}")
    log(f"输出摘要 (最后 25 行):")
    for l in proc.stdout.strip().splitlines()[-25:]:
        log("  " + l)

    assert proc.returncode == 0, f"单测退出码必须为 0，实际为 {proc.returncode}"
    assert "总计: 6 用例, 通过: 6, 失败: 0" in proc.stdout, "单测用例未全部通过"
    assert "最终判定: PASS (EXIT=0)" in proc.stdout, "未检测到最终 PASS (EXIT=0) 标识"
    log(">> 原版单测重跑结果: 6 条全 PASS，EXIT=0 [PASS]")

    # --------------------------------------------------------------------------
    # 3. 审查用例 2 断言强度 (total_extra_reads == edges * 5)
    # --------------------------------------------------------------------------
    log("\n[3. 审查用例 2 断言强度]")
    log("-" * 80)
    test_src = TARGET_TEST.read_text(encoding="utf-8")
    
    # 3.1 检查 total_extra_reads 的断言
    assert_eq_found = "assert total_extra_reads == expected_edges * 5" in test_src
    assert_le_found = "total_extra_reads <=" in test_src
    log(f"是否包含严格等式断言 'assert total_extra_reads == expected_edges * 5': {assert_eq_found}")
    log(f"是否存在放宽的不等式断言 'total_extra_reads <=': {assert_le_found}")
    assert assert_eq_found, "未找到严格等式断言 assert total_extra_reads == expected_edges * 5"
    assert not assert_le_found, "发现了放宽的 <= 断言，断言强度不合规!"

    # 3.2 检查帧号追加读与各 VA 追加读的等式断言
    frame_read_assert = "assert extra_frame_reads == expected_edges * 1" in test_src
    log(f"是否包含追加帧号读等式断言 'assert extra_frame_reads == expected_edges * 1': {frame_read_assert}")
    assert frame_read_assert

    for va_name in ["VA_GEN_STAMP", "VA_THREAT_CALLS", "VA_DIRTY_RECT", "VA_BULLET"]:
        va_assert = f"assert call_counts[{va_name}] == expected_edges" in test_src
        log(f"是否包含 {va_name} 严格等式断言: {va_assert}")
        assert va_assert

    # 3.3 检查 2.1b 复用模式读序与读次
    reuse_reads_assert = "assert len(order_log2) == 5" in test_src
    sample_reuse_assert = 'assert sample_reuse["reads_per_sample"] == 5' in test_src
    log(f"是否包含复用模式 5 读断言 'assert len(order_log2) == 5': {reuse_reads_assert}")
    log(f"是否包含样本结构 'sample_reuse[\"reads_per_sample\"] == 5': {sample_reuse_assert}")
    assert reuse_reads_assert and sample_reuse_assert
    log(">> 用例 2 断言强度判定: 确为严格等式 ==（非放宽 <=），逐字段与总量双重死锁 [PASS]")

    # --------------------------------------------------------------------------
    # 4. 审查用例 2.3 时间戳全序断言
    # --------------------------------------------------------------------------
    log("\n[4. 审查用例 2.3 时间戳全序断言]")
    log("-" * 80)
    # 源码中通过反斜杠折行:
    # assert ts["f_pre"] <= ts["segment_start"] <= ts["gen_stamp"] <= ts["threat_calls"] \
    #        <= ts["dirty_rect_count"] <= ts["bullet_count"] <= ts["f_post_start"] <= ts["segment_end"]
    ts_part1 = 'assert ts["f_pre"] <= ts["segment_start"] <= ts["gen_stamp"] <= ts["threat_calls"]'
    ts_part2 = '<= ts["dirty_rect_count"] <= ts["bullet_count"] <= ts["f_post_start"] <= ts["segment_end"]'
    ts_found = (ts_part1 in test_src) and (ts_part2 in test_src)
    log(f"全序链断言第一段 ('{ts_part1}'): {ts_part1 in test_src}")
    log(f"全序链断言第二段 ('{ts_part2}'): {ts_part2 in test_src}")
    log(f"是否包含 'ts[\"f_pre\"] <= ts[\"segment_start\"]' 适配复用模式: {'ts[\"f_pre\"] <= ts[\"segment_start\"]' in test_src}")
    assert ts_found, "用例 2.3 中未找到适配复用模式的时间戳全序断言!"
    log(">> 用例 2.3 时间戳断言判定: 已完全适配 D-21 裁 A 复用前读模式 (ts['f_pre'] <= ts['segment_start']) [PASS]")

    # --------------------------------------------------------------------------
    # 5. 反例要求: 在 V6_V3_REVIEW 内复制副本构造反例，验证改坏 f_pre 后单测必 FAIL
    # --------------------------------------------------------------------------
    log("\n[5. 隔离副本反例检验 (★ 反例要求: 绝不动原文件)]")
    log("-" * 80)

    sandbox_dir = BASE_DIR / "_counterexample"
    if sandbox_dir.exists():
        shutil.rmtree(sandbox_dir)
    sandbox_dir.mkdir(parents=True, exist_ok=True)

    sb_w5 = sandbox_dir / "W5_HARNESS_EXT"
    sb_a1 = sandbox_dir / "A1_SAMPLER_CANDIDATE"
    sb_w5.mkdir(parents=True, exist_ok=True)
    sb_a1.mkdir(parents=True, exist_ok=True)

    # 复制副本到沙盒内
    shutil.copy2(TARGET_TEST, sb_w5 / "_w5_test.py")
    shutil.copy2(TARGET_EXT, sb_w5 / "qc151_trip.harness8_v4_ext.py")
    shutil.copy2(TARGET_SAMPLER, sb_a1 / "frame_edge_sampler.py")

    sb_test = sb_w5 / "_w5_test.py"
    sb_sampler = sb_a1 / "frame_edge_sampler.py"

    orig_sampler_content = sb_sampler.read_text(encoding="utf-8")

    # --------------------------------------------------
    # 反例 A: 破坏 f_pre 复用 (退回 6 读: 传了 f_pre 依然自读 FRAME_VA)
    # --------------------------------------------------
    log("--- 反例实验 A: 破坏 f_pre 读次处理 (复用模式下依然调用 reader(FRAME_VA)，退化为 6 读) ---")
    bad_a_content = orig_sampler_content.replace(
        'if reuse:\n        # 复用前读：不再调 reader(FRAME_VA)，也不再取新 clock() 当前锚\n        rec["f_pre"] = f_pre',
        'if reuse:\n        # 【故意注入反例 A】复用模式下依然强行自读 FRAME_VA\n        rec["f_pre"] = read_one(reader, FRAME_VA)'
    )
    assert bad_a_content != orig_sampler_content, "反例 A 注入替换失败"
    sb_sampler.write_text(bad_a_content, encoding="utf-8")

    proc_a = subprocess.run([sys.executable, "-I", "-X", "utf8", str(sb_test.resolve())],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    log(f"反例 A 退出码: {proc_a.returncode} (预期 != 0)")
    log("反例 A 捕获的异常信息:")
    for line in proc_a.stdout.splitlines():
        if "AssertionError" in line or "FAIL" in line or "用例执行异常" in line:
            log("  " + line)
    assert proc_a.returncode != 0, "反例 A 注入后单测未 FAIL，断言存在漏判!"
    assert "AssertionError" in proc_a.stdout
    log(">> 反例实验 A 结论: 单测立即触发 AssertionError 且 EXIT!=0，成功捕获多余读取 [PASS]")

    # --------------------------------------------------
    # 反例 B: 破坏时间戳真实性 (冒充外层时刻: ts["f_pre"] = clock() 而非 t_pre)
    # --------------------------------------------------
    log("\n--- 反例实验 B: 破坏时间戳真实性 (用进入时刻冒充外层读前锚时刻) ---")
    bad_b_content = orig_sampler_content.replace(
        'rec["ts"]["f_pre"] = t_pre',
        'rec["ts"]["f_pre"] = clock()  # 【故意注入反例 B】冒充外层时刻'
    )
    assert bad_b_content != orig_sampler_content, "反例 B 注入替换失败"
    sb_sampler.write_text(bad_b_content, encoding="utf-8")

    proc_b = subprocess.run([sys.executable, "-I", "-X", "utf8", str(sb_test.resolve())],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    log(f"反例 B 退出码: {proc_b.returncode} (预期 != 0)")
    log("反例 B 捕获的异常信息:")
    for line in proc_b.stdout.splitlines():
        if "AssertionError" in line or "FAIL" in line or "用例执行异常" in line:
            log("  " + line)
    assert proc_b.returncode != 0, "反例 B 注入后单测未 FAIL，断言存在漏判!"
    assert "f_pre 时刻必须等于外层读前锚" in proc_b.stdout
    log(">> 反例实验 B 结论: 单测精准捕获时间戳冒充并抛出断言失败 [PASS]")

    # --------------------------------------------------
    # 反例 C: 破坏时间戳全序契约 (使 ts["segment_start"] 倒退早于 ts["f_pre"])
    # --------------------------------------------------
    log("\n--- 反例实验 C: 破坏时间戳全序契约 (ts['segment_start'] < ts['f_pre']，检验用例 2.3 全序断言) ---")
    bad_c_content = orig_sampler_content.replace(
        'if reuse:\n        rec["ts"]["segment_start"] = clock()',
        'if reuse:\n        # 【故意注入反例 C】令 segment_start 倒退到 f_pre 之前，破坏全序\n        rec["ts"]["segment_start"] = (t_pre - 1.0) if t_pre is not None else clock()'
    )
    assert bad_c_content != orig_sampler_content, "反例 C 注入替换失败"
    sb_sampler.write_text(bad_c_content, encoding="utf-8")

    proc_c = subprocess.run([sys.executable, "-I", "-X", "utf8", str(sb_test.resolve())],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    log(f"反例 C 退出码: {proc_c.returncode} (预期 != 0)")
    log("反例 C 捕获的异常信息:")
    for line in proc_c.stdout.splitlines():
        if "AssertionError" in line or "FAIL" in line or "用例执行异常" in line:
            log("  " + line)
    assert proc_c.returncode != 0, "反例 C 注入后单测未 FAIL，断言存在漏判!"
    assert "AssertionError" in proc_c.stdout
    log(">> 反例实验 C 结论: 用例 2.3 单调全序断言成功拦截时间倒流并立即抛出 AssertionError，非摆设 [PASS]")

    # 还原并清理沙盒
    shutil.rmtree(sandbox_dir)
    log("\n>> 临时沙盒清理完成: 隔离反例副本已安全移除")

    # --------------------------------------------------------------------------
    # 6. 原文件零修改确认
    # --------------------------------------------------------------------------
    log("\n[6. 原文件零修改证明]")
    log("-" * 80)
    final_test_sha, final_test_size = sha256_file(TARGET_TEST)
    final_ext_sha, final_ext_size = sha256_file(TARGET_EXT)
    final_sampler_sha, final_sampler_size = sha256_file(TARGET_SAMPLER)

    log(f"TARGET_TEST    后验 SHA256: {final_test_sha} (吻合: {final_test_sha == test_sha})")
    log(f"TARGET_EXT     后验 SHA256: {final_ext_sha} (吻合: {final_ext_sha == ext_sha})")
    log(f"TARGET_SAMPLER 后验 SHA256: {final_sampler_sha} (吻合: {final_sampler_sha == sampler_sha})")
    assert final_test_sha == test_sha
    assert final_ext_sha == ext_sha
    assert final_sampler_sha == sampler_sha
    log(">> 原文件字节绝对未动 (SHA256 100% 保持一致) [PASS]")

    log("\n" + "=" * 80)
    log("R5 全部核验项执行完毕: 全部严格通过 (CONFIRMED)")
    log("=" * 80)

    # 落盘输出
    with open(OUT_TXT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_out) + "\n")
    print(f"\n[OK] 探针输出已写入: {OUT_TXT_PATH.resolve()}")

if __name__ == "__main__":
    main()
