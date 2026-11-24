# MATRIX_ROW5_COUPLING — STATE_MATRIX.json:5 行「码序下欠宽」连带评估交付件

- 撰写：连带评估撰写员（动态工作流子代理），2026-11-09。性质：**只评估、不改件**——本件是对 `lead/matrix_row5_20261109/_r5_row5_linkage_assessment.md`（上轮评估回件）及其复核回件（**verdict = confirmed**）的交付汇编，指纹与 grep 全部由撰写人本轮实跑复现，实码与绑定文本本轮逐一实读。
- 评估对象：`lead/b2b_design_20261106/STATE_MATRIX.json` 第 5 行（文件行 :5，14 数据行之第 4 行），原文（本轮 Read 实读全文 16 行，:1–:16）：
  `{"state":"post_read_error","preState":"present","condition":"跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口","verdict":"post_read_error","confidence":"none","usableAsCrashEvidence":false}`
- 结论一句话：**:5 行确属「码序下欠宽」**——候选 `classify_except_freshness` 的 read_error 出口（候选 :4643-4646）先于一切 pre 分支，出口真实输入域 = 四态 preState 全体 + pre=None/{} 等，而 :5 只登记 `preState="present"`；:5 自身覆盖的 (present × read_error) 格取值正确，欠宽的是「行」对「出口域」的覆盖。

---

## 1 目的与边界

1. **目的**：只回答一件事——矩阵 :5 行是否真属「码序下欠宽」，以及它与 :2 行收紧建议（pf2 §4.5 文案，`lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md:188-196`，原文标题即「收紧表述建议（处方，**未实施**）」）的联动关系：收紧 :2 后哪类重叠输入无行可配（孤儿）、矩阵现有 14 行里还有哪些误盖/裸格、修复面怎么选。
2. **边界（本件做了什么/没做什么）**：
   - 只评估。上列被核九件（§2）+ 被核回件本体**零改动**（§5.3 声明）；唯一写域 = `lead/matrix_row5_20261109/`。
   - 零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析；探针为纯函数级标准 import + AST 静态分析）。
   - 不 commit、不 push；不执行 T1/T2/T5 门禁（未验项见 §5.5）。
   - 探针运行期只在写域内建临时目录并即席清理（`_r5v_probe.py:121-141`），对候选/母本只读。
3. **输入材料**：上轮评估回件（任务下发【评估】栏 + `lead/matrix_row5_20261109/_r5_row5_linkage_assessment.md`）与复核回件（任务下发【复核】栏，verdict=confirmed）。本件凡引「上轮/复核员」处均为任务下发材料，其余结论均带本轮实跑命令或 `文件:行`。

## 2 上游指纹（九件）

