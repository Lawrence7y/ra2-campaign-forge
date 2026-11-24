#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""check_timing_clarify.py — D-13b 时序规格澄清与条件预算复审机械门禁（只读，纯标准库）。

运行方式（在仓库根、隔离模式；传给解释器的参数就是本脚本自身的路径）：
    python -I -X utf8 lead/d13b_timing_clarify_20261106/check_timing_clarify.py lead/d13b_timing_clarify_20261106/check_timing_clarify.py

检查项：
1) lead/d13b_timing_clarify_20261106/TIMING_SPEC_CLARIFY.md /
   lead/d13b_timing_clarify_20261106/TIMELINE_MODEL.json /
   lead/d13b_timing_clarify_20261106/BUDGET_SCENARIOS.json /
   lead/d13b_timing_clarify_20261106/review/TIMING_CLARIFY_REVIEW.md 都存在且非空；
2) 主交付含四个小节标题（## 1 两个 50ms / ## 2 四类时刻 / ## 3 规范冲突 / ## 4 条件预算重算）；
3) 主交付正文含「:177」与「:190」字样；
4) ★ 主交付不得出现「物理上做不到」或「方案不可行」（出现即 FAIL）；
5) lead/d13b_timing_clarify_20261106/TIMELINE_MODEL.json 可解析为数组、长度 == 4、每项含 5 个键（kind/definition/hardDeadline/evidence/verified）；
6) lead/d13b_timing_clarify_20261106/BUDGET_SCENARIOS.json 可解析为数组、长度 >= 3；
   每组含 name/segments/totalMs/vsMedianMs/meetsMedian；segments 长度 == 4 且每段含 seg/ms/evidenceGrade；
7) 脚本自算每组四段之和 == totalMs（容差 0.01）；
8) 脚本核 meetsMedian 与 (totalMs < 129.93) 一致；
9) 每段 evidenceGrade 只能是「实测」「估算」「指标」「未验」之一；
10) lead/d13b_timing_clarify_20261106/review/TIMING_CLARIFY_REVIEW.md 含 checkedEveryRow: true、budgetSelfConsistent: true、noForbiddenWording: true、gradesHonest: true。

退出码：
    0 = PASS
    1 = 内容不合格（逐条打印原因）
    2 = 文件缺失/为空/不可读

脚本只读，不修改或写入任何文件。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# 防御性控制台 UTF-8 输出
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

SELF = Path(__file__).resolve()
BASE = SELF.parent  # lead/d13b_timing_clarify_20261106
REPO = BASE.parent.parent
REL_DIR = "lead/d13b_timing_clarify_20261106"

# 检查 1 所需的 4 个交付文件
TARGETS = (
    ("clarify_md", BASE / "TIMING_SPEC_CLARIFY.md", REL_DIR + "/TIMING_SPEC_CLARIFY.md"),
    ("timeline_json", BASE / "TIMELINE_MODEL.json", REL_DIR + "/TIMELINE_MODEL.json"),
    ("budget_json", BASE / "BUDGET_SCENARIOS.json", REL_DIR + "/BUDGET_SCENARIOS.json"),
    ("review_md", BASE / "review" / "TIMING_CLARIFY_REVIEW.md", REL_DIR + "/review/TIMING_CLARIFY_REVIEW.md"),
)

REQUIRED_HEADINGS = (
    (re.compile(r"^##\s+1\s+两个\s*50ms\s*$"), "## 1 两个 50ms"),
    (re.compile(r"^##\s+2\s+四类时刻\s*$"), "## 2 四类时刻"),
    (re.compile(r"^##\s+3\s+规范冲突\s*$"), "## 3 规范冲突"),
    (re.compile(r"^##\s+4\s+条件预算重算\s*$"), "## 4 条件预算重算"),
)

FORBIDDEN_WORDS = ("物理上做不到", "方案不可行")

TIMELINE_KEYS = ("kind", "definition", "hardDeadline", "evidence", "verified")
SCENARIO_KEYS = ("name", "segments", "totalMs", "vsMedianMs", "meetsMedian")
SEGMENT_KEYS = ("seg", "ms", "evidenceGrade")
VALID_GRADES = {"实测", "估算", "指标", "未验"}
MEDIAN_MS = 129.93

