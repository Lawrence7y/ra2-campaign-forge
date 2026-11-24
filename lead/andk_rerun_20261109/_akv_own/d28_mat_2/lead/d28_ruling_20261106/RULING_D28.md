# D-28 两链路线裁决

## 0 定谳
q1: AKV_BROKEN_DECL
q2: AKV_BROKEN_DECL

B 链立即安排独立候选复审及独立复核；D 链保持口径 B 与 D-13b 离线研究状态，先澄清时序规格并复审条件预算，再决定是否另立捕获方案。两条链分别验收，不以一条链的进展替代另一条链的证据。

证据说明：本文依据题给「裁决员结论」「事实核证 F1—F10、D1—D10、selfBias」和「裁决书事实核对意见」整理。下列文件行号来自这些输入，本撰写阶段未逐文件重读，未运行核证脚本、门禁、29 项测试、43 项测试或语料重算。题给核证阶段的执行事实均明确归于独立核证输入，不记作撰写阶段亲跑通过。

## 1 B 链下一步

选择 A：立即安排独立候选复审及独立复核，复审模型必须不同于候选作者 gemini-3.8-flash。这是补齐既定下一门，不是签候选通过。第 5 步要求逐项对照批准设计，核对状态矩阵、调用传参、输出字段、F/E 分离与范围限制，执行获准离线测试；只有阻断项关闭且绑定版本一致，才能签通过。依据：题给裁决 q1；lead/control_20261106/D28_ENTRY_DRAFT.md:91；lead/d25_ruling_20261106/RULING_D25.md:36。

复审交付应包括逐项设计对应、问题及关闭证据、精确测试命令、输出、退出码、未覆盖项，并绑定候选和母本完整指纹。题给 F1 的当前版本为：

- 候选：420292 B，SHA256 `9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc`。
- 母本：399508 B，SHA256 `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636`。

F1 只证明核证时当前母本与基准一致，不能证明所有历史时刻均未改动。F2 支持 H6 实际调用显式传入 pre_freshness_snapshot，F3 支持 H7 初始化及五个指定早退的相对位置。出处：lead/b2b_candidate_20261106/qc151_trip.candidate.py:6167、lead/b2b_candidate_20261106/qc151_trip.candidate.py:6528、lead/b2b_candidate_20261106/qc151_trip.candidate.py:6545；题给 F1—F3。这些证据足以启动复审，不足以跳过复审。

F4 支持报告五字段文本为 true；其中 testsActuallyRun 是报告声明。F5 支持独立核证阶段候选机械门禁 9/9、D-13b 机械门禁 8/8 通过，不支持把旧测试输出当作本轮重跑。出处：lead/b2b_candidate_20261106/review/CANDIDATE_REVIEW.md:22、lead/b2b_candidate_20261106/review/CANDIDATE_REVIEW.md:26、lead/b2b_candidate_20261106/check_candidate.py:195、lead/b2b_candidate_20261106/check_candidate.py:228、lead/d13b_design_20261106/check_d13b.py:202；题给 F4/F5。

下一执行任务须先明确允许的离线测试及输出写域，不得导入完整 harness 或触发真机。历史 29 项、43 项测试在裁决阶段和本撰写阶段均未运行。第 5 步通过后才安排第 6 步隔离副本离线集成；正式母本应用及真机验收仍未获准。出处：lead/d25_ruling_20261106/RULING_D25.md:21、lead/d25_ruling_20261106/RULING_D25.md:35、lead/d25_ruling_20261106/RULING_D25.md:37；本轮铁律。

## 2 D 链处置

选择丁：保留口径 B，保持 D-13b 离线研究和 D-13 采样实现与执行 PAUSE。先交付一项有限的时序规格澄清与条件预算复审，不以本裁决选择或授权新的捕获实现。出处：题给裁决 q2、bounds；lead/PENDING_DECISIONS.md:260；lead/d27_ruling_20261106/RULING_D27.md:8、lead/d27_ruling_20261106/RULING_D27.md:32。

规格澄清必须分别列出事件离线分类时刻、在线触发时刻、原始上下文保存截止、离线解析完成时刻。停滞发生后 50ms 与检测后 <50ms 是两个起算点，安全裕量 ≤20ms 也须明确所处时间段。定义对累计判定 ≥100ms 的触发机制有拒止要求；等待满 100ms 才触发的方案与该规则存在待解决的规范冲突，不得静默删除规则。出处：lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:177、lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:190、lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:191；题给 F7、D8。

现四段模型为 2.5+100+48+2=152.5ms。2.5ms 是代理估算，48ms 是名义预算拆分，2ms 是指标，均不是已证明的实现耗时下界。故只判该固定模型不满足在 129.93ms 代表性事件结束前完成在线快照的要求，不判当前口径下物理不可行，也不关闭整条路线。129.93ms 是保留标签集合中位数，不是每个事件的时长上界。出处：lead/d13b_design_20261106/BUDGET_MODEL.json:5、lead/d13b_design_20261106/BUDGET_MODEL.json:19、lead/d13b_design_20261106/BUDGET_MODEL.json:26、lead/d13b_design_20261106/BUDGET_MODEL.json:32；lead/d27_ruling_20261106/RULING_D27.md:12；题给 F6、D2、D7。

