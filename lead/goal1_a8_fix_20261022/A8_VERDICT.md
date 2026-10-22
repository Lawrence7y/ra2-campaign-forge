# A8 修复补丁 · 独立核验判定书

- 判定对象：GOAL-3T / A8（`--allow-loader` 授权趟收尾未清理 loader 派生的 `gamemd.exe`，裁决 3）
- 核验角色：**独立补丁核验员**（非实现者；不采信实现者自述数字，全部重算）
- 核验日期：2026-10-22
- 核验脚本：`lead/goal1_a8_fix_20261022/VERIFY_A8.py`
  sha256 `b8846f77acdcb26688d983298285d95c1e1fcf34b4de9f314943739cb326250d`
- 全量 stdout：`lead/goal1_a8_fix_20261022/VERIFY_A8.txt`
- 运行命令：`python VERIFY_A8.py > VERIFY_A8.txt 2>&1; ec=$?; echo EXIT=$ec`
- 运行退出码：**EXIT=0**

> 说明：本目录内原有一份同名 `A8_VERDICT.md`，是实现者侧的自述判定书（另含
> `_test_path_scope.py` / `PATH_SCOPE_TEST.txt` / `__pycache__`）。本文件是**独立核验员**
> 的判定书，已整体覆盖该自述件。两者冲突处以本文件为准，冲突项见 §7。

## 总判定

**CONFIRMED** —— A8 补丁通过全部 10 项独立核验，**REFUTED = 0**。

唯一未被证明的是**真机运行时行为**（真起 loader → 派生 gamemd → 实际清扫），按纪律未执行，
已在 K10 明确划为 UNVERIFIABLE，不计入缺陷，但也不得被宣称为已验证。

## 关键哈希（本核验员独立重算，未引用实现者数字）

| 对象 | 字节数 | LF sha256 |
|---|---|---|
| 母本 `qc151_trip.harness3_u8.py` | 416425 | `7db3c11009b7183c337ea53b0265140624675cba64703ee0a6c7751d9ea8192c` |
| 副本 `qc151_trip.harness4.py` | 424078 | `cd9bbc87e46054afd7fd591b59bb8c3a12574bed192833d0e41681dfc1492794` |

| 对象 | 值 |
|---|---|
| 母本 LF 前16 | `7db3c11009b7183c`（**== 期望值**） |
| 副本 LF 前16 | `cd9bbc87e46054af` |
| 副本 CRLF 前16（`\r\n`→`\n`→`\r\n` 后 sha256） | `896f45f1dcb474f5` |
| 副本 CRLF 全长 sha256 | `896f45f1dcb474f5811c1f1bc462e2e8e2ed3be15b57bfaef69e6d52a9a62749` |
| 副本 CRLF 展开后字节数 | 431797 |
| `a8.diff` | 9330 字节，纯 LF，sha256 `363cebf89bcda3735289f70c52c3c7c33bab4ef678603ae3efefc256745cb38b` |
| 副本行尾形态 | 纯 LF（`\r\n` 计数 0，lone LF 7719），无 BOM，末尾有换行，UTF-8 可解码 |

增量：字节 `+7653`（424078 − 416425），行 `+160`（7719 − 7559）。

## 逐项结果

| 项 | 核验内容 | 判定 |
|---|---|---|
| K1 | 母本零改动（LF sha256 前16） | **CONFIRMED** |
| K2 | 副本哈希自证（LF/CRLF 双哈希 + 字节数） | **CONFIRMED** |
| K3 | 反向重建（`a8.diff` 逐字节 / 生成器锚点复算） | **CONFIRMED** |
| K4 | AST 零改动面（按函数名分组比对） | **CONFIRMED** |
| K5 | 禁止面（按名全杀 / 注入类 API / winreg 写 / 既有语义） | **CONFIRMED** |
| K6 | 作用域正确性（finally 内 / 模块级容器 / 早于 launch） | **CONFIRMED** |
| K7 | 路径归属判定（`relative_to` + 三用例实跑） | **CONFIRMED** |
| K8 | 负控有效性（重跑 + 独立判断覆盖性） | **CONFIRMED** |
| K9 | 合成冒烟（`ast.parse` + 符号 + 路径三用例） | **CONFIRMED** |
| K10 | 附加风险审查（传导链 / 顺序 / 已知弱点 / 不可核验边界） | **CONFIRMED** |

