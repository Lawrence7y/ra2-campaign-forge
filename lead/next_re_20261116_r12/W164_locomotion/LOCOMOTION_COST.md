# W164 · 移动/寻路路径的每帧代价结构

> 卡 W164 · R12 · 2026-11-16 · 静态逆向（零真机 / 零母本改动 / 未 commit）
> 目标主程序 `ra2youli\gamemd.exe` SHA-256 `73201CC0...476` ImageBase `0x400000`（已复核）。
> 方法：byte-level capstone（`skipdata=True`，全 `.text` 解出 1,394,186 条，与 §6.2 真值 1,394,120 同量级）+ Ghidra `-noanalysis` 反编译 + 主台账/既有 atlas 交叉。
> 穷举性结论均给双通道，且至少一条不依赖 `function_atlas.tsv` 的 `entry+size`（全节逐字节扫描 / 从节首线性反汇编）。

## 5 行摘要

1. **[已证]** 每 tick 的 AI 派发确实遍历全部对象且**无门控**（`0x55B610` 循环 call `[vptr+0x5C]`，无 mode 门、无 `+0x98` 门），因此 FootClass::AI 每 tick 对每个活单位都进一次；"移动更新"的调用点在每 tick 都到达。
2. **[已证]** 真正决定成本的**寻路门控在 Locomotion::Process 内部**：Drive 的 Process wrapper `0x4B0500` 在 `0x4B0564/0x4B056D` 判 `[loco+0x54]==-1 || byte[loco+0x5F]==0` 即跳 `0x4B066C`（跳过整条寻路链）。即"无目标/未在移动 ⇒ 不做寻路"在代码层成立。
3. **[已证]** 每帧移动槽是 `Locomotion` **offset=4 子表的槽 16（`+0x40`）**（Drive→`0x4B0500`、Walk→`0x75AC80`、Hover→`0x514310`、Ship→`0x69FC10`…），**不是 `+0x5C`**；`+0x5C` 是 `0x55A910` 状态位设置器（stdcall `ret 4`，与 thiscall 派发点调用约定不符）。这是与派发提示词预设的一处 **DISAGREE**。
4. **[已证]** 寻路链 `0x4D3920`(UpdatePathfinding,669 指令/68 call)→`0x4CBBA0`→`0x42C900`→`0x429D6D`(SearchCore,544 指令单循环，默认轮数上限 `0xFFF7`=65527)，且 FootClass::AI 入口有 `frame % [0x8871E0+0x1808]` 节流；节流除数与运行期值 `[未证]`。
5. **[静态推断]** 判决：**「成本 ∝ 正在移动的对象数」在代码结构层成立（门控已钉死），但在数量级层静态不可判**——因为两趟图的运行期对象数从未采样（§14.3），且静态单对象上界（1 次满 SearchCore = 11.9–71 ms）**同时包容 67 µs 与 1.47 ms 两种每对象成本**，不能靠上界排除其一。下一步最有区分力的证据见 Q5。

---

## Q1 · 每 tick 的移动更新在哪里

### Q1.1 派发链逐跳（AI 槽 0x5C）

| 跳 | 地址/机制 | 做什么 | 证据等级 |
|---|---|---|---|
| 0 | `0x6BB9A0 → 0x48CCC0 → 0x55D360 →(0x55DC9E)→ 0x55AFB0` | 每帧链（题设/R12_FACTS §10.1） | [已证·台账] |
| 1 | `0x55AFB0` 内 `0x55B608` 循环 | `mov edi,[esp+0x10]`(=this)→`mov eax,[edi+0x10]`(Count)→ 循环 `mov ecx,[Items+esi*4]; mov edx,[ecx]; call [edx+0x5C]`；**每次重读 Count，无 mode 门，无 +0x98 门** | [已证·台账 §10.2] |
| 2 | 槽 `0x5C` = ObjectClass::AI | 主表字节直读：Object `0x5F3E70` / Foot `0x4DA530` / Techno `0x6F9E50` / **Unit `0x7360C0`** / **Infantry `0x51BAB0`** / **Aircraft `0x414BB0`** / Building `0x43FB20` / Bullet `0x4666E0` | [已证] `resolve_ai_slots.py` |
| 3a | UnitClass::AI `0x736204`：`8b8e78020000 / 85c9 / 7405 / 8b01 / ff505c` | `mov ecx,[esi+0x278]; test; jz; mov eax,[ecx]; call [eax+0x5C]` — **门控只有 NULL 检查**（thiscall 无栈参） | [已证] `W164_LocoCall.log` + capstone |
| 3b | InfantryClass::AI `0x51BB6E`：`8b4e78? → ff5105c` 同型（`call [EAX+0x5C]` @`0x51BB7A`） | 同上 | [已证] `W164_AI.log` |
| 3c | FootClass::AI `0x4DA530` 被 3 个子类 AI 直调（`0x73647B`/`0x51BC9F`/`0x414DA3`） | 子类 AI 显式 call 基类 AI | [已证] `W164_Path.log` |
| 4 | FootClass::AI 尾部 `0x4DAEE1..0x4DAEF3` | `mov esi,[esi+0x694]; test; jz; mov ecx,[esi+0x69c]; mov edx,[ecx]; call [edx+0x5C]` — 同样是 NULL 门 thiscall | [已证] capstone 原始字节 `8b b6 94 06 00 00 / 39 3b / f3 74 0b / 8b 8e 9c 06 00 00 / 8b 11 / ff 52 5c` |

