# SENTINEL_RULING.md — CellClass 对象链哨兵判读

> 卡：R09 / **W104**｜2026-11-14｜输入：W100 的 13 份 EVIDENCE（不再重扫镜像）。分级只用
> `[已证]` / `[静态推断]` / `[未证]`。复现命令 `<PY>` = `…\Python312\python.exe`。
> 反汇编引用的字节已由 `cell_sentinel.py --dump` 独立复核（11/11 OK，见 `EVIDENCE/dump.txt`）。

---

## 0 · 结论摘要（先行，便于核对）

| 项 | 判定 | 分级 |
|---|---|---|
| `CellClass` 元素大小 stride | **`0x148` (328)** | `[已证]` |
| 对象分配大小 == stride | `0x148` | `[已证]` |
| 索引 | **行优先 `idx = Y*512 + X`**（行步长 **512**，不是 100） | `[已证]` |
| 是否存在单一静态 `CellClass` 基址 | **不存在**；cell 经 `[0x87F924]` 指针表**两级**访问 | `[已证]` |
| 表项可 NULL | 是（空格子） | `[已证]` |
| 链头 | `+0xE4`（A）/ `+0xE8`（B） | `[已证]` |
| next | `+0x30` | `[已证]` |
| 终止 | `NULL` | `[已证]` |
| WhatAmI 槽 | `+0x2C` | `[已证]` |
| 合法 vtable 白名单 | **280 条**（Set A 16 + Set B 264） | `[已证]` |
| 白名单是否处理"相邻 vtable 合并成游程" | **未处理** ⇒ 会漏起点、哨兵有假阳性 | `[已证]` |

---

## 1 · `CellClass` 的基址（VA）是多少？

### 1-1 结论：**不存在单一静态基址**（这是结论，不是"不知道"）

三层事实，各带证据：

**(a) `0x0087F924` 是一个 DWORD 全局，里面存的是"cell 指针表"的基址 —— 不是表本身。**

```
0x00483B3B: a124f98700       mov  eax, dword ptr [0x87F924]   ; eax = 表基址（运行时值）
0x00483B40: 03f9             add  edi, ecx                    ; edi = Y<<9, ecx = X
0x00483B42: 8b0cb8           mov  ecx, dword ptr [eax + edi*4] ; 表项
```
来源：`W100_cell_sentinel/EVIDENCE/step7_cellptr_table.txt:519-521`。
字节自核：`0x00483B3B: a124f98700`（`--dump` byte self-check）。

**(b) 索引 = `Y*512 + X`，行步长是 2 的幂 512。**

```
0x00429DF5: a124f98700       mov  eax, dword ptr [0x87F924]
0x00429DFA: c1e109           shl  ecx, 9          ; Y * 512
0x00429DFD: 03ca             add  ecx, edx        ; + X
0x00429DFF: 8d0488           lea  eax, [eax + ecx*4]
```
来源：`step7_cellptr_table.txt:497-500`。同形另两处：`step7_cellptr_table.txt:20-21`
(`0x5780B4: c1e109`) 与 `step10_slab_base.txt:69-70` (`0x566542: c1e009`)。
`shl 9` = 512 ⇒ `[已证]` 行步长 512。

**(c) 表项是指针 ⇒ 两级解引用；且表项可为 NULL（空格子）。**

决定性的 `mov ebx,[eax]`（由 Lead 提供并已并入本报告）：
```
0x00429E19: 8b18             mov  ebx, dword ptr [eax]   ; <<< 表项解引用成 CellClass*
0x00429E1F: 85db             test ebx, ebx
0x00429E21: 0f847a030000     je   0x42A1A1              ; <<< 表项 NULL => 跳过（空格子）
0x00429E54: 8b8340010000     mov  eax, dword ptr [ebx+0x140]
```
旁证（同一语义，W100 自采）：
```
0x00483B3B: a124f98700       mov  eax, [0x87F924]
0x00483B42: 8b0cb8           mov  ecx, [eax + edi*4]     ; ecx = CellClass*
0x00483B45: 3bcb             cmp  ecx, ebx               ; ebx = 0 => 空格子比较
0x00483B4D: 8b11             mov  edx, [ecx]             ; 再取 vptr => 又一级
```
来源 `step7_cellptr_table.txt:519-526`；
另一处空槽分支 `step7_cellptr_table.txt:508-515`（`0x5780C9: 8b0c8a` → `test ecx,ecx` → `jne`）。
再一处 `step10_slab_base.txt:74-78`（`0x566556: 8b0482` → `test eax,eax` → `je`，NULL 时跳到静态兜底槽）。

⇒ **哨兵必须两级解引用，且必须先判 NULL。**

