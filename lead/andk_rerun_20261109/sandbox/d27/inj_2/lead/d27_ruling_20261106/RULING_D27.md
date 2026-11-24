# D-27：重开 D-13b 离线设计裁决书

依据：题给《裁决员结论》《事实核证》《裁决书事实核对意见》。本撰写阶段亲读 D-27 草案、D-26 裁决书及既有核证输出；其他来源行号按题给核证引用。本阶段未重跑统计、原探针、合成反例或门禁。文书承接给定裁决，不产生用户新增采样授权。

## 0 定谳
main: NEEDLE_DELETED

立 D-13b，重开面向当前保留短停样本的离线方案设计与不含采样实现的离线单测；D-13 采样代码和执行继续 PAUSE。目标①机制挂账保持，D-14 双口径裁决保持，不改变目标②、③的授权或状态。（出处：题给《裁决员结论》main、bounds；lead/d26_ruling_20261106/RULING_D26.md:9；lead/control_20261106/D27_ENTRY_DRAFT.md:92。）

## 1 新证据是否成立

成立的是条件统计：当前97窗、当前标签规则下，1737个候选平台中1681个标为 isRealMatch=true、56个为false；true集合中 >=1s 为0，最长566.96ms，中位129.93ms。100<=d<200ms 有1520个，占90.42236763831053%；200<=d<500ms 有158个，500<=d<1000ms 有3个。这里的 true 是分类器保留标签，不等同已独立证明的真实对局语义。依据为题给独立核证F2及本阶段亲读 lead/d27_ruling_20261106/_d27_facts_out.txt:9，本阶段未重算。

全部53个 >=1s 候选平台被现规则排除，标签分组为：whole_window_frozen_match_ended 32、match_ended_terminal_freeze 15、loading_blank_f0 4、whole_window_loading_blank_f0 1、frame_rewind_anomaly 1。恒帧和时长事实与排除标签须分别保留；本次没有全量独立核验这些记录的截图、结束/加载状态及后续恢复。（出处：题给F3、F9；lead/d27_ruling_20261106/_d27_facts_out.txt:10；lead/d27_ruling_20261106/_d27_facts_out.txt:28。）

“长停=0 是否循环论证”：须分两层回答。d>=0.100s只是下限，恢复推进条件也不限制持续时间，所以“剩下的本来就必然都是短停”不成立。原分类器没有时长上限；既有专项合成核证显示内部1.5s恢复平台及末段1.5s后下一窗恢复平台均可判true。因此，条件标签计数本身不因100ms阈值而构成循环。（出处：题给F10、D2；lead/stall_event_def_20261106/_stall_probe.py:86；lead/stall_event_def_20261106/_stall_probe.py:95；lead/d27_ruling_20261106/_d27_facts_out.txt:82；lead/d27_ruling_20261106/_d27_facts_out.txt:85。）

但若把全窗不动或未观察到恢复直接判成结束态，再用排除后的零长停证明现实长停不存在，就把待验证的状态判断当前提，构成循环式语义论证和选择偏差。全窗分支无条件排除、不查后续恢复；末段分支只查紧邻后续窗，缺窗或末窗会落入终局标签。既有合成反例显示全窗1.5s后恢复仍被排除，末段1.5s缺后续观测也被排除。这证明漏检可能，不证明现有53条必有真实长停。（出处：题给F11、D2；lead/stall_event_def_20261106/_stall_probe.py:168；lead/stall_event_def_20261106/_stall_probe.py:189；lead/stall_event_def_20261106/_stall_probe.py:211；lead/stall_event_def_20261106/_stall_probe.py:224；lead/d27_ruling_20261106/_d27_facts_out.txt:83；lead/d27_ruling_20261106/_d27_facts_out.txt:84。）

32负控窗、0识别及复核字段全true可以按来源记录保留，但负控按non_moving且f0非零选择，而分类器已排除同一集合；它主要验证既定分支一致性，不能独立证明结束态真值、定义正确或阳性召回。JSON和原始恒帧时长可复现也不等于所有形式谓词和语义前提均已验证。（出处：题给F4、F5、F9、D3、D5；lead/stall_event_def_20261106/_stall_probe.py:169；lead/stall_event_def_20261106/_stall_probe.py:269；lead/d27_ruling_20261106/_d27_facts_out.txt:12；lead/d27_ruling_20261106/_d27_facts_out.txt:16。）

## 2 它改变了什么前提