预算注释中的条件反例 2.5+100+20=122.5ms，距 129.93ms 留有 7.43ms，只说明算术仍有研究空间；它不能消除定义第 191 行的规范冲突，不能证明真实时延、扰动、资源释放或栈解析可行。当前 152.5ms 若要严格小于 129.93ms，须削减严格超过 22.57ms，恰好削减 22.57ms 仅到相等。出处：lead/d13b_design_20261106/BUDGET_MODEL.json:34；题给 F6、D3、D9。

下一阶段限于规格、假设矩阵和纯模型/合成时序论证。如提出提前或周期性保存历史上下文，须按新方案独立审查触发、覆盖、假阳性、扰动、配额及回退，不能称作调参，本次也不授权实施。停滞结束后才取当前栈，与解析停滞期间已经保存的原始上下文，应严格区分；现有设计区分在线保存和离线解析，但没有已验证可用的采样实现。出处：lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:200；lead/d27_ruling_20261106/RULING_D27.md:28、lead/d27_ruling_20261106/RULING_D27.md:32、lead/d27_ruling_20261106/RULING_D27.md:42；题给 D4—D6。

### 历史数字

本次选丁，不改变事件提取、分类或窗口集，保留当前历史数字和版本来源，不回溯重算：1737 是 full97 全部候选平台数；1681 是其中 isRealMatch=true 的保留标签数，另有 56 个 false。90.42% 是 1681 个保留标签事件中 1520 个落在 100≤d<200ms 的比例，不是 1681/1737，也不等同已独立确认的真实对局分布。129.93ms 同样只属于该保留标签集合。出处：lead/d27_ruling_20261106/RULING_D27.md:12、lead/d27_ruling_20261106/RULING_D27.md:48；题给 historyDisposal。本撰写阶段未重算。

口径 A 的历史引用及 occ_a/wait-trace 隔离继续遵守 lead/PENDING_DECISIONS.md:260、lead/PENDING_DECISIONS.md:261、lead/PENDING_DECISIONS.md:262。将来若另立提前/周期性捕获方案，而离线事件定义和标签规则不变，上述数字仍可作为原版本条件统计，不能直接当作新方案捕获覆盖率。若未来用户明确批准修改门槛、窗口或标签，须另建版本，独立计算新候选数、保留数及比例；旧 1737/1681/90.42% 保留为历史结果，禁止覆盖或跨版本直接比较。出处：题给 historyDisposal、D4；上述 D-12 与 D-27 引文。

## 3 优先级与并行

B 链独立候选复审优先，沿用 D-25 对既有语料分析的先后约束，不因 D 预算争议中断 B。现有材料没有证明两链技术互锁：B 候选语义核查不依赖 D 采样方案，D 时序规格澄清也不依赖 B 签通过。资源允许时可并行做本次限定的 D 规范澄清和纯预算审查；不得扩大为提前开展 D-25 排在 B 离线阶段收口之后的既有语料分析，更不得进入采样实现。出处：lead/d25_ruling_20261106/RULING_D25.md:15、lead/d25_ruling_20261106/RULING_D25.md:38；题给 q3Ordering。

来源会话须分别指定后续任务写域；复审人力冲突时先保 B。B 复审通过才进隔离集成；D 规格澄清后才对新方案作设计审查，两者各自验收，互不替代。依据：题给 q3Ordering；lead/d25_ruling_20261106/RULING_D25.md:36、lead/d25_ruling_20261106/RULING_D25.md:37。

## 4 本轮更该做的事

没有证据支持用另一工程任务取代 B 独立复审。应立即固定措辞与证据等级：候选“全绿”限于机械门禁和报告字段；“物理上做不到”改为固定预算模型未达代表性截止条件；D 下一设计任务须明确两个 50ms 起算点。本裁决承接这些更正，不修改只读草案或台账。出处：lead/control_20261106/D28_ENTRY_DRAFT.md:12、lead/control_20261106/D28_ENTRY_DRAFT.md:26、lead/control_20261106/D28_ENTRY_DRAFT.md:65、lead/control_20261106/D28_ENTRY_DRAFT.md:78；题给 q4Other。

全窗/缺窗事件状态语义及长停漏检仍是后续研究缺口，不宣告闭合，不据此重开真机采集。出处：lead/d27_ruling_20261106/RULING_D27.md:18、lead/d27_ruling_20261106/RULING_D27.md:42、lead/d27_ruling_20261106/RULING_D27.md:48。

## 5 授权边界

本次仅作路线裁决和后续任务建议，不代用户授权侵入性操作，不代用户修改 D-12。D-13 采样实现与执行继续 PAUSE，目标①机制挂账保持。依据：本轮铁律；lead/d27_ruling_20261106/RULING_D27.md:8、lead/d27_ruling_20261106/RULING_D27.md:32。