**(d) 静态锚点 `0x0089C2E0`：一个静态 cell 对象槽（存指针，不是对象本体）。**
```
0x00429E04: b8e0c28900       mov  eax, 0x89C2E0
0x00429E09: eb0e             jmp  0x429e19           ; 汇合到 mov ebx,[eax]
```
来源 `step7_cellptr_table.txt:502-503`。`[静态推断]`：它是"取不到表项时的兜底 cell"，值需运行时读。

**(e) 另一静态兜底槽 `0x00ABDC50`。** `step10_slab_base.txt:71-78`：
`0x566549: 3d00000400 cmp eax,0x40000` / `jge 0x566561` → `0x566565: be50dcab00 mov esi,0xabdc50`
（`step11_table_use.txt:4-7`，随后 `mov eax,[esi+0x24]`）。`[静态推断]`：静态 `CellClass` 兜底实例。

### 1-2 表容量推算（`[静态推断]`）
`512*512*4 = 1,048,576 B = 1 MB`。依据：`shl 9`（坐标→行步长 512）与 `0x566549` 的
上界比较 `cmp eax, 0x40000`（= 262,144 = 512*512）。**这是推断**，未在活进程核对实际分配长度。
反证一条：`0x005780BB: 3b0d28f98700 cmp ecx,[0x87F928]`（`step7_cellptr_table.txt:23`）
说明上界存在**变量** `[0x87F928]`，其 `.data` 初值 = `0x00200064`（`step8_elemtype.txt:57`）。
⇒ 上界不是硬编码常数，**"1 MB" 只是上界形状，不是实测容量**。

### 1-3 改用哪条锚点（施工口径）
1. 读全局 `[0x0087F924]` 得表基址 → 逐项判 NULL → 非 NULL 项得 `CellClass*` → 扫 `+0xE4`/`+0xE8`。
2. 交叉验证：`[0x0089C2E0]` 与 `[0x00ABDC50]` 各当对象扫一次。
3. **不要**去找"静态 `CellClass` 数组"——不存在。

`[未证]`：`[0x87F928]` 的语义（表长？行数？）与初值 `0x200064` 的关系。**不影响哨兵**（按 NULL 判空）。

---

## 2 · 元素大小（stride）与行列优先

### 2-1 stride = `0x148` = 328 `[已证]`

| 证据 | VA: bytes | file:line |
|---|---|---|
| 分配对象 | `0x005663C3: 6848010000  push 0x148` | `step11_table_use.txt:271` |
| 同上（后续 `call 0x7c8e17` = 分配器） | `0x005663C8: e84a2a2600` | `step11_table_use.txt:272` |
| slab 遍历步长 | `0x00566AA6: 81c548010000  add ebp, 0x148` | `step9_alloc_fill.txt:95` |
| 第二处 slab 遍历 | `0x0056629A: 81c548010000  add ebp, 0x148` | `step11_table_use.txt:194` |

**勘误（Lead 指出，已采纳）**：我上一版引的 `step9_alloc_fill.txt:455` 是错的 —
该行是 `--- mov [reg+0x13C], r32 sites (89 mod10) ---` 的小节标题，不含 `push 0x148`。
真实的 `push 0x148` 在 `step11_table_use.txt:271`。
`step9_alloc_fill.txt:4-95` 的窗口里确实含 `add ebp,0x148`（第 95 行），但不含 `push 0x148`。

配套（对象创建链）：
```
0x005663C3: 6848010000       push 0x148
0x005663C8: e84a2a2600       call 0x7c8e17          ; alloc
0x005663D4: 8bc8             mov  ecx, eax
0x005663D6: e81558f1ff       call 0x47bbf0          ; CellClass ctor
0x005663ED: 8b8b3c010000     mov  ecx, [ebx+0x13c]  ; 表基址
0x005663F3: 892cb9           mov  [ecx+edi*4], ebp  ; 写回表项（指针）
```
来源 `step11_table_use.txt:271-286`。⇒ `[已证]`：表项写回的是**指针**（`ebp` = ctor 返回值），
再次坐实两级语义。

`[静态推断]`：`0x47BBF0`（ctor）`call 0x410170`（`step12_whitelist.txt:7`）应是基类 ctor ⇒
`CellClass` 有基类，`+0xE4`/`+0xE8` 属该布局。`[未证]`：基类名与 `+0xE4` 前的字段归属。

### 2-2 行/列优先：**行优先**（`row*W+col`）`[已证]`
- `step7_cellptr_table.txt:498-499`：`shl ecx,9`（Y）后 `add ecx,edx`（X）。
- `step7_cellptr_table.txt:517-520`：`movsx edi,[esi+0x26]`（+0x26=Y）、`movsx ecx,[esi+0x24]`
  （+0x24=X）、`shl edi,9`、`add edi,ecx` ⇒ **低半字 X，高半字 Y**。
