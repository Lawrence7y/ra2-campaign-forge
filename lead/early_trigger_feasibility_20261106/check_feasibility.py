#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_feasibility.py — 提前触发方案离线可行性论证确定性门禁脚本（只读，纯标准库）。

运行方式（在仓库根、隔离模式；传给解释器的参数为脚本自身路径或目标目录）：
    python -I -X utf8 lead/early_trigger_feasibility_20261106/check_feasibility.py lead/early_trigger_feasibility_20261106/check_feasibility.py

检查项：
1) lead/early_trigger_feasibility_20261106/EARLY_TRIGGER_FEASIBILITY.md /
   lead/early_trigger_feasibility_20261106/FEASIBILITY_STATS.json /
   lead/early_trigger_feasibility_20261106/_feasibility_probe.py /
   lead/early_trigger_feasibility_20261106/_feasibility_probe_out.txt /
   lead/early_trigger_feasibility_20261106/review/FEASIBILITY_REVIEW.md 都存在且非空；
2) 主交付含五节标题（Q1..Q5，按 TASK 原文）；
3) 主交付含 `n=` 或「样本」>= 5 次；
4) ★ 主交付不得出现「物理上做不到」「方案不可行」「已验证可行」（出现即 FAIL）；
5) lead/early_trigger_feasibility_20261106/FEASIBILITY_STATS.json 可解析、含 corpus/q1/q2/q3/q4/q5 六键；
6) q3.kTable 长度 == 3；q4.quotaTable 长度 == 3；
7) q5.verified == false（严格布尔假）；
8) 脚本自算：q2.coverageByDuration 每项 rate 与 capturableWithin50ms/total 一致（容差 0.001），
   total 为 0 的项跳过；
9) 反扫描：lead/early_trigger_feasibility_20261106/_feasibility_probe.py 不得出现
   ctypes / OpenProcess / ReadProcessMemory / MiniDump / SuspendThread / StackWalk；
10) lead/early_trigger_feasibility_20261106/review/FEASIBILITY_REVIEW.md 含六字段且
    checkedEveryRow/statsHaveN/noCherryPicking/q5MarkedUnverified/noForbiddenWording 均为 true。

退出码：
    0 = PASS
    1 = 内容不合格（逐条打印原因）
    2 = 文件缺失/为空/不可读

