# SEMANTIC_REVIEW_AUDIT · 判定书独立复核件

**复核员**：判定书复核员（独立新上下文，工作流子代理）
**日期**：2026-11-06
**唯一写域**：`lead/b2b_candidate_review_20261106/`（本复核件落在其 `review/` 子目录）
**纪律**：零真机、零采样代码；未改被审对象 / 候选 / 测试 / 门禁 / 母本 / 设计 / 预审；未 commit / push；Python 全部 `python -I -X utf8`（重跑测试/门禁加 `-B`），绝对路径；指纹用 `hashlib`（本机无 `sha256sum` / `wc`）。本次写入仅限本复核件与 `review/_audit_*` 三份重跑输出。

---

## 0 机器可读字段（AuditVerdict）

```yaml
subjectSha256: 2546919f92e50091c286d78d001c160157c4149b089ee7b35648376cffb3de98
subjectBytes: 32013
checkedEveryRow: true
noOverreach: true
blockedCount: 2
```

- `subjectSha256` / `subjectBytes`：本次对 `lead/b2b_candidate_review_20261106/CANDIDATE_SEMANTIC_REVIEW.md` 实算。
  命令：`cd D:/Project/ra2-campaign-forge && python -I -X utf8 -c "import sys, hashlib; p='D:/Project/ra2-campaign-forge/lead/b2b_candidate_review_20261106/CANDIDATE_SEMANTIC_REVIEW.md'; d=open(p,'rb').read(); print('PY', sys.version); print('PATH', p); print('SHA256', hashlib.sha256(d).hexdigest()); print('BYTES', len(d))"`
  实跑输出：`PY 3.12.10 ...` / `SHA256 2546919f92e50091c286d78d001c160157c4149b089ee7b35648376cffb3de98` / `BYTES 32013`。
- `checkedEveryRow: true`：判定书里每一个 `文件:行` 引用全部逐条打开核对（清单见 §1），无抽样。
- `noOverreach: true`：专项 B（未把门禁通过/报告字段 true 写成语义已复核）与专项 C（未把语义 PASS 写成可应用到母本）双双通过（见 §4、§5）。
- `blockedCount: 2`：B-1 / B-2 两条硬性阻断项；判定书 `:194` 明写 C-1 / C-2「同源，不另计阻断数」，本次复核认同该计数。

---

## 1 逐条 `文件:行` 核对（不许抽样，全部打开）

方法：先用 `python -I -X utf8` 正则枚举判定书全文的路径+行号与裸 `:NNN` 引用（实跑输出：`distinct files cited with line specs` = 18 个文件、`distinct bare :line specs = 71`、`total bare occurrences = 90`），再逐文件按被引行区间 `read_text(encoding="utf-8").splitlines()` 打印，逐句比对判定书转述。被引 13 个文件全部存在（实跑：13 行 `OK ... B ... lines` 输出）。

### 1.1 控制类文件（全部真说）

| 判定书引用 | 被引原文（我实读） | 核 |
|:--|:--|:--|
| `RULING_D28.md:4` / `:13` / `:52` | `:4` `q1: A`；`:13`「选择 A：立即安排独立候选复审及独立复核…这是补齐既定下一门，不是签候选通过」；`:52`「候选『全绿』限于机械门禁和报告字段」 | 真 |
| `TASK.md:22-25` | 四件绑定指纹逐字 = 判定书 §0 表；我另用 `hashlib` 实算四件：`517889c6…/399508`、`9656e432…/420292`、`565771d8…/66735`、`3f97f3a4…/20615`，与表及 `:22-25` 全一致 | 真 |
| `TASK.md:30-45`, `:44`, `:126` | 三档证据等级表；`:44` 严禁「候选全绿/已验证/可用」；`:126`「不许因为门禁过了就判 PASS」 | 真 |
| `TASK.md:53`, `:62`, `:131-140`, `:134`, `:137`, `:142` | `:53` 三态「真的输出不同」；`:62` 7 字段+12 键 info 三路径都落盘；`:134` 三种输入任意两种输出相同 ⇒ BLOCKED；`:137` 某条路径缺失 ⇒ BLOCKED；`:142`「`verdict: PASS` 的准确含义…不等于可以应用到母本」 | 真 |
| `lead/b2b_design_20261106/TASK.md:40` | N3「**必须三态可分**：`unknown` / `absent_confirmed` / `present`。**禁止未知默认等于不存在**」 | 真 |
| `_test_rerun_out.txt:3`, `:65`, `:67`, `:69` | `:3` 用例总数: 29；`:65` `Ran 29 tests in 1.485s`；`:67` `OK`；`:69` `PASS=29 FAIL=0` | 真 |
| `_gate_rerun_out.txt:6-16`, `:16` | `:6`…`:14` `PASS [1]`…`PASS [9]`；`:16` `ALL 9 GATES PASSED! EXIT=0` | 真 |

