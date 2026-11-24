# GATE_REJUDGE_32.md — 32 域门禁判据逐域真伪重判（交付件）

- 唯一写域 `lead/gate_rejudge32_20261109/`；本件文件名不带 `_rj_` 前缀，系【交付】指定名；其余本会话产物一律 `_rj_` 前缀。
- 底稿 `_rj_findings.md`（29796 B，SHA256 `8be23bc2096b87f623b4c24df8a673897f0bcf2536557da26cc7d436d45fa5f2`）已由复核方判 **verdict=partial → 本件如实标 unconfirmed**；复核三处破绽见 §4(d)、§5(c)、§6。
- 零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）、零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 hashlib。

---

## 1 目的与边界（只重判不改件）

目的：对 32 个已交付写域的门禁判据逐域做真伪重判，分清「交付件真有缺口」与「门禁尺子本身报错」，给出修正后的账和 36 处改造件的补遗建议。**只重判，不改任何已交付件**——判定「误报」的绝不去删那份交付件里的词，那是掩盖证据。

边界（实读/实跑）：
- 上游只读件：32 个写域全部件、`lead/gate_doc_name_fix_20261109/`、`lead/gate_fp7_20261108/_g7_predicates.py`、`lead/gate_r9r12_20261109/_g9_gate.py`、`.zcode/workflow-runs/` 全部 mjs（历史 payload 绝对不改）、`lead/PENDING_DECISIONS.md` 与 `lead/GOAL_THREE_TARGETS_20261018.md`。本会话对它们全部只读（§6 有现值复算）。
- 唯一写域：`lead/gate_rejudge32_20261109/`。不 commit、不 push（实跑 `git -C D:\Project\ra2-campaign-forge rev-parse HEAD` → `26574589aa8401e8f3f2934680a1ea7109bafa2d`，与任务开始时一致）。
- 引用口径：只采「本次会话实跑命令 + 输出」或「文件:行」；拿不到的一律写「未验」，不补造。逐字原句由本会话实跑导出 `lead/gate_rejudge32_20261109/_rj_delivery_quotes.txt`（13 域 69 行全量）与 `_rj_context_dump_out.txt`（355 行，含行号/命中位置/语境）双份留证，下表逐域引用其行号。
- 语境类标尺：**A 检索动作 / B 小节标题 / C 否定式 / D 真断言**（任务书四档）；本轮另实证一类 R9-R12 库外的**语用语境缺口**（条件分支/清单格/判定档），§5 记为 E，属于补遗而非改写原四类。非断言词命中（缺要素、绑定行）标注「A–D 不适用」。
- 复核 verdict 如实记：前一轮【复核】判 `partial`（`"verdict":"partial"`，任务书原文），按本任务【交付】「refuted 或 partial 标 unconfirmed」→ **unconfirmed**。其成立部分（七件指纹、13/6 数字、9 域误报抽验、8 条真问题相对字面判据、判不了项、越界检查）作为本件证据链复用；其两处 FAIL（片段不可自洽、「真剩 4 域」无实跑支撑）在本件 §4/§5 用本会话新实跑补正，不隐去。

---

## 2 上游指纹（七件）+ 32 域基线复核

### 2.1 七件指纹（本会话 hashlib 实算 7/7 相符）

实跑 `python -I -X utf8 -c "<内联 hashlib 循环>"`（绝对路径 + `pathlib.Path.read_bytes()`），逐行输出：

```
OK lead/gate_doc_name_fix_20261109/_dn_regate_out.json sha=0d129e409ca5ab744891abccd85a0c0ca0c164ddea8620de634de5079fa8f096 bytes=22133 sizeOK=True
OK lead/gate_doc_name_fix_20261109/GATE_DOC_NAME_FIX.md sha=a1006e06836e902ec462186676ef66c4d6301ab8aee58234c05add9b946c46cd bytes=41361 sizeOK=True
OK lead/gate_fp7_20261108/_g7_predicates.py sha=02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120 bytes=11743 sizeOK=True
OK lead/gate_r9r12_20261109/_g9_gate.py sha=a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6 bytes=11623 sizeOK=True
OK lead/r33e_merge_20261109/_re_linked.py sha=7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52 bytes=19481 sizeOK=True
OK lead/PENDING_DECISIONS.md sha=3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 bytes=52419 sizeOK=True
OK lead/GOAL_THREE_TARGETS_20261018.md sha=2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede bytes=759518 sizeOK=True
```

与【编排方指纹】七个常量逐字节一致。另实跑 `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_r9r12_20261109\_g9_gate.py > …\_rj_delivery_g9_selftest_out.txt` → exit=0，`"all_pass": true`（U1/U2/U3，`U3` 自报谓词指纹 `02c17e49…c51120/11743 B`），落 `_rj_delivery_g9_selftest_out.txt`。

### 2.2 32 域基线复核（自己重跑，不采信编排方数字）

实跑：
```
python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_doc_name_fix_20261109\_dn_regate_domains.py > D:\Project\ra2-campaign-forge\lead\gate_rejudge32_20261109\_rj_delivery_baseline.json 2> …\_rj_delivery_baseline.err
```
→ `exit=0`、`stderr bytes 0`；重算输出 `fresh bytes 22133 sha 0d129e409ca5ab744891abccd85a0c0ca0c164ddea8620de634de5079fa8f096` —— 与已交付 `_dn_regate_out.json` **逐字节同一**，不是漂移。

| 口径 | 本会话实测 | 编排方口径 | 对照 |
|:--|--:|--:|:--|
| 域总数 | **32 域** | 32 域 | 一致 |
| gateProblems 非空 | **13 域** | **10 域** | 不符；`GATE_DOC_NAME_FIX.md:242` 自述「13 个提示域」并枚举同一清单 |
| 问题条目总数 | **24 条** | — | 13 域逐条见 §3 |
| bindings=0 | **6 域** | **5 域** | 不符，见 §4(c) |
| 编排方 REJUDGE_CODE 的 `bindingLines(SHA256)==0` | 3 域（逐字复刻 `_rj_orchestrator_replay.py`） | — | 6 / 3 / 3 三种口径均不是 5 |

**「10 域」集合对齐：未验。** 任务书只给「10 个域」数字、未给枚举；我实测 6 种口径（含断言 7、含绑定行 6、含缺要素 6、断言∪绑定 9、排除纯缺要素 9、问题条目 24）都得不出 10，故按 13 域全量逐域给判定，不猜集合。任务书必现要素中的「10 域」在此登记为「编排方口径 / 未验」。

### 2.3 双轨差异（朴素 vs 谓词化）

实跑 `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_rejudge32_20261109\_rj_double_track.py > …\_rj_delivery_double_track_stdout.txt` → exit=0，输出：

```
pred_sha256=02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120/11743B baseline_sha256=0d129e40…f096 domains=32
with_banned_list=30  hit_on_any_track=7
  lead/c07_slot_20261109/                  naiveP=1 r10P=5 r12P=0 r10W=1 occ=6
  lead/c07_truth_protocol_20261109/        naiveP=1 r10P=2 r12P=0 r10W=1 occ=3
  lead/ledger_appendix_20261108/           naiveP=1 r10P=0 r12P=0 r10W=3 occ=3
  lead/matrix_ab_ruling_20261109/          naiveP=3 r10P=0 r12P=0 r10W=3 occ=3
  lead/n10c04_ruling_20261108/             naiveP=2 r10P=0 r12P=0 r10W=5 occ=5
  lead/n4_yi_final_20261108/               naiveP=2 r10P=0 r12P=0 r10W=5 occ=5
  lead/s604_script_hunt_20261109/          naiveP=1 r10P=1 r12P=0 r10W=0 occ=1
wrote …\_rj_double_track_out.json
r12_nonzero_domains []
r10_hits_total 26
```

