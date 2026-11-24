# TASK · B2b 候选编写（D-25 执行顺序 第 4 步）

**派发**：2026-11-06 17:3x，总控会话。**模型**：`magpie/antigravity/gemini-3.8-flash$high`。**max_concurrency=2**。
**授权依据**：**D-25 裁决书**（`lead/d25_ruling_20261106/RULING_D25.md`）第 3 节 order 第 4 步：
「设计通过后**另派候选作者**，在新指定写域生成候选及必要的隔离合成测试。**先重跑适用于绑定 W11 版本的既有测试**，再覆盖早退、异常、未知快照、字段输出与接线；报告精确命令、输出、退出码和未覆盖项。**不得导入母本触发顶层逻辑或通过测试启动游戏。** 历史 14 测不能替代这些工作。」
**上游**：B2b 设计已过独立预审 `verdict: YES`（`lead/b2b_preaudit_20261106/B2B_PREAUDIT.md`，`3f97f3a4…` / 20,615 B）。
**唯一写域**：`lead/b2b_candidate_20261106/`（新建目录，只写此目录内的新文件）。

---

## 0 一句话

设计已经过了预审，**现在把它变成能跑的代码**。

你要产出**一份完整的 `qc151_trip.py` 候选副本**（不是 diff 片段，是完整文件）+ 隔离合成测试 + 测试报告。
**母本一个字节都不许动。**

## 1 上游绑定（开工先实算，不符就停）

