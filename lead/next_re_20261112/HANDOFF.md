# HANDOFF · RA2 Campaign Forge 逆向 · RE-N00 / RE-N01 阶段交付

> **run_id**：`NEXT_RE_20261112_R01`
> **日期**：2026-11-12（Asia/Shanghai）
> **本轮范围**：RE-N00（固定证据与版本）、RE-N01（修正采样、计时、原始数据保留）、RE-N02 静态部分、RE-N05 静态部分
> **本轮授权状态**：**零真机**。未启动游戏、未 attach 活进程、未读活进程内存、未 SuspendThread/StackWalk64、未注入、未 taskkill、未执行任何 git 写操作。
> **产出根目录**：`lead/next_re_20261112/`（选 `lead/` 而非任务书建议的 `out/re_work/`，因为 `out/` 被 `.gitignore` 排除，本轮交付必须可入库复核）

---

## 1 · 当前有效版本与输入指纹

| 对象 | 字节数 | SHA-256 | 状态 |
|---|---|---|---|
| `ra2bench/gamemd.exe` | 4,825,360 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | 与 `ra2youli/gamemd.exe` **逐字节相同** |
| `ra2youli/ddraw.dll`（cnc-ddraw 7.1.0.0） | 411,648 | `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9` | |
| `lead/re_d13_ruling_20261112/_run_hl_match.py` | 15,949 | `33bb2f61a7696e51eed979452f3d6d86859ebcb1d8322f348ff04bdb0ffa9426` | **本轮零字节改动**（收尾实算一致） |
| `lead/re_d13_ruling_20261112/e3_stack_sampler_candidate.py` | 55,720 | `98210b4af460a75746913e35c791147982ec9d492349c9ace275ec817d51840a` | **本轮零字节改动** |
| `ra2youli/RA2MD.INI` = `RA2MD.INI.benchbak` | 1,754 | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | 两者逐字节相同 |
| `ra2youli/ddraw.ini` | 14,782 | `c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52` | |
| 被测地图（`.yrm` 强候选） | 175,361 | `3e3c874572bc02199cddce05b3633888caf968e6fbb457e763fb70b9fbfd5b19` | `[8]试验地_Pro_ProvingGrounds.yrm` |

任务书 §2.2 的 5 个哈希 + 2 个冻结母本哈希：**7/7 实算一致，无漂移**（见 `RE-N00/BASELINE.json` 的 `verification`）。

**镜像身份（必须连带引用）**：本 exe **不是零售原版**——含官方自带的 `.detour`（Westwood Detours 1.x，`Dtr\0`，VA `0xB93000`，不可执行）、`ra2opt apply perf` 的 PE 头栈扩容、加载第三方 `xyr.dll`。既有登记：`docs/re/baseline_integrity_note.md:118-144`、`docs/re/REWRITE_ROADMAP.md:163`。
⇒ **RE-N04 的「原版对照臂」不满足**，要做三臂须另备干净零售 1.001。

---

## 2 · 已完成项（含证据位置与等级）

### 2.1 RE-N00 · 可复现工作包 ✅

交付：`RE-N00/BASELINE.json`（71,701 B）、`INPUTS.tsv`（8,975 B，40 行）、`CURRENT_FACTS.md`（40,302 B）、`RECONSTRUCT.md`（15,814 B）、`_baseline.py`（可重跑，**实测 exit 0**）。

- 40 个输入全实算，`inputs_missing: []`
- 工具链：Python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26 / PowerShell 7.6.10 / Win11 26200 / Ryzen 7 6800H
- git：`main@3872ef6`，未提交改动 290–291 条（含他人并行工作，仅计数、未做写操作）
- 分级分布：`[本次实测]` 27 / `[转引]` 63 / `[待运行验证]` 7 / `[静态推断]` 3 / `[本次读码]` 6

### 2.2 RE-N01 · 采样与原始记录 ✅（Lead 已跑 G1–G5）

