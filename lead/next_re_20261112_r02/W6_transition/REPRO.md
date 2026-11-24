# REPRO.md —— 过渡态定向复现 S_sleep（第 4 帧判定）

- run_id: `NEXT_RE_20261112_R02`；生成时刻(UTC): `2026-11-12T17:01:13.985018+00:00`
- 判别红线：正常局内前 3 帧与 S_sleep 相同（`ntdll+0x7858c / KERNELBASE+0x16a1f0 / +0x16a18f` 主循环 Sleep(30) 通用前缀）；**只看第 4 帧**：`gamemd+0x207f17` = S_sleep；`gamemd+0x15e332` = 正常态；其它 = 第三签名。
- 触发条件：`frame 连续 ≥1.0s 不推进（真实 t_mono_ns 差）且四门控全 0` ⇒ 抓窗口线程栈。
- 采样间隔：30 ms；UI 全量快照 0.50 s 一次（子窗口数 + 按钮/Static 文字）。

## 1. 总判定

**[已证] S_sleep 复现成功** —— 共 3 次抓栈第 4 帧 = `gamemd+0x207f17`。

## 2. 过渡窗口清单与帧推进曲线摘要

| 窗口(phase) | stop | 时长(s) | 样本数 | frame 首→末 | 净增量 | 1s窗推进率 | 停推≥1s段(全0) | 最长停推(s) | 抓栈 |
|---|---|---|---|---|---|---|---|---|---|
| P0_intro | True | 18.663 | 617 | 0→0 | 0 | 0/587 | 1 | 48.87 | （无） |
| P0_menu_idle | timeout | 12.016 | 391 | 0→0 | 0 | 0/363 | 1 | 48.87 | G01、G02、G03 |
| W_A_load | stable_10.0s | 15.037 | 493 | 0→315 | 315 | 331/465 | 1 | 48.87 | G04、G05 |
| W_A_ingame | timeout | 13.088 | 431 | 315→724 | 409 | 401/401 | 0 | 0.00 | G06 |
| W_B_esc_menu | True | 0.218 | 9 | 730→730 | 0 | — | 1 | 2.14 | （无） |
| W_B_confirm_click | skirmish_screen | 3.01 | 99 | 730→0 | -730 | 0/70 | 2 | 19.15 | G07 |
| idle_after_exit | timeout | 15.019 | 491 | 0→0 | 0 | 0/463 | 1 | 19.15 | G08、G09、G10 |
| W_D_load | stable_10.0s | 13.031 | 427 | 0→314 | 314 | 331/399 | 1 | 19.15 | G11、G12 |
| W_D_ingame | timeout | 11.105 | 365 | 314→661 | 347 | 335/335 | 0 | 0.00 | G13 |

> 1s窗推进率 = 「最近 1.0s 内 frame 增量>0」的窗口占比（≈帧推进健康度）。停推段按真实 `t_mono_ns` 差计算，段内所有样本四门控全 0 才计入「且门控全 0」。

## 3. 「停推 ≥1s 且门控全 0」段明细（全部）

| # | frame(停推值) | 时长(s) | 样本数 | 门控全0 | 跨越 phase |
|---|---|---|---|---|---|
| 1 | 0 | 48.87 | 1170 | True | `P0_intro`,`P0_menu_idle`,`W_A_load` |
| 2 | 730 | 2.14 | 72 | True | `W_B_confirm_click`,`W_B_esc_menu` |
| 3 | 0 | 19.15 | 623 | True | `W_B_confirm_click`,`W_D_load`,`idle_after_exit` |

## 4. 抓栈判定（第 4 帧逐条）

