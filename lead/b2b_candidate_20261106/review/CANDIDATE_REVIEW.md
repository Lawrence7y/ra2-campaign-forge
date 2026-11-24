# CANDIDATE_REVIEW · B2b 候选副本独立复核报告

**复核员**：候选复核员（独立子代理会话）  
**复核日期**：2026-11-06  
**复核依据**：D-25 裁决书（`lead/d25_ruling_20261106/RULING_D25.md`）第 3 节 order 第 4 步、任务书（`lead/b2b_candidate_20261106/TASK.md`）第 5 节独立复核要求  
**被复核对象**：
- 候选副本：`lead/b2b_candidate_20261106/qc151_trip.candidate.py`
- 候选差异：`lead/b2b_candidate_20261106/CANDIDATE.diff`
- 隔离测试：`lead/b2b_candidate_20261106/tests/test_candidate.py`
- 测试输出：`lead/b2b_candidate_20261106/tests/_test_out.txt`
- 测试报告：`lead/b2b_candidate_20261106/TESTS_REPORT.md`
- 门禁脚本：`lead/b2b_candidate_20261106/check_candidate.py`

---

## 0 机器可读指标（ReviewVerdict）

```yaml
subjectSha256: 9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc
subjectBytes: 420292
checkedEveryRow: true
motherUnchanged: true
nineHunksPresent: true
noImportMother: true
threeStatesDistinct: true
testsActuallyRun: true
issues: []
```

---

## 1 专项 A：母本未被改核验（零篡改、零漂移）

### 1.1 实算命令
在 Python 隔离模式 `-I` 下使用 `hashlib.sha256` 实算母本与候选文件指标：
```bash
python -I -c "
import hashlib, os
mother_path = r'D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py'
cand_path = r'D:\Project\ra2-campaign-forge\lead\b2b_candidate_20261106\qc151_trip.candidate.py'
for label, p in [('mother', mother_path), ('candidate', cand_path)]:
    data = open(p, 'rb').read()
    print(f'{label}: {len(data)} bytes, sha256={hashlib.sha256(data).hexdigest()}')
"
```

### 1.2 实算输出
```text
mother: 399508 bytes, sha256=517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636
candidate: 420292 bytes, sha256=9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc
```

### 1.3 对账结论
- 目标母本基准：`399508` B / `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636`；
- 实测母本数值：`399508` B / `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636`；
- 候选副本数值：`420292` B / `9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc`；
- 判定：**母本一个字节未动，零修改零漂移，`motherUnchanged: true`**。

---

## 2 专项 B：九处改动全量在场核验（H01–H09 逐条核对）

按任务书 §3 与设计稿 `lead/b2b_design_20261106/B2B_DESIGN.md` §4 / §7 对照表，逐条在候选全文 `qc151_trip.candidate.py` 中定位，核对 `+` 侧改动内容与设计完全一致：

| 编号 | 设计 Hunk 头 | 候选行号定位 | 关键改动内容与设计一致性核验 | 判定 |
|:---|:---|:---:|:---|:---:|
| **H1** | `@@ -212,6 +212,21 @@` | `qc151_trip.candidate.py:212-232` | 顶层注入 `FRESHNESS_GROUP = "FRESHNESS"` 等 5 个常量及合法取值白名单集合，单一真源定义完全与设计一致 | **PASS** |
| **H2** | `@@ -4458,6 +4473,10 @@` | `qc151_trip.candidate.py:4473-4482` | `backup_carrier` 成功记录 `rec.add("RESTORE", f"backup_mtime_pre:{name}", ...)`，同时保持 `bak[name]` 三键契约（`path`/`size`/`sha256`）不变 | **PASS** |
| **H3** | `@@ -4558,8 +4577,131 @@` | `qc151_trip.candidate.py:4577-4707` | 前置定义 `make_pre_freshness_snapshot(except_path: Path) -> dict` 与 `classify_except_freshness`；重构 `copy_post_except_evidence` 签名新增形参 `pre_freshness_snapshot: dict \| None = None` | **PASS** |
| **H4** | `@@ -4572,20 +4714,105 @@` | `qc151_trip.candidate.py:4714-4818` | 重写 `copy_post_except_evidence` 函数体：正常/异常/缺失三出口均落盘 7 个 `FRESHNESS` 字段 + 12 键 `info`；异常时记录 3 项 `ERROR` 留痕后 `raise`；`carrier_post_state.json` 覆盖 5 载体件 | **PASS** |
| **H5** | `@@ -5906,7 +6133,8 @@` | `qc151_trip.candidate.py:6133-6140` | `finalize_trip` 签名追加 `pre_freshness_snapshot: dict \| None = None` 末位形参 | **PASS** |
| **H6** | `@@ -5936,7 +6164,8 @@` | `qc151_trip.candidate.py:6164-6171` | `:6167` 调用点显式以关键字传参 `pre_freshness_snapshot=pre_freshness_snapshot`（彻底治愈上一版 B2 作用域断裂问题） | **PASS** |
| **H7** | `@@ -6294,6 +6523,9 @@` | `qc151_trip.candidate.py:6523-6531` | `main()` 内在 `try` 之前预初始化 `_pre_freshness_snapshot: dict \| None = None`，防早退路径未定义风险 | **PASS** |
| **H8** | `@@ -6386,6 +6618,15 @@` | `qc151_trip.candidate.py:6618-6632` | 备份完成后（`:6617`）、游戏进程启动前调用 `make_pre_freshness_snapshot(except_cur)` 并记录 `FRESHNESS.captured_at_iso_pre` | **PASS** |
| **H9** | `@@ -7122,7 +7363,8 @@` | `qc151_trip.candidate.py:7363-7370` | `finally` 块内调用 `finalize_trip` 显式传入 `pre_freshness_snapshot=_pre_freshness_snapshot` | **PASS** |