**分层结论（关键，勿混写）**：
- **采样器层 `e3_stack_sampler_candidate_r2.py`**：真实现。`--selftest` **58 项 / 0 失败 / exit 0**。新增 `N01-08`（六计时字段、`end_to_end ≥` 分项之和）、`N01-09`（E3Fail 被事件吸收不逃逸）、`N01-10`（五取值两两不同）、`N01-11`（不写私有 `_target_is32` 也能采样）。
- **驱动层 `_run_hl_match_candidate.py` + `re_n01_monitor.py`**：已重写。`run_monitor` 承载流式 NDJSON、分段、`OnlineAccumulator`、`EventTimer`（`perf_counter_ns`）。

**驱动互斥（我读码确认，非 docstring）**：
```python
def build_event(only_tid, sampler, pid, want_tid, timer):
    if only_tid:
        raw = sampler.sample_single(want_tid, pid, timer=timer)   # 不调 sample(pid)
    else:
        res = sampler.sample(pid, timer=timer)                    # 不直接调单线程入口
```

**离线测试（Lead 亲自实跑）**：`python -X utf8 test_re_n01_offline.py` → **13 项 / 0 失败 / exit 0**
| 关键项 | 实测读数 |
|---|---|
| T-A1 单线程模式全线程调用数 | `counts={'sample': 0, 'sample_single': 1, 'sample_one_thread': 0}` |
| T-A3 整事件成本 > 末次调用 | `event_total=24e6 > last_call=5e6`（ns） |
| T-C2 缺测不拼成连续冻结 | `online_conf=0 replay_conf=0 gap_runs=2 merged=False` |
| T-C2b 阳性对照 | `online=1 replay=1`（证明 T-C2 非空断言） |
| T-C4 在线 vs 离线重算 | `fields=114 diff=[]` |
| T-D1 六计时字段 | `e2e=16e6 parts=16e6 held=3e6` |

**变异测试真有区分力**（5 个变异体，红绿可辨）：
- `M-A1`（破坏互斥）→ `T-A1` 变红（`sample: 1`），复原后 exit=0
- `M-B2`（破坏五态）→ `T-B1/T-B2/T-B3` 变红
- `M-C2`（破坏分段/缺测）→ `T-C1/T-C2/T-C2b/T-C3/T-C4` 变红，含 `$.n_zero_delta_runs: 1 != 3`

**★ 计时器硬件级发现（Lead 亲跑，追溯影响既有全部计时读数）**
```
QueryPerformanceFrequency = 10,000,000 Hz  => 100 ns/tick
perf_counter_ns 最小非零增量 = 100 ns
time.monotonic() 量化步长 ≈ 15.0–15.6 ms（GetTickCount64 系 64 Hz）
```
原驱动 `_run_hl_match.py` 全部计时用 `time.monotonic()`（`:342/:345/:347/:353-354/:357`）⇒
| 既有读数 | 原表述 | 准确表述 |
|---|---|---|
| `STALL_CAPTURE_FINAL.md:43` `cost= 16.00 ms` | 「16 ms」 | **恰一个量化步长**，真值 15–30 ms 之间，是量化值不是测量值 |
| 同处 `#1..#5 cost= 0.00 ms` | 「0 ms / 零开销」 | 真值 **< 15 ms**，**不是零** |
| `_hl_match_14412.json:16` `paused_ms: 0.0` | 「远低于 50 ms」 | 仅支持「**< 15 ms**」 |
| `STALL_CAPTURE_FINAL.md:66` `Δ中位=6 ⇒ 30.0 fps` | 「30 fps」 | 分母是名义 0.2 s，未含 15 ms 量化 ⇒ **不可作帧率引用** |

⇒ `SAMPLER_CONTRACT.md` 的「`paused_ms=0.0` 是低于测量精度、非零开销」现已有硬件依据；r2 改用 `perf_counter_ns()` 必要且正确。

