# D-25 事实核证记录

日期：2026-11-06。本记录逐项转录本任务提供的《事实核证》，并保留其适用范围。F 表示输入核证方确认，D 表示输入核证方提出的争议或限缩；不表示本撰写员亲跑通过。未重新读取技术源文件，未执行 Python、测试、门禁或完整 harness。源文件引用及命令输出均来自任务输入，另有标注者除外。

## 确认项

### F1 — B2 预审为 NO，绑定设计指纹

输入核证方确认：预审 verdict: NO；被审 B2 为 `deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f / 11638 B`。（输入《事实核证》F1；lead/b2_preaudit_20261106/B2_PREAUDIT.md:3、:4、:5、:17。）

输入核证方执行 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/d25_ruling_20261106/_d25_facts.py`，报告输出 `FINGERPRINT lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f 11638`。本撰写员未重跑。

### F2 — 裸名无赋值

E1 为 NOT_FIXED；B2 全文 `_pre_freshness_snapshot` 仅在 35/63/200 行出现，63 行是关键字实参的值，并非赋值。（输入 F2；lead/b2_preaudit_20261106/B2_PREAUDIT.md:30；lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md:35、:63、:200。）

输入 F1 所列核证命令报告 `SNAPSHOT_OCCURRENCES` 行号 35/63/200、`SNAPSHOT_ASSIGNMENTS []`。本撰写员未重跑；异常类型须依 D1 限缩。

### F3 — 五个早退及 finally 调用位置

main 在 6387 前自身作用域的五个 return 为 6340/6349/6361/6374/6377；对应 finally 为 7038，finalize_trip 调用为 7117。进入 finally 不保证到达调用，之前另有语句。（输入 F3；out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:6313、:6340、:6349、:6361、:6374、:6377、:6387、:7038、:7117。）

输入 F1 所列命令以 ast.parse 静态解析，报告 `MAIN_EARLY_RETURNS_BEFORE_6387 [6340, 6349, 6361, 6374, 6377]`、`MAIN_FINALIZE_CALLS [7117]`。未执行母本；本撰写员未重跑。

### F4 — 缺 5939 接线 diff

B2 全文带 @@ 的 hunk 只有四处，43/52/75/128；116、188 仅声明将修改 5939，未给该调用点实际 diff；母本该处仍只传 rec, carrier_dir, out_dir。（输入 F4；lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md:43、:52、:75、:116、:128、:188；out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:5939。）

输入 F1 所列命令报告 `B2_HUNKS` 行号 `[43, 52, 75, 128]`。本撰写员未重跑；不能据此断言所有实际趟均降级。

### F5 — 正常路径字段交付缺口

B2 全文 freshness_confidence、freshness_note、captured_at_iso 各零次；freshness_verdict 只在 205 行叙述出现。163 正常路径继续读 bytes，186 为表格承诺；母本现有 info 无这些字段。（输入 F5；lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md:163、:186、:205；out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:4583、:4584、:4585、:4586。）

输入 F1 所列命令对全文 str.count，报告上述三项 `B2_TOKEN_COUNT` 为 0、`B2_FRESHNESS_VERDICT_LINES [205]`。本撰写员未重跑。

### F6 — W11 部分出口未保留

W11 初始化 is_new=None，有 error_pre_snapshot、缺 sha 出口，absent_both 为 low，vanished 不改 is_new；B2 替代算法未保留这些出口和口径。“删掉”只指设计语义未保留，不指母本已被修改。（输入 F6；lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py:141、:155、:157、:189、:202、:205、:207；lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md:133、:136、:137、:138。）

输入 F1 所列命令报告 B2 的 `error_pre_snapshot`、`is_new` 两项 `B2_TOKEN_COUNT` 均为 0。本撰写员未重跑；W11 自身未知折叠仍受 D6 限定。

### F7 — 母本基准指纹

输入核证方报告当前母本为 `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636 / 399508 B`，前后实算一致。对象为 out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py。（输入 F7。）

输入 F1 所列命令报告 `MOTHER_HASH_AND_BYTES_MATCH ('517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636', 399508)`。本撰写员未重算；未来开工须重算，不保证并行或未来状态。

### F8 — D-25 本地编号无冲突

输入核证方确认待裁顶层为 D-13、D-14、D-24，全文最大 D 编号 24。（输入 F8；lead/PENDING_DECISIONS.md:20、:22、:47、:66、:125。）

输入 F1 所列命令报告 `MAX_D 24 PENDING_ENTRY_IDS ['13', '14', '24']`。只绑定核证方本次读取的本地版本，不证明远端或未来状态；本撰写员未重跑。

### F9 — 复核回件与门禁的有限含义

复核回件记载 checkedEveryRow=true、overreachFound=false，并绑定当前预审件；输入核证方报告预审件为 `a108a6e45f42c449db5d228abc469e5c17d40db0b04f15aa32105adff8905449 / 28410 B`，与回件一致。（输入 F9；lead/b2_preaudit_20261106/review/B2_PREAUDIT_REVIEW.md:9、:10、:11、:158。）

输入核证方执行 `python -I -X utf8 lead/b2_preaudit_20261106/check_b2_preaudit.py`，报告 `RESULT: PASS`（全部检查项通过；exit 0），退出码 0。但 lead/b2_preaudit_20261106/check_b2_preaudit.py:194 只在 verdict=YES 时检查复核回件；本次 NO 分支不验证全部技术事实。本撰写员未执行此门禁。

### F10 — 核证脚本执行与只读检查

输入核证方执行 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/d25_ruling_20261106/_d25_facts.py`，报告退出 0；输出保存于 lead/d25_ruling_20261106/_d25_facts_out.txt，含 `CORE_CHECKS=8/8`、`READ_ONLY_SOURCES_CHANGED []`、`RESULT=PASS`、`SCRIPT_EXIT 0`。（输入 F10。）

