# STRICT_EXPOSURE — STATE_MATRIX.json 两口径（STRICT/LOOSE）暴露面交付件

- 撰写：暴露面撰写员（动态工作流子代理），2026-11-09。前序：评估轮产出 `_se_fp.py`/`_se_fp_out.txt`/`_se_enum.py`/`_se_enum_out.txt`/`_se_report.md`，复核轮产出 `_sev_fp.py`/`_sev_fp_out.txt`/`_sev_enum.py`/`_sev_enum_out.txt`；本交付轮新增**仅本件**。
- 性质：**只评估、不改件**。不判该不该改矩阵；§5.4 的文本修正为任务书要求的处方**描述，未实施**。

## 1 目的与边界

只评估乙矩阵 `lead/b2b_design_20261106/STATE_MATRIX.json`（14 行）在两种读法（STRICT/LOOSE）下，相对实码 `classify_except_freshness`（`lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py`）的**暴露面**：哪些格矩阵会给出与实码不符的声称（MISLABEL）、哪些格矩阵无行可答（ORPHAN）、这些格哪些实流可达、哪些不可达。

**两栏术语（全篇分开统计，不合并）**：
- **可达且会造成误读**（活性问题）：实流或结构上可产出该格输入，消费方按矩阵行文本读会得出错误结论或无答案。
- **不可达但文本仍误导**（**纯文本债**）：实流产不出该输入（仅 fixture 域可构，或需未来 pre 写点变更），行文本一旦被 fixture 构造或未来代码消费仍会误导。

**边界**：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，不 taskkill，不读活进程内存）；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 注入 / 动态内存解析）；绝对只读域（`lead/b2b_design_20261106/`、`lead/b2b_candidate_lf_20261107/`、`lead/o1prime_reach_20261109/`、`lead/matrix_reach_20261109/`、`lead/matrix_ab_ruling_20261109/`、`lead/matrix_row5_20261109/`、母本、两件台账）本轮零写入；唯一写域 = `lead/strict_exposure_20261109/`；不 commit、不 push。Python 一律 python -I -X utf8 + 绝对路径；指纹用 hashlib。

## 2 上游指纹（十一件）与两口径定义逐字摘录

### 2.1 上游指纹（本交付轮实跑 `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\strict_exposure_20261109\_se_fp.py`，EXIT=0，**11/11 MATCH**；绑定行格式版见 §5.1）

| # | 件 | SHA256 | 字节数 | 结果 |
|--:|:--|:--|--:|:--|
| 1 | lead/b2b_design_20261106/STATE_MATRIX.json（被核乙矩阵） | 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016 | 3558 | MATCH |
| 2 | lead/b2b_design_20261106/B2B_DESIGN.md | 565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf | 66735 | MATCH |
| 3 | lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py（被核实码） | ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2 | 412759 | MATCH |
| 4 | lead/o1prime_reach_20261109/O1PRIME_REACHABILITY.md | 7dca469ea29d2874217211944102fb7feac9dc0d398ab08543123be8cd1ff4e7 | 23488 | MATCH |
| 5 | lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md | cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6 | 27825 | MATCH |
| 6 | lead/matrix_reach_20261109/_mr_probe1_out.txt | 7a8a4198bdfff6aac5f0794f46432d446e592308ad27b819701e50397ca3e27e | 18180 | MATCH |
| 7 | lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md | 0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31 | 36851 | MATCH |
| 8 | lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md | 6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8 | 29818 | MATCH |
| 9 | out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py（母本） | 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636 | 399508 | MATCH |
| 10 | lead/PENDING_DECISIONS.md | 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 | 52419 | MATCH |
| 11 | lead/GOAL_THREE_TARGETS_20261018.md | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 759518 | MATCH |

### 2.2 两口径定义逐字摘录（本交付轮 Read/sed 实读）

