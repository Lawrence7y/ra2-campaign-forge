# _c7_SLOT_PREP · C07（N10-C07｜Q6 责任身份落实）补登落点准备件

- 立件：2026-11-09；落点准备员（动态工作流子代理）。**本件只定落点/字段/格式/校验，不填任何身份值。**
- 唯一写域 = `lead/c07_slot_20261109/`；零真机、零采样代码；不改台账、不改任何既有件；未 commit、未 push。
- ★ 占位符纪律：本件与 `_c7_record_template.json` 中全部身份值为显式占位符（形如 `<来源会话sessionId>`）；任何真实 session/run/任务 ID 均不写入本件。现盘先例件的 ID 值只以「格式形」描述、不转录。

---

## 1 第一步结论：C07 要补的三个值，逐字定义

卡面（实读）：`lead/d13d14_cards_20261108/DECISION_QUESTIONS.md:118-122`——
「Q6 | 责任身份落实 | 任务书未载来源会话 session/run ID | NEXT_STEPS:119 身份落实原则 | 来源会话补登实际身份（本件不补造，见 §6.2）」；裁决类型 = **非技术裁决——来源会话身份补登（行政动作）**（:121）；提交通道 = **来源会话直接补登、无需立 D-xx**（:122）。

上游口径（实读）：`lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md:151-152`（§6.2 具名责任；:152 自述「任务书未载来源会话 session/run ID，按 NEXT_STEPS:119 身份落实原则登记为**待补 [Q6]**，不补造」）、`:164`（Q6 卡源行）。
身份原则（实读）：`lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md:119`——「该会话派任务时须把自己的实际 session/run ID、任务 ID、签发角色写入 N-1 记录及 N-4 任务书。身份未落实是派发阻塞，不是让用户再次授权的一般权限阻塞，亦不能由计划作者冒签。」
事实包（实读）：`lead/pending_factpack_20261108/_fp_N10-C07_Q6.md:12-16`（①节三值清单）、`:44-47`（④缺口表，含第 4 项「落点件本身缺」）。

| # | C07 要补的值 | 语义（逐字口径） | 对应 N-1 字段 |
|---|---|---|---|
| 1 | 来源会话**实际 session/run ID** | 派发 N-11 离线分流任务的**那个会话自己**的运行标识（会话 ID 或含工作流 run 的复合 ID，取其运行环境自报者；NEXT:119「实际」= 运行态真值，不得编造） | `reviewerSessionId` |
| 2 | **任务 ID** | 来源会话派发 N-11 分流任务所用的任务标识（正式任务书编号或工作流任务 ID） | `sourceTaskId` |
| 3 | **签发角色** | 来源会话签发任务时的角色。NEXT:119 责任归属 = 持有 `lead/re_line_20261105/GOAL_RE_CONTINUOUS.md:89-105` 连续执行职责、可核实原授权与 D-24 的**项目负责人来源会话** | `reviewerRole` |

⚠ 主体澄清：PERF:151 已具名的「卡顿分流员·GLM／分流报告撰写员／独立复核员」是 N-11 件**内部**角色，**不是**签发角色；拿它们填 `reviewerRole` = 冒签（NEXT:119 明禁）。同样，N-1 r2 记录里已填的会话 ID 属 N-1 核对会话，与 C07 主体（N-11 派发会话）**不同一人格，不得互抄**（格式可参照，值不得照抄）。

## 2 第二步前置：N-1 固定字段实文 = **9 个**（不是 8 个）

