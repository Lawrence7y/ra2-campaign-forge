# W177-H · DISAGREE

| # | 前卡/Lead 表述 | 本卡处置 | 依据 |
|---|---|---|---|
| D1 | a-W177-G 初稿 "hover 格=地基原点格" | **不采纳**。lead 紧急更正：地基=hover+(0..2,+1..+2)。本卡 T1 闭环目标改为"地基覆盖目标格"的 anchor，而非目标格本身 | lead 消息 §1/§3；`t2_place.py` ANCHOR=(tx−1.., ty−2..) |
| D2 | HOVER_CELL.md §5 的 J 表 `(ΔX→(+50.85,+28.08), ΔY→(−70.35,+28.34))` | **不沿用**。lead 更正该表算错；本卡用自己两处闭环实测 J=[[0.005,0.015],[−0.01,0.015]]（一致 4/4），迭代以 lead 交叉校验值作先验、在线自适应 | `t1_steps.json`、`t1_goto.py` |
| D3 | W177-G "步兵持续漂移 = 推挤" | **不采纳为本次解释**。lead 更正：最像"点击落空成移动命令"。本卡 3 s 采样步兵 this 集合逐字不变（未观测到移动/推挤），故两说均无本卡证据 | `t2_place.json` push_analysis；PROGRESS C6 |
| D4 | "N/N 通过即证据" | **不采纳**。本卡先测基线（两处 J 复测、回 base ×5 全等、相机每样本复查、200 ms 复核），才宣称 T1 成立 | `t1_steps.json`、`t1_goto_112_56.json` |
| D5 | "1 帧 distinct 也算采样有效" | **不采纳**。T3 强制报 distinct-frames=71，明确 1 帧即判无效 | `t3_summary.json` |
| D6 | "0x88095C 每帧维护" | **按 lead 更正为事件驱动**：单写点 0x4FB3BC（事件队列排空循环）。本卡只断言"读值即光标格"，不声称每帧 | UNKNOWNS U5；CLOSED_LOOP §0 |
| D7 | "落格瞬间不成立即引擎字节拒绝" | **不采纳**。本卡 credits 未扣、无 limbo NAPOWR ⇒ ghost 未举起，属下单层失败，非 `0x47C620` 字节拒绝 | PROGRESS C3/C4；UNKNOWNS U1 |
| D8 | 类名凭外观/偏移猜 | **不采纳**。全程 RTTI `COL+0xC→TD+8`（`dsnap.rtti_name`），读不到 fail-closed；所有 InfantryClass/BuildingClass 判定均 RTTI | `work/dsnap.py`、`t2_place.json` rttiA |
| D9 | "恒 0/零跳变" 全域断言 | **不采纳**。改带速率"未观测到"：34,638/s 下未观测到 BuildingClass 出现、未观测到步兵离开目标格 | PROGRESS C5/C6；LIVE L8 |
