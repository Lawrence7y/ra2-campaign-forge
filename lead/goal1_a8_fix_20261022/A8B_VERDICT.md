# A8-b 补丁独立核验判定书

- **目标**：GOAL-3T · A8-b —— 给 A8（`a8_sweep_carrier_processes`）加「枚举器正控探针」，堵住 `find_pids()` 快照失败返回空 list 导致的 false-PASS 通道。
- **核验对象**：`qc151_trip.harness5.py`（相对基线 `qc151_trip.harness4.py`）
- **核验方式**：独立脚本 `VERIFY_A8B.py`，全部数字由核验脚本自行计算，未采信实现者自述（`A8_IMPL_SELF_REPORT.md` / `ENUM_PROBE_TEST.txt` 仅作对照，未作为证据）。
- **核验脚本 stdout**：`VERIFY_A8B.txt`（104 行，全量）
- **执行环境**：Windows 10.0.26200 / Python 3.12.10 / `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe`
- **核验时间**：2026-10-22
- **脚本退出码**：`EXIT=0`（脚本语义：0 = 全部 CONFIRMED）

---

## 总判定：**CONFIRMED**

30 项检查全部 CONFIRMED，0 项 REFUTED。补丁在**语义上确实关闭了**缺陷所描述的 false-PASS 通道，且改动面严格收敛在 A8 层，未触碰 `find_pids` 本体、未新增退出码、未引入任何禁止面 API。

---

## 逐项结果

