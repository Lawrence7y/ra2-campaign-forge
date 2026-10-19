# 非 RLE Blit 族优先级 与 未命名热点簇命名档案（gamemd.exe 1.001）

> 目标：1) 给出非 RLE `@G` Blitter 在 `BlitTransXlatAlphaZRead` 之后的 Top 5–8 模板优先级与算法/SSE2 要点（供 ra2render 补全）；2) 对 `0x531A0A` 附近与 `0x408F14` 附近两个未命名热点簇起名定性；3) 可选核实 `0x5D4B30`；4) 给出下一批 Hook 建议。
> 依据：`out/reverse/m1_blit_targets.txt`、`out/reverse/symbols.json`、`out/reverse/perf-profile.md`、`ra2youli/gamemd.exe` capstone 反汇编、`YRpp/Blitters/Blitter/*.h`、`ra2render/blitter_hooks.cpp`（只读）、`docs/re/rle_blit_family.md`（只读对照）。
> PE 事实：ImageBase=0x400000，.text RVA≈文件偏移，下文均为 VA。
> 反汇编工作产物：`out/re_work/disasm_nonrle_priority.txt`、`disasm_cluster_531A0A.txt`、`disasm_cluster_408F14.txt`、`disasm_cluster_5D4B30.txt`（中间产物，非交付）。
> **本档案不修改总档案、源码与 dll。**

---

## 1. 结论

1. **非 RLE `@G` 共 57 个实现**（`Blitter` 基类 vtable=`0x007E5B88`，虚函数 5 槽：dtor / Blit / CallBlit0 / CallBlit1 / CallBlit2）。与 RLE 族的四点关键差异：
   - **无 RLE 码流**：`src` 是「每像素 1 字节索引」的密集数组（`BlitTrans@G`/`BlitPlain@G` 除外，它们的 `src` 直接是 16 位像素），`length` 就是像素数，**没有 EncodedLen 左裁剪、没有 overshoot 修正**。
   - **调用约定不同**：Blit `ret 0x20`（**8 个 DWORD**），RLE 是 `ret 0x28`（10 个）。YRpp 头文件签名与汇编一致，现有 `Hook_BlitTransXlat_G` 等 5 个非 RLE Hook 的形参是对的。
   - **Z 测试更简单**：只比 `zBuf[i] > zMin`，**没有 zmap**（RLE 有逐像素 zmap）。
   - **src/dst/zBuf 每像素齐头并进**：Z 失败也 `src++`（位置对齐密集流），批处理可无条件 `src += n`——与 RLE 游程跳过完全不同，见 §2.2。
2. **像素算法仍是 RLE 文档 §1 那 5 个正交原语的组合**（Xlat / Darken / Lucent25·50·75 / ZRemapXlat / ZRead·ZReadWrite / Alpha / Warp），公式逐位一致，可直接复用 `rle_blit_family.md` §4 的伪代码——只删掉解码循环。
3. **单位重叠路径已经齐备**：已 Hook 的 `BlitTransXlatAlphaZRead` 是「Xlat+Alpha+Z」最全变体；但步兵/载具在重叠时主路径走的是**更瘦的** `BlitTransXlatZRead` / `BlitTransDarkenZRead`，影子半透明走 `BlitTransLucent*`。这三族是继 `BlitTransXlatAlphaZRead` 之后的真正热点，详见 §2。
4. **`0x531A0A` 簇 = 「Init.CPP 对话框 / 秘籍输入簇」**（非渲染、非逻辑热路径；大栈来自对话框字符串缓冲）。建议命名 `AboutDlgCheatCluster`，详见 §3.1。
5. **`0x408F14` 簇 = 「扇区缓冲读取 + 高精度时钟」双生小方法簇**。`0x408E00–0x409354` 是 MIX/CD 类扇区缓冲的读取核心（`rep movsd` 拷贝 + 环形缓冲前进）；紧邻的 `0x409360–0x4093FF` 是 QPC/timeGetTime 高精度时钟（函数指针安装在 `0x87E848`）。perf 里 `0x409300` 桶的 104 样本几乎全部落在**时钟侧**而非文件 I/O 侧。建议命名 `BufSectorReaderClockCluster`，详见 §3.2。
6. **`0x5D4B30` 一带不是 MPGameMode**（此前粗归因有误）。实证是 **Win32 主消息泵 + 快捷键/窗口向量**（`DynamicVectorClass<HWND>` @`0xABFC90`、`DynamicVectorClass<AcceleratorTracker>` @`0xABFCB8`，IAT：`IsDialogMessageA`/`TranslateAcceleratorA`/`TranslateMessage`/`DispatchMessageA`）。**单机遭遇战同样每帧跑，不能按「MP 专属」忽略**；但它与 blit/寻敌无关，渲染优化可以绕开。详见 §4。

