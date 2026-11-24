# W177-C · REJECT_MACHINE.md —— 「引擎拒绝放置」状态机

> 目标 B 主产出。全部状态来自 `ReadProcessMemory` 只读采样 + 合成鼠标点击后的可见后果；
> 拒绝的多重信号：红圈截图 + 目标格链无对象 + 对象维持 limbo + 额度无位移。
> 证据：`EVIDENCE/B01_conyard.json`、`B02_reject_conyard.json`、`B03_reject_unit.json`、`B04_rightcancel.json` 及对应 `*_hover.png`/`*_after.png`。

## 0. 参与状态量（可观测）

| 状态量 | 地址/字段 | 拒绝事件中的取值 |
|---|---|---|
| 信用额度 | PlayerHouse+0x30C | 9400 → 9400（Δ=0，无 −600、无退款） |
| ghost 对象存在 | BuildingClass::Array 中 NAPOWR | 0x158773f0 全程存在 |
| 放置/limbo 位 | obj+0x81 (o1) | 1（拒绝前）

I'll continue writing the rest of the file.<tool_call:6124c78e>write<arg_key:6124c78e>content</arg_key:6124c78e><arg_value:6124c78e># W177-C · REJECT_MACHINE.md —— 「引擎拒绝放置」状态机

> 目标 B 主产出。所有状态来自 `ReadProcessMemory` 只读采样 + 合成鼠标点击后的可观测后果；
> 「拒绝」用多重信号判定：红圈截图 + 目标格链无该对象 + 对象维持 limbo + 额度无 −600 位移。
> 证据：`EVIDENCE/B01_conyard.json`、`B02_reject_conyard.json`、`B03_reject_unit.json`、`B04_rightcancel.json` 及各自 `*_hover.png` / `*_after.png`（未截断）。

## 0. 参与状态量（可观测）

| 状态量 | 地址/字段 | 拒绝事件中的取值 |
|---|---|---|
| 信用额度 | PlayerHouse+0x30C | 9400 → 9400（Δ=0，无 −600、无退款） |
| ghost/limbo 对象 | BuildingClass::Array 中 NAPOWR | 0x158773f0 全程存在 |
| limbo 位 | obj+0x81 (o1) | 1（拒绝前后恒为 1） |
| 入格锁存 | obj+0x74 (o2) | 0（拒绝前后恒为 0） |
| can-place 候选 | obj+0x1AC | u8=0 / u32=0（拒绝前后恒为 0，未随点击变化） |
| 目标格链 | cell+0xE4(headA)/+0xE8(headB) | headA=0x15693c48(玩家conyard)、lenA=1、lenB=0；前后完全一致 |
| 目标格坐标 | §951 `CellClass*=[0x87F924]+((Y<<9)+X)*4` | (64,19)/(65,19)，cell 指针前后一致 |
| 红圈像素 | 截图 ±70px 邻域 R>150,G<90,B<90 | B02=7409、B03=12173、B04=7409 |
| 相机原点 | 0x886FA0/0x886FA4 | (0,0)（读数无变化，见 UNKNOWNS U1） |

## 1. 状态节点

- **S0 空闲**：无 limbo NAPOWR，额度=当前值（10000 或 9400），侧栏无「就緒」。
- **S1 已下单/建造中**：第 1 次点图标 → 额度 −600，创建 NAPOWR 对象 `o1=1,o2=0,cell=(0,0)`（limbo），处于建造计时。对应 B01（10000→9400，对象 0x158773f0 生成）。
- **S2 就緒 + ghost 已拿起**：侧栏显示「就緒」，第 2 次点图标 → ghost 跟随光标；此时 hover 合法空格出现**绿框**（rad120 red<150,green>9000），hover 占用格出现**红圈**（B02/B03/B04 的 hover 截图）。
- **S3 合法落格**：在纯绿 footprint 上点击 → 对象 `o1:1→0, o2:0→1, cell:(0,0)→(X,Y)`，地址写入目标格 `cell+0xE4/+0xE8` 链（in_cell_chain=True），额度不再变（−600 已在 S1 扣除）。见 LIVE.md 目标 A 的 A01–A10。
- **S4 拒绝 + 回滚到 S2**：在红圈格上点击（左键或右键）→ 出现红圈信号但对象**维持 S2 的 limbo 态**（o1=1,o2=0,cell=0,0），目标格链前后不变，额度 Δ=0。B02/B03/B04 停在此态。

