# RUNLOG.md —— 真机只读观测执行日志

- run_id: `NEXT_RE_20261112_R02`
- 开始(UTC): `2026-11-12T14:32:36.324415+00:00`
- 结束(UTC): `2026-11-12T14:36:27.823467+00:00`
- 退出码: **0**
- 精确命令（脚本自身视角）: `C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe -X utf8 D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W1_realtime_probe\realtime_gate_probe.py --seconds 180 --interval 0.05 --map-pattern "Proving Grounds" --out gate_probe_R02b.ndjson`
- 外层启动器命令: 由 `pwsh` 后台作业执行，见本文件末尾补充。
- NDJSON: `D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W1_realtime_probe\out\gate_probe_R02b.ndjson`（3580 行，每行 flush）
- 参数: seconds=180.0 interval=0.05 map_pattern='Proving Grounds' menu_timeout=90.0 load_wait=15.0
- pid=42372 is32=True map={'index': 265, 'display_name': '[8] Proving Grounds', 'n_items': 268, 'n_hits': 1, 'pattern': 'Proving Grounds'}

## stdout 关键片段（完整输出见 `out/probe_stdout.txt`）

```text
2026-11-12T14:32:36.324415+00:00 [P0] NDJSON sink 已打开: D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W1_realtime_probe\out\gate_probe_R02b.ndjson
2026-11-12T14:32:36.324415+00:00 [S1] 启动前：残留进程 + 实算 SHA-256
2026-11-12T14:32:36.344548+00:00     gamemd 残留 = 0 []
2026-11-12T14:32:36.345056+00:00     RA2MD.INI          1754  c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d
2026-11-12T14:32:36.346058+00:00     ddraw.ini         14782  c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52
2026-11-12T14:32:36.353199+00:00     gamemd.exe      4825360  73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
2026-11-12T14:32:36.354705+00:00     ddraw.dll        411648  85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9
2026-11-12T14:32:36.891899+00:00     启动前文件清单 647 项
2026-11-12T14:32:36.893694+00:00 [S2] WMI 分离启动 gamemd.exe
2026-11-12T14:32:37.415228+00:00     WMI Create 返回 '45052|0' (stderr='')
2026-11-12T14:32:38.450371+00:00     pid=42372 归属判定=wmi_child_parent_pid (launcher_pid=45052)
2026-11-12T14:32:38.450371+00:00     IsWow64Process -> is32=True
2026-11-12T14:32:38.450371+00:00     代码签名@0x55DE4F = 'a0493da800' 期望 'a0493da800' -> ok=True
2026-11-12T14:32:58.475061+00:00     主菜单就绪（20.0s）
2026-11-12T14:32:58.475061+00:00 [S3] 导航 SinglePlayer -> Skirmish
2026-11-12T14:32:58.477575+00:00     click GUI:SinglePlayer       hwnd=31133454   -> True
2026-11-12T14:33:01.479186+00:00     click GUI:Skirmish           hwnd=8457708    -> True
2026-11-12T14:33:04.982760+00:00     click GUI:ChooseMap          hwnd=6820066    -> True
2026-11-12T14:33:07.985529+00:00     地图 ListBox=18485576 条目=268
2026-11-12T14:33:08.014282+00:00     命中 [265] '[8] Proving Grounds'
2026-11-12T14:33:08.014282+00:00     含 'Proving Grounds' 的条目共 1 个
2026-11-12T14:33:08.014282+00:00     LB_SETCURSEL(265) -> 0  显示名='[8] Proving Grounds'
2026-11-12T14:33:08.619224+00:00     click GUI:UseMap             hwnd=12915078   -> True
2026-11-12T14:33:11.624765+00:00     游戏主窗口 hwnd=30084836
2026-11-12T14:33:11.632314+00:00     click GUI:StartGame          hwnd=18288986   -> True
2026-11-12T14:33:12.633931+00:00     等待加载 15.0s
2026-11-12T14:33:27.634377+00:00 [S4] 开始只读轮询 180.0s @ 0.050s
2026-11-12T14:33:27.810136+00:00     初始置前游戏窗口 -> True
2026-11-12T14:33:27.810644+00:00     [event] t=0.00s phase_game_start -> game_start {}
2026-11-12T14:33:42.211211+00:00     [event] t=14.40s phase_stable_ingame -> stable_ingame {}
2026-11-12T14:34:04.937730+00:00     菜单按钮文字(前 25): ['GUI:ResumeMission', 'GUI:GameControls', 'GUI:LoadGame', 'GUI:AbortMission', 'GUI:SaveGame', 'GUI:DeleteGame']
2026-11-12T14:34:04.937730+00:00     [event] t=36.00s event_esc_open_menu -> menu_open_attempt {'action': 'keybd_event(VK_ESCAPE)', 'frame_at_menu': 1455, 'menu_button_texts': ['GUI:ResumeMission', 'GUI:GameControls', 'GUI:LoadGame', 'GUI:AbortMission', 'GUI:SaveGame', 'GUI:DeleteGame'], 'intent': '打开局内菜单（是否真的暂停以帧/门控读数为准）'}
2026-11-12T14:34:16.441445+00:00     返回对局动作: {'method': 'button', 'hwnd': 9836410, 'text': 'GUI:ResumeMission', 'clicked': True}
2026-11-12T14:34:16.441445+00:00     [event] t=48.63s event_esc_return_game -> return_to_game {'action': 'click_resume_button', 'result': {'method': 'button', 'hwnd': 9836410, 'text': 'GUI:ResumeMission', 'clicked': True}, 'intent': '从菜单返回对局'}
2026-11-12T14:34:29.039015+00:00     ★ 恢复校验: 菜单后 Δframe=395 resumed=True
2026-11-12T14:34:29.039015+00:00     [event] t=61.23s event_verify_resume -> stable_ingame {'frame_at_menu': 1455, 'frame_now': 1850, 'delta_since_menu': 395, 'resumed': True, 'resume_action': {'method': 'button', 'hwnd': 9836410, 'text': 'GUI:ResumeMission', 'clicked': True}}
2026-11-12T14:34:50.822938+00:00     [event] t=82.83s event_focus_lost -> focus_lost_window {'action': 'SetForegroundWindow(other_hwnd)', 'other_hwnd': 70980, 'success': True, 'intent': '窗口失焦'}
2026-11-12T14:35:07.072662+00:00     [event] t=99.01s event_focus_regained -> focus_regained_window {'action': 'SetForegroundWindow(game_hwnd)', 'success': True, 'intent': '切回游戏'}
2026-11-12T14:35:19.423383+00:00     [event] t=111.61s phase_stable_ingame_3 -> stable_ingame {}
2026-11-12T14:36:27.823467+00:00 [S4] 轮询结束：实际 180.013s，采样 3569 拍，读失败 0，退出事件 0
2026-11-12T14:36:27.823467+00:00 [P1] 收尾：关闭自启动实例
2026-11-12T14:36:40.821137+00:00     WM_CLOSE(hwnd=30084836) -> True
2026-11-12T14:36:40.821137+00:00     taskkill /PID 42372 (无 /F) rc=0 out='SUCCESS: Sent termination signal to the process with PID 42372.'
2026-11-12T14:36:40.821137+00:00     taskkill /F /PID 42372 rc=0 out='SUCCESS: The process with PID 42372 has been terminated.'
2026-11-12T14:36:40.821137+00:00     最终存活=False
2026-11-12T14:36:40.835241+00:00     收尾后 gamemd 残留 = 0 []
2026-11-12T14:36:41.532138+00:00     收尾后文件清单 647 项
2026-11-12T14:36:41.548729+00:00     还原 RA2MD.INI -> c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d
2026-11-12T14:36:41.548729+00:00     还原 ddraw.ini -> c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52
2026-11-12T14:36:41.548729+00:00     还原 RA2MD.INI.benchbak -> c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d
2026-11-12T14:36:41.548729+00:00     还原 gamemd.exe -> 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
2026-11-12T14:36:41.548729+00:00     还原 ddraw.dll -> 85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9
```

