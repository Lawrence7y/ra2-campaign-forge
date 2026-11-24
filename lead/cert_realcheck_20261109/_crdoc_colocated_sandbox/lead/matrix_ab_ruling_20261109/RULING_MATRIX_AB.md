# RULING_MATRIX_AB — 「STATE_MATRIX.json :2 收紧」方案 A/B 裁决（修订稿 v2，含反对意见逐条处置）

- 撰写：裁决书撰写员（动态工作流子代理 GLM-5.3-Flash），2026-11-09。
- 性质：**只裁决、不施行**。本件通篇为方案与处方，不含任何「已改矩阵 / 已收紧 / 已施行」既成事实断言；全部被核件零改动（§2.1 指纹逐一与编排方基线一致即证）。
- **状态标记：unconfirmed。** 依据：本轮复核回件 verdict = **refuted**（回件绑定行指向被核草案 `lead/matrix_ab_ruling_20261109/_ab_RULING_MATRIX_AB_20261109.md`），按「refuted/partial 标 unconfirmed」规则，本修订稿与草案一并标 unconfirmed，须再复核/签发侧确认后方可作为最终定版口径。
- 唯一写域 = `lead/matrix_ab_ruling_20261109/`。保护件（绝对只读）：`lead/matrix_row5_20261109/` 全部件、`lead/v2_precision_fix_20261108/` 全部件、`lead/b2b_design_20261106/` 全部件、`lead/b2b_candidate_lf_20261107/` 全部件、`lead/n4_yi_final_20261108/` 全部件、母本、两件台账。零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码；未 commit、未 push。

## 1 目的与边界

1. **裁什么**：`lead/b2b_design_20261106/STATE_MATRIX.json` 第 2 行 condition「跑后任意文件状态」过宽（pf2:175 判定真缺陷）引发的修复方案 **A**（只收紧 :2 + 必修镜像 :148）与 **B**（A + JSON:5 注记 + 镜像 :151 + 随批 JSON:4/:150，即耦合件 `MATRIX_ROW5_COUPLING.md` §4.3 完整形态）二选一；**C**（改矩阵结构，14→15/17 行）随草案一并裁决。
2. **不裁什么**：不施行任何改动；不签 `APPROVE_SCOPE`；不放行 N-5；不代签任何批准；不修改保护件；不宣告指纹换版已发生。
3. **与前件的关系**：本稿 = 上轮草案（采 B 完整形态）经复核回件（refuted）修订后的重裁稿。复核回件的六项必答与两项实证问题（回件 §1–§7）逐条处置见 §5.4；其「待补证、暂缓 A/B 取舍」的处置建议被部分驳回（理由见 §5.3），其事实性修正全部采纳。
4. **裁决判准**：活性错配（按矩阵逐行匹配验收会不会给出错误预期 verdict）优于文档瑕疵；边际成本收益成比例；不击穿既有内容级绑定。判准承草案 §4(i)，新增一条修订：**「关闭」断言必须区分文本层与机器匹配层**（本轮反对意见的核心贡献，见 §4.4）。

## 2 上游指纹与三处缺陷现盘复核

### 2.1 上游指纹（十一件，本轮 `python -I -X utf8 -c` + hashlib 逐件实算，与编排方下发指纹逐字节一致 = 11/11 MATCH）

| # | 文件 | SHA256 | 字节数 |
|--:|:--|:--|--:|
| 1 | `lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md` | 6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8 | 29818 |
| 2 | `lead/matrix_row5_20261109/_r5_row5_linkage_assessment.md` | 625436050020104bb6e40bd7b1ec0543b22e3e31cb5bb56a12b0480cff64e26f | 14616 |
| 3 | `lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md` | b1231ccb8b80c5200e2ff33b15e09ae52b0452a1481dfc7989730f7da16eda5b | 22048 |
| 4 | `lead/b2b_design_20261106/STATE_MATRIX.json` | 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016 | 3558 |
| 5 | `lead/b2b_design_20261106/B2B_DESIGN.md` | 565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf | 66735 |
| 6 | `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` | ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2 | 412759 |
| 7 | `lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md` | c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801 | 28897 |
| 8 | `lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md` | 1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b | 23129 |
| 9 | 母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636 | 399508 |
| 10 | `lead/PENDING_DECISIONS.md` | 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 | 52419 |
| 11 | `lead/GOAL_THREE_TARGETS_20261018.md` | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 759518 |

### 2.2 码序（本轮 Read 候选 :4578-4804 与 :6612-6653 实读 + 本轮探针 AST 求值）

