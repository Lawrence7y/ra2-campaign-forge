# U5U6_MIRROR_TEXTS.md —— U5/U6/U7 镜像逐字改文交付件（2026-11-09，交付轮）

- 上游：撰写轮【改文】（正本 `_m5_cells.json`）＋ 复核轮【复核 verdict=confirmed】；本件为交付轮唯一文档交付物。
- 任务：把三处 B2B_DESIGN.md 对 `STATE_MATRIX.json` 的镜像逐字改文成文（只出改文，零落盘），给五节。
- 本轮核验脚本：`lead/u5u6_mirror_20261109/_m5d_fp.py`（本轮新建，只读；hashlib 指纹＋镜像区取证）。

---

## 1 目的与边界

**目的**：补齐 U5/U6/U7 三处 `lead/b2b_design_20261106/B2B_DESIGN.md` 对 JSON 侧（`lead/b2b_design_20261106/STATE_MATRIX.json`）的镜像逐字改文；改文本身不落盘，只在本件成文，待乙设计责任人批准后与 JSON 侧 U2/U3/U4 同批落盘。

**任务前提修正（如实记，撰写轮实读、本轮复核确认）**：三处并非全缺——
- U7 的镜像加句**源件已给逐字**：row5:135「+ B2B_DESIGN.md:150 镜像同句」（本轮实读）＝统一清单:110-111「与 U4 同句」（本轮实读）；
- 真正缺失的是 **U5/U6**：统一清单:92 自记「**两源均未给出逐字改文**……如实标注『未提供』」、:102 自记「**源件未给出逐字改文**」（本轮实读）。本轮补齐 U5/U6 逐字起草（正本 `_m5_cells.json`）。

**边界**：
- 唯一写域 = `lead/u5u6_mirror_20261109/`；本交付轮只新建 `U5U6_MIRROR_TEXTS.md`（本文件）与 `_m5d_fp.py`，**未修改任何文件**（详见 §5.2）。
- 绝对只读五路径未触碰：`lead/b2b_design_20261106/`、`lead/v2_precision_fix_20261108/`、`lead/matrix_row5_20261109/`、`lead/text_fix_unified_20261109/`、两件台账。
- 零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 hashlib；不 commit、不 push。

**生效前提（硬）**：改文以 **U2-U7 六处同批落盘**为前提（U2=JSON:2、U3=JSON:5、U4=JSON:4；U5/U6/U7 为其 B2B 镜像 :148/:151/:150）。单侧落盘即破 :144「下表与之逐行一致」（§4.3(a)）。批准人＝**乙设计责任人**。

---

## 2 上游指纹（十件，本轮实跑复测）＋ B2B_DESIGN 镜像区现状

### 2.1 十件指纹（本轮实跑 `_m5d_fp.py` 与撰写轮 `_m5_fp_check.py`，双双 10/10 MATCH，零漂移）

| # | 文件 | SHA256 | 字节数 | 复跑 |
|:--|:--|:--|--:|:--|
| 1 | lead/b2b_design_20261106/STATE_MATRIX.json | 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016 | 3,558 | MATCH |
| 2 | lead/b2b_design_20261106/B2B_DESIGN.md | 565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf | 66,735 | MATCH |
| 3 | lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md | b1231ccb8b80c5200e2ff33b15e09ae52b0452a1481dfc7989730f7da16eda5b | 22,048 | MATCH |
| 4 | lead/v2_precision_fix_20261108/_pf2_findings_20261109.md | 4aef8957094008262d980640836ab0aec3e797f892b25fe8ff02b6aa87957fe4 | 7,966 | MATCH |
| 5 | lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md | 6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8 | 29,818 | MATCH |
| 6 | lead/text_fix_unified_20261109/UNIFIED_TEXT_FIX.md | ec0fb8ec47cfb71be5b28bc8a76f9152a6cbd377e741e7be1902a0958fbba154 | 42,172 | MATCH |
| 7 | lead/text_fix_unified_20261109/_uf_UNIFIED_FIX_LIST_20261109.md | 441b073a39a2ac195d90d43e3ba85f3c2202d5fafce31bec9c96e000a01e0923 | 25,095 | MATCH |
| 8 | lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py | ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2 | 412,759 | MATCH |
| 9 | lead/PENDING_DECISIONS.md | 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 | 52,419 | MATCH |
| 10 | lead/GOAL_THREE_TARGETS_20261018.md | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 759,518 | MATCH |