## 收尾

- WM_CLOSE(hwnd=30084836) -> True
- taskkill /PID 42372 (无 /F) rc=0 out='SUCCESS: Sent termination signal to the process with PID 42372.'
- taskkill /F /PID 42372 rc=0 out='SUCCESS: The process with PID 42372 has been terminated.'
- 最终存活=False
- 收尾后 gamemd 残留: 0 []

## 外层启动器命令（两趟，`pwsh` 后台作业）

工作目录 `D:\Project\ra2-campaign-forge`，策略 `danger-full-access`，
`$py = C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe`，
`$d = ...\W1_realtime_probe`。两趟均用 `*>` 把全部流重定向到日志。

**Run 1（2026-11-12 14:24:28Z → 14:30:35Z，退出码 0）**

```powershell
& $py -X utf8 (Join-Path $d 'realtime_gate_probe.py') --seconds 300 --interval 0.05 --map-pattern 'Proving Grounds' --out 'out\gate_probe_R02.ndjson' *> (Join-Path $d 'out\probe_console.log')
```

- job id `pwsh-e3842350b5554bba`；`PROBE_EXIT=0`
- NDJSON: `out\out\gate_probe_R02.ndjson`（6001 行；`--out` 相对路径当时被叠加了一次 `out\`，
  故落在 `out\out\`，已另存字节完全一致的顶层副本 `out\gate_probe_R02.ndjson`）
- 5989 采样拍 / 300.030 s / 读失败 0 / 退出事件 0
- pid=41052, is32=True, `0x55DE4F` 代码签名 ok=True
- 收尾：WM_CLOSE → `taskkill /PID 41052` → `taskkill /F /PID 41052`；残留 0
- 报告原件保存在 `out\run1\`（`CONFIG_RESTORE.md` / `RUNLOG.md` / `ANALYSIS.md` /
  `UNCOVERED.md` / `run_meta.json` / `analysis.json` / `probe_stdout.txt` /
  `probe_console.log`），**未被改写**

**Run 2（2026-11-12 14:32:36Z → 14:36:41Z，退出码 0）—— 主判据**

```powershell
& $py -X utf8 (Join-Path $d 'realtime_gate_probe.py') --seconds 180 --interval 0.05 --map-pattern 'Proving Grounds' --out 'gate_probe_R02b.ndjson' *> (Join-Path $d 'out\probe_console_run2.log')
```

- job id `pwsh-41c51d6fbd9448c4`；`PROBE_EXIT=0`
- NDJSON: `out\gate_probe_R02b.ndjson`（3581 行）
- 3569 采样拍 / 180.013 s / 读失败 0 / 退出事件 0
- pid=42372, is32=True, 代码签名 ok=True
- 收尾：WM_CLOSE → `taskkill /PID 42372` → `taskkill /F /PID 42372`；残留 0

**为什么有第二趟**：Run 1 在 t=60 s 发第一记 Esc 打开局内菜单后，
第二记 Esc 未返回对局，帧计数从 2213 冻结到结束（约 240 s），
属于**观测自身引入的菜单暂停**，不是自然卡顿。
Run 2 改为按控件文字点击 `GUI:ResumeMission`（hwnd=9836410），
并加了 `event_verify_resume` 校验（菜单后 Δframe=395，resumed=True）。
第二趟缩短到 180 s（任务卡允许下限 120 s），原因：首趟已消耗约 10 分钟
准备与首轮 300 s 观测，为避免额度/时间不足而无法完成 P1 还原与交付，
主动缩短第二趟并如实写明。

**离线重算命令（P2，只从 ndjson）**

```powershell
& $py -X utf8 (Join-Path $d 'analyze_probe.py') --ndjson 'out\out\gate_probe_R02.ndjson' --ndjson 'out\gate_probe_R02b.ndjson' --md (Join-Path $d 'ANALYSIS.md') --uncovered (Join-Path $d 'UNCOVERED.md') --json (Join-Path $d 'out\analysis.json')
```

退出码 0；stdout: `analyze_probe OK: ... samples=3569 ok=3569 fail=0 adv_false=230 all_zero_no_adv=230 longest_ms=11450.175 comparison=1`

**两趟共同 stdout 关键片段**（见 `out\probe_stdout.txt` / `out\run1\probe_stdout.txt`）：
`RA2MD.INI c91c6a...` 通过启动前守卫；`命中 [265] '[8] Proving Grounds'`；
`代码签名@0x55DE4F = 'a0493da800'`；`轮询结束 ... 读失败 0`；
`[P1] 收尾完成（配置已还原 ...）`。