另外，对 `B2B_DESIGN.md` §4 的 9 个 diff 代码块与 `CANDIDATE.diff` 进行逐 hunk 比对，9 个 hunk 差异比较行数全部一致，`difflib` 逐行对比 0 差异。  
判定：**9 处改动全量在场且与设计严格一致，`nineHunksPresent: true`**。

---

## 3 专项 C：无 import 母本核验（零依赖、零顶层副作用）

### 3.1 扫描范围与方法
对 `lead/b2b_candidate_20261106/tests/` 下所有 Python 文件（实际包含 `tests/test_candidate.py`）进行两轮独立扫描：
1. **正则表达式扫描**：`^\s*(import\s+qc151_trip|from\s+qc151_trip\s+import)`；
2. **AST 语法树节点遍历**：检查所有 `ast.Import` 与 `ast.ImportFrom` 节点中的模块名称。

### 3.2 实测命令与输出
```bash
python -I -X utf8 -c '
import os, glob, re, ast
tests_dir = r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_20261106\tests"
py_files = glob.glob(os.path.join(tests_dir, "**/*.py"), recursive=True)
bad_imports = []
for pf in py_files:
    text = open(pf, "r", encoding="utf-8").read()
    m1 = re.findall(r"^\s*(import\s+qc151_trip.*)", text, re.M)
    m2 = re.findall(r"^\s*(from\s+qc151_trip\s+import.*)", text, re.M)
    if m1 or m2: bad_imports.append((pf, "regex", m1 + m2))
    tree = ast.parse(text, filename=pf)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if "qc151_trip" in a.name: bad_imports.append((pf, "ast.Import", a.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module and "qc151_trip" in node.module:
                bad_imports.append((pf, "ast.ImportFrom", node.module))
print(f"Bad imports found: {len(bad_imports)}")
'
```
**输出**：
```text
Bad imports found: 0
```

### 3.3 测试加载方式复核
复核 `lead/b2b_candidate_20261106/tests/test_candidate.py:40-57`：
- 使用 `importlib.util.spec_from_file_location("qc151_candidate_mod", str(candidate_path))` 仅加载候选副本；
- 使用 `unittest.mock.patch("ctypes.windll.user32.SetProcessDPIAware", return_value=1)` 拦截了 Windows GUI DPI 副作用；
- 未 import 母本，未执行 `eval`/`exec`；
- 判定：**完全不存在 import 母本行为，`noImportMother: true`**。

---

## 4 专项 D：未知快照三态可分与置信核验

### 4.1 三态可分性实测复核
针对输入 `None`、`{}`、`{"exists": False}` 三种形态，在候选代码中进行实测：
1. **落盘 info 字段隔离**（`qc151_trip.candidate.py:4810-4812`）：
   ```python
   info["pre_freshness_snapshot"] = (
       pre_freshness_snapshot
       if isinstance(pre_freshness_snapshot, dict) else None)
   ```
   - 输入 `None` 时，`info["pre_freshness_snapshot"]` 为 `None`；
   - 输入 `{}` 时，`info["pre_freshness_snapshot"]` 为 `{}`；
   - 输入 `{"exists": False}` 时，`info["pre_freshness_snapshot"]` 为 `{"exists": False}`；
   - 三者原样留痕，互不相等（`None != {} != {"exists": False}`），在 `test_candidate.py:270-299`（`test_c1`）中实测断言全量通过。
