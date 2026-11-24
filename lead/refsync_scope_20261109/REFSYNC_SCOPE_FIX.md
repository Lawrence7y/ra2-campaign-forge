# REFSYNC_SCOPE_FIX.md — 扫描口径修正件（全量载体图 / 差集 / 漏因 / 修正规则 / 分口径件数）

- 日期：2026-11-09。角色：口径修正件撰写员（动态工作流子代理）。
- 唯一写域 = `lead/refsync_scope_20261109/`。本件与本次新增的 `_fix_*` 输出件全部落在该目录；**未改任何既有件**。
- 铁律执行：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 hashlib；不 commit、不 push。
- 绝对只读域（`lead/ledger_appendix_20261108/`、`lead/ledger_bound_20261109/`、`lead/s604_refsync_full_20261109/`、`lead/s604_attribution_20261108/`、`lead/s604_exclusive_20261109/`、`lead/s604_verdict_entry_20261109/`、`lead/minhard_check_20261109/`）与两件台账一律未修改、未追加、未覆盖。
- 证据标准：每条判定追到「本会话实跑命令 + 输出」或「文件:行」。拿不到的一律写「**未验**」，不补造。判定「同一句」一律给逐字比对（EQUAL / NOT-EQUAL + 差异字符码位），不许用「已核对」概括。

---

## 1 目的与边界（只修扫描口径与给载体图，不改任何既有件）

**目的**：上一轮「载体与扫描口径核查」已产出 `lead/refsync_scope_20261109/_rs_CARRIER_MAP.md`（317 行）与可复用自检脚本 `_rs_carrier_scan.py`。本件把该结论整理为**口径修正件**，回答五件事：① 上游 14 件指纹是否仍与编排方一致；② 上一轮三个判定（组①逐字、组②区块内外、组③无转录块）及「随段进台账」逐组成立与否，独立复核是否通过；③ 全量**载体图**逐件逐行 + 是否进台账 + 判据，以及 13 件口径的**差集**；④ **扫描范围声明**为什么错、为什么漏 `ledger_bound`；⑤ 修正后的可执行**扫描规则**、**以句为单位**、**自检脚本**、**引用否定排除**，并给**分口径件数结论**（**严格交集** / **全量载体** / **§609 冲突** / 现在改仍来得及）。

**边界（★）**：**只做扫描与登记，不改任何既有件**。**全量载体图是地图，不是施工图**——本件只登记「这句话在哪些件的哪些行、哪些行会随整段进台账」，不判「该改哪几件」、不给改文文案、不执行追加、不代台账所有者裁决。台账正文「一律留台账所有者裁决」（`lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md:24`，本会话实读）。

**两句被扫表述（编排方指定的精确串，未私自扩展）**：`只能判「不可复现」` 与 `不能定位当年错误步骤`。引号变体 `只能判『不可复现』` 是**不同的串**：本会话 `python -I -X utf8 -c` 实算（dir-depth≤2、md、排除本写域）`只能判「不可复现」` = 16 文件 / 41 行，`只能判『不可复现』` = 14 文件 / 28 行，`不能定位当年错误步骤` = 16 文件 / 60 行；§607 用「」、§609 用『』（码位实测见 §5）。按指定串扫描，变体另记，不混算。

---

## 2 上游指纹（十四件）+ 上一轮三个判定的独立复核

### 2.1 十四件指纹（本会话 hashlib 全量重算）

命令：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rsv_fp.py"`
输出：`ALL_14_MATCH = True`；14/14 行 `OK`、逐行 `sha256 got=… exp=… EQUAL`、`bytes … EQUAL`、`lines … EQUAL`。`lines` 字段用「`LF` 计数 +1」约定（`splitlines()` 比它少 1，系末尾换行口径差，非内容差；例如 `S604_REFSYNC_FULL.md` splitlines=365 / countLF=365 / LF+1=366，与编排方 366 一致）。

| # | 件（相对 `lead/`） | SHA256 | 字节 | 行 |
|---|---|---|---:|---:|
| 1 | `s604_refsync_full_20261109/S604_REFSYNC_FULL.md` | `8ccf9866ebd7860f03d71e939960e018fd0cfbbe6b94add04dd50f7004c11ac5` | 61819 | 366 |
| 2 | `s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md` | `d9b9c5acd0077060fe7ab0a064c263aa609881bfdc1736407d66d5eec890e1f3` | 55331 | 338 |
| 3 | `ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md` | `724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e` | 45719 | 237 |
| 4 | `ledger_appendix_20261108/_la_draft3_s604_gapdiff.md` | `d5dc8f979503a65573bcf542fdd28dbf43f13e54dcf0d98229106db43b2f24a6` | 7703 | 41 |
| 5 | `ledger_appendix_20261108/_lad_tpl.md` | `a2313396db2ad9535ea211daf027d3956d4c84fb9927a138403ff1ee72ec083a` | 25723 | 173 |
| 6 | `ledger_bound_20261109/LEDGER_BOUND_VOLUME.md` | `47bb594b90e1c49cbbd83086468cbadb4bda05458d82cb7808661f975daf0b70` | 70587 | 439 |
| 7 | `ledger_bound_20261109/_lb_BOUND_VOLUME.md` | `7770da46b5c684add476ec286673d70d73f332fb5ac286d07cabcdaadc4eac43` | 60272 | 320 |
| 8 | `ledger_bound_20261109/_lb2_TEMPLATE.md` | `ba1dc5cc9fb35dbc3010a470909079fdd9afbd6fbea9cccdaed82b6dc317a425` | 42186 | 353 |
| 9 | `s604_attribution_20261108/S604_ATTRIBUTION.md` | `8e9a606752ce2fd4c3d279ba5bb4a54eba99bc83f8974921f3f5601aa1008237` | 27182 | 196 |
| 10 | `s604_attribution_20261108/_sa_ATTRIBUTION_S604.md` | `7241026122978426838d6c8ccaa8ea3335fe6213adef6bae10ab9c7aa83df2f2` | 17272 | 129 |
| 11 | `s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md` | `1e4ceb37187cd12601ad03cdc02f0cf2ee624d1f6870c03c0e35d84cbcb40cfc` | 36097 | 171 |
| 12 | `s604_verdict_entry_20261109/_ve_DRAFT_S609.md` | `058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec` | 18980 | 83 |
| 13 | `PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 | 382 |
| 14 | `GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 | 9758 |

与任务书【编排方指纹】14 件**逐位一致**；收尾再次重跑仍 `ALL_14_MATCH = True`（§6）。被核对象 = 第 1 件（43 处全量清单交付件）。

### 2.2 三个判定的独立复核（逐字比对证据 + 区块实测行号）

命令（本会话实跑，四条）：
`python -I -X utf8 "…/_rsv_verbatim.py"`、`python -I -X utf8 "…/_rs_verify.py"`、`python -I -X utf8 "…/_rsv_blocks2.py"`、`python -I -X utf8 "…/_rsv_blocks.py"`

#### 判定一：组① 逐字相同 —— **成立（EQUAL，差异字符数 0）**

| 行 | 字符数 | 整行 UTF-8 SHA256 |
|---|---:|---|
| `ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md:123` | 160 | `8daa70d7eac55d437fb5655dc71ca32b7b3714212a7b0c0e56f5f24731ec5ed8` |
| `ledger_appendix_20261108/_la_draft3_s604_gapdiff.md:25` | 160 | `8daa70d7eac55d437fb5655dc71ca32b7b3714212a7b0c0e56f5f24731ec5ed8` |

