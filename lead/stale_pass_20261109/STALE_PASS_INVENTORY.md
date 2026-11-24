# 失效 PASS 清点件（STALE_PASS_INVENTORY.md）

**执行者**：失效 PASS 清点件撰写员（subagent，工作流一问一答）
**日期**：2026-11-09
**性质**：**只做清点与建议**。本件**绝不修改台账、绝不修改任何登记**；`lead/PENDING_DECISIONS.md` 与 `lead/GOAL_THREE_TARGETS_20261018.md` 只由 Leader 改。本件不撤回、不加注、不删除任何既有行。
**唯一写域**：`lead/stale_pass_20261109/`；本件及本会话新增脚本/输出均在此目录，前缀 `_spi_`。
**铁律**：零真机（未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入、未写动态内存解析）。本会话所谓「坏针注射」全部是**静态文本脚本副本里的 OR 词表替换 / CLI `--needle` 参数替换**，与进程注入无关。
**未 commit、未 push**。Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib`。

**上游材料**：编排方给入本会话的「【编排方指纹】/【台账扫描】/【清点】/【复核】/【交付】」五段文本（下称「题给材料」）；清点报告本体 `lead/stale_pass_20261109/_sp_STALE_PASS_CENSUS.md`（390 行 / 52,161 B）；复核回件题给 `verdict = partial`（**非 refuted、非 PASS**）。按本任务交付要求，`partial` ⇒ 主清点标 **unconfirmed**（详见 §6）。

---

## 1 目的与边界

**目的**：对「已登记的 PASS 类声明」做逐条清点、三级分级、影响面展开、实质 vs 形式失效判定、逐条处置建议、制度建议；并把复核结论与未验项如实回写在本件（**只回写到本件，不回写台账**）。

**边界（逐条）**：

1. 本件**只清点与建议**。两件台账 `lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md` **绝对只读**；另 `lead/check_masking_20261109/`、`lead/masking_effect_20261109/`、`lead/falsifiable_no_relax_20261109/`、`lead/whitelist_audit_20261109/`、`lead/d27_ruling_20261106/`、`lead/d29_ruling_20261106/`、`lead/d30_ruling_20261106/`、`lead/refsync_scope_20261109/` 亦**绝对只读**。本会话 `git status --short -- <上列路径>` 输出：两账 `MM`（与初始快照一致，非本会话所致），八个只读域 `??`（未跟踪、未改）；`git rev-parse HEAD` = `26574589aa8401e8f3f2934680a1ea7109bafa2d`（与复核回件一致）。
2. 本会话唯一写域内新增：`STALE_PASS_INVENTORY.md`（本件）、`_spi_hash.py`、`_spi_lines.py` / `_spi_lines_out.txt`、`_spi_src_lines.py` / `_spi_src_lines_out.txt`、`_spi_verify.py` / `_spi_verify_out.txt`、`_spi_4gate_out.txt`、`_spi_andk_out.txt`、`_spi_rs_broken_out.txt`、`_spi_n1_out.txt`、`_spi_n2_out.txt`。原有的 27 件 `_sp_` 与 14 件 `_spv_` 产物**未改动**。
3. **「失效」三判据必须分清，三者处置完全不同**（本件核心，见 §3）：
   - **A 级 = 该 PASS 已被证明不可信**：尺子坏——坏输入注入后仍 `PASS` / `EXIT=0`，且与基线逐字一致。
   - **B 级 = 该 PASS 的输入已变**：尺子可能没坏，量的东西换了——登记数字与现盘不可复现，或登记命令口径与实跑口径不一致；PASS 未绑定输入指纹 ⇒ 效力过期。
   - **C 级 = 该 PASS 仍有效但需复核**：尺子没验过——未做坏针注射、未绑指纹、脚本未识别或只有裸 `exit=0`；既不能判不可信，也不能判有效，标 `UNVERIFIED`。
   - 增补 **D 级 = 已自认失效/已修**：登记自己已写「假绿/不可信/已修」，不是仍挂着的现行「已验证」PASS。
4. **本会话实跑与「题给材料里记录的上游实跑」严格区分**：凡本会话未亲自执行的命令，一律写「（题给材料记录，本会话未复跑）」或「未验」，不冒充本会话通过。本会话亲自跑的命令在 §6 列出命令与输出。

---

## 2 上游指纹 + 登记清点

### 2(a) 九件编排方指纹（本会话 `hashlib` 独立实算）

**实跑命令**：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/stale_pass_20261109/_spi_hash.py"`
**输出**（逐件 `sha256` / `bytes` / `MATCH`，末行汇总）：`NINE_ALL_MATCH = True`。会话末复跑 `tail -3` 仍 `NINE_ALL_MATCH = True`。九件逐项如下（值与题给【编排方指纹】逐字符相符，0 差异）：

| # | 文件 | SHA256 | 字节数 |
|---|---|---|---|
| 1 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 |
| 2 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 |
| 3 | `lead/check_masking_20261109/CHECK_MASKING_INJECT.md` | `99131e8aa03717c555a56b7cee75cf747b4127287e2cc1ec9b6bef5656da3c6c` | 56575 |
| 4 | `lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md` | `2f55283ef3380c6cb5915b2e8654a5506061ccb667a986d397b45a10a2f9119f` | 45536 |
| 5 | `lead/d27_ruling_20261106/check_d27.py` | `3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c` | 3764 |
| 6 | `lead/d29_ruling_20261106/check_d29.py` | `2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14` | 3906 |
| 7 | `lead/d30_ruling_20261106/check_d30.py` | `6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd` | 3926 |
| 8 | `lead/refsync_scope_20261109/_rs_carrier_scan.py` | `9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57` | 16053 |
| 9 | `lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md` | `83b215ccbbf2c3e221c247e7bd9c7c221fddcf9472977d2df8902bf1b94ec65e` | 49958 |

**复核对象本体**（题给【复核】绑定行）：`lead/stale_pass_20261109/_sp_STALE_PASS_CENSUS.md` = `f2d8fb32d196af4a2f143be8652d513437b60b3b885c862051a60a9f37dcb391` / 52,161 B / 390 行（`splitlines()`）。本会话 `_spi_hash.py` 独立实算相符；报告 §0 的 9 行严格格式绑定行经 `_spi_verify.py` 机械核验：`STRICT_BINDING_LINES = 9`、`ALL_64HEX = True`、`ALL_MATCH_BASE = True`。

### 2(b) 两台账逐行清点（file:line + 原文 + 总数与分布）

**本会话实跑**：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/stale_pass_20261109/_spi_verify.py" > .../_spi_verify_out.txt`；另 `python -I -X utf8 ".../_spi_lines.py" > .../_spi_lines_out.txt`（逐行原文回读，见该文件）。
**输出**：`PENDING LINES = 381`、`GOAL LINES = 9757`、`FIX LINES = 363`（题给【清点】记 382/9758，是按 `split('\n')` 多算一个末尾空行；两种数法都对，本件用 `splitlines()`，并如实标此口径差——题给【复核】⑤ 已作同判）。

**★ 必须纠正任务背景口径**：四件（`check_d27.py` / `check_d29.py` / `check_d30.py` / `_rs_carrier_scan.py`）的 PASS，在**两件台账里只有 3 行**，`GOAL` 中 **0 行**；第四件（`_rs_carrier_scan.py`）的 PASS **不在台账**，在**绝对只读交付件** `REFSYNC_SCOPE_FIX.md`，且共 **3 行**（`:251` / `:252` / `:253`）。本会话独立扫描（`_spi_verify_out.txt`）逐名计数：`check_d27` PENDING=[129] GOAL=[]；`check_d29` [105]/[]；`check_d30` [92]/[]；`check_d28` [117]/[]；`check_d26` [162]/[]；`check_d25` [186]/[]；`_rs_carrier_scan` / `carrier_scan` / `SELF_TEST` / `REFSYNC_SCOPE_FIX` 在两账 **全 0**。

**台账 3 行（逐字原文，`_spi_lines_out.txt:6/17/26`）**：

| # | file:line | 原文（逐字） | 级 |
|---|---|---|---|
| 1 | `lead/PENDING_DECISIONS.md:92` | `  裁决书 \`lead/d30_ruling_20261106/RULING_D30.md\`（13,197 B / \`d5afc90c50bbf57b…3983d04f\`）+ 事实核证 \`FACTCHECK.md\`（11,394 B）+ \`_d30_facts.py\`/\`_out.txt\`；门禁 \`check_d30.py\` 实跑 **exit=0**（2026-11-07 复跑仍 PASS）。` | **A** |
| 2 | `lead/PENDING_DECISIONS.md:105` | `  裁决书 \`lead/d29_ruling_20261106/RULING_D29.md\`（12,258 B / \`325c950eec4d3275…7212afb\`）+ \`FACTCHECK.md\`（12,647 B）+ \`_d29_facts.py\`/\`_out.txt\`；门禁 \`check_d29.py\` 实跑 **exit=0**。` | **A** |
| 3 | `lead/PENDING_DECISIONS.md:129` | `  裁决书 \`lead/d27_ruling_20261106/RULING_D27.md\`（17,658 B，71 处引用）+ 事实核证 \`FACTCHECK.md\` + \`_d27_facts.py\`/\`_out.txt\`；门禁 \`check_d27.py\` 实跑 **exit=0**。` | **A** |

