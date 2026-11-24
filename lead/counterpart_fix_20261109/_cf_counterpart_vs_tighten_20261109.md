# _cf_counterpart_vs_tighten_20261109 —— 「收紧 condition」vs「补对照行」双修法对比设计件

- 撰写：对照补齐设计员·GLM（动态工作流子代理），2026-11-09。
- 性质：**只设计与对比，不改任何文件、不施行**。零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 注入 / 动态内存解析；探针 = 标准库 importlib 静态装载候选真模块 + 直调纯函数 `classify_except_freshness`，沿 `_se_enum.py:60-64` 既证安全先例）；绝对只读域（`lead/b2b_design_20261106/`、`lead/strict_exposure_20261109/`、`lead/text_fix_unified_20261109/`、`lead/matrix_ab_ruling_20261109/`、`lead/matrix_row5_20261109/`、`lead/b2b_candidate_lf_20261107/`、母本、两件台账）零写入；唯一写域 = `lead/counterpart_fix_20261109/`；不 commit、不 push。Python 一律 `python -I -X utf8` + 绝对路径；指纹用 hashlib。
- ★ 术语纪律（全篇执行）：**收紧 condition** = 修改既有行的 condition 前件，让错答格不再被该行声称（行数不变，错答→不答/转由正确行接管）；**补对照行** = 在矩阵追加新行，让无行/错答格旁边多出一个正确答案（行数 14→17/18）。两者是不同修法，本文逐处标注归属。

---

## 0 实跑命令与指纹（全部本轮实跑）

本轮实跑命令（cwd=`D:\Project\ra2-campaign-forge`，EXIT 均 0）：
1. `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\counterpart_fix_20261109\_cf_fp_check.py`——15 件 hashlib 指纹复核，**15/15 MATCH**（首跑 12/12，终跑含追加 3 件 15/15，两次一致 = 全程零漂移）。
2. `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\counterpart_fix_20261109\_cf_enum_counterpart.py > …\_cf_enum_out.txt`——81 格六情景 × 多读法仿真。输出 `_cf_enum_out.txt`（38,331 B）。

仿真内置自检（`_cf_enum_out.txt:4/:8/:10/:32/:48/:70`）：
- F0 指纹 candidate `ca23c116…76d2`/412,759 + matrix `1d4ccc93…e016`/3,558 均 MATCH；
- F3 与耦合件 §4.1a 全格表交叉核对 **XCHECK ALL_PASS（0 mismatch / 81）**；
- M1 基线四组数字与在档枚举件逐一相符：STRICT **60/12/9**（=`_se_enum_out.txt:14`）、LOOSE **67/14/0**（=:36）、first-match STRICT **61/11/9**（=:52）、first-match LOOSE **69/12/0**（=:53）。

绑定行（本轮 `_cf_fp_check.py` 实跑，15/15 MATCH；顺序：乙矩阵 / 乙设计 / 暴露面交付件 / 其枚举输出 / 统一清单 / A-B 裁决件 / 矩阵连带评估件 / 候选 LF / V2 定版件 / 母本 / 台账一 / 台账二 / 重签件 / R3 复审 / 裁决探针输出）：

被核对象 SHA256 = 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016，字节数 = 3558
被核对象 SHA256 = 565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf，字节数 = 66735
被核对象 SHA256 = 3a4b1bb7cf7f0bd501b3e99d575c4907dd0e17f5557dd0b8826e5fb07fe2bdc8，字节数 = 23798
被核对象 SHA256 = 35d27095d697d167892b41f452c9fc3cccb85ef528ee8695266c95220ce023c2，字节数 = 17870
被核对象 SHA256 = 441b073a39a2ac195d90d43e3ba85f3c2202d5fafce31bec9c96e000a01e0923，字节数 = 25095
被核对象 SHA256 = 0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31，字节数 = 36851
被核对象 SHA256 = 6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8，字节数 = 29818
被核对象 SHA256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2，字节数 = 412759
被核对象 SHA256 = c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801，字节数 = 28897
被核对象 SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518
被核对象 SHA256 = 1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b，字节数 = 23129
被核对象 SHA256 = 96071dd9d58e30a54966a2a1e16f4af918c2f8dd5825363510e8ced8bc6a8fea，字节数 = 24661
被核对象 SHA256 = d78ada307dfad13f18f8d1e89f1eca771d7a4fc660663ef8c4c27c1680510ec6，字节数 = 7346

（第 15 件 = `lead/matrix_ab_ruling_20261109/_rv2_probe_20261109_out.txt`，哈希为本轮实算、字节数 7,346；其内容本轮 Read 实读 ：1-94。）读件而未自算指纹的还有：`_se_enum.py`、`_mr_probe1_out.txt`（转引）、`B2B_DESIGN.md:305-314` 区间之外的正文——相关引用均已标注出处行号。