| label | phase | 触发原因 | frames | 第4帧 | 判定 | 0x207f17在原始栈 | 0x20833f在原始栈 | EBP链 | held(ms) |
|---|---|---|---|---|---|---|---|---|---|
| G01 | P0_menu_idle | menu_idle_stall | 6 | `gamemd+0x207f17` | **S_sleep_hit** | True | True | `kernelbase+0x16a1f0→kernelbase+0x16a18f→gamemd+0x207f17` | 6.349 |
| G02 | P0_menu_idle | menu_idle_stall | 4 | `gamemd+0x13eb1c` | **third_signature:gamemd+0x13eb1c** | False | False | `user32+0xc7f51→ddraw+0x22b06→gamemd+0x13eb1c` | 2.086 |
| G03 | P0_menu_idle | menu_idle_stall | 4 | `gamemd+0x13eb1c` | **third_signature:gamemd+0x13eb1c** | False | False | `user32+0xc7f51→ddraw+0x22b06→gamemd+0x13eb1c` | 2.657 |
| G04 | W_A_load | load_transition_stall | 4 | `gamemd+0x207f17` | **S_sleep_hit** | True | False | `kernelbase+0x16a1f0→kernelbase+0x16a18f→gamemd+0x207f17` | 1.881 |
| G05 | W_A_load | load_transition_stall | 12 | `gamemd+0xf4b96` | **third_signature:gamemd+0xf4b96** | False | False | `kernelbase+0x16a1f0→kernelbase+0x16a18f→gamemd+0xf4b96→gamemd+0x29af0f` | 7.700 |
| G06 | W_A_ingame | N0_normal_ingame_contrast | 4 | `gamemd+0x15e332` | **normal_ingame_f3** | False | False | `kernelbase+0x16a1f0→kernelbase+0x16a18f→gamemd+0x15e332` | 1.287 |
| G07 | W_B_confirm_click | confirm_click_stall | 9 | `gamemd+0x70e6` | **third_signature:gamemd+0x70e6** | False | False | `acgenral+0xb1925→gamemd+0x93ce→gamemd+0x70e6→gamemd+0x2be066→gamemd+0x3cd8ef→kernel32+0x15d49→ntdll+0x6c75b→ntdll+0x6c6e1→?` | 5.906 |
| G08 | idle_after_exit | menu_idle_stall | 4 | `gamemd+0x207f17` | **S_sleep_hit** | True | False | `kernelbase+0x16a1f0→kernelbase+0x16a18f→gamemd+0x207f17` | 1.204 |
| G09 | idle_after_exit | menu_idle_stall | 4 | `gamemd+0x13eb1c` | **third_signature:gamemd+0x13eb1c** | False | False | `user32+0xc7f51→ddraw+0x22b06→gamemd+0x13eb1c` | 1.424 |
| G10 | idle_after_exit | menu_idle_stall | 4 | `gamemd+0x13eb1c` | **third_signature:gamemd+0x13eb1c** | False | False | `user32+0xc7f51→ddraw+0x22b06→gamemd+0x13eb1c` | 1.509 |
| G11 | W_D_load | load_transition_stall2 | 8 | `ddraw+0xb61b` | **third_signature:ddraw+0xb61b** | False | False | `ddraw+0x20aba→ddraw+0xb61b→gamemd+0xbafc9` | 2.618 |
| G12 | W_D_load | load_transition_stall2 | 7 | `gamemd+0xf4b96` | **third_signature:gamemd+0xf4b96** | False | False | `kernelbase+0x16a1f0→kernelbase+0x16a18f→gamemd+0xf4b96→gamemd+0x29af0f` | 4.425 |
| G13 | W_D_ingame | N1_normal_ingame_contrast | 4 | `gamemd+0x15e332` | **normal_ingame_f3** | False | False | `kernelbase+0x16a1f0→kernelbase+0x16a18f→gamemd+0x15e332` | 1.153 |

### G01（P0_menu_idle）判定=S_sleep_hit

- 抓栈时刻读数：frame=0 g1=0 g2=0 g3=0 g4=0 mode=0 A8E9A0=1 ABCD58=0 exitstate=0
- 逐帧（**返回地址**，非执行点；frame[0]=被挂起瞬间 EIP）：

  - #0 `ntdll.dll+0x7858c` addr=0x77c1858c —— frame[0]=当前 EIP（非返回地址）：ntdll 等待原语内（Sleep 最终落点）
  - #1 `KERNELBASE.dll+0x16a1f0` addr=0x763fa1f0 —— 返回地址：KERNELBASE Sleep 实现内
  - #2 `KERNELBASE.dll+0x16a18f` addr=0x763fa18f —— 返回地址：KERNELBASE Sleep 包装内
  - #3 `gamemd.exe+0x207f17` addr=0x607f17 —— 返回地址：前一条调用 = push 0x1E + call [0x7E11F0] = Sleep(30)（Lead 已证）
  - #4 `USER32.dll+0x2922e` addr=0x7791922e —— 符号未解析，不作已证事实
  - #5 `USER32.dll+0x3505d` addr=0x7792505d —— 返回地址：USER32 内模态泵

