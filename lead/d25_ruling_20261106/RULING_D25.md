# D-25 裁决书（限定离线路线）

日期：2026-11-06。证据来源：本任务提供的《裁决员结论》《事实核证》F1–F11、D1–D7 及《裁决书事实核对意见》。下列源文件引用均承接这些输入材料，不冒称撰写员亲读或亲跑；执行记录见第 7 节及 FACTCHECK.md。

## 0 定谳
verdict: A

裁限定版 A：保留 B2 为被否决的历史设计，另作 B2b 修正版设计，先经独立设计预审，才进入候选阶段。本次仅确定下一份设计的路线，不认定 A 成本低于 B，不认定 W11 已是正确集成基线。（出处：输入《裁决员结论》verdict、rationale；输入 F1–F6、D6；lead/control_20261106/D25_ENTRY_DRAFT.md:30、:42、:55、:59、:70。）

## 1 理由

1. 现版 B2 的预审结论为 NO，存在可定位的名字未绑定、关键调用点未给出接线 diff、字段落盘缺口，不能直接实现。这些缺口已经足以形成可审查的修订任务；问题编号或 high 数量不构成改走 B 的成本证据。（出处：输入 F1–F5、D2、D6；lead/b2_preaudit_20261106/B2_PREAUDIT.md:17、:30、:82、:90；lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md:63、:116、:163、:186、:205。）
2. 修正版必须补齐未知状态、错误出口与置信口径，不能仅补三处 diff。W11 可供参考的 error/None 出口有明确位置，但其 None/{} 折叠问题仍须处理，不能照搬或宣称语义全面正确。（出处：输入 F6、D3、D6；lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py:141、:154、:155、:181、:187、:189、:193、:205；lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md:133、:137、:138。）
3. 条目关于 B 更省事、A 近乎重写的表述没有同口径比较材料；现有证据不足以弃用整个设计基线，也不足以证明另起基线更快。选择 A 是修订路线判断，不是成本比较的实证结论。（出处：输入 D6；lead/control_20261106/D25_ENTRY_DRAFT.md:55、:59、:61、:71。）
4. B 链仍先于既有语料分析，沿用 D-24 的 A>B>D>C 顺序。B2 预审 NO 只证明当前设计不能放行，不证明应把分析路线提前，更不证明目标②已修复。A 汇总仍为 PARTIAL，继续保留其引用限定。（出处：输入 F11；lead/re_line_20261105/D24_RULING/RULING_D24.md:7、:11、:40、:44；lead/re_line_20261105/A1_ERRATA_MAP/A1_ERRATA_MAP.md:8。）

## 2 授权边界

本裁决提供限定路线；本撰写任务只写本目录内指定的两份文书，不实施设计或代码。来源会话已有安排限定离线工作的普通授权，无须重复询问同一一般权限；但执行代理仍须具体任务与明确写域，本裁决不是正式 harness 写域授权。（出处：输入《裁决员结论》bounds、sideAnswers(i)，输入 D7；lead/re_line_20261105/D24_RULING/RULING_D24.md:61、:65、:77；本任务《本项目铁律》3–5。）

立即可安排范围止于新指定写域内的 B2b 设计和独立设计预审。候选编写、候选复审、隔离副本集成须依次通过前置门禁，并由来源会话逐项指定写域。当前条目中的三处修改不是获准直接套用的补丁。（出处：输入《裁决员结论》bounds、order 1–6。）

本次不授权：

