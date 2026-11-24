# STRICT_EXPOSURE — STATE_MATRIX.json 两口径（STRICT/LOOSE）暴露面评估交付件

- 撰写：STRICT 口径暴露面评估员（动态工作流子代理），2026-11-09。
- 性质：**只评估、不改件**。被核件零改动（§0 十一件指纹与编排方基线逐字节一致即证）；唯一写域 = `lead/strict_exposure_20261109/`（本轮新增仅 `_se_fp.py`、`_se_fp_out.txt`、`_se_enum.py`、`_se_enum_out.txt`、本件）。零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 注入 / 动态内存解析）；未 commit、未 push。不判该不该改矩阵；§5(d) 为应任务书要求的**处方描述，未实施**。

## 0 指纹与绑定行（本轮 `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\strict_exposure_20261109\_se_fp.py` 实算，11/11 MATCH，输出 `_se_fp_out.txt`）

被核对象 SHA256 = 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016，字节数 = 3558
被核对象 SHA256 = 565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf，字节数 = 66735
被核对象 SHA256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2，字节数 = 412759
被核对象 SHA256 = 7dca469ea29d2874217211944102fb7feac9dc0d398ab08543123be8cd1ff4e7，字节数 = 23488
被核对象 SHA256 = cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6，字节数 = 27825
被核对象 SHA256 = 7a8a4198bdfff6aac5f0794f46432d446e592308ad27b819701e50397ca3e27e，字节数 = 18180
被核对象 SHA256 = 0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31，字节数 = 36851
被核对象 SHA256 = 6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8，字节数 = 29818
被核对象 SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

（第 1 行 = 被核乙矩阵 `lead/b2b_design_20261106/STATE_MATRIX.json`；第 3 行 = 被核实码 `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py`——两者为本评估的核心对象。其余顺序：乙设计 / O1′ 专查件 / 可达性报告 / 其探针输出 / A/B 裁决件 / 矩阵连带评估件 / 母本 / PENDING 台账 / GOAL 台账。）

## 1 第一步：两口径定义复现（逐字摘录）

**(a) STRICT**。匹配键纪律逐字（`lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md:67`，本轮 Read 实读）：「匹配键 = `preState` 字段 + condition 前件。判定列依据 = §3.1 码序 + §4.1 两轮 72 格实跑。」口径定义逐字（`lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md:42`，本轮 Read 实读）：「(i) **STRICT** = 耦合件 `MATRIX_ROW5_COUPLING.md:67`『匹配键 = preState 字段 + condition 前件』合取纪律（row5 探针 `:118` 的 cannot-claim 规则同源）」。即：一行声称一格，当且仅当（格的 preState 归一态 == 行 preState 字段）∧（格满足行 condition 前件）。

**(b) LOOSE**。逐字（`RULING_MATRIX_AB.md:42`）：「(ii) **LOOSE** = condition 文本承载路由、preState 列为登记示例态（草案 B 方案隐含读法）」。即：行是否声称一格由 condition 语义决定，preState 字段不作硬键。本轮复现时的两个必要编码选择（已写进探针注释，`_se_enum.py:171-231`）：① `:5` 行 condition「跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口」无 pre 限定 ⇒ LOOSE 下对**任意 pre** 的 read_error 格开放（`STATE_MATRIX.json:6` 行原文实读）；② `:2` 行对显式 unknown pre 的覆盖来自宽 preState 键读法——依据 = 耦合件 `:112`「宽 preState 键读法下 :2/:3 兜住且标签恰同」。若 ② 不采，LOOSE 会出现 6 格孤儿，与裁决基线 ORPHAN=0 矛盾，故 ② 是复现 67/14/0 的必要读法。

