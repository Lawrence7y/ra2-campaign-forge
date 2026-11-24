# EX-1 数据面：从原始 JSON 重建的 104 窗分类与 47 窗混杂控制表

本件为裁决 EX-1 数据面落实稿（域内候选件，未改台账/PENDING，未 commit）。全部数值从指定数据根的原始 `measure_w*.json` 顶层/嵌套字段直接读出，不推测、不补造；查不到的单元格写「缺」。只出文档，不含采样/注入/运行期探针代码。

## 0. 本次实际执行的检查（可复核）

**数据根（只读）**：`D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip`

**重建脚本（本轮自写，仅离线读 JSON / 源码片段 / 写文档）**：`D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/ex1_rebuild.py`

**执行命令**（`python -I -X utf8`，绝对路径，退出码 0；脚本内所有路径均为绝对路径，未使用 `..`）：

```bash
python -I -X utf8 'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/ex1_rebuild.py'
```

**副件**：机器可读重建结果 `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/ex1_rebuild.json`；完整 stdout 副本 `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/ex1_checks.txt`（含全库递归键扫描、47 窗帧沿端点核对、T34 分型核对、units0 源码定位）。关键输出摘录：

```text
COMMAND=python -I -X utf8 'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/ex1_rebuild.py'
INTERPRETER=C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe
DATA_ROOT=D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip
A total=104 root=3 child=101 deeper=0
A df_positive_total=63 root=0 child=63 deeper=0
A positive_25s=58 positive_4s=5 nonpositive=41
B all_avg_lt28=38 span25_avg_lt28=33 span4_avg_lt28=5 span25_both_lt28=22
B control=25 steady=22 stopped=11 unclassified=0
B steady_trip_ids=8 stopped_trip_ids=11 overlap=0
B steady_stall_min=0.103742 steady_stall_max=0.749879 n_stall_ge_1s=0
```

**口径**：`df = samples.f[-1] − samples.f[0]`（要求 `samples.t` 与 `samples.f` 等长且配对 ≥2）；`df>0` 为净正推进窗。名义窗长取顶层 `span_s`。分类只读 `stats.fps_avg` / `stats.fps_p50`。主指标 `fps_avg`，`fps_p50` 只作分型。

**已读的裁决/底账**：`RULING.md` 二、D-15（`RULING.md:69-93`，分层表 `RULING.md:75-85`，报数规定 `RULING.md:87`，混杂字段要求 `RULING.md:150`）、四、EX-1 行（`RULING.md:166`）；`FACTBASE.md` 二 a/b（`FACTBASE.md:38-84`）；`RECHECK.md` R1（`RECHECK.md:9-13`）。裁决记载值为对照目标，不是本件的数据来源。

## 1. 语料账（复现 104 = 子目录 101 + 根 3）

| 层级 | JSON 份数 | 其中净正推进 df>0 | 说明 |
|---|---:|---:|---|
| 趟根目录层（`.../qc161_u0400_trip/measure_w*.json`） | 3 | 0 | 根层 `measure_w0/w1/w2.json` 三个文件并非同一 trip（w0=T55j、w1/w2=T55h），全部 df=0 |
| 一层子目录层（各趟目录下 `measure_w*.json`） | 101 | 63 | 两层都扫，分别报数 |
| 更深层 | 0 | 0 | 无 |
| **合计** | **104** | **63** | `df<=0` 或样点不足共 41 |

与裁决 `RULING.md:77` 记载的 104=101+3 一致，无差异。根层三个文件的 `trip_id`（各 JSON 顶层字段）：`measure_w0.json` = `QC161-U0400-T55j`；`measure_w1.json` = `QC161-U0400-T55h`；`measure_w2.json` = `QC161-U0400-T55h`（`FACTBASE.md:59` 亦记 T55j / T55h / T55h）。

## 2. 净正推进窗、25 秒推进观测集、4 秒 settle 门控窗

| 口径 | 窗数 | 判据 |
|---|---:|---|
| 全部 JSON | 104 | 见第 1 节 |
| **净正推进窗 df>0** | **63** | `samples.f[-1] − samples.f[0] > 0` |
| 其中 **25 秒推进观测集** | **58** | `span_s=25.0` 且 df>0，完整性能观测分母 |
| 其中 **4 秒 settle 门控窗（剔除）** | **5** | `span_s=4.0` 且 df>0；排除 25 秒性能分析 |
| 非正推进/样点不足 | 41 | 见第 5 节 |

复现裁决 `RULING.md:78-84` 的 63 / 58 / 5 / 41，无差异。

### 2.1 5 个 4 秒 settle 门控窗（单列，不作同质性能样本）