## 逐项证据

### K1 母本零改动 —— CONFIRMED

- 独立计算 `sha256(master)` 前16 = `7db3c11009b7183c`，与要求逐字符相符。
- 母本 `\r\n` 计数 = 0（纯 LF），字节 416425，全程只读、未写入。
- 母本路径：`out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u8_impl_20261021/qc151_trip.harness3_u8.py`

### K2 副本哈希自证 —— CONFIRMED

- 副本 424078 字节；纯 LF；无 BOM；UTF-8 可解码；末尾有换行。
- LF sha256 = `cd9bbc87e46054afd7fd591b59bb8c3a12574bed192833d0e41681dfc1492794`（前16 `cd9bbc87e46054af`）。
- CRLF 口径 = `896f45f1dcb474f5811c1f1bc462e2e8e2ed3be15b57bfaef69e6d52a9a62749`（前16 `896f45f1dcb474f5`），展开后 431797 字节。

### K3 反向重建 —— CONFIRMED

- 用**自写**的 unified-diff 解析器读 `a8.diff`，得 4 个 hunk：`@484,6`、`@1417,6`、`@6691,6`、`@7348,6`。
- 逐 hunk 校验**上下文行**与**删除行**文本严格相等（不等即抛），再重建：
  - 重建 424078 字节，sha256 `cd9bbc87e46054afd7fd591b59bb8c3a12574bed192833d0e41681dfc1492794`，
    与副本 **逐字节相同**。
- 交叉验证（独立路径）：不 import 生成器，只用 AST 抽出其 4 组 `ANCHOR_*/PATCH_*` 字符串常量，
  在母本文本上依次替换；每组锚点在当前文本中**恰好命中 1 次**；复算结果同样与副本**逐字节相同**。
- 第三方工具交叉：系统 `patch -p0` 在临时目录实打补丁，`DRYRUN_EXIT=0`、`APPLY_EXIT=0`，产物 sha256 同上且与副本相等。
- 结论：`a8.diff`、生成器、副本三者互为可逆、可复现，不存在手工夹带。

### K4 AST 零改动面 —— CONFIRMED

- 母本模块级函数 131 个，副本 134 个。
- 副本**新增**函数恰好 3 个，正是允许集：`_a8_path_under_carrier`、`_a8_query_image_path`、`a8_sweep_carrier_processes`。
- **缺失**函数：无。
- 函数体**变化**者：仅 `main`（允许项）。其余 130 个函数 `ast.dump` 完全一致；
  4 组同名重定义（`_burst_battle`、`_spot_centers_match`、`_spot_screen_guard`、`_rpm_u32`）
  也按出现顺序逐一比对一致。
- `main` 内变化被精确量化：
  - `main.try.body` 语句 158 → 159（**+1**）
  - `main.finally` 语句 11 → 12（**+1**）
  - 两者均为**保序追加**（母本语句序列是副本序列的子序列，append-only = True）
- 模块级语句（排除函数定义，**两侧均排除 `main`**）：334 → 335（**+1**），保序追加；
  新增唯一语句即 `A8_ALLOW_LOADER = [False]`。
- 未发现任何未预期的函数增删或函数体重写。

### K5 禁止面 —— CONFIRMED

- **`taskkill /IM` 按名全杀**：AST 扫全部字符串常量，`taskkill` 与 `/im` 同现 **0 处**。
  副本中 `taskkill` 仅出现 2 处既有说明文本（模块 docstring 第 3 行、`terminate_owned_process`
  docstring 第 1343 行），与母本一致，**非调用**。新增代码路径无 `taskkill` 调用。
