# ② #10 写者指认 · 判定书（基于 goal2_writer_20261021 中间件收口）

**时间**：2026-10-21 20:0x
**性质**：离线二进制静态分析（零真机、零注入、母本只读）。
**来源**：`goal2_writer_20261021/` 下 w01–w13 的中间产物（#10 子代理产出，
其孤儿扫描进程 pid 3760 已于 19:20 停止，33,219 B 产出已备份为
`scan_0054a56e_orphan_181855.txt`——该件内容为**文档级全文检索**，非新二进制证据）。

---

## 一、结论摘要

| 项 | 判定 |
|:--|:--|
| 崩溃点归属 | `0x0054A56E` 属 **`VectorClass<PAUTileInsertType>` / `DynamicVectorClass<PAUTileInsertType>`** 的析构/清理路径 |
| 容器布局 | `+0x00 vptr` / `+0x04 element ptr` / `+0x08 count` / `+0x0C flag` / `+0x0D owns-buffer` / `+0x10 active` / `+0x14 capacity(=10)`，size ≥ `0x18` |
| 写者身份 | **`0x0054A566` 的 `free([esi+4])` 之后紧接 `0x0054A56E` 的 `mov dword [esi+4],0`** —— 写者就是这条指令本身，不是外部腐化 |
| 崩溃语义 | `esi`（= `this`）本身被腐化成 `.text` 地址 ⇒ `[esi+4]` 落到 `.text` 只读页 ⇒ 写失败 |
| vptr 式 store 是写者吗 | **否**（`w12` `count=0` **且** `w14` 两个 vtable「stored at +4: 0 sites」双重排除）|
| 与 RC-1 同族 | **机制同族**（同一 SBH 分配器簇），**但受害者不同**（RC-1 写 `.data` LUT，本例写 `.text`）|

**一句话**：`[esi+4]` 不是被谁写坏的；**`esi` 自己（this 指针）先坏了**，
所以 `[esi+4]` 落到了它不该去的段。写者是 `0x0054A56E` 这条指令，
但**根因在 `esi` 的来源**，不在这一条 store。

---

## 二、容器定名与布局（RTTI 实证）

### 2.1 RTTI 真值

`w03.out` 从 `.rdata` 的 TypeDescriptor 里读出：

```
00829078 : name@+8 = '.?AV?$DynamicVectorClass@PAUTileInsertType@IsometricTileTypeClass@@@@'
```

`w14_typeconf.py` 另从 vtable 侧独立确认（两个相邻 vtable）：

```
vtable 007ECBDC -> DynamicVectorClass<PAUTileInsertType>
vtable 007ECBFC -> VectorClass<PAUTileInsertType>
```

⇒ **元素类型 = `TileInsertType*`**（`IsometricTileTypeClass` 只是该 TD 的**外部类名**，
不是元素类型）。崩溃点所在函数用的是 **`VectorClass`（基类）** 的 vptr `0x7ECBFC`。

> ★ **勘误**：`w11.out` 的 Q5 段写作 `VectorClass<IsometricTileTypeClass*>`
> （元素类型漏了 `TileInsertType`）。**以 RTTI 真值为准**。
>
> ★ **`0x7ECBFC` 与 `0x7ECBDC` 是父子关系**：`VectorClass<PAUTileInsertType>` 是基类，
> `DynamicVectorClass<PAUTileInsertType>` 派生。静态实例 `@00AA1078` 装的是**基类** vptr
> `0x7ECBFC`，而在 `0x00543EBE` 的条件分支里会切到派生类 `0x7ECBDC`。

### 2.2 布局（**以 `w14` 的全局静态实例实测为准**）

`w14_typeconf.py` 从 `0x00543E70..0x00543EA6`（全局初始化器）读出静态实例的真实布局：

