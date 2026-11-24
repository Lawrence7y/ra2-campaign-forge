# C07_IDENTITY_SLOT · C07（N10-C07｜Q6 责任身份落实）身份落点规格书

- 立件：2026-11-09；撰写 = 落点准备撰写员（动态工作流子代理）。**本件只备落点、只定字段/格式/校验，不代填任何身份值。**
- 唯一写域 = `lead/c07_slot_20261109/`；写域外一律只读；零真机（不启动 gamemd.exe / ra2loader / YURI.exe，不 taskkill，不读活进程内存）；零采样代码；不 commit、不 push。
- ★ 占位符纪律：全文身份值只以显式占位符出现（`<来源会话sessionId>`／`<来源会话任务ID>`／`<来源会话签发角色>`）；盘上先例件的会话 ID 一律以「格式形」描述、不转录值；`_c7_selfcheck.py:198` 的负测样例（一串故意不匹配 `N-\d+` 的任务号形字符串）同样不转录。
- 承接链：`_c7_SLOT_PREP.md`（准备件，§1-§8）→ 独立复核回件（verdict = partial，见 §6.1）→ 本件为收敛后的落点规格书。本件不改三件既有产物一字（指纹见 §6.2 绑定行）。

## 1 目的与边界（只备落点，不代填身份）

- **目的**：把 C07 要补的三个身份值的落点固化为可执行规格——字段定义（§3）、载体与落点方案（§4）、逐字段校验规则与模板（§5）、多处同步面（§5.4）、补登责任人（§6.4）。来源会话照 §5 填模板、过门禁即完成补登。
- **边界**：
  1. 三字段只交付占位符；值只能由来源会话本人填（依据见 §3、§6.3）。
  2. 最终登记件（建议名 `ACCEPTANCE_RECORDS_C07.json`）不由本件代创建；模板与门禁已备于本写域，复制→替换占位符→跑门禁即可（§4.3）。
  3. 本件是行政登记面的准备文书：不升格任何技术结论（卡面定性 `DECISION_QUESTIONS.md:121`「非技术裁决——来源会话身份补登（行政动作）」）；不构成 APPROVE_SCOPE 签署、不构成 N-5 放行。
  4. 写域外既有件（含两件台账、a_residual 两件、全部只读域）零改动；本轮收尾指纹复核见 §6.2。

## 2 上游指纹（十件，本轮实算）

实跑：`python -I -X utf8` 内联两块（各 5 件）hashlib 逐件复算，与编排方给定基线比对——**10/10 MATCH**（命令与输出留会话痕；无文件产出）。

| # | 件 | 字节数 | SHA256 | MATCH |
|---|---|---|---|---|
| 1 | `lead/pending_factpack_20261108/_fp_N10-C07_Q6.md` | 5756 | `1b63256d22ee367eecf984f8661c9256222afce37582f6bc79711b436d03a450` | True |
| 2 | `lead/pending_factpack_20261108/_fp_INDEX.md` | 5802 | `e827d5ca784f0a194ba3ed509a89b2502ecb14ad7c7830f4a1f09719a74944e2` | True |
| 3 | `lead/d13d14_cards_20261108/DECISION_QUESTIONS.md` | 27172 | `0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f` | True |
| 4 | `lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md` | 29619 | `7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0` | True |
| 5 | `lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md` | 27225 | `c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c` | True |
| 6 | `lead/direction_ruling_20261108/RULING_DIRECTION.md` | 16514 | `0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653` | True |
| 7 | `lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md` | 28897 | `c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801` | True |
| 8 | `lead/b2b_yi_supersede_20261108/YI_SUPERSEDE_JIA_BINDING.md` | 7344 | `255356ca789955cc2c084388f547a1435feb310f210617b988f761e7ff331c7b` | True |
| 9 | `lead/PENDING_DECISIONS.md` | 52419 | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | True |
| 10 | `lead/GOAL_THREE_TARGETS_20261018.md` | 759518 | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | True |

