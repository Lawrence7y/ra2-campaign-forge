# 失效 PASS 清点与分级处置（_sp_STALE_PASS_CENSUS.md）

**执行者**：失效 PASS 清点员（subagent）
**日期**：2026-11-09
**性质**：只做清点与建议，**绝不修改台账、绝不修改任何登记**。台账只由 Leader 改。
**写域**：仅 `lead/stale_pass_20261109/`，全部件前缀 `_sp_`。
**铁律遵守**：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）。本轮所谓「注入」全部是**把静态文本检查脚本的 OR 词表在沙箱副本里换成零命中哨兵**（纯测试数据替换），与进程注入无关。
**未 commit、未 push**。Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`。

---

## 0 复核回件·绑定行（被核对象指纹，本会话 hashlib 独立实算）

命令：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/stale_pass_20261109/_sp_hashcheck.py"`
输出：`ALL_MATCH = True` / `N_FILES = 9`（9 件 SHA256 与字节数逐项等于编排方实跑指纹，0 差异）。

被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518
被核对象 SHA256 = 99131e8aa03717c555a56b7cee75cf747b4127287e2cc1ec9b6bef5656da3c6c，字节数 = 56575
被核对象 SHA256 = 2f55283ef3380c6cb5915b2e8654a5506061ccb667a986d397b45a10a2f9119f，字节数 = 45536
被核对象 SHA256 = 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c，字节数 = 3764
被核对象 SHA256 = 2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14，字节数 = 3906
被核对象 SHA256 = 6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd，字节数 = 3926
被核对象 SHA256 = 9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57，字节数 = 16053
被核对象 SHA256 = 83b215ccbbf2c3e221c247e7bd9c7c221fddcf9472977d2df8902bf1b94ec65e，字节数 = 49958

（依次对应 `lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md`、`lead/check_masking_20261109/CHECK_MASKING_INJECT.md`、`lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md`、`lead/d27_ruling_20261106/check_d27.py`、`lead/d29_ruling_20261106/check_d29.py`、`lead/d30_ruling_20261106/check_d30.py`、`lead/refsync_scope_20261109/_rs_carrier_scan.py`、`lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md`。末次复跑 `python -I -X utf8 .../_sp_hashcheck.py | tail -3` 仍得 `ALL_MATCH = True`，两件台账会话末未被我改动。）

---

## 1 第一步 核实与清点

### 1(a) 两件台账里各有哪些行登记了这四件的 PASS

**独立扫描命令**：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/stale_pass_20261109/_sp_scan.py" > .../_sp_scan_raw.json`（逐行匹配 `check_d27|check_d29|check_d30|_rs_carrier_scan|carrier_scan|SELF_TEST|REFSYNC_SCOPE_FIX`）+ `.../_sp_broad.py`（宽口径复核）+ `.../_sp_final_checks.py`（逐字短语计数）。

**输出**：`FOUR_HITS_COUNT= 3 {'PENDING': 3, 'GOAL': 0}`；`FOUR_NAME_COUNT = 3`，逐字计数 `check_d27` PENDING=1 GOAL=0、`check_d29` 1/0、`check_d30` 1/0、`_rs_carrier_scan` 0/0、`SELF_TEST` 0/0、`REFSYNC_SCOPE_FIX` 0/0。`GOAL mentions D-27/D-29/D-30 = 0 / 0 / 0`。

**两件台账中合计 3 行，全部在 `lead/PENDING_DECISIONS.md`，`GOAL_THREE_TARGETS_20261018.md` 中 0 行**：

| # | file:line | 原文（逐字） |
|---|---|---|
| 1 | `lead/PENDING_DECISIONS.md:92` | `  裁决书 \`lead/d30_ruling_20261106/RULING_D30.md\`（13,197 B / \`d5afc90c50bbf57b…3983d04f\`）+ 事实核证 \`FACTCHECK.md\`（11,394 B）+ \`_d30_facts.py\`/\`_out.txt\`；门禁 \`check_d30.py\` 实跑 **exit=0**（2026-11-07 复跑仍 PASS）。` |
| 2 | `lead/PENDING_DECISIONS.md:105` | `  裁决书 \`lead/d29_ruling_20261106/RULING_D29.md\`（12,258 B / \`325c950eec4d3275…7212afb\`）+ \`FACTCHECK.md\`（12,647 B）+ \`_d29_facts.py\`/\`_out.txt\`；门禁 \`check_d29.py\` 实跑 **exit=0**。` |
| 3 | `lead/PENDING_DECISIONS.md:129` | `  裁决书 \`lead/d27_ruling_20261106/RULING_D27.md\`（17,658 B，71 处引用）+ 事实核证 \`FACTCHECK.md\` + \`_d27_facts.py\`/\`_out.txt\`；门禁 \`check_d27.py\` 实跑 **exit=0**。` |

**★ 必须如实纠正一处口径**：第四件 `_rs_carrier_scan.py` 的 PASS **在两件台账里 0 行登记**。它写在**交付件** `lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md` 里，而且不止 `:251`：

- `REFSYNC_SCOPE_FIX.md:251`：`EXIT=0`；`scanned files = 627 ; carrier occurrences = 80 ; distinct files = 19`（现盘，含自引；撰写时点 622/73/18）；… `SELF_TEST = PASS`（6/6，含 `:215 want=ASSERTION got=ASSERTION`、`_ve_DRAFT_S609.md:22 want=REFUTING_QUOTE got=REFUTING_QUOTE`）
- `REFSYNC_SCOPE_FIX.md:252`：`EXIT=0`；… `SELF_TEST = PASS`
- `REFSYNC_SCOPE_FIX.md:253`：`EXIT=0`；… B 段仍 `6 / 6`；`SELF_TEST = PASS`

（`REFSYNC_SCOPE_FIX.md` 属编排方列名的绝对只读件，不是两件台账之一。任务背景「台账与交付件里」的表述在此需分开：台账 3 行 / 交付件 3 行。）

### 1(b) 除这四件外，台账里还有多少「门禁 exit=0」「PASS」「验证通过」类登记（总数与分布）

**四个口径全部实跑，数字并列，不合并冒充**：

| 口径 | 命令 | PENDING | GOAL | 合计 |
|---|---|---|---|---|
| `exit=0` 类（含 `EXIT=0`/`CL_EXIT=0`/`LINK_EXIT=0`/`final_exit=0`，大小写不敏感） | `_sp_tally.py` | 8 | 51 | **59 行** |
| 独立 `PASS` token（含 `SELF_TEST = PASS`） | `_sp_tally.py` | 3 | 90 | **93 行** |
| 「门禁 实跑 **exit=0**」显式句式 | `_sp_tally.py` `gate_run` | **7** | 0 | **7 行** |
| 「门禁」字面（任意上下文） | `_sp_tally.py` `gate_word` | 14 | 22 | 36 行 |
| 宽口径联合正则（exit0/PASS/通过/门禁/实跑/复跑/全绿/CL_EXIT…） | `_sp_tally.py` `broad` | 27 | 238 | **265 行** |
| 紧口径交集（去掉「授权边界/零真机/carrier/注入」噪声后命中上述任一 PASS 类关键词） | `_sp_classify.py` | 16 | 158 | **174 行**（BY_CAT 重叠：EXIT0=59 / PASS=93 / VERIFY=73 / GATE_RUN=10） |
| 互斥单标签分类（每行进一类） | `_sp_dist.py` | 23 | 187 | **210 行**（OTHER_PASS_WORD=108 / OTHER_EXIT0=48 / TEST_SUITE_PASS=36 / GATE_EXIT0=7 / KNOWN_FALSE_PASS=7 / COMPILE_EXIT0=4） |

