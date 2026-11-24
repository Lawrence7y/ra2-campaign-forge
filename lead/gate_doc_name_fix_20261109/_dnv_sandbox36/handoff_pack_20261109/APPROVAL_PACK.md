# APPROVAL_PACK —— 九条文本订正批准包·交付件（2026-11-09）

- 撰写：批准包交付轮（动态工作流子代理）。本件汇总整编包 `lead/handoff_pack_20261109/`（15 件 `_hp_` 文件）与复核回件，供批准人一次读完、照单执行。
- 纪律：零真机（未启动 gamemd.exe / ra2loader / YURI.exe、未 taskkill、未读活进程内存）；零采样代码；未 commit、未 push；唯一写域 = `lead/handoff_pack_20261109/`；Python 一律 `python -I -X utf8` + 绝对路径；指纹 hashlib 实算。
- 只整编不仲裁：九条改文逐字照抄前序写域正本，一个字未改（本件全部逐字块经 `_hp_ap_checks.py` 逐字节比对，见 §5.1）；未决项照列不替决。

## 1 一页纸总览

| 项目 | 值 |
|:--|:--|
| 内容订正条数 | **9 条**（U1–U9） |
| 落点 | **9 行、4 个文件**：`STATE_MATRIX.json` :2/:4/:5（U2/U4/U3）、`B2B_DESIGN.md` :148/:150/:151（U5/U7/U6）、`_n4v2_B_EXECUTION_SPEC_V2.md` :91（U1）、`MATRIX_DEFECT_REACHABILITY.md` :154/:146（U8/U9） |
| 换版次数 | 级联各件最多 1 次共 **4 次**（矩阵 1 + 设计 1 + V2 1 + 重签件 1，UNIFIED_TEXT_FIX §6.2）；U8/U9 不在绑定链，受核件落盘后自行登记新指纹 |
| 被改既有件上限 | 4 个内容件 + 重签件换版 + 两台账补登 = **最多 7 件受触** |
| 未决项 | **16 项**（P1–P16，集中列于 `_hp_PENDING_AND_SIGNOFFS.md` 与本件 §5.3；P1–P3 = 任务下发已知①②③） |
| 签字 | 3 方批准（乙设计责任人 / V2 来源会话 / 受核件主管侧）+ 重签侧换版 + 编排方台账补登 |
| 复核 verdict | **partial ⇒ unconfirmed**（三处瑕疵，均已定位；本交付轮逐一复验，见 §3.4、§5.1） |

**一句交接语**：九条改文逐字整编自前序写域（U1/U2←pf2、U3/U4←row5、U5/U6/U7←_m5_cells.json＋U5U6_MIRROR_TEXTS、U8/U9←W2），本轮三方同文逐字节比对全过、JSON↔B2B 映射 14 行全等、指纹 13/13 与编排方基线一致；批准人按 §5 指引分批执行（六处同批 → V2 一次重发 → 重签件收尾 → U8/U9 与台账），16 项未决无一代决。

## 2 上游指纹（十四件）＋ 九条逐条核对表

### 2.1 上游指纹（编排方指纹表 14 件，本轮实跑复算）

