# -*- coding: utf-8 -*-
"""Append §562: pathfinding node budget 2000 -> 65527 (guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7562"

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
## §562 · 「Dijkstra 2000 节点」**不成立**：真实默认预算是 **65527**（`0xFFF7`），差 32 倍（2026-11-05）

> **本节的地位**：**推翻仓内既有文档**的实质结论。
> 发现者 = W3 的 `Q1_C1_PATHFIND.md`（`lead/re_line_20261105/W3_COSTBOUND/sections/`，未过复核阶段）；
> **我逐字节复核确认**（探针 `_leader/_v_c1_budget_probe.py`，原始输出 `_out.txt`）。
> 被推翻的记载：`docs/re/pathfinding_deep_dive.md:46-51,68-74` 的「单次 Dijkstra 最大 2000 节点」，
> 以及 W2 定稿 §3.2 把它写进候选表的那一条（W2 是采信文档，不是它的错）。

### 一、2000 从哪来、又怎么丢的（我亲验的字节链）

**① 外层外层确实压了 `0x7D0`（2000）** —— `0x4D3E3B`：

```
004D3E37  51              push ecx
004D3E38  53              push ebx
004D3E39  6a00            push 0
004D3E3B  68d0070000      push 0x7d0          ← 2000 在这里
004D3E40  8d8424c01f0000  lea eax,[esp+0x1fc0]
004D3E47  52              push edx
004D3E48  50              push eax
004D3E49  8bcd            mov ecx,ebp
                            (call 0x4CBBA0 = FootClass::CallFindPath)
```

既有文档就是看到这条 `push 0x7D0` 推断出「上限 2000」的。

**② 但中间层把它丢了** —— `0x4CBC1B` 起的原始字节 `50 6a ff 6a ff …`：

```
004CBC1B  50              push eax
004CBC1C  6aff            push -1            ← arg5 = -1（常量，不是 0x7D0）
004CBC1E  6aff            push -1            ← arg4 = -1（常量，不是 0x7D0）
004CBC20  89542414        mov [esp+0x14],edx
004CBC24  57              push edi
...
004CBC2C  b9b8e88700      mov ecx,0x87E8B8   ; PathFinder 单例
004CBC31  e8...           call 0x42C900      ; PathFinder::FindPath
```

⇒ **`0x7D0` 在 `CallFindPath` 里被完全丢弃**，传给底层的 `arg4/arg5` 是常量 `-1`。

**③ 底层把 `-1` 重写成 `0xFFF7`** —— `0x429D59` 原始字节 `c7 44 24 70 f7 ff 00 00`：

```
00429D51  8b442470        mov eax,[esp+0x70]     ; arg4 = -1
00429D55  85c0            test eax,eax
00429D57  7d08            jge 0x429D61           ; >=0 就保持
00429D59  c7442470f7ff0000 mov dword [esp+0x70],0xFFF7   ; ← 否则强制 65527
```

⇒ **真实默认节点预算是 `0xFFF7` = 65,527，是 2000 的 32.76 倍。**

### 二、这对目标①意味着什么

1. **C1（寻路）的理论成本上限被低估了 32 倍。**
   W2 与我此前所有基于「2000 节点」的"数量级排除"论证**全部作废重算**；
   W3 正在做的数量级上界必须用 65527 这个真值。
2. **W2 定稿 §3.2 里「Dijkstra 2000 节点」这一括号注记需勘误**（其结论方向不受影响：
   C1 仍是头号嫌疑，而且现在**更强**）。
3. **`docs/re/pathfinding_deep_dive.md:46-51,68-74` 需要勘误**——这是仓内既有 RE 文档的实质错误，
   不是我本线的产物。**建议由 RE-ATLAS 线或本线下一轮追加勘误节**（本轮只登记，不改他线写域）。

### 三、这也解释了为什么 W3 的任务书要求「进函数体核实」

我在 `W3/TASK.md` 里写了三条纪律，其中第一条正是：
「凡『A 调用 B ⇒ A 具有 B 的性质』形式的推理，必须进 B 的函数体核实字节」。
**W3 严格执行了它，于是抓到了这个 32 倍的错误。**
而 `docs/re/pathfinding_deep_dive.md` 当年恰恰只看了外层 `push 0x7D0` 就下了结论——
**这是同一条纪律的又一个反例，只是发生在我接手之前。**

### 四、诚实账

1. **我亲验**：`0x4D3E3B push 0x7d0`；`0x4CBC1B..0x4CBC22` = `50 6a ff 6a ff 89 54 24 14 57`；
   `0x429D59..0x429D60` = `c7 44 24 70 f7 ff 00 00`；三段反汇编逐条。
2. **我未验**：`0xFFF7` 这个预算**实际怎么被消费**（是节点数上限还是别的计数），
   W3 的节文件说它是「预算」，我未进 SearchCore 主循环核对它的递减/比较点；
   **W3 节文件本身也仍是未过复核的初稿**。
3. **我未验**：`0x7D0` 在 `CallFindPath` **更深处**是否以别的形式被重新读取
   （我只 dump 了 `0x4CBBA0..0x4CBC3B` 的 0xA0 字节，函数在 `ret 0x18` 前是否还有别的路径未全查）。
4. **我未验**：`docs/re/pathfinding_deep_dive.md` 原文的确切措辞（我未读该文件，只引用 W3 的转述）。
5. 本节**不改动任何他线写域**（`docs/re/` 未改一字）；**零真机**、**零母本改动**、**未 commit**。
6. **本节不改变已裁结论**：D-16/D-15/D-13 处置不变；E3 维持「暂停」。
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION))
