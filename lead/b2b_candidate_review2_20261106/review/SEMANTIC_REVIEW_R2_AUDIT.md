# 第二轮判定书 · 独立复核件（专项 A/B/C/D + 逐条 文件:行）

**日期**：2026-11-06　**复核员**：判定书复核员（新上下文，独立）
**被核对象**：`lead/b2b_candidate_review2_20261106/CANDIDATE_SEMANTIC_REVIEW_R2.md`
**subjectSha256**：`126e18954d77d989bf7c036de676c3d3566f0d4feaa2afb2099ac5f671d76546`
**subjectBytes**：`27593`
（实跑：`python -I -B -X utf8 -c "import hashlib;...hashlib.sha256(b).hexdigest();len(b)"`，开工与交付前各算一次，两次一致）

**铁律遵守**：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）、零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入）；只读域未改；未 commit / push；Python 全部 `python -I -B -X utf8` + 绝对路径；指纹用 `hashlib`（本机无 sha256sum / wc，未用）。唯一写入为 `lead/b2b_candidate_review2_20261106/` 内本复核件与两份本人重跑输出、探针自身重写的 `_review2_probe_out.txt`。

---

## 0 结论摘要

| 字段 | 值 |
|:--|:--|
| `subjectSha256` | `126e18954d77d989bf7c036de676c3d3566f0d4feaa2afb2099ac5f671d76546` |
| `subjectBytes` | `27593` |
| `checkedEveryRow` | `true` |
| `noOverreach` | `true` |
| `blockedCount` | `1` |

- **专项 A（BLOCKED 写成 PASS）**：未发现。判定书 `:18` 唯一独立成行的 verdict 为 `verdict: BLOCKED`；B-1/B-2 的「不再成立 / 关闭」只针对两条旧阻断，`:26` 明写「两条旧阻断关闭 ≠ 整体 PASS」，`:117` 明写「以下为本轮新增阻断项，共 1 条」。
- **专项 B（机械通过 → 语义已复核）**：未发现。`:71`、`:155`、`:160`、`:157`、`:162` 均把门禁 9/9 明确归为「档 1 · 机械门禁通过」并写明「不作 verdict 依据」「未因门禁 9/9 或报告字段判 PASS」；`verdict: BLOCKED` 由 `:157` 声明出自档 3 的 §5 字节级实跑。
- **专项 C（语义 PASS → 可应用到母本）**：未发现。`可应用到母本` 3 处（`:131`、`:144`、`:162`）全部是否定式（「**即便成立也不等于**」「**不等于**」「更不写」）；`可直接施用` / `直接施用` 全文 0 处；`候选全绿`/`已验证`/`可用` 只出现在两处否定清单里。
- **专项 D（因裁定已修正口径就跳过重新验证、沿用上一轮结论）**：**未发现跳过**。B-1/B-2、七项硬性规则、五项遗留均声明本人实跑/实读复判，且我逐项复现其结论（见 §3）；唯一出现「沿用」的是 `:108`/`:141` 的「正式字段映射表」穷尽性，判定书**明写「未验（本探针）」**，是显式标注未验、不是把上一轮结论冒充本轮验证。

**其它问题（不影响 verdict，如实登记）**：2 条，见 §7。

---

## 1 逐条打开判定书里每个 文件:行（不抽样）

判定书共 42 行含引用（第 5/7/30/34/35/36/40/41/42/50/51/53/59/60/61/62/68/69/70/71/81/86/87/88/89/90/94/95/97/103/105/106/107/108/109/122/123/124/125/126/131/138/142/144/151/155/181 行），含 148 个引用 token（含 `:N` 裸引用，按上下文归属到本行点名的输出文件）。以下按文件分组，**全部 opened 并逐条核对**。

### 1.1 本轮 `TASK.md`（`lead/b2b_candidate_review2_20261106/TASK.md`，221 行）

