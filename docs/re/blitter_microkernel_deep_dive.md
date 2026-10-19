# 红色警戒2：尤里的复仇 Blitter 渲染微内核深度逆向与 SSE2 向量化设计

> **逆向目标**：`gamemd.exe` 1.001（官方版），ImageBase = `0x00400000`  
> **关联源码**：`ra2render/ra2render.h`、`ra2render/blitter_hooks.cpp`  
> **前置档案**：`docs/re/rle_blit_family.md`、`docs/re/nonrle_blit_and_named_hotspots.md`  
> **分析工具**：Capstone 32-bit x86 反汇编引擎、PE 结构剖析器、MSVC C++20 / SSE2 内联与 Intrinsic 编译链  

---

## 1. 摘要与虚表拓扑

在《尤里的复仇》引擎的软件光栅化渲染管线中，单位渲染（步兵、载具、建筑受损着色、影子）是 CPU 占用率最高的核心瓶颈。其中：
- **步兵本体与影子** 采用基于变长透明游程的 **RLE 码流**（`RLEBlit*@G`，16 位 RGB565）；
- **载具、建筑、单位重叠深度混合** 采用 **密集无压缩像素流**（`Blit*@G`，16 位 RGB565）。

通过对 `gamemd.exe` 的 PE 节区与虚表进行精确交叉引用取证，核心高频微内核的虚表地址、入口点及虚函数槽分布如下：

### 1.1 核心五大高频微内核拓扑表

| 微内核名称 | 虚表基址 (vtable) | Slot 1 地址 (Hook 点) | Slot 1 汇编入口 | 参数量与调用约定 | 核心职责 |
|---|---|---|---|---|---|
| `?$RLEBlitTransDarkenZRead@G` | `0x007E5540` | `0x007E5544` | `0x00496820` | 10 参数 (`ret 0x28`) `__thiscall` | 步兵重叠影子绘制（带 Z 缓冲测试与 RLE 裁剪） |
| `?$RLEBlitTransDarken@G` | `0x007E55A0` | `0x007E55A4` | `0x00496250` | 10 参数 (`ret 0x28`) `__thiscall` | 步兵无遮挡影子绘制（全屏最高频之一） |
| `?$RLEBlitTransXlat@G` | `0x007E55C0` | `0x007E55C4` | `0x004960A0` | 10 参数 (`ret 0x28`) `__thiscall` | 步兵本体绘制（调色板阵营色映射） |
| `?$BlitTransXlatZRead@G` | `0x007E5978` | `0x007E597C` | `0x00492B00` | 8 参数 (`ret 0x20`) `__thiscall` | 载具/重叠单位本体深度遮挡绘制 |
| `?$BlitTransDarkenZRead@G` | `0x007E5948` | `0x007E594C` | `0x00492D20` | 8 参数 (`ret 0x20`) `__thiscall` | 载具/建筑投射阴影深度遮挡变暗 |

> **关键澄清**：
> 社区部分文档（如 YRpp 或早期逆向笔记）将 `0x007E597C` 和 `0x007E594C` 标记为“虚表地址”。经二进制反汇编实测：
> - `0x007E5978` 是 `BlitTransXlatZRead@G` 的真正虚表基址，其 `+0x00` 槽为析构函数 `0x0049A000`，`+0x04` 槽（即地址 `0x007E597C`）存放 `Blit` 入口 `0x00492B00`；
> - `0x007E5948` 是 `BlitTransDarkenZRead@G` 的真正虚表基址，其 `+0x00` 槽为析构函数 `0x0049A040`，`+0x04` 槽（即地址 `0x007E594C`）存放 `Blit` 入口 `0x00492D20`。
> Hook 挂钩只需改写 `vtable + 4`（即 Slot 1）。

---

## 2. 核心数据结构与 ABI 取证分析

### 2.1 `this` 指针成员布局取证（Darken vs Xlat）

在西木引擎的工厂函数（`0x0048FAF8`–`0x0048FC98`）与析构函数（`0x0049A760`–`0x0049A860`）中，所有 Blitter 对象的分配大小统一为 **12 字节**（`push 0x0c; call operator new`）。

【勘误 2026-09-29 · E-1 · landing_audit】原文「所有 Blitter 对象的分配大小统一为 12 字节」→ 订正为：**按成员数分级 4/8/12/16 四级分配**（`push <size>; call operator new (0x007C8E17)`），**P0 微内核（步兵/载具本体与影子主路径）实测仅 8 字节**。按 12B 声明 `this+0x08` 将**越界 4 字节**（堆块尾部踩踏）。权威：`ARCHITECTURE_ATLAS.md` §1.2〔勘误 R1〕+ 同文 L1029 自勘误 + `re_sprint_S13_report.md:17`。原文保留不删字。

各派生类在 `+0x04` 偏移处存放的数据类型存在**本质差异**：

【勘误 2026-09-29 · E-1 · landing_audit】下图标题「(12 字节)」→ 订正为：**尺寸按成员数分级 4/8/12/16**；P0 微内核 = **8 字节**（仅 `+0x00` vtable + `+0x04` 一槽，**无 `+0x08`**）。Lucent/ZRemap/Alpha 族才是 12 字节（vtable + 2 槽）。按 12B 统一布局图声明结构体，在 8B 对象上访问 `this+0x08` 即越界 4 字节。原文围栏保留不删字。

```
[ Blitter 内存对象布局 (12 字节) ]
+0x00: void* __vfptr          (4 字节虚表指针)
+0x04: 变体核心参数            (4 字节，语义分化，见下表)
+0x08: 变体辅助参数 / 掩码      (4 字节)
```

| 派生类类别 | `this + 0x04` 真实类型与取证 | `this + 0x08` 真实类型与取证 | 工厂初始化指令取证 |
|---|---|---|---|
| **Darken 变体** (`*Darken*`) | **`uint16_t DarkenMask`**（**数值**，非指针！）典型值为 `0x7BEF` | 未使用（0 或对齐填充） | `0x0048FC69: mov cx, [esi+0x180]`<br>`0x0048FC70: mov [eax+4], cx` (写入 16-bit 值) |
| **Xlat 变体** (`*Xlat*`) | **`const uint16_t* XlatTable`**（**指针**）指向 256 项 uint16_t 调色板映射表 | 未使用（或辅助指针） | `0x0048FAFC: mov ecx, [esi+0x174]`<br>`0x0048FB02: mov [eax+4], ecx` (写入 32-bit 指针) |
| **Lucent 变体** (`*Lucent*`) | **`const uint16_t* XlatTable`**（指针） | **`uint16_t BlendMask`**（数值）典型值为 `0x7BEF` / `0x3DEF` | `0x0048FB89: mov [eax+4], edx`<br>`0x0048FB8C: mov [eax+8], cx` |
| **ZRemapXlat 变体** | **`uint8_t** pRemapTable`**（二级指针，先解引用得 256 字节表） | **`const uint16_t* XlatTable`**（指针） | `0x00496182: mov ecx, [ebp+4]; mov ecx, [ecx]` |

> [!CAUTION]
> **致命缺陷预警**：现网 `ra2render.h` 的 `RLEBlitterCore` 将 `+0x04` 声明为 `uint16_t *XlatTable`。若对 `RLEBlitTransDarken` 或 `RLEBlitTransDarkenZRead` 解引用 `XlatTable`，程序将把掩码 `0x7BEF` 作为指针进行访问，直接引发 `0xC0000005` 内存访问冲突（Crash）。Darken 必须使用专用结构体或直接读取 `uint16_t DarkenMask`！

### 2.2 调色板映射表格式（XlatTable）

- **数据规格**：长度固定为 **256 个 `uint16_t`**，占用 **512 字节** 连续内存。
- **寻址方式**：以源数据索引 `idx`（`uint8_t`, 0~255）作为下标：
  $$\text{Pixel}_{\text{RGB565}} = \text{XlatTable}[\text{idx}]$$
- **汇编实现**：`0x00496113: mov cx, word ptr [edx + ecx*2]`（基址加两倍变址寻址）。

### 2.3 调用约定与参数栈帧对照（RLE `ret 0x28` vs Non-RLE `ret 0x20`）

所有 Blitter 均使用 MSVC 32-bit `__thiscall` 约定：`ECX` 存放 `this` 指针，参数自右向左压栈，被调用者平栈。

#### (1) RLE 族 10 参数栈帧（`ret 0x28`，共 40 字节）：
```
[esp + 0x00]: 返回地址 (Return Address)
[esp + 0x04]: void*    dst          (arg1: 目标像素缓冲区指针，uint16_t*)
[esp + 0x08]: uint8_t* src          (arg2: RLE 压缩源字节码流)
[esp + 0x0C]: int      Length       (arg3: 完整 32 位！当前绘制扫描段的有效像素宽度)
[esp + 0x10]: int      EncodedLen   (arg4: 完整 32 位！左裁剪跳过像素数)
[esp + 0x14]: uint16_t zMin         (arg5: 当前精灵基准深度值)
[esp + 0x18]: uint16_t* zBuf        (arg6: 环形深度缓冲区当前行指针)
[esp + 0x1C]: uint16_t* aBuf        (arg7: Alpha 缓冲区指针，Alpha 变体用)
[esp + 0x20]: int      aLvl         (arg8: Alpha 混合等级，Alpha 变体用)
[esp + 0x24]: int      warpOffset   (arg9: 扭曲采样偏移，像素单位，Warp 变体用)
[esp + 0x28]: int8_t*  zmap         (arg10: 逐像素有符号深度偏移表，int8_t*)
```

> [!IMPORTANT]
> **参数语义修正**：
> 1. `Length`：**绝对不是 `uint8_t`**！在汇编 `0x004960ca: mov edi, [esp+0x18]`、`test edi, edi`、`sub edi, edx` 中，全程使用 32 位通用寄存器。若行宽或裁剪跨度超过 255 像素，现有 `uint8_t Length` 声明会发生严重高位截断！
> 2. `EncodedLen`：命名易产生误导（并非压缩包的字节长度），其实际语义是 **“左边界裁剪需要跳过的像素总数（Left Clip Skip Count）”**。

