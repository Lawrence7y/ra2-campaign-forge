# CANDIDATE_SEMANTIC_REVIEW · B2b 候选语义复审判定书

**作者**：语义复审判定员（本判定书唯一作者，独立会话）
**日期**：2026-11-06
**授权依据**：D-28 裁决书 `lead/d28_ruling_20261106/RULING_D28.md:4`（`q1: A`）、`:13`（「这是补齐既定下一门，不是签候选通过」）；D-25 第 5 步；本复审任务书 `lead/b2b_candidate_review_20261106/TASK.md`（下称 `TASK.md`）。
**唯一写域**：`lead/b2b_candidate_review_20261106/`（本判定书）。**未改候选、测试、门禁、母本或任何只读域；未 commit / push；零真机、零采样代码。**
**Python 全部走** `python -I -X utf8`（部分加 `-B`），绝对路径；指纹用 `hashlib`（本机无 `sha256sum` / `wc`）。

---

## 0 头部：四件实算指纹（我本次亲跑 `hashlib`，非抄派发材料）

命令：`cd D:/Project/ra2-campaign-forge && python -I -X utf8 - <<'PY'` → `open(p,'rb').read()` → `hashlib.sha256(d).hexdigest(), len(d)`。四件全部实算，**与 `TASK.md:22-25` 绑定值一致，上游无漂移，无需 `STOP_UPSTREAM_DRIFT.md`**。

| 对象 | 路径 | sha256（64 hex） | 字节数 |
|:--|:--|:--|--:|
| 正式母本 | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399508 B |
| 被审候选 | `lead/b2b_candidate_20261106/qc151_trip.candidate.py` | `9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc` | 420292 B |
| 批准设计 | `lead/b2b_design_20261106/B2B_DESIGN.md` | `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf` | 66735 B |
| 设计预审 | `lead/b2b_preaudit_20261106/B2B_PREAUDIT.md` | `3f97f3a4664981961b72a91a60053fe8c867fa9d8e25442e7159c3046ccbf69f` | 20615 B |

**我本次亲自重跑的档1 事实**（严格只当「门禁通过 / 测试本人重跑通过」用，不作为 verdict 依据）：

- 测试：`"$PY" -I -B -X utf8 ".../tests/test_candidate.py" > ".../_test_rerun_out.txt" 2>&1` → `TEST_PROCESS_EXIT_CODE=0`；`_test_rerun_out.txt:3` `用例总数: 29`、`:65` `Ran 29 tests in 1.485s`、`:67` `OK`、`:69` `PASS=29 FAIL=0`（`EXIT=0`）。29 条逐条 `ok`，无 FAIL / ERROR。
- 门禁：`"$PY" -I -B -X utf8 ".../check_candidate.py" > ".../_gate_rerun_out.txt" 2>&1` → `GATE_PROCESS_EXIT_CODE=0`；`_gate_rerun_out.txt:6-16` `PASS [1]`…`PASS [9]`、`:16` `ALL 9 GATES PASSED! EXIT=0`。
- 门禁性质（`check_candidate.py:128-259`，我实读）：验的是格式 / 存在性 / 锚点字符串 / 报告 5 个键值是否出现（`:101-116`）。**`[6]` 读的是旧的 `tests/_test_out.txt`（`check_candidate.py:68-69`），不是我这次的 `_test_rerun_out.txt`**；新输出落在我写域内。按铁律 7 / `TASK.md:126`，**门禁 9/9 不推出语义通过**。

---

verdict: BLOCKED

**判定依据（一句话）**：我未照抄编排方「预判存在硬性 BLOCKED 条件」那句话，而是自己逐条实跑；`TASK.md:134` 的「`None` / `{}` / `{"exists":False}` 三种输入有任意两种输出相同」在**判据层**被我实跑证实成立（三对全 IDENTICAL，两种 post 各一遍），且 `TASK.md:137` 的「12 键 info 在某条路径缺失」在两条路径上被我离线合成证实成立。按本 ask 与 `TASK.md:131-140` 的硬性规则，**任一成立 ⇒ 必须 BLOCKED**。同时我必须如实上报：这两条恰好与**批准设计明文要求**冲突（见下文「阻断项」小节 C-1 / C-2 的口径冲突登记），我不替总控择一隐瞒、也不擅自改用设计口径把它写成 PASS。

---

## 1 状态矩阵对照

被审对象定位（我本次 AST 实跑）：`classify_except_freshness` 全文件**唯一定义**在 `lead/b2b_candidate_20261106/qc151_trip.candidate.py:4616-4698`，参数 `['pre_freshness_snapshot', 'post_observed']`；`FRESHNESS_SNAPSHOT_STATES = ('unknown','absent_confirmed','present','error')` 在 `:228`。方法：AST 抽 `const + def` → `ast.Module` → `compile/exec` 进隔离命名空间 → 直接调用（非静态推测），脚本经 stdin heredoc 传入、未落盘、未改文件。

