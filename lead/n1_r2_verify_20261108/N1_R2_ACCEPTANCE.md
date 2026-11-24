# N-1 r2 交付验收报告（N1_R2_ACCEPTANCE · 2026-11-08）

- 撰写会话 = `sess_dwf-dwfrun-01a1190d-62d0-4b75-b05b-4044a79a82be-actor_3_1`（本轮 env 实跑：`ZCODE_SESSION_ID` = `CLAUDE_SESSION_ID` = `CLAUDE_CODE_SESSION_ID` 三变量一致；会话串为编排方运行标签，属声明非密码学凭据，与被验收件 JSON:48 `identityVerifiability` 登记同口径）。
- 角色链：r2 作者 = actor_3_1@dwfrun-324c613e（自称）；独立验收员 = actor_1_1@dwfrun-01a1190d（ranCommands=25）；独立复核员 = actor_2_1@dwfrun-01a1190d（ranCommands=12）；本报告撰写 = actor_3_1@dwfrun-01a1190d——与前三者互为不同会话（验收者 ≠ 作者成立；三方会话串本身均为声明，非可核证凭据）。
- 铁律遵守：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写任何钩子/转储/跨进程读写类代码，具体接口名依 r2 MD:13 同款口径不展开）；既有件一律只读（含被验收两件，未代修）；唯一写域 = `lead/n1_r2_verify_20261108/`；未 commit、未 push。
- 证据口径：指纹一律本轮 `python -I -X utf8` + hashlib 实算；引用一律「文件:行」或「本轮实跑命令 → 输出」；验收员/复核员已跑而本轮未重跑的项，以 `_v_evidence_log.txt` #01–#25（本轮全读）与验收/复核回件为据，未验面如实写「未验」。

## 1 目的与被验收对象

1. **目的**：对 N-1 r2 两件交付（作者会话自称 `sess_dwf-dwfrun-324c613e-fb0e-42f5-9883-805fef5b80de-actor_3_1`，MD:5 / JSON:46）的独立验收成果（验收员 actor_1_1，整体 decision=PARTIAL，`_v_verify_report.md`）及其复核（复核员 actor_2_1，verdict=confirmed）做收口归档：把**绑定锚 / 身份 / 替代关系**三缺口的闭合判定、九字段清单齐备性、decision 分布与未验面写成一份可联引的验收报告。任务依据 = `lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md:21-27`（逐项 ACCEPT/REJECT/PARTIAL 并绑定输入与交付 SHA256；身份或版本未填不得视为放行；PARTIAL 不提升技术结论）。
2. **被验收对象**：`lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md`（33,431 B）与 `lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json`（27,965 B）；辅助件 `_n1_records.py`（11,968 B，r1 时代遗留、未被 r2 修改）。
3. **作者「未经独立复核」自报（照录）**：MD:160「本 r2 自身尚未经独立复核（验收者≠作者由编排方另派）；验收完成前本件不作为放行凭据（`NEXT_STEPS_20261106.md:25`）」；MD:166 grade=PARTIAL 不评 COMPLETE；JSON:49 distinctFromAuthor 同旨；JSON 顶层 grade 同载。作者会话串仅见于其自述，无法从交付件独立核证签发人真实性（JSON:48 登记 unresolved；r1 同类声明已被证实与落盘机制不符——`_n1_records.py:13` 硬编码 `sess_dwf-dwfrun-324c613e-…-actor_1_1`，脚本内 `rg -n "environ|getenv"` 零命中 exit=1，本轮复跑）。本报告即为该验收环节的收口件。

## 2 被验收件实算指纹与版本锚

**本轮 hashlib 实算（`python -I -X utf8 -c` 内联，逐件 sha256+字节数）：**