```
[00AA1078] = 007ECBFC  (+0x00 vptr)               ← VectorClass<PAUTileInsertType>
[00AA107C] = 0         (+0x04 element ptr)
[00AA1080] = 0         (+0x08 count)
[00AA1084] = 1 (byte)  (+0x0C flag)
[00AA1085] = 0 (byte)  (+0x0D owns-buffer flag)
[00AA1088] = 0         (+0x10 active / used)
[00AA108C] = 0xA       (+0x14 capacity = 10)
```

| 偏移 | 含义 | 证据 |
|--:|:--|:--|
| `+0x00` | vptr（`0x7ECBFC` = `VectorClass` / `0x7ECBDC` = `DynamicVectorClass`）| dtor `0x0054A7B6` / `0x0054A806` 的 `mov dword [esi], 0x7ecbfc`；全局初始化器 `0x00543E8D` / `0x00543EBE` |
| `+0x04` | **element ptr**（堆缓冲）| 崩溃点；`free` 目标；`w12` 的 store 目标 |
| `+0x08` | count | dtor 里 `mov dword [esi+8], 0` |
| `+0x0C` | 类标志（byte）| ctor `0x0054A506` 的 `mov byte [esi+0xc],0`；全局初始化器 `+0x0C = 1` |
| `+0x0D` | **owns-buffer**（byte）| dtor 里 `mov cl,[esi+0xd]; test cl,cl; je` 守卫 `free` |
| `+0x10` | **active / used** | 全局初始化器 `[00AA1088] = 0` |
| `+0x14` | **capacity**（= 10）| 全局初始化器 `[00AA108C] = 0xA` |
| — | size ≈ `0x18` | 字段跨到 `+0x14` + 4 ⇒ 至少 `0x18` |

> ★★ **两处自我勘误**（`w11.out` 的 Q5 段 vs `w14` 实测）：
> 1. `+0x10` **不是** capacity，是 active/used；**capacity 在 `+0x14`**（= `0xA`）。
> 2. 结构 size 不是 `0x14`，**至少 `0x18`**（因为字段用到 `+0x14..+0x17`）。
>
> `w11.out` 把 `+0x10` 标为 capacity 是从「`0x0054A199` 等处出现 `+0x10`」倒推的，
> 但那些站点可能读的是 active 而非 capacity。**以全局初始化器的静态初值为准。**

### 2.3 两个析构函数（形态完全相同）

`w09.out` 的 `0x0054A7B0` 与 `0x0054A800` 是同一段代码的两份拷贝：

```
0054A7B0  push esi
0054A7B1  mov  esi, ecx
0054A7B3  mov  eax, [esi + 4]          ; element ptr
0054A7B6  mov  dword [esi], 0x7ecbfc   ; vptr ← 类 vtable
0054A7BC  test eax, eax
0054A7BE  je   0x54a7d7                ; 空缓冲 ⇒ 跳过
0054A7C0  mov  cl, [esi + 0xd]         ; owns-buffer
0054A7C3  test cl, cl
0054A7C5  je   0x54a7d7                ; 不拥有 ⇒ 跳过
0054A7C7  push eax
0054A7C8  call 0x7c8b3d                ; ★ free([esi+4])
0054A7CD  add  esp, 4
0054A7D0  mov  dword [esi + 4], 0      ; ★ 置 0（崩溃点的同款指令）
0054A7D7  mov  al, [esp + 8]
0054A7DB  mov  byte [esi + 0xd], 0
0054A7DF  test al, 1
0054A7E1  mov  dword [esi + 8], 0      ; count ← 0
0054A7E8  je   0x54a7f3
0054A7EA  push esi
0054A7EB  call 0x7c8b3d                ; 条件释放对象自身
```

**崩溃点 `0x0054A56E` 与 `0x0054A7D0` 是同一条指令形态**（`mov dword [esi+4],0`），
且前邻都是 `free([esi+4])`（`0x0054A566` ↔ `0x0054A7C8`）。

---

## 三、写者指认：**不是 vptr store，是 `esi` 自身腐化**