**交付件 3 行（逐字原文，`_spi_lines_out.txt:64/65/66`）**：`REFSYNC_SCOPE_FIX.md:251` = `| 1 | python -I -X utf8 … --needle "只能判「不可复现」" --needle "不能定位当年错误步骤" --max-depth 2 --ext .md … | EXIT=0；scanned files = 627 ; carrier occurrences = 80 ; distinct files = 19（现盘，含自引；撰写时点 622/73/18）；B 段 occurrences = 4 ; distinct files = 4；SELF_TEST = PASS（6/6 …） |`；`:252` = `EXIT=0；947/86/23；SELF_TEST = PASS`；`:253` = `EXIT=0；5500/2429/81（仅供审计，不作施工数）；B 段仍 6 / 6；SELF_TEST = PASS`。三行均 **A + B**（见 §3）。

**第 4 行台账 A 级（本会话独立复现题给【清点】的新证）**：`lead/PENDING_DECISIONS.md:117` = `  裁决书 lead/d28_ruling_20261106/RULING_D28.md（13,897 B / 29bb247fbf82d80a…763b5f15）+ FACTCHECK.md（13,028 B）+ _d28_facts.py/_out.txt；门禁 check_d28.py 实跑 **exit=0**。`（`_spi_lines_out.txt:23`）。编排方【台账扫描】未点名此行，但题给【清点】已列为新证；本会话 §3 独立注射复现。

**「门禁 exit=0」句式逐行（本会话 `_spi_verify_out.txt`）**：`PENDING` 中含「门禁」且含「exit=0」的行 = `[92, 105, 117, 129, 162, 186, 199]` 共 **7 行**；其中含「实跑」的只有前 6 行（`:199` 写作「门禁 exit=0）」无「实跑」二字）。题给【清点】`gate_run=7` 与广义口径一致；本件按**广义 7 行**列，并标出这一措辞差。**C 级 3 行原文**：`PENDING:162`（`check_d26.py` 实跑 exit=0，`_spi_lines_out.txt:33`）、`PENDING:186`（`check_d25.py`，:34）、`PENDING:199`（N-1 残余「17 条 = CONFIRMED 12 / PARTIAL 5，门禁 exit=0」，:35）。

**总数与分布（多口径并列，不合并冒充）**：

| 口径 | 命令/依据 | PENDING | GOAL | 合计 |
|---|---|---|---|---|
| `exit=0` 类（大小写不敏感，含 `CL_EXIT=0`/`LINK_EXIT=0`/`final_exit=0`） | 本会话 `_spi_verify.py`：8 / 51 | 8 | 51 | **59 行** |
| 独立 `PASS` token（含 `SELF_TEST = PASS`） | 本会话 `_spi_verify.py`：3 / 90 | 3 | 90 | **93 行** |
| 「门禁 … 实跑 … exit=0」显式 | 本会话 `_spi_verify.py` | 6 | 0 | 6 行 |
| 「门禁」+「exit=0」广义 | 本会话 `_spi_verify_out.txt` | 7 | 0 | **7 行** |
| 「门禁」字面任意上下文 | 题给【清点】`_sp_tally.py`（本会话未复跑该脚本） | 14 | 22 | 36 行 |
| 宽口径联合正则 | 题给【清点】`_sp_tally.py`（未复跑） | 27 | 238 | **265 行** |
| 紧口径交集 | 题给【清点】`_sp_classify.py`（未复跑） | 16 | 158 | **174 行** |
| 互斥单标签分类 | 题给【清点】`_sp_dist.py`（未复跑） | 23 | 187 | **210 行** |

**逐字事实（本会话 `_spi_verify_out.txt`）**：`验证通过` / `机械检查通过` / `逐项通过` / `SELF_TEST` / `REFSYNC_SCOPE_FIX` 在两件台账中命中行数 **均为 0**（PENDING=0、GOAL=0）。即台账不用「验证通过」措辞，用的是「实跑 exit=0」「PASS」「全绿」「N/N PASS」。

**D 级逐字原文**（`_spi_lines_out.txt:43/44/48`）：`GOAL:261` 「**假绿**——… 门禁报『0 个虚表槽均有对应还原』并因 `0==0` 判 **PASS**，13 槽完全失明」；`GOAL:262` 「**③ verify_hooks 假绿已修并四档实跑全绿** … v2 ini 13/13 **24/24 PASS**」；`GOAL:327` 「`verify_hooks` 假绿 | **已复现且已修**：原版对合并件报 0/0 却 PASS；v2 报 **13/13**」。三行自己已标「假绿」「已修」，不是仍挂着的现行「已验证」PASS。

### 2(c) 基于「已被证明不可信检验」的条数（A 级判据）

**判据**：把该检验 k≥2 输入中的一根换成保证零命中的哨兵 `TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ`，输出仍 `PASS` / `EXIT=0` / `SELF_TEST = PASS` 且与基线逐字一致 ⇒ 该 PASS 无法察觉死输入，**已证明不可信**。

**本会话实跑 1**：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/stale_pass_20261109/_sp_4gate_compare.py" > .../lead/stale_pass_20261109/_spi_4gate_out.txt; echo "EXIT=$?"` → `EXIT=0`；四组逐字输出：

| 被核对象 | BASE sha256 → INJ sha256 | BASE / INJ 输出 | EXIT | 逐字一致 |
|---|---|---|---|---|
| `check_d27.py` | `3b769d7c…7671c` → `f404f58783ab4da0…7d7af89` | `PASS: D-27 八项机械检查通过；裁决书引用 71 处` | 0 / 0 | True |
| `check_d29.py` | `2a50b09a…d780f14` → `2399e95a43eaafa4…580ced5` | `PASS` | 0 / 0 | True |
| `check_d30.py` | `6cb73796…05ee9fd` → `b1670537e12a6d7c…9a7129` | `PASS` | 0 / 0 | True |
| `check_d28.py`（新证） | `5b42a34a…9d268` → `f5ae184c…4692314` | `PASS: D-28 全部 8 项机械检查通过 (exit 0)` | 0 / 0 | True |

前三件 INJ sha256 与 `CHECK_MASKING_INJECT.md:211/271/331` 登记值逐字符相符（`_spi_src_lines_out.txt:91/93/94`）；d28 为本会话独立复现题给【清点】的新证（源码 `check_d28.py:90` OR 词表 `("历史数字","1681")`，`_spi_src_lines_out.txt:347`）。

**本会话实跑 2**：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan.py" --needle "不能定位当年错误步骤" --needle "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ" --max-depth 2 --ext .md > .../_spi_rs_broken_out.txt 2>&1; echo "EXIT=$?"` → `EXIT=0`；`_spi_rs_broken_out.txt:8` `needles = ['不能定位当年错误步骤', 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ']`、`:10` `scanned files = 662 ; carrier occurrences = 151 ; distinct files = 25`、`:750-755` 六条负控全 `PASS`、`:756` `SELF_TEST = PASS`。**坏针完全被掩蔽**。

**结论数字**：基于已被证明不可信检验的登记 = **7 处 A 级** = 台账 **4 行**（`PENDING:92/105/117/129`）+ 交付件 **3 行**（`REFSYNC_SCOPE_FIX.md:251/252/253`）。`PENDING:162/186/199` 及其余 ~170 行**未逐条注射实证**，不得计入 A，也不得当作「已证明有效」（题给【清点】1(c) 同判；本会话未逐条复跑，记为未验）。

---

## 3 失效分级（三级定义 + 逐条归类 + 若为假的下游影响面 + 优先处置顺序）

### 3(a) 三级（+D 级）定义

| 级 | 名称 | 判据 | 处置 |
|---|---|---|---|
| **A** | **已证明不可信** | 检验本身经坏输入注射实证失效（尺子坏）。判的是 **PASS 的证据资格**，不是结论错（本轮原词在文档里都实际命中，结果碰巧对，`CHECK_MASKING_INJECT.md:695` ②）。 | 立刻加注 `UNTRUSTWORTHY` + 甲' 重跑；不得再以「已验证」身份被引用。 |
| **B** | **输入已变** | 方法可能有效，但当时跑的输入（文档/语料/命令参数）后来变了；PASS 未绑定输入指纹 ⇒ 效力过期（尺子可能没坏，量的东西换了）。 | 绑定**当前**输入指纹重跑；旧数字保留标「历史口径」，不改写、不冒充复现。 |
| **C** | **需复核** | 未做坏针注射、未绑指纹、脚本未识别或只有裸 `exit=0`；既不能判不可信，也不能判有效。 | 标 `UNVERIFIED`；**不撤回、不加「不可信」注**；抽检 + 制度整改，重跑后才可继续以「已验证」引用。 |
| **D** | **已自认失效/已修** | 登记自己已写「假绿/不可信/已修」，不是仍挂着的现行 PASS。 | 保持不动，仅作历史准确性核对。 |

### 3(b) 逐条归类

