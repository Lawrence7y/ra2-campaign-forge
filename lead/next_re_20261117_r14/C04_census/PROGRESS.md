# C04 · P0 全镜像普查第 4 片 — PROGRESS

> 卡号 C04｜执行 2026-11-17｜目标 `ra2youli\gamemd.exe`（ImageBase 0x400000，SHA-256 73201CC0…F67476，只读）
> 片：`function_atlas.tsv` 逻辑行 **3877–5168**（1292 函数），入口范围 **0x004F1840 – 0x0054A28E**
> 通道：capstone 5.0.7（`skipdata=True`，全 .text 解出 1,394,120 条）+ pefile + audit_lib.sweep_calls；**本卡未用 Ghidra**

## 分级定义（三级，R14_COMMON §6-9）
- `[已证]` = YRpp `JMP_THIS`/`INI_READ` 或 re_atlas/kb 明确具名地址名（已剔除 `::noinit_t` 模板后缀、`Unsorted::sub_*` 占位名、裸词 ReadString/this 等）
- `[静态推断]` = RTTI 虚表类唯一映射到某 Sxx（core）/ 源文件模块归属
- `[未证]` = 字符串关键词 / 导入 API / 已知名邻居投票 / 零证据兜底
- **high 判据**（同 C02）：`self_known` 具名（96）+ vtable 类 core 映射（679）= **775**；med/low 不计入

## 结论表
| 项 | 值 | 分级 | 证据路径 |
|---|---|---|---|
| 本片函数数 | **1292** | [已证] | `EVIDENCE/slice_raw.tsv`；`work/verify_core.py` |
| 自动证据覆盖 | vtable 槽 723 函数 / 具名 96 / 源文件模块 10 | [已证] | `EVIDENCE/vtmap_hits.tsv`、`EVIDENCE/known_hits.tsv` |
| 分类完成度 | 1292/1292 全给 Sxx + 置信度 + 一行语义 | [已证] | `coverage_delta.tsv`、`EVIDENCE/classification_trace.tsv` |
| high 置信 | **775 / 1292 = 59.98%** | [已证] | `work/verify_core.py` 复算 |
| 证据分级 | [已证] 96 / [静态推断] 689 / [未证] 507 | [已证] | `EVIDENCE/classification_trace.tsv` 的 grade 列 |
| 无法归类 | **288**（source=none，S22 兜底） | [已证] | trace 过滤 `source==none`；见 UNKNOWNS |
| atlas 空洞入口 | **26**（严格 rel32：E8 call + E9 jmp，owner=None） | [已证] | `atlas_gaps.tsv`；`work/verify_core.py` |

## 三个核心数字（给审计员复算）
1. **本片函数数 = 1292**
   复算：`(wc -l coverage_delta.tsv)` = 1292（无表头）；
   或 `python -c "import audit_lib as a; r,_=a.load_func_atlas(); print(len(r[3876:5168]))"` → 1292。
2. **high 置信计数 = 775**
   复算：`awk -F'\t' '$3=="high"' EVIDENCE/classification_trace.tsv | wc -l` → 775
   （trace 列序：entry,sub,conf,grade,…）；交叉 `grep -c $'\t[已证]' coverage_delta.tsv` = 96 为 [已证] 子集。
   分解：`self_known` 96 + vtable-core 679；high 占比 = 775/1292 = **59.98%**。
3. **atlas 空洞入口数 = 26**
   复算：`(wc -l atlas_gaps.tsv)-1` = 26；
   独立通道：`work/gap_analyze.py` 全 .text 逐条复扫 opcode（E8/E9/EB），取 `has_rel32 ∧ owner(target)==None` = 26。
   ⚠️ 按卡纪律，另有 **69** 个仅由 EB(rel8) 短跳命中的洞目标**不计入** rel32 命中（见 UNKNOWNS）；C02 宽松口径（含 EB）会得 95。`0x4824D4` 在 C02 范围，不在本片。

## 各子系统计数（high 分母 = 775）
| Sxx | n | high | Sxx | n | high | Sxx | n | high |
|---|---:|---:|---|---:|---:|---|---:|---:|
| S01 | 2 | 0 | S08 | 0 | 0 | S15 | 0 | 0 |
| S02 | 6 | 0 | S09 | 300 | 285 | S16 | 24 | 16 |
| S03 | 9 | 4 | S10 | 74 | 74 | S17 | 1 | 0 |
| S04 | 78 | 33 | S11 | 23 | 23 | S18 | 46 | 44 |
| S05 | 85 | 80 | S12 | 5 | 1 | S19 | 7 | 0 |
| S06 | 62 | 27 | S13 | 0 | 0 | S20 | 24 | 24 |
| S07 | 10 | 0 | S14 | 198 | 162 | S21 | 6 | 2 |
|  |  |  |  |  |  | S22 | 332 | 0 |

合计 1292。本片 0x4F–0x54 段以 **S09 UI/命令派发**（大量 `*CommandClass` + `Init.CPP` 的 `Cmnd:`/`TXT_*` 串）与 **S14 House/AI**（HouseClass 41 槽 + 96 个具名方法中的大多数）为主；
S10（InfantryClass 74 槽）、S11（HoverLocomotionClass 22）、S18（IPX/ConnMan/WOL 网络）、S06（Map/IsometricTile）、S16（Ion.cpp 闪电风暴）次之。S08/S13/S15 在本地址段无落点（不是全局不存在）。

## 双通道与纪律落实
- 通道 A（atlas）：`function_atlas.tsv` entry+size 作切片与分类输入。
- 通道 B（不依赖 atlas entry+size）：`audit_lib.sweep_calls` 全 `.text` 线性扫 rel32 目标（skipdata=True），站点归属用「函数区间包含」`owner()`，不用 `entry_at_or_before`（R14 §6-17）。
- capstone 全程 `skipdata=True`；`boundary_check` 超 max_bytes 返回 `unknown`（`collect.py` 中 `"未判定" in reason` → 保留 None，不当 False）。
- 写卡前已 grep 台账 `GOAL_THREE_TARGETS_20261018.md`（`InfantryClass::AI@0x51BAB0`、`IsCellOccupied@0x51BF90`、`MixFileClass::Bootstrap` 等均已有 [已证]）；本卡所有一行语义标猜测，未写新 [已证] 发现。
- 未改 gamemd.exe / ddraw.dll / ra2youli\ 下任何文件；未写台账；未 git commit/push；未改 `COVERAGE\coverage.tsv`（只交 delta）。

## 主要缺口
- 288 个 `[未证]` 零证据函数归 S22 兜底，建议 P1 用 YRpp/kb 二次细化。
- 26 个 rel32 洞入口中 19 个 jmp32 目标多数是函数内部分支点（见 UNKNOWNS），非确定新入口；7 个 call 目标证据更强。
- 69 个 EB 短跳洞目标集中在 0x4F8xxx–0x4F9xxx、0x527xxx–0x52Axxx 等 atlas 空洞区，需 P1 逐点用序言+调用链证真。