### 1.2 设计 / 矩阵（全部真说）

| 判定书引用 | 被引原文（我实读） | 核 |
|:--|:--|:--|
| `B2B_DESIGN.md:100-102`, `:106`, `:95` | `:100-102` 三行实跑输出 `pre=None`/`pre={}`/`pre={exists:False}` 全 → `verdict='unknown' conf='none'`；`:106`「`{"exists": False}`（无 `state`）**不再是「确认无件」**」；`:95`「`state` 作唯一判别口…`exists` 不得反推状态」 | 真 |
| `B2B_DESIGN.md:78-81` | `:78`「三条出口全部落盘」；`:79` 正常路径 `info` 12 键；`:80` `src_missing` `_emit_f`；`:81` `copy_failed` `_emit_f` 后 `raise` — 未要求 12 键 info 三路径全落 | 真 |
| `B2B_DESIGN.md:434-435` | diff `+` 行 `rec.add("EXCEPT", "evidence_copy", None, f"{src}:path", ...)` | 真 |
| `B2B_DESIGN.md:597-603`, `:604`, `:605`, `:605-612` | `:597-603` 7 个 `FRESHNESS.*` 字段；`:604` 第 8 个 `captured_at_iso_pre`；`:605` `EXCEPT.evidence_copy` 类型 `dict \| None`、写入点「正常路径与 `src_missing` 分支」；`:605-612` 12 键 info 契约 | 真 |
| `B2B_DESIGN.md:626-639`, `:639`, `:652` | `:626` §6 标题；`:635` ③「不得进入退出码判据」；`:636` ④ 恒 False；`:639` 口径限缩（另有 `:5944`/`:7075`/`:7130` 收尾失败点）；`:652`「`ast.parse` 静态相等 ≠ 运行时退出码实测」 | 真 |
| `B2B_DESIGN.md:205,230,244,380,498,511,524,537,556` | 9 行分别为 `@@ -212,6 +212,21 @@` … `@@ -7122,7 +7363,8 @@`，逐行是 `@@` 头 | 真 |
| `B2B_DESIGN.md:656-673` | §7 H01–H09 清单 9 行，`:658`「无第 10 个 hunk、无 H10」 | 真 |
| `STATE_MATRIX.json:2`, `:2-15` | 全量 16 行 dump：`:2` 条件「跑后任意文件状态」、verdict `unknown`；14 行 `usableAsCrashEvidence` 全为 `false`（我实算值集合 `{False}`） | 真 |

### 1.3 候选 `qc151_trip.candidate.py`（全部真说）

我 dump 的区间：`217-228`、`4526-4553`、`4580-4593`、`4616-4698`、`4701-4815`、`6127-6137`、`6167-6168`、`6173`、`6214-6219`、`6264`、`6526-6528`、`6621-6629`、`7316`、`7358-7367`、`7372`、`7470`。判定书全部裸 `:NNN` 引用均落在这些区间内。

