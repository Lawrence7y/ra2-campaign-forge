# RUNLOG.md —— 真机单变量判决实验执行日志

- run_id: `NEXT_RE_20261112_R02`
- 开始(UTC): `2026-11-12T15:52:57.855205+00:00`；结束(UTC): `2026-11-12T15:54:10.995764+00:00`；本地: `2026-11-12T23:54:11.434822+08:00`
- 退出码: **2**
- 命令: `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -X utf8 D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W4_exit_dialog\exit_dialog_probe.py --map-pattern Proving Grounds --load-wait 15 --stable-seconds 20 --budget-ms 50 --r2-event-budget-ms 300 --max-frames 20 --raw-stack-bytes 65536 --menu-timeout 90 --dialog-timeout 12 --d1-count 3`
- Python: `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe` / `3.12.10`
- 写域: `lead/next_re_20261112_r02/W4_exit_dialog/`（其余资产只读复用）

## 1. §0 防双开守卫（脚本外先做了一次，脚本内再复核一次）

- 脚本外 `Get-Process -Name gamemd`：`NO_GAMEMD_PROCESS`（无 pid/启动时间/命令行）。
- 脚本内 `list_gamemd()` 启动前残留：**0** 个 `[]`。
- 另有无关 python 进程 `call_agy.py`(pid 36676) 在做 W5 交接评审，非 gamemd，按守卫要求**未启动第二个 gamemd、未杀任何其它进程**；其存在仅登记为不确定性。

## 2. 关键参数与实测

```json
{
 "args": {
  "map_pattern": "Proving Grounds",
  "load_wait": 15.0,
  "stable_seconds": 20.0,
  "budget_ms": 50.0,
  "r2_event_budget_ms": 300.0,
  "max_frames": 20,
  "raw_stack_bytes": 65536,
  "menu_timeout": 90.0,
  "dialog_timeout": 12.0,
  "d1_count": 3,
  "out": ""
 },
 "pid": 16052,
 "launcher_pid": 36408,
 "ownership": "wmi_child_parent_pid",
 "is32": true,
 "code_signature_ok": true,
 "map": {
  "index": 265,
  "display_name": "[8] Proving Grounds",
  "n_items": 268,
  "n_hits": 1,
  "pattern": "Proving Grounds"
 },
 "map_index": 265,
 "game_hwnd": 1968728,
 "window_tid": 37264,
 "self_tid": 12100,
 "walker": {
  "ok": true,
  "err": null,
  "n_modules": 111,
  "mods": [
   {
    "base": "0x400000",
    "size": 7954432,
    "name": "gamemd.exe"
   },
   {
    "base": "0x7ffb36400000",
    "size": 2523136,
    "name": "ntdll.dll"
   },
   {
    "base": "0x400000",
    "size": 7954432,
    "name": "gamemd.exe"
   },
   {
    "base": "0x77ba0000",
    "size": 1835008,
    "name": "ntdll.dll"
   },
   {
    "base": "0x76290000",
    "size": 2985984,
    "name": "KERNELBASE.dll"
   },
   {
    "base": "0x778f0000",
    "size": 2019328,
    "name": "USER32.dll"
   }
  ],
  "is32": true,
  "max_frames": 20
 },
 "prelaunch_match_all": true,
 "frame_stable_summary": {
  "seconds_target": 20.0,
  "interval": 0.25,
  "n_samples": 80,
  "frame_first": 337,
  "frame_last": 956,
  "frame_net_delta": 619,
  "max_consecutive_nonadvance_samples": 0,
  "frame_advanced": true
 },
 "d0_label": "D0",
 "dialog_meta": {},
 "p3_check": null,
 "p4_check": null,
 "hold_abort": false,
 "game_exited": true,
 "exit_readings": {
  "last_sentinel": {
   "frame": null,
   "g1": null,
   "g2": null,
   "g3": null,
   "g4": null,
   "mode_A8B238": null,
   "ingame_A8E9A0": null,
   "latch_ABCD58": null,
   "exitstate": null,
   "t_utc_iso": "2026-11-12T15:54:10.994260+00:00",
   "t_perf_ns": 99364994854900,
   "all_gates_zero": null,
   "any_gate_nonzero": null
  },
  "exit_code": 0,
  "t_utc_iso": "2026-11-12T15:54:10.994260+00:00"
 },
 "error": "GuardStop: Alt+F4 导致游戏直接退出（exit=0），按红线不重启补测"
}
```

