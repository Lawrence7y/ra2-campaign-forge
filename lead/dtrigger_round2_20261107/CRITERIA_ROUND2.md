# CRITERIA_ROUND2 · 四项调查与独立复核汇总（离线只读）

> 撰写范围：仅汇总题给「四项调查 + 独立复核」材料，以及本轮亲自实跑/亲读的落盘件行。本件不新增判据、不新增观测量、不改台账、不改裁决书、不改需求原文、不 commit / 不 push。
> 修订说明：按「冷读挑错员」意见修订——把 §6 的占位命令换成完整可复跑命令与逐行 stdout；把「已复现」一律改写为「题给调查件/复核回件载有；本撰写轮未重跑、记为未验」；撤去「无需用户裁决 / 冲突为空 / 工作流回执字段取假值」这一未被授权的结论；收紧 S_hat 与物理 S 的措辞；补齐 `S_low`、P、目标①、档数口径等定义与未定项。本件仍为唯一写域 `lead/dtrigger_round2_20261107/` 内同一文件 `CRITERIA_ROUND2.md`（本轮 `git -C D:/Project/ra2-campaign-forge status --porcelain -- lead/dtrigger_round2_20261107/CRITERIA_ROUND2.md` 输出 `?? lead/dtrigger_round2_20261107/CRITERIA_ROUND2.md`）。

## 1 目的与边界

**目的**：把 A「新判据族设计（禁止调参）」、B「§3.2 未验列统一锚补算」、C「塌陷归因独立重算」、D「物理 S 可观测量对齐」四项调查，与各自独立复核回件，汇成一份可逐条复核的对照件；只摊开已验/未验的边界，不作方案取舍。

**证据层级（本件所有读数按此归类，不混层）**：

| 层级 | 含义 | 本轮能否复核 |
|:---|:---|:---|
| L1 题给材料 | 本 ask 的「四项调查 + 独立复核」JSON 字段（含 `verdict`、`sha256Line`、`ranCommands`、`evidence`），以及题给【上游指纹】 | 只能与落盘件行号/指纹对照，不能重跑其自报命令 |
| L2 落盘件行 | `lead/dtrigger_round2_20261107/_d*`、`_verify_*`、上游只读件的 `:行` | 本轮用 Read/Python 只读打开逐行核对 |
| L3 本轮实跑 | 本轮亲自执行的 `python -I -X utf8` 指纹/算术命令与 `git status`，完整命令与 stdout 见 §6 | 已实跑，输出逐行给出 |

**关键登记**：四份复核的 `verdict = partial` 出自 **L1 题给材料的 `confirmation.verdict` 字段**，不是任何落盘件的某一行。本轮执行 `python -I -X utf8 -c "…遍历写域 47 个条目统计 'verdict'/'partial' 出现次数…"`（CMD-7，完整输出见 §6）→ `files_with_verdict_or_partial = 3`，其中 `CRITERIA_ROUND2.md verdict=12 partial=15`（本件自身文字）、`_dD_align.py verdict=2 partial=0`、`_verify_A_recompute.py verdict=1 partial=0`；**没有任何落盘复核回件文件记录 `verdict = partial` 这一字符串**。故 `partial → unconfirmed` 的判定来源是题给材料，本件如实标注，不冒充落盘证据。

**纪律（本轮实际执行）**：

- 零真机：不启动任何游戏可执行文件、不终止进程、不读活进程内存。
- 零采样代码：本轮未编写、未引用任何真实采样 API，也未写任何获取手段 / 实现方案；清单只描述观测量名称、口径与精度（见 §5、§7）。
- 只读母本与既有件：`ra2youli/**`、`out/re_work/**`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md`、`lead/ROUND_SUBAGENT_LOG_*`、`swarm_*` 及题给 7 个上游件一律未改；本轮 CMD-1 逐文件实算 7 个上游指纹输出 `MATCH = True` × 7（§6）。
- Python 一律 `python -I -X utf8` + 绝对路径；指纹用 Python `hashlib`（本机无 `sha256sum` / `wc`）。
- 口径 B 与 `STALL_EVENT_DEFINITION.md:177`、`:190`、`:191` 原文一律不改、不重述为「已闭合」；`RULING_D30.md:32,38,62`（本轮亲读）的执行 PAUSE、N=1/3/5 只作离线预算情景、不得改口径/需求原文继续有效。
- D-30 明令不选定 k 档进实现：`RULING_D30.md:32`「保持实现执行PAUSE」、`:38`「N=1/3/5只保留为离线预算情景，未选定为实际设计参数」、`:66-67`「不得把99.76%覆盖率外推为方案可行」「不背书 k10 已获执行批准…k25 已合规」。本件不把任何判据、锚、k 档、观测量清单升格为已批准方案。
- 四份复核 verdict 均为 `partial`（L1 题给材料），因此四项结论一律标注 **unconfirmed**，不得升格；见 §6、§8。

**本轮实跑清单**（完整命令与逐行 stdout 见 §6）：CMD-1 7 个上游指纹；CMD-2 4 个复核对象指纹；CMD-3 百分比/不确定度算术；CMD-4 写域 `git status`；CMD-5 8 个复核落盘件指纹；CMD-6 写域文件清单；CMD-7 `verdict`/`partial` 落盘检索；CMD-8 `S_low`/P/目标① 定义行重读。本轮**未**重跑任何调查/复核脚本（`_dA_run.py`、`_dB_anchor_recompute.py`、`_dC_recompute.py`、`_dD_align.py`、`_dD_check.py`、`_verify_*` 均会覆写或属题给既有件），故调查回件与复核回件自报的运行次数、退出码、`ranCommands` 在本撰写轮**未独立复核，记为未验**；§2–§5 中所有「实跑」「逐格全等」「独立复现」措辞均指 **L1/L2 转述**，不是本轮 L3 结论。

## 2 新判据族（三维比较与「不可兼得」的形式化证据）

**调查回件 A（L1）**：在 `(t,f)` 前缀在线因果判据族 D1–D5 共 **11 档新判据** 上做三维离线比较（`:177` 及时性含逐游程 e 修正、误触发抢占配额后的真实捕获、N=1/3/5），另设 **4 档 CAL 校准**（仅核对用，不参与新判据比较；合计 15 档出现在主表里，`_dA_out.txt:31-32,49`）。给出四条可判定计数界；任意实值函数型谓词的信息论级断言单列 U5 未验。

**落盘读数（L2，`_dA_out.txt`，本轮亲读；不是本轮实跑）**：

- 语料 `n=104` 文件 / `1125992` 点 / `64` 窗 / `28381` 游程 / `1681` real；逐游程 e 有效 `n=28317`，中位 `2.511`、P99 `4.145`、max `488.616` ms（`:21-29`）。
- 禁止项扫描命中 `[]`、4 档校准独立重算逐格全等 `PASS=4 FAIL=0`（`:31-40`）——均为调查件自报，本轮未重跑。
- 三维主表（`:49-65`）：`D5-phase` `trig=2357 / hits=434 / fRate=80.738% / latP50=105.151ms / in50_strict=18 / W5=66 / T5=27`；`D4-burst` `in50_strict=1569 / fRate=93.990% / W5=41`（`:62-64`）。`D1-word-MMM` 与 `D1-word-LLL` `falseRate=0` 仍各吃 1 个 W5 配额（`:55-56`、`:73-75`）。以上 `lat*` / `wait*` 均为 **S_hat 锚下界**（`:44-45`），不是物理 S 下的等待实测。
- 证据①配额硬上界（`:191-201`）：每窗理想 `W={1:26, 3:73, 5:117}`、每会话 `T={1:12, 3:31, 5:47}`；`N=5` 每窗 `≤117/1681`、实测最佳 `W5=66/1681`（`D5-phase`）。本轮 CMD-3 只实算了两个除法 `117/1681 = 6.960143 %`、`66/1681 = 3.926234 %`；**上界本身的推导未被本轮重算，复核 A 亦未反证**。「未反证」不等于「已复现」。
- 证据②存活集基准率（`:203-224`）：13 个 τ 单调不减，`τ=50ms → 33.2279%`；`:207` 把「单次触发」推到「混合 τ 的总查准率 ≤ max 基准率」。
- 证据③前缀签名命中集（`:226-249`）：限定特征类下 `τ=18 LB1=4056 → precision≤29.1899%`、`τ=50 LB1=1638 → precision≤50.6031%`、`UB_naive=26617`、`τ=18` 空前缀 real `9`；`:249` 自述仅限定「形状/序数/相邻游程摘要」类，`:280` 单列 U5：1µs 精确签名 `LB1=0`、信息论级断言未验。
- 证据④ e 计数（`:251-257`）：调查件写「`e>50` 落真实事件 `56` 条 + `startTick=0` 且 e 未验 `4` 条 = `60/1681`，**故** `in50_strict ≤ 1621/1681`」。本轮 CMD-3 只实算 `1621/1681 = 96.430696 %`（除法本身）。**本件不沿用这个「故」**：`in50_strict` 对应严格 S+50ms，而 `CRITERIA_COMPARE.md:93-98`（本轮亲读）明写严格核算需物理 S 且语料不可得；`e`/`U` 是 `S_hat − S ∈ [0,e]` 的观测锚侧间隙上界（`S_OBSERVABILITY.md:52-59,175-179`，本轮亲读）。因此该式只能读作**固定外部采样器下的离线事后可证计数**，不是物理 S 侧、也不是在线工程的普遍硬界；4 条 `startTick=0` 事件的 e 仍为未验，不得由减法把它变为「已计入的已验量」。调查件 `:253` 写作「任何 (t,f) 前缀判据的上确界」、`_dA_design.md:194-198`（本轮亲读）写作「不可兼得，且不是调参能绕过的 —— 证据①②④ 对任意 `(t,f)` 前缀谓词成立」，均为被复核质疑的原文，本件只转述。

**独立复核 A（L1，verdict = partial → unconfirmed）**：题给材料载复核实跑 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_verify_A_recompute.py` → `SUMMARY PASS=54 FAIL=1`（`_verify_A_out.txt:124`，本轮亲读该行）；15 档三维字段、6 格配额、13 个基准率、6 行 LB1、12 项自检对应物、11 行触发拍差异率逐格复现（L1/L2，本轮未重跑）。崩点：

