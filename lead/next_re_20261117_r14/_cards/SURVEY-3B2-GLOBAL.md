# SURVEY-3B2-GLOBAL — 全表 ③b② 可达性普查（找增量最大的子系统）

## 为什么要做这个

S13 / S15 / S16 三条主攻线都已量化到底（S13 严格口径 0 行可并、S15 差 26、S16 差 24）。R14_COMMON §8.7 已立规矩：**"用零区分力判据扩分母"是明令禁止的**。所以下一步不能凭感觉挑子系统，必须先用一个**只读、可信、有基础率**的普查把"哪里还有量"测出来。

**本卡只测量，不裁行、不并表、不限死结论。**

## 输入

- `lead\next_re_20261117_r14\COVERAGE\coverage.tsv`（只读；18,498 数据行、8 列、行内制表符；第 2 列 subsystem、第 3 列 name、第 4 列语义、第 5 列 grade）
- `lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv`（只读；12,916 行；**`entry` 列为小写十六进制，比对必须大小写归一**）
- `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`（只读；期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`）
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`
- capstone 5.0.7（**必须 `skipdata=True`**）+ pefile 2024.8.26，Python 3.12.10，无 venv、不许 pip install

## 要测的三件事（逐子系统，22 行）

池 = 该子系统且 entry 在 atlas 内 且 `grade != [已证]` 的行。

### 指标 1 · `pool`
池的行数。

### 指标 2 · `p3b2`（③b② 机械命中）

对池中每个 entry 反汇编，判定是否满足**全部**下列机械形态：

- 函数体内存在 `call`，其后**紧邻**（允许 1–2 条无关指令内）出现 `test eax,eax` / `cmp eax,<常量>` / `or eax,eax`
- 该比较后**紧跟条件跳转**
- 该跳转的失败路径与成功路径**指令序列不同**（不是同一处 call 只差参数）

> **注意**：`test` 之后 `eax` 被 `mov eax,[…]` 之类**覆写**再分支的，**不算**（这是上一轮把 S15 的 13 行打到 9 行的陷阱）。

### 指标 3 · `p3b2_named`（是否已具名）

`p3b2` 命中行中 name 非空且不匹配 `^(sub_|.*::sub_)` 的数量。**没名字的行即使 proved 够了也过不了 DoD 第 1 条**，必须单列。

### 派生指标（用来判断"值不值得投入"）

- `best_proved = 现有 proved + p3b2`（**上界，不是预测**）
- `gap_now = ceil(0.5n) − 现有 proved`
- `can_close = best_proved >= ceil(0.5n)`
- `named_ok`：现有 `named_S(R14)` 是否 ≥ `ceil(0.9n)`
- **`verdict`**：`proved 可闭且 named 已够` / `proved 可闭但 named 不够` / `proved 不可闭`

## 输出

- `SURVEY_3B2\survey.tsv`：表头
  `subsystem	n	named_S14	proved	proved_strict	p3b2	p3b2_named	best_proved	gap_now	can_close	named_ok	verdict`
  22 行数据（不含 TOTAL）
- `SURVEY_3B2\REPORT.md`：
  - 全表合计：池多少、`p3b2` 多少、**整体基础率**
  - **按 `best_proved − 现有 proved` 的绝对量排序**，列出前 5 个子系统及其 `verdict`
  - 明确回答：**「若把全部 p3b2 命中的行都证实，有没有任何一个新子系统能达标？是哪几个？」**
  - 明确回答：**「有没有子系统是'proved 可闭但 named 不够'——即瓶颈在名字不在证据？是哪几个、各差多少名字？」**
- `SURVEY_3B2\survey.py`：可复跑脚本
- `SURVEY_3B2\base_rate.tsv`：`population	pool	p3b2	rate`

## 纪律

- **只读**。不许改 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账；只写 `SURVEY_3B2\`。
- `p3b2` 是**机械形态命中**，不是"已证实"。报告里一律写"可辩护候选"，**不许**写成"可升格行"。
- 基础率必须如实报，不许四舍五入到好看。
- 若某子系统池为 0，照写 0，不要跳过该行。
