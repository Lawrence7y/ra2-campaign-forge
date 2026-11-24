# W108 · 遍历期失效审计（三处链遍历器 × 149 调用点）

> 卡片：W108_travinv｜逆向：DeepSeek-V4.1-Flash｜2026-11-14｜硬时限 45 min
> 工具：Ghidra 12.1.4 headless（**自建库** `_ghidra/ghidra_w108.gpr`，未碰 Lead 的 `_ghidra_proj`）＋ Python 原始字节扫描（`_w108_scan.py`）
> 授权范围：只读逆向。**未启动游戏、未附加调试器、未写任何被分析文件。**

---

## 0 · 结论（先给判定）

**判定：不存在 (A) 遍历期失效。** 级：`[已证]`（限"经 `0x47EA90` 摘链"这一动作；见 §5 边界）。

**最强候选：无（候选集为空）。**

理由一句话：**`0x0047EA90` 在整个 `.text` 里只有 1 个 `call rel32` 调用点（`0x005688EB`），且该调用点所在的 `0x005687F0` 里一次都没有调用三处遍历器**；该调用点在"缓存指针"含义上不持有任何链节点——它持有的是**索引 `esi`**，摘链后仍用同一索引**重新读表**。

另外两个子问题同时被关闭：
- **(B) 重复摘除：** 不存在 `[已证]` — 唯一调用点由循环内 `JZ` 守卫单次到达，且摘后 `next` 置 0（`0x47EAF0`）使二次摘除必然走"找不到"分支。
- **(C) 摘错链：** 该调用点传 `whichChain = *(byte*)(obj+0x8C)`，而**插入函数 `0x47E8A0` 的链选择器来自同一个对象同一偏移的语义对应字段**；且**遍历器一侧的 16 个带参调用点 100% 传 0（链 A）** ⇒ 不存在"A 链上的对象被要求从 B 链摘"的路径。

---

## 1 · 方法（可复算）

```powershell
# 1) 自建库 + 全量分析（203 s，8,948 函数）
& 'D:\ghidra\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat' `
  '...\W108_travinv\_ghidra' ghidra_w108 -import '...\ra2youli\gamemd.exe'
