# R17-PANEL-M103 :: REPORT

角色：合并员 / `PANEL.md` 唯一写者（`work/cn:hy4flash-free`）。日期：2026-11-21（R17 第 1 轮）。
卡面：`_cards/R17-PANEL-M103.md`。本卡动作 = 两处纯插入（insert only），未 replace 整行、未删除任何既有字节。

## 0. 绝对边界遵守情况

- 只改 `COVERAGE/PANEL.md`；未改 `coverage.tsv`、`R14_COMMON.md`、台账、看板、`LEAD_LOCK`、`PENDING_DECISIONS.md`、`_cards\`。
- L1 按倒序前插链规则，在 `# PANEL — R14 coverage` 的 `coverage` 之后插入 M103 备注；**未整行 replace**。
- 正文块插在 M102 块最后一行之后、`📌 M77 并表实算说明` 行之前（锚点唯一定位，实测行号 = 332）。
- 未读 `EVIDENCE\` 原始输出、未跑反汇编；文件行尾实测 bare LF（CR = 0），写盘后仍为 0。

## 1. 改前 / 改后指标

| 项 | 改前（`PANEL.before.md` = 开卡时 `COVERAGE/PANEL.md`） | 改后（现 `COVERAGE/PANEL.md`） |
|---|---|---|
| 路径 | `lead/next_re_20261117_r14/COVERAGE/PANEL.md` | 同左 |
| mtime | `2026-11-21 11:20:05.105192400 +0800` | `2026-11-21 13:18:00.197576+08:00` |
| 字节 | `205,207` | `207,702`（`+2,495`） |
| sha256 | `9a0be87e9bdde277e08b7145989bca132c6b253cd193034c205ea79dd848c1c9`（前 12：`9a0be87e9bdd`） | `628e0e9e1e2c378c7c41a831c9823094524cfbd2c7eeb7ff8895c060532b5d9e`（前 12：`628e0e9e1e2c`） |
| 换行数（`\n`） | `717` | `732` |
| CR 计数 | `0` | `0` |
| 末尾 LF | `True` | `True` |

行数增量 = `15` = 插入正文块行数 `15`（L1 备注为行内插入，不增行）。

## 2. 断言 a–e 实测值

| 断言 | 结果 | 实测值 |
|---|---|---|
| a | PASS | line delta 15 == inserted body lines 15 |
| b | PASS | L1 M-set sizes: before=53 / after=54; superset(before∪{103})=True |
| c | PASS | different lines: 1 (L1) + 0 (others); L1 changed=True, prefix_same=True, tail_same=True |
| d | PASS | §12.6 count 20 -> 20 |
| e | PASS | M103 occurrences 0 -> 2 (>= 2 required) |
| cr | PASS | CR count after = 0 (must be 0) |
| revert | PASS | rebuild-without-insertions == before: True (9a0be87e9bdd == 9a0be87e9bdd) |
| tokens | PASS | L1 required tokens present; missing=[] |

- a) 行数增量 == 插入内容行数：**PASS**。
- b) L1 M 号集合 ⊇ 改前集合 ∪ {103}：**PASS**（集合大小 改前 `53` / 改后 `54`；改前集合 = [9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 23, 24, 25, 26, 28, 29, 30, 31, 32, 34, 37, 39, 40, 41, 43, 44, 45, 46, 47, 48, 50, 51, 52, 53, 55, 56, 60, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78]）。
- c) 除 L1 与插入点外其余各行逐字节相同：**PASS**（不同行数 = 1（L1）+ 0）。
- d) `§12.6` 出现次数不变：**PASS**（`20` → `20`；本卡不碰第 4 列，PANEL 内计数仅如实报告）。
- e) 全文 `M103` 出现次数 ≥ 2：**PASS**（`2`）。
- 附加：CR 计数写盘后仍为 0：**PASS**；去掉两处插入可逐字节还原改前：**PASS**；L1 五个必需 token 齐备：**PASS**。

## 3. 插入内容定位

- L1：在 `# PANEL — R14 coverage` 之后前插 `M103 §2.6 两处表述更正成文 §2.7（…D-53…）；`，位于原首条备注 `M77 并表` 之前。
- 正文：M103 披露块 `15` 行，插在 M102 块末行（原第 331 行）之后、`📌 M77 并表实算说明`（原第 332 行）之前。

## 4. coverage.tsv 未变证明

- 开卡时：`4,147,334 B / sha256 c2ee063fd4f61f784585ef2abcc4ff563fa09ec1b1f7f5079643076e359c744a`
- 写盘后复查：`4,147,334 B / sha256 c2ee063fd4f61f784585ef2abcc4ff563fa09ec1b1f7f5079643076e359c744a`
- 结论：一致（True），本卡未碰 `coverage.tsv`，亦未被并发改写。

## 5. 复跑

`python insert.py`：从 `PANEL.before.md` 重建，断言全 PASS 后一次性写盘并读回复验。
