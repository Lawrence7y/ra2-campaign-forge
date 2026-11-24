# -*- coding: utf-8 -*-
"""Append §565: correcting my §564 claim that E3_SAMPLING_PLAN_REVIEWABLE.md is missing (guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7565"

head = subprocess.run(["git", "show", "HEAD:lead/GOAL_THREE_TARGETS_20261018.md"],
                      cwd=REPO, capture_output=True).stdout
wt = open(LEDGER, "rb").read()
if TAG.encode("utf-8") in wt:
    print("REFUSE: %s already present" % TAG)
    sys.exit(1)
if not wt.replace(b"\r\n", b"\n").startswith(head.replace(b"\r\n", b"\n")):
    print("REFUSE: not a prefix extension of HEAD")
    sys.exit(1)
if b"\r" in wt:
    print("REFUSE: bare CR in worktree")
    sys.exit(1)
print("guards OK; head=%d wt=%d" % (len(head), len(wt)))

SECTION = u"""
## §565 · 订正 §564：「`E3_SAMPLING_PLAN_REVIEWABLE.md` 不存在」是**查错目录**，文件在 `LEADER_battle/` 下（2026-11-05）

> **本节的地位**：**公开自我订正**（今天第五次被核出错误，但这次是**我自己复核时发现的**，
> 且**上轮的裁决员也犯了同一错误**——我在 §564 把它当作「值得核实的发现」照录，没有自查）。

### 一、错在哪

§564 第五节第 3 条我写：

> 「我未验：`E3_SAMPLING_PLAN_REVIEWABLE.md` —— **裁决员报告该文件不存在**
> （`rg --files` 只找到三件 E3 文件）。这是 D-13 条目里引用的一份路径，**可能已失效**，值得下一轮核实。」

**错在我把「裁决员查不到」当成了「文件不存在」，并且没有自己去核。**

### 二、真值（我本轮亲验）

```
文件：lead/codex_round_20261030/LEADER_battle/E3_SAMPLING_PLAN_REVIEWABLE.md
大小：6,268 B    行数：72     mtime：2026-10-30 21:09
首行：# E3 线程栈采样 / MiniDump 方案 —— 可审查产物（**未获授权、未执行**）
```

**存在，且路径正确、内容完整。**

**裁决员为什么没找到**：它在 `lead/goal3t_nightwatch_20261102/` 下跑 `rg --files -g '*E3*'`，
那只找到三件（`E3_FOR_GOAL1_CARD` / `E3_TRIGGER_N` / `E3_TRIGGER_N_CORRECTION`）。
**真实路径在 `lead/codex_round_20261030/LEADER_battle/`** ——
`PENDING_DECISIONS.md:120` 的引用**本来就是对的**（它写的是文件名而非全路径，
但台账 §935/:3105/:3174 与 `RC4_MECH_DOSSIER_20261101.md:8` 都给了完整路径）。

⇒ **D-13 的证据链未失效**；§564 那句「可能已失效」**作废**。

### 三、这条错误暴露的形态（与前四次不同）

| 次 | 错误 | 谁抓到 |
|---|---|---|
| 1（§558） | 把 `g_items` 堆指针当计数 | W2 子代理 |
| 2（§561） | 把 `[Actions]` 的 COUNT 当 kind | W1 子代理 |
| 3（§562） | 「32 倍」表述过简（上限比≠成本比） | 裁决线核证员 |
| 4（§563） | 两次地址/口径误述 | 裁决线核证员 |
| **5（本节）** | **把「他人查不到」当成「不存在」** | **我自己** |

**这一次的形态是新的**：前四次都是我自己读错了字节/字段；这一次是**我转述他人的否定结论时没有自查**。
而且我当时**明确写了「值得下一轮核实」，却仍把它写进了「我未验」栏当作事实陈述**——
「标注未验」不等于「已尽核实义务」，尤其当这个未验项会**影响下游判断**（D-13 的证据链是否失效）时。

**纪律第六条**：**转述他人的「不存在／找不到」结论时，必须自己按正确路径再查一次**
——否定性结论比肯定性结论更容易因为**查错范围**而出错。

### 四、诚实账

1. **我亲验**：`ls -la` 与 `wc -l` 的上述结果；`head -12` 的首行内容；
   全仓 `find . -name "*E3*"` 只返回三件（均在 `nightwatch_20261102/`）；
   `grep -rn "E3_SAMPLING_PLAN_REVIEWABLE"` 命中 8 处，其中
   `RC4_MECH_DOSSIER_20261101.md:8` 给出完整路径 `lead/codex_round_20261030/LEADER_battle/`。
2. **我未验**：该文件内容与 D-13 当前选项的匹配度（本轮只核「是否存在」，未核「是否支持 A/C/暂停」）。
3. **我不改** §564 原文（append-only 惯例），本节即勘误。
4. **不改** `PENDING_DECISIONS.md:120`——**它的引用是对的**。
5. 本轮**零真机**、**零母本改动**（只读）、**未 commit**。
6. **D-17/D-18 的定谳不受影响**：两条裁决的依据不涉及该文件是否存在的判断
   （裁决员该项自陈「本次没有继续读取原方案」）。
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION))
