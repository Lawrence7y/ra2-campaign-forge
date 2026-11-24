# D-15 落实候选稿（EX-1／EX-2／EX-3 组装件）

## 1. 抬头

> **本件性质**：本件是 **D-15 的落实候选稿**，由三份碎片拼接而成；依据 `RULING.md`（**GPT 6.1 裁决**）与 `RECHECK.md`（**独立复查**）。组装员只做拼接与格式化，**不改写三份碎片的任何结论、数字或措辞**。
>
> **依据件（本轮只读）**：
> - D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\ADJUDICATE_a70d00e5\RULING.md —— `RULING.md:1`（D-15 / D-13 裁决书）、`:5`（D-15 采用修正 A）、`:69-93`（D-15.1 数据面裁定与分层表）、`:162-170`（EX-1 `:166` / EX-2 `:167` / EX-3 `:168` 动作表，指定本件路径与「数据面」「追加勘误候选」「11窗证据表」三段）。
> - D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\ADJUDICATE_a70d00e5\RECHECK.md —— `RECHECK.md:1`（裁决书复查）、`:3`（判定「需修改后执行」，两处落实文书漏洞）、`:34`、`:82`（复查阶段未重做项）。
>
> **三段照录来源**（均在写域 `.../impl_f4bcf30c/`）：第 2 段 ← `EX1_DATAFACE.md`（347 行，CRLF 原样）；第 3 段 ← `EX2_ERRATA.md`（146 行，LF 原样）；第 4 段 ← `EX3_STALL_EVIDENCE.md`（284 行，LF 原样）。
>
> **冲突处置**：三份碎片之间若有数字或结论冲突，一律**原样保留**，并在冲突处以 `⚠️【组装员冲突标注】`（`<!-- BEGIN/END ASSEMBLER CONFLICT NOTE C* -->` 包裹）醒目标注；**不调和、不换算、不删除、不判定孰是孰非**。标注块为组装员添加，不属于任何碎片原文；去掉标注块后，各段与对应碎片逐字节一致。
>
> **边界**：零真机（未启动 gamemd.exe / ra2loader.exe / YURI，未 taskkill，未读活进程内存）；`gamemd.exe`、真机 json/png、三路核验件、`RULING.md`、`FACTBASE.md`、`RECHECK.md`、`GOAL_THREE_TARGETS_20261018.md`、`PENDING_DECISIONS.md` 全部只读；不改台账、不改 PENDING、不 commit；只出文档，未写任何采样/注入/运行期探针脚本；python 一律 `python -I -X utf8`，路径一律绝对路径。

---

## 2. 数据面 ← `EX1_DATAFACE.md` 全文

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

<!-- BEGIN ASSEMBLER CONFLICT NOTE C1 -->
> ⚠️ **【组装员冲突标注 · C1｜同一批停顿的 `max_stall_s` 数值表述差异；原样保留，不调和】**
> `EX1_DATAFACE.md:152` 记 `archive_T32/w0` 的 `stats.max_stall_s=9.574864`、`:154` 记 `archive_T34/w0` 为 `24.734761`、`:156` 记 `archive_T38/w1` 为 `24.077365`；
> `EX3_STALL_EVIDENCE.md:99` / `:101` / `:103` 分别写 `9.574864 s` / `24.734761s` / `24.077365 s`；
> `EX2_ERRATA.md:88`（§545.3(1)）对 T32/w0 与 T38/w1 分别记作 `max_stall=9.575s`（同段另引 `9.574`）与 `24.077s`，并另记 T32 w1/w2 `24.999s`、`l3_20261023r` w2 `24.998s`；
> `EX1_DATAFACE.md:330` 转述 `FACTBASE.md:86-103` 又写「停约 24.734760 秒」。
> **上述不同数值全部照录；未判定差异成因、未作换算、未选定唯一值。**（本块为组装员添加，非任何碎片原文）
<!-- END ASSEMBLER CONFLICT NOTE C1 -->

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

<!-- BEGIN ASSEMBLER CONFLICT NOTE C2 -->
> ⚠️ **【组装员冲突标注 · C2｜零推进／不可算窗计数口径不同；原样保留，不调和】**
> `EX1_DATAFACE.md:313` 把 41 拆为「样点不足 5 ＋ 计数回绕 1 ＋ 零推进 35」；
> `EX3_STALL_EVIDENCE.md:56` 把 41 拆为「`span25&nonpos=31` ＋ `span_other&nonpos=10`」，`:140` 另引「32 个零推进窗中的 11 个未充分覆盖窗」；
> `EX2_ERRATA.md:79` 引 `_LEADER_FROZEN_29_20261104.md:12` 判据计 **29 窗**，`EX2_ERRATA.md:94` 引 `S543_FREEZE_WAS_SCORESCREEN_20261104.md:189–191` 记 `df==0 且 f0≠0` 共 **32 窗**，`EX2_ERRATA.md:88` 又引 `EX1_DATAFACE.md:265–313` 的 **41 窗**。
> **29 / 32 / 35 / 41 及两种 41 的分解口径并存**；各碎片自己的分母说明均未改动，本件不合并、不换算、不判定。（组装员添加，非碎片原文）
<!-- END ASSEMBLER CONFLICT NOTE C2 -->

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

---

## 3. 追加勘误候选 ← `EX2_ERRATA.md` 全文

# EX-2「追加勘误候选」（域内候选件，2026-11-04）

本件是 `RULING.md` EX-2 行的落实候选稿，**历史原文不改**：台账 `GOAL_THREE_TARGETS_20261018.md`、`PENDING_DECISIONS.md`、`RULING.md`、`RECHECK.md`、`FACTBASE.md`、三路核验件与真机 json/png 全程只读；本件只写入指定写域 `.../ADJUDICATE_a70d00e5/impl_f4bcf30c/EX2_ERRATA.md`。未启动 gamemd.exe / ra2loader.exe / YURI，未 taskkill，未读活进程内存，未 commit，未产生任何采样/注入/运行期探针脚本。正文块（第 2 节）可整段追加到台账末尾；第 0、1、3 节是交付说明，不属于追加内容。

**本件的立场**：只撤销肯定归因的强度，不建立反向全称结论（`RULING.md:5`、`RULING.md:102`、`RULING.md:180`）。每处引用写「文件名 + 该件实际行号」；文件全路径见第 1 节。

## 0. 本件实际执行的检查（命令与输出）

**检查 A：grep 台账确认同号章节的实际行号**（只读，退出码 0）：

```bash
grep -n -E "^# §5(3[89]|4[0-4])|^## §544" "D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
```

实际 stdout：

```text
3800:# §538　唤醒轮（维护+核查，零新分析）：**BOOT#9 稳定（uptime 42min，双轴未变）**；
3890:# §539　**P05（他会话中间产物）与本线 §529 的冲突辨析：不冲突，两段不重叠**（纯离线核查，零真机）：
4003:# §540　**P01（他会话已完成报告）重大发现：帧冻结机制已字节级定谳** —— 本线**独立核验三条核心断言全部通过**：
4091:# §541　**`dwfrun-169a2a53` 已 completed（3576 万 tokens）——`BATCH1_VERDICT.md` 收敛：5 项全 CONFIRMED**；
4207:# §543　**★ 重大反转（自我纠错）：所谓「29 个战斗段完全冻结窗」绝大多数是对局打完后的「遭遇战得分」结算屏** ——
4361:## §544 · 三模型独立核验：§543/§544 两次改判被收敛（2026-11-04）
```

**检查 B：`l3_1101v4c` 三窗字段身份核对**（`python -I -X utf8`，绝对路径，只读原始 JSON，退出码 0）。这是一次只读字段核对，未产生脚本文件、非采样/注入/运行期探针：

```bash
python -I -X utf8 -c 'import json; from pathlib import Path
root=Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c")
for w in range(3):
 p=root/("measure_w%d.json"%w); d=json.loads(p.read_text(encoding="utf-8-sig")); e=d["frame_edges"]; live=(e[-1][0]-e[0][0])/(e[-1][1]-e[0][1])
 print(json.dumps({"path":p.as_posix(),"stored_stats_fps_avg":d["stats"]["fps_avg"],"stored_stats_fps_p50":d["stats"]["fps_p50"],"derived_live_fps_first_to_last_edge":live,"has_stored_live_fps":("live_fps" in d or "live_fps" in d["stats"])},ensure_ascii=False))'
```

实际 stdout：

```text
{"path": "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w0.json", "stored_stats_fps_avg": 18.520948494813613, "stored_stats_fps_p50": 19.81123852234025, "derived_live_fps_first_to_last_edge": 18.539626790502314, "has_stored_live_fps": false}
{"path": "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w1.json", "stored_stats_fps_avg": 28.40179635682234, "stored_stats_fps_p50": 30.2016260596662, "derived_live_fps_first_to_last_edge": 28.416096013424877, "has_stored_live_fps": false}
{"path": "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w2.json", "stored_stats_fps_avg": 30.681571141892938, "stored_stats_fps_p50": 30.84258868525148, "derived_live_fps_first_to_last_edge": 30.70530239738328, "has_stored_live_fps": false}
```

**检查 C**：追加正文的「已撤回旧支柱」禁用扫描在成文后执行，零命中；为避免把被撤回的数值/定性重新写进本件，扫描式样与输出不落在本文件内，记于交付结果的第 5 条验收自查。

**未做的检查（如实登记）**：未重跑 104 份全库重建、未重算 22 窗整体覆盖率、未新读/OCR 任何 PNG、未核截图时序/哈希、未做真机发射或运行期实验、未跑项目测试。21/32 覆盖与计分屏判定沿用已读原件，不冒充本件独立复核（`RULING.md:197`、`RECHECK.md:82`）。

## 1. 文件全路径对照（供第 2 节每个「文件名:行号」解析）

| 本件使用的文件名 | 绝对路径 |
|---|---|
| `RULING.md` | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md` |
| `RECHECK.md` | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RECHECK.md` |
| `FACTBASE.md` | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/FACTBASE.md` |
| `EX1_DATAFACE.md` | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/EX1_DATAFACE.md` |
| `GOAL_THREE_TARGETS_20261018.md` | `D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md` |
| `_LEADER_FROZEN_29_20261104.md` | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/_LEADER_FROZEN_29_20261104.md` |
| `_LEADER_FREEZE_INSTANT_20261104.md` | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/_LEADER_FREEZE_INSTANT_20261104.md` |
| `S543_FREEZE_WAS_SCORESCREEN_20261104.md` | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/S543_FREEZE_WAS_SCORESCREEN_20261104.md` |
| `S544_TRI_MODEL_VERDICT_20261104.md` | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/S544_TRI_MODEL_VERDICT_20261104.md` |
| `PENDING_DECISIONS.md` | `D:/Project/ra2-campaign-forge/lead/PENDING_DECISIONS.md` |

---

## 2. ★ 以下整段为可直接追加到台账末尾的勘误正文（历史原文不改）

<!-- BEGIN APPENDABLE ERRATA -->

### §545 · 勘误（2026-11-04）：撤销整批「在战引擎停摆」的肯定归因（追加节，原文不改）

> 本节为**追加勘误节**，`GOAL_THREE_TARGETS_20261018.md:3800`（§538 唤醒轮）、`GOAL_THREE_TARGETS_20261018.md:3890`（§539 P05 冲突辨析）、`GOAL_THREE_TARGETS_20261018.md:4003`（§540）、`GOAL_THREE_TARGETS_20261018.md:4091`（§541）、`GOAL_THREE_TARGETS_20261018.md:4207`（§543）、`GOAL_THREE_TARGETS_20261018.md:4361`（§544）及各散件的历史原文**一律不改、不删、不就地覆写**；裁定依据 `RULING.md:97`（D-15.2「追加勘误节，不就地改写，也不维持原叙事有效」）与 `RULING.md:167`（EX-2 行）。本节撤销的是**归因**，不改写任何原始读数。

#### 545.1 来源定位（防止同号错引）

历史散件 `_LEADER_FROZEN_29_20261104.md:1` 自题「§538 战斗段完全冻结：29 窗定谳」、`_LEADER_FREEZE_INSTANT_20261104.md:1` 自题「§539 冻结的精确时刻：从满速到零推进的断崖」，与台账 `GOAL_THREE_TARGETS_20261018.md:3800` 的 §538（唤醒轮·维护核查，该件 `:3806` 自记「本件不含任何机制结论」）及 `GOAL_THREE_TARGETS_20261018.md:3890` 的 §539（P05 与 §529 冲突辨析）**不是同一篇文章**（`RULING.md:187` 材料冲突表「低」行）。因此本节所有引用一律写「文件名 + 该件实际行号」，不单写章节号；台账同号章节的实际行号已由本轮 `grep -n` 核实为 `GOAL_THREE_TARGETS_20261018.md:3800` / `GOAL_THREE_TARGETS_20261018.md:3890` / `GOAL_THREE_TARGETS_20261018.md:4003` / `GOAL_THREE_TARGETS_20261018.md:4091` / `GOAL_THREE_TARGETS_20261018.md:4207` / `GOAL_THREE_TARGETS_20261018.md:4361`（完整命令与 stdout 见本件第 0 节检查 A；`RULING.md:34` 把台账代号固定为 L，`RULING.md:19–39` 固定各件全路径）。

