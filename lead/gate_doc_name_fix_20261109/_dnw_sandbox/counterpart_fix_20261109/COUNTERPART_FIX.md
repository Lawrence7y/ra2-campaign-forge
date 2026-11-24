# COUNTERPART_FIX —— 「收紧 condition」vs「补对照行」修法对比定稿（六节版）

- 撰写：修法对比撰写员·GLM（动态工作流子代理），2026-11-09。
- 性质：**只设计与对比，不施行、不改任何既有文件**。本件为该对比任务的定稿交付件；素材 = 上一轮对比件 `lead/counterpart_fix_20261109/_cf_counterpart_vs_tighten_20261109.md`（32,840 B）与其枚举件，全部数字经本轮复跑逐字节复核（见 §1 实跑命令）。
- 纪律：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析；枚举仿真 = importlib 静态装载候选真模块 + 直调纯函数 `classify_except_freshness`，沿 `_se_enum.py:60-64` 在案安全先例；本轮 grep 核过 `_cf_enum_counterpart.py` 无任何文件写行为——仅 3 处只读 `open(…,"rb")`/`json.loads`）；绝对只读域（`lead/b2b_design_20261106/`、`lead/strict_exposure_20261109/`、`lead/text_fix_unified_20261109/`、`lead/matrix_ab_ruling_20261109/`、`lead/matrix_row5_20261109/`、`lead/b2b_candidate_lf_20261107/`、母本、两件台账）零写入、零追加、零覆盖；唯一写域 = `lead/counterpart_fix_20261109/`；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 hashlib。
- ★ 术语纪律（全篇执行，三者不许混为一谈）：
  - **收紧 condition** = 修改既有行 condition 前件，让错答格不再被该行声称。行数不变（14 行）。机器效果 = 错答 → 不答（ORPHAN），或该坏 claimant 退场后由同格正确行接管（OK）。
  - **补对照行** = 矩阵追加新行，让无行/错答格旁边多出一个正确答案。行数 14→17/18。机器效果 = 消 ORPHAN；对 MISLABEL 格只是「加对冲」，坏 claimant 仍在、不摘除。
  - **分流表述** = 在 condition 内加注记/分流句（纯注记不动前件，或与收紧合并），让人类读者与「注记路由」读法看到落点。单用对 STRICT 机器键层零效果。
  - ★★ **「变 ORPHAN 不等于问题解决」**：收紧把错答换成不答，方向正确（裁决 :59「把『错答』换成『不答 + 文字兜底』」、:92「孤儿 = 『不答』，非『错答』，方向正确」，本轮实读），但孤儿在「把无行当通过」的验收里仍是暴露格。本件所有 tally 把 MISLABEL 与 ORPHAN 分列，从不用「暴露减少」冒充「键层清零」。
- 本文行号约定：`_cf_enum_out.txt` 引证行号 = 本轮复跑输出 `_cfx_enum_out.txt` 的行号（两者逐字节一致，零漂移）；其余为各件磁盘行号，均为本轮实读。

## 1 目的与边界

1. **目的**：对 81 格暴露面（STRICT 口径 21 格 = 12 MISLABEL + 9 ORPHAN）逐格对比两条修法——「收紧 condition」与「补对照行」——及其变体「分流表述」：每格在每方案下变 OK、变 ORPHAN 还是原样；每方案的行数变化、绑定击穿面、裁决链状态；并给出最小必要改动建议。**只设计，未对任何行做任何修改。**
2. **边界**：见页首纪律块。补充两条：(a) 本对比不改动矩阵、镜像、V2、重签件、台账任何一字，补A/补B/补C/补D 仅为**拟文**（未实施）；(b) 采纳权在乙设计责任人（裁决 §5.2「批准人一律 = 乙设计责任人」）与裁决件既定流程，本件不构成采纳决定。
3. **本轮实跑命令（cwd=`D:\Project\ra2-campaign-forge`，EXIT 均 0）**：
   1. `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\counterpart_fix_20261109\_cf_fp_check.py` → **15/15 MATCH**（编排方 12 件基线 + 上一轮追加 3 件）；
   2. `python -I -X utf8 -c`（hashlib 实算 7 件写域件哈希）→ 复核回件绑定对象 `_cf_counterpart_vs_tighten_20261109.md` 实算 = `9878bb7e…ddb4`/32,840 B，与复核回件绑定行逐字符一致；
   3. `python -I -X utf8 …\_cf_enum_counterpart.py > …\_cfx_enum_out.txt` → EXIT=0，`cmp -s` 与既有 `_cf_enum_out.txt` **逐字节一致（零漂移）**，两件 sha256 同为 `31377bb2…f850f`/38,331 B；
   4. grep 核 `_cf_enum_counterpart.py` 无文件写行为；Read 实读上游 12+3 件关键行（逐处引证见下文）。
