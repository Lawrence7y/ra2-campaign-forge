# _cf_REPORT.md — check_*.py 同族普查与模板溯源回件

范围：零真机、零采样代码、绝对只读（除唯一写域 `lead/check_family_20261109/`）；未改任何 `check_*.py`、自检脚本、台账；未 commit / push。Python 一律 `python -I -X utf8` + 绝对路径；指纹 `hashlib`。

## 绑定行（被核对象 = 四件生产门禁 + 模板母本，本会话独立实算）

被核对象 SHA256 = 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c，字节数 = 3764
被核对象 SHA256 = 5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268，字节数 = 4539
被核对象 SHA256 = 2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14，字节数 = 3906
被核对象 SHA256 = 6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd，字节数 = 3926
被核对象 SHA256 = 0018116a350de46dd98bbecc5f7aae15a3bd599a4e82bb5d43f3dc688c7f9f65，字节数 = 4245

（依序：`lead/d27_ruling_20261106/check_d27.py`、`check_d28.py`、`check_d29.py`、`check_d30.py`、`lead/d26_ruling_20261106/check_d26.py`。命令：`python -I -X utf8 -c` 读 bytes 后 `hashlib.sha256`。）

## 一、全库普查

- 实跑 `find . -type f -name "check_*.py" 2>/dev/null | sort` → **173 件**（编排方实跑为 25 件，是其口径内的子集；`_cf_full_census.md` 为全 173 行清单：rel / bytes / sha16 / lines / mtime / orch_any / require_all / pass_print；全 64 位指纹在 `_cf_census_out.json:all_files[*].sha256`）。
- 独立核对编排方 25 件：`bytes`、`sha256[:16]`、`orch_any`、`require_all` **逐项吻合，`orch_field_mismatches=[]`**（`_cf_census.py` 实跑）。★ 但编排方 `pass` 列**自相矛盾**：`check_d27.py` 与 `_sp_sandbox/check_d27_baseline.py` 同为 `3b769d7c64c27251…` / 3764 B、`:100` 同为 `print(f"PASS: D-27 …")`，却记为 `[]` 与 `[100]`（`_cf_census_out.json:orch_pass_contradictions`）。故本回件改用可复现口径 `pass_print = ^\s*print\(.*PASS`。
- 173 件分布（`_cf_census_out.json:summary`）：`any(生成器含成员测试)` 53 / 编排方等价 `orch_any` 48；`require_all` 29；`all(` 61（`all` 生成器 28）；`print("PASS` 字面 33、f-string 15、宽口径 `print(...PASS...)` 64；`return 0` 等出口 60；`requirements = (` 29；section 提取器 42。
- 1(c) ★「any() + 单行 PASS」组合：严格口径（`orch_any ∩ pass_literal`）= **28 件**；宽口径（`orch_any ∩ pass_print`）= **46 件**。**但该筛法漏掉 `check_d28.py` 与 `check_d27.py`**：d28 的 `:97` 是 `any(present)`（布尔列表 Name，非 `any(x in y for…)`）；d27 的 `:100` 是 f-string PASS。四件确诊同族里字面筛只捞到 d29/d30 两件 ⇒ 这正是「必须有代码级判据」的实证（`_cf_census.py` 与 `_cf_detect.py` 两次实跑）。
- 1(d) 「写法像但逐输入 / all() 不属本族」：`check_d25.py`（无 `any()`，单词检查 `:58,:60`）、`check_d26.py`（`:85,87,90` 的 `any()` 是「跨多个 section body 存在性」，不是 k 词 OR 词表）、`check_b2b_candidate_review.py:330` / `_r2.py:358` / `check_feasibility.py:119…` / `check_stall_def.py:244` 均**在 for 循环内逐项 print PASS**（`for p in passes: print(f"PASS {p}")`）⇒ 逐检查项可归因；`all()` 只在 d29/d30 的 `require_all=True` 分支（`:83`），按 `CHECK_MASKING_INJECT.md:128,443` 不属本族。另有 2026-10-02 的 `out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom*.py`：有 `any(w in low for w in OFFSET_WORDS)`（`:146`）+ 单行 PASS（`:252`），但其 docstring `:14-20,:46-59` 明载「防扫描器失能两道硬闸：金样例回归 GOLDEN_POS/NEG + 朴素口径下限 NAIVE_FLOOR + exit 2/3 扫描器失能」⇒ 形态相似但有反掩蔽硬闸，判 SUSPECT 非确诊（本会话未对其做哨兵注入，记未验）。

