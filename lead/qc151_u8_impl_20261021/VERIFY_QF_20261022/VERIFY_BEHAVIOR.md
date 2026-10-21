# VERIFY_BEHAVIOR · 行为核验报告（QF-20261022）

- **被核验件**：`out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u8_impl_20261021/qc151_trip.harness3_u8.py`（416,425 字节，md5 `ac8f75f435c367ad2006fe377e99c0d3`）
- **核心函数**：`allow_loader_authorized(args, trip_id)`（补丁件 `:366–384`）
- **基线件**：`out/re_work/work_chain/CONTINUE_20261003/lead/qc151_harness_merge_20261021/qc151_trip.harness3.py`
- **核验目录**（本测试独占）：`.../qc151_u8_impl_20261021/VERIFY_QF_20261022/`
  - 测试脚本：`qf_behavior_truth_table.py`；原始输出：`_behavior_truth_table.json`
- **环境**：Python 3.12.10（`C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe`），Git Bash / win32
- **纪律声明**：全程只读被核验件与基线件，未做任何修改；未运行 `launch_direct`（避免真启动游戏）。

## 总体结论：**CONFIRMED**

`allow_loader_authorized` 实测行为与「双键 fail-closed」规格逐条相符：八种输入全部返回期望布尔值，属性缺失时**不抛异常**（用 `getattr` 带缺省值），未发现 fail-open 缺陷。B4/B5 均通过。B3 的推论需限定，详见该节。

---

## B1 导入方式 —— 走「真导入」，未降级到 ast+exec

`importlib.util.spec_from_file_location + exec_module` 对**补丁件与基线件都一次成功**，无需 ast+exec 提取单函数。测试脚本设 `sys.dont_write_bytecode = True`，导入不在源目录写字节码。

命令（在 `VERIFY_QF_20261022/` 下）：

```
python qf_behavior_truth_table.py
```

输出摘录（`_behavior_truth_table.json` 的 `B1` 节）：

```json
"patch":    {"method": "importlib.util.spec_from_file_location + exec_module", "ok": true, "has_func": true},
"baseline": {"method": "importlib.util.spec_from_file_location + exec_module", "ok": true, "has_func": false}
```

说明：模块顶层只有常量定义与 `ctypes` 封装（如 `:392 INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value`），`main()` 由 `:7558 if __name__ == "__main__":` 守卫，导入不触发趟逻辑、无文件副作用。核验中未在被核验目录留下除 B5 所述外的任何新文件。

## B2 八种输入真值表 —— 8/8 通过，(a) 不抛 AttributeError

`args` 用 `types.SimpleNamespace` 构造，函数取自真导入的模块。判定标准：返回值 `is` 期望布尔（严格 True/False，非 truthy）。

| # | 输入 | 期望 | 实测 | 判定 |
|---|------|------|------|------|
| a | 无 `allow_loader` 属性（仅有 `trip_id='T1'`） | False | **False（bool）** | PASS，**未抛 AttributeError** |
| b | `allow_loader=False, trip_id='T1'` | False | False（bool） | PASS |
| c | `allow_loader=True, trip_id=None` | False | False（bool） | PASS |
| d | `allow_loader=True, trip_id=''` | False | False（bool） | PASS |
| e | `allow_loader=True, trip_id='  '`（纯空格） | False | False（bool） | PASS |
| f | `allow_loader=True, trip_id='T1'`，传入 `'T2'` | False | False（bool） | PASS |
| g | `allow_loader=True, trip_id='T1'`，传入 `'T1'` | True | True（bool） | PASS |
| h | `allow_loader=True, trip_id='  T1  '`，传入 `'T1'` | True | True（bool） | PASS |

`SUMMARY_B2_ALL_PASS = True`（脚本 stdout，八条 `ok` 全真、`is_bool` 全真）。

**(a) 专项说明**：无缺陷。实现（`:379`、`:381`）用 `getattr(args, "allow_loader", False)` 与 `getattr(args, "trip_id", None)`，属性整体缺失时返回 `False` 而非抛异常——这正是 fail-closed 要求的形态，无 fail-open 风险。

附加探针（事实记录，不构成判据；均在 `B2_patch_extra`）：
- 两属性全缺 → False；`allow_loader='yes'`（非空串）→ True（与规格「allow_loader **为真**」一致；argparse 侧是 `store_true`，实际只会给 bool）；
- `trip_id` 参数传 `None` → False（`str(None).strip()≠'T1'`）；大小写不同（`'T1'` vs `'t1'`）→ False（逐字比较，区分大小写）；制表/换行两侧空白 → 归一后 True（`strip()` 覆盖全部空白字符）。

## B3 与基线对比 —— 基线确无此函数；推论需限定

1. **grep 核实**（命令原文）：

```
grep -n "allow_loader_authorized" .../qc151_harness_merge_20261021/qc151_trip.harness3.py
→ 无输出，EXIT=1
grep -in "allow_loader|allow-loader|ALLOW_LOADER" 同文件
→ 仅命中 ra2loader.exe 相关的禁令/闸门注释与 S-4 扫描串，无任何授权通道标识
```

2. **动态核实**：基线模块真导入成功后 `hasattr(mod, "allow_loader_authorized") = False`，且 `dir(mod)` 中无任何含 `allow` 的属性（`B3_baseline: {"func_found_dynamically": false, "module_attrs_matching_allow_loader": []}`）。
3. **调用面核实**：基线 `launch_direct`（`:1137`）签名**无** `allow_loader` 形参，调用点基线 `:6582` 也不传；补丁调用点 `:6693–6698` 才引入 `_u8_authorized`。

