# _rs_CARRIER_MAP.md — 载体与扫描口径核查（只扫描与登记，未改任何既有件）

- 日期：2026-11-09。角色：载体与扫描口径核查员（动态工作流子代理）。
- 唯一写域 = `lead/refsync_scope_20261109/`，本目录全部产物前缀 `_rs_`。**未改任何既有件、未入账、未 commit、未 push。**
- 纪律：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 hashlib。
- 全部结论追到「本会话实跑命令 + 在盘输出」或「文件:行」。本写域产出：`_rs_probe.py` / `_rs_lines.py` / `_rs_verify.py` / `_rs_diff.py` / `_rs_markers.py`+`_out.txt` / `_rs_hits.py`+`_out.txt` / `_rs_final.py` / `_rs_verbatim.py`+`_out.txt` / `_rs_carrier_scan.py`+3 份 `_out.txt` / 本件。

## 0 绑定行（本会话 hashlib 实算，被核对象 = 43 处全量清单交付件）

被核对象 SHA256 = 8ccf9866ebd7860f03d71e939960e018fd0cfbbe6b94add04dd50f7004c11ac5，字节数 = 61819

（`_rs_final.py` 实跑输出「BINDING LINE」段；与任务书【编排方实跑指纹】逐位一致。`splitlines()` 行数 365，编排方 366 系末尾换行口径差 1，非内容差。）

---

## 1 独立复核上一轮三个判定（全部实跑）

命令：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_verify.py"`

### (a) 组① 两行逐字相同 —— **相等**

| 件:行 | 字符数 | SHA256（整行 UTF-8） |
|---|---:|---|
| `ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md:123` | 160 | `8daa70d7eac55d437fb5655dc71ca32b7b3714212a7b0c0e56f5f24731ec5ed8` |
| `ledger_appendix_20261108/_la_draft3_s604_gapdiff.md:25` | 160 | `8daa70d7eac55d437fb5655dc71ca32b7b3714212a7b0c0e56f5f24731ec5ed8` |

`verbatim EQUAL = True`，差异字符数 = **0**（若有差异脚本会逐位打印 `pos / U+xxxx`）。顺带实算组② `LEDGER_APPENDIX_DRAFT.md:215 ≡ _lad_tpl.md:151` 亦 `EQUAL = True`，101 字符，SHA256 = `46adf10470d8778cab8adb44e953ee0206fb7eeac91c560b3a7e9cee6e477059`，差异字符数 = 0。**组①与组②不是同一句**：一方 160 字符以 `- **边界（如实）**` 起，另一方 101 字符以 `3. §604 当年内联脚本未落盘` 起，首差异 `pos 0: '-' U+002D → '3' U+0033`（`_rs_verbatim_out.txt` 的 NOT-EQUAL 段）。

### (b) 转录区块边界（实测行号，`_rs_verify.py` / `_rs_hits_out.txt:2-7`）

- `LEDGER_APPENDIX_DRAFT.md` 四段块（锚定注释行实算）= `[(46,61),(80,92),(110,125),(149,179)]`；第 3 段开始 `:110` = `<!-- ============ 草案正文 3 逐字转录开始 ============ -->`，结束 `:125` 同类注释行。`:123` 满足 `110 < 123 < 125` ⇒ **块内（IN_BLOCK=True）**；`:215` 不满足 ⇒ **块外**。
- `:211` = `### 6.3 未验项（全批汇总，如实、不补造）`，`:215` 是该节第 3 条 ⇒ **确在 §6.3 未验项内、不在转录区块内**。
- `_la_draft3_s604_gapdiff.md` 块 = `[(11,28)]`（`:11` `## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓`、`:28` `## ↑↑↑ 草案正文结束 ↑↑↑`），`:25` 在块内。
- 两件 §607 正文段 `:111-124` 与 `:13-26` 均 **2707 字符**、SHA256 同为 `a758a87b31da39e740977dff05e315333e8fb336ac0d8cdd86866244cfdaab82`（与编排方 `LA_110_125`/`D3_13_26` 逐位一致）。

### (c) 组③ 所在件无转录块 —— **确认**

`S604_ATTRIBUTION.md` 27182 B / 195 行（`_rs_verify.py` C 段），对关键词 `逐字转录 / 整段复制 / ↓↓↓ / ↑↑↑ / 草案正文 / 从这里开始 / 可整段复制追加 / 转录开始 / 转录结束` 全件扫描 **marker-like hits = 0**。`:1` 自题「…归属裁定（**撰写终件**）」。`:171` 为该件 §6-3 缺口行，无块可随。

### (d)「会随整段进永久台账」对组②/组③ 是否成立

| 组 | 结论 | 依据 |
|---|---|---|
| ② `:215 ≡ _lad_tpl:151` | **不成立** | 两行均 `IN_BLOCK=False`；`:215` 在 `:211` 起 §6.3，四段区块止于 `:179`；`_lad_tpl.md` 块 `[(46,48),(67,69),(87,89),(113,115)]`，`:151` 在 `:147` 起 §6.3。`S604_REFSYNC_FULL.md:126` 自己写明「`:215` **不在**待追加正文内，不会随笔3 整段进永久台账…属**草案自洽硬项，非入账污染**」；`MINHARD_SET_CHECK.md:99-103` 同判。真实硬度只剩「同件 :123 改 / :215 未改的自相矛盾 + 两件逐字同文」。 |
| ③ `S604_ATTRIBUTION.md:171` | **完全不适用** | 历史撰写终件、全件 `blocks=[]`，无「整段复制追加」通道。`MINHARD_SET_CHECK.md:115-117` 判「完全不适用」，且 `S604_REFSYNC_FULL.md:85`/`:309` 自给降级出口（可降为行尾加注）。 |

