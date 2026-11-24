# 第二轮语义复审判定书 · B2b 候选（D-25 第 5 步 · 修正口径重审）

**日期**：2026-11-06　**作者**：第二轮判定书撰写员（独立复审，新上下文）
**方法**：全部数字取自本次会话亲自实跑（`python -I -X utf8` / 重跑加 `-B`，绝对路径，指纹用 `hashlib`）或本次实读的「文件:行」。零真机、零采样代码、不改候选/测试/门禁/母本/设计/上一轮判定书、不 commit / push。
**裁定依据**：`lead/b2b_candidate_review2_20261106/TASK.md:183-221`（裁定附录，裁定一 / 裁定二）；硬性阻断规则见本轮 ask「判定规则（按修正后口径）」。

## 头部 · 四件实算指纹（Python hashlib，实跑输出 `_r2_part1_out.txt:2-5`）

| 对象 | 路径 | SHA256（64 hex） | 字节数 | 与 TASK 期望一致 |
|:--|:--|:--|--:|:--|
| 母本 | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399508 B | True |
| 候选 | `lead/b2b_candidate_20261106/qc151_trip.candidate.py` | `9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc` | 420292 B | True |
| 设计 | `lead/b2b_design_20261106/B2B_DESIGN.md` | `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf` | 66735 B | True |
| 本轮 TASK | `lead/b2b_candidate_review2_20261106/TASK.md` | `63336d058952fc360c82f0341d85963ee88fe47adc458000724abcffe8533eca` | 13763 B | True |

交付前复算四件指纹仍全部 `match=True`（本人末次实跑 stdout），只读对象零漂移。

verdict: BLOCKED

**一句话总括**：按修正口径，上一轮 B-1 / B-2 **确实不再成立**（裁定一、裁定二由我本人实跑复现，见 §1）；上一轮已排除的七项本人逐条重验均未触发；上一轮登记的五项遗留事项本人复核后**保持原状态、不因裁定消失**（§6）。**但按同一口径出现了一个新的阻断项 N-1**：候选整篇行尾被从母本 LF 改为 CRLF，是设计 §4 九个 hunk 从未声明、且落在 H1–H9 范围之外的字节级改动（§5）。硬性规则「diff 有超出 H1–H9 的改动 ⇒ verdict 必须 BLOCKED」被触发。此结论**不美化、不由门禁 9/9 推出**。

---

## 1 上一轮 B-1/B-2 按修正口径的复判

**回答问题 ①：是，B-1 / B-2 按修正口径真的不再成立。** 但「两条旧阻断关闭」≠「整体 PASS」——§5 的新阻断项 N-1 与本轮裁定无关，是独立发现。

### B-1（原「三态不可分 / 三种原始输入同输出」）→ 关闭，成立依据充分

- 我本人用 `importlib.util` + `patch("ctypes.windll.user32.SetProcessDPIAware")`（同 `tests/test_candidate.py:40-57` 的隔离加载法）加载候选，真调 `classify_except_freshness`（`_r2_three_state_out.txt:1-2`）。同一 `post_present` 下实跑输出（`:11-16`）：
  - `unknown` → `unknown/none`，`pre_snapshot_state=unknown`；
  - `{"state":"absent_confirmed","exists":False}` → `new_first_appearance/high`，`pre_snapshot_state=absent_confirmed`；
  - `present` → `new_write/high`，`pre_snapshot_state=present`。
  - 三 verdict 两两不等 = `True`，集合 `['new_first_appearance','new_write','unknown']`；**裁定一验收点「absent_confirmed 与 unknown 输出不同」= True**（`:16`）。
