# B_EXECUTION_SPEC V2 · N-4 定版任务书（绑乙 · 未生效 · 非放行）

- 件名：`lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md`
- 日期：2026-11-08　撰写：定版员·GLM（动态工作流子代理，新上下文）
- 性质：**N-4 任务书定版件（V2）**——把 N-4 任务书从「甲/乙未决草案」（`lead/bexec_n4_20261108/B_EXECUTION_SPEC.md`，`be733333…`/32,183 B，SPEC_DRAFT）定版为「**绑乙**」。矩阵选择已定 = 乙；**`APPROVE_SCOPE` 仍未签署**，故本件**仍不构成放行**，不授权 N-5，不代签任何东西。
- 与草案的关系：草案件**一字未改**（本轮收尾指纹复核见 §2.2）；本件是独立新版本 V2，不回写、不覆盖草案。N-4:47 要求的「来源会话任务签发人在本目录 B_EXECUTION_SPEC.md 固定……」的**正式槽位登记动作仍未发生**，列入 §6 未生效条件。
- 铁律：零真机（不启动 gamemd.exe / ra2loader / YURI.exe，不 taskkill，不读活进程内存）；零采样代码；母本与既有件一律只读；本轮唯一写域 = `lead/n4_yi_final_20261108/`；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 Python `hashlib`。
- 本轮边界：只产出本定版任务书 + 一份 T3 重跑输出（`_n4v2_ast_rerun_out.txt`）；未运行完整 harness、未 import/未执行母本与候选、未改母本、**未应用任何补丁**、不签 `APPROVE_SCOPE`。

---

## 1 目的与性质（★ 定版绑乙，未生效，非放行）

