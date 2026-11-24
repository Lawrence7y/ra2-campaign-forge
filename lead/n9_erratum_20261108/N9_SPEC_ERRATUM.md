# N9_SPEC_ERRATUM.md — N-9:205「P6 静态 u64 窗口读可闭」勘误汇总件（只登记，不改原件）

- 登记域：lead/n9_erratum_20261108/（唯一写域；本件只登记勘误，不改任何原件）
- 登记日期：2026-11-08
- **状态：unconfirmed**（独立复核 verdict = **partial**，按交付纪律如实标注。partial 不是「反驳半成立」：复核明言反驳主结论本身成立、判 partial 仅因勘误件 §5 下游影响清单漏登记 3 件 + 3 处次要记载瑕疵。本汇总件已把漏登记 3 件并入 §4 清单。）
- 勘误登记件（被核对象）：`lead/n9_erratum_20261108/_er_N9_205_P6_B0CD48_ERRATUM.md`，**SHA256 = 414795407eef7f000baad213db075899513c86c2ee71fbeb3a72e1c5ff95ae73，字节数 = 15794**（本会话 hashlib 实算，与编排方所载、复核回件绑定行三方同值）。
- 铁律遵守：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）、零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / ctypes / OpenProcess / ReadProcessMemory；本会话 3 个脚本全部为磁盘文件只读 + struct 解析）；未 commit、未 push；本会话实跑 `git log -1` = **2657458**（无新提交），五上游目录 + 本写域 git status 全为 `??` 未跟踪。

## 1 目的与边界

1. **目的**：对 N-9 复核件（STATIC_COUNT_SPEC.md）:205 P6 行的前提「静态 u64 窗口读可闭」登记勘误——该前提对两常量**一真一假**：对 `[0x7E1738]` 成立（=0.5，.rdata 文件镜像直读），对 `[0xB0CD48]` **不成立**（.data 节内零初始化尾，文件镜像无字节，值只能运行期产生）。登记动作承接勘误登记件 `_er_N9_205_P6_B0CD48_ERRATUM.md`（下称「勘误件」）与其独立复核回件（下称「复核回件」，verdict=partial），并把复核发现的下游影响清单遗漏补全。
2. **只登记不改原件**：STATIC_COUNT_SPEC.md、spec_static_closure_20261108 两件、_n9_STATIC_COUNT_SPEC.md、PERF_REPAIR_HANDOFF.md、_n11_PERF_REPAIR_HANDOFF.md、DECISION_QUESTIONS.md、_n10_D13D14_CARDS_20261108.md、F8_VISIBILITY.md、W8_STATIC_LOCATE.md、台账一律不动；勘误件本身亦不改（其 §5 清单遗漏由本件 §4 补全，两件并存）。
3. **写域**：本会话新增产物全部落 lead/n9_erratum_20261108/：`_er_report_hash.py` / `_er_report_pe.py`（探件）+ 三份输出 `_er_report_hash_out.txt` / `_er_report_pe_out.txt` / `_er_report_rerun_out.txt` + 本件。指纹：`_er_report_hash.py` = d4d027f31192628fb9213037eef12b2eda5cb5d324a14d04e45f12d12ef019e8 / 3374 B；`_er_report_pe.py` = 4a1e1644d279655b952e2b5375690e684b342a19f05f4ae35904cf8bfe373945 / 6036 B；`_er_report_hash_out.txt` = 10aad68116f373f21d1e716dbdcc0be04d5f49901c782c6878f358c6eab273dd / 3381 B；`_er_report_pe_out.txt` = ac2d247600ab098c98e042359353e29978cf711f4c83a85881ec472c2bcb1a58 / 6908 B；`_er_report_rerun_out.txt` = 73f76c8c69a62db350c27759a50bdd8386f7c6c9dc249891877afd64f2ecd7a9 / 3104 B（与勘误件 `_er_check_b0cd48_out.txt` 存档逐字节一致）。本件自身指纹不入本件（自指不可计算，先例 PERF_REPAIR_HANDOFF.md:132），由回执登记。
4. **证据纪律**：每条论断追到「实跑命令 + 输出」或「文件:行」；本会话拿不到的记「未验」（§6.4）。

## 2 原表述原文与上下文（逐字 + 行号，本会话实读）

