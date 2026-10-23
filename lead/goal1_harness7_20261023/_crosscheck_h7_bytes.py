#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""H7 独立复核（第二实现，与 _verify_h7_behavior.py 不同路）。

★ 目的：主验证器用 AST 取值 + 模型求值；本件改用**逐行文本扫描 + 字节级比对**，
  两条路互不共享代码，用来抓「主验证器与产物共享同一盲区」这类错误。

★ 只读：不 import / 不 exec / 不写任何被检文件。

六项
----
R1  母本 while 行在副本里逐字节存在且唯一（文本扫描，非 AST）
R2  `deadline` 在副本 while 行之后的可执行行零引用（逐行 strip 判注释）
R3  副本相对母本的 diff 只有新增行（逐行序列比对，非 Counter 行多重集）
R4  两个文件的 EXIT_ 常量集合完全相同（逐行正则）
R5  内核函数体在副本里逐字节保留（按 def 边界切片后做子串包含判断）
R6  late_start 相关的三处字面量在同一分支内且取值自洽
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
H6 = ROOT / "lead/goal1_harness6_20261022/qc151_trip.harness6.py"
H7 = ROOT / "lead/goal1_harness7_20261023/qc151_trip.harness7.py"

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))


def executable_lines(text):
    """返回 (行号, 行内容) —— 跳过空行与以 # 开头的行。"""
    for i, ln in enumerate(text.split("\n"), 1):
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        yield i, ln


def main():
    if not (H6.exists() and H7.exists()):
        print("ABORT: missing artifact")
        return 1
    t6 = H6.read_text(encoding="utf-8")
    t7 = H7.read_text(encoding="utf-8")
    l6 = t6.split("\n")
    l7 = t7.split("\n")

    print("=" * 72)
    print("R1 母本 while 行逐字节存在且唯一")
    # ★ 用母本里**实际存在**的那一行，不从别处抄
    while_lines = [ln for ln in l6
                   if ln.strip().startswith("while (_cap_rect[2] - _cap_rect[0]")]
    check("R1a 母本恰有 1 条目标 while 行", len(while_lines) == 1,
          f"found={len(while_lines)}")
    if len(while_lines) != 1:
        return 1
    WL = while_lines[0]
    n7 = t7.count(WL)
    check("R1b 副本保留同一行且唯一", n7 == 1, f"count={n7}")
    print(f"     行内容: {WL.strip()[:90]}...")

    print("=" * 72)
    print("R2 `deadline` 在该 while 之后可执行行零引用")
    idx = next(i for i, ln in enumerate(l7) if ln == WL)
    refs = [(i + 1, ln) for i, ln in executable_lines("\n".join(l7[idx + 1:]))]
    hits = [(i, ln) for i, ln in refs if "deadline" in ln]
    check("R2 零引用", len(hits) == 0, f"refs={len(hits)}")
    for i, ln in hits[:3]:
        print(f"     ref L{idx + 1 + i}: {ln.strip()[:90]}")

    print("=" * 72)
    print("R3 副本相对母本只有新增行（逐行序列比对）")
    # ★ 用 difflib 的真实 opcodes，而不是行多重集（Counter 会漏「换位置」）
    import difflib
    sm = difflib.SequenceMatcher(None, l6, l7, autojunk=False)
    ops = sm.get_opcodes()
    deletes = [(tag, i1, i2) for tag, i1, i2, _j1, _j2 in ops if tag in ("delete", "replace")]
    check("R3 无 delete/replace 块", len(deletes) == 0, f"blocks={len(deletes)}")
    inserts = sum(j2 - j1 for tag, _i1, _i2, j1, j2 in ops if tag == "insert")
    check("R3b 纯新增行数 == 文件行数差",
          inserts == len(l7) - len(l6),
          f"insert={inserts} delta={len(l7) - len(l6)}")

    print("=" * 72)
    print("R4 EXIT_ 常量集合两文件完全相同")
    def exits(text):
        return {m.group(1) for m in re.finditer(r"^(EXIT_[A-Z0-9_]+)\s*=", text, re.M)}
    e6, e7 = exits(t6), exits(t7)
    check("R4a 新增退出码为空", not (e7 - e6), f"added={sorted(e7 - e6) or 'none'}")
    check("R4b 删除退出码为空", not (e6 - e7), f"removed={sorted(e6 - e7) or 'none'}")
    check("R4c 集合大小一致", len(e6) == len(e7), f"h6={len(e6)} h7={len(e7)}")

    print("=" * 72)
    print("R5 内核函数体逐字节保留（def 边界切片 + 子串包含）")
    KERNELS = ["_measure_stats", "_measure_write_json", "_measure_error_payload",
               "capture_frame_desktop", "_fs_arrival_poll", "terminate_owned_process"]

    def body(text, name):
        m = re.search(r"^def %s\(.*?(?=^def |^# =====)" % re.escape(name),
                      text, re.S | re.M)
        return m.group(0) if m else None

    for k in KERNELS:
        b6 = body(t6, k)
        if b6 is None:
            check(f"R5 {k} 母本可定位", False, "not found in mother")
            return 1
        present = b6 in t7
        check(f"R5 {k} 函数体原样保留", present,
              "byte-identical substring" if present else "CHANGED")

    print("=" * 72)
    print("R6 late_start 三处字面量自洽")
    check("R6a payload verdict 被改写",
          '_h7_payload["verdict"] = "late_start"' in t7, "")
    check("R6b rec 行记 late_start",
          'rec.add("MEASURE", "verdict", "late_start", "script:_measure_run"' in t7, "")
    check("R6c 写入用的错误文案含 late_start",
          '"late_start: nav→measure' in t7 or "late_start: nav" in t7, "")
    # ★ 三处必须都在同一个 if _h7_late: 分支内
    branch = re.search(r"            if _h7_late:\n(.*?)(?=\n        # <<< H7-END late-start-gate)",
                       t7, re.S)
    if branch is None:
        check("R6d 三处同处一分支", False, "branch not located")
    else:
        blk = branch.group(1)
        check("R6d 三处同处一分支",
              all(s in blk for s in ('_h7_payload["verdict"] = "late_start"',
                                     'rec.add("MEASURE", "verdict", "late_start"',
                                     "late_start: nav")),
              f"branch bytes={len(blk)}")

    print("=" * 72)
    npass = sum(1 for _, ok, _ in results if ok)
    print(f"TOTAL {npass}/{len(results)} PASS")
    return 0 if npass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
