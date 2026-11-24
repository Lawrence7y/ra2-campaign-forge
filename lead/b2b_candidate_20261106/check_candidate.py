#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""check_candidate.py — B2b 候选交付件机械门禁（只读，只用标准库）。

检查项：
1) lead/b2b_candidate_20261106/qc151_trip.candidate.py /
   lead/b2b_candidate_20261106/CANDIDATE.diff /
   lead/b2b_candidate_20261106/tests/test_candidate.py /
   lead/b2b_candidate_20261106/tests/_test_out.txt /
   lead/b2b_candidate_20261106/TESTS_REPORT.md /
   lead/b2b_candidate_20261106/review/CANDIDATE_REVIEW.md 都存在且非空；
2) 候选字节数 > 399508（只增不减）；
3) 候选 ast.parse 成功；
4) ★ 脚本自己实算 out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py
   的 SHA256 与字节数，必须仍是 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636 / 399508，
   否则 FAIL；
5) lead/b2b_candidate_20261106/tests/ 下所有 .py 里不得出现 import qc151_trip 或
   from qc151_trip import（正则扫）；
6) lead/b2b_candidate_20261106/tests/_test_out.txt 末 5 行含 PASS= 与 FAIL=0；
7) lead/b2b_candidate_20261106/TESTS_REPORT.md 含「命令」「退出码」「未覆盖」三词；
8) lead/b2b_candidate_20261106/review/CANDIDATE_REVIEW.md 含:
   motherUnchanged: true
   nineHunksPresent: true
   noImportMother: true
   threeStatesDistinct: true
   testsActuallyRun: true
9) 候选里九处改动的关键锚点全部可定位（按任务书 §3 描述的 9 个关键标识逐个搜，缺一即 FAIL）。

退出码：
  0 = PASS
  1 = 内容不合格（逐条打印原因）
  2 = 文件缺失