- 原始输入 `None` / `{}` / `{"exists":False}` / `{"state":"zzz"}` / `{"state":"unknown"}` 五种实跑输出 6 字段全同（均 `unknown/none`、`crash_ev=False`、`pre_state=unknown`），`全同=True`（`:5-10`）。按 `TASK.md:193-199`（作废原 §7 该条、生效口径为状态值层面三态互不相同、`:199`「原始输入全同是设计意图，不是缺陷」）与 `B2B_DESIGN.md:100-103`（四行输出全 `unknown/none`）、`:106`（「`{"exists":False}`（无 state）不再是确认无件」），**归一不是缺陷、不构成阻断**。
- 代码落点实读：`qc151_trip.candidate.py:4634-4638`（`state` 唯一判别口、脏值归一 unknown）、`:4648-4651`（unknown 出口）、`:4666-4669`（absent_confirmed + post 在场 → high）。与 `B2B_DESIGN.md:95`「第一个分支就分道」一致。

### B-2（原「12 键 info 在 copy_failed 路径缺失」）→ 关闭，成立依据充分

- 我本人离线合成三路径（内存 `FakePath`/`Recorder` stub，零落盘、零真机；修正 `sha256_file` stub 后干净结果，见 `_r2_paths_out.txt:2`）：`7F 三路径 = [True, True, True]`（`:15`）；`12键 info [正常,src_missing,copy_failed] = [True, False, False]`（`:16`）；`evidence_copy 次数 = [1,1,0]`（`:17`）。`copy_failed` 分支三条 `ERROR` 行 `freshness_copy_failed / freshness_copy_stage / freshness_copy_traceback`（`:14`），随后 `raise`（`candidate.py:4790`）。
- 按 `TASK.md:201-210` 裁定二：7 个 F 字段须三路径全落盘（已满足）；「12 键 info 只在正常路径与 src_missing 分支落盘即可」、`copy_failed` 路径没有 `evidence_copy` 行**符合设计、不算阻断**（`TASK.md:149`；`B2B_DESIGN.md:605` 定义 `dict|None`，`:434-435` diff 明写 `rec.add("EXCEPT","evidence_copy",None,...)`；候选 `:4759` 即该行）。三出口调用点实读：正常 `:4815`、src_missing `:4762-4763`、copy_failed `:4788-4789`。
- **如实限缩（措辞歧义，不升级为阻断）**：`src_missing` 分支「落盘」的是 `evidence_copy=None` **那一行**（有写入动作、有键，`:4759`），value **并非** 12 键 dict；本次实跑 `src_missing 的 ec value = None`（`_r2_paths_out.txt:18`）。若把裁定二正文「12 键 info 落盘」按字面理解成「写入 12 键字典」，则 src_missing 不成立——此措辞歧义与核心口径核验员登记一致。**候选与批准设计代码逐字一致**，按裁定二不重开 B-2，仅登记。

**其余硬性规则本人逐条重验（均未触发）**：14 状态覆盖、unknown 非 high、唯一调用点已传参、finalize_trip 兼容、freshness_* 不进退出码、亲自重跑测试 `PASS=29 FAIL=0`——见 §2 / §4 / 附命令清单。`diff 未超出 H1–H9` 这一条**是唯一触发项**，见 §5。

---

## 2 状态矩阵与三态（裁定一口径）

- **14 状态全覆盖**：`STATE_MATRIX.json:2-15` 共 14 行；被测函数 `qc151_trip.candidate.py:4616-4698`。本人以 14 组 fixture 逐行 exec 比对 `verdict + confidence + usable_as_crash_evidence`：`MATRIX_14_ALL_MATCH = True（rows=14）`（`_r2_matrix_out.txt:2-16`，14 行全 `match=True`）。
- **unknown 恒 none**：AST 扫得 `_finish` 调用点 **13** 处（`_r2_matrix_out.txt:17`）；`verdict='unknown'` 调用点仅 `[(4649,'unknown','none')]`（`:18`）；`conf='high'` 三处 `:4667/:4682/:4691` 均非 unknown（`:19`）。穷举 9 种未采集/脏值 pre × 4 种 post = **36 组，`unknown+high 泄漏 = 0`**（`:21`）。`UNKNOWN_CONF_ALWAYS_NONE = True`（`:20`）。
- **三态可分（裁定一）**：见 §1，状态值层面三 verdict 两两不等；`{"state":"absent_confirmed"}` 与 `unknown` 输出不同 = True。原始输入三种归一 = 设计意图、不算阻断（裁定一）。
- **STATE_MATRIX #1 条件覆盖偏差（保留登记）**：`STATE_MATRIX.json:2` 称「跑后任意文件状态 ⇒ unknown」，但本人实跑 `classify(None, {"exists":True,"read_error":"boom"})` → `post_read_error/none`（`_r2_leftovers_out.txt:13`），因 `candidate.py:4643-4646` 的 read_error 独立出口排在 `:4648` unknown 之前。这与批准设计 `B2B_DESIGN.md:310-311`「N1 错误独立出口优先于一切状态折叠」一致，属矩阵 condition 措辞过宽，非候选缺陷；`crash_ev=False`，无 high / 崩溃证据泄漏。详见 §6 第 3 条。