**勘误主对象 = STATIC_COUNT_SPEC.md（N-9 复核件）:205**（sha256 = 5b933fe2fcb3cc35c5026cb57b45f29da29c90b67a618346af248744ed3ccdb9，32281 B，本会话实算与编排方指纹一致）：

- **N-9:198**（§6.2 节题，前提的上位表述）：
  `### 6.2 搜索缺口（静态可闭、既有材料未做）`
- **N-9:205**（P6 行，勘误落点）：
  `| P6 | F8 两个 FPU 常量数值（静态 u64 窗口读可闭） | F8V:169/:222 |`

**同件内前提的更早表述**（本会话实读）：

- **N-9:139**：`- §5.1 一次性读取（:162-169）：`[0x887324]` → 视口原点 `[P+0xB0/B4]` → 屏宽高 `[0xB0CE30/34]` → 投影 FPU 常量 `[0xB0CD48]`/`[0x7E1738]`（两个 qword）。`
- **N-9:145**：`- 数值（两个 8 字节 double）未读出：F8V:169「数值本轮未读出，标未验」；F8V:222「规格阶段不需要，实现阶段必读」。静态 u64 窗口读即可闭；本任务按铁律不新增探针，未读（§6.2 P6）。`

**语境**：N-9 §6.1（:187）收「运行期未验边界（永久缺口）」、§6.2（:198）收「搜索缺口（静态可闭、既有材料未做）」，:205 把 P6 归入后者，即判定 P6 不需要运行期、静态窗口读即可闭。

**前提来源考（实读原文，出处件无该前提）**：

- **F8_VISIBILITY.md:169**：`| 4 | 投影 FPU 常量 | `[0xB0CD48]`(double), `[0x7E1738]`(double) | qword×2 | `0x6D21E2 fmul` / `0x6D21EC fadd`（数值本轮未读出，标未验） |`
- **F8_VISIBILITY.md:222**：`3. 投影 FPU 常量 `[0xB0CD48]/[0x7E1738]` 的**数值**未读出（规格阶段不需要，实现阶段必读）；`

F8V 原文只写「未读出 / 标未验 / 实现阶段必读」，**无任何静态可闭断言**。「静态 u64 窗口读即可闭」一语最早见于上游转录件 _n9_STATIC_COUNT_SPEC.md:81（`静态 u64 窗口读即可闭——本任务按铁律不新增探针，未读`），:109 表格行同语（`搜索（静态 u64 窗口读可闭；本任务未执行）`）；复核回件瑕疵 (a) 与本会话 mtime 实跑（§5）证实 _n9 mtime 2026-11-07 22:42:13 早于 STATIC_COUNT_SPEC.md 23:32:45，故 ：145 属**转录**而非首创——勘误件 ：47「是 N-9 复核件 :145 自己的归类推断」表述有归因时序偏差，不影响「对 [0xB0CD48] 不成立」的判定。STATIC_COUNT_SPEC.md:6-7 自认 _n9 六件为上游产出未改（转录链自证）。

## 3 反驳证据逐条（本会话独立实跑 + 上游存档双源）

本会话实跑命令：
`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/n9_erratum_20261108/_er_report_pe.py"`（EXIT=0，输出 `_er_report_pe_out.txt`，自写独立 PE 解析，不复用既有探件代码）；
`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/n9_erratum_20261108/_er_report_hash.py"`（EXIT=0，16/16 MATCH，`_er_report_hash_out.txt`）；
`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/n9_erratum_20261108/_er_check_b0cd48.py"`（勘误件探件复跑，EXIT=0，输出与存档 sha256 同值 73f76c8c…）。
上游承载：STATIC_GAP_CLOSURE.md §4.1（:96-102，sha256 = e0c00683fb23b0b3777d71639f3d7d265208057969073e53fd2b7195d0c3e1f7，28648 B）与 `_sc_scan_out.txt`（c715898ee1339fa6fdd303a2e93a75f7fec4d92ff725d5f2e6251d76a001a075，44255 B）。