**双轨数字与编排方完全一致**：30 域有 banned 词表、7 域任一轨命中、`R12` 全域 0（实读 `_g7_predicates.py:134-148` 的 `r12_scan`；本会话独立复核 `r12_all_zero=true`）。**朴素与谓词的差异数 = 6 域**（4 域朴素多报被 R10 全豁免：ledger_appendix / matrix_ab_ruling / n10c04_ruling / n4_yi_final；2 域 R10 比朴素报得多：c07_slot 1→5、c07_truth_protocol 1→2），另 1 域 s604_script_hunt 两轨一致（1/1）。合计朴素 11 条（按 token）、R10 8 条（按出现）、R10 豁免 18 处、命中 26 处。

提取器假象根因（实读）：`_dn_regate_domains.py:22` `BIND_RE = re.compile(r"re\.findall\((r'[^']+')")`、`:76` `m = BIND_RE.search(src)` 只取 GATE_CODE 里**第一个** `re.findall(`，`:97-100` 用它算 `nb`；`:93-95` 是朴素 `for bad … if bad in t`。本会话 `_rj_delivery_verify.py` 用各域 GATE_CODE 里真实的 `B=len(re.findall(...))` 复算 6 个 bindings=0 域（§4(c) 表）。

---

## 3 逐域真伪判定表（13 域 / 24 条 gateProblems）

下表每处给：域 / 主件 / 命中词 / 行号 / **逐字原句**（长句为保持逐字，按 `_rj_delivery_quotes.txt` 同行的原样节录，节录处标 `…`；完整原句见该件对应行）/ A-B-C-D 语境类 / 真伪 / 依据。语境依据写的是「该词出现在什么句子里、为什么不是断言」，不以「件里说不该报」代替。

