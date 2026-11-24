# RUNLOG.md —— 过渡态 S_sleep 复现执行日志

- run_id: `NEXT_RE_20261112_R02`
- 开始(UTC): `2026-11-12T16:59:04.156064+00:00`；结束(UTC): `2026-11-12T17:01:00.715879+00:00`；本地: `2026-11-13T01:01:14.005112+08:00`
- 退出码: **0**
- 命令: `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -X utf8 D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W6_transition\transition_probe.py `
- Python: `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe` / `3.12.10`
- pid=4460 tid(c0)=41576 self_tid=37084 is32=True walker_ok=True
- 实例锁：开工 owner=W6-transition-subagent → 收尾恢复 owner=lead。

## 1. 参数

```json
{
 "budget_ms": 50.0,
 "grab_cap_per_phase": 3,
 "grab_cap_total": 22,
 "grab_cooldown_s": 2.5,
 "interval_ms": 30.0,
 "map_pattern": "Proving Grounds",
 "r2_event_budget_ms": 300.0,
 "stall_threshold_s": 1.0,
 "ui_interval_ms": 500.0
}
```

## 2. 相位摘要

| phase | stop | 时长(s) | 样本 | frame 首→末 | 抓栈 |
|---|---|---|---|---|---|
| P0_intro | True | 18.663 | 617 | 0→0 | （无） |
| P0_menu_idle | timeout | 12.016 | 391 | 0→0 | G01、G02、G03 |
| W_A_load | stable_10.0s | 15.037 | 493 | 0→315 | G04、G05 |
| W_A_ingame | timeout | 13.088 | 431 | 315→724 | G06 |
| W_B_esc_menu | True | 0.218 | 9 | 730→730 | （无） |
| W_B_confirm_click | skirmish_screen | 3.01 | 99 | 730→0 | G07 |
| idle_after_exit | timeout | 15.019 | 491 | 0→0 | G08、G09、G10 |
| W_D_load | stable_10.0s | 13.031 | 427 | 0→314 | G11、G12 |
| W_D_ingame | timeout | 11.105 | 365 | 314→661 | G13 |

## 3. 相位事件时间线（节选）