- **STRICT 匹配键纪律**（MATRIX_ROW5_COUPLING.md:67，逐字）：「匹配键 = `preState` 字段 + condition 前件。判定列依据 = §3.1 码序 + §4.1 两轮 72 格实跑。」
- **口径归属**（RULING_MATRIX_AB.md:42，逐字）：「(i) **STRICT** = 耦合件 MATRIX_ROW5_COUPLING.md:67『匹配键 = preState 字段 + condition 前件』合取纪律（row5 探针 :118 的 cannot-claim 规则同源）」；(ii)「**LOOSE** = condition 文本承载路由、preState 列为登记示例态（草案 B 方案隐含读法）」。
- **操作化**：STRICT 下一行声称一格 ⇔（格 preState 归一态 == 行 preState 字段）∧（格满足行 condition 前件）；LOOSE 下由 condition 语义决定、preState 字段不作硬键。LOOSE 对 :2 的宽 preState 键读法依据 = 耦合件 :112（逐字）：「宽 preState 键读法下 :2/:3 兜住且**标签恰同**」。

## 3 两口径格数独立重算（不采信上一轮数字，本轮独立实现复现）

**(a) 方法**：`importlib spec_from_file_location` 静态装载候选真模块、直调真 `classify_except_freshness` 跑全 81 格（9 类 pre × 9 类 post：未采集四变体 None/{}/缺state/脏值、显式 unknown、absent_confirmed、present 带 sha、present 缺 sha、error × read_error·exists=None、read_error·exists=True、跑后无件、在场·缺 post.sha、在场·sha 异、在场·sha 同×{mt 同/升/降/缺}）；claimant 谓词按矩阵 14 行 condition 原文独立手编。计数规则：无 claimant ⇒ ORPHAN；全部 claimant 三元（verdict/conf/usable）与实码一致 ⇒ OK，否则 MISLABEL。

**(b) 命令与输出**：评估轮 `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\strict_exposure_20261109\_se_enum.py > …\_se_enum_out.txt`（EXIT=0）；**本交付轮复跑**（无重定向）并 diff 于在档件：`ENUM_RERUN_IDENTICAL`（逐行一致）。装载安全：import ok（`_se_enum_out.txt:8-10`）+ 81 格实码与耦合件 §4.1a 全格表交叉核对 **XCHECK ALL_PASS（0 mismatch / 81）**（`_se_enum_out.txt:11-12`）。

**(c) 结果与对照**：

| 口径 | OK | MISLABEL | ORPHAN | 出处 |
|:--|--:|--:|--:|:--|
| **STRICT** | **60** | **12** | **9** | `_se_enum_out.txt:14` |
| **LOOSE** | **67** | **14** | **0** | `_se_enum_out.txt:36` |

与上一轮 A/B 裁决基线（`RULING_MATRIX_AB.md:43`：「STRICT = OK 60 / MISLABEL 12 / ORPHAN 9；LOOSE = OK 67 / MISLABEL 14 / ORPHAN 0」）**完全一致**——但本轮为独立实现（真模块直调 + 独立手编谓词），复核员又以第二套独立实现复现同数（`_sev_enum_out.txt:7-8`，26 条命令）。

**(d) 敏感性变体**：first-match-wins ⇒ STRICT 61/11/9、LOOSE 69/12/0（`_se_enum_out.txt:51-53`）；复核员 LOOSE 去宽键（:2 不采宽键）⇒ 63/12/**6**（`_sev_enum_out.txt:49`，6 孤儿证实宽键是复现 ORPHAN=0 的必要读法）；:14 字面变体（不要求 pre.sha 在场）⇒ STRICT 59/13/9、LOOSE 66/15/0（`_sev_enum_out.txt:50-51`，稳健性注记，不影响可达栏）。

## 4 逐格暴露面分类（两栏分开，不合并）

实码列缩写：PRE = `post_read_error/none/None`（usable_as_crash_evidence 恒 False，候选 :4624-4632）；出处行号除另注外均属 `_se_enum_out.txt`。

### 4.1 STRICT 口径：21 格暴露 = 可达 6 格 + 不可达纯文本债 15 格

**栏一·可达且会造成误读（6 格，实跑 4 + 结构可达未单跑 2）**：

| 格（pre × post） | 矩阵声称（claimant 行） | 实码 | 可达性依据 | 误读内容 | 纯文本债？ |
|:--|:--|:--|:--|:--|:--|
| none × re_none | :2 → unknown/none/false（单 claimant 无对冲） | PRE | **实跑**：`_mr_probe1_out.txt:159`（pre=None × re·exists=None → 实码 PRE、矩阵归属 :2）；触发链 matrix_reach:151 | 「跑后证据复制失败」被读成「跑前快照未采集」——故障归因错位（W1） | 否 |
| none × re_true | :2（同上） | PRE | **结构可达未单跑**：read_error 写点 :4786 对任意 pre 生效（本交付轮实读 :4784-4786）+ exists=True 型 write_bytes 失败已实产于 absent pre（`_mr_probe1_out.txt:193-197`） | 同上 | 否 |
| error × re_none | :4 → error_pre_snapshot/none/false（单 claimant 无对冲） | PRE | **实跑**：`_mr_probe1_out.txt:179`（error × re → PRE）；触发链 matrix_reach:152 | 「跑后复制失败」归因为「跑前采集失败」——排障方向错位（W2） | 否 |
| error × re_true | :4（同上） | PRE | **结构可达未单跑**：两半机制正交（snap.error 与 read_error 分属 :4611/:4786） | 同上 | 否 |
| absent × re_true（O1′） | :6 → **new_first_appearance/high**/false（单 claimant 无对冲） | PRE | **实跑**：`_mr_probe1_out.txt:193-197`（C2 写侧失败）+ O1′ 专查五种真实失败（转引复核轮核验） | **环境级复制失败被虚报为「本趟新出现·高置信」**——唯一虚报置信格，最坏动作 = 当崩溃征兆上报 | 否 |
| absent × re_none（O1 主子格） | **无行（孤儿）** | PRE | **实跑**：`_mr_probe1_out.txt:187-191`（C1 读侧失败） | 严格匹配器「不答」；把无行当通过即静默漏报 | 否（孤儿） |

