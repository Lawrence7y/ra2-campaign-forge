# W162 PROGRESS

> 卡号 W162（R12）｜① 的因果性与混淆检验｜写域 `lead\next_re_20261116_r12\W162_causality\`

| 时间 | 做了什么 | 结论 / 下一步 |
|---|---|---|
| T+0:00 | 整份读 `R11_COMMON.md`（193 行）、`R12_FACTS.md`（304 行）、`PERF_BASELINE_V2.md` 口径段（§0–§8） | 拿到口径与禁令；确认 W158 主表 = 1161 段/82 趟、`t_perf_ns` 优先 |
| T+0:05 | `grep` 主台账 `win_cpu_ms\|win_cycle\|win_tid` | **撞上 §900**：Lead 已在同一轮做了 CPU-vs-墙钟与混淆项普查（CPU 10.4×、32ms 地板、B0CE88 不可用、g1..g4 恒 0）。⇒ 本卡改成**独立复算 + 增量**，并把"从未被检验"这个前提写进 DISAGREE |
| T+0:12 | `key_scan.py`：全 137 文件 key 并集 | 确认 137 文件 / 2,714,525 行 / 24 主字段；schema A 130 / B 7（与 `R12_FACTS §893-1` 一致） |
| T+0:25 | `field_scan.py`：逐文件字段存在表 | **新发现**：`A8E9A0/87E8E0/ABCD58/g1..g4` 只在 7 个文件（280,831 样本）；`B0CE88` 在 129 个文件；`X87E8E0` 与 `87E8E0` 是同一计数器的两种拼写，**互斥**出现 |
| T+0:40 | 查 `w94_trip.py:99/126-139/690-697`、`tick_cpu_probe.py:117` | **钉死语义**：`win_tid = GetWindowThreadProcessId(hwnd)` ⇒ `win_cpu_ms` 是**游戏窗口线程单线程** CPU。这是 Q1 能不能用的前提 |
| T+0:50 | `probe.py`（7 条趟） | 确认 15.625 ms 网格 `off_grid=0`、端点差 = Σdelta（0.000000）、`win_cpu_ms` 0 回退；发现 **schema A 的 `mode` 整趟恒 0**（接战趟也是），与 `R12_FACTS` 的 mode=5=局内 冲突 ⇒ DISAGREE D-1 |
| T+1:05 | `recompute.py` 首跑 | 被 `Select-Object -First` 截断杀掉（R11_COMMON §0 的陷阱，我又踩了一次）⇒ 改 `>` 重定向 |
| T+1:15 | `recompute.py` 全跑 | 1435 窗 / 89 趟；分桶三表出来：墙钟 32.030→85.089、CPU 6.625→67.506、duty 0.2032→0.7840、CPU 解释墙钟增量 **126.2%** |
| T+1:30 | `analyze2.py` | **本卡最重要发现**：hi 窗 19/19 恒为窗 0–1、lo 窗 3/4–14、**零交错**；`X87E8E0` 19/19 为负（它是单调趟内时钟）；B0CE88 中位口径全 0、均值口径 +0.297（复算 Lead §900-5） |
| T+1:50 | `analyze3.py` | 107.5 ms 第二模态：5 趟墙钟恒 1.4% 而 CPU/帧 差 2× ⇒ "在等"的正面证据；去开局两窗后关系仍在（符号一致 67.9%）；5 种口径稳健性 → 比值恒 2.657 |
| T+2:05 | `analyze4.py` | 加幅度门后：`\|Δb\|≥10` 时 98.5% 同向（对 (a) 有利）；range1 端点斜率 **18.9 ms/发** vs 标准臂 0.617–0.712（对 (c) 有利）；楼板段 cpu 涨 3 倍而墙钟只动 0.008 ms |
| T+2:20 | `tables.py` + 两次 `recompute.py` | 交付 TSV 落到卡根（首版误写到 `work\`，已改路径并重跑）；`confounders.tsv` 4 段全齐 |
| T+2:35 | 写 `CAUSALITY.md` / `UNKNOWNS.md` / `DISAGREE.md` / `EVIDENCE\INDEX.md` | 交付完成，未 `git commit` |

## 我排除了什么

- **`win_cpu_ms` 是 harness 采样线程**的假设 —— 排除。源码级 `GetWindowThreadProcessId(hwnd)`。
- **q1 是"在等"** —— 高弹区间排除（占空比 0.78–0.82、CPU 增量 126% 覆盖墙钟增量）；低弹区间**成立**（32ms 地板）。
- **25.30/50.40 是引擎台阶** —— 排除。25.30 低于全语料硬地板 31.9074，物理上不可能是真帧时间。
- **`B0CE88` / `g1..g4` / `A8E9A0` / `ABCD58` 可作混淆项** —— 排除（分布已列）。
- **"趟内配对能证明子弹驱动"** —— 排除其证明力（hi/lo 零交错，等价于开局 vs 之后）。

## 下一条最有区分力的证据

在同一窗口里加两个读址：`[0x00B0F730]`（`AbstractClass::Array.Count`）与 `[0x00A8ED50]`，让"对象数"与"子弹数"在某些窗口**不共线**。判据见 `CAUSALITY.md §5.3`。