| # | file:line | 对象 | 级 | 依据（file:line 或本会话实跑输出） |
|---|---|---|---|---|
| 1 | `PENDING:92` | `check_d30.py` exit=0 / 复跑仍 PASS | **A** | `_spi_4gate_out.txt`：`("93.98","误报率")` 杀一根仍 `PASS`/0；源码 `check_d30.py:76`（`_spi_src_lines_out.txt:291`） |
| 2 | `PENDING:105` | `check_d29.py` exit=0 | **A** | `_spi_4gate_out.txt`：`("互斥","前提")` 杀一根仍 `PASS`/0；`check_d29.py:76`（:217） |
| 3 | `PENDING:129` | `check_d27.py` exit=0（含「引用 71 处」） | **A** | `_spi_4gate_out.txt`：`("外推","卡顿不存在")` 杀一根输出一字不变；`check_d27.py:84`（:156） |
| 4 | `PENDING:117` | `check_d28.py` exit=0 | **A（新）** | `_spi_4gate_out.txt`：`("历史数字","1681")` 杀一根仍 `PASS: D-28 …`/0；`check_d28.py:90`（:347） |
| 5 | `REFSYNC_SCOPE_FIX.md:251` | `_rs_carrier_scan.py` `SELF_TEST = PASS` 6/6，登记 627/80/19 | **A + B** | A：`_spi_rs_broken_out.txt:750-756` 坏针仍 6/6 PASS；`_rs_carrier_scan.py:165` `min(pos)`、`:229` `any(n in txt)`、`:343` `ok &= good`、`:346` 单 `SELF_TEST`（`_spi_src_lines_out.txt:376/378/379/382`）。B：本会话同口径有界扫描 `662/151/25`（较题给【复核】的 `655/144/24` 又漂移，因本会话新落盘文件）；`MASKING_EFFECT_AUDIT.md:384`「PASS 未绑定语料指纹」 |
| 6 | `REFSYNC_SCOPE_FIX.md:252` | 同上 `SELF_TEST = PASS`，登记 947/86/23 | **A + B** | 同上；原文见 `_spi_lines_out.txt:65` |
| 7 | `REFSYNC_SCOPE_FIX.md:253` | 同上 B 段 6/6 `SELF_TEST = PASS`，登记 5500/2429/81（自标「仅供审计，不作施工数」） | **A + B** | 同上；原文见 `_spi_lines_out.txt:66` |
| 8 | `PENDING:162` | `check_d26.py` exit=0 | **C** | 题给【清点】直读 `check_d26.py:85-97` 未见 OR 多元组；**本会话未做注射实证** ⇒ 需复核 |
| 9 | `PENDING:186` | `check_d25.py` exit=0 | **C** | 题给【清点】直读 `check_d25.py:58-69`；本会话未注射 ⇒ 需复核 |
| 10 | `PENDING:199` | N-1「门禁 exit=0」（无「实跑」字样） | **C** | 未识别到具体脚本，无可复跑对象（本会话 `_spi_verify_out.txt` 广义口径命中） |
| 11 | `GOAL:261 / :262 / :327` | `verify_hooks` 假绿 | **D** | 原文自标「假绿」「已修」「v2 报 13/13 / 24/24 PASS」（`_spi_lines_out.txt:43/44/48`） |
| 12 | 其余 59 行 exit=0 类 / 93 行 PASS 类 / 265 行宽口径（扣上述） | 单测、编译、真机、工作流门槛、git 门禁 | **C（批量）** | 本会话未逐条重跑；多数为 `HISTORICAL_OBSERVATION` 而非现行验收声明 |

**B 级的诚实边界（本会话实跑）**：`python -I -X utf8 -c` 比较六件裁决书字节数 → `RULING_D27.md` 17658 / `D29` 12258 / `D30` 13197 / `D28` 13897 / `D26` 15373 / `D25` 15545 全部 `MATCH=True`，且 `RULING_D29.md` sha16=`325c950eec4d3275`、`RULING_D30.md` sha16=`d5afc90c50bbf57` 与 `PENDING:105`/`PENDING:92` 截断 sha 相符 ⇒ **四件 gate 的文档输入当前未变，不列 B 级**。但六个裁决目录 `git status --short` 全为 `??`（未跟踪），`git log -- RULING_D27.md` 无输出 ⇒ **判不了历史上输入是否变过**（题给【复核】⑥ 同判）。B 级目前只坐实在 scanner 语料上。

### 3(c) ★ 逐条「若该 PASS 为假，下游具体什么会被推翻 / 不被推翻」（不许笼统写「有影响」）

**统一前提**：四件 PASS 是**形式/机械门禁**，且「结果碰巧对，判的是 PASS 不可信，不是结论错」（`CHECK_MASKING_INJECT.md:695` ②）。故「PASS 为假」推翻的是**「该登记已验证」这一证据资格 / 格式合规保证**，不是裁决的事实与推理。以下逐条给 file:line。

**① `PENDING:92`（D-30，`check_d30.py`）**
- **被推翻**：`RULING_D30.md` 的**门禁要求的 7 个必需小节**（`check_d30.py:7-15` REQUIRED_SECTIONS 恰 7 项；裁决书实际 `## ` 标题为 8 个含「## 0 定谳」，本会话 `_spi_verify_out.txt` 四件均 `h2=8`）、`q1: 戊` 行（`RULING_D30.md:4`）、`check_d30.py:76` OR 词 `("93.98","误报率")` 至少一命中、`:90` 引用≥8、`:94` `FACTCHECK.md` 含 `selfBias` 的**格式合规「已验证」资格**；`PENDING:92` 自身「实跑 exit=0（2026-11-07 复跑仍 PASS）」；`check_d30.py:105` 输出的 `PASS`。
- **不被推翻**：`RULING_D30.md:4` `q1: 戊`（不选任何 k 档进入实现/执行）、`:6` 保留离线论证资格 + D-13 PAUSE、`PENDING:93-99` 与 `RULING_D30.md:20` 的三档实算 93.98% / 68.11% / 8.68%、`:96` Q4 配额 1.55%–6.96%、`:97` Q5 `verified=false`、`RULING_D30.md:76` 实跑 `_d30_facts.py` 得 `corpus: {"files":104,"samples":1125992}` + `All numeric assertions passed`。
- **★ 报告 `_sp_STALE_PASS_CENSUS.md:172` 第③条下游是错挂**：写「`PENDING:101` 引 `RULING_D30.md:6,:20,:28,:47`」。本会话直读 `PENDING:101`（`_spi_lines_out.txt:15`）原文引的是 **`RULING_D29.md:6,:20,:28,:47`**，台账内**无任何行**引 `RULING_D30.md:6/:20/:28/:47`（`_spi_verify_out.txt` 中 `RULING_D30.md` 仅在 `PENDING:92` 出现一次）。`RULING_D30.md:6` 是 D-30 **自己**引上游 D-29（`_spi_lines_out.txt:131`）。此条下游不存在。

**② `PENDING:105`（D-29，`check_d29.py`）**
- **被推翻**：`RULING_D29.md` 的 `check_d29.py:76` OR 词 `("互斥","前提")`、`:90` 引用≥8、`:94` `selfBias` 的格式合规证据；`PENDING:101` 引 `RULING_D29.md:6,:20,:28,:47` 时所附带的格式保证。
- **不被推翻**：`RULING_D29.md:4` `q1: 丁`、`:6` 保留四条约束 / 否决串行机制、`:10` S/T/C 不等式（`T−S≥100ms ∧ C≥T ⇒ C−S≥100ms>50ms`）、`:14` 实跑 `_d29_facts.py` 退出码 0 + `pureLogicalCounterexampleMs`（**注意：在 `:14` 而非报告三处误写的 `:19`，见 §6 修正表**）、`:18/20/26/28/47` 情景 B 作废 / `:191` 适用边界 / `PENDING:107`、`:110` 情景 B 作废、`:111` C/D 条件算术。

**③ `PENDING:129`（D-27，`check_d27.py`）**
- **被推翻**：`RULING_D27.md` 的 `check_d27.py:84` OR 词 `("外推","卡顿不存在")`、`:90` 引用≥8、`:93` `selfBias` 的格式合规证据；`check_d27.py:100` 报出的「裁决书引用 71 处」这一**由 gate 产出的数字**失去可验证性（本会话用 `check_d27.py:18` 同一 regex 独立实算 = 71，题给【清点】`_sp_final_checks.py` 亦记 71）。
- **不被推翻**：`RULING_D27.md:6` `main: B`（立 D-13b）、`PENDING:130/131` 的 1737 / 1681 / 56 / 566.96ms / 129.93ms / 90.42%、`PENDING:156-158` 三条证据行、`RULING_D27.md:12` 亲读 `_d27_facts_out.txt:9`（自标「本阶段未重算」）、`:16-18` 循环式语义论证。

**④ `PENDING:117`（D-28，`check_d28.py`，题给【清点】新证）**
- **被推翻**：`RULING_D28.md` 的 `check_d28.py:90` OR 词 `("历史数字","1681")`、`:100` 引用≥8 的格式合规证据。
- **不被推翻**：`RULING_D28.md:4/5` `q1: A` / `q2: 丁`、`:7` 两链分离、`PENDING:109` 勘误（依赖 `RULING_D28.md:30/:36/:42` 正文）、`PENDING:110` 情景 B 作废、`PENDING:111` C/D 条件算术、`RULING_D28.md:32` `2.5+100+48+2=152.5ms` 与 `BUDGET_MODEL.json` 引用。
- **★ 报告 `_sp_STALE_PASS_CENSUS.md:175` 右栏漏列 `PENDING:109/110/111` 这三条 D-28 实质下游**；且左栏②「`PENDING:103`（D-29）、`PENDING:113`、`RULING_D29.md:6` 等对 `RULING_D28.md:30,:32,:34,:36,:42` 的引用」为合并错挂：本会话直读 `PENDING:103`（`_spi_lines_out.txt:16`）**未引 R28 任何行**；`PENDING:113`（:22）引 `RULING_D28.md:30,:32,:34,:36`，**无 `:42`**；`RULING_D29.md:6`（:112）引 `:28/:36`；`:42` 实际在 `RULING_D29.md:20`（:117）与 `PENDING:109`（:19）。

