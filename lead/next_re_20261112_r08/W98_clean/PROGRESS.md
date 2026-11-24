# W98 PROGRESS（真机三点几何：g_idle / g_near / g_far × 2 趟，observe_sec=150）

FINAL: 2026-11-14T18:11 (+08:00) — 6/6 趟全 VALID_WINDOW ok=True（零崩溃/零残留/真目录零改动/4 锚点 identical/finalize ok=true）。参照带 R(g_far)/R(g_idle)=1.8634 落在 1.7–1.9 内 ⇒ 本批有效。拆分（预注册算法，三角恒等式精确自洽）：总 +16.16 pp（+86.3 %）＝ 交战 11.13 pp（68.9 %）＋ 行军 5.03 pp（31.1 %）；端点敏感性 交战 61.1–79.9 % / 行军 20.1–38.9 %，方向（交战>行军）全部端点不变。caveat：全趟 fg_loss 28–100 %（前台被 IDE 占据），GetThreadTimes 口径不受前台影响且带内复现支撑判读，[未证] 前台独立性，见 SPLIT.md §5 / UNKNOWNS U1。详见 SPLIT.md。

## 环境与预检（2026-11-14 17:46 +08:00）
- `Get-Process gamemd` = 0（启动前空），锁 `lead\next_re_20261112_r08\.game_instance.lock` owner=w98（2026-11-14T17:46:30.110+08:00）。
- 独占机器检查：12 s 窗口 CPU 增长只有桌面宿主自身（DSH GUI 13.2 s / dwm 7.2 s / Antigravity IDE 空闲 ~10.7 s / System 1.7 s），**无 python / agy / 编译类批处理任务**。
- 离线构建 3 包全 PASS：g_idle / g_far（原 C6 几何），g_near（enemy_zone=near：1200 辆最近优先填充，dist_min=1 / dist_max=13 / dist_mean=6.69，Chebyshev 到最近玩家对象）。
- FRESH 沙箱：real_pre 基线断言（647 files / 1989215270 B / 277 maplike / 4 锚点）通过；robocopy 沙箱副本；v0.3 仅在沙箱副本卸载；g_far 安装 verify exit 0（2026-11-14T17:47:19 +08:00）。

## 预注册执行顺序（shuffle seed=98，plan_w98_clean_split.json）
1. trip_g_near_r2
2. trip_g_far_r2
3. trip_g_idle_r2
4. trip_g_idle_r1
5. trip_g_far_r1
6. trip_g_near_r1

## 逐趟记录（batch_runner 自动追加）
- 2026-11-14T17:50:54.488+08:00 trip=trip_g_near_r2 cell=g_near outcome=VALID_WINDOW_target_reached ok=True
- 2026-11-14T17:54:07.159+08:00 trip=trip_g_far_r2 cell=g_far outcome=VALID_WINDOW_target_reached ok=True
- 2026-11-14T17:57:18.810+08:00 trip=trip_g_idle_r2 cell=g_idle outcome=VALID_WINDOW_target_reached ok=True
- 2026-11-14T18:00:29.589+08:00 trip=trip_g_idle_r1 cell=g_idle outcome=VALID_WINDOW_target_reached ok=True
- 2026-11-14T18:03:42.320+08:00 trip=trip_g_far_r1 cell=g_far outcome=VALID_WINDOW_target_reached ok=True
- 2026-11-14T18:06:55.903+08:00 trip=trip_g_near_r1 cell=g_near outcome=VALID_WINDOW_target_reached ok=True