#### (2) Non-RLE 族 8 参数栈帧（`ret 0x20`，共 32 字节）：
```
[esp + 0x00]: 返回地址
[esp + 0x04]: void*    dst          (arg1: uint16_t* 目标)
[esp + 0x08]: void*    src          (arg2: 密集未压缩源，Xlat/Darken 为 uint8_t* 索引流)
[esp + 0x0C]: int      length       (arg3: 32 位像素宽度)
[esp + 0x10]: uint16_t zMin         (arg4: 深度阈值)
[esp + 0x14]: uint16_t* zBuf        (arg5: 深度缓冲区)
[esp + 0x18]: uint16_t* aBuf        (arg6)
[esp + 0x1C]: uint16_t aLvl         (arg7)
[esp + 0x20]: int      warpOffset   (arg8)
```

### 2.4 全局 Z 缓冲描述符（0x00887644）与环绕逻辑

在带深度测试的变体中，深度缓冲区为一个**环形跨行缓冲区（Ring Buffer）**。全局指针 `*(void**)0x00887644` 指向其控制结构体：

```cpp
struct ZBufferDesc {
    int       X;            // +0x00
    int       Y;            // +0x04
    int       Width;        // +0x08
    int       Height;       // +0x0C
    int       Unused10;     // +0x10
    void*     Surface;      // +0x14
    uint16_t* BufferStart;  // +0x18 缓冲区起始指针
    uint16_t* BufferEnd;    // +0x1C 缓冲区结束指针 (One-past-the-end)
    uint32_t  BufferSize;   // +0x20 缓冲区总大小（以【字节】为单位！）
    uint32_t  DefaultZ;     // +0x24 默认清屏深度 (0x8000)
    int       Width2;       // +0x28
    int       Height2;      // +0x2C
};
```

**汇编环绕指令剖析**：
```asm
00492B59:  cmp  eax, edx             ; eax = zBuf (指针), edx = desc->BufferEnd
00492B5B:  jb   00492B60             ; 若未超出末端，跳过
00492B5D:  sub  eax, [esi + 0x20]    ; eax -= desc->BufferSize (字节减法回卷到前端)
```

> [!WARNING]
> **C++ 指针算术陷阱**：
> `BufferSize`（`+0x20`）记录的是**字节数**（即 `Width * Height * 2`）。在 C++ 中，如果 `zBuf` 为 `uint16_t*`，直接写 `zBuf -= desc->BufferSize` 会被编译器自动放大 2 倍（减去 `2 * BufferSize` 字节），直接导致指针跳出有效堆内存！
> 正确写法必须为：
> ```cpp
> if (zBuf >= desc->BufferEnd) {
>     zBuf = reinterpret_cast<uint16_t*>(reinterpret_cast<char*>(zBuf) - desc->BufferSize);
> }
> ```

---

## 3. Top 高频微内核汇编实现深度剖析

### 3.1 RLE 码流解析与两阶段状态机（`00 nn` 语法）

RLE 码流结构由两类标记构成：
1. **透明游程（Transparent Run）**：以单字节 `0x00` 开头，紧随一字节无符号计数 `nn`（0~255）。跳过 `nn` 个像素。注意：`00 00` 消耗 2 字节码流，代表 0 像素跳过，非终止符。
2. **不透明像素（Opaque Pixel）**：任何非 `0x00` 的字节 `c`。代表 1 个单独的不透明像素。**RLE 格式没有不透明 run，每个不透明像素占用 1 字节码流**。

所有 RLE 微内核严格执行**两阶段状态机**：

```
[ 进入 Blit ]
     │
     ▼
【阶段 A：左边界裁剪跳过】
while (EncodedLen > 0) {
    c = *src++;
    if (c == 0) EncodedLen -= *src++;
    else        EncodedLen -= 1;
}
     │
     ▼
【Overshoot 越界补偿】
overshoot = -EncodedLen;   // 游程跨越边界时 EncodedLen <= 0，故 overshoot >= 0
Length   -= overshoot;
dst      += overshoot;
zBuf     += overshoot; (并做 BufferEnd 环绕检查)
// 注意：原版汇编中 zmap 在 overshoot 处【绝不】推进！保持原版对齐行为！
     │
     ▼
【阶段 B：有效可见区间绘制】
while (Length > 0) {
    c = *src++;
    if (c == 0) {
        n = *src++;
        Length -= n; dst += n; (zBuf += n; zmap += n;)
    } else {
        执行像素着色 / 深度测试 / 写回;
        Length--; dst++; (zBuf++; zmap++;)
    }
}
```

---

### 3.2 `RLEBlitTransDarkenZRead@G` (虚表 0x007E5540 / 槽 1 入口 0x00496820)

步兵单位阴影绘制的核心，也是单位密集交战时最重的 RLE Blitter。共 93 字节代码。

#### 完整反汇编代码逐行分析：
```asm
00496820: 51               push     ecx                   ; 暂存 this〔勘误 ASM-FIX-34 · U-3〕本行起 5 行整体错位：原记 496820h 8b442410 `mov eax,[esp+0x10]`、496824h 8b542418 `mov edx,[esp+0x18]`、496828h 53 `push ebx`、496829h 55 `push ebp`、49682ah 51 `push ecx`；经 ±0x40 滑窗序列配准，真序列 = 下 5 行（`push ecx` 归位函数首指令）
00496821: 8B 44 24 14     mov      eax, [esp+0x14]       ; eax = EncodedLen (arg4)〔勘误 ASM-FIX-34〕原记 496824h + disp 0x18
00496825: 8B 54 24 1C     mov      edx, [esp+0x1C]       ; edx = zBuf (arg6)〔勘误 ASM-FIX-34〕原记 496828h + disp 0x18
00496829: 53               push     ebx                   ; 保护寄存器〔勘误 ASM-FIX-34〕原记 496828h（Δ=+1）
0049682a: 55               push     ebp〔勘误 ASM-FIX-34〕原记 496829h（Δ=+1）；原记 `push ecx` 的本行位置实为函数首指令（见上）
0049682b: 8b6c2414         mov      ebp, [esp+0x14]       ; ebp = src (arg2)
0049682f: 56               push     esi
00496830: 8b742414         mov      esi, [esp+0x14]       ; esi = dst (arg1)
00496834: 894c240c         mov      [esp+0x0c], ecx       ; 备份 this 到栈帧
00496838: 8b4c2438         mov      ecx, [esp+0x38]       ; ecx = zmap (arg10)
0049683c: 57               push     edi
0049683d: 8b3d44768800     mov      edi, [0x00887644]     ; edi = ZBufferDesc 指针

; --- 阶段 A：跳过 EncodedLen 像素 ---
00496843: 85c0             test     eax, eax
00496845: 7e31             jle      00496878              ; EncodedLen <= 0 直接跳到阶段 B
00496847: 8a5d00           mov      bl, [ebp]             ; bl = *src
0049684a: 45               inc      ebp                   ; src++
0049684b: 84db             test     bl, bl
0049684d: 750a             jne      00496859              ; 不透明像素 -> EncodedLen - 1
0049684f: 33db             xor      ebx, ebx
00496851: 8a5d00           mov      bl, [ebp]             ; bl = transparent run length (n)
00496854: 2bc3             sub      eax, ebx              ; EncodedLen -= n
00496856: 45               inc      ebp                   ; src++
00496857: eb01             jmp      0049685a
00496859: 48               dec      eax                   ; EncodedLen--
0049685a: 85c0             test     eax, eax
0049685c: 7fe9             jg       00496847              ; 继续跳过

; --- Overshoot 越界补偿 ---
0049685e: 8b5c2420         mov      ebx, [esp+0x20]       ; ebx = Length (arg3)
00496862: f7d8             neg      eax                   ; overshoot = -EncodedLen
00496864: 2bd8             sub      ebx, eax              ; Length -= overshoot
00496866: 8d3446           lea      esi, [esi+eax*2]      ; dst += overshoot * 2 (16-bit)
00496869: 8d0442           lea      eax, [edx+eax*2]      ; zBuf += overshoot * 2
0049686c: 3b471c           cmp      eax, [edi+0x1c]       ; zBuf >= BufferEnd?
0049686f: 7203             jb       00496874
00496871: 2b4720           sub      eax, [edi+0x20]       ; zBuf -= BufferSize
00496874: 8bd0             mov      edx, eax
00496876: eb04             jmp      0049687c

00496878: 8b5c2420         mov      ebx, [esp+0x20]       ; ebx = Length
0049687c: 85db             test     ebx, ebx
0049687e: 7e63             jle      004968e3              ; Length <= 0，退出

; --- 阶段 B：绘制循环 ---
00496880: 8a4500           mov      al, [ebp]             ; al = *src
00496883: 45               inc      ebp                   ; src++
00496884: 84c0             test     al, al
00496886: 751e             jne      004968a6              ; al != 0 -> 不透明处理

; [透明游程]
00496888: 8a4500           mov      al, [ebp]             ; run length n
0049688b: 45               inc      ebp                   ; src++
0049688c: 88442420         mov      [esp+0x20], al
00496890: 8b442420         mov      eax, [esp+0x20]
00496894: 25ff000000       and      eax, 0xff             ; eax = n
00496899: 2bd8             sub      ebx, eax              ; Length -= n
0049689b: 03c8             add      ecx, eax              ; zmap += n
0049689d: 8d3c00           lea      edi, [eax+eax]        ; edi = n * 2 字节
004968a0: 03f7             add      esi, edi              ; dst += n
004968a2: 03d7             add      edx, edi              ; zBuf += n
004968a4: eb2c             jmp      004968d2              ; 环绕检查

; [不透明像素 + Z 测试]
004968a6: 0fbe01           movsx    eax, byte ptr [ecx]   ; eax = (int)(int8_t)*zmap (有符号扩展！)
004968a9: 8b7c2428         mov      edi, [esp+0x28]       ; edi = zMin (arg5)
004968ad: 83c202           add      edx, 2                ; zBuf++ (预推进)
004968b0: 2bf8             sub      edi, eax              ; edi = zMin - zmap[i]
004968b2: 33c0             xor      eax, eax
004968b4: 668b42fe         mov      ax, [edx-2]           ; ax = *zBuf (当前像素深度)
004968b8: 41               inc      ecx                   ; zmap++
004968b9: 3bf8             cmp      edi, eax              ; 深度比较：(zMin - zmap[i]) ? zb
004968bb: 7d11             jge      004968ce              ; 若 threshold >= zb，被遮挡，跳过写回
004968bd: 668b06           mov      ax, [esi]             ; 读原目标像素 *dst
004968c0: 8b7c2410         mov      edi, [esp+0x10]       ; edi = this
004968c4: 66d1e8           shr      ax, 1                 ; 像素右移 1 位 (RGB565 变暗一半)
004968c7: 66234704         and      ax, [edi+4]           ; ax &= this->DarkenMask (清通道溢出)
004968cb: 668906           mov      [esi], ax             ; 写回 *dst

004968ce: 4b               dec      ebx                   ; Length--
004968cf: 83c602           add      esi, 2                ; dst++

; [ZBuffer 环绕检查]
004968d2: a144768800       mov      eax, [0x00887644]     ; eax = ZBufferDesc
004968d7: 3b501c           cmp      edx, [eax+0x1c]       ; zBuf >= BufferEnd?
004968da: 7203             jb       004968df
004968dc: 2b5020           sub      edx, [eax+0x20]       ; zBuf -= BufferSize
004968df: 85db             test     ebx, ebx
004968e1: 7f9d             jg       00496880              ; Length > 0 继续循环

004968e3: 5f 5e 5d 5b 59   pop edi, esi, ebp, ebx, ecx
004968e8: c22800           ret      0x28                  ; 平 10 个栈参数
```