**栏二·不可达但文本仍误导（15 格 = 纯文本债，逐格）**：

| 格（pre × post） | 矩阵声称 | 实码 | 不可达依据 | 误读内容 | 纯文本债？ |
|:--|:--|:--|:--|:--|:--|
| empty × re_none | :2 → unknown/none/false | PRE | 实流 pre 仅 None（:6528）或 make_pre 三态（:6623），{}/缺state/脏值**无第三写点**（matrix_reach §3.1①；两写点本交付轮实读 :6527-6529/:6622-6624） | W1 归因错位（仅 fixture 可消费） | 是 |
| empty × re_true | :2（同上） | PRE | 同上 | 同上 | 是 |
| missing × re_none | :2（同上） | PRE | 同上 | 同上 | 是 |
| missing × re_true | :2（同上） | PRE | 同上 | 同上 | 是 |
| dirty × re_none | :2（同上） | PRE | 同上 | 同上 | 是 |
| dirty × re_true | :2（同上） | PRE | 同上 | 同上 | 是 |
| present_nosh × re_true | :13 → error_pre_snapshot；**claimants=[5,13]，:5 同格正确行并存**（:24） | PRE | make_pre 在场路径必经 :4607 sha256_file（本交付轮实读），算炸整体 error；「present 且缺 sha」不在输出域（§3.5） | :13 误盖（W3）；有 :5 对冲的有对冲误配 | 是 |
| expl_unknown × re_none | 无行（孤儿） | PRE | make_pre 初值 unknown 三路必覆写（:4589→:4599/:4603/:4610），显式 unknown 非输出域（§3.4） | 孤儿：不答 | 是 |
| expl_unknown × re_true | 无行（孤儿） | PRE | 同上 | 孤儿：不答 | 是 |
| expl_unknown × no_post_sha | 无行（孤儿） | unknown/none/None | 同上 | 孤儿（实码恰 unknown，:2 若被宽读其值恰同——耦合件 :112「标签恰同」） | 是 |
| expl_unknown × sha_diff | 无行（孤儿） | unknown/none/None | 同上 | 同上 | 是 |
| expl_unknown × mt_same | 无行（孤儿） | unknown/none/None | 同上 | 同上 | 是 |
| expl_unknown × mt_up | 无行（孤儿） | unknown/none/None | 同上 | 同上 | 是 |
| expl_unknown × mt_down | 无行（孤儿） | unknown/none/None | 同上 | 同上 | 是 |
| expl_unknown × mt_missing | 无行（孤儿） | unknown/none/None | 同上 | 同上 | 是 |

（W1 家族口径差如实登记：matrix_reach:145 把实流可达子集记为「(pre=None × read_error) 单格」；81 格网格里为 none × {re_none, re_true} 两格——同一触发链的两种 read_error 形态。评估件引「matrix_reach R:153-154」系转引该报告 §4.1:145 自己的第二手引证；一手探针证据本交付轮已在 `_mr_probe1_out.txt:159-160` 实读落实。）

