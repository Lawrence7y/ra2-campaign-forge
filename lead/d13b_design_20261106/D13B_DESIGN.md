# D-13b 主设计 · 面向当前保留短停样本的离线观测方案（零采样实现）

**本文是什么**：D-27 §0 定谳 `main: B` 所立 D-13b 的**离线方案设计**主文书（`lead/d27_ruling_20261106/RULING_D27.md:6-8`）。授权上限仅为「离线设计 + 获准读取的既有离线材料分析 + 纯模型/合成数据单测」（`RULING_D27.md:32`）；**不编写真实采样候选、不执行采样、不用「单测」包装任何采样 API 调用**（`RULING_D27.md:32-34`）。唯一写域 `lead/d13b_design_20261106/`（`lead/d13b_design_20261106/TASK.md:7`；D-27 §3 的写域由本任务另行指定）。本文作者只负责本主设计文件；`BUDGET_MODEL.json` / `_state_machine.py` / `_test_state_machine.py` / `_test_out.txt` 为同批交付件，本文只引用、不改写、不宣称替它们复核。

**本文不是什么**：不是采样实现、不是真机/活进程方案、不是可行性已通过的证明、不是「短停可被捕获」的结论。`RULING_D27.md:68` 明确不预承诺离线通过后放行；`:69` 不背书未执行的门禁/单测/核验已通过。

---

**结论先行（读者据此判断「这条离线路线值不值得继续」）**

**值得继续，但只能作为「有界的可行性论证 + 语义缺口挂账」，不能作为「短停捕获方案可实现」的证明。**

- 本次会话**已实跑闭合**的：预算表自洽、六类场景的纯逻辑处置、状态机 43 条断言 `PASS=43 FAIL=0`、两个 `.py` 反扫描零命中、既有语料覆盖分桶复算、口径与标记诚实自检。这些证明的是**逻辑模型自洽**，不是真实系统表现。
- **本次结构上达不到**的：完整时间预算合计 `152.50ms ≥` 中位 `129.93ms`（超 `22.57ms`）。**在当前假设下达不到**「在中位短停内拿到快照」。更根本的是，段② `100ms` 是口径 B 的硬累积门槛、不可压缩，而 `STALL_EVENT_DEFINITION.md:191` 自身判定「任何累积判定耗时 ≥100ms 的触发机制均属不合格」——按现门槛，触发机制**在定义上已不合格**。这不是调参能修的，需要改触发范式（前馈/预测式）或另立裁决；本 D-13b **未获授权亦不背书**。
- 系统时延 / 扰动 / 资源释放 / 真实栈可解析性四项，按 `RULING_D27.md:42` 属「不能凭离线资料验证」，且本阶段零真机、零采样实现，一律 **[未验]**。缺的不是编码工作量，而是**未授权的真机实测与新裁决**。
- 若读者的判定标准是「证明短停捕获可达」，本阶段诚实答案是 **达不到**；若标准是「把设计写到可被证据审、把未验逐项挂账、把逻辑模型跑通」，则本路线已交付可审对象，值得按此有界目标继续。

**口径与措辞纪律（三条裁决更正，写错即废；`TASK.md:50-55`、`RULING_D27.md:44`、`:48`）**

1. 绝不写「长停不存在」。全文统一表述：**「当前 97 窗按现规则保留的事件中未识别到 ≥1s 平台，语义漏检及跨场景代表性未闭合」**（`RULING_D27.md:52`、`:64`）。
2. 绝不把「停顿 >1s 即确认终局」当结束态真值。`>1s` 在本文只作 **[保守停止预算]**（停止继续投入观测，只会少采，不会把长停误判为不存在），**不得当语义判据**（`RULING_D27.md:44`、`TASK.md:53`、`:66`）。本文所有输出 `semantic_truth_written` 恒为 `False`。
3. `n=1681`（保留标签数）与 `n=1737`（full97 全部候选，含 56 个 false）**不是同口径，不得直接对照**（`RULING_D27.md:48`）。本文凡用到 `1681` 的分母一律限定在同一保留标签集合内。

既有事实（不自行重算，只引用；`RULING_D27.md:12`）：候选平台 1737 / 保留标签 1681 / 排除 56；保留事件中 `>=1s` = 0；最长 `566.96ms`；中位 `129.93ms`；`100-200ms` 1520 条（90.42%）；`200-500ms` 158 条；`500-1000ms` 3 条。其中 `true` 是**分类器保留标签，不等同已独立证明的真实对局语义**（`RULING_D27.md:12`）。

---

## 1 完整时间预算

D-27 §4 要求「从事件起点、100ms 阈值累积、轮询/调度到拟定捕获时刻的**完整预算**，不能只报告『检测后 <50ms』」（`RULING_D27.md:42`）。逐段预算表如下（机器可读版 `lead/d13b_design_20261106/BUDGET_MODEL.json`，本次实读全文 `BUDGET_MODEL.json:1-35`）：

