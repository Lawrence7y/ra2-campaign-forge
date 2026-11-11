# E3 栈采样候选件 · 独立安全评审（REVIEW）

- 评审方：独立安全评审（非执行方）；评审时刻 2026-11-12
- 被评审对象：`lead/re_d13_ruling_20261112/e3_stack_sampler_candidate.py`
- **钉版指纹（本评审仅对以下哈希负责）**：
  - 候选件 sha256 = `f281cfba1f8cfe791b21266d29bff4582461db71b90c8130a3a8458424d895d6`（25,721 B / 592 行，CRLF；评审开始与结束两次实算同值，期间未被再改动）
  - 母本 probe_v2 sha256 = `6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9`（48,630 B）＝任务书给定值 **EXPECT-MATCH**
  - 母本 earlyclose sha256 = `2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1`（9,061 B）＝任务书给定值 **EXPECT-MATCH**
- 评审过程异常登记：评审首次读取候选件得到 **517 行旧修订版**（22 项检查、无 importlib 复用段）；复读得到 **592 行现行版**（30 项检查）并与对方存档 stdout 吻合。作者 evidently 在评审窗口内更新过文件。本评审一律以钉版哈希的 592 行版为准；**此后任何再改动即告失效，须重审**。

---

## 0 · 总判

**VERDICT = PASS_WITH_REQUIRED_FIXES**

授权边界（R1，安全生命线）成立：`--live` 真拒、默认路径零真机、`bind_real_ops` 无任何调用点、母本 import 静态核验为惰性。死锁防护（R2）代码级 D1–D4 成立，但存在 2 个**真机放行前必须修复的潜伏缺陷**（ctypes restype 导致挂起失败被当成功；dwSize 未设导致 Thread32First 必败）与 3 处「声明与实现不符」（D6 单线程闸未实现、D5 无前置校验、R6/R5 缺显式声明）。离线单测 30 项经本人独立复跑**逐字节复现**。

---

## 1 · 逐条结论表

| 评审项 | 结论 | 一句话依据 |
|---|---|---|
| R1 授权边界 | **PASS** | `--live` 显式拒绝（rc=3、stderr 五行引 D-15/D-31 Q4）；全文件无 `bind_real_ops()` 调用点；导入期零副作用；selftest 期间唯一执行的第三方代码=母本 import，已静态核验顶层惰性 |
| R2 死锁防护 D1–D6 | **PASS_WITH_REQUIRED_FIXES** | D1/D2/D3/D4 代码级成立且有测试；**D6 单线程闸未实现**（死参数）、**D5 无挂起前校验**、2 个真机潜伏缺陷（MF-1/MF-2）、ResumeThread 返回值不校验 |
| R3 离线单测 | **PASS（复现成立）** | 本人独立实跑 EXITCODE=0、30 项 0 失败，stdout sha256 与对方存档**逐字节相同**（`460cb127…BEB74`）；C1/D 组语义真实；残余覆盖缺口见 §4 |
| R4 冻结母本关系 | **PASS** | 两母本 sha256 实算与任务书给定值一致（零字节改动）；importlib 复用为**真实实现**（sha 预检→import→属性/G_FRAME 一致性验证），非仅注释；「复用深度=import 级、非调用级」不算偏离计划 |
| R5 反身护栏 | **需修改（缺口坐实）** | 「分列」仅注释级：②地址（G_EXITSTATE）确为零读取、零写进程、零写盘（结构性成立），但**无任何输出分列机制、无与②读数的时窗错峰机制**（当前无输出通道，属空真）；line 55 注释「只登记不分列」与 C6「分列」措辞自相矛盾 |
| R6 能力边界声明 | **需修改** | 「真机路径未授权，故意不实现」在案；但全文**无**「死锁防护未经真机独立验证」、**无**「离线单测通过≠真机可行」的显式声明（grep 零命中）；无过度归纳（未发现把离线通过说成真机可行的句子） |

---