### 1.1 14 状态是否全部有对应分支 → **是，14/14 有真分支**

- AST 扫得函数内 **13** 个 `_finish` 调用点：`:4644, 4649, 4653, 4659, 4662, 4667, 4674, 4679, 4682, 4687, 4691, 4694, 4697`。
- 我用 `sys.settrace` 记录 `classify_except_freshness` 帧逐行命中，补齐 sha 相同 + mtime 四种用例后共跑 **84 组**，输出 `命中 _finish 调用点 = [4644,4649,4653,4659,4662,4667,4674,4679,4682,4687,4691,4694,4697] 共 13`、`未命中 = NONE (13/13 全覆盖)`。（诚实披露：我第一次 trace 只记 `_finish` 函数体行、误报 4 处未覆盖；第二次改用 classify 帧、又因合成用例 sha「A」≠「P」恒走 `new_write` 漏 4 条 mtime 分支；第三次补齐同 sha 用例才得到 13/13。前两次是**探针自身缺陷**，非候选问题，结论以第三次为准。）
- 14 行矩阵（`lead/b2b_design_20261106/STATE_MATRIX.json:2-15`）我逐行 exec 比对 `verdict + confidence + usable_as_crash_evidence`：`MATRIX_14_ALL_MATCH = True`，14/14 一致。1↔2 同为 `unknown` 共用 `:4649`，有真分支；其余各占一支。
- 源码锚点：`:4634-4638`（`st not in FRESHNESS_SNAPSHOT_STATES ⇒ "unknown"` 归一）、`:4643-4646`（post `read_error` 优先）、`:4648-4651`（unknown）、`:4652-4654`（error）、`:4656-4669`（存在性）、`:4672-4698`（sha / mtime 四分支）。

### 1.2 `unknown` 的置信是否真的是 `none` → **是**

AST 扫 13 个 `_finish`：`verdict='unknown'` 的调用点**仅 `:4649`** 一处，实参 `conf='none'`；初值 `:4624-4626` 亦为 `confidence="none"`。带 `high` 的仅 3 处（`:4667` / `:4682` / `:4691`），均非 unknown。另实跑 10 种未采集 / 脏值 pre × 4 种 post = **40 组**，`high / crash_ev` 真泄漏 = **0**。⇒ 硬条件「unknown 给了 high」**未触发**。

### 1.3 `None` / `{}` / `{"exists":False}` 是否输出不同 → **否，判据层三对全同（硬性触发）**

我实跑（`python -I -X utf8 - <<'PY'`，输出原文）：

```
-- post_present --
   None             -> verdict='unknown' conf='none' is_new=None crash_ev=False pre_state='unknown'
   {}               -> verdict='unknown' conf='none' is_new=None crash_ev=False pre_state='unknown'
   {"exists":False} -> verdict='unknown' conf='none' is_new=None crash_ev=False pre_state='unknown'
   None  vs {}              : IDENTICAL
   None  vs {"exists":False}: IDENTICAL
   {}    vs {"exists":False}: IDENTICAL
-- post_absent --  （三对同样全 IDENTICAL）
>>> 三对在两种 post 下全部 IDENTICAL (6 字段 F 输出) = True
```

比对的是 F 判据 6 字段 `verdict / confidence / is_new / note / usable_as_crash_evidence / pre_snapshot_state`（`note` 亦逐字相同，均为「★ 跑前快照未采集/传参丢失/采集未完成 ⇒ F 不可判；未知 ≠ 不存在…」）。根因 `:4634-4638`：`pre` 非 dict 或 `state` 不在四态域内一律归一为 `"unknown"`，`exists` 不参与判状态。

**按 `TASK.md:134`（「三种输入有任意两种输出相同」⇒ BLOCKED）与 `TASK.md:53`（「三态是否真的输出不同」），此项构成硬性阻断。**

**必须同时登记的口径冲突（我不能替总控裁决）**：

