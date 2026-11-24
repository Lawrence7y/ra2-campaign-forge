#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix the two remaining stale 0x006DD8B0 statements in the handover."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

# line ~94 block (inside the 0'.4 section)
OLD_A = ("> `0x006DD8B0` 逐帧遍历的多组全局里，**`DAT_00a8eb44` 是\"对象指针数组基址\"，`DAT_00a8eb50` 是其计数**；\n"
         "> 另有 `DAT_00a8eaf8`/`DAT_008b3dd0`/`DAT_00a8ec88`/`DAT_00a80218`/`DAT_00a83df8` 等列表上界。\n"
         "> ⇒ 这解释了旧台账 §707 的\"格链不登记单位（213 vs 设计 1500）\"——**单位不在格链上，在这些全局数组里**。\n"
         "> ⇒ **`[未证]`**：数组元素类型、容量上限、与子弹容器 `0xA8ED3C` 的关系，**均未真机验证**。")
NEW_A = ("> `0x006DD8B0`（现已知是 **TAction 执行器**，见 §880）里引用的多组全局中，\n"
         "> **`DAT_00a8eb44` 是 `BuildingClass::Array.Items`，`DAT_00a8eb50` 是它的 Count**；\n"
         "> 另有 `DAT_00a8eaf8`=Trigger、`DAT_008b3dd0`=Foot、`DAT_00a8ec88`=Techno、\n"
         "> `DAT_00a80218`=ParticleSystem、`DAT_00a83df8`=Infantry 各自的 Count。\n"
         "> ⇒ 这些是**按类型分表的实例容器**，不是\"单位主表\"。\n"
         "> ⇒ **本项目真正的\"单位列表\"是 `UnitClass::Array` @ `0x008B4108`。**")
if h.count(OLD_A) == 1:
    h = h.replace(OLD_A, NEW_A); print("ok: line-94 block replaced")
else:
    print("WARN: line-94 block found %d times" % h.count(OLD_A))

# line ~182 statement
OLD_B = ("**结论**：`0x006DD8B0`（状态机分派器）遍历的不是\"单位列表\"，而是**六种不同类型数组**；\n"
         "项目一直在找的\"单位列表\"是 `UnitClass::Array` @ `0x008B4108`。")
NEW_B = ("**结论**：`0x006DD8B0` **不是主循环**（§880：它是 `TActionClass` 执行器），它所引用的那些全局\n"
         "是**按类型分表的实例容器**，不是\"单位主表\"；\n"
         "项目一直在找的\"单位列表\"是 `UnitClass::Array` @ `0x008B4108`。")
if h.count(OLD_B) == 1:
    h = h.replace(OLD_B, NEW_B); print("ok: line-182 statement replaced")
else:
    print("WARN: line-182 statement found %d times" % h.count(OLD_B))

io.open(HAND, "w", encoding="utf-8", newline="").write(h)
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("handover size=%d control chars=%d" % (len(h.encode("utf-8")), len(bad)))
