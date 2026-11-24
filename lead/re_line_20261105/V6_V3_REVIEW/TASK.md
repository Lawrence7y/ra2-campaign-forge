# V6 任务书 · W5 扩项副本 **V3 状态**的复核重跑（D-21 裁 A 之后）

> **为什么要有这一题**：D-21 裁 A 之后我改了 W5 扩项副本与 A1 采样接口，
> **副本 SHA256 已从 `eb53a617…` 变为 `5081780c…`**。
> W5 原四道复核（`reviews/Q1~Q4_review.md`）复核的是**旧值**，
> 按锚点 §三 **铁律 9**（「复核结论必须绑定被核对象 SHA256」）：
> **旧复核不能用于新副本** ⇒ 必须重跑。
>
> **本任务是复核重跑，不是新一轮设计。零真机、不运行副本。**

## 0. 先读（按序）

| # | 文件 | 作用 |
|---|---|---|
| 1 | `lead/re_line_20261105/D21_RULING/RULING_D21.md` | 裁 A 原文（改什么、为什么） |
| 2 | `lead/re_line_20261105/D21_RULING/EXECUTION_D21.md` | **我改了什么**（逐条对应裁决书五条） |
| 3 | `lead/re_line_20261105/D21_RULING/_d21_burden5_out.txt` | 五读负担实算（+13.094% / 最坏窗 +31.355%） |
| 4 | `lead/re_line_20261105/W5_HARNESS_EXT/TASK.md` | 原 W5 任务书（六问来源） |
| 5 | `lead/re_line_20261105/W5_HARNESS_EXT/reviews/Q1~Q4_review.md` | **旧复核**——读它只为对照，**不得沿用其结论** |

## 1. ★★ 强制要求：复核回件必须写死被核对象 SHA256

**每份复核回件的开头必须有这一段**（缺则整份作废）：

```
被核对象 SHA256 = <实算值>，字节数 = <实算值>
被核对象路径 = <绝对路径>
复核时刻 = <你实际读取的时刻>
```

**参照实算值**（你自己重算，**不得照抄我的**——照抄视为未核）：

| 文件 | 我算出的 SHA256 | 我算出的字节数 |
|---|---|---|
| `W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py` | `5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161` | 499,047 |
| `A1_SAMPLER_CANDIDATE/frame_edge_sampler.py` | `b382e893bafc6a7f38d08572affaa663eaef56a8de7c3f361eea38cc34185f3e` | 21,411 |
| `W5_HARNESS_EXT/_w5_test.py` | `df5771a830c4fa2df5445156284a65d7a5d1e2c4ac80945350a0d05c727df2c8` | 36,624 |

★ **若你算出的 SHA256 与上表不同** ⇒ 说明文件在我派单后又被改过 ⇒
**立即在回件里标 `OBJECT_CHANGED`，以你算出的为准，并说明差异。**

## 2. 四项复核（对应 D-21 裁 A 的五个执行点）

### R1 · 复用前读路径是否真的只读 5 次

- `read_sample(reader, clock, f_pre=None, t_pre=None)`：传 `f_pre` 时是否**真的不调** `reader(FRAME_VA)`？
- 缺省 `f_pre=None` 时是否**保持原 6 读行为**（向后兼容）？
- 用**可计数 reader** 实测两种模式的读次，**给出原始计数**。
- **反例要求**：构造一个「reader 只在 FRAME_VA 上计数」的探针，验证复用模式 **0 次**前帧号读。

### R2 · 时间戳契约是否被正确分开

- 复用模式下 `ts["f_pre"]` 是否等于传入的 `t_pre`（**而不是**进入函数的时刻）？
- `ts["segment_start"]` 是否**独立**记录为业务段起点（复用模式下 ≠ `ts["f_pre"]`）？
- 传 `f_pre` 但**不传** `t_pre` ⇒ `ts["f_pre"]` 是否为 `None` 且 `f_pre_anchor_known=False`？
- **反例要求**：故意传一个明显偏早的 `t_pre`，验证 `ts["f_pre"]` 用它而非当前时刻。

### R3 · W5 副本调用点是否真的传了新参数

- `qc151_trip.harness8_v4_ext.py` 的 `poll-span-hook` 块里，沿触发那行是否
  `read_sample(reader, time.perf_counter, f_pre=f, t_pre=t_now)`？
- **是否为唯一调用点**（不得有第二处旧式调用漏改）？
- 用 `grep`/AST 给出**全部** `read_sample(` 调用点清单。

### R4 · 改动面与禁止面是否仍成立（独立重跑）

- 重跑 `_w5_diff_proof.py`，确认：删 8 块后 SHA256 **仍 == 母本** `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`；
- 「新增 N 行 / 删除 0 / 修改 0」是否仍成立（N 应为 233）；
- 六个禁止面 API 出现次数是否仍与母本**逐项相同**。

### R5 · 单测是否真的覆盖了「5 读」（非空跑）

- 重跑 `_w5_test.py`，确认 6 条全 PASS 且 `EXIT=0`；
- **检查用例 2 的断言强度**：是否真的断言 `total_extra_reads == edges * 5`（而不是放宽成 `<=`）；
- 检查用例 2.3 的时间戳全序断言是否已适配复用模式（`ts["f_pre"] <= ts["segment_start"]`）；
- **反例要求**：把 `read_sample` 的 `f_pre` 处理临时改坏（在你的**副本副本**里改，不动原文件），
  确认单测会 **FAIL**（证明断言不是摆设）。

## 3. 交付物

写到 `lead/re_line_20261105/V6_V3_REVIEW/`：
- `V6_V3_REVIEW.md` —— 正文（六节：0 总判 / 1 SHA256 绑定 / 2 R1–R5 逐条判定 / 3 反例与实跑证据 / 4 必须改项 / 5 诚实账）
- `_v6_probe.py` + `_v6_probe_out.txt` —— 你实跑的探针与原始输出
- `reviews/` 下每项一份独立回件（若你分派子任务）

**判定规则**：
- 任一项会让「读数错/丢/null 变 0」或「flag-off 行为不再逐字相同」⇒ 总判 **REFUTED**；
- 只属可改进不产生错误读数 ⇒ **PARTIAL** 并列出改进项；
- 全部满足才可 **CONFIRMED**。
- ★ **缺 SHA256 绑定段 ⇒ 无论如何不得判 CONFIRMED**。

## 4. 铁律（违反即作废）

- **零真机**：不启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，**不读活进程内存**。
- **零采样注入代码**：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入。
- **只读**：`ra2youli\`、`out\re_work\...`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md`、
  `W1_*`…`W5_*` 既有件、`D*_RULING\`、`A1_*`、`A2_*`、`A3_*`、`_leader\*`、
  `lead/goal1_harness8_20261031/*` —— **一律不得修改**。
  **唯一写域 = `V6_V3_REVIEW/`**。
  ★ 「反例要求」里的「改坏副本」必须在 `V6_V3_REVIEW/` 内**复制一份**再改，**不得动原文件**。
- Python 一律 `python -I -X utf8`，绝对路径。
- **不 commit、不 push**。
- 每个数字追到「实跑命令 + 输出」或「文件:行」；**拿不到就写「未验」，不许补造**。
- ★ **不要把「查不到」当成「不存在」**（A3 曾两次犯此错）。
