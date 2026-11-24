D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe  sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476  size 4825360 B  —— 实测与卡面钉死值一致（前缀 73201CC0，尾部 F67476），镜像有效，本审计成立。

# R17-AUDIT-R20 · 异族审计（R20 纠正值 26 的独立复核）

## 0 · 方法与边界

- **未复用、未 import 执行方 `work.py`**；独立实现在本目录 `audit.py`（PE 节表 + .rdata/.data 原始字节 + coverage.tsv 只读），另用一份 TypeScript 实现交叉核对，两者结论相同。
- 读入字节：`.rdata` raw 0x3E1000 / 200704 B + `.data` raw 0x412000 / 442368 B = **643072 B**；另做全镜像 ASCII 检索用于判定"名字是否在镜像中出现过"。
- RTTI 锚点：TypeDescriptor vftable = 0x7F9594，命中 (vfptr,0,\".?\") 三段式，按 4 字节对齐步进，命中后跳到字符串 NUL 再对齐。
- 输入只读：`gamemd.exe`、`COVERAGE/coverage.tsv`（sha256 C2EE063FD4F61F784585EF2ABCC4FF563FA09EC1B1F7F5079643076E359C744A，与 R20 报告一致；**本次未修改**）。未触碰 `coverage.tsv`、未触碰 `R17_R20_RECON/` 下任何文件。
- 未建进程、未调试、未启动 gamemd。未取得项：0。

## 1 · 复算结果（与 R20 并列）

| 项 | R20 | 本次独立复算 | 判 |
|---|---:|---:|---|
| in-binary RTTI 条目（.?AV 962 / .?AU 26） | 988 | 988（962/26） | 一致 |
| 唯一裸名 | 988 | 988 | 一致 |
| 模板实例 / 首段基名键 | 634 / 109 | 634 / 109 | 一致 |
| coverage 数据行 / 列宽异常 | 18498 / 0 | 18498 / 0 | 一致 |
| coverage token 不同数 | 429 | 429 | 一致 |
| token 出现次数（每行去重） | 3777 | 3777（原始 4812） | 一致 |
| BOTH（coverage token 口径） | 403 | 403（exact 209 + prefix 186 + underscore 6 + template_base 2） | 数值一致，**规则有问题见 A2** |
| COVERAGE_ONLY | 26 | 26 | 数值一致，**规则有问题见 A2** |
| RTTI_ONLY | 383 | 383 | 一致 |
| RTTI 条目侧被覆盖 | 605 = 209 直接 + 396 模板基名 | 605 = 209 + 396 | 一致 |

## 2 · A1 · BOTH(403) 与「RTTI 被覆盖 605」为何不等 —— **AGREE（是口径差，不是算错）**

两者的分母不同，且 605 内部还含一类"不是 coverage 名本身命中的覆盖"：

1. **分母不同**：BOTH 的分母是 coverage 侧 **429 个不同 token**；605 的分母是 in-binary 侧 **988 个 RTTI 条目**。两个桶本来就不同量纲（R20 已在 Q3 里说明了这一点）。
2. **一个 token 覆盖多个 RTTI 条目**：396 个 `?$VectorClass@…` / `?$DynamicVectorClass@…` 实例被 **2 个** coverage 名（`VectorClass`、`DynamicVectorClass`）整体覆盖 —— 2 个 token 换来 396 条覆盖，这是 403 ≠ 605 的**全部差额来源**（605 − 403 = 202，恰好是 396 − 194 的镜像，见下）。
3. **一个 token 覆盖零个 RTTI 条目（悬挂）**：194 条被"消解"的 token 里，186 条 MSVC 前缀条目的归一化键（如 `TechnoClass`）**早已由同一 token 集里的 `TechnoClass` 自身直接命中**，剥离不新增任何 RTTI 条目。所以 403 里那 194 个 token 对 605 的贡献是 0。

等价校验成立：209 + 186 + 6 + 2 = 403（coverage token 口径）；209 + 396 = 605（RTTI 条目口径）；988 − 605 = 383 两条口径都闭合。
**结论：403 vs 605 是口径差（分母不同 + 一对多 + 悬挂），不是算错。** R20 只写了一句"多对一会出现"，没写清"2 个 token → 396 条"和"194 条 token 对 RTTI 侧贡献为 0"，属说明不足，不是数值错误。

## 3 · A2 · 归一化是否过度消解 —— **DISAGREE（6/194 过度）**

抽查 22 条（≥20，覆盖全部 4 条规则、含被点名的 `AVRTacticalClass` 同族），完整逐条见 `norm_spotcheck.tsv`。

- **前缀链规则 14/14 合理**。逐个核过 186 条前缀条目**无一例是多重前缀叠加**：剥离长度恒为 3（`PAV`）或 2（`AV`）或 1（`V`），剥离后剩余串**不以 P/A/V 开头**，不存在 chain 叠加。关键反例也成立：`AVRTacticalClass` **未被前缀规则消解**（剥 `AV` 得 `RTacticalClass`，剥 `AVR` 不合法因 R∉{P,A,V}），它留在未解析里 —— 卡面点名的"AVRTacticalClass 式过度"在本轮**没有发生**。
- **模板首段规则 2/2 合理**：`VectorClass`/`DynamicVectorClass` 本身就是模板基名，in-binary 里也不存在同名独立 TD，等价命中成立。
- **下划线分段规则 6/6 过度**。这是本轮唯一的过度消解来源，且**不是个别案例，而是规则本身与证据相冲突**：

| 原 token | R20 消解为 | in-binary 实际存在的 TD | 判定 |
|---|---|---|---|
| `TacticalClass_DisplayClass` | `DisplayClass` | `TacticalClass@DisplayClass` @0x820048 | 过度 |
| `INIEntry_INIClass` | `INIClass` | `INIEntry@INIClass` | 过度 |
| `INISection_INIClass` | `INIClass` | `INISection@INIClass` | 过度 |
| `RTacticalClass_RadarClass` | `RadarClass` | `RTacticalClass@RadarClass` @0x839298 | 过度 |
| `SelectClass_StripClass_SidebarClass` | `SidebarClass` | `SelectClass@SidebarClass`、`StripClass@SidebarClass` | 过度 |
| `SBGadgetClass_SidebarClass` | `SidebarClass` | `SBGadgetClass@SidebarClass` | 过度 |

  理由（同一条，六例全中）：被丢弃的那一段**本身没有顶层 TD**，而"丢弃段@保留段"的复合 TD **确实存在**。也就是说 token 携带的信息在 in-binary 里**是能找到对应物的**，R20 却把它记成"只等于基名"——把派生类条目错误地并到基类（`DisplayClass`/`RadarClass`/`INIClass`/`SidebarClass` 各自都有**独立的**顶层表，见 coverage L2622/L7883/L6399 等行）。这正是卡面警告的方向：命中基名 ≠ 命中该 token 所指的类。

  **纠正后：**
  - **COVERAGE_ONLY = 26 + 6 = 32**
  - **BOTH = 403 − 6 = 397**（仅计 exact + prefix + template_base）
  - 若把 6 条按"复合名命中"正确计为 BOTH（token 唯一对应一个复合 TD，且全部 6 条 token 都能一对一映到上面的复合 TD，无歧义），则 **COVERAGE_ONLY = 26** 仍成立、BOTH = 403 仍成立，**但归一化列必须写 `X@Y` 而不是 `Y`**。两种口径选一，**不能像 R20 那样用"取段得基名"的方式拿到同一个数**——记账时必须声明是哪种。
  - 推荐记账口径（较稳）：**COVERAGE_ONLY = 32**，另立 6 条"复合名命中（X@Y）"。

## 4 · A3 · 剩余 26 条归因 —— **DISAGREE（(a) 与 (c) 系统性错配，(d) 5 条不成立）**

复核 **全部 26 条**（≥12），逐条见 `attrib_check.tsv`。要点：

1. **(c) 模板类 9 条 → 8 条错**。`VocClass / VoxClass / IonBlastClass / LaserDrawClass / SpotlightClass / RadarEventClass / PlanningTokenClass` 的 coverage 行 **name 列就写着 `Xxx::方法`**（如 `VocClass::PlayGlobal`、`SpotlightClass::SpotlightClass`），名字在镜像里只以 `?$VectorClass@PAVXxxClass@@` 的模板**实参**形式出现——"类名出现在模板实参里"推不出"这个类本身是模板"。`PBVAnimClass / PAVLaserDrawClass` 两条是 `T_DynamicVectorClass_…` 表行名残留，属容器，但也**不是"模板类"这个归因**。归类应为：**(h) 名字来源在镜像外 / 仅以容器实参出现**，不是 (c)。
2. **(a) 无独立 vtable 6 条 → 6 条都缺证据，其中 2 条明确错**。全镜像 ASCII 检索：`RulesClass` **出现 0 次**、`ScenarioClass` **0 次**（连字符串都没有），`InputManagerClass / GameOptionsClass / CDDriveManagerClass / ZBufferClass` 同样 0 次。"没有 TD"可以推出"无独立 vtable"，但**推不出"名字 0 次出现"**；这 6 条应是 **(f) 名字在镜像中不存在（来源为 in-binary 外知识库）**。coverage 行标 `[已证] YRpp/kb 地址名`，即名字来源在镜像外 —— R20 自己的前言也说不得据此判名字错，那么更不能反推"无 vtable"。
3. **(b) 3 条**：`TacticalClass`/`RTacticalClass`/`AVRTacticalClass` 确实对应 `TacticalClass@DisplayClass`、`RTacticalClass@RadarClass` 复合名，方向对；但同一条 (b) 规则把 `TacticalClass_DisplayClass` 判成了"等于 DisplayClass"（A2），**同一份证据在一个环节是"复合名命中"、在另一个环节是"只等于基名"，自相矛盾**。
4. **(d) 疑似命名差异 5 条 → 5 条都不该是"疑似"**。`MPBattleClass / MPMegawealthClass / MPSiegeClass / MPUnholyAllianceClass` 的 coverage 行 SEM **已经写死** `RTTI=0082DAA8→.?AVMultiplayerBattle@@` / `0082FCE8→.?AVMegawealth@@` / `0082FEC8→.?AVMultiplayerSiege@@` / `00830058→.?AVUnholyAlliance@@`，我逐个解码 BD 地址全部对得上，且 `Megawealth/MultiplayerSiege/UnholyAlliance/MultiplayerBattle` 都是顶层 RTTI 类（另有 `?$Initializer@V…@@@MultiplayerGameMode` 佐证同一族）。这是**已在 coverage 里证过的事实**，应归 **(g) 已由已验证 IID 解决**，留在 unresolved 里属重复计数。
   `MPGameModeClass` 更严重：coverage L6291/L6309 自己写着"行名类 MPGameModeClass 在本镜像 **无 RTTI 表（连字符串均不存在）**"，且该类 36 行全部见证在 `MultiplayerBattle/FreeForAll/MultiplayerSiege/UnholyAlliance` 的活表上 —— `MultiplayerGameMode` 就是这组多玩家模式的共同基类。把"1 个基类"记成 1 条未解析，同时又把它 4 个派生类各自记成 1 条，**同一个事实被计了 5 次**。
5. **(e) 3 条**：`MessageListClass`、`ABufferClass` 归 (e) 可接受；`MissionControlClass` 的 name 列是 `MissionClass::MissionControlClass`，也可能是成员函数名，(e) 保守但正确。

## 5 · A4 · 「93.94% 可在 in-binary 定位」—— **DISAGREE（会误导，须改措辞）**

三处会误导：

1. **分母错位**：93.94% = 403/429 是**按不同 token 计**；按 token 出现次数（每行去重 3777 次）计，被"消解"的 194 条对 RTTI 侧的**新增覆盖为 0**（全落在 209 个精确命中的键上）。说"93.94% 的 coverage 类名可在 in-binary 定位"，读者会理解为"这些类名在镜像里找到了类"，实际其中 **186 条只是把前缀剥掉后命中了另一个 token 早已命中的类**。
2. **把"命中基类"说成"定位"**：6 条下划线条目命中的是基名，而 token 指的是派生复合类（见 A2）。
3. **前提未写**：in-binary RTTI 只能覆盖"有 RTTI 的类"；本镜像 `RulesClass/ScenarioClass` **连字符串都不存在**，这类名字无论多精确都永远不可能被 in-binary 定位。93.94% 天然会把这一点掩盖成"剩下的 6.06% 才需要解释"。

**应改措辞**：
> 429 个 coverage 类名 token 中，**403（93.94%）在 in-binary RTTI 中存在同名或可解释的对应物**：其中 **209 个与 RTTI 裸名逐字相等**，186 个仅在前缀剥离后命中**已被其他 token 覆盖的同一个类**（不新增任何定位），2 个是容器模板基名。此比例**不表示**这些类名在镜像中被独立验证——只表示 in-binary RTTI 中不出现"完全找不到对应物"的情况。且该口径**只适用于有 RTTI 的类**：本镜像确有一类名字（如 `RulesClass`、`ScenarioClass`）**在整个镜像中零出现**，其名字来源在镜像之外，任何 in-binary 方法都无法定位它们。

## 6 · 必改项（9 条）

| # | 必改 | 依据 |
|---|---|---|
| 1 | 下划线分段规则必须改为"复合名命中（X@Y）"，不得取段等于基名 | 6/6 过度，A2 表 |
| 2 | COVERAGE_ONLY 若沿用现有规则必须写成 **32** 而非 26；若改用复合名命中口径，须显式声明 | A2 |
| 3 | (c) 模板类 9 条中 ≥7 条改写为"仅以容器模板实参/表行名出现，非模板类" | A3-1 |
| 4 | (a) 无独立 vtable 6 条改写为"名字在镜像中零出现（来源 in-binary 外）" | A3-2，全镜像 0 次 |
| 5 | (d) 疑似 5 条升级为"已由 coverage 内已验证 IID 解决"，并只保留 1 条（共同基类 MPGameModeClass） | A3-4 |
| 6 | A4 那句 93.94% 按 §5 措辞重写，并补"只覆盖有 RTTI 的类"前提 | A4 |
| 7 | Q3 口径说明补上"2 个 token → 396 条覆盖"与"194 条 token 对 RTTI 侧贡献 0" | A1 |
| 8 | (b) 与 A2 的下划线规则自相矛盾须消除（同一复合证据不能既算命中又算取段） | A3-3 |
| 9 | `normalization.tsv` 的 20 条抽样全部取自"合理"一侧（exact/prefix/template/underscore 各若干），无一条覆盖真正有争议的 `TacticalClass_DisplayClass` 类——抽样设计有偏，需补争议样本 | normalization.tsv |

## 7 · 附：一处 R20 未提的口径风险（不计入必改，供 Lead 判）

R20 的 `work.py` 在 RTTI 侧用 `cov_keys`（**所有 token 的候选键并集**）去判定覆盖，这与 `resolve()`（逐 token 短路）不是同一套规则。我实测：该宽口径**实际未多算**（悬挂键只有 `VectorClass`/`DynamicVectorClass` 2 个，且二者恰是真实模板基名），但两套规则并存是**被动正确**而非设计正确；若将来 token 集变化，宽口径会凭空造出"覆盖"（例如 `PAVFooClass` 存在时会覆盖一个并不存在的 `FooClass` TD）。建议把 RTTI 侧也改成逐 token 的 `resolve()` 结果再统计。
