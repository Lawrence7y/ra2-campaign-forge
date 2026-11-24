# W177-H · LIVE（真机实测）

> 目标 SHA `73201CC0…F67476`（只读未改）。只读 RPM + 合成输入；未写内存/未注入/未改 `ra2youli\`/未联网。

| # | 会话实测 | 对照/结论 |
|---|---|---|
| L1 | 前置：LIVE_LOCK=`W177-H`；无残留 gamemd；`gamemd.exe` SHA=`73201CC0…F67476`/4,825,360 B，`except.txt` SHA=`6907F395…91094`，`ddraw.dll`/`ddraw.ini` 基线记于 `work/baseline_before.json` | 与任务给定一致 |
| L2 | 菜单进游戏：主選單→單人遊戲→遭遇戰→開始遊戲；发现游戏菜单空闲 ~54 s 自行退出，改用 DETACHED_PROCESS 启动 + 逐步截图导航；最终 pid 3452 进图（frame 从 0 递增到 18k+） | 导航坑已记录 UNKNOWNS U1 |
| L3 | 第一会话 pid 19960：Deadman's Ridge SE / Libya / 10000 / Deadman's Ridge SE，frame=635 起，cam=(0,0)；单位/步兵在 (105-113,55-63)；T1 在此完成 | 与 W177-G 同图、随机出生点不同 |
| L4 | T1 步长两处复测：anchor (1000,600) 与 (1400,800) 导出 J 逐项相等（X+200→Δ(+1,−2)、Y+200→Δ(+3,+3)、回 base ×5 全等）；cam 恒 (0,0) | `t1_steps.json`，4/4 一致 |
| L5 | T1 闭环：从 (108,64) 5 次迭代到 hover (112,56)=E(0,0)，200 ms 复核全等、cam=(0,0)、frame=7003；cursor 全程 screen(1000..1728, 480..609) 在安全区 | `t1_goto_112_56.json`，硬门槛达成 |
| L6 | 第二会话 pid 3452（重启求 MCV 出生点）：框选中心白色载具(screen 680,480→cell 31,85)+D → NACNST 落 (30,84) 于我 house，侧栏首图标出现 磁能反應爐(NAPOWR) | MCV 部署成功（本会话曾建 yard） |
| L7 | T2 尝试 target=(31,89) anchor=(30,87) 与 target=(27,85) anchor=(26,83)：两处下沉闭环 E=0、cam=(0,0)、hover 精确；但下单图标点击后 credits 恒 10000、建筑数组无 limbo NAPOWR；落格瞬间(≤2帧)目标格链均 3×InfantryClass 无 BuildingClass | 运行时未兑现 0/2，非字节拒绝 |
| L8 | T3 专用采样：83,847 样本 / 2.42 s / 34,638/s / distinct-frames=71（frame 16177..16253）；目标格(27,85)链全程 3×InfantryClass，RTTI 缓存 3 个 this 全 `.?AVInfantryClass@@` | 满足 ≥5k/s + 多帧，1 帧无效条款通过 |

## 实测 vs 静态/前卡

- **一致**：hover 格全局 0x88095C packed CellStruct（W177-G）、地基偏移 (0..2,+1..+2)（a-W177-G 更正）、0x47C620 拒集不含 15/1（前卡字节证）、相机 0x886FA0/4 读值恒 (0,0)。
- **新证**：步长两处复测 4/4（任务要求"复测一致才采信"）；T1 闭环 5 步收敛 + 200 ms 复核；菜单 54 s 退出 + 焦点偷取导致 hover 停更（前卡未记录）；T3 34.6k/s 全量落盘。
- **未兑现**：落格瞬间同格 0/2；根因是下单图标点击未生效（credits 未扣、无 limbo），非 0x47C620 字节拒绝、非推挤。