本轮实跑命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\matrix_row5_20261109\_r5c_fingerprint.py`（hashlib 逐件实算，输出 `_r5c_fingerprint_out.txt`，**FINGERPRINT_MATCH 10/10**——第 10 件为被核回件本体，其绑定行列于 §5.2；九件基线与编排方下发指纹逐字节一致）。

| # | 文件 | SHA256 | 字节数 | 角色 |
|--:|:--|:--|--:|:--|
| 1 | `lead/b2b_design_20261106/STATE_MATRIX.json` | `1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016` | 3,558 | 乙矩阵（评估对象所在，14 数据行 :2-15） |
| 2 | `lead/b2b_design_20261106/B2B_DESIGN.md` | `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf` | 66,735 | 乙设计（§2 状态矩阵镜像 :146-161，:144「下表与之逐行一致」） |
| 3 | `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` | `ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2` | 412,759 | 候选 LF（实码：classify :4616-4698、make_pre :4580-4613、copy :4701 起） |
| 4 | `lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md` | `c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801` | 28,897 | V2（绑定表 :45-46、§4.2 五列表 :114-130、门禁 T1-T5 :180-184） |
| 5 | `lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md` | `1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b` | 23,129 | 重签件（§2 十二件指纹表、:152-157 附条件全文） |
| 6 | `lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md` | `b1231ccb8b80c5200e2ff33b15e09ae52b0452a1481dfc7989730f7da16eda5b` | 22,048 | 修正提案（pf2：:175 标签误配论证、§4.5 处方 :188-196、§4.6 批准人 :198-200、§4.7 连带 :202-207） |
| 7 | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399,508 | 母本（只读对照） |
| 8 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52,419 | 台账一 |
| 9 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759,518 | 台账二 |

## 3 码序实证

### 3.1 `classify_except_freshness` 顶层分支码序逐行表（候选 :4616-4698）

证据：本轮 Read 候选 :4575-4799 逐行实读；上轮 `_r5_static_order.py` AST 实跑（`_r5_static_order_out.txt`，函数体顶层语句序列 14 行）；复核员独立 AST 实现 `_r5v_probe_out.txt` P2 **同序 0 处偏差**（:4637 归一、:4643 read_error、:4648 unknown、:4652 error、:4657 not post_exists、:4666 absent_confirmed、:4673 缺 pre_sha、:4678 缺 post_sha、:4681/:4686/:4690/:4693 mtime 四支）。13 处 `_finish` 调用行 = :4644/:4649/:4653/:4659/:4662/:4667/:4674/:4679/:4682/:4687/:4691/:4694/:4697（R3:43、V2:132 同名单）。

| 码序 | 候选行 | 分支/语句（本轮实读原文摘录） | 出口 `_finish(verdict, conf, is_new)` | 对应矩阵行 |
|--:|--:|:--|:--|:--|
| 0 | :4634-4639 | pre 归一：非 dict→{}；`st`∉`FRESHNESS_SNAPSHOT_STATES`（:228 四态元组）→ unknown；只赋 `out["pre_snapshot_state"]`，**无 return** | — | — |
| 1 | :4641 | post 归一：非 dict→{}，**无 return** | — | — |
| **2** | **:4643-4646** | `if post.get("read_error"):`（:4642 注释「★ N1：错误独立出口，优先于一切状态折叠」） | **post_read_error / none / None** | :5（仅登记 present） |
| 3 | :4648-4651 | `if st == "unknown":` | unknown / none / None | :2、:3（R3:43：行1-2→:4649，unknown 态合并覆盖读法） |
| 4 | :4652-4654 | `if st == "error":` | error_pre_snapshot / none / None | :4 |
| 5 | :4656-4664 | `if not post_exists:`（内分：absent_confirmed→:4659；其余→:4662） | absent_both / low / **False**（:4659）；vanished / none / None（:4662） | :7；:15 |
| 6 | :4666-4669 | `if st == "absent_confirmed":`（跑后在） | new_first_appearance / high / **True**（:4667） | :6 |
| 7 | :4672-4676 | `if not pre_sha:` | error_pre_snapshot / none / None（:4674） | :13 |
| 8 | :4677-4680 | `if not post_sha:`（post_read_error **第二出口**） | post_read_error / none / None（:4679） | :14 |
| 9 | :4681-4683 | `if post_sha != pre_sha:` | new_write / high / True（:4682） | :10 |
| 10 | :4685-4689 | `if pre_mt is None or post_mt is None:` | leftover_unchanged / medium / False（:4687） | :9 |
| 11 | :4690-4692 | `if abs(post_mt - pre_mt) <= 0.0:` | leftover_unchanged / high / False（:4691） | :8 |
| 12 | :4693-4696 | `if post_mt < pre_mt:` | rewritten_same_content / low / True（:4694） | :12 |
| 13 | :4697-4698 | 其余（mtime 变大） | rewritten_same_content / medium / True（:4697） | :11 |

**定论：read_error 出口在码序 2，先于一切 pre 分支（码序 3-6）与 present 支内全部子分支（码序 7-13）。** 设计依据同码：B2B_DESIGN.md:310-311 补丁原文「`# ★ N1：错误独立出口，优先于一切状态折叠`」+ 候选 :4642 同注释。

**read_error 的写入点（重叠输入为何可达，本轮实读 copy_post_except_evidence :4701-4790）**：`post_observed` 初始化含 `"read_error": None`（:4720-4722）；正常路径置 `exists=True`（:4769）后 `dst.write_bytes(blob)`（:4772）可失败；异常路径统一置 `post_observed["read_error"]`（:4786）再落盘 F 字段（:4788-4789）并上抛。故 read_error 与 `exists=None`（read/stat 失败型）及 `exists=True`（write_bytes 失败型）**两种 post 形态都可从实际流产出**，且与 pre 任意态正交组合。

