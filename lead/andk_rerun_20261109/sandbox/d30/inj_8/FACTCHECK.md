# D30 事实核对账

本账逐项保留题给核证F1—F8、D1—D8及，区分上游核证、裁决员阶段和本次撰写阶段。题给裁决书核对意见approved=true，blockers、missing、unverifiable均为空；不据此宣称工程合规。出处：本次题给“事实核证”“裁决员结论 bounds 第4项”“裁决书事实核对意见”。

本次实际命令A：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/d30_ruling_20261106/_d30_facts.py`。退出码0；输出 `corpus: {"files": 104, "samples": 1125992}` 和 `checks: "All numeric assertions passed"`。下文“命令A输出”均指本次工具返回，不冒称为原探针或原门禁结果。原探针、check_feasibility.py、原门禁均未运行；真机、活进程读取、采样实现和工程验证均未做。出处：本阶段命令A工具返回scope、checks；题给F1、裁决bounds第4项。

## 确认事项

1. **F1：全量离线数值断言通过。** 上游核证称已完整读取草案并保存脚本及输出；本阶段独立运行同一指定脚本，104份语料、1125992点，退出码0。上游输出路径为lead/d30_ruling_20261106/_d30_facts_out.txt；本阶段未声称重新保存该输出文件，也未声称运行原探针或工程门禁。出处：题给F1；命令A输出corpus、checks、scope。
2. **F2：Q2三桶与总量复现。** 总数/可覆盖数为1520/1517、158/157、3/3，总计1677/1681=99.7620464009518%。其锚点为observed t[startTick]，非物理起点S。出处：lead/early_trigger_feasibility_20261106/FEASIBILITY_STATS.json:11；题给F2、D4；命令A输出Q2各桶、Q2 total。
3. **F3：Q3三档计数与算术一致。** k10总/误/d≥100ms为28294/26590/1704，k25为5343/3639/1704，k50为1866/162/1704；均sumEqualsTotal=true、missedReal=0，含义限于语料候选覆盖。出处：lead/early_trigger_feasibility_20261106/_feasibility_probe.py:492；题给F3；命令A输出Q3三档。
4. **F4：误触发占比及持续时间口径查准率复现。** k10为93.97752173605711%/6.022478263942886%，k25为68.10780460415496%/31.89219539584503%，k50为8.681672025723474%/91.31832797427653%。分母均为总触发数，误触发占比非FP/(FP+TN)。出处：lead/early_trigger_feasibility_20261106/EARLY_TRIGGER_FEASIBILITY.md:131；题给F4；命令A输出Q3 falsePercent、precisionPercent。
5. **F5：Q4理想配额复现。** N=1/3/5捕获26/73/117，放弃1655/1608/1564，覆盖1.5466983938132064%/4.3426531826293875%/6.960142772159429%。算法仅对26个非空真实事件窗求sum(min(N,事件数))，配额只由真实事件消耗。出处：lead/early_trigger_feasibility_20261106/_feasibility_probe.py:549；题给F5；命令A输出real event windows、Q4。
6. **F6：Q1间隔与Q5未验复现。** 1677条有前序点事件的起点前间隔中位2.515000000130385ms、最大488.61599999509053ms；Q5 strictFalse=true、dependencyCount=4。四项依赖涉及现场保存耗时、线程挂起恢复耗时、队列压力、并发计数扰动；其实际工程确认均未验，本书不授权实施。出处：lead/early_trigger_feasibility_20261106/FEASIBILITY_STATS.json:7；lead/early_trigger_feasibility_20261106/FEASIBILITY_STATS.json:74；题给F6；命令A输出Q1、Q5。
7. **F7：状态缺口与原约束保留。** :176列内部IN_TACTICAL/SCORE_SCREEN/PAUSED/LOADING缺口；:177规定发生后50ms内捕获；:190规定检测至生效严格<50ms、安全裕量≤20ms；:191拒止累计判定≥100ms。D29保留上述约束与口径B，实现执行PAUSE。出处：lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:176；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:177；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:190；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:191；lead/d29_ruling_20261106/RULING_D29.md:6；命令A对应原文摘录；题给F7。
8. **F8：20–30FPS条件换算成立。** 30FPS=33.333333333333336ms=16.666666666666668个500Hz周期，20FPS=50ms=25周期；16.65是先舍入33.3ms再乘0.5的结果。仅为条件算术，非误触发物理因果证明。出处：lead/control_20261106/D30_ENTRY_DRAFT.md:51；题给F8；命令A输出FPS 30、FPS 20。

## 存疑、更正及未验事项

1. **D1：未证明三档均无法同时满足误报成本与:177，更不能关闭栈采样路线。** 草案未定义可接受误报阈值，另列接受高误报后筛选选项，且自设禁止路线外推边界；Q5未验。因此仅能说三档均未获满足全部要求的工程证明。出处：lead/control_20261106/D30_ENTRY_DRAFT.md:82；lead/control_20261106/D30_ENTRY_DRAFT.md:95；lead/control_20261106/D30_ENTRY_DRAFT.md:125；lead/d29_ruling_20261106/RULING_D29.md:26；题给D1；命令A输出Q5 strictFalse=true。
2. **D2：k点不可写成k个间隔。** 判据length=j−i+1、length≥k；500Hz理想跨度18/48/98ms，实测首观测至第k点中位17.613/47.766/97.7505ms。k25条件反例0.5+48+1=49.5ms、below50ms=true，但engineeringVerified=false，仅反驳必无余量；k50也非必已过100ms，其典型跨度仍不适合作为:177及时机制。出处：lead/early_trigger_feasibility_20261106/_feasibility_probe.py:499；lead/early_trigger_feasibility_20261106/_feasibility_probe.py:502；lead/control_20261106/D30_ENTRY_DRAFT.md:88；lead/control_20261106/D30_ENTRY_DRAFT.md:92；题给D2；命令A输出Q3、finiteGridCounterexample。
3. **D3：94%误报的20–30FPS物理归因未验。** k10误触发游程17454段<32ms、5781段32–50ms、3355段>50且<100ms；严格33.333…–50ms仅3215/26590=12.09101165851824%。游程采样跨度非完整帧执行时长，不可反推正常FPS。可复现的是len≥10而最终d<100ms被统计为误触发；正常帧率、亚100ms慢帧、抖动和状态混杂的因果份额均未验。出处：lead/control_20261106/D30_ENTRY_DRAFT.md:50；lead/control_20261106/D30_ENTRY_DRAFT.md:54；lead/early_trigger_feasibility_20261106/_feasibility_probe.py:527；题给D3；命令A输出Q3 k=10、Q3 k10 FPS20to30DurationBand。
4. **D4：四条未知非物理不可能，99.76%非真实保存成功率。** 四条均startTick=0，无前序点；算法使用观测首拍+50ms，未观测物理S、实际C。草案“物理上采不到”及“要求成立”必须降格；原可行性文本本已称语料不足以判定。出处：lead/control_20261106/D30_ENTRY_DRAFT.md:12；lead/control_20261106/D30_ENTRY_DRAFT.md:25；lead/control_20261106/D30_ENTRY_DRAFT.md:34；lead/early_trigger_feasibility_20261106/_feasibility_probe.py:343；lead/early_trigger_feasibility_20261106/EARLY_TRIGGER_FEASIBILITY.md:88；题给D4；命令A输出Q2 total。
5. **D5：1704不是1704个真实战斗事件。** 原算法先以dur≥0.100计数，再查real_map；其中1681属保留真实标签、23不属。按保留真实标签计算查准率为5.941188944652576%、31.461725622309565%、90.08574490889603%。原表可保留，但须标明d≥100ms口径。出处：lead/early_trigger_feasibility_20261106/_feasibility_probe.py:504；lead/early_trigger_feasibility_20261106/_feasibility_probe.py:506；题给D5；命令A输出Q3 realHits、durationGE100NotReal、strictRealPrecisionPercent。
6. **D6：104窗、配额5覆盖约三分之一错误，在线保证未验。** 104是语料文件数，真实事件位于26个非空窗，均值64.65384615384616事件/非空窗；N5为117/1681=6.960142772159429%。Q4仅取真实事件前N条，未计误触发抢占。须另做按候选时间顺序消耗配额的离线情景；该后续情景本阶段未运行。出处：lead/control_20261106/D30_ENTRY_DRAFT.md:66；lead/early_trigger_feasibility_20261106/_feasibility_probe.py:549；lead/early_trigger_feasibility_20261106/_feasibility_probe.py:558；题给D6；命令A输出real event windows、Q4。
7. **D7：488.616ms原因与实际起点滞后未验。** 计算仅为(ts[st]−ts[st−1])×1000，证明前序采样间隔异常，没有目标线程调度或阻塞证据，不能断言采样线程被卡住或物理S误差恰为该值。出处：lead/control_20261106/D30_ENTRY_DRAFT.md:39；lead/early_trigger_feasibility_20261106/_feasibility_probe.py:244；题给D7；命令A输出Q1 meaning。
8. **D8：17.7次/秒不可称实测误触发率。** 近似64×25=1600s分母下总触发28294/1600=17.68375次/秒，误触发26590/1600=16.61875次/秒；实际总窗时长未积分。草案:73若指总触发可保留，原可行性文:146称误触发需更正。出处：lead/early_trigger_feasibility_20261106/EARLY_TRIGGER_FEASIBILITY.md:146；lead/control_20261106/D30_ENTRY_DRAFT.md:73；lead/control_20261106/D30_ENTRY_DRAFT.md:84；题给D8；命令A输出frequencyAssuming64WindowsOf25Seconds。
9. **工程与修复仍未验。** 未测实际保存负担、扰动、配额竞争后的捕获、物理S与实际C；不能把低配额样本说成有代表性或因果充分，不能混用n=1681与n=1737，不解除目标①机制挂账。出处：题给裁决q2Quota、bounds第4项、notEndorsed第4及第6项；lead/control_20261106/D30_ENTRY_DRAFT.md:127；lead/control_20261106/D30_ENTRY_DRAFT.md:128；命令A输出Q5、scope。
10. **纯离线能力边界需准确。** “全部需要真机”不应扩大为任何纯算术预算与队列情景都无法分析；本次仅确认所执行数值核证，未完成后续队列和配额模型，也未授权任何工程执行。出处：题给裁决corrections第8项；lead/control_20261106/D30_ENTRY_DRAFT.md:70；命令A输出scope。

## ：偏差自查

以下为题给核证的风险提示，不据此断言作者主观动机。

1. 作者可能希望尽快给D链了结，把“当前判据与预算尚未验证”升级成“整条路线受阻”。草案:95–96有此风险，但:125又禁止该外推，故不能说作者已正式否决全部栈采样。出处：题给第1项；lead/control_20261106/D30_ENTRY_DRAFT.md:95；lead/control_20261106/D30_ENTRY_DRAFT.md:96；lead/control_20261106/D30_ENTRY_DRAFT.md:125。
2. 作者可能把低误报默认为必要条件，忽略提前保存、事后分类的资格。可接受性应以成本和配额标准判断，不能只看百分比。出处：题给第2项；lead/d29_ruling_20261106/RULING_D29.md:20；题给D1、裁决q1Rationale。
3. 作者可能偏爱直观20–30FPS故事，把条件换算当作完整因果证据；缺少独立正常状态标签和完整帧耗时，归因仍未验。出处：题给第3项；lead/control_20261106/D30_ENTRY_DRAFT.md:54；题给D3；命令A输出FPS及Q3 k10 FPS20to30DurationBand。
4. 作者可能偏向漂亮的99.76%覆盖，略去起点代理、四条未知与保存耗时；又把同四条写成物理不可能，造成确定性表达不一致。出处：题给第4项；lead/control_20261106/D30_ENTRY_DRAFT.md:34；题给D4；命令A输出Q2 total、Q5。
5. 我方也可能因任务强调抓外推而过度保留路线。k−1更正及k25条件反例只否定绝对措辞，均不证明工程可达、扰动合格或任一档满足:177/:190/:191。出处：题给第5项；命令A输出finiteGridCounterexample engineeringVerified=false；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:177；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:190；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:191。
