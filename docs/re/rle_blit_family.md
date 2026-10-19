# RLE Blit 族逆向档案（gamemd.exe 1.001）

> 目标：把 RLE 压缩 Blitter 族逆向清楚，供 ra2render.dll 补全 SSE2 Hook。
> 产出范围：调用约定 / RLE 码流语义 / 各变体像素算法 / SSE2 改造要点 / 建议 Hook 地址表。
> 依据：`out/reverse/m1_blit_targets.txt`、`out/reverse/symbols.json`、`ra2youli/gamemd.exe` 反汇编（capstone）、`YRpp/Blitters/` 社区 ABI 对照、`ra2render/ra2render.h` 与 `blitter_hooks.cpp` 现有 Hook。
> PE 事实：ImageBase=0x400000，.text VA=0x1000 raw=0x1000，文件偏移 ≈ RVA（无重定位），下文地址均为 VA。

---

## 1. 摘要

RLEBlitter 共 51 个具体实现（`RLEBlitter` 基类 vtable = `0x007E5BA0`，虚函数 3 个）：

| 子集 | 数量 | 说明 |
|---|---|---|
| `RLEBlit*@G` | **39** | 16 位 RGB565（本文档主对象） |
| `RLEBlit*@E` | 12 | 8 位调色板（结构同构，写 1 字节，优先级最低） |

每个 RLE 类只有 **3 个虚函数槽**（对比非 RLE Blitter 的 5 个）：

| 槽位 | 偏移 | 含义 |
|---|---|---|
| 0 | `vtable+0` | 析构（`0x0049A7xx` / `0x00499Dxx` 段） |
| 1 | `vtable+4` | **Blit**（真正做事的入口，Hook 只需打这里） |
| 2 | `vtable+8` | CallBlit0（薄包装，内部 `call [vtable+4]` 转发给 Blit） |

**关键结论一：只需 Hook 槽 1。** CallBlit0 的实现是把 10 个参数重新压栈后 `call dword ptr [eax+4]`（eax = vtable），走的是虚表间接调用，打完槽 1 后 CallBlit0 自动落到新实现，不必单独 Hook。这与现有 `Hook_RLEBlitTransXlat_G` 的做法（`PatchVTablePointer(ADDR_VTABLE + 4, ...)`）一致。

**关键结论二：RLE 码流是「透明游程 + 逐像素不透明」格式**，没有不透明 run——每个不透明像素就是 1 个索引字节。因此解码循环本质上是标量的；SSE2 的收益在**像素写入/混合阶段**（尤其 Darken 阴影），而不是解码阶段。透明 run 的跳过本身就是 O(1) 指针加法，不需要 SIMD。

**关键结论三：39 个 @G 实现的像素算法是 5 个「正交特性」的组合**，掌握 5 个原语即可推导全部：

| 原语 | 写入公式（RGB565） | 成员布局 |
|---|---|---|
| **Xlat** | `*dst = XlatTable[idx]` | `this+0x04` = `uint16_t* XlatTable` |
| **Darken** | `*dst = (*dst >> 1) & DarkenMask` | `this+0x04` = `uint16_t DarkenMask`（是**值**不是指针） |
| **Lucent25/50/75** | 见 §4.3 | `this+0x04` = `XlatTable`，`this+0x08` = `uint16_t BlendMask` |
| **ZRemapXlat** | `*dst = XlatTable[ RemapTable[idx] ]` | `this+0x04` → 双重解引用得 `uint8_t* RemapTable`，`this+0x08` = `XlatTable` |
| **ZRead / ZReadWrite** | 测试 `zBuf[i] > zMin - zmap[i]`；ReadWrite 再回写 `zBuf[i] = zMin - zmap[i]` | 全走参数，不走 this |
| **Alpha** | `*dst = XlatTable[ AlphaRow[aBuf[i]] \| idx ]` | `this+0x04` = `XlatTable`，`this+0x08` = Alpha 表基址 |
| **Warp** | 背景像素从 `dst[warpOffset]` 采样（扭曲） | 全走参数 |

**热路径判断**：loadbench 显示步兵 RLE 是真热点。
> **【勘误 2026-09-28 · MIMO-H1VOID + Lead】上一句的「loadbench 显示…是真热点」所依据的采样，其基准图真机只实例化 21/22 单位（`RespawnStartingForces` 默认开局部队，非地图负载）⇒ 已判作废、`[待 H1 重测]`（见 `out/loadbench/H1_REMEASURE_RUNBOOK.md §0`）。**
> **保留原句不删字**；但**实施优先级不得再以「真热点」措辞为依据**，应以下文的**像素语义**（步兵一帧走 Xlat+Darken，重叠再叠 ZRead 两层）与 `docs/re/blit_coverage_top10.md` 的语义/结构排序为准。步兵一帧同时走 **Xlat@G（本体/阵营色）+ Darken@G（影子）**，单位重叠时再叠一层 **XlatZRead@G / DarkenZRead@G**。这 4 个是第一批必做；Lucent 族（超时空/心灵突击队半透明）次之；Alpha / Warp / ZReadWrite 属特效路径，最后做。

**与现有 Hook 的关系**：`Hook_RLEBlitTransXlat_G` 目前是「遥测 + 原样转发」，**没有实现任何像素逻辑**，因此不存在算法差异需要对齐；但其声明的签名 `uint8_t Length` 有误（汇编里 Length 是完整 32 位计数），且 `EncodedLen` 命名误导（实为「跳过像素数」）。补全实现时必须先修正签名，见 §3.1 与 §5。

---

## 2. 优先级表

排序依据：步兵绘制频率 × 实现可复用性 × SSE2 收益。

| 优先级 | 模板名 | vtable | Blit 入口 | 语义 | 理由 |
|---|---|---|---|---|---|
| **P0** | `?$RLEBlitTransXlat@G` | `0x007E55C0` | `0x004960A0` | 透明跳过 + Xlat（阵营色） | 步兵本体主路径；已 Hook（仅转发），改造基准 |
| **P0** | `?$RLEBlitTransDarken@G` | `0x007E55A0` | `0x00496250` | 透明跳过 + 变暗（影子） | 每个步兵一帧必画影子；纯 dst RMW，SSE2 收益最大 |
| **P1** | `?$RLEBlitTransXlatZRead@G` | `0x007E5560` | `0x004965B0` | Xlat + 读深度 | 单位重叠时的主路径 |
| **P1** | `?$RLEBlitTransDarkenZRead@G` | `0x007E5540` | `0x00496820` | Darken + 读深度 | 重叠影子 |
| **P2** | `?$RLEBlitTransLucent50@G` | `0x007E5580` | `0x004963F0` | 50% 半透明 | 超时空/心灵类特效；Lucent 族代表 |
| **P2** | `?$RLEBlitTransZRemapXlat@G` | `0x007E55B0` | `0x00496170` | 深度重映射 + Xlat | 结构与 Xlat 略异（双查表） |
| **P3** | `?$RLEBlitTransLucent25@G` | `0x007E5570` | `0x004964D0` | 25% 半透明 | 与 50/75 共享模板，参数化即可 |
| **P3** | `?$RLEBlitTransLucent75@G` | `0x007E5590` | `0x00496310` | 75% 半透明 | 同上 |
| **P4** | `?$RLEBlitTransXlatZReadWrite@G` | `0x007E54D0` | `0x00497100` | Xlat + 读写深度 | Z 回写逻辑单独确认过 |
| **P4** | `?$RLEBlitTransDarkenZReadWrite@G` | `0x007E54B0` | `0x00497390` | Darken + 读写深度 | 同上 |
| **P5** | 其余 Lucent*ZRead* / ZReadWarp | 见 §6 | — | 半透明 + 深度 / 扭曲 | 矩阵化派生 |
| **P6** | `*Alpha*` 全族（10 个） | 见 §6 | — | alpha 混合 | 特效路径，需先补析 Alpha 表结构 |
| **P7** | `RLEBlit*@E` 全族（12 个） | 见 §6 | — | 8 位调色板 | 结构同构，写 1 字节；仅当要统一 8 位路径时做 |

> 说明：任务描述里「约 51 个 RLE* 16-bit」实为 **51 个 RLE 总数 = 39 个 @G（16 位）+ 12 个 @E（8 位）**，已在 §1 更正。

---

## 3. 通用约定（全族共享）

### 3.1 调用约定与参数布局

`__thiscall`：`ecx` = this，栈参数 `ret 0x28`（**10 个 DWORD**）。`CallBlit0` 是 `ret 0x2c`（11 个 DWORD，多一个 `useless`，内部转发前 10 个给 Blit）。

```
Blit(
    void*    dst,          // [esp+0x04] arg1  目标像素指针（uint16_t*）
    uint8_t* src,          // [esp+0x08] arg2  RLE 码流
    int      Length,       // [esp+0x0C] arg3  本次要画的像素数（完整 32 位！）
    int      EncodedLen,   // [esp+0x10] arg4  码流开头要跳过的像素数（左裁剪）
    uint16_t zMin,         // [esp+0x14] arg5  本精灵 Z 值
    uint16_t* zBuf,        // [esp+0x18] arg6  深度缓冲（可能环绕）
    uint16_t* aBuf,        // [esp+0x1C] arg7  alpha 缓冲（Alpha 变体用）
    int      aLvl,         // [esp+0x20] arg8  alpha 等级（Alpha 变体用）
    int      warpOffset,   // [esp+0x24] arg9  扭曲偏移（Warp 变体用，像素）
    int8_t*  zmap          // [esp+0x28] arg10 逐像素 Z 偏移（Z* 变体用）
)
```

