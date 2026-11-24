# -*- coding: utf-8 -*-
"""Append §560: W2 intake (guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7560"

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
## §560 · W2 收官：5.7 倍帧时差收敛到四个成本中心，但三条**靠现有数据永远判不了**（2026-11-05）

> **本节的地位**：回收 `dwfrun-f7182e80`（`magpie/antigravity/gemini-3.8-flash$high`，1h58m，
> **30.1M tokens**，五阶段全跑完，确定性门槛 `exit=0`）。
> 定稿：`lead/re_line_20261105/W2_FRAMETIME_ATTRIB/W2_FRAMETIME_ATTRIB.md`（40.5 KB）
> + 全量表 `_w2_matrix.tsv`（87 行 × 12 列）+ 探针 `_w2_probe.py`。
> **复核判定**：`b_valid` **CONFIRMED**(2 异议) / 全表 **CONFIRMED**(4 异议) / 候选 **PARTIAL**(5 异议)。
> **按纪律：第三份不得当 confirmed 引用。**

### 一、已确认（复核 CONFIRMED）

**① `b_valid` 语义（我上一轮的中期发现被独立确认）**
`b_valid=false` ⟺ 建筑实例向量处于**惰性未分配初始态**（`b_items=0 ∧ b=0`），**与帧时无因果**。
- `harness8_v4.py:3979-4001` 判定式、`:3981-3982` 的「Items 是指针」警告；
- `gamemd.exe:0x007E9E20` RTTI = `DynamicVectorClass<BuildingClass*>`；
- `gamemd.exe:0x004E6B60` CRT 静态构造置 `0xA8EB44/0xA8EB50` 为 0；
- `gamemd.exe:0x0043BAD6..0x0043BB24` 建筑构造首增才 `Resize`；
- **反例双证**：`t55k_20261020/w0` 全 false 但 `32.24ms/31.24fps` 满帧；
  `l3_1101v4c/w2` 全 false 但 `32.42ms/30.68fps`。

**② 87 窗全表（分母与对子全部对账）**
N=87（29 趟×3 窗），排除 15 份 4s/0s 短窗 + 2 份根散件。
同图且 `units0` 差 ≤10% 却 `p50` 差 >1.5 倍：**107 对**（大者基准，含 25 对临界透明标注）/ 82 对（小者基准）。
**只有 2 张图慢**：`f3bb0a4e`（中位 41.79ms）、`0add791d`（中位 75.72ms）；
**其余 7 张图 31.64–32.38ms（极差 <1ms）**。

**③ 进程独立性（钉死「不是环境差异」）**
`l3_1101v4c` PID=18880 / 创建 09:43:43 vs `l3_1101v4d` PID=2820 / 创建 16:47:11
⇒ **相隔 7.05 小时的两个独立冷启动**。这否掉了「同一进程持续恶化」的可能。

### 二、候选归因（复核 PARTIAL，**5 项修订已吸收**）

| 排序 | 候选 | 关键证据 | 能否离线定谳 |
|---|---|---|---|
| **C1** | 寻路 / 避障重搜（`0x0087E8B8`，Dijkstra 2000 节点，跨单位零缓存） | `docs/re/pathfinding_deep_dive.md:46-51,68-74` | **永远判不了**（未采 `GenerationStamp` `+0x28`） |
| **C2** | 渲染 / 视口裁剪（`DrawIfVisible` v[65]） | 需视口坐标 | **永远判不了**（窗内零截图、未采 `0x887308/0x88730C`） |
| **C3** | 微观索敌（`SelectAutoTarget 0x006FB010` / `Greatest_Threat 0x006F8DF0`，20×20 桶 + 螺旋 Cell） | `docs/re/targeting_spatial.md:29-70` | **永远判不了**（未采索敌计数） |
| C4 | 战斗物理（`BulletClass`/`DamageArea`/`AnimClass`） | 本轮新增补入 | 数量级待 W3 |
| 催化 | 建筑存在性改变战局拓扑 | — | 仅催化，非根因 |
| **判死** | 输入失焦 Sleep / 节流 Sleep / 音频调度 / 宿主降频 | 见下 | **已判死** |

**判死详情**：`max_stall_s ≤ 0.75s` + `logic_frames` 全正 ⇒ 斩死 Sleep 族；
`docs/re/clock_frame_loop.md:477` + `Q02/REPORT.md:92`（帧时超 32ms 时零 Sleep）；
`docs/re/audio_throttle_landing.md:20-25`（300 槽固定池，单次微秒级）；
7 张图跨 21 趟恒定 31.64–32.38ms ⇒ 斩死宿主降频。

### 三、★ 复核推翻 W2 自己初稿的一整层判断（这是本轮最重要的方法学收获）

W2 初稿断言「靶图 `[2]0LoadBench_U0400.yrm` **根本无** `[TeamTypes]` 与 `[AITriggerTypes]`
⇒ AI 决策爆炸**物理上不存在**」。**复核员推翻了这条，我亲自核实：**

```
[AITriggerTypesEnable]  idx=13854   （含 043F40BC-G=yes 等条目）
IgnoreGlobalAITriggers=no          （idx=17463，即**不忽略**全局 AI）
[TeamTypes]  NOT FOUND
```

⇒ **靶图虽无本地 `[TeamTypes]`，但启用了全局 AITrigger（`IgnoreGlobalAITriggers=no`），
遭遇战会加载 `aimd.ini` 的全局 AI 循环。**
「AI 层已排除」是**机制误判**，已按复核意见**降级为「未判候选」**。

**这条给了本轮一条可复用的判据**：
「地图里没有 `[X]` 段」**不等于**「引擎不会运行 X」——必须同时检查
「是否启用全局 `X`」的开关（本例 `IgnoreGlobalAITriggers`）。

### 四、三条「永远判不了」的红线（W2 给出，我认为这是本轮最有价值的诚实部分）

1. **视口渲染**：`harness8_v4.py:3826` 明文「测量窗内零键鼠、零 PrintWindow」⇒
   87 个窗**磁盘上零张截屏**；且从未采视口坐标 `0x887308/0x88730C`。
2. **微观寻路**：从未采 `0x0087E8B8+0x28` GenerationStamp；从未遍历单位 `Locomotor->State`。
3. **微观索敌**：从未采索敌定时器/执行计数，且与 C1 在宏观曲线上**高度共线**（无法离线解耦）。

**根本原因（W2 的信息论表述，我认同）**：500Hz 帧沿只能测出「这一帧多慢」，
**物理上无法拆解** `FrameTime = T_Dijkstra + T_Targeting + T_Physics + T_Render + T_Other`。

### 五、W1 状态（同轮）

`dwfrun-3eee0767`（hy4free）**已完全恢复**：phase-1 四路 4/4 有结论（34.7M tokens），
正进 phase-2 **四路并行复核**，5m 前有进度；§559 记的「51 分钟卡死」已自行解除。

### 六、据此新派 W3（本轮）

`dwfrun-1aeaeb17`（`magpie/antigravity/gemini-3.8-flash$high`，W2 已释放该通道）：
**W3 四大成本中心的静态可定量边界** —— 把 C1/C2/C3/C4 各自压到「数量级上界」，
判定哪几条**可在纯离线条件下静态排除**（例如「理论差 2 个数量级 ⇒ 可排除」），
并榨干 `frame_edges` 这个唯一未用尽的细粒度通道，同时出**最小可行采样清单（设计非实现）**。
任务书记入 §559 的两条自我纠错纪律（「A 调用 B ⇒ 必须进 B 函数体」「引用文件必须读紧邻注释」）。

### 七、诚实账

1. **我亲验**：`[AITriggerTypesEnable]` 存在（idx=13854）、`IgnoreGlobalAITriggers=no`（idx=17463）、
   `[TeamTypes]` 不存在；W2 定稿的复核状态与三条红线原文；W1 已恢复（token 18.0M→34.7M）。
2. **我未验**：W2 的 107 对/82 对/7 张图等等数字（**采信其复核 CONFIRMED 的结论**，
   我只复核了 `b_valid` 与 `g` 两组，其余未逐项重算）。
3. **我未验**：C1/C3/C4 的任何机制判断——W2 将其标为需帧内通道，我无独立证据。
4. **§558 与本节的关系**：§558 记的「`g` 慢组高 31%」被 W2 **CONFIRMED**，
   但 W2 同时指出该量**不能作因果**（慢组 `g` 高但 `t55k` 无建筑满帧是另一回事）。
5. 本轮**零真机**、**零母本改动**、**未 commit**。
6. **本轮新增的一条纪律（第四次派上用场）**：
   「没有 `[X]` 段」≠「引擎不运行 X」，必须查**全局开关**。
   这与 §557/§559 的两条（读紧邻注释 / 进函数体核实）同属「**把间接线索当直接证据**」，
   现已凑成三条，下一轮起在任务书里统一前置。
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION))
