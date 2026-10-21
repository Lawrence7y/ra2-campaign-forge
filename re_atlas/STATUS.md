# RE-ATLAS · 进度与覆盖率 (STATUS)

更新：2026-10-21（首轮 R0 + R1 骨架）

## 一句话

种子已建、基线已钉：语料 1,304 个命名点全部过段表校验，323 条 claims 全量复算
**323/323 PASS**，虚表 **20/20 与 ATLAS 一致**，并**翻案 2 条实例尺寸**（首报 1 条）。
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
| claims 字节断言复算 | **323 / 323 PASS** | `out/claims_verify.txt` |
| RTTI 类 | 988（954 有虚表） | `out/rtti/` |
| 虚表 vs ATLAS 交叉 | **20 一致 / 0 不一致 / 14 口径不适用** | `out/vtable_xcheck.txt` |
| 实例尺寸复算 | 12 OK / **2 翻案** / 2 口径失效 | `out/size_xcheck.txt` |
| 递归遍历发现函数入口 | **15,224** | `out/fn_walk.txt` |
| 已命名的入口 | 551（**3.62%**） | 保守下界 |
| 线性扫描覆盖率（反面样本） | 11.1% | 证明该法不可用 |

## 子系统覆盖

| 子系统 | 状态 | 说明 |
|:---|:---|:---|
| R0 盘点（索引/种子/冲突） | ✅ 完成 | 本轮 |
| R1 全局骨架（PE/RTTI/虚表/覆盖率） | ✅ 完成 | 本轮 |
| R2-1 地图 / 触发器 / 脚本 / TaskForce / TeamClass | 🟢 **派发层 + 类尺寸/前缀布局完成** | Action 145 / Team 65 / Event 两级 49 槽全解析；触发器族 8 类尺寸全实证；`AbstractClass` 多继承 4 vptr 结构实证。见 `kb/10_map_triggers.md`、`kb/11_class_layouts.md`。余：各派生类具体字段（TaskForce 内部结构、ScriptType 大块结构） |
| R2-2 INI 与规则加载 | ⬜ 未开始 | 种子：`RulesClass*` `0x008871E0`；语料 `config_key_matrix.md`（53KB） |
| R2-3 生产与建造 | ⬜ 未开始 | |
| R2-4 战斗 / 武器 / 弹道 | ⬜ 未开始 | 语料 `weapons_damage_production.md`（449 VA）可作起点 |
| R2-5 AI 决策 | ⬜ 未开始 | 语料 `house_team_ai_update.md` |
| R2-6 超级武器 | ⬜ 未开始 | 语料 `superweapon_re.md`（520 VA） |
| R2-7 存档与读档 | ⬜ 未开始 | 语料 `savegame_block_manifest.md`（525 VA） |
| R2-8 UI 与菜单 | ⬜ 未开始 | 语料 `sidebar_selection_ui.md`、`ui_command_dispatch_deep_dive.md` |
| R2-9 网络与联机同步 | ⬜ 未开始（只读） | 语料 `net_sync_checksum.md`（444 VA） |
| R3 其余模块 | ⬜ 未开始 | |

## 本轮新增量化（R2-1 第二/三轮）

| 指标 | 值 |
|:---|---:|
| 触发器族类尺寸实证 | **8 类**（Script 48 / Tag 56 / Trigger 72 / TEvent 88 / TAction 148 / Team 160 / TaskForce 212 / ScriptType 564） |
| `AbstractClass` 多继承 vptr 数 | **4**（COL.offset 0/4/8/12） |
| 已确证派生字段 | **8 个**（TEvent +0x2C/+0x30/+0x34/+0x54；TAction +0x90；Team +0x3C；TaskForce +0x9C(计数)；Script +0x2C） |
| 已撤回的过度解读 | **3 条**（`.data` 当格式串常量；`+0xA4` 跨类推广；`0x723CE0` 当条目访问器） |
| 归属纠正 | **1 条**（`+0x24`/`+0x64` 由 ScriptType → AbstractTypeClass） |
| 异族核验 | GLM settled（82.5k tok）/ 千问限流未回 ⇒ `TeamTypeClass` 248 仍为**单通道** |
| 已确证基类前缀字段 | 6 个（4 vptr + `+0x10` dword + `+0x20` bool） |
| 序列化顺序 | **先基类后派生**（`ScriptClass::Save` 实证） |
| 交接件 | **6 条**（H-001…H-006） |
| KB 正文 | 3 篇（`00_global_skeleton` / `10_map_triggers` / `11_class_layouts`） |
| 可复跑工具 | 5 个（verify_claims / dump_trigger_tables / xcheck_sizes / dump_class_layouts / disas） |

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