### 3.1 vptr 式 store 被排除（**两条独立硬证据**）

**证据 A（`w12.out`，按 vtable 地址范围扫）**：

```
=== do ANY of these stores write a .TEXT (00401000-007E1000) address into +4? ===
  count = 0
```

`w12` 扫的是「`mov dword [reg+4], <007E1000..007EFFFF 的 vtable 地址>`」形态，
按 owner class 分组（`AirstrikeClass` 6 处、`AlphaShapeClass` 6 处……），
**没有任何一处把 `.text` 段地址写进 `+4`**。

**证据 B（`w14_typeconf.py`，按本类两个 vtable 精确查）**：

```
=== is 007ECBFC / 007ECBDC ever stored at +4 anywhere? ===
  007ECBFC stored at +4: 0 sites []
  007ECBDC stored at +4: 0 sites []
```

`0x007ECBFC`（`VectorClass<PAUTileInsertType>`）与 `0x007ECBDC`
（`DynamicVectorClass<PAUTileInsertType>`）**从未被写到任何 `[reg+4]`**。

⇒ **「`[esi+4]` 被 vptr fixup 写坏」这个假设被双重证伪。**

### 3.2 那 `[esi+4]` 为什么落到 `.text`？

因为 **`esi` 本身 = 一个 `.text` 段地址**，而不是一个合法对象地址。

`esi` 在这个函数里来自 `mov esi, ecx`（`0x0054A4FA`，`w05`/`VERIFY_GLM.md:100`）
⇒ `esi = this`。`this` 是 `.text` 地址 ⇒ 只有两种可能：

| 可能 | 机制 | 与本例相容性 |
|:--|:--|:--|
| (a) **函数指针 / 成员函数指针**被当成对象指针传入 | 多继承下的 vptr-fixup 或 `thiscall` 调用错位 | 需调用者侧证据 |
| (b) **栈上返回地址**或对象指针槽被腐化 | 与 §312 另一条「栈返回地址被腐化」同形 | 与 E1c 现场相容 |

**本轮不做 (a)/(b) 二选一**——`w13.out`/`w14_typeconf.py` 正是在查
「多继承 vptr-fixup 机制与所属类布局」，但该线**未产出结论**
（#10 子代理的扫描进程卡死，其最后产物 `w14_typeconf.py` 未运行）。

### 3.3 写者判定（可写下来的部分）

- **直接写者**：`0x0054A56E` 的 `mov dword [esi+4], 0`。
  它写的是「释放后置空」的**正常语义**——在 `esi` 合法时完全正确。
- **根因写者**：**使 `esi` 变成 `.text` 地址的那一次腐化**。
  该次写**不在本函数内**，也不在 `[esi+4]` 的 store 集合里（§3.1 已排除 vptr 式）。
  ⇒ 需要**调用者侧 / 栈帧级**证据才能指认。

---

## 四、与 RC-1 的关系

| 维度 | RC-1 | 本例 `0x0054A56E` |
|:--|:--|:--|
| 分配器 | SBH `0x7C8B3D` / `0x7C93E8` / `0x7CF7BD` | **同一组**（`w05.out` 逐条反汇编证实）|
| 守卫 | `0x7CFC9B`（SBH 守卫）| 同簇 |
| 全局 | `0x00B78B94` / `0x00B78B98` | 同簇（`0x00B78B9C` 出现在 `0x7C9422`）|
| **受害者** | `.data` 的 phase LUT（`0x0084F2BA`）| **`.text`**（`esi` 腐化后的 `[esi+4]`）|
| 是否同一处写 | — | **否**：`goal2_crashaddr_20261020/CRASH_ADDR_ANALYSIS.md:140` 已判 `0x0084F2BA` 的 LUT 无 SBH 写落点 |