#### 545.2 明确撤销的四项归因

1. **撤销「整批是战斗段完全冻结」**。`_LEADER_FROZEN_29_20261104.md:12`（判据 `f0!=0 且 df==0` 计 29 窗）、`_LEADER_FROZEN_29_20261104.md:17`（称「真正的绝对多数现象」）、`_LEADER_FROZEN_29_20261104.md:109`（R1「整窗冻结」29 窗、25s 零推进）所下的「**战斗段**」定性超出读数：这些读数只说明窗内帧号零推进，不说明当时处于战斗阶段（`RULING.md:97`、`RULING.md:101`）。`S543_FREEZE_WAS_SCORESCREEN_20261104.md:133` 与 `S544_TRI_MODEL_VERDICT_20261104.md:199–200` 亦记该叙事须降级。
2. **撤销「引擎停摆已定谳」**。`_LEADER_FREEZE_INSTANT_20261104.md:81–88`（「目标①的实测形态现已确定」→「这正是『引擎停摆』而非『崩溃』、也非『变慢』」）及 `GOAL_THREE_TARGETS_20261018.md:4054`（§540 §四「『帧冻结』的机制已被字节级定谳，不再是黑箱」）中，**把「已定谳」当作运行期因果/定位结论**的部分撤销；台账自身已在 `GOAL_THREE_TARGETS_20261018.md:4075` 把「目标①本质是被主动挂起」登记为「属推测性归纳，未经独立验证」，并在 `GOAL_THREE_TARGETS_20261018.md:4134–4135` 把两个行为学问题判为 DATA_INSUFFICIENT / 单通道不可分辨（`RULING.md:97`、`RULING.md:197`）。**§540/§541 的静态字节事实不随本项撤回**，见 545.3(2)。
3. **撤销「永不恢复」被用作超出观察窗的机制结论**。`_LEADER_FROZEN_29_20261104.md:95`（「再未恢复」）、`_LEADER_FROZEN_29_20261104.md:131`（「某个点之后就永久冻结了」）、`_LEADER_FREEZE_INSTANT_20261104.md:55`（「永不恢复」）、`_LEADER_FREEZE_INSTANT_20261104.md:74`（「从不恢复」）、`_LEADER_FREEZE_INSTANT_20261104.md:85`（「状态永久保持」）的**窗内观测**（后续 25 秒窗 `df=0`、帧号恒等于前窗末值）保留；被撤销的是把它外推为「引擎永久停摆、永不恢复」这一**超出观察窗范围的机制结论**（`RULING.md:97`、`RULING.md:102`）。`_LEADER_FREEZE_INSTANT_20261104.md:98` 自己已记该表述与 T38 存在「细微不符」。
4. **撤销「凭窗口停帧形态证明某条静态路径已在历史趟命中」**。`_LEADER_FROZEN_29_20261104.md:133–134` 以「形态上吻合」关联 §533 免-inc 出口（同件 `:134` 自记「矛盾未解」），`_LEADER_FREEZE_INSTANT_20261104.md:100–102` 自陈「本件没有把冻结与任何引擎机制关联起来」且 §533 假说「进一步被弱化」；`GOAL_THREE_TARGETS_20261018.md:4058–4063`（§540 §四「挂起计数器 → 免-inc 出口」解读）不得据窗口停帧形态升格为历史趟的运行期命中（`RULING.md:155`「已有静态反汇编只列『静态事实/候选路径』，不能把可达路径写成历史运行期命中」、`RULING.md:197`）。**可达的静态路径 ≠ 历史运行期命中**；运行期是否命中的证据为「缺」（见 545.3(2)）。

**本节撤销的是肯定归因，不是已证相反结论**：不得据此改写成「32 窗全部已证正常终局」或「全部冻结窗都不是引擎停摆」（`RULING.md:5`、`RULING.md:102`、`RULING.md:180`）；理由是撤销旧肯定结论的充分证据，不构成对全称相反命题的证明（`RULING.md:101–102`）。

#### 545.3 保留项：原始读数与 §540/§541 静态字节结论

**(1) 原始读数全部保留、不撤回、不改写。** 帧号、时间、零推进计数照旧有效：`_LEADER_FROZEN_29_20261104.md:51–63` 的三趟三窗字节级读数（`archive_T32` w0 `f=[296,778]` `df=482` `max_stall=9.575s`、w1/w2 `f=[778,778]` `df=0` `max_stall=24.999s`、`t_abs0=1792285955.9/1792285980.9/1792286006.0`；`archive_T38` w0 `f=[130,910]` `df=780`、w1 `f=[911,940]` `df=29` `max_stall=24.077s`、w2 `f=[940,940]` `df=0`；`l3_20261023r` w0 `f=[3100,3883]`、w1 `f=[3883,4367]`、w2 `f=[4367,4367]` `df=0` `max_stall=24.998s`）、`_LEADER_FROZEN_29_20261104.md:40–41`（`f0=3514` / `3594`、`df=0`、`4.000s`）、`_LEADER_FREEZE_INSTANT_20261104.md:10`（T32 w0 `frame_edges` 483 条、`f=[296,778]`、`span=25.0s`、`max_stall_s=9.574`）、`_LEADER_FREEZE_INSTANT_20261104.md:15–30`（末 12 个帧沿、`f=778` 落在 `t=15.42s`、此后 9.58 秒帧号恒为 778）、`_LEADER_FREEZE_INSTANT_20261104.md:66–75`（`f0!=0` 29/29、`df==0` 29/29、`max_stall_s≈窗长`、`rc=0` 正常退出）均不改动（`RULING.md:97`「保留原始帧号、时间、零推进等读数」）。上一阶段从 104 份原始 JSON 只读重建的 41 个零/负推进或样点不足窗及其逐窗首末帧号，见 `EX1_DATAFACE.md:265–313`（重建命令与输出见 `EX1_DATAFACE.md:11–15`）；按 `RULING.md:85`，这 41 窗**不得统称 41 个冻结**。

**(2) `GOAL_THREE_TARGETS_20261018.md:4003`（§540）与 `GOAL_THREE_TARGETS_20261018.md:4091`（§541）的静态字节结论不随本次勘误撤回**：`GOAL_THREE_TARGETS_20261018.md:4041–4050` 的四条字节断言复算（`0x55D877` 处 `c3`、`0x684174` 为 `inc [eax+0x62C]`、MLF 三 ret、`[0xA8B230]` 三写点，`:4050` 判「四条全部通过」）与 `GOAL_THREE_TARGETS_20261018.md:4114–4128` 的 `BATCH1_VERDICT.md` 字节主线表（`+0x62C` 挂起深度计数器写点恰 3 处、`0x55D877` 双门、`CurrentFrame` 唯一 RMW 链）按「静态事实／候选路径」全部保留（`RULING.md:97`「静态字节结论与运行期因果归因分开，§540/§541 字节结论不得随此自动撤回，也不得继续冒充运行期定位证据」、`RULING.md:155`）。**但它们不得再冒充运行期定位证据**：台账 `GOAL_THREE_TARGETS_20261018.md:4067–4075`（语义推断链未复核、P01 未经异族核验、§四解读属推测）与 `GOAL_THREE_TARGETS_20261018.md:4130–4137`（行为学问题不可判定）已自陈这一限度（`RULING.md:197`）。**运行期耗时落点、以及该静态路径在历史趟是否命中：缺**；已查阅 `RULING.md:155`、`RULING.md:197`、`RULING.md:202`、`_LEADER_FREEZE_INSTANT_20261104.md:100–102` 仍无该证据，按「缺」登记，不据其他窗/其他趟/推理补值（`RECHECK.md:82` 记本线未新读 PNG、未核截图时序/哈希、未做运行期实验）。

<!-- BEGIN ASSEMBLER CONFLICT NOTE C3 -->
> ⚠️ **【组装员冲突标注 · C3｜见 C1：本段保留读数与数据面／证据表精确值并存，不调和】**
> 本节 `EX2_ERRATA.md:88` 的 `9.575s` / `9.574` / `24.077s` / `24.999s` / `24.998s`，与 `EX1_DATAFACE.md:152,154,156` 的
> `9.574864` / `24.734761` / `24.077365`、`EX3_STALL_EVIDENCE.md:99,101,103` 的同值 **原样并存**；
> 不调和、不判定差异成因、不改动任何一侧。另本节 `EX2_ERRATA.md:111`、`:112` 与 `EX3_STALL_EVIDENCE.md:108`、`:103` 的冲突见 C4。（组装员添加，非碎片原文）
<!-- END ASSEMBLER CONFLICT NOTE C3 -->

#### 545.4 证据范围写死：21/32，不是全部