---

## 3 输出字段（裁定二口径）

- **7 个 F 字段三路径全落盘**：`_emit_f`（`candidate.py:4724-4753`）固定 7 键，本人实读键位：`:4730 freshness_verdict`、`:4733 freshness_confidence`、`:4736 freshness_is_new`、`:4740 freshness_note`、`:4743 pre_snapshot_state`、`:4747 usable_as_crash_evidence`、`:4751 captured_at_iso`，与 `B2B_DESIGN.md:597-603` 逐名一致。本人离线合成 `7F 三路径 = [True,True,True]`（`_r2_paths_out.txt:15`，三路径的 `FRESHNESS 键` 列表见 `:4/:8/:12`）。
- **12 键 info 两路径**：正常路径 `ec_value=dict`、`12键info=True`（`:5`）；src_missing `ec_value=None`（有行、非 12 键 dict，`:9`）；copy_failed 无 `evidence_copy` 行、三条 `ERROR` 留痕（`:12-14`）。`info[正常,src_missing,copy_failed]=[True,False,False]`、`ec 次数=[1,1,0]`（`:16-17`），与 `TASK.md:209-210` 裁定附录记录逐项吻合。
- **按裁定二不升级为阻断**：copy_failed 缺 12 键 info **不算**（`TASK.md:148-149`、`:203-204`）；src_missing 落 `None` 行符合 `B2B_DESIGN.md:605` `dict|None` 与 `:434-435`。第 8 个 F 字段 `captured_at_iso_pre`（设计 `:604`）在 H08 `:6625-6629` 单独落盘，不属 `_emit_f` 7 键。
- **措辞歧义登记**（见 §1 B-2 限缩）：裁定二正文「12 键 info 在 src_missing 分支落盘」与附录 `:210`「info 12 键 `[True,False,False]`」及设计代码存在张力；候选实测与设计**代码**一致，此系裁定文本措辞，不改裁定、不重开 B-2。

---

## 4 接线与 F/E 分离

- **唯一调用点已传参**：AST 全量扫 `copy_post_except_evidence` 调用点 **1** 处：`candidate.py:6167`，`pos=['rec','carrier_dir','out_dir']`，`kw=[('pre_freshness_snapshot','pre_freshness_snapshot')]`，传参 = True；`未传 pre 的调用点 = 0`（`_r2_wiring_out.txt:2-3`）。签名 `:4701-4704` 第 4 参保留默认 `None`。
- **finalize_trip 兼容**：def `:6127` 共 14 参，末位 `pre_freshness_snapshot` 带默认（defaults 数 9）；唯一调用点 `:7358`（5 位置参数 + 9 关键字，含 `pre_freshness_snapshot`），不会抛 TypeError（`_r2_wiring_out.txt:4-5`）。
- **F/E 分离（freshness_* 不进退出码）**：`no_new_exception` 判据 `If` 节点 **1** 处，`:6214-6219`，`test = not setdiff.get('no_new_exception', True)`，子树内 `fresh_token=[]`、原文含 `freshness=False`（`_r2_wiring_out.txt:8-9`）。母本 `:5985` 与候选判据行 `:6214` **逐字相等 = True**（`:10-12`）。5 个退出码相关函数体含 `freshness` 全 False：`note_cleanup_failure:403`、`merge_cleanup_code:411`、`except_set_diff:687`、`run_guarded_steps:4526`、`_main_wrapper:7381`（`:13-17`）。设计限缩见 `B2B_DESIGN.md:639`（另有 `:5944/:7075/:7130` 收尾失败点，本人不扩大声称「全局退出码未动」）。
- 本人**亲自重跑**：测试 `python -I -B -X utf8 ".../tests/test_candidate.py"` → 退出码 0、`用例总数: 29`、`Ran 29 tests`、`OK`、`PASS=29 FAIL=0`、`EXIT=0`（`_r2_test_rerun_out.txt:3,65,67,69-70`）；门禁 `python -I -B -X utf8 ".../check_candidate.py"` → 退出码 0、`PASS [1]…[9]`、`ALL 9 GATES PASSED! EXIT=0`（`_r2_gate_rerun_out.txt:6-14,16`）。**按铁律 7，门禁 9/9 只记为「门禁通过」，不作 verdict 依据。**