⇒ 上一轮（甲）判定**成立**：三组里只有组① 真满足「会随整段进永久台账且已过时」。

---

## 2 全量载体图（独立重跑）

### 2.1 实跑命令与口径

`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_probe.py"` → 输出在盘。
`python -I -X utf8 "…/_rs_diff.py"` → 与编排方 carrier map 逐件逐行集合比对。
`python -I -X utf8 "…/_rs_hits.py" > "…/_rs_hits_out.txt"` → 73 行命中逐行分类。

- 全 `lead/` md = **943**（按 dir-depth：`0:5 / 1:453 / 2:165 / 3:261 / 4:59`），dir-depth≤2 的 md = **623**，与编排方 `scanned=623` 逐位一致。编排方 `dirs=288` 我未复现（我实算「含 scoped md 的目录数」= 221、「depth≤2 全部目录」= 355、总目录 1303）；该数按其声明口径为**未验**，不影响 623/18 结论。
- 两句 needle = `只能判「不可复现」` / `不能定位当年错误步骤`。**注意**：正文里还有 `只能判『不可复现』`（弯单引号）变体；`_rs_probe.py` 实算该变体全 lead/ 命中 18 文件 / 32 行，与 `只能判「不可复现」` 的 18 文件 / 45 行不是同一集合；本任务按编排方指定的两句精确串扫描，**未私自扩展变体**（若扩展，见 §4 教训 2）。

### 2.2 (a) 编排方口径（dir-depth≤2，md）：**18 文件 / 70 命中行**；我独立重跑 **18 文件 / 73 命中行**

逐件（`_rs_diff.py` 逐件比对输出，17/18 件逐行 MATCH）：

| # | 件 | 编排方行 | 我实跑行 | 差 |
|---|---|---|---|---|
| 1 | `ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md` | 123, 215 | 123, 215 | — |
| 2 | `ledger_appendix_20261108/_lad_tpl.md` | 151 | 151 | — |
| 3 | `ledger_appendix_20261108/_la_draft3_s604_gapdiff.md` | 25 | 25 | — |
| 4 | `ledger_bound_20261109/LEDGER_BOUND_VOLUME.md` | 179, 196, 270, 288 | 同 | — |
| 5 | `ledger_bound_20261109/_lb2_TEMPLATE.md` | 152, 202 | 同 | — |
| 6 | `ledger_bound_20261109/_lb_BOUND_VOLUME.md` | 112, 129, 201, 216, 226 | 同 | — |
| 7 | `minhard_check_20261109/MINHARD_SET_CHECK.md` | 34, 75, 79, 94, 164, 207, 214, 238 | 同 | — |
| 8 | `minhard_check_20261109/_mh_MINHARD_CHECK.md` | 49, 52, 66, 125, 146, 187, 196, 197 | 49, 52, 66, 125, 146, 187, 196, 197, **206, 207, 253** | **+3** |
| 9 | `s604_refsync_20261109/S604_REFSYNC_DRAFT.md` | 58, 65, 102, 108, 121, 127 | 同 | — |
| 10 | `s604_refsync_20261109/_rs_REFSYNC_DRAFT.md` | 26, 32, 36, 126, 131, 135, 144 | 同 | — |
| 11 | `s604_refsync_full_20261109/S604_REFSYNC_FULL.md` | 125, 127, 143, 206 | 同 | — |
| 12 | `s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md` | 130, 131, 132, 133, 206, 319 | 同 | — |
| 13 | `s604_script_gap_20261109/S604_SCRIPT_GAP.md` | 55 | 同 | — |
| 14 | `s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md` | 58, 79, 94, 107, 150, 151 | 同 | — |
| 15 | `s604_verdict_entry_20261109/_ve_DRAFT_S609.md` | 22, 46, 53, 69, 70 | 同 | — |
| 16 | `slowframe_r3_20261108/S604_GAP_RECHECK.md` | 101 | 同 | — |
| 17 | `slowframe_r3_20261108/_r3_GAPDIFF_RECHECK.md` | 63 | 同 | — |
| 18 | `slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md` | 91, 127 | 同 | — |

**+3 的实测交代**（不掩盖）：`_mh_MINHARD_CHECK.md` 现盘 44293 B / 299 行 / SHA256 `c31bf7f0de15697de0f5a448a3759104be103b232761bcf1da3de279c29cc20a` / mtime `2026-11-09 11:04:59`（本会话实算）。`:206` 含 N1+N2、`:207` 含 N1+N2、`:253` 含 N2，均为「改前/改后/验收」引述（`_rs_hits_out.txt:87-92`）。编排方未列这 3 行，但文件字节数与我一致 ⇒ **不是文件被改动**，而是其扫描 predicate/去重口径与我的 OR-of-two-exact-strings 不同；具体口径编排方未给命令，按「未验」登记，不臆断。**文件集合 18 件完全一致**。

### 2.3 (b) 逐件判「随整段进台账」——判据与结论