## 二、模板来源（核心）

- 2(a) 逐对相似度（`_cf_lineage.py` 实跑，规范化行 = 去空行/纯注释，`difflib.SequenceMatcher`）：
  - **d29|d30：共同行 84、差异 14/14、Jaccard 0.75、difflib 0.8571；`section_bodies()` 29/29 行完全相同** ⇒ 直接复制，mtime 19:33:47 < 21:57:57 ⇒ d30 抄 d29。
  - **d27|d26：共同 69、差异 22/27、Jaccard 0.5847、difflib 0.738；`sections()` 27/29 共同、ratio 0.9474** ⇒ d27 抄 d26 的提取器（`check_d26.py:21-48` / `check_d27.py:21-50`）。
  - d27|d29 19 共同（0.1118）、d27|d28 22（0.1222）、d28|d29 30（0.1676）、d28|d30 30（0.1676）、d27|d30 19（0.1118）⇒ **四件不是一条逐字复制链，而是两条模板线**：(A) d26→d27（`sections()` + 三元组 OR 词表 + `any()`）；(B) d28→d29→d30（`requirements` 四元组 + `require_all` 旗标 + `any(matches)`/`any(present)` + `section_bodies()`）。d28 自带 30 行 `section_bodies()`，与 d29/d30 的 29 行版只 5 行共同（ratio 0.1695）⇒ d29 抄的是 d28 的**四元组骨架**、换掉了提取器。
- 2(b) mtime 顺序（`find lead -printf %T@ … | sort`）：d25 14:41:54 → d26 14:59:27 → d27 16:41:55 → d28 18:42:26 → d29 19:33:47 → d30 21:57:57（均 2026-11-06）。**同族原件中最早的是 `check_d27.py`（16:41:55）**；更早的「形态相似件」是 `check_fileoffset_axiom.template.py`（2026-10-02 01:00:46，见 1(d)，非确诊同族）；全库最早 `check_*.py` 在 2026-09-26（`out/re_work/re_sprint/`），无 any+PASS 组合。
- 2(c) 原始写法与意图：直读 `check_d25.py:1` / `check_d26.py:1` docstring —— "Read-only mechanical checks / Read-only D-26 gate"；`check_d26.py:21-48` `sections()` 收二级标题正文，`:72-97` 检查 verdict 行、7 个小节标题、`本次不授权`、`勘误`+`挂账`（AND）、`未背书` 非空、引用 ≥8、`selfBias`。**意图是「裁决书格式/机械合规」，不是验事实**（`STALE_PASS_INVENTORY.md:196` 同判）。缺陷进入点：`check_d27.py:81-88` 首次把「正文须含 X」推广成「正文须含 X 或 Y」，用 3 元组 `("外推","卡顿不存在")` + `any(keyword in body …)`；d28 再引入 `require_all` 旗标把 OR/AND 并进同一循环（`:89-99`）。
- 2(d) ★ 扩散到 `check_*.py` 之外会波及什么：
  - `grep -rln "for number, title, words, require_all in requirements" --include="*.py" .` → **38 件**，其中 12 件是 `lead/stale_pass_20261109/_sp_sandbox/**/_w_d27_A/B/S.py` 等**非 check_*.py 注入副本**（`:80-88` 整段 OR 塌缩 + `:105` 单行 PASS 仍在）；`require_all` 全库 42 件 .py，另含 `lead/masking_effect_20261109/_mev_final.py:48-56`（复现 `any(w in body for w in words)` 的诊断器）、`lead/check_masking_20261109/_cm_inject.py`（注入驱动）⇒ **修复若「按模板批量替换」会连带改到证据生产副本**，须先把审计沙箱与生产门禁分开。
  - **最严重的一件恰不叫 `check_*.py`**：`lead/refsync_scope_20261109/_rs_carrier_scan.py`（16,053 B）—— `:165` `min(pos)`、`:229` `any(n in txt for n in a.needle)`、`:343` `ok &= good`、`:346` 单 `SELF_TEST = ...`、`:349` `return 0 if ok else 1`（本会话 `sed -n` 直读）。审计按抽象 k→1bit 把它列为「4/4」同族（`CHECK_MASKING_INJECT.md:441`），但按本回件的代码级判据它**没有 `requirements` 元组 / section 提取器，属异族同抽象**。它的 3 处 PASS 不在台账而在交付件 `REFSYNC_SCOPE_FIX.md:251/252/253`（本会话直读：`627/80/19`、`947/86/23`、`5500/2429/81`），失效会推翻 `:243` R6 承诺与 `:273/:274/:276/:282-286` 六行计数（`STALE_PASS_INVENTORY.md:167`），**不波及任何裁决**。

