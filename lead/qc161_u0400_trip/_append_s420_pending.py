#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-07/H-1 追加：§420 三窗全通路径预演（字节级追加，CRLF 不变）。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "PENDING_DECISIONS.md"

SECTION = """
- **★★ 判档器「真机会走的那条路」也已验过（2026-10-24，GOAL-3T §420）**
  §416 只验了三形态在**短路路径**（判档器 `:430`）下的行为；真机 h7a 若顺利，
  走的是 `:536` 的**正常完成路径**（三窗全通）。本轮补齐：
  `_preview_h7_fullpath.py` **9/9**、负控 `_verify_h7_fullpath.py` **6/6**。
  - 源趟 `l1c_20261021`（w0/w1/w2 均 ok，polls=247 / frame=123.704）。
    盘上三窗齐全的只有 5 趟，**无一是 harness7** ⇒ 必须造副本。
  - **三形态判型全对**：windowed / fullscreen_short / fullscreen_keep；
    冒烟断言分别 3 / 4 / 4 条全 PASS（short 臂 frame=1.32 < 2.0）。
  - **两段共存已证**：同一份输出同时含 `[1] measure 三窗` 与 `[4b]`，
    即三窗全通路径确实执行到冒烟段，未被前面 return 掉。
  - ★ `rc=1` 不是冒烟失败，是**源趟本身** `pre_fps15=8.023` 撞 V11-a 硬门禁
    ⇒ 正好证明本预演能区分「冒烟过 / 档位不过」。
  - **互不干扰负控**：短路臂 `frame=123.7` ⇒ 冒烟段红在 `frame_s_max`，
    三窗段落**零新增红项**。
  - ★★ **装置两次翻车（均已修）**：
    ① 首跑 1/9、九条红项文字完全相同 ⇒ **装置没跑起来**：副本里
    `JUDGE = Path(__file__).resolve().parent / ...` 指向临时目录 ⇒ 子进程 rc=2、
    stderr 为空。负控必须**同时钉住 ROOT 与 JUDGE 两个锚点**；
    每换一个件都要重新数它的路径锚点。
    ② M2 首版只改 `harness_sha16` ⇒ **变异存活**：判档器
    `is_h7_run = (sha==H7) or (sk is not None) or (n2m is not None)`
    有**三条独立退路**。要模拟「非 harness7 趟」必须**三路全撤**；
    改完立刻捕获。★ **变异存活先问「是件错了还是尺子错了」**，
    本例判据设计是对的，错在变异只打了一条。
  - **边界不变**：盘上 harness7 产物仍为 **0**；§416 与 §420 证明的都是
    **判读能力**，不是**被测物行为**。真机三趟仍是唯一补齐手段。
    台账 §420。
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
