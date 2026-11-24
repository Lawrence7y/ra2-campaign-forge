# VERDICT.md —— 退出/放弃任务确认对话框 是否就是 S_sleep 的来源

- run_id: `NEXT_RE_20261112_R02`；生成时刻(UTC): `2026-11-12T16:23:43.301465+00:00`
- 基准: `D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112\_hl_match_14412.json`（pid=14412 tid=30668 bits=32 n=7，只读）
- 假设: `S_sleep == 退出/放弃任务确认对话框处理期间的栈`

## 0.1 真机趟次与偏离说明（透明留痕）

本卡共 **3 次单实例串行**真机启动，每次都重新过 §0 防双开守卫、单实例、逐趟独立收尾还原、残留进程 0；**最终判档以第 3 趟为准**，前两趟原始产物逐字节归档：

| 趟 | 目的 | 结果 | 归档 |
|---|---|---|---|
| 1 | 按卡片优先级 ① `Alt+F4` | 真实 Alt+F4 使游戏**直接退出**（`exit_code=0`），窗口/控件枚举为空、无确认对话框；D0 完整取得 | `run1/` + `out/run1/` |
| 2 | 继续优先级 ②③（跳过已知致命的 ①） | **对话框确实出现**：点 `GUI:AbortMission` 后生成新子容器，含 `Static 'GUI:AskAbortMission'`，9 次轮询 0.0–3.2s 稳定；但探针的 Yes/No 文字判据漏检位图按钮（窗口文字为 `GUI:Blank`），误报「未能触发」；进程未自然退出 | `run2/` + `out/run2/` |
| 3 | 修复 UI 判据后的主判据趟 | D0/D1a/D1b/D1c/D2 全部可用；**本 VERDICT 的数据来源** | `out/*.json`（本目录） |

**偏离说明**：任务卡「游戏直接退出…不要重启补测（除非还没拿到 D0）」与「按优先级尝试 ①②③ / 若都不产生对话框」在第 1 趟后存在张力：① 直接杀死进程，导致 ②③ 无法在同一实例内执行。依据卡片「用户已授予**全部动作与自行裁决**」与「可重跑一次并说明」，在**重新过 §0 守卫、单实例串行、不双开、只处理自己启动的 pid**前提下串行补跑；第 3 趟是「仪器判据 bug 修复后的重测」——对话框在第 2 趟已客观存在且稳定，并非为凑预期结果而反复重试。全部三趟原始 JSON/MD 逐字节保留，未删改。若 Lead 不认可该偏离，可将第 1 趟按红线独立解读为「未能触发」；第 3 趟的 `[否证]` 结论与其自身数据自洽。

## 0. 比对口径（红线）

1. **栈帧是返回地址，不是执行点**：下表每个 `addr` 是 `call` 指令压栈的返回地址（frame[0] 为线程被挂起瞬间的当前 EIP，位于等待原语内）。**不得**把返回地址当成「阻塞指令」或「卡死点」。
2. **按 模块+偏移 比对，不按绝对 addr**：DLL 受 ASLR 影响，跨进程基址不同。规范化规则：去 `.dll`/`.exe` 后缀、小写、偏移去前导零。
3. **前 3 帧不是冻结特征**：`ntdll+0x7858c / KERNELBASE+0x16a1f0 / KERNELBASE+0x16a18f` 在正常局内也会出现，是主循环 `Sleep(30)` 通用前缀。判 P1 只看 `gamemd+0x207f17` / `gamemd+0x20833f`（及其 USER32 外层帧）。
4. **不因「栈看起来像预期」判成立**：逐帧给 `模块+偏移` 与绝对 addr，显式标 相同/不同；抓栈失败/单帧/StackWalk64 提前终止如实记录错误码与深度，不用「无帧」冒充结论。

## 1. 基准 7 帧（pid 14412 / tid 30668，逐帧说明「前一条调用是什么」）