1. `:111` `FAIL e hard bound is only an offline verifiability bound, NOT an online physical upper bound`；`:112` `offline verifiable=1621, conceptual online possible=1681; no online execution performed`。依据 `CRITERIA_COMPARE.md:93-98`、`S_OBSERVABILITY.md:173-179`（`:176` U 反映离线工具事后分辨率、`:178` 在线实现不受外部掉拍制约、`:179` S 不可精确观测不构成 `:177` 无法满足的证明）、`RULING_D30.md:30`（「不能判成物理采不到」），均本轮亲读。
2. 谓词无关的查准率上界被复核显式反证：`_verify_A_out.txt:119` 确定性查表谓词 `trig=1679 real=1678 false=1 precision=0.999404 > 0.332279`；`:120` `EXACT_LOOKUP in50_strict=1619/1681 W1/W3/W5={1:26,3:73,5:117}`；`:121` 差分触发反例 `precision=0.980432`。`:110` 列出三处「任意/一律成立」措辞（`_dA_out.txt:191,206,253`）。
3. 证据③的特征类不覆盖 D3/D5：`_verify_A_out.txt:118` 复现 `_dA_run.py:281-360` 与 `:569-581` 的 mismatch；`_dA_design.md:198-204` 仍把基准率与 e 写成「无条件成立」。
4. 其他裂缝：`:364-377` 禁止项自检只扫描四个字符串、`_dA_out.txt:282` U7 承认字母表 `0.05/0.5/2/5ms` 与 `S4/M6` 未做敏感性扫描；`_dA_check.txt:17` 自列铁律 9 对象是上游 `CRITERIA_COMPARE.md`（本轮亲读、CMD-1 实算 MATCH）；`_dA_check.txt:14` `PASS=12 FAIL=0` 与自指哈希旧值不可当最终自证。

**本件判定（只摊开，不作肯定性裁决）**：L1/L2 载有配额理想 `26/73/117`、`W5=66`、`56+4=60` 计数、e 分布、11 档三维表；本轮 L3 只实算了其中三个百分比。**以下一律 unconfirmed**：「33.2279% 谓词无关上界」「1621/1681 物理上确界」「三者不可兼得且非调参可绕过」「配额硬上界已被本轮复现」。`W5=66` 只是调查件 15 档（11 新 + 4 校准）中的最佳，不是全局最佳；「全局最佳」按哪一批档算、要不要算，本件无清单、未验。

## 3 §3.2 未验列统一锚补算（12 格数值与适用域）

**口径 U（L1 调查回件 B 明写，`_dB_anchor_recompute_out.txt:44-46`，本轮亲读）**：U1 每个 id 取其权威登记锚（4 档 lastEdge、2 档 runStart，`_dtrigger_metrics.py:217,223-227`）；U2 两列等待锚一律 `S_hat=t[runStart]`，`wait=(t[idx]-t[i])*1000`；U3 `og=(t[i]-t[i-1])*1000`，`i=0` 时 `og=None`；U4 `e=2.510999999ms` 全精度中位常数（`n=28317`，`CRITERIA_COMPARE.md:222-223` 只加中位常数）；U5 `>=100: wait>=100.0`、`+e>50: wait+e>50.0`，分母 = 全部触发；U6 `og=None / he<64 / base<=0 ⇒ 不触发`。**U1 是选择而非推导**（复核 B 崩点 5），本件不把口径 U 指定为批准口径。

**12 格 L2 读数**（`_dB_anchor_recompute_out.txt:48-55` 主表、`:57-87` 逐格有序 wait 表；复核 `_verify_B_out.txt:8-13,38-43` 逐值全等——均本轮亲读，**本轮未重跑**）。**所有 `wait` 与 `>=100` / `+e>50` 格数都是 S_hat 锚下的触发等待计数，不是物理 S 下的严格核算**（`CRITERIA_COMPARE.md:222-223`；`_dB_anchor_recompute_out.txt:149`）：

| id | 谓词锚（U1 选择） | nTrig | `>=100` | `+e>50` | waitMin/Med/Max (ms，S_hat 下界) | realHits |
|:---|:---|---:|---:|---:|:---|---:|
| C2-abs-P95x2 | lastEdge | 29 | 5 | 29 | 66.334/70.931/321.002 | 8 |
| C3-r4 | lastEdge | 24 | 24 | 24 | 125.884/127.491/440.389 | 8 |
| C3-r4-clean | runStart | 24 | 24 | 24 | 128.284/130.237/461.598 | 8 |
| C3-r8 | lastEdge | 16 | 16 | 16 | 251.709/256.261/258.378 | 1 |
| C3-r8-clean | runStart | 16 | 16 | 16 | 254.247/258.835/260.904 | 1 |
| C3-r12 | lastEdge | 15 | 15 | 15 | 377.385/385.601/387.990 | 0 |