4. **基线锚点（本轮复跑实证）**：F0 指纹 MATCH（`_cf_enum_out.txt:2-4`）；XCHECK ALL_PASS（0 mismatch / 81，:8）；STRICT 60/12/9（:10）、LOOSE 67/14/0（:32）、first-match 61/11/9（:48）/69/12/0（:70）——与 `_se_enum_out.txt:14/:36/:52/:53` 在档值逐一相符；复核人独立实现 `_cfv_enum.py` 的 16 情景 tally 全 MATCH（`_cfv_enum_out.txt:46-62`「SCENARIO_SUMMARY ALL_MATCH」）。

## 2 上游指纹（十二件）与 21 个暴露格逐格身份

### 2(a) 上游指纹

本轮实跑 `_cf_fp_check.py`，15/15 MATCH（含编排方 12 件 + 上一轮追加 3 件）。绑定行如下（顺序：乙矩阵 / 乙设计 / 暴露面交付件 / 其枚举输出 / 统一清单 / A-B 裁决件 / 矩阵连带评估件 / 候选 LF / V2 定版件 / 母本 / 台账一 / 台账二 / 重签件 / R3 复审 / 裁决探针输出）：

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

前 12 行与编排方指纹基线逐字符一致 = 十二件零漂移硬证；下文全部「文件:行」引证在该基线上有效。实码 PRE = `post_read_error/none/None`（usable 恒 False）。

### 2(b) 12 个 MISLABEL 格逐格身份（STRICT 合取键口径；数据源 `_cf_enum_out.txt:11-22` 本轮复跑）

| # | 格（pre × post） | 错误 claimant | 该行声称 | 实码 | 同格对冲（STRICT） | LOOSE claimants | 可达性 |
|--:|:--|:--|:--|:--|:--|:--|:--|
| 1 | none × re_none | **:2** | unknown/none/false | PRE | **无**（claimants=[2]） | [2,5] | 可达-实跑（STRICT_EXPOSURE:67） |
| 2 | none × re_true | **:2** | 同上 | PRE | **无** | [2,5] | 可达-结构未单跑（:68） |
| 3 | empty × re_none | **:2** | 同上 | PRE | **无** | [2,5] | 不可达-文本债（:78） |
| 4 | empty × re_true | **:2** | 同上 | PRE | **无** | [2,5] | 不可达 |
| 5 | missing × re_none | **:2** | 同上 | PRE | **无** | [2,5] | 不可达 |
| 6 | missing × re_true | **:2** | 同上 | PRE | **无** | [2,5] | 不可达 |
| 7 | dirty × re_none | **:2** | 同上 | PRE | **无** | [2,5] | 不可达 |
| 8 | dirty × re_true | **:2** | 同上 | PRE | **无** | [2,5] | 不可达 |
| 9 | absent × re_true（O1′） | **:6** | **new_first_appearance/high**/false（唯一虚报置信格） | PRE | **无**（claimants=[6]） | [5,6] | 可达-实跑（:71，C2 写侧失败） |
| 10 | present_nosh × re_true（W3） | **:13** | error_pre_snapshot/none/false | PRE | **有**：:5 同格正确行并存（claimants=[5,13]，`_cf_enum_out.txt:20`） | [5,13] | 不可达（make_pre 在场必算 sha，耦合件 :63/:115） |
| 11 | error × re_none（W2） | **:4** | error_pre_snapshot/none/false | PRE | **无**（claimants=[4]） | [4,5] | 可达-实跑（:69） |
| 12 | error × re_true（W2） | **:4** | 同上 | PRE | **无** | [4,5] | 可达-结构未单跑（:70） |

对冲结构：**11/12 单一错误 claimant、同格无正确行**（:2×8、:4×2、:6×1）；**1/12（W3）有对冲**（:5 正确行并存）。与暴露面件 §5.1 瑕疵 1 改述一致（STRICT_EXPOSURE:137 本轮实读）。LOOSE 口径下 14 个误配格（上 12 + expl_unknown×re_* 2 格）claimants 全部含正确的 :5（`_cf_enum_out.txt:33-46`），冲突文本层自明。

### 2(c) 9 个 ORPHAN 格逐格身份（无任何行声称；数据源 `_cf_enum_out.txt:23-31` 本轮复跑）

