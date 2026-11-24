# D-28 事实核证登记

本表逐条转录并整理题给「事实核证」的确认、存疑及 。出处中的文件行号和执行结果来自该输入；撰写阶段没有重新读取这些源文件或执行核证、门禁、测试、探针。故下列“确认”表示独立核证输入已确认，不表示本撰写阶段亲跑通过。题给「裁决书事实核对意见」为 approved=true，blockers=[]、missing=[]、unverifiable=[]，亦不替代本阶段复验。

## 确认项

### F1 当前完整指纹一致（关键）

候选 420292 B / SHA256 `9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc`；母本 399508 B / SHA256 `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636`。仅证明核证时当前母本与基准一致，不证明历史所有时刻未变。

出处：题给 F1，独立核证执行 `python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/d28_ruling_20261106/_d28_facts.py`，exit=0；输出 candidate.bytes=420292、mother.bytes=399508，两个 matchesExpected=true，完整 SHA256 如上；输出件 lead/d28_ruling_20261106/_d28_facts_out.txt。本阶段未运行该命令。

### F2 H6 显式传参存在（关键）

H6 旧三参数原文调用出现 0 次，唯一实际调用显式传入 pre_freshness_snapshot=pre_freshness_snapshot。

出处：lead/b2b_candidate_20261106/qc151_trip.candidate.py:6167、lead/b2b_candidate_20261106/qc151_trip.candidate.py:6168；题给 F2，同 F1 精确命令的输出 H6_old_literal_count=0；H6_AST_calls 唯一项 line=6167、endLine=6168、keywords={pre_freshness_snapshot: pre_freshness_snapshot}。本阶段未重验。

### F3 H7 初始化先于指定早退（关键）

带类型标注初始化位于外层 try 前；指定五早退位于初始化后且处于该 try 内。

出处：lead/b2b_candidate_20261106/qc151_trip.candidate.py:6528 初始化，:6545 try，:6572 EXIT_CARRIER_NOT_OWNED、:6581 EXIT_TARGET_MISSING、:6593 EXIT_TARGET_MISMATCH、:6606 EXIT_PRECHECK_SHA_MISMATCH、:6609 EXIT_PRECHECK_SIG_MISMATCH；题给 F3，同 F1 命令 AST 输出 allAfterInit=true。本阶段未重验，不外推全部状态语义通过。

### F4 五字段文本为 true（关键）

motherUnchanged、nineHunksPresent、noImportMother、threeStatesDistinct、testsActuallyRun 指定文本均为 true。testsActuallyRun 是报告声明，不能仅凭字段证明历史执行。

出处：lead/b2b_candidate_20261106/review/CANDIDATE_REVIEW.md:22、:23、:24、:25、:26；题给 F4，同 F1 命令逐字段精确匹配各 1 项。该报告 :158、:198、:202、:203 另载历史命令和 Ran 29 tests / PASS=29 FAIL=0 / EXIT=0。本阶段未运行 29 项测试。

### F5 独立核证机械门禁通过（关键）

题给核证阶段候选只读门禁 9/9、D-13b 只读门禁 8/8 通过；不能扩写为本撰写阶段通过或旧测试已重跑。

出处：题给 F5，独立核证执行：

- `python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/b2b_candidate_20261106/check_candidate.py`，exit=0，输出 `ALL 9 GATES PASSED! EXIT=0`。
- `python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/d13b_design_20261106/check_d13b.py`，exit=0，输出 `[RESULT] PASS — 全部 8 项检查通过（exit 0）`。

候选门禁 lead/b2b_candidate_20261106/check_candidate.py:195 读旧测试输出、:228 检查字段文本、:247 定位锚点；lead/d13b_design_20261106/check_d13b.py:202 读旧输出。题给 scope 明示候选 29 项和状态机 43 项未重跑。本撰写阶段以上两门禁及两组测试均未运行。

### F6 固定预算算术一致（关键）

2.5+100.0+48.0+2.0=152.5ms，与 totalMs 差 0.0ms；152.5<129.93 为 false，与 meetsMedian=false 一致，差额 22.57ms。

出处：lead/d13b_design_20261106/BUDGET_MODEL.json:6、:13、:20、:27、:32、:33；题给 F6，同 F1 命令 Decimal 输出 sumMs=152.5、differenceMs=0.0、computedTotalLessThan129_93=false、flagConsistent=true、excessMs=22.57。本阶段未重算。

### F7 定义确有累计判定拒止规则（关键）

第 191 行原文：“**拒止原则**：任何累积判定耗时 ≥100 ms 的触发机制均属不合格。”后文说明延迟可能采到下一帧正常代码并产生因果倒错。该条属于设计规则，不是所有采样方案物理不可能的定律。