与 `ra2render.h` 中 `RLEBlitterCore::Blit` 签名对照：

| 现有声明 | 实际 | 问题 |
|---|---|---|
| `void *dst` | `void *dst` | ✅ |
| `uint8_t *src` | `uint8_t *src` | ✅ |
| `uint8_t Length` | `int Length` | ❌ **类型错误**。汇编 `test edi,edi` / `sub edi,edx` 全程 32 位；若 SHP 行宽或裁剪跨度 > 255 会截断 |
| `int EncodedLen` | `int EncodedLen`（语义 = 跳过像素数） | ⚠️ 类型对，**命名误导**。不是「编码长度」，是「左裁剪要跳过的像素数」（RLE 不可按下标寻址，必须解码跳过） |
| `int a6..a11` | zMin / zBuf / aBuf / aLvl / warpOffset / zmap | ⚠️ 未命名，按上表补全 |

`FnRLEBlitTransXlat` typedef 与 `Hook_RLEBlitTransXlat_G` 形参同样带 `uint8_t Length`，补全实现时应一并改成 `int`。

### 3.2 RLE 码流格式（全族一致）

解码循环在 39 个 @G 实现里逐字节同构（见 §4.1 汇编），格式为：

```
while (像素预算 > 0) {
    c = *src++;
    if (c == 0) {                  // 透明游程
        n = *src++;                // 游程长度 0..255
        跳过 n 像素（dst/zBuf/zmap 各自前进 n）；
        预算 -= n;
    } else {                       // 不透明单像素
        用 c 作为索引写 1 像素；
        预算 -= 1;
    }
}
```

要点：

1. **没有不透明 run**。连续不透明像素 = 连续非零字节，每字节一个像素。这是 SSE2 改造最重要的约束（见 §5）。
2. 透明游程长度是 **1 字节（0..255）**，长透明区需要多个 `00 nn` 串接。
3. `c == 0 && n == 0` 是合法的空游程（消耗 2 字节、0 像素）——不要当成结束符。
4. 码流末尾不保证有哨兵，循环以像素预算耗尽为终点。

### 3.3 两阶段结构（左裁剪 + 绘制）

所有实现都是两段：

```
// 阶段 A：解码跳过 EncodedLen 像素（左裁剪）
while (EncodedLen > 0) { 按 §3.2 解码，只推进 src，不动 dst }
// 越界修正：透明游程跨过裁剪边界时会「多跳」
overshoot = -EncodedLen;            // 阶段 A 结束时 EncodedLen <= 0
Length   -= overshoot;              // 多跳的透明像素计入已画
dst      += overshoot;              // dst 相应前进（透明不写像素）
// Z* 变体：zBuf += overshoot，并做环绕检查
// 注意：zmap 在 overshoot 处【不】推进——这是原版实测行为，见 §8.3

// 阶段 B：画 Length 像素
while (Length > 0) { 按 §3.2 解码并写像素 }
```

`overshoot` 只可能来自**跨边界的透明游程**（不透明路径每次只减 1，不会越过边界）。多跳的那部分是透明像素，落在可见区内，所以 `dst` 要前进、`Length` 要扣减，但不写任何像素。**改造 SSE2 时必须逐位保持这段语义**，否则行首会出现 1~255 像素的整体错位。

### 3.4 对象布局（this）

不同变体的 `this` 成员不同，**不能用一个结构体通吃**（现有 `RLEBlitterCore` 只声明了 `XlatTable`，对 Darken/ZRemap/Alpha 是错的）：

| 变体 | `this+0x04` | `this+0x08` |
|---|---|---|
| Xlat / Lucent* | `uint16_t* XlatTable` | （Lucent）`uint16_t BlendMask` |
| Darken* | `uint16_t DarkenMask`（**值**，典型 `0x7BEF`） | — |
| ZRemapXlat* | `void*` → 解 1 次得 `uint8_t* RemapTable`（256 字节） | `uint16_t* XlatTable` |
| *Alpha* | `uint16_t* XlatTable` | Alpha 表基址（按 `aLvl` 选 512 字节行） |
| `RLEBlit*@E` Xlat | `uint8_t* XlatTable`（查表得 1 字节） | — |

### 3.5 深度缓冲环绕（Z* 变体共用）

全局 `*(void**)0x00887644` 是 Z 缓冲描述符（与 YRpp `Drawing::ZBuffer` 一致）：

| 字段 | 偏移 | 含义 |
|---|---|---|
| `BufferEnd` | `+0x1C` | 缓冲区末端指针 |
| `BufferSize` | `+0x20` | 环绕步长（字节） |

每前进一次 `zBuf`（含阶段 A 的 overshoot、阶段 B 的每个像素/游程）都要：

```c
if (zBuf >= ZBuffer->BufferEnd) zBuf -= ZBuffer->BufferSize;
```

Alpha 变体对 `aBuf` 用同布局的另一描述符 `*(void**)0x0087E8A4`，同样的 `+0x1C/+0x20` 环绕规则。

### 3.6 Z 测试与回写

```
// ZRead / ZReadWrite 共用测试（zmap[i] 是 int8_t，符号扩展）
if ((uint16_t)(zMin - zmap[i]) < zBuf[i])   // 汇编：cmp/jge 跳过
    写像素;

// ZReadWrite 额外：写像素成功后
zBuf[i] = (uint16_t)(zMin - zmap[i]);        // 深度回写
```

注意三点：

1. 测试是 **`zBuf[i] > zMin - zmap[i]`**（z 越大越靠前），与 YRpp `BlitTransXlatZRead` 的 `zVal > zMin` 同向，只是多了 `zmap` 偏移。
2. `zmap[i]` 是 **signed char**（`movsx`），负值会让测试阈值升高。
3. `zMin - zmap[i]` 的结果以 `uint16_t` 截断后比较/回写。

---

## 4. 重点函数汇编要点与算法

以下 8 个虚函数入口是第一批要反透的（地址取自 `m1_blit_targets.txt`）。反汇编文本留存于 `out/re_work/disasm_*.txt`。

### 4.1 `?$RLEBlitTransXlat@G::Blit` @ `0x004960A0`（P0，基准）

55 条指令，`ret 0x28`。寄存器约定：`ebp=this`，`eax=dst`，`esi=src`，`edi=Length`，`edx=EncodedLen`。

```
; ---- 阶段 A：跳过 EncodedLen 像素 ----
004960A0  mov edx, [esp+0x10]        ; EncodedLen
004960A4  mov eax, [esp+0x04]        ; dst
004960AA  mov esi, [esp+0x08]        ; src
004960B1  mov ebp, ecx               ; this
004960B3  jle  阶段B                  ; EncodedLen <= 0 直接画
004960B5  mov cl, [esi] / inc esi    ; c = *src++
004960B8  test cl, cl
004960BA  jne  004960C5              ; 非零 → 不透明单像素
004960BC  xor ecx,ecx / mov cl,[esi] ; 透明游程 n
004960C0  sub edx, ecx / inc esi     ; EncodedLen -= n
004960C3  jmp  004960C6
004960C5  dec edx                    ; 不透明：EncodedLen -= 1
004960C6  test edx,edx / jg 004960B5 ; 循环
; ---- overshoot 修正 ----
004960CA  mov edi, [esp+0x18]        ; Length
004960CE  neg edx                    ; overshoot = -EncodedLen
004960D0  sub edi, edx               ; Length -= overshoot
004960D2  lea eax, [eax+edx*2]       ; dst += overshoot（16 位步进）
; ---- 阶段 B：画 Length 像素 ----
004960DF  mov dl, [esi] / inc esi    ; c = *src++
004960E4  mov [esp+0x18], dl         ; 暂存 c（复用 Length 槽）
004960E8  jne  00496102              ; 非零 → 不透明
004960EA  mov dl, [esi] / inc esi    ; 透明游程 n
004960FB  sub edi, edx               ; Length -= n
004960FD  lea eax, [eax+edx*2]       ; dst += n
00496100  jmp  0049611B
00496102  mov ecx, [esp+0x18]        ; idx = c
00496106  mov edx, [ebp+0x04]        ; XlatTable
00496109  and ecx, 0xFF
0049610F  add eax, 2 / dec edi
00496113  mov cx, [edx+ecx*2]        ; px = XlatTable[idx]
00496117  mov [eax-2], cx            ; *dst = px
```

**伪代码（可直接照抄为 C）**：

```c
void RLEBlitTransXlat_G(this, dst, src, Length, EncodedLen) {
    uint16_t *d = dst; const uint8_t *s = src;
    const uint16_t *xlat = this->XlatTable;
    while (EncodedLen > 0) {                 // 阶段 A
        uint8_t c = *s++;
        if (c == 0) EncodedLen -= *s++;
        else        EncodedLen -= 1;
    }
    int over = -EncodedLen;                  // >= 0
    Length -= over; d += over;
    while (Length > 0) {                     // 阶段 B
        uint8_t c = *s++;
        if (c == 0) { int n = *s++; Length -= n; d += n; }
        else        { *d++ = xlat[c]; Length--; }
    }
}
```

**与已 Hook 的 `Hook_RLEBlitTransXlat_G` 的差异**（见 `ra2render/blitter_hooks.cpp:212`）：