---

## 5 范围限制

**这一节是本轮 BLOCKED 的唯一成因。** 编排方预判「存在范围外改动」，并要求我本人自核、不许照抄。我以下全部亲自实跑，两种口径分开如实报，不隐瞒任何一种。

### 口径 A · 行文本（`splitlines()`，设计 §4 / 上一轮 / 核心口径核验员所用）：干净，无代码行夹带

- 本人实跑 `difflib.SequenceMatcher(autojunk=False)`：`变更块=12`、`+行=255`、`-行=13`；设计 §4 提取到 `diff 块=9`、`+行=255`、`-行=13`；`候选+ 多重集 == 设计+ = True`、`候选- 多重集 == 设计- = True`、`未在设计+出现的候选+行数 = 0`（`_r2_part1_out.txt:12-16`）。反事实重建：候选 CRLF→LF 后 412759 B，`按行文本(LF拼接)重建 == 候选CRLF剥离 = True`（`:10-11`）。
- **结论（口径 A）**：逐行文本层面 9 个 hunk 精确对上，**没有任何一行代码文本被夹带**。上一轮与核心口径核验员的「范围无夹带」在**此口径下**成立，本人复核无异。

### 口径 B · 字节级（`splitlines(keepends=True)`，本轮新增自核）：整篇行尾被改写，范围外

- 本人实算（`_r2_part1_out.txt:8-9`）：**母本 `CRLF=0 / LF=7291`（全 `\n`，零 CR 字节）**；**候选 `CRLF=7533 / LF=7533`（全 `\r\n`，每行都带 CR）**。
- 字节级 difflib：`变更块=1`、`+行=7533`、`-行=7291`，整篇退化为替换，无法按 H1–H9 逐块归因（`_r2_part1_out.txt:17`）。
- **范围外落点实锤**：设计 §6③ 的 9 个 hunk `-` 侧覆盖区间见 `B2B_DESIGN.md:635`（`212-217 / 4458-4463 / 4558-4565 / 4572-4591 / 5906-5912 / 5936-5942 / 6294-6299 / 6386-6391 / 7122-7128`）。本人取**第 1 行**（明确不在任何 hunk 区间内，`_r2_part1_out.txt:23`）比对：母本第 1 行末字节 `b'3\n'`，候选第 1 行末字节 `b'\r\n'`，文本相同但**行尾被加了 `\r`**（`:21-24`，`第1行(所有hunk之外)文本相同但行尾被加CR = True`）。同样的改写发生在全部 7278 行上下文行上。
- **因果（本人实跑复现）**：`_implement_candidate.py:165` `candidate_text = "\n".join(candidate_lines) + "\n"`，`:166` `CANDIDATE_PATH.write_text(candidate_text, encoding="utf-8")`；Windows 上 `Path.write_text` 默认 `newline=None` 把每个 `\n` 翻成 `\r\n`。本人复现（`_r2_causal_out.txt:2-4`）：写入 `'alpha\nbeta\n'` → 落盘 `b'alpha\r\nbeta\r\n'`，`os.linesep='\r\n'`。⇒ 行尾 `\r` 是候选与「母本 + 设计 9 hunk」之间**唯一**的字节差异类别；设计 §4 **从未声明**此行尾转换。
- 设计侧旁证：`B2B_DESIGN.md:677` 自述「本任务只写设计，不写候选」，`patched` 只在检查脚本内存里以 LF 存在；`:645` build 输出 `母本行数: 7292 patched 行数: 7534`（`split("\n")`）。即批准设计的 9 hunk 定义的是**行文本**改动，完整 `.py` 交付件的整篇行尾转换是候选物化时引入、未被设计覆盖的字节改动。

