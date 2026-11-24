# RUNLOG.md —— 真机单变量判决实验执行日志

- run_id: `NEXT_RE_20261112_R02`
- 开始(UTC): `2026-11-12T16:04:56.101509+00:00`；结束(UTC): `2026-11-12T16:06:31.775501+00:00`；本地: `2026-11-13T00:23:43.302471+08:00`
- 退出码: **0**
- 命令: `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -X utf8 D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W4_exit_dialog\exit_dialog_probe.py --map-pattern Proving Grounds --load-wait 15 --stable-seconds 20 --budget-ms 50 --r2-event-budget-ms 300 --max-frames 20 --raw-stack-bytes 65536 --menu-timeout 90 --dialog-timeout 12 --d1-count 3 --skip-altf4`
- Python: `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe` / `3.12.10`
- 写域: `lead/next_re_20261112_r02/W4_exit_dialog/`（其余资产只读复用）

## 0. 三趟真机串行（最终判档以第 3 趟为准）

| 趟 | 时间(UTC) | pid | 结果 | 归档 |
|---|---|---|---|---|
| 1 | 15:52:57–15:54:11 | 16052 | ① Alt+F4 直接退出 exit=0；D0 完整；无 D1/D2 | `run1/`、`out/run1/`、`out/_pre_run3_stale/` |
| 2 | 15:57:31–15:59:05 | 32448 | ②③ 已触发 `GUI:AskAbortMission` 确认对话框（稳定 >3.2s），但 UI 判据漏检位图按钮，误报「未能触发」 | `run2/`、`out/run2/` |
| 3 | 16:04:56–16:06:45 | 4856 | 修复判据后完整跑完 D0/D1a/D1b/D1c/D2，判档 `[否证]` | 本目录 `out/*.json`（主判据） |

三趟均为**单实例串行**，各自重新过 §0 守卫、独立收尾还原、残留进程 0；未同时存在两个 gamemd，未杀任何其它进程。偏离「不要重启补测」的完整理由见 VERDICT.md §0.1。

> 完整性 caveat：比对 `run1/RUNLOG.md` 与 `run2/RUNLOG.md` 头部可证，有**外部代理在第 1 趟与第 2 趟之间并发编辑过本脚本**，把 §1 的硬编码 `call_agy.py(pid 36676)` 说明换成动态生成版本，并在后续给 `classify_button` 加了中文加速键后缀（否(N)/是(Y)）支持；同时该代理在 约 00:01 本地另跑过一趟真机（pid 13260，同样记录 Alt+F4 直接退出 exit=0，产物混在 `out/_pre_run3_stale/`），并在本目录留下 `RUNS.md` 与 `selftest_offline.py`（后者离线自检 `ALL PASS`）。这些改动只涉及文档渲染字符串与文字分类器健壮性，**未触及地址常量、抓栈实现、判据与读数逻辑**；本卡所有原始读数/帧序列/恢复返回值均来自脚本运行时落盘的 `out/*.json`，主交付 `out/*.json` 经核对 pid=4856 / tid=9832（本卡第 3 趟），逐趟可独立复核。本卡每次启动前均实测 `list_gamemd()==[]`，未与并行实例同时存在。

## 1. 防双开守卫（脚本内实测，动态生成）

- 脚本内 `list_gamemd()` 启动前残留：**0** 个 `[]`。
- 哈希守卫：`prelaunch_match_all = True`（逐文件明细见 CONFIG_RESTORE.md §1）。
- 防双开纪律：本脚本只启动 1 个 gamemd 实例并全程只处理该 pid；对其它进程只读不动、未杀任何进程；运行期间若出现其它 gamemd 仅登记不处理。

## 2. 关键参数与实测