`_rsv_verbatim.py` 输出：`EQUAL = True`、`len(left)=160 chars / 330 bytes ; len(right)=160 chars / 330 bytes`、`DIFF_COUNT = 0 ; DIFF_POSITIONS = [] ; no differing codepoints`。**组① 与组② 不是同一句**：输出 `EQUAL = False`，首差异 `pos=0: left='-' (U+002D) right='3' (U+0033)`，其后 `pos1 ' '(U+0020)→'.'(U+002E)`、`pos3 '*'(U+002A)→'§'(U+00A7)`，`DIFF_COUNT = 160`。

组① 那一行在四份「可整段复制追加」载体中逐字相同（本会话 `_rsv_verbatim.py` 输出 `EQUAL_TO_A=True` 四行、`_rsv_ten.py` 输出 `IN_APPENDABLE_BLOCK = 6 distinct files = 6`）：`LEDGER_APPENDIX_DRAFT.md:123`、`_la_draft3_s604_gapdiff.md:25`、`LEDGER_BOUND_VOLUME.md:196`、`_lb_BOUND_VOLUME.md:129`，四者整行 SHA256 全为 `8daa70d7…`。**如实登记一个边界**：整行相同 ≠ 整段相同——本会话 `python -I -X utf8 -c` 实算 §607 正文段（`_rsv_blocks.py` 输出）：`LEDGER_APPENDIX_DRAFT.md:111-124` 与 `_la_draft3:13-26` 均 2707 字符、SHA256 `a758a87b31da39e740977dff05e315333e8fb336ac0d8cdd86866244cfdaab82`（与任务书【区块与标记】`LA_110_125`/`D3_13_26` 逐位一致）；而两件合订本正文区 `:182-199` / `:115-132` 各 2711 字符、SHA256 `ffea81a0e1ca9cdeb0adf0cf1bea164e702256d459685d18bcf913d9f04f358d`——差在块首/块尾各 2 个空行（行级比对：`BOUND` 首行 `len=0`，`LA` 首行即 `## §607…`），**同一句 = 那 160 字符整行，不是整段段落**。

#### 判定二：组② 区块内外 —— **成立（两行均块外 / §6.3 内）**

`_rs_verify.py` 本会话输出：`LEDGER_APPENDIX_DRAFT.md` 标记行 `:46/:61/:80/:92/:110/:125/:149/:179` ⇒ 四段块 `[(46,61),(80,92),(110,125),(149,179)]`；`:110` = `<!-- ============ 草案正文 3 逐字转录开始 ============ -->`、`:125` = 同类结束注释；`line 123 in [111,124]? True`、`line 215 in [111,124]? False`；`§6.3 heading line 211 = '### 6.3 未验项（全批汇总，如实、不补造）'`。`_lad_tpl.md` 块 `[(46,48),(67,69),(87,89),(113,115)]`（`_rsv_blocks2.py` 输出），`:151` 在 `:147` 起 §6.3、块外。

组② 逐字证据：`LEDGER_APPENDIX_DRAFT.md:215` vs `_lad_tpl.md:151` → `EQUAL = True`、各 101 字符 / 197 字节、SHA256 同为 `46adf10470d8778cab8adb44e953ee0206fb7eeac91c560b3a7e9cee6e477059`、`DIFF_COUNT = 0`。本会话独立全 lead/ 扫描 `python -I -X utf8 -c` 得组② 整行逐字同文 **5 份**（不是 2 份 +2 sandbox）：`LEDGER_APPENDIX_DRAFT.md:215`、`_lad_tpl.md:151`、`MINHARD_SET_CHECK.md:94`、以及 `_dnw_sandbox/` 与 `_dnv_sandbox36/` 的两份 `:215`；**5 份 `IN_BLOCK=False` 全部实测**，`IN_BLOCK = 0` ⇒ 入账污染 0 件（这是【复核】次要点 (a) 的更正，结论不变，见 §6.4）。

#### 判定三：组③ 无转录区块 —— **成立（0 标记命中）**

`_rs_verify.py` 本会话输出：`ATT bytes = 27182 lines = 195 marker-like hits = 0`（关键词含 `逐字转录 / 整段复制 / ↓↓↓ / ↑↑↑ / 草案正文 / 从这里开始 / 可整段复制追加 / 转录开始 / 转录结束`）；`ATT:1 = '# S604_ATTRIBUTION.md —— … 归属裁定（撰写终件）'`；`:171` 为 §6-3 缺口行，`blocks=[]`。`MINHARD_SET_CHECK.md:115-117` 同判「完全不适用」，并引 `S604_REFSYNC_FULL.md:85`/`:309` 自给「降级为行尾加注」出口。

#### 「随段进台账」逐组成立与否

| 组 | 逐字 | 转录区块实测 | 「随段进台账」 | 依据 |
|---|---|---|---|---|
| ① `:123 ≡ :25`（+ 合订本 `:196`/`:129`） | EQUAL / DIFF 0 | `[(110,125)]`、`[(11,28)]`、`[(181,200)]`、`[(114,133)]` 四块，均 `start < line < end` | **成立（HIGH）** | `LEDGER_BOUND_VOLUME.md:34`（本会话实读）「5 笔状态**全部「未入账、可整段复制追加、草案正文逐字照抄已验」**」；`:3`「不是台账、不入台账」；`MINHARD_SET_CHECK.md:237` 同判 |
| ② `:215 ≡ :151` | EQUAL / DIFF 0 | 两行 `IN_BLOCK=False`；四段区块止于 `:179` / `:115` | **不成立** | `S604_REFSYNC_FULL.md:126`（本会话实读）「`:215` **不在**待追加正文内，**不会随笔3 整段进永久台账**…属**草案自洽硬项，非入账污染**」；`MINHARD_SET_CHECK.md:99-103` 同判 |
| ③ `S604_ATTRIBUTION.md:171` | 非同句 | 全件 `blocks=[]` | **完全不适用** | 撰写终件、无「整段复制追加」通道；`MINHARD_SET_CHECK.md:115-117` |

⇒ 上一轮（甲）「三组里只有组① 真满足『会随整段进永久台账且已过时』」**成立**；但组① 的载体不是 2 件而是 **4 件**（编排方口径）。

### 2.3 复核 verdict 如实登记

任务书【复核】回件：`"verdict":"confirmed"`，`ranCommands: 44`，核心结论九项全通过、不 refuted；本会话按铁律「refuted 或 partial 标 unconfirmed」→ **本口径修正件对上一轮载体图核查回件的复核结论 = confirmed（不标 unconfirmed）**。同时如实登记【复核】列出的 5 处次要点更正（§6.4 逐条给本会话复算结果），以及另一个**不同对象**的状态：`S604_REFSYNC_FULL.md:292` 自述其**自身**「复核 verdict = partial ⇒ …本交付件整体登记为 unconfirmed」，`LEDGER_BOUND_VOLUME.md:34` 亦记「第 5 笔 §609 状态 unconfirmed」——那是 43 处清单交付件 / §609 笔的状态，**不等于**本件所复核的载体图回件，两者不可混称。

---

## 3 全量载体图（逐件逐行 + 是否进台账 + 判据）+ 13 件口径的差集

### 3.1 口径与实跑

