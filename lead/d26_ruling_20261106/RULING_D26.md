# D-26：D-13 / D-14 裁决书

依据：本次任务提供的《裁决员结论》《事实核证》及《裁决书事实核对意见》。本文承接给定裁决，不将文书生成解释为用户新增采样授权。前序核证输出已在本次亲读；来源文献行号依题给核证记录引用，不冒称本次逐件复核或原始复算。

## 0 定谳
d13: PAUSE
d14: C

D-13 采样代码与执行继续暂停；D-14 双口径并列，逐项标明窗口定义、n、变量和适用范围。两项决策可以登记为已定谳，但不解除目标①机制挂账，不改变本轮零真机、零采样代码及唯一写域限制。（出处：本次《裁决员结论》d13、d14、unblockGoal1；本次铁律第1–4条；lead/goal3t_nightwatch_20261102/E3_FOR_GOAL1_CARD_20261103.md:129。）

## 1 D-13 理由

暂停有独立技术理由：将29个结束态冻结窗当真实对局停滞的前提已撤销。下一步须先明确要解释慢爬成本还是≥1s长停；D-24与D-25均建议暂停，两者同向且均未代裁，并非两份相反的最终裁决。（出处：lead/PENDING_DECISIONS.md:23；lead/PENDING_DECISIONS.md:25；lead/re_line_20261105/D24_RULING/RULING_D24.md:68；lead/re_line_20261105/D24_RULING/RULING_D24.md:70；lead/d25_ruling_20261106/RULING_D25.md:46。）

来源建议A有缩小范围、候选易回退的优点，但1s触发天然遗漏条目所述87.7%的0.1–0.2s短停。历史指定语料中的“N=1s误触率0”不能证明剩余长停是有效的真实对局目标事件，也不能保证普遍零误触或短停覆盖。dump解析路径仍未验证，因此不凭阈值校准批准A，也不认定A永久不可用。（出处：lead/PENDING_DECISIONS.md:30；lead/PENDING_DECISIONS.md:32；lead/PENDING_DECISIONS.md:36；lead/goal3t_nightwatch_20261102/E3_FOR_GOAL1_CARD_20261103.md:145；lead/goal3t_nightwatch_20261102/E3_FOR_GOAL1_CARD_20261103.md:150；题给事实核证F3。）

C的≤50ms是设计护栏，实际时延、短停命中率和安全性均未证明。暂停线程可能自造死锁并污染②，不能据此承诺短停覆盖；即使得到栈，也须事件真实、触发后仍处于事件、快照和解析成功，栈位置不自动等于机制。（出处：lead/codex_round_20261030/LEADER_battle/E3_SAMPLING_PLAN_REVIEWABLE.md:21；lead/codex_round_20261030/LEADER_battle/E3_SAMPLING_PLAN_REVIEWABLE.md:25；lead/codex_round_20261030/LEADER_battle/E3_SAMPLING_PLAN_REVIEWABLE.md:31；lead/goal3t_nightwatch_20261102/E3_FOR_GOAL1_CARD_20261103.md:125。）

先补项目为：在既有离线语料中定义并识别真实对局目标事件，明确性能量及长停代表范围，排除结束态和合法冻结混淆；提交触发延迟、采样扰动、栈解析、停止及回退设计。语料不足则记未验并列所需证据，不自行采集。这些是后续证据要求，不是本次执行授权。（出处：本次《裁决员结论》d13Rationale；lead/re_line_20261105/D24_RULING/RULING_D24.md:70。）

## 2 D-14 理由

裁C是为保留可追溯描述并展示窗口选择敏感性。moving按窗内有推进筛选，会限定研究对象；全量包含全窗冻结及结束态混淆，也不能直接解释真实对局卡顿。现有事件语义证据不足以支持统一删除任一口径，“有推进才有停滞”或“全量更保守”均不足以裁定唯一正确口径。双口径保留不等于任一套已证明机制。（出处：lead/PENDING_DECISIONS.md:23；lead/PENDING_DECISIONS.md:49；lead/PENDING_DECISIONS.md:51；lead/PENDING_DECISIONS.md:57；lead/PENDING_DECISIONS.md:61；本次《裁决员结论》d14Rationale。）