| # | 格 | 实码 | 无行原因（按 :2-:15 condition 原文核） | LOOSE 下 | 可达性 |
|--:|:--|:--|:--|:--|:--|
| 1 | expl_unknown × re_none | PRE | :2 strict 枚举不含显式 unknown；:3 要「跑后无件」；:5 preState=present | 仍无 :5 以外对冲（宽键下 :2/:3 兜且标签恰同，耦合件 :112） | 不可达（make_pre 三路必覆写，耦合件 :63） |
| 2 | expl_unknown × re_true | PRE | 同上 | 同上 | 不可达 |
| 3 | expl_unknown × no_post_sha | unknown/none/false | 同上 | :2/:3 宽读可兜且标签恰同 | 不可达（O2 家族） |
| 4 | expl_unknown × sha_diff | unknown/none/false | 同上 | 同上 | 不可达 |
| 5 | expl_unknown × mt_same | unknown/none/false | 同上 | 同上 | 不可达 |
| 6 | expl_unknown × mt_up | unknown/none/false | 同上 | 同上 | 不可达 |
| 7 | expl_unknown × mt_down | unknown/none/false | 同上 | 同上 | 不可达 |
| 8 | expl_unknown × mt_missing | unknown/none/false | 同上 | 同上 | 不可达 |
| 9 | absent × re_none（O1 主子格） | PRE | :5 要 present、:6 要「跑后在场（exists=True）」、:7 要「跑后无件」——exists=None 三者皆不满足（耦合件 :113） | :5 正确接管（[5]） | **可达-实跑**（STRICT_EXPOSURE:72，C1 读侧失败）——9 孤儿中唯一可达格 |

### 2(d) 可达性汇总（STRICT_EXPOSURE §4.1 栏一 ：63-72 本轮实读）

- **可达-实跑（4 格）**：none×re_none（M）、absent×re_true（M）、error×re_none（M）、absent×re_none（O）。
- **可达-结构未单跑（2 格）**：none×re_true（M）、error×re_true（M）。
- **不可达-文本债（15 格）**：其余全部。
- **可达 6 格 = 5 MISLABEL + 1 ORPHAN**（STRICT）；LOOSE 口径可达暴露 = 5 格全 MISLABEL（absent×re_none 被 :5 接管，`_se_enum_out.txt:139` 同证）。**STRICT 比 LOOSE 危险**：量 21 vs 14、11 格静默无对冲（:167）、9 孤儿含 1 可达格。

## 3 「收紧 condition」路线分析（逐格：变 OK 还是变 ORPHAN）

### 3(a) 纯收紧 T4（收紧 :2/:4/:6/:13 四行前件、行数不变）——逐格归属

| 被收紧行（修法归属：收紧） | 直接受影响格 | 收紧后状态（STRICT） | 机理 |
|:--|:--|:--|:--|
| :2 | none/empty/missing/dirty × re_*（8 格，全 MISLABEL） | **8 格 → ORPHAN**（`_cf_enum_out.txt:86-93`） | 唯一 claimant 即 :2；收紧后无行可配。:5 strict 键 preState=present 不吸收非 present pre（裁决探针 M2b：`_rv2_probe_20261109_out.txt:77`「:5 NOT eligible」） |
| :4 | error × re_*（2 格，MISLABEL） | **2 格 → ORPHAN**（:104-105） | 同理 |
| :6 | absent × re_true（O1′，1 格 MISLABEL） | **→ ORPHAN**（:103） | 同理 |
| :13 | present_nosh × re_true（W3，1 格 MISLABEL） | **→ OK**（M4 表 :398 该格 T4 列=OK） | **唯一由错答变正确答案的格**：:13 退场后同格正确行 :5 独占接管 |

合计：**12 MISLABEL → 0（其中 11 格变 ORPHAN、1 格变 OK）；ORPHAN 9→20；STRICT 61/0/20**（:85），与 STRICT_EXPOSURE §5.3 处方预测「约 OK 61 / MISLABEL 0 / ORPHAN 20」（:168 本轮实读）逐数相符；LOOSE 81/0/0（:106）。可达 6 格：5 个错答格全部变孤儿 + 1 个既有孤儿 = **6 ORP**（`_cf_enum_out.txt:331-337`）。

**★★ 变 ORPHAN 不等于问题解决**：T4 的「MISLABEL 12→0」只说明错答消失；20 个孤儿（含 6 个可达格）在「无行 = 放行」的验收里仍是暴露。收紧的收益是**质**的（消错答），不是**量**的（STRICT 键层暴露 21→20）。「暴露格数清零」的断言只能在 LOOSE/注记路由读法下作出。

### 3(b) 统一清单 U2/U3/U4 前后对照表（处方逐字见统一清单，本轮实读；tally 本轮复跑）