- 编排方全量扫描口径（`lead/` dir-depth≤2、`.md`、两句精确串）：**18 件 / 70 行**（任务书【全量载体扫描】，`scanned: 623`、`dirs: 288`）。
- 本会话独立重跑同口径（`_rsv_diffset.py`、`_rsv_scope2.py`）：**18 件 / 73 行**，文件集合与编排方**完全一致**；多出的 3 行全在 `minhard_check_20261109/_mh_MINHARD_CHECK.md:206/:207/:253`。本会话实算该件现盘 44293 B / 299 行 / SHA256 `c31bf7f0de15697de0f5a448a3759104be103b232761bcf1da3de279c29cc20a`（字节数与编排方一致 ⇒ 非文件改动）；`_rs_verify.py` 输出 (d) 段逐行原文 + `needle present?` = `206 True True False` / `207 True True False` / `253 False True False`，三行确含 needle，均为「改前 / 建议改后 / 验收」引述。编排方未列这 3 行的**具体 predicate 未随任务书下发，按「未验」登记**，不臆断。
- 本会话 `python -I -X utf8 "…/_rsv_scope2.py"` 用 mtime 截止 12:19:00 复原撰写时点语料：`.md` 总 942 / d≤2 = 622，重扫得 `18 件 / 73 行`（d2）、`22 件 / 79 行`（无深度上限）——与回件一致。**现盘**因 `_rs_CARRIER_MAP.md`（12:20:40，自引 7 行）与并行新件，重扫为 `19 件 / 80 行`（d2）、`23 件 / 86 行`（无上限）；差值 = 作者自引产物，非真实漏载体（脚本无自排除，如实登记）。
- 编排方 `dirs=288` 的统计口径**未验**：本会话实算含 scoped-md 目录数 / d≤2 全部目录 / 总目录三值均不等（上一轮 221 / 355 / 1303；本轮因并行写入浮动为 224 / 360 / 1310）。不影响 623/18 结论。

### 3.2 转录区块实测行号（锚定正则：整行必须是标记行）

判据：START/END 正则必须**整行命中**（`_rs_carrier_scan.py:61-72`），只认开区间 `start < line < end` 为「随整段进台账」；标记不成对 ⇒ `UNKNOWN: 需人工复核`，绝不猜。本会话 `python -I -X utf8 "…/_rsv_blocks2.py"` 与直导 `blocks_of()` 双向实测：

| 件 | 转录区块 `(start,end)` |
|---|---|
| `LEDGER_APPENDIX_DRAFT.md` | `[(46,61),(80,92),(110,125),(149,179)]` |
| `_la_draft3_s604_gapdiff.md` | `[(11,28)]` |
| `_lad_tpl.md` | `[(46,48),(67,69),(87,89),(113,115)]`（`:87-89` 为 `__DRAFT3__` 占位符） |
| `LEDGER_BOUND_VOLUME.md` | `[(123,142),(153,169),(181,200),(212,246),(258,276)]` |
| `_lb_BOUND_VOLUME.md` | `[(57,76),(87,103),(114,133),(144,178),(189,207)]` |
| `_lb2_TEMPLATE.md` | `[(123,127),(138,142),(154,158),(170,174),(186,190)]`（`:154-158` 为 `@@BODY_3@@`） |
| `S604_VERDICT_ENTRY_DRAFT.md` | `[(68,84)]` ← 直导 `blocks_of()` 输出 `START lines: [(68, '↓↓↓ 草案正文 ↓↓↓')]`、`END lines: [(84, '↑↑↑ 草案正文结束 ↑↑↑')]` |
| `_ve_DRAFT_S609.md` | `[(11,27)]` |

**如实登记一处检测器差异**：`_rsv_blocks2.py` 的宽松前缀判据把 `S604_VERDICT_ENTRY_DRAFT.md:66`（`### 4.1 草案正文（整段复制「↓↓↓」至「↑↑↑」…）`，是**说明行不是标记行**）误判为 START，输出 `pairs=[(66,None)]`；主脚本锚定正则给出正确 `[(68,84)]`（本会话直导验证，输出 `blocks_of : ([(68, 84)], [])`），与 `_rs_carrier_scan.py` A 段 `entry=APPENDABLE_BLOCK [(68, 84)]` 一致。本件采用锚定正则结果；这正是 R4「整行命中、不靠子串」的理由。

### 3.3 全量载体图（18 件 / 73 行；「编排方行」列给 70 行口径）

下表 `role` / `risk` 取自本会话实跑 `python -I -X utf8 "…/_rs_carrier_scan.py" --needle … --max-depth 2 --ext .md`（输出 `_fix_d2_out.txt`，`EXIT=0`、`SELF_TEST = PASS` 6/6）。`needs_fix = (role == ASSERTION) AND (risk == HIGH)`。

| # | 件（相对 `lead/`） | 编排方行 / 我实跑行 | 命中行逐行判据（role ⇒ 是否随段进台账） |
|---|---|---|---|
| 1 | `ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md` | 123, 215 | `:123` **ASSERTION / HIGH `[(110,125)]` / needs_fix=True**；`:215` ASSERTION / NONE（`:211` 起 §6.3，块外） |
| 2 | `ledger_appendix_20261108/_la_draft3_s604_gapdiff.md` | 25 | `:25` **ASSERTION / HIGH `[(11,28)]` / needs_fix=True** |
| 3 | `ledger_appendix_20261108/_lad_tpl.md` | 151 | `:151` ASSERTION / NONE（§6.3 块外） |
| 4 | `ledger_bound_20261109/LEDGER_BOUND_VOLUME.md` | 179, 196, 270, 288 | `:179` REFUTING_QUOTE / NONE；`:196` **ASSERTION / HIGH `[(181,200)]` / needs_fix=True**；`:270` REFUTING_QUOTE / **HIGH `[(258,276)]`**（进台账但是§609否定句，needs_fix=False）；`:288` QUOTED / NONE |
| 5 | `ledger_bound_20261109/_lb2_TEMPLATE.md` | 152, 202 | `:152` REFUTING_QUOTE / **INDIRECT**（`@@BODY_n@@` 重建注入）；`:202` QUOTED / INDIRECT；两行均块外，骨架本身不含字面句 |
| 6 | `ledger_bound_20261109/_lb_BOUND_VOLUME.md` | 112, 129, 201, 216, 226 | `:112` REFUTING_QUOTE / NONE；`:129` **ASSERTION / HIGH `[(114,133)]` / needs_fix=True**；`:201` REFUTING_QUOTE / **HIGH `[(189,207)]`**（否定句）；`:216` REFUTING_QUOTE / NONE；`:226` QUOTED / NONE |
| 7 | `minhard_check_20261109/MINHARD_SET_CHECK.md` | 34, 75, 79, 94, 164, 207, 214, 238 | `blocks=[]` 全 NONE：`:34` REFUTING_QUOTE、`:75` ASSERTION（组① 逐字转录）、`:79` REFUTING_QUOTE、`:94` ASSERTION（组② 逐字转录）、`:164` REFUTING_QUOTE、`:207` REFUTING_QUOTE、`:214` UPDATED_SAMPLE、`:238` REFUTING_QUOTE |
| 8 | `minhard_check_20261109/_mh_MINHARD_CHECK.md` | 49, 52, 66, 125, 146, 187, 196, 197 **+ 我 206, 207, 253** | `blocks=[]` 全 NONE；`:49/:66` QUOTED、其余 REFUTING_QUOTE；+3 行见 §3.1 |
| 9 | `s604_refsync_20261109/S604_REFSYNC_DRAFT.md` | 58, 65, 102, 108, 121, 127 | `blocks=[]` 全 NONE：`:58/:65` REFUTING_QUOTE、`:102/:121` ASSERTION（逐字引文）、`:108` UPDATED_SAMPLE、`:127` ANALYSIS_MENTION |
| 10 | `s604_refsync_20261109/_rs_REFSYNC_DRAFT.md` | 26, 32, 36, 126, 131, 135, 144 | `blocks=[]` 全 NONE：`:26/:126` REFUTING_QUOTE、`:32/:131/:144` ASSERTION、`:36` ANALYSIS_MENTION、`:135` UPDATED_SAMPLE |
| 11 | `s604_refsync_full_20261109/S604_REFSYNC_FULL.md` | 125, 127, 143, 206 | `blocks=[]` 全 NONE，全部 REFUTING_QUOTE（原文逐字 / 改后逐字 / grep 验收） |
| 12 | `s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md` | 130, 131, 132, 133, 206, 319 | `blocks=[]` 全 NONE，全部 REFUTING_QUOTE |
| 13 | `s604_script_gap_20261109/S604_SCRIPT_GAP.md` | 55 | `blocks=[]` NONE、QUOTED（对 `S604_GAP_RECHECK.md:101` 的逐字引文；`S604_REFSYNC_FULL.md:142-145` 判「保留」） |
| 14 | `s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md` | 58, 79, 94, 107, 150, 151 | `:58/:94/:107/:150/:151` REFUTING_QUOTE / NONE；`:79` REFUTING_QUOTE / **HIGH `[(68,84)]`**（§609 否定句，会进台账但 needs_fix=False） |
| 15 | `s604_verdict_entry_20261109/_ve_DRAFT_S609.md` | 22, 46, 53, 69, 70 | `:22` REFUTING_QUOTE / **HIGH `[(11,27)]`**（§609 否定句）；其余 REFUTING_QUOTE / NONE |
| 16 | `slowframe_r3_20261108/S604_GAP_RECHECK.md` | 101 | `blocks=[]` NONE、ASSERTION（独立调查报告） |
| 17 | `slowframe_r3_20261108/_r3_GAPDIFF_RECHECK.md` | 63 | `blocks=[]` NONE、ANALYSIS_MENTION |
| 18 | `slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md` | 91, 127 | `blocks=[]` NONE：`:91` ANALYSIS_MENTION、`:127` ASSERTION（43 清单外同类句，`MINHARD_SET_CHECK.md:164` 已登记） |