**显式 "unknown" 运行期不产出**：`make_pre_freshness_snapshot`（:4580-4613）初值 `state="unknown"`（:4589）但三路必覆写——无件→absent_confirmed（:4599）、在场→present（:4603，且必算 sha256 :4607）、异常→error（:4610）；复核员运行期探针 P4「explicit unknown-state produced at runtime: **False**」（`_r5v_probe_out.txt:113`）。

### 3.2 矩阵 14 行匹配键表（STATE_MATRIX.json :2-15，本轮 Read 全文实读）

匹配键 = `preState` 字段 + condition 前件。判定列依据 = §3.1 码序 + §4.1 两轮 72 格实跑。

| 文件行 | state | preState | condition 前件（匹配键摘要） | verdict / conf / is_new | 命中码序 | 登记判定 |
|--:|:--|:--|:--|:--|:--|:--|
| :2 | unknown | unknown | pre=None/{}/缺state/脏值 + **跑后任意文件状态** | unknown/none/None | 3 | **W1**：后件过宽，read_error 格被错盖（R2:53/R3:47/V2:132/重签件:89 已登记） |
| :3 | unknown | unknown | pre.state **显式** unknown + 跑后**无件** | unknown/none/None | 3 | ✓（但不含显式unknown×跑后在 → O2，见 §4） |
| :4 | error | error | snap.error 非空（**无跑后限定**） | error_pre_snapshot/none/None | 4 | **W2**：read_error 格被错盖（本轮新发现，前轮各登记均未载） |
| :5 | post_read_error | present | post.read_error 非空 | post_read_error/none/None | 2 | **欠宽**：出口域=四态全体，行键 present 独占；自身格取值 ✓ |
| :6 | absent_confirmed | absent_confirmed | 跑前确认无件 + 跑后**在场（存在性硬证）** | new_first_appearance/high/True | 6 | ✓（但 write_bytes 失败子格被字面误claim → O1′） |
| :7 | absent_both | absent_confirmed | 跑前确认无件 + 跑后无件 | absent_both/low/False | 5 | ✓ |
| :8 | leftover_unchanged | present | 跑前在+跑后在+sha同+mt未变（双侧齐） | leftover_unchanged/high/False | 11 | ✓ |
| :9 | leftover_unchanged | present | 同上 + mt 侧缺失 | leftover_unchanged/medium/False | 10 | ✓ |
| :10 | new_write | present | 跑前在+跑后在+sha 不同 | new_write/high/True | 9 | ✓ |
| :11 | rewritten_same_content | present | sha同 + mtime 变大 | rewritten_same_content/medium/True | 13 | ✓ |
| :12 | rewritten_same_content | present | sha同 + mtime 回拨 | rewritten_same_content/low/True | 12 | ✓ |
| :13 | missing_sha | present | 跑前在+跑后在+**缺 pre.sha256** | error_pre_snapshot/none/None | 7 | ✓（read_error 时被 :5 先截 → W3 重叠，仅 fixture 域） |
| :14 | missing_sha | present | 跑前在+跑后在+**缺 post.sha256** | post_read_error/none/None | 8 | ✓（与 :5 在 read_error 时重叠，四元组同值，无害；present 独占成立） |
| :15 | vanished | present | 跑前在 + 跑后无件 | vanished/none/None | 5 | ✓ |

（V2 §4.2 :114-130 为同 14 行的五列收录表——文件行/preState/verdict/confidence/usable，**无 condition 列**；重签件 §3 :56 起为三方逐行比对章。）

## 4 重叠输入与孤儿分析

### 4.1 重叠输入矩阵（9 类 pre × 9 类 post，两轮独立实跑 72/81 格全落定）