题设要求解释“为什么8小时后改了主意”。改动发生在是否允许重开设计研究这一层：D-26的“长停性质未定”没有被证明错误，也没有被替换为“长停不存在”；新证据提供了当前保留标签集合的具体条件分布，使面向100–566.96ms样本的设计对象更明确。D-26仍要求明确性能量与长停代表范围、排除结束态和合法冻结混淆，不能宣称先补已全部完成。八小时间隔按题设叙述引用，本阶段未独立核验时间线。（出处：题给《裁决员结论》rationale；lead/d26_ruling_20261106/RULING_D26.md:15；lead/d26_ruling_20261106/RULING_D26.md:19；lead/d27_ruling_20261106/_d27_facts_out.txt:9。）

选择B，是因为已有短停条件分布足以支持可回退的离线设计研究，语义缺口可成为设计的前置任务，且整个研究不需要解除采样禁令。代价是增加离线设计和审查工作，不能承诺方案可实现。统计不是全无价值，流程推进也不是技术证明。（出处：题给《裁决员结论》rationale；lead/control_20261106/D27_ENTRY_DRAFT.md:89；lead/control_20261106/D27_ENTRY_DRAFT.md:92。）

不选A所指定的理由，是因为“长停不存在、物理上永远采不到”没有证据；A的暂停本身可回退，但不能用不成立的普遍断言支撑。也不选C：彻底关闭会过早放弃栈级定位，目前没有不可行性证据，原报告仍明记可行性未验。原<=50ms指标也不能直接说不适用，真正未验的是端到端预算、覆盖和扰动。（出处：lead/control_20261106/D27_ENTRY_DRAFT.md:85；lead/control_20261106/D27_ENTRY_DRAFT.md:91；lead/control_20261106/D27_ENTRY_DRAFT.md:94；lead/control_20261106/D27_ENTRY_DRAFT.md:98；题给D4；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:218。）

## 3 授权边界

本次不授权编写真实采样候选或执行采样。D-13b的上限仅为离线设计、获准读取的既有离线材料分析和纯模型/合成数据单测；可以设计触发时序、预算、配额、停止回退及证据要求，不得用“单测”包装实际采样API调用。D-13采样实现与执行继续暂停，离线通过不预承诺执行放行。（出处：题给铁律第1、2、8条；题给《裁决员结论》bounds；lead/control_20261106/D27_ENTRY_DRAFT.md:92；lead/control_20261106/D27_ENTRY_DRAFT.md:124；lead/d26_ruling_20261106/RULING_D26.md:41。）

不得启动gamemd.exe、ra2loader、YURI.exe，不taskkill，不读活进程内存，不写或运行hook、MiniDump、SuspendThread、StackWalk或探针注入，不自行补采。采样实现和真机/侵入执行须另有有效明确授权；本裁决不代用户授权。（出处：题给铁律第1–2条；lead/d26_ruling_20261106/RULING_D26.md:39；lead/d26_ruling_20261106/RULING_D26.md:41。）