**⚠ 必须留痕的失效**：RE-N01 第一版驱动候选件是**伪交付**——`difflib` ratio 0.9671，非相同块全在头部（13–56 行），第 57 行之后逐字相同，N7 循环仍 `sample(pid)`→判 only_tid。`run_monitor`/`NDJSON` 仅存在于 docstring。**任何"只跑作者自检器"的复核都发现不了**（自检器只覆盖采样器 58 项，不覆盖驱动层）。已记入 `RE-N01/FACT_CHECK.md` 与 `REVIEW/LEAD_INDEPENDENT_CHECKS.md` §L-9。

**RE-N01 交付完整清单**：`candidate/{_run_hl_match_candidate.py, e3_stack_sampler_candidate_r2.py, re_n01_monitor.py}`、`test_re_n01_offline.py`、`mutation_run.py`、`replay_re_n01.py`、`make_fixture.py`、`timer_calibration.py`、`make_diff.py`、`make_test_output.py`、`candidate.diff`、`raw/`（7 个 NDJSON 含 `derived_from_14412`）、`out/`（含 5 变异体）、`DIFF.md`、`FACT_CHECK.md`、`MUTATION_LOG.md`、`TIMER_CALIBRATION.md`、`SAMPLER_CONTRACT.md`、`TEST_REPORT.md`、`TEST_OUTPUT.txt`、`UNCOVERED.md`、`DISAGREE.md`。

**执行方自报的未闭合项（保留原话要点）**：零真机下真实 `SuspendThread`/`StackWalk64`/WOW64/50 ms 预算未验；0.2 s 轮询不能算逐帧 P95/P99、不覆盖 0.1–0.2 s 短停；`derived_from_14412.ndjson` 不含全量 3493 序列故不能重算该统计；`MF8-d` 在 `workspace-write`(47/1 红) 与 `danger-full-access`(58/0) 两读数并列、另一策略是否转绿本会话无法复现；r2 里 `ok` 态实际不可达，五态应理解为**契约取值域**（`DISAGREE.md` D8）。

### 2.3 RE-N02 · 帧/线程/状态语义 ✅（核心结论经 Lead 逐字节验证）

交付：`_frame_semantics_v2.py`、`PE_MAP.md`、`WRITE_POINTS.csv`（1009 行）、`FRAME_STATE_CONTRACT.md`（28,290 B）、`PRIOR_CLAIMS_REVIEW.md`、`UNKNOWNS.md`、`DISAGREE.md`、`EVIDENCE/`。

**`0xA8ED84`**：全文件 1009 处引用全在 `.text`；**10 个写点**（全 dword 直接写、非 RMW）：W01 `0x52DA08`、W02 `0x55DE81`、W03 `0x5B7329`(清零)、W04 `0x5BB20C`、W05 `0x5E550F`、W06 `0x5E747C`(清零)、W07 `0x68466B`、W08 `0x686765`、W09 `0x795234`(清零)、W10 `0x79758C`。

**★ 推进点已定位（Lead 逐字节验证）**：
```
0x0055DE73  mov edx, dword ptr [0xa8ed84]   ← 读
0x0055DE7E  inc edx                          ← 寄存器自增
0x0055DE81  mov dword ptr [0xa8ed84], edx    ← 回写
```
两个门控字节 `[0x41C0]`、`[0xA83D48]` 任一非零则跳过推进（`jne 0x55DEC8`）。

**`0xA8ED80`**：46 处引用**全 1 字节**（45 读 + 1 写 `0x7778CE`）；唯一写点前一条是 `setne al` ⇒ **是 0/1 布尔标志字节**。`0xA8ED88` 引用 0；`0xA8ED7C` 是独立 32 位字段。
⇒ **❌「32 位 tick」、❌ `G_TICK` 作语义依据、❌「帧号 = 渲染 FPS」三条命名全部停用。**