证据：`_r5_probe_import_out.txt`（9 pre × 8 post 全格表 + C1-C5 全 PASS + `PROBE_ALL_PASS`）∪ `_r5v_probe_out.txt` P3（read_error 变体拆 `exists=None`/`exists=True` 两型，C1-C4 PASS）；两轮同格取值**全同**。记法：n=none，N=None（未测），T=True，F=False；PRE=post_read_error，UNK=unknown，EPS=error_pre_snapshot，NFA=new_first_appearance，AB=absent_both，VAN=vanished，NW=new_write，LU=leftover_unchanged，RW=rewritten_same_content。

**4.1a 码实跑全格（verdict·conf·is_new）**：

| pre \ post | read_error·exists=None | read_error·exists=True | 跑后无件 | 在场·缺post.sha | 在场·sha异 | 在场·sha同·mt同 | 在场·sha同·mt升 | 在场·sha同·mt降 | 在场·sha同·mt缺 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| None / {} / 缺state / 脏值（四变体分别实跑、逐格相同；`_r5_probe_import_out.txt:5-8` 四行逐一列出） | PRE·n·N | PRE·n·N | UNK·n·N | UNK·n·N | UNK·n·N | UNK·n·N | UNK·n·N | UNK·n·N | UNK·n·N |
| 显式unknown | PRE·n·N | PRE·n·N | UNK·n·N | UNK·n·N | UNK·n·N | UNK·n·N | UNK·n·N | UNK·n·N | UNK·n·N |
| absent_confirmed | PRE·n·N | PRE·n·N | AB·low·F | NFA·high·T | NFA·high·T | NFA·high·T | NFA·high·T | NFA·high·T | NFA·high·T |
| present（带 pre.sha256） | PRE·n·N | PRE·n·N | VAN·n·N | PRE·n·N | NW·high·T | LU·high·F | RW·med·T | RW·low·T | LU·med·F |
| present（缺 pre.sha256） | PRE·n·N | PRE·n·N | VAN·n·N | EPS·n·N | EPS·n·N | EPS·n·N | EPS·n·N | EPS·n·N | EPS·n·N |
| error | PRE·n·N | PRE·n·N | EPS·n·N | EPS·n·N | EPS·n·N | EPS·n·N | EPS·n·N | EPS·n·N | EPS·n·N |

（present缺pre.sha × 缺post.sha 落 EPS 而非 PRE：码序 7（:4673 缺 pre.sha）先于码序 8（:4678 缺 post.sha）。）

**4.1b 矩阵归属（同一网格，格 = 现行 14 行中按匹配键可命中的行 / 缺口标注）**：

| pre \ post | read_error·exists=None | read_error·exists=True | 跑后无件 | 在场·缺post.sha | 在场·sha异 | mt同 | mt升 | mt降 | mt缺 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| 未采集四变体 | **W1**（:2 后件「跑后任意文件状态」错盖，声称 UNK 实码 PRE） | W1 同 | :2 ✓ | :2 ✓ | :2 ✓ | :2 ✓ | :2 ✓ | :2 ✓ | :2 ✓ |
| 显式unknown | **W1′**（:2 枚举不含显式unknown、:3 前件要「跑后无件」——严格键今日即无行；宽 preState 键读法下 :2/:3 兜住且**标签恰同**，P5 标 MISLABEL 即此读法） | W1′ 同 | :3 ✓ | **O2** | **O2** | **O2** | **O2** | **O2** | **O2** |
| absent_confirmed | **O1 主子格**（无行：:5 要 present、:6 要「在场硬证」、:7 要「无件」，exists=None 三者皆不满足） | **O1′**（:6 字面「跑后在场（存在性硬证）」被满足 → 会误claim NFA/high） | :7 ✓ | :6 ✓ | :6 ✓ | :6 ✓ | :6 ✓ | :6 ✓ | :6 ✓ |
| present（带 sha） | **:5 ✓**（本行自身格，取值正确） | :5 ✓ | :15 ✓ | :14 ✓ | :10 ✓ | :8 ✓ | :11 ✓ | :12 ✓ | :9 ✓ |
| present（缺 pre.sha） | **W3**（:5/:13 重叠：缺pre.sha 前件亦命中，实码 PRE；实际流不可达——make_pre 在场必算 sha :4607，算炸→error；仅 fixture 域） | W3 同 | :15 ✓ | :13 ✓ | :13 ✓ | :13 ✓ | :13 ✓ | :13 ✓ | :13 ✓ |
| error | **W2**（:4 前件无跑后限定，声称 EPS 实码 PRE） | W2 同 | :4 ✓ | :4 ✓ | :4 ✓ | :4 ✓ | :4 ✓ | :4 ✓ | :4 ✓ |

