# _la_draft4_yi_supersede_jia.md — 第四笔草案：「以乙替代甲」补登（供 Leader 整段复制追加；本文件本身不是台账，不入台账）

- **核对结论**：成立，附两条**引用限定**（①乙件 §1 引文未能在裁决书逐字定位；②裁决书整体 unconfirmed、Q1 仅方向意见——登记不等于绑定生效。均已写入草案正文；证据见文末「核对记录」）。全部指纹、九 hunk、+255/−13、`_finish(` 14 处、四项分支差异、四条未完成生效条件均在现盘独立复现。
- **建议入账位置**：`lead/GOAL_THREE_TARGETS_20261018.md` 尾部追加为新节（暂编 §608；Leader 可重排）。不追加进 PENDING_DECISIONS.md：该件明确「只放需要裁决的事项、已裁决整条删除」，补登是登记动作而非待裁项；四条未完成条件中的 N-5 应用授权如需立新待裁条目，属来源会话动作，本草案不代立。
- **基线指纹（追加前基线，两条）**：
  - `lead/PENDING_DECISIONS.md` SHA256 = `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7`（382 行口径；52419 B，本会话实算同值）
  - `lead/GOAL_THREE_TARGETS_20261018.md` SHA256 = `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede`（759518 B，本会话实算同值）

---

## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓

## §608 · 补登登记：「以乙替代甲」——B 链绑定改挂乙（B2B 设计 + STATE_MATRIX + LF 候选），九 hunk + 四项分支差异 + 版本指纹全量绑定；**登记而非放行**（2026-11-08）