对经来源和时序核验的计分屏，证据足以认定**相应采图时刻已处于终局/结算界面**，并足以撤销「仅凭 `df==0` 就已证实在战引擎停摆」的归因（`RULING.md:101`）。**冻结窗终局证据的覆盖为 21/32，不是全部**：`S543_FREEZE_WAS_SCORESCREEN_20261104.md:189–191`（`df==0 且 f0≠0` 共 32 窗，其中「有计分屏证据 21 个」、11 个须挂账）、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:218–228`（11 个未覆盖窗的名单与原因：无截图／纯战斗画面副本；`:228` 明记「不判为『终局态』，明确挂账」）、`S544_TRI_MODEL_VERDICT_20261104.md:200`（覆盖 21/32）、`GOAL_THREE_TARGETS_20261018.md:4466`（§544 §七「覆盖 21/32 窗」）、`RULING.md:102`。截图在窗末，不能单靠该图把整个 25 秒每一时刻都标成终局，也不能从后续结算反推先前完全没有性能问题（`RULING.md:102`）。

**未充分覆盖的零推进窗一律归「零推进、原因未定」**：不贴「引擎停摆」标签，也**不**改记「终局已证实」（`RULING.md:103`「这是当前有效分类，执行无需等待新证据」、`RULING.md:180`）。另须区分：`RULING.md:120` 记明「这 32 个零推进窗中的 11 个未充分覆盖窗」与 D-15.3 的 **11 个有推进的停摆主导窗不是同一集合**，不得混算或互相替代。

#### 545.5 数据面分层（22 + 11 + 5）与主指标

按 D-15.1 分层表（`RULING.md:75–87`）与上一阶段数据面落实稿 `EX1_DATAFACE.md:38–84`（从 104 份原始 JSON 只读重建，命令与输出见 `EX1_DATAFACE.md:11–15`）：语料账 **104 = 子目录 101 + 根 3**（`EX1_DATAFACE.md:38–45`、`FACTBASE.md:42–47`）；净正推进窗 **63**，其中 **58** 个 25 秒窗、**5** 个 4 秒 settle 门控窗、**41** 个非正推进或样点不足窗（`EX1_DATAFACE.md:49–57`、`:265–313`）。58 窗三分类为 **25** 个 `fps_avg>=28` 对照、**22** 个持续低速核心（`fps_avg<28 且 fps_p50<28`，**8 个独立趟**）、**11** 个停摆主导（`fps_avg<28 且 fps_p50>=28`，11 趟，与 22 窗 `trip_id` 交集 0）（`EX1_DATAFACE.md:73–80`、`:119–164`）。

**22 + 11 + 5 分层与报数规定**：核心持续低速分析样本 = **22 个 25 秒窗 / 8 趟**（`RULING.md:82`、`EX1_DATAFACE.md:119–146`）；25 秒低 avg 总计 **33 = 22 持续低速 + 11 停摆主导**（`RULING.md:81`、`EX1_DATAFACE.md:320`）；**11** 个停摆主导窗整组另列「**停摆观测、待归因**」异常层，**既不作为已证在战卡顿正证，也不整组认定终局**（`RULING.md:111`、`RULING.md:5`、`EX1_DATAFACE.md:148–164`）；**5** 个 4 秒门控窗剔出 25 秒性能分析，保留测量失败/加载相位诊断用途（`RULING.md:84`、`EX1_DATAFACE.md:59–69`）。`38` 是混入 5 个 4 秒窗的旧混合计数（38 = 33 + 5），不得再冒充同质性能样本数（`EX1_DATAFACE.md:315–324`、`RULING.md:178`）。每次目标①摘要必须同时出现「核心持续低速 22/8 趟；25 秒低 avg 总计 33，其中 11 停摆另列；另 5 个 4 秒门控窗排除」；只用 22+25=47 窗的分析必须标为「排除 11 个待归因停摆窗后的持续低速/对照分析集」，不得把 22/47 写成全体真机卡顿发生率（`RULING.md:87`、`EX1_DATAFACE.md:324`）。

**主指标维持 `fps_avg`**（`RULING.md:89`、`EX1_DATAFACE.md:32`）；同时披露 `max_stall_s`、零推进数量、时长/门控状态与阶段证据。`fps_p50` 与派生 `live_fps` 仅作分型，不替换主指标、不用于给停摆窗出健康结论（`RULING.md:89`、`EX1_DATAFACE.md:326–330`）；窗口与独立趟两个单位同时报告，一趟多窗不得当成多个独立会话样本（`RULING.md:87`）。

#### 545.6 已撤回、禁止复用的三项旧支柱

以下三项旧支柱已被证伪，**不得再作为本勘误或后续归因的依据**（`RULING.md:105`「不能再以这些已撤回依据强化终局归因」、`RULING.md:167`）：

1. §543 的「屏显时间 ÷ 帧率常数 = 帧号」换算（`GOAL_THREE_TARGETS_20261018.md:4209`、`:4227–4245`）**撤销**：该常数实为健康窗 `stats.fps_avg` 成簇的**帧率帽瞬时值**，不是结算屏时钟换算常数，因果方向搞反（`S544_TRI_MODEL_VERDICT_20261104.md:115`、`GOAL_THREE_TARGETS_20261018.md:4417`）；不得再以该换算反推帧号或终局。
2. §543 的首版比分读数（`GOAL_THREE_TARGETS_20261018.md:4261–4262`）**撤销**：两路独立读得 **126/206/0/201034** 与 **198/731/4/126800**（`S544_TRI_MODEL_VERDICT_20261104.md:116`、`GOAL_THREE_TARGETS_20261018.md:4418`）；旧读数不得再引用。
3. §543 对 `archive_T38` 屏显秒数及 w1 图「时序错位」的判断（`GOAL_THREE_TARGETS_20261018.md:4234`、`:4254`）**撤销**：屏显实为 **`00:00:32`**，且该 w1 图是**磁盘残留件**（mtime 比窗尾早 4410.95 秒，与 T36/w1 同 sha、同字节、mtime 同到微秒），不是时序错位，不得作精确读数（`S544_TRI_MODEL_VERDICT_20261104.md:113–114`、`GOAL_THREE_TARGETS_20261018.md:4415–4416`）。

<!-- BEGIN ASSEMBLER CONFLICT NOTE C4 -->
> ⚠️ **【组装员冲突标注 · C4｜★ 结论／数值冲突：「禁止再引用」vs「作为材料记载转述」；原样保留，不调和】**
> **(a) 比分**：`EX2_ERRATA.md:111` 裁定 §543 首版比分读数**撤销**，采用 `126/206/0/201034` 与 `198/731/4/126800`，并明写「**旧读数不得再引用**」；
> `EX3_STALL_EVIDENCE.md:108`（§1 第 10 行）却以「材料记载」转述 `S543_FREEZE_WAS_SCORESCREEN_20261104.md:81-94` 的「**126/146 摧毁、201034/126800 分**」，同句又列出订正值。
> **(b) 屏显秒数**：`EX2_ERRATA.md:112` 裁定屏显实为 `00:00:32`、「不是时序错位，不得作精确读数」；
> `EX3_STALL_EVIDENCE.md:103`（§1 第 5 行）转述已撤回的 `00:00:10 / 1 帧级时间错位`（该行自注「已撤回、不再采信」）。
> **两处「禁止再引用／不得作精确读数」与「作为材料记载转述」的处置并存，旧值与订正值同时保留**；本件不判定 EX-3 是否违反 EX-2 的禁令，不删除任一数值，不改写任一结论。（组装员添加，非碎片原文）
<!-- END ASSEMBLER CONFLICT NOTE C4 -->

#### 545.7 ★ 字段身份（复查 R2）：`l3_1101v4c` 三窗速度序列

同版本同地图的 `l3_1101v4c` 趟内「由慢转快」线索，两组数**必须注明字段，不得把派生值填进 avg 栏**（`RULING.md:151–154`、`RECHECK.md:15–21`）：

| 窗口 | 主指标 `stats.fps_avg`（原始 JSON 存储字段） | 派生 `live_fps`（首末帧沿差商，**非存储字段**） |
|---|---:|---:|
| `measure_w0.json` | **18.52**（原值 `18.520948494813613`） | **18.54**（`18.539626790502314`） |
| `measure_w1.json` | **28.40**（原值 `28.40179635682234`） | **28.42**（`28.416096013424877`） |
| `measure_w2.json` | **30.68**（原值 `30.681571141892938`） | **30.71**（`30.70530239738328`） |

`S544_TRI_MODEL_VERDICT_20261104.md:147` 报的 `18.54→28.42→30.71` 是**派生 `live_fps`**（首末帧沿差商），不是源码/JSON 字段（`RECHECK.md:15–19`；该原件同时把这两处报数的全路径列在 `RECHECK.md:17`，分别对应代号 H 的 hy4free 核验件与代号 Q2 的 qfmodel V2 报告，路径对照见 `RULING.md:25`、`:28`）；**主指标 `fps_avg` 序列是 `18.52→28.40→30.68`**（`RULING.md:153`、`RECHECK.md:19`、`:77–79`）。本件生成时只读核对 `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w0.json`、`.../measure_w1.json`、`.../measure_w2.json`（各为单行文件，源位置第 1 行），确认三窗 `stats.fps_avg` 与派生值如上，且三份原件**均无 `live_fps` 存储字段**（`has_stored_live_fps=false`；完整命令与 stdout 见本件第 0 节检查 B）。两组数都只支持「趟内由慢转快」这一**线索**，不据此归因寻路/会话/宿主/兵力变化；同版本同地图的趟内比较不得与跨日期的版本/地图/相位混杂合成因果配对（`RULING.md:150–151`、`:155`）。

#### 545.8 D-15 结案用语（供后续可维护既有件的轮次登记）

D-15 已裁（采用修正 A），历史叙事按「追加勘误、原文不改」处理，不维持原叙事有效（`RULING.md:5`、`RULING.md:97`）；本件为域内候选稿，当前轮次台账 `GOAL_THREE_TARGETS_20261018.md` 与 `PENDING_DECISIONS.md` 保持只读，**未追加、未删条、未登记、未 commit**（`RULING.md:13`、`:170`）。目标①的现象证据（22 个 25 秒持续低速窗 / 8 趟）成立，**运行期耗时落点与因果链未定位、机制未闭合**（`RULING.md:146`、`:204`）；D-13「当前 E3→① 实施路径关闭」不替代本节的证据限度说明（`RULING.md:128`、`:130`）。

<!-- END APPENDABLE ERRATA -->

---

## 3. 逐条验收自查与边界（不属于追加正文）

| # | 判据 | 落实位置 |
|---|---|---|
| 1 | 明确撤销四项归因（整批战斗段完全冻结／引擎停摆已定谳／「永不恢复」超窗机制化／凭停帧形态证明静态路径历史命中），且不写成已证相反结论 | 545.2 第 1–4 项 + 「撤销的是肯定归因，不是已证相反结论」段 |
| 2 | 保留帧号/时间/零推进计数；保留 §540/§541 静态字节结论；声明不得再冒充运行期定位证据；缺项写「缺」并列查阅件 | 545.3(1)、545.3(2) |
| 3 | 证据范围写死 21/32、未覆盖窗归「零推进、原因未定」、不贴停摆标签也不改记终局 | 545.4 |
| 4 | 22 + 11 + 5 分层、33/38 分母、报数规定、`fps_avg` 主指标 | 545.5 |
| 5 | 三项被证伪旧支柱只作「已撤回、禁止复用」列出并给出正确值，不作依据 | 545.6；禁用扫描见第 0 节检查 C |
| 6 | 每处引用写「文件名 + 实际行号」；显式说明散件 §538/§539 与台账同号章节不是同文；台账行号经 grep 核实 | 545.1、全篇引用；第 0 节检查 A |
| 7 | `l3_1101v4c` 三窗序列标明 `fps_avg` 与派生 `live_fps` 身份 | 545.7；第 0 节检查 B |

**边界**：本件只出文档，未写任何采样/注入/运行期探针脚本；第 0 节检查 B 是一次只读字段核对（内联 `python -I -X utf8 -c`，绝对路径，未产生脚本文件）。未改台账/PENDING/RULING/RECHECK/FACTBASE/核验件/真机件，未 commit。数据面数字引用上一阶段 `EX1_DATAFACE.md`，本件未重跑其重建脚本；21/32 覆盖、截图时序与计分屏判定沿用已读原件，未在本件独立复核（`RULING.md:197`、`RECHECK.md:82`）。

---

## 4. 11 窗证据表 ← `EX3_STALL_EVIDENCE.md` 全文

# EX-3　11 个停摆主导窗：逐窗证据资格表

**交付件**：`D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/EX3_STALL_EVIDENCE.md`
**依据**：`RULING.md` D-15.3（`RULING.md:109-122`）与 EX-3 行（`RULING.md:168`）；`RECHECK.md:1-5` 判定「需修改后执行」，两处漏洞（R1 47 窗混杂字段、R2 v4c 派生指标）已由 Leader 修补进 RULING，与本表无关。
**整组裁定（照抄用途，不加强）**：11 窗整组归「停摆观测、待归因」，**既不作为已证在战卡顿正证，也不整组认定终局**；主指标计数仍为 33（22 持续低速＋11 停摆主导），核心持续低速分析仍为 22 窗/8 趟（`RULING.md:81-83`、`RULING.md:111`）。本表**不得**用来删改原始 33 个低 avg 计数。

---

## 0. 方法、口径与边界（先读）

### 0.1 名单来源与独立重建

名单取自上一阶段底账 `EX1_DATAFACE.md:148-162`（其上游 `S544_TRI_MODEL_VERDICT_20261104.md:175-176`、`XVERIFY_S544_c1606d35/VERDICT.md:73`）。本轮**独立从 104 份原始 JSON 重建**以确认「恰好 11」：

**命令（本轮实际执行，`python -I -X utf8`，退出码 0）**：

```bash
python -I -X utf8 - <<'PY'
import json, os, glob
data=r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
allj=glob.glob(os.path.join(data,'**','measure_w*.json'),recursive=True)
cand=[]
for f in allj:
    j=json.load(open(f,encoding='utf-8-sig'))
    s=j.get('stats') or {}
    if j.get('span_s')==25.0 and s.get('fps_avg') is not None and s.get('fps_avg')<28 and s.get('fps_p50') is not None and s.get('fps_p50')>=28:
        cand.append(f)
print('CHECK-1 total measure_w*.json=',len(allj))
print('CHECK-1 25s avg<28 & p50>=28 count=',len(cand))
for f in sorted(cand): print('   ',os.path.relpath(f,data).replace(os.sep,'/'))
all25=[f for f in allj if json.load(open(f,encoding='utf-8-sig')).get('span_s')==25.0]
low=[f for f in all25 if (json.load(open(f,encoding='utf-8-sig')).get('stats') or {}).get('fps_avg') is not None and json.load(open(f,encoding='utf-8-sig'))['stats']['fps_avg']<28]
print('CHECK-1 25s windows=',len(all25),' 25s low avg=',len(low))
PY
```

**实际 stdout（节选）**：

```text
CHECK-1 total measure_w*.json= 104
CHECK-1 25s avg<28 & p50>=28 count= 11
    archive_T32/measure_w0.json
    archive_T33/measure_w0.json
    archive_T34/measure_w0.json
    archive_T36/measure_w0.json
    archive_T38/measure_w1.json
    archive_T39/measure_w1.json
    archive_T43/measure_w0.json
    archive_T47/measure_w0.json
    archive_T49_u0800/measure_w0.json
    l3_20261023q/measure_w2.json
    l3_20261023r/measure_w1.json
CHECK-1 25s windows= 89  25s low avg= 33
```

`25s windows=89` 是「`span_s==25.0`」的全部件数，含 31 个非正推进/不足样窗；本轮另以 `df>0` 交叉核对得 `span25&pos=58`、`span25&nonpos=31`、`span_other&pos=5`（4 秒门控窗）、`span_other&nonpos=10`，合计 104，正推进 63、非正推进 41。故可算 25 秒窗为 58（`EX1_DATAFACE.md:77-80`），其中低 avg **33**；33 = 22 持续低速 + 11 停摆主导。本表只用其中 11 个，**33 的计数不变**。

<!-- BEGIN ASSEMBLER CONFLICT NOTE C6 -->
> ⚠️ **【组装员冲突标注 · C6｜见 C2：41 窗的两种分解与 29／32 窗计数并存，原样保留，不调和】**
> 本节 `EX3_STALL_EVIDENCE.md:56` 的「41 = `span25&nonpos=31` + `span_other&nonpos=10`」与 `EX1_DATAFACE.md:313` 的「41 = 5 + 1 + 35」、
> `EX2_ERRATA.md:79` 的 29 窗、`EX2_ERRATA.md:94` 的 32 窗为**不同口径计数**；不合并、不换算、不判定。（组装员添加，非碎片原文）
<!-- END ASSEMBLER CONFLICT NOTE C6 -->

### 0.2 时序判据的可计算性（关键前提，已实测）

题定判据：`mtime - (t_abs0 + span_s)` 落在 **+0.05 ~ +0.20 秒**内算「来源与时序可确认」；**偏离数小时的是磁盘残留件**。

- `t_abs0` 在源码里由 `time.time()` 取得（[`qc151_trip.harness8_v4.py:5301`](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:5301)、[`:5322`](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:5322)、[`:5345`](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:5345)），是 **Unix 墙钟秒**；`span_s=25.0`，故 `t_abs0+span_s` 即窗尾的墙钟时刻，可直接与文件 `mtime`（同为 Unix 墙钟秒）相减。
- 窗 JSON 在窗尾即刻落盘（[`qc151_trip.harness8_v4.py:4821-4825`](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:4821)），末取证函数在 `end_stage` 之后调用（[`:5362-5363`](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:5362)）。

**本轮实测校验（11 个停摆窗的 JSON 自身 mtime 对其窗尾）**：`+0.013521s ~ +0.026548s`，全部为正且远小于 0.05 s，证明该时钟口径自洽、可用于判据。命令与输出见 §3 检查 C。

**判据适用对象**：本表第 2/3 列评估的是**当窗（该停摆窗）窗尾**的末截图。第 5 列另评估**同趟后续窗**的截图（按其**各自**窗尾对齐），二者严格分开记录，绝不混用。

### 0.3 截图的「来源」如何确认

harness 只在 `empty_window=True` 时落 `measure_w{k}_end_x.png`（[`qc151_trip.harness8_v4.py:4886-4889`](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:4886)、[`:4911-4919`](D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:4911)），并把 `forensics_png`/`capture_ok` 写进 `qc151_fields.json` 的 `measure_forensics_w{k}` 记录。**来源可确认** = 该窗有对应 `qc151_fields.json` 声明（`capture_ok=true`、声明文件名）＋ 该文件确实在盘 ＋ mtime 对齐该窗窗尾。三者缺一即「不可确认／未知」。

### 0.4 图像内容判读的证据等级（不越权）

本轮**没有独立打开 PNG 做目视/OCR**（`FACTBASE.md:129` 已把「PNG 目视或 OCR、截图 sha/mtime 复核」列为前一步未运行项；本轮补做了 mtime/sha 复核与存在性，但**未做新的目视**）。表中「计分屏／无面板」等画面判读，一律**转述**已读材料 `_leader_fullcensus_out.txt:57-82`（像素判据 p + 逐窗判读）、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:196-201, 209-230`（勘误 B、重复件、无证据清单）、`_leader_scorescreen_out.txt:13-37`，并**明确标注为「材料记载、非本轮独立读图」**。裁决已限定 `RULING.md:101-102`：经来源与时序核验的计分屏足以认定**相应采图时刻**已处于终局/结算界面，但**不足以**把整个 25 秒或前窗整段停顿判成终局，更不能反推先前无性能问题。

