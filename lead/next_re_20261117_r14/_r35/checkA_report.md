# Round 35 · Check A 明细：limitations 中非 § 引用

共 22 行 limitations 含非 § 引用。

## F08 [[静态推断]]

- limitations 原文：定谳句与 a–e 与 (a′) 是不可拆的引用单元：引用 ②-b/定谳句/(a)/(a′) 必须同时同引 a–e 与 (a′)，不得单独引用、不得写成 [已证]；不得只引 §2.6 而不引 §2.9/§2.10；D-1：与 F17 部分重叠，引用时二者同看
- evidence_paths：lead\next_re_20261117_r14\R14_COMMON.md(§2.9一/§2.10一/二);lead\next_re_20261117_r14\R17_LEDGER_1064\SECTION.md(事项4)
  - FACT `F17` : 存在于索引=True

## F13 [[流程]]

- limitations 原文：规则一与 §2.8 规则A(负面结论须自带正控与反控)同族；规则二来自 AUDIT-R30、A5 PARTIAL 因未实际同引 a–e；两条都不得只引用结论而不引方法；D-3：与 F20 部分重叠，引用时二者同看
- evidence_paths：lead\next_re_20261117_r14\BOARD_ARCHIVE.md(R17 第 16 轮 段);lead\next_re_20261117_r14\R17_LEDGER_1063\SECTION.md(事项3);lead\next_re_20261117_r14\R17_LEDGER_1064\SECTION.md(事项5);lead\next_re_20261117_r14\R14_COMMON.md(§2.8规则A/§2.10三)
  - FACT `F20` : 存在于索引=True

## F15 [[已证]]

- limitations 原文：stats.tsv 的 108/82/4/33 是过期中间态、已被 REPORT.md 取代、不得引用(见 conflicts.md C01)；形态命中数不受 host 修正影响须给 267/70/1/7/9 依据；原稿 R17_LEDGER_1063 记为 108/82/4/33
- evidence_paths：lead\next_re_20261117_r14\R17_LEDGER_1063R\SECTION.md(事项4);lead\next_re_20261117_r14\BOARD_ARCHIVE.md(R17 第 16 轮 段)
  - CARD `R17_LEDGER_1063` : 目录存在=True / 在本行 evidence_paths=True

## F17 [[已证]]

- limitations 原文：须与 F08 同引 a–e 与 (a′)；不得据此判 ②-b 升格；D-1：与 F08（b 部分）部分重叠，引用时二者同看；D-2：与 F36 部分重叠，引用时二者同看；引 ②-b 须同引 §2.9 定谳句 + 书面限制 a–e + §2.10 的 (a′)，四者不可拆
- evidence_paths：lead\next_re_20261117_r14\R14_COMMON.md(§2.6四 / §2.10一)
  - FACT `F08` : 存在于索引=True
  - FACT `F36` : 存在于索引=True

## F20 [[流程]]

- limitations 原文：—；D-3：与 F13 部分重叠，引用时二者同看
- evidence_paths：lead\LEAD_LOCK(AG4/AE7/AD2);lead\next_re_20261117_r14\R17_R36_VERIFY_TABLEBASE\VERDICT.md;lead\next_re_20261117_r14\R17_AUDIT_FACTINDEX\VERDICT.md
  - FACT `F13` : 存在于索引=True

## F28 [[流程]]

- limitations 原文：卡面明确「删除析构签名可为 test al,1，不止 [esp+X],1」；§13.5 与 NAMED_PUSH_AUDIT10 §2 分别支撑两种签名形态，§8.1 错源㉓ 支撑「成对行必有一假」。
- evidence_paths：lead\next_re_20261117_r14\R14_COMMON.md(§8.1 错源㉓ / §13.5);lead\LEAD_LOCK(追加·2026-11-20 19:0x·r15 第 86-92 轮 段);lead\next_re_20261117_r14\NAMED_PUSH_AUDIT10\VERDICT.md(§2);lead\next_re_20261117_r14\COVERAGE\PANEL.md(M72 ㉓ 正向记录)
  - CARD `NAMED_PUSH_AUDIT10` : 目录存在=True / 在本行 evidence_paths=True

## F29 [[已证]]

- limitations 原文：mov eax,1; ret 4 与 vt+0x20 均为卡面口径；§13.3 给出字节形态、逐表反例与「不写 Release 释放」的措辞纪律；D-4 已裁（2026-11-21，R17_R52_ADJ_D4）判定 ① 两者可并存：本条是语义级判据且带 imm32==1 前置条件，F49 是形态级全称否定，二者作用域不相交、无共同被否定命题；引本条须同引该裁决规范措辞，不得再用「口径待裁」表述；0x6C2AC0 的「InterlockedIncrement」是 §13.3 的推断措辞（字节只给 call [0x7E11C8]），本条引用时须写明该词未经字节证实
- evidence_paths：lead\next_re_20261117_r14\R14_COMMON.md(§13.3);lead\LEAD_LOCK(追加·2026-11-20 14:1x·r15 第 70-78 轮 段);lead\next_re_20261117_r14\COVERAGE\PANEL.md(M71 披露);lead\next_re_20261117_r14\R17_R52_ADJ_D4\VERDICT.md
  - CARD `R17_R52_ADJ_D4` : 目录存在=True / 在本行 evidence_paths=True
  - FACT `F49` : 存在于索引=True