（P5 claimant 交叉表 `_r5v_probe_out.txt:114-136`：preState=unknown 组的 read_error 格 claimant=:2/:3、absent_confirmed 组=:6/:7、present 组含 :5 [MATCH] 与 :8-:15、error 组=:4——与 4.1b 一致。O2 各格今日若按宽键读法被 :2 兜住，标签 unknown 与实码相同，**无误配**，只是登记缺行。）

### 4.2 收紧 :2 后（若采 A/B）哪类输入无行可配

1. **O3（:2 收紧新造的唯一孤儿）**：pre 未采集（None/{}/缺state/脏值）× read_error。:2 前件若限定「跑后读取正常（post.read_error 为空）」，该格严格按键无行。但按上轮建议文案（pf2 §4.5 :193），:2 的新 condition **内嵌分流句**「post.read_error 非空时先落 post_read_error（码序 read_error 出口先于 unknown 出口，候选 :4643 先于 :4648，**见 :5 行**）」——落点在**文档层有记载**，仅严格键匹配层为空。且今天的现状不是孤儿而是**误配**（W1：声称 unknown，实码 post_read_error）——收紧是把「错答」换成「不答」，方向正确。
2. **O1（既有，与 :2 无关）**：absent_confirmed × read_error。主子格（read_bytes/stat 失败，exists=None）无行（孤儿）；write_bytes 子格（exists=True，:4769 先置位→:4772 才可能失败）按 :6 字面会被 claim 并误标 new_first_appearance/high（误配）——复核员细化属实，本轮以实读 :4769-:4772/:4786 确认；:6/:7 均缺 read_error 口径的总结论不变，该细化只会让文档层问题更重。
3. **O2（既有，与 :2 无关）**：显式unknown × 跑后在。严格键今日即无行（:3 前件限定「跑后无件」）；实际流**不可达**（make_pre 三路必覆写初值，§3.1 末 + 探针 P4 False）；宽键读法下标签恰同，无实害。
4. **归因**：既非 :5 单方也非 :2 单方——本体是矩阵缺「read_error × 非 present preState」承载行/注记（该出口按设计 B2B_DESIGN.md:310-311 preState 无关，矩阵 :5 键却 present 独占）；:2 过宽错盖一格（W1）、:4 过宽错盖一格（W2，同型新发现）、absent_confirmed 格裸露（O1）。**收紧 :2 只是掀盖，不制造问题本体**；另有 fixture 域重叠 W3（:5/:13 同抢 present×缺pre.sha×read_error 格）。

### 4.3 三选项与推荐

- **选项 A｜只收紧 :2**（pf2 §4.5 :193 文案原样）：修 W1；O3 成文档级孤儿（分流句兜底）；**O1 仍裸、W2（:4 格）仍是活性误配**——最刺眼残留是 W2：按 :4 匹配的输入会被声称 error_pre_snapshot，实码 post_read_error，正是修正提案:175 警告的「标签误配」换个格子存在。验收面：T5（V2:184，14 组 fixture 四元组断言）不受影响（condition 文本不进四元组断言；R3:42 行1 fixture benign-post 已 match）；T2（unknown→high=0）不受影响。**可接受但不完整。**
- **选项 B｜同时动 :2 与 :5（推荐）**：
  - JSON:2 ← pf2 §4.5 :193 文案原样；
  - JSON:5 condition 追加码序注记（**preState 字段不动**——B2B_DESIGN.md:142 约束 preState ∈ 四态、由 H01 `FRESHNESS_SNAPSHOT_STATES`（候选 :228）约束，写 "any" 违值域契约；域覆盖由 condition 文本承载）：`「跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口（★ N1 码序 read_error 出口先于一切 pre 分支：候选 :4643-4646 先于 :4648 unknown / :4652 error / :4657 无件 / :4666 absent_confirmed / :4672 起 present 支；pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行，preState 列的 present 为最常见登记态，匹配以本 condition 为准）」`；
  - **镜像必改**：B2B_DESIGN.md:151（:5 镜像行，该表带 condition 列且 :144 明言「下表与之逐行一致」）、B2B_DESIGN.md:148（:2 镜像「跑后任意」，pf2:205 已登记滞留风险）；
  - **V2:120 不需要动**：V2 §4.2 表（:114-130）只有五列、无 condition 列，preState 未变则该行仍真；登记项「放宽需连带 V2:120 与 B2B_DESIGN.md:151」（pf2_findings:35②）只在「放宽 = 改 preState 字段」读法下才对 V2:120 成立；
  - **建议随批（同一族，关闭 W2）**：JSON:4 condition 加「（post.read_error 非空时仍先落 post_read_error，见 :5 行）」+ B2B_DESIGN.md:150 镜像同句；不加则须在登记中如实保留 W2；
  - 绑定级联与 A 全同：乙矩阵 sha 变 → V2:46 / 重签件 §2 第 5 行（:34）/ 重签件 :153 生效条件 1 换版登记；B 下乙设计 sha 亦变 → V2:45 行同入。14 行结构不动 → T5 的「14 组 fixture/14/14」无需重述。
