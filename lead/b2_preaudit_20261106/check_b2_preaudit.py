#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 设计预审判定书的确定性门禁（只读）。

用法（仓库根执行）：
    python -I -X utf8 lead/b2_preaudit_20261106/check_b2_preaudit.py

退出码：
    0 = PASS
    1 = 内容不合格（逐条 print 原因）
    2 = 文件缺失 / 不可解析

本脚本不写任何文件，尤其不修改判定书。
"""
from __future__ import annotations

import io
import os
import re
import sys

# --- 路径 ---------------------------------------------------------------
# 以仓库根的 cwd 为基准，避免依赖 __file__ 在不同调用方式下的差异。
ROOT = os.getcwd()
BASE = os.path.join(ROOT, "lead", "b2_preaudit_20261106")
VERDICT_PATH = os.path.join(BASE, "B2_PREAUDIT.md")
REVIEW_PATH = os.path.join(BASE, "review", "B2_PREAUDIT_REVIEW.md")
PROBE_PY_PATH = os.path.join(BASE, "_b2_probe.py")
PROBE_OUT_PATH = os.path.join(BASE, "_b2_probe_out.txt")

# --- 正则 ---------------------------------------------------------------
RE_VERDICT_LINE = re.compile(r"verdict:\s*(YES|NO)\s*")
RE_SHA256 = re.compile(r"\b[0-9a-f]{64}\b")
RE_BYTES = re.compile(r"\b\d{5,7}\b")
RE_SECTION = re.compile(r"^##(?!#)[ \t]*(.+?)[ \t]*$", re.MULTILINE)
RE_ANY_HEADING = re.compile(r"^#{1,2}(?!#)[ \t]", re.MULTILINE)
RE_CHECKED = re.compile(
    r"^[ \t]*checkedEveryRow:[ \t]*(true|false)[ \t]*$",
    re.MULTILINE | re.IGNORECASE,
)
RE_SUBJECT_SHA = re.compile(
    r"^[ \t]*subjectSha256:[ \t]*([0-9a-fA-F]{64})[ \t]*$", re.MULTILINE
)

# 两个收集器：content_failures -> 退出码 1；missing_failures -> 退出码 2
CONTENT_FAILURES: list[str] = []
MISSING_FAILURES: list[str] = []
PASSED: list[str] = []
NOTES: list[str] = []


def fail_content(msg: str) -> None:
    CONTENT_FAILURES.append(msg)


def fail_missing(msg: str) -> None:
    MISSING_FAILURES.append(msg)


def section_lines_span(text: str, wanted: str) -> tuple[int, int, str]:
    """返回「## <wanted>」小节正文的 (起始行, 结束行, 正文)。

    起始/结束为 0 基、左闭右开的行下标；若无该小节返回 (-1, -1, "").
    小节范围截止到下一个同级或更高级（## / #）标题。
    """
    lines = text.splitlines()
    # 所有标题行（# 或 ## 开头），小节范围截止到下一个同级/更高级标题。
    boundaries = [
        i for i, line in enumerate(lines) if RE_ANY_HEADING.match(line)
    ]
    for m in RE_SECTION.finditer(text):
        title = m.group(1).strip()
        if title != wanted:
            continue
        line_no = text.count("\n", 0, m.start())
        start = line_no + 1
        later = [b for b in boundaries if b >= start]
        end = later[0] if later else len(lines)
        return start, end, "\n".join(lines[start:end])
    return -1, -1, ""


def read_text(path: str, label: str) -> str | None:
    """只读地读取 UTF-8 文本；缺失或不可解析记入 missing 并返回 None。"""
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            data = fh.read()
    except FileNotFoundError:
        fail_missing(f"缺失：{label} 不存在（{path}）")
        return None
    except OSError as exc:
        fail_missing(f"不可读：{label} 读取失败（{path}）：{exc}")
        return None
    except UnicodeDecodeError as exc:
        fail_missing(f"不可解析：{label} 非 UTF-8（{path}）：{exc}")
        return None
    if not data.strip():
        fail_content(f"空文件：{label} 没有任何非空内容（{path}）")
    return data


def read_bytes_nonempty(path: str, label: str) -> None:
    """检查文件存在、可读且字节数 > 0；只读。"""
    try:
        with io.open(path, "rb") as fh:
            payload = fh.read()
    except FileNotFoundError:
        fail_missing(f"缺失：{label} 不存在（{path}）")
        return
    except OSError as exc:
        fail_missing(f"不可读：{label} 读取失败（{path}）：{exc}")
        return
    if len(payload) == 0:
        fail_content(f"空文件：{label} 为 0 字节（{path}）")
    else:
        PASSED.append(f"存在且非空：{label}（{len(payload)} 字节）")


def main() -> int:
    # 1) 判定书存在（读取失败由 read_text 归入 missing）
    verdict_text = read_text(VERDICT_PATH, "B2_PREAUDIT.md")

    # 8) 探针脚本与输出都存在且非空（与判定书内容无关，总是检查）
    read_bytes_nonempty(PROBE_PY_PATH, "_b2_probe.py")
    read_bytes_nonempty(PROBE_OUT_PATH, "_b2_probe_out.txt")

    if verdict_text is None:
        # 判定书缺失/不可解析，后续正文检查无法执行（详细原因见 MISSING_FAILURES）。
        NOTES.append("未执行：检查项 2–7 依赖判定书正文")
    else:
        PASSED.append("存在且可读：B2_PREAUDIT.md")

        # 2) 六个 E 标题（正则匹配行首，允许标题后带文字）
        missing_e_titles: list[int] = []
        for n in range(1, 7):
            pat = re.compile(r"^#### E" + str(n) + r" ", re.MULTILINE)
            if not pat.search(verdict_text):
                missing_e_titles.append(n)
                fail_content(f"缺失标题：未匹配行首 `#### E{n} `（检查项 2）")
        if not missing_e_titles:
            PASSED.append("检查项 2：六个 `#### E1 ` … `#### E6 ` 标题齐全")

        # 3) 至少 2 个 SHA256 + 至少 2 个字节数
        shas = RE_SHA256.findall(verdict_text)
        byte_counts = RE_BYTES.findall(verdict_text)
        if len(shas) < 2:
            fail_content(
                f"SHA256 不足：需 >= 2 个 64 位十六进制，实得 {len(shas)}（检查项 3）"
            )
        if len(byte_counts) < 2:
            fail_content(
                f"字节数不足：需 >= 2 个 \\b\\d{{5,7}}\\b，实得 {len(byte_counts)}（检查项 3）"
            )
        if len(shas) >= 2 and len(byte_counts) >= 2:
            PASSED.append(
                f"检查项 3：SHA256 {len(shas)} 个、字节数 {len(byte_counts)} 个"
            )

        # 4) 有一行匹配 `^verdict:\s*(YES|NO)\s*$`；取首个匹配值决定 6/7 分支
        verdict: str | None = None
        for line in verdict_text.splitlines():
            m = RE_VERDICT_LINE.fullmatch(line)
            if m:
                verdict = m.group(1)
                break
        if verdict is None:
            fail_content("缺失 verdict：未匹配 `^verdict:\\s*(YES|NO)\\s*$`（检查项 4）")
        else:
            PASSED.append(f"检查项 4：verdict = {verdict}")

        # 5) 「## 未验」小节且正文非空
        start, end, unverified_body = section_lines_span(verdict_text, "未验")
        if start < 0:
            fail_content("缺失小节：未找到 `## 未验`（检查项 5）")
        elif not unverified_body.strip():
            fail_content("空小节：`## 未验` 正文为空（检查项 5）")
        else:
            PASSED.append("检查项 5：`## 未验` 小节存在且正文非空")

        # 判定书头部第一个 SHA256：按文档顺序取第一个匹配（不限定在某一行区间，
        # 以保持「头部」= 正文前部出现的第一个哈希这一确定性口径）。
        head_sha = shas[0] if shas else None

        # 7) verdict=NO 时必须含「## 阻断与责任角色」小节
        if verdict == "NO":
            if section_lines_span(verdict_text, "阻断与责任角色")[0] < 0:
                fail_content(
                    "缺失小节：verdict=NO 但未找到 `## 阻断与责任角色`（检查项 7）"
                )
            else:
                PASSED.append("检查项 7：verdict=NO，`## 阻断与责任角色` 小节存在")

        # 6) verdict=YES 时的复核回件检查
        if verdict == "YES":
            review_text = read_text(REVIEW_PATH, "review/B2_PREAUDIT_REVIEW.md")
            if review_text is not None:
                PASSED.append("存在且可读：review/B2_PREAUDIT_REVIEW.md")
                checked = RE_CHECKED.search(review_text)
                if checked is None:
                    fail_content(
                        "缺失字段：复核回件未匹配 `checkedEveryRow:`（检查项 6）"
                    )
                elif checked.group(1).lower() != "true":
                    fail_content(
                        "字段值不合格：checkedEveryRow = %s，需为 true（检查项 6）"
                        % checked.group(1)
                    )
                else:
                    PASSED.append("检查项 6：checkedEveryRow = true")

                subj = RE_SUBJECT_SHA.search(review_text)
                if subj is None:
                    fail_content(
                        "缺失字段：复核回件未匹配 `subjectSha256: <64hex>`（检查项 6）"
                    )
                elif head_sha is None:
                    fail_content(
                        "无法比对：判定书头部无 SHA256，subjectSha256 无从核对（检查项 6）"
                    )
                elif subj.group(1).lower() != head_sha.lower():
                    fail_content(
                        "SHA256 不一致：判定书头部首个 = %s，复核 subjectSha256 = %s（检查项 6）"
                        % (head_sha, subj.group(1))
                    )
                else:
                    PASSED.append("检查项 6：subjectSha256 与判定书头部首个 SHA256 一致")

    # --- 结果输出 -------------------------------------------------------
    print("=== B2_PREAUDIT 门禁 ===")
    for item in PASSED:
        print("PASS:", item)
    for item in NOTES:
        print("NOTE:", item)
    for item in MISSING_FAILURES:
        print("FAIL[缺失/不可解析]:", item)
    for item in CONTENT_FAILURES:
        print("FAIL[内容]:", item)

    if MISSING_FAILURES:
        print(
            "RESULT: FAIL（文件缺失/不可解析；exit 2；"
            "另外 %d 条内容不合格）" % len(CONTENT_FAILURES)
        )
        return 2
    if CONTENT_FAILURES:
        print("RESULT: FAIL（内容不合格，共 %d 条；exit 1）" % len(CONTENT_FAILURES))
        return 1
    print("RESULT: PASS（全部检查项通过；exit 0）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
