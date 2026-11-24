#!/usr/bin/env python3
"""Append §833: authoritative guard classification of all 69 loads (+ the false-positive record)."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §833 · **69 处载入的权威守卫分类：50 处无守卫 / 16 处有守卫 / 2 处 ECX 被改写 / 1 处无调用**（2026-11-15 12:10）

- **§833-1 [已证·方法与两次自我纠错]** 工具 `W127_reach\guard_classify.py`。
  判定"某处载入是否构成崩溃点"需要同时满足：
  ① 载入后到调用前，**ECX（含 `CX`/`CL`/`CH` 子寄存器）从未被写**；
  ② 该调用**没有任何条件跳转会跳过它**。
  - **纠错 1**：我第一版（`this_census.py`）用 `op_str` 前缀匹配判 ECX 写入 ⇒ **漏掉子寄存器写入**
    （`xor cl,cl` 的 op_str 是 `cl,cl`，能命中；但 `xchg eax,ecx`、`pop ecx` 这类形态会漏）。
  - **纠错 2**：我第二版（`this_census_strict.py`）改用 `ins.regs_access()`，但
    **capstone 把 `xor cl,cl` 记为写 `X86_REG_CL` 而非 `X86_REG_ECX`**，且**未考虑条件跳转可跳过调用**
    ⇒ 得出"66 处无守卫 / `0x7241A0` 有 13 处"的**假阳性**结论。
    复核时逐个反汇编才发现：12 处 `0x7241A0` 调用点前面都有 `cmp ecx,ebx / test ecx,ecx + je`（**有守卫**）。
  - ⇒ **最终版同时检查 4 个寄存器名 + 条件跳转目标是否越过调用点**。这才是本条的数据来源。

- **§833-2 [已证·权威表]**
  | 分类 | 数量 | 明细 |
  |---|---:|---|
  | **无守卫（真正的崩溃点）** | **50** | 见 §833-3 |
  | 有守卫（不构成崩溃点） | 16 | 12×`0x7241A0`、1×`0x724730`(`load=0x4A8B18`)、1×`0x724C00`、1×`0x724200`、1×`0x6A70AB` |
  | ECX 被改写 | 2 | `load=0x4F4562`（`xor cl,cl @0x4F457C`）、`load=0x7777F3`（`pop ecx @0x778827`） |
  | 窗口内无调用 | 1 | `load=0x6403A8` |

- **§833-3 [已证·50 处无守卫调用点按被调用者分组]**
  | 被调用者 | 无守卫调用点数 | 备注 |
  |---|---:|---|
  | **`0x00724730`**（容器 remove） | **28** | 含 §821 的 20 + 8 处（§825-4） |
  | **`0x00724580`**（容器 add） | **18** | §825 新增发现的第二条路径 |
  | `0x007241A0` | 1 | `load=0x5C4BB8 / call=0x5C4BE3` |
  | `0x00724520` | 1 | `load=0x6AB99F / call=0x6AB9A7` |
  | `0x00724530` | 1 | `load=0x6AB994 / call=0x6AB99A` |
  | `0x00724540` | 1 | `load=0x6AB9E3 / call=0x6AB9E9` |
  - ⇒ **46 + 4 = 50**，与 §825-2 的结论**一致**（§825-2 当时是按"喂给谁"统计的，口径正确）。

- **§833-4 [已证·对 §800 的量化]** §800 曾写"74 处引用中多数带比较式空检查"。
  现在有了量化答案：**69 处 `mov ecx,[0x887368]` 中，16 处（23%）在调用前有守卫，50 处（72%）没有。**
  ⇒ "多数有守卫"这个说法**反了**：**多数是没守卫的**。

- **§833-5 [已证·对修复方案的直接影响]**
  - 只守 `0x724730` ⇒ 漏 22 处（18 + 4），且会**崩溃点平移**（§825-6 已证）。
  - **G2（守 `0x724730` + `0x724580`）** ⇒ 覆盖 46/50。
  - **G6（再守 `0x7241A0`/`0x724520`/`0x724530`/`0x724540`）** ⇒ 覆盖 **50/50**。
  - 4 个字段访问器的入口 stub 语义（`0x724520` 为 `ret 4`；`0x724580`/`0x7241A0` 返回 `al`）见 §825-7。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §833" in src:
    sys.exit("ABORT: §833 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §833", "50", "16 处"):
    print("  %-10s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
