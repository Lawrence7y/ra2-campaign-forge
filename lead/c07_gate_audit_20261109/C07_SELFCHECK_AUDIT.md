# C07_SELFCHECK_AUDIT — lead/c07_slot_20261109/_c7_selfcheck.py 门禁审计报告

被核对象 SHA256 = 74bec4d48498903df08dbf3a56ba942e74b58f5b4a7940c094eafdeb03adbf2e，字节数 = 9961

- 撰写人：审计报告撰写员（本报告为撰写任务交付件）
- 报告路径：lead/c07_gate_audit_20261109/C07_SELFCHECK_AUDIT.md（唯一写入文件）
- 依据：审计会话回件（36 攻样本实跑）、复核会话回件（verdict=confirmed，12 自建样本 + 撰写人 36 样本全量重跑）、两套实跑转录（`_c7a_attack_results.txt` 1862 行、`_c7v_attack_results.txt` 238 行）、门禁源码实读、本撰写会话亲手复跑（指纹两轮 + T04/T06a/T13/selftest 四次实跑）。
- 铁律遵守：零真机、零采样代码、绝对只读保护件、唯一写域 = lead/c07_gate_audit_20261109/、不 commit 不 push。

---

## 1 目的与边界

**目的**：审计 `lead/c07_slot_20261109/_c7_selfcheck.py`（C07 身份补登件填写门禁）能否胜任「C07 身份补登入账前守门人」角色：15 项校验逐项核对判据与绕过空间、构造错填攻样本实跑门禁取真实 exit code、独立重实现对照、给出缺口清单与严重性评级。**审计门禁，不改门禁**。

**边界（本报告及前置审计/复核会话共同遵守）**：
1. 未改 `_c7_selfcheck.py` 一字（撰写会话始末两轮 hashlib 实算指纹均为 74bec4d4…/9961 B，见 §2.1 与 §5）；
2. 未修补任何缺口——缺口只记录（修补属另一任务，需先有缺口报告；本报告即缺口报告）；
3. 零真机：未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存；
4. 零采样代码：无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析；
5. 保护件绝对只读：lead/c07_slot_20261109/ 全部、lead/pending_factpack_20261108/、lead/d13d14_cards_20261108/、两件台账（PENDING_DECISIONS.md、GOAL_THREE_TARGETS_20261018.md）；
6. 写域仅 lead/c07_gate_audit_20261109/；不 commit、不 push；
7. 门禁自述的固有边界（`_c7_selfcheck.py:5`、`:182`）：ID 真值真伪由来源会话自证，门禁只验格式、一致性与冒用面——本审计在此边界内检验，另用边界样本 T29 验证该边界确属两器都无法离线证明。