---

## 2. 非 RLE 优先级表（继 BlitTransXlatAlphaZRead 之后）

排序依据：**单位重叠常见程度**（重叠时换 ZRead 变体）× 出现频率（每单位一帧必画本体/影子）× SSE2 收益 × 实现可复用性。

| 优先级 | 模板名 | vtable | Blit 入口 | 像素公式要点（RGB565） | 重叠相关性 | SSE2 难点 |
|---|---|---|---|---|---|---|
| **P0** | `?$BlitTransXlatZRead@G` | `0x007E5978` | `0x00492B00` | `if (zBuf[i] > zMin && idx) *dst = XlatTable[idx]` | ★★★★★ 重叠时本体主路径 | Z 逐像素比较 + zBuf 环绕；查表 gather |
| **P0** | `?$BlitTransDarkenZRead@G` | `0x007E5948` | `0x00492D20` | `if (zBuf[i] > zMin && idx) *dst = (*dst>>1)&DarkenMask` | ★★★★★ 重叠时影子路径 | 纯 dst RMW，SIMD 收益最大；zBuf 环绕 |
| **P1** | `?$BlitTransLucent50@G` | `0x007E59C0` | `0x00492830` | `*dst = ((s>>1)&m) + ((d>>1)&m)`，`s=XlatTable[idx]` | ★★★★ 超时空/心灵/隐形半透明 | 移位+掩码混合，8px/拍完美 SIMD |
| **P1** | `?$BlitPlainXlat@G` | `0x007E5A38` | `0x004924C0` | 不透明：`*dst = XlatTable[idx]`（无透明跳过） | ★★★ 不透明帧也常带阵营色 | 纯查表写入；可 8 索引 gather 后批量写 |
| **P2** | `?$BlitTransZRemapXlat@G` | `0x007E5A08` | `0x00492590` | `*dst = XlatTable[ RemapTable[idx] ]`（双查表） | ★★★ 深度重映射单位 | 两次 gather，建议标量查表 + SIMD 批写 |
| **P2** | `?$BlitTransXlatZReadWrite@G` | `0x007E5888` | `0x00493600` | 同 P0 且 `zBuf[i] = zMin`（回写） | ★★★ 重叠 + 深度写回 | 回写值必须是 `zMin`（本变体无 zmap） |
| **P3** | `?$BlitTransLucent25@G` / `?$BlitTransLucent75@G` | `0x007E59A8` / `0x007E59D8` | `0x00492920` / `0x00492740` | 25: `3*((s>>2)&m)+((d>>2)&m)`；75: `((s>>2)&m)+3*((d>>2)&m)` | ★★ 与 50 同模板参数化 | 与 Lucent50 共享模板，无额外难点 |
| **P3** | `?$BlitTransDarkenZReadWrite@G` / `?$BlitPlainXlatZRead@G` | `0x007E5858` / `0x007E5990` | `0x00493830` / `0x00492A10` | Darken 回写 z / 不透明+Z | ★★ | 同上组合 |

### 2.1 通用约定（非 RLE 全族）

```
Blit(                          // ret 0x20，8 个 DWORD
    void*    dst,              // [esp+0x04] uint16_t* 目标
    void*    src,              // [esp+0x08] 多数变体是 uint8_t* 索引流；
                               //           BlitTrans@G / BlitPlain@G 是 uint16_t* 像素流
    int      length,           // [esp+0x0C] 像素数（32 位）
    uint16_t zMin,             // [esp+0x10]
    uint16_t* zBuf,            // [esp+0x14] 深度缓冲（可环绕）
    uint16_t* aBuf,            // [esp+0x18] alpha 缓冲（Alpha 变体）
    uint16_t aLvl,             // [esp+0x1C] alpha 等级
    int      warpOffset        // [esp+0x20] 扭曲偏移（Warp 变体）
)
```

- `__thiscall`：`ecx=this`。**只 Hook 槽 1（vtable+4）**；CallBlit0/1/2 都是薄包装转发给 Blit（YRpp 头文件可见），虚表改完自动跟随。
- **this 布局**（与 RLE §3.4 相同，但无 zmap 成员差异）：