## F30 [[流程]]

- limitations 原文：卡面给定「pTD/pCHD 为绝对 VA」；§13.1 给可执行三步判据与四表实测。F01 只给类名链、未含 VA/RVA 读法，故本条为新增而非重复。
- evidence_paths：lead\next_re_20261117_r14\R14_COMMON.md(§13.1);lead\LEAD_LOCK(追加·2026-11-20 19:0x·r15 第 86-92 轮 段)
  - FACT `F01` : 存在于索引=True

## F34 [[流程]]

- limitations 原文：G1–G5 与 host <= site < fn_end 均为卡面口径；LEAD_LOCK 两段分别给「缺位置断言不算校验（M98–M102）」与「同一根因翻车四次」的原文。
- evidence_paths：lead\LEAD_LOCK(方法论硬约束（R17 起继续有效） 段 / R16 遗留的方法论保留 段);lead\next_re_20261117_r14\COVERAGE\PANEL.md(M98 / M102)
  - MITEM `M102` : 出现于卡=COVERAGE,LEAD_LOCK / 其中在本行锚内=COVERAGE,LEAD_LOCK
  - MITEM `M98` : 出现于卡=COVERAGE,LEAD_LOCK / 其中在本行锚内=COVERAGE,LEAD_LOCK

## F35 [[流程]]

- limitations 原文：ceil(0.9n)/ceil(0.5n)/proved_strict 均为卡面口径；PANEL M47 给判定式原文，M52 给达标复算，M44 给 proved_strict 定义。F25/F26 只记结果与裁定、未记判据式，故不重复。
- evidence_paths：lead\next_re_20261117_r14\COVERAGE\PANEL.md(M47 / M52 / 严格口径双列表)
  - MITEM `M44` : 出现于卡=COVERAGE / 其中在本行锚内=COVERAGE
  - MITEM `M47` : 出现于卡=COVERAGE,LEAD_LOCK / 其中在本行锚内=COVERAGE
  - MITEM `M52` : 出现于卡=COVERAGE,LEAD_LOCK / 其中在本行锚内=COVERAGE
  - FACT `F25` : 存在于索引=True
  - FACT `F26` : 存在于索引=True

## F36 [[流程]]

- limitations 原文：GATE_MAP 用途见 §2.6 来源行；既有误记与更正见 §2.7（标题及正文）与 PANEL M103。F17 记的是另一处更正（§2.10 (a′)），不覆盖本条；D-2：与 F17 部分重叠，引用时二者同看；引 ②-b 须同引 §2.9 定谳句 + 书面限制 a–e + §2.10 的 (a′)，四者不可拆
- evidence_paths：lead\next_re_20261117_r14\R14_COMMON.md(§2.6 来源段 / §2.7);lead\next_re_20261117_r14\COVERAGE\PANEL.md(M103 段)
  - MITEM `M103` : 出现于卡=COVERAGE,LEAD_LOCK / 其中在本行锚内=COVERAGE
  - FACT `F17` : 存在于索引=True

## F37 [[流程]]

- limitations 原文：规则C 四要件在 §2.8 规则C 逐字成文；F01/F02 仅在 limitations 引用「按 §2.8 规则C裁决」、未陈述规则内容，故为新增。
- evidence_paths：lead\next_re_20261117_r14\R14_COMMON.md(§2.8 规则C)
  - FACT `F01` : 存在于索引=True
  - FACT `F02` : 存在于索引=True

## F39 [[流程]]

- limitations 原文：须与 F08（②-b 书面限制 a–e）及 F23（④ 三口径/真两链）同引语境：同源只计一环，不得把环②字段写与环④被调语义当两条独立证据；本条不支撑 ②-b 升格。
- evidence_paths：lead\next_re_20261117_r14\R14_COMMON.md(§8.3 R14-R17 同源不得双计);lead\next_re_20261117_r14\BOARD_ARCHIVE.md(R14-R17);lead\next_re_20261117_r14\HANDOFF_R14_R3.md(五)
  - FACT `F08` : 存在于索引=True
  - FACT `F23` : 存在于索引=True

## F40 [[流程]]

- limitations 原文：F16 limitations 已引本规则名但未陈述内容；引用单源推断须与 F16 同引并带推断强度标注，不得写成事实。
- evidence_paths：lead\next_re_20261117_r14\R14_COMMON.md(§2.8 规则B)
  - FACT `F16` : 存在于索引=True

## F45 [[已证]]