**严格交集（ASSERTION ∧ HIGH）= 4 行 / 4 件**：`LEDGER_APPENDIX_DRAFT.md:123`、`_la_draft3_s604_gapdiff.md:25`、`LEDGER_BOUND_VOLUME.md:196`、`_lb_BOUND_VOLUME.md:129`。本会话 `_fix_d2_out.txt` B 段输出 `occurrences = 4 ; distinct files = 4`。四行逐字相同（§2.2，160 字符 / `8daa70d7…`）⇒ 「改了 :123/:25 却漏两件合订本，Leader 从合订本复制时错句照样进永久台账」是本轮最重一条（`MINHARD_SET_CHECK.md:237` 同判）。

**组① 整行逐字同文全 lead/ 共 10 行 / 9 文件**（本会话 `_rsv_ten.py` 输出 `COUNT = 10 distinct files = 9`、`IN_APPENDABLE_BLOCK = 6 distinct files = 6`）：上述 4 行 + `MINHARD_SET_CHECK.md:75`、`S604_REFSYNC_DRAFT.md:102`、`_rs_REFSYNC_DRAFT.md:131/:144`（后 6 行 `IN_BLOCK=False`）+ 2 份 sandbox 的 `LEDGER_APPENDIX_DRAFT.md:123`（`IN_BLOCK=True`）。**如实更正**：`_rs_CARRIER_MAP.md:213` 写「分布 8 个文件」与其自身 `_rs_verbatim_out.txt:5-14` 的 10 行 / 9 文件不符（【复核】次要点 (b)，本会话复算确认 9 文件），本件按 9 文件登记；回件 `carrierMap` 的 10 行枚举本身正确。

### 3.4 13 件口径的差集

命令：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_final.py"`（本会话实跑）；`python -I -X utf8 "…/_rsv_diffset.py"`（独立复算，输出 `carrier files=18 hit lines=73`）。13 件清单逐件转录自 `S604_REFSYNC_FULL.md:42-54`（本会话实读）。

- `13 ∩ 18 = 6 件`：`LEDGER_APPENDIX_DRAFT.md`、`_la_draft3_s604_gapdiff.md`、`_lad_tpl.md`、`S604_SCRIPT_GAP.md`、`S604_GAP_RECHECK.md`、`SLOW_WINDOW_LIMITS.md`。
- `13 − 18 = 7 件`（过时点是**别的短语**，如「无法定谳」「落盘副本」「不可定位」，不是这两句载体）：`S604_ATTRIBUTION.md`、`_sa_ATTRIBUTION_S604.md`、`_sg_FINDINGS.md`、`S604_EXCLUSIVITY.md`、`_ex_EXCLUSIVITY.md`、`RULING_DIRECTION.md`、`_dr_RULING.md`。⇒ 两口径**不是包含关系，是不同维度**。
- **`18 − 13 = 12 件漏掉的载体`**（`_rs_final.py` 逐行 `MISSED` 输出）：

```
ledger_bound_20261109/LEDGER_BOUND_VOLUME.md            ← 真·入账污染（:196 HIGH）
ledger_bound_20261109/_lb_BOUND_VOLUME.md               ← 真·入账污染（:129 HIGH）
ledger_bound_20261109/_lb2_TEMPLATE.md                  ← @@BODY_3@@ 重建/旧指纹登记风险
s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md   ← §609 正文（:79 否定句，HIGH 但 needs_fix=False）
s604_verdict_entry_20261109/_ve_DRAFT_S609.md             ← §609 正文（:22 否定句，HIGH 但 needs_fix=False）
s604_refsync_20261109/S604_REFSYNC_DRAFT.md
s604_refsync_20261109/_rs_REFSYNC_DRAFT.md
s604_refsync_full_20261109/S604_REFSYNC_FULL.md
s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md
minhard_check_20261109/MINHARD_SET_CHECK.md
minhard_check_20261109/_mh_MINHARD_CHECK.md
slowframe_r3_20261108/_r3_GAPDIFF_RECHECK.md
```

其中**只有前 2 件是「会随整段进台账且表述旧」的实质漏项**；第 3 件是模板指纹/重建风险；§609 两件 + 合订本 `:270`/`:201` 是**矛盾的另一半（引该句来否定它）**，不是过时载体；其余 7 件是分析/校核/转述件。把它们与实质漏项混算会虚增件数。

### 3.5 全 lead/ 无深度上限补充（4 件 sandbox 副本）

本会话 `python -I -X utf8 "…/_rs_carrier_scan.py" --needle … --ext .md`（无 `--max-depth`，输出 `_fix_md_out.txt`）：`scanned files = 947`、现盘 `23 件 / 86 行`（撰写时点语料 `22 件 / 79 行`）、B 段 `occurrences = 6 ; distinct files = 6`。多出的 4 件全是 `gate_doc_name_fix_20261109/` 下 dir-depth=3 的逐字副本，本会话 hashlib 实算：

```
_dnv_sandbox36/…/LEDGER_APPENDIX_DRAFT.md  sha256 724458d9… / 45719 B   (:123,:215)
_dnw_sandbox/…/LEDGER_APPENDIX_DRAFT.md     sha256 724458d9… / 45719 B   (:123,:215)
_dnv_sandbox36/…/S604_SCRIPT_GAP.md        sha256 593c7a3e… / 20271 B   (:55)
_dnw_sandbox/…/S604_SCRIPT_GAP.md           sha256 593c7a3e… / 20271 B   (:55)
```

两件 `:123` 在 `[(110,125)]` 块内 ⇒ 全树严格交集 6 件（`MINHARD_SET_CHECK.md:180` A′ 同数）。**sandbox 是否具实际复制效力未验**（`:287` 亦标未验），按「存在风险」登记，不宣称一定发生。

---

## 4 扫描口径为什么错（扫描范围声明 + 圈定维度 + 为何漏 ledger_bound + 教训）

### 4.1 `S604_REFSYNC_FULL.md` 自己写的扫描范围声明（本会话实读）