## 2 · R1 授权边界（最高优先）——详细证据

**R1-1 `--live` 真拒。** 路由在所有分支之前：`e3_stack_sampler_candidate.py:582-583`（`if "--live" in argv: return main_live_guard(argv)`）——即便同时给 `--selftest` 也先拒绝。拒绝体 `e3_stack_sampler_candidate.py:568-577`：stderr 五行，逐字含「拒绝执行：真机发射 / 活进程采集未获授权」「D-15 已裁决原文…」「D-31 Q4「真机/活进程须当轮明示」」「用户 2026-11-12 仅明示「D-13 选 c」…**未**就真机发射明示」，返回码 **3**。本人实跑 stderr 捕获全文：`_review_selftest_stderr.txt:1-5`；rc=3 由本人 stdout 第 41 行（`AUTH-a … rc=3`）证实。**通过。**

**R1-2 selftest 之外无触真路径。** 危险 API 全部收拢在 `bind_real_ops()`（`e3_stack_sampler_candidate.py:94-110`：OpenProcess :100、SuspendThread :107、GetThreadContext :109）与 `_real_read_mem`（:113-121，ReadProcessMemory :117）之内。**全文件 grep 无 `bind_real_ops()` 调用点**（仅 :94 定义）——它在本文件任何路径（含 `--live` 拒绝路径、`main()`）上都不可达。模块顶层只有常量/类/函数定义，`__main__` 守卫在 `e3_stack_sampler_candidate.py:591-592`；导入即执行面=零。`OPS` 初始为空 dict（:91），默认 `--selftest`（:509：`"--selftest" in argv or not argv`）只绑 stub（:355、:413 等 `mk_ops` 纯 Python dict）。无 `WriteProcessMemory`（grep 零命中）。**通过。**

**R1-3 selftest 期间执行的第三方代码=母本 import，静态核验为惰性。** `load_mother_probe()`（`e3_stack_sampler_candidate.py:307-334`）在 selftest 中 `exec_module` 执行母本顶层（:535）。核验母本 `_drive_c2_x_probe_v2.py`：顶层仅有 `k32 = WinDLL` + restype/argtypes **赋值**（母本 :80-90，属性赋值不调用）、`OPS = {}`（母本 :240）、函数定义（`bind_real_ops` 定义于母本 :252）；其唯一调用点母本 :1024 位于 `main()` 内（母本 :1013 def），而 `main()` 仅在母本 :1045-1046 `if __name__ == "__main__"` 下执行——候选件以模块名 `e3_mother_probe_v2` 导入（候选件 :326），守卫不触发。候选件对母本**只 hasattr 不调用**（:539-540）。C5-import 组测试证实母本 `OPS` 导入后 len=0（本人 stdout :37）。**通过**——但此保证依赖「母本顶层无副作用」这一静态事实，母本若被改（哪怕合法更新）即失效；候选件已用 sha 预检对冲（:322，指纹不符即拒绝导入），对冲正确。

**R1-4 潜伏缺陷（现不可达，真机放行前阻塞）。** `bind_real_ops()` **未设置任何 restype/argtypes**（对照母本 :80-90 有现成范式）⇒ ctypes 默认 c_int 返回：`SuspendThread` 失败返回 **−1** 而非 0xFFFFFFFF ⇒ 候选件 :220 的判据 `prev == 0xFFFFFFFF` 在真机路径**永不命中** ⇒ 失败被当作成功（−1 不满足 `is None`、不满足 `==0xFFFFFFFF`、不满足 `>0`）⇒ `suspended_by_us = True`（:227）后对**根本没挂起的线程**取上下文、走栈（数据竞态），finally 再对未挂起线程 Resume。同理 `OpenThread` 句柄高位为 1 时经 c_int 变负数，`not h`（:214）判空依赖运气。现在该路径不可达（R1-2），**但它正是未来真机放行时唯一的挂起安全判据** ⇒ 列入必改 **MF-1**。

---

## 3 · R2 死锁防护 D1–D6 逐条核实