脚本只读。
"""
from __future__ import annotations

import ast
import hashlib
import re
import sys
from pathlib import Path

# Windows 控制台防御性 UTF-8 输出
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 路径解析：支持通过命令行参数传入自身路径或默认 __file__
if len(sys.argv) > 1 and sys.argv[1].endswith(".py"):
    _script_path = Path(sys.argv[1]).resolve()
else:
    _script_path = Path(__file__).resolve()

BASE = _script_path.parent
if BASE.name != "b2b_candidate_20261106":
    candidate_base = Path.cwd() / "lead" / "b2b_candidate_20261106"
    if candidate_base.is_dir():
        BASE = candidate_base.resolve()

ROOT = BASE.parent.parent

# 交付文件清单
CANDIDATE_REL = "lead/b2b_candidate_20261106/qc151_trip.candidate.py"
DIFF_REL = "lead/b2b_candidate_20261106/CANDIDATE.diff"
TEST_PY_REL = "lead/b2b_candidate_20261106/tests/test_candidate.py"
TEST_OUT_REL = "lead/b2b_candidate_20261106/tests/_test_out.txt"
REPORT_REL = "lead/b2b_candidate_20261106/TESTS_REPORT.md"
REVIEW_REL = "lead/b2b_candidate_20261106/review/CANDIDATE_REVIEW.md"
MOTHER_REL = "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"

DELIVERY_FILES = [
    ("candidate", BASE / "qc151_trip.candidate.py", CANDIDATE_REL),
    ("diff", BASE / "CANDIDATE.diff", DIFF_REL),
    ("test_candidate", BASE / "tests" / "test_candidate.py", TEST_PY_REL),
    ("test_out", BASE / "tests" / "_test_out.txt", TEST_OUT_REL),
    ("report", BASE / "TESTS_REPORT.md", REPORT_REL),
    ("review", BASE / "review" / "CANDIDATE_REVIEW.md", REVIEW_REL),
]

MOTHER_PATH = ROOT / MOTHER_REL
TESTS_DIR = BASE / "tests"

EXPECTED_MOTHER_SHA256 = "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636"
EXPECTED_MOTHER_BYTES = 399508

ANCHORS = [
    ("H1", 'FRESHNESS_GROUP = "FRESHNESS"', "模块顶层注入 F 命名空间常量"),
    ("H2", "backup_mtime_pre:{name}", "backup_carrier 记 RESTORE.backup_mtime_pre，保持 bak[name] 三键"),
    ("H3", "def make_pre_freshness_snapshot(except_path: Path) -> dict:", "前置定义快照构造 + 新鲜性判定函数；扩展签名 pre_snapshot=None"),
    ("H4", "def copy_post_except_evidence(", "copy_post_except_evidence 三出口全量落盘 7 个 FRESHNESS + 12 键 info"),
    ("H5", "pre_freshness_snapshot: dict | None = None) -> int:", "finalize_trip 末尾追加 pre_freshness_snapshot: dict | None = None"),
    ("H6", "pre_freshness_snapshot=pre_freshness_snapshot", ":5939 调用点显式传参"),
    ("H7", "_pre_freshness_snapshot: dict | None = None", "main 内 try 之前预初始化 _pre_freshness_snapshot = None"),
    ("H8", "_pre_freshness_snapshot = make_pre_freshness_snapshot(", "备份后（:6388）、进程启动前构造快照"),
    ("H9", "pre_freshness_snapshot=_pre_freshness_snapshot", "finally 里把快照传入 finalize_trip"),
]


def main() -> int:
    print("=" * 70)
    print("B2b 候选确定性门禁自检")
    print("=" * 70)
    print(f"[BASE] {BASE}")
    print(f"[ROOT] {ROOT}")

    missing_files: list[str] = []
    content_failures: list[str] = []
    passes: list[str] = []

    # 1. 前置检查：检查 1 中 6 个交付件以及母本文件是否存在
    for key, path, rel in DELIVERY_FILES:
        if not path.is_file():
            missing_files.append(f"交付件缺失: {rel} ({path})")

    if not MOTHER_PATH.is_file():
        missing_files.append(f"母本文件缺失: {MOTHER_REL} ({MOTHER_PATH})")

    if missing_files:
        for m in missing_files:
            print(f"[MISSING] {m}")
        print("=" * 70)
        print(f"FAILED (EXIT=2): 共有 {len(missing_files)} 个必要文件缺失")
        print("=" * 70)
        return 2

    # 检查 1: 6 个交付件必须非空
    empty_files = []
    for key, path, rel in DELIVERY_FILES:
        try:
            sz = path.stat().st_size
            if sz == 0:
                empty_files.append(rel)
        except OSError as e:
            content_failures.append(f"无法访问文件: {rel} ({e})")
    if empty_files:
        content_failures.append(f"[1] 交付件为空: {', '.join(empty_files)}")
    else:
        passes.append("[1] 6 个交付件均存在且非空")

    # 检查 2: 候选字节数 > 399508（只增不减）
    cand_path = BASE / "qc151_trip.candidate.py"
    cand_bytes = cand_path.stat().st_size
    if cand_bytes <= EXPECTED_MOTHER_BYTES:
        content_failures.append(f"[2] 候选副本字节数 ({cand_bytes}) 必须严格大于母本 ({EXPECTED_MOTHER_BYTES})")
    else:
        passes.append(f"[2] 候选副本字节数 = {cand_bytes} B (> {EXPECTED_MOTHER_BYTES} B, 只增不减)")

    # 检查 3: 候选 ast.parse 成功
    cand_text = ""
    try:
        cand_text = cand_path.read_text(encoding="utf-8")
        ast.parse(cand_text, filename=str(cand_path))
        passes.append("[3] 候选副本 ast.parse 语法解析成功 (0 语法错误)")
    except Exception as exc:
        content_failures.append(f"[3] 候选副本 ast.parse 失败: {exc}")

    # 检查 4: ★ 脚本自己实算母本 SHA256 与字节数
    try:
        m_data = MOTHER_PATH.read_bytes()
        m_sha = hashlib.sha256(m_data).hexdigest()
        m_bytes = len(m_data)
        if m_sha != EXPECTED_MOTHER_SHA256 or m_bytes != EXPECTED_MOTHER_BYTES:
            content_failures.append(
                f"[4] 母本发生改变！期望 {EXPECTED_MOTHER_SHA256}/{EXPECTED_MOTHER_BYTES} B，"
                f"实际 {m_sha}/{m_bytes} B"
            )
        else:
            passes.append(f"[4] 母本 SHA256 与字节数零漂移实算核验通过 ({m_sha} / {m_bytes} B)")
    except Exception as exc:
        content_failures.append(f"[4] 读取母本失败: {exc}")

    # 检查 5: tests/ 下所有 .py 里不得出现 import qc151_trip 或 from qc151_trip import
    test_py_files = sorted(TESTS_DIR.glob("*.py"))
    if not test_py_files:
        content_failures.append("[5] tests/ 目录下未发现任何 .py 测试脚本")
    else:
        bad_imports = []
        for pf in test_py_files:
            try:
                txt = pf.read_text(encoding="utf-8")
                m1 = re.findall(r"^\s*import\s+qc151_trip\b.*", txt, re.MULTILINE)
                m2 = re.findall(r"^\s*from\s+qc151_trip\b.*import.*", txt, re.MULTILINE)
                if m1 or m2:
                    bad_imports.append((pf.name, m1 + m2))
            except Exception as exc:
                content_failures.append(f"[5] 读取测试文件 {pf.name} 失败: {exc}")
        if bad_imports:
            for fname, matches in bad_imports:
                content_failures.append(f"[5] 测试脚本 {fname} 包含违规 import 母本语句: {matches}")
        else:
            passes.append(f"[5] tests/ 下 {len(test_py_files)} 个测试脚本经正则扫描，零处 import 母本")

    # 检查 6: tests/_test_out.txt 末 5 行含 PASS= 与 FAIL=0
    test_out_path = BASE / "tests" / "_test_out.txt"
    try:
        out_lines = test_out_path.read_text(encoding="utf-8").splitlines()
        tail_5 = out_lines[-5:] if len(out_lines) >= 5 else out_lines
        tail_joined = "\n".join(tail_5)
        # 也兜底检查末 5 个非空行
        non_empty = [l for l in out_lines if l.strip()]
        tail_5_ne = non_empty[-5:] if len(non_empty) >= 5 else non_empty
        tail_ne_joined = "\n".join(tail_5_ne)

        has_pass = ("PASS=" in tail_joined) or ("PASS=" in tail_ne_joined)
        has_fail_0 = ("FAIL=0" in tail_joined) or ("FAIL=0" in tail_ne_joined)

        if not has_pass or not has_fail_0:
            content_failures.append(f"[6] _test_out.txt 末 5 行未同时包含 'PASS=' 与 'FAIL=0' (实际末尾:\n{tail_joined})")
        else:
            passes.append("[6] _test_out.txt 末 5 行包含 PASS= 与 FAIL=0")
    except Exception as exc:
        content_failures.append(f"[6] 读取 _test_out.txt 失败: {exc}")

    # 检查 7: TESTS_REPORT.md 含「命令」「退出码」「未覆盖」三词
    report_path = BASE / "TESTS_REPORT.md"
    try:
        rep_text = report_path.read_text(encoding="utf-8")
        missing_kw = [kw for kw in ["命令", "退出码", "未覆盖"] if kw not in rep_text]
        if missing_kw:
            content_failures.append(f"[7] TESTS_REPORT.md 缺失关键字: {', '.join(missing_kw)}")
        else:
            passes.append("[7] TESTS_REPORT.md 包含「命令」「退出码」「未覆盖」三词")
    except Exception as exc:
        content_failures.append(f"[7] 读取 TESTS_REPORT.md 失败: {exc}")

    # 检查 8: review/CANDIDATE_REVIEW.md 含 5 个指定键值
    review_path = BASE / "review" / "CANDIDATE_REVIEW.md"
    try:
        rev_text = review_path.read_text(encoding="utf-8")
        req_keys = [
            "motherUnchanged: true",
            "nineHunksPresent: true",
            "noImportMother: true",
            "threeStatesDistinct: true",
            "testsActuallyRun: true",
        ]
        missing_keys = [k for k in req_keys if k not in rev_text]
        if missing_keys:
            content_failures.append(f"[8] CANDIDATE_REVIEW.md 缺失必填键值: {', '.join(missing_keys)}")
        else:
            passes.append("[8] CANDIDATE_REVIEW.md 包含 5 个指定核验键值")
    except Exception as exc:
        content_failures.append(f"[8] 读取 CANDIDATE_REVIEW.md 失败: {exc}")

    # 检查 9: 候选里九处改动的关键锚点全部可定位
    if cand_text:
        missing_anchors = []
        for hid, token, desc in ANCHORS:
            if token not in cand_text:
                missing_anchors.append(f"{hid} ({desc}): 未找到 '{token}'")
        if missing_anchors:
            for ma in missing_anchors:
                content_failures.append(f"[9] 候选副本关键锚点缺失: {ma}")
        else:
            passes.append("[9] 候选副本九处改动的关键锚点全部可定位 (9/9 锚点定位成功)")
    else:
        content_failures.append("[9] 候选副本内容为空或未读入，无法核验锚点")

    # 打印通过项
    for p in passes:
        print(f"PASS {p}")

    # 判定输出
    print("=" * 70)
    if content_failures:
        print(f"FAILED (EXIT=1): 共有 {len(content_failures)} 项内容不合格：")
        for cf in content_failures:
            print(f"  - {cf}")
        print("=" * 70)
        return 1

    print("ALL 9 GATES PASSED! EXIT=0")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