| # | 域 / 主件 | 命中词 / 行号 / 逐字原句 | 类 | 真伪 | 依据（语境 + 实跑/实读） |
|--:|:--|:--|:-:|:-:|:--|
| 1 | `lead/c07_gate_audit_20261109/` / `C07_SELFCHECK_AUDIT.md` | 缺要素 `未改 _c7_selfcheck.py`；L17「1. 未改 `_c7_selfcheck.py` 一字（撰写会话始末两轮 hashlib 实算指纹均为 74bec4d4…/9961 B，见 §2.1 与 §5）；」；L239「本撰写会话未修改任何既有文件。…**未改 `_c7_selfcheck.py` 一字**，未改模板，未改 SLOT_PREP/C07_SLOT/事实包/D13D14 卡片/两台账。」 | A–D 不适用（R9 包裹符） | **误报** | 两句都是否定式「未改门禁」的自我声明；反引号把 token `未改 _c7_selfcheck.py` 拆成 `未改 \`_c7_selfcheck.py\``。实跑 `_rj_r9r11_check.py` → `raw=False r9_present=True layer=normalized`（`_g7_predicates.py:31-53` 的 `r9_normalize` 先删反引号跨度再换包裹符）；复核方 `_rjv_step3_out.json` 独立复算同值。删词反而抹掉任务书要求的声明。 |
| 2 | `lead/c07_protocol_attacks_20261109/` / `PROTOCOL_ATTACK_TEST.md` | 缺绑定行；L8「被核对象 SHA256 = 68395681bbfd6b348a91664ec8c0dfafe1b9aa22a939691d0683414071f96547，字节数 = 25630」；L102「被核对象 SHA256 = 4a2f0e860179e4dfd58d26535f09b327481831e31baa2757604b91fb0f1a38e7，字节数 = 20048」 | A–D 不适用 | **误报** | 严格相邻格式绑定行 2 条在场。基线 `bindingRegex='sess_[A-Za-z0-9]{24,}'`（`_rj_context_dump_out.txt` 该域首段）是伪造 ID 扫描，不是绑定行；`_rj_delivery_verify.py` 从该域 GATE_CODE 取真实 `B=len(re.findall(r'被核对象 SHA256 = [0-9a-fA-F]{64}',t))` → `real_B=2 strict=2`。R11 回验 2 bindings / 0 problems。 |
| 3 | `lead/c07_slot_20261109/` / `C07_IDENTITY_SLOT.md` | `已填`；L79「**填用流程**：① 复制 `_c7_record_template.json` 到落点名 `ACCEPTANCE_RECORDS_C07.json`；② 仅替换 `<…>` 占位符与定档字段（grade/decision/independentReview/writeDomain）；③ `python -I -X utf8 _c7_selfcheck.py <已填件路径>` 须 GATE PASS exit 0；④ 回件含绑定行（§6.2 格式）。」 | A（命令占位符） | **误报** | 「<已填件路径>」是尖括号占位符，句子是「填用流程」的命令示例，不宣告任何身份值已填；`_rj_double_track_out.json` 该处 `kind=assertion` 是 R10 逐出现扫描的新误报。 |
| 4 | 同上 | `已填`；L103「1. 三个身份字段已填、全件无 `<` 占位残留（含容器层）；2. `reviewerSessionId` 是**本会话**运行态 ID，非他件 ID；3. `sourceTaskId` 若只能给计划号 → `unresolved` 已如实登记「正式任务书编号未落实」；…10. **多处同步**：同一值已在 N-4 任务书签署动作复用（§5.4），只填登记件不满足 NEXT:119。」 | E（自检清单条文；A–D 无对应） | **误报** | 同一行 10 条编号，是 §5.2「人工自检清单」的**验收条件**（将来填用后才检查），不是完成体陈述；全件 L114-119 六行排查表逐行记「**未填**」（如 L114「\| 1 \| \`DECISION_QUESTIONS.md\`（C07 卡登记面） \| … \| **未填** \|」）。R10 把它当 assertion，属语用语境缺口。 |
| 5 | 同上 | `已填`；L110「### 5.4 多处同步排查表（哪件/哪行/需什么字段/是否已填）」 | **B 小节标题** | **误报** | 行首 `###` 的标题，且是「**是否**已填」的提问式——任务书第五步原句「列出「哪件、哪一行、需要什么身份字段、是否已填」」、【交付】§5 原句「多处同步排查表（哪件/哪行/需什么字段/是否已填）」自己要求写该词（实跑 `_rj_final_checks.py` 输出 `(1) 任务书自相矛盾检查` 逐字打印）。删词即抹掉任务书要求的证据。 |
| 6 | 同上 | `已填`；L112「\| # \| 件 \| 行 \| 需什么字段 \| 是否已填 \|」 | **B 表格表头** | **误报** | Markdown 表列头「是否已填」，是待填列名，不是状态值；紧随 L114-119 六行全为「**未填**」。 |
| 7 | 同上 | `已填` ×2；L120「\| 7 \| \`a_residual_n1_20261108/ACCEPTANCE_RECORDS.json\`（先例件，非 C07 落点） \| 7 条 \`sourceTaskId\` 全 = \`N-1\`（计划号）；\`reviewerSessionId\` 已填 \| 其自身任务的签发身份（非 C07 主体） \| 部分（session 已填、任务号仍计划号——先例与反例） \|」 | A（先例件引述） | **误报** ×2 | 句子明写「先例件，非 C07 落点」「其自身任务」「先例与反例」，说的是**他件**的状态，不是本域身份已补登。附：第二处被 R10 以回看窗内「（先例件，**非** C07 落点）」的「非」判 `negation` 豁免——**理由错、结论对**（否定词不支配该 token，见 `_g7_predicates.py:69-70` 的 `NEG_RE`/24 字窗）。 |
| 8 | 同上 | 缺绑定行；L136「被核对象 SHA256 = \`084158116dde618cdb0588970305f533f7c6d532aebcc44bb1529d97f2aeabd5\`，字节数 = 17233」、L137/L138/L139/L140 同式（5 条） | A–D 不适用 | **误报** | 任务书【交付】§6 明写「绑定行格式：被核对象 SHA256 = \`hex\`，字节数 = n」——**要求反引号**，5 条字面全合规；本任务铁律禁反引号是跨任务书格式不统一，不是该件的错。`_rj_delivery_verify.py` 取真实 `B=len(re.findall(r'SHA256\s*=\s*`[0-9a-fA-F]{64}`',t))` → `real_B=5`（`strict_adjacent_count=0` 因反引号，非缺失）。R11 5 bindings / 0 problems。 |
| 9 | `lead/c07_truth_protocol_20261109/` / `C07_TRUTH_SELF_PROOF.md` | `已填`；L151「- 处置：已填 → 见证同为声明、非密码学证明，但其价值在独立性（记账方 ≠ 值的主张方，满足 NEXT:23「验收者与作者不得相同」）与可交叉检索性——伪造从「单方改文本」变成「两方合谋 + 两处可互查痕迹」；未填且缺席声明如实 → 通过档不可达，登记最高 PARTIAL + unresolved「运行标识无独立见证/独立记载」。」 | E（条件分支标签；A–D 无对应） | **误报** | 「已填 → …；未填且… → …」是协议状态机的**两个分支标签**，句子讨论的是「若已填该判什么」，不是「本件已填」；L6 逐字「- 本件不含任何真实身份值：reviewerSessionId / sourceTaskId / reviewerRole 三值全文只以「S1 / S2 / S3」与占位符指称；文中全部 SHA256 为文件指纹（非身份值），均由本会话实算（\`_tsp_fp_check.py\`）。」自证未填。 |
| 10 | 同上 | `已填`；L228「\| G 见证与两处落笔 \| 3 \| 见证槽已填（见证人≠来源会话≠核验者）；见证缺席处置；两处落笔同值复用 \| 代填见证→**拒绝**；N-4 同值复用失败→**拒绝** \|」 | E（可核项清单格） | **误报** | 表格「可核项 G」的**待核条目**（后接「拒绝」判定），是核验清单要检查的条件；同件 L6 明写不含真实身份值。 |
| 11 | 同上 | `已填`；L240「\| **通过** \| A-G 全部可核项 PASS、无未验残留、（G1 见证已填 或 S1 有 ≥1 处先于补登的外部独立记载）、无存疑项 \| C07 行政登记完成（Q6 补登动作闭合）；不升格技术结论、不构成 APPROVE_SCOPE 签署或 N-5 放行 \|」 | E（判定档条件表达式） | **误报** | 「通过档」的**成立条件**之一，是「或」连接的二择一条件，不是既成事实。附：该处被 R10 因「**无**未验残留」「**无**存疑项」的「无」判 `negation` 豁免——**理由错、结论对**（同 #7 的假豁免）。另实测 `\b或\b` 在 CJK 夹字语境不命中（`_rj_delivery_verify_out.json.cjk_or_b`：`见证已填或S1有记载:false`），故不能拿 `\b或\b` 做判据，见 §5(c)。 |
| 12 | 同上 | 缺绑定行；L29/L33/L37/L41/L45/L49/L53/L57/L61/L65/L69/L75/L79/L83/L182 共 15 条，例 L29「被核对象 SHA256 = fd1ada2fc74afb0fb2aefa9443c45f7ac2c9371594ff60ad39729be5767de4cf，字节数 = 25770」 | A–D 不适用 | **误报** | 基线 `bindingRegex='sess_[A-Za-z0-9]{20,}'` 是伪造 ID 扫描；`_rj_delivery_verify.py` 真实正则 → `real_B=15 strict=15`。R11 15 bindings / 0 problems。 |
| 13 | `lead/ledger_appendix_20261108/` / `LEDGER_APPENDIX_DRAFT.md` | `已生效`；L146「  2. \`RULING_DIRECTION.md\` 整体状态 **unconfirmed**（:5、:77 本会话亲读）——**登记 ≠ 绑定生效**：草案正文明写「不宣告 N-4 正式绑定已生效」（否定句）。」 | **C 否定式**（短引证跨度） | **误报** | 「不宣告 N-4 正式绑定已生效」是否定句，且在「…」引证跨度内报告该否定句；主句是「登记 ≠ 绑定生效」「整体状态 unconfirmed」。R10 判 `negation`，正确豁免。 |
| 14 | 同上 | `已生效`；L177「- **引用限定（本会话如实登记两点，引用本节者须连带）**：① YI §1「裁决原文（Q1 摘录）」引文在裁决书中 grep（…）= **0 逐字命中**——…② RULING_DIRECTION.md 整体状态 **unconfirmed**（:5/:77），…——**本节登记「以乙替代甲」是登记动作，不宣告 N-4 正式绑定已生效**（与补登件自述一致）。」 | **C 否定式** | **误报** | 「本节登记…是登记动作，**不宣告** N-4 正式绑定已生效」；件首自述「只出草案、台账只由 Leader 追加」。完整原句见 `_rj_delivery_quotes.txt` 该行（445 字符未删节）。 |
| 15 | 同上 | `已生效`；L194「  6. 四草案 + SUMMARY 越权词族 grep 唯一命中 = 草案 4 正文否定句「不宣告 N-4 正式绑定已生效」，无正面完成时断言；」 | **A 检索动作**（grep 检索报告） | **误报** | 句子是「grep 唯一命中 = …否定句」的检索结果逐字引证，末句「无正面完成时断言」；描述的是检索动作命中了什么词，不是宣告生效。 |
| 16 | 同上 | 缺绑定行；L186「- **被核对象绑定**：被核对象 = 核对回件文本（复核会话收件逐字转写、UTF-8 无尾换行、存本写域 \`_lv_subject_reply.txt\`）——**SHA256 = \`6888379ac7297758fdbdf4f839b417cd68cc19e1213a030c61606754f8c63227\`，字节数 = 5592**（复核轮绑定行转录；本会话撰写轮对 \`_lv_subject_reply.txt\` hashlib 实算**同值**）。」 | A–D 不适用 | **真问题（格式类）** | 任务书要求「被核对象 SHA256 = <64位>，字节数 = <n>」严格相邻；此处「被核对象」与「SHA256 =」之间插入长括注与破折号，hex 带反引号 → 严格格式 0 条（复核方 `_rjv_step4_out.json.r11_true_problem_domains`：`strict_adjacent:0`）。语义绑定在场：`_rj_r9r11_out.json` R11 `path='_lv_subject_reply.txt' match=True bytes=5592`，本会话实跑确认该锚文件在场且 5592 B。**若判据迁 R11 则自动消解、无需改件**。 |
| 17 | `lead/matrix_ab_ruling_20261109/` / `RULING_MATRIX_AB.md` | 缺要素 `需谁批准`；L108「### 5.2 可执行改动清单（★ 处方，未实施；批准人一律 = **乙设计责任人**，pf2:200；改后立即做登记 7/8，顺序不可倒）」、L138「若批准人不采随批：B 核心仍成立，但 **W2 必须在台账如实登记为未关闭**，不得声称已关闭。」 | A–D 不适用（措辞变体） | **真问题（字面措辞）** | 任务书【交付】§5「…需谁批准…」+ 必现要素字面串 `需谁批准`；全文 `需谁`/`谁批准` 0 命中（本会话 `_rj_context_dump_out.txt` 该域 elem 列表实读）。语义（批准人 = 乙设计责任人）完整在场，但 `r9_element_present` raw 与归一化文本双缺（`_rj_final_checks.py` → `缺要素 需谁批准（R9：raw 与包裹归一化文本双缺）`）。属任务书把语义要求写成字面 token。 |
| 18 | 同上 | `已改矩阵` / `已收紧` / `已施行`；L4「- 性质：**只裁决、不施行**。本件通篇为方案与处方，不含任何「已改矩阵 / 已收紧 / 已施行」既成事实断言；全部被核件零改动（§2.1 指纹逐一与编排方基线一致即证）。」 | **C 否定式** + 短引证跨度 | **误报 ×3** | 三词同处一行，被「**不含任何**…既成事实断言」否定、且落在「…」短引证跨度内；`_rj_double_track_out.json` 三处 `kind=negation in_span=True`。句子是「本件不含该断言」的自我限定，不是断言。 |
| 19 | `lead/matrix_reach_20261109/` / `MATRIX_DEFECT_REACHABILITY.md` | 缺要素 `实跑输出`；L65「- **构造输入 → 实跑返回**：classify 直调，pre 八变体（None/{}/缺state/脏值/显式unknown/absent_confirmed/present/error）× read_error 两型（exists=None / exists=True），16/16 格实跑：」；L74「- **落哪一行 / 与矩阵声称是否一致**：…（16/16，out:159-174；复核 45 格全表中 18 个 read_error 格全部 PRE，R:112）。…」；L26 逐条实跑命令 | A–D 不适用（措辞变体） | **真问题（字面措辞）** | 任务书（dwfrun-c482b235）「要给出**实跑输出**」+ 必现要素 `实跑输出`；全文 0 命中，用的是 `实跑返回` / `out:159-174` / L26 的 `PROBE_DONE` 输出索引。语义在场而 R9 双缺（`_rj_final_checks.py` → `缺要素 实跑输出（R9：raw 与包裹归一化文本双缺）`）。 |
| 20 | `lead/n10c04_ruling_20261108/` / `RULING_STATIC_ORDER.md` | `授实施权` / `解除 PAUSE`；L5「            本裁决只定次序与写域：不授实施权、不解除 D-13 PAUSE、不代签 APPROVE_SCOPE、」；L44「2. **不授实施权**：T1-T4 的实施以来源会话任务书为准；任务书未发 = 不实施。」；L348「- 意见要点：全文未见「授实施权/解除 PAUSE/应用母本」类越权断言（R:5-6/:231-233/:244-252 均为禁止或」；L425「1. 本件**不授实施权**：T1-T4 实施以来源会话任务书（含写域、身份、纪律条款）为准；任务书未发 = 不实施。」 | **C 否定式** ×4 + **A 检索动作** ×1 | **误报 ×2**（按 2 条问题条目） | 5 处命中全在「不授实施权」「不解除 D-13 PAUSE」「全文未见…类越权断言」的否定/复核检索语境；R10 五处全豁免（`r10W=5`）。任务书本身要求「不授实施权、不解除 PAUSE」出现在边界声明里。 |
| 21 | `lead/n11_wording_fix_20261108/` / `N11_WORDING_FIX.md` | 缺要素 `改前改后`；L76「## 4 订正草案（改前/改后逐处对照）」；L81「- 【改前】本件按 **13 项分写**，与裁决列名一一对应，无缺漏、无新增：拆分只改颗粒度、不改内容。」；L82「- 【改后】本件按 **13 项分写**，与裁决列名逐项对应（其中「帧数/重复性/阈值论证」一项拆为 D-08/D-09/D-10 三维，故 11 项列名展开为 13 维），无缺漏、无新增：拆分只改颗粒度、不改内容。」 | A–D 不适用（斜杠变体） | **真问题（字面措辞）** | 任务书（dwfrun-65d9f3a9）必现要素 `改前改后`；件用「改前/改后」+【改前】【改后】逐处对照完整在场，`改前改后` 0 命中，R9 双缺。 |
| 22 | `lead/n4_yi_final_20261108/` / `CANDIDATE_RESIGN_YES_V2.md` | 缺要素 `不签 APPROVE_SCOPE`；L15「1. **不签 \`APPROVE_SCOPE\`**——该签署属来源会话签发人（N-4 原文 \`NEXT_STEPS_20261106.md:49\` 验收条款：「独立审阅者签候选 YES、来源会话签发人签 APPROVE_SCOPE」，本轮实读）。」；L150「**性质限定（越权断言排除声明）**：本 YES **不签 \`APPROVE_SCOPE\`**（属来源会话签发人）；…」 | A–D 不适用（R9 包裹符） | **误报** | 反引号把 token 拆断；两句都是否定式边界声明「不签 APPROVE_SCOPE」。`_rj_r9r11_out.json`：`raw=False r9_present=True layer=normalized`；复核方独立复算同值。 |
| 23 | 同上 | `可应用母本` / `放行 N-5`；L17「3. **不放行 N-5**——N-5 需有权来源会话派发新任务书（N-4 原文 :53-58，本轮实读）。」；L130「- **翻案条款（复核回件原文）**：若上述任一实体件（母本/候选/矩阵/V2/台账）指纹漂移、或矩阵↔V2↔实码三方出现取值分叉、或回件出现「可应用/放行 N-5」断言，本 confirmed 即翻。」；L150「**性质限定（越权断言排除声明）**：本 YES **不签 \`APPROVE_SCOPE\`**（属来源会话签发人）；**不应用母本**（母本指纹 517889c6…/399,508 本轮零改动）；**不放行 N-5**；不断言运行时行为、整趟行为或崩溃修复效果；不签真机验收。…」；L155「3. **无越权断言**：审阅/复核回件不出现「可应用母本 / 放行 N-5 / APPROVE_SCOPE 已签」类断言；」 | **C 否定式** ×4 + 短引证/条件式 ×1 | **误报 ×2** | 5 处命中全在「不放行 N-5」「不应用母本」「不出现…类断言」「翻案条款（若…即翻）」的否定/条件/引证语境；R10 全豁免（4 `negation` + 1 `quote_mention`，`r10W=5`）。 |
| 24 | 同上 | 缺绑定行；L122「**被核对象（审阅回件 \`lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md\`）SHA256 = \`ee27b4caf4faa7920b602636bc0f43c1a265554fe6354659c59323fc11e3102e\`，字节数 = 11948**——复核回件绑定值，撰写员本轮 hashlib 实算相符（\`_rw_fpcheck\` MATCH 行）。」 | A–D 不适用 | **真问题（格式类）** | 「被核对象」与「SHA256 =」间插入括注路径，严格相邻格式 0 条。R11 回验 `path='lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md' match=True bytes=11948`（本会话实跑确认该锚文件 11948 B 在场）；迁 R11 即消解、无需改件。 |
| 25 | `lead/s604_attribution_20261108/` / `S604_ATTRIBUTION.md` | 缺绑定行；L160「  - 归因回件（复核的被核对象）\`lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md\` **SHA256 = 7241026122978426838d6c8ccaa8ea3335fe6213adef6bae10ab9c7aa83df2f2，字节数 = 17272**（与其自报前缀 7241026122978426 一致）；」；L161「  - 该回件所述被核对象 \`lead/slowframe_r3_20261108/_r3_GAPDIFF_RECHECK.md\` **SHA256 = 98cd612f63210182f1f6aa9f1c4d664e711d7616e79bc9805d450695a919cf6e，字节数 = 11215**（与编排方基线一致）。」 | A–D 不适用 | **真问题（格式类）** | 两条都没有「被核对象 SHA256 =」严格相邻前缀（是「归因回件（…）\`路径\` **SHA256 = …**」）；严格格式 0 条。R11 回验 2 条 `match=True`（17272 B / 11215 B，本会话实跑确认两锚文件在场且字节数相符）；迁 R11 即消解。 |
| 26 | `lead/s604_script_gap_20261109/` / `S604_SCRIPT_GAP.md` | 缺要素 `脚本存在性`；L10「1. **只查两件事**：(a) 台账 §604（「同一窗内慢 1/3 帧 vs 快 1/3 帧对照」）的**生成脚本**是否在盘、能否重建；(b) 该表「单向压缩」的数字行为能否归属到某一候选错误类、哪些候选可证伪、哪些筛不出。」；L32「## 3 脚本搜索全结果与存在性判定（四路逐路）」；L69「### 3.5 存在性判定」 | A–D 不适用（措辞变体） | **真问题（字面措辞）** | 任务书（dwfrun-5e5d5e49）必现要素 `脚本存在性`；件用「存在性判定」/`生成脚本是否在盘`，字面 0 命中，R9 双缺。 |
| 27 | 同上 | 缺要素 `可重建`；L73「## 4 重建可行性与单向压缩候选筛选」；L87「**判定：正确算法【可唯一重建】。** 已有四重独立实现逐位一致（N-8、R3 蓝本、\`_verify_r3_gapdiff.py\` 第三方、上轮探针 [0] 三窗逐位复现 R3 [B]，\`_sg_probe_compression_out.txt:1-4\`【实读】），复核轮另有第 5 重独立实现与 R3 [B] 逐位一致（max\|Δ\|=0.000000）【转述：复核回件】。」 | A–D 不适用（措辞变体） | **真问题（字面措辞）** | 必现要素 `可重建`；件用「可唯一重建」（多了「唯一」二字），`可重建` 0 命中，R9 双缺。注：复核方 `_rjv_step5.py:37` 用 `tok = prob[5:]` 取「缺要素 可重建」得「重建」（本会话 `_rj_delivery_verify_out.json.rjv_step5_token_slice` 实算），故其 step5 表只报 1 条缺要素；本件按基线 2 条问题条目如实记 2 条。 |
| 28 | `lead/s604_script_hunt_20261109/` / `S604_SCRIPT_HUNT.md` | `已删除`；L143「**不可能/未覆盖（如实申报，穷搜轮 §5 :105-110 申报 + 复核轮确认）**：已删除文件的磁盘未分配残块 carving 未做（本体已得，无必要）；JetBrains LocalHistory 为专有二进制未解析；OneDrive 仅确认存在、云端内容未审计；R6h（90.5s）/R9（120.1s）两路预算截断后的残余未补扫（…）；WAL 为活文件，读的是扫描时点快照。」 | **A 检索动作 / 检索对象** | **误报** | 「已删除」是「**文件**」的定语，句子在「不可能/未覆盖（如实申报）」清单里申报「这类文件的磁盘残块 **carving 未做**」，不是「已删除了什么」的既成事实断言。任务书 (b) 原文即「有哪些位置**不可能**覆盖（如已删除文件的磁盘残块、未记录的远程备份）？」（`_rj_final_checks.py` 输出逐字打印），门禁 `for bad in ['已改','已删除','已清理']` 却禁该词——**删词反而抹掉任务书要求的申报**（掩盖证据）。朴素与 R10 同报 1 处（`naiveP=1 r10P=1 r12P=0`）。 |

**逐域汇总（13 域 / 24 条问题条目；上表 28 行按「词 × 行」展开，#7/#12/#18/#20/#23 等按 baseline 的 1 条问题条目计数）：真问题 8 / 误报 16。**

| 域 | 问题条目 | 真问题 | 误报 |
|:--|--:|--:|--:|
| c07_gate_audit_20261109 | 1 | 0 | 1 |
| c07_protocol_attacks_20261109 | 1 | 0 | 1 |
| c07_slot_20261109 | 2 | 0 | 2 |
| c07_truth_protocol_20261109 | 2 | 0 | 2 |
| ledger_appendix_20261108 | 2 | 1 | 1 |
| matrix_ab_ruling_20261109 | 4 | 1 | 3 |
| matrix_reach_20261109 | 1 | 1 | 0 |
| n10c04_ruling_20261108 | 2 | 0 | 2 |
| n11_wording_fix_20261108 | 1 | 1 | 0 |
| n4_yi_final_20261108 | 4 | 1 | 3 |
| s604_attribution_20261108 | 1 | 1 | 0 |
| s604_script_gap_20261109 | 2 | 2 | 0 |
| s604_script_hunt_20261109 | 1 | 0 | 1 |
| **合计** | **24** | **8** | **16** |

**重点（c07_slot / c07_truth_protocol）**：R10 比朴素多报的 7 处（c07_slot 5 + c07_truth_protocol 2）**全是新误报**（标题 / 表头 / 清单 / 条件式 / 占位符 / 先例引述），「朴素漏真断言」假设**不成立**——朴素报的正是同一 token `已填`（各 1 条），R10 多的不是新词或同义词，只是同一 token 的其它出现次数；`_g7_predicates.py:78-111` 的 `r10_context` 只有 `double_neg / negation / quote_mention / assertion` 四类，缺 A/B 两类语用豁免 + 一类库外新缺口（条件分支/清单格/判定档，§5 记 E）。另有 2 处「理由错、结论对」的否定豁免（#7 第二处、#11），根因 `_g7_predicates.py:69-70` 的 24 字 `NEG_RE` 回看窗。

---

## 4 修正后的账

### (a) 真问题 / 误报

- **真问题 8 处**（按 24 条条目计，均相对「字面判据」成立）= 3 条严格格式绑定行偏离（`ledger_appendix:186` / `n4_yi_final:122` / `s604_attribution:160-161`）+ 5 条字面措辞变体（`需谁批准` / `实跑输出` / `改前改后` / `脚本存在性` / `可重建`）。
- **误报 16 处** = 3 条提取器假象（c07_protocol_attacks / c07_slot / c07_truth_protocol 的「缺绑定行」）+ 2 条 R9 反引号包裹符（c07_gate_audit / n4_yi_final 的「缺要素」）+ 11 条断言词语境（c07_slot 1 / c07_truth_protocol 1 / ledger_appendix 1 / matrix_ab_ruling 3 / n10c04_ruling 2 / n4_yi_final 2 / s604_script_hunt 1）。
- 判据层改走 **R11**（容忍 ≤160 字符路径隔断 + 引用锚回验，`_g7_predicates.py:152-222`）→ 3 处格式类自动消解 → **真问题 5 / 误报 19**（本会话 `_rj_final_checks.py` 实跑：13 域 `R11=0 problems`，且 3 域 `strict_adjacent:0 / r11_bindings=1,1,2 / match=true`）。
- 若再扩同义词/语义要素层（R9-R12 库外新写）→ 真问题 0；但那是新写判据，不在本轮「复用 R9-R12」范围内，标「未验」。

### (b) 全量谓词化模拟（两套口径，均本会话实跑）

1. **原样谓词化（R9 + R10 + R12 + R11 + 小节）**：实跑 `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_rejudge32_20261109\_rj_final_checks.py > …\_rj_delivery_final_checks_stdout.txt` → `谓词化后仍不通过 = 7 域`：`c07_slot`(R10×5) / `c07_truth_protocol`(R10×2) / `matrix_ab_ruling`(R9 需谁批准) / `matrix_reach`(R9 实跑输出) / `n11_wording_fix`(R9 改前改后) / `s604_script_gap`(R9×2) / `s604_script_hunt`(R10 已删除)；`R12` 全域 0。产物 `_rj_predicatized_sim_out.json`。
2. **补 R10 语境类后真剩 4 域**：前一轮 `afterRejudge` 与 `_rj_findings.md:98` 声称的「真正剩下的 = 4 域」，复核方 `_rjv_step5.py` 用 `_rj_findings.md:128` 原样 STRUCT 片段实测为 **5 域**（多 `s604_script_hunt`），判 FAIL；原稿的 `_rj_final_checks.py:85-97` 只跑原始 `r10_scan`、没加任何 STRUCT 豁免，故「4 域」当时**无实跑输出支撑**。本会话不掩盖该破绽，给出修正版片段（§5(b)）并实跑 `_rj_delivery_verify.py`：
```
=== (2) 修正版片段 13 域模拟 ===
  fail_count=4 fail=['lead/matrix_ab_ruling_20261109/', 'lead/matrix_reach_20261109/',
                     'lead/n11_wording_fix_20261108/', 'lead/s604_script_gap_20261109/']
