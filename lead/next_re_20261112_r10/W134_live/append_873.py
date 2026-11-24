#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §873: case 1 of 0x006DD8B0 is the win/lose check, NOT the per-frame sim."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
s = io.open(LED, encoding="utf-8", newline="").read()

SEC = """
## §873 · **【更正 §853】`0x006DD8B0` 的 `case 1` **不是**每帧模拟，而是胜负判定 —— ① 卡顿这条线找错了入口**（2026-11-15 16:45）

> 来源：`ds-t6b-frame` 的重跑结论 + **我的逐字节复验（反汇编 + 字符串双重确认）**。
> 性质：**推翻 §853 里我自己写的一条 [已证]**，且它正是 ① 卡顿调查的锚点。

- **§873-1 [已证·`case 1` 的完整代码（我亲自反汇编）]**
  `state == 1` 跳转到 `0x006DEA37`，全部内容 14 条指令：
  ```asm
  006DEA37  8b0d4c3da800      mov  ecx, [0x00A83D4C]
  006DEA3D  8b8690000000      mov  eax, [esi + 0x90]
  006DEA43  55                push ebp
  006DEA44  8b5134            mov  edx, [ecx + 0x34]
  006DEA47  3b82b8000000      cmp  eax, [edx + 0xB8]
  006DEA4D  0f8548f3ffff      jne  0x006DDD9B          ; 不等 ⇒ 跳进大块
  006DEA53  e888dfe1ff        call 0x004FC9E0          ; House.CPP
  006DEA58  b001              mov  al, 1
  006DEA5A  5f                pop  edi
  006DEA5B  5e                pop  esi
  006DEA5C  5d                pop  ebp
  006DEA5D  5b                pop  ebx
  006DEA5E  81c440020000      add  esp, 0x240
  006DEA64  c21000            ret  0x10
  ```
  - `case 2`（`0x006DEA67`）是同一段代码，只把 `jne` 换成 `je 0x006DDD9B`。
  - ⇒ **`case 1` 只做一次比较 + 一次调用 + 返回**，没有任何对象遍历。

- **§873-2 [已证·那两个被调函数是胜负处理（字符串实证）]**
  我扫出两个函数的全部字符串引用：
  | 函数 | 字符串 |
  |---|---|
  | `0x004FC9E0` | `D:\\ra2mdpost\\House.CPP`、**`TXT_SCENARIO_WON`**、`TXT_VICTORIOUS`、`EVA_MissionAccomplished`、`EVA_YouAreVictorious` |
  | `0x004FCBD0` | `D:\\ra2mdpost\\House.CPP`、**`TXT_SCENARIO_LOST`**、`TXT_LOST`、`EVA_MissionFailed`、`EVA_YouHaveLost` |
  - ⇒ 一个**胜**、一个**败**。`case 1`/`case 2` 是**胜负判定**（可能在判"本条触发条件的对象是否已达胜/败条件"）。
  - ⇒ **§853 里"`case 1` = 进入游戏内逻辑"这句作废。**

- **§873-3 [已证·顺带更正 §869 的一处标签错误]**
  我在 §869 把 `0x006DDD9B` 标成"`BuildingClass` 主循环"。**这个标签不准确**：
  它是**被 `case 1` 的 `jne` 与 `case 2` 的 `je` 共同跳入的一块共享代码区**（首尾 `0x006DDD9B..0x006DEA4D`，1020 条指令），
  其中**内含** Building 的若干循环，但它本身是"状态分支的共享尾块"，不是"一个 Building 循环"。
  - ⇒ §869 的"Building ×7"应理解为"**在该共享区内及附近出现 7 处 Building 相关循环/区间**"，
    而不是"7 个顶层循环"。
  - ⇒ §869 的循环**总数 20/21** 这个计数本身不受影响（那是回边的客观结果），但**层级归属需要重做**。

- **§873-4 [已证·每帧模拟在别的 `state` 值里，且有一个真实的重入点]**
  子代理的重跑结论（我未逐条复核，但方向与 §873-1 自洽）：
  | 项 | 内容 |
  |---|---|
  | 循环头 | **19 个**，分布在 **13 个 case 块** |
  | 其中遍历数组的 | **16 个** |
  | 遍历的数组 | `Infantry`(1)、`Foot`(2)、`Techno`(1)、`Building`(7)、`Trigger`(3)、`ParticleSystem`(1)、`House`(1) |
  | **从不访问** | **`UnitClass`、`AircraftClass`** |
  | 唯一重入 | `0x006DF0FF`（`TriggerClass` 循环）→ `0x007265C0` → 对每个 `[+0x28]` 链表节点**再次调用整个分派器 `0x006DD8B0`** |
  - ⇒ 与 §869 的分歧：我数 `Trigger` 2 个、无 `House` 循环、共 20 个不同 (head,back)；
    子代理数 `Trigger` 3 个、有 `House` 1 个、共 19 个循环头。**两边口径不同（回边数 vs 循环头数），未对齐。**
  - ⇒ **`UnitClass` / `AircraftClass` 从不被直接遍历**这一点，两方一致 —— 因为载具是 `FootClass`，
    已被 Foot 循环覆盖；这条结论**可靠**。
  - ⇒ **重入点是本轮对 ① 最有价值的结构发现**：分派器在 Trigger 循环内被逐节点重入，
    静态深度 2。是否存在 ≥3 层，**只能真机测**。

- **§873-5 [已证·为什么这解释了此前多次测量不一致]**
  子代理指出：循环体内有**数据依赖分支** —— 在调用 `[obj+0x514]` 之前会检查
  `[obj+0x90]`、`[obj+0x74]`、`[obj+0x81]`、`[obj+0x34]`。
  - ⇒ **看似最重的调用，对多数对象可能从不执行。**
  - ⇒ 这与台账 §707/§723/§725 一连串"用代理指标测 N 却测错"的失败**同一机制**：
    静态可见的调用次数 ≠ 实际执行次数。**这条值得写进 ① 的方法纪律。**

- **§873-6 [未证·如实登记]**
  1. 19 vs 20（循环头 vs 回边）的**口径未统一**，我不确定哪个更该用于成本统计。
  2. `case` 编号到 `state` 值的映射我只验了 **case 1 和 case 2**，其余 11 个 case 块未逐条核。
  3. "每帧模拟在别的 state 值里"这句我是**转述子代理**，未自己逐 case 确认。
  4. 重入深度 ≥3 是否存在：**未证，需真机**。
  5. 子代理承认它的 `cost_centres.tsv` 在构造上会**多计数**（虚拟调用无法解析到单一地址，
     11/12 个虚拟点各有 4 个候选）。**因此本轮不提供任何成本排名。**

- **§873-7 [已证·对 ① 卡顿这条线的净影响]**
  | 项 | 改前 | 改后 |
  |---|---|---|
  | `case 1` 定性 | 进入游戏内逻辑 | **胜负判定** |
  | 每帧模拟位置 | 以为在 `case 1` | **在其它 `state` 值里，且被 Trigger 循环逐节点重入** |
  | 可用的成本排名 | — | **没有**（虚拟调用无法解析 + 数据依赖分支） |
  - ⇒ **结论：① 的"逐帧开销"至今没有任何可信的静态入口定位。**
    此前基于"`case 1` = 主循环"的所有推断都应视为**基于错误锚点**。
"""

if "## §873 ·" in s:
    raise SystemExit("REFUSE: §873 already present")

# forward pointer at §853's case-1 claim
OLD = "  | **`0x006DD8B0`** | 9,530 | 140 | `Sleep(1000)`、`TAction.CPP`、`switch(*(obj+0x2C))` 分派 | **游戏状态机分派器**（`case 1` = 进入游戏内逻辑） |"
NEW = ("  | **`0x006DD8B0`** | 9,530 | 140 | `Sleep(1000)`、`TAction.CPP`、`switch(*(obj+0x2C))` 分派 | "
       "**游戏状态机分派器**（~~`case 1` = 进入游戏内逻辑~~ → **§873 已证否：`case 1` 是胜负判定**） |")
if s.count(OLD) == 1:
    s = s.replace(OLD, NEW)
    print("forward pointer added at §853")
else:
    print("WARN: §853 row anchor found %d times, skipped" % s.count(OLD))

s = s.rstrip("\n") + "\n" + SEC
io.open(LED, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("appended §873; size=%d; control chars=%d" % (len(s.encode("utf-8")), len(bad)))
