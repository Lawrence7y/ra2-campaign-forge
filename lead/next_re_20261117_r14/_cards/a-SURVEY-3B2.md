# a-SURVEY-3B2 — 异族审计全表 ③b② 普查的 1,733 计数

## 身份

你是**异族独立审计员**。执行器家族是 Hy4 / Zhipu 的普查代理，你不是。不采信普查结论，只采信你自己反汇编出的字节。

## 为什么要审

`SURVEY_3B2-GLOBAL` 报了一个将成为后续全部决策基础的数：

- 池 **11,426** 行（Lead 已独立复算，确认无误）
- ③b② **机械形态可辩护候选 1,733** 行（基础率 **15.17%**）
- 其中**已具名仅 552**
- 结论：即使 1,733 行全部证实，**没有任何新子系统能达标**

这个 1,733 是**上界型数字**，一旦虚高，就会让"不可达"的结论建立在沙上。**本卡审的就是这个数准不准。**

## 待审

- `SURVEY_3B2\survey.tsv`（22 行、12 列）
- `SURVEY_3B2\hits_detail.tsv`（命中明细，首选抽样来源）
- `SURVEY_3B2\REPORT.md`、`SURVEY_3B2\survey.py`、`SURVEY_3B2\base_rate.tsv`
- 全部**只当线索**

## 目标与工具

- `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`
- capstone 5.0.7（**必须 `skipdata=True`**）+ pefile 2024.8.26，Python 3.12.10，无 venv、不许 pip install

## 抽样规则

从 `p3b2` 命中的 1,733 行里抽 **12 行**，必须覆盖：

- 4 行来自命中数最多的两个子系统（S22、S06）
- 4 行来自中等命中（S18、S09、S14 中任选）
- 2 行来自命中数最少的子系统（接近 0 的那几个）
- 2 行随机（用固定种子，把种子写进报告）

把你实际抽到的 12 个 entry 与抽样命令写进报告。

## 每行要验的四件事

1. **检查点真实**：`call` 之后确有 `test eax,eax` / `cmp eax,<常量>` / `or eax,eax`，给地址与字节（`85 C0` / `3D …` / `85 C0` 等）。
2. **比较后紧跟条件跳转**：给跳转地址与目标。
3. **失败路径与成功路径指令序列不同**：给出两条路径的首几条指令，证明不是"同一处 call 只差参数"。
4. **`eax` 覆写陷阱**：`test` 之后 `eax` 是否在分支前被 `mov eax,[…]` 之类覆写？**覆写则本行不计命中**（这是上一轮把 S15 的 13 行打到 9 行的陷阱）。

另外核一次**口径正确性**：

5. 该行在 `coverage.tsv` 里确实是 `grade != [已证]` 且 entry 在 atlas 内（atlas 的 `entry` 是**小写**，须大小写归一）。若抽到的行不符合池定义，说明池算错，**立刻报告**。

## 输出

- `SURVEY_3B2\_audit\VERDICT.md`：逐行四项结论 + 地址与字节
- `SURVEY_3B2\_audit\sample.tsv`：表头 `entry	subsystem	check_at	jump_at	paths_differ	eax_overwritten	verdict	reason`，12 行
  - `verdict`：`HIT_OK` / `HIT_BAD` / `NOT_IN_POOL`
  - `entry` 大写十六进制、无 `0x` 前缀
- `SURVEY_3B2\_audit\SUMMARY.md`：必须回答
  1. `HIT_OK` 几行、`HIT_BAD` 几行、`NOT_IN_POOL` 几行
  2. **若把 12 行的命中率外推到 1,733，虚报率是多少**
  3. 「1,733 这个上界是否可信」——给出你的判断与依据
  4. 「若把虚报率计入，1,733 降到多少」，以及**这个下降会不会推翻『没有新子系统能达标』的结论**（用最接近达标的 S04 做检验：它的 `p3b2` 是 73，`best_proved` 164 对门槛 158，余量只有 6；若 73 里虚报 6 行以上，S04 就连 proved 都闭不上了）

## 纪律

- 证据不足判 `HIT_BAD`，不许"基本成立"。
- 不许引用 `hits_detail.tsv` 当证据，必须自己反汇编。
- **不许修改** `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账、以及 `SURVEY_3B2` 下的普查产物；只写 `SURVEY_3B2\_audit\`。