2. **状态判定与置信度约束**（`qc151_trip.candidate.py:4634-4651`）：
   - `state` 是唯一判定口，`exists` 绝不参与反推状态；
   - `None`、`{}`、`{"exists": False}`（缺失 `state` 字段）在入口处均被归一为 `st = "unknown"`；
   - 分类器判定结果：`verdict = "unknown"`，`confidence = "none"`，`is_new = None`，`usable_as_crash_evidence = False`；
   - 置信度为 `none`，**绝对不输出 `high`**；
3. **防伪折叠机制**（`qc151_trip.candidate.py:4648-4660` 与 `test_candidate.py:326-345` `test_c3`）：
   - 伪快照 `{"exists": False}` 缺少 `state` 字段，判定为 `unknown/none`；
   - 真实无件快照必须显式为 `{"state": "absent_confirmed", "exists": False}`，判定为 `new_first_appearance/high`；
   - 二者输出严格不同，彻底杜绝了上一版 B2 把未知快照折叠为 `absent_confirmed` 的设计缺陷。

判定：**三态严格可分且置信非 high，`threeStatesDistinct: true`**。

---

## 5 专项 E：测试真跑与输出一致性核验

### 5.1 亲自重跑命令（隔离模式 + UTF-8）
```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/b2b_candidate_20261106/tests/test_candidate.py"
```

### 5.2 独立实跑输出截取
```text
[2026-11-06T18:17:34.559697] 开始执行候选合成隔离测试套件...
候选路径: D:\Project\ra2-campaign-forge\lead\b2b_candidate_20261106\qc151_trip.candidate.py
用例总数: 29
----------------------------------------------------------------------
test_a1_ast_verify_five_early_exits_pre_freshness_is_none ... ok
test_a2_finalize_trip_runs_safely_when_snapshot_is_none_no_carrier_file ... ok
test_a3_finalize_trip_runs_safely_when_snapshot_is_none_with_carrier_file ... ok
test_a4_copy_post_except_evidence_early_exits_all_five_paths_simulation ... ok
test_b1_make_pre_snapshot_exception_handled_returns_state_error ... ok
test_b2_classify_pre_snapshot_error_gives_independent_error_exit ... ok
test_b3_copy_post_evidence_with_pre_snapshot_error_emits_f_and_info ... ok
test_b4_post_copy_exception_records_error_and_reraises ... ok
test_c1_three_inputs_distinct_in_copy_post_info ... ok
test_c2_unknown_confidence_is_never_high ... ok
test_c3_missing_without_state_differs_from_absent_confirmed ... ok
test_d1_seven_freshness_fields_exact_match_and_values ... ok
test_d2_twelve_info_keys_exact_match_and_disk_persistence ... ok
test_d3_seven_freshness_fields_persisted_in_early_return_when_src_missing ... ok
test_e1_ast_verify_copy_post_call_in_finalize_trip ... ok
test_e2_ast_verify_finalize_trip_signature_has_pre_freshness_snapshot ... ok
test_e3_ast_verify_main_pre_freshness_snapshot_lifecycle ... ok
test_f01_matrix_absent_confirmed ... ok
test_f02_matrix_absent_both ... ok
test_f03_matrix_leftover_unchanged_mtime_match ... ok
test_f04_matrix_leftover_unchanged_mtime_missing ... ok
test_f05_matrix_new_write ... ok
test_f06_matrix_rewritten_same_content_mtime_greater ... ok
test_f07_matrix_rewritten_same_content_mtime_rollback ... ok
test_f08_matrix_missing_sha_pre ... ok
test_f09_matrix_missing_sha_post ... ok
test_f10_matrix_vanished ... ok
test_f11_matrix_post_read_error ... ok
test_f12_usable_as_crash_evidence_is_always_false ... ok

----------------------------------------------------------------------
Ran 29 tests in 0.914s

OK
----------------------------------------------------------------------
PASS=29 FAIL=0
EXIT=0
```