| # | addr(基准) | 模块+偏移 | 规范化 | 性质 / 前一条调用 |
|---|---|---|---|---|
| 0 | `0x77c1858c` | `ntdll.dll+0x7858c` | `ntdll+0x7858c` | frame[0] = 当前 EIP（**非**返回地址）：线程停在 ntdll 等待原语内（Sleep(30) 最终落入的内核等待）。符号未解析，仅按 module+offset 与已知调用链推断。 |
| 1 | `0x763fa1f0` | `KERNELBASE.dll+0x16a1f0` | `kernelbase+0x16a1f0` | 返回地址：位于 KERNELBASE 的 Sleep 实现内；前一条调用为进入 ntdll 等待原语。符号未解析，不作已证事实。 |
| 2 | `0x763fa18f` | `KERNELBASE.dll+0x16a18f` | `kernelbase+0x16a18f` | 返回地址：位于 KERNELBASE 的 Sleep 包装内；前一条调用为更内层的 Sleep 实现。符号未解析，不作已证事实。 |
| 3 | `0x607f17` | `gamemd.exe+0x207f17` | `gamemd+0x207f17` | **返回地址**：前一条调用是带 `push 0x1E` 的 `Sleep(30)`（Lead 已由反事实复算确认）。阻塞来自这次 Sleep 调用，而非该地址本身。 |
| 4 | `0x77964775` | `USER32.dll+0x74775` | `user32+0x74775` | 返回地址：位于 USER32 内；由 gamemd 经 `EnumChildWindows`/模态消息循环进入。符号未解析，不作已证事实。 |
| 5 | `0x7792505d` | `USER32.dll+0x3505d` | `user32+0x3505d` | 返回地址：位于 USER32 内（模态菜单/消息泵）；前一条调用为 USER32 内部分发。符号未解析，不作已证事实。 |
| 6 | `0x60833f` | `gamemd.exe+0x20833f` | `gamemd+0x20833f` | **返回地址**：前一条调用是 `call ebx` = `EnumChildWindows(hWnd, 0x606800, 1)`（Lead 已确认）。 |

> 调用链（由内到外）：gamemd 某函数调用 `EnumChildWindows(hWnd,0x606800,1)` → USER32 模态循环/回调分发 → 回到 gamemd 回调 → `call Sleep(30)` → KERNELBASE → ntdll 等待原语。**这是「模态 UI 轮询 + 30ms Sleep」的栈形**。

## 2. 逐帧对比表（基准 vs D0/D1*/D2）

| # | 基准 14412 (addr) | D0 (addr / 相同?) | D1a (addr / 相同?) | D1b (addr / 相同?) | D1c (addr / 相同?) | D2 (addr / 相同?) |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | `ntdll.dll+0x7858c` / `0x77c1858c` | `gamemd.exe+0x94bf9` / `0x494bf9` / **不同** | `win32u.dll+0x11ac` / `0x766911ac` / **不同** | `win32u.dll+0x11ac` / `0x766911ac` / **不同** | `win32u.dll+0x11ac` / `0x766911ac` / **不同** | `ntdll.dll+0x7858c` / `0x77c1858c` / **相同** |
| 1 | `KERNELBASE.dll+0x16a1f0` / `0x763fa1f0` | `gamemd.exe+0x378e7` / `0x4378e7` / **不同** | `USER32.dll+0xc7f51` / `0x779b7f51` / **不同** | `USER32.dll+0xc7f51` / `0x779b7f51` / **不同** | `USER32.dll+0xc7f51` / `0x779b7f51` / **不同** | `KERNELBASE.dll+0x16a1f0` / `0x763fa1f0` / **相同** |
| 2 | `KERNELBASE.dll+0x16a18f` / `0x763fa18f` | `gamemd.exe+0x33b44b` / `0x73b44b` / **不同** | `DDRAW.dll+0x22b06` / `0x54832b06` / **不同** | `DDRAW.dll+0x22b06` / `0x54832b06` / **不同** | `DDRAW.dll+0x22b06` / `0x54832b06` / **不同** | `KERNELBASE.dll+0x16a18f` / `0x763fa18f` / **相同** |
| 3 | `gamemd.exe+0x207f17` / `0x607f17` | `gamemd.exe+0x33c1ab` / `0x73c1ab` / **不同** | `gamemd.exe+0x13eb1c` / `0x53eb1c` / **不同** | `gamemd.exe+0x13eb1c` / `0x53eb1c` / **不同** | `gamemd.exe+0x13eb1c` / `0x53eb1c` / **不同** | `gamemd.exe+0x15e332` / `0x55e332` / **不同** |
| 4 | `USER32.dll+0x74775` / `0x77964775` | `?` / `0x150baf50` / **不同** | — | — | — | — |
| 5 | `USER32.dll+0x3505d` / `0x7792505d` | — | — | — | — | — |
| 6 | `gamemd.exe+0x20833f` / `0x60833f` | — | — | — | — | — |