**AI 层的门控结论**：派发循环对全部对象无门（跳 1）；子类 AI 里两处 `call [vptr+0x5C]` 只有 NULL 指针检查；FootClass::AI 入口有一个总门 `0x4DA53E mov al,[ESI+0x90]; cmp al,0; jz 0x4DAF00`（对象 `+0x90` 字节为 0 则整段跳过）——**这不是"是否在移动"门，是对象活跃性门**。⇒ [已证] 每个 tick 每个活跃 FootClass 都会进到移动处理路径入口；"是否每 tick 都做寻路"由下一节的内部门决定。

### Q1.2 Locomotion 子类虚表：`+0x5C` 不是每帧更新槽

`vtables_canonical.json` 主表判定用 `COL.offset==0`；我用 COL 指针（`vftable[-4] == col`）二次确认了所有 Locomotion 表的边界（byte-level 通道，不依赖 atlas size）：主表 10 槽（Teleport 12）、offset=4 子表 **50** 槽、offset=24 子表 8 槽。
⚠️ 台账 §3.1 记 "offset=4 子表 49 槽"，我实测 **50**（COL 指针前的最后一项仍是合法 .text 函数指针）。记入 DISAGREE。

| 子类 | off4 vt | 槽16 `+0x40`（≈每帧 Process wrapper） | 槽23 `+0x5C`（状态设置器） |
|---|---|---|---|
| Drive | `0x7E7EB0` | `0x4B0500` → 大 Process `0x4B2630` | `0x55A910` |
| Walk | `0x7F69F8` | `0x75AC80` → 大 Process `0x75AEC0` | `0x55A910` |
| Hover | `0x7EACFC` | `0x514310` → 大 Process `0x5164D0` | `0x516BF0` |
| Fly | `0x7E89F4` | `0x4CCB40` | `0x4CFD20` |
| Ship | `0x7F2D8C` | `0x69FC10` → 大 Process `0x6A1C80` | `0x55A910` |
| Mech | `0x7EDB6C` | `0x5B0060` → 大 Process `0x5B01C0` | `0x55A910` |
| Jumpjet | `0x7ECD68` | `0x54AEC0` | `0x55A910` |
| Teleport | `0x7F5000` | `0x7192F0` | `0x55A910` |
| Rocket | `0x7F0B1C` | `0x6622C0` | `0x55A910` |
| Tunnel | `0x7F5A24` | `0x728E30` | `0x55A910` |
| DropPod | `0x7E8278` | `0x4B5B70` | `0x55A910` |
| LocomotionClass(基) | `0x7EADF4` | `0x55AC60` | `0x55A910` |

`check_off4_process.py` 逐槽检查直接 callee：Drive/Walk/Hover/Ship/Mech 的槽16 wrapper 直接调用各自"大 Process"（调用 `0x4D3920` UpdatePathfinding 的函数）；其余类的大 Process 未含 `0x4D3920` 直调（`[未证]` 是否深度调用）。

`+0x5C` 槽的 `0x55A910` 反汇编（`55 a9 10`）:
```
mov eax,[esp+4]; push eax; mov byte [eax+0xc],0; mov ecx,[eax]; call [ecx+0x60]; ret 4
```
= 清 `obj+0xC` 字节再调 `[vtable+0x60]`，是**状态位设置器**（`ret 4` = 1 栈参 stdcall），**不是**每帧驱动，也与 AI 派发点的 thiscall 调用约定不符。Fly 的 `0x4CFD20` / Hover 的 `0x516BF0` 同族（都读 `[esp+8]` 的栈参）。⇒ "把 Locomotion 的 `+0x5C` 当每帧更新槽"是错的（DISAGREE）。

