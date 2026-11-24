#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_r4_independent_check.py - 独立复核员·R4 独立复核探针
全量独立核验 R4 回件中的各项物理量、判据与反例敏感性。
不修改任何既有文件，输出写在 reviews/ 目录内。
"""

import os
import sys
import hashlib
import difflib

REPO_ROOT = r"D:/Project/ra2-campaign-forge"
MOTHER_PATH = os.path.join(REPO_ROOT, "lead", "goal1_harness8_20261031", "qc151_trip.harness8_v4.py")
EXT_PATH = os.path.join(REPO_ROOT, "lead", "re_line_20261105", "W5_HARNESS_EXT", "qc151_trip.harness8_v4_ext.py")
R4_PROBE_PATH = os.path.join(REPO_ROOT, "lead", "re_line_20261105", "V6_V3_REVIEW", "_v6_r4.py")
R4_OUT_PATH = os.path.join(REPO_ROOT, "lead", "re_line_20261105", "V6_V3_REVIEW", "_v6_r4_out.txt")
W5_DIFF_PATH = os.path.join(REPO_ROOT, "lead", "re_line_20261105", "W5_HARNESS_EXT", "_w5_diff_proof.py")
W5_OUT_PATH = os.path.join(REPO_ROOT, "lead", "re_line_20261105", "W5_HARNESS_EXT", "_w5_diff_proof_out.txt")

PROHIBITED_TERMS = [
    "WriteProcessMemory",
    "CreateRemoteThread",
    "SuspendThread",
    "MiniDumpWriteDump",
    "StackWalk",
    "SetWindowsHookEx",
]

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def strip_w5ext_blocks(raw_bytes: bytes):
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
    print("=" * 80)
    print("独立复核员·R4: 独立复核探针执行")
    print("=" * 80)

    # 1. 独立计算物理量
    print("[1] 独立物理量测量")
    with open(MOTHER_PATH, "rb") as f:
        mother_bytes = f.read()
    with open(EXT_PATH, "rb") as f:
        ext_bytes = f.read()

    m_sha = sha256_bytes(mother_bytes)
    m_sz = len(mother_bytes)
    m_lines = mother_bytes.split(b"\n")
    m_lc = len(m_lines)

    e_sha = sha256_bytes(ext_bytes)
    e_sz = len(ext_bytes)
    e_lines = ext_bytes.split(b"\n")
    e_lc = len(e_lines)

    print(f"  母本: SHA256={m_sha}, 字节数={m_sz}, 行数={m_lc}")
    print(f"  副本: SHA256={e_sha}, 字节数={e_sz}, 行数={e_lc}")

    # 2. 删块即还原检验
    print("\n[2] 删 8 块即还原独立验证")
    restored_bytes, blocks = strip_w5ext_blocks(ext_bytes)
    r_sha = sha256_bytes(restored_bytes)
    r_sz = len(restored_bytes)
    total_block_lines = sum(b[2] for b in blocks)

    print(f"  识别插入块数: {len(blocks)}")
    for i, (s, e, cnt, content) in enumerate(blocks, start=1):
        first_line = content.split("\n")[0].strip()
        last_line = content.split("\n")[-1].strip()
        print(f"    块 #{i}: L{s}~L{e} ({cnt} 行) [{first_line} ... {last_line}]")
    print(f"  插入块总行数: {total_block_lines}")
    print(f"  删块后尺寸: {r_sz} (母本={m_sz})")
    print(f"  删块后 SHA256: {r_sha}")
    print(f"  逐字节完全相同: {restored_bytes == mother_bytes}")
    print(f"  删块还原 PASS: {restored_bytes == mother_bytes and r_sha == m_sha and len(blocks) == 8 and total_block_lines == 233}")

    # 3. 改动面清单
    print("\n[3] 改动面清单 (SequenceMatcher) 独立验证")
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
            print(f"    [INSERT] 副本 L{j1+1}~L{j2} (母本 L{i1} 后插入 {cnt} 行)")
        elif tag == "delete":
            cnt = i2 - i1
            deleted += cnt
            print(f"    [DELETE] 母本 L{i1+1}~L{i2} 被删除 ({cnt} 行)")
        elif tag == "replace":
            c_del = i2 - i1
            c_add = j2 - j1
            modified += max(c_del, c_add)
            print(f"    [REPLACE] 母本 L{i1+1}~L{i2} 替换为副本 L{j1+1}~L{j2}")

    print(f"  改动面统计: 新增={added}, 删除={deleted}, 修改={modified}")
    print(f"  改动面 PASS: {added == 233 and deleted == 0 and modified == 0}")

    # 4. 禁止面 API 独立扫描
    print("\n[4] 禁止面 API 独立扫描")
    m_txt = mother_bytes.decode("utf-8", errors="replace")
    e_txt = ext_bytes.decode("utf-8", errors="replace")
    api_pass = True
    for term in PROHIBITED_TERMS:
        mc = m_txt.count(term)
        ec = e_txt.count(term)
        diff = ec - mc
        print(f"    - {term:22s}: 母本={mc:2d}, 副本={ec:2d}, 差值={diff:+d}")
        if diff != 0:
            api_pass = False
    print(f"  禁止面扫描 PASS: {api_pass}")

    # 5. 反例敏感性验证
    print("\n[5] 反例与篡改敏感性独立验证")
    # 5.1 篡改母本区 1 字节
    tampered_1 = bytearray(ext_bytes)
    tampered_1[100] = (tampered_1[100] + 1) % 256
    r_t1, _ = strip_w5ext_blocks(bytes(tampered_1))
    t1_pass = (sha256_bytes(r_t1) != m_sha)
    print(f"    反例 1 (母本区单字节篡改): 拦截成功={t1_pass}")

    # 5.2 块内注入禁止词
    tampered_2 = ext_bytes.replace(b"# >>> W5EXT-BEGIN imports", b"# >>> W5EXT-BEGIN imports\n# WriteProcessMemory\n")
    t2_pass = (tampered_2.decode("utf-8", errors="replace").count("WriteProcessMemory") - mc > 0)
    print(f"    反例 2 (块内注入禁止词): 拦截成功={t2_pass}")

    # 5.3 破坏定界符闭合性
    tampered_3 = ext_bytes.replace(b"# <<< W5EXT-END imports", b"# CORRUPTED_DELIMITER")
    r_t3, b_t3 = strip_w5ext_blocks(tampered_3)
    t3_pass = (len(b_t3) != 8 or sha256_bytes(r_t3) != m_sha)
    print(f"    反例 3 (破坏块定界符): 拦截成功={t3_pass}")

    # 6. R4 回件代码与落盘真实性核验
    print("\n[6] R4 探针代码与落盘输出核验")
    with open(R4_OUT_PATH, "r", encoding="utf-8") as f:
        r4_out_content = f.read()
    
    # 检查落盘文件中的关键字符串
    has_m_sha = m_sha in r4_out_content
    has_e_sha = e_sha in r4_out_content
    has_blocks = "识别插入块总数: 8" in r4_out_content
    has_233 = "改动统计: 新增 233 行, 删除 0 行, 修改 0 行" in r4_out_content
    has_zero_diff = "差异=+0" in r4_out_content
    has_pass = "总复核结论: CONFIRMED (PASS)" in r4_out_content
    print(f"  _v6_r4_out.txt 包含母本 SHA: {has_m_sha}")
    print(f"  _v6_r4_out.txt 包含副本 SHA: {has_e_sha}")
    print(f"  _v6_r4_out.txt 包含 8 块识别: {has_blocks}")
    print(f"  _v6_r4_out.txt 包含 233 行新增/0删/0改: {has_233}")
    print(f"  _v6_r4_out.txt 包含禁止词差值+0: {has_zero_diff}")
    print(f"  _v6_r4_out.txt 包含 CONFIRMED 判定: {has_pass}")

    # 检查 R4 是否真算 SHA256 还是仅比较常量
    with open(R4_PROBE_PATH, "r", encoding="utf-8") as f:
        r4_probe_code = f.read()
    genuine_calc = ("sha256_b(ext_b)" in r4_probe_code and 
                    "with open(EXT_PATH, \"rb\") as f:" in r4_probe_code and
                    "ext_b = f.read()" in r4_probe_code)
    print(f"  R4 探针是否真有从磁盘读取并动态哈希逻辑: {genuine_calc}")

    all_ok = (m_sha == "38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8" and
              e_sha == "5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161" and
              restored_bytes == mother_bytes and
              added == 233 and deleted == 0 and modified == 0 and
              api_pass and t1_pass and t2_pass and t3_pass and genuine_calc)

    print("\n" + "=" * 80)
    print(f"独立复核总结论: {'CONFIRMED (PASS)' if all_ok else 'REFUTED (FAIL)'}")
    print("=" * 80)

if __name__ == "__main__":
    main()
