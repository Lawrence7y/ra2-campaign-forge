#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-09 立项（真机守卫首验结果 + 挂死分叉）—— 行尾自适应追加。

★★ 行尾纪律（本件两次实测）：
  - 母本曾被 e8dc58e 从纯 CRLF(119) 重写成纯 LF ⇒ 现件是 **LF-only**；
  - 断言对象是「写回后行尾风格与写回前一致」，不再硬写 CRLF==旧值
    （那是上一版的口径，对本件会假红）。
"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md")

BODY = """<!-- SYNCPOINT 2026-10-24 晚：②-A 守卫首验 12 趟已跑（真开臂 3/3 零 AV，但挂死）；D-09 待裁 -->

## D-09 · RC-4 守卫「不崩但挂死」——部署门槛如何改，与判据通道缺失 [来源 GOAL-3T]

- **背景**：v12 §6 真机序列的 ②-A 项「v5 守卫 A/B」已于 2026-10-24 首验（台账 §426，
  产物 `lead/qc161_u0400_trip/ab24/`，发射器 `_drive_rc4_ab24.py`；他线
  `_rc4_ab_probe.py` 一字未改）。同开机会话（10:36 起）共 6 批 12 次实跑趟。

  **每趟判定**（全部 a8=PASS、趟间残留 0、母本四哈希未变、dump 只落 `D:\\ra2dumps`）：

  | 臂/批 | hit(RC-4 三元组) | 关窗后 | 自评 |
  |---|---|---|---|
  | A 直启 ×4（批1/2/3/4）| **YES**（Eip=0x724737 Access=read@0x250，singleton_at_hit=0）| ~9.3–9.7 s 命中 | 基线复现 **达标** |
  | B 注入 Guard=0 ×2（批3/4）| **YES**（三元组逐位同 A）| 同上 | 注入中性对照 **达标** |
  | B 注入 Guard=1 **假开臂** ×1（批3）| **YES** | 同上 | 开关写入被注释陷阱吞掉，守卫日志自证 =0 |
  | B 注入 Guard=1 **真开臂** ×3（批4/5/6）| **no**（三趟一致）| **无 AV 也无退出**：短窗 24.1 s / 长窗 114 s 均未见 EXIT_PROCESS，最终由趟清扫击杀 | 抑制 **达标**，退出 **不达标** |

  dump 通道双证：崩溃形态 7/7 全部落 dump；真开臂趟零 dump。
  守卫日志三趟均「原字节比对 8/8 ⇒ 守卫已装 8/8」（gamemd 母本 sha 未变）。

- **★ 分叉点**：v12 §3-②-A 开臂判据四条 = 「3 趟 0 AV / **守卫计数≥1** /
  ≤20 s 正常退出 / L1 进局无副作用」。本轮实测：
  1. **「守卫计数≥1」结构上不可达**——计数只在 `DLL_PROCESS_DETACH` 落日志，
     而趟终是 `TerminateProcess`，**强杀不跑 detach** ⇒ 开臂趟 hits 恒 None。
     这不是「没抓到」，是**判据通道不存在**（按 v12 §4.3：抓不住的判据要降级登记）。
  2. **「≤20 s 正常退出」被证伪**——守卫让空 this 调用安全返回，但退出链似乎在等
     那些调用的**副作用**（消息循环的退出信号），结果把崩溃换成了挂死。
     ⇒ **作为部署修复不合格**：用户关窗后游戏进程不消失，比崩更难收拾（要杀进程）。

- **选项**：
  - **A** 判「抑制有效、部署不合格」，退回守卫件设计：跳过的同时补齐退出推进
    （候选=ecx=0 分支不直接返回，而是置退出标志/跳到原函数的非空副作用路径）。
    需静态设计 + 他线写域（守卫件在 `lead/goal2_rc4_fixv5_20261022/src/`）。
  - **B** 先钉死挂死机制再设计：旁路读 `[0xA8EDD8]`（退出状态机）+ 消息循环存活
    判据，逐 100 ms 采样一趟，确认「停在哪个阶段」。**一次真机场次**。
  - **C** 把 §3-②-A 判据**就地改口径**为可观测三条件：真开臂 0 AV（✓）+
    守卫安装日志 8/8 memcmp（✓）+ 崩溃形态与注入中性对照（✓），
    把「正常退出」移出本轮门槛、单列新缺陷 RC-4-H1。
- **建议**：**B → A**（先花一趟钉机制，再改件）；**C 的判据修订需 Lead 明确批准**，
  本线不自改口径。若选 A，守卫件改造属他线写域，须 Lead 派给归属线或授权本线出补丁副本。
- **阻塞**：②-A 的 v5 部署准备（本轮已确证不可按现件部署）；
  D-08（harness7 升格）不受影响。
- **状态**：待 Lead / 用户裁决
- **提出**：2026-10-24（§426 同轮）
"""


def main() -> int:
    before = TARGET.read_bytes()
    crlf0, lf0 = before.count(b"\r\n"), before.count(b"\n")
    style = "CRLF" if crlf0 == lf0 and crlf0 > 0 else ("LF" if crlf0 == 0 else "MIXED")
    assert style in ("CRLF", "LF"), "行尾混合，手术面扩大，停手：%d/%d" % (crlf0, lf0)
    assert before.endswith(b"\n")

    body = BODY.lstrip("\n").replace("\r\n", "\n")
    if style == "CRLF":
        body = body.replace("\n", "\r\n")
    payload = body.encode("utf-8")

    after = before + payload
    assert after.startswith(before), "前缀必须逐字节保持"
    c1, l1 = after.count(b"\r\n"), after.count(b"\n")
    if style == "CRLF":
        assert c1 == l1, "写回后须仍纯 CRLF：%d/%d" % (c1, l1)
    else:
        assert c1 == 0, "写回后须仍纯 LF：%d" % c1
    TARGET.write_bytes(after)
    print("appended %d bytes (%s style); %d -> %d" % (len(payload), style, len(before), len(after)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
