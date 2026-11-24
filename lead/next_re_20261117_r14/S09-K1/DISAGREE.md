# S09-K1 DISAGREE — 与 S09-F1 / 台账 / kb11 的冲突与口径差异

> 引用节号：R14_COMMON §1 作废索引、§8.1 错源①/⑦/⑧、§8.2 技术①②；STATUS_BOARD R14-R1..R12；PANEL.md；S09-F1 PROGRESS / `_audit\VERDICT.md`；`re_atlas\kb\11_class_layouts.md`；`docs\re\R8_ui_crt.md`(atlas_rev).

## D1 本卡与任务卡面数字（快照差异，非技术冲突）
- 任务 §1 引 S09 `atlas 1049 / named 679 (64.7%) / [已证] 64 (6.10%)`；当前 `COVERAGE\PANEL.md` S09 行为 `proved_n 67 (6.39%)`（M2 并表后 +3）。这是**快照差异**（卡面写于并表前），本卡以 PANEL 现值 67 为准，不改动任何 coverage 文件。来源 PANEL.md S09 行 / STATUS_BOARD COVERAGE 段。

## D2 与 kb11「slot11=WhatAmI / slot12=GetSize」的适用范围（口径收窄，非推翻）
- `kb\11_class_layouts.md` §0.1 的 GetSize/WhatAmI 结论基于 **AbstractClass 派生类**（ScriptClass/TagClass/TriggerClass 等，槽11/12 为 `B8 imm C3`）。本卡实测 S09 **UI 主类**走 **IGameMap（COM）层次**（RTTI CHD：`IGameMap→GScreenClass→MapClass→DisplayClass→…→SidebarClass`），其 slot11/12 是共享复杂函数 `0x4F43F0/0x4F4410` 等，**不是** WhatAmI/GetSize。
- ⇒ 不是 kb11 错，是**该槽约定只适用 AbstractClass 族**；本卡对 UI 类的 GetSize 报 [未证]（LAYOUT T2），不套用槽12。符合纪律 4（偏移不能跨类定语义）。
- 唯一例外是本卡证实的 **Tactical（RTTI 父类 = AbstractClass）**：slot11=0x6DC450→WhatAmI 0x38、slot12=0x6DC460→GetSize 0xE18，符合 kb11 约定。

## D3 与 S09-F1 的对账（支持 / 新增 / 无冲突）
- **支持**：S09-F1 §PROGRESS#18/VERDICT §2 的侧栏 4×75、stride 0x34、基址 0x880D2C、Count@tab+0x54、Cameos@tab+0x58 —— 本卡 RTTI 确认 SidebarClass vtable 0x7F3058（55 槽）、SelectClass@Strip vtable 0x7F2FCC（34 槽）、父类链一致；v[31]=0x6AAD00、v[48]=0x4AB9B0 字节复核 OK（VERDICT §7「可升级」项，本卡槽值一致）。
- **新增**：RTTI 全类表（21 主类 + ~40 CommandClass 子类）的 TD/COL/槽数/CHD 父类；Tactical GetSize/WhatAmI 双向闭合；1214/14,044 基线复现；12 条槽语义字节复核；DisplayClass 字段写读点。
- **冲突**：无。S09-F1 VERDICT §1「12 跳→11 边」的更正本卡继承（未在 FLOW 层重做）；本卡的"12 条槽语义"是其 §7 可升级项之外的独立证据。

## D4 B8 imm C3 基线数字（口径差异，已显式标注）
- 审计 §969（S20-K1）：全镜像 `B8 imm32 C3` ~837、其中 543 落非槽12。本卡严格口径（`mov eax,imm32` 5B + 紧接 `C3`）得 638、其中 71 落真 slot12（≈11%）。两者宽严不同、方向一致（判据不特异）。本卡只用自己的 638/71 作基线（PROGRESS 核心数字#2），不挪用 837/543 当分母。

## D5 vtables_v2.json 槽数（已知错源，本卡不信）
- §8.1 错源①：vtables_v2.json 13,351 槽 vs 实测 14,044（794 表各少 1 末槽等）。本卡自数 14,044/1214，与审计一致，未引用 JSON 数字。

## D6 R8_ui_crt.md / clue docs 的 RTTI 名（本卡以 RTTI 为准）
- clue doc 称 `TacticalClass`（sidebar_selection_ui.md §1.1）；本卡 RTTI TypeDescriptor 实测名为 `Tactical`（无 Class 后缀）——按任务 §3 T1「类名一律以 RTTI 字符串为准」，本卡用 `Tactical`。
- clue doc 称 WWMouseClass 父类 `MouseClass`？实测 CHD 父类为 `Mouse`（RTTI 名）——同样以 RTTI 为准。
- `CommandClass` v[8]=0x4C9150 抽象桩（R8 §21.1 / E-R8-4）：本卡字节复核 OK，一致。

## D7 无引用的作废节
- 本卡未引用 R14_COMMON §1 作废索引（41 条）中任何节；未引用 STATUS_BOARD 标作废的 vtables JSON 槽数 / 13,755~13,792 分母 / 12 跳口径。若审计发现本卡某处误引，按作废索引裁定。

## D8 coverage_delta.tsv 的 subsystem 字段说明（交合并员裁定）
- 本卡按卡片格式把 delta 全部 5 行的 subsystem 填 **S09**。但其中 `006DC460`/`006DC450`（Tactical::GetSize/WhatAmI）在 `coverage.tsv` 现为 **S07**（渲染/Blitter 桶，且语义被写成"槽语义未证的渲染方法"）。本卡的贡献是**用字节证据更正其语义为 GetSize/WhatAmI 并提级 [已证]**；是否把这 2 行的 subsystem 从 S07 改为 S09（Tactical 也服务 S09 的坐标映射 `0x6D6590`）由合并员/Lead 裁定，本卡不擅自改 coverage.tsv。若保持 S07，本卡证据仍成立。
- 另 3 行（`004AB9B0`/`006AAD00`/`006ABD30`）现为 S09 `[未证]`（"无来源支撑，待补证"），本卡补的是**槽位字节证据**（证明该函数确在此 vtable 槽），据此升 `[静态推断]`；语义名来自 R8_ui_crt.md §21.1，未声称字节层证明行为因果（遵循 M3-UNBLOCK「证据含地址≠支撑语义」口径，故只给 [静态推断] 不给 [已证]）。
