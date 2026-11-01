#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§418 追加器：字节级追加，不动既有 CRLF 行。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

SECTION = """
---

# §418 H-1 飞行前检查 —— 窗口趟预算只剩 36 s，且它是**唯一**没放宽的那趟

**轮次目标**：§417 修好了命令文本，但「命令能粘贴」不等于「命令能跑完」。
本轮在用户不在场的前提下，把三条命令的**物理前提**逐条验掉，
让真机时段只剩「执行 + 读产物」两件事。

## 一、16 条检查全绿

| 组 | 项 | h7a（窗口） | h7b/h7c（全屏） |
|---|---|---|---|
| 路径 | 载体目录长度 | **110** < 127 WARN | 110 < 127 |
| 路径 | 最长载体全路径 | **134** < 260 MAX_PATH | 134 < 260 |
| 路径 | 最长件 = `[2]0LoadBench_U0400.yrm` | 载体目录 + 该件 | 同 |
| 状态 | out-dir 尚不存在（防旧证据混叠） | ✓ | ✓ |
| 状态 | 载体源目录存在 | ✓ 88 件齐全 | ✓ |
| 预算 | 单趟 / 单阶段上限 | **180 s / 30 s** | 540 s / 150 s |

★ 载体目录 **110**，距 127 WARN 还有 17 字符余量；最长全路径 134，
距 MAX_PATH 260 有 126 余量。路径这一项**不是风险**。

★ 载体源 `_src_L1_sf8_20261020` 复核：**manifest 88 = on-disk 88**，
missing 0 / extra 0 / **尺寸不符 0**；`gamemd.exe` 4,825,360 B
哈希 `73201cc021497c95` **仍等于冻结值**；`XMP29U2.MAP` 哈希
`0add791d11aea84d` 与发射器 `map_sha` 逐位一致。
★ 残留进程 `gamemd.exe` / `game.exe` 均为 **0**。

## 二、★ 真发现：h7a 是唯一**没被放宽预算**的那趟

`--fullscreen` 分支里有这两行（`:7391-7393`）：

```python
global STAGE_TIMEOUT_S, TRIP_BUDGET_S
STAGE_TIMEOUT_S = 150.0
TRIP_BUDGET_S = 540.0
```

而 **h7a 恰恰不传 `--fullscreen`（它就是要窗口模式）** ⇒ 预算仍是母本默认的
`180 s / 30 s`。三趟里只有它没有那张豁免。

盘上 35 份真实**窗口模式**产物（`archive_*`，按 `stage_seconds:*` 求和）：

| 口径 | 值 |
|---|---|
| 最大 | **143.94 s**（archive_T32） |
| 中位数 | 59.17 s |
| 标准差 | 49.26 s（**波动很大**） |
| 超 180 s 的 | **0 份** |

⇒ **余量 = 180 − 143.94 = 36.06 s**。工程上够用，但**不是宽裕**：
样本标准差 49 s 说明总时长受启动/导航波动支配（`nav_start` 2.8–60 s 级差），
历史上没爆只是因为样本还没撞上更慢的启动。

★ **单阶段上限更值得注意**：`measure_w0/w1/w2` 各自是独立阶段，
上限 30 s。42 个真实样本实测 **25.00–25.05 s、中位 25.02、标准差 0.007**
⇒ 这是**固定时长**（settle + 采样窗的构造值），不是负载相关
⇒ 余量约 5 s，**属设计留白，不是风险**。

★ 判定：**36 s 余量记为「可接受但需留意」**，不据此改任何参数 ——
真机时段是唯一能拿到真实启动耗时的机会，先测再谈调参。
若 h7a 真的撞上 `EXIT_TRIP_BUDGET(18)`，那是**有价值的观测**，
记下来正好标定「窗口模式预算该不该也放宽」。

## 三、装置与负控

`_preflight_h1.py`：**16/16 PASS**，只读不写（不建目录、不启动进程）。

`_verify_preflight_h1.py`：**7/7 PASS**，4 个变异全部被捕获：

| 变异 | 结果 |
|---|---|
| M1 载体目录阈值 127 → 50 | 红（h7a/h7b 都报） |
| M2 MAX_PATH 260 → 100 | 红 |
| M3 「out-dir 尚不存在」判据反转成「必须存在」 | 红 |
| M4 窗口预算余量门限 20 s → 999 s（实际余量 36） | 红（仅 h7a，因为只有它走这条判据） |

★ M4 的红项**只有 h7a**，这本身就是判据正确性的证据：
全屏两趟走的是「预算 540s/150s（放宽）」分支，不该受窗口预算判据约束。
若 M4 把三趟都判红，说明我把两种预算口径混在一起了。

## 四、交付件

| 件 | 说明 | 结果 |
|---|---|---|
| `_preflight_h1.py` | 飞行前检查（路径/状态/预算） | **16/16** |
| `_verify_preflight_h1.py` | 负控（4 变异） | **7/7** |
| `_probe_win_duration.py` | 窗口趟时长取证 | 35 份样本 |

★ 本轮**不改** harness、**不改**发射器、**不改**规划器参数。
它只回答一个问题：**「现在让用户坐到机器前，三趟有哪几件事会当场炸？」**
答案：路径不会炸、载体不会缺、目录不会撞、进程干净；
唯一需要盯的是 **h7a 的 36 s 预算余量**，且它的失败本身带信息量。
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
