# -*- coding: utf-8 -*-
"""Append §552: serial rotation discipline for the two backup channels (guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7552"

head = subprocess.run(
    ["git", "show", "HEAD:lead/GOAL_THREE_TARGETS_20261018.md"],
    cwd=REPO, capture_output=True).stdout.replace(b"\r\n", b"\n")
wt = open(LEDGER, "rb").read()
if TAG.encode("utf-8") in wt:
    print("REFUSE: %s already present" % TAG)
    sys.exit(1)
if not wt.startswith(head):
    print("REFUSE: not a prefix extension of HEAD")
    sys.exit(1)
print("guards OK; head=%d wt=%d" % (len(head), len(wt)))

SECTION = """
## §552 · 备选双通道串行轮换纪律（2026-11-05 用户令）

> **本节的地位**：用户 2026-11-05 口述纪律，写死入账。
> 与 §551 同属派发层纪律，不涉及分析结论。

### 一、用户令原文要点

> 「Gemini 3.8 Flash、DeepSeek V4.1 Flash 这两个模型不要并发太多，让他们交叉使用。」

### 二、写死的规则

推进任务可用的备选通道**只有两条**：

```
备选 A : magpie/antigravity/gemini-3.8-flash
备选 B : new-provider/cn:deepseek-v4.1-flash      （ListModels 标 disabled 则跳过）
```

**纪律**：
1. **交叉轮换**：上一轮用 A，下一轮用 B，交替使用。
2. **不并发**：**同一时刻只允许一个推进工作流在飞**。不得同时开 A 和 B。
3. **不连续占用**：同一模型不连续占用超过一个 run。
4. **换道顺序**：A 报错 → 换 B；B 也报错 → **停下列给用户**，不自行换被禁模型。
5. **裁决不受此限**：`magpie/codex/gpt-6.1-sol` 的裁决工作流可与其他并行。

### 三、为什么这条重要

前一夜的实际情况是反例：`dwfrun-72de3cd1` 空等 1h38m（`server_error` 退避），
期间我**没有换道也没有开第二条**——既没守住「报错就换」，也没建立轮换机制。
如果当时并发开多路，问题会变成「多路一起空等、额度一起烧」；
如果像现在这样一路死等，问题就是「卡住 1.5 小时零产出」。
**串行 + 报错即换** 是这两个坏结果之间唯一可行的那条路。

### 四、当前在飞（本节落笔时）

| run | 模型（完整 ID） | 状态 |
|---|---|---|
| `dwfrun-65734a63` | `magpie/antigravity/gemini-3.8-flash` | running（备选 A，N16-4 目视） |

**符合纪律**：只有一路在飞。

### 五、诚实账

1. 这是**用户订正**，不是我自行发现。我在 §551 之后仍然没有主动想到「并发上限」这件事。
2. 我在派 `dwfrun-65734a63` 时并未预告「这是备选 A，下次应换 B」——**轮换状态没有记录载体**。
   本节即为该载体：**每轮派发前先查本节的最新一条，确认上次用的是哪一路。**
3. 本节**未 commit**；**零真机**；**未改任何母本**。
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION.encode("utf-8")))