REVIEW_FLAGS = (
    "checkedEveryRow: true",
    "budgetSelfConsistent: true",
    "noForbiddenWording: true",
    "gradesHonest: true",
)


def is_number(val: object) -> bool:
    """判断是否为数值（排除 bool，因 bool 是 int 的子类）。"""
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def main() -> int:
    print(f"[SELF] {SELF}")
    print(f"[BASE] {BASE}")
    print(f"[REPO] {REPO}")
    print(f"[CWD]  {Path.cwd()}")
    print(f"[ARGV0] {sys.argv[0] if sys.argv else '(none)'}")
    print(f"[ISOLATED] {bool(getattr(sys.flags, 'isolated', False))}")

    # =========================================================================
    # 检查项 1：四个交付文件存在且非空（若有缺失/为空/不可读即 exit 2）
    # =========================================================================
    texts: dict[str, str] = {}
    missing: list[str] = []

    for key, path, rel in TARGETS:
        if not path.is_file():
            missing.append(f"{rel} : 文件不存在 ({path})")
            continue
        try:
            sz = path.stat().st_size
            if sz == 0:
                missing.append(f"{rel} : 文件为空 (0 字节)")
                continue
            txt = path.read_text(encoding="utf-8")
            if not txt.strip():
                missing.append(f"{rel} : 文件内容仅包含空白")
                continue
            texts[key] = txt
        except (OSError, UnicodeDecodeError) as exc:
            missing.append(f"{rel} : 无法按 UTF-8 读取 ({exc})")

    if missing:
        for m in missing:
            print(f"[MISSING] {m}")
        print(f"[CHECK 1] FAIL — {len(missing)} 个交付文件缺失/为空/不可读")
        print("[RESULT] 文件缺失（exit 2）")
        return 2

    print(f"[CHECK 1] PASS — 4 个交付文件均存在且非空")

    problems: list[str] = []

    def chk(num: int, ok: bool, okmsg: str, failmsg: str) -> None:
        if ok:
            print(f"[CHECK {num}] PASS — {okmsg}")
        else:
            print(f"[CHECK {num}] FAIL — {failmsg}")
            problems.append(f"{num}) {failmsg}")

    clarify_text = texts["clarify_md"]
    clarify_lines = clarify_text.splitlines()

    # =========================================================================
    # 检查项 2：主交付含四个小节标题
    # =========================================================================
    missing_headings = [
        label for pat, label in REQUIRED_HEADINGS
        if not any(pat.match(line.strip()) for line in clarify_lines)
    ]
    chk(
        2,
        len(missing_headings) == 0,
        "主交付四个小节标题齐全（## 1 两个 50ms / ## 2 四类时刻 / ## 3 规范冲突 / ## 4 条件预算重算）",
        f"主交付缺少小节标题: {'、'.join(missing_headings)}",
    )

    # =========================================================================
    # 检查项 3：主交付正文含「:177」与「:190」字样
    # =========================================================================
    has_177 = ":177" in clarify_text
    has_190 = ":190" in clarify_text
    missing_line_refs = []
    if not has_177:
        missing_line_refs.append("':177'")
    if not has_190:
        missing_line_refs.append("':190'")
    chk(
        3,
        len(missing_line_refs) == 0,
        "主交付正文含 ':177' 与 ':190' 字样",
        f"主交付正文缺少行号引用: {' 与 '.join(missing_line_refs)}",
    )

    # =========================================================================
    # 检查项 4：★ 主交付不得出现「物理上做不到」或「方案不可行」（出现即 FAIL）
    # =========================================================================
    forbidden_hits: list[str] = []
    for fw in FORBIDDEN_WORDS:
        hit_lines = [i + 1 for i, line in enumerate(clarify_lines) if fw in line]
        if hit_lines:
            forbidden_hits.append(f"'{fw}'(出现在行: {hit_lines})")
    chk(
        4,
        len(forbidden_hits) == 0,
        "主交付禁用词排查 0 命中（未出现「物理上做不到」「方案不可行」）",
        f"主交付出现被禁措辞: {'、'.join(forbidden_hits)}",
    )

    # =========================================================================
    # 检查项 5：TIMELINE_MODEL.json 可解析为数组、长度 == 4、每项含 5 个键
    # =========================================================================
    t_errs: list[str] = []
    t_parsed = False
    try:
        t_data = json.loads(texts["timeline_json"])
        t_parsed = True
    except Exception as exc:
        t_errs.append(f"TIMELINE_MODEL.json 无法解析为 JSON: {exc}")

    if t_parsed:
        if not isinstance(t_data, list):
            t_errs.append(f"顶层不是数组，而是 {type(t_data).__name__}")
        elif len(t_data) != 4:
            t_errs.append(f"数组长度 {len(t_data)} != 4")
        else:
            expected_keys = set(TIMELINE_KEYS)
            for idx, item in enumerate(t_data):
                if not isinstance(item, dict):
                    t_errs.append(f"第 {idx} 项不是对象")
                    continue
                actual_keys = set(item.keys())
                if actual_keys != expected_keys:
                    t_errs.append(f"第 {idx} 项键集不符: {actual_keys} != {expected_keys}")
                if not isinstance(item.get("kind"), str) or not item.get("kind"):
                    t_errs.append(f"第 {idx} 项 kind 不是非空字符串")
                if not isinstance(item.get("definition"), str) or not item.get("definition"):
                    t_errs.append(f"第 {idx} 项 definition 不是非空字符串")
                if not isinstance(item.get("hardDeadline"), bool):
                    t_errs.append(f"第 {idx} 项 hardDeadline 不是 bool")
                if not isinstance(item.get("evidence"), str) or not item.get("evidence"):
                    t_errs.append(f"第 {idx} 项 evidence 不是非空字符串")
                if not isinstance(item.get("verified"), bool):
                    t_errs.append(f"第 {idx} 项 verified 不是 bool")
    chk(
        5,
        t_parsed and len(t_errs) == 0,
        "TIMELINE_MODEL.json 可解析为数组、长度 == 4、每项含 5 个键（kind/definition/hardDeadline/evidence/verified）且类型合法",
        "TIMELINE_MODEL.json 检查未通过: " + "；".join(t_errs),
    )

    # =========================================================================
    # 检查项 6–9：BUDGET_SCENARIOS.json 解析、结构、求和自洽、meetsMedian、证据等级
    # =========================================================================
    b_errs_6: list[str] = []
    b_errs_7: list[str] = []
    b_errs_8: list[str] = []
    b_errs_9: list[str] = []
    b_parsed = False
    b_data = None

    try:
        b_data = json.loads(texts["budget_json"])
        b_parsed = True
    except Exception as exc:
        msg = f"BUDGET_SCENARIOS.json 无法解析为 JSON: {exc}"
        b_errs_6.append(msg)
        b_errs_7.append(msg)
        b_errs_8.append(msg)
        b_errs_9.append(msg)

    n_scenarios = 0
    if b_parsed:
        if not isinstance(b_data, list):
            msg = f"顶层不是数组，而是 {type(b_data).__name__}"
            b_errs_6.append(msg)
            b_errs_7.append(msg)
            b_errs_8.append(msg)
            b_errs_9.append(msg)
        elif len(b_data) < 3:
            b_errs_6.append(f"情景组数 {len(b_data)} < 3")
        else:
            n_scenarios = len(b_data)
            required_sc_keys = set(SCENARIO_KEYS)
            required_seg_keys = set(SEGMENT_KEYS)

            for idx, sc in enumerate(b_data):
                sc_name = sc.get("name", f"情景[{idx}]") if isinstance(sc, dict) else f"情景[{idx}]"
                if not isinstance(sc, dict):
                    b_errs_6.append(f"第 {idx} 项不是对象")
                    continue

                missing_sc_keys = required_sc_keys - set(sc.keys())
                if missing_sc_keys:
                    b_errs_6.append(f"'{sc_name}' 缺键: {missing_sc_keys}")

                segments = sc.get("segments")
                if not isinstance(segments, list):
                    b_errs_6.append(f"'{sc_name}' segments 不是数组")
                    continue
                if len(segments) != 4:
                    b_errs_6.append(f"'{sc_name}' segments 长度 {len(segments)} != 4")
                    continue

                seg_sum = 0.0
                all_segs_numeric = True
                for s_idx, seg in enumerate(segments):
                    if not isinstance(seg, dict):
                        b_errs_6.append(f"'{sc_name}' 第 {s_idx} 段不是对象")
                        all_segs_numeric = False
                        continue
                    missing_seg_keys = required_seg_keys - set(seg.keys())
                    if missing_seg_keys:
                        b_errs_6.append(f"'{sc_name}' 第 {s_idx} 段缺键: {missing_seg_keys}")

                    # 检查 9：证据等级
                    grade = seg.get("evidenceGrade")
                    if grade not in VALID_GRADES:
                        b_errs_9.append(
                            f"'{sc_name}' 第 {s_idx} 段 evidenceGrade '{grade}' 非法，必须在 {VALID_GRADES} 之一"
                        )

                    ms_val = seg.get("ms")
                    if not is_number(ms_val):
                        b_errs_6.append(f"'{sc_name}' 第 {s_idx} 段 ms 不是数值: {ms_val!r}")
                        all_segs_numeric = False
                    else:
                        seg_sum += float(ms_val)

                total_ms = sc.get("totalMs")
                if not is_number(total_ms):
                    b_errs_6.append(f"'{sc_name}' totalMs 不是数值: {total_ms!r}")
                elif all_segs_numeric:
                    # 检查 7：自算四段之和 == totalMs（容差 0.01）
                    diff = abs(seg_sum - float(total_ms))
                    if diff > 0.01:
                        b_errs_7.append(
                            f"'{sc_name}' 四段之和 {seg_sum:.4f} != totalMs {float(total_ms):.4f}（差异 {diff:.4f} > 0.01）"
                        )

                # 检查 8：meetsMedian 与 (totalMs < 129.93) 一致
                meets_median = sc.get("meetsMedian")
                if not isinstance(meets_median, bool):
                    b_errs_8.append(f"'{sc_name}' meetsMedian 不是 bool: {meets_median!r}")
                elif is_number(total_ms):
                    expected_meets = (float(total_ms) < MEDIAN_MS)
                    if meets_median != expected_meets:
                        b_errs_8.append(
                            f"'{sc_name}' meetsMedian={meets_median} 与 (totalMs < {MEDIAN_MS})={expected_meets} 不一致"
                        )

    # 检查 6
    chk(
        6,
        b_parsed and len(b_errs_6) == 0,
        f"BUDGET_SCENARIOS.json 可解析为数组、长度 {n_scenarios} >= 3，每组含 5 键且 segments 长度 == 4 含 3 键",
        "BUDGET_SCENARIOS.json 结构不合格: " + "；".join(b_errs_6),
    )

    # 检查 7
    chk(
        7,
        b_parsed and len(b_errs_7) == 0,
        f"每组四段之和自算均等于 totalMs（容差 0.01，共 {n_scenarios} 组）",
        "预算分段累加和不自洽: " + "；".join(b_errs_7),
    )

    # 检查 8
    chk(
        8,
        b_parsed and len(b_errs_8) == 0,
        f"每组 meetsMedian 与 (totalMs < {MEDIAN_MS}) 完全一致（共 {n_scenarios} 组）",
        "meetsMedian 判定不一致: " + "；".join(b_errs_8),
    )

    # 检查 9
    chk(
        9,
        b_parsed and len(b_errs_9) == 0,
        f"每段 evidenceGrade 均在 {'/'.join(sorted(VALID_GRADES))} 之一（共 {n_scenarios * 4} 段）",
        "evidenceGrade 存在非法值: " + "；".join(b_errs_9),
    )

    # =========================================================================
    # 检查项 10：TIMING_CLARIFY_REVIEW.md 含 4 个机器可读标志
    # =========================================================================
    review_text = texts["review_md"]
    missing_flags = []
    for flag in REVIEW_FLAGS:
        key, val = flag.split(":", 1)
        pat = rf"\b{re.escape(key.strip())}\s*:\s*{re.escape(val.strip())}\b"
        if not re.search(pat, review_text):
            missing_flags.append(flag)

    chk(
        10,
        len(missing_flags) == 0,
        "复核件含全部 4 个机器可读字段（checkedEveryRow/budgetSelfConsistent/noForbiddenWording/gradesHonest: true）",
        f"复核件缺少标志字段: {'、'.join(missing_flags)}",
    )

    # =========================================================================
    # 结果汇总与退出码
    # =========================================================================
    if problems:
        print(f"\n[RESULT] FAIL — {len(problems)} 项内容不合格（exit 1）:")
        for p in problems:
            print(f"  - {p}")
        return 1

    print("\n[RESULT] PASS — 全部 10 项检查均通过（exit 0）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