| # | 核验项 | 判定 | 关键证据 |
|---|---|---|---|
| 1 | 基线零改动 | **CONFIRMED** | `harness4.py` 424078 B，LF16 = `cd9bbc87e46054af`（与给定基线一致）；文件 mtime 仍为 `2026-10-22 12:32:01`（早于副本 13:01:40）；`git status` 对该文件无输出（未修改）。 |
| 2a | 副本 LF 哈希 | **CONFIRMED** | `harness5.py` LF16 = `f1e5bc7b0ff30c9c` |
| 2b | 副本 CRLF 哈希 | **CONFIRMED** | CRLF16 = `3b10dae011d08c4b`（算法：`\r\n`→`\n`，再 `\n`→`\r\n`，取 sha256） |
| 2c | 副本字节数 | **CONFIRMED** | 427456 B；实测**不含任何 CR 字节**（纯 LF），故 LF16 == raw sha16。 |
| 3a | 反向重建（生成器路径） | **CONFIRMED** | 从 `_gen_harness5.py` 的 AST 中取出 `ANCHOR_1..4` / `PATCH_1..4` 常量，独立执行 4 次唯一锚点替换（每锚点出现次数实测 = 1），产出 427456 B、LF16 `f1e5bc7b0ff30c9c`，**逐字节等于** `harness5.py`。 |
| 3b | 反向重建（diff 路径） | **CONFIRMED** | 自写 unified-diff 应用器，对 `a8b.diff` 的每个 hunk 逐行校验旧文本（context/removal 全部匹配，无一处 fallback），重建结果同样**逐字节等于** `harness5.py`。两条独立路径互证。 |
| 4a | 新增符号唯一 | **CONFIRMED** | 按函数/类名分组比对 `ast.dump`：h4 = 173 个，h5 = 174 个；新增集合 = `['def:_a8_enum_probe']`。 |
| 4b | 无删除 | **CONFIRMED** | 删除集合 = `[]`。 |
| 4c | 变更面收敛 | **CONFIRMED** | 变更集合 = `['def:a8_sweep_carrier_processes']`，**其余 172 个函数/类 `ast.dump` 完全相同**。 |
| 4d | `find_pids` 逐字节相同 | **CONFIRMED** | 用 `ast.get_source_segment` 取两文件的 `find_pids` 源码段，字符串相等；段长 2264 B，段 sha16 = `61626b4b252d0260`。实现者「不改本体」的声称成立。 |
| 5 | 不新增退出码 | **CONFIRMED** | 解析顶层 `EXIT_* = <literal>` 赋值：h4 27 个、h5 27 个；名称集合相同、取值逐一相同；added = `[]`，removed = `[]`。探针失败走既有 `EXIT_TERMINATE_FAILED`(24) 收口语义（`note_cleanup_failure`），未新增码。 |
| 6a | 新增行禁止面 | **CONFIRMED** | 新增 62 行内，`taskkill`/`SendMessage`/`PostMessage`/`SendInput`/`WriteProcessMemory`/`CreateRemoteThread`/`RegSetValue`/`RegCreateKey`/`RegDeleteKey`/`RegOpenKey`/`winreg`/`QueueUserAPC`/`SetWindowsHookEx`/`DebugActiveProcess` 命中数**全为 0**。 |
| 6b | 全量计数未上升 | **CONFIRMED** | 两文件全量计数逐一比较，无任何禁用词出现次数上升（`SendInput`=11、`WriteProcessMemory`=3、`CreateRemoteThread`=1、`QueueUserAPC`=1、`SetWindowsHookEx`=1、`DebugActiveProcess`=1，均为 harness4 既有、位于禁令注释区）。 |
| 6c | `taskkill` 无按名全杀 | **CONFIRMED** | 用 `tokenize` 归类每次出现：h5 仅 2 处，均为 `STRING`（第 3、1343 行，即文件头禁令文档串）；h4 同为 2 处 `STRING`。**代码区 0 次**。 |
| 7a | 可安全 import | **CONFIRMED** | 模块级副作用仅 1 处 `SetProcessDPIAware()`（DPI 感知，自身进程声明）+ 常量赋值；`if __name__ == "__main__"` 守卫存在；无 `Popen`/`system`/`run`。import 成功，未启动任何进程。 |
| 7b | 正控 ok=True | **CONFIRMED** | 实调 `_a8_enum_probe`：`self_name='python.exe'`、`self_pid=17316`、`found` 含该 pid、`ok=True`。 |
| 7c | 留痕正确 | **CONFIRMED** | FakeRec 收到 `a8_enum_probe_where/self_name/self_pid/found/ok` 五条，`a8_enum_probe_ok=True`。 |
| 7d | 负控（快照恒空） | **CONFIRMED** | 打补丁 `find_pids = lambda name: []` 后，探针 `ok=False`。 |
| 7e | 负控下 `remaining` 非空 | **CONFIRMED** | 传不存在的载体目录调用 `a8_sweep_carrier_processes`，返回 `remaining=[{'pid': None, 'image': '<ENUM_FAILED_BEFORE_SWEEP>'}]`、`rounds=0`、`enum_probe_ok=False`。 |
| 7f | 哨兵可识别 | **CONFIRMED** | `remaining` 中 `image` 含 `ENUM_FAILED` 子串。 |
| 7g | 无「误杀」 | **CONFIRMED** | 负控下 `swept == []`，说明探针失败时**没有进入任何 TerminateProcess 分支**。 |
| 7h | verdict 记录 | **CONFIRMED** | 负控下 `a8_enum_verdict` 值为 `'FAIL'`。 |
| 7i | 中途失效也拦下 | **CONFIRMED** | 构造「前 3 次正常、之后返回空」的 flaky `find_pids`（覆盖 `before_sweep` + 清扫循环），返回 `remaining=[{'pid': None, 'image': '<ENUM_FAILED_BEFORE_REMAINING>'}]`、`swept=[]`。收尾探针确实起作用，不是摆设。 |
| 7j | 正控清扫路径 | **CONFIRMED** | 真实枚举器 + 不存在的载体目录：`remaining=[]`、`swept=[]`、`rounds=1`（第一轮 killed==0 即 break）。正常路径未被误伤。 |
| 7k | 抛异常形态 | **CONFIRMED** | `find_pids` 抛 `OSError` 时，探针内部 `except` 兜住，`ok=False`、`error` 有值，**异常不逃逸**（不会让 A8 整体崩成 `EXIT_INTERNAL_ERROR`，仍走 V-fail 语义）。 |
| 8a | 探针顺序 | **CONFIRMED** | 静态偏移：`before_sweep@64800 < sweep_loop@65252 < before_remaining@66706 < remaining_enum@67171 < return@68458`，严格递增。顺序正确——若收尾探针放在 `remaining` 枚举之后，探针即形同虚设。 |
| 8b | 探针在同一函数体 | **CONFIRMED** | 两次探针调用位置都落在 `def a8_sweep_carrier_processes(...)` 与下一个顶层 `def` 之间。 |
| 8c | 调用方 V-fail 路径存在 | **CONFIRMED** | `main()` finally 段 `if _a8_res["remaining"]:` → `note_cleanup_failure(EXIT_TERMINATE_FAILED, ...)`，哨兵因此必然触发非 0 退出。 |
| 9 | 零删除行 | **CONFIRMED** | `Counter` 多重集比较：h4 7720 行 → h5 7782 行（+62）；缺失行数 = 0。补丁纯追加。 |
| 10 | 合成冒烟 | **CONFIRMED** | `ast.parse(harness5)` 通过。未使用 `py_compile`，未落 `.pyc` 到被核验目录（import 产生的 `__pycache__` 已在核验后删除）。未启动游戏、未杀任何进程。 |

