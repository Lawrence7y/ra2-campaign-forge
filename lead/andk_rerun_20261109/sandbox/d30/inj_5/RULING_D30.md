# D30 裁决书：三档 k 的代价与离线论证资格

## 0 定谳
q1: 戊

裁定为“保留提前候选、事后分类的离线论证资格，现阶段不选定任何 k 档进入实现或执行”。优先以 k=10 检验高召回候选能否承受成本，以 k=25 作边界敏感性对照，不采纳 k=50 作为满足发生后50ms捕获要求的现行方案。D-13 实现与执行继续 PAUSE，目标①机制挂账不解除。依据：题给裁决员结论 q1、q1Rationale；lead/d29_ruling_20261106/RULING_D29.md:6；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:177。

本书沿用口径B全部约束，分别保留发生后50ms内捕获、检测至生效严格<50ms及安全裕量≤20ms、拒止累计判定≥100ms；提前候选与最终分类分开，捕获失败不得从原统计母体静默剔除。依据：题给裁决员结论 bounds 第1项；lead/d29_ruling_20261106/RULING_D29.md:6；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:177；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:190；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:191。

## 1 三档权衡的实质

下表“误报率”仅指误触发数/总触发数，“查准率”仅指最终持续时间 d≥100ms 的候选数/总触发数，不是战斗真实事件标签查准率，也不是 FP/(FP+TN)。来源：题给核证 F3、F4、D5；lead/early_trigger_feasibility_20261106/EARLY_TRIGGER_FEASIBILITY.md:131；lead/early_trigger_feasibility_20261106/_feasibility_probe.py:504；lead/early_trigger_feasibility_20261106/_feasibility_probe.py:506；本次命令A输出 Q3。

| k | 总触发 | 误触发 | d≥100ms候选 | 误报率 | 查准率 | 理想500Hz首点至第k点跨度 | 语料内触发跨度中位数 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 28294 | 26590 | 1704 | 93.98% | 6.02% | 18ms | 17.613ms |
| 25 | 5343 | 3639 | 1704 | 68.11% | 31.89% | 48ms | 47.766ms |
| 50 | 1866 | 162 | 1704 | 8.68% | 91.32% | 98ms | 97.7505ms |

表中数值由本次命令A全量复现；k点只有k−1个间隔，原判据为 length=j−i+1、length≥k。三档均有 realHits=1681、missedReal=0，另23条 d≥100ms 候选不属于保留真实标签集合；若按该集合计算，查准率分别为5.9412%、31.4617%、90.0857%。依据：题给核证 F3、F4、D2、D5；lead/early_trigger_feasibility_20261106/_feasibility_probe.py:499；lead/early_trigger_feasibility_20261106/_feasibility_probe.py:502；本次命令A输出 Q3。

k=10 的代价是大量提前候选：26590/28294最终不足100ms，可能消耗保存、队列与配额资源；其收益是较早产生候选，仍值得离线检验。93.98%本身不能决定成本是否可接受，尚须定义实际保存负担、配额竞争和扰动界限。Q5 verified=false，四项工程依赖未验。依据：题给裁决 q1Rationale、核证 F6、D1；lead/early_trigger_feasibility_20261106/FEASIBILITY_STATS.json:74；本次命令A输出 Q5。

k=25 降低候选负担，但名义48ms已接近发生后50ms预算；不能写成必定50ms、绝无余量。条件算式0.5+48+1=49.5ms仅反驳“必无余量”，没有测得实际物理起点误差或保存时延，也不证明工程合规。依据：题给核证 D2；lead/control_20261106/D30_ENTRY_DRAFT.md:88；本次命令A输出 finiteGridCounterexample 的 engineeringVerified=false。

k=50 的误触发占比最低，但名义98ms、语料中位97.7505ms明显不适合作为发生后50ms捕获的及时机制；不能为降低误报而牺牲:177。也不能把98ms写成必已过100ms。依据：题给裁决 q1Rationale、核证 D2；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:177；本次命令A输出 Q3 k=50。

## 2 选择与理由

目标①需要停滞期间的机制证据。missedReal=0证明的是题给语料中的候选覆盖，没有证明正确线程上下文在物理起点S后50ms内保存。1677/1681=99.7620464%也只是观测首拍锚点下的理论覆盖；四条startTick=0缺前序信息，物理S与实际保存时刻C仍未知，不能判成物理采不到。依据：题给裁决 q1Rationale、corrections 第1项；核证 F2、D4；lead/early_trigger_feasibility_20261106/_feasibility_probe.py:343；lead/early_trigger_feasibility_20261106/EARLY_TRIGGER_FEASIBILITY.md:88；本次命令A输出 Q2 total。