### 0.5 硬约束（裁决明文，逐条落到本表）

| # | 硬约束 | 本表落实位置 |
|---|---|---|
| H1 | `l3_20261023q/w2` **不得**标「已证终局」；单列「未知阶段停摆」 | 第 11 行，§2 第 11 行；`RULING.md:118` |
| H2 | `archive_T32/w0`、`archive_T47/w0` **不得**靠后续 `df==0` 确证终局（后续冻结窗无截图） | 第 1、8 行，§2 第 1、8 行，§4；`RULING.md:120`、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:221-222` |
| H3 | 11 窗整组**不得**计为「已证在战机制」或「已证终局」 | 表头、§1 汇总行、§4；`RULING.md:111` |
| H4 | 本表**不得**删改原始 33 个低 avg 计数 | §0.1、§1、§4；`RULING.md:111`、`RULING.md:168` |
| H5 | **绝不把「后续窗零推进」当成「本窗停顿的原因」** | 全表第 4 列与第 5 列分列、§1 说明、§4；`RULING.md:113-120` |

---

## 1. 主表：恰好 11 行（6 列 + 窗标识）

> 列 2「当窗末截图是否实际落盘」：以该停摆窗自己的窗尾 `t_abs0+span_s` 为基准。所有 11 行的答案均为「否」，理由见 §0.3／§3 检查 A、B。
> 列 3「来源与时序是否可确认」：当窗截图既然不存在，即**不可确认**；另把当趟内任何偏离数小时的候选件逐一点名标为**磁盘残留件**。
> 列 4「同一趟后续窗整窗零推进」：只报 `logic_frames==0`／`df==0` 的**读数**，不作因果。
> 列 5「可确认的终局关联证据」：仅当**后续窗**存在「声明＋落盘＋mtime 对齐其自身窗尾＋材料记载为计分屏」时才记「有（终局关联旁证）」；且一律注明它只覆盖采图时刻、不覆盖本窗整段。
> 列 6「未知项」：查不到的一律写「未知」，并注明查阅了哪些文件仍是缺。

| # | ① 窗标识与绝对路径 | ② 当窗末截图是否实际落盘（文件存在？mtime 与窗尾相符？） | ③ 截图来源与时序是否可确认 | ④ 同一趟后续窗整窗零推进 | ⑤ 可确认的终局关联证据 | ⑥ 未知项 |
|---|---|---|---|---|---|---|
| 1 | **`archive_T32/w0`**<br>`D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T32/measure_w0.json`<br>尾 `2026-10-18 01:13:00.913Z`（`t_abs0=1792285955.913532 + 25.0`） | **否**。窗尾 +0.05~+0.20 s 内**无任何 PNG**（本轮遍历该趟 49 张 PNG，命中 0）；`measure_w0_end_x.png` 不存在。**`mtime 与窗尾相符：不适用（无文件）`**。`qc151_fields.json` 中 `measure_forensics_w*` 记录**缺**（该趟为旧 harness，无 QC208-② 通道）。 | **不可确认**。`frame_target_01.png` mtime `01:12:31.871Z`、Δ`−29.042s`（窗**前**开局帧，非窗末）；`navsig_*` 多张偏离 `−5375.684s ~ −16314.661s`，属**磁盘残留件**（数小时级，非本窗采集）。按判据不得算「可确认」。 | **有**。`w1`：`logic_frames=0`、`df=0`；`w2`：`logic_frames=0`、`df=0`（`measure_w1.json` / `measure_w2.json` 顶层 `stats` 与 `frame_edges`）。**仅证明停摆序列，不证明本窗停顿原因**。 | **无／未知**。后续 `w1`/`w2` 均**无截图**（`measure_w1_end_x.png`、`measure_w2_end_x.png` 都不在盘；`qc151_fields.json` 无 forensics 声明）。`S543_FREEZE_WAS_SCORESCREEN_20261104.md:221` 明记 `archive_T32 w1/w2 无截图`。**不得靠后续 `df==0` 确证终局（H2）**。 | **未知**：本窗 25 s 内各时刻战术阶段、9.574864 s 停顿的运行期原因、是否/何时进入终局。已查 `measure_w0.json`、`measure_w1.json`、`measure_w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt`、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:218-230` 仍是**缺**。 |
| 2 | **`archive_T33/w0`**<br>`.../archive_T33/measure_w0.json`<br>尾 `2026-10-18 03:45:45.590Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w0_end_x.png` 不存在。`qc151_fields.json:measure_forensics_w0` 明记 `empty_window=False`、无 `forensics_png`、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。同趟 `measure_w1_end_x.png` Δ`+25.103682s`、`measure_w2_end_x.png` Δ`+50.193619s`（相对**本窗**窗尾）均不在窗内；`frame_target_01.png` Δ`−29.030s` 为窗前开局帧；`navsig_nav_setup_post_01_g.png` 等偏离 `−25479.338s` 属**磁盘残留件**。 | **有**。`w1`：`logic_frames=0`、`df=0`；`w2`：`logic_frames=0`、`df=0`。**仅停摆序列**。 | **有（终局关联旁证，级别受限）**。后续 `w1` 的 `measure_w1_end_x.png` 存在，mtime `03:46:10.694Z`，对**其自身窗尾** `03:46:10.610Z` Δ`+0.084068s`（在 +0.05~+0.20）；`qc151_fields.json:measure_forensics_w1` 声明该文件且 `capture_ok=true`，来源可确认；`_leader_fullcensus_out.txt:58` 记 `p=0.349 3c55bc86b7076794 计分屏(待目视)`（**材料记载、非本轮独立读图**）。`w2` 图 Δ`+0.089937s` 亦对齐，但 `_leader_fullcensus_out.txt:59` 记 `p=0.040 … 无面板`（`S543_FREEZE_WAS_SCORESCREEN_20261104.md:209-211, 215-230` 计入「纯战斗画面／4 张同图副本」），**不构成计分屏正证**。⇒ 只可注「采图时刻处于终局/结算界面」的旁证，**不得把本窗整段停顿判成终局，也不得把后续零推进自动等同计分屏**（`RULING.md:117`）。 | **未知**：本窗 10.814527 s 停顿原因、本窗内是否已在结算界面、`w1` 与 `w2` 图像不同（计分屏→无面板）的含义——`S543_FREEZE_WAS_SCORESCREEN_20261104.md:229-230` 自承「要么截图陈旧、要么真是另一种停摆，本件分不清，不作结论」。已查上述 JSON、`qc151_fields.json`、`_leader_fullcensus_out.txt`、`_leader_scorescreen_out.txt` 仍是**缺**。 |
| 3 | **`archive_T34/w0`**<br>`.../archive_T34/measure_w0.json`<br>尾 `2026-10-18 04:18:07.086Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w0_end_x.png` 不存在；`measure_forensics_w0` 记 `empty_window=False`、无 png、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。同趟 `measure_w1_end_x.png` Δ`+25.097453s`、`measure_w2_end_x.png` Δ`+50.179159s`（相对本窗窗尾）不在窗内；`frame_target_01.png` Δ`−29.025s` 为窗前开局帧；`navsig_nav_setup_post_01_g.png` 偏离 `−27420.834s` 属**磁盘残留件**。 | **有**。`w1`：`logic_frames=0`、`df=0`；`w2`：`logic_frames=0`、`df=0`。**仅停摆序列**。 | **有（终局关联旁证，级别受限）**。`w1`/`w2` 的 `measure_w1_end_x.png`（Δ`+0.079328s`）、`measure_w2_end_x.png`（Δ`+0.081706s`）均存在、声明一致、`capture_ok=true`、时序对齐各自窗尾；`_leader_fullcensus_out.txt:60-61` 记两图均为 `p=0.349 计分屏(待目视)`（**材料记载**）。⇒ 仅采图时刻的终局/结算界面旁证；`RULING.md:102` 明确「截图在窗末，不能单靠该图把整个 25 秒每一时刻都标成终局」。本窗 `max_stall_s=24.734761s`、`df=9`，**本窗内部状态仍未知**。 | **未知**：本窗 24.734761 s 长停顿的运行期原因、本窗末沿后到 w1 之间的阶段转换时点。已查 `measure_w0/w1/w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt`、`FACTBASE.md:103`（1 微秒差披露）仍是**缺**。 |
| 4 | **`archive_T36/w0`**<br>`.../archive_T36/measure_w0.json`<br>尾 `2026-10-18 04:53:02.566Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w0_end_x.png` 不存在；`measure_forensics_w0` 记 `empty_window=False`、无 png、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。同趟 `measure_w1_end_x.png` Δ`+25.090641s`、`measure_w2_end_x.png` Δ`+50.185656s`（相对本窗窗尾）不在窗内；`frame_target_01.png` Δ`−29.029s` 为窗前开局帧；`navsig_nav_setup_post_01_g.png` 偏离 `−18577.337s` 属**磁盘残留件**。 | **有**。`w1`：`logic_frames=0`、`df=0`；`w2`：`logic_frames=0`、`df=0`。**仅停摆序列**。 | **有（终局关联旁证，级别受限）**。`w1`/`w2` 两图存在、声明一致、`capture_ok=true`，对各自窗尾 Δ`+0.076847s` / `+0.094500s`；`_leader_fullcensus_out.txt:62-63` 记均 `p=0.349 计分屏(待目视)`（**材料记载**）。⇒ 仅采图时刻终局/结算界面旁证，不覆盖本窗整段；`S543_FREEZE_WAS_SCORESCREEN_20261104.md:61` 记 w1/w2 计时器逐像素相同（静态结算屏），亦只描述**后续窗**画面。 | **未知**：本窗 19.332772 s 停顿原因、本窗内是否已进入结算。已查 `measure_w0/w1/w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt`、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:54-77` 仍是**缺**。 |
| 5 | **`archive_T38/w1`**<br>`.../archive_T38/measure_w1.json`<br>尾 `2026-10-18 06:06:58.607Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；**`measure_w1_end_x.png` 虽在盘，但 mtime 为 `2026-10-18 04:53:27.657Z`，对窗尾 Δ`−4410.949692s`（≈ −1.23 小时）**，与窗尾**严重不符**；`qc151_fields.json:measure_forensics_w1` 明记 `empty_window=False`、无 `forensics_png`、无 `capture_ok`（即 harness 声明**该窗没有落图**），且 `focus_ok=False`。 | **不可确认，且该同名文件明确为磁盘残留件**：本轮实测其 sha256 `c1c1dbbd0881e694a1bea969b1de0ea1f056f9ce2f125f3077a04d195985fdb2`，与 `archive_T36/measure_w1_end_x.png` **逐字节相同**（同 269628 B、mtime 同到微秒）；与 `S544_TRI_MODEL_VERDICT_20261104.md:114`（错误清单第 2 条：「**磁盘残留件**：mtime 比窗尾早 4410.95 秒，与 T36/w1 同 sha `c1c1dbbd`」）一致。**不得把这残留件当作本窗或本趟的时序证据**。另有 `navsig_burst_01_g.png` Δ`−6560.752s` 等同趟数小时级残留件。（`S543_FREEZE_WAS_SCORESCREEN_20261104.md:72-77, 213-214` 曾把该残留件当「T38/w1 屏显 00:00:10 / 1 帧级时间错位」，该判读已被 `S544_TRI_MODEL_VERDICT_20261104.md:113-114`、`RULING.md:105` 撤回，**不再采信**。） | **有**。`w2`：`logic_frames=0`、`df=0`。**仅停摆序列**。 | **有（终局关联旁证，级别受限；不含 w1 残留件）**。后续 `w2` 的 `measure_w2_end_x.png` 存在，mtime `06:07:23.773Z`，对**其自身窗尾** `06:07:23.634Z` Δ`+0.138980s`（在 +0.05~+0.20），`qc151_fields.json:measure_forensics_w2` 声明一致且 `capture_ok=true`（但 `focus_ok=False`）；`_leader_fullcensus_out.txt:65` 记 `p=0.349 a7ca0134817abdd7 计分屏(待目视)`（**材料记载**）。⇒ 仅 w2 采图时刻的终局/结算界面旁证。**`measure_w1_end_x.png` 残留件不参与任何正面证据**；`RULING.md:105` 明确不得再用已撤回的 T38 时间/截图时序作依据。 | **未知**：本窗 24.077365 s 停顿原因、`w1` 残留件的来源与落盘路径（只知与 T36/w1 同字节，不知谁在何时拷入）、`focus_ok=False` 对截图内容的影响、本窗内阶段。已查 `measure_w1.json`、`measure_w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt`、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:67-77`、`S544_TRI_MODEL_VERDICT_20261104.md:113-114` 仍是**缺**。 |
| 6 | **`archive_T39/w1`**<br>`.../archive_T39/measure_w1.json`<br>尾 `2026-10-18 07:51:30.070Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w1_end_x.png` 不存在；`measure_forensics_w1` 记 `empty_window=False`、无 png、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。同趟 `measure_w2_end_x.png` Δ`+25.097439s`（相对本窗窗尾）不在窗内；`frame_target_01.png` Δ`−54.044s` 为窗前开局帧；`navsig_nav_start_pre_03_g.png` 等偏离 `−34813.986s` 属**磁盘残留件**。 | **有**。`w2`：`logic_frames=0`、`df=0`。**仅停摆序列**。 | **有（终局关联旁证，级别受限）**。后续 `w2` 的 `measure_w2_end_x.png` 存在，mtime `07:51:55.167Z`，对其自身窗尾 `07:51:55.085Z` Δ`+0.082308s`，`qc151_fields.json:measure_forensics_w2` 声明一致、`capture_ok=true`；`_leader_fullcensus_out.txt:66` 记 `p=0.349 253956a689cf1ee6 计分屏(待目视)`（**材料记载**）。⇒ 仅 w2 采图时刻的终局/结算界面旁证，不覆盖本窗整段。 | **未知**：本窗 23.981746 s 停顿原因、本窗内阶段、`w1` 为何无末图。已查 `measure_w1/w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt` 仍是**缺**。 |
| 7 | **`archive_T43/w0`**<br>`.../archive_T43/measure_w0.json`<br>尾 `2026-10-18 08:23:11.367Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w0_end_x.png` 不存在；`measure_forensics_w0` 记 `empty_window=False`、无 png、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。同趟 `measure_w1_end_x.png` Δ`+25.114727s`、`measure_w2_end_x.png` Δ`+50.209925s`（相对本窗窗尾）不在窗内；`frame_target_01.png` Δ`−29.041s` 为窗前开局帧；`navsig_nav_start_pre_03_g.png` 偏离 `−36715.283s` 属**磁盘残留件**。 | **有**。`w1`：`logic_frames=0`、`df=0`；`w2`：`logic_frames=0`、`df=0`。**仅停摆序列**。 | **有（终局关联旁证，级别受限）**。`w1`/`w2` 两图存在、声明一致、`capture_ok=true`，对各自窗尾 Δ`+0.101206s` / `+0.094192s`；`_leader_fullcensus_out.txt:73-74` 记均 `p=0.349 计分屏(待目视)`（**材料记载**）；`S543_FREEZE_WAS_SCORESCREEN_20261104.md:65` 记计时器 w1/w2 逐像素相同。⇒ 仅后续窗采图时刻的终局/结算界面旁证，不覆盖本窗整段。 | **未知**：本窗 19.188367 s 停顿原因、本窗内阶段。已查 `measure_w0/w1/w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt` 仍是**缺**。 |
| 8 | **`archive_T47/w0`**<br>`.../archive_T47/measure_w0.json`<br>尾 `2026-10-18 09:55:16.030Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w0_end_x.png` 不存在；`measure_forensics_w0` 记 `empty_window=False`、无 png、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。`frame_target_01.png` Δ`−29.035s` 为窗前开局帧；`navsig_nav_start_pre_03_g.png` 等偏离 `−42239.946s` 属**磁盘残留件**。同趟 `measure_w1_end_x.png` / `measure_w2_end_x.png` **连文件都不存在**（无 mtime 可比对）。 | **有**。`w1`：`logic_frames=0`、`df=0`；`w2`：`logic_frames=0`、`df=0`。**仅停摆序列，不得外推原因**。 | **无／未知**。后续 `w1`/`w2` **无截图**：本轮实测两文件 `exists=False`；但 `qc151_fields.json:measure_forensics_w1/w2` 却声明 `empty_window=True`、`forensics_png=measure_w1_end_x.png` / `measure_w2_end_x.png`、`capture_ok=true`（**声明与盘面不一致，记为未知，不猜原因**）。`S543_FREEZE_WAS_SCORESCREEN_20261104.md:222` 明记 `archive_T47 w1/w2 无截图`。**不得靠后续 `df==0` 确证终局（H2）**；不得拿别趟、别的计分屏凑证（`RULING.md:120`）。 | **未知**：本窗 6.618178 s 停顿原因、本窗内阶段、后续两窗「声明有图但盘面无图」的原因、终局归属。已查 `measure_w0/w1/w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt`、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:218-230`、`RULING.md:120` 仍是**缺**。 |
| 9 | **`archive_T49_u0800/w0`**<br>`.../archive_T49_u0800/measure_w0.json`<br>尾 `2026-10-18 10:11:46.682Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w0_end_x.png` 不存在；`measure_forensics_w0` 记 `empty_window=False`、无 png、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。同趟 `measure_w1_end_x.png` Δ`+25.093054s`、`measure_w2_end_x.png` Δ`+50.172883s`（相对本窗窗尾）不在窗内；`frame_target_01.png` Δ`−29.028s` 为窗前开局帧；`navsig_nav_start_pre_03_g.png` 偏离 `−43230.598s` 属**磁盘残留件**。 | **有**。`w1`：`logic_frames=0`、`df=0`；`w2`：`logic_frames=0`、`df=0`。**仅停摆序列**。 | **有（终局关联旁证，级别受限）**。`w1`/`w2` 两图存在、声明一致、`capture_ok=true`，对各自窗尾 Δ`+0.077891s` / `+0.079829s`；`_leader_fullcensus_out.txt:79-80` 记均 `p=0.349 计分屏(待目视)`（**材料记载**）；`S543_FREEZE_WAS_SCORESCREEN_20261104.md:66` 记计时器 w1/w2 逐像素相同。⇒ 仅后续窗采图时刻的终局/结算界面旁证，不覆盖本窗整段。 | **未知**：本窗 14.820029 s 停顿原因、本窗内阶段。已查 `measure_w0/w1/w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt` 仍是**缺**。 |
| 10 | **`l3_20261023r/w1`**<br>`.../l3_20261023r/measure_w1.json`<br>尾 `2026-10-30 13:02:08.958Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w1_end_x.png` 不存在；`measure_forensics_w1` 记 `empty_window=False`、无 png、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。同趟 `measure_w2_end_x.png` Δ`+25.123816s`（相对本窗窗尾）不在窗内；`frame_target_01.png` Δ`−54.074s` 为窗前开局帧。 | **有**。`w2`：`logic_frames=0`、`df=0`。**仅停摆序列**。 | **有（终局关联旁证，级别受限）**。后续 `w2` 的 `measure_w2_end_x.png` 存在，mtime `13:02:34.082Z`，对其自身窗尾 `13:02:33.982Z` Δ`+0.099388s`，`qc151_fields.json:measure_forensics_w2` 声明一致、`capture_ok=true`；`_leader_fullcensus_out.txt:82` 记 `p=0.347 7045326f8051b197 计分屏(待目视)`（**材料记载**）；`S543_FREEZE_WAS_SCORESCREEN_20261104.md:81-94` 记该图为**完整终局比分**结算屏（126/146 摧毁、201034/126800 分）。⇒ 仅 w2 采图时刻的终局/结算界面旁证；且 `S544_TRI_MODEL_VERDICT_20261104.md:116` 已把比分读数订正为 `126/206/0/201034` 与 `198/731/4/126800`，`RULING.md:105` 要求不再用已撤回支柱强化终局归因。**不覆盖本窗 9.436278 s 停顿的每一时刻**。 | **未知**：本窗 9.436278 s 停顿原因、本窗内阶段、`w1`→`w2` 阶段转换时点。已查 `measure_w1/w2.json`、`qc151_fields.json`、`_leader_fullcensus_out.txt`、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:81-94`、`S544_TRI_MODEL_VERDICT_20261104.md:116` 仍是**缺**。 |
| 11 | **`l3_20261023q/w2`**　★单列「**未知阶段停摆**」<br>`.../l3_20261023q/measure_w2.json`<br>尾 `2026-10-30 12:50:40.467Z` | **否**。窗尾 +0.05~+0.20 s 内命中 0；`measure_w2_end_x.png` 不存在；`measure_forensics_w2` 记 `empty_window=False`、无 png、无 `capture_ok`。**`mtime：不适用`**。 | **不可确认**（当窗无图）。`frame_target_01.png` mtime `12:49:21.388Z`、Δ`−79.079s`，为窗**前**开局帧，不是窗末图。 | **无**。该趟 `w0`：`logic_frames=778`、`df=778`；`w1`：`logic_frames=782`、`df=782`；本窗 `w2` 是最后一窗，`logic_frames=120`、`df=120`。数据根内无 `measure_w3+`（本轮 `CHECK: any measure_w3+ ... []`）。⇒ **没有后续零推进窗作同向序列证据**（`RULING.md:118`、`XVERIFY_S544_c1606d35/VERDICT.md:73`）。 | **无／未知**。**不得标「已证终局」，也不标「正常终局」**（H1）。全趟三窗均 `empty_window=False`，harness 未落任何 `end_x` 图；无后续计分屏、无时序可确认的终局图。 | **未知**：本窗 21.155847 s 停顿的原因、战术阶段、是否/何时进入终局、`df=120` 后是否还有未采样时间。已查 `measure_w0/w1/w2.json`、`qc151_fields.json`（三窗 forensics 均非空窗、无 png）、`_leader_fullcensus_out.txt`、`RULING.md:118` 仍是**缺**。单列**未知阶段停摆**。 |

<!-- BEGIN ASSEMBLER CONFLICT NOTE C5 -->
> ⚠️ **【组装员冲突标注 · C5｜见 C4：本表与 `EX2_ERRATA.md` 的比分／屏显数值冲突，原样保留，不调和】**
> 本表第 5 行的 `00:00:10` 与 `EX2_ERRATA.md:112` 的 `00:00:32`；本表第 10 行的 `126/146 摧毁、201034/126800 分` 与
> `EX2_ERRATA.md:111` 的 `126/206/0/201034`、`198/731/4/126800` 及「旧读数不得再引用」——**全部照录，不调和、不判定**。
> 另本表第 1/3/5 行的 `9.574864 s` / `24.734761s` / `24.077365 s` 与 `EX2_ERRATA.md:88` 的 `9.575s` / `24.077s` 见 C1/C3。（组装员添加，非碎片原文）
<!-- END ASSEMBLER CONFLICT NOTE C5 -->

**表中 `.../` 均为前缀 `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/` 的省略；每个窗的完整绝对路径见 §2 清单。**

---

## 2. 11 窗绝对路径清单（不省略，供逐条追溯）

| # | 窗标识 | 绝对原件路径 |
|---|---|---|
| 1 | `archive_T32/w0` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T32/measure_w0.json` |
| 2 | `archive_T33/w0` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T33/measure_w0.json` |
| 3 | `archive_T34/w0` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T34/measure_w0.json` |
| 4 | `archive_T36/w0` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T36/measure_w0.json` |
| 5 | `archive_T38/w1` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T38/measure_w1.json` |
| 6 | `archive_T39/w1` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T39/measure_w1.json` |
| 7 | `archive_T43/w0` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T43/measure_w0.json` |
| 8 | `archive_T47/w0` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T47/measure_w0.json` |
| 9 | `archive_T49_u0800/w0` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T49_u0800/measure_w0.json` |
| 10 | `l3_20261023r/w1` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261023r/measure_w1.json` |
| 11 | `l3_20261023q/w2` | `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261023q/measure_w2.json` |

对应 `qc151_fields.json` 同目录；`end_x` 截图同目录，文件名在各行⑤列写明。

### 2.1 按裁决 D-15.3 的证据分组（`RULING.md:115-120`）

| 分组 | 窗 | 本轮核实结果 |
|---|---|---|
| 前 10 窗（除 q/w2 外的 9 个 archive 窗 + `l3_20261023r/w1`） | #1–#10 | 10/10 同趟后续有整窗零推进（`logic_frames==0` 且 `df==0`），**只证明停摆序列**。其中 #2、#3、#4、#5、#6、#7、#9、#10 共 8 窗另有「来源/时序可确认的后续计分屏」→ 可注**终局关联旁证**；#1、#8 两窗后续冻结窗**无截图** → 无可确认终局证据。 |
| `l3_20261023q/w2` | #11 | 无后续零推进窗；单列**未知阶段停摆**，不标已证终局、不标正常终局。 |

**分组只作证据用途登记，不是本轮独立图像核验**（`RULING.md:120`）。裁决还提示 `S543_FREEZE_WAS_SCORESCREEN_20261104.md:30-43` 与 `:200-201` 的计分屏趟名单本身未完全一致，本表**不强凑一个已确认图像子集数**；每一窗的图像判读均只按 `_leader_fullcensus_out.txt:57-82` 的逐窗行转述，未跨窗补齐。另：`RULING.md:120` 明确「这里 11 个有推进停摆窗，与 32 个零推进窗中『11 个未充分覆盖窗』不是同一集合」——本表**不把两者混谈**。

---

## 3. 本轮实际执行的检查（命令与输出）

全部为**离线只读**，未启动 `gamemd.exe`/`ra2loader.exe`/YURI，未 taskkill，未读运行中进程内存，未改动任何真机 json/png、核验件、`RULING.md`/`FACTBASE.md`/`RECHECK.md`、台账或 `PENDING_DECISIONS.md`，未 commit，未写任何采样/探针/注入脚本。Python 一律 `python -I -X utf8`，路径一律绝对路径。所有原始 JSON 为单行文件，源码位置均为各文件第 1 行（引用按 `路径:1` 记）。

**检查 A：11 窗名单与 33 计数独立重建** —— 命令与实际 stdout 见 §0.1。结果 `104` 份 JSON、`11` 个停摆主导窗、`33` 个 25 秒低 avg 窗，与 `EX1_DATAFACE.md:148-162`、裁决 `RULING.md:81` 一致。

**检查 B：当窗末截图存在性与时序（题定 +0.05~+0.20 s 判据）**。命令：

```bash
python -I -X utf8 - <<'PY'
import json, os, glob
data=r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
trips=[('archive_T32','measure_w0.json'),('archive_T33','measure_w0.json'),('archive_T34','measure_w0.json'),('archive_T36','measure_w0.json'),('archive_T38','measure_w1.json'),('archive_T39','measure_w1.json'),('archive_T43','measure_w0.json'),('archive_T47','measure_w0.json'),('archive_T49_u0800','measure_w0.json'),('l3_20261023q','measure_w2.json'),('l3_20261023r','measure_w1.json')]
for trip,fn in trips:
    d=os.path.join(data,trip)
    j=json.load(open(os.path.join(d,fn),encoding='utf-8'))
    tail=j['t_abs0']+j['span_s']
    pngs=sorted(glob.glob(os.path.join(d,'*.png')))
    near=[]
    for f in pngs:
        delta=os.stat(f).st_mtime-tail
        if 0.05<=delta<=0.20: near.append((os.path.basename(f),delta))
    print('%-20s stallTail=%f pngCount=%3d near(+0.05..+0.20)=%s'%(trip,tail,len(pngs),near))