### 4.2 LOOSE 口径：14 格暴露 = 可达 5 格 + 不可达纯文本债 9 格（无孤儿）

| 格（pre × post） | 矩阵声称 | 实码 | 可达性依据 | 误读内容 | 纯文本债？ |
|:--|:--|:--|:--|:--|:--|
| none × re_none | 坏 :2；**同格 :5 正确行并存**（:37） | PRE | **实跑**（同 §4.1 栏一） | W1 归因错位；:5 冲突文本自明 | 否 |
| none × re_true | 坏 :2；:5 并存（:38） | PRE | **结构可达未单跑**（同上） | 同上 | 否 |
| absent × re_true（O1′） | 坏 :6（high 虚标）；:5 并存（:47） | PRE | **实跑**（C2，`_mr_probe1_out.txt:193-197`） | O1′ 虚报置信；:5 冲突文本自明 | 否 |
| error × re_none | 坏 :4；:5 并存（:49） | PRE | **实跑**（`_mr_probe1_out.txt:179`） | W2 归因错位；:5 冲突自明 | 否 |
| error × re_true | 坏 :4；:5 并存（:50） | PRE | **结构可达未单跑** | 同上 | 否 |
| empty × re_none | 坏 :2；:5 并存（:39） | PRE | 不可达（无第三写点） | W1 残余 | 是 |
| empty × re_true | 坏 :2；:5 并存（:40） | PRE | 不可达 | 同上 | 是 |
| missing × re_none | 坏 :2；:5 并存（:41） | PRE | 不可达 | 同上 | 是 |
| missing × re_true | 坏 :2；:5 并存（:42） | PRE | 不可达 | 同上 | 是 |
| dirty × re_none | 坏 :2；:5 并存（:43） | PRE | 不可达 | 同上 | 是 |
| dirty × re_true | 坏 :2；:5 并存（:44） | PRE | 不可达 | 同上 | 是 |
| expl_unknown × re_none | 坏 :2（宽键接住）；:5 并存（:45） | PRE | 不可达（make_pre 三路必覆写） | W1′ | 是 |
| expl_unknown × re_true | 坏 :2；:5 并存（:46） | PRE | 不可达 | 同上 | 是 |
| present_nosh × re_true | 坏 :13；:5 并存（:48） | PRE | 不可达（:4607 必算 sha） | W3 | 是 |

（LOOSE 的 ORPHAN=0：STRICT 的 9 格孤儿中，expl_unknown × 在场六型被 :2 宽键**正确**接住转 OK（:133-138），absent × re_none 被 :5 **正确**接管（:139），expl_unknown × re 两型转为误配。同格两口径归属差实例：absent × re_true 在 STRICT 下 claimant 仅 :6、LOOSE 下 [5,6]；absent × re_none 在 STRICT 下孤儿、LOOSE 下 [5]——`_se_enum_out.txt:139-140` 实跑。）

### 4.3 两栏分开统计（不相加、不合并）

| 栏 | STRICT | LOOSE |
|:--|--:|--:|
| 总暴露（MISLABEL + ORPHAN） | **21/81（约 26%）** | **14/81（约 17%）** |
| MISLABEL | 12 | 14 |
| ORPHAN | 9 | 0 |
| 可达-实跑 | 4 | 3 |
| 可达-结构未单跑 | 2 | 2 |
| **可达合计** | **6** | **5** |
| **不可达纯文本债** | **15** | **9** |

校验：STRICT 12+9=21=6+15；LOOSE 14+0=14=5+9。✓

## 5 复核回件、总评、声明与未验

### 5.1 复核回件（verdict 如实登记：**confirmed**）

复核员 26 条命令独立复核，核心全部通过：指纹 11/11（`_sev_fp_out.txt:12` TOTAL_MATCH=11/11）；定义摘录逐字一致；独立重算复现全部基线与变体；M4 逐格 claimant 与评估轮输出逐行一致；两栏分开未合并；后果无缩小、兜底引证全核实；零越界。**三处外围瑕疵随件登记（本交付轮逐条实读核验，全部属实）**：