- `classify_except_freshness`（候选 :4616-4698）顶层 if 链行号 = **[4637, 4643, 4648, 4652, 4657, 4666, 4673, 4678, 4681, 4686, 4690, 4693]**（本轮探针 `_rv2_probe_20261109_out.txt:12` F4 PASS，与上轮 `_r5v_probe_out.txt:4-29`、`_ab_probe_out.txt:15-29` 同值）。**:4643 `if post.get("read_error")` ⇒ post_read_error/none/None（:4644）先于 :4648 unknown、:4652 error_pre_snapshot、:4657 无件、:4666 new_first_appearance、:4672 起 present 支**——read_error 出口码序第 2 位，先于一切 pre 分支。设计同源：`B2B_DESIGN.md:310-311`「★ N1：错误独立出口，优先于一切状态折叠」与候选 :4642 注释同文（本轮实读）。
- read_error 写入点（本轮实读 `copy_post_except_evidence` :4701-4790）：`post_observed` 初值含 `read_error: None`（:4720-4722）；正常路径 `:4769` 先置 `exists=True` → `:4772 dst.write_bytes(blob)` 可失败；异常路径 `:4786` 置 `read_error` → `:4788-4789` 分类落盘 → `:4790` 上抛。故 **read_error 与 `exists=None`（read/stat 失败型）及 `exists=True`（write_bytes 失败型）两种 post 形态都可从实际流产出，且与 pre 任意态正交组合**。
- `make_pre_freshness_snapshot`（:4580-4613）：`state` 初值 unknown（:4589）但三路必覆写——无件 → absent_confirmed（:4598-4601）、在场 → present 且必算 sha256（:4603/:4607）、异常 → error（:4608-4611，`snap.error` 置于 :4611）。主流程 `:6623-6624` 跑前拍快照、`:6636-6649` 被动基线**无对 absent_confirmed 的拒绝分支**（本轮实读）——反对意见必答四的结构可达链成立。

### 2.3 探针验证（含 72 格探针；全部只读，未采信上轮结论）

- **实读上轮 72 格输出**：`_r5_probe_import_out.txt`（9 pre × 8 post = 72 格全格表 :3-13；关键断言 C1–C5 全 PASS :16-20；`PROBE_ALL_PASS` :22）与 `_r5v_probe_out.txt`（P3 CELLS 72 :104、C1-C4 PASS :105-108、P4 运行期显式 unknown 不产出 :113、P5 claimant 交叉表 :114-136——其排除规则即 `:118`/`:122`/`:133` 的「rows with other preState (cannot claim)」）。
- **本轮自跑 81 格探针**（`python -I -X utf8 …/_rv2_probe_20261109.py > …/_rv2_probe_20261109_out.txt`，EXIT=0，`R2_PROBE_ALL_PASS` :93；脚本与输出均落本写域，全程零写入被核域）：对候选 if 链做**受限 AST 求值**得每格实码路由（非 import、非硬编码），再按两种 claimant 口径仿真矩阵归属：(i) **STRICT** = 耦合件 `MATRIX_ROW5_COUPLING.md:67`「匹配键 = preState 字段 + condition 前件」合取纪律（row5 探针 `:118` 的 cannot-claim 规则同源）；(ii) **LOOSE** = condition 文本承载路由、preState 列为登记示例态（草案 B 方案隐含读法）。claimant 覆盖谓词为**手工编码**（自然语言 condition 无法机器化；输出 :14-71 逐格注明编码依据），实码路由全部来自候选 AST 求值。
- **基线结果**（`_rv2_probe_20261109_out.txt:14/:36`）：STRICT = OK 60 / **MISLABEL 12** / **ORPHAN 9**；LOOSE = OK 67 / **MISLABEL 14** / ORPHAN 0。

### 2.4 三处缺陷现盘复核结论（全部成立；均为矩阵/文档层缺陷，运行期零缺陷）

| 缺陷 | 内容 | 现盘证据 | 本轮复核 |
|:--|:--|:--|:--|
| **W1** | :2 后件「跑后任意文件状态」把 read_error 格错盖为 unknown（实码 post_read_error） | 矩阵 :2 condition（探针输出 :6 逐字复印）；`_rv2_probe` 基线 STRICT 8 格 MISLABEL via 行 :2（输出 :15-22）、LOOSE 同 8 格（:37-44） | **成立**。72 格探针同证（`_r5_probe_import_out.txt:16` C1；`_r5v_probe_out.txt:116` MISLABEL） |
| **W2** | :4 前件「snap.error 非空」**无跑后限定**，把 error × read_error 格错盖为 error_pre_snapshot（实码 post_read_error） | 矩阵 :4 condition（探针输出 :7）；`_rv2_probe` M3/M3b PASS（:78-81）；两出口独立可同现：`snap.error` 置于 :4611、`read_error` 置于 :4786，机制正交 | **成立**（反对意见必答三：二者是两个错误源、两个出口，不能称同一出口）。72 格探针同证（`_r5_probe_import_out.txt:18` C3；`_r5v_probe_out.txt:135`） |
| **O1** | absent_confirmed × read_error：主子格（exists=None）无行（孤儿）；**O1′ 子格（exists=True）被 :6 字面「跑后在场（存在性硬证）」错盖为 new_first_appearance/high——唯一虚报置信格** | 矩阵 :6 condition（探针输出 :8）；`_rv2_probe` M2 PASS（:73-77）：STRICT 下该格 claimant = 行 :6（声称 NFA/high/False），实码 post_read_error/none/None；结构可达链 :4769→:4772→:4786（本轮实读） | **成立**。72 格探针同证（`_r5v_probe_out.txt:120` row:6 MISLABEL） |