- 批准设计 `lead/b2b_design_20261106/B2B_DESIGN.md:100-102` 的实跑输出明文写着三者**都** → `verdict='unknown' conf='none'`；`:106` 又写「`{"exists": False}`（无 `state`）**不再是「确认无件」**」；`:95` 写「`state` 作唯一判别口…`exists` 不得反推状态」。
- 设计任务书 `lead/b2b_design_20261106/TASK.md:40` 的 N3 原文是「**必须三态可分**：`unknown` / `absent_confirmed` / `present`」——此处「三态」指三种**状态值**，不是三种**原始输入**。按此口径我实跑确认候选**满足**：`{"exists":False}` → `unknown/none`（`:4649`），而 `{"state":"absent_confirmed","exists":False}` + 跑后在场 → `new_first_appearance/high`（`:4667`），verdict 与 confidence 均不同（与 `tests/test_candidate.py:326-344` 的 C3 断言一致；我**未单独执行该测试套件以外的用例**，但 29 项全套本人已重跑通过，见 §0）。
- 复审 `TASK.md:53,134` 与本 ask 把同一要求表述为「三种原始输入**输出两两不同**」。两种口径不可同时为真。
- 档2 报告 `lead/b2b_candidate_20261106/review/CANDIDATE_REVIEW.md:25` 声明 `threeStatesDistinct: true`，其论证（`:126-150`）用的是 `:4810-4812` 对 `pre_freshness_snapshot` 的**原样回显**（`None` / `{}` / `{"exists":False}` 三个不同的 raw 值），**不是 F 判据输出**。即「输出」的定义本身有分歧：全 `info` 字典两两不等，F 判据 6 字段两两全等。按证据等级纪律，我只能写「**报告字段声明为 true**」，不能把它当成我核过的语义事实。

### 1.4 `usableAsCrashEvidence` 一致性 → **是，14/14 为 False**

矩阵 `STATE_MATRIX.json:2-15` 全部 14 条取值集合 = `{False}`；代码 `:4625` 初值 `False`，`:4628-4632` 的 `_finish` **每次无条件硬编码 `False`**（13 条返回路径全经过），`:4747-4750` 落盘并注「恒 False」。14 行实跑与上节 40 组穷举均为 `False`。**口径限缩**：矩阵键为 camelCase `usableAsCrashEvidence`，代码输出键为 snake_case `usable_as_crash_evidence`（我 `grep` 实算：候选全文 camelCase 出现 **0** 次、snake_case **6** 次；矩阵 camelCase **14** 次）——二者是**按语义对应**，值已核；**是否存在正式字段映射表，未验**。

### 1.5 附带偏差：矩阵 #1 条件覆盖（**非硬性阻断**，如实登记）

`STATE_MATRIX.json:2` 写「跑后**任意**文件状态 ⇒ unknown」，但 `:4643-4646` 的 `post.read_error` 分支排在 unknown 之前。我实跑 `classify(None, {'exists':True,'read_error':'boom'})` → `post_read_error / none`（不是 `unknown`）；40 组穷举里「非 unknown verdict = 10」全部由此产生，且这 10 组 `conf=none`、`crash_ev=False`，**不构成 high / 崩溃证据泄漏**。同理 `error` + read_error 亦被抢先。这是矩阵条件与实现不一致，不是「找不到分支」。

---

## 2 调用传参核对

方法：`ast.walk` 全量找 `ast.Call`（非 grep），脚本 `python -I -X utf8 - <<'PY'`。

- **`copy_post_except_evidence` 全部调用点**：真实调用点总数 = **1**，在 `candidate.py:6167-6168`，实参 `['rec','carrier_dir','out_dir']` + 关键字 `pre_freshness_snapshot=pre_freshness_snapshot`。`存在未传参的调用点 = False` ⇒ 硬条件「另一个调用点没传参」**未触发**。签名 `:4701-4704` 第 4 参 `pre_freshness_snapshot: dict|None = None` 仍留默认值（若漏传会静默降级为 `unknown/none`），但当前唯一调用链已闭合；这是隐患登记，非当前缺陷。
- **母本 `:5939` ↔ 候选**：母本原文 `copy_post_except_evidence(rec, carrier_dir, out_dir)`（无 pre 参）；候选 `:6167-6168` 改为关键字传参。**确实传了参**。
- **`finalize_trip` 签名兼容**：候选 `:6127-6137` 共 14 参，新增 `pre_freshness_snapshot` 在**末位**且**带默认值 `None`**（AST 实读 `是否有默认值 = True`）。全部真实调用点 = **1**（`:7358-7367`），位置参数 5 个 + 关键字含 `pre_freshness_snapshot`（`:7367`）⇒ **不会抛 TypeError**，硬条件「调用点因新形参不兼容」**未触发**。
- 预初始化 `_pre_freshness_snapshot: dict|None = None` 在 `:6528`（早于 `:6623` 赋值、`:7367` 传出），E1 作用域链闭合；`captured_at_iso_pre` 落盘在 `:6625-6629`。

**结论：本档 3 语义复核通过（接线闭合、无漏传、无 TypeError）。** 这**不**代表候选整体通过。

---

## 3 输出字段核对

### 3.1 字段名逐个一致 → **是**