**关于「不可补算」的登记（不替用户判定）**：调查 B 的 `what` 把任务定义为「证明 `og=None` 只导致不触发而非已触发但无定义，故无需写不可补算」，L2 依据为 `_verify_B_out.txt:15-20`（`i==0 n=64`、`og=None 且 he>=64 n=0`、`he<64 n=3813`、4 条 `startTick=0` 事件 `he=0 / og=None` 不进任何 id 触发集、各 id 触发行 `og=None` 计数全 0）与 `_dB_anchor_recompute_out.txt:146`。**但**§3.2 台账未验的真实原因不是 `og=None`：`CRITERIA_COMPARE.md:242-251`（本轮亲读）明写是补算 `f_rate` 用 runStart 锚 vs metrics 用 lastEdge 锚、历史标签误标（`:245-246`）、`-clean` 两档无独立行（`:251`）、全触发 wait 中位与仅真实命中 `latP50` 两个母体不可互换（`:252`）；复核 B 全文搜「不可补算」= 0 命中。本件**不改台账**：`CRITERIA_COMPARE.md:170-180,242-251` 的「未验」标记保持原状；上表只是口径 U 下的 L2 补算读数，**不得替换成「已验」，也不据此判定「无需写不可补算」**——该判定属用户/裁决层，本件 unconfirmed。

**独立复核 B（L1，verdict = partial → unconfirmed）**：题给材料载复核另写 `_verify_B_recompute.py` 实跑（exit=0，未复用调查脚本、未重跑会覆写落盘件的 `_dB_anchor_recompute.py`）得 12 格逐值相同、`A_ok/B_ok/C_ok/D_ok=True`（`_verify_B_out.txt:68`）。崩点：

1. 铁律 9 指错对象：`_dB_anchor_recompute_out.txt:18` 与调查 evidence 的 `4a342405…/48343` 是 `CRITERIA_COMPARE.md`（`_verify_B_out.txt:61-63` 实算 `hash==CRITERIA_COMPARE.md True`、`==out.txt False`）；复核正确值见 §6。
2. evidence 指纹串损坏：`:58` 实算脚本 `44b10371cdc258e7db5c232f53d9d64dfdf4f34cb084115d0bb8c7a05a5a382b/27324`；`:65-66` 证明回件所称尾 `26f3fb61829756dfeecf` 不在任何 `_dB_*` hash 中、`b6f95763794` 是 data.json 的尾 12 位被混入 out.txt 行。该段不可作指纹证据。
3. 自检含硬编码：`_dB_anchor_recompute.py:401-413`（本轮亲读）把四档 min/med/max 写成 `probe_expect` 字面元组、通篇不读 `_dtrigger_probe_out.txt`，`:409-413` 是自己结果与自己常量比对；`_dB_anchor_recompute_out.txt:155`「全部检查项均为本脚本本轮实跑」对第 (2) 项不成立。复核另跑的 `B_ok=True` 属 L1/L2，本轮未重跑。
4. `+e>50` 六格是空列：`_verify_B_out.txt:45-46` 载 `+e>50` 与 `>50` 在 6 档恒等，全体触发最小 wait `66.334ms`、`50−minwait=−16.334ms`，故任何 `e>−16.334ms` 都给同样答案；U4 的 e 重算数值真但零判别力。`>=100` 五档恒等于 nTrig，只有 `C2-abs-P95x2` 的 `5/29` 有区分。
5. 「统一」是选择而非推导：`_verify_B_out.txt:47-53` 若六档一律 runStart，则 `C2-abs-P95x2 → 27/4/27`、`C3-r12 waitMed 387.348 vs 385.601`；两个 `-clean` 档主探针无独立行，其 wait 分布依赖重标论证（`_dB_anchor_recompute_out.txt:115-129`），非独立同 id 实测。
6. `og=None` 论证答非所问：`og=None` 只出现在 `i==0` 而 `i==0 ⇒ he=0`，是游程构造的结构恒真式；`_dB_anchor_recompute_out.txt:146` 把 2 个 runStart 档也归到 U6，实际它们只由 `he<64` 拦下。

**边界登记（措辞扫描，非语义确证）**：L2 文件 `_dB_anchor_recompute_out.txt:148-154`（本轮亲读）明写 S_hat 锚下界、逐游程 og/e 实测未做、Q5 四项未验、4 条 `startTick=0` 事件物理 S 不可判定、工程可行性/修复收益/方案批准未实跑；`:113` 称 `C3-r12` realHits=0/15 为口径 B 计费漏洞。复核 B 据此登记「没有把 S_hat 当物理 S」「没有把低误报率外推成方案可行」——这是**文本措辞层面的登记**，不是本轮对语义/工程的实跑确证。另 `_verify_B_out.txt:21`：`C2-abs-P95x2` 的 `>=100=5` 与 `falseTriggers=5` 数值巧合但集合不相交（5 条 wait≥100 的 d_fin 最小 158.582ms，false(d_fin<100) 另 5 条，交集 0）——`>=100` 定义见 `CRITERIA_COMPARE.md:220-221`，是触发等待而非事后 d_fin 计费，口径 B 未变。

## 4 塌陷归因独立重算（156 格不变式与 54/71 计数）

**调查回件 C（L1）**：从 `lead/dtrigger_compare_20261107/_cost_quota_data.json` 的 `results/nofalse/upper` 独立重算，数据源仅该 JSON；本轮 CMD-1 实算其 `SHA256 = e6c26896319acb0387f06384665d5db3668e0f15e29f7328cac97f4931c03cac`、`字节数 = 111044`、`MATCH = True`。

**落盘读数（L2，`_dC_out.txt`，本轮亲读；26 判据 = 该 JSON 的判据全集，与 §2 的 11 新 + 4 校准、§4 的 13 档 C2/C3 不是同一批次，见 §8 档数口径）**：

- `:27-32` 格数 `156 = 26 判据 × 6 情景`；分解式 `ideal − captured = (ideal − noFalse) + (noFalse − captured)` 不成立 `0/156`、两项非负违例 `0/156`、链式违例 `0/156`、`captured==ideal` `0/156`。理想值 `window1/3/5 = 26/73/117`、`trip1/3/5 = 12/31/47`（`_dC_out.txt:20-25`；`RULING_D30.md:40-46` 本轮亲读给出同表并声明「在线误触发抢占后没有同等覆盖保证」）。
- `:34-37` 前缀分组 `A = C1-/C4-/C5- = 54` 格、`B = C2-/C3- = 102` 格、`54+102=156`。
- `:40-46` A 族 `noFalse==理想 54/54`、召回/时序损失 `0` `54/54`、抢占损失 `0` 的格 `0/54`、塌陷 `>0` `54/54`；附加 `captured==capUpper 54/54`、`capUpper==理想 0/54`。
- `:48-57` B 族 `noFalse−captured==0` `71/102`、`capUpper==理想 73/102`、交集 `71/102`；多出的 2 格为 `C3-N16-r2 | trip3 … preempt=2`、`C3-N16-r2 | trip5 … preempt=3`。
- `:72-75` 口径歧义：`CRITERIA_COMPARE.md:338` 括注 7 档 × 6 情景 = `42` 格，而 `71` 实为 C2/C3 全族零抢占格数、来自 13 档，非括注档贡献 `29` 格；`73 ≠ 71`。