| 变体 | `this+0x04` | `this+0x08` |
|---|---|---|
| Xlat / PlainXlat / Lucent* | `uint16_t* XlatTable`（YRpp 名 `Data`） | （Lucent）`uint16_t BlendMask`（YRpp 名 `ExtraData`，典型 `0x7BEF`） |
| Darken* | `uint16_t DarkenMask`（**值**不是指针） | — |
| ZRemapXlat* | `void*`→解 1 次得 `uint8_t* RemapTable` | `uint16_t* XlatTable` |
| *Alpha* | `uint16_t* XlatTable` | Alpha 表基址（按 aLvl 选 512 字节行） |

- **Z 环绕**（Z* 变体）：全局 `*(void**)0x00887644`，`+0x1C=BufferEnd`、`+0x20=BufferSize`，每次 `zBuf++` 后 `if (zBuf >= End) zBuf -= Size`。Alpha 变体对 `aBuf` 用 `0x0087E8A4` 同布局描述符。
- **透明判据**：索引流 `idx==0` 跳过（`BlitTrans*`）；`BlitPlain*` **无**透明跳过；`BlitTrans@G` 是 16 位像素 `px==0` 跳过（`src` 已是颜色，不查表）。
- **左裁剪/overshoot：非 RLE 不存在**。行裁剪由调用方直接偏移 `dst/src/zBuf` 指针完成（对比 RLE §3.3）。SSE2 改造**不要**引入 EncodedLen 语义。

### 2.2 重点算法（与 RLE 文档同深度，已删解码）

#### `BlitTransXlatZRead@G` @ `0x00492B00`（P0，重叠本体）

40 条指令，`ret 0x20`。寄存器：`ecx=this`，`edx=length`，`eax=zBuf`，`ebx=src`，`edi=dst`。

```
00492B22  mov  dx, [eax]         ; zb = *zBuf
00492B25  add  eax, 2            ; zBuf++
00492B28  cmp  [esp+0x20], edx   ; zMin ? zb   （jge = zMin>=zb → 跳过）
00492B2C  jge  00492B52
00492B2E  mov  dl, [ebx]         ; idx = *src++
00492B30  test dl, dl
00492B36  je   00492B52          ; 透明跳过
00492B45  mov  dx, [esi+edx*2]   ; px = XlatTable[idx]
00492B49  mov  [edi], dx
00492B52  ... zBuf 环绕检查 ...
00492B56  add  edi, 2 / dec ebp  ; 无论过不过 Z 都推进 dst 与计数
```

```c
while (length-- > 0) {
    uint16_t zb = *zBuf++; zbuf_wrap();
    int idx = *src++;                 // 无论 Z 是否通过都推进
    if (zb > zMin && idx) *dst = xlat[idx];
    dst++;
}
```

> **关键：src / dst / zBuf 三者每像素齐头并进（位置对齐的密集流）**。汇编里 `jge` 只跳过「读索引 + 写像素」，循环底部的 `inc ebx`（src++）/ `add edi,2`（dst++）/ zBuf 环绕在**两条路径上都会执行**（`0x00492B55 inc ebx` 位于 `jge` 目标之后）。YRpp 头文件把 `*src++` 写在 Z 分支内是简化写法，语义等价（Z 失败时索引字节被跳过但仍占一个像素槽位）。
> 这与 RLE 族**根本不同**（RLE 透明游程只推 dst/zBuf/zmap 不推 src；且有 EncodedLen）。非 RLE 的 SSE2 批处理可以放心 `src += 8`。
> 全族同构：`BlitTransDarkenZRead@0x00492D69 inc edi`、`BlitTransXlatAlphaZRead@0x00494C09 inc eax`、`BlitPlainXlatZRead@0x00492A55 inc esi` 均如此。

#### `BlitTransDarkenZRead@G` @ `0x00492D20`（P0，重叠影子）

= 上式 + Darken 写入：

```c
if (zb > zMin && idx) *dst = (*dst >> 1) & this->DarkenMask;  // idx 只作标志
dst++; /* src 仅在 Z 通过时消耗 */
```

与 `BlitTransDarken@G` @ `0x00492670`（已 Hook）写法相同，差别只在 Z 门控。

#### Lucent 族（`0x00492830` / `0x00492920` / `0x00492740`）

三档公式与 RLE §4.4 **逐位一致**（`m = this+0x08 BlendMask`）：