出处：lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:191；:184 标为“四项设计要求”，:190 为设计指标；题给 F7。本阶段未重读。

### F8 D-12 明确口径 B（关键）

裁决写明“口径 B 为准”，口径 A 仅在引用 §507 历史数字时注明来源、不回溯重算；所读裁决段未明文要求所有在线触发等到分类门槛。

出处：lead/PENDING_DECISIONS.md:257、:260、:261、:262；题给 F8。该段原标签“②停滞口径 = A”与正文“口径 B 为准”并存，本裁决遵守题给已确定的正文裁决，不擅改原记录。

### F9 实际提取阈值及位置（关键）

T_DEFAULT=0.100 秒；同帧平台首末样本差 dur 达到 thr 才记录平台。核证脚本只读取该探针，未执行它。

出处：lead/stall_event_def_20261106/_stall_probe.py:28、:86、:93、:95、:96、:105；题给 F9，同 F1 命令输出对应行。本阶段也未运行探针。

### F10 核证脚本及输出位置（非关键）

题给核证脚本、输出均位于唯一写域，核证输入报告只做静态解析、只读门禁及输出写入，没有真机、活内存、采样实现、门禁修改或 commit/push。

出处：题给 F10；脚本 lead/d28_ruling_20261106/_d28_facts.py，输出 lead/d28_ruling_20261106/_d28_facts_out.txt；同 F1 精确命令 exit=0，输出 isolated=true、FACT_SCRIPT_COMPLETED。这是核证方执行说明，本阶段没有独立审查该脚本内容。

## 存疑、限缩与更正

### D1 探针路径和行号有误（非关键）

给定 lead/d13b_design_20261106/_stall_probe.py 不存在；实际 if dur >= thr 在 lead/stall_event_def_20261106/_stall_probe.py:96，:100 为 pos = "FIRST"。

出处：题给 D1，核证 Read 返回 File does not exist，同 F1 命令输出 requested_probe_path.exists=false；lead/control_20261106/D28_ENTRY_DRAFT.md:63 引 :100。本阶段未重新查询该缺失路径。

### D2 预算不足不能推出物理不可行（关键）

152.5>129.93 只否决固定四段数值、串行相加、满 100ms 才触发、要求在代表性事件结束前快照这些共同假设，不证明全部实现的下界。

出处：lead/control_20261106/D28_ENTRY_DRAFT.md:46、:78、:115；lead/d13b_design_20261106/BUDGET_MODEL.json:5、:19、:26、:34；题给 D2。裁决采用固定模型不足的限缩结论。

### D3 122.5ms 仅是条件算术反例（关键）

保持事件 100ms 分类，改变未验调度/捕获预算，2.5+100+20=122.5ms，算术余量 7.43ms。48ms 不是实测最低耗时，≤2ms 指标也不能推出实际耗时 ≥2ms。反例不消除第 191 行冲突，不证明实现可行。

出处：lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:190、:191；lead/d13b_design_20261106/BUDGET_MODEL.json:19、:26、:34；题给 D3，同 F1 命令输出算术反例。本阶段未算。

### D4 分类与在线触发可分开讨论（关键）

提前/周期性记录，事后仍按 d≥100ms 筛事件，不在逻辑上自动改口径 B 或使历史统计全部失效；这是待独立审查的可能性，不是选定或授权实现。

出处：lead/PENDING_DECISIONS.md:260；lead/stall_event_def_20261106/_stall_probe.py:86、:95、:96；lead/control_20261106/D28_ENTRY_DRAFT.md:72、:75、:76；题给 D4。

### D5 改截止目标须另验（关键）

若不要求在结束前取得原始上下文，152.5ms 与中位数关系就不是该新目标的否决条件；结束后取得当前栈仍不能直接视为停滞栈。

出处：lead/control_20261106/D28_ENTRY_DRAFT.md:76、:77；lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:191；题给 D5。本次未更换目标。

### D6 事后解析不等于事后才取现场（关键）

停滞期间已存的上下文可离线解析；没有预存时，不能凭结束后当前栈恢复冻结瞬间。现有文书分开在线原始寄存器/微型内存页保存与退出后符号反解/栈回溯，但未证明实现可用。

出处：lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:200；lead/control_20261106/D28_ENTRY_DRAFT.md:76、:77；题给 D6。

### D7 中位数不是逐事件上界（关键）

129.93ms 是 1681 个保留标签事件的中位数；最长 566.96ms，200≤d<500ms 有 158 个、500≤d<1000ms 有 3 个。预算超中位数不推出零覆盖；长事件覆盖率、偏差、机制代表性仍未验。