**(c) 两口径对同一输入的归属会不同**——实例（本轮探针 `_se_enum_out.txt:139-140` 实跑输出）：输入 `absent_confirmed × read_error·exists=True`（O1′ 格）：STRICT 下 claimant = **仅 :6**（:5 的 preState=present 合取不上）⇒ 矩阵归属 `new_first_appearance/high`，与实码 `post_read_error/none` 误配且**同格无任何正确行对冲**；LOOSE 下 claimants = **{:5, :6}** ⇒ :5 给出与实码一致的 `post_read_error/none`，冲突在文本层自明。第二例：`absent_confirmed × read_error·exists=None`（`_se_enum_out.txt:139`）：STRICT 下 **无行（孤儿）**；LOOSE 下 claimant = {:5} ⇒ `post_read_error/none`（正确）。

## 2 第二步：独立重算（不采信上一轮 60/12/9 与 67/14/0）

**(a) 网格**：9 类 pre × 9 类 post = 81 格（与耦合件 §4.1「9 类 pre × 9 类 post」同基）。pre 九类：未采集四变体（None / {} / 缺 state / 脏值）、显式 unknown、absent_confirmed、present 带 sha、present 缺 sha、error；post 九类：read_error·exists=None、read_error·exists=True、跑后无件、在场·缺 post.sha、在场·sha 异、在场·sha 同×{mt 同 / mt 升 / mt 降 / mt 缺}。**域的出处**：make_pre 输出域 = {absent_confirmed, present（必含非空 sha）, error}，**不含显式 unknown、不含 present 缺 sha**（候选 :4589-4613 实读：初值 unknown :4589 三路必覆写 :4599/:4603/:4610，在场必算 sha :4607；矩阵可达性报告 §2.2(a)、out:153/out:220-221 转引实跑）；copy_post 输出域四形态 = 无件（:4756-4764）/ 全观测（:4766-4769，sha+mt 必置）/ read_error·exists=None（:4766-4767 读炸）/ read_error·exists=True（:4769 先置 True→:4772 写炸→:4786 只增 read_error 键）；缺 post.sha 与 mt 缺仅在 fixture 域可构。pre=None 为调用侧实流值（唯一两写点 :6528/:6623，字段级改写点为空——矩阵可达性报告 §2.2 调用链）。显式 unknown / {} / 缺 state / 脏值 / present 缺 sha **实流不可产**，入网格只为矩阵 14 行全覆盖（与上轮同基）。