处方归属（裁决采 B 的六处 = U2/U3/U4 + 镜像 U5/U6/U7）：**U2** = `STATE_MATRIX.json:2` condition 收紧 + 内嵌分流句「post.read_error 非空时先落 post_read_error（…见 :5 行）」（统一清单 :55-64，pf2 §4.5:193 文案原样）；**U3** = `:5` condition 追加码序注记 + 末句「匹配以本 condition 为准」、**preState 字段不动**（:66-76，写 "any" 违 B2B_DESIGN.md:142 四态值域）；**U4** = `:4` condition 加句「（post.read_error 非空时仍先落 post_read_error，见 :5 行）」、**前件字面不变**（:78-86）；**U5/U6/U7** = B2B_DESIGN.md:148/:151/:150 镜像同步（:88-112）。:2 与 :5 一交一接语义闭合（统一清单 :145-149 本轮实读）。

| 情景（行数均 14） | STRICT OK/M/O（supp） | LOOSE OK/M/O（supp） | 格级变化（逐格证据 = `_cf_enum_out.txt`） |
|:--|:--|:--|:--|
| S0 基线 | 60/12/9（0） | 67/14/0（0） | — |
| **U2only**（:2 收紧） | 60/**4**/**17**（0） | 77/**4**/0（0） | strict：8 格 MIS→**ORPHAN**（UNC×re_*，:134-141）；残留 4 M = absent×re_true、present_nosh×re_true、error×2（:130-133）。loose：10 格 MIS→OK（经 :5 接管） |
| **U3only**（:5 注记+优先句） | 61/**11**/9（supp=1） | 69/**12**/0（supp=2） | strict：**仅 present_nosh×re_true 1 格 MIS→OK**（:5 优先句压制 :13——读法依赖，11 个残留 MIS 清单 ：157-167 不含该格）；absent×re_true 仍 MIS（:165）。loose：absent×re_true、present_nosh×re_true 2 格 MIS→OK |
| **U4only**（:4 分流句，前件不变） | 60/**12**/9（0）＝基线 | 69/**12**/0（0） | **strict 机器层零效果**（:190-211 逐格同基线；裁决探针 M3b 同证 `_rv2_probe_20261109_out.txt:81`「:4 unchanged coverage → W2 open」）；loose：error×2 格 MIS→OK |
| **U = U2+U3+U4** | **61/3/17**（supp=1） | **81/0/0**（supp=2） | 与裁决探针 AFTER-B 两口径逐数相同（`_rv2_probe_20261109_out.txt:51` 61/3/17 supp1、:72 81/0/0 supp2）；残留 3 M = absent×re_true（:108）、error×2（:109-110） |
| U_NP（U 但不采优先句） | 60/4/17（0） | 77/4/0（0） | 证明 U 的 strict 3 误配依赖 :5 优先句被消费（W3 格），不采则 4 误配（:225-251） |
| **T4**（纯收紧 ：2/:4/:6/:13，无分流句） | **61/0/20**（0） | **81/0/0**（0） | 比 U 多杀 strict 层 3 个误配（→孤儿）；代价 = 无分流句兜底文本 |

要点：**U 在 STRICT 键层仍留 3 错答（W2×2、O1′×1）+ 17 孤儿**——「B 的全关闭」仅在「注记路由 + :5 优先句被消费方采纳」读法下成立（裁决 :90-92 分层登记，本轮实读）；U 的 strict 收益本质 = U2 的 8 格错答→不答 + U3 的 1 格错答→正确，U4 零机器效果。

### 3(c) 收紧路线的绑定击穿面

行数不变 → **内容级零击穿**：T5「14 组 fixture」（V2:184）、重签件 §3「十四行逐行比对」（:56）/「14/14」（:148）、B2B_DESIGN:144「14 项」/:163 八类对账全部原样；镜像三行属 U2/U3/U4 同批处方（不属击穿）。仅触发**指纹换版登记**：乙矩阵 sha 变 → V2:46、重签件 :34、:153 条件 1；乙设计 sha 变（镜像）→ V2:45、重签件 :33、:153（裁决 §4.1 表 :66-77、统一清单 U2/U3/U4 级联行，本轮实读）。

## 4 「补对照行」与「分流表述」路线分析

### 4(a) 补对照行：需补几行、行数变化——★ 明示行数代价

