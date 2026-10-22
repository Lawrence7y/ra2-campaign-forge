# RE-ATLAS · 进度与覆盖率 (STATUS)

更新：2026-10-22 **R-028 核验**（独立门禁 **49/49** + 异族盲验；**推翻 3 条**：TypeClass 字段表 **613→644 键**（31 个 `ReadDouble` 字段整批丢失）／`MovementZone` 属 **rulesmd** 非 artmd／`INI_Art` 依据改写入点（BSS 直读无效）；**新增 1 条**：`ReadDouble` 静默吃掉 `%`（`50%`→`0.5`，`0x7E3808`=0.01））

更新（上一轮）：2026-10-22 R-021 核验（§13 机器门禁 **34/34** + 异族盲验；**推翻 3 条**：`Read_File` 有分离冷块真范围到 `0x668FA3`／29 次调用 26 个 loader（非 28）／MP 节被读；**纠 H-014** 第三难度键是 `Difficult` 非 `Hard`；**自纠一处方向反转**——单机读的是 `AdvancedCommandBar`，联机才读 MP 节）

## 一句话

种子已建、基线已钉：语料 1,304 个命名点全部过段表校验，323 条 claims 全量复算
**323/323 PASS**，虚表 **20/20 与 ATLAS 一致**，**翻案 2 条实例尺寸并已获异族双通道核验**。
新解出**虚表槽位契约**（槽 11 = 类型 ID / 槽 12 = 尺寸，**69 类零冲突**，
与引擎名字表 74 项及 YRpp 三方一致）。
函数命名覆盖率基线 **3.62%**（551 / 15,224 个已发现入口）。

## 量化面板

| 指标 | 值 | 口径 |
|:---|---:|:---|
| 目标二进制 sha256 | `73201cc0…f67476` | `ra2youli/gamemd.exe` |
| 语料文件索引 | 256 | `docs/re` + `atlas_rev` + `goal3_audit` |
| 语料内 distinct VA 总数 | 23,174 | 含 RVA/噪声，未过滤 |
| **段表校验后的命名点** | **1,304** | .text 内，去 RVA 与反汇编噪声 |
| 其中唯一名 | 923 | |
| 冲突（REAL/ALIAS/NOISE） | 5 / 400 / 14 | 5 条已全裁定 |
| claims 字节断言复算 | **323 / 323 PASS** | `evidence/claims_verify.txt` |
| RTTI 类 | 988（954 有虚表） | `evidence/rtti/` |
| 虚表 vs ATLAS 交叉 | **20 一致 / 0 不一致 / 14 口径不适用** | `evidence/vtable_xcheck.txt` |
| 实例尺寸复算 | 12 OK / **2 翻案（已核验）** / 2 口径失效 | `evidence/size_xcheck.txt` |
| **类 ID + 尺寸双命中** | **69 类，ID 冲突 0** | `evidence/class_ids.txt` |
| **`AbstractType` 名字表** | **74 项，`0x816EE0`，值域 0x00..0x49 无空穴** | 直读 |
| 引擎表 ID 未对应类 | **5 项**（哨兵/抽象桩/`.rdata` 无此类） | `evidence/class_ids.txt` 尾部 |
| 递归遍历发现函数入口 | **15,224** | `evidence/fn_walk.txt` |
| 已命名的入口 | 551（**3.62%**） | 保守下界 |
| 线性扫描覆盖率（反面样本） | 11.1% | 单次 `md.disasm` 在 `0x46F5A0` 停（只覆盖 9%），见 G-23 |
| **带审计重同步的全段扫描** | **1,389,579 条 / 100%** | `tools/text_sweep.py`；与纯 `E8` 字节扫描逐址对账 |

## 子系统覆盖

