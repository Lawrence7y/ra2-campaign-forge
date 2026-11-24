# TASK · B2b 独立候选复审（D-25 第 5 步 · D-28 问一 = A）

**派发**：2026-11-06 18:4x，总控会话。**模型**：`magpie/work/cn:hy4free$high`（**不同于候选作者 gemini-3.8-flash**，D-28 明文要求）。**max_concurrency=2**。
**授权依据**：**D-28 裁决书**（`lead/d28_ruling_20261106/RULING_D28.md`）§0 `q1: A` ——
「立即安排独立候选复审及独立复核，复审模型必须不同于候选作者…这是**补齐既定下一门，而非签候选通过**」；
**D-25 裁决书**（`lead/d25_ruling_20261106/RULING_D25.md`）order 第 5 步。
**唯一写域**：`lead/b2b_candidate_review_20261106/`（新建目录，只写此目录内的新文件）。

---

## 0 一句话

候选已过机械门禁，**但还没人独立审过它的语义**。

你的任务是**逐项对照批准设计，判断这个候选是不是真的实现了设计**。
**不是重跑门禁，是审它「做对了没有」。**

## 1 上游绑定（开工先实算，不符就停）

| 对象 | 路径 | 必须等于 |
|:--|:--|:--|
| 正式母本 | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` / **399,508 B** |
| 被审候选 | `lead/b2b_candidate_20261106/qc151_trip.candidate.py` | `9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc` / **420,292 B** |
| 批准设计 | `lead/b2b_design_20261106/B2B_DESIGN.md` | `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf` / **66,735 B** |
| 设计预审 | `lead/b2b_preaudit_20261106/B2B_PREAUDIT.md` | `3f97f3a4664981961b72a91a60053fe8c867fa9d8e25442e7159c3046ccbf69f` / **20,615 B** |

**任一不符 ⇒ 立即停**，写 `STOP_UPSTREAM_DRIFT.md`。
（本机没有 `sha256sum`/`wc`，用 Python hashlib。）

## 2 ★ 证据等级纪律（D-28 明文要求，违反即废）

D-28 裁决书明确要求：

> 「候选『全绿』**限于机械门禁和报告字段**」

⇒ **你的结论里必须严格区分这三档，不许混用**：

| 档 | 含义 | 能写成什么 |
|:--|:--|:--|
| **机械门禁通过** | `check_candidate.py` 9/9 PASS | 只能说「门禁通过」 |
| **报告字段为 true** | `CANDIDATE_REVIEW.md` 里那五个字段值为 true | 只能说「报告字段声明为 true」 |
| **语义已独立复核** | **你这次做的事** | 只有你逐项核过才能说 |

**★ 严禁写「候选全绿」「候选已验证」「候选可用」** —— 除非你逐项核过并给出证据。
**★ 严禁把「报告字段说 testsActuallyRun=true」当成「测试真跑过」** —— 你自己重跑才算。

## 3 必须逐项对照的五件事（D-25 第 5 步原文）

### 3.1 状态矩阵
对照 `lead/b2b_design_20261106/STATE_MATRIX.json`（14 条）与候选里 `classify_except_freshness` 的实现：
- 14 个状态是否**全部**在代码里有对应分支？
- `unknown` 的置信是否真的是 `none`（不是 `high`）？
- **三态可分性（★ 2026-11-06 20:1x 总控裁定修正，见文末「裁定附录」）**：
  「三态可分」指**状态值层面** `unknown` / `absent_confirmed` / `present` 三种**状态**互不相同，
  **不是**指 `None` / `{}` / `{"exists": False}` 三种**原始输入**必须输出不同。
  按批准设计 `B2B_DESIGN.md:100-106`，这三种原始输入**本就应该归一到 `unknown/none`**
  （`:106` 明写「`{"exists": False}`（无 `state`）**不再是「确认无件」**」）。
  ⇒ 验收应核：**`{"state": "absent_confirmed", "exists": False}` 是否与 `unknown` 输出不同**；
  `None` / `{}` / `{"exists": False}` 三者相同是**设计意图，不构成缺陷**。

### 3.2 调用传参
- `:5939`（母本行号）对应到候选是 `:6167-6168`，是否真的传了 `pre_freshness_snapshot`？
- `finalize_trip` 签名（候选 `:6528` 附近）与 `copy_post_except_evidence` 签名（候选 `:4701-4704`）是否与设计一致？
- **有没有别的地方**还有一个 `copy_post_except_evidence(...)` 调用没传参？（用 AST 全量扫）
- `finalize_trip` 在候选里的**所有**调用点是否都兼容新形参（默认值语义）？

### 3.3 输出字段
- **7 个 `FRESHNESS` 字段**是否在早退 / 正常 / 异常**三条路径上都落盘**？
- **12 键 `info`** 是否在**正常路径**与 **`src_missing` 分支**落盘？
  （★ 20:1x 裁定修正：`info` 是 `dict | None`，**不要求**在 `copy_failed` 等异常路径也落 12 键 ——
  批准设计 `:605` 明写写入点为「正常路径与 `src_missing` 分支」；见文末「裁定附录」裁定二）
- 字段名是否与设计 `## 5 字段契约` 逐个一致？
- 有没有字段只在某一条路径上有、另两条没有？

