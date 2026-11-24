# B2b 「以乙替代甲」正式补登记录

- **立件日期**：2026-11-08
- **依据**：D-31 方向裁决 Q1（`lead/direction_ruling_20261108/RULING_DIRECTION.md`）
- **性质**：**补登件（登记而非放行）**。本件只完成「乙替代甲」的正式登记与指纹绑定，
  **不构成 `APPROVE_SCOPE` 签署、不构成 N-5 应用放行**。
- **零真机、零采样代码、未改母本、未改既有设计件**。

---

## 1 裁决原文（Q1 摘录）

> **Q1**：N-4 绑定乙（B2B 设计 + STATE_MATRIX 及现行 LF 候选）；必须由有权来源会话补登
> 「以乙替代甲」，更新九 hunk 范围、矩阵/字段/版本绑定及签署，**禁止混用甲预期**。
> 本裁决**不代签 `APPROVE_SCOPE`**。矩阵选择无需新增实施授权；
> N-5 正式应用依本轮明确边界**待用户当轮明示**，技术门仍须补齐。

**用户当轮明示（2026-11-08）**：选「**先补登再应用**」——即本件先行，应用另批。

---

## 2 甲被否决的事实基础

| 项 | 内容 | 出处 |
|---|---|---|
| 甲预审结论 | `verdict: NO`（`shouldApply = NO`，全面阻断） | `lead/b2_preaudit_20261106/B2_PREAUDIT.md:17`；`lead/re_line_20261105/B1_HARNESS_PATCH/PRE_AUDIT.md:4` |
| 否决理由一 | 六条旧错中 `E1 = NOT_FIXED`（旧规则第一条即触发 NO） | `B2_PREAUDIT.md:20` |
| 否决理由二 | 新增问题 `severity=high` 共 5 条（N1/N2/N4/N5/N11） | `B2_PREAUDIT.md:21` |
| 独立性 | 两条规则**各自独立足以判 NO** | `B2_PREAUDIT.md:22` |
| 甲的状态 | 明写「本文件只是设计，应用前必须重新走一遍 B1 的预审硬门」；**甲无候选实现** | `lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md:198` |

## 3 乙的批准链（四节闭合）

| # | 环节 | 结论 | 出处 |
|---|---|---|---|
| ① | 乙设计独立预审 | `verdict: YES`（边界：可以拿去编写候选；**不等于可以应用到母本**） | `lead/b2b_preaudit_20261106/B2B_PREAUDIT.md:13`、`:16`、`:17` |
| ② | 乙候选语义复审（R3） | `verdict: PASS`（边界：**PASS ≠ 可应用到母本**，D-25 第 6 步未做） | `lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md:21`、`:23`、`:122`、`:137` |
| ③ | 两条独立重建路径 | 母本+设计 §4 九 hunk == 候选；母本+CANDIDATE_LF.diff == 候选（**逐字节**） | `R3:32-34`；`_review_probe_r3_out.txt:124,126` |
| ④ | 指纹闭合 | 候选 `ca23c116…`/412,759 与母本 `517889c6…`/399,508 双端一致 | 本件 §4 |

## 4 版本绑定（本会话 `python -I -X utf8` + `hashlib` 实算）

| 角色 | 路径 | SHA256（完整 64 位） | 字节数 |
|:--|:--|:--|--:|
| **母本** | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399,508 |
| **候选（乙实现）** | `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` | `ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2` | 412,759 |
| **候选 diff** | `lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff` | `72b108021637cf7d225a9b109a542ec10c934abb1a8e40b8850a82c6bea9cdb9` | 18,454 |
| **乙设计（绑定对象）** | `lead/b2b_design_20261106/B2B_DESIGN.md` | `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf` | 66,735 |
| **乙矩阵（绑定对象）** | `lead/b2b_design_20261106/STATE_MATRIX.json` | `1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016` | 3,558 |
| 甲设计（**不再绑定**，仅留档对照） | `lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md` | `deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f` | 11,638 |
| 甲预审（NO 的依据） | `lead/b2_preaudit_20261106/B2_PREAUDIT.md` | `a108a6e45f42c449db5d228abc469e5c17d40db0b04f15aa32105adff8905449` | 28,410 |
| 乙预审（YES 的依据） | `lead/b2b_preaudit_20261106/B2B_PREAUDIT.md` | `3f97f3a4664981961b72a91a60053fe8c867fa9d8e25442e7159c3046ccbf69f` | 20,615 |
| R3 复审（PASS 的依据） | `lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md` | `96071dd9d58e30a54966a2a1e16f4af918c2f8dd5825363510e8ced8bc6a8fea` | 24,661 |
| N-4 任务书（**草案态，未生效**） | `lead/bexec_n4_20261108/B_EXECUTION_SPEC.md` | `be73333541ddef9a9782aff2ae2f98e657d50d254c50dad5acdf8052ebc25358` | 32,183 |
| 裁决书 | `lead/direction_ruling_20261108/RULING_DIRECTION.md` | `0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653` | 16,514 |