**独立复核 C（L1，verdict = partial → unconfirmed）**：题给材料载复核 `_verify_C_recompute.py` / `_verify_C_cells.py` / `_verify_C_ast.py` / `_verify_C_rerun.py` 输出 `cells=156 decomp bad=0 chain bad=0 A=54 B=102 A+B=156 B preempt==0=71 B up==ideal=73 intersection=71 named 7 criteria -> p0 cells=42 not-named p0 cells=29`；逐格重读 `_dC_cells.txt` 156 行违例 0；AST `imports=['collections','hashlib','json','os']`、写模式 open 0。本轮未重跑。崩点：

1. §7c-2–§7h 是纯字面输出：`_dC_recompute.py:356-368`（本轮亲读）为 `emit("…")` 常量串；`all_pass` 门（`:391-401`，本轮亲读）只 gate `n_cells / decomp_fail / nonneg_fail / chain_fail / 54 / 102 / 71 / 73 / bad_within50 / probe_bad`，9.3/9.4/9.5/9.6 的子断言与 7b 无聚合断言却并入 `:148` `总判定 = PASS`。
2. `:147` §9.7「高档 ≥100ms」把「部分/无行」写成「已验」：复核独立解析 supplement 得 13 档中仅 4 档全部触发 ≥100ms、5 档只是部分、4 档无行（`_verify_C_rerun_stdout.txt:97-108`，本轮亲读；例如 `C2-P95x2 nTrig=27 >=100=4`、`C2-P99x2 24/1`、`C3-N16-r2 195/156`、`C3-r2 180/148`），成立的只是「可读行全部 >50ms」。**本件不裁定这一口径冲突**：它与 §3 的 `C2-abs-P95x2 5/29` 并列登记为待裁决项（§8），不写「已收敛」「不构成需裁决的冲突」。
3. 分解式是减法恒等式（复核在 1331 组 `(idl,nf,cap)` 上全成立，L1），有信息量的是非负/链式不等式（L2 违例 0）。
4. `within50=0.000000` 不纯是「触发晚」：`_dtrigger_metrics.py:26,54,283` 分母固定 1681 全集、漏检按 0 计，`C3-r12 realHits=0 / latP50=0.000` 是占位。
5. `_cost_quota_data.json` 无延迟字段，「触发等待越线」只能读回既有输出、不能从该 JSON 重算（`_dC_out.txt:77-79`）；`results/nofalse/upper` 是否忠实于 `1125992` 点 / `28381` 游程的原始重放未验（`:134`）。`:129` 明写「越线为 S_hat 锚下的实测结论，不是相对物理 S 的严格核算」，§9 未复述该限定。
6. L2 措辞扫描登记「没有把 S_hat 当物理 S」「没有把低误报率外推成方案可行」（`_dC_out.txt:133,135` 单列未验），但 §9.3/§9.4 未复述 `CRITERIA_COMPARE.md:281,339,449`「0/156 达到理想、不合规方向、不是修复」。此为文本层面登记，非本轮语义确证。

## 5 物理 S 可观测量对齐（硬阻断判定 + 最小新观测量清单）

**调查回件 D（L1，`_dD_PHYSICAL_S_ALIGNMENT.md:45-47`，本轮亲读）把 e 与 U 称为「同一物理量、不同统计母体」**：本件须加限定——按 `CRITERIA_COMPARE.md:93-98` 与 `S_OBSERVABILITY.md:52-59,175-179`（本轮亲读），e = `S_hat − S_low_max` 一类观测锚间隙上界、U = `S_obs − S_low` 离线工具事后分辨率，**两者都是 S_hat / 观测锚侧的统计量，不是物理起点 S 上的点值**；「同一物理量」只在「两者都描述相邻采样间隔/观测不确定度」这一观测侧意义上成立。§2.1 的 e（全体 `28317` 游程，中位 `2.511` / P99 `4.145` / max `488.616` ms）与 S 件的 U（`1677` 条真实事件，中位 `2.515` / P99 `111.495` / max `488.616` ms）是同一观测侧量的不同筛选母体：`B ⊂ A`、长尾富集 `11.26×`（L1/L2，本轮未重算）。

**落盘描述性统计（L2，`_verify_D_out.txt:1-17` 与 `_dD_check_out.txt:24-31`，本轮亲读；不是本轮 L3 实跑）**：`files=104 samples=1125992`、`windows=64`、`all_runs=28381 A_valid=28317 window_first=64`、`e: min=0.008 med=2.511 P95=2.667 P99=4.145 max=488.616`、`e>50=84`、`U(n=1677) med=2.515 P95=35.367 P99=111.495 max=488.616`、`U>50=56 U>48=62 U>100=22`、`contained=1677/1677 pair_equal=1677/1677`、`d_final>=100=1704 delta=23`、`B/A=5.9222% enrichment=11.2570x`、禁词扫描 5/5 CLEAN。`S_OBSERVABILITY.md:163-179`（本轮亲读）给出保守预算 `50−U` 与「S 不可精确观测不构成 `:177` 无法满足的证明」。

**硬阻断判定（调查 D 的结论，L1，`_dD_PHYSICAL_S_ALIGNMENT.md:106-114`，本轮亲读）**：

- 「物理 S 不可得」的硬阻断**只**落在「离线语料上的肯定性合规确证」——证据不足，未验，**不是已证明不合规**（`:108-110`）。
- 「观测锚下界越线」在调查件 `:114` 被称作「独立证成的不合规方向结论，不依赖 S」，所据 `_dD_check_out.txt:39-41` 的反向不等式与 `CRITERIA_COMPARE.md:34-35,145-147` 的「不合规方向」。**本件不沿用「独立证成」这一强度**：复核 D 崩点 1（`_verify_D_out3.txt:7-10`，本轮亲读）实测 B3/B4 块 `computed=0 literal_prose=12/10`，即「两个不等式」是打印文字命题、零确定性计算；整份 verdict 为 partial → **unconfirmed**。故此处只登记为「调查件的文字论证 + 上游不合规方向记载」，不是本轮/复核的实跑证成。
- C（现场快照实际保存完成时刻）在语料中完全缺席，调查件列为第二个独立阻断项（`_dD_check_out.txt:42-44`；`CRITERIA_METRICS.json:542-558` U4-EndToEndSave = notImplementable 占位）；同属结论层文字命题，unconfirmed。
- `:190` 的时间核算起算点是检测确认时刻 D，与 S 正交（`:111`）；在线工程物理可行性未验且 D-30 禁止由离线掉拍外推（`:112`、`RULING_D30.md:30,60,66`）。

**最小新观测量清单（L1 原文，`_dD_PHYSICAL_S_ALIGNMENT.md:118-134`，本轮亲读；`_dD_check_out.txt:46-55`）**

| 编号 | 观测量（口径，非获取手段） | 精度要求（调查件原文） | 本件登记 |
|:---|:---|:---|:---|
| O1 | 逐事件物理停滞起点 `S`，与 `S_hat` 可逐事件配对，保留 `S ∈ (S_low, S_hat]` 区间校验 | ≤1ms / ≤1ms；原文称「合计 ≤ :177 的 50ms 预算的 2%」 | 「2%」被 CMD-3 实算否证（见下），**搁置、不采纳、不修正** |
| O2 | 逐事件现场快照保存完成时刻 `C`，与 O1 逐事件一一配对 | ≤1ms / ≤1ms | 无实跑支撑，未验 |
| O3 | `S` 与 `C` 的时基一致性 / 同步残差上界（关系量） | 残差上界 ≤1ms | 无实跑支撑，未验 |
| O4 | 目标线程上下文归属与完整性标记（布尔/枚举） | 缺失数 = 0、归属误配数 = 0 | 无实跑支撑，未验 |
| O5（条件项） | 窗首 / 跨窗无断档前序连续时序 | 仅当覆盖 4 条 `startTick=0` 事件时必需；否则须显式声明覆盖母体 | **O5 不属「最小集 O1–O4」**；条件是否成立、由谁判定未定（§8） |