| 目标格组 | 所需对照行（拟文，未实施） | 覆盖格数 | 修复什么 |
|:--|:--|:--|:--|
| none/empty/missing/dirty × re_*（8 M）+ expl_unknown × re_*（2 O） | **补A**（拟第 16 行）：state=post_read_error，preState=unknown，condition 含「跑前快照未采集或显式 unknown + 跑后 read_error 非空 ⇒ 独立 error 出口（码序 read_error 先于 unknown 出口，候选 :4643 先于 :4648）」 | 10 格 | 修 2 孤儿；对 8 误配格**加对冲** |
| absent × re_true（1 M，O1′）+ absent × re_none（1 O） | **补B**（拟第 17 行）：state=post_read_error，preState=absent_confirmed，condition 含「不得判 new_first_appearance（read_error 先于 ：4666 absent 分支）」 | 2 格 | 修 1 可达孤儿；对 O1′ 加对冲 |
| error × re_*（2 M，W2） | **补C**（拟第 18 行）：state=post_read_error，preState=error，condition 含「post_read_error 优先（N1 先于 error_pre_snapshot 出口 ：4652）」 | 2 格 | 对 2 误配格加对冲 |
| expl_unknown × 在场六型（6 O） | **补D**（可选，拟第 19 行）：state=unknown，preState=unknown，「未知不得默认等于不存在」 | 6 格 | 修 6 孤儿（全部不可达文本债） |
| present_nosh × re_true（W3） | **不需要新行**——:5 已同格正确声称；修法归属 = 收紧 ：13 或 :5 优先句压制，补行无效 | — | — |

**★★ 行数变化明示：补A/补B/补C 三行 → 矩阵 14→17（P3 情景，`_cf_enum_out.txt:252`「rows=17」）；加补D → 14→18（P4，:286）。任务书预警的 15/17 档落在 17。代价 = 增行击穿多处内容级绑定（§4(c) 十处：断言重写 + T5 重规约 + V2 内容批准 + 历史记录失配），且与裁决 :102/:106「C 不采」相抵——这不是改一个数字，是全链取证重做。**（值域核查：四行 preState ∈ {unknown, absent_confirmed, error}、state ∈ FRESHNESS_VERDICTS——不触发当年选项 C「preState=any 违值域」那条，B2B_DESIGN.md:142 本轮实读。）

### 4(b) 补对照行逐格效果：修孤儿，不消错答

「全 claimant 一致」裁决规则下，坏 claimant（:2/:4/:6）仍在，追加正确行不摘除错误行——**P3-strict MISLABEL 12→12 原样**（`_cf_enum_out.txt:252`；claimants 仅多了 16/17/18：:253-264），first-match 亦然（64/11/6）。补行直接修复的是 **ORPHAN**：P3 把 9 孤儿修掉 3（expl_unknown×re_* 2 + absent×re_none 1，:265-270 残留 6 = 在场六型）；P4 全消（69/12/0，:286）。可达 6 格：仅 absent×re_none 孤儿→OK（:351/:358），5 个错答格原样（:346-350）。**「让错答格旁边多一个正确答案」≠「错答格不再错答」**——对冲只让冲突自明，LOOSE 下本就自明（14/14 有 :5 对冲），STRICT 下 12 误配格 P3 后仍 12 误配。

### 4(c) 补对照行的绑定击穿面（逐处，全部本轮实读原文）

| # | 绑定处（本轮实读） | 击穿方式 | 后续义务 |
|--:|:--|:--|:--|
| 1 | `B2B_DESIGN.md:144`：「严格 JSON 数组，**14 项**…下表与之逐行一致」 | 「14 项」失真；镜像表 :146-161 须增 3-4 行 | 重写断言 + 镜像增补 + 乙设计指纹换版 |
| 2 | `B2B_DESIGN.md:163`：8 类逐条对账按**行位**引用（「第 1–2 行」…「第 14 行」） | 新行使行位引用漂移且不在八类叙述内 | 对账重写 |
| 3 | `V2:110`：「**14 数据行（:2-15**…）为机器可读唯一口径」 | 行数与行区间双失真 | 重写 + 短指纹登记（连带 V2:45-46/:66-67） |
| 4 | `V2 §4.2` 表 ：114-130：14 行五列收录表（无 condition 列，耦合件 ：86 同证） | 增 3-4 行 = **V2 正文内容改动** → 按先例需 V2 来源会话批准（pf2:231 转引；裁决 :242 未验项 3 在案） | 内容批准 + V2 指纹换版 |
| 5 | `V2:184`：T5「**14 组 fixture**…**14/14 match**」 | fixture 组数与断言目标行数失配 | **T5 重规约**（17/18 组）+ 重跑（V2:184 自记本轮未跑） |
| 6 | 重签件 `:56`：§3 标题「矩阵**十四行**逐行比对（三方…）」 | 标题与三方表行数失真 | 章节重写 + 重新取证 |
| 7 | 重签件 `:148`：五项必查「矩阵三方一致 **14/14**」 | 必查口径失真 | 断言重写 + 新一轮逐行取证 |
| 8 | 重签件 `:33`/`:34`（乙设计/乙矩阵指纹行）+ `:153` 条件 1「任一漂移即失效」 | 指纹漂移 → 既有 YES 自动作废 | 换版重签（**收紧路线同样触发本条**——非补行独有） |
| 9 | 重签件 `:154` 条件 2「三方 (verdict,confidence) 不分叉」 | JSON 增行而 V2 §4.2 不同步即三方分叉 | 三表必须同批同步 |
| 10 | `R3:42`：「**14/14 逐行 match**：本人以 14 组 fixture 逐一 exec 实跑」（历史记录） | 历史记录不可回改，增行后不再描述新矩阵 | 只能新增一轮 17/18 行取证，旧记录与新矩阵失配 |