**⑤ `REFSYNC_SCOPE_FIX.md:251 / :252 / :253`（`_rs_carrier_scan.py`）**
- **被推翻**：
  - `REFSYNC_SCOPE_FIX.md:243` 的 **R6 承诺**「6 个已知肯定/否定样本必须**分别**判 ASSERTION / REFUTING_QUOTE，否则 `EXIT=1`」未被满足——实测 `_rs_carrier_scan.py:343-346` 把 6 条压进单一 `ok`，`:165` `min(pos)`、`:229` `any(n in txt)` 同族；**R1–R6 在 §5.1（`:234`）不是报告 `:176` 写的 §5.3（`:258` 是 R5 排除逻辑）**。
  - `:251` 的 `627/80/19`、`:252` 的 `947/86/23`、`:253` 的 `5500/2429/81` 三组数字失去「自检护航」。
  - 与同一 scanner 输出同源的 **`:273`「编排方全量口径 4 件」、`:274`「全 lead/ 无深度上限 6 件」、`:276`「主答案 = 4 件」、`:282-286` §5.4(b) 五行件数表（18/70、18/73、22/79、19/23 与 80/86、81/2429）**——报告 `_sp_STALE_PASS_CENSUS.md:176` 只笼统写「三个施工/审计数字」「B 段 fix list」，漏列这六行具体结论。
  - `:254`「换 needle 结果随之变化 ⇒ 脚本不硬编码结论」的论证强度。
- **不被推翻**：`:234-242` 的 **R1–R5** 规则文本、`:260` `classify_line()` 引号/否定词表逻辑（代码事实）、`:292-299` §5.4(c) 逐字比对 `EQUAL=False` / `DIFF_COUNT=156` / `U+8FB9` vs `U+4E0E`（题给【复核】④ 记独立 `python -c` 实算，不走 `SELF_TEST`；**本会话未复跑该 `python -c`，记为题给材料记录**）。
- **硬下游实证（本会话实跑）**：`_spi_n1_out.txt:8/10/503` = 单针 `['只能判「不可复现」']` / `662/95/23` / `SELF_TEST = FAIL`（`:501` `:22 got=<not-scanned>`）；`_spi_n2_out.txt:8/10/580` = 单针 / `662/108/25` / `SELF_TEST = PASS`（`:574-579` 6/6）；`_spi_rs_broken_out.txt:8/10/756` = 双针含哨兵 / `662/151/25` / 六条负控全 PASS + `SELF_TEST = PASS` ⇒ **AND_k = FAIL 且坏针被掩蔽**，登记的双针 PASS 在正确逐输入门禁下**应为 FAIL**。三套数字互异（本会话 662 系列 vs 题给【清点】655 系列 vs 登记 627 系列），本会话只判性质不判当时数字（`CHECK_MASKING_INJECT.md:392` 亦记三次数都不同、属口径差）。

### 3(d) 优先处置顺序

1. **P0** `REFSYNC_SCOPE_FIX.md:251`（连带 `:252/:253`、并按 `MASKING_EFFECT_AUDIT.md:380` 补 `:243`）：现行交付件的验收口径、A+B 双级、正确 AND_k 下应为 FAIL。**属绝对只读件 ⇒ 只能建议 Leader 加注，我无权改**。
2. **P0** `PENDING:92 / :105 / :129`：编排方点名、三条裁决链式互引、仍是「已验证」身份。
3. **P0（不可漏）** `PENDING:117`：同族 A 级新证；只修三件会漏网，且位于 D-27↔D-29↔D-30 引用链上游。
4. **P1** `PENDING:162 / :186 / :199`：C 级，与上述同批「门禁 exit=0」句式，用同一甲' 外壳顺手重跑定级。
5. **P1** 其余 `KNOWN_FALSE_PASS` 命中行（题给【清点】记 `GOAL:246/261/262/263/303/327/1192` 共 7 行）由 Leader 人工判读，本会话未逐行定级。
6. **P2** 其余 ~170 行 PASS 类：保持不动 + 制度整改（§6）+ 抽检「裸 exit=0 且无指纹绑定」行。
7. **P3** `GOAL:261/:262/:327`（D 级）：无需动作。

---

## 4 实质 vs 形式（三裁决实质结论 + 是否依赖失效 PASS + 逐条判定 + 两类统计）

### 4(a) D-27 / D-29 / D-30 三件分别是什么裁决（逐条 file:line）

- **D-27**（台账 `PENDING:127-158`，裁决书 `RULING_D27.md:1-7`，定谳 `RULING_D27.md:6` `main: B`）：**立 D-13b 离线设计**——`PENDING:127` 原文「D-13 依据新证据重裁：立 D-13b，面向当前保留的短停样本重开『离线』方案设计与『不含采样实现』的离线单测；D-13 采样代码与执行继续 PAUSE」；`PENDING:130/131` 11 条新证据（1737 候选 / 1681 true / 56 false，`>=1s` 为 0、最长 566.96ms、中位 129.93ms、`100<=d<200ms` 1520 条 = 90.42%）；`RULING_D27.md:16-18` 循环式语义论证；`PENDING:90-101` 相邻登记显示 D-14 双口径维持、目标①机制挂账不解除。
- **D-29**（`PENDING:103-113`，`RULING_D29.md:4` `q1: 丁`）：**保留四条约束，只否决串行机制**——`PENDING:103`、`RULING_D29.md:6` 保留 `:177` 50ms 捕获 / `:190` <50ms / `:191` 拒止 / 口径 B；`RULING_D29.md:10` S/T/C 不等式只在串行前提下成立；`PENDING:107` `:191` 适用边界为规范解释；`PENDING:110` 情景 B 作废；工程可达性未验、D-13 PAUSE。
- **D-30**（`PENDING:90-101`，`RULING_D30.md:4` `q1: 戊`）：**不选任何 k 档进入实现/执行**——`PENDING:93` `k=10` 高召回离线基准 / `k=25` 边界对照 / 不采纳 `k=50`；`PENDING:94` 三档实算 18ms/28294/93.98%/5.94%、48ms/5343/68.11%/31.46%、98ms/1866/8.68%/90.09%；`PENDING:96` Q4 26 个非空窗 → 1.55%/4.34%/6.96% 且不放开配额；`PENDING:97` Q5 `verified=false` 四项依赖全需真机；`PENDING:99` 驳正 20–30 FPS 只说明条件重叠（12.09%）；D-13 PAUSE、目标①机制挂账不解除。

### 4(b) 是否依赖失效 PASS —— 逐条判定

**判：三件全部「不依赖」。PASS 只是形式要件。依据（本会话逐行回读 `_spi_lines_out.txt` / `_spi_src_lines_out.txt`）**：

1. **门禁自述是格式/机械检查**：`check_d27.py:1` "Read-only D-27 gate"、`check_d29.py:1` "format gate"、`check_d30.py:1` "format gate"、`check_d28.py:1` "mechanical gate"（`_spi_src_lines_out.txt:107/176/250/324`）。实际检查项：`check_d27.py:53-100`、`check_d29.py:75-105`、`check_d30.py:75-105`、`check_d28.py:85-115` = 文件存在/非空、`main:`/`q1:` 合法值行、**7 个必需小节**（`check_d27.py:9-17`、`check_d29.py:7-15`、`check_d30.py:7-15`、`check_d28.py:8-16`；四件裁决书实际 `## ` 均 **8** 个含「## 0 定谳」，本会话 `_spi_verify_out.txt` `h2=8`）、小节正文含某词、引用计数 ≥8、`FACTCHECK.md` 含 `selfBias`。**没有任何数值、统计或逻辑断言**。
2. **裁决书自己明确否认把门禁计为通过**（逐字）：
   - `RULING_D27.md:3`「本阶段未重跑统计、原探针、合成反例或**门禁**」；`:58`「『Leader亲跑exit=0』和复核通过只能标来源声明或已有字段，**不得签为本阶段执行通过**」；`:69`「**不背书本阶段未执行的门禁**…已通过」；`:75`「不签为本阶段检查通过」；`:77`「未运行 `check_stall_def.py` 或**其他门禁**」（`_spi_lines_out.txt:91/100/101/102/103`）。
   - `RULING_D29.md:67`「这是题给核对意见，**不是本撰写阶段门禁通过证明**」；`:71`「**未运行原探针、门禁**、历史语料重算…**不记通过**」（:121/122）。
   - `RULING_D30.md:62`「未改门禁」；`:76`「…**不把原探针、`check_feasibility.py` 或原门禁计为通过**；后三者本次未运行」（:135/136）。
   - `RULING_D28.md:9/72/78` 自述未运行核证脚本、门禁、测试、语料重算，不记亲跑通过（:146/152/153）。
3. **实质结论来源是另一条线**：`RULING_D29.md:14` 实跑 `_d29_facts.py` 退出码 0 + `pureLogicalCounterexampleMs`（**报告 `_sp_STALE_PASS_CENSUS.md:127/173/209` 三处误写为 `RULING_D29.md:19`；本会话直读 `:19` 为空行，`:14` 才是正文**）；`RULING_D30.md:76` 实跑 `_d30_facts.py` 得 `corpus 104/1125992` + `All numeric assertions passed`；`RULING_D27.md:12` 亲读 `_d27_facts_out.txt:9` 且自标「本阶段未重算」；`RULING_D28.md:78` 自述只跑 `pwd; rg --files`。定谳行 `RULING_D27.md:6` `main: B`、`RULING_D29.md:4` `q1: 丁`、`RULING_D30.md:4` `q1: 戊`、`RULING_D28.md:4/5` `q1: A`/`q2: 丁` **均不引用 gate**。
4. **四件裁决正文与失败门禁零耦合**（本会话 `_spi_verify_out.txt`）：`check_d27.py` / `check_d29.py` / `check_d30.py` / `check_d28.py` 在四件裁决书中出现 **0 次**（`four_failing_gates=[]`）；`PASS` 0 次；`exit=0` 仅 `RULING_D27.md:58` 一处且为否定句。四件中出现的其它 `check_*.py` 为 `check_stall_def.py`（R27:58/77）、`check_feasibility.py`（R30:76）、`check_candidate.py` / `check_d13b.py`（R28:22），**均非本次四件失败门禁**，且都出现在「未运行/不计通过」语境。
5. **审计报告自认**：`CHECK_MASKING_INJECT.md:695` ①「判不了裁决书事实与推理（三件 docstring 自称 format gate）」②「本次是**主动注入**，三件原词在文档里都实际命中，故**结果碰巧对，判的是 PASS 不可信，不是结论错**」；`:642` 修复建议只要求「把 `PENDING_DECISIONS.md:92,105,129` 三处 `exit=0` 换成『逐输入 PASS 表 + 指纹』」，**未建议重审裁决**（`_spi_src_lines_out.txt:99/103`）。
6. **第四件**：`_rs_carrier_scan.py` 的 PASS 与三件裁决**无引用关系**（两台账 0 行提及 `_rs_carrier_scan` / `carrier_scan` / `SELF_TEST` / `REFSYNC_SCOPE_FIX`），它服务 `REFSYNC_SCOPE_FIX.md` 的语料范围修复交付，不影响任何 D-27/D-29/D-30 结论。