## 3 三字段定义与「N-1 八字段」口径的关系（逐字摘原文；判定：同一套，实为九字段）

### 3.1 卡面与上游逐字

- 卡面问题原文（`DECISION_QUESTIONS.md:120`，逐字）：「Q6 | 责任身份落实 | 任务书未载来源会话 session/run ID | NEXT_STEPS:119 身份落实原则 | 来源会话补登实际身份（本件不补造，见 §6.2）」；裁决类型（`:121`）：「**非技术裁决**——来源会话身份补登（行政动作）」；通道（`:122`）：「来源会话直接补登、无需立 D-xx」。
- N-11 上游自述（`PERF_REPAIR_HANDOFF.md:152`，逐字）：「任务书未载来源会话 session/run ID，按 NEXT_STEPS:119 身份落实原则登记为**待补 [Q6]**，不补造」。
- 身份落实原则（`NEXT_STEPS_20261106.md:119`，逐字）：「责任归属为持有 lead/re_line_20261105/GOAL_RE_CONTINUOUS.md:89 至 :105 所述连续执行职责、可核实原授权与 D-24 的项目负责人来源会话；该会话派任务时须把自己的实际 session/run ID、任务 ID、签发角色写入 N-1 记录及 N-4 任务书。身份未落实是派发阻塞，不是让用户再次授权的一般权限阻塞，亦不能由计划作者冒签。」
- 事实包三值清单（`_fp_N10-C07_Q6.md:12-16`）：①该会话的实际 session/run ID；②任务 ID；③签发角色；并点明「相邻字段惯例：N-1 验收记录格式含 `reviewerSessionId`、`sourceTaskId`」。

### 3.2 N-1 固定字段逐字：实文为九字段，不是八个

`NEXT_STEPS_20261106.md:23`（逐字）：「在 lead/nextstep_plan_20261106/ACCEPTANCE_RECORDS.json 保存验收记录，字段固定为 **itemId、reviewerRole、reviewerSessionId、sourceTaskId、inputHashes、artifactHashes、decision、unresolved、timestamp**，来源会话验收者与作者不得相同。」——**九个固定字段，含 timestamp**。盘上双证：`a_residual_n1_20261108/ACCEPTANCE_RECORDS.json` 的 schemaNote 同口径（本轮 probe 实读），且 7 条记录每条实测恰这 9 键、键序全等（本轮 probe 输出 `[2]`）。**任务书提问口径写「八」与实文差一个 timestamp；按实文 + 盘上 schema 双证取 9。**

### 3.3 判定：字段同一套；角色词汇两套并存

- **字段是同一套**：C07 三值恰好 = N-1 九固定字段中的 `reviewerRole`（第 2 位）、`reviewerSessionId`（第 3 位）、`sourceTaskId`（第 4 位），顺序按 NEXT:23 原序。⇒ 落点载体应复用 `N-1-ACCEPTANCE-RECORDS/2` 形制，**不另造字段体系**（`_c7_SLOT_PREP.md:34` 同判定）。
- **角色词汇是两套，值不得互抄**：`PERF_REPAIR_HANDOFF.md:151` 具名的是 N-11 件**内部**分工（分流员、撰写、独立复核员三角色），**不是**签发角色；拿它们填 `reviewerRole` = 冒签（NEXT:119 明禁「不能由计划作者冒签」）。这是 §5.2 人工判据 9 的依据。

## 4 落点件现盘状态与方案（本轮实跑）

### 4.1 全仓分布（环安全 walk 实跑：dirsVisited=16630，reparse 剪枝 + visited 去重）

全仓 `ACCEPTANCE_RECORDS*` **恰 2 件**；`NEXT:23` 字面路径实测 `exists=False`（probe 输出 `[1]`）：

| 件 | 字节数 | SHA256 |
|---|---|---|
| `lead/a_residual_20261106/ACCEPTANCE_RECORDS.json`（r1） | 37517 | `d421f8bc5cc02eee2a0ea908a60477cdb313541cbff3cfd96a65728528d0efda` |
| `lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json`（r2） | 27965 | `d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b` |