### 5.3 对账结论
- 29 个用例全部运行通过，0 失败、0 错误；
- 与 `lead/b2b_candidate_20261106/tests/_test_out.txt` 中的用例清单、顺序、测试结果、末 5 行 `PASS=29 FAIL=0`、`EXIT=0` 完全吻合；
- 同时独立重跑 W11 测试 `python -I -X utf8 "D:\Project\ra2-campaign-forge\lead\re_line_20261105\W11_EXCEPT_FRESHNESS\candidate\test_except_freshness.py"`，输出 `PASS=14 FAIL=0 EXIT=0`；
- 判定：**测试真跑过，`testsActuallyRun: true`**。

---

## 6 专项 F：未覆盖项诚实性核验

复核 `lead/b2b_candidate_20261106/TESTS_REPORT.md` 第 3 节「未覆盖项清单及风险评估」：
- 报告列出了 6 项未覆盖测试：
  1. 真机游戏进程启动与真实引擎退出（受限于铁律 1 零真机）；
  2. 真实动态探针注入与崩溃转储生成（受限于铁律 2 零采样注入）；
  3. 操作系统级 GUI 窗口枚举与 DPI 感知实测（测试环境为 Headless 且隔离副作用）；
  4. 母本 `qc151_trip.py` 的执行或直接 import（受限于铁律 3/4）；
  5. 真实 CLI 命令行黑盒调用与顶层进程退出码冒烟（为避免直接拉起载体）；
  6. 真实文件系统高精时间戳并发与时钟回拨极端实测（临时目录隔离沙箱约束）；
- 逐项核对：报告未对上述任何一项作虚假覆盖声明，所有声明为「未覆盖」的项目均如实详细说明了「哪些没测」、「为什么没测（铁律约束）」以及「会带来什么具体技术风险」；
- 判定：**未覆盖报告诚实守信，无虚假瞒报，`checkedEveryRow: true`**。

---

## 7 确定性门禁脚本（`check_candidate.py`）实跑结果

以命令 `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/b2b_candidate_20261106/check_candidate.py"` 亲自重跑自检脚本：

```text
======================================================================
B2b 候选确定性门禁自检
======================================================================
PASS [1]: 候选副本存在，字节数 = 420292 B (> 399508 B)
PASS [2]: 候选副本 ast.parse 语法解析成功 (0 语法错误)
PASS [3]: CANDIDATE.diff 存在且非空 (18692 B)
PASS [4]: 母本 SHA256 与字节数 100% 保持原样 (零漂移)
PASS [5]: tests/ 下 1 个测试脚本经正则扫描，零处 import 母本
PASS [6]: _test_out.txt 末 5 行包含 PASS= 与 FAIL=0
PASS [7]: TESTS_REPORT.md 包含「命令」「退出码」「未覆盖」三词
PASS [8]: 候选副本 9 处改动锚点全部准确定位
PASS [9]: 复核回件 5 个必填布尔键值核对完全一致
======================================================================
ALL 9 GATES PASSED! EXIT=0
======================================================================
```

---

## 8 复核结论与 Issues 清单

### 8.1 六项专项检查全景汇总

| 专项检查项 | 判定要求 | 本次复核实测情况 | 结论 |
|:---|:---|:---|:---:|
| **专项 A** | 母本未被改 | 实测 `399508` B / `517889c6…5ba636`，零修改零漂移 | **PASS** (`motherUnchanged: true`) |
| **专项 B** | 九处改动都在 | H1..H9 逐行定位且与设计稿 Section 4 逐字一致 | **PASS** (`nineHunksPresent: true`) |
| **专项 C** | 无 import 母本 | 正则与 AST 双重扫描 0 匹配，独立 mock 隔离加载 | **PASS** (`noImportMother: true`) |
| **专项 D** | 三态可分且置信非 high | `None`/`{}`/`{"exists":False}` 原样保留，未采集置信恒为 `none` | **PASS** (`threeStatesDistinct: true`) |
| **专项 E** | 测试真跑 | 亲自执行 29 测，`PASS=29 FAIL=0`，耗时 `0.914s`，`EXIT=0` | **PASS** (`testsActuallyRun: true`) |
| **专项 F** | 未覆盖诚实 | 6 项未覆盖如实披露风险与铁律原因，无虚报 | **PASS** (`checkedEveryRow: true`) |

### 8.2 遗留问题（Issues）
```json
[]
```
经独立逐行复核与实跑重验，本候选副本质量扎实，六项专项检查全部一次性无瑕疵通过，零遗留技术问题。