| 历史条目 | 保留数值与窗口定义 | 必须附带的限制 |
|---|---|---|
| §522 | n=64 moving，只取窗内有推进；ρ(uptime,B%)=+0.0395、ρ(window,B%)=−0.0403 | 与97全量并列；仅该窗口集所报总体相关接近零，不能推广到全量或作因果排除。本次未原始复算。 |
| §528 | n=97全量，含全窗冻结；ρ(uptime,B%)=+0.3461、ρ(window,B%)=+0.3474 | 与64 moving并列；C2 MATCH仅为数值MATCH，不能推出相位驱动，也不能证明冻结窗解释全部差异。本次未原始复算。 |
| §534 | 复列的四个总体系数按以上限定保留 | 撤销“可算8个BOOT、中位+0.4472”统计汇总，撤销以它强化“相位不驱动”的结论。 |

表中前两项出处：lead/PENDING_DECISIONS.md:49；lead/PENDING_DECISIONS.md:50；lead/PENDING_DECISIONS.md:51；lead/PENDING_DECISIONS.md:54；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:49；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:52。第三项出处：lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:62；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:71；lead/d26_ruling_20261106/_d26_facts_out.txt:70。

§534表有8行，但uptime相关仅6个有限值、2个nan；4负/2正只描述六个uptime相关，不能概括window列。按公布四位小数表值，中位数为−0.34305，原始精度及BOOT分组仍待独立复算。原脚本把nan一并append并按len计数，取排序中间一项，未计算有限偶数样本的中央两项均值。这里只承接表内勘误，不把它包装成97原始窗复算。（出处：题给事实核证D1；lead/goal3t_nightwatch_20261102/_phase_recompute.py:189；lead/goal3t_nightwatch_20261102/_phase_recompute.py:195；lead/goal3t_nightwatch_20261102/_phase_recompute.py:197；本次亲读lead/d26_ruling_20261106/_d26_facts_out.txt:70；lead/d26_ruling_20261106/_d26_facts_out.txt:71。）

有限样本方向不一致不足以排除相位作用：样本极小、BOOT大多反推，且未做因果分析。D-24、D-25的同向建议也不等于两次独立统计复核。（出处：lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:119；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:121；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:125；lead/d25_ruling_20261106/RULING_D25.md:46。）

## 3 授权边界

本次不授权编写或执行任何采样候选，不授权启动gamemd.exe、ra2loader、YURI.exe，不授权taskkill、读取活进程内存、hook、MiniDump、SuspendThread、StackWalk或探针注入。唯一写域为lead/d26_ruling_20261106/；不改只读来源、不改门禁、不commit、不push。（出处：本次铁律第1–5、8条；本次《裁决员结论》notEndorsed。）

`d13OfflineOnly=true`只表示未来若重裁批准候选，权限上限先限于离线候选与离线验证，并非本次批准离线采样实现。`d13NeedsUserForCode=true`表示编写候选须用户明确改变当前零采样代码限制并指定写域；历史“d”或一般授权不覆盖本轮明禁。此处要求当前任务有效的明确授权，不创设每轮重复询问规则。真机、活进程和侵入采集仍须具体授权，离线通过不保证另批一次即可执行。（出处：本次《裁决员结论》d13OfflineOnly、d13NeedsUserForCode、d13Rationale；lead/d25_ruling_20261106/RULING_D25.md:42；本次铁律第1–4条。）

## 4 执行顺序与后续

两项无相互等待的执行顺序：D-14可作为报告规则定谳，不能因此放行D-13；D-13暂停不阻止离线统计勘误。草案已声明互不依赖。D-13内部须先澄清目标及事件，再审设计与授权，随后才考虑候选及执行。未来另获授权产生新数据时，应在解释前定义事件/窗口映射，按C报告适用双口径，不能直接套用历史64/97窗。（出处：lead/control_20261106/D26_ENTRY_DRAFT.md:3；lead/control_20261106/D26_ENTRY_DRAFT.md:4；lead/re_line_20261105/D24_RULING/RULING_D24.md:70；lead/re_line_20261105/D24_RULING/RULING_D24.md:78；本次《裁决员结论》ordering。）