```
→ **补 A/B/E 语境类后真正剩下 4 域**（全部是 R9 字面措辞变体），`c07_slot` / `c07_truth_protocol` / `s604_script_hunt` 三域的 8 条 R10 断言已实证消解。修正版同时补上复核方要求的假阴性探针：`all_assertion_probes_still_D=True`（5 条真断言反例全部仍判 D、不放过）。

### (c) 6 个 bindings=0 域逐个定性（任务书【交付】写「5 个」，实测 6 个；此处按 6 个全给，「5 个」差 1 标未验）

实跑 `_rj_delivery_verify.py` 的 `(1)` 段（用各域 GATE_CODE 里真实的 `B=re.findall(...)` 正则，而非 `_dn_regate_domains.py:22/:76` 只取第一个 findall 的假象）：

| 域 | 基线 fake regex | 真实绑定正则 | 真实 B | 严格相邻行 | 任务书要求 | 定性 |
|:--|:--|:--|--:|--:|:--|:--|
| c07_protocol_attacks_20261109 | `sess_…{24,}` | `被核对象 SHA256 = [0-9a-fA-F]{64}` | **2** | L8/L102 = 2 | 「★ 回件必须含绑定行」 | **要求了、交付件有** → 提取器误报，不是问题 |
| c07_slot_20261109 | `sess_…{6,}` | ``SHA256\s*=\s*`[0-9a-fA-F]{64}` `` | **5** | 0（反引号为任务书要求） | 「复核回件必须含绑定行，格式固定为：被核对象 SHA256 = \`64位hex\`」 | **要求了、交付件有** → 提取器误报，不是问题 |
| c07_truth_protocol_20261109 | `sess_…{20,}` | `被核对象 SHA256 = [0-9a-fA-F]{64}` | **15** | L29-83/L182 = 15 | 「★ 回件必须含绑定行」 | **要求了、交付件有** → 提取器误报，不是问题 |
| ledger_appendix_20261108 | `被核对象 SHA256\s*=\s*`?hex`?` | 同左 | 0 | 0（L186 语义绑定） | 「复核回件必须含「被核对象 SHA256 = <64位>，字节数 = <n>」」 | **要求了、严格格式缺** → 真问题（格式类）；R11 MATCH=True/5592 B |
| n4_yi_final_20261108 | `^\|\s*(R\d+|\d+)\s*\|` | `被核对象 SHA256\s*=\s*`?hex`?` | 0 | 0（L122 语义绑定） | 同上 | **要求了、严格格式缺** → 真问题（格式类）；R11 MATCH=True/11948 B |
| s604_attribution_20261108 | `被核对象 SHA256\s*=\s*`?hex`?` | 同左 | 0 | 0（L160/L161 语义绑定） | 同上 | **要求了、严格格式缺** → 真问题（格式类）；R11 MATCH=True×2（17272/11215 B） |

3 个「提取器假象」的根因在 `_dn_regate_domains.py:22` + `:76`；另 3 个是真实严格格式偏离。复核方 `_rjv_step3_out.json.extractor_all_findall` 与 `_rjv_step4_out.json.r11_true_problem_domains` 独立复算同值。

### (d) 复核 verdict 记录

- 复核回件【复核】`verdict = partial` → 按【交付】要求标 **unconfirmed**。其 `ranCommands=24`，七件指纹、13/6 数字、9 域误报抽验、8 条真问题（相对字面判据）、判不了项、越界检查均判 PASS。
- 两处 FAIL 实证保留：① `_rj_findings.md:140-142` 的「主件缺失即 FAIL」只是三行注释，片段本身无可执行 `if not DOC.is_file():` 分支，且 `raise SystemExit('predicate fingerprint mismatch')` 在失配时不输出合法 JSON（复核 `_rjv_step3_out.json.fragment.fail_branch_is_comment_only=true`）；② 原样 STRUCT 片段跑出 5 域而非 4 域，且对 4 条真断言反例 `STRUCT_match=true` 会制造新漏判面、`\b或\b` 在 CJK 夹字不命中。本件 §5(b) 的可粘贴片段针对这两点重写并在 `_rj_delivery_verify.py:95-140` 实跑自洽。

---

## 5 36 处改造件补遗建议

### (a) 位点 / 判据两件事为何必须一起做（含 c07_slot 具体失败场景）

位点修的是「核哪个文件」，判据修的是「用什么尺子量」，失效面互不覆盖。上游 36 处改造模板实读 `GATE_DOC_NAME_FIX.md:88-95`（`DOC=wd/'<MAIN>';SHA='MISSING'` + `if not DOC.is_file():` + `else:` + 1 空格缩进）、`:125-127`（主件缺失仍输出合法 JSON `ok=false`）、`:129-148`（6 处 `<ELSE_ONLY_VARS>` NameError 加固）、`:162-169`（迁移路径）、`:181-218`（36 处逐处表）。

**失败场景（c07_slot，方案 A 已生效后只改位点）**：`DOC=wd/'C07_IDENTITY_SLOT.md'` 把主件钉死（位点对），但判据仍是 `_dn_regate_domains.py:93-95` 的 `for bad in ['已补登','已填入','已填','已代填']: if bad in t: P.append('含越界断言 '+bad)`。任务书第五步与【交付】§5 都要求写出「多处同步排查表（…**是否已填**）」→ 合规交付件必然含 `已填` → 门禁必然 FAIL（就是 `_dn_regate_out.json` 现况）。后果三条：①合规件被打回、白重发一轮；②撰写方为过门禁删掉排查表或改写「是否已填」，**任务书要求的证据被删除而门禁 PASS**（掩盖证据）；③反过来只修判据不修位点，`max(cands,key=st_size)` 挑到更大更干净的侧件（S2 绕过，`GATE_DOC_NAME_FIX.md:251` 实读：`ok=True doc=_side_big.md（绕过）`），语境谓词再精细也作用在错误对象上，主件里的真断言溜过。

### (b) 判据层最小可粘贴片段（复用 R9-R12，不新写谓词本体）

**原则**：`importlib` 动态加载已指纹绑定的 `_g7_predicates.py`（`_g9_gate.py:36-52` 有「加载前 hashlib 验指纹、失配拒绝运行」范式；本会话 `_g9_gate.py` self_test U3 `all_pass=true` 实证），**不复制、不分叉**；`R9` 要素 / `R10` 断言 / `R11` 绑定 / `R12` 双重否定守卫全部复用。**只补 R10 的 A/B/E 语用语境分类**（库外薄层，不改写谓词本体），并**保留「主件缺失即 FAIL」为可执行分支**——这是复核方第 ① 条 FAIL 的正面修正。

下面片段替换 GATE_CODE 的 `else:` 内原「缺小节 / 缺要素 / 违禁词 / 绑定行正则」四段；`<MAIN>` / `ELEMS` / `SECTS` / `BAD` 逐处代入 `GATE_DOC_NAME_FIX.md:181-218` 的原值，`BAD` **不改词表**。首行已有 `import json,pathlib,re,hashlib`。

```python
import importlib.util as _ilu
_PRED = pathlib.Path(r'D:/Project/ra2-campaign-forge/lead/gate_fp7_20261108/_g7_predicates.py')
_PRED_SHA = '02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120'
# ① 缺失即 FAIL：可执行分支（不是注释）；失配只 P.append，不 raise，保证仍输出合法 JSON
g7 = None
if not _PRED.is_file() or hashlib.sha256(_PRED.read_bytes()).hexdigest() != _PRED_SHA \
        or _PRED.stat().st_size != 11743:
    P.append('谓词库缺失/指纹失配')
