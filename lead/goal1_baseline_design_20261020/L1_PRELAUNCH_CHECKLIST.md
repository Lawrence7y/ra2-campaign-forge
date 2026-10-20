# L1 基线趟 · 发射前预检实测值（§7 清单）

**日期**：2026-10-20 13:1x  **性质**：离线预检，未启动游戏。
**变体**：`out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020\`（新建，不改共享变体）
**裁决依据**：Notion U1–U9（台账 §300）；方案 `BASELINE_MEASURE_DESIGN.md`。

## A. 离线预检

| # | 检查 | 期望 | 实测值 | 判定 |
|:--|:--|:--|:--|:--|
| A1 | 母本二进制 | `73201cc0…f67476` / 4,825,360 B | `73201cc021497c95…` / 4,825,360 B | ✅ |
| A2 | 图哈希 | `0add791d…60bc` / 311,822 B | `0add791d11aea84d…60bc` / 311,822 B | ✅ |
| A3 | 图内 owner 分布 | `[Units]` 3360（h0/Computer 各 240）/ `[Infantry]` 2240（各 160） | `[Units]`=3360：`<human player>`/`Computer`/`Neutral`/`Special` 及其余 10 户 **各 240**；`[Infantry]`=2240：**各 160** | ✅ |
| A4 | 无 Structures 节 | 27 节，无 `Structures` | **27 节**，无 `Structures`、无 `Aircraft` | ✅ |
| A5 | INI 设置 | `ShortGame=no` / `GameSpeed=2` / `ScenIndex` 存在 | `:25 ShortGame=no`、`:22 GameSpeed=2`、`:20 ScenIndex=166`、`:21 Scenario=[2]0LoadBench_U0400.yrm` | ✅ |
| A6 | 呈现层常量 | `ddraw.ini=95949842…` / `ddraw.dll=85e0f7d5…` / `ra2render.dll=39cbd665…`（在位不加载） | `95949842fe6c0b25` / `85e0f7d530dfda13` / `39cbd66550141610`（+ `ra2render.ini=27c9a60c`） | ✅ |
| A7 | `windowed=false` | 第 1 行 `windowed=false`；第 21 行 `\x01false`（已知缺陷不改） | 第 1 行 `windowed=false` | ✅（缺陷登记 U9） |
| A8 | 残留进程 | 0 行 | 0 | ✅ |
| A9 | 载体目录干净 | 空/无旧 `c_*` | `qc161_u0400_trip/ct` = 0 项 | ✅ |
| A10 | 磁盘余量 | ≥5 GB | D: 410 GB 可用 | ✅ |
| A11 | 锚哈希 | `517889c6…` | `517889c68f037ab6…5ba636` | ✅ |
| A12 | `--carrier-create-files` 字符串已落回执 | 含空格项整体引号、字符串已抄进回执 | 见下「载体串」；**89 件（84 t31 + 5 自动）**，含 `RA2MD Update.ico` | ⚠️ 需核对件数 |

### A12 载体串（L1 用，89 件目标）

T55k 实收为 **88 件**（5 默认 + 83 附加），本变体即按该 88 件复制。**Notion U7 要求 L1 按 89 件（含 `RA2MD Update.ico`）**——该文件在源目录存在但未进 T55k。发射前需决定：按 88 件（与 T55k 一致）或按 89 件（Notion 口径）。此项**未决，属 A12 阻塞**。

## B. 命令装配（草案，待 A12 定后填 trip-id/out-dir）

| # | 检查 | 值 |
|:--|:--|:--|
| 装1 | `--target-map` | `<变体>\XMP29U2.MAP`（**不是任何 .yrm**）✅ |
| 装2 | `--target-sha256` | `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` ✅ |
| 装3 | `--trip-id` | `QC161-U0800-L1` |
| 装4 | `--out-dir` | `lead\qc161_u0400_trip\l1_u0800_20261020`（后代）✅ |
| 装5 | 含 `--measure 1 --fullscreen --evid-diff` | 是 |
| 装6 | 不含 `--frozen-dump` | 是 |
| 装7 | `--probe-frames` ≥6 点、均 > 起始帧一半 | `3900,4200,4500,4800,5100,5400,5700,6000` |
| 装8 | 同刻只有一个真机趟 | 是（当前无在飞真机） |

## C. 趟中/趟后核对（照方案 §7-C，按 U3 裁决修正）

C7 依 Notion U3 **降为只记录**（写回 INI 不可信，判不了 GameSpeed 是否读 INI）；真正判别=L2 或读 `[0xA8B558]`（新开项）。V10 口径相应调整。

## 阻塞项

1. **A12 件数**：88 vs 89（`RA2MD Update.ico` 含否）——需用户/Lead 一句话定。
2. **A6 注记**：`ra2render.dll` 在载体中**在位但不加载**（S-4 零命中为硬门），这是 Arm A 的定义，不是缺陷。
3. 其余 A1–A11、装1–装8 全部实测通过。