- **性质与依据**：补登件 = `lead/b2b_yi_supersede_20261108/YI_SUPERSEDE_JIA_BINDING.md`（SHA256 = `255356ca789955cc2c084388f547a1435feb310f210617b988f761e7ff331c7b` / 7344 B，本会话实算与编排方指纹一致）。依据 = D-31 方向裁决 Q1（`lead/direction_ruling_20261108/RULING_DIRECTION.md`）；用户当轮明示「先补登再应用」——即补登先行、N-5 应用另批。**本节只完成登记，不构成 `APPROVE_SCOPE` 签署、不构成 N-5 应用放行**。
- **版本绑定指纹（11 件，YI §4；本会话逐一 hashlib 实算 11/11 MATCH）**：
  - 母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` = `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` / 399,508 B
  - 候选（乙实现）`lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` = `ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2` / 412,759 B
  - 候选 diff `lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff` = `72b108021637cf7d225a9b109a542ec10c934abb1a8e40b8850a82c6bea9cdb9` / 18,454 B
  - 乙设计 `lead/b2b_design_20261106/B2B_DESIGN.md` = `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf` / 66,735 B
  - 乙矩阵 `lead/b2b_design_20261106/STATE_MATRIX.json` = `1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016` / 3,558 B
  - 甲设计（不再绑定，仅留档对照）`lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md` = `deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f` / 11,638 B
  - 甲预审（NO 依据）`lead/b2_preaudit_20261106/B2_PREAUDIT.md` = `a108a6e45f42c449db5d228abc469e5c17d40db0b04f15aa32105adff8905449` / 28,410 B
  - 乙预审（YES 依据）`lead/b2b_preaudit_20261106/B2B_PREAUDIT.md` = `3f97f3a4664981961b72a91a60053fe8c867fa9d8e25442e7159c3046ccbf69f` / 20,615 B
  - R3 复审（PASS 依据）`lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md` = `96071dd9d58e30a54966a2a1e16f4af918c2f8dd5825363510e8ced8bc6a8fea` / 24,661 B
  - N-4 任务书（草案态，未生效）`lead/bexec_n4_20261108/B_EXECUTION_SPEC.md` = `be73333541ddef9a9782aff2ae2f98e657d50d254c50dad5acdf8052ebc25358` / 32,183 B
  - 裁决书 `lead/direction_ruling_20261108/RULING_DIRECTION.md` = `0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653` / 16,514 B
- **变更范围（甲 A—D 四处 → 乙 H01—H09 九 hunk）**：乙改动面 **+255 / −13**（YI 引 R3:43；**本会话 `git diff --no-index --numstat` 独立实测 255/13**；`CANDIDATE_LF.diff` 中 `^@@` 计数 = **9**，本会话实测）；`_finish(` 在候选全文 **14 处** = 1 处 `def` @:4628 + 13 处调用（:4644/:4649/:4653/:4659/:4662/:4667/:4674/:4679/:4682/:4687/:4691/:4694/:4697，本会话 grep 实测与 YI §5 清单一致）。甲原范围 A—D 四处（净增约 31 行）**不再适用**。
- **四项分支差异（YI §5 表前四行 = MATRIX_BINDING_FACTS.md §4.1 :46-51，本会话实读逐一对应）**：

  | 分支 | 甲 | 乙 |
  |:--|:--|:--|
  | `absent_both` 的 confidence | `n/a` | `low`（is_new=False，「文件未出现」不能证无崩溃） |
  | `vanished` 的 confidence | `high` | `none`（不给 high、is_new=null、须人工复核） |
  | 空快照 `{}`（≡exists=False） | 折叠为 `absent_both`/`new_first_appearance` | `unknown`/`none`、未知 ≠ 不存在，不作本趟新出现归因 |
  | `mtime_pre` 缺失 | `elif` 守卫跳过比较 → `leftover_unchanged`/`high` | `leftover_unchanged`/`medium`（盲区如实标注、不虚报 high） |

  另随登记的值域/字段差（MATRIX_BINDING_FACTS.md §4.2/§4.3，本会话实读）：confidence 值域 {high, low, medium, n/a} → {high, medium, low, none}（none=不可判，显式区别于 low）；verdict 值域 6 值 → 9 值（新增 `unknown`/`error_pre_snapshot`/`post_read_error`）；新增字段 `is_new`/`note`/`usable_as_crash_evidence`/`pre_snapshot_state`/`captured_at_iso`（另 H08 单独落 `captured_at_iso_pre`）。**★ 禁止混用甲预期**：任何验收、门禁、复算一律以乙的九 hunk 与矩阵为准，不得以甲的 A—D 四处或甲的 `n/a` 值域作为验收基准。
- **四条未完成生效条件（YI §6，缺一不可）**：① **`APPROVE_SCOPE` 未签署**——属来源会话任务签发人，补登件不代签（裁决 Q1 明令）；② **N-4 任务书仍草案态**——`B_EXECUTION_SPEC.md` 判 `SPEC_DRAFT`、明写不生效，须按乙重制并更新全部绑定后才具备放行能力；③ **任务书编号/身份未落实**——N-1 验收记录 `sourceTaskId` 以计划任务号代替、身份核证登记为 unresolved；④ **N-5 正式应用未授权**——用户当轮明示「先补登再应用」，应用需**另批**。母本 `qc151_trip.py` 于补登件落盘时未被修改（`517889c6…` / 399,508 B，本会话复算 MATCH）；D-25 第 6 步隔离副本离线集成已由 `lead/b2b_isolated_20261107/INTEGRATION_REPORT.md` 完成演练（PASS=29 FAIL=0）但同样不是放行。
- **引用限定（本会话如实登记两点，引用本节者须连带）**：① YI §1「裁决原文（Q1 摘录）」引文在裁决书中 grep（「先补登再应用」「必须由有权来源会话补登」「矩阵选择无需新增实施授权」）= **0 逐字命中**——引文可能转引题给裁决原文而非汇编件自身措辞，逐字出处**未验**；实质内容（技术方向采乙、禁止混用甲预期、不代签 APPROVE_SCOPE、N-5 正式应用须用户当轮明示）在 RULING_DIRECTION.md:23/:62/:66 有对应裁定，**引用时以 :23/:66 原句为准**。② RULING_DIRECTION.md 整体状态 **unconfirmed**（:5/:77），Q1 为「待有权签发人确认的方向意见」（:23）、MATRIX_BINDING_FACTS.md:98 四项决断留白待签发人（:102「建议绑乙」非裁决）——**本节登记「以乙替代甲」是登记动作，不宣告 N-4 正式绑定已生效**（与补登件自述一致）。
- 本节**零真机、零采样代码、零母本改动、零既有设计件改动、未 commit、未 push**。

## ↑↑↑ 草案正文结束 ↑↑↑

---

## 核对记录（不入台账）

- **事实基础**：成立（附两条引用限定，均已写入草案正文）。
- **逐项证据**（本会话实读/实跑）：
  1. 补登件全件亲读（YI_SUPERSEDE_JIA_BINDING.md，105 行 + 尾行）：§4 指纹表 = :43-55；九 hunk/+255−13/_finish 14 处 = §5（:57-63）；四项分支差异表 = §5（:65-77，注：该表标签「四项分支差异」但列 8 行，前四行 = MATRIX_BINDING_FACTS.md §4.1 四处分支取值差，后四行 = §4.2/§4.3 值域差与字段差——草案正文已按此如实分层）；四条未完成生效条件 = §6（:81-94）。
  2. **指纹独立实算**：§4 表 11 件全部 MATCH（`_la_fpcheck2.py`，23/23 SUMMARY 含其余上游件）；母本、候选、diff、乙设计、乙矩阵、甲设计、甲预审、乙预审、R3 复审、N-4 任务书草案、裁决书逐一核对（哈希前 8 位 + 字节数全同）。
  3. **九 hunk 与增删行独立实测**：`git diff --no-index --numstat <母本> <候选>` → `255 13`；`grep -c "^@@" CANDIDATE_LF.diff` → 9；`grep -c "_finish(" qc151_trip.candidate_lf.py` → 14（def@:4628 + 13 调用行与 YI §5 清单一致）；候选 `_finish` 调用实值（absent_both→low、vanished→none、unknown/error_pre_snapshot/post_read_error、leftover_unchanged→medium/high）与矩阵差异方向一致。
  4. 四项分支差异出处亲读：`lead/matrix_binding_20261108/MATRIX_BINDING_FACTS.md:46-51`（§4.1 表四行逐项对应）；值域/字段差 = §4.2（:53-59）/§4.3（:61-63）。
  5. 引用限定实测：`grep -n "先补登再应用\|必须由有权来源会话补登\|矩阵选择无需新增实施授权" RULING_DIRECTION.md` = 0 命中；RULING_DIRECTION.md:5/:23/:62/:66/:77 亲读（Q1 措辞、unconfirmed 状态、partial 三限制、汇总表行）；MATRIX_BINDING_FACTS.md:98/:102 引文（四项决断留白待签发人、建议绑乙非裁决）见 RULING_DIRECTION.md:23 转述，本会话未直读 :98/:102 原行——该两行按裁决书转引登记，标注为转引。
  6. 母本未改：qc151_trip.py SHA256 = 517889c6…/399,508 B 本会话实算 MATCH。
- **被核对象绑定**：YI_SUPERSEDE_JIA_BINDING.md SHA256 = 255356ca789955cc2c084388f547a1435feb310f210617b988f761e7ff331c7b，字节数 = 7344。
