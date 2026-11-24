# GATE_MAP.md — S02B-GATE：从 `0x43F180` 入口到拒绝返回的完整路径图

> 全部地址/分支取自本卡 fresh 反汇编（EVIDENCE/fresh_47C620.txt、fresh_47C3D0.txt、q4_q5_q6_evidence.txt 的 0x43F180 段），capstone 5.0.7 skipdata=True。分支目标逐条核对；「什么都不做」的分支已打到 ret（纪律 2/5）。
> 记法：`A →(cond) B` = A 处条件成立跳 B；`A ──> B` = 顺序/调用。

## 第一段：调用方 `0x43F180`（BuildingClass slot73，mode 1/3 挂链 + 逐格校验）

| 节点 | 做什么 | 分支目标 |
|---|---|---|
| `0x43F180` | `sub esp,0xB0`; push ebx/ebp/esi/edi; `edi=ecx`(this=BuildingClass/ghost); `ebp=[esp+0xBC]`=mode; push ebp | ──> 0x43F198 |
| `0x43F198` | `call 0x6F4A70`（TechnoClass slot73 基类），`test al,al` | `je 0x43F5E0`（基类拒绝则退出） |
| `0x43F1A5` | `[eax+0x1B8]` 取格矩形 → `0x43F1B6 cmp ebp,3 / ja 0x43FAFC` | `jmp [ebp*4+0x43FB0C]` 跳表：mode1/3→`0x43F1E9`，mode0→`0x43F1CA`(摘链 ret)，mode2→`0x43F9A6` |
| `0x43F1E9` | mode 1/3：`eax=[edi+0x520]`(BuildingTypeClass*)；`cmp [eax+0xE58],ebx` | `je 0x43F5EF` |
| `0x43F210` | `call 0x5657A0` GetCellAt（第 1 次，取基准格）；`push eax`; `call [esi+0x1AC]`（can-place 槽） | `jne 0x43F5D8`（不可放则拒绝） |
| `0x43F226`~`0x43F241` | `[BType]` 计算 footprint 宽高/循环上界；`xor ebp,ebp` 计数器归零（注意：此处 ebp 已复用为计数器，mode 判定仅在 0x43F188/0x43F1B6 短路路径上，见 §2） | ──> 0x43F269 逐格循环 |
| `0x43F269`~`0x43F290` | 逐格构造 CellStruct：`[esp+0x4C]`=X、`[esp+0x4E]`=Y（`0x43F276`/`0x43F281`）；`edx=[esp+0x4C]` 写入 `[esp+0x14]`；压栈 arg | ──> 0x43F2A7 |
| `0x43F2A7` | `call 0x5657A0` GetCellAt（第 2 次，把逐格 `{X,Y}` 解析成 `CellClass*`）；`mov ecx,eax` | ──> 0x43F2AE |
| `0x43F2AE` | **`call 0x47C620`**（每格占用闸）；`test al,al` | `je 0x43F504`（=al0，拒绝分支）；al1 继续 `0x43F2BB` |

## 第二段：`0x47C620` 内部（CellClass* this + BuildingTypeClass arg2 → al）

