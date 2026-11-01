#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-07/H-1 追加：§419 阈值支撑度（字节级追加，CRLF 不变）。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "PENDING_DECISIONS.md"

SECTION = """
- **★ 阈值支撑度已逐条标注（2026-10-24，GOAL-3T §419）—— 防真机跑完后误读「没红=正常」**
  `_audit_threshold_support.py` **13/13**、负控 `_verify_threshold_audit.py` **6/6**。
  - **`fullscreen_short.frame_s_max = 2.0` 余量 9.1 倍**：用恒等式
    `采帧+分类 = stage_seconds:frame − polls × 0.5` 从 34 份真实产物反推，
    实测 **0.000–0.219 s**（中位 0.140）⇒ 短路后 frame 段约 0.219 s。
    **不会因采帧抖动误红，也不会因短路生效而误绿。**
  - **`windowed.polls_max = 5`：未误伤（25 份窗口趟 polls 全为 0），但信息量很低**。
    ★ 查清成因：`deadline` 在 window 阶段设置（`deadline = now + 30 s`），
    而采帧循环在 nav 之后。实测 25 份窗口趟「frame 前累计耗时」**最小 44.20 s、
    25/25 全部 > 30 s** ⇒ 到采帧时 `deadline` **必已过期** ⇒ `while` 第二条件
    立即为假 ⇒ **`polls` 必然为 0，结构性而非运气**。
    ⇒ 该判据在窗口模式**几乎不可能变红**，**不能当作「窗口等待正常」的强证据**；
    但**不必删**——它是「短路未生效/等待被跳过」的免费哨兵。
  - **对照臂两条判据覆盖同一批 8/9、同一个例外**（48 s 短帧那趟），
    再次印证 `polls_min:200` 与 `frame_s_min:100` 是同一条时长判据的两种写法。
  - **边界（如实申报）**：盘上 harness7 样木仍为 **0**，`fullscreen_short` 的
    `polls_max:0` 只能靠代码语义（`deadline=0.0` ⇒ while 首判即假）支撑，
    两个全屏臂的阈值**无真实产物支撑**，真机三趟才能补。
  - ★ 过程中修掉本件自己两处：① 首版把「harness7 样木 n=0」当失败项 ⇒ 永远红、
    淹没真检查，改成如实打印 + 结论边界申报；② 修完后「无实测支撑」写成
    `rec(..., True)` ⇒ 恒真断言，改成输出会变的事实（真机后自动升级）。
  - **真机判读提示**：`polls_max:5` 没红**不构成**窗口等待正常的证据；
    真正该看的是 `fullscreen_short` 的 `frame_s` 是否塌到 <2 s（余量 9.1 倍，稳）。
    台账 §419。
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