PY
```

实际 stdout（11 行，全部 `near=[]`）：

```text
archive_T32          stallTail=1792285980.913532 pngCount= 49  near(+0.05..+0.20)=[]
archive_T33          stallTail=1792295145.590396 pngCount= 51  near(+0.05..+0.20)=[]
archive_T34          stallTail=1792297087.086869 pngCount= 50  near(+0.05..+0.20)=[]
archive_T36          stallTail=1792299182.566726 pngCount= 57  near(+0.05..+0.20)=[]
archive_T38          stallTail=1792303618.607058 pngCount= 57  near(+0.05..+0.20)=[]
archive_T39          stallTail=1792309890.070121 pngCount= 58  near(+0.05..+0.20)=[]
archive_T43          stallTail=1792311791.367030 pngCount= 55  near(+0.05..+0.20)=[]
archive_T47          stallTail=1792317316.030230 pngCount= 53  near(+0.05..+0.20)=[]
archive_T49_u0800    stallTail=1792318306.682727 pngCount= 55  near(+0.05..+0.20)=[]
l3_20261023q         stallTail=1793364640.467545 pngCount=  9  near(+0.05..+0.20)=[]
l3_20261023r         stallTail=1793365328.958254 pngCount= 10  near(+0.05..+0.20)=[]
```

补充范围检查：对**整个数据根 + lead 镜像树共 2254 张 PNG** 逐个比对 11 个停摆窗窗尾，`total aligned hits for stall-window tails: 0`（本轮执行）。⇒ **11/11 当窗末截图均未实际落盘**，第 2、3 列因此全部为「否／不可确认」。这与其 `qc151_fields.json` 的 `measure_forensics_w{k}` 一致：当窗 `empty_window=False`（无图声明），只有 `archive_T32` 连 forensics 记录都缺。

**检查 C：时序框架自洽性（JSON 自身 mtime 对窗尾）**。命令见 §0.2 同源脚本，实际 stdout：

```text
  archive_T32          measure_w0.json    delta=+0.021791s t_clock=time.perf_counter
  archive_T33          measure_w0.json    delta=+0.019614s t_clock=time.perf_counter
  archive_T34          measure_w0.json    delta=+0.018125s t_clock=time.perf_counter
  archive_T36          measure_w0.json    delta=+0.013793s t_clock=time.perf_counter
  archive_T38          measure_w1.json    delta=+0.026548s t_clock=time.perf_counter
  archive_T39          measure_w1.json    delta=+0.014128s t_clock=time.perf_counter
  archive_T43          measure_w0.json    delta=+0.013521s t_clock=time.perf_counter
  archive_T47          measure_w0.json    delta=+0.013859s t_clock=time.perf_counter
  archive_T49_u0800    measure_w0.json    delta=+0.015163s t_clock=time.perf_counter
  l3_20261023q         measure_w2.json    delta=+0.017914s t_clock=time.perf_counter
  l3_20261023r         measure_w1.json    delta=+0.023427s t_clock=time.perf_counter
