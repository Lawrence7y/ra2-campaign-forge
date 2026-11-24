# D-29 时序要求与口径 B 裁决

## 0 定谳
q1: 丁

保留发生后 50ms 捕获、检测后严格 <50ms 与安全裕量 ≤20ms、:191 拒止原则及口径 B；否决“等满 100ms 才触发、随后才捕获”的串行机制。允许在既定边界内继续离线论证提前保存与事后分类的独立方案，工程可达性未验，D-13 采样实现与执行继续 PAUSE。依据：题给裁决 q1、bounds；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:177、lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:190、lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:191；lead/d28_ruling_20261106/RULING_D28.md:28、lead/d28_ruling_20261106/RULING_D28.md:36。

## 1 冲突是否成立

:177 与 100ms 门槛不构成无条件的数学互斥；互斥依赖“在线必须等满 100ms 才触发，捕获不早于触发”的串行。设物理停滞起点 S、触发时刻 T、原始上下文实际保存时刻 C，若 T−S≥100ms 且 C≥T，则 C−S≥100ms>50ms，必然违反 :177，同时属于 :191 拒止的累积判定机制。依据：lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:177、lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:191；lead/d28_ruling_20261106/RULING_D28.md:30；题给 F10。

口径 B 的 100ms 是事件持续时间 d 的分类门槛。代码计算 dur=ts[j]−ts[i]，再判断 dur≥thr；这不能直接推出所有在线捕获必须等待 100ms。:177 从停滞发生起算，:190 从检测到起算，两条约束不能互相代替。依据：lead/stall_event_def_20261106/_stall_probe.py:28、lead/stall_event_def_20261106/_stall_probe.py:95、lead/stall_event_def_20261106/_stall_probe.py:96；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:177、lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:190。

