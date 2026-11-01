#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§418b 追加器：勘误 §418 的余量数字。字节级追加，不动既有 CRLF 行。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

SECTION = """
---

# §418b 勘误：§418 的「余量 36 s」是错的 —— 拿 sum 当总时长，实测低估 16.75 s

**轮次目标**：§418 结了「h7a 窗口预算余量 36.06 s」。收尾后后台扫描报回
「真实窗口趟带 `_launch_result.json` 的 **0 份**」—— 我用的 35 份样本
**全都是 `stage_seconds:*` 求和**，没有一份有真实总时长。这暴露出：
**§418 的分子不是预算判据比的那个量。**

## 一、预算判的是 `elapsed()`，我算的是 `sum(stage_seconds)`

`Budget.check_trip()` 判的是 `time.monotonic() - self.t0`（全程单调时钟），
而 `stage_seconds:*` 只覆盖 `begin_stage` / `end_stage` 之间的区间。
**t0 到第一个 `begin_stage` 的空档、以及各 stage 之间的空隙，都不在任何
`stage_seconds` 里。**

用**同时有两种数据**的趟标定（7 份可信样本，排除 `l1b` 那种 sum≈5.86 的残缺产物）：

| 趟 | duration_s | sum(stage) | delta | ratio |
|---|---:|---:|---:|---:|
| l1c_20261021 | 260.00 | 242.20 | 17.80 | 1.0735 |
| l3_20261021 | 258.40 | 240.89 | 17.51 | 1.0727 |
| l1d_20261021 | 255.90 | 239.51 | 16.39 | 1.0684 |
| l1e_20261021 | 255.80 | 239.62 | 16.18 | 1.0675 |
| l1_20261023b | 181.50 | 165.06 | 16.44 | 1.0996 |
| l1_20261023 | 181.40 | 165.36 | 16.04 | 1.0970 |
| l3_20261023 | 181.30 | 164.39 | 16.91 | 1.1029 |

**delta = 16.75 ± 0.63 s（16.04 … 17.80），七份全部落在 16–18 s 的窄带里。**
这不是噪声，是**结构性漏计**（t0 空档 + stage 间隙）。

## 二、更正后的余量

| 算法 | 真实总时长估计 | 180 s 余量 |
|---|---:|---:|
| ~~§418 原报：sum 直接当总时长~~ | ~~143.94~~ | ~~36.06~~ |
| delta 均值 16.75 加回 | 160.69 | 19.31 |
| **delta 上界 17.80 加回（采用）** | **161.73** | **18.27** |
| ratio 上界 1.1029 放缩 | 158.75 | 21.25 |

⇒ **真实余量 18–21 s，不是 36 s。§418 高估了一倍。**

★ 取 **delta 上界**而非均值：余量估计宁可**偏低**，因为失败代价
（真机时段白跑一趟 + 用户在场时间）远高于「提前调参」的代价。

## 三、这条错误的性质：判据用错了量，不是算错了数

§418 的算式没问题（`180 − 143.94 = 36.06`），错在**分子取错了**：
`sum(stage_seconds)` 是 `elapsed()` 的**下界代理**，不是它本身。
这与本项目反复出现的同一族缺陷同型：

| 旧例 | 错法 |
|---|---|
| §414 判档器 | 用**被验证量**（polls）判型 ⇒ 循环论证 |
| 本轮 §418 | 用**代理量**（sum）当预算分子 ⇒ 余量虚高 |
| 共同点 | **判据算的是「方便算的量」，不是「判据真正比的那个量」** |

## 四、修法与负控（这里也踩了一次老坑）

`_preflight_h1.py` 新增 `duration_calibration()`：用同时有 `duration_s` 与
`fields` 的趟标定 delta，取上界加回；并把门限从 `>20` 收到 `>15`。

新增 M5 变异（把 `hist_max + cal_max` 改成 `hist_max + 0.0`，即退回旧错法）。
**首版 M5 存活**——因为我把新判据写成 `cal_max > 10`，而变异改的是
`hist_max_real`。**判据落在供给方（`cal_max`），没落在消费方
（`hist_max_real`）** ⇒ 改消费侧不影响断言。

★ 这正是记忆里 `gate-assert-values-not-existence` 的「变种 D」：
**断言要落在消费方，不是供给方**。改成断言 `hist_max_real > hist_max + 10`
之后 M5 立刻被捕获。

第二次跑 M5 仍然报 FAIL，但红项内容是对的（`rc=1`）——
是**验证器的预期子串**写成了「delta 校准」，而实际断言名是「校准已进入余量计算」。
★ **变异被捕获 ≠ 验证器判对**：黑盒匹配串与被测断言名是两套文本，必须对齐。

## 五、更正后的完整状态

| 项 | 值 |
|---|---|
| 飞行前检查 | **17/17 PASS**（原 16，新增校准断言） |
| 负控 | **8/8 PASS**（原 7，新增 M5） |
| h7a 真实余量 | **18.27 s**（非 36.06 s） |
| 其余结论 | **不变**：路径 110/134、载体 88/88、哈希、out-dir、进程 0 |

★ 判定相应收紧：**18 s 余量不算宽裕**。但结论仍然「不预先调参」——
真机是唯一能拿真实启动耗时的机会，且现在我知道该盯的阈值是 **180 s**
而不是我先前口头说的「36 s 余量很大」。
★ 若 h7a 撞 `EXIT_TRIP_BUDGET(18)`，直接证据是 `BUDGET.stage_begin:*`
最后一条的时刻；若停在 179–180 s 附近，说明只需放宽窗口预算而非改流程。
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