| 段 | 内容 | 耗时 | 性质 | 依据（`文件:行` / 实跑） | 是否可离线验证 |
|:--|:--|--:|:--|:--|:--|
| ① 事件起点 | 停滞开始 → 首次被观察到 | `2.50ms` | **[估算]** 乐观下界代理 | 题给《预算模型》段①所载前序实跑：`python -I -X utf8` 复算 97 窗 `samples.t` 的 1121892 个相邻间隔 → dt 中位 `2.4960ms`，取 `2.50ms`；`FREEZE_ONSET_20261103.md:18`、`:93` 记引擎满速突然停住、无减速预兆，无可提前预警量。见 `BUDGET_MODEL.json:5-7`。★ 该 dt 复算**非本文作者本次会话重跑**，本文只引用该交付件所载依据 | **否**（真实在线首次观察延迟 [未验]） |
| ② 阈值累积 | 首次观察恒帧 → 达到 `100ms` 判定门槛 | `100.00ms` | 口径 B **定义值**，硬下限，不可写 0、不可压缩 | `lead/stall_event_def_20261106/_stall_probe.py:28`（`T_DEFAULT=0.100`）、`:100`（`if dur >= thr`）、`:86-105`（`dur=ts[j]-ts[i]`）；`STALL_EVENT_DEFINITION.md:31`；`RULING_D27.md:16`（「d>=0.100s 只是下限」）。本次实跑 `STALL_EVENTS.json`：`min durationMs=100.0`、`<100` 为 0 条 | **是**（已在既有离线语料完全复算） |
| ③ 轮询/调度 | 判定成立 → 发出捕获指令 | `48.00ms` | **[估算] [待论证指标]** 对名义值的工程拆分 | `STALL_EVENT_DEFINITION.md:190`（端到端 `<50ms`、安全裕量 `≤20ms`）、`:200`（在线抓取 `≤2ms` 归④）、`:201`（目标线程定位）；`50 - 2 = 48`。文档未单列该段，`RULING_D27.md:42`、`:67` 明列系统时延未验/不背书 | **否** |
| ④ 捕获执行 | 指令 → 拿到快照 | `2.00ms` | **[估算] [待论证指标]** 设计指标，非实测 | `STALL_EVENT_DEFINITION.md:200`（在线仅抓原始寄存器上下文 + 微型内存页，限时 `≤2ms`，符号反解/栈回溯全部离线）、`:199`（实时符号解析几十至数百毫秒须离线）；`RULING_D27.md:44`、`:67` 不背书 | **否** |
| **合计** | | **`152.50ms`** | **[估算] + [待论证指标]** | `2.50 + 100.00 + 48.00 + 2.00 = 152.50`；`BUDGET_MODEL.json:32-34` | ①③④ 不可离线验证 |

**本次会话实跑核验（输出节选；完整精确命令与输出见 `## 3 纯模型单测` 命令 2）**

命令 2 为 `python -I -X utf8 - <<'PY' … PY`（隔离模式、UTF-8、绝对路径读取 `BUDGET_MODEL.json`；脚本体与全量输出逐字列于 §3）。其预算相关段输出：

```
=== BUDGET_MODEL.json ===
  event_onset        ms=  2.50 offlineVerifiable=False
  threshold_accum    ms=100.00 offlineVerifiable=True
  poll_dispatch      ms= 48.00 offlineVerifiable=False
  capture_exec       ms=  2.00 offlineVerifiable=False
  segments sum = 152.50 ; totalMs = 152.50 ; equal = True
  meetsMedian = False ; 152.5 < 129.93 = False ; gap = 22.57ms
  zero/neg segments = 0
```

⇒ 各段之和 `152.50 == totalMs 152.50`（自洽）；**没有任何一段被写成 0 或负数**（`zero/neg segments = 0`），遵守 `TASK.md:87`「不许为了好看而把某一段写成 0」。

**totalMs 是否 < 129.93？——否。**

`152.50ms ≥ 129.93ms`，超出 `22.57ms`；`BUDGET_MODEL.json:33` 记 `meetsMedian=false`。`129.93ms` 是 1681 个**保留标签事件**的时长中位（`RULING_D27.md:12`）；与 1737 个 full97 全部候选**不是同口径，不得直接对照**（`RULING_D27.md:48`）。

> **在当前假设下达不到**「在中位短停内拿到快照」。这不是口径 trick，也不是把某段乐观化就能绕过的：②=100ms 是判定门槛的定义值，不改动判定口径就不可压缩。

**需要什么条件才可能达到（逐条，全部 [未验] / [待论证指标]）**

结构上，`152.50 = 100（②） + 52.50（①③④）`；要在 `129.93ms` 内拿到快照，需 **①+③+④ < 29.93ms**（当前 `52.50ms`，至少再砍 `22.57ms`）。若把 ①=2.50ms 视为不可再压的乐观下界，则 **③+④ 需 < 27.43ms**（当前 `50.00ms`）。须同时满足：

- **(a)** ③+④ 端到端不能取 `:190` 的名义上界 `50ms`，须兑现 `≤20ms` 安全裕量甚至更低。即便乐观取 ③+④=`20ms`，合计仍 `= 2.5 + 100 + 20 = 122.5ms`，余量仅 `7.43ms`，且依赖全部 [未验] 项取最优、真实系统时延零增长 —— **不可保证** [待论证指标]。
- **(b)** `STALL_EVENT_DEFINITION.md:190` 的 `<50ms`/`≤20ms`、`:195` 扰动 `<10ms`、`:200` 在线 `≤2ms`、`:206` 配额/冷却、`:207` `>1s Disarm`、`:208` `100ms` 清理/rc=0 全为 **[待论证指标]**；`RULING_D27.md:67` 明确不背书、`STALL_EVENT_DEFINITION.md:218` 记「完全未验」，须有真机实测证明真实运行上界成立。
- **(c)** `RULING_D27.md:42` 四项未验 —— 系统调度时延、扰动、资源释放、真实栈可解析性 —— 须逐项闭合（详见 `## 4 未验`，本阶段结构上无法闭合）。
- **(d)** ① 的真实在线首次观察延迟、`:201` 目标线程精准定位须实测不引入额外增长。
- **(e) 结构性冲突**：`STALL_EVENT_DEFINITION.md:191` 自身判定「任何累积判定耗时 `>=100ms` 的触发机制均属不合格」。按现 `100ms` 门槛，触发机制**在定义上已不合格**；本文只记录该矛盾，**不擅自改判定口径**。
- **另一条可能出路**：把 `100ms` 累积门槛改为前馈/预测式触发（不待累积满 100ms 即捕获）。但这会引入假阳性、与 `STALL_EVENT_DEFINITION.md:31`、`:191` 冲突，**需另有有效裁决授权**；本 D-13b 未获授权亦不背书（`BUDGET_MODEL.json:34`）。

**预算的定位声明**：本模型是**端到端时间预算（保守捕获/停止预算）**，**不是结束态语义真值**。`>1s` 只可作保守停止预算，不得当终局真值（`RULING_D27.md:44`、`TASK.md:53`），否则会再次排除待研究长停。预算命中后的停止只影响「是否继续投入观测」，绝不写入「该停滞已结束/不存在」。正确表述见开篇第 1 条。