**逐字事实**：`验证通过`、`机械检查通过`、`逐项通过`、`SELF_TEST`、`REFSYNC_SCOPE_FIX` 在**两件台账里出现次数均为 0**（`_sp_final_checks.py` 输出）。即台账并不用「验证通过」这个措辞，用的是「实跑 exit=0」「PASS」「全绿」「N/N PASS」等。

**「门禁 实跑 exit=0」7 行逐行（`_sp_tally.py` GATE_RUN_LINES，全在 PENDING）**：

- `PENDING:92` check_d30 ← 四件之一
- `PENDING:105` check_d29 ← 四件之一
- `PENDING:117` check_d28 ← **本会话新发现同族缺陷（见 1(c)）**
- `PENDING:129` check_d27 ← 四件之一
- `PENDING:162` check_d26
- `PENDING:186` check_d25
- `PENDING:199` N-1（`lead/a_residual_20261106/`，17 条 = CONFIRMED 12 / PARTIAL 5，门禁 exit=0）

⇒ **除四件（台账 3 行）外，显式「门禁 exit=0」还有 4 行**（:117 / :162 / :186 / :199）；其余为 59 行 exit=0 类、93 行 PASS 类、265 行宽口径中的非门禁项，主要是：离线单测（`GOAL:7053` `PASS=85 FAIL=0`、`GOAL:7196/7197` `_w5_diff_proof.py`/`_w5_test.py` 6 条全 PASS、`GOAL:9220` `test_except_freshness.py` 14/14、`GOAL:9341/9349` T3 候选 14 测全绿、`GOAL:6896` `SUMMARY PASS=67 FAIL=0`）、编译/链接（`GOAL:261` `CL_EXIT=0 / LINK_EXIT=0`、`GOAL:325` `CL/CL2/LINK 全 exit=0`）、真机趟件 `rc=0`/`EXIT=0`（`GOAL:260/619/658/1734` 等）、工作流确定性门槛 `exit=0`（`GOAL:5999/6362/6499/6502/6621/9009/9330/9420` 等）、git 门禁（`PENDING:348`）。

**已自认失效的一类（不冒充「仍有效的 PASS」）**：`GOAL:261`（`verify_hooks 假绿`、0/13 因 `0==0` 判 PASS、13 槽完全失明）、`GOAL:262`（`假绿已修并四档实跑全绿`、v2 ini `24/24 PASS`）、`GOAL:327`（`原版对合并件报 0/0 却 PASS；v2 报 13/13`）。这 3 行**自己已标注为假绿并已修**，不是一条仍挂着的「已验证」PASS。

### 1(c) ★ 这些登记里有多少基于「已被证明不可信的检验」

**判据（A 级）**：坏输入注入实证——把该检验的 k≥2 输入中的一根换成保证零命中的哨兵 `TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ`，输出仍 `PASS` / `EXIT=0` / `SELF_TEST = PASS`，且与基线逐字一致 ⇒ 该 PASS 无法察觉死输入，**不可信**。

**独立复跑（本会话，全部 `python -I -X utf8` + 绝对路径，沙箱副本，源脚本零字节改动）**，命令与输出落 `.../_sp_4gate_compare_out.txt`，驱动 `.../_sp_4gate_compare.py`：

| 被核对象 | BASE sha256 → INJ sha256 | BASE 输出 / EXIT | 注射后输出 / EXIT | 逐字一致 |
|---|---|---|---|---|
| `check_d27.py` | `3b769d7c…7671c` → `f404f58783ab4da0…7d7af89` | `PASS: D-27 八项机械检查通过；裁决书引用 71 处` / 0 | 同左 / 0 | True |
| `check_d29.py` | `2a50b09a…d780f14` → `2399e95a43eaafa4…580ced5` | `PASS` / 0 | `PASS` / 0 | True |
| `check_d30.py` | `6cb73796…05ee9fd` → `b1670537e12a6d7c…9a7129` | `PASS` / 0 | `PASS` / 0 | True |
| **`check_d28.py`（新发现）** | `5b42a34a…9d268` → `f5ae184c…4692314` | `PASS: D-28 全部 8 项机械检查通过 (exit 0)` / 0 | 同左 / 0 | True |

前 3 件的注射后 sha256 与 `CHECK_MASKING_INJECT.md:211/271/331` 登记值逐字符相符；`check_d28.py` 是本会话新增（编排方未点名）。第四件 scanner（`--needle` 参数层注入，不改源）：

```
$ python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan.py" --needle "不能定位当年错误步骤" --needle "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ" --max-depth 2 --ext .md > ".../_sp_rs_broken_out.txt" 2>&1; echo "EXIT=$?"
EXIT=0
_sp_rs_broken_out.txt:8   needles = ['不能定位当年错误步骤', 'TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ']
_sp_rs_broken_out.txt:719-724  6 条负控全 PASS
_sp_rs_broken_out.txt:725      SELF_TEST = PASS
```

**结论数字**：

- **两件台账里基于已被证明不可信检验的登记 = 4 行**：`PENDING:92`（d30）、`PENDING:105`（d29）、`PENDING:129`（d27）、**`PENDING:117`（d28，本会话新证）**。其中 3 行是编排方点名、我独立复现；第 4 行是我直读 `check_d28.py:90` 发现 OR 词表 `("历史数字","1681")` 后独立注射实证，编排方材料未列。
- **交付件里另 3 行**：`REFSYNC_SCOPE_FIX.md:251`、`:252`、`:253`（均 `SELF_TEST = PASS`）。
- 合计 **7 处 A 级登记**（4 台账 + 3 交付件）。
- `PENDING:162`（d26）、`PENDING:186`（d25）、`PENDING:199`（N-1）：我直读 `check_d26.py:85-97` / `check_d25.py:58-69` 未见 OR 多元组（都是单字面量或 AND），但**未做坏针注射实证** ⇒ 不算「已证明不可信」，列 C 级。
- 其余 ~170 行：**未逐条注射实证**，不得计入「已证明不可信」，也**不得当作「已证明有效」**。

### 1(d) 有哪些登记基于其它检验（可能仍有效）·区分

按检验族区分（我**只做方法区分、未逐条重跑**，故一律标注「可能仍有效·未复核」）：

| 族 | 代表 file:line | 检验对象 | 与四件的关系 |
|---|---|---|---|
| 离线单测 / 自检套件 | `GOAL:6896` `PASS=67 FAIL=0`、`GOAL:7053` `PASS=85 FAIL=0`、`GOAL:7196/7197` `_w5_diff_proof.py`/`_w5_test.py`、`GOAL:7362/7401/7404`、`GOAL:9220` `test_except_freshness.py 14/14`、`GOAL:9341/9349` T3 14 测全绿、`GOAL:7566-7569` | 单元/差分/新鲜度断言 | 不同脚本、不同检验；多数带 N/N 计数 |
| 编译 / 链接 | `GOAL:261` `CL_EXIT=0 / LINK_EXIT=0`、`GOAL:325`、`GOAL:384`、`GOAL:7566` | 工具链退出码 | 与文本门禁无关 |
| 真机趟件 `rc=0`/`EXIT=0` | `GOAL:260/619/658/1734/3119`、`PENDING:209` | 一次性运行观测 | 历史观测，非现行验收 |
| 工作流确定性门槛 | `GOAL:5999/6362/6499/6502/6621/7352/9009/9330/9420` | 报告结构/长度/标记 | 与四件无关 |
| git 门禁 / 路径门禁 | `PENDING:348`、`GOAL:46/107/129/262/297/301` | 提交 diff / 路径口径 | 与四件无关 |
| 事实核证脚本 | `RULING_D29.md:19`（`_d29_facts.py` 退出码 0）、`RULING_D30.md:76`（`corpus: {"files":104,"samples":1125992}`、`checks: "All numeric assertions passed"`）、`PENDING:129` 所引 `_d27_facts.py` | 数值/逻辑断言 | **不是** `check_d*.py` 格式门禁 |
| 已自认假绿并修复 | `GOAL:261/262/327` | `verify_hooks` | 已标注失效+已修，非仍挂着的 PASS |