范围是静态解析母本和手写离线合成模型，未启动或导入母本 harness。本撰写员未读取脚本/输出内容或重跑，不将其记为亲跑通过。

### F11 — 既有顺序、PARTIAL 与历史 14 测

D-24 顺序 A>B>D>C；A1 总判 PARTIAL；W11 候选输入核证方实算为 13190 B。历史日志 14 测通过，本轮核证未重跑该套件。（输入 F11；lead/re_line_20261105/D24_RULING/RULING_D24.md:7、:61、:70、:71；lead/re_line_20261105/A1_ERRATA_MAP/A1_ERRATA_MAP.md:8；lead/re_line_20261105/W11_EXCEPT_FRESHNESS/_w11_t3_test_out.txt:34、:35。）

输入核证方执行命令：

```text
rg -n '_pre_freshness_snapshot|不得用.*sha|PASS=14|EXIT=0|CONFIRMED.*12|PARTIAL.*5|采用档位.*CONFIRMED|采用档位.*PARTIAL' out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py lead/re_line_20261105/W11_EXCEPT_FRESHNESS/_w11_t3_test_out.txt lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md
```

输入报告历史日志 :34 `PASS=14 FAIL=0`、:35 `EXIT=0`；其余输出与该 rg 退出码未在输入逐字提供，不补造。本撰写员未执行；不记为本轮测试通过。

## 存疑项与必须收窄的结论

### D1 — 异常类型、到达保证与遮蔽

“早退/异常必抛 UnboundLocalError”不成立。完全未赋值的裸名为 NameError 风险，补 main 局部赋值而被早退绕过才可能是 UnboundLocalError。finally 之前语句可能失败，不能保证总到达调用。（输入 D1、F2–F3；lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md:63；out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:7048、:7117。）

输入 F1 所列核证命令中的合成模型报告 synthetic_no_assignment 的 early/exception/normal 均 NameError；synthetic_normal_assignment 的 early/exception 为 UnboundLocalError、normal 返回 {}；原 ValueError 保留在 __context__。完整应用后 harness 未运行。本撰写员未重跑；仅确认风险，不推全路径必然异常。

### D2 — N4/N6 错引

正常路径缺新鲜性字段为 N4/high，N6 是 diff 示意不可套用/改动面账不符，medium。（输入 D2；lead/b2_preaudit_20261106/B2_PREAUDIT.md:82、:90。）输入核证脚本报告 `HIGH_IDS ['N1', 'N2', 'N4', 'N5', 'N11']`；本撰写员未重跑。字段缺口本身仍成立。

### D3 — high 并非所有分支

{} 与 {'exists': False} 折叠成立；high 只限 post_exists=True，跑后无件为 absent_both/n/a。（输入 D3；lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md:137、:138。）输入核证命令中的手写转录模型报告两类 pre 在 post_exists=True 均为 `('new_first_appearance', 'high')`，False 均为 `('absent_both', 'n/a')`。本撰写员未重跑；不能写“恒给 high”。

### D4 — 引用错误数与调用点总数

复核回件写 4 处错引 + 1 处轻微不精确，共五个编号项，不是六处。（输入 D4；lead/b2_preaudit_20261106/review/B2_PREAUDIT_REVIEW.md:18、:85、:110、:116、:121、:128、:132、:166。）输入核证脚本报告 `REVIEW_ENUMERATED_ISSUES ['1','2','3','4','5']`。

22 处是复核员限定目录自报，见该回件 :112；本轮核证未确认全仓恰为 22。输入核证方执行 `rg -n --glob '*.py' 'copy_post_except_evidence\(rec' lead/goal1_a8_fix_20261022 lead/goal1_harness8_20261031`，报告找到母本外至少五处，足以否定“全仓唯一”；完整逐行输出与退出码未提供。本撰写员未重跑，不补造全仓总数。

### D5 — 新鲜性风险不等于已违反 crash 禁令