else:
    _sp = _ilu.spec_from_file_location('_g7p', _PRED)
    g7 = _ilu.module_from_spec(_sp); _sp.loader.exec_module(g7)
ELEMS = [<原 for k in [...]>]; SECTS = [<原 for s in [...]>]
BAD   = [<原 for bad in [...]>，逐处代入，不改词表]
# ② A/B/E 语用语境分类：只豁免「被讨论的对象」，不按行形一刀切（复核 FAIL② 的修正）
def _line_of(t, pos):
    s = t.rfind('\n', 0, pos) + 1; e = t.find('\n', pos)
    return t[s:len(t) if e < 0 else e]
def _cls(t, h, line):
    tok = h['token']
    if h['kind'] == 'double_neg': return 'D'                    # 交 R12 判违规
    if h['kind'] in ('negation', 'quote_mention'): return 'C'   # 否定式 / 短引证
    if re.search(r'<[^>\n]{0,40}' + re.escape(tok) + r'[^>\n]{0,40}>', line): return 'A'
    if re.search(re.escape(tok) + r'(文件|的)', line) and ('未覆盖' in line or '不可能' in line): return 'A'
    if '先例' in line and '非' in line: return 'A'                # 他件状态引述
    if ('是否' + tok) in line and line.lstrip().startswith(('#', '|')): return 'B'
    if '→' in line and ('未' + tok[1:]) in line: return 'E'        # 条件分支标签
    if re.match(r'^\s*\|\s*[A-G](?=\s|\|)', line) and ('拒绝' in line or '判定' in line): return 'E'
    if len(re.findall(r'(?:^|[；;\s])\d+\.\s', line)) >= 3: return 'E'  # 自检清单条文
    return 'D'                                                  # 真断言：一律不放过