---

## 1 第一步：12 个误配格与 9 个孤儿格逐格身份

数据源：本轮独立重算（`_cf_enum_out.txt:10-31`，与 `_se_enum_out.txt:14-35` 逐格一致）；可达性标注沿 `_se_enum.py:291-306` REACH 表（本轮实读）与 STRICT_EXPOSURE.md §4.1（:67-72 的实跑触发链引证为**转引**，一手探针 `_mr_probe1_out.txt` 本轮未开）。实码 PRE = `post_read_error/none/false`（usable 恒 False，候选 :4624-4632，转引复核轮）。

### 1(a) 12 个 MISLABEL 格（STRICT 合取键口径，裁决规则 = 全部 claimant 三元须与实码一致）

| # | 格（pre × post） | 错误 claimant | 该行声称 | 实码 | 同格对冲 | 可达性 |
|--:|:--|:--|:--|:--|:--|:--|
| 1 | none × re_none | **:2** | unknown/none/false | PRE | **无**（claimants=[2]） | 可达-实跑（STRICT_EXPOSURE:67） |
| 2 | none × re_true | **:2** | unknown/none/false | PRE | **无** | 可达-结构未单跑（:68） |
| 3 | empty × re_none | **:2** | unknown/none/false | PRE | **无** | 不可达-文本债（:78） |
| 4 | empty × re_true | **:2** | unknown/none/false | PRE | **无** | 不可达 |
| 5 | missing × re_none | **:2** | unknown/none/false | PRE | **无** | 不可达 |
| 6 | missing × re_true | **:2** | unknown/none/false | PRE | **无** | 不可达 |
| 7 | dirty × re_none | **:2** | unknown/none/false | PRE | **无** | 不可达 |
| 8 | dirty × re_true | **:2** | unknown/none/false | PRE | **无** | 不可达 |
| 9 | absent × re_true（O1′） | **:6** | **new_first_appearance/high**/false（唯一虚报置信格） | PRE | **无**（STRICT 下 claimants=[6]） | 可达-实跑（:71，C2 写侧失败） |
| 10 | present_nosh × re_true（W3） | **:13** | error_pre_snapshot/none/false | PRE | **有**：:5 同格正确行并存（claimants=[5,13]，`_cf_enum_out.txt:20`） | 不可达（make_pre 在场必算 sha :4607，耦合件 §4.1b） |
| 11 | error × re_none（W2） | **:4** | error_pre_snapshot/none/false | PRE | **无**（claimants=[4]） | 可达-实跑（:69） |
| 12 | error × re_true（W2） | **:4** | error_pre_snapshot/none/false | PRE | **无** | 可达-结构未单跑（:70） |

对冲结构结论：**11/12 单一错误 claimant、同格无正确行**（:2×8、:4×2、:6×1）；**1/12（W3）有对冲**（:5 正确行并存）。与 STRICT_EXPOSURE.md §5.1 瑕疵 1 的改述「11/12 无对冲、1/12 有对冲」一致（该件已纠正其评估件原表述「全部无对冲」）。LOOSE 口径下 14 个误配格（上 12 格 + expl_unknown×re_* 2 格）的 claimants 全部含正确的 :5（[2,5]/[4,5]/[5,6]/[5,13]，`_cf_enum_out.txt:33-46`），冲突文本层自明。

### 1(b) 9 个 ORPHAN 格（无任何行声称）

| # | 格 | 实码 | 无行原因（本轮按 :2-:15 condition 原文核） | 可达性 |
|--:|:--|:--|:--|:--|
| 1 | expl_unknown × re_none | PRE | :2 strict 枚举仅 None/{}/缺state/脏值不含显式 unknown；:3 要「跑后无件」；:5 preState=present | 不可达（make_pre 初值三路必覆写，:4589→:4599/:4603/:4610） |
| 2 | expl_unknown × re_true | PRE | 同上 | 不可达 |
| 3 | expl_unknown × no_post_sha | unknown/none/false | 同上（:2 宽读可兜且标签恰同——耦合件 :112） | 不可达（O2 家族） |
| 4 | expl_unknown × sha_diff | unknown/none/false | 同上 | 不可达 |
| 5 | expl_unknown × mt_same | unknown/none/false | 同上 | 不可达 |
| 6 | expl_unknown × mt_up | unknown/none/false | 同上 | 不可达 |
| 7 | expl_unknown × mt_down | unknown/none/false | 同上 | 不可达 |
| 8 | expl_unknown × mt_missing | unknown/none/false | 同上 | 不可达 |
| 9 | absent × re_none（O1 主子格） | PRE | :5 要 present、:6 要「跑后在场（exists=True）」、:7 要「跑后无件」——exists=None 三者皆不满足（耦合件 §4.1b） | **可达-实跑**（STRICT_EXPOSURE:72，C1 读侧失败）——9 孤儿中唯一可达格 |

