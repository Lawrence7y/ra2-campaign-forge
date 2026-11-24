#!/usr/bin/env python3
"""Append §847: function atlas + the Westwood source-module discovery."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §847 · **里程碑(2) 函数图谱完成 + 重大发现：二进制里带 74 个西木原始源文件名（`D:\ra2mdpost\*.cpp`）**（2026-11-15 22:30）

- **§847-1 [已证·函数图谱 v1（全量可枚举集）]**
  | 指标 | 值 |
  |---|---:|
  | 函数（可枚举） | **8,578** |
  | 代码字节合计 | 2,589,221 |
  | 出现在 `.rdata/.data` 作函数指针（虚表槽/函数表） | **1,966** |
  | 有 ≥1 个直接调用者 | 6,702 |
  | 调用者数为 0（根/仅虚表可达） | 1,876 |
  | 引用 ≥1 个字符串 | 738（8.6%） |
  | 调用 ≥1 个导入 API | 754 |
  | 不同导入 API | 187 |
  - 字段：`entry / size / n_instr / n_callers / n_callees / is_fnptr / first_import / n_strings / strings(≤40)`。
  - 产物：`W130_atlas\FuncAtlas.java`（第一趟）+ `FuncStrings.java`（字符串趟）+ `function_atlas.tsv`。

- **§847-2 [已证·图谱正确性校验：6/6 精确命中既有台账值]**
  | 函数 | 台账值 | 图谱值 |
  |---|---:|---:|
  | `0x00724730` | 385 | **385** |
  | `0x00724580` | 430 | **430** |
  | `0x007241A0` | 87 | **87** |
  | `0x006F3F40` | 953 | **953** |
  | `0x006D1660` | 270 | **270** |
  | `0x004FC0B0` | 1,559 | **1,559** |
  - ⇒ 这 6 个值分别由 §834/§838/§831/§826 在**不同轮次**独立得出，图谱全部复现 ⇒ 函数边界与大小可信。

- **§847-3 [已证·★ 重大发现：镜像内含西木原始源文件名]**
  字符串里出现形如 `D:\ra2mdpost\wonline.cpp` 的路径 —— 是 `assert()` 宏嵌入的 `__FILE__`。
  **全镜像共 74 个**（全部在 `D:\ra2mdpost\`），是本项目第一次拿到**二进制自带的模块 ground truth**。
  部分清单（按被引用函数数排序）：
  | 模块 | 函数数 | 模块 | 函数数 |
  |---|---:|---|---:|
  | `wonline.cpp` | 41 | `ModemHst.cpp` | 5 |
  | `GDlgSupp.cpp` | 14 | `Session.CPP` | 5 |
  | `PlanMgr.cpp` | 12 | `WOLPersonaInformation.cpp` | 5 |
  | `netshare.cpp` | 9 | `Init.CPP` | 4 |
  | `Scenario.CPP` | 8 | `Ion.cpp` | 4 |
  | `House.CPP` | 7 | `ModemGst.cpp` | 4 |
  | `netdlg2.cpp` | 7 | `NullDlg.CPP` | 4 |
  | `WDTSel.cpp` | 7 | `SerialEd.cpp` | 4 |
  | `wwmous.cpp` | 7 | `Sidebar.CPP` | 3 |
  | `MapGen.cpp` | 6 | `Skirmish.cpp` | 3 |
  | `Queue.CPP` | 6 | `AbsType.cpp` | 2 |
  | `UICmnds.cpp` | 6 | `Conquer.CPP` | 2 |
  - ⇒ 分布本身就有信息：**被引用最多的是网络/WOL（`wonline` 41）与对话框（`GDlgSupp` 14）、剧情管理（`PlanMgr` 12）**，
    说明这些模块的断言最密集（也说明它们调试期最不稳定）。
  - 同类还有 `Scenario.CPP`/`House.CPP`/`Infantry.CPP`/`Sidebar.CPP`/`MapSel.CPP`/`Init.CPP` —— 与游戏主体模块对得上。

- **§847-4 [已证·用源文件名做模块归属：覆盖 229 个函数 / 66 个模块 / 11.0% 代码字节]**
  - 方法：函数若引用某个源路径字符串，即归入该模块（产物 `module_attribution.tsv`）。
  - **覆盖上限已测**：把"每函数取 4 个字符串"放宽到 **40 个**，覆盖只从 8.9% → **11.0%**（215 → 229 函数）。
  - ⇒ **结论（重要，防止后续误判）**：`__FILE__` 路线**是种子，不是完整子系统图** ——
    因为 **8,578 个函数里只有 738 个引用任何字符串**（8.6%），其余函数压根没有字符串可用。
  - ⇒ 里程碑(3) 必须叠加其它杠杆：**① 虚表归属（1,966 个函数指针 → 954 个类）**、
    ② **导入 API 分组（187 个 API / 754 个函数）**、③ 调用图社区检测。

- **§847-5 [未证·一个尚未解释的差异（如实记录）]**
  `FunctionManager.getFunctionCount()` = **8,948**，但 `getFunctions()` 只能枚举 **8,578**（差 **370**），
  Ghidra 同时报告 `external=0`、`thunks=44`。
  - ⇒ 这 370 条**不是** external 函数；推测是无 body / 非默认地址空间的条目，**未证**。
  - ⇒ 既有台账/交接里的"**8,948 函数**"这个数字，指的是**管理器总数**；本图谱覆盖的是**可枚举的 8,578**。
  - ⚠️ 后续引用时须区分这两个数，不要混用。

- **§847-6 [已证·本轮工程教训（两个我自己踩的坑）]**
  1. **`\s` 会吃掉 TAB**：解析 headless 日志时用 `re.sub(r"\s*\(GhidraScript\)\s*$", …)`，
     把行尾**空的表格列**（末尾连续 `\t`）一起删掉，导致 8,578 行里 7,824 行被误判为"列数不足"而丢弃。
     改用 ` *`（只吃空格）后 8,578/8,578 全部解析成功。**教训：TSV 清洗禁用 `\s`。**
  2. **`getDataAt(代码地址)` 取不到字符串**：字符串是**代码引用到 `.rdata` 的目标**，
     必须遍历 `insn.getReferencesFrom()` 再看目标是否有 string value。第一版因此得到"0 个函数有字符串"。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §847" in src:
    sys.exit("ABORT: §847 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §847", "ra2mdpost", "8,578"):
    print("  %-12s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