### Q1.3 关键：每 tick 都调，还是只在"正在移动"时调？—— 门控钉死

真正的大 Process（如 Drive `0x4B2630`，2600 指令 / 181 call）由 wrapper `0x4B0500`（1486 B）进入。wrapper 入口原始字节（byte-level 已证）：
```
004B055A  8b4654          mov eax,[esi+0x54]        ; esi=Locomotion 对象
004B055D  83cdff          or  ebp,-1                ; ebp=-1
004B0562  3bc5            cmp eax,ebp
004B0564  0f8402010000    je  0x4B066C              ; 门A: [loco+0x54]==-1 → 跳过
004B056A  385e5f          cmp byte [esi+0x5f],bl     ; bl=0
004B056D  0f84f9000000    je  0x4B066C              ; 门B: byte[loco+0x5F]==0 → 跳过
```

⇒ **门控字段与取值（Q1 的核心答案）**：
- **字段 `+0x54`（dword）**：值 `-1` = 无目标/无路径索引 ⇒ 跳过昂贵寻路；
- **字段 `+0x5F`（byte）**：值 `0` = 未处于移动态 ⇒ 跳过。
- 二者任一命中即跳 `0x4B066C`（`[静态推断]`：该分支是 short-circuit，未逐字节追踪到 `0x4B066C` 之后是否立即 ret，但 wrapper 的多个 early-return 分支（如 `0x4B058C je 0x4B0AC2`）显示跳过路径后走的是轻量出口）。

**回答派发提示词的关键问**：FootClass::AI / Locomotion::Process **每 tick 都被调用**（调用点无"移动"门），但**昂贵寻路只在 `+0x54 != -1 && +0x5F != 0` 时执行**。所以"成本 ∝ 正在移动的对象数"在代码结构层**成立**：静止对象每 tick 只付一次便宜的 wrapper+门检查，移动对象才付完整寻路。这是 [已证] 的门控结构。

---

## Q2 · 寻路是每 tick 重算还是缓存

### 寻路入口与逐跳（主台账 §562/§563 + 本卡复核）

| 环节 | 地址 | 规模/证据 |
|---|---|---|
| Locomotion 大 Process | `0x4B2630`(Drive)/`0x75AEC0`(Walk)/`0x6A1C80`(Ship)/`0x5B01C0`(Mech)/`0x5164D0`(Hover) | 2600/1505/2590/1664/569 指令（capstone skipdata）[已证] |
| `FootClass::UpdatePathfinding` | `0x4D3920` | 2259 B / 669 指令 / 68 call；被上述 5 个大 Process 直调（Ghidra call xref，双通道）[已证] |
| `FootClass::CallFindPath` | `0x4CBBA0` | 158 B / 58 指令 / 3 call；`0x4D3E4B` 唯一调用者 [已证] |
| `PathFinder::FindPath` | `0x42C900` | 1563 指令 / 67 call（capstone）；`0x4CBC31` 调用者 [已证] |
| `SearchCore` 主循环 | `0x429D6D..0x42A3D8` | 1649 B / **544 指令**，整函数就是 1 个大循环（回边 `0x42A3D8→0x429D6D`），内含 5 个嵌套循环头（`0x429DC2/0x42A07A/0x42A0E2/0x42A242/0x42A345`）[已证] |

**预算**：默认轮数上限 `0xFFF7`=65527（主台账 §562 逐字节已证 `0x429D59 c7442470f7ff0000`；§563 更正为"轮数上限"而非"剩余节点预算"）。本卡 byte 复核 `0x4D3920` 内引用 PathFinder 单例 `0x87E8B8`（`0x4D3C97` 等 8 处）。`0xFFF7` 的消费点本卡未再下钻（承接台账 §562-4 "未验实际消费"）。

### 调用条件：非每 tick 重算，由两层门控