复跑命令（实跑，输出 `SUMMARY: 10/10 MATCH, 0 MISMATCH`）：
`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/u5u6_mirror_20261109/_m5d_fp.py`
`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/u5u6_mirror_20261109/_m5_fp_check.py`

两件被核对象绑定行（本轮实跑实算值）：

被核对象 SHA256 = 565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf，字节数 = 66735（lead/b2b_design_20261106/B2B_DESIGN.md）

被核对象 SHA256 = 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016，字节数 = 3558（lead/b2b_design_20261106/STATE_MATRIX.json）

**引用坐标澄清（本轮实读核得）**：先轮简称「pf2 §4.5 :193 / pf2:200 / pf2:205」实指 `V2_PRECISION_FIX_PROPOSAL.md`（本轮实读 :188-:207，段文逐字吻合编排方镜像段）；同款 JSON:2 改文亦见 `_pf2_findings_20261109.md:35`（44 行短件，其 :35 为 row5:134 所引）。本文引用一律写全文件名。

### 2.2 B2B_DESIGN.md 镜像区现状（§2 状态矩阵，:140-:168；本轮实读＋实跑取证）

- **总量**：B2B_DESIGN.md 693 行；STATE_MATRIX.json 16 行、`json.loads` = 14 条目（实跑 `_m5d_fp.py`）。
- **:142（列定义）**：`preState` ∈ 四态（`unknown / absent_confirmed / present / error`，H01 `FRESHNESS_SNAPSHOT_STATES` 约束）；`is_new` 为 `True / False / None`（`None` = 未测写 null，母本 `:439-440` 口径）；`usableAsCrashEvidence` 恒 `false`（`:677` 口径）。
- **:144（约束力，原文逐字）**：

> 机器可读版为同目录 `STATE_MATRIX.json`（严格 JSON 数组，14 项，每项含 `state` / `condition` / `verdict` / `confidence` / `usableAsCrashEvidence`，另附 `preState`）；下表与之逐行一致。

  约束力：表 14 行与 JSON 14 项「逐行一致」是设计正本的**明文硬声明**——任一侧改 condition 而另一侧不动，该声明即假。这也是 U5/U6/U7 必须存在的直接依据。
- **:146（表头，原文逐字，实跑切列 = 7 列）**：`| state | preState | condition（输入条件） | verdict | confidence | is_new | usableAsCrashEvidence |`
- **数据行 :148-:161 共 14 行 ↔ STATE_MATRIX.json:2-:15**（镜像门禁 ①② 项本轮实跑 PASS）；`is_new` 为 B2B 独有列，JSON 各行无该键（实跑检查 PASS）。
- **三行原文整行逐字（:148 / :150 / :151，本轮实读，与复核 `_m5v_indep.py` 逐字节比对结论一致）**：

```
:148（U5）| `unknown` | `unknown` | `pre=None` / `{}` / 缺 `state` / 脏值（未采集或采集未完成），跑后任意 | `unknown` | `none` | `None` | `false` |
:150（U7）| `error` | `error` | 跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口 | `error_pre_snapshot` | `none` | `None` | `false` |
:151（U6）| `post_read_error` | `present` | 跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口 | `post_read_error` | `none` | `None` | `false` |
```

