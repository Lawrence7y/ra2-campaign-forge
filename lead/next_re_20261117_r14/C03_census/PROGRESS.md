# C03 · P0 全镜像普查第 3 片 — PROGRESS

> 卡号 C03｜执行 2026-11-17｜目标 `ra2youli\gamemd.exe` (ImageBase 0x400000)
> 片：`function_atlas.tsv` 逻辑行 **2585–3876**（Python 索引 2584:3876，**1292** 函数），入口范围 **0x004A60D0–0x004F183C**
> 通道：capstone 5.0.7 (`skipdata=True`, 全 .text 解出 1,394,120 条) + pefile + audit_lib.sweep_calls；**本卡未用 Ghidra**

## 结论表（分级 + 证据路径）

| 项 | 值 | 分级 | 证据 |
|---|---|---|---|
| 本片函数数 | **1292** | [已证] | `EVIDENCE/slice_raw.tsv`（1292 行）；`work/verify_core.py` |
| 自动证据覆盖 | vtable 槽命中 958 / YRpp·kb 显式名 64 / 台账名 1 / 源文件模块 19 / 带字符串 41 / 带导入 51 | [已证] | `EVIDENCE/vtmap_hits.tsv`, `known_hits.tsv`, `slice_raw.tsv`, `work/meta.json` |
| 分类完成 | 1292/1292 全部给 Sxx + 置信度 + 一行语义 | [已证] | `coverage_delta.tsv`, `EVIDENCE/classification_trace.tsv` |
| 高置信(high) | **427 / 1292 = 33.1%** | [已证] | `work/verify_core.py` 双路复算；判据见下 |
| 证据分级 | [已证]64 / [静态推断]367 / [未证]861 | [已证] | `coverage_delta.tsv` 第 5 列；`classification_trace.tsv` grade 列 |
| 无法归类 | 151（其中真零证据 137） | [已证] | source=none；见 UNKNOWNS.md |
| atlas 空洞入口 | **41** | [已证] | `atlas_gaps.tsv`（41 行）；`work/verify_core.py` 复算 |

## 给审计员的三个核心数字（及复算方法）

1. **本片函数数 = 1292**
   复算：`wc -l coverage_delta.tsv` = 1292；或 `audit_lib.load_func_atlas()` 返回 rows 后 `len(rows[2584:3876])` = 1292。
2. **high 置信计数 = 427**
   复算：`python work/verify_core.py`（trace JSON 与 `EVIDENCE/classification_trace.tsv` 第 3 列 `conf==high` 双路都 = 427）。
   high 判据（同 C02）：(A) 有 YRpp/kb 明确地址名且归属一致 = 64；(B) 是 RTTI 类 vtable 槽且该类在 PLAN §1 唯一映射到某 Sxx（core=True）= 363。
   分布：S10 118 + S11 108 + S09 78 + S07 44 + S12 22 + S20 23 + S06 11 + S18 8 + S08 7 + S03 6 + S05 2 = 427。
3. **atlas 空洞入口数 = 41**
   复算：`(wc -l atlas_gaps.tsv)-1` = 41；独立通道：`sweep_targets.json` 全部 call/jmp rel32 目标 ∩ [0x4A60D0,0x4F183C) ∩ `owner()==None`（区间包含判据）= 41。
   已知例 `0x4824D4` 属 C02 片，**不在本片范围**，已确认未混入（verify_core 打印 `4824D4_in=False`）。

## 各子系统计数（high 占比分母 = 427）

| S | n | high | S | n | high | S | n | high |
|---|---|---|---|---|---|---|---|---|
| S01 | 3 | 0 | S08 | 7 | 7 | S15 | 1 | 0 |
| S02 | 1 | 0 | S09 | 106 | 78 | S16 | 0 | 0 |
| S03 | 8 | 6 | S10 | 126 | 118 | S17 | 1 | 0 |
| S04 | 1 | 0 | S11 | 112 | 108 | S18 | 9 | 8 |
| S05 | 8 | 2 | S12 | 22 | 22 | S19 | 2 | 0 |
| S06 | 40 | 11 | S13 | 4 | 0 | S20 | 26 | 23 |
| S07 | 58 | 44 | S14 | 11 | 0 | S21 | 1 | 0 |

S22（通用容器/数学/字符串/第三方库）= **745**，high=0。无法归类（source=none）= **151**（真零证据 137 + 弱信号未命中规则 14）。

## 说明

- 本片 0x4Axxxx–0x4Fxxxx 以 **Locomotion 族(S11 112)、Foot/Unit/Infantry/Aircraft(S10 126)、UI 控件(S09 106)、Display/Surface(S07 58)、Map(S06 40)、特效 DiskLaser/EBolt/EMPulse(S20 26)** 为主；S22 高达 745 是本片真实分布——大量 `T_VectorClass_*`/`T_DynamicVectorClass_*` 模板容器虚表（589 个），每个 6–7 槽均为通用容器方法，按 C02 约定归 S22（非元素类型）。
- grade=[已证] 的 64 个均来自 YRpp 头文件 `JMP_THIS`/`INI_READ` 与 re_atlas/kb 的明确地址名；语义一行仍为猜测，均标 `[未证]`，未升级。
- 与 C02 的类→Sxx 映射保持一致（BuildingClass/TechnoClass→S05，Unit/Infantry/Aircraft→S10，UI gadget→S09 等）；本片新增映射（Locomotion→S11、Factory→S12、DiskLaser/EBolt/EMPulse→S20、MissionClass→S10）的理由与歧义见 DISAGREE.md。
- 已 grep 台账：0x4C9150（本片 [已证] 名 "AbstractClass"）台账 §20008 记为共享 `xor eax,eax;ret` 空桩，见 DISAGREE.md；未把任何猜测写成 [已证]。
- 本卡只交 delta，未改 `COVERAGE\coverage.tsv`，未写台账，未改游戏文件，未 git commit；capstone 全程 skipdata=True，boundary_check 超限返回 unknown。