**审计方法**（前置会话产物，本撰写会话已抽查复跑）：
- 审计会话：36 个错填攻样本（`_c7a_samples/`，36 件）+ 未填模板/selftest 两个基线，每样本对门禁与独立实现校验器各实跑一遍，共 72 次实跑 + 2 基线，全文转录 `_c7a_attack_results.txt`（1862 行，含每样本 exit code）；
- 复核会话（独立，未读撰写人实现）：自建 12 样本（`_c7v_samples/`）双器实跑 + 撰写人 36 样本全量重跑，转录 `_c7v_attack_results.txt:102-238`；
- 本撰写会话亲手复跑：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/c07_slot_20261109/_c7_selfcheck.py <样本>` 对 T04、T06a、T13 及 `--selftest` 四次，exit code 分别为 1、0、0、0（详见 §4.3）；11 件上游指纹两轮 hashlib 实算与编排方清单逐一相符。

---

## 2 上游指纹（十一件）与 15 项校验逐项记录

### 2.1 上游指纹（十一件）

下表指纹为本撰写会话以 `python -I -X utf8` + hashlib 实算（会话首轮），与编排方清单逐件相符；会话末轮复算见 §5 未改声明。

| # | 文件 | SHA256 | 字节数 | 一致 |
|---|------|--------|--------|------|
| 1 | lead/c07_slot_20261109/_c7_selfcheck.py（被核对象） | 74bec4d48498903df08dbf3a56ba942e74b58f5b4a7940c094eafdeb03adbf2e | 9961 | ✓ |
| 2 | lead/c07_slot_20261109/_c7_record_template.json | 3d763a8b679370ade8999a23a18679c7296909bf8a020b71694c0ccca7e8b062 | 3812 | ✓ |
| 3 | lead/c07_slot_20261109/_c7_SLOT_PREP.md | 084158116dde618cdb0588970305f533f7c6d532aebcc44bb1529d97f2aeabd5 | 17233 | ✓ |
| 4 | lead/c07_slot_20261109/C07_IDENTITY_SLOT.md | 05ecdfca451476bb80d84281068fcd9c59d1364b2247cb5482943de6417781fc | 20651 | ✓ |
| 5 | lead/pending_factpack_20261108/_fp_N10-C07_Q6.md | 1b63256d22ee367eecf984f8661c9256222afce37582f6bc79711b436d03a450 | 5756 | ✓ |
| 6 | lead/d13d14_cards_20261108/DECISION_QUESTIONS.md | 0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f | 27172 | ✓ |
| 7 | lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md | c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c | 27225 | ✓ |
| 8 | lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json | d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b | 27965 | ✓ |
| 9 | lead/a_residual_20261106/ACCEPTANCE_RECORDS.json | d421f8bc5cc02eee2a0ea908a60477cdb313541cbff3cfd96a65728528d0efda | 37517 | ✓ |
| 10 | lead/PENDING_DECISIONS.md | 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 | 52419 | ✓ |
| 11 | lead/GOAL_THREE_TARGETS_20261018.md | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 759518 | ✓ |

补充件（非编排方清单，但属门禁 H11 必绑第 4 件）：lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md，sha256=7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0 / 29619 B（审计会话实算 `_c7a_fp_out.txt:8`；本撰写会话末轮复算一致，见 §5）。

**H09 对照数据源实况**（`_c7a_fp_out.txt:15-41`，实跑读取）：a_residual_20261106 件 17 条记录 reviewerSessionId 全为 None（旧 schema 无此键，对 H09 对照集**零贡献**）；a_residual_n1 件 7 条记录共用 1 个 ID（sess_dwf-dwfrun-324c613e-fb0e-42f5-9883-805fef5b80de-actor_3_1）。即 **H09 冒用面对照基数=1**——本撰写会话 selftest 复跑输出「对照已登ID基数=1」与门禁各样本输出一致，一手证实。

### 2.2 15 项校验逐项记录

判据行号均引自我在本会话对 `_c7_selfcheck.py` 的实读；失败条件/绕过空间均给出实跑证据（样本号 + 转录行）。「拦住」=门禁 exit=1；「漏过」=门禁 exit=0 但样本为错填/冒签通道。15 项 = 打印口径 checks=15（H06 对三字段各打一行）。

| # | 门禁项 | 判据（文件:行） | 失败条件（门禁能拦的） | 绕过空间（门禁拦不住的，实跑证据） |
|---|--------|----------------|------------------------|----------------------------------|
| 1 | H01 JSON可解析 | _c7_selfcheck.py:91-95（json.loads） | 非 JSON 必拦 | 无绕过面。36 样本全部过 H01 |
| 2 | H02 容器13键齐 | :97-99 | 13 键（:18-20）有**缺**则拦（T09a 缺 grade，FAIL exit=1，:707-731） | **只查缺失不查多余**：多余键 `extraApprovalClaim`（夹带 APPROVE_SCOPE 附加声明）放行——T09b gate exit=0（:757-777）。独立器 I02 键集合精确相等，拦（:780-781）。→ G9（medium） |
| 3 | H03 schema精确串 | :100-101 | schema ≠ "N-1-ACCEPTANCE-RECORDS/2" 拦 | 无绕过面（精确串比对）。T13 正样本 PASS |
| 4 | H04 records恰1条 | :102-105 | records=0（T08a）/ =2（T08b）均 FAIL exit=1（:613-631、:660-678）；且 rec 非 dict 时 H05–H12 整组判「记录缺失，未检」FAIL（:167-168），仍拦 | 无绕过面 |
| 5 | H05 9字段名与顺序 | :107-108（FIELDS9 :16-17） | list(keys)==FIELDS9 严格相等：乱序（T10，timestamp 移第 2 位）FAIL exit=1（:807-827） | 无绕过面（list 相等含顺序） |
| 6 | H06 reviewerRole非空非拒填值 | :109-112（BAD_VALUES :32） | 空串/unknown/TODO/N/A 等黑名单值拦（T01、T02a/b/c 全拦） | **无内部角色黑名单**：照抄 PERF:151 三内部角色全放行——T06a「卡顿分流员·GLM」、T06b「分流报告撰写员」、T06c「独立复核员」gate exit=0「GATE PASS checks=15 failed=0」（:412-432、:462-482、:512-532），任务书明列此为冒签。独立器 I11 全拦。→ **G1（high·冒签）** |
| 7 | H06 reviewerSessionId非空非拒填值 | 同 :109-112 | 黑名单值拦（T02a/b/c） | **无运行态形制校验**：黑名单外任意垃圾值放行——T18a `-`、T18b `12345` gate exit=0（:1357-1377、:1408-1428）；任务书失败条件明列「编造非运行态UUID」。独立器 I10 要求 sess_dwf-dwfrun-\<UUID\>-actor_\<n\>_\<m\> 形制，全拦。→ **G5（high·冒签）** |
| 8 | H06 sourceTaskId非空非拒填值 | 同 :109-112 | 非空即过（本项设计如此）；裸计划号由 H10 补查（T04） | 见 #12 H10 的两个绕过（G7/G8） |
| 9 | H07 记录内无占位符残留 | :113-114（正则 :31 `r"<[^>]*>"`） | 半角 `<>` 占位符拦（T07 `<来源会话sessionId>` FAIL exit=1，:562-582；未填模板 H07 FAIL，:15-25） | **仅半角**：全角 `＜来源会话sessionId＞` 放行——T22 gate exit=0（:1560-1580）。独立器 I07 半角+全角+裸角字符，拦。→ G10（medium） |
| 10 | H08 记录内无unknown/TODO等拒填值 | :115-116 | 与 H06 同黑名单**精确匹配**：T01 三空串命中全拦 | 黑名单外组合词（如「暂无」类）可放行——代码读证（:115 精确 in 判定），**无实跑样本，未验**。独立器 I08 精确+词级正则。→ 并入 G5 面的旁证（无独立评级） |
| 11 | H09 sessionId不冒用他件已登ID | :117-120（对照集 :62-77，来源 :27-30） | **精确照抄**已登 ID 拦：T03 FAIL「与a_residual两件已登ID冲突」exit=1（:261-281） | (a) **仅精确集合比对**：尾随空格/大小写变体放行——T19 gate exit=0（:1459-1479），独立器 I09 归一化拦；(b) **对照基数=1**（§2.1），冒用面覆盖极窄。→ G6（medium·冒用面） |
| 12 | H10 计划号时unresolved必非空 | :121-128（fullmatch :123） | 裸计划号 + unresolved=[] 拦：**T4**（T04_n11_no_registration）FAIL「计划号须在unresolved登记…」exit=1（:312-332；本撰写会话复跑同结果，§4.3） | (a) **fullmatch 装饰绕过**：`N-11（计划号）` fullmatch 失败 → 走 :127-128 else「计划号规则未触发」PASS 且免登记——T20 gate exit=0（:1510-1530）；(b) **登记语不验**：unresolved 任意非空即过——T23 非空但登记语无关，gate exit=0（:1611-1631）。独立器 I12 子串触发+登记语必验，全拦。→ G7、G8（均 medium） |
| 13 | H11 inputHashes四件实算复核 | :129-156（必绑4件 :21-26） | 必绑件缺/格式错/复算不符全拦：T12a 假 hex、T12b 假 bytes、T12c 缺 PERF_REPAIR_HANDOFF 均 FAIL exit=1（:1007-1027、:1057-1077、:1107-1127） | (a) **额外键零校验**（:135 只遍历 REQUIRED_INPUTS）：T24 夹带指向不存在文件的伪造键 gate exit=0（:1661-1681）；(b) **artifactHashes 整字段零校验**（该词全文仅出现于 :16-17 字段名表）：T17 对现有文件填 ff×32/123 假指纹 gate exit=0（:1307-1327）。独立器 I13/I14 全键实算，全拦。→ G11（medium） |
| 14 | H12 timestamp ISO8601可解析 | :157-165 | 不可解析拦（T11a `2026-11-09 40:70:00`、T11b int 20261109、T11c `不是时间` 全 FAIL） | **无合理域**：任意年代/日期-only（如 `2026-11-09`）可解析即过——代码读证（fromisoformat），**无实跑样本，未验**。独立器 I15 有 INFO 面。→ G12（low） |
| 15 | H13 容器层无占位符残留 | :169-171（同 :31 半角正则） | 容器层半角占位符拦（未填模板 H13 FAIL） | 同 #9 仅半角（T22 面上记录层）；且**容器层值内容完全零校验**——grade/decision/decisionSemantics/reviewer.role/reviewer.sessionId 任意值皆过：T16 语义掉包、T26 容器 role=独立复核员、T27 grade=APPROVE_SCOPE、T09b 附加声明全部 gate exit=0；复核器 S15 容器 sessionId=已登 ID 亦 gate exit=0（_c7v_attack_results.txt:194-197）。→ G1/G2/G3/G4（high）+ G9/G10（medium）+ **G14（复核补列，medium）** |

另（门禁自身文书形制，非绕过面）：门禁打印的绑定行 `_c7_selfcheck.py:181` 为 `print("被核对象 SHA256 = \`%s\`，字节数 = %d"…)`，hex 两侧带反引号，不符合「绑定行中间不得插入反引号」的复核格式要求 → G13（low）。

---

## 3 独立重实现与双实现对比

### 3.1 两套独立实现

- **审计独立器** `_c7a_independent.py`（I 系列，打印 24 项；仅依据任务书填写规则 + 模板固定值口径编写）：I01 JSON可解析；I02 容器键集合==13键**精确相等**（缺+多都拦）；I03 schema 精确串；I04 records恰1条dict；I05 9字段名与顺序精确相等；I06 三身份字段非空非拒填（×3 行）；I07 全件无占位符残留（**半角+全角+裸角括号**）；I08 全件无拒填值（精确+词级）；I09 sessionId 不冒用（**精确+归一化近似**）；I10 sessionId 符合**运行态先例形制**（sess_dwf-dwfrun-\<UUID\>-actor_\<n\>_\<m\>）；I11 签发角色不冒用**内部角色**（**记录层+容器 reviewer.role**）；I12 计划号**子串触发+登记语必验**；I13 inputHashes **全键实算**（含额外键）；I14 artifactHashes **全键实算**；I15 timestamp 可解析；I16 decision∈{REGISTERED,PARTIAL}；I17 grade 非空且无 APPROVE/放行语汇（+未取 REGISTERED/PARTIAL 的 INFO）；I18 **六固定字段与模板逐字一致**；I19 writeDomain 非空且非既有只读域；I20 revisionOf=null；I21 容器 reviewer.sessionId 不冒用已登 ID 且符合形制。（检查名引自审计转录 `_c7a_attack_results.txt:28-51` 基线输出）
- **复核独立器** `_c7v_independent.py`（22 检查，复核会话**未读撰写人实现**独立写成）：I01–I08 同向；I09/I10 合并为「记录层 sessionId 非冒用（精确+归一）且运行态形制」；I11 容器 role 非拒填/非占位/非内部角色；I12 计划号登记（子串触发+登记语必验）；I13/I14 全键实算；I15 timestamp **且含时间成分**；I16 decision 值域；I17 grade 定档且禁签署语汇；I18 六固定字段逐字；I19 writeDomain 形制；I20 revisionOf==null；I21 **容器 sessionId 非冒用/运行态形制/与记录一致**；**I22 itemId 固定值**（N10-C07-Q6-identity）；I23 unresolved 为字符串列表。（检查名引自 `_c7v_attack_results.txt:28-49`）

### 3.2 双实现判定对比（36 输入，逐行取自 _c7a_attack_results.txt）

- **判定一致 20 个**：17 个双拦（T01、T02a/b/c、T03、T04、T07、T08a/b、T09a、T10、T11a/b/c、T12a/b/c）+ 3 个双放（T05、T13、T29）。
- **分歧 16 个**：T06a/b/c、T09b、T14、T16、T17、T18a/b、T19、T20、T22、T23、T24、T26、T27——**全部为「门禁放行、独立器拦下」单一方向**，零反向误伤（17 个门禁拦住的样本独立器无一放行）。
- 计数勘误：审计回件自称「22 一致、14 分歧」，按转录逐行重计为 **20 一致、16 分歧**；与复核回件对样本级计数的勘误（拦住 17 非 18、放行枚举 16 项非 14）同源——**逐项枚举本身全对，仅汇总计数有误**，方向结论不变。
- 复核独立器在 12 个自建样本上与门禁产生 **9 个分歧**（S02/S03/S04/S05/S06/S07/S08/S09/S15，全部「门禁放行、独立器拦下」），S01、S11 双器皆拦，S10 双器皆放（_c7v_attack_results.txt:102-201）——第二套独立实现得出同向结论。

### 3.3 差异点分析（门禁 vs 独立器，逐条对应实测分歧）

| 差异点 | 门禁口径 | 独立器口径 | 实测后果 |
|--------|----------|-----------|----------|
| 容器键集合 | H02 只查缺失（:98） | I02 精确相等 | T09b 多键夹带声明，门禁放行 |
| 占位符 | H07/H13 仅半角正则（:31） | I07 半角+全角+裸角 | T22 全角残留，门禁放行 |
| 拒填值 | H08 精确匹配（:115） | I08 精确+词级 | 组合词面无实跑样本（未验） |
| 冒用面 | H09 精确集合比对，对照基数=1（:119） | I09 精确+归一化 | T19 尾随空格照抄，门禁放行 |
| sessionId 形制 | H06 无形制校验 | I10 运行态形制 | T18a `-`、T18b `12345`，门禁放行 |
| 内部角色 | H06 无黑名单 | I11 记录层+容器层黑名单 | T06a/b/c、T26，门禁放行（冒签） |
| 计划号 | H10 fullmatch+仅非空（:123-124） | I12 子串触发+登记语必验 | T20 装饰免登记、T23 假登记语，门禁放行 |
| inputHashes | H11 仅 4 必绑件（:135） | I13 全键实算 | T24 伪造额外绑定，门禁放行 |
| artifactHashes | 门禁整字段不验（全文无校验） | I14 全键实算 | T17 假指纹，门禁放行 |
| decision/grade/decisionSemantics | 门禁零校验 | I16 值域 / I17 语汇 / I18 六固定字段逐字 | T14、T27、T16，门禁放行（冒签/语义掉包） |
| itemId/writeDomain/revisionOf/unresolved 形制 | 门禁不验（itemId 无固定值校验） | I22（复核器）/I19/I20/I23 | 无专门 T 样本（itemId 面**未验**）；正负样本两器无冲突 |
| 真值真伪 | 两器均声明不代证（:5、:182；独立器 I10 注记） | 同 | T29 形制合规编造 sessionId 两器皆过——边界确证 |

---

## 4 攻样本逐样本实跑结果表与缺口清单

任务书第四节述「13 个攻样本」；实跑为 **36 个样本**（`_c7a_samples/` 36 件；本撰写会话逐行核对 `_c7a_attack_results.txt:57-1862` 的 36 个 `===SAMPLE` 段：17 个 exit=1、19 个 exit=0；复核回件全量重跑同结果，`_c7v_attack_results.txt:202-238`）。「13」恰与本报告缺口清单 G1–G13 的数目一致。下表按实跑 **36 行全量**给出，不删减。判定列：**拦住**=门禁 exit=1；**漏过**=门禁 exit=0 但样本为错填/冒签通道；双PASS=合法路径符合预期；边界=两器固有边界样本。

### 4.1 基线（实跑）

| 基线 | 结果 | 出处 |
|------|------|------|
| `--selftest` | SELFTEST PASS（对照已登ID基数=1），exit=0 | _c7a_attack_results.txt:1-3；本会话复跑同 |
| 未填模板 → 门禁 | GATE FAIL checks=15 failed=4（H07/H11/H12/H13），exit=1 | :5-25 |
| 未填模板 → 独立器 | I-GATE FAIL checks=24 failed=6，exit=1 | :27-55 |
| 复核基线3：S10 正样本双器 | GATE PASS / INDEP PASS，双 exit=0 | _c7v_attack_results.txt:53-101 |

### 4.2 36 攻样本逐样本实跑结果表

| # | 样本 | 攻击面（样本字段实读） | 门禁 GATE 行 / exit | 判定 | 独立器 exit | 缺口·严重性 |
|---|------|------------------------|---------------------|------|-------------|-------------|
| 1 | T01_empty_trio | 三身份字段全空串 | FAIL checks=15 failed=4（H06×3+H08）/ 1 | 拦住 | 1（I06×3+I08+I10） | 无（黑名单内值） |
| 2 | T02a_sid_unknown | sessionId=unknown | FAIL failed=2（H06+H08）/ 1 | 拦住 | 1 | 无 |
| 3 | T02b_sid_todo | sessionId=TODO | FAIL failed=2（H06+H08）/ 1 | 拦住 | 1 | 无 |
| 4 | T02c_sid_na | sessionId=N/A | FAIL failed=2（H06+H08）/ 1 | 拦住 | 1 | 无 |
| 5 | T03_sid_copied_n1r2 | 照抄 n1 件已登 ID（精确） | FAIL failed=1（H09 与a_residual两件已登ID冲突）/ 1 | 拦住 | 1（I09 精照抄） | 无（H09 精确面有效） |
| 6 | **T4** T04_n11_no_registration | sourceTaskId=裸 N-11 + unresolved=[] | FAIL failed=1（H10）/ 1 | 拦住 | 1（I12） | 无（H10 触发面有效） |
| 7 | T05_n11_registered_gap | N-11 + 合规登记语 | PASS checks=15 failed=0 / 0 | 双PASS（合法） | 0 | 无 |
| 8 | **T6** T06a_role_kadun | reviewerRole=卡顿分流员·GLM（冒签） | PASS checks=15 failed=0 / 0 | **漏过** | 1（I11 记录层） | **G1·high（冒签）** |
| 9 | T06b_role_fenliu | reviewerRole=分流报告撰写员（冒签） | PASS checks=15 failed=0 / 0 | **漏过** | 1（I11） | **G1·high（冒签）** |
| 10 | T06c_role_fuhe | reviewerRole=独立复核员（冒签） | PASS checks=15 failed=0 / 0 | **漏过** | 1（I11） | **G1·high（冒签）** |
| 11 | T07_sid_placeholder | sessionId=`<来源会话sessionId>`（半角占位符） | FAIL failed=1（H07）/ 1 | 拦住 | 1（I07+I10） | 无 |
| 12 | T08a_records_zero | records=[] | FAIL checks=13 failed=9（H04+H05–H12 记录缺失未检）/ 1 | 拦住 | 1 | 无 |
| 13 | T08b_records_two | records=2 条 | FAIL checks=13 failed=9 / 1 | 拦住 | 1 | 无 |
| 14 | T09a_container_missing_grade | 容器缺 grade 键 | FAIL failed=1（H02 缺=['grade']）/ 1 | 拦住 | 1（I02+I17） | 无 |
| 15 | T09b_container_extra_key | 多余键 extraApprovalClaim 夹带「本件同时构成 APPROVE_SCOPE 签署」附加声明 | PASS checks=15 failed=0 / 0 | **漏过** | 1（I02 多=['extraApprovalClaim']） | G9·medium |
| 16 | T10_field_order | 9 字段乱序（timestamp 移第 2 位） | FAIL failed=1（H05）/ 1 | 拦住 | 1（I05） | 无 |
| 17 | T11a_ts_bad | timestamp=`2026-11-09 40:70:00` | FAIL failed=1（H12）/ 1 | 拦住 | 1（I15） | 无 |
| 18 | T11b_ts_int | timestamp=20261109（int） | FAIL failed=1（H12）/ 1 | 拦住 | 1（I15） | 无 |
| 19 | T11c_ts_text | timestamp=「不是时间」 | FAIL failed=1（H12）/ 1 | 拦住 | 1（I15） | 无 |
| 20 | T12a_hash_wrong_hex | inputHashes 假 hex（fa709f…） | FAIL failed=1（H11 复算不符）/ 1 | 拦住 | 1（I13） | 无 |
| 21 | T12b_hash_wrong_bytes | 字节数改 27173 | FAIL failed=1（H11 复算不符）/ 1 | 拦住 | 1（I13） | 无 |
| 22 | T12c_hash_missing_binding | 缺必绑件 PERF_REPAIR_HANDOFF | FAIL failed=1（H11 缺必绑件）/ 1 | 拦住 | 1（I13） | 无 |
| 23 | T13_positive | 完全合法正样本 | PASS checks=15 failed=0 / 0 | 双PASS（合法） | 0 | 无 |
| 24 | T14_decision_approve_scope | decision=APPROVE_SCOPE（越权签署） | PASS checks=15 failed=0 / 0 | **漏过** | 1（I16 'APPROVE_SCOPE'） | **G2·high（冒签）** |
| 25 | T16_decisionsemantics_tampered | decisionSemantics 掉包为 decision=APPROVE_SCOPE 语义 | PASS checks=15 failed=0 / 0 | **漏过** | 1（I18 decisionSemantics） | **G4·high（冒签）** |
| 26 | T17_artifacthash_fake | artifactHashes 对现有文件填假指纹（ff×32/123） | PASS checks=15 failed=0 / 0 | **漏过** | 1（I14 复算不符） | G11·medium |
| 27 | T18a_sid_dash | sessionId=`-`（非运行态） | PASS checks=15 failed=0 / 0 | **漏过** | 1（I10） | **G5·high（冒签）** |
| 28 | T18b_sid_digits | sessionId=`12345`（非运行态） | PASS checks=15 failed=0 / 0 | **漏过** | 1（I10） | **G5·high（冒签）** |
| 29 | T19_sid_nearcopy | 已登 ID+尾随空格（近似照抄） | PASS checks=15 failed=0 / 0 | **漏过** | 1（I09 近似+I10） | G6·medium（冒用面） |
| 30 | T20_n11_decorated | sourceTaskId=`N-11（计划号）`+unresolved=[] | PASS checks=15 failed=0 / 0 | **漏过** | 1（I12） | G7·medium |
| 31 | T22_fullwidth_placeholder | sessionId=`＜来源会话sessionId＞`（全角占位符） | PASS checks=15 failed=0 / 0 | **漏过** | 1（I07+I10） | G10·medium |
| 32 | T23_unresolved_wrong_phrase | N-11+unresolved 非空但登记语无关 | PASS checks=15 failed=0 / 0 | **漏过** | 1（I12） | G8·medium |
| 33 | T24_inputhash_extra_fake | inputHashes 夹带指向不存在文件的伪造键 | PASS checks=15 failed=0 / 0 | **漏过** | 1（I13 文件不存在） | G11·medium |
| 34 | T26_container_role_fuhe | 容器 reviewer.role=独立复核员（容器层冒签） | PASS checks=15 failed=0 / 0 | **漏过** | 1（I11 容器层） | **G1·high（冒签）** |
| 35 | T27_grade_approve_scope | grade=APPROVE_SCOPE（越权签署） | PASS checks=15 failed=0 / 0 | **漏过** | 1（I17 'APPROVE_SCOPE'） | **G3·high（冒签）** |
| 36 | T29_sid_fabricated_shape | 形制完全合规但编造的 sessionId（零 UUID 真实性） | PASS checks=15 failed=0 / 0 | 边界（两器皆过） | 0 | 无缺口可评——真值真伪属两器固有边界，须来源会话自证叠加 |

**汇总（转录逐行重计）**：门禁拦住 17（exit=1）；门禁放行 19（exit=0）＝漏过 16（T06a/b/c、T09b、T14、T16、T17、T18a/b、T19、T20、T22、T23、T24、T26、T27）+ 双PASS 2（T05、T13）+ 边界 1（T29）。漏过 16 个中 **6 个直接命中任务书明列的冒签通道**（照抄内部角色×3、decision=APPROVE_SCOPE、grade=APPROVE_SCOPE、非运行态 sessionId×2，样本次数 7）。复核回件 36 样本全量重跑逐项 exit code 与本表一致（_c7v_attack_results.txt:202-238），并勘误审计原汇总（拦住 18→17、放行 14→16 项枚举）。

### 4.3 关键样本实跑原文（本撰写会话亲手复跑，非转引）

**T4（T04_n11_no_registration）——拦住，exit=1**：
命令 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/c07_slot_20261109/_c7_selfcheck.py D:/Project/ra2-campaign-forge/lead/c07_gate_audit_20261109/_c7a_samples/T04_n11_no_registration.json`，输出关键行：
```
  [FAIL] H10 sourceTaskId为计划号时unresolved必非空  — 计划号须在unresolved登记「正式任务书编号未落实」（先例教训 YI_SUPERSEDE:90）
GATE FAIL checks=15 failed=1
```
T04_EXIT=1。其余 14 项全 PASS（H09 对照基数=1 一手可见）。