| # | 绝对原件路径 | trip_id | span_s | stats.fps_avg | stats.fps_p50 | stats.max_stall_s | gate.ok | verdict | df |
|---:|---|---|---:|---:|---:|---:|---|---|---:|
| 1 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1_20261023e1/measure_w0.json` | `QC161-U0800-L1-20261023E1` | `4.0` | `2.0007963669736997` | `36.03116695987822` | `3.780845` | `false` | `no_advance` | `8` |
| 2 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1_20261023hb/measure_w0.json` | `QC161-U0800-L1-20261023HB` | `4.0` | `10.002424587719968` | `30.160180719827185` | `2.558256` | `false` | `no_advance` | `40` |
| 3 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1_20261023hc/measure_w0.json` | `QC161-U0800-L1-20261023HC` | `4.0` | `5.7501535290994275` | `31.894569311358797` | `3.286867` | `false` | `no_advance` | `23` |
| 4 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1_20261023k/measure_w0.json` | `QC161-U0800-L1-20261023K` | `4.0` | `4.502089757513919` | `24.922118380351534` | `3.266247` | `false` | `no_advance` | `18` |
| 5 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261031ha/measure_w0.json` | `QC161-U0800-L3-H8-20261031A` | `4.0` | `3.0007471110078` | `2.985901766203604` | `0.490684` | `false` | `no_advance` | `12` |

**字段来源**：`trip_id`、`span_s`、`verdict`、`gate.ok`、`samples.f`、`stats.*` 均为各绝对路径指向的原始 JSON 顶层/子字段；`df` 由 `samples.f[0]` 与 `samples.f[-1]` 相减（派生，非存储字段）。5 窗全部 `span_s=4.0`，且 `stats.fps_avg<28` 共 5 个（与 `FACTBASE.md:71` 的 4 秒行一致）。

## 3. 58 窗逐行三分类

| 类别 | 窗数 | 定义 | 独立 trip_id 数 |
|---|---:|---|---:|
| `avg>=28` 对照 | 25 | `stats.fps_avg >= 28` | 15 |
| **持续低速核心** | **22** | `stats.fps_avg<28` 且 `stats.fps_p50<28` | **8** |
| 停摆主导 | 11 | `stats.fps_avg<28` 且 `stats.fps_p50>=28` | 11 |
| 合计 | 58 | 25+22+11=58，无其他未分类窗 （0） | — |

**22 窗的 8 个独立 trip_id**（取自各 JSON 顶层 `trip_id`）：`QC161-U0800-L1C`、`QC161-U0800-L1D`、`QC161-U0800-L1E`、`QC161-U0800-L3`、`QC161-U0800-L3-H8-20261031B`、`QC161-U0800-L3-V3-20261101A`、`QC161-U0800-L3-V3-20261101B`、`QC161-U0800-L3-V4-20261101C`。11 停摆窗的 trip_id 共 11 个，与 22 窗 trip_id 集合交集 0 个。

**每行字段来源（统一说明，避免逐行重复）**：

- `绝对原件路径`：本次 `rglob('measure_w*.json')` 的实际绝对路径，绝对化后写入。
- `trip_id`：JSON 顶层 `trip_id`；`span_s`（名义窗长）：JSON 顶层 `span_s`。
- `stats.fps_avg` / `stats.fps_p50` / `stats.max_stall_s`：`stats` 对象内同名键，原值照抄（`repr(float)` 保留原精度），**未重算、未事后截尾**。
- `df`（若有）：派生量 `samples.f[-1] − samples.f[0]`，只用于判定可算性，不填入任何存储字段。

### 3.1 `avg>=28` 对照（25 窗）

| # | 绝对原件路径 | trip_id | span_s | stats.fps_avg | stats.fps_p50 | stats.max_stall_s |
|---:|---|---|---:|---:|---:|---:|
| 1 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T38/measure_w0.json` | `QC161-U0400-T38` | `25.0` | `31.202657842400296` | `31.015301396756165` | `0.112586` |
| 2 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T39/measure_w0.json` | `QC161-U0400-T39` | `25.0` | `31.240218431597572` | `31.10458604991512` | `0.040262` |
| 3 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T40/measure_w0.json` | `QC161-U0400-T40` | `25.0` | `31.001933032558473` | `31.134607354313214` | `0.166851` |
| 4 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T41/measure_w0.json` | `QC161-U0400-T41` | `25.0` | `29.121604134418185` | `31.051609321258557` | `1.72409` |
| 5 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T42/measure_w0.json` | `QC161-U0400-T42` | `25.0` | `30.081814174065407` | `31.10763396778743` | `0.942842` |
| 6 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T44/measure_w0.json` | `QC161-U0400-T44` | `25.0` | `30.042434759085854` | `30.945860231282527` | `0.983718` |
| 7 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T45/measure_w0.json` | `QC161-U0400-T45` | `25.0` | `28.52061342137603` | `31.128792270099602` | `1.880033` |
| 8 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1_20261023e4/measure_w0.json` | `QC161-U0800-L1-20261023E4` | `25.0` | `29.441409419151583` | `30.651481920341467` | `0.06958` |
| 9 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1a_20261020/measure_w0.json` | `QC161-U0800-L1-E2-shortpath` | `25.0` | `31.241755536728597` | `30.967134574515242` | `0.042096` |
| 10 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1a_20261020/measure_w1.json` | `QC161-U0800-L1-E2-shortpath` | `25.0` | `31.24059994446713` | `31.062556890464236` | `0.060218` |
| 11 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1a_20261020/measure_w2.json` | `QC161-U0800-L1-E2-shortpath` | `25.0` | `29.000675483728244` | `30.959752316022794` | `1.78159` |
| 12 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w1.json` | `QC161-U0800-L3-V4-20261101C` | `25.0` | `28.40179635682234` | `30.2016260596662` | `0.063188` |
| 13 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w2.json` | `QC161-U0800-L3-V4-20261101C` | `25.0` | `30.681571141892938` | `30.84258868525148` | `0.066098` |
| 14 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4d/measure_w0.json` | `QC161-U0800-L3-V4-20261101D` | `25.0` | `31.161901499229856` | `30.953714910025038` | `0.045516` |
| 15 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4d/measure_w1.json` | `QC161-U0800-L3-V4-20261101D` | `25.0` | `31.242757610757927` | `30.98728591654269` | `0.054657` |
| 16 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4d/measure_w2.json` | `QC161-U0800-L3-V4-20261101D` | `25.0` | `31.242972706367077` | `31.108359749514573` | `0.047961` |
| 17 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4e/measure_w0.json` | `QC161-U0800-L3-V4-20261101E` | `25.0` | `31.28012962485644` | `31.015541887682275` | `0.051982` |
| 18 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4e/measure_w1.json` | `QC161-U0800-L3-V4-20261101E` | `25.0` | `31.20209378530051` | `30.93489905073814` | `0.081078` |
| 19 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4e/measure_w2.json` | `QC161-U0800-L3-V4-20261101E` | `25.0` | `31.241971493369142` | `30.83878408877042` | `0.046068` |
| 20 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261023q/measure_w0.json` | `QC161-U0800-L3-20261023Q` | `25.0` | `31.12026165915985` | `31.343295275817844` | `0.068397` |
| 21 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261023q/measure_w1.json` | `QC161-U0800-L3-20261023Q` | `25.0` | `31.2807909035173` | `31.236431675397686` | `0.051041` |
| 22 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261023r/measure_w0.json` | `QC161-U0800-L3-20261023R` | `25.0` | `31.32041305360772` | `31.147117178470648` | `0.045683` |
| 23 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/t55k_20261020/measure_w0.json` | `QC161-U0400-T55k` | `25.0` | `31.24052309131934` | `31.014964715725064` | `0.048165` |
| 24 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/t55k_20261020/measure_w1.json` | `QC161-U0400-T55k` | `25.0` | `31.280439802982308` | `30.889605187168716` | `0.042802` |
| 25 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/t55k_20261020/measure_w2.json` | `QC161-U0400-T55k` | `25.0` | `31.242074348760568` | `30.95917723251618` | `0.042664` |

### 3.2 持续低速核心（22 窗 / 8 趟）