| 变体 | 公式 | 汇编要点 |
|---|---|---|
| Lucent25 | `*dst = 3*((s>>2)&m) + ((d>>2)&m)` | `shr ax,2 / lea eax,[eax+eax*2]`（@`0x492959-0x492966`） |
| Lucent50 | `*dst = ((s>>1)&m) + ((d>>1)&m)` | `shr eax,1 / shr ebx,1 / and / add`（@`0x492868-0x492873`） |
| Lucent75 | `*dst = ((s>>2)&m) + 3*((d>>2)&m)` | `lea edx,[eax+eax*2]` 乘目标侧（@`0x492785`） |

**必须「移位+掩码」**，换成除法会渗色。

#### `BlitPlainXlat@G` @ `0x004924C0`（P1）

无透明跳过，逐像素 `*dst = XlatTable[*src++]`。这是最简单的查表拷贝，SSE2 收益主要来自减少分支，而非运算本身（gather 是瓶颈）。

#### `BlitTransZRemapXlat@G` @ `0x00492590`（P2）

```c
const uint8_t* remap = *(uint8_t**)(this+4);   // 双重解引用
while (length-- > 0) {
    int idx = *src++;
    if (idx) *dst = xlat[ remap[idx] ];
    dst++;
}
```

#### `BlitTransXlatZReadWrite@G` @ `0x00493600`（P2）

通过 Z 测试后 `mov [eax], bp` 回写 `zBuf[i] = zMin`（@`0x49364D`）。本变体**无 zmap**，回写值就是 `zMin`（不是 `zMin - zmap[i]`，那套只在 RLE）。

#### `BlitTransXlatAlphaZRead` 族（已 Hook，公式备查）

`0x00494B60`：行号 `row = min(0xFE, (max(aLvl,0) * 261) >> 11)`，`extra = *(this+8) + (row<<9)`；像素 `*dst = XlatTable[ extra[*aBuf++] | idx ]`。与 YRpp `BlitTransXlatAlphaZRead.h` 一致（查表式伪 alpha，非运行时混色）。

### 2.3 SSE2 非 RLE 改造要点（相对 RLE 的差异）

| 要点 | 说明 |
|---|---|
| **无解码循环** | 整段 run 可直接 8/16 像素批处理，**这是非 RLE 比 RLE 更适合 SIMD 的根本原因** |
| **透明位图** | `pcmpeqb` vs 0 + `pmovmskb` 一次得 16 像素透明掩码；全透明块跳过，全不透明块可整块向量 |
| **src/dst/zBuf 齐头并进** | 每像素三指针同步推进（位置对齐密集流），批处理可无条件 `src += n`（与 RLE 的游程跳过不同） |
| **zBuf 环绕** | 与 RLE §5.4 第 5 条相同：一批 8 像素可能跨 `BufferEnd`，需「本批最大安全长度」或一分为二 |
| **Darken** | 8px/拍：`movdqu` 读 dst → `psrlw 1` + `pand mask` → 掩码写回。收益最高 |
| **Lucent** | `psrlw/pand/paddw` 一次算 8 像素；25/75 的 `*3` 用 `paddw` 两次或 `pmullw`（注意 16 位饱和，本公式不会溢出通道） |
| **Xlat 查表** | SSE2 无原生 gather（要 SSE4.1 `vpgatherdd`；目标是 SSE2 则标量查 8 个索引再 `_mm_set_epi16` 批写） |
| **BlitTrans@G** | `src` 是 16 位像素流，透明判据 `px==0`，可 `pcmpeqw` + 掩码混合，已有 Hook 实现可作模板 |
| **BlitPlain@G** | `rep movsd` 等价 memcpy，现有 Hook 的 `memcpy` 即最优，无需再改 |

---

## 3. 两簇命名档案

### 3.1 `0x531800–0x532200`：`AboutDlgCheatCluster`（Init.CPP 对话框 / 秘籍输入簇）

**perf**：`0x531D00` 桶 56 样本（0.7%）+ `0x531F00` 桶 3 样本。