**T6（T06a_role_kadun）——漏过（冒签），exit=0**：
同一命令换样本 T06a_role_kadun.json（记录层 reviewerRole=`卡顿分流员·GLM`），输出：15 项全 `[PASS]`，其中 H06 reviewerRole 一行显示 `'卡顿分流员·GLM'` 照常 PASS，`GATE PASS checks=15 failed=0`。T06a_EXIT=0。**门禁对冒签角色零校验，放行**。

T13 正样本：GATE PASS checks=15 failed=0，exit=0（合法路径可用）；`--selftest`：SELFTEST PASS（对照已登ID基数=1），exit=0。

### 4.4 缺口清单与补法（只描述，未实施）

总评级 **high**：G1–G5 任一即可让错误身份值/越权签署语义通过校验、被当成合法登记（**冒签成功**）。

| 编号 | 严重性 | 缺口（实跑证据） | 补法描述（未实施） |
|------|--------|------------------|--------------------|
| G1 | **high·冒签** | reviewerRole 无内部角色黑名单：照抄 PERF:151 三内部角色过闸（T06a/b/c 记录层、T26 容器层，均 gate exit=0） | 对记录层 reviewerRole 与容器 reviewer.role 做精确+子串黑名单比对 |
| G2 | **high·冒签** | decision 值域不验：填 APPROVE_SCOPE 即成「签署」（T14 exit=0） | decision ∈ {REGISTERED, PARTIAL} |
| G3 | **high·冒签** | grade 无值域/语汇校验：APPROVE_SCOPE 过闸（T27 exit=0） | grade 限 REGISTERED/PARTIAL 且禁 APPROVE/放行字样 |
| G4 | **high·冒签** | decisionSemantics 等六固定字段不验照抄：语义掉包过闸（T16 exit=0） | 六固定字段与模板逐字比对 |
| G5 | **high·冒签** | sessionId 无运行态形制校验：`-`、`12345` 入账（T18a/b exit=0；任务书失败条件明列「编造非运行态UUID」） | sess_dwf-dwfrun-\<UUID\>-actor_\<n\>_\<m\> 形制校验（真值仍由来源会话自证） |
| G6 | medium·冒用面 | H09 仅精确集合比对：尾随空格/大小写近似照抄过闸（T19 exit=0）；且对照集实际基数=1（20261106 件旧 schema 无 reviewerSessionId 键，零贡献） | 归一化比对；对照集来源宜扩展 |
| G7 | medium | H10 计划号用 fullmatch：`N-11（计划号）` 装饰绕过免登记（T20 exit=0） | 子串命中即触发 |
| G8 | medium | H10 不验登记语：unresolved 任意非空即过（T23 exit=0） | 必须含「正式任务书编号未落实」 |
| G9 | medium | H02 不查多余键：可夹带任意附加声明（T09b 实测夹带 APPROVE_SCOPE 声明 exit=0） | 键集合精确相等 |
| G10 | medium | H07/H13 占位符仅半角：全角 `＜＞` 残留过闸（T22 exit=0） | 加全角与裸角字符 |
| G11 | medium | H11 不验 inputHashes 额外键（T24）、artifactHashes 整字段不验（T17）：伪造指纹绑定入账，登记可信链断裂 | 两字段全键实算 |
| G12 | low | timestamp 无合理域：任意年代/日期-only 可解析即过（代码读证 :157-165，无实跑样本，未验） | 合理区间 + 须含时间成分 |
| G13 | low·文书形制 | 门禁自身绑定行 print（:181）hex 两侧带反引号，不符复核绑定行格式 | 去掉反引号 |
| G14 | medium·冒用面（**复核回件补列**） | 容器 reviewer.sessionId 无冒用面/形制校验：复核器 S15 容器 sessionId=已登 ID，gate exit=0（_c7v_attack_results.txt:194-197），独立器 I21 拦——审计 36 样本未覆盖此面、原缺口清单漏列 | 容器 sessionId 与记录层一致 + 同冒用面校验 |
| G15 | low（**复核回件补列**） | 记录 itemId 固定值不验（门禁无此项；复核器 I22 有；无专门 T 样本，未验） | itemId == "N10-C07-Q6-identity" |

