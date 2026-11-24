# TASK · B2b 独立设计预审（D-25 第 3 步 · 硬门）

**派发**：2026-11-06 15:5x，总控会话。**模型**：`magpie/antigravity/gemini-3.8-flash$high`（**刻意与环境作者 hy4free 不同族**，执行者≠核验者）。
**max_concurrency=2**。
**授权依据**：**D-25 裁决书**（`lead/d25_ruling_20261106/RULING_D25.md`）第 3 节 order 第 3 步：
「来源会话派**独立于作者的预审员**审查绑定版本设计和完整 diff，再由**独立复核员**复查。通过门为无未关闭阻断项、无未解释语义变化、范围符合离线文件处理边界、材料与对象指纹一致。**旧 B2 的 NO、旧 E3/E4/E6 评价与历史测试均不继承为 B2b 通过。**」
**唯一写域**：`lead/b2b_preaudit_20261106/`（新建目录，只写此目录内的新文件）。

---

## 0 这道门是干什么的

上一轮 **B2 设计**就是死在这道门上（`lead/b2_preaudit_20261106/B2_PREAUDIT.md` 判 `verdict: NO`）。
领队随后手写 **B2b** 修正版（`lead/b2b_design_20261106/B2B_DESIGN.md`，66,735 B，9 个 diff hunk），
已过设计层复核（清单↔hunk 对齐、unknown 不映射 high、五个早退覆盖）。

**但 B2b 还没过独立预审。** 你现在就是这道门。

**★ 关键：不要继承 B2 的结论。**裁决书明写「旧 B2 的 NO 与旧评价不继承为 B2b 通过」——
意思是 B2b 要**从零判定**，不是「B2 挂了所以 B2b 假定有问题」，也不是「B2b 是修正版所以假定更好」。

---

## 1 三件基准（开工先实算，不符就停）

| 对象 | 路径 | 预期指纹 | 预期字节 |
|:--|:--|:--|--:|
| 正式母本 | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399,508 |
| 被审新设计 | `lead/b2b_design_20261106/B2B_DESIGN.md` | 自己算（设计稿，**不要求等于某个固定值**，但要在文首记录你审的是哪个版本） | — |
| 被否的旧设计 | `lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md` | `deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f` | 11,638 |

**母本指纹不符 ⇒ 立即停，写 `STOP_MOTHER_DRIFT.md` 结束。**
（本机没有 `sha256sum`/`wc`，用 Python hashlib。）

---

## 2 必须逐个 hunk 验（这是本次核心）

B2b 声称 9 个 hunk。**你要逐个打开母本核，不许抽样：**

| hunk 头 | 断言 | 你要核什么 |
|:--|:--|:--|
| `@@ -212,6` | 载体内文件清单处 | 母本 212 行附近是不是这件事；改法是否成立 |
| `@@ -4458,6` | `backup_carrier` 写 `exists` 键 | 写入侧是否真写 `"exists": True`；键名与判定侧是否一致 |
| `@@ -4558,8` | `copy_post_except_evidence` 签名 | 新形参名、默认值、返回类型 |
| `@@ -4572,20` | 新鲜性判定主体 | 三态是否真可分（unknown / absent_confirmed / present）；`unknown` 是否给 `none` 而非 `high` |
| `@@ -5906,7` | `finalize_trip` 签名 | 新形参是否加在末尾、是否破坏既有调用 |
| `@@ -5936,7` | **`:5939` 调用点传参** | ★ **这是 B2 的死因** —— 母本 `:5939` 是 `copy_post_except_evidence(rec, carrier_dir, out_dir)`，这个 hunk 是否真覆盖它、真加了参数 |
| `@@ -6294,6` | `bak` 预初始化 | 是否在 `try` 之前、五个早退能否安全走到 |
| `@@ -6386,6` | 快照构造 | 是否在 `:6387 bak = backup_carrier(...)` 之后且被 `try` 覆盖 |
| `@@ -7122,7` | `finalize_trip` 调用点 | 是否真传了新形参 |

**★ 行号偏移检查（B2b 最大的技术风险）**：
hunk `@@ -4558,8 +4577,131 @@` 加了 **131 行**。
后面所有 hunk 的**新文件行号**都会因此偏移。你要核：
- 每个 hunk 的 `-` 侧行号（原文行号）是否对得上母本；
- 各 hunk 应用后是否会产生**行号冲突或重叠**；
- 按 hunk 顺序依次应用后，结果是否仍然语法正确（可用 `ast.parse` 验证拼接后的结果，**但不许真写母本**）。

---

## 3 五个早退路径逐条验

母本 `main` 内、`:6387` 之前有 5 个 `return`：`:6340 / :6349 / :6361 / :6374 / :6377`。

**逐条核**：B2b 的 `@@ -6294,6`（bak 预初始化）与 `@@ -6386,6`（快照构造）之后，
这五条路径上 `_pre_freshness_snapshot` 的值是什么？`finalize_trip` 拿到什么？
会不会抛 `NameError` / `UnboundLocalError`？

**★ 注意 D-25 裁决的更正**：未赋值裸名是 `NameError`；只有补了局部赋值但被早退绕过才是 `UnboundLocalError`。
**别写错异常类型。**