### 1.1 正式目标与对象
- 目标：②崩溃 / ③安全改动（`lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md:46`，本轮实读）。
- 对象：正式母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` 与唯一正式候选 `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py`（指纹 §2.1）。

### 1.2 定版依据链（本轮逐件实读）
1. **N-4 原文**：`NEXT_STEPS_20261106.md:45-51`——:47 合成矩阵原文（甲口径）、:49 签署与 API 门禁规则原文（「独立审阅者签候选 YES、来源会话签发人签 APPROVE_SCOPE……身份、任一规则或版本缺失则任务书不生效」）。
2. **方向裁决 Q1**（`lead/direction_ruling_20261108/RULING_DIRECTION.md`，本轮实读）：:23 裁定技术方向采用乙（B2B 设计、STATE_MATRIX 及现行 LF 候选），禁止混用甲预期；:25 与 :81（nextActions 1）建议「若确认乙，再补登『乙替代甲』、九 hunk 范围、矩阵/字段/候选/母本/差异指纹及签署身份」。Q1 原文转录见补登件 §1（`lead/b2b_yi_supersede_20261108/YI_SUPERSEDE_JIA_BINDING.md:13-16`）。
3. **用户当轮明示（2026-11-08）**：选「**先补登再应用**」——补登先行，应用另批（`YI_SUPERSEDE_JIA_BINDING.md:18`）。
4. **补登件已完成**：`YI_SUPERSEDE_JIA_BINDING.md`（本轮全文实读）已完成「乙替代甲」登记、九 hunk 范围更新（其 §5）、11 件指纹绑定（其 §4）；其 §6 明列四项未完成项，本件 §6 承接。
5. 本件在该链上的位置：**应用路径的下一块砖 = N-4 任务书本身按乙定版**；定版 ≠ 生效，生效条件清单见 §6.2。

### 1.3 放行边界（本定版件不代签任何东西）
- **不签 `APPROVE_SCOPE`**：属来源会话任务签发人（N-4:49 原文；裁决 Q1 明令「本裁决不代签」；补登件 §1 同）。**本件不构成放行。**
- **不代签候选 YES**：R3:21 `verdict: PASS` 属独立审阅者，且 R3:23/:122/:137 明写「PASS ≠ 可应用到母本」——该 PASS 不因本件升级。
- **不签真机验收 / 崩溃修复完成**：`RULING_D24.md:52` 只许签离线集成状态（转引自草案 §1.3；`RULING_D24.md` 本轮仅实算指纹 `56167a5e…`/15,301，原文未逐行复读——**未验**，见 §6.3）。
- **不应用母本**：本轮母本零改动；应用属 N-5，须另批。
- 矩阵选择「无需新增实施授权」（裁决 Q1 原文，补登件 :15-16 转录）——本件行使的正是该项选择，不含任何实施动作。

---

## 2 版本绑定（定版基线）

### 2.1 绑定指纹表（本轮实算，命令与核对见 §2.2）

本轮实跑命令（两次 `python -I -X utf8 -c`，hashlib 逐件读字节计算，绝对路径、以仓库根为 cwd）覆盖下表全部 19 件；输出原文见本轮 Bash 会话记录，逐件与补登件 §4 / 草案 §2.1 / R3 头部表的绑定值相符：

| 角色 | 路径 | SHA256（完整 64 位） | 字节数 |
|:--|:--|:--|--:|
| **母本（只读）** | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399,508 |
| **候选（乙实现，唯一正式）** | `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` | `ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2` | 412,759 |
| **候选 diff** | `lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff` | `72b108021637cf7d225a9b109a542ec10c934abb1a8e40b8850a82c6bea9cdb9` | 18,454 |
| **乙设计（绑定对象）** | `lead/b2b_design_20261106/B2B_DESIGN.md` | `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf` | 66,735 |
| **乙矩阵（绑定对象）** | `lead/b2b_design_20261106/STATE_MATRIX.json` | `1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016` | 3,558 |
| **乙预审（YES 依据）** | `lead/b2b_preaudit_20261106/B2B_PREAUDIT.md` | `3f97f3a4664981961b72a91a60053fe8c867fa9d8e25442e7159c3046ccbf69f` | 20,615 |
| **R3 复审（PASS 依据）** | `lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md` | `96071dd9d58e30a54966a2a1e16f4af918c2f8dd5825363510e8ced8bc6a8fea` | 24,661 |
| **补登件（乙替代甲登记）** | `lead/b2b_yi_supersede_20261108/YI_SUPERSEDE_JIA_BINDING.md` | `255356ca789955cc2c084388f547a1435feb310f210617b988f761e7ff331c7b` | 7,344 |
| **裁决书（方向裁决）** | `lead/direction_ruling_20261108/RULING_DIRECTION.md` | `0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653` | 16,514 |
| 甲设计（**不再绑定**，仅留档对照） | `lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md` | `deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f` | 11,638 |
| 甲预审（NO 依据，留档） | `lead/b2_preaudit_20261106/B2_PREAUDIT.md` | `a108a6e45f42c449db5d228abc469e5c17d40db0b04f15aa32105adff8905449` | 28,410 |
| N-4 原文 | `lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md` | `c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c` | 27,225 |
| D-24 裁决 | `lead/re_line_20261105/D24_RULING/RULING_D24.md` | `56167a5e869540d7e14a7f13d29a2ed9d780d0c6352635e6e12b36cd633dcdf5` | 15,301 |
| N-1 绑定 | `lead/b2b_n1_binding_20261107/N1_BINDING.md` | `00ea6fe87ee5508b84332447b23951d4db86a1682ee36aaa48a3bd9cf774d310` | 8,493 |
| T1 测试命令对象（改绑副本） | `lead/b2b_candidate_review3_20261107/_test_candidate_lf.py` | `1a1335d6d4dd472e4def5e739d54f6e229f83d0b5d8a178cb5b641c491fe8d11` | 34,111 |
| 旧候选（**禁绑**，已被 N-1 替换） | `lead/b2b_candidate_20261106/qc151_trip.candidate.py` | `9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc` | 420,292 |
| 旧测试套件（T1 错版，**禁绑**） | `lead/b2b_candidate_20261106/tests/test_candidate.py` | `33b0c5105c4f287056590340fd7bd801c0766dfff9da451e406e32ad77d95790` | 34,105 |
| AST 静态审查输出件 | `lead/bexec_n4_20261108/_n4_ast_scan_out.txt` | `9986fc2e335afa0748bfd9164c58c3eb04127c2f3db27b4e9fd91d5ee3cafdb6` | 22,510 |
| 旧草案（SPEC_DRAFT，留档不覆盖） | `lead/bexec_n4_20261108/B_EXECUTION_SPEC.md` | `be73333541ddef9a9782aff2ae2f98e657d50d254c50dad5acdf8052ebc25358` | 32,183 |

### 2.2 实算命令与核对声明
- 命令形态：`python -I -X utf8 -c "import hashlib; …（逐件 open('rb') → len → sha256）"`，绝对路径。9 件编排指纹（母本/候选/diff/乙设计/乙矩阵/草案/补登件/裁决书）+ 乙设计外 10 件（乙预审/甲预审/甲设计/N-4 原文/D-24/N-1/T1 副本/旧候选/旧测试/AST 输出）**全部本轮实算**；19/19 与补登件 §4、草案 §2.1、R3 头部表记载值逐一相符。
- **被核对象 SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508**（母本）。
- **被核对象 SHA256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2，字节数 = 412759**（正式候选）。
- **被核对象 SHA256 = 565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf，字节数 = 66735**（乙设计）。
- **被核对象 SHA256 = 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016，字节数 = 3558**（乙矩阵）。
- **被核对象 SHA256 = 255356ca789955cc2c084388f547a1435feb310f210617b988f761e7ff331c7b，字节数 = 7344**（补登件）。
- **被核对象 SHA256 = be73333541ddef9a9782aff2ae2f98e657d50d254c50dad5acdf8052ebc25358，字节数 = 32183**（旧草案——本轮零改动实证，其值与编排方指纹一致）。
- 版本纪律：正式候选仅 `qc151_trip.candidate_lf.py`（`ca23c116…`）；旧候选 `9656e432…` 已被 N-1 绑定替换（R3:150 转引；N-1 绑定件指纹本表），**禁止**作为 N-5 对象；N-5:57「版本不符立即 STOP」。

---

## 3 允许改动范围（定版：H01–H09 九 hunk；★ 甲 A–D 不再绑定）

### 3.1 定版范围 = 乙的九 hunk
依据乙设计 §7 表（`B2B_DESIGN.md:660-670`，本轮实读）逐个固定；hunk 头与母本锚点为唯一口径，无第 10 个 hunk（:658）：

| 编号 | 物理改动（母本锚点） | hunk 头 | 治哪条 |
|:--|:--|:--|:--|
| H01 | `:214` 后插入 F 命名空间 5 常量 | `-212,6 +212,21` | N6 / N9 |
| H02 | `:4460` 后追加 `RESTORE.backup_mtime_pre:{name}` 留痕（不改 `bak[name]` 三键） | `-4458,6 +4473,10` | N10 |
| H03 | `:4561` 前插入 `make_pre_freshness_snapshot` + `classify_except_freshness`；并改 `:4561-4562` def 签名加 `pre_freshness_snapshot` 形参 | `-4558,8 +4577,131` | N3 / N1 / N2 / N6 / N5 / N9 |
| H04 | `:4574-4599` 函数体重写：三态判别 + 正常/错误双落盘 + 3 条 `ERROR` 留痕 + `raise` + `info` 扩到 12 键 | `-4572,20 +4714,105` | N4 / N6 / N10 / N1 / N3 |
| H05 | `:5909` `finalize_trip` 签名加 `pre_freshness_snapshot` 形参 | `-5906,7 +6133,8` | E1 / N5 |
| H06 | `:5939` **唯一调用点**改为关键字传参 | `-5936,7 +6164,8` | N5 |
| H07 | `:6296` 后、`:6313 try` 前预初始化 `_pre_freshness_snapshot = None` | `-6294,6 +6523,9` | E1 / N3 |
| H08 | `:6388` 后构造跑前快照 + 落 `FRESHNESS.captured_at_iso_pre` | `-6386,6 +6618,15` | E1 / N10 |
| H09 | `:7125` 后把快照传给 `:7117 finalize_trip` | `-7122,7 +7363,8` | E1 / N5 |

- 允许范围 = **且仅 =** 上表九 hunk；删除行数 0；范围外任何改动（含 H 编号重排、新增 hunk、E 判据块）均 FAIL。九 hunk 的 `-` 侧覆盖区间均不含 E 判据块 `5984-5990`（`B2B_DESIGN.md:635` 本轮实读）。
- 候选与九 hunk 的逐字节等价已由 R3 双决定性路径确证（R3:31-34，本轮实读；两条重建路径 `_review_probe_r3_out.txt:124,126` 转引）。
- **范围条款的替代说明**：N-4:49 原文「删除也须解释且只许 A—D 内变动」——本定版按裁决 Q1「更新九 hunk 范围」将其替代为「**只许 H01–H09 内变动**」；此替代的授权来源 = 方向裁决 Q1 + 用户当轮明示 + 补登件 §5，非本件擅自扩权。

### 3.2 ★ 甲不再绑定（明确声明，不留两可）
**甲（`B2_FIX_DESIGN.md` 的 A—D 四处改动）自本件起不再绑定**：不得作为本任务书的允许范围、验收基准、矩阵口径或复算依据。理由（每条均本轮实读/实算）：
1. **甲预审 verdict = NO**：`lead/b2_preaudit_20261106/B2_PREAUDIT.md:17`（本轮实读）`verdict: NO`，全面阻断。
2. **两条独立否决理由各自足以判 NO**：`B2_PREAUDIT.md:20` 六条旧错中 `E1 = NOT_FIXED`（旧规则第一条即触发 NO）；`:21` 新增 `severity=high` 共 5 条（N1/N2/N4/N5/N11，旧规则第二条亦触发）；`:22`「两条规则各自独立足以判 NO」（:17-22 均本轮实读）。
3. **甲自身声明未达可应用态**：`B2_FIX_DESIGN.md:198`「本文件只是设计。应用前必须重新走一遍 B1 的预审硬门」（转引自草案 §2.2；该文件 :103-118 的 A—D 表与「四处改动是可论证的最小集」:118 为本轮实读）——且其预审已判 NO，该硬门不可能通过。
4. **裁决与补登已定**：方向裁决 Q1 禁止混用甲预期（RULING_DIRECTION.md:23）；补登件 §5 已把变更范围由「甲 A—D 四处（净增约 31 行）」改登为「乙 H01–H09 九 hunk（+255/-13，R3:43）」。
5. **现行唯一正式候选按乙实现**：R3 以乙设计+乙矩阵对照判 PASS（R3:5,42-44）；若按甲口径验收，候选在 absent_both、vanished、空快照等场景必 FAIL（差异明细 §4.3）——混用即自相矛盾。

**禁止混用甲预期**：任何验收、门禁、复算一律以乙的九 hunk 与乙矩阵为准；不得以甲的 A—D 四处、甲的 `absent_both,n/a` 或甲的空快照折叠作为验收基准。甲设计/甲预审两件仅留档对照（指纹见 §2.1），不再具有规格效力。

---

## 4 合成矩阵定版（绑乙；★ 全部按乙取值）

### 4.1 唯一通过判据
- **乙矩阵**：`lead/b2b_design_20261106/STATE_MATRIX.json`（`1d4ccc93…`/3,558 B）14 数据行（:2-15，本轮全文实读）为机器可读唯一口径。
- **值域（候选实码，本轮实读/grep）**：`FRESHNESS_VERDICTS` 9 值 = unknown / absent_both / new_first_appearance / vanished / leftover_unchanged / new_write / rewritten_same_content / error_pre_snapshot / post_read_error（候选 :223-226）；`FRESHNESS_CONFIDENCES` = high / medium / low / none（**无 n/a**，:227）；`FRESHNESS_SNAPSHOT_STATES` 四态 = unknown / absent_confirmed / present / error（:228）；`usable_as_crash_evidence` 恒 False（:4628-4631 `_finish` 实码）。H01 五常量定义处 = 候选 :221-228（本轮 grep 实证）。
- **判别口**：`state` 唯一判别（`B2B_DESIGN.md:95` 本轮实读）；`None`/`{}`/缺 `state`/脏值一律归一 `unknown`（候选 :4634-4639 实读）；确认无件必须显式 `state="absent_confirmed"`（`B2B_DESIGN.md:106`）。

### 4.2 乙矩阵 14 行定版（逐行 = STATE_MATRIX.json，行号即文件行）
| 文件行 | preState | verdict | confidence | usable |
|--:|:--|:--|:--|:--|
| :2 | unknown | unknown | none | false |
| :3 | unknown | unknown | none | false |
| :4 | error | error_pre_snapshot | none | false |
| :5 | present | post_read_error | none | false |
| :6 | absent_confirmed | new_first_appearance | high | false |
| :7 | absent_confirmed | absent_both | **low** | false |
| :8 | present | leftover_unchanged | high | false |
| :9 | present | leftover_unchanged | **medium** | false |
| :10 | present | new_write | high | false |
| :11 | present | rewritten_same_content | medium | false |
| :12 | present | rewritten_same_content | low | false |
| :13 | present（缺 pre.sha256） | error_pre_snapshot | none | false |
| :14 | present（缺 post.sha256） | post_read_error | none | false |
| :15 | present | vanished | **none**（旗标，人工复核） | false |

行→分支映射与 13 处 `_finish` 调用：R3:43（本轮实读）；候选 13 处调用行 = :4644/:4649/:4653/:4659/:4662/:4667/:4674/:4679/:4682/:4687/:4691/:4694/:4697（本轮 grep 逐行实证，含取值：:4659 `absent_both/low`、:4662 `vanished/none`、:4687 `leftover_unchanged/medium`、:4691 `leftover_unchanged/high`、:4694 `rewritten_same_content/low`、:4697 `rewritten_same_content/medium`）。R3:47 的 :2 行 condition 措辞保留登记（文档精度事项，非候选缺陷，本轮实读）。

### 4.3 甲→乙取值差异定版表（★ 甲值废止，乙值生效）
| 分支 | 甲（N-4:47 原文 / B2，**废止**） | 乙（STATE_MATRIX + 候选实码，**生效**） |
|:--|:--|:--|
| absent_both 置信 | `n/a` | **low**（STATE_MATRIX:7；候选 :4659） |
| vanished 置信 | `high` | **none**（旗标，人工复核；STATE_MATRIX:15；候选 :4662） |
| 空快照 `{}`（含 None/缺 state/脏值） | ≡ `exists=False` → absent_both / new_first_appearance 折叠 | → **unknown / none**，不作新出现归因（STATE_MATRIX:2-3；候选 :4634-4651） |
| mtime_pre 缺失（sha 同） | `elif` 守卫跳过 → leftover_unchanged/high | **leftover_unchanged / medium**（盲区如实标注，不虚报 high；STATE_MATRIX:9；候选 :4685-4689，grep 实证 :4687） |
| confidence 值域 | 含 `n/a` | high / medium / low / none（**无 n/a**） |
| verdict 值域 | 6 值 | 9 值（新增 unknown 独立出口、error_pre_snapshot、post_read_error） |
| 字段 | verdict + confidence | verdict / confidence / is_new / note / usable_as_crash_evidence / pre_snapshot_state（乙超集；候选 :4624-4626） |

N-4:47 原文的甲口径（`:47`「跑前无／跑后无→absent_both,n/a；有／无→vanished,high……空快照 {} 与显式 exists=False 等价」）**在本定版件中被乙口径整体替代**；此替代的授权链同 §3.1。

### 4.4 七分支 + 空快照 + 复制失败 + 四类异常契约（逐项固定：输入 → 输出 → 落盘 → 错误预期）
1. **空快照 `{}`（含 None/缺 state/脏值）**：归一 `unknown`（候选 :4634-4639 实读）→ `unknown / none / is_new=None / usable=False`（:4648-4651 实读，note 含「未知 ≠ 不存在」）；落盘 `_emit_f` 7 键（:4730-4753 实读）；**绝不作**「本趟新出现」归因。R3:44 穷举 36 组 unknown→high 泄漏 = 0（转引）。
2. **复制失败（须记 error 且不签复制成功）**：copy 内 `except`（候选 :4773-4790 本轮实读）→ 三条 `rec.add("ERROR",…)`：`freshness_copy_failed`（:4777）／`freshness_copy_stage`（:4780）／`freshness_copy_traceback`（:4784，本轮 grep 实证）→ `post_observed["read_error"]` 置错（:4786）→ `_emit_f(…, "copy_failed")`（:4788-4789）→ **`raise` 原异常**（:4790）；成功路径 info 记录仅 :4792 起可达 ⇒ 错误路径不签复制成功。早退（跑后无件）路径：`EXCEPT.evidence_copy=None` + `_emit_f(…, "src_missing")` + `return None`（:4756-4764 实读）。
3. **mtime_pre 缺失**：state=present 且 sha 同但 mtime 侧缺失 → `leftover_unchanged / medium / is_new=False`，盲区如实标注（STATE_MATRIX:9；候选 :4687）；不作新崩溃归因。
4. **读写异常（跑前侧）**：采集抛异常 → `state="error"` + `error` + `traceback` 三字段（候选 :4608-4612，内含 `import traceback` :4609 本轮 grep 实证）→ `error_pre_snapshot / none`（:4652-4654 实读），独立出口、不降级、不静默。
5. **初始化前收尾**：H07 预初始化 `_pre_freshness_snapshot: dict | None = None`（候选 :6528，本轮 grep 实证）；早于 :6623（H08 赋值，grep 实证）抛出 ⇒ 快照为 None → `unknown / none`；原异常保留、收尾失败进 `CLEANUP_FAILURES` 不写 verdict 局部量（`B2B_DESIGN.md:184` P6 契约，转引自草案 §3.5-5）。
6. **缺省调用路径**：`copy_post_except_evidence(pre_freshness_snapshot=None)` 默认（def :4701，grep 实证）与 `finalize_trip(…, pre_freshness_snapshot=None)` 默认（def :6127，grep 实证）→ 非 dict 归一 `{}` → `unknown / none`；与「报告未验或错误、不作新崩溃归因」相符（N-4:47）。
7. **F/E 边界（:677 不侵犯）**：E 唯一口径恒为母本 `except_set_diff`（`B2B_DESIGN.md:628-629` 本轮实读）；候选 :4619-4621 N9 docstring 声明（本轮实读）；九 hunk 区间均不含 E 判据块 5984-5990（:635）。
- 输出键名契约：classify 返回 6 键（:4624-4626 实读）；`_emit_f` 固定 7 键全落 `FRESHNESS` group（:4730-4753 实读）；`post_observed` 6 键（:4720-4722 实读）；`is_new=None` 未测写 null、不得写 False 冒充（:4736-4739 实读）。
- **运行时行为全部未验**（零真机/零采样）：以上为静态实读+结构性结论，运行时复现属 N-6/真机阶段（`B2B_DESIGN.md:676` 同口径，本轮实读）。

---

## 5 API 调用边基线（母本为基线；候选新增禁止调用 = 0）

### 5.1 禁止集合（与 N-4:49 原文一致，本轮实读 `NEXT_STEPS_20261106.md:49`）
MiniDumpWriteDump、SuspendThread、StackWalk／StackWalk64、ReadProcessMemory、WriteProcessMemory、VirtualAllocEx、CreateRemoteThread、SetWindowsHookEx、OpenProcess、TerminateProcess 及其包装／动态查找；另核 subprocess、os.system、ctypes 相关调用边；禁止新增游戏发射与 taskkill 路径。方法要求（N-4:49 原文）：基线与候选对同一集合**逐符号及调用边计数**，新增调用、导入、包装或动态解析均 FAIL；删除也须解释且只许范围内变动（范围按 §3.1 替代为 H01–H09）；字符串计数不能代替调用边审阅。

### 5.2 本轮实跑核验（T3 重跑，EXIT=0）
- 命令：`python -I -X utf8 "D:\Project\ra2-campaign-forge\lead\bexec_n4_20261108\_n4_ast_scan.py" > lead/n4_yi_final_20261108/_n4v2_ast_rerun_out.txt 2>&1`（本轮实跑，**EXIT=0**）。
- 重跑输出与本轮实读的既有输出件 `lead/bexec_n4_20261108/_n4_ast_scan_out.txt`（`9986fc2e…`/22,510）**逐字节一致**（`diff` 本轮实跑：identical）。
- 结论（`_n4v2_ast_rerun_out.txt` 与 `_n4_ast_scan_out.txt` 行号相同，本轮实读）：:623-633 十一禁止符号逐符号 **UNCHANGED**（MiniDumpWriteDump 1/3/0/0、ReadProcessMemory 1/3/0/0、OpenProcess 5/15/0/0，其余 0/0/0/0，两版同值）；**:635「候选新增禁止边符号: 无」**；:637-668 subprocess.Popen 1→1、ctypes 24 类逐类一致、getattr 13/13、importlib.util 边 2/2；:670-671 import 目标集合完全一致；:673 调用边差集「候选新增边 10 种，消失边 0 种（基线 536 种 / 候选 546 种）」；:675-684 新增边 = `_finish`×13、`classify_except_freshness`×3、`make_pre_freshness_snapshot`×1、`_emit_f`×3、`pre.get`×4、`post.get`×4、`post_observed.get`×2、`post_observed.update`×1、`out.update`×1、`src.stat`×2——全部落在批准九 hunk 的新鲜性逻辑与错误出口内（与 R3:31-34 相容）。
- 门禁判定：按 N-4:49 FAIL 条件（禁止集合新增调用/导入/包装/动态解析）**未触发**；删除边 0 无需解释。**该项静态判定 PASS（本轮实跑）。**
- 存量面（非候选引入，留档）：6 个包装函数两版同名同位（`_n4_ast_scan_out.txt:612-618` 实读：`get_process_creation_time`/`s4_enum_modules`/`_rpm_open`/`_rpm_u32`/`_qc151p3_frozen_dump`/`_pid_alive_check`），属母本既有采样机器，非本候选新增；**其运行时行为未验**。
- AST 静态相等 ≠ 运行时行为；本基线只在静态层约束 N-5。

---

## 6 测试命令 T1–T5（定版绑乙）+ 未生效条件清单

### 6.1 测试命令定版（绑乙后即为 N-5 通过判据；对**应用后副本**重跑，NEXT_STEPS:55）
| # | 命令（绝对路径） | 预期 | 本轮状态 |
|---|---|---|---|
| T1 | `python -I -B -X utf8 D:\Project\ra2-campaign-forge\lead\b2b_candidate_review3_20261107\_test_candidate_lf.py` | stdout `Ran 29 tests` / `OK` / `PASS=29 FAIL=0`，exit 0 | **本轮未跑**（禁执行/禁 import 候选，承草案先例）。先例 R3:145 `PASS=29 FAIL=0` 为历史转引；本轮实读：该副本 :37 `CANDIDATE_PATH = …lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py`（grep 实证）指向**正式候选**，`def test_` 计数 = 29（grep 实证）。指纹 `1a1335d6…`/34,111（§2.1） |
| T2 | `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\_draft_semantics_check.py verify` | `VERIFY_ALL = PASS`（脚本 :618 打印行本轮 grep 实证） | **本轮未跑**。`B2B_DESIGN.md:646` 历史输出记「STATE_MATRIX.json 行数 = 12」而现行矩阵为 14 行（本轮实读 :2-15）；草案 §5.5-2 判该差异为记录时点问题、`:599` 仅断言 `>=8`（转引）——重跑预期打印 14，**此为实读推演，以实际输出为准** |
| T3 | `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\bexec_n4_20261108\_n4_ast_scan.py` | 十一禁止符号逐符号 UNCHANGED、候选新增禁止边=无、新增边仅落九 hunk、消失边 0 | **本轮实跑 EXIT=0**，输出与本轮实读的 `_n4_ast_scan_out.txt` 逐字节一致（§5.2）；N-5 应用后须对应用后副本重跑 |
| T4 | `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\bexec_n4_20261108\_n4_fingerprint.py` | 绑定指纹逐项相符 | **脚本未跑**；本轮以独立 `python -I -X utf8 -c` + hashlib 实算等价完成 19 件（§2.1/§2.2） |
| T5 | 14 组 fixture 按 STATE_MATRIX.json 逐行断言 verdict / confidence / is_new / usable_as_crash_evidence 四元组（R3:42 同法） | 14/14 match | **本轮未跑**；R3:42 为历史转引（其自述档 3 实跑）。绑乙后 T5 为 N-5 必跑门禁 |

- T1 绑定说明（承草案 §3.7 缺陷修正）：旧草案原 T1 绑 `lead/b2b_candidate_20261106/tests/test_candidate.py`（:37 指向旧候选 `9656e432…`，转引），本定版**沿用改绑副本** `_test_candidate_lf.py` 为 T1 对象（唯一改动 = 第 37 行重定向，R3:152-154 转引；:37 内容本轮 grep 实证）。签发人若不认可该副本，须另做等价副本（唯一改动 = 第 37 行重定向到正式候选）。
- N-5 集成时 T1–T5 须对**应用后副本**重跑；版本不符立即 STOP（N-5:57）；应用前重核母本指纹（RULING_D24:52 转引）。

### 6.2 ★ 定版后仍缺的生效条件（缺一不可；本件全部不代办）
1. **`APPROVE_SCOPE` 未签署**——属来源会话任务签发人（N-4:49；裁决 Q1 明令不代签；补登件 §6-1）。
2. **来源会话任务签发人身份未落实**——N-1 验收记录 `sourceTaskId` 以计划任务号代替、身份核证登记 `unresolved`（补登件 §6-3）。
3. **任务书编号未落实**——本件 V2 无正式任务书编号；N-4:47 的正式槽位（来源会话签发人在 `lead/bexec_n4_20261108/B_EXECUTION_SPEC.md` 固定条款）登记动作未发生，本件不代做、不回写该槽位。
4. **N-5 正式应用未授权**——用户当轮明示为「先补登再应用」，应用须**另批**（补登件 §6-4、:18）。
5. **T1 绑定对象（改绑副本 `_test_candidate_lf.py`）待签发人确认**——草案轮该修正标 unconfirmed（草案 §3.7/§5.4-4）；本定版沿用之，签发人确认或另做等价副本前不生效。
6. **签署时点的 N-1 格式绑定未做**——N-4:49 要求签署时「以 N-1 记录格式绑定任务书与基线／候选哈希」，本件无签署、该绑定自然未发生。

### 6.3 本轮未验项（如实登记，不补造）
1. T1/T2/T5 本轮未跑（§6.1）；`PASS=29 FAIL=0`、14/14 match、`VERIFY_ALL = PASS` 均历史转引。
2. `RULING_D24.md` 原文本轮未逐行复读（仅指纹实算）——其 :52/:61 内容承草案与 N-4 原文转引。
3. `RULING_D25.md` 原文未直接实读（经 `B2B_DESIGN.md:43` 与 R3:23 转引，承草案 §5.5-5）。
4. `lead/b2b_isolated_20261107/INTEGRATION_REPORT.md`（D-25 第 6 步）本轮未审阅内容——隔离集成状态**未验**（补登件 §7 记其已演练但不构成放行）。
5. 母本既有采样机器（§5 存量面 6 包装函数）运行时行为未验；运行时退出码语义未复现（`B2B_DESIGN.md:652` 同口径）。
6. 候选对母本的正式应用未做（N-5 未发生）；本件落盘时母本指纹与 §2.1 绑定值一致（本轮实算）。

---

## 7 结论
- **grade = SPEC_FINAL_BOUND_YI（定版绑乙 · 未生效 · 非放行）**。本件把 N-4 任务书的矩阵选择定版为乙：允许范围 = H01–H09 九 hunk（§3）、通过判据 = 乙矩阵 14 行 + 七分支/空快照/复制失败/四类异常契约（§4）、API 基线 = 母本基线且候选新增禁止调用 = 0（§5，本轮 T3 实跑 EXIT=0）、测试命令 T1–T5 定版（§6.1）；甲 A–D 与甲矩阵口径**明确废止、不再绑定**（§3.2/§4.3）。
- 本件**不签 `APPROVE_SCOPE`、不代签候选 YES、不应用母本、不改既有草案与设计件、不改台账、不 commit、不 push**。生效须 §6.2 六项条件全部满足；在此之前 N-4 任务书整体仍不生效（N-4:49「身份、任一规则或版本缺失则任务书不生效」）。
- 本轮产出仅两件，均在唯一写域 `lead/n4_yi_final_20261108/`：本件 + `_n4v2_ast_rerun_out.txt`。母本轮前轮后指纹均为 `517889c6…`/399,508（§2.1 本轮实算），母本与既有件零改动。