| 子系统 | 状态 | 说明 |
|:---|:---|:---|
| R0 盘点（索引/种子/冲突） | ✅ 完成 | 本轮 |
| R1 全局骨架（PE/RTTI/虚表/覆盖率） | ✅ 完成 | 本轮 |
| R2-1 地图 / 触发器 / 脚本 / TaskForce / TeamClass | 🟢 **派发层 + 类尺寸/前缀布局/对象字段完成** | Action 145 / Team 65 / Event 两级 49 槽全解析；触发器族 8 类**ID+尺寸双命中**；`AbstractClass` 多继承 4 vptr；`TEventClass` 三接口字段 + `Save` 四项；`AbstractTypeClass` 字段边界实测。见 `kb/10_map_triggers.md`、`kb/11_class_layouts.md`、`kb/20_vtable_contract.md`、`kb/21_swizzle_and_object_fields.md`。余：`ScriptType` 大块结构、`+0x28`/`+0x30` 接口对象类名（L-21） |
| R2-2 INI 与规则加载 | ✅ **结题（R-029）**：核心闭环 + 类型层已解 + §20 总览 + **§12.7 键索引定稿（R-031）** | **R-015…028**：单继承布局（**撤回** R-015 的"多继承 + `VectorClass` 基类"）；`INISection`=`0x44`/`INIEntry`=`0x28`/`List<T>`=`0x1C`；**节查找 = CRC32 排序数组+二分，大小写敏感，未命中返哨兵 `0xB7882C`**；**`ReadBool` 只认首字符、`ReadInteger` 尾 `h` 走十六进制**；**`RulesClass` 尺寸 `0x18C0`**（分配点+字段上界+对齐三重吻合），构造器 `0x665650`；**`[MultiplayerDialogSettings]` 27 键字段表**；**载入后 18 字段镜像到独立全局**（`ShortGame`→`0x00A8B262` 50 处）；**全引擎键索引 2,426 调用点**（R-019 旧值 478/473/427 **作废**，根因=capstone 单次 `md.disasm` 静默截断，见 G-23；**键列口径已由 R-031 换成 ABI 键槽：2,209 站点/2,023 键/217 非字面量/137 多读**，M1 旧值 2,305/1,893/164/121 只作"范围内有字面量"计数，见 §12.7）；**★ 含 `%` 的字面量键 = 0**（21 个 `%` 串全是运行期拼键模板，被 M1 误记为键）；**`RulesClass` 节表** 31 项 + 载入顺序；**`[General]` 268 标量字段**（279 键，12 个列表型）；**`[AudioVisual]` 151/152**；**其余 10 个小节字段全解**；**逐 loader 键清单 651 键**（R-022 旧值 306 **作废**）；**R-028 新增：`TypeClass` 继承链 7 层、613 键全解、0 未定** —— `AbstractType(1) → ObjectType(20) → TechnoType(252) → {Infantry(33), Unit(27), Aircraft(10), Building(270)}`，尺寸 0xED0/0xE78/0xE10/0x1798；**四个派生 loader 同时读 rulesmd 与 artmd**（`INI_Art`=`0x887180`，COL 解出 `.?AVCCINIClass@@`），Building 有 **151/270 键属 artmd**；25 键走 cdecl 枚举包装器；构造器链独立核对 **269/269 全归因**（含 132 个指针环清零）。见 `kb/30_ini_subsystem.md` §0–§20；**§20 结题总览 + G 系坑点汇总（R-029）**。余（转按需补充，不排新轮）：其余 15 个 TypeClass（A-40）、动画子结构字段名（A-41）、枚举值表（A-42）；**核验欠账 R-018…R-028 共 8 条 HANDOFF 仍属 P0**（§20.3；R-017 已 R-030 闭：
异族盲验 18C/0R/1U + 机器门禁 `verify_r017_claims.py` 53/53，
推翻 `0x100` 子句 ⇒ `Key=0x100` 实为 0，`$100`/`100h` 才是 256；**R-018/R-019 已 R-031 闭**：
异族 GLM 盲验 21C/9R/2U + 键槽双算 17/17，H-013 原地追加已核验） |
| R2-4 战斗 / 武器 / 弹道 | ⬜ 未开始 | 语料 `weapons_damage_production.md`（449 VA）可作起点 |
| R2-5 AI 决策 | ⬜ 未开始 | 语料 `house_team_ai_update.md` |
| R2-6 超级武器 | ⬜ 未开始 | 语料 `superweapon_re.md`（520 VA） |
| R2-7 存档与读档 | ⬜ 未开始 | 语料 `savegame_block_manifest.md`（525 VA） |
| R2-8 UI 与菜单 | ⬜ 未开始 | 语料 `sidebar_selection_ui.md`、`ui_command_dispatch_deep_dive.md` |
| R2-9 网络与联机同步 | ⬜ 未开始（只读） | 语料 `net_sync_checksum.md`（444 VA） |
| R3 其余模块 | ⬜ 未开始 | |

