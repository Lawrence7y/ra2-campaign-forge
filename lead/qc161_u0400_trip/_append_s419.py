#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§419 追加器：字节级追加，不动既有 CRLF 行。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

SECTION = """
---

# §419 判档器阈值反查：三条数值判据**逐个对到实测分布**，其中一条余量 9.1 倍

**轮次目标**：§418b 的教训是「判据用了代理量」。同族风险是
**判据看着合理，但永远不红/永远误红 = 零信息量**。
本轮把 `H7_SMOKE` 里每条数值阈值逐个反查到真实产物分布上，
并明确写出「该阈值靠什么才能变红」。

## 一、方法：用恒等式从真实产物反推，不靠推断

短路臂的核心收益是「frame 段从 ~125 s 掉到 <2 s」。但 `frame_s` 段里含两项：

```
stage_seconds:frame  =  矩形等待(polls × 0.5 s)  +  采帧 + 分类
⇒ (采帧 + 分类)      =  stage_seconds:frame − polls × 0.5
```

这个恒等式让我**不需要真机**就能算出「短路后 frame 段会是多少」
（因为短路就是把 `polls` 归零）。34 份真实产物实测：

| 量 | 值 |
|---|---|
| 采帧+分类 最小 | 0.000 s |
| 采帧+分类 最大 | **0.219 s** |
| 中位 | 0.140 s |

⇒ 短路后 `frame` 段约 **0.219 s**，对门限 `2.0` 有 **9.1 倍余量**。
**该判据不会因采帧抖动误红，也不会因短路生效而误绿。**

## 二、四条阈值逐条定性

| 判据 | 阈值 | 实测分布 | 定性 |
|---|---|---|---|
| `windowed.polls_max` | 5 | 窗口 25 份 **全为 0** | 未误伤；变红条件 = 出现 polls>5 |
| `fullscreen_short.polls_max` | 0 | 无 harness7 产物 | 靠代码语义（`deadline=0.0` ⇒ while 首判即假） |
| `fullscreen_short.frame_s_max` | 2.0 | 采帧开销 **0.000–0.219** | **9.1 倍余量** |
| `fullscreen_keep.polls_min` | 200 | harness6 全屏 96–253 | 覆盖 8/9（例外 = 48 s 短帧） |
| `fullscreen_keep.frame_s_min` | 100 | harness6 全屏 48.16–126.70 | 覆盖 8/9（同一例外） |

★ `frame_s_min` 与 `polls_min` 覆盖**同一批 8/9、同一个例外**，
再次印证二者是**同一条时长判据的两种写法**（`frame ÷ polls = 0.5007 ± 0.0003`）。

## 三、★ 顺带查清：窗口模式 `polls=0` 是**结构性的**，不是运气

`deadline` 在 window 阶段设置（`:7641`）：

```python
deadline = time.monotonic() + STAGE_TIMEOUT_S      # 180 s 档下 = +30 s
```

而采帧循环在 nav **之后**。实测 25 份窗口趟的「frame 前累计耗时」：

| 量 | 值 |
|---|---|
| 最小 | **44.20 s** |
| 最大 | 143.80 s |
| > 30 s（即 `deadline` 必已过期） | **25/25** |

⇒ **全部 25 份的 `deadline` 在到达采帧循环时都已过期**
⇒ `while rect != 800×600 and monotonic() < deadline` 的**第二个条件立即为假**
⇒ 循环体一次都不进 ⇒ `polls` **必然为 0**。

★★ 这意味着 `polls_max: 5` 在窗口模式里**几乎不可能变红**（除非 nav 快到
frame 前累计 <30 s，而 25/25 样本都 >44 s）。
**它的真实信息量很低** —— 但**不必删**：它是「短路未生效 / 等待被跳过」的
免费哨兵，留着不花成本；只是**不能把它当作「窗口模式等待正常」的强证据**。

★ 同时这也解释了旧版 `archive_T5/T8/T9` 三份为何 `polls` 缺失：
它们是**旧版进程**产物（stage 名是 `nav` 而非 `nav_start`/`nav_menu`），
本判据按 `fs 缺席 + polls 存在` 取样，自然排除它们。

## 四、装置与负控

| 件 | 说明 | 结果 |
|---|---|---|
| `_audit_threshold_support.py` | 阈值支撑度审计（**import 判档器**取阈值，保证同源） | **13/13** |
| `_verify_threshold_audit.py` | 负控：改**被判档器的阈值** + 改**审计自己的判据** | **6/6** |

变异：M1 `polls_max` 5→−1、M2 `frame_s_max` 2.0→0.05、M4 窗口样木判据反转。
三个全部被捕获。

★ 过程中修掉本件自己的两个问题：
1. 首版把「harness7 样木 n=0」当**失败项** ⇒ 本件永远红，反而淹没真检查。
   改成**如实打印 + 在结论边界显式申报**。
2. 修完后「无实测支撑」那行写成 `rec(..., True)` ⇒ **恒真断言**（零信息量）。
   改成输出**会变的事实**（`无实测` / `有真实 harness7 产物`），
   真机跑过后本行自动反映新证据。

★ M2 的红项显示「门限 0.1 s」而注入值是 0.05 —— 那是 `%.1f` 格式化舍入，
判据本身正确失败。**看红项要看它是否红在该红的原因上，不看数字是否逐字相同。**

## 五、交付件

| 件 | 结果 |
|---|---|
| `_probe_frame_stage_cost.py` | 采帧开销反推（34 份样本） |
| `_probe_deadline_expiry.py` | deadline 过期取证（28 份窗口趟） |
| `_audit_threshold_support.py` | **13/13** |
| `_verify_threshold_audit.py` | **6/6** |

★ 本轮**不改**判档器、**不改** harness、**不改**任何阈值。
它做的是**给每条阈值标注「它靠什么才能红」**，避免真机跑完后
把「判据没红」误读成「被测物正常」。
"""


def main() -> int:
    before = LEDGER.read_bytes()
    assert b"\r\n" in before
    crlf0 = before.count(b"\r\n")
    assert before.endswith(b"\n")

    body = SECTION.lstrip("\n")
    payload = body.replace("\r\n", "\n").encode("utf-8")

    after = before + payload
    assert after.startswith(before), "前缀必须逐字节保持"
    assert after.count(b"\r\n") == crlf0, (
        "CRLF 数必须不变：before=%d after=%d" % (crlf0, after.count(b"\r\n")))

    LEDGER.write_bytes(after)
    print("appended %d bytes; total %d -> %d"
          % (len(payload), len(before), len(after)))
    print("CRLF preserved: %d" % crlf0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