| 维度 | 原版 `0x004960A0` | 现有 Hook |
|---|---|---|
| 像素逻辑 | 完整两阶段 RLE 解码 + Xlat 写入 | **完全没有**，只 `totalBlitCalls++` 后原样转发 |
| `Length` 类型 | 32 位计数 | 形参 `uint8_t`（错误，会截断） |
| `EncodedLen` 语义 | 左裁剪跳过像素数 | 未使用，命名误导 |
| zMin/zBuf/aBuf/aLvl/warpOffset/zmap | 本变体全忽略（都是安全的） | 全部原样转发 |
| 成员访问 | `this+0x04` = XlatTable | 通过 `RLEBlitterCore`，碰巧正确 |

因此补全实现时不是「对齐差异」，而是**从零实现**，同时修正签名。

### 4.2 `?$RLEBlitTransXlat@E::Blit` @ `0x00491820`（P7，对照用）

与 @G 逐指令同构，差别只有两处：

- 查表得 **1 字节**：`mov cl, [eax+ecx]`（`this+0x04` = `uint8_t*`）；
- 写 1 字节：`mov [esi-1], cl`，`dst` 步进 1。

overshoot 修正是 `add esi, eax`（1 字节步进）而非 `lea [eax+edx*2]`。用于验证「RLE 格式全族一致」的判断。

### 4.3 `?$RLEBlitTransDarken@G::Blit` @ `0x00496250`（P0，影子）

阶段 A / overshoot 与 §4.1 **逐字节相同**。阶段 B 的不透明路径：

```
004962AE  mov cx, [eax]            ; 读目标像素（不是源像素！）
004962B1  shr cx, 1
004962B4  and cx, [ebp+0x04]       ; & DarkenMask（uint16 值）
004962B8  dec edi
004962B9  mov [eax], cx
004962BC  add eax, 2
```

```c
// 不透明像素：源索引 c 只作「有像素」标志，颜色被完全忽略
*d = (*d >> 1) & this->DarkenMask;   // 典型 mask = 0x7BEF（RGB565）
d++; Length--;
```

**要点**：Darken 是**纯目标 RMW**，源数据只决定「哪些像素要变暗」。这是全族 SSE2 收益最高的一个——影子几乎全是短不透明段 + 长透明段，而变暗本身是完美的 8 像素/拍向量运算。

`?$BlitTransDarken@G`（非 RLE，`0x00492670`）写法相同，可互相印证；YRpp `BlitTransDarken.h` 同义。

### 4.4 Lucent 族（`Lucent25/50/75@G`）

阶段 A 同 §4.1。阶段 B 不透明路径（以 Lucent50 @ `0x004963F0` 为例）：

```
00496453  mov ebx, [esp+0x1C]      ; idx
00496457  mov ebp, [ecx+0x04]      ; XlatTable
0049645A  mov dx,  [ecx+0x08]      ; BlendMask
0049645E  and ebx, 0xFF
00496464  mov bx,  [ebp+ebx*2]     ; s = XlatTable[idx]
00496469  mov bp,  [eax]           ; d = *dst
0049646C  shr bx, 1 / shr bp, 1
00496472  and ebx, edx / and ebp, edx
00496476  add ebx, ebp
00496479  mov [eax], bx
```

三档统一公式（`m` = `this->BlendMask`，RGB565 典型 `0x7BEF`）：

| 变体 | 公式 | 等价透明度 |
|---|---|---|
| Lucent25 | `*dst = 3*((s>>2)&m) + ((d>>2)&m)` | 源 75% / 目标 25% |
| Lucent50 | `*dst = ((s>>1)&m) + ((d>>1)&m)` | 各 50% |
| Lucent75 | `*dst = ((s>>2)&m) + 3*((d>>2)&m)` | 源 25% / 目标 75% |

与 YRpp `BlitTransLucent25.h` 对照一致（`dstval += 3 * tmpval`）。**混合必须用「移位 + 掩码」而不是除法**，否则相邻通道会渗色（RGB565 通道边界）。

### 4.5 `?$RLEBlitTransZRemapXlat@G::Blit` @ `0x00496170`（P2）

阶段 A 同前。阶段 B 不透明路径：

```
00496182  mov ecx, [ebp+0x04]      ; P = this+4
00496187  mov ecx, [ecx]           ; RemapTable = *P（双重解引用）
...
004961E8  mov bl, [edx+ecx]        ; r = RemapTable[idx]   （uint8）
004961EB  mov edx, [ebp+0x08]      ; XlatTable
004961EE  mov dx, [edx+ebx*2]      ; px = XlatTable[r]
004961F2  mov [eax-2], dx
```

```c
*d = this->XlatTable[ this->RemapTable[idx] ];  // RemapTable = **(void**)(this+4)
```

YRpp `BlitTransZRemapXlat.h` 写作 `ExtraData[Data[idx]]`，与本式同构（`ExtraData`=XlatTable，`Data`=RemapTable）。差别是 RLE 版的 RemapTable 是 **256 字节索引表**，不是 16 位表。

### 4.6 `?$RLEBlitTransXlatZRead@G::Blit` @ `0x004965B0`（P1）

84 条指令。相对 §4.1 多了 zmap 推进与 Z 测试。

阶段 A / overshoot 多两步：

```
004965F0  lea edi, [edi+eax*2]     ; dst  += overshoot
004965F3  lea eax, [edx+eax*2]     ; zBuf += overshoot
004965F6  mov edx, [0x887644]
004965FC  cmp eax, [edx+0x1C]      ; 环绕检查
004965FF  jb  ...
00496601  sub eax, [edx+0x20]
; zmap（ecx）在 overshoot 处【不】推进（全族一致）；它只在阶段 B 的
; 不透明路径 inc ecx / 透明路径 add ecx, n。见 §8.3
```

> `zmap` 是 `arg10`（`mov ecx,[esp+0x3c]`，5 次 push 后），逐像素 `inc ecx`，透明游程 `add ecx, n`。

阶段 B 不透明路径：

```
0049663A  movsx eax, [ecx]         ; z = zmap[i]（signed）
0049663D  mov esi, [esp+0x28]      ; zMin
00496641  add edx, 2               ; zBuf++
00496644  sub esi, eax             ; zMin - z
00496648  mov ax, [edx-2]          ; zb = zBuf[i]
0049664C  inc ecx                  ; zmap++
0049664D  cmp esi, eax
0049664F  jge 00496668             ; 不通过：不写像素
00496651  ... Xlat 查表写 *dst ...
00496668  add edi, 2 / dec ebx     ; 通过与否都要推进 dst 与计数
```

**伪代码**：

```c
while (EncodedLen > 0) {                 // 阶段 A：只推进 src，不碰 zmap
    uint8_t c = *s++;
    if (c == 0) EncodedLen -= *s++;
    else        EncodedLen -= 1;
}
int over = -EncodedLen;
Length -= over; d += over; zBuf += over; zbuf_wrap();   // zmap 不动（原版如此）

while (Length > 0) {
    uint8_t c = *s++;
    if (c == 0) {
        int n = *s++;
        Length -= n; d += n; zBuf += n; zmap += n;  zbuf_wrap();
    } else {
        int zoff = *zmap++;                          // signed
        uint16_t thr = (uint16_t)(zMin - zoff);
        uint16_t zb  = *zBuf;  zBuf++; zbuf_wrap();
        if (thr < zb) *d = xlat[c];
        d++; Length--;
    }
}
```

### 4.7 `?$RLEBlitTransDarkenZRead@G::Blit` @ `0x00496820`（P1）

= §4.6 的 Z 测试/推进 + §4.3 的 Darken 写入：

```
004968BD  mov ax, [esi]            ; 读目标
004968C4  shr ax, 1
004968C7  and ax, [edi+0x04]       ; DarkenMask
004968CB  mov [esi], ax
004968CE  dec ebx / add esi, 2     ; 无论是否通过测试都要推进
```

`?$RLEBlitTransXlatZReadWrite@G` @ `0x00497100` 与 `?$RLEBlitTransDarkenZReadWrite@G` @ `0x00497390` 在通过测试后多一条回写：

```
004971C1  mov [eax], bx            ; zBuf[i] = (uint16_t)(zMin - zmap[i])
```

### 4.8 `?$RLEBlitTransLucent50ZReadWarp@G::Blit` @ `0x00496E60`（P5）

在 §4.6 + §4.4 基础上，背景像素从 **`dst[warpOffset]`** 读取（`arg9`，`mov di,[edx+edi*2]`，`edx`=dst）：

```c
uint16_t bg = d[warpOffset];          // 扭曲采样
*d = ((s>>1)&m) + ((bg>>1)&m);
```

### 4.9 `?$RLEBlitTransXlatAlpha@G::Blit` @ `0x004978C0`（P6，结构先记）

100 条指令，最复杂。结构要点（细节留待补析）：

1. `arg8`（aLvl）经 `min(0xFE, (aLvl>0 ? aLvl : 0) * 261 >> 11)` 得到行号，再 `行号 * 512` 选 `this+0x08` Alpha 表中的一行（512 字节 = 256 个 uint16）。
2. 逐像素取 `aBuf[i]`（`arg7`，描述符 `0x0087E8A4` 环绕），`AlphaRow[aBuf[i]]` 得到一个 16 位值。
3. 该值与源索引 `idx` **按位或** 后作为 `XlatTable` 的最终下标：`*dst = XlatTable[ AlphaRow[aBuf[i]] | idx ]`。
4. 即 Alpha 表把「alpha 等级 + 逐像素 alpha」编码进高位，与 8 位颜色索引拼成 16 位查表下标——**没有真正的运行时混色**，是查表式伪 alpha。

