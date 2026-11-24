# N-1 r2 独立验收回件（验收员：GLM，全新会话，与作者 actor_3_1 非同一会话）

- 验收对象：`lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md` 与 `lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json`（作者 sess_dwf-dwfrun-324c613e-…-actor_3_1）
- 任务依据：`lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md:21-27`（逐项 ACCEPT/REJECT/PARTIAL + 绑定输入与交付 SHA256；身份或版本未填不得视为放行；PARTIAL 不提升技术结论）
- 实跑证据日志：`_v_evidence_log.txt`（本目录，#01–#25）；行锚断言脚本：`_v_line_checks.py`
- 铁律遵守：零真机、零采样代码、未 commit、未 push、未改被验收件与任何既有件；唯一写域 = `lead/n1_r2_verify_20261108/`。

## 被核对象绑定行（本轮 hashlib 实算，#01）

**被核对象 = lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md，SHA256 = 1209ca4c8149722fffd1731a0f435637a2988a6e90993f87ef632eb4763b585e，字节数 = 33431**

**被核对象 = lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json，SHA256 = d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b，字节数 = 27965**

辅助件：`_n1_records.py` SHA256 = b089d809d6a7ae9f729fdbaa1437ef8613d4512ce1e257c50154fdf3de005275 / 11,968 B（r1 时代遗留，本轮未改）。

三件与编排方指纹逐位一致（MATCH×3）。

## 一、交付指纹与绑定核对（任务 1）

- 三件实算与编排方指纹一致（#01）。
- r2 JSON `inputHashes` 7 件上游输入与 #06 实算逐键一致；7 条记录 `artifactHashes` 均绑定现盘 MD = `1209ca4c…/33431B`（#20），与 #01 一致。
- r1 锚（MD:4 = `3343cfbe…/26,435 B` + `15e4731c…/18,045 B`；MD:130 = 复核回件照录行）标注如实（「就地替代同目录 r1」「覆写前 hashlib 实算」），非误标。r1 MD 指纹有 r1 时代旁证：`_n1_records_out.txt:9`（mtime 10:04，#22）留有同值；r1 JSON 指纹无 trace；两件全文无独立副本（MD:159 自认）→ 不可复算。

## 二、JSON 结构校验（任务 2）

程序化校验（#20）：records = 7；每条恰 9 固定字段且顺序 = `[itemId, reviewerRole, reviewerSessionId, sourceTaskId, inputHashes, artifactHashes, decision, unresolved, timestamp]`；timestamp 格式合规；哈希格式合规。

- **decision 分布 = ACCEPT 5（W9-2/W9-19/W8-6/W8-11/W8-8）+ PARTIAL 2（W9-9/W8-7）+ REJECT 0**。W8-7 由 r1 ACCEPT 依复核破绽③下调为 PARTIAL（JSON:236/:240 照录 r1 原值），与上游判定档（`ERRATA_W8.md:124` = PARTIAL，#23 PASS）同档。
- **unresolved 登记**：每条均含①「身份核证 unresolved（独立复核破绽②）…不视为放行凭据」与②「编排方未随任务下发独立任务书编号，sourceTaskId 按计划任务号 N-1 填写」两类缺口条（7/7 计数通过，#20），另如实登记各条核对面与 grade=PARTIAL 自评（JSON:5）。
- 顶层 `grade = PARTIAL`、`revisionOf`（r1 两件指纹+无副本声明）、`independentReview`（verdict=partial、三破绽、disposition）结构与 MD §5 一致。

## 三、三缺口逐项判定（任务 3）

### 缺口① 绑定锚错位 —— 判定：**部分闭合**

实算确认（#01/#04/#05）：

- 现盘 MD = `1209ca4c…/33,431 B`、JSON = `d847de88…/27,965 B`；MD:4 与 :130 所载为 r1 值（3343cfbe…/26,435；15e4731c…/18,045），标注为 r1 锚，无冒充。
- r2 MD 全文 **0 次**出现现盘两件指纹（rg exit=1）→「MD 无指向自身的绑定行」属实。
- 但 JSON 侧存在指向现盘 MD 的绑定：7 条 `artifactHashes` + `writeDomain`（JSON:52）共 8 处 `1209ca4c…/33431B`，与实算一致；JSON `hashMethod`（:53）明示「ACCEPTANCE_RECORDS.json 自身指纹无法内嵌，以验收方复核实算为准」。
- 本回件上方绑定行完成现盘两件的外部绑定（即该机制设计的最后一环）。

为何非 ACCEPT：①r1 两件被就地覆盖且无独立副本（MD:159 自认），其指纹作为版本锚永久不可复算（旁证仅 `_n1_records_out.txt:9`，且 r1 JSON 指纹无 trace）；②JSON 自身指纹在域内无绑定点（物理约束 + 已登记，但凭据链完备性因此依赖外部回件）；③MD 侧无任何现盘自绑行。三点合计，凭据自含完备性存在已登记、部分不可闭合的 residue → 记 PARTIAL（与被验收件自评 grade=PARTIAL 同向，不构成对内容的否证）。

### 缺口② 身份硬编码 —— 判定：**已闭合**