### G02（P0_menu_idle）判定=third_signature:gamemd+0x13eb1c

- 抓栈时刻读数：frame=0 g1=0 g2=0 g3=0 g4=0 mode=0 A8E9A0=1 ABCD58=0 exitstate=0
- 逐帧（**返回地址**，非执行点；frame[0]=被挂起瞬间 EIP）：

  - #0 `win32u.dll+0x11ac` addr=0x766911ac —— 符号未解析，不作已证事实
  - #1 `USER32.dll+0xc7f51` addr=0x779b7f51 —— 符号未解析，不作已证事实
  - #2 `DDRAW.dll+0x22b06` addr=0x54832b06 —— 符号未解析，不作已证事实
  - #3 `gamemd.exe+0x13eb1c` addr=0x53eb1c —— 符号未解析，不作已证事实

### G03（P0_menu_idle）判定=third_signature:gamemd+0x13eb1c

- 抓栈时刻读数：frame=0 g1=0 g2=0 g3=0 g4=0 mode=0 A8E9A0=1 ABCD58=0 exitstate=0
- 逐帧（**返回地址**，非执行点；frame[0]=被挂起瞬间 EIP）：

  - #0 `win32u.dll+0x11ac` addr=0x766911ac —— 符号未解析，不作已证事实
  - #1 `USER32.dll+0xc7f51` addr=0x779b7f51 —— 符号未解析，不作已证事实
  - #2 `DDRAW.dll+0x22b06` addr=0x54832b06 —— 符号未解析，不作已证事实
  - #3 `gamemd.exe+0x13eb1c` addr=0x53eb1c —— 符号未解析，不作已证事实

### G04（W_A_load）判定=S_sleep_hit

- 抓栈时刻读数：frame=0 g1=0 g2=0 g3=0 g4=0 mode=5 A8E9A0=1 ABCD58=0 exitstate=0
- 逐帧（**返回地址**，非执行点；frame[0]=被挂起瞬间 EIP）：

  - #0 `ntdll.dll+0x7858c` addr=0x77c1858c —— frame[0]=当前 EIP（非返回地址）：ntdll 等待原语内（Sleep 最终落点）
  - #1 `KERNELBASE.dll+0x16a1f0` addr=0x763fa1f0 —— 返回地址：KERNELBASE Sleep 实现内
  - #2 `KERNELBASE.dll+0x16a18f` addr=0x763fa18f —— 返回地址：KERNELBASE Sleep 包装内
  - #3 `gamemd.exe+0x207f17` addr=0x607f17 —— 返回地址：前一条调用 = push 0x1E + call [0x7E11F0] = Sleep(30)（Lead 已证）

### G05（W_A_load）判定=third_signature:gamemd+0xf4b96

- 抓栈时刻读数：frame=0 g1=0 g2=0 g3=0 g4=0 mode=5 A8E9A0=1 ABCD58=0 exitstate=0
- 逐帧（**返回地址**，非执行点；frame[0]=被挂起瞬间 EIP）：

  - #0 `ntdll.dll+0x7858c` addr=0x77c1858c —— frame[0]=当前 EIP（非返回地址）：ntdll 等待原语内（Sleep 最终落点）
  - #1 `KERNELBASE.dll+0x16a1f0` addr=0x763fa1f0 —— 返回地址：KERNELBASE Sleep 实现内
  - #2 `KERNELBASE.dll+0x16a18f` addr=0x763fa18f —— 返回地址：KERNELBASE Sleep 包装内
  - #3 `gamemd.exe+0xf4b96` addr=0x4f4b96 —— 符号未解析，不作已证事实
  - #4 `gamemd.exe+0x29af0f` addr=0x69af0f —— 符号未解析，不作已证事实
  - #5 `ntdll.dll+0x95f9e` addr=0x77c35f9e —— 符号未解析，不作已证事实
  - #6 `gamemd.exe+0x3cda69` addr=0x7cda69 —— 符号未解析，不作已证事实
  - #7 `gamemd.exe+0x3c9412` addr=0x7c9412 —— 符号未解析，不作已证事实
  - #8 `gamemd.exe+0x25ca51` addr=0x65ca51 —— 符号未解析，不作已证事实
  - #9 `gamemd.exe+0x28784c` addr=0x68784c —— 符号未解析，不作已证事实
  - #10 `KERNELBASE.dll+0x14e8e0` addr=0x763de8e0 —— 符号未解析，不作已证事实
  - #11 `gamemd.exe+0x2867c3` addr=0x6867c3 —— 符号未解析，不作已证事实