| 判定书引用 | 实读结果 | 核 |
|:--|:--|:--|
| `:183-221`（裁定附录） | `:183`=「## 裁定附录…」、`:191`=裁定一、`:201`=裁定二、`:221`=末行 | ✅ |
| `:193-199`（裁定一） | `:193` 作废「三种输入有任意两种输出相同 ⇒ BLOCKED」、`:194` 生效「状态值层面…互不相同」、`:199`「原始输入全同是**设计意图**，不是缺陷」 | ✅ `:35` 引用属实 |
| `:199` | 同上 | ✅ |
| `:201-210`（裁定二） | `:203` 作废「12 键 info 在某条路径缺失 ⇒ BLOCKED」、`:204` 生效「7 个 FRESHNESS 字段必须三路径全落盘；12 键 info 只在正常路径与 src_missing 分支落盘即可」、`:209-210`「`True/True/True`；`[True, False, False]`；`[1,1,0]`」 | ✅ `:41`、`:60`、`:62` 引用属实 |
| `:148-149`、`:149`、`:203-204`、`:209-210`、`:210` | `:148-149` 明写「copy_failed 路径没有 evidence_copy 行**符合设计**，不算阻断」；`:203-204` 作废/生效口径；`:210` `[True, False, False]`、`[1,1,0]` | ✅ |
| `:151` | `候选 diff 里有**超出 H1–H9 范围**的改动；` —— 硬性规则字面确为「超出 H1–H9 ⇒ BLOCKED」（`:140-152` 段） | ✅ `:94`/`:125` 引用属实 |
| `:154,219` | `:154`「`verdict: PASS` 的准确含义…**不等于可以应用到母本**」；`:219`「★ 本裁定不构成『候选可应用到母本』」 | ✅ `:131` 引用属实 |
| `:219`（`:144`） | 同上，D-25 第 6 步未做 | ✅ |
| `:220-221` | 五项「**保持原状态登记，不因本裁定消失**」 | ✅ `:103` 引用属实 |
| `:30-45` | 三档证据等级纪律 + 严禁「候选全绿/已验证/可用」 | ✅ `:151` 引用属实 |

### 1.2 批准设计 `B2B_DESIGN.md`（693 行）

