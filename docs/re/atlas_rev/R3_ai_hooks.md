# R3 · 战术 AI/小队调度/生产招募 与 补丁生命周期 — atlas 锚定补丁块交付

> **任务**：共享任务板 `task-3`｜[R3] 把小队AI/生产更新与补丁字节审计结论并入 atlas §5、§12.4 与附录勘误
> **执行方**：DSH 子代理 · Agent Teams 成员 `atlas-r3-ai-hooks`
> **基线二进制（只读）**：`ra2youli/gamemd.exe` — 4,825,360 B，MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`，ImageBase `0x400000`，`FileOffset = VA − 0x400000`（`.text/.rdata/.data` 段内等价）
> **证据标准**：`docs/re/EVIDENCE_STANDARD.md` v3 三档 [实证]/[推演]/[待实测]；回报骨架 `docs/re/AGENT_DELIVERY_FORMAT.md` §A 十节
> **快照**：本文件全部字节由**本任务自写只读探针 + Capstone 5.0.7 独立现算**（未转抄他方 claims）；`ra2render/**` 仅只读 grep。
> **红线**：未启动游戏 / 未注入 / 未挂调试器 / 未写二进制；`docs/re/ARCHITECTURE_ATLAS.md` **零写入**（Lead 是 atlas 唯一写者）。

---

## 1. 锚定补丁块（共 10 块，Lead 可机械套用）

> 每块含：目标锚点（行号 + 该行**前 40 字符**原文，已实跑唯一命中）／动作／现状问题／可直接粘贴的替换文本（四反引号围栏）／证据／影响面。

### PATCH-R3-01  ERRATUM：mermaid 节点 H13「招募三兄弟」兵种分工纠正（陆军/海军/空军 ⇒ 战车/步兵/战机）
- **目标锚点**：`docs/re/ARCHITECTURE_ATLAS.md:875`
- **该行前 40 字符原文**：``        H13["AIMode==2: 招募三兄弟 (陆军 0x4FEA``
- **唯一命中实证**：`grep -F 'H13["AIMode==2: 招募三兄弟 (陆军 0x'` → **1 hit @ 875**（全文无第二处）
- **动作**：ERRATUM
- **现状问题**：mermaid 节点把 `0x4FEA60 / 0x4FEEE0 / 0x4FF210` 标为「陆军 / 海军 / 空军」。`house_team_ai_update.md` §9.2-1（:410-415）已定谳三分支的类型过滤分别为 `WhatAmI == 0x28 (UnitType) / 0x10 (InfantryType) / 0x03 (AircraftType)`，即 **战车 / 步兵 / 战机**；atlas 未吸收该订正，节点标签仍是旧猜测。
- **替换文本**：
````markdown
        H13["AIMode==2: 招募三兄弟（战车 0x4FEA60 / 步兵 0x4FEEE0 / 战机 0x4FF210；原记陆军/海军/空军已被 house_team_ai_update.md §9.2 推翻）"]
````
- **证据**：[实证] `0x004FEC9C = 83 F8 28`（`cmp eax, 0x28`，招募①类型过滤）、`0x004FEFC8 = 83 F8 10`（招募②）、`0x004FF2F8 = 83 F8 03`（招募③）；调用点字节 `0x004F90F2 = E8 69 59 00 00` / `0x004F9198 = E8 43 5D 00 00` / `0x004F919F = E8 6C 60 00 00`。来源 `docs/re/house_team_ai_update.md:408-415,419-421`。
- **影响面**：§5.5 正文同源（见 PATCH-R3-02）；§11 速查表**无**招募三分支条目 ⇒ 不受影响；§12 契约不受影响；§2/§3/§4 不受影响。

---

### PATCH-R3-02  REPLACE_BLOCK：§5.5 招募三分支纠正 + 订单槽/工厂下单三数组补全
- **目标锚点**：`docs/re/ARCHITECTURE_ATLAS.md:969`
- **该行前 40 字符原文**：``  分流至西木经典的“招募三兄弟”例程，遍历 `Rules+0xB3C` 可造对``
- **唯一命中实证**：`grep -F '分流至西木经典的'` → **1 hit @ 969**
- **动作**：REPLACE_BLOCK（替换范围 **atlas:968–972 含首尾**，即 `AIMode == 2` 那一条的 5 行）
- **现状问题**：(a)「陆军/海军/空军」与「战车工场与步兵兵营 / 造船厂 / 机场与飞机场」的错误配对（PATCH-R3-01 同源）；(b) 漏掉三分支的**订单槽门控语义**（`+0x5650/+0x5654/+0x5658 == -1` 才评估）与**工厂下单三数组**（`0x00A83CE4 / 0x00A8E34C / 0x00A8B21C` + 虚表槽 `v[0x94]`），这两项是招募路径的全部可观测副作用点。
- **替换文本**：
````markdown
- **`AIMode == 2`（暴兵招募模式）**：
  分流至西木经典的「招募三兄弟」例程，调用点固定顺序 **战车 `0x004F90F2` → 步兵 `0x004F9198` → 战机 `0x004F919F`**（同帧串行，禁调换）[实证]；遍历 `Rules+0xB3C` 可造对象数组，按阵营生产位图（`+0x6CC`）过滤，并调用 `CanBuild (0x004F7870)` 实施分派：
  1. **战车招募**：`0x004FEA60`｜订单槽 `+0x5650`（`0x004FEA70: cmp dword [ebp+0x5650], -1`，非 -1 即直接返回）｜类型过滤 `WhatAmI == 0x28`（`UnitType`，`0x004FEC9C: 83 F8 28`）｜下单走 `UnitTypeClass::Array (0x00A83CE4)`（`0x004F91D0: 8B 0D E4 3C A8 00`）；
  2. **步兵招募**：`0x004FEEE0`｜订单槽 `+0x5654`（`0x004FEEED: 83 BD 54 56 00 00 FF`）｜类型过滤 `WhatAmI == 0x10`（`InfantryType`，`0x004FEFC8: 83 F8 10`）｜下单走 `InfantryTypeClass::Array (0x00A8E34C)`（`0x004F91F8: 8B 0D 4C E3 A8 00`）；
  3. **战机招募**：`0x004FF210`｜订单槽 `+0x5658`（`0x004FF21D: 83 BD 58 56 00 00 FF`）｜类型过滤 `WhatAmI == 0x03`（`AircraftType`，`0x004FF2F8: 83 F8 03`）｜下单走 `AircraftTypeClass::Array (0x00A8B21C)`（`0x004F9220: 8B 0D 1C B2 A8 00`）。
  三分支命中后把订单索引写回各自槽位（如 `0x004FEB09: mov [ebp+0x5650], eax`）；随后 `0x004F91A4`–`0x004F9238` 逐槽取表并以工厂虚表槽 **`v[0x94]`（`StartProduction`）** 下单（`0x004F91E2: FF 92 94 00 00 00`）[实证]。
  > **〔勘误 R3-1 · 2026-09-28〕** 原记「陆军（战车工场与步兵兵营）／海军（造船厂）／空军（机场与飞机场）」为**推演误标**，其三段配对全部不成立；正确分工 = **战车（War Factory）／步兵（Barracks）／战机（Airfield/Helipad）**。证据见 `house_team_ai_update.md` §9.2-1 与本任务独立复算字节（`0x004FEC9C / 0x004FEFC8 / 0x004FF2F8`）。
````
- **证据**：[实证] 见上列 11 处 VA+字节（全部落 `out/re_work/atlas_rev/R3/claims_R3.txt`，门禁 2 全 OK）；类型过滤语义来源 `docs/re/house_team_ai_update.md:410-415`；工厂下单来源 `docs/re/house_team_ai_update.md:422-425`。
- **影响面**：§5.5 内 self-contained（仅本条 5 行）；`PATCH-R3-01` 需同步改 mermaid 标签；§11/§12/§0 不受影响；**影响产品决策**（招募轮转/时间片优化的「类内顺序不可动」边界由此确定）。

---

### PATCH-R3-03  INSERT_AFTER：§5.4 增补「5.4-bis AITrigger 权重回写：唯一写点、精确算式与 YRpp 命名纠偏」
- **目标锚点**：`docs/re/ARCHITECTURE_ATLAS.md:959`
- **该行前 40 字符原文**：``   - **成员解散**：循环调用 `LiberateMember (0x00``
- **唯一命中实证**：`grep -F 'LiberateMember (0x006EA870)'` → **1 hit @ 959**
- **动作**：INSERT_AFTER（插在 :959 之后、§5.5 标题之前）
- **现状问题**：atlas §5.4 只写「权重上调/下调惩罚」，缺三项 09-28 定谳：(1) 权重**写入点唯一性**（不存在每帧漂移）、(2) `RegisterSuccess/RegisterFailure` 的**唯一调用宿主**；(3) **YRpp 头文件命名颠倒**（`+0x104/+0x108` 语义互换）与精确回写算式 —— 后两项直接影响任何「Trigger 权重加速/缓存」优化的正确性。
- **替换文本**：
````markdown
#### 5.4-bis AITrigger 权重回写：唯一写点、精确算式与 YRpp 命名纠偏 [实证]

1. **权重写入点唯一性**：全 `.text` 对 `[reg+0xB8]`（`Weight_Current`）的写操作仅 4 处 —— ctor 初始化 `0x0041E374`、`LoadFromINI` 浮点解析回写 `0x0041F8AC`、`RegisterSuccess (0x0041FD60)` 内 `0x0041FDB3 / 0x0041FDCC / 0x0041FDF7`、`RegisterFailure (0x0041FE20)` 内 `0x0041FE7C / 0x0041FE95 / 0x0041FEC0`。⇒ **不存在每帧/周期性权重浮动**，动态权重完全依赖两个 Register（来源 `house_team_ai_update.md` §9.1-1 [实证]）。
2. **调用宿主唯一**：`call 0x0041FD60` 全镜像仅 `0x006E8E2A`（`E8 31 6F D3 FF`）；`call 0x0041FE20` 全镜像仅 `0x006E8E31`（`E8 EA 6F D3 FF`）。两点均在 `TeamClass::~TeamClass (0x006E8DE0)` 的 `AITriggerTypeClass::Array (0x00A8B204 / 0x00A8B210)` 匹配循环内；匹配键 `0x006E8E13: 8B 46 24 / 8B 91 DC 00 00 00`（`Type(+0x24) vs Trigger.Team1(+0xDC)`）[实证·本任务复算]。
3. **成败标志唯一置位**：`+0x84 AchievedGreatSuccess` 由 ctor `0x006E8B2C`（`88 9E 84 00 00 00`）置 0；全镜像唯一置 1 的指令为 `0x006E9CE8`（`C6 86 84 00 00 00 01`），位于 `TeamClass::AI (0x006E9050)` 的脚本动作跳转表 `0x006E9F74`（派发指令 `0x006E945B: FF 24 85 74 9F 6E 00`；越界默认分支 `0x006E9459: 0F 87 50 01 00 00`）**表项 #49（0x31 = Success）→ 块 `0x006E9CE1`** 之内 [实证·本任务复算]。⇒ 未走完 Action 49 的队伍析构时一律走 `RegisterFailure`。
4. **YRpp 命名颠倒纠偏**：`0x0041FD61: 8B 91 08 01 00 00` 读 `[ecx+0x108]` 作除法的分母；`RegisterSuccess` 同时自增 `+0x104` 与 `+0x108`，而 `RegisterFailure` 只自增 `+0x108` ⇒ 真实语义 **`+0x104 = TimesSuccess`（成功/完成次数）、`+0x108 = TimesExecuted`（总执行次数）**，与 YRpp 头文件命名相反 [实证+推演]。
5. **精确回写算式**（双精度常量 `0x007E2800 = 0.0`、`0x007E1738 = 0.5`）：设 `R = TimesSuccess / TimesExecuted`；
   - `RegisterSuccess`：`Δ = max(TimesExecuted × (R − 0.5), 0)`；`Weight += Rules.AITriggerSuccessWeightDelta(+0xC0) + Δ`，再夹紧到 `[Weight_Min(+0xC0? 实为 +0xC0/+0xC8/+0xD0 族)]`；
   - `RegisterFailure`：`Δ = min(TimesExecuted × (R − 0.5) × Rules.AITriggerTrackRecordCoefficient(+0xD0), 0)`；`Weight += Rules.AITriggerFailureWeightDelta(+0xC8) + Δ`；
   - 写回字节锚点：`0x0041FDAB: DC 81 B8 00 00 00`（`fadd qword [ecx+0xB8]`）、`0x0041FDB3: DD 91 B8 00 00 00`（`fst qword [ecx+0xB8]`）。
   > **禁改**：浮点运算顺序与夹紧逻辑（`>0` 区间浮点不可重排），否则同帧 bit 级结果漂移。
6. **评估宿主只读性**：`0x006F0AB0` 在 `0x006F0C61`（`DD 86 B8 00 00 00` = `fld qword ptr [esi+0xB8]`）读取权重后调 `0x007C5F00 (__ftol)` 转整型用于轮盘赌；**评估路径对 `+0xB8` 只读**（本任务复算：函数体内无写该字段的指令）[实证]。
````
- **证据**：[实证] `0x0041FD61 / 0x0041FDAB / 0x0041FDB3 / 0x006F0C61 / 0x006E8E2A / 0x006E8E31 / 0x006E8B2C / 0x006E9CE8 / 0x006E945B`（本任务独立现算，落 `claims_R3.txt`）；来源 `docs/re/house_team_ai_update.md:362-404`。
- **影响面**：§5.4 明确化；**§12.2 红线「随机数消费序 / 威胁评估枚举序」不涉及**（本块无语义变更）；§11 速查表**建议**后续补 `AITriggerTypeClass` 三个字段偏移的「语义更正」备注（本块不直接改 §11）；影响「AITrigger 权重缓存/加速」类优化的可行域。

---

### PATCH-R3-04  INSERT_AFTER：§5.3 补全 ConditionMet 第 6 条子条件 + 权重读取点
- **目标锚点**：`docs/re/ARCHITECTURE_ATLAS.md:945`
- **该行前 40 字符原文**：``3. **小队实例化**：所有条件满足后，调用 `TeamTypeClass::``
- **唯一命中实证**：`grep -F '小队实例化'` → **1 hit @ 945**
- **动作**：INSERT_AFTER（插在 :945 之后、§5.4 标题之前）
- **现状问题**：atlas §5.3-2 只列 4 个条件，漏 `CivilianHouseOwns (0x0041EC90)`（第 5 个条件类型）与内部 5 个私有辅助；亦缺评估宿主的**权重读取点/轮盘赌**与只读性结论。
- **替换文本**：
````markdown
> **〔R3 补充 · 2026-09-28〕** `ConditionMet (0x0041E720)` 的子条件共 **6** 类（原文列 4 类，漏 `CivilianHouseOwns`）：`OwnerHouseOwns (0x0041EE90)` / `EnemyHouseOwns (0x0041EAF0)` / **`CivilianHouseOwns (0x0041EC90)`**（平民所有权判定）/ `HouseCredits (0x0041F230)` / `IronCurtainCharged (0x0041F0D0)` / `ChronoSphereCharged (0x0041F180)`（来源 `docs/re/house_team_ai_update.md:51-57` [实证]）。评估宿主 `0x006F0AB0` 另有 5 个仅被其调用的私有辅助 `0x6F2230 / 0x6F25E0 / 0x6F26E0 / 0x6F2780 / 0x6F27F0`（语义未展开，见 `house_team_ai_update.md:332`）。
>
> **权重读取与轮盘赌**：`0x006F0AB0` 于 `0x006F0C61`（`DD 86 B8 00 00 00` = `fld qword ptr [esi+0xB8]`）读 `Weight_Current` → `call 0x007C5F00 (__ftol)` → 多分支累加总权重 → `call 0x0065C7E0`（轮盘赌随机选择；权重 5000 特权短路清空候选表除外）。**评估过程对 `+0xB8` 零写入** [实证]。
>
> **数组三元组精确化 [实证]**：`TeamTypeArray` 的正确三元组 = Items `0x00A8ECA4` / Capacity `0x00A8ECA8` / **Count `0x00A8ECB0`**（写回链 `0x006F085C: 89 0D B0 EC A8 00 → 8B 0D A4 EC A8 00 → 89 34 81`；`ProcessAllTaskforces 0x006F2040` 亦以 `A1 B0 EC A8 00` 读 Count），与 House 数组（Items `0xA8022C` / Capacity `0xA80230` / Count `0xA80238`，锚点 `0x0067D4EC` / `0x0067D4C2`）完全同构 ⇒ §5.1 的「TeamTypeArray (0x00A8ECA0)」应读作「向量对象基址 0x00A8ECA0；Items / Count = 0x00A8ECA4 / 0x00A8ECB0」。
>
> **顺序红线（AI 侧）**：`AITriggerTypeClass::Array` 的**下标顺序**决定同权重下的轮盘赌边界，属 §12.2「并列时原枚举序」的同族约束；任何「脏标记跳过 / 结果缓存」改造**不得**改变该数组遍历顺序，也不得复用跨帧结果（同帧多 House 共享亦须慎重）。
````
- **证据**：[实证] `0x0041E720 = 53 55 56 8B F1 57 8B 8E DC 00 00 00`（序言）；`0x006F0AB0 = 83 EC 50 53 55 56 33 F6`；`0x006F0C61 = DD 86 B8 00 00 00`；`0x006F0B12 = 8A 87 F2 01 00 00`（`AITriggersActive +0x1F2` 门控）。来源 `docs/re/house_team_ai_update.md:51-57,402-404`。
- **影响面**：§5.3 明确化；§12.2 红线（同族顺序约束，不新增红线）；§11/§0 不受影响。

---

### PATCH-R3-05  INSERT_AFTER：§12.4 第 1 条后补「安装期字节级通法条目（等长/平齐/Cave/rel32/装后自检）」
- **目标锚点**：`docs/re/ARCHITECTURE_ATLAS.md:1966`
- **该行前 40 字符原文**：``   - 必须通过 `VirtualProtect` 精确获取并备份目标内存地址``
- **唯一命中实证**：`grep -F '必须通过' + 'VirtualProtect'` → **1 hit @ 1966**（§12.4 全文仅此一处）
- **动作**：INSERT_AFTER（插在 :1966 之后、:1967「Phase 0 至 Phase 6」之前；**保持 1./2./3. 序号不变**）
- **现状问题**：atlas 全文 **0 命中** `pending_execution_master_table` / `P-1…P-6` / `rel32` 复算规则；§12.4 只写「VirtualProtect 备份 + Phase 顺序」，**缺**全部 18 项补丁落地所依赖的字节级通法：等长性 + `90` 平齐、Cave 固定基址 `0x01B00000` 与**分配失败即跳过**、跳板 21 处 rel32（含负向回绕）复算契约、装后机械自检。这四项是「回滚 = 逐字节无损」可判定性的前提。
- **替换文本**：
````markdown
   - **等长性与平齐通法 [实证]**：任何原地替换的机器码长度必须 ≤ 原指令长度；不足处以 `90`（NOP）严格平齐，**严禁**让下一条指令首字节落在替换区中间。台账全 18 项中 15 处机器码补丁全部等长；`E9 rel32` 覆盖 5/6/8/9 字节者分别补 0/1/3/4 个 `90`（例如 P-6.1：原 6B `0F 8D 98 00 00 00` → `E9 99 00 00 00 90`）。（来源 `docs/re/patch_hex_audit.md` §1.2 [E2]）
   - **Cave 基址与分配失败策略**：外部挂钩统一使用**固定基址 `0x01B00000`** 独立页；分配/属性改写失败时**直接跳过该项不安装**（禁止带病写入），且**不启用**动态重定位机制。（来源 `docs/re/patch_hex_audit.md` §[9]-1）
   - **rel32 逐位复算契约 [实证]**：`rel32 = target − (site + insn_len)`，32 位小端回绕。外部正向挂钩 10 处 + 跳板内负向回绕 11 处 = **21 处**，须由脚本逐位复算并与注入字节一致；负向回绕值必须 `>= 0x80000000`。示例：注入点 `0x0064C911` → `0x01B00000` 得 `E9 AA 37 4B 01`；跳板 `0x01B000D8` 回跳 `0x004C6CB0` 得 `E8 D3 6B 9C FE`。（来源 `docs/re/patch_hex_audit.md` §2.2）
   - **装后自检（机械可判）[推演]**：`VirtualQuery` 校验目标页可执行属性 + 读取目标 VA 首 5 字节确认 `E9`/`E8` + 复算 `rel32` 命中 Cave 槽位；三者全绿才置「hook armed」遥测，否则回滚该点并记日志。（规格来源 `docs/re/patch_hex_audit.md` §1.2 [E5] 行；**注**：该行自引的「本报告 §2.5」在源文档中不存在，属交叉引用悬空，见 [3] 勘误）
````
- **证据**：[实证] `0x006D3D99 = 0F 8D 98 00 00 00`（原版 6B）、`0x0064C911 = E8 9A A3 E7 FF`（P-1.4 注入点）、`0x0064C6F2 = 0F 85 69 05 00 00`（P-1.1，6B→5B+1×90）；rel32 数值来源 `docs/re/patch_hex_audit.md:85-112`（第三方脚本复算，本任务抽验 `P-1.4` 与 `P-6.1` 两条 rel32 算术自洽）。
- **影响面**：§12.4 安装期条款具体化；**§0.2/§0.3 不涉及**；§11 速查表不涉及；与 §12.4 第 3 条「逐字节无损写回」互为前提（本块给安装期，第 3 条给卸载期）。

---

### PATCH-R3-06  APPEND_SECTION：§12.4 尾增「12.4-bis 已落地补丁字节级验收账（P-1 ~ P-6 · 18 项）」
- **目标锚点**：`docs/re/ARCHITECTURE_ATLAS.md:1973`
- **该行前 40 字符原文**：``   - 依据 **G-07 规约**，必须将启动时修改的 `TYPE` 字段原``
- **唯一命中实证**：`grep -F 'G-07 规约'` → **1 hit @ 1973**（§12.4 末行）
- **动作**：APPEND_SECTION（插在 :1973 之后、:1975 的 `---` 之前）
- **现状问题**：atlas **0 命中** `pending_execution_master_table` 与 `P-1…P-6`。18 项「零推演落地」补丁（含 P-2 裂缝/间谍卫星包）是 §12.4 生命周期规范的实际适用对象，其**原字节/等长/rel32/风险层级**在 atlas 中完全缺失；P-2 更触及 ①同步语义 与 ③存档结构（Tier 1 极高风险），必须单列。
- **替换文本**：
````markdown
### 12.4-bis 已落地补丁字节级验收账（P-1 ~ P-6 · 18 项）[实证]

> **性质**：本小节把台账 `pending_execution_master_table.md` 声明的「零推演落地」18 项补丁纳入 §12.4 生命周期管辖，作为**安装期**（原字节与等长核对、rel32 复算）与**回滚期**（逐字节写回）的字节级验收依据。
> **依据**：`docs/re/patch_hex_audit.md`（第三方独立复算，17 处静态 VA 全 MATCH / 15 处机器码补丁全等长 / 21 处 rel32 全 MATCH）；**本任务独立复算全部 17 处原字节 = 17/17 MATCH**（落 `out/re_work/atlas_rev/R3/claims_R3.txt`）。
> **Cave 基址**：`0x01B00000`（固定基址，分配失败即跳过，见 §12.4 第 1 条通法条目）。

| 项号 | 目标 VA | 原字节 | 等长性 | rel32 | 语义要点 | 风险层级 |
|:---:|:---:|:---|:---:|:---:|:---|:---:|
| P-1.1 | `0x0064C6F2` | `0F 85 69 05 00 00` | 6B→5B+`90` | `0x014B3909` | H-D1 ZF 探针（`test [esp+0x20],0x40` 读原始 ZF；`popad;popfd` 还原） | 中高 |
| P-1.2 | `0x0064CC61` | `A0 80 48 B0 00` | 5B 等长 | `0x014B33DA` | H-D2 断开快照（首位 `pushad` 保护原 `EAX=slot*37`） | 低 |
| P-1.3 | `0x0064DE75` | `5F 5E 5D 5B 83 C4 14 C3` | 8B→5B+3×`90` | `0x014B2206` | H-D5 帧 CRC 环；★必须 `0F B6 C0`（`movzx eax,al`）杜绝 `83 E0 FF` 符号扩展 | 中 |
| P-1.4 | `0x0064C911` | `E8 9A A3 E7 FF` | 5B 等长 | `0x014B37AA` | H-D6 主事件流镜像（`ECX` 现场无损透传 `0x4C6CB0`） | **高**（①命令序） |
| P-1.5 | `0x0064CC0A` | `E8 A1 A0 E7 FF` | 5B 等长 | `0x014B34F1` | H-D6b 次事件流镜像 | **高**（①命令序） |
| P-2.1 | `0x00568273` | `89 99 34 01 00 00` | 6B→6×`90` | N/A | `RevealArea2` 误清零 `Cell+0x134` | **极高**（①③） |
| P-2.2 | `0x00577EC5` | `89 B8 34 01 00 00` | 6B→6×`90` | N/A | `RevealArea3` 误清零 `Cell+0x134` | **极高**（①③） |
| P-2.3 | `0x00577B60` | `89 98 34 01 00 00` | 6B→6×`90` | N/A | `Reshroud` 误清零 `Cell+0x134` | **极高**（①③） |
| P-2.4 | `0x00508F8F` | `74 65` | 2B 等长（`EB 65`） | 短跳 → `0x00508FF6` | SpySat 门控短路全图点亮分支 | **极高**（①③） |
| P-2.5 | TYPE 动态区 | 动态捕获 | N/A | N/A | 首次捕获 4 处原值（`SW+0xB0/+0xF8`、`BldType+0x16A5/+0x16F0`），卸载时原样回写（= §12.4 第 3 条 G-07） | 高 |
| P-3.1 | `0x007EFA68` | `C0 CE 62 00` | 4B（虚表槽 69） | N/A | `ParticleClass::v[69] → 0x0062CEC0` 剔除 | 低 |
| P-3.2 | `0x007EFCB0` | `80 E2 62 00` | 4B（虚表槽 69） | N/A | `ParticleSystemClass::v[69] → 0x0062E280` | 低 |
| P-4.1 | `0x007C8E17` | `6A 01 FF 74 24 08` | 6B→5B+`90` | `0x01337324` | CRT `operator new` 池命中改写 `[esp+0x1C]` | 中 |
| P-4.2 | `0x007C8B3D` | `FF 74 24 04 E8 A2 08 00 00` | 9B→5B+4×`90` | `0x0133763E` | CRT `operator delete` 范围守卫 + 投毒 `0xDEADBEEF` | 中 |
| P-5.1 | `0x00750920` | `51 A0 AC 64 84 00` | 6B→5B+`90` | `0x013AF89B` | PlayGlobal 限频早退 → `xor eax,eax; ret 8` | 低 |
| P-5.2 | `0x007509E0` | `A0 AC 64 84 00` | 5B 等长 | `0x013AF85B` | PlayAt 限频早退 → `xor eax,eax; ret 4` | 低 |
| P-6.1 | `0x006D3D99` | `0F 8D 98 00 00 00` | 6B→5B+`90` | `0x00000099` | L4 双模切换（字节对照表见 §2.2） | 最低 |
| P-6.2 | `0x006DA7D0` | `A1 F4 F7 87 00` | 原生 API 驱动 | N/A | `RegisterCellAsVisible`，350 格全量保底（见 §2.3） | 最低 |

**P-2 专项（Tier 1 · 强触 ①同步语义 与 ③存档结构）**
- 三处 6 字节写点原字节（本任务独立复算 MATCH）：`0x00568273 = 89 99 34 01 00 00`、`0x00577EC5 = 89 B8 34 01 00 00`、`0x00577B60 = 89 98 34 01 00 00`；写入目标 = `CellClass+0x134 (GapsCoveringThisCell)`（§12.4 §11 字段表 `:1834`），该字段**进入 `.SAV`** 且主导索敌开火判定分支。
- 门禁要求：P-2.1–P-2.4 落地的构建须将 `EnableGapProtection` / `EnableSpySatGate` 纳入**联机握手校验字段**，版本或配置不一致直接终止对局握手；**严禁混端联机**（一端打补丁一端原版必发 DESYNC）。
- 与 S1（`PatchSpySatBuildingTypes` 改 `TYPE` 数据）为相邻双路径：混装须统一开关，且 S1 必须按 G-07 提供 Remove 还原（当前**未落地**，见 `hook_gate_gap_table.md` §9.3 G-07 行）。

**与 §12.4 第 2 条的合规缺口（需 Lead 判决）**
- A6：B1/B2 混色桩与 `0x006D3D99` 补丁在 `InstallCellClassDrawHook` 内**无条件安装**，无独立开关 ⇒ 违反「每一个新增功能提供独立 INI 开关」；G-04 已部分落地（`L4DirtyMode` 三档，见 `ra2render/blitter_hooks.cpp:696-707`），但 `EnableFogBlendStubs` 仍 0 命中。
> 【W3 勘误 · W3-A6/ISSUE-STALE-L4-EXIST】改前：L4DirtyMode` 三档，见 `ra2render/blitter_hooks.cpp:696-707`），但 `EnableFogBlendStubs` 仍 0 命中；改后：L4DirtyMode 已在 blitter_hooks.cpp:757 读取并支持 force-full / vision-dirty 模式；三处 ini 均已配置出厂值。；依据：ra2render/blitter_hooks.cpp:757; ra2render/ra2render.ini:251; ra2youli/ra2render.ini:186; ra2bench/ra2render.ini:186；分级：P1
- A8：S1 `PatchSpySatBuildingTypes` **无 Remove 还原** ⇒ 违反 §12.4 第 3 条 G-07（P-2.5 即为其补丁规格）。
- A1：`Hook_RLEBlitTransXlat_G` 仅遥测转发、无像素逻辑 ⇒ 「装了但功能未实现」，遥测计数会误导 §12.4 第 2 条的「独立遥测 = 生效证据」判读。
````
- **证据**：[实证] 17 处静态 VA 原字节（本任务 `claims_R3.txt` 全 OK）；Cave/rel32 数值来源 `docs/re/patch_hex_audit.md:85-112`；风险层级与语义要点来源 `docs/re/patch_hex_audit.md` §1.1/§2.3/§[7]；合规缺口来源 `docs/re/INSTALLED_HOOKS_AUDIT.md` §5.2 A1/A6/A8 与 `docs/re/hook_gate_gap_table.md` §5 G-04/G-07。
- **影响面**：**影响产品决策**（发布门禁读法、回滚手册）；§11 速查表**建议**增列 Cave 区段 `0x01B00000` 一行（本块不直接改 §11）；§12.2 红线**触及**（P-2 属 ①③，须 MP 门控矩阵 + 真机对拍）；§0 准则不涉及。

---

### PATCH-R3-07  ERRATUM：§9.4 G-04 行 —— 实施方式已由「安装期条件化」改为「运行期门控」，验收判据随之更新
- **目标锚点**：`docs/re/ARCHITECTURE_ATLAS.md:1591`
- **该行前 40 字符原文**：``| **G-04** | `EnableStarCraftFog` | **1*``
- **唯一命中实证**：`grep -F '| **G-04** |'` → **1 hit @ 1591**
- **动作**：ERRATUM（**替换该表格行**）
- **现状问题**：G-04 行记「置 0 时联动关闭 B1/B2 混色桩与 L4 补丁，**逐字节还原官方机器码**」。`hook_gate_gap_table.md` §10.2（E2）与 `INSTALLED_HOOKS_AUDIT.md` §5.2 A6 已定谳：**补丁字节在开/关闸两种状态下都常驻**，实施改为**运行期门控**（桩内 `cmp [总闸] / je` 决定是否混色/是否驱动，关闸出口不经过任何写像素或写状态指令）⇒ 原「关闸后原字节恢复」判据**不再适用**；另 `L4DirtyMode` 已于工作树落地（见 PATCH-R3-08）。
- **替换文本**：
````markdown
| **G-04** | `EnableStarCraftFog` 总闸 + `[FogOfWar] L4DirtyMode` ＋ `[FogOfWar] EnableFogBlendStubs`（未落地） | 总闸 `1`；`L4DirtyMode=force-full` | 星际迷雾总闸。**补丁字节常驻安装**，桩内以 `cmp [总闸]/je` 做**运行期门控**：总闸 `=0` 时 B1/B2/L4 三桩走关闸出口，**不还原字节、不写像素、不写状态** | **判据（E2 订正）＝关闸时「三计数恒 0」（半透明层绘制 / 混色桩介入 / 小地图减暗驱动，连续两行遥测均 0）＋ 关闸出口反汇编证据**；原「关闸后逐字节还原官方机器码」判据**作废**（补丁字节常驻属设计如此）；产品决策不变 |
````
- **证据**：[实证] 产物侧（第三方只读复算，本任务未复跑）：B1 关闸出口 RVA `0x21B1 = B9 40 F4 47 00 FF E1`、B2 `0x2251 = B9 E1 F4 47 00 FF E1`、L4 `0x22D2` 侧 `popfd; jge; mov ecx,0x6D3D9F; jmp ecx`，计数 `inc` 位于 `je` 之后（关闸不增）；来源 `docs/re/hook_gate_gap_table.md:377-386`（§10.2 E2）与 `docs/re/INSTALLED_HOOKS_AUDIT.md:192`（A6）。引擎侧原字节本任务复算：`0x6D3D99 = 0F 8D 98 00 00 00`。
- **影响面**：**影响产品决策**（验收判据）；§12.4 第 2 条「软开关直通原版」的**实现形态**（运行期门控 ≠ 安装期条件化）；§0.3 第 4 条 G-04 措辞同源（见 PATCH-R3-08）；**[待实测]**：真机「三计数恒 0」未跑（本任务禁跑游戏）。

---

### PATCH-R3-08  ERRATUM：§0.3 第 5 条「G-03/G-04/G-06/G-07/G-10 维持未落地」——G-04 已部分落地（工作树事实）
- **目标锚点**：`docs/re/ARCHITECTURE_ATLAS.md:164`
- **该行前 40 字符原文**：``   - **G-03 / G-04 / G-06 / G-07 / G-10 ``
- **唯一命中实证**：`grep -F 'G-03 / G-04 / G-06 / G-07 / G-10 维持未落地'` → **1 hit @ 164**
- **动作**：ERRATUM（**替换该行**，其余不变）
- **现状问题**：该行断言「全源码 grep 0 命中 … `L4DirtyMode` …」。本任务对当前工作树只读核验：`ra2render/blitter_hooks.cpp` 现为 **194,530 B / 3,039 行**，`L4DirtyMode` **已落地**（定义 `:43`、三档读取与红字告警 `:696-707`、运行期判定 `:2418`、遥测 `:825`），双份 ini 亦新增该键（`ra2render/ra2render.ini:176` 注释、`:186 = force-full`）。⇒ 原「0 命中」口径已过期（其余四项仍成立）。
- **替换文本**：
````markdown
   - **G-04 已部分落地（R3 复核 · 2026-09-28）[实证]**：`ra2render/blitter_hooks.cpp` = **194,530 B / 3,039 行**；`L4DirtyMode` 已入源码（定义 `:43`、读取/合法性校验/红字告警 `:696-707`、运行期判定 `:2418`、遥测 `:825`）与 `ra2render/ra2render.ini`（`:176` 注释 / `:186 L4DirtyMode=force-full`）；`ra2render/ra2render.dll` = 152,576 B。**仍 0 命中**：`EnableThreatRetention` / `MpStateWrites` / `RestoreSpySat` / `EnableFogBlendStubs` ⇒ **G-03 / G-06 / G-07 维持未落地**，**G-10** 卫生项（死符号/死宏/空开关）未清理；
````
- **证据**：[实证·工作树只读] `grep -R 'L4DirtyMode|RestoreSpySat|EnableThreatRetention|MpStateWrites|EnableFogBlendStubs|RestoreTypeOffsets|EnableGapProtection|EnableSpySatGate' ra2render/ → 11 命中`，其中 `L4DirtyMode` 占 9 条（源码 8 条 + ini 2 条，含 1 条同文件重复）；文件规模由 `Get-Item/Get-Content` 实测。快照时点：本卡执行期间（见 [5] 快照 mtime）。
- **影响面**：**影响产品决策**（发布门禁读法：`L4DirtyMode` 已可配置，G-04 余项仅 `EnableFogBlendStubs`）；§9.4 G-04 行同源（PATCH-R3-07）；§12.4-bis 合规缺口段同步。

---

### PATCH-R3-09  APPEND_SECTION：附录 DA1 追加「DA1-bis 跨文档冲突登记（R3 · 2026-09-28）」
- **目标锚点**：`docs/re/ARCHITECTURE_ATLAS.md:2000`
- **该行前 40 字符原文**：``| 其余全文地址/行号 | 本任务只复核与 DA1 六份文档相关的锚点（雷达双点``
- **唯一命中实证**：`grep -F '本任务只复核与 DA1 六份文档相关的锚点'` → **1 hit @ 2000**（文件末行）
- **动作**：APPEND_SECTION（插在文件末尾）
- **现状问题**：`patch_hex_audit.md` §[7]-2（:282）写「P-1.3 H-D5 挂载于 `call 0x650A90` 之后，严格保证**每帧消费 1 次** `ScenarioClass::Random` 的黄金契约」——与 atlas §9.2 / §12.2〔ASM-FIX2-1〕已订正的「帧 CRC 路径每逻辑帧 **2** 次」**直接冲突**。该文档未列入 `asm_fix2_report.md` §3.9 的域外订正清单（该清单只点了 `REVERSE_ENGINEERING_AND_PATCHES.md:2215`、`docs/RE_COORDINATION.md:1352`、`HOOK_POINT_MATRIX.md:405`、`re_sprint_S17_report.md:132`、`trigger_runtime_deep_dive.md:454`），属**新发现的第 6 处同源过期表述**，必须登记以免再次成为错误源。
- **替换文本**：
````markdown

---

## 附录 DA1-bis · 跨文档冲突登记与交叉确认（R3 · 2026-09-28）

> **性质**：本小节为**勘误登记**（不就地改写他方文档；他方文档属 Lead 处置面）。
> **快照**：`ra2youli/gamemd.exe` 4,825,360 B / MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`（只读未变）；本卡实跑 `python tools/verify_anchors.py` = **323/323 PASS**、`python tools/audit_bytes.py out/re_work/atlas_rev/R3/claims_R3.txt` = **63/63 OK**。

| 位置 | 改前原文（逐字） | 改后文本 | 理由 | 影响面 |
|---|---|---|---|---|
| `docs/re/patch_hex_audit.md:282` | `P-1.3 H-D5 挂载于 `call 0x650A90` 之后，严格保证每帧消费 1 次 `ScenarioClass::Random` 的黄金契约` | `帧尾路径（`0x0064DE70 → 0x00650A90`）消费 1 次；**帧 CRC 路径每逻辑帧合计 2 次**（折叠点 `0x0064DE3F` + 帧尾 `0x00650AB7`/`0x00650AF2` 之一）` | 与 atlas §9.2〔ASM-FIX2-1〕订正后口径冲突；本任务独立反汇编复算 4 个调用点全部为 `E8 …` 调用 `0x0065C780`（局内 RNG 抽取入口），确认 2 次 | **影响产品决策**（补丁 RNG 禁令的计数依据）；同源表述 `HOOK_POINT_MATRIX.md:405` 已订正、本处**未订正** |
| `docs/re/patch_hex_audit.md:57`（§1.2 E5 行） | `给出 VirtualQuery 属性检验 + 目标 VA 5 字节 read + rel32 加算判定规格`（自引「本报告 §2.5」） | 内容成立；**交叉引用悬空** —— 该报告 §2 只有 §2.1/§2.2/§2.3，**不存在 §2.5** | 源文档内部引用失效，规格正文实际在该表格行内 | 文档一致性（P2，不影响结论） |
| `docs/re/patch_hex_audit.md` §1.1 表（18 项） | — | **交叉确认（非勘误）**：17 处静态 VA 原字节本任务**独立复算 17/17 MATCH**；P-6.1 `0x006D3D99 = 0F 8D 98 00 00 00` 与 DA1 `:1999`「未在本任务复算的项」互为独立闭环 | atlas 附录 DA1 曾标注该项「未复算」 | 提升 `§2.2` 双模对照表的证据等级（由「未复算」→ 双源独立一致） |
| `docs/re/hook_gate_gap_table.md:377-386`（§10.2 E2） | `EnableStarCraftFog=0/FadeFogTransition=0 时`不写`对应补丁字节（安装期条件化）；验收＝关闸后读原字节恢复` | `运行期门控：字节常驻，关闸走出口；判据＝关闸三计数恒 0 + 出口反汇编证据` | atlas §9.4 G-04 行仍记旧判据（「逐字节还原官方机器码」） | 见 PATCH-R3-07（atlas 就地订正） |
````
- **证据**：[实证] `0x0064DE3F = E8 3C E9 00 00`、`0x0064DE70 = E8 1B 2C 00 00`、`0x00650AB7 = E8 C4 BC 00 00`、`0x00650AF2 = E8 89 BC 00 00`（4 处均 `call 0x0065C780`；本任务现算）；`0x006D3D99 = 0F 8D 98 00 00 00`；来源 `docs/re/asm_fix2_report.md:182-189`（§3.9 域外清单）与 `docs/re/patch_hex_audit.md:282`。
- **影响面**：§12.2 红线「每帧恰消费 2 次」的证据链**加强**（新增第 6 处同源纠正指引）；§9.2 不涉及；**不改写他方文档**（交 [3] 勘误清单）。

---

### PATCH-R3-10  INSERT_AFTER：§12.2 红线框后补「枚举序红线的等价实现口径」（跨节候选，非本卡指定目标）
- **目标锚点**：`docs/re/ARCHITECTURE_ATLAS.md:1929`
- **该行前 40 字符原文**：`` │   - 威胁评估并列时的原枚举序 (Greatest_Threat 严格大``
- **唯一命中实证**：`grep -F '威胁评估并列时的原枚举序'` → **1 hit @ 1929**
- **动作**：INSERT_AFTER（插在 :1929 之后，仍在红线框内；或在框后 :1931 之后加脚注，两者择一，Lead 决定）
- **现状问题**：§12.2 只列红线「先到者胜」，未给**可判定的等价实现口径**；`house_team_ai_update.md` §9.3 已给出字典序元组等价性证明（本题 [推演]），可直接决定「空间索引改造是否必须保序」这一高频争议。
- **替换文本**：
````markdown
> **〔R3 补充 · 2026-09-28〕枚举序红线的等价实现口径 [推演 + 实证]**：原版择优为**严格大于**（`0x006F936B: 3B C1 → 0x006F936D: 7E 08`；同构更新点 `0x006F9C3C` / `0x006F9D87`，前置打分函数均为 `0x006F7CA0`）⇒「并列时枚举序先到者胜」等价于在维护最优目标时增加**平分决胜比较** `ord(c)`：令 `V(c) = (S(c), −ord(c))`，取字典序最大元即恒等于原版结果，**与遍历顺序无关**。工程口径：空间哈希查询循环**无需排序**（O(1) 维护），但**必须**实现 `(score, −ord)` 全序决胜；未实现决胜的任何几何分桶改造一律判**违反本条红线**。`ord` 取 `ArrayIndex`（全局数组路）或 `UniqueID`（格子链，`ScenarioClass::Instance->UniqueID` 严格自增）。
> **[待实测]**：两端 `UniqueID` 的同帧一致性需真机对拍确认（若两端分配序不同，则 `UniqueID` 不可作为跨端决胜键，须回落 `(WhatAmI << 16) | ArrayIndex`）。取证步骤：双端同种子开局，记录同一帧内同分候选的 `UniqueID` 序列；判定标准＝两端序列逐位一致（一致⇒可用），任一不一致⇒禁用。
````
- **证据**：[实证] `0x006F936B = 3B C1` / `0x006F936D = 7E 08`（来源 `docs/re/house_team_ai_update.md:444-454`，本任务未逐字节复算该两组地址，标注**转引 [实证·来源]**）；[推演] 等价性定理来源 `house_team_ai_update.md` §9.3-2（:460-471）。
- **影响面**：**§4.4 同源**（寻敌择优，属他人节）；§12.2 红线语义明确化（**不放松**，只是给出可判定口径）；若 Lead 认为与 R4 的 §12.2 用词类补丁冲突，**可整块丢弃**（不影响其余 9 块）。


---

## 2. 覆盖度自证表（来源文档 §小节 → 命中的 PATCH-R3-NN）

> Lead 定向要求（V1 覆盖审计）：`house_team_ai_update.md` 已判 **INTEGRATED**（atlas L862/870/875/900/903/936/949/963 已收录地址层），本表对该文件整体标注 **「已收口」**，只在「标签/算式/字段精度」层给出 ERRATUM，**不重复补地址**。

### 2.1 `docs/re/house_team_ai_update.md`
| 来源小节 | 归属 | 说明 |
|---|---|---|
| §0 结论速览 | **已收口** | 地址层已在 atlas §5 全量收录；无新增地址 |
| §1 每帧 AI 调用树 | **已收口** | atlas L853-908 mermaid + §5.1/§5.2 已含 ProcessAllTaskforces / HouseClass::Update / 8 帧 / 100 帧 / Timer / AITrigger / 三兄弟 / dtor |
| §2.1 全局数组（含 task-11 勘误） | **PATCH-R3-04** | TeamType Count=`0xA8ECB0`、House 数组同构（本任务独立复算 4 锚点） |
| §2.2 HouseClass 偏移 | **已收口** | atlas §5.2 表已含 `+0x1E4/+0x1F2/+0x5798/+0x5634/+0x566C` 等 |
| §2.3 TeamClass 偏移 | **PATCH-R3-03** | `+0x24`(Type) / `+0x84`(AchievedGreatSuccess) 的字节级匹配证据 |
| §2.4 AITriggerTypeClass 偏移 | **PATCH-R3-03** | `+0xB8/+0x104/+0x108` 命名颠倒纠偏 + 写回算式 |
| §3 热点函数表 | **已收口** | atlas §5.2/§5.5 已列 |
| §3.1 权重更新伪码 | **PATCH-R3-03** | 以定谳算式替换原粗粒度描述 |
| §4 与 Greatest_Threat 关系 | **已收口** + **PATCH-R3-10** | 「AI 不扫全图」已收口；「并列序」等价口径见 R3-10 |
| §5 优化插入点 A/B/C | **部分吸收 + 不入 atlas（余）** | 该节属**建议规格**（含风险/收益），非架构图谱内容；其「禁改清单」（数组遍历顺序 / ConditionMet 短路 / 浮点顺序 / CanBuild 递归）已以「禁改」形式并入 **PATCH-R3-03/04** |
| §6 确定性风险总表 | **同上（部分吸收）** | 风险分级属规格面；红线结论已在 §12.2 覆盖 |
| §7 未决问题 | **PATCH-R3-04**（第 1/7 项已定谳）；第 2/3/5 项 → **不入 atlas** | 第 2/3 项（`0x006E53A0` this 类型、`+0x3C` 向量真实类型）**仍开放**，atlas 不应收录未定谳内容 |
| §8 验证脚本 | **不入 atlas** | 工具索引，非架构内容 |
| §9.1 权重回写全链路 | **PATCH-R3-03** | 唯一写点/唯一调用宿主/Action49 |
| §9.2 招募三兄弟时序 | **PATCH-R3-01 + PATCH-R3-02** | 分工纠错 + 订单槽/下单数组 |
| §9.3 空间哈希等效性证明 | **PATCH-R3-10**（跨节候选） | 属 §12.2 红线口径 |

### 2.2 `docs/re/patch_hex_audit.md`（Lead 判定 PARTIAL；下列 4 项 **0 命中** 均已在 R3 补块）
| 来源小节 | 归属 | 说明 |
|---|---|---|
| [0] 摘要 / 总裁决 | **PATCH-R3-06** | 「全 18 项可落地」纳入 §12.4-bis |
| [1.1] **18 项补丁总表**（原字节/等长/rel32/风险） | **PATCH-R3-06** | atlas 原 **0 命中**（无 `P-1…P-6`、无 `pending_execution_master_table`） |
| [1.2] E1–E6 | **PATCH-R3-05**（E2 等长平齐 / E5 装后自检）+ **PATCH-R3-06**（E1/E3/E4/E6） | E5 的行内自引「§2.5」悬空 → **PATCH-R3-09** 登记 |
| [2.1] claims 17 条 | **PATCH-R3-06** + `claims_R3.txt` | 本任务独立复算 17/17 MATCH |
| [2.2] **rel32 21 处（Cave 0x01B00000）** | **PATCH-R3-05** | atlas 原文**无 rel32 复算契约、无固定基址策略** |
| [2.3] 语义等价实证（`0F B6 C0` / `ret 8` / `ret 4`） | **已收口**（atlas §0.3 第 1/2 条） | 本任务复算其原字节侧锚点一致 |
| [3] 勘误「无」 | **PATCH-R3-09** | 本卡新增 1 处跨文档冲突（RNG 计数）+ 1 处悬空引用 |
| [4] 未闭环「无」 | **PATCH-R3-09** | 该报告未覆盖 RNG 计数同源表述（属其自述「无」的边界外） |
| [5] 写作用域 | **不入 atlas** | 执行方合规声明 |
| [6] 门禁原文 | **已收口** | 本卡独立复跑（323/323 + 63/63） |
| [7] 风险红线（**P-2 Cell+0x134** / Tier 分级） | **PATCH-R3-06**（P-2 专项）；其中「每帧消费 1 次 RNG」→ **PATCH-R3-09 ERRATUM** | atlas 原无 Tier 分级与 P-2 存档/同步面 |
| [8] 交付物 | **不入 atlas** | 台账 |
| [9] 待裁决（固定基址降级 / P-2 联机门禁键） | **PATCH-R3-05 + PATCH-R3-06** | 固化为 §12.4 通法条目 |

### 2.3 `docs/re/INSTALLED_HOOKS_AUDIT.md`
| 来源小节 | 归属 | 说明 |
|---|---|---|
| §0 覆盖率自证 / §2.1–§2.7 Hook 清单 / §6 遥测 / §7 ini 键 | **不入 atlas + 理由** | 属**部署台账/工具产物**；atlas 只收契约，不收逐 Hook 清单（否则每次源码变更都要改 atlas） |
| §1 安装入口与生命周期 | **已收口**（§12.4 第 1/3 条） | — |
| §3 v1.6.0 四键 | **PATCH-R3-07** | G-04 判据订正 |
| §4 可序列化 × 联机总表 | **不入 atlas + 理由** | 该表口径已由 §10.1 就地订正，且与 atlas §9.4 重叠；本卡无新增字节事实 |
| §5.1 对称性结论 / §5.2 **A1–A10** | **PATCH-R3-06**（合规缺口段：A1/A6/A8） | §12.4 第 2 条的违规面单列 |
| §8 还原路径总表 | **PATCH-R3-07** | 「关闸后原字节恢复」判据作废 |
| §9 结论 1–6 | **PATCH-R3-08**（结论 5 的落地状态） | G-04 已部分落地 |
| §10.1–§10.5 DA1 勘误 | **PATCH-R3-08 / PATCH-R3-09** | 行数第三次漂移（194,530 B / 3,039 行） |

### 2.4 `docs/re/hook_gate_gap_table.md`（**抽样口径声明**：只取与 §12.4 门控/回滚相关的 §0/§1.4/§1.6/§2/§4/§5/§9/§10，未通读 §3/§6/§7 全文）
| 来源小节 | 归属 | 说明 |
|---|---|---|
| §0 时点差异 | **PATCH-R3-08** | L4DirtyMode 已落地 |
| §1.1–§1.3（Blitter/L2/Draw 槽） | **不入 atlas + 理由** | 逐 Hook 门控清单属部署面（与 2.3 同理） |
| §1.4 #17/#18/#19（B1/B2/L4 无独立键） | **PATCH-R3-06**（合规缺口）+ **PATCH-R3-07**（判据） | — |
| §1.6 S1–S4 | **PATCH-R3-06** | P-2.5/G-07 还原契约 |
| §2 v1.6.0 四键专项 | **PATCH-R3-07** | FadeFogTransition 行为描述随判据更新 |
| §3 L2 三处 `>>4` | **不入 atlas + 理由** | 已由 atlas §9.4 G-02 收口且源码已强制 position（§0.3 第 5 条） |
| §4 L4 `0x006D3D99` 专项 | **PATCH-R3-07 / PATCH-R3-08** | 「无门控」口径已过期 |
| §5 执行缺口 G-01…G-10 | **PATCH-R3-06 / 07 / 08** | G-04 状态更新、G-07 还原缺口并入 12.4-bis |
| §6 ini 键全表 / §7 台账草稿 | **不入 atlas + 理由** | 台账 |
| §8 附录（终局裁决） | **已收口** | atlas §9.4 为唯一权威口径 |
| §9.1 G-01/G-02/G-08 已落地 | **已收口** | atlas §0.3 第 5 条 + DA1 已登记 |
| §9.3 G-03/G-04/G-06/G-07/G-10 | **PATCH-R3-08** | G-04 部分落地纠正 |
| §10.1 E1 / §10.2 E2 | **PATCH-R3-07** | 运行期门控 + 混色语义 |
| §10.3 E3（S2 条件写） | **PATCH-R3-06**（合规缺口）；正文表述 → **不入（R4 用词面）** | 避免与 R4 的用词类补丁重叠 |
| §10.4 E4（行号失效→VA/RVA） | **不入 atlas + 理由** | atlas 已统一用 VA；属引用纪律 |

### 2.5 `docs/re/HOOK_POINT_MATRIX.md`（**抽样口径声明**：只取 §三/§四/§五/§6.0/§6.4/§6.5/§6.8，未通读 §二 全表与 §一）
| 来源小节 | 归属 | 说明 |
|---|---|---|
| §2.5 / §3.5 / §6.8.4 雷达挂钩 | **不入 atlas + 理由** | DA1 已就地订正 atlas :99/:517/:1888；本卡无新增字节事实 |
| §三 冲突三（Greatest_Threat inline） | **已收口**（atlas §4/§9.3） | — |
| §三 冲突四（L4 `0x006D3D99`） | **PATCH-R3-07** | 与 P-6.1 双模口径对齐 |
| §三 冲突五（小地图） | **不入 atlas + 理由** | 已由路线 A 收口（DA1） |
| §三 冲突六（裂缝 NOP + 超武透缝） | **PATCH-R3-06**（P-2 专项） | 补联机门禁与存档面 |
| §四 唯一推荐落地顺序表 Phase 0–6 | **已收口**（§12.4 第 1 条引用）+ **PATCH-R3-05** | 通法条目落 §12.4 |
| §五 红线（RNG 2 次 ASM-FIX2-1） | **PATCH-R3-09** | 追加第 6 处同源过期表述 |
| §6.0 勘误 E-1…E-4 / §6.5 DS-1…DS-6 | **PATCH-R3-08** | DS-4 行数第三次漂移 |
| §6.4 裁决 1（L4 双模键）/ 裁决 3（P-2.5 TYPE 还原） | **PATCH-R3-06 / 07 / 08** | — |
| §6.6 门禁原文 / §6.7 产出物 | **不入 atlas** | 过程记录 |

### 2.6 `docs/re/asm_fix2_report.md`
| 来源小节 | 归属 | 说明 |
|---|---|---|
| [3.1]–[3.4] atlas 内 RNG 勘误（4 处） | **PATCH-R3-09**（补第 6 处跨文档） | — |
| [3.5]–[3.8] Surface / landing / asm_fix 勘误 | **不入 atlas + 理由** | 与本卡目标（§5/§12.4/DA1）无交集 |
| **[3.9] 域外最小订正清单（5 项）** | **PATCH-R3-09** | **新增第 6 项**：`patch_hex_audit.md:282` |
| [4] 未闭环 1（RNG 2 次行为面，P0） | **PATCH-R3-09** + 回报 [4] | [待实测] |
| [5]/[6]/[8] 合规声明/门禁/交付物 | **不入 atlas** | 过程记录 |
| [7] 风险红线 ②（RNG 消费序） | **PATCH-R3-09** | — |
| [9] 待裁决 1/2（禁区两行、`HOOK_POINT_MATRIX:405`） | **已收口**（:405 已订正）+ 本卡同类新增第 6 处 | — |

---

## 3. 交付回报（`docs/re/AGENT_DELIVERY_FORMAT.md` §A 十节骨架）

```text
[META]
task=task-3  executor=DSH 子代理 / Agent Teams 成员 atlas-r3-ai-hooks  elapsed≈2400s（无可靠计时器，按里程碑估算）  mode=read-only（仅写本卡授权作用域内新文件）
scope_declared=docs/re/atlas_rev/R3_ai_hooks.md、out/re_work/atlas_rev/R3/**
```

### [0] 结论摘要
1. 交付 **10 个锚定补丁块**（全部锚点已实跑唯一命中，见 §1 各块「唯一命中实证」）：§5 四块（三兄弟分工纠错 ×2 / 权重算式 / ConditionMet 与权重读取），§12.4 两块（安装期字节通法 / 18 项补丁账），附录 DA1 一块（跨文档冲突登记），跨节 ERRATUM 两块（§9.4 G-04 判据、§0.3 落地状态），跨节候选一块（§12.2 枚举序等价口径）。
2. **最硬结论**：招募三分支真实分工 = **战车 / 步兵 / 战机**（类型过滤 `WhatAmI == 0x28 / 0x10 / 0x03`，本任务独立复算 + 工厂下单三数组 `0x00A83CE4 / 0x00A8E34C / 0x00A8B21C`）⇒ atlas §5.5 与 mermaid H13 的「陆军 / 海军 / 空军」为**误标**，须 ERRATUM。
3. **patch_hex_audit 与 atlas 确有一处冲突**：其 §[7]-2 记「每帧消费 **1** 次 `ScenarioClass::Random`」，与 atlas §12.2 / §9.2〔ASM-FIX2-1〕订正后的「**2** 次」矛盾；本任务独立反汇编 4 个调用点（`0x64DE3F` + `0x650AB7/0x650AF2`）确认 2 次，已单列 ERRATUM（PATCH-R3-09）。该处**未被** `asm_fix2_report.md` §3.9 的 5 项域外清单覆盖。
4. **18 项补丁原字节本任务独立复算 17/17 MATCH**（含 Cave `0x01B00000` rel32 抽验），补齐 atlas 对 `pending_execution_master_table` / `P-1…P-6` 的 0 命中面。
5. **最大风险**：P-2（`Cell+0x134` 三处 NOP + SpySat 门控）为 Tier 1，**强触 ①同步语义 + ③存档结构**；其字节面已闭，行为面须真机 MP 对拍（本卡未跑，标 [待实测]）。

### [1] 逐条必答项结论表
| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|:--:|---|---|:--:|---|
| 1 | §5.1–§5.5 需并入哪些 09-28 新结论？ | 地址层**已收口**；须 ERRATUM 两处（三兄弟分工 L875/L968-972）、补充三类（权重算式 L959 后 / ConditionMet 第 6 条件 L945 后 / TeamType Count 精度） | [实证] | atlas:875,945,959,968-972；`house_team_ai_update.md:362-471` |
| 2 | §12.4 需并入哪些？ | ①安装期字节通法（等长+`90`平齐 / Cave 固定基址与失败跳过 / 21 处 rel32 复算 / 装后自检）②18 项补丁字节级验收账 + P-2 Tier 1 专项 + 合规缺口（A1/A6/A8） | [实证]+[推演] | atlas:1966,1973；`patch_hex_audit.md` §1.2/§2.2/§[9]；`INSTALLED_HOOKS_AUDIT.md:187,192,194` |
| 3 | 附录 DA1 需登记哪条勘误？ | 新增 **1 处跨文档冲突**（`patch_hex_audit.md:282` RNG 1→2）+ **1 处悬空交叉引用**（同文 :57 自引 §2.5 不存在）+ 1 条交叉确认（P-6.1 原字节） | [实证] | atlas:2000；`patch_hex_audit.md:57,282` |
| 4 | patch_hex_audit 是否给出与 atlas 冲突的字节或等长替换结论？ | **字节/等长结论无冲突**（17/17 原字节 MATCH、15/15 等长、与 atlas §2.2 `0x006D3D99` 一致）；**唯一冲突在 RNG 消费计数**（非字节面） | [实证] | `claims_R3.txt`（17 条 P-* 断言）；atlas:438,1999 |
| 5 | 门禁是否实跑通过？ | `verify_anchors.py` = **323/323 PASS**；`audit_bytes.py claims_R3.txt` = **63/63 OK**（原文见 [6]） | [实证] | 本卡实跑，退出码 0/0 |
| 6 | 是否越界写入？ | **否**：仅写 3 处授权路径；atlas / 他方 R# / `ra2render/**` / `ra2youli/**` / 既有 `docs/re/*.md` 零写入（见 [5]） | [实证] | [5] 清单 + mtime |
| 7 | 是否伪造实测？ | **否**：全部「实测」均由只读脚本对基线镜像现算，脚本与输出在交付物内可复跑；未跑游戏的一律标 [待实测] | [实证] | `out/re_work/atlas_rev/R3/{probe_r3*.py,gate1_*.txt,gate2_*.txt}` |

### [2] 关键证据块
1. **招募三兄弟类型过滤（本任务现算）**：`0x004FEC9C = 83 F8 28`（`cmp eax, 0x28`，`UnitType`）／`0x004FEFC8 = 83 F8 10`（`InfantryType`）／`0x004FF2F8 = 83 F8 03`（`AircraftType`）；均为「先 `call dword ptr [edx+0x2c]`（`WhatAmI` 虚调用）后比较」。
2. **订单槽与工厂下单**：`0x004FEA70 = 83 BD 50 56 00 00 FF`／`0x004FEEED = 83 BD 54 56 00 00 FF`／`0x004FF21D = 83 BD 58 56 00 00 FF`（三槽 `== -1` 才评估）；下单 `0x004F91D0 = 8B 0D E4 3C A8 00`／`0x004F91F8 = 8B 0D 4C E3 A8 00`／`0x004F9220 = 8B 0D 1C B2 A8 00` → `0x004F91E2 = FF 92 94 00 00 00`（`call [edx+0x94]` = `StartProduction`）。
3. **Action 49 唯一置位（跳表实证）**：派发 `0x006E945B = FF 24 85 74 9F 6E 00`（`jmp dword ptr [eax*4 + 0x6E9F74]`）→ 表项 #49（`0x31`）= `0x006E9CE1` → 块内 `0x006E9CE8 = C6 86 84 00 00 00 01`（`mov byte [esi+0x84], 1`）。
4. **权重回写唯一宿主**：`0x006E8E2A = E8 31 6F D3 FF`（`call 0x41FD60`）／`0x006E8E31 = E8 EA 6F D3 FF`（`call 0x41FE20`）；权重读写 `0x0041FDAB = DC 81 B8 00 00 00`（`fadd [ecx+0xB8]`）、`0x0041FDB3 = DD 91 B8 00 00 00`（`fst [ecx+0xB8]`）、评估侧只读 `0x006F0C61 = DD 86 B8 00 00 00`（`fld [esi+0xB8]`）。
5. **帧 CRC 路径 RNG = 2 次（本任务现算，与 patch_hex_audit:282 冲突）**：`0x0064DE3F = E8 3C E9 00 00`（`call 0x65C780`，折叠点）+ `0x0064DE70 = E8 1B 2C 00 00`（`call 0x650A90`）→ 帧尾 `0x00650AB7 = E8 C4 BC 00 00` / `0x00650AF2 = E8 89 BC 00 00`（各 `call 0x65C780`；二者属互斥分支）。
6. **P-2 存档/同步面字节**：`0x00568273 = 89 99 34 01 00 00`／`0x00577EC5 = 89 B8 34 01 00 00`／`0x00577B60 = 89 98 34 01 00 00`（均 `mov [cell+0x134], 0`，`CellClass+0x134 = GapsCoveringThisCell`，进 `.SAV`）；`0x00508F8F = 74 65`（`je 0x508FF6`）。
7. **Cave/rel32 抽验**：`P-1.4` 注入点 `0x0064C911 = E8 9A A3 E7 FF`，目标 `0x01B00000` ⇒ `rel32 = 0x01B00000 − (0x0064C911 + 5) = 0x014B37AA` → 小端 `AA 37 4B 01`（与 `E9 AA 37 4B 01` 一致）；`P-6.1` 原地 `0x006D3D99 = 0F 8D 98 00 00 00` → `rel32 = 0x00000099`（`rel32` 算术自洽）。
8. **机器可读断言**：`out/re_work/atlas_rev/R3/claims_R3.txt` 共 **63 条**（PART A 33 / PART B 17 / PART C 6 / PART D 4 + 3 条补充锚点），`audit_bytes.py` **63/63 OK**。

### [3] 勘误（逐条；勘误单列，不得藏在正文）
| # | 目标文件:行号 | 改前原文 | 改后文本 | 理由 | 影响面 |
|:--:|---|---|---|---|---|
| E-1 | `docs/re/ARCHITECTURE_ATLAS.md:875` | `H13["AIMode==2: 招募三兄弟 (陆军 0x4FEA60 / 海军 0x4FEEE0 / 空军 0x4FF210)"]` | 见 **PATCH-R3-01** | mermaid 标签把三分支误标为海/空军 | 影响产品决策（招募轮转优化边界）；同源 §5.5 |
| E-2 | `docs/re/ARCHITECTURE_ATLAS.md:968-972` | 「陆军（战车工场与步兵兵营）／海军（造船厂）／空军（机场与飞机场）」 | 见 **PATCH-R3-02** | 三段配对全部不成立；真实 = 战车/步兵/战机 | 影响产品决策 |
| E-3 | `docs/re/patch_hex_audit.md:282` | `P-1.3 H-D5 挂载于 `call 0x650A90` 之后，严格保证每帧消费 1 次 `ScenarioClass::Random` 的黄金契约` | 「帧尾路径消费 1 次；**帧 CRC 路径每逻辑帧合计 2 次**（`0x0064DE3F` + `0x00650AB7/0x650AF2`）」 | 与 atlas §12.2〔ASM-FIX2-1〕冲突；本任务独立复算 4 调用点 | **影响产品决策**（RNG 禁令计数）；**不在本卡写作用域 ⇒ 交 Lead**（见 PATCH-R3-09 与 [9]-1） |
| E-4 | `docs/re/patch_hex_audit.md:57` | `给出 VirtualQuery 属性检验 + …（本报告 §2.5 装后自检机械脚本设计规格）` | 内容成立；把「本报告 §2.5」改为「本文 §1.2 本行」 | 该报告 §2 只有 §2.1/§2.2/§2.3，**无 §2.5** ⇒ 交叉引用悬空 | 文档一致性 P2（不影响结论） |
| E-5 | `docs/re/ARCHITECTURE_ATLAS.md:1591`（§9.4 G-04 行） | 「置 0 时联动关闭 B1/B2 混色桩与 L4 补丁，**逐字节还原官方机器码**」 | 见 **PATCH-R3-07** | 实施已改为**运行期门控**（字节常驻），原验收判据作废 | **影响产品决策**（验收判据）；§12.4 第 2 条实现形态 |
| E-6 | `docs/re/ARCHITECTURE_ATLAS.md:164`（§0.3 第 5 条） | 「G-03 / G-04 / G-06 / G-07 / G-10 维持未落地…grep 0 命中 … `L4DirtyMode`…」 | 见 **PATCH-R3-08** | 工作树实测 `L4DirtyMode` **已落地**（源码 8 处 + ini 2 处） | 影响产品决策（发布门禁读法） |
| E-7 | `docs/re/HOOK_POINT_MATRIX.md:517`（§6.5 DS-4）／`:562`（§6.8.1 E-4）／`hook_gate_gap_table.md:342,354`／`INSTALLED_HOOKS_AUDIT.md:322` | 「当前源文件 1788 行」／「1892 行」／「2346 行 / 117,930 B」 | 统一刷新为 **194,530 B / 3,039 行**（本任务实测快照） | 源码行数**第三次漂移**，四处「当前值」断言全部失效 | 文档一致性 P2（属他方文档，交 Lead） |
| E-8 | `docs/re/ARCHITECTURE_ATLAS.md` §5.1「TeamTypeArray (0x00A8ECA0)」 | 以向量对象基址代指 Items/Count | 补注 Items `0x00A8ECA4` / Count `0x00A8ECB0`（House 数组同构） | 精度补充（非错误） | 文档一致性 P3；并入 **PATCH-R3-04** |

> 除上表外**无其他勘误**；本卡未就地改写任何他方文档（含 `patch_hex_audit.md`）。

### [4] 未闭环清单
| # | 缺口 | 为何无法静态闭环 | 下一步取证方法（可执行） | 级别 |
|:--:|---|---|---|:--:|
| 1 | 「帧 CRC 每逻辑帧 2 次 RNG」的**行为面后果**（是否改变 desync 判定/对拍门限） | 静态只能定字节与计数 | MP 门控矩阵 + 双端真机对拍：同种子开局，逐帧比对 `CurrentFrameCRC (0x00AC51FC)` 序列与 `SYNC_SNAP`；判据＝两端 CRC 序列逐帧一致且 RNG 抽取计数各为 2 | **P0 [待实测]** |
| 2 | 招募三分支的**运行时归属**（静态已到 `WhatAmI` 过滤 + 下单数组，但未观测哪类工厂实际接单） | 需运行期观测 House 订单槽与工厂队列 | 在 `0x004F90F2/0x004F9198/0x004F919F` 三入口读 `+0x5650/+0x5654/+0x5658` 与 `+0x1E4`；判据＝AIMode==2 时三槽被依次写非 -1 | P2 [待实测] |
| 3 | G-04 关闸「三计数恒 0」判据的真实性 | 需真机遥测 | 删键/置 0 启动 → 连续两行 `[ra2render-fogswitch] 总闸三计数` 均 0；判据＝三计数恒 0 且无 except.txt | P1 [待实测] |
| 4 | §12.2 枚举序决胜键：两端 `UniqueID` 同帧一致性 | 跨进程分配序无法静态证 | 双端同种子同帧记录同分候选 `UniqueID` 序列；一致⇒可用，否则回落 `(WhatAmI << 16) | ArrayIndex` | P2 [待实测] |
| 5 | 18 项补丁的实际**落地/联机门控**验收（现网仅 L4/雷达/Draw 等已装；P-1/P-2/P-4/P-5 未装） | 需构建后真机 | 按 [4]-1 方式对每项做 MP 门控矩阵；P-2 另需握手字段 `EnableGapProtection`/`EnableSpySatGate` | P1 [待实测] |
| 6 | `hook_gate_gap_table.md` §10.2 的「三计数」符号（`s_fogLayerDraws / s_fogBlendStubHits / s_radarDarkenDriven`）未在 atlas 遥测契约中登记 | 属 §12.4 遥测条款缺口（本卡未越界改 §12.4 之外的契约表） | 由 Lead 决定是否在 §12.4 增列「遥测字段命名契约」 | P2 |

### [5] 写作用域合规声明
**改动文件清单**（全部在任务卡授权范围内；时间窗＝本卡执行期）：
| 文件 | 字节数 | 行数 | 说明 |
|---|---:|---:|---|
| `docs/re/atlas_rev/R3_ai_hooks.md` | 70965 | 533 | 本交付（补丁块 + 覆盖度 + 十节回报） |
| `out/re_work/atlas_rev/R3/claims_R3.txt` | 5322 | 77 | 63 条机器可读断言 |
| `out/re_work/atlas_rev/R3/probe_r3.py` / `probe_r3b.py` / `probe_r3c.py` / `dump_anchors.py` | 5688 | — | 只读探针（VA→字节/反汇编/xref/跳表） |
| `out/re_work/atlas_rev/R3/gate1_verify_anchors.txt` / `gate2_audit_bytes.txt` | 10368 | — | 门禁原文落盘 |
| `out/re_work/atlas_rev/R3/anchors.json` | 1200 | — | 锚点前 40 字符机器提取（机器可读） |

**未触碰清单（零写入）**：`docs/re/ARCHITECTURE_ATLAS.md`（Lead 唯一写者）、其他 R# 成员的 `docs/re/atlas_rev/*.md` 与 `out/re_work/atlas_rev/R*/**`、全部既有 `docs/re/*.md`（只读引用）、`ra2render/**`（只读 grep）、`ra2youli/**`（含 `gamemd.exe`，只读）、`REVERSE_ENGINEERING_AND_PATCHES.md`、`tools/*`（金标准脚本只读）。

**目标二进制只读证明**：`ra2youli/gamemd.exe` — 4,825,360 B，MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`，mtime 2026-09-25 08:10:48Z（执行期内未变）；`.text` 原始段哈希 `c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738`（门禁 1 PASS）、`.detour` 原生签名完好。**未启动游戏、未注入、未挂调试器、未改 exe/dll。**

### [6] 门禁实跑输出（原文粘贴）
```text
> python tools\verify_anchors.py          （工作目录 D:\Project\ra2-campaign-forge）
===================================================================================================================
  RA2/YR 二进制决定性锚点自动化回归测试套件 (verify_anchors.py)
===================================================================================================================
目标文件 : D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe (大小: 4,825,360 字节, ImageBase: 0x400000)
断言文件 : D:\Project\ra2-campaign-forge\docs\re\anchor_claims.txt
反汇编器 : Capstone x86-32 引擎已就绪
-------------------------------------------------------------------------------------------------------------------
[基线完整性审计]
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
  [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
-------------------------------------------------------------------------------------------------------------------
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
===================================================================================================================
(exit code = 0)
```

```text
> python tools\audit_bytes.py out/re_work/atlas_rev/R3/claims_R3.txt
VA         期望字节                       实际字节                   判定     标签/上下文
--------------------------------------------------------------------------------------------------------------
0x4f8440   83 ec 4c 53 55 56 8b f1    83 ec 4c 53 55 56 8b f1 OK     HouseClass::Update 序言 (v[23] 逐 House 虚调用) | sub esp, 0x4c
0x4f9093   0f 84 b0 01 00 00          0f 84 b0 01 00 00      OK     AIMode==0 早退 (je 0x4F9249) | je 0x4f9249
0x4f90a7   83 f8 01                   83 f8 01               OK     cmp eax,1  (AIMode 分派) | cmp eax, 1
0x4f90ae   e8 2d 53 00 00             e8 2d 53 00 00         OK     call 0x004FE3E0 AI_BaseConstructionUpdate (AIMode==1) | call 0x4fe3e0
0x4f90f2   e8 69 59 00 00             e8 69 59 00 00         OK     call 0x004FEA60 招募①战车 (WhatAmI==0x28) | call 0x4fea60
0x4f9198   e8 43 5d 00 00             e8 43 5d 00 00         OK     call 0x004FEEE0 招募②步兵 (WhatAmI==0x10) | call 0x4feee0
0x4f919f   e8 6c 60 00 00             e8 6c 60 00 00         OK     call 0x004FF210 招募③战机 (WhatAmI==0x03) | call 0x4ff210
0x4fea70   83 bd 50 56 00 00 ff       83 bd 50 56 00 00 ff   OK     cmp dword [ebp+0x5650],-1 招募①锁槽 | cmp dword ptr [ebp + 0x5650], -1
0x4feeed   83 bd 54 56 00 00 ff       83 bd 54 56 00 00 ff   OK     cmp dword [ebp+0x5654],-1 招募②锁槽 | cmp dword ptr [ebp + 0x5654], -1
0x4ff21d   83 bd 58 56 00 00 ff       83 bd 58 56 00 00 ff   OK     cmp dword [ebp+0x5658],-1 招募③锁槽 | cmp dword ptr [ebp + 0x5658], -1
0x4fec9c   83 f8 28                   83 f8 28               OK     WhatAmI==0x28 (UnitType) 类型过滤 (招募①) | cmp eax, 0x28
0x4fefc8   83 f8 10                   83 f8 10               OK     WhatAmI==0x10 (InfantryType) 类型过滤 (招募②) | cmp eax, 0x10
0x4ff2f8   83 f8 03                   83 f8 03               OK     WhatAmI==0x03 (AircraftType) 类型过滤 (招募③) | cmp eax, 3
0x6f0ab0   83 ec 50 53 55 56 33 f6    83 ec 50 53 55 56 33 f6 OK     AITrigger 评估宿主序言 | sub esp, 0x50
0x6f0b12   8a 87 f2 01 00 00          8a 87 f2 01 00 00      OK     AITriggersActive (+0x1F2) 门控读取 | mov al, byte ptr [edi + 0x1f2]
0x4f8a00   8b 96 98 57 00 00          8b 96 98 57 00 00      OK     TeamDelayTimer +0x5798 读取 | mov edx, dword ptr [esi + 0x5798]
0x4f8f9c   8b 7e 48 4f 78 1c          8b 7e 48 4f 78 1c      OK     8 帧门控: 建筑向量 +0x48 计数 / +0x3C 基址 | mov edi, dword ptr [esi + 0x48]
0x4f8522   39 ae 14 56 00 00          39 ae 14 56 00 00      OK     100 帧门控: BaseNode 向量 +0x5614 长度比较 | cmp dword ptr [esi + 0x5614], ebp
0x4f8fbe   8b 96 34 56 00 00          8b 96 34 56 00 00      OK     生产门控 Timer +0x5634 读取 | mov edx, dword ptr [esi + 0x5634]
0x6e8e13   8b 46 24 8b 91 dc 00 00 00 8b 46 24 8b 91 dc 00 00 00 OK     TeamClass.Type(+0x24) vs Trigger.Team1(+0xDC) | mov eax, dword ptr [esi + 0x24]
0x6e8e20   8a 86 84 00 00 00 84 c0 74 07 8a 86 84 00 00 00 84 c0 74 07 OK     AchievedGreatSuccess(+0x84) 成败判决 | mov al, byte ptr [esi + 0x84]
0x6e8e2a   e8 31 6f d3 ff             e8 31 6f d3 ff         OK     call 0x0041FD60 RegisterSuccess (全程序唯一调用点) | call 0x41fd60
0x6e8e31   e8 ea 6f d3 ff             e8 ea 6f d3 ff         OK     call 0x0041FE20 RegisterFailure (全程序唯一调用点) | call 0x41fe20
0x6e8b2c   88 9e 84 00 00 00          88 9e 84 00 00 00      OK     TeamClass::ctor 将 +0x84 初始化为 0 | mov byte ptr [esi + 0x84], bl
0x6e9ce8   c6 86 84 00 00 00 01       c6 86 84 00 00 00 01   OK     Action 49(0x31) 分支内唯一置 +0x84=1 | mov byte ptr [esi + 0x84], 1
0x6e945b   ff 24 85 74 9f 6e 00       ff 24 85 74 9f 6e 00   OK     jmp dword ptr [eax*4+0x6E9F74] 脚本动作跳表分发 | jmp dword ptr [eax*4 + 0x6e9f74]
0x41fd61   8b 91 08 01 00 00          8b 91 08 01 00 00      OK     RegisterSuccess 读 [ecx+0x108] (TimesExecuted) | mov edx, dword ptr [ecx + 0x108]
0x41fdab   dc 81 b8 00 00 00          dc 81 b8 00 00 00      OK     fadd qword [ecx+0xB8] Weight_Current 累加 | fadd qword ptr [ecx + 0xb8]
0x41fdb3   dd 91 b8 00 00 00          dd 91 b8 00 00 00      OK     fst qword [ecx+0xB8] Weight_Current 写回 | fst qword ptr [ecx + 0xb8]
0x6f0c61   dd 86 b8 00 00 00          dd 86 b8 00 00 00      OK     评估宿主只读读取 Weight_Current (无写回) | fld qword ptr [esi + 0xb8]
0x6f085c   89 0d b0 ec a8 00          89 0d b0 ec a8 00      OK     TeamTypeArray Count = 0xA8ECB0 写回 | mov dword ptr [0xa8ecb0], ecx
0x67d4c2   8b 15 38 02 a8 00          8b 15 38 02 a8 00      OK     House 数组 Count = 0xA80238 | mov edx, dword ptr [0xa80238]
0x67d4ec   8b 15 2c 02 a8 00          8b 15 2c 02 a8 00      OK     House 数组 Items = 0xA8022C | mov edx, dword ptr [0xa8022c]
0x6e9281   e8 0a 18 00 00             e8 0a 18 00 00         OK     call 0x006EAA90 TeamClass::Recruit (主动通道) | call 0x6eaa90
0x686b20   81 ec 64 01 00 00          81 ec 64 01 00 00      OK     场景全局更新序言 (调 0x006F2040 ProcessAllTaskforces) | sub esp, 0x164
0x6f2040   a1 b0 ec a8 00             a1 b0 ec a8 00         OK     ProcessAllTaskforces 读 TeamType Count 0xA8ECB0 | mov eax, dword ptr [0xa8ecb0]
0x64c6f2   0f 85 69 05 00 00          0f 85 69 05 00 00      OK     P-1.1 H-D1 校验探针 (jne 0x64CC61) | jne 0x64cc61
0x64cc61   a0 80 48 b0 00             a0 80 48 b0 00         OK     P-1.2 H-D2 断开快照 (mov al,[0xB04880]) | mov al, byte ptr [0xb04880]
0x64de75   5f 5e 5d 5b 83 c4 14 c3    5f 5e 5d 5b 83 c4 14 c3 OK     P-1.3 H-D5 帧 CRC 环尾声 | pop edi
0x64c911   e8 9a a3 e7 ff             e8 9a a3 e7 ff         OK     P-1.4 H-D6 主事件流 (call 0x4C6CB0) | call 0x4c6cb0
0x64cc0a   e8 a1 a0 e7 ff             e8 a1 a0 e7 ff         OK     P-1.5 H-D6b 次事件流 (call 0x4C6CB0) | call 0x4c6cb0
0x568273   89 99 34 01 00 00          89 99 34 01 00 00      OK     P-2.1 Gap1 局部开图 (mov [ecx+0x134],ebx) | mov dword ptr [ecx + 0x134], ebx
0x577ec5   89 b8 34 01 00 00          89 b8 34 01 00 00      OK     P-2.2 Gap2 全图开图 (mov [eax+0x134],edi) | mov dword ptr [eax + 0x134], edi
0x577b60   89 98 34 01 00 00          89 98 34 01 00 00      OK     P-2.3 Gap3 重遮蔽 (mov [eax+0x134],ebx) | mov dword ptr [eax + 0x134], ebx
0x508f8f   74 65                      74 65                  OK     P-2.4 SpySat 门控 (je 0x508FF6) | je 0x508ff6
0x7efa68   c0 ce 62 00                c0 ce 62 00            OK     P-3.1 Particle v[69] -> 0x0062CEC0 | ror dh, 0x62
0x7efcb0   80 e2 62 00                80 e2 62 00            OK     P-3.2 PSys v[69] -> 0x0062E280 | and dl, 0x62
0x7c8e17   6a 01 ff 74 24 08          6a 01 ff 74 24 08      OK     P-4.1 CRT operator new | push 1
0x7c8b3d   ff 74 24 04 e8 a2 08 00 00 ff 74 24 04 e8 a2 08 00 00 OK     P-4.2 CRT operator delete | push dword ptr [esp + 4]
0x750920   51 a0 ac 64 84 00          51 a0 ac 64 84 00      OK     P-5.1 音频 PlayGlobal | push ecx
0x7509e0   a0 ac 64 84 00             a0 ac 64 84 00         OK     P-5.2 音频 PlayAt | mov al, byte ptr [0x8464ac]
0x6d3d99   0f 8d 98 00 00 00          0f 8d 98 00 00 00      OK     P-6.1 L4 视口模式切换 (jge 0x6D3E37) | jge 0x6d3e37
0x6da7d0   a1 f4 f7 87 00             a1 f4 f7 87 00         OK     P-6.2 RegisterCellAsVisible 入口 | mov eax, dword ptr [0x87f7f4]
0x655d38   89 44 24 28 a1 50 35 b7 00 89 44 24 28 a1 50 35 b7 00 OK     路线 A 下沉挂钩点 9B 原字节 | mov dword ptr [esp + 0x28], eax
0x655d41   3b c5 74 18                3b c5 74 18            OK     跳板回跳目标原字节 | cmp eax, ebp
0x655c50   a1 4c 3d a8 00             a1 4c 3d a8 00         OK     RadarClass::Plot_Cell 函数本体序言 | mov eax, dword ptr [0xa83d4c]
0x65719a   e8 91 93 00 00             e8 91 93 00 00         OK     跳帧抑制调用点 (call 0x00660530) | call 0x660530
0x6574c3   e8 88 e7 ff ff             e8 88 e7 ff ff         OK     已废弃历史调用点 (call 0x00655C50) | call 0x655c50
> 【W3 勘误 · W3-A6/ISSUE-DISAMBIG-RADAR-HOOK】改前：0x6574c3；改后：0x006574C3（RadarClass::Plot_Cell 主循环调用点，见 ra2render.h:158；实际补丁下沉点位于 0x00655D38，见 blitter_hooks.cpp:150, 3016）；依据：ra2render/ra2render.h:158; ra2render/blitter_hooks.cpp:150, 2711, 2920, 3016, 3090；分级：P2
0x6f8df0   83 ec 5c 8b 15 34 ec a8 00 83 ec 5c 8b 15 34 ec a8 00 OK     Greatest_Threat 汇聚入口 9B inline 原字节 | sub esp, 0x5c
0x64de3f   e8 3c e9 00 00             e8 3c e9 00 00         OK     call 0x0065C780 折叠点消费 1 次 | call 0x65c780
0x64de70   e8 1b 2c 00 00             e8 1b 2c 00 00         OK     call 0x00650A90 帧尾路径 | call 0x650a90
0x650ab7   e8 c4 bc 00 00             e8 c4 bc 00 00         OK     call 0x0065C780 帧尾消费点 A | call 0x65c780
0x650af2   e8 89 bc 00 00             e8 89 bc 00 00         OK     call 0x0065C780 帧尾消费点 B | call 0x65c780
--------------------------------------------------------------------------------------------------------------
合计 63 条：OK=63  MISMATCH/NOREAD=0
(exit code = 0)
```

### [7] 风险与红线提示
| 触及项 | 是否触及 | 说明 |
|---|:--:|---|
| ① 同步语义 / 命令序 | **触及** | P-2（`Cell+0x134` ×3 + SpySat 门控）与 P-1.4/P-1.5 命令镜像属强触碰面；本卡只做**字节级归档**，**不宣称零风险/零 Desync** ⇒ **需要 MP 门控矩阵 + 真机对拍验收** |
| ② 随机数消费序 | **触及（证据链层）** | 本卡修正「1 次 → 2 次」的**计数依据**（atlas 侧已是 2 次，patch_hex_audit 侧过期）；**未改任何同步语义结论**，但该计数是「视觉/音效禁止调用局内 RNG」的门控依据 ⇒ 需真机对拍确认行为面 |
| ③ 存档结构 | **触及** | `CellClass+0x134` 属地图单元格序列化块（进 `.SAV`）；P-2.1–P-2.3 的 NOP 保护改变该字段的写入语义 ⇒ 各端存档一致性受此约束，**严禁混端联机** |
| ④ 渲染像素等价性 | **未触及** | 本卡无任何渲染/像素改动；B1/B2 语义（FOG.SHP alpha 插值）仅在 G-04 判据条目中被引用 |

### [8] 交付物清单
| 类别 | 路径 | 规模 |
|---|---|---|
| **新文档（主交付）** | `docs/re/atlas_rev/R3_ai_hooks.md` | 532 行 / 70923 B |
| **机器可读断言** | `out/re_work/atlas_rev/R3/claims_R3.txt` | **63 条**（`audit_bytes.py` 63/63 OK） |
| 只读探针脚本 | `out/re_work/atlas_rev/R3/{probe_r3.py, probe_r3b.py, probe_r3c.py, dump_anchors.py}` | 4 件 |
| 门禁原文落盘 | `out/re_work/atlas_rev/R3/{gate1_verify_anchors.txt, gate2_audit_bytes.txt}` | 2 件 |
| 中间产物 | `out/re_work/atlas_rev/R3/{anchors.json, _part1.md}` | 2 件 |
| **补丁块** | 本文件 §1 | **10 块**（ERRATUM×3 / REPLACE_BLOCK×1 / INSERT_AFTER×4 / APPEND_SECTION×2；逐块动作见 §1 标题） |

### [9] 待裁决项
1. **E-3（`patch_hex_audit.md:282` 的「1 次 RNG」）是否授权就地订正？** 建议：授权 Lead 就地改 1 行（或由原执行方重开任务）。理由：该文是 P-1.x 跳板设计的直接依据，未订正将持续作为错误源（`asm_fix2_report.md` §3.9 域外清单未覆盖此处）。
2. **跨节 ERRATUM（PATCH-R3-07 §9.4 / PATCH-R3-08 §0.3）是否采纳？** 二者均在本卡**指定介入目标之外**，但属**工作树事实**级过期（`L4DirtyMode` 已落地、G-04 判据已变）。建议：采纳为 ERRATUM；若 Lead 认为与 R4 的 §0.3/§9.4 用词类补丁冲突，可整块丢弃（不影响其余 8 块）。
3. **PATCH-R3-10（§12.2 枚举序等价口径）是否保留？** 建议：保留（[推演] 部分标注来源为 `house_team_ai_update.md` §9.3，未逐字节复算 `0x006F936B/0x006F9C3C/` 三点）；并附 [待实测] 的 `UniqueID` 跨端一致性取证步骤。
4. **P-2 联机握手字段（`EnableGapProtection` / `EnableSpySatGate`）是否强制？** 建议：强制，并写进 §12.4-bis 与联机门控矩阵；否则「一端打补丁一端原版」无法在握手期拦截（必发 DESYNC）。
5. **G-04 判据替换后，既有验收脚本/清单（A-1 基线）是否同步改？** 「关闸后原字节恢复」判据作废 ⇒ 任何按该判据写的验收脚本会在补丁常驻时**误判**。建议：Lead 指派一次性清扫（`mp_release_safety_checklist.md` / `v160_acceptance*.md`）。
6. **是否把「补丁遥测字段命名契约」写入 §12.4 第 2 条？** 建议：增列一行（现网三计数符号 `s_fogLayerDraws / s_fogBlendStubHits / s_radarDarkenDriven` 与死字段 `g_telemetry.minimapFogPixels`），以便「独立遥测 = 生效证据」可机械判读。