### 4.2 已存在件的结构（本轮 probe 实读）

- **r2**（N-1 r2 件）：顶层 **dict**，13 键 = schema, schemaNote, natureNote, grade, revisionOf, independentReview, replacementNote, reviewer, sourceTask, writeDomain, hashMethod, decisionSemantics, records；schema=`N-1-ACCEPTANCE-RECORDS/2`；grade=`PARTIAL`（自述「本 r2 自身尚未经独立复核」）；records=7 条、每条 9 键且键序全等 FIELDS9；`sourceTaskId` 7 条全 = `N-1`（**计划号**）；`reviewerSessionId` 7/7 在位、唯一值 1 个、形如 `sess_dwf-dwfrun-<UUID>-actor_<n>_<m>`（格式形，值不转录）。
- **r1**（N-1 旧件）：顶层 **list**，17 条；`reviewerSessionId` 缺位 0/17、`sourceTaskId` 缺位 0/17、`reviewerRole` 在位 17/17——即「身份两键缺位」按 sessionId+sourceTaskId 读法成立。
- 两件均为 N-1 主体（W9/W8 文书核对），**无一覆盖 C07 登记主体**（N-11 派发来源会话身份）。

### 4.3 追加还是新建——三案后果对比与推荐

| 案 | 做法 | 后果 | 判定 |
|---|---|---|---|
| A 追加 | 把 C07 记录追加进 r2 | ① 违反 r2 自声明 writeDomain（越写域）；② r2 grade=PARTIAL 且自述未经独立复核，外来条目与待复核内容纠缠；③ 登记主体错位（r2 sourceTask=N-1，C07 主体是 N-11 派发会话） | **否** |
| B 字面新建 | 在 `lead/nextstep_plan_20261106/` 按 NEXT:23 字面路径新建 | 字面合规，但该目录属 N-1 计划件（manifest/check_plan），NEXT:23 该句的登记主体是 W9/W8 文书核对项；事后补建会被误读为 N-1 自己的记录件 | 仅当来源会话为字面合规明确选择 |
| C 独立新建（推荐） | 新建单条登记件（建议名 `ACCEPTANCE_RECORDS_C07.json`），容器 13 键与 9 字段记录格式**照抄** N-1-ACCEPTANCE-RECORDS/2 形制，落来源会话当轮写域 | 零既有件改动；一文件一登记主体；「复用 N-1 载体」落在格式与 schema 上而非物理文件上；填完即过门禁 | **推荐**（模板 `_c7_record_template.json` + 门禁 `_c7_selfcheck.py` 已备于本写域） |

**落点最终指定权在来源会话**（事实包 `_fp_N10-C07_Q6.md:47` ④-4：「落点由来源会话指定」）——本件只定格式与校验。

**填用流程**：① 复制 `_c7_record_template.json` 到落点名 `ACCEPTANCE_RECORDS_C07.json`；② 仅替换 `<…>` 占位符与定档字段（grade/decision/independentReview/writeDomain）；③ `python -I -X utf8 _c7_selfcheck.py <已填件路径>` 须 GATE PASS exit 0；④ 回件含绑定行（§6.2 格式）。

## 5 字段规格表与可追加记录模板 + 多处同步排查表

### 5.1 容器与记录规格

容器 13 键照 r2 形制（模板 `_c7_record_template.json` 实体，键名与顺序一致）；`records` **恰 1 条**、9 字段 **NEXT:23 原序**。逐字段规格（类型/约束/占位符/校验规则）：