- **现状取证（本轮实跑 `_m5d_fp.py`）**：行长 :148=118、:150=112、:151=155 字符；「跑后任意」B2B 1 处（仅 :148）、JSON 1 处（仅 :2）；「任意文件状态」B2B 0 处、JSON 1 处（:2）；STATE_MATRIX.json 含「」的行 = **[7]**（:7 condition 含「文件未出现」——复核 F1 取证，本轮复跑吻合）。
- **码序依据（改文谓词出处）**：B2B_DESIGN.md:310-311 补丁注释原文「`# ★ N1：错误独立出口，优先于一切状态折叠`」（本轮实读 :310）＋ row5:59「read_error 出口在码序 2，先于一切 pre 分支（码序 3-6）与 present 支内全部子分支（码序 7-13）」（本轮实读）。

---

## 3 U5/U6/U7 逐字改文（正本 `_m5_cells.json`；三处均只动第 3 列 condition，不含管道符，不破坏 7 列表格与 14 行结构）

### 3.1 U5 —— B2B_DESIGN.md:148（镜像 STATE_MATRIX.json:2 ＝ U2）

- **文件/行**：`lead/b2b_design_20261106/B2B_DESIGN.md` 第 148 行，第 3 列 condition。
- **原文整行逐字**：

```
| `unknown` | `unknown` | `pre=None` / `{}` / 缺 `state` / 脏值（未采集或采集未完成），跑后任意 | `unknown` | `none` | `None` | `false` |
```

- **改后整行逐字**：

```
| `unknown` | `unknown` | `pre=None` / `{}` / 缺 `state` / 脏值（未采集或采集未完成），跑后读取正常（`post.read_error` 为空）；`post.read_error` 非空时先落 `post_read_error`（码序 `read_error` 出口先于 `unknown` 出口，见 :5 行） | `unknown` | `none` | `None` | `false` |
```

- **JSON 侧对照（U2 改文逐字；源＝V2_PRECISION_FIX_PROPOSAL.md:193「处方，未实施」，同文亦见 _pf2_findings_20261109.md:35，两处本轮实读）**：

```
pre=None / {} / 缺 state / 脏值（跑前快照未采集或采集未完成），跑后读取正常（post.read_error 为空）；post.read_error 非空时先落 post_read_error（码序 read_error 出口先于 unknown 出口，候选 :4643 先于 :4648，见 :5 行）
```

- **JSON 侧 ↔ B2B 侧对照表**（B2B 侧列出去反引号后文本；等式「JSON − 白名单 ＝ B2B」经门禁④实跑验证）：

| 段 | JSON 侧（:193 逐字） | B2B 侧改文（去反引号） | 差异性质 |
|:--|:--|:--|:--|
| 谓词① | 跑后读取正常（post.read_error 为空） | 跑后读取正常（post.read_error 为空） | 仅反引号 |
| 谓词② | post.read_error 非空时先落 post_read_error | post.read_error 非空时先落 post_read_error | 仅反引号 |
| 谓词③ | 码序 read_error 出口先于 unknown 出口，候选 :4643 先于 :4648，见 :5 行 | 码序 read_error 出口先于 unknown 出口，见 :5 行 | 白名单差＝「候选 :4643 先于 :4648，」（候选行号指针；省略行号系本表未改行的既有惯例，见 §4.3(c)） |
| 既有缩写 | 跑前快照未采集或采集未完成 | 未采集或采集未完成 | 白名单差＝「跑前快照」（原 :148 即为缩写，非新差） |

- **不动项**：其余 6 列、14 行结构、行序全不动。

### 3.2 U6 —— B2B_DESIGN.md:151（镜像 STATE_MATRIX.json:5 ＝ U3）

- **文件/行**：`lead/b2b_design_20261106/B2B_DESIGN.md` 第 151 行，第 3 列 condition。
- **原文整行逐字**：

```
| `post_read_error` | `present` | 跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口 | `post_read_error` | `none` | `None` | `false` |
```

- **改后整行逐字**：

