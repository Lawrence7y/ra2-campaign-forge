#!/usr/bin/env python3
"""Append §844: full 6-entry behavioural A/B matrix."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §844 · **六个入口的行为 A/B 矩阵全部通过（6/6 YES）：`ecx=0` 时无一例外 AV，装了守卫后无一例外安全返回**（2026-11-15 20:20）

- **§844-1 [已证·矩阵]** 同一 `live_guard_ab.py`，只换 trampoline 里的目标地址（`--fn`）：
  | 入口 | control（不装 hook） | patched（装 group A） | 判决 |
  |---|---|---|---|
  | `0x00724730`（容器 remove） | 线程 `0xC0000005`，进程死 | 存活，`mark=1` | **YES** |
  | `0x00724580`（容器 add） | 同上 | 同上 | **YES** |
  | `0x007241A0`（设 byte 状态） | 同上 | 同上 | **YES** |
  | `0x00724520`（写 `+0x228`） | 同上 | 同上 | **YES** |
  | `0x00724530`（保存） | 同上 | 同上 | **YES** |
  | `0x00724540`（恢复） | 同上 | 同上 | **YES** |
  - 六臂的 control 结果**完全一致**（`0xC0000005` + 进程死亡），patched 结果**完全一致**（`259` 自旋 + `mark=1` + 进程存活）。

- **§844-2 [已证·对"50 处无守卫"的独立佐证]**
  - §833 的结论是"这些例程在调用前不检查 `this`"，依据是**静态**的窗口分析。
  - 本节给出**运行期**佐证：对六个例程逐一以 `this=NULL` 调用，**没有一个自己活下来**（全部 AV）。
    ⇒ "它们确实都没有自我保护" 从静态推断升级为**真机事实**。
  - ⇒ 反过来说：在 `[0x887368]==NULL` 期间，任何一处无守卫调用点都必然崩——这正是 §833 的 50 处。

- **§844-3 [已证·修复有效性覆盖 ②-a 的全部 6 个入口]**
  结合 §842（装入/回读 6/6）与本节（行为 6/6），②-a 的修复链在**六个入口上都闭合**：
  静态生成 → 真机装入 → 独立回读 → 行为 A/B。

- **§844-4 [未证·第三条缺陷没有同等的 A/B]** 它的触发需要构造"`[obj+0xAC]==0` 的对象图"并调用
  `FUN_006f3f40`（依赖 map 对象与虚调用上下文），**本轮未做**。现有证据只有：
  磁盘字节核对（3/3）+ 真机装入回读（3/3，§842-4）。**行为效果未验**。
  可行的最小做法：给 helper 单独造一次真机调用（在目标进程里放一个 `+0xAC=0` 的假对象，
  分别以"未替换的原序列"和"helper"执行，比较是否 AV）——属下一轮工作。

- **§844-5 [已证·工具状态]** `live_guard_ab.py` 支持 `--fn <hex>` 指定目标、`--arm control|patched|both`；
  每次运行都会先清掉残留 gamemd、把旧 `except.txt` 改名备份、跑完 `TerminateThread` + `taskkill /T`，
  并打印 `residual`。本轮全部运行 `residual=[]`。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §844" in src:
    sys.exit("ABORT: §844 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §844", "6/6", "YES"):
    print("  %-10s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