| # | 被核项 | 实测（本会话 `_er_report_pe.py` 实跑输出，两副本同值） | 上游存档对应 |
|---|---|---|---|
| 1 | **[0x7E1738] = 0.5（前提成立的一半）** | sec=.rdata（VA=0x7E1000/RAWSZ=0x31000），d=0x738 → 文件偏移 0x3E1738，qword=0x3FE0000000000000，double=**0.5**；同法 0x7E1728=**60.0**、0x7E27F8=**900.0**（方法校验锚）三点直读全中 ⇒ 映射法无系统偏差 | GAP_CLOSURE:98；_scan:85-86（0.5）、:24（900.0 OK） |
| 2 | **[0xB0CD48] 文件偏移实测（结构性开口）** | IMAGEBASE=0x00400000、5 节（.text/.rdata/.data/.rsrc/.detour，**无独立 .bss 节**，HAS_INDEPENDENT_.bss_SECTION=False）；.data VA=0x812000/VSZ=0x367BE4/RAWPTR=0x412000/RAWSZ=0x6C000（ZEROINIT_TAIL，尾长 0x2FBBE4）。0xB0CD48→RVA=0x70CD48→唯一命中 .data，节内 d=0x2FAD48 ≥ RAWSZ=0x6C000 ⇒ **文件镜像无字节、qword 不可读**；位于 .data 零初始化尾 VA∈[0x87E000,0xB79BE4)；假想线性文件偏移 0x70CD48 超出 .data RAW 末端 0x28ED48 字节（全文件仅 0x49A110=4825360 B） | GAP_CLOSURE:99；_scan:58（文件映射=False）、:59 |
| 3 | **写者 0x6D1BDD（唯一写点）** | 文件偏移 0x2D1BDD 字节 = `dd1d48cdb000` = `fstp qword [0xB0CD48]`，实码在案；全文件 disp32 `48 CD B0 00` 扫描**恰 12 命中** = 1×DD1D（写，fstp@0x6D1BDD）+ 11×DC0D（读，fmul@0x6D1FAF/0x6D2103/0x6D21E2/0x6D24DE/0x6D8D11/0x6D9711/0x6D9C77/0x6D9E05/0x6DB095/0x6DBC71/0x6DBC93），与 _scan:73-84 逐条对应 ⇒ 唯一写者归因由原始字节层面独立证实（未依赖 capstone） | GAP_CLOSURE:99；_scan:72-84 |
| 4 | **函数 0x6D1BB0（写者宿主）** | 0x6D1BB0 = `dd0528177e00`（fld qword [0x7E1728]）、0x6D1BB6 = `dc3578cdb000`（fdiv qword [0xB0CD78]）、0x6D1BC9 = `dd1d18ceb000`（fstp qword [0xB0CE18]）、0x6D1BCF = `E8` + rel32=0xFFDF90DC（-2125604）→ 独立复算 target=**0x4CACB0**、0x6D1BD4 = `dc0d18ceb000`（fmul qword [0xB0CE18]）、0x6D1BDA = `83c408`（add esp,8）、0x6D1BDD = fstp [0xB0CD48]——逐指令编码全部从文件镜像核中；前邻 ret@0x6D1BA7 + nop×8（_scan:754-762） | GAP_CLOSURE:99；_scan:763-774 |
| 5 | **表达式（运行期计算链）** | `[0xB0CD48] = ret(0x4CACB0, [0xB0CD88], [0xB0CD8C]) × (60.0 / [0xB0CD78])`：fld [0x7E1728]（=60.0）→ fdiv [0xB0CD78] → fstp/fmul [0xB0CE18]（中间值暂存）→ call 0x4CACB0（实参 [0xB0CD88]/[0xB0CD8C]）→ fmul → fstp [0xB0CD48]。**输入端 0xB0CD78/88/8C 与暂存槽 0xB0CE18 本会话逐一判定全部落 .data 零初始化域（d=0x2FAD78/0x2FAD88/0x2FAD8C/0x2FAE18 ≥ RAWSZ）⇒ 文件镜像均无值，链条静态不可求值** | GAP_CLOSURE:99（公式同）、:101（输入链未追声明） |

**附加精确化注记（勘误件 §3-4 提出，本会话实跑证实）**：该 PE 无独立 .bss 节；GAP_CLOSURE:99「落在 .data 零初始化域」表述准确；GAP_CLOSURE:173「[0xB0CD48] 结构性开口（BSS，运行期计算值）」的「BSS」应读作「**.data 节内零初始化尾（BSS 型）**」，作节名理解则不确——术语精确化，非新疵点。