1. **外层（每 tick 都判）**：Process wrapper 的 `[loco+0x54]`/`[loco+0x5F]` 门（Q1.3）—— 静止对象根本不进 `0x4D3920`。
2. **内层（进入 UpdatePathfinding 后）**：`0x4D3920` 开头就有 `cVar3 = call [vptr+0x2CC]; if (cVar3==0){ [this+0x178]=-1; return 0; }` —— 位置无效直接返回；随后大量坐标比较（`[this+0x1A4]` 等）与目标变化检查（`0x8B3D88/0x8B3D8A` = 当前 cell X/Y）。
   ⇒ [静态推断] 是**缓存式**：目标 cell 未变（`sStack_1c==DAT_8B3D88 && sStack_1a==DAT_8B3D8A`）时不重算，只对"目标变/路径失效"重算。与台账 §5844 "跨单位零缓存" 不矛盾（那说的是不同单位之间不共享）。

### 节流机制

FootClass::AI 入口 `0x4DA554..0x4DA568`：
```
mov eax,[0xA8ED84]        ; 逻辑帧计数
mov ecx,[0x8871E0]        ; 单例指针
cdq; idiv dword [ecx+0x1808]
test edx,edx; jnz 0x4DA63B   ; 余数非0 → 跳过该刷新块
```
⇒ 存在 `frame % N` 节流，**N = `[0x8871E0 + 0x1808]`**（运行期单例字段，静态值 0，因为 `0x8871E0` 是运行时指针；`[0x8871E0]` 静态读回 0）。**N 的数值 `[未证]`**（需真机或追 `0x8871E0` 的初始化点）。注意这个节流只拦 `0x4DA572` 之后的"位置/朝向刷新"块，**不拦** Q1.3 的寻路门（寻路在子类 AI 更深处）。

---

## Q3 · 格/占位表更新

### 相关全局（byte-level 双通道）

| 全局 | 身份 | 引用数/证据 |
|---|---|---|
| `0x87F7E8` | MapClass 单例（构造器 `0x40D1B2` 写 vptr `0x7E1964`）| 全 `.text` 数十处 `mov ecx,0x87f7e8` [已证] |
| `0x87F924` | `0x87F7E8 + 0x13C` = MapClass `+0x13C` 格表槽 | 全字节扫描 30+ 处 `mov reg,[0x87f924]`（含 `0x429AA1/0x429DF5` 在 SearchCore 相邻区，`0x568xxx` 挂/摘链族，`0x55DDD1` 每帧链）[已证] |
| `0x87E8B8` | PathFinder 单例 | `0x4CBC2C`、`0x4D3C97` 等 30 处 [已证] |

### 每帧路径上的格表写

- **挂链/摘链**：`0x5683C0`（挂）/ `0x5687F0`（摘）（台账 §3.6）；`0x87F924` 在 `0x568Dxx/0x569xxx` 密集引用 —— 单位移动时从旧格摘链、向新格挂链。
- **`+0xE4/+0xE8` 非栈写**：全 `.text` 字节扫描 `[reg+0xE4]` 读改写 **99 处**（含 `[esp+0xE4]` 栈写，需按题设口径剔除后 ≈ 93 处/38 函数——本卡只做了总数 99，未逐函数去栈归类，`[部分已证]`）。这些是 CellClass/ObjectClass 的格坐标/占用位字段（题设口径）。
- **单位不进格链**：台账 §707-2 实测格链节点 213 vs 设计 1500；§853 更正"单位在全局数组不在格链"。⇒ **单位本身不挂在格链上**，挂链的是格对象/覆盖物。

### 复杂度判定

- 挂链/摘链操作对单个格子是 **O(1)**（改固定数量指针 + 读 `0x87F924` 取格表基址）。
- 一次移动跨越的格数 = 速度 × dt / 格尺寸，通常 0 或 1 格 ⇒ **每次移动更新 O(1)**（若单 tick 跨 k 格则 O(k)，k 小）。
- **O(半径²)** 只出现在"重算 footprint 占用"（多格建筑，2-b 病态的结构，非本卡移动对象）。
- ⇒ [静态推断] **普通单位移动每 tick 的格表更新是 O(1)**，不是热点；真正的成本在 `SearchCore` 的 544 指令循环 × 最多 65527 轮。

---

## Q4 · 数量级核算（本卡最重要）

### (a) 1500 个单位是否都进 AbstractClass::Array？有无上限？