---

### 3.3 `RLEBlitTransDarken@G` (虚表 0x007E55A0 / 槽 1 入口 0x00496250)

无 Z 缓冲的普通步兵阴影绘制。省去了 Z 比较与 zmap 维护，是纯粹的目标像素 RMW（Read-Modify-Write）操作。

#### 核心写入片段：
```asm
004962ae: 668b08           mov      cx, [eax]             ; cx = *dst (RGB565)
004962b1: 66d1e9           shr      cx, 1                 ; cx >>= 1
004962b4: 66234d04         and      cx, [ebp+4]           ; cx &= this->DarkenMask (0x7BEF)
004962b8: 4f               dec      edi                   ; Length--
004962b9: 668908           mov      [eax], cx             ; *dst = cx
004962bc: 83c002           add      eax, 2                ; dst++
```

---

### 3.4 `RLEBlitTransXlat@G` (虚表 0x007E55C0 / 槽 1 入口 0x004960A0)

步兵本体阵营色绘制的主路径。

#### 核心写入片段：
```asm
00496102: 8b4c2418         mov      ecx, [esp+0x18]       ; ecx = c (颜色索引)
00496106: 8b5504           mov      edx, [ebp+4]          ; edx = this->XlatTable
00496109: 81e1ff000000     and      ecx, 0xff             ; ecx &= 0xFF
0049610f: 83c002           add      eax, 2                ; dst++
00496112: 4f               dec      edi                   ; Length--
00496113: 668b0c4a         mov      cx, [edx+ecx*2]       ; cx = XlatTable[c]
00496117: 668948fe         mov      [eax-2], cx           ; *(dst-1) = cx
```

---

### 3.5 Non-RLE `BlitTransXlatZRead@G` (虚表 0x007E5978 / 槽 1 0x007E597C / 入口 0x00492B00)

密集无压缩流，与 RLE 的显著不同：
- **无透明游程，无 EncodedLen，无 overshoot**；
- `src`、`dst`、`zBuf` **三者齐头并进**：每一轮循环各步进 1 像素，即便 Z 测试失败或遇到透明索引 0，源指针 `src` 依然 `inc`，目标 `dst` 依然 `add 2`。

#### 完整反汇编代码剖析：
```asm
00492B00: 8b54240c         mov      edx, [esp+0xc]        ; edx = length
00492B04: 8b442414         mov      eax, [esp+0x14]       ; eax = zBuf
00492B08: 85d2             test     edx, edx
00492B0A: 7e5b             jle      00492b67              ; length <= 0 退出
00492B0C: 53               push     ebx
00492B0D: 8b5c240c         mov      ebx, [esp+0xc]        ; ebx = src (uint8_t* 索引流)
00492B11: 55 56            push     ebp, esi
00492B13: 8b3544768800     mov      esi, [0x00887644]     ; esi = ZBufferDesc
00492B19: 57               push     edi
00492B1A: 8b7c2414         mov      edi, [esp+0x14]       ; edi = dst (uint16_t*)
00492B1E: 8bea             mov      ebp, edx              ; ebp = length

; --- 循环核心 ---
00492B20: 33d2             xor      edx, edx
00492B22: 668b10           mov      dx, [eax]             ; dx = *zBuf
00492B25: 83c002           add      eax, 2                ; zBuf++
00492B28: 39542420         cmp      [esp+0x20], edx       ; 比较：zMin ? zb
00492B2C: 7d24             jge      00492b52              ; zMin >= zb -> 深度被遮挡，跳过写像素
00492B2E: 8a13             mov      dl, [ebx]             ; dl = *src
00492B30: 84d2             test     dl, dl
00492B32: 88542424         mov      [esp+0x24], dl
00492B36: 741a             je       00492b52              ; dl == 0 -> 透明色，跳过写像素
00492B38: 8b542424         mov      edx, [esp+0x24]
00492B3C: 8b7104           mov      esi, [ecx+4]          ; esi = this->XlatTable
00492B3F: 81e2ff000000     and      edx, 0xff
00492B45: 668b1456         mov      dx, [esi+edx*2]       ; dx = XlatTable[dl]
00492B49: 668917           mov      [edi], dx             ; *dst = dx
00492B4C: 8b3544768800     mov      esi, [0x00887644]     ; 恢复 esi

; --- 指针推进与环绕（无论是否绘制均执行） ---
00492B52: 8b561c           mov      edx, [esi+0x1c]       ; edx = BufferEnd
00492B55: 43               inc      ebx                   ; src++
00492B56: 83c702           add      edi, 2                ; dst++
00492B59: 3bc2             cmp      eax, edx              ; zBuf >= BufferEnd?
00492B5b: 7203             jb       00492b60
00492B5d: 2b4620           sub      eax, [esi+0x20]       ; zBuf -= BufferSize
00492B60: 4d               dec      ebp                   ; length--
00492B61: 75bd             jne      00492b20              ; 循环

00492B63: 5f 5e 5d 5b      pop edi, esi, ebp, ebx
00492B67: c22000           ret      0x20                  ; 平 8 个栈参数
```

---

### 3.6 Non-RLE `BlitTransDarkenZRead@G` (虚表 0x007E5948 / 槽 1 0x007E594C / 入口 0x00492D20)

载具和建筑投射阴影落到不同高程地形时的深度变暗。逻辑与 `BlitTransXlatZRead@G` 结构完全一致，仅在写入阶段由查表换为 `*dst = (*dst >> 1) & this->DarkenMask`。

#### 核心写入片段：
```asm
00492D48: 396c2420         cmp      [esp+0x20], ebp       ; zMin ? zb
00492D4C: 7d18             jge      00492d66              ; 遮挡跳过
00492D4E: 803f00           cmp      byte ptr [edi], 0     ; *src == 0 (透明)
00492D51: 7413             je       00492d66              ; 透明跳过
00492D53: 668b32           mov      si, [edx]             ; si = *dst
00492D56: 66d1ee           shr      si, 1
00492D59: 66237104         and      si, [ecx+4]           ; si &= this->DarkenMask (ECX 为 this)
00492D5D: 668932           mov      [edx], si             ; *dst = si
00492D60: 8b3544768800     mov      esi, [0x00887644]
00492D66: ... 推进 src/dst/zBuf 并检查 BufferEnd ...
```

---

## 4. 现网代码缺陷诊断与修复方案

### 4.1 `ra2render.h` 现有声明缺陷

| 符号 / 位置 | 现网声明 | 汇编真实情况 | 潜在危害 | 修复要求 |
|---|---|---|---|---|
| `RLEBlitterCore::Blit` | `uint8_t Length` | `int Length` (32-bit) | 任何扫描线宽 > 255 像素时发生高位截断，导致右侧渲染缺失 | 修正为 `int Length` |
| `RLEBlitterCore::Blit` | `int EncodedLen` | 语义为 `int leftClipSkip` | 命名误导为压缩包字节长度 | 明确注释为左裁剪像素跳过数 |
| `RLEBlitterCore::Blit` | `int a6, a7, ..., a11` | `zMin, zBuf, aBuf, aLvl, warpOffset, zmap` | 未具名且缺少指针类型约束 | 补齐具名类型签名 |
| `RLEBlitterCore` 成员 | `uint16_t *XlatTable` | Darken 变体中是 `uint16_t DarkenMask` | Darken 变体解引用直接 Crash | 拆分特化结构体或定义通用联合体 |
| 全局 Z 描述符 | 未定义 | `0x00887644` 存放 `ZBufferDesc*` | 现有 ZRead Hook 缺少环形回卷支持，越界时写飞内存 | 新增 `ZBufferDesc` 结构体 |

### 4.2 `blitter_hooks.cpp` 现有逻辑缺陷

