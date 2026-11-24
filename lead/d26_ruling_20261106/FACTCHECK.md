# D-26 事实核证记录

本记录依据本次任务提供的《事实核证》《裁决员结论》《裁决书事实核对意见》，并在本阶段亲读lead/d26_ruling_20261106/_d26_facts_out.txt。以下“确认”区分文献存在与统计正确性；引用来源文献的行号承接题给核证，不冒称本阶段逐件亲读。记录供RULING_D26.md追溯，不新增执行授权。（出处：本次任务上述三个输入；本阶段Read工具记录。）

## 确认

- **F1：当前待裁主条目为D-13、D-14，全文最大编号D-25。** 当前段正文引用D-15不构成第三个主条目。前序输出为`item_headers=[13, 14]; full_document_max_D=25`，本阶段确认既有记录，未重新扫描源文。（出处：题给事实核证F1；lead/PENDING_DECISIONS.md:20；lead/PENDING_DECISIONS.md:22；lead/PENDING_DECISIONS.md:47；lead/PENDING_DECISIONS.md:66；本次亲读lead/d26_ruling_20261106/_d26_facts_out.txt:16。）

- **F2：按前项目录展开的方案路径不存在，实际方案位于lead/codex_round_20261030/LEADER_battle/E3_SAMPLING_PLAN_REVIEWABLE.md。** 前序输出`wrong_path_exists=False; real_path_is_file=True`，记录6268字节，sha256=97599cfd06bacfd2330c40c0863228f1231984a568122fd0a1ed6cf6a7cd51a1。本阶段未重新计算指纹；计算方法据前序记录为二进制读取、hashlib.sha256与len，未用sha256sum或wc。原条目只给basename，完整错路径是展开推断，详见D2。（出处：题给事实核证F2；lead/PENDING_DECISIONS.md:44；lead/PENDING_DECISIONS.md:45；lead/d26_ruling_20261106/_d26_facts_out.txt:3；lead/d26_ruling_20261106/_d26_facts_out.txt:8；lead/d26_ruling_20261106/_d26_facts_out.txt:18；lead/d26_ruling_20261106/_d26_facts_out.txt:22。）

- **F3：文献确有“N=1.0s（K=400）误触率实测0”“N=1.0s站得住”“87.7%是0.1–0.2s短停”的表述。** 历史记载包括Δf==1样本28212、Δf>1三例最大410ms和K=400零误触。确认的是文献记载，本阶段没有重算原始采窗；不能称本阶段复现实测，也不能推广为真实对局通用保证。（出处：题给事实核证F3；lead/PENDING_DECISIONS.md:30；lead/PENDING_DECISIONS.md:31；lead/PENDING_DECISIONS.md:32；lead/GOAL_THREE_TARGETS_20261018.md:3297；lead/GOAL_THREE_TARGETS_20261018.md:3307；lead/GOAL_THREE_TARGETS_20261018.md:3309；lead/d26_ruling_20261106/_d26_facts_out.txt:23；lead/d26_ruling_20261106/_d26_facts_out.txt:34。）

- **F4：两窗口定义和四个总体相关系数有明确出处。** 64 moving只取窗内有推进，ρ(uptime,B%)=+0.0395、ρ(window,B%)=−0.0403；97全量含全窗冻结，分别+0.3461、+0.3474。两套条件不同，不互相替代；本阶段未原始复算。（出处：题给事实核证F4；lead/PENDING_DECISIONS.md:49；lead/PENDING_DECISIONS.md:50；lead/PENDING_DECISIONS.md:51；lead/PENDING_DECISIONS.md:52；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:49；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:50；lead/d26_ruling_20261106/_d26_facts_out.txt:36；lead/d26_ruling_20261106/_d26_facts_out.txt:44。）

- **F5：§534确实刊载“可算8个BOOT，负4/正2，中位+0.4472”。** 这里只确认引文存在；其统计正确性被前序表内复算否定，见D1，不能以引文匹配PASS替代统计正确性。（出处：题给事实核证F5；lead/GOAL_THREE_TARGETS_20261018.md:3505；lead/PENDING_DECISIONS.md:55；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:71；lead/d26_ruling_20261106/_d26_facts_out.txt:69；lead/d26_ruling_20261106/_d26_facts_out.txt:72。）

- **F6：D-24建议D-13保留执行暂停、D-14选C，并明确采样方案与采集继续暂停。** 它明说仅提建议、不宣称已裁或删除，不能据此虚构先前最终裁决。（出处：题给事实核证F6；lead/re_line_20261105/D24_RULING/RULING_D24.md:68；lead/re_line_20261105/D24_RULING/RULING_D24.md:70；lead/re_line_20261105/D24_RULING/RULING_D24.md:71；lead/re_line_20261105/D24_RULING/RULING_D24.md:78；lead/d26_ruling_20261106/_d26_facts_out.txt:91；lead/d26_ruling_20261106/_d26_facts_out.txt:96。）

