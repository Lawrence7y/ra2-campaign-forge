#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_r3_independent_check.py · 独立复核员·R3 独立验证脚本
用于独立重跑并复核 R3 结论的真实性与严谨性
"""

import ast
import hashlib
import os
import re
import sys

def run_independent_checks():
    repo_root = r"D:\Project\ra2-campaign-forge"
    target_path = os.path.join(repo_root, "lead", "re_line_20261105", "W5_HARNESS_EXT", "qc151_trip.harness8_v4_ext.py")
    w5_dir = os.path.join(repo_root, "lead", "re_line_20261105", "W5_HARNESS_EXT")

    print("[CHECK 1] 独立物理量测算")
    with open(target_path, "rb") as f:
        content_bytes = f.read()
    
    sha256_actual = hashlib.sha256(content_bytes).hexdigest()
    size_actual = len(content_bytes)
    lines_actual = len(content_bytes.split(b"\n"))
    print(f"  SHA256: {sha256_actual}")
    print(f"  SIZE: {size_actual}")
    print(f"  LINES: {lines_actual}")

    # [CHECK 2] poll-span-hook 块内时序拓扑与参数传递分析
    print("\n[CHECK 2] 定界块提取与 AST 节点深度检验")
    text = content_bytes.decode("utf-8")
    lines = text.splitlines()

    # 验证定界符
    begin_marker = "# >>> W5EXT-BEGIN poll-span-hook"
    end_marker = "# <<< W5EXT-END poll-span-hook"
    begin_idx = None
    end_idx = None
    for i, line in enumerate(lines, 1):
        if begin_marker in line:
            begin_idx = i
        if end_marker in line:
            end_idx = i
            break
    print(f"  poll-span-hook 范围: L{begin_idx} ~ L{end_idx} (行数: {end_idx - begin_idx + 1 if begin_idx and end_idx else 0})")

    # 独立 AST 遍历
    tree = ast.parse(text, filename=target_path)
    
    all_calls = []
    all_read_sample_nodes = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # 检查函数名
            func_str = ast.unparse(node.func)
            if "read_sample" in func_str:
                all_calls.append(node)
        if isinstance(node, ast.Attribute) and node.attr == "read_sample":
            all_read_sample_nodes.append(node)

    print(f"  AST 找到 read_sample Call 节点数: {len(all_calls)}")
    print(f"  AST 找到 read_sample Attribute 节点数: {len(all_read_sample_nodes)}")

    for call in all_calls:
        print(f"    Call 定位: L{call.lineno}:{call.col_offset}")
        print(f"    调用表达式: {ast.unparse(call)}")
        print(f"    参数列表:")
        for idx, arg in enumerate(call.args):
            print(f"      arg[{idx}] = {ast.unparse(arg)}")
        for kw in call.keywords:
            print(f"      kw[{kw.arg}] = {ast.unparse(kw.value)}")

    # [CHECK 3] Grep 纯代码行与注释行
    print("\n[CHECK 3] Grep 文本全量核对")
    grep_results = []
    for i, line in enumerate(lines, 1):
        if "read_sample" in line:
            is_comm = line.strip().startswith("#")
            grep_results.append((i, is_comm, line.strip()))
            print(f"    L{i:4d} [{'COMMENT' if is_comm else 'CODE'}]: {line.strip()}")

    # [CHECK 4] W5_HARNESS_EXT 全量 Python 文件扫描
    print("\n[CHECK 4] 目录级文件调用核查")
    for fname in sorted(os.listdir(w5_dir)):
        if not fname.endswith(".py"):
            continue
        fpath = os.path.join(w5_dir, fname)
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            f_content = f.read()
        f_tree = ast.parse(f_content, filename=fpath)
        f_calls = []
        for n in ast.walk(f_tree):
            if isinstance(n, ast.Call) and "read_sample" in ast.unparse(n.func):
                f_calls.append(n)
        f_grep = [line.strip() for line in f_content.splitlines() if "read_sample" in line]
        print(f"  {fname}: AST Calls = {len(f_calls)}, Grep hits = {len(f_grep)}")
        for c in f_calls:
            print(f"    AST Call L{c.lineno}: {ast.unparse(c)}")

    print("\n[CHECK 5] 时序与依赖独立静态分析")
    # 检查 _w5_measure_poll_span 函数内部变量定义与赋值顺序
    # 寻找 def _w5_measure_poll_span
    func_node = None
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == "_w5_measure_poll_span":
            func_node = n
            break
    if func_node:
        print(f"  找到 _w5_measure_poll_span: L{func_node.lineno} ~ L{func_node.end_lineno}")
        # 提取 while 循环
        while_node = None
        for n in func_node.body:
            if isinstance(n, ast.While):
                while_node = n
                break
        if while_node:
            print(f"  找到 while 循环: L{while_node.lineno} ~ L{while_node.end_lineno}")
            for stmt in while_node.body:
                print(f"    语句 L{stmt.lineno}: {ast.unparse(stmt).splitlines()[0]}")

if __name__ == "__main__":
    run_independent_checks()