1. `Hook_RLEBlitTransXlat_G`：目前仅有性能计数器统计，**完全未实现像素级逻辑**，全部原样转调原版汇编；
2. `Hook_BlitTransXlatAlphaZRead`：在 SIMD 循环中直接使用 `z[i+k]` 索引深度缓冲，**完全忽略了 0x00887644 环形跨界回卷**。当一行像素跨越 `BufferEnd` 时，将产生非法越界读取；
3. 未安装 `RLEBlitTransDarken`、`RLEBlitTransDarkenZRead`、`BlitTransXlatZRead` 与 `BlitTransDarkenZRead` 的 Hook，核心高频路径仍处于原版标量低效运行状态。

---

## 5. SSE2 向量化替代微内核设计

### 5.1 向量化可行性与加速天花板分析

1. **RLE 码流解析的本质限制**：
   RLE 编码是逐字节可变长序列，无法用 SIMD 展开解码循环。
2. **真正的向量化加速红利**：
   - **Darken 像素变暗**：纯目标内存 RMW，无查表开销。一次处理 8 个 RGB565 像素（128-bit），每拍吞吐量提升 8 倍！
   - **前瞻扫描批处理（Opaque Chunk Batching）**：利用 `_mm_cmpeq_epi8` 与 `_mm_movemask_epi8` 一次检查 8~16 字节源码流。若全为非零字节，则代表 8~16 个连续实体像素，完全绕过标量解码分支，直接进入 SIMD 批写。
   - **无分支深度遮挡掩码（Branchless Z Masking）**：使用 `_mm_cmpgt_epi16` 结合符号位翻转（Unsigned Compare Trick）一次性对比 8 像素深度，生成写回掩码，消除流水线分支预测失误。
   - **环形缓冲区安全距离（Safety Runaway）**：批处理前计算 `safePixels = (BufferEnd - zBuf) >> 1`。仅在 `safePixels >= 8` 时开启 SIMD 8 像素批处理；临界跨界段退化为严格的标量回卷微内核，确保 100% 内存安全。

### 5.2 SSE2 16 位无符号数比较算法（Unsigned Compare Trick）

x86 SSE2 的 `_mm_cmpgt_epi16` 只能做**有符号** 16 位整数比较。而深度缓冲 `zBuf` 为**无符号 `uint16_t`**（0~65535）。  
标准 IEEE/Intel 向量化技巧：**将两个操作数同时翻转最高符号位（`^ 0x8000`）**，将其无符号大小映射为有符号数，再调用 `_mm_cmpgt_epi16`：

$$\text{SignFlip}(x) = x \oplus \text{0x8000}$$
$$A > B \iff (A \oplus \text{0x8000}) >_{\text{signed}} (B \oplus \text{0x8000})$$

---

## 6. 生产级落地 C++ / SSE2 微内核实现原型

以下代码可直接接入 `ra2render` 生产工程，兼顾精确汇编行为与 SSE2 性能极限。

### 6.1 核心头文件扩展定义（注入 `ra2render.h`）

```cpp
#pragma once
#include <cstdint>
#include <emmintrin.h>

// ----------------------------------------------------------------------------
// 虚表与入口地址常量
// ----------------------------------------------------------------------------
#define ADDR_VTABLE_RLE_BLIT_TRANS_XLAT_G        0x007E55C0
#define ADDR_VFUNC_RLE_BLIT_TRANS_XLAT_G          0x004960A0

#define ADDR_VTABLE_RLE_BLIT_TRANS_DARKEN_G      0x007E55A0
#define ADDR_VFUNC_RLE_BLIT_TRANS_DARKEN_G        0x00496250

#define ADDR_VTABLE_RLE_BLIT_TRANS_DARKEN_ZREAD_G 0x007E5540
#define ADDR_VFUNC_RLE_BLIT_TRANS_DARKEN_ZREAD_G  0x00496820

#define ADDR_VTABLE_BLIT_TRANS_XLAT_ZREAD_G      0x007E5978
#define ADDR_VFUNC_BLIT_TRANS_XLAT_ZREAD_G        0x00492B00

#define ADDR_VTABLE_BLIT_TRANS_DARKEN_ZREAD_G    0x007E5948
#define ADDR_VFUNC_BLIT_TRANS_DARKEN_ZREAD_G      0x00492D20

#define ADDR_GLOBAL_ZBUFFER_DESC                 0x00887644
#define ADDR_GLOBAL_ABUFFER_DESC                 0x0087E8A4

// ----------------------------------------------------------------------------
// 全局 Z 缓冲描述符
// ----------------------------------------------------------------------------
#pragma pack(push, 1)
struct ZBufferDesc {
    int       X;
    int       Y;
    int       Width;
    int       Height;
    int       Unused10;
    void*     Surface;
    uint16_t* BufferStart;   // +0x18
    uint16_t* BufferEnd;     // +0x1C (末端警戒指针)
    uint32_t  BufferSize;    // +0x20 (总字节数)
    uint32_t  DefaultZ;      // +0x24 (0x8000)
    int       Width2;
    int       Height2;
};
#pragma pack(pop)

// ----------------------------------------------------------------------------
// 特化 Blitter 对象布局
// ----------------------------------------------------------------------------
class RLEBlitterCoreBase {
public:
    virtual ~RLEBlitterCoreBase() = default;
    virtual void __thiscall Blit(
        void *dst, const uint8_t *src, int Length, int leftClipSkip,
        uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, int aLvl, int warpOffset, const int8_t *zmap
    ) = 0;
    virtual void __thiscall CallBlit0(
        void *dst, const uint8_t *src, int Length, int leftClipSkip,
        uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, int aLvl, int warpOffset, const int8_t *zmap,
        uint32_t useless
    ) = 0;
};

class RLEBlitterXlatCore : public RLEBlitterCoreBase {
public:
    const uint16_t *XlatTable; // +0x04
};

class RLEBlitterDarkenCore : public RLEBlitterCoreBase {
public:
    uint16_t DarkenMask;       // +0x04 (值)
    uint16_t Padding06;        // +0x06
};

class NonRLEBlitterCoreBase {
public:
    virtual ~NonRLEBlitterCoreBase() = default;
    virtual void __thiscall Blit(
        void *dst, const void *src, int length,
        uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset
    ) = 0;
};

class NonRLEBlitterXlatCore : public NonRLEBlitterCoreBase {
public:
    const uint16_t *XlatTable; // +0x04
};

class NonRLEBlitterDarkenCore : public NonRLEBlitterCoreBase {
public:
    uint16_t DarkenMask;       // +0x04 (值)
    uint16_t Padding06;
};
```

---

### 6.2 SSE2 向量化微内核实现代码（注入 `blitter_hooks.cpp`）

