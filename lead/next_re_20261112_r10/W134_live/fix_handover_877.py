#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handover: correct the AbstractClass ctor identity (ledger §877)."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

OLD = ("4. **`AbstractClass` 有 4 个 vptr**（§862），\"vptr 在 +0\"只对单继承类成立。\n"
       "   `AbstractClass::AbstractClass` = `0x004101F0`，**28 字节 / 5 条指令 / `n_callees=0` / 不登记**。")

NEW = ("4. **`AbstractClass` 有 4 个 vptr**（§862），「vptr 在 +0」只对单继承类成立。\n"
       "   ⚠️ **§877 更正了函数身份**：真构造器是 **`0x00410170`**（71 字节、**44 个调用者**、\n"
       "   初始化 `+0x10=-1`/`+0x18`/`+0x1C`/`+0x20`/`+0x14` 标志位）。`0x004101F0`（28 字节）\n"
       "   只是「仅装 4 个主虚表」的辅助函数，我原先把它当成了构造器。\n"
       "   **结论不变且更强**：该类 **4 个已验的 vtable 安装点全部 0 引用 `0xB0F720`**\n"
       "   （`0x00410170`/`0x004101C0`/`0x004101F0` 三个 ctor 变体 + `0x004105A0` 标量删除析构器）。\n"
       "   ⇒ 「根类不登记」不再依赖「我把哪个函数认成构造器」这个判断。")

n = h.count(OLD)
if n != 1:
    raise SystemExit("REFUSE: anchor found %d times" % n)
h = h.replace(OLD, NEW)

# append a 5th trap candidate about shape-vs-direction
ANCH = "**两个必须记住的陷阱**"
ADD = """**第四条陷阱（§877-5）**：我给子代理的启发式「1 次 `Items` + 3 次 `Count` = push」**被两次证伪**——
`0x005F3B80` 其实是**析构函数**，`0x007258D0` **根本不改 `Count`**（它是遍历数组、对每个元素调槽 `+0x28` 的死亡广播）。
**方向必须由 `inc`/`dec` 定，不能由「引用了几次」定。**

"""
if h.count(ANCH) == 1 and "第四条陷阱" not in h:
    h = h.replace(ANCH, ADD + ANCH)
    print("ok: 4th trap added")
else:
    print("WARN: trap anchor not unique or already present")

# bump the trap header count
h = h.replace("**两个必须记住的陷阱**", "**必须记住的陷阱**")

io.open(HAND, "w", encoding="utf-8", newline="").write(h)
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("handover size=%d control chars=%d" % (len(h.encode("utf-8")), len(bad)))