- **F7：D-25同样只建议暂停/C，不代用户裁定。** 它还要求撤去将29个结束态冻结窗当对局停滞的前提。（出处：题给事实核证F7；lead/d25_ruling_20261106/RULING_D25.md:40；lead/d25_ruling_20261106/RULING_D25.md:46；lead/d26_ruling_20261106/_d26_facts_out.txt:97；lead/d26_ruling_20261106/_d26_facts_out.txt:98。）

- **F8：来源建议为A/A，与D-24、D-25同向的暂停/C建议不同。** 这是来源建议之间的分歧，不是D-24和D-25相互冲突。两份建议也不能当成两次独立原始数据复核。（出处：题给事实核证F8及selfBias第2项；lead/PENDING_DECISIONS.md:40；lead/PENDING_DECISIONS.md:60；lead/GOAL_THREE_TARGETS_20261018.md:3585；lead/GOAL_THREE_TARGETS_20261018.md:3594；lead/d25_ruling_20261106/RULING_D25.md:46；lead/d26_ruling_20261106/_d26_facts_out.txt:99；lead/d26_ruling_20261106/_d26_facts_out.txt:111。）

- **F9：前序核证有实际命令和输出，文献检查8/8，保留BOOT统计争议。** 题给前序精确命令为`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/d26_ruling_20261106/_d26_facts.py > D:/Project/ra2-campaign-forge/lead/d26_ruling_20261106/_d26_facts_out.txt`，题给记录称成功退出；本阶段亲读输出为`RESULT documentary_checks=8/8; arithmetic_dispute=BOOT summary; no protected files written by this script.`。本阶段未重跑该命令，不签本阶段8/8；该输出也不证明原始数据、机制、项目门禁或修复效果通过。（出处：题给事实核证F9；lead/d26_ruling_20261106/_d26_facts_out.txt:2；lead/d26_ruling_20261106/_d26_facts_out.txt:112；lead/d26_ruling_20261106/_d26_facts_out.txt:113。）

## 存疑、否定及未验

- **D1：否定“可算8个BOOT、中位+0.4472”的统计正确性。** 表列8行，其中uptime相关有限值为−0.2176、+0.6547、−0.4685、−0.5000、+0.4472、−0.8061，另两行nan。前序输出`table_rows=8; finite=6; nan=2; negative=4; positive=2`；排序后`[-0.8061, -0.5, -0.4685, -0.2176, 0.4472, 0.6547]`，公布值中位数−0.34305。原脚本把nan append到within，len包括nan，排序后仅取中间索引，未对偶数有限样本取中央两项均值。此修正只依公布四位小数表值，原始精度、BOOT分组和97原始窗均未验；本阶段未执行或修改原脚本，也未重新算表内中位数。（出处：题给事实核证D1；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:62；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:69；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:123；lead/goal3t_nightwatch_20261102/_phase_recompute.py:189；lead/goal3t_nightwatch_20261102/_phase_recompute.py:195；lead/goal3t_nightwatch_20261102/_phase_recompute.py:197；本次亲读lead/d26_ruling_20261106/_d26_facts_out.txt:70；lead/d26_ruling_20261106/_d26_facts_out.txt:71；lead/d26_ruling_20261106/_d26_facts_out.txt:90。）

- **D2：完整错路径不是D-13原文逐字引文。** 第44行给E3主卡全路径，第45行对另两项只给basename；按前项目录展开的方案路径不存在。完整错路径字面出现在草案中，应追加勘误并与原条目双向关联，不能覆写只读原文。本阶段仅在两份指定文书记录，台账关联仍待有写域任务办理。（出处：题给事实核证D2；本次《裁决员结论》pathErratum；lead/PENDING_DECISIONS.md:44；lead/PENDING_DECISIONS.md:45；lead/control_20261106/D26_ENTRY_DRAFT.md:46；lead/control_20261106/D26_ENTRY_DRAFT.md:47；lead/d26_ruling_20261106/_d26_facts_out.txt:18；lead/d26_ruling_20261106/_d26_facts_out.txt:22。）

- **D3：“两套系数都反号”不成立。** 只有ρ(window,B%)从−0.0403到+0.3474反号，uptime的+0.0395、+0.3461均正。因此只能限定变量描述，不能笼统说两个窗口集符号相反。（出处：题给事实核证D3；lead/PENDING_DECISIONS.md:48；lead/PENDING_DECISIONS.md:50；lead/PENDING_DECISIONS.md:52；lead/control_20261106/D26_ENTRY_DRAFT.md:57；lead/d26_ruling_20261106/_d26_facts_out.txt:45。）

- **D4：4负/2正不足以证明“无一致相位效应”或强化“相位不驱动”。** 可确认的是六个有限uptime相关方向不一致，不能概括window列或作因果排除。原文自述未经异族核验、样本小且检验力弱、不做因果推断；本阶段未做显著性、功效或因果分析，且配套中位数有误。（出处：题给事实核证D4；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:73；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:76；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:119；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:121；lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:125；lead/control_20261106/D26_ENTRY_DRAFT.md:64；lead/control_20261106/D26_ENTRY_DRAFT.md:65。）