- `:228` `FRESHNESS_SNAPSHOT_STATES = ("unknown","absent_confirmed","present","error")` — 真（§1 开头）。
- `classify_except_freshness` 唯一定义在 `:4616-4698`（我 AST 实跑：`classify_except_freshness defs = [('classify_except_freshness', 4616, 4698)]`，参数 `['pre_freshness_snapshot', 'post_observed']`）— 真。
- `:4624-4626` 初值 `confidence="none"` / `usable_as_crash_evidence=False`；`:4628-4632` `_finish` 无条件硬编码 `False` — 真。
- `:4634-4638` `pre` 非 dict / `state` 不在四态域一律归一 `"unknown"`，`exists` 不参与判状态 — 真。
- `:4643-4646` `post.read_error` 优先分支；`:4648-4651` 唯一 unknown 出口 `:4649` 实参 `none`；`:4652-4654` error；`:4656-4669` 存在性；`:4667` `new_first_appearance/high`；`:4672-4698` sha/mtime 四分支 — 真。
- 13 个 `_finish` 调用点我 AST 实跑列举 = `[4644,4649,4653,4659,4662,4667,4674,4679,4682,4687,4691,4694,4697]` count 13，与判定书 `:42` 清单逐字一致；`high` 仅 `:4667/:4682/:4691` 三处、unknown 仅 `:4649` — 真。
- `:4701-4704` 签名第 4 参带默认 `None`；`:4724-4753` `_emit_f` 7 个 `rec.add`（`:4730/4733/4736/4740/4743/4747/4751`）；`:4751` `captured_at_iso` — 真。
- `:4755-4764` `src_missing` 早退（`:4759` `evidence_copy=None`）；`:4773-4790` 异常（3 条 `ERROR` `:4777/:4780/:4784` + `_emit_f :4788` + `raise :4790`，不写 `evidence_copy`）；`:4792-4815` 正常路径 12 键 `info`；`:4810-4812` `pre_freshness_snapshot` 原样回显 — 真。
- `:6167-6168` 唯一调用点带 `pre_freshness_snapshot=...`；`:6127-6137` `finalize_trip` 14 参末位带默认；`:7358-7367` 唯一调用点关键字传参；`:6528` 预初始化；`:6625-6629` `captured_at_iso_pre` 落盘；`:6264`/`:7470` 两处 `rec.dump`；`:6173`/`:7316`/`:7372` 三个 `note_cleanup_failure` 调用点 — 真（我逐行实读 + AST 实跑：`copy_post_except_evidence: calls=1 → (6167, ['rec','carrier_dir','out_dir'], [('pre_freshness_snapshot','pre_freshness_snapshot')])`；`finalize_trip: calls=1 → (7358, …, [('pre_freshness_snapshot','_pre_freshness_snapshot')])`）。
- `:6214-6219` 集合差判据块：我实跑母本 `:5985-5990` vs 候选 `:6214-6219` 逐行比对 `equal = True`，与判定书 `:139`「逐字相等 = True」一致 — 真。
- 5 个退出码函数体零 `freshness`：我 AST 实跑 `note_cleanup_failure :403-408` / `merge_cleanup_code :411-425` / `except_set_diff :687-723` / `run_guarded_steps :4526-4553` / `_main_wrapper :7381-7444` 的 `freshness-lines` 全为 `[]` — 真。
- 母本 `freshness` 全文计数 0、`:672-708` 仅 E 集合差：我实跑 `mother 'freshness' total count = 0`、`mother :672-708 freshness count = 0` — 真。
- 键名计数：我实跑 `camelCase usableAsCrashEvidence count = 0`、`snake_case usable_as_crash_evidence count = 6`、`matrix camelCase count = 14` — 与判定书 `:80` 一致（真）。

### 1.4 测试 / 门禁 / 档2 报告

