#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-07/H-1 追加：§416 预演结果 + 自检计数更正（字节级追加，CRLF 不变）。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "PENDING_DECISIONS.md"

SECTION = """
- **★ 勘误 + 预演结果（2026-10-24，GOAL-3T §416）**
  - **勘误**：上条「`_trip_plan_h1.py` 自检 **17/17**」是 `§413` 时的旧数；
    现件实为 **19/19**（后续加了 C9b 阳性对照与 C10「`--json` stdout 纯净」两条）。
    以 **19/19** 为准。
  - **补做**：此前只验过「判据**逻辑**对不对」（`_verify_h2e_smoke.py` 25/25，全手搓最小 JSON），
    没验「**真实产物**下判型对不对」。新增 `_preview_h7_forms.py`：
    拿真实 harness6 全屏产物（`l1_20261023`，polls=251 / frame=125.703）**纯加法**改造成
    三形态，再跑判档器 ⇒ **8/8 PASS**，含
    `windowed` / `fullscreen_short` / `fullscreen_keep` 三臂判型互不相同（承重性），
    与 4 条负控（窗口臂写 skipped ⇒ 红；短路臂 frame=125.7 ⇒ 红在 frame_s_max；
    对照臂 polls=96 ⇒ 仍判 keep 且红在 polls_min；该趟不得被判成 windowed）。
  - **阈值已钉到实测分布**：盘上 57 份 `qc151_fields.json` 全量分类 ——
    **窗口趟 29 份 polls 全为 0**（`polls_max: 5` 有 29/29 实测支撑，与
    `S399 §九`「历史窗口模式实测 0」独立吻合）；harness6 全屏 9 份 frame 段
    48.2–126.7 s（`frame_s_min: 100` 覆盖 8/9，例外正是那趟 48 s 短帧）。
    ⇒ `polls_min: 200` 与 `frame_s_min: 100` 是**同一条时长判据的两种写法**
    （`frame ÷ polls = 0.5007 ± 0.0003`），属冗余校验而非重复缺陷。
  - **真实产物回归**：7 趟有 `_launch_result.json` 的旧趟逐一跑判档器，
    **7/7 全部正确跳过**（`[跳过] 本趟不是 harness7`）。若按 §414 前的判法，
    它们会因 `polls ≥ 200` 被判成 keep 再报「skipped 应 == False 而实测 None」
    ⇒ **7 趟全假红**。这是 §414 修复的真实产物级证据。
  - ★ **仍未验的部分**：盘上 harness7 产物 **0 份**，所以两个全屏臂的**产物形态**
    仍是设计预期。预演证明的是**判读能力**，不是**被测物行为**；
    这一层只有真机三趟能补。台账 §416。
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