| # | 绝对原件路径 | trip_id | span_s | stats.fps_avg | stats.fps_p50 | stats.max_stall_s |
|---:|---|---|---:|---:|---:|---:|
| 1 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1c_20261021/measure_w0.json` | `QC161-U0800-L1C` | `25.0` | `9.16034567480517` | `9.68549268158322` | `0.246478` |
| 2 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1c_20261021/measure_w1.json` | `QC161-U0800-L1C` | `25.0` | `9.120620639994248` | `9.058188443883942` | `0.238382` |
| 3 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1c_20261021/measure_w2.json` | `QC161-U0800-L1C` | `25.0` | `10.000940928527887` | `10.821931076316062` | `0.224594` |
| 4 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1d_20261021/measure_w0.json` | `QC161-U0800-L1D` | `25.0` | `10.24001589250349` | `11.078061560330227` | `0.261453` |
| 5 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1d_20261021/measure_w1.json` | `QC161-U0800-L1D` | `25.0` | `10.240722052829652` | `10.500330235226475` | `0.238886` |
| 6 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1d_20261021/measure_w2.json` | `QC161-U0800-L1D` | `25.0` | `13.680390930853786` | `14.36284275118345` | `0.181353` |
| 7 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1e_20261021/measure_w0.json` | `QC161-U0800-L1E` | `25.0` | `11.641046809492279` | `12.825445684491065` | `0.216746` |
| 8 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1e_20261021/measure_w1.json` | `QC161-U0800-L1E` | `25.0` | `12.400814088645319` | `13.20655044889561` | `0.188701` |
| 9 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1e_20261021/measure_w2.json` | `QC161-U0800-L1E` | `25.0` | `14.601238126586205` | `16.499227011391007` | `0.181068` |
| 10 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v3a/measure_w0.json` | `QC161-U0800-L3-V3-20261101A` | `25.0` | `11.600218223305832` | `12.12124885195029` | `0.201816` |
| 11 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v3a/measure_w1.json` | `QC161-U0800-L3-V3-20261101A` | `25.0` | `14.041324770903133` | `14.224953413466212` | `0.129392` |
| 12 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v3a/measure_w2.json` | `QC161-U0800-L3-V3-20261101A` | `25.0` | `5.880161022330211` | `5.99403234114283` | `0.308852` |
| 13 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v3b/measure_w0.json` | `QC161-U0800-L3-V3-20261101B` | `25.0` | `16.720206461104823` | `18.093194425909058` | `0.141001` |
| 14 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v3b/measure_w1.json` | `QC161-U0800-L3-V3-20261101B` | `25.0` | `12.360771658250622` | `17.968612427801297` | `0.306968` |
| 15 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v3b/measure_w2.json` | `QC161-U0800-L3-V3-20261101B` | `25.0` | `11.200134401612683` | `13.146374361632706` | `0.261811` |
| 16 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w0.json` | `QC161-U0800-L3-V4-20261101C` | `25.0` | `18.520948494813613` | `19.81123852234025` | `0.103742` |
| 17 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261021/measure_w0.json` | `QC161-U0800-L3` | `25.0` | `8.760520725352274` | `9.501873769429576` | `0.2966` |
| 18 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261021/measure_w1.json` | `QC161-U0800-L3` | `25.0` | `11.960498609264949` | `13.726440281388168` | `0.224015` |
| 19 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261021/measure_w2.json` | `QC161-U0800-L3` | `25.0` | `10.200774442796618` | `10.82997694338584` | `0.270706` |
| 20 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261031hb/measure_w0.json` | `QC161-U0800-L3-H8-20261031B` | `25.0` | `6.787163913198485` | `9.379367267451554` | `0.493929` |
| 21 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261031hb/measure_w1.json` | `QC161-U0800-L3-H8-20261031B` | `25.0` | `4.731722368997936` | `5.468718383922593` | `0.749879` |
| 22 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261031hb/measure_w2.json` | `QC161-U0800-L3-H8-20261031B` | `25.0` | `10.600849382453761` | `13.88034861830716` | `0.580262` |

22 窗 `stats.max_stall_s` 的最小值/最大值（由本表数值直接取，未重算）：`0.103742` / `0.749879` 秒；与 `FACTBASE.md:80`、`RECHECK.md:55` 的 0.103742 / 0.749879 一致。按记录值，N=1 秒谓词覆盖 **0/22**（`RULING.md:135`、D-13.2）。

### 3.3 停摆主导（11 窗 / 11 趟）——整组「停摆观测、待归因」

