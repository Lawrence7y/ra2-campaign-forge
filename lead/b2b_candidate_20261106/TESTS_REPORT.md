# TESTS_REPORT · B2b 候选副本隔离合成测试与基线重跑报告

**报告性质**：候选副本进门判定报告（供评审方判断「本候选副本值不值得进下一道门」）  
**执行日期**：2026-11-06  
**候选文件**：`lead/b2b_candidate_20261106/qc151_trip.candidate.py` (420,292 B, SHA256: `9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc`)  
**母本基线**：`out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` (399,508 B, SHA256: `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636`, 零修改零漂移)  
**设计来源**：`lead/b2b_design_20261106/B2B_DESIGN.md` (66,735 B, SHA256: `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf`)  
**测试套件**：`lead/b2b_candidate_20261106/tests/test_candidate.py`  
**核心结论**：候选自身 29 测全量实跑通过（`PASS=29 FAIL=0`，退出码 `0`）；上游 W11 基线 14 测重跑通过（`PASS=14 FAIL=0`，退出码 `0`）。无假通过、无降级断言、无未捕获异常。

---

## ① 候选自身的测试

### 1.1 精确命令与执行环境

- **直接控制台执行命令**：
  ```bash
  python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/b2b_candidate_20261106/tests/test_candidate.py"
  ```
- **重定向日志落盘命令**：
  ```bash
  python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/b2b_candidate_20261106/tests/test_candidate.py" > "D:/Project/ra2-campaign-forge/lead/b2b_candidate_20261106/tests/_test_out.txt" 2>&1
  ```
- **解释器与环境参数**：Python 3.12（强制使用隔离模式 `-I` 屏蔽 `sys.path` 与环境变量干扰，强制 `-X utf8` 杜绝 Windows 编码转换乱码，全绝对路径引用）；
- **进程退出码**：`0`；
- **用例统计与耗时**：共 29 个测试用例，**`PASS=29 FAIL=0`**，运行耗时 **`1.024s`**。

### 1.2 真实运行输出（引用自 `lead/b2b_candidate_20261106/tests/_test_out.txt:1-71` 全文）