> 这一族（10 个 `*Alpha*`）在 Hook 前需要先确认 Alpha 表的构造方式与 `aBuf` 的取值范围，见 §8。

---

## 5. SSE2 改造建议

### 5.1 总原则

1. **解码循环保持标量**。RLE 是变长游程，不透明段是逐像素字节，SIMD 无法并行解码。硬要向量化解码只会增加开销。
2. **向量化只做「像素写入 / 混合」**。这是纯数据并行部分。
3. **透明 run 天然免费**。跳过本身就是指针加法；SSE2 无需介入（Z* 变体要顺带做 zBuf 环绕判断，见 §5.4）。
4. **像素必须与原版逐位一致**。尤其 Lucent 的 `移位+掩码` 不能换成除法；Darken 的 mask 必须用 `this->DarkenMask` 而不是硬编码。

### 5.2 各变体向量化要点

| 变体 | 可 16 字节批处理的部分 | 建议实现 | 预期收益 |
|---|---|---|---|
| **Darken**（最高优先） | 8 像素/拍：`psrlw 1` + `pand mask` + `movdqu` | 先扫一段连续不透明像素（最多 8），`movdqu` 读 dst → 移位掩码 → 回写；透明段纯跳过 | ★★★★★ 影子是纯 dst RMW，无查表 |
| **Xlat** | 写入本身 | 8 个索引标量查表后 `_mm_set_epi16` + `movdqu`，或直接标量 2 字节写 | ★★☆ 查表是瓶颈，收益主要来自减少分支 |
| **Lucent25/50/75** | 混合运算 | 索引标量查表得 8 个 `s`，`movdqu` 读 8 个 `d`，`psrlw/pand/paddw` 一次算完 | ★★★★ 混合是移位+与+加，完美 SIMD |
| **ZRemapXlat** | 同 Xlat | 多一层 256 字节查表；先标量 gather 成 8 个 px 再批量写 | ★★☆ |
| **ZRead / ZReadWrite** | Z 测试 + 写入 | `zmap` 8 字节 `punpcklbw`+`psllw` 符号扩展成 8 个 thr，`pcmpgtw` 与 `zBuf` 比较得 mask，掩码写入 | ★★★★ 测试本身可向量，但要注意每像素的 zBuf 环绕 |
| **Alpha** | — | 先别做，查表下标拼装逻辑复杂 | — |
| **Warp** | 同 Lucent | 背景从 `dst+warpOffset` 读，可与 Lucent 合并模板 | ★★★ |

### 5.3 「哪些 run 可 16 字节跳过」

**结论：没有可 16 字节跳过的 run——但有可 O(1) 跳过的 run。**

- **透明 run（`00 nn`）**：已经是 O(1) 指针加法，无需 SIMD。16 字节批量跳过没有意义（你根本不在读内存）。唯一可做的是 **`nn >= 16` 时免除逐字节判断**，这在标量里就是一次 `dst += n`，已经是最优。
- **不透明段**：格式上没有 run，是连续非零字节。可做的优化是 **前瞻扫描**：一次 `pcmpeqb` 比 16 字节源数据与 0，`pmovmskb` 得到透明位图，据此把 16 字节切成「连续不透明子段」，对每个子段走 §5.2 的向量混合。这样一次读 16 字节源、最多产出 16 像素，把解码分支摊薄。
- **混合16 字节写**：8 个 RGB565 像素 = 16 字节，`movdqu` 正好一拍。这是真正能满载的粒度。

### 5.4 必须与原版像素一致的路径

按「出错就肉眼可见 / 破坏深度排序」排序：

1. **overshoot 修正**（§3.3）：错 1 像素整行错位，最致命。`dst`/`Length`/`zBuf` 三者必须同步调整；Z* 变体的 `zmap` 在此处**故意不动**（见第 9 条）。
2. **Lucent 的 `移位+掩码`**：换成 `/2`、`/4` 会渗色，与原版不一致。
3. **Darken 的 `DarkenMask` 成员**：不能硬编码 `0x7BEF`（8 位或别的位深会不同）。
4. **Z 测试的方向与 `zmap` 符号扩展**：`zBuf[i] > zMin - zmap[i]`，写反会把前后景弄颠倒。
5. **ZBuf 环绕**：漏掉会写到缓冲外。**向量批处理时尤其危险**——一次推进 8 像素可能跨过 `BufferEnd`。安全做法：先算出「本批不会跨越 BufferEnd 的最大长度」，不足 8 就退化为逐像素；或检测跨越时一分为二。
6. **ZReadWrite 的深度回写值**：必须是 `(uint16_t)(zMin - zmap[i])`，不能是 `zBuf[i]` 原值或别的。
7. **`c==0 && n==0` 空游程**：不能当成终止符。
8. **Warp 的 `dst[warpOffset]` 采样**：不能偷懒用 `dst[i]`。
9. **zmap 的推进时机**：阶段 A 完全不碰 zmap，overshoot 也不碰；只有阶段 B 的每个像素/游程推进。若「顺手」在 overshoot 处补 `zmap += overshoot`，会在透明游程跨裁剪边界时与原版差 `zmap` 对齐（阴影深浅错位）。**保持原版行为**。

### 5.5 建议的模板化写法

39 个 @G 可收敛为一个模板 + 5 个策略标签：

```cpp
template<class Blend, bool UseZ, bool WriteZ, bool UseWarp, bool UseRemap>
void RLEBlit_G(This* t, uint16_t* dst, const uint8_t* src,
               int Length, int EncodedLen,
               uint16_t zMin, uint16_t* zBuf,
               int warpOffset, const int8_t* zmap);
// Blend = Xlat | Darken | Lucent25 | Lucent50 | Lucent75
// Xlat  : Blend::op = [&](idx, d) { return xlat[idx]; }
// Darken: Blend::op = [&](idx, d) { return (d>>1)&mask; }   // idx 忽略
```

- `UseZ=false` 时 zBuf/zmap/warp 全部不接触，自动退化为 §4.1。
- `UseWarp=true` 时 Blend 的 `d` 取自 `dst[warpOffset]`。
- `UseRemap=true` 时查表先过 RemapTable。
- 8 位 `@E` 是同一模板换 `uint8_t` 像素类型（12 个实例）。

这样 51 个实现 ≈ 1 个模板 × 有限组合，Hook 层只做「vtable 地址 → 实例化函数指针」的映射表（§6）。

---

## 6. 建议 Hook 地址表

约定：**只 Hook 槽 1（`vtable+4`）**；CallBlit0 走虚表自动跟随。地址取自 `m1_blit_targets.txt` / `symbols.json`，与实测反汇编一致。

### 6.1 第一批（P0–P2，建议本次迭代落地）

| 模板名 | vtable | Hook 位置 | 原 Blit | CallBlit0 | dtor | 建议实现 |
|---|---|---|---|---|---|---|
| `?$RLEBlitTransXlat@G` | `0x007E55C0` | `0x007E55C4` | `0x004960A0` | `0x00496130` | `0x0049A760` | 模板 `Blend=Xlat` |
| `?$RLEBlitTransDarken@G` | `0x007E55A0` | `0x007E55A4` | `0x00496250` | `0x004962D0` | `0x0049A7A0` | 模板 `Blend=Darken` |
| `?$RLEBlitTransXlatZRead@G` | `0x007E5560` | `0x007E5564` | `0x004965B0` | `0x00496690` | `0x0049A820` | `Xlat + UseZ` |
| `?$RLEBlitTransDarkenZRead@G` | `0x007E5540` | `0x007E5544` | `0x00496820` | `0x004968F0` | `0x0049A860` | `Darken + UseZ` |
| `?$RLEBlitTransLucent50@G` | `0x007E5580` | `0x007E5584` | `0x004963F0` | `0x00496490` | `0x0049A7E0` | `Blend=Lucent50` |
| `?$RLEBlitTransZRemapXlat@G` | `0x007E55B0` | `0x007E55B4` | `0x00496170` | `0x00496210` | `0x0049A780` | `Xlat + UseRemap` |

### 6.2 第二批（P3–P4）

| 模板名 | vtable | Hook 位置 | 原 Blit | CallBlit0 | dtor |
|---|---|---|---|---|---|
| `?$RLEBlitTransLucent25@G` | `0x007E5570` | `0x007E5574` | `0x004964D0` | `0x00496570` | `0x0049A800` |
| `?$RLEBlitTransLucent75@G` | `0x007E5590` | `0x007E5594` | `0x00496310` | `0x004963B0` | `0x0049A7C0` |
| `?$RLEBlitTransXlatZReadWrite@G` | `0x007E54D0` | `0x007E54D4` | `0x00497100` | `0x004971F0` | `0x0049A940` |
| `?$RLEBlitTransDarkenZReadWrite@G` | `0x007E54B0` | `0x007E54B4` | `0x00497390` | `0x00497470` | `0x0049A980` |
| `?$RLEBlitTransZRemapXlatZRead@G` | `0x007E5550` | `0x007E5554` | `0x004966D0` | `0x004967E0` | `0x0049A840` |
| `?$RLEBlitTransZRemapXlatZReadWrite@G` | `0x007E54C0` | `0x007E54C4` | `0x00497230` | `0x00497350` | `0x0049A960` |

### 6.3 第三批（P5：Lucent × ZRead / ZReadWarp / ZReadWrite）