- **选项 C｜改结构（拆 :5 成四行或新增行）**：能消严格键孤儿，但 14→15/17 行击穿至少六处**内容级**绑定文本——B2B_DESIGN.md:144「14 项」/:163 八类对账、V2:110「14 数据行」/:114/:184「14 组 fixture/14/14」、重签件 §3:56「矩阵十四行逐行比对」/:148 五项必查 14/14、R3:42-43——不止指纹换版而是断言重写 + T5 重规约，且 preState=any 新行自身违四态值域（B2B_DESIGN.md:142）。对三个落点 confidence=none/is_new=None/usable=False 的 error 格收益边际、代价全面。**不推荐。**
- **推荐：选项 B**。理由：① 两轮 72 格实跑证实 read_error 出口域=四态全体，只做 A 会留下 W2 误配与 O1 裸格；② A→B 的边际代价仅一句（JSON:5 + B2B_DESIGN:151），绑定级联与 A 完全相同（B2B_DESIGN:148 反正要随 :2 修，:144「逐行一致」不变式一破俱破）；③ C 的全量断言重写与三个 none 格的收益不成比例。若取绝对最小批（A），**必须同步 :148 镜像**（否则双源不一致，见 §4.5），并如实登记 W2/O1 残留。

### 4.4 「最小修复面」grep 复核（本轮自跑，不采信上轮口径）

| # | 命令（本轮实跑，cwd=D:\Project\ra2-campaign-forge） | 结果 | 判读 |
|--:|:--|:--|:--|
| 1 | `grep -rl "任意文件状态" . --exclude-dir=.git` | 18 件命中：规范源仅 `lead/b2b_design_20261106/STATE_MATRIX.json`；其余全部为**转引该登记**的复审/审计/台账/规格/脚本件（R2 及两审计、R3 及审计、旧复审及审计、重签件:89、B_EXECUTION_SPEC_V2_YI:150、cs 复核:44、bexec 规格:117、pf2 两件、修正提案 :119/:126/:138/:141/:175/:183/:205/:206/:232、gate 复盘探针输出、上轮评估件、`_pv_checks.py`/`_pf2_read3.py` 引证） | 「该词组仅存于 JSON:2」（pf2:206、修正提案 §4.7-3）**复核成立**——无第二规范源 |
| 2 | `grep -rn "跑后任意" --include="*.md" --include="*.json" . --exclude-dir=.git` | `B2B_DESIGN.md:148`（**设计镜像**）+ 非绑定副本 4 处：`_draft_semantics.md:146`、`B2B_PREAUDIT.md:138`、`B_EXECUTION_SPEC.md:102`（:117 为登记转引）、`_n4_SPEC_N4_B2B_MATRIX.md:89`，另 11 处为 R2/R3/cs/重签件/pf2/修正提案的登记/转引行 | B2B_DESIGN 内「跑后任意」仅 :148——上轮「grep 0 命中」字面为真（pf2:206）；**复核员细化 (b) 独立复现属实**：4 处陈旧副本均不在 V2:45-46 绑定表、非重签件 :153 指纹对象 |
| 3 | `grep -n "连带供裁量\|matrix_row5\|欠宽\|:5 行\|post_read_error" lead/PENDING_DECISIONS.md` | **0 命中**（exit=1） | 台账一未载 :5 连带项 |
| 4 | 同词 `lead/GOAL_THREE_TARGETS_20261018.md` | 仅 :9173 一处无关命中（「另 12 项覆盖：`src_missing`、`post_read_error`…」——本轮 Read :9169-9174 定性为历史测试覆盖枚举，与 :5 行无涉） | 台账二亦未载 :5 连带项（上轮评估仅对 PENDING 实跑过，本轮补齐） |