---

## 2 剩余覆盖检验

**先立两个不同的「覆盖」，避免踩口径更正（`RULING_D27.md:48`）**

| 概念 | 数值 | 性质 | 出处 |
|:--|:--|:--|:--|
| 识别 / 保留标签覆盖 | 1681 条（`isRealMatch=true`），其中 `100-200ms` = 1520 | 现分类器**保留标签数**，条件统计，不等同独立证明的对局语义 | `RULING_D27.md:12`；本次实跑复核一致 |
| 捕获时间可达覆盖 | `503/1681 = 29.92%`（主战场 `342/1520 = 22.50%`） | 纯模型在**假定预算**下回放的**条件上界** **[估算] [待论证指标]**，**非实测捕获成功率** | 本次实跑，命令见 §3 |

- 时间可达覆盖以 `BUDGET_MODEL.json` 的 `totalMs=152.5` 为分界；`152.5ms` 整体是 **[估算]+[待论证指标]**，其中 ①③④ 的真实系统时延/扰动/资源释放/栈可解析性一律 **[未验]**（`RULING_D27.md:42`、`:44`、`:67`；`STALL_EVENT_DEFINITION.md:216-219`）。故下文任何「可达 N 条」都是**条件上界**，真实捕获覆盖 **[未验]**。
- `>1s` 全程只作**保守停止预算**（Disarm 观测动作，只会少采，不会把长停误判为不存在），**不得当结束态语义真值**（`RULING_D27.md:44`、`TASK.md:53`）。
- 既有语料细节（窗边界、manifest、回滚、字段巡检）来自题给《覆盖分析》前序实跑输出；`STALL_EVENTS.json` 的分桶数字由本次会话独立实跑复核（§3）。两者均不重算既有事实本身。

**场景一 · 100–200ms 平台（1520 条，主战场）**

- 实况（本次实跑）：`100<=d<200 = 1520`、`200-500 = 158`、`500-1000 = 3`、`>=1000 = 0`；`min=100.00`、`median=129.93`、`max=566.96`；与 `RULING_D27.md:12` 一致（属对照，不构成对裁决的复核结论）。题给《覆盖分析》§1 另从 `evidence.pos=` （`_stall_probe.py:235` 写入格式）解析得 1520 条中 `MID 1515 / FIRST 3 / LAST 2`。
- 本次实跑灵敏度：`durs>=100.00 → 1681`、`durs>=129.93 → 841`、`durs>=152.50 → 503 (29.923%)`、`durs>=200 → 161`；主战场内 `d<152.5` = **1178 条**、`d>=152.5` = **342 条（22.50%）**。
- 处置：不以时长短丢弃任何候选；`MIN_PLATFORM_MS=100` 只作**候选入队门槛**，不作「值得捕获」的筛子。110ms 的 MID 平台照样进状态机（合成 S1 PASS，`_test_out.txt:52`）。捕获可达性单列 `time_reachable: bool` + `budget_B_ms: 152.5 [估算][待论证指标]`，与语义标签分离。
- **结论：按现假定预算，结构上够不到主战场的大多数** —— `1178/1520（77.50%）` 在名义捕获时刻之前已结束，全体 true 有 `1178/1681（70.08%）` 不可达；时间可达上界 `342/1520 = 22.50%`（全体 `503/1681 = 29.92%`）**[估算] [待论证指标]**，真实捕获覆盖 **[未验]**。根因是 ②=100ms 硬门槛（`_stall_probe.py:28`、`:100`；`STALL_EVENT_DEFINITION.md:31`）。出路见 §1 (a)-(e)，均不获本 D-13b 授权、不背书。

**场景二 · 窗末截断（事件跨窗）**

- 实况（题给《覆盖分析》§2）：全体 true 中 `pos=FIRST 4 / LAST 2`（`_stall_probe.py:97-104` 定义 WHOLE/FIRST/LAST/MID）；60 对相邻窗边界间隔实跑 `median=20.62ms`、`>=50ms` 14 对、`>=100ms` 3 对、`max=247.79ms`。具体样本 `l3_20261031hb w1` LAST（`dur=139.78ms, f=725`）→ `w2` FIRST（`dur=101.98ms, f=726`），窗间空洞 `121.54ms`、帧号 `+1`，两侧窗口样本全为各自单一帧值 —— **帧值不同、中间有观测空洞，不是同一条连续同帧平台**。
- 处置：**不拼接、不跨窗合并、不外推总时长**。窗内可见跨度 `d = ts[j]-ts[i]` 一律标为**下界** **[估算]**，附 `BOUNDARY_TRUNCATED` 标记与窗间间隔实测值。位置标签 `WHOLE/FIRST/LAST` 只作**截断标志**，不作结束态语义判据 —— 这是与 `_stall_probe.py:211-224` 的关键差异（那里把 LAST 直接送去判 `match_ended_terminal_freeze`）。去重键 `(trip, window, startTick, f_val)`：同一停滞在相邻窗被两次观察到时**不重复计数**，但也**不伪造为一条更长的平台**；疑似同源另出 `possibly_same_event` 且状态标 [未验]，交独立核验，不进入覆盖分子。
- **结论：6 条边界候选保留但标下界，不计入「完整时长」分子**；跨窗同源性 **[未验]**。合成 S2（跨窗 LAST→FIRST 分别得 `REAL_CANDIDATE` / `BOUNDARY_TRUNCATED`）PASS。

**场景三 · 全窗后恢复（整窗冻结，下一窗/后续窗恢复）—— 必须避开的两个缺陷**

