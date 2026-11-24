# S01-K2 · MAINLOOP — 主循环每 tick 完整调用顺序

目标：`ra2youli\gamemd.exe`（ImageBase 0x400000），只读静态反汇编（capstone 5.0.7 skipdata=True）。
证据：`EVIDENCE/mainloop_disasm.txt`、`perframe_55D360_disasm.txt`、`framepred_full_disasm.txt`、
`framedraw_48C8B0_disasm.txt`、`gate_4DA560_disasm.txt`、`loco_4DA820_disasm.txt`、
`timer_iat_sites.txt`、`xref_all.txt`。

## 0. 从 WinMain 到主循环（启动链）

| 环节 | 地址 | 证据/语义 | 分级 |
|---|---|---|---|
| WinMainCRTStartup | `0x7CD80F`（函数约 `0x7CD7E0` 起） | CRT 入口；coverage S01 `[静态推断]` | [静态推断] |
| 游戏入口 (WinMain 等价) | `0x6BB9A0` | SEH 序言 + 数百次 `call 0x4068E0`（memset/init）+ 16 次 `FindWindowA/SetForegroundWindow/ShowWindow`（单实例检查，`cmp eax,0xb7`）；尾部继续初始化 | [静态推断] |
| 主循环容器 | `0x48CCC0`（780 B / `ret@0x48CFCB`） | 先 `call 0x52BA60`（初始化）→ `call 0x52D9A0`（前置）→ 外层/内层帧循环 | [静态推断] |

注：启动链各入口的 subsystem 归属沿用 coverage S01 既有行（`0x7CD80F`/`0x6BB9A0`/`0x48CCC0`），本卡不新增行。

## 1. 一个 tick 的顶层调用有序表（内层帧循环）

内层循环区间：**`[0x48CE8A, 0x48CEA8]`**，回边 `0x48CEA8 → 0x48CE8A`（`je`）。
下表按**执行序**排列（不是按地址盲排；条件跳转的真实走向逐条注明）。

| 序 | 调用点 | 被调函数 | 一句语义 | 每 tick? | 分级 |
|---|---|---|---|---|---|
| 1 | `0x48CE8A` | `0x55D360` MainLoop::PerFrameUpdate | 帧心跳：Sleep 限速 + timeGetTime 计时 + 帧计数 `0xA8ED84` inc（`0x55DE7E`/写回`0x55DE81`）+ House::Update(`0x55E160`) + 消息泵 + 对象 AI/移动 | 是（循环入口，必调） | [已证]（栈边命中 94739） |
| 2 | `0x48CE93` | `0x55CFD0` MainLoop::FramePredicate | 帧谓词/UI 状态翻牌（mode/失焦标志判定）；仅当 #1 返回 `al!=0` 才调 | 条件（`test al,al@0x48CE8F; je 0x48CE9C`） | [已证]（此 site 条件；另一 site `0x48CEA1` 栈命中2） |
| 3 | `0x48CE9C` | `0x48C8B0` Conquer::FrameDraw | 绘制：9 路 jump table（`0x48CC84`）按 `[0xA8EDA0]` 阶段分派 → 层遍历/Blit + 每阶段 `timeGetTime` 采样 | 是（当 #1 返回0 或 #2 返回0；即常态路径） | [已证]（栈边命中3） |
| 4 | `0x48CEA1` | `0x55CFD0` MainLoop::FramePredicate | 帧谓词复判；`test al,al@0x48CEA6`，`je 0x48CE8A` 回边继续下一 tick，`jne 0x48CEAA` 出循环 | 是（无条件调用） | [已证]（栈边命中2） |

**内层控制流精确式**（`mainloop_disasm.txt` 117–126 行）：
```
0x48CE8A  call 0x55D360        ; #1 返回 al
0x48CE8F  test al,al
0x48CE91  je   0x48CE9C        ; al==0 → 跳过 #2，直接 #3
0x48CE93  call 0x55CFD0        ; #2 返回 al
0x48CE98  test al,al
0x48CE9A  jne  0x48CEAA        ; al!=0 → 出循环
0x48CE9C  call 0x48C8B0        ; #3
0x48CEA1  call 0x55CFD0        ; #4 返回 al
0x48CEA6  test al,al
0x48CEA8  je   0x48CE8A        ; al==0 → 下一 tick
```
⇒ 每 tick 的被调用集合：`{0x55D360, 0x48C8B0, 0x55CFD0}`（#4 必调；#2 视 #1 返回值）。
**前序卡"5 个 callee/3 出现 2 未出现"口径已按 VERDICT B 更正：`0x7241A0`/`0x69BAB0` 的 call site 在内层回边之上（外层），应为 3/3 而非 3/5。**

## 2. 外层循环调用（每外层迭代/每帧最多一次，在内层回边之上）