实跑命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\handoff_pack_20261109\_hp_fp_verify.py`（输出 13 行 OK + 1 行 MISSING_AS_EXPECTED + 1 行 EXTRA_OK）与 `_hp_ap_checks.py`（UNIFIED_TEXT_FIX 旁证实算）。

| # | 路径 | SHA256 | 字节数 | 本轮复跑 |
|--:|:--|:--|--:|:--|
| 1 | lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md | b1231ccb8b80c5200e2ff33b15e09ae52b0452a1481dfc7989730f7da16eda5b | 22048 | OK |
| 2 | lead/v2_precision_fix_20261108/_pf2_findings_20261109.md | 4aef8957094008262d980640836ab0aec3e797f892b25fe8ff02b6aa87957fe4 | 7966 | OK |
| 3 | lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md | 6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8 | 29818 | OK |
| 4 | lead/w2_samecause_20261109/W2_SAME_CAUSE.md | 75a0369b97f72f9d615ced86c580c6e63bfcce4f29de1c86bd74e8542aa5c895 | 19552 | OK |
| 5 | lead/text_fix_unified_20261109/_uf_UNIFIED_FIX_LIST_20261109.md | 441b073a39a2ac195d90d43e3ba85f3c2202d5fafce31bec9c96e000a01e0923 | 25095 | OK |
| 6 | lead/u5u6_mirror_20261109/_m5_cells.json | ce89f6463d1b2fb64deae55f869db4d94086bcb4bce868cec3870317b2c63bf3 | 2525 | OK |
| 7 | lead/u5u6_mirror_20261109/U5U6_MIRROR_TEXTS.md | f320a80110806e6b57281988085d40776b43e719123db29cdb6564fe68c6c545 | 24897 | OK |
| 8 | lead/counterpart_fix_20261109/COUNTERPART_FIX.md | 编排方基线 = MISSING；**交付时点实存** e291f5a8f8b2c303b31e7f06989233e122460d9838817271fa425cae066ff416 | 32830 | MISSING_AS_EXPECTED（06:18 新出现，见 §3.4-②） |
| 9 | lead/strict_exposure_20261109/STRICT_EXPOSURE.md | 3a4b1bb7cf7f0bd501b3e99d575c4907dd0e17f5557dd0b8826e5fb07fe2bdc8 | 23798 | OK |
| 10 | lead/b2b_design_20261106/STATE_MATRIX.json | 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016 | 3558 | OK |
| 11 | lead/b2b_design_20261106/B2B_DESIGN.md | 565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf | 66735 | OK |
| 12 | lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md | c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801 | 28897 | OK |
| 13 | lead/PENDING_DECISIONS.md | 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 | 52419 | OK |
| 14 | lead/GOAL_THREE_TARGETS_20261018.md | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 759518 | OK |
| 补 | lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md（U8/U9 目标件，编排方表外补登记） | cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6 | 27825 | EXTRA_OK |
| 旁 | lead/text_fix_unified_20261109/UNIFIED_TEXT_FIX.md（汇总件，非编排方表内） | ec0fb8ec47cfb71be5b28bc8a76f9152a6cbd377e741e7be1902a0958fbba154 | 42172 | 与 U5U6_MIRROR_TEXTS §2.1 转引值一致 |

### 2.2 九条总表

| # | 目标件:行 | 动作 | 需谁批准 | 成组 | 完整性 |
|:--|:--|:--|:--|:--|:--|
| U1 | `_n4v2_B_EXECUTION_SPEC_V2.md:91` | 「删除行数 0」五字替换 | **V2 来源会话**（定版件签发人；pf2 §3.6:111、重签件:168 预留） | 独立；V2 重发宜在六处定稿后一次完成 | 齐；字形二选一（P4） |
| U2 | `STATE_MATRIX.json:2` | condition 收紧（去「跑后任意文件状态」＋分流句） | **乙设计责任人**（pf2 §4.6:200、row5 §5.4-1） | 六处同批（P3），与 U5 成对 | 齐；两源同文（pf2:193＝row5:131 明写原样） |
| U3 | `STATE_MATRIX.json:5` | condition 追加码序注记（preState 不动） | **乙设计责任人**（row5 §5.4-1） | 六处同批，与 U6 成对 | 齐；「去外侧「」」判读待确认（P5） |
| U4 | `STATE_MATRIX.json:4` | condition 加分流句 | **乙设计责任人**（row5 §5.4-1）；可推迟须登记保留 W2 | 六处同批，与 U7 成对 | 齐；拼接点源件未逐字指明（P6，推荐已给出） |
| U5 | `B2B_DESIGN.md:148` | JSON:2 镜像同步（第 3 列） | **乙设计责任人**（row5 §5.4-2） | 六处同批，与 U2 成对 | 齐；正本系后补起草件（两汇总件如实标「未提供」，时间线自洽） |
| U6 | `B2B_DESIGN.md:151` | JSON:5 镜像同步（第 3 列） | **乙设计责任人**（同 U5） | 六处同批，与 U3 成对 | 齐；同 U5（后补起草正本） |
| U7 | `B2B_DESIGN.md:150` | JSON:4 镜像加句（同句无反引号） | **乙设计责任人**（同 U5）；可推迟性同 U4 | 六处同批，与 U4 成对 | 齐；拼接点同 U4（P6） |
| U8 | `MATRIX_DEFECT_REACHABILITY.md:154` | W2 链措辞收窄（整句替换） | **源③未载明**（P9：编排方指派/主管侧认领） | 独立；与 U9 同批为宜 | 批准人缺（P9）；行首前缀去留（P7）；包内原文引文 1 字符差（复核①，本件已录实文） |
| U9 | `MATRIX_DEFECT_REACHABILITY.md:146` | 评级格注记（W2 行） | 同 U8（未载明，P9） | 同 U8 | 批准人缺（P9）；替换/追加形态未指明（P8）；量级全部推理未验 |

### 2.3 逐条核对（原文 / 改后逐字 ＋ 出处）

#### U1 —— V2:91「删除行数 0」→ 实测 +255/−13

目标：`lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md` 第 91 行（V2 定版件，指纹 c7bcf035…/28,897）。

原文逐字（实读 :91，比对 True）：
```
- 允许范围 = **且仅 =** 上表九 hunk；删除行数 0；范围外任何改动（含 H 编号重排、新增 hunk、E 判据块）均 FAIL。九 hunk 的 `-` 侧覆盖区间均不含 E 判据块 `5984-5990`（`B2B_DESIGN.md:635` 本轮实读）。
```
改后逐字（只替换「删除行数 0」五字，其余语句不动——pf2:101/:107；源件处方原文 = `V2_PRECISION_FIX_PROPOSAL.md` §3.5:104，比对 True）：
```
九 hunk 内实测 +255/−13（替换位删除 13 行：H03=1、H04=9、H05/H06/H09 各 1；R3:31,43 与 CANDIDATE_LF.diff 实测一致）；允许范围外删除 = 0
```
同源格式变体（P4，批准人二选一）：`_pf2_findings_20261109.md:27` 同文，但末句作「**允许范围外删除 = 0**」（多粗体一对；本轮实跑验证：变体去粗体后与 pf2:104 逐字节相同，语义同、格式异）。

出处：pf2 §3.5:104（处方）、§3.6:111（批准人与级联）；重签件 :116（+255/-13 分解）、:168（「措辞修订待定版件处理」预留）。
需谁批准：V2 来源会话。改后 V2 指纹必变 → 重签件 §2 第 6 行（:35）+ :153 生效条件 1 换版登记。

#### U2 —— STATE_MATRIX.json:2 condition 收紧

目标：`lead/b2b_design_20261106/STATE_MATRIX.json` 第 2 行（指纹 1d4ccc93…/3,558，16 行/14 数据行）。

原文逐字（实读 :2，比对 True）：
```
  {"state":"unknown","preState":"unknown","condition":"pre=None / {} / 缺 state / 脏值（跑前快照未采集或采集未完成），跑后任意文件状态","verdict":"unknown","confidence":"none","usableAsCrashEvidence":false},