**「基线无此函数 ⇒ 不授权时行为不可能被改变」是否成立？—— 单靠这一点不成立，须分两层说**：
- 「基线无此函数」只证明**授权通道在基线中不存在**，它本身不证明补丁在未授权时与基线逐字同行为——补丁件还含其他改动（如 `s4_injection_gate` 加了 `authorized` 形参 `:1035`、`resolve_pid` 加了 `expect_name` 形参），这些是否等价属于**全量 diff 审计**的范围，不是本函数存在性可以推出的。
- 我另行核验了**授权判定值的三个消费点在 False 分支上与基线同构**（只读比对，非运行）：
  - `launch_direct`：`allow_loader=False` ⇒ `exe = carrier_dir / "gamemd.exe"`（补丁 `:1234`），与基线 `:1148` 同式；
  - `resolve_pid`：补丁 `:6703` 传 `expect_name=("gamemd.exe" if not _u8_authorized)`，False 时即基线缺省 `"gamemd.exe"`；
  - `s4_injection_gate`：补丁 `:1128–1148` 的授权旁路整体嵌在 `if authorized:` 内，False 时落回与基线 `:1079–1090` 相同的「HIT ⇒ 62」路径（比对了两侧代码块原文）。
- **结论表述**：在「启动目标 / PID 解析名 / S-4 闸门」这三个由授权值直接控制的决策点上，未授权路径与基线同构成立（源码级证据如上）；但「整个补丁在未授权时与基线行为完全一致」是一个更强的命题，需全量 diff 审计背书，本次核验范围（B1–B5）不能仅凭「基线无此函数」下此断言。

## B4 启动目标选择 —— 判定正确（AST 只读，未运行）

用 `ast.parse` + `ast.walk` 读 `launch_direct` 源码（脚本 `B4_launch_direct_patch/base` 节，含行号），并用 Read 复核原文。

**补丁件**（`def launch_direct`，`:1208–1268`，形参含 `allow_loader`）：

```python
:1228  if allow_loader:
:1229      exe = carrier_dir / ALLOW_LOADER_EXE          # ALLOW_LOADER_EXE = "ra2loader.exe"（:363）
:1233  else:
:1234      exe = carrier_dir / "gamemd.exe"  # ★★ 可执行体 = gamemd.exe（静态自检 #3）
:1255  proc = subprocess.Popen([str(exe)], cwd=str(carrier_dir))   # 全函数唯一 Popen
```

**AST 判定**：`allow_loader` 为真 ⇒ `ra2loader.exe`（经 `:363` 常量），为假 ⇒ `gamemd.exe`。与交付者宣称一致。

**调用接线**（`main()`，`:6693–6698`）：

```python
:6693  _u8_authorized = allow_loader_authorized(args, TRIP_ID)
:6697  proc = launch_direct(rec, budget, carrier_dir, LAUNCH_TOKEN,
:6698                       allow_loader=_u8_authorized)
```

`TRIP_ID` 在 `--trip-id` 缺省时由 `new_trip_id()` 随机生成（`:6491–6493`），结构上保证判据 2 失败 ⇒ 缺省即不授权。我用真实 argparse 复刻了 CLI 接线（`:6296–6306`）验证：不给任何 flag ⇒ `allow_loader=False, trip_id=None` ⇒ False；只给 `--allow-loader`（trip_id 为随机值）⇒ False；两者都给且匹配 ⇒ True。（此探针仅调用 argparse 与 `new_trip_id()`/判定函数，未触任何启动路径。）

**基线件**（`def launch_direct`，`:1137–1177`）：无条件 `exe = carrier_dir / "gamemd.exe"`（`:1148`），无 loader 分支——与「基线无授权通道」互为印证。

## B5 语法与编译 —— 退出码 0

- 主证据（输出仅落临时目录，符合「不留 __pycache__ 在源目录」的要求）：

```
python -c "import py_compile; py_compile.compile(SRC, cfile=<TMP>/u8_b5.pyc, doraise=True)"
→ compile OK；api_exit=0；临时目录内生成 401951 字节 pyc，临时目录已随后删除
```

- 附注（诚实披露副作用）：也跑了 `python -B -m py_compile <补丁件>`，退出码 0（`dash_B_exit=0`）；但 `py_compile` CLI 会**显式**写源目录 `__pycache__`（不受 `-B` 抑制）。该目录在**本核验开始前**已由交付流程存在（首见 `01:01:52`，早于本会话），我的运行仅使其 mtime 更新为 `01:24:30`，文件尺寸不变（401951 字节）且源码未改，故 pyc 内容逐字节同旧。基线目录被早先一次探针误建的 `__pycache__` 已删除并复核不存在。

## 缺陷与风险清单

- **未发现真实缺陷。** 重点核查项 (a)：属性缺失返回 False，无 `AttributeError`，无 fail-open。
- 规格符合性备注（非缺陷）：函数对**传入的 trip_id 参数也做 strip**（`:384 str(trip_id).strip()`），与任务书「args.trip_id 去空格后与传入 trip_id 逐字相等」的字面表述相比是双侧归一；但 `main()` 侧 TRIP_ID 本就 strip 过（`:6491`），实际运行中无差异，且 (h) 用例正是按此语义定为期望 True。
- 残余风险（超出 B1–B5 范围）：补丁其余改动面与基线的整体等价性需全量 diff 审计（见 B3 第 3 段）。

## 证据文件索引

| 文件 | 内容 |
|------|------|
| `VERIFY_QF_20261022/qf_behavior_truth_table.py` | B1–B4 测试脚本（只读被核验件，`sys.dont_write_bytecode=True`） |
| `VERIFY_QF_20261022/_behavior_truth_table.json` | 全部八输入实测返回值、附加探针、AST 提取行号与原文 |
| 本报告 | B3/B5 的命令原文与输出摘录（脚本外补跑：grep×2、py_compile×2、argparse 复刻） |