**定义补齐（本轮 CMD-8 重读）**：

- `S_low` = 上一拍帧号变化时刻 `(t[i_start−1] − t[0]) × 1000 ms`，与 `S_obs = S_hat = (t[i_start] − t[0]) × 1000 ms` 夹逼出 `S ∈ (S_low, S_obs]`、宽度 `U = S_obs − S_low`（`S_OBSERVABILITY.md:52-59`，本轮亲读；`:61-63` 明写只给区间、不给点估计、`S = S_obs` 属无证据插补）。
- **目标命题 P** = 「对声明覆盖的每条真实事件，`C − S ≤ 50.0 ms`，且保存的是 `STALL_EVENT_DEFINITION.md:177` 要求的上下文（主线程 EIP/RIP 虚拟地址、模块偏移、前 5 层调用栈指针）」（`_dD_PHYSICAL_S_ALIGNMENT.md:120`，本轮亲读）。
- **目标①** = D-30 的「停滞期间的机制证据」目标；`RULING_D30.md:30`（本轮亲读）明写 `missedReal=0` 只证候选覆盖、未证正确线程上下文在 S 后 50ms 内保存，物理 S 与 C 仍未知；`:60`（本轮亲读）D-13 实现执行继续 PAUSE、目标①机制挂账保留。
- 清单 `:134` 明写「只列观测量名称、口径与精度要求；不含任何真实采样 API、不含任何获取手段 / 探针设计 / 注入方案 / 代码；未获取任何新观测量」。本件同样不写任何真实采样 API 或获取手段，不触碰 D-13。

**独立复核 D（L1，verdict = partial → unconfirmed）**：题给材料载复核 `_verify_D_hash.py` / `_verify_D_recompute.py` / `_verify_D_secondary.py` / `_verify_D_claims.py` 统计层 V1–V17、S1–S4、T1–T8 输出（本轮亲读 `_verify_D_out.txt:1-17`、`_verify_D_out2.txt:1-11`、`_verify_D_out3.txt:1-29`），5 个 `_dD_` 交付件 SHA/字节与回件一致、7/7 上游 `OK=True`、禁词 5/5 CLEAN、`git status` 只见新文件。本轮未重跑。崩点（`_verify_D_out3.txt`，本轮亲读）：

1. 结论层不是实跑层：`:7-10` T3 实测 `_dD_check.py` B3 块 `computed=0 literal_prose=12`、B4 块 `computed=0 literal_prose=10`；「证明最小新观测量集 O1–O4」「两个不等式」「C 是第二独立阻断」是打印文字命题，零确定性计算；有跑数支撑的只有描述性统计。
2. O1 精度算术错且跨命题引用：`:16-18` T5、`_dD_PHYSICAL_S_ALIGNMENT.md:126` 称两个 ≤1ms「合计 ≤ 2%」。本轮 CMD-3 实跑输出 `1ms/50ms = 2.0 %`、`(1+1)ms/50ms = 4.0 %`、`(1+1+1)ms/50ms = 6.0 %`、`O1+O2+O3 worst 5ms/50ms = 10.0 %`。同格又写「≤ :190 的 20ms 安全裕量」，而 `:111` 自己声明 `:190` 与 S 正交、`STALL_EVENT_DEFINITION.md:190`（本轮亲读）原文是「从帧停滞被检测到…端到端延迟 <50ms（安全裕量 ≤20ms）」。**本件对这份精度要求的处置 = 登记算术否证并搁置，不采纳、不自行修正、不判已验**。
3. 交付件内部自相矛盾：`_dD_check_out.txt:12`（本轮亲读）= `U > 48.000 ms : n= 62`，同件 `:19` = 「62 在本轮重算的任何门限上都不对应」；主件 `:72` 与回件 evidence 却写「62 对应 U>48ms」。上游另有 `S_OBSERVABILITY.md:171`（56）与 `S_UNCERTAINTY.md:126`（62）的冲突。**56/62 后续计算该用哪个 = 未定，成因未验，本件不择一判真**（§8 待裁决项）。
4. 未验写成肯定标签：主件 `:47`（本轮亲读）「其余 26640 条是正常慢帧/其它游程」——`28317−1677=26640` 是减法可得，但「正常慢帧」是机制定性，`CRITERIA_COMPARE.md:396` 与 `RULING_D30.md:54`（本轮亲读）明写语料无法区分；§5 `:138-146` 未含此项。
5. P 的覆盖母体从未声明：主件 `:120,122,130`（本轮亲读）讨论「声明覆盖的每条真实事件」「最小集」，但 §1–§4 结论未显式声明覆盖母体；4 条 `startTick=0` 事件可被静默排除，「最小性」相对未定覆盖域不闭合。
6. 数字「碰巧对」：`_dD_align.py:288-289`（本轮亲读）把 `len(real)`（=1681）当作「d_final>=100 中的真实事件数」打印，未做集合交；`_verify_D_out3.txt:1-3` T1 独立算出 `1704 / 1681 / 23` 确认结论正确，但交付脚本本身未验证。
7. 措辞升级：主件 `:90/:92` 标题用加粗「已证明不合规」，上游 `CRITERIA_COMPARE.md:35` 只写「不合规方向」、`:219` 写「不是 `:177` 的合规判定」。
8. 全部数字锚定单一上游窗口过滤（复核 `_verify_D_secondary.py` 配套实跑：manifest 正则命中 97 行去重 97 键、按「有帧号变化」筛到 64 窗）；母体 A 的 `28317 / 2.511 / 4.145` 与 B⊆A 都依赖该继承口径，换窗集即变，本轮与被核件均未独立重推窗口选择。

**边界登记（措辞扫描，非语义确证）**：L2 文件 `_dD_PHYSICAL_S_ALIGNMENT.md:60,65,88,141`（本轮亲读 `:141` 明列逐事件物理 S 未验）、`:146`（工程可行性/方案批准未实跑）、`_verify_D_out3.txt:26` 措辞扫描显示「可行」2 次均在未验语境。复核据此登记「没有把 S_hat 当物理 S」「没有把低误报率外推成方案可行」——这是**文本措辞层面的登记**，不是本轮对语义/工程的实跑确证。

## 6 四份复核回件

**本轮实算命令与逐行 stdout（L3，完整可复跑，指纹不手抄）**。

CMD-1（7 个题给上游指纹，完整期望值写在命令内）：

```
python -I -X utf8 -c "
import hashlib, os
exp = {
 'D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md': ('4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726', 48343),
 'D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/CRITERIA_METRICS.json': ('7e2533eabf795e8aa0063a16ee875d95742880dcefab55d596cfc5aa6e7f958b', 17926),
 'D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_cost_quota_data.json': ('e6c26896319acb0387f06384665d5db3668e0f15e29f7328cac97f4931c03cac', 111044),
 'D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt': ('f0177d2cbafdb4dbd388d6b38b97d14ae73688f36f58df4f0fff7edc31a59b66', 5088),
 'D:/Project/ra2-campaign-forge/lead/d30_ruling_20261106/RULING_D30.md': ('d5afc90c50bbf57be1e58bf9000b1940392337b6c57a444e3b084fe57983d04f', 13197),
 'D:/Project/ra2-campaign-forge/lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md': ('ed8951e72bd61cd322b1687c4496ec9fc0e8a362c1425d4020901228d885a001', 27271),
 'D:/Project/ra2-campaign-forge/lead/dstart_observable_20261107/S_OBSERVABILITY.md': ('1d90325ca899c0611ac03dd49a6fb07ede4e21cde2062a5a793a7ea694c9da29', 20133),
}
for p,(h,b) in exp.items():
    if not os.path.isfile(p):
        print('MISSING', p); continue
    data = open(p,'rb').read()
    gh = hashlib.sha256(data).hexdigest(); gb = len(data)
    print(p.split('/')[-1], 'SHA256 =', gh, 'bytes =', gb, 'MATCH =', (gh==h and gb==b))
"
```