| 地址 | 名称建议 | 职责 | 证据 |
|---|---|---|---|
| `0x005318C0` | `SaveRecordingValues` | 写出录制/回放参数到流（`[edx+0x30]` × 7 次） | 串 `"Saving recording values for scenario : %s"` @`0x8262A0` |
| `0x00531960` | `LoadRecordingValues` | 读入录制/回放参数（`[eax+0x24]` × 7 次） | 串 `"Loaded recording values for scenario : %s"` @`0x82637C` |
| `0x00531A00` | **`AboutDlgProc`** | 对话框过程（资源 ID `0xD4`）：`sub esp,0x288` 大栈；处理 `WM_COMMAND(0x111)` 与 `WM_USER+0x97(0x497)`；用 `GetDlgItem`+`SendMessageA(WM_SETTEXT 0x4C8/0x4CD/0x4B2)` 填版本信息 | 串 `"Version %s"` / `"Internal Version %s"` / `"Release Build: %s by %s - %s"` / `"MMX %s, Vendor: %s"` / `"Yes"`/`"No"`/`"Not available"`；调用 `0x7C8EF4`(sprintf 类)、`0x734E60`(取版本)、`0x74FDC0`/`0x74FAE0`(取构建信息) |
| `0x00531C30` | `ShowAboutDialog` | 用 `0x622650`（对话框框架，内部 `call 0x4A3B40`）创建 ID=`0xD4`、回调=`0x531A00` | `mov edx,0x531a00 / mov ecx,0xd4 / call 0x622650` |
| `0x00531CC0` | **`CheatConsole_Run`** | 创建 ID=`0xE2` 对话框（回调 `0x531F60`）→ 定位窗口（`SetWindowPos`，按 `0x8A00A4/0x8A00A8` 屏幕宽高）→ **按键捕获循环**：`0x54F000/0x54F050` 读键盘状态类（`0x87F770`），逐字符追加到缓冲 `0xA8F7B8`（上限 0x1F），与秘籍表比对，命中则翻转标志位并 `0x750920` 播放音效 | 秘籍表 @`0x825C28`：`PENGO` / `THETEAM` / `HIRES` / `TOGGLE` / `all1`/`sov1`/`tut1`；`cmp bl,0x7E`（`~`）等 |
| `0x00531F60` | `AboutDlgProc2` | 第二对话框过程（栈 `0x100`）：`WM_PAINT(0xF)` / `WM_COMMAND` 分发 ID `0x3EE/0x55C/0x683/0x684/0x686` 等 | 与 `0x531A00` 同构的 `0x622B50` 预处理 |

**热路径判定**：**否**（渲染/逻辑主路径无关）。`0x531D00` 样本落在 `CheatConsole_Run` 中段（对话框创建 + 按键轮询循环）。只有开着该对话框/秘籍输入时才会热；正常遭遇战主循环不经过。任务描述里「`0x531D00` 样本在 `0x531A0A` 大栈函数」需更正：`0x531A00` 函数于 `0x531C28` 结束，`0x531D00` 属**紧邻的 `0x531CC0`**，两者同簇。

**是否值得继续挖**：对 ra2render 的 SSE2/渲染目标 **不值得**；若要做「秘籍/菜单扩展」再挖。

### 3.2 `0x408E00–0x409800`：`BufSectorReaderClockCluster`（扇区缓冲读取 + 高精度时钟双生簇）

**perf**：`0x409300` 桶 104 样本（1.4%）—— 时钟侧。

| 地址 | 名称建议 | 职责 | 证据 |
|---|---|---|---|
| `0x00408E00` | `~BufBase` | 释放 `this+0x10` 与 this（`0x7C8B3D` = `YRMemory::Deallocate`） | — |
| `0x00408EE0` | **`BufSectorReader::ReadTo`** | 从内部缓冲 `rep movsd` 拷到目标（方向由 `this+0x14` 决定 src/dst），耗尽后 `call 0x4091C0` 续页 | 扇区表寻址 `lea ebx,[eax*8+0x20]` |
| `0x00408F80` | `BufSectorReader::ReadVia` | 同上但经底层流虚函数 `+0x30`（写）/`+0x24`（读）回调；失败写 `this+0x24 = 0x80040000` | 与 `CStreamClass`/`FileClass` 读写槽对应 |
| `0x004091C0` | `BufSectorReader::Advance` | 环形缓冲前进/翻页：`remain = end-pos-total`，按 `this+0x10` 标志选扇区，推进 `+0x2C/+0x30`，必要时 `call 0x409100` | 布局：`+0x04` 当前指针、`+0x08` 可用量、`+0x0C` 流对象、`+0x10` 标志、`+0x14` 扇区号、`+0x28/2C/30/34/38` 缓冲窗 |
| `0x004092B0` | `BufSectorReader::Reset` | 清计数、重装扇区起点、标志 `&= ~1` | — |
| `0x004092F0/0x409310/0x409320/0x409330` | `Flush / Remaining / Free / Pos` | 小 getter | — |
| `0x00409360` | **`Clock::Init`** | `QueryPerformanceFrequency` → `0x7C92D0` 缩放存 `0x87E828/0x87E82C`，安装 `0x87E848 = 0x4093C0`（QPC 路径）或 `0x4093F0`（timeGetTime 路径） | IAT：`0x7E11D8=QueryPerformanceFrequency`、`0x7E11D4=QueryPerformanceCounter`、`0x7E1530=timeGetTime` |
| `0x004093B0` | `Clock::Now` | `jmp [0x87E848]` 间接跳转 | **perf 热点本体** |
| `0x004093C0` | `Clock::NowQpc` | QPC 读取 + 缩放 | — |
| `0x004093F0` | `Clock::NowTick` | `timeGetTime` 回退，自旋对齐 `0x87E84C` 计数、处理 32 位回绕 | 含 `0x40941E` 自旋等待 |

