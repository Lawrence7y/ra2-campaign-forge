# TASK · D-26 后续 · D-13 先补离线件（真实对局停滞事件的定义与识别）

**派发**：2026-11-06 15:2x，总控会话。**模型**：`magpie/antigravity/gemini-3.8-flash$high`（实际 `magpie/antigravity/gemini-3.8-flash$high`）。**max_concurrency=2**。
**授权依据**：**D-26 裁决书**（`lead/d26_ruling_20261106/RULING_D26.md`）第 1 节末段「**先补项目**为：在既有离线语料中定义并识别真实对局目标事件，明确性能量及长停代表范围，排除结束态和合法冻结混淆；提交触发延迟、采样扰动、栈解析、停止及回退设计」。
**唯一写域**：`lead/stall_event_def_20261106/`（新建目录，只写此目录内的新文件）。

---

## 0 这条为什么存在

D-13（E3 栈采样）被裁 **PAUSE**，理由不是「不重要」，而是**前提没立住**：

- 「29 个冻结窗 = 对局内停滞」**这个前提已被撤销**（`PENDING_DECISIONS.md:23-25`）——那些窗是对局已结束态；
- 全量 1734 个停滞段中 **87.7% 是 0.1–0.2s 短停**，而 MiniDump 自身停顿数百 ms–秒，**物理上采不到短停主体**；
- 「N=1.0s 误触率 0」只是**历史指定语料内**的记载，**不能证明剩余长停是有效的真实对局目标事件**。

裁决书要求：**先在既有离线语料里把「什么才算真实对局内的停滞」定义清楚并能识别出来**，再谈采样。
**你的任务就是这一件，且只这一件。**

## 1 严禁事项（越界即废）

**★ 本任务零采样代码、零真机。** 具体禁止：
- 不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入；
- 不启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，不读活进程内存；
- **不设计也不编写任何采样实现**（裁决书明写「不授权编写或执行任何采样候选」）；
- 不 commit、不 push。

**你要交的是「定义 + 识别 + 证据」，不是「怎么采」。**

## 2 可用语料（全部只读）

| 语料 | 位置 | 规模 |
|:--|:--|:--|
| `measure_w*.json` | `lead/**/measure_w*.json`（多处） | **138 份** |
| 既有探针脚本 | `lead/goal3t_nightwatch_20261102/_*.py` | 50+ 个 |
| 停滞结构分析 | `lead/goal3t_nightwatch_20261102/STALL_TIMESTRUCTURE_20261103.md` + `STALL_VS_GAP_20261103.md` | — |
| 冻结起始 | 同目录 `FREEZE_ONSET_20261103.md` | — |
| 口径普查 | 同目录 `OCC_CENSUS_20261103.md` + `OCC_CENSUS_XVERIFY_20261103.md` | — |
| 相位重算（**有 bug，见 §3**） | 同目录 `_phase_recompute.py` + `PHASE_BY_BOOT_20261104.md` | — |
| E3 原方案 | `lead/codex_round_20261030/LEADER_battle/E3_SAMPLING_PLAN_REVIEWABLE.md` | 6,268 B |
| E3 主卡 | `lead/goal3t_nightwatch_20261102/E3_FOR_GOAL1_CARD_20261103.md` | 7,207 B |
| 双口径数据 | `PHASE_BY_BOOT_20261104.md`（**注意 §3 的 bug**） | — |

**★ 先自己 `find` / `ls` 核一遍上表路径，不存在就报「未找到」，不许照抄本文。**

## 3 ★ 一个已知的统计 bug（本任务必须正确处理）

`lead/goal3t_nightwatch_20261102/_phase_recompute.py` 有缺陷，D-26 裁决已认定：

- `:189` 把 `nan` 也 append 进结果；
- `:195-196` 用 `len()` 当「可算数量」，把 nan 算进去了；
- `:197` 取 `sorted()[len//2]`，**既没过滤 nan，也没对偶数样本取中央两项均值**。

**后果**：`PHASE_BY_BOOT_20261104.md:71` 写的「可算 8 个 BOOT，中位 +0.4472」是错的。
实际：8 行里有 **2 个 nan**，只有 **6 个有限值**，其中位数是 **−0.34305**（不是 +0.4472）。

**你要做的事**：在本任务里**如果要算任何中位数/相关，必须先显式处理 nan**，
并在交付件里写明「样本数 = 有限值个数，nan 已排除，偶数取中央两项均值」。
**不许再犯同一个错。**

## 4 交付物（全部写进 `lead/stall_event_def_20261106/`）

### 4.1 `STALL_EVENT_DEFINITION.md` —— 主交付