- `:11`：「`S604_VERDICT_ENTRY_DRAFT.md` §4.2（本会话实读 `:88-131`）列出…引用面 **13 件 43 处**（严数）…本件只补**剩余 30 处**」。
- `:12`（边界）：「**只出草案、不改任何件**——不修改既有 13 件的任何一字，也不修改 `lead/s604_verdict_entry_20261109/`、`lead/s604_refsync_20261109/` 两个**只读域**，更不改两台账」。
- `:14`：「§4.2 的 43 处清单原文是本会话第一步实读的 `S604_VERDICT_ENTRY_DRAFT.md:88-131`…**非凭任务书转述**」。
- `:36-55`：「43 处完整清单（实读 §4.2 `:94-125`，按 file:line 严数展开 = 13 件 43 点）」，逐件 13 行表。
- `:90`（`S604_VERDICT_ENTRY_DRAFT.md`，本会话实读）：「按 file:line 严数 = **13 件 43 处**…整理回件原清单「6 件 13 处」系其自身口径…**复核回件补 11 组；本交付轮全树扫描另查得 6 行/组**…每处均经本会话直读核实」。
- `:131`（同件，**扫描覆盖诚实账**）：「全树失效语扫描两轮（12+6 个变体短语），命中除上表 13 件外另有…约 20 处——抽读 3 处…其余未逐行复读、**按目录主题与成文日期**判非本议题；**此项为抽样判断，非全量亲读**」。

⇒ **13 件不是一次扫描得出的边界**，而是「§4.2 那张 32 行表按 `file:line` 展开后的去重文件集合」，上游又是「6 件 13 处 → 补 11 组 → 补 6 行/组」的**三轮人工累加**。

### 4.2 圈定维度：不是写域白名单，也不是文件名模式

是「人工逐处列举 + 按历史写域归并」的**施工清单继承**：`S604_REFSYNC_DRAFT.md:10`（本会话实读）「编排方指定的 13 处失效/过时引用分布在 **5 个历史写域的 6 件**（8 个行位文件）中」；`S604_REFSYNC_FULL.md:275` 把 13 件当作「**13 次历史件指纹变更**」的执行单位；`:319-320` 用「全量方案 13 件 13 次 − 最小硬项 4 次 = 省 9 次」算节省。⇒ 13 件是「**要动哪些历史件**」，被反向当成「**过时表述存在于哪些件**」。它把只读域（`s604_verdict_entry_20261109/`、`s604_refsync_20261109/`、`s604_refsync_full_20261109/`、`minhard_check_20261109/`）天然排除在「待改件」之外，于是这些域里成打的逐字转录/引文命中根本不进清单。

### 4.3 为什么漏 `ledger_bound` —— **不是「更晚 / 圈定时不存在」，也不是没扫到**

本会话 `python -I -X utf8 -c`（`os.path.getmtime`）实算时间线：

```
07:46:48  S604_VERDICT_ENTRY_DRAFT.md   （13 件口径的定义处 §4.2）
08:31:24  S604_REFSYNC_DRAFT.md         （原 13 处同步草案）
10:11:15  _lb_BOUND_VOLUME.md           （ledger_bound 最早成件）
10:19:36  _full_checks_out.txt          （43 清单自己的 R2 全树 grep 输出）
10:26:57  S604_REFSYNC_FULL.md          （43 处全量清单交付件）
10:28:50  _lb2_TEMPLATE.md
10:29:52  LEDGER_BOUND_VOLUME.md
12:02:38  MINHARD_SET_CHECK.md
```

**关键实证**：本会话 `python -I -X utf8 -c` 读 `lead/s604_refsync_full_20261109/_full_checks_out.txt:35-55`，输出 `:35| TERM '不能定位当年错误步骤' -> 65 hits`，其中 `:48-52` 逐行是 `lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md:112 / :129 / :201 / :216 / :226`，`:53-55` 是 `_lb_build.py:175 / :223 / :249`。`S604_REFSYNC_FULL.md:278`（本会话完整实读）白纸黑字：「**另全树 grep 命中 `ledger_bound_20261109`…等多处旧指纹登记**（本会话实跑，输出见 §5.4 R15）」。

⇒ **10:19 的 R2 全树 grep 已经打到 ledger_bound**，且早于 43 清单（10:26:57）7 分钟；`_lb_BOUND_VOLUME.md`（10:11:15）早于清单 15 分钟。是**扫描结果被继承自 §4.2 的 13 件人工清单过滤掉**：65 命中只被用作「改文安全性 / 无第三方逐字引用」旁证（`:126`、`:295`、`:319`），从未用来**扩充载体集合**；`ledger_bound` 只以「旧指纹 errata 登记面」身份被提及（`:278`），其「同一句被逐字收进可整段复制区块」的性质完全没被判。

**如实收窄一处措辞**（【复核】次要点 (d)）：`LEDGER_BOUND_VOLUME.md` 编译本 mtime `10:29:52` **确实晚于** 43 清单 3 分钟，所以「因为更晚所以漏」只对这 1 件成立；「不是更晚 / 不是没扫到」的举证由**源件** `_lb_BOUND_VOLUME.md`（10:11:15 且已被 65 命中扫到）+ `:278` 自认承担，整体结论（不是「更晚/不存在/没扫到」）仍成立，但不写成「三件全部更早」。

### 4.4 一般性教训（≥2 条）

1. **扫描集合被施工集合取代（selection-by-actionability）**：先有「要改哪些件」的清单，再拿它当「这句话在哪些件」的答案。凡只读域、后建域、分析件、复核件里的逐字副本一律不可见；而**后建的合订本/汇编件恰恰是最危险的载体**（自带「可整段复制追加」）。⇒ 扫描口径必须与被核结论的执行口径解耦，扫描全集由内容定，施工清单只能是它的子集且须明示「差集 = 未处置载体」。
2. **grep 命中 ≠ 载体登记（结果用途错配）**：同一份 65 命中输出被用来证「改文安全」却没被用来建载体图；`S604_VERDICT_ENTRY_DRAFT.md:131` 还把约 20 处额外命中按「目录主题 + 成文日期」抽样判无关。⇒ 每次全树 grep 必须同时产出「命中全集」与「判为无关的逐行理由」，**抽样判断不得充当排除依据**。
3. **按写域/日期/文件名过滤 = 对副本免疫**：`ledger_bound_20261109/`、`_dnw_sandbox/`、`_dnv_sandbox36/` 都是既有件的逐字副本，同哈希（`724458d9…/45719`、`593c7a3e…/20271` 本会话实算）。**内容寻址才认得出来，路径寻址认不出来**。
4. **变体短语靠人工列 + 无负控**：`「」` 与 `『』` 命中集合不同（本会话 16/41 vs 14/28 文件/行）；12+6 变体仍靠人工列。⇒ 必须有负控样本，否则漏了哪一类自己不知道。
5. **同文去重按「文件」而非「出现点」**：`:123≡:25` 被当作「1 处」，于是「2 对同文重复 ⇒ 41 独立表述」。但组① 全 lead/ 有 10 份逐字同文、其中 6 份在可追加块内；按文件去重让「改 2 件就够」看似成立。

---

## 5 修正后的扫描规则、自检脚本、引用否定排除 + 分口径件数结论

### 5.1 可执行规则 R1–R6（实现于 `lead/refsync_scope_20261109/_rs_carrier_scan.py`）