### 1(c) 可达性汇总

- **可达-实跑（4 格）**：none×re_none（M）、absent×re_true（M）、error×re_none（M）、absent×re_none（O）。
- **可达-结构未单跑（2 格）**：none×re_true（M）、error×re_true（M）。
- **不可达-文本债（15 格）**：其余全部（empty/missing/dirty×re_* 6 M、present_nosh×re_true 1 M、expl_unknown×8 2+6 O）。
- **可达 6 格 = 5 MISLABEL + 1 ORPHAN**（STRICT 口径；LOOSE 口径可达暴露 = 5 格，全部 MISLABEL——absent×re_none 在 LOOSE 下被 :5 正确接管，`_se_enum_out.txt:139` 同证）。

---

## 2 第二步：「收紧 condition」路线分析

情景编码（本轮独立实现，`_cf_enum_counterpart.py`）：收紧 = 在该行 condition 前件内加「post.read_error 为空」类限定。T4 = 纯收紧 :2/:4/:6/:13 四行（无分流句）；U2/U3/U4 = 统一清单 B 形态（U2=:2 收紧+内嵌分流句；U3=:5 追加码序注记+「匹配以本 condition 为准」优先句、preState 字段不动；U4=:4 加分流句、前件字面不变；:6/:13 不动）。

### 2(a) 收紧后该格变 OK 还是 ORPHAN？——逐格

| 被收紧行 | 直接受影响格 | 收紧后状态（STRICT） | 机理 |
|:--|:--|:--|:--|
| :2 | none/empty/missing/dirty × re_*（8 格，全为 MISLABEL） | **8 格全部 → ORPHAN**（`_cf_enum_out.txt:85-92`） | 其唯一 claimant 即 :2；收紧后无行。实码 post_read_error，而 :5 strict 键 preState=present 不吸收 unknown 归一态（裁决探针 M2b 同证：`_rv2_probe_20261109_out.txt:77`） |
| :4 | error × re_*（2 格，全为 MISLABEL） | **2 格 → ORPHAN**（T4 情景 :103-105） | 同理无行可配 |
| :6 | absent × re_true（1 格，MISLABEL） | **→ ORPHAN**（T4 :103） | 同理 |
| :13 | present_nosh × re_true（1 格，MISLABEL） | **→ OK**（`_cf_enum_out.txt` M4 表该格 T4 列=OK） | **唯一由错答变正确答案的格**：:13 退场后 :5 同格正确行独占接管（claimants=[5]，值恰为 PRE） |

### 2(b) 「错答换不答」算改善吗？

**方向正确、性质改善，但 STRICT 口径下暴露格数几乎不减。** 依据裁决 :59「把『错答』换成『不答 + 文字兜底』」与 :92「孤儿 = 『不答』，非『错答』，方向正确」：
- **错答的害处是主动给错标签**：W1/W2 把「跑后复制失败」归因为「跑前未采集/采集失败」（排障方向错位），O1′ 把环境级失败虚报为「本趟新出现·high」（唯一虚报置信格，最坏动作=当崩溃征兆上报，STRICT_EXPOSURE:71/:159）。不答的最坏动作只是「把无答案当无异常放行」——且有五层兜底（运行期恒 PRE/usable=False、ERROR×3 账本自明、候选不读矩阵、E 判据独立、T2/T5 不读 condition 文本；STRICT_EXPOSURE §5.2）。
- **量的账（STRICT）**：T4 后 21 暴露 → 20（MISLABEL 12→0、ORPHAN 9→20，`_cf_enum_out.txt:85`）；可达 6 格 6→6（全部变孤儿）。**与 STRICT_EXPOSURE §5.3 的预测「约 OK 61 / MISLABEL 0 / ORPHAN 20」逐数相符**（本轮独立复现）。
- **量的账（LOOSE）**：14→0（`_cf_enum_out.txt:106`，81/0/0）——收紧在 LOOSE 读法下才是量的全消，因为坏 claimant 被摘除后 :5（LOOSE 下 pre 任意态可配）接管。
- 结论：算改善（虚报与归因错位这两个「会咬人」的害处消失），但「暴露格数清零」的断言只能在 LOOSE/注记路由读法下作出，STRICT 键层 20 格孤儿仍在。

### 2(c) 统一清单 U2/U3/U4 的逐格前后对照（单因子拆分 + 合计，全部本轮实跑）