```
改后 condition 逐字（源件处方原文 = pf2 §4.5:193；row5 §4.3-B:131 明写「pf2 §4.5 :193 文案原样」——两源同文，三方比对 True：pack＝_m5_cells.json json2_new＝pf2:193）：
```
pre=None / {} / 缺 state / 脏值（跑前快照未采集或采集未完成），跑后读取正常（post.read_error 为空）；post.read_error 非空时先落 post_read_error（码序 read_error 出口先于 unknown 出口，候选 :4643 先于 :4648，见 :5 行）
```
该行其余键值（state/preState/verdict/confidence/usableAsCrashEvidence）不动（pf2:196）。

出处：pf2 §4.5:190-196、§4.6:200；row5 §4.3-B:131；上游登记 R3:47 / V2:132 / 重签件:89。
需谁批准：乙设计责任人。改后乙矩阵指纹变 → V2:46 + 重签件 §2 第 5 行（:34）+ :153 生效条件 1。

#### U3 —— STATE_MATRIX.json:5 condition 追加码序注记

目标：同 U2 件第 5 行。

原文逐字（实读 :5，比对 True）：
```
  {"state":"post_read_error","preState":"present","condition":"跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口","verdict":"post_read_error","confidence":"none","usableAsCrashEvidence":false},
```
追加文本逐字（源件处方原文 = row5 §4.3-B:132；源件外侧「」为引注记号——该判读经复核 F1 更正后依据成立，待批准人确认 = P5）：
```
（★ N1 码序 read_error 出口先于一切 pre 分支：候选 :4643-4646 先于 :4648 unknown / :4652 error / :4657 无件 / :4666 absent_confirmed / :4672 起 present 支；pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行，preState 列的 present 为最常见登记态，匹配以本 condition 为准）
```
改后完整 condition 逐字（＝ row5:132 去外侧「」，本轮实跑去「」后逐字节相同；＝ _m5_cells.json json5_new）：
```
跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口（★ N1 码序 read_error 出口先于一切 pre 分支：候选 :4643-4646 先于 :4648 unknown / :4652 error / :4657 无件 / :4666 absent_confirmed / :4672 起 present 支；pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行，preState 列的 present 为最常见登记态，匹配以本 condition 为准）
```
preState 字段不动（row5:132：写 "any" 违 B2B_DESIGN.md:142 四态值域契约，域覆盖由 condition 文本承载）。

出处：row5 §0/§3.1/§4.3-B:132（选项 B 推荐）；pf2 §4.7-1:204 只列「放宽 preState」分支（两源不矛盾，UNIFIED_TEXT_FIX §5.1 组(a)）。
需谁批准：乙设计责任人。级联同 U2（同文件同批 → 指纹一次性变化）。

#### U4 —— STATE_MATRIX.json:4 condition 加句（随批关闭 W2；可推迟须登记）

目标：同 U2 件第 4 行。

原文逐字（实读 :4，比对 True）：
```
  {"state":"error","preState":"error","condition":"跑前采集抛异常（snap.error 非空）⇒ 独立 error 出口，不降级、不静默、不给 high","verdict":"error_pre_snapshot","confidence":"none","usableAsCrashEvidence":false},
