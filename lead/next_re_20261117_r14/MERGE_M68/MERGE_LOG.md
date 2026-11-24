# M68 MERGE_LOG

## 任务与独占写权
按卡片 `M68-MERGE.md`，本轮唯一 COVERAGE 写者；仅改 `COVERAGE/coverage.tsv` 与
`COVERAGE/PANEL.md`，不改 `R14_COMMON.md` / `STATUS_BOARD.md` / 台账 /
`NAMED_PUSH_*` / `NAMED_PUSH_AUDIT*` / `RESCAN_MOVED`；未 git commit。两文件改前/改后
mtime、字节、SHA-256 见 `BEFORE_AFTER.txt`（改前备份 `coverage.tsv.bak` / `PANEL.md.bak`
在本目录）。BEFORE 两文件 sha256 与本轮开场实测一致，且与 MERGE_M67 的 AFTER 值逐字节吻合。

## 并表输入与交集核验（先核后并，不符即停）
审计表 `NAMED_PUSH_AUDIT8/verdict.tsv`：4 行、8 列、第 3 列 `verdict` 全 PASS，无 FAIL。
delta：`NAMED_PUSH_S12_B1/delta.tsv`（4 行、6 列）。

| 组 | 审计 PASS | delta | 交集（应并行数） | 要求 | PASS∖delta | delta∖PASS |
|---|---|---|---:|---:|---:|---:|
| S12 | AUDIT8 verdict PASS（4） | S12_B1/delta（4） | **4** | 4 | 0 | 0 |

再与卡面 entry 及 coverage 现盘 entry 相交，仍为同样 4 行（双向差集均 0），
交集正好 4 行，符合卡片"交集必须正好 4 行；不是就停下报告"的要求，故未停下。
4 行 entry：00442230、00447210、00447F10、0044E8F0；在 coverage 中各命中唯一一行，
改前 grade 全 `[静态推断]`。

atlas 归属（entry 归一为大写 8 位后核 `function_atlas.tsv`）：4 行全在 atlas 内
（00447F10/0044E8F0 在 atlas 原文为小写 `00447f10`/`0044e8f0`，须归一后命中），
atlas 外 0，无"A 口径不计"行。

前置复核（改前实测，卡片"Lead 已核过"全部吻合）：数据行 18,498；全表 `[已证]` 1,569；
atlas 内 1,563；atlas 外 6；S12 proved 55。

## coverage.tsv 改动（4 行 × 3 列）
对 4 行逐行改：
- 第 4 列 `one_line_semantics` ← 对应 delta 第 4 列**原文照抄**（4/4 逐字节相等）；
- 第 5 列 `grade` `[静态推断]` → `[已证]`；
- 第 6 列 `evidence_path` → `NAMED_PUSH_AUDIT8/VERDICT.md`。

第 1/2/3/7/8 列不动。行数 18,498、8 列、TAB 分隔、LF、无 BOM、无尾随换行均不变。
改后逐行 diff：仅第 4/5/6 列变化，immutable 列逐字节不变，4 行新语义均不含字面 `[未证]`。

逐行落点（coverage.tsv 行号）：00442230 L1159、00447210 L1174、00447F10 L1181、
0044E8F0 L1210。

## PANEL.md 同步
- 标题行（第 1 行）前插 M68 摘要。
- 三分母行 `全表 [已证] / atlas 内 [已证]`：`1,569 / 1,563` → **`1,573 / 1,567`**，
  说明列前插卡片指定 M68 备注；atlas 外仍 6。
- 覆盖面板主表：S12 proved 55→59（19.71%→21.15%）、TOTAL 1,563→1,567（12.10%→12.13%），
  两行备注列前插卡片指定 M68 文案；named 各列不动。
- 严格口径双列表：S12 55/40→59/44（proved_pct 21.15%、strict_pct 15.77%）、
  TOTAL 1,563/1,246→1,567/1,250（proved_pct 12.13%、strict_pct 9.68%），
  名义/严格判定列保持 3/22 与 1/22。
- 严格口径双列表节追加"M68 并表实算说明"（承 M67 段之后），写明 strict 用
  `strict_panel.py` 第 78 行 `if "[未证]" not in sem:` 的带方括号字面口径；达标判定未翻转。
  M68 文案含"00447210 与 00447F10 的 ③ 站点为「返回值搬入 ebx/ebp 再判」，审计独立枚举
  被调全部 ret 确认为多值状态码 {0,4,5,7,8,0x1A,0x37} 与 {0,1,3,5,6,8,9}，非 {0,1} 布尔"。

## 复算与达标
- 权威 `strict_panel.py`（仅重定向输出目录到 `MERGE_M68/_strict_out`）改后实算：
  S12 59/44、TOTAL 1567/1250；与独立复核脚本 `_postcheck.py` 一致。
- 名义达标：改前/改后均 S15/S16/S17（3/22）；严格达标：改前/改后均 S17（1/22）。
  **无达标翻转**，符合卡片要求。
- 全部数字与口径见 `VERIFY.txt`。

## 工作脚本与产物（均在 MERGE_M68 内）
`_preflight.py`（交集/前置/atlas 归属/模拟改后统计）、`_apply.py`（落盘 4 行）、
`_postcheck.py`（改后逐行 diff + 全量计数 + DoD 判定）、`_strict_panel_run.py` +
`_strict_out/`（权威脚本重定向副本与输出）、`_panel_edit.py`（PANEL 同步）、
`coverage.tsv.bak`、`PANEL.md.bak`、`_state.json`、`BEFORE_AFTER.txt`、`VERIFY.txt`、
`MERGE_LOG.md`。