---

## 4 状态矩阵验

读 `lead/b2b_design_20261106/STATE_MATRIX.json`（14 条）。逐条核：
- `unknown` 的 confidence 是否为 `none`（**不能是 high**）；
- `absent_confirmed` / `absent_both` / `leftover_unchanged` / `new_write` / `rewritten_same_content` / `missing_sha` / `vanished` 是否都在；
- **`usableAsCrashEvidence` 是否全为 false**（若某条为 true，判断是否合法）；
- 有没有「未知被当作不存在」的路径。

---

## 5 F/E 分离验

母本 `:672-708` 是 `except_set_diff`，`:677` 明令「**不得用 sha 变化判 crash**」，`:5985-5990` 是唯一影响退出码处。
核 B2b 的「**## 6 F/E 分离的实现级约束**」：
- 是否写了具体约束（字段命名、group、不得进退出码）；
- 是否**只是口头声明**而没有可验证的检查点；
- `freshness_verdict` 会不会污染 E 口径。

---

## 6 硬性纪律

1. **零真机、零采样代码**、不 commit、不 push。
2. **只读**：`ra2youli/**`、`out/re_work/**`、`lead/re_line_20261105/**`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md`、`lead/b2b_design_20261106/**`（**被审对象也不许改**）一律不改。
3. `python -I -X utf8`，绝对路径；算指纹用 Python hashlib。
4. 引用追到「文件:行」或「实跑输出」，拿不到写「未验」。
5. **不许把「设计里写了」当成「设计能工作」** —— 静态正确性 ≠ 运行正确性，但静态错误必须揪出来。

---

## 7 交付物（写进 `lead/b2b_preaudit_20261106/`）

### 7.1 `B2B_PREAUDIT.md` —— 主判定书

必须含：
- 头部：**母本 / 被审 B2b / 旧 B2** 三件实算 SHA256 + 字节数（共 3 个哈希、3 个字节数）；
- 一行 `verdict: YES` 或 `verdict: NO`（独立成行）；
- **9 个 hunk 逐个判定**：标题 `#### H1`…`#### H9`，每个写 `OK / BLOCKED / UNVERIFIABLE` + 文件:行 证据 + 一句话后果；
- 「## 行号偏移与拼接」小节：验证 hunk 依序应用后是否语法正确（给出 `ast.parse` 的实际输出）；
- 「## 五个早退路径」小节：5 行表格，逐条给值/异常类型/结论；
- 「## 状态矩阵」小节：14 条逐条判定；
- 「## F/E 分离」小节；
- 「## 未验」小节（非空）。

### 7.2 `_b2b_pa_probe.py` + `_out.txt`

**你实际用的验证脚本与真实输出**。必须包含：
- 逐个 hunk 的 `-` 侧行号与母本原文比对；
- 按 hunk 依序拼接后的代码 `ast.parse` 结果；
- 五个早退路径的静态分析。

### 7.3 `review/B2B_PREAUDIT_REVIEW.md`

独立复核（见 §9）。

---

## 8 判定规则（硬性）

**只要满足任一条，`verdict` 必须是 `NO`：**
- 9 个 hunk 里有任何一个 `BLOCKED`；
- `:5939` 调用点那个 hunk（`@@ -5936,7`）没有真的覆盖 `:5939` 并加上参数；
- 五个早退路径里有任何一条会抛未绑定名字异常；
- 状态矩阵里 `unknown` 给了 `high` 置信；
- 按 hunk 依序拼接后 `ast.parse` 失败；
- 有 hunk 的新文件行号区间互相重叠或冲突。

**`verdict: YES` 的准确含义**：这份设计可以拿去**编写候选**；**不等于可以应用到母本**。

---

## 9 独立复核（必做）

另起一个**新上下文**复核员：
- 逐条打开主判定书的每个 `文件:行`，核是否真说了那句话；
- 亲自重跑 `_b2b_pa_probe.py`，核输出一致；
- **专项 A**：判定书有没有把 `BLOCKED` 悄悄写成 `OK`；
- **专项 B**：有没有把「设计 YES」写成「可应用到母本」。

复核件必须含 `subjectSha256` / `subjectBytes` / `checkedEveryRow` / `noOverreach` / `hunkVerdictCount`（形如 `9/9`）。

---

## 10 确定性门禁

写 `check_b2b_preaudit.py`，`python -I -X utf8` 跑，检查：
- 主判定书存在，含 3 个不同 64-hex + 3 个字节数；
- 含 `#### H1`…`#### H9` 九个标题；
- 含 `^verdict:\s*(YES|NO)\s*$` 一行；
- 含「行号偏移」与「五个早退路径」「状态矩阵」「F/E 分离」「未验」五个小节；
- 「未验」小节非空；
- `_b2b_pa_probe.py` 与 `_out.txt` 存在且非空；
- 复核件含 `checkedEveryRow: true`、`noOverreach: true`、`hunkVerdictCount: 9/9`；
- **一致性**：若 `verdict: YES`，则 9 个 hunk 判定里不得出现 `BLOCKED`（脚本自己扫）。

退出码 0 = PASS。**exitCode 与完整输出写进交付说明。**