**(b/c) 实码路由**：本轮**不采信上轮的受限 AST 求值，也不用硬编码**——用 importlib `spec_from_file_location` 静态装载候选真模块、直调真 `classify_except_freshness` 跑全 81 格。命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\strict_exposure_20261109\_se_enum.py > …\_se_enum_out.txt`（EXIT=0）。装载安全：本轮自有顶层 AST 扫描（`_se_enum_out.txt:5-7`：tree.body 直接顶层 Call = 0 处，`__main__` 守卫 :7532）+ 实跑 import 成功。**交叉核对**：81 格实码 (verdict, confidence, is_new) 与耦合件 §4.1a 全格表逐格比对 = **ALL_PASS（0 mismatch / 81）**（`_se_enum_out.txt:11-12`）——我的 fixture 与前两轮实跑证据完全一致。

**(d) 计数**（claimant 谓词 = 本轮按 14 行 condition 原文独立手编；裁决规则 = 无 claimant ⇒ ORPHAN，全部 claimant 三元（verdict/conf/usable；JSON 无 is_new 字段）与实码一致 ⇒ OK，否则 MISLABEL——与上轮同基可比）：

| 口径 | OK | MISLABEL | ORPHAN | 出处（本轮实跑输出行） |
|:--|--:|--:|--:|:--|
| **STRICT**（preState ∧ 前件合取） | **60** | **12** | **9** | `_se_enum_out.txt:14` |
| **LOOSE**（condition 承载路由 / preState=示例态） | **67** | **14** | **0** | `_se_enum_out.txt:36` |

**与上一轮 A/B 裁决基线（STRICT 60/12/9、LOOSE 67/14/0，`RULING_MATRIX_AB.md:43`）完全一致**——但本轮为独立实现（真模块直调 + 独立手编谓词），非复读。

**敏感性变体**（裁决规则换为 first-match-wins，`_se_enum_out.txt:51-53`）：STRICT = OK 61 / MISLABEL 11 / ORPHAN 9（唯一变化 = present缺sha × re_true 的 :5/:13 双 claimant 改由 :5 先赢，W3 消失）；LOOSE = OK 69 / MISLABEL 12 / ORPHAN 0（:5 先序压掉 :6/:13 的坏 claimant）。孤儿数对编码选择稳健（STRICT 恒 9）。

## 3 第三步：逐格分类（两栏分开，不合并）

### 3.1 STRICT 口径：21 格暴露 = 「可达且会造成误读」6 格 + 「不可达但文本仍误导」15 格

**栏一：可达且会造成误读（6 格，全部 actual=post_read_error/none）**

| 格（pre × post） | STRICT 归属（坏行） | 实码 | 可达性依据 | 误读内容 |
|:--|:--|:--|:--|:--|
| none × re_none | :2 声称 unknown/none（W1） | post_read_error/none | **实跑**：matrix_reach §3.1 R:153-154（pre=None × 读锁 → PRE）；触发链 §4.2-3 | 「跑后证据复制失败」被读成「跑前快照未采集」——故障归因错位 |
| none × re_true | :2（W1） | post_read_error/none | **结构可达未单跑**（:4786 对任意 pre 生效 + :4769→:4772 写炸型已实产于 absent pre：C2 out:193-197、O1′ B1/B2/B4/A′-1/A′-2） | 同上 |
| error × re_none | :4 声称 error_pre_snapshot（W2） | post_read_error/none | **实跑**：matrix_reach out:179（error × read_error(exists=None) → PRE） | 「跑后复制失败」被读成「跑前采集失败」——排障方向错位（W2） |
| error × re_true | :4（W2） | post_read_error/none | **结构可达未单跑**（两半机制正交：snap.error 置 :4611、read_error 置 :4786） | 同上 |
| absent × re_true | :6 声称 **new_first_appearance/high**（O1′） | post_read_error/none | **实跑**：matrix_reach C2 out:193-197 + O1′ 专查 §3.1 B1/B2/B4、§3.2 A′-1/A′-2（五种真实 write_bytes 失败，traceback 逐帧绑定候选 :4772） | **环境故障被虚报成「本趟新出现·高置信」**——三处缺陷中唯一虚报置信格 |
| absent × re_none | **无行（孤儿，O1 主子格）** | post_read_error/none | **实跑**：matrix_reach C1 out:187-191 | 严格键匹配器对该格「不答」；若消费方把无行当通过即静默漏报 |

（W1 家族的口径差如实登记：矩阵可达性报告 §4.1 把 W1 可达子集记为「(pre=None × read_error) 单格」；在 81 格网格里它是 none × {re_none, re_true} 两格——同一触发链的两种 read_error 形态。）

**栏二：不可达但文本仍误导（15 格 = 纯文本债）**

| 格族 | 格数 | STRICT 归属 | 不可达控制流依据（均为 matrix_reach 实证，本轮转引其文件与行） |
|:--|--:|:--|:--|
| empty / missing / dirty × re 两型 | 6 | :2 误盖 unknown（W1 残余） | 实流 pre 仅 None / make_pre 三态（§2.2 调用链）；{}/缺state/脏值 dict **无第三写点可注入**（§3.1①） |
| present缺sha × re_true | 1 | :13 误盖 error_pre_snapshot（W3；:5 同格正确 claimant 并存） | make_pre 在场线性必经 :4607 sha256_file，算炸⇒整体 error；「present 且缺 sha」不在输出域（§3.5，out:220-221/R:23） |
| 显式unknown × re 两型 | 2 | 无行（孤儿，W1′） | 显式 unknown 不在 make_pre 输出域（§3.4 三重证明：AST 路径枚举 0 条保持 unknown / 运行期 sweep out:153 / 传参链封闭） |
| 显式unknown × 在场六型 | 6 | 无行（孤儿，O2） | 同上（§3.4 判「不可达，实证成立」） |

### 3.2 LOOSE 口径：14 格暴露 = 「可达且会造成误读」5 格 + 「不可达但文本仍误导」9 格

- **可达-实跑 3 格**：none × re_none、absent × re_true、error × re_none（坏 claimant 分别 = :2/:6/:4；三格同格均有 :5 正确 claimant 并存，`_se_enum_out.txt:37/47/49`）。
- **可达-结构未单跑 2 格**：none × re_true、error × re_true。
- **不可达纯文本债 9 格**：empty/missing/dirty × re 两型（6）、显式unknown × re 两型（2，LOOSE 下被 :2 宽键接住成误配——STRICT 下它们是孤儿）、present缺sha × re_true（1，W3）。
- LOOSE 无孤儿（ORPHAN=0）：STRICT 的 9 格孤儿中，显式unknown × 在场六型被 :2 宽键**正确**接住（unknown=实码，转 OK），absent × re_none 被 :5 **正确**接住，显式unknown × re 两型转为误配。

## 4 第四步：误导读数的实际后果（对 6 个可达格）

**(a) 谁会读**：① 人类审计者——按矩阵行文本解读账本 F 字段；② 严格键匹配器——耦合件 :67 合取键口径的验收器（STRICT 口径即为此类消费方而设）；③ 自动化验收——现役 T5 只做 14 组 fixture 四元组断言、**不执行 condition 匹配**（裁决 :92，转引 `_review_probe_r3.py:434/:457-458/:460-462`），故今天没有活性机器消费方；但矩阵被定为「机器可读唯一口径」（V2:110，经裁决 :60/耦合件 :129 转引，V2 原文本轮未直接实读）——一旦 STRICT 验收落地即成为 ②。

**(b) 误读会导致什么动作**：O1′ 格——把环境级复制失败读成「本趟新出现·高置信」，最坏动作是当崩溃征兆上报/升级；W2 两格——把「跑后复制失败」归因成「跑前采集失败」，误导排障方向（去查 make_pre 而非 copy_post）；W1 两格——同类归因错位（读成「快照未采集」）；absent × re_none 孤儿格——严格匹配器「不答」，最坏动作是把「无答案」当「无异常」放行（裁决 :122 同判：不答优于错答，但仍是暴露）。触发现实性：全部为环境级故障（AV 瞬时锁/ACL/磁盘满/out_dir 异常），无 trip 自身逻辑路径，评级「近乎不可能/罕见」（matrix_reach §4.1，零真机下的推理评级，未实测）。

**(c) 兜底机制（每格都有，多层）**：
1. **运行期零错误输出**：read_error 是 classify 第一判定分支（候选 :4643-4646，注释 :4642「★ N1：错误独立出口，优先于一切状态折叠」），六格实码恒 (post_read_error, none, None, usable=False)——本轮 81 格实跑逐格确认；O1′ 专查 §3.1/3.2 五种真实失败 + 复核五组同值。
2. **usable_as_crash_evidence 恒 False**：候选 :4624-4626 初值 + :4628-4632 `_finish` 强制；「虚报 high」只存在于矩阵 :6 的**文本层声称**，运行期账本四元组被 conf=none + usable=False 双重兜住（O1′ 专查 §4.3-2）。
3. **同账本 ERROR 留痕自相矛盾**：copy 失败路径 ERROR×3（:4777-4785 freshness_copy_failed/stage/traceback）→ finalize_errors.txt（:4547-4553）→ error.txt（:4571-4577）——若有人按 :6 文本读成 high，账内 ERROR 行与之直接冲突、自明易察（O1′ 专查 §4.3-3）。
4. **无运行期消费分支**：候选不读矩阵（grep STATE_MATRIX = 0）、confidence 无分支消费（O1′ 专查 §4.3-1，转引实跑）；E/退出码判据独立于 F（候选 :217-220 门禁注释、:5985-5990 集合差，本轮实读 :217-220）。
5. **门禁层**：T2（unknown→high=0）与 T5（fixture 四元组断言，benign-post 已 match）不受 condition 文本影响（耦合件 :129）。

## 5 第五步：暴露面总评

**(a) STRICT**：总暴露 **21/81 格**（MISLABEL 12 + ORPHAN 9，26%）；其中**实流可达 6 格**（实跑 4 + 结构未单跑 2：误配 5 + 孤儿 1），**纯文本债 15 格**。可达误配里 5 格全为 error 族标签（conf=none/usable=False 兜底），唯一虚报置信格 = O1′（absent × re_true）。
**(b) LOOSE**：总暴露 **14/81 格**（MISLABEL 14 + ORPHAN 0，17%）；**实流可达 5 格**（实跑 3 + 结构未单跑 2），**纯文本债 9 格**；无孤儿。
**(c) 哪个口径更危险：STRICT**。理由：① 量大（21 vs 14）；② STRICT 的 12 个误配格**全部是单一错误 claimant、同格无正确行对冲**（`_se_enum_out.txt:15-26`：claimants=[2]/[4]/[6] 均单行），其中 O1′ 的 high 虚标无任何同格冲突提示，是最危险的静默虚高；LOOSE 下同格全部有 :5 正确 claimant 并存（claimants=[2,5]/[4,5]/[5,6]/[5,13]），冲突文本层自明。③ STRICT 另有 9 格孤儿（含 1 个可达格），在把「无行」当「通过」的自动化验收里等于静默放行；LOOSE 无孤儿。**反面向（如实）**：LOOSE 的安全性依赖两个未成文读法（宽 preState 键 + condition 注记路由），矩阵无 match-order/priority 字段（裁决 :92）——若 LOOSE 消费方改用 first-match 行序，W1/W2 的 10 格仍错（`_se_enum_out.txt:53`：FIRSTMATCH-LOOSE 69/12/0）；且「冲突自明」只对会复读全表的人类成立，机器匹配器未必报冲突。
**(d) 若验收一定要用 STRICT 口径，最小必要的文本修正（只描述，未实施）**：STRICT 合取键下 `:5` 的 preState=present 字段使其**无法**吸收非 present pre 的 read_error 格（B2B_DESIGN:142 四态值域契约，经耦合件 :132/:137 转引），故纯文本修正做不到「让 :5 接管」，只能做**前件收紧**：在 :2（已收）、:4、:6（:13 随批）的 condition **前件**内显式加「post.read_error 为空」类限定——效果是把 11 个可达+fixture 误配格从「错答」转「不答」（W3 一格因 :5 独占转 OK），STRICT 变为约 OK 61 / MISLABEL 0 / ORPHAN 20 的形态；**20 个孤儿在 STRICT 口径下无法用文本消除**——消除需改匹配键纪律或加 match_priority 字段（裁决 :236 的 B′ 补证项）或拆行（裁决 :106 不采的选项 C）。镜像与级联义务同裁决 §5.2（B2B_DESIGN:148/:150/:151、V2/重签件指纹换版登记）。**本件只描述，不构成改动建议的采纳。**

## 6 未验项（如实登记，不补造）

1. 真机端到端实流未跑（零真机纪律）；可达评级沿用 matrix_reach §4.1/O1′ §4.2 的「实跑 + 推理」结论，未独立量化概率。
2. none × re_true、error × re_true 两格为**结构可达、组合未单跑**（无 pre=None/pre=error 与 write_bytes 失败的 copy_post 组合实跑；机制两半各有实跑证据）。
3. V2:110、重签件、修正提案（pf2）原文未直接实读，相关引用均为经裁决件/耦合件的**转引**，已逐处标注。
4. claimant 覆盖谓词为手工编码（自然语言 condition 无法完全机器化，裁决 :42 同认）；LOOSE 的 :2 宽键读法（含显式 unknown）是复现 ORPHAN=0 的必要编码选择——若不采，LOOSE 将出现 6 格孤儿，与基线矛盾。
5. T1/T2/T5 门禁未跑（沿裁决 :240）。
6. 本轮 F1 顶层 Call 扫描口径 = tree.body 直接子节点（= 0 处），与 matrix_reach 复核轮「11 处顶层 Call 全良性」口径不同（其含 `__main__` 守卫内调用）；import 安全以本轮实跑装载成功 + 81/81 交叉核对为准。
