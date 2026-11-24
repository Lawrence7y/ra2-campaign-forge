# C09 · P0 全镜像普查第 9 片 — PROGRESS
> 卡号 C09｜执行 2026-11-17｜目标 `ra2youli\gamemd.exe`（ImageBase 0x400000，SHA-256 73201CC0…F67476，只读）
> 片：`function_atlas.tsv` 逻辑行 **10337–11628**（1292 函数），入口范围 **0x00719F30 – 0x007734F9**
> 通道：capstone 5.0.7（`skipdata=True`，全 .text 解出 1,394,120 条）+ 自写 struct PE + pefile 2024.8.26；**本卡未用 Ghidra**
> 写域：仅 `lead\next_re_20261117_r14\C09_census\`

## 分级定义（三级，R14_COMMON §6-9）
- `[已证]` = YRpp `JMP_THIS`/`INI_READ` 或 re_atlas/kb 明确具名地址名（剔除 `noinit_t`/模板后缀/裸词）
- `[静态推断]` = RTTI 虚表类唯一映射到某 Sxx（core）/ 源文件模块
- `[未证]` = 字符串关键词 / 导入 API / 已知名邻居投票 / 零证据兜底
- **high 判据**（与 C01–C08 同规格）：self_known 具名 63 + vtable 类 core 映射 360 = **423**；med/low 不计入
## 结论表
| 项 | 值 | 分级 | 证据路径 |
|---|---|---|---|
| 本片函数数 | **1292** | [已证] | `EVIDENCE/slice_raw.tsv`；`work/verify_core.py` |
| 自动证据覆盖 | vtable 槽 584 函数 / 具名 80（clean 63）/ 源文件模块 18 | [已证] | `EVIDENCE/vtmap_hits.tsv`、`EVIDENCE/known_hits.tsv` |
| 虚表槽实测 | **14044**（v2.json 13351，+693）| [已证] | `work/rtti_independent.json`；delta `{1:794,0:327,-1:85,-2:8}` 与 C03/C08 审计一致 |
| 分类完成度 | 1292/1292 全给 Sxx + 置信度 + 一行语义 | [已证] | `coverage_delta.tsv`、`EVIDENCE/classification_trace.tsv` |
| high 置信 | **423 / 1292 = 32.74%** | [已证] | `work/verify_core.py` 复算 |
| 证据分级 | [已证] 63 / [静态推断] 367 / [未证] 862 | [已证] | `EVIDENCE/classification_trace.tsv` 的 grade 列 |
| 无法归类 | **440**（source=none，S22 兜底） | [已证] | trace 过滤 `source==none`；见 UNKNOWNS |
| atlas 空洞（三通道） | call32 **17** / jmp32 **8** / jmp8 **79** | [已证] | `atlas_gaps.tsv`；`work/verify_core.py` 独立重扫 |

## 核心数字（给审计员复算）
1. **本片函数数 = 1292**
   复算：`wc -l coverage_delta.tsv` = 1292（无表头）；`function_atlas.tsv` → `rows[10336:11628]` = 1292；verify_core CORE1 三路一致。
2. **high 置信计数 = 423**
   复算：`awk -F'\t' '$3=="high"' EVIDENCE/classification_trace.tsv | wc -l` = 423；分解 self_known 63 + vtable-core 360。
3. **atlas 空洞三通道 = call32 17 / jmp32 8 / jmp8 79；行数 104 / 独立地址 100；疑似真入口 = 17**
   复算：按 chan 列统计 `atlas_gaps.tsv` → 17/8/79（104 行 = 100 独立地址，4 地址 jmp32+jmp8 双命中）。
   通道定义：call32=全 .text `E8 rel32` 目标 owner=None；jmp32=`E9 rel32`；jmp8=`EB rel8`。
   `work/verify_core.py` 用 pefile+op_str 独立重扫，三通道数全 match；`owner(0x482854)=None`（R14 §6-17）。
   **疑似真入口（R14-R1 严格）= 17，全部为 call32**：17 个 call32 目标均 16 字节对齐 + 前驱 nop 填充 + 首指令为函数序言（push/sub esp/mov，非分支标签）。
   **jmp32 贡献 0**：8 个 jmp32 全部 align16=0、prev=other（其中 3 个首指令 test/cmp 为函数内分支标签，5 个非分支但同样不对齐/前驱非 nop-ret-jmp），按 R14-R1 严格判据一概不计（见 UNKNOWNS，不因凑数放宽）。
   唯一 1 例 boundary unknown（`0x71F2C5` jmp8，no-prior-entry）保留 None 不当 False；`0x71F613` jmp8 落 `jno` 指令内部（bd=False），均 jmp8 不入疑似真入口。
## 各子系统计数（high 分母 = 423）
| Sxx | n | high | Sxx | n | high | Sxx | n | high |
|---|---:|---:|---|---:|---:|---|---:|---:|
| S01 | 6 | 0 | S08 | 0 | 0 | S15 | 69 | 55 |
| S02 | 0 | 0 | S09 | 65 | 33 | S16 | 15 | 14 |
| S03 | 1 | 0 | S10 | 74 | 72 | S17 | 1 | 0 |
| S04 | 18 | 0 | S11 | 68 | 66 | S18 | 7 | 0 |
| S05 | 24 | 18 | S12 | 2 | 0 | S19 | 33 | 9 |
| S06 | 99 | 65 | S13 | 20 | 18 | S20 | 59 | 54 |
| S07 | 37 | 5 | S14 | 14 | 0 | S21 | 11 | 10 |
| S22 | 669 | 4 | | | | | | |
合计 1292。本片 0x71–0x77 段为类名字典序尾段（T–W）：**S10 UnitClass 整族 + S11 Walk/Tunnel/Teleport Locomotor**、**S06 Terrain/Tiberium/WaypointPath/Tube**、**S15 Trigger/TEvent/TAction**、**S20 VoxelAnim/Wave/VeinholeMonster/MS*Anim**、**S13 Weapon/Warhead**、**S19 Voc/Vox 音频**、**S16 Temporal 超级武器**、**S07 Convert/VXL 渲染**为主；另含**大量自定义 `WorldDominationTour`(WDT) 战役/游戏选项/ territory/conflict/history 类族**（`WDTSel.cpp`/`WDTGameOptions.cpp`/`WDTProps.cpp`/`WDTTerr.cpp`，归 S09/S21，见 DISAGREE）、S22 兜底 669（其中 440 零证据 + 大量 `T_VectorClass`/`T_DynamicVectorClass`/`T_rc_ptr` 泛型容器，实例类型判为参数不虚高，见 DISAGREE）。S02/S08 在本地址段无落点（不是全局不存在）。

## 双通道与纪律落实
- 通道 A（atlas）：`function_atlas.tsv` entry+size 作切片边界与 `owner()` 区间包含判定。
- 通道 B（不依赖 atlas entry+size）：自写 struct PE 解 RTTI（`rtti_independent.py`，真实槽数非 v2.json slots）+ 自写 struct PE + capstone skipdata 按操作码字节分 E8/E9/EB（`sweep_independent.py`）；与通道 A 不同源。
- 通道 C（verify_core.py，第三路）：pefile + capstone(detail=True) + op_str 解析独立重扫，与通道 B 的 bytes[0]+rel 算法不同源；三通道数 + 疑似真入口全 match。
- capstone 全程 `skipdata=True`（全 .text 1,394,120 条，跳过 66 字节）；自建 `boundary_check_unknown` 超 max_bytes 返回 None（unknown），不当 False。
- 写卡前已 grep 主台账 `GOAL_THREE_TARGETS_20261018.md`；本片一行语义均标猜测，未写新 [已证] 发现。
- 未改 gamemd.exe / ddraw.dll / ra2youli\ 下任何文件；未写台账；未 git commit/push；未改 `COVERAGE\coverage.tsv`（只交 delta）；未用 Ghidra。
## 主要缺口
- 440 个零证据函数归 S22 兜底；建议 P1 用 YRpp/kb 二次细化（多为 0x75–0x77 段 tail 未具名 wrapper）。
- 79 个 jmp8 洞目标（引用站点多在洞内、首指令 mov/cmp/add）与 8 个 jmp32 目标（全 align16=0/prev=other）均判洞内分支/未建模代码块，不计入疑似真入口（见 UNKNOWNS）。
- 17 个 call32 疑似真入口集中在 0x72–0x76 的 atlas 函数尺寸低估空洞（前驱 nop 填充、序言完整），建议 P1 优先为这些地址补 atlas 函数条目（见 EVIDENCE/gap_channels.tsv）。