**D1 逐线程挂→走→立刻恢复 —— PASS。** 采样单元是 `sample_one_thread`（`e3_stack_sampler_candidate.py:207-239`）：单线程挂起→取上下文→走栈→返回，恢复在 finally；`sample()` 逐 tid 串行调用（:265-277）。不存在「全挂再走」路径。

**D2 prev_count 精确还原 —— PASS（附 2 条保留）。** 挂起前记录 `prev = OPS["suspend_thread"](h)`（:219）。prev==0（本件挂起）路径：一次 ResumeThread（:236）使计数 1→0，精确还原。**任务书问点①「prev>0 立刻 resume 是否会把别人挂的线程恢复掉」——不会**：SuspendThread 把别人已挂线程的计数 prev≥1 加 1，一次 ResumeThread 只抵消本件自己的 +1，线程仍以计数 prev≥1 挂着，原持有者的挂起未被释放；:223-226 的语义正确。保留： 两条路径的 `ResumeThread` 返回值**均不校验**（:225、:236）——恢复失败将留下不可见的残余挂起（MF-6）； 自测 stub 把挂起建模为**集合**而非计数（selftest :415-425），无法证明「按差值精确还原」的计数语义（测试保真度缺口，见 §4）。

**D3 try/finally 兜底 —— PASS。** `suspended_by_us` 仅在挂起**确认成功**后置位（:227），故 :220-221 的挂起失败路径正确地不恢复（无可恢复）；成功置位后所有路径（含非 E3Fail 异常）经 finally :232-239 恢复。`sample()` 以裸 `except Exception` 兜住非常规异常并记 `unexpected:*`（:275-276），异常不逃逸。**该路径有专测**：D3-a/b（:488-503，walk_stub 注入 `RuntimeError` → 断言挂起集空、两线程都恢复、错误串 `unexpected:RuntimeError`）——本人实跑 :26-27 均 OK。唯一理论边角：finally 内 resume 的吞异常用 `except Exception`，挂起状态下吃 Ctrl+C（KeyboardInterrupt）时恢复调用本身可能被打断——低优先级，登记不阻塞。

**D4 跳自身/跳 prev>0 —— PASS（附缺口）。** prev>0 跳过分支 :222-226，测试 D-e/f（:453-461，本人实跑 :19-20 OK）。自身线程经 owner-pid 过滤天然排除（`enumerate_threads` :196-201 只收 `th32OwnerProcessID == pid`）。**缺口**：无 `pid == os.getpid()` 守卫——若未来真机路径被传入自身 pid，采样线程会挂起自身所在进程的线程（含自己）⇒ 自死锁（MF-5）。

**D5 挂起前完成初始化 —— 部分成立，需修改。** 结构上 walker 绑定发生于构造期（:186 `self.stack_walker`），先于挂起循环——方向正确。但**无前置校验**：walker 未绑定时每线程仍走「挂起 → `_walk` 内 :252 抛 `E3Fail("walker_not_bound")` → finally 恢复」，即失败发现于挂起**之后**（fail-late），与 D5「挂起任何线程之前完成准备」的原则相悖；真机上这意味着对每个线程白挂一次。符号初始化本体（StackWalk64/SymInitialize）属真机路径，按授权**刻意未实现**（:245、:252 注释），故 D5 现阶段无被违反的实体，但结构保证不到位 ⇒ **MF-4**（`sample()` 起始 fail-fast 校验 walker 可用）。

**D6 双闸 —— 半实现，需修改。** 总闸存在：线程间检查 `(now-t0)*1000 > budget_ms` 即中止（:266-269），中止后无残留挂起（C3-b 实跑 :25 OK）。但**单线程预算从未实现**：`per_thread_ms` 仅出现于常量 :63、形参 :180、赋值 :183（grep 三处，零使用），`_get_context`/`_walk` 内无任何时间检查。后果： 「D6 双闸」名不副实； C3「单次总停顿**硬上限** ≤50ms」实为「线程间软闸」——单线程内 SuspendThread/GetThreadContext 是阻塞 Win32 调用、无超时机制，单线程即可超 50ms 且窗口内无法中止； 闸用严格 `>`：恰好 50.0ms 时**不**中止、会再启动一个线程（边界无测试，C3-c :505-518 只测了 10ms<50ms）。⇒ **MF-3**（实现 per-thread 预算，或如实改文档并把「硬上限」降格表述）。