| # | 绝对原件路径 | trip_id | span_s | stats.fps_avg | stats.fps_p50 | stats.max_stall_s |
|---:|---|---|---:|---:|---:|---:|
| 1 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T32/measure_w0.json` | `QC161-U0400-T32` | `25.0` | `19.280273394293534` | `30.912617755000618` | `9.574864` |
| 2 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T33/measure_w0.json` | `QC161-U0400-T33` | `25.0` | `17.760271234860046` | `31.11286034167601` | `10.814527` |
| 3 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T34/measure_w0.json` | `QC161-U0400-T34` | `25.0` | `0.36000229681454066` | `31.608659530882008` | `24.734761` |
| 4 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T36/measure_w0.json` | `QC161-U0400-T36` | `25.0` | `7.120450097895377` | `30.887363052622558` | `19.332772` |
| 5 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T38/measure_w1.json` | `QC161-U0400-T38` | `25.0` | `1.1600354785237839` | `30.82262503110947` | `24.077365` |
| 6 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T39/measure_w1.json` | `QC161-U0400-T39` | `25.0` | `1.2800392204023243` | `31.339906364758725` | `23.981746` |
| 7 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T43/measure_w0.json` | `QC161-U0400-T43` | `25.0` | `7.280394830378549` | `31.34840460294721` | `19.188367` |
| 8 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T47/measure_w0.json` | `QC161-U0400-T47` | `25.0` | `23.001589409827396` | `31.015349508641272` | `6.618178` |
| 9 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T49_u0800/measure_w0.json` | `QC161-U0400-T49` | `25.0` | `12.68033836215675` | `31.05059694802443` | `14.820029` |
| 10 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261023q/measure_w2.json` | `QC161-U0800-L3-20261023Q` | `25.0` | `4.800044198806858` | `31.125401128915527` | `21.155847` |
| 11 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261023r/measure_w1.json` | `QC161-U0800-L3-20261023R` | `25.0` | `19.36043390604397` | `31.00063861299945` | `9.436278` |

按 `RULING.md:111`、`RULING.md:117-120`，这 11 窗**既不作为已证在战卡顿正证，也不整组认定终局**；它们是 25 秒低 avg 观测的有效记录，不用于替代 22 窗持续低速机制，也不从 33 的原始计数中抹除。

## 4. ★ 混杂控制表（复查 R1 补强）：22 + 25 = 47 窗逐行五列

**列定义与字段来源**（缺一律写「缺」，不补造）：

1. `map_sha256`：原始 JSON 顶层 `map_sha256`。
2. `harness 版本/哈希`：本次对 104 份原始 JSON 做完整递归键扫描（含 `stats` / `gate` / `w1` / `h8` / `counters` 等），`harness` 或 `sha16` 类键命中 **0**（`ex1_checks.txt` 的 `D full_recursive_key_walk`、`D top_level_keys`）。按裁决 `RULING.md:150`、EX-1 `RULING.md:166` 指示，改查该趟目录 `_launch_result.json` 的 `harness_sha16` 与 `harness`（脚本文件绝对路径/版本名）；两者皆无时记「缺」，`_launch_result.json` 不存在也记「缺」并注明。
3. `实际采样起止帧`：`frame_edges[0][0]`（首个帧沿元素帧号）与 `frame_edges[-1][0]`（末个元素帧号），均为原始 JSON 顶层 `frame_edges` 数组元素 `[帧号, 时间]` 的第 0 位；不是派生量，也不重算。47 窗已核对 `frame_edges` 首末帧号与 `samples.f[0]`/`samples.f[-1]` 一致（`ex1_checks.txt` 的 `D grp47_frame_edges_endpoints_equal_samples_f=47/47`）。
4. `门控状态`：`gate.ok`（`gate` 对象内）与顶层 `verdict`。
5. `units0 及取值阶段`：`gate.units0`。**取值阶段为 settle 阶段起始读数**：源码 `qc151_trip.harness8_v4.py:5173-5196` 显示 settle 4 s 的 `_measure_poll_span` 之后，从 `s_counters` 取第一个非 null 的 `units`（`units0`），并在 `:5220-5224` 写入 `gate_block`；同型写法另见 `qc151_trip.harness6.py:4957-4967`、`qc151_trip.harness7.py:5025-5035`、`qc151_trip.harness8.py:5159-5169`、`qc151_trip.harness3.py:4051-4061`（本次只读定位，未执行这些源码）。`settle_s` 取自 JSON 顶层。按 `RULING.md:150`，它只是**起始/settle 负载描述，不冒充每个窗的实时同负载**。

### 4.1 22 个持续低速窗

| # | 绝对原件路径 | trip_id | map_sha256（顶层） | harness 版本/哈希（_launch_result.json） | 起帧→末帧（frame_edges[0][0]→[-1][0]） | gate.ok | verdict | gate.units0 | units0 阶段 | settle_s |
|---:|---|---|---|---|---|---|---|---|---|---:|
| 1 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1c_20261021/measure_w0.json` | `QC161-U0800-L1C` | `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` | 缺 / 缺 | `957` → `1186` | `true` | `ok` | `881` | settle 起始（见上） | `4.0` |
| 2 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1c_20261021/measure_w1.json` | `QC161-U0800-L1C` | `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` | 缺 / 缺 | `1187` → `1415` | `true` | `ok` | `881` | settle 起始（见上） | `0.0` |
| 3 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1c_20261021/measure_w2.json` | `QC161-U0800-L1C` | `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` | 缺 / 缺 | `1415` → `1665` | `true` | `ok` | `881` | settle 起始（见上） | `0.0` |
| 4 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1d_20261021/measure_w0.json` | `QC161-U0800-L1D` | `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` | 缺 / 缺 | `1095` → `1351` | `true` | `ok` | `874` | settle 起始（见上） | `4.0` |
| 5 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1d_20261021/measure_w1.json` | `QC161-U0800-L1D` | `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` | 缺 / 缺 | `1352` → `1608` | `true` | `ok` | `874` | settle 起始（见上） | `0.0` |
| 6 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1d_20261021/measure_w2.json` | `QC161-U0800-L1D` | `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` | 缺 / 缺 | `1609` → `1951` | `true` | `ok` | `874` | settle 起始（见上） | `0.0` |
| 7 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1e_20261021/measure_w0.json` | `QC161-U0800-L1E` | `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` | 缺 / 缺 | `1158` → `1449` | `true` | `ok` | `866` | settle 起始（见上） | `4.0` |
| 8 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1e_20261021/measure_w1.json` | `QC161-U0800-L1E` | `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` | 缺 / 缺 | `1449` → `1759` | `true` | `ok` | `866` | settle 起始（见上） | `0.0` |
| 9 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1e_20261021/measure_w2.json` | `QC161-U0800-L1E` | `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` | 缺 / 缺 | `1759` → `2124` | `true` | `ok` | `866` | settle 起始（见上） | `0.0` |
| 10 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v3a/measure_w0.json` | `QC161-U0800-L3-V3-20261101A` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `37a7c9cdf2ca97e3` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v3.py` | `434` → `724` | `true` | `ok` | `1349` | settle 起始（见上） | `4.0` |
| 11 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v3a/measure_w1.json` | `QC161-U0800-L3-V3-20261101A` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `37a7c9cdf2ca97e3` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v3.py` | `724` → `1075` | `true` | `ok` | `1349` | settle 起始（见上） | `0.0` |
| 12 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v3a/measure_w2.json` | `QC161-U0800-L3-V3-20261101A` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `37a7c9cdf2ca97e3` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v3.py` | `1075` → `1222` | `true` | `ok` | `1349` | settle 起始（见上） | `0.0` |
| 13 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v3b/measure_w0.json` | `QC161-U0800-L3-V3-20261101B` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `37a7c9cdf2ca97e3` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v3.py` | `454` → `872` | `true` | `ok` | `1352` | settle 起始（见上） | `4.0` |
| 14 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v3b/measure_w1.json` | `QC161-U0800-L3-V3-20261101B` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `37a7c9cdf2ca97e3` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v3.py` | `873` → `1182` | `true` | `ok` | `1352` | settle 起始（见上） | `0.0` |
| 15 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v3b/measure_w2.json` | `QC161-U0800-L3-V3-20261101B` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `37a7c9cdf2ca97e3` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v3.py` | `1182` → `1462` | `true` | `ok` | `1352` | settle 起始（见上） | `0.0` |
| 16 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w0.json` | `QC161-U0800-L3-V4-20261101C` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `38244d2907e7f7fa` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py` | `869` → `1332` | `true` | `ok` | `1229` | settle 起始（见上） | `4.0` |
| 17 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261021/measure_w0.json` | `QC161-U0800-L3` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | 缺 / 缺 | `387` → `606` | `true` | `ok` | `1342` | settle 起始（见上） | `4.0` |
| 18 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261021/measure_w1.json` | `QC161-U0800-L3` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | 缺 / 缺 | `606` → `905` | `true` | `ok` | `1342` | settle 起始（见上） | `0.0` |
| 19 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261021/measure_w2.json` | `QC161-U0800-L3` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | 缺 / 缺 | `905` → `1160` | `true` | `ok` | `1342` | settle 起始（见上） | `0.0` |
| 20 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261031hb/measure_w0.json` | `QC161-U0800-L3-H8-20261031B` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `dd5459fe0cf3461c` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8.py` | `437` → `606` | `true` | `ok` | `1347` | settle 起始（见上） | `4.0` |
| 21 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261031hb/measure_w1.json` | `QC161-U0800-L3-H8-20261031B` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `dd5459fe0cf3461c` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8.py` | `607` → `725` | `true` | `ok` | `1347` | settle 起始（见上） | `0.0` |
| 22 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261031hb/measure_w2.json` | `QC161-U0800-L3-H8-20261031B` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `dd5459fe0cf3461c` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8.py` | `726` → `991` | `true` | `ok` | `1347` | settle 起始（见上） | `0.0` |

### 4.2 25 个 `avg>=28` 对照窗

| # | 绝对原件路径 | trip_id | map_sha256（顶层） | harness 版本/哈希（_launch_result.json） | 起帧→末帧（frame_edges[0][0]→[-1][0]） | gate.ok | verdict | gate.units0 | units0 阶段 | settle_s |
|---:|---|---|---|---|---|---|---|---|---|---:|
| 1 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T38/measure_w0.json` | `QC161-U0400-T38` | `6fac3a3e60fb2ac959302add4343fc96cb1afb77a7f25529310e7fe74453e69c` | 缺 / 缺 | `130` → `910` | `true` | `ok` | `242` | settle 起始（见上） | `4.0` |
| 2 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T39/measure_w0.json` | `QC161-U0400-T39` | `6fac3a3e60fb2ac959302add4343fc96cb1afb77a7f25529310e7fe74453e69c` | 缺 / 缺 | `131` → `912` | `true` | `ok` | `242` | settle 起始（见上） | `4.0` |
| 3 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T40/measure_w0.json` | `QC161-U0400-T40` | `9a2495268be03f17f9599c9467c477f9529bb1f59f27f7e39e65562f95b57723` | 缺 / 缺 | `133` → `908` | `true` | `ok` | `242` | settle 起始（见上） | `4.0` |
| 4 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T41/measure_w0.json` | `QC161-U0400-T41` | `9a2495268be03f17f9599c9467c477f9529bb1f59f27f7e39e65562f95b57723` | 缺 / 缺 | `132` → `860` | `true` | `ok` | `242` | settle 起始（见上） | `4.0` |
| 5 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T42/measure_w0.json` | `QC161-U0400-T42` | `9a2495268be03f17f9599c9467c477f9529bb1f59f27f7e39e65562f95b57723` | 缺 / 缺 | `131` → `883` | `true` | `ok` | `242` | settle 起始（见上） | `4.0` |
| 6 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T44/measure_w0.json` | `QC161-U0400-T44` | `9a2495268be03f17f9599c9467c477f9529bb1f59f27f7e39e65562f95b57723` | 缺 / 缺 | `132` → `883` | `true` | `ok` | `242` | settle 起始（见上） | `4.0` |
| 7 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T45/measure_w0.json` | `QC161-U0400-T45` | `e7dee568b3a8ea9efc7b1d956d1d87aaceec60155a6b77035e8ecac94a6c5c87` | 缺 / 缺 | `132` → `845` | `true` | `ok` | `242` | settle 起始（见上） | `4.0` |
| 8 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1_20261023e4/measure_w0.json` | `QC161-U0800-L1-20261023E4` | `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` | `d019e8beecfb5fd8` / `D:\Project\ra2-campaign-forge\lead\goal1_harness7_20261023\qc151_trip.harness7.py` | `2821` → `3557` | `true` | `ok` | `702` | settle 起始（见上） | `4.0` |
| 9 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1a_20261020/measure_w0.json` | `QC161-U0800-L1-E2-shortpath` | `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` | 缺 / 缺 | `3849` → `4630` | `true` | `ok` | `732` | settle 起始（见上） | `4.0` |
| 10 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1a_20261020/measure_w1.json` | `QC161-U0800-L1-E2-shortpath` | `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` | 缺 / 缺 | `4631` → `5412` | `true` | `ok` | `732` | settle 起始（见上） | `0.0` |
| 11 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1a_20261020/measure_w2.json` | `QC161-U0800-L1-E2-shortpath` | `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` | 缺 / 缺 | `5412` → `6137` | `true` | `ok` | `732` | settle 起始（见上） | `0.0` |
| 12 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w1.json` | `QC161-U0800-L3-V4-20261101C` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `38244d2907e7f7fa` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py` | `1333` → `2043` | `true` | `ok` | `1229` | settle 起始（见上） | `0.0` |
| 13 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w2.json` | `QC161-U0800-L3-V4-20261101C` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `38244d2907e7f7fa` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py` | `2044` → `2811` | `true` | `ok` | `1229` | settle 起始（见上） | `0.0` |
| 14 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4d/measure_w0.json` | `QC161-U0800-L3-V4-20261101D` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `38244d2907e7f7fa` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py` | `920` → `1699` | `true` | `ok` | `1225` | settle 起始（见上） | `4.0` |
| 15 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4d/measure_w1.json` | `QC161-U0800-L3-V4-20261101D` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `38244d2907e7f7fa` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py` | `1700` → `2481` | `true` | `ok` | `1225` | settle 起始（见上） | `0.0` |
| 16 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4d/measure_w2.json` | `QC161-U0800-L3-V4-20261101D` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `38244d2907e7f7fa` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py` | `2482` → `3263` | `true` | `ok` | `1225` | settle 起始（见上） | `0.0` |
| 17 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4e/measure_w0.json` | `QC161-U0800-L3-V4-20261101E` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `38244d2907e7f7fa` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py` | `925` → `1707` | `true` | `ok` | `1189` | settle 起始（见上） | `4.0` |
| 18 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4e/measure_w1.json` | `QC161-U0800-L3-V4-20261101E` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `38244d2907e7f7fa` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py` | `1707` → `2487` | `true` | `ok` | `1189` | settle 起始（见上） | `0.0` |
| 19 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4e/measure_w2.json` | `QC161-U0800-L3-V4-20261101E` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `38244d2907e7f7fa` / `D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py` | `2488` → `3269` | `true` | `ok` | `1189` | settle 起始（见上） | `0.0` |
| 20 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261023q/measure_w0.json` | `QC161-U0800-L3-20261023Q` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `d019e8beecfb5fd8` / `D:\Project\ra2-campaign-forge\lead\goal1_harness7_20261023\qc151_trip.harness7.py` | `2955` → `3733` | `true` | `ok` | `974` | settle 起始（见上） | `4.0` |
| 21 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261023q/measure_w1.json` | `QC161-U0800-L3-20261023Q` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `d019e8beecfb5fd8` / `D:\Project\ra2-campaign-forge\lead\goal1_harness7_20261023\qc151_trip.harness7.py` | `3733` → `4515` | `true` | `ok` | `974` | settle 起始（见上） | `0.0` |
| 22 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261023r/measure_w0.json` | `QC161-U0800-L3-20261023R` | `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | `d019e8beecfb5fd8` / `D:\Project\ra2-campaign-forge\lead\goal1_harness7_20261023\qc151_trip.harness7.py` | `3100` → `3883` | `true` | `ok` | `941` | settle 起始（见上） | `4.0` |
| 23 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/t55k_20261020/measure_w0.json` | `QC161-U0400-T55k` | `93c2974b934acdc4e5c2d4ba042f1a98c647b1fa704ea1da92f27edc3dba2b69` | 缺 / 缺 | `3899` → `4680` | `true` | `ok` | `842` | settle 起始（见上） | `4.0` |
| 24 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/t55k_20261020/measure_w1.json` | `QC161-U0400-T55k` | `93c2974b934acdc4e5c2d4ba042f1a98c647b1fa704ea1da92f27edc3dba2b69` | 缺 / 缺 | `4681` → `5463` | `true` | `ok` | `842` | settle 起始（见上） | `0.0` |
| 25 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/t55k_20261020/measure_w2.json` | `QC161-U0400-T55k` | `93c2974b934acdc4e5c2d4ba042f1a98c647b1fa704ea1da92f27edc3dba2b69` | 缺 / 缺 | `5463` → `6244` | `true` | `ok` | `842` | settle 起始（见上） | `0.0` |