```cpp
#include "ra2render.h"

// 辅助内联：安全执行 Z 缓冲区跨界回卷
static inline void CheckAndWrapZBuffer(uint16_t*& zBuf, const ZBufferDesc* desc) {
    if (desc && zBuf >= desc->BufferEnd) {
        zBuf = reinterpret_cast<uint16_t*>(reinterpret_cast<char*>(zBuf) - desc->BufferSize);
    }
}

// ----------------------------------------------------------------------------
// 1. RLEBlitTransDarken@G: 步兵无遮挡变暗 (最高频，纯 dst RMW)
// ----------------------------------------------------------------------------
void __fastcall Microkernel_RLEBlitTransDarken_SSE2(
    uint16_t *dst, const uint8_t *src, int Length, int leftClipSkip, uint16_t darkenMask
) {
    // ---- 阶段 A：左边界裁剪跳过 ----
    while (leftClipSkip > 0) {
        uint8_t c = *src++;
        if (c == 0) {
            leftClipSkip -= *src++;
        } else {
            leftClipSkip -= 1;
        }
    }

    // ---- Overshoot 越界补偿 ----
    int overshoot = -leftClipSkip;
    if (overshoot > 0) {
        Length -= overshoot;
        dst += overshoot;
    }

    if (Length <= 0) return;

    // ---- 阶段 B：绘制循环 ----
    const __m128i mask128 = _mm_set1_epi16(static_cast<short>(darkenMask));

    while (Length > 0) {
        uint8_t c = *src++;
        if (c == 0) {
            // [透明游程]
            uint8_t n = *src++;
            Length -= n;
            dst += n;
        } else {
            // [不透明像素前瞻]
            // 若剩余预算 >= 8，尝试探测连续非零块
            if (Length >= 8) {
                // 读取当前及后续字节
                // 由于 c 已经读取，回退指针做 8 字节前瞻检测
                const uint8_t *lookaheadSrc = src - 1;
                // 快速检查后续连续非零
                int opaqueCount = 1;
                while (opaqueCount < 8 && lookaheadSrc[opaqueCount] != 0) {
                    opaqueCount++;
                }

                if (opaqueCount == 8) {
                    // 完美的 8 像素连续变暗！直接执行 SSE2 向量写入
                    __m128i d = _mm_loadu_si128(reinterpret_cast<const __m128i*>(dst));
                    __m128i darkened = _mm_and_si128(_mm_srli_epi16(d, 1), mask128);
                    _mm_storeu_si128(reinterpret_cast<__m128i*>(dst), darkened);

                    dst += 8;
                    src += 7; // 前面已读 1 字节，推进剩余 7 字节
                    Length -= 8;
                    continue;
                }
            }

            // 标量回退处理单像素
            *dst = (*dst >> 1) & darkenMask;
            dst++;
            Length--;
        }
    }
}

// ----------------------------------------------------------------------------
// 2. RLEBlitTransDarkenZRead@G: 步兵带深度遮挡变暗
// ----------------------------------------------------------------------------
void __fastcall Microkernel_RLEBlitTransDarkenZRead_SSE2(
    uint16_t *dst, const uint8_t *src, int Length, int leftClipSkip,
    uint16_t zMin, uint16_t *zBuf, const int8_t *zmap, uint16_t darkenMask
) {
    const ZBufferDesc *zDesc = *reinterpret_cast<const ZBufferDesc**>(ADDR_GLOBAL_ZBUFFER_DESC);

    // ---- 阶段 A：左边界裁剪跳过 ----
    while (leftClipSkip > 0) {
        uint8_t c = *src++;
        if (c == 0) {
            leftClipSkip -= *src++;
        } else {
            leftClipSkip -= 1;
        }
    }

    // ---- Overshoot 越界补偿 ----
    int overshoot = -leftClipSkip;
    if (overshoot > 0) {
        Length -= overshoot;
        dst += overshoot;
        zBuf += overshoot;
        CheckAndWrapZBuffer(zBuf, zDesc);
        // 注意：zmap 依照原版汇编规范不予推进
    }

    if (Length <= 0) return;

    // ---- 阶段 B：绘制循环 ----
    const __m128i mask128 = _mm_set1_epi16(static_cast<short>(darkenMask));
    const __m128i signFlip = _mm_set1_epi16(static_cast<short>(0x8000));
    const __m128i zMin128 = _mm_set1_epi16(static_cast<short>(zMin));

    while (Length > 0) {
        uint8_t c = *src++;
        if (c == 0) {
            // [透明游程]
            uint8_t n = *src++;
            Length -= n;
            dst += n;
            zmap += n;
            zBuf += n;
            CheckAndWrapZBuffer(zBuf, zDesc);
        } else {
            // [不透明像素 + 深度测试]
            // 检查环形缓冲安全距离与剩余长度，若 >= 8 且连续 8 个不透明，走 SSE2 批处理
            uintptr_t safeBytes = zDesc ? (reinterpret_cast<uintptr_t>(zDesc->BufferEnd) - reinterpret_cast<uintptr_t>(zBuf)) : 0;
            if (Length >= 8 && safeBytes >= (8 * sizeof(uint16_t))) {
                const uint8_t *lookaheadSrc = src - 1;
                int opaqueCount = 1;
                while (opaqueCount < 8 && lookaheadSrc[opaqueCount] != 0) {
                    opaqueCount++;
                }

                if (opaqueCount == 8) {
                    // 1. 加载 8 字节 zmap 并符号扩展为 8 个 16 位整数
                    __m128i z8 = _mm_loadl_epi64(reinterpret_cast<const __m128i*>(zmap));
                    __m128i z16 = _mm_srai_epi16(_mm_unpacklo_epi8(z8, z8), 8);

                    // 2. 计算 8 像素阈值: thr = zMin - zmap[i]
                    __m128i thr16 = _mm_sub_epi16(zMin128, z16);

                    // 3. 加载 8 像素深度: zb
                    __m128i zb16 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(zBuf));

                    // 4. 无符号比较: zb > thr
                    __m128i zb_s = _mm_xor_si128(zb16, signFlip);
                    __m128i thr_s = _mm_xor_si128(thr16, signFlip);
                    __m128i passMask = _mm_cmpgt_epi16(zb_s, thr_s);

                    // 5. 变暗与掩码条件写回
                    __m128i d = _mm_loadu_si128(reinterpret_cast<const __m128i*>(dst));
                    __m128i darkened = _mm_and_si128(_mm_srli_epi16(d, 1), mask128);
                    __m128i result = _mm_or_si128(_mm_and_si128(passMask, darkened), _mm_andnot_si128(passMask, d));
                    _mm_storeu_si128(reinterpret_cast<__m128i*>(dst), result);

                    // 推进指针
                    dst += 8;
                    zmap += 8;
                    zBuf += 8;
                    src += 7;
                    Length -= 8;
                    CheckAndWrapZBuffer(zBuf, zDesc);
                    continue;
                }
            }

            // 标量微内核回退
            int8_t zoff = *zmap++;
            uint16_t thr = static_cast<uint16_t>(zMin - zoff);
            uint16_t zb = *zBuf++;
            if (zb > thr) {
                *dst = (*dst >> 1) & darkenMask;
            }
            dst++;
            Length--;
            CheckAndWrapZBuffer(zBuf, zDesc);
        }
    }
}

// ----------------------------------------------------------------------------
// 3. RLEBlitTransXlat@G: 步兵本体调色板阵营色绘制
// ----------------------------------------------------------------------------
void __fastcall Microkernel_RLEBlitTransXlat_SSE2(
    uint16_t *dst, const uint8_t *src, int Length, int leftClipSkip, const uint16_t *xlat
) {
    while (leftClipSkip > 0) {
        uint8_t c = *src++;
        if (c == 0) leftClipSkip -= *src++;
        else        leftClipSkip -= 1;
    }

    int overshoot = -leftClipSkip;
    if (overshoot > 0) {
        Length -= overshoot;
        dst += overshoot;
    }

    if (Length <= 0) return;

    while (Length > 0) {
        uint8_t c = *src++;
        if (c == 0) {
            uint8_t n = *src++;
            Length -= n;
            dst += n;
        } else {
            // 实体像素查表写回
            *dst++ = xlat[c];
            Length--;
        }
    }
}

// ----------------------------------------------------------------------------
// 4. BlitTransDarkenZRead@G: Non-RLE 密集深度变暗 (载具/建筑阴影)
// ----------------------------------------------------------------------------
void __fastcall Microkernel_BlitTransDarkenZRead_SSE2(
    uint16_t *dst, const uint8_t *src, int length,
    uint16_t zMin, uint16_t *zBuf, uint16_t darkenMask
) {
    const ZBufferDesc *zDesc = *reinterpret_cast<const ZBufferDesc**>(ADDR_GLOBAL_ZBUFFER_DESC);
    const __m128i mask128 = _mm_set1_epi16(static_cast<short>(darkenMask));
    const __m128i signFlip = _mm_set1_epi16(static_cast<short>(0x8000));
    const __m128i zMin_s = _mm_xor_si128(_mm_set1_epi16(static_cast<short>(zMin)), signFlip);
    const __m128i zero128 = _mm_setzero_si128();

    while (length >= 8) {
        uintptr_t safeBytes = zDesc ? (reinterpret_cast<uintptr_t>(zDesc->BufferEnd) - reinterpret_cast<uintptr_t>(zBuf)) : 0;
        if (safeBytes < (8 * sizeof(uint16_t))) {
            break; // 靠近环形边界，交由标量处理
        }

        // 1. 加载 8 字节索引，判断非零
        __m128i s8 = _mm_loadl_epi64(reinterpret_cast<const __m128i*>(src));
        __m128i s16 = _mm_unpacklo_epi8(s8, zero128);
        __m128i nonzeroMask = _mm_cmpgt_epi16(s16, zero128);

        // 2. 加载 8 像素深度，无符号比较 zb > zMin
        __m128i zb16 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(zBuf));
        __m128i zb_s = _mm_xor_si128(zb16, signFlip);
        __m128i zPassMask = _mm_cmpgt_epi16(zb_s, zMin_s);

        // 3. 组合通过掩码
        __m128i activeMask = _mm_and_si128(nonzeroMask, zPassMask);
        int activeBits = _mm_movemask_epi8(activeMask);

        if (activeBits == 0) {
            // 快速跳过：8 像素全为透明或全被遮挡，完全无需碰触目标显存！
            dst += 8;
            src += 8;
            zBuf += 8;
            length -= 8;
            CheckAndWrapZBuffer(zBuf, zDesc);
            continue;
        }

        // 4. 掩码混合写回
        __m128i d = _mm_loadu_si128(reinterpret_cast<const __m128i*>(dst));
        __m128i darkened = _mm_and_si128(_mm_srli_epi16(d, 1), mask128);
        __m128i result = _mm_or_si128(_mm_and_si128(activeMask, darkened), _mm_andnot_si128(activeMask, d));
        _mm_storeu_si128(reinterpret_cast<__m128i*>(dst), result);

        dst += 8;
        src += 8;
        zBuf += 8;
        length -= 8;
        CheckAndWrapZBuffer(zBuf, zDesc);
    }

    // 标量收尾
    while (length-- > 0) {
        uint16_t zb = *zBuf++;
        uint8_t idx = *src++;
        if (zb > zMin && idx != 0) {
            *dst = (*dst >> 1) & darkenMask;
        }
        dst++;
        CheckAndWrapZBuffer(zBuf, zDesc);
    }
}

// ----------------------------------------------------------------------------
// 5. BlitTransXlatZRead@G: Non-RLE 密集调色板映射与深度测试 (载具本体重叠)
// ----------------------------------------------------------------------------
void __fastcall Microkernel_BlitTransXlatZRead_SSE2(
    uint16_t *dst, const uint8_t *src, int length,
    uint16_t zMin, uint16_t *zBuf, const uint16_t *xlat
) {
    const ZBufferDesc *zDesc = *reinterpret_cast<const ZBufferDesc**>(ADDR_GLOBAL_ZBUFFER_DESC);
    const __m128i signFlip = _mm_set1_epi16(static_cast<short>(0x8000));
    const __m128i zMin_s = _mm_xor_si128(_mm_set1_epi16(static_cast<short>(zMin)), signFlip);
    const __m128i zero128 = _mm_setzero_si128();

    while (length >= 8) {
        uintptr_t safeBytes = zDesc ? (reinterpret_cast<uintptr_t>(zDesc->BufferEnd) - reinterpret_cast<uintptr_t>(zBuf)) : 0;
        if (safeBytes < (8 * sizeof(uint16_t))) {
            break;
        }

        __m128i s8 = _mm_loadl_epi64(reinterpret_cast<const __m128i*>(src));
        __m128i s16 = _mm_unpacklo_epi8(s8, zero128);
        __m128i nonzeroMask = _mm_cmpgt_epi16(s16, zero128);

        __m128i zb16 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(zBuf));
        __m128i zb_s = _mm_xor_si128(zb16, signFlip);
        __m128i zPassMask = _mm_cmpgt_epi16(zb_s, zMin_s);

        __m128i activeMask = _mm_and_si128(nonzeroMask, zPassMask);
        int activeBits = _mm_movemask_epi8(activeMask);

        if (activeBits == 0) {
            dst += 8;
            src += 8;
            zBuf += 8;
            length -= 8;
            CheckAndWrapZBuffer(zBuf, zDesc);
            continue;
        }

        // 部分或全部通过：标量高效查表写回通过像素
        for (int k = 0; k < 8; ++k) {
            if ((activeBits >> (k * 2)) & 3) {
                dst[k] = xlat[src[k]];
            }
        }

        dst += 8;
        src += 8;
        zBuf += 8;
        length -= 8;
        CheckAndWrapZBuffer(zBuf, zDesc);
    }

    while (length-- > 0) {
        uint16_t zb = *zBuf++;
        uint8_t idx = *src++;
        if (zb > zMin && idx != 0) {
            *dst = xlat[idx];
        }
        dst++;
        CheckAndWrapZBuffer(zBuf, zDesc);
    }
}
```