## 本轮新增量化（R-012）

| 指标 | 值 |
|:---|---:|
| **虚表槽位契约** | 槽 11 = `WhatAmI()`（类型 ID）/ 槽 12 = `GetSize()`，**69 类零冲突** |
| **`AbstractType` 类型 ID** | 74 项全表（`0x816EE0`），值域 `0x00..0x49` 无空穴 |
| 三方一致 | 槽 11 字节 ↔ 引擎名字表 ↔ YRpp `AbstractType` |
| 触发器族双槽命中 | **8/8**（Script/Tag/Trigger/TEvent/TAction/Team/TaskForce/ScriptType） |
| `TEventClass` 接口字段 | **3 个**（`+0x28`/`+0x30`/`+0x54`），前轮漏记 `+0x28` |
| `TEventClass::Save` 序列化项 | **4 项**（基类 + `+0x28` + `+0x2C` + `+0x30` + `+0x34`），前轮记 3 项 |
| 关闭悬项 | **3**（L-6 部分闭合 / L-14 / L-16） |
| 新开悬项 | **6**（L-17 / L-19 / L-20 / L-21 / L-22 / L-23） |
| 撤回 | **1**（`0xB0C110` 字段注册表 → `SwizzleManagerClass::Instance`，累计 **4**） |
| **核验升级** | **2**（G-1 `TeamTypeClass`=248 / G-2 `AITriggerTypeClass`=272 → **已核验**） |
| **R-016 八条异族复核** | 确认 **3** / 推翻 **0** / 无法核 **0**（有效票仅 2 个模型家族，见 `kb/30` §7.2 边界） |
| 异族核验通道 | GLM 5.3 + DeepSeek v4.1-flash，两路 `CONFIRMED` |
| 交接件 | **9 条**（H-001…H-009；R-014 新增 H-009 虚表槽位三易错点） |
| KB 正文 | **6 篇**（`00` / `10` / `11` / `20` / `21` / `22`） |
| 可复跑工具 | **9 个**（verify_claims / dump_trigger_tables / xcheck_sizes / dump_class_layouts / dump_class_ids / dump_vtable_slots / disas / extract_symbols / classify_conflicts） |

### 本轮两次方法教训

1. **typed `ask` 的协议假设错误**：`agent().ask<T>` 要求模型主动调 `submit_result`，
   两族模型都不这么做（GLM settled 82.5k token 却零产出）。改用**纯文本四行约定 + 脚本侧正则**，
   首次即成。已记为纪律 #6。
2. **capstone 的 `op_str` 带逗号后空格**（`"eax, 0x30"`），
   用 `startswith("eax,0x")` 判断会**全部漏检**——当场表现为"0 类命中"。
   已固化进 `dump_class_ids.py` 的 `immediate()`，并在 docstring 写明。
   这是"工具静默返回空集"的典型，需配**肯定对照**（同文件内全类命中即为对照）。
   R-013 又发现同源第二坑：capstone 把**小立即数渲染成十进制**（`mov eax, 1` 而非 `0x01`），
   字符串判据因此漏掉 id `0x00..0x09` 的 10 个核心类。已改读 `operands[i].imm`。