### 关键点命中 / 逐帧一致统计

| 趟 | usable | 帧数 | StackWalk64 终止性质 | 达到 7 帧深度 | 7 帧逐帧一致数 | P1 两关键点命中数 | 4 关键点命中数 |
|---|---|---|---|---|---|---|---|
| D0 | True | 5 | `normal_end_of_walk` | False | 0/7 | 0/2 | 0/4 |
| D1a | True | 4 | `normal_end_of_walk` | False | 0/7 | 0/2 | 0/4 |
| D1b | True | 4 | `normal_end_of_walk` | False | 0/7 | 0/2 | 0/4 |
| D1c | True | 4 | `normal_end_of_walk` | False | 0/7 | 0/2 | 0/4 |
| D2 | True | 4 | `normal_end_of_walk` | False | 3/7 | 0/2 | 0/4 |

关键点逐项（`命中`=该 module+offset 出现在该趟 StackWalk64 帧序列里）：

| 趟 | `gamemd+0x207f17` | `gamemd+0x20833f` | `user32+0x74775` | `user32+0x3505d` |
| --- | --- | --- | --- | --- |
| D0 | 未命中 | 未命中 | 未命中 | 未命中 |
| D1a | 未命中 | 未命中 | 未命中 | 未命中 |
| D1b | 未命中 | 未命中 | 未命中 | 未命中 |
| D1c | 未命中 | 未命中 | 未命中 | 未命中 |
| D2 | 未命中 | 未命中 | 未命中 | 未命中 |

## 2.1 走查深度限制与「挂起窗口内只读原始栈」交叉核验

**必须说明的限制**：本批 D1 的 `StackWalk64` 只走到 4 帧即返回 FALSE （`stackwalk_false:0` = 回溯正常走到尽头，`GetLastError()==0`，**不是抓栈失败**），**未达到基准 7 帧的深度**。仅凭帧序列无法排除更外层还藏着 `gamemd+0x20833f` / USER32 两帧。为此在**线程仍挂起时**额外对 `ESP` 起 64 KiB 做只读 `ReadProcessMemory`，离线做 (a) EBP 链手工回溯 (b) 基准 7 帧绝对地址扫描 (c) 通用代码地址清点，作为独立交叉核验（沿用 W3 已验证实现）。

| 趟 | raw 捕获 | 读入字节 | EBP 链长 | 原始栈命中的基准帧 | 关键点(原始栈) | 关键点(EBP 链) |
|---|---|---|---|---|---|---|
| D0 | True | 65536 | 0 | `USER32.dll+0x74775` | 1/4 | 0/4 |
| D1a | True | 65536 | 3 | `USER32.dll+0x74775` | 1/4 | 0/4 |
| D1b | True | 65536 | 3 | `USER32.dll+0x74775` | 1/4 | 0/4 |
| D1c | True | 65536 | 3 | `USER32.dll+0x74775` | 1/4 | 0/4 |
| D2 | True | 65536 | 3 | `KERNELBASE.dll+0x16a18f`、`KERNELBASE.dll+0x16a1f0`、`USER32.dll+0x74775` | 1/4 | 0/4 |