设计 `B2B_DESIGN.md:597-603` 的 7 个 `FRESHNESS` 字段 ↔ 候选 `_emit_f`（`:4724-4753`）7 个 `rec.add`：`freshness_verdict :4730` / `freshness_confidence :4733` / `freshness_is_new :4736` / `freshness_note :4740` / `pre_snapshot_state :4743` / `usable_as_crash_evidence :4747` / `captured_at_iso :4751`，全名一致；第 8 个 `FRESHNESS.captured_at_iso_pre`（设计 `:604`）由 `:6625` 落盘。12 键 `info`（设计 `:605-612`）候选 `:4792-4803` 恰为这 12 键：`source / evidence_path / size / sha256 / note / mtime_post / freshness_verdict / freshness_confidence / freshness_note / captured_at_iso / pre_snapshot_state / pre_freshness_snapshot`。

### 3.2 三条路径落盘 → **7 字段三路径全落；12 键 info 仅正常路径（硬性触发 + 口径冲突）**

我做了**离线合成实跑**（AST 抽 `classify_except_freshness` + `copy_post_except_evidence` → `exec` 隔离命名空间 → 内存 `FakePath` / `Recorder` stub，**零落盘、零真机、零采样**）。诚实披露：第一次跑因我给的 `datetime` stub 只有模块、没有 `.now()`，正常路径抛 `AttributeError`；修正 stub 后重跑得到干净结果，以下为**修正后**输出：

```
[正常 copied]      raise=None
   FRESHNESS 7字段齐全 = True (行键数=7)
   EXCEPT.evidence_copy 次数=1  value 为完整 12 键 info = True  (dict(12 keys))
[早退 src_missing]  raise=None
   FRESHNESS 7字段齐全 = True (行键数=7)
   EXCEPT.evidence_copy 次数=1  value 为完整 12 键 info = False (value=None)
[异常 copy_failed]  raise='OSError: synthetic read failure'
   FRESHNESS 7字段齐全 = True (行键数=7)
   EXCEPT.evidence_copy 次数=0  value 为完整 12 键 info = False (value='<<MISSING>>')
7 字段: 三路径全 = True | 12 键 info: 正常/早退/异常 = [True, False, False]
```

源码对应：`src_missing` 早退 `:4755-4764`（`:4759` 写 `rec.add("EXCEPT","evidence_copy", None, ...)`）；`copy_failed` 异常 `:4773-4790`（3 条 `ERROR` `:4777/4780/4784` + `_emit_f` `:4788` + `raise` `:4790`，**根本不写 `evidence_copy`**）；正常 `:4792-4815` 写 12 键 `info`。

落盘链（**AST 静态确认，非真机**）：三路径写同一 `rec`，`finalize_trip._dump` 在 `:6264` 调 `rec.dump(out_dir/"qc151_fields.json")`，`:7470` 再 dump 一次到 `WORKDIR`；`run_guarded_steps`（`:4526-4553`）每项独立 try、前项失败仍跑完再重抛，故异常路径的 F 行 / ERROR 行也会被落盘。边界：main 的 `finally` 在到达 `finalize_trip` **之前**失败时，`copy_post_except_evidence` 根本不被调用、无 F 字段落盘——属真实可达路径，我**未**做运行时复现。

- 按 `TASK.md:62,137` 字面（「7 个 FRESHNESS 字段 + 12 键 info 三条路径都落盘 / 某条路径缺失即 BLOCKED」）⇒ **硬性阻断成立**。
- 按**批准设计**候选**正确**：`B2B_DESIGN.md:605` 明示 `EXCEPT.evidence_copy` 类型 `dict | None`、写入点为「正常路径与 `src_missing` 分支」（设计 §4 #4 的 diff 在 `B2B_DESIGN.md:434-435` 明写 `rec.add("EXCEPT", "evidence_copy", None, ...)`）；`B2B_DESIGN.md:78-81`（§1 N4）只要求「三出口全部落盘」针对 **7 个 FRESHNESS 字段**，12 键 info 从不要求三路径都落。

**这是第二处口径冲突，我不替总控裁决。** 结论：7 字段三路径全落（档3 已核），12 键 info 早退为 `None`、异常缺行（档3 已核）。

---

## 4 F/E 分离核对

方法：AST 全量扫退出码 / 清理函数体 + 原始字节逐行比对（`python -I -X utf8 - <<'PY'`）。