**区分要点**：`check_d27/d29/d30/d28` 的 docstring 自述是 **format/mechanical gate**（`check_d27.py:1` "Read-only D-27 gate"、`check_d29.py:1` "Read-only D-29 **format** gate"、`check_d30.py:1` "Read-only D-30 **format** gate"、`check_d28.py:1` "Read-only D-28 **mechanical** gate"），只查「文件在不在 / `main:`或`q1:`行 / 7 个二级标题 / 小节里有没有某个词 / 引用≥8 / FACTCHECK 含 selfBias」（`check_d27.py:53-100`），**不查数值、不查推理**。而事实核证走的是 `_dNN_facts.py` 另一条线。二者在台账里被并列成一句「裁决书 + FACTCHECK + 门禁 exit=0」，正是「语义过载」的根因之一（见 5(a)）。

---

## 2 第二步 失效分级（本任务核心）

### 2(a) 三级（+1 级）定义，判据写清

| 级 | 名称 | **判据（三者处置完全不同）** | 处置 |
|---|---|---|---|
| **A** | **已证明不可信** | 检验**本身**已被坏输入注入实证失效：一根输入换成零命中哨兵后仍 `PASS`/`EXIT=0`/`SELF_TEST=PASS` 且与基线逐字一致 ⇒ 该 PASS 不能作为「每根输入都有效」的证据。**注意：判的是 PASS 不可信，不是结论错**（本轮原词在文档里都实际命中，结果碰巧对）。 | 立刻加注「不可信」+ 用甲' 外壳重跑；不得再以「已验证」身份被引用 |
| **B** | **输入已变** | 检验**方法可能有效**，但它当时跑的输入（文档/语料）后来变了：登记的数字/文件数与现盘不可复现，或登记命令口径与实跑口径不一致。PASS 未绑定输入指纹 ⇒ 效力过期。 | 绑定当前输入指纹重跑；旧数字保留但标「历史口径」，不改写、不冒充复现 |
| **C** | **需复核** | 无法判断：**未做**坏针注入、**未**绑定指纹、脚本未识别、或只有裸 `exit=0` 无逐输入输出。既不能判不可信，也不能判有效。 | 重跑（同甲' 外壳）后才能继续以「已验证」身份引用；在此之前标 `UNVERIFIED` |
| **D** | **已自认失效/已修**（增补级） | 登记**自己**已写明「假绿/不可信/已修」，不是一条仍挂着的现行「已验证」PASS。 | 保持不动，仅作历史准确性核对 |

**★ 一句话区分三者**：A = 「尺子坏了」；B = 「尺子可能没坏，但量的东西换了」；C = 「尺子没验过，不知道」。

### 2(b) 逐条登记归类

| # | file:line | 对象 | 级 | 依据 |
|---|---|---|---|---|
| 1 | `PENDING:92` | `check_d30.py` exit=0 / 复跑仍 PASS | **A** | 编排方 + 本会话 `_sp_4gate_compare_out.txt`：`"误报率"`→哨兵仍 `PASS` / 0 |
| 2 | `PENDING:105` | `check_d29.py` exit=0 | **A** | 同上：`"前提"`→哨兵仍 `PASS` / 0 |
| 3 | `PENDING:129` | `check_d27.py` exit=0（含「引用 71 处」） | **A** | 同上：`"卡顿不存在"`→哨兵输出一字不变；`CHECK_MASKING_INJECT.md:231` |
| 4 | `PENDING:117` | `check_d28.py` exit=0 | **A（新）** | 本会话：`check_d28.py:90` `("历史数字","1681")`→`"1681"`换哨兵仍 `PASS: D-28 全部 8 项机械检查通过` / 0 |
| 5 | `REFSYNC_SCOPE_FIX.md:251` | `_rs_carrier_scan.py` `SELF_TEST = PASS` 6/6 | **A + B** | A：本会话坏针注入仍 6/6 PASS；`MASKING_EFFECT_AUDIT.md:380,384`。B：登记 `627/80/19`，本会话同口径 `--max-depth 2 --ext .md` 得 `655/144/24`（`_sp_rs_broken_out.txt:10`）；`CHECK_MASKING_INJECT.md:392` 记录三次数都不同 |
| 6 | `REFSYNC_SCOPE_FIX.md:252` | 同上 `SELF_TEST = PASS` | **A + B** | 同上 |
| 7 | `REFSYNC_SCOPE_FIX.md:253` | 同上 B 段 6/6 `SELF_TEST = PASS` | **A + B** | 同上 |
| 8 | `PENDING:162` | `check_d26.py` exit=0 | **C** | 直读 `check_d26.py:85-97` 无 OR 多元组；未注射实证 |
| 9 | `PENDING:186` | `check_d25.py` exit=0 | **C** | 直读 `check_d25.py:58-69` 无 OR 多元组；未注射实证 |
| 10 | `PENDING:199` | N-1「门禁 exit=0」 | **C** | 未识别到具体脚本，无可复跑对象 |
| 11 | `GOAL:261 / :262 / :327` | `verify_hooks` 假绿 | **D** | 原文自标「假绿」「已修」「v2 报 13/13」 |
| 12 | 其余 59 行 exit=0 类 / 93 行 PASS 类 / 265 行宽口径（扣上述） | 单测、编译、真机、工作流门槛、git 门禁 | **C（批量）** | 未逐条重跑；多数是 `HISTORICAL_OBSERVATION` 而非现行验收声明 |

**B 级的诚实边界**：三件裁决书的登记字节数与当前盘**完全一致**（`python -I -X utf8 -c ...` 实跑：`RULING_D27.md` 17658、`RULING_D29.md` 12258、`RULING_D30.md` 13197、`RULING_D28.md` 13897、`RULING_D26.md` 15373、`RULING_D25.md` 15545 全部 `MATCH=True`；d29/d30 截断 sha 前缀 `325c950e…7212afb` / `d5afc90c…3983d04f` 亦与登记相符）⇒ **三件 gate 的文档输入未变，不列 B 级**。但这些目录 `git status --short` 全为 `??`（未跟踪），无 `git log` 可比 ⇒ 我只能证「当前与登记一致」，**判不了历史上是否变过**（见 5(d)）。B 级目前只坐实在 scanner 的语料上。

### 2(c) ★ 逐条「若该 PASS 其实为假，下游什么结论会被推翻」

**统一的前提认识**：这些 PASS 是**形式/机械门禁**（见 1(d)），且本轮实证「结果碰巧对，判的是 PASS 不可信，不是结论错」（`CHECK_MASKING_INJECT.md:695` ②）。所以「PASS 为假」推翻的是**「该登记已验证」这一证据资格**，不是裁决的事实与推理。逐条：