## 三、同族的代码级判据

- 3(a) 形式判据（`_cf_lineage.py:family_predicate` / `_cf_detect.py` 的 P1–P4，全是 AST/结构，不靠名字）：
  - **F1** 字面元组表存在一行含 k≥2 个字符串词且为 OR 分支（`require_all=False`，或 d27 式无旗标三元组）；
  - **F2** 一个 `any(...)` 把该 k 词 OR 塌缩成**一个**布尔（含 `GeneratorExp` 成员测试、`ListComp` 绑定后的 `any(present)` Name、`any(matches)`）；
  - **F3** 恰好一个**聚合** PASS print（不在 for 循环内）+ `return 0` / `sys.exit` / `SystemExit`，且**无逐词 HIT/DEAD / PER_NEEDLE 输出**；
  - **F4** 有 section 正文提取器（`sections` / `section_bodies` / `section_body`）喂词测试。
  - 四条齐 ⇒ `CONFIRMED`；只有 F2+F3 ⇒ `SUSPECT`。确诊再加经验第 4 步（`CHECK_MASKING_INJECT.md:457`）：把一根词换成零命中哨兵，仍 `EXIT=0` ⇒ 实证。**判据的语义**即 `CHECK_MASKING_INJECT.md:445-450`：待证命题 ∀i 有效、观测量只有 ∃i 命中、不保留 hits 下标 ⇒ `PASS` 与「input_1 全死」观测等价。
- 3(b) 确诊/存疑（AST 检测器 `python -I -X utf8 _cf_detect.py ROOT` 实跑全 173）：**40 CONFIRMED / 3 SUSPECT / 130 NOT_FAMILY**。
  - 四件生产门禁 **全部 CONFIRMED 且 P1–P4 全 True**（`_cf_detect_out.json:four`）；字面筛漏掉的 d28 被 AST 抓到（`any(present)` Name 形态）。
  - 40 件 = 4 原件 + 36 副本（33 件 `_cm_tmp`/`_cmv_tmp` 注入副本、3 件 `_sp_sandbox` d28 副本；按 SHA 去重为 11 个不同字节串，见 `_cf_lineage_out.json`）。
  - **存疑 3 件**：`check_d26.py`（有 `any()` 但无 k 词 OR 元组；`PENDING:162` 记 `exit=0`；`STALE_PASS_INVENTORY.md:133,385` 列 C 级「未注射实证」）、两件 10-02 `check_fileoffset_axiom*.py`（有反掩蔽硬闸）。**本会话未对三者做哨兵注入 ⇒ 未验，不冒充确诊或排除。**