- `2026-11-12T16:59:05.970641+00:00` [P0_intro] 开始（timeout=120s ui=0.30s）
- `2026-11-12T16:59:24.637316+00:00` [P0_intro] 结束 stop=True dur=18.7s n=617 frame 0→0 grabs=[]
- `2026-11-12T16:59:24.637316+00:00` [P0_menu_idle] 开始（timeout=12s ui=0.50s）
- `2026-11-12T16:59:24.641343+00:00` [P0_menu_idle] 抓栈 G01 开始 tid=41576 原因=menu_idle_stall frame=0
- `2026-11-12T16:59:27.240606+00:00` [P0_menu_idle] 抓栈 G02 开始 tid=41576 原因=menu_idle_stall frame=0
- `2026-11-12T16:59:29.857950+00:00` [P0_menu_idle] 抓栈 G03 开始 tid=41576 原因=menu_idle_stall frame=0
- `2026-11-12T16:59:36.656666+00:00` [P0_menu_idle] 结束 stop=timeout dur=12.0s n=391 frame 0→0 grabs=['G01', 'G02', 'G03']
- `2026-11-12T16:59:49.841291+00:00` [W_A_load] 已点击 GUI:StartGame，从点击瞬间开始密集采样
- `2026-11-12T16:59:49.841291+00:00` [W_A_load] 开始（timeout=180s ui=0.50s）
- `2026-11-12T16:59:49.845825+00:00` [W_A_load] 抓栈 G04 开始 tid=41576 原因=load_transition_stall frame=0
- `2026-11-12T16:59:52.458804+00:00` [W_A_load] 抓栈 G05 开始 tid=41576 原因=load_transition_stall frame=0
- `2026-11-12T17:00:04.879893+00:00` [W_A_load] 结束 stop=stable_10.0s dur=15.0s n=493 frame 0→315 grabs=['G04', 'G05']
- `2026-11-12T17:00:04.879893+00:00` [W_A_ingame] 开始（timeout=5s ui=0.50s）
- `2026-11-12T17:00:09.882447+00:00` [W_A_ingame] 结束 stop=timeout dur=5.0s n=166 frame 315→471 grabs=[]
- `2026-11-12T17:00:09.883695+00:00` [W_A_ingame] 抓栈 G06 开始 tid=41576 原因=N0_normal_ingame_contrast frame=471
- `2026-11-12T17:00:09.962927+00:00` [W_A_ingame] 开始（timeout=8s ui=0.50s）
- `2026-11-12T17:00:17.971431+00:00` [W_A_ingame] 结束 stop=timeout dur=8.0s n=431 frame 315→724 grabs=['G06']
- `2026-11-12T17:00:18.256508+00:00` [W_B_esc_menu] 开始（timeout=6s ui=0.20s）
- `2026-11-12T17:00:18.260100+00:00` [W_B_esc_menu] 结束 stop=True dur=0.0s n=1 frame 730→730 grabs=[]
- `2026-11-12T17:00:18.261609+00:00` [W_B_esc_menu] 点击 'GUI:AbortMission' hwnd=5969202 -> True
- `2026-11-12T17:00:18.261609+00:00` [W_B_esc_menu] 开始（timeout=6s ui=0.20s）
- `2026-11-12T17:00:18.477113+00:00` [W_B_esc_menu] 结束 stop=True dur=0.2s n=9 frame 730→730 grabs=[]
- `2026-11-12T17:00:18.479145+00:00` [W_B_confirm_click] 点击候选 pos=0 prio=1 text='GUI:Blank' hwnd=17567346 -> True
- `2026-11-12T17:00:18.479145+00:00` [W_B_confirm_click] 开始（timeout=3s ui=0.20s）
- `2026-11-12T17:00:18.511084+00:00` [W_B_confirm_click] 结束 stop=dialog_gone dur=0.0s n=2 frame 730→730 grabs=[]
- `2026-11-12T17:00:18.511084+00:00` [W_B_confirm_click] 开始（timeout=25s ui=0.30s）
- `2026-11-12T17:00:19.268684+00:00` [W_B_confirm_click] 抓栈 G07 开始 tid=41576 原因=confirm_click_stall frame=730
- `2026-11-12T17:00:21.493409+00:00` [W_B_confirm_click] 结束 stop=skirmish_screen dur=3.0s n=99 frame 730→0 grabs=['G07']
- `2026-11-12T17:00:21.496422+00:00` [idle_after_exit] 开始（timeout=15s ui=0.50s）
- `2026-11-12T17:00:21.892415+00:00` [idle_after_exit] 抓栈 G08 开始 tid=41576 原因=menu_idle_stall frame=0
- `2026-11-12T17:00:24.508615+00:00` [idle_after_exit] 抓栈 G09 开始 tid=41576 原因=menu_idle_stall frame=0
- `2026-11-12T17:00:27.102024+00:00` [idle_after_exit] 抓栈 G10 开始 tid=41576 原因=menu_idle_stall frame=0
- `2026-11-12T17:00:36.518487+00:00` [idle_after_exit] 结束 stop=timeout dur=15.0s n=491 frame 0→0 grabs=['G08', 'G09', 'G10']
- `2026-11-12T17:00:36.575916+00:00` [W_D_load] 第二次 StartGame，开始密集采样
- `2026-11-12T17:00:36.575916+00:00` [W_D_load] 开始（timeout=180s ui=0.50s）
- `2026-11-12T17:00:36.580289+00:00` [W_D_load] 抓栈 G11 开始 tid=41576 原因=load_transition_stall2 frame=0
- `2026-11-12T17:00:39.175731+00:00` [W_D_load] 抓栈 G12 开始 tid=41576 原因=load_transition_stall2 frame=0
- `2026-11-12T17:00:49.609718+00:00` [W_D_load] 结束 stop=stable_10.0s dur=13.0s n=427 frame 0→314 grabs=['G11', 'G12']
- `2026-11-12T17:00:49.609718+00:00` [W_D_ingame] 开始（timeout=5s ui=0.50s）
- `2026-11-12T17:00:54.615399+00:00` [W_D_ingame] 结束 stop=timeout dur=5.0s n=166 frame 314→471 grabs=[]
- `2026-11-12T17:00:54.615399+00:00` [W_D_ingame] 抓栈 G13 开始 tid=41576 原因=N1_normal_ingame_contrast frame=471
- `2026-11-12T17:00:54.709685+00:00` [W_D_ingame] 开始（timeout=6s ui=0.50s）
- `2026-11-12T17:01:00.715879+00:00` [W_D_ingame] 结束 stop=timeout dur=6.0s n=365 frame 314→661 grabs=['G13']