- **母本 `:5985-5990` vs 候选 `:6214-6219`**：`逐字相等 = True`（我 `splitlines` 比对）。该块是集合差判据（`if not setdiff.get("no_new_exception", True): ... note_cleanup_failure(...)`），**未被动过**。
- **退出码判据路径是否读 `freshness_*`**：候选全文含 `freshness` 字面量的 38 行我实列（`:217,222,4580,4593,4616,4634,4635,4703,4731,4734,4737,4741,4745,4749,4762,4777,4780,4784,4788,4798-4807,4810-4812,6137,6168,6528,6623,6626,6627,6629,7367`），**无一落入 `:6214-6219`**（`F 名字是否出现在退出码判据区间 = False`）。AST 查 `note_cleanup_failure` / `merge_cleanup_code` / `except_set_diff` / `_main_wrapper` / `run_guarded_steps` 五个函数体含 `freshness` 的定义行 = **NONE**（全部）。`E 集合差判据块(母本 5984-5990) 落入变更块 = NONE`。⇒ 硬条件「`freshness_*` 被退出码判据读取」**未触发**。
- **`usable_as_crash_evidence` 恒 False**（见 §1.4），F 结论不作崩溃证据；`B2B_DESIGN.md:626-639` 的 ③ 约束在候选有具体落点（`:4628-4632` 硬编码 + `:4747-4750` 写入 group），不只是注释。

**口径限缩（遵设计 `B2B_DESIGN.md:639` 取舍 E，不扩大声称）**：母本另有 `:5944` / `:7075` / `:7130` 等 `note_cleanup_failure` 调用点（候选对应 `:6173` / `:7316` / `:7372`）也影响收尾失败码；本次只核到「E 集合差判据块逐字未改 + F 区零退出码符号」，**未**声称「全局退出码逻辑未动」，**未**做运行时退出码实测（铁律 1 零真机）。

**结论：本档 3 语义复核通过（F/E 静态隔离成立）。**

---

## 5 范围限制核对

方法：`difflib.SequenceMatcher(autojunk=False)` 全量比对母本 vs 候选（我本次实跑，非引用前序输出）。

```
母本行数 = 7291   候选行数 = 7533
变更块(opcode) 数 = 12     + 行 = 255   - 行 = 13
12 块：母本 215-214→候选 215-229(H01) / 4461-4460→4476-4479(H02) /
       4561-4560→4580-4700(H03) / 4562→4702-4704(H03) /
       4575-4582→4717-4791(H04) / 4586→4795-4812(H04) / 4589-4588→4815(H04) /
       5909→6136-6137(H05) / 5939→6167-6168(H06) / 6297-6296→6526-6528(H07) /
       6389-6388→6621-6629(H08) / 7125→7366-7367(H09)
E 集合差判据块(母本 5984-5990) 落入变更块 = NONE
设计 §4 hunk(@ @) 数 = 9   （B2B_DESIGN.md:205,230,244,380,498,511,524,537,556）
difflib 新增行中, 未在设计 §4 '+' 行出现的条数 = 0
```

- 12 个 opcode 块对应设计 §7 的 9 个 `@@` hunk（`B2B_DESIGN.md:656-673` 的 H01–H09 清单，9 行 = 9 hunk）：H03 跨 2 块（插入 + def 签名 replace）、H04 跨 3 块，其余各 1 块，合计 12。**无第 10 个 hunk、无 H10**。
- 我用 `Counter` 做多重集比对：`difflib` 的 255 条 `+` 行**全部**能在设计 §4 的 `+` 行中找到（`未在设计 §4 '+' 行出现的条数 = 0`）；`-` 行 13 条亦与设计 `-212,6 / -4458,6 / -4558,8 / -4572,20 / -5906,7 / -5936,7 / -6294,6 / -6386,6 / -7122,7` 的替换区一致。⇒ **无夹带、无法归属的块 = 0**，硬条件「diff 超出 H1–H9 范围」**未触发**。
- 母本 `grep` 无任何 F / 新鲜性判据（`freshness` 文本计数 0，`:672-708` 仅为 E 集合差）：这是**新增逻辑，不是移植**，故 14 条矩阵在母本无对应实现可对照。

**结论：本档 3 语义复核通过（范围无夹带）。**

---

## 阻断项

> 下列每条给「`文件:行` + 后果 + 关闭所需证据」。B-1 / B-2 是本 ask 与 `TASK.md:131-140` 硬性规则的**直接触发项**；两者同时与批准设计冲突，故在 C-1 / C-2 登记口径冲突，我不替总控裁决、也不擅自改用设计口径改判 PASS。

### B-1（硬性触发 · `TASK.md:134`）三态 F 判据输出两两相同