- 实况（题给《覆盖分析》§3）：`STALL_EVENTS.json` 中整窗排除 33 行（`whole_window_frozen_match_ended 32` + `whole_window_loading_blank_f0 1`），逐行检查 **33/33 在同趟内均无任何后续推进窗**；`match_ended_terminal_freeze` 18 行中下一窗存在 15（**15 个仍全窗冻结，恢复 0**）、缺失 3。manifest 97 窗 / 37 趟，逐趟最大窗号 `{0:7, 2:30}`，**全库不存在 w3 及以后任何窗** ⇒ 「w2 冻结后下一窗恢复」在本语料里**结构上不可观测**。
- 代码缺陷对照（本次实读 `lead/stall_event_def_20261106/_stall_probe.py:165-189`、`:211-224`）：`:169-189` 整窗无推进即**无条件** `isRealMatch=False` 并 `continue`（`:189`），完全不看后续窗；`:211-224` 只查 `w_{i+1}` 一个窗，`resumed=False` 即判 `match_ended_terminal_freeze`（`:223-224`）。D-27 已认定其为循环式语义论证与选择偏差（`RULING_D27.md:18`）。
- 处置：整窗恒帧 → 先入 `QUARANTINED`（待定），**绝不判 false、绝不 continue 丢弃**；扫描同趟**全部**后续窗（不限紧邻一窗），只要任一窗出现帧推进即 **retro-upgrade 为 `RECOVERED`**。若受限于已录视野内未观察到恢复 → 输出 `UNKNOWN`（**数据不足**），**不写「终局」「不存在」「已证非真实停滞」** —— 未观察到 ≠ 不存在。恒帧时长事实与排除标签**分开保留**：53 条 `>=1s` 候选按 `32/15/4/1/1` 分组（`RULING_D27.md:14`），表述为「**>=1s 恒帧候选平台，当前规则排除出真实对局事件集；排除原因标签如下，独立状态语义未全量核验**」（`RULING_D27.md:48`）。`d>1s` 仅触发 `budget_disarm_conservative`，`semantic_truth_written=False`。
- **结论：真实语料中未观察到恢复（≠ 已证终局）**；retro-upgrade 能力由合成 S3（w0 冻结、w1 冻结、w2 才恢复，w0/w1 均被 retro-upgrade；旧缺陷会把 w1 判成终局冻结）验证 PASS，**恢复态 / 结束态语义真值 [未验]**。

**场景四 · 缺窗（中间少一个窗）**

- 实况（题给《覆盖分析》§4）：manifest 97 窗 / 37 趟，**编号不连续对数 = 0**（每趟 `w0..w2` 或仅 `w0`）⇒ 「缺窗」在既有真实语料中**不出现，纯合成场景**。另存在一处**时间非单调**：`(root) w0→w1` 间隔 `-11754677.64ms`、帧 `3950→373`（Δ=-3577），属时钟/帧号复位异常，不是可桥接的空洞。
- 处置：同时以「窗号不连续」+「时间戳单调性」检洞；命中则两侧窗一律 `BOUNDARY_TRUNCATED` / `UNKNOWN`。**不桥接、不插值、不推断跨洞事件仍在持续**；输出 `gap_detected: true` + 缺失窗号 + 「跨洞事件状态 [未验]」，该段不计入任何覆盖分子。时间倒退（Δt<0）不按缺窗处理，转 `REWIND_SUSPECT`（见场景五）并单列 `clock_reset_suspect`。`l3_20261031hb w1→w2` 的 `121.54ms` 窗间空洞虽非「缺窗」，同样按「观测空洞 [未验]」处理。
- **结论：真实语料 0 例（纯合成场景）**；合成 S4（`w0→w2` 识别 `gaps=[(0,2)]`，两侧 `BOUNDARY_TRUNCATED`）PASS；**跨洞状态 [未验]**。

**场景五 · 回滚（frame_rewind）**

- 实况（题给《覆盖分析》§5）：全库仅 1 条 `frame_rewind_anomaly`（`l1_20261023e4 / w1`，`startTick=1848, endTick=4632, dur=5569.08ms`，窗内帧号下降恰 1 次 `3668→0`）；跨窗帧号下降另 1 处（`(root) w0→w1`，`3950→373`）。旧检测在 `_stall_probe.py:200-202`（MID）与 `:206-208`（FIRST）：`fs[e_i+1] < f_val` → `frame_rewind_anomaly`、`isRealMatch=False`（本次实读 `:196-210` 确认）。
- 处置：任意帧号下降（窗内或跨窗）→ `REWIND_SUSPECT`，**隔离但不销毁**：保留 `startTick/endTick/durationMs/f_val` 原始事实，标为「时钟复位异常候选」，**不并入真实对局候选集、不折算成更长的停滞、不推断「不存在」**。与旧代码的差别：旧路径把 `isRealMatch=False` 当终局结论；本设计 quarantine 后交独立状态核验（截图/结束/加载态 **未全量核验**，`RULING_D27.md:14`），状态标 [未验]。
- **结论：2 处均隔离挂账、不计入覆盖分子**；合成 S5（帧 `100..139` 后归 0 判 `REWIND_SUSPECT`）PASS；**独立状态语义核验 [未验]**。

**场景六 · 未知状态（数据不足）**

- 实况（题给《覆盖分析》§6，104 个 `measure_*.json` 全量字段巡检）：`verdict` 取值 `{'ok':89, 'no_advance':12, 'frame_wait_timeout':3}` ⇒ **15 个非 ok**；`gate.units0` 为 `None` 出现在 **5 个文件**；无 `t`/`f` 缺失、无长度不匹配、无 NaN。视野内未观察到恢复（§3）、跨洞（§4）、时钟复位（§5）亦归入本类。
- 处置：命中任一条件即输出**一等公民** `UNKNOWN` + 显式 `reason_code`（`frames is None / n<2 / verdict != 'ok' / units0 is None / Δt<0 / NaN in t / frame decrease / recovery_not_observed_within_horizon`）。`UNKNOWN` **必须单独计数并上报**，不得静默丢弃、不得折叠成 `false`、不得写成「无事件」或「不存在」；覆盖报表中与 `REAL_CANDIDATE` / `QUARANTINED` / `REWIND_SUSPECT` / `BOUNDARY_TRUNCATED` **并列分行**。「>1s 只作保守停止预算」断言亦列入单测并 PASS。
- **结论：全部 15+5 条保留为 `UNKNOWN`，0 条被写成 false/不存在**；合成 S6（`frames=None, verdict=frame_wait_timeout, units0=None` → `UNKNOWN`）PASS。