| 情景（行数均 14） | STRICT（OK/M/O） | LOOSE（OK/M/O） | 格级变化 |
|:--|:--|:--|:--|
| S0 基线 | 60/12/9 | 67/14/0 | — |
| **U2only**（:2 收紧） | 60/**4**/**17** | 77/**4**/0 | strict：8 格 MIS→ORP（UNC×re_*），0 格变 OK；loose：10 格 MIS→OK（8 UNC×re_* + 2 expl_unknown×re_*，经 :5 接管）；残留 4 M = absent×re_true、present_nosh×re_true、error×re_*×2 |
| **U3only**（:5 注记+优先句） | 61/**11**/9（suppressed=1） | 69/**12**/0（suppressed=2） | strict：仅 present_nosh×re_true 1 格 MIS→OK（:5 优先句压制 :13——**读法依赖**，不采优先句则不变）；loose：absent×re_true、present_nosh×re_true 2 格 MIS→OK（压制 :6/:13） |
| **U4only**（:4 分流句） | 60/**12**/9（**零格变化**） | 69/**12**/0 | strict：前件字面不变 → 机器层零效果（裁决探针 M3b 同证 `_rv2_probe_20261109_out.txt:81`）；loose：error×re_* 2 格 MIS→OK（分流句承载 read_error 子分支取值） |
| **U = U2+U3+U4** | **61/3/17**（suppressed=1） | **81/0/0**（suppressed=2） | 与裁决件独立探针 AFTER-B 两口径逐数相同（`_rv2_probe_20261109_out.txt:51/:72`：61/3/17 suppressed 1；81/0/0 suppressed 2）——本轮独立实现复现 |
| U_NP（U 但不采优先句） | 60/4/17 | 77/4/0 | 证明 U 的 strict「3 误配」依赖 :5 优先句被消费（W3 格），不采则 4 误配 |
| T4（纯收紧 :2/:4/:6/:13，无分流句） | **61/0/20** | **81/0/0** | 比 U 多杀 strict 层 3 个误配（W2×2、O1′×1 → 孤儿）、多 3 个孤儿；代价 = 无分流句兜底文本 |

21 格逐格前后全表见 `_cf_enum_out.txt:264-286`（M4 表：12 误配格 + 9 孤儿格 × S0/T4/U/P3/P4/PT 六情景）。要点摘录：present_nosh×re_true 在 T4/U 两列均 OK（T4 经 :13 收紧、U 经优先句压制）；expl_unknown×re_* 在 P3/P4 列转 OK（补行接住）；全部 12 误配格仅 PT 列全 OK。

---

## 3 第三步：「补对照行」路线分析

### 3(a) 需要补几行、每行长什么样（逐格）

补行归属判定先行：**12 个误配格中 11 格不能靠补行修复**——「全 claimant 一致」裁决规则下，坏 claimant（:2/:4/:6）仍在，追加正确行不摘除错误行（P3-strict 误配 12→12 实证，`_cf_enum_out.txt:129-141`；first-match 亦然，追加行在尾部不改变首行，64/11/6）。补行直接修复的是 **ORPHAN**（无行→有正确答案）；对误配格的作用是「加对冲」（让同格多一个正确答案，冲突自明）。逐格所需对照行：

| 目标格组 | 所需对照行（拟文，未实施） | 覆盖格数 | 修复什么 |
|:--|:--|:--|:--|
| none/empty/missing/dirty × re_*（8 M）+ expl_unknown × re_*（2 O） | **补A**（拟为矩阵第 16 行）：`{"state":"post_read_error","preState":"unknown","condition":"跑前快照未采集或显式 unknown（pre 归一 unknown）+ 跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口（★ N1 码序 read_error 出口先于 unknown 出口，候选 :4643 先于 :4648）","verdict":"post_read_error","confidence":"none","usableAsCrashEvidence":false}` | 10 格 | 修 2 孤儿；对 8 误配格加对冲（须配合 :2 收紧才变 OK） |
| absent × re_true（1 M，O1′）+ absent × re_none（1 O，O1 主子格） | **补B**（拟第 17 行）：`{"state":"post_read_error","preState":"absent_confirmed","condition":"跑前确认无件 + 跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口，不得判 new_first_appearance（read_error 出口先于 absent_confirmed 分支，候选 :4643 先于 :4666）","verdict":"post_read_error","confidence":"none","usableAsCrashEvidence":false}` | 2 格 | 修 1 孤儿（可达格）；对 O1′ 加对冲（须配合 :6 收紧才变 OK） |
| error × re_*（2 M，W2） | **补C**（拟第 18 行）：`{"state":"post_read_error","preState":"error","condition":"跑前采集抛异常（snap.error 非空）+ 跑后 read_error 非空 ⇒ post_read_error 优先（N1 先于 error_pre_snapshot 出口，候选 :4643 先于 :4652）","verdict":"post_read_error","confidence":"none","usableAsCrashEvidence":false}` | 2 格 | 对 2 误配格加对冲（须配合 :4 收紧才变 OK） |
| expl_unknown × 在场六型（6 O） | **补D**（可选，拟第 19 行）：`{"state":"unknown","preState":"unknown","condition":"pre.state 显式 unknown（未采集）+ 跑后任意非 read_error 状态 ⇒ unknown（未知不得默认等于不存在）","verdict":"unknown","confidence":"none","usableAsCrashEvidence":false}` | 6 格 | 修 6 孤儿（全部不可达文本债） |
| present_nosh × re_true（W3，1 M） | **不需要新行**——:5 已同格正确声称；修法 = 收紧 :13（T4 路线）或 :5 优先句压制（U3 路线），补行无效 | — | — |