**逐条结论**：
- **D-27：形式要件失效，实质结论不受影响** ⇒ 需修形式（登记加注 + 重跑），不需重审裁决。
- **D-29：形式要件失效，实质结论不受影响** ⇒ 同上。
- **D-30：形式要件失效，实质结论不受影响** ⇒ 同上。
- 附加：**D-28 同为形式要件**；`q1: A / q2: 丁` 不受影响，但它是 D-29/D-30 的引用上游，形式链需一并补。

**诚实限定**：本件判的是**依赖结构**（实质结论并非由该 PASS 推出），依据是上述文档自述与代码结构。本会话**未重跑** `_d27_facts.py` / `_d29_facts.py` / `_d30_facts.py` 的数值断言 ⇒ **不能**进一步断言「实质结论已被本会话独立验证为正确」；题给【复核】③ 亦同判。另 `PENDING:90-101/103-113/127-158` 的登记文本把「裁决书 + FACTCHECK + 门禁 exit=0」并列成「已验证」交付包，那个**「已验证」的证据资格**确实失效——这是必须修的部分。

### 4(c) 两类统计

| 类别 | 处数 | 明细 |
|---|---|---|
| **形式要件失效** | **7 处** | 台账 4 行 `PENDING:92/105/117/129` + 交付件 3 行 `REFSYNC_SCOPE_FIX.md:251/252/253` |
| **实质结论失效** | **0 处** | D-27 / D-29 / D-30 及 D-28 的实质结论均不依赖失效 PASS；第四件不涉裁决 |
| **需复核才能定论（C 级）** | ~170+ 行 | 其余 PASS 类登记未逐条注射实证；另含 `_dNN_facts.py` 数值核证脚本本会话未重跑 |
| **已自认失效/已修（D 级）** | 3 行 | `GOAL:261/262/327` |

---

## 5 处置建议（逐条 + 四件可信重跑方案 + 登记模板 + 不值得重跑的理由）

> **总原则**：**不撤回任何裁决登记**，也**不撤回任何登记行**；唯一应「撤回」的是 7 处 PASS 的**证据资格**，实现方式为**就地加注**（不删原文、不改数字）+ 状态字段改 `UNTRUSTWORTHY` / `STALE_INPUT`。台账只由 Leader 改，以下均为建议，本件不执行。

### 5(a) 逐条建议

| file:line | 建议 | 理由（逐条） |
|---|---|---|
| `PENDING:92` | **加注 + 重跑** | A 级；`check_d30.py` 坏针仍 `PASS`/0（`_spi_4gate_out.txt`）。加注「本 PASS 经坏输入注入实证不可信，2026-11-09」；随后按 5(b) 重跑并登记新结果；`q1: 戊` 不动 |
| `PENDING:105` | **加注 + 重跑** | A 级；同上（`check_d29.py`） |
| `PENDING:129` | **加注 + 重跑** | A 级；同上（`check_d27.py`）。加注须区分「引用 71 处数字对」与「PASS 不可信」 |
| `PENDING:117` | **加注 + 重跑** | A 级（题给【清点】新证、本会话复现）；漏修会让同族缺陷继续挂在链上游 |
| `REFSYNC_SCOPE_FIX.md:243` | **加注（Leader 执行）** | `MASKING_EFFECT_AUDIT.md:380` 明确把 `:243`（R6 描述）列为应加注对象；报告 `_sp_STALE_PASS_CENSUS.md:245` 只写 `:251` 而漏 `:243`（题给【复核】⑦） |
| `REFSYNC_SCOPE_FIX.md:251` | **加注（Leader 执行）+ 重跑** | A+B 级，正确 AND_k 下应为 FAIL。限定文本照 `MASKING_EFFECT_AUDIT.md:380`：「本 PASS 系 N1∪N2 并集口径，不构成逐 needle 有效性证据；`:22` 仅由第二 needle 命中；详见 `MASKING_EFFECT_AUDIT.md`」。旧数字保留不改写 |
| `REFSYNC_SCOPE_FIX.md:252` / `:253` | **加注（Leader 执行）+ 重跑** | 同样 `SELF_TEST = PASS`；`:253` 自标「仅供审计，不作施工数」，漂移影响更大 |
| `REFSYNC_SCOPE_FIX.md:273/274/276/282-286` | **加注「同源输出，效力待重跑」** | 与 `:251-253` 同一 scanner 输出同源的具体件数结论，题给【复核】④ 指出报告漏列 |
| `PENDING:162` | **重跑** | C 级；`check_d26.py` 未见 OR 多元组但未注射实证；顺手用甲' 外壳定级 |
| `PENDING:186` | **重跑** | C 级；`check_d25.py` 同上。注 `PENDING:160` 明示 D-26 的 D-13 部分已由 D-27 重裁，但 **D-14 定谳继续有效**，故整行仍值得跑 |
| `PENDING:199` | **重跑（先识别脚本）** | C 级；N-1 门禁未识别到具体脚本，须先定位再跑；定位不到标「未验」 |
| 其余 ~170 行 PASS 类 | **保持不动 + 制度约束** | 异质（真机/编译/单测/工作流门槛/历史观测），大规模撤回会不成比例地使整本台账失效；改为新登记强制 §6(c) 清单 + 对「裸 exit=0 无指纹」行抽检 |
| `GOAL:261 / :262 / :327` | **保持不动** | D 级，原文已自标「假绿」「已修」，无现行假 PASS 声明 |
| 三条裁决正文 `RULING_D27.md` / `RULING_D29.md` / `RULING_D30.md` | **保持不动** | 实质结论不依赖失效 PASS；只修形式登记 |

**关于「撤回」**：删行会破坏台账可追溯性与引用链（`PENDING:101/113/125` 仍引用这些裁决书），且 `CHECK_MASKING_INJECT.md:642` 与 `MASKING_EFFECT_AUDIT.md:380` 两处审计建议都只要求「加注/换口径」，不要求撤回。

### 5(b) ★ 四件的可信重跑方案（甲' 外壳：逐输入独立跑 + AND_k + 坏针注入）

**依据（file:line，本会话逐行回读 `_spi_src_lines_out.txt`）**：`MASKING_EFFECT_AUDIT.md:176`（`AGGREGATE = AND_k(REAL per-needle self-test)`，每根单独跑未修改扫描器，`EXIT=0 AND 6 条负控逐条匹配 WANT`；`HITSET / MASKED_LINES / EXCLUSIVE(k)` 只报告不门禁；`PER_NEEDLE_SELFTEST` 必须来自**真实 k 次运行**）、`:180`（甲' 推荐、零侵入、被审脚本 0 行改动）、`:202-211`（判据 `DISTINGUISHABLE_PASS`，`MASKED_LINES=41/122`、`EXCLUSIVE_CONTROLS=[0,1]`，代入交付口径 `DISTINGUISHABLE_PASS = FALSE`）、`:213-253`（可粘贴片段）、`:335`（`min/argmin` 反向掩蔽；「唯一可靠的门禁是 `AND_k` 真实逐输入自检」）、`:388-399` §6.4 十条清单、`:390` 口径逐字一致、`:393` 门禁/诊断分离、`:398` 单调性、`:399` 未验项；`CHECK_MASKING_INJECT.md:570-628` **修正版**外壳（`:664` 说明 `_cm_AUDIT.md:469-536` 旧模板因「用被掩蔽的并集布尔判 caught」不可用，**勿沿用**）、`:634-642` 落地成本与修复顺序。

**四件具体重跑法**：

1. **三 gate + d28（OR 词表类）**：把「k 个输入」定义为该 gate 的 `require_all=False` OR 词表：`check_d27.py:84` `("外推","卡顿不存在")`、`check_d29.py:76` `("互斥","前提")`、`check_d30.py:76` `("93.98","误报率")`、`check_d28.py:90` `("历史数字","1681")`（均见 `_spi_src_lines_out.txt`）。甲' 外壳对**每个词 w** 生成一份沙箱副本，把 OR 元组换成单元素 `(w,)`，`python -I -X utf8 <绝对路径副本>` 独立跑一次，捕获 `EXIT/STDOUT/逐检查项`；`AGGREGATE = AND_k(rc==0 ∧ 输出含 PASS ∧ 无 FAIL)`；再对每根依次换 `TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ`，要求 `AGGREGATE` 变 FAIL（`BAD_NEEDLE_CAUGHT`）；输出 k 行 `input_i: PASS/FAIL`。
   - **路径坑必须处理**（本会话直读源码相符）：`check_d27.py:8` 用 **CWD 相对** `DIRECTORY = Path("lead/d27_ruling_20261106")`；`check_d29.py:50` / `check_d30.py:50` 用 `Path(__file__).resolve().parent`；`check_d28.py:54-55` 用 `Path(__file__).resolve().parents[2] / "lead" / "d28_ruling_20261106"`。三者沙箱布局不同（`CHECK_MASKING_INJECT.md:154` 记撰写人第一次漏此点得 6 个 `EXIT=2` 作废重跑）。
