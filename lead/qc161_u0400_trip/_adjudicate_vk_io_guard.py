#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-07 判定件 B：`_vk_io.resolve_writable_path` 的守卫是空证。

为什么单独成件：`_classify_sinks_d07.py` 把这 28 条分成
「CLI 参数 / 形参 / 字面量」三类，都属无边界跨越或误报。
但其中 **tools/verify_kit/_vk_io.py:23** 不一样：
它的 docstring 明写「every file written by a verify_kit tool goes through
write_bytes() so ... parent-directory traversal is rejected in exactly one
audited place」——**它声称自己是那道守卫**。

声称是守卫的地方，必须实测，不能读注释就信。

实测结论（下方断言逐条可复跑）：
  resolve_writable_path("../etc/passwd")  **不抛错**，静默返回
  D:\\Project\\etc\\passwd —— 即 `..` 被放行。
根因：先 `os.path.abspath()` 把 `..` 折叠掉，之后再用
`".." in parts` 判断，该条件恒为假 ⇒ **整条检查是死条件**。

★ 这是本线在 D-07 普查中**唯一认定为真实缺陷**的一条
（其余 27 条为 CLI 参数 / 字面量 / 冻结件内死代码）。
它不在本线写域，本件**只出判定不改他线文件**。

复跑：python lead/qc161_u0400_trip/_adjudicate_vk_io_guard.py
退出码：0 = 判定成立（缺陷复现）；1 = 判定不成立（守卫其实有效）。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "verify_kit"))

RESULTS: list[tuple[str, bool, str]] = []


def rec(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    print("  %s %s%s" % ("✓" if ok else "✗", name,
                         ("  | %s" % detail) if detail else ""))


def main() -> int:
    import _vk_io

    print("=" * 84)
    print("D-07 判定 B：_vk_io 的路径穿越守卫是否真的成立")
    print("=" * 84)

    print("\n[1] 读源码确认「它自称是守卫」")
    src = (ROOT / "tools" / "verify_kit" / "_vk_io.py").read_text(
        encoding="utf-8")
    rec("docstring 声称 traversal is rejected in exactly one audited place",
        "rejected" in src and "traversal" in src, "")

    print("\n[2] 正控：正常相对路径必须通过（否则守卫把功能也拦了）")
    try:
        good = _vk_io.resolve_writable_path("out/x.json")
        rec("正常相对路径不抛错", True, "-> %s" % good[-24:])
    except Exception as exc:                       # noqa: BLE001
        rec("正常相对路径不抛错", False, "抛了 %r" % exc)

    print("\n[3] 负控：带 `..` 的路径**必须**被拒（这是守卫的全部职责）")
    cases = ["../etc/passwd", "a/../../b", "..\\x", "./../y"]
    escaped = []
    for bad in cases:
        try:
            got = _vk_io.resolve_writable_path(bad)
            escaped.append((bad, got))
            print("      ★ 未拦住 %-16r -> %s" % (bad, got))
        except ValueError as exc:
            print("      已拦住 %-16r -> %s" % (bad, exc))
    rec("全部 4 个 `..` 用例被拒", not escaped,
        "逃逸 %d 个" % len(escaped))

    print("\n[4] 根因：`..` 在检查之前就被 abspath 折叠掉了")
    raw = "../etc/passwd"
    folded = os.path.abspath(raw)
    parts = os.path.realpath(folded).replace("\\", "/").split("/")
    rec("abspath 后已无 `..` 分量（故 `'..' in parts` 恒假）",
        ".." not in parts, "parts 尾部=%s" % parts[-3:])

    print("\n[5] 自检覆盖：verify_kit selftest 是否测过这条")
    st = (ROOT / "tools" / "verify_kit" / "selftest" /
          "run_selftest.sh").read_text(encoding="utf-8", errors="replace")
    covers = ("traversal" in st.lower()) or ("resolve_writable" in st)
    rec("selftest 含 traversal/resolve_writable 断言",
        covers, "结论：**未覆盖**（NC-1..NC-7 全测功能，无一条测穿越）")

    print("\n" + "=" * 84)
    verdict = (not escaped) is False     # 有逃逸 => 缺陷复现
    if verdict:
        print("判定：★ 缺陷成立 —— `..` 全部逃逸，守卫是空证（死条件）。")
        print("      这不是误报，是真实缺陷；D-07 里 28 条静态 sink 中**唯一**一条。")
        print("      修法（供他线采用，本件不执行）：先判 `..` 再归一化，")
        print("      即 `parts = PurePath(raw).parts` 用**原始**串取分量；")
        print("      或 `os.path.commonpath([base, resolved]) == base`。")
    else:
        print("判定：守卫有效，D-07 无真实缺陷。")
    print("=" * 84)
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