| 规则 | 内容 |
|---|---|
| **R1 内容寻址全集** | `U = { f \| f 在 ROOT=`整个 lead/` 下、深度**无上限**、扩展名白名单、非二进制 }`。禁止按 目录名 / 写域 / 成文日期 / 文件名模式 预过滤；**绝不拿 prior report 的文件列表当扫描全集**；先按内容过滤（`file_bytes` 含 needle 才入候选，副本自动入选）；逐文件登记 `sha256 + 字节数 + 命中行号` 与 `scanned-files` 计数，使重跑可复核。 |
| **R2 以句为单位** | 唯一键 = `(abs_path, line_no)`；**文件只是派生分组**（先得 `(file,line,role,entry,risk)` 元组，再 `GROUP BY file` 出件数）。同哈希 sandbox 副本是**不同键**，单列 `SANDBOX_COPY` 组标「效力未验」，不合并、不静默丢弃。**以句为单位而非以件为单位**的理由：① 组① 整行 160 字符在 lead/ 有 10 份逐字同文 / 9 文件，按文件计会压成 9 个、按「同文去重」再压成 1 处；② **入账风险是行级属性**——同一 `LEDGER_APPENDIX_DRAFT.md` 的 `:123`（块内 HIGH）与 `:215`（§6.3 NONE）风险相反，`LEDGER_BOUND_VOLUME.md` 的 `:196`（块内过时断言）与 `:270`（块内否定句）风险相反，按文件判必然误判其一；③ 「2 件 / 4 件 / 6 件 / 18 件 / 22 件」都可由同一批元组按谓词重算，不再随口径漂移。 |
| **R3 显式逐字比对** | 「同一句」必须打印 `EQUAL / NOT-EQUAL` + 首个差异字符的 `U+xxxx` 码位 + 整行 SHA256；不许肉眼判「一样」（§2.2 给足证据）。 |
| **R4 转录区块判 HIGH** | START/END 正则**整行命中**锚定标记行；只认开区间 `start < line < end` ⇒ `HIGH: 随整段进台账`；`@@BODY_n@@` ⇒ `INDIRECT: 重建时由源件注入`；块外 / 无块 / 独立终件 ⇒ `NONE`；**标记不成对 ⇒ `UNKNOWN: 需人工复核`，绝不猜**（§3.2 的 `:66` 误判即反例）。 |
| **R5 引用否定不删除，打 ROLE** | `needs_fix = (role == ASSERTION) AND (risk == HIGH)`；详见 §5.3。 |
| **R6 负控自检** | 6 个已知肯定/否定样本必须分别判 `ASSERTION` / `REFUTING_QUOTE`，否则 `EXIT=1`。 |

### 5.2 可复用自检脚本（本会话实跑命令 + 输出）

脚本：`lead/refsync_scope_20261109/_rs_carrier_scan.py`（只读、只打印 stdout，`validated_root()` 用 `os.path.commonpath` 把 root 限制在仓库内；不写任何文件，输出记录由调用方重定向到本写域）。

| # | 本会话实跑命令（均 `python -I -X utf8` + 绝对路径，两句 needle） | 输出（本会话） |
|---|---|---|
| 1 | `python -I -X utf8 "…/_rs_carrier_scan.py" --needle "只能判「不可复现」" --needle "不能定位当年错误步骤" --max-depth 2 --ext .md > "…/_fix_d2_out.txt"` | `EXIT=0`；`scanned files = 627 ; carrier occurrences = 80 ; distinct files = 19`（现盘，含自引；撰写时点 622/73/18）；B 段 `occurrences = 4 ; distinct files = 4`；`SELF_TEST = PASS`（6/6，含 `:215 want=ASSERTION got=ASSERTION`、`_ve_DRAFT_S609.md:22 want=REFUTING_QUOTE got=REFUTING_QUOTE`） |
| 2 | 同上，去 `--max-depth`（无深度上限 `--ext .md`）`> "…/_fix_md_out.txt"` | `EXIT=0`；`scanned files = 947 ; carrier occurrences = 86 ; distinct files = 23`（撰写时点 942/79/22）；B 段 `occurrences = 6 ; distinct files = 6`（+2 sandbox）；`SELF_TEST = PASS` |
| 3 | 同上，默认全扩展名 `.md,.txt,.py,.json` 无深度上限 `> "…/_fix_all_out.txt"` | `EXIT=0`；`scanned files = 5500 ; carrier occurrences = 2429 ; distinct files = 81`（**仅供审计，不作施工数**；上一轮撰写时点 5442 / 1052 / 67，差值含本写域与并行新件）；B 段仍 `6 / 6`；`SELF_TEST = PASS` |
| 4 | 负控探针 `python -I -X utf8 "…/_rs_carrier_scan.py" --needle "三选一不可定谳" --ext .md --max-depth 2 --no-self-test` | `scanned files = 627 ; carrier occurrences = 13 ; distinct files = 5` ⇒ 换 needle 结果随之变化，**脚本不硬编码结论**（【复核】⑦ 的复现） |

全量逐行输出 A 段（每文件每行的 `role / risk / needs_fix / entry / verbatim(canonical==line) / 差异码位 / SHA256`）、B 段（严格交集）、C 段（非修复项 + 角色直方图）、D 段（排除逻辑）、E 段（负控）分别在 `_fix_d2_out.txt` / `_fix_md_out.txt` / `_fix_all_out.txt` 在盘。上一轮在盘输出另有 `_rs_carrier_scan_d2_out.txt`（3624 行）、`_rs_carrier_scan_md_out.txt`（528 行）、`_rs_carrier_scan_out.txt`（5929 行）。

### 5.3 如何排除「引用该句来否定它」的文件（R5，不是删掉，是打角色）

实现在 `_rs_carrier_scan.py:164-189` 的 `classify_line()`：① 求 needle 在行内位置，再求成对引号跨度（`「」`/`『』`/反引号/`“”`）与 `>`、`|` 引用前缀；needle 落在引号跨度内 ⇒ 引文候选；② 同行含否定/更新词表（`不再成立 / 过时 / 已定谳 / 已定位 / 被推翻 / 取代 / 自本节起 / 改前 / 改后 / 逐字 / grep / 命中 / 验收 / 复核 / 未验项 / …`）⇒ `REFUTING_QUOTE` 或 `NEGATED_CITATION`；③ 「改后样例」无引号但含 `2026-11-09 更新 / 错误步骤已定谳为 / 改为：` ⇒ `UPDATED_SAMPLE`；④ 纯命令/校核行 ⇒ `ANALYSIS_MENTION`；⑤ **只有裸断言**（无引号包裹、无否定词）才是 `ASSERTION`；⑥ `needs_fix` 必须同时满足 `ASSERTION` 且 `risk = HIGH`。

本会话 `python -I -X utf8 "…/_rsv_r5.py"` 直导 `classify_line` 11 例输出（节选）：真实 `LEDGER:123` → `ASSERTION`（`neg=[]`、`vline=True`）；真实 `_ve_DRAFT_S609.md:22` 与 `LEDGER_BOUND_VOLUME.md:270` → `REFUTING_QUOTE`（`neg=['不再成立','过时','已定谳','已定位','被推翻','取代','自本节起',…]`）；真实 `LEDGER:215` → `ASSERTION`（但 `IN_BLOCK=False` ⇒ `needs_fix=False`）。`_fix_d2_out.txt` A 段实测：`:79`（`S604_VERDICT_ENTRY_DRAFT.md`）、`:22`、`LEDGER_BOUND_VOLUME.md:270`、`_lb_BOUND_VOLUME.md:201` 四条**在可追加块内的否定句**均 `role=REFUTING_QUOTE / risk=HIGH / needs_fix=False`，**完整保留在 A 段（不隐瞒 §609 正文会进台账），但不混进修复件数**。反向亦成立：`:215` 是裸断言却因块外被正确排除。