判据（`_rs_hits.py` / `_rs_carrier_scan.py` R4）：**标记行必须整行命中锚定正则**（`<!--…草案正文 N 逐字转录开始/结束-->`、`#### ↓↓↓ 草案正文（逐字照抄，从下一行起）↓↓↓` / `↑↑↑`、`## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓`），只认开区间 `start < line < end`；并交叉核对件内是否有「可整段复制追加 / 不是台账、不入台账」自述、`@@BODY_n@@` 占位符、独立终件自题。

| 件 | 实测块 | 命中行中 IN_BLOCK | 性质 / 入账风险 |
|---|---|---|---|
| `LEDGER_APPENDIX_DRAFT.md` | `[(46,61),(80,92),(110,125),(149,179)]` | **:123** | 4 笔草案汇编，`:11`/`:31` 明写「整段追加」、`:4`「不是台账、不入台账」 ⇒ **HIGH（组①）**；`:215` 在 §6.3 ⇒ NONE |
| `_la_draft3_s604_gapdiff.md` | `[(11,28)]` | **:25** | 单件草案件，`:1`「供 Leader 整段复制追加」 ⇒ **HIGH（组①）** |
| `LEDGER_BOUND_VOLUME.md` | `[(123,142),(153,169),(181,200),(212,246),(258,276)]` | **:196**（§607 章）、**:270**（§609 章，否定句） | 合订本，`:3`「不是台账、不入台账」、`:10` 逐字照抄、`:34`「5 笔全部未入账、可整段复制追加」 ⇒ **HIGH**：`:196` 是组① 第三份可复制载体；`:270` 虽在块内但属**引该句来否定**（见 §4d） |
| `_lb_BOUND_VOLUME.md` | `[(57,76),(87,103),(114,133),(144,178),(189,207)]` | **:129**（§607 章）、**:201**（§609 章，否定句） | 同式合订本单件版，`:2` 自述 ⇒ **HIGH**：`:129` 是第四份；`:201` 为否定句 |
| `_lb2_TEMPLATE.md` | `[(123,127),(138,142),(154,158),(170,174),(186,190)]` | 无 | **INDIRECT（非 HIGH）**：`:154-158` 是 `@@BODY_3@@` 占位符，骨架本身不含字面句；但 `_lb_build.py` 重建时会由源件注入 ⇒ 指纹登记面会失效（`MINHARD_SET_CHECK.md:161`）。两命中 `:152/:202` 是索引/依赖标注，块外 |
| `_lad_tpl.md` | `[(46,48),(67,69),(87,89),(113,115)]` | 无 | **NONE**：`:151` 在 §6.3；`:87-89` 为 `__DRAFT3__` 占位符 |
| `S604_VERDICT_ENTRY_DRAFT.md` | `[(68,84)]` | **:79**（§609 正文，否定句） | `:3`「本件本身不是台账、不入台账」，但 §4.1 `:66` 明写「整段复制追加于 GOAL」 ⇒ 块 `:68-84` 会进台账；`:79` 是**否定该句**的关系句，不是过时载体 |
| `_ve_DRAFT_S609.md` | `[(11,27)]` | **:22**（§609 正文，否定句） | 同上，§609 单件草案件，`:1` 自述「供 Leader 整段复制追加」；`:22` 否定句 |
| `s604_refsync_20261109/*`（2 件） | `[]` | 无 | 修订建议/同步草案，无 `## §6xx` 入账正文；命中均为改前/改后逐字引文 ⇒ NONE |
| `s604_refsync_full_20261109/*`（2 件） | `[]` | 无 | 43 处清单与草案，命中均为「原文逐字 / 改后逐字」引文 ⇒ NONE |
| `minhard_check_20261109/*`（2 件） | `[]` | 无 | 校核件，命中均为原句转录 / 改前改后 / grep 验收命令 ⇒ NONE |
| `s604_script_gap_20261109/S604_SCRIPT_GAP.md` | `[]` | 无 | 调查报告，`:55` 是对 `GAP_RECHECK:101` 的逐字引文（`S604_REFSYNC_FULL.md:142-145` 判「保留」）⇒ NONE |
| `S604_GAP_RECHECK.md` / `_r3_GAPDIFF_RECHECK.md` / `SLOW_WINDOW_LIMITS.md` | `[]` | 无 | 历史复算/被核质疑件，独立调查报告，无转录块 ⇒ NONE（但属"已定谳但表述旧"的**修读面**，13 件清单已列 `:101` / `:91`；`:127` 是 43 清单外同类句，`MINHARD_SET_CHECK.md:164` 已登记） |

**严格交集（「随段进台账」∩「已定谳但表述旧」）的实质断言载体 = 4 行 / 4 件**：`LEDGER_APPENDIX_DRAFT.md:123`、`_la_draft3_s604_gapdiff.md:25`、`LEDGER_BOUND_VOLUME.md:196`、`_lb_BOUND_VOLUME.md:129`。这 4 行**逐字相同**（`_rs_verbatim_out.txt`：整行 160 字符、SHA256 全为 `8daa70d7…`）。全 lead/ 含该 160 字符整行的共 **10 行**（另 6 行是合订本/同步草案/校核件里的逐字转录，均无入账通道）。

### 2.4 (c) 13 件口径与全量口径的差集 —— **漏掉的载体**

命令：`python -I -X utf8 "…/_rs_final.py"`（集合运算输出）。