### G06（W_A_ingame）判定=normal_ingame_f3

- 抓栈时刻读数：frame=471 g1=0 g2=0 g3=0 g4=0 mode=5 A8E9A0=1 ABCD58=1 exitstate=0
- 逐帧（**返回地址**，非执行点；frame[0]=被挂起瞬间 EIP）：

  - #0 `ntdll.dll+0x7858c` addr=0x77c1858c —— frame[0]=当前 EIP（非返回地址）：ntdll 等待原语内（Sleep 最终落点）
  - #1 `KERNELBASE.dll+0x16a1f0` addr=0x763fa1f0 —— 返回地址：KERNELBASE Sleep 实现内
  - #2 `KERNELBASE.dll+0x16a18f` addr=0x763fa18f —— 返回地址：KERNELBASE Sleep 包装内
  - #3 `gamemd.exe+0x15e332` addr=0x55e332 —— 返回地址：正常局内主循环 Sleep(30) 的调用点（W3 三趟已定性为正常态第 4 帧）

### G07（W_B_confirm_click）判定=third_signature:gamemd+0x70e6

- 抓栈时刻读数：frame=730 g1=0 g2=0 g3=0 g4=0 mode=5 A8E9A0=1 ABCD58=0 exitstate=0
- 逐帧（**返回地址**，非执行点；frame[0]=被挂起瞬间 EIP）：

  - #0 `ntdll.dll+0x611ee` addr=0x77c011ee —— 符号未解析，不作已证事实
  - #1 `AcGenral.DLL+0xb1925` addr=0x54c91925 —— 符号未解析，不作已证事实
  - #2 `gamemd.exe+0x93ce` addr=0x4093ce —— 符号未解析，不作已证事实
  - #3 `gamemd.exe+0x70e6` addr=0x4070e6 —— 符号未解析，不作已证事实
  - #4 `gamemd.exe+0x2be066` addr=0x6be066 —— 符号未解析，不作已证事实
  - #5 `gamemd.exe+0x3cd8ef` addr=0x7cd8ef —— 符号未解析，不作已证事实
  - #6 `KERNEL32.DLL+0x15d49` addr=0x761a5d49 —— 符号未解析，不作已证事实
  - #7 `ntdll.dll+0x6c75b` addr=0x77c0c75b —— 符号未解析，不作已证事实
  - #8 `ntdll.dll+0x6c6e1` addr=0x77c0c6e1 —— 符号未解析，不作已证事实

### G08（idle_after_exit）判定=S_sleep_hit

- 抓栈时刻读数：frame=0 g1=0 g2=0 g3=0 g4=0 mode=5 A8E9A0=1 ABCD58=0 exitstate=0
- 逐帧（**返回地址**，非执行点；frame[0]=被挂起瞬间 EIP）：

  - #0 `ntdll.dll+0x7858c` addr=0x77c1858c —— frame[0]=当前 EIP（非返回地址）：ntdll 等待原语内（Sleep 最终落点）
  - #1 `KERNELBASE.dll+0x16a1f0` addr=0x763fa1f0 —— 返回地址：KERNELBASE Sleep 实现内
  - #2 `KERNELBASE.dll+0x16a18f` addr=0x763fa18f —— 返回地址：KERNELBASE Sleep 包装内
  - #3 `gamemd.exe+0x207f17` addr=0x607f17 —— 返回地址：前一条调用 = push 0x1E + call [0x7E11F0] = Sleep(30)（Lead 已证）