### 裁定（按硬性规则）

- 硬性规则原文（本轮 ask「判定规则」及 `TASK.md:151`）：「**diff 有超出 H1–H9 的改动** ⇒ `verdict` 必须 `BLOCKED`」。该条**没有被裁定一 / 裁定二加任何豁免**（两条豁免分别用 ★ 明确标注在「状态值层面」与「copy_failed 缺 info」处）。
- 候选是「完整文件」交付件（`lead/b2b_candidate_20261106/TASK.md:15`「你要产出一份完整的 `qc151_trip.py` 候选副本（不是 diff 片段，是完整文件）」、`:33`「必须是完整文件」）。以交付件字节为准，H1–H9 之外区域（含第 1 行、含 E 判据块 `:5984-5990` 所在的不变区）与母本**并非字节相同**。设计 §4 无行尾声明、该改写无法归属任何 hunk（核心口径核验员之外的范围探针亦把它点名为「范围外字节级改动」并交总控裁定）。
- 编排方预判「存在范围外改动」经本人自核**属实**，故该硬性规则触发。**本人不照抄预判、不代为豁免**：按规则 `verdict: BLOCKED`，阻断项登记为 N-1（见「## 阻断项」）。
- **如实两面**：这是**行尾字节转换，不是被夹带的可执行代码**；Python 源码对 CRLF/LF 等价，门禁 `[3]` `ast.parse` 成功（`_r2_gate_rerun_out.txt:8`），行文本语义 9 hunk 干净。但硬性规则没有「仅行尾不计」的例外，且完整文件交付件的整篇行尾改动在 D-25 第 6 步隔离副本集成时会产生整篇 diff，属实打实的范围外改动。是否把「行尾转换」排除出「改动」是**总控裁定权**，本人不代签；关闭路径写在阻断项里。

---

## 6 上一轮遗留事项复核

按 `TASK.md:220-221`，五项**不因裁定消失**。本人逐条自核（实跑输出 `_r2_leftovers_out.txt`），结论均为文档/引用/门禁卫生事项，**不构成候选缺陷**，也**不是本轮 BLOCKED 的成因**（成因仅 §5 的 N-1）：