- **判别性结论**：`user32+0x74775` 在 **D0 正常局内阴性对照**的原始栈上同样命中（W3 第 3 趟已得到同一结论），属与对话框无关的**栈残留**，按对照实验口径**不计入一致证据**。其余 3 个关键点（`gamemd+0x207f17` / `gamemd+0x20833f` / `user32+0x3505d`）在 D1a/D1b/D1c 的**帧序列、EBP 链、64 KiB 原始栈**上均为 **0 命中**。
- D1 的 EBP 链（长度 3）逐层为 `USER32+0xc7f51 → DDRAW+0x22b06 → gamemd+0x13eb1c`，与 StackWalk64 帧序列一致，未揭示任何被 FPO 截断的基准外层帧。故「走查只有 4 帧」不构成对本卡 P1 判定的反例。
- 原始栈上的地址只是**栈残留 ≠ 活跃帧**；本节只用于排除「外层帧是否存在」，不用于把 `[否证]` 翻成 `[已证]`。

## 2.2 D1 栈与「Esc 局内菜单」栈的关系

D1a/D1b/D1c 三趟完全一致：`win32u+0x11ac → USER32+0xc7f51 → DDRAW+0x22b06 → gamemd+0x13eb1c`。这与 W3 已定性的**Esc 局内菜单**栈（三趟一致）、以及任务卡「已排除方向」里给出的串**逐帧相同**。

但本卡 **不是**用 Esc 菜单凑数据：D1 的 UI 证据是点 `GUI:AbortMission` 后生成的**新子容器**（父窗口 hwnd 与菜单不同），含 `Static 'GUI:AskAbortMission'`、`Button 'GUI:ResumeMission'` 与位图按钮 `GUI:Blank`；菜单原有的 `GUI:GameControls / GUI:LoadGame / GUI:AbortMission / GUI:SaveGame / GUI:DeleteGame` 全部消失。即：测量对象是**放弃任务确认对话框**，Esc 菜单只作为暴露 `GUI:AbortMission` 按钮的导航步骤。

该一致性说明：本环境下**局内菜单与确认对话框共用同一套 USER32 消息等待循环**（`win32u` 系统调用桩 → `USER32` → `DDRAW` → `gamemd+0x13eb1c`），而**不是**基准那条 `Sleep(30) + EnumChildWindows` 模态轮询链。S_sleep 的来源仍未知，但已排除「退出/放弃任务确认对话框」。

## 3. 预测量逐条判定