- 反算：`X = idx & 0x1FF`，`Y = idx >> 9`。
`[静态推断]`：`0x00578080` 把 16.8 定点坐标 `sar 8` 归约后按同式取表（`step7:9-26`）。

---

## 3 · 两条链头 `+0xE4` / `+0xE8` 的语义与 next 偏移

与 Lead 的 L1 逐字节一致，我复核结论如下（`[已证]`，限这三个同族函数）：

| 项 | 值 | 证据 |
|---|---|---|
| 链 A 头 | `+0xE4` | `0x0047C52A: 8bb1e4000000 mov esi,[ecx+0xE4]`（`step1_disasm.txt:51`） |
| 链 B 头 | `+0xE8` | `0x0047C4E3: 8bb1e8000000 mov esi,[ecx+0xE8]`（`step1_disasm.txt:18`） |
| 选择器 | `0x47C4D0`/`0x47C550` 按第 2 参数选 A/B | `step1_disasm.txt:15-20,73-78` |
| next | `+0x30` | `0x0047C540: 8b7630 mov esi,[esi+0x30]`（`step1_disasm.txt:59`） |
| WhatAmI | `+0x2C` | `0x0047C538: ff502c call [eax+0x2C]`（`step1_disasm.txt:56`） |
| 终止 | `NULL`（`test esi,esi / jne`） | `step1_disasm.txt:60-61` |
| `0x47C520` 走哪条 | **只走链 A**（硬比较 `WhatAmI()==6`） | `step1_disasm.txt:51,57` |

**独立旁证（W100 自采，与 Lead 无关）：**
- `0x0051C237: 8bb1e8000000` / `0x0051C243: 8bb2e4000000`（`step3_base_hunt.txt:37,40`）
  ——`IsCellOccupied` 内同一对选择分支。
- `0x0051C70F: 8b7630 mov esi,[esi+0x30]`（`step2_stride_hunt.txt:5`）——`+0x30` next。
- `0x00484F6D: 8b4030 mov eax,[eax+0x30]`（`step2_stride_hunt.txt:41`），且该函数自带
  **10 节点上限**（`0x00484F66: 83f90a / jge`，`step2_stride_hunt.txt:38-39`）
  ⇒ `[已证]` **引擎自己就假设链可能过长/成环**，与哨兵必带节点上限一致。

`[未证]`：链 A 与链 B 的**语义区分**（"占用者链"vs"建筑链"之类）。现有证据只能给出"两套按参数
选择的对象列表"，无一条证明哪条装什么。`[未证]`：节点 `+0x30` 以外字段的类型。

---

## 4 · 合法 vtable 白名单

### 4-1 规模：**280 条** `[已证]`
- 机器可读清单 `EVIDENCE/vtable_whitelist.txt`：`0x` 开头的数据行 = **280**
  （命令：`Select-String -Path vtable_whitelist.txt -Pattern "^0x" | Measure-Object` → `Count=280`；
  SHA-256 = `FC0A0F3CBAAD416C96EC8928E7D52BA9121E80B0AE5BA381B4615131CE987889`）
- 组成：Set A（slot11 = WhatAmI thunk 锚）= **16**，Set B（结构游程起点）= **264**，
  并集 **280**（`step12_whitelist.txt:24,29,36`）。
- 两个锚点均在白名单内（`step12_whitelist.txt:38`）：`0x7EB058`（N=15）、`0x7E3EBC`（N=6）。

### 4-2 判据（`work/step12_whitelist.py` 实际行为，`[已证]`）
- Set A：遍历 `.rdata` 每条可执行指针游程的**每一个 word** 当候选起点，要求 `+0x2C` 是
  `B8 imm32 C3` thunk 且 `N<=0x80`。
- Set B：游程**长度 >= 8** 且**前一 word 不是可执行指针** ⇒ 结构起点。
- `step13_anchor_debug.py` 另做 pure=**119** / strict=**108** 两档（`step13_anchor_debug.txt:41,46`），
  但**未并入交付的白名单**。

### 4-3 已知限制：**未处理"相邻 vtable 被合并成一条游程"** `[已证]`

> 游程 = **最大连续可执行指针段**。相邻两个 vtable 之间没有非指针 word 分隔时会被**合并**，
> 此时该游程的 slot11 只反映**第一个** vtable 的 WhatAmI。
> （`LEAD_FINDINGS_R09.md` L2-2，第 124-126 行）

⇒ **直接后果（必须写在任何引用这张表的结论里）：**
1. **白名单会漏起点。** 被合并的第二个及以后 vtable 的起点不在 Set B / Set A 里。
   实测旁证：`step12_whitelist.txt:26` 报 `N missing in 1..73` 缺 **61 个值**；
   `step13_anchor_debug.txt:43` 的 pure 扫法只缺 `[31, 58]` 两个 ⇒ 档位不同漏得也不同，
   **没有任何一档是完备的**。