```
| `post_read_error` | `present` | 跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口（★ N1 码序 `read_error` 出口先于一切 pre 分支；pre 任意态——`unknown`/`absent_confirmed`/`present`/`error`——+ `read_error` 均落本行，`preState` 列的 `present` 为最常见登记态，匹配以本 condition 为准） | `post_read_error` | `none` | `None` | `false` |
```

- **JSON 侧对照（U3 改文逐字；源＝row5:132 追加注记，去外侧「」引注记号——「」系本件判读，依据与复核 F1 更正见 §4.3(f)/§5.1；本轮实读 row5:132 内侧以 JSON:5 现文逐字开头）**：

```
跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口（★ N1 码序 read_error 出口先于一切 pre 分支：候选 :4643-4646 先于 :4648 unknown / :4652 error / :4657 无件 / :4666 absent_confirmed / :4672 起 present 支；pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行，preState 列的 present 为最常见登记态，匹配以本 condition 为准）
```

- **JSON 侧 ↔ B2B 侧对照表**：

| 段 | JSON 侧（row5:132 逐字） | B2B 侧改文（去反引号） | 差异性质 |
|:--|:--|:--|:--|
| 谓词① | ★ N1 码序 read_error 出口先于一切 pre 分支 | 同文 | 仅反引号 |
| 谓词① 续 | ：候选 :4643-4646 先于 :4648 unknown / :4652 error / :4657 无件 / :4666 absent_confirmed / :4672 起 present 支 | （无） | 白名单差＝候选行号指针串（指针级，见 §4.3(c)） |
| 谓词② | pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行 | 同文（含同款 `/` 分隔） | 仅反引号 |
| 谓词③ | preState 列的 present 为最常见登记态，匹配以本 condition 为准 | 同文 | 仅反引号 |

- **不动项**：`preState` 列保持 `present` 不动（row5:132 同款约束——B2B_DESIGN.md:142 约束 preState ∈ 四态值域，注记由 condition 文本承载，不得写 "any"）；其余 6 列、14 行结构、行序全不动。

### 3.3 U7 —— B2B_DESIGN.md:150（镜像 STATE_MATRIX.json:4 ＝ U4）

- **文件/行**：`lead/b2b_design_20261106/B2B_DESIGN.md` 第 150 行，第 3 列 condition。
- **原文整行逐字**：

```
| `error` | `error` | 跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口 | `error_pre_snapshot` | `none` | `None` | `false` |
```

- **改后整行逐字（加句＝源定同句 row5:135 / 统一清单:83、:111 逐字「（post.read_error 非空时仍先落 post_read_error，见 :5 行）」，cell 端拼接；无反引号＝「同句」字面要求）**：

```
| `error` | `error` | 跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口（post.read_error 非空时仍先落 post_read_error，见 :5 行） | `error_pre_snapshot` | `none` | `None` | `false` |
```

- **JSON 侧对照**：加句与 JSON:4 为**同句逐字（零字面差）**。JSON:4 既有尾句「，不降级、不静默、不给 high」为白名单差（原 :150 即无此尾句，非新差；门禁④白名单＝该尾句，实跑零残差）。
- **JSON:4 推荐拼后全文（拼接点系本件推荐＝「独立 error 出口」之后，与 B2B cell 端拼接平行；源件未逐字指明拼接点——统一清单:82 自记「拼接点源件未逐字指明」——最终由批准人定）**：

```
跑前采集抛异常（snap.error 非空）⇒ 独立 error 出口（post.read_error 非空时仍先落 post_read_error，见 :5 行），不降级、不静默、不给 high
```

- **不动项**：其余 6 列、14 行结构、行序全不动；U4 可推迟性同源件（row5:135「不加则须在登记中如实保留 W2」，本轮实读）。

---

## 4 镜像一致性校验方案 ＋ 改文风险评估

### 4.1 人工逐行对照（签认仪式）