值域核查：四行 state ∈ {post_read_error, unknown}（FRESHNESS_VERDICTS 9 值内）、preState ∈ {unknown, absent_confirmed, error}（B2B_DESIGN.md:142 四态值域内）——**不触发当年选项 C 被否理由中的「preState=any 违值域契约」那条**（耦合件 §4.3-C）；conf=none、usable=false 与三个落点实码一致。

### 3(b) 行数变化

**14→17**（补A/补B/补C 三行，`P3` 情景）或 **14→18**（加补D，`P4` 情景）。任务书预警的「14→15/17」落在 17 档。

### 3(c) 代价：击穿的内容级绑定（逐处，全部本轮实读原文）

收紧路线只触发**指纹换版登记**（值变更，非内容断言改写）；补对照行在指纹换版之外**额外击穿以下内容级断言**——每处为「断言重写 + 取证重做」，非改一个数字了事：

| # | 绑定处（本轮实读原文） | 击穿方式 | 后续义务 |
|--:|:--|:--|:--|
| 1 | `B2B_DESIGN.md:144`：「机器可读版为同目录 `STATE_MATRIX.json`（严格 JSON 数组，**14 项**，…）；下表与之逐行一致。」 | 「14 项」失真；镜像表 :146-161 须增 3-4 行 | 重写断言 + 镜像行增补 + 乙设计指纹换版（V2:45、重签件:33） |
| 2 | `B2B_DESIGN.md:163`：8 类逐条对账，按**行位**引用（「表中第 1–2 行」…「第 13 行」「第 14 行」） | 新行使行位引用语义漂移，且新行不在八类叙述内 | 对账重写 |
| 3 | `V2:110`：「…（`1d4ccc93…`/3,558 B）**14 数据行（:2-15**，本轮全文实读）为机器可读唯一口径。」 | 行数与行区间（:2-18）双失真 | 重写 + 短指纹/字节数（连带 V2:45-46/:66-67 登记行） |
| 4 | `V2 §4.2` 表 :114-130：14 行五列收录表（文件行 :2-:15） | 须增 3-4 行 = **V2 正文内容改动** → 按 pf2:231 先例（转引，裁决 §5.2 未验项 3 在案）需 V2 来源会话批准 | 内容批准 + V2 指纹换版（重签件:35） |
| 5 | `V2:184`：T5 门禁「**14 组 fixture** 按 STATE_MATRIX.json 逐行断言 …（R3:42 同法）14/14 match」 | fixture 组数与断言目标行数失配 | **T5 重规约**（17/18 组）+ 重跑（V2:180-184 自记本轮未跑） |
| 6 | 重签件 `:56`：§3 标题「矩阵**十四行**逐行比对（三方…）」+ §3 全表 | 标题与三方表行数失真 | 章节重写 + 重新取证 |
| 7 | 重签件 `:148`：五项必查之一「矩阵三方一致 **14/14**（逐行见 §3）」 | 必查口径失真 | 断言重写 + 新一轮逐行取证 |
| 8 | 重签件 `:34`（§2 第 5 行乙矩阵指纹）+ `:153` 条件 1「母本/候选/乙矩阵/V2/台账…任一漂移即失效」 | 指纹漂移 → 既有 YES 自动作废 | 换版重签（**收紧路线同样触发本条**——此条非补行独有） |
| 9 | 重签件 `:154` 条件 2「三方 (verdict,confidence) 不分叉」 | JSON 增行而 V2 §4.2 不同步即三方分叉 | 三表必须同批同步 |
| 10 | `R3:42`：「**14/14 逐行 match**：本人以 14 组 fixture 逐一 exec 实跑…」（历史实跑记录） | 历史记录不可回改，增行后不再描述新矩阵 | 只能新增一轮 17/18 行逐行取证，旧记录与新矩阵失配 |

