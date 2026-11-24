#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_v6_r4.py - V6_V3_REVIEW R4 独立复核探针
复核目标: W5 扩项副本 (qc151_trip.harness8_v4_ext.py) 在 D-21 裁 A 后的 V3 状态
验证项:
  1. 删 8 块后 SHA256 仍等于母本 (38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8)
  2. 新增行数是否为 233、删除 0、修改 0
  3. 六个禁止面 API 出现次数是否与母本逐项相同
  4. 反例与篡改敏感性检验 (验证门禁非空跑)
"""

import os
import sys
import hashlib
import difflib
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))

MOTHER_PATH = os.path.join(REPO_ROOT, "lead", "goal1_harness8_20261031", "qc151_trip.harness8_v4.py")
EXT_PATH = os.path.join(REPO_ROOT, "lead", "re_line_20261105", "W5_HARNESS_EXT", "qc151_trip.harness8_v4_ext.py")
OUT_PATH = os.path.join(BASE_DIR, "_v6_r4_out.txt")

EXPECTED_MOTHER_SHA256 = "38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8"
EXPECTED_MOTHER_SIZE = 489502
EXPECTED_EXT_SHA256 = "5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161"
EXPECTED_EXT_SIZE = 499047

PROHIBITED_TERMS = [
    "WriteProcessMemory",
    "CreateRemoteThread",
    "SuspendThread",
    "MiniDumpWriteDump",
    "StackWalk",
    "SetWindowsHookEx",
]

def sha256_b(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def strip_blocks(raw_bytes: bytes) -> tuple[bytes, list[tuple[int, int, int, str]]]:
    lines = raw_bytes.split(b"\n")
    in_block = False
    restored = []
    blocks = []
    curr_lines = []
    start_idx = -1

    for idx, line in enumerate(lines, start=1):
        if b"W5EXT-BEGIN" in line:
            in_block = True
            start_idx = idx
            curr_lines = [line.decode("utf-8", errors="replace")]
            continue
        if b"W5EXT-END" in line:
            in_block = False
            curr_lines.append(line.decode("utf-8", errors="replace"))
            blocks.append((start_idx, idx, len(curr_lines), "\n".join(curr_lines)))
            curr_lines = []
            continue
        if in_block:
            curr_lines.append(line.decode("utf-8", errors="replace"))
        else:
            restored.append(line)

    return b"\n".join(restored), blocks

def main():
    lines_out = []
    def log(msg=""):
        lines_out.append(msg)
        print(msg)

    log("=" * 80)
    log("V6_V3_REVIEW R4: 改动面与禁止面独立复核探针")
    log(f"执行时刻: {datetime.datetime.now().isoformat()}")
    log("=" * 80)
    log(f"母本路径: {MOTHER_PATH}")
    log(f"副本路径: {EXT_PATH}")
    log("-" * 80)

    # 1. 基础物理量测量
    with open(MOTHER_PATH, "rb") as f:
        mother_b = f.read()
    with open(EXT_PATH, "rb") as f:
        ext_b = f.read()

    m_sha = sha256_b(mother_b)
    m_size = len(mother_b)
    m_lines = mother_b.split(b"\n")
    m_line_count = len(m_lines)

    e_sha = sha256_b(ext_b)
    e_size = len(ext_b)
    e_lines = ext_b.split(b"\n")
    e_line_count = len(e_lines)

    log(f"母本实测 SHA256: {m_sha}")
    log(f"母本实测 字节数:  {m_size} (预期: {EXPECTED_MOTHER_SIZE})")
    log(f"母本实测 行数:    {m_line_count}")
    log(f"副本实测 SHA256: {e_sha}")
    log(f"副本实测 字节数:  {e_size} (预期: {EXPECTED_EXT_SIZE})")
    log(f"副本实测 行数:    {e_line_count}")

    pass_base = (m_sha == EXPECTED_MOTHER_SHA256 and m_size == EXPECTED_MOTHER_SIZE and
                 e_sha == EXPECTED_EXT_SHA256 and e_size == EXPECTED_EXT_SIZE)
    log(f">> 基础物理量核对: {'PASS' if pass_base else 'FAIL'}")
    log("-" * 80)

    # 2. 删块即还原检验
    log("[检验 1: 删块即还原 (8 块)]")
    restored_b, blocks = strip_blocks(ext_b)
    r_sha = sha256_b(restored_b)
    r_size = len(restored_b)

    log(f"识别插入块总数: {len(blocks)} (预期: 8)")
    total_block_lines = 0
    for idx, (s, e, count, content) in enumerate(blocks, start=1):
        total_block_lines += count
        first_line = content.split("\n")[0].strip()
        log(f"  块 #{idx}: 行 {s:4d} ~ {e:4d} (共 {count:2d} 行) -> {first_line}")

    log(f"插入块总行数: {total_block_lines} 行 (预期: 233 行)")
    log(f"删块后字节数: {r_size} (母本: {m_size})")
    log(f"删块后 SHA256: {r_sha}")
    log(f"母本   SHA256: {m_sha}")

    pass_strip = (len(blocks) == 8 and total_block_lines == 233 and
                  r_size == m_size and r_sha == m_sha and restored_b == mother_b)
    log(f">> 检验 1 判定: {'PASS' if pass_strip else 'FAIL'}")
    log("-" * 80)

    # 3. 改动面清单检验 (difflib SequenceMatcher)
    log("[检验 2: 改动面清单 (新增 233 / 删除 0 / 修改 0)]")
    m_str_lines = [l.decode("utf-8", errors="replace") + "\n" for l in m_lines]
    e_str_lines = [l.decode("utf-8", errors="replace") + "\n" for l in e_lines]

    matcher = difflib.SequenceMatcher(None, m_str_lines, e_str_lines)
    opcodes = matcher.get_opcodes()

    added = 0
    deleted = 0
    modified = 0

    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            continue
        elif tag == "insert":
            cnt = j2 - j1
            added += cnt
            log(f"  [INSERT] 副本行 {j1+1}~{j2} (母本行 {i1} 后插入 {cnt} 行)")
        elif tag == "delete":
            cnt = i2 - i1
            deleted += cnt
            log(f"  [DELETE] 母本行 {i1+1}~{i2} 被删除 ({cnt} 行)!")
        elif tag == "replace":
            c_del = i2 - i1
            c_add = j2 - j1
            modified += max(c_del, c_add)
            log(f"  [REPLACE] 母本行 {i1+1}~{i2} 替换为副本行 {j1+1}~{j2}!")

    log(f"改动统计: 新增 {added} 行, 删除 {deleted} 行, 修改 {modified} 行")
    pass_diff = (added == 233 and deleted == 0 and modified == 0)
    log(f">> 检验 2 判定: {'PASS' if pass_diff else 'FAIL'}")
    log("-" * 80)

    # 4. 禁止面 API 扫描
    log("[检验 3: 六个禁止面 API 逐项同数扫描]")
    m_txt = mother_b.decode("utf-8", errors="replace")
    e_txt = ext_b.decode("utf-8", errors="replace")

    pass_prohibited = True
    for term in PROHIBITED_TERMS:
        m_cnt = m_txt.count(term)
        e_cnt = e_txt.count(term)
        diff = e_cnt - m_cnt
        status = "OK (+0)" if diff == 0 else f"FAIL ({diff:+d})"
        log(f"  - {term:22s}: 母本={m_cnt:2d}, 副本={e_cnt:2d}, 差异={diff:+d} [{status}]")
        if diff != 0:
            pass_prohibited = False

    log(f">> 检验 3 判定: {'PASS' if pass_prohibited else 'FAIL'}")
    log("-" * 80)

    # 5. 反例与篡改敏感性检验
    log("[检验 4: 反例与篡改敏感性检验 (验证非空跑)]")
    # 5.1 篡改母本已有行: 模拟在副本母本区改动 1 字节
    tampered_1 = bytearray(ext_b)
    tampered_1[10] = (tampered_1[10] + 1) % 256
    r_tampered_1, _ = strip_blocks(bytes(tampered_1))
    t1_pass = (sha256_b(r_tampered_1) != m_sha)
    log(f"  - 篡改母本区 1 字节: 删块后 SHA256 判定失败 (正确拦截: {t1_pass})")

    # 5.2 篡改禁止词: 模拟在副本块内注入 1 个 WriteProcessMemory
    tampered_2 = ext_b.replace(b"# >>> W5EXT-BEGIN imports", b"# >>> W5EXT-BEGIN imports\n# WriteProcessMemory\n")
    t2_m_cnt = m_txt.count("WriteProcessMemory")
    t2_e_cnt = tampered_2.decode("utf-8", errors="replace").count("WriteProcessMemory")
    t2_pass = (t2_e_cnt - t2_m_cnt == 1)
    log(f"  - 注入禁止面 API: 差异检出为 +1 (正确拦截: {t2_pass})")

    # 5.3 篡改块边界: 模拟漏掉一个 END
    tampered_3 = ext_b.replace(b"# <<< W5EXT-END imports", b"# INVALID_DELIMITER")
    r_tampered_3, b_tampered_3 = strip_blocks(tampered_3)
    t3_pass = (len(b_tampered_3) != 8 or sha256_b(r_tampered_3) != m_sha)
    log(f"  - 破坏块定界符: 识别块数/还原校验失败 (正确拦截: {t3_pass})")

    pass_tamper = t1_pass and t2_pass and t3_pass
    log(f">> 检验 4 判定: {'PASS' if pass_tamper else 'FAIL'}")
    log("=" * 80)

    all_pass = pass_base and pass_strip and pass_diff and pass_prohibited and pass_tamper
    log(f"总复核结论: {'CONFIRMED (PASS)' if all_pass else 'REFUTED (FAIL)'}")
    log("=" * 80)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_out) + "\n")

    return all_pass

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