| 判定书引用 | 实读结果 | 核 |
|:--|:--|:--|
| `:95`、`:100-103`、`:106` | `:95`「`classify_except_freshness` 首段把 `None`/`{}`/缺 `state`/脏值一律归一为 `unknown`，且在**第一个分支**就让 `unknown` 与 `absent_confirmed` 分道」；`:100-103` 四行全 `unknown/none`；`:106`「`{"exists": False}`（无 `state`）**不再是「确认无件」**」 | ✅ `:35`/`:36` 属实 |
| `:310-311` | `:310`「`# ★ N1：错误独立出口，优先于一切状态折叠`」、`:311` `if post.get("read_error"):` | ✅ `:53`/`:107` 属实 |
| `:434-435` | 明写 `rec.add("EXCEPT", "evidence_copy", None, f"{src}:path", ...)` | ✅ `:41`/`:61` 属实 |
| `:597-603` | 7 行依次为 `freshness_verdict/confidence/is_new/note/pre_snapshot_state/usable_as_crash_evidence/captured_at_iso` | ✅ `:59` 属实 |
| `:604`、`:605` | `:604` `FRESHNESS.captured_at_iso_pre`；`:605` `EXCEPT.evidence_copy`（`info` 由 5 键扩到 12 键）`dict \| None`，写入点「正常路径与 `src_missing` 分支」 | ✅ `:41`/`:61` 属实 |
| `:635` | 9 个 hunk `-` 侧覆盖区间 `212-217 / 4458-4463 / 4558-4565 / 4572-4591 / 5906-5912 / 5936-5942 / 6294-6299 / 6386-6391 / 7122-7128`，且「均不含 5984-5990」 | ✅ `:88`/`:123`/`:125` 属实 |
| `:639` | 「③ 的口径限缩（不美化）」：另有 `:5944`/`:7075`/`:7130` 三个 `note_cleanup_failure` 调用点，绑定结论收窄 | ✅ `:70` 引用属实（我另实读母本 `:5944`/`:7075`/`:7130`，三行确为 `note_cleanup_failure(` 调用） |
| `:645` | `母本行数: 7292  patched 行数: 7534`（`split("\n")`） | ✅ `:90` 属实 |
| `:652` | 「**未验**：`ast.parse` 静态相等 ≠ 运行时退出码实测」 | ✅ `:138` 属实 |
| `:677` | 「2. **未写出候选 `.py`**：铁律 4『本任务只写设计，不写候选』。`patched` 只在检查脚本内存里存在」 | ✅ `:90` 属实 |
| `:205,230,244,380,498,511,524,537,556` | 实跑 `L[i] for i in ...` 得 9 行全部为 `@@ -...` hunk 头，与判定书逐字一致 | ✅ `:125` 属实 |
| 设计 §4 无行尾声明 | 我实跑扫全文 `CRLF|\\r\\n|行尾|换行|newline|line.ending` → **0 命中**；9 个 ```diff 块内亦 0 命中 | ✅ 支撑 `:89`/`:125` 的「从未声明」 |

### 1.3 候选 `qc151_trip.candidate.py`（7533 行）

| 判定书引用 | 实读结果 | 核 |
|:--|:--|:--|
| `:4634-4638` | `pre.get("state")`；`if st not in FRESHNESS_SNAPSHOT_STATES: st = "unknown"` | ✅ `:36` 属实 |
| `:4648-4651` | `if st == "unknown": return _finish("unknown","none",...)` | ✅ |
| `:4666-4669` | `if st == "absent_confirmed": return _finish("new_first_appearance","high",...)` | ✅ |
| `:4643-4646`、`:4648` | `read_error` 独立出口在 `unknown` 之前 | ✅ `:53` 属实 |
| `:4616-4698` | `def classify_except_freshness` 至 `rewritten_same_content/medium` 返回，共 83 行 | ✅ `:50` 属实 |
| `:4701-4704` | 第 4 参 `pre_freshness_snapshot: dict \| None = None` | ✅ `:68` 属实 |
| `:4724-4753`、`:4730/:4733/:4736/:4740/:4743/:4747/:4751` | `_emit_f` 内 7 个 `rec.add`，键位逐名一致（我实跑正则提取得 7 键） | ✅ `:59` 属实 |
| `:4759` | `rec.add("EXCEPT","evidence_copy", None, ...)` | ✅ `:41`/`:42` 属实 |
| `:4762-4763`、`:4788-4789`、`:4815`、`:4790` | src_missing / copy_failed / copied 三处 `_emit_f` 调用；`:4790` = `raise` | ✅ `:40`/`:41` 属实 |
| `:4795-4815` | 正常路径 `info` 12 键 + `_emit_f(fresh,"copied")` | ✅ |
| `:4801`/`:4802` | `captured_at_iso: None` / `pre_snapshot_state: None`，确不含 `freshness` 字面量 | ✅ `:106` 属实 |
| `:5984-5990` | 候选该区间与母本 `:5984-5990` **行号不对应**（候选是 `shutil.rmtree` 块），判定书 `:95`/`:126` 用它指「E 判据块所在的不变区」，属**母本行号借指**；见 §7 问题 1 | ⚠️ 表述不精确，非实质错误 |
| `:6127`、`:6167`、`:6168`、`:6214-6219`、`:7358`、`:6625-6629`、`:5985`(母本) | 逐一实读均相符；`:6214` 与母本 `:5985` **逐字相等 = True**（我实跑比对） | ✅ |
| `:403/:411/:687/:4526/:7381` | 5 个退出码相关函数定义行，我实跑 AST 得 5 个函数体含 `freshness` 全 False | ✅ `:70` 属实 |

### 1.4 其它文件

| 判定书引用 | 实读结果 | 核 |
|:--|:--|:--|
| `STATE_MATRIX.json:2-15`、`:2` | 实为 14 行（`:2`-`:15`），`:2` 条件含「跑后任意文件状态」⇒ `unknown` | ✅ `:50`/`:53` 属实 |
| `_implement_candidate.py:165`、`:166`、`:165-166` | `:165` `candidate_text = "\n".join(candidate_lines) + "\n"`；`:166` `CANDIDATE_PATH.write_text(candidate_text, encoding="utf-8")`（无 `newline=` 参数） | ✅ `:89`/`:124` 属实 |
| `lead/b2b_candidate_20261106/TASK.md:15`、`:33` | `:15`「你要产出**一份完整的** `qc151_trip.py` 候选副本（不是 diff 片段，是完整文件）」；`:33`「**必须是完整文件**」 | ✅ `:95` 属实 |
| `tests/test_candidate.py:40-57` | `load_candidate_isolated` 用 `importlib.util` + `patch("ctypes.windll.user32.SetProcessDPIAware", return_value=1)` | ✅ `:30`/`:181` 属实 |
| `check_candidate.py:101-116`、`:68`、`:196`、`:232-238`、`:228` | `:101`=`def main() -> int:`，`:101-116` 无 `req_keys`；`:68` `TEST_OUT_REL = "…/tests/_test_out.txt"`；`:196` `test_out_path = BASE/"tests"/"_test_out.txt"`；`:232-238` 五个 `req_keys`；`:228` 检查[8] 注释 | ✅ `:105`/`:109` 属实（我另实跑全文扫 `'_test_rerun_out' present=False`、`'_test_out.txt' present=True`） |
| `CANDIDATE_SEMANTIC_REVIEW.md:26`（上一轮） | 确为「验的是格式 / 存在性 / 锚点字符串 / 报告 5 个键值是否出现（`:101-116`）」 | ✅ `:105` 属实 |
| `B2B_PREAUDIT.md:156` | 只是「`usableAsCrashEvidence` 属性」语义对应旁注；全文无「映射表」三字 | ✅ `:108` 属实 |
| 全部 `_r2_*.txt` / `_r2_part1_out.txt:2-5,8-9,10-11,12-16,17,20-24` / `_r2_causal_out.txt:2-4,2-7` / `_r2_three_state_out.txt:1-2,5-10,11-16,16` / `_r2_matrix_out.txt:2-16,17-21` / `_r2_paths_out.txt:2,5,9,12-14,15-18` / `_r2_wiring_out.txt:2-3,4-5,7-17,8-9,10-12,13-17` / `_r2_leftovers_out.txt:3-4,5,8-10,12-13,16,20-21` / `_r2_test_rerun_out.txt:3,65,67,69-70` / `_r2_gate_rerun_out.txt:6-14,16,8,13` | 逐行 `nl -ba` 打开全部 9 份输出，引用行号与内容逐条相符 | ✅ 无一条错引 |

**`checkedEveryRow = true`**：判定书 182 行全部读过，148 个引用 token 全部按上下文归属并打开核对；含引用的 42 行、无引用的说明行亦读过。

---

## 2 亲自重跑 `_review2_probe.py`，核输出一致

**实跑命令**（原样，未加替代参数）：
```
cd /d/Project/ra2-campaign-forge
python -I -B -X utf8 "D:/Project/ra2-campaign-forge/lead/b2b_candidate_review2_20261106/_review2_probe.py"
```
**stdout**：
```
WROTE D:/Project/ra2-campaign-forge/lead/b2b_candidate_review2_20261106/_review2_probe_out.txt lines= 466
STATS total_blocks=12 attributed=12 unattributed=0 unattributed_plus_lines=0 extra_plus=0 extra_minus=0
REBUILD_EQUALS_CANDIDATE= True
PROBE_EXIT=0
```
脚本自身会覆写 `_review2_probe_out.txt`（`:473` `P_OUT.write_text(..., newline="\n")`）。我在重跑前后各算一次 hashlib 指纹：
- 重跑前：`b1e5f6010405c653722278784c8b4c9847b2bc9b85806edd0abc42b5a718e14d` / 36002 B
- 重跑后：`b1e5f6010405c653722278784c8b4c9847b2bc9b85806edd0abc42b5a718e14d` / 36002 B
- `MATCH = True`

⇒ **探针输出与既有 `_review2_probe_out.txt` 逐字节一致**（466 行），判定书引用的 `_r2_part1_out.txt` 数字亦由我独立实算复现（见 §3）。

---

## 3 `_test_rerun_out.txt` / `_gate_rerun_out.txt` 是否为真实运行输出

我**亲自重跑**了被核对象所声称的两条命令（同一脚本、同一参数，输出落到本写域 `review/` 下的新文件，不覆盖原件）：
```
python -I -B -X utf8 "D:/Project/ra2-campaign-forge/lead/b2b_candidate_20261106/tests/test_candidate.py" > ".../review/_audit_test_rerun_out.txt" 2>&1   → TEST_AUDIT_EXIT=0
python -I -B -X utf8 "D:/Project/ra2-campaign-forge/lead/b2b_candidate_20261106/check_candidate.py" > ".../review/_audit_gate_rerun_out.txt" 2>&1      → GATE_AUDIT_EXIT=0
```
归一化（仅替换首行 ISO 时间戳与 `Ran 29 tests in X.XXXs` 的耗时）后逐行比对：

| 比对 | 结果 |
|:--|:--|
| `_test_rerun_out.txt` vs `_r2_test_rerun_out.txt` | `equal=True` |
| `_test_rerun_out.txt` vs 我的 `_audit_test_rerun_out.txt` | `equal=True` |
| `_r2_test_rerun_out.txt` vs 我的 `_audit_test_rerun_out.txt` | `equal=True` |
| `_gate_rerun_out.txt` vs `_r2_gate_rerun_out.txt` | `equal=True` |
| `_gate_rerun_out.txt` vs 我的 `_audit_gate_rerun_out.txt` | `equal=True` |
| `_r2_gate_rerun_out.txt` vs 我的 `_audit_gate_rerun_out.txt` | `equal=True` |

我的重跑尾行分别为 `PASS=29 FAIL=0` / `EXIT=0` 与 `ALL 9 GATES PASSED! EXIT=0`，与两份既有文件一致。我另实读两个脚本的输出生成点：`test_candidate.py:645` 打印 ISO 时间戳、`:657` `print(f"PASS={pass_count} FAIL={fail_count}")`、`:658` `print(f"EXIT=...")`；`check_candidate.py:274` `print("ALL 9 GATES PASSED! EXIT=0")`。文件 mtime（21:24:48 / 21:24:50 / 21:36:48 / 21:36:52）与内嵌时间戳（21:24:46 / 21:36:46）自洽；`git log -1` 仍为 `2657458`，review2 整目录为 `??` 未入账。

⇒ **两份 `_test_rerun_out.txt` / `_gate_rerun_out.txt` 及 `_r2_` 副本均可由本人重跑逐行复现，属真实运行输出（档 1 机械门禁/测试），不是编造。** 但按铁律 7，此结论**不**推出语义 PASS，判定书亦未如此推（`:71` 明写「门禁 9/9 只记为『门禁通过』，不作 verdict 依据」）。

---

## 4 判定书语义结论的独立复现（验它「有没有把机械通过说成语义通过」）

判定书的语义结论我不照抄，逐项亲自实跑/实算复现：

| 判定书主张 | 我的实跑命令（摘要） | 我的输出 | 一致 |
|:--|:--|:--|:--|
| 四件指纹 `517889…/9656…/5657…/6333…` + 字节数 | `hashlib.sha256` 读 4 件 | 全部逐字相同，399508/420292/66735/13763 | ✅ |
| 母本 `CRLF=0/LF=7291`、候选 `CRLF=7533/LF=7533`、去 CR 后 412759 B | `bytes.count` | `0/7291`、`7533/7533`、`412759` | ✅ |
| 第 1 行在所有 hunk 之外、文本相同但行尾被加 CR | `splitlines(keepends=True)` + 区间检查 | 母本 `b'3\n'` / 候选 `b'\r\n'`（首行 `#!/usr/bin/env python3`），`any(a<=1<=b)=False` | ✅ |
| Windows `write_text` 换行翻译因果 | 写域内临时件 `write_text('alpha\nbeta\n')` 后读字节并删除 | `b'alpha\r\nbeta\r\n'`，`os.linesep='\r\n'` | ✅ |
| 口径 A `12 块 / +255 / -13`、设计 9 块 `+255/-13`、候选+/-多重集相等、EXTRA+=0 | `difflib.SequenceMatcher(autojunk=False)` + `Counter` | 全部一致 | ✅ |
| 口径 B `1 块 / +7533 / -7291` | `splitlines(keepends=True)` + difflib | 一致 | ✅ |
| 设计 §4 九块无行尾声明 | 正则扫设计全文 + 9 个 diff 块 | 0 命中 | ✅ |
| 三态可分、五种原始输入归一、裁定一验收点 True | `importlib` + DPI patch 隔离加载，真调 `classify_except_freshness` | `五种全同=True`；`['new_first_appearance','new_write','unknown']`；`absent_confirmed≠unknown=True` | ✅ |
| 14 行矩阵 `MATRIX_14_ALL_MATCH=True` | 依 `STATE_MATRIX.json` 14 行条件造 fixture 真调分类器 | 14/14 `match=True` | ✅ |
| `_finish` 13 处、unknown 仅 `(4649,unknown,none)`、high 三处、36 组泄漏 0 | AST + `itertools.product` | 全部一致 | ✅ |
| 三路径 `7F=[T,T,T]`、`info=[T,F,F]`、`ec=[1,1,0]`、三条 ERROR、`raise` | 内存 `Rec`/`FakePath` stub 离线合成（**修正自己的 stub 两轮**，未改候选） | 与 `_r2_paths_out.txt:15-18` 逐项一致 | ✅ |
| 唯一调用点 `:6167` 已传参、`finalize_trip :6127` 14 参/9 defaults、`:7358` 兼容 | `ast.walk` 全量 | `1` 处、kw 含 `pre_freshness_snapshot`；`14/9`；`pos=5 kw=9` | ✅ |
| `no_new_exception` If 1 处 `:6214-6219` 子树零 freshness；母本 `:5985` 与候选 `:6214` 逐字相等；5 函数体零 freshness | AST + `splitlines` 比对 | 全部一致 | ✅ |
| 全文严格小写 `freshness` 38 行 / 不区分大小写 52 行；`:4801/:4802` 不含字面量 | 逐行计数 | `38` / `52`，`[4801,4802]` | ✅ |
| `camel=0/snake=6`（候选）、`14/0`（矩阵）、`4/10`（设计，按行计） | 逐行计数 | 一致（注：按出现次数计设计为 `4/11`，见 §7 问题 2） | ✅ |
| `__pycache__` 两件 .pyc mtime 早于本人会话 | `stat().st_mtime` | `18:05:13` / `18:27:40` | ✅ |