**线程**：静态下 `tid=30668` **只能称「窗口线程」**；升级为逻辑推进线程需运行证据（最小观测 5 步已写，`[待运行验证]`）。
**状态**：七态各一条独立判据，明确引用任务书 `:140` 的反循环约束，全部 `[待运行验证]`。

**撤销旧结论 8 条**（含「唯一写点」「推进机制不在 exe」「653 假阳性」实为错位解码伪影、「355 处 32 位读」等），收窄 3 条。

### 2.4 RE-N05 · 等待链静态回溯 ✅（决定性纠错，经 Lead 验证四跳）

交付：`MODULE_BINDING.md`、`WAIT_CHAIN.md`、`WAIT_HYPOTHESES.csv`(12 条)、`UNKNOWNS.md`、`DISAGREE.md`、`EVIDENCE/`。

**★ `ddraw+0x22B06` 不是 Blt，是 cnc-ddraw 的 `PeekMessageA` 钩子**（Lead 独立验证）：
```
gamemd RVA 0x13EB16  ff 15 84 14 7e 00   call dword ptr [0x7e1484]  → IAT = USER32!PeekMessageA
gamemd RVA 0x13EB1C  8b d8               mov ebx, eax   ← 栈中返回地址
ddraw  RVA 0x22B00   ff 15 68 3a 05 10   call dword ptr [0x10053a68]
ddraw  RVA 0x22B06   8b f0               mov esi, eax   ← 栈中返回地址
槽 0x10053A68 在 .data，初值 0x1002786A = jmp [0x1003e374]；ddraw IAT 仅 RVA 0x3E000+0x3F8 ⇒ 该槽非 IAT、非 COM vtable
.data RVA 0x53F08 起 hook 描述表（逐项 0x34 B）：…GetForegroundWindow / "PeekMessageA"@0x5400C / "GetMessageA"@0x54040 / …
```

**四个位置全部是返回地址，前一条调用分别是**：
| 位置 | 前一条调用 | 语义 |
|---|---|---|
| `gamemd+0x13EB1C` | `call [0x7E1484]` | `USER32!PeekMessageA`（非阻塞） |
| `ddraw+0x22B06` | `call [0x10053A68]` | cnc-ddraw `PeekMessageA` 钩子内部 |
| `gamemd+0x207F17` | `push 0x1E` + call | `KERNEL32!Sleep(30)`，有界轮询循环 |
| `gamemd+0x20833F` | `call ebx`（=`[0x7E14E4]`） | `USER32!EnumChildWindows(hWnd, 0x606800, 1)` |

**⇒ 必须作废**：`STALL_CAPTURE_SUCCESS.md:54-97`、`STALL_CAPTURE_FINAL.md:104-109` 的「Blt」定性及「两条独立根因」推论。
**⇒ 新最强运行假设**：`EnumChildWindows` 枚举子窗口 → 回调 `0x606800`（含 `0x607F17`）→ 回调内 `Sleep(30)` 有界轮询。若在帧推进线程上，每枚举一个子窗口睡 30 ms，可直接解释成规模卡顿。**未证**，交 RE-N06。

`0x4068E0` 实测为裸 `C3`（`ret`），在 W09/W10 与 `0x7778DA` 处被 call；运行期是否仍为 `ret` 未证（可能是 Detours hotpatch 占位）。

---

## 3 · 如何验证（可复制执行）