- 3(c) ★ 可自动化，已实跑：`_cf_detect.py`（`ast.parse` → P1 字面向量表 / P2 any 塌缩 / P3 聚合 PASS+出口且排除循环内逐项 / P4 提取器），全 173 件一次跑完，四件全中、d25/d26/逐项打印件不误报。踩坑如实：首版把 f-string 的 `PASS`（`JoinedStr`）漏判致 d27 假阴性，已修（`_cf_detect.py` 现用 `ast.walk` 收 `Constant`）；静态判据只给候选，**确诊仍需动态哨兵注入 + `DISTINGUISHABLE_PASS`**（`lead/stale_pass_20261109/_sp_andk.py:27-42` 的 `AND_k(over 2 real per-word runs)`；本会话只做静态检测，未跑注入）。
- 3(d) 值得另普查的族（方向，非本族）：① `min()/argmin` 反向掩蔽（`_rs_carrier_scan.py:165`，加一根针可把 PASS 翻 FAIL）；② `ok &= good` + 单 `SELF_TEST`（`:343-349`）；③ `0==0` 空真 PASS（`GOAL_THREE_TARGETS_20261018.md:261` verify_hooks「13 槽完全失明」，`STALE_PASS_INVENTORY.md:136` D 级）；④ CWD 相对路径脆弱性（`check_d27.py:8` `Path("lead/d27_ruling_20261106")`）；⑤ PASS 不绑定输入指纹/语料漂移（627→655→662，`STALE_PASS_INVENTORY.md:353`）；⑥ `require_all=True` AND 项的逐词不可归因（`:389` 自认未验，全库 `all_gen` 28 件）；⑦ 台账「裸 exit=0」无状态字段（~170 行，`:221,384`）。

## 四、连带影响

- 4(a) 逐条核：**四条全部写了「门禁 exit=0」** —— `PENDING_DECISIONS.md:92`（d30，另加「2026-11-07 复跑仍 PASS」）、`:105`（d29）、`:117`（d28）、`:129`（d27）；`GOAL_THREE_TARGETS_20261018.md` 中 `D-27|D-28|D-29|D-30` 命中 **0 行**（`grep -c` 实跑输出 `0`）。与题给背景一致。
- 4(b) ★ **同意「四条裁决的实质结论全部不依赖失效 PASS」**，但须限定为「依赖结构」，不是「结论真值」。本会话直读四份裁决书正文：
  - `RULING_D27.md:3`「本阶段未重跑统计、原探针、合成反例或门禁」、`:58`「『Leader亲跑exit=0』…不得签为本阶段执行通过」、`:69`「不背书本阶段未执行的门禁…已通过」、`:77`「未运行 check_stall_def.py 或其他门禁」；定谳 `:6` `main: B`；数值来自 `_d27_facts_out.txt:9`（`:12` 自标「本阶段未重算」）。
  - `RULING_D28.md:9`「未运行核证脚本、门禁、29 项测试、43 项测试或语料重算」、`:72`、`:78`「仅执行 `pwd; rg --files`」；定谳 `:4/:5` `q1: A` / `q2: 丁`。
  - `RULING_D29.md:67`「不是本撰写阶段门禁通过证明」、`:71`「未运行原探针、门禁…不记通过」、`:14` 实跑 `_d29_facts.py` 得 `pureLogicalCounterexampleMs`；定谳 `:4` `q1: 丁`。
  - `RULING_D30.md:62`「未改门禁」、`:76`「不把原探针、check_feasibility.py 或原门禁计为通过；后三者本次未运行」+ 实跑 `_d30_facts.py` 得 `All numeric assertions passed`；定谳 `:4` `q1: 戊`。
  - 精确扫描（`python -I -X utf8 -c` 逐行）确认四件对自身 `check_dNN.py` / PASS / exit=0 **零次正面引用**，命中的全是否认句。
  - **不修的代价不能略**：`PENDING:92/105/117/129` 把「裁决书 + FACTCHECK + 门禁 exit=0」并列成「已验证」交付包，该**证据资格**确失效（`STALE_PASS_INVENTORY.md:213`）；`PENDING:129` 的「71 处引用」是 `check_d27.py:100` 由 gate 产出的数字（`:155`；本会话未独立重算该 regex，记未验）。