D-13路径勘误采用追加并与原条目双向关联的登记方式，保留历史原文。本次只在本裁决书及FACTCHECK记录登记内容，未修改台账或创建独立勘误件；后续由有台账写域的任务追加勘误链接，单在草案记录不能消除原入口歧义。准确措辞是：PENDING_DECISIONS.md第44行给主卡全路径，第45行只给方案basename；沿前项目录展开会指向不存在路径，并非原文逐字写出完整错路径。正确方案路径是lead/codex_round_20261030/LEADER_battle/E3_SAMPLING_PLAN_REVIEWABLE.md。前序核证记录其6268字节、sha256=97599cfd06bacfd2330c40c0863228f1231984a568122fd0a1ed6cf6a7cd51a1；本次未重新计算指纹。（出处：lead/PENDING_DECISIONS.md:44；lead/PENDING_DECISIONS.md:45；题给事实核证F2、D2；本次亲读lead/d26_ruling_20261106/_d26_facts_out.txt:8；lead/d26_ruling_20261106/_d26_facts_out.txt:18；lead/d26_ruling_20261106/_d26_facts_out.txt:22。）

目标①机制挂账不解除。两项定谳只解决决策状态和报告规则，未提供真实多单位卡顿机制定位或改善证据。主卡也明确采样只看到栈位置、仍须归因、不清理①机制。后续应关联证据任务承接真实对局事件定义、慢爬/长停划分和§534复核，编号及台账修改交有写域的任务；本次不代写台账、不授权采样。（出处：lead/goal3t_nightwatch_20261102/E3_FOR_GOAL1_CARD_20261103.md:125；lead/goal3t_nightwatch_20261102/E3_FOR_GOAL1_CARD_20261103.md:129；本次《裁决员结论》unblockGoal1。）

## 5 对条目的更正

1. 路径引文须区分原文basename与推断展开路径；登记方法及完整正确路径见第4节。（出处：lead/control_20261106/D26_ENTRY_DRAFT.md:46；lead/PENDING_DECISIONS.md:44；lead/PENDING_DECISIONS.md:45；题给事实核证D2。）
2. 建议张力在来源A/A与裁决建议暂停/C之间；D-24与D-25彼此同向且未代裁。（出处：lead/PENDING_DECISIONS.md:40；lead/PENDING_DECISIONS.md:60；lead/re_line_20261105/D24_RULING/RULING_D24.md:68；lead/d25_ruling_20261106/RULING_D25.md:46。）
3. “两窗口集符号相反”仅适用于ρ(window,B%)，uptime两值均正。（出处：lead/PENDING_DECISIONS.md:48；lead/PENDING_DECISIONS.md:50；lead/PENDING_DECISIONS.md:52；题给事实核证D3。）
4. 撤销§534“可算8个BOOT、中位+0.4472”的有效汇总；改记8行、6有限、2nan，公布值中位−0.34305，原始精度未验。4负/2正不概括window列。（出处：lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:62；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:71；lead/d26_ruling_20261106/_d26_facts_out.txt:70；lead/d26_ruling_20261106/_d26_facts_out.txt:71。）
5. 撤销据上述方向数强化“相位不驱动”的推论。PHASE文档将64/97口径问题记成D-12，关联勘误应注明当前编号D-14。（出处：lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:73；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:113；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:125；lead/PENDING_DECISIONS.md:47。）
6. N=1s零误触仅是历史指定语料记载，不能扩成真实对局通用保证；29个结束态窗前提撤销须显式带入。（出处：lead/PENDING_DECISIONS.md:23；lead/PENDING_DECISIONS.md:25；lead/PENDING_DECISIONS.md:30；题给事实核证F3。）
7. “拿到冻结瞬间栈”须改为附条件预期，≤50ms须记设计目标；快照不自动完成机制定位。（出处：lead/PENDING_DECISIONS.md:35；lead/PENDING_DECISIONS.md:38；lead/codex_round_20261030/LEADER_battle/E3_SAMPLING_PLAN_REVIEWABLE.md:25；lead/goal3t_nightwatch_20261102/E3_FOR_GOAL1_CARD_20261103.md:125。）
8. 统一64或97均需事件语义及选择条件证据；双口径不等于认可任一套为纯粹对局停滞样本。（出处：lead/PENDING_DECISIONS.md:23；lead/PENDING_DECISIONS.md:57；lead/PENDING_DECISIONS.md:61。）
9. 合并办理、条目归档和解除机制挂账须分开，不以清单减少代替技术进展。（出处：lead/control_20261106/D26_ENTRY_DRAFT.md:3；lead/control_20261106/D26_ENTRY_DRAFT.md:89；lead/goal3t_nightwatch_20261102/E3_FOR_GOAL1_CARD_20261103.md:129。）