```powershell
cd D:\Project\ra2-campaign-forge

# RE-N00 基线（可重跑）                                          exit=0  已验
python -X utf8 lead\next_re_20261112\RE-N00\_baseline.py

# RE-N01 采样器自检（58 项）                                       exit=0  已验
python -X utf8 lead\next_re_20261112\RE-N01\candidate\e3_stack_sampler_candidate_r2.py --selftest

# RE-N01 离线测试（13 项）                                         exit=0  已验
python -X utf8 lead\next_re_20261112\RE-N01\test_re_n01_offline.py

# RE-N01 变异测试（5 变异体，红→绿）                                exit=0  已验
python -X utf8 lead\next_re_20261112\RE-N01\mutation_run.py

# RE-N01 离线重算（G4 闭环；注意是**位置参数**，不是 --ndjson）        exit=0  已验
python -X utf8 lead\next_re_20261112\RE-N01\replay_re_n01.py lead\next_re_20261112\RE-N01\raw\fixture_long_stall.ndjson
python -X utf8 lead\next_re_20261112\RE-N01\replay_re_n01.py lead\next_re_20261112\RE-N01\raw\derived_from_14412.ndjson

# RE-N02 静态复算（负控五样例）                                     exit=0  已验
python -X utf8 lead\next_re_20261112\RE-N02\_frame_semantics_v2.py --selftest

# RE-N05 证据脚本                                                  exit=0  已验
python -X utf8 lead\next_re_20261112\RE-N05\EVIDENCE\re_n05_step7.py
```

> ★ 上表 7 条命令由 Lead 于收尾时**逐条实跑**，退出码均为 **0**。
> 其中 `replay_re_n01.py` 吃**位置参数**（`--ndjson` 会报 `unrecognized arguments` 并 exit=2）。
> `replay_re_n01.py` 对 `derived_from_14412.ndjson` 会如实输出 `n_records: 5`、
> `provenance: derived_from_recorded_event`，**不冒充**可重算 3493 样本。

**独立复核（不复用作者自检器）**：`REVIEW/LEAD_INDEPENDENT_CHECKS.md` + `REVIEW/_lead_framefield_recheck.py`。

---

## 4 · 仍未证明的结论（不得当作事实引用）

1. **`0xA8ED84` 的更新节拍**（每帧 / tick / 逻辑步）与两个门控字节对应的状态 —— 纯静态不可定谳。
2. **「帧号停推 = 玩家看到的卡顿」** 未成立：停推可能只是门控跳过（见 §2.3）。
3. **`EnumChildWindows + Sleep(30)` 是否是卡顿根因** —— 未证是否在帧推进线程、门控条件未知。
4. **`.yrm` 载体是否就是当趟加载的地图** —— 只有名称+哈希强匹配，无运行期证据。
5. **`0x4068E0` 运行期是否仍为 `ret`**、IAT/钩子槽是否被 hook 安装器覆写。
6. **所有「栈证据」都是单次采样**，且采样本身挂起线程（对读数是高反身影响）。
7. **`paused_ms=0.0` 是低于计时精度，不是零开销** —— 且原驱动用 `time.monotonic()`，本机量化步长实测 **~15.0 ms** ⇒ 原驱动的 `16.00 ms` 恰一个量化步长、`0.00 ms` 实为 `<15 ms`（见 §2.2）。
8. **0.2 s 轮询不能计算逐帧 P95/P99**；短停（0.1–0.2 s）覆盖能力未验。
9. RE-N02 的 `explained 1009/1009` 是**有限静态搜索的解释率**，不是运行期全称证明；W01/W05/W09/W10 可达性未定。
10. **cosmetic**：`.detour` 段与 `ra2opt` 栈扩容使本镜像不能作「原版对照」基线。

---

## 5 · 下一张卡与唯一阻塞

### 下一张卡：**RE-N06（一步一变量的等待路径对照）** —— 但需先解除阻塞

**最优先的单一观测**（依 §2.4 新假设，一次只改一个变量）：
1. 真机进同一张图，**只读**以下 5 个值（不抓栈、不挂起）：
   - `[0xA8ED84]`（帧计数）
   - `[0x41C0]`、`[0xA83D48]`（两个门控字节）← **判定「停推是门控还是卡顿」的决定性观测**
   - `[0xA8ED84]` 变化时刻与 `0x607F17` 是否同线程（用 `GetThreadTimes` 而非挂起）
