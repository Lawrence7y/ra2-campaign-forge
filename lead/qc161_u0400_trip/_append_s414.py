#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§414 追加器：字节级追加，不动既有 86 行 CRLF。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

SECTION = """
---

# §414 判档器用「被验证量」当判型依据 —— 循环论证，且红在错误原因上

**轮次目标**：§413 让三趟命令可复跑了。本轮做最后一件事：**用盘上 50 份真实产物
反查判档器的判据是否站得住**。结果查出一个循环论证。

## 一、起点：`polls` 到底是什么量

先把真实产物摊开看。50 个见证趟目录，有 `pre_capture_wait_polls` 的 35 趟，
其中全屏且 polls 在场的 10 趟：

| 趟 | polls | stage_seconds:frame | 秒/poll |
|---|---:|---:|---:|
| l3_20261021 | **96** | 48.157 | 0.5016 |
| l3_20261023 | 244 | 122.140 | 0.5006 |
| l1e_20261021 | 244 | 122.187 | 0.5008 |
| l1c_20261021 | 247 | 123.704 | 0.5008 |
| l1_20261023 | 251 | 125.703 | 0.5008 |
| l1_20261023b | 251 | 125.719 | 0.5009 |
| t55k_20261020 | 252 | 126.187 | 0.5007 |
| l1_20261023c | 253 | 126.657 | 0.5006 |
| l1a_20261020 | 253 | 126.688 | 0.5007 |
| l1d_20261021 | 253 | 126.704 | 0.5008 |

**秒/poll 恒为 0.5007 ± 0.0003，十趟全中。**
对应 harness `:8103-8106` 的循环：`time.sleep(0.5)` 一次算一次
⇒ **`polls` 的语义是「等了几个 0.5 秒 tick」，是时长的代理量，不是次数上限。**

★ `l3_20261021` 的 96 **不是异常**：它 frame 段本来就只有 48 秒，
矩形在那时就变成 800×600 了。同一天的另一趟 `l3_20261023` 是 244/122 s。
**同一份地图可以跑出 96，也可以跑出 244。**

## 二、由此暴露的缺陷：判型用了被验证量

原判法（§408 引入）：

```
if skipped is True:            form = "fullscreen_short"
elif polls >= 200:             form = "fullscreen_keep"     ← 问题在这
else:                          form = "windowed"
```

而对照组臂的断言恰恰是 `polls_min = 200`。**判型先假定 polls ≥ 200 才归入
对照臂，然后再断言「polls ≥ 200」** ⇒ 该断言**恒真**，改它不会让任何趟变红
⇒ 零信息量（与既有记忆 `gate-assert-values-not-existence` 的恒真式同型）。

**更糟的后果**：对照臂若 polls < 200（如 l3 那种短帧），会被判成 `windowed`，
于是去判「窗口模式**不该写** `h7_fs_rect_wait_skipped`」——
而对照臂**确实**写 `skipped=False` ⇒ 该趟被判红，
**且红在错误的原因上**：报告会说「窗口模式不该有 skipped」，
而真相是「polls 不足」。排查方向直接被带偏。

## 三、修法：判型只许用直接证据

| 判据来源 | 是否可用于判型 | 理由 |
|---|---|---|
| `META.fullscreen` | ✅ | harness 只在 `--fullscreen` 时写（`:7382`），窗口模式**根本不写** ⇒ 「无此字段」即窗口模式的直接证据 |
| `h7_fs_rect_wait_skipped` | ✅ | harness7 只在全屏分支写；`True`=短路 / `False`=保持死等 ⇒ 直接区分两个全屏臂 |
| `polls` | ❌ | 是**被验证量**，用它判型 = 循环论证 |

新判法：

```
if fs_flag is None:            form = "windowed"
elif skipped is True:          form = "fullscreen_short"
elif skipped is False:         form = "fullscreen_keep"
else:                          # 全屏但 skipped 缺失 ⇒ 没跑到矩形等待
    → 明确报「不是冒烟样本」，return（不产生断言）
```

★ 那个 `else` 分支也要紧：全屏但 `skipped` 缺失 = 该趟没跑到矩形等待那一步
（多半提前失败）。这是「**不是冒烟样本**」，不是「判据不通过」——
两者混为一谈会让失败趟被记成设计违约。

## 四、负控：新增 S10，专打这个缺陷

S10 = **对照臂但 polls=96**（`skipped=False` + `META.fullscreen` 在场 +
frame 48.2 s，完整复刻 l3_20261021 的真实形态）。

| 断言 | 结果 |
|---|---|
| 识别为 `fullscreen_keep`（不是 windowed） | ✓ |
| 变红 | ✓ |
| 红在 `pre_capture_wait_polls ≥ 200` | ✓（红在该红的原因上） |
| **承重性**：旧判法在同一产物上给出 `windowed`（与新判法不同） | ✓ |

**25/25 PASS**（原 22 + S10 三条）。

★ 过程中 S10 首跑 rc=2：我抄了 S5 的 `make_w12=False`，而 S5 是靠
`verdict="late_start"` 走短路分支的；S10 是 `verdict="ok"`，缺 w1/w2
会在 `[1] measure 三窗` 就被判「产物异常」而**根本到不了 `[4b]`**。
⇒ 造样本时「照抄相邻样本的参数」是坑：**参数的含义依赖于该样本走哪条分支**。

## 五、对 H-1 真机三趟的影响

- 第 1 趟（窗口）：`META.fullscreen` 不在场 ⇒ 直接判 windowed，比原先更硬；
- 第 2 趟（短路）：`skipped=True` ⇒ 判 short，与原先一致；
- 第 3 趟（对照臂）：`skipped=False` + fs 在场 ⇒ 判 keep，**不再依赖 polls 是否够 200**。
  ★ 这意味着即使对照臂因战斗提前结束只等到 96，判档器也会正确识别为 keep，
  并把「polls 不足」作为**真实观察**报出来，而不是伪装成窗口模式。

## 六、交付件

| 件 | 改动 | 结果 |
|---|---|---|
| `_judge_l1_20261023.py` | 形态识别改用 META.fullscreen + skipped（+25/−10） | 纯 LF 保持 |
| `_verify_h2e_smoke.py` | 新增 S10 三条断言（+28/−0） | **25/25** |
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