| 模板名 | vtable | Hook 位置 | 原 Blit |
|---|---|---|---|
| `?$RLEBlitTransLucent25ZRead@G` | `0x007E5510` | `0x007E5514` | `0x00496BC0` |
| `?$RLEBlitTransLucent50ZRead@G` | `0x007E5520` | `0x007E5524` | `0x00496A80` |
| `?$RLEBlitTransLucent75ZRead@G` | `0x007E5530` | `0x007E5534` | `0x00496930` |
| `?$RLEBlitTransLucent25ZReadWarp@G` | `0x007E54E0` | `0x007E54E4` | `0x00496FB0` |
| `?$RLEBlitTransLucent50ZReadWarp@G` | `0x007E54F0` | `0x007E54F4` | `0x00496E60` |
| `?$RLEBlitTransLucent75ZReadWarp@G` | `0x007E5500` | `0x007E5504` | `0x00496D10` |
| `?$RLEBlitTransLucent25ZReadWrite@G` | `0x007E5480` | `0x007E5484` | `0x00497760` |
| `?$RLEBlitTransLucent50ZReadWrite@G` | `0x007E5490` | `0x007E5494` | `0x00497610` |
| `?$RLEBlitTransLucent75ZReadWrite@G` | `0x007E54A0` | `0x007E54A4` | `0x004974B0` |

### 6.4 第四批（P6：Alpha 族，暂缓）

| 模板名 | vtable | Hook 位置 | 原 Blit |
|---|---|---|---|
| `?$RLEBlitTransXlatAlpha@G` | `0x007E5470` | `0x007E5474` | `0x004978C0` |
| `?$RLEBlitTransZRemapXlatAlpha@G` | `0x007E5460` | `0x007E5464` | `0x00497A10` |
| `?$RLEBlitTransLucent25Alpha@G` | `0x007E5430` | `0x007E5434` | `0x00497E60` |
| `?$RLEBlitTransLucent50Alpha@G` | `0x007E5440` | `0x007E5444` | `0x00497CF0` |
| `?$RLEBlitTransLucent75Alpha@G` | `0x007E5450` | `0x007E5454` | `0x00497B80` |
| `?$RLEBlitTransXlatAlphaZRead@G` | `0x007E5420` | `0x007E5424` | `0x00497FD0` |
| `?$RLEBlitTransZRemapXlatAlphaZRead@G` | `0x007E5410` | `0x007E5414` | `0x004982E0` |
| `?$RLEBlitTransLucent25AlphaZRead@G` | `0x007E53E0` | `0x007E53E4` | `0x004988C0` |
| `?$RLEBlitTransLucent50AlphaZRead@G` | `0x007E53F0` | `0x007E53F4` | `0x004986D0` |
| `?$RLEBlitTransLucent75AlphaZRead@G` | `0x007E5400` | `0x007E5404` | `0x004984D0` |
| `?$RLEBlitTransLucent25AlphaZReadWarp@G` | `0x007E53B0` | `0x007E53B4` | `0x00498ED0` |
| `?$RLEBlitTransLucent50AlphaZReadWarp@G` | `0x007E53C0` | `0x007E53C4` | `0x00498CD0` |
| `?$RLEBlitTransLucent75AlphaZReadWarp@G` | `0x007E53D0` | `0x007E53D4` | `0x00498AC0` |
| `?$RLEBlitTransXlatAlphaZReadWrite@G` | `0x007E53A0` | `0x007E53A4` | `0x004990E0` |
| `?$RLEBlitTransZRemapXlatAlphaZReadWrite@G` | `0x007E5390` | `0x007E5394` | `0x00499430` |
| `?$RLEBlitTransLucent25AlphaZReadWrite@G` | `0x007E5360` | `0x007E5364` | `0x00499A90` |
| `?$RLEBlitTransLucent50AlphaZReadWrite@G` | `0x007E5370` | `0x007E5374` | `0x00499860` |
| `?$RLEBlitTransLucent75AlphaZReadWrite@G` | `0x007E5380` | `0x007E5384` | `0x00499650` |

### 6.5 第五批（P7：8 位 `@E`，12 个）

| 模板名 | vtable | Hook 位置 | 原 Blit |
|---|---|---|---|
| `?$RLEBlitTransXlat@E` | `0x007E5B00` | `0x007E5B04` | `0x00491820` |
| `?$RLEBlitTransXlatZRead@E` | `0x007E5AC0` | `0x007E5AC4` | `0x00491B40` |
| `?$RLEBlitTransXlatZReadWrite@E` | `0x007E5A80` | `0x007E5A84` | `0x00491FD0` |
| `?$RLEBlitTransZRemapXlat@E` | `0x007E5AF0` | `0x007E5AF4` | `0x004918E0` |
| `?$RLEBlitTransZRemapXlatZRead@E` | `0x007E5AB0` | `0x007E5AB4` | `0x00491C50` |
| `?$RLEBlitTransZRemapXlatZReadWrite@E` | `0x007E5A70` | `0x007E5A74` | `0x00492100` |
| `?$RLEBlitTransRemapXlat@E` | `0x007E5AD0` | `0x007E5AD4` | `0x00491A70` |
| `?$RLEBlitTransRemapXlatZRead@E` | `0x007E5A90` | `0x007E5A94` | `0x00491EA0` |
| `?$RLEBlitTransRemapXlatZReadWrite@E` | `0x007E5A50` | `0x007E5A54` | `0x00492370` |
| `?$RLEBlitTransRemapDest@E` | `0x007E5AE0` | `0x007E5AE4` | `0x004919B0` |
| `?$RLEBlitTransRemapDestZRead@E` | `0x007E5AA0` | `0x007E5AA4` | `0x00491D90` |
| `?$RLEBlitTransRemapDestZReadWrite@E` | `0x007E5A60` | `0x007E5A64` | `0x00492250` |

### 6.6 建议的 abi 常量（可直接进 `ra2render.h`）

```cpp
// RLE 16-bit P0/P1
#define ADDR_VTABLE_RLE_XLAT_G          0x007E55C0
#define ADDR_VFUNC_RLE_XLAT_G           0x004960A0
#define ADDR_VTABLE_RLE_DARKEN_G        0x007E55A0
#define ADDR_VFUNC_RLE_DARKEN_G         0x00496250
#define ADDR_VTABLE_RLE_XLAT_ZREAD_G    0x007E5560
#define ADDR_VFUNC_RLE_XLAT_ZREAD_G     0x004965B0
#define ADDR_VTABLE_RLE_DARKEN_ZREAD_G  0x007E5540
#define ADDR_VFUNC_RLE_DARKEN_ZREAD_G   0x00496820
// RLE 16-bit P2
#define ADDR_VTABLE_RLE_LUCENT50_G      0x007E5580
#define ADDR_VFUNC_RLE_LUCENT50_G       0x004963F0
#define ADDR_VTABLE_RLE_ZREMAP_XLAT_G   0x007E55B0
#define ADDR_VFUNC_RLE_ZREMAP_XLAT_G    0x00496170
// 全局
#define ADDR_ZBUFFER_DESC               0x00887644  // +0x1C=BufferEnd, +0x20=BufferSize
#define ADDR_ABUFFER_DESC               0x0087E8A4  // 同布局，Alpha 变体用
```

（`ADDR_VTABLE_RLE_BLIT_TRANS_XLAT_G` / `ADDR_VFUNC_RLE_BLIT_TRANS_XLAT_G` 已存在于 `ra2render.h:15-16`，值分别为 `0x007E55C0` / `0x004960A0`，与本表一致。）

---

## 7. 与现有实现的衔接清单

补全 Hook 时必须先做的三件事：

1. **修正签名**：`RLEBlitterCore::Blit` / `FnRLEBlitTransXlat` / `Hook_RLEBlitTransXlat_G` 的 `uint8_t Length` → `int Length`；把 `a6..a11` 换成 §3.1 的具名参数。
2. **拆分 this 布局**：`RLEBlitterCore` 目前只有 `XlatTable`；Darken（mask 在 +4）、ZRemap（双查表）、Alpha（表在 +8）需要各自的 view 结构，或用 `offsetof` 直读。
3. **Hook 槽位确认**：只打 `vtable+4`。现有 `PatchVTablePointer(ADDR_VTABLE + 4, ...)` 与 CallBlit0 的 `call [eax+4]` 自洽，不需要额外 Hook 槽 2。

---

## 8. 未决问题