```text
[2026-11-06T18:05:48.707527] 开始执行候选合成隔离测试套件...
候选路径: D:\Project\ra2-campaign-forge\lead\b2b_candidate_20261106\qc151_trip.candidate.py
用例总数: 29
----------------------------------------------------------------------
test_a1_ast_verify_five_early_exits_pre_freshness_is_none (__main__.TestCategoryA_EarlyExits.test_a1_ast_verify_five_early_exits_pre_freshness_is_none)
A1: AST 静态验证 main() 中 5 个早退路径均在快照采集之前，快照保持 None。 ... ok
test_a2_finalize_trip_runs_safely_when_snapshot_is_none_no_carrier_file (__main__.TestCategoryA_EarlyExits.test_a2_finalize_trip_runs_safely_when_snapshot_is_none_no_carrier_file)
A2: 早退场景下（快照为 None 且载体无 except.txt），finalize_trip 不崩溃，落盘 unknown/none。 ... ok
test_a3_finalize_trip_runs_safely_when_snapshot_is_none_with_carrier_file (__main__.TestCategoryA_EarlyExits.test_a3_finalize_trip_runs_safely_when_snapshot_is_none_with_carrier_file)
A3: 早退场景下（快照为 None 但载体有残留 except.txt），finalize_trip 不崩溃，落盘 unknown/none。 ... ok
test_a4_copy_post_except_evidence_early_exits_all_five_paths_simulation (__main__.TestCategoryA_EarlyExits.test_a4_copy_post_except_evidence_early_exits_all_five_paths_simulation)
A4: 模拟五个早退路径直接调用 copy_post_except_evidence，均输出 unknown/none。 ... ok
test_b1_make_pre_snapshot_exception_handled_returns_state_error (__main__.TestCategoryB_Exceptions.test_b1_make_pre_snapshot_exception_handled_returns_state_error)
B1: 快照采集阶段抛异常（如目标是目录）时被捕获，返回 state=error 与 traceback。 ... ok
test_b2_classify_pre_snapshot_error_gives_independent_error_exit (__main__.TestCategoryB_Exceptions.test_b2_classify_pre_snapshot_error_gives_independent_error_exit)
B2: classify_except_freshness 收到 state=error 快照时进入独立 error_pre_snapshot 出口。 ... ok
test_b3_copy_post_evidence_with_pre_snapshot_error_emits_f_and_info (__main__.TestCategoryB_Exceptions.test_b3_copy_post_evidence_with_pre_snapshot_error_emits_f_and_info)
B3: copy_post_except_evidence 收到 state=error 快照时落盘 error_pre_snapshot 且置信为 none。 ... ok
test_b4_post_copy_exception_records_error_and_reraises (__main__.TestCategoryB_Exceptions.test_b4_post_copy_exception_records_error_and_reraises)
B4: 跑后复制写操作抛异常时，必须记录 3 项 ERROR 留痕、落盘 post_read_error 并原样重抛。 ... ok
test_c1_three_inputs_distinct_in_copy_post_info (__main__.TestCategoryC_UnknownSnapshotStates.test_c1_three_inputs_distinct_in_copy_post_info)
C1: None / {} / {'exists': False} 三种输入在 copy_post_except_evidence 的 info 中可分。 ... ok
test_c2_unknown_confidence_is_never_high (__main__.TestCategoryC_UnknownSnapshotStates.test_c2_unknown_confidence_is_never_high)
C2: 所有未采集/缺失快照形态（None, {}, {'exists': False}, unknown, 脏值）置信绝不是 high。 ... ok
test_c3_missing_without_state_differs_from_absent_confirmed (__main__.TestCategoryC_UnknownSnapshotStates.test_c3_missing_without_state_differs_from_absent_confirmed)
C3: 伪快照 {'exists': False} 绝不等于确认无件 absent_confirmed。 ... ok
test_d1_seven_freshness_fields_exact_match_and_values (__main__.TestCategoryD_FieldOutputs.test_d1_seven_freshness_fields_exact_match_and_values)
D1: 7 个 FRESHNESS 字段逐个核对，无漏键、无多键，取值约束正确。 ... ok
test_d2_twelve_info_keys_exact_match_and_disk_persistence (__main__.TestCategoryD_FieldOutputs.test_d2_twelve_info_keys_exact_match_and_disk_persistence)
D2: 12 键 info 全部落盘，逐键核对，且 carrier_post_state.json 正确写入。 ... ok
test_d3_seven_freshness_fields_persisted_in_early_return_when_src_missing (__main__.TestCategoryD_FieldOutputs.test_d3_seven_freshness_fields_persisted_in_early_return_when_src_missing)
D3: 载体无 except.txt 时（早退分支），同样全量落盘 7 个 FRESHNESS 字段。 ... ok
test_e1_ast_verify_copy_post_call_in_finalize_trip (__main__.TestCategoryE_Wiring.test_e1_ast_verify_copy_post_call_in_finalize_trip)
E1: :5939 / :6167 调用点确实传了 pre_freshness_snapshot。 ... ok
test_e2_ast_verify_finalize_trip_signature_has_pre_freshness_snapshot (__main__.TestCategoryE_Wiring.test_e2_ast_verify_finalize_trip_signature_has_pre_freshness_snapshot)
E2: finalize_trip 签名末尾必须包含 pre_freshness_snapshot 参数。 ... ok
test_e3_ast_verify_main_pre_freshness_snapshot_lifecycle (__main__.TestCategoryE_Wiring.test_e3_ast_verify_main_pre_freshness_snapshot_lifecycle)
E3: main() 内 _pre_freshness_snapshot 的完整生命周期：预初始化 -> 采集 -> 传入 finalize_trip。 ... ok
test_f01_matrix_absent_confirmed (__main__.TestCategoryF_StateMatrix.test_f01_matrix_absent_confirmed)
F01: absent_confirmed 跑前确认无件 + 跑后在地 ⇒ new_first_appearance / high / is_new=True。 ... ok
test_f02_matrix_absent_both (__main__.TestCategoryF_StateMatrix.test_f02_matrix_absent_both)
F02: absent_both 跑前确认无件 + 跑后无件 ⇒ absent_both / low / is_new=False。 ... ok
test_f03_matrix_leftover_unchanged_mtime_match (__main__.TestCategoryF_StateMatrix.test_f03_matrix_leftover_unchanged_mtime_match)
F03: leftover_unchanged 跑前在 + 跑后在 + sha同 + mtime同 ⇒ leftover_unchanged / high / is_new=False。 ... ok
test_f04_matrix_leftover_unchanged_mtime_missing (__main__.TestCategoryF_StateMatrix.test_f04_matrix_leftover_unchanged_mtime_missing)
F04: leftover_unchanged 跑前在 + 跑后在 + sha同 + mtime缺失 ⇒ leftover_unchanged / medium / is_new=False。 ... ok
test_f05_matrix_new_write (__main__.TestCategoryF_StateMatrix.test_f05_matrix_new_write)
F05: new_write 跑前在 + 跑后在 + sha不同 ⇒ new_write / high / is_new=True。 ... ok
test_f06_matrix_rewritten_same_content_mtime_greater (__main__.TestCategoryF_StateMatrix.test_f06_matrix_rewritten_same_content_mtime_greater)
F06: rewritten_same_content 跑前在 + 跑后在 + sha同 + mtime变大 ⇒ rewritten_same_content / medium / is_new=True。 ... ok
test_f07_matrix_rewritten_same_content_mtime_rollback (__main__.TestCategoryF_StateMatrix.test_f07_matrix_rewritten_same_content_mtime_rollback)
F07: rewritten_same_content 跑前在 + 跑后在 + sha同 + mtime回拨 ⇒ rewritten_same_content / low / is_new=True。 ... ok
test_f08_matrix_missing_sha_pre (__main__.TestCategoryF_StateMatrix.test_f08_matrix_missing_sha_pre)
F08: missing_sha 跑前在 + 跑后在 + 缺 pre.sha256 ⇒ error_pre_snapshot / none / is_new=None。 ... ok
test_f09_matrix_missing_sha_post (__main__.TestCategoryF_StateMatrix.test_f09_matrix_missing_sha_post)
F09: missing_sha 跑前在 + 跑后在 + 缺 post.sha256 ⇒ post_read_error / none / is_new=None。 ... ok
test_f10_matrix_vanished (__main__.TestCategoryF_StateMatrix.test_f10_matrix_vanished)
F10: vanished 跑前在 + 跑后无件 ⇒ vanished / none / is_new=None。 ... ok
test_f11_matrix_post_read_error (__main__.TestCategoryF_StateMatrix.test_f11_matrix_post_read_error)
F11: post_read_error 跑后 read_error 非空 ⇒ post_read_error / none / is_new=None。 ... ok
test_f12_usable_as_crash_evidence_is_always_false (__main__.TestCategoryF_StateMatrix.test_f12_usable_as_crash_evidence_is_always_false)
F12: 铁纪律 N9/N10：所有状态输出的 usable_as_crash_evidence 恒为 False。 ... ok

----------------------------------------------------------------------
Ran 29 tests in 1.024s

OK
----------------------------------------------------------------------
PASS=29 FAIL=0
EXIT=0
```