| 件 | SHA256 | 字节数 | 判定 |
|---|---|---|---|
| `lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md` | `1209ca4c8149722fffd1731a0f435637a2988a6e90993f87ef632eb4763b585e` | 33,431 | 与编排方指纹 / 验收回件绑定行（`_v_verify_report.md:10`）/ 复核回件逐位一致（MATCH） |
| `lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json` | `d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b` | 27,965 | MATCH |
| `lead/a_residual_n1_20261108/_n1_records.py` | `b089d809d6a7ae9f729fdbaa1437ef8613d4512ce1e257c50154fdf3de005275` | 11,968 | MATCH |
| `lead/a_residual_20261106/ACCEPTANCE_RECORDS.json`（旧件） | `d421f8bc5cc02eee2a0ea908a60477cdb313541cbff3cfd96a65728528d0efda` | 37,517 | 与 r2 MD:18 一致 |
| `NEXT_STEPS_20261106.md` / `A1_ERRATA_MAP.md` / `ERRATA_W8.md` | `c364467d…` / `d0097994…` / `660a9ece…` | 27,225 / 48,180 / 28,443 | 与编排方指纹一致（MATCH×3） |

**绑定锚（本轮实跑）：**

- JSON→现盘 MD 绑定存在：`rg -c "1209ca4c" ACCEPTANCE_RECORDS.json` = **8**（7 条 artifactHashes + writeDomain JSON:52 一处）；JSON 全部 inputHashes+artifactHashes 共 56 条对现盘逐一复算 **0 不符**（程序化实跑）。
- **★ r1 指纹已消失（版本锚事实）**：r1 两件（MD `3343cfbe…4125`/26,435 B + JSON `15e4731c…d420`/18,045 B，载于 MD:4/:130、JSON:16/:29/:240）被 r2 **就地覆盖且无独立副本**（MD:159 自认「无独立副本留存」）；目录 `ls -la` 实读仅存 r2 版。r1 MD 指纹旁证 = `_n1_records_out.txt:9`（mtime 11-08 10:04，r1 时代运行摘要：MD 指纹同值 + r1 决策分布 W8-7=ACCEPT）；**r1 JSON 指纹无独立 trace**。本轮追加重构复算：现盘 r1 生成器 `_n1_records.py` 实跑（stdout 18,045 B，恰 = r1 JSON 字节数）产出 r1 型内容（schema=`N-1-ACCEPTANCE-RECORDS/1`、W8-7 decision=ACCEPT、replacementNote 无 R3、sessionIdSource=「运行环境实读…」式、无 grade/revisionOf/independentReview 顶层键、writeDomain 无指纹串），将其中现盘 MD 指纹串替换回 r1 MD 指纹串后 SHA256 = `ec455e1f…2b79` ≠ `15e4731c…`（另试 MD+PD 双串替换 = `259ceb2e…` 亦不命中；PD mtime 2026-11-07 13:58 早于 r1 窗口，双替换假设不成立）→ **r1 JSON 指纹经此途径不可复算**，验收「不可复算」登记维持成立并获本轮负结果佐证。
- **★ r2 无自身绑定行（版本锚事实）**：r2 MD 全文 **0 次**出现现盘两件指纹（`rg -c "1209ca4c|d847de88" A_RESIDUAL_REFERENCES.md` → exit=1，0 命中）；r2 JSON 自身指纹物理不可内嵌（hashMethod JSON:53 明示「以验收方复核实算为准」）→ 现盘两件的绑定闭环依赖外部回件：验收回件绑定行（`_v_verify_report.md:10-12`）+ 本报告 §2 本节。
- mtime 佐证：被验收两件 mtime = 11-08 10:47:51 / 10:50:56，早于验收员产出 11:17–11:23；旧目录 `lead/a_residual_20261106/` 全部 Nov 6（r2 窗口前未动）。

## 3 逐项验收

### 3.1 九字段清单齐备性（本轮程序化实读）