1. **引用精度瑕疵 1（复核为真）**：上一轮判定书 `CANDIDATE_SEMANTIC_REVIEW.md:26` 把「报告 5 键值是否出现」括注到 `check_candidate.py:101-116`。本人实读 `:101 = 'def main() -> int:'`，`:101-116 含 'req_keys' = False`（`_r2_leftovers_out.txt:3-4`）；`req_keys` 实际在 `:232-238`、检查 [8] 注释在 `:228`（`:5`）。属行号引用瑕疵，实质结论（5 键值确实被检查）不受影响。正确区间 `:228-243`（`req_keys :232-238`）。**保持原状态登记，不重开判定。**
2. **引用精度瑕疵 2（复核为真）**：候选全文严格小写 `freshness` = **38** 行、不区分大小写 = **52** 行（`:8`）；判定书 `:140` 清单区间 `:4798-4807` + `:4810-4812` 展开 13 行，其中 `:4801`（`"captured_at_iso": None`）与 `:4802`（`"pre_snapshot_state": None`）不含字面量（`:9`）。「38 行」数字在严格小写口径下正确，属清单表示与自述数字不一致的呈现瑕疵；退出码判据区间 `:6214-6219` 含 `freshness` = False（`:10`），原结论仍成立。**保持原状态登记。**
3. **STATE_MATRIX #1 条件覆盖偏差（复核为真）**：见 §2；本人实跑 `pre=None + post.read_error` → `post_read_error/none`、`crash_ev=False`（`:12-13`）。偏差成立，但候选与批准设计分类器一致（`B2B_DESIGN.md:310-311`），属矩阵 #1「跑后任意文件状态」措辞应排除 read_error 独立出口的文档精度瑕疵，无 high / 崩溃证据泄漏。**保持「非硬性阻断、如实登记」原状态。**
4. **键名 camelCase ↔ snake_case 映射（值一致；正式映射表本探针未验）**：本人实算（`:16`）候选 `camel=0 / snake=6`，矩阵 `camel=14 / snake=0`，设计 `camel=4 / snake=10`；14 行值集合全 `{False}`，分类器 14/14 全 False（`_r2_matrix_out.txt:2-16`）。**正式字段映射表：本探针未做全库扫描**，沿用上一轮复核件的有界扫描结论「无」（绑定文档集 + `lead/` + `out/re_work/`），本次如实标「未验（本探针）」；`B2B_PREAUDIT.md:156` 只是语义对应旁注，不构成正式映射表。**保持登记，不升级为缺陷。**
5. **门禁读旧输出（复核为真）**：`check_candidate.py:68` `TEST_OUT_REL` 指向 `tests/_test_out.txt`、`:196` `test_out_path = BASE/"tests"/_test_out.txt`；门禁全文引用 `_test_rerun_out` = False、引用 `_test_out.txt` = True（`:20-21`）。检查 [6] 读的是候选目录既存旧输出，不读本人本轮 `_r2_test_rerun_out.txt`。属门禁卫生缺陷（验陈旧产物）；按铁律 7 不据此判语义，按铁律 8 未修改门禁。**保持原状态登记。**

**上一轮已排除七项本人逐条重验（均未触发）**：14 状态覆盖（§2）、unknown 非 high（§2）、唯一调用点已传参（§4）、finalize_trip 兼容（§4）、freshness_* 不进退出码（§4）、重跑测试 `PASS=29 FAIL=0`（§4）、**diff 未超出 H1–H9（此项在行文本口径下未触发、在字节口径下触发，见 §5）**。

---

## 阻断项

**B-1 / B-2 不在本节**：按裁定一 / 裁定二及本人实跑复判，两条确已关闭（§1）。以下为本轮**新增**阻断项，共 1 条。

### N-1（新）· 候选整篇行尾 LF→CRLF，属设计 §4 未声明、H1–H9 之外的字节级改动

- **文件:行 / 实跑输出**：
  - `_r2_part1_out.txt:8-9` — 母本 `CRLF=0 / LF=7291`；候选 `CRLF=7533 / LF=7533`（7533 行全带 `\r`）。
  - `_r2_part1_out.txt:20-24` — 第 1 行（不在 `B2B_DESIGN.md:635` 任何 hunk `-` 侧区间内）文本相同、行尾由 `b'3\n'` 变 `b'\r\n'`；`字节级 keepends 口径变更块=1 / +7533 / -7291`（`:17`）。
  - `_r2_causal_out.txt:2-7` — 复现 `_implement_candidate.py:165-166` 的 `write_text` Windows 换行翻译（写 `'alpha\nbeta\n'` → 落盘 `b'alpha\r\nbeta\r\n'`）。
  - `B2B_DESIGN.md:635`（9 hunk 覆盖区间）、`:205,230,244,380,498,511,524,537,556`（§4 九个 `@@` hunk 头）——**均不含任何行尾转换声明**；`TASK.md:151` / 本轮 ask 判定规则「diff 有超出 H1–H9 的改动 ⇒ BLOCKED」。