- **注入类 API 增量**：`SendMessage` / `PostMessage` / `SendInput` / `WriteProcessMemory` /
  `CreateRemoteThread` 的调用次数，副本与母本**逐一相同**（`SendInput` 各 2 次，其余各 0 次），
  **增量为 0**。A8 新增代码不含窗口消息、输入合成、跨进程写内存或远程线程。
- **`winreg` 写**：全 AST 无 `winreg` 名称引用、无 `winreg` 导入；
  `SetValue`/`SetValueEx`/`RegSetValue`/`RegSetValueEx`/`CreateKey`/`CreateKeyEx`/
  `SetKeyValue`/`DeleteKey`/`DeleteValue` 调用 **0 处**。
- **`terminate_owned_process` 既有语义**：该函数 `ast.dump` 母本与副本**完全相同**
  （dump sha256 前16 两侧均 `4c9ae655585fbab4`，行跨度均 85 行）。A8 未改其身份核验、
  `proc.terminate()`、等待/复核、返回值语义，也未改其 fail-closed 的
  `EXIT_PID_IDENTITY_UNVERIFIED` 记账。
- A8 的终止手段是 `OpenProcess(PROCESS_TERMINATE|SYNCHRONIZE)` + `TerminateProcess` +
  `WaitForSingleObject`，且**先**核 `QueryFullProcessImageNameW` 全路径归属再终止——不是按名全杀。

### K6 作用域正确性 —— CONFIRMED

- `A8_ALLOW_LOADER` 是**模块级 `Assign`**（模块 body 第 493 行），初值 `[False]`；
  模块级 `AnnAssign` 计数 0。
- `main()` 内 `Try`-带-`finalbody` 节点数 = 1；A8 守卫 `if A8_ALLOW_LOADER[0]:`
  位于该 `finally` 的 `finalbody` **第 6 条**（0-based index 6）。
- 守卫 test AST = `Subscript(value=Name('A8_ALLOW_LOADER'), slice=Constant(0))`
  ⇒ **读模块级容器**；守卫 AST 中**不含** `_u8_authorized`（判定 False）。
- 守卫体内确含：`a8_sweep_carrier_processes` 调用、`remaining` 检查、
  `note_cleanup_failure`、`EXIT_TERMINATE_FAILED`、`a8_verdict` 写入。
- **执行顺序**（finalbody 索引）：`termination_verdict`(5) → **A8 清扫(6)** → `fin_carrier`/载体删除(7)。
  即先按原语义终止 loader，再进程树清扫，最后删载体目录（避免文件占用）——顺序正确。
- **赋值早于 launch**：`A8_ALLOW_LOADER[0] = bool(_u8_authorized)` 在行 **6823**，
  `launch_direct(...)` 在行 **6827**，`6823 < 6827` 成立；且该赋值紧跟
  `_u8_authorized = allow_loader_authorized(...)`（行 6821），早于任何 `Popen`。
- 默认 `False` ⇒ 非授权趟守卫短路，不触碰任何进程。

### K7 路径归属判定 —— CONFIRMED

- 静态：`_a8_path_under_carrier` 内调用集合 `{Path, relative_to, resolve}`；
  **用 `relative_to`**、**不用 `startswith`**；两侧均先 `resolve()`（消除 `..`/相对路径/链接差异）。
- 实跑（把**副本原文**经 `ast.get_source_segment` 取出后 exec 到受控命名空间，
  测的就是补丁里那几行）：
  - (a) 载体 `D:\qa\carrier\abc`、进程 `D:\qa\carrier\abc\gamemd.exe` ⇒ **True**（期望 True）
  - (b) 载体 `D:\qa\carrier\abc`、进程 `D:\qa\carrier\abcd\x.exe` ⇒ **False**（期望 False）
  - (c) 载体 `D:\qa\carrier\abc`、进程 `C:\Windows\system32\x.exe` ⇒ **False**（期望 False）