- 13 件 = `S604_VERDICT_ENTRY_DRAFT.md:90` / `S604_REFSYNC_FULL.md:40-55` 逐件表所列的 13 个文件。
- 18 件（全量 carrier）∩ 13 件 = **6 件**：`LEDGER_APPENDIX_DRAFT.md`、`_la_draft3_s604_gapdiff.md`、`_lad_tpl.md`、`S604_SCRIPT_GAP.md`、`S604_GAP_RECHECK.md`、`SLOW_WINDOW_LIMITS.md`。
- 13 件中**不是这两句载体**的 7 件：`S604_ATTRIBUTION.md`、`_sa_ATTRIBUTION_S604.md`、`_sg_FINDINGS.md`、`S604_EXCLUSIVITY.md`、`_ex_EXCLUSIVITY.md`、`RULING_DIRECTION.md`、`_dr_RULING.md`（它们的过时点是别的短语，如「无法定谳」「落盘副本」「不可定位」）。⇒ 两个口径**不是包含关系**，是不同维度。
- **差集（全量 − 13 件）= 12 件漏掉的载体**：

```
ledger_bound_20261109/LEDGER_BOUND_VOLUME.md          ← 真·入账污染（:196）
ledger_bound_20261109/_lb_BOUND_VOLUME.md             ← 真·入账污染（:129）
ledger_bound_20261109/_lb2_TEMPLATE.md                ← 模板指纹/重建风险
s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md  ← §609 正文（:79 否定句）
s604_verdict_entry_20261109/_ve_DRAFT_S609.md            ← §609 正文（:22 否定句）
s604_refsync_20261109/S604_REFSYNC_DRAFT.md
s604_refsync_20261109/_rs_REFSYNC_DRAFT.md
s604_refsync_full_20261109/S604_REFSYNC_FULL.md
s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md
minhard_check_20261109/MINHARD_SET_CHECK.md
minhard_check_20261109/_mh_MINHARD_CHECK.md
slowframe_r3_20261108/_r3_GAPDIFF_RECHECK.md
```

其中**只有前 2 件是「会随整段进台账且表述旧」的实质漏项**（即背景 (乙) 点名的两件）；`ledger_bound` 三件是本次口径事故的核心。其余 9 件是分析/校核/转述件，属「同一句被多份文件逐字复制」的载体，但**不是入账污染源**——把它们与实质漏项混为一谈会虚增件数。

### 2.5 全 lead/ 无深度上限的补充实跑（我主动扩大口径，如实登记）

`python -I -X utf8 "…/_rs_carrier_scan.py" --needle … --ext .md`（无 `--max-depth`）→ `scanned files = 943`，carrier occurrences = **79**，distinct files = **22**，SELF_TEST = PASS。比 depth≤2 多出的 4 件全是 sandbox 副本：

```
gate_doc_name_fix_20261109/_dnv_sandbox36/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md  (:123,:215) sha256 724458d9… 45719 B
gate_doc_name_fix_20261109/_dnv_sandbox36/s604_script_gap_20261109/S604_SCRIPT_GAP.md       (:55)     sha256 593c7a3e… 20271 B
gate_doc_name_fix_20261109/_dnw_sandbox/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md     (:123,:215) 同上
gate_doc_name_fix_20261109/_dnw_sandbox/s604_script_gap_20261109/S604_SCRIPT_GAP.md          (:55)     同上
```

两件 sandbox 的 `:123` 与原件逐字相同且在 `[(110,125)]` 块内 ⇒ 全树严格交集 = **6 行 / 6 件**（`MINHARD_SET_CHECK.md:180` A′ 口径同数，本会话独立复现）。sandbox 是否具复制效力**未验**（`MINHARD_SET_CHECK.md:287` 亦标未验），按「存在风险」登记，不宣称一定发生。

---

## 3 扫描口径为什么错

### (a) 43 处清单的 13 件范围是怎么定的（实读自己的口径声明）

- `S604_VERDICT_ENTRY_DRAFT.md:90`（定谳交付件 §4.2 计数口径）：「下表按 file:line 严数 = **13 件 43 处**；其中 2 对为汇编件与单件版同文重复…整理回件原清单「6 件 13 处」系其自身口径…**复核回件补 11 组；本交付轮全树扫描另查得 6 行/组**（表中标 ◆）。每处均经本会话直读核实，非转抄。」
- `S604_REFSYNC_FULL.md:11`（本任务被核对象 §1 目的）：「`S604_VERDICT_ENTRY_DRAFT.md` §4.2（本会话实读 `:88-131`）列出…引用面 **13 件 43 处**（严数）…本件只补**剩余 30 处**」；`:14`「§4.2 的 43 处清单原文是本会话第一步实读的 `:88-131`…**非凭任务书转述**」；`:36-55`「43 处完整清单（实读 §4.2 `:94-125`，按 file:line 严数展开 = 13 件 43 点）」，并逐件列出 13 行表。
- ⇒ **13 件不是一次扫描得出的边界，而是「§4.2 那张 32 行表按 file:line 展开后的去重文件集合」**；其上游又是「整理回件 6 件 13 处 → 复核回件补 11 组 → 交付轮全树扫描补 6 行/组」的**三轮人工累加**。`S604_VERDICT_ENTRY_DRAFT.md:131` 自己承认「扫描覆盖诚实账」：全树两轮 12+6 变体短语命中除 13 件外另有约 20 处，只抽读 3 处、其余按目录主题与成文日期判非本议题，「**此项为抽样判断，非全量亲读**」。

### (b) 按什么维度圈定 13 件