**热路径判定**：**是（时钟侧）**。`0x4093B0/Clock::Now` 每帧多次调用（帧计时/动画/逻辑节拍），是 perf 桶 `0x409300` 的主要来源。**文件 I/O 侧**（`ReadTo/Advance`）在资源加载/MIX 读取时热，局内稳态不高。

**类归属**：symbols.json 里无对应 vtable 命中（这些是**非虚方法或 vtable 未被 RTTI 捕获**）。对象布局（扇区表 `+0x20`、双缓冲窗）与 `BufferIOFileClass`/`CDFileClass`（YRpp `CCFileClass.h`）的扇区缓冲行为同构，但 vtable 地址不重合——**不能直接套用 YRpp 类名**，建议自建 `BufSectorReader` / `Clock` 两个名字。

**是否值得继续挖**：时钟侧可挖（若要替换/校准帧节拍）；文件 I/O 侧对渲染无益，建议搁置。

---

## 4. 可选核实：`0x5D4B30` 一带

**结论：不是 MPGameMode，是 Win32 主消息泵 + 快捷键/窗口向量。此前「MPGameMode/HWND」粗归因应更正。**

| 地址 | 名称建议 | 职责 | 证据 |
|---|---|---|---|
| `0x005D4B20` | `WideWordWrap` | 宽字符按词换行（在 WORD 串里找 `<=0x20` 的分隔，`memmove`/`rep movsd` 截断） | 字符比较 `cmp dx,0x20` |
| `0x005D4BF0` | `DlgListWalk` | 遍历对话框相关链表节点（`this+0x19/0x1A` 标志、`+0x14` 步长、虚函数 `+4`） | — |
| `0x005D4C50` / `0x005D4CD0` | `InitHwndVector` / `InitAccelVector` | 静态构造 `DynamicVectorClass<HWND>` @`0xABFC90`（vtable `0x7EEC8C`）与 `DynamicVectorClass<AcceleratorTracker>` @`0xABFCB8`（vtable `0x7EECCC`），`atexit` 注册析构 | 与 symbols.json 两个模板类 vtable **精确命中** |
| `0x005D4D50` | **`MainMessagePump`** | 消息泵：`0x53E770/0x53E730`（PeekMessage 封装）取 MSG → 遍历 HWND 向量 `IsDialogMessageA` → 遍历 AcceleratorTracker `TranslateAcceleratorA` → `TranslateMessage` → `DispatchMessageA` | IAT 精确命中：`0x7E14F4/0x7E14F8/0x7E14BC/0x7E14C0` |

perf `0x5D4D00` 桶 144 样本（1.9%）主要落在 `MainMessagePump`（`0x5D4D50`）。

**单机局是否可忽略**：
- **不能忽略消息泵本身**——它在单机/联机/菜单**所有模式**下每帧运行，是 UI 输入的必经之路。
- **可以忽略它对渲染优化的意义**——与 blit、单位绘制、寻敌无关；ra2render 的 SSE2 补全不必覆盖。
- 邻近的 `MultiplayerGameMode` 等 vtable（`0x5D7F20` 等）只是 RTTI 地址相近，**不是本簇代码**；真 MP 逻辑在 `0x5C0xxx–0x5D0xxx` 的 `*GameMode` 虚函数里，单机遭遇战用不到那些。

---

## 5. 建议 Hook 表（非 RLE 下一批 5 个）

约定：只 Hook `vtable+4`；地址与 `m1_blit_targets.txt` 一致。建议按 P0→P1 顺序落地。