与在案裁决的关系：耦合件 §4.3-C 与裁决 :106 已判「**C 不采**：14→15/17 行击穿至少六处内容级绑定（B2B_DESIGN:144『14 项』/:163 八类对账、V2:110『14 数据行』/:114/:184、重签件 §3:56/:148 五项必查 14/14），需 T5 重规约」——本轮逐一实读，**上述六处全部在盘、引文相符**；本表再补 3 处（重签件 :154 条件 2、R3:42 历史记录失配、pf2:231 先例下的 V2 内容批准）。裁决 :102 明示「C 不采」是裁决结论的一部分；**单方面补对照行 = 重开已裁事项**。

### 3(d) 「不增行」的替代：分流表述——两种形态，效果不同

- **形态一｜纯注记（不动前件）**：在某行 condition 里写「本行同时承接 X 与 Y；X 时 verdict=…，Y 时 verdict=…」（U3 的 :5 注记 + 优先句、U4 的 :4 分流句即此形态）。**STRICT 键层零机器效果**（U4only-strict 60/12/9 = 基线，U3only-strict 仅 1 格；本轮实证）；**LOOSE 层有效**（U4only-loose 69/12/0、U3only-loose 69/12/0）。强依赖「消费方按 condition 文本路由」——现役无任何程序按 condition 文本做行匹配（裁决 :92；T5 只断言 fixture 四元组，`_rv2_probe` 引 `_review_probe_r3.py:434/:457/:460`，转引）。
- **形态二｜收紧+分流句合一（U2 实态）**：前件加「跑后读取正常（post.read_error 为空）」+ 内嵌「post.read_error 非空时先落 post_read_error（…见 :5 行）」。strict 层错答消失（→孤儿），LOOSE 层全绿。这是统一清单与裁决 B 的实际形态——**分流表述不是收紧的替代品，而是收紧的配套文本**。
- **结构性不可能**：「不增行且 STRICT 键层每格都有正确答案」做不到——strict 匹配键 = `preState` 字段 ∧ condition 前件（耦合件 :67），preState 字段受 B2B_DESIGN:142 四态值域约束为单值，一行不能同时持 unknown/absent_confirmed/error 三键；verdict 字段亦单值、无法表达分支。这正是裁决 :106 判 C 不采、又把 B′（修订 :67 纪律或增 match_priority 字段）列为补证项而非处方的结构性原因（裁决 §6 触发条件 ④）。

---

## 4 第四步：两方案对比与决策表

全部数字来源 = `_cf_enum_out.txt` M2/M3（本轮实跑）；「收紧」列以 U（统一清单 B 形态）为主行、T4（纯收紧）为参照行。

| 维度 | 收紧 condition（U2/U3/U4+镜像，行数不变） | 补对照行（+3~4 行） | 分流表述（:5 注记+优先句 / :4 分流句） |
|:--|:--|:--|:--|
| STRICT 暴露格数变化 | 21→**20**（M 12→3、O 9→17；纯收紧 T4：M 12→0、O 9→20） | 21→**18**（P3：M 不减 12、O 9→6）/ 21→12（P4：O 9→0） | 单用：STRICT 21→**21**（机器层不动、文本层自明化）；与 U2 合并即 U |
| LOOSE 暴露格数变化 | 14→**0** | 14→**14**（误配一格不消，仅孤儿受益） | 14→**0**（需 U2 随批摘除坏 :2 claimant） |
| 是否引入新孤儿（STRICT） | **是**：+8~11 格（错答→不答） | **否**：孤儿 −3~−9 格 | 否 |
| 可达 6 格·STRICT 键层 | 6→**6**（3 MIS + 3 ORP；T4 则 6 ORP） | 6→**5**（仅 absent×re_none 孤儿→OK；5 个错答格原样） | 6→**6**（同 U）；LOOSE 读法 6→0 |
| 可达 6 格·LOOSE/注记路由读法 | 6→**0** | 6→5 | 6→**0** |
| 错答性质消除 | W1（2 可达格）文本层关闭；W2 文本层关闭（U4）；O1′ high 虚报**仅在 T4（:6 随批收紧）下消失**，U 下残留 | 错答格原样（对冲仅让冲突自明） | O1′/W2 的误读文本消除（LOOSE 读法） |
| 改动行数 | 3-6 行 × 2 文件（JSON :2/:4/:5 + 镜像 :148/:150/:151） | +3~4 行 × 1 文件（JSON）+ §3(c) 全链重写 | 1-2 行 × 2 文件（U3/U4 本体） |
| 是否增行 | **否**（14 行不动） | **是**（14→17/18） | 否 |
| 绑定击穿面 | 指纹换版登记 5 处（V2:45-46/:66-67/:110 值、重签件 :33-34/:153）；**内容级零击穿**；T5/§3/对账全不动 | 指纹换版 + **§3(c) 十处内容级击穿**（含 T5 重规约、V2 内容批准、R3 历史记录失配） | 同收紧（更小） |
| 对消费方契约的依赖 | STRICT 层不依赖；「全绿」断言依赖 LOOSE 读法（已分层登记，裁决 §4.3） | **不依赖**（新行是真实行键，两口径同效） | **强依赖**（现役无程序读 condition 文本；B′ 触发条件 ④ 未满足） |
| 可读性 | :2 交棒句 + :5 承接句语义闭合（统一清单 §2-a）；孤儿格需读分流句才知道落点 | 每格有唯一正确行、查表最直观；但 17-18 行表更长、镜像/对账/T5 全链要跟 | 一行承载双分支：人类可读、机器不可路由（无 match-order 字段） |
| 可维护性 | 行数不变 → T5/重签件 §3/八类对账永不需要重述 | 行数成为新的维护面：每次行数类断言随行数重述 | 同收紧 |
| 裁决/批准链现状 | **全链在案**：pf2 判定 A（§4.4）→ row5 选项 B（confirmed 复核）→ 裁决采 B（unconfirmed，待确认）→ 统一清单汇总；批准人 = 乙设计责任人 | 与裁决 :102/:106「C 不采」**相抵**；须满足裁决 §6 触发条件 ④（消费方契约实证为严格合取键且拒绝注记路由）后重开裁决 | U3/U4 已在处方内，非独立选项 |