## 4. stdout（首 80 行 + 尾 80 行，完整见 out/stdout.txt）

```text
2026-11-12T16:59:04.156064+00:00 [S0] 实例锁 + 残留进程 + 哈希守卫
2026-11-12T16:59:04.156064+00:00     实例锁 owner 状态 = lead_free（接管）
2026-11-12T16:59:04.164374+00:00     只读资产加载完成（W1 导航 / r2 采样器 / e3_stackwalker）
2026-11-12T16:59:04.177599+00:00     RA2MD.INI                1754 c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d match=True
2026-11-12T16:59:04.177599+00:00     ddraw.ini               14782 c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52 match=True
2026-11-12T16:59:04.177599+00:00     RA2MD.INI.benchbak       1754 c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d match=True
2026-11-12T16:59:04.181903+00:00     gamemd.exe            4825360 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476 match=True
2026-11-12T16:59:04.182409+00:00     ddraw.dll              411648 85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9 match=True
2026-11-12T16:59:04.573871+00:00     启动前文件清单 647 项
2026-11-12T16:59:04.575372+00:00     基准 7 帧：ntdll+0x7858c → kernelbase+0x16a1f0 → kernelbase+0x16a18f → gamemd+0x207f17 → user32+0x74775 → user32+0x3505d → gamemd+0x20833f
2026-11-12T16:59:04.575372+00:00 [S1] WMI 分离启动 gamemd.exe
2026-11-12T16:59:05.965614+00:00     pid=4460 归属=wmi_child_parent_pid launcher_pid=14892
2026-11-12T16:59:05.965614+00:00     is32=True 代码签名@0x55DE4F ok=True
2026-11-12T16:59:05.965614+00:00 [S2] 挂起任何线程之前完成 StackWalk64/符号初始化
2026-11-12T16:59:05.968129+00:00     walker ok n_modules=90 max_frames=20 raw_bytes=65536
2026-11-12T16:59:05.969136+00:00     游戏窗口 hwnd=[8917116] tid=41576
2026-11-12T16:59:05.970641+00:00 [P0_intro] 开始（timeout=120s ui=0.30s）
2026-11-12T16:59:24.637316+00:00 [P0_intro] 结束 stop=True dur=18.7s n=617 frame 0→0 grabs=[]
2026-11-12T16:59:24.637316+00:00 [P0_menu_idle] 开始（timeout=12s ui=0.50s）
2026-11-12T16:59:24.641343+00:00 [P0_menu_idle] 抓栈 G01 开始 tid=41576 原因=menu_idle_stall frame=0
2026-11-12T16:59:24.723441+00:00     抓栈 G01  tid=41576 bits=32 prev=0 frames=6 usable=True held=6.349ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=20480 key_on_raw=4/4
2026-11-12T16:59:24.723441+00:00       #0 ntdll.dll+0x7858c            addr=0x77c1858c
2026-11-12T16:59:24.723441+00:00       #1 KERNELBASE.dll+0x16a1f0      addr=0x763fa1f0
2026-11-12T16:59:24.723441+00:00       #2 KERNELBASE.dll+0x16a18f      addr=0x763fa18f
2026-11-12T16:59:24.723441+00:00       #3 gamemd.exe+0x207f17          addr=0x607f17
2026-11-12T16:59:24.723441+00:00       #4 USER32.dll+0x2922e           addr=0x7791922e
2026-11-12T16:59:24.723441+00:00       #5 USER32.dll+0x3505d           addr=0x7792505d
2026-11-12T16:59:24.723441+00:00     抓栈 G01 判定=S_sleep_hit wall=82.2ms frames=ntdll+0x7858c → kernelbase+0x16a1f0 → kernelbase+0x16a18f → gamemd+0x207f17 → user32+0x2922e → user32+0x3505d
2026-11-12T16:59:27.240606+00:00 [P0_menu_idle] 抓栈 G02 开始 tid=41576 原因=menu_idle_stall frame=0
2026-11-12T16:59:27.338518+00:00     抓栈 G02  tid=41576 bits=32 prev=0 frames=4 usable=True held=2.086ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=16384 key_on_raw=1/4
2026-11-12T16:59:27.338518+00:00       #0 win32u.dll+0x11ac            addr=0x766911ac
2026-11-12T16:59:27.338518+00:00       #1 USER32.dll+0xc7f51           addr=0x779b7f51
2026-11-12T16:59:27.338518+00:00       #2 DDRAW.dll+0x22b06            addr=0x54832b06
2026-11-12T16:59:27.338518+00:00       #3 gamemd.exe+0x13eb1c          addr=0x53eb1c
2026-11-12T16:59:27.338518+00:00     抓栈 G02 判定=third_signature:gamemd+0x13eb1c wall=97.1ms frames=win32u+0x11ac → user32+0xc7f51 → ddraw+0x22b06 → gamemd+0x13eb1c
2026-11-12T16:59:29.857950+00:00 [P0_menu_idle] 抓栈 G03 开始 tid=41576 原因=menu_idle_stall frame=0
2026-11-12T16:59:29.957456+00:00     抓栈 G03  tid=41576 bits=32 prev=0 frames=4 usable=True held=2.657ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=16384 key_on_raw=1/4
2026-11-12T16:59:29.957456+00:00       #0 win32u.dll+0x11ac            addr=0x766911ac
2026-11-12T16:59:29.957456+00:00       #1 USER32.dll+0xc7f51           addr=0x779b7f51
2026-11-12T16:59:29.957456+00:00       #2 DDRAW.dll+0x22b06            addr=0x54832b06
2026-11-12T16:59:29.957456+00:00       #3 gamemd.exe+0x13eb1c          addr=0x53eb1c
2026-11-12T16:59:29.957456+00:00     抓栈 G03 判定=third_signature:gamemd+0x13eb1c wall=99.5ms frames=win32u+0x11ac → user32+0xc7f51 → ddraw+0x22b06 → gamemd+0x13eb1c
2026-11-12T16:59:36.656666+00:00 [P0_menu_idle] 结束 stop=timeout dur=12.0s n=391 frame 0→0 grabs=['G01', 'G02', 'G03']
2026-11-12T16:59:36.656666+00:00 [W_A] 导航 SinglePlayer → Skirmish → 选图 → StartGame
2026-11-12T16:59:49.785464+00:00     地图：index=265 name='[8] Proving Grounds'
2026-11-12T16:59:49.841291+00:00 [W_A_load] 已点击 GUI:StartGame，从点击瞬间开始密集采样
2026-11-12T16:59:49.841291+00:00 [W_A_load] 开始（timeout=180s ui=0.50s）
2026-11-12T16:59:49.845825+00:00 [W_A_load] 抓栈 G04 开始 tid=41576 原因=load_transition_stall frame=0
2026-11-12T16:59:49.940443+00:00     抓栈 G04  tid=41576 bits=32 prev=0 frames=4 usable=True held=1.881ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=20480 key_on_raw=2/4
2026-11-12T16:59:49.940443+00:00       #0 ntdll.dll+0x7858c            addr=0x77c1858c
2026-11-12T16:59:49.940443+00:00       #1 KERNELBASE.dll+0x16a1f0      addr=0x763fa1f0
2026-11-12T16:59:49.940443+00:00       #2 KERNELBASE.dll+0x16a18f      addr=0x763fa18f
2026-11-12T16:59:49.940443+00:00       #3 gamemd.exe+0x207f17          addr=0x607f17
2026-11-12T16:59:49.940443+00:00     抓栈 G04 判定=S_sleep_hit wall=94.9ms frames=ntdll+0x7858c → kernelbase+0x16a1f0 → kernelbase+0x16a18f → gamemd+0x207f17
2026-11-12T16:59:52.458804+00:00 [W_A_load] 抓栈 G05 开始 tid=41576 原因=load_transition_stall frame=0
2026-11-12T16:59:52.542903+00:00     抓栈 G05  tid=41576 bits=32 prev=0 frames=12 usable=True held=7.700ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=20480 key_on_raw=1/4
2026-11-12T16:59:52.542903+00:00       #0 ntdll.dll+0x7858c            addr=0x77c1858c
2026-11-12T16:59:52.542903+00:00       #1 KERNELBASE.dll+0x16a1f0      addr=0x763fa1f0
2026-11-12T16:59:52.542903+00:00       #2 KERNELBASE.dll+0x16a18f      addr=0x763fa18f
2026-11-12T16:59:52.542903+00:00       #3 gamemd.exe+0xf4b96           addr=0x4f4b96
2026-11-12T16:59:52.542903+00:00       #4 gamemd.exe+0x29af0f          addr=0x69af0f
2026-11-12T16:59:52.542903+00:00       #5 ntdll.dll+0x95f9e            addr=0x77c35f9e
2026-11-12T16:59:52.542903+00:00       #6 gamemd.exe+0x3cda69          addr=0x7cda69
2026-11-12T16:59:52.542903+00:00       #7 gamemd.exe+0x3c9412          addr=0x7c9412
2026-11-12T16:59:52.542903+00:00       #8 gamemd.exe+0x25ca51          addr=0x65ca51
2026-11-12T16:59:52.542903+00:00       #9 gamemd.exe+0x28784c          addr=0x68784c
2026-11-12T16:59:52.542903+00:00       #10 KERNELBASE.dll+0x14e8e0      addr=0x763de8e0
2026-11-12T16:59:52.542903+00:00       #11 gamemd.exe+0x2867c3          addr=0x6867c3
2026-11-12T16:59:52.542903+00:00     抓栈 G05 判定=third_signature:gamemd+0xf4b96 wall=83.8ms frames=ntdll+0x7858c → kernelbase+0x16a1f0 → kernelbase+0x16a18f → gamemd+0xf4b96 → gamemd+0x29af0f → ntdll+0x95f9e → gamemd+0x3cda69 → gamemd+0x3c9412 → gamemd+0x25ca51 → gamemd+0x28784c → kernelbase+0x14e8e0 → gamemd+0x2867c3
2026-11-12T17:00:04.879893+00:00 [W_A_load] 结束 stop=stable_10.0s dur=15.0s n=493 frame 0→315 grabs=['G04', 'G05']
2026-11-12T17:00:04.879893+00:00 [W_A_ingame] 开始（timeout=5s ui=0.50s）
2026-11-12T17:00:09.882447+00:00 [W_A_ingame] 结束 stop=timeout dur=5.0s n=166 frame 315→471 grabs=[]
2026-11-12T17:00:09.883695+00:00 [W_A_ingame] 抓栈 G06 开始 tid=41576 原因=N0_normal_ingame_contrast frame=471
2026-11-12T17:00:09.962927+00:00     抓栈 G06  tid=41576 bits=32 prev=0 frames=4 usable=True held=1.287ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=16384 key_on_raw=1/4
2026-11-12T17:00:09.962927+00:00       #0 ntdll.dll+0x7858c            addr=0x77c1858c
2026-11-12T17:00:09.962927+00:00       #1 KERNELBASE.dll+0x16a1f0      addr=0x763fa1f0
2026-11-12T17:00:09.962927+00:00       #2 KERNELBASE.dll+0x16a18f      addr=0x763fa18f
2026-11-12T17:00:09.962927+00:00       #3 gamemd.exe+0x15e332          addr=0x55e332
2026-11-12T17:00:09.962927+00:00     抓栈 G06 判定=normal_ingame_f3 wall=79.7ms frames=ntdll+0x7858c → kernelbase+0x16a1f0 → kernelbase+0x16a18f → gamemd+0x15e332
2026-11-12T17:00:09.962927+00:00 [W_A_ingame] 开始（timeout=8s ui=0.50s）
... (省略 11 行) ...
2026-11-12T17:00:19.268684+00:00 [W_B_confirm_click] 抓栈 G07 开始 tid=41576 原因=confirm_click_stall frame=730
2026-11-12T17:00:19.371536+00:00     抓栈 G07  tid=41576 bits=32 prev=0 frames=9 usable=True held=5.906ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=16384 key_on_raw=1/4
2026-11-12T17:00:19.371536+00:00       #0 ntdll.dll+0x611ee            addr=0x77c011ee
2026-11-12T17:00:19.371536+00:00       #1 AcGenral.DLL+0xb1925         addr=0x54c91925
2026-11-12T17:00:19.371536+00:00       #2 gamemd.exe+0x93ce            addr=0x4093ce
2026-11-12T17:00:19.371536+00:00       #3 gamemd.exe+0x70e6            addr=0x4070e6
2026-11-12T17:00:19.371536+00:00       #4 gamemd.exe+0x2be066          addr=0x6be066
2026-11-12T17:00:19.371536+00:00       #5 gamemd.exe+0x3cd8ef          addr=0x7cd8ef
2026-11-12T17:00:19.371536+00:00       #6 KERNEL32.DLL+0x15d49         addr=0x761a5d49
2026-11-12T17:00:19.371536+00:00       #7 ntdll.dll+0x6c75b            addr=0x77c0c75b
2026-11-12T17:00:19.371536+00:00       #8 ntdll.dll+0x6c6e1            addr=0x77c0c6e1
2026-11-12T17:00:19.371536+00:00     抓栈 G07 判定=third_signature:gamemd+0x70e6 wall=103.0ms frames=ntdll+0x611ee → acgenral+0xb1925 → gamemd+0x93ce → gamemd+0x70e6 → gamemd+0x2be066 → gamemd+0x3cd8ef → kernel32+0x15d49 → ntdll+0x6c75b → ntdll+0x6c6e1
2026-11-12T17:00:21.493409+00:00 [W_B_confirm_click] 结束 stop=skirmish_screen dur=3.0s n=99 frame 730→0 grabs=['G07']
2026-11-12T17:00:21.496422+00:00 [idle_after_exit] 开始（timeout=15s ui=0.50s）
2026-11-12T17:00:21.892415+00:00 [idle_after_exit] 抓栈 G08 开始 tid=41576 原因=menu_idle_stall frame=0
2026-11-12T17:00:21.991314+00:00     抓栈 G08  tid=41576 bits=32 prev=0 frames=4 usable=True held=1.204ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=20480 key_on_raw=2/4
2026-11-12T17:00:21.991314+00:00       #0 ntdll.dll+0x7858c            addr=0x77c1858c
2026-11-12T17:00:21.991314+00:00       #1 KERNELBASE.dll+0x16a1f0      addr=0x763fa1f0
2026-11-12T17:00:21.991314+00:00       #2 KERNELBASE.dll+0x16a18f      addr=0x763fa18f
2026-11-12T17:00:21.991314+00:00       #3 gamemd.exe+0x207f17          addr=0x607f17
2026-11-12T17:00:21.991314+00:00     抓栈 G08 判定=S_sleep_hit wall=97.9ms frames=ntdll+0x7858c → kernelbase+0x16a1f0 → kernelbase+0x16a18f → gamemd+0x207f17
2026-11-12T17:00:24.508615+00:00 [idle_after_exit] 抓栈 G09 开始 tid=41576 原因=menu_idle_stall frame=0
2026-11-12T17:00:24.585291+00:00     抓栈 G09  tid=41576 bits=32 prev=0 frames=4 usable=True held=1.424ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=16384 key_on_raw=1/4
2026-11-12T17:00:24.585291+00:00       #0 win32u.dll+0x11ac            addr=0x766911ac
2026-11-12T17:00:24.585291+00:00       #1 USER32.dll+0xc7f51           addr=0x779b7f51
2026-11-12T17:00:24.585291+00:00       #2 DDRAW.dll+0x22b06            addr=0x54832b06
2026-11-12T17:00:24.585291+00:00       #3 gamemd.exe+0x13eb1c          addr=0x53eb1c
2026-11-12T17:00:24.585291+00:00     抓栈 G09 判定=third_signature:gamemd+0x13eb1c wall=77.3ms frames=win32u+0x11ac → user32+0xc7f51 → ddraw+0x22b06 → gamemd+0x13eb1c
2026-11-12T17:00:27.102024+00:00 [idle_after_exit] 抓栈 G10 开始 tid=41576 原因=menu_idle_stall frame=0
2026-11-12T17:00:27.181490+00:00     抓栈 G10  tid=41576 bits=32 prev=0 frames=4 usable=True held=1.509ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=16384 key_on_raw=1/4
2026-11-12T17:00:27.181490+00:00       #0 win32u.dll+0x11ac            addr=0x766911ac
2026-11-12T17:00:27.181490+00:00       #1 USER32.dll+0xc7f51           addr=0x779b7f51
2026-11-12T17:00:27.181490+00:00       #2 DDRAW.dll+0x22b06            addr=0x54832b06
2026-11-12T17:00:27.181490+00:00       #3 gamemd.exe+0x13eb1c          addr=0x53eb1c
2026-11-12T17:00:27.181490+00:00     抓栈 G10 判定=third_signature:gamemd+0x13eb1c wall=79.1ms frames=win32u+0x11ac → user32+0xc7f51 → ddraw+0x22b06 → gamemd+0x13eb1c
2026-11-12T17:00:36.516970+00:00 [idle_after_exit] 结束 stop=timeout dur=15.0s n=491 frame 0→0 grabs=['G08', 'G09', 'G10']
2026-11-12T17:00:36.522609+00:00 [W_D] 再次开局（起点=skirmish_screen，覆盖 加载→局内 边界）
2026-11-12T17:00:36.575916+00:00 [W_D_load] 第二次 StartGame，开始密集采样
2026-11-12T17:00:36.575916+00:00 [W_D_load] 开始（timeout=180s ui=0.50s）
2026-11-12T17:00:36.580289+00:00 [W_D_load] 抓栈 G11 开始 tid=41576 原因=load_transition_stall2 frame=0
2026-11-12T17:00:36.656806+00:00     抓栈 G11  tid=41576 bits=32 prev=0 frames=8 usable=True held=2.618ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=20480 key_on_raw=1/4
2026-11-12T17:00:36.656806+00:00       #0 KERNELBASE.dll+0x15aed2      addr=0x763eaed2
2026-11-12T17:00:36.656806+00:00       #1 KERNEL32.DLL+0x685b4         addr=0x761f85b4
2026-11-12T17:00:36.656806+00:00       #2 DDRAW.dll+0x20aba            addr=0x54830aba
2026-11-12T17:00:36.656806+00:00       #3 DDRAW.dll+0xb61b             addr=0x5481b61b
2026-11-12T17:00:36.656806+00:00       #4 gamemd.exe+0xbafc9           addr=0x4bafc9
2026-11-12T17:00:36.656806+00:00       #5 gamemd.exe+0x207f0a          addr=0x607f0a
2026-11-12T17:00:36.656806+00:00       #6 ?                            addr=0x2fcc304
2026-11-12T17:00:36.656806+00:00       #7 gamemd.exe+0x2180e           addr=0x42180e
2026-11-12T17:00:36.656806+00:00     抓栈 G11 判定=third_signature:ddraw+0xb61b wall=77.0ms frames=kernelbase+0x15aed2 → kernel32+0x685b4 → ddraw+0x20aba → ddraw+0xb61b → gamemd+0xbafc9 → gamemd+0x207f0a → ? → gamemd+0x2180e
2026-11-12T17:00:39.175731+00:00 [W_D_load] 抓栈 G12 开始 tid=41576 原因=load_transition_stall2 frame=0
2026-11-12T17:00:39.273066+00:00     抓栈 G12  tid=41576 bits=32 prev=0 frames=7 usable=True held=4.425ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=20480 key_on_raw=1/4
2026-11-12T17:00:39.273066+00:00       #0 ntdll.dll+0x7858c            addr=0x77c1858c
2026-11-12T17:00:39.273066+00:00       #1 KERNELBASE.dll+0x16a1f0      addr=0x763fa1f0
2026-11-12T17:00:39.273066+00:00       #2 KERNELBASE.dll+0x16a18f      addr=0x763fa18f
2026-11-12T17:00:39.273066+00:00       #3 gamemd.exe+0xf4b96           addr=0x4f4b96
2026-11-12T17:00:39.273066+00:00       #4 gamemd.exe+0x29af0f          addr=0x69af0f
2026-11-12T17:00:39.273066+00:00       #5 ntdll.dll+0x61160            addr=0x77c01160
2026-11-12T17:00:39.273066+00:00       #6 gamemd.exe+0x93eb            addr=0x4093eb
2026-11-12T17:00:39.273066+00:00     抓栈 G12 判定=third_signature:gamemd+0xf4b96 wall=97.2ms frames=ntdll+0x7858c → kernelbase+0x16a1f0 → kernelbase+0x16a18f → gamemd+0xf4b96 → gamemd+0x29af0f → ntdll+0x61160 → gamemd+0x93eb
2026-11-12T17:00:49.609718+00:00 [W_D_load] 结束 stop=stable_10.0s dur=13.0s n=427 frame 0→314 grabs=['G11', 'G12']
2026-11-12T17:00:49.609718+00:00 [W_D_ingame] 开始（timeout=5s ui=0.50s）
2026-11-12T17:00:54.615399+00:00 [W_D_ingame] 结束 stop=timeout dur=5.0s n=166 frame 314→471 grabs=[]
2026-11-12T17:00:54.615399+00:00 [W_D_ingame] 抓栈 G13 开始 tid=41576 原因=N1_normal_ingame_contrast frame=471
2026-11-12T17:00:54.709685+00:00     抓栈 G13  tid=41576 bits=32 prev=0 frames=4 usable=True held=1.153ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=16384 key_on_raw=1/4
2026-11-12T17:00:54.709685+00:00       #0 ntdll.dll+0x7858c            addr=0x77c1858c
2026-11-12T17:00:54.709685+00:00       #1 KERNELBASE.dll+0x16a1f0      addr=0x763fa1f0
2026-11-12T17:00:54.709685+00:00       #2 KERNELBASE.dll+0x16a18f      addr=0x763fa18f
2026-11-12T17:00:54.709685+00:00       #3 gamemd.exe+0x15e332          addr=0x55e332
2026-11-12T17:00:54.709685+00:00     抓栈 G13 判定=normal_ingame_f3 wall=93.7ms frames=ntdll+0x7858c → kernelbase+0x16a1f0 → kernelbase+0x16a18f → gamemd+0x15e332
2026-11-12T17:00:54.709685+00:00 [W_D_ingame] 开始（timeout=6s ui=0.50s）
2026-11-12T17:01:00.715879+00:00 [W_D_ingame] 结束 stop=timeout dur=6.0s n=365 frame 314→661 grabs=['G13']
2026-11-12T17:01:00.715879+00:00 [P1] 收尾：walker cleanup → 关游戏 → 残留核对 → 配置还原 → 锁恢复
2026-11-12T17:01:00.716885+00:00     SymCleanup 完成
2026-11-12T17:01:13.555536+00:00     WM_CLOSE(hwnd=8917116) -> True
2026-11-12T17:01:13.555536+00:00     taskkill /PID 4460 (无 /F) rc=0 out='SUCCESS: Sent termination signal to the process with PID 4460.'
2026-11-12T17:01:13.555536+00:00     taskkill /F /PID 4460 rc=0 out='SUCCESS: The process with PID 4460 has been terminated.'
2026-11-12T17:01:13.555536+00:00     最终存活=False
2026-11-12T17:01:13.567174+00:00     收尾后 gamemd 残留 = 0 []
2026-11-12T17:01:13.965930+00:00     实例锁已恢复 owner=lead
```

## 5. 收尾

- 收尾后 gamemd 残留: 0 `[]`