- **依据**：`lead/b2b_candidate_20261106/qc151_trip.candidate.py:4634-4638`（`pre` 非 dict / `state` 不在四态域一律归一 `"unknown"`，`exists` 不参与判状态）、`:4648-4651`（唯一 unknown 出口）；规则 `lead/b2b_candidate_review_20261106/TASK.md:53,134`。
- **实跑证据**：我本次 `python -I -X utf8 - <<'PY'` exec `classify_except_freshness`，`None` / `{}` / `{"exists":False}` 在 `post_present` 与 `post_absent` 两种 post 下，F 判据 6 字段（`verdict/confidence/is_new/note/usable_as_crash_evidence/pre_snapshot_state`）三对**全部 `IDENTICAL`**，输出 `>>> 三对在两种 post 下全部 IDENTICAL = True`。
- **后果**：按硬性规则 `verdict` 必须 BLOCKED；候选**不得**进入 D-25 第 6 步隔离副本集成。档2 的 `threeStatesDistinct: true`（`CANDIDATE_REVIEW.md:25`）只证明 `info` 中 `pre_freshness_snapshot` 原样回显两两不等（`:4810-4812`、报告 `:126-150`），**不**推翻判据层全同这一事实。
- **关闭所需证据**（二者择一，须总控书面裁决并登记 D 编号）：
  1. 采用复审 `TASK.md:134` 字面口径 ⇒ 需候选修改 `classify_except_freshness` 使三种原始输入在 **F 判据层**两两可分，重新提交绑定指纹，并由我（或同档复核员）重跑 §1 全部 14 矩阵 + 40 组穷举 + 29 项测试 + 9 项门禁；**同时必须修订批准设计** `B2B_DESIGN.md:100-102,106`（现明文要求三者相同）与 `lead/b2b_design_20261106/TASK.md:40` 的 N3 表述，否则候选改完即违反设计。
  2. 采用批准设计口径（「三态可分」= `unknown` / `absent_confirmed` / `present` 三种**状态值**）⇒ 需总控出具书面裁决，明确 `TASK.md:53,134` 的「三种原始输入输出两两不同」**不适用或已修订**，并在判定书中固定「输出」的定义为「F 判据字段」还是「`info` 全字典」；随后由复核员重新出具判定书。**我不代签。**

### B-2（硬性触发 · `TASK.md:137` 字面）12 键 info 未在三条路径都落盘

- **依据**：`candidate.py:4755-4764`（`src_missing` 写 `evidence_copy=None`）、`:4773-4790`（`copy_failed` 无 `evidence_copy` 行）、`:4792-4815`（正常路径 12 键）；规则 `TASK.md:62,137`。
- **实跑证据**：我本次离线合成三路径输出 `12 键 info: 正常/早退/异常 = [True, False, False]`；`EXCEPT.evidence_copy` 次数分别为 `1 / 1 / 0`，早退 value = `None`，异常 value = `<<MISSING>>`。7 个 FRESHNESS 字段三路径 `True / True / True`。
- **后果**：按任务书字面须 BLOCKED。但按批准设计 `B2B_DESIGN.md:605`（类型 `dict | None`、写入点「正常路径与 `src_missing` 分支」）、`B2B_DESIGN.md:434-435`（diff 明写 `rec.add(..., None, ...)`）、`B2B_DESIGN.md:78-81`（N4 的「三出口全部落盘」只针对 7 个 F 字段），**候选行为与设计完全一致，不是候选缺陷**。
- **关闭所需证据**：总控书面裁决验收口径 =「批准设计 §5:605」还是「`TASK.md:62,137` 字面」。若采用设计口径，须写明 `TASK.md:62,137` 该分句作废；若采用任务书字面，须候选在 `src_missing` / `copy_failed` 也落 12 键 `info` 并同步修订设计 §5 / §4 #4，再重跑三路径合成与全套测试。

### C-1 / C-2 口径冲突登记（与 B-1 / B-2 同源，不另计阻断数）

| 编号 | 冲突双方 | 我核到的事实 |
|:--|:--|:--|
| C-1 | `B2B_DESIGN.md:100-102,106` + `lead/b2b_design_20261106/TASK.md:40` **vs** 复审 `TASK.md:53,134` | 设计明文要求 `None`/`{}`/`{"exists":False}` **都** → `unknown/none`；候选正是如此实现（我实跑 14/14 矩阵一致）。设计口径下「`unknown` vs `absent_confirmed` vs `present` 三态可分」**成立**（`{"state":"absent_confirmed","exists":False}` → `new_first_appearance/high`，`:4667`）。复审字面口径下**不成立**。 |
| C-2 | `B2B_DESIGN.md:605,434-435,78-81` **vs** `TASK.md:62,137` | 设计定义 `EXCEPT.evidence_copy` 为 `dict | None` 且只在正常路径给 12 键；任务书字面要求三路径全落 12 键。 |