### 1.3 隔离加载机制与安全性验证

为满足铁纪律「不启动游戏、不 import 母本、无全局副作用」：
1. **独立模块加载规范**：采用 `importlib.util.spec_from_file_location` 将候选副本加载为独立命名空间模块 `'qc151_candidate_mod'`（`tests/test_candidate.py:40-57`），完全禁止使用 `eval()` 与 `exec()`；
2. **顶层副作用拦截**：候选文件第 182 行（`qc151_trip.candidate.py:182`）包含 `ctypes.windll.user32.SetProcessDPIAware()`。测试套件在加载期间使用 `unittest.mock.patch("ctypes.windll.user32.SetProcessDPIAware", return_value=1)` 拦截了该调用，彻底防止测试宿主进程的全局 DPI 感知状态被篡改；
3. **主入口防护**：候选末尾为 `if __name__ == '__main__': sys.exit(_entry())`，由于加载模块名为 `'qc151_candidate_mod'`，主程序入口绝不触发；
4. **母本零污染**：全量测试代码正则扫描 `^\s*(import\s+qc151_trip|from\s+qc151_trip\s+import)` 匹配数严格为 0。

### 1.4 六大类 29 项测试对账与定位

| 类别与方法 | 源码行号 (`test_candidate.py`) | 覆盖语义与测试设计 | 运行判定 |
|:---|:---:|:---|:---:|
| **A 类：早退路径** | | | |
| `test_a1` | `:82` | AST 静态分析验证 `main()` 内 5 个早退点（`:6573`、`:6583`、`:6593`、`:6606`、`:6609`）均在 H8 快照采集（`:6623`）之前，快照恒为 `None` | **PASS** |
| `test_a2` | `:145` | 快照为 `None` 且载体无 `except.txt` 时，`finalize_trip` 安全执行，落盘 `verdict="unknown"` 与 `confidence="none"` | **PASS** |
| `test_a3` | `:161` | 快照为 `None` 且载体有残留旧件时，`finalize_trip` 安全执行，落盘 `verdict="unknown"` 与 `confidence="none"` | **PASS** |
| `test_a4` | `:178` | 模拟 5 个早退退出码直接调用 `copy_post_except_evidence`，输出恒为 `unknown/none` | **PASS** |
| **B 类：异常出口** | | | |
| `test_b1` | `:199` | 采集快照抛异常（如目标为目录）时被内部捕获，返回 `state="error"` 与 traceback 记录 | **PASS** |
| `test_b2` | `:212` | 分类器收到 `state="error"` 快照时进入独立出口 `error_pre_snapshot`，置信度恒为 `none` | **PASS** |
| `test_b3` | `:227` | `copy_post_except_evidence` 收到 `state="error"` 时落盘 `error_pre_snapshot/none`，不可作崩溃证据 | **PASS** |
| `test_b4` | `:244` | 跑后文件复制写异常时记录 3 项 ERROR 留痕、落盘 `post_read_error` 并原样重抛（不吞异常） | **PASS** |
| **C 类：未知快照三态** | | | |
| `test_c1` | `:270` | `None`、`{}`、`{"exists": False}` 三种输入在落盘的 `info["pre_freshness_snapshot"]` 中原样保留且严格可分 | **PASS** |
| `test_c2` | `:300` | 所有未采集与脏值形态在分类器中置信度绝不为 `high`（恒为 `none`） | **PASS** |
| `test_c3` | `:326` | 伪快照 `{"exists": False}` 判定为 `unknown/none`，绝不折叠为 `absent_confirmed` | **PASS** |
| **D 类：字段输出核验** | | | |
| `test_d1` | `:376` | 7 个 `FRESHNESS` 字段全量核对无多无漏，取值在白名单内，`usable_as_crash_evidence` 恒为 `False` | **PASS** |
| `test_d2` | `:397` | 12 键 `info` 字典全量落盘核对；`carrier_post_state.json` 覆盖 5 个载体件并写盘 | **PASS** |
| `test_d3` | `:418` | 源文件缺失早退分支（`:4761-4763`）同样全量落盘 7 个 `FRESHNESS` 字段 | **PASS** |
| **E 类：接线 AST 静态核验** | | | |
| `test_e1` | `:433` | AST 静态核验 `:6167` 调用点显式传入 `pre_freshness_snapshot=pre_freshness_snapshot`，闭合上一版 B2 缺陷 | **PASS** |
| `test_e2` | `:456` | AST 静态核验 `finalize_trip` 签名（`:6137`）形参末尾包含 `pre_freshness_snapshot` | **PASS** |
| `test_e3` | `:472` | AST 静态核验 `main()` 内预初始化（`:6528`）-> 采集（`:6623`）-> 传递（`:7367`）生命周期闭合 | **PASS** |
| **F 类：状态矩阵覆盖** | | | |
| `test_f01` | `:501` | `absent_confirmed` 跑前确认无件 + 跑后在地 ⇒ `new_first_appearance / high / is_new=True` | **PASS** |
| `test_f02` | `:511` | `absent_both` 跑前确认无件 + 跑后无件 ⇒ `absent_both / low / is_new=False` | **PASS** |
| `test_f03` | `:521` | `leftover_unchanged` 跑前在 + 跑后在 + sha同 + mtime同 ⇒ `leftover_unchanged / high / is_new=False` | **PASS** |
| `test_f04` | `:531` | `leftover_unchanged` 跑前在 + 跑后在 + sha同 + mtime缺 ⇒ `leftover_unchanged / medium / is_new=False` | **PASS** |
| `test_f05` | `:541` | `new_write` 跑前在 + 跑后在 + sha不同 ⇒ `new_write / high / is_new=True` | **PASS** |
| `test_f06` | `:551` | `rewritten_same_content` 跑前在 + 跑后在 + sha同 + mtime推进 ⇒ `rewritten_same_content / medium / is_new=True` | **PASS** |
| `test_f07` | `:561` | `rewritten_same_content` 跑前在 + 跑后在 + sha同 + mtime回拨 ⇒ `rewritten_same_content / low / is_new=True` | **PASS** |
| `test_f08` | `:571` | `missing_sha_pre` 跑前在 + 跑后在 + 缺 pre.sha ⇒ `error_pre_snapshot / none / is_new=None` | **PASS** |
| `test_f09` | `:581` | `missing_sha_post` 跑前在 + 跑后在 + 缺 post.sha ⇒ `post_read_error / none / is_new=None` | **PASS** |
| `test_f10` | `:591` | `vanished` 跑前在 + 跑后无件 ⇒ `vanished / none / is_new=None` | **PASS** |
| `test_f11` | `:601` | `post_read_error` 跑后 read_error 非空 ⇒ `post_read_error / none / is_new=None` | **PASS** |
| `test_f12` | `:611` | 铁纪律 N9/N10：所有 12 种矩阵分支中输出的 `usable_as_crash_evidence` 恒为 `False` | **PASS** |

