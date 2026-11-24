# C08 · P0 全镜像普查第 8 片 — PROGRESS

> 卡号 C08｜执行 2026-11-17｜目标 `ra2youli\gamemd.exe`（ImageBase 0x400000，SHA-256 73201CC0…F67476，只读）
> 片：`function_atlas.tsv` 逻辑行 **9045–10336**（1292 函数），入口范围 **0x006BF750 – 0x00719F29**
> 通道：capstone 5.0.7（`skipdata=True`，全 .text 解出 1,394,120 条）+ 自写 struct PE + pefile 2024.8.26；**本卡未用 Ghidra**
> 写域：仅 `lead\next_re_20261117_r14\C08_census\`

## 分级定义（三级，R14_COMMON §6-9）
- `[已证]` = YRpp `JMP_THIS`/`INI_READ` 或 re_atlas/kb 明确具名地址名（剔除 `noinit_t`/模板后缀/裸词）
- `[静态推断]` = RTTI 虚表类唯一映射到某 Sxx（core）/ 源文件模块
- `[未证]` = 字符串关键词 / 导入 API / 已知名邻居投票 / 零证据兜底
- **high 判据**（与 C01–C06 同规格）：self_known 具名 101 + vtable 类 core 映射 307 = **408**；med/low 不计入

## 结论表
| 项 | 值 | 分级 | 证据路径 |
|---|---|---|---|
| 本片函数数 | **1292** | [已证] | `EVIDENCE/slice_raw.tsv`；`work/verify_core.py` |
| 自动证据覆盖 | vtable 槽 683 函数 / 具名 101 / 源文件 0 | [已证] | `EVIDENCE/vtmap_hits.tsv`、`EVIDENCE/known_hits.tsv` |
| 虚表槽实测 | **14044**（v2.json 13351，+693）| [已证] | `work/rtti_independent.json`；delta `{1:794,0:327,-1:85,-2:8}` 与 C03 审计一致 |
| 分类完成度 | 1292/1292 全给 Sxx + 置信度 + 一行语义 | [已证] | `coverage_delta.tsv`、`EVIDENCE/classification_trace.tsv` |
| high 置信 | **408 / 1292 = 31.58%** | [已证] | `work/verify_core.py` 复算 |
| 证据分级 | [已证] 101 / [静态推断] 308 / [未证] 883 | [已证] | `EVIDENCE/classification_trace.tsv` 的 grade 列 |
| 无法归类 | **309**（source=none，S22 兜底） | [已证] | trace 过滤 `source==none`；见 UNKNOWNS |
| atlas 空洞（三通道） | call32 **2** / jmp32 **2** / jmp8 **37** | [已证] | `atlas_gaps.tsv`；`work/verify_core.py` 独立重扫 |

## 核心数字（给审计员复算）
1. **本片函数数 = 1292**
   复算：`wc -l coverage_delta.tsv` = 1292（无表头）；`function_atlas.tsv` → `rows[9044:10336]` = 1292；verify_core CORE1 三路一致。
2. **high 置信计数 = 408**
   复算：`awk -F'\t' '$3=="high"' EVIDENCE/classification_trace.tsv | wc -l` = 408；分解 self_known 101 + vtable-core 307。
3. **atlas 空洞三通道 = call32 2 / jmp32 2 / jmp8 37；行数 41 / 独立地址 41；疑似真入口 = 3**
   复算：按 chan 列统计 `atlas_gaps.tsv` → 2/2/37（合计 41 行 = 41 独立地址，无通道重叠）。
   通道定义：call32=全 .text `E8 rel32` 目标 owner=None；jmp32=`E9 rel32`；jmp8=`EB rel8`。
   **疑似真入口（R14-R1 严格）= 3**：`0x6C8900`(call32,align16,prev=ret,push 序言)、`0x6E8000`(call32,align16,prev=nop,mov/push 序言)、`0x6C89D0`(jmp32,align16,prev=nop,首 mov 非分支标签)。
   其余 38 行：37 个 jmp8 + 1 个 jmp32(`0x6CA204`,align16=0,prev=other) 判为洞内分支标签，不入疑似真入口；见 UNKNOWNS。

## 各子系统计数（high 分母 = 408）
| Sxx | n | high | Sxx | n | high | Sxx | n | high |
|---|---:|---:|---|---:|---:|---|---:|---:|
| S01 | 0 | 0 | S08 | 0 | 0 | S15 | 90 | 53 |
| S02 | 0 | 0 | S09 | 14 | 14 | S16 | 45 | 39 |
| S03 | 1 | 1 | S10 | 118 | 112 | S17 | 9 | 9 |
| S04 | 5 | 0 | S11 | 15 | 15 | S18 | 2 | 1 |
| S05 | 90 | 83 | S12 | 28 | 21 | S19 | 4 | 0 |
| S06 | 50 | 0 | S13 | 3 | 0 | S20 | 4 | 1 |
| S07 | 27 | 17 | S14 | 102 | 42 | S21 | 0 | 0 |
| S22 | 685 | 0 | | | | | | |
合计 1292。本片 0x6B–0x71 段以 **S05/S10/S12 对象模型整族**（Techno/Foot/Building/Aircraft/Infantry/Unit 及其 TypeClass）、**S16 超级武器**（SuperClass/SuperWeaponTypeClass，`Super.CPP`）、**S15 触发器**（TAction/Tag/TagType/Trigger）、**S14 团队/AI**（Team/TeamType/TaskForce/AITriggerType/Neuron）、**S17 存档**（SwizzleManager/Here_I_Am）、**S07 渲染**（Tactical/DirtyArea/Shadow）、**S11 传送**（TeleportLocomotion）为主；**S22 兜底 685**（其中 **284 个 `TClassFactory<V*>` 泛型工厂**四法逐字节同构，见 DISAGREE）+ UI 控件(S09)、战斗(S13)、EVA(S19) 次之。S01/S02/S08/S21 在本地址段无落点（不是全局不存在）。

## 双通道与纪律落实
- 通道 A（atlas）：`function_atlas.tsv` entry+size 作切片边界与 `owner()` 区间包含判定。
- 通道 B（不依赖 atlas entry+size）：自写 struct PE 解 RTTI（`rtti_independent.py`，真实槽数非 v2.json slots）+ 自写 struct PE + capstone skipdata 按操作码字节分 E8/E9/EB（`sweep_independent.py`）；与通道 A 不同源，互不读对方判定产物。第三通道 `verify_core.py` 用 pefile + `op_str` 解析独立复核。
- capstone 全程 `skipdata=True`；`boundary_check` 超 max_bytes 的「未判定」保留 None 不当 False（R14 §6-3）。
- S22 通用模板包装器（TClassFactory/VectorClass/DynamicVectorClass/DistributionObject）先于 core 规则识别，避免按嵌入类型虚高判级（见 DISAGREE）。
- 写卡前已 grep 主台账；本片一行语义均标猜测，未写新 [已证] 发现。
- 未改 gamemd.exe / ddraw.dll / ra2youli\ 下任何文件；未写台账；未 git commit/push；未改 `COVERAGE\coverage.tsv`（只交 delta）；未用 Ghidra。

## 主要缺口
- 309 个零证据函数归 S22 兜底；284 个 TClassFactory 工厂方法虽明确是泛型基础设施，但可 P1 用其实例化 T 二次细化（见 UNKNOWNS）。
- 37 个 jmp8 洞目标全部「引用站点在洞内」，首指令多为 mov/cmp/test，疑似未建模代码块内短跳，不计入疑似真入口（见 UNKNOWNS）。
- S06/S13/S19 high=0：本片这几个子系统仅有泛型工厂/容器虚表（被归 S22），无 core 类直接命中（不是全局不存在）。
