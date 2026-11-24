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

    # ---------- 出口改造（仅追加；原件 1-288 行逐字节未动）----------
    # 原型：lead/dtrigger_compare_20261107/_check_dtrigger.py:31-35 + :226-228
    # A. 原件对自身的检查 = :81-82 / :88 / :94 / :110-112 / :127-128 / :133 /
    #    :138(×4) / :145 / :162 / :199 / :209-210 / :221 / :231-232 / :243 /
    #    :253-254 / :273-275 共 25 条 assert。结果通道：:50-52 log() 把每一行
    #    打到 stdout 并 append 进 lines_out；:283-285 把同一份 lines_out 落盘
    #    OUT_TXT_PATH (:33)；各处另有 ">> ... [PASS]" 小结。无显式出口，
    #    正常跑到 :288 退出码恒 0；任一 assert 失败则抛 AssertionError (EXIT=1)。
    # B. 本件不是库本体：全库 Python 实 grep 无任何 import _v6_r5 /
    #    spec_from_file_location 引用；_r5_independent_check.py:26 与
    #    _ecv_compare.py:44 只把它当被读的磁盘文件/路径字符串处理。
    #    :1-58 常量与 log/sha256_file、:59-285 的 main 主体、:287-288 守卫
    #    全部逐字保留；新增代码只写在 __main__ 守卫内部，被 import 时不执行，
    #    故不向库里新增任何全局名字（ok/check/_out/... 都不是模块级可见名）。
    # C. main() 的局部变量在模块级不可见；为不重跑、不重复打印、不改写任何
    #    原有 assert/打印/写盘/判定式，取 main() 刚写出的 OUT_TXT_PATH 文本
    #    与三个只读目标件为同一判定的记录，逐字重算每条 assert 的布尔表达式
    #    并合取进 ok。ok ≡ 25 条 assert 全部为真；任一 assert 原会抛异常的
    #    场合对应 cond 为假 -> ok 置假 -> EXIT=1，全部为真 -> EXIT=0。
    # :125/:126/:137/:143/:144/:159-161 打印的是【被测对象 _w5_test.py】的
    #    断言强度/时间戳词句，属领域观测值；其真假由 :127-128/:133/:138/:145/
    #    :162 的 assert 表达式承载，故只按那些 assert 的同一表达式聚合，不另造判定。
    # :204/:226/:248 的反例 EXIT!=0、:210/:232/:254 的 AssertionError 字样
    #    是【故意注入缺陷后被测单测的预期 FAIL 表现】，不是本脚本失败；原件的
    #    assert 正是要求它们为真，故按 assert 原式聚合，绝不把 FAIL/!=0 取反塞进 ok。

    ok = True

    def check(name, cond, detail=""):
        global ok
        ok = ok and bool(cond)          # 合取聚合：全部检查通过才真（唯一置假点）
        print(("  [PASS] " if cond else "  [FAIL] ") + name
              + ((" | " + detail) if detail else ""))

    _out = OUT_TXT_PATH.read_text(encoding="utf-8") if OUT_TXT_PATH.is_file() else ""
    _src = TARGET_TEST.read_text(encoding="utf-8")
    _sampler_src = TARGET_SAMPLER.read_text(encoding="utf-8")
    _t_sha, _t_size = sha256_file(TARGET_TEST)
    _e_sha, _e_size = sha256_file(TARGET_EXT)
    _s_sha, _s_size = sha256_file(TARGET_SAMPLER)

    # §1 (:81-82/:88/:94)：四件指纹/字节数与参照值严格吻合
    check("§1:81 _w5_test.py SHA256 严格吻合", _t_sha == REF_SHA256["_w5_test.py"])
    check("§1:82 _w5_test.py 字节数严格吻合", _t_size == REF_SIZE["_w5_test.py"])
    check("§1:88 扩展件 SHA256 严格吻合", _e_sha == REF_SHA256["qc151_trip.harness8_v4_ext.py"])
    check("§1:94 采样件 SHA256 严格吻合", _s_sha == REF_SHA256["frame_edge_sampler.py"])

    # §2 (:110-112)：原版单测重跑 EXIT=0 / 6 条全 PASS / 最终 PASS 标识
    check("§2:110 原版单测重跑 EXIT=0", "进程退出码 (EXIT_CODE): 0" in _out)
    check("§2:111 原版单测 6 用例全通过", "总计: 6 用例, 通过: 6, 失败: 0" in _out)
    check("§2:112 原版单测最终判定 PASS", "最终判定: PASS (EXIT=0)" in _out)

    # §3 (:127-128/:133/:138/:145)：用例 2 断言强度，逐字复用原件同一子串比较
    _eq = "assert total_extra_reads == expected_edges * 5" in _src
    _le = "total_extra_reads <=" in _src
    check("§3:127 用例 2 含严格等式断言", _eq)
    check("§3:128 用例 2 无放宽 <= 断言", not _le)
    check("§3:133 追加帧号读等式断言在场",
          "assert extra_frame_reads == expected_edges * 1" in _src)
    for _va in ["VA_GEN_STAMP", "VA_THREAT_CALLS", "VA_DIRTY_RECT", "VA_BULLET"]:
        check("§3:138 %s 严格等式断言在场" % _va,
              ("assert call_counts[%s] == expected_edges" % _va) in _src)
    check("§3:145 复用模式双 5 读断言在场",
          "assert len(order_log2) == 5" in _src
          and 'assert sample_reuse["reads_per_sample"] == 5' in _src)

    # §4 (:162)：时间戳全序链两段均在场
    _ts1 = 'assert ts["f_pre"] <= ts["segment_start"] <= ts["gen_stamp"] <= ts["threat_calls"]'
    _ts2 = '<= ts["dirty_rect_count"] <= ts["bullet_count"] <= ts["f_post_start"] <= ts["segment_end"]'
    check("§4:162 时间戳全序链两段在场", _ts1 in _src and _ts2 in _src)

    # §5 (:199/:221/:243)：三处注入替换确曾成功（原件文本中三句替换前片段仍在）
    _inj_a = ("if reuse:\n"
              "        # 复用前读：不再调 reader(FRAME_VA)，也不再取新 clock() 当前锚\n"
              '        rec["f_pre"] = f_pre')
    _inj_b = 'rec["ts"]["f_pre"] = t_pre'
    _inj_c = ("if reuse:\n"
              '        rec["ts"]["segment_start"] = clock()')
    check("§5:199 反例 A 注入替换成功", _inj_a in _sampler_src)
    check("§5:221 反例 B 注入替换成功", _inj_b in _sampler_src)
    check("§5:243 反例 C 注入替换成功", _inj_c in _sampler_src)
    # §5 (:209-210/:231-232/:253-254)：三个反例的 FAIL / AssertionError / 精准报错。
    # 原件 :204/:226/:248 把各退出码打印成 "反例 X 退出码: {rc} (预期 != 0)"，
    # :206-208/:228-230/:250-252 把 proc.stdout 中带 AssertionError/FAIL/
    # 用例执行异常 的行逐行 log 出来；故按 "--- 反例实验 X:" 分段即可逐字还原
    # 每个 assert 的同一条件：rc != 0 对应 :209/:231/:253；段内 "AssertionError"
    # 对应 :210/:254；B 段精准报错串对应 :232（只在 proc_b 的断言失败行出现）。
    _a = _out.find("--- 反例实验 A:")
    _b = _out.find("--- 反例实验 B:")
    _c = _out.find("--- 反例实验 C:")
    _z = _out.find(">> 临时沙盒清理完成")
    if _z < 0:
        _z = len(_out)
    _sec_a, _sec_b, _sec_c = _out[_a:_b], _out[_b:_c], _out[_c:_z]

    def _rc(sec, tag):
        key = "反例 %s 退出码: " % tag
        i = sec.find(key)
        if i < 0:
            return None
        v = sec[i + len(key):].split(" ", 1)[0]
        return int(v) if v.lstrip("-").isdigit() else None
    _rc_a, _rc_b, _rc_c = _rc(_sec_a, "A"), _rc(_sec_b, "B"), _rc(_sec_c, "C")
    check("§5:209 反例 A 单测 FAIL (EXIT!=0)", _rc_a is not None and _rc_a != 0)
    check("§5:210 反例 A 抛 AssertionError", "AssertionError" in _sec_a)
    check("§5:231 反例 B 单测 FAIL (EXIT!=0)", _rc_b is not None and _rc_b != 0)
    check("§5:232 反例 B 精准报 f_pre 时刻冒充", "f_pre 时刻必须等于外层读前锚" in _sec_b)
    check("§5:253 反例 C 单测 FAIL (EXIT!=0)", _rc_c is not None and _rc_c != 0)
    check("§5:254 反例 C 抛 AssertionError", "AssertionError" in _sec_c)

    # §6 (:273-275)：三件后验 SHA256 零漂移，与 §1 同一实算值
    check("§6:273 TARGET_TEST 后验 SHA256 零漂移", _t_sha == REF_SHA256["_w5_test.py"])
    check("§6:274 TARGET_EXT 后验 SHA256 零漂移", _e_sha == REF_SHA256["qc151_trip.harness8_v4_ext.py"])
    check("§6:275 TARGET_SAMPLER 后验 SHA256 零漂移", _s_sha == REF_SHA256["frame_edge_sampler.py"])

    print("核验结论: " + ("ALL PASS" if ok else "FAIL"))
    raise SystemExit(0 if ok else 1)