---

## ② W11 既有测试重跑（上游基线验证与边界说明）

### 2.1 上游基线文件指纹实算

在本次测试执行前后，使用 Python `hashlib`（隔离模式 `-I`）实算 W11 上游源文件指标，保持完全一致：

| 文件绝对路径 | 文件字节数 (Bytes) | SHA256 校验和 |
|:---|:---:|:---|
| `D:\Project\ra2-campaign-forge\lead\re_line_20261105\W11_EXCEPT_FRESHNESS\candidate\except_freshness.py` | 13,190 | `e6685167f5d26030f9a2e28df06ee2fbda23c7e91687aa209f6769ac3450480b` |
| `D:\Project\ra2-campaign-forge\lead\re_line_20261105\W11_EXCEPT_FRESHNESS\candidate\test_except_freshness.py` | 10,524 | `d305b776a95e93d8c4f2d2f51b380f933405b71ee285742007824e10448bf3b4` |

### 2.2 精确命令与运行结果

- **精确执行命令**：
  ```bash
  python -I -X utf8 "D:\Project\ra2-campaign-forge\lead\re_line_20261105\W11_EXCEPT_FRESHNESS\candidate\test_except_freshness.py" > "D:\Project\ra2-campaign-forge\lead\b2b_candidate_20261106\_w11_rerun_out.txt" 2>&1
  ```