| 判定书引用 | 被引原文（我实读） | 核 |
|:--|:--|:--|
| `tests/test_candidate.py:326-344` | C3 `test_c3_missing_without_state_differs_from_absent_confirmed`，`:343-344` 两条 `assertNotEqual(verdict / confidence)` | 真 |
| `check_candidate.py:68-69` | `TEST_OUT_REL = "lead/b2b_candidate_20261106/tests/_test_out.txt"`；`REPORT_REL` — 门禁 `[6]` 读旧 `_test_out.txt`，非新 `_test_rerun_out.txt` | 真 |
| `check_candidate.py:128-259` | 检查 1–9 主体（存在性/字节数/ast.parse/母本 sha/正则扫 import/末 5 行 `PASS=`/报告三词/报告 5 键值/锚点字符串），`:274` `ALL 9 GATES PASSED! EXIT=0` | 真 |
| `CANDIDATE_REVIEW.md:21-27`, `:25` | `checkedEveryRow: true` … `threeStatesDistinct: true` … `issues: []` | 真 |
| `CANDIDATE_REVIEW.md:126-150` | 专项 D 论证用 `:4810-4812` 的 `pre_freshness_snapshot` **原样回显**（`:136-139` `None` / `{}` / `{"exists": False}` 互不相等），`:150` 判 `threeStatesDistinct: true` — 确非 F 判据输出 | 真 |

### 1.5 我发现的引用精度瑕疵（不推翻结论，如实登记为 issues）

1. **`:26` 的 `check_candidate.py:101-116` 括注行号不准**：判定书写「验的是格式 / 存在性 / 锚点字符串 / 报告 5 个键值是否出现（`:101-116`）」。我实读 `:101-116` 是 `main()` 开头 + 前置 `missing_files` 循环（`check_candidate.py:101-116`），并不含报告键值；报告 5 个 `req_keys` 在 `:232-238`，检查 `[8]` 在 `:228-243`。总述 `:128-259` 正确，但该括注把说明挂到了错的区间。属行号引用瑕疵，非语义造假。
2. **`:140` 「含 `freshness` 字面量的 38 行我实列」清单有 2 行误差**：判定书列 `:4798-4807,4810-4812` 两段区间；我实跑全文含字面量正好 38 行，但 `:4801` / `:4802`（`captured_at_iso` / `pre_snapshot_state`）不含 `freshness` 字面量。判定书按区间展开共 40 行、实含 38 行，即区间表示把 2 行不符者纳入，且「我实列」的清单数与「38 行」自述不一致。不影响结论：38 行本身正确、且这 2 行同样不落在 `:6214-6219` 内，「无一落入退出码判据区间」仍成立（我 AST 复核为真）。

---

## 2 亲自重跑 `_review_probe.py`（隔离模式 + UTF-8）

命令（实跑）：
```
cd D:/Project/ra2-campaign-forge && mkdir -p "lead/b2b_candidate_review_20261106/review" && python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/b2b_candidate_review_20261106/_review_probe.py" > "D:/Project/ra2-campaign-forge/lead/b2b_candidate_review_20261106/review/_audit_probe_rerun_out.txt" 2>&1; echo "PROBE_EXIT_CODE=$?"
```
实跑输出：`PROBE_EXIT_CODE=0`。

比对命令（实跑）：
```
cd D:/Project/ra2-campaign-forge && python -I -X utf8 - <<'PY'   # hashlib 比对 _review_probe_out.txt 与 review/_audit_probe_rerun_out.txt
```
实跑输出：
```
stored bytes = 35151 rerun bytes = 35151
stored CRLF = 502 rerun CRLF = 502
byte-identical = True
sha256 stored = 5fe4f9032f598e8b1d2b90cef3e6c2b620b437276b13139ae1bf33de797a4dec
sha256 rerun  = 5fe4f9032f598e8b1d2b90cef3e6c2b620b437276b13139ae1bf33de797a4dec
LF-normalized text identical = True
stored lines = 502 rerun lines = 502
```
**结论：存档 `_review_probe_out.txt` 与本人重跑输出逐字节一致**（含 502 处 CRLF、末尾 `END`）。探针 5 项输出（四件指纹 MATCH、12 块/9 hunk 归因、重建 `RECON_EQ=True`、调用点=1 已传参、退出码判据 0 命中）与判定书 §2 / §5 结论一致。