- 4(c) **无任何一条裁决的实质结论依赖门禁结果**，故无反例可指。最接近的是上条「71 处引用」（形式数字，非实质结论）与 D-28 作为 D-29/D-30 的**引用上游**（`RULING_D29.md:6`、`PENDING:113` 引 `RULING_D28.md:30/:32/:34/:36`）⇒ 形式链须四件一并补（`:176`「只修三件会漏网」）。
- 4(d) 波及清单：
  - **A 级确诊**：仅 D-27/D-28/D-29/D-30 四条（台账 4 行 `PENDING:92/105/117/129`）。
  - **其它裁决（C 级、未注射实证）**：D-26（`PENDING:162` / `check_d26.py`）、D-25（`PENDING:186` / `check_d25.py`）、N-1（`PENDING:199`「门禁 exit=0」无可复跑脚本）—— `STALE_PASS_INVENTORY.md:133-135,177,385`；本会话静态判 d25/d26 为 NOT_FAMILY/SUSPECT、未跑注入 ⇒ **未验，不冒充有效**。
  - **非裁决**：`REFSYNC_SCOPE_FIX.md:251/252/253` 三行（A+B 级）；`GOAL:261/:262/:327` verify_hooks 假绿（D 级，已自认+已修，异族）。
  - 引用链：D-27（`PENDING:125`）→ D-28 → D-29（`PENDING:113`）→ D-30（`RULING_D30.md:6` 引 D-29），形式缺陷沿链传播，但链上传递的是**正文引用**，不是 gate PASS。

## 五、结论与建议