复核回件对缺口面的判定：撰写人缺口清单**漏列两面**（G14、G15），两处均使洞面更大，撰写人结论方向无误且偏保守；无「可冒签缺口被评 low」的情况。

---

## 5 复核回件与结论

### 5.1 复核回件（verdict 如实记录）

**verdict = confirmed**（复核成立）。复核绑定行（照录，格式合规）：

被核对象 SHA256 = 74bec4d48498903df08dbf3a56ba942e74b58f5b4a7940c094eafdeb03adbf2e，字节数 = 9961

复核要点（详见复核回件原文；其 12 自建样本与 36 全量重跑转录在本写域 `_c7v_attack_results.txt`）：
1. 指纹：门禁/模板会话首中末三算一致，等于编排方基线；a_residual 对照集实况与撰写人断言一致（对照基数=1）；
2. **T4 复现**：撰写人 T04 重跑 exit=1（H10 FAIL），复核自建等价样本 S01 同 exit=1，独立器 I12 亦拦；
3. **T6 复现**：T06a/b/c 重跑 exit=0「GATE PASS checks=15 failed=0」，复核自建等价 S02/S03 亦 exit=0，独立器 I06 黑名单全拦；
4. 复核自实现 22 检查器（未读撰写人实现）在 12 自建样本上 9 个分歧，全部「门禁放行、独立器拦下」，零反向误伤；并补出 G14（容器 sessionId 冒用，S15）与 G15（itemId 固定值）两面；
5. 撰写人 36 样本全量重跑 exit code 逐项一致（17 个 exit=1、19 个 exit=0），计数勘误两处（拦住 17 非 18；漏过枚举 16 项非 14），逐项枚举全对；
6. 严重性 high 成立：G1–G5 冒签通道全部实跑复现，无可冒签缺口被评 low；
7. 零越界：保护件指纹全程未变；复核写入仅限写域；零真机、零采样、未 commit/push。