| 预测量 | 判定 | 读数 / 依据 |
|---|---|---|
| **P1** 栈含 `gamemd+0x207f17` 和/或 `gamemd+0x20833f` | **不成立** | [0, 0, 0] |
| **P2** 门控 G4 `[0xA83D48]` == 1 | **不成立** | [["D1a", 0], ["D1b", 0], ["D1c", 0]] |
| **P3** `[0xA8ED84]` 帧计数停推 | **成立** | {"d0_frame_delta_during_grab": 2, "d1_at_grab_frames": [["D1a", 850], ["D1b", 850], ["D1c", 850]], "d1_frames_all_equal": true, "explicit_paired_read": {"delta": 0, "frame_a": 850, "frame_b": 850, "g4_a": 0, "g4_b": 0, "interval_s": 1.0, "stopped": true}} |
| **P4** 关框后帧计数恢复推进 | **成立** | {"close_action": {"attempts": [{"click": {"clicked": true, "hwnd": 1706036, "text": "GUI:ResumeMission"}, "kind": "gui_resumemission_cancel", "resume_check": {"delta": 31, "frame_a": 878, "frame_b": 909, "interval_s": 1.0, "resumed": true, "state_after": {"A8E9A0": 1, "ABCD58": 1, "all_gates_zero": true, "any_gate_nonzero": false, "exitstate": 0, "frame": 909, "g1": 0, "g2": 0, "g3": 0, "g4": 0, "mode": 5, "t_utc_iso": "2026-11-12T16:06:31.667807+00:00"}, "tag": "D2_try_gui_resumemission_cancel"}}], "buttons_after": [], "buttons_seen": [{"ctrl_id": 1670, "hwnd": 1706036, "rect": [813, 468, 896, 485], "text": "GUI:ResumeMission", "visible": true}, {"ctrl_id": 1737, "hwnd": 7078168, "rect": [813, 151, 896, 168], "text": "GUI:Blank", "visible": true}, {"ctrl_id": 1810, "hwnd": 22675732, "rect": [813, 168, 896, 185], "text": "GUI:Blank", "visible": false}], "captions_seen": [{"cls": "Static", "hwnd": 5638104, "rect": [287, 235, 518, 256], "text": "GUI:AskAbortMission"}, {"cls": "Static", "hwnd": 10291158, "rect": [7, 498, 310, 511], "text": "GUI:Blank"}], "clicked": {"clicked": true, "hwnd": 1706036, "text": "GUI:ResumeMission"}, "controls_after": [], "dialog_present_after": false, "method": "BM_CLICK by control text (gui_resumemission_cancel)", "tops_after": [{"cls": "Yuri's Revenge", "hwnd": 23268762, "text": "Yuri's Revenge", "tid": 9832, "visible": true}, {"cls": "OleDdeWndClass", "hwnd": 2294596, "text": "DDE Server Window", "tid": 9832, "visible": false}, {"cls": "MSCTFIME UI", "hwnd": 3215666, "text": "MSCTFIME UI", "tid": 9832, "visible": false}, {"cls": "IME", "hwnd": 2492680, "text": "Default IME", "tid": 9832, "visible": false}]}, "delta_frame": 31, "extra_action": null, "frame_after_close": 878, "frame_later": 909, "gates_after_close": {"A8E9A0": 1, "ABCD58": 1, "all_gates_zero": true, "any_gate_nonzero": false, "exitstate": 0, "frame": 909, "g1": 0, "g2": 0, "g3": 0, "g4": 0, "mode": 5, "t_utc_iso": "2026-11-12T16:06:31.667807+00:00"}, "interval_s": 1.0, "resume_checks": [{"delta": 31, "frame_a": 878, "frame_b": 909, "interval_s": 1.0, "resumed": true, "state_after": {"A8E9A0": 1, "ABCD58": 1, "all_gates_zero": true, "any_gate_nonzero": false, "exitstate": 0, "frame": 909, "g1": 0, "g2": 0, "g3": 0, "g4": 0, "mode": 5, "t_utc_iso": "2026-11-12T16:06:31.667807+00:00"}, "tag": "D2_try_gui_resumemission_cancel"}], "resumed": true, "resumed_after_extra_action": false} |

- P1 定义：对话框打开时窗口线程栈含 gamemd+0x207f17 和/或 gamemd+0x20833f。
- P2 定义：对话框打开时 G4 [0xA83D48] == 1。静态依据：唯一置位点 `0x004C7917` 紧跟打印 `"Processing EXIT event on frame %d"`（实参 `[0xA8ED84]`）；`0x0055DE6A` 读 G4，非 0 则跳过帧推进。
- P3 定义：对话框打开时 [0xA8ED84] 帧计数停推。
- P4 定义：关闭对话框（否/取消/No）后帧计数恢复推进（P4 为恢复性对照，不计入 `[已证]` 的 P1∧P2∧P3 合取）。

### D0 / D1 / D2 读数（frame / g1..g4 / mode / A8E9A0 / ABCD58 / exitstate）