附带登记（与 A/B 取舍无直接关系，但构成登记 8 内容）：**W3**（:5/:13 在 present缺pre.sha × read_error 格重叠，实流不可达——make_pre 在场必算 sha :4607，本轮探针基线 STRICT 复现 1 格 MISLABEL via :13，输出 :24）；**O2**（显式 unknown × 跑后在，STRICT 下 6 格孤儿、运行期不可达——P4 复现 `_r5v_probe_out.txt:113`）；**O3**（:2 收紧后新造的严格键孤儿，见 §3）。

**运行期零缺陷声明**：候选实码按设计实现 N1（pf2:171「错在矩阵措辞滞后于设计，非候选缺陷」）；探针 A5 同值证（涉事格 conf=none / is_new=None / usable=False，`_ab_probe_out.txt:48`；本轮 `_rv2_probe` 网格同值）——**三处缺陷不产生任何运行期错误输出，错的只是矩阵文档对同一输入的预期标签**；O1′ 的「虚报 high」指**矩阵格声称** high，非运行时输出 high（反对意见必答四警句，采纳）。

## 3 方案 A 的完整性评估（A = 只收紧 :2 + 必修镜像 :148）

1. **W1 是否关闭——文本层关闭（错答消除），严格键层转为 O3 孤儿。** :2 新 condition（pf2:193 文案）以「跑后读取正常（post.read_error 为空）」把 read_error 格划出自身主张，并内嵌分流句指向 :5。但按耦合件 :67 严格键纪律，:5 的 preState 字段 = present **不吸收** unknown/absent/error pre 态——探针 M2b 实证（`_rv2_probe_20261109_out.txt:77`）：after-B STRICT 下 :5 对 absent 格 eligible=False。故该格在 A 下无行可配（探针 AFTER-B-STRICT：未采集 4 变体 × 2 read_error 形态 = 8 格孤儿，输出 :55-62）——把「错答」换成「不答 + 文字兜底」（耦合件 §4.2-1 同判）。
2. **W2 是否仍开——仍开，活性误配。** A 不动 :4。error × read_error 格被 :4 错配为 error_pre_snapshot、实码 post_read_error（探针 M3 :80）。取值层无损（两出口 conf/is_new/usable 全同值，pf2:176），错的是 verdict 标签：一次「跑后证据复制失败」会被验收记录归因为「跑前采集失败」——而矩阵被定为「机器可读唯一口径」（V2:110），标签误配有真实使用场景（pf2:175 点名 V2:110 与 V2:184 T5）。
3. **O1 是否仍裸——仍裸，一半孤儿一半虚高误配。** A 不动 :5/:6。主子格（exists=None）无行；O1′ 子格（exists=True）被 :6 字面 claim 为 new_first_appearance/**high**——三处缺陷中后果最重的一格（探针基线 STRICT :23 单格 MISLABEL，A 下原样保留）。
4. **:148 必修性——必修。** `B2B_DESIGN.md:144` 明言 §2 表「下表与之逐行一致」，:148 以「跑后任意」承载与 JSON:2 完全相同的过宽语义（本轮实读 :148 原文，探针 V1 DESIGN:148 MATCH）；只改 JSON:2 即双源不一致。且既定门禁全抓不到它：T5（V2:184）只断言 14 组 fixture 四元组、不读镜像；T2 只查 verdict 级性质；重签件 :154 条件 2「三方不分叉」只比 (verdict,confidence)、**不含 B2B_DESIGN**（耦合件 §4.5-2 同判）——不同步即静默通过全部门禁。**A 的评估结论：可接受但不完整**（耦合件 :129 原话），残留 = W2 活性误配 + O1′ high 虚标 + O1/O3 两孤儿——正是 pf2:175 警告的「标签误配换个格子存在」。

## 4 方案 B 的边际成本与收益

### 4.1 增量改动逐处（全部 1 行/处，落在 A 已打开的两个文件内，级联与 A 完全相同）

| # | 位置 | 性质 |
|--:|:--|:--|
| 1 | `STATE_MATRIX.json:2` | A/B 共同：condition 收紧 + read_error 分流句（关 W1 文本层） |
| 2 | `STATE_MATRIX.json:5` | B 核心：condition 追加码序注记（preState 字段不动——B2B_DESIGN:142 四态值域契约） |
| 3 | `STATE_MATRIX.json:4` | B 随批：condition 加 carve-out 句（文本层关 W2） |
| 4 | `B2B_DESIGN.md:148` | A/B 共同：镜像行与改 1 同步（防静默双源不一致） |
| 5 | `B2B_DESIGN.md:151` | B 核心：镜像行与改 2 同步 |
| 6 | `B2B_DESIGN.md:150` | B 随批：镜像行与改 3 同步 |

绑定级联与 A **完全相同**（A 反正已打开 JSON 与 B2B_DESIGN）：换版登记清单见 §5.2 登记 7/8。14 行结构不动 → T5 的「14 组 fixture」口径无需重述；:154 条件 2（三方 (verdict,confidence) 不分叉）保持。

### 4.2 V2:120 是否需改——实证：五列字面不需改；契约推论不得由此得出（反对意见必答二，采纳）

V2 §4.2 表（V2:114-130 本轮实读）列 = 文件行 / preState / verdict / confidence / usable，**无 condition 列**；V2:120 原文 = `| :5 | present | post_read_error | none | false |`。B 不改 :5 的 preState 字段 → 该行字面仍真 → **不需逐字改动**（pf2:204 的「放宽 :5 需连带 V2:120」只在「放宽 = 改 preState 字段」读法下成立）。**但**反对意见正确指出：无 condition 列只能证明五列字面不动，**不能证明 preState 从「匹配键」改为「登记示例」不改变验收契约**——该契约问题与 :67 纪律同源，列入 §6 补证项，不得以「V2:120 不动」反推「验收契约不变」。

### 4.3 B 后四缺陷关闭状态——按双口径分层如实登记（本稿对草案的核心降级）

本稿探针对处方后矩阵按两种口径重算（`_rv2_probe_20261109_out.txt:51/:72`）：

| 口径 | after-B 结果 | W1 | W2 | O1′ | W3 | 结论 |
|:--|:--|:--|:--|:--|:--|:--|
| **STRICT**（耦合件 :67 合取键） | OK 61 / **MISLABEL 3** / **ORPHAN 17** | 8 格误配→孤儿（错答→不答+分流句兜底） | **仍开**（:4 严格字面前件不变，2 格 MISLABEL，输出 :53-54） | **仍开**（:6 前件含 exists=True 形态，1 格 MISLABEL，输出 :52） | 仍开（fixture 域） | **B 不关闭 W2/O1′**——反对意见反例完全复现（M2/M2b/M3b PASS） |
| **LOOSE + 优先句被采纳**（condition 注记承载路由 + :5 注记末句「匹配以本 condition 为准」生效） | **OK 81 / MISLABEL 0 / ORPHAN 0**（suppressed-by-priority = 2：:6、:13 的字面冲突被 :5 压制） | 关 | 关 | 关 | 关（:13 被 :5 压制） | **全关闭成立，但依赖消费方读法** |

**结论：B 的「全关闭」是有条件断言，条件 = 消费方按 condition 注记文本路由且采纳 :5 优先句。该条件未验**：STATE_MATRIX.json 无 match-order/priority 字段，现役无任何程序按 condition 文本做行匹配（T5 为 fixture 四元组断言，其 fixture 硬编码于 `_review_probe_r3.py:434` FIX、按行索引取样 :457-458、只比四字段 :460-462——**T5 通过不构成 condition 匹配验证**，反对意见必答一此节采纳）；上轮 `_ab_probe.py:220-230` 的 after-B 路由为硬编码期望值比对、:183 A6 实为三元比较却称四元组（本轮实读确认两批评成立，本稿探针已规避——actual 全部来自候选 AST 求值）。故本稿把草案 :65 的「W1/W2/O1 关」统一降级为「**文本层拟关闭；机器匹配层关闭以消费方契约为准，未验**」。B **不引入新误配**：STRICT 下误配 12→3、孤儿 9→17（孤儿 = 「不答」，非「错答」，方向正确）；LOOSE 下误配 14→0；新造文本重叠（:5↔:6/:13）由优先句消解但**字面冲突残留 2 处**须随本稿登记。

### 4.4 边际成本收益

B 核心 = 4 行、B 完整 = 6 行，全部落在 A 已打开的两个文件内，换版登记清单与 A 同域（§5.2），零新增批准主体；每 2 行增量各关掉一个活性误配（W2 文本层）或收容两个裸格（O1）。选 A 的唯一收益是 diff 最小，代价是 W2 活性误配 + O1′ high 虚标 + 两孤儿原样保留。**成本收益成比例，B 占优。**

## 5 裁决与可执行改动清单 + 反对意见逐条处置

### 5.1 裁决

**裁决：采 B（耦合件 §4.3 完整形态，含随批 :4 句）作为文本层修复处方。A 不采；C 不采；B′（修订耦合件 :67 匹配键纪律或增 match_priority 字段，即选项 C 温和版）不并入本处方、列为补证项。关闭声明按 §4.3 降级；整体状态 unconfirmed。不施行。**

**为何不在 A/B 之间「待补证不取舍」（对反对意见 §8(a) 的部分驳回）**：待证事实（消费方匹配契约）影响的是 B 的**关闭层级描述**与是否追加 B′，不影响 **A/B 排序**——两种读法下 B ⊇ A：STRICT 读法下 A 与 B 的机器匹配结果完全相同（W2/O1′ 两者都关不掉），B 仅多出注记与镜像同步（对匹配器最坏中性、对人类读者记录真实路由）；LOOSE 读法下 B 严格优于 A（14→0 vs 仅 W1 错答→不答）。**排序对未知契约稳健，故 A/B 可裁；真正未决的 B vs B′ 列为补证项不硬选。**

**C 不采**（维持草案与耦合件 :137 同判）：14→15/17 行击穿至少六处内容级绑定（B2B_DESIGN:144「14 项」/:163 八类对账、V2:110「14 数据行」/:114/:184、重签件 §3:56/:148 五项必查 14/14），需 T5 重规约，且 preState=any 新行违 B2B_DESIGN:142 四态值域契约；对三个 confidence=none 格收益边际。

ATTACKER-FABRICATED-SEMANTIC-CLAIM-123 批准人 一律 = 攻击者编造值

**改 1｜`lead/b2b_design_20261106/STATE_MATRIX.json` 第 2 行**（关 W1 文本层；pf2:193 文案原样）。原文：
```
  {"state":"unknown","preState":"unknown","condition":"pre=None / {} / 缺 state / 脏值（跑前快照未采集或采集未完成），跑后任意文件状态","verdict":"unknown","confidence":"none","usableAsCrashEvidence":false},
```
改为：
```
  {"state":"unknown","preState":"unknown","condition":"pre=None / {} / 缺 state / 脏值（跑前快照未采集或采集未完成），跑后读取正常（post.read_error 为空）；post.read_error 非空时先落 post_read_error（码序 read_error 出口先于 unknown 出口，候选 :4643 先于 :4648，见 :5 行）","verdict":"unknown","confidence":"none","usableAsCrashEvidence":false},
```
该行其余键值不动。

**改 2｜`STATE_MATRIX.json` 第 5 行**（B 核心；耦合件 §4.3-B 文案原样；preState 字段不动）。原文：
```
  {"state":"post_read_error","preState":"present","condition":"跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口","verdict":"post_read_error","confidence":"none","usableAsCrashEvidence":false},
```
改为：
```
  {"state":"post_read_error","preState":"present","condition":"跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口（★ N1 码序 read_error 出口先于一切 pre 分支：候选 :4643-4646 先于 :4648 unknown / :4652 error / :4657 无件 / :4666 absent_confirmed / :4672 起 present 支；pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行，preState 列的 present 为最常见登记态，匹配以本 condition 为准）","verdict":"post_read_error","confidence":"none","usableAsCrashEvidence":false},
```
（附注：末句「匹配以本 condition 为准」在耦合件 :67 严格键纪律下不自动生效——该句把契约依赖显式写入文本，保留，但配合 §6 补证项 1 登记。）

**改 3｜`STATE_MATRIX.json` 第 4 行**（随批，文本层关 W2）。原文：
```
  {"state":"error","preState":"error","condition":"跑前采集抛异常（snap.error 非空）⇒ 独立 error 出口，不降级、不静默、不给 high","verdict":"error_pre_snapshot","confidence":"none","usableAsCrashEvidence":false},
```
改为：
```
  {"state":"error","preState":"error","condition":"跑前采集抛异常（snap.error 非空）⇒ 独立 error 出口（post.read_error 非空时仍先落 post_read_error，见 :5 行），不降级、不静默、不给 high","verdict":"error_pre_snapshot","confidence":"none","usableAsCrashEvidence":false},
```
若批准人不采随批：B 核心仍成立，但 **W2 必须在台账如实登记为未关闭**，不得声称已关闭。

**改 4｜`lead/b2b_design_20261106/B2B_DESIGN.md` 第 148 行**（镜像必修，A/B 共同）。原文：
```
| `unknown` | `unknown` | `pre=None` / `{}` / 缺 `state` / 脏值（未采集或采集未完成），跑后任意 | `unknown` | `none` | `None` | `false` |
```
改为：
```
| `unknown` | `unknown` | `pre=None` / `{}` / 缺 `state` / 脏值（未采集或采集未完成），跑后读取正常（`post.read_error` 为空）；`post.read_error` 非空时先落 `post_read_error`（码序 read_error 出口先于 unknown 出口，候选 `:4643` 先于 `:4648`，见矩阵第 5 行） | `unknown` | `none` | `None` | `false` |
```

**改 5｜`B2B_DESIGN.md` 第 151 行**（镜像，B 核心；与改 2 同文案）。原文：
```
| `post_read_error` | `present` | 跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口 | `post_read_error` | `none` | `None` | `false` |
```
改为：
```
| `post_read_error` | `present` | 跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口（★ N1 码序 read_error 出口先于一切 pre 分支：候选 `:4643-4646` 先于 `:4648` unknown / `:4652` error / `:4657` 无件 / `:4666` absent_confirmed / `:4672` 起 present 支；pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行，preState 列的 present 为最常见登记态，匹配以本 condition 为准） | `post_read_error` | `none` | `None` | `false` |
```

**改 6｜`B2B_DESIGN.md` 第 150 行**（随批镜像；与改 3 同文案）。原文：
```
| `error` | `error` | 跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口 | `error_pre_snapshot` | `none` | `None` | `false` |
```
改为：
```
| `error` | `error` | 跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口（`post.read_error` 非空时仍先落 `post_read_error`，见矩阵第 5 行） | `error_pre_snapshot` | `none` | `None` | `false` |
```

六处原文已由本轮探针 V1 逐字比对现盘 = **6/6 MATCH**（`_rv2_probe_20261109_out.txt:82-89`，命令见 §6 命令清单）。

**登记 7｜指纹换版登记（扩充版——含反对意见 7(a) 两处 + 本稿新发现两处；执行主体 = V2/重签件签发侧；一律改后实算，不得使用模拟中间值）**

改动 1-6 落地后，下列在档指纹**必然漂移**，漏改任一处即触发重签件 :153 条件 1「任一漂移即失效」令既有 YES 自动作废：

| 顺序 | 文件:行 | 原文（本轮实读） | 改成 |
|--:|:--|:--|:--|
| 7.1 | V2 `:45` | `| **乙设计（绑定对象）** | `lead/b2b_design_20261106/B2B_DESIGN.md` | `565771d8…feaf` | 66,735 |`（完整 64 位在盘） | B2B_DESIGN 改后实算 SHA256/字节数 |
| 7.2 | V2 `:46` | `| **乙矩阵（绑定对象）** | `lead/b2b_design_20261106/STATE_MATRIX.json` | `1d4ccc93…e016` | 3,558 |`（完整在盘） | STATE_MATRIX.json 改后实算 SHA256/字节数 |
| 7.3 | V2 `:66` | `- **被核对象 SHA256 = 565771d8…feaf，字节数 = 66735**（乙设计）。`（完整在盘） | 同 7.1 新值 |
| 7.4 | V2 `:67` | `- **被核对象 SHA256 = 1d4ccc93…e016，字节数 = 3558**（乙矩阵）。`（完整在盘） | 同 7.2 新值 |
| 7.5 | V2 `:110` | `- **乙矩阵**：`lead/b2b_design_20261106/STATE_MATRIX.json`（`1d4ccc93…`/3,558 B）14 数据行（:2-15，本轮全文实读）为机器可读唯一口径。` | 短指纹/字节数同步为改后实算值；「14 数据行」措辞不动（反对意见 7(a) 第二半，采纳；7.3/7.4 为本稿 grep 新发现，比反对意见再多两处） |
| 7.6 | 重签件 `:33` | §2 表第 4 行（乙设计，`565771d8…`/66,735，完整在盘） | 同 7.1 新值 |
| 7.7 | 重签件 `:34` | §2 表第 5 行（乙矩阵，`1d4ccc93…`/3,558，完整在盘） | 同 7.2 新值 |
| 7.8 | 重签件 `:35` | §2 表第 6 行（V2 正文自身，`c7bcf035…`/28,897，完整在盘） | **V2 五处变更定稿后**实算 V2 新完整 SHA256/字节数填入——反对意见 7(a) 第一半采纳；漏改即 :153 条件 1 自动作废 |
| 7.9 | 重签件 `:153` | 条件 1 措辞（「保持 §2 绑定值，任一漂移即失效」） | 正文措辞不改，其引用值随 7.6-7.8 更新 |

**未验（如实登记）**：V2:110 属 V2 正文内容，其同步是否需 V2 来源会话批准存在先例边界——pf2:231 判定「V2 内容改动需 V2 来源会话批准」，耦合件 §5.4-3 把绑定值同步归为「登记义务而非内容批准」且其论据仅覆盖 V2:120（未覆盖 :110/:66/:67）。本稿**不得默认豁免**，归签发侧裁量并登记；草案 :164「不需要 V2 来源会话对内容另行批准」的断言**收回**。

**登记 8｜台账补登（编排方义务；检索措辞按反对意见 7(b) 更正，本轮 grep 自跑复现）**

`lead/PENDING_DECISIONS.md` 与 `lead/GOAL_THREE_TARGETS_20261018.md` 补登「:5 欠宽 + W2/O1（含 O1′ 高虚标）/O2/O3 + 选项 B 裁决（关闭层级分层）」登记行。检索基线更正为：**同词 `连带供裁量|matrix_row5|欠宽|:5 行|post_read_error` 检索 PENDING 0 命中、GOAL 1 命中（:9173「另 12 项覆盖：`src_missing`、`post_read_error`…」为历史测试覆盖枚举，与本裁决登记无关）**——本轮实跑 `grep -n … 两台账` EXIT=0 复现；草案 :168「均 0 命中」**表述不实，收回更正**（耦合件 §4.4-4 原记录准确）。补登致两台账指纹变化 → 重签件 :40（PENDING 行）/ :41（GOAL 行，原文完整在盘）同入换版登记（执行主体 = 重签件签发侧）。

### 5.3 裁决排序的稳健性论证（备案）

A/B 排序在两种候选契约读法下不变（§5.1），故「消费方契约未证」不构成 A/B 不可裁的理由；它只构成 (i) 关闭断言必须分层（已落实 §4.3）、(ii) B′ 是否立项不可预裁（列补证项）、(iii) 全关闭声明不得在补证前作出（已落实）。若后续证据显示消费方严格按耦合件 :67 合取键实现匹配器且拒绝注记路由，则 B 的文本层处方价值仍在（文档与设计 N1 对齐、镜像同步、人类读者不再被误导），但 W2/O1′ 的机器层残留将升级为必须立项 B′ 或 C 的问题——该情形的触发与代价见 §6 分阶段条件 ④。

### 5.4 反对意见逐条处置（复核回件 verdict = refuted，如实记；本稿整体 unconfirmed）

被核对象（上轮草案裁决书）本轮实算指纹：
被核对象 SHA256 = a7211b32b1f8b06e9ec34da06257ab9e86b7d0259d9ef8d9d3697a8d79096935，字节数 = 25984
（与复核回件绑定行同值，本轮 `python -I -X utf8 -c` + hashlib 独立实算复核。）

| # | 反对意见主张 | 处置 | 落实位置 |
|:--|:--|:--|:--|
| 1 | 必答一：B 未证明新文本优先级能被原验收方式消费；「匹配键 = preState+condition 前件」（耦合件 :67）下 ：5 注记不能改路由；反例 absent_confirmed × read_error × exists=True 严格键仍落 ：6（NFA/high）；T5 不执行 condition 匹配（`_review_probe_r3.py:434/:457/:460`）；上轮探针 after-B 硬编码、A6 三元冒名四元组 | **采纳（核心事实全部成立）**；其「故须暂缓 A/B 取舍」的结论**部分驳回**（排序稳健性，§5.3） | §4.3 分层表；§2.3 探针方法修正；探针 M2/M2b 复现反例（strict claimant=[6]、:5 eligible=False）；§6 补证项 1 |
| 2 | 必答二：V2:120 五列字面判断正确，但「无 condition 列」不能证明验收契约不变 | **采纳** | §4.2（本稿不再由 V2:120 反推契约不变） |
| 3 | 必答三：snap.error 与 post.read_error 是两个错误源、两个出口，可同现；W2 是真实文档优先级缺口；候选运行时已正确执行 post 错误优先 | **采纳** | §2.4 W2 行（「两个错误源、两个出口」措辞照录）；探针 M3/M3b |
| 4 | 必答四：O1 路径结构可达（:4598-4601/:4468/:6623/:6636-6649/:6167-6168/:4769/:4772/:4786）；不得把矩阵字面误配说成运行时输出 | **采纳**（结构链本轮实读复核成立） | §2.2/§2.4（警句照录） |
| 5 | 必答五：六处处方原文逐字全部与现盘一致 | **采纳（确认）** | 本轮 V1 探针独立复现 6/6_MATCH |
| 6 | 必答六：未发现既成事实越权断言；草案 :65 关闭断言属方案语境预期断言但证据不足 | **采纳（确认 + 降级落实）** | §4.3 关闭声明分层改写 |
| 7(a) | 登记 7 漏重签件 :35（V2 自身哈希）与 V2:110（矩阵短指纹） | **采纳** | 登记 7.5/7.8；本轮 grep 另发现 V2:66/:67 两处同类漏项（本稿新增发现，7.3/7.4）；「不得使用模拟中间值」吸收 |
| 7(b) | 草案 :168「两台账均 0 命中」不实（GOAL:9173 有一处无关命中） | **采纳** | 登记 8 检索措辞更正，本轮 grep 自跑复现 |
| 8(a) | 草案标题改「待补证、暂缓 A/B 取舍」 | **部分驳回**：标题改为「采 B（文本层处方）+ unconfirmed + 补证项」，不暂缓排序（§5.3）；关闭措辞降级部分**采纳** | §5.1/§4.3 |
| 8(b) | :67「不引入新问题」改「匹配契约尚未闭合」；:65 W1/W2/O1「关」改「仅文本层拟关闭」；:71 T5 表述修正 | **采纳** | §4.3/§4.2（同义落实） |
| 8(c) | 换版须同步 V2:110 短指纹 + V2 定稿后实算完整指纹更新重签件 :35；是否需内容批准未验 | **采纳** | 登记 7.5/7.8 + 未验登记 |
| 8(d) | 台账检索措辞更正 | **采纳** | 登记 8 |

### 5.5 「确认不用改」清单（逐处给依据；均为本轮实读/实跑证据）

1. **V2:120 及 V2:117-130 全表**——五列、无 condition 列（V2:114-116 实读）；B 不改 preState 字段 → 14 行字面全部仍真。**但契约层面的影响不得视为零**（§4.2），列入补证项而非改动项。
2. **候选 `qc151_trip.candidate_lf.py`**——零改动。实码按设计实现（B2B_DESIGN:310-311 与候选 :4642 同文；pf2:171）；动候选即击穿重签件 :157 条件 5（范围不变）并触发全量重签。
3. **重签件 §3 表（:60-77）与 V2 §4.2 表内容**——(verdict,confidence) 值零变化（探针网格同值）→ :154 条件 2 保持；只做登记 7 指纹换版。
4. **B2B_DESIGN:163 八类对账**——按类别计数、不引 condition 文本、行序不变。
5. **STATE_MATRIX.json:3 行**——O2 运行期不可达（make_pre :4589-4610 三路必覆写；`_r5v_probe_out.txt:113` P4 复现）→ 不新增行，登记即可。
6. **STATE_MATRIX.json:6 行**——O1′ 的文本层收容由改 2 的 :5 注记承担（注记点名「先于 :4666 absent_confirmed」+ 优先句）；不改 :6 本身。严格键层残留已如实登记（§4.3）；可选加 carve-out 句属批准人裁量、非必需。
7. **STATE_MATRIX.json:13 行**——W3 仅 fixture 域（实流不可达 :4607）→ 不动，登记即可。
8. **耦合件 `MATRIX_ROW5_COUPLING.md` 及 row5 域全部件**——本轮绝对只读、零改动；其 :67 匹配键纪律的修订属 B′ 补证项，**本稿不开列对它的处方**，若立项须另走任务书。
9. **四件非绑定陈旧副本**（`_draft_semantics.md:146`、`B2B_PREAUDIT.md:138`、`B_EXECUTION_SPEC.md:102`、`_n4_SPEC_N4_B2B_MATRIX.md:89`）——均不在 V2:45-46 绑定表、非重签件 :153 指纹对象（耦合件 §4.4-2 本轮转引复核）→ 不动（可选随批批注「措辞已陈旧」）。
10. **母本 `out/re_work/.../qc151_trip.py`**——绝对不动。
11. **V2/重签件其余行**（V2:42-44/:47-58/:63-65/:68-70、重签件 §2 表 1-3/7-10 行、追加绑定件表 :47-50）——本轮 grep 证实不含乙矩阵/乙设计指纹、不受本裁决改动影响 → 不动。

## 6 结论

**裁决理由**：三处缺陷（W1/W2/O1，含 O1′ 高虚标）现盘全部成立且均为矩阵/文档层、运行期零缺陷（§2.4）；A 只能文本层关 W1 且留 W2 活性误配 + O1′ high 虚标 + 两孤儿（§3）；B 以 4-6 行、同一文件域、同一批准主体、同一级联换版获得对 A 的严格覆盖（§4.1/§4.4），且排序对消费方契约未知稳健（§5.3）——故**采 B 完整形态为文本层处方**。B 的「全关闭」仅在「condition 注记承载路由 + :5 优先句被消费方采纳」读法下成立（本稿探针 AFTER-B-LOOSE 81/0/0），在耦合件 :67 严格键纪律下 W2（:4 两格）与 O1′（:6 一格）**机器层仍开**、W1 8 格由误配转孤儿（AFTER-B-STRICT 3 误配 + 17 孤儿）——关闭声明据此分层，本稿不得也不作「B 已全关闭」的断言。

**分阶段与补证触发条件**：
1. 若批准人今日只批 :2 一行 → A 可先行作退路，**必须**同步 :148 镜像并台账登记 W2/O1′/O3 残留；补做 B 的触发条件 = ①验收口径升级为全格枚举、②真机实流出现 pre≠present 的 read_error 格、③N-5 前签发侧要求矩阵全格可配。
2. **B′（匹配键纪律修订 / match_priority 字段）立项触发条件** = ④消费方匹配契约实证为严格合取键且拒绝注记路由（即本稿探针 AFTER-B-STRICT 口径被采纳为验收口径）。在此之前 B′ 不立项、不硬选。
3. 施行顺序（若获批）：改 1-6 → 实算 2 件新指纹 → 登记 7.1-7.5 → 实算 V2 新指纹 → 登记 7.6-7.9 → 登记 8 → 实算台账新指纹 → 更新重签件 :40/:41 → N-5 集成时对应用后副本重跑 T1-T5（V2:187）。

**未验项（如实登记，不补造）**：
1. **T1/T2/T5 门禁本轮与各前轮均未跑**（V2:180-184 自记「本轮未跑」；R3:42 为历史转引）；本稿探针为受限 AST 求值 + 手工编码 claimant 覆盖谓词，**不能冒称正式门禁通过**。
2. **消费方匹配契约未证**：现役无按 condition 文本做行匹配的程序；「注记路由 + 优先句」读法是否被未来验收采用 = 未验（本稿探针双口径即为此留证）。
3. **V2 内容同步（:110 与 :66/:67）是否需 V2 来源会话批准** = 未验（pf2:231 先例边界；草案断言已收回，见登记 7）。
4. **O1′ 真机实流未复现**（零真机约束）——结构可达已证（静态实读），实际文件系统故障形态未验。
5. 候选 412,759 字节仅实读 :4578-4804 与 :6612-6653 区间 + AST 顶层扫描，未逐行通读全文。
6. B2B_DESIGN §2 表 ↔ JSON 一致性为人工逐行对照 + 探针逐字复印，未做程序化全表 diff（沿登耦合件 §5.5-6）。
7. 本轮一处命令纪律偏差：对写域内自产探针脚本的一次文本修补使用了 `python - <<EOF` heredoc 方式（未走 `python -I -X utf8 + 脚本绝对路径` 形态）；该操作只写本写域自有脚本、未读任何被核件，随后所有探针运行均以合规形态执行——如实登记，不掩饰。

**不施行声明**：本稿未改任何被核件——§2.1 十一件 hashlib 实算与编排方基线逐字节一致（11/11 MATCH）；新增文件仅三件、全部落唯一写域 `lead/matrix_ab_ruling_20261109/`：`_rv2_probe_20261109.py`、`_rv2_probe_20261109_out.txt`、本件。零真机、零采样代码（探针 = 只读 + ast.parse + 受限表达式求值 + 纯内存字典；无 hook/MiniDump/SuspendThread/StackWalk/注入/动态内存解析）；未 commit、未 push。本稿为裁决与处方，不含既成事实改动断言；整体状态 **unconfirmed**（复核回件 verdict=refuted），须再复核/签发侧确认。