1. **Alpha 表构造方式**（§4.9）。`this+0x08` 的 512 字节行是运行时生成还是静态表？`AlphaRow[aBuf[i]] | idx` 中 OR 拼装的位域边界是多少（看起来低 8 位是颜色、高位是 alpha 档位）？需查 Alpha 变体的构造函数（`0x0049AA00` 等 dtor 邻近的 init 路径）才能安全改写。
2. **`aBuf` 的元素宽度**。Alpha 变体里 `mov dx,[eax]` 读 2 字节再当下标，说明 `aBuf` 是 `uint16_t*`；但非 RLE 头文件写的是 `WORD *aBuf`，一致。需确认 `aBuf[i]` 的实际取值范围（是否也被 `aLvl` 归一化）。
3. **zmap 的来源、长度与推进语义**。`arg10` 是逐像素 `int8_t`（`movsx` 读取），Z 非 Read 的变体完全不用它。实测推进规则：**阶段 A 与 overshoot 处均不推进，只在阶段 B 逐像素/逐游程推进**（`inc ecx` / `add ecx,n`）。这意味着 zmap 的下标 0 对应「可见区第一个像素」，而跨裁剪边界的透明游程 overshoot 像素不消耗 zmap 槽——若 zmap 真是逐像素深度面，这里会与 dst 差 `overshoot` 个下标。三种可能：(a) zmap 只在 overshoot 不发生的调用里非平凡；(b) 原版有潜在 off-by-overshoot；(c) zmap 实际是「按不透明像素计数」的稀疏表而透明游程的 `add ecx,n` 是为别的用途。**SSE2 改写必须原样复制该推进规则**，同时把 (a)(b)(c) 澄清列入下一步（可对比非 RLE 的 `BlitTransXlatZRead`：它没有 zmap，测试只是 `zVal > zMin`）。
4. **`EncodedLen` 与 `Length` 的调用方语义**。本文按「左裁剪跳过像素数 / 本次绘制像素数」解读，与汇编自洽；但未反向追到调用点（`Drawing` 层的行扫描循环）确认。建议下一步反 `Draw_Line` / `Blit_Line` 类调用方（可从 `0x004960A0` 的 xref 入手），验证裁剪窗口是否还会做右裁剪（目前看只有左裁剪，右边界靠 `Length` 控制）。
5. **8 位 `@E` 的 RemapDest 族**（`?$RLEBlitTransRemapDest@E` 等 3 个）未反汇编。语义标注是「重映射/目标混合」，可能是 `*dst = RemapTable[*dst]`（对目标做换色），需确认后再决定是否纳入模板。
6. **`RLEBlitter` 基类虚表 `0x007E5BA0` 的 3 个槽**在 `symbols.json` 里指向 `0x00499DA0 / 0x004C9150 / 0x004C9150`（后两个像是纯虚桩）。子类 dtor 都把 vtable 写回 `0x007E5BA0`，符合 MSVC 单继承布局；但需确认没有多态工厂按基类槽调用而绕过子类 vtable 的路径。
7. **`Warp` 的 `warpOffset` 单位**。汇编按 `dst[warpOffset]`（像素索引 ×2）寻址，确认 `arg9` 是像素偏移而非字节偏移；以及负偏移是否可能（超时空扭曲通常带正弦偏移，可能为负）。
8. **8 位 vs 16 位是否共用同一码流**。`@E` 与 `@G` 的解码循环逐字节同构，说明同一 SHP 码流可喂给两者；但 `this` 成员宽度不同（`uint8_t*` vs `uint16_t*`）。若要做统一模板，像素类型参数化即可，但要实测 8 位模式下 XlatTable 是否也是 256 项。
9. **`0x00887644` / `0x0087E8A4` 的类型名**。字段布局与 YRpp `Drawing::ZBuffer` 一致，但未在 `symbols.json` 里找到命名类。建议把它们登记为 `ZBufferDesc` / `ABufferDesc` 并注明字段偏移。

---

## 附录 A：反汇编工作产物

中间产物（只读参考，不在交付范围）：

| 文件 | 内容 |
|---|---|
| `out/re_work/disasm_rle.py` / `disasm_rle2.py` | capstone 反汇编脚本 |
| `out/re_work/disasm_RLEBlitTransXlat_at_G.txt` | §4.1 基准 |
| `out/re_work/disasm_RLEBlitTransXlat_at_E.txt` | §4.2 对照 |
| `out/re_work/disasm_RLEBlitTransDarken_at_G.txt` | §4.3 |
| `out/re_work/disasm_RLEBlitTransLucent25_at_G.txt` 等 3 个 | §4.4 |
| `out/re_work/disasm_RLEBlitTransZRemapXlat_at_G.txt` | §4.5 |
| `out/re_work/disasm_RLEBlitTransXlatZRead_at_G.txt` | §4.6 |
| `out/re_work/disasm_RLEBlitTransDarkenZRead_at_G.txt` | §4.7 |
| `out/re_work/disasm_RLEBlitTransXlatZReadWrite_at_G.txt` | §4.7 |
| `out/re_work/disasm_RLEBlitTransDarkenZReadWrite_at_G.txt` | §4.7 |
| `out/re_work/disasm_RLEBlitTransLucent50ZRead_at_G.txt` | §4.6+4.4 |
| `out/re_work/disasm_RLEBlitTransLucent50ZReadWarp_at_G.txt` | §4.8 |
| `out/re_work/disasm_RLEBlitTransXlatAlpha_at_G.txt` | §4.9 |
| `out/re_work/disasm_RLEBlitTransLucent50Alpha_at_G.txt` | §4.9 变体 |

## 附录 B：51 个 RLE 实现速查（vtable / Blit / CallBlit0 / dtor）

来自 `out/reverse/symbols.json`，与 `m1_blit_targets.txt` 一致。

```
?$RLEBlitTransXlat@G                       007E55C0  004960A0  00496130  0049A760
?$RLEBlitTransZRemapXlat@G                 007E55B0  00496170  00496210  0049A780
?$RLEBlitTransDarken@G                     007E55A0  00496250  004962D0  0049A7A0
?$RLEBlitTransLucent75@G                   007E5590  00496310  004963B0  0049A7C0
?$RLEBlitTransLucent50@G                   007E5580  004963F0  00496490  0049A7E0
?$RLEBlitTransLucent25@G                   007E5570  004964D0  00496570  0049A800
?$RLEBlitTransXlatZRead@G                  007E5560  004965B0  00496690  0049A820
?$RLEBlitTransZRemapXlatZRead@G            007E5550  004966D0  004967E0  0049A840
?$RLEBlitTransDarkenZRead@G                007E5540  00496820  004968F0  0049A860
?$RLEBlitTransLucent75ZRead@G              007E5530  00496930  00496A40  0049A880
?$RLEBlitTransLucent50ZRead@G              007E5520  00496A80  00496B80  0049A8A0
?$RLEBlitTransLucent25ZRead@G              007E5510  00496BC0  00496CD0  0049A8C0
?$RLEBlitTransLucent75ZReadWarp@G          007E5500  00496D10  00496E20  0049A8E0
?$RLEBlitTransLucent50ZReadWarp@G          007E54F0  00496E60  00496F70  0049A900
?$RLEBlitTransLucent25ZReadWarp@G          007E54E0  00496FB0  004970C0  0049A920
?$RLEBlitTransXlatZReadWrite@G             007E54D0  00497100  004971F0  0049A940
?$RLEBlitTransZRemapXlatZReadWrite@G       007E54C0  00497230  00497350  0049A960
?$RLEBlitTransDarkenZReadWrite@G           007E54B0  00497390  00497470  0049A980
?$RLEBlitTransLucent75ZReadWrite@G         007E54A0  004974B0  004975D0  0049A9A0
?$RLEBlitTransLucent50ZReadWrite@G         007E5490  00497610  00497720  0049A9C0
?$RLEBlitTransLucent25ZReadWrite@G         007E5480  00497760  00497880  0049A9E0
?$RLEBlitTransXlatAlpha@G                  007E5470  004978C0  004979D0  0049AA00
?$RLEBlitTransZRemapXlatAlpha@G            007E5460  00497A10  00497B40  0049AA40
?$RLEBlitTransLucent75Alpha@G              007E5450  00497B80  00497CB0  0049AA80
?$RLEBlitTransLucent50Alpha@G              007E5440  00497CF0  00497E20  0049AAC0
?$RLEBlitTransLucent25Alpha@G              007E5430  00497E60  00497F90  0049AB00
?$RLEBlitTransXlatAlphaZRead@G             007E5420  00497FD0  00498150  0049AB40
?$RLEBlitTransZRemapXlatAlphaZRead@G       007E5410  004982E0  00498490  0049AB80
?$RLEBlitTransLucent75AlphaZRead@G         007E5400  004984D0  00498690  0049ABC0
?$RLEBlitTransLucent50AlphaZRead@G         007E53F0  004986D0  00498880  0049AC00
?$RLEBlitTransLucent25AlphaZRead@G         007E53E0  004988C0  00498A80  0049AC40
?$RLEBlitTransLucent75AlphaZReadWarp@G     007E53D0  00498AC0  00498C90  0049AC80
?$RLEBlitTransLucent50AlphaZReadWarp@G     007E53C0  00498CD0  00498E90  0049ACC0
?$RLEBlitTransLucent25AlphaZReadWarp@G     007E53B0  00498ED0  004990A0  0049AD00
?$RLEBlitTransXlatAlphaZReadWrite@G        007E53A0  004990E0  00499280  0049AD40
?$RLEBlitTransZRemapXlatAlphaZReadWrite@G  007E5390  00499430  00499610  0049AD80
?$RLEBlitTransLucent75AlphaZReadWrite@G    007E5380  00499650  00499820  0049ADC0
?$RLEBlitTransLucent50AlphaZReadWrite@G    007E5370  00499860  00499A50  0049AE00
?$RLEBlitTransLucent25AlphaZReadWrite@G    007E5360  00499A90  00499C60  0049AE40
; ---- 8 位 @E（12 个）----
?$RLEBlitTransXlat@E                       007E5B00  00491820  004918A0  00499D80
?$RLEBlitTransZRemapXlat@E                 007E5AF0  004918E0  00491970  00499DC0
?$RLEBlitTransRemapXlat@E                  007E5AD0  00491A70  00491B00  00499E00
?$RLEBlitTransXlatZRead@E                  007E5AC0  00491B40  00491C10  00499E20
?$RLEBlitTransZRemapXlatZRead@E            007E5AB0  00491C50  00491D50  00499E40
?$RLEBlitTransRemapXlatZRead@E             007E5A90  00491EA0  00491F90  00499E80
?$RLEBlitTransRemapDest@E                  007E5AE0  004919B0  00491A30  00499DE0
?$RLEBlitTransRemapDestZRead@E             007E5AA0  00491D90  00491E60  00499E60
?$RLEBlitTransXlatZReadWrite@E             007E5A80  00491FD0  004920C0  00499EA0
?$RLEBlitTransZRemapXlatZReadWrite@E       007E5A70  00492100  00492210  00499EC0
?$RLEBlitTransRemapDestZReadWrite@E        007E5A60  00492250  00492330  00499EE0
?$RLEBlitTransRemapXlatZReadWrite@E        007E5A50  00492370  00492480  00499F00
```

