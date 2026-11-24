#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_w5_diff_proof.py - Q2 改动面证明审计脚本
验证三件事：
1. 删块即还原：把 W5EXT-BEGIN..END 全部删掉后剩余内容与母本 harness8_v4.py 逐字节相等（SHA256 对照）。
2. 改动面清单：除块内新增外，母本原有行零改动（新增 N 行、删除 0、修改 0）。
3. 禁止面扫描：WriteProcessMemory / CreateRemoteThread / SuspendThread / MiniDumpWriteDump /
   StackWalk / SetWindowsHookEx 出现次数必须与母本相同（不能变多）。
"""

import os
import sys
import hashlib
import difflib
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))

MOTHER_PATH = os.path.join(REPO_ROOT, "lead", "goal1_harness8_20261031", "qc151_trip.harness8_v4.py")
EXT_PATH = os.path.join(BASE_DIR, "qc151_trip.harness8_v4_ext.py")
OUT_TXT_PATH = os.path.join(BASE_DIR, "_w5_diff_proof_out.txt")

PROHIBITED_TERMS = [
    "WriteProcessMemory",
    "CreateRemoteThread",
    "SuspendThread",
    "MiniDumpWriteDump",
    "StackWalk",
    "SetWindowsHookEx",
]

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def strip_w5ext_blocks(raw_bytes: bytes) -> tuple[bytes, list[tuple[int, int, str]]]:
    """
    Remove all blocks delimited by W5EXT-BEGIN and W5EXT-END.
    Returns (restored_bytes, list_of_blocks).
    Preserves exact byte line endings (LF).
    """
    lines = raw_bytes.split(b"\n")
    in_block = False
    restored = []
    blocks = []
    current_block_lines = []
    block_start_idx = -1

    for idx, line in enumerate(lines, start=1):
        if b"W5EXT-BEGIN" in line:
            in_block = True
            block_start_idx = idx
            current_block_lines = [line.decode("utf-8", errors="replace")]
            continue
        if b"W5EXT-END" in line:
            in_block = False
            current_block_lines.append(line.decode("utf-8", errors="replace"))
            blocks.append((block_start_idx, idx, "\n".join(current_block_lines)))
            current_block_lines = []
            continue
        if in_block:
            current_block_lines.append(line.decode("utf-8", errors="replace"))
        else:
            restored.append(line)

    restored_bytes = b"\n".join(restored)
    return restored_bytes, blocks

def run_diff_proof():
    lines_out = []
    def log(msg=""):
        lines_out.append(msg)
        print(msg)

    log("=" * 80)
    log("W5 改动面证明 (Q2) 机械验证")
    log("=" * 80)
    log(f"母本路径: {MOTHER_PATH}")
    log(f"副本路径: {EXT_PATH}")
    log("-" * 80)

    # 1. 检查母本存在性
    if not os.path.exists(MOTHER_PATH):
        log(f"[FATAL] 母本文件不存在: {MOTHER_PATH}")
        return False, "\n".join(lines_out)

    with open(MOTHER_PATH, "rb") as f:
        mother_bytes = f.read()

    mother_sha = sha256_bytes(mother_bytes)
    mother_size = len(mother_bytes)
    mother_lines = mother_bytes.split(b"\n")
    mother_line_count = len(mother_lines)

    log(f"母本字节数: {mother_size}")
    log(f"母本行数:   {mother_line_count}")
    log(f"母本 SHA256: {mother_sha}")

    # 母本基线禁止词扫描
    mother_text = mother_bytes.decode("utf-8", errors="replace")
    mother_prohibited_counts = {term: mother_text.count(term) for term in PROHIBITED_TERMS}
    log("母本禁止面 API 出现基线:")
    for term, cnt in mother_prohibited_counts.items():
        log(f"  - {term}: {cnt}")
    log("-" * 80)

    # 2. 检查副本存在性
    if not os.path.exists(EXT_PATH):
        log("[BLOCKING] Q1 副本文件尚未生成: qc151_trip.harness8_v4_ext.py 不存在！")
        log("根据任务书规定，不可代写副本，阻断等待 Q1 交付件。")
        log("=" * 80)
        log("结论: 阻断 (BLOCKING - PREREQUISITE MISSING)")
        log("=" * 80)
        return False, "\n".join(lines_out)

    with open(EXT_PATH, "rb") as f:
        ext_bytes = f.read()

    ext_sha = sha256_bytes(ext_bytes)
    ext_size = len(ext_bytes)
    ext_lines = ext_bytes.split(b"\n")
    ext_line_count = len(ext_lines)

    log(f"副本字节数: {ext_size}")
    log(f"副本行数:   {ext_line_count}")
    log(f"副本 SHA256: {ext_sha}")
    log("-" * 80)

    all_passed = True

    # -------------------------------------------------------------
    # 检验 1: 删块即还原 (逐字节比对)
    # -------------------------------------------------------------
    log("[检验 1: 删块即还原]")
    restored_bytes, blocks = strip_w5ext_blocks(ext_bytes)
    restored_sha = sha256_bytes(restored_bytes)
    restored_size = len(restored_bytes)

    log(f"识别到 W5EXT 插入块数量: {len(blocks)}")
    for b_idx, (start, end, content) in enumerate(blocks, start=1):
        b_lines = content.count("\n") + 1
        log(f"  块 #{b_idx}: 行 {start} ~ {end} (共 {b_lines} 行)")

    log(f"删块后字节数: {restored_size} (母本: {mother_size})")
    log(f"删块后 SHA256: {restored_sha}")
    log(f"母本   SHA256: {mother_sha}")

    if restored_sha == mother_sha and restored_bytes == mother_bytes:
        log(">> 检验 1 判定: PASS (删块后内容与母本逐字节完全一致)")
    else:
        log(">> 检验 1 判定: FAIL (删块后内容与母本存在字节差异)")
        all_passed = False

    log("-" * 80)

    # -------------------------------------------------------------
    # 检验 2: 改动面清单 (母本原有行零改动)
    # -------------------------------------------------------------
    log("[检验 2: 改动面清单]")
    mother_str_lines = [l.decode("utf-8", errors="replace") + "\n" for l in mother_lines]
    ext_str_lines = [l.decode("utf-8", errors="replace") + "\n" for l in ext_lines]

    matcher = difflib.SequenceMatcher(None, mother_str_lines, ext_str_lines)
    opcodes = matcher.get_opcodes()

    added_lines_count = 0
    deleted_lines_count = 0
    modified_lines_count = 0

    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            continue
        elif tag == "insert":
            cnt = j2 - j1
            added_lines_count += cnt
            log(f"  [INSERT] 副本第 {j1+1}~{j2} 行 (母本第 {i1} 行后插入 {cnt} 行)")
        elif tag == "delete":
            cnt = i2 - i1
            deleted_lines_count += cnt
            log(f"  [DELETE] 母本第 {i1+1}~{i2} 行在副本中被删除 ({cnt} 行)!")
        elif tag == "replace":
            cnt_del = i2 - i1
            cnt_add = j2 - j1
            modified_lines_count += max(cnt_del, cnt_add)
            log(f"  [REPLACE] 母本第 {i1+1}~{i2} 行被替换为副本第 {j1+1}~{j2} 行!")

    log(f"改动统计: 新增 {added_lines_count} 行, 删除 {deleted_lines_count} 行, 修改 {modified_lines_count} 行")

    if deleted_lines_count == 0 and modified_lines_count == 0 and added_lines_count > 0:
        log(f">> 检验 2 判定: PASS (母本原有行零改动，纯新增 {added_lines_count} 行)")
    else:
        log(f">> 检验 2 判定: FAIL (存在删除 {deleted_lines_count} 或修改 {modified_lines_count})")
        all_passed = False

    log("-" * 80)

    # -------------------------------------------------------------
    # 检验 3: 禁止面扫描 (高危 API 出现次数不增加)
    # -------------------------------------------------------------
    log("[检验 3: 禁止面扫描]")
    ext_text = ext_bytes.decode("utf-8", errors="replace")
    ext_prohibited_counts = {term: ext_text.count(term) for term in PROHIBITED_TERMS}

    prohibited_pass = True
    for term in PROHIBITED_TERMS:
        m_cnt = mother_prohibited_counts[term]
        e_cnt = ext_prohibited_counts[term]
        diff = e_cnt - m_cnt
        status = "OK" if diff == 0 else ("FAIL (+)" if diff > 0 else "DECREASED")
        log(f"  - {term:22s}: 母本={m_cnt:2d}, 副本={e_cnt:2d}, 差异={diff:+d} [{status}]")
        if diff > 0:
            prohibited_pass = False

    if prohibited_pass:
        log(">> 检验 3 判定: PASS (所有禁止面 API 出现次数均未增加)")
    else:
        log(">> 检验 3 判定: FAIL (存在禁止面 API 出现次数增加)")
        all_passed = False

    log("=" * 80)
    final_verdict = "PASS" if all_passed else "FAIL"
    log(f"最终判定: {final_verdict}")
    log("=" * 80)

    return all_passed, "\n".join(lines_out)

if __name__ == "__main__":
    success, output = run_diff_proof()
    with open(OUT_TXT_PATH, "w", encoding="utf-8") as f:
        f.write(output + "\n")
    sys.exit(0 if success else 1)
