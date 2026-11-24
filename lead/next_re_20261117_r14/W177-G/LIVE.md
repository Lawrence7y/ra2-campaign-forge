# W177-G · LIVE（实测 vs 静态/前卡）

> 目标 `ra2youli\gamemd.exe` SHA `73201CC0…F67476`（只读）。全程 RPM + 合成输入。

## 一、实测（M2 会话，pid 32280，Deadman's Ridge SE，Libya，10000 credit）
| # | 实测 | 对照 |
|---|---|---|
| L1 | 主菜单→单人→遭遇战→默认配置（Libya/10000/Deadman's Ridge SE，游戏记住上卡配置）→开始；随机出生点，玩家步兵 7 格 (26-36,82-90)、单位 4、无建筑（MCV 未部署） | 与上卡同图不同出生点 ✓ |
| L2 | 选框选中 MCV + D 键 → NACNST 部署成功（RTTI BuildingClass, short=NACNST）；侧栏首图标 `(2328,480)`=NAPOWR（磁能反應堆,600） | 与 W177-F 侧栏坐标一致 ✓ |
| L3 | `.data` 全段 892,665 dword 四点差分，仅 36 dword 随光标变；`0x88095C` 唯一符合格坐标签名（lo +10 on X-move, hi +13 on Y-move, 回 base 精确复位） | W177-F 候选被坐实 ✓ |
| L4 | 细步进 26 点：`dword[0x88095C]` 拆 X/Y，每点取格 `dword[0x87F924]+((Y<<9)+X)*4` 的 `MapCoords(+0x24/+0x26)` 与 (X,Y) 全等（26/26） | 静态 GetCellAt 公式 ✓ |
| L5 | 静态：12 处 `.text` 立即数命中；`0x6DBECB call 0x5657A0` 的实参直接来自 `[0x88095C]`；`0x4FB3BC` 每帧写该全局 | 确认链闭合 ✓ |
| L6 | 闭环定位：以 `0x88095C` 反馈，3 次迭代到 (35,85)，cam 恒 (0,0) | 格空间闭环成立 ✓ |
| L7 | ghost 在 (35,85) 显绿足迹但锚点格有红片；点击后建筑未落该格、留 limbo；改偏移锚点 (34,85) 后 NAPOWR `o1=0/o2=1` 落格、相邻格挂 BuildingClass，但步兵已漂移到 (35,86)/(30,79) | 卡在"同格稳定命中"，非引擎字节拒绝 ✓ |
| L8 | 采样：try1 165,640 样本/75,290/s/distinct=69；click_t=0.4s 前后 hover 恒 (35,85)、cam=(0,0)、reentry(0xA8E7AC)=0（未观测到翻转，带速率表述）| 满足 T3 ≥5k/s + distinct自检 ✓ |

## 二、实测 vs 静态/前卡
- **一致**：取格公式 `(Y<<9)+X`/stride 4/MapCoords 自洽（S12-Q2）；GetCellAt `0x5657A0`（W177-F/VERDICT）；拒集不含 15/1（W177-E 审计）；跨类共链可能性（W177-E try5）。
- **新证**：hover 格全局 `0x88095C` = packed CellStruct（前卡仅列为未确认候选）；W177-F 曾把 `0x88095C` 差分命中但归因边缘滚屏——本卡证明该归因无据（脚本无 x=0，见 DISAGREE）。
- **未兑现**：建筑+步兵同格链 0 次；非字节层拒绝，因锚点红 + 步兵漂移双因。
