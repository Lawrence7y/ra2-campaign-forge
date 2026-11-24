# RUNLOG · W15 RE-N04e

run_id `NEXT_RE_20261112_R02` ｜ 时区 Asia/Shanghai ｜ 写域 `W15_tick_cpu\`

## 时间线

| 时刻 | 事件 |
|---|---|
| 04:14–04:26 | 开工：读锁（owner=lead）、无 gamemd 残留、基线/载体核对；写 `tick_cpu_probe.py`、`tick_ui_watch.py` |
| 04:26–04:33 | 仪器自测：编译 ×3；绑定测试（GetThreadTimes/QueryThreadCycleTime/NtQuery 布局 x64 校验通过）；**发现 2 个仪器事实**——(a) 本机 `Thread32First` 要求 dwSize=28（SDK 文档 24），已补尾随字段；(b) 6 ms 采样下窗口线程 ΔCPU 非零值 distinct={15.625}——**记账量子=15.625 ms**。全线程扫移至观察者进程（Toolhelp 全系统 ~7,639 线程迭代 ≈5 ms，留采样循环会污染 6 ms 节奏）。tkinter 窗口枚举验证 EnumChildWindows 绑定 |
| 04:33:05 | **attempt1** WMI 启动探针（launcher pid 39916）：S0 守卫全过、游戏启动成功（pid 31576） |
| 04:33:07 | attempt1 **崩溃**：`EnumChildWindows` argtypes 缺参（转录笔误）→ TypeError。**自愈链完整执行**：停观察者→关游戏（taskkill /F /PID 31576 rc=0）→残留 0→配置逐字节还原自证→meta_end(exit_code=1)→锁恢复 lead。副产品：taskkill 的 GBK 输出崩 utf-8 读线程（已修：capture bytes + errors=replace） |
| 04:33–04:36 | 修复：EnumChildWindows 绑定（探针+观察者）、taskkill/WMI 子进程解码加固、meta 字段；编译+绑定复测全绿 |
| 04:36–04:40 | 分析器 `analyze_tickcost.py` 编写 + **合成数据自测**：抓出 3 个 bug 并修复——(1) 归属基线滚成"最近 ok 采样"导致逐样本差（interval=6ms 假象），改为**只在递增事件上推进**；(2) occupancy ms→s 单位错 ×1000；(3) med=0 时 falsy 打印。修复后合成指标全部合理 |
| 04:42:26 | **attempt2** WMI 启动探针（launcher pid 41208 → probe python 39128） |
| 04:42:27–04:42:56 | S0 守卫全过（残留 0、5 文件哈希 match、载体 match）；S1 主菜单就绪；线程仪器就绪（菜单相位 32 线程、sum_cpu 16546.9 ms）；**GetProcessTimes 一次性探测：两种句柄权限均 ok=true**（k=8750/u=7843.75 ms）——与 Lead 早前"同权限返回 False"的观察矛盾，如实记录；S2 导航：地图列表 268 条，`Proving Grounds` 命中 1 → **索引 265 `[8] Proving Grounds`** |
| 04:43:00 | S3 置前成功 → StartGame 点击（最后输入） |
| 04:43:01 | 观察者 WMI 启动（cmd 42228）——**因 attempt1 遗留的陈旧 `watcher_stop.json` 首循环即退出**（当时未察觉） |
| 04:43:06 | 首个 frame>0（frame=2，StartGame 后 5.314 s）⇒ 采样起点 |
| 04:43–04:45 | 采样 0–120 s：fg=True，n_resync=0，win_cpu 平稳爬升（24171.9→30640.6 ms 累计） |
| 04:45:05–04:45:11 | 发现观察者死亡（sum_all/n_th=null）→ 根因=陈旧 stop 文件 → **救援**：删 stop 文件 + WMI 重启观察者（--pid 40244）→ 1 Hz 正常（23 线程、NtQuery tid 校验 True） |
| 04:45:35.8 | **t=148.83 s 焦点丢失 ×1**（frame 4653，fg True→False 至段末；非键鼠输入，归因未定） |
| 04:47:06 | t=240 s `target_reached`，采样结束；探针终扫（23 线程 sum 54937.5 ms） |
| 04:47:18 | 收尾：WM_CLOSE 无效窗口句柄（对局中）→ taskkill /PID 40244（无 /F）rc=0 → /F rc=0 → 存活=False；救援观察者见 stop 文件退出（等待 0.0 s） |
| 04:47:19 | 残留 0；清单 647 项、diff 全零；配置逐字节还原自证 5/5；**锁恢复 owner=lead**；meta_end（exit_code=0）；NDJSON 40,887 行 |
| 04:48–04:52 | 离线分析（`analyze_tickcost.py`）+ 本报告族 |

## 关键计数（attempt2）
- 采样：40,871 拍（局内 ok 40,001，fail 0，win-thread fail 0，n_resync 0）
- 递增事件：7,501（df1 7,500 + df2 1 个边界事件）
- 观察者（救援后）：81 次扫描 / 81 次全线程扫 / NtQuery 校验全过 / open·query 失败 0
- 探针自身扫：菜单初扫 + 终扫（meta n_sweeps=2）

## 产物
`tick_cpu_probe.py`、`tick_ui_watch.py`、`analyze_tickcost.py`（可重跑）、
`out\run.ndjson`、`out\meta.json`、`out\ui_watch.ndjson`、`out\analysis.json`、
`out\tickcost.csv`、`probe_live_stdout.txt`、`probe_stdout.txt`、`watcher_live_stdout2.txt`、
`TICK_COST.md`、`SAFETY.md`、`CONFIG_RESTORE.md`、`UNCOVERED.md`、本文件。
