#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_stall_def.py - 停滞事件定义确定性门禁检查脚本。

纯只读检查脚本，只用 Python 标准库，在仓库根以隔离模式运行。
参数为脚本自身路径（或目标目录路径）。

检查项：
1) lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md、
   lead/stall_event_def_20261106/STALL_EVENTS.json、
   lead/stall_event_def_20261106/_stall_probe.py、
   lead/stall_event_def_20261106/_stall_probe_out.txt、
   lead/stall_event_def_20261106/review/STALL_EVENT_DEF_REVIEW.md
   都存在且非空；
2) 主交付含五个小节标题（Q1..Q5，按 TASK 里的原文）；
3) 主交付含「负控」字样，且含「排除」字样；
4) 主交付含至少 3 处 `n=` 或「样本」；
5) 主交付含「## 未验」小节且正文非空；
6) lead/stall_event_def_20261106/STALL_EVENTS.json 可解析为数组、非空、每条含 9 个键；
7) 反扫描：lead/stall_event_def_20261106/_stall_probe.py 全文不得出现
   ctypes / ReadProcessMemory / MiniDump / SuspendThread / StackWalk / SetWindowsHook；
8) lead/stall_event_def_20261106/review/STALL_EVENT_DEF_REVIEW.md 含
   checkedEveryRow: true、negativeControlPassed: true、noSamplingCode: true。

退出码：
  0 = PASS
  1 = 内容不合格（逐条打印原因）
  2 = 文件缺失
脚本只读，不修改任何文件。
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys


BANNED_KEYWORDS = (
    "ctypes",
    "ReadProcessMemory",
    "MiniDump",
    "SuspendThread",
    "StackWalk",
    "SetWindowsHook",
)

REQUIRED_REVIEW_TAGS = (
    "checkedEveryRow: true",
    "negativeControlPassed: true",
    "noSamplingCode: true",
)


def resolve_base_dir() -> Path:
    """根据命令行参数或 __file__ 解析 lead/stall_event_def_20261106 目录。"""
    if len(sys.argv) > 1:
        arg_path = Path(sys.argv[1])
        if arg_path.is_dir():
            return arg_path.resolve()
        return arg_path.resolve().parent
    return Path(__file__).resolve().parent


def to_rel(p: Path, repo_root: Path) -> str:
    """转为相对于仓库根的 posix 路径字符串。"""
    try:
        return p.resolve().relative_to(repo_root.resolve()).as_posix()
    except Exception:
        return p.as_posix()