### 4.3 47 窗缺格统计与查阅来源（禁止补造）

| 列 | 47 窗中「缺」格数 |
|---|---:|
| map_sha256 | 0 |
| harness_sha16 | 25 |
| frame_edges 首末帧号 | 0 |
| gate.ok | 0 |
| verdict | 0 |
| gate.units0 | 0 |
| settle_s | 0 |

**harness 版本/哈希大面积缺失**：47 窗中有 **25** 窗从 `_launch_result.json` 取不到 `harness_sha16`，表中已逐行写「缺」。逐趟查阅的绝对路径（全部为本数据根下的绝对路径，只读；不存在者如实标注）：

- `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T38/_launch_result.json` — **不存在**；键：无
- `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T39/_launch_result.json` — **不存在**；键：无
- `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T40/_launch_result.json` — **不存在**；键：无
- `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T41/_launch_result.json` — **不存在**；键：无
- `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T42/_launch_result.json` — **不存在**；键：无
- `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T44/_launch_result.json` — **不存在**；键：无
- `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T45/_launch_result.json` — **不存在**；键：无
- `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1a_20261020/_launch_result.json` — **不存在**；键：无
- `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1c_20261021/_launch_result.json` — 存在；键：`argv`、`carriers_deleted`、`duration_s`、`leftover_procs`、`out_dir`、`rc`、`trip_id`；`argv[0]` 脚本路径为 `D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_harness_merge_20261021\qc151_trip.harness3.py`，但该件**无 `harness_sha16` 字段**，按铁律不据文件名/他趟补造哈希
- `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1d_20261021/_launch_result.json` — 存在；键：`argv`、`carriers_deleted`、`duration_s`、`leftover_procs`、`out_dir`、`rc`、`trip_id`；`argv[0]` 脚本路径为 `D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_harness_merge_20261021\qc151_trip.harness3.py`，但该件**无 `harness_sha16` 字段**，按铁律不据文件名/他趟补造哈希
- `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1e_20261021/_launch_result.json` — 存在；键：`argv`、`carriers_deleted`、`duration_s`、`leftover_procs`、`out_dir`、`rc`、`trip_id`；`argv[0]` 脚本路径为 `D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_harness_merge_20261021\qc151_trip.harness3.py`，但该件**无 `harness_sha16` 字段**，按铁律不据文件名/他趟补造哈希
- `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261021/_launch_result.json` — 存在；键：`argv`、`carriers_deleted`、`duration_s`、`leftover_procs`、`out_dir`、`rc`、`trip_id`；`argv[0]` 脚本路径为 `D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_harness_merge_20261021\qc151_trip.harness3.py`，但该件**无 `harness_sha16` 字段**，按铁律不据文件名/他趟补造哈希
- `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/t55k_20261020/_launch_result.json` — **不存在**；键：无