- **后果**：触发该硬性规则，`verdict` 必须为 `BLOCKED`。候选作为「完整文件」交付件，其 H1–H9 之外区域（含第 1 行、含 E 判据块 `:5984-5990` 的不变区）与母本并非字节相同；D-25 第 6 步隔离副本集成时会产生整篇行尾 diff。设计 §4 的「9 个 hunk、+255/-13」只在**行文本口径**成立（`_r2_part1_out.txt:12-16`），不能覆盖交付件的字节层。此为**行尾字节转换、非夹带代码**，`ast.parse` 仍成功（`_r2_gate_rerun_out.txt:8`），Python 语义层等价——但规则无「仅行尾不计」豁免，本人不代为豁免。
- **关闭所需证据（任一，且须经复核件确认；本人按铁律 8 不改候选）**：
  1. 总控**书面裁定**「行尾 LF/CRLF 转换不计入本规则的『改动』，且以行文本口径为 diff 唯一权威口径」，并明确该口径适用于 D-25 第 6 步集成；或
  2. 候选按母本 LF **重新物化**（H1–H9 之外逐字节与母本相同），四件指纹中「候选」一项随之更新并由总控重新绑定；或
  3. 批准设计 §4 **增补声明**该行尾转换（明确其覆盖整篇、列出为第 10 项或并入 9 hunk 的落盘约定），经独立复核后重判。
- 关闭前，本判定书维持 `verdict: BLOCKED`；`PASS` 的准确含义（语义上实现批准设计）**即便成立也不等于可应用到母本**（`TASK.md:154,219`，D-25 第 6 步未做）。

---

## 未验

- **真机 / 运行时整趟验证**：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存，未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入（铁律 1、2）。
- **运行时退出码实测**：F/E 分离结论来自静态 AST + 行文本逐字比对（`_r2_wiring_out.txt:7-17`）；`B2B_DESIGN.md:652` 亦自认 `ast.parse` 静态相等 ≠ 运行时实测。
- **`qc151_fields.json` 磁盘实际落盘**：本轮为内存 `Recorder` 离线合成（`_r2_paths_out.txt`），`rec.dump` 链只到上一轮 AST 静态确认，未做真实磁盘落盘复现。
- **main `finally` 在到达 `finalize_trip` 之前失败时 F 是否落盘**：未验。
- **正式字段映射表全库穷尽性**：本探针未做全库扫描（§6 第 4 条）；「无」是上一轮复核件的**有界**扫描结论，非全仓库穷尽否定。
- **档 2 `CANDIDATE_REVIEW.md` 五字段内容属实性**：仅由门禁 [8] 确认五个字面量存在（`_r2_gate_rerun_out.txt:13`），未逐字复核其声明是否为真（铁律：报告字段为 true 只记「声明为 true」）。
- **N-1 的最终定性**：「行尾转换是否构成硬性规则里的『改动』」属总控裁定权；本判定书按规则字面判 BLOCKED 并给出三条关闭路径，未代总控豁免。
- **D-25 第 6 步隔离副本离线集成**：未做（`TASK.md:219`）。本结论**不等于**「候选全绿 / 已验证 / 可用 / 可应用到母本」。
- 上一轮 84 组 `sys.settrace` 轨迹与三次探针修正过程本人未复现（本轮以 14 行矩阵 exec + 13 处 `_finish` AST 佐证）。

---

## 证据等级说明

严格区分三档（承 `TASK.md:30-45`、铁律 7），不混用：

| 档 | 含义 | 本判定书里对应什么 | 能否写进 verdict 依据 |
|:--|:--|:--|:--|
| **档 1 · 机械门禁通过** | `check_candidate.py` 9/9 PASS | 本人重跑 `ALL 9 GATES PASSED! EXIT=0`（`_r2_gate_rerun_out.txt:16`） | **否**。只记「门禁通过」；且门禁 [6] 读旧输出（§6 第 5 条） |
| **档 2 · 报告字段为 true** | `CANDIDATE_REVIEW.md` 五个字段为 true | 仅门禁 [8] 确认字面量存在；内容属实性**未验** | **否**。只记「报告字段声明为 true」 |
| **档 3 · 语义已独立复核** | 本人逐项亲自实跑 / 实读「文件:行」 | §1–§6 全部：四件指纹、三态 exec、14 行矩阵、36 组穷举、三路径离线合成、全量 AST 调用点 / F/E、行文本与字节级 difflib、Windows 换行复现、测试/门禁本人重跑、五项遗留复核 | **是**。本判定书属此档；`verdict: BLOCKED` 由档 3 的 §5 字节级实跑推出 |