`NEXT_STEPS_20261106.md:23` 实文（本轮 Read 逐字）：「在 lead/nextstep_plan_20261106/ACCEPTANCE_RECORDS.json 保存验收记录，字段固定为 **itemId、reviewerRole、reviewerSessionId、sourceTaskId、inputHashes、artifactHashes、decision、unresolved、timestamp**，来源会话验收者与作者不得相同。」——**九个字段，含 timestamp**。
盘上先例同口径：`lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json` 顶层 `schemaNote`（`_c7_probe2.py` 实读输出）：「记录仍为 **9 固定字段且顺序不变**（itemId、reviewerRole、reviewerSessionId、sourceTaskId、inputHashes、artifactHashes、decision、unresolved、timestamp）」；该件 7 条记录每条实测恰这 9 键（probe2 rec[0..6].keys）。
**任务书说「八个」与实文差一个 timestamp，按实文与盘上 schema 双证取 9。**

## 3 两组字段是否同一套 ⇒ 是

C07 三值恰好 = N-1 九字段中的 `reviewerSessionId`、`sourceTaskId`、`reviewerRole` 三个（事实包 `_fp_N10-C07_Q6.md:16` 亦点明此「相邻字段惯例」）。⇒ **落点应复用 N-1 的载体（schema `N-1-ACCEPTANCE-RECORDS/2` 的 9 字段记录格式），不另造字段体系**；差异只在登记主体与容器元数据，不在字段。

## 4 第二步结论：落点件现盘实查（本轮实跑，不采信转述）

实跑命令与输出（脚本均在 `lead/c07_slot_20261109/`，`python -I -X utf8` 运行）：

- **`_c7_probe2.py`**（结构+指纹）：
  - `lead/nextstep_plan_20261106/ACCEPTANCE_RECORDS.json exists = False`——NEXT:23 指定物理路径**不存在**（与事实包 ③-命令④ 一致）。
  - `lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json`：27,965 B / sha256 `d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b`；顶层 = **dict**（非数组），schema=`N-1-ACCEPTANCE-RECORDS/2`；顶层键 = schema, schemaNote, natureNote, grade, revisionOf, independentReview, replacementNote, reviewer, sourceTask, writeDomain, hashMethod, decisionSemantics, records；**records = 7 条**（W9-2/W9-9/W9-19/W8-6/W8-11/W8-8/W8-7），每条 9 键；7 条 `sourceTaskId` 全 = 'N-1'（**计划任务号**）；`reviewerSessionId` 7 条同值、形如 `sess_dwf-dwfrun-<UUID>-actor_<n>_<m>`（格式先例；值不转录）。
  - `lead/a_residual_20261106/ACCEPTANCE_RECORDS.json`：37,517 B / sha256 `d421f8bc5cc02eee2a0ea908a60477cdb313541cbff3cfd96a65728528d0efda`；顶层 = **list**（r1 旧制）；其替代关系由 r2 件 `replacementNote` 收口（旧 17 条身份两键缺位，仅作历史链保留）。
  - 编排方 10 件指纹复算：**10/10 MATCH**。
- **`_c7_probe3.py`**（全仓查找，环安全 walk、follow_symlinks=False、实环剪枝 1195、dirsVisited=16624、耗时 12.7s；首轮 `_c7_probe1.py` 无环剪枝撞目录环超时作废——如实记录）：全仓**恰 2 件** ACCEPTANCE_RECORDS.json，路径与字节数与编排方 rglob 一致：
  1. `lead/a_residual_20261106/ACCEPTANCE_RECORDS.json`（37,517 B）
  2. `lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json`（27,965 B）
- **`_c7_probe4.py` / `_c7_probe5.py`**（登记面）：两件台账 **无 C07/Q6 登记行**（GOAL:9382 的 Q6 是另一张表的「except_post_* 归档」行、无关；PENDING 仅 :28 以 DQ 件作 D-13 同步行证据）。

**事实修正（如实）**：背景所称「补登落点件 ACCEPTANCE_RECORDS.json 现不存在」仅对 **NEXT:23 字面路径**成立；仓内另有 2 件同名文件（均在 a_residual 域、均为 N-1 主体），**没有任何一件覆盖 C07 的登记主体**——C07 的落点件确实需要新建。