### 3.4 F/E 分离
- 设计 `## 6 F/E 分离的实现级约束` 是否在代码里**有具体落点**（不只是注释）？
- `freshness_*` 字段是否会**影响退出码**？（母本 `:5985-5990` 是唯一影响退出码处，`:677` 明令「不得用 sha 变化判 crash」）
- 用 AST 核：退出码判据的代码路径里**有没有读到** `freshness_*`？

### 3.5 范围限制
- 候选相对母本的 diff，是否**只在**九个 hunk 的范围内？
- 有没有**夹带**设计外的改动？（用 `difflib` 全量比对，逐 hunk 归因到 H1–H9）

## 4 必须亲自重跑（不许信报告）

D-28 原话：「历史 29 项和 43 项测试本裁决阶段均未运行，不能记为本阶段通过」。

你要：
1. **亲自跑一次候选的测试**（`lead/b2b_candidate_20261106/tests/test_candidate.py`），记录命令、输出的 PASS/FAIL 数、退出码；
2. **亲自跑一次 `check_candidate.py`**，核是否 9/9；
3. 把两次的**真实输出**存成本地文件（你的写域内），不要引用旧输出。

**★ 若测试失败，如实报，不许改测试。**

## 5 交付物（写进 `lead/b2b_candidate_review_20261106/`）

### 5.1 `CANDIDATE_SEMANTIC_REVIEW.md` —— 主判定书

必须含：
- 头部：四件实算 SHA256 + 字节数；
- 一行 `verdict: PASS` 或 `verdict: BLOCKED`（独立成行）；
- **五节**（标题一字不差）：
  - `## 1 状态矩阵对照`
  - `## 2 调用传参核对`
  - `## 3 输出字段核对`
  - `## 4 F/E 分离核对`
  - `## 5 范围限制核对`
- 「## 阻断项」小节：逐条列 `BLOCKED` 项，每条带 `文件:行` + 后果 + **关闭所需证据**；
- 「## 未验」小节（非空）；
- 「## 证据等级说明」小节：明确写出「机械门禁通过 / 报告字段为 true / 语义已独立复核」三档各自对应什么，**并声明本判定书属于哪一档**。

### 5.2 `_review_probe.py` + `_review_probe_out.txt`

你实际用的验证脚本与真实输出。必须包含：
- 四件指纹实算；
- AST 全量扫 `copy_post_except_evidence` 所有调用点及参数；
- AST 扫退出码判据路径是否读 `freshness_*`；
- `difflib` 全量 diff 并逐 hunk 归因到 H1–H9。