此外，对全部 104 份 `measure_w*.json` 做过**完整递归键扫描**（不只顶层；结果在 `ex1_checks.txt`）：**没有任何 harness 版本或哈希键**。对根目录层查过 `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip` 下文件名含 `harness`/`launch` 的清单（`_l1b_launch_out.txt`、`_launch_l1b.py`、`t55_launch.log`、`t55_launch_4b.log`、`t55_launch_c.log`、`t55_launch_d.log`），这些是发射日志/脚本，不是 47 窗所属趟的 `harness_sha16` 记录，不用于代填。

**47 窗行覆盖核对**：22 + 25 = 47 行，与 4.1/4.2 两表行数之和一致；路径均为绝对路径。不同版本/地图/相位不得合成因果配对（`RULING.md:150`）。

## 5. 41 个不可算窗单列（零推进 / 样点不足 / 计数回绕）

判据统一为：`df = samples.f[-1] − samples.f[0]` 非正，或样点不足（`samples.t` / `samples.f` 长度不等或配对 <2）；这些窗的 `stats.fps_avg` / `stats.fps_p50` 为 null 或不可作可算 fps 样本。按 `RULING.md:85`，保留终局、复位、门控失败等审计用途，**不得统称 41 个冻结**。

| # | 绝对原件路径 | trip_id | span_s | 判据 | 首沿帧号 | 末沿帧号 | df | 样点对数 | stats.fps_avg | verdict |
|---:|---|---|---:|---|---:|---:|---:|---:|---:|---|
| 1 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T32/measure_w1.json` | `QC161-U0400-T32` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `778` | `778` | `0` | `12501` | `缺` | `ok` |
| 2 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T32/measure_w2.json` | `QC161-U0400-T32` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `778` | `778` | `0` | `12501` | `缺` | `ok` |
| 3 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T33/measure_w1.json` | `QC161-U0400-T33` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `738` | `738` | `0` | `12501` | `缺` | `ok` |
| 4 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T33/measure_w2.json` | `QC161-U0400-T33` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `738` | `738` | `0` | `12501` | `缺` | `ok` |
| 5 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T34/measure_w1.json` | `QC161-U0400-T34` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `302` | `302` | `0` | `12501` | `缺` | `ok` |
| 6 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T34/measure_w2.json` | `QC161-U0400-T34` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `302` | `302` | `0` | `12501` | `缺` | `ok` |
| 7 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T36/measure_w1.json` | `QC161-U0400-T36` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `310` | `310` | `0` | `12501` | `缺` | `ok` |
| 8 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T36/measure_w2.json` | `QC161-U0400-T36` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `310` | `310` | `0` | `12501` | `缺` | `ok` |
| 9 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T38/measure_w2.json` | `QC161-U0400-T38` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `940` | `940` | `0` | `12501` | `缺` | `ok` |
| 10 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T39/measure_w2.json` | `QC161-U0400-T39` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `945` | `945` | `0` | `12502` | `缺` | `ok` |
| 11 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T40/measure_w1.json` | `QC161-U0400-T40` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `908` | `908` | `0` | `12501` | `缺` | `ok` |
| 12 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T40/measure_w2.json` | `QC161-U0400-T40` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `908` | `908` | `0` | `12501` | `缺` | `ok` |
| 13 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T41/measure_w1.json` | `QC161-U0400-T41` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `860` | `860` | `0` | `12502` | `缺` | `ok` |
| 14 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T41/measure_w2.json` | `QC161-U0400-T41` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `860` | `860` | `0` | `12501` | `缺` | `ok` |
| 15 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T42/measure_w1.json` | `QC161-U0400-T42` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `883` | `883` | `0` | `12501` | `缺` | `ok` |
| 16 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T42/measure_w2.json` | `QC161-U0400-T42` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `883` | `883` | `0` | `12501` | `缺` | `ok` |
| 17 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T43/measure_w1.json` | `QC161-U0400-T43` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `314` | `314` | `0` | `12502` | `缺` | `ok` |
| 18 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T43/measure_w2.json` | `QC161-U0400-T43` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `314` | `314` | `0` | `12501` | `缺` | `ok` |
| 19 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T44/measure_w1.json` | `QC161-U0400-T44` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `883` | `883` | `0` | `12501` | `缺` | `ok` |
| 20 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T44/measure_w2.json` | `QC161-U0400-T44` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `883` | `883` | `0` | `12502` | `缺` | `ok` |
| 21 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T45/measure_w1.json` | `QC161-U0400-T45` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `845` | `845` | `0` | `12501` | `缺` | `ok` |
| 22 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T45/measure_w2.json` | `QC161-U0400-T45` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `845` | `845` | `0` | `12501` | `缺` | `ok` |
| 23 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T47/measure_w1.json` | `QC161-U0400-T47` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `708` | `708` | `0` | `12501` | `缺` | `ok` |
| 24 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T47/measure_w2.json` | `QC161-U0400-T47` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `708` | `708` | `0` | `12501` | `缺` | `ok` |
| 25 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T49_u0800/measure_w1.json` | `QC161-U0400-T49` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `448` | `448` | `0` | `12501` | `缺` | `ok` |
| 26 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T49_u0800/measure_w2.json` | `QC161-U0400-T49` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `448` | `448` | `0` | `12501` | `缺` | `ok` |
| 27 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1_20261023/measure_w0.json` | `QC161-U0800-L1-20261023` | `4.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `3514` | `3514` | `0` | `2001` | `缺` | `no_advance` |
| 28 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1_20261023b/measure_w0.json` | `QC161-U0800-L1-20261023B` | `4.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `3594` | `3594` | `0` | `2002` | `缺` | `no_advance` |
| 29 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1_20261023c/measure_w0.json` | `QC161-U0800-L1-20261023C` | `4.0` | 样点不足（samples.t/f 配对 <2 或长度不等） | `缺` | `缺` | `缺` | `0` | `缺` | `no_advance` |
| 30 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1_20261023e4/measure_w1.json` | `QC161-U0800-L1-20261023E4` | `25.0` | 计数回绕（末沿帧号 − 首沿帧号 < 0） | `3557` | `0` | `-3557` | `12501` | `缺` | `ok` |
| 31 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1_20261023e4/measure_w2.json` | `QC161-U0800-L1-20261023E4` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `0` | `0` | `0` | `5949` | `缺` | `ok` |
| 32 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v3c/measure_w0.json` | `QC161-U0800-L3-V3-20261101C` | `0.0` | 样点不足（samples.t/f 配对 <2 或长度不等） | `缺` | `缺` | `缺` | `0` | `缺` | `frame_wait_timeout` |
| 33 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4b/measure_w0.json` | `QC161-U0800-L3-V4-20261101B` | `0.0` | 样点不足（samples.t/f 配对 <2 或长度不等） | `缺` | `缺` | `缺` | `0` | `缺` | `frame_wait_timeout` |
| 34 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4f/measure_w0.json` | `QC161-U0800-L3-V4-20261101F` | `4.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `0` | `0` | `0` | `2001` | `缺` | `no_advance` |
| 35 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4g/measure_w0.json` | `QC161-U0800-L3-V4-20261101G` | `4.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `0` | `0` | `0` | `2002` | `缺` | `no_advance` |
| 36 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4h/measure_w0.json` | `QC161-U0800-L3-V4-20261101H` | `0.0` | 样点不足（samples.t/f 配对 <2 或长度不等） | `缺` | `缺` | `缺` | `0` | `缺` | `frame_wait_timeout` |
| 37 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261023/measure_w0.json` | `QC161-U0800-L3-20261023` | `4.0` | 样点不足（samples.t/f 配对 <2 或长度不等） | `缺` | `缺` | `缺` | `0` | `缺` | `no_advance` |
| 38 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261023r/measure_w2.json` | `QC161-U0800-L3-20261023R` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `4367` | `4367` | `0` | `12501` | `缺` | `ok` |
| 39 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/measure_w0.json` | `QC161-U0400-T55j` | `4.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `3950` | `3950` | `0` | `2002` | `缺` | `no_advance` |
| 40 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/measure_w1.json` | `QC161-U0400-T55h` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `373` | `373` | `0` | `12501` | `缺` | `ok` |
| 41 | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/measure_w2.json` | `QC161-U0400-T55h` | `25.0` | 零推进（末沿帧号 − 首沿帧号 = 0） | `373` | `373` | `0` | `12502` | `缺` | `ok` |

