# UNKNOWNS.md — S15-K2 未决/未证清单

## U1 · named S 口径仍差 6 条（未达标，如实报）
- 现状 137/158 = 86.71%，DoD 门槛 143（90%）。剩余未具名 `sub_` 行 21 条，其中 5 条有候选但被严格判据剔除（见 U2）。本卡**未编名**补足。

## U2 · 5 条动作候选被严格薄壳判据剔除（保持 `sub_`）
这些行落在某动作 handler 区间内、有语义匹配，但 handler 内还有其它 call（非"唯一 call 薄壳"），不能唯一确定"该函数就是该动作实现"，故不命名、不提级：
- `006D6070` → 疑似 CenterCameraAtWaypoint（动作ID 112）：handler `0x6DF795` 内 6 个 call，且该行全镜像 6+ 调用者（共享 helper）。证据 `T2_verify_promotions.txt`/`T2_strict_filter.txt`。
- `006E1830` → 疑似 PlaySoundEffectAtWaypoint（动作ID 99）：handler `0x6DE845` 内 4 个 call（waypoint 解析 + 声音播放链），该行是 coordinate→cell 子步。证据同上。
- `0070F120` → 疑似 TalkBubble（动作ID 105）：handler `0x6DF588` 内 3 个 call（含两次本行）。
- `0072DDB0` / `0072DEF0` → 疑似 PlayMovie（动作ID 10）：同一 handler `0x6DE72F` 内两个不同 call，二者关系未定（不可都叫 PlayMovie）。

## U3 · 完整字段布局未做
- 6 个核心类已定 RTTI/vtable/GetSize/WhatAmI，但未做"每字段偏移+类型+≥3 读点+写点"的完整表。KB 已证 `TEventClass+0x2C`、Team+0x3C、TagClass+0x90（house/索引）、+0x24/+0x28（字段），但非穷举。调用 `call [reg+disp]` 为虚槽调用，本卡未计入数据字段读点（若后续字段卡需统计须显式报剔除数）。

## U4 · INI 键穷举未做
- 动作实现中触及多个全局（见 `DOD.md` 第 4 条），但未系统列出 S15 相关 INI 键表；INI 键枚举属独立卡。

## U5 · 真机验证未做（本卡静态，理由已述）
- 见 `DOD.md` 第 5 条。触发器派发/GetSize 均可静态定，未申请真机槽。

## U6 · KB 文件未建（按派卡指令）
- S15 现只有老格式 `re_atlas\kb\10_map_triggers.md`；`KB\S15_触发器.md` 由后续 KB 卡创建，本卡只供素材。

## U7 · 盘上 S15 coverage 行数 159 vs PANEL 158
- 多出的 `006E6080`（`TagTypeClass::slot25`，`[静态推断]`）是 atlas 外 P0-GATE 直 vt 入口，不属 atlas 分母。本卡沿用 atlas 分母 158（与 PANEL 一致），该行未纳入本卡 delta。

## U8 · 6 条 COM/多继承 GetSize 教训不适用于本子系统
- S11-K2 发现 Locomotor 族 GetSize 在 `off0 slot9`（非槽 12）。S15 六类均含 AbstractClass（RTTI 已证），GetSize 确在槽 12，`v[11]`=WhatAmI 同为 `B8 imm32 C3` 但已用 AbstractType 枚举值严格区分——本卡无 COM 槽偏移风险。