脚本只读，不修改或写入任何文件。
"""

from __future__ import annotations

import ast
import io
import json
from pathlib import Path
import re
import sys
import tokenize

# 防御性控制台 UTF-8 输出
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


def resolve_base_dir() -> tuple[Path, Path]:
    """解析交付件目录 BASE 与仓库根目录 REPO。"""
    if len(sys.argv) > 1 and sys.argv[1].strip():
        arg_path = Path(sys.argv[1]).resolve()
        if arg_path.is_file():
            base = arg_path.parent
        elif arg_path.is_dir():
            base = arg_path
        else:
            base = Path(__file__).resolve().parent
    else:
        base = Path(__file__).resolve().parent

    repo = Path.cwd().resolve()
    if not (repo / "lead").is_dir():
        repo = base.parent.parent
    return base, repo


def to_rel(p: Path, repo_root: Path) -> str:
    """转为相对于仓库根的 posix 路径字符串。"""
    try:
        return p.resolve().relative_to(repo_root.resolve()).as_posix()
    except Exception:
        return p.as_posix()


def main() -> int:
    base_dir, repo_root = resolve_base_dir()

    print("=" * 80)
    print("【提前触发方案可行性确定性门禁检查】")
    print(f"目标目录: {base_dir}")
    print(f"仓库根:   {repo_root}")
    print(f"执行参数: {sys.argv}")
    print("=" * 80)

    # =========================================================================
    # 检查项 1：五个交付件存在且非空（若有缺失/为空/不可读即 exit 2）
    # =========================================================================
    required_files = {
        "main_doc": base_dir / "EARLY_TRIGGER_FEASIBILITY.md",
        "stats_json": base_dir / "FEASIBILITY_STATS.json",
        "probe_py": base_dir / "_feasibility_probe.py",
        "probe_out": base_dir / "_feasibility_probe_out.txt",
        "review_doc": base_dir / "review" / "FEASIBILITY_REVIEW.md",
    }

    file_contents: dict[str, str] = {}
    missing_errors: list[str] = []

    for key, path in required_files.items():
        rel_str = to_rel(path, repo_root)
        if not path.is_file():
            missing_errors.append(f"文件不存在: {rel_str} ({path})")
            continue
        try:
            sz = path.stat().st_size
            if sz == 0:
                missing_errors.append(f"文件为空 (0 字节): {rel_str}")
                continue
            text = path.read_text(encoding="utf-8")
            if not text.strip():
                missing_errors.append(f"文件内容仅含空白字符: {rel_str}")
                continue
            file_contents[key] = text
            print(f"[PASS] 检查项 1: 文件存在且非空: {rel_str} ({sz} 字节)")
        except (OSError, UnicodeDecodeError) as exc:
            missing_errors.append(f"文件读取失败 ({rel_str}): {exc}")

    if missing_errors:
        print("\n" + "!" * 80)
        print("【门禁检查失败 · 文件缺失】")
        for merr in missing_errors:
            print(f"  [MISSING] {merr}")
        print("!" * 80)
        print("RESULT: FAIL (exit 2: 文件缺失)")
        return 2

    content_errors: list[str] = []

    # =========================================================================
    # 检查项 2：主交付含五节标题（Q1..Q5，按 TASK 原文）
    # =========================================================================
    md_text = file_contents["main_doc"]
    required_headings = [
        (re.compile(r"^##\s*Q1\s+起点可观测性及误差", re.MULTILINE), "## Q1 起点可观测性及误差"),
        (re.compile(r"^##\s*Q2\s+50ms\s*窗口内的可捕获性", re.MULTILINE), "## Q2 50ms 窗口内的可捕获性"),
        (re.compile(r"^##\s*Q3\s+假阳性", re.MULTILINE), "## Q3 假阳性"),
        (re.compile(r"^##\s*Q4\s+配额与回退", re.MULTILINE), "## Q4 配额与回退"),
        (re.compile(r"^##\s*Q5\s+扰动", re.MULTILINE), "## Q5 扰动"),
    ]
    missing_headings = [label for pat, label in required_headings if not pat.search(md_text)]
    if missing_headings:
        content_errors.append(f"主交付缺少小节标题: {missing_headings}（检查项 2）")
    else:
        print(f"[PASS] 检查项 2: 主交付包含完整的 Q1..Q5 五节小节标题")

    # =========================================================================
    # 检查项 3：主交付含 `n=` 或「样本」>= 5 次
    # =========================================================================
    matches_n = re.findall(r"n\s*=", md_text, re.IGNORECASE)
    matches_sample = re.findall(r"样本", md_text)
    total_n_sample = len(matches_n) + len(matches_sample)
    if total_n_sample < 5:
        content_errors.append(
            f"主交付中 'n=' 或 '样本' 出现频次不足 5: 实际 {total_n_sample} "
            f"(其中 'n=' 出现 {len(matches_n)} 次, '样本' 出现 {len(matches_sample)} 次)（检查项 3）"
        )
    else:
        print(
            f"[PASS] 检查项 3: 主交付中 'n=' 出现 {len(matches_n)} 次，'样本' 出现 {len(matches_sample)} 次，"
            f"合计 {total_n_sample} 次 (>= 5)"
        )

    # =========================================================================
    # 检查项 4：★ 主交付不得出现「物理上做不到」「方案不可行」「已验证可行」（出现即 FAIL）
    # =========================================================================
    forbidden_words = ["物理上做不到", "方案不可行", "已验证可行"]
    hits_forbidden = [fw for fw in forbidden_words if fw in md_text]
    if hits_forbidden:
        content_errors.append(f"主交付包含违禁措辞: {hits_forbidden}（检查项 4）")
    else:
        print(f"[PASS] 检查项 4: 主交付未出现任何违禁措辞 ({forbidden_words})")

    # =========================================================================
    # 检查项 5-8：FEASIBILITY_STATS.json 结构与数值自洽检查
    # =========================================================================
    stats_raw = file_contents["stats_json"]
    try:
        stats_data = json.loads(stats_raw)
        if not isinstance(stats_data, dict):
            content_errors.append("FEASIBILITY_STATS.json 顶层不是 JSON 对象（检查项 5）")
            stats_data = {}
    except Exception as exc:
        content_errors.append(f"FEASIBILITY_STATS.json 无法解析为 JSON: {exc}（检查项 5）")
        stats_data = {}

    # 5) 含 corpus/q1/q2/q3/q4/q5 六键
    required_keys = ["corpus", "q1", "q2", "q3", "q4", "q5"]
    missing_keys = [k for k in required_keys if k not in stats_data]
    if missing_keys:
        content_errors.append(f"FEASIBILITY_STATS.json 缺少顶级键: {missing_keys}（检查项 5）")
    else:
        print(f"[PASS] 检查项 5: FEASIBILITY_STATS.json 包含全部 6 个顶级键: {required_keys}")

    # 6) q3.kTable 长度 == 3；q4.quotaTable 长度 == 3
    k_table = stats_data.get("q3", {}).get("kTable")
    if not isinstance(k_table, list):
        content_errors.append("q3.kTable 不是数组（检查项 6）")
    elif len(k_table) != 3:
        content_errors.append(f"q3.kTable 长度期望 3，实际为 {len(k_table)}（检查项 6）")
    else:
        print(f"[PASS] 检查项 6: q3.kTable 长度 == 3 (k={ [x.get('k') for x in k_table] })")

    quota_table = stats_data.get("q4", {}).get("quotaTable")
    if not isinstance(quota_table, list):
        content_errors.append("q4.quotaTable 不是数组（检查项 6）")
    elif len(quota_table) != 3:
        content_errors.append(f"q4.quotaTable 长度期望 3，实际为 {len(quota_table)}（检查项 6）")
    else:
        print(f"[PASS] 检查项 6: q4.quotaTable 长度 == 3 (n={ [x.get('n') for x in quota_table] })")

    # 7) q5.verified == false（严格布尔假）
    q5_val = stats_data.get("q5", {}).get("verified")
    if type(q5_val) is not bool or q5_val is not False:
        content_errors.append(
            f"q5.verified 必须为严格布尔假 (False)，实际为: {q5_val!r} (类型: {type(q5_val).__name__})（检查项 7）"
        )
    else:
        print(f"[PASS] 检查项 7: q5.verified 为严格布尔假 False")

    # 8) 脚本自算：q2.coverageByDuration 每项 rate 与 capturableWithin50ms/total 一致（容差 0.001），total 为 0 的项跳过
    cov_list = stats_data.get("q2", {}).get("coverageByDuration")
    if not isinstance(cov_list, list) or len(cov_list) == 0:
        content_errors.append("q2.coverageByDuration 缺失或不是非空数组（检查项 8）")
    else:
        for idx, item in enumerate(cov_list):
            if not isinstance(item, dict):
                content_errors.append(f"q2.coverageByDuration[{idx}] 不是字典对象（检查项 8）")
                continue
            bucket_name = item.get("bucket", f"item_{idx}")
            tot = item.get("total")
            cap = item.get("capturableWithin50ms")
            rate = item.get("rate")
            if not isinstance(tot, (int, float)) or isinstance(tot, bool):
                content_errors.append(f"q2 分桶 '{bucket_name}' 的 total 非数值: {tot}（检查项 8）")
                continue
            if tot == 0:
                print(f"[INFO] 检查项 8: q2 分桶 '{bucket_name}' total 为 0，跳过比对")
                continue
            if not isinstance(cap, (int, float)) or isinstance(cap, bool):
                content_errors.append(f"q2 分桶 '{bucket_name}' 的 capturableWithin50ms 非数值: {cap}（检查项 8）")
                continue
            if not isinstance(rate, (int, float)) or isinstance(rate, bool):
                content_errors.append(f"q2 分桶 '{bucket_name}' 的 rate 非数值: {rate}（检查项 8）")
                continue

            expected_rate = cap / tot
            diff = abs(rate - expected_rate)
            if diff > 0.001:
                content_errors.append(
                    f"q2 分桶 '{bucket_name}' rate 不自洽: 声明值={rate}, 期望值={expected_rate:.6f}, 差异={diff:.6f} > 0.001（检查项 8）"
                )
            else:
                print(
                    f"[PASS] 检查项 8: q2 分桶 '{bucket_name}': total={tot}, capturable={cap}, "
                    f"rate={rate} (自算={expected_rate:.6f}, diff={diff:.6f} <= 0.001)"
                )

    # =========================================================================
    # 检查项 9：反扫描（_feasibility_probe.py 不得出现敏感采样/注入 API 与底层调用）
    # 检查: ctypes / OpenProcess / ReadProcessMemory / MiniDump / SuspendThread / StackWalk
    # =========================================================================
    probe_text = file_contents["probe_py"]
    banned_keywords = (
        "ctypes",
        "openprocess",
        "readprocessmemory",
        "minidump",
        "suspendthread",
        "stackwalk",
    )

    detected_code_apis: list[str] = []
    try:
        probe_ast = ast.parse(probe_text, filename="_feasibility_probe.py")
        for node in ast.walk(probe_ast):
            # 检查模块导入 import xxx
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name_low = alias.name.lower()
                    for bkw in banned_keywords:
                        if bkw in name_low:
                            detected_code_apis.append(f"import {alias.name} (行 {node.lineno})")
            # 检查 from xxx import yyy
            elif isinstance(node, ast.ImportFrom):
                mod_low = (node.module or "").lower()
                for bkw in banned_keywords:
                    if bkw in mod_low:
                        detected_code_apis.append(f"from {node.module} import ... (行 {node.lineno})")
                for alias in node.names:
                    name_low = alias.name.lower()
                    for bkw in banned_keywords:
                        if bkw in name_low:
                            detected_code_apis.append(f"from {node.module} import {alias.name} (行 {node.lineno})")
            # 检查代码标识符名称
            elif isinstance(node, ast.Name):
                id_low = node.id.lower()
                if id_low in banned_keywords:
                    detected_code_apis.append(f"标识符 {node.id} (行 {node.lineno})")
            # 检查属性访问 (如 ctypes.windll 或 kernel32.OpenProcess)
            elif isinstance(node, ast.Attribute):
                attr_low = node.attr.lower()
                if attr_low in banned_keywords:
                    detected_code_apis.append(f"属性访问 {node.attr} (行 {node.lineno})")

        # 检查词法 Token（排除注释与字符串字面量）
        tokens = list(tokenize.tokenize(io.BytesIO(probe_text.encode("utf-8")).readline))
        for tok in tokens:
            if tok.type not in (
                tokenize.COMMENT,
                tokenize.STRING,
                tokenize.ENCODING,
                tokenize.NL,
                tokenize.NEWLINE,
            ):
                tok_low = tok.string.lower()
                if tok_low in banned_keywords:
                    detected_code_apis.append(f"代码 Token '{tok.string}' (行 {tok.start[0]})")

    except SyntaxError as exc:
        content_errors.append(f"_feasibility_probe.py 语法解析失败: {exc}（检查项 9）")

    if detected_code_apis:
        content_errors.append(
            f"反扫描失败: _feasibility_probe.py 存在敏感采样/注入接口与调用: {detected_code_apis}（检查项 9）"
        )
    else:
        print(
            "[PASS] 检查项 9: 反扫描通过，_feasibility_probe.py 零命中敏感 API"
            "（代码中未出现 ctypes / OpenProcess / ReadProcessMemory / MiniDump / SuspendThread / StackWalk 的导入或调用）"
        )

    # =========================================================================
    # 检查项 10：lead/early_trigger_feasibility_20261106/review/FEASIBILITY_REVIEW.md
    # 含六字段且 checkedEveryRow/statsHaveN/noCherryPicking/q5MarkedUnverified/noForbiddenWording 均为 true
    # =========================================================================
    review_text = file_contents["review_doc"]
    expected_flags = [
        "checkedEveryRow",
        "statsHaveN",
        "noCherryPicking",
        "q5MarkedUnverified",
        "noForbiddenWording",
    ]
    for flag in expected_flags:
        pat = rf"^\s*{flag}\s*:\s*(true|false)\b"
        m = re.search(pat, review_text, re.MULTILINE | re.IGNORECASE)
        if not m:
            content_errors.append(f"复核件缺少标记字段: '{flag}'（检查项 10）")
        elif m.group(1).lower() != "true":
            content_errors.append(
                f"复核件标记字段 '{flag}' 期望 true，实际为 '{m.group(1)}'（检查项 10）"
            )

    has_sha = bool(re.search(r"^\s*subjectSha256\s*:\s*.+", review_text, re.MULTILINE))
    has_bytes = bool(re.search(r"^\s*subjectBytes\s*:\s*.+", review_text, re.MULTILINE))
    if not has_sha:
        content_errors.append("复核件缺少 'subjectSha256' 字段（检查项 10）")
    if not has_bytes:
        content_errors.append("复核件缺少 'subjectBytes' 字段（检查项 10）")

    if not any("检查项 10" in e for e in content_errors):
        print(
            "[PASS] 检查项 10: 复核件包含全量字段 (subjectSha256/subjectBytes 等) 且全部 5 个复核标记均为 true"
        )

    # =========================================================================
    # 门禁汇总判定输出
    # =========================================================================
    print("-" * 80)
    if content_errors:
        print(f"【门禁检查失败 · 内容不合格】共发现 {len(content_errors)} 处错误:")
        for cerr in content_errors:
            print(f"  [CONTENT_ERROR] {cerr}")
        print("-" * 80)
        print("RESULT: FAIL (exit 1: 内容不合格)")
        return 1

    print("★ 所有门禁检查项全部通过！(ExitCode 0 = PASS)")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