```
加句逐字（源件处方原文 = row5 §4.3-B:135「JSON:4 condition 加」；拼接点源件未逐字指明 = P6）：
```
（post.read_error 非空时仍先落 post_read_error，见 :5 行）
```
改后推荐全文逐字（＝ _m5_cells.json json4_new_recommended，推荐拼接点 =「独立 error 出口」之后；本轮实跑验证该全文＝原文条件串按推荐点机械拼装的结果）：
```
跑前采集抛异常（snap.error 非空）⇒ 独立 error 出口（post.read_error 非空时仍先落 post_read_error，见 :5 行），不降级、不静默、不给 high
```

出处：row5 §4.3-B:135（随批，不加则登记中如实保留 W2）；W2 本体 = W2_SAME_CAUSE.md §4.2:100。
需谁批准：乙设计责任人；row5 明示可推迟，推迟须登记。级联同 U2。

#### U5 —— B2B_DESIGN.md:148 镜像同步（JSON:2 的设计镜像）

目标：`lead/b2b_design_20261106/B2B_DESIGN.md` 第 148 行（指纹 565771d8…/66,735，693 行）第 3 列 condition。

原文整行逐字（实读 :148，比对 True）：
```
| `unknown` | `unknown` | `pre=None` / `{}` / 缺 `state` / 脏值（未采集或采集未完成），跑后任意 | `unknown` | `none` | `None` | `false` |
```
改后整行逐字（改文正本 = `_m5_cells.json` U5.new_condition_cell 起草、`U5U6_MIRROR_TEXTS.md` §3.1 成文交付；本轮实跑验证＝原行仅第 3 列换 cell、其余 6 列逐字节不动；镜像件含同文行 True）：
```
| `unknown` | `unknown` | `pre=None` / `{}` / 缺 `state` / 脏值（未采集或采集未完成），跑后读取正常（`post.read_error` 为空）；`post.read_error` 非空时先落 `post_read_error`（码序 `read_error` 出口先于 `unknown` 出口，见 :5 行） | `unknown` | `none` | `None` | `false` |
```
JSON 侧 ↔ B2B 侧差异（白名单，U5U6_MIRROR_TEXTS §3.1）：仅反引号＋既有缩写「跑前快照」＋候选行号指针「候选 :4643 先于 :4648，」（未改行省略行号的既有惯例）；无语义分叉。

出处：镜像义务 = B2B_DESIGN.md:144「下表与之逐行一致」（实读 ✓）；row5 §4.3-B:133/§4.5-1:153；pf2 §4.7-2:205。
需谁批准：乙设计责任人。改后乙设计指纹变 → V2:45 + 重签件 §2 第 4 行（:33）+ :153 生效条件 1。

#### U6 —— B2B_DESIGN.md:151 镜像同步（JSON:5 的设计镜像）

目标：同 U5 件第 151 行第 3 列。

原文整行逐字（实读 :151，比对 True）：
```
| `post_read_error` | `present` | 跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口 | `post_read_error` | `none` | `None` | `false` |
```
改后整行逐字（正本 = `_m5_cells.json` U6.new_condition_cell、`U5U6_MIRROR_TEXTS.md` §3.2；本轮实跑验证＝仅第 3 列换 cell；`preState` 列保持 `present` 不动）：
```
| `post_read_error` | `present` | 跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口（★ N1 码序 `read_error` 出口先于一切 pre 分支；pre 任意态——`unknown`/`absent_confirmed`/`present`/`error`——+ `read_error` 均落本行，`preState` 列的 `present` 为最常见登记态，匹配以本 condition 为准） | `post_read_error` | `none` | `None` | `false` |
```
JSON 侧 ↔ B2B 侧差异（白名单，§3.2）：B2B 侧省略候选行号指针串「：候选 :4643-4646 先于……present 支」（指针级，既有省略惯例）；其余仅反引号。

出处：B2B_DESIGN.md:144（实读 ✓）；row5 §4.3-B:133「镜像必改」。
需谁批准：乙设计责任人。级联同 U5。

#### U7 —— B2B_DESIGN.md:150 镜像加句（JSON:4 的设计镜像，同句无反引号）

目标：同 U5 件第 150 行第 3 列。

原文整行逐字（实读 :150，比对 True）：
```
| `error` | `error` | 跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口 | `error_pre_snapshot` | `none` | `None` | `false` |
```
改后整行逐字（加句 = 源定同句 row5:135 逐字，cell 端拼接、无反引号 =「同句」字面要求——U5U6_MIRROR_TEXTS §3.3；本轮实跑验证＝仅第 3 列换 cell）：
```
| `error` | `error` | 跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口（post.read_error 非空时仍先落 post_read_error，见 :5 行） | `error_pre_snapshot` | `none` | `None` | `false` |
```
JSON:4 既有尾句「，不降级、不静默、不给 high」为白名单差（原 :150 即无此尾句，非新差）。

出处：row5 §4.3-B:135「B2B_DESIGN.md:150 镜像同句」；镜像义务 B2B_DESIGN.md:144。
需谁批准：乙设计责任人；可推迟性同 U4。级联同 U5。

#### U8 —— MATRIX_DEFECT_REACHABILITY.md:154 W2 链措辞收窄（整句替换）

目标：`lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md` 第 154 行（§4.2 最短触发链第 2 条；指纹 cd03a91a…/27,825，编排方表外补登记）。

原文逐字（**受核件实文**，实读 :154；注意 ：6623 处为全角冒号 U+FF1A）：
```
2. **W2**：make_pre 在 ：6623 对载体 except.txt 采集抛异常（AV 瞬时锁/ACL/路径异常 → error 态，out:146-148）+ 同趟收尾复制又失败（同一持续根因横跨 pre/post 两时点可一次造成）→ read_error 先截（out:26 vs out:28）→ :4 声称 error_pre_snapshot 与实码 PRE 不符。
```
（`_hp_U8.md` 页引文在上处为半角「:」（U+003A），与实文恰差这 1 字符、等长——复核瑕疵①，本交付轮逐字符比对复验成立（diff 数 = 1，位置 21）。以本件所录实文为准；改后文不受影响。）

改后逐字（源件提案原文 = W2_SAME_CAUSE.md §5.2:122 引用块，本轮实跑 pack 改后＝该引用块内容逐字节相同；整句替换，行首列表前缀「2. **W2**：」去留 = P7 待定，按文义 = 保留前缀、其后链文整句替换）：
```
make_pre 在 :6623 对载体 except.txt 采集抛异常（源读面持续阻断：ACL 拒读〔目录继承 deny-ACE，跨文件重建仍持续——写域探针实证〕/AV 对该路径持续拦截 → error 态；AV 瞬时锁非持续根因，双时点命中需两次独立竞态；路径异常在 py3.12.10 实测〔非法字符/ENOTDIR/超长〕均被 exists() 吞为 absent_confirmed，不产 error 态）+ 同趟收尾复制对同一源路径再失败（同一 ACE/拦截持续 ⇒ 一因双时点；游戏句柄〔T0 未启动、term 成功即句柄随进程终止被内核关闭〕与磁盘满〔仅写侧〕均只在收尾时点成立，不能单独桥接）→ read_error 先截（out:26 vs out:28）→ :4 声称 error_pre_snapshot 与实码 PRE 不符。
```

出处：W2 §5.2:118-124（三选一结论「部分同源」§4.1:82-90；复核 verdict=confirmed §5.1:108）。
需谁批准：**源③未载明**（§5.2 只「描述，不改那件」）——P9，编排方指派或批准人自行认领。

#### U9 —— MATRIX_DEFECT_REACHABILITY.md:146 评级格注记（W2 行）

目标：同 U8 件第 146 行（§4.1 汇总表 W2 行「触发条件现实性评级」格）。

原文逐字（评级格，实读 :146 行内该格，比对 True）：
```
**罕见**（同根因双时点；评级为推理）
```
改后逐字（源件建议注记原文 = W2_SAME_CAUSE.md §5.2:124；**源件未指明整格替换还是格内追加 = P8**。源句以句号结尾，`_hp_U9.md` 页引文略去该末句号——属源件行文标点，随 P8 一并由批准人定）：
```
「罕见」仅限**源读面持续阻断**子集（deny-ACE 为环境常量、台账可证伪；AV 持续拦截 ~1e-5–1e-3）；AV 瞬时锁双击 ~1e-6–1e-4、两独立因 ~1e-7–1e-5（均极罕见档；全部为推理、未验）。
```
量级全部为推理、未验（源③ §4.2:96-98 自记；零真机未实测）。

出处：W2 §4.2:94（现措辞按其括号内含「AV 瞬时锁/ACL/路径异常」读偏高，需随 §5 修正措辞收窄后方可维持）、§5.2:124。
需谁批准：同 U8（源③未载明，P9）。对照备注：同表 :147（O1 行）另有评级格「**罕见**（句柄残留/AV 锁/磁盘满；评级为推理）」——不在九条内，本包不动（本轮实读 :147 在案）。

## 3 九条之间的依赖与矛盾检查 ＋ 发现的问题

### 3.1 U2-U4 ↔ U5-U7 映射核对（本轮实跑）

- 成对关系：U2↔U5（JSON:2↔B2B:148）、U3↔U6（JSON:5↔B2B:151）、U4↔U7（JSON:4↔B2B:150）。
- 全表映射 `i ↔ 148+(i−2)`：STATE_MATRIX.json 数据行 i=2..15 ↔ B2B_DESIGN.md 表行 :148..:161，14 行 × 5 字段（state/preState/verdict/confidence/usableAsCrashEvidence）逐行比对 **ALL EQUAL**（`_hp_ap_checks.py` 输出）；STATE_MATRIX.json 为严格 JSON、json.loads = 14 项。
- 单侧落盘即破 B2B_DESIGN.md:144「下表与之逐行一致」硬声明，且该不一致会静默通过 T2/T5/重签件:154 条件 2 全部既定门禁（row5 §4.5-2、U5U6_MIRROR_TEXTS §1 生效前提（硬））——六处同批 = P3，强制前提非可选。

### 3.2 U1 与换版的关系

- V2 对矩阵/设计**零行级引用**：`grep` 模式 `B2B_DESIGN\.md:1[45][0-9]|STATE_MATRIX\.json:[0-9]` 于 V2 全文 = **0 命中**（本轮实跑）→ U1 改文文本无需随 U2-U7 同步，连带面 = 纯指纹换版（V2 §2.1 :45/:46 两绑定行刷新，本轮实读两行原文）。
- 顺序：U1 的 V2 重发宜在六处定稿后**一次**完成（:91 改文 + :45/:46 刷新）；若先改 V2 再改矩阵/设计，V2 需重发两次（UNIFIED_TEXT_FIX §6.2-2）。
- 换版级联（整编实读 + 重签件本轮实读锚定）：U2-U4 → STATE_MATRIX 新指纹 → V2:46 + 重签件 §2 第 5 行（:34）+ :153 生效条件 1；U5-U7 → B2B 新指纹 → V2:45 + 重签件 §2 第 4 行（:33）+ :153 条件 1；U1 → V2 新指纹 → 重签件 §2 第 6 行（:35）+ :153 条件 1。重签件 :153 生效条件 1 原文（实读）：「**指纹稳定**：母本/候选/乙矩阵/V2/台账（§2 表 12 件，另含 CANDIDATE_LF.diff）保持 §2 绑定值，任一漂移即失效」。

### 3.3 U8/U9 与源件其他部分

- **P10（矛盾登记，指出不调解）**：受核件 :90 载旧措辞「同一持续根因（句柄/ACL 横跨两时点）可一次造成两半」（本轮实跑子串命中 True），与 U8 将 :154 收窄为「源读面持续阻断」后相抵（W2 §3 R1/R6：句柄 T0 结构性不成立/term 成功即句柄关闭；ACL 仅 deny-ACE 持续形态桥接；路径异常不产 error 态）。:90 不在九条内，包不代拟改文，需主管侧决定是否另立订正。grep 定位（本轮实跑）：命中行 = 1/12/71/77/79/86/89/90/146/147/154/180。
- **P14（未验）**：U8/U9 目标件不在 V2 §2.1 与重签件 §2 两绑定表内——两文件 grep `MATRIX_DEFECT|matrix_reach` 均 0 命中（本轮实跑）；**是否另有他件按指纹绑定 = 未验**。
- :147（O1 行评级格）不在九条内，不动（本轮实读 :147 在案）。

### 3.4 发现的问题（复核三瑕疵全部复验 ＋ 交付时点新观察）

复核 verdict = **partial**（按规则标 **unconfirmed**）。三处瑕疵本交付轮逐一复验（`_hp_ap_checks.py` 实跑）：

1. **瑕疵①（U8 原文引文 1 字符差）——复验成立**：`_hp_U8.md` 引文 vs 受核件实 :154 等长、diff 恰 1 字符（位置 21：引文半角 `:` U+003A，实文全角 `：` U+FF1A）。改后文不受影响（改后＝W2:122 逐字节相同）。本件 §2.3-U8 已录实文。
2. **瑕疵②（P11/附录A「域内仅三件」过时）——复验成立且进一步变化**：`lead/counterpart_fix_20261109/` 本轮 ls 实跑 = **9 件**（复核时 7 件）；`COUNTERPART_FIX.md`（32,830 B，mtime 06:18）**在复核之后、本交付轮之前新出现**，故 `_hp_fp_verify.py` 现输出 `MISSING_AS_EXPECTED` 并附实测指纹（e291f5a8…/32830）而非 ABSENT。**内容结论仍成立**：对 `COUNTERPART_FIX.md` 与 `_cf_counterpart_vs_tighten_20261109.md` 的九条改文片段探针（9 片段＋9 条改文全文），仅命中谓词级引文（前者 F5×1，后者 F2/F3/F7），**九条改文全文 0 命中**——「无一改文出自该域」在交付时点仍真。P11 的「缺失」登记按其登记时点保留，交付时点状态以本段为准（是否补登/改写 P11 = 编排方裁量，不代决）。
3. **瑕疵③（P1 行/总览 §4.1 引 row5:138 误）——复验成立**：「可接受但不完整」实文在 **row5:129**（grep 唯一命中），:138 实际承载「采 A 必须同步 :148 并如实登记 W2/O1 残留」（子串命中 True）。引用坐标应以 :129 为准，P1 决断内容本身不受影响。
4. **如实记录（非缺陷）**：U9/P10 引文略去源句末句号（源件行文标点，随 P8 形态未决）；`lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md` 为第三件既有 MM（包未声称涉它，本轮未检查其内容）。
5. **无「两源件改文互相矛盾」情形**：U2 两源同文（row5:131 明写「原样」）；U5/U6 汇总件「未提供」与后补正本为时间线关系非矛盾——未触发「停止该条整编」条款。范围准冲突①（P1：pf2 §4.5:196「最小修复只动一行」vs row5 §4.3-B 选项 B 六处，:129 评 A「可接受但不完整」）文字可调和、执行互斥，照列不替决（P1）；U1 字形准冲突②（P4）同。
6. **交付时点脚注**：`_hp_APPROVER_RUNBOOK.md` 第 0 步预期「1 行 ABSENT」已因瑕疵②过时——现预期为 1 行 `MISSING_AS_EXPECTED`（附实测指纹）；批准人按 §5.2 第 0 步的新预期执行。

## 4 批准包目录结构与每份内容大纲

唯一写域 `lead/handoff_pack_20261109/` 现存 18 件（15 件整编产出 ＋ 复核脚本 ＋ 交付轮 2 件）：

| 文件 | 大纲 |
|:--|:--|
| `_hp_OVERVIEW.md`（5,512 B） | 一页纸总览：9 条/9 行/4 文件、换版 4 次级联图、已知未决①②③、P10/P11 新登记 |
| `_hp_U1.md`…`_hp_U9.md`（9 件，1,806–3,705 B） | 每条一页：目标件:行、原文逐字、改后逐字、出处（文件:行）、需谁批准、依赖关系 |
| `_hp_PENDING_AND_SIGNOFFS.md`（6,991 B） | 未决 16 项 P1–P16（每项：出处/决断人/影响条目）＋ 签字 5 方（谁签什么）＋ 沿登未验 6 项 |
| `_hp_APPROVER_RUNBOOK.md`（4,968 B） | 第 0–8 步操作指引（命令可照做）＋ 部分批准成组规则 |
| `_hp_APPENDIX_FINGERPRINTS.md`（6,059 B） | 14+1 件指纹绑定行、九条改文正本索引（源件:行 → 目标件:行）、实跑记录 6 条 |
| `_hp_HANDOFF_DECLARATION.md`（4,290 B） | 交接声明 (a) 做了/没做 (b) 改文来源 (c) 未决声明 (d) 成组规则 ＋ 四件被订正件指纹锚定 |
| `_hp_fp_verify.py`（3,156 B，只读） | 逐件 hashlib 核验编排方指纹表（14 件）＋受核件补登记 |
| `_hpv_ulpn_verify.py`（12,348 B，复核轮写入，只读） | 复核轮独立核验脚本（九条改文零改动比对等） |
| `_hp_ap_checks.py`（本交付轮新建，只读） | 交付轮核验：复核绑定行复现、九条三方同文、映射 14 行、复核三瑕疵复验、counterpart 域探针 |
| `APPROVAL_PACK.md`（本件） | 六节交付件：总览 / 指纹＋九条核对 / 依赖矛盾 / 目录大纲 / 复核回件＋操作指引 / 交接声明 |

## 5 复核回件（绑定行）＋ 批准人操作指引

### 5.1 复核回件（如实转录；verdict = partial，按规则标 unconfirmed）

被核对象 SHA256 = ac8bc70519c506359cab77a3b27f2c1275c2d8c5083071e2a3e5399a4047de8d，字节数 = 55567

- 被核对象 = 整编包 15 件 `_hp_` 文件。**本交付轮复现成功**：`_hp_ap_checks.py` 实跑，15 件字节数合计 = 55567；按**文件名升序拼接**后 hashlib 实算 = 上列哈希（**MATCH**）；按整编清单顺序拼接不匹配（58e8a1df…），故拼接口径 = 文件名升序，据此登记。
- 复核核心结论（通过项）：九条改文「改后逐字」独立实跑比对为零改动；14 件指纹逐字节等于编排方基线；JSON↔B2B 映射 14 行全等；`_m5_mirror_check.py` 现状 3/3 ＋ `--after` 6/6；16 项未决照列未被替决；git 前后对比零越界。
- 三处瑕疵（判 partial 的原因）：§3.4-①②③，本交付轮全部复验成立，处置见 §3.4。
- **本交付轮实跑命令与结果**（全部只读）：① `_hp_fp_verify.py` → 13 OK + MISSING_AS_EXPECTED（COUNTERPART_FIX.md e291f5a8…/32830）+ EXTRA_OK（cd03a91a…/27825）；② `_m5_mirror_check.py` → 「结论（现状改前）: 3/3 PASS」、`--after` → 「结论（--after 内存模拟）: 6/6 PASS」；③ `_hp_ap_checks.py` → 绑定行 MATCH、cells==改文正本 6/6 True、U1–U9 逐字比对全 True、映射 ALL EQUAL、U8 diff=1（瑕疵①）、P1 行号=129（瑕疵③）、P10 :90 命中、V2 行级引用 0、counterpart 探针九条全文 0 命中；④ `git status --porcelain`（相关路径）→ 九源域全部 ?? 未跟踪、两台账 MM 为既有状态且指纹与基线一致。

### 5.2 批准人操作指引（第 0–8 步，照做即可；所有命令在 `D:\Project\ra2-campaign-forge` 下执行）

- **第 0 步｜核包**：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\handoff_pack_20261109\_hp_fp_verify.py`。预期：13 行 `OK` + 1 行 `MISSING_AS_EXPECTED`（COUNTERPART_FIX.md，交付时点已出现，附实测指纹 e291f5a8…/32830）+ 1 行 `EXTRA_OK`（受核件 cd03a91a…/27825）。**13 个内容件任一 MISMATCH = 包内改文不可信，停止。**
- **第 1 步｜决断必须批准人自己下的事**：P1 范围决断（乙设计责任人，最小批 vs 选项 B，执行互斥不许混采）；P4 字形决断（V2 来源会话，无粗体 vs 粗体，二选一）。P2/P5/P6/P7/P8 可在落笔前一并定（§5.3）。
- **第 2 步｜乙设计责任人批 U2-U7 并六处同批落盘（P3 强制前提）**：依据 §2.3-U2…U7。**六处一批**：STATE_MATRIX.json :2/:5/:4 + B2B_DESIGN.md :148/:151/:150，一次编辑会话内完成；成对（U2↔U5、U3↔U6、U4↔U7），不许单侧落盘。落盘前预检（只读，可随时重跑）：
  `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\u5u6_mirror_20261109\_m5_mirror_check.py`（现状：3/3 PASS）
  `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\u5u6_mirror_20261109\_m5_mirror_check.py --after`（内存模拟：6/6 PASS）
  落盘时人工逐行签认（P16）：脚本第 7 段 14 行 condition 并列输出即签认底稿（对应重签件 §3:56 既有仪式）。