本次不授权：启动 gamemd.exe、ra2loader、YURI.exe，taskkill，读取活进程内存，编写或运行 hook、MiniDump、SuspendThread、StackWalk、注入探针或任何真实采样实现；不得以合成单测名义调用采样 API。依据：本轮铁律 1—2；lead/d27_ruling_20261106/RULING_D27.md:32、lead/d27_ruling_20261106/RULING_D27.md:34。

本次不授权修改题列只读路径，包括 ra2youli/**、out/re_work/**、lead/re_line_20261105/**、lead/GOAL_*、lead/PENDING_DECISIONS.md、lead/b2b_*/**、lead/b2b_preaudit_*/**、lead/d13b_design_*/**、lead/stall_event_def_*/**、lead/d2*_ruling_*/**。其中本轮明确指定的唯一写域 lead/d28_ruling_20261106/ 是本次两份输出的例外写域。不得改门禁使检查通过，不 commit、不 push；Python 如执行须隔离模式、UTF-8、绝对路径。依据：本轮铁律 3—8及本次明确输出要求。

确定下一阶段不扩大本代理写域到后续复审、测试或集成目录。由来源会话按既有离线授权派发具体任务和写域，无须重问一般离线权限。第 5 步未签通过不得进入第 6 步，第 6 步通过也不代表允许正式母本写入。出处：lead/d25_ruling_20261106/RULING_D25.md:19、lead/d25_ruling_20261106/RULING_D25.md:21、lead/d25_ruling_20261106/RULING_D25.md:36、lead/d25_ruling_20261106/RULING_D25.md:37；题给 bounds。

## 6 未背书

- 不把预算超标外推为栈采样不可行；不自行改口径 B。出处：lead/control_20261106/D28_ENTRY_DRAFT.md:115；lead/d13b_design_20261106/BUDGET_MODEL.json:34；lead/PENDING_DECISIONS.md:260。
- 不背书 B2b 已通过 D-25 第 5 步、可应用母本、已完成隔离集成或目标②主崩溃已修复；目标①真实多单位卡顿改善、目标③新一轮安全验收均无本轮证据。出处：lead/d25_ruling_20261106/RULING_D25.md:36、lead/d25_ruling_20261106/RULING_D25.md:37、lead/d25_ruling_20261106/RULING_D25.md:67；题给 notEndorsed。
- 不背书 152.5ms 是普适下界、122.5ms 是真实可行性证明、较长事件捕获覆盖率已验证，或真实时延、扰动、资源释放、栈解析已达标。出处：lead/d13b_design_20261106/BUDGET_MODEL.json:5、lead/d13b_design_20261106/BUDGET_MODEL.json:19、lead/d13b_design_20261106/BUDGET_MODEL.json:26、lead/d13b_design_20261106/BUDGET_MODEL.json:34；lead/d27_ruling_20261106/RULING_D27.md:42、lead/d27_ruling_20261106/RULING_D27.md:67。
- 不背书保留标签等同真实对局真值、全部 53 条长平台确为非真实停滞、现实长停不存在，或 1681 与 1737 可作同口径事件数直接对照。出处：lead/d27_ruling_20261106/RULING_D27.md:12、lead/d27_ruling_20261106/RULING_D27.md:18、lead/d27_ruling_20261106/RULING_D27.md:48。
- 不将题给独立核证成功及历史报告声明记为本撰写阶段亲跑通过；门禁、测试、语料重算本阶段均未运行。依据：本阶段工具记录；题给 F4/F5。

## 7 诚实账

题给「裁决书事实核对意见」为 approved=true，blockers=[]、missing=[]、unverifiable=[]；这是输入核对意见，不是本撰写阶段独立重验结果。没有题给 blocker 需要登记；其余证据限制仍如实保留。

本撰写阶段仅执行目录定位命令 `pwd; rg --files lead/d28_ruling_20261106`，输出工作目录 `/d/Project/ra2-campaign-forge`，并列出 `_d28_facts.py`、`_d28_facts_out.txt`，退出码 0；随后以文件写入工具生成本裁决及 FACTCHECK.md。未运行核证脚本、门禁、历史测试、探针或统计重算。本文来源行号与数值均来自题给材料，本阶段原文件内容未重读、历史执行未独立复现。

必须保留以下更正，详见 FACTCHECK.md：草案 :12/:26 的“全绿/全 true”限缩为机械门禁/字段状态；:32 的“生成前/后均”不能由当前指纹证明；:44 应分开 8/8 门禁与历史 43 项测试；:63 的 if dur >= thr 实际位于 lead/stall_event_def_20261106/_stall_probe.py:96，非给定 d13b 路径或 :100；:65 的“任何触发机制”过宽；:46/:78 不得作物理不可行结论；:66 须为严格削减超过 22.57ms；:75 不得称历史数字“全部失效”；:76/:77 须区分当前栈与预存上下文离线回溯。依据：题给 corrections、F1、F5、F9、D1—D10。

自偏风险：条目可能受推进 B 或收口 D 的叙事影响；总控可能把“B 全绿、D 超预算”误作同强度结论；核证方也可能过重强调算术反例而低估实施难度。上述均为风险提示，不断言作者动机。122.5ms 不能背书真实可行，机械门禁也不能替代独立语义复审。依据：题给 selfBias 全四项。
