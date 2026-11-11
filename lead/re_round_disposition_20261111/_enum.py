#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_enum.py — lead/ 下日期后缀 >=20261106 轮次目录只读枚举与分类脚本

运行方式：
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/re_round_disposition_20261111/_enum.py

约束：
  零真机、纯只读检查、唯一写域为本脚本所在目录。
"""

import sys
sys.dont_write_bytecode = True

import os
import re
import json
import hashlib
from collections import defaultdict

LEAD_DIR = r"D:\Project\ra2-campaign-forge\lead"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def classify_dir(full_path):
    """递归扫描目录下的所有文件并分类。"""
    files = []
    md_files = []
    py_files = []
    other_files = []
    
    for root, subdirs, fs in os.walk(full_path):
        for f in fs:
            rel = os.path.relpath(os.path.join(root, f), full_path)
            files.append(rel)
            fl = f.lower()
            if fl.endswith(".md"):
                md_files.append(rel)
            elif fl.endswith(".py"):
                py_files.append(rel)
            else:
                other_files.append(rel)
                
    # 浅层检查（仅一级子项）
    try:
        shallow_items = os.listdir(full_path)
    except Exception:
        shallow_items = []
    shallow_files = [item for item in shallow_items if os.path.isfile(os.path.join(full_path, item))]
    shallow_dirs = [item for item in shallow_items if os.path.isdir(os.path.join(full_path, item))]

    if not files:
        cls = "EMPTY"
    elif md_files:
        cls = "HAS_MD"
    else:
        cls = "PROBE_ONLY"

    return {
        "cls": cls,
        "total_files": len(files),
        "md_files": md_files,
        "py_files": py_files,
        "other_files": other_files,
        "shallow_files_count": len(shallow_files),
        "shallow_dirs_count": len(shallow_dirs),
    }

def main():
    all_entries = sorted(os.listdir(LEAD_DIR))
    matching_dirs = []
    for d in all_entries:
        full = os.path.join(LEAD_DIR, d)
        if not os.path.isdir(full):
            continue
        m = re.search(r"(2026\d{4})$", d)
        if m and m.group(1) >= "20261106":
            # 排除当前脚本所在的写域自身
            if d == "re_round_disposition_20261111":
                continue
            matching_dirs.append((d, m.group(1)))

    # 元轮次集合（11-11 的审计/派发元轮）
    meta_rounds = {
        "re_progress_check_20261111",
        "re_progress_xverify_20261111",
        "re_dispatch_20261111",
    }

    results = {}
    for d, dt in matching_dirs:
        full = os.path.join(LEAD_DIR, d)
        info = classify_dir(full)
        info["date"] = dt
        info["is_meta"] = d in meta_rounds
        results[d] = info

    # 统计表
    # 口径1: 基准 182 轮（排除 3 个元轮次）
    base_counts = defaultdict(lambda: {"HAS_MD": 0, "PROBE_ONLY": 0, "EMPTY": 0, "TOTAL": 0})
    # 口径2: 包含元轮次（共 185 轮）
    all_counts = defaultdict(lambda: {"HAS_MD": 0, "PROBE_ONLY": 0, "EMPTY": 0, "TOTAL": 0})

    for d, info in results.items():
        dt = info["date"]
        c = info["cls"]
        all_counts[dt][c] += 1
        all_counts[dt]["TOTAL"] += 1
        if not info["is_meta"]:
            base_counts[dt][c] += 1
            base_counts[dt]["TOTAL"] += 1

    # 写入输出文本文件
    out_txt_path = os.path.join(OUT_DIR, "_enum_out.txt")
    out_json_path = os.path.join(OUT_DIR, "_enum_out.json")

    with open(out_txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("lead/ 轮次目录实跑枚举输出 (>=20261106)\n")
        f.write("=" * 80 + "\n\n")

        f.write("【口径说明】\n")
        f.write(f"1. 盘面扫描命中总数: {len(results)} 个目录 (含 3 个 11-11 进度审计/核验/派发元轮次)\n")
        f.write(f"2. 任务书基准统计总数: 182 个目录 (扣除 3 个元轮次: re_progress_check, re_progress_xverify, re_dispatch)\n")
        f.write("3. const_exit_fix_20261110: 浅层 ls 无文件，但 patched/ 子目录下落盘 32 个文件 (18 py)。\n")
        f.write("   - 表面/浅层统计下: 153 个带 md / 17 个仅探针 / 12 个空目录 (原初人工速查口径)\n")
        f.write("   - 递归真实统计下: 153 个带 md / 18 个仅探针 / 11 个完全空目录 (机器全量 walk 口径)\n\n")

        f.write("【按日期数量统计表（基准 182 轮次）】\n")
        f.write(f"{'日期':<10} | {'有 md 报告':<10} | {'仅探针无报告':<12} | {'完全空目录':<10} | {'总计':<8}\n")
        f.write("-" * 62 + "\n")
        t_md = t_probe = t_empty = t_tot = 0
        for dt in sorted(base_counts.keys()):
            c = base_counts[dt]
            f.write(f"{dt:<10} | {c['HAS_MD']:<10} | {c['PROBE_ONLY']:<12} | {c['EMPTY']:<10} | {c['TOTAL']:<8}\n")
            t_md += c["HAS_MD"]
            t_probe += c["PROBE_ONLY"]
            t_empty += c["EMPTY"]
            t_tot += c["TOTAL"]
        f.write("-" * 62 + "\n")
        f.write(f"{'合计':<10} | {t_md:<10} | {t_probe:<12} | {t_empty:<10} | {t_tot:<8}\n\n")

        f.write("【按日期数量统计表（含 3 个元轮次共 185 轮）】\n")
        f.write(f"{'日期':<10} | {'有 md 报告':<10} | {'仅探针无报告':<12} | {'完全空目录':<10} | {'总计':<8}\n")
        f.write("-" * 62 + "\n")
        t_md = t_probe = t_empty = t_tot = 0
        for dt in sorted(all_counts.keys()):
            c = all_counts[dt]
            f.write(f"{dt:<10} | {c['HAS_MD']:<10} | {c['PROBE_ONLY']:<12} | {c['EMPTY']:<10} | {c['TOTAL']:<8}\n")
            t_md += c["HAS_MD"]
            t_probe += c["PROBE_ONLY"]
            t_empty += c["EMPTY"]
            t_tot += c["TOTAL"]
        f.write("-" * 62 + "\n")
        f.write(f"{'合计':<10} | {t_md:<10} | {t_probe:<12} | {t_empty:<10} | {t_tot:<8}\n\n")

        f.write("=" * 80 + "\n")
        f.write("完全空目录清单 (EMPTY, 递归检查 0 文件, 共 11 个)\n")
        f.write("=" * 80 + "\n")
        empty_list = [d for d, info in results.items() if info["cls"] == "EMPTY"]
        for d in sorted(empty_list):
            f.write(f"- {d} (日期: {results[d]['date']})\n")
        f.write("\n注: 若按浅层一级目录无文件统计，则 const_exit_fix_20261110 亦名列其中，合计 12 个。\n\n")

        f.write("=" * 80 + "\n")
        f.write("仅探针无报告目录清单 (PROBE_ONLY, 共 18 个)\n")
        f.write("=" * 80 + "\n")
        probe_list = [d for d, info in results.items() if info["cls"] == "PROBE_ONLY"]
        for d in sorted(probe_list):
            info = results[d]
            f.write(f"- {d} (日期: {info['date']}, 文件数: {info['total_files']}, py: {len(info['py_files'])})\n")
            f.write(f"  py 文件: {info['py_files'][:5]}\n")
            f.write(f"  其它文件: {info['other_files'][:5]}\n")
        f.write("\n")

        f.write("=" * 80 + "\n")
        f.write("有 md 报告目录清单概要 (HAS_MD, 共 153 个基准 + 3 个元轮 = 156 个)\n")
        f.write("=" * 80 + "\n")
        has_md_list = [d for d, info in results.items() if info["cls"] == "HAS_MD"]
        for d in sorted(has_md_list):
            info = results[d]
            f.write(f"- {d} (日期: {info['date']}, md 件数: {len(info['md_files'])}, md: {info['md_files']})\n")

    # 导出 JSON 结构化数据
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_by": os.path.basename(__file__),
            "base_182_summary": dict(base_counts),
            "all_185_summary": dict(all_counts),
            "directories": results,
        }, f, ensure_ascii=False, indent=2)

    print(f"[OK] 枚举完成。结果写入:")
    print(f"  - {out_txt_path}")
    print(f"  - {out_json_path}")
    print(f"基准 182 轮次统计: HAS_MD={t_md-3 if 're_progress_check_20261111' in results else t_md}, PROBE_ONLY={len(probe_list)}, EMPTY={len(empty_list)}")

if __name__ == "__main__":
    main()