| # | 若 PASS 为假，被推翻的 | **不被推翻的** |
|---|---|---|
| `PENDING:92`（D-30） | ① `RULING_D30.md` 的 7 个二级标题/`q1: 戊`行/「三档权衡的实质」小节含 `93.98`/`误报率`/引用≥8/`selfBias` 等**格式合规**未获有效验证；② 台账把该裁决书作为「已核证交付」的措辞失效；③ `PENDING:101` 引 `RULING_D30.md:6,:20,:28,:47` 作为其它条目的证据时，其格式保证失效 | `q1: 戊` 不选 k 档、D-13 PAUSE、目标①机制挂账不解除、三档实算 93.98%/68.11%/8.68%、Q4 配额 1.55–6.96%、Q5 `verified=false` —— 均来自裁决员结论与 `_d30_facts.py` 数值核证（`RULING_D30.md:76`），与 gate 无关 |
| `PENDING:105`（D-29） | ① `RULING_D29.md` 格式合规未获有效验证（「冲突是否成立」含 `互斥`/`前提`、`:191` 边界、`q1: 丁` 行、引用≥8）；② 该裁决书被 `RULING_D30.md:6`、`PENDING:101/113`、`D-28` 链引用的**格式保证**失效 | `q1: 丁`、保留四条约束、否决串行机制、S/T/C 不等式论证（`RULING_D29.md:19` 实跑 `_d29_facts.py` 的 `pureLogicalCounterexampleMs`）、情景 B 作废、`:191` 适用边界 —— 均来自裁决员结论与事实核证 |
| `PENDING:129`（D-27） | ① `RULING_D27.md` 格式合规未获有效验证（「未背书」含 `外推`/`卡顿不存在`、7 标题、引用≥8、`FACTCHECK` 含 `selfBias`）；② 输出所宣称的「裁决书引用 71 处」这一**由 gate 报出的数字**失去可验证性（但我用同一 regex 独立实算得 **71**，`_sp_final_checks.py`）；③ `PENDING:125` 引 `RULING_D27.md:12,:28,:32,:42,:48` 支撑 D-28 的格式保证失效 | `main: B` 立 D-13b、采样 PAUSE、11 条新证据（1737/1681/56、`≥1s`=0、最长 566.96ms、中位 129.93ms、90.42%）、三处对 Leader 表述的更正、循环式语义论证成立、100ms 阈值质疑被证伪、D-13b 后续论证要求 —— 来自 `_d27_facts.py` 与题给 F/D |
| `PENDING:117`（D-28，**新**） | ① `RULING_D28.md` 格式合规未获有效验证（「D 链处置」含 `历史数字`/`1681`）；② `PENDING:103`（D-29）、`PENDING:113`、`RULING_D29.md:6` 等对 `RULING_D28.md:30,:32,:34,:36,:42` 的引用，其上游格式保证失效；③ 若按「只修 3 件」处理，这一条会**继续以已验证身份漏网** | `q1: A` / `q2: 丁`、两链不互锁、B 链独立复审优先、`2.5+100+48+2=152.5ms` 条件算术、四组情景 16 段实测数=0 —— 来自裁决员结论与 `BUDGET_MODEL.json` |
| `REFSYNC_SCOPE_FIX.md:251-253` | ① §5.2「可复用自检脚本」整段交付口径失效：`SELF_TEST = PASS` 不再能证明「6 条负控逐条有效」；② §5.2 表内 `627/80/19`、`947/86/23`、`5500/2429/81` 三个施工/审计数字失去「自检护航」；③ `:254`「换 needle 结果随之变化 ⇒ 脚本不硬编码结论」的论证减弱；④ §5.3 的 R1–R6 规则中 **R6 负控自检**的可信度；⑤ B 段 fix list（`occurrences=4 ; distinct=4`）作为「施工数」的验收依据 | R1–R5 的规则文本、`classify_line()` 的引号/否定词表逻辑（`REFSYNC_SCOPE_FIX.md:260`）本身是代码事实，不因 PASS 失效而变；`MASKING_EFFECT_AUDIT.md:380-381` 已独立指出 `:22` 仅由第二 needle 命中、N1 有 43 行掩蔽（`MASKING_EFFECT_AUDIT.md:375-377`） |

**★  strongest downstream finding**：我在当前语料上按甲' 口径逐 needle 独立跑 scanner（`_sp_agg_*.txt`），得到 `["只能判「不可复现」"]` 单跑 `SELF_TEST = FAIL`（`:22 got=<not-scanned>`，`_sp_agg_f0b7c1.txt:579-581`）、`["不能定位当年错误步骤"]` 单跑 `SELF_TEST = PASS`（`_sp_agg_87196b.txt:661`）⇒ **AND_k = FAIL**。即 `REFSYNC_SCOPE_FIX.md:251` 那个 PASS 不只是「不可信」，在正确的逐输入门禁下**应为 FAIL**。诚实限定：我的单跑是 `--max-depth 2 --ext .md` 有界口径、当前语料 655/656 文件，**不是**对登记时 627 文件口径的复现，故只判性质不判当时数字（`CHECK_MASKING_INJECT.md:392` 亦如此声明）。

### 2(d) 优先处置顺序（哪些必须最快修）

1. **P0**：`REFSYNC_SCOPE_FIX.md:251`（以及 `:252/:253`）——它是**现行交付件的验收口径**、是「可复用自检脚本」会被后续任务复制的模板，且 A+B 双级、且正确门禁下应为 FAIL。它属绝对只读件 ⇒ **只能建议 Leader 加注**，我无权改。
2. **P0**：`PENDING:92 / :105 / :129` —— 编排方点名、三条裁决链式互引、仍是「已验证」身份。
3. **P0（不可漏）**：`PENDING:117`（`check_d28.py`）—— 本会话新证的同族 A 级。若只修三件，它会漏网；且它位于 D-27↔D-29↔D-30 引用链上游。
4. **P1**：`PENDING:162 / :186 / :199` —— C 级，但与上面同一批 `门禁 exit=0` 句式，用同一甲' 外壳顺手重跑成本极低；跑完即可确定是升 A 还是保持有效。
5. **P1**：`GOAL:261/:262/:327` 之外的「已自认假绿」类复核一遍有无别的（本会话扫描 `KNOWN_FALSE_PASS` = 7 行，`GOAL:246/261/262/263/303/327/1192`，其中只有 261/262/327 与 verify_hooks 相关，其余是「不可信/作废/门禁演算」等不同语境，需 Leader 人工判读）。
6. **P2**：其余 ~170 行 PASS 类 —— 不逐条撤回，走制度整改（§5(b)）；只抽检「裸 exit=0 且无指纹绑定」的高风险行。
7. **P3**：`GOAL:261/:262/:327`（D 级）—— 无需动作。

---

## 3 第三步 这四件的 PASS 失效会不会影响已入账的裁决

### 3(a) D-27 / D-29 / D-30 三件分别是什么裁决（台账正文）

- **D-27**（`PENDING:127-158`，裁决书 `RULING_D27.md:1-7` `main: B`）：**立 D-13b** —— 「D-13 依据新证据重裁：立 D-13b，面向当前保留的短停样本重开『离线』方案设计与『不含采样实现』的离线单测；D-13 采样代码与执行继续 PAUSE」。附 11 条新证据（1737 候选 / 1681 true / 56 false；`>=1s` 为 0、最长 566.96ms、中位 129.93ms、`100<=d<200ms` 1520 条 = 90.42%）；三处对 Leader 表述的撤销/收窄（「长停不存在」外推无效、负控语义被高估、D-26「先补四项」系整理）；循环式语义论证成立（`_stall_probe.py:169-189`、`:211-224`）；「100ms 阈值排除长停」质疑被证伪；两条纠正（`>1s 即终局`错误、`n=1681` 与 `n=1737` 不同口径）；D-13b 后续论证要求（完整预算、合成时序、未验项）。不解除目标①机制挂账，D-14 双口径维持。
- **D-29**（`PENDING:103-113`，`RULING_D29.md:1-6` `q1: 丁`）：**保留四条约束，只否决串行机制** —— 保留 `:177`「发生后 50ms 内捕获」、`:190`「检测后 <50ms、裕量 ≤20ms」、`:191` 拒止原则、口径 B；否决「等满 100ms 才触发、随后才捕获」的串行机制；允许在既定边界内继续离线论证「提前保存 + 事后分类」独立方案；工程可达性未验，D-13 PAUSE。`S/T/C` 不等式（`T−S≥100ms` 且 `C≥T` ⇒ `C−S≥100ms>50ms`）只在串行前提下成立；`:191` 适用边界是规范解释，不是删除拒止原则。
- **D-30**（`PENDING:90-101`，`RULING_D30.md:1-5` `q1: 戊`）：**不选任何 k 档进入实现/执行** —— 保留「提前候选 + 事后分类」的离线论证资格，`k=10` 作高召回成本离线基准、`k=25` 边界敏感性对照、不采纳 `k=50` 作为满足 `:177` 的现行方案，不得为降误报牺牲 `:177`；三档实算（18ms/28294/93.98%/5.94%、48ms/5343/68.11%/31.46%、98ms/1866/8.68%/90.09%）；Q4 配额 26 个非空窗 → 1.55%/4.34%/6.96% 且不放开配额；Q5 扰动 `verified=false` 四项依赖全需真机；判据下一步要求重新设计并离线比较；驳正 20–30 FPS 只能说明条件重叠（12.09%）。D-13 PAUSE、目标①机制挂账不解除。