2. **`_rs_carrier_scan.py`（--needle 类）**：逐 needle 各跑一次**完整扫描**（`--needle <n>` 单值，`--max-depth 2 --ext .md` 且与登记命令**逐字比对**），每次要求 `EXIT=0 ∧ SELF_TEST=PASS ∧ 6 条负控逐条 want/got 匹配`；`AGGREGATE = AND_k`；再把其中一根换成保证零命中哨兵，要求 `AGGREGATE = FAIL`。
3. **门禁/诊断分离**：`EXCLUSIVE(k)` / `HITSET` / `MASKED_LINES` 只作诊断量；**不得**用「语料独占行>0」「独占负控≥1」替代 `AND_k`（`MASKING_EFFECT_AUDIT.md:176,393`）。
4. **指纹绑定**：每次跑绑定「被核脚本 SHA256 + 字节数 + 输入语料文件数/快照指纹」；stdout 原文落盘并算 sha256；依赖 `min(pos)` / argmin 时加「多加一根输入」单调性对照（`MASKING_EFFECT_AUDIT.md:391,398`）。

**★ 本会话已实跑验证 4/4 gate 侧可行（不是只提建议）**：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/stale_pass_20261109/_sp_andk.py" > .../_spi_andk_out.txt; echo "EXIT=$?"` → `EXIT=0`；`_spi_andk_out.txt` 四组均 `AND_k(over 2 real per-word runs) = True`、`BAD_NEEDLE_CAUGHT = True (sentinel EXIT=1)`、`DISTINGUISHABLE_PASS = True`。scanner 侧本会话 `_spi_n1_out.txt:503` `SELF_TEST = FAIL` / `_spi_n2_out.txt:580` `SELF_TEST = PASS` / `_spi_rs_broken_out.txt:756` 坏针仍 `SELF_TEST = PASS` ⇒ **AND_k = FAIL**。

**★★ 但方案不能直接照抄执行，必须先修两处（题给【复核】⑤，本会话逐行复核）**：

- **口径陷阱**：报告 `_sp_STALE_PASS_CENSUS.md:264` 写「其余参数与登记逐字一致」并 `:258` 让读者照抄 `MASKING_EFFECT_AUDIT.md:216-249`。本会话直读该片段 `MASKING_EFFECT_AUDIT.md:229-231` 带 `--include-refuting`（`_spi_src_lines_out.txt:39`），而 `REFSYNC_SCOPE_FIX.md:251` 登记口径**无此参数**；`MASKING_EFFECT_AUDIT.md:385-386` 自己就登记这是口径差并明说「该 FAIL **不能直接当交付件的验收结论**」（:70/71）。直接照抄会引入第三套口径，与 §5(c) 模板「口径逐字比对」自相矛盾 ⇒ **执行前剥离该参数或显式标「非登记口径」**。
- **部署陷阱**：`_sp_andk.py:7-15` hardcode 12 个已生成的 `_w_dNN_[ABS].py` 沙箱副本，副本由 `_sp_gen_word.py:1-20` 生成（本会话直读，`argv: d27|d29|d30|d28, WORD`，`sys.stdout.buffer.write` 由 shell 重定向落盘）；报告 §6 列了生成器却**未给「生成→落盘→驱动」调用序列**，清空沙箱即跑不起来 ⇒ 它是**演示外壳、非可部署门禁**（报告 `_sp_STALE_PASS_CENSUS.md:361` §5(d):6 已自认「未部署成门禁、未跑修复后回归」）。

### 5(c) 重跑后登记模板（建议，不执行）

```
[§XXX] <对象名> · 重跑登记（2026-11-09，形式要件 / 我亲跑 / VERIFIED）
被核对象 SHA256 = <64hex>，字节数 = <n>
输入语料快照 SHA256 = <64hex>，语料文件数 = <n>，行数 = <n>（或逐输入文档 SHA256+字节数）
实跑口径逐字：<python -I -X utf8 "<绝对路径>" --needle ... --ext ... --max-depth ...>（每个参数列出）
与既往登记口径比对：一致 / 非登记口径（逐项列出差异，如相差一个 --needle 或 --include-refuting）
CWD = <绝对路径>；Python = <版本>；源脚本零字节改动（前后 hashlib 自证）

逐输入判定表（k = <n> 次真实独立运行，非推断）：
| i | input_i | CMD(绝对路径) | EXIT | 汇总行 | 逐条负控 want/got | PASS/FAIL |
| 0 | ... | ... | 0 | SELF_TEST=PASS | 6/6 ... | PASS |
| 1 | ... | ... | 0 | SELF_TEST=PASS | 6/6 ... | PASS |
AGGREGATE = AND_k(...) = PASS/FAIL
坏针注入对照（每根依次换 TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ）：
| i | broken_i | EXIT | AGGREGATE | BAD_NEEDLE_CAUGHT |
DISTINGUISHABLE_PASS = <PASS/FAIL>
诊断量（只报告不门禁）：HITSET / MASKED_LINES / EXCLUSIVE(k)
单调性声明：依赖 min(pos)/argmin ⇒ 加输入对照结果 = ...
stdout 原文落盘：<写域/_spi_xxx_out.txt>，该文件 SHA256 = <64hex>
结论等级：形式要件（不涉实质结论）；与旧登记 <file:line> 的关系 = 取代其 PASS 证据资格 / 旧行保留并加注未删
未验项：<逐条写「未验」，不补造>
```

（模板中「被核对象 SHA256 = <64hex>，字节数 = <n>」为本任务规定的**固定绑定行格式**；值与实跑同发。）

### 5(d) 哪些不值得重跑（逐条理由）

| 对象 | 不重跑理由 |
|---|---|
| `GOAL:261 / :262 / :327` `verify_hooks` 假绿 | 原文已自标「假绿」「已修」「v2 报 13/13 / 24/24 PASS」，是历史记录非现行验收声明；复跑需 `build/ra2render_merged.dll` 与 `ra2render.ini` 合并产物，属构建/部署态，本轮铁律不授权且无增量信息 |
| 真机趟件 `rc=0`/`EXIT=0` 类（`GOAL:260/619/658/1734/3119` 等，题给【清点】登记） | 一次性观测记录 `HISTORICAL_OBSERVATION`；复跑需启动游戏，被零真机铁律禁止；本就不是「现行验收」 |
| 编译 `CL_EXIT=0 / LINK_EXIT=0` 类（`GOAL:261/:325`） | 依赖当时工具链/中间文件状态；`GOAL:261` 自己已记「`.rej` 存在即合并未完成，不能只看 exit code」（`_spi_lines_out.txt:43`） |
| 工作流确定性门槛 `exit=0`（`GOAL:5999/6362/6499/...`，题给【清点】登记） | 一次性交付门槛，对象已定稿；重做需重跑整条 workflow，不成比例 |
| 已被后续裁决取代的部分 | `PENDING:160` 明示「D-26 的 D-13 部分已由 D-27 重裁为 B（立 D-13b）」——该部分重跑无意义；但 **D-14 定谳继续有效**，故 `PENDING:162` 整行仍建议顺手跑（5(a)） |

---

## 6 复核回件 + 系统性建议 + 未验项

### 6(a) 复核回件（绑定行，格式固定）

**被核对象** = 复核回件所指的清点报告 `lead/stale_pass_20261109/_sp_STALE_PASS_CENSUS.md`；下列第 1 行为该被核对象的绑定行，第 2–10 行为九件编排方上游指纹的绑定行（与清点报告 `_sp_STALE_PASS_CENSUS.md:17-25` 同格式、同值）。全部由本会话 `hashlib` 独立实算（`_spi_hash.py` / `_spi_final.py`）；格式固定，值前不插路径、括号、星号、反引号或空格。

被核对象 SHA256 = f2d8fb32d196af4a2f143be8652d513437b60b3b885c862051a60a9f37dcb391，字节数 = 52161
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518
被核对象 SHA256 = 99131e8aa03717c555a56b7cee75cf747b4127287e2cc1ec9b6bef5656da3c6c，字节数 = 56575
被核对象 SHA256 = 2f55283ef3380c6cb5915b2e8654a5506061ccb667a986d397b45a10a2f9119f，字节数 = 45536
被核对象 SHA256 = 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c，字节数 = 3764
被核对象 SHA256 = 2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14，字节数 = 3906
被核对象 SHA256 = 6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd，字节数 = 3926
被核对象 SHA256 = 9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57，字节数 = 16053
被核对象 SHA256 = 83b215ccbbf2c3e221c247e7bd9c7c221fddcf9472977d2df8902bf1b94ec65e，字节数 = 49958

（绑定行依次对应：`_sp_STALE_PASS_CENSUS.md`；`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md`、`lead/check_masking_20261109/CHECK_MASKING_INJECT.md`、`lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md`、`lead/d27_ruling_20261106/check_d27.py`、`lead/d29_ruling_20261106/check_d29.py`、`lead/d30_ruling_20261106/check_d30.py`、`lead/refsync_scope_20261109/_rs_carrier_scan.py`、`lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md`。）

**本件自身指纹**：`STALE_PASS_INVENTORY.md` 的 SHA256 与字节数不写入本件正文（自指哈希无不动点，写入即改变其值），由本会话 `_spi_final.py` 实算并落盘 `lead/stale_pass_20261109/_spi_final_out.txt`，同时在交付结果中回报；本件正文只写可独立复核的上游绑定行。