**镜像同一性**：ra2youli/gamemd.exe 与 ra2bench/gamemd.exe SHA256 同为 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476、4825360 B（本会话实算，与语料指纹一致），判定对两副本同值。

## 4 反驳成立性判定与下游影响清单

### 4.1 判定

**反驳成立（E-1）**：N-9:205 前提「静态 u64 窗口读可闭」为**半成立前提**——对 `[0x7E1738]` 成立（0.5，直读），对 `[0xB0CD48]` **不成立**（结构性静态开口：PE 头层面 d≥RAWSZ ⇒ 文件镜像无字节，与访存清单完备性、重定位、overlay 均无关；复核回件排查 .rsrc 重叠/别名节/TLS/overlay 反例均未成立，本会话独立复跑同判定）。P6 应由「静态可闭」改为「**半闭半开**」：[0xB0CD48] 数值只能运行期读取，或待输入链（0xB0CD78/88/8C 写者、0x4CACB0 语义，GAP_CLOSURE:101 未做项）闭口后推导。

### 4.2 下游影响清单（勘误件 §5 六行 + 复核回件新增三件，本件补全为九行；行内容本会话逐一实读、指纹逐一实算）

| # | 件（SHA256 前 8 位 / 字节数，本会话 `_er_report_hash.py` 实算） | 需加限定处 | 性质 |
|---|---|---|---|
| 1 | lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md（5b933fe2/32281） | :205（P6 行）、:145、:139、§6.2 节题 :198 | **勘误主对象** |
| 2 | lead/static_spec_n9_20261107/_n9_STATIC_COUNT_SPEC.md（1817d9ce/19949） | :81「静态 u64 窗口读即可闭」、:109「搜索（静态 u64 窗口读可闭；本任务未执行）」 | 上游转录（同语最早载体，mtime 22:42 先于 N-9 复核件 23:32） |
| 3 | lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md（7a617a43/29619） | :139（P6 联引）、:161（Q3 授权卡「S1/S2/S3/S4/P6/P7/P8/P11 均静态可闭」） | 授权卡限定 |
| 4 | lead/perf_repair_n11_20261108/_n11_PERF_REPAIR_HANDOFF.md（cf73fd80/22745） | :108（Q3 授权卡前置草稿版，同语）、:146（P6 联引「FPU 两 double 数值（P6，N-9:143-145）」） | **复核新增**：Q3 同链载体 |
| 5 | lead/d13d14_cards_20261108/DECISION_QUESTIONS.md（0a709f2d/27172） | :102（Q3「问题原文（逐字）」全行同语；:104 状态 proposed 待裁）——待裁问题卡，裁决者据此授权静态检索任务 | **复核新增**：漏登记中影响最大的一件 |
| 6 | lead/d13d14_cards_20261108/_n10_D13D14_CARDS_20261108.md（8a36d60a/30122） | :157（N10-C04 卡，Q3 问题原文逐字同语；:159 状态 proposed） | **复核新增**：Q3 同链载体 |
| 7 | lead/re_line_20261105/W8_STATIC_LOCATE/F8_VISIBILITY.md（ebacbfca/19335） | :169/:222 非前提载体（原文无静态可闭断言），但实现阶段按行取值会踩 [0xB0CD48] 开口，引用须注明取值方式受限 | 引用限定，不构成疵点 |
| 8 | lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md（20e4eeac/26485） | :162 只写「未读出」，无该前提 | **无需勘误** |
| 9 | lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md（e0c00683/28648）、_sc_CLOSURE_20261108.md（9b8695a3/23490） | :50/:98-102 与 :44/:63/:164/:173 已自带修正 | **反驳承载件，无需加注** |

grep 佐证（本会话实跑 `grep -rn "均静态可闭" lead --include="*.md"`，恰 7 行）：Q3 授权卡逐字载体 = 上表 #3/:161、#4/:108、#5/:102、#6/:157 共 4 件（勘误件 §5 仅登记 #3 一件，漏 #4/#5/#6，与复核回件判定一致）；另 2 行为反驳承载件自引（GAP_CLOSURE:26、_sc_CLOSURE_20261108.md:4），1 行为勘误件自身（:86）。