⇒ 判定书 §1–§6 的语义结论**确实有本人实跑/实读支撑**，不是把机械门禁当作语义证据。判定书 `:157` 自称「档 3 · 语义已独立复核」在本复核范围内成立。

---

## 5 专项 A：有没有把 BLOCKED 写成 PASS

逐行搜 `PASS`（11 处）与 `BLOCKED`（12 处），并核唯一独立成行的 verdict：
- `:18` `verdict: BLOCKED`（实跑 `re.fullmatch` 得唯一 1 条）。
- `:26` 「两条旧阻断关闭 ≠ 整体 PASS」；`:44`、`:71`、`:111`、`:178` 的 `PASS=29` 是**测试输出字面量**，不是 verdict；`:155` 是档 1 表格里的 `9/9 PASS`；`:160` 明写「未因门禁 9/9 或报告字段判 PASS」；`:161`/`:162` 讨论 `verdict: PASS` 的**准确含义**，`:162` 结句「本轮为 `BLOCKED`」；`:131`「维持 `verdict: BLOCKED`」。
- `## 阻断项`（`:115-131`）登记 1 条 N-1，带文件:行（`:122-125`）、后果（`:126`）、三条关闭所需证据（`:127-130`）。

⇒ **专项 A 未发现违规**。B-1/B-2 的「关闭」是按 `TASK.md:214`/裁定附录明文（我实读 `:214`「B-1 / B-2 两条阻断，按本裁定不再成立」）且经本人实跑复判，不是把 BLOCKED 改写成 PASS。