- **第 3 步｜落盘后立即验证（六处）**：① 重跑第 0 步脚本：STATE_MATRIX.json 与 B2B_DESIGN.md 两行应报 MISMATCH（旧指纹），**记下脚本打印的新指纹**（换版登记要用）；② 重跑 `_m5_mirror_check.py`（磁盘态）：预期 3/3 结构门禁 PASS ＋ 谓词/清零取证打印转「双侧同在/清零」，按 P15 处置选项 (i) 人工判读，或先按 (ii) 在 u5u6_mirror 写域补 `--disk` 全检模式另行登记后再用（该脚本不在本包写域，本包未代改）；③ 确认 :144「下表与之逐行一致」重新为真（六处同批后自然成立）。
- **第 4 步｜V2 来源会话批 U1 并重发 V2（一次）**：:91 改文（P4 定夺字形）+ §2.1 :45/:46 刷成第 3 步记下的矩阵/设计新指纹。若先重发 V2 再改矩阵/设计，V2 需重发两次——不建议。
- **第 5 步｜重签侧换版重签件（一次，收尾）**：§2 :33/:34/:35 三行换新指纹（设计/矩阵/V2）+ :153 生效条件 1 复核；文本不变、仅换版；放最后避免反复换版。
- **第 6 步｜U8/U9（主管侧，与绑定链无耦合、随时可做；与 U9 同批为宜）**：:154 整句替换（P7 前缀定夺）+ :146 评级格注记（P8 形态定夺）；落盘后重跑第 0 步脚本核对受核件新指纹；P10（:90 是否扩面另立订正）与 P14（他件绑定）由主管侧定。
- **第 7 步｜台账补登收尾（编排方）**：一批补登全部订正（行数未定 = P12）；连带处置重签件:170「均已原样上账」未检得对应行的未验项。
- **第 8 步｜门禁收尾**：T1/T2/T5 对**应用后副本**重跑（V2:187；本轮与历史均未跑 = P13），门禁脚本不在本包写域，由门禁签发侧执行。

