# W19 / RE-N04h 运行日志（LoadBench U800 CPU 负载对照，单趟）

run_id = NEXT_RE_20261112_R02 · 执行代理 = W19-load-U800-subagent
时区标注：+08:00 为本地，UTC 为探针 stdout 时间戳。

## 时间线
| 时刻 (+08:00) | 事件 |
|---|---|
| 05:45–05:54 | 读 W18 仪器（load_hexbay_probe.py / analyze_hexbay.py / load_hexbay_ui_watch.py 全文）；核对载体（48,745 B、sha ac0881fd…f421e0、[Basic].Name="[2] 0LoadBench U800"、Official=no、MaxPlayer=2、MinPlayer=2、MultiplayerOnly=1、GameMode=standard）；离线逐段计数 [Units,480]=480、[Infantry,320]=320、无 [Structures]；W17 白名单确认索引 96 唯一命中；gamemd 残留=0；基线哈希与 baseline_pre_launch 一致 |
| 05:54–05:55 | 生成 W19 三脚本（复制 W18 + 定向替换 + 手术修改）：load_u800_probe.py / load_u800_ui_watch.py / analyze_u800.py；py_compile 全部通过；read_yrm_carrier 离线自测 S0 守卫 PASS |
| 05:55:04 | WMI 分离启动探针（cmd pid=7244，retval=0，父=WmiPrvSE）；锁 owner=lead → 认领 |
| 05:55:05 | gamemd 启动 pid=41640；S0：残留=0、五文件哈希 match、载体实读 Name/Official/MaxPlayer/声明计数核对 PASS、代码签名@0x55DE4F ok、进程 BELOW_NORMAL 优先级 |
| 05:55:24 | 主菜单就绪（窗口 hwnd=3476078、tid=2124）；初始线程扫 n_threads=32 |
| 05:55:25–05:55:34 | 导航 SinglePlayer→Skirmish→ChooseMap；地图列表 268 条，全列表名称落盘 maplist_names.json；关键词探针命中 [93] U100 / [96] U800；模式 '[2] 0LoadBench U800' **精确唯一命中**，LB_SETCURSEL(96)，UseMap |
| 05:55:38 | 置前成功（此后零输入）；StartGame 点击；观察者独立启动（cmd pid=14180）；timeBeginPeriod(1)=0 |
| 05:55:43 | **首个 frame>0（frame=2，StartGame 后 4.787 s）⇒ 采样计时起点** |
| 05:55:43–05:59:43 | 采样 240.0 s @ 6 ms 目标间隔：fg=True 全程、n_resync=0、自然结束=无、线程数 32→23 |
| 05:59:43 | 采样结束 reason=**target_reached**，有效局内段 240.006 s，seq=40732；结束扫 |
| 05:59:43–05:59:56 | P1 收尾链：停观察者（reason=stop_file，433 行，thread 校验 216/216）→ WM_CLOSE+taskkill 关游戏（最终存活=False）→ 残留=0 → 文件清单 647 项 → 逐字节还原 RA2MD.INI/ddraw.ini/benchbak（全部 byte_identical=True）→ gamemd.exe/ddraw.dll unchanged=True → 锁恢复 owner=lead → meta_end 落盘 |
| 05:59:56 | [MAIN] exit_code=0 pid=41640 map_index=96 display='[2] 0LoadBench U800' phase_stop=target_reached ingame_s=240.006；NDJSON=40,801 行 |
| 06:00–06:05 | analyze_u800.py 运行（analysis.json + tickcost.csv 7,501 行）；结果见 LOAD_U800.md |

## 仪器健康
- 采样拍数 40,732（有效 ok 40,002 + pre/post）；read_status fail=0；窗口线程查询失败=0。
- 实测采样间隔：中位 6.041 ms / p90 6.244 / p99 6.488 / max 19.062，>20 ms 拍 = 0。
- 零输入核对：观察者在局内段 212 次扫描，`last_input` 去重=1（全程无变化）；fg_true=40002/40002。
- 观察者 NtQuery tid 校验 216 OK / 0 失败；state.json 读 270 成功 / 1 失败。
- 观察者停机：stop_file（正常链路）；无孤儿进程；无残留 gamemd。

## 与预设协议的偏差
- 无。单趟、240 s、6 ms、零输入、无重试、无自然结束。
