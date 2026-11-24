# M67 MERGE_LOG

## 任务与独占写权
按卡片 `M67-MERGE.md`，本轮唯一 COVERAGE 写者；仅改 `COVERAGE/coverage.tsv` 与
`COVERAGE/PANEL.md`，不改 `R14_COMMON.md` / `STATUS_BOARD.md` / 台账 /
`NAMED_PUSH_*` / `NAMED_PUSH_AUDIT*` / `RESCAN_MOVED`；未 git commit。两文件改前/改后
mtime、字节、SHA-256 见 `BEFORE_AFTER.txt`（改前备份 `coverage.tsv.bak` / `PANEL.md.bak`
在本目录）。

## 并表输入与交集核验（先核后并，不符即停）
审计表 `NAMED_PUSH_AUDIT7/verdict.tsv`：13 行、8 列、第 3 列 `verdict` 全 PASS，无 FAIL。
delta：`NAMED_PUSH_S20_B2/delta.tsv`（8 行）+ `NAMED_PUSH_S06_B3/delta.tsv`（5 行）。

| 组 | 审计 PASS | delta | 交集（应并行数） | 要求 | PASS∖delta | delta∖PASS |
|---|---|---|---:|---:|---:|---:|
| S20 | AUDIT7 verdict PASS ∩ subsystem S20（8） | S20_B2/delta（8） | **8** | 8 | 0 | 0 |
| S06 | AUDIT7 verdict PASS ∩ subsystem S06（5） | S06_B3/delta（5） | **5** | 5 | 0 | 0 |

交集正好 13（S20 8 + S06 5），双向差集均 0，无"PASS 在 delta 找不到"或"delta 不在
PASS 集合"的异常，故未停下。13 行 entry 逐行归一为大写 8 位后全部命中 atlas
（atlas 内 13，atlas 外 0），无"A 口径不计"。13 行在 coverage 中各命中唯一一行，
改前 grade 全 `[静态推断]`。

未并 `NAMED_PUSH_S12_B1` 4 行：其审计代理失败（未产出）、尚未过审，留池。

前置复核（改前实测，卡片"Lead 已核过"全部吻合）：数据行 18,498；全表 `[已证]` 1,556；
atlas 内 1,550；atlas 外 6；S20 proved 53、S06 130。

## coverage.tsv 改动（13 行 × 3 列）
对 13 行逐行改：
- 第 4 列 `one_line_semantics` ← 对应 delta 第 4 列**原文照抄**；
  **`0062FE90` 的表址按审计勘误改字：`007E9D84` → `007E9D64`、`0x7E9D84` → `0x7E9D64`**
  （死表 007E9D84 系析构器 0062E244 teardown 写；活表 007E9D64 系 ctor 0062DC50 于
  0062DC95 装入，Find 004EA010）。
- 第 5 列 `grade` → `[已证]`；
- 第 6 列 `evidence_path` → `NAMED_PUSH_AUDIT7/VERDICT.md`。

第 1/2/3/7/8 列不动。行数 18,498、8 列、TAB 分隔、LF 换行、无 BOM 均不变。
改后逐行 diff：仅第 4/5/6 列变化，immutable 列逐字节不变，grade 全 `[已证]`。

S20 八行 entry：0062D9A0、0062FE90、00630090、00644960、006457A0、00645950、
00749F30、0074BA30。
S06 五行 entry：0071E1D0、007220A0、007220D0、007281A0、00763D90。

## 两条审计勘误落实
1. **0062FE90 表址**：delta 第 4 列原文含 `007E9D84`×1、`0x7E9D84`×1；落盘 coverage
   第 4 列改为 `007E9D64`/`0x7E9D64`，原死表串 0 残留。PANEL 备注列记
   "0062FE90 表址按审计勘误改为 007E9D64"、"M67 按审计勘误改表址"。
2. **S06 五行 ④**：delta 第 4 列本无 ④，按卡片"照抄、不改执行器原文"处理——coverage
   五行语义栏与 delta 原文逐字节相等、均无 ④（未注入 ④）；④ 由 a-S20S06 审计补证，
   PANEL 备注列记 "M67 备注：S06 五行 ④ 由 a-S20S06 审计补证，见
   NAMED_PUSH_AUDIT7\VERDICT.md"。

## PANEL.md 同步
- 标题行（第 1 行）前插 M67 摘要。
- 三分母行 `全表 [已证] / atlas 内 [已证]`：1,556 / 1,550 → **1,569 / 1,563**，
  说明列前插 M67 备注；atlas 外仍 6。
- 覆盖面板主表：S06 proved 130→135（15.35%→15.94%）、S20 53→61（12.93%→14.88%）、
  TOTAL 1,550→1,563（12.00%→12.10%），三行备注列前插卡片指定 M67 文案；named 各列不动。
- 严格口径双列表：S06 135/120（15.94%/14.17%）、S20 61/49（14.88%/11.95%）、
  TOTAL 1,563/1,246（12.10%/9.65%），名义/严格判定列保持 3/22 与 1/22。
- 严格口径双列表节追加"M67 并表实算说明"（承 M66 段之后），写明 strict 用
  `strict_panel.py` 第 78 行 `if "[未证]" not in sem:` 的带方括号字面口径；达标判定未翻转。
- 第 98 行 SHA 绑定注记未改：卡片未要求，且该注记在改前就已停留在 M52 旧 SHA，本卡不扩大范围。

## 复算与达标
- 权威 `strict_panel.py`（仅重定向输出目录到 `MERGE_M67/_strict_out`）改后实算：
  S20 61/49、S06 135/120、TOTAL 1563/1246；与独立复核脚本 `_postcheck.py` 一致。
- 名义达标：改前/改后均 S15/S16/S17（3/22）；严格达标：改前/改后均 S17（1/22）。
  **无达标翻转**，符合卡片要求。
- 全部数字与口径见 `VERIFY.txt`。

## 工作脚本与产物（均在 MERGE_M67 内）
`_analyze.py`（交集/前置/勘误点核验）、`_apply.py`（落盘 13 行）、`_postcheck.py`
（改后逐行 diff + 全量计数 + DoD 判定）、`_strict_panel_run.py` + `_strict_out/`
（权威脚本重定向副本与输出）、`_panel_edit.py`（PANEL 同步）、`_panel_verify.py`
（PANEL 核验）、`coverage.tsv.bak`、`PANEL.md.bak`、`BEFORE_AFTER.txt`、`VERIFY.txt`、
`MERGE_LOG.md`。