**R2 重点问点小结**： 挂起后抛异常未恢复的路径——未发现（D3，且有专测）； 0xFFFFFFFF——Win32 语义为**失败、未挂起**，不恢复直接 raise 的意图正确，但真机路径判据失效（MF-1）、stub 路径从未演练该返回值； prev>0 分支——恢复语义安全（见 D2），不误放他人挂起。

---

## 4 · R3 离线单测独立复跑与覆盖判定

**复跑（铁律 3 口径）**：`python -I -X utf8 "D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112\e3_stack_sampler_candidate.py" --selftest`（经写域内 `_run_selftest.cmd` 执行，stdout/stderr 分流落盘）。结果 **EXITCODE=0，30 项检查 0 失败**；本人 stdout 的 sha256 `460CB127BE8EB4A9083D34AEB0E8A2959763E7B731FB9B52D5CA3A1ADC6BEB74` 与对方存档 `_selftest_stdout.txt` **逐字节相同**——独立复现成立，无「报告与实跑不符」。任务书所引「22 项」系旧修订版数字，现行钉版为 30 项，文件自述与实跑一致。

**C1 组 7 项——语义真实。** 被测即「帧号连续 N 秒不变」：段起点帧值/起点时刻在帧值变化时重置（:154-158）；触发需 观测数 ≥ min_obs（:161-162）且 `t - base_t >= n`（:163-165）；同段只报一次（:159-160）；None 读失败不推进/不重置/不判停滞（:150-152），C1-e/f 专测 None 居中不重置且后续仍可触发（:367-372）——与文档语义「读失败不是停滞证据」一致。未测的小项：恰好 `t-base_t == n` 的等号边界（:163 用 `>=`）、多段交替帧的连续重置。

**D 组 6 项——「挂起必恢复」证明力成立但粒度有限。** stub 在 suspend 时把 tid 加入 `state["suspended"]`（:415-418）、resume 时移除（:420-425）——任何「挂了没恢复」都会让该集合非空，D-b/D-c（:448-450）即会 RED；本人实跑该集合为 `set()`（stdout :16）。被覆盖路径：正常、prev>0 跳过、open 失败、预算中止、snapshot 失败、非 E3Fail 异常（D3-a/b）——共 6 类。**粒度限制**： 集合模型不含计数 ⇒ D2「精确还原」不可由本测试证明（建议 stub 改计数模型：resume 使 count−1、count>0 仍算挂起，则 D-f 应断言 21 仍挂起）； `suspend_thread` 失败返回（None/0xFFFFFFFF/−1）路径零演练； resume 失败路径零演练。

**覆盖缺口清单**（任务书点名项的最终答案）：
1. 非 E3Fail 异常仍恢复——**当前版已覆盖**（D3-a/b；旧 517 行版无此测试，作者 evidently 已补）。
2. 预算闸「恰好等于 50ms」——**未覆盖**，且严格 `>` 下该点行为是「再采一个线程」。
3. `suspend_thread` 失败返回路径——未覆盖（与 MF-1 同源）。
4. pid==自身——无守卫也无测试（MF-5）。
5. AUTH 组只断言 `rc != 0`（:551），未断言拒绝文案与返回码 3 本身。

---

## 5 · R4 与冻结母本的关系