## 禁区遵守记录

**R-031（2026-10-22，在飞轮）**：
- `tasklist` 查无 `gamemd` / `ra2loader`。
- 子代理 1 个（GLM 5.3，异族盲验），纯只读字节、写面=其报告一份；运行中。
- 本地只读 exe；未启动游戏/loader、未写 `ra2youli`、未跑 trip、未编译。
- 未修改 `lead/`、`docs/re/`、`ra2render/`、根 `tools/`。
- GOAL-3T 台账尾部（§356 RC-4 触发路径定案）：禁区内容，仅做冲突排查读取，零交集。
- 本轮发现全在 §12 通用索引内，**不涉 RC-4 地址/对象**。

**R-021 核验（2026-10-22 19:xx–20:xx）**：
- `tasklist` 查无 `gamemd` / `ra2loader` / `game.exe`。
- 读 GOAL-3T 台账尾部（§370 RC4_RECONCILE），确认无未闭合真机时段；
  该线全在 §3 禁区内，本轮仅遵守，未写任何因果/触发/修复意见。
- **派 1 个子代理**（general-purpose，异族盲验；`ra2-re-analyst` 绑 Step
  已被规则禁用，改用通用通道）。任务书纯只读字节推导，写面=其报告一份。
  **该盲验抓出我自己的方向反转**（见 LEDGER §5b / G-40），已修。
- 本地只读 exe；未启动游戏/loader、未写 `ra2youli`、未跑 trip、未编译。
- 未修改 `lead/`、`docs/re/`、`ra2render/`、根 `tools/`。
- **`0xA8B238`（`GameMode`）与禁区全局 `0xA8B23C` 相邻但不同址**，
  本轮只按普通全局引用，未做任何 RC-4 关联推断。

**R-031 定稿（2026-10-22 18:xx–19:xx）**：
- `tasklist` 查无 `gamemd` / `ra2loader` / `game.exe` ⇒ 可做完整离线分析。
- 读 GOAL-3T 台账尾部（§368 Mimosa deep 档）+ 三目标台账尾部（L3 高负载），
  两条线均与本轮零交集；无「真机时段开始」未闭合标记。
- 未派子代理：异族 GLM 盲验报告已在盘，本地键槽双算即可闭环，
  不重复占用通道。
- 本地只读 exe；未启动游戏/loader、未写 `ra2youli`、未跑 trip、未编译、未改注册表。
- 未修改 `lead/`、`docs/re/`、`ra2render/`、根 `tools/`、`.gitignore`。
- 新增 6 个工具 + 1 份 evidence，全部在 `re_atlas/`。
- 未触碰 §3 禁区任何函数/全局；未写 RC-4 因果、触发、修复意见。
- `dump_typeclass_family.py` 待归属改动仍未触碰（见 R-029 记录）。

**R-030（2026-10-22）**：
- `tasklist` 查无 `gamemd` / `ra2loader`。
- 派 1 个子代理（千问 qfmodel，异族核验），任务书为纯只读字节推导，写入面=仅其证据文件一份。
- 本地只读 exe；未启动游戏/loader、未写 `ra2youli`、未跑 trip、未编译、未改注册表。
- 未修改 `lead/`、`docs/re/`、`ra2render/`、`tools/`（`re_atlas/tools/` 属本线）。
- 读 GOAL-3T 台账尾部（§351）：其线在 RC-4 触发点（禁区），与本轮零交集。
- `dump_typeclass_family.py` 待归属改动仍未触碰（见 R-029 记录）。