**附带登记（非硬性阻断，不扩大为 BLOCKED 理由）**：
- 矩阵 #1 条件覆盖偏差：`STATE_MATRIX.json:2` 称「跑后任意文件状态 ⇒ unknown」，但 `candidate.py:4643-4646` 的 `read_error` 优先分支使 `pre=None + post.read_error` → `post_read_error/none`（我实跑确认）。属矩阵条件与实现不一致，不是「找不到分支」，也不是 `high` / 崩溃证据泄漏。
- 键名映射：矩阵 `usableAsCrashEvidence`（camelCase，14 次）↔ 代码 `usable_as_crash_evidence`（snake_case，6 次；camelCase 全文 0 次）。值的一致性已核；**有无正式字段映射表，未验**。
- 门禁 `[6]` 读旧 `tests/_test_out.txt`（`check_candidate.py:68-69`），非我本次 `_test_rerun_out.txt`；两文件内容仅时间戳 / 耗时不同，不影响结论，但须登记。

### 已排除的硬性条件（我逐条实跑，均未触发）

| 硬条件 | 结果 | 我的证据 |
|:--|:--|:--|
| 14 状态任一找不到分支 | 未触发 | 13/13 `_finish` 全覆盖（84 组 trace），14/14 矩阵一致 |
| `unknown` 给 `high` | 未触发 | 仅 `:4649` 一处 unknown，实参 `none`；40 组穷举真泄漏 0 |
| 另一 `copy_post_except_evidence` 调用点没传参 | 未触发 | AST 全量：调用点 = 1（`:6167`），已传 |
| `finalize_trip` 调用点不兼容新形参 | 未触发 | 新参末位带默认 `None`；调用点 = 1（`:7358`）走关键字 |
| `freshness_*` 被退出码判据读取 | 未触发 | `:6214-6219` 逐字未改；5 个退出码函数体零 `freshness` |
| diff 超出 H1–H9 | 未触发 | 12 块 / 9 hunk，`未归因 + 行 = 0` |
| 本人重跑测试有 FAIL | 未触发 | `PASS=29 FAIL=0`，退出码 0（`_test_rerun_out.txt:69`） |

---

## 未验

**以下均未验 / 未跑，不填入任何推测结论**：

1. **未做真机或运行时整趟验证**（铁律 1、2）：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存，未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入。`qc151_fields.json` 的实际磁盘落盘只由 AST 静态确认到 `:6264` / `:7470` 的 `rec.dump` 调用点，**未**真跑整趟看磁盘文件。
2. **未做运行时退出码实测**：F/E 分离结论来自静态 AST + 原始字节逐行比对（`B2B_DESIGN.md:652` 亦自认「`ast.parse` 静态相等 ≠ 运行时退出码实测」）。「F 字段存在时整趟退出码仍只由集合差触发」只由静态断言保证。
3. **未验** main 的 `finally` 在到达 `finalize_trip` **之前**失败（设计 §3 P7a/P7b）时 F 字段是否落盘——真实可达路径，本次未复现。
4. **未验** 是否有 `usableAsCrashEvidence` → `usable_as_crash_evidence` 的正式字段映射表（契约层），仅按语义对应核了值。
5. **未验** `B2B_DESIGN.md` 的草稿脚本 `_draft_semantics_check.py matrix` 是否可复现（我**未**重跑它；`:100-102` 的输出我只是**读取**设计稿记载）。四件上游之外的旧 W11 / B2 材料亦未复核。
6. **未重跑** `lead/b2b_candidate_review_20261106/_review_probe.py`（前序核验员产物，写域内已存在，28734 B / 输出 35151 B）——本判定书**没有**引用它的输出作为自己的证据；我全部结论来自本次会话自己执行的内联 `python -I -X utf8 - <<'PY'` 脚本、测试 / 门禁重跑、以及实读文件行。
7. **未核** 档2 `CANDIDATE_REVIEW.md` 五字段（`checkedEveryRow` / `motherUnchanged` / `nineHunksPresent` / `noImportMother` / `threeStatesDistinct` / `testsActuallyRun`，`:21-27`）是否**内容属实**：我只读了它们「声明为 true」这一事实，并核出 `threeStatesDistinct` 的论证口径（见 B-1）。按证据等级纪律，**不写「报告字段已核实」**。
8. **未做** D-25 第 6 步隔离副本集成，也未核「可应用到母本」。本判定书 verdict 为 BLOCKED，本身即不构成进入第 6 步的许可；`verdict: PASS` 的准确含义也仅止于「语义上实现了批准设计」，**不等于可应用到母本**（`TASK.md:142`）。
9. **未裁决** C-1 / C-2 两处口径冲突——需总控书面裁决，见「关闭所需证据」。我不具备该授权。
10. 本次全部写入仅 `lead/b2b_candidate_review_20261106/` 内的本判定书，以及被我本人重跑覆盖的 `_test_rerun_out.txt` / `_gate_rerun_out.txt`；**未改候选、测试、门禁、母本、设计、预审或任何只读域**；未 commit / push。

---

## 证据等级说明

严格按 D-28 明文（`RULING_D28.md:52`：「候选『全绿』**限于机械门禁和报告字段**」；`TASK.md:30-45`）区分三档，**互不推导**：