---

## 3 两份 rerun 输出是否为真实运行输出（含时间戳 / 命令痕迹）

先实读两个脚本确认零副作用：`check_candidate.py` 全文无写文件调用（实跑扫描输出仅注释行）；`tests/test_candidate.py` 写入仅落在 `tempfile.mkdtemp` 临时目录并 `shutil.rmtree`（`:66-75`、`:163` 等），不写项目文件、不启进程。

### 3.1 `_test_rerun_out.txt`

- 真实运行痕迹：`:1` `[2026-11-06T19:32:39.084188] 开始执行候选合成隔离测试套件...` — 与 `tests/test_candidate.py:645` `print(f"[{datetime.now().isoformat()}] 开始执行…")` 格式逐字对应；`:2` `候选路径: D:\...` 对应 `:646`；`:3` `用例总数: 29` 对应 `:647`；`:65` `Ran 29 tests in 1.485s` / `:67` `OK` 是 `unittest.TextTestRunner` 原生输出；`:69` `PASS=29 FAIL=0` / `:70` `EXIT=0` 对应 `:657-658`。29 条 `... ok` 逐条在册，零 FAIL/ERROR。
- 命令痕迹：判定书 `:24` / `:259` 记 `"$PY" -I -B -X utf8 ".../tests/test_candidate.py" > ".../_test_rerun_out.txt" 2>&1` → `TEST_PROCESS_EXIT_CODE=0`。我按同一命令亲自重跑（输出到 `review/_audit_test_rerun_out.txt`）：实跑 `AUDIT_TEST_EXIT_CODE=0`，首行 `[2026-11-06T19:54:11.456359]`、`Ran 29 tests in 0.879s`、`PASS=29 FAIL=0` / `EXIT=0`。
- 一致性：把两份输出的时间戳行与耗时行归一后比对，实跑输出 `normalized-identical = True`（`stored bytes 7703 / audit rerun bytes 7703`）。**是真实运行输出。**

### 3.2 `_gate_rerun_out.txt`

- 真实运行痕迹：`:4` `[BASE] D:\...\b2b_candidate_20261106` / `:5` `[ROOT] D:\Project\ra2-campaign-forge` 对应 `check_candidate.py:105-106`；`:6-14` 9 条 `PASS [n]` 对应 `:262-263` 的 `print(f"PASS {p}")`；`:16` `ALL 9 GATES PASSED! EXIT=0` 对应 `:274`。脚本本身不打印时间戳（源码无 `datetime`），故输出内无时间戳属脚本行为，非伪造。
- 命令痕迹：判定书 `:25` / `:260` 记 `"$PY" -I -B -X utf8 ".../check_candidate.py" > ".../_gate_rerun_out.txt" 2>&1` → `GATE_PROCESS_EXIT_CODE=0`。我按同一命令亲自重跑（输出到 `review/_audit_gate_rerun_out.txt`）：实跑 `AUDIT_GATE_EXIT_CODE=0`，输出逐行一致。
- 一致性：归一后 `normalized-identical = True`（`stored bytes 1143 / audit rerun bytes 1143`），实为字节级一致（仅换行风格同为 CRLF）。**是真实运行输出。**

### 3.3 附带核实

判定书 `:204` 称门禁 `[6]` 读的旧 `tests/_test_out.txt` 与新 `_test_rerun_out.txt`「仅时间戳 / 耗时不同」：我实跑比对 `old _test_out.txt bytes = 7633 new _test_rerun_out.txt bytes = 7633`、`after normalizing timestamp/duration: identical = True`，raw diff 仅 `:1` 时间戳与 `:65` 耗时两处 — 真。

---

## 4 专项 A：九个判定里有没有把 BLOCKED 写成 PASS / UNVERIFIABLE 写成 PASS

九个判定 = `TASK.md:131-140` 九条硬规则，判定书拆为「已排除的硬性条件」7 行（`:208-216` 表）+ B-1 / B-2 两条触发（`:178` / `:187`），合计 9 条，对应整体 `verdict: BLOCKED`。

