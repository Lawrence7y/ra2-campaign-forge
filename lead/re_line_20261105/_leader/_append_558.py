# -*- coding: utf-8 -*-
"""Append §558: g_items pointer-vs-count correction + W2 candidate ranking intake (guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7558"

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
## §558 · 我把堆指针当成了计数：`g_items` 是 `Items` 指针，`g` 才是计数——慢组 `g` 反而高 31%（2026-11-05）

> **本节的地位**：**公开自我订正** + 回收 W2 初稿的候选排序。
> §556 第三节我写「`g_items` 慢组 256,152,480 / 快组 369,700,440 ⇒ 快组更大 ⇒ 方向反 ⇒ 非成本源」，
> 这条推理**整条作废**：`g_items` 是**堆内存指针**，不是计数。
> W2 回件（`dwfrun-f7182e80`，`magpie/antigravity/gemini-3.8-flash$high`）抓到，
> 我自己写探针（`lead/re_line_20261105/_leader/_v_g_probe.py`）独立复现。

### 一、错在哪

| 字段 | 我上一轮的理解 | 真实语义 |
|---|---|---|
| `g_items`（VA `0x008A0394`） | 「G 的对象计数」 | **`DynamicVectorClass::Items` 堆指针**（`MapClass::ObjectsInLayers` Layer-2 = Ground 的缓冲区首地址） |
| `g`（VA `0x008A03A0`） | 未使用 | **真正的 Count（地面层对象数）** |

**最刺眼的一点**：证据就在我自己引用的那个函数里——
`lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:3981-3982` 的 docstring 明写：

> `Items 形状自检 D-3：Items != 0 ∧ Count ≤ 100000 —— Items 是**指针**，
> 禁用 Count−Items==0xC（把指针当计数，恒假；§3.6-D3）`

我在 §556 引用了同一文件的 `:3838-3841` 定义，**却没有读下面两行的警告**，
并把 `.get('g_items')` 当成计数去做「方向反」的推理。
**这是「引用了一个文件却没读它自带的警告」的典型。**

### 二、订正后的数值（我亲验）

`_v_g_probe.py` 对 35 个 25s 窗按快/慢两组统计 `g`（窗内均值）：

```
SLOW (n=21)  g 中位 = 1504.1   范围 1093.4 … 1802.8
FAST (n=14)  g 中位 = 1148.4   范围  971.8 … 1540.5
慢组/快组 中位比 = 1.310
```

单窗对照（W2 给出、我复现）：

| 趟 | p50 | `g` | `g_items`(hex) | `b` |
|---|---:|---:|---|---:|
| `l3_1101v4d`（快） | 32.31 | **1589** | `0x16092E58` | 3 |
| `l3_1101v3a`（慢） | 82.50 | **1832** | `0x0F4493A0` | 0 |
| `l3_20261031hb`（慢） | 106.62 | **1828** | `0x0F4493A0` | 0 |

⇒ **慢组的真实地面层对象数反而高约 31%**，「方向反 ⇒ 非成本源」**不成立**；
真实方向与「对象越多越慢」**一致**（但这仍是相关性，不是因果——§549/§529 的否定结论不变，
它们用的是 `units0` 与单位数，不是 `g`）。

`ws_kb`/`pf_kb` 的「快组更高」同理降级：差值 <0.8%（约 1 MB），
W2 解释为快组有 3 个建筑实例、多加载了建筑 SHP/Art 资源。**该解释我未独立验证**，标 [推演]。

### 三、W2 的候选排序（初稿，**其自身复核阶段仍在跑，不得当定稿引用**）

W2 给出 7 项候选，我照录其排序与「能否离线判死」：

| 排序 | 候选 | W2 定性 |
|---|---|---|
| **C1** | 寻路 / 阻挡碰撞（`FootClass::UpdatePathfinding` @`0x4D3920`，单次 Dijkstra 预算 2000 节点，**跨单位零缓存**） | **最高嫌疑**；定量定谳**不可判**（未采 `0x87E8B8+0x28` GenerationStamp） |
| **C2** | 渲染 / 视口裁剪（`DrawIfVisible` v[65]，视口外单位短路） | **核心主嫌疑**；**现有数据永远不可判**（窗内零截图、从未读视口 `0x887308/0x88730C`） |
| C3 | 「建筑存在性改变战局宏观拓扑」（有建筑→集结围攻 vs 无建筑→全图巡逻） | 关键催化变量 |
| 排除 | 输入/焦点失焦 Sleep（`0xA8ED80`）、节流器 Sleep（`0x55E160`）、宿主降频/进程环境、音频调度风暴 | 斩死 |
| 降级 | AI 决策复杂度爆炸 | 靶图 `[2]0LoadBench_U0400.yrm` **无 `[TeamTypes]` 与 `[AITriggerTypes]`** |

**W2 另给两条「永远判不了」的红线**（我认为这是本轮最有价值的诚实部分）：
1. 渲染层视口位置与屏内可见单位数——harness 守「测控零扰动」，**窗内零截图**，且从未读视口 VA；
2. 微观寻路调用次数与耗时——**从未采样**寻路单例与单位移动状态机，
   500 Hz 逻辑帧沿**无法拆解帧内微观函数用时**。

⇒ 这与我 §A7 挂账的「周期性未查成」是同一条边界：**现有语料只有帧沿，没有帧内分解**。

### 四、连带处置

1. **§556 第三节那张「第一层筛查」表**里的 `g_items` 与 `ws_kb`/`pf_kb` 两行**作废**，以本节为准；
   同表的 `b_valid` 行**仍然成立**（那是布尔形状自检，不是指针语义）。
2. **§556 第三节的受控对照事实不变**（同图 units0±10% 却帧时差 2–5.7 倍）。
3. **不改变任何已裁结论**：D-16/D-15/D-13 处置不变；E3 维持「暂停」。
   C1/C2 两条主嫌疑**都指向需要帧内采样才能定谳** ⇒ **更加印证 D-13 的取舍是实质性的，不是流程拖延**。
4. **W1 侧**：`dwfrun-3eee0767` 的 Q3（来源完备性）与 Q3b（地图普查）**已 38 分钟无进度**，
   本线如实登记为「疑似子代理挂起」，本轮不干预（running 零干预纪律）；若下轮仍无进度按换道处理。

### 五、诚实账

1. **我亲验**：`g` 的 35 窗分组统计与中位比 1.310；三趟单窗 `g`/`g_items`/`b` 数值；
   `harness8_v4.py:3981-3982` 的 docstring 原文。
2. **我未验**：`0x008A0394` 是否确为 `ObjectsInLayers[2]+0x04`（**采信 W2 引用的 `ARCHITECTURE_ATLAS.md:3975` 等**，我未逐条读原文）。
3. **我未验**：W2 的 7 项候选排序与其中任何机制判断——**其复核阶段（phase 3）此刻仍在跑**，
   本节只是「照录 + 标注未定稿」，**不构成对 C1/C2 的背书**。
4. **我未验**：`ws_kb` 高 0.8% 的「建筑资源加载」解释（标 [推演]）。
5. 本轮**零真机**、**零母本改动**、**未 commit**。
6. **本轮教训（写给下一轮的我）**：
   **引用一个文件时，必须读它紧邻的注释/警告，不能只读我要的那几行。**
   §556 那次如果读了 `:3981`，整条错误推理不会发生。
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION))