### 3(b)(c) ★ 实质结论依赖那个失效的 PASS 吗？——逐条判

**判：三件全部「不依赖」。PASS 只是形式要件。** 依据（全部是「文件:行」）：

1. **门禁自述是格式检查**：`check_d27.py:1`、`check_d29.py:1`（"format gate"）、`check_d30.py:1`（"format gate"）；实际检查项在 `check_d27.py:53-100`、`check_d29.py:75-105`、`check_d30.py:75-105` —— 文件存在/非空、`main:`或`q1:` 合法值行、7 个二级标题、小节正文含某词、引用计数 ≥8、`FACTCHECK.md` 含 `selfBias`。**没有任何数值、统计或逻辑断言**。
2. **裁决书自己明确否认把门禁计为通过**：
   - `RULING_D27.md:3`「本阶段未重跑统计、原探针、合成反例或**门禁**」；`:58`「『Leader亲跑exit=0』和复核通过只能标来源声明或已有字段，**不得签为本阶段执行通过**…本阶段未运行 `check_stall_def.py`、核证脚本、原探针或合成反例」；`:69`「**不背书本阶段未执行的门禁**…已通过」；`:77`「未运行 `check_stall_def.py` 或**其他门禁**」。
   - `RULING_D29.md:67`「题给『裁决书事实核对意见』为 approved=true…**这是题给核对意见，不是本撰写阶段门禁通过证明**」；`:71`「**未运行原探针、门禁**、历史语料重算…**不记通过**」。
   - `RULING_D30.md:76`「…**不把原探针、`check_feasibility.py` 或原门禁计为通过**；后三者本次未运行」；`:62`「未改门禁」。
3. **实质结论的来源是另一条线**：三件的定谳来自「题给《裁决员结论》main/q1/bounds + 独立事实核证 `_d27_facts.py` / `_d29_facts.py` / `_d30_facts.py` 输出 + 题给 F/D 材料」。实证：`RULING_D29.md:19` 记载实跑 `_d29_facts.py` 退出码 0 并给出 `pureLogicalCounterexampleMs`；`RULING_D30.md:76` 记载 `corpus: {"files":104,"samples":1125992}` 与 `checks: "All numeric assertions passed"`；`RULING_D27.md:12` 引用 `_d27_facts_out.txt:9`。台账 `PENDING:101/113/125/156-158` 的证据行也指向 `STALL_EVENTS.json`、`_stall_probe.py`、`BUDGET_MODEL.json`、`EARLY_TRIGGER_FEASIBILITY.md`。
4. **审计报告自认**：`CHECK_MASKING_INJECT.md:695`「① 判不了裁决书事实与推理（三件 docstring 自称 format gate）」；「② …本次是**主动注入**，三件原词在文档里都实际命中，故**结果碰巧对，判的是 PASS 不可信，不是结论错**」。`CHECK_MASKING_INJECT.md:642` 的修复建议也只是「把 `PENDING_DECISIONS.md:92,105,129` 三处 `exit=0` 换成『逐输入 PASS 表 + 指纹』」，**未建议重审裁决**。
5. **独立旁证**：我用 gate 同一 regex 实算 `RULING_D27.md` 引用数 = **71**（`_sp_final_checks.py`），与 gate 输出一致；三件裁决书字节数与登记一致、d29/d30 sha 前缀与登记一致 ⇒ 格式事实本身也没坏，坏的是「这个 PASS 能不能证明它」。
6. **第四件**：`_rs_carrier_scan.py` 的 PASS 与三件裁决**无引用关系**（两台账 0 行提及），它服务的是 `REFSYNC_SCOPE_FIX.md` 的语料范围修复交付，不影响任何 D-27/D-29/D-30 结论。

**逐条结论**：
- **D-27：形式要件失效，实质结论不受影响**。需修形式（登记加注 + 重跑），不需重审裁决。
- **D-29：形式要件失效，实质结论不受影响**。同上。
- **D-30：形式要件失效，实质结论不受影响**。同上。
- **附加**：`check_d28.py`（`PENDING:117`）失效同样是形式要件；D-28 的 `q1:A / q2:丁` 结论亦不受影响，但它是 D-29/D-30 的引用上游，形式链需一并补。

**诚实限定**：我判的是**依赖结构**（实质结论并非由该 PASS 推出），依据是上述文档自述与代码结构；我**没有**重跑 `_d27_facts.py` / `_d29_facts.py` / `_d30_facts.py` 的数值断言，因此**不能**进一步断言「实质结论已被本会话独立验证为正确」。另：`PENDING:90-101/103-113/127-158` 的登记文本把「裁决书 + FACTCHECK + 门禁 exit=0」并列成「已验证」交付包，那个**「已验证」的证据资格**确实失效——这是必须修的部分。

### 3(d) 「形式要件失效」与「实质结论失效」区分统计

| 类别 | 处数 | 明细 |
|---|---|---|
| **形式要件失效** | **7 处** | 台账 4 行（`PENDING:92/105/117/129`）+ 交付件 3 行（`REFSYNC_SCOPE_FIX.md:251/252/253`） |
| **实质结论失效** | **0 处** | 三条裁决（D-27/D-29/D-30）及 D-28 的实质结论均不依赖失效 PASS；第四件不涉裁决 |
| **需复核才能定论（C 级）** | ~170+ 行 | 其余 PASS 类登记未逐条注射实证；另含 `_dNN_facts.py` 数值核证脚本本会话未重跑 |
| **已自认失效/已修（D 级）** | 3 行 | `GOAL:261/262/327` |

---

## 4 第四步 处置建议

### 4(a) 逐条建议：加注 / 重跑 / 撤回 / 保持不动（含理由）

> **总原则**：**不撤回任何裁决登记**；只**撤回「该 PASS 作为已验证证据」的效力**（以「加注」实现，不删原文、不改数字）。台账只由 Leader 改，以下均为建议。