if g7 is not None:
    for s in SECTS:
        if s not in t: P.append('缺小节 ' + s)
    for k in ELEMS:
        if not g7.r9_element_present(t, k)[0]: P.append('缺要素 ' + k + '（R9 双缺）')
    p10, w10, h10 = g7.r10_scan(t, BAD)
    for h in h10:
        if _cls(t, h, _line_of(t, h['pos'])) == 'D':
            P.append('含越权断言 %s @L%d（D 真断言）' % (h['token'], t.count('\n', 0, h['pos']) + 1))
    for x in g7.r12_scan(t, BAD)[0]: P.append('R12 ' + x)          # 双重否定守卫，勿省
    p11, w11, binds = g7.r11_scan(t, wd, root=root)                 # R11 容忍路径隔断 + 锚回验
    B = len(binds)
    for x in p11: P.append('R11 ' + x)
    if B < 1: P.append('缺 SHA256 绑定行（R11）')
# ★ 上方必须已有（GATE_DOC_NAME_FIX.md:88-95 原样、勿退回去）：
#   <ELSE_ONLY_VARS>                                   # print 引用的 else-only 名字预初始化
#   DOC=wd/'<MAIN>';SHA='MISSING'
#   if not DOC.is_file(): P.append('主件缺失 <MAIN>（写域='+wd.name+'）')
#   else:
#    raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()
#    t=raw.decode('utf-8',errors='replace')
# print(...) 里 'docSha256':SHA 也必须保留（GATE_DOC_NAME_FIX.md:97-100）
```

**本会话自证实跑**：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_rejudge32_20261109\_rj_delivery_verify.py > …\_rj_delivery_verify_stdout.txt`（exit=0）。`(2)` 段把上述逻辑做成 `gate()` 函数（`_rj_delivery_verify.py:61-94` 分类、`:95-140` 门禁主体，`:108` 为可执行 `if not DOC.is_file():`），对 13 域全量跑 → `fail_count=4 fail=[matrix_ab_ruling, matrix_reach, n11_wording_fix, s604_script_gap]`，即 §4(b) 的「真剩 4 域」**现有实跑输出支撑**；`(3)` 段假阴性探针 → `all_assertion_probes_still_D=True`，复核方举的 5 条真断言反例（`| 1 | **已改台账**（完成） |`、`1. 已改门禁，缺口已修补完毕。`、`### 5.4 已填身份值`、`| 状态 | 已生效 |`、`- 处置：已填 → 见证同为声明`）全部仍判 D、不被豁免；`cjk_or_b={'见证已填或S1有记载': False, '通过档或存疑档': False}` 说明**不能用 `\b或\b` 做条件式判据**（原稿 `_rj_findings.md:128` 的 STRUCT 用了它，复核方实测破绽成立）。片段未在 36 处历史 payload 上落地（铁律禁止）；只在唯一写域内模拟。

