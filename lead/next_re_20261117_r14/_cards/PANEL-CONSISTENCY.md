# PANEL-CONSISTENCY — PANEL.md 全量数值一致性普查

## 为什么做

本轮已发现 `PANEL.md` 的「严格双列」表里 **S02 / S09 / S13 / S19 / S22 / TOTAL 六处是旧截面**（分别落后 1 / 8 / 11 / 7 / 10 / 33 行），是**碰巧**发现的。同类问题极可能还有，必须系统扫一遍，不靠运气。

## 输入

- `lead\next_re_20261117_r14\COVERAGE\PANEL.md`（只读）
- `lead\next_re_20261117_r14\COVERAGE\coverage.tsv`（只读；18,498 数据行、8 列、行内制表符）
- `lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv`（只读；12,916 行；**`entry` 列为小写十六进制，比对必须大小写归一**）

## 重算口径（严格照此，别自创）

- `n` = 该 subsystem 且 entry 在 atlas 内的行数
- `proved` = 上述行中 grade `== [已证]`
- `named_L` = 上述行中 name 非空且不以 `sub_` 开头
- `named_S(R14)` = `named_L` 再排除匹配 `::sub_[0-9A-Fa-f]+$` 的
- `named_strict` = `named_S(R14)` 再排除含 `::slotN` / `::vslotN` 的
- `proved_strict` = `proved` 中语义串**不含** `未证` 的
- 门槛：`ceil(0.9n)`、`ceil(0.5n)`

## 要做什么

1. **枚举**：把 `PANEL.md` 里**所有**含数值的表逐行提取出来——不只知道有一张严格双列表，把每张表、每个子系统行、每个 TOTAL/合计行都列上（给行号）。
2. **逐格重算**：对每一个能由 `coverage.tsv` + atlas 推出的格子，算出真值并与面板值比对。
3. **分类不符**：每一处不符归入下列之一，并说明依据：
   - `旧截面`（落后于某次并表，能指出是哪一次）
   - `口径错`（算法与上面口径定义不同，例如拿 raw 计数当 atlas 内、或没归一大小写）
   - `算错`（同一口径下算错了）
   - `无法判定`（面板该格的定义无法从上下文确定，写明你缺什么）
4. **影响面**：逐处回答"这一处错了会不会改变任何子系统的达标判定或对外头条数字"。**明确列出所有会翻转的格子**（若有）。
5. **头条核对**：独立算出当前
   - 名义达标（`named_S(R14) >= ceil(0.9n)` 且 `proved >= ceil(0.5n)`）有几个、是哪几个
   - 严格达标（再加 `proved_strict >= ceil(0.5n)`）有几个、是哪几个
   与面板 TOTAL 行现记的 `3/22`、`1/22` 对比。

## 输出（只写自己目录，不改 PANEL）

- `PANEL_CHK\REPORT.md`：方法、口径、逐表逐行结果、分类统计、头条核对
- `PANEL_CHK\mismatches.tsv`：表头 `panel_line	table_id	subsystem	column	panel_value	recalc_value	class	affects_dod`
- `PANEL_CHK\recalc_all.tsv`：表头 `subsystem	n	named_L	named_S14	named_strict	proved	proved_strict	thr_named	thr_proved	nominal_pass	strict_pass`，22 行 + 1 行 TOTAL
- `PANEL_CHK\recalc.py`：可复跑脚本

## 纪律

- **不许修改** `PANEL.md`、`coverage.tsv`、`R14_COMMON.md`、台账；只写 `PANEL_CHK\`。
- 每个数字必须能被 `recalc.py` 重跑出来；只给结论不给脚本的不算完成。
- 判 `口径错` 之前先确认不是你自己没归一大小写（本轮已有一次前车之鉴：atlas `entry` 是小写）。
- 面板某格定义模糊就记 `无法判定`，**不许猜**。