---

## 缺陷闭合性论证

原缺陷链：`CreateToolhelp32Snapshot` 失败 → `find_pids` 返回 `[]` → A8 的 `remaining` 为空 → 调用方判「零残留」→ **false-PASS**。

补丁后的链：
1. 清扫**前**查本进程自身（必然存在）⇒ 查不到即枚举器失效 ⇒ 立即返回带 `<ENUM_FAILED_BEFORE_SWEEP>` 的 `remaining`，**不进入清扫循环**（`swept=[]`，不会误杀）。
2. 清扫**后**、`remaining` 枚举**前**再查一次 ⇒ 中途失效同样被捕获（7i 实测）。
3. 两种失效都产出**非空** `remaining` ⇒ 调用方 `if _a8_res["remaining"]:` 命中 ⇒ `note_cleanup_failure(EXIT_TERMINATE_FAILED)` ⇒ 退出码非 0 ⇒ V-fail。

⇒ 「枚举失败」与「确实无残留」在返回值层面**已可区分**，false-PASS 通道关闭。

---

## 残余限制（不构成 REFUTED，供后续卡参考）

1. **仅能捕获「整体失效」**：探针判定 `self_pid in found`，只能发现快照完全失败（空表）或抛异常。若 `Process32Next` 在枚举到自身之后中途失败，`found` 仍含 `self_pid`，探针会判 PASS，而目标进程可能漏枚举。此为本修法设计上的天花板，非本次补丁引入的回归。
2. **依赖 exe 名可比性**：`self_name = Path(sys.executable).name`，与 `find_pids` 的 `mbcs` 解码后小写比较一致，本环境（`python.exe`）实测通过。若以改名副本或路径极长的解释器运行，理论上有名字解析差异风险，但失败方向是 **fail-closed**（探针判 False ⇒ V-fail），不会造成新的 false-PASS。
3. **`A8_ALLOW_LOADER[0]` 为假时不执行清扫**：此时探针也不执行，但 `remaining` 断言同样不执行，无 false-PASS 面。

---

## 纪律遵守说明

- 全程**只读** `qc151_trip.harness4.py` / `qc151_trip.harness5.py`（mtime 未变，git 无改动）。
- 仅写入三件交付物：`VERIFY_A8B.py`、`VERIFY_A8B.txt`、`A8B_VERDICT.md`。
- 未使用 `--no-verify`；未使用 `py_compile`（改用 `ast.parse`）；未启动游戏、未杀任何进程、未创建测试载体目录（`_a8b_never_created_dir` 实测不存在）。
- import 产生的 `__pycache__/qc151_trip.harness5.cpython-312.pyc` 已在核验结束后删除。
