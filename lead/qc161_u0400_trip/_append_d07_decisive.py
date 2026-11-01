#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-07 决定性结论追加：CRLF 逐字节保持；正文不含可执行的坏路径字面量。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "PENDING_DECISIONS.md"

BLOCK = """
- **★★★ 决定性实测（2026-10-24，GOAL-3T §411）：修好那条唯一真缺陷，告警条数也一条不少。**
  在临时副本上给 `resolve_writable_path` 施加最小修复（先在原始串判上溯分量、再归一化），
  实测 **9/9 PASS**：修复前 4/4 坏用例逃逸（负控先红）、修复后全部被拒、两条正控不误伤。
  **但密封产物的命中行是第 23 行的写盘调用，守卫在第 11–17 行，修复后第 23 行一字未改**
  ⇒ 规则锚在写盘调用上，改守卫动不到锚点，扫描器仍报同一条。
  ⇒ **「修真缺陷」与「减少告警」是两件正交的事。**
- **⇒ 选项 A「清零」由此彻底证否**（不是工作量问题）：27 条无边界/误报/死代码不可修，
  唯一真缺陷修了也不减数。规则判「写盘调用 + 变量」这个**形状**，不判数据流；
  只要还有带变量的写盘调用就还会报。
  **B（按写域路由）** 仍是唯一可执行路径。
  ★ 那 1 条修复本身仍有价值（守卫从空证变真守卫），只是**不能拿它换门禁放行**。
- **支撑件追加**：`_verify_vkio_fix.py`（修复验证 + 修了不减数实证，9/9）；台账 §411。
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
