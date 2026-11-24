# W177-G · DISAGREE

| # | 前卡/Lead 表述 | 本卡处置 | 依据 |
|---|---|---|---|
| D1 | W177-F "鼠标全局扫描把光标留在 x=0 → 边缘滚屏/视图漂移" | **不采纳为归因**。W177-F 唯一扫描脚本 `find_mouse_global.py` 的 p1=(1000,450)/p2=(1900,700)，无 `SetCursorPos` 到 x=0；本卡全程 ≥200px 离边、cam 恒 (0,0)，无滚屏。删除该归因 | a-Lead 更正；本卡 `t1a_k10_scan.json`/`t1a_v1_verify.json` cam=(0,0) |
| D2 | W177-F "4 点过定标定，残差 <0.2 格" | **不继承**。a-W177-F 审计：实为 3 点有落盘、近共线（最小高度 15.3px≈0.25 格），第 4 点无记录且等于三点解预测 ⇒ 自由度 0，"过定"不成立。本卡用 hover 全局完全绕开标定 | a-W177-F 审计（Lead 消息）；`HOVER_CELL.md` |
| D3 | "T1b 凸包内标定：由目标格反推屏幕点" | **不适用**。目标格 cx 不在可见域时无屏幕像素可标定；且本卡 hover 全局已证，标定非必需 | Lead 更正；`HOVER_CELL.md` |
| D4 | W177-F 把 `0x88095C` 列为 hover 格"未确认候选" | **坐实为 hover 格全局**：26/26 取格自洽 + `0x6DBECB call 0x5657A0` 直接喂入 | `EVIDENCE/t1a_v1_verify.json`、`work/t1a_xref2.py` |
| D5 | `0x47C620` 拒集 {6,0x24}（W177-E 执行员原值） | **更正为 {6 Building, 0x24 Terrain, 2 Aircraft}**，15/1 一次未比较（引用审计，未独立复验字节）| a-W177-E VERDICT:6,20；本卡标 [静态推断] |
| D6 | "footprint 显绿 ⇒ 该格 can-place 通过" | **不采纳为特异判据**：本卡 (35,85) 显绿足迹但锚点格有红片且落格被拒；颜色只作候选，落格以链 RTTI 为准 | `decisive_d1_hover.png`、a-W177-E VERDICT ★A |
| D7 | "恒 0 / 零跳变"全域断言 | **删除**：改带速率"未观测到"（本卡 try1 75k/s 观测 reentry=0）| 审计 §五.7；`t2_try1_hifreq.jsonl` |
| D8 | coverage 行用非 hex8 入口 | 本卡 `coverage_delta.tsv` entry 全为真实 hex8 函数入口 | `coverage_delta.tsv` |