- **判别力反证**：(b) 若用 `startswith` 本机会返回 **True**（实测），而实现返回 False
  ⇒ 该用例确实能区分两种实现，测试有判别力。
- 附加用例：真实载体形态（`...\qc161_u0400_trip\c_20261022_120000_1234\ra2loader.exe`）⇒ True；
  进程路径恰等于载体目录 ⇒ True；空 `image_path` ⇒ False（有前置 `if not image_path`）。
- **大小写语义实测（重要，纠正实现者自述）**：win32 上 `pathlib.PureWindowsPath` 会做大小写折叠，
  故 `Path.relative_to` 在本机是**大小写不敏感**的：`C:\T\ABC\gamemd.exe` vs 载体 `C:\t\abc`
  判定为 **True（命中）**，`D:\QA\CARRIER\ABC` vs `D:\qa\carrier\abc` 同样命中。
  ⇒ 不存在"大小写不同导致漏杀"的已知局限（实现者 §3.3 的相反结论是错的，见 §7）。

### K8 负控有效性 —— CONFIRMED

- 亲自重跑 `_a8_negctl.py`：**EXIT=0**，输出
  `negative-control RED segments: 6/6`、`checks passed: 13/13`、`RESULT: ALL PASS`
  （13 = 1 基线母本哈希 + 6 基线判定 + 6 负控段）。
- **独立判断覆盖性**（自建变体复算，不采信脚本自述）：

| 段 | 做法 | 是否真覆盖对应断言 |
|---|---|---|
| N-1 | 母本追加 1 字节，哈希 `df354bc6ed7c337c` ≠ `7db3c11009b7183c` | 是：哈希对字节变化敏感，可拦误改母本 |
| N-2 | 守卫替换为 `if allow_loader_flag:` | 是：`"if A8_ALLOW_LOADER[0]:" not in text` 变红，覆盖"守卫必须模块级" |
| N-3 | 声明改名 `A8_ALLOW_LOADER_DISABLED` | 是：`decl < assign < guard` 顺序判定变红 |
| N-4 | 删 `def find_pids(name: str) -> list:` | 是：该行经独立核实在**母本第 823 行真实存在**、副本亦存在；删除后 `Counter` 逐行计数确实减少 ⇒ `no_removed_lines` 变红。**不是删空行/注释的假阴性** |
| N-5 | `def a8_sweep_carrier_processes(` 改名 | 是：`symbols` 判定变红 |
| N-6 | A8 尾段注入 `if _u8_authorized:` | 是：`no_try_local` 变红，覆盖"finally 不得读 try 局部名" |

- 独立复算的 8 条判断全部 True。
- **边界如实标注**：N-1~N-6 检验的是**生成器自检的判别力**，不检验**运行时进程树终止行为**；
  后者见 K10/R1、R2 的 UNVERIFIABLE。

### K9 合成冒烟 —— CONFIRMED

- `ast.parse(copy)` 通过（**未用 `py_compile`**，本核验未生成 `.pyc`）。
- 模块级 `def` 存在：`a8_sweep_carrier_processes`、`_a8_query_image_path`、
  `_a8_path_under_carrier`、`terminate_owned_process`、`find_pids`、
  `note_cleanup_failure`、`main` 全部 True。
- 模块级常量 `A8_ALLOW_LOADER` 存在；`ctypes` / `time` / `Path` 均已导入。
- **导入期安全**：`from __future__ import annotations` 存在（注解延迟求值）；
  即使按立即求值，注解引用的 `Recorder`(定义@552)、`TripBudget`(定义@573)
  也均早于 A8 函数定义@1479 ⇒ 不会在 `def` 时 `NameError`。