```

⇒ `t_abs0+span_s` 与文件系统 mtime 同一墙钟口径，判据可计算。

**检查 D：全部 27 张 `end_x` 截图对其「各自窗尾」的对齐**（本轮执行），实际 stdout 关键行：

```text
archive_T33/measure_w1_end_x.png        delta=+0.084068s OK
archive_T33/measure_w2_end_x.png        delta=+0.089937s OK
archive_T34/measure_w1_end_x.png        delta=+0.079328s OK
archive_T34/measure_w2_end_x.png        delta=+0.081706s OK
archive_T36/measure_w1_end_x.png        delta=+0.076847s OK
archive_T36/measure_w2_end_x.png        delta=+0.094500s OK
archive_T38/measure_w1_end_x.png        delta=-4410.949692s MISMATCH
archive_T38/measure_w2_end_x.png        delta=+0.138980s OK
archive_T39/measure_w2_end_x.png        delta=+0.082308s OK
archive_T43/measure_w1_end_x.png        delta=+0.101206s OK
archive_T43/measure_w2_end_x.png        delta=+0.094192s OK
archive_T49_u0800/measure_w1_end_x.png  delta=+0.077891s OK
archive_T49_u0800/measure_w2_end_x.png  delta=+0.079829s OK
l3_20261023r/measure_w2_end_x.png       delta=+0.099388s OK
```

⇒ 除 `archive_T38/measure_w1_end_x.png` 外，26/27 张时序可确认；**唯一 MISMATCH 是数小时级偏离的磁盘残留件**，已在第 5 行③列点名。另 `archive_T32`、`archive_T47` 的 w1/w2 图**根本不在 27 张清单内**（`exists=False`），但 T47 的 `qc151_fields.json` 仍声明了文件名与 `capture_ok=true`，该不一致已如实写进第 8 行。

**检查 E：残留件字节同一性**（本轮执行）：

```text
  T38/w1 sha256 = c1c1dbbd0881e694a1bea969b1de0ea1f056f9ce2f125f3077a04d195985fdb2
  T36/w1 sha256 = c1c1dbbd0881e694a1bea969b1de0ea1f056f9ce2f125f3077a04d195985fdb2
  identical = True size 269628 269628
```

与 `S544_TRI_MODEL_VERDICT_20261104.md:114` 的 sha16 `c1c1dbbd`、269628 B、4410.95 秒记载一致。

**检查 F：同一趟后续窗零推进读数和 `qc151_fields.json` 声明**（本轮执行），命令/输出要点：

```text
CHECK: any measure_w3+ anywhere in data root? []
CHECK: subsequent-window zero-advance per trip (exact)
  archive_T32          w0:lf=482,df=482 | w1:lf=0,df=0 | w2:lf=0,df=0
  archive_T33          w0:lf=444,df=444 | w1:lf=0,df=0 | w2:lf=0,df=0
  archive_T34          w0:lf=9,df=9     | w1:lf=0,df=0 | w2:lf=0,df=0
  archive_T36          w0:lf=178,df=178 | w1:lf=0,df=0 | w2:lf=0,df=0
  archive_T38          w0:lf=780,df=780 | w1:lf=29,df=29 | w2:lf=0,df=0
  archive_T39          w0:lf=781,df=781 | w1:lf=32,df=32 | w2:lf=0,df=0
  archive_T43          w0:lf=182,df=182 | w1:lf=0,df=0 | w2:lf=0,df=0
  archive_T47          w0:lf=575,df=575 | w1:lf=0,df=0 | w2:lf=0,df=0
  archive_T49_u0800    w0:lf=317,df=317 | w1:lf=0,df=0 | w2:lf=0,df=0
  l3_20261023q         w0:lf=778,df=778 | w1:lf=782,df=782 | w2:lf=120,df=120
  l3_20261023r         w0:lf=783,df=783 | w1:lf=484,df=484 | w2:lf=0,df=0
```

⇒ 10/11 有后续整窗零推进；`l3_20261023q/w2` 无（且是末窗）。forensics 声明逐窗输出（含 `archive_T47` 声明有图但 `on_disk=False`、`archive_T32` 无 forensics 记录）已用于 §1 各行③/⑤列；`capture_ok` 缺失一律写「缺」，未补造。

**检查 G：未运行／未验证的项**（如实登记）：本轮未做 PNG 目视或 OCR；未重算 104 份全库统计、21/32 图像覆盖、旧 1734 段/87.7%、ρ/φ、argv/BOOT 归属、异常件普查、12 份镜像逐字节比对；未做运行期实验、E3 或项目测试；未启动/读取活进程。表中所有「计分屏／无面板／完整终局比分」均为**材料记载**，证据等级按 `RULING.md:197` 的「他方原件核验，本裁决未重做」处理。

---

## 4. 验收对照（逐条对应题定 4 条硬约束 + 6 列）

| 判据 | 结论 | 证据位置 |
|---|---|---|
| **H1 `l3_20261023q/w2` 不得标「已证终局」，单列「未知阶段停摆」** | **满足**。该行⑤列写「无／未知；不得标已证终局，也不标正常终局」，⑥列写「单列未知阶段停摆」；④列写「无」后续零推进。依据本轮 `CHECK F`（w0/w1/w2 分别 df=778/782/120，无 w3+）与 `RULING.md:118`。 | §1 第 11 行、§2 清单第 11 行、§2.1 分组表、§3 检查 F |
| **H2 `archive_T32/w0` 与 `archive_T47/w0` 不得靠后续 `df==0` 确证终局（后续冻结窗无截图）** | **满足**。两行④列只报 `logic_frames=0, df=0` 读数并注明「仅停摆序列」；⑤列明写「无／未知」「后续 w1/w2 均无截图」「不得靠后续 `df==0` 确证终局（H2）」。本轮实测 T32 两图 `exists=False` 且无 forensics 记录；T47 两图 `exists=False`（`qc151_fields.json` 却声明 `capture_ok=true`，不一致如实记为未知）。与 `S543_FREEZE_WAS_SCORESCREEN_20261104.md:221-222`、`RULING.md:120` 一致。 | §1 第 1、8 行、§2.1、§3 检查 F、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:221-222` |
| **H3 11 窗整组不得计为「已证在战机制」或「已证终局」** | **满足**。文首、§1 表头、§2.1 之后、本节均固定「停摆观测、待归因」；8 个有后续计分屏的窗只写「**终局关联旁证**」并逐行限定「仅采图时刻／不覆盖本窗整段／后续零推进不得自动等同计分屏」，无一行把整窗判成已证终局或在战机制正证。 | 文首、§0.5 H3、§1 各行⑤列、§2.1、`RULING.md:111,117` |
| **H4 本表不得用来删改原始 33 个低 avg 计数** | **满足**。§0.1 本轮独立重建 `25s low avg= 33`；文首与 §1 明写「主指标计数仍为 33，核心持续低速分析仍为 22 窗/8 趟」；全表未删除、未重分类、未改写任何窗的 `fps_avg`。 | §0.1（命令与 stdout）、文首、§1 表头、`RULING.md:81-83,111,168` |
| **列 1 窗标识（趟名/窗号）与绝对路径** | **满足**，恰好 11 行，每行含趟名/窗号；§2 另给 11 条不省略的完整绝对路径。 | §1 列①、§2 清单 |
| **列 2 当窗末截图是否实际落盘（文件存在？mtime 是否与窗尾相符？）** | **满足**。11/11 写「否」，并给出窗尾绝对时刻、遍历该趟 PNG 的命中数 0、`mtime 与窗尾相符：不适用（无文件）`；`archive_T38/w1` 特别说明同名文件虽在盘但 Δ`−4410.949692s` 与窗尾**严重不符**。 | §1 列②、§3 检查 B/C/D |
| **列 3 截图来源与时序是否可确认（+0.05~+0.20 s；偏离数小时标磁盘残留件）** | **满足**。11/11 判「不可确认」并说明来源通道（`qc151_fields.json` 的 `empty_window=False`／记录缺）；逐窗点名数小时级候选件为**磁盘残留件**（含 T38/w1 的 −4410.95 s 与 T36/w1 同 sha）；判据在 §0.2 定义并在 §3 检查 B/C 实测。 | §1 列③、§0.2/§0.3、§3 检查 B/C/D/E |
| **列 4 同一趟后续窗是否有整窗零推进（`logic_frames==0` 或 `df==0`）** | **满足**。10 行写「有」并给逐窗 `logic_frames`/`df`；第 11 行写「无」并给 w0/w1/w2 读数与「无 w3+」。每行注明「仅停摆序列，不证明本窗停顿原因」。 | §1 列④、§3 检查 F |
| **列 5 是否有可确认的终局关联证据** | **满足**。8 行写「有（终局关联旁证，级别受限）」并给出后续窗截图文件名、mtime、对**其自身窗尾**的 Δ（全部 +0.076847~+0.138980 s）、`capture_ok=true`、材料记载的计分屏判读及「仅采图时刻」限定；3 行（T32、T47、q/w2）写「无／未知」。T33/w2 无面板、T38/w1 残留件明确排除出正面证据。 | §1 列⑤、§0.4、§3 检查 D/E、§2.1 |
| **列 6 未知项：查不到的一律写「未知」** | **满足**。11/11 有「未知」段，逐行列明未知内容（本窗停顿运行期原因、本窗内战术阶段、阶段转换时点、声明与盘面不一致的原因等），并**注明查阅了哪些文件仍是缺**；未从其他窗/其他趟/推理填值。 | §1 列⑥、§0.4、§3 检查 G |
| **H5 绝不把「后续窗零推进」当成「本窗停顿的原因」** | **满足**。④列与⑤列分列且各自限定；`RULING.md:113-117,120` 的措辞在 §0.5 H5、§1 表头、§2.1、本节反复固定。 | §0.5 H5、§1 表头及各行④⑤、§2.1、`RULING.md:113-120` |