| 节点 | 做什么 | 分支目标 |
|---|---|---|
| `0x47C620` | `mov eax,[0xA8E7AC]`; `sub esp,8`; push ebx/ebp/esi/edi; `xor ebp,ebp`; `edi=ecx`(CellClass*); `cmp eax,ebp` | `jne 0x47CA70`（重入计数非 0 → 直接放行 `al=1`） |
| `0x47C638` | `eax=[esp+0x20]`=arg2(BuildingTypeClass*)；`cmp eax,ebp` | `je 0x47C6A0` |
| `0x47C640` | `cl=[arg2+0x16BF]`; `test cl,cl` | `je 0x47C6DD` |
| `0x47C64E` | `al=[0xA8E9A0]`; `test al,al` | `je 0x47C6A0` |
| `0x47C657`~`0x47C678` | head A `[edi+0xE4]` 链扫 WhatAmI==6（Building）；found 且 esi 非 0 → `0x47C6D1`（`xor al,al` 拒） | 否则 → 0x47C67A |
| `0x47C67A`~`0x47C69E` | `al=[0xA8E9A0]`；head A 扫 WhatAmI==0x24（Terrain）；found → `0x47C6CD`→`0x47C6D1` 拒 | 否则 → 0x47C6A0 |
| `0x47C6A0` | `al=[0xA8ED6B]`; `test al,al` | `je 0x47C878`；非 0 → `0x47C6AD`（`lea eax,[edi+0x24]`; `call 0x568300`; `jne 0x47C88D`） |
| `0x47C6DD`~`0x47C6FF` | arg2 另三标志：`+0x16BE`(0x47C6DD)、`+0x16B7`(0x47C6EB) 任一非 0 → `0x47C7C8`；`+0xE58`(0x47C6F9) 非 0 → `0x47C76B` | 三者全 0 → 0x47C701 |
| `0x47C701` | 写 `[esp+0x10]=[esp+0x14]=0`（准备 `{0,0}`）；`al=[0xA8E9A0]` | `je 0x47C72F`（=0 直接进闸）；=1 → 0x47C712 head A 扫 WhatAmI==2（Aircraft，found→0x47C763→回 0x47C74F） |
| **`0x47C72F`** | 组装闸参：`push ebp(0)` / `lea ecx,[esp+0x14]`(=`&{0,0}`) / `push ebp(0)` / `push ecx` / `mov ecx,edi`(CellClass*) | ──> `0x47C738` |
| **`0x47C738`** | **`call 0x47C3D0`**（bit0 存在性闸，选择子 arg2=0）；`cmp eax,ebp` | `jne 0x47C853`（非空 → 拒绝）；=0 → 0x47C745 |
| `0x47C745` | `push ebp; push 0x24; mov ecx,edi; call 0x47C4D0`（Terrain 第二闸）；`cmp eax,ebp` | `je 0x47C85F`（→ `test [edi+0x124],0x3f`；=0 回 0x47C6A0）；非 0 → `0x47C757 xor al,al` 拒 |
| `0x47C7C8`~`0x47C805` | 第二闸路径（arg2 标志非 0 分支）：同构 `{0,0}` 组装 + **`call 0x47C3D0`@0x47C805** | `jne 0x47C818`（非空 → 0x47C81E 再判 WhatAmI==6 → 0x47C853 拒 / 0x47C836 较 BuildingType） |
| `0x47C853` | `pop edi/esi/ebp; xor al,al; pop ebx; add esp,8; ret 0xc` | **拒绝返回 al=0** → 调用方 `0x43F2B5 je 0x43F504` |
| `0x47CA70` | `pop…; mov al,1; ret 0xc` | 允许返回 al=1（重入/多分支汇合出口） |

## 第三段：`0x47C3D0` 内部（闸核：bit0 存在性）

| 节点 | 做什么 | 分支目标 |
|---|---|---|
| `0x47C3D0` | push ebp; `mov ebp,esp`; `and esp,-8`; `sub esp,0x34`; `edx=[ebp+8]`(&coord); push ebx/esi/edi | ──> 0x47C3DF |
| `0x47C3DF`~`0x47C40D` | `edi=7*[edx]`、`ebx=7*[edx+4]`（距离系数）；`al=[ebp+0xC]`=选择子 | `je 0x47C40F`→`[ecx+0xE4]`(head A)；非 0→`[ecx+0xE8]`(head B) |
| `0x47C415` | `cmp ecx,esi`(NULL) | `je 0x47C4BF`（空链 → `mov eax,esi`=0 返回） |
| `0x47C41D`~`0x47C435` | `esi=ecx`; `test esi,esi`→`je 0x47C4A7`; **`0x47C427 mov al,[esi+0x14] / 0x47C42A and al,1 / 0x47C430 je 0x47C4A7`**（bit0=0 跳过）；`0x47C432 cmp esi,[ebp+0x10]`（排除自身）→ `je 0x47C4A7` | 通过 → 0x47C437 |
| `0x47C437`~`0x47C4A3` | `call [edx+0x48]` 取对象格坐标；`fild/fmul/fadd`/`call 0x4CAC40`/`call 0x7C5F00` 算距离；更近则存 `[esp+0x14]/[esp+0x18]` | ──> 0x47C4A7 |
| **`0x47C4A7`** | `mov esi,[esi+0x30]`（下一对象）；`test esi,esi` | **`0x47C4AC jne 0x47C427`（回边）**；链尾 → 0x47C4B2 |
| `0x47C4B2`~`0x47C4BC` | `mov eax,[esp+0x14]`（最近 bit0=1 对象指针，或 0）; 退栈; `ret 0xc` | 非空 → 上层 `0x47C73F` 拒 |
| `0x47C4BF`~`0x47C4C7` | 空链：`mov eax,esi`(=0); `ret 0xc` | 上层放行至 terrain 闸 |

## 一句话路径
`0x43F180(mode1/3) → GetCellAt → this=CellClass* → 0x47C620 → [0xA8E9A0/标志分支] → 0x47C72F {0,0} → 0x47C738 call 0x47C3D0 → 0x47C427 bit0 测试 → 0x47C4AC 回边 → 非空 → 0x47C73F → 0x47C853 xor al,al ret 0xc → 0x43F2B5 je 0x43F504（拒放）`。