stdout（逐行原样）：

```
CRITERIA_COMPARE.md SHA256 = 4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726 bytes = 48343 MATCH = True
CRITERIA_METRICS.json SHA256 = 7e2533eabf795e8aa0063a16ee875d95742880dcefab55d596cfc5aa6e7f958b bytes = 17926 MATCH = True
_cost_quota_data.json SHA256 = e6c26896319acb0387f06384665d5db3668e0f15e29f7328cac97f4931c03cac bytes = 111044 MATCH = True
_dtrigger_supplement_out.txt SHA256 = f0177d2cbafdb4dbd388d6b38b97d14ae73688f36f58df4f0fff7edc31a59b66 bytes = 5088 MATCH = True
RULING_D30.md SHA256 = d5afc90c50bbf57be1e58bf9000b1940392337b6c57a444e3b084fe57983d04f bytes = 13197 MATCH = True
STALL_EVENT_DEFINITION.md SHA256 = ed8951e72bd61cd322b1687c4496ec9fc0e8a362c1425d4020901228d885a001 bytes = 27271 MATCH = True
S_OBSERVABILITY.md SHA256 = 1d90325ca899c0611ac03dd49a6fb07ede4e21cde2062a5a793a7ea694c9da29 bytes = 20133 MATCH = True
```

CMD-2（4 个复核对象指纹，完整期望值写在命令内）：

```
python -I -X utf8 -c "
import hashlib, os
objs = {
 'A': ('D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_dA_design.md', 'd5d487a7792da6ce89e143faa05727a4fe484cb66b400622c02511230770e0df', 20819),
 'B': ('D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_dB_anchor_recompute_out.txt', '3e9588ce1def2ebc5b9ad77a3ce242b47bcada4ae1ab1bc4ea606775edd40807', 14479),
 'C': ('D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_dC_out.txt', 'a0deb34a4aed83efe3d0b80dfff4f05eb28eeec5fac5613ff49316fd8081337a', 13473),
 'D': ('D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_dD_PHYSICAL_S_ALIGNMENT.md', 'bb61eedbddea61e9ffcb1ac8981dadd8b3ee0fb12c715ccb3e600ca78c50fac1', 18262),
}
for k,(p,h,b) in objs.items():
    if not os.path.isfile(p):
        print(k, 'MISSING', p); continue
    data = open(p,'rb').read()
    gh = hashlib.sha256(data).hexdigest(); gb = len(data)
    print(k, p.split('/')[-1], 'SHA256 =', gh, 'bytes =', gb, 'MATCH_REVIEW =', (gh==h and gb==b))
"
```

stdout（下列四行即各复核回件「铁律 9」行的实算来源）：

```
A _dA_design.md SHA256 = d5d487a7792da6ce89e143faa05727a4fe484cb66b400622c02511230770e0df bytes = 20819 MATCH_REVIEW = True
B _dB_anchor_recompute_out.txt SHA256 = 3e9588ce1def2ebc5b9ad77a3ce242b47bcada4ae1ab1bc4ea606775edd40807 bytes = 14479 MATCH_REVIEW = True
C _dC_out.txt SHA256 = a0deb34a4aed83efe3d0b80dfff4f05eb28eeec5fac5613ff49316fd8081337a bytes = 13473 MATCH_REVIEW = True
D _dD_PHYSICAL_S_ALIGNMENT.md SHA256 = bb61eedbddea61e9ffcb1ac8981dadd8b3ee0fb12c715ccb3e600ca78c50fac1 bytes = 18262 MATCH_REVIEW = True
```

CMD-3（百分比/不确定度算术，完整命令）：

```
python -I -X utf8 -c "
b = 50.0
print('1ms/50ms =', round(100*1/b,4), '%')
print('(1+1)ms/50ms =', round(100*2/b,4), '%')
print('(1+1+1)ms/50ms =', round(100*3/b,4), '%')
print('O1+O2+O3 worst 5ms/50ms =', round(100*5/b,4), '%')
print('1621/1681 =', round(100*1621/1681,6), '%')
print('117/1681 =', round(100*117/1681,6), '%')
print('66/1681 =', round(100*66/1681,6), '%')
"
```

stdout：

```
1ms/50ms = 2.0 %
(1+1)ms/50ms = 4.0 %
(1+1+1)ms/50ms = 6.0 %
O1+O2+O3 worst 5ms/50ms = 10.0 %
1621/1681 = 96.430696 %
117/1681 = 6.960143 %
66/1681 = 3.926234 %
```

CMD-4（写域状态）：

```
git -C "D:/Project/ra2-campaign-forge" status --porcelain -- lead/dtrigger_round2_20261107/CRITERIA_ROUND2.md
?? lead/dtrigger_round2_20261107/CRITERIA_ROUND2.md
git -C "D:/Project/ra2-campaign-forge" status --porcelain -- lead/dtrigger_round2_20261107/
?? lead/dtrigger_round2_20261107/
```

CMD-5（8 个复核落盘件指纹；回答「复核回件本身的文件名/路径/指纹在哪」）：

```
python -I -X utf8 -c "
import hashlib, os
files = [
 'D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_verify_A_out.txt',
 'D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_verify_B_out.txt',
 'D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_verify_C_rerun_stdout.txt',
 'D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_verify_D_out3.txt',
 'D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_verify_A_recompute.py',
 'D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_verify_B_recompute.py',
 'D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_verify_C_recompute.py',
 'D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_verify_D_claims.py',
]
for p in files:
    if not os.path.isfile(p):
        print('MISSING', p); continue
    d = open(p,'rb').read()
    print(os.path.basename(p), 'SHA256 =', hashlib.sha256(d).hexdigest(), 'bytes =', len(d))
"
```

stdout：

```
_verify_A_out.txt SHA256 = 145d4fa12e0e618f859c8f98305034d0ddb2952ae47b668e7a6a4c37290ca3b7 bytes = 11204
_verify_B_out.txt SHA256 = 4ee6a6b78d80a336c3431a6f71d9f5a77fec93ef65b7a4c642a49b669368c107 bytes = 7229
_verify_C_rerun_stdout.txt SHA256 = c3c6f57b919666fcd1d63ba69cd8154fe3df9cf9d420fffd4b5fecac5b29be15 bytes = 39141
_verify_D_out3.txt SHA256 = 0e5e84331b2126bd487b526c71095f432303974cdc3960b28794c32807bef84a bytes = 3352
_verify_A_recompute.py SHA256 = 5d906aa00069a4b9d484221db37368efe9cb83930cfeee85a4b0c5c53124fd4e bytes = 36794
_verify_B_recompute.py SHA256 = 11246dce64d51923e21bf5fba52e659c98926cac0c4e5bb03fcca00d5ecb6bc7 bytes = 14966
_verify_C_recompute.py SHA256 = 7c11d6154f76bf34b9271beeca95061d637e1455dc59a2e9e76cd8c136ff9026 bytes = 5114
_verify_D_claims.py SHA256 = 76bba8ccd2534acaefe88303b9e1c3785f7a2833e4a5d1f42881f796c1899a1e bytes = 4698
```