---

## 5. 与裁决其他部分的关系（不越界）

- 本表是 **EX-3 单项交付**，写到题定 `EX3_STALL_EVIDENCE.md`；未改 `RULING.md`、`FACTBASE.md`、`RECHECK.md`、`D15_IMPLEMENTATION_CANDIDATE.md`（未创建）、`D13_MECHANISM_GAP_AND_OFFLINE_CARD.md`（未创建）、台账、`PENDING_DECISIONS.md`、任何真机 json/png 或三路核验件。
- 22 窗核心集、25 对照、47 窗混杂控制字段属 EX-1／EX-4，本表不重复也不代填；33/38 的完整分母解释见 `EX1_DATAFACE.md` 与 `RULING.md:81-89`。
- 「追加勘误、历史原文不改」属 EX-2；D-13「当前 E3→① 不执行、0/22 阈值覆盖」属 EX-4。本表不涉及其结论，也不写任何采样代码。
- `RULING.md:122`：完成 EX-3 时**允许明确未知**，不要求补真机，也不以未知阻塞结案。本表的 11 个「未知」按此处置。

---

## 5. 自检与缺口

> 本节为组装员汇总：5.1 是本次组装的三段齐全性自检；5.2–5.4 逐份列出三份碎片各自的 `acceptance`（验收自查表）与 `gaps`（边界／未做／缺项）**原文引文**（表格逐行照录；段落引文仅加 `> ` 引用前缀，正文原样）；5.5 是冲突清单；5.6 是本轮实际执行的检查与未复核项。

### 5.1 三段齐全性自检（组装员本次执行）

| 段 | 落点 | 照录来源 | 行数 | 冲突标注 | 去标注后与碎片原文一致 |
|---|---|---|---:|---|---|
| 1 抬头 | 本文件第 1 节 | `RULING.md` / `RECHECK.md`（抬头说明） | — | — | 不适用（组装员撰写） |
| 2 数据面 | 本文件第 2 节 | `EX1_DATAFACE.md` 全文 | 347 | C1、C2 | PASS |
| 3 追加勘误候选 | 本文件第 3 节 | `EX2_ERRATA.md` 全文 | 146 | C3、C4 | PASS |
| 4 11 窗证据表 | 本文件第 4 节 | `EX3_STALL_EVIDENCE.md` 全文 | 284 | C5、C6 | PASS |
| 5 自检与缺口 | 本文件第 5 节 | 三份碎片的自查表／边界段 | — | C1–C6 汇总 | 不适用（组装员汇总） |

校验方式（在组装命令内执行）：把每个 `<!-- BEGIN/END ASSEMBLER CONFLICT NOTE C* -->` 块从各段中精确删除，再与原碎片解码字符串做 `==` 比较；三项均为 `True`。落盘后的独立复核命令见 5.6 第 10 条。

### 5.2 `EX1_DATAFACE.md` 的 `acceptance` 与 `gaps`

**`acceptance` 原文表**（`EX1_DATAFACE.md:334-343`，§8「逐条验收自查与边界」）：

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

**`gaps` 原文引文**（`EX1_DATAFACE.md:233-243` 缺格统计表、`:245`、`:261`、`:345`）：

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

> **harness 版本/哈希大面积缺失**：47 窗中有 **25** 窗从 `_launch_result.json` 取不到 `harness_sha16`，表中已逐行写「缺」。逐趟查阅的绝对路径（全部为本数据根下的绝对路径，只读；不存在者如实标注）：
>
> 此外，对全部 104 份 `measure_w*.json` 做过**完整递归键扫描**（不只顶层；结果在 `ex1_checks.txt`）：**没有任何 harness 版本或哈希键**。对根目录层查过 `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip` 下文件名含 `harness`/`launch` 的清单（`_l1b_launch_out.txt`、`_launch_l1b.py`、`t55_launch.log`、`t55_launch_4b.log`、`t55_launch_c.log`、`t55_launch_d.log`），这些是发射日志/脚本，不是 47 窗所属趟的 `harness_sha16` 记录，不用于代填。
>
> **边界与未做**：未启动 gamemd.exe / ra2loader.exe / YURI，未 taskkill，未读活进程内存，未改任何既有件，未 commit。未重算 104 份的 `stats`（只照抄原存值），未重算 22 窗的 `max_stall_s`（只取第 3.2 节原存值），未目视/OCR 任何 PNG，未核截图时序/哈希，未做真机发射或运行期采样。写入仅 `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/EX1_DATAFACE.md`、机器可读副件 `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/ex1_rebuild.json` 与 stdout 副本 `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/ex1_checks.txt`，均在指定写域内。

### 5.3 `EX2_ERRATA.md` 的 `acceptance` 与 `gaps`

**`acceptance` 原文表**（`EX2_ERRATA.md:136-144`，§3「逐条验收自查与边界」）：

| # | 判据 | 落实位置 |
|---|---|---|
| 1 | 明确撤销四项归因（整批战斗段完全冻结／引擎停摆已定谳／「永不恢复」超窗机制化／凭停帧形态证明静态路径历史命中），且不写成已证相反结论 | 545.2 第 1–4 项 + 「撤销的是肯定归因，不是已证相反结论」段 |
| 2 | 保留帧号/时间/零推进计数；保留 §540/§541 静态字节结论；声明不得再冒充运行期定位证据；缺项写「缺」并列查阅件 | 545.3(1)、545.3(2) |
| 3 | 证据范围写死 21/32、未覆盖窗归「零推进、原因未定」、不贴停摆标签也不改记终局 | 545.4 |
| 4 | 22 + 11 + 5 分层、33/38 分母、报数规定、`fps_avg` 主指标 | 545.5 |
| 5 | 三项被证伪旧支柱只作「已撤回、禁止复用」列出并给出正确值，不作依据 | 545.6；禁用扫描见第 0 节检查 C |
| 6 | 每处引用写「文件名 + 实际行号」；显式说明散件 §538/§539 与台账同号章节不是同文；台账行号经 grep 核实 | 545.1、全篇引用；第 0 节检查 A |
| 7 | `l3_1101v4c` 三窗序列标明 `fps_avg` 与派生 `live_fps` 身份 | 545.7；第 0 节检查 B |

**`gaps` 原文引文**（`EX2_ERRATA.md:44`、`:46`、`:90`、`:146`）：

> **检查 C**：追加正文的「已撤回旧支柱」禁用扫描在成文后执行，零命中；为避免把被撤回的数值/定性重新写进本件，扫描式样与输出不落在本文件内，记于交付结果的第 5 条验收自查。
>
> **未做的检查（如实登记）**：未重跑 104 份全库重建、未重算 22 窗整体覆盖率、未新读/OCR 任何 PNG、未核截图时序/哈希、未做真机发射或运行期实验、未跑项目测试。21/32 覆盖与计分屏判定沿用已读原件，不冒充本件独立复核（`RULING.md:197`、`RECHECK.md:82`）。
>
> **(2) `GOAL_THREE_TARGETS_20261018.md:4003`（§540）与 `GOAL_THREE_TARGETS_20261018.md:4091`（§541）的静态字节结论不随本次勘误撤回**：`GOAL_THREE_TARGETS_20261018.md:4041–4050` 的四条字节断言复算（`0x55D877` 处 `c3`、`0x684174` 为 `inc [eax+0x62C]`、MLF 三 ret、`[0xA8B230]` 三写点，`:4050` 判「四条全部通过」）与 `GOAL_THREE_TARGETS_20261018.md:4114–4128` 的 `BATCH1_VERDICT.md` 字节主线表（`+0x62C` 挂起深度计数器写点恰 3 处、`0x55D877` 双门、`CurrentFrame` 唯一 RMW 链）按「静态事实／候选路径」全部保留（`RULING.md:97`「静态字节结论与运行期因果归因分开，§540/§541 字节结论不得随此自动撤回，也不得继续冒充运行期定位证据」、`RULING.md:155`）。**但它们不得再冒充运行期定位证据**：台账 `GOAL_THREE_TARGETS_20261018.md:4067–4075`（语义推断链未复核、P01 未经异族核验、§四解读属推测）与 `GOAL_THREE_TARGETS_20261018.md:4130–4137`（行为学问题不可判定）已自陈这一限度（`RULING.md:197`）。**运行期耗时落点、以及该静态路径在历史趟是否命中：缺**；已查阅 `RULING.md:155`、`RULING.md:197`、`RULING.md:202`、`_LEADER_FREEZE_INSTANT_20261104.md:100–102` 仍无该证据，按「缺」登记，不据其他窗/其他趟/推理补值（`RECHECK.md:82` 记本线未新读 PNG、未核截图时序/哈希、未做运行期实验）。
>
> **边界**：本件只出文档，未写任何采样/注入/运行期探针脚本；第 0 节检查 B 是一次只读字段核对（内联 `python -I -X utf8 -c`，绝对路径，未产生脚本文件）。未改台账/PENDING/RULING/RECHECK/FACTBASE/核验件/真机件，未 commit。数据面数字引用上一阶段 `EX1_DATAFACE.md`，本件未重跑其重建脚本；21/32 覆盖、截图时序与计分屏判定沿用已读原件，未在本件独立复核（`RULING.md:197`、`RECHECK.md:82`）。

### 5.4 `EX3_STALL_EVIDENCE.md` 的 `acceptance` 与 `gaps`

**`acceptance` 原文表**（`EX3_STALL_EVIDENCE.md:263-275`，§4「验收对照」）：