2. 若门控为 0 仍停推 ⇒ 转向 `EnumChildWindows`/`Sleep(30)` 路径；若门控非零 ⇒ 停推是**正常状态切换**，该伪故障关闭。

### 唯一阻塞：**真机 / 活进程授权口径冲突未裁**

- `lead/PENDING_DECISIONS.md:22-24`（D-13，2026-11-12）：真机发射 / 活进程采集**仍未授权**。
- 但四处回执称用户同日明示「统一真机以及一切操作，可以上传GitHub」：`WOW64_RECEIPT.md:4`、`RULING_RECEIPT_611.md:129`、`FRAMESOURCE_RECEIPT.md:4`、`e3_stack_sampler_candidate.py:1030`。
- **两者冲突未裁**。裁决提案已写好：`REVIEW/PENDING_DECISION_PROPOSAL_D32.md`（建议编号 D-32，未写入共享台账——本会话不执行 `git pull` 无法确认编号，且该文件有他人未提交改动）。
- ⇒ **本会话按「未授权」执行，全部真机项标 `[待运行验证]`。** 解除需用户明示。

---

## 6 · 本轮未做（如实）

- **零真机**：无任何运行期读数、无游戏内状态/画面证据。
- **RE-N03（地图与负载）未启动**：仅固定了载体候选哈希，未做进图计数、未做最小成功/失败对照图。
- **RE-N04 / N06 / N07 / N08 / N09 / N10（DLC）未启动**：本轮 P0 只到 N00/N01 + 两条静态线。
- `call_agy` / Gemini 3.8 Flash **配额耗尽**（`RESOURCE_EXHAUSTED`，约 149 h 后重置），RE-N05 改由 Hy4 子代理完成。
  ⇒ 目标里「经 call-agy(Gemini 3.8 Flash) 执行」这一条**本轮只部分满足**：agy 成功启动、读 8 个文件、
  写 1 个半成品后即被配额中断；**结论与交付由 Hy4 产出**，不是 Gemini 的产出。
- **RE-N01 文档不存在缺口**（更正 Lead 早前误述）：收尾核对 **27/27 交付物齐全**，
  `TEST_REPORT.md`、`UNCOVERED.md`、`DISAGREE.md` 均已落盘。

---

## 7 · 产物清单

```
lead/next_re_20261112/
├── HANDOFF.md                       ← 本文件
├── RE-N00/  BASELINE.json  INPUTS.tsv  CURRENT_FACTS.md  RECONSTRUCT.md  _baseline.py
├── RE-N01/  candidate/{_run_hl_match_candidate.py, e3_stack_sampler_candidate_r2.py, re_n01_monitor.py}
│            test_re_n01_offline.py  mutation_run.py  replay_re_n01.py  make_fixture.py
│            timer_calibration.py  candidate.diff  DIFF.md  SAMPLER_CONTRACT.md
│            FACT_CHECK.md  MUTATION_LOG.md  TIMER_CALIBRATION.md  TEST_OUTPUT.txt
│            raw/  out/  (含 5 个变异体目录)
├── RE-N02/  _frame_semantics_v2.py  PE_MAP.md  WRITE_POINTS.csv  FRAME_STATE_CONTRACT.md
│            PRIOR_CLAIMS_REVIEW.md  UNKNOWNS.md  DISAGREE.md  EVIDENCE/
├── RE-N05/  MODULE_BINDING.md  WAIT_CHAIN.md  WAIT_HYPOTHESES.csv  UNKNOWNS.md  DISAGREE.md  EVIDENCE/
└── REVIEW/  LEAD_INDEPENDENT_CHECKS.md  _lead_framefield_recheck.py
             PENDING_DECISION_PROPOSAL_D32.md  _n05_prompt.md  agy_n05_handoff.md
```

**本轮未提交 git**（仓库有他人 290+ 条未提交改动，按纪律不做写操作）。提交由归属会话按其授权办理。
