#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-07 证据追加：GOAL-3T 实测结果，CRLF 逐字节保持。

PENDING_DECISIONS.md 实测为纯 CRLF（119 CRLF = 119 LF），
故本件追加内容一律用 CRLF，并在写回前断言 CRLF 增量 == 新增行数。
"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md")

BLOCK = """
- **更新（2026-10-24，GOAL-3T 实测，不改本条选项）**：§409 用密封深扫
  `scan-2026-10-23T20-36-58.833Z-8f7e7ad6abd0` 把「36 high」拆开，三条实测：
  - **口径**：36 是 occurrence；`findingId` 唯一值 29，粒度实测为 **(规则,文件) 对**
    （同文件同规则多行共用、跨文件从不用），**不能当缺陷数**。
    构成 = **28 静态 sink + 8 跨文件污点链**（后者扫描器自标 `advisory: true`
    并带 `proofGaps`「需人工确认真实数据流」）。这 8 条是深扫才出现，
    且全部落在 harness4/5/6/7 —— 这三个件本线一个字节未碰，非本轮引入。
  - **决定性**：**6 条落在已实测哈希冻结件上**（harness6 `ff8245d27b3db22a` /
    harness7 `d019e8beecfb5fd8`，逐位复核仍等于冻结值）。
    ⇒ **选项 A「清零」与「母本零改动」铁律直接冲突**，不是工作量问题；
    A 若要成立，需先裁决「是否允许为安全告警破冻结」——**Lead 级口径冲突**。
  - **本线无责**：本线写域（`lead/qc161_u0400_trip/`）命中 **0 条**。
    这也解释了「commit 能过、push 不能过」：commit 走 diff-only，push 走整仓。
- **对选项的实测影响**：**B（按写域路由）** 不是偷懒，而是与 commit 已有的
  diff-only 档**对齐**（同一件事，push 端没跟上）；C 仍受「主仓=唯一真源」限制；
  A 需先解上面的口径冲突。
- **支撑件**：`lead/qc161_u0400_trip/_census_d07_gate36.py`（普查，exit 0）、
  `_verify_census_d07.py`（负控 **11/11 PASS，6/6 变异被捕获**）。
  台账 §409。
"""


def main() -> int:
    before = TARGET.read_bytes()
    crlf0 = before.count(b"\r\n")
    lf0 = before.count(b"\n")
    assert crlf0 == lf0, "预期纯 CRLF 母本，实测 CRLF=%d LF=%d" % (crlf0, lf0)
    assert before.endswith(b"\r\n"), "母本应以 CRLF 结尾"

    body = BLOCK.lstrip("\n").replace("\r\n", "\n").replace("\n", "\r\n")
    payload = body.encode("utf-8")
    added_lines = payload.count(b"\r\n")

    after = before + payload
    assert after.startswith(before), "前缀必须逐字节保持"
    assert after.count(b"\r\n") == crlf0 + added_lines, (
        "CRLF 增量必须等于新增行数：%d + %d != %d"
        % (crlf0, added_lines, after.count(b"\r\n")))
    assert after.count(b"\n") == after.count(b"\r\n"), "写回后必须仍是纯 CRLF"

    TARGET.write_bytes(after)
    print("appended %d bytes / %d lines; total %d -> %d"
          % (len(payload), added_lines, len(before), len(after)))
    print("CRLF %d -> %d (pure CRLF preserved)" % (crlf0, after.count(b"\r\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
