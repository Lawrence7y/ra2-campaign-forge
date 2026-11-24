# MATRIX_BINDING_FACTS_20261108 · 矩阵绑定事实件（甲↔乙 核证收录 + 复核回件绑定）

- 日期：2026-11-08　撰写：核证报告撰写员（动态工作流子代理，新上下文）
- 输入：①矩阵核证回件（diffComplete=true / chainClosed=true / severity=medium）；②矩阵复核回件（**verdict = partial → 按派发规则标 unconfirmed**，见 §5.3）；③本会话对全部原始出处件的实读与实算（命令与输出清单见 §6.3）。
- 合规：零真机、零采样代码；既有件一律只读（收尾 `git diff --stat` 对 re_line_20261105 / b2b_design_20261106 / b2b_preaudit_20261106 / b2_preaudit_20261106 / b2b_candidate_review3_20261107 / bexec_n4_20261108 / nextstep_plan_20261106 / b2b_candidate_lf_20261107 全为空，实跑）；唯一写域 = `lead/matrix_binding_20261108/`；未 commit、未 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`。

## 1 目的与边界

★ **本件只核证事实，不代签发人决断甲/乙，不签 APPROVE_SCOPE，不放行 N-5。**

- 决断权归属的在档依据（本会话实读）：`lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md:47`「……若与设计冲突退 N-2，不由测试者临时决定」；`:49`「独立审阅者签候选 YES、来源会话签发人签 APPROVE_SCOPE……身份、任一规则或版本缺失则任务书不生效」；`lead/bexec_n4_20261108/B_EXECUTION_SPEC.md:6`（现行状态 = SPEC_DRAFT 未生效）、`:239`「矩阵甲/乙**绑定未决**——签发人决断点（§3.6），本草案不代决」。
- 效力上界：本件一切结论只到「文件:行 + 实跑命令与输出已核证」为止；**不包含**「可应用到母本」「运行时已验证」「集成已演练」（同 `_m_CHAIN_VERIFY_20261108.md:46` 对链闭合的限缩）。
- 复核回件 verdict = **partial**：按派发规则，凡仅由该回件支撑、本件未独立重验的细分主张，状态标 **unconfirmed**；核证实质主张经复核员与本件各自独立复算后**未被推翻**（见 §5.3）。

## 2 甲的定义与出处

**甲** = 「B2 · 新鲜性补丁修复版」设计件：`lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md`。
**被核对象 SHA256 = deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f，字节数 = 11638**（本会话 hashlib 实算命中派发指纹，`_facts_fp_out.txt` §A）。

出处（本会话逐行实读）：

| 主题 | 行 | 内容 |
|:--|:--|:--|
| 改动面 **A—D** | :113-116 | 四处改动表：A `backup_carrier` 补 `exists`/`mtime_pre`/`captured_at_epoch`；B `copy_post_except_evidence` 签名+判定+info；C `finalize_trip` 签名；D 接线+快照构造；`:118`「四处改动是可论证的最小集」 |
| 判定块 | :133-154 | `:133` `_pre = dict(pre_snapshot or {})` ⇒ 空快照 `{}` 折叠为 exists=False；`:136-138` `absent_both`→置信 `n/a`、`vanished`→`high`；`:150` elif `_pre_mtime is not None` 守卫 ⇒ mtime_pre 缺失时跳过比较、`:154` 落 `leftover_unchanged`/`high` |
| 规模 | :192 | 「预计净增 ≈ 31 行，删除 0 行，无既有逻辑改动」 |
| **预审**硬门 | :196 / :198 | `:196` §3 标题「修复版必须重新过预审（不能直接用）」；`:198`「★ **本文件只是设计。** 应用前必须重新走一遍 B1 的预审硬门」 |

甲的批准状态（详见 §5.2）：甲的预审 = `lead/b2_preaudit_20261106/B2_PREAUDIT.md`（`:3` 判定对象 = 甲、实算指纹 deacab49…/11638 与上同）：`:15` 门语义「只回答能不能拿去制作完整候选」、`:17` `verdict: NO`、`:20-22` 判 NO 依据 = E1=NOT_FIXED + 5 条 severity=high。甲所在目录本会话 `ls` 实跑仅 5 件（B2_FIX_DESIGN.md / PRE_AUDIT.md / TASK.md / _b1_preaudit.py / _b1_preaudit_out.txt），**无任何候选件**；`B2B_PREAUDIT.md:9` 把甲登记为「历史被否参照件」。

## 3 乙的定义与出处

**乙** = 「B2b」批准设计：`lead/b2b_design_20261106/B2B_DESIGN.md`（**SHA256 = 565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf，字节数 = 66735**）+ 同目录机器可读状态矩阵 `STATE_MATRIX.json`（**SHA256 = 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016，字节数 = 3558**，14 数据行 :2-15）。两件指纹本会话实算命中（`_facts_fp_out.txt` §A）。

出处（本会话实读/实跑）：
- §2 状态矩阵 :140-168：`verdict` ∈ 9 值、`confidence` ∈ high/medium/low/none（`:142`「`none` = **不可判**，不是 `low`」）；preState 4 态唯一判别口、`exists` 不得反推（`:142`、`:580`）；置信硬规三条 :165-168（`low` 给 `absent_both`、`none` 给**所有不可判出口**含 `vanished`）。
- §4 完整 diff :198-566：**九个 ```diff 块**（本会话 `grep -c '^```diff'` 实跑 = 9，位于 :204/:229/:243/:379/:497/:510/:523/:536/:555）。
- §5 字段契约 :570-619：F 输出 7 键 + info 扩键 + H08 单独落 `captured_at_iso_pre`（`:604`）。
- §7 改动清单 ↔ hunk 对照表 :656-670：**H01—H09 九 hunk**（`:658`「9 行数据 = §4 里 9 个 `@@ ` hunk……无第 10 个 hunk」），锚点 = :214/:4460/:4561/:4574-4599/:5909/:5939/:6296/:6388/:7125 后；`:635` 九 hunk 的 `-` 侧覆盖区间均不含 E 判据块 5984-5990。
- 正式候选：`lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py`（SHA256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2，字节数 = 412759）= 母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py`（SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508）+ 乙九 hunk，两路逐字节重建证实（§5.1③）；两件指纹本会话实算命中（`_facts_fp_out.txt` §B）。旧候选 `lead/b2b_candidate_20261106/qc151_trip.candidate.py`（9656e432f5b5…/420292，本会话实算）按 `B_EXECUTION_SPEC.md:74` 已被替换、禁绑。

## 4 逐项差异表（甲值 | 乙值 | 出处）

### 4.1 四处分支取值差（承接 `B_EXECUTION_SPEC.md:119-128` §3.4 已登记项；本会话对原始出处逐项实读核同）

| # | 分支 | 甲值 | 乙值 | 甲出处 | 乙出处 |
|:--|:--|:--|:--|:--|:--|
| 1 | `absent_both` 的 confidence | `n/a` | `low`（is_new=False，「文件未出现」不能证无崩溃） | B2_FIX_DESIGN.md:137-138 | STATE_MATRIX.json:7；B2B_DESIGN.md:153、:167 |
| 2 | `vanished` 的 confidence | `high` | `none`（不给 high、is_new=null、须人工复核） | B2_FIX_DESIGN.md:137-138 | STATE_MATRIX.json:15；B2B_DESIGN.md:161、:168 |
| 3 | 空快照 `{}` | 折叠为 exists=False ⇒ 跑后有件→`new_first_appearance`/high；跑后无件→`absent_both`/n-a | `unknown`/`none`、is_new=None、未知 ≠ 不存在，不作本趟新出现归因 | B2_FIX_DESIGN.md:133-134 | STATE_MATRIX.json:2；B2B_DESIGN.md:148 |
| 4 | `mtime_pre` 缺失 | 无独立分支：`:150` elif 守卫直接跳过 mtime 比较 ⇒ `leftover_unchanged`/`high` | `leftover_unchanged`/`medium`（A 旁证不可用、盲区如实标注、不虚报 high） | B2_FIX_DESIGN.md:150-154 | STATE_MATRIX.json:9；B2B_DESIGN.md:155 |

### 4.2 值域差

| 维度 | 甲值 | 乙值 | 出处 |
|:--|:--|:--|:--|
| confidence | `{high, low, medium, n/a}` | `{high, medium, low, none}`，`none`=不可判、显式区别于 `low` | 甲：:137-154 实码字面量（本会话实读）；乙：B2B_DESIGN.md:142、`:579` + STATE_MATRIX.json 14 行实测（本会话复跑输出与 `_m_rebuild_out.txt:21` 同值） |
| verdict | 6 值：absent_both / vanished / new_first_appearance / new_write / rewritten_same_content / leftover_unchanged | 9 值 = 甲 6 值 + `unknown` + `error_pre_snapshot` + `post_read_error` | 甲：:136-154（本会话实读）；乙：B2B_DESIGN.md:578 + 实测（`_m_rebuild_out.txt:22`，本会话复跑同） |
| 跑前快照判别 | `exists` 布尔唯一判别（`:134`） | `preState` 4 态唯一判别口、`exists` 不得反推 | 乙：B2B_DESIGN.md:142、`:580` |

### 4.3 字段差（乙输出为超集）

甲 F 输出两值——`evidence_freshness` 记录（value=verdict、note 内含置信，B2_FIX_DESIGN.md:160-161）+ info 加 4 键（`:186`）。乙 F 输出 7 键全路径落盘：`freshness_verdict / freshness_confidence / freshness_is_new / freshness_note` + `pre_snapshot_state / usable_as_crash_evidence / captured_at_iso`（B2B_DESIGN.md:574-619），另 H08 单独落 `captured_at_iso_pre`（`:604`）。相对甲新增：**is_new、note、usable_as_crash_evidence、pre_snapshot_state、captured_at_iso、captured_at_iso_pre**。

### 4.4 改动面差

| 项 | 甲 | 乙 |
|:--|:--|:--|
| 清单 | **A—D 四处**（:113-116）+ :181-190 明细 8 行 + :192「净增 ≈31 行，删除 0 行」 | **H01—H09 九 hunk**（:656-670）；+255/-13 行（R3:85 实测；母本 7292→候选 7534 行，`_m_rebuild_out.txt:13`，本会话复跑同值） |
| 结构 | 判定内联在 `copy_post_except_evidence` 内；无预初始化（早退路径作用域风险，甲预审 E1=NOT_FIXED）；无常量命名空间 | 判定抽纯函数 `classify_except_freshness` + 采集函数 `make_pre_freshness_snapshot`；H07 预初始化先于 try；H01 注入 5 常量单一真源 |
| 对应关系（事实映射，非等价声明） | 甲A ≈ 乙H02（语义不同：甲改 bak 三键、乙不动 bak 只加留痕）；甲B ≈ 乙H03+H04；甲C ≈ 乙H05；甲D ≈ 乙H06+H08；乙H01/H07/H09 在甲中无对应物 | 同左 |

## 5 批准链核证 + 复核回件

### 5.1 乙批准链四节（本会话逐条实读/实跑核证成立）

- **① 预审 YES**：`B2B_PREAUDIT.md:13` `verdict: YES`；`:16`「`verdict: YES` 的准确含义 = 可以拿去编写候选；不等于可以应用到母本」；`:17`「**绝对禁止将本设计直接应用到母本**」（本会话实读）。
- **② R3 PASS**：`CANDIDATE_SEMANTIC_REVIEW_R3.md:21` `verdict: PASS`；`:23`「**PASS ≠ 可应用到母本**（D-25 第 6 步隔离副本集成未做，N1_BINDING.md:110）」；`:122`「本判定书不构成『候选可应用到母本』」；`:137`「PASS 的准确含义 = 候选**语义上**实现了批准设计……不等于：可应用到母本、运行时已验证（零真机）、集成已演练」；`:138`「本件仍需另起新上下文的独立复核……该复核**尚未发生**」——R3 自身无独立复核为链上现存缺口，交签发人知悉（以上本会话实读）。
- **③ 逐字节重建**：R3:32-34 两条决定性路径（设计 §4 九个 ```diff 块、`CANDIDATE_LF.diff` 九个 `@@`）。本会话实跑 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/matrix_binding_20261108/_m_rebuild.py`：exit=0，路径①/② 恰 9 块/9 hunk，两路重建 SHA256=ca23c116…/412759 ==候选 True，`FINAL: ALL_REBUILD_PASS`，且输出与在档 `_m_rebuild_out.txt` **逐字节相同**（`cmp -s` 实跑，落档 `_facts_rerun_out.txt`）。至此四方一致：核证员原始实跑（`_m_rebuild_out.txt`）、复核员独立实现重建（`_verify_hy4_out.txt` FINAL `REBUILD_BOTH_PASS=True`）、复核员复跑（`_verify_rerun_m_rebuild.txt`，本会话 `cmp` 实证与原件逐字节相等）、本件撰写员复跑。
- **④ 指纹闭合**：候选 ca23c116…/412759、母本 517889c8…/399508、CANDIDATE_LF.diff 72b10802…/18454 三件本会话 hashlib 实算全命中（`_facts_fp_out.txt` §B）。
- **链闭合含义**（承 `_m_CHAIN_VERIFY_20261108.md:46`）：= 「候选逐字节等于批准设计且语义经三轮复审」；**不包含**可应用到母本（D-25 第 6 步隔离副本集成未做）、运行时已验证、R3 独立复核已发生；**不据此放行任何应用或 N-5**。

### 5.2 甲的批准状态

`:198` 明写「只是设计、应用前必须重走预审硬门」成立（§2 实读）；该前置的实际结果 = 甲的预审 `verdict: NO`（B2_PREAUDIT.md:17）→ 甲无候选、无 PASS 记录。同时 N-4 原文（NEXT_STEPS_20261106.md:47-48）的动作与依据行全部锚定**甲**的矩阵与 A—D——即 N-4 原文判据与现行 R3 PASS 候选实现的**不是同一套**（本会话实读两边原文核同）。

### 5.3 复核回件收录（verdict = partial → **unconfirmed**）

- **被核对象绑定**（复核回件 sha256Line 原文；聚合指纹本会话重算命中，`_facts_fp_out.txt` §C）：
  **被核对象 SHA256 = 524a98ca80b2bb8112a0e0c6b9a8608103964cebaf2168da59f49d7e0594cd4d，字节数 = 33357**（lead/matrix_binding_20261108/ 五件主产出按文件名升序拼接的聚合指纹）。五件单件指纹（本会话实算与复核回件 §六 逐项一致）：`_m_MATRIX_DIFF_20261108.md`=aa6aa58f…/10077、`_m_CHAIN_VERIFY_20261108.md`=636551f7…/7813、`_m_DECISION_POINTS_20261108.md`=a8a7d2eb…/4939、`_m_rebuild.py`=77c091d9…/8329、`_m_rebuild_out.txt`=e768a2d3…/2199。
- **复核结论**：核证实质主张（四分支差异/值域/改动面/甲乙归属、YES/PASS 未升格为「可应用」、未代决未签未放行、甲批准状态未漏、写域外无改动）经复核员独立复算**全部成立**；**唯一缺陷类 = 引用精度**：核证回件 evidence 与 `_m_CHAIN_VERIFY` / `_m_MATRIX_DIFF` 对自有输出 `_m_rebuild_out.txt` 的行号自引大面积错位/越界。verdict = **partial ⇒ 本节整体标 unconfirmed**（实质未被推翻、缺陷真实存在）。
- **本会话对该缺陷的独立确认**（`_facts_fp_out.txt` §D 实测）：`_m_rebuild_out.txt` 实为 23 物理行全非空、CRLF、2199 B；实际行位 = 派发 7 件指纹 :2-8、母本/候选 :9-10、CANDIDATE_LF.diff :11、CR 检查 :12、行数 :13、路径① :14-15、路径② :16-17、链④ :18-19、矩阵行数 :20、confidence 值域 :21、verdict 值域 :22、`FINAL: ALL_REBUILD_PASS` :23。对照错位实例（复核回件所列，本会话逐条实读核同）：`_m_CHAIN_VERIFY:30-33`（引 :19-24，FINAL :35——:35 越界，FINAL 实在 :23）、`:38`（引 :11-12,27-28——:27-28 越界，实在 :9-10 / :18-19）、`:41`（引 :16 指 CR——实在 :12）；`_m_MATRIX_DIFF:6`（引 :3-13 指派发件——实在 :2-8）、`:37`（引 :31——实在 :21）、`:38`（引 :32——实在 :22）、`:57`（引 :19,23——实在 :14/:16）、`:59`（引 :17——实在 :13）；核证回件 evidence 自引（FINAL「:19-24,35」、派发「:3-13」）同病。
- **后果定性**（承复核回件）：下游按这些行号回溯会在多处找不到所述内容或越界，证据链在这些指针处断裂，违反「引用必须追到实跑命令+输出或文件:行」的精度要求；但属引用精度缺陷，**不推翻任何实质结论**（全部数字/结论已由复核员与本件各自独立证明）。修正方向 = 按上行实际行位改引，或改引「实跑命令+输出全文」。
- **附注**：复核员自产 `_verify_hy4_out.txt` §G「甲 verdict(5)」系其抽取正则（`_verify_hy4.py:161`）只捕 `("` 之后字面量所致；甲 `:137` 实含 `"absent_both"`（本会话实读 + `_facts_fp_out.txt` §F 脚本确认），甲 verdict 6 值成立，不影响 §4.2。

## 6 签发人决断点清单与未验项

### 6.1 决断点（四项全部留白待签发人；本件不预设答案、**不代决**；出处 `_m_DECISION_POINTS_20261108.md`）

| # | 要拍板的事 | 两侧事实（出处） |
|:--|:--|:--|
| 1 | 绑甲还是绑乙 | 绑乙侧：候选逐字节 = 母本+乙九 hunk（§5.1③ 本会话复跑）、R3 PASS 对照设计即乙（R3:5）、乙预审 YES（B2B_PREAUDIT.md:13）。绑甲侧：甲预审 verdict: NO（B2_PREAUDIT.md:17）、甲无候选（§2）。两套矩阵不能同时绑定为通过判据（B_EXECUTION_SPEC.md:141）；在档「建议绑乙」自标「**仅建议，非裁决**」（B_EXECUTION_SPEC.md:141），引用它不构成决断 |
| 2 | 若绑甲：是否必退 N-2 | N-4:47 明文「若与设计冲突退 N-2，不由测试者临时决定」；绑甲则现行候选在 absent_both（low vs n/a）、vanished（none vs high）、空快照（unknown vs 折叠）等场景与甲判据不符（B_EXECUTION_SPEC.md:69；差异本身见 §4.1） |
| 3 | 若绑乙：是否补登「以乙替代甲」正式记录 | N-4 原文依据行全锚定甲（NEXT_STEPS_20261106.md:47-48），乙不在其引用之列；本工作流核证范围内未检索到任何在档文件宣布「乙替代甲成为 N-4 判据」；是否补、由谁补、登记到哪份档，属签发人权限 |
| 4 | APPROVE_SCOPE 的签署前提 | 在档条款（N-4:49 原文）：正式目标/候选 SHA256/允许范围/替代条款/测试命令与 API 基线固定 + 独立审阅者签候选 YES + 来源会话签发人签 APPROVE_SCOPE + N-1 格式绑定哈希，缺一不生效。现状：B_EXECUTION_SPEC.md:6 = SPEC_DRAFT 未生效、`:239` 绑定未决不代决；R3:138 自述其独立复核尚未发生；R3:23/:122/:137 D-25 第 6 步离线集成未做；N-5 动作原文见 NEXT_STEPS_20261106.md:55 |

### 6.2 未验项（如实登记，不补造）

- `lead/d25_ruling_20261106/RULING_D25.md` 原文：核证员、复核员均未实读，B_EXECUTION_SPEC.md:241 亦自报未直接实读（仅经 R3:23 等转引）——本件同样未读。
- `lead/b2b_n1_binding_20261107/N1_BINDING.md`：本件与核证员未实读（仅经 R3:7/:29 转引）。
- `lead/b2b_candidate_review3_20261107/_review_probe_r3_out.txt`：未逐字节复读；链③以本工作流自跑重建为准。
- 候选 `ast.parse` / 测试套件 / 门禁重跑：本件与核证员未跑（B2B_DESIGN.md:645-646 与 R3:144-145 各有该会话历史实跑记录，属历史转引）。
- commit / push：未执行，也未做 git log 比对。
- 复核员一次全树 `find -newermt` 120s 超时被终止、未采信（改用 `git diff --stat` 定向检查只读域）；本件沿用同法。
- 真机/运行时整趟：零真机铁律下从未发生（R3:114 未验节）；运行时退出码语义未复现（B2B_DESIGN.md:652 自我声明）。
- D-25 第 6 步隔离副本离线集成：未做（R3:122）；候选对母本的正式应用（N-5）未发生。

### 6.3 本件撰写员的实跑/实读清单（Python 一律 `python -I -X utf8` + 绝对路径；新增件全部落写域）

1. `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/matrix_binding_20261108/_facts_fp.py > …\_facts_fp_out.txt`——7 件派发指纹 + 甲预审/母本/候选/diff/旧候选指纹 + 5 件主产出单件与聚合指纹 + `_m_rebuild_out.txt` 行结构实测 + 复核重跑件逐字节比对 + 甲:137 字面量在位检查。
2. `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/matrix_binding_20261108/_m_rebuild.py > …\_facts_rerun_out.txt`——exit=0；与 `_m_rebuild_out.txt` `cmp -s` 逐字节相同；`FINAL: ALL_REBUILD_PASS`。
3. `grep -c '^```diff' lead/b2b_design_20261106/B2B_DESIGN.md` → 9；`grep -c '^@@' lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff` → 9。
4. `git status --porcelain lead/matrix_binding_20261108/`（写域整体 untracked）+ `git diff --stat` 八个只读域全空。
5. 实读件：B2_FIX_DESIGN.md 全文；STATE_MATRIX.json 全文；B2B_DESIGN.md §2(:140-172)/§5(:570-673)/§7 表；B2B_PREAUDIT.md:1-40；R3:1-145；B2_PREAUDIT.md:1-40；B_EXECUTION_SPEC.md:1-145/:232-245；NEXT_STEPS_20261106.md:40-64；写域内 `_m_MATRIX_DIFF` / `_m_CHAIN_VERIFY` / `_m_DECISION_POINTS` / `_m_rebuild.py` / `_m_rebuild_out.txt` / `_verify_hy4.py` / `_verify_hy4_out.txt` 全文。

—— 本件只登记事实与决断点；甲/乙绑定、N-2 回退、APPROVE_SCOPE 签署、N-5 放行全部留待签发人。