### 4.1 追加 vs 新建——两法后果与推荐

| 方案 | 后果 | 判定 |
|---|---|---|
| A. 追加进 `lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json` | ① 违反该件自declared `writeDomain`（唯一写域=该目录两件，属 N-1 r2 任务）；② 该件 `replacementNote` 已把 9 条替代面收口、`grade=PARTIAL` 且自述「本 r2 自身尚未经独立复核」——再追加会让外来条目与待复核内容纠缠；③ 登记主体错位：该件 sourceTask=N-1、验收者=N-1 r2 会话，C07 主体是 N-11 派发会话 | **否** |
| B. 在 `lead/nextstep_plan_20261106/` 新建（NEXT:23 字面路径） | 字面合规，但该目录属 N-1 计划件（manifest/check_plan），N-1 记录实际已落 a_residual_* 域；事后补建会被误读为 N-1 自己的记录件（NEXT:23 该句的登记主体是 W9/W8 文书核对项） | 不推荐（除非来源会话为字面合规明确选择） |
| C. **新建独立单条登记件**，容器与记录格式照抄 `N-1-ACCEPTANCE-RECORDS/2`，落来源会话当轮写域（模板已备于本写域 `_c7_record_template.json`） | 零既有件改动；主体单一（一文件一登记主体）；「复用 N-1 载体」落在格式与 schema 上而非物理文件上；来源会话填完即用，门禁 `_c7_selfcheck.py` 可验 | **推荐** |

落点最终指定权在来源会话（事实包 ④-4：「落点由来源会话指定」）——本准备件交付的是**格式、占位模板与门禁**，写域由来源会话填用时落定（建议：本写域就地复制填用，或来源会话自指新写域）。

## 5 第三步：三个身份字段规格表

> 通用规则（三字段共用）：① 值只能由**来源会话本人**填（NEXT:119「不能由计划作者冒签」）；② 不得出现尖括号占位残留；③ 不得照抄盘上任何他件已登 ID（防冒用）；④ 填后须过 `_c7_selfcheck.py`（exit 0）。

| 字段 | 类型 | 取值约束 | 示例占位符（仅此形，绝不写成看似真实的 ID） | 通过判据 | 失败判据 |
|---|---|---|---|---|---|
| `reviewerSessionId` | string，非空 | 来源会话运行态自报标识。盘上格式先例：`sess_dwf-dwfrun-<UUID>-actor_<n>_<m>` 形（`lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json` 实读，值不转录）；其他运行环境取其实际标识 | `<来源会话sessionId>` | 非空；无占位残留；与来源会话自身运行标识一致（来源会话自证）；不等于 a_residual 两件内任何已登会话 ID（门禁脚本对照实查） | 空 / `unknown` / `N/A` / `TODO` / `待补`；照抄他件 ID；自造非运行态 UUID |
| `sourceTaskId` | string，非空 | 来源会话派发 N-11 任务的**实际任务标识**。**教训**：先例以计划号 'N-1' 填此键，被 `lead/b2b_yi_supersede_20261108/YI_SUPERSEDE_JIA_BINDING.md:90` 与 `lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md:191` 登记为「sourceTaskId 以计划任务号代替、身份核证 unresolved」——计划号≠任务 ID | `<来源会话任务ID>` | 非空；无占位残留；若确无正式任务编号、只能给计划号（如 'N-11'），必须**同时**在 `unresolved` 逐条登记「正式任务书编号未落实，暂以计划号代替」 | 空；填计划号且 `unresolved` 留空（= 重蹈 :90 缺陷）；占位残留 |
| `reviewerRole` | string，非空 | 来源会话**签发**角色（NEXT:119 责任归属口径：项目负责人来源会话）。具名惯例参照 PERF:151「角色名·模型（上下文说明）」形 | `<来源会话签发角色>` | 非空；无占位残留；明确可区分于 N-11 件内部分流/撰写/复核角色（签发方≠被派方） | 空；照抄 PERF:151 内部角色冒充签发角色；占位残留 |