### G09（idle_after_exit）判定=third_signature:gamemd+0x13eb1c

- 抓栈时刻读数：frame=0 g1=0 g2=0 g3=0 g4=0 mode=5 A8E9A0=1 ABCD58=0 exitstate=0
- 逐帧（**返回地址**，非执行点；frame[0]=被挂起瞬间 EIP）：

  - #0 `win32u.dll+0x11ac` addr=0x766911ac —— 符号未解析，不作已证事实
  - #1 `USER32.dll+0xc7f51` addr=0x779b7f51 —— 符号未解析，不作已证事实
  - #2 `DDRAW.dll+0x22b06` addr=0x54832b06 —— 符号未解析，不作已证事实
  - #3 `gamemd.exe+0x13eb1c` addr=0x53eb1c —— 符号未解析，不作已证事实

### G10（idle_after_exit）判定=third_signature:gamemd+0x13eb1c

- 抓栈时刻读数：frame=0 g1=0 g2=0 g3=0 g4=0 mode=5 A8E9A0=1 ABCD58=0 exitstate=0
- 逐帧（**返回地址**，非执行点；frame[0]=被挂起瞬间 EIP）：

  - #0 `win32u.dll+0x11ac` addr=0x766911ac —— 符号未解析，不作已证事实
  - #1 `USER32.dll+0xc7f51` addr=0x779b7f51 —— 符号未解析，不作已证事实
  - #2 `DDRAW.dll+0x22b06` addr=0x54832b06 —— 符号未解析，不作已证事实
  - #3 `gamemd.exe+0x13eb1c` addr=0x53eb1c —— 符号未解析，不作已证事实

### G11（W_D_load）判定=third_signature:ddraw+0xb61b

- 抓栈时刻读数：frame=0 g1=0 g2=0 g3=0 g4=0 mode=5 A8E9A0=1 ABCD58=0 exitstate=0
- 逐帧（**返回地址**，非执行点；frame[0]=被挂起瞬间 EIP）：

  - #0 `KERNELBASE.dll+0x15aed2` addr=0x763eaed2 —— 符号未解析，不作已证事实
  - #1 `KERNEL32.DLL+0x685b4` addr=0x761f85b4 —— 符号未解析，不作已证事实
  - #2 `DDRAW.dll+0x20aba` addr=0x54830aba —— 符号未解析，不作已证事实
  - #3 `DDRAW.dll+0xb61b` addr=0x5481b61b —— 符号未解析，不作已证事实
  - #4 `gamemd.exe+0xbafc9` addr=0x4bafc9 —— 符号未解析，不作已证事实
  - #5 `gamemd.exe+0x207f0a` addr=0x607f0a —— 符号未解析，不作已证事实
  - #6 `?` addr=0x2fcc304 —— 符号未解析，不作已证事实
  - #7 `gamemd.exe+0x2180e` addr=0x42180e —— 符号未解析，不作已证事实

### G12（W_D_load）判定=third_signature:gamemd+0xf4b96

- 抓栈时刻读数：frame=0 g1=0 g2=0 g3=0 g4=0 mode=5 A8E9A0=1 ABCD58=0 exitstate=0
- 逐帧（**返回地址**，非执行点；frame[0]=被挂起瞬间 EIP）：

  - #0 `ntdll.dll+0x7858c` addr=0x77c1858c —— frame[0]=当前 EIP（非返回地址）：ntdll 等待原语内（Sleep 最终落点）
  - #1 `KERNELBASE.dll+0x16a1f0` addr=0x763fa1f0 —— 返回地址：KERNELBASE Sleep 实现内
  - #2 `KERNELBASE.dll+0x16a18f` addr=0x763fa18f —— 返回地址：KERNELBASE Sleep 包装内
  - #3 `gamemd.exe+0xf4b96` addr=0x4f4b96 —— 符号未解析，不作已证事实
  - #4 `gamemd.exe+0x29af0f` addr=0x69af0f —— 符号未解析，不作已证事实
  - #5 `ntdll.dll+0x61160` addr=0x77c01160 —— 符号未解析，不作已证事实
  - #6 `gamemd.exe+0x93eb` addr=0x4093eb —— 符号未解析，不作已证事实