- limitations 原文：与 F01 同引：F01 只记 .?AV/.?AU 装饰名形态，本条补 PAU/PAV 前缀不得并入类名的禁例。
- evidence_paths：lead\next_re_20261117_r14\R14_COMMON.md(§8.1 / 模板前缀不是类名);lead\next_re_20261117_r14\S13_K10\_audit\VERDICT.md(§3)
  - FACT `F01` : 存在于索引=True

## F46 [[流程]]

- limitations 原文：与 F38（先测基线、对照同质）配套引用；随机基线恒 0 时不得据此背书。
- evidence_paths：lead\next_re_20261117_r14\R14_COMMON.md(§8.1 / 对同源系统性错误，随机基线恒为 0，必须用差分检验);lead\next_re_20261117_r14\S10_KPROVED\_audit\VERDICT.md(§4);lead\next_re_20261117_r14\S13_K12\_audit\VERDICT.md(§3)
  - FACT `F38` : 存在于索引=True

## F49 [[已证]]

- limitations 原文：与 F13 同引区分：F13 的反例是 C3 作 modrm 字节，本条是 ret 4 的 C2 04 00 形态，两者不是同一坑；D-4 已裁（2026-11-21，R17_R52_ADJ_D4）判定 ① 两者可并存：本条只讲形态，F29 只讲槽级行为且带 imm32==1 条件；全文件另有 32 处 b8 imm32 c2 04 00 的 imm≠1，故本条在「任意 imm」层面成立、不得反推槽级语义；引本条须同引该裁决规范措辞，不得再用「口径待裁」表述
- evidence_paths：lead\next_re_20261117_r14\R14_COMMON.md(§8.3 新增坑);lead\next_re_20261117_r14\HANDOFF_R14_R3.md(九);lead\next_re_20261117_r14\R17_R52_ADJ_D4\VERDICT.md
  - CARD `R17_R52_ADJ_D4` : 目录存在=True / 在本行 evidence_paths=True
  - FACT `F13` : 存在于索引=True
  - FACT `F29` : 存在于索引=True

## F50 [[流程]]

- limitations 原文：va−ImageBase 只在 VirtualAddress==PointerToRawData 的节内等价，且等价只保证数值相同、不保证该偏移有文件映射；错节读数是读法反例，不是该地址无数据；与 F20① 部分重叠，引用时二者同看
- evidence_paths：lead\next_re_20261117_r14\R17_R36_VERIFY_TABLEBASE\VERDICT.md;lead\next_re_20261117_r14\R17_R56_FACTINDEX_V53\lead_byte_checks.tsv
  - FACT `F20` : 存在于索引=True

## F51 [[已证]]

- limitations 原文：336 是裸 E8 命中数，不是严格 atexit 注册数；68 与 1439 口径不可互换；引用必须同列三数；Lead 已独立复算三数（严格形态按「紧邻 push imm32 + E8→0x7C978A」判据复现 68），故本条为双源；与 F27 部分重叠（F27 只给 68 与误命中禁令），引用时二者同看
- evidence_paths：lead\next_re_20261117_r14\R17_AUDIT_FI_V5\VERDICT.md(A5 / N2);lead\GOAL_THREE_TARGETS_20261018.md(N9 三条方法论修正 段)
  - FACT `F27` : 存在于索引=True

## F52 [[流程]]

- limitations 原文：三件齐是判据，单一 test 形态不构成删除析构器证据；与 F28/F29 同看
- evidence_paths：lead\next_re_20261117_r14\R14_COMMON.md(§13.3 / 要判「释放」，必须找);lead\next_re_20261117_r14\R14_COMMON.md(§13.5 判据);lead\next_re_20261117_r14\NAMED_PUSH_AUDIT10\VERDICT.md(§2)
  - FACT `F28` : 存在于索引=True
  - FACT `F29` : 存在于索引=True

## F53 [[流程]]

- limitations 原文：0x007E88D0 固定反例不得外推为全表属性；写点枚举与剔除顺序不可省略；Lead 已逐处核字节：4 处写点均为 vptr 安装，其中 0x4CA778 位于 0x4CA770 体内，该函数具备 test byte ptr [esp+X],1(+255) + call 0x7C8B3D(+263) + ret 4(+275) 三件，故属删除析构器侧写、成对写成立；与 F28 部分重叠，引用时二者同看
- evidence_paths：lead\next_re_20261117_r14\R14_COMMON.md(§13.5 边界段);lead\next_re_20261117_r14\R17_R56_FACTINDEX_V53\lead_byte_checks.tsv
  - FACT `F28` : 存在于索引=True

## F54 [[流程]]

- limitations 原文：PEFormatError 仅提示读法/映射需复核；不得直接判 RTTI 不可解或未取得；四表实测范围以外不得外推；与 F30 部分重叠（F30 讲 pTD/pCHD 存绝对 VA），引用时二者同看
- evidence_paths：lead\next_re_20261117_r14\R14_COMMON.md(§13.1 / 解引用失败不得直接判不可解);lead\next_re_20261117_r14\NAMED_PUSH_AUDIT15\VERDICT.md
  - FACT `F30` : 存在于索引=True