- 计划契约原文（`NEXT_STEPS_20261106.md:23`）：「字段固定为 itemId、reviewerRole、reviewerSessionId、sourceTaskId、inputHashes、artifactHashes、decision、unresolved、timestamp」。实读 7/7 条记录键序恰为该九字段、顺序一致；7/7 `reviewerSessionId` = `sess_dwf-dwfrun-324c613e-…-actor_3_1`、7/7 `sourceTaskId` = `"N-1"`、7/7 `timestamp` = `2026-11-08T10:48:01+08:00`。
- 命名注记：验收任务书用语 **acceptanceId** 在盘无对应键（`rg -n "acceptanceId" ACCEPTANCE_RECORDS.json` → exit=1），盘上条目 ID 字段实名 = **itemId**（计划契约原文即 itemId，`rg -c '"itemId"'` = 7）。两者为同一槽位的命名差，登记为命名注记，非缺字段。
- `unresolved`：7/7 条各含「身份核证 unresolved（独立复核破绽②）」条与「sourceTaskId 按计划任务号 N-1」缺口条（程序化 7/7 True）；W8-7 另含 decision 变更记录照录 r1 原值（JSON:240）。拼写备查：验收/复核文字作 identityVerability，盘上键实名 = `identityVerifiability`（JSON:48，keys() 实读）。

### 3.2 decision 分布（程序化 Counter 实跑）

- **ACCEPT×5**（W9-2 / W9-19 / W8-6 / W8-11 / W8-8）+ **PARTIAL×2**（W9-9：PD 版本时刻标注未落实 + PD 现盘再漂移，MD:150；W8-7：被修原句定位未验，MD:111/:115）+ REJECT×0。W8-7 由 r1 ACCEPT 依复核破绽③如实下调 PARTIAL（JSON:236/:240 照录 r1 原值），与上游判定档 `ERRATA_W8.md:124`（PARTIAL，行锚 PASS）同档——无 ACCEPT 化拔高。

### 3.3 三缺口闭合判定

- **缺口① 绑定锚错位 → 部分闭合（PARTIAL）**：r2 MD 无自绑行 + JSON 自身指纹不可内嵌 + r1 指纹不可复算（§2 两条★）→ 凭据自含完备性 residue 在案；JSON→MD 绑定 8 处与实算一致、外部回件绑定行补齐闭环。判 PARTIAL 如实、未拔高为 ACCEPT。
- **缺口② 身份硬编码 → 已闭合（登记层面）**：r1 缺陷在盘属实（`_n1_records.py:13` 硬编码 actor_1_1 会话 + `:195` 仍称「运行环境实读」+ rg 零命中，本轮复跑）；r2 已更正——JSON:47 sessionIdSource 改可复现命令+输出式、JSON:48 identityVerifiability 登记 unresolved 并照录 r1 缺陷、7/7 记录含身份核证条。残留 = 作者 env 输出固有不可由交付件复现；采信复核回件 (d)：此为**登记层面闭合**，非核证层面闭合。
- **缺口③ 替代关系 → 已闭合**：9 条同域替代收口（JSON:43 + MD §6.2 表 9 行一致）；旧件 17 条两键整体缺位实读在案；其余 8 条主题不同保留原状（与旧件 decisions 实读一致）。细则见 §4。

### 3.4 行锚断言与 grep/sed 复跑（本轮实跑）

- `python -I -X utf8 _v_line_checks.py` → **PASS=57 FAIL=14 / TOTAL=71**（与验收 #23、复核回件一致）；14 项 FAIL 甄别：13 项为关键词格式差而实际行支持 r2 引用（本轮补验：W9:151 实含 `qc151_trip.py:4561-4578`/`4575` 守卫、A1:97 实为「:155, :156, :157, :230」、A1:144/145/146 行首②③④、EW:52「通吃」实际在 :53 等），**1 项为 r2 引用精度瑕疵**——MD:111 将短语「PARTIAL（被修原文定位未验）」并挂 `ERRATA_W8.md:121` 与 `A1_ERRATA_MAP.md:285`，`rg -n` 该短语在两文件仅命中 A1:285（EW:121 实读为「修订表述（引用限定句）」，无该字样）→ 瑕疵属实，登记不代修。
- 指定 grep/sed 复跑（本轮实跑）：`sed -n '198p' W8_STATIC_LOCATE.md` 清单无 W8-6/8/7/11 落点；`rg -in 740B51` 在 `F7_TARGETING.md` 与 `_w8_f7_out.txt` 均 0 命中 exit=1；目录级 `fn 0x740B51` 恰 2 处（W8:178 自引 + `reviews/F7_review.md:193`）；全目录 740B51 恰 5 处 = `ERRATA_W8.md:120` 记载；`_f7rev_out.txt:433-434` = `00740b50 c3 ret` / `00740b51 90 nop`；W8:177 / W8:185 各单命中。全数支持 r2 记载。