**既不是写域、也不是文件名模式，是「人工逐处列举 + 按历史写域归并」的清单继承**：`S604_REFSYNC_DRAFT.md:10` 自述「编排方指定的 13 处失效/过时引用分布在 **5 个历史写域的 6 件**（8 个行位文件）中」；`S604_REFSYNC_FULL.md:275` 把 13 件当作「13 次历史件指纹变更」的执行单位；`:320` 用「13 件 − 4 件 = 省 9 次」算节省。也就是说，13 件是**「要动哪些历史件」的施工清单**，被反向当成了**「过时表述存在于哪些件」的扫描结果**。这两者本不是同一个集合，事故由此而来。同时它把只读域（`s604_verdict_entry_20261109/`、`s604_refsync_20261109/`、`s604_refsync_full_20261109/`、`minhard_check_20261109/`）天然排除在「待改件」之外，于是这些域里成打的逐字转录/引文命中根本不进清单。

### (c) 为什么 `ledger_bound_20261109` 会被漏掉 —— **不是「更晚 / 圈定时不存在」**

mtime 本会话实算（`python -I -X utf8 -c` + `os.path.getmtime`）：

```
07:46:48  S604_VERDICT_ENTRY_DRAFT.md   (13 件口径的定义处 §4.2)
08:31:24  S604_REFSYNC_DRAFT.md         (原 13 处同步草案)
10:11:15  _lb_BOUND_VOLUME.md           (ledger_bound 最早成件)
10:19:36  _full_checks_out.txt          (43 清单自己的 R2 全树 grep 输出)
10:26:57  S604_REFSYNC_FULL.md          (43 处全量清单交付件)
10:28:50  _lb2_TEMPLATE.md
10:29:52  LEDGER_BOUND_VOLUME.md
12:02:38  MINHARD_SET_CHECK.md
```

**关键实证（纠正一个常见猜测）**：`_full_checks_out.txt:48-55`（43 清单自己 10:19 的 R2 全树 grep「不能定位当年错误步骤」→ 65 命中）**已经命中** `lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md:112/:129/:201/:216/:226` 及 `_lb_build.py:175/:223/:249`。`S604_REFSYNC_FULL.md:278` 也白纸黑字写了「另全树 grep 命中 `ledger_bound_20261109` …等多处旧指纹登记（本会话实跑，输出见 §5.4 R15）」。

⇒ **不是时间上更晚、不是圈定时不存在，也不是 grep 没扫到**。是**扫描结果被"13 件"这个继承自 §4.2 的人工清单过滤掉了**：R2 的 65 命中只被用来做「改文安全性 / 无第三方逐字引用」的旁证（`:126`、`:295`、`:319`），从未被用来**扩充载体集合**；`ledger_bound` 只以「旧指纹 errata 登记面」的身份被提及（`:278`），其「同一句被逐字收进可整段复制区块」的性质完全没被判。`LEDGER_BOUND_VOLUME.md`（10:29:52）确实晚于 43 清单（10:26:57）**3 分钟**，但 `_lb_BOUND_VOLUME.md`（10:11:15）早于清单 15 分钟且已被 65 命中扫到 —— 所以「因为更晚所以漏」只对这 1 件成立，不构成对 3 件整体的解释。

### (d) 这类「按写域/清单圈定扫描范围」的系统性漏法（≥2 条一般性教训）

1. **扫描集合被施工集合取代（selection-by-actionability）**：先有了「要改哪些件」的清单，再用它当「这句话在哪些件」的答案。凡只读域、后建域、分析件、复核件里的逐字副本一律不可见；而后建的**合订本/汇编件恰恰是最危险的载体**（自带「可整段复制追加」）。教训：**扫描口径必须与被核结论的执行口径解耦**，扫描全集由内容定（见 §4a），施工清单只能是它的一个子集且须明示「差集 = 未处置载体」。
2. **grep 命中 ≠ 载体登记（结果用途错配）**：同一份 65 命中输出，被用来证「改文安全」却没被用来建载体图；`S604_VERDICT_ENTRY_DRAFT.md:131` 还把 20 处额外命中按「目录主题 + 成文日期」抽样判无关。教训：**每次全树 grep 必须同时产出「命中全集」与「判定为无关的逐行理由」**，抽样判断不得充当排除依据。
3. **按写域/日期/文件名过滤 = 对副本免疫**：`ledger_bound_20261109/`、`gate_doc_name_fix_20261109/_dnw_sandbox/`、`_dnv_sandbox36/` 都是既有件的**逐字副本**；按写域白名单或「成文日期早于/晚于 §604」过滤会把它们整批剔掉。副本与原件同哈希（`724458d9…` / `45719 B` 本会话实算），**内容寻址才认得出来，路径寻址认不出来**。
4. **变体短语不充分 + 无负控**：`只能判『不可复现』`（弯单引号）与 `只能判「不可复现」` 命中集合不同（本会话实算 32 行 vs 45 行）；12+6 变体仍靠人工列。教训：扫描须有**负控样本**（已知的肯定/否定命中必须分别被分类），否则漏了哪一类自己不知道（脚本 R6 已实现）。
5. **同文去重按「文件」而非「出现点」**：`:123≡:25` 被当作「1 处」计，于是「2 对同文重复 ⇒ 41 独立表述」。但组① 全 lead/ 有 10 份逐字同文（含 2 份 sandbox），其中 4 份在可追加块内。按文件去重会让「改 2 件就够」看起来成立。教训见 §4b。

---

## 4 修正后的扫描口径