- 5(a) **同族总数**：按「有台账登记、覆盖裁决的生产门禁」= **4 件**（d27/d28/d29/d30），去重后 **3 套代码模板**（d27 三元组式 / d28 四元组式 / d29=d30 同构式）。按「全库带该缺陷代码的 `check_*.py` 实例」= **40 件**（4 原件 + 36 注入/沙箱副本，AST 全 173 实跑）。另有非 `check_*.py` 的 12 件 `_w_d*.py` 副本与异族同抽象的 `_rs_carrier_scan.py`。依据：`_cf_census_out.json`、`_cf_detect_out.json`、`_cf_lineage_out.json`、`_cf_full_census.md`。
- 5(b) **模板来源**：源头 = 2026-11-06 14:41/14:59 的 `check_d25.py`/`check_d26.py`「只读机械格式门禁」范式（意图只查标题/词/引用数/selfBias）；复制链两条 —— d26 `sections()` → d27（并首次引入 `any()` OR 词表），d28 `requirements` 四元组骨架 → d29 → d30（`section_bodies()` 29/29 全同）。为什么这么写：把「须含 X」泛化成「须含 X 或 Y」时沿用 `any()` +「逐项 append + 末尾一行 PASS」汇总 ⇒ k→1bit。扩散：4 门禁 → 台账 4 行 → D-27→D-28→D-29→D-30 引用链 → 36 副本 → 交付件 3 行。**诚实限定**：`git log --oneline -- lead/d2*_ruling_*/check_*.py` 五件全空、`git status --short` 显示 `d30_ruling_20261106/` 为 `??`（本会话实跑）⇒ mtime 只能证现盘时间顺序，**判不了历史作者归属与是否被改过**（`STALE_PASS_INVENTORY.md:390` 同判）。
- 5(c) ★ **统一外壳为主，不逐件改源码**：理由 ① 四件均在绝对只读域，本任务及后续修复都不得改其一个字节（`PENDING:112,124` 明记「不改门禁脚本」）；② `CHECK_MASKING_INJECT.md:522-534,634` 结论「能通吃四件的只有甲'（逐输入独立跑 + `AND_k` + 坏针注入）外部外壳，被审脚本 0 行改动、完全不破坏既有输出」；③ 逐件内嵌需动 3–4 处源码约 55 行（`:638`）且破坏只读铁律；④ 但**适配器不能一行通吃**（`:535-540`）：scanner 是 CLI `--needle` 可注入、三 gate 是硬编码字面量且无 CLI ⇒ 只能走沙箱副本；d29/d30 的 `require_all=True` 项必须排除在 `AND_k` 外；路径基准三种不同（`check_d27.py:8` CWD 相对、`check_d29.py:50` `__file__.parent`、`check_d28.py:54-55` `parents[2]`）。**不能只靠外壳**：`_sp_andk.py` 是 hardcode 12 个副本的演示外壳、未部署成门禁（`STALE_PASS_INVENTORY.md:251-268`），`_cm_AUDIT.md` 旧模板套 d29 实测 `BAD_NEEDLE_CAUGHT=False`（`CHECK_MASKING_INJECT.md:544-565`），必须用修正版（`:570-626`，该件作者实跑 `TEMPLATE_EXIT=0`）。判断 = **统一甲' 外壳 + 逐件适配器 + 逐件指纹绑定 + 台账 7 处就地加注**（`PENDING:92/105/117/129` + `REFSYNC_SCOPE_FIX.md:251/252/253`）。
- 5(d) **判不了什么 / 未验**：① 四条裁决实质结论的**真值**（未重跑 `_d27/_d28/_d29/_d30_facts.py` 数值断言）；② **坏针注入实证本会话未跑**（只读普查 + 静态 AST），四件「坏针仍 PASS」结论引自 `CHECK_MASKING_INJECT.md:183-365` / `STALE_PASS_INVENTORY.md:126-131` 既有实跑，未独立复现；③ d25/d26/N-1 与 10-02 两件 SUSPECT 是否真掩蔽（未注射）；④ git 历史全空 ⇒ 判不了「谁先写」的作者身份与历史改动；⑤ `require_all=True` AND 项逐词可归因（`:389`）；⑥ 修复部署与修复后回归（`:388` / `CHECK_MASKING_INJECT.md:628`）；⑦ 编排方 `pass` 列自相矛盾的真实口径（只能指出矛盾，无法得知其脚本定义）；⑧ `PENDING:129`「71 处引用」本会话未独立重算；⑨ `.git/` 内部与符号链接目标未纳入 173 清单；⑩ `_rs_carrier_scan.py` 是否算「同族」取决于判据严格度（审计按抽象算 4/4，本回件按代码模板算异族同抽象）——两种读法都如实列出。

## 本会话实跑命令（节选，全部可复核）

```
find . -type f -name "check_*.py" 2>/dev/null | sort          # 173 件
find lead -type f -name "check_*.py" -printf "%TY-%Tm-%Td %TH:%TM:%TS|%p\n" | sort
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_family_20261109/_cf_census.py D:/Project/ra2-campaign-forge
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_family_20261109/_cf_lineage.py D:/Project/ra2-campaign-forge
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_family_20261109/_cf_detect.py D:/Project/ra2-campaign-forge
grep -rln "for number, title, words, require_all in requirements" --include="*.py" .   # 38 件
grep -n "门禁.*exit=0\|exit=0.*门禁" lead/PENDING_DECISIONS.md                        # 7 行
git log --oneline -- "lead/d2[6-9]_ruling_20261106/check_*.py"                       # 无输出
sha256sum lead/d27_ruling_20261106/check_d27.py lead/stale_pass_20261109/_sp_sandbox/check_d27_baseline.py
```

产出（唯一写域，前缀 `_cf_`）：`_cf_filelist.txt`、`_cf_census.py` / `_cf_census_out.json` / `_cf_full_census.md`、`_cf_lineage.py` / `_cf_lineage_out.json`、`_cf_detect.py` / `_cf_detect_out.json`、本件。**未改任何脚本**（写域内新建的分析脚本除外）、未改台账、未 commit / push。