- `verdict:` 独立成行仅 1 处：`:30` `verdict: BLOCKED`（我实跑 `re.match(r'^\s*verdict\s*:', l)` 全文命中 = 1 行）。`:231`/`:247`/`:249` 的 `verdict: PASS` 均出现在「`verdict: PASS` 的准确含义」「整体 verdict 见文首单独一行 `verdict: BLOCKED`」等**解释/否定**语境，不是结论。
- `UNVERIFIABLE` 全文 0 次（我实跑扫描）；「未验」7 处均为如实披露（`:220-232` 有非空「## 未验」小节，`TASK.md:100` 要求满足）。无「把 UNVERIFIABLE 写成 PASS」。
- B-1（`:178-185`）与 B-2（`:187-192`）明写「按硬性规则 `verdict` 必须 BLOCKED」「按任务书字面须 BLOCKED」，并各自给「关闭所需证据」；`:182`「候选**不得**进入 D-25 第 6 步隔离副本集成」。
- 我独立复现了两条触发的底层事实（不靠判定书自述）：
  - 三态 F 判据 6 字段：我 exec `classify_except_freshness`，`None`/`{}`/`{"exists":False}` 在 `post_present` 与 `post_absent` 两种 post 下三对全部 `IDENTICAL`（实跑 `-> all pairs IDENTICAL = True` 两行），note 亦逐字相同 — B-1 成立。
  - 三路径离线合成（AST 抽 `const`+`classify`+`copy_post_except_evidence` 重建签名 → 内存 `FakePath`/`Recorder` stub，零落盘）：实跑输出 `[正常 copied] raise=None FRESHNESS字段=7 evidence_copy次数=1 12键info=True value=dict(12 keys)` / `[早退 src_missing] raise=None FRESHNESS字段=7 evidence_copy次数=1 12键info=False value=None` / `[异常 copy_failed] raise='OSError: synthetic read failure' FRESHNESS字段=7 evidence_copy次数=0 12键info=False value=<<MISSING>>` — 与判定书 `:112-121` 逐字一致，B-2 成立。
  - 另复现：14 行矩阵 `MATRIX_14_ALL_MATCH = True (rows = 14)`、40 组穷举 `high/crash_ev 泄漏 = 0 / 非 unknown verdict = 10`（与 `:49`/`:84` 一致）、`difflib` `变更块=12, + 行=255, - 行=13, hunk=9, 未归因 + 行=0`（与 `:154-164` 一致）、母本 `5985-5990` vs 候选 `6214-6219` `equal=True`。
- **观察项（不判违规）**：`:97` / `:145` / `:170` 三处写「**结论：本档 3 语义复核通过**（接线闭合 / F/E 静态隔离成立 / 范围无夹带）」。这是 §2 / §4 / §5 三节的**分节结论**，对应九条硬规则中确实「未触发」的三项；且 `:97` 紧跟「这**不**代表候选整体通过」、`:249` 明确「§2 / §4 / §5 的『本档语义复核通过』**仅限该节范围**，不构成候选整体 PASS——整体 verdict 见文首单独一行 `verdict: BLOCKED`」。范围已限缩，整体 verdict 未改，不构成把 BLOCKED 写成 PASS。
- **结论：专项 A 通过 —— 无把 BLOCKED 写成 PASS，无把 UNVERIFIABLE 写成 PASS。blockedCount = 2。**

---

## 5 专项 B：有没有把「门禁通过」或「报告字段为 true」写成「语义已复核」

全文逐行扫描「门禁 / 报告字段 / 档 1 / 档 2 / 9/9 / true」相关句（实跑输出 25 行），决定性证据：