### 5.2 结论

**该门禁不能单独作为 C07 身份补登的守门人。**

- **保证边界（它守得住的）**：「形制层」——JSON 可解析、容器 13 键无缺、schema 精确串、records 恰 1 条、9 字段名与顺序、三身份字段非空非黑名单拒填值、半角占位符残留、精确拒填值、已登 ID **精确**照抄、裸计划号+空 unresolved、inputHashes 四必绑件指纹实算相符、timestamp ISO 可解析。这 15 项在 36 攻样本 + 复核全量重跑中判定与预期零不符，形制层可信赖。
- **守不住的（不能缺的）**：「冒用与语义层」——内部角色冒签（G1，记录层+容器层）、decision/grade 越权签署语汇（G2/G3）、六固定字段语义掉包（G4）、非运行态 sessionId（G5）、近似冒用（G6）、多余键夹带（G9）、全角占位符（G10）、额外哈希绑定（G11）、容器 sessionId 冒用（G14）。另真值真伪属两器固有边界（T29：形制合规的编造 sessionId 双器皆过），**必须由来源会话自证叠加**（门禁 :5、:182 自述）。
- **使用判定**：「门禁 exit=0」只能作为 C07 补登入账的**必要条件**，绝不能作为充分条件。以本门禁单独放行即入账，G1–G5 五条通道（全部实跑复现）任一可致冒签成功。入账前至少叠加：独立实现校验器（I 系列口径，实跑已证其对 16 个漏过样本全拦）+ 来源会话身份自证；G1–G5/G14 建议按缺口报告先行修补门禁或以独立器双闸代替。

