# S15-K2 · PROGRESS（触发器子系统 · 静态 K 卡）

## 结论（三级分级 = L口径 named / S口径 named / proved；分母 atlas S15=158）

| 指标 | 基线(盘上) | 本卡后 | DoD 门槛 | 达标? |
|---|---|---|---|---|
| named **L 口径**（PANEL 字面：非空且非 `sub_` 起头） | 107/158 = 67.72% | **137/158 = 86.71%** | — | 面板口径 |
| named **S 口径**（DoD 判据：再排除 `Class::sub_XXXXXXXX`） | 107/158 = 67.72% | **137/158 = 86.71%** | ≥90% (143) | **否**（差 6） |
| proved `[已证]` | 53/158 = 33.54% | **95/158 = 60.13%** | ≥50% (79) | **是** |

- S15 全表**无** `Class::sub_XXXXXXXX` 占位 ⇒ L 口径与 S 口径数值相同（107→137）。S15 未入 DoD named 线，但 proved 已过硬跨线。
- 本卡新升 `[已证]` **42 条**（25 动作实现 + 6 GetSize + 6 WhatAmI + 5 构造器），全部字节硬证，见 `EVIDENCE/PROMOTIONS_FINAL.tsv`。
- **S15 未达 DoD 第 1 条**（named S 口径 86.71% < 90%）；proved 已达标。未为凑数编名。

## 给审计员的 3 个核心数字（可独立复算）

1. **proved% = 95/158 = 60.13%**。复算：`coverage.tsv` 取 `subsystem==S15` ∩ `function_atlas.tsv`，基线 `[已证]`=53；`coverage_delta.tsv` 42 行全部 `[已证]` 且 entry 均在 atlas ⇒ 53+42=95。分母 158 与 `PANEL.md` S15 行一致。
2. **named S% = 137/158 = 86.71%**。复算：基线 named（非空、非 `sub_` 起头、非 `Class::sub_`）107；本卡 30 个 `sub_` 行改为具名（25 TActionClass 动作 + 5 构造器），12 个 `slotN` 行改名不改变 named 计数 ⇒ 107+30=137。
3. **两个派发表**：`TEventClass::HasOccured 0x71E940` 的 L1 表 `0x71F218`（12 dword，元素=事件处理函数绝对地址）+ 二级选择表 `0x71F248`（49 byte，元素=L1 下标 0..11，11=兜底）。派发指令 `0x71E964: FF 24 95 18 F2 71 00`。见 `EVIDENCE/T2_event_dispatch_tables.txt`；此为 KB 已入账内容，本卡独立字节复核、不重做。

## 证据路径（三级分级）

- 新升 `[已证]` 全表：`EVIDENCE/PROMOTIONS_FINAL.tsv`（42 行，每行含新名/理由/证据文件）。
- 动作实现 25 条：`EVIDENCE/T2_action_map.txt`、`T2_action_handlers.txt`、`T2_action_index_verify.txt`（跳表索引 = 动作ID−1，薄壳唯一 call）。
- GetSize 6 条 + WhatAmI 6 条：`EVIDENCE/T2_vtable_verify.txt`、`T2_slot_disasm.txt`、`T2_rtti_and_sub_callers.txt`、`T2_alloc_sites.txt`（vtable 槽 11/12 + RTTI COL→TD + YRpp 枚举 + ctor push 大小）。
- 构造器 5 条：`EVIDENCE/T2_constructor_candidates.txt`（入口写本类 vtable 链 + 基类 ctor）。
- 派发层复核：`EVIDENCE/T2_dispatch_tables.txt`、`T2_event_dispatch_tables.txt`。
- 计数脚本与原始输出：`work/*.py`、`EVIDENCE/finalize_counts_stdout.txt`、`add_ctors_final_stdout.txt`。

## 基线核验（纪律 9/停机核验）

- 盘上 `coverage.tsv` S15 = 159 行：158 在 atlas + 1 行 `006E6080`（P0-GATE 表外入口 `TagTypeClass::slot25`，`[静态推断]`）。`PANEL.md` 的 158/107/53 是 **atlas 分母**口径，本卡复算 atlas 内 158/L-named107/S-named107/proved53 **逐值吻合** ⇒ 不凑数、不下调。
- 目标 SHA-256 `73201CC0…F67476` / 4,825,360 B 实测一致；capstone 全程 `skipdata=True`（`sweep_calls` 解出 1,394,120 条、跳过 66 B）。
- 字节通道（跳表/ vtable / 构造器）不依赖 atlas entry+size；atlas 仅作入口与分级交叉表 → 满足双通道不同源。

## 交付物

`TARGETS.tsv`（158 行）、`coverage_delta.tsv`（42 行）、`DOD.md`、`UNKNOWNS.md`、`DISAGREE.md`、`LAYOUT.md`、`EVIDENCE/`（不截断）、`work/`（可复跑）。未改 `COVERAGE/coverage.tsv`，未建 KB 文件，未写台账，未 git commit。