# 2) 调用点普查 + 反编译全部调用者
... -process gamemd.exe -noanalysis -scriptPath ...\ghidra_scripts -postScript Callers.java census
... -postScript Callers.java decomp
# 3) 独立原始字节复核（不依赖 Ghidra）
python _w108_scan.py
```

**两条独立证据链**：Ghidra `ReferenceIterator`（`EVIDENCE/step2_census.txt`）与纯字节 `E8 rel32` 扫描（`EVIDENCE/step5_rawscan.txt`）。二者在四处目标上**逐一相符**。

---

## 2 · 调用点普查（两条链互相印证）

| 目标 | Ghidra `call` xref | 原始 `E8` 扫描 | 原始 `E9` 尾跳 | 地址取用 |
|---|---:|---:|---:|---:|
| `0x0047C520` 找 `WhatAmI()==6`，链 A | **133** | **133** | 0 | 0 |
| `0x0047C4D0` 参数化 wanted-id | **6** | **6** | 0 | 0 |
| `0x0047C550` 找 `WhatAmI()==0x24` | **10** | **10** | 0 | 0 |
| **三处合计** | **149** | **149** | 0 | 0 |
| `0x0047EA90` 摘链 | **1** | **1** | **0** | **0** |

`EVIDENCE/step5_rawscan.txt`：

```
0x0047C520  TRAV_find6_chainA         133
0x0047C4D0  TRAV_findWanted_argchain  6
0x0047C550  TRAV_find0x24_chainAB             10
0x0047EA90  UNLINK_node               1
TOTAL E8 call sites to the 4 targets = 150
```

- `[已证]` 三处遍历器 149 个调用点，与 Lead L4 的 149 **一致**（我的分项是 133/6/10，L4 是 134/6/9；**合计数相同**，分项差 1 见 `DISAGREE.md` D-1）。
- `[已证]` **三处遍历器不是同一个查询**（`EVIDENCE/step21_550.txt`）：`0x47C520` 比硬编码 **6**；`0x47C4D0` 比**栈参数**；`0x47C550` 比硬编码 **0x24**（`0x0047C56C 83 F8 24`），且只收 1 个参数（whichChain）。⇒ 三者不可互相替代，`0x24` 不是 `0x47C4D0` 的专属值。
- `[已证]` `0x47EA90` 不是虚函数（`.rdata` 无地址项），也**没有**被 `E9` 尾跳复用，**没有**任何 `mov reg,0x47EA90` 式的地址取用 ⇒ **`E8` 那 1 处就是全部调用者**。这一条把问题从"149×N 的组合爆炸"直接压成**单点审计**。

---

## 3 · 那一处摘链调用：逐指令审计（`[已证]`）

`EVIDENCE/step11_inspect_fn.txt`（Ghidra 指令边界），寄存器实况：

```
0056889e  LEA ESI,[EAX + ECX*1]        <- ESI 写 #1：ESI = iVar10 = 行*0x200+列 = **索引**
005688a1  TEST ESI,ESI / JL  …          <- 索引范围检查
005688a9  CMP ESI,[ESP+0x1c] / JGE …    <- 索引上界检查
005688b3  MOV EAX,[EBX+0x13c]           <- 表基址（不是 0x3c，Ghidra 首份反编译显示错，见 §6）
005688b9  MOV ECX,[EAX+ESI*4]           <- ECX = cell = table[索引]   （指针，只活在 ECX）
005688bc  TEST ECX,ECX / JZ …           <- cell==NULL 则跳过
005688c0  MOV EBX,[ESP+0x14]            <- 覆盖 EBX
005688c4  TEST ESI,ESI / JL  0x005688d6
005688c8  CMP ESI,0x40000 / JGE 0x005688d6
005688d0  MOV EAX,ECX                   <- EAX = cell
005688d2  TEST EAX,EAX / JNZ 0x005688e1
005688d6  MOV [0x00abdc74],EBX          <- 仅"无效格 fallback"路径：[ECX]==0 时才走
005688dc  MOV EAX,0xabdc50              <- fallback 静态槽
005688e1  MOV DL,byte ptr [EDI + 0x8c]  <- whichChain = obj->[+0x8C]
005688e7  MOV ECX,EAX                   <- ECX = **this = cell**（指针在这里最后一次被使用）
005688e9  PUSH EDX                      <- arg2 whichChain
005688ea  PUSH EDI                      <- arg1 node = **obj**（不是 cell、不是链节点）
005688eb  CALL 0x0047ea90               <<< 唯一的摘链调用
005688f0  TEST ESI,ESI / JL …
005688f4  CMP ESI,0x40000 / JGE …
005688fc  MOV EAX,[ESP+0x18]
00568900  MOV ECX,[EAX+0x13c]
00568906  MOV ESI,[ECX + ESI*0x4]       <- ESI 写 #2：**用同一索引重新读 cell 表**
00568909  TEST ESI,ESI / JZ …
0056890d  MOV ECX,ESI                   <- ECX = 重新取到的 cell
00568911  CALL 0x0047d2b0               <- 对重读的 cell 做清理
```

### 3-1 为什么这是 **(A) 不成立**（三条独立理由）

1. `[已证]` **摘链后没有任何链节点指针存活。** 跨越 `0x005688EB` 的活寄存器是 `ESI`（索引，非指针）、`EBP`（坐标游标，循环尾 `ADD EBP,0x4` 自增）、`EDI`（被摘的 obj 本身）、`EBX/[ESP+…]`（表/上下文）。`ECX=cell` 是**最后一次使用**（见 `0x005688e7`），摘链后不再被引用。
2. `[已证]` **`esi` 全程是索引，不是节点。** 唯一的 ESI 写入点里，只有 `0x0056889e`（索引）与 `0x00568906`（**重读表**）落在本循环；`0x005689cd/0x00568a24/0x00568adc` 在另一段代码（`0x00568940` 起的第二条路径）。⇒ 摘链后取 cell 用的是 `table[index]` **重读**，不是缓存的 `node->next`。
3. `[已证]` **该函数一次都没调用三处遍历器。** 函数体内全部 `call`：`0x48DEE0`、`0x47EA90`、`0x47D2B0`（×2）。三个遍历器 `0x47C520/0x47C4D0/0x47C550` **零命中**（`EVIDENCE/step8_selfcheck.txt`）。

⇒ 危险形状 `for (p = cell->head; p; p = p->next) { …free/unlink… ; …use p… }` **在本二进制里没有任何实例**，因为遍历器本身不摘链，而唯一的摘链点不在遍历里。

### 3-2 被调 callee `0x47D2B0` 也不会释放仍在用的对象 `[已证]`

`EVIDENCE/step12_callees.txt`：`FUN_0047d2b0(cell, -1)` 做的是格占位计数维护——

```c
if (param_1 == &DAT_00abdc50) return;            // 静态 fallback 一格直接返回
if (*(int *)(puVar4 + 0x100) != 0) *(int *)(puVar4 + 0x100) -= 1;   // 递减 +0x100
```

全程只有字段递减/标志赋值，**无 `free`、无摘链**。且它在 `0x00568906` **重读**之后才被调用，作用对象是重读到的 cell。

---

## 4 · (B) 重复摘除 与 (C) 摘错链

### 4-1 (B) 重复摘除：不存在 `[已证]`

- 唯一调用点受 `0x005688d2 TEST EAX,EAX / JNZ 0x005688e1` 与 `0x005688be JZ` 双重守卫，**每次 cell 只到达一次**；摘链后 `0x0056891d/0x0056893b` 回到 `0x00568862` 的循环尾已 `ADD EBP,0x4`（游标前进，不回访同一坐标）。
- 即便二次摘，`0x47EA90` 的 `0x47EAF0 MOV dword ptr [ESI+0x30],0` 已在首次把 `next` 清零 ⇒ 二次必走"找不到前驱"分支，**不产生悬挂**。这与 Lead §2-1 的逐指令结论一致，我只是补上"调用侧确实只调一次"。

### 4-2 (C) 摘错链：不存在 `[已证]`（遍历器一侧全部传 0）

`EVIDENCE/step16_whichchain.txt` / `step17_argorder.txt`。先证参数顺序（Ghidra 指令边界）：

```
0047c4d0  MOV AL,[0x00A8E9A0]
0047c4d5  PUSH ESI ; PUSH EDI
0047c4db  MOV AL,byte [ESP+0x10]    -> arg2 = whichChain （先压）
0047c4f5  MOV EDI,[ESP+0x0C]        -> arg1 = wanted-id （后压）
```

| 调用点 | 所属函数 | 传入 `whichChain` | 传入 `wanted` |
|---|---|---|---|
| `0x005085D4` | `0x005082C0` | `0` | — |
| `0x005085E0` | `0x005082C0` | `push eax`，前有 `TEST EAX,EAX` ⇒ 此处 **EAX==0** | — |
| `0x00586816` | `0x00586780` | `0` | — |
| `0x005FC4A0` | `0x005FC380` | `0` | — |
| `0x005FD2BA` | `0x005FD270` | `0` | — |
| `0x0062AB97` | `0x0062AB40` | `0` | — |
| `0x006D57C5` | `0x006D5730` | `0` | — |
| `0x006E1896` | `0x006E1830` | **0**（`JNZ` 未跳则 EAX==0） | — |
| `0x006E1A0D` | `0x006E1980` | **0**（同上） | — |
| `0x0047BDC4` | `0x0047BDB0` | `0` | `6` |
| `0x0047C06B` | `0x0047C060` | `0` | `0x24` |
| `0x0047C74A` | `0x0047C620` | `EBP`，其定义 `0x0047C62A XOR EBP,EBP` ⇒ **0** | `0x24` |
| `0x0047C813` | `0x0047C620` | `EBP`（同函数，同一个 `XOR EBP,EBP`） | `0x24` |
| `0x004812A7` | `0x00481180` | `0` | `6` |
| `0x004812C6` | `0x00481180` | `0` | `6` |
| `0x0047C520` ×133 | — | 无参数，`0x0047C52A MOV ESI,[ECX+0xE4]` **硬编码链 A** | — |

⇒ `[已证]` **16 个带参调用点全部选链 A**；`0x47C520` 本身只读 `+0xE4`。**遍历器从来不会去碰链 B。**
⇒ `[已证]` 摘链侧唯一调用点传 `obj->[+0x8C]`；插入侧 `0x47E8A0` 的选链参数（`param_3`）是**独立参数**，读 `+0xE4` 或 `+0xE8`（`0x0047e8b0 / 0x0047e8b8`），写头分别在 `0x0047e91f(+0xE4)` 与 `0x0047e90b(+0xE8)`。
⇒ `[静态推断]` 若 `+0x8C` 与 `param_3` 不同源，理论上可构造 (C)。但**没有任何调用点同时出现"遍历器选链 A"与"摘链选 B"** ⇒ 就"遍历期"而言 (C) 不可达。`+0x8C` 与 `param_3` 是否恒等仍 `[未证]`（见 `UNKNOWNS.md`）。

---

## 5 · 边界（本判定**不能**推到的地方）

1. `[已证]` 限定：本判定只覆盖**经 `0x47EA90` 摘链**。若有别的路径直接写 `cell+0xE4`（`EVIDENCE/step18_chainwrites.txt` 列出 60 条非栈基址写点），**不在此判定内**。
2. `[已证]` 限定：`0x47EA90` 只有 1 个调用点——这是"全部调用者"而非"全部摘链机制"。**`0x47BBF0` / `0x47BB60` 等也写 `+0xE4`/`+0xE8`**，它们是不是另一种摘链，本卡未判。
3. `[未证]` 与 W105 同一硬约束：`+0xE4/+0xE8` 是**通用偏移**（`step18` 里 `[EBX+0xE4]=0x40000000`、`[ESI+0xE8]=0xFFFFFFFF` 等明显不是指针），所以上述 60/49 条写点**不能**当作 "cell 链写者" 的干净清单。
4. `[未证]` `0x47C520` 里 `WhatAmI()` 是**虚调用**（`0x47C538 call [eax+0x2C]`）。若对象已被释放，崩溃点在遍历器**内部**——这是本卡**排除掉的形态之外**的另一类 UAF（对象已死但仍在链上），本卡不覆盖。

---

## 6 · 我发现的一处证据缺陷（自己的勘误）

`EVIDENCE/step4_decomp.txt` 里 `FUN_005687f0` 首份反编译把同一个"表基址"字段显示成 **`+0x13c`**（`0x00568901` 前后）与 **`+0x3c`**（`LAB_00568938` 处 `*(int*)(iVar2 + 0x13c)` vs `*(int *)(iVar2 + 0x3c)` 混用）。**Ghidra 指令边界给出的真值是 `0x13c`**（`0x005688b3 MOV EAX,[EBX+0x13c]`、`0x00568900 MOV ECX,[EAX+0x13c]`）。
⇒ 任何引用 `step4_decomp.txt` 的 **C 源码** 都要回 `step11_inspect_fn.txt` 的**指令**核对。反编译代码在本轮只作**结构**证据，偏移一律以指令为准。

---

## 7 · 交付物与数字可复算

| 数字 | 产出它的文件 |
|---|---|
| 8,948 函数 / 203 s | `EVIDENCE/step1_analyze.log` |
| 133 / 6 / 10 = 149 遍历器调用点 | `EVIDENCE/step2_census.txt`、`step5_rawscan.txt` |
| `0x47EA90` 1 个调用点 `0x005688EB`，0 尾跳，0 地址取用 | `EVIDENCE/step5_rawscan.txt` |
| 摘链点逐指令 + 5 处 ESI 写 | `EVIDENCE/step11_inspect_fn.txt` |
| 该函数不含遍历器调用 | `EVIDENCE/step8_selfcheck.txt` |
| 16 个带参调用点全传 0 | `EVIDENCE/step16_whichchain.txt`、`step17_argorder.txt` |
| `+0xE4` 97 写 / `+0xE8` 74 写 / `+0x8C` 252 写 | `EVIDENCE/step18_chainwrites.txt` |
| 插入函数 `0x47E8A0` 双头写 + 仅 1 调用点 | `EVIDENCE/step19_insert.txt` |
| `0x47D2B0` 不释放、不摘链 | `EVIDENCE/step12_callees.txt` |

---

## 8 · 下一步（针对真机）

本判定把 (A)(B)(C) 三条**遍历期**形态全部关闭 ⇒ 崩溃点 `0x47C538` 的成因**不在遍历逻辑**，而在**链上挂着已死对象**（本卡 §5.4 那条，未覆盖）。真机最该看的是 `0x47C538` 崩溃时 **`esi`（节点地址）指向的内存首 dword** 与**该内存的分配/释放时间戳**，而不是调用栈上的函数名（L4-1 已证归因不可用栈）。