与在案裁决的关系：裁决 :106「C 不采：14→15/17 行击穿至少六处内容级绑定（B2B_DESIGN:144『14 项』/:163 八类对账、V2:110『14 数据行』/:114/:184、重签件 §3:56/:148 五项必查 14/14），需 T5 重规约」——上述六处全部在上表内、引文逐字相符（本轮实读）；本表另补 3 处（重签件 ：154 条件 2、R3:42 历史失配、pf2:231 先例下的 V2 内容批准）+ 1 处共性（指纹换版）。裁决 :102 明示「C 不采」是裁决结论的一部分；**单方面补对照行 = 重开已裁事项**。

### 4(d) 不增行的替代：分流表述——两种形态，效果不同

- **形态一｜纯注记（不动前件）**：U3 的 ：5 注记 + 优先句、U4 的 ：4 分流句即此形态。**STRICT 键层零机器效果**（U4only-strict 60/12/9 = 基线，`_cf_enum_out.txt:190`；U3only-strict 仅 1 格 ：156）——本轮实证；LOOSE 层有效（U4only-loose 69/12/0 :212、U3only-loose 69/12/0 supp2 :177）。**强依赖「消费方按 condition 文本路由」**——现役无任何程序按 condition 文本做行匹配（裁决 :92 本轮实读；T5 只断言 fixture 四元组）。
- **形态二｜收紧+分流句合一（U2 实态）**：前件收紧 + 内嵌「见 :5 行」。strict 层错答消失（→孤儿），LOOSE 层全绿。**分流表述不是收紧的替代品，而是收紧的配套文本。**
- **结构性不可能**：「不增行且 STRICT 键层每格都有正确答案」做不到——strict 匹配键 = `preState` 字段 ∧ condition 前件（耦合件 :67 本轮实读），preState 字段受 B2B_DESIGN:142 四态值域约束为单值，一行不能同时持 unknown/absent_confirmed/error 三键；verdict 字段亦单值。这正是裁决 :106 判 C 不采、又把 B′（修订 :67 纪律或增 match_priority 字段）列为补证项而非处方的结构性原因（裁决 :236 触发条件 ④ 本轮实读）。

## 5 三方案决策表 + 复核回件 + 两方案可否并存

### 5(a) 三方案决策表（全部数字 = `_cf_enum_out.txt` 本轮复跑；「收紧」列以 U 为主行、T4 为参照行）

| 维度 | 收紧 condition（U2/U3/U4+镜像，行数不变） | 补对照行（+3~4 行，14→17/18） | 分流表述（:5 注记+优先句 / :4 分流句） |
|:--|:--|:--|:--|
| STRICT 暴露（M+O） | 21→**20**（M 12→3、O 9→17；T4：M 12→0、O 9→20） | 21→**18**（P3：M 12 不减、O 9→6）/ 21→12（P4：O 9→0） | 单用 21→**21**（机器层零效果）；与 U2 合并即 U |
| LOOSE 暴露 | 14→**0**（:128/:106） | 14→**14**（错答一格不消，:271/:299） | 14→**0**（需 U2 随批摘坏 claimant） |
| 是否引入新孤儿（STRICT） | **是**：+8（U）~+11（T4）格（错答→不答）——**变 ORPHAN ≠ 问题解决** | **否**：孤儿 −3（P3）~−9（P4） | 否 |
| 可达 6 格·STRICT 键层 | 6→**6**（3 MIS+3 ORP；T4 则 6 ORP） | 6→**5**（仅 absent×re_none 孤儿→OK） | 6→**6**（同 U） |
| 可达 6 格·LOOSE/注记路由读法 | 6→**0**（:366-372） | 6→5 | 6→**0** |
| 错答性质消除 | W1 文本层关闭；W2 文本层关闭（U4）；O1′ high 虚报**仅在 T4（:6 随批收紧）下机器层消失**，U 下 STRICT 残留（裁决 :223 可选 carve-out 属批准人裁量） | 错答格原样（对冲仅自明） | O1′/W2 误读文本消除（LOOSE 读法） |
| 增行 | **否** | **是**（14→17/18，§4(a) ★） | 否 |
| 绑定击穿面 | 指纹换版 5 处；**内容级零击穿**；T5/§3/八类对账不动 | 指纹换版 + **§4(c) 十处内容级击穿** | 同收紧（更小） |
| 对消费方契约的依赖 | STRICT 层不依赖；「全绿」断言依赖 LOOSE 读法（已分层登记，裁决 ：90-92） | **不依赖**（新行是真实行键，两口径同效） | **强依赖**（现役无程序读 condition 文本；触发条件 ④ 未满足） |
| 裁决/批准链 | **全链在案**：pf2 判定 A → row5 选项 B → 裁决采 B（:102）→ 统一清单；批准人 = 乙设计责任人（:108） | 与裁决 ：102/:106「C 不采」**相抵**；须满足 ：236 触发条件 ④ 重开裁决 | U3/U4 已在处方内，非独立选项 |