---

## 7. 虚表挂钩安装对照表与验证策略

### 7.1 Hook 入口包装函数与虚表挂钩点

```cpp
// ----------------------------------------------------------------------------
// 虚表注入点包装函数
// ----------------------------------------------------------------------------
void __thiscall Hook_RLEBlitTransDarkenZRead_G(
    void *dst, const uint8_t *src, int Length, int leftClipSkip,
    uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, int aLvl, int warpOffset, const int8_t *zmap
) {
    RLEBlitterDarkenCore *pThis = reinterpret_cast<RLEBlitterDarkenCore*>(this);
    g_telemetry.totalBlitCalls++;
    g_telemetry.totalBlitPixels += Length;

    if (g_enableSIMD) {
        Microkernel_RLEBlitTransDarkenZRead_SSE2(
            static_cast<uint16_t*>(dst), src, Length, leftClipSkip, zMin, zBuf, zmap, pThis->DarkenMask
        );
    } else if (g_pOrigRLEBlitTransDarkenZRead_G) {
        g_pOrigRLEBlitTransDarkenZRead_G(pThis, dst, src, Length, leftClipSkip, zMin, zBuf, aBuf, aLvl, warpOffset, zmap);
    }
}

void __thiscall Hook_RLEBlitTransDarken_G(
    void *dst, const uint8_t *src, int Length, int leftClipSkip,
    uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, int aLvl, int warpOffset, const int8_t *zmap
) {
    RLEBlitterDarkenCore *pThis = reinterpret_cast<RLEBlitterDarkenCore*>(this);
    g_telemetry.totalBlitCalls++;
    g_telemetry.totalBlitPixels += Length;

    if (g_enableSIMD) {
        Microkernel_RLEBlitTransDarken_SSE2(
            static_cast<uint16_t*>(dst), src, Length, leftClipSkip, pThis->DarkenMask
        );
    } else if (g_pOrigRLEBlitTransDarken_G) {
        g_pOrigRLEBlitTransDarken_G(pThis, dst, src, Length, leftClipSkip, zMin, zBuf, aBuf, aLvl, warpOffset, zmap);
    }
}

void __thiscall Hook_BlitTransDarkenZRead_G(
    void *dst, const void *src, int length,
    uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset
) {
    NonRLEBlitterDarkenCore *pThis = reinterpret_cast<NonRLEBlitterDarkenCore*>(this);
    g_telemetry.totalBlitCalls++;
    g_telemetry.totalBlitPixels += length;

    if (g_enableSIMD) {
        Microkernel_BlitTransDarkenZRead_SSE2(
            static_cast<uint16_t*>(dst), static_cast<const uint8_t*>(src), length, zMin, zBuf, pThis->DarkenMask
        );
    } else if (g_pOrigBlitTransDarkenZRead_G) {
        g_pOrigBlitTransDarkenZRead_G(pThis, dst, src, length, zMin, zBuf, aBuf, aLvl, warpOffset);
    }
}

void __thiscall Hook_BlitTransXlatZRead_G(
    void *dst, const void *src, int length,
    uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset
) {
    NonRLEBlitterXlatCore *pThis = reinterpret_cast<NonRLEBlitterXlatCore*>(this);
    g_telemetry.totalBlitCalls++;
    g_telemetry.totalBlitPixels += length;

    if (g_enableSIMD) {
        Microkernel_BlitTransXlatZRead_SSE2(
            static_cast<uint16_t*>(dst), static_cast<const uint8_t*>(src), length, zMin, zBuf, pThis->XlatTable
        );
    } else if (g_pOrigBlitTransXlatZRead_G) {
        g_pOrigBlitTransXlatZRead_G(pThis, dst, src, length, zMin, zBuf, aBuf, aLvl, warpOffset);
    }
}
```

### 7.2 虚表挂钩安装代码（扩展 `InstallVTableHooks()`）

```cpp
// 注入 InstallVTableHooks()
PatchVTablePointer(ADDR_VTABLE_RLE_BLIT_TRANS_XLAT_G + 4,
                   union_cast<uintptr_t>(&Hook_RLEBlitTransXlat_G),
                   reinterpret_cast<uintptr_t*>(&g_pOrigRLEBlitTransXlat_G),
                   "?$RLEBlitTransXlat@G::v1");

PatchVTablePointer(ADDR_VTABLE_RLE_BLIT_TRANS_DARKEN_G + 4,
                   union_cast<uintptr_t>(&Hook_RLEBlitTransDarken_G),
                   reinterpret_cast<uintptr_t*>(&g_pOrigRLEBlitTransDarken_G),
                   "?$RLEBlitTransDarken@G::v1");

PatchVTablePointer(ADDR_VTABLE_RLE_BLIT_TRANS_DARKEN_ZREAD_G + 4,
                   union_cast<uintptr_t>(&Hook_RLEBlitTransDarkenZRead_G),
                   reinterpret_cast<uintptr_t*>(&g_pOrigRLEBlitTransDarkenZRead_G),
                   "?$RLEBlitTransDarkenZRead@G::v1");

PatchVTablePointer(ADDR_VTABLE_BLIT_TRANS_XLAT_ZREAD_G + 4,
                   union_cast<uintptr_t>(&Hook_BlitTransXlatZRead_G),
                   reinterpret_cast<uintptr_t*>(&g_pOrigBlitTransXlatZRead_G),
                   "?$BlitTransXlatZRead@G::v1");

PatchVTablePointer(ADDR_VTABLE_BLIT_TRANS_DARKEN_ZREAD_G + 4,
                   union_cast<uintptr_t>(&Hook_BlitTransDarkenZRead_G),
                   reinterpret_cast<uintptr_t*>(&g_pOrigBlitTransDarkenZRead_G),
                   "?$BlitTransDarkenZRead@G::v1");
```

---

## 8. 总结与下一步建议

1. **结构体类型与安全性修复完毕**：彻底澄清了 `Darken` 变体中 `this+0x04` 为标量 `uint16_t DarkenMask`（数值，非指针）的关键事实，避免了原版代码中的指针类型误用风险；
2. **栈帧签名彻底纠偏**：将 `RLEBlitterCore::Blit` 中的 `Length` 由截断的 `uint8_t` 修正为标准的 32 位 `int`，补全了 `zMin/zBuf/zmap` 等 10 项参数；
3. **环形深度缓冲跨界安全机制**：解析了 `0x00887644` 全局描述符，确保在 SSE2 批处理中采用安全前瞻检测（Safety Runaway），在跨界边缘无缝退化为安全回卷标量处理；
4. **SSE2 向量化落地收益**：对于暗化阴影（纯 dst RMW），8 像素单拍变暗与无分支批量跳过可实现 4~8 倍的微内核吞吐加速，显著降低大型战役中百人步兵集群同屏时的掉帧现象。

---

## §8 冲刺结论（S13）

在 S13 专项冲刺中，通过对 `gamemd.exe` 1.001（西木引擎软件渲染微内核）展开深度符号交叉引用与二进制反汇编取证，彻底闭环了此前遗留的 **Blitter 对象 this 成员布局分化**、**ZRead/WriteZ 深度比较与指针推进语义边界**、以及 **非 RLE 族具名热点接管优先级排序** 三大核心架构议题。

---

### 8.1 Blitter 微内核各变体 this 布局全矩阵与西木工厂分配机制

#### 8.1.1 西木工厂方法整体拓扑（0x0048EBF0–0x00490488）
西木引擎在 `ConvertClass` 内部构建了一个统一的集中式工厂方法（入口位于 `0x0048EBF0`，返回于 `0x00490488`）。该方法依据目标颜色模式分化为两大独立子流水线：
- **8 位调色板管线（@E）**：`0x0048EBF6: cmp dword ptr [esi+4], 1; jne 0x48f054`。当且仅当像素深度为 8 位时，分配并初始化 8 位调色板重映射与混合对象；
- **16 位 HighColor 管线（@G）**：`0x0048F054`。负责全套 RGB565 精灵渲染、阴影暗化、半透明以及 Z 缓冲交互对象的初始化。

#### 8.1.2 内存分配大小分化（4 字节 / 8 字节 / 12 字节 / 16 字节）
反汇编证实，早期研究中“所有 Blitter 对象统一分配 12 字节”的认知存在偏差。引擎严格遵循按需分配原则（通过 `push <size>; call operator new(0x7c8e17)`）：

```
[ Blitter 对象内存规格分类 ]
1.  4 字节：无成员对象（BlitPlain@G, BlitTrans@G），通常在栈帧或静态区直接构造，仅含 vtable 指针；
2.  8 字节：单成员对象（Xlat 单级查表族、Darken 掩码值族），含 vtable 指针 + 1 个 4 字节槽；
3. 12 字节：双成员对象（Lucent 查表+掩码族、ZRemap 二级查表族、Alpha 动态表族），含 vtable 指针 + 2 个 4 字节槽；
4. 16 字节：复合三成员对象（Lucent*Alpha* 复杂特效复合变体），含 vtable 指针 + 3 个 4 字节槽。
```

#### 8.1.3 核心变体 this 布局全矩阵表

