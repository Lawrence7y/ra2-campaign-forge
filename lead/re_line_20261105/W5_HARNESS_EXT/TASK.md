# W5 任务书 · harness **只读扩项副本**（四 VA + 帧沿触发）——**不实现真机发射**

> 你是 RA2/YR 引擎观测工具链工程师 + 代码审计员。
> **本任务是 D-20 步骤 A 的第二半之前置件**：现有 harness
> `lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py` **不带**这四个 VA 的读取，
> 要跑 3 趟真机必须先做一个**只加四个只读 VA** 的副本。
>
> ★ **本任务不跑真机、不发任何进程**：只写副本 + 离线单测。

## 0. 先读（按序）

| # | 文件 | 作用 |
|---|---|---|
| 1 | `lead/re_line_20261105/D19_RULING/RULING_D19.md` §1「执行步骤」第 4–6 条 | 规格来源（读序/时间戳/df>1/冻结/回绕/null/附加读取） |
| 2 | `lead/re_line_20261105/D20_RULING/RULING_D20.md` | 本步骤的裁定与出口 |
| 3 | `lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py` | **已验收的候选件（V2）**——扩项必须复用它的语义，不要另造 |
| 4 | `lead/re_line_20261105/A1_REVIEW/A1_DISPOSITION.md` | 候选件 V1→V2 修了什么（5 条缺陷） |
| 5 | `lead/re_line_20261105/A2_EDGE_BURDEN/A2_EDGE_BURDEN.md` | **负担实测数**（+10.475% 整体 / +25.08% 最坏窗）与冻结窗零样本盲区 |
| 6 | `lead/re_line_20261105/A3_S4_INJECTION_CENSUS/A3_S4_INJECTION_CENSUS.md` | ★ **`ra2render.dll` Hook 风险**与「必须断言 `ra2render_hits==[]`、禁 `--allow-loader`」 |
| 7 | `lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py` | **被扩项的母本**（489,502 B；SHA256 `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`） |

## 1. 已定谳的前提（**直接采用，不得推翻**）

1. 四个 VA 已由 D-19 采纳为「**语义受限**的候选字段」，**不得**换算为可见单位数/工作量/耗时：
   - `0x0087E8E0` 工作区代际**尝试**代理
   - `0x00A8EC34` 索敌入口**调用累计**代理（★ 见 §4 的 Hook 风险）
   - `0x00B0CE88` **脏矩形向量当前 Count**（瞬时队列量，**非**可见单位数）
   - `0x00A8ED50` **注册 Bullet 对象 Count**（实际更新另受 `+0x98` 活跃标志门控）
2. 帧号 VA = `0x00A8ED84`；既有轮询 `MEASURE_HZ = 500`。
3. **alpha 映射未校准、采样充分性未证** —— 两个标记必须出现在**每一份**产出里。
4. **四 VA 地址不连续**，**不是**一次原子 16 字节快照。

## 2. 你要交付的四件事

### Q1 · 扩项副本本体（**唯一产出的代码文件**）

在 `lead/re_line_20261105/W5_HARNESS_EXT/` 下产出 `qc151_trip.harness8_v4_ext.py`，
**以 `harness8_v4.py` 为母本逐字节复制后用最小改动插入新块**，要求：

| 要求 | 判据 |
|---|---|
| **默认关闭** | 新增 CLI 开关缺省 `0`；开关为 `0` 时行为与母本**逐字相同**（flag-off 房规） |
| **只读** | 只新增 `ReadProcessMemory` 读；**零** `WriteProcessMemory` / 零注入 / 零挂线程 |
| **复用候选件语义** | 直接 `import frame_edge_sampler`（`sys.path` 指向 `A1_SAMPLER_CANDIDATE`），**不重写**帧沿状态机 |
| **四 VA + 帧号** | 只在检测到 `CurrentFrame` 变化时追加四读（A2 已算负担） |
| **null 不补 0** | 读失败记 `null`，不得写 0 |
| **两个标记** | 每条记录带 `markers: ["alpha_uncalibrated","sampling_sufficiency_unproven"]` |
| **断言 S4** | ★ 新增一条**硬断言**：`ra2render_hits == [] and ra2loader_hits == []`，否则**立即停手**；并且**拒绝**在 `--allow-loader` 下启用扩项（A3 §7 的硬要求） |
| **改动面可审计** | 用**块标记**（如 `# >>> W5EXT-BEGIN` / `# <<< W5EXT-END`）包裹所有新增，使「删块即还原母本」可机械验证 |

