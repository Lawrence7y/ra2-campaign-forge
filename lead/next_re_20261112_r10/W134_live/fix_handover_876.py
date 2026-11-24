#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handover: ②-a settled as genuine NULL; patch list needs 0x6CD8CD added."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

OLD = """1. **`0x7241A0` 有 14 个调用点，不是我原先说的 1 个**（§865）。
   ⚠️ **但 §870 已自我更正：这不造成补丁缺口。** 补丁是**每函数入口挂钩**
   （`entries.json` 6 条 = 6 个函数入口），入口守卫覆盖该函数的**每一次**调用。
   所以 `entries.json` / `stubs.json` / `sites.json` **不需要因这条重建**。
   错的只是我的**统计口径**（把「调用点数」当「补丁面」讨论），不是补丁本身。
   真正待解的仍是两条语义风险：NULL 守卫对**悬空指针**无效；`ecx=0` 时静默返回的后果。
   14 个地址已列出（`0x48CE5D 0x4E1FA9 0x52DB04 0x55D0AB 0x55D173 0x55D202 0x5C4BE3`
   `0x683F61 0x684026 0x685D90 0x6863AF 0x68643E 0x686553 0x69BBA8`）。
"""

NEW = """1. **②-a 的统计与守卫列表都有错，但方案方向是对的**（§865 / §870 / §875 / §876）。

   **已定谳**：真机现场 `Eip:00724737` 的 **`Access address` 一致为 `00000250`** ⇒ `this == 0` ⇒
   **真 NULL，不是悬空指针** ⇒ **`ecx==0` 入口守卫足以拦住这类崩溃**。第三缺陷同理
   （`Eip:006F40A2`，Access `00000155`，`edx=[this+0xAC]==0`）。

   **必须修的三件事**：
   - **`0x724730` 的 30 个调用点全部未守卫**，不是我说的"28+2"。那 4 个所谓"守卫"测的是
     `add eax,0xB0C1C0` 算出的**表指针**（永远非零），而 `this` 在 `test` **之后**才从
     `[0x887368]` 装载。**测了等于没测。**
   - **`0x724580` 不直接碰 `[reg+0x250]`**：它先 `mov eax,[edi]`（参数），再
     `lea esi,[ebx+0x24C]` / `mov eax,[esi+4]` 才到达 `this+0x250`。**`this==0` 同样崩在 ~0x250**，
     只是晚 4 条指令 —— 这反而印证"守卫一个只会平移"。
   - **守卫列表漏了 `0x006CD8CD`**：`mov eax,[0x8871E0]` → `mov ecx,[eax+0x250]`，**无任何守卫**，
     与 6 个已修补例程无关。**这是真实缺口，需补进 `entries.json`。**
     另两个 `0x004FD7A0` / `0x0059A5B0` 形态成立但上游未追；`0x005B32CA` 是虚调用槽
     （`call [edx+0x250]`，崩在地址 **0**），**不是同类**。

   **不需要改的**：`0x7241A0` 的 14 个调用点**不必逐点补**——入口守卫覆盖每一次调用。

   **仍 `[未证]`**：`ecx=0` 时静默返回的语义后果（需交互测试）。
"""

n = h.count(OLD)
if n != 1:
    raise SystemExit("REFUSE: anchor found %d times" % n)
h = h.replace(OLD, NEW)

# overturned table: ②-a row
OLD_R = "| ②-a 修复面 = **50 处 / 6 例程** | **统计错**：`0x7241A0` 有 **14** 个调用点（我只算 1 个）。**但补丁按函数入口挂钩，覆盖不受影响**（§870） | **§865 / §870** |"
NEW_R = ("| ②-a 修复面 = **50 处 / 6 例程** | **统计错且列表不全**：`0x7241A0` 有 **14** 个调用点；"
         "`0x724730` 是 **30 全未守卫**（那 4 个\"守卫\"测的是表指针）；**漏了 `0x6CD8CD`** | "
         "**§865 / §875 / §876** |")
if h.count(OLD_R) == 1:
    h = h.replace(OLD_R, NEW_R)
    print("ok: overturned row updated")
else:
    print("WARN: overturned row not updated")

io.open(HAND, "w", encoding="utf-8", newline="").write(h)
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("handover size=%d control chars=%d" % (len(h.encode("utf-8")), len(bad)))