| # | 模板名 | vtable | Hook 位置 | 原 Blit | CallBlit0 | dtor | 建议实现 |
|---|---|---|---|---|---|---|---|
| 1 | `?$BlitTransXlatZRead@G` | `0x007E5978` | `0x007E597C` | `0x00492B00` | `0x00492BA0` | `0x0049A000` | 模板 `Xlat+UseZ`（src/dst/zBuf 每像素齐头并进） |
| 2 | `?$BlitTransDarkenZRead@G` | `0x007E5948` | `0x007E594C` | `0x00492D20` | `0x00492DB0` | `0x0049A040` | 模板 `Darken+UseZ` |
| 3 | `?$BlitTransLucent50@G` | `0x007E59C0` | `0x007E59C4` | `0x00492830` | `0x004928C0` | `0x00499FA0` | 模板 `Blend=Lucent50` |
| 4 | `?$BlitPlainXlat@G` | `0x007E5A38` | `0x007E5A3C` | `0x004924C0` | `0x00492530` | `0x00499F20` | 模板 `PlainXlat`（无透明跳过） |
| 5 | `?$BlitTransZRemapXlat@G` | `0x007E5A08` | `0x007E5A0C` | `0x00492590` | `0x00492610` | `0x00499F40` | 模板 `Xlat+UseRemap` |

第二批（P2–P3，可与上表同模板参数化一次做完）：

| 模板名 | vtable | Hook 位置 | 原 Blit |
|---|---|---|---|
| `?$BlitTransXlatZReadWrite@G` | `0x007E5888` | `0x007E588C` | `0x00493600` |
| `?$BlitTransDarkenZReadWrite@G` | `0x007E5858` | `0x007E585C` | `0x00493830` |
| `?$BlitTransLucent25@G` | `0x007E59A8` | `0x007E59AC` | `0x00492920` |
| `?$BlitTransLucent75@G` | `0x007E59D8` | `0x007E59DC` | `0x00492740` |
| `?$BlitPlainXlatZRead@G` | `0x007E5990` | `0x007E5994` | `0x00492A10` |

### 5.1 未命名簇是否值得继续挖

| 簇 | 建议 | 理由 |
|---|---|---|
| `AboutDlgCheatCluster`（`0x531A0A`） | **不挖**（渲染目标下） | 对话框/秘籍输入，非帧热路径；样本是打开 UI 时的噪声 |
| `BufSectorReaderClockCluster`（`0x408F14`） | **时钟侧可挖，I/O 侧搁置** | `Clock::Now @0x4093B0` 每帧调用，若要统一帧节拍/高精度计时可替换；文件读取与 SSE2 无关 |
| `MainMessagePump`（`0x5D4B30`） | **不挖** | Win32 消息泵，单机也不能旁路；与渲染解耦 |

### 5.2 与现有 Hook 的衔接

现有 5 个非 RLE Hook（`Hook_BlitTransXlatAlphaZRead` / `Hook_BlitTransXlat_G` / `Hook_BlitTrans_G` / `Hook_BlitTransDarken_G` / `Hook_BlitPlain_G`）签名正确（8 参 `ret 0x20`），可直接沿用 `FnBlit8Arg`。新 Hook 建议：

1. 共用一个 `template<class Blend, bool UseZ, bool WriteZ, bool UseRemap, bool Opaque>` 非 RLE 模板（比 RLE 模板少 `UseWarp`/`EncodedLen`）。
2. `this` 视图继续用 `BlitterCore`/`BlitterDarkenCore` 拆分（现有代码已区分 DarkenMask）。
3. 与 RLE 模板最大差异：**没有 EncodedLen/overshoot/zmap**，且 src/dst/zBuf 每像素齐头并进；不要把 RLE 的游程跳过习惯抄进来。

---

## 6. 未决问题