## 6 专项 B：有没有把「门禁通过」写成「语义已复核」

- `:71`：「**按铁律 7，门禁 9/9 只记为「门禁通过」，不作 verdict 依据。**」
- `:155`（档 1 表格行）：「**否**。只记「门禁通过」；且门禁 [6] 读旧输出」——「能否写进 verdict 依据」列明确为「否」。
- `:156`（档 2）：「**否**。只记「报告字段声明为 true」」；`:142`「内容属实性**未验**」。
- `:157`（档 3）：「**是**。本判定书属此档；`verdict: BLOCKED` 由档 3 的 §5 字节级实跑推出」。
- `:160`「未因门禁 9/9 或报告字段判 PASS」；`:162`「本轮为 `BLOCKED`，更不写…」；`:97`、`:126` 把 `ast.parse` 成功（门禁 [3]）只用作「行尾字节转换、非夹带可执行代码」的**如实两面**陈述，并明写「但硬性规则没有『仅行尾不计』的例外」。
- 我另独立核实门禁 [6] 确读旧输出（`check_candidate.py:196` 指向 `tests/_test_out.txt`，全文不含 `_test_rerun_out`），判定书 `:109` 的卫生缺陷登记属实。

⇒ **专项 B 未发现违规**。三档分层与 `TASK.md:30-45` 一致，verdict 依据来自字节级实跑而非门禁。