**六类场景覆盖汇总（并表）**

| # | 场景 | 既有语料实况 | 本方案处置 | 时间可达 / 覆盖结论 |
|:--|:--|:--|:--|:--|
| 1 | 100–200ms 平台 | 1520 条（MID 1515 / FIRST 3 / LAST 2）；`d<152.5` 1178 条 | 全量入队、不因短丢弃；`time_reachable` 单列 | **342/1520 = 22.50%**（全体 `503/1681 = 29.92%`）**[估算][待论证指标]**；真实捕获覆盖 **[未验]** |
| 2 | 窗末截断 | FIRST 4 / LAST 2；60 对边界 14 对 `≥50ms`、3 对 `≥100ms`、max `247.79ms` | 不拼接；时长为下界；`BOUNDARY_TRUNCATED`；去重不重复计数 | 6 条边界候选**保留但标下界**，不计入「完整时长」分子；跨窗同源 **[未验]** |
| 3 | 全窗后恢复 | 33 整窗排除行 **0 个**有后续推进窗；18 terminal_freeze 中下一窗存在 15（全冻结）、缺失 3；全库无 w3+ | QUARANTINED → 扫**全部**后续窗 → RECOVERED / UNKNOWN；`>1s` 仅保守停止预算 | 真实语料中**未观察到恢复**（≠ 已证终局）；retro-upgrade 能力合成 S3 PASS；恢复态真值 **[未验]** |
| 4 | 缺窗 | manifest 97 窗 / 37 趟，**编号缺口 0 对**；1 处时间非单调 `(root) w0→w1` | 检洞 → 两侧 `BOUNDARY_TRUNCATED`/`UNKNOWN`；不桥接不插值 | 真实语料 **0 例**（纯合成）；合成 S4 PASS；跨洞状态 **[未验]** |
| 5 | 回滚 | 1 条 `frame_rewind_anomaly` + 1 处跨窗帧降 | `REWIND_SUSPECT` 隔离、保留原始事实、不并入真实候选 | 2 处**隔离挂账**、不计入覆盖分子；独立状态核验 **[未验]** |
| 6 | 未知状态 | 15 个非 `ok` verdict；5 个 `units0=None` | `UNKNOWN` 一等输出 + `reason_code`，单独计数上报 | **15+5 条全部保留为 UNKNOWN**，0 条写成 false/不存在；合成 S6 PASS |

**不复制旧缺陷的自检**：本设计无「整窗无推进 ⇒ 无条件 false + continue」（对照 `_stall_probe.py:169-189`）；无「只看紧邻下一窗 ⇒ 判终局」（对照 `:211-224`）；所有停止均为 `budget_disarm_conservative`，`semantic_truth_written=False`；合成 S3 直接构造旧缺陷会误判的反例并 PASS（`_test_out.txt:56`、`:58`）。若需要判断「是否结束」，本文明确：**仅保守预算，非语义真值**；这里停止只会少采，不会把长停误判为不存在（`TASK.md:66`）。

---

## 3 纯模型单测

**范围**：只测纯逻辑模型 —— 状态机、预算计算、配额与回退转换、事件匹配判定（`TASK.md:31`、`:101-109`）。**不测真实采样**；两个 `.py` 均不含任何进程/内存/系统接口调用。状态机 `_state_machine.py:1-47` 的模块说明声明「零 import、零系统接口」；测试 `_test_state_machine.py:26-36` 仅用 `importlib.util` 按绝对路径加载状态机，并以 `open(...).read()` 作只读文本内省，无 `exec`/`eval`/`compile` 外部数据执行。

**本次会话实跑命令 1（隔离模式、UTF-8、绝对路径）**

```
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/d13b_design_20261106/_test_state_machine.py" 2>&1 | tail -n 8
```

实跑输出（末尾 8 行，stdout）：

```
  [PASS] 保守停止不删除停滞登记 -> 不把长停误判为不存在（TASK.md:66）
  [PASS] >1s 观察不产出任何结束态 / 长停不存在语义真值

       NOTE: 真实栈格式与可解析性、系统调度时延、采样扰动、资源释放时序
             均为 [未验]；本单测只验证纯逻辑状态转换，不验证真实运行上界。

==============================================================================
PASS=43 FAIL=0
```

存档 `lead/d13b_design_20261106/_test_out.txt` 末行本次读取核验为 `'PASS=43 FAIL=0'`（`_test_out.txt:69`）。注意：命令 1 输出到 stdout，**未覆盖存档文件**；存档由同批交付件产生，本文只核验其尾行。

**本次会话实跑命令 2（合并核验：`BUDGET_MODEL.json` 自洽 + `STALL_EVENTS.json` 复算 + 反扫描 + `_test_out.txt` 尾行）**