| 趟 | frame | g1 | g2 | g3 | **g4** | mode | A8E9A0 | ABCD58 | exitstate |
|---|---|---|---|---|---|---|---|---|---|
| D0 | 840 | 0 | 0 | 0 | **0** | 5 | 1 | 1 | 0 |
| D1a | 850 | 0 | 0 | 0 | **0** | 5 | 1 | 0 | 0 |
| D1b | 850 | 0 | 0 | 0 | **0** | 5 | 1 | 0 | 0 |
| D1c | 850 | 0 | 0 | 0 | **0** | 5 | 1 | 0 | 0 |
| D2 | 909 | 0 | 0 | 0 | **0** | 5 | 1 | 1 | 0 |

## 4. 对话框证据与触发路径

- 触发成功手段：**按控件文字点击 Abort/Exit/放弃类按钮**
- 对话框稳定存在 >3 s：**True**
- 对话框窗口类名/标题/子控件文字：见 `out/triggers.json` 与 `out/D1*.json` 的 `dialog_evidence`（逐趟完整留存）。

```json
{
 "abort_buttons": [],
 "all_controls_with_text": [
  {
   "cls": "Button",
   "ctrl_id": 1670,
   "hwnd": 1706036,
   "parent_hwnd": 5178498,
   "rect": [
    813,
    468,
    896,
    485
   ],
   "text": "GUI:ResumeMission",
   "top_cls": "Yuri's Revenge",
   "top_hwnd": 23268762,
   "top_text": "Yuri's Revenge",
   "top_tid": 9832,
   "visible": true
  },
  {
   "cls": "Static",
   "ctrl_id": 65535,
   "hwnd": 5638104,
   "parent_hwnd": 5178498,
   "rect": [
    287,
    235,
    518,
    256
   ],
   "text": "GUI:AskAbortMission",
   "top_cls": "Yuri's Revenge",
   "top_hwnd": 23268762,
   "top_text": "Yuri's Revenge",
   "top_tid": 9832,
   "visible": true
  },
  {
   "cls": "Button",
   "ctrl_id": 1737,
   "hwnd": 7078168,
   "parent_hwnd": 5178498,
   "rect": [
    813,
    151,
    896,
    168
   ],
   "text": "GUI:Blank",
   "top_cls": "Yuri's Revenge",
   "top_hwnd": 23268762,
   "top_text": "Yuri's Revenge",
   "top_tid": 9832,
   "visible": true
  },
  {
   "cls": "Button",
   "ctrl_id": 1810,
   "hwnd": 22675732,
   "parent_hwnd": 5178498,
   "rect": [
    813,
    168,
    896,
    185
   ],
   "text": "GUI:Blank",
   "top_cls": "Yuri's Revenge",
   "top_hwnd": 23268762,
   "top_text": "Yuri's Revenge",
   "top_tid": 9832,
   "visible": false
  },
  {
   "cls": "Static",
   "ctrl_id": 1685,
   "hwnd": 10291158,
   "parent_hwnd": 5178498,
   "rect": [
    7,
    498,
    310,
    511
   ],
   "text": "GUI:Blank",
   "top_cls": "Yuri's Revenge",
   "top_hwnd": 23268762,
   "top_text": "Yuri's Revenge",
   "top_tid": 9832,
   "visible": true
  }
 ],
 "all_top_windows": [
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
 ],
 "caption_controls": [
  {
   "cls": "Static",
   "ctrl_id": 65535,
   "hwnd": 5638104,
   "parent_hwnd": 5178498,
   "rect": [
    287,
    235,
    518,
    256
   ],
   "text": "GUI:AskAbortMission",
   "top_cls": "Yuri's Revenge",
   "top_hwnd": 23268762,
   "top_text": "Yuri's Revenge",
   "top_tid": 9832,
   "visible": true
  }
 ],
 "dialog_tids": [
  9832
 ],
 "dialog_top_candidates": [],
 "new_child_parent_hwnds": [
  5178498
 ],
 "new_container_groups": [
  {
   "controls": [
    {
     "cls": "Button",
     "ctrl_id": 1670,
     "hwnd": 1706036,
     "parent_hwnd": 5178498,
     "rect": [
      813,
      468,
      896,
      485
     ],
     "text": "GUI:ResumeMission",
     "top_cls": "Yuri's Revenge",
     "top_hwnd": 23268762,
     "top_text": "Yuri's Revenge",
     "top_tid": 9832,
     "visible": true
    },
    {
     "cls": "Static",
     "ctrl_id": 65535,
     "hwnd": 5638104,
     "parent_hwnd": 5178498,
     "rect": [
      287,
      235,
      518,
      256
     ],
     "text": "GUI:AskAbortMission",
     "top_cls": "Yuri's Revenge",
     "top_hwnd": 23268762,
     "top_text": "Yuri's Revenge",
     "top_tid": 9832,
     "visible": true
    },
    {
     "cls": "Button",
     "ctrl_id": 1737,
     "hwnd": 7078168,
     "parent_hwnd": 5178498,
     "rect": [
      813,
      151,
      896,
      168
     ],
     "text": "GUI:Blank",
     "top_cls": "Yuri's Revenge",
     "top_hwnd": 23268762,
     "top_text": "Yuri's Revenge",
     "top_tid": 9832,
     "visible": true
    },
    {
     "cls": "Button",
     "ctrl_id": 1810,
     "hwnd": 22675732,
     "parent_hwnd": 5178498,
     "rect": [
      813,
      168,
      896,
      185
     ],
     "text": "GUI:Blank",
     "top_cls": "Yuri's Revenge",
     "top_hwnd": 23268762,
     "top_text": "Yuri's Revenge",
     "top_tid": 9832,
     "visible": false
    },
    {
     "cls": "Static",
     "ctrl_id": 1685,
     "hwnd": 10291158,
     "parent_hwnd": 5178498,
     "rect": [
      7,
      498,
      310,
      511
     ],
     "text": "GUI:Blank",
     "top_cls": "Yuri's Revenge",
     "top_hwnd": 23268762,
     "top_text": "Yuri's Revenge",
     "top_tid": 9832,
     "visible": true
    }
   ],
   "n_controls": 5,
   "parent_hwnd": 5178498
  }
 ],
 "new_top_windows": [],
 "no_buttons": [],
 "yes_buttons": []
}
```