### (a) 怎么圈范围才不重不漏（可执行规则，写进 `_rs_carrier_scan.py` R1）

```
全集 U = { f | f 是 ROOT 下深度无上限、扩展名在白名单(.md/.txt/.py/.json)、非二进制的文件 }
   · ROOT = 整个 lead/，不是任何写域白名单、不是任何 prior report 的文件列表
   · 禁止按 目录名 / 写域 / 成文日期 / 文件名模式 预过滤
   · 先按内容过滤：file_bytes 含 needle 才进入候选（内容寻址，副本自动入选）
   · 逐文件登记 sha256 + 字节数 + 命中行号，输出 scanned-files 计数，使重跑可复核
不漏 = 无深度上限 + 无路径过滤 + 不依赖人工列举
不重 = 以 (abs_path, line_no) 为唯一键；同哈希的 sandbox 副本是不同键，
        单列 SANDBOX_COPY 组并标「效力未验」，不与原件合并、也不静默丢弃
```

实跑：`_rs_carrier_scan.py --ext .md`（无 max-depth）→ `scanned files = 943`、22 文件 / 79 行；`--max-depth 2` → `scanned files = 3437`（含 .txt/.py/.json）、62 文件 / 533 行；md-only + depth≤2 = 18 文件 / 73 行。四个口径各自的数字都给出，不混算。

### (b) 以句子为单位，还是以文件为单位 —— **以「句子/出现点」为单位**

理由（均有实跑支撑）：
1. 同一句被逐字复制进 N 份合订本/模板/草案：组① 整行 160 字符在 lead/ 有 **10 份逐字同文**（`_rs_verbatim_out.txt`），分布 8 个文件；按文件计会把 10 份压成 8 个、再按「同文去重」压成 1 处。
2. **入账风险是行级属性，不是文件级属性**：同一文件 `LEDGER_APPENDIX_DRAFT.md` 的 `:123`（块内、HIGH）与 `:215`（§6.3、NONE）风险相反；`LEDGER_BOUND_VOLUME.md` 的 `:196`（块内过时断言）与 `:270`（块内否定句）风险相反。按文件判必然误判其一。
3. 文件只是**派生分组**：先得 `(file,line,role,entry,risk)` 元组，再 `GROUP BY file` 出件数。这样「2 件 / 4 件 / 6 件 / 18 件 / 22 件」都可由同一批元组按谓词重算，不会再出现「省 9 次随口径漂移」（`MINHARD_SET_CHECK.md:185`）。

### (c) 可复用自检脚本

`lead/refsync_scope_20261109/_rs_carrier_scan.py`（本写域，`python -I -X utf8` + 绝对路径）：

```
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan.py" \
  --needle "只能判「不可复现」" --needle "不能定位当年错误步骤" \
  --canonical "<组① 整行 160 字符>" --include-refuting \
  > "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan_out.txt"
```

- 输出 A 段 = 全量载体图（每文件每行的 `role / entry / risk / needs_fix / verbatim(canonical==line) / 差异码位 / SHA256`）；B 段 = 严格交集；C 段 = 非修复项（含角色直方图）；D 段 = 排除逻辑；E 段 = 负控自检。
- **入账风险判据**：R4 锚定标记行正则 → `APPENDABLE_BLOCK (s,e)` ⇒ `HIGH`；`@@BODY_n@@` ⇒ `INDIRECT`（重建注入）；块外 / 无块 / 独立终件 ⇒ `NONE`；标记不成对 ⇒ `UNKNOWN: 需人工复核`（绝不猜）。
- `needs_fix = (role == ASSERTION) AND (risk == HIGH)`。实跑 `--max-depth 2 --ext .md`：B 段 = **4 行 / 4 件**（正是组① + 两件合订本），SELF_TEST = **PASS**（6/6 负控）。无深度上限 `--ext .md`：B 段 = **6 行 / 6 件**（+2 sandbox）。
- 脚本**只读、只打印到 stdout，不写任何文件**（`validated_root()` 用 `os.path.commonpath` 把 root 限制在仓库内；输出记录由调用方重定向到本写域），避免写越界。全部在盘输出：`_rs_carrier_scan_d2_out.txt`（3624 行）、`_rs_carrier_scan_out.txt`（5929 行）、`_rs_carrier_scan_md_out.txt`（528 行）。

### (d) 怎么避免把「引用该句来否定它」的文件也列成载体

**不是删掉，是打角色标签 + 双条件门**（R5，实现在 `classify_line()`）：

1. 先在行内求 needle 的位置，再求成对引号跨度（`「」` / `『』` / 反引号 / `“”`）与 `>`、`|` 引用前缀；needle 落在引号跨度内 ⇒ 候选「引文」。
2. 同行若含否定/更新词表（`不再成立 / 过时 / 已定谳 / 已定位 / 被推翻 / 被超越 / 取代 / 自本节起 / 改前 / 改后 / 建议改 / 原句 / 原文逐字 / 逐字 / grep / 命中 / 验收 / 误读 / 瑕疵 / 不可引用 / 不影响 / 复核 / 未验项 / 说错 / 更新：`）⇒ `role = REFUTING_QUOTE` 或 `NEGATED_CITATION`。
3. 「改后样例」即使无引号，只要含 `2026-11-09 更新 / 错误步骤已定谳为 / 本句…自该节起不再成立 / 改为：` ⇒ `UPDATED_SAMPLE`。
4. 纯命令/校核行 ⇒ `ANALYSIS_MENTION`；只有**裸断言**（无引号包裹、无否定词）才是 `ASSERTION`。
5. `needs_fix` 必须同时满足 `ASSERTION` **且** `risk = HIGH`。因此 `S604_VERDICT_ENTRY_DRAFT.md:79`、`_ve_DRAFT_S609.md:22`、`LEDGER_BOUND_VOLUME.md:270`、`_lb_BOUND_VOLUME.md:201` 这些**在可追加块内的否定句**仍完整出现在 A 段（不隐瞒 §609 正文会进台账），但不会混进修复件数；实跑负控 `want=REFUTING_QUOTE got=REFUTING_QUOTE` PASS。
6. 反向也成立：`LEDGER_APPENDIX_DRAFT.md:215` 虽是裸断言（role=ASSERTION，负控 PASS），但因 `IN_BLOCK=False` 得 `risk=NONE`，照样正确排除 —— 与 `MINHARD_SET_CHECK.md:99` 组② 判定一致。