- 路径三用例复跑 True/False/False，与 K7 一致。
- 全程未启动游戏、未 `Popen` 任何游戏二进制、未碰真机。

### K10 附加风险审查 —— CONFIRMED（含已标注弱点）

**V-fail 退出码传导链（静态确认闭合）**

1. `remaining` 非空 ⇒ `note_cleanup_failure(EXIT_TERMINATE_FAILED, ...)`；
   该函数 `append` 到模块级 `CLEANUP_FAILURES`（AST 确认）。
2. `EXIT_TERMINATE_FAILED = 24` 在 `CLEANUP_CODE_PRIORITY` 中（最高档），
   `merge_cleanup_code` 按 `_rank` 取 `min`（AST 确认）。
3. `main()` 的 `finally` 末尾 `FINALIZE_CODE[0] = merge_cleanup_code(EXIT_OK)`；
   `_main_wrapper()` 中 `final = merge_cleanup_code(code)` 再与 `main()` 返回值合并
   ⇒ 进程退出码非 0。
4. `CLEANUP_FAILURES.clear()` 在 `main()` 开头执行（单趟一次性），不跨趟污染。

⇒ **"残留不满足 ⇒ 该趟 V-fail（退出码非 0）"这条链路闭合**，不是只写日志。

**清扫异常同样判失败**：`except Exception as _a8e` 分支也调
`note_cleanup_failure(EXIT_TERMINATE_FAILED, ...)` 并记 `a8_verdict = "ERROR"`
⇒ 清扫本身抛异常不会静默通过。

**顺序正确**：A8 清扫在载体删除之前（finalbody 6 vs 7），避免"进程仍占文件导致删目录失败"。

**已记录但不构成 REFUTED 的静态弱点**

- **C1 死局部变量**：`a8_sweep_carrier_processes` 内 `TARGETS = ("gamemd.exe", "ra2loader.exe")`
  赋值后从未使用（全函数仅 1 次出现），实际枚举硬编码为
  `find_pids("gamemd.exe") + find_pids("ra2loader.exe")`。纯冗余，无行为影响；
  建议后续清理或改为按 `TARGETS` 循环。
- **C2 查询失败即跳过**：`OpenProcess` / `QueryFullProcessImageNameW` 失败时，该 pid 在
  **终止循环**与**残留断言**中都被静默跳过 ⇒ 理论上存在"载体目录下存在无法查询的进程 ⇒ 误判 PASS"。
  缓解：同用户进程用 `PROCESS_QUERY_LIMITED_INFORMATION` 通常可查询，且 loader/gamemd 均为本趟同用户进程。
  风险低，但严格意义上断言不是"绝对零残留"。
- **C3 own_pid 排除**：`remaining` 计算排除 `own_pid`（loader 自身 pid），故"loader 存活"不由
  `a8_remaining_count` 反映；但该情形已由既有 TERM 项判 `EXIT_TERMINATE_FAILED(24)` ⇒ 仍触发 V-fail，不构成漏判。
- **C4 名称 + 路径双重条件**：先用 `find_pids` 按 basename 枚举，再逐个核全路径归属后才终止
  ⇒ 属"按名枚举 + 按路径精确筛选"，**不是**按名全杀，符合裁决 3 的"按进程树终止"意图。
- **C5 非授权趟零影响**：A8 块仅在 `A8_ALLOW_LOADER[0]` 为真时执行，默认 `False`，
  非授权趟只多写一条 `a8_verdict = "N/A"` 记录，不触碰任何进程。
- **C6 枚举失败即空表（false-PASS 通道）**：`find_pids` 在
  `CreateToolhelp32Snapshot` 失败（`not snap or snap == INVALID_HANDLE_VALUE`）或
  `Process32First` 失败时**返回空 list**，不区分"无进程"与"枚举失败"。
  `a8_sweep_carrier_processes` 未对该情形做任何补偿（无正控探针、无异常传播）
  ⇒ 若枚举整体失败，清扫循环空转、`remaining` 为空 ⇒ 记 `a8_verdict = "PASS"`。
  这是**断言可靠性**的真实缺口（非安全缺口：不会误杀）。建议下一轮加一条显式正控
  （例如枚举 `explorer.exe` 之类必然存在的进程名，为空则判 `ERROR` 而非 `PASS`）。

