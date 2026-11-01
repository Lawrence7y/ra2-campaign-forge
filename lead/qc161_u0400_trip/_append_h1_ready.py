#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""H-1 就绪追加：CRLF 保持；正文不含可执行坏路径字面量。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "PENDING_DECISIONS.md"

BLOCK = """
- **H-1 就绪（2026-10-24，GOAL-3T §413）**：真机三趟从「散文描述」变为**可复跑命令**。
  `_trip_plan_h1.py` 只打印三趟命令（不建目录、不启动进程，自检 **17/17**），
  `_verify_trip_plan_h1.py` 负控 **8/8（5 变异全捕获）**。
  三趟 suffix 互异（h7a/h7b/h7c，防 out-dir 覆盖）：窗口模式（无全屏）/ 全屏短路 /
  对照臂（`--h7-keep-rect-wait`），全部 harness7。
  ★ 关键：命令由发射器**同一个** `build_harness_argv()` 纯函数生成，
  自检 C7 逐字比对 ⇒ 不存在「编排器与发射器两处各写一份」的漂移。
  **真机时段只需复制粘贴这三条命令**；仍待用户在场。
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
