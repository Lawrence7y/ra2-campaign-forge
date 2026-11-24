# W177-I · LIVE（真机实测）

> 目标 SHA `73201CC0…F67476`（只读未改）；只读 RPM + 合成键鼠；未写内存/未注入/未改 `ra2youli\`/未联网。

| # | 会话实测 | 结论/证据 |
|---|---|---|
| L0 | 前置 LIVE_LOCK=`W177-I`、无残留 gamemd；基线四文件 SHA+mtime 记于 `work/baseline_before.json` | 与任务给定一致 |
| L1 | 菜单→单人→遭遇战→开始：主菜单需等 Westwood intro 播完(~16s)再点；早点击落在 splash 无效 | `work/full_attempt.py` 修正后 nav 成功 |
| L2 | 首会话 pid 3928：进图 frame 递增，Deploy MCV(D) 后玩家有 NACNST(108,58)，侧栏首槽出现磁能反應爐(NAPOWR) | `EVIDENCE/after_deploy.png` |
| L3 | T1 像素定位：全屏抓→侧栏 x2246..2560 剖面→tile(2272..2400,426..518) 中心(2336,472) | `sidebar_grid.json`，稳定两帧全等 |
| L4 | T2 下单（前台校验通过）：credits 10000→9989→…→9400；limbo NAPOWR 0x147e14e8 t=0.008s 出现 o1=1；tile 进度条 0.6384 变化 | 三层全成立；上轮卡此步失败 |
| L5 | 构建完成后第2次点图标，ghost 举起（红色2×2预览随光标）；`t3_ghost_check.png` | ghost 拾取成功 |
| L6 | 连续会话 pid 23208（单进程 launch→nav→deploy→order→pickup→闭环→落格→采样，避免会话间空闲退出）：全部环节跑通 | `EVIDENCE/full_run.json` |
| L7 | 落格尝试1 anchor(112,61)（旧偏移假设）：frame 667 click，≤3帧原子读，目标格仍 3×InfantryClass 无 BuildingClass；采样 62,943/2.3s/64帧覆盖点击帧 | main_ok=False |
| L8 | 对照实验：同一 ghost 放全绿空格 hover(106,60) → NAPOWR 放置成功 o1=0 cell(105,60) valid；足迹六格 (105..107,60..61) ⇒ 实测偏移 X∈[h−1,h+1] Y∈[h,h+1] | `control_green.json`；证明机制可用、旧偏移假设错 |
| L9 | 落格尝试2 anchor(113,62)（修正偏移，覆盖T(113,63)）：frame 13123 click，frames_elapsed=2（满足≤2帧），目标格仍 3×InfantryClass 无 BuildingClass；采样 64,214/2.3s/27.9k/s/64帧覆盖点击帧 | main_ok=False；预览红格（步兵格 invalid）`t3b_preview_crop.png` |
| L10 | 两次会话中断（空闲退出/焦点被 Chrome 抢），非崩溃：except.txt SHA/mtime 全程未变；已只关闭本卡启动的 pid | 卫生见 `work/baseline_end.json` |

## 实测 vs 静态/前卡
- **一致**：hover 全局 packed CellStruct；0x88095C 事件驱动；相机恒 (0,0)；局内坐标=物理/1.875 铺满全屏（§986）。
- **新证**：T1 像素定位中心 (2336,472)；T2 三层下单首次全成立（突破上轮 0）；NAPOWR 实测足迹 3×2 偏移 [−1..+1,0..+1]；UI 红格拒绝步兵格放置。
- **未兑现**：步兵格落格 0/2（原子读无 BuildingClass）——根因 UI 放置校验（红格），非字节层拒绝；对照空格放置成功。