### 5.3 必须批准人自己下的决定（未决项集中列，未替决）

| # | 事项 | 决断人 |
|:--|:--|:--|
| P1 | 范围准冲突①：pf2「最小修复只动一行（JSON:2+镜像 :148）」vs row5 选项 B 六处；执行互斥不许混采；采最小批须登记 W2/O1 残留 | 乙设计责任人 |
| P2 | 三处改文「见 :5 行」坐标（指 STATE_MATRIX.json 第 5 行＝镜像 :151；若改「见 :151」须三处同改并登记坐标差） | 乙设计责任人 |
| P3 | 六处同批（强制前提，非可选；确认执行纪律） | 乙设计责任人 |
| P4 | U1 字形（pf2:104 无粗体 vs _pf2_findings:27 粗体；语义同） | V2 来源会话 |
| P5 | U3 追加判读（row5:132 外侧「」＝引注记号、去「」后追加）确认 | 乙设计责任人 |
| P6 | U4/U7 拼接点（源件未逐字指明；推荐 =「独立 error 出口」之后） | 乙设计责任人 |
| P7 | U8 行首列表前缀「2. **W2**：」去留 | 受核件主管侧 |
| P8 | U9 整格替换 vs 格内追加（含末句号去留） | 受核件主管侧 |
| P9 | U8/U9 批准人指派（源③未载明） | 编排方指派 / 主管侧认领 |
| P10 | 受核件 :90 滞留旧措辞是否另立订正 | 受核件主管侧 |
| P11 | counterpart 域处置（COUNTERPART_FIX.md 交付时点已出现，见 §3.4-②；是否补登记/改写该未决项） | 编排方 |
| P12 | 两台账补登行数；重签件:170「已原样上账」未检得对应行的处置 | 编排方 |
| P13 | T1/T2/T5 门禁（对应用后副本重跑） | 门禁签发侧 |
| P14 | U8/U9 他件指纹绑定检索（两绑定表外） | 受核件主管侧 |
| P15 | 落盘后正式门禁形态：(i) 磁盘态 3/3 结构门禁＋取证打印人工判读，或 (ii) 补 `--disk` 全检模式另行登记 | 批准人裁量 |
| P16 | 「语义等价」人工逐行签认（不可程序化证明，属批准动作） | 乙设计责任人 |

