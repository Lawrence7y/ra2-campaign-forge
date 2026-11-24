# RUNLOG.md —— 真机批次 B 执行日志

- run_id: `NEXT_RE_20261112_R02`
- 开始(UTC): `2026-11-12T15:17:39.706993+00:00`；结束(UTC): `2026-11-12T15:19:00.689524+00:00`
- 本地时间: `2026-11-12T23:19:14.216392+08:00`
- 退出码: **0**
- 命令: `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -X utf8 D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W3_stack_contrast\stack_contrast.py --map-pattern Proving Grounds --load-wait 15 --stable-seconds 20 --budget-ms 50 --r2-event-budget-ms 300 --max-frames 20 --raw-stack-bytes 65536 --c1-count 3 --menu-timeout 90`
- Python: `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe` / `3.12.10`
- 本批共三次单实例串行真机启动（每趟独立收尾还原、残留进程 0）：第 1 趟 `out/run1/` 完整但派生 `usable` 判据误把 `stackwalk_false:0` 当失败；第 2 趟 `out/run2_aborted/` 因只读原始栈扫描的 WOW64 同名双模块溢出 bug 在 C0 后异常、已 `finally` 安全收尾并修复，仅作透明留痕；**本 RUNLOG 对应第 3 趟（主判据）**。三趟的帧停推/门控全 0/Δframe>0/配置还原结论一致。

