# C05 · P0 全镜像普查第 5 片 — PROGRESS

> 卡号 C05｜执行 2026-11-17｜目标 `ra2youli\gamemd.exe`（ImageBase 0x400000，SHA-256 73201CC0…F67476，只读）
> 片：`function_atlas.tsv` 逻辑行 **5169–6460**（1292 函数），入口范围 **0x0054A290 – 0x005CBD1F**
> 通道：capstone 5.0.7（`skipdata=True`，全 .text 解出 1,394,120 条）+ pefile 2024.8.26 + audit_lib.sweep_calls；**本卡未用 Ghidra**
> 写域：仅 `lead\next_re_20261117_r14\C05_census\`

## 分级定义（三级，R14_COMMON §6-9）
- `[已证]` = YRpp `JMP_THIS`/`INI_READ` 或 re_atlas/kb 明确具名地址名（已剔除 `::noinit_t` 模板后缀、`Unsorted::sub_*`、裸词）
- `[静态推断]` = RTTI 虚表类唯一映射到某 Sxx（core）/ 源文件模块归属
- `[未证]` = 字符串关键词 / 导入 API / 已知名邻居投票 / 零证据兜底
- **high 判据**（与 C01/C02/C04 同规格）：self_known 具名（106）+ vtable 类 core 映射（457）= **563**；med/low 不计入

## 结论表
| 项 | 值 | 分级 | 证据路径 |
|---|---|---|---|| 本片函数数 | **1292** | [已证] | `EVIDENCE/slice_raw.tsv`；`work/verify_core.py` |
| 自动证据覆盖 | vtable 槽 605 函数 / 具名 106 / 源文件模块 28 | [已证] | `EVIDENCE/vtmap_hits.tsv`、`EVIDENCE/known_hits.tsv` |
| 分类完成度 | 1292/1292 全给 Sxx + 置信度 + 一行语义 | [已证] | `coverage_delta.tsv`、`EVIDENCE/classification_trace.tsv` |
| high 置信 | **563 / 1292 = 43.58%** | [已证] | `work/verify_core.py` 复算 |
| 证据分级 | [已证] 106 / [静态推断] 483 / [未证] 703 | [已证] | `EVIDENCE/classification_trace.tsv` 的 grade 列 |
| 无法归类 | **335**（source=none，S22 兜底） | [已证] | trace 过滤 `source==none`；见 UNKNOWNS |
| atlas 空洞（三通道） | call32 **32** / jmp32 **23** / jmp8 **97** | [已证] | `atlas_gaps.tsv`；`work/verify_core.py` 独立重扫 |

## 核心数字（给审计员复算）
1. **本片函数数 = 1292**
   复算：`(wc -l coverage_delta.tsv)` = 1292（无表头）；或 `audit_lib.load_func_atlas()` → `rows[5168:6460]` = 1292。
2. **high 置信计数 = 563**
   复算：`awk -F'\t' '$3=="high"' EVIDENCE/classification_trace.tsv | wc -l` = 563（trace 列序 entry,sub,conf,…）。
   交叉 `grep -c $'\t\[已证\]' coverage_delta.tsv` = 106 为 [已证] 子集。分解 self_known 106 + vtable-core 457。
3. **atlas 空洞三通道 = call32 32 / jmp32 23 / jmp8 97；疑似真入口 = 53**
   复算：`awk -F'\t' '{c[$2]++} END{...}' atlas_gaps.tsv` → call32=32, jmp32=23, jmp8=97（合计 152 行 = 150 个独立地址，2 地址同时被 jmp32+jmp8 命中）。
   通道定义（Lead 统一口径）：call32=全 .text `E8 rel32` 目标 owner=None；jmp32=`E9 rel32` 目标 owner=None；jmp8=`EB rel8` 目标 owner=None。
   `work/verify_core.py` 用独立重扫逐条按首字节 E8/E9/EB 分类，三通道数全 match。
   疑似真入口 = call32(32) + 非分支标签 jmp32(21) = **53**；2 个 jmp32 分支标签 = `0x5B1E20`(`cmp [ecx],0;jne`)、`0x5C8F1B`(`cmp ebp,eax;jl`) 已标「疑函数内分支标签」。
   全部 152 行 boundary_check=True；call32 首指令多为函数序言（push/sub esp/mov eax,[esp+..]）。

## 各子系统计数（high 分母 = 563）
| Sxx | n | high | Sxx | n | high | Sxx | n | high |
|---|---:|---:|---|---:|---:|---|---:|---:|
| S01 | 10 | 2 | S08 | 0 | 0 | S15 | 0 | 0 |
| S02 | 0 | 0 | S09 | 120 | 66 | S16 | 0 | 0 |
| S03 | 24 | 15 | S10 | 33 | 33 | S17 | 1 | 0 |
| S04 | 0 | 0 | S11 | 86 | 83 | S18 | 115 | 98 |
| S05 | 4 | 4 | S12 | 10 | 7 | S19 | 22 | 20 |
| S06 | 278 | 126 | S13 | 19 | 19 | S20 | 31 | 31 |
| S07 | 50 | 25 | S14 | 11 | 0 | S21 | 42 | 34 |
| S22 | 436 | 0 | S08/S15/S16 | 0 | 0 | S02/S04 | 0 | 0 |
合计 1292。本片 0x54–0x5C 段以 **S11 Locomotion 整族**（Jumpjet/Mech/Rocket/Teleport/Walk/Hover/Fly/Drive/Ship/Tunnel/DropPod）、**S18 MPGameMode 系**（MPCooperative/Siege/FreeForAll/Megawealth/UnholyAlliance + MPTeams）、**S06 MapClass/MapSeedClass 地图与随机地图生成**、**MissionClass(S10)**、**RadioClass(S14)**、UI 控件(S09) 为主；VQ/BinkMovie(S19)、LightSource/LaserDraw/LineTrail(S07/S20)、压缩管线 BlowStraw/LCW/LZO(S03) 次之。S02/S04/S08/S15/S16 在本地址段无落点（不是全局不存在）。

## 双通道与纪律落实
- 通道 A（atlas）：`function_atlas.tsv` entry+size 作切片与分类输入。
- 通道 B（不依赖 atlas entry+size）：全 `.text` skipdata=True 逐条反汇编，按 opcode 首字节分 E8/E9/EB；站点归属用「函数区间包含」`owner()`，不用 `entry_at_or_before`（R14 §6-17，抽检 `owner(0x482854)=None`）。
- capstone 全程 `skipdata=True`；`boundary_check` 超 max_bytes 返回 `unknown`（保留 None 不当 False）。
- 写卡前已 grep 台账 `GOAL_THREE_TARGETS_20261018.md`；本卡所有一行语义标猜测，未写新 [已证] 发现。
- 未改 gamemd.exe / ddraw.dll / ra2youli\ 下任何文件；未写台账；未 git commit/push；未改 `COVERAGE\coverage.tsv`（只交 delta）。

## 主要缺口
- 335 个零证据函数归 S22 兜底；建议 P1 用 YRpp/kb 二次细化。
- 97 个 jmp8 洞目标全部「引用站点在洞内」，首指令多为 mov/cmp/test，疑似短跳函数内分支，需 P1 用序言+调用链证真（见 UNKNOWNS）。
- S14 仅 11 且 high=0：37 个含 RadioClass 虚表的函数因多类并列「most_common 取首个」被归到 S10/S12/S05（同 C04 规则），count 分散见 UNKNOWNS。