结论：pf2 §4.5:196「最小修复只动一行」在 **JSON 单文件内字面成立**，但**语义层不成立**（:148 镜像，见 §4.5）；:5 连带项目前**两台账均无登记行**。

### 4.5 双源不一致风险

1. **JSON ↔ 乙设计**：B2B_DESIGN.md:144 明言设计 §2 表「下表与之逐行一致」，:148 以「跑后任意」承载与 JSON:2 完全相同的过宽语义（本轮实读 :148）。只改 JSON:2 不同步 :148，即成双源不一致——同一行两处口径（JSON 说「跑后读取正常 + 分流见 :5」，设计表仍说「跑后任意→unknown」）。
2. **既定门禁抓不到它**：T5（V2:184）只做 14 组 fixture 的代码↔矩阵四元组断言，从不比对 B2B_DESIGN §2 表与 JSON；T2（V2:181）只查 verdict 级性质（unknown→high=0）；重签件 :154 生效条件 2 的「三方不分叉」= STATE_MATRIX ↔ V2 §4.2 ↔ 候选实码、只比 (verdict,confidence)，**不含 B2B_DESIGN**。故该不一致会静默通过全部既定门禁，只能靠人工/代理复读发现（pf2:205 已登记滞留风险）。
3. **扩大面（更严标准下的批注项，不阻塞）**：§4.4-2 的 4 处非绑定副本（_draft_semantics:146、B2B_PREAUDIT:138、B_EXECUTION_SPEC:102、_n4_SPEC_N4_B2B_MATRIX:89）同滞留旧语义；均非 V2:45-46 绑定表与重签件 :153 指纹对象，不动摇选项 B 的必改清单；若采「无陈旧措辞残留」标准可作随批批注。

## 5 复核回件与声明

### 5.1 复核 verdict

**confirmed**（如实记；refuted/partial 才标 unconfirmed，本件不适用）。复核回件无推翻项：九件基线 9/9 逐字节一致；独立 AST 码序 0 偏差；72 格实跑 C1-C4 全 PASS；W1/W2/O1 独立复现；选项代价全部落到实读文本。两处**不改变结论的细化**已并入本件：细化 (a)——O1 的 write_bytes 子格（exists=True）按 :6 字面属误配而非纯孤儿，主导子格（read/stat 失败，exists=None）确为孤儿（§4.1b/§4.2-2）；细化 (b)——「跑后任意」语义另滞留于 4 处非绑定副本（§4.4-2/§4.5-3）。复核员自记未跑项见 §5.5。

### 5.2 绑定行（本轮 `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\matrix_row5_20261109\_r5c_fingerprint.py` 实算，10/10 MATCH，输出 `_r5c_fingerprint_out.txt`）

被核对象 SHA256 = `625436050020104bb6e40bd7b1ec0543b22e3e31cb5bb56a12b0480cff64e26f`，字节数 = 14616
被核对象 SHA256 = `1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016`，字节数 = 3558
被核对象 SHA256 = `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf`，字节数 = 66735
被核对象 SHA256 = `ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2`，字节数 = 412759
被核对象 SHA256 = `c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801`，字节数 = 28897
被核对象 SHA256 = `1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b`，字节数 = 23129
被核对象 SHA256 = `b1231ccb8b80c5200e2ff33b15e09ae52b0452a1481dfc7989730f7da16eda5b`，字节数 = 22048
被核对象 SHA256 = `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636`，字节数 = 399508
被核对象 SHA256 = `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7`，字节数 = 52419
被核对象 SHA256 = `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede`，字节数 = 759518

