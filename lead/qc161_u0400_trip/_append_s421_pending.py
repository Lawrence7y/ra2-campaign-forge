#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-07/H-1 追加：§421 合成失真修正与 late_start 判据语义（字节级，CRLF 不变）。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "PENDING_DECISIONS.md"

SECTION = """
- **★ 合成失真修正 + 真机判读预期（2026-10-24，GOAL-3T §421）**
  - §416/§420 预演件曾给三形态**都**注入 `h7_nav_to_measure`；真实 harness7
    只在**短路臂**写它（`:4970` 条件含 `fs_rect_wait_skipped`，keep/窗口臂不写）。
    已修正（`_preview_h7_fullpath.py` 9/9、`_preview_h7_forms.py` 8/8、
    `_verify_h7_fullpath.py` 6/6、`_verify_h2e_smoke.py` 25/25 全回归通过）。
  - **真机判读预期（重要）**：
    ① h7c（对照臂）fields 里**不会**有 `h7_nav_to_measure` 记录 ⇒ 判档器
    `对照臂 late_start 不得出现` 会以 `late_start=None` 通过，**这是正确形态**。
    该断言验的是**设计不变量**（短路闸没被误装到 keep 臂），不是运行时时机；
    它变红 ⇔ harness7 在 keep 臂错误写入了 `late_start=True`。
    ② h7b（短路臂）的 `nav_to_measure_s` 仍是**边界 2 的唯一实测数**，
    真机后须记录其值以裁 90 s 阈值是否重标（S399 §九 第 2 条）。
  - ★ **纪律沉淀**：合成样本每个字段要回答「**真机会写它吗**」，
    不是「判据要读它吗」。判据读而真机不写 ⇒ 断言实为缺席分支；
    合成时替真机补写会让验证语义漂移（本轮正是如此）。
    台账 §421。
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
