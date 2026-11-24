# W20 · RUNLOG.md — 全程时间线（本地时间 = UTC+8）

## §0 开工
- 06:04–06:16 环境勘察：锁 owner=lead ✓；载体 175,361 B / sha256 3e3c8745…bfd5b19 ✓；
  离线实读 [Basic].Name="[8] Proving Grounds"、MaxPlayer=8、Structures=52、无 Units/Infantry；
  W19 全列表 268 条中该显示名唯一命中（索引 265）。
- 复用 W19 全链仪器（cycle 自标定 / WMI 脱离 / finally 自愈），生成
  `combat_probe.py` / `combat_ui_watch.py` / `analyze_combat.py`；py_compile 通过。
- 分析器自测：把 W19 真实输出复制到 `W20_combat/selftest/`（只读 W19，写在 W20），
  `--dir selftest` 跑通：med=1.3358 / occ=4.26% 与 W19 原分析完全一致；A8ED50 全零路径、
  [数据不足] 分档正确。自测后清理自测大文件。

## §1 attempt=1 —— 探针缺陷，早期自愈（06:17:03–06:17:18）
- 06:17:03 WMI 分离启动探针 → S0 全绿（哈希/残留/载体）→ WMI 启动 gamemd（pid 35024）。
- 06:17:04.9 `wait_main_menu` 阶段崩溃：`u.EnumChildWindows` 绑定写成 2 参
  （W19 原件为 `[HWND, callback, LPARAM]` 3 参，改写时漏 HWND）→ TypeError。
- **首次 frame>0 之前失败** ⇒ 属卡面允许重试范围；finally 自愈链完整执行：
  06:17:17 关闭 pid 35024（taskkill 两级）→ 残留 0 → 配置逐字节还原（5 文件全 match）→
  锁恢复 owner=lead → meta_end（exit_code=1）。
- 修复：combat_probe.py 绑定补 HWND；06:17:40 重新编译，确认无 gamemd 残留、锁
  owner=lead 后重启（attempt=2）。

## §2 attempt=2 正式趟（06:18:23 起）
- 06:18:23 S0 全绿 → 06:18:2x WMI 启动 gamemd（pid 40188，launcher 14100）→
  is32=True，代码签名 ✓ → 主菜单就绪。
- 06:18:5x 导航：SinglePlayer → Skirmish → ChooseMap（列表 268 条，
  maplist_names.json 落盘）→ `[8] Proving Grounds` 精确唯一命中（索引 265）→ UseMap。
- 06:19:00 **S2b 遭遇战设置枚举**（纯 UI 只读）：117 控件、39 可见 ComboBox；
  **条目文本全部读不到**（owner-draw，CB_GETLBTEXT 空）——仅条目数+索引可读；
  `out/skirmish_settings.json` 落盘。未改任何设置。
- 06:19:00.8 置前（开局阶段最后一次输入）→ StartGame 点击。
- 06:19:01 探针按协议生成观察者（WMI，cmd_pid=34908）；timeBeginPeriod(1)=0。
- 06:19:06.07 首个 frame>0（StartGame 后 5.248 s）⇒ 采样计时起点；6 ms 节拍全程
  **0 次重锚**，实测间隔中位 6.040 ms。

## §3 中途事件（如实记录，全部无键鼠输入）
- 06:19:01 观察者 cmd 启动后**立即退出**（reason=stop_file）：上一趟 finally 遗留的
  `out/watcher_stop.json` 未被新一轮清理 ⇒ 1Hz 观察通道（全线程扫/ctx/last_input/
  natural_end）缺失。主通道（每拍 RPM/cycle/FILETIME）不受影响，采样继续。
- 06:23:44（t≈278 s）**误干预 #1**：本代理为补观察通道手工分离 watcher2 时未传
  隐藏窗口参数，cmd 控制台弹窗**抢走前台**：fg 于 t=284.26 s 转 False（帧循环不受扰，
  31.25 计数/s 不变；fg=False 条件 CPU 后验 +0.4%，见 COMBAT.md）。
- 06:24:0x 发现 watcher2 自身也带同一 EnumChildWindows 绑定缺陷
  （ui_watch.ndjson 95 条 scan_error=TypeError；state.json 停在初始帧）。
- 06:26:2x–06:26:4x 修复动作：
  1) 保全证据副本 `out/ui_watch_broken_watcher.ndjson`（95 条 scan_error）；
  2) 终止 watcher2（python pid 43792；其 cmd 34156 已随之退出）；
     **前台随焦点归还自动回到游戏：t=445.87 s fg 转 True**（伴随一次 96.02 ms、
     df=2 的帧拍滑移单事件，已标注）；
  3) combat_ui_watch.py 绑定补 HWND → 编译通过；
  4) **隐藏窗口方式**（Win32_ProcessStartup ShowWindow=0）分离重启 watcher3
     （cmd_pid=38848）：06:26:48 起 state 正常刷新（23 线程 tids_match，
     sum_all 连续供给，last_input 恒定）。
- 06:23:32（t≈266.4 s）**★ A8ED50 首次非零**（值 1，frame 8327）——探针即时事件
  `a8ed50_first_nonzero` 落盘。

## §4 收尾（06:29:06–06:29:19）
- 06:29:06.14 采样段结束：reason=`target_reached`，有效局内段 **600.006 s**，
  seq=100,805（另 pre_map 相位 + 事件行，NDJSON 共 100,876 行）；natural_end=False
  （对局未自然结束；600 s 到点收尾，符合卡面"不重启补测"）。
- 06:29:18 关闭游戏：WM_CLOSE → taskkill（无 /F）→ taskkill /F → 存活=False。
- 06:29:19 残留核对 = 0；文件清单差分 added/removed/changed = 0/0/0；
  配置逐字节还原自证（RA2MD.INI 被游戏回写 → 还原成功，见 CONFIG_RESTORE.md）；
  timeEndPeriod(1)；观察者（watcher3）经探针 finally 写 stop_file 退出
  （watcher_done.txt reason=stop_file，259 行，thread_ok=129 / fail=0）；
  实例锁恢复 owner=lead；meta_end（exit_code=0）落盘。
- 06:29:19+ `analyze_combat.py` 跑通（含补判读），`analysis.json` + `tickcost.csv`
  （18,750 行）落盘；本报告与 COMBAT/SAFETY/CONFIG_RESTORE/UNCOVERED 落盘。

## §5 产物清单
- `combat_probe.py`（可重跑；含 finally 自愈 + 锁恢复 + S2b 设置枚举）
- `combat_ui_watch.py`（1Hz 只读观察者；含修复后的 EnumChildWindows 绑定）
- `analyze_combat.py`（cycle 自标定 + A8ED50 时间线 + 分段 + 战斗对照 + 四臂对照）
- `out/run.ndjson`（100,876 行）、`out/meta.json`、`out/tickcost.csv`（18,750 行）、
  `out/skirmish_settings.json`、`out/analysis.json`、`out/maplist_names.json`（268 条）、
  `out/ui_watch.ndjson`（watcher3 期）、`out/ui_watch_broken_watcher.ndjson`（缺陷期证据）
- `COMBAT.md` / `SAFETY.md` / `CONFIG_RESTORE.md` / `RUNLOG.md`（本文件）/ `UNCOVERED.md`
- `fg_restore_once.py`（误干预 #1 的备用修复工具；因焦点已自动归还，**未实际执行**）