## 3. 触发路径逐步记录（每步做了什么 / 观察到哪些窗口与控件文字）

### 尝试 1：Alt+F4

- 动作: {"force_foreground": true, "foreground_hwnd": 1968728, "game_hwnd": 1968728, "keys": "keybd_event(VK_MENU down, VK_F4 down/up, VK_MENU up)", "sent": true}
- 结果: `dialog_present=False`；进程存活=False；退出码=0
- 判据: no=0 yes=0 abort=0 new_tops=0 dialog_tops=0
- 触发前顶层窗口: `[{"hwnd": 1968728, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 37264}, {"hwnd": 1639554, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 37264}, {"hwnd": 6490720, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 37264}, {"hwnd": 4588816, "cls": "IME", "text": "Default IME", "visible": false, "tid": 37264}]`
- 触发前按钮文字: `[]`
- 触发后顶层窗口: `[]`
- 触发后按钮文字: `[]`
- 触发后全部有文字控件: `[]`

## 4. stdout（完整输出见 `out/stdout.txt` / `out/console.txt`）

```text
2026-11-12T15:52:57.871621+00:00 [S1] 启动前：只读资产自证 + 残留进程 + 实算 SHA-256
2026-11-12T15:52:57.882110+00:00     只读资产加载完成：W1 导航 / W3 抓栈 / r2 采样器 / e3_stackwalker
2026-11-12T15:52:57.882110+00:00     基准 7 帧：ntdll.dll+0x7858c → KERNELBASE.dll+0x16a1f0 → KERNELBASE.dll+0x16a18f → gamemd.exe+0x207f17 → USER32.dll+0x74775 → USER32.dll+0x3505d → gamemd.exe+0x20833f
2026-11-12T15:52:57.894673+00:00     gamemd 残留 = 0 []
2026-11-12T15:52:57.896182+00:00     RA2MD.INI                1754  c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d  match=True
2026-11-12T15:52:57.896182+00:00     ddraw.ini               14782  c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52  match=True
2026-11-12T15:52:57.897188+00:00     RA2MD.INI.benchbak       1754  c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d  match=True
2026-11-12T15:52:57.901202+00:00     gamemd.exe            4825360  73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476  match=True
2026-11-12T15:52:57.902207+00:00     ddraw.dll              411648  85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9  match=True
2026-11-12T15:52:58.606012+00:00     启动前文件清单 647 项
2026-11-12T15:52:58.607517+00:00 [S2] WMI 分离启动 gamemd.exe
2026-11-12T15:53:00.044418+00:00     pid=16052 归属=wmi_child_parent_pid launcher_pid=36408
2026-11-12T15:53:00.044418+00:00     IsWow64Process -> is32=True
2026-11-12T15:53:00.044418+00:00     代码签名@0x55DE4F = 'a0493da800' 期望 'a0493da800' -> ok=True
2026-11-12T15:53:20.062767+00:00 [S3] 导航 SinglePlayer -> Skirmish -> 按名称选图
2026-11-12T15:53:33.195880+00:00     地图命中：index=265 显示名='[8] Proving Grounds' 条目=268 命中数=1
2026-11-12T15:53:33.196888+00:00     游戏主窗口 hwnd=1968728
2026-11-12T15:53:34.200505+00:00     等待加载 15.0s
2026-11-12T15:53:49.200824+00:00 [S3b] 帧稳定推进观测 20.0s
2026-11-12T15:54:09.236437+00:00     样本=80 frame 337→956 Δ=619 最长连续不推进=0 拍
2026-11-12T15:54:09.236437+00:00 [S4] 挂起任何线程之前完成 StackWalk64/符号初始化
2026-11-12T15:54:09.240865+00:00     StackWalker ok=True err=None n_modules=111 is32=True max_frames=20 raw_bytes=65536
2026-11-12T15:54:09.241869+00:00     游戏窗口线程 tid=37264
2026-11-12T15:54:09.241869+00:00     自身线程守卫：GetCurrentThreadId=12100 ≠ 目标 tid=37264 ✓
2026-11-12T15:54:09.241869+00:00 [D0] 正常局内阴性对照：单次 ≤50ms 抓栈（平静、无交火）
2026-11-12T15:54:09.354770+00:00     抓栈 D0   tid=37264 bits=32 prev=0 frames=4 usable=True held=9.111ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=65536 key_on_raw=1/4
2026-11-12T15:54:09.354770+00:00       #0 ntdll.dll+0x7858c            addr=0x77c1858c
2026-11-12T15:54:09.354770+00:00       #1 KERNELBASE.dll+0x16a1f0      addr=0x763fa1f0
2026-11-12T15:54:09.354770+00:00       #2 KERNELBASE.dll+0x16a18f      addr=0x763fa18f
2026-11-12T15:54:09.354770+00:00       #3 gamemd.exe+0x15e332          addr=0x55e332
2026-11-12T15:54:09.358903+00:00     D0 state={"frame": 964, "g1": 0, "g2": 0, "g3": 0, "g4": 0, "mode": 5, "A8E9A0": 1, "ABCD58": 1, "exitstate": 0, "all_gates_zero": true, "any_gate_nonzero": false, "t_utc_iso": "2026-11-12T15:54:09.243408+00:00"}
2026-11-12T15:54:09.358903+00:00 [T1] 尝试 ①：Alt+F4（真实键盘事件，前置 force_foreground）
2026-11-12T15:54:10.994260+00:00     [尝试1] Alt+F4 -> dialog_present=False (no=0 yes=0 abort=0 new_tops=0 dialog_tops=0) alive=False ec=0
2026-11-12T15:54:10.994260+00:00       后窗口=[]
2026-11-12T15:54:10.994260+00:00       后按钮=[]
2026-11-12T15:54:10.995764+00:00 !! GuardStop: Alt+F4 导致游戏直接退出（exit=0），按红线不重启补测
2026-11-12T15:54:10.995764+00:00 [P1] 收尾：回溯器 cleanup → 关游戏 → 残留核对 → 配置逐字节还原
2026-11-12T15:54:10.995764+00:00     SymCleanup 完成
2026-11-12T15:54:11.008206+00:00     already_exited: 轮询期间进程已自然退出，不重启补测
2026-11-12T15:54:11.021785+00:00     收尾后 gamemd 残留 = 0 []
2026-11-12T15:54:11.413159+00:00     收尾后文件清单 647 项
2026-11-12T15:54:11.430134+00:00     还原 RA2MD.INI -> c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d
2026-11-12T15:54:11.430134+00:00     还原 ddraw.ini -> c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52
2026-11-12T15:54:11.430134+00:00     还原 RA2MD.INI.benchbak -> c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d
2026-11-12T15:54:11.430134+00:00     还原 gamemd.exe -> 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
2026-11-12T15:54:11.430134+00:00     还原 ddraw.dll -> 85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9
2026-11-12T15:52:57.871621+00:00 [S1] 启动前：只读资产自证 + 残留进程 + 实算 SHA-256
2026-11-12T15:52:57.882110+00:00     只读资产加载完成：W1 导航 / W3 抓栈 / r2 采样器 / e3_stackwalker
2026-11-12T15:52:57.882110+00:00     基准 7 帧：ntdll.dll+0x7858c → KERNELBASE.dll+0x16a1f0 → KERNELBASE.dll+0x16a18f → gamemd.exe+0x207f17 → USER32.dll+0x74775 → USER32.dll+0x3505d → gamemd.exe+0x20833f
2026-11-12T15:52:57.894673+00:00     gamemd 残留 = 0 []
2026-11-12T15:52:57.896182+00:00     RA2MD.INI                1754  c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d  match=True
2026-11-12T15:52:57.896182+00:00     ddraw.ini               14782  c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52  match=True
2026-11-12T15:52:57.897188+00:00     RA2MD.INI.benchbak       1754  c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d  match=True
2026-11-12T15:52:57.901202+00:00     gamemd.exe            4825360  73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476  match=True
2026-11-12T15:52:57.902207+00:00     ddraw.dll              411648  85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9  match=True
2026-11-12T15:52:58.606012+00:00     启动前文件清单 647 项
2026-11-12T15:52:58.607517+00:00 [S2] WMI 分离启动 gamemd.exe
2026-11-12T15:53:00.044418+00:00     pid=16052 归属=wmi_child_parent_pid launcher_pid=36408
2026-11-12T15:53:00.044418+00:00     IsWow64Process -> is32=True
2026-11-12T15:53:00.044418+00:00     代码签名@0x55DE4F = 'a0493da800' 期望 'a0493da800' -> ok=True
2026-11-12T15:53:20.062767+00:00 [S3] 导航 SinglePlayer -> Skirmish -> 按名称选图
2026-11-12T15:53:33.195880+00:00     地图命中：index=265 显示名='[8] Proving Grounds' 条目=268 命中数=1
2026-11-12T15:53:33.196888+00:00     游戏主窗口 hwnd=1968728
2026-11-12T15:53:34.200505+00:00     等待加载 15.0s
2026-11-12T15:53:49.200824+00:00 [S3b] 帧稳定推进观测 20.0s
2026-11-12T15:54:09.236437+00:00     样本=80 frame 337→956 Δ=619 最长连续不推进=0 拍
2026-11-12T15:54:09.236437+00:00 [S4] 挂起任何线程之前完成 StackWalk64/符号初始化
2026-11-12T15:54:09.240865+00:00     StackWalker ok=True err=None n_modules=111 is32=True max_frames=20 raw_bytes=65536
2026-11-12T15:54:09.241869+00:00     游戏窗口线程 tid=37264
2026-11-12T15:54:09.241869+00:00     自身线程守卫：GetCurrentThreadId=12100 ≠ 目标 tid=37264 ✓
2026-11-12T15:54:09.241869+00:00 [D0] 正常局内阴性对照：单次 ≤50ms 抓栈（平静、无交火）
2026-11-12T15:54:09.354770+00:00     抓栈 D0   tid=37264 bits=32 prev=0 frames=4 usable=True held=9.111ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=65536 key_on_raw=1/4
2026-11-12T15:54:09.354770+00:00       #0 ntdll.dll+0x7858c            addr=0x77c1858c
2026-11-12T15:54:09.354770+00:00       #1 KERNELBASE.dll+0x16a1f0      addr=0x763fa1f0
2026-11-12T15:54:09.354770+00:00       #2 KERNELBASE.dll+0x16a18f      addr=0x763fa18f
2026-11-12T15:54:09.354770+00:00       #3 gamemd.exe+0x15e332          addr=0x55e332
2026-11-12T15:54:09.358903+00:00     D0 state={"frame": 964, "g1": 0, "g2": 0, "g3": 0, "g4": 0, "mode": 5, "A8E9A0": 1, "ABCD58": 1, "exitstate": 0, "all_gates_zero": true, "any_gate_nonzero": false, "t_utc_iso": "2026-11-12T15:54:09.243408+00:00"}
2026-11-12T15:54:09.358903+00:00 [T1] 尝试 ①：Alt+F4（真实键盘事件，前置 force_foreground）
2026-11-12T15:54:10.994260+00:00     [尝试1] Alt+F4 -> dialog_present=False (no=0 yes=0 abort=0 new_tops=0 dialog_tops=0) alive=False ec=0
2026-11-12T15:54:10.994260+00:00       后窗口=[]
2026-11-12T15:54:10.994260+00:00       后按钮=[]
2026-11-12T15:54:10.995764+00:00 !! GuardStop: Alt+F4 导致游戏直接退出（exit=0），按红线不重启补测
2026-11-12T15:54:10.995764+00:00 [P1] 收尾：回溯器 cleanup → 关游戏 → 残留核对 → 配置逐字节还原
2026-11-12T15:54:10.995764+00:00     SymCleanup 完成
2026-11-12T15:54:11.008206+00:00     already_exited: 轮询期间进程已自然退出，不重启补测
2026-11-12T15:54:11.021785+00:00     收尾后 gamemd 残留 = 0 []
2026-11-12T15:54:11.413159+00:00     收尾后文件清单 647 项
2026-11-12T15:54:11.430134+00:00     还原 RA2MD.INI -> c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d
2026-11-12T15:54:11.430134+00:00     还原 ddraw.ini -> c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52
2026-11-12T15:54:11.430134+00:00     还原 RA2MD.INI.benchbak -> c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d
2026-11-12T15:54:11.430134+00:00     还原 gamemd.exe -> 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
2026-11-12T15:54:11.430134+00:00     还原 ddraw.dll -> 85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9
```

## 5. 收尾

- 收尾后 gamemd 残留: 0 `[]`