## 7 专项 C：有没有「可应用到母本」「可直接施用」这类越权表述

全文检索（实跑）：
- `可应用到母本` 3 处：`:131`「**即便成立也不等于可应用到母本**」、`:144`「本结论**不等于**『候选全绿 / 已验证 / 可用 / 可应用到母本』」、`:162`「**不等于可应用到母本**…本轮为 `BLOCKED`，更不写『候选全绿 / 已验证 / 可用』」——**全为否定式**。
- `可直接施用` / `直接施用` / `可以应用`：**0 处**。
- `候选全绿`/`已验证`/`可用`：仅 `:144`、`:162` 两处否定清单中出现。

⇒ **`noOverreach = true`**。判定书 `:154,219`（我实读 `TASK.md:154`、`TASK.md:219`）与 `TASK.md:44` 的禁令一致，D-25 第 6 步未做如实登记（`:144`）。

## 8 ★ 专项 D：有没有因为「裁定已修正口径」就跳过重新验证、直接沿用上一轮结论

这是本轮最需警惕的一项，我逐条核：

1. **B-1（裁定一）**：`:30-36` 明写「我本人用 `importlib.util` + patch…真调 `classify_except_freshness`」，引用 `_r2_three_state_out.txt:1-2,5-10,11-16`；我独立复现五种输入归一 = True、三态两两不等 = True、裁定一验收点 = True（§4）。**未跳过**。
2. **B-2（裁定二）**：`:40-42` 明写「我本人离线合成三路径」，引用 `_r2_paths_out.txt`；我独立复现 `7F=[T,T,T]`、`info=[T,F,F]`、`ec=[1,1,0]`、三条 ERROR + `raise`（§4）。**未跳过**。
3. **七项硬性规则**：`:44`「**其余硬性规则本人逐条重验（均未触发）**」、`:111`「上一轮已排除七项本人逐条重验」；我逐项复现 14 状态覆盖、unknown 非 high、唯一调用点、finalize_trip 兼容、F/E 分离、测试 29/0（§4），并核第 7 项 diff 在两口径下如实分报（`:111` 明写「行文本口径下未触发、字节口径下触发」）。**未跳过**。
4. **五项遗留**：`:103`「本人逐条自核（实跑输出 `_r2_leftovers_out.txt`）」、`:105-109` 逐条给出本人实读/实算数字；我复现了 `req_keys` 行号瑕疵、38/52 行计数、STATE_MATRIX #1 偏差、camel/snake 计数、门禁读旧输出（§4）。结论是「保持原状态登记」（符合 `TASK.md:220-221`），**不是**「照抄上一轮结论」。
5. **范围限制（本轮 BLOCKED 成因）**：`:77`「编排方预判…并要求我本人自核、**不许照抄**。我以下全部亲自实跑」、`:96`「经本人自核属实…**本人不照抄预判、不代为豁免**」、`:159`「未照抄编排方…的预判，而是自核到『第 1 行在所有 hunk 之外被加 `\r`』+ 复现 `write_text` 因果后才判」。我独立复现了行尾、第 1 行落点、write_text 因果、两口径 difflib（§4）。**不仅未跳过，反而是新增自核导致本轮 BLOCKED**。
6. **唯一「沿用」字样**：`:108`/`:141` 的「正式字段映射表全库穷尽性」——`:108` 原文「**正式字段映射表：本探针未做全库扫描**，沿用上一轮复核件的有界扫描结论『无』…本次如实标『未验（本探针）』」、`:141`「『无』是上一轮复核件的**有界**扫描结论，非全仓库穷尽否定」。这是**显式标注未验**，把上一轮结论明确限定为「有界扫描」且不作为本轮验证结果，与「跳过重新验证直接沿用上一轮结论」性质不同。我实读 `B2B_PREAUDIT.md:156` 确认其只是语义对应旁注、全文无「映射表」三字，判定书 `:108` 的定性属实。