**上游复核回件（题给【复核】）如实记录**：
- `verdict = **partial**`（**非 refuted、非 PASS**）。按本任务交付要求「refuted 或 partial 标 unconfirmed」 ⇒ 主清点结论标 **unconfirmed**：**不得**把「形式要件失效 7 处 / 实质结论失效 0 处」当成已完全确认的定谳使用；**仍不建议撤回任何裁决登记**，但 Leader 采用前须先修 6(b) 的 7 处引用，再按 §5(a) 加注重跑。
- 复核绑定行（题给【复核】`sha256Line`）：`被核对象 SHA256 = f2d8fb32d196af4a2f143be8652d513437b60b3b885c862051a60a9f37dcb391，字节数 = 52161`（对象 = `_sp_STALE_PASS_CENSUS.md`；本会话 `_spi_hash.py` 独立实算相符）。

### 6(b) ★ 复核指出的 7 处引用错指（本会话逐条独立回读确认，全部成立 —— 这是 `partial` 的实据）

| # | 报告行 | 报告写法 | 本会话实读（file:line） | 性质 |
|---|---|---|---|---|
| 1 | `_sp_STALE_PASS_CENSUS.md:127/173/209`（3 处） | `RULING_D29.md:19` 记 `_d29_facts.py` 退出码 0 / `pureLogicalCounterexampleMs` | `RULING_D29.md:19` 是**空行**；真实在 `RULING_D29.md:14`（`_spi_lines_out.txt:114/116`） | 错指行号，且位于「实质结论不依赖 PASS」证据链 |
| 2 | `:172` 第③条 | `PENDING:101` 引 `RULING_D30.md:6,:20,:28,:47` | `PENDING:101` 原文引 `RULING_D29.md:6,:20,:28,:47`（`_spi_lines_out.txt:15`） | **文件错挂**，导致 D-30 影响面虚构下游 |
| 3 | `:173` | 「该裁决书被 `PENDING:101/113` 引用」 | `PENDING:113` 引 `RULING_D28.md:30,:32,:34,:36`（:22），非 D-29 | 引用链错挂 |
| 4 | `:175` | `PENDING:103`（D-29）、`PENDING:113`、`RULING_D29.md:6` 对 `RULING_D28.md:30,:32,:34,:36,:42` 的引用 | `PENDING:103` 未引 R28 任何行；`PENDING:113` 无 `:42`；`RULING_D29.md:6` 引 `:28/:36`；`:42` 实际在 `RULING_D29.md:20` 与 `PENDING:109`（:16/:22/:112/:117/:19） | 合并错挂 |
| 5 | `:176` | 「§5.3 的 R1–R6」 | R1–R6 实为 **§5.1**（`REFSYNC_SCOPE_FIX.md:234-243`，R6 在 `:243`）；§5.3 是 R5 排除逻辑（`:258`）（`_spi_lines_out.txt:53/62/68`） | 章节错指 |
| 6 | `:172` | 「`RULING_D30.md` 的 **7 个二级标题**」措辞 | 四件裁决书实际 `## ` 均 **8** 个（`_spi_verify_out.txt` `h2=8`）；**7** 是门禁 `REQUIRED_SECTIONS` 项数（`check_d30.py:7-15` 等） | 非实质错，但应写「门禁要求的 7 个必需小节」 |
| 7 | `:245` | 称「照抄 `MASKING_EFFECT_AUDIT.md:380` 的建议文本」却只列 `FIX:251` | `MASKING_EFFECT_AUDIT.md:380` 原件列 `:243`、`:251`、`:252-253`（`_spi_src_lines_out.txt:67`），漏 `:243`（R6 描述行） | 漏列加注对象 |

**自反瑕疵（题给【复核】⑥）**：报告 §5(b):2 制度建议写「同步扫描/加注所有引用它的下游登记」，而本轮自己漏了 `FIX:243`、`FIX:273-276/282-286`，并把 `PENDING:101` 挂错文件 ⇒ **制度建议对、本轮执行未自洽**。本件 §3(c)/§5(a) 已逐条补齐这些下游。

### 6(c) 系统性建议：根因（技术层 + 制度层）

**技术根因（本会话逐行核源码 `_spi_src_lines_out.txt`）**：
1. **k → 1 bit 有损压缩**：`any()`（`check_d27.py:86-87`、`check_d29.py:83-87`、`check_d30.py:83-87`、`check_d28.py:96-97`）、`ok &= good`（`_rs_carrier_scan.py:343`）、`min(pos)`（`:165`）、`any(n in txt)`（`:229`）把 k≥2 个输入的存活合成单一布尔，输出里**看不出哪根输入死了**（`CHECK_MASKING_INJECT.md:25,138`、`MASKING_EFFECT_AUDIT.md:335`）。
2. **无逐输入自检**：三 gate 连 `SELF_TEST` 记号都没有（`CHECK_MASKING_INJECT.md:124-126,179`），PASS 是一行裸布尔；scanner 有 `SELF_TEST` 名但 6 条负控压进同一个 `ok`（`_rs_carrier_scan.py:343-346`）⇒「有自检名、无逐输入自检实」。
3. **PASS 未绑定输入指纹**：台账只记 `exit=0`，没有被核脚本 SHA256+字节数、没有语料快照指纹 ⇒ 语料从 627 漂到 655（本会话再漂到 662）也无人察觉（`MASKING_EFFECT_AUDIT.md:384`、`CHECK_MASKING_INJECT.md:640`）。
4. **命令口径与登记口径不一致且未标注**：`REFSYNC_SCOPE_FIX.md:251` 正式登记双 needle，编排方实跑单 needle；撰写人另多传 `--include-refuting`（`MASKING_EFFECT_AUDIT.md:385-386`）⇒ 无法区分「N1 坏了」与「我少传了一个参数」。
5. **「通过」语义过载**：台账把「格式门禁 exit=0」「数值核证通过」「真机 rc=0」「编译 exit=0」「工作流门槛 exit=0」全部写成「通过/PASS」，不区分**形式要件 vs 实质结论**、**我亲跑 vs 来源声明**。`RULING_D27.md:58` 自己就警告过「不得签为本阶段执行通过」。
6. **没有「失效回写」机制（制度根因，最直接）**：题给【复核】⑥ 独立验证 `lead/needle_norm_20261109/_nn_REPORT.md:365`「每个 needle 单独跑一次自检…掩盖效应」、`:402`「自检必须跑，且自检自身必须有覆盖度门禁」、`NEEDLE_NORMALIZATION.md:364` 同，而 `REFSYNC_SCOPE_FIX.md` 全文未加注（与 `MASKING_EFFECT_AUDIT.md:379-381` 一致）。**本会话未重跑该有界定位，记为题给材料记录**。发现与登记脱节 ⇒ 失效 PASS 继续以「已验证」身份留在台账。
7. **门禁本身是「结果导向」弱检查**：只查词/标题/引用计数存在性，不查语义与数值（`check_d27.py:81-94`），天然容易「结果碰巧对」而掩盖检验失效（`CHECK_MASKING_INJECT.md:515`「最像逐项已验却最易误读」）。

**台账登记制度改法（8 条，建议，不执行；台账只由 Leader 改）**：
1. **效力状态字段**：每条 PASS 加 `status ∈ {VERIFIED, UNTRUSTWORTHY, STALE_INPUT, UNVERIFIED, HISTORICAL_OBSERVATION}`，并强制打 `形式要件 / 实质结论` 与 `我亲跑 / 来源声明` 两个标签。
2. **失效回写通道**：任何复核/审计判定某 PASS 不可信，**必须**在原登记行就地加注（不删原文、不改数字），并同步扫描/加注所有引用它的下游登记；由 Leader 统一执行。本轮 7 处 A/B 级正是缺这条通道的直接后果。
3. **强制指纹绑定**：PASS 登记须带「被核对象 SHA256 + 字节数 + 输入语料快照指纹 + 命令全文（逐字含所有参数）+ stdout 落盘路径及其 sha256」。
4. **禁止裸 `exit=0` 当验收结论**：k≥2 输入的检验必须给「逐输入判定表」并显式写 `AGGREGATE = AND_k(...)`；k=1 须说明理由。
5. **负控 + 坏针注入设为登记前置**：报 PASS 前必须跑「去掉/替换一根输入」对照，且结果可区分（`DISTINGUISHABLE_PASS`）；门禁与诊断量（`EXCLUSIVE`/`HITSET`/`MASKED_*`）严格分离。
6. **口径一致性检查**：新登记须与既往同名登记逐字比对命令参数；不一致即标「非登记口径」，不得据此下交付结论（照 `MASKING_EFFECT_AUDIT.md:390`）。
7. **定期失效扫描**：把「台账中仍引用了已标 `UNTRUSTWORTHY` 检验的行」做成机械可查项——但这个新门禁**自身**也必须遵守 `AND_k` 与坏针注入，避免重蹈覆辙（自检的自检）。
8. **区分「历史记录」与「现行验收」**：真机/编译/工作流门槛的一次性 `exit=0` 标 `HISTORICAL_OBSERVATION`，不得冒充现行验收证据；被引用时自动带限定。