## 5 复核回件（含 SHA256 加字节数绑定）+ 勘误条目表

### 5.1 复核回件转录（verdict = partial → 标 unconfirmed）

- **绑定**：被核对象 SHA256 = 414795407eef7f000baad213db075899513c86c2ee71fbeb3a72e1c5ff95ae73，字节数 = 15794（复核回件绑定行原文；本会话 hashlib 实算同值）。
- **总判定（原样转录）**：反驳主结论本身 = confirmed（复核自写 `_verify_hy4.py` 独立实跑，PE 头反例狩猎——.rsrc 重叠/别名节/TLS/overlay 映射——均未成立）；判 **partial 仅因 ④ 下游影响清单有实质遗漏 + 3 处次要记载瑕疵**，不是「反驳半成立」。复核明言：「PE 头层面的『d≥RAWSZ ⇒ 文件镜像无字节』是结构性事实……『P6 半闭半开』判定成立」，建议补入 3 件后可升 confirmed。
- **partial 三因 + 复核新增遗漏（本会话逐项复验结果）**：
  - **④ 下游清单漏 3 件**（DECISION_QUESTIONS.md:102、_n10:157、_n11:108/:146）——本会话实读三处行原文（§4.2 表 #4/#5/#6）+ 指纹实算 3/3 + grep「均静态可闭」7 行复现，**属实，已并入 §4.2**；
  - **(a) 归因时序**：勘误件 ：47 称前提系 N-9 复核件 :145 首创，实为转录 _n9:81——本会话 `ls -l --time-style=full-iso` 实跑：_n9 = 2026-11-07 22:42:13 < STATIC_COUNT_SPEC.md = 23:32:45，**属实**（已在 §2 改正表述）；
  - **(b) 数字失真**：勘误件 §6 命令 11 自记 grep「8 处」——本会话实跑 `grep -rn "静态 u64 窗口读" lead --include="*.md" | wc -l` = **22** 行，**属实**（不承重：勘误件引用面结论以 §4/§5 表为准，非以该计数为准）；
  - **(c) 论证强度**：勘误回执称「上游件零改动（git status 复核）」——git status 对未跟踪件无内容级变更检测力；本会话以**逐字节指纹比对补强**：编排方指纹 4 件 + 勘误件 §0 四件 + 复核前缀三件 + 被核对象 + 两 exe = **16/16 MATCH**（`_er_report_hash_out.txt`），上游件 mtime 均早于勘误件 2026-11-08 20:20:13，零改动结论由此坐实。
- **复核回件自报未做项（转录）**：全仓（lead 之外）walk 因 >120s 中止改用 lead 有界版；capstone 全量反汇编未重演（以原始字节 disp32 扫描替代验证 12 条）；0x4CACB0 语义与 0xB0CD78/88/8C 写者未追。

### 5.2 勘误条目表

| 编号 | 原表述 | 勘误内容 | 判定 | 建议处置 |
|---|---|---|---|---|
| **E-1** | N-9:205「\| P6 \| F8 两个 FPU 常量数值（静态 u64 窗口读可闭） \| F8V:169/:222 \|」（上位节题 :198「静态可闭、既有材料未做」；同件 :145「静态 u64 窗口读即可闭」、:139 两常量并列为「两个 qword」；转录链 _n9:81/:109、PERF:139/:161、_n11:108/:146、DQ:102、_n10:157） | 前提对两常量一真一假：[0x7E1738]=0.5 静态可闭（.rdata 直读）；[0xB0CD48] 落 .data 节内零初始化尾（VA∈[0x87E000,0xB79BE4)，d=0x2FAD48≥RAWSZ=0x6C000），文件镜像无字节，值 = ret(0x4CACB0,[0xB0CD88],[0xB0CD8C])×(60.0/[0xB0CD78]) 运行期算出且输入端同无值 ⇒ **结构性静态不可闭** | 反驳成立（复核主结论 confirmed；登记包状态 unconfirmed，partial 因 §4 清单遗漏，本件已补） | **保留原表述、加勘误注记**（原件不可改）：在 N-9:205/:145 挂注「P6 半闭半开——[0x7E1738] 可静闭，[0xB0CD48] 为 .data 零初始化尾运行期计算值，静态 u64 窗口读无值可读，勘误见 lead/n9_erratum_20261108/」；**下游引用（九行清单）须带「P6 半闭半开」限定**；F8 实现阶段排程改道：[0xB0CD48] 须运行期读取或先闭输入链（GAP_CLOSURE:101 未做项） |