- **进程退出码**：`0`；
- **用例统计与耗时**：共 14 个测试用例，**`PASS=14 FAIL=0`**，运行耗时 **`0.290s`**；
- **输出保存文件**：`lead/b2b_candidate_20261106/_w11_rerun_out.txt`（35 行，2,734 字节，SHA256: `0aa4e06f0a7ac5775f6d5b4ca738ca77569e88b65b83fbb28ba6ebac08f93f73`）。

### 2.3 真实运行输出（引用自 `lead/b2b_candidate_20261106/_w11_rerun_out.txt:1-35` 全文）

```text
test_01_branch1_source_missing (__main__.FreshnessTest.test_01_branch1_source_missing)
分支1 · 源件缺失：跑前无、跑后无 ⇒ absent_both / is_new=False。 ... ok
test_02_branch2_leftover_unchanged (__main__.FreshnessTest.test_02_branch2_leftover_unchanged)
分支2 · 原样遗留：跑前有、跑后内容与 mtime 均未变 ⇒ not_new。 ... ok
test_03_branch3_content_changed (__main__.FreshnessTest.test_03_branch3_content_changed)
分支3 · 内容变化：跑前有、跑后内容变了 ⇒ new_write / is_new=True。 ... ok
test_04_branch4_copy_failure_write (__main__.FreshnessTest.test_04_branch4_copy_failure_write)
分支4 · 复制失败（write_bytes 抛异常）⇒ error 显式留痕，不是静默。 ... ok
test_04b_branch4_copy_failure_read (__main__.FreshnessTest.test_04b_branch4_copy_failure_read)
分支4b · 复制失败（read_bytes 抛异常：src 是目录）⇒ 同样显式留痕。 ... ok
test_04c_copy_src_missing (__main__.FreshnessTest.test_04c_copy_src_missing)
复制前置：源件缺失 ⇒ 显式 src_missing（harness :4575-4578 返回 None 的对应位）。 ... ok
test_05_post_read_error (__main__.FreshnessTest.test_05_post_read_error)
跑后件读失败（classify 路径）⇒ post_read_error 显式留痕。 ... ok
test_06_rewritten_same_content (__main__.FreshnessTest.test_06_rewritten_same_content)
T2 盲区补测 · 同内容重写：sha 同 mtime 变 ⇒ rewritten_same_content。 ... ok
test_07_vanished (__main__.FreshnessTest.test_07_vanished)
跑前在、跑后失 ⇒ vanished 旗标，is_new=None（F 不可判）。 ... ok
test_08_new_first_appearance_and_c_mode (__main__.FreshnessTest.test_08_new_first_appearance_and_c_mode)
跑前无、跑后有 ⇒ new_first_appearance；C 模式只改置信标注。 ... ok
test_09_clock_rollback_flag (__main__.FreshnessTest.test_09_clock_rollback_flag)
mtime 被拉回 + sha 同 ⇒ rewritten_same_content + suspect_clock_rollback。 ... ok
test_10_run_start_anchor_is_corroboration_only (__main__.FreshnessTest.test_10_run_start_anchor_is_corroboration_only)
★ 防回归：run_start 只是旁证——锚点再荒谬也不改变判定（否决 naive A）。 ... ok
test_11_pure_function_writes_nothing (__main__.FreshnessTest.test_11_pure_function_writes_nothing)
纯函数性：classify 全程不产生/修改任何文件（沙箱目录清单不变）。 ... ok
test_12_pre_snapshot_error_is_loud (__main__.FreshnessTest.test_12_pre_snapshot_error_is_loud)
跑前快照失败（src 变目录）⇒ classify 返回 error_pre_snapshot（不静默）。 ... ok

----------------------------------------------------------------------
Ran 14 tests in 0.290s

OK
PASS=14 FAIL=0
EXIT=0
```