| 字段 | 类型/约束 | 占位符（仅此形） | 校验规则（门禁码 + 人工判据） |
|---|---|---|---|
| `itemId` | string，固定值 `N10-C07-Q6-identity` | 无（常量） | H05（9 字段名与顺序 == NEXT:23 实文）；人工：主体不得错位 |
| `reviewerRole` | string 非空 | `<来源会话签发角色>` | H06 非空非拒填值；H07 无占位残留；**人工判据 9（唯一防线）**：不得取 PERF:151 内部三角色冒充签发角色——门禁无此校验（复核负测 D 实证 GATE PASS），须逐字人工比对 |
| `reviewerSessionId` | string 非空 | `<来源会话sessionId>` | H06；H07；H09 不冒用 a_residual 两件任何已登 ID（门禁对照实查）；人工：与来源会话自身运行标识一致（自证） |
| `sourceTaskId` | string 非空 | `<来源会话任务ID>` | H06；H07；H10：值为裸计划号（形如 `N-\d+`）时 `unresolved` 必须非空；人工：不得填计划号且 unresolved 留空（先例教训 YI:90/N4V2:191） |
| `inputHashes` | dict 非空；四件必绑，值为 `64hex/字节数` | `<SHA256/字节数，填时实算>` | H11：门禁对 DQ 件、factpack 件、PERF 件、NEXT 件四路 SHA256+字节数**实算复核**，错一字符即 FAIL |
| `artifactHashes` | dict，登记件填 `{}` | 无 | 无专码（H02/H05 覆盖键位）；承 r2 hashMethod 口径：登记件自身指纹无法内嵌，以验收方复核实算为准 |
| `decision` | string 非空 | 建议 REGISTERED（来源会话定稿） | H07 无占位残留；人工：REGISTERED=行政登记完成，不升格技术结论（模板 decisionSemantics 固定格式值） |
| `unresolved` | list；无缺口 `[]` | 无缺口则置 `[]` | H10 联动；人工：有缺口必须逐条字符串登记，不得留占位 |
| `timestamp` | string，ISO8601 | `<补登时点 ISO8601，来源会话填时实生成>` | H12：`datetime.fromisoformat` 可解析 |

容器级：H01 JSON 可解析、H02 13 键齐、H03 schema 串正确、H04 恰 1 条、H13 容器层（grade/independentReview/reviewer/writeDomain 等）无占位残留。

### 5.2 人工自检清单（门禁之外，10 条）

1. 三个身份字段已填、全件无 `<` 占位残留（含容器层）；2. `reviewerSessionId` 是**本会话**运行态 ID，非他件 ID；3. `sourceTaskId` 若只能给计划号 → `unresolved` 已如实登记「正式任务书编号未落实」；4. 9 字段名与顺序 == NEXT:23 实文 == r2 schemaNote；5. `inputHashes` 四件为填时实算（python -I -X utf8 + hashlib）；6. `timestamp` 为填时实生成；7. 填用过程零改动既有件；8. 回件含绑定行（§6.2 格式）；9. `reviewerRole` 与 PERF:151 内部三角色逐字不同（签发方≠被派方）；10. **多处同步**：同一值已在 N-4 任务书签署动作复用（§5.4），只填登记件不满足 NEXT:119。

### 5.3 门禁行为（本轮实跑复现）

- `--selftest` → `SELFTEST PASS`（对照已登 ID 基数=1），exit 0；
- 未填模板 → `GATE FAIL checks=15 failed=4`（H07/H11/H12/H13），exit 1，绑定行按固定格式输出（`_c7_selfcheck.py:181`）。

### 5.4 多处同步排查表（哪件/哪行/需什么字段/是否已填）