- **指纹实算（hashlib.sha256，本人直算）**：probe_v2 `6afe2711…d13b9`（48,630 B）、earlyclose `2e970eec…c2e1`（9,061 B），均与任务书给定值一致 ⇒ **母本零字节改动成立**；候选件内嵌期望值与任务书一致（:67-69）且 selftest C5-mother 两项 OK（本人 stdout :32-33）。
- **importlib 复用为真实实现**：`import importlib.util`（:42）→ `load_mother_probe()`（:307-334，先 sha 预检防母本被改 :322 → `spec_from_file_location` :325 → `exec_module` :331）→ selftest 五项断言（:535-546：导入成功、`tri_read_u32`/`phase_sentinels` 在、母本 OPS 未绑定、`G_FRAME` 0xa8ed84 与母本一致）。**不是复制母本代码**：候选件自己的 OPS 层是新写的采样原语，母本通道未被抄写。
- **判断（任务书问点）**：复用深度=**import 级（一致性验证），非调用级**。这**不算偏离计划**： C5 的硬承诺是母本零字节改动，已实证； 甲案采集原语（OpenThread+SuspendThread+GetThreadContext+StackWalk64 回调）与母本读通道（OpenProcess+ReadProcessMemory 读哨兵）不同构，在真机路径被授权前**本来就不存在可调用的复用对象**； docstring 明写「只 import，不调用」（:313-315、:330），与实现一致，无虚假声明。登记为「复用深度说明」，非缺陷；未来真机放行时若走 StackWalk64 的内存回调，应继续从母本取 `ReadProcessMemory` 封装而非再写一份。

---

## 6 · R5 反身护栏（对目标②读数）

- **已成立的（结构性）**：②地址 `G_EXITSTATE = 0x00A8EDD8` 仅 :55 定义、全文零读取（grep 实证）；无 `WriteProcessMemory`、无任何写盘/写状态代码（采样结果仅在内存 dict、selftest 仅 print）⇒ 本件在当前形态下**不可能污染②读数文件**。
- **缺口（坐实）**：C6 所称「与目标②读数**分列**」（:29）**没有任何代码级机制**——当前根本没有输出通道，「分列」是空真；没有为未来真机输出预置独立文件/目录约定，也没有「采样窗口与②读数窗口错峰/互斥」的任何机制。而 E3 卡 §4 已认定甲案对②为**高反身影响**（挂起目标线程本身会扰动②的读数窗口）——这个扰动本件完全未对冲。:55 注释「本件只登记**不分列**」与 C6「分列」措辞自相矛盾，属文档疵点。⇒ **MF-8**：真机授权前必须落为（a）独立输出文件/目录，与②读数物理分列；（b）采样窗口与②读数的时窗错峰或互斥的显式设计；（c）修正 :55 措辞。

---

## 7 · R6 能力边界声明

- **在案**：授权状态段（:5-12）明写「未解除：真机发射/活进程采集/attach/读活进程内存……须用户当轮明示」；「真机路径未授权，故意不实现」（:245、:252）；「--live 入口显式拒绝执行并给出原因」（:11）；C5「不重试、不强杀」（:27）。
- **缺失（grep「未验/未独立/真机可行」零命中）**：全文无「**死锁防护 D1–D6 仅经离线 stub 验证，未在真机独立验证**」的显式句；无「**离线单测通过 ≠ 真机可行**」的免责句。甲案自述「可能自造死锁」（:20），本件的对冲只经 stub 演练——这句验证状态必须白纸黑字。⇒ **MF-7**。
- **过度归纳扫描**：未发现任何把「离线单测通过」表述为「真机可行/真机已验」的句子。:58 「§532：…N=1.0s 误触率 0」是对既往台账复算的转引（设计依据），不构成真机宣称——可接受，但建议将来真机阶段引用时保留「未验」限定。

---

## 8 · 必须修改项清单（按优先级）