**UNVERIFIABLE 边界（如实声明，不计入缺陷）**

- **R1** 真实 `ra2loader.exe` → 派生 `gamemd.exe` 的**实际进程树终止未执行**
  （纪律：不启动游戏、不碰真机）。静态可确认的仅为：按已核验的载体路径逐个
  `TerminateProcess` 并 `WaitForSingleObject(5000)`，三轮重试，随后再枚举断言。
  **运行时实效性本核验无法证明**。
- **R2** 真实趟次"零残留"断言的运行时结果同样 UNVERIFIABLE。
- 本判定书不对 R1/R2 作任何 CONFIRMED 声明。若要闭环，应在**独立**真机授权趟中采集
  `a8_swept_count` / `a8_remaining_count` / `a8_verdict` 三项记录，并以进程快照前后差佐证。

## 7. 与实现者自述判定书的冲突

| 项 | 实现者自述 | 本核验实测 | 处置 |
|---|---|---|---|
| `Path.relative_to` 大小写语义 | §3.3 称"win32 是**大小写敏感**的字符串比较"，并据此把大小写差异记为"判窄/漏杀"已知局限 | **错误**。`pathlib.PureWindowsPath` 在 win32 折叠大小写；`C:\T\ABC\gamemd.exe` vs `C:\t\abc` 实测 **命中（True）**；`D:\QA\CARRIER\ABC` vs `D:\qa\carrier\abc` 同样命中 | 该"已知局限"不存在，应撤销；无需 `os.path.normcase` 加固 |
| `find_pids` 枚举失败 | §6 提及"会把枚举失败误判为零残留"，但未列为本轮缺口 | 实测确认：快照失败 / `Process32First` 失败均 `return pids`（空表），A8 无补偿 ⇒ **false-PASS 通道真实存在** | 提升为 C6，建议下一轮加正控探针 |
| 目录卫生 | 未提及 | 目录内存在实现者自测产物 `__pycache__/qc151_trip.harness4.cpython-312.pyc`（12:38 由 `_test_path_scope.py` 导入模块产生）、`_test_path_scope.py`、`PATH_SCOPE_TEST.txt` | 与本补丁副本无关，但 `.pyc` 违反"不落 pyc"门禁习惯，建议清理；**本核验未删除**（只读纪律 + 非本核验产物） |

以上三项均为**文档/卫生**问题，不改变代码判定：**代码侧 CONFIRMED**。

## 8. 结论

A8 补丁在**静态与合成层面完全成立**：

- 母本零改动（`7db3c11009b7183c`）；
- 副本哈希可自证（LF `cd9bbc87e46054af` / CRLF `896f45f1dcb474f5`）；
- `a8.diff` 可逐字节反向重建（自写解析器 + 生成器锚点 + 系统 `patch` 三路一致）；
- AST 改动面严格收敛于 **3 个新函数 + `main` 的 2 处追加 + 1 条模块级常量**；
- 禁止面零新增，`terminate_owned_process` 语义逐字节未变；
- 作用域与执行顺序正确（finally 内、模块级容器、赋值早于 launch、清扫早于删载体）；
- 路径判定用 `relative_to`，三用例（含 `abcd` 前缀陷阱）实跑通过，且用例具判别力；
- 负控 6 段均具真实判别力（N-4 删的是母本第 823 行真实存在的行）；
- V-fail 退出码传导链闭合。

**总判定：CONFIRMED（REFUTED = 0）**，附 C1–C6 六项非阻断建议，与 R1/R2 两项真机不可核验边界。