### 5(b) 可达 6 格 × 情景逐格状态（STRICT；`_cf_enum_out.txt:323-365` 本轮复跑 + `_cfv_enum_out.txt:64-69` 独立实现同值）

| 格 | S0 | T4（纯收紧） | U（U2/U3/U4） | P3/P4（补行） | PT（收紧+补行） |
|:--|:--|:--|:--|:--|:--|
| none × re_none | MIS | ORP | ORP | MIS | **OK** |
| none × re_true | MIS | ORP | ORP | MIS | **OK** |
| error × re_none | MIS | ORP | **MIS** | MIS | **OK** |
| error × re_true | MIS | ORP | **MIS** | MIS | **OK** |
| absent × re_true（O1′） | MIS | ORP | **MIS** | MIS | **OK** |
| absent × re_none | ORP | ORP | ORP | **OK** | **OK** |
| 合计 | 5 MIS+1 ORP | 6 ORP | 3 MIS+3 ORP | 5 MIS+1 OK | **6 OK** |

**STRICT 机器键层唯一能把可达 6 格清零的是组合（PT）**；单一方案均不行。

### 5(c) 复核回件登记（verdict 如实记）

- **verdict = confirmed**（本对比设计的复核回件，针对上一轮交付件 `_cf_counterpart_vs_tighten_20261109.md`）。绑定行（格式固定，本轮以 hashlib 实算复核同值）：

被核对象 SHA256 = 9878bb7ec170599dd8d74eacfa0a7be0806294d91d8be994a456ad6ed864ddb4，字节数 = 32840

- 复核七项全过：指纹（编排方 12 件 12/12 + 撰写人 15 件 15/15）；身份清单独立实现复现（基线 60/12/9、67/14/0 及 16 情景 tally 全 MATCH，含与 `_rv2_probe_20261109_out.txt:51/:72/:77/:81` 逐数核对）；核心检查确认撰写人未把「收紧」与「补对照」混为一谈、未把「变成 ORPHAN」说成「问题解决」（主交付件 ：96-99/:101-107/:129/:180/:195 逐行核过）；绑定击穿面十处逐处实读命中；分流表述两形态与死指针修订点确认；最小必要改动六处与裁决改 1-6 对应；无越界。
- 三处**非阻断瑕疵**随件登记（复核原文如实转录）：(a) 上一轮证据所引 `_cf_enum_out.txt` 行号过期（引 ：48-198/:200-263/:264-286，现版 410 行实为 ：47-322/:323-386/:387-409——**本件已按现版行号重引**）；(b) 上一轮回件 orphanCells 摘要句「absent×re_none…宽读也无行」措辞含混（对 ：2/:3 宽 preState 键读法为真，对 LOOSE 全口径不真：`_se_enum_out.txt:139` [5] 实读）；(c) 上一轮 §5(c) 把 absent×re_none 的 LOOSE 接管归因于「U3 的 ：5 注记」，机制实为 ：5 宽键在基线即覆盖（U3 注记对该格无增量）——结论均不受影响。
- 另如实登记两个不同对象的状态，不混淆：**裁决件自身整体状态 = unconfirmed**（其复核回件 verdict=refuted，RULING_MATRIX_AB.md:248 本轮实读）；**本对比设计复核 verdict = confirmed**。

### 5(d) 两方案可否并存