- **Rules 有 `MaxUnitCount`，但语义是"开局单位数上限"**：`RULESMD_expandmd01.INI:2997` 注释 `MaxUnitCount = maximum number of starting units. (def=20)`，`:3024 MaxUnitCount=10`。**这不是运行期数组上限**，只是场景放置规则；地图 `[Units]` 段可放 1500 MTNK 绕过它。
- **引擎无运行期单位硬上限**：台账 §189 "引擎无上限实锤"（T55 冻结根因是 AI 对手屋装载期全灭→终局路径死锁，非容量非畸形）。
- **真机实测装载量**：`units0=961`（§134，frame 437 冻结）、`units0=1212`（§140，spawnfix10），均 < 1500。⇒ 1500 MTNK **在真机上未全部存活到局内**（但这是不同实验的容器/AI 配置，不能直接套到 range1/c2_near 两趟）。
- **静态上限**：`AbstractClass::Array` 是 `DynamicVectorClass`（+4 Items/+8 Cap/+0x10 Count/+0x14 Increment），容量可增长，静态**给不出对象数上限** [已证·负结果]。
- **§887 的 69 对象**是另一张小图（12 单位 LoadBench），不是这两趟 1500-MTNK 图。⇒ 这两趟的运行期对象数**从未被采样**（正是 §14.3 指出的缺口）。

### (b) 单对象每帧移动代价静态上界 → 判数量级

**测出的静态结构**（Q1/Q2）：
- 每对象每 tick 必付：`UnitClass::AI` 651 指令 + `FootClass::AI` 722 指令 + Process wrapper ~430 指令（0x4B0500 前 0x90 字节 ≈ 90 指令，全函数 1486B）+ 门检查 ≈ **~1900 指令固定开销**。
- 移动对象额外付：大 Process（Drive 2600 指令）+ `UpdatePathfinding`(669) + `CallFindPath`(58) + `FindPath`(1563) + **`SearchCore` 544 指令 × R 轮**。
- **单对象每帧移动代价静态上界 = 1 次满 SearchCore = 544 × 65527 ≈ 3.56×10⁷ 指令**（R 上限 `0xFFF7`）。

**三档主频上界**（每指令周期数 CPI 明写；x86 取 CPI≈1 乐观 / CPI≈2 保守，两者都给）：

| 主频 | CPI=1（乐观）单次满寻路上界 | CPI=2（保守）单次满寻路上界 |
|---|---|---|
| **1.0 GHz** | 35.6 ms | 71.3 ms |
| **2.0 GHz** | 17.8 ms | 35.6 ms |
| **3.0 GHz** | 11.9 ms | 23.7 ms |

（复跑：`count_instr.py` 得 SearchCore=544 指令；`0xFFF7` 见台账 §562；上界 = 544×65527/f。）

**判别**：
- 若 N≈1500：101.27 ms / 1500 = **67 µs/对象/帧**。这比"固定开销 1900 指令"（1 GHz/CPI2 约 3.8 µs）大 ~18×，落在"每对象付一次**部分** SearchCore"区间：67 µs 在 1 GHz/CPI2 下 ≈ 67 µs/(544×2/1e9) ≈ **62 轮** SearchCore —— 完全可能（短路径/早停）。
- 若 N≈69：101.27 ms / 69 = **1.47 ms/对象/帧**。1.47 ms 在 1 GHz/CPI2 下 ≈ **1350 轮** SearchCore —— 也可能（长路径/拥挤重搜）。

⇒ **静态上界（11.9–71 ms/对象）同时包容 67 µs 与 1.47 ms，不能用"上界"排除任何一个数量级。** 这正是静态分析的边界：**数量级静态不可判**。要判必须知道这两趟的 N（§14.3 的 harness 加 `AbstractClass::Array.Count` 字段）与移动中对象数。

**但可以给一个方向性约束** [静态推断]：§887 真机 0 弹基线 32 ms/帧时只有 61–70 个对象 / 12 单位；若这两趟真有 ~1500 个**活跃**对象，则光固定开销 1500×3.8 µs ≈ 5.7 ms（1 GHz/CPI2），加上部分寻路可达 100 ms；若只有 69 个对象，则每对象须付 1.47 ms ≈ 1350 轮 SearchCore，意味着**几乎每个对象每帧都在做长距离重搜**——这与"移动到后来会停下、成本单调下降"的观察一致（早期都在走⇒都重搜⇒慢；后期停下⇒门A/B 关闭⇒只剩 3.8 µs/对象⇒快）。**两种解释都自洽，静态不可分离。**

---

## Q5 · 判决

**「成本 ∝ 正在移动的对象数」：**