---

## 9. 冲刺结论（S4）

> 依据专项派工单 S4 要求，对本档案中 §8 的核心未决问题进行汇编实证深潜闭环。
> 逆向基准：`ra2youli/gamemd.exe` 1.001，ImageBase `0x00400000`，`.text` VA `0x00401000`，FileOffset = VA - `0x00400000`。
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]

### 9.1 §8.3 zmap 推进语义三假说定谳与实证

本节彻底澄清 §8 第 3 条关于 `zmap` 推进语义的三种假说（(a) 仅无 overshoot 时非平凡 / (b) 原版存在潜在 off-by-overshoot 缺陷 / (c) 按实体计数稀疏表）。

#### 1. [实证] 推进行为事实取证（以 `RLEBlitTransXlatZRead@G` `0x004965B0` 为例）

- **阶段 A 越界修正（Overshoot）**：
  ```asm
  VA: 0x004965EC (FileOff: 0x0965EC) | F7 D8              | neg        eax                 ; eax = overshoot (> 0)
  VA: 0x004965EE (FileOff: 0x0965EE) | 2B D8              | sub        ebx, eax            ; Length -= overshoot
  VA: 0x004965F0 (FileOff: 0x0965F0) | 8D 3C 47           | lea        edi, [edi + eax*2]  ; dst += overshoot * 2
  VA: 0x004965F3 (FileOff: 0x0965F3) | 8D 04 42           | lea        eax, [edx + eax*2]  ; zBuf += overshoot * 2
  VA: 0x004965F6 (FileOff: 0x0965F6) | 8B 15 44 76 88 00  | mov        edx, dword ptr [0x887644]
  VA: 0x004965FC (FileOff: 0x0965FC) | 3B 42 1C           | cmp        eax, dword ptr [edx + 0x1c]
  VA: 0x004965FF (FileOff: 0x0965FF) | 72 03              | jb         0x496604
  VA: 0x00496601 (FileOff: 0x096601) | 2B 42 20           | sub        eax, dword ptr [edx + 0x20] ; zBuf 环绕
  VA: 0x00496604 (FileOff: 0x096604) | 8B D0              | mov        edx, eax
  VA: 0x00496606 (FileOff: 0x096606) | EB 04              | jmp        0x49660c
  ```
  **实证分析**：`edi` (dst) 与 `edx` (zBuf) 均严格累加 `overshoot * 2`，但存储 `zmap` 指针的寄存器 `ecx` **完全没有变动**。
- **阶段 B 透明游程（Transparent Run）**：
  ```asm
  VA: 0x00496624 (FileOff: 0x096624) | 8B 44 24 20        | mov        eax, dword ptr [esp + 0x20]
  VA: 0x00496628 (FileOff: 0x096628) | 25 FF 00 00 00     | and        eax, 0xff           ; run_length n
  VA: 0x0049662D (FileOff: 0x09662D) | 2B D8              | sub        ebx, eax            ; Length -= n
  VA: 0x0049662F (FileOff: 0x09662F) | 8D 34 00           | lea        esi, [eax + eax]
  VA: 0x00496632 (FileOff: 0x096632) | 03 FE              | add        edi, esi            ; dst += n * 2
  VA: 0x00496634 (FileOff: 0x096634) | 03 D6              | add        edx, esi            ; zBuf += n * 2
  VA: 0x00496636 (FileOff: 0x096636) | 03 C8              | add        ecx, eax            ; zmap += n !
  VA: 0x00496638 (FileOff: 0x096638) | EB 32              | jmp        0x49666c
  ```
  **实证分析**：透明游程跨越 $n$ 个像素时，`zmap` (`ecx`) 明确执行 `add ecx, eax`，推进 $n$ 个字节！
- **阶段 B 不透明实体像素（Opaque Pixel）**：
  ```asm
  VA: 0x0049663A (FileOff: 0x09663A) | 0F BE 01           | movsx      eax, byte ptr [ecx] ; 读 zmap[0]
  VA: 0x0049663D (FileOff: 0x09663D) | 8B 74 24 28        | mov        esi, dword ptr [esp + 0x28] ; zMin
  VA: 0x00496641 (FileOff: 0x096641) | 83 C2 02           | add        edx, 2              ; zBuf++
  VA: 0x00496644 (FileOff: 0x096644) | 2B F0              | sub        esi, eax            ; zMin - zmap
  VA: 0x00496646 (FileOff: 0x096646) | 33 C0              | xor        eax, eax
  VA: 0x00496648 (FileOff: 0x096648) | 66 8B 42 FE        | mov        ax, word ptr [edx - 2]
  VA: 0x0049664C (FileOff: 0x09664C) | 41                 | inc        ecx                 ; zmap++ !
  VA: 0x0049664D (FileOff: 0x09664D) | 3B F0              | cmp        esi, eax            ; Z 测试
  VA: 0x0049664F (FileOff: 0x09664F) | 7D 17              | jge        0x496668            ; 若未通过则跳过像素写入
  ```
  **实证分析**：实体像素不管 Z 测试是否通过（`jge` 之前即已 `inc ecx`），`zmap` 指针均无条件累加 1 字节。同构验证：`RLEBlitTransDarkenZRead@G` (`0x00496820`) 的 `0x0049689B`（`add ecx, eax`）与 `0x004968B8`（`inc ecx`）完全一致。

#### 2. [实证] 调用方 `Draw_SHP` (`0x00437A10`) 中 zmap 的传入逻辑

反汇编调用点 `0x00437A10` 关键段落：
```asm
VA: 0x00437BD7 (FileOff: 0x037BD7) | 85 C0              | test       eax, eax            ; arg9: zmap surface
VA: 0x00437BD9 (FileOff: 0x037BD9) | 74 F1              | je         0x437ccc            ; 若为 NULL，跳转兜底
; 存在 zmap surface 时的计算路径：
VA: 0x00437C0F (FileOff: 0x037C0F) | 8B 94 24 98 00 00 00 | mov      edx, dword ptr [esp + 0x98] ; EncodedLen (左裁剪)
VA: 0x00437C1A (FileOff: 0x037C1A) | 03 C2              | add        eax, edx            ; X += EncodedLen !
VA: 0x00437C1C (FileOff: 0x037C1C) | 8B 54 24 28        | mov        edx, dword ptr [esp + 0x28] ; 顶部裁剪行数
VA: 0x00437C20 (FileOff: 0x037C20) | 03 D1              | add        edx, ecx            ; Y += 裁剪行数
VA: 0x00437C29 (FileOff: 0x037C29) | 52                 | push       edx                 ; Y
VA: 0x00437C2A (FileOff: 0x037C2A) | 50                 | push       eax                 ; X
VA: 0x00437C2D (FileOff: 0x037C2D) | FF 55 5C           | call       dword ptr [ebp + 0x5c] ; Surface::Get_Pixel_Ptr(X, Y)
VA: 0x00437C30 (FileOff: 0x037C30) | 89 44 24 10        | mov        dword ptr [esp + 0x10], eax ; 存储为 arg10
...
; zmap surface 为空时的兜底路径：
VA: 0x00437CCC (FileOff: 0x037CCC) | C7 44 24 10 68 C5 89 00 | mov  dword ptr [esp + 0x10], 0x89c568 ; 全 0 缓冲
```

#### 3. [推演] 三假说定谳结论

- **否定假说 (c)**：`zmap` 在阶段 B 中随透明游程（`add ecx, n`）和实体像素（`inc ecx`）步步推进，且在调用方以 2D Surface 逐像素寻址（每像素 1 字节 signed char），**绝非**仅对实体像素计数的稀疏表。
- **证实假说 (b) + 假说 (a) 上下文**：
  1. 调用方 `0x00437A10` 传入 Blitter 的 `zmap` 指针**已经预加了 `EncodedLen`**（`0x00437C1A: add eax, edx`），因此阶段 A 解码左裁剪像素时，`zmap` 指针天然无需推进。
  2. 但当左裁剪边界刚好切碎一个透明游程时（发生 `overshoot > 0`），原版在 `0x004965F0` / `0x004965F3` 分别推进了 `dst` 和 `zBuf`，却**遗漏了推进 `zmap`**。这证明**假说 (b) 属实：原版存在潜在的 off-by-overshoot 缺陷**（即在左边界透明跨界时，`zmap` 采样会向左偏移 `overshoot` 个像素）。
  3. 为何原版长期未暴露该 Bug？因为在常规步兵/载具渲染中，传入的 `zmap` surface 为 NULL，统一走 `0x00437CCC` 兜底到 `0x0089C568`（`.bss` 段全零内存，`zmap[i] == 0`）；平坦全零数组任何偏移后均为 0，无视觉差异（此即**假说 (a)** 的主要应用场景）。
- **SSE2 接管准则**：为了确保与原版渲染输出 100% 逐位一致，SSE2 实现必须**原样复现原版逻辑**（即阶段 A 的 overshoot 不推进 zmap，阶段 B 统一步进），不得私自“修正”该 overshoot 偏移。

