# C06 · P0 全镜像普查第 6 片 — PROGRESS

> 卡号 C06｜执行 2026-11-17｜目标 `ra2youli\gamemd.exe`（ImageBase 0x400000，SHA-256 73201CC0…F67476，只读）
> 片：`function_atlas.tsv` 逻辑行 **6461–7752**（1292 函数），入口范围 **0x005CBD20 – 0x00640A3C**
> 通道：capstone 5.0.7（`skipdata=True`，全 .text 解出 1,394,120 条）+ pefile 2024.8.26 + audit_lib.sweep_calls；**本卡未用 Ghidra**
> 写域：仅 `lead\next_re_20261117_r14\C06_census\`

## 分级定义（三级，R14_COMMON §6-9）
- `[已证]` = YRpp `JMP_THIS`/`INI_READ` 或 re_atlas/kb 明确具名地址名（已剔除 `::noinit_t` 模板后缀、`Unsorted::sub_*`、裸词）
- `[静态推断]` = RTTI 虚表类唯一映射到某 Sxx（core）/ 源文件模块归属
- `[未证]` = 字符串关键词 / 导入 API / 已知名邻居投票 / 零证据兜底
- **high 判据**（与 C01/C02/C04/C05 同规格）：self_known 具名（41）+ vtable 类 core 映射（341）= **382**；med/low 不计入

## 结论表
| 项 | 值 | 分级 | 证据路径 |
|---|---|---|---|
| 本片函数数 | **1292** | [已证] | `EVIDENCE/slice_raw.tsv`；`work/verify_core.py` |
| 自动证据覆盖 | vtable 槽 546 函数（508 映射 Sxx）/ 具名 41 / 源文件模块 44 | [已证] | `EVIDENCE/vtmap_hits.tsv`、`EVIDENCE/known_hits.tsv` |
| 分类完成度 | 1292/1292 全给 Sxx + 置信度 + 一行语义 | [已证] | `coverage_delta.tsv`、`EVIDENCE/classification_trace.tsv` |
| high 置信 | **382 / 1292 = 29.57%** | [已证] | `work/verify_core.py` 复算 |
| 证据分级 | [已证] 41 / [静态推断] 385 / [未证] 866 | [已证] | `EVIDENCE/classification_trace.tsv` 的 grade 列 |
| 无法归类 | **452**（source=none，S22 兜底） | [已证] | trace 过滤 `source==none`；见 UNKNOWNS |
| atlas 空洞（三通道） | call32 **24** / jmp32 **78** / jmp8 **301** | [已证] | `atlas_gaps.tsv`；`work/verify_core.py` 独立重扫 |

## 核心数字（给审计员复算）
1. **本片函数数 = 1292**
   复算：`(wc -l coverage_delta.tsv)` = 1292（无表头）；或 `audit_lib.load_func_atlas()` → `rows[6460:7752]` = 1292。
2. **high 置信计数 = 382**
   复算：`awk -F'\t' '$3=="high"' EVIDENCE/classification_trace.tsv | wc -l` = 382（trace 列序 entry,sub,conf,…）。
   交叉 `grep -c $'\t\[已证\]' coverage_delta.tsv` = 41 为 [已证] 子集。分解 self_known 41 + vtable-core 341。
3. **atlas 空洞三通道 = call32 24 / jmp32 78 / jmp8 301；疑似真入口 = 96**
   复算：`awk -F'\t' '{c[$2]++} END{...}' atlas_gaps.tsv` → call32=24, jmp32=78, jmp8=301；合计 **403 行 = 388 独立地址**（15 地址同时被 2 通道命中）。
   通道定义：call32=全 .text `E8 rel32` 目标 owner=None；jmp32=`E9 rel32` owner=None；jmp8=`EB rel8` owner=None。
   `work/verify_core.py` 独立重扫逐条按首字节 E8/E9/EB 分类，三通道数全 match。
   疑似真入口 = call32(24) + 非分支标签 jmp32(72) = **96**；6 个 jmp32 分支标签（首指令 jle/cmp×4/test）已标「疑函数内分支标签」。
   boundary_check：401 True / 2 False（`0x5DF100`/`0x5DF104` jmp8 目标落在 2B `add al,[edx]` 指令内部，双通道自证非边界；jmp8 不计入疑似真入口）。疑似真入口 union 亦为 96（call32 与 jmp32-good 不重叠）。

## 各子系统计数（high 分母 = 382）
| Sxx | n | high | Sxx | n | high | Sxx | n | high |
|---|---:|---:|---|---:|---:|---|---:|---:|
| S01 | 6 | 0 | S08 | 0 | 0 | S15 | 0 | 0 |
| S03 | 15 | 5 | S09 | 145 | 16 | S16 | 0 | 0 |
| S04 | 10 | 0 | S10 | 2 | 2 | S17 | 0 | 0 |
| S05 | 23 | 22 | S11 | 0 | 0 | S18 | 113 | 80 |
| S06 | 42 | 32 | S12 | 5 | 1 | S19 | 6 | 0 |
| S07 | 34 | 14 | S13 | 27 | 26 | S20 | 140 | 138 |
| S14 | 49 | 24 | S21 | 34 | 22 | S22 | 641 | 0 |
合计 1292。本片 0x5C–0x64 段以 **S20 粒子/Anim 特效整族**（Particle/ParticleSystem/VoxelAnim/Wave/VeinholeMonster/Anim/MS*Anim）、**S22 兜底**（452 零证据 + 容器）、**S09 UI 对话框**（导入 API 以 GetDlgItem/SendMessage 为主）、**S18 联机/Modem**（MPGameMode 系 + NullModem + net*.cpp）、**S06 地图地表**（Overlay/Terrain/Smudge/IsometricTile）、**S13 战斗**（Bullet/Parasite）、S14（Radio/House）为主；S01/S04/S17/S19 少量，S02/S08/S11/S15/S16 在本地址段无落点（不是全局不存在）。

## 双通道与纪律落实
- 通道 A（atlas）：`function_atlas.tsv` entry+size 作切片与分类输入。
- 通道 B（不依赖 atlas entry+size）：全 `.text` skipdata=True 逐条反汇编按 opcode 首字节分 E8/E9/EB；站点归属用「函数区间包含」`owner()`，不用 `entry_at_or_before`（抽检 `owner(0x482854)=None`）。
- capstone 全程 `skipdata=True`；`boundary_check` 超 max_bytes 返回 unknown（保留 None 不当 False）；2 例 False 已用自建指令边界双证落在指令内部。
- 写卡前已 grep 台账 `GOAL_THREE_TARGETS_20261018.md`；本片所涉已证事实（DrawIfVisible 0x5F4B10、Limbo 0x5F4D30/0x5F4EC0、Slot-114 0x5F5F40、MAPSEL 阶段 0x5CEEF0/0x5CF830、INI 键上限 0x5CF04F/0x5CF367）均照引不推翻；所有一行语义标猜测，未写新 [已证] 发现。
- 未改 gamemd.exe / ddraw.dll / ra2youli\ 下任何文件；未写台账；未 git commit/push；未改 `COVERAGE\coverage.tsv`（只交 delta）；未用 Ghidra。

## 主要缺口
- 452 个零证据函数归 S22 兜底；建议 P1 用 YRpp/kb 二次细化（多集中在 0x63–0x64 尾段 MPGameMode 未具名方法与 wrapper）。
- 301 个 jmp8 洞目标中 2 个（0x5DF100/0x5DF104）经双证落在指令内部（假阳性）；其余首指令多为 mov/cmp/test，疑似函数内短跳，不计入疑似真入口（见 UNKNOWNS）。
- S10 仅 2 且 MissionClass 原始 vtable 命中 70：多数含 MissionClass/RadioClass 虚表的函数因多类并列 `most_common 取首个` 被归 S20/S06/S05/S18（同 C05 规则），见 UNKNOWNS。