### (c) 迁移顺序（先判据后位点）

**工程迁移顺序：①判据 → ②位点 → ③合并回归；运行期判定顺序反过来（位点在前、判据在后）**。理由：
1. 判据是纯静态文本谓词，可在 32 域现盘主件上离线全量回归（本会话已跑 `_rj_delivery_verify.py` 13 域 + `_rj_final_checks.py` 13 域 + `_rj_double_track.py` 32 域），零 payload 改动、零重发；位点改造要动 DOC 选择段、`<ELSE_ONLY_VARS>` 加固与 print 行（`GATE_DOC_NAME_FIX.md:129-148` 的 6 处 NameError 面），牵连更大。
2. 若先改位点而判据仍朴素，回归会在这 13 域报 24 条问题，把「位点改造是否成功」的差分信号淹没在 16 条误报噪音里（§5(a) 的 c07_slot 场景），无法判定效果；先消掉误报噪音，位点改造的 S1–S4 差分才干净。
3. 判据补丁是 GATE_CODE 的 `else:` 内一段，位点补丁是其上的选择段，两者不冲突；合并时把「主件缺失即 FAIL」放在最前，`<ELSE_ONLY_VARS>` 预初始化放在 `DOC=` 之前，再跑 32 域全量 + S1–S6 + 主件在场/缺失两态（`GATE_DOC_NAME_FIX.md:162-169` 的回归层）。
4. **历史 36 处 payload 绝对不改**，两者都只在「下一发」落地；`GATE_DOC_NAME_FIX.md:169` 原样「36 处一律不落地修改，只登记欠账」。