### G13（W_D_ingame）判定=normal_ingame_f3

- 抓栈时刻读数：frame=471 g1=0 g2=0 g3=0 g4=0 mode=5 A8E9A0=1 ABCD58=1 exitstate=0
- 逐帧（**返回地址**，非执行点；frame[0]=被挂起瞬间 EIP）：

  - #0 `ntdll.dll+0x7858c` addr=0x77c1858c —— frame[0]=当前 EIP（非返回地址）：ntdll 等待原语内（Sleep 最终落点）
  - #1 `KERNELBASE.dll+0x16a1f0` addr=0x763fa1f0 —— 返回地址：KERNELBASE Sleep 实现内
  - #2 `KERNELBASE.dll+0x16a18f` addr=0x763fa18f —— 返回地址：KERNELBASE Sleep 包装内
  - #3 `gamemd.exe+0x15e332` addr=0x55e332 —— 返回地址：正常局内主循环 Sleep(30) 的调用点（W3 三趟已定性为正常态第 4 帧）

## 5. 第三签名清单

- G02（P0_menu_idle）：third_signature:gamemd+0x13eb1c，帧序列 `win32u+0x11ac → user32+0xc7f51 → ddraw+0x22b06 → gamemd+0x13eb1c`
- G03（P0_menu_idle）：third_signature:gamemd+0x13eb1c，帧序列 `win32u+0x11ac → user32+0xc7f51 → ddraw+0x22b06 → gamemd+0x13eb1c`
- G05（W_A_load）：third_signature:gamemd+0xf4b96，帧序列 `ntdll+0x7858c → kernelbase+0x16a1f0 → kernelbase+0x16a18f → gamemd+0xf4b96 → gamemd+0x29af0f → ntdll+0x95f9e → gamemd+0x3cda69 → gamemd+0x3c9412 → gamemd+0x25ca51 → gamemd+0x28784c → kernelbase+0x14e8e0 → gamemd+0x2867c3`
- G07（W_B_confirm_click）：third_signature:gamemd+0x70e6，帧序列 `ntdll+0x611ee → acgenral+0xb1925 → gamemd+0x93ce → gamemd+0x70e6 → gamemd+0x2be066 → gamemd+0x3cd8ef → kernel32+0x15d49 → ntdll+0x6c75b → ntdll+0x6c6e1`
- G09（idle_after_exit）：third_signature:gamemd+0x13eb1c，帧序列 `win32u+0x11ac → user32+0xc7f51 → ddraw+0x22b06 → gamemd+0x13eb1c`
- G10（idle_after_exit）：third_signature:gamemd+0x13eb1c，帧序列 `win32u+0x11ac → user32+0xc7f51 → ddraw+0x22b06 → gamemd+0x13eb1c`
- G11（W_D_load）：third_signature:ddraw+0xb61b，帧序列 `kernelbase+0x15aed2 → kernel32+0x685b4 → ddraw+0x20aba → ddraw+0xb61b → gamemd+0xbafc9 → gamemd+0x207f0a → ? → gamemd+0x2180e`
- G12（W_D_load）：third_signature:gamemd+0xf4b96，帧序列 `ntdll+0x7858c → kernelbase+0x16a1f0 → kernelbase+0x16a18f → gamemd+0xf4b96 → gamemd+0x29af0f → ntdll+0x61160 → gamemd+0x93eb`

## 6. 结论边界

- 判定只对本趟该 pid / 该地图 / 该时刻成立，不外推。
- 「没观测到」≠「不存在」：本趟未复现时，只说明四个过渡窗口在本趟条件下未出现 S_sleep 特征栈，不排除其它过渡路径或更长等待下的出现。
- 栈帧是返回地址；`stackwalk_false:0` 是正常走完不是失败；原始栈/EBP 链仅作外层帧交叉核验，栈残留 ≠ 活跃帧。

