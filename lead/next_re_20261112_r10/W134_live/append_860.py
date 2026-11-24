#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §860 to the atlas ledger: the 370 gap is now explained."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

SEC = """
## §860 · **§857-5 第 5 条闭合：那 370 个"计入总数但不可枚举"的条目就是 PE 导入函数，不是丢失的代码**（2026-11-15 14:20）

> 来源：用户裁定"先不跑真机，只做静态"。本条纯静态、纯 Ghidra，零真机。

- **§860-1 [已证·根因]**
  Ghidra 的 `FunctionManager.getFunctionCount()` 统计的是**程序全部地址空间**里的函数，
  而 `getFunctions(true)`（`true` 是**遍历方向**，不是"包含外部函数"）只走 **默认地址空间（`ram`）**。
  两者之差恒为 **370**，因为那 370 个都在 **`EXTERNAL` 地址空间**里。
  | 量 | 值 |
  |---|---:|
  | `getFunctionCount()` | **13,286** |
  | `getFunctions(true)` 枚举数 | **12,916** |
  | **差额** | **370** |
  | `getExternalFunctions().size` | **370** |
  | 差额 == 外部函数数 | **true** |
  | 枚举到的 `isExternal` 计数 | **0**（证明迭代器跳过 EXTERNAL） |
  | 枚举到的 `isThunk` 计数 | 68（thunk 与这个差额**无关**） |
  | `getBody()==null` 的函数 | **0**（不是"无 body 条目"） |
  | 枚举结果按地址空间分布 | `{ram=12916}` |
  | 程序全部地址空间 | `ram`、`OTHER` |

- **§860-2 [已证·370 是什么]** 逐条枚举 `getExternalFunctions()`：
  - **370 个名字全不重复**，全部是 **Win32 API 导入**，例如
    `VirtualProtect`、`CreateProcessA`、`ReadFile`、`GetSystemTime`、`MulDiv`、`GetDateFormatA`……
  - 所属导入库 16 个：`ADVAPI32 / BINKW32 / COMCTL32 / DDRAW / DSOUND / GDI32 / IMM32 /
    KERNEL32 / OLE32 / OLEAUT32 / SHELL32 / USER32 / VERSION / WINMM / WSOCK32 / XYR`。
  - 其中 **0 个**被标记为 thunk。

- **§860-3 [已证·结论]** **12,916 就是引擎代码的完整函数数**，370 不是丢失的代码、不是无 body 条目、
  不是 thunk、不是导出表残留。§851-5 里那条"恒有 370 个计入总数但不可枚举的条目（未证）"**闭合**。
  - ⇒ **口径定稿**：今后所有覆盖率/统计一律用 **12,916**；引用 13,286 时必须写明是"含 370 个导入伪函数的管理器总数"。
  - ⇒ 覆盖率的**分母不再有任何未解释的余量**：12,916 个函数全部在 `ram` 空间、全部有 body。

- **§860-4 [已证·纠正我自己的一处误读]**
  §851-5 与 `FuncStrings.java` 的注释把 `getFunctions(true)` 里的 `true` 当成"包含外部函数"，
  并据此写下"external=0 ⇒ 没有外部函数"。**这是误读**：参数是遍历方向。
  真相是 **external 确实非 0（370）**，但迭代器根本不枚举它们，所以枚举时数到 0。
  - ⇒ 同一类错误形态（**把 API 参数语义猜错，然后用猜错的语义解释观测**）在本项目已是第 3 次
    （前两次见 §859-1 与 §835）。**判决性事实必须来自枚举/字节，不能来自 API 名的直觉。**

- **§860-5 [未证·一个小残差（如实登记）]** `external symbols = 372` 而 `external functions = 370`，
  差 **2**。可能是 2 个导入符号没有建立对应函数条目（例如只有 ordinal、或名为 `X` 之类的异常项）。
  这不影响 §860-3 的结论（差额 370 已按函数口径精确对上），但**未逐条核对**是哪 2 个符号。

- **§860-6 [已证·产物]** `lead\\next_re_20261112_r10\\W134_live\\`
  | 文件 | 内容 |
  |---|---|
  | `GapProbe.java` | 差额归因（管理器总数 / 枚举数 / 外部函数 / 按空间分布 / 判决） |
  | `GapExternals.java` | 370 个外部函数逐条枚举 + 导入库清单 |
  | `gap.log` / `gapext.log` | 两次 headless 运行的完整输出 |
  - 复跑：`analyzeHeadless.bat <proj> gamemd_auto -process gamemd.exe -noanalysis -readOnly -scriptPath <dir> -postScript GapProbe.java`
"""

P = LED
s = io.open(P, encoding="utf-8", newline="").read()
if "## §860 ·" in s:
    raise SystemExit("REFUSE: §860 already present")
s = s.rstrip("\n") + "\n" + SEC
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("appended §860; size=%d bytes; control chars=%d" % (len(s.encode("utf-8")), len(bad)))
if bad:
    print("BAD:", bad[:5])
