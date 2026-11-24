# 复核任务书 · 帧沿触发采样候选件（D-20 步骤 A）的**独立复核**

> 你是独立复核员。**执行者 ≠ 核验者**：候选件与单测由 RE 线驱动器本人所写，
> 你的职责是**默认怀疑**地去证伪，而不是背书。
> **零真机、零采样实现、零母本改动。唯一写域 = `lead/re_line_20261105/A1_REVIEW/`。**

## 0. 先读（按序）

| # | 文件 | 作用 |
|---|---|---|
| 1 | `lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py` | **被复核的候选件** |
| 2 | `lead/re_line_20261105/A1_SAMPLER_CANDIDATE/test_frame_edge_sampler.py` | 离线单测（声称 67 PASS / 0 FAIL） |
| 3 | `lead/re_line_20261105/A1_SAMPLER_CANDIDATE/_test_out.txt` | 单测原始输出 |
| 4 | `lead/re_line_20261105/D19_RULING/RULING_D19.md` §1「执行步骤」第 4–6 条 | 规格来源（读序/时间戳/df>1/冻结/回绕/null 的**逐条要求**） |
| 5 | `lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:3831`、`:4004-4045` | 既有 500 Hz 帧号轮询的实现参照 |
| 6 | `lead/re_line_20261105/D20_RULING/RULING_D20.md` | 本步骤的裁定与出口 |

## 1. 你要回答的六个问题（逐条给 是/否 + 证据）

### R1 · 读写语义是否真的守住了「失败不补 0」
- `read_one()` 是否可能把失败**变成**一个看起来合法的 0？
- `bool` 拒收是否覆盖了 `True/False`（Python 里 `bool` 是 `int` 子类）？
- 越界值（负数 / >0xFFFFFFFF）是否被拒？**有没有漏掉的类型**（float / numpy int / Decimal）？

### R2 · 读序与时间戳是否满足 D-19 的「每字段或读段起止时间戳」
- 现在的实现只记**读取之前**的 `clock()`，**不记读取之后**。
  D-19 第 5 条要求「每字段或读段**起止**时间戳」。
  ⇒ **这是否构成不可接受的不满足？** 给出你的判定（满足 / 部分满足 / 不满足）+ 理由 + 若要满足**最小改动**是什么。
- 帧号前读 / 后读各自的时刻是否可用于判定「四字段读数落在哪个帧区间」？给出判据。

### R3 · `df > 1`、`df < 0`、`f is None` 三条边界
- `df>1` 是否**真的没有**插值/补帧（读源码，不要只看注释）？
- `df<0` 标 `unjudgeable` 是否合理？还是应当**进一步区分**「进程重启」与「帧号回绕/重置」？
  若要区分，**静态上有什么可用信号**（提示：可查 `0x55DE7E` 附近有无写 0/写初值的路径）——
  若查不到，明确写「当前不可区分」。
- `f is None` 时 `cross_frame` 记 `None`（不可判）而非 `False`，是否正确？

### R4 · 首样本 vs `unjudgeable` 的区分是否引入新问题
- `classify_first()` 只看 `prev_f is None`。
  ⇒ 如果**窗口中途**出现一次读失败（`f=None`，不改 `prev_f`），下一次成功的帧号会不会被误判？
  **请构造反例测试**：序列 `[100, None, 100]` 与 `[100, None, 150]`，看 `stats()` 计数是否合理。
- 若发现误判，给出最小修复方案（不必实现，写清判据）。

### R5 · 「不得宣称业务字段冻结」这句防线是否真的有效
- `stats()["note"]` 只是**一句话**。若下游只读 `freeze_max_s` 而不读 `note`，会不会误用？
- 建议：是否应把 `freeze_max_s` 改名为自解释的 `frame_clock_freeze_max_s`？
  给出你的判定（应改 / 不必改）+ 理由。

### R6 · 铁律合规
- 源码里是否有 `CreateRemoteThread` / `WriteProcessMemory` / `SuspendThread` /
  `MiniDumpWriteDump` / `StackWalk` / `SetWindowsHookEx`？（单测 T7.3 声称「无」——**独立重跑验证**）
- `RpmReader` 默认 `enable=False`，`open()` 在未启用时是否**真的不触碰**系统调用？
- 有没有**任何**自动发射/自动开句柄的路径（即 import 本模块就会碰系统）？

## 2. 你要交付的

写到 `lead/re_line_20261105/A1_REVIEW/`：
- `A1_REVIEW.md` —— 六问逐条判定 + 你构造的反例测试 + 结论（CONFIRMED / PARTIAL / REFUTED）
- `_review_probe.py` + `_review_probe_out.txt` —— 你实跑的探针（**允许 import 候选件做黑盒测试**，
  **禁止**调用 `RpmReader(enable=True)`、禁止开任何进程句柄）

**判定规则**：
- 六个问题里若任一答「不满足」且属**实质缺陷**（会让读数错/丢/null 变 0）⇒ 总判 **REFUTED**；
- 若只是「可改进但当前不产生错误读数」⇒ 总判 **PARTIAL** 并列出改进项；
- 只有六问全部「满足/可接受」才可判 **CONFIRMED**。

## 3. 铁律（违反即作废）

- **零真机**：不启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，**不读活进程内存**，
  **不调用 `RpmReader(enable=True)`**。
- **零采样代码**：不写任何 `ReadProcessMemory` 可运行实现、hook、MiniDump、SuspendThread、StackWalk。
- **只读**：`ra2youli\`、`out\re_work\...`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md`、
  `W1_*`、`W2_*`、`W3_*`、`W4_*`、`D*_RULING\`、`A1_SAMPLER_CANDIDATE\*`、`_leader\*`
  —— 一律不得修改。**唯一写域 = `A1_REVIEW/`**。
- Python 一律 `python -I -X utf8`，绝对路径。
- **不 commit、不 push**。
- 每个数字追到「实跑命令 + 输出」或「文件:行」；**拿不到就写「未验」，不许补造**。
- 引用候选件行为必须**读源码或跑黑盒测试**，不得只看 docstring 就采信。
