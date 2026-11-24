# C02 · P0 全镜像普查第 2 片 — PROGRESS

> 卡号 C02｜执行 2026-11-17｜目标 `ra2youli\gamemd.exe` (ImageBase 0x400000)
> 片：`function_atlas.tsv` 逻辑行 **1293–2584**（物理行 1294–2585），地址范围 **0x00456E00–0x004A60CB**（入口 min/max）
> 通道：capstone 5.0.7 (`skipdata=True`, 全 .text 解出 1,394,120 条) + pefile + audit_lib.sweep_calls；**本卡未用 Ghidra**

## 结论表（分级 + 证据路径）

| 项 | 值 | 分级 | 证据 |
|---|---|---|---|
| 本片函数数 | **1292** | [已证] | `EVIDENCE/slice_raw.tsv`（1292 行）；`work/verify_core.py` |
| 自动证据覆盖率 | 有 vtable 槽 753 / 已知函数名 144 / 源文件归属 7 | [已证] | `EVIDENCE/vtmap_hits.tsv`, `EVIDENCE/known_hits.tsv`, `EVIDENCE/callgraph.tsv` |
| 分类完成 | 1292/1292 全部给 Sxx + 置信度 + 一行语义 | [已证] | `coverage_delta.tsv`, `EVIDENCE/classification_trace.tsv` |
| 高置信(high) | **840 / 1292 = 65.0%** | [已证] | `work/verify_core.py` 复算；判据见下 |
| 证据分级 | [已证]143 / [静态推断]703 / [未证]446 | [已证] | `EVIDENCE/classification_trace.tsv` 的 grade 列 |
| 无法归类 | 220（其中真零证据 211） | [已证] | source=none；见 UNKNOWNS.md |
| atlas 空洞入口 | **111**（含已知例 `0x4824D4`） | [已证] | `atlas_gaps.tsv`；`work/verify_core.py` 复算 |

## 给审计员的三个核心数字（及复算方法）

1. **本片函数数 = 1292**
   复算：`wc -l coverage_delta.tsv` = 1292；或 `python -c "import sys;sys.path.insert(0,r'…\\_lead_audit');import audit_lib as a;r,_=a.load_func_atlas();print(len(r[1292:2584]))"` = 1292。
2. **high 置信计数 = 840**
   复算：在 `EVIDENCE/classification_trace.tsv` 数第 3 列 `conf==high` 的行 = 840；high 判据 = (A) 有 YRpp/kb 明确地址名(self_known) 且归属一致，或 (B) 函数是某 RTTI 类的 vtable 槽且该类在 PLAN §1 唯一映射到某 Sxx（core=True）。`S07 358 + S13 66 + S12 67 + S18 63 + S06 58 + S05 56 + S09 43 + S04 33 + S03 26 + S17 19 + S21 15 + S08 12 + S20 12 + S10 12 = 840`。
3. **atlas 空洞入口数 = 111**
   复算：`(wc -l atlas_gaps.tsv)-1` = 111；独立通道：`sweep_targets.json` 全部 call/jmp rel32 目标 ∩ [0x456E00,0x4A60CB) ∩ `owner()==None`（区间包含判据，`audit_lib.load_func_atlas` 的 entry+size）= 111。`0x4824D4` 必须在内。

## 各子系统计数（high 占比分母 = 840）

| S | n | high | S | n | high | S | n | high |
|---|---|---|---|---|---|---|---|---|
| S01 | 2 | 0 | S08 | 14 | 12 | S15 | 0 | 0 |
| S02 | 1 | 0 | S09 | 48 | 43 | S16 | 0 | 0 |
| S03 | 36 | 26 | S10 | 12 | 12 | S17 | 21 | 19 |
| S04 | 79 | 33 | S11 | 0 | 0 | S18 | 64 | 63 |
| S05 | 60 | 56 | S12 | 81 | 67 | S19 | 2 | 0 |
| S06 | 112 | 58 | S13 | 74 | 66 | S20 | 12 | 12 |
| S07 | 377 | 358 | S14 | 0 | 0 | S21 | 22 | 15 |

S22（通用容器/数学/字符串/第三方库）= **275**，high=0。无法归类（source=none）= **220**（真零证据 211 + 有弱信号未命中规则 9）。

## 说明

- 本片 0x45xxxx–0x4Axxxx 覆盖 BuildingType/Bullet/Cell/Map/CCINI/Convert/Blitter 模板 + 网络连接类 + UI 控件 + 战役得分 ⇒ S07(377) 与 S22(275，Vector/DynamicVector/TypeList 容器) 占多数，符合地址分布。
- grade=[已证] 的 143 个均是 YRpp 头文件 `JMP_THIS/INI_READ` 明确地址名或 re_atlas/kb 已证名；已剔除正则误抓裸词（setne/this/ReadString…）。语义一行仍按普查要求为猜测，未升级为 [已证]。
- 本卡只交 delta，未改 `COVERAGE\coverage.tsv`，未写台账，未改游戏文件，未 git commit。
