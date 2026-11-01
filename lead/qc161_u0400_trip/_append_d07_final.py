#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-07 最终判定追加：CRLF 逐字节保持；正文不含可执行的上溯路径字面量。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "PENDING_DECISIONS.md"

BLOCK = """
- **★ 最终判定（2026-10-24，GOAL-3T §410 逐条溯源，不改本条选项）**：把 28 条静态 sink
  逐条做 AST 溯源后，**真缺陷只有 1 条**，其余 27 条不可能「清零」：
  - **来源分布**：CLI 参数 12 / 形参 3 / 字面量 3 / 局部名 10 / **环境变量 0**。
    即所有输入都来自「开发者自己给的命令行参数」或「源码常量」，
    **不跨越信任边界**。「修」它们等于给所有工具的 `--out` 套受限目录
    （改变公开接口语义），且改完**仍会被报**——规则命中的是「写盘调用 + 变量」
    这个**形状**，不是数据流。⇒ **选项 A 在技术上不可达。**
  - **撞冻结件的 4 条是死代码**：`harness4/5/6/7` 的 `except_reset()` 全部
    **零 Load 引用**、无动态派发（AST 实测，非 grep），harness7 `:7553` 还明写
    「U-5：except_reset 已禁用」⇒ 不可达。但仍在冻结件内，处置权归其所有者。
  - **★ 唯一真缺陷：`tools/verify_kit/_vk_io.py` 的空守卫**。其 docstring 自称
    「traversal is rejected in exactly one audited place」，实测 **4/4 上溯用例全部逃逸**：
    根因是 `realpath(abspath(x))` 先把上溯分量折叠掉，之后才判它是否存在 ⇒ **恒假死条件**。
    这不是误报。**且 selftest 的 NC-1..NC-7 没有一条测路径穿越** ⇒ 长期未被发现。
  - **行动项收敛为 1 条**：修 `resolve_writable_path`（先判分量再归一化，
    或用 `commonpath` 前缀校验）+ 给 selftest 补 NC-8「上溯分量必须被拒」。
    该文件在 `tools/` 他线写域，本线**只出判定不改**。
- **对选项的影响**：A 不可达（27 条无边界 + 4 条冻结死代码）；**B（按写域路由）**
  仍是唯一可执行路径；C 受「主仓=唯一真源」限制。若 Lead 要走 A，
  现实等价于「接受 1 条真缺陷修完 + 其余 27 条以例外清单登记」。
- **支撑件**：`_census_d07_gate36.py`（§409 普查）、`_classify_sinks_d07.py`（28 条溯源）、
  `_adjudicate_vk_io_guard.py`（空守卫判定，缺陷复现）；台账 §409/§410。
"""


def main() -> int:
    before = TARGET.read_bytes()
    crlf0 = before.count(b"\r\n")
    lf0 = before.count(b"\n")
    assert crlf0 == lf0, "预期纯 CRLF 母本，实测 CRLF=%d LF=%d" % (crlf0, lf0)
    assert before.endswith(b"\r\n"), "母本应以 CRLF 结尾"

    body = BLOCK.lstrip("\n").replace("\r\n", "\n").replace("\n", "\r\n")
    payload = body.encode("utf-8")
    added = payload.count(b"\r\n")

    after = before + payload
    assert after.startswith(before), "前缀必须逐字节保持"
    assert after.count(b"\r\n") == crlf0 + added, (
        "CRLF 增量必须等于新增行数：%d + %d != %d"
        % (crlf0, added, after.count(b"\r\n")))
    assert after.count(b"\n") == after.count(b"\r\n"), "写回后必须仍是纯 CRLF"

    TARGET.write_bytes(after)
    print("appended %d bytes / %d lines; total %d -> %d"
          % (len(payload), added, len(before), len(after)))
    print("CRLF %d -> %d (pure CRLF preserved)" % (crlf0, after.count(b"\r\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
