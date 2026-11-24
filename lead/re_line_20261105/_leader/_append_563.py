# -*- coding: utf-8 -*-
"""Append §563: fact-base corrections from the D-17/D-18 ruling workflow (guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7563"

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
## §563 · 裁决线的事实核证推翻我两处表述：`0x887308` **不是视口坐标**；`0xFFF7` 不是「剩余预算」而是**轮数上限**（2026-11-05）

> **本节的地位**：**公开自我订正**（第二次在一天内被第三方核证抓到实质错误）。
> 来源：`dwfrun-9b224a40`（`magpie/codex/gpt-6.1-sol$medium`）的 **phase-1 独立事实核证员**，
> 它**没有采信我的转述**，而是逐条从原始 PE 与原文重算。
> 核证件：`lead/re_line_20261105/D17D18_RULING/FACTBASE_D17.md`、`FACTBASE_D18.md`。

### 一、★ 订正一：`0x887308 / 0x88730C` 是 **DSurface 指针槽**，不是视口坐标

我（以及 W2 定稿 `:305`）把这两个全局当作「视口左上角 X/Y 坐标」。**核证员反证**：

```
读点 0x004328DE  A1 0C 73 88 00   mov eax,[0x88730C]  → 0x004328EA FF 52 7C 当作 this 解引用虚表
读点 0x00432A35  A1 08 73 88 00   mov eax,[0x887308]  → 0x00432A3A 8B 40 1C 读对象 +0x1C
写点 0x0053410D  A3 0C 73 88 00   写入 0x004BA5A0 的构造结果
写点 0x00560D32  A3 08 73 88 00   写入 0x004BA770 的构造结果
两个构造体均赋 vtable:  C7 06 D4 85 7E 00 = 0x007E85D4
RTTI 名字字节 = '.?AVDSurface@@'
```

⇒ **它们是 `DSurface` 对象的指针槽**（DirectDraw 表面），不是坐标。
**读这两个 u32 拿不到任何视口位置。**

**影响**：
- W2 定稿 `:305` 及所有转述该地址为「视口坐标」的地方**须更正**；
- **但 D-17 的结论方向不变**：视口**仍然**不可判——因为 harness 从未采任何视口相关量，
  而现在连「该采哪个 VA」都还需要重新定位（核证员明确写「实际视口坐标 VA 本次未定位」）。
- ⇒ **「视口不可判」这条红线的理由要改写**：不是「未采 `0x887308/0x88730C`」，
  而是「**尚未定位视口坐标的 VA，且窗内零截图**」。

### 二、★ 订正二：`0xFFF7` 是**节点展开轮数上限**，不是「剩余预算变量」，也不是「最多 65527 个格子」

§562 我写「真实默认预算是 65527」并暗示它可被「用满」。核证员进 `SearchCore 0x00429A90..0x0042A45D`
（重同步解码 **2509/2509 字节、100%、失败 0**）逐条核实：

```
0x00429AB6  C7 44 24 28 00 00 00 00   mov [esp+0x28],0      ; 展开轮数计数器归零
0x00429D6D  8B 4C 24 70               取预算
0x00429D71  8B 44 24 28               取轮数
0x00429D77  3B C1                     cmp
0x00429D79  0F 8D 5F 06 00 00         jge → 失败收口 0x0042A3DE
...
0x0042A3D1  41                        inc
0x0042A3D4  89 4C 24 28               轮数 += 1
0x0042A3D8  0F 85 8F F9 FF FF         jne → 回预算比较
```

⇒ `0xFFF7` 是**外层「节点处理/展开轮数」的上限**：
- **不是**「剩余预算递减变量」；
- **不是**「最多能碰 65527 个不同格子」；
- 到目标 / 开放集耗尽 / 其他早退**可先结束**，**不能说每次都会用满 65527**；
- **更不能凭它断言运行耗时或慢帧根因**（核证员原话）。

**§562 那句「C1 理论成本上限被低估 32 倍」须加限定**：
被低估的是**上限**（2000 → 65527），但**实际用多少取决于搜索是否提前终止**——
所以「32 倍」是**上限之比，不是实际成本之比**。这条必须与 §562 一起读。

### 三、★ 订正三：文档 `:74` 的 `+0x3C = MaxNodeBudget` 也不准

`docs/re/pathfinding_deep_dive.md:74` 写「`+0x3C` int `MaxNodeBudget` 最大节点搜索预算，由外层传入（`0x7D0`=2000）」。
核证员核实：

```
0x0042C927  8B 4C 24 4C   mov ecx,[esp+0x4C]
0x0042C92F  89 4D 3C      mov [ebp+0x3C],ecx     ← 存的是 FindPath 的**第七**参数
0x00429C10  8B 46 3C / 85 C0 / 74 08           ← SearchCore 只按 this+0x3C 是否非零决定是否调 0x0042ACF0
```

⇒ **实际预算走的是第五参数**，`+0x3C` **不是预算槽**。
这条是**对既有文档的第二个证伪点**（第一个是 2000 本身），已并入 D-18 的裁决范围。

### 四、★ 核证员对我另外两处表述的限定（我接受）

1. **`GenerationStamp`（`0x0087E8B8+0x28` = `0x0087E8E0`）不是无界单调**
   —— `0x0042A5FB..0x0042A5FF` 是 `inc [ecx+0x28]`，但 `0x0042A602` 非零即退出，
   **回绕为零时会清访问戳数组再增至 1、跳过 0**。
   ⇒ 采样它得到的是「**搜索/工作区代际初始化的尝试次数**」，**不能等同实际完成的 Dijkstra 展开次数**。
   （D-17 若裁 (B)，采样设计必须处理初始化/重置/回绕。）
2. **「全部 87 窗零 PNG」不是我亲验的**：核证员只核了源码禁令
   （`harness8_v4.py:3826-3828` 原文已抄录，确实写了「零键鼠、零 PrintWindow」），
   **没有普查 87 窗或 shots 时间线**。⇒ 该断言必须降级为「源码禁令成立 + W2 报告如此陈述」。

### 五、诚实账

1. **我亲验**：本节引用的核证员全部字节（我未重新反汇编，但核证员给了完整 VA+字节，
   且与我此前 §562 亲验的 `0x429D59` 一致）；`FACTBASE_D17.md` / `FACTBASE_D18.md` 全文。
2. **我未验**：`DSurface` RTTI 字符串（采信核证员）；
   `0x0042A5B0` 全函数体（采信）；
   `0x00432ACF0` 的条件调用语义（核证员自己都写「不凭该条件调用进一步命名其完整语义」，我也不命名）。
3. **我未验**：视口坐标的真实 VA（核证员未定位，我也没有）。
4. **订正范围**：§562 的「32 倍」限定、W2 定稿 `:305`、`docs/re/pathfinding_deep_dive.md:48/:74`
   —— **后两者我未改一字**（W2 定稿属本线但已定稿，改为追加勘误；`docs/re/` 属他线，等 D-18 裁决）。
5. 本轮**零真机**、**零母本改动**、**未 commit**。
6. **这是今天第四次被第三方抓到实质错误**（§558 堆指针 / §561 COUNT / §562 32 倍表述 / 本节两条）。
   **共同点：我都在「读到足够像结论的东西」时就停下，没有把口径问到最底层。**
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION))