```json
{
 "args": {
  "budget_ms": 50.0,
  "d1_count": 3,
  "dialog_timeout": 12.0,
  "load_wait": 15.0,
  "map_pattern": "Proving Grounds",
  "max_frames": 20,
  "menu_timeout": 90.0,
  "out": "",
  "r2_event_budget_ms": 300.0,
  "raw_stack_bytes": 65536,
  "skip_altf4": true,
  "stable_seconds": 20.0
 },
 "pid": 4856,
 "launcher_pid": 42996,
 "ownership": "wmi_child_parent_pid",
 "is32": true,
 "code_signature_ok": true,
 "map": {
  "display_name": "[8] Proving Grounds",
  "index": 265,
  "n_hits": 1,
  "n_items": 268,
  "pattern": "Proving Grounds"
 },
 "map_index": 265,
 "game_hwnd": 23268762,
 "window_tid": 9832,
 "self_tid": 17512,
 "walker": {
  "err": null,
  "is32": true,
  "max_frames": 20,
  "mods": [
   {
    "base": "0x400000",
    "name": "gamemd.exe",
    "size": 7954432
   },
   {
    "base": "0x7ffb36400000",
    "name": "ntdll.dll",
    "size": 2523136
   },
   {
    "base": "0x400000",
    "name": "gamemd.exe",
    "size": 7954432
   },
   {
    "base": "0x77ba0000",
    "name": "ntdll.dll",
    "size": 1835008
   },
   {
    "base": "0x76290000",
    "name": "KERNELBASE.dll",
    "size": 2985984
   },
   {
    "base": "0x778f0000",
    "name": "USER32.dll",
    "size": 2019328
   }
  ],
  "n_modules": 111,
  "ok": true
 },
 "prelaunch_match_all": true,
 "frame_stable_summary": {
  "frame_advanced": true,
  "frame_first": 208,
  "frame_last": 832,
  "frame_net_delta": 624,
  "interval": 0.25,
  "max_consecutive_nonadvance_samples": 0,
  "n_samples": 80,
  "seconds_target": 20.0
 },
 "d0_label": "D0",
 "dialog_meta": {
  "note": "对话框证据逐趟完整留存于 out/D1*.json 的 dialog_evidence；UI 判据独立于 P2/P3/P4 读数",
  "stable": true,
  "successful_method": "按控件文字点击 Abort/Exit/放弃类按钮"
 },
 "p3_check": {
  "delta": 0,
  "frame_a": 850,
  "frame_b": 850,
  "g4_a": 0,
  "g4_b": 0,
  "interval_s": 1.0,
  "stopped": true
 },
 "p4_check": {
  "close_action": {
   "attempts": [
    {
     "click": {
      "clicked": true,
      "hwnd": 1706036,
      "text": "GUI:ResumeMission"
     },
     "kind": "gui_resumemission_cancel",
     "resume_check": {
      "delta": 31,
      "frame_a": 878,
      "frame_b": 909,
      "interval_s": 1.0,
      "resumed": true,
      "state_after": {
       "A8E9A0": 1,
       "ABCD58": 1,
       "all_gates_zero": true,
       "any_gate_nonzero": false,
       "exitstate": 0,
       "frame": 909,
       "g1": 0,
       "g2": 0,
       "g3": 0,
       "g4": 0,
       "mode": 5,
       "t_utc_iso": "2026-11-12T16:06:31.667807+00:00"
      },
      "tag": "D2_try_gui_resumemission_cancel"
     }
    }
   ],
   "buttons_after": [],
   "buttons_seen": [
    {
     "ctrl_id": 1670,
     "hwnd": 1706036,
     "rect": [
      813,
      468,
      896,
      485
     ],
     "text": "GUI:ResumeMission",
     "visible": true
    },
    {
     "ctrl_id": 1737,
     "hwnd": 7078168,
     "rect": [
      813,
      151,
      896,
      168
     ],
     "text": "GUI:Blank",
     "visible": true
    },
    {
     "ctrl_id": 1810,
     "hwnd": 22675732,
     "rect": [
      813,
      168,
      896,
      185
     ],
     "text": "GUI:Blank",
     "visible": false
    }
   ],
   "captions_seen": [
    {
     "cls": "Static",
     "hwnd": 5638104,
     "rect": [
      287,
      235,
      518,
      256
     ],
     "text": "GUI:AskAbortMission"
    },
    {
     "cls": "Static",
     "hwnd": 10291158,
     "rect": [
      7,
      498,
      310,
      511
     ],
     "text": "GUI:Blank"
    }
   ],
   "clicked": {
    "clicked": true,
    "hwnd": 1706036,
    "text": "GUI:ResumeMission"
   },
   "controls_after": [],
   "dialog_present_after": false,
   "method": "BM_CLICK by control text (gui_resumemission_cancel)",
   "tops_after": [
    {
     "cls": "Yuri's Revenge",
     "hwnd": 23268762,
     "text": "Yuri's Revenge",
     "tid": 9832,
     "visible": true
    },
    {
     "cls": "OleDdeWndClass",
     "hwnd": 2294596,
     "text": "DDE Server Window",
     "tid": 9832,
     "visible": false
    },
    {
     "cls": "MSCTFIME UI",
     "hwnd": 3215666,
     "text": "MSCTFIME UI",
     "tid": 9832,
     "visible": false
    },
    {
     "cls": "IME",
     "hwnd": 2492680,
     "text": "Default IME",
     "tid": 9832,
     "visible": false
    }
   ]
  },
  "delta_frame": 31,
  "extra_action": null,
  "frame_after_close": 878,
  "frame_later": 909,
  "gates_after_close": {
   "A8E9A0": 1,
   "ABCD58": 1,
   "all_gates_zero": true,
   "any_gate_nonzero": false,
   "exitstate": 0,
   "frame": 909,
   "g1": 0,
   "g2": 0,
   "g3": 0,
   "g4": 0,
   "mode": 5,
   "t_utc_iso": "2026-11-12T16:06:31.667807+00:00"
  },
  "interval_s": 1.0,
  "resume_checks": [
   {
    "delta": 31,
    "frame_a": 878,
    "frame_b": 909,
    "interval_s": 1.0,
    "resumed": true,
    "state_after": {
     "A8E9A0": 1,
     "ABCD58": 1,
     "all_gates_zero": true,
     "any_gate_nonzero": false,
     "exitstate": 0,
     "frame": 909,
     "g1": 0,
     "g2": 0,
     "g3": 0,
     "g4": 0,
     "mode": 5,
     "t_utc_iso": "2026-11-12T16:06:31.667807+00:00"
    },
    "tag": "D2_try_gui_resumemission_cancel"
   }
  ],
  "resumed": true,
  "resumed_after_extra_action": false
 },
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

- 动作: {"candidates": [{"hwnd": 10225622, "text": "GUI:AbortMission"}], "clicked": {"clicked": true, "hwnd": 10225622, "text": "GUI:AbortMission"}, "keyword_rule": "classify_button(text)=='abort'，按文字而非索引", "menu_button_texts": ["GUI:ResumeMission", "GUI:GameControls", "GUI:LoadGame", "GUI:AbortMission", "GUI:SaveGame", "GUI:DeleteGame"], "opened_esc_menu_as_route": true}
- 结果: `dialog_present=True`；进程存活=True；退出码=259
- 判据: no=0 yes=0 abort=0 captions=1 new_containers=1 new_tops=0 dialog_tops=0
- 触发前顶层窗口: `[{"hwnd": 23268762, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 9832}, {"hwnd": 2294596, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 9832}, {"hwnd": 3215666, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 9832}, {"hwnd": 2492680, "cls": "IME", "text": "Default IME", "visible": false, "tid": 9832}]`
- 触发前按钮文字: `["GUI:ResumeMission", "GUI:GameControls", "GUI:LoadGame", "GUI:AbortMission", "GUI:SaveGame", "GUI:DeleteGame"]`
- 触发后顶层窗口: `[{"hwnd": 23268762, "cls": "Yuri's Revenge", "text": "Yuri's Revenge", "visible": true, "tid": 9832}, {"hwnd": 2294596, "cls": "OleDdeWndClass", "text": "DDE Server Window", "visible": false, "tid": 9832}, {"hwnd": 3215666, "cls": "MSCTFIME UI", "text": "MSCTFIME UI", "visible": false, "tid": 9832}, {"hwnd": 2492680, "cls": "IME", "text": "Default IME", "visible": false, "tid": 9832}]`
- 触发后按钮文字: `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]`
- 触发后全部有文字控件: `["GUI:ResumeMission", "GUI:AskAbortMission", "GUI:Blank", "GUI:Blank", "GUI:Blank"]`
- 触发后轮询观察（每 0.4s，捕捉延迟/短暂出现的对话框）：

  | t_s | dialog_present | 判据 | 顶层窗口 | 按钮文字 |
  |---|---|---|---|---|
  | 0.003 | True | `no=0 yes=0 abort=0 captions=1 new_containers=1 new_tops=0 dialog_tops=0` | `[{"cls": "Yuri's Revenge", "hwnd": 23268762, "text": "Yuri's Revenge", "tid": 9832, "visible": true}, {"cls": "OleDdeWndClass", "hwnd": 2294596, "text": "DDE Server Window", "tid": 9832, "visible": false}, {"cls": "MSCTFIME UI", "hwnd": 3215666, "text": "MSCTFIME UI", "tid": 9832, "visible": false}, {"cls": "IME", "hwnd": 2492680, "text": "Default IME", "tid": 9832, "visible": false}]` | `["GUI:ResumeMission", "GUI:Blank", "GUI:Blank"]` |

## 4. stdout（完整输出见 `out/stdout.txt` / `out/console.txt`）

```text
```

## 5. 收尾

- WM_CLOSE(hwnd=23268762) -> True
- taskkill /PID 4856 (无 /F) rc=0 out='SUCCESS: Sent termination signal to the process with PID 4856.'
- taskkill /F /PID 4856 rc=0 out='SUCCESS: The process with PID 4856 has been terminated.'
- 最终存活=False
- 收尾后 gamemd 残留: 0 `[]`