- 修改 ra2youli/**、out/re_work/**、lead/re_line_20261105/**、lead/GOAL_* 或 lead/PENDING_DECISIONS.md；当前撰写员写域仅为 lead/d25_ruling_20261106/。（出处：本任务《本项目铁律》3–4。）
- 把隔离副本离线集成扩大为正式母本应用；后续正式应用必须另有明确允许目标文件写入的任务，不得回溯扩大本次权限。（出处：输入《裁决员结论》bounds 4、order 6。）
- 启动 gamemd.exe、ra2loader、YURI.exe，执行 taskkill，读取活进程内存，编写 hook、MiniDump、SuspendThread、StackWalk 或注入探针；不运行或导入完整 harness，不恢复用户停止的 W7。（出处：本任务《本项目铁律》1–2；输入《裁决员结论》bounds 5、notEndorsed 6。）
- commit、push，或绕过门禁直接实现、集成。Python 如需执行，一律 python -I -X utf8。（出处：本任务《本项目铁律》5；输入《裁决员结论》order 3–6。）

## 3 执行顺序

1. 来源会话派设计作者，在新指定目录编写 B2b；旧 B2 保持只读并保留 NO 状态。绑定母本完整 SHA256/字节数、旧设计与 W11 候选版本。输入 F7 的母本基准为 `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636 / 399508 B`；实际开工前须重新计算，版本不同即停止按旧行号套用。旧设计输入指纹为 `deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f / 11638 B`。（出处：输入 F1、F7；lead/b2_preaudit_20261106/B2_PREAUDIT.md:3、:4、:5；输入《裁决员结论》order 1。）
2. 提交完整可应用 diff 与路径矩阵：快照在所有引用前定义；五个早退、采集异常、finally 调用前失败均明确处理；覆盖 5939 接线、正常与错误分支字段落盘、全部受影响调用点兼容性。区分未知/错误快照、确认不存在、vanished、缺 sha，禁止未知默认等于不存在。定义 F/E 分离，保持 crash 判据的集合差语义，验收不能只写“补三处”。（出处：输入 F2–F6、D5；out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:5939、:6340、:6349、:6361、:6374、:6377、:7038、:7117、:677；输入《裁决员结论》order 2。）
3. 来源会话派独立于作者的预审员审查绑定版本设计和完整 diff，再由独立复核员复查。通过门为无未关闭阻断项、无未解释语义变化、范围符合离线文件处理边界、材料与对象指纹一致。NO 或未验均退回设计，不转实现。旧 B2 的 NO、旧 E3/E4/E6 评价与历史测试均不继承为 B2b 通过。（出处：输入《裁决员结论》order 3；输入 F1、F9。）
4. 设计通过后另派候选作者，在新指定写域生成候选及必要的隔离合成测试。先重跑适用于绑定 W11 版本的既有测试，再覆盖早退、异常、未知快照、字段输出与接线；报告精确命令、输出、退出码和未覆盖项。不得导入母本触发顶层逻辑或通过测试启动游戏。历史 14 测不能替代这些工作。（出处：输入《裁决员结论》order 4；输入 F11、D6；lead/re_line_20261105/W11_EXCEPT_FRESHNESS/_w11_t3_test_out.txt:34、:35。）
5. 独立候选复审员及复核员逐项对照批准设计，核对状态矩阵、调用传参、输出字段、F/E 分离与范围限制，执行获准离线测试。阻断项全部关闭且版本一致才签候选通过，不能只按测试数量放行。（出处：输入《裁决员结论》order 5；输入 F2–F6、D6。）
6. 来源会话派具有明确隔离副本写域的人员离线集成；独立复审最终差异并复跑离线回归，保存输入/输出指纹、差异和回退材料。只签“隔离副本离线集成通过”，不签正式母本已应用或真机验收。本次不授权正式母本写入。（出处：输入《裁决员结论》order 6、bounds 4。）
7. B 链遇不可解决阻断，先记录证据并重新裁路线，不默认换 B 或提前分析。B 离线阶段收口后，依 D-24 顺序安排既有语料分析；D-13 所涉采集继续阻塞。“D-24 的 D 链”不是本条选项 D。（出处：输入《裁决员结论》order 7；lead/re_line_20261105/D24_RULING/RULING_D24.md:7、:40、:44；lead/PENDING_DECISIONS.md:23。）

## 4 附带三问

(i) 只批准限定离线路线：设计与独立预审先行，通过后由来源会话指定写域安排候选、单测、候选复审及隔离副本集成。真机完全不批，不预先承诺“另批一次就可发射”。一般离线授权无须重问，具体任务写域与本轮铁律仍优先。（出处：输入《裁决员结论》sideAnswers(i)；lead/re_line_20261105/D24_RULING/RULING_D24.md:61、:77。）

(ii) D-24 应按“已裁决，执行未全部完成”归档，保留裁决书及 A>B>D>C 顺序，关联本次修订裁决，保留 A 汇总 PARTIAL。仍挂待裁是状态同步问题，归档不等于执行完成。本代理不改只读台账，归档交有相应写域的后续任务。（出处：输入《裁决员结论》sideAnswers(ii)、F11；lead/re_line_20261105/D24_RULING/RULING_D24.md:7、:11；lead/PENDING_DECISIONS.md:66；lead/re_line_20261105/A1_ERRATA_MAP/A1_ERRATA_MAP.md:8。）

(iii) 只给建议，不代用户裁 D-13/D-14。D-13 建议维持暂停，重新明确解释慢爬成本还是 ≥1s 长停，撤去把 29 个结束态冻结窗当对局停滞的前提，不写采样代码。D-14 建议选 C，双口径并列且写清窗口集；用户裁定前继续现行规则。（出处：输入《裁决员结论》sideAnswers(iii)；lead/PENDING_DECISIONS.md:23、:43、:47、:63；lead/re_line_20261105/D24_RULING/RULING_D24.md:70、:71。）

## 5 对条目的更正

以下均为对 lead/control_20261106/D25_ENTRY_DRAFT.md 的更正意见，不在本任务中修改该文件。

1. :32–33 不得写 finally“无条件进 :7117”或“必抛 UnboundLocalError”。无赋值裸名存在 NameError 风险；仅补局部赋值但早退绕过时才可能为 UnboundLocalError。finally 中先行语句也可能失败，合成模型没有证明完整 harness 全路径。收尾异常可能遮蔽原异常主报告，合成模型仍保留原异常为 __context__。（出处：输入 F2、F3、D1；lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md:63；out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:7038、:7048、:7117。）
2. :29、:34 的 E1、N5 与字段缺口不得仅按编号计为独立根因，不得从 high 数量推出选 B。:38 正常路径字段缺失应为 N4/high；N6 是 diff 示意不可套用/改动面账不符，medium。（出处：输入 F2–F5、D2；lead/b2_preaudit_20261106/B2_PREAUDIT.md:30、:82、:90。）
3. :36–37 应写“展示的 diff 未完成关键调用点传参，存在默认快照静默降级风险”；全部趟实际均降级未通过完整集成验证。（出处：输入 F4；lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md:116、:188；out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:5939。）
4. :42–47 的“删掉”限于 B2 设计未保留候选语义，母本未应用。{} 与 exists=False 折叠成立，high 只限跑后有件；跑后无件是 absent_both/n/a。vanished 的置信字段与 is_new=None 不能直接互换。（出处：输入 F6、D3；lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md:137、:138；lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py:189、:202。）
5. :47 应写“未知状态折叠和置信口径存在误读风险”，不能断言已用新鲜性判 crash 或已违反母本 :677。当前未发现实际消费 F 判 crash 的执行证据。（出处：输入 D5；out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:672、:677、:679、:689、:700；lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md:160、:161、:205；lead/b2_preaudit_20261106/B2_PREAUDIT.md:111。）
6. :48 应为“4 处错引加 1 处轻微不精确”，不是 6 处。22 处是复核员限定目录统计的自报结果，本轮核证未确认全仓恰为 22；只能确认“全仓唯一”不成立。（出处：输入 D4；lead/b2_preaudit_20261106/review/B2_PREAUDIT_REVIEW.md:18、:85、:110、:112、:116、:121、:128、:132、:166。）
7. :55、:59、:61、:71 删除“重写一半”“改动面更小”“零风险推进目标①”“重写量可能超过重做”等确定措辞；无同口径成本/收益比较，离线分析不等于真实卡顿修复。:57、:59 的 W11 显式出口不等于基线正确，历史 14 测未证明本轮重跑、接线或完整集成。（出处：输入 D6、F11；lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py:154、:181、:187、:193；lead/re_line_20261105/W11_EXCEPT_FRESHNESS/_w11_t3_test_out.txt:34、:35。）
8. :27–28 可转述复核回件 checkedEveryRow=true、overreachFound=false 和核证方门禁通过；不能推为所有技术事实已由门禁验证，NO 分支不检查全部复核内容。（出处：输入 F9；lead/b2_preaudit_20261106/review/B2_PREAUDIT_REVIEW.md:9、:10、:11、:158；lead/b2_preaudit_20261106/check_b2_preaudit.py:194。）
9. :65 应分清一般离线授权、具体写域、设计/候选门禁与真机限制；B2 被否不使一般授权失效。:5 的 D-25 无冲突仅绑定核证方读取的本地版本。（出处：输入 D7、F8；lead/re_line_20261105/D24_RULING/RULING_D24.md:61、:65、:77；lead/PENDING_DECISIONS.md:20、:22、:47、:66、:125。）

## 6 未背书

- 不背书现版 B2 可实现、“修三处即完整”或 B2b 已通过；当前材料支持现版 NO，不提供新版通过证据。（出处：输入 F1–F6。）
- 不背书 W11 全面正确、A/B 谁成本更低或另起基线必然更快。（出处：输入 D6。）
- 不把历史 14 测、核证方脚本或门禁计为本撰写员执行通过。（出处：输入 F9–F11；第 7 节执行账。）
- 不背书正式母本已应用、目标②主崩溃修复、目标①卡顿改善或目标③完成新一轮安全验收；本条只处理离线文件新鲜性设计交付路线。（出处：输入《裁决员结论》notEndorsed 4；输入 F1–F6、D6。）
- 不背书由 freshness/sha 变化推出 crash，或把未知写为确定新出现。（出处：输入 D5、D6；out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:677。）
- 不背书扩大当前写域、改只读台账、启游戏、采样、读活进程、恢复 W7、commit 或 push。（出处：本任务《本项目铁律》；输入《裁决员结论》notEndorsed 6。）
- 不背书 D-24 归档即执行完毕，也不把 D-13/D-14 建议写成用户定谳。（出处：输入《裁决员结论》sideAnswers(ii)–(iii)、notEndorsed 7。）

## 7 诚实账

裁决员自报只读取条目、D-24 裁决书与待裁段，未运行 Python、测试或门禁；F1–F11、D1–D7 的实跑结果来自本任务提供的独立核证材料。本撰写员未重新读取上述源文件、未运行 Python、未重跑核证脚本、预审门禁、W11 测试套件或完整 harness；本文件中的技术结论按输入证据转述，不能作为本撰写员复跑证明。（出处：输入《裁决员结论》rationale、notEndorsed 3；本轮工具记录。）

本撰写员实际执行目录定位命令 `pwd; rg --files lead/d25_ruling_20261106`，输出工作目录 `/d/Project/ra2-campaign-forge`，当时目录列出 `_d25_facts_out.txt`、`_d25_facts.py`。这只是定位，不是核证通过。其后仅用文件写入工具生成指定的 RULING_D25.md 与 FACTCHECK.md；未修改其他文件。（出处：本轮 Bash 与 Write 工具记录。）

输入《裁决书事实核对意见》为 approved=true，blockers=[]、missing=[]、unverifiable=[]，未提出需登记的事实错误；这是一份输入核对意见，不是本撰写员执行检查所得。仍保留 D1–D7 的限缩和第 6 节未背书事项。事实核证中的 selfBias 全部记入 FACTCHECK.md，动机未经验证，不当成事实。（出处：输入《裁决书事实核对意见》及《事实核证》selfBias。）