## 6 未背书

- 不背书任何采样实现、游戏启动、活进程操作或新增授权；一般授权不撤销本轮明禁，离线通过也不预先放行执行。（出处：本次铁律第1–4条；本次《裁决员结论》notEndorsed。）
- 不背书A代表87.7%短停主体、C能≤50ms安全覆盖短停、不污染②，或MiniDump“不会自造死锁”的绝对保证。（出处：lead/PENDING_DECISIONS.md:32；lead/PENDING_DECISIONS.md:38；lead/goal3t_nightwatch_20261102/E3_FOR_GOAL1_CARD_20261103.md:88；lead/codex_round_20261030/LEADER_battle/E3_SAMPLING_PLAN_REVIEWABLE.md:27；本次《裁决员结论》notEndorsed。）
- 不背书“相位驱动”“相位不驱动”或“已排除BOOT混杂”等因果机制结论。（出处：lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:119；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:125；题给事实核证D4。）
- 不背书97原始窗、历史阈值、原始精度中位数、项目门禁或真机修复已验证通过；前序文献检查8/8不证明上述事项。（出处：lead/d26_ruling_20261106/_d26_facts_out.txt:2；lead/d26_ruling_20261106/_d26_facts_out.txt:112；lead/d26_ruling_20261106/_d26_facts_out.txt:113。）
- 不背书修改只读来源、改门禁让检查通过、commit或push。（出处：本次铁律第3–5、8条。）

## 7 诚实账

题给《裁决书事实核对意见》为approved=true，blockers=[]、missing=[]、unverifiable=[]，没有列出阻断项；这只是题给核对意见，不是本次新运行门禁或新增授权。前序裁决员结论中的“本次未写文件”仅适用于其前序阶段；本撰写阶段按本次明确要求写入RULING_D26.md和FACTCHECK.md，不能沿用为本阶段事实。（出处：本次《裁决书事实核对意见》；本次写两份文件的指令；本次《裁决员结论》notEndorsed。）

本阶段实际操作为定位目录、亲读前序核证输出、通过文件写入工具生成两份指定文书。前序命令 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/d26_ruling_20261106/_d26_facts.py > D:/Project/ra2-campaign-forge/lead/d26_ruling_20261106/_d26_facts_out.txt` 的成功及8/8来自题给F9和已亲读的既有输出，本阶段未重跑，不能签本阶段核证通过。（出处：题给事实核证F9；lead/d26_ruling_20261106/_d26_facts_out.txt:113；本阶段工具记录。）

未验：97原始窗口复算、历史阈值复现、原始精度BOOT中位数和分组、触发时延、采样扰动、短停命中、安全性、dump解析、显著性及因果分析、项目门禁、真实卡顿改善。未运行真机、活进程或采样操作；未执行历史实验脚本；不将表内算术修正充当机制证据。（出处：本次《裁决员结论》notEndorsed；题给事实核证F9、D1、D4；lead/d26_ruling_20261106/_d26_facts_out.txt:2；lead/d26_ruling_20261106/_d26_facts_out.txt:112；本阶段工具记录。）

偏向风险另详FACTCHECK.md：合并办理的行政便利、重复引用被误当独立补强、建议分歧被写强、维持C的举证不对称、归档与技术解挂混同。这些是题给核证的框架风险，不推断作者主观动机，也不代替技术证据。（出处：本次《事实核证》selfBias。）