因此保留 k=10 离线基准、k=25 边界对照，同时保持实现执行PAUSE。继续离线论证的代价有限、可停止；它不代表接受 k=10 的实际开销，也不代表 k=25 已合规或三档已全部被证明不可能。误报容忍标准尚未定义，Q5未验，不能凭比例关闭整条路线。依据：题给裁决 q1Rationale；核证 D1、F6；lead/control_20261106/D30_ENTRY_DRAFT.md:95；lead/control_20261106/D30_ENTRY_DRAFT.md:125；lead/d29_ruling_20261106/RULING_D29.md:47。

D链继续朝物理起点与时间预算可审查、事件状态可区分、候选成本与覆盖可计量、既有语料内机制假说可检验的方向推进；本书不指定采集手段，不关闭整条栈采样路线，未来执行授权另议。依据：题给裁决 q1Rationale；lead/d29_ruling_20261106/RULING_D29.md:20；lead/d29_ruling_20261106/RULING_D29.md:28；lead/d29_ruling_20261106/RULING_D29.md:47。

## 3 配额覆盖率的可接受性

1.55%–6.96%可有条件地服务于目标①探索性抽样取证，不能承诺全量观测，也不足以证明能闭合真实多单位卡顿机制。承认抽样属性，不放开配额；N=1/3/5只保留为离线预算情景，未选定为实际设计参数。依据：题给裁决 q2Quota；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:170；lead/d29_ruling_20261106/RULING_D29.md:20。

| 每窗理想配额N | 理想捕获/1681 | 放弃 | 理想覆盖率 |
| --- | ---: | ---: | ---: |
| 1 | 26/1681 | 1655 | 1.55% |
| 3 | 73/1681 | 1608 | 4.34% |
| 5 | 117/1681 | 1564 | 6.96% |

该表仅按26个非空事件窗求和 sum(min(N,事件数))，假设配额只由真实事件消耗；104是语料文件数，非真实事件窗数。每非空窗均值64.6538事件，配额5并非覆盖约三分之一。在线误触发抢占后没有同等覆盖保证。依据：题给核证 F5、D6；lead/early_trigger_feasibility_20261106/_feasibility_probe.py:549；lead/early_trigger_feasibility_20261106/_feasibility_probe.py:558；lead/control_20261106/D30_ENTRY_DRAFT.md:66；本次命令A输出 real event windows、Q4。

下一步先离线核算候选按时间顺序耗尽配额后的真实事件覆盖，并按会话、窗口、时长及可用状态标签披露偏差、未覆盖母体与窗边界未知；明确支持或否定具体机制假说需要什么证据。少量样本可能帮助形成假说，但当前没有上下文证据，代表性、因果充分性和修复收益均未验；若有限预算不足，应登记证据不足。依据：题给裁决 q2Quota；核证 F5、F6、D6；lead/control_20261106/D30_ENTRY_DRAFT.md:60；lead/control_20261106/D30_ENTRY_DRAFT.md:68；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:179。

## 4 触发判据的下一步

要求重新设计并离线比较候选判据，不预定P95相对阈值胜出。早期连续k点同帧不足以确认最终d≥100ms，但D29允许提前候选、事后按口径B分类，故早期不要求零误报。相对帧间隔只能作为待验证候选，须审查历史基线可用性、抖动、阈值漂移、额外等待、边界事件及配额竞争；不得以等待P95突破时间约束。依据：题给裁决 q3Criterion；lead/control_20261106/D30_ENTRY_DRAFT.md:110；lead/control_20261106/D30_ENTRY_DRAFT.md:114；lead/d29_ruling_20261106/RULING_D29.md:20；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:190；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:191。

内部IN_TACTICAL/SCORE_SCREEN/PAUSED/LOADING继续登记为数据缺口；它们可帮助区分战斗、计分、暂停、加载，单凭IN_TACTICAL不能区分战斗内正常慢帧与停滞，也不能给出阻塞机制。相同早期外部观测可能有不同后续，若要求早期高精度确认，需要额外且有证据支持的区分信息；现有材料不证明某一种旗标必要且充分，也不要求取得旗标后才能做全部离线工作。依据：题给裁决 q3Criterion；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:176；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:177；lead/control_20261106/D30_ENTRY_DRAFT.md:115。

20–30FPS仅说明条件重叠可能：33.333…–50ms、16.666…–25个500Hz周期；不能解释全部93.98%误触发。严格该时长带只有3215/26590=12.091%，且游程采样跨度不是独立测得的完整帧执行耗时。优先明确物理起点S的可观测性与误差、实际保存时刻C的合规证据，并联合审查成本和配额，不能只继续调k。依据：题给裁决 q3Criterion、核证 F8、D3；lead/control_20261106/D30_ENTRY_DRAFT.md:54；本次命令A输出 FPS、Q3 k10 FPS20to30DurationBand。