**机制上能并存、裁决层不并存。**
- 机制正交：收紧改既有行前件（行数不变、消错答），补对照增行（消孤儿、给错答格加对冲），互不抵消——组合情景 **PT（T4 收紧 + 补A/补B/补C）实证 strict 75/0/6**（:314；剩余 6 孤儿 = expl_unknown×在场六型，全部不可达文本债）、**LOOSE 81/0/0**（:321）、可达 6 格 6/6 OK（:359-365）；补行与收紧后的 ：2/:4 无格冲突（那些格收紧后无 claimant，新行恰好接住），LOOSE 无新错答。
- 裁决层不并存：补对照行 = 选项 C 族动作，被裁决 :102/:106 明判「C 不采」，再立项条件 = :236 触发条件 ④（消费方匹配契约实证为严格合取键且拒绝注记路由）。**因此：先收紧（已裁决处方、批准链完整），补对照作为条件触发的二期，不得与 U2/U3/U4 同批混入。**

## 6 结论

1. **最小必要改动（可达 6 格，不增行）= 统一清单六处 = U2 + U3 + U4 + 镜像 ：148/:150/:151**（即裁决采 B 的改 1-6）：none×re_* 两格由 U2 收紧消错答（STRICT→孤儿+分流句、LOOSE→:5 接管 OK）；error×re_* 两格由 U4 文本层关闭（STRICT 前件不变、残留如实登记）；absent×re_true（唯一 high 虚报）由 U3 注记文本层收容（STRICT 残留，:223 可选 carve-out 属批准人裁量）；absent×re_none 可达孤儿由 :5 宽键 LOOSE 接管（STRICT 保持不答）。**镜像三行是必要部分**：只改 JSON 不同步 ：148/:150/:151 即双源不一致，且 T2/T5/重签件 ：154 条件 2 全抓不到（静默通过）。
2. **与 U2/U3/U4 兼容还是冲突（U2-U4 兼容性）**：**内容兼容**——补A/补B/补C 与收紧后的 ：2/:4 无格冲突、LOOSE 同值无新错答（P3/PT 的 LOOSE 均 81/0/0 实证）；**裁决层冲突**——补对照 = C 族，被 ：106 不采，不得作为 U2/U3/U4 同批附件，须走触发条件 ④ 再裁决；**文本一处可选修订点**——U2 分流句「见 ：5 行」在 strict 键下对非 present pre 是死指针（M2b ：77），若二期真补行宜改「见 ：5 行与新增 read_error 承载行」，U2 文本无须预改。
3. **两修法不可混为一谈（结论重申）**：收紧把错答变不答（或由正确行接管），行数不变，绑定量小；补对照给错答格旁边加正确答案、消孤儿，但行数 14→17/18，击穿十处内容级绑定并与在案裁决相抵。若只能选一个：**选收紧**（零内容级击穿、批准链完整、错答比不答危险且五层兜底不变——STRICT_EXPOSURE:161）。STRICT 键层可达 6 格全清零的唯一路径 = 组合 PT，但其增行代价与裁决相抵，只能经触发条件 ④（B′ 或二期补行）立项。
4. **未改任何文件声明**：本轮对被核 15 件 hashlib 实算与编排方基线/在档值逐字节一致（15/15 MATCH）= 只读域零改动硬证；绝对只读域与两件台账零写入；上一轮 4 件与复核人 3 件既有件零改动。本轮写域新增仅两件：**本件 `COUNTERPART_FIX.md`** 与枚举复跑输出 `_cfx_enum_out.txt`（与既有 `_cf_enum_out.txt` 逐字节一致，作零漂移证据留档）。未 commit、未 push（未执行任何 git 写命令）；零真机、零采样。
5. **未验项（如实登记，不补造）**：
   - 真机实流未跑（零真机）；可达性评级为推理评级（STRICT_EXPOSURE:159 自记未实测）；一手探针 `_mr_probe1_out.txt` 未开读（可达栏引证为转引 STRICT_EXPOSURE §4.1）。
   - T1/T2/T5 门禁未跑（沿 V2:180-184 在档自记）；本仿真不能冒称门禁通过。
   - claimant 覆盖谓词为手工编码（自然语言 condition 无法完全机器化）；LOOSE 宽键与 :5 优先句压制是复现在案数字的必要建模选择（去宽键 ⇒ 6 孤儿，STRICT_EXPOSURE:55 转引在案；U_NP 情景 = 不采优先句对照）。
   - pf2、row5（源①/源②）原文未直读（经统一清单/裁决件转引并在案）；`_review_probe_r3.py:434/:457/:460` 为转引。
   - 补A/补B/补C/补D 拟文未做逐字镜像推演（B2B_DESIGN 镜像行、V2 §4.2 行、重签件 §3 行的对应改文未起草）——若二期立项按 §4(c) 清单补齐。
   - 本轮 Bash 命令计数 4 次（指纹脚本 1、inline hashlib 2、枚举复跑+cmp 1）+ grep 1 次 + Read 若干；无任何写域外写入。