**注意**：上面 8 个指纹是**复核落盘输出件/脚本**，不是「复核回件」本身。`verdict = partial` 出自 L1 题给材料的 `confirmation.verdict` 字段；题给材料未把四份复核回件作为独立落盘文件提供，故「回件本身的文件名/路径/指纹」在本轮**未取得，记为未验**。CMD-2 的四个对象是各复核的**被核主产出**，不是回件。

CMD-6（写域清单）：

```
python -I -X utf8 -c "
import os
d = 'D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107'
names = sorted(os.listdir(d))
print('entries =', len(names))
print('CRITERIA_ROUND2.md present =', 'CRITERIA_ROUND2.md' in names)
for n in names:
    if n.startswith('CRITERIA_'): print('CRITERIA_PREFIX:', n)
"
```

stdout：

```
entries = 47
CRITERIA_ROUND2.md present = True
CRITERIA_PREFIX: CRITERIA_ROUND2.md
```

CMD-7（检索落盘件是否记录 `verdict`/`partial`）：

```
python -I -X utf8 -c "
import os
d = 'D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107'
hits = []
for n in sorted(os.listdir(d)):
    p = os.path.join(d, n)
    if not os.path.isfile(p): continue
    try:
        t = open(p, 'r', encoding='utf-8', errors='replace').read()
    except Exception as e:
        continue
    c = t.count('verdict')
    cp = t.count('partial')
    if c or cp: hits.append((n, c, cp))
print('files_with_verdict_or_partial =', len(hits))
for n, c, cp in hits: print(n, 'verdict=', c, 'partial=', cp)
"
```

stdout：

```
files_with_verdict_or_partial = 3
CRITERIA_ROUND2.md verdict= 12 partial= 15
_dD_align.py verdict= 2 partial= 0
_verify_A_recompute.py verdict= 1 partial= 0
```

CMD-8（定义行重读）：`python -I -X utf8 -c "…逐行打印…"` 输出 `S_OBSERVABILITY.md:52-59` 的 `S_low = (t[i_start-1] - t[0]) × 1000.0 ms`、`U = S_obs - S_low`、`S ∈ (S_low, S_obs]`；`_dD_PHYSICAL_S_ALIGNMENT.md:120` 的 P 定义；`RULING_D30.md:30` 的目标①定义（原文见 §5「定义补齐」，本轮亲读）。

### 复核 A · 新判据族（verdict = partial → unconfirmed，L1）

被核对象 SHA256 = d5d487a7792da6ce89e143faa05727a4fe484cb66b400622c02511230770e0df，字节数 = 20819

对象 `lead/dtrigger_round2_20261107/_dA_design.md`（CMD-2 实算）。题给材料载复核 `_verify_A_recompute.py` → `SUMMARY PASS=54 FAIL=1`（`_verify_A_out.txt:124`，本轮亲读）；数值层载逐格复现（L1/L2，本轮未重跑）；结论层三处越界详见 §2。调查 A 自报的铁律 9 行指向上游 `CRITERIA_COMPARE.md`（`_dA_check.txt:17`），不是本轮主产出；本行按题给 `confirmation.sha256Line` 对象实算。

### 复核 B · §3.2 统一锚补算（verdict = partial → unconfirmed，L1）

被核对象 SHA256 = 3e9588ce1def2ebc5b9ad77a3ce242b47bcada4ae1ab1bc4ea606775edd40807，字节数 = 14479

对象 `lead/dtrigger_round2_20261107/_dB_anchor_recompute_out.txt`（CMD-2 实算）。题给材料载复核 `_verify_B_recompute.py`（exit=0，stderr 0 字节）得 12 格逐值相同、`A_ok/B_ok/C_ok/D_ok=True`（`_verify_B_out.txt:68`），本轮未重跑。崩点见 §3。

### 复核 C · 塌陷归因（verdict = partial → unconfirmed，L1）

被核对象 SHA256 = a0deb34a4aed83efe3d0b80dfff4f05eb28eeec5fac5613ff49316fd8081337a，字节数 = 13473

对象 `lead/dtrigger_round2_20261107/_dC_out.txt`（CMD-2 实算）。题给材料载复核算数核心逐项吻合、但整份 verdict 仍为 `partial` → **unconfirmed**；证据链与结论范围存在漏洞，详见 §4。调查 C 自报的铁律 9 行指向上游 `_cost_quota_data.json`（`_dC_out.txt:150`）；本行按题给 `confirmation.sha256Line` 对象实算。

### 复核 D · 物理 S 可观测量对齐（verdict = partial → unconfirmed，L1）

被核对象 SHA256 = bb61eedbddea61e9ffcb1ac8981dadd8b3ee0fb12c715ccb3e600ca78c50fac1，字节数 = 18262

对象 `lead/dtrigger_round2_20261107/_dD_PHYSICAL_S_ALIGNMENT.md`（CMD-2 实算）。题给材料载复核描述性统计全部吻合；结论层「硬阻断」「最小集」「两个不等式」是打印文字命题（`computed=0 literal_prose=12/10`）、O1 精度算术 2% vs CMD-3 实算 4%/10%、`:19` 与 `:12` 自相矛盾、覆盖母体未声明、「已证明不合规」措辞强于上游，详见 §5。调查 D 自报的铁律 9 两行指向上游 `CRITERIA_COMPARE.md` 与 `S_OBSERVABILITY.md`（`_dD_PHYSICAL_S_ALIGNMENT.md:15,18`）；本行按题给 `confirmation.sha256Line` 对象实算。

**四份 verdict 汇总（L1）**：A `partial`、B `partial`、C `partial`、D `partial`；无 `confirmed`、无 `refuted`。四项结论一律 **unconfirmed**，不得升格。各回件自报 `ranCommands`（A 35 / B 30 / C 17 / D 12；调查件 40 / 14 / 37 / 17）在本撰写轮**未验**（复核 D 亦指出 `ranCommands=17` 与「交付末尾再次复核 7/7 OK」在交付件里找不到）。交付件落盘后如何处置、谁重跑哪些脚本、什么条件下允许升格，本件**不作规定、记为待裁决**（§8）。

## 7 未验项（单独节，不并入 §2–§6 任何结论）

**A 维（L1 题给 U1–U8，`_dA_out.txt:275-283`，本轮亲读）**：U1 物理 S 微秒点估计 / `:177` 严格闭环证明；U2 4 条 `startTick=0` 的 e；U3 `:190` 端到端延迟、`:191` 累计判定耗时、Q5 四项扰动；U4 内部状态旗标；U5 任意实值函数型谓词的信息论级不可判定性（1µs 精确签名 `LB1=0`）；U6 保存动作是否生效 / 跨硬件外推；U7 字母表边界 `0.05/0.5/2/5ms` 与 `S4/M6` 的超参敏感性；U8 配额先到先得仅离线模拟、窗边界截断。复核追加：在线物理 S / 在线工程可行性未做（`_verify_A_out.txt:112,122`）；`_dA_probe_out.txt:60` 首拍游程措辞与 `e_none=64 D_none=128 runs_with_e_but_no_D=64` 不符。

