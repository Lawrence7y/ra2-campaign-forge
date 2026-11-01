#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-07/H-1 追加：§418b 余量勘误（字节级追加，CRLF 不变）。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "PENDING_DECISIONS.md"

SECTION = """
- **★★★ 勘误（2026-10-24，GOAL-3T §418b）—— h7a 预算余量是 18 s，不是 36 s**
  - **上条数字作废**：§418 报的「余量 36.06 s」基于把 `sum(stage_seconds:*)`
    当作总时长。而 `Budget.check_trip()` 判的是 `elapsed()`（t0 起单调时钟），
    `stage_seconds` **不含** t0 到首个 `begin_stage` 的空档与 stage 间隙。
  - **标定**（7 份同时有 `duration_s` 与 `fields` 的可信趟，排除残缺产物）：
    `delta = duration_s − sum(stage_seconds)` = **16.75 ± 0.63 s**
    （16.04 / 16.18 / 16.39 / 16.44 / 16.91 / 17.51 / 17.80），
    **七份全部落在 16–18 s 窄带 ⇒ 结构性漏计，非噪声**。
  - **更正后**：最慢窗口趟真实总时长 ≈ **161.73 s**（sum 143.94 + delta 上界 17.80）
    ⇒ 180 s 余量 **18.27 s**（原报 36.06，**高估一倍**）。
    取 delta **上界**而非均值：余量宁可估低（真机白跑一趟的代价远高于提前调参）。
  - **错误性质**：算式没错，**分子取错**——`sum` 是 `elapsed()` 的**下界代理**。
    与 §414 判档器「用被验证量判型」同族：**判据算的是方便算的量，
    不是判据真正比的那个量**。
  - **修法**：`_preflight_h1.py` 新增 `duration_calibration()` 标定 delta 并加回；
    门限 `>20` 收紧到 `>15`。⇒ **17/17 PASS**；负控新增 M5 ⇒ **8/8 PASS**。
  - ★ **过程中再踩一次老坑**：M5 首版**存活**，因为新判据写成 `cal_max > 10`
    （**供给方**），而变异改的是 `hist_max_real`（**消费方**）。
    改成断言 `hist_max_real > hist_max + 10` 后立刻捕获。
    第二次 M5 仍报 FAIL，但红项内容正确（`rc=1`）—— 是**验证器预期子串**
    （「delta 校准」）与实际断言名（「校准已进入余量计算」）不一致。
    **变异被捕获 ≠ 验证器判对**，黑盒匹配串必须与被测断言名对齐。
  - **其余结论不变**：路径 110/134、载体 88/88、gamemd 哈希、out-dir 不存在、进程 0。
  - **判定收紧**：18 s 余量**不算宽裕**，但仍**不预先调参** ——
    真机是唯一能拿真实启动耗时的机会。要盯的阈值是 **180 s**；
    若撞 `EXIT_TRIP_BUDGET(18)`，看 `BUDGET.stage_begin:*` 最后一条的时刻：
    停在 179–180 s 附近 ⇒ 只需放宽窗口预算，不必改流程。台账 §418b。
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