## 4 替代关系核查

- **旧件基线（本轮 python 实读）**：`lead/a_residual_20261106/ACCEPTANCE_RECORDS.json` = 17 条（type=list），per-record 键集 13 个、**无 reviewerSessionId/sourceTaskId 键**（整体缺位，非空值）；R3-W8-7 decision=PARTIAL、R3-W8-8 decision=ACCEPT 在列；旧件哈希 `d421f8bc…efda`/37,517 B 与 r2 MD:18 一致。
- **R3-W8-7／R3-W8-8 是否补全：是（登记层面闭合）**。r1 仅把 7 条 R1/R2 列为替代对象、R3 两条被归入「保留原状」且无排除理由（r1 破绽①）；r2 JSON:43 replacementNote 增列两条并给出纳入理由（「r1 遗漏……排除无据故纳入替代」），MD §6.2:182-183 同旨；同主题新旧凭据并存的替代边界在登记层面收口。
- **主题等同核实（本轮归一化实跑：剥离行首列表编号/行内反引号/加粗星号后比对 + difflib）**：R2-W8-6 vs W8:177、R2-W8-7 vs W8:178、R2-W8-8 vs W8:179、R2-W8-11 vs W8:185 归一化逐字相等（True×4）；R3-W8-7 vs W8:178、R3-W8-8 vs W8:179 归一化后仍各差一处——W8 行含「（小）」而旧 R3 originalClaim 无 → r2「逐字同句」（JSON:43、MD §6.2:182-183）对这两行不成立。此为复核回件 (b) 新登记，本轮独立复现成立。叠加 schema 事实：新记录九字段中无 originalClaim 字段（声称文本载体 = MD §3/§4 逐字引文），JSON:43 该措辞属精度残留，不影响替代收口与主题等同判定。
- **其余 8 条**（R2-W8-1/2/3/4/5/9/10/12）：旧件实读 decisions 与主题均为 W8-1/2/3/4/5/9/10/12，与 7 条新记录不同题，保留原状——与 JSON:43 / MD:185 一致。

## 5 复核回件

- 复核会话 = actor_2_1@dwfrun-01a1190d（编排方另派，与验收员、作者非同一会话）；复核产出三件（本轮 hashlib 复算，全 MATCH）：`_v_verify_report.md` = `b0e2e274fd4bced4bde17577ea68af46a97b500df4909f9e68e9194c97b8d1c3` / 9,145 B；`_v_evidence_log.txt` = `6ab5f2e6bef6669d24947f9d2ea189130ab0d13d8ad1a284bd94236f8d9b271f` / 7,479 B；`_v_line_checks.py` = `eb7c32f1cb6ca11090701031ac458959178d6201b6dc69bc9988088e6e05b006` / 4,422 B。
- 复核绑定行（照录；被核对象 = 验收员主产出，本轮 hashlib 实算复现同值）：

  **被核对象 SHA256 = b0e2e274fd4bced4bde17577ea68af46a97b500df4909f9e68e9194c97b8d1c3，字节数 = 9145**（主产出 = `lead/n1_r2_verify_20261108/_v_verify_report.md`）