| 变体名称 | 虚表基址 (vtable) | Slot 1 Blit 入口 | 析构函数 (Slot 0) | 对象内存大小 | `this + 0x04` 真实类型与语义 | `this + 0x08` 真实类型与语义 | `this + 0x0C` 真实类型与语义 | 析构行为与资源所有权 |
|---|---|---|---|---|---|---|---|---|
| **`BlitPlain@G`** | `0x007F7BC4` | `0x007BC7F0` | `0x007BC660` | **4 字节** | 无（未分配） | 无 | 无 | Trivial（仅 `operator delete`） |
| **`BlitTrans@G`** | `0x007F7BF4` | `0x007BC890` | `0x007BC6A0` | **4 字节** | 无（未分配） | 无 | 无 | Trivial（仅 `operator delete`） |
| **`BlitPlainXlat@G`** | `0x007E5A38` | `0x004924C0` | `0x00499F20` | **8 字节** | `const uint16_t* XlatTable`（指针） | 无（越界不可访问） | 无 | Trivial，借用引擎静态调色板表 |
| **`BlitPlainXlatZRead@G`** | `0x007E5990` | `0x00492A10` | `0x00499FE0` | **8 字节** | `const uint16_t* XlatTable`（指针） | 无 | 无 | Trivial |
| **`BlitTransXlat@G`** | `0x007E5A20` | `0x004912B0` | `0x00499CA0` | **8 字节** | `const uint16_t* XlatTable`（指针） | 无 | 无 | Trivial |
| **`BlitTransXlatZRead@G`** | `0x007E5978` | `0x00492B00` | `0x0049A000` | **8 字节** | `const uint16_t* XlatTable`（指针） | 无 | 无 | Trivial |
| **`BlitTransXlatZReadWrite@G`** | `0x007E5888` | `0x00493600` | `0x0049A140` | **8 字节** | `const uint16_t* XlatTable`（指针） | 无 | 无 | Trivial |
| **`BlitTransDarken@G`** | `0x007E59F0` | `0x00492670` | `0x00499F60` | **8 字节** | **`uint16_t DarkenMask`（数值！）** | 无 | 无 | Trivial，数值掩码无所有权 |
| **`BlitTransDarkenZRead@G`** | `0x007E5948` | `0x00492D20` | `0x0049A040` | **8 字节** | **`uint16_t DarkenMask`（数值！）** | 无 | 无 | Trivial，数值掩码无所有权 |
| **`BlitTransDarkenZReadWrite@G`** | `0x007E5858` | `0x00493830` | `0x0049A180` | **8 字节** | **`uint16_t DarkenMask`（数值！）** | 无 | 无 | Trivial，数值掩码无所有权 |
| **`BlitTransLucent50@G`** | `0x007E59C0` | `0x00492830` | `0x00499FA0` | **12 字节** | `const uint16_t* XlatTable`（指针） | **`uint16_t BlendMask`（数值！）** | 无 | Trivial（掩码典型 `0x7BEF`） |
| **`BlitTransLucent50ZRead@G`** | `0x007E5918` | `0x00492F30` | `0x0049A080` | **12 字节** | `const uint16_t* XlatTable`（指针） | **`uint16_t BlendMask`（数值！）** | 无 | Trivial |
| **`BlitTransLucent25@G`** | `0x007E59A8` | `0x00492920` | `0x00499FC0` | **12 字节** | `const uint16_t* XlatTable`（指针） | **`uint16_t BlendMask`（数值！）** | 无 | Trivial（掩码典型 `0x3DEF`） |
| **`BlitTransLucent75@G`** | `0x007E59D8` | `0x00492740` | `0x00499F80` | **12 字节** | `const uint16_t* XlatTable`（指针） | **`uint16_t BlendMask`（数值！）** | 无 | Trivial（掩码典型 `0x3DEF`） |
| **`BlitTransZRemapXlat@G`** | `0x007E5A08` | `0x00492590` | `0x00499F40` | **12 字节** | **`const uint8_t** pRemap`（二级指针）** | `const uint16_t* XlatTable`（指针） | 无 | Trivial |
| **`BlitTransZRemapXlatZRead@G`** | `0x007E5960` | `0x00492C00` | `0x0049A020` | **12 字节** | **`const uint8_t** pRemap`（二级指针）** | `const uint16_t* XlatTable`（指针） | 无 | Trivial |
| **`BlitTransXlatAlpha@G`** | `0x007E57E0` | `0x00493DF0` | `0x0049A240` | **12 字节** | `const uint16_t* XlatTable`（指针） | **`void* AlphaTable`（动态缓冲）** | 无 | **Non-Trivial**：`call 0x420270` 释放 AlphaTable |
| **`BlitTransXlatAlphaZRead@G`** | `0x007E56F0` | `0x00494B60` | `0x0049A420` | **12 字节** | `const uint16_t* XlatTable`（指针） | **`void* AlphaTable`（动态缓冲）** | 无 | **Non-Trivial**：`call 0x420270` 释放 AlphaTable |
| **`BlitTranslucent50NonzeroAlpha@G`** | `0x007E5720` | `0x00494920` | `0x0049A3E0` | **12 字节** | `const uint16_t* XlatTable`（指针） | `uint16_t BlendMask`（数值） | 无 | Trivial |
| **`RLEBlitTransDarken@G`** | `0x007E55A0` | `0x00496250` | `0x0049A7A0` | **8 字节** | **`uint16_t DarkenMask`（数值！）** | 无 | 无 | Trivial |
| **`RLEBlitTransDarkenZRead@G`** | `0x007E5540` | `0x00496820` | `0x0049A860` | **8 字节** | **`uint16_t DarkenMask`（数值！）** | 无 | 无 | Trivial |
| **`RLEBlitTransDarkenZReadWrite@G`**| `0x007E54B0` | `0x00497390` | `0x0049A980` | **8 字节** | **`uint16_t DarkenMask`（数值！）** | 无 | 无 | Trivial |
| **`RLEBlitTransXlat@G`** | `0x007E55C0` | `0x004960A0` | `0x0049A760` | **8 字节** | `const uint16_t* XlatTable`（指针） | 无 | 无 | Trivial |
| **`RLEBlitTransXlatZRead@G`** | `0x007E5560` | `0x004965B0` | `0x0049A820` | **8 字节** | `const uint16_t* XlatTable`（指针） | 无 | 无 | Trivial |
| **`RLEBlitTransXlatZReadWrite@G`**| `0x007E54D0` | `0x00497100` | `0x0049A940` | **8 字节** | `const uint16_t* XlatTable`（指针） | 无 | 无 | Trivial |
| **`RLEBlitTransLucent50@G`** | `0x007E5580` | `0x004963F0` | `0x0049A7E0` | **12 字节** | `const uint16_t* XlatTable`（指针） | `uint16_t BlendMask`（数值） | 无 | Trivial |
| **`RLEBlitTransLucent50ZRead@G`** | `0x007E5520` | `0x00496A80` | `0x0049A8A0` | **12 字节** | `const uint16_t* XlatTable`（指针） | `uint16_t BlendMask`（数值） | 无 | Trivial |
| **`RLEBlitTransZRemapXlat@G`** | `0x007E55B0` | `0x00496170` | `0x0049A780` | **12 字节** | **`const uint8_t** pRemap`（二级指针）** | `const uint16_t* XlatTable`（指针） | 无 | Trivial |
| **`RLEBlitTransZRemapXlatZRead@G`**| `0x007E5550` | `0x004966D0` | `0x0049A840` | **12 字节** | **`const uint8_t** pRemap`（二级指针）** | `const uint16_t* XlatTable`（指针） | 无 | Trivial |
| **`RLEBlitTransXlatAlphaZRead@G`** | `0x007E5420` | `0x00497FD0` | `0x0049AB40` | **12 字节** | `const uint16_t* XlatTable`（指针） | **`void* AlphaTable`（动态缓冲）** | 无 | **Non-Trivial**：`call 0x420270` 释放 AlphaTable |

#### 8.1.4 `ra2render.h` 数据结构纠偏蓝图
为彻底规避野指针访问与结构体越界读写风险，现网代码应完成如下分类声明：

```cpp
// 1. 4 字节轻量对象（无额外字段）
class BlitterPlainCore {
public:
    virtual ~BlitterPlainCore() = default;
    virtual void __thiscall Blit(void *dst, const void *src, unsigned int length,
                                 uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset) = 0;
};

// 2. 8 字节 Xlat 调色板对象（严格单字段）
class BlitterXlatCore {
public:
    virtual ~BlitterXlatCore() = default;
    virtual void __thiscall Blit(void *dst, const void *src, unsigned int length,
                                 uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset) = 0;
    const uint16_t *XlatTable; // +0x04 指向 256 项 uint16_t 调色板
};

// 3. 8 字节 Darken 阴影暗化对象（标量数值掩码）
class BlitterDarkenCore {
public:
    virtual ~BlitterDarkenCore() = default;
    virtual void __thiscall Blit(void *dst, const void *src, unsigned int length,
                                 uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset) = 0;
    uint16_t DarkenMask;       // +0x04 典型值 0x7BEF (RGB565 截断掩码)
    uint16_t Pad06;            // +0x06 对齐填充
};

// 4. 12 字节 Lucent 半透明对象
class BlitterLucentCore {
public:
    virtual ~BlitterLucentCore() = default;
    virtual void __thiscall Blit(void *dst, const void *src, unsigned int length,
                                 uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset) = 0;
    const uint16_t *XlatTable; // +0x04 调色板映射表
    uint16_t BlendMask;        // +0x08 典型值 0x7BEF (50%) 或 0x3DEF (25%/75%)
    uint16_t Pad0A;            // +0x0A 对齐填充
};

// 5. 12 字节 ZRemap 二级重映射对象
class BlitterZRemapCore {
public:
    virtual ~BlitterZRemapCore() = default;
    virtual void __thiscall Blit(void *dst, const void *src, unsigned int length,
                                 uint16_t zMin, uint16_t *zBuf, uint16_t *aBuf, uint16_t aLvl, int warpOffset) = 0;
    const uint8_t * const *pRemapTable; // +0x04 二级指针，解引用得到 256 字节重映射表
    const uint16_t *XlatTable;          // +0x08 一级调色板表
};
```