### 5.4 六处同批落盘检查（检查什么、用什么查）

1. 落盘**前**：`_m5_mirror_check.py` 现状模式 3/3 PASS（结构门禁①②＋is_new）＋ `--after` 内存模拟 6/6 PASS（含④白名单外零残差、⑤「跑后任意」双侧清零；行长 :148 118→226、:150 112→159、:151 155→318）——本轮两式均实跑吻合。
2. 落盘**时**：成对校验 U2↔U5、U3↔U6、U4↔U7；JSON 侧三行与其余键值不动、B2B 侧三行仅第 3 列变化（本轮已验证拼装式）。
3. 落盘**后**：`_hp_fp_verify.py` 记录新指纹 → `_m5_mirror_check.py` 磁盘态（3/3 门禁＋取证打印，P15 口径）→ :144 重新为真。

### 5.5 落盘后验证（全链）

重跑 `_hp_fp_verify.py` 记录新指纹 → `_m5_mirror_check.py` 磁盘态 → T1/T2/T5 对应用后副本重跑（P13，本轮未跑）→ 重签件 :153 生效条件 1 复核（换版 :33/:34/:35）→ 受核件新指纹登记（U8/U9 落盘后）→ 两台账补登收尾。

## 6 交接声明

### 6.1 本包（整编＋交付两轮）做了什么、没做什么