---

## 5 修正后的件数结论（分口径如实给）

### (a) 严格交集口径（「随段进台账」∩「已定谳但表述旧」）

| 范围 | 件数 | 具体 |
|---|---:|---|
| 13 件口径内 | **2 件** | `LEDGER_APPENDIX_DRAFT.md:123`、`_la_draft3_s604_gapdiff.md:25`（`MINHARD_SET_CHECK.md:179` A 口径同数） |
| 编排方全量口径（lead/ dir-depth≤2，md） | **4 件** | 上述 2 件 + `LEDGER_BOUND_VOLUME.md:196` + `_lb_BOUND_VOLUME.md:129`（本会话 `_rs_carrier_scan_md_out.txt` B 段实跑） |
| 全 lead/ 无深度上限 | **6 件** | 上述 4 件 + 2 份 `gate_doc_name_fix_20261109/_dnw_sandbox/` 与 `_dnv_sandbox36/` 的 `LEDGER_APPENDIX_DRAFT.md:123`（`MINHARD_SET_CHECK.md:180` A′ 同数；sandbox 效力未验） |

**主答案 = 4 件**（按本任务编排方指定的全量口径）。「最小硬项只需 4 件」这个数字巧合地仍对，但**内容完全不同**：原建议的 4 件是 `{LEDGER_APPENDIX_DRAFT, _la_draft3, _lad_tpl, S604_ATTRIBUTION}`（含两组不成立/不适用的硬度），正确的 4 件是 `{LEDGER_APPENDIX_DRAFT, _la_draft3, LEDGER_BOUND_VOLUME, _lb_BOUND_VOLUME}`。`_lad_tpl.md` 只余 `INDIRECT` 指纹登记风险，`S604_ATTRIBUTION.md` 完全不在交集内。

### (b) 全量载体口径

| 口径 | 文件数 | 行数 |
|---|---:|---:|
| 编排方全量扫描（lead/ dir-depth≤2，md，两句精确串） | **18** | 70 |
| 我独立重跑（同口径，OR-of-two-exact-strings） | **18** | **73**（+3 见 §2.2） |
| 全 lead/ 无深度上限，md | **22** | 79 |
| 全 lead/ 无深度上限，.md/.txt/.py/.json | **67** 文件 | 1052 出现点（含脚本/输出件的转述，仅供审计，不作施工数） |

### (c) §609 与组① 同批入账而不改 `:123/:25`：GOAL 台账内的直接矛盾（逐字冲突文本）

两台账现尾 = `## §604 @ GOAL_THREE_TARGETS_20261018.md:9687`，`§605–§609` 各 0 命中（本会话 `_rs_final.py` 实跑）。若两节按草案整段追加，GOAL 内会同时出现：

- **§607（来自 `_la_draft3_s604_gapdiff.md:25` / `LEDGER_APPENDIX_DRAFT.md:123` / 两件合订本 `:196`/`:129`）**：
  > `- **边界（如实）**：§604 内联生成脚本未落盘（:9751-9755 两次自认），**只能判「不可复现」、不能定位当年错误步骤**；…`

- **§609（来自 `_ve_DRAFT_S609.md:22` / `S604_VERDICT_ENTRY_DRAFT.md:79`）**：
  > `…其边界句「只能判『不可复现』、不能定位当年错误步骤」（:123）**自本节起不再成立**——错误步骤已定位（dur 字典错位），该句属被本节取代的过时表述，如何修订留台账所有者裁决。`

**直接冲突**：同一台账内 §607 断言「**不能定位当年错误步骤**」，§609 断言「该句**自本节起不再成立**、**错误步骤已定位（dur 字典错位）**」；§609 还把 `:123` 这个**草案里的行号**当作台账内可指认的对象，一旦追加后该行号在 GOAL 里并不存在，指认失效。`MINHARD_SET_CHECK.md:238` / `:170` 同判「GOAL 台账内两节互斥」。`LEDGER_BOUND_VOLUME.md:46` 把「笔3 §607 ↔ 第五笔 §609」列为唯一「建议成组」的一对，正是为此。

### (d)「现在改仍来得及」的判断依据

`python -I -X utf8 "…/_rs_final.py"` 实跑两台账逐项扫描：

| 件 | 字节 / SHA256（本会话） | `^## §60[5-9]` | `§60[5-9]` | `码形定谳` / `dur 字典` / `512655` | 两句 needle |
|---|---|---:|---:|---:|---:|
| `GOAL_THREE_TARGETS_20261018.md` | 759518 / `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 0 | 0 | 0 / 0 / 0 | 0 / 0 |
| `PENDING_DECISIONS.md` | 52419 / `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 0 | 0 | 0 / 0 / 0 | 0 / 0 |