1. **夸大 1/12**：评估件称 STRICT 12 个误配格「全部单一错误 claimant、同格无正确行对冲」——其自家输出 `_se_enum_out.txt:24` 与复核员 `_sev_enum_out.txt:28` 均显示 present_nosh × re_true 的 claimants=[5,13]，:5 为同格正确行。实情 = **11/12 无对冲、1/12（W3）有对冲**。不影响 STRICT 更危险的结论与任何数字；本件 §4/§5.3 已按 11/12 改述。
2. **错引**：评估件 §4(b) 引「裁决 :122 同判：不答优于错答」——本交付轮实读 RULING_MATRIX_AB.md:118-124，**:122 实为裁决件「改 2」节中 STATE_MATRIX.json 第 5 行的 JSON 原文**（`{"state":"post_read_error","preState":"present",…}`），件内无该原句；同类表述实在 :59（「把『错答』换成『不答 + 文字兜底』」）与 :92（「孤儿 = 『不答』，非『错答』，方向正确」）。本件改引 :59/:92。
3. **登记数字不实**：评估件 F1 称候选顶层 Call=0（`_se_enum_out.txt:6`）——复核员同口径 AST 扫描得 1 处（`_sev_enum_out.txt:3`「top-level Expr-Call = [182]」），本交付轮实读候选 :178-182 证实 **:182 `ctypes.windll.user32.SetProcessDPIAware()` 为顶层直接调用**、其 :180 注释自认「模块导入即生效」。良性、进程自声明级、matrix_reach 复核轮已登记；import 安全结论不变（评估轮与复核轮 import 均实跑成功 + 81/81 交叉核对 ALL_PASS）。

**稳健性注记（复核员，非缺陷）**：present_nosh × no_post_sha（fixture 域）的 :13/:14 前件同时字面成立；耦合件 §4.1a 取正典读法（码序 7 缺 pre.sha 先于码序 8 缺 post.sha）；若取 :14 字面读法则 STRICT 59/13/9、LOOSE 66/15/0。该格不可达，可达栏与文本债构成不受任何变体影响。

**绑定行（本交付轮实跑 `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\strict_exposure_20261109\_se_fp.py`，11/11 MATCH，EXIT=0；顺序：乙矩阵/乙设计/候选LF/O1′专查件/可达性报告/其探针输出/A-B裁决件/矩阵连带评估件/母本/PENDING/GOAL）**：

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

### 5.2 可达误读的实际后果与兜底（两栏都报）

**后果（可达 6/5 格）**：O1′ 格——环境级复制失败被虚报为「本趟新出现·高置信」，最坏动作 = 当崩溃征兆上报/升级；W2 两格——「跑后复制失败」归因成「跑前采集失败」，排障方向错位（去查 make_pre 而非 copy_post）；W1 两格——同类归因错位（读成「快照未采集」）；absent × re_none 孤儿格——严格匹配器「不答」，最坏动作 = 把无答案当无异常放行（不答优于错答，方向正确：裁决 :59/:92，但仍是暴露）。触发现实性：全部为环境级罕见故障（AV 瞬时锁/ACL/磁盘满/out_dir 异常），无 trip 自身逻辑路径；评级「近乎不可能/罕见」为零真机下的**推理**评级、未实测（matrix_reach:145/:180 自记）。

**兜底（多层，每格都有）**：① 运行期实码恒 PRE/usable=False——read_error 是 classify 第一判定分支（候选 :4643-4646，注释 :4642「★ N1：错误独立出口，优先于一切状态折叠」，本交付轮实读）；② usable_as_crash_evidence 恒 False（:4624-4632，转引复核轮核实）；③ 同账本 ERROR×3（:4777-4785）→ finalize_errors.txt（:4547-4553）→ error.txt（:4571-4577）与任何 high 误读直接冲突、自明易察；④ 候选不读矩阵（grep STATE_MATRIX=0，复核轮）、confidence 无运行期消费分支、E/退出码判据独立于 F（:217-220/:5985-5990）；⑤ T2/T5 门禁不受 condition 文本影响（裁决 :92：现役无任何程序按 condition 文本做行匹配）。15 格文本债仅在 fixture 构造输入或未来 pre 写点变更时才可被消费。

### 5.3 暴露面总评

