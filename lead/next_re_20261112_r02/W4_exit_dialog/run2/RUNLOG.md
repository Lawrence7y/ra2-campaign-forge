# RUNLOG.md —— 真机单变量判决实验执行日志

- run_id: `NEXT_RE_20261112_R02`
- 开始(UTC): `2026-11-12T15:57:31.757987+00:00`；结束(UTC): `2026-11-12T15:58:52.487869+00:00`；本地: `2026-11-12T23:59:05.824744+08:00`
- 退出码: **0**
- 命令: `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -X utf8 D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W4_exit_dialog\exit_dialog_probe.py --map-pattern Proving Grounds --load-wait 15 --stable-seconds 20 --budget-ms 50 --r2-event-budget-ms 300 --max-frames 20 --raw-stack-bytes 65536 --menu-timeout 90 --dialog-timeout 12 --d1-count 3 --skip-altf4`
- Python: `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe` / `3.12.10`
- 写域: `lead/next_re_20261112_r02/W4_exit_dialog/`（其余资产只读复用）

## 1. 防双开守卫（脚本内实测，动态生成）

- 脚本内 `list_gamemd()` 启动前残留：**0** 个 `[]`。
- 哈希守卫：`prelaunch_match_all = True`（逐文件明细见 CONFIG_RESTORE.md §1）。
- 防双开纪律：本脚本只启动 1 个 gamemd 实例并全程只处理该 pid；对其它进程只读不动、未杀任何进程；运行期间若出现其它 gamemd 仅登记不处理。

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
  "skip_altf4": true,
  "out": ""
 },
 "pid": 32448,
 "launcher_pid": 41260,
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
 "game_hwnd": 52760734,
 "window_tid": 36700,
 "self_tid": 44656,
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
  "frame_first": 340,
  "frame_last": 959,
  "frame_net_delta": 619,
  "max_consecutive_nonadvance_samples": 0,
  "frame_advanced": true
 },
 "d0_label": "D0",
 "dialog_meta": {
  "successful_method": null,
  "stable": false,
  "evidence_summary": null,
  "note": "未能触发；见 out/triggers.json 与 RUNLOG 第 3 节"
 },
 "p3_check": null,
 "p4_check": null,
 "hold_abort": false,
 "game_exited": false,
 "exit_readings": null,
 "error": null
}
```

## 3. 触发路径逐步记录（每步做了什么 / 观察到哪些窗口与控件文字）

### 尝试 1：Alt+F4（第 1 趟已实测，本趟跳过）

- 动作: {"note": "run1/triggers.json + run1/out/run1/triggers.json: 真实 keybd_event Alt+F4（force_foreground 成功）后 游戏直接退出 exit_code=0，本 pid 窗口/控件枚举为空，无确认对话框；为避免再次杀死实例，本趟不再重发。"}
- 结果: `dialog_present=False`；进程存活=None；退出码=0
- 判据: 第 1 趟实测：直接退出，无对话框（已归档，非本趟新观察）
- 触发前顶层窗口: `[]`
- 触发前按钮文字: `[]`
- 触发后顶层窗口: `[]`
- 触发后按钮文字: `[]`
- 触发后全部有文字控件: `[]`

### 尝试 2：按控件文字点击 Abort/Exit/放弃类按钮

- 动作: {"keyword_rule": "classify_button(text)=='abort'，按文字而非索引", "opened_esc_menu_as_route": true, "menu_button_texts": ["GUI:ResumeMission", "GUI:GameControls", "GUI:LoadGame", "GUI:AbortMission", "GUI:SaveGame", "GUI:DeleteGame"], "candidates": [{"hwnd": 2495812, "text": "GUI:AbortMission"}], "clicked": {"hwnd": 2495812, "text": "GUI:AbortMission", "clicked": true}}
- 结果: `dialog_present=False`；进程存活=True；退出码=259
- 判据: no=0 yes=0 abort=0 new_tops=0 dialog_tops=0
- 触发前顶层窗口: `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]`
- 触发前按钮文字: `["GUI:ResumeMission", "GUI:GameControls", "GUI:LoadGame", "GUI:AbortMission", "GUI:SaveGame", "GUI:DeleteGame"]`
- 触发后顶层窗口: `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]`
- 触发后按钮文字: `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]`
- 触发后全部有文字控件: `["GUI:ResumeMission", "GUI:AskAbortMission", "GUI:Blank", "GUI:Blank", "GUI:Blank"]`
- 触发后轮询观察（每 0.4s，捕捉延迟/短暂出现的对话框）：

  | t_s | dialog_present | 判据 | 顶层窗口 | 按钮文字 |
  |---|---|---|---|---|
  | 0.001 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |
  | 0.403 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |
  | 0.805 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |
  | 1.207 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |
  | 1.609 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |
  | 2.011 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |
  | 2.413 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |
  | 2.815 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |
  | 3.217 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |

### 尝试 3：局内菜单 Restart/Exit to main menu 类按钮

- 动作: {"keyword_rule": "restart/重新开始/main menu/主菜单/exit/quit/surrender", "opened_esc_menu_as_route": false, "menu_button_texts": ["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"], "candidates": [], "clicked": null, "no_candidate_reason": "局内菜单按钮文字中无 restart/重新开始/exit to main menu 类"}
- 结果: `dialog_present=False`；进程存活=True；退出码=259
- 判据: no=0 yes=0 abort=0 new_tops=0 dialog_tops=0
- 触发前顶层窗口: `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]`
- 触发前按钮文字: `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]`
- 触发后顶层窗口: `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]`
- 触发后按钮文字: `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]`
- 触发后全部有文字控件: `["GUI:ResumeMission", "GUI:AskAbortMission", "GUI:Blank", "GUI:Blank", "GUI:Blank"]`
- 触发后轮询观察（每 0.4s，捕捉延迟/短暂出现的对话框）：

  | t_s | dialog_present | 判据 | 顶层窗口 | 按钮文字 |
  |---|---|---|---|---|
  | 0.001 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |
  | 0.402 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |
  | 0.804 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |
  | 1.206 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |
  | 1.608 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |
  | 2.009 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |
  | 2.411 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |
  | 2.813 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |
  | 3.214 | False | `no=0 yes=0 abort=0 new_tops=0 dialog_tops=0` | `[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |

## 4. stdout（完整输出见 `out/stdout.txt` / `out/console.txt`）

```text
2026-11-12T15:57:31.759988+00:00 [S1] 启动前：只读资产自证 + 残留进程 + 实算 SHA-256
2026-11-12T15:57:31.767341+00:00     只读资产加载完成：W1 导航 / W3 抓栈 / r2 采样器 / e3_stackwalker
2026-11-12T15:57:31.767341+00:00     基准 7 帧：ntdll.dll+0x7858c → KERNELBASE.dll+0x16a1f0 → KERNELBASE.dll+0x16a18f → gamemd.exe+0x207f17 → USER32.dll+0x74775 → USER32.dll+0x3505d → gamemd.exe+0x20833f
2026-11-12T15:57:31.780036+00:00     gamemd 残留 = 0 []
2026-11-12T15:57:31.780551+00:00     RA2MD.INI                1754  c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d  match=True
2026-11-12T15:57:31.781084+00:00     ddraw.ini               14782  c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52  match=True
2026-11-12T15:57:31.781084+00:00     RA2MD.INI.benchbak       1754  c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d  match=True
2026-11-12T15:57:31.785046+00:00     gamemd.exe            4825360  73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476  match=True
2026-11-12T15:57:31.785577+00:00     ddraw.dll              411648  85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9  match=True
2026-11-12T15:57:32.170456+00:00     启动前文件清单 647 项
2026-11-12T15:57:32.170456+00:00 [S2] WMI 分离启动 gamemd.exe
2026-11-12T15:57:33.554121+00:00     pid=32448 归属=wmi_child_parent_pid launcher_pid=41260
2026-11-12T15:57:33.554121+00:00     IsWow64Process -> is32=True
2026-11-12T15:57:33.554121+00:00     代码签名@0x55DE4F = 'a0493da800' 期望 'a0493da800' -> ok=True
2026-11-12T15:57:53.571139+00:00 [S3] 导航 SinglePlayer -> Skirmish -> 按名称选图
2026-11-12T15:58:06.702117+00:00     地图命中：index=265 显示名='[8] Proving Grounds' 条目=268 命中数=1
2026-11-12T15:58:06.703631+00:00     游戏主窗口 hwnd=52760734
2026-11-12T15:58:07.706894+00:00     等待加载 15.0s
2026-11-12T15:58:22.707089+00:00 [S3b] 帧稳定推进观测 20.0s
2026-11-12T15:58:42.740428+00:00     样本=80 frame 340→959 Δ=619 最长连续不推进=0 拍
2026-11-12T15:58:42.740428+00:00 [S4] 挂起任何线程之前完成 StackWalk64/符号初始化
2026-11-12T15:58:42.743448+00:00     StackWalker ok=True err=None n_modules=111 is32=True max_frames=20 raw_bytes=65536
2026-11-12T15:58:42.744475+00:00     游戏窗口线程 tid=36700
2026-11-12T15:58:42.744475+00:00     自身线程守卫：GetCurrentThreadId=44656 ≠ 目标 tid=36700 ✓
2026-11-12T15:58:42.744475+00:00 [D0] 正常局内阴性对照：单次 ≤50ms 抓栈（平静、无交火）
2026-11-12T15:58:42.837250+00:00     抓栈 D0   tid=36700 bits=32 prev=0 frames=4 usable=True held=5.444ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=65536 key_on_raw=1/4
2026-11-12T15:58:42.837250+00:00       #0 ntdll.dll+0x7858c            addr=0x77c1858c
2026-11-12T15:58:42.837250+00:00       #1 KERNELBASE.dll+0x16a1f0      addr=0x763fa1f0
2026-11-12T15:58:42.837250+00:00       #2 KERNELBASE.dll+0x16a18f      addr=0x763fa18f
2026-11-12T15:58:42.837250+00:00       #3 gamemd.exe+0x15e332          addr=0x55e332
2026-11-12T15:58:42.840796+00:00     D0 state={"frame": 967, "g1": 0, "g2": 0, "g3": 0, "g4": 0, "mode": 5, "A8E9A0": 1, "ABCD58": 1, "exitstate": 0, "all_gates_zero": true, "any_gate_nonzero": false, "t_utc_iso": "2026-11-12T15:58:42.746001+00:00"}
2026-11-12T15:58:42.841838+00:00     [尝试1] Alt+F4 已在第 1 趟实测为致命（exit=0）；本趟跳过，从 ② 继续优先级序列
2026-11-12T15:58:42.841838+00:00 [T2] 尝试 ②：按控件文字找并点击 Abort/Exit/放弃类按钮（不猜索引）
2026-11-12T15:58:42.842997+00:00     正常局内无 Abort 类按钮；仅作导航按一次 Esc 暴露菜单按钮
2026-11-12T15:58:45.249001+00:00     点击按钮 'GUI:AbortMission' hwnd=2495812
2026-11-12T15:58:48.867390+00:00     [尝试2] 按控件文字点击 Abort/Exit/放弃类按钮 -> dialog_present=False (no=0 yes=0 abort=0 new_tops=0 dialog_tops=0) alive=True ec=259
2026-11-12T15:58:48.867390+00:00       后窗口=[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]
2026-11-12T15:58:48.867390+00:00       后按钮=["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]
2026-11-12T15:58:48.867390+00:00 [T3] 尝试 ③：局内菜单里 Restart/Exit to main menu 类按钮
2026-11-12T15:58:52.486866+00:00     [尝试3] 局内菜单 Restart/Exit to main menu 类按钮 -> dialog_present=False (no=0 yes=0 abort=0 new_tops=0 dialog_tops=0) alive=True ec=259
2026-11-12T15:58:52.486866+00:00       后窗口=[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]
2026-11-12T15:58:52.486866+00:00       后按钮=["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]
2026-11-12T15:58:52.486866+00:00 !! 三条路径均未产生确认对话框：按红线如实写「未能触发」，不伪造 D1/D2
2026-11-12T15:58:52.486866+00:00 [S5] 逐帧比对与判档
2026-11-12T15:58:52.487869+00:00     判档 = [未证实] (P1=未测 P2=未测 P3=未测 P4=未测)
2026-11-12T15:58:52.487869+00:00 [P1] 收尾：回溯器 cleanup → 关游戏 → 残留核对 → 配置逐字节还原
2026-11-12T15:58:52.488870+00:00     SymCleanup 完成
2026-11-12T15:59:05.375893+00:00     WM_CLOSE(hwnd=52760734) -> True
2026-11-12T15:59:05.375893+00:00     taskkill /PID 32448 (无 /F) rc=0 out='SUCCESS: Sent termination signal to the process with PID 32448.'
2026-11-12T15:59:05.375893+00:00     taskkill /F /PID 32448 rc=0 out='SUCCESS: The process with PID 32448 has been terminated.'
2026-11-12T15:59:05.375893+00:00     最终存活=False
2026-11-12T15:59:05.388780+00:00     收尾后 gamemd 残留 = 0 []
2026-11-12T15:59:05.800958+00:00     收尾后文件清单 647 项
2026-11-12T15:59:05.820414+00:00     还原 RA2MD.INI -> c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d
2026-11-12T15:59:05.820414+00:00     还原 ddraw.ini -> c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52
2026-11-12T15:59:05.820414+00:00     还原 RA2MD.INI.benchbak -> c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d
2026-11-12T15:59:05.820414+00:00     还原 gamemd.exe -> 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
2026-11-12T15:59:05.820414+00:00     还原 ddraw.dll -> 85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9
2026-11-12T15:57:31.759988+00:00 [S1] 启动前：只读资产自证 + 残留进程 + 实算 SHA-256
2026-11-12T15:57:31.767341+00:00     只读资产加载完成：W1 导航 / W3 抓栈 / r2 采样器 / e3_stackwalker
2026-11-12T15:57:31.767341+00:00     基准 7 帧：ntdll.dll+0x7858c → KERNELBASE.dll+0x16a1f0 → KERNELBASE.dll+0x16a18f → gamemd.exe+0x207f17 → USER32.dll+0x74775 → USER32.dll+0x3505d → gamemd.exe+0x20833f
2026-11-12T15:57:31.780036+00:00     gamemd 残留 = 0 []
2026-11-12T15:57:31.780551+00:00     RA2MD.INI                1754  c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d  match=True
2026-11-12T15:57:31.781084+00:00     ddraw.ini               14782  c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52  match=True
2026-11-12T15:57:31.781084+00:00     RA2MD.INI.benchbak       1754  c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d  match=True
2026-11-12T15:57:31.785046+00:00     gamemd.exe            4825360  73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476  match=True
2026-11-12T15:57:31.785577+00:00     ddraw.dll              411648  85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9  match=True
2026-11-12T15:57:32.170456+00:00     启动前文件清单 647 项
2026-11-12T15:57:32.170456+00:00 [S2] WMI 分离启动 gamemd.exe
2026-11-12T15:57:33.554121+00:00     pid=32448 归属=wmi_child_parent_pid launcher_pid=41260
2026-11-12T15:57:33.554121+00:00     IsWow64Process -> is32=True
2026-11-12T15:57:33.554121+00:00     代码签名@0x55DE4F = 'a0493da800' 期望 'a0493da800' -> ok=True
2026-11-12T15:57:53.571139+00:00 [S3] 导航 SinglePlayer -> Skirmish -> 按名称选图
2026-11-12T15:58:06.702117+00:00     地图命中：index=265 显示名='[8] Proving Grounds' 条目=268 命中数=1
2026-11-12T15:58:06.703631+00:00     游戏主窗口 hwnd=52760734
2026-11-12T15:58:07.706894+00:00     等待加载 15.0s
2026-11-12T15:58:22.707089+00:00 [S3b] 帧稳定推进观测 20.0s
2026-11-12T15:58:42.740428+00:00     样本=80 frame 340→959 Δ=619 最长连续不推进=0 拍
2026-11-12T15:58:42.740428+00:00 [S4] 挂起任何线程之前完成 StackWalk64/符号初始化
2026-11-12T15:58:42.743448+00:00     StackWalker ok=True err=None n_modules=111 is32=True max_frames=20 raw_bytes=65536
2026-11-12T15:58:42.744475+00:00     游戏窗口线程 tid=36700
2026-11-12T15:58:42.744475+00:00     自身线程守卫：GetCurrentThreadId=44656 ≠ 目标 tid=36700 ✓
2026-11-12T15:58:42.744475+00:00 [D0] 正常局内阴性对照：单次 ≤50ms 抓栈（平静、无交火）
2026-11-12T15:58:42.837250+00:00     抓栈 D0   tid=36700 bits=32 prev=0 frames=4 usable=True held=5.444ms resume_ret=1 state=resume_verified_ok sw_end=normal_end_of_walk raw_bytes=65536 key_on_raw=1/4
2026-11-12T15:58:42.837250+00:00       #0 ntdll.dll+0x7858c            addr=0x77c1858c
2026-11-12T15:58:42.837250+00:00       #1 KERNELBASE.dll+0x16a1f0      addr=0x763fa1f0
2026-11-12T15:58:42.837250+00:00       #2 KERNELBASE.dll+0x16a18f      addr=0x763fa18f
2026-11-12T15:58:42.837250+00:00       #3 gamemd.exe+0x15e332          addr=0x55e332
2026-11-12T15:58:42.840796+00:00     D0 state={"frame": 967, "g1": 0, "g2": 0, "g3": 0, "g4": 0, "mode": 5, "A8E9A0": 1, "ABCD58": 1, "exitstate": 0, "all_gates_zero": true, "any_gate_nonzero": false, "t_utc_iso": "2026-11-12T15:58:42.746001+00:00"}
2026-11-12T15:58:42.841838+00:00     [尝试1] Alt+F4 已在第 1 趟实测为致命（exit=0）；本趟跳过，从 ② 继续优先级序列
2026-11-12T15:58:42.841838+00:00 [T2] 尝试 ②：按控件文字找并点击 Abort/Exit/放弃类按钮（不猜索引）
2026-11-12T15:58:42.842997+00:00     正常局内无 Abort 类按钮；仅作导航按一次 Esc 暴露菜单按钮
2026-11-12T15:58:45.249001+00:00     点击按钮 'GUI:AbortMission' hwnd=2495812
2026-11-12T15:58:48.867390+00:00     [尝试2] 按控件文字点击 Abort/Exit/放弃类按钮 -> dialog_present=False (no=0 yes=0 abort=0 new_tops=0 dialog_tops=0) alive=True ec=259
2026-11-12T15:58:48.867390+00:00       后窗口=[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]
2026-11-12T15:58:48.867390+00:00       后按钮=["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]
2026-11-12T15:58:48.867390+00:00 [T3] 尝试 ③：局内菜单里 Restart/Exit to main menu 类按钮
2026-11-12T15:58:52.486866+00:00     [尝试3] 局内菜单 Restart/Exit to main menu 类按钮 -> dialog_present=False (no=0 yes=0 abort=0 new_tops=0 dialog_tops=0) alive=True ec=259
2026-11-12T15:58:52.486866+00:00       后窗口=[{"hwnd": 52760734, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 36700}, {"hwnd": 20122206, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 36700}, {"hwnd": 49813190, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 36700}, {"hwnd": 6621792, "cls": "IME", "text": "Default IME", "visible": false, "tid": 36700}]
2026-11-12T15:58:52.486866+00:00       后按钮=["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]
2026-11-12T15:58:52.486866+00:00 !! 三条路径均未产生确认对话框：按红线如实写「未能触发」，不伪造 D1/D2
2026-11-12T15:58:52.486866+00:00 [S5] 逐帧比对与判档
2026-11-12T15:58:52.487869+00:00     判档 = [未证实] (P1=未测 P2=未测 P3=未测 P4=未测)
2026-11-12T15:58:52.487869+00:00 [P1] 收尾：回溯器 cleanup → 关游戏 → 残留核对 → 配置逐字节还原
2026-11-12T15:58:52.488870+00:00     SymCleanup 完成
2026-11-12T15:59:05.375893+00:00     WM_CLOSE(hwnd=52760734) -> True
2026-11-12T15:59:05.375893+00:00     taskkill /PID 32448 (无 /F) rc=0 out='SUCCESS: Sent termination signal to the process with PID 32448.'
2026-11-12T15:59:05.375893+00:00     taskkill /F /PID 32448 rc=0 out='SUCCESS: The process with PID 32448 has been terminated.'
2026-11-12T15:59:05.375893+00:00     最终存活=False
2026-11-12T15:59:05.388780+00:00     收尾后 gamemd 残留 = 0 []
2026-11-12T15:59:05.800958+00:00     收尾后文件清单 647 项
2026-11-12T15:59:05.820414+00:00     还原 RA2MD.INI -> c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d
2026-11-12T15:59:05.820414+00:00     还原 ddraw.ini -> c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52
2026-11-12T15:59:05.820414+00:00     还原 RA2MD.INI.benchbak -> c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d
2026-11-12T15:59:05.820414+00:00     还原 gamemd.exe -> 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
2026-11-12T15:59:05.820414+00:00     还原 ddraw.dll -> 85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9
```

## 5. 收尾

- 收尾后 gamemd 残留: 0 `[]`