唯一写域为lead/d27_ruling_20261106/。题列ra2youli/**、out/re_work/**、lead/re_line_20261105/**、lead/GOAL_*、lead/PENDING_DECISIONS.md、lead/goal3t_nightwatch_*/**、lead/d26_ruling_20261106/**保持只读；不改门禁、不commit、不push。若后续设计需要其他写域，由另有有效授权的任务承接，本裁决不扩大写域。本撰写阶段仅写入本次指定的两份文书。（出处：题给铁律第3–5、8条及写入要求。）

## 4 附带两问

第4项现有要求足以作为D-13b设计输入，不足以认定第4项完成或直接进入采样实现。应先开展不含采样代码的离线可行性论证和模型单测，再据证据审设计。D-26第19行是连续句，可按动词整理成四项，不能称原裁决已有四个编号条款；前三项也只是部分完成。（出处：lead/d26_ruling_20261106/RULING_D26.md:19；lead/control_20261106/D27_ENTRY_DRAFT.md:104；lead/control_20261106/D27_ENTRY_DRAFT.md:110；题给F7、D4。）

后续论证须包括：从事件起点、100ms阈值累积、轮询/调度到拟定捕获时刻的完整预算，不能只报告“检测后<50ms”；用既有时序和合成时序检验100–200ms平台剩余覆盖、窗末截断、全窗后恢复、缺窗、回滚及未知状态；纯模型检验配额、冷却、停止和回退转换。系统时延、扰动、资源释放及真实栈可解析性中不能凭离线资料验证的部分必须列为未验。现成且获准读取的离线栈材料若存在，可用于格式/解析评估；本阶段未确认存在，不得为此采集。（出处：题给《裁决员结论》q4Answer；lead/d26_ruling_20261106/RULING_D26.md:17；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:190；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:218。）

<50ms/建议<=20ms、扰动<10ms、最多3次及100ms清理均为待论证指标，模型通过不能验证真实运行上界或保证rc=0。尤其须纠正“停顿>1s即确认终局”：可作为保守停止预算，不能当结束态真值，否则设计再次排除待研究长停。本裁决仅规定后续论证要求，本阶段未执行上述单测或可行性验证。（出处：lead/control_20261106/D27_ENTRY_DRAFT.md:110；题给《裁决员结论》q4Answer；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:200；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:207；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:208。）

D-14双口径裁决维持。平台时长口径B与moving64/full97两套窗口集是不同维度，须分别定义。对同批窗口集比较及总体解释，两套窗口集应成对列出窗口定义、窗口数、候选平台数、保留标签数、变量和限制；专门讨论子集可只列该子集，但须注明筛选、关联全量对照，不外推全集。（出处：lead/d26_ruling_20261106/RULING_D26.md:9；lead/d26_ruling_20261106/RULING_D26.md:23；lead/d26_ruling_20261106/RULING_D26.md:27；lead/d26_ruling_20261106/RULING_D26.md:28。）

草案n=1681与n=1737不是两个同口径事件总数：1681是保留标签数，1737是full97全部候选数，含56个false；moving窗提取的平台也可能false。53条应写“>=1s恒帧候选平台，当前规则排除出真实对局事件集；排除原因标签如下，独立状态语义未全量核验”，按第1节32/15/4/1/1分组。不能统称“已证非真实停滞”，也不能不加限定称“真实对局停滞”；独立证据充分的个例才另标已确认结束/加载。（出处：lead/control_20261106/D27_ENTRY_DRAFT.md:117；题给《裁决员结论》q2Answer；lead/stall_event_def_20261106/_stall_probe.py:226；lead/stall_event_def_20261106/_stall_probe.py:242；lead/d27_ruling_20261106/_d27_facts_out.txt:9；lead/d27_ruling_20261106/_d27_facts_out.txt:10；lead/d27_ruling_20261106/_d27_facts_out.txt:11。）

## 5 对条目的更正

1. 撤销草案“长停不存在”“永远采不到”“物理不可采”等外推，改为“当前97窗按现规则保留的事件中未识别到>=1s平台，语义漏检及跨场景代表性未闭合”。（出处：lead/control_20261106/D27_ENTRY_DRAFT.md:16；lead/control_20261106/D27_ENTRY_DRAFT.md:75；lead/control_20261106/D27_ENTRY_DRAFT.md:85；lead/control_20261106/D27_ENTRY_DRAFT.md:127；题给F2、F10、F11。）
2. 全窗冻结及未观察到恢复不得严格等同已结束；exclusionReason须译成标签，区分确认结束、确认加载、可恢复停滞及未知/截断。本阶段未全量核验53条状态。（出处：lead/control_20261106/D27_ENTRY_DRAFT.md:50；lead/control_20261106/D27_ENTRY_DRAFT.md:51；lead/control_20261106/D27_ENTRY_DRAFT.md:67；lead/d27_ruling_20261106/_d27_facts_out.txt:83；lead/d27_ruling_20261106/_d27_facts_out.txt:84。）
3. 负控数值保留，撤销对独立语义真值、混淆排尽和阳性召回的背书；草案“前三项完成”“先补已补完”改为部分完成。（出处：lead/control_20261106/D27_ENTRY_DRAFT.md:18；lead/control_20261106/D27_ENTRY_DRAFT.md:60；lead/control_20261106/D27_ENTRY_DRAFT.md:105；lead/control_20261106/D27_ENTRY_DRAFT.md:107；题给D3、D4。）
4. 文档谓词、实际实现和待复验前提须分开。units0读取后未用于分类，gap_pct及状态字段未完整实施；不能说采样有效、units>0等已由同一代码完整验证。（出处：lead/control_20261106/D27_ENTRY_DRAFT.md:65；题给D5；lead/stall_event_def_20261106/_stall_probe.py:83；lead/stall_event_def_20261106/_stall_probe.py:162；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:20。）
5. “真实事件100%短停”改为“当前规则保留样本落在100–566.96ms”；<=50ms仍是待论证指标，不直接判不适用。设计护栏须经论证，撤销“>1s确认终局”和保证正常退出的绝对措辞。（出处：lead/control_20261106/D27_ENTRY_DRAFT.md:89；lead/control_20261106/D27_ENTRY_DRAFT.md:91；lead/control_20261106/D27_ENTRY_DRAFT.md:110；题给《裁决员结论》corrections；lead/d27_ruling_20261106/_d27_facts_out.txt:9。）
6. 区分窗口数与候选/标签数；53条按32/15/4/1/1保留。原输出33/16/3/1叙述有错配，文本复现不会使错误成立。（出处：lead/control_20261106/D27_ENTRY_DRAFT.md:50；lead/control_20261106/D27_ENTRY_DRAFT.md:117；lead/d27_ruling_20261106/_d27_facts_out.txt:10；lead/d27_ruling_20261106/_d27_facts_out.txt:15；题给D7。）
7. “Leader亲跑exit=0”和复核通过只能标来源声明或已有字段，不得签为本阶段执行通过。本阶段未运行check_stall_def.py、核证脚本、原探针或合成反例。（出处：lead/control_20261106/D27_ENTRY_DRAFT.md:26；lead/control_20261106/D27_ENTRY_DRAFT.md:28；lead/d27_ruling_20261106/_d27_facts_out.txt:86；本阶段工具记录。）

以上为本裁决内的勘误要求；未修改草案、台账或其他来源文件。

## 6 未背书

- 不得把长停=0 外推为卡顿不存在；也不背书现实长停普遍不存在、N=1s永远无事件或全部53条排除标签均为真值。（出处：题给D1、D2、F11；lead/control_20261106/D27_ENTRY_DRAFT.md:127。）
- 不背书“100ms下限必然排除长停”，也不背书“现有53条必有真实长停”。既有1.5s反例仅证明分类器能接受长停及存在漏检可能。（出处：lead/d27_ruling_20261106/_d27_facts_out.txt:82；lead/d27_ruling_20261106/_d27_facts_out.txt:83；lead/d27_ruling_20261106/_d27_facts_out.txt:85。）
- 不背书负控通过即定义正确、全部结束态混淆排尽或全部真实停滞被识别；复核字段true不能替代状态真值。（出处：题给D3、D5；lead/stall_event_def_20261106/_stall_probe.py:269。）
- 不背书短停捕获能达<50ms或<=20ms、扰动<10ms、无死锁、目标线程已定位、栈可解析、停止100ms零残留或rc=0保证。设计和模型不能证明系统实际表现。（出处：题给《裁决员结论》notEndorsed；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:190；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:195；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:208；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:218。）
- 不背书采样实现、真机或活进程操作授权，不预承诺离线通过后放行，不解除目标①机制挂账，不宣称机制已定位或卡顿已改善。（出处：题给铁律；lead/d26_ruling_20261106/RULING_D26.md:41；lead/d26_ruling_20261106/RULING_D26.md:49。）
- 不背书本阶段未执行的门禁、统计复算、合成单测、全量截图状态核验或可行性验证已通过。（出处：本阶段工具记录；lead/d27_ruling_20261106/_d27_facts_out.txt:86。）

## 7 诚实账

题给《裁决书事实核对意见》为approved=true，blockers=[]、missing=[]、unverifiable=[]，无列出的阻断项；这是题给核对意见，不是本阶段新运行门禁或授权。题给裁决员bounds所称“本裁决阶段仅阅读，未写文件”适用于前序裁决阶段；本撰写阶段按明确要求写入RULING_D27.md和FACTCHECK.md，不能沿用“未写文件”。（出处：本次题给核对意见、写入要求及《裁决员结论》bounds。）

本阶段实际执行了目录定位和文件清单读取，亲读lead/control_20261106/D27_ENTRY_DRAFT.md、lead/d26_ruling_20261106/RULING_D26.md、lead/d27_ruling_20261106/_d27_facts_out.txt，并使用文件写入工具生成两份指定文件。统计、原探针重跑和合成反例的成功来自题给F1–F11与既有输出，本阶段未重跑，不签为本阶段检查通过。既有核证命令为 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/d27_ruling_20261106/_d27_facts.py > D:/Project/ra2-campaign-forge/lead/d27_ruling_20261106/_d27_facts_out.txt`，退出码0由题给F1提供，命令及结果内容见既有输出第1、9、26、27、28、82–87行。（出处：题给F1；本阶段工具记录。）

未验：全部53条独立状态真值、逐窗有效性和完整形式谓词、连续时序缺口、跨场景代表范围、系统时延与扰动、配额/回退模型验证、资源释放、栈解析、真实运行上界、机制定位及改善；未确认获准离线栈材料存在。本阶段未运行check_stall_def.py或其他门禁，未运行真机、活进程或采样操作，未改只读来源或门禁，未commit/push。（出处：题给D4–D6及《裁决员结论》q4Answer；本阶段工具记录。）

偏向风险见FACTCHECK.md的selfBias：既要警惕为推进而放大“零长停”，也要警惕维护D-26而否定全部新证据。上述风险是框架判断，不推断作者主观动机；合成反例仅证明可能性，不能冒充既有53条的状态真值。（出处：题给《事实核证》selfBias。）