**分因计数**：样点不足（samples.t/f 配对 <2 或长度不等） = 5；计数回绕（末沿帧号 − 首沿帧号 < 0） = 1；零推进（末沿帧号 − 首沿帧号 = 0） = 35；合计 41。计数回绕窗即 `l1_20261023e4/measure_w1.json`（首沿 3557 → 末沿 0，df=−3557，`stats.logic_frames=-3557`），单列为计数回绕，不并入零推进。5 个样点不足窗的 `samples.t/f` 均为空数组、`stats.note=insufficient samples`，其中 3 个 `span_s=0.0` / `verdict=frame_wait_timeout`，另 2 个 `span_s=4.0` / `verdict=no_advance`。

## 6. 口径解释：33 与 38 的分母差异

| 计数 | 本次重建值 | 分母 / 组成 | 能否当同质性能样本 |
|---|---:|---|---|
| 全部 104 份中 `stats.fps_avg<28` | 38 | 分母为全部 104 份（根层 3、零推进/样点不足窗的 `fps_avg` 为 null，不贡献命中）；命中 = 25 秒低 avg 33 + 4 秒低 avg 5 | **不能**：混入 5 个 4 秒门控窗 |
| **25 秒低 avg 总计** | **33** | 仅 `span_s=25.0`；= 22 持续低速 + 11 停摆主导 | 是「全部 25 秒低 avg 观测」总数，但两类证据用途不同 |
| 25 秒双低（avg<28 且 p50<28） | 22 | 22 核心 | 核心持续低速分析样本 |
| 4 秒 `span_s=4.0` 且 avg<28 | 5 | 5 个 settle 门控窗 | 排除 25 秒性能分析 |