| 对象 | 路径 | 必须等于 |
|:--|:--|:--|
| 正式母本 | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` / **399,508 B** |
| 被实现的 B2b 设计 | `lead/b2b_design_20261106/B2B_DESIGN.md` | `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf` / **66,735 B** |
| 预审判定书 | `lead/b2b_preaudit_20261106/B2B_PREAUDIT.md` | `3f97f3a4664981961b72a91a60053fe8c867fa9d8e25442e7159c3046ccbf69f` / **20,615 B** |

**任一不符 ⇒ 立即停**，写 `STOP_UPSTREAM_DRIFT.md` 并结束。
（本机没有 `sha256sum`/`wc`，用 Python hashlib。）

## 2 交付物（全部写进 `lead/b2b_candidate_20261106/`）

### 2.1 `qc151_trip.candidate.py` —— 完整候选副本

**必须是完整文件**（7,291 行 + 增补），**不是 diff**。

生成方式：
1. 读母本全文字节；
2. 显式实现 B2b 设计里那 **9 个 hunk** 的改动；
3. 逐 hunk 核对：改完后的行内容与设计声明的 `+` 侧一致；
4. 写出完整文件。

**★ 不许用「运行时 monkey patch」绕过** —— 要的是真实改过的文件。

### 2.2 `CANDIDATE.diff` —— 文件级差异

用 `difflib.unified_diff` 生成**母本 vs 候选**的完整 diff，写出到文件。

**★ 必须能逐 hunk 对上 B2b 设计里那 9 个 hunk**（数量可在设计基础上因上下文合并而变化，但每个设计 hunk 都要能找到对应）。

### 2.3 `tests/test_candidate.py` —— 隔离合成测试

**★ 绝对禁止 `import qc151_trip`**（那会触发母本顶层逻辑）。

正确做法：**把候选里需要测的函数用 `importlib.util.spec_from_file_location` 加载为独立模块**，
或用 `ast` 提取函数源码后 `exec` 到隔离命名空间。**不许触发顶层执行**。

测试必须覆盖（D-25 第 4 步原文列的五项 + 设计状态矩阵）：

| 类别 | 必测项 |
|:--|:--|
| **早退** | 五个早退路径（`:6340/:6349/:6361/:6374/:6377`）快照为 `None` 时 `finalize_trip` 不崩、输出 `unknown/none` |
| **异常** | 快照采集抛异常时的出口（`state=error`，置信 `none`）|
| **未知快照** | `None` / `{}` / `{"exists": False}` 三态**必须可分**，且 `unknown` 绝不输出 `high` |
| **字段输出** | 7 个 `FRESHNESS` 字段 + 12 键 `info` 全部落盘，字段名逐个核对 |
| **接线** | `:5939` 调用点确实传了 `pre_freshness_snapshot`（可用 AST 静态核）|
| **状态矩阵** | `absent_confirmed` / `absent_both` / `leftover_unchanged` / `new_write` / `rewritten_same_content` / `missing_sha` / `vanished` 全覆盖 |

### 2.4 `tests/_test_out.txt` —— 真实测试输出

**必须真跑**，末行打印 `PASS=<n> FAIL=<m>`。

### 2.5 `TESTS_REPORT.md` —— 测试报告

必须含：
- **精确命令**（可复制粘贴）；
- **完整输出**（或指向 `_test_out.txt` 的行号）；
- **退出码**；
- **未覆盖项**（逐条说明哪些测试没做、为什么）。

### 2.6 重跑 W11 既有测试的记录

D-25 原文：「先重跑适用于绑定 W11 版本的既有测试」。

`lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/test_except_freshness.py` 是 W11 的 14 项测试。
**你要真跑它一次**，把命令 + 输出 + 退出码记进报告。

**★ 注意**：它测的是 W11 的 `except_freshness.py`，**不是你的候选**。重跑它的意义是「确认上游测试环境仍然可用」，
**不能替代**对你候选的测试。报告里要明确区分这两件事。

## 3 九处改动必须逐条落实

按设计实现，逐条自核：

| # | 设计 hunk | 内容 |
|:--|:--|:--|
| H1 | `@@ -212,6` | 模块顶层注入 F 命名空间常量 |
| H2 | `@@ -4458,6` | `backup_carrier` 记 `RESTORE.backup_mtime_pre`，保持 `bak[name]` 三键 |
| H3 | `@@ -4558,8` | 前置定义快照构造 + 新鲜性判定函数；扩展签名 `pre_snapshot=None` |
| H4 | `@@ -4572,20` | `copy_post_except_evidence` 三出口全量落盘 7 个 FRESHNESS + 12 键 info |
| H5 | `@@ -5906,7` | `finalize_trip` 末尾追加 `pre_freshness_snapshot: dict \| None = None` |
| **H6** | `@@ -5936,7` | **`:5939` 调用点显式传参** ← 上一版 B2 的死因，重点核 |
| H7 | `@@ -6294,6` | `main` 内 `try` 之前预初始化 `_pre_freshness_snapshot = None` |
| H8 | `@@ -6386,6` | 备份后（`:6388`）、进程启动前构造快照 |
| H9 | `@@ -7122,7` | `finally` 里把快照传入 `finalize_trip` |

## 4 硬性纪律

1. **零真机**：不启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，不读活进程内存。
2. **零采样代码**：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入。
3. **母本只读**：`qc151_trip.py` **一个字节都不许改**。你只写候选副本。
4. **只读**：`ra2youli/**`、`out/re_work/**`、`lead/re_line_20261105/**`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md`、
   `lead/b2b_design_20261106/**`、`lead/b2b_preaudit_20261106/**`、`lead/d2*_ruling_*/**` 一律不改。
5. **★ 测试不得启动游戏、不得 import 母本**（触发顶层逻辑即违规）。
6. 不 commit、不 push。`python -I -X utf8`，绝对路径。
7. 引用追到「文件:行」或「实跑输出」；拿不到写「未验」。
8. **★ 不许为了让测试通过而改测试** —— 测试失败就如实报，不许放宽断言。

## 5 独立复核（必做）

新上下文复核员，逐项做：

- **专项 A（母本未被改）**：实算母本 SHA256 + 字节数，必须仍是 `517889c6…5ba636` / 399,508 B；
- **专项 B（九处改动都在）**：逐个 hunk 在候选全文里定位，核 `+` 侧内容与设计一致；
- **专项 C（无 import 母本）**：扫 `tests/` 下所有 .py，**不得出现 `import qc151_trip`** 或 `from qc151_trip import`；
- **专项 D（三态可分）**：核测试里 `unknown` / `{}` / `{"exists": False}` 三种输入**输出不同**，且 `unknown` 的置信不是 `high`；
- **专项 E（测试真跑）**：亲自重跑测试，核 `_test_out.txt` 是真实输出、`FAIL=0`；
- **专项 F（未覆盖诚实）**：报告里的「未覆盖项」是否真的如实，有没有把没测的说成测了。

复核件必须含：`subjectSha256` / `subjectBytes` / `checkedEveryRow` / `motherUnchanged` / `nineHunksPresent` / `noImportMother` / `threeStatesDistinct` / `testsActuallyRun`。

## 6 确定性门禁

写 `check_candidate.py`，`python -I -X utf8` 跑，检查：

1. `qc151_trip.candidate.py` 存在，字节数 **> 399,508**（只增不减）；
2. 候选文件 `ast.parse` 成功；
3. `CANDIDATE.diff` 存在且非空；
4. **母本 SHA256 仍为 `517889c6…5ba636`、字节仍为 399,508**（脚本自己算，不符直接 FAIL）；
5. `tests/` 下**不存在** `import qc151_trip` / `from qc151_trip import`（正则扫）；
6. `_test_out.txt` 末 5 行含 `PASS=` 与 `FAIL=0`；
7. `TESTS_REPORT.md` 含「命令」「退出码」「未覆盖」三词；
8. 候选里 **9 处改动锚点全部可定位**（按设计给的 9 个关键行内容逐条搜）；
9. 复核件含 `motherUnchanged: true`、`nineHunksPresent: true`、`noImportMother: true`、`threeStatesDistinct: true`、`testsActuallyRun: true`。

退出码 0 = PASS。**exitCode 与完整输出写进交付说明。**

---

## 7 判定说明

本候选**不等于可应用到母本**。
即使全绿，也只证明「离线合成测试范围内通过」。
按 D-25 第 5、6 步，还要经过：独立候选复审 → 隔离副本离线集成 →
（且不得签正式母本已应用、不得签真机验收）。