本撰写阶段实跑 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/d29_ruling_20261106/_d29_facts.py`，退出码 0。纯逻辑赋值 S=0、T=30、C=40、分类时刻=120、d=120ms，使发生后≤50、检测后<50、安全裕量≤20、触发累计判定<100、最终 d≥100、分类不早于事件结束六项均为 true。这只反驳无条件数学互斥，没有证明工程实现、真实覆盖或起点可观测性。依据：该命令输出 pureLogicalCounterexampleMs；lead/d29_ruling_20261106/_d29_facts_out.txt:179；lead/d13b_timing_clarify_20261106/TIMING_SPEC_CLARIFY.md:54、lead/d13b_timing_clarify_20261106/TIMING_SPEC_CLARIFY.md:55。

## 2 处置选择

选择丁：不选甲降级需求，不选乙更改用户分类口径，也不选丙以无条件互斥关闭整条 D 链。保留原规范，限定否决串行机制，提前或周期性保存另按独立方案审查。依据：题给裁决 q1；lead/PENDING_DECISIONS.md:260；lead/d28_ruling_20261106/RULING_D28.md:30、lead/d28_ruling_20261106/RULING_D28.md:36。

提前候选与最终事件分类可以分开。在最终仍按原版 d≥100ms、原窗口与标签规则分类，候选不冒充已确认事件，且未捕获事件不被静默剔除而改变统计母体的下，提前保存与 D-12 不冲突。若最终阈值降为 30ms，或按捕获成功与否改写原集合，就不能宣称沿用不变的口径 B；修改只能建议，须用户另行裁定。依据：题给裁决 q2ConflictWithD12；lead/PENDING_DECISIONS.md:260；lead/stall_event_def_20261106/_stall_probe.py:96；lead/d28_ruling_20261106/RULING_D28.md:42。

历史数字：本次不改事件定义、门槛、窗口或标签，不重算或覆盖旧统计。1737 是 full97 候选平台数；1681 是其中 isRealMatch=true 的保留标签数，另 56 为 false；90.42% 是保留标签集合内 1520/1681 落在 100≤d<200ms 的比例，不是 1681/1737；129.93ms 是该集合中位数，不是各事件上界。四者保留原版本和来源限定，不能作为新方案覆盖率或独立确认的真实对局分布。未来用户明示修改分类规则时须另立版本独立统计，旧值继续留档。依据：lead/d28_ruling_20261106/RULING_D28.md:32、lead/d28_ruling_20261106/RULING_D28.md:40、lead/d28_ruling_20261106/RULING_D28.md:42；题给裁决 historyDisposal。历史语料本阶段未重算。

## 3 :191 的适用边界

:191 禁止累积判定耗时≥100ms的触发机制，包括等满口径 B 门槛再触发当前现场捕获；其文字没有直接禁止离线按 d≥100ms 分类，也不能推出禁止所有提前触发或周期性历史保存。这是对规范适用范围的解释，不是删除拒止原则或授权新实现。依据：lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:191；lead/d28_ruling_20261106/RULING_D28.md:30、lead/d28_ruling_20261106/RULING_D28.md:36；题给裁决 q2Bounds。

提前保存与事后筛选的逻辑相容不意味着 :177 自动满足。仍须证明正确事件、正确目标线程的原始上下文在物理起点 S 后 50ms 内实际保存，检测至生效满足 :190，并审查起点可观测性与误差、覆盖、假阳性、扰动、配额和回退。停滞结束后才取当前栈，不能替代停滞期间已保存的上下文。依据：lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:177、lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:190；lead/d28_ruling_20261106/RULING_D28.md:36；题给裁决 q2Bounds。

“并未禁止所有提前触发”不能标为 D-28 §2 原话。本阶段命令输出 claimed_D28_exact_quote_in_section2=false、claimed_D28_exact_quote_anywhere=false；该措辞见澄清文件 :141。可以据 D-28 :30、:36、:42 作范围概括，不能冒充逐字引文。依据：lead/d13b_timing_clarify_20261106/TIMING_SPEC_CLARIFY.md:141；lead/d29_ruling_20261106/_d29_facts_out.txt:62；上述实跑命令输出 checks。

## 4 情景 B 作废后的 D 链

B 作为独立的 :190 合规情景作废；A 仍保留固定参数算术用途。A/B 四段数值、段名和证据等级相同可核，作者确曾执行复制动作未验。两者检测后 48+2=50ms，均违反严格 <50ms；不能把重复预算写成新的合规情景。依据：lead/d29_ruling_20261106/_d29_facts_out.txt:65、lead/d29_ruling_20261106/_d29_facts_out.txt:89、lead/d29_ruling_20261106/_d29_facts_out.txt:110；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:190；题给 D4。

下表是本阶段上述核证命令的固定模型输出；每组 differenceMs=0.0000，16 段实测数为 0，每组证据等级依次为估算、指标、估算、指标。它们没有已验证的工程可达预算。依据：lead/d29_ruling_20261106/_d29_facts_out.txt:67、lead/d29_ruling_20261106/_d29_facts_out.txt:71；题给 F7、F8。

| 情景 | 四段合计 ms | 检测后 ms | 严格 <50 | 安全裕量 ≤20 | 发生后 ≤50 |
| --- | --- | --- | --- | --- | --- |
| A | 2.5+100+48+2=152.5 | 50 | 否 | 否 | 否 |
| B | 2.5+100+48+2=152.5 | 50 | 否 | 否 | 否 |
| C | 2.5+100+18+2=122.5 | 20 | 是 | 是 | 否 |
| D | 2.5+100+25+2=129.5 | 27 | 是 | 否 | 否 |

A 比 129.93ms 多 22.57ms，要严格低于它须削减严格超过 22.57ms。C/D 比该中位数分别低 7.43/0.43ms，只是条件算术；四组均含等待 100ms 的串行段，C/D 低于中位数也不能满足 :177 或绕开 :191。129.93ms 不能充当全事件截止或推定覆盖率。依据：lead/d28_ruling_20261106/RULING_D28.md:32、lead/d28_ruling_20261106/RULING_D28.md:34；上述命令输出 budget；题给裁决 q3BudgetConclusion。

下一步限于离线可审查的时间约束与假设矩阵，分列物理起点、触发、上下文保存、事件分类及离线解析，注明每段起止、并行/串行关系、证据等级、未知量与误差，分别验证 C−S≤50、C−T<50、安全裕量≤20、触发累计判定<100、最终 d≥100。纯数学与合成时序应覆盖短于100ms假阳性、恰好50/100ms边界、起点误差、周期相位、窗口切断和配额/回退，给出可行域与反例。优先补足物理起点可观测性和覆盖定义；实际耗时离线无法确认的继续标“未验”，不得倒推参数充作实测。提前或周期性保存须独立审查，不能称作调参，也不授权采样实现。依据：题给裁决 q3NextStep；lead/d28_ruling_20261106/RULING_D28.md:30、lead/d28_ruling_20261106/RULING_D28.md:36；本阶段命令输出 timeline 四类 verified 均 false。

## 5 授权边界

本次仅裁定目标① D 链的规范解释、纯模型逻辑与条件预算，D-13 采样实现与执行保持 PAUSE；目标①机制挂账不解除。依据：题给裁决 bounds、notEndorsed；lead/d28_ruling_20261106/RULING_D28.md:28、lead/d28_ruling_20261106/RULING_D28.md:36。

本次不授权启动 gamemd.exe / ra2loader / YURI.exe、taskkill、读取活进程内存、hook、MiniDump、SuspendThread、StackWalk、探针注入或任何采样实现，亦不授权 E3。依据：题给铁律1、2及裁决 bounds。

本次不授权修改口径 B、需求原文、门禁脚本或题列只读路径；唯一写域为 lead/d29_ruling_20261106/，它是本次明确指定的输出例外，不扩大到其他 d2* 裁决目录。不得 commit、push。Python 须隔离模式、UTF-8、绝对路径；指纹使用 hashlib。依据：题给铁律3—8及两份文件输出要求；lead/PENDING_DECISIONS.md:260。

## 6 未背书

- 不自行改口径 B，不静默删除或架空 :191。依据：lead/PENDING_DECISIONS.md:260；lead/d28_ruling_20261106/RULING_D28.md:30；题给 notEndorsed。
- 不把预算超标外推为栈采样不可行，不以某串行机制失败关闭整条路线。依据：lead/d28_ruling_20261106/RULING_D28.md:32、lead/d28_ruling_20261106/RULING_D28.md:34。
- 不背书提前或周期性保存已实现、满足50ms或具有覆盖率保障；纯逻辑赋值与合成时序均非实测。依据：lead/d29_ruling_20261106/_d29_facts_out.txt:180；lead/d28_ruling_20261106/RULING_D28.md:36。
- 不把1681和1737当同口径独立对照，不把90.42%当1681/1737，不把129.93ms当全部停滞上界或新方案覆盖保证。依据：lead/d28_ruling_20261106/RULING_D28.md:32、lead/d28_ruling_20261106/RULING_D28.md:40、lead/d28_ruling_20261106/RULING_D28.md:42。
- 不据本裁决解除目标①机制挂账或宣称真实多单位卡顿已修复。依据：题给裁决 notEndorsed；本阶段未执行任何真机、采样或机制验收。

## 7 诚实账

题给“裁决书事实核对意见”为 approved=true、blockers=[]、missing=[]、unverifiable=[]；没有输入 blocker 需要登记。这是题给核对意见，不是本撰写阶段门禁通过证明。依据：题给核对意见原字段。

本阶段先读 _d29_facts.py 全文、既有输出和 D-28 全文，再实际执行 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/d29_ruling_20261106/_d29_facts.py`，退出码0；脚本只读8份来源，AST解析、hashlib指纹、Decimal算术及纯逻辑赋值，并在允许写域更新 _d29_facts_out.txt。该命令是本阶段唯一核证脚本命令；目录定位另执行 `pwd; rg --files lead/d29_ruling_20261106`，退出码0。依据：本阶段工具执行记录；lead/d29_ruling_20261106/_d29_facts.py:24、lead/d29_ruling_20261106/_d29_facts.py:35、lead/d29_ruling_20261106/_d29_facts.py:44、lead/d29_ruling_20261106/_d29_facts.py:64、lead/d29_ruling_20261106/_d29_facts.py:79。

未运行原探针、门禁、历史语料重算或任何真机与采样实现，不记通过。来源原文部分由脚本读取并输出逐行摘录；草案措辞和历史统计的进一步核证归于题给 F/D 与裁决材料，未独立追查全部历史来源。作者复制动作、工程时延、起点可观测性及覆盖均未验。依据：本阶段工具记录；题给事实核证 D4、F14；上述命令输出 scope。

草案更正及五项 selfBias 在 FACTCHECK.md 逐条留档：事件时长不能偷换为所有触发必等时间；范围概括不能标为 D-28 原话；工程未验不能改写为无条件互斥；B作废不能抹去A的算术用途；低于中位数不能标作完整规范合规。依据：题给 corrections、selfBias；lead/d29_ruling_20261106/_d29_facts_out.txt:57、lead/d29_ruling_20261106/_d29_facts_out.txt:157、lead/d29_ruling_20261106/_d29_facts_out.txt:179。