（第 1 行 = 被核回件本体 `lead/matrix_row5_20261109/_r5_row5_linkage_assessment.md`；第 2-10 行 = 编排方基线九件，顺序：乙矩阵 / 乙设计 / 候选LF / V2 / 重签件 / 修正提案 / 母本 / PENDING / GOAL 台账。）

### 5.3 未改任何文件声明

本任务**未改任何文件**：上列 10 件被核对象（含只读九件与被核回件本体）零改动——本轮 hashlib 实算与编排方基线、复核回件三方逐字节一致（10/10 MATCH）。本件新增仅三个文件、全部落唯一写域 `lead/matrix_row5_20261109/`：`MATRIX_ROW5_COUPLING.md`（本件）、`_r5c_fingerprint.py`、`_r5c_fingerprint_out.txt`。未 commit、未 push；零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（探针为纯函数级标准 import + AST 静态分析，无 hook / MiniDump / SuspendThread / StackWalk / 注入 / 动态内存解析）。本件通篇为**建议与裁量材料**，不含任何既成事实改动断言；任何改动须走 §5.4 批准人 + 指纹换版登记。

### 5.4 需谁批准

1. **主批准人：乙设计责任人**（修正提案 §4.6:200「需乙设计责任人批准（`STATE_MATRIX.json` 为乙矩阵，其定版主体为乙设计侧）」、:232 判定表同）。:2/:4/:5 三行的 condition 措辞变更同属此主体。
2. **镜像连带（若采 B）**：B2B_DESIGN.md:148/:151（及随批的 :150）改在乙设计本体内——同一批准人；改则乙设计指纹换版（V2:45 行同入级联）。
3. **绑定级联登记（非内容批准、是登记义务）**：乙矩阵 sha 变 → V2:46、重签件 §2 第 5 行（:34）、重签件 :153 生效条件 1（指纹漂移即失效）须换版登记；B 形态下 V2/重签件**正文内容无需改**（V2:120 不动），故不需要 V2 来源会话对内容另行批准，仅需签发侧执行换版登记（对照先例：pf2 事项一 :231——只有 V2 **内容**改动才需 V2 来源会话批准）。
4. **若采 C**：另需 T5 重规约与门禁签发侧批准（14→15/17 行击穿 §4.3-C 列六处内容级断言）——此为不推荐 C 的代价构成之一。
5. **台账补登**：编排方（lead）统筹将本连带项（:5 欠宽 + W2/O1/O2/O3 + 选项 B 建议）补登两台账——两台账现均未载（§4.4-3/4 本轮实跑）。

### 5.5 未验项（如实登记，不补造）

1. **T1/T2/T5 门禁本轮与上轮均未跑**：V2:180-184 三项均自记「本轮未跑」；R3:42「14/14 逐行 match」为历史转引（其 `_review_probe_r3_out.txt` 未复读，V2:180 亦注明 R3:145 `PASS=29 FAIL=0` 为历史转引）。若采 A/B/C 任一，N-5 集成时须对**应用后副本**重跑（V2:187）。
2. R2/R3 历史实跑输出与自述档链未独立复核（本件相应处均标「转引」）。
3. pre=present + exists=False + read_error 同置的组合格未测：实流不可达（copy 路径 exists 只取 False@:4757 / None / True@:4769 三值，read_error 置位@:4786 不与 exists=False 同路），仅 fixture 域理论重叠 :15/:5。
4. 「跑后载体件快照」候选 :4816-4825 等本函数之外的收尾链未展开（与 :5 行无涉）。
5. 重签件 :170「两项均已原样上账」的台账落行 = 未验（pf2_findings 附记 + 修正提案 §5.3:236-237 已登记；本轮 §4.4-3/4 同向：两台账未检得对应行）。
6. B2B_DESIGN §2 表（:146-161）与 JSON 14 行的一致性，本轮为**人工实读对照**（14 行 verdict/confidence/usable 逐行相符），未做程序化逐字 diff——「逐行一致」断言的全面程序化复核未跑。
