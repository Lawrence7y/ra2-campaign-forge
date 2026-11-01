#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-08 立项 + H-1 真机结果（SYNCPOINT 信标）—— 字节级追加，CRLF 不变。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "PENDING_DECISIONS.md"

SECTION = """
<!-- SYNCPOINT 2026-10-24 11:2x：H-1 真机三趟已跑完，harness7 冒烟核心两臂全过；D-08 待裁 -->

## D-08 · harness7 是否升为在用件（H-1 真机结果待裁决）

- **背景**：S399 §九 第 5 条口径「三趟都过 ⇒ harness7 升在用件；任一不过 ⇒ 回改重跑」。
  2026-10-24 真机三趟（用户授权自主执行）已跑完，产物 `l1_20261023{ha,hb,hc}/`。
- **实测结论（盘面取证）**：
  - **第2趟 hb（全屏短路）冒烟 4/4 PASS**：`skipped=True`、`polls=0`、
    `frame=0.079 s`（对 §419 反推的 0.000–0.219 s 带）、`nav_to_measure_s=0.079`
    ⇒ **边界 2 的 90 s 阈值无需重标**。核心收益实证（122–127 s → 0.079 s）。
  - **第3趟 hc（对照臂）冒烟 5/5 PASS**：真机字段形态 = META=False + **FRAME 缺席**
    + n2m 缺席 ⇒ **直接证实 §422 修复必要**（旧判档器读 FRAME 会把本趟判成
    「不是冒烟样本」⇒ 对照臂判据永不执行、整趟白跑）。keep 臂 122.203 s 复现死等，
    A/B 对照成立。
  - **第1趟 ha（窗口）结构性 N/A**：载体 `ddraw.ini windowed=false`（boot-hang 修复）
    ⇒ 游戏恒全屏 2560×1440 ⇒ 窗口臂抓帧 `capture_ok=False` ⇒ 主菜单签名失效 ⇒
    nav INCOMPLETE。**非 harness7 缺陷、非配置漂移**——是窗口态与 boot 修复载体互斥。
- **裁决选项**：
  - **A. 正式把 §九 第 1 条改判 N/A-环境，按「两臂全过」升 harness7 为在用件**。
    佐证：窗口模式 skipped 语义已有 29 份历史窗口产物（polls=0 全中）+
    本趟 `MEASURE.skipped` 设计行为双重支持；且 harness7 全部新增字段只在
    `--fullscreen` 分支写，窗口模式行为=与 harness6 逐字节一致（设计即如此）。
  - **B. 为窗口臂单独造 `windowed=true` 载体重跑第 1 趟**。
    代价：重新面对 boot-hang（窗口态当年就是靠 `windowed=false` 治的），
    很可能复现龟放/卡启动，收益低（验的只是「不写 skipped」，历史样本已证）。
  - **C. 维持三趟口径不放宽，harness7 继续候选态。**
- **本线意见**：**A**。§九 的三趟设计写于窗口态可用时，未预见与 boot-hang 修复
  互斥；两臂全屏 A/B（122 s ⇄ 0.079 s）才是 D-05 要验的补丁语义本体，已全部实证。
- **附带更正（D-07 相关）**：发射前发射器路径门禁 BLOCK（131>130）暴露
  `_preflight_h1.py` 度量口径取错（量 `out_dir\\ct`=110 而非发射器占位符公式=131）。
  已按发射器原文修尺 + 阳性对照（P-GATE2）。**迁就门禁不改门禁**：改用 2 字符
  后缀 `ha/hb/hc`（口径 130 恰过门），零绕闸。台账 §422b/§423。
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