母本禁的是用 sha 变化判 crash。B2 输出 evidence_freshness 并声明不做 crash 归因/F-E 分离；当前母本以集合差判新异常，预审亦未发现 E 函数本体修改。未发现实际消费 F 判 crash 的执行证据。（输入 D5；out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:672、:677、:679、:689、:700；lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md:160、:161、:205；lead/b2_preaudit_20261106/B2_PREAUDIT.md:111。）只能写下游误读风险，不能断言已违反禁令。

### D6 — 路线成本未验，W11 未全面解决未知

“重写一半”“B 改动面更小”“零风险推进目标①”“重写量可能超过重做”缺同口径完整候选、工作量或差异统计。（输入 D6；lead/control_20261106/D25_ENTRY_DRAFT.md:55、:59、:61、:71；lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md:183、:190。）

W11 虽有显式 error/None 出口，仍经 bool(pre.get('exists')) 把 None/{} 当跑前无件，不能当已正确的集成基线。（输入 D6；lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py:154、:181、:187、:193。）历史 14 测不证明集成或成本；A/B 成本优劣与真实卡顿收益均未验。

### D7 — 一般授权不因 NO 失效

草案重新询问一般离线授权，遗漏 D-24 已作的区别：来源会话可安排限定离线 B，不必重复一般授权；执行代理仍须指定任务写域，真机限制继续生效。（输入 D7；lead/control_20261106/D25_ENTRY_DRAFT.md:65；lead/re_line_20261105/D24_RULING/RULING_D24.md:61、:65、:77。）不从 B2 被否推导授权失效，也不从一般授权扩大本轮写域。

## selfBias：偏差提示与处理

以下来自输入《事实核证》selfBias，属于需防范的推论倾向；动机未验，不作为人物事实。

1. 草案 :70 明示偏 B/C，:55 把 A 说成“重写一半”、:59 把 B 说成“改动面更小”，没有可比较的完整实现。可能偏好另起基线或避免返工；裁决不采纳成本断言。（出处：输入 selfBias 1、D6；lead/control_20261106/D25_ENTRY_DRAFT.md:55、:59、:70。）
2. 草案 :29 的“独立理由”与 :35 N5、:38 实际 N4 存在 E1 接线/交付根因重叠，多次计数可能强化否决叙事。裁决不从数量推出路线优劣。（出处：输入 selfBias 2、D2；lead/control_20261106/D25_ENTRY_DRAFT.md:29、:35、:38；lead/b2_preaudit_20261106/B2_PREAUDIT.md:30、:82。）
3. :47 “高置信地判错”“会踩禁令”、:48 六处错引放大负面结论。保留状态折叠、字段缺失与未证 crash 归因的界线。（出处：输入 selfBias 3、D3–D5；lead/control_20261106/D25_ENTRY_DRAFT.md:47、:48。）
4. :57、:71 以历史 14 测背书 B，可能锚定测试数量；模块历史测试未证明母本接线、全部早退、未知快照和完整收尾。裁决要求新版本逐项审查及获准离线测试。（出处：输入 selfBias 4、F11、D6；lead/control_20261106/D25_ENTRY_DRAFT.md:57、:71；lead/re_line_20261105/W11_EXCEPT_FRESHNESS/_w11_t3_test_out.txt:34、:35。）
5. :60、:61 把 C 说成零风险，可能偏好易交付分析；不能证明目标①修复收益，提前分析也须解释相对 D-24 新证据与收益。裁决保留原顺序。（出处：输入 selfBias 5；lead/control_20261106/D25_ENTRY_DRAFT.md:60、:61；lead/re_line_20261105/D24_RULING/RULING_D24.md:7、:40、:44。）
6. 核证方自身须防止因确认 NO 就追认全部措辞。八项核心事实复现不覆盖异常类型、编号、high 范围和路线成本；核证未替用户裁 A/B/C。本文继续逐项限缩。（出处：输入 selfBias 6、F10、D1–D7。）

## 核对意见与本撰写员执行账

输入《裁决书事实核对意见》：`approved: true`、`blockers: []`、`missing: []`、`unverifiable: []`。没有输入核对意见要求登记的事实错误。此意见不取消上述争议和未验，不是本撰写员新跑的门禁。

本撰写员实际执行 `pwd; rg --files lead/d25_ruling_20261106`，输出 `/d/Project/ra2-campaign-forge`，列出 `_d25_facts_out.txt` 与 `_d25_facts.py`。该命令仅定位目录与已存在文件。随后使用文件写入工具写指定两份文书；未读取技术源文件，未重跑 F1/F9 命令或 W11 套件，未执行任何技术检查，不声明本轮亲跑 PASS。（出处：本轮工具记录。）

本任务无另行指定必须由撰写员执行的检查命令；格式要求按写入内容落实，未运行外部门禁。全部执行限制继续有效：零真机、零采样代码、只读指定母本与既有件、唯一写域 lead/d25_ruling_20261106/、不 commit/push、Python 如需执行只能 python -I -X utf8。（出处：本任务《本项目铁律》与《硬性格式》；本轮工具记录。）
