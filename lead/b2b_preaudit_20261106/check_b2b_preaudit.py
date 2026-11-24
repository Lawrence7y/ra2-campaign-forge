#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_b2b_preaudit.py — B2b 独立设计预审判定书机械门禁（只读，只用标准库）。

用法（仓库根以隔离模式运行，参数为脚本自身路径）：
    python -I -X utf8 lead/b2b_preaudit_20261106/check_b2b_preaudit.py

退出码：
    0 = PASS
    1 = 内容不合格（逐条打印原因）
    2 = 文件缺失

本脚本只读，不写任何文件，尤其不修改任何交付件。
"""
from __future__ import annotations

import io
import os
import re
import sys
from pathlib import Path

# Windows 控制台输出防御性设置
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# --- 路径解析 -------------------------------------------------------------
# 优先根据命令行参数或 __file__ 解析基准目录，定位于 lead/b2b_preaudit_20261106/
if len(sys.argv) > 1 and sys.argv[1].endswith(".py"):
    _script_path = Path(sys.argv[1]).resolve()
else:
    _script_path = Path(__file__).resolve()

BASE = _script_path.parent
if BASE.name != "b2b_preaudit_20261106":
    candidate = Path.cwd() / "lead" / "b2b_preaudit_20261106"
    if candidate.is_dir():
        BASE = candidate.resolve()

ROOT = BASE.parent.parent

# 四个核心交付文件 (key, path, rel_path)
TARGET_FILES = [
    ("verdict", BASE / "B2B_PREAUDIT.md", "lead/b2b_preaudit_20261106/B2B_PREAUDIT.md"),
    ("probe_py", BASE / "_b2b_pa_probe.py", "lead/b2b_preaudit_20261106/_b2b_pa_probe.py"),
    ("probe_out", BASE / "_b2b_pa_probe_out.txt", "lead/b2b_preaudit_20261106/_b2b_pa_probe_out.txt"),
    ("review", BASE / "review" / "B2B_PREAUDIT_REVIEW.md", "lead/b2b_preaudit_20261106/review/B2B_PREAUDIT_REVIEW.md"),
]

# 状态收集器
MISSING_FAILURES: list[str] = []
CONTENT_FAILURES: list[str] = []
PASSED: list[str] = []


def fail_missing(msg: str) -> None:
    MISSING_FAILURES.append(msg)


def fail_content(msg: str) -> None:
    CONTENT_FAILURES.append(msg)


def pass_check(check_id: str, msg: str) -> None:
    PASSED.append(f"[CHECK {check_id}] PASS — {msg}")


def main() -> int:
    print(f"[BASE] {BASE}")

    # =========================================================================
    # 检查项 1：四个核心文件存在且非空
    # =========================================================================
    texts: dict[str, str] = {}
    missing_in_target = False

    for key, path, rel in TARGET_FILES:
        if not path.is_file():
            fail_missing(f"文件缺失：{rel} 不存在（{path}）")
            missing_in_target = True
            continue
        try:
            stat_res = path.stat()
        except OSError as exc:
            fail_missing(f"文件不可访问：{rel} 无法 stat（{exc}）")
            missing_in_target = True
            continue

        if stat_res.st_size == 0:
            fail_content(f"文件为空：{rel} 大小为 0 字节")
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            fail_content(f"文件不可解析：{rel} 非 UTF-8 编码（{exc}）")
            continue
        except OSError as exc:
            fail_missing(f"文件不可读：{rel} 读取失败（{exc}）")
            missing_in_target = True
            continue

        if not content.strip():
            fail_content(f"文件为空：{rel} 仅包含空白字符")
            continue

        texts[key] = content

    if not missing_in_target and len(texts) == 4:
        pass_check("1", "4 个交付文件均存在且非空")
    else:
        if missing_in_target:
            print(f"[CHECK 1] FAIL — 存在文件缺失（共 {len(MISSING_FAILURES)} 处）")
        else:
            print(f"[CHECK 1] FAIL — 存在文件为空或不可解析（共 {len(CONTENT_FAILURES)} 处）")

    verdict_text = texts.get("verdict")
    review_text = texts.get("review")

    # =========================================================================
    # 判定书各项内容检查（检查项 2–6, 8）
    # =========================================================================
    if verdict_text is None:
        fail_missing("判定书 B2B_PREAUDIT.md 无法读取，后续判定书检查无法执行")
    else:
        verdict_lines = verdict_text.splitlines()

        # ---------------------------------------------------------------------
        # 检查项 2：判定书头部含 3 个不同的 64 位 hex 与 3 个字节数
        # 头部定义：文件开头至第一个二级标题（## ）之前的文本
        # ---------------------------------------------------------------------
        head_end = next(
            (i for i, line in enumerate(verdict_lines) if re.match(r"^##\s+", line)),
            len(verdict_lines),
        )
        header_text = "\n".join(verdict_lines[:head_end])

        hexes = set(h.lower() for h in re.findall(r"\b[0-9a-fA-F]{64}\b", header_text))

        byte_vals: set[str] = set()
        # 1) Markdown 表格单元格中的纯数字（从表格数据列提取 4–7 位字节数）
        for line in header_text.splitlines():
            if line.strip().startswith("|"):
                parts = [c.strip() for c in line.split("|")[1:-1]]
                for part in parts:
                    clean = part.replace(",", "").strip("`* ")
                    if clean.isdigit() and 4 <= len(clean) <= 7:
                        byte_vals.add(clean)
        # 2) 补充独立 5–7 位数字（如 \b\d{5,7}\b）
        for m in re.findall(r"\b\d{5,7}\b", header_text):
            byte_vals.add(m)

        hex_ok = len(hexes) >= 3
        bytes_ok = len(byte_vals) >= 3
        if not hex_ok:
            fail_content(f"判定书头部 64 位 hex 不足：需 >= 3 个不同 hex，实得 {len(hexes)}（检查项 2）")
        if not bytes_ok:
            fail_content(f"判定书头部字节数不足：需 >= 3 个不同字节数，实得 {len(byte_vals)}（检查项 2）")
        if hex_ok and bytes_ok:
            pass_check(
                "2",
                f"判定书头部含 {len(hexes)} 个不同 64 位 hex 与 {len(byte_vals)} 个不同字节数",
            )

        # ---------------------------------------------------------------------
        # 检查项 3：含 #### H1 … #### H9 九个标题
        # ---------------------------------------------------------------------
        missing_hunks: list[str] = []
        for i in range(1, 10):
            pat = re.compile(rf"^####\s+H{i}(?:\s|$)", re.MULTILINE)
            if not pat.search(verdict_text):
                missing_hunks.append(f"H{i}")

        if missing_hunks:
            fail_content(f"缺少 Hunk 标题：未匹配 #### {', '.join(missing_hunks)}（检查项 3）")
        else:
            pass_check("3", "含 #### H1 … #### H9 九个标题")

        # ---------------------------------------------------------------------
        # 检查项 4：含 ^verdict:\s*(YES|NO)\s*$ 一行
        # ---------------------------------------------------------------------
        re_verdict_line = re.compile(r"^verdict:\s*(YES|NO)\s*$", re.MULTILINE)
        m_verdict = re_verdict_line.search(verdict_text)
        verdict: str | None = None
        if not m_verdict:
            fail_content("缺少合法 verdict 行：未匹配 `^verdict:\\s*(YES|NO)\\s*$`（检查项 4）")
        else:
            verdict = m_verdict.group(1)
            pass_check("4", f"含合法 verdict 行：verdict = {verdict}")

        # ---------------------------------------------------------------------
        # 检查项 5：含五个小节标题（行号偏移与拼接 / 五个早退路径 / 状态矩阵 / F/E 分离 / 未验）
        # ---------------------------------------------------------------------
        required_sections = [
            "行号偏移与拼接",
            "五个早退路径",
            "状态矩阵",
            "F/E 分离",
            "未验",
        ]
        missing_sections: list[str] = []
        for sec_name in required_sections:
            pat = re.compile(rf"^##\s+.*{re.escape(sec_name)}.*$", re.MULTILINE)
            if not pat.search(verdict_text):
                missing_sections.append(sec_name)

        if missing_sections:
            fail_content(f"缺少小节标题：未匹配包含「{', '.join(missing_sections)}」的二级标题（检查项 5）")
        else:
            pass_check("5", "含全部五个小节标题（行号偏移与拼接 / 五个早退路径 / 状态矩阵 / F/E 分离 / 未验）")

        # ---------------------------------------------------------------------
        # 检查项 6：「未验」小节正文非空
        # ---------------------------------------------------------------------
        m_unv = re.search(r"^##\s+.*未验.*$", verdict_text, re.MULTILINE)
        if not m_unv:
            fail_content("缺失「未验」小节（检查项 6）")
        else:
            start_pos = m_unv.end()
            m_next = re.search(r"^#{1,2}\s+", verdict_text[start_pos:], re.MULTILINE)
            end_pos = start_pos + m_next.start() if m_next else len(verdict_text)
            unv_body = verdict_text[start_pos:end_pos].strip()
            if not unv_body:
                fail_content("「未验」小节正文为空（检查项 6）")
            else:
                pass_check("6", f"「未验」小节正文非空（{len(unv_body)} 字符）")

    # =========================================================================
    # 检查项 7：复核回件检查
    # =========================================================================
    if review_text is None:
        fail_content("复核回件不可读或缺失，无法检查复核字段（检查项 7）")
    else:
        review_issues: list[str] = []
        if not re.search(r"checkedEveryRow:\s*true\b", review_text, re.IGNORECASE):
            review_issues.append("缺少 checkedEveryRow: true")
        if not re.search(r"noOverreach:\s*true\b", review_text, re.IGNORECASE):
            review_issues.append("缺少 noOverreach: true")
        if not re.search(r"hunkVerdictCount:\s*['\"]?9/9['\"]?", review_text):
            review_issues.append("缺少 hunkVerdictCount: 9/9")

        if review_issues:
            fail_content(f"复核回件字段不合格：{', '.join(review_issues)}（检查项 7）")
        else:
            pass_check("7", "复核回件包含 checkedEveryRow: true、noOverreach: true、hunkVerdictCount: 9/9")

    # =========================================================================
    # 检查项 8：一致性：若判定书是 verdict: YES，则九个 hunk 小节里不得出现 BLOCKED
    # =========================================================================
    if verdict_text is not None:
        if verdict == "YES":
            m_h1 = re.search(r"^####\s+H1(?:\s|$)", verdict_text, re.MULTILINE)
            m_h9 = re.search(r"^####\s+H9(?:\s|$)", verdict_text, re.MULTILINE)
            if not m_h1 or not m_h9:
                fail_content("未找到 H1 或 H9 标题，无法划定 hunk 小节范围（检查项 8）")
            else:
                m_after = re.search(r"^#{1,2}\s+", verdict_text[m_h9.end():], re.MULTILINE)
                hunk_zone_end = m_h9.end() + m_after.start() if m_after else len(verdict_text)
                hunk_zone_text = verdict_text[m_h1.start():hunk_zone_end]

                blocked_found: list[str] = []
                for i in range(1, 10):
                    pat_h = re.compile(rf"^####\s+H{i}(?:\s|$)", re.MULTILINE)
                    m_h = pat_h.search(verdict_text)
                    if not m_h:
                        continue
                    h_start = m_h.start()
                    if i < 9:
                        pat_next_h = re.compile(rf"^####\s+H{i+1}(?:\s|$)", re.MULTILINE)
                        m_next_h = pat_next_h.search(verdict_text)
                        h_end = m_next_h.start() if m_next_h else hunk_zone_end
                    else:
                        h_end = hunk_zone_end
                    sub_text = verdict_text[h_start:h_end]
                    if re.search(r"\bBLOCKED\b", sub_text):
                        blocked_found.append(f"H{i}")

                if blocked_found:
                    fail_content(
                        f"一致性冲突：verdict 为 YES 但以下 hunk 小节中出现 BLOCKED：{', '.join(blocked_found)}（检查项 8）"
                    )
                elif re.search(r"\bBLOCKED\b", hunk_zone_text):
                    fail_content("一致性冲突：verdict 为 YES 但 hunk 区域内包含 BLOCKED（检查项 8）")
                else:
                    pass_check("8", "一致性核验通过：verdict 为 YES 且九个 hunk 小节中均无 BLOCKED")
        elif verdict == "NO":
            pass_check("8", "判定书 verdict 为 NO，一致性检查通过")

    # =========================================================================
    # 结果汇总与退出码
    # =========================================================================
    print("\n=== B2B_PREAUDIT 门禁核验结果 ===")
    for msg in PASSED:
        print(msg)
    for msg in MISSING_FAILURES:
        print(f"[FAIL-MISSING] {msg}")
    for msg in CONTENT_FAILURES:
        print(f"[FAIL-CONTENT] {msg}")

    if MISSING_FAILURES:
        print(f"\nRESULT: FAIL（文件缺失，共 {len(MISSING_FAILURES)} 项；exit 2）")
        return 2
    if CONTENT_FAILURES:
        print(f"\nRESULT: FAIL（内容不合格，共 {len(CONTENT_FAILURES)} 项；exit 1）")
        return 1

    print("\nRESULT: PASS（全部检查项通过；exit 0）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