## 2. 拒绝路径状态转移（本卡实测）

```
S2 (就緒,ghost拿起,o1=1,o2=0,cell=0,0,额度=9400)
   │ hover 目标格 (占用/单位/不可放置)
   ▼
S2-hover：红圈出现（red=7409~12173），can-place+0x1AC 仍为 0
   │ 左键点击(B02 conyard / B03 unit) 或 右键点击(B04)
   ▼
S4 拒绝：o1=1,o2=0,cell=(0,0) 不变；cell 链 headA/lenA 前后一致（无该对象）；额度 9400→9400
   │ （ghost 仍激活，可继续尝试或改点纯绿格）
   ├─► 改点纯绿格 → S3 成功落格（见目标A）
   └─► 本环境未观察到 9400→10000 退款分支：退款数=0/3
```

## 3. 从「点击」到「拒绝+回滚」的可观测状态序列（逐字段）

以 B02（点 conyard 格 (64,19)）为例，`B02_reject_conyard.json` 逐字段：

1. **before**：frame/mode/credit=9400；NAP o1=1,o2=0,cell=(0,0),valid=False，+0x1AC u8/u32=0；target cell(64,19) headA=0x15693c48,lenA=1,lenB=0,nodesA=[0x15693c48]。
2. **hover**：截图 `B02_reject_conyard_hover.png` 红像素 7409；内存态同 before（红圈是绘制层信号，未改对象/额度/格链）。
3. **click**：左键 down/up 作用于 gamemd 前台目标点 (1620,560)。
4. **after**：credit=9400（Δ0）；NAP o1=1,o2=0,cell=(0,0) 不变；target cell(64,19) headA/lenA/lenB/nodesA **逐字节一致**；无新 NAPOWR 入格。截图 `B02_reject_conyard_after.png`。

B03（单位占用格 (65,19)）与 B04（右键）序列相同，仅红圈计数与目标格不同；三者构成「拒绝态 = 可见红圈 + 状态零位移」的一致性证据。

## 4. 关于 0x47C620 逐格校验的可观测后果

本卡未对 `0x47C620` 做断点/EIP 采样（纪律 10：EIP 权重 ≠ 调用频率，且只读约束不便于逐指令跟踪）。但可从状态后果反推其**可观测效应**：
- 拒绝时：目标格链无写入（lenA/headA 不变）、对象不入格（o2 保持 0）、额度不二次扣减也不退款 ⇒ 校验失败的净效果是**无副作用回滚**。
- 成功时（目标A）：目标格链 headA 变为该对象、lenA=1、o2=1 ⇒ 校验通过才发生格链写入。
- 因此 `0x47C620` 的判定边界在「是否允许 o1→0/o2→1 + 格链写入」，红圈是其**可见前置信号**。这是 observable consequence，不是对函数内部的断言。

## 5. 与 W177-B 的差异（诚实记录）

- W177-B 报告「点击无效格 → 取消并退款 9400→10000」。本卡 3 次拒绝**均未见退款**（额度恒 9400）。差异原因未定（可能与本机 AI 设置/游戏阶段/点击目标类型有关）；按纪律如实报退款 0，不套用上卡结论。
- 本卡额外发现「两步建造/第2次点图标拿起 ghost」是 W177-B 未记录的关键前置步骤，解释了其上卡「ghost 落不到格」的根因。

## 6. 分级

| 结论 | 分级 | 证据 |
|---|---|---|
| 红圈是拒绝的可见信号（3 例 red>7000） | [已证] | B02/B03/B04 hover.png + json |
| 拒绝时 o1=1/o2=0/cell=0,0 不变 | [已证] | B02/B03/B04 before/after |
| 拒绝时目标格链无写入、无退款 | [已证] | B02/B03/B04 target before/after 相同、credit Δ0 |
| 0x47C620 校验失败的净效果=无副作用回滚 | [推断·可观测后果] | 本文件 §4（未取 EIP，仅状态后果） |
| 退款分支存在 | [未证] | 本卡 0/3；W177-B 曾报但本卡未复现 |