**如实登记一个已知局限**（【复核】次要点 (e)）：`NEG_LEX` 是整行子串表，任一 `复核 / grep / 逐字 / 命中 / 验收 / 未验项 / 过时 / 改前 / 不再成立` 即可把**裸断言**翻成 `ANALYSIS_MENTION`（`_rsv_r5.py` 例 E「…待复核。」与例 F「…见 grep 结果。」均复现为 `ANALYSIS_MENTION`）——这是假阴性路径。本会话逐条核过 `_fix_d2_out.txt` 中 B 段 4 条 `ASSERTION` 行 `neg=[]` 全部未受影响，故本语料结论不变；但 **6 个负控未覆盖此假阴性路径，属未验/待加固项**，不宣称脚本对任意语料免疫。

### 5.4 分口径件数结论

#### (a) 严格交集（「随段进台账」∩「已定谳但表述旧」）

| 范围 | 件数 | 具体 |
|---|---:|---|
| **13 件口径内** | **2 件** | `LEDGER_APPENDIX_DRAFT.md:123`、`_la_draft3_s604_gapdiff.md:25`（`MINHARD_SET_CHECK.md:179` A 口径同数） |
| **编排方全量口径**（lead/ d≤2、md） | **4 件** | 上述 2 件 + `LEDGER_BOUND_VOLUME.md:196` + `_lb_BOUND_VOLUME.md:129`（本会话 `_fix_d2_out.txt` B 段 `4/4`） |
| **全 lead/ 无深度上限** | **6 件** | 上述 4 件 + `_dnw_sandbox/` 与 `_dnv_sandbox36/` 的 `LEDGER_APPENDIX_DRAFT.md:123`（本会话 `_fix_md_out.txt` B 段 `6/6`；`MINHARD_SET_CHECK.md:180` A′ 同数；sandbox 效力未验） |

**主答案 = 4 件**（编排方指定口径）。「最小硬项 4 件」这个数字巧合地仍对，但**内容完全不同**：`S604_REFSYNC_FULL.md:319` 原建议的 4 件是 `{LEDGER_APPENDIX_DRAFT, _la_draft3, _lad_tpl, S604_ATTRIBUTION}`（含两组不成立/不适用的硬度），正确的 4 件是 `{LEDGER_APPENDIX_DRAFT, _la_draft3, LEDGER_BOUND_VOLUME, _lb_BOUND_VOLUME}`。`_lad_tpl.md` 只余 `INDIRECT` 指纹登记风险，`S604_ATTRIBUTION.md` 完全不在交集内。

#### (b) 全量载体

| 口径 | 文件数 | 行数 |
|---|---:|---:|
| 编排方全量扫描（lead/ d≤2、md、两句精确串） | **18** | 70 |
| 本会话独立重跑（同口径，OR-of-two-exact-strings，**撰写时点语料**） | **18** | **73**（+3 见 §3.1） |
| 全 lead/ 无深度上限、md（撰写时点语料） | **22** | 79 |
| 现盘（含本写域自引与并行新件）d≤2 / 无上限 | **19 / 23** | **80 / 86** |
| 全 lead/ 无上限、`.md/.txt/.py/.json`（现盘） | **81** | 2429 出现点（仅供审计，不作施工数） |

#### (c) §609 同批入账的冲突文本（逐字）

命令：`python -I -X utf8 "…/_rs_final.py"`（本会话实跑，Step 5c 段原样输出两行）。

- **§607**（`_la_draft3_s604_gapdiff.md:25`，160 字符 / SHA256 `8daa70d7eac55d437fb5655dc71ca32b7b3714212a7b0c0e56f5f24731ec5ed8`；经 `:123` / 合订本 `:196` / `:129` 四份逐字同文进台账）：
  > `- **边界（如实）**：§604 内联生成脚本未落盘（:9751-9755 两次自认），**只能判「不可复现」、不能定位当年错误步骤**；§603 项（:9673/:9680 ratio_max=0.9831 等）未核；本节只登记复算事实与可引用边界，**台账 :9704-9729 原文是否修订由台账所有者裁决**。`
- **§609**（`_ve_DRAFT_S609.md:22`，711 字符 / SHA256 `ae80c41095d061b0e7d03e54894c6ff7746f82b102f1607712c446c319709b29`；`S604_VERDICT_ENTRY_DRAFT.md:79` 同文，合订本 `:270`/`:201` 副本）：
  > `…其边界句「只能判『不可复现』、不能定位当年错误步骤」（:123）**自本节起不再成立**——错误步骤已定位（dur 字典错位），该句属被本节取代的过时表述，如何修订留台账所有者裁决。`

**逐字比对（不是「看着一样」）**：本会话 `python -I -X utf8 -c` 输出 `607:25 len= 160 sha= 8daa70d7…`、`609:22 len= 711 sha= ae80c410…`、`EQUAL = False`、`DIFF_COUNT(common prefix) = 156`，首差异 `pos=4 left='边' U+8FB9 right='与' U+4E0E`；引号码位实测 `607:25 quote marks = [(50,'「',U+300C),(55,'」',U+300D)]`、`609:22` 前 8 个含 `(165,'『',U+300E),(170,'』',U+300F)`；`N1 in 607 = True`、`V1 in 609 = True` ⇒ **两行不是同一句，且用了不同引号变体**，但都含 `不能定位当年错误步骤`。

**直接冲突**：§607 断言「**不能定位当年错误步骤**」，§609 断言「该句**自本节起不再成立**、**错误步骤已定位（dur 字典错位）**」；§609 还把 `:123` 这个**草案里的行号**当作台账内可指认对象，追加后该行号在 GOAL 里并不存在，指认失效。`MINHARD_SET_CHECK.md:238` 同判「GOAL 台账内两节互斥」；`LEDGER_BOUND_VOLUME.md:46` 把「笔3 §607 ↔ 第 5 笔 §609」列为唯一「建议成组」的一对。

#### (d)「现在改仍来得及」的依据

`python -I -X utf8 "…/_rs_final.py"`（本会话实跑）两台账逐项扫描：

| 件 | 字节 / SHA256（本会话） | `^## §60[5-9]` | `§60[5-9]` | `码形定谳` / `dur 字典` / `512655` | 两句 needle |
|---|---|---:|---:|---:|---:|
| `GOAL_THREE_TARGETS_20261018.md` | 759518 / `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 0 | 0 | 0 / 0 / 0 | 0 / 0 |
| `PENDING_DECISIONS.md` | 52419 / `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 0 | 0 | 0 / 0 / 0 | 0 / 0 |

GOAL 最后一个 `^## §` 头 = `:9687 ## §604 …`（输出 `^## §604\b hits=1 [9687]`），9757 行；`PENDING_DECISIONS.md` 无 `^## §` 头。两件 SHA256 与【编排方指纹】逐位一致 ⇒ **两台账自基线未变，§605–§609 五笔全部尚未入账**；污染只会在 Leader 动笔「整段复制追加」时发生，此刻改 4 份可复制载体仍是改**写域草案**（不是改台账正文，授权层级不同）。

**三条限定**（`MINHARD_SET_CHECK.md:161,203-204,287,288`）：① 改 `:25` 后 `d5dc8f97…/7703` 与 `e9842d41…/4894` 的旧指纹登记面须同批 errata（`:161` 列十余点，`:288` 自认未做全树全量反链枚举）；② 执行顺序宜 §607 四载体先修（或同批并明确两节互引）再追加 §609（`:204`）；③ **Leader 究竟从哪份载体复制入账属编排方裁决事实，本会话无从得知**，本件只登记「存在该风险」，不宣称一定发生。

---

## 6 复核回件（绑定行）+ 未改既有件声明 + 未验项

### 6.1 绑定行（被核对象 = `lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md`）

被核对象 SHA256 = 8ccf9866ebd7860f03d71e939960e018fd0cfbbe6b94add04dd50f7004c11ac5，字节数 = 61819

本会话 `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rsv_fp.py"` 输出 `BINDING LINE:` 段原样；与任务书【编排方指纹】及【核查】/【复核】的 `sha256Line` 逐位一致。

