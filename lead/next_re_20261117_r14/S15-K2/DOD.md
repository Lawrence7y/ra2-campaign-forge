# DOD.md — S15 触发器 · PLAN §1 六条对账

> 分母口径（R14-R15）：A = 12,916（atlas 下界，DoD 第 1 条字面分母）；本卡 S15 atlas 分母 = 158（`PANEL.md` S15 行），盘上 coverage S15 = 159（158 atlas + 1 表外 P0-GATE 行 `006E6080`）。
> named 口径（R14-R14）：L = PANEL 字面（非空且非 `sub_` 起头）；S = DoD 判据（再排除 `Class::sub_XXXXXXXX`）。S15 无 `Class::sub_` 占位 ⇒ L/S 同值。

## 第 1 条 · ≥90% 有名字与一行语义 且 ≥50% `[已证]`

| 口径 | 基线 | 本卡后 | 门槛 | 判定 |
|---|---|---|---|---|
| named L | 107/158 = 67.72% | 137/158 = 86.71% | （面板口径，非 DoD 判据） | — |
| named **S** | 107/158 = 67.72% | **137/158 = 86.71%** | ≥90%=143 | **未达标**（差 6 条真名） |
| proved `[已证]` | 53/158 = 33.54% | **95/158 = 60.13%** | ≥50%=79 | **达标** |

- **结论：S15 未达 DoD 第 1 条**（named S 口径 86.71% < 90%）；proved 已跨线。
- 本卡新升 `[已证]` 42 条（byte 硬证），其中 30 条同时新增真名（25 动作 + 5 构造器）。12 条 `slotN`→`GetSize`/`WhatAmI` 属改名，不增 named 计数。
- 每行 `coverage_delta.tsv` 均带一行语义；未从 `sub_` 编造语义——无硬证者保持 `sub_`（见 UNKNOWNS）。
- 复算见 `PROGRESS.md` 核心数字 1/2 与 `EVIDENCE/FINAL_COUNTS.txt`。

## 第 2 条 · 核心类完整字段布局（偏移/类型/读写者，与 GetSize 一致）

- **部分达成**。本卡确立 6 个核心类（TActionClass/TagClass/TagTypeClass/TEventClass/TriggerClass/TriggerTypeClass）的：
  - RTTI 身份：COL→TD→`.?AV<class>@@`（`T2_rtti_and_sub_callers.txt`）；
  - vtable 定界（`.rdata`）：`TActionClass 0x7F443C(COL 0x80BAF0)` / `TagClass 0x7F44E0(0x80BBA0)` / `TagTypeClass 0x7F45C4(0x80BCF0)` / `TEventClass 0x7F5578(0x80C5E0)` / `TriggerClass 0x7F5858(0x80C968)` / `TriggerTypeClass 0x7F5904(0x80CA20)`（`T2_vtable_verify.txt`）；
  - GetSize 双点闭合：`v[12]` 的 `B8 imm32 C3` imm = 0x94/0x38/0xA4/0x58/0x48/0xB4 与构造器 `push <size>`→allocator 独立对上（6/6 精确）；
  - WhatAmI 槽：`v[11]` 常量 = YRpp `AbstractType` 枚举值（Action47/Tag44/TagType45/Event48/Trigger38/TriggerType39，6/6 精确）。
- **缺口**：完整字段读写者表（每字段 ≥3 读 + 写点）本卡未做——KB `10_map_triggers.md` 已证 `TEventClass+0x2C`=事件类型 ID、`TeamClass+0x3C`，但 6 类全字段布局仍需专卡。

## 第 3 条 · 关键数据流（入口 → 每帧更新 → 销毁/存档）调用链图

- **部分达成（已有前提 + 本卡复核，不重做）**：动作派发 `TActionClass::Execute 0x6DD8B0` → 跳表 `0x6DFDEC`(145 项) → 143 唯一目标；Team `0x6E9050` → `0x6E9F74`(65 项)；Event `TEventClass::HasOccured 0x71E940` → L1 `0x71F218`(12 dword)+L2 `0x71F248`(49 byte)。均在 `T2_dispatch_tables.txt`/`T2_event_dispatch_tables.txt` 逐项复核。
- 存档链 `PrepareSaveToINI`/`LoadFromINI` 已在 coverage `[已证]`。销毁链 5 个构造器本卡补。
- **缺口**：完整的"入口→每帧更新→销毁/存档"图未单列文件；KB 已有骨架，供后续汇总。

## 第 4 条 · 涉及的 INI 键与全局变量表

- **部分达成**：本卡在动作实现语义中触及 `0xA8EC7C/0xA8EC88`（Team 数组）、`0xA8B230`（House/会话单例）、`0x8871E0`（游戏全局）、`0x880D2C` 系列（tab）、`0xB0E680/82`（哨兵坐标）、`0xB0F678/710`（全局对象数组）等（`T2_sub_bodies.txt`）。
- **缺口**：未做穷举 INI 键表（`BATTLEMD*.INI` 属 S21/DLC，非本子系统）。列 `UNKNOWNS.md`。

## 第 5 条 · ≥1 张真机卡验证 ≥2 条关键运行时事实（或说明不适用理由）

- **未做（本卡为静态 K 卡，且不适用）**。S15 触发器为地图加载/事件求值逻辑，关键事实（派发表、vtable、构造器）皆为静态可判定字节结构，已由静态双通道字节复核；运行时"某 trigger 是否触发"需预设地图与真机输入，属 L 卡范畴。
- 说明：本卡不申请真机，理由=静态证据已足够定 42 条 `[已证]`，运行时触发序列不属于本卡写域。

## 第 6 条 · `KB\Sxx_<名称>.md` 交付并通过异族审计；台账对应结题节

- **未创建 KB 文件（按派卡指令）**。现状 `re_atlas\kb\00_INDEX.md` §E 示 22 个子系统全缺 `KB\Sxx_*.md`；S15 现有的是 `re_atlas\kb\10_map_triggers.md`（15.6 KB，R2-1 老格式，非 `S15_触发器.md` 命名）。
- 本卡产出（42 条 `[已证]` 的 entry/新名/语义/证据 + 6 类 vtable/RTTI/GetSize/WhatAmI + 派发表地址项数元素语义）**为将来 `S15_触发器.md` 提供素材**。
- 未写台账、未派异族审计（由 Lead 统一调度）。
