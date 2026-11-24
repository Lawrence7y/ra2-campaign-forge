#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""check_d13b.py — D-13b 设计交付件的机械门禁（只读，只用标准库）。

运行（在仓库根、隔离模式；传给解释器的参数就是本脚本自身的路径）：
    python -I -X utf8 lead/d13b_design_20261106/check_d13b.py

退出码： 0 = PASS ；1 = 内容不合格（逐条打印原因）；2 = 文件缺失/为空/不可读。

定位以 __file__ 为准，不依赖 cwd / PYTHONPATH（-I 下两者均不可靠）；
不解析命令行参数（sys.argv[0] 即自身路径），不写任何文件。
"""
import json
import re
import sys
from pathlib import Path

# 中文输出在部分 Windows 控制台代码页下会抛 UnicodeEncodeError；
# 只调整本进程标准流的编码，不涉及任何文件写入。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

SELF = Path(__file__).resolve()
BASE = SELF.parent                    # lead/d13b_design_20261106/
REPO = BASE.parent.parent            # 仓库根（仅用于打印）
REL_DIR = "lead/d13b_design_20261106"

# (键, 绝对路径, 用于打印的仓库相对路径)
TARGETS = (
    ("design",  BASE / "D13B_DESIGN.md",
     REL_DIR + "/D13B_DESIGN.md"),
    ("budget",  BASE / "BUDGET_MODEL.json",
     REL_DIR + "/BUDGET_MODEL.json"),
    ("state",   BASE / "_state_machine.py",
     REL_DIR + "/_state_machine.py"),
    ("test",    BASE / "_test_state_machine.py",
     REL_DIR + "/_test_state_machine.py"),
    ("testout", BASE / "_test_out.txt",
     REL_DIR + "/_test_out.txt"),
    ("review",  BASE / "review" / "D13B_DESIGN_REVIEW.md",
     REL_DIR + "/review/D13B_DESIGN_REVIEW.md"),
)
RELS = {key: rel for key, _path, rel in TARGETS}

# 检查 2：五个二级小节标题（允许标题内空白有差异）
HEADINGS = (
    (r"^##\s+1\s+完整时间预算\s*$", "## 1 完整时间预算"),
    (r"^##\s+2\s+剩余覆盖检验\s*$", "## 2 剩余覆盖检验"),
    (r"^##\s+3\s+纯模型单测\s*$", "## 3 纯模型单测"),
    (r"^##\s+4\s+未验\s*$",       "## 4 未验"),
    (r"^##\s+5\s+指标定位\s*$",   "## 5 指标定位"),
)
SEC4_HEAD = r"^##\s+4\s+未验\s*$"
SEC4_WORDS = ("系统时延", "扰动", "资源释放", "栈")
MARKER_RE = re.compile(r"\[待论证指标\]|\[估算\]")
BUDGET_KEYS = ("segments", "totalMs", "meetsMedian", "gapToMedian")
FORBIDDEN = (
    "ctypes", "OpenProcess", "ReadProcessMemory", "WriteProcessMemory",
    "VirtualAllocEx", "CreateRemoteThread", "SetWindowsHook", "MiniDump",
    "SuspendThread", "StackWalk", "TerminateProcess",
)
REVIEW_FLAGS = (
    "checkedEveryRow: true",
    "noSamplingCode: true",
    "budgetSelfConsistent: true",
    "coversUnverified: true",
)


def section_body(lines, head_pat):
    """返回该二级标题之后、下一个一级/二级标题之前的正文；找不到返回 None。

    '^#{1,2}(?:\\s|$)' 只截一/二级标题，三级及以下小标题仍属于本节正文。
    """
    start = next((i for i, line in enumerate(lines)
                  if re.match(head_pat, line)), None)
    if start is None:
        return None
    end = start + 1
    while end < len(lines) and not re.match(r"^#{1,2}(?:\s|$)", lines[end]):
        end += 1
    return "\n".join(lines[start + 1:end])


def is_number(value):
    """JSON 数值（排除 bool，它是 int 的子类）。"""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def main():
    print("[SELF] " + str(SELF))
    print("[BASE] " + str(BASE))
    print("[REPO] " + str(REPO))
    print("[CWD]  " + str(Path.cwd()))
    print("[ARGV0] " + (sys.argv[0] if sys.argv else "(none)"))
    print("[ISOLATED] %s" % bool(getattr(sys.flags, "isolated", False)))

    # ---- 检查 1：六个交付文件存在且非空（前置条件，失败即退出码 2）----
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
        except (OSError, UnicodeError) as exc:
            missing.append(rel + " : 无法按 UTF-8 读取 (" + str(exc) + ")")
    if missing:
        for msg in missing:
            print("[MISSING] " + msg)
        print("[CHECK 1] FAIL — %d 个交付文件缺失/为空/不可读" % len(missing))
        print("[RESULT] 文件缺失（exit 2）")
        return 2
    print("[CHECK 1] PASS — 6 个交付文件均存在且非空")

    problems = []

    def chk(num, ok, okmsg, failmsg):
        if ok:
            print("[CHECK %s] PASS — %s" % (num, okmsg))
        else:
            print("[CHECK %s] FAIL — %s" % (num, failmsg))
            problems.append("%s) %s" % (num, failmsg))

    design_lines = texts["design"].splitlines()

    # ---- 检查 2：主设计含五个小节标题 ----
    miss_h = [label for pat, label in HEADINGS
              if not any(re.match(pat, line) for line in design_lines)]
    chk(2, not miss_h,
        "五个小节标题齐全",
        "主设计缺小节标题：" + "、".join(miss_h))

    # ---- 检查 3：「## 4 未验」正文同时含四个词 ----
    sec4 = section_body(design_lines, SEC4_HEAD)
    if sec4 is None:
        chk(3, False, "", "主设计中找不到「## 4 未验」小节")
    else:
        miss_w = [w for w in SEC4_WORDS if w not in sec4]
        chk(3, not miss_w,
            "## 4 未验 正文 %d 字符，四词齐全" % len(sec4),
            "## 4 未验 正文缺词：" + "、".join(miss_w))

    # ---- 检查 4：全文 [待论证指标] 或 [估算] 至少 3 处 ----
    n_markers = len(MARKER_RE.findall(texts["design"]))
    chk(4, n_markers >= 3,
        "主设计全文标注 %d 处（需 >= 3）" % n_markers,
        "主设计全文标注仅 %d 处（需 >= 3）" % n_markers)

    # ---- 检查 5：BUDGET_MODEL.json 可解析、键齐全、各段之和 == totalMs ----
    msgs5, parsed, data = [], False, None
    try:
        data = json.loads(texts["budget"])
        parsed = True
    except Exception as exc:
        msgs5.append("BUDGET_MODEL.json 不能解析为 JSON: " + str(exc))
    if parsed:
        if not isinstance(data, dict):
            msgs5.append("顶层类型是 %s，不是对象" % type(data).__name__)
        else:
            miss_k = [k for k in BUDGET_KEYS if k not in data]
            if miss_k:
                msgs5.append("缺键：" + "、".join(miss_k))
            segments = data.get("segments")
            seg_sum = None
            if not isinstance(segments, list):
                msgs5.append("segments 类型是 %s，不是数组"
                             % type(segments).__name__)
            else:
                if len(segments) < 4:
                    msgs5.append("segments 段数 %d < 4" % len(segments))
                bad = [i + 1 for i, seg in enumerate(segments)
                       if not (isinstance(seg, dict)
                               and is_number(seg.get("ms")))]
                if bad:
                    msgs5.append("第 %s 段非对象或 ms 非数值"
                                 % ",".join(str(i) for i in bad))
                else:
                    seg_sum = sum(seg["ms"] for seg in segments)
            total = data.get("totalMs")
            if not is_number(total):
                msgs5.append("totalMs 非数值：%r" % (total,))
            elif seg_sum is not None:
                if abs(float(seg_sum) - float(total)) > 0.01:
                    msgs5.append("各段之和 %.4f != totalMs %.4f（容差 0.01）"
                                 % (float(seg_sum), float(total)))
            n_seg = len(segments) if isinstance(segments, list) else "N/A"
            sum_txt = ("%.4f" % float(seg_sum)) if seg_sum is not None else "N/A"
            tot_txt = ("%.4f" % float(total)) if is_number(total) else "N/A"
            print("[CHECK 5] 自算：segments=%s 段, sum=%s, totalMs=%s"
                  % (n_seg, sum_txt, tot_txt))
    chk(5, parsed and not msgs5,
        "JSON 可解析、4 键齐全、segments>=4 且各段之和自洽",
        "；".join(msgs5))

    # ---- 检查 6：_test_out.txt 末 5 行内含 PASS= 与 FAIL=0 ----
    tail_lines = texts["testout"].splitlines()[-5:]
    tail = "\n".join(tail_lines)
    has_pass, has_fail0 = "PASS=" in tail, "FAIL=0" in tail
    print("[CHECK 6] 末 5 行：%r" % (tail_lines,))
    chk(6, has_pass and has_fail0,
        "末 5 行含 PASS= 与 FAIL=0",
        "末 5 行缺：" + "、".join(
            t for t, present in (("PASS=", has_pass), ("FAIL=0", has_fail0))
            if not present))

    # ---- 检查 7：反扫描，两个 .py 不得出现采样/注入类标识符 ----
    hits7 = []
    for key in ("state", "test"):
        lowered = texts[key].lower()
        for token in FORBIDDEN:
            if token.lower() in lowered:
                hits7.append(RELS[key] + " 命中 " + token)
    chk(7, not hits7,
        "两个 .py 共 %d 个文件 × %d 个禁用标识符零命中"
        % (2, len(FORBIDDEN)),
        "反扫描命中：" + "；".join(hits7))

    # ---- 检查 8：复核件四个机器可读字段 ----
    miss8 = [flag for flag in REVIEW_FLAGS if flag not in texts["review"]]
    chk(8, not miss8,
        "复核件含全部 4 个机器可读字段",
        "复核件缺字段：" + "、".join(miss8))

    # ---- 汇总 ----
    if problems:
        print("[RESULT] FAIL — %d 项内容不合格（exit 1）" % len(problems))
        for problem in problems:
            print("  - " + problem)
        return 1
    print("[RESULT] PASS — 全部 8 项检查通过（exit 0）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
