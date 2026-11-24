# VERDICT.md —— 退出/放弃任务确认对话框 是否就是 S_sleep 的来源

- run_id: `NEXT_RE_20261112_R02`；生成时刻(UTC): `2026-11-12T15:54:11.433261+00:00`
- 基准: `D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112\_hl_match_14412.json`（pid=14412 tid=30668 bits=32 n=7，只读）
- 假设: `S_sleep == 退出/放弃任务确认对话框处理期间的栈`

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

| # | 基准 14412 (addr) | D0 (addr / 相同?) |
| --- | --- | --- |
| 0 | `ntdll.dll+0x7858c` / `0x77c1858c` | `ntdll.dll+0x7858c` / `0x77c1858c` / **相同** |
| 1 | `KERNELBASE.dll+0x16a1f0` / `0x763fa1f0` | `KERNELBASE.dll+0x16a1f0` / `0x763fa1f0` / **相同** |
| 2 | `KERNELBASE.dll+0x16a18f` / `0x763fa18f` | `KERNELBASE.dll+0x16a18f` / `0x763fa18f` / **相同** |
| 3 | `gamemd.exe+0x207f17` / `0x607f17` | `gamemd.exe+0x15e332` / `0x55e332` / **不同** |
| 4 | `USER32.dll+0x74775` / `0x77964775` | — |
| 5 | `USER32.dll+0x3505d` / `0x7792505d` | — |
| 6 | `gamemd.exe+0x20833f` / `0x60833f` | — |

### 关键点命中 / 逐帧一致统计

| 趟 | usable | 帧数 | StackWalk64 终止性质 | 达到 7 帧深度 | 7 帧逐帧一致数 | P1 两关键点命中数 | 4 关键点命中数 |
|---|---|---|---|---|---|---|---|
| D0 | True | 4 | `normal_end_of_walk` | False | 3/7 | 0/2 | 0/4 |

关键点逐项（`命中`=该 module+offset 出现在该趟 StackWalk64 帧序列里）：

| 趟 | `gamemd+0x207f17` | `gamemd+0x20833f` | `user32+0x74775` | `user32+0x3505d` |
| --- | --- | --- | --- | --- |
| D0 | 未命中 | 未命中 | 未命中 | 未命中 |

## 3. 预测量逐条判定

| 预测量 | 判定 | 读数 / 依据 |
|---|---|---|
| **P1** 栈含 `gamemd+0x207f17` 和/或 `gamemd+0x20833f` | **未测** | null |
| **P2** 门控 G4 `[0xA83D48]` == 1 | **未测** | [] |
| **P3** `[0xA8ED84]` 帧计数停推 | **未测** | {"explicit_paired_read": null, "d1_at_grab_frames": [], "d1_frames_all_equal": false, "d0_frame_delta_during_grab": 2} |
| **P4** 关框后帧计数恢复推进 | **未测** | null |

- P1 定义：对话框打开时窗口线程栈含 gamemd+0x207f17 和/或 gamemd+0x20833f。
- P2 定义：对话框打开时 G4 [0xA83D48] == 1。静态依据：唯一置位点 `0x004C7917` 紧跟打印 `"Processing EXIT event on frame %d"`（实参 `[0xA8ED84]`）；`0x0055DE6A` 读 G4，非 0 则跳过帧推进。
- P3 定义：对话框打开时 [0xA8ED84] 帧计数停推。
- P4 定义：关闭对话框（否/取消/No）后帧计数恢复推进（P4 为恢复性对照，不计入 `[已证]` 的 P1∧P2∧P3 合取）。

### D0 / D1 / D2 读数（frame / g1..g4 / mode / A8E9A0 / ABCD58 / exitstate）

| 趟 | frame | g1 | g2 | g3 | **g4** | mode | A8E9A0 | ABCD58 | exitstate |
|---|---|---|---|---|---|---|---|---|---|
| D0 | 964 | 0 | 0 | 0 | **0** | 5 | 1 | 1 | 0 |

## 4. 对话框证据与触发路径

- 触发成功手段：**None**
- 对话框稳定存在 >3 s：**False**
- 对话框窗口类名/标题/子控件文字：见 `out/triggers.json` 与 `out/D1*.json` 的 `dialog_evidence`（逐趟完整留存）。

| 尝试 | 手段 | 对话框出现 | 观察 / 原因 |
|---|---|---|---|
| 1 | Alt+F4 | False | no=0 yes=0 abort=0 new_tops=0 dialog_tops=0 |

## 5. 总档

**[未证实]**

- 判档理由：未取得任何可用的 D1（对话框打开时）抓栈；按红线不伪造 D1，判 [未证实]。触发路径与观察见 RUNLOG/triggers.json。
- 分档口径：`[已证]` = P1∧P2∧P3 全成立；`[部分成立]` = 仅部分成立（下表逐条列出）；`[未证实]` = 未取得可用 D1 抓栈或关键读数缺失；`[否证]` = 可用 D1 栈与基准 7 帧明显不同（两个 gamemd 关键点全部未命中）。
- 逐条判定：P1=未测 / P2=未测 / P3=未测 / P4=未测。
- 结论仅对本批 `Proving Grounds` / 该 pid / 该 tid / 该时刻成立，不外推。

