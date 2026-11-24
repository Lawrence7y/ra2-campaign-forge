# Antigravity handoff

## Partial result

_The run was not successful. Text received before or with the failure is preserved below as partial evidence._

已完成离线卡 **W93（限帧通道定谳 + ABBA 观测器标定脚本）**，所有产物均仅写于 `lead/next_re_20261112_r06/W93_limiter/` 下，未启动游戏、未注入/调试、未改动原始二进制（`ra2youli/ddraw.dll` SHA-256 仍为 `85E0F7D530DFDA134793A57CB3E76B0287DCC96892EE57162DD68F47283B03A9`）。

---

### 一、核心定谳（任务一，详见 [LIMITER.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/LIMITER.md) 与 [DISAGREE.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/DISAGREE.md)）

1. **`clamp=210` 并非脚本读错，而是 `DEVMODEA.dmDisplayFrequency` 的真实刷新率** `[静态读码]+[本次实测]`：
   - [exp_rpm_framebeat.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r05/W90_replicates/work/tools/exp_rpm_framebeat.py#L104-L112) 直接 `read_u32(h, base + 0x5EE48)`，无算术/偏移错误；唯一误导是 L14/L112 的 `(期望 60/60/16)` 注释。
   - `0x1005EDD0..0x1005EE6B`（`0x9C` 字节）是 `DEVMODEA`，`0x1005EE48`（`+0x78`）即 `dmDisplayFrequency`。`0x10015E34..0x10015E50` 调用 `USER32!EnumDisplaySettingsA(NULL, -1, 0x1005EDD0)` 直接填充；成功时跳过 `0x10015E83`（`mov [0x1005EE48], 0x3C` 仅为 API 失败兜底）。本机只读调用 `EnumDisplaySettingsA` 实测返回 `2560x1440 @ 32bpp, 210 Hz`。
   - 经 `.reloc` 全表（411,648 B / 7 节）与 `.text`+`.detourc` 的 `[reg+0x78]` 间接写扫描，`[0x1005EE48]` 不存在其它静态/间接写入点（仅 `0x10015E35` 传参 `&g_dm` 与 `0x10015E85` 兜底写）。
2. **`sub_10006AE0` 支路与 `[0x1005F120]` (`last_t`) 逐帧更新判决** `[静态读码]`：
   - D3D9 (`0x1001B01A`)、OpenGL (`0x1001CD51`)、GDI (`0x1001D2D2`) 均在渲染循环**顶部**检查 `[0x1005F128] > 0` 后调用 `timeGetTime()` 写入 `[0x1005F120]`，再在循环底部调用 `sub_10006AE0`。
   - 在 `vsync=0, maxfps=60`（基线 `[0x1005F128]=16`）、`vsync=1, maxfps < refresh_hz`、`vsync=1, maxfps >= refresh_hz`、以及 `maxfps=-1`（只要 `1 <= refresh_hz <= 1000`）下，**`[0x1005F120]` 均每帧更新**。Windows 正常路径在 `sub_10006AE0` 内优先走 `WaitableTimer`（`[0x1005F138] != 0`），不写 `[0x1005F124]` (`cur_t`)，仅定时器失败才回退 `0x10006D66`（`timeGetTime+Sleep`）——与 W90 `framebeat_1794640742.csv` 中 `cur_t` 恒为 `0` 互相印证。
   - **失效分支**：`vsync=0` 且 `maxfps=0` 或 `maxfps > 1000`（`interval == 0`）时，三条循环直接跳过写入，`[0x1005F120]` **不再更新**。
3. **只读自检脚本**：已交付纯标准库脚本 [verify_ddraw_globals.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/verify_ddraw_globals.py)，支持枚举 `ddraw.dll` 基址、dump `RVA 0x5EE30..0x5EE70`（16 个 DWORD），断言 `[0x594E8]=60`、`[0x5F128]=16`、`[0x5EE48]=EnumDisplaySettingsA` 刷新率（失败兜底 `60`），失败时打印原始 hex 字节并干净退出。

---

### 二、ABBA 标定脚本与说明（任务二，详见 [ABBA.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/ABBA.md)）

- [abba_driver.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/abba_driver.py)：按 `--blocks 3 --seg-sec 60 --warm-sec 10` 执行 `A->B->B->A` 外部启停（A 启 `exp_rpm_framebeat.py`、B 不启动），写入 `switch_log.ndjson`（含 `t_perf_ns`、区组/段号、相位、`observer_pid`）；支持 `Ctrl-C`/`SIGINT`/`SIGBREAK`/`SIGTERM` 写入 `finished` 优雅退出，以及相位 A 段中提前退出（`crash` + `aborted_crash`，`rc=3`）即停保护；无任何注入或目标内存写入。
- [abba_analyze.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/abba_analyze.py)：联合读取 `switch_log.ndjson` 与被测逐拍 NDJSON，按段丢弃前 `warm-sec`，计算有效窗 `CPU 消耗率 (%) = (Δwin_cpu_ms / 墙钟ms) * 100` 与 `d_block = mean(A) - mean(B)`，输出均值/极差与三档判决（`ACCEPTABLE` / `UNACCEPTABLE` / `UNRESOLVED`），严格不输出 p 值与置信区间。
- **未覆盖与硬边界**：**无独立画面参照**（即使 ABBA 判定 `<= 0.5 pp` 可接受，也只能确认观测器 CPU 扰动在预算内，**不能**用于判断画面本身是否掉帧/卡顿）；默认 3 区组属降配设计；真机 `gamemd.exe` 连续 12 分钟 ABBA 尚未实跑（`[未证]`，见 [UNKNOWNS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/UNKNOWNS.md)）。

---

### 三、交付文件与最终自测结果

- 主要交付：
  - [LIMITER.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/LIMITER.md)、[ABBA.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/ABBA.md)、[DISAGREE.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/DISAGREE.md)、[UNKNOWNS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/UNKNOWNS.md)、[PROGRESS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/PROGRESS.md)
  - [verify_ddraw_globals.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/verify_ddraw_globals.py)、[abba_driver.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/abba_driver.py)、[abba_analyze.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/abba_analyze.py)
  - 证据与反汇编档案：[disasm_evidence.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/EVIDENCE/disasm_evidence.txt)、[limiter_full_disasm.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/EVIDENCE/limiter_full_disasm.txt)、[verify_ddraw_globals_selftest.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/EVIDENCE/verify_ddraw_globals_selftest.txt)、[abba_selftest.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/EVIDENCE/abba_selftest.txt)
- **最终自测**（全部在最终落盘后重跑通过，`rc=0`）：
  - `python lead\next_re_20261112_r06\W93_limiter\EVIDENCE\test_verify_ddraw_globals.py` → `[ALL PASS]`（覆盖 `EnumDisplaySettingsA` 实测 `210 Hz`、`check_globals` 通过/失败/截断字节输出、`--help`、本机无 `ddraw.dll` 进程退出 `rc=2`、`--module kernel32.dll` 活体 RPM）
  - `python lead\next_re_20261112_r06\W93_limiter\EVIDENCE\test_abba_suite.py` → `[ALL PASS]`（覆盖两脚本 `--help`、模拟观测器 3 区组闭环、段中崩溃 `rc=3`、`CTRL_BREAK_EVENT` 写 `finished` 优雅退出 `rc=0`、以及 `[ACCEPTABLE]` / `[UNACCEPTABLE]` / `[UNRESOLVED]` 三档判决与预热尖峰丢弃）

## Prompt sent to Antigravity

````text
# W93 · 提示词（agy / Gemini-4-hydrogen-high）· 限帧通道定谳 + ABBA 可跑脚本

你要执行 RA2 Campaign Forge 项目的**离线卡 W93**。工作目录 `D:\Project\ra2-campaign-forge`。
**只允许写 `lead\next_re_20261112_r06\W93_limiter\` 目录下的文件**；其余路径只读。**禁止启动游戏、禁止注入/调试器、禁止改任何二进制。**

## 背景（已签发，可直接引用；详见 `lead\next_re_20261112_r05\REVIEW\LEAD_VERIFY_W90.md` 与 `lead\next_re_20261112_r03\REVIEW\LEAD_VERIFY_W86.md`）
已确认 cnc-ddraw（`ra2youli\ddraw.dll`，411,648 B，SHA-256 `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9`，ImageBase `0x10000000`，`DllCharacteristics=0x0140` ⇒ **DYNAMICBASE 开**）存在一条**非注入**可观测链：

```
maxfps 解析 → [0x100594E8]        （ddraw.ini: 全局 maxfps=-1；[gamemd] 段 maxfps=60 生效）
     ↓
sub_10006880 初始化 → interval(ms) [0x1005F128] = int(1000/fps)，参考上限 [0x1005EE48]
     ↓
每帧门闸 sub_10006AE0：用 timeGetTime 比 [0x1005F120]（上一帧放行时刻），不足则 Sleep 补差
     ↓
[0x1005F120] 每帧写入（3 处写入点，对应三条 renderer 路径）
```

Lead 已独立核过的字节（你可直接复用，但**若你的反汇编与之冲突，必须以你的实测为准并写 DISAGREE**）：
- `0x10006884  a1 e8 94 05 10  mov eax,[0x100594E8]`
- `0x1001E17D  a3 e8 94 05 10  mov [0x100594E8],eax`
- `0x1001B01A  a3 20 f1 05 10  mov [0x1005F120],eax`
- `0x10006D6C  8b 15 20 f1 05 10  mov edx,[0x1005F120]`
- `0x10015E83  c7 05 48 ee 05 10 3c 00 00 00  mov dword ptr [0x1005EE48], 0x3C`（**唯一的立即数写入 = 60**）

## 任务一（**主任务**）：把限帧通道**完整**定谳，并解释 `clamp=210`
真机实测时，W86 的脚本 `exp_rpm_framebeat.py` 校验 `maxfps=60`、`interval=16` 都通过，但打印的 **`clamp=210`**（脚本注释预期 60）。而 Lead 静态只找到"写入 60"这一条路径。请**定谳**：

1. **`exp_rpm_framebeat.py` 到底读的是哪个地址、那句 `clamp` 是怎么算出来的**（读脚本源码，逐行指出）。若它是读了别的偏移/做了别的换算 ⇒ 直接说明「210 是脚本口径问题」，并给出正确读法。**这是最可能的答案，请优先验它。**
2. 若脚本口径没问题，那么 `[0x1005EE48]` 在运行期**确实**是 210 ⇒ 找**非立即数**写入路径：`mov [abs],eax`（`a3` 形态）、`mov [reg+disp]`（reg 指向该地址）、`memcpy`/`RtlZeroMemory` 批量清零后再赋值等。给地址与字节。
3. **把限帧门闸的三条分支走完**：`vsync` 开/关、`maxfps < 参考上限`、`maxfps == -1`、`interval==0` 时分别走哪条路径，**列出每条路径下 `[0x1005F120]`（放行时刻）是否每帧更新**——因为"这个通道能不能当逐帧仪器"完全取决于此。若某些配置下它不更新，必须明说。
4. 给出**一个只读自检脚本** `verify_ddraw_globals.py`：输入 pid，枚举 `ddraw.dll` 基址，dump `RVA 0x5EE30..0x5EE70` 共 16 个 dword，并**断言** `[0x594E8]=60`、`[0x5F128]=16`、`[0x5EE48]=?`（把期望值与容差写清，失败要打印原始字节而不是崩）。这个脚本要能被下一张真机卡直接用。

## 任务二：把 `OBSERVER_ABBA_PROTOCOL.md` 变成**可跑脚本**
`lead\next_re_20261112_r06\OBSERVER_ABBA_PROTOCOL.md` 是我写的协议（尚未执行）。请写两件东西：
1. `abba_driver.py`：给定 `--pid`、`--blocks 3`、`--seg-sec 60`、`--warm-sec 10`，按 **A→B→B→A** 循环切换观测器（A=启动 `exp_rpm_framebeat.py` 子进程并记录 pid、B=不启动），每次切换写一行 `switch_log.ndjson`（`t_perf_ns`、段号、A/B、观测器 pid）。
   - **要求**：只做"启动/停止外部只读进程"，**不注入、不写目标内存**；能优雅退出（Ctrl-C 时写入 finished 标记）；对"段中崩溃"要能记录并停止。
2. `abba_analyze.py`：吃 `switch_log.ndjson` + 被测的那份逐拍 ndjson（含 `t_perf_ns`/`win_cpu_ms`/`elapsed_ingame_s`），按段切分、丢弃每段前 `warm-sec`、算每段 `CPU 消耗率 = Δwin_cpu_ms/墙钟`，做**区组内配对** `d_block = mean(A) − mean(B)`，输出均值/极差 + **三档判决**（预算：`d` 均值 ≤ 0.5 个百分点、且 3 区组方向一致 ⇒ 扰动可接受；> 0.5 ⇒ 不可接受；方向不一致 ⇒ 未分辨）。**禁止**输出 p 值/CI（点数不够，协议已说明）。

## 交付（`lead\next_re_20261112_r06\W93_limiter\`）
- `LIMITER.md`：任务一的完整定谳（含 `clamp=210` 的结论、三条分支表、`[0x1005F120]` 是否逐帧更新的判决）。
- `ABBA.md`：脚本用法、协议与实现的对应、未覆盖项（尤其"无独立画面参照"这一条**不可**掩盖）。
- `verify_ddraw_globals.py`、`abba_driver.py`、`abba_analyze.py`（**都要能在本机 python 3.12 直接跑**，只用 stdlib + 已装库 `pefile`/`capstone`；写清 `--help`）。
- `EVIDENCE\`：反汇编清单（VA/RVA/文件偏移/字节）、脚本自测输出。
- `UNKNOWNS.md` / `DISAGREE.md` / `PROGRESS.md`。

## 纪律
- 只读二进制；先复制到本卡再分析。
- 结论分级 `[本次实测]`/`[静态读码]`/`[静态推断]`/`[未证]`；**"没找到写入者"要写清搜索范围**（扫了哪些节/多少字节/哪些编码/反例校验）。
- **小步落盘**，每完成一节写一次盘（本机 agy 长任务曾多次 `print timeout` 无最终答复）。
- 时间预算 60–90 分钟；做不到就标 `[未证]` 并给下一步最小证据，**不要编**。



Workspace: D:\Project\ra2-campaign-forge
- For a text-only or connectivity task, reply directly without inspecting files or running tools.
- Report changed workspace paths relative to this workspace.
- Treat additional accessible directories as context unless the task explicitly targets one; report an explicit external target by absolute path.
- Perform the task and create or edit its deliverables in this workspace.
- Use file editing tools for substantive file contents. Keep shell commands concise and use them for build, test, lint, or inspection steps.

At the end, return a concise handoff covering: outcome, files changed (if any), verification performed, and any blockers or remaining risks.
Keep inspection proportional to the task: avoid unbounded recursive enumeration, and if remaining time is limited, stop exploring and deliver the evidence already gathered.
````

## Run

- status: `ERROR`
- wrapper_status: `PARTIAL_NON_SUCCESS`
- process_exit_code: `0`
- conversation_id: `3b90e933-2dcd-48ba-8d15-4dca6396b4e9`
- model: `gemini-4-hydrogen-high`
- effort: `high`
- mode: `accept-edits`
- permission_mode: `always-proceed`
- receipt_path: `C:\Users\Administrator\AppData\Local\Temp\call-agy\.staging\20261114-082025-10672-5a4630e521c0d4c9-receipt.md`
- wrapper_watchdog: `5430.0s`
- agy_total_timeout: `90m`
- idle_warning: `10m`
- idle_grace: `5m`
- elapsed: `1109.5s`
- agy_cumulative_duration_seconds: `1092.5483268`
- agy_cumulative_num_turns: `1`

## Tools used

- `edit_file` ×5
- `manage_task` ×2
- `read_file` ×31
- `run_command` ×37
- `write_file` ×20

## Attempt history

- attempt 1: native_status=ERROR, exit=0, elapsed=1109.469s, conversation_id=3b90e933-2dcd-48ba-8d15-4dca6396b4e9, final_wrapper_status=PARTIAL_NON_SUCCESS, tools={'read_file': 31, 'run_command': 37, 'manage_task': 2, 'write_file': 20, 'edit_file': 5}

## Usage reported by AGY

_These are native AGY counters. On resumed conversations they may be cumulative; do not add cache_read_tokens to total_tokens or infer billing without provider evidence._

- input_tokens: `617366`
- output_tokens: `112369`
- thinking_tokens: `40193`
- cache_read_tokens: `6288698`
- total_tokens: `729735`

## Error

API error (attempt 2): request failed: Post "https://daily-cloudcode-pa.googleapis.com/v1internal:streamGenerateContent?alt=sse": write tcp 198.18.0.1:58512->198.18.0.17:443: wsasend: An existing connection was forcibly closed by the remote host.

---
Generated by `call-agy` via the official local `agy` CLI. Raw tool arguments/outputs are omitted by default.