| 判据 | 结论 | 证据位置 |
|---|---|---|
| **H1 `l3_20261023q/w2` 不得标「已证终局」，单列「未知阶段停摆」** | **满足**。该行⑤列写「无／未知；不得标已证终局，也不标正常终局」，⑥列写「单列未知阶段停摆」；④列写「无」后续零推进。依据本轮 `CHECK F`（w0/w1/w2 分别 df=778/782/120，无 w3+）与 `RULING.md:118`。 | §1 第 11 行、§2 清单第 11 行、§2.1 分组表、§3 检查 F |
| **H2 `archive_T32/w0` 与 `archive_T47/w0` 不得靠后续 `df==0` 确证终局（后续冻结窗无截图）** | **满足**。两行④列只报 `logic_frames=0, df=0` 读数并注明「仅停摆序列」；⑤列明写「无／未知」「后续 w1/w2 均无截图」「不得靠后续 `df==0` 确证终局（H2）」。本轮实测 T32 两图 `exists=False` 且无 forensics 记录；T47 两图 `exists=False`（`qc151_fields.json` 却声明 `capture_ok=true`，不一致如实记为未知）。与 `S543_FREEZE_WAS_SCORESCREEN_20261104.md:221-222`、`RULING.md:120` 一致。 | §1 第 1、8 行、§2.1、§3 检查 F、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:221-222` |
| **H3 11 窗整组不得计为「已证在战机制」或「已证终局」** | **满足**。文首、§1 表头、§2.1 之后、本节均固定「停摆观测、待归因」；8 个有后续计分屏的窗只写「**终局关联旁证**」并逐行限定「仅采图时刻／不覆盖本窗整段／后续零推进不得自动等同计分屏」，无一行把整窗判成已证终局或在战机制正证。 | 文首、§0.5 H3、§1 各行⑤列、§2.1、`RULING.md:111,117` |
| **H4 本表不得用来删改原始 33 个低 avg 计数** | **满足**。§0.1 本轮独立重建 `25s low avg= 33`；文首与 §1 明写「主指标计数仍为 33，核心持续低速分析仍为 22 窗/8 趟」；全表未删除、未重分类、未改写任何窗的 `fps_avg`。 | §0.1（命令与 stdout）、文首、§1 表头、`RULING.md:81-83,111,168` |
| **列 1 窗标识（趟名/窗号）与绝对路径** | **满足**，恰好 11 行，每行含趟名/窗号；§2 另给 11 条不省略的完整绝对路径。 | §1 列①、§2 清单 |
| **列 2 当窗末截图是否实际落盘（文件存在？mtime 是否与窗尾相符？）** | **满足**。11/11 写「否」，并给出窗尾绝对时刻、遍历该趟 PNG 的命中数 0、`mtime 与窗尾相符：不适用（无文件）`；`archive_T38/w1` 特别说明同名文件虽在盘但 Δ`−4410.949692s` 与窗尾**严重不符**。 | §1 列②、§3 检查 B/C/D |
| **列 3 截图来源与时序是否可确认（+0.05~+0.20 s；偏离数小时标磁盘残留件）** | **满足**。11/11 判「不可确认」并说明来源通道（`qc151_fields.json` 的 `empty_window=False`／记录缺）；逐窗点名数小时级候选件为**磁盘残留件**（含 T38/w1 的 −4410.95 s 与 T36/w1 同 sha）；判据在 §0.2 定义并在 §3 检查 B/C 实测。 | §1 列③、§0.2/§0.3、§3 检查 B/C/D/E |
| **列 4 同一趟后续窗是否有整窗零推进（`logic_frames==0` 或 `df==0`）** | **满足**。10 行写「有」并给逐窗 `logic_frames`/`df`；第 11 行写「无」并给 w0/w1/w2 读数与「无 w3+」。每行注明「仅停摆序列，不证明本窗停顿原因」。 | §1 列④、§3 检查 F |
| **列 5 是否有可确认的终局关联证据** | **满足**。8 行写「有（终局关联旁证，级别受限）」并给出后续窗截图文件名、mtime、对**其自身窗尾**的 Δ（全部 +0.076847~+0.138980 s）、`capture_ok=true`、材料记载的计分屏判读及「仅采图时刻」限定；3 行（T32、T47、q/w2）写「无／未知」。T33/w2 无面板、T38/w1 残留件明确排除出正面证据。 | §1 列⑤、§0.4、§3 检查 D/E、§2.1 |
| **列 6 未知项：查不到的一律写「未知」** | **满足**。11/11 有「未知」段，逐行列明未知内容（本窗停顿运行期原因、本窗内战术阶段、阶段转换时点、声明与盘面不一致的原因等），并**注明查阅了哪些文件仍是缺**；未从其他窗/其他趟/推理填值。 | §1 列⑥、§0.4、§3 检查 G |
| **H5 绝不把「后续窗零推进」当成「本窗停顿的原因」** | **满足**。④列与⑤列分列且各自限定；`RULING.md:113-117,120` 的措辞在 §0.5 H5、§1 表头、§2.1、本节反复固定。 | §0.5 H5、§1 表头及各行④⑤、§2.1、`RULING.md:113-120` |

**`gaps` 原文引文**（`EX3_STALL_EVIDENCE.md:257`、`:279-284`）：另 §1 主表 11/11 行的⑥列均含「未知」段（`EX3_STALL_EVIDENCE.md:99-109`），逐行列明查阅过哪些文件仍是缺；该 11 行已在本件第 4 段全文照录，不在此重复摘录。

> **检查 G：未运行／未验证的项**（如实登记）：本轮未做 PNG 目视或 OCR；未重算 104 份全库统计、21/32 图像覆盖、旧 1734 段/87.7%、ρ/φ、argv/BOOT 归属、异常件普查、12 份镜像逐字节比对；未做运行期实验、E3 或项目测试；未启动/读取活进程。表中所有「计分屏／无面板／完整终局比分」均为**材料记载**，证据等级按 `RULING.md:197` 的「他方原件核验，本裁决未重做」处理。
>
> ## 5. 与裁决其他部分的关系（不越界）
>
> - 本表是 **EX-3 单项交付**，写到题定 `EX3_STALL_EVIDENCE.md`；未改 `RULING.md`、`FACTBASE.md`、`RECHECK.md`、`D15_IMPLEMENTATION_CANDIDATE.md`（未创建）、`D13_MECHANISM_GAP_AND_OFFLINE_CARD.md`（未创建）、台账、`PENDING_DECISIONS.md`、任何真机 json/png 或三路核验件。
> - 22 窗核心集、25 对照、47 窗混杂控制字段属 EX-1／EX-4，本表不重复也不代填；33/38 的完整分母解释见 `EX1_DATAFACE.md` 与 `RULING.md:81-89`。
> - 「追加勘误、历史原文不改」属 EX-2；D-13「当前 E3→① 不执行、0/22 阈值覆盖」属 EX-4。本表不涉及其结论，也不写任何采样代码。
> - `RULING.md:122`：完成 EX-3 时**允许明确未知**，不要求补真机，也不以未知阻塞结案。本表的 11 个「未知」按此处置。

### 5.5 冲突清单（原样保留，不调和）

| 编号 | 冲突性质 | 冲突双方（碎片:行） | 标注落点 |
|---|---|---|---|
| C1 / C3 | 同一批停顿 `max_stall_s` 的不同数值表述（`9.574864` / `9.575s` / `9.574`；`24.077365` / `24.077s`；`24.734761` / `24.734760`；另有 `24.999s`、`24.998s`） | `EX1_DATAFACE.md:152,154,156,330`、`EX3_STALL_EVIDENCE.md:99,101,103` ↔ `EX2_ERRATA.md:88` | 第 2 段 §3.3 表后；第 3 段 §545.3 后 |
| C2 / C6 | 零推进／不可算窗计数口径不同（29 / 32 / 35 / 41；41 的两种分解 5+1+35 与 31+10） | `EX1_DATAFACE.md:313`、`EX3_STALL_EVIDENCE.md:56,140` ↔ `EX2_ERRATA.md:79,88,94` | 第 2 段 §5 分因计数后；第 4 段 §0.1 后 |
| C4 / C5 | ★ 结论冲突：「旧读数不得再引用」「不得作精确读数」vs「作为材料记载转述」；比分 `126/146`、`201034/126800` ↔ `126/206/0/201034`、`198/731/4/126800`；屏显 `00:00:10` ↔ `00:00:32` | `EX2_ERRATA.md:111,112` ↔ `EX3_STALL_EVIDENCE.md:103,108` | 第 3 段 §545.6 后；第 4 段 §1 主表后 |

> C1/C3、C2/C6、C4/C5 是同一组差异／冲突在两份碎片各自冲突处的成对标注；本件**不合并、不换算、不删除、不判定孰是孰非**，各碎片原文一律未改。

### 5.6 本轮组装员实际执行的检查（命令与输出）与未复核项

1. `ls -la ".../ADJUDICATE_a70d00e5/"` 与 `ls -la ".../ADJUDICATE_a70d00e5/impl_f4bcf30c/"` → 目标件 `D15_IMPLEMENTATION_CANDIDATE.md` **不存在**；三份碎片存在（EX1 62449 B / EX2 23826 B / EX3 42584 B）；同目录另有 `RULING.md`、`RECHECK.md`、`FACTBASE.md`、`D13_MECHANISM_GAP_AND_OFFLINE_CARD.md`（本轮全部只读，未改）。
2. `grep -n -m 40 -E "GPT|6\.1|裁决|独立|复查|D-15" RULING.md | head -40` → 命中 `RULING.md:1`、`:5`、`:13`、`:69`、`:95`、`:109`、`:162`、`:166`、`:167`、`:170`、`:178`、`:204` 等；`grep -n -m 30 -E "独立|复查|GPT|6\.1|结论|判定" RECHECK.md | head -30` → 命中 `RECHECK.md:1`、`:34`、`:82`。
3. `grep -n -E "6\.1|GPT|gpt" RULING.md RECHECK.md` → **`(no hits)`**（两份原件均未出现「GPT 6.1」字样）。
4. `wc -l impl_f4bcf30c/EX1_DATAFACE.md impl_f4bcf30c/EX2_ERRATA.md impl_f4bcf30c/EX3_STALL_EVIDENCE.md` → `347 / 146 / 284，total 777`。
5. `python -I -X utf8 -c`（读三份碎片字节，判 BOM / CRLF / LF / 末尾换行）→ `EX1_DATAFACE.md bytes=62449 CRLF=347 LF=347`（CRLF），`EX2_ERRATA.md bytes=23826 CRLF=0 LF=146`，`EX3_STALL_EVIDENCE.md bytes=42584 CRLF=0 LF=284`；三份均无 BOM、均以换行结尾。本件照录时保留各自原行尾。
6. `grep -n -E "146|171|126/206|126/146|00:00:32|00:00:10|4410|269628|24\.734|9\.574|21/32|29 窗|32 窗" EX1_DATAFACE.md EX2_ERRATA.md EX3_STALL_EVIDENCE.md` → 命中 `EX2_ERRATA.md:79,88,94,111,112` 与 `EX3_STALL_EVIDENCE.md:103,108`、`EX1_DATAFACE.md:152,154,156,328,330`，据此定位 C1/C2/C4 的差异行。
7. `python -I -X utf8 -c`（只读打印 `GOAL_THREE_TARGETS_20261018.md:4254-4263`、`:4415-4419`、`S543_FREEZE_WAS_SCORESCREEN_20261104.md:81-94`、`ADJUDICATE_a70d00e5/RULING.md:100-107`）→ 旧比分 `126/146/0/201034`、`198/171/4/126800` 与订正 `126/206/0/201034`、`198/731/4/126800` 并存；`RULING.md:105` 明写已撤回支柱不得作依据。
8. `python -I -X utf8 - <<'PY'`（只读 heredoc，打印三份碎片中冲突行的完整原文）→ 确认 `EX1_DATAFACE.md:152,313,328`、`EX2_ERRATA.md:79,88,94,111,112`、`EX3_STALL_EVIDENCE.md:56,99,103,108` 的逐字内容；后续 `python -I -X utf8 - <<'PY'`（只读打印 `EX2_ERRATA.md:111` 与 `EX3_STALL_EVIDENCE.md:108` 的比分句）→ 确认两处冲突文本。
9. `python -I -X utf8 -c`（打印 `RULING.md:162-170` 并定位 6 个插入锚点）→ EX-1 `:166` / EX-2 `:167` / EX-3 `:168` 三段结构与本件路径一致；锚点均为唯一命中。
10. 组装与复核脚本（均置于写域 `.../impl_f4bcf30c/`，运行后删除）：`python -I -X utf8 ".../impl_f4bcf30c/_assemble_d15.py"` → `VERBATIM_CHECKS [True, True, True]`、`NOTES [C1..C6]`、`DOC_HAS_S5 True`；`python -I -X utf8 ".../impl_f4bcf30c/_verify_d15.py"` → 复核 6 个标注块、三段全文各出现 1 次且顺序正确、第 5 节各小节与三份 `acceptance` 表／`gaps` 引文标记齐全、`ALL CHECKS PASSED`（完整输出见交付结果 acceptance）。

**未复核／未做的项（如实登记）**：

- 抬头中「`RULING.md`（GPT 6.1 裁决）」按任务指定措辞写入；本轮 `grep -n -E "6\.1|GPT|gpt" RULING.md RECHECK.md` 返回 `(no hits)`，故该署名**无法从这两份原件复核**，本件不补证、不改写。
- 未重跑任何碎片自报的检查：EX-1 的 `ex1_rebuild.py`／`ex1_checks.txt`、EX-2 的检查 A/B/C、EX-3 的检查 A–F 均**未在本轮重跑**；本轮只做拼接、只读比对与冲突定位。三份碎片中的验收表与「满足／是」结论按原文照录，不冒充组装员重新验收通过。
- 未新读／OCR 任何 PNG，未核截图时序或哈希，未做真机发射、运行期实验或项目测试；未启动/读取活进程内存。
- 未改台账、`PENDING_DECISIONS.md`、`RULING.md`、`FACTBASE.md`、`RECHECK.md`、三路核验件、真机 json/png 或三份碎片；未 commit。
- 本件不含任何采样/注入/运行期探针代码；组装与复核以 `python -I -X utf8` 运行两个临时文档脚本完成，二者在写域内运行后即删除，未保留在交付目录中。