- 脚本第 7 段（`_m5_mirror_check.py:145-151`）输出 14 行 condition 逐行并列（`:148+i ↔ JSON:{2+i}`，含「◀ 改」标），批准人逐行签认——对应重签件 §3:56「矩阵十四行逐行比对」既有仪式（`lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md:56`，本轮实读确认存在）。
- **诚实声明**：condition 是自然语言，全文「语义等价」无法程序化证明——白名单残差法只能把剩余差异收敛为已声明片段并机检其外零差异；「语义等价」的最终确认仍需人工逐行签认（属批准动作，本件未代行）。

### 4.2 程序化门禁（可行性已评估并实跑；建议与人工签认并用）

五层设计（`lead/u5u6_mirror_20261109/_m5_mirror_check.py`，对两件被核对象只读）：
① 行数 14/14；② 五枚举字段（state/preState/verdict/confidence/usableAsCrashEvidence）逐行全等；③ 三处改文判别谓词双侧同在＋旧语义词（跑后任意/任意文件状态）双侧清零（B2B 侧去反引号后逐字子串）；④ 白名单残差等式「JSON 条件 − 白名单片段（逐项断言在侧并剔除）＝ B2B 条件」，白名单外任何残差即 FAIL；⑤ 全文「跑后任意」清零；另含 is_new 独有性检查。