**哪个方案在「可达 6 格」上效果最好？** 分层回答：
- **STRICT 机器键层**：唯一能把 6 格全绿的是**组合**（先收紧 :2/:4/:6/:13、再补对照 3 行 = PT 情景：6/6 OK，`_cf_enum_out.txt:236-242`）。单一方案都不行：U 留 3 错答 + 3 孤儿；T4 留 6 孤儿；补行留 5 错答。
- **不增行约束下**：收紧（U2+U4+U3+镜像）最好——LOOSE/注记路由读法 6 格全绿、STRICT 键层把「5 错答 + 1 孤儿」压成「3 错答 + 3 孤儿」，且若批准人采裁决 §5.5-6 的可选项（:6 加 carve-out 句）或随批收紧 :6（T4 形态），唯一 high 虚报格 O1′ 在文本层也被关闭。
- **补对照行单独用于可达 6 格几乎无效**：只救 absent×re_none 一个孤儿，5 个错答格原样——「让错答格旁边多一个正确答案」不等于「错答格不再错答」。

---

## 5 第五步：建议

### 5(a) 两方案能否并存？

**能并存，机制正交，且只有组合能把 STRICT 键层可达 6 格清零**（PT：STRICT 75/0/6，剩余 6 孤儿全部不可达文本债；LOOSE 81/0/0）。机制上：收紧改既有行前件（行数不变），补对照增行（消孤儿），互不抵消——P3 补行在 T4 收紧后的矩阵上恰好接住全部 read_error × 非 present 态格（14 格）。但**裁决层不并存**：补对照行 = 选项 C 族动作，被裁决 :102/:106 明判「不采」，其再立项条件 = 裁决 §6 触发条件 ④（消费方匹配契约实证为严格合取键且拒绝注记路由，即 AFTER-B-STRICT 口径被采纳为验收口径）。**因此：先收紧（已裁决处方），补对照作为条件触发的二期，不得与 U2/U3/U4 同批混入。**

### 5(b) 如果只能选一个，选哪个？

**选收紧（统一清单 U2/U3/U4 形态，即裁决采 B 的六处处方）。** 理由：
1. **零内容级击穿**：行数不动，T5「14 组 fixture」、重签件 §3「十四行逐行比对」/「14/14」、B2B_DESIGN:144「14 项」/:163 八类对账全部原样；只有指纹换版登记义务。
2. **批准链完整**：pf2 判定 A → row5 选项 B（复核 confirmed）→ 裁决采 B → 统一清单汇总，批准人同一（乙设计责任人）；补对照无任何登记背书且与在案裁决相抵。
3. **错答比不答危险**：W1/W2 是归因错位（排障方向错）、O1′ 是唯一 high 虚报（会驱动「当崩溃征兆上报」的错误动作）；不答的五层兜底（STRICT_EXPOSURE §5.2）不变，且不答优于错答已是两轮裁决口径（:59/:92）。
4. **收益集中度**：补对照的独有收益（孤儿→有正确答案）主要落在**不可达文本债格**（9 孤儿中 8 格不可达），对三个 conf=none 格的重规约代价不成比例（耦合件 §4.3-C 同判）。

### 5(c) 对「可达 6 格」的最小必要改动（不解决全部 21 格）