必须回答五个问题，每个都要有语料证据：

**Q1「真实对局内的停滞」的可操作定义是什么？**
- 给出**判定式**（用哪些字段、什么阈值、什么时序关系）；
- 必须**能与「对局已结束」区分开**（这是 29 窗错误的根源）；
- 必须**能与「合法冻结」区分开**（例如过场、暂停、加载、菜单）。

**Q2 在既有语料里，这个定义能识别出多少个事件？**
- 逐趟列出：趟名 / 窗数 / 识别到的事件数 / 时长分布；
- **必须做负控**：拿已确认的「对局已结束」窗去跑同一个定义，**应当识别不出来**（若识别出来，说明定义有假阳性）。

**Q3 长停（≥1s）在真实对局事件里占多少？短停（0.1–0.2s）占多少？**
- 给出**双口径**（64 moving / 97 全量）下的分布，**逐项标明窗口集与 n**；
- 明确回答：**≥1s 长停是否足以代表目标现象**？（这是 D-13 选 A 的关键前提）

**Q4 现有语料够不够支撑这个定义？**
- 列出**缺什么**：缺哪类趟、缺哪个字段、缺哪种状态标注；
- 每条缺失都要说明「补它需要什么」（不写怎么采，只写需要什么数据）。

**Q5 若定义成立，触发延迟/采样扰动/栈解析/停止与回退这四项的设计要求是什么？**
- **只写要求，不写实现**：例如「触发延迟必须 < X ms，因为短停只有 Y ms」；
- **不写任何采样代码**，不选 SDK/API。

### 4.2 `STALL_EVENTS.json`

机器可读：每个识别到的事件一行：
```json
{
  "trip": "str", "window": "w0|w1|w2",
  "startTick": 0, "endTick": 0, "durationMs": 0.0,
  "windowSet": "moving64|full97",
  "isRealMatch": true, "exclusionReason": null,
  "evidence": "文件:行 或 字段路径"
}
```

### 4.3 `_stall_probe.py` + `_stall_probe_out.txt`

**你自己写的**识别脚本与**真实输出**。
- 必须**真跑**，不许手写结论；
- 必须显式打印「排除的窗及理由」「nan 处理方式」「样本 n」。

### 4.4 `review/STALL_EVENT_DEF_REVIEW.md`

独立复核（见 §6）。

## 5 硬性纪律

1. **零真机、零采样代码**（见 §1，越界即废）。
2. **只读**：`ra2youli/**`、`out/re_work/**`、`lead/re_line_20261105/**`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md`、`lead/goal3t_nightwatch_*/**` 一律不改。
3. `python -I -X utf8`，绝对路径。
4. 引用追到「文件:行」或「实跑输出」；拿不到写「未验」。
5. **★ 任何统计必须显式报 n，并显式说明 nan / 缺失值怎么处理。**
6. **★ 不许把「我认为应该这样」写成「语料显示这样」。**

## 6 独立复核（必做）

新上下文复核员，逐项做：
- 亲自重跑 `_stall_probe.py`，核输出与 `_stall_probe_out.txt` 一致；
- **专项 A**：Q2 的负控是否真做且真通过（拿「对局已结束」窗去跑，应当识别不出来）；
- **专项 B**：所有统计是否都报了 n，且 nan 处理方式明确；
- **专项 C**：有没有偷偷写采样实现（关键词扫描 hook/MiniDump/SuspendThread/StackWalk/ctypes/ReadProcessMemory）；
- **专项 D**：有没有把「未验」写成「已证」。

复核件必须含 `subjectSha256` / `subjectBytes` / `checkedEveryRow` / `negativeControlPassed` / `noSamplingCode`。

## 7 确定性门禁

写 `check_stall_def.py`，`python -I -X utf8` 跑，检查：
- 主交付存在，且含五个 Q 的小节标题（Q1..Q5）；
- `STALL_EVENTS.json` 可解析、是数组、非空，每条含 9 个字段；
- `_stall_probe.py` 与 `_stall_probe_out.txt` 都存在且非空；
- 主交付里出现「负控」或「negative control」字样，且给出排除的窗数；
- 主交付里每个统计段落都出现 `n=` 或「样本」字样；
- **反扫描**：`_stall_probe.py` 里**不得**出现 `ctypes` / `ReadProcessMemory` / `MiniDump` / `SuspendThread` / `StackWalk` / `SetWindowsHook`;
- 复核件含 `checkedEveryRow: true`、`negativeControlPassed: true`、`noSamplingCode: true`。

退出码 0 = PASS。**exitCode 与完整输出写进交付说明。**