- `:22`「**我本次亲自重跑的档1 事实**（严格只当「门禁通过 / 测试本人重跑通过」用，**不作为 verdict 依据**）」。
- `:26`「按铁律 7 / `TASK.md:126`，**门禁 9/9 不推出语义通过**」，并点破 `[6]` 读的是旧 `_test_out.txt`。
- `:76`「按证据等级纪律，我只能写「**报告字段声明为 true**」，**不能把它当成我核过的语义事实**」。
- `:182` / `:244`：「只证明 `info` 中 `pre_freshness_snapshot` 原样回显两两不等，**不**推翻判据层全同这一事实」「**没有**把 `threeStatesDistinct: true` 当成语义事实」。
- `:230`「**不写「报告字段已核实」**」；`:244`「★ 我**没有**把「`testsActuallyRun=true`」当成「测试真跑过」——测试是我自己重跑的」。
- `:239`「三档，**互不推导**」；`:243` 档 1 栏「只能说「**门禁通过**」…**不是**语义判据」；`:244` 档 2 栏「只能说「**报告字段声明为 true**」」；`:245` 档 3 栏「只有这些能说「**语义已独立复核**」」。
- `:247`「其 `verdict: BLOCKED` 是**档 3 结论**…**不是**由档 1（门禁 9/9）或档 2（报告字段全 true）推导而来——恰恰相反：档 1 / 档 2 都显示「绿」，而档 3 判 BLOCKED，正说明**机械通过 ≠ 语义通过**」。
- 机械通过本身我亦独立复核：门禁 9/9 与测试 `PASS=29 FAIL=0` 我均亲自重跑（§3，退出码各 0），判定书把它记为「本人重跑」而非「报告字段为真」，符合 `TASK.md:45`。

**结论：专项 B 通过 —— 无把机械门禁通过或报告字段 true 说成语义已复核；三档严格分列，且 verdict 明确不由档 1 / 档 2 推出。**

---

## 6 专项 C：有没有「可应用到母本」「可直接施用」这类越权表述

全文关键词实跑扫描（`可应用到母本` / `可应用` / `可直接施用` / `可直接应用` / `施用` / `应用到母本` / `进入第 6 步` / `可以应用` / `合并到母本` / `签候选通过` / `候选可用` / `候选已验证` / `候选全绿`）：

- `可应用到母本` 命中 2 处，**均为否定 / 禁止语境**：
  - `:231`「**未做** D-25 第 6 步隔离副本集成，也**未核**「可应用到母本」。本判定书 verdict 为 BLOCKED，本身即**不构成**进入第 6 步的许可；`verdict: PASS` 的准确含义也仅止于「语义上实现了批准设计」，**不等于可应用到母本**（`TASK.md:142`）」。
  - `:249`「本判定书**不写**「候选全绿」「候选已验证」「候选可用」；**不写**「可应用到母本」；**不写**「报告字段已核实」…」。
- `可直接施用` / `可直接应用` / `施用` / `可以应用` / `合并到母本` 命中 **0**。
- 反向禁止：`:182`「候选**不得**进入 D-25 第 6 步隔离副本集成」；`:5` 引 `RULING_D28.md:13`「不是签候选通过」。
- 判定书整体 verdict 是 `BLOCKED`，本就不存在「语义 PASS」可供放大；且 `:231` 主动援引 `TASK.md:142` 划清界限。

**结论：专项 C 通过 —— 无越权表述；`noOverreach = true`。**

---

## 7 其它问题（issues，均不推翻本次复核结论）

