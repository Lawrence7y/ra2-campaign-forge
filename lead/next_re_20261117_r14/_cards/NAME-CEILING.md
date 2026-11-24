# NAME-CEILING — 名字天花板测量（决定 DoD 是否还有意义）

## 为什么要做

`SURVEY-3B2-GLOBAL` 已测出：即使把全表 **1,733** 行 ③b② 可辩护候选全部证实，**没有任何新子系统能达标**。唯一 proved 可闭的是 S04（`best_proved` 164 ≥ 门槛 158，余 +6），但 S04 的 `named_S(R14)` 只有 **104**、门槛 **285**、差 **181**，且它的 73 个命中**全部无名**。

所以现在**全项目的瓶颈是名字，不是证据**。本卡要回答一个决定性问题：

> **每个子系统的 `named_S(R14)` 最多能做到多少？有没有任何一个子系统能到 `ceil(0.9n)`？**

如果答案是没有，那"22 个子系统全部达到 DoD"在当前判据下就是**数学上不可达**，必须让用户知道并裁决，而不是继续无限期地扫。

## 输入（本卡大部分可以从表算，不必全量反汇编）

- `lead\next_re_20261117_r14\COVERAGE\coverage.tsv`（只读；18,498 行、8 列；第 3 列 name、第 5 列 grade）
- `lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv`（只读；12,916 行；**`entry` 为小写，比对必须大小写归一**）
  - 注意该表有 `strings` 列与 `n_strings` 列，**命名线索很可能就在这里**，先用表算，不要一上来就全镜像反汇编
- `lead\next_re_20261117_r14\SURVEY_3B2\survey.tsv`（现成口径参考）
- 如需反汇编：`ra2youli\gamemd.exe`（期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`），ImageBase `0x400000`，`.text = [0x401000, 0x7E038D)`，capstone 5.0.7（**必须 `skipdata=True`**）

## 口径定义（严格照此）

对每个子系统（22 行），`n` = 该子系统且 entry 在 atlas 内的行数。把 `n` 行按名字状态分四类：

- `A_named`：name 非空且不以 `sub_` 开头、且不匹配 `::sub_`
- `B_substyle`：匹配 `^(sub_|.*::sub_)`
- `C_slotstyle`：已具名但形如 `::slotN` / `::vslotN`（属 `A_named` 的子集，单独统计以便看 strict 口径）
- `D_empty`：name 为空

`named_S(R14)` 现值 = `A_named` 数（含 `C_slotstyle`）。

## 要测的三件事

### 1. 名字可解上限（`nameable`）

对 `B_substyle` 与 `D_empty` 的行，判断**名字能否被解出来**。按证据强度分三级，分别计数：

- **L1 · 表内可解**：`function_atlas.tsv` 的 `strings` 列里含可识别的类名/方法名线索（例如 `.?AV<Class>@@`、`<Class>::<Method>` 形态），且能唯一对应
- **L2 · 需反汇编可解**：表内无线索，但 entry 可从虚表槽反查到所属类（虚表地址 + 槽号 + RTTI 描述符），能定出 `Class::slotN`
- **L3 · 不可解**：既无线索、也无法由虚表/RTTI 归属

给出每级计数。

### 2. 天花板

- `ceiling_strict_off = A_named + L1 + L2`（把能解的全解出来，`slotN` 也算）
- `ceiling_strict_on = A_named + (L1 + L2 中不是 slotN 形态的)`
- `thr_named = ceil(0.9n)`
- `reachable = ceiling_strict_off >= thr_named`

### 3. 结论（本卡核心）

明确回答三问：

1. **有几个子系统的 `named_S(R14)` 天花板够 `ceil(0.9n)`？分别是谁、余量多少？**
2. **有几个即使把全部可解的名字都解出来也够不到门槛？分别差多少？**
3. 若第 2 问的名单覆盖全部 22 个 ⇒ **明确写出「在当前判据下，22 个子系统全部达到 DoD 在数学上不可达」**，并给出支撑这一句话的两个最硬数字（最优子系统的天花板与它的门槛、以及差距）。

## 输出

- `NAME_CEILING\ceiling.tsv`：表头
  `subsystem	n	A_named	C_slotstyle	B_substyle	D_empty	L1	L2	L3	ceiling_off	ceiling_on	thr_named	reachable`
  22 行数据
- `NAME_CEILING\REPORT.md`：方法、口径、三问结论、以及"不可达"论证（若成立）
- `NAME_CEILING\ceiling.py`：可复跑脚本
- `NAME_CEILING\samples_L1.tsv` / `samples_L2.tsv`：各抽 ≥10 行，给出 entry、你的判定依据（strings 原文或虚表槽 + RTTI 地址）

## 纪律

- **只读**。不许改 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账；只写 `NAME_CEILING\`。
- `L1/L2` 是**可解**判定，不是"已解"。报告里写"可解上限"，**不许**写成"已具名"。
- 抽样必须给依据原文；只报计数不给样本的不算完成。
- 若某级判定拿不准，**宁可记 L3（不可解）**——本卡要的是保守下界，不是乐观上界。