## 6 结论

### 6.1 erratumCount 与 downstreamImpact

- **erratumCount = 1**（E-1，见 §5.2）。
- **downstreamImpact**（九件，§4.2 完整清单）：①STATIC_COUNT_SPEC.md :205/:145/:139/:198（主对象）；②_n9_STATIC_COUNT_SPEC.md :81/:109；③PERF_REPAIR_HANDOFF.md :139/:161；④_n11_PERF_REPAIR_HANDOFF.md :108/:146；⑤DECISION_QUESTIONS.md :102（proposed 待裁，裁决者据此授权）；⑥_n10_D13D14_CARDS_20261108.md :157；⑦F8_VISIBILITY.md :169/:222（引用限定）；⑧W8_STATIC_LOCATE.md :162（无需勘误）；⑨GAP_CLOSURE / _sc_CLOSURE（反驳承载件，无需加注）。其中 ④⑤⑥ 为复核回件发现、勘误件 §5 漏登记的三件，本件补全。**影响实质**：P6 由「静态可闭」改为「半闭半开」——[0xB0CD48] 数值只能运行期读取或待输入链闭口后推导，凡涉 Q3 授权卡（PERF:161 一链四件）与 F8 实现阶段排程的下游，均须带该限定改道。

### 6.2 建议处置

保留原表述加勘误注记（原件一律不改）：N-9:205/:145 挂勘误注记指向本写域；九行清单的引用者带「P6 半闭半开」限定；[0xB0CD48] 取值改道（运行期读取，或先闭 0xB0CD78/88/8C 写者与 0x4CACB0 语义再推导——后者属另立搜索任务，不在本件范围）。

### 6.3 铁律与不改原件声明

本会话零真机（未启动任何 exe、未 taskkill、未读活进程内存）、零采样代码（无 hook/MiniDump/SuspendThread/StackWalk/注入/ctypes/OpenProcess/ReadProcessMemory；两探件均为磁盘只读 + struct 解析，实跑 EXIT=0）；未 commit、未 push（git log -1 = 2657458 不变）；上游原件与勘误件、台账零改动——佐证 = 编排方指纹 4 件 + 全部被引件 16/16 逐字节指纹 MATCH（`_er_report_hash_out.txt`）且 mtime 均早于本会话；git status 对未跟踪件无内容级检测力，故零改动以指纹比对为准（复核瑕疵 (c) 的改正）。

### 6.4 未验项（如实，不补造）

1. **capstone 全量反汇编未重演**（本会话与两前会话同）：12 条访存清单由本会话以原始字节 disp32 扫描（`_er_report_pe.py`，恰 12 命中 = 1 fstp 写 + 11 fmul 读）独立证实，唯一写者归因不再依赖存档转引；但 647 条 [0x7E1738] 访存形态清点（_scan:87-99）未复跑。
2. **0x4CACB0 语义、0xB0CD78/88/8C 写者未追**（同 GAP_CLOSURE:101 未做项）：表达式各输入的运行期来源不明，工程含义不补猜。
3. **全仓（lead 之外）引用面未做**：本会话引用面检索仅覆盖 lead/**/*.md 两串关键词（「静态 u64 窗口读」= 22 行、「均静态可闭」= 7 行，均实跑）；ra2youli/**、out/re_work/** 等域未扫。
4. **[0xB0CD48] 运行期实际数值**：铁律禁止真机，永久缺口（P6 运行期部分），不标未验值。
5. **复核会话自有产物未复跑**：_verify_hy4*.py 及其输出在场（写域 ls 实见 4 件）但本会话未重演，其内容以复核回件转录为准；本会话关键判定均以自有探件独立重跑为准（`_er_report_pe.py` EXIT=0、`_er_check_b0cd48.py` 复跑输出与存档逐字节一致）。

—— 本件登记完毕。状态 unconfirmed（复核 verdict=partial）；反驳主结论成立，partial 缘由（下游清单遗漏）已由本件 §4.2 补全，可提请复核方按其建议升 confirmed。