| 调用点 | 被调函数 | 语义 | 分级 |
|---|---|---|---|
| `0x48CDD3` | `0x52D9A0` | 前置初始化；返回0则退出主循环（`test al; je 0x48CFB7`） | [静态推断] |
| `0x48CE35` | `0x6C87F0` | mode==4 分支（会话/回放态）专用 | [静态推断] |
| `0x48CE5D` | `0x7241A0` | 条件 helper（ecx=`[0x887368]`），`[0xA8EB80]` 作参；S01 名 MainLoop::ConditionalHelper | [静态推断] |
| `0x48CE85` | `0x69BAB0` | 帧前 helper（ecx=`0xA8B238`=mode），`[0x822CFC]=1`；S01 名 MainLoop::PreFrameHelper | [静态推断] |
| `0x48CEAA` | `0x72DFB0` | 内层循环退出后的收尾（coverage 归 S07 `[未证]`，弱信号） | [未证] |
| `0x48CEB4` | `0x69BB40` | 退出收尾 helper（ecx=mode；coverage S09 `[未证]`） | [未证] |
| `0x48CEE2` | `0x4068E0` | 统计：除法结果入 `[0x81D514]`（性能/FPS 记录） | [静态推断] |
| `0x48CEEA` | `0x48E0B0` | 退出段调用（coverage S22 `[未证]`） | [未证] |
| `0x48CF02` | `0x4A3C30` | `[0x8175B0]==0` 时弹提示（`edx=0x1e`） | [静态推断] |
| `0x48CF09` | `0x532100` | cl=1 | [静态推断] |
| `0x48CF1C` | `0x473CE0` | `[0xA8D5F8]&3!=0` 时 | [静态推断] |
| `0x48CF3E`/`0x48CF4E`/`0x48CF79` | `0x5DA720`/`0x5F0070`/`0x699450` | 按 mode∈{1,2,3,4,5} 的退出/切换分支（虚调用 `[0x887640]` 也有） | [静态推断] |
| `0x48CFA1` | `[edx+0x10]` 虚调用 | `[0x887640]` 虚表槽，退出时 | [静态推断] |

## 3. N=16 门控的精确分界（§916 更正，逐字节核实）

在被调函数内（`FootClass::AI` 路径，本卡按地址归属不猜类）：

```
0x4DA554  mov eax, [0xA8ED84]          ; frame
0x4DA559  mov ecx, [0x8871E0]
0x4DA560  idiv dword [ecx+0x1808]      ; ÷ N（N=16，局内）
0x4DA566  test edx,edx
0x4DA568  jne 0x4DA63B                 ; 余数≠0 → 跳过整段
; ---- 被跳过区间 [0x4DA56E, 0x4DA63B)：应答/声音/矿石价值块（约40条）----
0x4DA56E  call [edx+0x84] / 0x4DA588 call [eax+0x54] / 0x4DA5A8 call [edx+0x48]
0x4DA5E6  call 0x5657A0(GetCellAt) / 0x4DA5ED call 0x487CB0 / 0x4DA60A call 0x7C5F00(_ftol)
0x4DA629  call [eax+0x16C]
; ---- 门控之后：0x4DA63B 起，每帧都跑 ----
0x4DA63B  cmp byte [esi+0x3D5],bl ...  ; 类型无关占格闸
0x4DA647  call [eax+0x84] / 0x4DA65B call [edx+0x1BC] / 0x4DA667 call 0x578540
0x4DA677  cmp dword [esi+0x674],ebx    ; loco 指针
0x4DA692  call [ecx+0x80]              ; loco vcall（非 locomotion 派发点）
...
```

**独立派发点确认**：`0x4DA877 = call [ecx+0x40]`（`ecx`=`[esi+0x674]`=loco 对象；`loco_4DA820_disasm.txt` 第14行），
位于 `0x4DA63B` **之后**、每帧都跑 —— 与派卡前提 `0x4DA877` 一致 ✓。
⚠️ 本次新见：`0x4DA90E idiv [ecx+0x294]` 是**另一处 per-object 节流除数**（非 N=16 的 `[0x8871E0+0x1808]`），
不得混为同一个 N。

**结论**：`frame % 16` 只跳过 `[0x4DA56E,0x4DA63B)` 那段（应答/声音/矿石价值），
**不**跳过 locomotion 派发（`0x4DA877`）或 `0x4DA63B` 之后的任何代码。§916 三轮更正结论成立。

## 4. 层遍历/渲染三段遍历器（消费 0x8A0394 Count / 0x8A0390 容器）

| 遍历器 | 关键证据 | 结论 |
|---|---|---|
| `0x6D8DB0` | 遍历 `[5]LayerClass` 数组（`0x8A0360`）由上层调用 | [已证]（§4.2 交叉） |
| `0x6D97D0` | `dec eax…jns` 倒序；`call [edx+0x104]` + `mov byte [esi+0x80],0` | [已证]（§4.5） |
| `0x6D9920` | `inc eax; cmp [0x8A03A0]; jl` 正序；同上 | [已证]（§4.5） |
| `0x6D9A50` | `0x6D9A88 mov al,[esi+0x80]` → `test/je 0x6D9B21`（脏标记门控）→ 几何裁剪（4 比较，滚动原点 `0x886FA0`/`0x886FA4`）→ **`0x6D9B15 call 0x6D2790`**（直接调用）→ `0x6D9B1A mov byte [esi+0x80],0` | **[已证]：无 `call [edx+0x104]`**，§4.7 更正正确，无 DISAGREE |

## 5. 帧时钟（IAT + 变量）—— 详见 PROGRESS / UNKNOWNS

- Sleep = IAT `0x7E11F0`（52 处引用），timeGetTime = IAT `0x7E1530`（106 处）。
- 帧计数 `0xA8ED84`（1007 引用/10 写）；时间戳存 `0xA8B55C`（`call [0x7E1530]@0x55D3D4`）。
- 目标帧间隔由 `0x887328..330`/`0x887348..350` 环形计时器 + `0xA8B558` 目标 FPS 决定
  （`0x55D4FB: 60/idiv`、`0x55D51C: 1000/idiv [0xA8B558]`）；
  `0x55E160`（S16 MainLogicFrame::UpdateHouses）内部 `push esi; call [Sleep]` 做剩余时间等待。
- 32 ms 地板 ↔ 1000/32≈31.25 fps，与真机 31.247 fps 一致（差 <0.1%，属 timer 量化）。