## 关键参数与实测

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
  "c1_count": 3,
  "menu_timeout": 90.0,
  "out": ""
 },
 "pid": 37684,
 "launcher_pid": 32996,
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
 "game_hwnd": 917908,
 "window_tid": 41924,
 "c0_tid": 41924,
 "walker": {
  "ok": true,
  "err": null,
  "n_modules": 100,
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
 "map_index": 265,
 "frame_stable_summary": {
  "seconds_target": 20.0,
  "interval": 0.25,
  "n_samples": 80,
  "frame_first": 325,
  "frame_last": 943,
  "frame_net_delta": 618,
  "max_consecutive_nonadvance_samples": 0,
  "frame_advanced": true
 },
 "c1_cycles": [
  {
   "label": "C1a",
   "fg_ok": true,
   "menu_button_hwnd": 7408342,
   "menu_button_text": "GUI:ResumeMission",
   "menu_present": true,
   "window_tid_now": 41924,
   "same_tid_as_C0": true,
   "frame_a": 963,
   "frame_b": 963,
   "frame_stopped": true,
   "gates_zero": true,
   "g1": 0,
   "g2": 0,
   "g3": 0,
   "g4": 0,
   "mode_A8B238": 5,
   "ingame_A8E9A0": 1,
   "latch_ABCD58": 0,
   "sentinels_at_grab": {
    "frame": 963,
    "g1": 0,
    "g2": 0,
    "g3": 0,
    "g4": 0,
    "mode_A8B238": 5,
    "ingame_A8E9A0": 1,
    "latch_ABCD58": 0,
    "t_utc_iso": "2026-11-12T15:18:52.977977+00:00",
    "t_perf_ns": 97246978163900,
    "all_gates_zero": true,
    "any_gate_nonzero": false
   }
  },
  {
   "label": "C1b",
   "fg_ok": true,
   "menu_button_hwnd": 3150062,
   "menu_button_text": "GUI:ResumeMission",
   "menu_present": true,
   "window_tid_now": 41924,
   "same_tid_as_C0": true,
   "frame_a": 1010,
   "frame_b": 1010,
   "frame_stopped": true,
   "gates_zero": true,
   "g1": 0,
   "g2": 0,
   "g3": 0,
   "g4": 0,
   "mode_A8B238": 5,
   "ingame_A8E9A0": 1,
   "latch_ABCD58": 0,
   "sentinels_at_grab": {
    "frame": 1010,
    "g1": 0,
    "g2": 0,
    "g3": 0,
    "g4": 0,
    "mode_A8B238": 5,
    "ingame_A8E9A0": 1,
    "latch_ABCD58": 0,
    "t_utc_iso": "2026-11-12T15:18:56.124888+00:00",
    "t_perf_ns": 97250125082500,
    "all_gates_zero": true,
    "any_gate_nonzero": false
   }
  },
  {
   "label": "C1c",
   "fg_ok": true,
   "menu_button_hwnd": 7539414,
   "menu_button_text": "GUI:ResumeMission",
   "menu_present": true,
   "window_tid_now": 41924,
   "same_tid_as_C0": true,
   "frame_a": 1057,
   "frame_b": 1057,
   "frame_stopped": true,
   "gates_zero": true,
   "g1": 0,
   "g2": 0,
   "g3": 0,
   "g4": 0,
   "mode_A8B238": 5,
   "ingame_A8E9A0": 1,
   "latch_ABCD58": 0,
   "sentinels_at_grab": {
    "frame": 1057,
    "g1": 0,
    "g2": 0,
    "g3": 0,
    "g4": 0,
    "mode_A8B238": 5,
    "ingame_A8E9A0": 1,
    "latch_ABCD58": 0,
    "t_utc_iso": "2026-11-12T15:18:59.279615+00:00",
    "t_perf_ns": 97253279745700,
    "all_gates_zero": true,
    "any_gate_nonzero": false
   }
  }
 ],
 "resume_verifications": [
  {
   "label": "C1a",
   "click": {
    "found": true,
    "name": "GUI:ResumeMission",
    "hwnd": 7408342,
    "text": "GUI:ResumeMission",
    "clicked": true
   },
   "frame_after_click": 991,
   "frame_later": 1004,
   "delta_frame": 13,
   "resumed": true
  },
  {
   "label": "C1b",
   "click": {
    "found": true,
    "name": "GUI:ResumeMission",
    "hwnd": 3150062,
    "text": "GUI:ResumeMission",
    "clicked": true
   },
   "frame_after_click": 1038,
   "frame_later": 1051,
   "delta_frame": 13,
   "resumed": true
  },
  {
   "label": "C1c",
   "click": {
    "found": true,
    "name": "GUI:ResumeMission",
    "hwnd": 7539414,
    "text": "GUI:ResumeMission",
    "clicked": true
   },
   "frame_after_click": 1085,
   "frame_later": 1098,
   "delta_frame": 13,
   "resumed": true
  }
 ],
 "hold_abort": false,
 "error": null
}
```

## stdout 片段（完整输出见 `out/stdout.txt`）

```text
2026-11-12T15:17:39.708075+00:00 [S1] 启动前：残留进程 + 只读资产自证 + 实算 SHA-256
2026-11-12T15:17:39.718402+00:00     只读资产加载完成：W1 导航 / r2 采样器 / e3_stackwalker（结构自证通过）
2026-11-12T15:17:39.718940+00:00     基准 7 帧已读：ntdll.dll+0x7858c → KERNELBASE.dll+0x16a1f0 → KERNELBASE.dll+0x16a18f → gamemd.exe+0x207f17 → USER32.dll+0x74775 → USER32.dll+0x3505d → gamemd.exe+0x20833f
2026-11-12T15:17:39.735534+00:00     gamemd 残留 = 0 []
2026-11-12T15:17:39.736059+00:00     RA2MD.INI                1754  c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d  match=True
2026-11-12T15:17:39.736579+00:00     ddraw.ini               14782  c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52  match=True
2026-11-12T15:17:39.741947+00:00     gamemd.exe            4825360  73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476  match=True
2026-11-12T15:17:39.743007+00:00     ddraw.dll              411648  85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9  match=True
2026-11-12T15:17:39.743540+00:00     RA2MD.INI.benchbak       1754  c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d  match=True
2026-11-12T15:17:40.275416+00:00     启动前文件清单 647 项
2026-11-12T15:17:40.276452+00:00 [S2] WMI 分离启动 gamemd.exe
2026-11-12T15:17:41.849113+00:00     pid=37684 归属=wmi_child_parent_pid launcher_pid=32996
2026-11-12T15:17:41.849113+00:00     IsWow64Process -> is32=True
2026-11-12T15:17:41.849113+00:00     代码签名@0x55DE4F = 'a0493da800' 期望 'a0493da800' -> ok=True
2026-11-12T15:18:01.868241+00:00 [S3] 导航 SinglePlayer -> Skirmish -> 按名称选图
2026-11-12T15:18:15.006976+00:00     地图命中：index=265 显示名='[8] Proving Grounds' 条目=268 命中数=1
2026-11-12T15:18:15.008484+00:00     游戏主窗口 hwnd=917908
2026-11-12T15:18:16.012075+00:00     等待加载 15.0s
2026-11-12T15:18:31.012702+00:00 [S3b] 帧稳定推进观测 20.0s
2026-11-12T15:18:51.049064+00:00     样本=80 frame 325→943 Δ=618 最长连续不推进=0 拍
2026-11-12T15:18:51.049064+00:00 [S4] 挂起前完成 StackWalk64/符号初始化（attach_walker）
2026-11-12T15:18:51.053584+00:00     StackWalker ok=True err=None n_modules=100 is32=True max_frames=20 raw_stack_bytes=65536
2026-11-12T15:18:51.053584+00:00       gamemd.exe base=0x400000 size=7954432
2026-11-12T15:18:51.053584+00:00       ntdll.dll base=0x7ffb36400000 size=2523136
2026-11-12T15:18:51.053584+00:00       gamemd.exe base=0x400000 size=7954432
2026-11-12T15:18:51.053584+00:00       ntdll.dll base=0x77ba0000 size=1835008
2026-11-12T15:18:51.053584+00:00       KERNELBASE.dll base=0x76290000 size=2985984
2026-11-12T15:18:51.053584+00:00       USER32.dll base=0x778f0000 size=2019328
2026-11-12T15:18:51.055090+00:00     游戏窗口线程 tid=41924 (主窗口 hwnd=[917908])
2026-11-12T15:18:51.055090+00:00     自身线程守卫：采样器 GetCurrentThreadId=8776 ≠ 目标 tid=41924 ✓
2026-11-12T15:18:51.055090+00:00 [C0] 正常局内阴性对照：单次 ≤50ms 抓栈（平静、无交火）
2026-11-12T15:18:51.163257+00:00     抓栈 C0   tid=41924 bits=32 prev=0 frames=4 usable=True held=5.992ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=65536 key_on_raw=1/4
2026-11-12T15:18:51.163257+00:00       #0 ntdll.dll+0x7858c            addr=0x77c1858c
2026-11-12T15:18:51.163257+00:00       #1 KERNELBASE.dll+0x16a1f0      addr=0x763fa1f0
2026-11-12T15:18:51.163257+00:00       #2 KERNELBASE.dll+0x16a18f      addr=0x763fa18f
2026-11-12T15:18:51.163257+00:00       #3 gamemd.exe+0x15e332          addr=0x55e332
2026-11-12T15:18:51.163257+00:00 [C1a] 第 1/3 趟：按 Esc 打开局内菜单
2026-11-12T15:18:51.399384+00:00     force_foreground -> True
2026-11-12T15:18:52.977977+00:00     菜单按钮='GUI:ResumeMission'(hwnd=7408342) 帧 963→963 停推=True 四门控全0=True g=[0,0,0,0] mode=5 ingame=1 latch=0
2026-11-12T15:18:53.074981+00:00     抓栈 C1a  tid=41924 bits=32 prev=0 frames=4 usable=True held=1.952ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=65536 key_on_raw=1/4
... (省略 1 行) ...
2026-11-12T15:18:53.074981+00:00       #1 USER32.dll+0xc7f51           addr=0x779b7f51
2026-11-12T15:18:53.074981+00:00       #2 DDRAW.dll+0x22b06            addr=0x54832b06
2026-11-12T15:18:53.074981+00:00       #3 gamemd.exe+0x13eb1c          addr=0x53eb1c
2026-11-12T15:18:53.074981+00:00 [C1a] 点 GUI:ResumeMission 恢复对局
2026-11-12T15:18:54.377175+00:00     恢复点击=True Δframe=13 resumed=True
2026-11-12T15:18:54.377175+00:00 [C1b] 第 2/3 趟：按 Esc 打开局内菜单
2026-11-12T15:18:54.549054+00:00     force_foreground -> True
2026-11-12T15:18:56.124888+00:00     菜单按钮='GUI:ResumeMission'(hwnd=3150062) 帧 1010→1010 停推=True 四门控全0=True g=[0,0,0,0] mode=5 ingame=1 latch=0
2026-11-12T15:18:56.225811+00:00     抓栈 C1b  tid=41924 bits=32 prev=0 frames=4 usable=True held=1.956ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=65536 key_on_raw=1/4
2026-11-12T15:18:56.225811+00:00       #0 win32u.dll+0x11ac            addr=0x766911ac
2026-11-12T15:18:56.225811+00:00       #1 USER32.dll+0xc7f51           addr=0x779b7f51
2026-11-12T15:18:56.225811+00:00       #2 DDRAW.dll+0x22b06            addr=0x54832b06
2026-11-12T15:18:56.225811+00:00       #3 gamemd.exe+0x13eb1c          addr=0x53eb1c
2026-11-12T15:18:56.225811+00:00 [C1b] 点 GUI:ResumeMission 恢复对局
2026-11-12T15:18:57.528286+00:00     恢复点击=True Δframe=13 resumed=True
2026-11-12T15:18:57.528286+00:00 [C1c] 第 3/3 趟：按 Esc 打开局内菜单
2026-11-12T15:18:57.701749+00:00     force_foreground -> True
2026-11-12T15:18:59.279615+00:00     菜单按钮='GUI:ResumeMission'(hwnd=7539414) 帧 1057→1057 停推=True 四门控全0=True g=[0,0,0,0] mode=5 ingame=1 latch=0
2026-11-12T15:18:59.382551+00:00     抓栈 C1c  tid=41924 bits=32 prev=0 frames=4 usable=True held=2.070ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=65536 key_on_raw=1/4
2026-11-12T15:18:59.382551+00:00       #0 win32u.dll+0x11ac            addr=0x766911ac
2026-11-12T15:18:59.382551+00:00       #1 USER32.dll+0xc7f51           addr=0x779b7f51
2026-11-12T15:18:59.382551+00:00       #2 DDRAW.dll+0x22b06            addr=0x54832b06
2026-11-12T15:18:59.382551+00:00       #3 gamemd.exe+0x13eb1c          addr=0x53eb1c
2026-11-12T15:18:59.382551+00:00 [C1c] 点 GUI:ResumeMission 恢复对局
2026-11-12T15:19:00.687012+00:00     恢复点击=True Δframe=13 resumed=True
2026-11-12T15:19:00.687012+00:00 [S5] 逐帧比对与判档
2026-11-12T15:19:00.689524+00:00     判档 = [部分一致]
2026-11-12T15:19:00.689524+00:00 [P1] 收尾：回溯器 cleanup → 关游戏 → 残留核对 → 配置逐字节还原
2026-11-12T15:19:00.689524+00:00     SymCleanup 完成
2026-11-12T15:19:13.733388+00:00     WM_CLOSE(hwnd=917908) -> True
2026-11-12T15:19:13.733388+00:00     taskkill /PID 37684 (无 /F) rc=0 out='SUCCESS: Sent termination signal to the process with PID 37684.'
2026-11-12T15:19:13.733388+00:00     taskkill /F /PID 37684 rc=0 out='SUCCESS: The process with PID 37684 has been terminated.'
2026-11-12T15:19:13.733388+00:00     最终存活=False
2026-11-12T15:19:13.748454+00:00     收尾后 gamemd 残留 = 0 []
2026-11-12T15:19:14.197103+00:00     收尾后文件清单 647 项
2026-11-12T15:19:14.213878+00:00     还原 RA2MD.INI -> c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d
2026-11-12T15:19:14.213878+00:00     还原 ddraw.ini -> c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52
2026-11-12T15:19:14.213878+00:00     还原 RA2MD.INI.benchbak -> c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d
2026-11-12T15:19:14.213878+00:00     还原 gamemd.exe -> 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
2026-11-12T15:19:14.213878+00:00     还原 ddraw.dll -> 85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9
```

> 离线重算补记（2026-11-12T15:22:25Z，**判档以此为准**）：上方 stdout 片段是本趟真机运行时的**历史原样输出**，其中 `判档 = [部分一致]` 是当时脚本内 `analyze()` 把「原始栈上命中 1 个关键点」直接算作部分一致所得。随后离线复核发现：该唯一命中 `USER32+0x74775` 在 **C0 正常局内阴性对照里同样出现**，属与菜单无关的栈残留，按对照实验口径不应计入一致证据。修正判据后以 `--reanalyze` 从**同一批未经改动的 `out/*.json`** 重算，最终判档为 **`[未证实]`**（见 `CONTRAST.md` / `summary.json`）。命令、退出码、时间戳、stdout 均为运行时原样，未改动。
