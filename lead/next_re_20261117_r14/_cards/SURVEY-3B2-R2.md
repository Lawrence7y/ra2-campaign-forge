# SURVEY-3B2-R2 — 把 1,733 收敛到"真实可证池"（② 是约束瓶颈）

## 为什么要重做

上一轮 `SURVEY-3B2-GLOBAL` 测出 ③b② **机械形态**可辩护候选 **1,733** 行。但 S04 的两批实测给了反证：

- S04 的 73 个候选里，抽核 **36 行**，**四环齐全 0 行**
- 系统性败因是 **② 类身份全部 `未取得`**（以及 ④ 只有 direct-only）
- 而 S04 的 `p3b2_named = 0`——它的 73 个命中**一个名字都没有**

结论：**③b② 的机械形态不是瓶颈，② 类身份才是。** 1,733 是个虚高的上界，真实可证池远小于它。本卡把这个数收敛掉。

## 输入（全部只读）

- `lead\next_re_20261117_r14\SURVEY_3B2\survey.tsv`、`hits_detail.tsv`、`REPORT.md`
- `lead\next_re_20261117_r14\S04_PUSH_B1\REPORT.md`、`S04_PUSH_B2\REPORT.md`（36 行的实测败因，**这是本卡的锚点证据**）
- `lead\next_re_20261117_r14\COVERAGE\coverage.tsv`（18,498 行、8 列；第 3 列 name）
- `lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv`（12,916 行；**`entry` 小写，须归一**；有 `strings` 列）
- `lead\next_re_20261117_r14\NAME_CEILING\ceiling.tsv`（L1/L2 分级的现成口径）

## 要做的事

对 1,733 个候选逐个打三个标签（都可以从表算，**不必全量反汇编**）：

### 标签 1 · ② 是否可能成立（`r2_feasible`）

- `yes_named`：该行在 `coverage.tsv` 里 name 非空且不匹配 `^(sub_|.*::sub_)`（**名字本身给了类归属**）
- `yes_rtti`：名字不可用，但 entry 可由虚表槽反查到类（用 `ceiling.tsv` 的 L2 口径）
- `no`：两者都不成立

> 依据：S04 实测 36 行全败，正是因为它们全是 `no`。所以 `r2_feasible` 是硬约束。

### 标签 2 · ④ 是否可能成立（`r4_feasible`）

- `yes`：存在**非 direct-only** 的使用见证（活虚表派发点），且该见证与 ② 的来源**不同源**（D-40 新禁则：② 与 ④ 不得共用同一虚表槽）
- `no`：只有 direct-only 或与 ② 同源

### 标签 3 · 是否在池内

确认 `grade != [已证]` 且 entry 在 atlas 内。

## 要产出的表

### 表 A · 逐子系统收敛

`subsystem | p3b2 | r2_yes_named | r2_yes_rtti | r2_no | r4_yes | **realistic** | proved_now | thr_proved | closable`

- `realistic` = `r2_feasible 且 r4_feasible` 的行数（**这才是真实可证池**）
- `closable` = `proved_now + realistic >= thr_proved`

### 表 B · 全表收敛

| 量 | 值 |
|---|---|
| 上界（机械形态） | 1,733 |
| ② 可行 | ? |
| ②∧④ 可行（真实可证池） | **?** |
| 收敛率 | ?% |

### 表 C · 抽样验证（必须做）

从 `realistic` 命中的行里抽 **10 行**，逐行**实际反汇编**确认：

1. ② 类身份确实能定出来（给 RTTI 描述符地址或虚表槽 + 类名的依据）
2. ④ 使用见证确实存在且与 ② 不同源（给派发点地址）
3. ③b② 检查点链条成立（`call` → `test/cmp` → 条件跳转 → 失败路径不同 → 返回值被消费）

给出这 10 行里 `FULL_OK` 几行 / `FAIL` 几行。

## 输出

- `SURVEY_3B2_R2\collapse.tsv`（表 A，22 行）
- `SURVEY_3B2_R2\REPORT.md`（表 B + 表 C + 结论）
- `SURVEY_3B2_R2\sample10.tsv`：表头 `entry	subsystem	r2_ok	r4_ok	r3b2_ok	verdict	reason`，10 行
- `SURVEY_3B2_R2\collapse.py`：可复跑

## 必须回答的三个问题（写进 REPORT）

1. **真实可证池是多少行？**（②∧④ 可行）收敛率多少？
2. **收敛后，有没有任何子系统的 `closable` 由 True 变 False？**（即上一轮 S04 那条"唯一 proved 可闭"是否也被推翻）
3. **按 `realistic` 排序，前 5 个子系统各有多少行**——这决定后续批次该投给谁。

## 纪律

- **只读**。不许改 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账、`SURVEY_3B2` 与 `S04_PUSH_*` 下产物；只写 `SURVEY_3B2_R2\`。
- 表 A 若某子系统 `p3b2 = 0`，照写 0，不要跳过。
- 抽样 10 行必须真反汇编，**不许**用标签推定代替。
- 结论允许打自己的脸：若 `realistic` 很小，就如实写"1,733 主要是机械形态噪声"。