| # | 级别 | 内容 | 证据 |
|---|---|---|---|
| MF-1 | **P0（真机放行前阻塞）** | `bind_real_ops` 为全部 k32 函数补 restype/argtypes（照抄母本 :80-90 范式）；挂起失败判据改为 `prev is None or prev == -1 or prev == 0xFFFFFFFF`。现判据 `prev == 0xFFFFFFFF`（:220）在 ctypes 默认 c_int 下永不命中 ⇒ 挂起失败被当成功 ⇒ 采样未挂起线程 + 对未挂起线程 Resume | `e3_stack_sampler_candidate.py:94-110,220` vs `_drive_c2_x_probe_v2.py:80-90` |
| MF-2 | **P0（真机放行前阻塞）** | `enumerate_threads` 未设 `entry.dwSize`，真 `Thread32First` 将因 dwSize=0 失败/未定义；补 `entry.dwSize = ctypes.sizeof(_ThreadEntry32)`（stub 在测试内代设了 dwSize，掩盖了此缺陷：selftest :396） | `e3_stack_sampler_candidate.py:196-197` |
| MF-3 | P1 | D6 单线程预算未实现（`per_thread_ms` 死参数）；总闸仅线程间生效且严格 `>`；「硬上限 ≤50ms」须降格表述或补实现（单线程内阻塞调用无超时是甲案固有风险，至少如实声明） | `:63,180,183,266-269` |
| MF-4 | P1 | D5 前置校验缺失：`sample()` 起始 fail-fast 校验 walker/context 可用，避免「先挂起后失败再恢复」 | `:247-252` |
| MF-5 | P1 | 加 `pid == os.getpid()` 自采样守卫（防未来真机路径自死锁） | `:255`（sample 无守卫） |
| MF-6 | P2 | `ResumeThread` 返回值不校验（两处）⇒ 恢复失败不可见（残余挂起）；失败须记入 `errors` | `:225,236` |
| MF-7 | P1 | docstring 补两句：「死锁防护 D1–D6 仅经离线 stub 验证，未在真机独立验证」「离线单测通过不构成真机可行结论」 | grep 零命中（§7） |
| MF-8 | P2 | 「分列」机制未实现（当前空真）；真机授权前落独立输出 + 与②错峰/互斥设计；修正 :55 「只登记不分列」与 C6 矛盾措辞 | `:29,55` |
| MF-9 | P3 | 测试补强：stub 改挂起计数模型；补 suspend 失败返回路径、==50ms 边界、AUTH 拒绝文案/码 3 断言 | §4 |

---

## 9 · 边界与未验

1. **本评审全程零真机**：未启动 gamemd.exe / ra2loader / YURI.exe，未 attach，未读任何活进程内存，未运行候选件 `--live`（其本就会拒绝）；仅以 `python -I -X utf8 <绝对路径> --selftest` 实跑一次，另以同口径实算全部指纹（hashlib.sha256）。
2. **被评审对象以哈希钉版** `f281cfba1f8cfe791b21266d29bff4582461db71b90c8130a3a8458424d895d6`；评审期间观测到一次版本更替（517 行→592 行），此后两次实算同值。**结论只对该哈希有效；任何后续改动须重审。**
3. **未验（不可在本轮验证，不得当作已证伪或已证实）**：真机上 D1–D6 的实际死锁防护行为；SuspendThread/GetThreadContext/StackWalk64 真机可行性；≤50ms 停顿在真机的实际分布；甲案对②读数的实际反身幅度；CTYPES restype 修复后（MF-1/MF-2）的行为——均属真机路径，按 D-15/D-31 Q4 须用户当轮明示方可进行。
4. 评审自身的工具残留：`_run_selftest.cmd` 的 rem 注释行在 GBK 代码台下产生一行无害 stderr 噪声（`'命令只跑离线单测…' is not recognized`），不影响 python 命令与落盘内容（EXITCODE=0 来自 python 实跑）；特此登记，非候选件问题。
5. 写域纪律：本评审仅新建 `lead/re_d13_review_20261112/`（REVIEW.md、本人实跑 stdout/stderr、指纹与实跑工具件）；仓库其余路径只读；无 git 操作。

**VERDICT = PASS_WITH_REQUIRED_FIXES**