- 实读 `_n1_records.py:13`：`SESSION_ID = "sess_dwf-dwfrun-324c613e-…-actor_1_1"` = 硬编码字面量（r1 作者会话）；`rg -n "environ|getenv"` 该脚本 0 命中 exit=1（#03）；`:195` 仍写「运行环境实读 ZCODE_SESSION_ID」→ r1 缺陷在盘属实。
- r2 是否更正：**已更正**。r2 JSON `reviewer.sessionIdSource`（:47）= 可复现命令+输出式（env | rg 三变量一致 = …actor_3_1）；`identityVerifiability`（:48）= 登记 unresolved「会话标识非密码学凭据、无法从交付件独立核证签发人真实性」并照录 r1 缺陷（`_n1_records.py:13` 硬编码、rg 零命中）；7 条记录 unresolved 各含身份核证条（#20）。r2 未再以与落盘机制矛盾的「实读」声明作凭据。
- 机制核实（#19）：验收员会话实跑同形命令，三变量存在且会话内一致，证明机制真实、且验收员会话 ≠ r1 作者会话 ≠ r2 作者自称会话（验收者≠作者）。
- 残留：作者 env 输出本身不可由交付件复现（固有）——r2 已按 `NEXT_STEPS_20261106.md:25` 登记为 unresolved 并声明不作放行凭据，属如实处理而非缺陷。r1 脚本文本在盘不改（写域限制两件，MD:14），由 r2 照录隔离。

### 缺口③ 替代关系 —— 判定：**已闭合**

- 旧件实读（#07/#08）：`lead/a_residual_20261106/ACCEPTANCE_RECORDS.json` = 17 条；`R3-W8-7`（decision=PARTIAL）、`R3-W8-8`（ACCEPT）在列；17 条 `reviewerSessionId`/`sourceTaskId` 两键整体缺位（键列表不存在）；旧件哈希 = `d421f8bc…/37,517 B` 与 r2 MD:18 一致；旧目录 mtime 全部 Nov 6（r2 窗口前未动）。
- r2 JSON `replacementNote`（:43）已收口为 **9 条同域替代**（R1-W9-2/9/19 + R2-W8-6/7/8/11 + R3-W8-7/R3-W8-8），给出纳入 R3 两条的理由（r1 未列亦未说明排除理由，同主题新旧并存属替代边界未闭合，故纳入）与其余 8 条（R2-W8-1/2/3/4/5/9/10/12）主题不同、保留原状的说明；MD §6.2 逐条表与之一致。
- 主题等同核实（#09）：旧 6 条相关 originalClaim 与 `W8_STATIC_LOCATE.md:177/:178/:179/:185` 句文一致（逐字同句在剥离列表编号/行内反引号/加粗星号后成立）；其余 8 条 originalClaim 实读确为 W8-1/2/3/4/5/9/10/12 主题，与 7 条新记录不同题。
- 精度注记（不改变闭合）：r2 称「逐字同句」，复核破绽①原文「逐字近似」更准（markdown 标记差异在案，#09）。

## 四、内容抽核（支撑性）

- 复跑 r2 自报 grep/sed 证据 10 项全中（#10–#18、#25）：W9:193/:210 单命中、W8:177/:185 单命中、:198 清单 0 命中、F7_TARGETING.md 与 _w8_f7_out.txt 的 740B51 零命中、目录级「fn 0x740B51」仅 2 处、全目录大小写不敏感恰 5 处（= ERRATA_W8.md:120 记载）、`_f7rev_out.txt:433-434` 字节证据（ret/nop）。
- 71 项行锚断言（#23/#24）：57 PASS；14 FAIL 经全文甄别，13 项为检查关键词格式差而实际行支持 r2 引用，1 项为 r2 引用精度瑕疵——r2 MD:111 将短语「PARTIAL（被修原文定位未验）」并挂 `ERRATA_W8.md:121` 与 `A1_ERRATA_MAP.md:285`，实读该短语逐字仅在 A1:285，EW:121 为规则正文。登记不代修。
- 未验/未跑项照 r2 维持：PD 现盘仅验指纹未逐行重查；W9/W8 其余条目联引不重查；QC124 运行期事件零真机未复现；作者会话 env 输出不可复现核证（详见证据日志末节）。

## 五、整体结论（任务 4）

**整体 decision = PARTIAL。**

- 依据：缺口①部分闭合（凭据自含完备性 residue：r1 指纹不可复算、JSON 自身指纹域内无绑定点、MD 无现盘自绑行）；缺口②③已闭合；7 条 decision 中 2 条 PARTIAL（W9-9、W8-7）与全部 unresolved 如实在案。
- **不可作为放行凭据**：本件性质为文书核对与引用凭据登记（JSON natureNote/decisionSemantics 自证），PARTIAL 不提升技术结论、文书核对≠根因确认（`NEXT_STEPS_20261106.md:25,:27`）；身份核证 unresolved 固有存在。本回件完成后，两件可作为「N-1 引用凭据登记已经一轮独立复核」的**文书层**凭据使用；W9-9/W8-7 的 PARTIAL、五条 ACCEPT 的「仅指凭据登记核对通过」语义、及全部 unresolved 维持原样，任何技术命题均未因此获得放行或升格。
- r2 三破绽处置（§5.2/JSON independentReview.disposition）经本轮实算复核成立：9 条替代收口属实、sessionIdSource 改命令式+unresolved 登记属实、W8-7 decision 下调与 r1 原值照录属实。