---

## 6 复核回件（绑定行格式）+ 判不了的边界 + 未改件声明 + 未验项

### 6.1 复核回件绑定行（七件上游指纹，本会话 hashlib 实算 7/7 相符）

按【铁律】固定格式：`被核对象 SHA256 = ` 紧跟完整 64 位十六进制，中间不插路径/括号/星号/反引号/空格；随后 `，字节数 = ` 再写数字。

```
被核对象 SHA256 = 0d129e409ca5ab744891abccd85a0c0ca0c164ddea8620de634de5079fa8f096，字节数 = 22133
被核对象 SHA256 = a1006e06836e902ec462186676ef66c4d6301ab8aee58234c05add9b946c46cd，字节数 = 41361
被核对象 SHA256 = 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120，字节数 = 11743
被核对象 SHA256 = a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6，字节数 = 11623
被核对象 SHA256 = 7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52，字节数 = 19481
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518
```

底稿 `_rj_findings.md` 现值（复核回件 sha256Line 第八行，本会话复算一致）：

```
被核对象 SHA256 = 8be23bc2096b87f623b4c24df8a673897f0bcf2536557da26cc7d436d45fa5f2，字节数 = 29796
```

**复核 verdict 如实记**：`partial` → **unconfirmed**（见 §1 / §4(d)）。不成立的两处（片段不可自洽、4 域无实跑支撑）已在本会话 §4(b)/§5(b) 用 `_rj_delivery_verify.py` 补正；成立的部分不重复粉饰。

### 6.2 判不了的边界（5 条，均非回避判定）

1. **判不了**：编排方「10 个域」「5 个 bindings=0」的出处与枚举。我实测 13 / 6（§2.2、§4(c)），`GATE_DOC_NAME_FIX.md:242` 自述也是 13；编排方未给 10 域枚举，6 种口径都得不出 10 → **10 域集合对齐未验**，本件按 13 域全量判，不猜。
2. **判不了**：35 处历史门禁**当时**的实跑输出（exit / problems / 读了谁）不可复原（`GATE_DOC_NAME_FIX.md:316` 逐字），本轮只判现盘主件文本，不判当时是否误判。
3. **判不了**：台账漂移段（PRE 指纹为运行期值）与门禁一次性复合条件未纳入 32 域补跑（`GATE_DOC_NAME_FIX.md:318`）；R10 覆盖 `「…」` 短引证与 24 字否定回看窗（`_g7_predicates.py:69-72`），表格 `|`、Markdown 标题、`<…>` 占位符、`→`/`或` 条件式的彻底判定只能人工逐句读（本会话已逐句读 26 处命中，见 `_rj_context_dump_out.txt`）。
4. **需要人工看**：3 处格式偏离绑定行（`ledger_appendix:186` / `n4_yi_final:122` / `s604_attribution:160-161`）是补严格格式行还是采纳 R11 语义绑定；5 处措辞变体（`需谁批准` / `实跑输出` / `改前改后` / `脚本存在性` / `可重建`）是补字面串还是扩同义词谓词；`c07_slot` / `c07_truth_protocol` 的「已填」语境需裁决任务书禁词表与「是否已填」交付要求的冲突。
5. **任务书本身含糊（不是门禁的错）**：① c07_slot 第五步 +【交付】§5 要求写「是否已填」，同时门禁把 `已填` 列为既成事实断言禁词，字面执行必 FAIL；② s604_script_hunt (b) 原文要求讨论「**已删除**文件的磁盘残块」，同时门禁禁 `已删除`（删词即抹掉任务书要求的申报）；③ c07_truth_protocol 要求「协议文本必须可直接给来源会话使用」却禁 `已填`，协议状态机无法写「已填 → …」分支；④ 绑定行格式跨任务书不统一（多数禁反引号、c07_slot 明确要求反引号、本任务铁律又禁反引号）；⑤「必现要素」当字面 token 还是语义要求未写清（`s604_script_gap` 的 `脚本存在性` vs 交付件 `存在性判定`）。

### 6.3 未改已交付件声明（本会话实跑复核）

- 实跑 `python -I -X utf8 -c "<32 主件逐件 hashlib 复算 + 七件现值 + banned 词计数 + mjs 拼接>"` → `32 main count 32 drift 0 []`；`lead/c07_slot_20261109/C07_IDENTITY_SLOT.md 已填 count 6`、`lead/s604_script_hunt_20261109/S604_SCRIPT_HUNT.md 已删除 count 1`（**词仍在，一个没删**，即未掩盖证据）；七件上游指纹现值见 §2.1（7/7 相符）。
- `.zcode/workflow-runs/` 历史 payload：复核时 231 件，本会话现值 234 件；实跑按 mtime 取前 231 件拼接 sha256 = `322efde423538fb63270e16953f1d64265e094160c9ca394c37f34e46149110a`，与复核方 `_rjv_step3_out.json.boundary.mjs_sha256_concat` **逐字节一致**（旧件零改写）；新增 3 件为其它工作流新建（`dwfrun-428fc888…` / `dwfrun-95347e3f…` / `dwfrun-daba575b…`，本会话实读其 mtime 与首行，均非本写域产物），本会话对全部 mjs 只读。
- `git -C D:\Project\ra2-campaign-forge rev-parse HEAD` → `26574589aa8401e8f3f2934680a1ea7109bafa2d`（未 commit）；`git status --porcelain=v1 -- lead/gate_rejudge32_20261109` → `?? lead/gate_rejudge32_20261109/`（未 push、未 add）。唯一写域外零写入。
- 零真机、零采样代码；本会话所有 Python 均 `python -I -X utf8` + 绝对路径；指纹用 hashlib。

### 6.4 未验项汇总

`10 域枚举` / `35 处门禁当时实跑输出` / `台账漂移段与一次性复合条件` / `R10 语用语境的库外彻底覆盖边界` / `同义词·语义要素层（R9-R12 库外新写）能否把 5 条措辞变体全消解` / `编排方 REJUDGE_CODE 里 10/5 的具体算式出处`（`dwfrun-868215ce-ea87-4e41-a54b-5a0af3c441dd.mjs` 内 `ASK_ANALYST` 实读只有数字、未枚举集合）——以上均标**未验**，不补造。