1. **src 推进时机（已核实，留档防回退）**：非 RLE 全族（Trans / Plain / Alpha / Darken × Z）**每像素都 `src++`**，与 Z 测试结果无关；Z 失败只跳过「读索引做混合」这一步。因此批处理可无条件 `src += n`。YRpp 头把 `*src++` 写在 Z 分支内属于等价简化，不是「Z 失败不推 src」。**请勿**把 RLE 的 zmap/游程推进语义套到非 RLE 上。
2. **`BlitTrans@G` 的 src 是 16 位像素流**（`mov ax,[ecx]`）—— **锚点（ASM-FIX-3 · 2026-09-27 已定谳）：`0x007BC8A3: 66 8B 01`**（`BlitTrans@G` 本体 `0x007BC890`，`ret 0x20`；循环体 `mov ax,[ecx]` → `add ecx,2` → `test ax,ax` → `je`（跳色键）→ `mov [edx],ax` → `add edx,2` → `dec esi` → `jne`，独立反汇编复核）【A 类 · [实证]】，与其余 8 位索引流不同。现有 `Hook_BlitTrans_G` 已按 16 位实现，正确；但文档/清单里「透明（跳过色键）」容易误读为索引流。
3. **`0x80040000` 错误码**（`BufSectorReader`）语义未查（像 `STG_E_*` 或自定义 CD 错误），影响 `CDCheck` 路径。
4. **`Clock::Now` 的调用者**未反向追完（`0x87E848` 间接跳转无静态 xref）。若要 Hook 帧节拍，需先列全 `call [0x87E848]` / `call 0x4093B0` 的调用点。
5. **`0x531A00` 对话框资源 ID `0xD4` / `0xE2`** 未与 `.mix` 内的 UI 资源对照；若做菜单汉化/扩展再挖。
6. **Lucent 的 `BlendMask` 是否恒为 `0x7BEF`**：汇编从 `this+0x08` 读，不能硬编码（8 位或特殊模式可能不同）。
7. **非 RLE 的 Warp 变体**（`BlitTransLucent*ZReadWarp` 等）未列入 Top8：它们仅超时空传送时使用，优先级低于上表；需要时可复用 RLE §4.8 的 `dst[warpOffset]` 采样语义（注意非 RLE 无 zmap）。
8. **`0x53E770/0x53E730`**（PeekMessage 封装）未命名；若做输入子系统再挖。

---

## 附录 A：已反汇编的非 RLE Blit 一览（工作产物摘录）

| 模板 | Blit VA | 指令数 | 备注 |
|---|---|---|---|
| `BlitTransXlatAlphaZRead@G` | `0x00494B60` | 75 | 已 Hook，Alpha+Z 全家桶 |
| `BlitTransXlat@G` | `0x004912B0` | 33 | 已 Hook，P0 基准 |
| `BlitTrans@G` | `0x007BC890` | 17 | 已 Hook，16 位像素流 |
| `BlitTransDarken@G` | `0x00492670` | 22 | 已 Hook，影子 |
| `BlitPlain@G` | `0x007BC7F0` | 15 | 已 Hook，memcpy |
| `BlitTransXlatZRead@G` | `0x00492B00` | 40 | **P0 建议** |
| `BlitTransDarkenZRead@G` | `0x00492D20` | 37 | **P0 建议** |
| `BlitTransLucent50@G` | `0x00492830` | 40 | **P1 建议** |
| `BlitTransLucent25@G` | `0x00492920` | 36 | P3 |
| `BlitTransLucent75@G` | `0x00492740` | 36 | P3 |
| `BlitPlainXlat@G` | `0x004924C0` | 24 | **P1 建议** |
| `BlitTransZRemapXlat@G` | `0x00492590` | 32 | **P2 建议** |
| `BlitTransXlatZReadWrite@G` | `0x00493600` | 44 | P2 |
| `BlitTransDarkenZReadWrite@G` | `0x00493830` | 41 | P3 |
| `BlitPlainXlatZRead@G` | `0x00492A10` | 36 | P3，不透明 + Z；src 推进与 Trans 族一致（每像素都推） |
| `BlitTransLucent50ZRead@G` | `0x00492F30` | 50 | 组合变体 |
| `BlitTransXlatAlpha@G` | `0x00493DF0` | 61 | Alpha 族，结构同 RLE §4.9 |
| `BlitTranslucent50NonzeroAlpha@G` | `0x00494920` | 47 | Alpha 写回，特效路径 |

完整反汇编：`out/re_work/disasm_nonrle_priority.txt`。

## 附录 B：命名对照速查

| 地址簇 | 建议名 | 一句话定性 | 热路径 |
|---|---|---|---|
| `0x531800–0x532200` | `AboutDlgCheatCluster` | Init.CPP 对话框（关于框）+ 秘籍输入循环 + 录制值存取 | 否 |
| `0x408E00–0x409354` | `BufSectorReader` | MIX/CD 扇区缓冲读取（rep movsd + 环形窗） | 加载时 |
| `0x409360–0x4093FF` | `Clock`（QPC/timeGetTime） | 高精度时钟，`Now @0x4093B0` | **是** |
| `0x5D4B20–0x5D4E80` | `MainMessagePump` | Win32 消息泵 + HWND/AcceleratorTracker 向量 | 是（但与渲染无关） |