| file:line | 建议 | 理由 |
|---|---|---|
| `PENDING:92` | **加注 + 重跑** | A 级；`check_d30.py` 坏针仍 PASS。加注「本 PASS 经坏输入注入实证不可信，2026-11-09」；随后按甲' 重跑并登记新结果。裁决 `q1: 戊` 不动 |
| `PENDING:105` | **加注 + 重跑** | A 级；同上（`check_d29.py`） |
| `PENDING:129` | **加注 + 重跑** | A 级；同上（`check_d27.py`）。注意输出里「引用 71 处」我已独立实算为 71，加注应区分「数字对」与「PASS 不可信」 |
| `PENDING:117` | **加注 + 重跑** | A 级（本会话新证）；漏修会让同族缺陷继续挂在链上游 |
| `REFSYNC_SCOPE_FIX.md:251` | **加注（Leader 执行）+ 重跑** | A+B 级，且正确 AND_k 下应为 FAIL。建议追加限定（照抄 `MASKING_EFFECT_AUDIT.md:380` 的建议文本）：「本 PASS 系 N1∪N2 并集口径，不构成逐 needle 有效性证据；`:22` 仅由第二 needle 命中；详见 `MASKING_EFFECT_AUDIT.md`」。旧数字保留不改写 |
| `REFSYNC_SCOPE_FIX.md:252` / `:253` | **加注（Leader 执行）+ 重跑** | 同样 `SELF_TEST = PASS`，且 `:253` 标「仅供审计，不作施工数」，漂移影响更大 |
| `PENDING:162` | **重跑** | C 级；`check_d26.py` 未见 OR 多元组但未经注射实证；顺手用甲' 外壳跑一遍定级 |
| `PENDING:186` | **重跑** | C 级；同上（`check_d25.py`）。注：`PENDING:160` 明示 D-26 的 D-13 部分已由 D-27 重裁，但 **D-14 定谳继续有效**，故仍值得跑 |
| `PENDING:199` | **重跑（先识别脚本）** | C 级；N-1 门禁未识别到具体脚本，须先定位再跑；若定位不到标「未验」 |
| 其余 ~170 行 PASS 类 | **保持不动 + 制度约束** | 异质（真机/编译/单测/工作流门槛/历史观测），多为一次性观测记录；大规模撤回会不成比例地使整本台账失效。改为：新登记强制 §5(c) 清单 + 对「裸 exit=0 无指纹」行抽检 |
| `GOAL:261 / :262 / :327` | **保持不动** | D 级，原文已自标「假绿」「已修」「v2 报 13/13」，无现行假 PASS 声明 |
| 三条裁决正文 | **保持不动** | 实质结论不依赖失效 PASS；只修形式登记 |

**关于「撤回」**：本轮**不建议撤回任何登记行或裁决**。唯一应「撤回」的是那 7 处 PASS 的**证据资格**，实现方式是就地加注 + 状态字段改为 `UNTRUSTWORTHY`/`STALE_INPUT`，而非删行。理由：删行会破坏台账的可追溯性与引用链（`PENDING:101/113/125` 等仍引用这些裁决书），且 `CHECK_MASKING_INJECT.md:642` 与 `MASKING_EFFECT_AUDIT.md:380` 两处审计建议也都只要求「加注/换口径」，不要求撤回。

### 4(b) ★ 重跑的可行方案：甲' 外壳（逐输入独立跑 + AND_k）

**依据（文件:行）**：`MASKING_EFFECT_AUDIT.md:176`（`AGGREGATE = AND_k(REAL per-needle self-test)`，每根单独跑未修改扫描器，`EXIT=0 AND 6 条负控逐条匹配 WANT`；`HITSET/MASKED_LINES/EXCLUSIVE` 只报告不门禁）、`:180-182`（甲' 推荐、零侵入、被审脚本 0 行改动）、`:202-211`（判据：`PER_NEEDLE_SELFTEST` 必须来自真实 k 次运行，`DISTINGUISHABLE_PASS = FALSE` 时结果碰巧对也不可信）、`:213-253`（可粘贴片段，含逐条 `want/got` 比对与坏针注入）、`:335`、`:388-399`（§6.4 报 PASS 前 10 条清单）、`:390-396`；`CHECK_MASKING_INJECT.md:570-628`（**修正版**外壳：`bad_needle_injection()` 不信任并集布尔，要求 `AND_k(broken)` 变 FAIL；`:664` 说明原模板因「用被掩蔽的并集布尔判 caught」而不可用，勿沿用 `_cm_AUDIT.md:469-536` 旧模板）、`:634-642`（落地成本、修复顺序）。

**四件具体重跑法**：

1. **三 gate + d28（OR 词表类）**：把「k 个输入」定义为该 gate 的 `require_all=False` OR 词表。`check_d27.py:84` `("外推","卡顿不存在")`、`check_d29.py:76` `("互斥","前提")`、`check_d30.py:76` `("93.98","误报率")`、`check_d28.py:90` `("历史数字","1681")`。甲' 外壳对**每个词 w** 生成一份沙箱副本，把 OR 元组换成单元素 `(w,)`，`python -I -X utf8 <绝对路径副本>` 独立跑一次，捕获 `EXIT/STDOUT/逐检查项`；`AGGREGATE = AND_k(rc==0 ∧ 输出含 PASS ∧ 无 FAIL)`；再对每根依次换 `TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ`，要求 `AGGREGATE` 变 FAIL（`BAD_NEEDLE_CAUGHT`）；输出 k 行 `input_i: PASS/FAIL`。
   - **路径坑必须处理**：`check_d27.py:8` 用 **CWD 相对** `DIRECTORY = Path("lead/d27_ruling_20261106")`；`check_d29.py:50` / `check_d30.py:50` 用 `Path(__file__).resolve().parent`；`check_d28.py:54-55` 用 `Path(__file__).resolve().parents[2] / "lead" / "d28_ruling_20261106"`。三者沙箱布局不同，我本会话已各自搭好并实跑通过（`CHECK_MASKING_INJECT.md:154` 也记录撰写人第一次因漏此点得到 6 个 `EXIT=2` 作废重跑）。
2. **`_rs_carrier_scan.py`（--needle 类）**：直接逐 needle 各跑一次**完整扫描**（`--needle <n>` 单值，其余参数与登记逐字一致），每次要求 `EXIT=0 ∧ SELF_TEST=PASS ∧ 6 条负控逐条 want/got 匹配`；`AGGREGATE = AND_k`；再把其中一根换成保证零命中哨兵，要求 `AGGREGATE = FAIL`。可粘贴实现见 `MASKING_EFFECT_AUDIT.md:216-249`。
3. **门禁/诊断分离**：`EXCLUSIVE(k)` / `HITSET` / `MASKED_LINES` 只作诊断量；**不得**用「语料独占行>0」「独占负控≥1」替代 `AND_k`（`MASKING_EFFECT_AUDIT.md:176,393`；乙'/丙' 已被复核判 partial，勿沿用 `_me_design.py:PLAN_A/B/C`）。
4. **指纹绑定**：每次跑绑定「被核脚本 SHA256 + 字节数 + 输入语料文件数/快照指纹」；stdout 原文落盘并算 sha256；依赖 `min(pos)`/argmin 时加「多加一根输入」单调性对照（`MASKING_EFFECT_AUDIT.md:391,398`）。

**★ 本会话已实跑验证该方案可行（不是只提建议）**：

```
$ python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/stale_pass_20261109/_sp_andk.py" > .../_sp_andk_out.txt
```
输出（4/4 gates）：`AND_k(over 2 real per-word runs) = True`、`BAD_NEEDLE_CAUGHT = True (sentinel EXIT=1)`、`DISTINGUISHABLE_PASS = True`；每根词单跑 `EXIT=0 PASS=True`，哨兵单跑 `EXIT=1` 且打印 `[4]/[6]` 归因行（`_sp_andk_out.txt`）。即：**旧 gate 的原始 OR 运行不可信，但拆成逐输入独立跑 + AND_k 后，同样的输入能给出可区分、可归因、坏针被抓的判定**——这正是「重跑才算可信」的实证。