### Q2 · 改动面证明（**必须机械可验**）

写 `_w5_diff_proof.py` + 输出 `_w5_diff_proof_out.txt`，证明：

1. **删块即还原**：把 `W5EXT-BEGIN..END` 全部删掉后，剩余内容与 `harness8_v4.py` **逐字节相等**（给 SHA256 对照）。
2. **改动面清单**：除块内新增外，母本原有行**零改动**（逐行 diff 计数：新增 N 行、删除 0 行、修改 0 行）。
3. **禁止面扫描**：副本里 `WriteProcessMemory` / `CreateRemoteThread` / `SuspendThread` /
   `MiniDumpWriteDump` / `StackWalk` / `SetWindowsHookEx` 出现次数**必须与母本相同**（不能变多）。

### Q3 · 离线单测（**不跑真机**）

写 `_w5_test.py` + `_w5_test_out.txt`，用**注入的假 reader**覆盖：

1. 开关为 `0` ⇒ 不产生任何新采样行（零行为差的**结构**证明）；
2. 开关为 `1` ⇒ 每沿恰好追加 4 次读 + 2 次帧号读；
3. 读失败 ⇒ 字段为 `null`，**不是** 0；
4. `S4` 命中 ⇒ 立即停手（不得进入采样）；
5. `--allow-loader` + 扩项 ⇒ **拒绝启动**；
6. 帧冻结窗 ⇒ **零样本**，且不宣称该窗零成本。

**全部用例必须 `EXIT=0` 才算通过。**

### Q4 · 负担复算（对齐 A2）

用 A2 的 87 窗真实沿数重算本副本的追加读写量，与 A2 的 `+10.475%` / `+25.08%` **逐项对照**。
若与 A2 不一致，**指出差异并给原因**，不要强行对齐。

## 3. 交付物

写到 `lead/re_line_20261105/W5_HARNESS_EXT/`：
- `W5_HARNESS_EXT.md` —— 正文（六节：1 一句话结论；2 扩项设计与块标记；3 改动面证明；4 离线单测；5 负担复算；6 诚实账）
- `qc151_trip.harness8_v4_ext.py` —— 扩项副本
- `_w5_diff_proof.py` / `_w5_diff_proof_out.txt`
- `_w5_test.py` / `_w5_test_out.txt`

## 4. ★ 必须写进正文的安全披露

`ra2render.dll` 的 9 字节 Hook（`0x6F8DF0`）会把 `0x00A8EC34` 的自增节流到 1/8。
正文必须写一行：
> 「本副本在启用扩项前断言 S4 零命中；若 `ra2render` 在场，`threat_calls` 字段**不可解释为入口调用总数**。」

## 5. 铁律（违反即作废）

- **零真机**：不启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，**不读活进程内存**，
  **不运行本副本**（只静态改 + 离线单测）。
- **零采样注入代码**：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入。
- **只读**：`ra2youli\`、`out\re_work\...`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md`、
  `W1_*`、`W2_*`、`W3_*`、`W4_*`、`D*_RULING\`、`A1_*`、`A2_*`、`A3_*`、`_leader\*`、
  `lead/goal1_harness8_20261031/*` —— **一律不得修改**。**唯一写域 = `W5_HARNESS_EXT/`**。
- Python 一律 `python -I -X utf8`，绝对路径。
- **不 commit、不 push**。
- 每个数字追到「实跑命令 + 输出」或「文件:行」；**拿不到就写「未验」，不许补造**。
- ★ **纪律第四条**：统计结构化文本前先确认「第几个字段是什么」，并从**产出该文件的代码**反查格式。
- ★ **不要把「查不到」当成「不存在」**（A3 曾两次犯此错）。