其余六字段（非身份，简规格）：`itemId` 固定 `N10-C07-Q6-identity`；`inputHashes` 至少实算绑定四件引用链（DQ 件、`_fp_N10-C07_Q6.md`、`PERF_REPAIR_HANDOFF.md`、`NEXT_STEPS_20261106.md`，门禁强制复算）；`artifactHashes` 记 `{}`（登记件自身指纹无法内嵌，承 r2 `hashMethod` 口径「以验收方复核实算为准」）；`decision` 建议「REGISTERED——来源会话身份补登完成（Q6 行政动作，非技术裁决，不升格技术结论）」由来源会话定稿；`unresolved` 无缺口 = `[]`，有缺口逐条字符串；`timestamp` ISO8601（填时实生成）。

## 6 第四步：模板与自检

- **模板**：`_c7_record_template.json`（同目录）——容器 13 键照 r2 形制（schema/schemaNote/natureNote/grade/revisionOf/independentReview/replacementNote/reviewer/sourceTask/writeDomain/hashMethod/decisionSemantics/records），`records` 恰 1 条、9 字段**原序**、值全部为 `<…>` 占位符或显式标注「（固定格式值，照抄）」的格式常量（schema 串、性质声明等非身份值）。
- **填法**：复制模板 → 目标落点文件名建议 `ACCEPTANCE_RECORDS_C07.json` → 仅替换占位符与定档字段 → 跑门禁。
- **门禁**：`_c7_selfcheck.py`——`python -I -X utf8 _c7_selfcheck.py <已填文件路径>`；硬校验 = JSON 可解析 / schema 正确 / 恰 1 条记录 / 9 字段名与顺序一致 / 三身份字段+timestamp+decision 无占位残留 / `reviewerSessionId` 不与 a_residual 两件任何已登 ID 相同 / `sourceTaskId` 为计划号时 `unresolved` 必须非空 / `inputHashes` 四件 SHA256+字节数实算复核 / `timestamp` ISO8601 可解析；输出含被核文件绑定行。**ID 真值真伪由来源会话自证，门禁只验格式与冒用面**（真值只有来源会话知道）。
- **人工自检清单（8 条）**：
  1. 三个身份字段已填、全件无 `<` 占位残留；
  2. `reviewerSessionId` 是**本会话**运行态 ID，非他件 ID；
  3. `sourceTaskId` 若只能给计划号 → `unresolved` 已如实登记；
  4. 9 字段名与顺序 == NEXT:23 实文 == r2 schemaNote；
  5. `inputHashes` 四件为填时实算（python -I -X utf8 + hashlib），与门禁复算一致；
  6. `timestamp` 为填时实生成 ISO8601；
  7. 填用过程零改动既有件（git status 仅新增本写域/来源写域新件）；
  8. 回件含绑定行：`被核对象 SHA256 = `+64 位 hex+`` ` ``，`，字节数 = n`（SHA256 三字之后直接 = 与反引号，中间无路径/括号/空格）。

## 7 第五步：同一身份还在哪些地方需要（逐处实读清单）

| # | 件 | 行 | 需要什么身份 | 是否已填 |
|---|---|---|---|---|
| 1 | C07 卡登记面 `lead/d13d14_cards_20261108/DECISION_QUESTIONS.md` | :118-122（:122 状态行「proposed（待补登动作）」） | 三值补登本身；补登完成后状态行同步 | **未填**（卡面即待补登记；DQ 件属 N-10 域，本准备不改） |
| 2 | N-11 上游自述 `lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md` | :151（具名三角色）、**:152（待补 [Q6] 声明）**、:164（Q6 卡源行） | 来源会话 session/run ID、任务 ID、签发角色 | **未填**（自述不补造，等补登） |
| 3 | N-4 任务书定版件 `lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md` | **:190**（APPROVE_SCOPE 未签署，属来源会话任务签发人）、**:191**（签发人身份未落实——sourceTaskId 以计划任务号代替、unresolved）、**:192**（任务书编号未落实）、**:195**（签署时点 N-1 格式绑定未做）；:5/:26 同口径 | 来源会话任务签发人身份 + APPROVE_SCOPE 签署 + 任务书编号 | **未填**（生效条件 §6.2 六项缺四项身份/编号/绑定面） |
| 4 | N-4 正式槽位（草案）`lead/bexec_n4_20261108/B_EXECUTION_SPEC.md` | :6（SPEC_DRAFT 未生效，占 N-4:47 槽位）、**:253**（签署三要件：①矩阵绑定声明 ②T1 确认 ③**以 N-1 记录格式绑定签署时点哈希**；「身份、任一规则或版本缺失则任务书不生效」） | 同 #3（签署动作发生时） | **未填** |
| 5 | 甲乙绑定补登件 `lead/b2b_yi_supersede_20261108/YI_SUPERSEDE_JIA_BINDING.md` | **:87**（APPROVE_SCOPE 未签署——属来源会话任务签发人，本件不代签）、**:90**（N-1 验收记录 sourceTaskId 以计划任务号代替、身份核证登记 unresolved） | 同一来源会话签发身份 | **未填**（登记而非放行，自述边界） |
| 6 | N-1 验收记录（先例件，非 C07 落点）`lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json` | 7 条记录 `sourceTaskId` 全 = 'N-1'（计划号）；`reviewerSessionId` 已填（N-1 r2 会话） | 其**自身**任务的签发身份（非 C07 主体） | 部分（session 已填、任务号仍计划号——先例缺陷，C07 填写须避免重蹈） |
| 7 | 台账 `lead/PENDING_DECISIONS.md` / `lead/GOAL_THREE_TARGETS_20261018.md` | 检索无 C07/Q6/N-10 卡行（`_c7_probe4.py`；PENDING:28 仅 D-13 同步行引 DQ 件） | ——（C07 未入台账；补登后如需状态同步属台账维护动作，不属本补登槽位） | 不适用 |

**结论：一次补登、两处落笔。** 三个值一旦由来源会话确定：① 填入 C07 登记件（本模板，NEXT:119「写入 N-1 记录」）；② 同一值在 N-4 任务书签署动作中复用（APPROVE_SCOPE + N-1 格式绑定，NEXT:49 / N4V2 §6.2-6 / 草案 :253-③，NEXT:119「及 N-4 任务书」）。两处是**同一身份的两次登记，不是两套身份**；只填①不等于 NEXT:119 满足。D-31 对「实际责任身份」的 deferred 项（`lead/direction_ruling_20261108/RULING_DIRECTION.md:93`「缺输入不编数值、不编身份」）在补登落盘后即获得其输入。

## 8 本件命令与产物指纹

实跑命令（本轮全部 `python -I -X utf8` + 绝对路径；脚本与输出留本写域）：
1. `_c7_probe1.py` —— 全仓朴素 walk，**超时作废**（撞目录环，未采信）；
2. `_c7_probe2.py` —— N-1 两件结构 + NEXT 路径存在性 + 编排方 10 件指纹复算（10/10 MATCH）；
3. `_c7_probe3.py` → `_c7_probe3_out.txt` —— 环安全全仓查找，恰 2 件；
4. `_c7_probe4.py` —— 台账 C07/Q6/身份检索（两台账零登记行）；
5. `_c7_probe5.py` —— 草案任务书身份槽位 + 台账 N-10/N-11 登记面检索；
6. `_c7_selfcheck.py` 对**未填模板**自测（预期 FAIL，验门禁有效性）。

产物三件：本件、`_c7_record_template.json`、`_c7_selfcheck.py`（指纹见回件绑定行）。