scanner 侧（`_sp_agg_f0b7c1.txt:575-581` / `_sp_agg_87196b.txt:655-661`）：`["只能判「不可复现」"]` 单跑 `SELF_TEST=FAIL`（`:22 got=<not-scanned>`）、`["不能定位当年错误步骤"]` 单跑 `SELF_TEST=PASS` ⇒ 登记的双针 `SELF_TEST=PASS` 在 `AND_k` 下**应为 FAIL**；坏针配置 `[N2, SENTINEL]` 仍 6/6 PASS（`_sp_rs_broken_out.txt:719-725`）⇒ 掩蔽实证。**限定**：这些单跑用 `--max-depth 2 --ext .md` 有界口径、当前语料 655/656 文件，不是登记时 627 文件口径的复现，只判性质不判当时数字。

### 4(c) 「重跑后如何登记」模板（建议，不执行）

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
stdout 原文落盘：<写域/_sp_xxx_out.txt>，该文件 SHA256 = <64hex>
结论等级：形式要件（不涉实质结论）；与旧登记 <file:line> 的关系 = 取代其 PASS 证据资格 / 旧行保留并加注未删
未验项：<逐条写「未验」，不补造>
```

（模板中「被核对象 SHA256 = <64hex>，字节数 = <n>」为本任务规定的固定绑定行格式；值与实跑同发。）

### 4(d) 哪些不值得重跑（理由）

| 对象 | 不重跑理由 |
|---|---|
| `GOAL:261 / :262 / :327` `verify_hooks` 假绿 | 原文已自标「假绿」「已修」「v2 报 13/13 / 24/24 PASS」，是历史记录非现行验收声明；复跑需 `build/ra2render_merged.dll` 与 `ra2render.ini` 的合并产物，属构建/部署态，本轮铁律不授权且无增量信息 |
| 真机趟件 `rc=0`/`EXIT=0` 类（`GOAL:260/619/658/1734/3119` 等） | 一次性观测记录（HISTORICAL_OBSERVATION）；复跑需启动游戏，被零真机铁律禁止；且它们本就不是「现行验收」 |
| 编译 `CL_EXIT=0 / LINK_EXIT=0` 类（`GOAL:261/325/384`） | 依赖当时的工具链/中间文件状态；现在复跑不等于复现当时，价值低；`GOAL:261` 自己已记「`.rej` 存在即合并未完成，不能只看 exit code」 |
| 工作流确定性门槛 `exit=0`（`GOAL:5999/6362/6499/...`） | 一次性交付门槛（报告六节/长度/标记），对象已定稿；重做需重跑整条 workflow，不成比例 |
| 已被后续裁决取代的部分 | 如 `PENDING:160` 明示「D-26 的 D-13 部分已由 D-27 重裁为 B（立 D-13b）」——该部分的 PASS 重跑无意义；但 **D-14 定谳继续有效**，所以 `PENDING:162` 整行仍建议顺手跑（见 4(a)） |

---

## 5 第五步 系统性建议

### 5(a) 根因分析

1. **k → 1 bit 有损压缩**（技术根因）：`any()`（三 gate 的 OR 项）、`ok &= good`（`_rs_carrier_scan.py:343`）、`min(pos)`（`:165`）把 k≥2 个输入的存活合成单一布尔，输出里**看不出哪根输入死了**（`CHECK_MASKING_INJECT.md:25,138`、`MASKING_EFFECT_AUDIT.md:335`）。兄弟输入一活，坏针即被掩蔽。
2. **无逐输入自检**：三 gate 连 `SELF_TEST` 记号都没有（`grep -c -F "SELF_TEST"` = 0/0/0，`CHECK_MASKING_INJECT.md:124-126,179`），PASS 是一行裸布尔；scanner 有 `SELF_TEST` 名但 6 条负控压进同一个 `ok`（`_rs_carrier_scan.py:343-346`）——「有自检名、无逐输入自检实」。
3. **PASS 未绑定输入指纹**：台账只记 `exit=0`，没有被核脚本 SHA256+字节数、没有语料快照指纹 ⇒ 语料从 627 漂到 655 也无人察觉（`MASKING_EFFECT_AUDIT.md:384`「PASS 未绑定语料指纹」、`CHECK_MASKING_INJECT.md:640`）。三次数（627/947/5500 与审计三次 6030/6088/6122）互不相同正是不绑定的后果。
4. **命令口径与登记口径不一致且未标注**：`REFSYNC_SCOPE_FIX.md:251` 正式登记是**双 needle**，编排方实跑单 needle；撰写人另多传 `--include-refuting`（`MASKING_EFFECT_AUDIT.md:385-386`）。口径差未登记 ⇒ 无法区分「N1 坏了」与「我少传了一个参数」。
5. **「通过」语义过载**：台账把「格式门禁 exit=0」「数值核证通过」「真机 rc=0」「编译 exit=0」「工作流门槛 exit=0」全部写成「通过/PASS」，不区分**形式要件 vs 实质结论**、**我亲跑 vs 来源声明**。`RULING_D27.md:58` 自己就警告过「『Leader亲跑exit=0』…不得签为本阶段执行通过」，但台账登记仍把三者并列成一句。
6. **没有「失效回写」机制**（制度根因，最直接）：下一轮 `_nn_REPORT.md:365` 与 `NEEDLE_NORMALIZATION.md:364` **已经**登记了「掩盖效应」并建议「每个 needle 单独跑一次自检」，`_nn_REPORT.md:402` 自认「本次 FAIL 之所以暴露，是编排方用单 needle 重跑了负控自检」——但**上一轮交付件 `REFSYNC_SCOPE_FIX.md` 全文无「掩盖/假 PASS/不可信」**（`MASKING_EFFECT_AUDIT.md:379-381`，`_mev_final_out.txt:2-6`）。发现与登记脱节 ⇒ 失效 PASS 继续以「已验证」身份留在台账。
7. **门禁本身是「结果导向」的弱检查**：只查词/标题/引用计数存在性，不查语义与数值（`check_d27.py:81-94`）。这类门禁天然容易「结果碰巧对」而掩盖检验失效，也容易被误读成「八项机械检查通过」（`CHECK_MASKING_INJECT.md:515`：「最像逐项已验却最易误读」）。

### 5(b) ★ 台账登记制度该怎么改（建议，不执行；台账只由 Leader 改）

1. **给每条 PASS 登记加「效力状态」字段**：`status ∈ {VERIFIED, UNTRUSTWORTHY, STALE_INPUT, UNVERIFIED, HISTORICAL_OBSERVATION}`，并强制打 `形式要件 / 实质结论` 与 `我亲跑 / 来源声明` 两个标签。
2. **建立失效回写通道**：任何复核/审计判定某 PASS 不可信，**必须**在原登记行就地加注（不删原文、不改数字），并同步扫描/加注所有引用它的下游登记；由 Leader 统一执行。本轮 7 处 A/B 级就是缺少这条通道的直接后果。
3. **强制指纹绑定**：PASS 登记必须带「被核对象 SHA256 + 字节数 + 输入语料快照指纹 + 命令全文（逐字含所有参数）+ stdout 落盘路径及其 sha256」。
4. **禁止裸 `exit=0` 当验收结论**：k≥2 输入的检验必须给「逐输入判定表」并显式写 `AGGREGATE = AND_k(...)`；k=1 须说明理由。
5. **负控 + 坏针注入设为登记前置**：报 PASS 前必须跑「去掉/替换一根输入」对照，且结果可区分（`DISTINGUISHABLE_PASS`）；门禁与诊断量（`EXCLUSIVE`/`HITSET`/`MASKED_*`）严格分离。
6. **口径一致性检查**：新登记须与既往同名登记逐字比对命令参数；不一致即标「非登记口径」，不得据此下交付结论（照 `MASKING_EFFECT_AUDIT.md:390`）。
7. **定期失效扫描**：把「台账中仍引用了已标 `UNTRUSTWORTHY` 检验的行」做成机械可查项——但这个新门禁自身也必须遵守 `AND_k` 与坏针注入，避免重蹈覆辙（自检的自检）。
8. **区分「历史记录」与「现行验收」**：真机/编译/工作流门槛的一次性 `exit=0` 标 `HISTORICAL_OBSERVATION`，不得冒充现行验收证据；被引用时自动带限定。

### 5(c) 「以后登记 PASS 时必须附带什么」清单（10 条，逐条可执行）

基于 `MASKING_EFFECT_AUDIT.md:388-399` §6.4 十条，补入本轮新增的绑定/状态要求：

1. **固定绑定行**：`被核对象 SHA256 = <64hex>，字节数 = <n>`（本任务规定格式，值与实跑同发）。
2. **完整实跑命令逐字**（含每个 `--needle / --pattern / --ext / --max-depth / --include-refuting`）+ CWD + `python -I -X utf8` + 绝对路径 + Python 版本；源脚本前后 hashlib 零改动自证。
3. **输入语料/文档快照指纹** + 文件数/行数（防漂移）。
4. **stdout 原文落盘路径** + 该输出文件的 sha256；正文只引「命令 + 输出文件:行」。
5. **逐输入判定表**：k 行 `input_i: EXIT / 汇总行 / 逐条负控 want/got / PASS|FAIL`；`PER_NEEDLE_SELFTEST` 必须来自真实 k 次独立运行，不得由语料推断。
6. **`AGGREGATE = AND_k(...)` 显式值** + 判定依据（`rc==0 ∧ PASS ∧ 无 FAIL`）。
7. **坏针注入对照**：每根依次换保证零命中的哨兵，`AGGREGATE` 须变 FAIL；给出 `DISTINGUISHABLE_PASS`；注入坏针仍 PASS ⇒ 原 PASS 作废。
8. **口径一致性声明**：与既往登记逐字比对；不一致即标「非登记口径」，不得据此下交付结论。
9. **效力/范围标签**：`形式要件 vs 实质结论`、`我亲跑 vs 来源声明`、`VERIFIED vs HISTORICAL_OBSERVATION`、`UNTRUSTWORTHY/STALE_INPUT/UNVERIFIED`。
10. **未验项显式清单**（搜不全/跑不动/没实跑一律写「未验」，不补造）+ **单调性声明**（依赖 `min(pos)`/argmin 时跑「多加一根输入」对照）。

### 5(d) 这条工作判不了什么（如实列）

1. **判不了裁决书事实与推理是否正确**：本会话未重跑 `_d27_facts.py` / `_d29_facts.py` / `_d30_facts.py` 的数值断言、未重算统计/原探针/合成反例（`RULING_D27.md:3,75` 自述亦同）。我只判「实质结论**不依赖**失效 PASS」这一**依赖结构**，不判结论真值。
2. **判不了其余 ~170 条 PASS 类登记是否可信**：未逐条做坏针注入；`MASKING_EFFECT_AUDIT.md:404-405` 亦自认「D 段 4110 个提及自检/负控的文件、B 段 1436 处 `any()/min()` 未逐个实跑」。
3. **判不了 `check_d25.py` / `check_d26.py` / N-1 门禁是否有同族缺陷**：只直读源码未见 OR 多元组，未做注射实证 ⇒ 列 C 级，不冒充「已证明有效」。
4. **判不了历史上是否真有「死词」**：本次是主动注入；三件原词在文档里都实际命中（我实算 `RULING_D27.md` 引用 = 71；六件裁决书字节数与登记全一致），故「结果碰巧对」。
5. **判不了 `REFSYNC_SCOPE_FIX.md:251` 当时那三个数字**：语料已漂移（627→655），`CHECK_MASKING_INJECT.md:392` 记录三次数都不同；只能判「坏针仍 `SELF_TEST=PASS`」这一性质。
6. **判不了修复后的长期效果**：甲' 外壳我只在本会话沙箱实跑 4/4（d27/d29/d30/d28）与 scanner 的逐针单跑，**未部署成门禁、未跑修复后回归**（`CHECK_MASKING_INJECT.md:628` 同样声明）。
7. **判不了 `require_all=True` 的 AND 项是否有逐词可归因问题**：审计 `CHECK_MASKING_INJECT.md:695` ⑦ 亦列为未验。
8. **判不了 git 历史上输入是否变过**：六个 `d*_ruling_20261106/` 目录 `git status --short` 全为 `??`（未跟踪）、`git log -- <RULING_D27.md>` 无输出；只能证「当前字节数/截断 sha 与登记一致」。
9. **判不了 `GOAL:261/262/327` 的 verify_hooks 修复在现盘是否仍有效**：需构建产物与 ini，属构建/部署态，本轮铁律不授权。
10. **判不了 `GOAL:246/263/303/1192` 等 `KNOWN_FALSE_PASS` 命中行是否属同类**：它们含「不可信/作废/演算」等不同语境，需 Leader 人工判读，我未逐行定级。
11. **未做全库无界扫描**：首次 unbounded 扫描（默认全扩展名、无深度上限）>120s 未完成，被我 `TaskStop` 停止；所有 scanner 数字基于 `--max-depth 2 --ext .md` 有界口径（`_sp_rs_broken_out.txt:2`）。`MASKING_EFFECT_AUDIT.md:403` 亦自认三次数均为有界扫描。
12. **判不了「该不该撤回裁决」的最终决定**：我只给建议，台账只由 Leader 改；本会话对两台账及所有列名只读件的改动 = **0**。

---

## 6 写域产物清单（全部 `_sp_` 前缀，未 commit / 未 push）

| 件 | 用途 |
|---|---|
| `_sp_STALE_PASS_CENSUS.md` | 本报告 |
| `_sp_hashcheck.py` | 9 件编排方指纹独立 hashlib 核对（ALL_MATCH=True） |
| `_sp_scan.py` / `_sp_scan_raw.json` | 两台账四件命中 + PASS 宽口径扫描 |
| `_sp_broad.py` / `_sp_broad_raw.json` / `_sp_report.py` / `_sp_report.txt` | 宽口径词扫描与可读汇总 |
| `_sp_classify.py` / `_sp_classify_raw.json` | 紧口径 PASS 分类（174 行） |
| `_sp_dist.py` / `_sp_dist_raw.json` | 互斥单标签分布（210 行） |
| `_sp_tally.py` / `_sp_tally_raw.json` | 多口径精确计数 |
| `_sp_final_checks.py` | docstring / 逐字短语计数 / 引用数 |
| `_sp_gen_injected.py` / `_sp_gen_d29d30.py` / `_sp_gen_d28.py` / `_sp_gen_word.py` | 沙箱注射副本生成器（只读源，stdout 重定向） |
| `_sp_4gate_compare.py` / `_sp_4gate_compare_out.txt` | 四 gate 基线 vs 坏针注射对照（真 EXIT 捕获） |
| `_sp_andk.py` / `_sp_andk_out.txt` | 甲' 逐输入独立跑 + AND_k + 坏针捕获（4/4） |
| `_sp_rs_broken_out.txt` | scanner 坏针注入 stdout 原文 |
| `_sp_agg_87196b.txt` / `_sp_agg_f0b7c1.txt` | scanner 逐 needle 独立跑 stdout 原文 |
| `_sp_sandbox/` | 全部沙箱副本与文档拷贝（源脚本零字节改动） |

**会话末复核**：`git status --short lead/PENDING_DECISIONS.md lead/GOAL_THREE_TARGETS_20261018.md` 仍为初始快照的 `MM`（非本会话所致）；`python -I -X utf8 .../_sp_hashcheck.py | tail -3` 仍得 `ALL_MATCH = True` / `N_FILES = 9`。