出处：lead/d27_ruling_20261106/RULING_D27.md:12；题给 D7。上述为历史统计输入，本阶段未重算，也不将保留标签当作真实对局真值。

### D8 规范冲突及两个 50ms 起算点（关键）

等待满 100ms 再触发与累计判定 ≥100ms 拒止规则冲突，但不能推到所有触发方式。发生后 50ms 与检测后 <50ms 是不同起点；若坚持前者，满 100ms 才捕获在更早条件上失败。

出处：lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md:177、:190、:191；lead/control_20261106/D28_ENTRY_DRAFT.md:65；题给 D8。下一阶段须显式澄清，不静默删规则。

### D9 差额严格不等式（非关键）

满足 totalMs<129.93 要削减严格超过 22.57ms；恰好 22.57ms 只到相等。当前其余三段 52.5ms，允许值严格 <29.93ms。

出处：lead/control_20261106/D28_ENTRY_DRAFT.md:66；题给 F6/D9 的 Decimal 输出。本阶段未重算。

### D10 “全绿”只限机械状态（关键）

机械门禁与报告字段不等于候选语义、真实运行、母本应用条件闭合。独立候选复审及隔离集成仍未通过；29 项、43 项在核证阶段和本撰写阶段均未重跑。

出处：lead/b2b_candidate_20261106/check_candidate.py:195、:228、:247；lead/b2b_candidate_20261106/review/CANDIDATE_REVIEW.md:216；lead/control_20261106/D28_ENTRY_DRAFT.md:34、:117；题给 F5/D10。

## 历史数字与附加措辞更正

1737 为 full97 全部候选平台；1681 为 isRealMatch=true 保留标签，另有 56 false；90.42% 是其中 1520/1681 落在 100≤d<200ms 的条件比例，不是 1681/1737，也不保证真实对局分布。保留原版本，不回溯重算。若未来获批改筛选规则，应另版独立计算，不覆盖旧结果；若只改捕获而分类不变，旧数字只能作为原版本条件统计，不能直接作新捕获覆盖率。出处：lead/d27_ruling_20261106/RULING_D27.md:12、:48；lead/PENDING_DECISIONS.md:260、:261、:262；题给 historyDisposal、corrections。

草案 :32 “生成前/后均”应限缩为当前指纹一致；:44 应拆开门禁 8/8 和历史 43 项测试；:75 “全部失效”应改为保留原版、获批变更则另版计算。其他措辞更正分别见 F4/F5、D1—D10。出处：lead/control_20261106/D28_ENTRY_DRAFT.md:32、:44、:75；题给 corrections。

## 

以下逐项保留题给 ，均是可能偏差，不是作者动机定论：

1. 条目作者可能急于推进 B：“候选已全绿”“全 true”可能混同字段声明、机械门禁与完整候选复审；但草案同时保留未通过阶段，不能断言有意隐瞒。出处：lead/control_20261106/D28_ENTRY_DRAFT.md:12、:26、:34、:117；题给  第 1 项。
2. 条目作者可能想给 D 一个了结：“物理上做不到”比固定预算不足更强，选项可能诱导先改口径或收口；但稿内也反对全面否定，反映结论强度不一致。出处：lead/control_20261106/D28_ENTRY_DRAFT.md:78、:95、:96、:97、:68、:115；题给  第 2 项。
3. 总控可能受“B 全绿、D 超预算”的对称叙事影响；文本门禁与未实测预算的证据强度不同，须分别限定。出处：题给  第 3 项、F4/F5、D2/D10。
4. 核证方也可能偏向可行反例而低估实施困难；122.5ms 仅是假设算术反例，不能背书在线调度、扰动、资源释放或栈可解析性。零真机、零采样代码继续保持。出处：题给  第 4 项、D3；lead/d13b_design_20261106/BUDGET_MODEL.json:34。

## 本撰写阶段执行账

唯一执行的 shell 命令为 `pwd; rg --files lead/d28_ruling_20261106`，exit=0；输出工作目录 `/d/Project/ra2-campaign-forge`，列出 `_d28_facts_out.txt` 与 `_d28_facts.py`。该命令只定位目录，不核验文件内容。随后通过文件写入工具生成指定 RULING_D28.md、FACTCHECK.md。

本阶段未运行：`_d28_facts.py`、`check_candidate.py`、`check_d13b.py`、29 项候选测试、43 项状态机测试、停滞探针、语料重算。未启动游戏、读活内存、写采样实现、修改门禁、commit 或 push。输入核证结果不计入本阶段亲跑通过；源文件内容、指纹和既有报告的独立复验在本阶段均为未验。