```
python -I -X utf8 - <<'PY'
import json, statistics
base = 'D:/Project/ra2-campaign-forge'
bm = json.load(open(base + '/lead/d13b_design_20261106/BUDGET_MODEL.json', encoding='utf-8'))
print('=== BUDGET_MODEL.json ===')
segs = bm['segments']; s = sum(x['ms'] for x in segs)
for x in segs: print('  %-18s ms=%6.2f offlineVerifiable=%s' % (x['seg'], x['ms'], x['offlineVerifiable']))
print('  segments sum = %.2f ; totalMs = %.2f ; equal = %s' % (s, bm['totalMs'], abs(s-bm['totalMs'])<1e-9))
print('  meetsMedian = %s ; 152.5 < 129.93 = %s ; gap = %.2fms' % (bm['meetsMedian'], bm['totalMs']<129.93, bm['totalMs']-129.93))
print('  zero/neg segments = %d' % sum(1 for x in segs if x['ms']<=0))
print('\n=== STALL_EVENTS.json 复算 ===')
rows = json.load(open(base + '/lead/stall_event_def_20261106/STALL_EVENTS.json', encoding='utf-8-sig'))
true = [r for r in rows if r['isRealMatch'] is True]; dur = [r['durationMs'] for r in true]
print('  total=%d  true=%d  false=%d' % (len(rows), len(true), len(rows)-len(true)))
print('  min=%.2f median=%.2f max=%.2f' % (min(dur), statistics.median(dur), max(dur)))
print('  >=1000ms(true)=%d' % sum(1 for d in dur if d>=1000))
print('  100-200=%d  200-500=%d  500-1000=%d' % (sum(1 for d in dur if 100<=d<200), sum(1 for d in dur if 200<=d<500), sum(1 for d in dur if 500<=d<1000)))
B=152.5
print('  durs>=%.2f = %d (%.3f%%)' % (B, sum(1 for d in dur if d>=B), 100*sum(1 for d in dur if d>=B)/len(dur)))
print('  durs>=129.93 = %d' % sum(1 for d in dur if d>=129.93))
print('  durs>=200 = %d' % sum(1 for d in dur if d>=200))
b1=[d for d in dur if 100<=d<200]
print('  100-200 & d<152.5 = %d ; 100-200 & d>=152.5 = %d (%.2f%%)' % (sum(1 for d in b1 if d<152.5), sum(1 for d in b1 if d>=152.5), 100*sum(1 for d in b1 if d>=152.5)/len(b1)))
print('\n=== 反扫描 ===')
kw = ['ctypes','OpenProcess','ReadProcessMemory','WriteProcessMemory','VirtualAllocEx','CreateRemoteThread','SetWindowsHookEx','MiniDumpWriteDump','MiniDump','SuspendThread','StackWalk','TerminateProcess']
for f in ['_state_machine.py','_test_state_machine.py']:
    txt = open(base + '/lead/d13b_design_20261106/'+f, encoding='utf-8').read()
    hits = [k for k in kw if k in txt]
    print('  %s : hits=%s' % (f, hits if hits else 'NONE'))
print('\n=== _test_out.txt ===')
lines = open(base + '/lead/d13b_design_20261106/_test_out.txt', encoding='utf-8').read().splitlines()
print('  last non-empty line: %r' % [l for l in lines if l.strip()][-1])
PY
```

实跑输出（完整）：

```
=== BUDGET_MODEL.json ===
  event_onset        ms=  2.50 offlineVerifiable=False
  threshold_accum    ms=100.00 offlineVerifiable=True
  poll_dispatch      ms= 48.00 offlineVerifiable=False
  capture_exec       ms=  2.00 offlineVerifiable=False
  segments sum = 152.50 ; totalMs = 152.50 ; equal = True
  meetsMedian = False ; 152.5 < 129.93 = False ; gap = 22.57ms
  zero/neg segments = 0

=== STALL_EVENTS.json 复算 ===
  total=1737  true=1681  false=56
  min=100.00 median=129.93 max=566.96
  >=1000ms(true)=0
  100-200=1520  200-500=158  500-1000=3
  durs>=152.50 = 503 (29.923%)
  durs>=129.93 = 841
  durs>=200 = 161
  100-200 & d<152.5 = 1178 ; 100-200 & d>=152.5 = 342 (22.50%)

=== 反扫描 ===
  _state_machine.py : hits=NONE
  _test_state_machine.py : hits=NONE

=== _test_out.txt ===
  last non-empty line: 'PASS=43 FAIL=0'
```

**反扫描结论**：`ctypes` / `OpenProcess` / `ReadProcessMemory` / `WriteProcessMemory` / `VirtualAllocEx` / `CreateRemoteThread` / `SetWindowsHookEx` / `MiniDumpWriteDump` / `MiniDump` / `SuspendThread` / `StackWalk` / `TerminateProcess` 两个 `.py` 文件 **hits=NONE**（`TASK.md:144-146` 专项 A 关键词集）。此外 `_test_out.txt:10` 记 `[PASS] 状态机源码无任何 import / from 语句（零系统接口）`。

**单测覆盖内容（`_test_out.txt:9-63` 五组，43 条断言全 PASS）**

| 组 | 覆盖 | 关键断言（节选，均 PASS） |
|:--|:--|:--|
| 0 结构性不变量 | 零系统接口、语义取值集合不含「结束态/终局/长停不存在」、四类定位标记、D-27 三条更正、未验四项、参数标记 | `_test_out.txt:10-15` |
| 1 窗内配额 | `quota_cap=3` **[待论证指标]** 耗尽行为 | 单窗 5 个不同停滞 → 恰好 3 次 `CAPTURE`，2 次 `QUOTA_EXHAUSTED`；换窗配额归零而 dedup 注册表不归零（`:18-21`） |
| 2 冷却期 | `cooldown_ms=3000` **[待论证指标]**、`>=` 边界、冷却回退 | `t=2999ms` 仍抑制、`t=3000ms` 回退 `COOLDOWN -> ARMED`；合成时钟回退 `t=-50ms` 不误判（`:24-28`） |
| 3 停止与回退 | 保守停止预算、正常退出路径 | `>1s` → `DISARMED_BUDGET`/`BUDGET_STOP_ONLY`（非语义真值）；回退 A 按窗界、回退 B 正向恢复证据；显式 `EXIT`→`EXITED` 幂等（`:31-41`） |
| 4 事件匹配 / 去重 | 同一停滞多次观察 | 5 次原始观察 → `distinct_stalls=1 / captures=1`，跨窗合并同一身份（避开 `_stall_probe.py:169-189` 逐窗独立处理）（`:44-49`） |
| 5 六类场景 | 合成时序 + 既有缺陷反向验证 | 窗末截断保持开放、后续窗正向恢复 `RECOVERED`（不看后续窗的缺陷已避开）、缺窗/未观察到恢复 → `UNKNOWN` 绝不写终局冻结、`>1s` 5 次全不捕获且不产出结束态语义（`:52-63`） |

**单测不验证什么（诚实声明）**：`_test_out.txt:53`、`:65-66` 已写明 —— 「这只是逻辑放行；真实剩余覆盖受端到端预算约束，系统时延/扰动 [未验]，实测覆盖 [未验]（合计 152.5ms >= 中位 129.93ms）」；「真实栈格式与可解析性、系统调度时延、采样扰动、资源释放时序均为 [未验]；本单测只验证纯逻辑状态转换，不验证真实运行上界」。**模型通过不能验证真实运行上界、不保证 `rc=0`**（`RULING_D27.md:44`、`:67`）。