**R-029（2026-10-22）**：
- `tasklist` 查无 `gamemd` / `ra2loader`。
- 纯文档轮：未启动游戏/loader，未写 `ra2youli`，未跑 trip，未编译，未派子代理。
- 未修改 `lead/`、`docs/re/`、`ra2render/`、`tools/`。
- 读 GOAL-3T 台账尾部（§351 L3 直接触发点普查）与本篇零交集；该线全部在 §4 禁区内，仅做禁读遵守，未写任何因果/触发/修复意见。
- **待归属告警**：工作区 `re_atlas/tools/dump_typeclass_family.py` 有一处**非本会话所做**的未提交改动（撤销了 HEAD 2ad293d 中的 G-32 修复、把 `this` 寄存器重新硬编码为 ESI）。本轮未触碰、未提交；若属其他会话所改请其自行处理，本线以 HEAD 版本为权威（G-32 修复正确）。

**R-028（2026-10-22）**：
- `tasklist` 查无 `gamemd` / `ra2loader`。
- 未启动游戏/loader，未写 `ra2youli`，未跑 trip，未编译。
- 未修改 `lead/`、`docs/re/`、`ra2render/`、`tools/`。
- 未派子代理（本轮纯本地；异族复核仍欠，见 §核验状态）。
- 读 GOAL-3T 台账尾部确认其在飞的是 `units0`/HouseClass 线，与本轮零交集。

**R-012（2026-10-21 20:1x–21:0x）**：
- `tasklist` 查无 `gamemd` / `ra2loader` / `game.exe`。
- 未启动游戏/loader，未写 `ra2youli`，未跑 trip，未编译。
- 未修改 `lead/`、`docs/re/`、`ra2render/`、`tools/`。
- 派了 1 个工作流 / 2 个子代理（异族核验 v3，纯文本协议），仅只读复算。
- 读 GOAL-3T 台账尾部确认其在飞的是 HouseClass/`units0` 线，与本轮零交集。

## 禁区遵守记录

**R2-1 第三轮（2026-10-21 19:3x–19:4x）**：
- `tasklist` 干净。
- 未启动游戏/loader，未写 `ra2youli`，未跑 trip，未编译。
- 未修改 `lead/`、`docs/re/`、`ra2render/`、`tools/`。
- 冷却结束后派了 1 个工作流 / 2 个子代理（异族核验 v2，简化任务书），仅只读复算。

**R2-1 第二轮（2026-10-21 19:2x–19:3x）**：
- `tasklist` 查无 `gamemd` / `ra2loader` ⇒ 可做完整分析。
- 未启动游戏/loader，未写 `ra2youli`，未跑 trip，未编译。
- 未修改 `lead/`、`docs/re/`、`ra2render/`、`tools/`。
- 因异族核验通道仍在冷却（至约 19:41），本轮**未派子代理**，只做本地整理。

**R0/R1 首轮（2026-10-21 18:4x）**：
- `tasklist` 查无 `gamemd` / `ra2loader` 进程 ⇒ 可按 §8.3 做完整分析。
- 未启动任何游戏/loader，未写 `ra2youli`，未跑 trip，未编译。
- 未修改 `lead/`、`docs/re/`、`ra2render/`、`tools/` 下任何文件（只读）。
- 只使用 `.ra2opt/orig` 与生产件的**只读字节**，未写回。

## 下一步（R-029 起）

1. **P0 核验清欠（在飞）**：R-018/R-019 的 GLM 异族盲验返回后定稿 §11/§12
   核验状态、必要时重算 §12 头部数字、H-012/H-013 原地追加已核验；
   之后批次 = R-021/R-022/R-023（节表/651 键/字段布局+镜像）。
2. **P1 R1-3 调试字符串命名普查**（目标：3.62% 覆盖率显著提升）。
3. P1 R1-4 全局交叉引用索引 → R1-5 虚表槽间接调用索引。
4. R2-1 余项（`ScriptType` 大块、`+0x28`/`+0x30` 类名 L-21）按需推进；
   R2-2 已结题，只按需补充。
5. 每完成一组就更新 kb / INDEX / STATUS / LEDGER。
