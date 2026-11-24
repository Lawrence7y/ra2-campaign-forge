# D-29 事实核对与证据限制

证据范围：本表根据题给“裁决员结论”“事实核证”“裁决书事实核对意见”，并结合本撰写阶段读取的 D-28、_d29_facts.py 和输出整理。题给核对意见 approved=true、blockers=[]、missing=[]、unverifiable=[]，不等于本阶段运行了发布门禁。出处：题给对应字段；本阶段工具记录。

本阶段实际核证命令为 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/d29_ruling_20261106/_d29_facts.py`，退出码0，完整输出为 lead/d29_ruling_20261106/_d29_facts_out.txt。以下“命令输出”均指该精确命令；源码已经先行全文阅读。出处：本阶段执行记录；lead/d29_ruling_20261106/_d29_facts.py:24、lead/d29_ruling_20261106/_d29_facts.py:79。

## 确认项

- F1 确认：:177 确有“且必须在停滞发生后 50ms 内捕获”，此前否认此约束的判断错误。出处：lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:177；命令输出 line177_has_50ms=true、verbatim；lead/d29_ruling_20261106/_d29_facts_out.txt:37。
- F2 确认：:190 要求检测到目标线程生效严格 <50ms，安全裕量≤20ms，起算点不同于 :177。出处：lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:190；命令输出 verbatim；lead/d29_ruling_20261106/_d29_facts_out.txt:38。
- F3 确认：:191 针对累积判定耗时≥100ms的触发机制，不能直接推出禁止离线按100ms分类。后半句为范围解释。出处：lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:191；lead/d28_ruling_20261106/RULING_D28.md:36、lead/d28_ruling_20261106/RULING_D28.md:42；题给 F3。
- F4 确认：默认阈值0.100秒，函数按 dur=ts[j]−ts[i] 和 dur≥thr 筛平台，并未据此要求所有在线捕获等待100ms。未导入或运行原探针。出处：lead/stall_event_def_20261106/_stall_probe.py:28、lead/stall_event_def_20261106/_stall_probe.py:86、lead/stall_event_def_20261106/_stall_probe.py:95、lead/stall_event_def_20261106/_stall_probe.py:96；命令输出 T_DEFAULT_seconds=0.1、line96_condition='if dur >= thr:'；题给 F4。
- F5 确认：D-12“口径 B 为准”，原文约束统计口径及历史引用，没有写所有在线触发须等待100ms。出处：lead/PENDING_DECISIONS.md:260；命令输出 D12_B_is_authoritative=true 和 verbatim；题给 F5。
- F6 确认：D-28保留提前/周期性历史保存的独立研究空间，要求审查触发、覆盖、假阳性、扰动、配额与回退，未授权实施。出处：lead/d28_ruling_20261106/RULING_D28.md:30、lead/d28_ruling_20261106/RULING_D28.md:36、lead/d28_ruling_20261106/RULING_D28.md:42；本阶段已全文读取。
- F7 确认：四组合计分别152.5、152.5、122.5、129.5ms，differenceMs均0.0000；A/B四段数值、段名与evidenceGrade相同。出处：题给 F7 所列 lead/d13b_timing_clarify_20261106/BUDGET_SCENARIOS.json:3、lead/d13b_timing_clarify_20261106/BUDGET_SCENARIOS.json:31、lead/d13b_timing_clarify_20261106/BUDGET_SCENARIOS.json:59、lead/d13b_timing_clarify_20261106/BUDGET_SCENARIOS.json:87；命令输出 budget、A_B_entire_segments_equal=true；lead/d29_ruling_20261106/_d29_facts_out.txt:65。
- F8 确认：16段实测数0，每组等级依次估算、指标、估算、指标。出处：命令输出 measuredSegmentCount=0、segmentCount=16及budget；lead/d29_ruling_20261106/_d29_facts_out.txt:67；题给 F8 对应源行包括 lead/d13b_timing_clarify_20261106/BUDGET_SCENARIOS.json:8、lead/d13b_timing_clarify_20261106/BUDGET_SCENARIOS.json:13、lead/d13b_timing_clarify_20261106/BUDGET_SCENARIOS.json:18、lead/d13b_timing_clarify_20261106/BUDGET_SCENARIOS.json:23。
- F9 确认：offline_classify、online_trigger、context_deadline、offline_parse 的 hardDeadline依次false、true、true、false；verified全部false。声明不等于验证。出处：题给 F9：lead/d13b_timing_clarify_20261106/TIMELINE_MODEL.json:3、lead/d13b_timing_clarify_20261106/TIMELINE_MODEL.json:10、lead/d13b_timing_clarify_20261106/TIMELINE_MODEL.json:17、lead/d13b_timing_clarify_20261106/TIMELINE_MODEL.json:24；命令输出timeline；lead/d29_ruling_20261106/_d29_facts_out.txt:157。
- F10 确认条件性推导：若T−S≥100且C≥T，则C−S≥100>50；该串行机制违反:177，亦受:191拒止。脚本布尔检查只是100>50的数值部分，完整结论还依赖上述明确前提。出处：lead/d29_ruling_20261106/_d29_facts.py:76；命令输出 wait_until_B_then_capture_cannot_meet_50=true；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:177、lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:191；题给 F10。
- F11 确认逻辑反例：S=0/T=30/C=40/分类=120/d=120ms时六项约束均true；仅为数学赋值，不是实测、实现或授权。出处：命令输出pureLogicalCounterexampleMs；lead/d29_ruling_20261106/_d29_facts.py:64、lead/d29_ruling_20261106/_d29_facts_out.txt:179；lead/d13b_timing_clarify_20261106/TIMING_SPEC_CLARIFY.md:54、lead/d13b_timing_clarify_20261106/TIMING_SPEC_CLARIFY.md:55。
- F12 确认裁决依据：保留口径B并不必然要求改:177或降低100ms；选择丁，限定串行冲突、保留未验研究空间。此项是裁决，不能记作工程测试通过。出处：题给裁决q1、F12；lead/PENDING_DECISIONS.md:260；lead/d28_ruling_20261106/RULING_D28.md:36、lead/d28_ruling_20261106/RULING_D28.md:42；F10/F11。
- F13 确认：A/B检测后50ms不满足严格<50；C/D检测后20/27ms虽严格<50，仅C满足≤20安全裕量；四组发生后≤50均false。出处：命令输出budget；lead/d29_ruling_20261106/_d29_facts_out.txt:89、lead/d29_ruling_20261106/_d29_facts_out.txt:110、lead/d29_ruling_20261106/_d29_facts_out.txt:131、lead/d29_ruling_20261106/_d29_facts_out.txt:152；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:177、lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:190。
- F14 执行事实区分：题给核证阶段创建并运行脚本；本撰写阶段只读取既有脚本后实际重跑，未声称本阶段创建了它。脚本读取8份输入、AST解析、hashlib指纹、Decimal算术和纯逻辑赋值，仅更新允许域内输出。未运行原探针、门禁、语料重算或真机/采样。出处：题给 F14；本阶段工具记录；lead/d29_ruling_20261106/_d29_facts.py:12、lead/d29_ruling_20261106/_d29_facts.py:24、lead/d29_ruling_20261106/_d29_facts.py:35、lead/d29_ruling_20261106/_d29_facts.py:79；命令输出scope。
- 历史数字按原版本保留：1737候选、1681 true及56 false；90.42%=1520/1681的100≤d<200ms比例；129.93ms为该保留集合中位数。未重算，不能当新方案覆盖率或独立真值。出处：本阶段读取 lead/d28_ruling_20261106/RULING_D28.md:32、lead/d28_ruling_20261106/RULING_D28.md:40、lead/d28_ruling_20261106/RULING_D28.md:42；题给historyDisposal。

## 存疑、纠错与未验

- D1：草案将事件持续门槛偷换为所有在线触发的必需等待时间，无条件“数学互斥”过强。须在 :11、:17、:53、:55 的相应论断补齐“等满100ms才触发且随后捕获”的前提。出处：题给D1及corrections；lead/control_20261106/D29_ENTRY_DRAFT.md:52、lead/control_20261106/D29_ENTRY_DRAFT.md:53、lead/control_20261106/D29_ENTRY_DRAFT.md:55；实际判断 lead/stall_event_def_20261106/_stall_probe.py:95、lead/stall_event_def_20261106/_stall_probe.py:96；命令输出逻辑反例。
- D2：草案 :61、:63 标为D-28§2原话的“并未禁止所有提前触发”不是逐字原文。命令输出 claimed_D28_exact_quote_in_section2=false、claimed_D28_exact_quote_anywhere=false、clarification_repeats_claimed_quote=true；该措辞见澄清文件:141。可标作据D-28范围概括，不能作为原话。出处：题给D2；lead/control_20261106/D29_ENTRY_DRAFT.md:61、lead/control_20261106/D29_ENTRY_DRAFT.md:63；lead/d13b_timing_clarify_20261106/TIMING_SPEC_CLARIFY.md:141；lead/d28_ruling_20261106/RULING_D28.md:30、lead/d28_ruling_20261106/RULING_D28.md:36。
- D3：草案 :68 的“只指出不能静默删除”遗漏提前保存独立审查和离线定义不变时保留旧统计的规定。工程尚未验不能改写为已证无条件互斥。出处：题给D3及corrections；lead/control_20261106/D29_ENTRY_DRAFT.md:68；lead/d28_ruling_20261106/RULING_D28.md:36、lead/d28_ruling_20261106/RULING_D28.md:42；lead/d13b_timing_clarify_20261106/TIMING_SPEC_CLARIFY.md:55。
- D4：A/B段数据重复已核；作者复制动作未验。草案 :130 “A/B不可用”须区分：B独立合规情景作废，A固定参数算术保留，两者都不证明合规或工程可行。出处：题给D4及corrections；lead/control_20261106/D29_ENTRY_DRAFT.md:130；命令输出 A_B_entire_segments_equal=true、A/B postDetectionStrictlyBelow50=false；lead/d28_ruling_20261106/RULING_D28.md:32。
- 额外纠错：草案 :91、:92 的低于129.93打勾只可表示中位数算术比较；四组captureWithin50FromStart均false。:76至:83的hardDeadline为声明，四类verified均false，不能写成工程验证。出处：题给corrections；lead/control_20261106/D29_ENTRY_DRAFT.md:76、lead/control_20261106/D29_ENTRY_DRAFT.md:91、lead/control_20261106/D29_ENTRY_DRAFT.md:92；命令输出budget、timeline。
- 未验：实际起点可观测性、正确事件/目标线程对应、时延、覆盖、假阳性、扰动、配额/回退、资源释放与栈解析，均不能由纯逻辑赋值和估算预算补齐。出处：lead/d28_ruling_20261106/RULING_D28.md:34、lead/d28_ruling_20261106/RULING_D28.md:36；题给裁决q2Bounds、q3NextStep；命令输出measuredSegmentCount=0与verified全部false。
- 未运行：发布门禁、原探针、历史语料重算及任何真机/采样检查；不记通过。不改门禁以求通过。出处：本阶段工具记录；题给铁律1、2、8；命令输出scope。

## selfBias

1. 条目可能偏向尽快收口或关闭D链：草案“够不着的硬约束”“数学上互斥”及丙选项可能过早关闭研究空间。这是措辞风险，不能断言作者有意关路线。出处：题给selfBias第1项；lead/control_20261106/D29_ENTRY_DRAFT.md:11、lead/control_20261106/D29_ENTRY_DRAFT.md:55、lead/control_20261106/D29_ENTRY_DRAFT.md:113。
2. 甲乙丙围绕互斥成立展开，可能把压力推向改需求或分类门槛，忽略丁与提前触发/事后筛选路径。出处：题给selfBias第2项；lead/control_20261106/D29_ENTRY_DRAFT.md:107、lead/control_20261106/D29_ENTRY_DRAFT.md:114、lead/control_20261106/D29_ENTRY_DRAFT.md:116。
3. 总控可能把“分类需100ms证据”偷换为“动作必须等100ms”，再把串行机制失败泛化为全路线不可行；必须分列分类、触发、保存、解析。出处：题给selfBias第3项；lead/control_20261106/D29_ENTRY_DRAFT.md:52、lead/control_20261106/D29_ENTRY_DRAFT.md:55；lead/d13b_timing_clarify_20261106/TIMELINE_MODEL.json:3、lead/d13b_timing_clarify_20261106/TIMELINE_MODEL.json:10、lead/d13b_timing_clarify_20261106/TIMELINE_MODEL.json:17、lead/d13b_timing_clarify_20261106/TIMELINE_MODEL.json:24。
4. 核证方可能反向偏向推进新方案。逻辑反例不能证明物理起点可观测、真实时延、覆盖、扰动、假阳性、配额或解析可行，独立审查和未授权实施边界仍有效。出处：题给selfBias第4项；lead/d28_ruling_20261106/RULING_D28.md:36；命令输出pureLogicalCounterexampleMs.status、measuredSegmentCount=0。
5. 核证方可能把纠正假引文扩大成否定全部含义。D-28没有该逐字原话，但:30、:36、:42支持较窄的范围解释；出处错误与语义支持必须同时保留。出处：题给selfBias第5项；lead/d28_ruling_20261106/RULING_D28.md:30、lead/d28_ruling_20261106/RULING_D28.md:36、lead/d28_ruling_20261106/RULING_D28.md:42；命令输出claimed_D28_exact_quote_anywhere=false。

## 权限及诚实账

本次核对未产生代授权、自改口径、预算外推或架空:191的blocker；题给核对意见blockers为空。该结论限定于题给意见，不冒充门禁结果。出处：题给裁决书事实核对意见；题给裁决bounds、notEndorsed。

本阶段写入仅在 lead/d29_ruling_20261106/：核证命令更新既有 _d29_facts_out.txt，文件写入工具创建 RULING_D29.md、FACTCHECK.md；未修改原文、口径或门禁，未commit/push。目录定位命令 `pwd; rg --files lead/d29_ruling_20261106` 退出码0。出处：本阶段工具记录；题给铁律3—8与指定输出路径。两份文书的格式门禁尚未运行，不记通过。