| # | 件 | 行 | 需什么字段 | 是否已填 |
|---|---|---|---|---|
| 1 | `DECISION_QUESTIONS.md`（C07 卡登记面） | :118-122（:120 问题原文、:121 非技术裁决、:122 proposed 待补登） | 三值补登本身；补登后状态行同步（属 N-10 域） | **未填** |
| 2 | `PERF_REPAIR_HANDOFF.md`（N-11 上游） | :151（内部三角色）、**:152（待补 [Q6] 声明）**、:164（Q6 卡源行） | session/run ID、任务 ID、签发角色 | **未填** |
| 3 | `_n4v2_B_EXECUTION_SPEC_V2.md`（N-4 定版件） | **:190** APPROVE_SCOPE 未签署、**:191** 签发人身份未落实、**:192** 任务书编号未落实、**:195** 签署时点 N-1 格式绑定未做；:5/:26 同口径 | 同一签发身份 + APPROVE_SCOPE + 任务书编号 | **未填** |
| 4 | `B_EXECUTION_SPEC.md`（N-4 正式槽位草案） | :6（SPEC_DRAFT 未生效）、**:253**（签署三要件：①矩阵绑定声明 ②T1 确认 ③**以 N-1 记录格式绑定签署时点哈希**；「身份、任一规则或版本缺失则任务书不生效」） | 同 #3（签署动作发生时） | **未填** |
| 5 | `YI_SUPERSEDE_JIA_BINDING.md`（甲乙绑定补登件） | **:87**（APPROVE_SCOPE 未签署，不代签）、**:90**（sourceTaskId 以计划任务号代替、身份核证 unresolved） | 同一签发身份 | **未填** |
| 6 | `OBSERVATION_PROTOCOL_SPEC.md`（协议规格件） | **:306**（「来源会话 session/run ID = 待补（不补造）」）、**:413**（缺口表第 7 行 → N10-C07 待补登动作） | 同三值（登记/状态面） | **未填**（本行系复核轮补收、本件入表） |
| 7 | `a_residual_n1_20261108/ACCEPTANCE_RECORDS.json`（先例件，非 C07 落点） | 7 条 `sourceTaskId` 全 = `N-1`（计划号）；`reviewerSessionId` 已填 | 其自身任务的签发身份（非 C07 主体） | 部分（session 已填、任务号仍计划号——先例与反例） |
| 8 | 两台账 `PENDING_DECISIONS.md` / `GOAL_THREE_TARGETS_20261018.md` | 本轮 grep 实跑：PENDING 零命中；GOAL 仅 :5906 地址常量巧合子串（GOAL:9382 的 Q6 属另一张表的归档行，无关） | ——（C07 未入台账） | 不适用 |

**结论：一次补登、两处落笔**——① C07 登记件（NEXT:119「写入 N-1 记录」）；② 同一值在 N-4 任务书签署动作复用（NEXT:49、N4V2 §6.2-6、草案 :253-③，「及 N-4 任务书」）。只填①不等于 NEXT:119 满足。D-31 对「实际责任身份」的 deferred 项（`RULING_DIRECTION.md:93`「缺输入不编数值、不编身份」）在补登落盘后获得输入。

## 6 复核回件 + 不许代填声明 + 需谁补登 + 未验项

### 6.1 复核回件（如实记；verdict = partial ⇒ **unconfirmed**）

- **复核确认面**（复核轮 14 条命令）：十件基线 10/10 MATCH；全仓恰 2 件；r1/r2 结构与本件 §4.2 一致；NEXT:23 九字段实文与 :119/:49 原文吻合；门禁行为全部复现；其余落点逐行实读吻合；伪造扫描（写域 13 件）零真实身份格式串。
- **破绽一（本件已处置）**：§7 落点清单漏列 `OBSERVATION_PROTOCOL_SPEC.md:306/:413`（同一身份的待补登记面）。处置：本件已收为 §5.4 第 6 行（本轮 Read 实读确认原文）。
- **破绽二（本件披露并以人工判据补强）**：门禁不拦冒签角色——复核负测 D 将 PERF:151 内部角色填入 `reviewerRole` 后 GATE PASS exit 0；15 项校验与 8 条人工清单均无对应校验项。处置：本件 §5.2 第 9 条为唯一防线；门禁脚本本身未改（改之将改变其指纹、使已录绑定行失效，属另立轮次的决定）。
- **本 ask 未重跑项（如实区分）**：复核轮 8 例负测（照抄已登 ID→H09、unknown→H06+H08 等）本轮未重跑；本 ask 实跑 = 指纹 10/10、结构 probe、全仓 walk、台账 grep、门禁两态（§2/§4/§5.3）。