**以后登记 PASS 必附清单（10 条，基于 `MASKING_EFFECT_AUDIT.md:388-399` §6.4 + 本轮新增绑定/状态要求）**：
1. **固定绑定行** `被核对象 SHA256 = <64hex>，字节数 = <n>`（值与实跑同发）。
2. **完整实跑命令逐字**（含每个 `--needle / --pattern / --ext / --max-depth / --include-refuting`）+ CWD + `python -I -X utf8` + 绝对路径 + Python 版本；源脚本前后 `hashlib` 零改动自证。
3. **输入语料/文档快照指纹** + 文件数/行数（防漂移）。
4. **stdout 原文落盘路径** + 该输出文件 sha256；正文只引「命令 + 输出文件:行」。
5. **逐输入判定表**：k 行 `input_i: EXIT / 汇总行 / 逐条负控 want/got / PASS|FAIL`；`PER_NEEDLE_SELFTEST` 必须来自真实 k 次独立运行，不得由语料推断。
6. **`AGGREGATE = AND_k(...)` 显式值** + 判定依据（`rc==0 ∧ PASS ∧ 无 FAIL`）。
7. **坏针注入对照**：每根依次换保证零命中的哨兵，`AGGREGATE` 须变 FAIL；给出 `DISTINGUISHABLE_PASS`；注入坏针仍 PASS ⇒ 原 PASS 作废。
8. **口径一致性声明**：与既往登记逐字比对；不一致即标「非登记口径」，不得据此下交付结论。
9. **效力/范围标签**：`形式要件 vs 实质结论`、`我亲跑 vs 来源声明`、`VERIFIED vs HISTORICAL_OBSERVATION`、`UNTRUSTWORTHY / STALE_INPUT / UNVERIFIED`。
10. **未验项显式清单**（搜不全/跑不动/没实跑一律写「未验」，不补造）+ **单调性声明**（依赖 `min(pos)`/argmin 时跑「多加一根输入」对照）。

### 6(d) 判不了什么 / 未验项（逐条如实列）

1. **未验：三件裁决实质结论的真值**。本会话**未重跑** `_d27_facts.py` / `_d29_facts.py` / `_d30_facts.py` 数值断言、未重算统计/原探针/合成反例（`RULING_D27.md:3,75` 自述亦同）。本件只判「实质结论**不依赖**失效 PASS」这一**依赖结构**，不判结论真值（题给【复核】③ 同判）。
2. **未验：其余 ~170 行 PASS 类登记是否可信**。未逐条做坏针注射；`MASKING_EFFECT_AUDIT.md:404-405` 亦自认「D 段 4110 个提及自检/负控的文件、B 段 1436 处 `any()/min()` 未逐个实跑」。
3. **未验：`check_d25.py` / `check_d26.py` / N-1 门禁是否有同族缺陷**。题给【清点】直读源码未见 OR 多元组，本会话未注射实证 ⇒ 列 C 级，不冒充「已证明有效」。
4. **未验：历史上是否真有「死词」**。本次是主动注入；三件原词在文档里都实际命中（本会话实算 `RULING_D27.md` 引用 = 71 系题给【清点】记录，本会话未独立重算该 regex；六件裁决书字节数与登记全一致为**本会话实跑**），故「结果碰巧对」。
5. **未验：`REFSYNC_SCOPE_FIX.md:251` 当时那三个数字**。语料已漂移（登记 627 → 题给【清点】655 → 本会话 662），`CHECK_MASKING_INJECT.md:392` 记三次数都不同；只能判「坏针仍 `SELF_TEST=PASS`」这一性质。
6. **未验：修复后长期效果**。甲' 外壳本会话只在既有沙箱实跑 4/4 gate 与 scanner 三跑，**未部署成门禁、未跑修复后回归**（`CHECK_MASKING_INJECT.md:628` 同声明；`_sp_andk.py` 是演示外壳，见 §5(b) 部署陷阱）。
7. **未验：`require_all=True` 的 AND 项是否有逐词可归因问题**（`CHECK_MASKING_INJECT.md:695` ⑦ 亦列为未验）。
8. **未验：git 历史上输入是否变过**。六个 `d*_ruling_20261106/` 目录 `git status --short` 全为 `??`（未跟踪）、无 `git log` 可比；只能证「当前字节数/截断 sha 与登记一致」。
9. **未验：`GOAL:261/262/327` 的 verify_hooks 修复在现盘是否仍有效**。需构建产物与 ini，属构建/部署态，本轮铁律不授权。
10. **未验：`GOAL:246/263/303/1192` 等 `KNOWN_FALSE_PASS` 命中行是否属同类**。它们含「不可信/作废/演算」等不同语境（本会话 `_spi_lines_out.txt:40/45/46/49` 仅直读，未逐行定级），需 Leader 人工判读。
11. **未做全库无界扫描**：题给【清点】/【复核】均记首次 unbounded `glob('**/...', recursive=True)` >120s 未完成被 `TaskStop` 停止（复核 `task exec_c39fc698…` status=killed），该命令**不计为通过**；本会话所有 scanner 数字基于 `--max-depth 2 --ext .md` 有界口径。`MASKING_EFFECT_AUDIT.md:403` 亦自认三次数均为有界扫描。
12. **未在本会话独立复跑的题给材料记录**：`_sp_tally.py` / `_sp_classify.py` / `_sp_dist.py` / `_sp_final_checks.py` / `_sp_broad.py` / `_sp_report.py` 的 36/265/174/210 行等计数、`_sp_hashcheck.py` 的 `ALL_MATCH`（本会话用自写 `_spi_hash.py` 等价复算）、`FIX:292-299` 逐字比对 `EQUAL=False` 的 `python -c`、`_nn_REPORT.md:365/402` 有界定位、题给【清点】的 `git status`/`git log` 与 `_sp_4gate_compare.py` 首轮（本会话已独立复跑后者）。以上均标「题给材料记录 / 本会话未复跑」，不冒充本会话通过。
13. **判不了「该不该撤回裁决」的最终决定**：本件只给建议，台账只由 Leader 改；本会话对两台账及所有列名只读件的改动 = **0**（九件指纹初/末态全相符、两账 `MM` 与初始快照一致、HEAD 未变）。

### 6(e) 本会话实跑命令与输出（逐条，可复核）

| # | 命令（`cd D:/Project/ra2-campaign-forge`） | 输出要点 |
|---|---|---|
| 1 | `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/stale_pass_20261109/_spi_hash.py"` | 九件逐项 `MATCH=True`；`NINE_ALL_MATCH = True`；复核对象 `f2d8fb32…d391` / 52161 B / 390 行 |
| 2 | `python -I -X utf8 ".../_spi_lines.py" > ".../_spi_lines_out.txt"` | 153 行逐行原文（`PENDING:92/101/103/105/109/110/111/113/117/129…`、`GOAL:261/262/327`、`FIX:234/243/251-253/273-286/292-299`、四件裁决正文） |
| 3 | `python -I -X utf8 ".../_spi_src_lines.py" > ".../_spi_src_lines_out.txt"` | 385 行源码/审计原文（四 gate、scanner、MEA:176-253/375-405、CMI:25-695） |
| 4 | `python -I -X utf8 ".../_spi_verify.py" > ".../_spi_verify_out.txt"` | 两账 381/9757 行；四件命中 PENDING 3 行 GOAL 0；`exit0` 8/51、`PASS` 3/90；五短语两账 0；广义 GATE_EXIT0 `[92,105,117,129,162,186,199]`；7 处错指原文；四件 `h2=8`；9 行绑定行 `ALL_64HEX=True / ALL_MATCH_BASE=True` |
| 5 | `python -I -X utf8 ".../_sp_4gate_compare.py" > ".../_spi_4gate_out.txt"; echo "EXIT=$?"` | `EXIT=0`；d27/d29/d30/d28 四组 BASE→INJ sha 与逐字 `OUTPUT_IDENTICAL=True / EXIT_IDENTICAL=True` |
| 6 | `python -I -X utf8 ".../_sp_andk.py" > ".../_spi_andk_out.txt"; echo "EXIT=$?"` | `EXIT=0`；4/4 `AND_k=True`、`BAD_NEEDLE_CAUGHT=True (sentinel EXIT=1)`、`DISTINGUISHABLE_PASS=True` |
| 7 | `python -I -X utf8 ".../lead/refsync_scope_20261109/_rs_carrier_scan.py" --needle "不能定位当年错误步骤" --needle "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ" --max-depth 2 --ext .md > ".../_spi_rs_broken_out.txt" 2>&1; echo "EXIT=$?"` | `EXIT=0`；`:8` 双针含哨兵、`:10` `662/151/25`、`:750-755` 六负控全 PASS、`:756` `SELF_TEST = PASS` |
| 8 | 同 7，`--needle "只能判「不可复现」"` 单针 → `_spi_n1_out.txt` | `N1_EXIT=1`；`662/95/23`；`:501` `:22 got=<not-scanned>`、`:503` `SELF_TEST = FAIL` |
| 9 | 同 7，`--needle "不能定位当年错误步骤"` 单针 → `_spi_n2_out.txt` | `N2_EXIT=0`；`662/108/25`；`:574-579` 6/6、`:580` `SELF_TEST = PASS` |
| 10 | `python -I -X utf8 -c` 六件裁决书字节数/sha16 比较 | 17658/12258/13197/13897/15373/15545 全 `MATCH=True`；D29 `325c950eec4d3275`、D30 `d5afc90c50bbf57` |
| 11 | `python -I -X utf8 -c` 门禁标题数 / `check_*.py` 出现 / GATE 广义口径 | 四件 `h2=8`（7 必需小节在 `check_d*.py:7-17`）；四件失败门禁在裁决书 0 次；`门禁+exit=0` = 7 行，`门禁+实跑+exit=0` = 6 行 |
| 12 | `git status --short -- <两台账 + 八只读域>` / `git rev-parse HEAD` / `_spi_hash.py` 末态 | 两账 `MM`、八域 `??`；HEAD `26574589aa8401e8f3f2934680a1ea7109bafa2d`；`NINE_ALL_MATCH = True` |

**纪律核对**：零真机、零采样代码；「注射」全为静态文本副本/CLI 参数替换；Python 全 `python -I -X utf8` + 绝对路径；指纹全 `hashlib`；未 commit / 未 push；未改两台账、未改任何登记、未改任何只读件；唯一写域 `lead/stale_pass_20261109/`。
