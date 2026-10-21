# RE-ATLAS · 进度与覆盖率 (STATUS)

更新：2026-10-21 R-013（L-17 结清：工具缺陷修复，59 → 69 类）

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
| 线性扫描覆盖率（反面样本） | 11.1% | 证明该法不可用 |

## 子系统覆盖

| 子系统 | 状态 | 说明 |
|:---|:---|:---|
| R0 盘点（索引/种子/冲突） | ✅ 完成 | 本轮 |
| R1 全局骨架（PE/RTTI/虚表/覆盖率） | ✅ 完成 | 本轮 |
| R2-1 地图 / 触发器 / 脚本 / TaskForce / TeamClass | 🟢 **派发层 + 类尺寸/前缀布局/对象字段完成** | Action 145 / Team 65 / Event 两级 49 槽全解析；触发器族 8 类**ID+尺寸双命中**；`AbstractClass` 多继承 4 vptr；`TEventClass` 三接口字段 + `Save` 四项；`AbstractTypeClass` 字段边界实测。见 `kb/10_map_triggers.md`、`kb/11_class_layouts.md`、`kb/20_vtable_contract.md`、`kb/21_swizzle_and_object_fields.md`。余：`ScriptType` 大块结构、`+0x28`/`+0x30` 接口对象类名（L-21） |
| R2-2 INI 与规则加载 | ⬜ 未开始 | 种子：`RulesClass*` `0x008871E0`；语料 `config_key_matrix.md`（53KB） |
| R2-3 生产与建造 | ⬜ 未开始 | |
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
| 异族核验通道 | GLM 5.3 + DeepSeek v4.1-flash，两路 `CONFIRMED` |
| 交接件 | **8 条**（H-001…H-008；本轮新增 H-007 swizzle 清零、H-008 类型判定法） |
| KB 正文 | **5 篇**（`00` / `10` / `11` / `20` / `21`） |
| 可复跑工具 | **7 个**（verify_claims / dump_trigger_tables / xcheck_sizes / dump_class_layouts / dump_class_ids / disas / extract_symbols） |

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

## 下一步（R2-1 优先）

1. 吸收 `trigger_system_manifest.md` 的 515 个 VA，按"TagClass→TriggerClass→
   TEventClass/TActionClass"链分组，逐组做入口确认（用 `fn_walk` 的入口集做门禁）。
2. TaskForce / TeamClass / TeamTypeClass 的字段布局：以本线已实证的
   `TeamTypeClass` 尺寸 248 为地基，逐字段反推。
3. 每完成一组就更新 `kb/10_map_triggers.md` 与 INDEX §C。
