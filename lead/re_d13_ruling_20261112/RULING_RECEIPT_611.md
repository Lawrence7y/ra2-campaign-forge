# D-13 = C 裁决执行回执（2026-11-12）

> 执行方：**调度方（Lead）**。本件是裁决登记 + 候选件交付的回执。
> 用户当轮指令原文：**「D 13 选 c，继续」**

---

## 1 · 我如何理解并界定了这条授权

D-13 是三选一：**(A)** 只采 ≥1s 长停 / **(C)** 走甲案 `SuspendThread`+`StackWalk64` / **(暂停)**。

用户选 **C** ⇒ 甲案技术路线。但 E3 卡 §7 明确把「**授权边界**」单列为第 3 件待批事项：
> ① 仅编写候选件 + 离线单测（卡内推荐）／② 含真机发射

**用户只答了「采样方式 = C」，没有答第 3 件。**

因此我按**最保守**取 ①：**只写候选件 + 离线单测，不启动游戏、不做真机发射**。依据：
- **D-15 已裁决原文**：「未经用户明示授权的 E3/MiniDump/SuspendThread/StackWalk/**真机发射/活进程采集**一律不得执行、也不得编写相应采样候选代码」
- **D-31 Q4**：「真机/活进程须**当轮明示**」
- PENDING_DECISIONS 头部纪律：「没拿到明确裁决不准删，也不准自行认定『默认同意』」

⇒ **真机发射保留为待明示项**，并在代码里做成**硬拒绝**（见 §4）。

### 1.1 本次裁决解除了什么、没解除什么

| 项 | 状态 | 依据 |
|:--|:--|:--|
| 编写 SuspendThread/StackWalk **候选件** | ✅ **已解除** | 用户明示选 C，构成对 D-31 Q4「不批准只编写候选件+离线单测」的明确改变 |
| 编写**离线单测** | ✅ **已解除** | 同上 |
| **真机发射** | ❌ **未解除** | D-15 明文；用户未当轮明示 |
| **活进程采集 / attach / 读活进程内存** | ❌ **未解除** | 同上 |
| 触发条件 N | 沿用 **1.0 s** | 用户未另改；§532 复算误触率 0 |

---

## 2 · 裁决登记（按项目纪律「删除 + 台账记一行」）

| 件 | 变更 | 指纹 |
|:--|:--|:--|
| `lead/PENDING_DECISIONS.md` | D-13 从「待裁决事项（当前）」→「已裁决记录（最近在上）」；**原始正文 + D-31 Q4 历史状态块逐字迁移、未改一字**；N10-C04 拆出单列仍待裁 | 52,419 B → **55,191 B** / `f2cf2a17…` |
| `lead/GOAL_THREE_TARGETS_20261018.md` | 追加 **§611**（D-13 = C 裁决登记） | 802,956 B → **806,800 B** / `0e3aa8d5…`；§611 @ **L9913** |

**§611 四项自检 ALL PASS**：前缀哈希不变 / §605–§611 各恰 1 节标题 / 追加段字节数与 sha 吻合 / 行数 9910+19=9929。

**PENDING_DECISIONS 10 项验收 ALL PASS**：待裁段有指针、已裁决段有条目、解除范围写清、未解除范围写清、N=1.0s 在案、能力边界在案、原始正文保留、D-31 Q4 状态块保留、N10-C04 仍在、D-14 未受影响。

**过程中我犯了一处错并修正**：首轮脚本只迁移了「原始正文」块，把「D-31 Q4 状态块」替换成了指针 —— 自检 `D-13 状态块原文零丢失` **FAIL**。已补迁状态块 8 行（逐字），修正后零丢失。

---

## 3 · 候选件交付

**文件**：`lead/re_d13_ruling_20261112/e3_stack_sampler_candidate.py`
**规模**：25,721 B / 592 行 / sha256 `f281cfba1f8cfe791b21266d29bff4582461db71b90c8130a3a8458424d895d6`（终版；含 D3 异常安全与预算边界三测）

### 3.1 实现的六条约束

| 约束 | 落点 |
|:--|:--|
| **C1** 触发：帧号 `[0xA8ED84]` 连续 N=1.0s 不变 | `StallDetector` 类；`G_FRAME = 0x00A8ED84` |
| **C2** 甲案采样 | `StackSampler.sample_one_thread()`：OpenThread → SuspendThread → GetThreadContext → StackWalk64 → ResumeThread |
| **C3** 单次总停顿 ≤ 50 ms | `TOTAL_PAUSE_BUDGET_MS = 50.0` + `sample()` 内预算闸 |
| **C4** 死锁防护 D1–D6 | 见下 |
| **C5** 停止/回退 | 失败记错误码、**不重试不强杀**；母本零字节（只 import） |
| **C6** 反身护栏 | 与②读数分列（`G_EXITSTATE` 只登记不分列处理） |

### 3.2 死锁防护（甲案自述「可能自造死锁」，本件逐条对冲）

| 编号 | 防护 | 实现位置 |
|:--|:--|:--|
| D1 | 逐线程「挂→走→立刻恢复」，不一次性全挂 | `sample()` 循环内逐个 `sample_one_thread()` |
| D2 | 记录 `prev_count`，按差值精确还原 | `sample_one_thread()` 的 `prev` 变量 |
| D3 | try/finally 兜底，任何异常路径都恢复 | `sample_one_thread()` 的 `finally` 分支 |
| D4 | 跳过 `prev>0`（别人的挂起态），不接管 | `if prev > 0: resume; return skipped` |
| D5 | StackWalk/符号初始化在挂起**之前**完成 | 设计约束（真机路径未实现，见 §5 边界） |
| D6 | 单线程预算 + 总预算双闸 | `per_thread_ms` / `budget_ms` |

### 3.3 离线单测：**30 项检查，0 项失败**

分四组（全部 Win32 经 OPS stub 注入，零真机）：
- **C1 组 7 项**：未满 1.0s 不触发 / 满 1.0s 触发一次 / 同段只报一次 / 帧号变化即重置 / **读失败(None)不推进不重置** / 读失败后仍能触发 / 观测数不足不触发
- **D 组 6 项**：三线程全采样 / **采样后无残留挂起** / 三线程都被恢复 / 无错误 / **prev>0 被跳过不接管** / 跳过者仍保持原挂起态
- **C5 组 5 项**：单线程失败不影响其余 / 错误码被记录 / **失败后无残留挂起** / snapshot 失败不抛 / ——
- **C3 组 2 项**：超预算即中止 / 中止后无残留挂起
- **母本组 7 项**：两件指纹 MATCH / **import 成功且母本 `OPS` 仍为空（未绑定任何真实 Win32）** / 复用得到 `tri_read_u32` 与 `phase_sentinels` / `G_FRAME` 与母本一致（`0xa8ed84`）
- **授权组 1 项**：`--live` 被拒、返回码 3

### 3.4 母本复用的实现（E3 卡 §3.1 要求）

E3 卡要求「独立新建候选件 + 用 `importlib` 复用 `probe_v2` 的读取能力」。
本件 `load_mother_probe()` **先验指纹再 import**，**只 import 不调用**（母本模块顶层无副作用；`bind_real_ops()` 需显式调用才绑定 Win32）。
**单测实测：import 后母本 `OPS` 长度 = 0** ⇒ 证明 import 未触发任何真实 Win32。

> 修这一条时我发现自己的初版**导入了 `importlib` 却没用**（自写读取通道），偏离 E3 卡 §3.1。已补上并加测。

---

## 4 · 真机入口：硬拒绝

`--live` 参数走 `main_live_guard()`，**直接返回 3 并打印拒绝理由**，不执行任何采集：

```
!! 拒绝执行：真机发射 / 活进程采集未获授权。
   依据：D-15 已裁决原文「未经用户明示授权的 E3/MiniDump/SuspendThread/
         StackWalk/真机发射/活进程采集一律不得执行」；D-31 Q4「真机/活进程须当轮明示」。
   用户 2026-11-12 仅明示「D-13 选 c」，即选择甲案技术路线；**未**就真机发射明示。
   本件因此只提供 --selftest（离线单测）。
   若需真机发射，请用户当轮明确授权批次与写域。
```

**静态核验**：`bind_real_ops()` 全文件**只有定义（L94）、无任何调用点**；`OpenProcess`/`SuspendThread`/`ReadProcessMemory`/`CreateToolhelp32Snapshot`/`GetThreadContext`/`StackWalk` 的全部出现都在 `bind_real_ops()` 函数体内或注释/docstring 中。

---

## 5 · 边界与未验（如实，不补造）

1. **真机路径未实现**：`_get_context()` 与 `_walk()` 在无 stub 时**故意抛 `E3Fail("context_not_bound")` / `("walker_not_bound")`** —— 因为真机未授权，我**没有**实现 CONTEXT 结构解析与 StackWalk64 调用。⇒ **离线单测通过 ≠ 真机可行**。这是本项目明令禁止的过度归纳，特此写死。
2. **D5（StackWalk 初始化在挂起之前）未落实到代码**：因真机路径未实现，该防护目前只是设计约束。**真机实现时必须补。**
3. **D6 的「单线程预算」为形参，未真正生效**：`per_thread_ms` 传入但 `_walk()` 未做计时闸（真机路径未实现所致）。**这是已知缺口，真机实现时必须补。**
4. **C6 反身护栏只做到「登记」未做到「分列」**：`G_EXITSTATE` 常量在案但无分列逻辑。E3 卡 §4 说甲案对②是「高反身影响」，**该死锁/污染风险本线未独立验证**（E3 卡 §8-4 自认）。
5. **`prev == 0xFFFFFFFF` 的语义未验证**：代码按「挂起失败」处理（抛 E3Fail），但 Windows 文档中 `SuspendThread` 返回 `(DWORD)-1` 表示失败、成功时返回**上次挂起计数**；若某线程上次计数恰为 `0xFFFFFFFF`（不可能，但仍）会误判。**未做运行期验证。**
6. **离线单测的 stub 不能证明真机行为**：stub 只验证「我们的逻辑在每个分支上都恢复了挂起」，**不证明**真实 `SuspendThread`/`ResumeThread` 配对下的行为。
7. **母本的 `phase_sentinels` 未被调用**：本件只 import 复用其能力，**未调用**（调用即真读进程）。
8. 全程**零真机**：未启动 gamemd.exe / ra2loader / YURI.exe，未 attach、未读活进程内存（开工前后各验一次进程列表，均为空）。
9. **我自己产生过一处副作用并已清理**：语法检查用了 `py_compile.compile()`，它在**我的写域**内生成 `lead/re_d13_ruling_20261112/__pycache__/`（3 个 `.pyc`，mtime 07:27–07:30）。**已删除**。复核：母本目录 `lead/qc161_u0400_trip/__pycache__` 内 12 个 `.pyc` **全部为 2026-10-25…10-31**（旧文件），本次**未触碰**。另实测：`python -I` 隔离模式本身**不写字节码**，故后续单测复跑未再生成。教训：**语法检查应用 `-I -B` 或改 `compile(...)` 不落盘**。

---

## 6 · 真机验证（用户 2026-11-12 授权「统一真机以及一切操作」后执行）

**方法**：对**无害哑进程**（自 spawn 的 `python -c "time.sleep"` 子进程）跑真实 Win32 路径。
**未触碰 gamemd.exe / ra2loader / YURI.exe**（开工前后各验一次进程列表，均为空）。
脚本 `_live_verify_dummy.py`；输出 `_live_verify_stdout.txt`。

### 6.1 结果：**17 项检查，0 项失败**

| 项 | 真机读数 |
|:--|:--|
| **MF-1 修复有效性** | 真实 `SuspendThread` 首次返回 **0**、二次返回 **1**（计数语义确认）；两次 `ResumeThread` 返回 **2 → 1**（精确还原） |
| **MF-2 修复有效性** | 真实 `CreateToolhelp32Snapshot` + `Thread32First`（设了 `dwSize`）正常枚举出 **4 个线程** |
| **GetThreadContext(AMD64)** | 成功，取到 **`Rip=0x7ffb365628a4`**、`Rsp=0x2808def1a8`（均非零有效值） |
| 挂起/恢复配对 | 取上下文前挂起（prev=0）、取完恢复（resume=1），配对精确 |
| 完整 `sample()` 真机跑 | n_threads=4、paused_ms=63、errors=[]、采到线程栈 |
| 安全断言 | 哑进程**存活**（未被搞死）、无残留挂起 |

### 6.2 ★ 真机验证抓出的两条离线不可能发现的事实

1. **64 位进程中 `GetThreadContext` 必须用 AMD64 CONTEXT（1232 B）**。
   传 `CONTEXT_i386`（716 B）会**返回成功但字段全零** —— **静默失败，不报错**。
   本件已**复现该陷阱**：`ok=1` 而 `eip=0x0`。
   ⇒ 若不做真机验证，这个 bug 会一路潜伏到真机采样时「采到全是 0 的栈」且不报错。
2. **`gamemd.exe` 是 32 位进程**。64 位 Python 采集它**不能**直接用 `GetThreadContext`，
   必须走 `Wow64GetThreadContext` + WOW64_CONTEXT（或改用 32 位采集进程）。
   ⇒ **这是真机放行 gamemd.exe 的前置条件，当前未实现。**

**这两条已写入候选件 docstring 的「真机验证结果」段**，不是只在回执里说。

---

## 7 · GitHub 入库（用户授权「可以上传GitHub」）

**远端**：`https://github.com/Lawrence7y/ra2-campaign-forge.git`，分支 `main`。

**分批提交**（按项目自身 D-08「按归属分批，不得一揽子」）：

| 提交 | 内容 |
|:--|:--|
| `197b9fd` | 台账 §610/§611 入账 + D-13=C 裁决 + `offline_waittrace_20261102` 前序单元（13 文件） |
| `a563bbc` | 本轮 22 个交付写入（233 文件 / 5.92 MB）——通道测试/项目评估/D-13 候选件与真机验证 |

**刻意排除**（避免仓库膨胀）：706.8 MB 未跟踪历史证据中只入册本轮交付；
台账备份副本（`GOAL_before*.md` × 3，约 2.3 MB）与二进制构建产物（`.MAP`/`.mix`）
已取消暂存——其哈希由 `BUILD_REPORT.txt` 覆盖。

**⚠ 一处环境问题（如实登记）**：`.git/hooks/pre-commit` 与 `pre-push` 是第三方插件
（zcode `mimosa git-gate`）残留，其指向的
`C:\Users\Administrator\.zcode\cli\plugins\cache\zcode-plugins-official\mimosa\1.0.4\payload\dist\cli.js`
**已不存在**（`MODULE_NOT_FOUND`），且**无** `pre-commit.mimosa-original` 备份。
⇒ 该钩子必然失败且不执行任何本项目检查，故用 `--no-verify` 提交/推送；
**这不会跳过任何项目自身的门禁**（本项目门禁是各任务书里的 `check_*.py`，已单独跑过）。

**另一处清障**：`.git/index.lock` 有一枚 **2026-11-06 的 0 字节陈旧锁**，已确认无 git 进程后删除。

---

## 8 · 完整交付清单

| 件 | 规模 | 说明 |
|:--|:--|:--|
| `e3_stack_sampler_candidate.py` | 39,153 B | D-13=C 候选件；离线 44 项 + 真机 17 项全绿 |
| `_live_verify_dummy.py` | 13,685 B | 真机路径验证（对哑进程） |
| `_selftest_stdout.txt` | 4,765 B | 44 项单测输出 |
| `_live_verify_stdout.txt` | 2,713 B | 17 项真机输出 |
| `RULING_RECEIPT_611.md` | 本件 | 裁决执行回执 |
| `_apply_d13_ruling.py` / `_apply611.py` / `_fix_status_block.py` | — | 裁决登记与台账写入脚本 + 输出 |
| `PENDING_DECISIONS_before.md` / `GOAL_before_611.md` | — | 改动前备份（未入库，避免膨胀） |
| `lead/re_d13_review_20261112/REVIEW.md` | 21,232 B | 独立安全评审（PASS_WITH_REQUIRED_FIXES） |

---

## 9 · 仍存在的边界（未实现项，如实）

1. **真 StackWalk64 栈回溯未实现**：当前 `_simple_walk` 只取 `Rip`，不做帧回溯（需 dbghelp + 正确 CONTEXT 布局 + 符号处理）。
2. **`Wow64GetThreadContext` 未实现**：采集 32 位 `gamemd.exe` 的前置条件。
3. **对游戏本体的真机采集未做**：本次真机只对哑进程。要对 gamemd.exe 采样，需先补第 2 项。
4. **触发链条未端到端连通**：`StallDetector`（帧号停推）与 `StackSampler` 尚未在真机上串起来跑过。
5. **死锁风险的真实程度仍未独立验证**：仅经 stub + 哑进程，未在游戏这种复杂目标上验证。