⇒ **专项 D 未发现违规**：判定书没有因「裁定已修正口径」跳过重新验证；B-1/B-2 的关闭是「按新口径 + 本人实跑复判」，而非「照抄裁定附录 `:198`/`:209-210` 的『候选实测（复审员已做）』」。裁定附录里那两句「复审员已做」若被直接当作本轮结论才会构成违规，判定书没有这样做。

---

## 9 其它问题（如实登记，均不影响 verdict）

1. **候选行号借指母本行号**：判定书 `:95` 与 `:126` 写「含 E 判据块 `:5984-5990` 所在的不变区」，但 `:5984-5990` 是**母本**行号（我实读母本 `:5984-5990` 为集合差判据块；候选 `:5984-5990` 是 `shutil.rmtree` 清理块）。判定书 §5 的论证意指的是「该不变区在候选里对应 `:6214-6219`」，属行文借指、未标明母本，读起来易生歧义。**非实质错误**：N-1 的落点实锤用的是第 1 行（`:88`、`:123`），我已独立验证第 1 行确在所有 hunk 之外且被加 CR，BLOCKED 依据不受影响。
2. **`snake=10` 的计量口径未标注**：`:108` 写「设计 `camel=4 / snake=10`」。我实算：按「含字面量的**行数**」为 `4/10`（与判定书一致）；按「**出现次数**」为 `4/11`（`B2B_DESIGN.md:118` 一行含 2 次 `usable_as_crash_evidence`）。判定书未声明按行计，属计量口径未标注的呈现瑕疵，不是数值错误。B-1/B-2 与 N-1 结论均不依赖该数字。