**B 维（L2 `_dB_anchor_recompute_out.txt:148-154`，本轮亲读）**：①物理 S 精确 waitAfterS，全部 wait 是 S_hat 锚下界；②逐游程代入各自 og/e 的实测 `+e>50` 未跑；③Q5 四项全未验（`RULING_D30.md:22,78`）；④4 条 `startTick=0` 事件的物理 S 与总时长不可判定（`S_OBSERVABILITY.md:191`）；⑤§7 其余各项（保存负担/配额资源、内部旗标、跨窗连续时序、全 26 档延迟分布逐档重跑、工程可行性/修复收益/方案批准）未实跑。复核追加：调查件 4 次实跑 / `ranCommands=14` 无法由落盘件推出；两个 `-clean` 档缺独立同 id 实测，是否补、由谁补未定。

**C 维（L2 `_dC_out.txt:132-138`，本轮亲读）**：①物理 S 不可测、相对 S 的严格 waitAfterS 未验；②`results/nofalse/upper` 是否忠实于 `1125992` 点 / `28381` 游程原始重放未验；③「误触发抢占 / 判据自身漏检」因果标签背后的模拟器语义未验；④`C3-r4-clean / C3-r8-clean / C3-r2` 逐触发延迟分布未验；⑤真机 / 活进程 / 采样类证据按铁律禁止，未验；⑥上游 `CRITERIA_COMPARE.md:338` 括注 7 档（42 格）作者原意未验。

**D 维（L2 `_dD_PHYSICAL_S_ALIGNMENT.md:138-146`，本轮亲读）**：①真机 / 活进程任何量；②物理 S 逐事件点值、实际保存完成时刻 C、`:190` 端到端延迟、Q5 四项、内部状态旗标；③既有探针本轮未重跑（会覆写只读件），「可复现」均指题给材料自报；④56/62 差异成因、后续计算该用哪个；⑤`AUDIT_S_OBSERVABLE_20261107.md:107` 失效行号的原始指向（该文件实测 152 行、无 §7.3）；⑥n=1681 与 n=1737 同口径对照（裁决边界禁止）；⑦任何判据工程可行性、修复收益、方案批准；目标①机制挂账不解除。复核追加：`ranCommands=17` 与「末尾再次复核 7/7」无输出可核；窗口集选择未独立重推；O1/O2/O3 规格无实跑支撑；P 的覆盖母体未声明；O5 条件是否成立、由谁判定未定。

**撰写轮新增未验**：本轮未重跑任何调查/复核脚本（会覆写既有件），只做 §6 的 CMD-1..CMD-8（指纹、算术、检索、状态、只读行读取）；四份复核的 `ranCommands`、调查件自报的退出码与运行次数、§6 之外的其它交付件指纹串（题给材料中出现的截断 hash）本轮**未逐一实算，记为未验**；四份复核回件本身的落盘路径/指纹未取得；本轮未做任何真机、活进程、在线或工程可行性验证；未验项一律不并入结论，也不把任何「未验」改写为「已验」。

## 8 结论（只摊开比较，不选方案）

1. **四项复核 verdict 全为 `partial`（L1 题给材料）**，故 A「三维不可兼得且非调参可绕过」、B「12 格在统一锚下可补算、无需写不可补算」、C「156 格分解 + 54/71 归因 + §9.7 越线」、D「硬阻断判定 + O1–O4 最小集」四项结论一律标注 **unconfirmed**；不升格、不合并成肯定性裁决，也不由本件判定「是否需要用户裁决」。
2. **读数层（L1/L2 载有；本轮 L3 只实算 §6 的指纹与 7 个百分比/计数除法，未重跑任何调查/复核脚本）**：A 的 11 档三维表、4 档校准、配额理想 `26/73/117`、`W5=66`、`e>50=56 / e 未验=4`；B 的 12 格 `5/29, 24/24, 24/24, 16/16, 16/16, 15/15`（**S_hat 锚下的 wait 计数**）；C 的 `156` 格分解/链式违例 0、`54+102=156`、`71/73/42` 与 2 个 `C3-N16-r2` 格；D 的两套观测侧母体统计 `28317 / 2.511 / 4.145 / 488.616` 与 `1677 / 2.515 / 111.495`、`U>50=56 / U>48=62`（**56/62 内部措辞相反、成因未验、不择一判真，见第 4 点**）、`B/A=5.9222%`、`11.26×`。以上全部并列摊开，不写「已复现」、不作方案背书。
3. **结论层的适用域（不得越过）**：`33.2279%` 不是任意谓词的查准率上界（复核 A 的 `precision=0.999404` 反例，`_verify_A_out.txt:119`）；`1621/1681` 是固定外部采样器下的离线可证数，不是物理 S / 在线工程的普遍硬界（`_verify_A_out.txt:111-112`；`S_OBSERVABILITY.md:173-179`；`RULING_D30.md:30`）；`+e>50` 六格不携带关于 e 的信息（`min wait=66.334ms`）；156 格分解式是减法恒等式；`O1–O4` 的「最小/必要」是文字命题而非机械证明（`_verify_D_out3.txt:7-10`）；O5 不属最小集、是否启用未定；O1 的「2%」被 CMD-3 实算否证、搁置不采纳。
4. **待裁决项（只登记，不判「已收敛」「不需裁决」「冲突为空」）**：①A 的「任意谓词普遍上界」与 D 的「离线不可观测只阻断肯定性合规确证」在结论层的张力；②C §9.7「高档 ≥100ms」与 B 的 `C2-abs-P95x2 5/29`、复核 C 的「13 档仅 4 档全部 ≥100ms」之间的判据级读法分歧；③`_dD_check_out.txt:12` 与 `:19` 的 56/62 内部措辞相反、上游 `S_OBSERVABILITY.md:171`（56）与 `S_UNCERTAINTY.md:126`（62）冲突、后续计算该用哪个；④§3.2 台账「未验」是否、按哪个锚口径补算、两个 `-clean` 档是否补独立实测；⑤四项 unconfirmed 结论的下一步（要不要裁决、裁决哪一项、谁重跑哪些脚本、升格条件、交付件落盘后处置）——本件**无授权、无责任人、无升格条件，全部记为待裁决/未验**。`needsRuling` 与 `conflicts` 属工作流回执字段，本件不填写、不推定其值；是否与 D-30 执行 PAUSE 相容、凭什么判张力收敛，本件不裁定。
5. **档数口径（并列登记，不合并）**：11 档 = A 的 D1–D5 新判据；4 档 = A 的 CAL 校准（不参与新判据比较）；15 档 = A 主表 11+4；26 判据 = C 的 `_cost_quota_data.json` 判据全集（×6 情景 = 156 格）；13 档 = C 的 C2/C3 全族零抢占格所涉判据；7 档 = `CRITERIA_COMPARE.md:338` 括注的高档名单（×6 = 42 格）。「全局最佳」按哪一批档算、要不要算，无清单、未验。
6. **不选定任何方案**：本件只把上述读数与四项观测量清单并列摊开。不指定 k 档、不指定谓词族、不指定锚口径为批准口径、不指定 N=1/3/5 为实际设计参数、不把 O1–O5 视为已获授权的新观测；`RULING_D30.md:32,38,62,66-67` 的执行 PAUSE、离线预算情景限定、不改口径/需求原文、不得由误报率或覆盖率外推方案可行，全部继续有效。
7. **红线不变**：口径 B 未改；`STALL_EVENT_DEFINITION.md:177`、`:190`、`:191` 未改、未判为已闭合；真机、活进程、任何真实采样 API、任何获取手段均未使用或建议；未改台账、未改裁决书、未改只读母本与既有件；未 commit、未 push；本件是唯一写域内同一文件（CMD-4、CMD-6）。所有工程可行性、修复收益、在线实现、物理 S/C 逐事件点值、机制挂账解除，一律保持 **未验**（见 §7）。
