# W164 UNKNOWNS（分级未证清单）

## [未证] · 需真机
1. **两趟图（range1 / c2_near，各 1500 MTNK）的运行期 `AbstractClass::Array.Count`**。§887 的 69 对象是另一张 12 单位小图，不能套用。⇒ Q4 数量级判别的唯一缺口（§14.3）。取法：harness 每帧读 `[0x00B0F730]`。
2. **"移动中对象数"**：遍历 LogicClass 向量统计 `[loco+0x54]!=-1 && [loco+0x5F]!=0` 的对象数。取法见报告 Q5 证据 1。
3. **节流除数 N** = `[0x8871E0 + 0x1808]` 的运行期值。`0x8871E0` 静态读回 0（运行时指针），未追其初始化点。
4. **`0x4B066C` 分支之后**：门A/门B 命中跳转后的目标，是否立即 ret / 走多轻量的出口。首段 wrapper 有多个 early-return（如 `0x4B058C je 0x4B0AC2`）佐证是轻量出口，但未逐字节追到 `0x4B066C`。
5. **`[loco+0x5F]` 的确切语义**：字节标志，推断为"移动态/有路径"，未从写入点反查其语义（FIELD_LAYOUT 记 Movement_Locomotion +0x5F 写 6 次）。
6. **`[obj+0x90]`（FootClass::AI 总门）语义**：推断为对象活跃/在册标志（与 §6.1 的 +0x98 "在册"标志相邻但不同）。

## [未证] · 静态可继续
7. 其余 Locomotion 子类（Jumpjet/Teleport/Rocket/Tunnel/DropPod/Fly）的槽16 wrapper 是否最终也调 `0x4D3920`（本卡只对 Drive/Walk/Hover/Ship/Mech 验到直接 callee；其余深度调用未查）。
8. `0xFFF7`=65527 在 SearchCore 中的具体消费点（承接台账 §562-4；本卡未下钻）。
9. `+0xE4/+0xE8` 非栈写按题设口径（93 处/38 函数）的逐函数去栈归类——本卡只给总数 99。
10. `0x8871E0` 单例身份（可能是 RulesClass，+0x1808 字段含义未知）。

## [静态推断] · 有证据但未实机确认
11. 缓存式寻路：目标 cell 未变（UpdatePathfinding 内 `sStack_1c==DAT_8B3D88 && sStack_1a==DAT_8B3D8A`）时不重算。
12. 普通单位移动的格表更新 O(1)（挂/摘链 + 读 0x87F924 取基址）；O(半径²) 只在多格建筑的 footprint 重算。

## 已排除（负结果，也是交付）
- **[已证]** "成本来自固定 AI 开销"：1500×~3.8 µs ≈ 5.7 ms ≪ 101 ms，固定开销不主导。
- **[已证]** "Locomotion 的 +0x5C 是每帧更新槽"：调用约定不符（stdcall ret 4 vs thiscall），实际更新槽是 +0x40。
- **[已证]** 大 Process（0x4B2630 等）不在任何虚表（全 .rdata 字节扫描 0 命中）——它们是内部 callee，不是虚表槽直指。