## 5 变更范围（由甲 A—D 四处 → 乙 H01—H09 九 hunk）

**乙的改动面**（`R3:43` 实证）：`+255 / -13`，九 hunk（H01–H09）；
`_finish(` 在候选全文 **14 处**（1 处 `def` @`:4628` + **13 处调用**：
`:4644/:4649/:4653/:4659/:4662/:4667/:4674/:4679/:4682/:4687/:4691/:4694/:4697`）。

**甲原范围**（不再适用）：A—D 四处，净增约 31 行。

**矩阵/字段变更**（甲→乙，四项分支差异，详见 `MATRIX_BINDING_FACTS.md §4`）：

| 分支 | 甲 | 乙 |
|:--|:--|:--|
| `absent_both` confidence | `n/a` | `low` |
| `vanished` confidence | `high` | `none` |
| 空快照 `{}`（≡`exists=False`） | 折叠为 `absent_both`/`new_first_appearance` | `unknown`/`none`，不作新出现归因 |
| `mtime_pre` 缺失 | `elif` 守卫跳过 → `leftover_unchanged`/`high` | `leftover_unchanged`/`medium` |
| `confidence` 值域 | 含 `n/a` | `high`/`medium`/`low`/`none`（`none ≠ low`） |
| `verdict` 值域 | 6 值 | 9 值 |
| 新增出口 | — | `unknown`/`error_pre_snapshot`/`post_read_error` |
| 新增字段 | — | `is_new`/`note`/`usable_as_crash_evidence`/`pre_snapshot_state`/`captured_at_iso` |

**★ 禁止混用甲预期**：任何验收、门禁、复算一律以乙的九 hunk 与 Zustand 矩阵为准；
不得以甲的 A—D 四处或甲的 `n/a` 值域作为验收基准。

## 6 生效条件与未完成项

**本件已完成**：乙替代甲的正式登记、九 hunk 范围更新、矩阵/字段/版本指纹绑定。

**本件未完成（生效前置，缺一不可）**：

1. **`APPROVE_SCOPE` 未签署** —— 属来源会话任务签发人，本件不代签（裁决 Q1 明令）。
2. **N-4 任务书仍为草案态** —— `B_EXECUTION_SPEC.md` 判 `SPEC_DRAFT`、明写「不生效」；
   须按乙重制并更新全部绑定后才具备放行能力。
3. **任务书编号/身份未落实** —— N-1 验收记录中 `sourceTaskId` 以计划任务号代替、身份核证登记为 `unresolved`。
4. **N-5 正式应用未授权** —— 用户当轮明示为「先补登再应用」，应用需**另批**。

**因此本件不构成 N-5 放行**；母本 `qc151_trip.py` 于本件落盘时**未被修改**
（指纹 `517889c68f037ab6…5ba636` / 399,508 B，与 §4 一致）。

## 7 与 D-25 第 6 步的关系

D-25 第 6 步「隔离副本离线集成」已由 `lead/b2b_isolated_20261107/INTEGRATION_REPORT.md` 完成演练
（母本集成前后三次实算指纹零漂移，`PASS=29 FAIL=0`）。但该件**同样不构成「可应用到母本」的放行**
（其自有声明）。本补登件与该件共同构成 N-5 的技术前置，但两者都不是放行。

---

**本件写入域**：`lead/b2b_yi_supersede_20261108/`（唯一）。
**未 commit、未 push。零真机、零采样代码。**