本轮实跑结果（四条命令均为 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/u5u6_mirror_20261109/_m5_mirror_check.py`，第二条加 `--after`）：
- **现状（改前）模式：3/3 PASS**（①②＋is_new）＋三处谓词缺口如实取证（U5 4 谓词＋2 禁词、U7 1 谓词、U6 3 谓词全部 json=False/b2b=False）＋「跑后任意」B2B=1@:148 / JSON=1@:2。
- **`--after` 内存模拟（U2-U7 六处同批应用，含 :57-:59 拼接位置守卫断言）：6/6 PASS**（含④白名单外零残差）；行长 :148 118→226（Δ+108）、:150 112→159（Δ+47）、:151 155→318（Δ+163）。

**建议**：两者并用——脚本为门禁，人工逐行签认为批准动作的一部分。

**门禁复跑口径更正（本轮实读脚本代码发现；撰写轮「落盘后跑应 6/6 PASS」表述不准，如实更正）**：`_m5_mirror_check.py:107-135` 中，检查③④⑤均在 `if after:` 分支内才构成 PASS/FAIL 门禁；**不带 `--after` 的磁盘态运行只门禁 ①②＋is_new（3 项）**，谓词/清零仅打印取证、不 FAIL；且带 `--after` 在真实落盘后会因 :57 现状守卫断言（`old_cells[0].endswith("，跑后任意")`）直接 AssertionError 拒跑。处置选项（批准人裁量，本件不擅改既有脚本）：(i) 接受「落盘后 3/3 结构门禁＋取证打印人工判读」；(ii) 在写域内给脚本补 `--disk` 全检模式并另行登记后再用。

### 4.3 改文风险评估

**(a) :144 是否被破坏——不破坏，前提是 U2-U7 六处同批落盘。** 六处同批则表 14 行与 JSON 14 项逐行仍一致，:144 保持为真，也无需改 :144 本身；只改 JSON 不改 :148/:150/:151 则 :144 变假且 W1/W2 旧语义滞留（V2_PRECISION_FIX_PROPOSAL.md:205、row5:133 已登记，本轮实读），反向只改 B2B 同假。级联换版：B2B_DESIGN.md 指纹变 → 统一清单:177（V2:45＋重签件 §2 第 4 行 :33＋:153 生效条件 1）；STATE_MATRIX.json 指纹变 → V2_PRECISION_FIX_PROPOSAL.md:200（V2:46＋重签件 §2 第 5 行 :34＋:153 条件 1）——两条级联链本轮实读（清单:176-177），绑定行原件未逐字下探（§5.3-1）。

**(b) 行长度**：:148 118→226（Δ+108）、:150 112→159（Δ+47）、:151 155→318（Δ+163，成全表最长行）——实跑 `--after` 实测。GFM 渲染无碍（改文无管道符、无换行，实跑确认）但可读性有代价；**不建议**删「pre 任意态」四态枚举或「匹配以本 condition 为准」来缩短——删任一即破坏与 JSON:5 的白名单对应，门禁④ FAIL。

**(c) 详略不等风险**：三处均为「B2B 略于 JSON」，略的只是候选行号指针（U5/U6）与既有缩写/既有尾句（U5/U7），与本表未改行的省略惯例一致（六处同批口径下未改行为 **11** 行＝14−3；「13」系 V2_PRECISION_FIX_PROPOSAL.md:196 最小修复口径残留，撰写轮表述已按复核 F2 更正）：JSON:10「（:677）」↔:156 无、JSON:15「is_new=null」↔:161 无（本轮逐行实读核对）。不存在「B2B 更详细」的行，读者不会据表误推 JSON 之外语义。U7 加句无反引号＝「同句」字面要求，与 cell 内其他记号样式微差（纯样式；若统一须连 JSON:4 一并）。

**(d) 「见 :5 行」坐标歧义**：三处均指 STATE_MATRIX.json 第 5 行（post_read_error 行，本表镜像 :151）；B2B 先读的读者可能误读为「本表第 5 行」（那是 absent_confirmed）。若改用本表坐标「见 :151」须三处同改并登记与 JSON 侧的坐标差（指向同一行，语义等价，不属语义分叉）。

**(e) 验收面与既有坐标**：T5 的 14 组 fixture 四元组断言不受影响（condition 文本不进断言——row5:129；14 行结构不动——row5:136）；:163 八类对账的「表中第 N 行」坐标全部保持为真（行序不动）；:142 preState 四态值域契约由「注记进 condition 而非改 preState 列」守住（row5:132 同款约束）。

**(f) 本件判读（非源件逐字，须批准人确认）**：row5:132 外侧「」为源件引注记号——撰写轮所引依据「JSON 14 行 condition 均无『』」经复核为**假**（实跑：STATE_MATRIX.json 含「」的行=[7]，:7 condition 含「文件未出现」；本轮复跑吻合）；判读结论仍成立，依据改为：V2_PRECISION_FIX_PROPOSAL.md:193 同族改文无「」（本轮实读为真）＋ row5:132 内侧以 JSON:5 现文逐字开头（本轮实读为真）＋ 统一清单:82-83/:110-111 既有转载链即剥「」。JSON:4 拼接点推荐「独立 error 出口」之后（源件未指明，清单:82 自记）。

**(g) severity = medium 依据**：硬声明 :144 在六处不同批时变假，且既有门禁（T2/T5/重签件:154 条件 2）抓不到 condition 文本层破坏（统一清单:93，本轮实读）；属治理文档一致性风险，无运行时影响（改文只动 markdown/JSON 文本，不触候选/母本/真机）。

---

## 5 复核回件 ＋ 未改任何文件声明 ＋ 未验项

### 5.1 复核回件（如实记）

- **verdict = confirmed**（非 refuted/partial，不标 unconfirmed）。
- 复核绑定行（复核回件原文照录；本轮 `_m5d_fp.py` 复跑同值）：

被核对象 SHA256 = 565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf，字节数 = 66735（lead/b2b_design_20261106/B2B_DESIGN.md）

被核对象 SHA256 = 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016，字节数 = 3558（lead/b2b_design_20261106/STATE_MATRIX.json）

- 复核核心结论（本轮可复跑部分已全部复跑吻合）：①指纹 10/10 等于编排方基线（复核员 hashlib 两次零漂移＋撰写员 `_m5_fp_check.py` 复跑；本交付轮再复跑 10/10）；②:148/:150/:151 三行原文逐字节一致；③pf2:193/row5:132/:135 摘录逐字无漏词；④三处均满足「JSON 侧改文 − 白名单片段 ＝ B2B 侧改文（去反引号）」完全等号，判别谓词逐段同文，B2B 侧无独有语句，无「任意 vs present」类分叉；⑤门禁亲验可行（改前 3/3＋取证、--after 6/6、行长一致）；⑥:144 风险已被改文明确承认；⑦零越界（十件指纹零漂移、写域恰为撰写人 5 件＋复核 2 件、三脚本只读、未 commit/push、零真机、零采样）。
- **复核两处非阻断瑕疵（随件更正，已并入 §3/§4）**：
  - **F1**：撰写回件判读「row5:132 外侧『』为引注记号」所引依据「JSON 14 行 condition 均无『』」为假——实跑 STATE_MATRIX.json 含「」的行=[7]（:7 condition 含「文件未出现」）；判读结论仍成立（其余依据为真），且原回件已自标该判读须批准人确认。
  - **F2**：「本表 13 个未改行」在撰写回件自己主张的 U2-U7 六处同批口径下应为 **11**（14−3=11）；「13」系沿用 V2_PRECISION_FIX_PROPOSAL.md:196 最小修复口径的残留表述；省略惯例本身属实（B2B 14 行 condition 无「（:行号」指针、JSON 仅 :10 有「（:677」——本轮逐行实读核对一致）。
- 执行前提（复核确认）：改文生效以 U2-U7 六处同批落盘为前提；U7 加句无反引号＝「同句」字面约束的样式微差；「见 :5 行」坐标歧义已在 §4.3(d) 声明。

### 5.2 未改任何文件声明

本交付轮**只新建** `lead/u5u6_mirror_20261109/U5U6_MIRROR_TEXTS.md`（本文件）与 `lead/u5u6_mirror_20261109/_m5d_fp.py`（只读核验脚本）；**未修改、未追加、未覆盖任何既有文件**——含：被核十件（本轮首尾两次指纹复跑均 10/10 MATCH，零漂移）、绝对只读五路径（`lead/b2b_design_20261106/`、`lead/v2_precision_fix_20261108/`、`lead/matrix_row5_20261109/`、`lead/text_fix_unified_20261109/`、两件台账）、写域内撰写轮 5 件与复核轮 2 件（本件对 `_m5_mirror_check.py` 的门禁口径更正只登记、不动代码）。未启动任何游戏进程、未写任何采样代码；改文零落盘（`--after` 为内存模拟）；未 commit、未 push。

### 5.3 未验项（如实列，不补造）

1. **重签件 §2 第 4/5 行（:33/:34）、:153 生效条件 1 与 V2 §2.1:45/:46 绑定行原件未逐字下探**——本轮只核到统一清单:171/:176-177 与 V2_PRECISION_FIX_PROPOSAL.md:200 的转载层（两处转载一致）；`CANDIDATE_RESIGN_YES_V2.md` 本轮只实读 :50-:59。属批准后换版动作，不影响本轮改文成立。
2. **U7 的 JSON:4 拼接点**：源件未逐字指明（统一清单:82 自记），「独立 error 出口」后拼接系本件推荐，待批准人定。
3. **row5:132 外侧「」＝引注记号**：判读在 F1 更正后依据成立，仍待批准人确认（§4.3(f)）。
4. **台账「已原样上账」对应行**：`_pf2_findings_20261109.md:39` 记两台账未检得对应行＝未验，本轮未复查两台账内容（仅指纹核验）。
5. **「语义等价」的最终确认**：不可程序化证明（§4.1 诚实声明）；人工逐行签认属批准动作，本轮未代行。
6. **落盘后的正式门禁形态**：§4.2 更正所示脚本行为缺口（磁盘态 3/3 vs 6/6、`--after` 落盘后拒跑）如何处置，待批准人裁量；本轮未改脚本，该项在处置前视为**未验**。