## 5 授权边界

启动gamemd.exe、ra2loader、YURI.exe，不授权taskkill、读取活进程内存、E3、hook、MiniDump、SuspendThread、StackWalk、探针注入以及任何采样代码或执行。D-13实现执行继续PAUSE，目标①机制挂账保留。依据：本次题给铁律1、2；题给裁决 bounds 第2项；lead/control_20261106/D30_ENTRY_DRAFT.md:122；lead/control_20261106/D30_ENTRY_DRAFT.md:128；lead/control_20261106/D30_ENTRY_DRAFT.md:129。

修改题列只读路径、口径B、需求原文、门禁脚本；唯一写域为lead/d30_ruling_20261106/，不commit、不push。Python使用隔离模式、UTF-8、绝对脚本路径，指纹使用hashlib。本阶段仅在允许写域创建本书与FACTCHECK.md，并运行指定离线核证脚本；未改门禁。依据：本次题给铁律3—8及本阶段工具调用记录。

## 6 未背书

- 不得把误报率高外推为栈采样不可行，也不得把99.76%覆盖率外推为方案可行。依据：题给裁决 notEndorsed 第1、2项；lead/control_20261106/D30_ENTRY_DRAFT.md:125；lead/control_20261106/D30_ENTRY_DRAFT.md:126；核证 D1、D4。
- 不背书k10已获执行批准、missRate=0等于真实捕获零遗漏、k25已合规，或k50可牺牲:177采用。依据：题给裁决 notEndorsed 第3项；lead/d29_ruling_20261106/RULING_D29.md:28；核证 F3、D2。
- 不背书低配额样本具有代表性、理想覆盖率为在线保证、可以放开配额，或已取得推进真实修复的机制证据。依据：题给裁决 notEndorsed 第4项；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:170；核证 F5、F6、D6。
- 不背书内部战术旗标足以区分战斗内慢帧与停滞、P95已验证、20–30FPS已解释全部误报。依据：题给裁决 notEndorsed 第5项；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:176；核证 D3。
- 不把n=1681与n=1737当同口径对照，不解除目标①机制挂账，不宣称修复完成或工程验收。依据：题给裁决 notEndorsed 第6项；lead/control_20261106/D30_ENTRY_DRAFT.md:127；lead/control_20261106/D30_ENTRY_DRAFT.md:128。

## 7 诚实账

题给“裁决书事实核对意见”为approved=true、blockers=[]、missing=[]、unverifiable=[]，未列出需要登记的代授权、改约束或外推阻断项；这不代表工程验证通过。依据：本次题给核对意见全文；题给裁决 bounds 第4项。

裁决员阶段未运行核证脚本；本次撰写阶段实际执行命令A：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/d30_ruling_20261106/_d30_facts.py`，退出码0，输出 `corpus: {"files": 104, "samples": 1125992}`、`checks: "All numeric assertions passed"`。这是全量离线数值核证通过，不把上游运行冒充本阶段运行，也不把原探针、check_feasibility.py或原门禁计为通过；后三者本次未运行。依据：本阶段命令A工具返回；题给裁决 bounds 第4项；题给核证 F1。

工程耗时、扰动、实际捕获覆盖、真实修复、物理S及实际C均未验。Q5仍strictFalse=true、dependencyCount=4；未开展真机、活进程读取或采样实现。488.616ms只是起点前采样间隔最大值，不能证明采样线程被卡住，不能认作实测起点误差。依据：本次命令A输出 Q1、Q5、scope；lead/early_trigger_feasibility_20261106/_feasibility_probe.py:244；题给核证 F6、D7。

17.7次/秒是64×25=1600秒近似分母下总触发频率17.68375的舍入值，同前提误触发频率为16.61875次/秒。实际总窗时长本次未积分，不作为实测速率。依据：本次命令A输出 frequencyAssuming64WindowsOf25Seconds；题给核证 D8；lead/early_trigger_feasibility_20261106/EARLY_TRIGGER_FEASIBILITY.md:146。

作者可能偏向尽快关闭D链、偏好低误报、偏爱20–30FPS因果故事或漂亮的99.76%覆盖，也可能因强调抓外推而过度保留路线。本书不据此推断主观动机；以未定义成本、未测S/C、Q5未验及条件反例不证工程可达约束结论，完整偏差账见FACTCHECK.md。依据：题给核证 selfBias 全五项；核证 D1—D4、F6。