1. `CANDIDATE_SEMANTIC_REVIEW.md:26` 把「报告 5 个键值是否出现」括注为 `check_candidate.py:101-116`；实读该区间为 `main()` 前置检查，正确区间应为 `:228-243`（`req_keys` 在 `:232-238`）。总述 `:128-259` 无误，属括注行号不准。
2. `CANDIDATE_SEMANTIC_REVIEW.md:140` 自述「含 `freshness` 字面量的 38 行我实列」，所列 `:4798-4807,4810-4812` 按区间展开为 40 行，其中 `:4801` / `:4802` 不含该字面量；「38 行」的计数正确，但清单区间含 2 行误差。不影响「无一落入 `:6214-6219`」结论（我 AST 复核为真）。
3. `CANDIDATE_SEMANTIC_REVIEW.md:43` 的 84 组 `sys.settrace` 13/13 行覆盖与三次探针修正陈述：我**未独立复现该具体 trace**（未运行 `settrace`），按纪律不写「已复现」；但我用 AST 列全 13 个 `_finish` 调用点 + 14 行矩阵 exec 全 match 独立佐证其结论。
4. `CANDIDATE_SEMANTIC_REVIEW.md:229` 自述「**未重跑** `_review_probe.py`」：这是判定员对其自身证据来源的如实披露（判定书结论来自其内联脚本，不引用探针输出），非缺陷；本次复核按 ask 第 2 项已亲自重跑该探针并确认与存档逐字节一致（§2）。
5. `_gate_rerun_out.txt` 文件内不含时间戳（`check_candidate.py` 不打印时间）；其真实性依据是「输出逐行对应脚本 `:105-106`/`:262-263`/`:274` 打印语句」+「本人按同一命令复跑，字节级一致（1143 B）」，已确认。
6. `:97` / `:145` / `:170` 三处「本档 3 语义复核通过」为分节措辞；虽已由 `:97` 与 `:249` 明确限缩为「仅限该节范围、不构成候选整体 PASS」，仍登记为易被断章取义的措辞（不构成专项 A 违规）。

---

## 8 未验 / 边界（如实登记，不填推测）

1. **未独立复现**判定书自称的 `sys.settrace` 84 组行覆盖轨迹与三次探针修正过程（见 §7 第 3 条）；已用等价的 AST + 14 矩阵 exec 佐证结论。
2. **未做真机 / 运行时整趟验证**（铁律 1、2）：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存，未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入；`qc151_fields.json` 落盘链只静态核到 `:6264` / `:7470`。
3. **未做运行时退出码实测**；F/E 分离结论仅静态 AST + 原始字节比对（判定书 `:225` 亦自认）。
4. **未裁决** C-1 / C-2 两处口径冲突（`复审 TASK.md:53,134/62,137` 字面 vs 批准设计口径）：需总控书面裁决，本复核员无该授权，也不改判 PASS。
5. **未核** 档2 `CANDIDATE_REVIEW.md` 五（六）字段内容是否属实；只读到「声明为 true」的事实（与判定书 `:230` 一致）。
6. **未重跑** `check_semantic_review.py` 确定性门禁（本 ask 未要求）；本复核件按 `TASK.md:153-164` 给出 `checkedEveryRow: true` / `noOverreach: true` 等字段，未自行声称门禁通过。

---

## 9 总结

| 复核项 | 结果 | 依据 |
|:--|:--|:--|
| 每个 `文件:行` 逐条打开核对 | 通过（`checkedEveryRow: true`） | §1，13 个文件、71 个行号规格、90 处引用全部打开；2 处引用精度瑕疵登记于 §7 |
| 亲自重跑 `_review_probe.py` | 通过 | §2，退出码 0，与存档 `byte-identical = True`（sha `5fe4f903…`） |
| 两份 rerun 输出真实性 | 通过 | §3，时间戳 / 打印语句痕迹 + 本人复跑归一后 identical |
| 专项 A（BLOCKED→PASS / UNVERIFIABLE→PASS） | 通过 | §4，唯一 `verdict:` 行 = `BLOCKED`；`UNVERIFIABLE` 0 次；两触发项我独立复现 |
| 专项 B（机械通过→语义已复核） | 通过 | §5，三档互不推导，`:22/:26/:76/:243-247` 明确否认 |
| 专项 C（语义 PASS→可应用到母本） | 通过 | §6，2 处命中全为否定/禁止语境，`noOverreach: true` |
| 阻断项条数 | 2（B-1 / B-2） | `:178`/`:187`；C-1/C-2 按 `:194` 不另计 |

**本复核件不修改任何候选、测试、门禁或判定书；不签候选通过，不裁决口径冲突，不声称可应用到母本。**