### 6.2 绑定行（本轮实算，格式固定）

被核对象 SHA256 = `084158116dde618cdb0588970305f533f7c6d532aebcc44bb1529d97f2aeabd5`，字节数 = 17233
被核对象 SHA256 = `3d763a8b679370ade8999a23a18679c7296909bf8a020b71694c0ccca7e8b062`，字节数 = 3812
被核对象 SHA256 = `74bec4d48498903df08dbf3a56ba942e74b58f5b4a7940c094eafdeb03adbf2e`，字节数 = 9961
被核对象 SHA256 = `d421f8bc5cc02eee2a0ea908a60477cdb313541cbff3cfd96a65728528d0efda`，字节数 = 37517
被核对象 SHA256 = `d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b`，字节数 = 27965

（前三条 = 本写域三件既有产物，与准备件/复核回件所录绑定行逐字一致，证明其未被本件改动；后两条 = §4 两件记录件。本件 `C07_IDENTITY_SLOT.md` 自身指纹无法内嵌自身，于任务回件中另行给出。）

### 6.3 不许代填声明

三个身份字段（`reviewerSessionId`／`sourceTaskId`／`reviewerRole`）的值**任何他方不得代填**：NEXT:119 原文「本作者不能编造身份」「不能由计划作者冒签」；事实包 `_fp_N10-C07_Q6.md:4`「缺的就是『值』，谁都不能替来源会话编」；门禁自述 `_c7_selfcheck.py:5`「ID 真值真伪由来源会话自证（门禁无法也不应代证）」。本件与模板中出现的全部身份值均为显式占位符，无任何真实 session/run/任务 ID。

### 6.4 需谁补登

**来源会话**（= 派发 N-11 离线分流任务的会话；NEXT:119 责任归属 = 持有 `GOAL_RE_CONTINUOUS.md:89-105` 连续执行职责、可核实原授权与 D-24的**项目负责人来源会话**）本人补登，两处落笔：① 按 §4.3 C 案填 `ACCEPTANCE_RECORDS_C07.json`（或其自指落点）→ 过门禁 exit 0；② 同值用于 N-4 任务书签署（APPROVE_SCOPE + N-1 格式绑定，§5.4 #3/#4）。C07 卡状态行同步（§5.4 #1）与台账登记（#8）分别属 N-10 域与台账维护动作，不属本补登槽位。

### 6.5 未验项（如实登记，不补造）

1. **ID 真值真伪不可由门禁证明**——`_c7_selfcheck.py:5/:182` 自述只验格式/一致性/冒用面；真值由来源会话自证，本件无法代证。
2. **冒签角色门禁缺口**——见 §6.1 破绽二；在门禁增补校验前，§5.2 第 9 条纯靠人工与来源会话自证。
3. **`ROUND_SUBAGENT_LOG_*` 与 `.zcode/` 工作流内部态未查**（同 `_fp_N10-C07_Q6.md:38` 检索边界口径）——其中是否载有 N-11 派发身份未取证据。
4. **全仓计数口径不可比**——本 walk dirsVisited=16630、准备件 walk=16624、编排方 rglob=2460（walk 语义与剪枝不同）；但决定性事实（恰 2 件、同路径、同字节数、同哈希）三种方法一致。
5. **本轮工具链异常自披露**：本会话两次以 Write 生成探针脚本时产物损坏（路径字面量错乱/未定义变量），均已当场删除、未运行、未采信；最终改用内联 `python -I -X utf8` 实跑，写域经 `ls` 复核无遗留坏件，三件既有产物指纹与既有绑定行逐字一致（§6.2）。另外安全钩子（Mimosa）三次拦截含 `open(...,"w")` 的脚本写入——本件探针因此改为纯 print、不落文件，属规避面收敛而非绕过校验。
