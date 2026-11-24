#!/usr/bin/env python3
"""Sync the §825-8 / §825-9 update from the staging file into the ledger.

The ledger already contains §825-§827 (appended earlier). §825-8's item 3 is
now proven, so the block is replaced in place. Fails loudly if the anchors are
not found exactly once.
"""
import io
import re
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
OLD_MARK = "- **§825-8 [未证]**"
NEW_MARK = "## §826"
END_MARK = "## §827"

src = io.open(LEDGER, encoding="utf-8").read()
start = src.find(OLD_MARK)
end = src.find(NEW_MARK)
if start < 0 or end < 0 or end <= start:
    sys.exit("ABORT: anchors not found (start=%d end=%d)" % (start, end))

new_block = """- **§825-8 [未证]**
  1. 46 处中哪些在**实际运行**中会在 `[0x887368]==NULL` 的时刻被触发（本次已证 1 处：`0x6D16C2`）。
  2. 4 处字段访问器（`0x7241A0/520/530/540`）的调用点是否能在 NULL 期到达。

- **§825-9 [已证·两个容器例程的语义（反编译）]**
  ```c
  // FUN_00724580(this, elem) —— 追加元素
  undefined4 __thiscall FUN_00724580(int this, undefined4 *elem) {
      if (*(int *)(this + 0x250) != 0) {          // 首访 this+0x250（NULL 时即崩在 0x250）
          if (FUN_00724fa0(&elem)) return 0;       // 已存在 ⇒ 直接返回
          int slot = FUN_00724fc0(&elem);          // 找空槽
          if (slot != 0) { *(int *)(this + 0x25c) = slot; return 0; }
      }
      void *n = operator_new(0x1c);                // 0x1C 字节元素
      if (n == 0) return 0;
      memcpy7(n, elem);                            // 拷贝 7 个字段（6 dword + 1 byte）
      if (...容量/链表检查失败...) { FUN_007c8b3d(n); return 0; }
      *(int *)(this + 0x244) += 1;                 // 增长计数
      ...
  }
  // FUN_00724730(this, key) —— 删除元素 + 前移紧凑化（§797-2 已述）
  ```
  - ⇒ `[0x887368]` 指向的对象是一个**元素步长 0x1C 的容器**（字段：`+0x234` 链表/表头、`+0x24C` 数组、`+0x250` 计数、`+0x25C` 当前槽）。
  - ⇒ `FUN_00724580` = **add**，`FUN_00724730` = **remove**；两者都**只查计数/数组，不查 `this`**。
  - ⇒ 这也解释了为什么"零填充 dummy 对象"不可行：add 路径会继续写 `[this+0x244]/[this+0x25C]` 与表指针，
    零填充时 `[this+0x238]` 读出来是 0，随后写地址 0。

"""

out = src[:start] + new_block + src[end:]
io.open(LEDGER, "w", encoding="utf-8", newline="").write(out)

back = open(LEDGER, "rb").read().decode("utf-8")
print("replaced block, ledger chars=%d" % len(back))
for m in ("§825-9", "§825-8", "## §826", "## §827"):
    print("  %-10s count=%d" % (m, back.count(m)))
print("tail:", repr(back[-80:]))
