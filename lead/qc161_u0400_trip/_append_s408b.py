#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§408b 追加：§408 的两处补记（CRLF 事故 + 判档器窗口模式盲区）。

★ 为什么不改 §408 本体：§408 已经写进台账，**重写既有段落**会触发
  「整文件重写 ⇒ 行尾被改」的老问题（§403 / §408 各踩一次）。
  用独立小节追加，既有内容一字不动。
"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")

SECTION = """
## 七、★ 补记 A：§407 的盲区 —— 窗口模式趟被判成「不是冒烟样本」

修发射器时核对 harness7 的写入条件，发现两行 rec 的**前提不同**：

| 行 | 位置 | 条件 |
|:--|:--|:--|
| `h7_fs_rect_wait_skipped` | `:7364` 起 | 整块包在 `if args.fullscreen:` 里 ⇒ **只在全屏写** |
| `pre_capture_wait_polls` | `:8109` | **无条件写** |

而 §407 的判据是「`skipped` 与 `polls` 都非 None 才算冒烟样本」
⇒ **窗口模式趟（第 1 趟）永远被判「不是冒烟样本」**，而那恰恰是
D-05 冒烟要验的三种形态之一。

⇒ 改法：判据变为「`polls` 在场即可」；窗口模式下断言 `skipped` **不在场**。
窗口模式的正确值不是 `skipped=False`，而是**那一行根本不存在**。

★ 这个改动又逼出一处**死数据**：`H7_SMOKE["windowed"]["skipped"]` 这个键
**从未被读取**（窗口模式走另一条分支）。变异自检 M2 去改它，**没有任何断言变化**
⇒ 当场删掉该键。**留着它等于给后人一个「改这里有用」的错觉。**

新增合成趟 S9（窗口模式但 polls=40）证明窗口模式**确实被真判**，
不是「判不出来就放过」。

## 八、★ 补记 B：本轮自己造成的 CRLF 污染（第二次同类事故，已修）

提交前查 `git diff --numstat` 发现判档器 **+580/−551** —— 而真实改动只有几十行。

**根因**：该文件**行尾基线是纯 LF**（HEAD 侧 CRLF=0），而 `Edit` 工具在 Windows 上
**整文件重写**并写成 CRLF ⇒ CRLF 计数 **0 → 580**，逐行都算一次重写。

**修法**：`bytes.replace(b"\\r\\n", b"\\n")` 复原。`+580/−551` 立刻回到 **+43/−14**。
修后三个验证器重跑：21/21、36/36、22/22 全绿。

★ 与 §403 的台账事故**同族但方向相反**：

| 事故 | 基线行尾 | Edit 的破坏方向 |
|:--|:--|:--|
| §403 台账 | **混合**（86 CRLF + 15k bare-LF） | 把 86 个 CRLF **抹成 LF** |
| §408 判档器 | **纯 LF** | 把全部 LF **转成 CRLF** |

⇒ 教训不是「别用 Edit」，而是 **Edit 之后必须查 `--numstat`**：

- 纯追加件：删除数应为 **0**；
- 局部修改：行数应与改动规模**相称**；
- **删除数远超真实改动 = 行尾被动过**，与内容无关。

★ 第三次同族事故了（§403 台账、§403 修复脚本、§408 判档器）。
**这条纪律应写进动手清单，而不是每次事后发现。**
"""


def main() -> int:
    before = LEDGER.read_bytes()
    payload = SECTION.encode("utf-8")
    if not payload.endswith(b"\n"):
        payload += b"\n"
    after = before + payload
    assert after.startswith(before), "append must preserve prefix"
    assert len(after) == len(before) + len(payload), "size arithmetic"
    assert before.count(b"\r\n") == after.count(b"\r\n"), "CRLF must not change"
    print("before %d B / lines %d / CRLF %d"
          % (len(before), before.count(b"\n"), before.count(b"\r\n")))
    print("append %d B -> after %d B / lines %d / CRLF %d"
          % (len(payload), len(after), after.count(b"\n"), after.count(b"\r\n")))
    LEDGER.write_bytes(after)
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