`blockedCount = 1`：判定书 `## 阻断项` 仅 N-1 一条（`:117` 明写「共 1 条」），B-1/B-2 已按裁定附录关闭且本节不列入（`:117`）。本复核**不代为豁免** N-1，也不把 `verdict: BLOCKED` 改写成 PASS。

---

## 10 实跑命令清单（本次会话亲自执行）

| # | 命令（`cd /d/Project/ra2-campaign-forge`） | 用途 |
|:--|:--|:--|
| 1 | `python -I -B -X utf8 -c "import hashlib;..."` | subject SHA256 / 字节数；开工 + 交付前各一次 |
| 2 | `python -I -B -X utf8 "…/_review2_probe.py"` | 亲自重跑探针；stdout 见 §2 |
| 3 | `python -I -B -X utf8 -c "hashlib… _review2_probe_out.txt"` | 重跑前后输出指纹比对 |
| 4 | `python -I -B -X utf8 "…/tests/test_candidate.py" > "…/review/_audit_test_rerun_out.txt" 2>&1` | 亲自重跑测试，`EXIT=0` |
| 5 | `python -I -B -X utf8 "…/check_candidate.py" > "…/review/_audit_gate_rerun_out.txt" 2>&1` | 亲自重跑门禁，`EXIT=0` |
| 6 | `python -I -B -X utf8 -c "归一化时间戳后 4 份输出两两逐行比对"` | §3 六项 `equal=True` |
| 7 | `python -I -B -X utf8 -c "批量 dump 候选/设计/母本/TASK/check_candidate 引用行区间"` | §1 逐条 文件:行 |
| 8 | `python -I -B -X utf8 -c "importlib+DPI patch 真调 classify_except_freshness"` | 三态 / 36 组 / 14 行矩阵 / STATE_MATRIX #1 |
| 9 | `python -I -B -X utf8 -c "内存 stub 三路径离线合成"` | 7F / info / ec / ERROR / raise |
| 10 | `python -I -B -X utf8 -c "ast.walk 全量调用点 + finalize_trip + If 判据"` | 接线与 F/E 分离 |
| 11 | `python -I -B -X utf8 -c "difflib 两口径 + Counter 多重集 + 设计 diff 块"` | 行文本 9 hunk / 字节级整篇改写 |
| 12 | `python -I -B -X utf8 -c "write_text('alpha\\nbeta\\n') 复现 + 临时件删除"` | Windows 换行因果 |
| 13 | `python -I -B -X utf8 -c "全文检索 PASS/BLOCKED/可应用/未验/沿用/裁定…"` | 专项 A/B/C/D |

未运行 / 未验：真机整趟验证（铁律 1）、运行时退出码实测、D-25 第 6 步隔离副本集成、正式字段映射表全库穷尽性（判定书已自标「未验（本探针）」）。这些**未验**项本复核同样未做，不作为通过依据。