GOAL 最后一个 `^## §` 头 = `:9687 ## §604 …`，9757 行；`PENDING_DECISIONS.md` 无 `^## §` 头。两件 SHA256 与【编排方实跑指纹】逐位一致 ⇒ **两台账自基线未变，§605–§609 五笔全部尚未入账**。因此污染只会在 Leader 动笔「整段复制追加」时发生，此刻改 4 份可复制载体仍是改**写域草案**（不是改台账正文，授权层级不同，`_ve_DRAFT_S609.md:24` 明写台账正文「一律留台账所有者裁决」）。

**但必须附三条限定**（`MINHARD_SET_CHECK.md:171,203-207,287`）：① 改 `:25` 后 `d5dc8f97…/7703` 与 `e9842d41…/4894` 的旧指纹登记面须同批 errata（`MINHARD_SET_CHECK.md:161` 列出十余个点）；② 执行顺序宜 §607 四载体先修（或同批并明确两节互引）再追加 §609；③ **Leader 究竟从哪份载体复制入账属编排方裁决事实，本会话无从得知**，本报告只登记「存在该风险」，不宣称一定发生。

---

## 6 本会话实跑命令清单（全部只读 / 仅写本写域）

| # | 命令 | 结果 |
|---|---|---|
| 1 | `mkdir -p lead/refsync_scope_20261109` | 写域建立（此前不存在） |
| 2 | `python -I -X utf8 "…/_rs_probe.py"` | 943 md；dir-depth≤2 = 623；18 文件 / 73 行；全树 22 文件 / 79 行 |
| 3 | `python -I -X utf8 "…/_rs_lines.py"` | 组①/② 行原文与块标记逐行 dump |
| 4 | `python -I -X utf8 "…/_rs_verify.py"` | 组①/② 逐字 EQUAL、块边界、组③ 0 marker |
| 5 | `python -I -X utf8 "…/_rs_diff.py"` | 17/18 件逐行 MATCH；`_mh_MINHARD_CHECK.md` +3 行 |
| 6 | `python -I -X utf8 "…/_rs_markers.py" > "…/_rs_markers_out.txt"` | 240 行标记 dump |
| 7 | `python -I -X utf8 "…/_rs_hits.py" > "…/_rs_hits_out.txt"` | 202 行：73 命中逐行块/否定/角色分类 |
| 8 | `python -I -X utf8 "…/_rs_final.py"` | 13 vs 18 集合运算；两台账 0 命中；§607/§609 冲突文本；14 件指纹 + 绑定行 |
| 9 | `python -I -X utf8 "…/_rs_verbatim.py" > "…/_rs_verbatim_out.txt"` | 组① 整行 10 份逐字同文 / 22 行 NOT-EQUAL + 差异码位 |
| 10 | `python -I -X utf8 "…/_rs_carrier_scan.py" … --max-depth 2 > "…/_rs_carrier_scan_d2_out.txt"` | EXIT=0；B 段 4 行 / 4 件；SELF_TEST PASS |
| 11 | `python -I -X utf8 "…/_rs_carrier_scan.py" … > "…/_rs_carrier_scan_out.txt"`（无深度上限） | EXIT=0；5442 文件 / 1052 出现点 / 67 文件；B 段 6 件；SELF_TEST PASS |
| 12 | `python -I -X utf8 "…/_rs_carrier_scan.py" … --ext .md > "…/_rs_carrier_scan_md_out.txt"` | EXIT=0；943 md / 79 行 / 22 文件；B 段 6 件；SELF_TEST PASS |
| 13 | `grep -n -E "扫描范围\|…" S604_REFSYNC_FULL.md` + `python -I -X utf8 -c` 读 `_full_checks_out.txt:35-100` / `S604_VERDICT_ENTRY_DRAFT.md:127-131` | 13 件口径来源；R2 65 命中已含 `ledger_bound`；抽样诚实账 |
| 14 | `python -I -X utf8 -c` + `os.path.getmtime` / `hashlib` / `git log -3` | 时间线、指纹、无新提交（`2657458`） |

**未验项（不补造）**：① 编排方 `dirs=288` 的具体统计口径（我实算 221/355/1303 三个不同数均不等）；② `_mh_MINHARD_CHECK.md:206/207/253` 未被编排方列出的具体 predicate；③ 两份 sandbox 副本是否具实际复制效力；④ Leader 最终会从哪份载体复制入账；⑤ 编排方全量扫描的确切命令文本（未随任务书下发），我只按它给的 needle 与 depth 独立复现。

---

**结论一句话**：13 件口径把「要改哪些件」当成了「这句话在哪些件」；同一句过时表述在编排方口径下共 **18 件 70 行**（我独立重跑 18 件 73 行），其中真正「会随整段进台账且已过时」的是 **4 件 4 行**（`LEDGER_APPENDIX_DRAFT.md:123`、`_la_draft3:25`、`LEDGER_BOUND_VOLUME.md:196`、`_lb_BOUND_VOLUME.md:129`，四行逐字相同），漏掉的两件正是 2026-11-09 的合订本；两台账 `§605–§609` 全部 0 命中，现在改仍是改草案、来得及。本件是地图，不是施工图；未改任何既有件。
