# C07 · P0 全镜像普查第 7 片 — PROGRESS

> 卡号 C07｜执行 2026-11-17｜目标 `ra2youli\gamemd.exe`（ImageBase 0x400000，SHA-256 73201CC0…F67476，只读）
> 片：`function_atlas.tsv` 逻辑行 **7753–9044**（1292 函数），入口范围 **0x00640A40 – 0x006BF750**
> 通道：capstone 5.0.7（`skipdata=True`，全 .text 解出 1,394,120 条）+ pefile 2024.8.26 + audit_lib.sweep_calls；**未用 Ghidra**｜写域：仅 `lead\next_re_20261117_r14\C07_census\`

## 分级定义（三级，R14_COMMON §6-9）
- `[已证]` = YRpp `JMP_THIS`/`INI_READ` 或 re_atlas/kb 明确具名地址名（已剔除 `noinit_t` 模板后缀、`Unsorted::sub_*`、裸寄存器词）
- `[静态推断]` = RTTI 虚表类唯一映射到某 Sxx（core）/ 源文件模块归属
- `[未证]` = 字符串关键词 / 导入 API / 已知名邻居投票 / 零证据兜底
- **high 判据**（与 C01–C06 同规格）：self_known 具名（109）+ vtable 类 core 映射（450）= **559**；med/low 不计入

## 结论表
| 项 | 值 | 分级 | 证据路径 |
|---|---|---|---|
| 本片函数数 | **1292** | [已证] | `EVIDENCE/slice_raw.tsv`；`work/verify_core.py` |
| 自动证据覆盖 | vtable 槽命中 500 函数（665 槽次）/ 具名 109（原始 125）/ 源文件模块 34 | [已证] | `EVIDENCE/vtmap_hits.tsv`、`EVIDENCE/known_hits.tsv`、`EVIDENCE/vtables_direct.tsv` |
| 分类完成度 | 1292/1292 全给 Sxx + 置信度 + 一行语义 | [已证] | `coverage_delta.tsv`、`EVIDENCE/classification_trace.tsv` |
| high 置信 | **559 / 1292 = 43.27%** | [已证] | `work/verify_core.py` 复算 |
| 证据分级 | [已证] 109 / [静态推断] 483 / [未证] 700 | [已证] | `EVIDENCE/classification_trace.tsv` 的 grade 列 |
| 无法归类 | **362**（source=none，S22 兜底） | [已证] | trace 过滤 `source==none`；见 UNKNOWNS |
| atlas 空洞（三通道） | call32 **14** / jmp32 **18** / jmp8 **93** | [已证] | `atlas_gaps.tsv`；`work/verify_core.py` 独立重扫 |
| 疑似真入口（R14-R1 严格判据） | **17** | [已证] | `work/gap_stats.json`；两套独立实现一致 |

## 核心数字（给审计员复算）
1. **本片函数数 = 1292**
   复算：`(wc -l coverage_delta.tsv)` = 1292（无表头）；或 `audit_lib.load_func_atlas()` → `rows[7752:9044]` = 1292。
2. **high 置信计数 = 559**
   复算：`awk -F'\t' '$3=="high"' EVIDENCE/classification_trace.tsv | wc -l` = 559（trace 列序 entry,sub,conf,…）。
   交叉 `grep -c $'\t\[已证\]' coverage_delta.tsv` = 109 为 [已证] 子集。分解 self_known 109 + vtable-core 450。
3. **atlas 空洞三通道 = call32 14 / jmp32 18 / jmp8 93；行数 125 = 独立地址数 125（无通道重叠）；疑似真入口合计 = 17**
   复算：`awk -F'\t' '{c[$2]++} END{...}' atlas_gaps.tsv` → 14/18/93，合计 125 行。通道定义（R14-R1）：call32=全 .text `E8 rel32` 目标 owner=None；jmp32=`E9 rel32` owner=None；jmp8=`EB rel8` owner=None。`work/verify_core.py` 独立重扫按首字节分类，三通道数全 match。
   **疑似真入口判据（R14-R1，前三片审计实证）**：16 字节对齐 + 前驱为 nop 填充/ret/jmp + 首指令不像循环体分支标签。17 = call32 全部 14（全 align16、前驱 ret、首指令 sub/mov 序言）+ jmp32 3（`0x661700`/`0x69B670`/`0x6B9530`）。jmp32 中 3 个分支标签（`0x6582D3` cmp、`0x6B3523` test、`0x6B3D73` cmp）标「疑函数内分支标签」不计入；93 个 jmp8 均不满足严格判据不计入。
   `verify_core.py` 用**原始字节前驱判据**（C3/C2/E9/EB/90/CC，与 gap_full 指令起点表法不同实现）独立复算 = 17，逐地址一致；boundary_check 125 全 True（仅辅助，不作权威判据，见 DISAGREE）。

## 各子系统计数（high 分母 = 559）
| Sxx | n | high | Sxx | n | high | Sxx | n | high |
|---|---:|---:|---|---:|---:|---|---:|---:|
| S01 | 14 | 1 | S08 | 0 | 0 | S15 | 0 | 0 |
| S02 | 0 | 0 | S09 | 191 | 115 | S16 | 1 | 0 |
| S03 | 40 | 35 | S10 | 77 | 76 | S17 | 48 | 12 |
| S04 | 107 | 35 | S11 | 54 | 53 | S18 | 71 | 46 |
| S05 | 12 | 9 | S12 | 7 | 0 | S19 | 8 | 0 |
| S06 | 88 | 55 | S13 | 30 | 27 | S20 | 40 | 40 |
| S07 | 27 | 12 | S14 | 57 | 41 | S21 | 11 | 2 |
| S22 | 409 | 0 | — | — | — | 合计 | 1292 | 559 |

合计 1292。本片 0x64–0x6C 段以 **S09 UI**（Sidebar/Radar/Scroll/Mouse/Tab/Power/Slider/ScoreFont）、**S22 兜底**（362 零证据 + 容器/模板工厂）、**S04 规则加载**（RulesClass::Read_*）、**S11 Locomotion**（Ship/Rocket）、**S14**（Radio/Script/SlaveManager/SpawnManager/Side）、**S18 网络**（Queue/Session/SerialEd/SendFile/Skirmish）、**S06 地表**（Smudge/Terrain）、**S03 文件**（RawFile/RAMFile/CDFile/BufferIOFile）为主；S17 序列化、S20 粒子、S05/S13/S10/S07/S21 次之；S02/S08/S15 本段无落点（非全局不存在）。

## 双通道与纪律落实
- 通道 A（atlas）entry+size 作切片输入；通道 B（不依赖 atlas）全 `.text` skipdata=True 逐条反汇编按首字节分 E8/E9/EB；站点归属用「函数区间包含」`owner()`，非 `entry_at_or_before`（抽检 `owner(0x482854)=None`，§6-17）。
- **虚表槽数从 `.rdata` RTTI COL 直读**（`EVIDENCE/vtables_direct.tsv`），不用 `vtables_v2.json['slots']`：1205 共有虚表中 790 真实槽=JSON+1、83=JSON−1、8=JSON−2、仅 324 一致（证实 off-by-one）。
- capstone 全程 `skipdata=True`；boundary_check 超 max_bytes 返回 unknown（保留 None 不当 False）；125 洞目标 boundary 全 True，仅辅助不作判据。
- 写卡前已 grep 台账（RadSiteClass/SlaveManagerClass 有既有条目，按原结论引用不推翻）；前瞻声明 `class X;` 已在具名提取中过滤（C01 教训）；本卡纯自动归类，无寄存器语义/thiscall 结论。所有一行语义标 `[未证]`/`[静态推断]`，未写新 `[已证]`。
- 未改 gamemd.exe / ddraw.dll / ra2youli\；未写台账；未 git commit/push；未改 `COVERAGE\coverage.tsv`；未用 Ghidra。

## 主要缺口
- 362 个零证据归 S22 兜底，建议 P1 用 YRpp/kb 细化（多集中在 0x68–0x6B 段 Rules/Network 未具名 wrapper 与 UI 小函数）。
- 93 个 jmp8 洞不满足 R14-R1 严格入口判据（前驱 plain / align16=N），疑似函数内短跳，见 UNKNOWNS。
- 模板容器按元素类型归 core（S22 固有偏差）；多类并列 vtable 按 `most_common` 取首类致 S12/S16 偏低；见 UNKNOWNS / DISAGREE。