**明确写出**：`38` 是**混入 5 个 4 秒门控窗的旧混合计数**（38 = 33 + 5），来自未按时长分层的 `avg<28` 全量筛选（`FACTBASE.md:69-71`）；`33` 是**仅 25 秒窗的低 avg 总数**（33 = 22 + 11，见 `RULING.md:81-83`、`FACTBASE.md:70`）。二者分母不同，**38 不得再当同质性能样本数**，也不得把 22/47 写成全体真机卡顿发生率；22 窗与 25 对照的 47 窗分析集必须标为「排除 11 个待归因停摆窗后的持续低速/对照分析集」（`RULING.md:87`）。本次重建 38 / 33 / 22 / 11 / 5 与裁决分层逐项一致。

## 7. `p50` 高不得记为健康

本次直接读原件 `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T34/measure_w0.json` 得：`stats.fps_avg=0.36000229681454066`（`<28`），`stats.fps_p50=31.608659530882008`（`>=28`），`stats.max_stall_s=24.734761`，`frame_edges` 共 10 条，首末帧号 293→302（df=9）。按第 3 节定义它归入**停摆主导**（第 3.3 节表内），**不是健康/对照窗**；核对行见 `ex1_checks.txt` 的 `D t34_path=... in_stopped=True in_control=False`。

依据：`RULING.md:89-91` 规定主指标维持 `fps_avg`，`p50` 仅作分型、不用于给停摆窗出健康结论；`FACTBASE.md:86-103` 记该窗采样无 >10ms 缺口却停约 24.734760 秒而 p50 仍 31.608660 fps；`RECHECK.md:56-57` 复查也读得同一组原存值。本件**声明：任何 `fps_p50>=28` 且 `fps_avg<28` 的窗一律列「停摆观测、待归因」，不得记为健康**，也整组不得判为已证终局（`RULING.md:111`）。

## 8. 逐条验收自查与边界

| 判据 | 本次是否做到 | 证据位置 |
|---|---|---|
| 1 语料账 104=101+3，两层分别报份数 | 是 | 第 1 节；`ex1_checks.txt` 的 `A total=104 root=3 child=101 deeper=0` |
| 2 净正推进窗 63 | 是 | 第 2 节；`A df_positive_total=63` |
| 3 58 / 5 分开列 | 是 | 第 2 节及第 2.1 节 5 窗逐行表 |
| 4 58 窗三分类逐行、字段来源、22 窗独立 trip_id=8 | 是 | 第 3.1/3.2/3.3 节；8 个 trip_id 明列；`B steady_trip_ids=8` |
| 5 47 窗逐行五列混杂控制、缺写「缺」并标查阅来源 | 是（harness 哈希大面积「缺」，如实登记） | 第 4.1/4.2/4.3 节；`D grp47=47 missing={"harness_sha16": 25}` |
| 6 41 个不可算窗单列 + 判据 | 是 | 第 5 节；`B reasons=...` |
| 7 33 与 38 分母差异 | 是 | 第 6 节 |
| 8 p50 高不得记为健康（archive_T34/measure_w0.json） | 是 | 第 7 节 |

**边界与未做**：未启动 gamemd.exe / ra2loader.exe / YURI，未 taskkill，未读活进程内存，未改任何既有件，未 commit。未重算 104 份的 `stats`（只照抄原存值），未重算 22 窗的 `max_stall_s`（只取第 3.2 节原存值），未目视/OCR 任何 PNG，未核截图时序/哈希，未做真机发射或运行期采样。写入仅 `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/EX1_DATAFACE.md`、机器可读副件 `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/ex1_rebuild.json` 与 stdout 副本 `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/ex1_checks.txt`，均在指定写域内。

生成时间（UTC）：`2026-11-04T13:17:57.486405+00:00`；解释器：`C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe`。