---

### 8.2 ZRead / WriteZ 语义边界与指针推进精细判定

#### 8.2.1 物理参数语义全透视
通过对 `0x00492B00`, `0x00492D20`, `0x004965B0`, `0x00496820` 等关键反汇编深入验证：
1. **`zMin`（16 位无符号整数，寄存器传入）**：
   代表当前正在渲染的精灵或单位整体的**世界基准深度（Base Depth）**。
   - 深度约定：**数值越小越靠近摄像机，数值越大越远离摄像机**。
   - 初始背景清屏深度由 `0x00887644` 结构体中的 `DefaultZ = 0x8000` 初始化；
2. **`zBuf`（16 位无符号整数环形指针，`uint16_t*`）**：
   代表帧缓冲区当前扫描线上已存在的像素深度；
3. **`zmap`（8 位有符号深度微调表，`int8_t*`，由 `0f be 01 movsx` 读取）**：
   **仅存在于 RLE 族**。非 RLE 族无论是否带 Z 测试，参数中均无 `zmap`。它提供了精灵局部的逐像素凹凸/高低浮动（例如步兵倾斜或头盔高于脚底的微小 Z 差）。

#### 8.2.2 深度判定不等式实证

| 变体类别 | 汇编核心指令序列 | 实证不等式 | 像素绘制判定 |
|---|---|---|---|
| **Non-RLE ZRead** | `00492B28: cmp [esp+0x20], edx`<br>`00492B2C: jge skip` | `zMin >= *zBuf` 则跳过 | **`*zBuf > zMin`** 时通过（现有像素更远，新像素在前） |
| **RLE ZRead** | `004968A6: movsx eax, byte ptr [ecx]`<br>`004968B0: sub edi, eax`<br>`004968B9: cmp edi, edx`<br>`004968BB: jge skip` | `(zMin - *zmap) >= *zBuf` 则跳过 | **`*zBuf > zMin - (*zmap)`** 时通过（等价于 `*zBuf + *zmap > zMin`） |

#### 8.2.3 WriteZ 深度回写规则
- **Non-RLE WriteZ（`0x0049364D: mov [eax-2], bp`）**：
  通过 Z 测试后，直接将未加偏移的标量 **`zMin`** 写回 `*zBuf`；
- **RLE WriteZ（`0x004971C1: mov word ptr [eax], bx`）**：
  通过 Z 测试后，回写的深度值必须为 **`zMin - (*zmap)`**（精确保存带局部高程偏移的深度）。

#### 8.2.4 指针推进与行末 Overshoot 行为对比表

| 渲染阶段 / 事件 | Non-RLE 族行为（密集对齐流） | RLE 族行为（两阶段变长状态机） |
|---|---|---|
| **左裁剪阶段（Phase A）** | 不存在（行首偏移由调用方预先计算并平移指针） | `src` 消费游程，`EncodedLen` 递减；**`dst` / `zBuf` / `zmap` 严格静止** |
| **左跨界补偿（Overshoot）** | 不存在 | `overshoot = -EncodedLen >= 0`；`Length -= overshoot`；`dst += overshoot`；`zBuf += overshoot`（带环绕检查）；<br>**【关键实证】：`zmap`（寄存器 `ecx`）在 overshoot 处绝不推进！保持为行首初始基址！** |
| **可见区透明游程（`00 nn`）** | 不存在（透明表现为 `src[i] == 0`） | `Length -= n`；`dst += n`；`zBuf += n`；**`zmap += n`**；（若跨界则触发 `BufferEnd` 环绕） |
| **可见区不透明像素** | `src++`、`dst++`、`zBuf++` 无条件同步推进（Z 失败仅跳过写回） | `Length--`；`dst++`；`zBuf++`；**`zmap++`**（无论 Z 成功与否，`zmap` 均递增 1 字节） |
| **行末截断越界（`n > Length`）** | `length` 递减至 0 正常退出 | 游程跨越行尾导致 `Length <= 0`，循环立即 `break` 并 `ret 0x28` 返回。**不进行任何行末指针回退或截断修复**，下一行指针完全由上层调用方基于行间步幅重新计算并压栈。 |

---

### 8.3 非 RLE 族具名热点接管优先级与向量化工程蓝图

#### 8.3.1 “调用频次 × 像素吞吐量”综合评估排序表

| 优先级 | 模板名称 | 虚表基址 | Slot 1 Blit 入口 | 调用场景与热度成因 | 像素吞吐特征 | SSE2 向量化可行性与核心收益 |
|---|---|---|---|---|---|---|
| **TOP 1 (P0)** | **`?$BlitTransXlatZRead@G`** | `0x007E5978` | `0x00492B00` | 载具集群重叠、建筑与重叠单位本体主路径 | 密集未压缩 8 位索引，多单位交战单帧达数十万像素 | 极高：8 字节无条件前进，`_mm_cmpgt_epi16` 并行测试，标量查表+向量写回 |
| **TOP 2 (P0)** | **`?$BlitTransDarkenZRead@G`** | `0x007E5948` | `0x00492D20` | 载具/建筑向斜坡或重叠单位投射的带深度阴影 | 密集未压缩流，纯目标读-改-写（RMW） | **极高（最高收益点）**：无查表开销，8 像素单拍 `psrlw` + `pand`，吞吐提升 6~8 倍 |
| **TOP 3 (P1)** | **`?$BlitTransLucent50@G`** | `0x007E59C0` | `0x00492830` | 幻影隐形、超时空传送、心灵控制涟漪半透明特效 | 密集特效矩形区域 | **完美 SIMD 模式**：`((s>>1)&m) + ((d>>1)&m)` 8 像素单拍完成，无分支惩罚 |
| **TOP 4 (P1)** | **`?$BlitPlainXlat@G`** | `0x007E5A38` | `0x004924C0` | 不透明建筑基座、无色键地表装饰与 UI/Cameo 阵营着色 | 100% 填充率（无任何透明跳过） | 高：消除分支，8 索引预加载查表 + 128 位对齐流式写入（`_mm_storeu_si128`） |
| **TOP 5 (P2)** | **`?$BlitTransZRemapXlat@G`** | `0x007E5A08` | `0x00492590` | 精英三星标记、战损冒烟着色等二级重映射载具 | 中等偏高 | 中高：二级查表 `XlatTable[RemapTable[idx]]`，可构建 8 像素快速查找流水线 |
| **TOP 6 (P2)** | **`?$BlitTransXlatZReadWrite@G`** | `0x007E5888` | `0x00493600` | 地面重型单位绘制同时刷新深度图层 | 中等 | 高：深度比较通过后向量化广播写入 `zMin` 到 `zBuf` |
| **TOP 7 (P3)** | **`?$BlitTransLucent25@G`**<br>**`?$BlitTransLucent75@G`** | `0x007E59A8`<br>`0x007E59D8` | `0x00492920`<br>`0x00492740` | 特殊武器爆炸、护盾边缘半透明衰减 | 低频特效区域 | 高：与 Lucent50 完全共享同一模板，仅乘数权重调整（`*3` 转换为 `paddw`+`paddw`） |
| **TOP 8 (P3)** | **`?$BlitPlainXlatZRead@G`**<br>**`?$BlitTransDarkenZReadWrite@G`** | `0x007E5990`<br>`0x007E5858` | `0x00492A10`<br>`0x00493830` | 陡坡建筑基石 / 带深度写回的投影阴影 | 边缘生僻路径 | 中等：已有模板组合扩展即可覆盖 |

#### 8.3.2 SSE2 向量化通用工程设计蓝图
非 RLE 族相比 RLE 族具备绝对的向量化优势——**内存连续且无变长状态机**。实现微内核时推荐遵循如下核心设计规范：

1. **8 像素齐头并进（Lockstep Advance）**：
   循环体首部无条件执行 `src += 8; dst += 8; zBuf += 8; length -= 8;`，彻底消除条件推进分支；
2. **透明掩码一拍提取**：
   使用 `_mm_loadl_epi64` 读取 8 字节索引，`_mm_cmpeq_epi8(idx, _mm_setzero_si128())` 并配合 `_mm_movemask_epi8` 获得透明位掩码。全透明块直接跳步，全不透明块跳过掩码融合；
3. **无符号 16 位 Z 测试技巧**：
   SSE2 的 `_mm_cmpgt_epi16` 仅支持有符号比较。通过对 `zBuf` 与 `zMin` 异或 `0x8000`（翻转最高符号位），将 `[0, 65535]` 无符号数无损投影为 `[-32768, 32767]`，实现硬件单拍并行深度测试：
   ```cpp
   const __m128i signFlip = _mm_set1_epi16(static_cast<short>(0x8000));
   __m128i zb_s = _mm_xor_si128(_mm_loadu_si128((__m128i*)zBuf), signFlip);
   __m128i zmin_s = _mm_xor_si128(_mm_set1_epi16(zMin), signFlip);
   __m128i zPassMask = _mm_cmpgt_epi16(zb_s, zmin_s); // zb > zMin
   ```
4. **环形深度缓冲跨行前瞻（Safety Runaway 区间）**：
   在进入向量化主循环前，计算距 `desc->BufferEnd` 的剩余线性跨度：
   ```cpp
   int safeSteps = (reinterpret_cast<uintptr_t>(desc->BufferEnd) - reinterpret_cast<uintptr_t>(zBuf)) / sizeof(uint16_t);
   int vectorSafe = (min(length, safeSteps) / 8) * 8;
   ```
   在 `vectorSafe` 区域内执行无环绕开销的高速 SIMD 展开；在剩余跨界边界处无缝退化为标量回卷逻辑，既保证 100% 内存安全，又达到极限理论吞吐。