### 2.4 ★ 核心边界声明：二者绝不能互相替代

读者在评估此候选时，必须明确区分两套测试的职责界限，绝不能将二者等同或互相替代：

1. **被测主体与代码范围截然不同**：
   - W11 测试直接针对的是上游原型模块 `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py`（单文件 13 KB），它是一个脱离宿主 harness 的独立纯算法实现；
   - 候选自身测试直接针对的是经过 9 个 Hunk 植入后的完整候选大文件 `lead/b2b_candidate_20261106/qc151_trip.candidate.py`（420 KB，7,533 行代码）。
2. **测试验证的核心维度完全不同**：
   - W11 测试重跑的目的是**「确认上游算法逻辑基准未发生腐化、纯函数状态机在当前 Python 环境下依旧有效」**，它完全不关心、也无法感知候选副本在宿主中的接线状态；
   - 候选自身测试验证的是**「9 个 Hunk 在真实大文件中的实际植入、作用域闭包、AST 接线、`main()` 函数生命周期全链路穿透、早退时安全不崩、以及异常时记录留痕」**；
3. **血淋淋的历史教训**：
   - 上一轮 B2 版本的失败正是因为上游算法（W11）通过，但植入宿主后 `:5939` 调用点漏传了 `pre_freshness_snapshot`，导致全链断裂；
   - **结论**：W11 测试通过**不能证明**候选可用；反之，若不重跑 W11 测试，也无法确认候选所依赖的纯函数设计基线是否发生外部环境漂移。**二者互相独立、互为前置与补充，不可混淆，更不可互相替代。**

