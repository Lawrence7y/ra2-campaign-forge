#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-07/H-1 追加：§417 命令文本缺陷与修复（字节级追加，CRLF 不变）。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "PENDING_DECISIONS.md"

SECTION = """
- **★★ H-1 前置缺陷已修（2026-10-24，GOAL-3T §417）—— 三趟命令此前一粘贴就废**
  - **缺陷**：`_trip_plan_h1.py` 的 `quote()` 只在**含空白**时加引号，而 argv 全是
    Windows 反斜杠路径（**无空格**）⇒ 全部裸奔。Git Bash 里 `\\` 是转义符，
    实测未加引号的 `D:\\Project\\...` 被吃成 `D:Projectra2-campaign...`
    ⇒ **照抄粘贴后三条趟全部因路径不存在而立刻失败**。
  - **为什么此前没发现**：C7/C8 验的是 **list 层**（argv 列表），
    `quote()` 在 list 之后才介入；§416 预演完全在判档器侧。**没有任何一条自检
    跨过「list → shell 命令文本」这条边界**——验零件 ≠ 验装配。
  - **修复**：`quote()` 一律加双引号 + 转义内部双引号。新增两条自检：
    **C11**（`shlex.split(cmd, posix=True)[1:]` 必须逐字等于 argv）
    + **C11b 阳性对照**（换回旧实现，同一条分词**必须**失真）。
    ⇒ `_trip_plan_h1.py` **21/21**（原 19）；负控器新增 **M6** ⇒ **9/9**（原 8）。
  - **双向闭合验收**：除 `shlex` 外，另用**真 bash** 跑一遍（`python`→`echo`，
    看 bash 实际收到什么），h7a/h7b/h7c **三条首尾参数全完好**。
    ★ 只用 shlex 会担心「尺子自己错」，只用 bash 无法写成断言；两者都用才兼得
    **可判**与**可信**。
  - **顺带核到（无问题）**：① 三趟用到的 10/11/12 个 flag **全部**在 harness7
    argparse 的 20 个选项内，零未知；② 发射器走 `os.spawnv` **不过 shell**，
    其引号规则只影响打印美观，与规划器用途不同，**不可强行统一**。
  - ★ **真机时段用的就是这三条命令**，所以这条修复直接决定 H-1 能不能一次跑成。
    台账 §417。
"""


def main() -> int:
    before = TARGET.read_bytes()
    assert b"\r\n" in before
    crlf0 = before.count(b"\r\n")
    assert before.endswith(b"\n")

    body = SECTION.lstrip("\n")
    payload = body.replace("\r\n", "\n").encode("utf-8")

    after = before + payload
    assert after.startswith(before), "前缀必须逐字节保持"
    assert after.count(b"\r\n") == crlf0, (
        "CRLF 数必须不变：before=%d after=%d" % (crlf0, after.count(b"\r\n")))

    TARGET.write_bytes(after)
    print("appended %d bytes; %d -> %d" % (len(payload), len(before), len(after)))
    print("CRLF preserved: %d" % crlf0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
