# W3-CS3 派工单 · coverage_ledger 台账杂项三件 + RPT1 登记建议处置

> 派发：2026-10-02 19:5x（Lead）· 前置：**CS2 已验收（21/21，§476）**，同写域串行解除
> 执行：Qoder CN（新会话）· 预估 40–70 分钟

## 背景（先读这些依据，再动手）

1. 台账 `out/re_work/qc/W3_20261001/coverage_ledger/`（COVERAGE_LEDGER.md + coverage_ledger.json）刚经 **CS2 读数重钉**验收：每处引用带 scope_label 与复算记录。本卡是它的**收尾杂项**，不是重做。
2. 依据件（全部先读原文，禁止凭本卡转述下判断）：
   - `out/re_work/qc/W3_20261001/coverage_ledger/_LEAD_DECISION_F_game.md`（Lead §401 决定件）
   - E1 验收报告与 M34R 报告（`out/re_work/qc/W3_20261002/e1_claims_closure/`、`out/re_work/qc/W3_20261001/m34r_m27_recheck/`，以实际目录为准，先扫再读）
   - CS2 产物 `out/re_work/qc/W3_20261002/cs2_readings/`（scope_label 的既有写法模板）
   - RPT1 报告 `out/re_work/qc/W3_20261002/rpt1_readpoints/RPT1_REPORT.md`（§477 已验收）

## 四件任务（逐件做，逐件留证）

### ① M34R 更正稿采纳
E1 在验收时**更正了 M34R 的一句话**：M34R 的 `task_D_machine_readable_coverage:「没有覆盖」` 指的是 **claims_game/*.txt**，**不是 Task D 的机器可读交付副本**（按字面读会误伤已验收的包）。台账中引用该措辞的行/字段，采纳更正稿：
- 更正后的表述必须把作用域写全（哪份文件、哪个时点）；
- 采纳动作本身要留痕（改了哪一行、before/after 摘要进你的报告）；
- **原行的既有数字一个都不许改**（这句更正只动"覆盖指的是什么"的措辞，不动读数）。

### ② row_F 补 scope_label
`row_F`（19.23%，5/26）目前缺 CS2 给其它读数加的那种作用域标签。按 CS2 模板补：**YR 侧 `docs/re/ARCHITECTURE_ATLAS.md` × lead10 库集 · 最低章 §11 全局关键单例与类虚表地址速查总表 = 5/26 = 19.23%**。
- 判死依据已存在：`row_f_adjudication_20261002.decision = "A"`（只标注来源，不重算）——**不许重算、不许改登记值**；
- 整串引：凡写"章级覆盖率"必须带文档名 + 库集作用域（Lead 裁定件"禁止裸引"）。

### ③ F_game 登记（按 Lead 决定件，不是入册新行）
`_LEAD_DECISION_F_game.md` 已裁：**不入册新行**（行集合 = W2 §0 九口径，F_game 不在其中；且"原版侧用哪个库集"无定义）。但**"数据已备妥"必须留痕**：
- 在台账的登记/备注字段（**不是新增行**）记录：F_game 数据备妥位置（`crosscheck_g1_game_claims_body0206.json` 12 章 total/asserted/dangling，与 M16 已 12/12 对拍）+ 不入册决定的**一句理由**（引决定件原文）；
- 严禁把它做成 `A_game` 的章级分解行。

### ④ RPT1 的登记建议处置（降格/补登记）
RPT1（§477 已验收）给任务 E 留了两条建议：
- **idx 4 COFF Machine 保持 STILL_UNPROVEN**（六仪器两次变异零邻判；真正一票否决 PE32 身份的是 OptionalHeader.Magic @ 0x68 = 0x010B，而它不在 36 条里）⇒ 是否在台账相关行做**降格标注** + **补登记 Magic 字段**；
- **口径警告**：若验收要求"读取点必须在仓库自研门禁代码"，idx 9/10（SectionAlignment/FileAlignment，判据在 pefile）应回退 UNATTESTED。
- **处置规则**：只动**措辞/标注/登记建议**级别的，直接做；若需要**改行结构或改读数值**，**不要做**——写成 NEEDS_LEAD 提案（列选项 + 证据 + 推荐），放你的报告里等 Lead 裁。

## 铁律

1. **写域仅两处**：`out/re_work/qc/W3_20261001/coverage_ledger/`（被改对象）+ `out/re_work/qc/W3_20261002/cs3_ledger_misc/`（你的报告/留证）。其余全部只读 —— 特别是 ATLAS 两份、dispatch 台账、CS2/RPT1/E1 的产物目录**零写入**。
2. **开工先快照**：coverage_ledger 目录全文件 sha 前置快照进你的写域；收尾再快照 ⇒ 除本卡点名的改动外**零差异**（逐文件 diff 白名单）。
3. **改后台账必须仍全绿**：亲跑 `verify_ledger`（及其内嵌的 V-18 复跑），EXIT=0 才算完；同时自写 `verify_cs3.py`：
   - 正控：四件事各有 before/after 断言（点名行确实变了、变成的目标文本）；
   - 负控 ≥2：投毒副本上（如把 scope_label 改错、把 F_game 做成新行）验证器必须 FAIL；
   - 旧正文零删除：改动只能是"加标签/改点名措辞"，对被改行做前后对照留证。
4. **空扫描 = INSTRUMENT_FAILED**，不许 `[]` 冒充通过；拿不准的条目如实列 NEEDS_LEAD，**禁止硬做**。
5. 报告头一行：改了哪几件 / 没改哪几件 + 原因。

## 交付

`out/re_work/qc/W3_20261002/cs3_ledger_misc/`：`CS3_REPORT.md` + `verify_cs3.py` + 正负控输出 + 前后快照。完成后回报 `[0]`：四件的逐件结论（做了/提案/不做 + 一句理由）+ verdict tally 原文 + `verify_ledger` 与 `verify_cs3` 的 EXIT。
