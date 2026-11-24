# S16-PADD · UNKNOWNS

## U1 · Task A（补 named）0 行 —— S16 named 指标仍在悬崖边，本卡未能补 named 余量

S16 两指标均在悬崖边（named 81/90 余量 0；proved 46/90 余量 +1）。本卡 proved 已补 +3（余量 +4），但 **named 未能补余量**：补前 81/90、补后仍 81/90、余量仍 0。

补 named 的全部候选（S16 atlas 内 name 为 `sub_XXXXXXXX` 或 `Xxx::slotN` 的行）共 36 条：
- 9 个 sub_：`00430BA0` `0053A6C0` `0053D8E0` `0053DDA0` `0065E660` `006CE240` `006CE2D0` `006CE320` `0071AB60`（S16_N1 已用掉另 8 个）
- 27 个 slotN：容器族 14 + SuperClass 3 + SuperWeaponTypeClass 4 + TemporalClass 9 中的 slotN 形态行

**两条合法通道全数为 0：**
1. **通道一（YRpp 地址绑定）**：本卡自写扫描器（在 6 个已知正例上验证：53A0E0→SuperClass.h:166、53AE50→:188、6CE270→LocomotionClass.h:213、6CE2C0→Doc、53AF40、595740）扫 YRpp 全部 2275 个文本文件（.h/.cpp/.txt/.html/.source，排除 .png/.gif/.pack），36/36 候选 0 命中（`work/scan_yrpp2.py`）。与 S16_N2 独立一致。
2. **通道二（跨项目独立源）**：S16_N2 已穷 docs/re(403)/re_atlas/kb/台账/CONFLICT_CLASS2 —— 仅 `0065E660` 有 docs/re 名（`SpawnAircraftEdge`），但 (a) docs/re 按 §8.5 主条非合法通道，(b) 该名已被 radar_sweep:64 / MapClass.h:287 归给 `0x4AA440`、归属冲突 fail-closed。

⇒ 无一候选具备 §8.5 要求的异源通道，按「只有一条通道不写 delta」交 0 行。这是硬约束下的结果，非凑数。

## U2 · 关于 D-38 口径
named 81/90 = named(S-R14)（slotN 计入）。若用户裁 D-38(B)（slotN 不计入），S16 named 立刻崩塌（strict 口径现 54/90=60%），本卡 0 行 named 更无补益。按裁决前默认 (A) 报，不擅自改口径。

## U3 · ③b 基率偏高（0.4054）的如实披露
S16 `[静态推断]` 池里 37 行中 15 行过 strict ③b 检测器（多为 E_POINTER/HRESULT 哨兵与 4-槽形状写），基率 40.5% 不低。这意味着「单靠 ③b」在该池内判别力有限；本卡 3 行之所以成立，靠的是 **③b + ② clean RTTI + ④ exact 活 vtable 派发** 的组合，且行数仅 3。不声称 ③b 单独强判别。

## U4 · ④ 的虚函数口径风险（见 DISAGREE D1）
三行 direct call 全为 0（虚函数结构性），④ 只在活 vtable 槽位派发意义上成立。按 D-39 默认：本卡用的是「exact 活 vtable 派发」（构造器装活表 + vt[slot]==entry + site 不共用），与 M32 保留 13 行/S13_K9 白名单 11 行同口径；若审计采 D-39(B) 严格四环（虚函数永不可证），这 3 行应退回 [静态推断]，proved 回 46。该风险如实登记，不隐瞒。