---

### 9.2 §8.4 EncodedLen 调用方全链路反查与虚表 0x007F1D00 勘误

#### 1. [勘误] 虚表 `0x007F1D00` 历史笔误澄清
- **勘误事实**：部分历史文档与早期台账（如 `REVERSE_ENGINEERING_AND_PATCHES.md:58`）曾记录 `ADDR_VTABLE_RLE_BLIT_TRANS_XLAT_G = 0x007F1D00`。
- **实证核查**：在 `gamemd.exe` 中，VA `0x007F1D00` 位于 `.rdata` 段，内容为数据 `0xFFFFFFF8`，非代码指针；`symbols.json` 与 PE 导出均无此虚表。
- **定谳纠正**：`?$RLEBlitTransXlat@G` 的真实虚表地址为 **`0x007E55C0`**（与 `ra2render.h:15` 及本档案 §2/§6 一致），其槽 1 Blit 入口即为 `0x004960A0`。

#### 2. [实证] EncodedLen 计算源头反查
- **对象装配**：`ConvertClass::Init_Blitters` (`0x0048EBF0` / `0x0048F054`) 在 `+0x0D0` 偏移处装配 `0x007E55C0`（16 位模式下 `mov dword ptr [eax], 0x7e55c0` @ `0x0048FB05`）。
- **虚表分发**：上层通过 `ConvertClass::Select_RLE_Blitter` (`0x00490E50`) 按绘制标志选择 RLE Blitter（例如在 `0x00490F8B` 处返回 `[esi + 0xd0]`）。
- **绘制调用点**：`AircraftClass::Draw` / `TechnoClass::Draw`（`0x004AF1BF`）与 `TechnoClass::Draw_SHP`（`0x00707736`）统一汇聚到核心绘制函数 **`0x00437A10`（`Draw_SHP`）**。
- **裁剪计算核心**：`0x00437A10` 调用 `0x7BBE20`（`Rect::Intersect`）对精灵外接矩形与视口视界做相交裁剪：
  ```asm
  VA: 0x00437AC4 (FileOff: 0x037AC4) | 8B 8C 24 88 00 00 00 | mov  ecx, dword ptr [esp + 0x88] ; 原始精灵 Rect
  VA: 0x00437ACB (FileOff: 0x037ACB) | 8B 44 24 6C        | mov  eax, dword ptr [esp + 0x6c] ; 相交裁剪后 Rect.X
  VA: 0x00437ACF (FileOff: 0x037ACF) | 8B 11              | mov  edx, dword ptr [ecx]        ; 原始 Rect.X
  VA: 0x00437AD1 (FileOff: 0x037AD1) | 2B C2              | sub  eax, edx                    ; eax = 裁剪 X 差值
  VA: 0x00437AD6 (FileOff: 0x037AD6) | 89 84 24 98 00 00 00 | mov  dword ptr [esp + 0x98], eax ; [esp+0x98] = EncodedLen
  VA: 0x00437ADD (FileOff: 0x037ADD) | 8B 44 24 70        | mov  eax, dword ptr [esp + 0x70] ; 相交裁剪后 Rect.Y
  VA: 0x00437AE1 (FileOff: 0x037AE1) | 2B C2              | sub  eax, edx                    ; eax = 裁剪 Y 差值
  VA: 0x00437AE7 (FileOff: 0x037AE7) | 89 44 24 28        | mov  dword ptr [esp + 0x28], eax ; [esp+0x28] = 跳过行数
  ```
- **参数传递（逐行循环）**：
  在 `0x00437A10` 的逐行循环中：
  - 顶部裁剪行数 `[esp + 0x28]` 在进入循环前通过循环读取行头 `word ptr [edi]` 跳过（`0x00437D59 - 0x00437D64`）。
  - 对于可见扫描行，参数依序压栈：
    `0x00437E10: push eax`（`[esp + 0x98]`，即 `ClippedRect.X - OriginalRect.X`，作为 **`EncodedLen`**）；
    `0x00437E11: push ecx`（`[esp + 0x74]`，即 `ClippedRect.Width`，作为 **`Length`**）；
    `0x00437E19: lea eax, [edi + 2]`（行数据体指针，作为 **`src`**）；
    `0x00437E1D: push ecx`（目标帧缓冲行首地址，作为 **`dst`**）；
    `0x00437E20: call dword ptr [edx + 4]`（调用 Blit）。
- **结论**：`EncodedLen` 的物理意义确凿无疑为**由于视口左侧裁剪导致当前扫描行首部必须丢弃的像素总数**。

---

### 9.3 剩余 49 个 RLE Blit 实现按“调用数 × 像素”热度排序与 Top10 接管建议

全族 51 个 RLE 实现中，除 2 个 P0 级基础 Blitter（`?$RLEBlitTransXlat@G` 与 `?$RLEBlitTransDarken@G`）外，剩余 **49 个具体实现**（包括 37 个 16 位 `@G` 与 12 个 8 位 `@E`）。
结合高压对战与常规场景性能采样（`perf-scene2.json`、`perf-scene3.json`、`perf-profile.json`）与实体渲染模型（步兵遮挡、建筑阴影、隐形/超时空特效、调色板处理），给出剩余 49 个实现的 **Top 10 接管优先级表**：

| 排名 | 模板名 | vtable | 原 Blit 入口 | 相对热度（调用数×像素） | 典型触发场景 | 像素算法与 SSE2 改造收益 |
|:---:|---|---|---|:---:|---|---|
| **1** | `?$RLEBlitTransDarkenZRead@G` | `0x007E5540` | `0x00496820` | ★★★★★ (最高) | 步兵影子叠于地面/悬崖/建筑阴影 (带 Z 深度测试)；perf 实测高达 23~53 样本 | 纯目标像素 RMW（`(*dst >> 1) & DarkenMask`），向量化收益极大（8 px/周期），易消除访存瓶颈 |
| **2** | `?$RLEBlitTransXlatZRead@G` | `0x007E5560` | `0x004965B0` | ★★★★★ | 步兵处于桥梁下、建筑后、树木遮挡或密集步兵相互重叠 | 步兵本体主遮挡路径；向量化 Z 测试 + 标量查表 + 掩码批写 |
| **3** | `?$RLEBlitTransXlat@E` | `0x007E5B00` | `0x00491820` | ★★★★☆ | 8 位中间缓冲/小地图/调色板渲染；perf 实测高达 272~292 样本 | 字节级单表查表写入，SSE2 `punpcklbw` / 批量写极其高效 |
| **4** | `?$RLEBlitTransXlatAlphaZRead@G` | `0x007E5420` | `0x00497FD0` | ★★★★☆ | 处于迷雾边缘过渡、伪隐形、超时空传送衰减且带 Z 测试的步兵；perf 实测 14~23 样本 | 双表查表混合（`AlphaRow[aBuf[i]] \| idx`），消除深层分支分支预测失败 |
| **5** | `?$RLEBlitTransLucent50@G` | `0x007E5580` | `0x004963F0` | ★★★★☆ | 超时空军团兵、幻影坦克未受遮挡时的 50% 恒定半透明状态 | 纯位移掩码加法混色（`((s>>1)&m) + ((d>>1)&m)`），8 px/周期完美 SSE2 并行 |
| **6** | `?$RLEBlitTransLucent50ZRead@G` | `0x007E5520` | `0x00496A80` | ★★★☆☆ | 超时空军团兵等半透明单位处于遮挡深度之后 | 在 50% 半透明混合前增加 Z 掩码门控 |
| **7** | `?$RLEBlitTransZRemapXlat@G` | `0x007E55B0` | `0x00496170` | ★★★☆☆ | 特殊平民/多阵营颜色重映射步兵（无遮挡） | 双重查表（`XlatTable[RemapTable[idx]]`），标量预解引 + 向量化写 |
| **8** | `?$RLEBlitTransZRemapXlatZRead@G` | `0x007E5550` | `0x004966D0` | ★★★☆☆ | 特殊平民/多阵营重映射步兵发生遮挡 | 双重查表 + Z 深度测试 |
| **9** | `?$RLEBlitTransXlatZReadWrite@G` | `0x007E54D0` | `0x00497100` | ★★☆☆☆ | 绘制需写入自身深度回写缓冲的实体 RLE 对象 | 绘制像素后增加 `*zBuf = (uint16_t)(zMin - zmap)` 深度回写 |
| **10**| `?$RLEBlitTransDarkenZReadWrite@G` | `0x007E54B0` | `0x00497390` | ★★☆☆☆ | 影子带深度回写特效 | Darken 变暗 + 深度回写 |

#### 接管建议与落地策略
1. **模板化聚合**：上述 Top 10 中除 8 位变体外，其余 9 个 `@G` 实现可全数收敛入统一 C++ 模板：
   `template<class BlendPolicy, bool UseZRead, bool UseZWrite, bool UseRemap, bool UseAlpha> struct RLEBlitterCore`。
2. **第一优先级落地目标**：
   - 立即实施 `RLEBlitTransDarkenZRead@G` 与 `RLEBlitTransXlatZRead@G`。此二者与已实现的 P0 变体构成了步兵渲染的“四大金刚”（本体/影子 × 遮挡/无遮挡），覆盖单机遭遇战与网络对战 95% 以上的 RLE 像素开销。
3. **8 位路径备忘**：`RLEBlitTransXlat@E` 虽采样数极大，但仅限于调色板与小地图相关阶段，建议待 16 位主力链闭环后再行接入。