- **其他未验范围。** 真实对局事件语义及剩余长停代表性、历史阈值复现、触发延迟、采样扰动、短停命中率、安全性、dump解析、97原始窗及原始精度中位数、项目门禁、真实修复效果均未在本阶段验证。≤50ms是护栏而非实测保证，栈位置不是机制定位；不以文献核证补足这些缺口。（出处：本次《裁决员结论》d13Rationale及notEndorsed；lead/goal3t_nightwatch_20261102/E3_FOR_GOAL1_CARD_20261103.md:125；lead/goal3t_nightwatch_20261102/E3_FOR_GOAL1_CARD_20261103.md:150；lead/codex_round_20261030/LEADER_battle/E3_SAMPLING_PLAN_REVIEWABLE.md:25；lead/d26_ruling_20261106/_d26_facts_out.txt:112。）

## selfBias

以下保留题给核证中的五项偏向风险，均是可观察的框架问题，不推断作者主观动机，也不直接否定裁C的技术理由。

1. **合并办理可能服务于减少待裁项和流程负担。** 草案自称两项互不依赖，却以同卡目标①、已挂两天为合并理由，另又要求分开裁；这提示行政便利倾向，不能证明技术合并必要性或执行依赖。（出处：题给事实核证selfBias第1项；lead/control_20261106/D26_ENTRY_DRAFT.md:3；lead/control_20261106/D26_ENTRY_DRAFT.md:4；lead/control_20261106/D26_ENTRY_DRAFT.md:77。）
2. **重复引用可能被当成独立补强。** 草案借§534增强论据，但汇总统计有误；D-25又引用D-24，两份同向建议不能计作两次独立统计复核。（出处：题给事实核证selfBias第2项、D1；lead/control_20261106/D26_ENTRY_DRAFT.md:64；lead/control_20261106/D26_ENTRY_DRAFT.md:65；lead/d25_ruling_20261106/RULING_D25.md:46；lead/d26_ruling_20261106/_d26_facts_out.txt:72。）
3. **为推进定谳可能把建议分歧写得更强。** 张力在来源A/A与建议暂停/C之间；D-24、D-25都仅建议且彼此一致，不存在两份相反最终裁决。（出处：题给事实核证selfBias第3项；lead/control_20261106/D26_ENTRY_DRAFT.md:13；lead/control_20261106/D26_ENTRY_DRAFT.md:21；lead/re_line_20261105/D24_RULING/RULING_D24.md:68；lead/d25_ruling_20261106/RULING_D25.md:46。）
4. **提问框架可能偏向维持暂停/C。** 草案要求改判A/B给推翻C的理由，对维持C没有对称举证要求；这是框架不对称，不等于C本身错误。（出处：题给事实核证selfBias第4项；lead/control_20261106/D26_ENTRY_DRAFT.md:100；lead/control_20261106/D26_ENTRY_DRAFT.md:101。）
5. **归档可能与技术解挂混同。** 草案询问定谳后能否解除机制挂账，但文献和表内算术并未证明短停解释力或真实卡顿改善，清单减少不能充当修复证据。（出处：题给事实核证selfBias第5项；lead/control_20261106/D26_ENTRY_DRAFT.md:89；lead/goal3t_nightwatch_20261102/E3_FOR_GOAL1_CARD_20261103.md:129；lead/d26_ruling_20261106/_d26_facts_out.txt:112。）

## 核对意见、操作范围与检查状态

题给《裁决书事实核对意见》为`approved=true; blockers=[]; missing=[]; unverifiable=[]`，没有列出阻断项。此项只记录输入，不称为本阶段运行的门禁结果，也不解除当前限制。（出处：本次任务《裁决书事实核对意见》；本次铁律第1–4条。）

本阶段实际先执行`pwd; rg --files lead/d26_ruling_20261106`，输出工作目录`/d/Project/ra2-campaign-forge`及既有`_d26_facts.py`、`_d26_facts_out.txt`；随后使用Read读取既有输出，使用Write生成两份指定文书。这些操作只说明文书生成及既有记录可读，不是原始实验检查。本阶段没有修改来源文献、原统计脚本、门禁或台账，没有commit、push、真机、活进程读取及采样操作。（出处：本阶段工具记录；本次写域限制。）

本阶段未运行前序核证脚本、历史实验脚本或项目门禁，未进行97原始窗复算；不能据F9的前序成功把这些检查登记为本阶段通过。本次文件交付的格式检查如有执行，以任务最终返回的精确命令及输出为准，不将其扩大为项目检查。（出处：本阶段工具记录；题给事实核证F9；lead/d26_ruling_20261106/_d26_facts_out.txt:2；lead/d26_ruling_20261106/_d26_facts_out.txt:113。）