| 档 | 含义 | 本判定书里对应的事实 | 能写成什么 |
|:--|:--|:--|:--|
| **档 1 · 机械门禁通过** | `check_candidate.py` 9/9 | 我本次重跑：`_gate_rerun_out.txt:16` `ALL 9 GATES PASSED! EXIT=0`；测试重跑 `PASS=29 FAIL=0`、退出码 0 | 只能说「**门禁通过**」「测试本人重跑通过」。门禁只验格式 / 锚点 / 字段存在性（`check_candidate.py:128-259`），**不是**语义判据 |
| **档 2 · 报告字段为 true** | `CANDIDATE_REVIEW.md` 五（六）字段 | `lead/b2b_candidate_20261106/review/CANDIDATE_REVIEW.md:21-27` 声明 `checkedEveryRow / motherUnchanged / nineHunksPresent / noImportMother / threeStatesDistinct / testsActuallyRun` 均为 `true`、`issues: []`；门禁 `[8]` 只验这些键值**出现** | 只能说「**报告字段声明为 true**」。★ 我**没有**把「`testsActuallyRun=true`」当成「测试真跑过」——测试是我自己重跑的；也**没有**把 `threeStatesDistinct: true` 当成语义事实（其论证基于 `info` 回显，见 B-1 / §1.3） |
| **档 3 · 语义已独立复核** | 我逐项亲自核过 | §1–§5 全部：14 矩阵 exec、13/13 trace 覆盖、40 组穷举、三态 F 输出比对、AST 全量调用点、三路径离线合成、母本判据块逐字比对、difflib 12 块 / 9 hunk 归因；以及测试 / 门禁本人重跑 | 只有这些能说「**语义已独立复核**」 |

**本判定书属于档 3（语义已独立复核）**，其 `verdict: BLOCKED` 是**档 3 结论**，依据是 B-1 / B-2 两条本人实跑证实的硬性触发条件，**不是**由档 1（门禁 9/9）或档 2（报告字段全 true）推导而来——恰恰相反：档 1 / 档 2 都显示「绿」，而档 3 判 BLOCKED，正说明**机械通过 ≠ 语义通过**。

**明确不写的措辞**（`TASK.md:44`、D-28 纪律）：本判定书**不写**「候选全绿」「候选已验证」「候选可用」；**不写**「可应用到母本」；**不写**「报告字段已核实」；**不写**「测试真跑过」来替代我自己的重跑记录（我确已重跑，但按事实陈述为「本人重跑通过」）。§2 / §4 / §5 的「本档语义复核通过」**仅限该节范围**，不构成候选整体 PASS——整体 verdict 见文首单独一行 `verdict: BLOCKED`。

---

## 附：本次我实际执行的命令清单（可复核）

| # | 命令（`cd D:/Project/ra2-campaign-forge`） | 用途 |
|:--|:--|:--|
| 1 | `python -I -X utf8 - <<'PY'`（hashlib 四件 + AST 抽 `const/classify` + exec 14 矩阵 + 三态比对） | §0 指纹、§1.1–1.3 |
| 2 | `python -I -X utf8 - <<'PY'`（AST 调用点 / finalize 兼容 / F/E / difflib 全量 + `Counter` 归因） | §2、§4、§5 |
| 3 | `"$PY" -I -B -X utf8 ".../tests/test_candidate.py" > ".../_test_rerun_out.txt" 2>&1` → `echo $?` | §0 测试重跑，退出码 0 |
| 4 | `"$PY" -I -B -X utf8 ".../check_candidate.py" > ".../_gate_rerun_out.txt" 2>&1` → `echo $?` | §0 门禁重跑，退出码 0 |
| 5 | `python -I -X utf8 - <<'PY'`（三路径离线合成，内存 FakePath；首跑 stub 缺陷已修正后重跑） | §3.2 |
| 6 | `python -I -X utf8 - <<'PY'`（`sys.settrace` 行覆盖 ×3 次修正 / 40 组穷举 / 矩阵 #1 偏差 / rec.dump 链） | §1.1、§1.2、§1.5 |
| 7 | `grep -n` / `sed -n` 精读 `B2B_DESIGN.md`、`STATE_MATRIX.json`、`TASK.md`、`CANDIDATE_REVIEW.md`、`test_candidate.py`、`check_candidate.py` 指定行 | 全部「文件:行」引用 |

其中 `$PY = /c/Users/Administrator/AppData/Local/Programs/Python/Python312/python`（`Python 3.12.10`）。所有内联脚本经 stdin 传入、未落盘；离线合成使用 `-B` 且 `Recorder` / `FakePath` 为内存 stub，**无任何文件写入**，仅输出重定向到写域内两个重跑输出文件。
