#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Insert the 4th trap (it was appended to a later header) and refresh the open-items list."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

# 1) the 4th trap landed under a different header -- move it to the traps list
TRAP4 = """**第四条陷阱（§877-5）**：我给子代理的启发式「1 次 `Items` + 3 次 `Count` = push」**被两次证伪**——
`0x005F3B80` 其实是**析构函数**，`0x007258D0` **根本不改 `Count`**（它是遍历数组、对每个元素调槽 `+0x28` 的死亡广播）。
**方向必须由 `inc`/`dec` 定，不能由「引用了几次」定。**

"""
if TRAP4 in h:
    h = h.replace(TRAP4, "")
    print("removed misplaced trap block")
else:
    print("WARN: misplaced trap block not found")

TRAP_LIST_TAIL = """2. **`TypeDescriptor` 的名字内联在 `TD+0x08`**，不是 `char*`。
   这一点已让**两个独立实现各错一次**（我 §859-3、复核 §868-5）。
   **凡"扫描得到 0 个结果"，必须先怀疑扫描器。**
"""
TRAP_LIST_NEW = TRAP_LIST_TAIL + """3. **有人在枚举报告里写过「`0x008B4108…0x008B417C` 这 20 个 dword 持有 `VectorClass<ObjectClass*>`」**。
   **实测否掉**：全镜像只有 **3 处** `0x007E192C` 存储（`0x0087F778`/`0x00A8E360`/`0x00A8ECB8`），
   `0x008B4108` 收到的是 `0x007E9EA4`（`DynamicVectorClass<UnitClass*>`）。
4. **「形状像」≠「是」**（§877-5）。我给子代理的启发式「1 次 `Items` + 3 次 `Count` = push」被两次证伪：
   `0x005F3B80` 其实是**析构函数**；`0x007258D0` **根本不改 `Count`**（它是遍历数组、
   对每个元素调槽 `+0x28` 的死亡广播）。**方向必须由 `inc`/`dec` 定，不能由「引用了几次」定。**
"""
if h.count(TRAP_LIST_TAIL) == 1:
    h = h.replace(TRAP_LIST_TAIL, TRAP_LIST_NEW)
    print("ok: traps list now 4 items")
else:
    print("WARN: traps tail not unique")

# 2) refresh the stale open-items list
OLD_OPEN = """**新增未闭合**
1. 那 12 个 `AbstractClass*` 数组各自的用途**完全未知**。
2. `0x7241A0` 的 14 个调用点里几个未守卫：**我判 13:1，复核判 7:7，未定谳**（§866）。
3. `ClassDescriptor` 的 `+0x40` 自校验在本镜像**对所有类失败** ⇒ **继承关系无法从 RTTI 验证**。
4. 143 个数组**尚未合并进 `instance_arrays.tsv`**；合并会改变所有下游分母，需单独决定。
"""

NEW_OPEN = """**新增未闭合**
1. 那 **12 个** `AbstractClass*` 数组各自的用途**完全未知**（`0xB0F5B8…0xB0F720`）。
2. `ClassDescriptor` 的 `+0x40` 自校验在本镜像**对所有类失败** ⇒ **继承关系无法从 RTTI 验证**。
3. **140 个数组尚未合并进 `instance_arrays.tsv`**；合并会改变所有下游分母，需单独决定。
4. **`0x006CD8CD` 能否真被触发未知**（需知道 `[0x8871E0]` 何时为 0）——决定它算不算真补丁缺口。
5. **① 的每帧入口仍无锚点**：`case 1` 已排除，真实每帧模拟所在的 `state` 值未定（§873）。
6. `ecx=0` 时静默返回的**语义后果**未证，需交互测试。
7. `0x00421730`（AlphaShapeClass 构造器却 `RemoveItem`）经 vtable 槽到达，**哪个调用点到达它未知**。
"""
if h.count(OLD_OPEN) == 1:
    h = h.replace(OLD_OPEN, NEW_OPEN)
    print("ok: open-items list refreshed")
else:
    print("WARN: open-items block not unique")

io.open(HAND, "w", encoding="utf-8", newline="").write(h)
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("handover size=%d control chars=%d" % (len(h.encode("utf-8")), len(bad)))