**最小必要改动（不增行）= 统一清单六处 = U2 + U3 + U4 + 镜像 :148/:150/:151**（裁决改 1-6）：
- none×re_none、none×re_true：U2 收紧后错答消失（strict 层→孤儿 + 分流句指路；LOOSE 层 :5 接管→OK）；
- error×re_none、error×re_true：U4 分流句文本层关闭（LOOSE 层→OK；strict 前件字面不变，层残留如实登记）；
- absent×re_true（O1′，唯一 high 虚报）：U3 的 :5 注记文本层收容（LOOSE 层压制 :6→OK；strict 层残留，裁决 §5.5-6 明示可选加 carve-out 句属批准人裁量）；
- absent×re_none（可达孤儿）：U3 的 :5 注记使其在 LOOSE 层被正确接管；STRICT 键层该格保持孤儿（不答，方向正确）；
- **镜像三行是本最小集的必要部分**：只改 JSON 不同步 :148/:150/:151 即双源不一致，且 T2/T5/重签件:154 条件 2 全抓不到（耦合件 §4.5-2，静默通过）。
- 若要把 STRICT 机器键层的可达 6 格也清零：唯一不违裁决的路径是满足触发条件 ④ 后立项 **B′**（match_priority 字段）；补对照 3 行（14→17）是备选但代价 = §3(c) 十处击穿。

### 5(d) 与统一清单 U2/U3/U4 是兼容还是冲突？

**内容兼容、裁决层冲突、文本有一处可选修订点。**
- 内容兼容：补A/补B/补C 与收紧后的 :2/:4 无格冲突（收紧后那些格无 claimant，新行恰好接住）；LOOSE 下新行与 :5 同值（post_read_error/none/false），无新错答（P3/PT 的 LOOSE 均保持 81/0/0 实证）。
- 裁决层冲突：补对照 = 选项 C 族，被 :106 不采——不能作为 U2/U3/U4 的同批附件直接混入，须走触发条件 ④ 的再裁决。
- 可选文本修订点：U2 分流句「见 :5 行」在 strict 键层对非 present pre 是死指针（:5 preState=present 不吸收）——若二期真补 A/B/C 三行，宜把分流句改为「见 :5 行与新增 read_error 承载行」或由补行 condition 自带码序注记（拟文已含）；U2 文本本身无须为兼容补行而预改。

---

## 6 声明与未验项

**未改任何文件声明**：本轮写域 `lead/counterpart_fix_20261109/` 内新增仅四件：`_cf_fp_check.py`、`_cf_enum_counterpart.py`、`_cf_enum_out.txt`、本件。被核 15 件 hashlib 实算与编排方基线/在档值逐字节一致（**15/15 MATCH**，首跑与终跑两次一致 = 全程零漂移）= 零改动硬证。未 commit、未 push（本轮未执行任何 git 写命令）。零真机、零采样。本件为设计与对比，**不含任何既成事实改动断言**；不构成采纳决定——采纳权在乙设计责任人（矩阵/设计侧）与裁决件既定流程。

**未验项（如实登记，不补造）**：
1. 真机实流未跑（零真机纪律）；可达 6 格的触发概率沿用 matrix_reach §4.1 的推理评级（转引 STRICT_EXPOSURE:159 自记「未实测」）。
2. `_mr_probe1_out.txt`（可达格一手探针输出）本轮未开读——可达性一手引证为**转引** STRICT_EXPOSURE §4.1 栏一表格；本轮亲手证据 = 81 格网格实跑（纯函数直调）+ REACH 表实读（`_se_enum.py:291-306`）。
3. T1/T2/T5 门禁未跑（沿 V2:180-184 自记与裁决 §6 未验 1）；本仿真不能冒称门禁通过。
4. claimant 覆盖谓词为手工编码（自然语言 condition 无法完全机器化）；LOOSE :2 宽键与 U3 优先句压制是复现在案数字的必要建模选择（去宽键 ⇒ 6 孤儿，`_sev_enum_out.txt:49` 转引；U_NP 情景 = 不采优先句的对照）。
5. 补A/补B/补C/补D 拟文未做逐字镜像推演（B2B_DESIGN 镜像行、V2 §4.2 行、重签件 §3 行的对应改文未起草）——若二期立项，按 §3(c) 清单补齐。
6. R3:42 的 14/14 为历史转引（`_review_probe_r3_out.txt` 未复读）；pf2:231 先例为转引（pf2 原文未直读）。
7. 本轮实跑命令计数：Bash 8 次（目录清点 2 次、指纹脚本 2 次【首跑 12 件 / 终跑 15 件】、枚举脚本 3 次、inline `python -c` 实算 `_rv2_probe` 输出哈希 1 次——该次仅读裁决写域单件、未写任何被核域）；Write/Edit 均落唯一写域。
