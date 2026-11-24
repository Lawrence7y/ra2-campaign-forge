D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe  sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476  （实测，前缀 73201CC0 匹配 → 有效）

# R17-AUDIT-R22 · 异族审计：对 R17_R22_RING2_CORROB 的独立复核

- 审计产物只写本目录；未改 `coverage.tsv`，未改 `R17_R22_RING2_CORROB\` 下任何文件（见 A5）。
- 独立实现：`audit.py`（本目录，未 import / 未调用执行方 `work.py`；PE 解析、TD/COL 扫描、vtable 切分、类键索引、行筛选全部自写）。
- 读取范围：`.rdata`(200,704 B) + `.data`(442,368 B) = **643,072 B** 做 TD 扫描；槽值只读 `.text`(4,060,045 B 区间)；`coverage.tsv` 只读一次（4,147,334 B）。
- 未建进程、未调试、未启动 gamemd。

## A1 · 四个数是否成立 —— **成立（逐数复现）**

| 量 | 执行方 | 本审计独立复算 | 结论 |
|---|---:|---:|---|
| [已证] 行总数 | 1,654 | **1,654** | 一致 |
| 类名可 in-binary 定位 | 1,094 | **1,094** | 一致 |
| entry 与定位类同一 vtable 闭合 | 433 | **433** | 一致 |
| entry 出现在非该类 vtable（“矛盾信号”） | 141 | **141** | 一致 |
| 其中仅非该类命中、未闭合 | 64 | **64** | 一致 |
| 精确裸名变体（敏感性对照） | 1,085 / 397 / 168 / 91 | **1,085 / 397 / 168 / 91** | 一致 |

我的口径（全部显式实现于 `audit.py`）：
- 行筛选：`coverage.tsv` 第 5 列（表头 `entry,subsystem,name,one_line_semantics,grade,evidence_path,n_sources,conflict`）精确等于 `[已证]`；数据行 18,498，列宽异常 0。
- 类名：第 4 列 `one_line_semantics` 上 `(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*Class(?![A-Za-z0-9_])`，逐行去重。
- MSVC 前缀链 PAV/AV/PA/P/A（`PAV` 是 `?AV` 的剥离残留），逐级剥离取第一个命中索引的候选。
- 类键：裸 TD 名；主口径加 `?$X@…` 模板基名别名（键 1,062，多表类 111）。
- 闭合：entry 数值 ∈ 该行定位类所有 vtable 的连续 `.text` 槽值。矛盾：entry ∈ 任一 vtable 槽值且该 vtable 不属于该行定位类。

数可信。但这四个数“能说什么”差别极大（A2/A3）。执行方对 433 的措辞已比“可升级”克制，但 **对 141 完全没有做继承分析**——这是本卡的核心缺陷。

## A2 · 「矛盾信号 141」的语义是否被正确限定 —— **没有；执行方把继承当成了矛盾**（必改项 1）

执行方 `work.py` 的矛盾判据只有一句：`other_hit = any(h["vtable"] not in own_bases for h in hits)` —— 只要 entry 出现在“任何不属于本行定位类”的 vtable 就算矛盾，**没有任何基类/派生类关系判断**。MSVC 单继承下基类方法出现在所有派生类 vtable 里是常态，所以 141 里绝大部分是继承的算术结果。

### 区分方法（本审计新增，`audit.py` 的 `parents()` / `chain_to()` / `related()`）

在同一颗 vtable 槽值空间里做**槽位单调性检验**，不依赖外部类图：

> 对 vtable C 与候选表 P（|P| ≥ 3 且 |P| ≤ |C|+2）：取 C 与 P 的公共槽值（≥3 个），若这些值在 P 中的槽号 j 都**不小于**在 C 中的槽号 i（允许 ≤1 个例外、比例 ≥0.9），则 P 是 C 的**基类表**。
> 依据：MSVC 单继承下派生类 override 只会就地替换/保留基类槽，新增虚函数只能追加在尾部 —— 基类方法**绝不会被挪到比基类表更靠前的槽位**。

关系沿派生链可传递（上溯 ≤6 层），**双向**（P 是 C 的基类，或 C 是 P 的基类）都算“继承可解释”。

用已知真类验证该判据：

| 派生 → 基 | 共同槽 | 单调成立 | 违背 |
|---|---:|---:|---:|
| InfantryClass(343) → FootClass(341) | 270 | 270 | 0 |
| FootClass(341) → TechnoClass(309) | 222 | 219 | 3 |
| TechnoClass(309) → RadioClass(161) | 108 | 104 | 2 |
| RadioClass(161) → MissionClass(157) | 150 | 148 | 2 |
| ObjectClass(122) → AbstractClass(24) | 15 | 12 | 3 |

旁证：Infantry(343) 与 Foot(341) 共有 270 个相同槽值 —— 这正是“矛盾”的来源。

### 重算（141 行，逐行见 `inherit_vs_mismatch.tsv`）

| 分类 | 条数 | 说明 |
|---|---:|---|
| **继承可解释** | **81** | 非该类命中全部与该行定位类成基类/派生类关系（含跨 2+ 层的传递基类，如 AbstractClass → 全部派生类） |
| 同址复用（非继承、非错配） | **56** | 全部是 `?$TClassFactory@V*` 的 IClassFactory 模板表：同一手写 `TClassFactory<T>` 的槽机器码在 56 张不同实例 vtable 里复用同一地址。与行名类无继承关系，但是模板实例码复用的已知现象 |
| **真正可疑** | **4** | 见下表 |
| （部分继承可解释，判在可疑侧） | 1 | `0055AB40 LocomotionClass::GetSizeMax`：12 个 Locomotion 派生类共用同一 slot7 实现，另有 5 类该槽被 override。属**派生类覆盖**，最可能可解释，但判据只对其中 5 个成立，故保守落在可疑侧 |

结论：**141 ≙ 81 纯继承 + 56 模板码复用 + 4 真正可疑**（严格上限含 `0055AB40` 为 5）。141 **不是** 141 条问题。

4 条真正可疑（均未闭合：entry 只出现在一个别类 vtable，且行类自身 vtable 不含此 entry）：

| entry | 行名类 | 命中的别类 | 语义原文（截断） | 读法 |
|---|---|---|---|---|
| `004A88C0` | MapClass::ClearLayers（抽取到 LayerClass） | DisplayClass `0x7e6114` slot7 | 遍历[5]LayerClass逐层调虚槽+0x0C清空 | MapClass 函数操作 `LayerClass` 局部/参数，抽取器把 LayerClass 当成所属类 → **行名类口径错位** |
| `006539D0` | RTacticalClass_RadarClass::slot31 | `RTacticalClass@RadarClass` `0x7f02bc` slot31 | 虚表槽 31(+0x7C) 雷达点击派发 | **该行自证**：entry 正在 `RTacticalClass@RadarClass` 的 slot31。`@`→`_` 替换导致 in-binary 名假不等 → 字符串判据盲区 |
| `00721A50` | TiberiumClass::slot25（抽取到 CCINIClass） | TiberiumClass `0x7f5728` slot25 | ore-type rule loader…CCINIClass::ReadInteger at 0x721B0C | entry 实际就在 TiberiumClass slot25；抽取器把 **callee 类**当成所属类 |
| `0055AB40` | LocomotionClass::GetSizeMax | DropPod/Fly/Hover/Jumpjet/Mech/Rocket/Ship/Teleport/Tunnel/Walk 共 10 表 slot7 | ④ 活表槽位见证：DriveLocomotionClass::slot7 | 语义已明说归属 DriveLocomotionClass；其余派生类共用同一 slot7 → **派生覆盖** |

4 条里 3 条是**行名类抽取口径**问题（抽取器取到了语义里的别的类名），不是“entry 挂错类”。真正需要人工看一眼的只有 `004A88C0`（该算 LayerClass 还是 MapClass）。

## A3 · 433 能说什么 / 不能说什么

**能说**：
1. 433 行的 entry 地址与“该行语义所提类”的某张 RTTI vtable 的某槽值**数值相同** —— 存在一条独立于 YRpp 的二进制内地址锚，可用于交叉核对“该 entry 是某类虚函数”。
2. 433 是 [已证] 1,654 中可定位 1,094 的子集，覆盖约 40%；其中 **393 行**与已有独立审计链并存（但见 A4 对分类器的限制）。

**不能说**：
1. 不能说“entry 是**该**类的成员”。地址相等 ≠ 成员归属：未做槽号一致性、未做 COL 二次校验、未做装表点校验时，同址复用（56 例 `TClassFactory` 即铁证）、继承、虚覆盖都会造成地址相等。
2. 不能说“433 已把类身份证到 ② 水准”。② 的准入是 D-51 的“有独立审计链”，不是“地址在表里”；433 里 **40 行的既有 ② 证据按执行方标签属“仅 YRpp 代理”**，按 D-51 不进 ②。
3. 不能说“433 行 grade 可升”。measurement ≠ 改判。执行方 Q5#3 已写“不得被引用为「② 已升级」”，这条正确。
4. 不能把 433 当“独立审计链”。in-binary RTTI 索引与既有审计链是否同源未审，二者可能共享同一份 TD/COL 解析代码。

**执行方限制段不足（必改项 2）**：Q5 只有 2 条（无 RTTI 类不覆盖 / 地址相等≠成员），缺：
- 未声明“entry 在别类 vtable = 可能继承”，反在 Q3 把 141 写成“矛盾信号”；
- 未声明同一 entry 在多张 vtable 中出现是常态（141 条矛盾行里 77 条同时闭合，即双归属常见）；
- 未声明“闭合”未做**槽号一致性**校验：行文若写了 slotN，未与 vtable 实测槽号比对（`006539D0` 恰是该缺口暴露的例子）。

**建议补足措辞（可替换 Q3 脚注与 Q5）**：

> - “闭合 433”仅表示**地址锚定成立**：该行 entry 数值等于其语义所提类的一张 RTTI vtable 的某槽值。它**不**证明成员归属，**不**构成 ②，**不**支持任何 grade 变更。
> - 同一 entry 常同时出现在基类与派生类 vtable 中（MSVC 单继承正常形态）。本次把“entry 出现在非本行类 vtable”的 141 行按基类/派生类关系重分：**81 行纯继承**、**56 行 STL `TClassFactory` 模板实例码复用**、**4 行真正可疑**（3 行为行名类抽取口径错位，1 行待人工确认）。141 **不等于** 141 条问题。
> - 闭合未做槽号一致性校验；行文标注 slotN 的行须另测。

## A4 · 40 条「仅 YRpp 代理」是否可靠 —— **可复现，但判据是兜底桶；抽查 8 条 4 条名实不符**（必改项 3）

判据在脚本里**确实显式实现**（`work.py` 的 `AUDIT_CHAIN_RE` / `YRPP_PROXY_RE` / `evidence_type()`），但逻辑是**三值压成两值**：

```python
if AUDIT_CHAIN_RE.search(sem): return "有独立审计链"
if YRPP_PROXY_RE.search(sem):  return "仅 YRpp 代理"
return "仅 YRpp 代理"          # 兜底
```

我用同一组正则独立复现 433 行：
- `AUDIT_CHAIN_RE` 命中 **339**，未命中 **94**；
- 未命中的 94 里 `YRPP_PROXY_RE` 命中 **0** 条 —— 全部走兜底；
- 落在“仅 YRpp 代理”的是 **40**；另 54 条是两条正则**同时命中**，被优先级覆盖成“有独立审计链”。

即：“仅 YRpp 代理”实际收的是“**既无审计链关键词、也无 YRpp 措辞**”的残余桶，**没有一个真的命中 YRpp 正则**。证据见 `_a4_evidence.json`（逐行 `audit_hit/yrpp_hit/mine`，可用 `audit.py` 复跑）。

### 8 条抽查

| # | entry | 类 | 语义原文 | 标签 | 与语义相符？ |
|---|---|---|---|---|---|
| 1 | `00414A80` | AircraftClass | Mission handler v[v138]: Hunt (AircraftClass) | 仅 YRpp 代理 | 名不副实（无 YRpp 字样、无审计链词） |
| 2 | `0041FB10` | AITriggerTypeClass | …LoadFromINI……③b① 三路分派 + ③b② -1 哨兵可证伪 | 仅 YRpp 代理 | **错**：含 `可证伪`/`③b①`/`③b②`+具体地址，属独立链语义，只是 `③b` 不在正则里 |
| 3 | `0043DA80` | BuildingClass | BuildingClass DrawBehind/DrawExtras helper (sets NeedsRedraw) | 仅 YRpp 代理 | 名不副实（无 YRpp 字样） |
| 4 | `0044C980` | BuildingClass | Mission handler v[v148]: Missile (BuildingClass) | 仅 YRpp 代理 | 名不副实（同 #1 型） |
| 5 | `00471500` | CampaignScoreClass | 标量删除析构子：写 vptr 0x7e4aac，test al&1→operator delete(0x7c8b3d) | 仅 YRpp 代理 | **错**：写明 `写 vptr`，正是 ④ 活表装配语义 |
| 6 | `004D27C0` | FoggedObjectClass | FoggedObjectClass::GetSize=0x78 | 仅 YRpp 代理 | 名不副实（最小信息行） |
| 7 | `004DF320` | AircraftClass | QueueMission wrapper…Ring3 reaches Aircraft override 0041BA90…（nsrc=4） | 仅 YRpp 代理 | **错**：含 Ring3 链、地址、flip 条件 |
| 8 | `005656D0` | MapClass | …双闸+哨兵可证伪，③b②（nsrc=1，conflict=1） | 仅 YRpp 代理 | **错**：与 #2 同型 |

抽查结论：**8/8 语义原文都没有“YRpp 代理”措辞**；其中 **4/8**（#2 #5 #7 #8）带独立链语义（`写 vptr` / `可证伪` / `③b` / Ring3 链），被兜底错分进“仅 YRpp 代理”。40 在“可复现”意义上为真，在“语义相符”意义上偏差，且整桶 0 条真正命中 YRpp 正则。

**D-51 现状描述（只描述，不建议改判）**：D-51 原文口径为「② 只收**有独立审计链**的行（entry 能在 `NAMED_PUSH_AUDIT*/verdict.tsv` 找到且类身份有审计记录），不接受仅靠 YRpp 知识库代理的 ②」（见 `_cards/R16-AUDIT-D1-FINAL.md:28-31`、`_cards/R17-R22-RING2-CORROB.md:5`）。按此口径，这 40 行**现状是“不进 ②”**，本卡测量与该现状一致、执行方也没有改。需要指出：其中至少 4 条语义看起来带独立链特征（抽查 #2 #5 #7 #8）；是否属于“审计链在别处、语义未写产物名”，本卡不作判定，**也不建议改判**。

## A5 · 是否引入 grade 变更 —— **未引入（通过）**

- `coverage.tsv`：mtime `2026-11-21T04:56:21Z`（本地 2026/11/21 12:56:21），size 4,147,334 B；本次读取前后 sha256 均为 `C2EE063FD4F61F784585EF2ABCC4FF563FA09EC1B1F7F5079643076E359C744A`，**与执行方 REPORT 第 4 行所记一致**。
- 执行目录 7 个文件 mtime 全在 `2026-11-21T09:35:05Z`–`09:35:16Z`，晚于 `coverage.tsv` 的 `04:56:21Z` → 执行期间未回写 coverage。
- REPORT 全文“升级/可变/改判/可升”只出现一次，且是否定句：Q5#3「本卡**不建议任何 grade 变更**，也不得被引用为「② 已升级」」。**没有**“② 已升级 / grade 可变”这类结论。`corroborated.tsv` 只有 5 列（entry/class_name/vtable/slot/evidence_type），无 grade 列。

## 必改项（4 条）

1. **A2 重写**（严重）：Q3「矛盾信号 141」与矛盾判据把**继承**当矛盾。须改为中性表述“entry 跨类出现”，并按 **继承可解释 81 / 同址复用（TClassFactory 模板码）56 / 真正可疑 4（上限 5）** 三分类，不得让下游读成“141 行有问题”。
2. **A3 措辞补足**：加入上述三条补足措辞。现 Q5 只有 2 条限制，不足以挡住“433 可升级”误读。
3. **A4 标签诚实性**：`仅 YRpp 代理` 实为兜底残余桶（`YRPP_PROXY_RE` 命中 0 条），且会把 54 条双命中行按优先级算进“有独立审计链”。至少写清“40 = 未命中独立链关键词且未命中 YRpp 措辞的兜底”，或三桶（审计链 / YRpp 显式 / 兜底）。**不涉及改判**。
4. **A1 口径敏感性入主表**：主口径（含 `?$X@` 模板基名别名）与精确裸名变体相差 9 行可定位、36 行闭合、27 行矛盾（1,094/433/141 vs 1,085/397/168）。现仅在脚注提两数，易被读成 433 不敏感。

## 未取得项

无。四个数、A2/A4 全量、A5 的 mtime/sha256 均实测取得。

## 产物

- `VERDICT.md`（本文件）
- `inherit_vs_mismatch.tsv`（141 行逐行：entry / 行名类 / 其他类 / 继承可解释? / 判定 / own_closure / n_vtable_hits）
- `audit.py`（独立实现，可复跑）
- `_audit_result.json` / `_a4_evidence.json` / `_a5.json`（中间结果）