**做了**：编排方指纹表 14 件逐一 hashlib 核验（13/13 内容件与基线逐字节一致，COUNTERPART_FIX.md 交付时点状态如实登记）；九条改文六要素（目标文件/行、原文逐字、改后逐字、出处、批准人、完整性）逐条核到实读原文与实跑比对；依赖与矛盾检查（映射 14 行全等、V2 零行级引用 0 命中、P10 :90 滞留措辞定位）；`_m5_mirror_check.py` 两模式实跑；复核三瑕疵逐一复验并定位；产出 15 件 `_hp_` 文件与本件。

**没做**：未修改、未追加、未覆盖任何既有件；未跑 T1/T2/T5、未重跑 fixture、未做 B2B↔JSON 之外的程序化 diff；未 commit、未 push；零真机、零采样代码。

### 6.2 改文来源声明

九条改文**全部来自前序写域**，本包未新造任何改文：U1/U2 ← `lead/v2_precision_fix_20261108/`（pf2 §3.5:104、§4.5:193）；U3/U4 ← `lead/matrix_row5_20261109/`（:132、:135）；U5/U6/U7 ← `lead/u5u6_mirror_20261109/`（`_m5_cells.json` ＋ U5U6_MIRROR_TEXTS §3，后补起草正本，两份汇总件均如实标「未提供」，时间线自洽）；U8/U9 ← `lead/w2_samecause_20261109/`（§5.2:122、:124）。counterpart 域无一改文出自（交付时点探针复验：九条改文全文 0 命中，仅谓词级引文）。

### 6.3 未决项声明

16 项未决（P1–P16）全部照列于 §5.3 与 `_hp_PENDING_AND_SIGNOFFS.md`，**未替批准人决定任何一项**：范围决断（P1）、坐标（P2）、字形（P4）、拼接点（P5/P6）、前缀（P7）、U9 形态（P8）、U8/U9 批准人（P9）、:90 扩面（P10）等均留待对应签字人。

### 6.4 部分批准时的成组约束（按源件口径转述）

- **必须成组**：{U2,U5}、{U3,U6}、{U4,U7} 三对——单侧落盘即破 B2B_DESIGN.md:144 硬声明，且 T2/T5/重签件:154 条件 2 抓不到；P3 要求 U2–U7 六处一批落盘。
- **P1 决断下的组伸缩**：采最小批 → 组缩为 {U2,U5}，U3/U6 为省略项（代价 = 严格键层 O3 孤儿 + W2 残留，须如实登记），U4/U7 可推迟（须登记保留 W2）；采选项 B → 六处全做。
- **可单独做**：U1（独立批准人；但顺序宜在六处定稿后重发 V2，否则重发两次）；U8/U9（与绑定链无耦合、随时可做；U9 注记语义以 U8 收窄为前提，建议同批）。
- **永远收尾**：重签件换版最后做（避免反复换版）；两台账补登最后收尾。

### 6.5 未改任何文件声明

本交付轮**只新建** `lead/handoff_pack_20261109/APPROVAL_PACK.md`（本件）与 `lead/handoff_pack_20261109/_hp_ap_checks.py`（只读核验脚本，因内联命令超长截断而落盘）；**未修改、未追加、未覆盖任何既有文件**。凭据（本轮实跑）：① 13 个内容件指纹与编排方基线逐字节一致（`_hp_fp_verify.py` 输出）；② `git status --porcelain`（相关路径）→ 九个前序写域全部 `??` 未跟踪、两台账 `MM` 为任务开始前既有状态且指纹与基线一致；③ 未 commit、未 push；零真机、零采样代码。整编轮与复核轮的写域记录同此口径（各自声明件在案）。

### 6.6 未验项（如实列，不补造）

1. T1/T2/T5 门禁未跑（P13；V2:180-184 三项自记本轮未跑，R3:42「14/14」为历史转引）——落盘后对应用后副本重跑。
2. `_m5_mirror_check.py` 磁盘态全检形态（P15 选项 (ii) `--disk` 模式）未实现、未验。
3. U8/U9 在 V2 §2.1 与重签件 §2 两绑定表之外的他件指纹绑定（P14）——本轮只核两表 0 命中，未做全库检索。
4. 两台账「已原样上账」对应行未检得（P12；重签件:170）——本轮未复查两台账内容（仅指纹核验）。
5. 「语义等价」最终确认不可程序化证明（P16）——人工逐行签认未代行。
6. `COUNTERPART_FIX.md`（32,830 B，交付时点新出现）仅做指纹与九条改文片段/全文探针，**全文内容审查未做**；其与九条的实质关系（如有）待编排方裁量（P11）。
7. `lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md`（第三件既有 MM）内容未检查。
8. U9 全部概率量级为推理、未验（W2 §4.2 自记）；V2:169「删除边 0」旁辨（源件主张非缺陷不改）未复验。