**本次未运行 / 未找到（不补造）**：`find "D:/Project/ra2-campaign-forge/lead/d13b_design_20261106/" -type f` 实跑输出中**未出现** `check_d13b.py`，亦未出现 `review/D13B_DESIGN_REVIEW.md`；故门禁脚本与独立复核件（`TASK.md:141-152`、`:155-165`）本次**未运行、未验证、不宣称通过**。它们由其他上下文承接，非本作者交付物。真机 / 活进程 / 采样执行、全量截图状态核验一律**未运行**（铁律禁止）。

---

## 4 未验

D-27 §4：「**系统时延、扰动、资源释放及真实栈可解析性**中不能凭离线资料验证的部分**必须列为未验**」（`RULING_D27.md:42`）；§6 `:67` 明列不背书；`STALL_EVENT_DEFINITION.md:212-219` 亦记「完全未验」。四项逐条说明**为什么离线验不了**：

| # | 未验项 | 为什么离线验不了 | 依据 |
|:--|:--|:--|:--|
| 1 | **系统时延**（系统调度 / 轮询 / 中断到发出捕获指令的真实耗时；被测线程实际响应；目标线程精准定位） | 既有离线语料只有外部帧推进时钟 `samples.t`，其 dt 节拍（`2.4960ms` 中位）是**既有离线 harness 的采样节拍代理**，不是目标系统的中断/调度/线程切换耗时（`BUDGET_MODEL.json:5-7`）。零真机铁律禁止启动 `gamemd.exe` / `ra2loader` / `YURI.exe`、不读活进程内存，本阶段**无法产生任何真实在线时延样本**；`RULING_D27.md:42` 已把「系统时延」明列为不能凭离线资料验证项。③=48ms 只是 `:190` 名义值的工程拆分 **[估算]**。 | `RULING_D27.md:34`、`:42`、`:67`；`STALL_EVENT_DEFINITION.md:201`、`:218`；`BUDGET_MODEL.json:19-21` |
| 2 | **扰动**（采样动作引入的额外停顿、GC / 分页影响、对帧率的影响、无死锁） | 离线语料不含任何注入、挂起或探针事件，无法测量「观察者自身引入的额外停顿」；且 D-27 §3 与项目铁律禁止写 `hook` / `MiniDump` / `SuspendThread` / `StackWalk` / 探针注入、禁止自行补采（`RULING_D27.md:34`），**不得为此产生真机扰动样本**。`STALL_EVENT_DEFINITION.md:218` 原文：「轻量非侵入采样探针在真机上的实际扰动与可行性……**完全未验**」，并说明 `<10ms` 只是「基于物理尺度的设计要求」。 | `STALL_EVENT_DEFINITION.md:195`、`:218`；`RULING_D27.md:34`、`:67` |
| 3 | **资源释放**（`100ms` 零残留、句柄与内存映射释放时序、`rc=0`、无孤儿进程/僵尸句柄） | 需要真实进程的退出序列、句柄表与退出码观测；离线语料无任何进程生命周期记录。零真机不启动进程、不 `taskkill`，**无 `rc` 可观测、无释放时序可测**。状态机仅记录 `exit_budget_ms` 数值与 `EXIT -> EXITED` 转换（`_state_machine.py:99-100`、`:235-243`、`:408`），`_test_out.txt:41` 明确断言「100ms 零残留 / rc=0 标为未验，模型不背书」。 | `STALL_EVENT_DEFINITION.md:208`；`RULING_D27.md:44`、`:67`；`_state_machine.py:99-100` |
| 4 | **栈**（真实调用栈格式、符号可解析性、函数归因、在线抓取 `≤2ms` 能否真的拿到可解析上下文） | 现有语料仅含外部帧推进时钟与单位计数，**未采集任何进程内部指令地址（EIP/RIP）或函数栈**（`STALL_EVENT_DEFINITION.md:216`）。`RULING_D27.md:42` 特别写明「现成且获准读取的离线栈材料若存在，可用于格式/解析评估；**本阶段未确认存在，不得为此采集**」—— 即本次既无栈材料、也不得去采。④=2ms 只是 `:200` 的设计指标 **[待论证指标]**，符号反解与栈回溯按两段式解耦全部离线化，但「离线能否解析」本身 **[未验]**。 | `RULING_D27.md:42`、`:67`；`STALL_EVENT_DEFINITION.md:199-200`、`:216`、`:218` |

**扩展未验清单（`_state_machine.py:108-115` 的 `UNVERIFIED` 六项 + `TASK.md:115`）**

- 系统调度时延 / 轮询到发指令的真实耗时 **[未验]**（`RULING_D27.md:42`）
- GC / 分页影响与采样扰动对帧率的影响 **[未验]**（`STALL_EVENT_DEFINITION.md:218`）
- 资源释放时序 / `100ms` 零残留 / `rc=0` **[未验] [待论证指标]**（`RULING_D27.md:67`）
- 真实调用栈格式与可解析性 **[未验]**（`STALL_EVENT_DEFINITION.md:216`）
- 被测线程实际响应 / 目标线程精准定位 **[未验]**（`STALL_EVENT_DEFINITION.md:201`、`:218`）
- 首次在线观察延迟（中断 / 调度）及真实首次采到时刻 **[未验]**（`BUDGET_MODEL.json` 段①）
- 跨窗 / 跨洞同源性、恢复态与结束态语义真值 **[未验]**（`RULING_D27.md:14`、`:48`）
- 53 条 `>=1s` 候选的截图 / 结束 / 加载状态全量独立核验 **[未验]**（`RULING_D27.md:14`）
- 真实捕获成功率、`rc=0` **[未验]**
- 500–1000 单位超大规模停滞形态、逻辑/渲染耗时解耦占比 **[未验]**（`STALL_EVENT_DEFINITION.md:217`、`:219`）