def main() -> int:
    repo_root = Path.cwd().resolve()
    base_dir = resolve_base_dir()

    missing_errors: list[str] = []
    content_errors: list[str] = []
    passed_items: list[str] = []

    # 1. 检查 5 个交付文件是否存在且非空
    required_files = {
        "main_doc": base_dir / "STALL_EVENT_DEFINITION.md",
        "events_json": base_dir / "STALL_EVENTS.json",
        "probe_py": base_dir / "_stall_probe.py",
        "probe_out": base_dir / "_stall_probe_out.txt",
        "review_doc": base_dir / "review" / "STALL_EVENT_DEF_REVIEW.md",
    }

    file_contents: dict[str, str] = {}
    file_bytes: dict[str, bytes] = {}

    for key, path in required_files.items():
        rel_str = to_rel(path, repo_root)
        if not path.is_file():
            missing_errors.append(f"{rel_str} 不存在")
            continue

        try:
            raw = path.read_bytes()
            file_bytes[key] = raw
            if len(raw) == 0:
                content_errors.append(f"文件为空: {rel_str} 字节数为 0")
                continue
        except OSError as exc:
            missing_errors.append(f"{rel_str} 读取失败: {exc}")
            continue

        try:
            text = raw.decode("utf-8")
            file_contents[key] = text
            if not text.strip():
                content_errors.append(f"文件内容空白: {rel_str} 无有效文本")
        except UnicodeDecodeError as exc:
            content_errors.append(f"文件非 UTF-8 编码: {rel_str} ({exc})")

    if not missing_errors and not any("文件为空" in e or "文件内容空白" in e for e in content_errors):
        passed_items.append("检查项 1 通过：5 个核心交付文件均存在且非空")

    # 2. 主交付含五个小节标题（Q1..Q5，按 TASK 里的原文）
    main_doc_text = file_contents.get("main_doc")
    if main_doc_text is not None:
        missing_q: list[str] = []
        for q in range(1, 6):
            # 匹配行首二级标题后跟随 Q1..Q5
            pattern = re.compile(rf"^##\s*Q{q}\b", re.MULTILINE)
            if not pattern.search(main_doc_text):
                missing_q.append(f"Q{q}")
        if missing_q:
            content_errors.append(f"主交付缺少小节标题: {', '.join(missing_q)}（检查项 2）")
        else:
            passed_items.append("检查项 2 通过：主交付包含完整的 Q1..Q5 五个小节标题")

        # 3. 主交付含「负控」字样，且含「排除」字样
        has_nc = "负控" in main_doc_text
        has_ex = "排除" in main_doc_text
        if not has_nc:
            content_errors.append("主交付缺少「负控」字样（检查项 3）")
        if not has_ex:
            content_errors.append("主交付缺少「排除」字样（检查项 3）")
        if has_nc and has_ex:
            passed_items.append("检查项 3 通过：主交付同时包含「负控」与「排除」字样")

        # 4. 主交付含至少 3 处 `n=` 或「样本」
        n_matches = re.findall(r"n\s*=|样本", main_doc_text)
        if len(n_matches) < 3:
            content_errors.append(
                f"主交付中「n=」或「样本」出现不足 3 处（实得 {len(n_matches)} 处）（检查项 4）"
            )
        else:
            passed_items.append(
                f"检查项 4 通过：主交付出现「n=」或「样本」共 {len(n_matches)} 处 (>= 3)"
            )

        # 5. 主交付含「## 未验」小节且正文非空
        unverified_m = re.search(
            r"^##\s*(?:\d+[.、\s]*)?未验[^\r\n]*$", main_doc_text, re.MULTILINE
        )
        if not unverified_m:
            content_errors.append("主交付缺少「## 未验」小节标题（检查项 5）")
        else:
            rest = main_doc_text[unverified_m.end():]
            next_heading = re.search(r"^#{1,2}\s+", rest, re.MULTILINE)
            body = rest[:next_heading.start()].strip() if next_heading else rest.strip()
            if not body:
                content_errors.append("主交付「## 未验」小节正文为空（检查项 5）")
            else:
                passed_items.append(
                    f"检查项 5 通过：主交付包含「## 未验」小节且正文非空 ({len(body)} 字符)"
                )
    else:
        content_errors.append("主交付文档未成功读取，跳过小节内容检查（检查项 2-5）")

    # 6. STALL_EVENTS.json 可解析为数组、非空、每条含 9 个键
    json_text = file_contents.get("events_json")
    if json_text is not None:
        try:
            events_data = json.loads(json_text)
            if not isinstance(events_data, list):
                content_errors.append("STALL_EVENTS.json 根节点不是数组（检查项 6）")
            elif len(events_data) == 0:
                content_errors.append("STALL_EVENTS.json 数组为空（检查项 6）")
            else:
                bad_items = []
                for idx, row in enumerate(events_data):
                    if not isinstance(row, dict) or len(row.keys()) != 9:
                        bad_items.append(idx)
                if bad_items:
                    content_errors.append(
                        f"STALL_EVENTS.json 存在键数量不为 9 的记录 (第 {bad_items[:5]} 条等共 {len(bad_items)} 条)（检查项 6）"
                    )
                else:
                    passed_items.append(
                        f"检查项 6 通过：STALL_EVENTS.json 为非空数组 (共 {len(events_data)} 条)，每条严格含 9 个键"
                    )
        except json.JSONDecodeError as exc:
            content_errors.append(f"STALL_EVENTS.json 无法解析为 JSON: {exc}（检查项 6）")
    else:
        content_errors.append("STALL_EVENTS.json 未成功读取，跳过 JSON 格式检查（检查项 6）")

    # 7. 反扫描：_stall_probe.py 全文不得出现 ctypes / ReadProcessMemory / MiniDump / SuspendThread / StackWalk / SetWindowsHook
    probe_text = file_contents.get("probe_py")
    if probe_text is not None:
        detected_banned = [
            kw for kw in BANNED_KEYWORDS if kw.lower() in probe_text.lower()
        ]
        if detected_banned:
            content_errors.append(
                f"_stall_probe.py 出现违禁敏感 API/关键词: {detected_banned}（检查项 7）"
            )
        else:
            passed_items.append(
                "检查项 7 通过：反扫描排查无敏感 API，零命中违禁采样调用"
            )
    else:
        content_errors.append("_stall_probe.py 未成功读取，跳过反扫描检查（检查项 7）")

    # 8. review/STALL_EVENT_DEF_REVIEW.md 含 checkedEveryRow: true、negativeControlPassed: true、noSamplingCode: true
    review_text = file_contents.get("review_doc")
    if review_text is not None:
        missing_tags: list[str] = []
        for tag in REQUIRED_REVIEW_TAGS:
            key, val = tag.split(":")
            pat = rf"\b{re.escape(key.strip())}\s*:\s*{re.escape(val.strip())}\b"
            if not re.search(pat, review_text, re.IGNORECASE):
                missing_tags.append(tag)
        if missing_tags:
            content_errors.append(
                f"STALL_EVENT_DEF_REVIEW.md 缺少必要标记: {', '.join(missing_tags)}（检查项 8）"
            )
        else:
            passed_items.append(
                "检查项 8 通过：独立复核件包含全部 3 个强制核验状态标记"
            )
    else:
        content_errors.append("独立复核件未成功读取，跳过复核标记检查（检查项 8）")

    # 输出汇总结果
    print("=" * 70)
    print("【停滞事件定义 · 确定性门禁检查 check_stall_def.py】")
    print("=" * 70)
    for p_msg in passed_items:
        print(f"PASS: {p_msg}")

    if missing_errors:
        print("\n--- 缺失错误 ---")
        for m_err in missing_errors:
            print(f"FAIL [文件缺失]: {m_err}")

    if content_errors:
        print("\n--- 内容不合格错误 ---")
        for c_err in content_errors:
            print(f"FAIL [内容不合格]: {c_err}")

    print("=" * 70)
    if missing_errors:
        print("RESULT: FAIL (exit 2: 文件缺失)")
        return 2
    if content_errors:
        print("RESULT: FAIL (exit 1: 内容不合格)")
        return 1

    print("RESULT: PASS (exit 0)")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
