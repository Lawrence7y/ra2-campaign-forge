#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-07/H-1 追加：§418 飞行前检查结果（字节级追加，CRLF 不变）。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "PENDING_DECISIONS.md"

SECTION = """
- **★★ H-1 飞行前检查完成（2026-10-24，GOAL-3T §418）—— 真机时段只剩「执行 + 读产物」**
  `_preflight_h1.py` **16/16**、负控 `_verify_preflight_h1.py` **7/7（4 变异全捕获）**。
  - **路径不是风险**：三趟载体目录长度 **110**（< 127 WARN，余 17）；
    最长载体全路径 **134**（< 260 MAX_PATH，余 126；最长件
    `[2]0LoadBench_U0400.yrm`）。
  - **载体源完好**：`_src_L1_sf8_20261020` manifest **88 = on-disk 88**，
    missing 0 / extra 0 / **尺寸不符 0**；`gamemd.exe` 4,825,360 B
    哈希 `73201cc021497c95` **仍等于冻结值**；`XMP29U2.MAP` `0add791d…`
    与发射器 `map_sha` 逐位一致。残留 `gamemd.exe`/`game.exe` 进程 **0**。
  - **out-dir 三趟均不存在** ⇒ 不会与旧证据混叠。
  - ★ **唯一需要盯的一项**：`--fullscreen` 会把预算从母本 `180 s / 30 s` 放宽到
    `540 s / 150 s`（`:7391-7393`），而 **h7a 恰恰不传 `--fullscreen`**
    ⇒ 三趟里只有它没有豁免。35 份真实窗口趟按 `stage_seconds:*` 求和：
    **最大 143.94 s / 中位 59.17 / 标准差 49.26 / 超 180 s 的 0 份**
    ⇒ **余量 36.06 s**。判定「**可接受但需留意**」，不据此调参 ——
    真机是唯一能拿到真实启动耗时的机会，**先测再谈**。
    若 h7a 撞 `EXIT_TRIP_BUDGET(18)`，那本身是有价值的观测，正好标定
    「窗口模式预算该不该也放宽」。
  - **单阶段上限不是风险**：`measure_w0/w1/w2` 各为独立阶段、上限 30 s；
    42 个真实样本实测 **25.00–25.05 s、标准差 0.007** ⇒ 固定时长，余 ~5 s 属设计留白。
  - ★ 负控 M4 的红项**只有 h7a**（全屏两趟走 540/150 分支，不受窗口预算判据约束）
    —— 若三趟都红，说明两种预算口径被混在一起了。这条反向印证判据正确。
  - **结论**：路径/载体/目录/进程四项均无阻碍，真机时段可**直接执行**；
    执行时重点记录 h7a 的 `duration_s` 与 `BUDGET.stage_seconds:*`。台账 §418。
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