### 6.2 复核 verdict 如实登记

- 本任务【复核】回件对**载体与扫描口径核查回件**的 verdict = **confirmed**（`ranCommands: 44`，九项核心结论全通过、不 refuted）⇒ 按铁律「refuted 或 partial 标 unconfirmed」，**本件不标 unconfirmed**。
- 不同对象的状态不得混称：`S604_REFSYNC_FULL.md:292` 自登记其**自身**「复核 verdict = partial ⇒ 本交付件整体登记为 **unconfirmed**」；`LEDGER_BOUND_VOLUME.md:34` 记「第 5 笔 §609 状态 **unconfirmed**」。这两处是 43 处清单交付件 / §609 笔的上游状态，**不是**本件所复核对象。
- 本会话对【核查】evidence 的关键项逐一实跑复现（14/14 指纹、组①/② 逐字、区块行号、13∩18/差集、严格交集 4/6、两台账 0 命中、脚本 `EXIT=0`/`SELF_TEST=PASS`），结果见 §2–§5；未在 §2–§5 复现的项一律列 §6.5「未验」。

### 6.3 未改任何既有件声明（本会话实跑）

- `cd "D:/Project/ra2-campaign-forge" && git log -1 --format="%h %s"` → `2657458 GOAL-3T: 台账 §400→§508 与 D-07..D-11 裁决登记入账`（与起始快照一致，**无新提交**；不 commit、不 push）。
- `git status --short` 过滤只读域与两台账 → 七个只读域仍全为 `??`、`GOAL_THREE_TARGETS_20261018.md` / `PENDING_DECISIONS.md` 仍为 `MM`（与起始快照同状态），写域 `?? lead/refsync_scope_20261109/`。
- 收尾重跑 `_rsv_fp.py` → `ALL_14_MATCH = True`，14 件指纹全未变。
- 本会话**唯一写入** = `lead/refsync_scope_20261109/` 下的新件：`REFSYNC_SCOPE_FIX.md`（本件）、`_fix_d2_out.txt`、`_fix_d2_err.txt`（空）、`_fix_md_out.txt`、`_fix_all_out.txt`；均为新建输出/文档，**未修改、未追加、未覆盖任何既有件**。
- 零真机、零采样代码；Python 全部 `python -I -X utf8` + 绝对路径；指纹全部 `hashlib`。

### 6.4 【复核】次要点更正逐条登记（本会话复算）

| 项 | 【复核】指出 | 本会话实跑结论 |
|---|---|---|
| (a) | 组②「2 份 +2 sandbox」实为 5 份，漏 `MINHARD_SET_CHECK.md:94` | **成立**：`python -I -X utf8 -c` 全 lead/ md 扫描输出 `COUNT = 5 distinct files = 5 IN_BLOCK = 0`，5 份为 `:215` / `_lad_tpl:151` / `MINHARD:94` / 2 sandbox `:215`，逐份 101 字符 / `46adf104…`。**0 污染结论不变** |
| (b) | `_rs_CARRIER_MAP.md:213`「分布 8 个文件」与自身 `_rs_verbatim_out.txt:5-14` 的 10 行 / 9 文件不符 | **成立**：本会话实读 `_rs_CARRIER_MAP.md:213` 原文 + `_rsv_ten.py` 输出 `COUNT = 10 distinct files = 9`；本件按 9 文件登记，回件 `carrierMap` 的 10 行枚举本身正确 |
| (c) | 现盘重跑 19 件/80 行(d2)、23 件/86 行(全树)，多 1 件 7 行 = `_rs_CARRIER_MAP.md` 自引 | **成立**：`_rsv_scope2.py` 输出 `current d2 = 19/80`、`current no-cap = 23/86`，`FILES ADDED AFTER 12:19` 明列 `refsync_scope_20261109/_rs_CARRIER_MAP.md mtime=12:20:40 hits=[60, 179, 188, 223, 272, 275, 277]`；本会话 `_fix_d2_out.txt` / `_fix_md_out.txt` 同数 |
| (d) | 「不是更晚」举证只用了 `_lb_BOUND_VOLUME.md`；编译本 `LEDGER_BOUND_VOLUME.md` 10:29:52 晚于 10:26:57 | **成立**：本会话 mtime 实算见 §4.3，措辞已收窄为「整体结论由源件 + `:278` 承担，更晚只对编译本 1 件成立」 |
| (e) | `NEG_LEX` 整行子串表存在假阴性路径，6 个负控未覆盖 | **成立**：`_rsv_r5.py` 例 E/F 复现裸断言被翻成 `ANALYSIS_MENTION`；本会话核过 `_fix_d2_out.txt` B 段 4 条 `ASSERTION` 行 `neg=[]` 未受影响，本语料结论不变，**但对任意语料免疫未验** |

### 6.5 未验项（不补造）

1. 编排方 `dirs=288` 的具体统计口径**未复现**（本会话/上一轮实算含 scoped-md 目录数 / d≤2 全部目录 / 总目录三值均不等，且并行写入浮动）；不影响 `scanned=623` / 18 件结论。
2. 编排方全量扫描的**确切命令文本**未随任务书下发；本会话只按它给的 needle、depth、扩展名白名单独立复现，18 件文件集合一致。
3. `_mh_MINHARD_CHECK.md:206/:207/:253` 未被编排方列出的**具体 predicate 未下发**（3 行确含 needle 已本会话实算，文件字节数 44293 与编排方一致 ⇒ 非文件改动）。
4. 两份 sandbox 副本（`_dnw_sandbox/`、`_dnv_sandbox36/`）是否具实际**复制效力未验**（`MINHARD_SET_CHECK.md:287` 亦标未验），按「存在风险」登记。
5. **Leader 最终会从哪份载体复制入账未验**（`:287`），本件只登记风险，不宣称一定发生。
6. `NEG_LEX` 假阴性路径对任意语料的免疫性**未验**（§6.4 (e)）；`blocks` 检测器在宽松前缀判据下的 `:66` 误判已定位并采用锚定正则，其他宽松变体未逐一枚举。
7. 旧指纹 errata 级联面的**全树全量反链枚举未做**（`MINHARD_SET_CHECK.md:288` 自认、`S604_REFSYNC_FULL.md:278` 自认「未逐一枚举全部登记文件」）。
8. 两台账**全文未通读**：本会话只做正则 `§60[5-9]|§610|码形定谳|dur 字典|512655` 与两句 needle 各 0 命中 + 14 件 hashlib 指纹核对（`MINHARD_SET_CHECK.md:286` 同口径），非逐行亲读。
9. 引号变体 `只能判『不可复现』` 的**全量载体图未建**（本会话只给 d≤2 的 14 文件 / 28 行计数）；按编排方指定串扫描，未私自扩展。
10. 本件写就后自身含两句 needle，会使全树重扫计数再增（自引产物）；本会话未在本件写就后重扫登记该增量，按「未验」列出。

---

**结论一句话**：13 件口径把「要改哪些件」当成了「这句话在哪些件」；按编排方全量口径两句过时表述共 **18 件 70 行**（本会话独立重跑 18 件 73 行），真正「会随整段进台账且已过时」的**严格交集 = 4 件 4 行**（`LEDGER_APPENDIX_DRAFT.md:123`、`_la_draft3:25`、`LEDGER_BOUND_VOLUME.md:196`、`_lb_BOUND_VOLUME.md:129`，四行逐字相同），漏掉的两件正是 2026-11-09 的合订本；全树含 sandbox 为 6 件；两台账 `§605–§609` 全部 0 命中，现在改仍是改草案、来得及。本件是**地图，不是施工图**；只做扫描与登记，**未改任何既有件**。