⇒ **机制同族（同一堆管理器）、受害者不同（`.data` vs `.text`）**。
SBH 守卫（`EnableSbhGuard`）对两者**都**有覆盖意义，但**不能**据此声称已修 `0x0084F2BA`。

---

## 五、诚实边界（不可越过）

| 项 | 状态 |
|:--|:--|
| 容器定名与布局 | ✅ **定谳**（RTTI + vtable 双向 + 全局初始化器静态初值）|
| `[esi+4]` 的 store 写者 | ✅ **定谳 = `0x0054A56E` 自身**（正常语义）|
| vptr 式 store 是写者 | ✅ **已双重排除**（`w12` `count=0` + `w14` 两 vtable 均 0 sites）|
| `esi` 腐化的**来源** | ❌ **未定谳**：(a) 函数指针错位 vs (b) 栈槽腐化，二者未分 |
| 腐化值是否 = RC-1 的 `0xFE00FFFF` | ❌ **未证**（静态可证机制与分配器，不能证具体毒值）|
| 多继承 vptr-fixup 机制 | ✅ **已排除作为写者**（`w14` 跑完：本类两 vtable 从不写 `+4`）|

**注意**：`w14` 跑完后，「多继承 vptr-fixup」这条线的**结论是负的**——
它不是 `[esi+4]` 的写者。这**缩小**了 (a)/(b) 的候选面：
`esi` 腐化**不是** vptr-fixup 的产物，更可能来自调用者侧的指针/栈槽问题。

---

## 六、下一步（若要闭合 `esi` 来源）

**`w14` 已跑完，把「多继承 vptr-fixup」这条线判为负** ⇒ 剩余候选收窄为：

1. **调用者侧普查**：找所有 `call 0x0054A4F0`（`esi` 来源函数的入口）的站点，
   检查调用前 `ecx` 的装载来源。若某站点用 `.text` 地址（如函数指针 / vtable slot 误取）
   装载 `ecx` ⇒ 判 (a)。
2. **栈槽腐化普查**：检查 `0x0054A4F0` 的调用者是否在同一栈帧内存在越界写
   （尤其 `DynamicVectorClass` 的 `Resize` 路径 `0x0054A535` 附近）。
3. **真机 dump**：按 ② 原计划用 procdump `-e -ma` 抓现场，
   直接读 `esi` 值与栈回溯——这是唯一能**直接**分开 (a)/(b) 的手段，
   也是 ② 判据「dump/指令级证据」的硬要求。

**优先级建议**：先 3（真机 dump，判据硬要求且能一锤定音），
再按 dump 结果决定是否值得做 1/2（静态普查）。

---

## 七、取证件

| 件 | 说明 |
|:--|:--|
| `w01.out` | vtable 扫描（`0x007ECBDC=0x0054A800`、`0x007ECBE0=0x0054A4B0`）|
| `w03.out` | **RTTI 定名** `DynamicVectorClass<TileInsertType*>` |
| `w05.out` | `free` thunk `0x7C8B3D` 与 body `0x7C93E8` 逐条反汇编 |
| `w06.out` | `[0054A000,0054A900)` 内 44 个函数入口候选 |
| `w09.out` | **两个析构函数** `0x0054A7B0` / `0x0054A800` + 原始字节 |
| `w10.out` | `call [reg+disp]` 分布（`+0` 566 / `+4` 260 / `+8` 276 / `+0xc` 204）|
| `w11.out` | Q5 布局推导（**注意 §2.1 / §2.2 两处勘误**）|
| `w12.out` | **vptr 式 store 排除证据 A**（`count=0`）|
| `w13.out` | P2/P3 store 普查（1306 条 `[REG+4]` register-source store）|
| `w14_typeconf.py` + 本轮输出 | **vptr-fixup 排除证据 B**（两 vtable「stored at +4: 0 sites」）+ **全局静态实例布局实测** |
| `scan_0054a56e_orphan_181855.txt` | #10 孤儿扫描产出（文档级检索，非二进制证据）|