2. ⇒ **哨兵若用这张表当"合法 vptr"判据，会把合法 vptr 判成非法（假阳性）。**
3. ⇒ **`--self-test` 全绿 ≠ 真机不误报。** selftest 用的是自造假 vtable，
   与这张表的完备性无关。

### 4-4 前 16 条明显不是 vtable 的项（`[静态推断]`）
`vtable_whitelist.txt:2-17` 前 16 条是 `.text` 里的**代码地址**（`0x00410260`…，带 Set A 的 N 值）——
因为 Set A 遍历"游程里的每个 word"，而 `.rdata` 含指向 `.text` 的函数指针数组。
⇒ 白名单**不能**当"起点集合"精确用于"非法 vptr"判定，只能当"疑似合法"的一票。

---

## 5 · W100 哪一步的结论可疑或自相矛盾（逐条）

1. **`step2_stride_hunt.py` 的 imul 直方图靠不住（`[已证]`）。** 脚本在 `mod != 3` 时仍把
   `text[i+2]` 当 imm32（`work/step2_stride_hunt.py` 的 `if True else 0`），内存形式 `69 /r` 的
   imm32 在 disp 之后 ⇒ 位置算错。证据：`step2_stride_hunt.txt:64-78` 与 `step3_base_hunt.txt:68-98`
   对**同一镜像**报不同计数（`0x74`: 18 vs 29）。⇒ **stride 不能靠 imul 直方图立论**，真证据是
   `push 0x148` / `add ebp,0x148`（§2-1）。**W100 的 stride 结论对，但方法错，属"结论侥幸正确"。**

2. **`step3_base_hunt.py` 的 `imul eax,[0x0089C2DC]` 计数是假信号。**
   `step3_base_hunt.txt:100-260` 报 140 次同址 —— 绝大多数是 `0F AF 05` 在**非指令边界**的偶然命中
   （该文件 `:1-2` 自己就打印了一条从指令中间解码的垃圾）。且 `0x0089C2DC` ≠ 真表指针 `0x0087F924`。
   ⇒ 该文件不能用来定位 stride 或基址。

3. **`step7_cellptr_table.txt:292-459`（`.text refs to 0x0087F924: 399`）不可用。**
   它是"在字节流里搜 4 字节常量"，非按指令边界解码；窗口含大量非指令起点产物（`:490`）。
   与 `LEAD_FINDINGS_R09.md` L3/L5 同类失败**同源**。⇒ **399 不采信。**
   可用的是文件里手工挑出的 6 个窗口（`:461-537` 等）。

4. **`step8_elemtype.txt:56` 把 `.data` 初值当"表指针"印出，误导。**
   对一个运行期填充的全局打印初值 `0x006E0061`（ASCII "an"）意义有限；
   `[已证]` 仅"初值是这个数"，`[未证]` 其语义。拿它当表基址会得出荒谬结论。

5. **`step12` 与 `step13` 两档口径不一致且未合并（`[已证]`）。**
   `step12` 交付 280 条；`step13` 的 pure 扫法 119 条、strict 108 条，**两组互不包含性未分析**，
   也**未说明为何交付 280 而不是 108**。⇒ 白名单的"权威档位"未定义，是被追问的直接原因。

6. **`step9` 与 `step11` 大段重复（`[已证]`）**：`step9_alloc_fill.txt:4-77` 与
   `step11_table_use.txt:88-173` 是同一段 `0x565D..` 转储 ⇒ 引用时**只能算一条证据**。
7. **`step13_anchor_debug.txt:19,39` 的 `prev word exec?` 只对两个锚点打印**，Set B 的
   264 条无同等核验 ⇒ `[未证]`：这 264 条的 `prev` 是否真都非可执行。

---

## 6 · 对哨兵的净影响（施工口径）

1. **两级解引用 + 先判 NULL**（§1-1c）——写代码时唯一容易搞错的地方。
2. **两锚点**：`[0x0087F924]` 表 + `[0x0089C2E0]` / `[0x00ABDC50]` 静态槽（§1-3）。
3. **两条链都扫**，每条带节点上限与已访问集合（引擎自己也有 10 节点上限，§3）。
4. **白名单只能当"疑似合法"**，不得当判决依据（§4-3）。
5. **不要计算 `base + stride*i`**：没有静态基址（§1-1）。

## 附：本次交付的复核物
- `--dump`：PE 节表 + 11 条关键字节自核 + 两个 vtable 锚槽 → `EVIDENCE/dump.txt`。
- `--self-test`：4 套独立对象图、**14 项断言全 PASS** → `EVIDENCE/selftest.txt`（`RESULT: GREEN`）。
