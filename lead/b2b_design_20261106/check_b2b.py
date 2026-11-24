#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""check_b2b.py — B2b 设计交付件的机械门禁（只读，只用标准库）。

运行（在仓库根、隔离模式；传给解释器的参数就是本脚本自身的路径）：
    python -I -X utf8 lead/b2b_design_20261106/check_b2b.py

退出码： 0 = PASS ；1 = 内容不合格（逐条打印原因）；2 = 文件缺失/为空。

定位以 __file__ 为准，不依赖 cwd / PYTHONPATH（-I 下两者均不可靠）；
脚本只读文件，不写任何文件，不解析命令行参数（sys.argv[0] 即自身路径）。
"""
import json
import re
import sys
from pathlib import Path

SELF = Path(__file__).resolve()
BASE = SELF.parent  # lead/b2b_design_20261106/

# (键, 绝对路径, 用于打印的仓库相对路径)
TARGETS = [
    ("design",   BASE / "B2B_DESIGN.md",
     "lead/b2b_design_20261106/B2B_DESIGN.md"),
    ("matrix",   BASE / "STATE_MATRIX.json",
     "lead/b2b_design_20261106/STATE_MATRIX.json"),
    ("probe",    BASE / "_b2b_probe.py",
     "lead/b2b_design_20261106/_b2b_probe.py"),
    ("probeout", BASE / "_b2b_probe_out.txt",
     "lead/b2b_design_20261106/_b2b_probe_out.txt"),
    ("review",   BASE / "review" / "B2B_DESIGN_REVIEW.md",
     "lead/b2b_design_20261106/review/B2B_DESIGN_REVIEW.md"),
]

SEP_RE = re.compile(r"\|?[\s:\-|]+\|?")


def is_sep(s):
    """markdown 表格分隔行：必须含 '|'，只由 | : - 空白组成，且至少含一个 '-'。

    必须要求 '|'：否则纯 '---' 水平分隔线（章节间常见）会被误判为表格
    分隔行，进而把它上方最近的表格数据行错当表头排除。
    """
    return "|" in s and "-" in s and SEP_RE.fullmatch(s) is not None


def table_data_rows(sec):
    """表格数据行 = 以 | 开头、非分隔行、且不是表头（分隔行前紧邻的表格行）。"""
    s = [line.strip() for line in sec]
    header_idx = set()
    for i, line in enumerate(s):
        if is_sep(line):
            for j in range(i - 1, -1, -1):
                if s[j] == "":
                    continue
                if s[j].startswith("|"):
                    header_idx.add(j)
                break
    return [line for i, line in enumerate(s)
            if line.startswith("|") and not is_sep(line) and i not in header_idx]


def section(lines, num):
    """'## <num> ' 标题之后、下一个 '## ' 标题之前的行；找不到返回 None。"""
    pat = re.compile(r"^##\s+" + str(num) + r"(?!\d)")
    start = next((i for i, line in enumerate(lines) if pat.match(line)), None)
    if start is None:
        return None
    end = next((j for j in range(start + 1, len(lines))
                if re.match(r"^##\s+", lines[j])), len(lines))
    return lines[start + 1:end]


def main():
    print("[BASE] " + str(BASE))

    # ---- 检查 1：五个交付文件存在且非空（前置条件，失败即退出码 2）----
    texts, missing = {}, []
    for key, path, rel in TARGETS:
        if not path.is_file():
            missing.append(rel + " : 文件不存在")
            continue
        if path.stat().st_size == 0:
            missing.append(rel + " : 文件为空")
            continue
        try:
            texts[key] = path.read_text(encoding="utf-8")
        except Exception as exc:
            missing.append(rel + " : 无法读取 (" + str(exc) + ")")
    if missing:
        for msg in missing:
            print("[MISSING] " + msg)
        print("[CHECK 1] FAIL — %d 个交付文件缺失/为空/不可读" % len(missing))
        print("[RESULT] 文件缺失")
        return 2
    print("[CHECK 1] PASS — 5 个交付文件均存在且非空")

    problems = []

    def chk(num, ok, okmsg, failmsg):
        if ok:
            print("[CHECK %s] PASS — %s" % (num, okmsg))
        else:
            print("[CHECK %s] FAIL — %s" % (num, failmsg))
            problems.append("%s) %s" % (num, failmsg))

    lines = texts["design"].splitlines()

    # ---- 检查 2：设计头部含 3 个不同 64-hex + 3 个字节数 ----
    # “头部” = 从文件开头到第一个数字编号二级标题（## 0 …）之前。
    head_end = next((i for i, line in enumerate(lines)
                     if re.match(r"^##\s+\d", line)), len(lines))
    header = "\n".join(lines[:head_end])
    hexes = set(h.lower() for h in re.findall(
        r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{64}(?![0-9A-Fa-f])", header))
    # 字节数来源 A：`399508 B` / `13,190 B`（带 B 标注）
    b1 = re.findall(r"(?<![\d,])(\d[\d,]*)\s*B\b", header)
    # 字节数来源 B：实算输出行 “<64hex> <bytes> <lines> <path>”
    b2 = re.findall(r"^\s*[0-9A-Fa-f]{64}\s+(\d+)\s+\d+\s+\S.*$", header, re.M)
    byte_vals = set(v.replace(",", "") for v in b1 + b2)
    chk(2, len(hexes) >= 3 and len(byte_vals) >= 3,
        "头部含 %d 个不同 64-hex、%d 个字节数（各需 >= 3）"
        % (len(hexes), len(byte_vals)),
        "头部不同 64-hex = %d、不同字节数 = %d（各需 >= 3）"
        % (len(hexes), len(byte_vals)))

    # ---- 检查 3：## 1 下 >= 10 个以 #### 开头的标题 ----
    sec1 = section(lines, 1)
    n_h4 = len([line for line in sec1
                if re.match(r"^####\s", line)]) if sec1 is not None else -1
    chk(3, n_h4 >= 10,
        "## 1 下 %d 个 #### 标题（需 >= 10）" % n_h4,
        "## 1 下 #### 标题 = %d（需 >= 10；章节缺失记 -1）" % n_h4)

    # ---- 检查 4：## 2 与 ## 3 各 >= 7 行表格数据行 ----
    for tag, num in (("4a", 2), ("4b", 3)):
        sec = section(lines, num)
        cnt = len(table_data_rows(sec)) if sec is not None else -1
        chk(tag, cnt >= 7,
            "## %d 表格数据行 = %d（需 >= 7）" % (num, cnt),
            "## %d 表格数据行 = %d（需 >= 7；章节缺失记 -1）" % (num, cnt))

    # ---- 检查 5：## 7 对照表数据行数 == 全文以 @@ 开头的行数 ----
    sec7 = section(lines, 7)
    n7 = len(table_data_rows(sec7)) if sec7 is not None else -1
    n_at = len([line for line in lines if line.startswith("@@")])
    chk(5, sec7 is not None and n7 == n_at,
        "## 7 数据行 = %d == 全文 @@ 行数 = %d" % (n7, n_at),
        "## 7 数据行 = %d != 全文 @@ 行数 = %d（或 ## 7 缺失）" % (n7, n_at))

    # ---- 检查 6：## 8 正文非空 ----
    sec8 = section(lines, 8)
    body = "\n".join(sec8).strip() if sec8 is not None else ""
    chk(6, len(body) > 0,
        "## 8 正文 %d 字符（非空）" % len(body),
        "## 8 正文为空或 ## 8 章节缺失")

    # ---- 检查 7：STATE_MATRIX.json 可解析为数组、长度 >= 8、每条 >= 5 键 ----
    parsed, data = False, None
    try:
        data = json.loads(texts["matrix"])
        parsed = True
    except Exception as exc:
        chk(7, False, "", "STATE_MATRIX.json 不能解析为 JSON: " + str(exc))
    if parsed:
        msgs, ok = [], True
        if not isinstance(data, list):
            ok = False
            msgs.append("顶层类型是 %s，不是数组" % type(data).__name__)
        else:
            if len(data) < 8:
                ok = False
                msgs.append("数组长度 %d < 8" % len(data))
            bad = [i + 1 for i, item in enumerate(data)
                   if not isinstance(item, dict) or len(item) < 5]
            if bad:
                ok = False
                msgs.append("第 %s 项不是对象或键数 < 5" % bad)
        n = len(data) if isinstance(data, list) else "N/A"
        chk(7, ok, "数组 %s 项、每条 >= 5 键" % n, "；".join(msgs))

    # ---- 检查 8：不存在 confidence=high 且 state 含 unknown 的项 ----
    viol = []
    if parsed and isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                conf = str(item.get("confidence", "")).strip().lower()
                state = str(item.get("state", "")).lower()
                if conf == "high" and "unknown" in state:
                    viol.append("第 %d 项 state=%r confidence=%r"
                                % (i + 1, item.get("state"),
                                   item.get("confidence")))
    chk(8, parsed and isinstance(data, list) and not viol,
        "无 confidence=high 且 state 含 unknown 的项",
        ("发现违规映射：" + "；".join(viol)) if viol
        else "矩阵未解析为数组，无法判定违规映射")

    # ---- 检查 9：复核件四个机器可读字段 ----
    need_tokens = [
        "checkedEveryRow: true",
        "hunksMatchManifest: true",
        "earlyReturnsCovered: 5/5",
        "unknownToHigh: false",
    ]
    miss_tok = [t for t in need_tokens if t not in texts["review"]]
    chk(9, not miss_tok,
        "复核件含全部 4 个机器可读字段",
        "复核件缺字段：" + "、".join(miss_tok))

    # ---- 汇总 ----
    if problems:
        print("[RESULT] FAIL — %d 项内容不合格（原因已逐条打印于上）"
              % len(problems))
        return 1
    print("[RESULT] PASS — 全部检查项通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