- **代码结构层：成立 [已证]。** 门控（`[loco+0x54]!=-1 && [loco+0x5F]!=0`）明确把昂贵寻路限制在"有目标且在移动"的对象上；静止对象每 tick 只付 ~1.9K 指令的固定开销。这能同时解释"开局最重（都在走）、单调下降（陆续到达/卡住/被毁⇒门关闭）"和"与子弹数无关"（子弹不过 +0x5C 门进寻路）。
- **数量级层：静态不可判 [未证]。** 静态上界（11.9–71 ms/对象）同时覆盖 67 µs（N=1500）与 1.47 ms（N=69）两种每对象成本；两趟图的运行期对象数与移动中对象数从未采样（§14.3）。
- **综合判决：结构支持、定量待真机 —— "静态不可判（偏向成立）"。** 这是负结果交付：已排除"固定开销主导"（只为 5.7 ms 量级，不足 101 ms），已钉死门控字段；剩下只差 N。

### 下一条最有区分力的证据（1–3 条）

1. **【最高区分力】harness 每帧采 `[0x00B0F730]`(AbstractClass::Array.Count) 与"移动中对象数"**：移动中对象数 = 遍历 `0x87F778` 的 Vector，统计 `FootClass`（或 `[obj+0x278]` 非空）对象中 Locomotion 满足 `[loco+0x54]!=-1 && [loco+0x5F]!=0` 的个数。**能区分**：若移动中对象数与 ms/帧强相关（且 objects 数恒定）⇒ 本假设成立；若总对象数相关而移动数不相关⇒ 是"对象数"而非"移动数"。这正是 §14.3 的唯一一刀切方案，且能一并解决 §14.1 的 100% 结构混淆。
2. **【次高】采 `0x87E8E0`（PathFinder GenerationStamp `0x87E8B8+0x28`）的每帧增量 + `0xA8ED84` 帧号**：ΔGenerationStamp 直接数"寻路工作区初始化次数"。**能区分**：若 Δ 与 ms/帧同阶跳变 ⇒ 寻路重算驱动；若 CPU 涨而 Δ≈0 ⇒ 是非寻路的持续刷新（否决本假设）。注意 §563 的回绕/重置需在采样设计里处理。
3. **【验证门控】真机在两趟的低弹窗对同一单位读 `[loco+0x54]`/`[loco+0x5F]`（经 `[unit+0x278]` 或 FootClass 的 Locomotion 指针）**：**能区分**"大量单位静止但 CPU 仍高"（⇒ 门控不是主因，另有下游）vs"大量单位门控开启"（⇒ 门控假设成立）。

---

## LEAD_AUDIT（可独立复算的抽验数字）

1. **AI 派发槽与门控字节**：`0x736204 = 8b 8e 78 02 00 00 85 c9 74 05 8b 01 ff 50 5c`；`0x736210` 的 `ff 50 5c` = `call [eax+0x5C]`，门控只有 `[esi+0x278]!=0`。复跑：`python -c "from work.pehelp import *;[print(fmt(i)) for i in disasm(0x736204,16)]"`（cwd=卡目录）。槽身份：UnitClass 主表 vt `0x7F5C70` 的 `+0x5C` = `0x7360C0`（`work/resolve_ai_slots.py`）。
2. **移动门控字段偏移与取值**：Drive Process wrapper `0x4B055A`：`8b4654`(mov eax,[esi+0x54]) / `83cdff` / `3bc5` / `0f8402010000`(je 0x4B066C，即 `[+0x54]==-1` 跳过) / `385e5f`(cmp byte [esi+0x5F],BL) / `0f84f9000000`(je 0x4B066C)。复跑：`python -c "from work.pehelp import *;[print(fmt(i)) for i in disasm(0x4B055A,32)]"`（cwd=卡目录；原始字节 `rd(0x4B056A,10).hex()=385e5f0f84f900000053`）。**门控字段 = `+0x54`(dword, -1) 与 `+0x5F`(byte, 0)**。
3. **每帧更新槽号 + SearchCore 规模**：Locomotion **offset=4 子表槽 16（`+0x40`）** 指向 Process（Drive `0x7E7EB0+0x40 → 0x4B0500`），**非 `+0x5C`**（`→0x55A910`）；SearchCore `0x429D6D..0x42A3D8` = 1649 字节 / 544 指令 / 回边 `0x42A3D8→0x429D6D`。复跑（cwd=`work/`）：`python check_off4_process.py`（槽表）与 `python -c "from pehelp import *;print(len([i for i in disasm(0x429D6D,1649)]))"`（得 544）；SearchCore 预算 `0xFFF7` 见主台账 §562 字节 `c7442470f7ff0000`。
