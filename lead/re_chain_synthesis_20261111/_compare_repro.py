#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_compare_repro.py — 复现门（第一道硬门）逐项核验与比对脚本。

按任务 B′ 规则执行：
1. 校验靶件 ra2bench/gamemd.exe sha256 与文件大小。
2. 逐一比对 6 个探针目录重跑生成物与原始基线文件（.txt / .json），检查哈希与 JSON 树结构。
3. 检查重跑 stdout 落盘文件（_repro_*.txt）。
4. 产出结构化比对结果：_compare_repro_out.txt 与 _compare_repro_out.json。
"""
import sys
sys.dont_write_bytecode = True

import os
import json
import hashlib
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
EXE = os.path.join(REPO, "ra2bench", "gamemd.exe")
EXPECTED_EXE_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
EXPECTED_EXE_SIZE = 4825360

PROBES = [
    {
        "id": "PROBE_1",
        "dir": "re_crashwriter_static_20261110",
        "script": "_cw_disasm.py",
        "repro_stdout": "_repro_cw_disasm.txt",
        "outputs": ["_cw_disasm_out.txt", "_cw_disasm_out.json"]
    },
    {
        "id": "PROBE_2",
        "dir": "slot2_fullscan_20261111",
        "script": "_sf_scan.py",
        "repro_stdout": "_repro_sf_scan.txt",
        "outputs": ["_sf_scan_out.txt", "_sf_scan_out.json"]
    },
    {
        "id": "PROBE_3",
        "dir": "playerctrl_semantics_20261111",
        "script": "_ps_disasm.py",
        "repro_stdout": "_repro_ps_disasm.txt",
        "outputs": ["_ps_disasm_out.txt", "_ps_disasm_out.json"]
    },
    {
        "id": "PROBE_4A",
        "dir": "re_orphan_owners_20261110",
        "script": "_oo_map.py",
        "repro_stdout": "_repro_oo_map.txt",
        "outputs": ["_oo_map_out.txt", "_oo_map_out.json"]
    },
    {
        "id": "PROBE_4B",
        "dir": "re_orphan_owners_20261110",
        "script": "_oo_disasm.py",
        "repro_stdout": "_repro_oo_disasm.txt",
        "outputs": ["_oo_disasm_out.txt", "_oo_disasm_out.json"]
    },
    {
        "id": "PROBE_5",
        "dir": "re_map_preset_decode_20261110",
        "script": "_md_parse.py",
        "repro_stdout": "_repro_md_parse.txt",
        "outputs": ["_md_parse_out.txt", "_md_parse_out.json"]
    },
    {
        "id": "PROBE_6",
        "dir": "re_loadbench_diff_20261110",
        "script": "_ld_diff.py",
        "repro_stdout": "_repro_ld_diff.txt",
        "outputs": ["_ld_diff_out.txt", "_ld_diff_out.json"]
    }
]

def hash_file(p):
    with open(p, "rb") as f:
        data = f.read()
    return len(data), hashlib.sha256(data).hexdigest()

def diff_json(j1, j2, prefix=""):
    diffs = []
    if type(j1) != type(j2):
        return [f"{prefix}: type mismatch {type(j1).__name__} vs {type(j2).__name__}"]
    if isinstance(j1, dict):
        all_keys = sorted(set(j1.keys()) | set(j2.keys()))
        for k in all_keys:
            if k not in j1:
                diffs.append(f"{prefix}.{k}: missing in rerun")
            elif k not in j2:
                diffs.append(f"{prefix}.{k}: missing in baseline")
            else:
                diffs.extend(diff_json(j1[k], j2[k], f"{prefix}.{k}" if prefix else k))
    elif isinstance(j1, list):
        if len(j1) != len(j2):
            diffs.append(f"{prefix}: length mismatch {len(j1)} vs {len(j2)}")
        else:
            for idx, (v1, v2) in enumerate(zip(j1, j2)):
                diffs.extend(diff_json(v1, v2, f"{prefix}[{idx}]"))
    else:
        if j1 != j2:
            diffs.append(f"{prefix}: value mismatch {j1!r} vs {j2!r}")
    return diffs

def main():
    lines = []
    def p(s=""):
        lines.append(s)
        print(s)

    p("=" * 80)
    p("任务 B′：六探针合流复现门比对判定报告 (_compare_repro.py)")
    p("=" * 80)

    # 1. 靶件自核
    p("\n[1] 靶件自核 (ra2bench/gamemd.exe)")
    exe_size, exe_sha = hash_file(EXE)
    p(f"  路径: {EXE}")
    p(f"  大小: {exe_size} B (期望 {EXPECTED_EXE_SIZE} B)")
    p(f"  SHA-256: {exe_sha}")
    p(f"  期望 SHA-256: {EXPECTED_EXE_SHA}")
    if exe_size != EXPECTED_EXE_SIZE or exe_sha != EXPECTED_EXE_SHA:
        p("  [FATAL] 靶件校验不符，硬门终止！")
        sys.exit(1)
    p("  [PASS] 靶件大小与哈希完全一致。\n")

    # 2. 逐探针比对
    p("[2] 六探针重跑逐项比对")
    bak_root = os.path.join(HERE, "baseline_backup")
    lead_root = os.path.join(REPO, "lead")

    results = OrderedDict()
    total_matches = 0
    total_mismatches = 0

    for probe in PROBES:
        pid = probe["id"]
        dname = probe["dir"]
        script = probe["script"]
        stdout_file = probe["repro_stdout"]
        stdout_path = os.path.join(HERE, stdout_file)
        
        stdout_size, stdout_sha = hash_file(stdout_path) if os.path.exists(stdout_path) else (0, None)
        p("-" * 80)
        p(f"◆ {pid} | 目录: lead/{dname} | 脚本: {script}")
        p(f"  重跑 stdout: {stdout_file} ({stdout_size} B, sha256={stdout_sha[:16] if stdout_sha else 'MISSING'}...)")

        probe_rec = {
            "id": pid,
            "dir": dname,
            "script": script,
            "repro_stdout": {
                "file": stdout_file,
                "size": stdout_size,
                "sha256": stdout_sha
            },
            "files": []
        }

        for out_name in probe["outputs"]:
            current_path = os.path.join(lead_root, dname, out_name)
            bak_path = os.path.join(bak_root, dname, out_name)

            if not os.path.exists(current_path) or not os.path.exists(bak_path):
                p(f"  [ERROR] 文件缺失: {out_name}")
                total_mismatches += 1
                probe_rec["files"].append({
                    "name": out_name,
                    "verdict": "MISSING",
                    "diffs": ["file does not exist"]
                })
                continue

            sz_cur, sha_cur = hash_file(current_path)
            sz_bak, sha_bak = hash_file(bak_path)

            file_verdict = "MATCH"
            diffs = []

            if sz_cur != sz_bak or sha_cur != sha_bak:
                file_verdict = "MISMATCH"
                diffs.append(f"sha256: cur {sha_cur} vs bak {sha_bak}, size: cur {sz_cur} vs bak {sz_bak}")
                total_mismatches += 1
            else:
                total_matches += 1

            json_status = "N/A"
            if out_name.endswith(".json"):
                with open(current_path, "r", encoding="utf-8") as f1, open(bak_path, "r", encoding="utf-8") as f2:
                    j_cur = json.load(f1)
                    j_bak = json.load(f2)
                j_diffs = diff_json(j_cur, j_bak)
                if j_diffs:
                    file_verdict = "MISMATCH"
                    diffs.extend(j_diffs)
                    json_status = f"MISMATCH ({len(j_diffs)} diffs)"
                else:
                    json_status = "EXACT_MATCH"

            p(f"  [{file_verdict}] {out_name:<20s} 大小: {sz_cur:10d} B | SHA: {sha_cur[:16]}... | JSON: {json_status}")
            if diffs:
                for d in diffs[:10]:
                    p(f"    -> DIFF: {d}")

            probe_rec["files"].append({
                "name": out_name,
                "verdict": file_verdict,
                "size_current": sz_cur,
                "size_baseline": sz_bak,
                "sha256_current": sha_cur,
                "sha256_baseline": sha_bak,
                "json_status": json_status,
                "diffs": diffs
            })

        results[pid] = probe_rec

    p("=" * 80)
    p(f"[3] 复现门最终裁定: MATCH={total_matches}, MISMATCH={total_mismatches}")
    if total_mismatches == 0:
        p("  >>> 判定: 全部重跑生成物与基线 100% 咬合无偏差，复现门通过 (PASS) <<<")
    else:
        p("  >>> 判定: 存在不一致项，复现门失败 (FAIL) <<<")
    p("=" * 80)

    out_txt = os.path.join(HERE, "_compare_repro_out.txt")
    out_json = os.path.join(HERE, "_compare_repro_out.json")

    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "target": {
                "path": EXE,
                "size": exe_size,
                "sha256": exe_sha,
                "expected_sha256": EXPECTED_EXE_SHA
            },
            "summary": {
                "total_matches": total_matches,
                "total_mismatches": total_mismatches,
                "gate_status": "PASS" if total_mismatches == 0 else "FAIL"
            },
            "probes": results
        }, f, ensure_ascii=False, indent=2)

    print(f"\nWritten: {out_txt}")
    print(f"Written: {out_json}")

if __name__ == "__main__":
    main()