- **本判定书属于档 3（语义已独立复核）**，且是**独立复审**：未照抄编排方「存在范围外改动」的预判，而是自核到「第 1 行在所有 hunk 之外被加 `\r`」+ 复现 `write_text` 因果后才判。
- **未因门禁 9/9 或报告字段判 PASS**；反向也未因「B-1/B-2 关闭 + 七项未触发」就一路放行（§5 的 N-1 即取舍所在）。
- 核心口径核验员的「`verdict: PASS` 的语义条件成立」是在**行文本口径 + 其 8 项核验范围**内得出的；本轮新增的字节级 `keepends` 自核不在该 8 项内，其结论不被推翻、但被 N-1 按硬性规则覆盖。
- `verdict: PASS` 的准确含义 = 语义上实现批准设计；**不等于可应用到母本**（D-25 第 6 步未做）。本轮为 `BLOCKED`，更不写「候选全绿 / 已验证 / 可用」。
- 只读域零改动：交付前四件指纹复算全部 `match=True`；`lead/b2b_candidate_20261106/__pycache__/` 两件 `.pyc` 的 mtime 为 18:05 / 18:27（早于本人 21:xx 会话），本人未写入、未更新；未 commit / push。唯一写入为 `lead/b2b_candidate_review2_20261106/` 下的输出文件。

---

## 附 实跑命令清单（均为本次会话亲自执行，`cd /d/Project/ra2-campaign-forge`）

| 命令（摘要） | 输出文件 | 关键结论 |
|:--|:--|:--|
| `python -I -X utf8 - <<'PY'`（4 件 hashlib 指纹 + 行文本/字节级 difflib + 第 1 行落点） | `_r2_part1_out.txt` | 4/4 match；母本 LF / 候选 CRLF；第 1 行范围外加 `\r` |
| `python -I -X utf8 - <<'PY'`（Windows `write_text` 换行复现） | `_r2_causal_out.txt` | `'alpha\nbeta\n'` → `b'alpha\r\nbeta\r\n'` |
| `python -I -X utf8 - <<'PY'`（importlib 隔离加载 + 三态 exec） | `_r2_three_state_out.txt` | 三态可分；原始输入归一 = 设计意图 |
| `python -I -X utf8 - <<'PY'`（14 行矩阵 + `_finish` AST + 36 组穷举） | `_r2_matrix_out.txt` | 14/14 match；unknown 恒 none；泄漏 0 |
| `python -I -X utf8 - <<'PY'`（三路径内存 stub 离线合成，修正 `sha256_file` stub 后） | `_r2_paths_out.txt` | 7F `[T,T,T]`；info `[T,F,F]`；ec `[1,1,0]` |
| `python -I -X utf8 - <<'PY'`（全量 AST 调用点 + finalize_trip + F/E） | `_r2_wiring_out.txt` | 调用点 1 已传参；判据零 freshness |
| `python -I -X utf8 - <<'PY'`（五项遗留复核） | `_r2_leftovers_out.txt` | 五项复核为真 / 未验，保持原状态 |
| `python -I -B -X utf8 "…/tests/test_candidate.py" > "_r2_test_rerun_out.txt" 2>&1` | `_r2_test_rerun_out.txt` | 退出码 0；`PASS=29 FAIL=0` |
| `python -I -B -X utf8 "…/check_candidate.py" > "_r2_gate_rerun_out.txt" 2>&1` | `_r2_gate_rerun_out.txt` | 退出码 0；`ALL 9 GATES PASSED!`（仅档 1） |

（说明：Mimosa 钩子以「exec 外部数据」拦截了写入 `.py` 探针的尝试，故按任务明许的「AST 提取后 exec 到隔离命名空间」改为**全部内联 heredoc 实跑**；三态/矩阵/三路径/接线/遗留改用与 `tests/test_candidate.py:40-57` 相同的 `importlib` + DPI patch 隔离加载，结论只取实跑输出。两次失败的 heredoc 残留已删除，写域内仅留上表 9 份干净输出与本判定书。）