---

## ③ 未覆盖项清单及风险评估

本报告绝不美化。读者要据此判断风险，因此必须如实逐条列出离线合成测试中**哪些测试没做**、**为什么没测**、以及**会带来什么具体技术风险**：

### 未覆盖项 1：真机游戏进程启动与真实引擎退出（`gamemd.exe` / `ra2loader.exe` / `YURI.exe`）
- **哪些没测**：未在真实 Windows 桌面环境中拉起游戏原生进程或其加载器；未经历真实 35 秒单趟运行周期；未实测游戏真实退出、卡死或非正常退出时操作系统级子进程树状态（`subprocess.Popen` / `process.poll()` / `win32process` 交互）。
- **为什么没测**：严格受限并遵守项目铁律第 1 条「零真机：不启动 gamemd.exe / ra2loader / YURI.exe，不 taskkill，不读活进程内存」。测试套件 100% 运行于离线合成沙箱。
- **会带来什么风险**：
  1. 真实环境下若游戏启动器存在未预料的深层子进程派生机制，可能导致父进程已退出而子进程仍在占用工作目录；
  2. 若游戏原生退出耗时严重超出预期，导致 `finalize_trip` 触发超时或并发冲突，离线合成测试无法预警此类操作系统进程调度层面的竞态问题。

### 未覆盖项 2：真实动态探针注入与崩溃转储生成（真实 `except.txt`）
- **哪些没测**：未通过注入非法内存访问或断点促使游戏原生引擎写入真实的 `except.txt`；未测试千万种内存异常场景下原生引擎输出文件的字符编码（如 ANSI / GBK / Shift-JIS）、文件末尾 EOF 标志以及磁盘刷新缓冲时滞。
- **为什么没测**：严格受限并遵守项目铁律第 2 条「零采样代码：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入」。
- **会带来什么风险**：
  1. 真实引擎崩溃时，若其文件写入流未执行 `fflush` 即被系统终止，可能导致 `except.txt` 瞬间落盘字节为 0，随后才被系统刷入，产生极短暂的读写时钟空窗；
  2. 真实崩溃可能在游戏以独占锁（Exclusive Lock）打开文件期间触发收尾，虽然测试了 `PermissionError` 分支，但未验证真实操作系统文件锁解除重试的最佳退避时间（Backoff）。

### 未覆盖项 3：操作系统级 GUI 窗口枚举与 DPI 感知实测
- **哪些没测**：未在多显示器或具有真实桌面交互的物理环境中调用 Win32 API `FindWindow`、`EnumWindows`、`GetWindowRect`，未真正执行候选副本第 182 行的 `SetProcessDPIAware()`。
- **为什么没测**：测试运行于无图形终端（Headless CLI）；铁纪律要求测试全过程保持绝对零副作用，在模块加载时通过 mock 将其存根化（`tests/test_candidate.py:51`）。
- **会带来什么风险**：若在特定 Windows 构建版本（如启用严格沙盒或第三方注入防御的系统）下，该 Win32 API 抛出意外的 `ctypes` 权限或环境异常，隔离测试无法在模块加载期感知。

