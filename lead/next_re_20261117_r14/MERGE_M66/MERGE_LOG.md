# M66 MERGE_LOG

## 任务与独占写权
按卡片 `M66-MERGE.md`，本轮唯一 COVERAGE 写者；仅改 `COVERAGE/coverage.tsv` 与
`COVERAGE/PANEL.md`，不改 `R14_COMMON.md` / `STATUS_BOARD.md` / 台账 /
`NAMED_PUSH_*` / `NAMED_PUSH_AUDIT*`；未 git commit。两文件改前/改后 mtime、字节、
SHA-256 见 `BEFORE_AFTER.txt`（改前备份 `coverage.tsv.bak` / `PANEL.md.bak` 在本目录）。

## 并表输入与交集核验（先核后并）
| 组 | 审计表 PASS | delta | 交集（应并行数） | 要求 | PASS∖delta | delta∖PASS |
|---|---|---|---:|---:|---:|---:|
| A | NAMED_PUSH_AUDIT6 verdict（S22，18 PASS） | NAMED_PUSH_S22_B2/delta（18） | **18** | 18 | 0 | 0 |
| B/S06 | NAMED_PUSH_AUDIT5 verdict PASS 且 subsystem=S06（4） | NAMED_PUSH_S06_B1/delta（4） | **4** | 4 | 0 | 0 |
| B/S20 | NAMED_PUSH_AUDIT5 verdict PASS 且 subsystem=S20（7） | NAMED_PUSH_S20_B1/delta（7） | **7** | 7 | 0 | 0 |

三组恰好 18/4/7，双向差集均 0，无"PASS 在 delta 找不到"或"delta 不在 PASS 集合"
的异常，故未停下。29 行 entry 逐行归一为大写 8 位后全部命中 atlas（atlas 内 29，
atlas 外 0），无需"A 口径不计"。29 行在 coverage 中各命中唯一一行，改前 grade：
A 组 18 行 `[未证]`、B 组 11 行 `[静态推断]`，无一行已是 `[已证]`。

## coverage.tsv 改动（29 行 × 3 列）
对 29 行逐行改：
- 第 4 列 `one_line_semantics` ← 对应 delta 第 4 列原文照抄；
- 第 5 列 `grade` → `[已证]`；
- 第 6 列 `evidence_path` → A 组 `NAMED_PUSH_AUDIT6/VERDICT.md`、
  B 组 `NAMED_PUSH_AUDIT5/VERDICT.md`。
第 1/2/3/7/8 列不动。行数 18,498、8 列、TAB 分隔、LF 换行均不变。
改后逐行 diff 核对：仅第 4/5/6 列变化、grade 全 `[已证]`、语义与 evidence_path 正确。

A/S22 18 行 entry：006C1010、006C1190、006C1310、006C1490、006C1610、006C1790、
006C1910、006C1A90、006C1C10、006C1D90、006C1F10、006C2090、006C2210、006C2390、
006C2510、006C2690、006C2810、006C2990（TClassFactory 同族工厂 slot3）。
B/S06 4 行 entry：004839F0、00483C10、005F92D0、005FC570。
B/S20 7 行 entry：00423AC0、00428EA0、004A7C90、004C5A30、004C5AC0、005F44A0、0062D7A0。

## PANEL.md 同步
- 三分母行：`全表 [已证] / atlas 内 [已证]` 1,527 / 1,521 → **1,556 / 1,550**，
  备注列前插 M66 说明；atlas 外仍 6。
- 覆盖面板主表：S06 proved 126→130（14.88%→15.35%）、S20 46→53（11.22%→12.93%）、
  S22 69→87（1.42%→1.79%）、TOTAL 1,521→1,550（11.78%→12.00%），
  四行备注列前插卡片指定 M66 文案；named 三列不动。
- 严格口径双列表：S06 130/115（13.58%）、S20 53/41（10.00%）、S22 87/44（0.91%）、
  TOTAL 1,550/1,233（9.55%/12.00%），名义/严格判定列保持 3/22 与 1/22。
- 严格口径双列表节追加"M66 并表实算说明"（承 M65 段之后），写明 strict 用
  `strict_panel.py` 第 78 行 `if "[未证]" not in sem:` 的带方括号字面口径。
- 标题行（第 1 行）前插 M66 摘要。
- 第 98 行 SHA 绑定注记未改：卡片未要求，且该注记在改前就已停留在 M52 旧 SHA，本卡不扩大范围。

## 复算与达标
- 权威 `strict_panel.py`（仅重定向输出目录到 `_strict_out`）改后实算：S22 87/44、
  S06 130/115、S20 53/41、TOTAL 1550/1233；与独立复核脚本 `_postcheck.py` 一致。
- 名义达标：改前/改后均 S15/S16/S17；严格达标：改前/改后均 S17（1/22）。
  **无达标翻转**，符合卡片要求。
- 全部数字与口径见 `VERIFY.txt`。

## 工作脚本与产物（均在 MERGE_M66 内）
`_analyze.py`（交集）、`_verify.py`（改前/模拟改后）、`_apply.py`（落盘）、
`_postcheck.py`（改后复核）、`_mkstrict.py` + `_strict_panel_run.py`（权威脚本重定向副本）、
`_strict_out/`、`_panel_edit.py`、`_fix_title.py`、`_panel_verify.py`、`_panel_verify.txt`、
`coverage.tsv.bak`、`PANEL.md.bak`、`BEFORE_AFTER.txt`、`VERIFY.txt`、`MERGE_LOG.md`。