### 5.3 `_test_rerun_out.txt` 与 `_gate_rerun_out.txt`

你**亲自重跑**的测试与门禁的真实输出。

### 5.4 `review/SEMANTIC_REVIEW_AUDIT.md`

独立复核（见 §7）。

## 6 硬性纪律

1. **零真机、零采样代码**、不 commit、不 push。
2. **只读**：`ra2youli/**`、`out/re_work/**`、`lead/re_line_20261105/**`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md`、
   `lead/b2b_design_*/**`、`lead/b2b_preaudit_*/**`、`lead/b2b_candidate_*/**`（**被审对象也不许改**）一律不改。
3. `python -I -X utf8`，绝对路径；算指纹用 Python hashlib。
4. 引用追到「文件:行」或「实跑输出」；拿不到写「未验」。
5. **★ 不许因为门禁过了就判 PASS** —— 门禁只验格式，你验的是语义。
6. **★ 不许修改候选、测试或门禁来让结论好看。**

## 7 判定规则（硬性）

**只要满足任一条，`verdict` 必须是 `BLOCKED`：**
- 14 个状态里有任何一个在代码里**找不到**对应分支；
- `unknown` 在代码里给了 `high` 置信；
- **（★ 20:1x 裁定修正）状态值层面不可分**：`{"state":"absent_confirmed",...}` 与 `unknown` 的输出**相同**；
  ★ 注意：`None` / `{}` / `{"exists": False}` 三者输出相同**不算阻断**（见 3.1 与文末裁定附录）；
- 存在**另一个** `copy_post_except_evidence` 调用点没传 `pre_freshness_snapshot`；
- 存在 `finalize_trip` 调用点因新形参而不兼容（会抛 TypeError）；
- **（★ 20:1x 裁定修正）7 个 FRESHNESS 字段在任一条路径缺失**
  （★ 注意：**12 键 `info` 只在「正常路径」与「`src_missing` 分支」落盘即可** —— 批准设计 `:605` 定义为 `dict | None`；
  `copy_failed` 路径没有 `evidence_copy` 行**符合设计**，不算阻断）；
- `freshness_*` 被退出码判据读取；
- 候选 diff 里有**超出 H1–H9 范围**的改动；
- 你亲自重跑的测试**有 FAIL**。

**`verdict: PASS` 的准确含义**：候选**语义上**实现了批准设计；**不等于可以应用到母本**（D-25 第 6 步隔离副本集成还没做）。

## 8 独立复核（必做）

另起**新上下文**复核员：
- 逐条打开主判定书每个 `文件:行`，核是否真说了那句话；
- 亲自重跑 `_review_probe.py`，核输出一致；
- **专项 A**：判定书有没有把 `BLOCKED` 写成 `PASS`；
- **专项 B**：有没有把「门禁通过」或「报告字段为 true」写成「语义已复核」；
- **专项 C**：有没有把「语义 PASS」写成「可应用到母本」。

复核件必须含：`subjectSha256` / `subjectBytes` / `checkedEveryRow` / `noOverreach` / `blockedCount`。

## 9 确定性门禁

写 `check_semantic_review.py`，`python -I -X utf8` 跑，检查：
- 主判定书存在，含 4 个不同 64-hex + 4 个字节数；
- 含 `^verdict:\s*(PASS|BLOCKED)\s*$` 一行；
- 含五个小节标题（状态矩阵对照 / 调用传参核对 / 输出字段核对 / F/E 分离核对 / 范围限制核对）；
- 含「## 阻断项」与「## 未验」「## 证据等级说明」小节，且「未验」非空；
- `_review_probe.py` / `_review_probe_out.txt` / `_test_rerun_out.txt` / `_gate_rerun_out.txt` 都存在且非空；
- `_test_rerun_out.txt` 里含 `PASS=` 与 `FAIL=`（真实重跑痕迹）；
- 复核件含 `checkedEveryRow: true`、`noOverreach: true`；
- **一致性**：若 `verdict: PASS`，则正文里不得出现 `BLOCKED` 作为已成立结论（脚本扫「## 阻断项」小节应为空或写「无」）。

退出码 0 = PASS。**exitCode 与完整输出写进交付说明。**

---

## 裁定附录（2026-11-06 20:1x · 总控裁定，用户明示「1」授权）

**背景**：本任务书原 §3.1 与 §7 的两条硬性规则，与**批准设计**直接冲突，
导致语义复审对候选判出 `BLOCKED`（`CANDIDATE_SEMANTIC_REVIEW.md` 的 B-1 / B-2 两条）。
复审员做得对（按规则判 BLOCKED 并登记口径冲突、未擅改判），**但规则本身写错了**。

**裁定：两处均按批准设计口径（即复审员列的「乙」方案）。**

### 裁定一 · 三态可分性（关闭 B-1）

- **作废**：原 §7「`None` / `{}` / `{"exists": False}` 三种输入有任意两种输出相同 ⇒ BLOCKED」。
- **生效口径**：「三态可分」= **状态值层面** `unknown` / `absent_confirmed` / `present` 互不相同。
- **依据**：批准设计 `B2B_DESIGN.md:100-103` 明文规定三种原始输入**都归一到 `unknown/none`**；
  `:106` 明写「`{"exists": False}`（无 `state`）**不再是「确认无件」**，确认无件必须显式带 `state="absent_confirmed"`」。
- **验收改为**：核 `{"state":"absent_confirmed","exists":False}` 与 `unknown` 是否输出不同。
- **候选实测（复审员已做）**：设计口径下三态**可分**（`:4667` 的 `absent_confirmed` → `new_first_appearance/high`）；
  原始输入全同是**设计意图**，不是缺陷。

### 裁定二 · 12 键 info 落盘范围（关闭 B-2）

- **作废**：原 §7「12 键 info 在某条路径缺失 ⇒ BLOCKED」。
- **生效口径**：**7 个 FRESHNESS 字段**必须三路径全落盘；**12 键 `info` 只在「正常路径」与「`src_missing` 分支」落盘即可**。
- **依据**：批准设计 `:605` 把 `EXCEPT.evidence_copy` 定义为 `dict | None`，
  写入点明写「H04（§4 #4，**正常路径与 `src_missing` 分支**）」；
  `:434-435` 的 diff 明写 `rec.add(..., None, ...)`；`:78-81` 的 N4「三出口全落盘」只针对 7 个 F 字段。
- **验收改为**：核 7 个 F 字段三路径齐全 + `info` 在正常与 `src_missing` 两路径齐全。
- **候选实测（复审员已做）**：7 个 F 字段三路径 `True/True/True`；
  `info` 12 键 `[True, False, False]`、`EXCEPT.evidence_copy` 次数 `[1,1,0]` —— **与设计完全一致**。

### 由此产生的结论

- `CANDIDATE_SEMANTIC_REVIEW.md` 的 **B-1 / B-2 两条阻断，按本裁定不再成立**。
- 复审员在「已排除的硬性条件」里**逐条实跑确认的七项**（14 状态覆盖、`unknown` 非 `high`、
  唯一调用点已传参、`finalize_trip` 兼容、`freshness_*` 不进退出码、diff 未超出 H1–H9、重跑测试 `PASS=29 FAIL=0`）
  **全部继续有效**。
- **本裁定只改验收口径，不改候选、不改批准设计、不改母本。**
- ★ **本裁定不构成「候选可应用到母本」** —— D-25 第 6 步（隔离副本离线集成）仍未做。
- ★ 复审员登记的其余事项（引用精度瑕疵 1/2、措辞观察、`STATE_MATRIX` #1 条件覆盖偏差、
  键名 camelCase↔snake_case 映射未验、门禁读旧输出）**保持原状态登记，不因本裁定消失**。