### 未覆盖项 4：母本 `qc151_trip.py` 的执行或直接 import
- **哪些没测**：未直接执行母本中的代码路径，未直接 `import qc151_trip` 进行实时的运行时并排（side-by-side）比对。
- **为什么没测**：严格遵守项目铁律第 3 条「母本 qc151_trip.py 一个字节都不许改」与第 4 条「测试不得 import 母本、不得触发母本顶层逻辑、不得启动游戏」。
- **会带来什么风险**：虽然 AST 分析确认候选中的 9 个 Hunk 变量名与函数签名完全兼容，但由于未对母本未改动部分做全量动态回归跑测，若母本中隐藏着对某全局变量的未知动态依赖，可能存在未被察觉的隐蔽副作用。

### 未覆盖项 5：真实 CLI 命令行黑盒调用与顶层进程退出码冒烟
- **哪些没测**：未通过 Windows CMD / Git Bash 外层启动 `python qc151_trip.candidate.py --flags...` 进程来黑盒检验命令行参数解析器（`argparse`）以及全流程的 `sys.exit(exit_code)`。
- **为什么没测**：候选副本的 `__main__` 入口包含真实的载体启动与主流程调用，黑盒启动会尝试访问真实载体目录；为杜绝真机风险，测试均在单元测试框架中通过模块符号调用与 AST 解析完成。
- **会带来什么风险**：外层 CLI 参数输入格式错误或环境变量缺失时，`argparse` 的标准错误输出与外层 exit code 传递在端到端层面未做黑盒冒烟。

### 未覆盖项 6：真实文件系统高精时间戳并发与时钟回拨极端实测
- **哪些没测**：测试中使用的 `mtime` 是通过合成浮点数（如 `+10.0s`、`-10.0s`）模拟的，未在真实 NTFS 文件系统上进行毫秒/纳秒级并发读写测试，未在非 NTFS 文件系统（如 FAT32 / exFAT / SMB 网络共享）上测试 2 秒级时间戳截断。
- **为什么没测**：合成测试运行于本地临时目录（`tempfile.TemporaryDirectory`），目标是保证纳秒级隔离与快速确定性执行。
- **会带来什么风险**：若游戏载体被放置于 FAT32 分区，其修改时间精度仅为 2 秒，在极短时间内发生的文件重写同内容可能出现 `mtime_post == mtime_pre`，从而被分类器从 `rewritten_same_content` 判定为 `leftover_unchanged`。

---

## ④ 进门判定建议（供读者决策）

基于以上精确实测数据与边界分析，供读者判断「本候选副本值不值得进下一道门」：

1. **客观达标证据**：
   - 候选代码语法树解析成功（`ast.parse` 0 错误），420,292 B（只增不减），9 处改动锚点全部就位；
   - 候选自身 29 项隔离测试 100% 通过（`PASS=29 FAIL=0`，退出码 `0`），覆盖了早退、异常、未知快照三态、字段落盘、接线 AST、状态矩阵六大关键领域；
   - 上游 W11 基线 14 项测试 100% 通过（`PASS=14 FAIL=0`，退出码 `0`），基线纯函数逻辑完好；
   - 确定性门禁 `check_candidate.py` 9 项检查全部一次性通过（`EXIT=0`）；
   - 母本零改动、零漂移（SHA256 仍为 `517889c6…5ba636`），测试零母本 import。
2. **决策建议**：
   - **结论**：**值得进入下一道门（候选复审与离线集成演练）**。
   - **红线限制**：进入下一道门后，依然必须严格执行离线集成，**严禁**跳过后续复审直接将候选应用至正式母本，**严禁**签批真机验收。