| 尝试 | 手段 | 对话框出现 | 观察 / 原因 |
|---|---|---|---|
| 1 | Alt+F4（第 1 趟已实测，本趟跳过） | False | 第 1 趟实测：直接退出，无对话框（已归档，非本趟新观察） |
| 2 | 按控件文字点击 Abort/Exit/放弃类按钮 | True | no=0 yes=0 abort=0 captions=1 new_containers=1 new_tops=0 dialog_tops=0 |

## 5. 总档

**[否证]**

- 判档理由：D1 逐帧与基准 7 帧明显不同：4 个关键点命中 0/4，两个 gamemd 关键点（Sleep(30)/EnumChildWindows）在全部可用 D1 栈里均未出现；共享的前 3 帧是主循环 Sleep(30) 通用前缀，按任务卡不算命中。
- 分档口径：`[已证]` = P1∧P2∧P3 全成立；`[部分成立]` = 仅部分成立（下表逐条列出）；`[未证实]` = 未取得可用 D1 抓栈或关键读数缺失；`[否证]` = 可用 D1 栈与基准 7 帧明显不同（两个 gamemd 关键点全部未命中）。
- 逐条判定：P1=不成立 / P2=不成立 / P3=成立 / P4=成立。
- 结论仅对本批 `Proving Grounds` / 该 pid / 该 tid / 该时刻成立，不外推。