- 复核 **verdict = confirmed**（按「refuted/partial 标 unconfirmed」规则，本回件 verdict=confirmed，故不作 unconfirmed 标注）。复核结论：验收员 5 项指定复核全数通过、未发现拔高；验收 decision=PARTIAL、缺口①=部分闭合、W8-7 下调均维持。
- 复核新增登记（a）–（e）与本轮复现状态：
  - (a) 会崩条件（三指纹任一不符 / 缺口①被记 ACCEPT / 被验收件被改）均未发生——本轮实算/实读同证。
  - (b) 验收证据日志 #09 对 R3 两行的差异描述不完整（漏「（小）」）——本轮 difflib 复现成立（§4）。
  - (c) 域内无 r2 JSON 生成器——本轮实跑复现：`_n1_records.py`（r1 生成器）产出 r1 型 JSON（§2），与现盘 /2 JSON 在 schema、W8-7 decision、replacementNote、sessionIdSource、unresolved 条数（4 vs 5/6）、writeDomain 有无指纹串等多处不同 → r2 JSON 正文无域内生成轨迹，仅哈希可程序复算。
  - (d) 缺口②「已闭合」系登记层面而非核证层面——采信，§3.3 已按此措辞。
  - (e) 任何粘贴的会话串都是声明而非凭据——本报告 env 实跑亦证（本会话 actor_3_1@01a1190d ≠ 验收员自报 actor_1_1@01a1190d ≠ 复核员 actor_2_1 ≠ 作者自称 actor_3_1@324c613e）。
- 复核未验项（照录，本报告维持未验）：验收员 #19 特定会话串；r1 两件全文（本轮追加重构复算仍不命中，§2）；QC124 运行期事件（零真机）；PD 现盘逐行内容（本轮仅指纹链核对与 os.stat 50,194 B）。
- 覆盖声明：验收员 25 条命令中，本报告撰写会话实跑复现其中指纹 3 件、rg×5、行锚脚本 1 件、结构校验、旧件实读、grep/sed 10 项、env 1 项；其余以 `_v_evidence_log.txt` #01–#25（本轮全读）与验收/复核回件为据，未逐条重跑，如实计入未验面。

## 6 结论

- **整体 decision = PARTIAL**（验收员判定，复核 verdict=confirmed 确认，本报告维持不改）：九字段清单齐备（条目 ID 实名 itemId，acceptanceId 为任务书同槽命名注记）；decision = 5 ACCEPT + 2 PARTIAL + 0 REJECT；三缺口判定 = ①绑定锚**部分闭合** ②身份**已闭合（登记层面）** ③**替代关系已闭合**；1 处引用精度瑕疵（MD:111）与复核新增「（小）」精度残留均已登记、未代修；W8-7 由 r1 ACCEPT 如实下调 PARTIAL 且 r1 原值照录（JSON:240），无拔高。
- **能否作放行凭据：不能单独作为放行凭据。** 依据：①作者自报验收完成前不作放行凭据（MD:160、JSON:49）；②身份核证 unresolved 固有在案（JSON:48，会话标签非密码学凭据，作者 env 输出不可复现）；③sourceTaskId 为代用值 N-1（编排方未下发独立任务书编号，7/7 登记）；④绑定锚缺口①部分闭合（r1 指纹不可复算、r2 MD 无自绑行、JSON 自身指纹域内无绑定点）；⑤「身份或版本未填不得视为放行、PARTIAL 不提升技术结论」（`NEXT_STEPS_20261106.md:25/:27`）。可作「N-1 引用凭据登记已经一轮独立验收且复核 confirmed」的**文书层**凭据供后续联引；任何技术命题均未因此获得放行或升格，5 条 ACCEPT 语义 = 凭据登记核对通过（decisionSemantics JSON:54）。
- **未验项（汇总，如实未验、不补造）**：作者会话 env 输出（固有不可复现）；r1 MD/JSON 全文（r1 MD 旁证仅 `_n1_records_out.txt:9`，r1 JSON 仅字节数+决策分布旁证且重构复算不命中）；QC124 运行期事件（零真机）；PD 现盘逐行内容；验收员/复核员自报会话串（声明）；W9 其余 17 条、W8 其余 6 条、W7/G5 各条（按 N-1 联引条款不重查，`NEXT_STEPS_20261106.md:25`）。
- 本报告自身：写域内新增 = 本件 + 探针产物 `_v_r1gen_probe_out.txt` / `_v_r1gen_probe_err.txt`（复核点 (c) 与 r1 重构复算的证据件）；被验收件与全部既有件零改动（本会话首轮与成稿后各实算指纹一次，两件逐位一致，见落盘后末次实算记录）；未 commit、未 push；零真机、零采样代码。本报告自身指纹不内嵌（同 hashMethod JSON:53 物理约束），绑定由提交回执承载。