**诚实声明**：以上不是「本阶段漏做」，而是 `RULING_D27.md:42` 明列「不能凭离线资料验证」、且本阶段零真机 / 零采样实现，一律**未跑、未验、不补造**。`RULING_D27.md:69` 不背书未执行的门禁、统计复算、合成单测、全量截图状态核验或可行性验证已通过。本文 §3 的实跑只覆盖**纯逻辑模型**，不覆盖上述任一项。

---

## 5 指标定位

D-27 §4：「`<50ms` / 建议 `<=20ms`、扰动 `<10ms`、最多 3 次及 `100ms` 清理**均为待论证指标**，模型通过**不能**验证真实运行上界或保证 `rc=0`」（`RULING_D27.md:44`）；§6 `:67` 逐项不背书；`TASK.md:119-121` 要求凡出现这些数字必须标 `[待论证指标]`，**不得写成「已达成」或「保证」**。

**逐字定位五个指标（每个一律 `[待论证指标]`，无一个写成已达成/保证）**：`<50ms` **[待论证指标]**；`≤20ms`（即 `<=20ms`）**[待论证指标]**；`<10ms` **[待论证指标]**；最多3次（最多 3 次）**[待论证指标]**；100ms 清理（`100ms` 清理）**[待论证指标]**。逐项展开见下表：

| 指标 | 出处（`文件:行`） | 定位 | 本文中的状态 |
|:--|:--|:--|:--|
| `<50ms`（端到端触发延迟） | `STALL_EVENT_DEFINITION.md:190` | **[待论证指标]** | 仅作为 §1 段③ `48ms` **[估算]** 拆分的名义来源；未达成、未验证 |
| `≤20ms`（安全裕量） | `STALL_EVENT_DEFINITION.md:190` | **[待论证指标]** | §1 (a) 作为「若兑现」的假设条件；即便取该值合计仍 `122.5ms`，余量 `7.43ms`，**不可保证** |
| `<10ms`（扰动，最高 `≤15ms`） | `STALL_EVENT_DEFINITION.md:195` | **[待论证指标]** | `STALL_EVENT_DEFINITION.md:218` 记「完全未验」；`## 4 未验` 第 2 项 |
| 最多 3 次（单窗配额） | `STALL_EVENT_DEFINITION.md:206` | **[待论证指标]** | 状态机 `quota_cap=3`（`_state_machine.py:118`、`:88-89`），仅为纯模型参数；合成单测组 1 PASS 只验证逻辑转换 |
| `100ms` 清理（零残留 / `rc=0`） | `STALL_EVENT_DEFINITION.md:208` | **[待论证指标]** | `_state_machine.py:99-100` 标 `[待论证指标][未验]`；`_test_out.txt:41` 断言「模型不背书」；`## 4 未验` 第 3 项 |
| `≤2ms`（在线抓取，两段式解耦） | `STALL_EVENT_DEFINITION.md:200` | **[待论证指标]** | §1 段④ `2.00ms` **[估算]** 的名义来源；真实捕获执行耗时 **[未验]** |
| `≥3.0s` 冷却 | `STALL_EVENT_DEFINITION.md:206` | **[待论证指标]** | 状态机 `cooldown_ms=3000`（`_state_machine.py:119`、`:90-91`）；合成单测组 2 PASS 只验证 `>=` 边界逻辑 |
| `>1.0s Disarm` | `STALL_EVENT_DEFINITION.md:207` | **[待论证指标]**，且**必须更正** | 按 `RULING_D27.md:44`、`TASK.md:53` 更正为**仅 [保守停止预算]**，**不得当结束态语义真值**；状态机 `budget_stop_ms=1000`（`_state_machine.py:120`、`:92-94`）、语义取值集合不含任何终局值（`:63-68`） |
| `rc=0` 保证 | `STALL_EVENT_DEFINITION.md:208` | **[待论证指标]** | `RULING_D27.md:44`、`:67` 明确「模型通过不能……保证 rc=0」；本文不背书 |

**总声明**：上述全部数字是 **设计指标 / 工程估算**，不是实测。凡本文出现的 `152.50ms` 合计、`2.50ms` / `48.00ms` / `2.00ms` 分段、`503/1681` / `342/1520` 可达条数、窗内可见时长下界，一律标 **[估算]** 或 **[待论证指标]**；凡 §4 的四项与扩展清单，一律 **[未验]**。**状态机 43 条断言 `PASS=43 FAIL=0` 只证明纯逻辑自洽，不验证真实运行上界、不保证 `rc=0`、不背书短停捕获可达**（`RULING_D27.md:44`、`:67`、`:69`）。`RULING_D27.md:68` 不背书采样实现 / 真机 / 活进程操作授权，不预承诺离线通过后放行；D-13 采样实现与执行继续 PAUSE（`:8`、`:32`）。

---

**收束（写给拿本文判断「值不值得继续」的人）**：这条离线路线**值得继续**，但继续的目标必须被严格限定为「把设计写到可审、把逻辑模型跑通、把未验逐项挂账」，而**不是**「证明短停捕获方案可实现」。本次交付中，可审的部分已实跑闭合（预算自洽、反扫描零命中、`PASS=43 FAIL=0`、覆盖分桶复算、三条裁决更正与标记纪律）；不可闭合的部分也已诚实写明：`152.50ms ≥ 129.93ms` **在当前假设下达不到**、按现 `100ms` 门槛触发机制在 `STALL_EVENT_DEFINITION.md:191` 定义上已不合格，以及系统时延 / 扰动 / 资源释放 / 栈可解析性四项 **[未验]**。若下一步要真正推进方案，缺的不是更多离线模型，而是**另有有效明确授权**的新裁决（触发范式）与真机实测（`RULING_D27.md:32`、`:34`、`:68`）—— 本 D-13b 不代授权、不预承诺放行。正确表述始终是：**当前 97 窗按现规则保留的事件中未识别到 ≥1s 平台，语义漏检及跨场景代表性未闭合**；不写「长停不存在」，`>1s` 仅作保守停止预算。