### 5.3 未改任何文件声明

本撰写会话未修改任何既有文件。唯一写入 = lead/c07_gate_audit_20261109/C07_SELFCHECK_AUDIT.md（本文件）。被核对象与全部保护件于会话始（§2.1 表）与会话末（下轮复算）两轮 hashlib 实算指纹逐一相符——**未改 `_c7_selfcheck.py` 一字**，未改模板，未改 SLOT_PREP/C07_SLOT/事实包/D13D14 卡片/两台账。零真机、零采样、未 commit、未 push。

### 5.4 未验项（如实列出，不补造）

1. 审计 36 样本本撰写会话**未全量重跑**：只亲手复跑 T04、T06a、T13、selftest 四项；其余样本结论引实跑转录 `_c7a_attack_results.txt`（逐行核对过 36 个 exit code 与 FAIL 项）与复核回件的全量重跑记录 `_c7v_attack_results.txt:202-238`。
2. H08 黑名单外组合词绕过、H12 任意年代/日期-only 放行：仅代码读证（_c7_selfcheck.py:115-116、:157-165），**无实跑样本，未验**。
3. G15 itemId 固定值不验：复核器有对应检查项但审计/复核均**未构造专门样本**，未验。
4. T29 类真值真伪：两器均无法离线证明，固有未验——必须由来源会话自证。
5. 复核会话 ranCommands=15 未逐条重演：其转录我已逐行读过并核对计数（§5.1），但 S 系列样本未由本会话亲手重跑。
6. 审计会话「Mimosa PreToolUse 钩子 4 次拦截脚本写入」为审计材料转述的环境事实，本会话未复现验证，未验。
7. 36 样本编号跳号（无 T15/T21/T25/T28）：生成器即如此编号，未验其原因，不影响判定完整性（实跑件数 36 与转录段数一致）。