- **STRICT**：总暴露 **21/81 格（约 26%）** = **可达 6**（实跑 4 + 结构未单跑 2）+ **不可达纯文本债 15**；MISLABEL 12 + ORPHAN 9。可达误配 5 格全被 conf=none/usable=False 兜底，唯一虚报置信格 = O1′。
- **LOOSE**：总暴露 **14/81 格（约 17%）** = **可达 5**（实跑 3 + 结构未单跑 2）+ **文本债 9**；MISLABEL 14 + ORPHAN 0。
- **哪个更危险：STRICT**。① 量大（21 vs 14）；② 12 个误配格中 **11 格单一错误 claimant、同格无正确行对冲**（claimants=[2]×8、[4]×2、[6]×1），O1′ 的 high 虚标无任何同格冲突提示，是最危险的静默虚高（W3 一格有 :5 对冲）；LOOSE 下同格全部有 :5 正确 claimant 并存（[2,5]/[4,5]/[5,6]/[5,13]），冲突文本层自明；③ STRICT 另有 9 格孤儿（含 1 可达格），在把无行当通过的验收里静默放行；LOOSE 无孤儿。**反面向（如实）**：LOOSE 依赖两个未成文读法（宽 preState 键 + condition 注记路由），矩阵无 match-order/priority 字段（裁决 :92）；若消费方改用 first-match 行序，LOOSE 仍有 12 格错（`_se_enum_out.txt:53`）；且「冲突自明」只对复读全表的读者成立，机器匹配器未必报冲突。
- **STRICT 下最小必要文本修正（只描述，未实施，不构成采纳建议）**：合取键下 :5 的 preState=present 字段受 B2B_DESIGN:142 四态值域契约约束（本交付轮实读），无法吸收非 present pre 的 read_error 格——纯文本修正做不到「让 :5 接管」，只能**前件收紧**：在 :2、:4、:6（:13 随批）的 condition 前件内显式加「post.read_error 为空」类限定，把 11 个误配格从「错答」转「不答」（W3 因 :5 独占转 OK），STRICT 变为约 OK 61 / MISLABEL 0 / ORPHAN 20 的形态；**20 个孤儿在 STRICT 口径下文本不可消除**——消除需 B′（匹配键纪律修订 / match_priority 字段，裁决 :236 补证项）或拆行（选项 C，裁决 :106 不采）。镜像与级联登记义务同裁决 §5.2。

### 5.4 未改任何文件声明

本交付轮在写域内**仅新增本件**（STRICT_EXPOSURE.md）；被核 11 件 SHA256+字节数与本交付轮实跑逐件一致（11/11 MATCH）= 零改动硬证；`git log --since "2026-11-09 00:00" --oneline` 输出 **0 条**，末次 commit = 2657458（2026-11-01 19:35:33 +0800）——未 commit、未 push。三程（评估/复核/交付）均零真机、零采样；绝对只读域与两件台账零写入、零追加、零覆盖；未判该不该改矩阵。

### 5.5 未验项（如实登记，不补造）

1. 真机端到端实流未跑（零真机纪律）；可达评级（近乎不可能/罕见）沿用 matrix_reach §4.1 的推理结论，未独立量化概率（matrix_reach:180 自记「全部为推理——未实测」）。
2. none × re_true、error × re_true 两格为**结构可达、组合未单跑**（机制两半各有实跑证据，组合未实跑）。
3. V2:110、重签件、修正提案（pf2）原文未直接实读，相关引用均为经裁决件/耦合件/评估件的**转引**。
4. claimant 覆盖谓词为手工编码（自然语言 condition 无法完全机器化）；LOOSE 的 :2 宽键读法是复现 ORPHAN=0 的必要编码选择（去宽键 ⇒ 6 孤儿，`_sev_enum_out.txt:49`）。
5. T1/T2/T5 门禁未跑（沿裁决 :240）。
6. 评估轮 `_se_enum.py` 源码未逐行审计——以本交付轮复跑输出与在档件逐行一致（ENUM_RERUN_IDENTICAL）+ 复核员第二套独立实现复现同数代替。
7. O1′ 专查件 §3.1/§3.2 的五种真实失败明细、matrix_reach §3.1①/§3.4/§3.5 的不可达证明明细，本交付轮未逐一重开原文，采信复核轮「实跑引证逐一落实」的核验结论；本交付轮亲手实读落实的一手引证见 §4 各行与 §5.1 瑕疵 2/3。
