# R1｜渲染/Blitter 族 09-28 新结论并入 atlas §1 / §2.1（锚定补丁块交付）

> **执行方**：DSH 子代理 `atlas-r1-render`（Agent Teams 成员） ｜ **任务**：共享任务 `task-1`（流 R1 渲染/Blitter）
> **基线二进制**：`ra2youli/gamemd.exe`（YR 1.001）MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`，4,825,360 字节，ImageBase `0x400000`，FileOffset = VA − 0x400000（.text/.rdata/.data 三段 VA−rawptr 均为 0，等价）
> **本文件不修改 atlas**：`docs/re/ARCHITECTURE_ATLAS.md` 由 Lead 独占写入；本流只产出下列**锚定补丁块**供 Lead 机械套用。所有 atlas 行号均为**本流快照**（atlas mtime 2026-09-27 22:22:08，读为 2,001 行）；每个锚点行的「前 40 字符原文」已实跑 grep 校验唯一命中（`hits=1`）。
> **证据等级**：[实证] = VA + FileOffset + 原始机器码字节（本流只读复算，脚本与 dump 见 `out/re_work/atlas_rev/R1/`）/ [推演] / [待实测]。未在真机运行过的一律标 [待实测]，本文件不含任何伪造实测。

---

## 0. 补丁块总览（9 块）

| 补丁 | 动作 | 目标锚点（atlas 现行行号） | 一句话 |
|:---|:---|:---|:---|
| PATCH-R1-01 | INSERT_AFTER | L176 | 族级数量口径 108 = 57 + 51；两族基类虚表 `0x007E5B88` / `0x007E5BA0` |
| PATCH-R1-02 | INSERT_AFTER | L236 | 3 槽 vs 5 槽结构 + CallBlit0 转发（`ret 0x2c` / `ret 0x24`） |
| PATCH-R1-03 | REPLACE_BLOCK | L242（覆盖 L242–L249） | **推翻**「固定 12 字节」→ 4/8/12/16 四级尺寸矩阵 + `+0x08` 越界红线 |
| PATCH-R1-04 | INSERT_AFTER | L327 | Z 测试判定式（`*zBuf > zMin` vs `*zBuf > zMin − zmap`）与 WriteZ 回写差异 |
| PATCH-R1-05 | INSERT_AFTER | L341 | 阶段 A 越界补偿 overshoot + `zmap` 禁改硬约束 |
| PATCH-R1-06 | REPLACE_BLOCK | L348（覆盖 L347–L351） | §1.6 吞吐口径勘误（撤回「>40%」）+ 遥测口径红线 |
| PATCH-R1-07 | APPEND_SECTION | L356（插在本行**之前**） | 新增 §1.7 五正交原语矩阵 + Alpha 伪 alpha + 8 位 `@E` |
| PATCH-R1-08 | APPEND_SECTION | L356（插在 **PATCH-R1-07 之后**、本行之前） | 新增 §1.8 Hook 覆盖率 6/108 + Top10 接管排序 + 插桩规格 |
| PATCH-R1-09 | INSERT_AFTER | L427 | §2.1 补「单位绘制接口收敛点」`Draw_SHP 0x00437A10` → 虚表槽 1 |

**应用顺序（避免锚点漂移）**：R1-03 → R1-06 → R1-01 → R1-02 → R1-04 → R1-05 → R1-09 → R1-07 → R1-08。即「先 REPLACE_BLOCK 类，再 L356 上的两次 APPEND_SECTION（R1-07 必须先于 R1-08）」。若按「行号从大到小」应用，L356 上的两块需反向（R1-08 先插）才能保持 §1.7 在 §1.8 之前。

---

## PATCH-R1-01  补「微内核族级数量口径 + 两族基类虚表」

- **目标锚点**：atlas **L176** ｜ 该行前 40 字符原文：`- **载具、建筑、单位重叠深度混合** 采用 **密集无压缩像素流`（grep 实跑：`hits=1 → 176`）
- **动作**：INSERT_AFTER
- **现状问题**：atlas §1 开篇只给「RLE 变长游程 / 密集无压缩」两条族性描述，**没有任何数量口径，也没有两族基类虚表**。09-28 主来源 `rle_blit_family.md:12-19`（RLEBlitter 基类 vtable `0x007E5BA0`、51 个实现 = 39 `@G` + 12 `@E`）与 `blit_coverage_top10.md:12,96-104`（Blitter 57 + RLEBlitter 51 = 108）带来的族级口径在 atlas **0 命中**；缺此口径时，§1.1 的 10 行表无法被判断是「全族」还是「抽样」。
- **替换文本**：

````markdown
**族级数量口径与两族基类虚表**〔2026-09-28 · R1 并入；[实证] `rle_blit_family.md:12-19`、`blit_coverage_top10.md:12,96-104`〕：

| 族 | 基类虚表 | 虚函数槽数 | 具体实现数 | 位深构成 |
|:---|:---:|:---:|:---:|:---|
| `RLEBlitter`（RLE 变长游程族） | `0x007E5BA0` | **3**（dtor / Blit / CallBlit0） | **51** | `@G` 16 位 RGB565 **39** + `@E` 8 位调色板 **12** |
| `Blitter`（密集像素族） | `0x007E5B88` | **5**（dtor / Blit / CallBlit0 / CallBlit1 / CallBlit2） | **57** | `@G` **50** + `@E` **7** |
| **合计** | — | — | **108** | — |

- **槽数实测**：`0x7E5B88` 之后第 6 个 dword 为 .rdata RTTI 指针（非代码指针）⇒ 恰 5 槽；`0x7E5BA0` 之后第 4 个 dword 为 `0x00000000` ⇒ 恰 3 槽 [实证]（字节：`0x7E5B88 = C0 9C 49 00 50 91 4C 00 50 91 4C 00 50 91 4C 00 50 91 4C 00 F8 F4 7F 00`、`0x7E5BA0 = A0 9D 49 00 50 91 4C 00 50 91 4C 00 00 00 00 00`）。
- **数量独立复算（RTTI 修饰名普查，不采信来源文档）**：全 exe 内 `?$Blit*@G@@/@E@@` 去重 **57**，`?$RLEBlit*@G@@/@E@@` 去重 **51**；其中 `@G` = 50 / 39，`@E` = 7 / 12，与上表逐格一致 [实证]（首命中 VA `0x81ED0C = 3F 24 52 4C 45 42 6C 69 74 54 72 61 6E 73 58 6C 61 74 40 47 40 40` = `"?$RLEBlitTransXlat@G@@"`）。
- `@E` 族与 `@G` 族**解码循环逐字节同构**，仅像素宽度（1 字节 vs 2 字节）与查表宽度（`uint8_t*` vs `uint16_t*`）不同 [实证] `rle_blit_family.md:278-285`。
````
- **证据**：[实证] vtable 槽数（本流只读复算）+ RTTI 修饰名普查 57/51/39/12/7；来源 `docs/re/rle_blit_family.md:12-19`、`docs/re/blit_coverage_top10.md:12,96-104`；字节断言见 `out/re_work/atlas_rev/R1/claims_R1.txt` 段 B/F。
- **影响面**：§1.1（本节口径是 §1.1 表的族员依据）；**§11.2 虚表总表**（建议补 `Blitter`/`RLEBlitter` 基类虚表 2 行与「槽数」列）；§11.1 无影响；§12 契约无影响；§0 准则无影响。

---

## PATCH-R1-02  补「RLE 3 槽 / 非 RLE 5 槽结构 + CallBlit0 转发实证」

- **目标锚点**：atlas **L236** ｜ 该行前 40 字符原文（整行仅 39 字符，故给全行）：`> Hook 挂接只需原子改写 `vtable + 4`（即 Slot 1）。`（grep 实跑：`hits=1 → 236`）
- **动作**：INSERT_AFTER
- **现状问题**：atlas §1.1 只断言「只需改写 Slot 1」，**未给两族槽数差异，也未说明 CallBlit0 的存在与转发机制**。09-28 `rle_blit_family.md:19-27,79` 的「RLE 3 槽 / CallBlit0 内部 `call [vtable+4]` 转发 / `ret 0x2c`」在 atlas **0 命中**；缺此条时工程侧无法判断「是否还要额外拦截槽 2」。
- **替换文本**：

````markdown
> **槽结构与 CallBlit0 转发实证（2026-09-28 · R1 并入）[实证]**
> - **RLE 族**：每个具体类恰 **3 槽**（`+0x00` 析构 / `+0x04` Blit / `+0x08` CallBlit0）；**非 RLE 族**恰 **5 槽**（`+0x00` 析构 / `+0x04` Blit / `+0x08` CallBlit0 / `+0x0C` CallBlit1 / `+0x10` CallBlit2）。实例：`0x007E55C0`（`RLEBlitTransXlat@G`）= `60 A7 49 00 / A0 60 49 00 / 30 61 49 00` + RTTI 指针；`0x007E5978`（`BlitTransXlatZRead@G`）= 5 槽 `0049A000 / 00492B00 / 00492BA0 / 00492B70 / 00492BD0`。
> - **CallBlit0 是薄包装**：把参数重新压栈后走虚表间接调用 —— `0x00496164: FF 50 04 call dword ptr [eax+4]`（`eax = [ecx] = vtable`），随后 `0x00496167: C2 2C 00 ret 0x2c`（11 DWORD = 10 实参 + 1 个 `useless`）[实证]（`rle_blit_family.md:79`）。
> - **非 RLE 族 CallBlit0 同构但栈帧更小**：`0x00492BC7: FF 50 04 call dword ptr [eax+4]` → `0x00492BCA: C2 24 00 ret 0x24`（9 DWORD = 8 实参 + 1 个 dummy）[实证]。
> ⇒ **只改写 `vtable + 4` 即可同时覆盖 Blit 与 CallBlit0 两条入口**（CallBlit0 转发时自动落到新实现），无需单独拦截 `+0x08`；这与本 atlas 既有 Hook 口径自洽。
````
- **证据**：[实证] `0x496130`（CallBlit0 序言 `8B 54 24 28 8B 01`）、`0x496164`（`FF 50 04`）、`0x496167`（`C2 2C 00`）、`0x492BC7` / `0x492BCA`，以及上表 vtable 槽数；来源 `docs/re/rle_blit_family.md:19-27,79,530-537`、`docs/re/blit_coverage_top10.md:92,102`、`docs/re/nonrle_blit_and_named_hotspots.md:57`。
- **影响面**：§1.1（与既有 Hook 口径一致，仅补充依据）；**§11.2**（建议补「槽数」列）；§12.4 补丁生命周期（CallBlit0 无需重复挂接 ⇒ 减少 1 处 Hook 面）；§0 准则无影响。

---

## PATCH-R1-03  §1.2 推翻「所有 Blitter 实例固定 12 字节」→ 尺寸矩阵 + `+0x08` 越界红线

- **目标锚点**：atlas **L242** ｜ 该行前 40 字符原文：`在西木引擎的工厂函数（`0x0048FAF8`–`0x0048FC98`）中，所`（grep 实跑：`hits=1 → 242`）
- **动作**：REPLACE_BLOCK（**覆盖 L242–L249**：L242 正文 1 行 + L243 空行 + L244–L249 的围栏布局图块）
- **现状问题**：atlas §1.2 断言所有 Blitter 实例由 `push 0x0C` 分配、**固定 12 字节**，并把 `+0x08` 描述为「变体辅助参数/掩码」。两处均有实证反证：① 09-27 S13（`blitter_microkernel_deep_dive.md:1028-1037` / `re_sprint_S13_report.md:17,58,65-72`）已证「4/8/12/16 四级分配」，**该纠正从未并入 atlas**；② 本流独立复算给出逐 vtable 的分配尺寸：**全部 P0 微内核（步兵/载具本体与影子主路径）实测仅 8 字节**。后果：按 atlas 现文的 12 字节统一结构体实现，在 8 字节对象上访问 `+0x08` 即**堆越界 4 字节**（内存破坏，且不保证立刻崩溃 ⇒ 极难定位）。
- **替换文本**：

````markdown
在西木引擎的 Blitter 工厂（入口 `0x0048EBF0`，入口前为 `90` 填充：`0x48EBEC = 90 90 90 90`；S13 定名 `ConvertClass::Init_Blitters`）中，对象尺寸**按成员数分级分配**（`push <size>; call operator new (0x007C8E17)`），**并非固定 12 字节**〔**勘误 · R1 · 2026-09-28**：本节原记「所有 Blitter 实例…固定为 12 字节」**错**；实测为 4 / 8 / 12 / 16 四级（四级分类的首次提出见 `blitter_microkernel_deep_dive.md:1028-1037`，本块的逐 vtable 尺寸与字节锚点为本流独立复算）〕：

```
[ Blitter 对象内存规格分类（本流实测） ]
 4 字节：无成员变体（vtable 指针即全部内容）
 8 字节：单成员变体（vtable + 1 个 4 字节槽）—— 全部 P0 微内核均属此类
12 字节：双成员变体（vtable + 2 个 4 字节槽）
16 字节：三成员复合变体（vtable + 3 个 4 字节槽）
```

逐 vtable 分配尺寸实证（工厂内 `push imm` → `call 0x007C8E17` 成对识别；113 处分配点的尺寸直方图 = 4×2 / 8×24 / 12×57 / 16×30）[实证]：

| 变体 | vtable | 分配指令（VA: 字节） | 对象尺寸 | `this + 0x04` | `this + 0x08` |
|:---|:---:|:---|:---:|:---|:---|
| `RLEBlitTransXlat@G` | `0x007E55C0` | `0x0048FAE8: 6A 08` | **8** | `uint16_t* XlatTable`（`0x48FB02: 89 48 04` 写 32 位指针） | **越界（不存在）** |
| `RLEBlitTransDarken@G` | `0x007E55A0` | `0x0048FB3F: 6A 08` | **8** | `uint16_t DarkenMask`（值） | **越界** |
| `RLEBlitTransXlatZRead@G` | `0x007E5560` | `0x0048FBFE: 6A 08` | **8** | `uint16_t* XlatTable` | **越界** |
| `RLEBlitTransDarkenZRead@G` | `0x007E5540` | `0x0048FC55: 6A 08` | **8** | `uint16_t DarkenMask`（`0x48FC70: 66 89 48 04` 写 16 位值） | **越界** |
| `RLEBlitTransZRemapXlat@G` | `0x007E55B0` | `0x0048FB0F: 6A 0C` | 12 | `uint8_t** pRemap`（二级指针） | `uint16_t* XlatTable` |
| `RLEBlitTransLucent50@G` | `0x007E5580` | `0x0048FB9A: 6A 0C` | 12 | `uint16_t* XlatTable` | `uint16_t BlendMask` |
| `BlitTransXlat@G` | `0x007E5A20` | `0x0048F075: 6A 08` | **8** | `uint16_t* XlatTable` | **越界** |
| `BlitTransDarken@G` | `0x007E59F0` | `0x0048F0C6: 6A 08` | **8** | `uint16_t DarkenMask`（值） | **越界** |
| `BlitTransXlatZRead@G` | `0x007E5978` | `0x0048F19D: 6A 08` | **8** | `uint16_t* XlatTable` | **越界** |
| `BlitTransDarkenZRead@G` | `0x007E5948` | `0x0048F1EE: 6A 08` | **8** | `uint16_t DarkenMask`（值） | **越界** |
| `BlitTransLucent50@G` | `0x007E59C0` | `0x0048F11B: 6A 0C` | 12 | `uint16_t* XlatTable` | `uint16_t BlendMask` |

> [!CAUTION] 结构体越界红线（2026-09-28 · R1 新增）：
> 上表加粗的 8 字节变体恰是**步兵/载具本体与影子主路径（P0）**。若按「统一 12 字节」声明成员并在 `this+0x08` 读/写，即对该分配块**越界 4 字节**（堆块尾部踩踏 ⇒ 不可恢复的内存破坏，且不保证立刻崩溃）。Darken 变体另有更早的既有红线：`this+0x04` 是**掩码数值**（`66 89 48 04` 写 16 位）而非指针，按 `uint16_t*` 解引用必触发 `EXCEPTION_ACCESS_VIOLATION (0xC0000005)`（见本节下方既有 CAUTION）。

> **工厂范围口径补正**：本节原记 `0x0048FAF8–0x0048FC98` 只是该工厂中「RLE 16 位段」的一小段；完整工厂主体自 `0x0048EBF0` 起（8 位/16 位双管线在 `0x0048EBF6: 83 7E 04 01 / 0F 85 54 04 00 00` 处分流）[实证]。
````
- **证据**：[实证] 分配点与 vtable 落位字节（`claims_R1.txt` 段 A：`0x48FAE8` / `0x48FB3F` / `0x48FBFE` / `0x48FC55` / `0x48FB0F` / `0x48FB9A` / `0x48F075` / `0x48F0C6` / `0x48F19D` / `0x48F1EE` / `0x48F11B`）；成员写宽对照 `0x48FC70 = 66 89 48 04`（16 位值）vs `0x48F1BA = 89 48 04`（32 位指针）；尺寸直方图（4×2/8×24/12×57/16×30）由 `out/re_work/atlas_rev/R1/scan_factory_allocs3.py` 全量扫描得出，dump 见 `dump_factory_sizes.txt`；来源 `docs/re/blitter_microkernel_deep_dive.md:1028-1037,1039-1072`、`docs/re/re_sprint_S13_report.md:58,65-72`。
- **影响面**：**§1.1/§1.3/§1.5 无影响**；**§11.2 虚表总表**（建议补「对象尺寸」列）；**§12.4** 补丁生命周期（结构体声明属工程侧，需与 `ra2render.h` 同步纠正）；**对产品决策是阻断项**——按 12 字节声明将在 P0 路径越界；§0 准则无影响。

---

## PATCH-R1-04  §1.4 补「Z 测试判定式 + WriteZ 回写值（RLE vs 非 RLE）」

- **目标锚点**：atlas **L327** ｜ 该行前 40 字符原文：`> `BufferSize`（`+0x20`）记录的是**字节数**（即 `Wi`（grep 实跑：`hits=1 → 327`）
- **动作**：INSERT_AFTER
- **现状问题**：atlas §1.4 只给 Z 缓冲描述符与环绕逻辑；**带深度测试变体的判定不等式、`zmap` 的角色、两族 WriteZ 回写值差异**在 atlas 0 命中。09-28 `rle_blit_family.md:182-197` 与 09-27 `blitter_microkernel_deep_dive.md:1142-1153` / `re_sprint_S13_report.md:19-22,87-138` 均已定谳。缺此条时，SSE2 接管会把深度测试写反（前后景颠倒）或回写错误深度值（破坏排序）。
- **替换文本**：

````markdown
**Z 测试判定式与深度回写（2026-09-28 · R1 并入）[实证]**：

| 变体族 | 判定指令与 VA | 像素绘制条件 | WriteZ 回写值 |
|:---|:---|:---|:---|
| 非 RLE `*ZRead` | `0x00492B28: 39 54 24 20 cmp [esp+0x20], edx`（`edx = *zBuf`）→ `0x00492B2C: 7D 24 jge` | **`*zBuf > zMin`** 时通过 | `0x0049364D: 66 89 28 mov [eax], bp` ⇒ 回写 **`zMin`** |
| RLE `*ZRead` | `0x004968A6: 0F BE 01 movsx eax, byte [ecx]` → `0x004968B0: 2B F8 sub edi, eax` → `0x004968B9: 3B F8 cmp edi, eax` → `0x004968BB: 7D 11 jge` | **`*zBuf > zMin - *zmap`** 时通过 | `0x004971C1: 66 89 18 mov [eax], bx` ⇒ 回写 **`(uint16_t)(zMin - *zmap)`** |

- `zmap`（RLE 专属，`arg10`）是 **`int8_t*`**：汇编以 `movsx` 读取（`0x004968A6`），负值抬高阈值 `zMin - zmap`；差值以 `uint16_t` 截断后再比较/回写。非 RLE 族**无 `zmap`**（参数表里根本没有该槽）。
- Z 未通过的像素**仍要推进 `dst`/`zBuf`** —— 非 RLE 是三者齐头并进（`0x00492B55: 43 83 C7 02 inc ebx / add edi,2` 位于 `jge` 目标之后，两条路径都执行）；RLE 是 `0x004968CE: 4B 83 C6 02 dec ebx; add esi,2` 照常推进。
- Alpha 变体的 `aBuf` 走**另一套同布局描述符** `*(void**)0x0087E8A4`（`+0x1C` BufferEnd / `+0x20` BufferSize），环绕规则与 Z 缓冲一致 [实证] `rle_blit_family.md:180`。

> **地址属性提示**：`0x00887644` / `0x0087E8A4` / `0x0089C568` 位于 .data 的虚拟尾部（.bss，`VSize 0x367BE4` > `RawSize 0x6C000`）⇒ **无文件字节可断言**，只能断言「该地址处的运行时指针」与布局偏移；不得对这些地址写字节级 claim [实证]。
````
- **证据**：[实证] `0x492B22 = 66 8B 10 83 C0 02 39 54 24 20 7D 24`；`0x4968A6 = 0F BE 01`、`0x4968B0 = 2B F8`、`0x4968B9 = 3B F8`、`0x4968BB = 7D 11`；`0x49364D = 66 89 28`、`0x4971C1 = 66 89 18`；`0x492B55 = 43 83 C7 02`、`0x4968CE = 4B 83 C6 02`（本流只读复算）；来源 `docs/re/rle_blit_family.md:182-197,169-180`、`docs/re/blitter_microkernel_deep_dive.md:1142-1153`、`docs/re/nonrle_blit_and_named_hotspots.md:16,32-33,100-111`。
- **影响面**：§1.6 SSE2 设计（Z 测试符号位翻转策略的前提）；**§11.2**（建议补 `zmap` 有无）；§12 确定性契约（Z 回写影响像素输出，MP 需门控）；§0 准则无影响。

---

## PATCH-R1-05  §1.5 补「阶段 A 越界补偿（Overshoot）+ zmap 禁改硬约束」

- **目标锚点**：atlas **L341** ｜ 该行前 40 字符原文：`  将解压出的像素通过 `XlatTable` 查表着色，或根据 `Darken`（grep 实跑：`hits=1 → 341`）
- **动作**：INSERT_AFTER
- **现状问题**：atlas §1.5 的两阶段状态机缺 **阶段 A 越界补偿（overshoot）** 这一步，也缺「`zmap` 在 overshoot 处不推进 = 原版缺陷、严禁纠正」的硬约束。09-28 `rle_blit_family.md:133-151,486-498,741-814` 与 `blit_coverage_top10.md:245-253` 均属 0 命中；而这是 ra2render 补全实现时像素等价性的**头号雷区**（错 1 像素即整行错位）。
- **替换文本**：

````markdown
**阶段 A 越界补偿（Overshoot）与 `zmap` 禁改约束〔2026-09-28 · R1 并入；[实证]〕**：

阶段 A 以「解码消耗像素」递减 `EncodedLen`。一旦左裁剪边界**切碎一个透明游程**，该游程会整段扣减而越过边界（`EncodedLen` 变负）⇒ 必须补偿，否则整行整体错位 1~255 像素：

```asm
; RLEBlitTransXlat@G (0x004960A0) 阶段 A → B 交界
0x004960CA: 8B 7C 24 18      mov  edi, [esp+0x18]   ; edi = Length
0x004960CE: F7 DA            neg  edx               ; edx = overshoot = -EncodedLen >= 0
0x004960D0: 2B FA            sub  edi, edx          ; Length -= overshoot
0x004960D2: 8D 04 50         lea  eax, [eax+edx*2]  ; dst += overshoot（16 位步进）
; RLEBlitTransXlatZRead@G (0x004965B0) 同段，多出 zBuf 补偿与环绕检查
0x004965EC: F7 D8            neg  eax               ; overshoot
0x004965EE: 2B D8            sub  ebx, eax          ; Length -= overshoot
0x004965F0: 8D 3C 47         lea  edi, [edi+eax*2]  ; dst  += overshoot*2
0x004965F3: 8D 04 42         lea  eax, [edx+eax*2]  ; zBuf += overshoot*2  ← 注意：zmap 不在此列
0x004965F6: 8B 15 44 76 88 00  mov edx, [0x00887644]
0x004965FC: 3B 42 1C         cmp  eax, [edx+0x1C]   ; zBuf 环绕检查
0x004965FF: 72 03            jb   0x00496604
0x00496601: 2B 42 20         sub  eax, [edx+0x20]   ; -= BufferSize（字节口径）
```

- **阶段 B 的 `zmap` 推进规则**：透明游程 `0x00496636: 03 C8 add ecx, eax`（`zmap += n`）；实体像素 `0x0049664C: 41 inc ecx`（`zmap++`，**在 Z 测试 `jge` 之前无条件执行**，通过与否都推进）。
- **调用方解释了阶段 A 为何不碰 `zmap`**：`Draw_SHP`（`0x00437A10`）在 `0x00437C1A: 03 C2 add eax, edx` 处已把 `zmap` 指针**预加了 `EncodedLen`**，因此阶段 A 天然无需推进。
- **★ 但 overshoot 处不推进 `zmap` 是原版缺陷（off-by-overshoot）**：`0x004965F0`/`0x004965F3` 推了 `dst`/`zBuf` 却未推 `zmap`（存 `zmap` 的 `ecx` 在该段无任何写操作）。常规渲染的 `zmap` surface 为 NULL，兜底到全零缓冲 `0x0089C568`（`0x00437CCC: C7 44 24 10 68 C5 89 00`），任何偏移后读数皆为 0 ⇒ 长期未暴露。[实证：汇编与兜底路径 / 推演：缺陷归因]
- **SSE2 接管硬约束**：**必须 1:1 复现原版行为（overshoot 处不动 `zmap`），严禁擅自「修正」该偏移**。同理，RLE 族**没有不透明 run** —— 不透明段就是连续非零字节，**解码循环必须保持标量**，SIMD 只能用于像素写入/混合阶段 [实证] `rle_blit_family.md:29,128,458-484`。
- **透明游程 `00 00`**（消耗 2 字节、0 像素）是合法空游程，**非终止符**；码流末尾无哨兵，循环以像素预算耗尽为终点（本节既有表述保持成立，此处补上「无 run」这一条约束）。
````
- **证据**：[实证] 字节断言 `claims_R1.txt` 段 C/E：`0x4960CA = 8B 7C 24 18 F7 DA 2B FA 8D 04 50`、`0x4965EC = F7 D8 2B D8 8D 3C 47 8D 04 42`、`0x496636 = 03 C8`、`0x49664C = 41`、`0x437C1A = 03 C2`、`0x437CCC = C7 44 24 10 68 C5 89 00`；来源 `docs/re/rle_blit_family.md:133-151,486-498,741-814`、`docs/re/blit_coverage_top10.md:238-253`。
- **影响面**：§1.6（SSE2 边界条件）；**§12 契约**——本约束直接决定像素等价性，属「渲染像素等价性红线」，MP 场景需门控/对拍验收；§11 速查表（建议在 RLE 族条目加「overshoot/zmap 陷阱」列注）；§0 准则无影响。

---

## PATCH-R1-06  §1.6 吞吐口径勘误：撤回「>40%」+ 补遥测口径红线

- **目标锚点**：atlas **L348** ｜ 该行前 40 字符原文：`  在 1080p（1920×1080）分辨率下，每帧视口约需重绘 200 万像`（grep 实跑：`hits=1 → 348`）
- **动作**：REPLACE_BLOCK（**覆盖 L347–L351**：第 1 条 bullet 及其续行 + 第 2 条 bullet 与两条子项，至 L351 止；L345 小节标题与 L352 空行保持不动）
- **现状问题**：① §1.6 的「L1/L2 缓存与流水线停顿占整机耗时超 40%」**无来源、无证据等级标注**，且与项目可溯源口径冲突：perf 采样给出 blit 族占忙时 **11.55% → 16.55%**；② 该采样场景已被判**作废**（基准图真机只实例化 21/22 单位，非地图负载），`blit_coverage_top10.md:363-365` 附录 L1 与 `rle_blit_family.md:44` 均有 Lead 就地判定；③ §1.6 未声明 **ra2render-telemetry 只有总量、无按函数分解** 这一前置口径，容易被误读为「已做过 per-func 度量」。
- **替换文本**：

````markdown
- **数据吞吐特征（口径修正 · 2026-09-28 R1）**：
  - 〔**勘误 · R1**：本节原记「L1/L2 缓存与流水线停顿占整机耗时超 40%」**无来源、无证据等级，予以撤回**；引用本节的任何文档必须改用下述可溯源口径。〕
  - **已有采样（降级为方向性提示，不得作低负载热点证据）**：`out/reverse/perf-profile.md` 与 `docs/REWRITE_RESEARCH.md:168-181` 报 blit 族占忙时 **11.55% → 16.55%**，其中 `BlitTransXlatAlphaZRead@G` 在复杂场景独占 **15.64%**（已 Hook）、`BlitPlain@G` 0.7%（已 Hook）。其采样场景 `U0800_Accelerated_Skirmish` 真机**只实例化 21/22 单位**（国家默认开局部队，非地图负载）⇒ **已由 H1VOID 判作废**，仅作方向性提示 [实证：来源文档 + Lead 判定]。
  - **遥测现状（口径红线）**：`ra2render.log` 的 `[ra2render-telemetry]` 行仅含**总量**字段（`BlitCalls` / `BlitPixels` / `TargetScans` 等，3153 条），**不存在任何按函数/按模板分解**的字段 ⇒ 任何「每函数调用数 × 像素」的分布必须**真机插桩**取得，**不得以估算代替** [实证] `blit_coverage_top10.md:20-47`。
  - **静态可得的排序依据**：108 个实现入口的直接 `call/jmp` 命中数 **= 0**（虚函数经 `call [vtable+4]` 间接派发），静态 xref 只能给出「虚表地址被字面引用次数」（量级 2–4，区分度不足）⇒ 优先级排序目前只能依据**像素语义/结构**与既有定谳文档，并以 H1 重测校准 [实证] `blit_coverage_top10.md:131-167`。
  - **量级旁证（[推演]，非同一 run）**：日志总量峰值 18.6M calls / 1460 Mpx 出现在复杂场景段，与上述 16.55% 量级吻合，仅作旁证。
- **SSE2 向量化设计模式（保留原设计，补两条前提与一条防护）**：
  - **前提 1（能否向量化）**：RLE 族**解码循环不可向量化**（不透明段是连续非零字节，无 run 头），收益只在像素写入/混合阶段；非 RLE 族因「密集对齐流、无变长状态机」才具备整段 8/16 像素批处理条件 [实证] `rle_blit_family.md:458-484`、`nonrle_blit_and_named_hotspots.md:150-163`。
  - **前提 2（寄存器粒度）**：8 个 RGB565 像素 = 16 字节，`movdqu` 正好一拍，这是唯一能满载的粒度。
  - **Darken 影子变暗**：`_mm_srli_epi16(dst, 1)` 结合 `_mm_and_si128(..., mask)`，单指令并行处理 8 个 16-bit 像素；**`mask` 必须取 `this+0x04` 的 `DarkenMask` 值，严禁硬编码 `0x7BEF`**（8 位或特殊模式不同）[实证] `rle_blit_family.md:464,492`。
  - **纯色块透明复制**：使用 `_mm_cmpeq_epi16(src, zero)` 生成 8 像素透明掩码，通过 `_mm_blendv_epi8` 或 `_mm_or_si128` 实现无分支快速写回。
  - **环形缓冲批量越界防护（新增）**：一批 8 像素可能跨过 `BufferEnd`（`0x00887644`，`+0x1C` / `+0x20`）。进入向量主循环前先算「本批不超过 `BufferEnd` 的最大安全长度」（`(BufferEnd - zBuf)/2`），不足 8 像素则退化为标量逐像素环绕 [推演：设计规格，**仅纸面，未落地**]。
````
- **证据**：[实证] 遥测字段口径（`blit_coverage_top10.md:20-47` 3153 条 telemetry 行字段普查）+ Lead 作废判定（`blit_coverage_top10.md:359-370`、`rle_blit_family.md:44`）；[推演] 环形缓冲安全步长设计；[待实测] 两条百分比数字的重测（见 [4] 未闭环）。
- **影响面**：**§0 准则**（「禁止把估算当实测」——本节原 40% 违反该准则，故必须撤回）；**§11 速查表**（若曾引用 40%/16.55%，需同步改口径）；**§12 契约**无直接影响；其他引用 §1.6 数值的文档（如容量规划类）建议全库扫一次。

---

## PATCH-R1-07  §1.7（新增小节）像素原语正交分解与变体组合矩阵

- **目标锚点**：atlas **L356** ｜ 该行前 40 字符原文：`## 2. §2 战术主视图渲染与战争迷雾管线 (Tactical Viewpo`（grep 实跑：`hits=1 → 356`）
- **动作**：APPEND_SECTION（语义明确化：**把下列内容插入锚点行之前**，即追加到 §1 末尾，成为 §1.7）
- **现状问题**：atlas §1.1–§1.6 只给若干入口地址与 Z 缓冲/状态机，**没有五项正交原语 → 覆盖全部 @G 实现 的组合矩阵**，也没有 RLE Lucent 三档公式、ZRemap 双查表、Alpha 查表式伪 alpha 的落库。这些是 09-28 主来源的结构性结论（`rle_blit_family.md:31-41,306-355,444-453`），atlas **0 命中**；缺此节无法判断哪些变体可共用一个模板、哪些不能。
- **替换文本**（同一锚点上还有 PATCH-R1-08；本节必须先于 §1.8 插入）：

````markdown
### 1.7 Blitter 像素原语正交分解与变体组合矩阵〔2026-09-28 · R1 新增；[实证]〕

39 个 16 位 `@G` RLE 实现的像素算法并非 39 套独立逻辑，而是 **5 个正交特性的组合**（非 RLE 族复用同一组原语，仅去掉解码循环）[实证] `rle_blit_family.md:31-41`：

| # | 原语 | RGB565 写入公式 | `this` 成员 | 本流复核的汇编锚点 |
|:--:|:---|:---|:---|:---|
| 1 | **Xlat** | `*dst = XlatTable[idx]` | `+0x04 = uint16_t* XlatTable` | `0x00496106: 8B 55 04 81 E1 FF 00 00 00` → `0x00496113: 66 8B 0C 4A 66 89 48 FE` |
| 2 | **Darken** | `*dst = (*dst >> 1) & DarkenMask` | `+0x04 = uint16_t DarkenMask`（**数值**） | `0x004962AE: 66 8B 08` → `0x004962B1: 66 D1 E9 66 23 4D 04` |
| 3 | **Lucent25/50/75** | 25：`3*((s>>2)&m)+((d>>2)&m)`；50：`((s>>1)&m)+((d>>1)&m)`；75：`((s>>2)&m)+3*((d>>2)&m)`，`m = BlendMask` | `+0x04 = XlatTable`；`+0x08 = uint16_t BlendMask` | `0x00496457: 8B 69 04 66 8B 51 08` |
| 4 | **ZRemapXlat** | `*dst = XlatTable[ RemapTable[idx] ]` | `+0x04` → **二级解引用**得 256 字节 `uint8_t* RemapTable`；`+0x08 = uint16_t* XlatTable` | `0x004961E8: 8A 1C 0A 8B 55 08 66 8B 14 5A` |
| 5 | **Alpha**（查表式伪 alpha，**非运行时混色**） | `*dst = XlatTable[ AlphaRow[aBuf[i]] OR idx ]`；行号 `min(0xFE, (max(aLvl,0) * 261) >> 11)`；`AlphaRow = *(this+0x08) + (row << 9)`（512 字节/行）；生成下标用的是**按位或**（此处以 OR 代写竖线） | `+0x04 = XlatTable`；`+0x08 = Alpha 表基址` | 入口 `0x004978C0`（100 条指令，全族最复杂） |

叠加维度（不改像素公式，只改门控/寻址）：**ZRead**（`*zBuf > zMin - *zmap` 才写）、**ZReadWrite**（通过后再回写 `(uint16_t)(zMin - *zmap)`）、**Warp**（背景像素取自 `dst[warpOffset]`，**不得偷懒用 `dst[i]`**）。

- **Lucent 必须用移位 + 掩码**，禁止换成除法或其它化简：RGB565 通道边界会渗色 [实证] `rle_blit_family.md:335,464`。
- **Darken 的掩码必须读 `this+0x04`**，禁止硬编码 `0x7BEF` [实证]。
- 8 位 `@E` 族（12 个）与原语矩阵**逐字节同构**，仅像素宽度与查表宽度不同（例：`0x007E5B00` `RLEBlitTransXlat@E`，Blit `0x00491820`，vtable `80 9D 49 00 20 18 49 00 A0 18 49 00`）⇒ 可收敛为「同一模板 × 5 原语 × 门控组合 × 2 位深」。
````
- **证据**：[实证] 上表汇编锚点均经本流只读复算（`claims_R1.txt` 原语块：`0x496106` / `0x496113` / `0x4962B1` / `0x496457` / `0x4961E8` / `0x7E5B00`）；来源 `docs/re/rle_blit_family.md:31-41,306-355,444-453,278-285`、`docs/re/nonrle_blit_and_named_hotspots.md:30-39,58-65,146-148`。
- **影响面**：§1.1（原语矩阵解释表内各变体关系）；§1.3（ABI 不变）；§1.6（向量化粒度以本矩阵为依据）；§11.2（建议在虚表总表加原语组合列）；§12 无影响。

---

## PATCH-R1-08  §1.8（新增小节）Hook 覆盖率 6/108、接管优先级与真机插桩规格

- **目标锚点**：atlas **L356**（与 PATCH-R1-07 同一锚点）｜ 该行前 40 字符原文：`## 2. §2 战术主视图渲染与战争迷雾管线 (Tactical Viewpo`
- **动作**：APPEND_SECTION（**插入 PATCH-R1-07 产出的 §1.7 之后、锚点行之前**，成为 §1.8）
- **现状问题**：atlas §1 完全没有「当前 Hook 覆盖率 / 缺口口径 / 接管排序 / 如何取得实测分布」。09-28 `blit_coverage_top10.md` 的核心结论（**6/108**、102 项缺口、Top10 具名热点、遥测无 per-func 分解、可机械验证的插桩规格）在 atlas **0 命中**。缺此节时读者无法判断 §1.1 所列微内核哪些**已接管**、哪些只是**清单**，也无法复现优先级依据。
- **替换文本**：

````markdown
### 1.8 Blitter Hook 覆盖率、接管优先级与真机插桩规格〔2026-09-28 · R1 新增；[实证] 覆盖率与排序依据 / [推演] 收益档 / [待实测] 插桩〕

**覆盖率现状：6 / 108**（Blitter 57 + RLEBlitter 51 ⇒ 未覆盖 **102**）[实证] `blit_coverage_top10.md:12,79-93`；6 项均为「只改 vtable+4」口径：

| # | 修饰名 | 位深 / 语义 | 虚表 | 槽 1（已改） | 原 Blit 入口 |
|---:|:---|:---|:---:|:---:|:---:|
| 1 | `?$BlitTransXlatAlphaZRead@G` | 16 位 · 透明/Xlat/alpha/ZRead | `0x007E56F0` | `0x007E56F4` | `0x00494B60` |
| 2 | `?$BlitTransXlat@G` | 16 位 · 透明/Xlat（阵营色） | `0x007E5A20` | `0x007E5A24` | `0x004912B0` |
| 3 | `?$RLEBlitTransXlat@G` | 16 位 · RLE/透明/Xlat | `0x007E55C0` | `0x007E55C4` | `0x004960A0` |
| 4 | `?$BlitTrans@G` | 16 位 · 透明（色键；src 为 16 位像素流） | `0x007F7BF4` | `0x007F7BF8` | `0x007BC890` |
| 5 | `?$BlitTransDarken@G` | 16 位 · 透明/变暗（阴影） | `0x007E59F0` | `0x007E59F4` | `0x00492670` |
| 6 | `?$BlitPlain@G` | 16 位 · 不透明 | `0x007F7BC4` | `0x007F7BC8` | `0x007BC7F0` |

**下一步接管优先级 Top10（已 Hook 项不入表）** —— [实证] 语义/结构依据 + [推演] 收益档：

| 排名 | 变体（虚表 → Blit 入口） | 语义 | 优先级依据 | 落地风险 |
|---:|:---|:---|:---|:---|
| 1 | `?$BlitTransXlatZRead@G`（`0x007E5978` → `0x00492B00`） | 透明/Xlat/ZRead | 单位重叠本体主路径 | 中：Z 逐像素比较 + `zBuf` 环绕；无 overshoot/`zmap` |
| 2 | `?$BlitTransDarkenZRead@G`（`0x007E5948` → `0x00492D20`） | 透明/变暗/ZRead | 重叠影子路径；SIMD 收益最大（纯 dst RMW） | 中：同上 + `DarkenMask` 必须按值读 |
| 3 | `?$RLEBlitTransXlatZRead@G`（`0x007E5560` → `0x004965B0`） | RLE/透明/Xlat/ZRead | 步兵重叠本体 | **高**：overshoot + `zmap` 推进（原版缺陷**严禁纠正**）+ 左裁剪 |
| 4 | `?$RLEBlitTransDarkenZRead@G`（`0x007E5540` → `0x00496820`） | RLE/透明/变暗/ZRead | 步兵重叠影子 | **高**：同 #3 + `DarkenMask` |
| 5 | `?$BlitTransLucent50@G`（`0x007E59C0` → `0x00492830`） | 透明/50% 半透明 | 超时空/心灵/隐形 | 低：移位 + 掩码混色 |
| 6 | `?$BlitPlainXlat@G`（`0x007E5A38` → `0x004924C0`） | 不透明/Xlat | 不透明帧也常带阵营色 | 低：无透明跳过、无 Z |
| 7 | `?$BlitTransZRemapXlat@G`（`0x007E5A08` → `0x00492590`） | 透明/ZRemap/Xlat | 深度重映射单位 | 中：双重 gather |
| 8 | `?$BlitTransXlatZReadWrite@G`（`0x007E5888` → `0x00493600`） | 透明/Xlat/ZReadWrite | 重叠 + 深度写回 | 中：回写值必须是 `zMin`（非 RLE 无 `zmap`） |
| 9 | `?$BlitTransLucent25@G` / `?$BlitTransLucent75@G`（`0x007E59A8` / `0x007E59D8`） | 透明 25% / 75% | 与 #5 同模板参数化 | 低 |
| 10 | `?$RLEBlitTransDarken@G`（`0x007E55A0` → `0x00496250`） | RLE/透明/变暗 | 步兵影子（非 Z 版） | 中：overshoot + `DarkenMask` |

> **排序口径声明（重要）**：上表**不是实测 ROI 排序**。① 全部 108 项入口的直接 `call/jmp` 静态命中 **= 0**（虚表间接派发），`vtRef` 量级仅 2–4，区分度不足；② 遥测只有总量、无按函数分解；③ 原引用的 perf 百分比（11.55%→16.55%、15.64%）其采样场景已判作废（见 §1.6 勘误）。⇒ **主依据 = 像素语义/结构 + 既有定谳文档**，实测仅作方向性提示；收益档「高/中高/中/中低」为**语义预估**（[推演]），须由插桩实测按 `pixels × calls` 百分位回填 [实证] `blit_coverage_top10.md:129-167,308-313`。

**真机插桩规格（纸面规格，未落地生效 · [待实测]）** —— 目标是取得「每函数调用数 × 像素」分布：

1. **计数点位置**：统一插在**虚表槽 1（Blit）入口**，对全部 108 个虚表建 trampoline：`orig = vtable[1]; vtable[1] = &Thunks[i]`；每个 trampoline 做 `inc [g_BlitCalls + i*4]` + 从栈参读 `length` 累加 `[g_BlitPixels + i*4]` + `jmp orig`。
2. **原子性与开销**：引擎渲染为单线程（主逻辑单线程已有实证）⇒ 普通 `inc` 即可；像素累加用非原子 `add`；写盘按帧末或每 5s 汇总，避免日志风暴。
3. **字段与格式**：新增 `[ra2render-blit-func]` 行，逐变体输出 `calls=…  pixels=…`，仅输出 `calls>0` 项。
4. **可机械验证的验收判据**：① **守恒** `sum(per-func BlitCalls) == BlitCalls`（同理 pixels），允许 ±1% 节流误差；② **单调**：per-func 计数非负、单调不减；③ **覆盖**：重放同一对局，Top10 排名与实测排名的 Kendall τ ≥ 0.6；④ **零侵入**：插桩前后像素输出 **bit-identical**；⑤ **可关闭**：`ra2render.ini` 加 `BlitFuncTelemetry=0/1`，默认 0 时零开销（不装 trampoline）。
````
- **证据**：[实证] 覆盖率 6/108 与 6 项 vtable/入口（`blit_coverage_top10.md:79-93`）、xref 全 0 口径（`blit_coverage_top10.md:156-167`）、遥测字段普查（`blit_coverage_top10.md:20-47`）；[推演] Top10 收益档与接管顺序；[待实测] 插桩规格全部条目。该来源文档亦已自查声明「本表给的是可辩护的优先级，不是实测 ROI 排序」。
- **影响面**：§1.6（口径红线互相引用）；**§11 速查表**（建议为 6 项已 Hook 变体加已接管标记列）；**§12 契约**——插桩属只读遥测，不改像素、不进同步契约，但仍建议走 MP 门控矩阵评审；§0 准则（本节给出禁止编数的可执行替代路径）。

---

## PATCH-R1-09  §2.1 补「单位绘制接口收敛点：Draw_SHP → 虚表槽 1」

- **目标锚点**：atlas **L427**（§2.1 Pass 8 勘误块末行）｜ 该行前 40 字符原文：`  > ⚠️ **【勘误 · U3-P1 · 2026-09-29】本 Pas`（grep 实跑：`hits=1 → 427`）
- **动作**：INSERT_AFTER
- **现状问题**：§2.1 描述 Pass 6 时只说「依次调用 `DrawIfVisible`（槽 65）→ `Draw`（槽 69）」，**没有给出位图层真正的接口收敛点**：exe 内所有 RLE/非 RLE Blitter 调用**唯一汇聚**于 `Draw_SHP (0x00437A10)` 的 `0x00437E20: FF 52 04 call dword ptr [edx+4]`（虚表槽 1），且 `EncodedLen` 就是此处算出的 `ClippedRect.X - OriginalRect.X`。缺此锚点时「战术视口流水线接口」在位图层是断链的（09-28 `rle_blit_family.md:787-849`、`blit_coverage_top10.md:226-236,245-253`）。
- **替换文本**：

````markdown
**位图层接口收敛点：`Draw_SHP (0x00437A10)` → Blitter 虚表槽 1（2026-09-28 · R1 并入）[实证]**

Pass 5/6/7 的**一切 SHP 像素落盘**（步兵/载具/建筑/投影阴影/动画帧）都经 `Draw_SHP` 汇聚为「逐扫描行 → 虚表槽 1」的一次调用，这是战术视口流水线与渲染微内核之间的**唯一接口**：

```asm
; 左裁剪量（EncodedLen）与顶部裁剪行数的计算
0x00437AC4: 8B 8C 24 88 00 00 00  mov ecx, [esp+0x88]   ; 原始精灵 Rect
0x00437ACB: 8B 44 24 6C           mov eax, [esp+0x6C]   ; 相交裁剪后 Rect.X
0x00437ACF: 8B 11                 mov edx, [ecx]        ; OriginalRect.X
0x00437AD1: 2B C2                 sub eax, edx          ; ClippedRect.X - OriginalRect.X
0x00437AD6: 89 84 24 98 00 00 00  mov [esp+0x98], eax   ; ⇒ EncodedLen（左裁剪要跳过的像素数）
0x00437ADD: 8B 44 24 70           mov eax, [esp+0x70]   ; 相交裁剪后 Rect.Y
0x00437AE1: 2B C2                 sub eax, edx          ; Y 差值（与 X 分量同形；语义见来源文档）
0x00437AE7: 89 44 24 28           mov [esp+0x28], eax   ; ⇒ 顶部裁剪行数
; zmap surface：NULL 则兜底到全零缓冲
0x00437BD7: 85 C0 0F 84 ED 00 00 00  test eax,eax; je 0x00437CCC
0x00437C1A: 03 C2                 add eax, edx          ; zmap 指针 += EncodedLen（故阶段 A 无需推进 zmap）
0x00437CCC: C7 44 24 10 68 C5 89 00  mov [esp+0x10], 0x0089C568  ; 全零兜底（平坦 zmap）
; 逐扫描行调用 Blitter（虚表槽 1）
0x00437E10: 50                    push eax              ; EncodedLen
0x00437E11: 51                    push ecx              ; Length（本行可见像素数）
0x00437E19: 8D 47 02              lea  eax, [edi+2]     ; src（行数据体，跳过 RLE 行头）
0x00437E1D: 51                    push ecx              ; dst（目标帧缓冲行首）
0x00437E20: FF 52 04              call dword ptr [edx+4]  ; ★ 唯一 Blitter 出口 = 虚表槽 1
```

- 因此「Hook 槽 1」= 在**位图层出口**统一接管，与 §1.1/§1.2 的 Hook 口径完全自洽；没有任何绕过槽 1 的位图路径（否则该调用点不会成为唯一收敛点）。
- `EncodedLen` 的语义由此确凿：**因视口左侧裁剪而必须丢弃的本行首部像素数**（不是「编码长度」）[实证]。
````
- **证据**：[实证] `0x437AC4` / `0x437AD6 = 89 84 24 98 00 00 00` / `0x437AE7 = 89 44 24 28` / `0x437BD7 = 85 C0 0F 84 ED 00 00 00` / `0x437C1A = 03 C2` / `0x437CCC = C7 44 24 10 68 C5 89 00` / `0x437E10 = 50 51` / `0x437E20 = FF 52 04`（本流只读复算）；来源 `docs/re/rle_blit_family.md:787-849`、`docs/re/blit_coverage_top10.md:226-236`。
- **影响面**：§2.1（接口补齐）；**§2.2**（打脏/重绘决策与本接口无耦合，无影响）；**§12.1 渲染线程与主逻辑关系**（本接口仍在主线程内，无并发语义变化）；**§11 速查表**（建议加 `Draw_SHP` 单例条目）；§0 准则无影响。**注**：`0x00437AE1` 行标为 [推演]（本流只复核了字节 `2B C2` 与 X 分量同形，未逐条语义定谳），其余行 [实证]。

---

## 覆盖度自证表（来源文档 §小节 → 命中补丁块）

> 规则：每个来源小节都必须有归属；确无需入 atlas 的写「不入 atlas + 理由」。**已收口→PATCH 命中**表示该结论 atlas 现文已有等价表述（标出 atlas 行号），本流不再重复出补丁。

### A. `docs/re/rle_blit_family.md`（876 行，09-28 11:14，主来源）

| 来源 §小节 | 归属 |
|:---|:---|
| §1 摘要（51 = 39@G + 12@E；RLEBlitter 基类 vtable `0x007E5BA0`；3 槽；5 原语） | **PATCH-R1-01**（数量/基类）+ **PATCH-R1-02**（3 槽/CallBlit0）+ **PATCH-R1-07**（5 原语矩阵） |
| §2 优先级表（P0–P7 排序） | **PATCH-R1-08**（Top10 与批次口径）；P0–P2 具体地址已在 atlas §1.1 表中 → 已收口→PATCH-R1-08 命中 |
| §3.1 调用约定与参数布局（10 参 `ret 0x28`；`Length` 32 位；`EncodedLen` 语义） | 已收口→PATCH 命中（atlas **L267–L281**）；`CallBlit0 ret 0x2c` 归 **PATCH-R1-02** |
| §3.2 RLE 码流格式（`00 nn`；`00 00` 非终止符；无哨兵） | 已收口→PATCH 命中（atlas **L331–L335**）；新增约束「无不透明 run、解码循环须保持标量」归 **PATCH-R1-05** |
| §3.3 两阶段结构（左裁剪 + 绘制；overshoot 修正） | 两阶段框架已收口（atlas **L337–L341**）；**overshoot 修正在 atlas 0 命中 → PATCH-R1-05** |
| §3.4 对象布局（this 成员分化矩阵） | **PATCH-R1-03**（尺寸矩阵把 `+0x04`/`+0x08` 的真实类型与是否越界逐变体定死） |
| §3.5 深度缓冲环绕（`0x00887644`；`+0x1C`/`+0x20`；aBuf 描述符 `0x0087E8A4`） | Z 缓冲本体已收口（atlas **L298–L327**）；**`0x0087E8A4`（Alpha 的 aBuf）在 atlas 0 命中 → PATCH-R1-04** |
| §3.6 Z 测试与回写（`*zBuf > zMin - *zmap`；movsx；WriteZ 回写） | **PATCH-R1-04** |
| §4.1–4.2（Xlat @G / @E 基准） | atlas 入口已收口（L223 表）；`@E` 族与 Xlat 公式归 **PATCH-R1-01**（@E 存在性）+ **PATCH-R1-07**（原语 1） |
| §4.3（Darken 纯 dst RMW） | **PATCH-R1-07**（原语 2）；DarkenMask 按值读的既有红线已在 atlas L253/L259 → 已收口→PATCH-R1-07 命中 |
| §4.4（Lucent25/50/75 三档公式；BlendMask） | **PATCH-R1-07**（原语 3） |
| §4.5（ZRemapXlat 双查表） | **PATCH-R1-07**（原语 4）；atlas L256 已有二级指针表述 → 部分已收口，公式与字节锚点为本块新增 |
| §4.6–4.7（XlatZRead / DarkenZRead / *ZReadWrite） | **PATCH-R1-04**（Z 测试与回写）+ **PATCH-R1-05**（zmap 推进） |
| §4.8（Lucent50ZReadWarp：`dst[warpOffset]` 采样） | **PATCH-R1-07**（Warp 叠加维度） |
| §4.9（Alpha：`AlphaRow[aBuf[i]] OR idx`；行号 `min(0xFE,(aLvl*261)>>11)`） | **PATCH-R1-07**（原语 5）—— atlas 仅列 `BlitTransXlatAlphaZRead@G` 入口（L226），公式 0 命中 |
| §5 SSE2 改造建议（解码保持标量；可向量化粒度；9 条必保一致路径） | **PATCH-R1-05**（overshoot/zmap 必保）+ **PATCH-R1-06**（粒度与环形缓冲防护）+ **PATCH-R1-07**（Lucent 移位掩码、DarkenMask 不硬编码） |
| §6 建议 Hook 地址表（P0–P7 全量 vtable/Hook 位置/CallBlit0/dtor） | **PATCH-R1-02**（槽口径与「只 Hook 槽 1」的实证依据）；具体地址表：不入 atlas（atlas 是架构图谱，地址清单宜由 `docs/re/HOOK_POINT_MATRIX.md` 承载；如需入 atlas，建议进 §11.2 而非 §1） |
| §7 与现有实现的衔接清单（签名纠偏、this 拆分、槽位确认） | **PATCH-R1-03**（this 拆分的尺寸依据）+ **PATCH-R1-02**（槽位自洽）；其余为 ra2render 源码级动作：不入 atlas |
| §8 未决问题（9 条） | 不入 atlas（未闭环项，无定谳；其中 zmap 三假说已由 §9.1 定谳 → 归 **PATCH-R1-05**） |
| §9.1 zmap 推进语义定谳（off-by-overshoot 缺陷；调用方预加 EncodedLen；NULL→`0x0089C568`） | **PATCH-R1-05**（+ `0x0089C568` 数据锚点进 **PATCH-R1-04**） |
| §9.2 EncodedLen 调用方全链路 + 虚表 `0x007F1D00` 勘误 | **PATCH-R1-09**（调用方与出口）；`0x007F1D00` 笔误属台账侧，见 [3] 勘误 5 |
| §9.3 剩余 49 个实现 Top10 | **PATCH-R1-08**（与 blit_coverage Top10 合并为一张「下一步接管优先级」表） |
| 附录 A（反汇编工作产物清单） | 不入 atlas（中间产物清单，非架构结论） |
| 附录 B（51 个实现速查 vtable/Blit/CallBlit0/dtor） | **PATCH-R1-01**（数量口径）；逐条地址表：不入 atlas（理由同 §6；本流已独立复算 RTTI 名 51/39/12 佐证口径） |

### B. `docs/re/blit_coverage_top10.md`（370 行，09-28 11:14）

| 来源 §小节 | 归属 |
|:---|:---|
| §1 结论摘要（108 个 = 57+51；当前 6/108；无 per-func 遥测；Top3） | **PATCH-R1-01**（族口径）+ **PATCH-R1-08**（6/108 与 Top10） |
| §2 E1 遥测可用性判定（只有总量；不可得字段；口径声明；量级曲线） | **PATCH-R1-06**（遥测口径红线）+ **PATCH-R1-08**（排序口径声明） |
| §2.5 日志劫持虚表原文交叉核对（6 项原入口 VA 恒定） | **PATCH-R1-08**（6 项已 Hook 表逐项列 VA） |
| §3 E2 覆盖现状表（6 项已 Hook，逐项 vtable/槽/入口） | **PATCH-R1-08** |
| §4 E3 覆盖缺口清单（108 全量 / 102 未 Hook；语义粗计） | **PATCH-R1-08**（102 缺口与未覆盖口径）；全量 108 行清单本身：不入 atlas（属 `out/re_work/` 产物） |
| §5 E4 优先级排序（三类静态证据口径 + Top10 表 + xref 全 0） | **PATCH-R1-08**（Top10 + 排序口径声明） |
| §6 E5 前三项落地前提（Top1/2/3 的槽、入口、序言字节、像素语义、对拍要点） | **PATCH-R1-08**（风险列）+ **PATCH-R1-04**（Z 环绕/回写值）+ **PATCH-R1-05**（overshoot/zmap 严禁纠正） |
| §7 E6 真机插桩规格（计数点/开销/字段/验收判据 5 条） | **PATCH-R1-08**（§1.8 插桩规格块） |
| §8 排序依据方法论与局限（不编数；语义热度非新实测） | **PATCH-R1-08**（排序口径声明）+ **PATCH-R1-06**（遥测红线） |
| §9 未闭环清单（4 条） | 不入 atlas（未闭环；#1/#3 已转写为 **PATCH-R1-08** 的插桩规格与待实测项） |
| §10 附录（产物清单 / 门禁 / 写作用域合规） | 不入 atlas（流程性内容） |
| 附录 L1 Lead 保留判定（perf 百分比降级待重测；Top10 收益档回填口径；先插桩后 Hook） | **PATCH-R1-06**（降级判定与撤回 40%）+ **PATCH-R1-08**（收益档为预估、须实测回填） |

### C. `docs/re/nonrle_blit_and_named_hotspots.md`（315 行，09-27 10:13）

| 来源 §小节 | 归属 |
|:---|:---|
| §1 结论（非 RLE 57 个；5 槽；`ret 0x20`；无 EncodedLen/overshoot；三指针齐头并进） | **PATCH-R1-01** + **PATCH-R1-02**（`ret 0x24`）+ **PATCH-R1-04** |
| §2 非 RLE 优先级表（P0–P3，8 项） | **PATCH-R1-08**（Top10 表 #1/#2/#5/#6/#7/#8/#9 取自本表） |
| §2.1 通用约定（8 参栈帧；this 布局；Z 环绕；透明判据；无左裁剪） | 8 参栈帧已收口（atlas **L283–L293**）；this 布局归 **PATCH-R1-03**；其余归 **PATCH-R1-04** |
| §2.2 重点算法（XlatZRead 三段；DarkenZRead；Lucent；PlainXlat；ZRemapXlat；WriteZ；Alpha 族公式） | **PATCH-R1-04** + **PATCH-R1-07**（与 RLE 同构的 5 原语）+ **PATCH-R1-05**（RLE/非 RLE 推进语义对照） |
| §2.3 SSE2 非 RLE 改造要点（无解码循环→更适合 SIMD；透明位图；zBuf 环绕） | **PATCH-R1-06**（向量化前提 1 + 环形缓冲防护） |
| §3 / §4 未命名热点簇命名（`AboutDlgCheatCluster` / `BufSectorReaderClockCluster` / `MainMessagePump`） | **不入 atlas（超出 R1 作用域）**——三者均不在 §1/§2.1（渲染/Blitter）范围内，且来源 §3.1/§5.1 已定谳「对渲染目标不值得继续挖」。建议 Lead 指派给帧时钟/消息泵相关流（若将来入 atlas，落点应是 §8 帧时钟循环/§12 并发契约，非 §1）。**请 Lead 裁决是否另开任务卡。** |
| §5 建议 Hook 表（非 RLE 下一批 5 个） | **PATCH-R1-08**（Top10 覆盖其 5 项） |
| §6 未决问题（8 条；src 推进已核实） | 不入 atlas（未闭环）；其中「src 推进与 Z 无关」由 **PATCH-R1-04** 吸收为实证结论 |
| 附录 A（已反汇编 18 项一览，含指令数） | 不入 atlas（工作产物） |
| 附录 B（命名对照速查） | 同 §3/§4 归属，不入 atlas（超出作用域） |

### D. `docs/re/blitter_microkernel_deep_dive.md`（1,204 行，09-27 10:14，与 atlas §1 现文对照）

| 来源 §小节 | 归属 |
|:---|:---|
| §1 摘要与虚表拓扑（§1.1 五大高频微内核表） | 已收口→PATCH 命中（atlas **L215–L236**）；数量口径补 **PATCH-R1-01** |
| §2.1 this 成员布局（Darken vs Xlat） | 已收口→PATCH 命中（atlas **L240–L259**）；但「12 字节统一」被 **PATCH-R1-03** 推翻 |
| §2.3 调用约定与参数栈帧 | 已收口→PATCH 命中（atlas **L263–L294**） |
| §2.4 全局 Z 缓冲描述符与环绕 | 已收口→PATCH 命中（atlas **L298–L327**）；Z 判定式补 **PATCH-R1-04** |
| §3.1–3.6 各微内核汇编剖析 | 结构已收口（atlas §1.1/§1.5）；算法细节归 **PATCH-R1-04 / R1-05 / R1-07** |
| §4 现网代码缺陷诊断（`ra2render.h`/`blitter_hooks.cpp`） | 不入 atlas（源码级缺陷，属 ra2render 轨） |
| §5 SSE2 向量化设计（无符号比较技巧） | **PATCH-R1-06**（向量化前提与粒度）；符号位翻转技巧属实现细节：不入 atlas |
| §6 生产级实现原型（约 350 行 C++/SSE2） | 不入 atlas（代码交付物） |
| §7 虚表挂钩安装对照表与验证策略 | **PATCH-R1-02**（槽口径）；逐项挂接清单：不入 atlas（同 §6 理由） |
| **§8.1.1–8.1.4 S13：工厂拓扑 + 4/8/12/16 四级分配 + this 布局全矩阵 + 头文件纠偏蓝图** | **PATCH-R1-03（核心：推翻 atlas「固定 12 字节」）**；8.1.4 蓝图属源码级：不入 atlas |
| §8.2.1–8.2.4 S13：ZRead/WriteZ 语义边界与指针推进对照表 | **PATCH-R1-04** + **PATCH-R1-05** |
| §8.3.1–8.3.2 S13：非 RLE 具名热点优先序 + 向量化蓝图 | **PATCH-R1-08** + **PATCH-R1-06** |

### E. `docs/re/re_sprint_S13_report.md`（186 行，09-26 22:46）

| 来源 §小节 | 归属 |
|:---|:---|
| §1 成果摘要（三项） | 已由 §2 各证据块细分归属；摘要本身不入 atlas |
| §2.1 证据 1–4（工厂入口、Darken 掩码值、8 字节分配、栈上构造 4 字节对象） | **PATCH-R1-03**（证据 2/3/4 即尺寸分级的原始取证；atlas 从未并入） |
| §2.2 证据 5–7（非 RLE/RLE Z 判定；overshoot 处 zmap 静止） | **PATCH-R1-04** + **PATCH-R1-05** |
| §2.3 非 RLE 接管优先级（perf-scene2/3） | **PATCH-R1-08**（Top10 #1/#2/#5 语义依据）；其 perf 采样与 §1.6 勘误同源风险，见 [7] |
| §3 交付物核验清单 / §4 下一步建议 | 不入 atlas（流程性与建议）；头文件重构与 P0 批量注入归 [9] 待裁决 |

**零遗漏声明**：上述 5 份来源文档的全部 §小节均已给出归属，未出现无归属小节。

---

## 十节回执（`docs/re/AGENT_DELIVERY_FORMAT.md` §A 骨架）

```text
[META]
task=task-1（流 R1 渲染/Blitter）  executor=atlas-r1-render（DSH Agent Teams 成员）  mode=read-only（二进制/他人文档）+ accept-edits（仅本流作用域）
scope_declared=docs/re/atlas_rev/R1_render_blit.md、out/re_work/atlas_rev/R1/**、out/re_work/atlas_rev/R1/claims_R1.txt

[0] 结论摘要（≤5 行）
1. 产出 9 个锚定补丁块（R1-01..09），覆盖 §1.1–§1.6 与 §2.1；其中 R1-03 是推翻性勘误：atlas §1.2「所有 Blitter 实例固定 12 字节」被字节级实证推翻——全部 P0 微内核（步兵/载具本体与影子）实测仅 8 字节，按 12 字节声明结构体将越界 4 字节。
2. 09-28 两份主来源的 0 命中条目已全部给出补丁块：族级数量口径 108/57/51/39/12、3 槽 vs 5 槽与 CallBlit0 转发、5 正交原语矩阵、overshoot 禁改约束、6/108 覆盖率与 Top10、遥测无 per-func 分解、插桩规格。
3. §1.6 的「流水线停顿占整机耗时超 40%」无来源且与已作废采样冲突，按 §0 准则建议撤回（R1-06）；§1.6 同时补上「遥测只有总量」的口径红线。
4. 本流对 57/51/39/12/7 的族计数做了独立 RTTI 修饰名普查（未采信来源文档），逐格一致。
5. 最大风险：像素等价性（overshoot/zmap 必须原样复现原版缺陷）；次要风险：本流结论均为静态实证，perf 口径须真机重测。

[1] 逐条必答项结论表
| # | 问题 | 结论 | 证据等级 | 证据锚点 |
| 1 | rle_blit_family 是否带来新虚表槽结论 | 是：RLE 3 槽 / 非 RLE 5 槽；CallBlit0 转发槽 1（ret 0x2c / ret 0x24） | [实证] | 0x496164/0x496167、0x492BC7/0x492BCA、0x7E5B88/0x7E5BA0 |
| 2 | 是否带来新热点 | 是（语义排序，非实测）：Top10 见 R1-08 | [实证]语义+[推演]收益 | rle_blit_family.md:858-869、blit_coverage_top10.md:143-154 |
| 3 | 是否带来新覆盖率结论 | 是：软件 blit 实现族 108 个，当前 Hook 6/108，未覆盖 102 | [实证] | blit_coverage_top10.md:12,79-93；RTTI 普查 57+51（本流复算） |
| 4 | 是否推翻 atlas §1 既有表述 | 是，1 条硬推翻 + 1 条撤回：① §1.2「固定 12 字节」；② §1.6「>40%」 | [实证] | R1-03 / R1-06 |
| 5 | 是否给 §2.1 接口新锚点 | 是：Draw_SHP 0x00437A10 → 0x00437E20: FF 52 04（唯一出口=槽 1）；EncodedLen = ClippedRect.X - OriginalRect.X | [实证] | R1-09；0x437AC4–0x437AE7 |
| 6 | 是否有伪造实测 | 无。本流未启动游戏/未注入/未改二进制；未运行项一律标 [待实测] | — | [5]/[7] |

[2] 关键证据块（VA / FileOffset / 字节 / 反汇编 / 来源）
- 尺寸分级（核心）：0x0048FAE8 = 6A 08（RLEBlitTransXlat@G 分配 8 字节，FileOffset 0x0008FAE8）→ 0x0048FB05 = C7 00 C0 55 7E 00（vtable 落位 0x007E55C0）；0x0048FC55 = 6A 08（DarkenZRead 8 字节）→ 0x0048FC70 = 66 89 48 04（16 位掩码）。113 处分配点尺寸直方图 4×2 / 8×24 / 12×57 / 16×30。
- 槽结构：0x7E5B88 五槽 + 第 6 dword 0x007FF4F8（.rdata RTTI）；0x7E5BA0 三槽 + 0x00000000。
- CallBlit0：0x00496130 = 8B 54 24 28 8B 01 … 0x00496164 = FF 50 04（call [eax+4]）0x00496167 = C2 2C 00（ret 0x2c）。
- overshoot/zmap：0x004965EC = F7 D8 2B D8 8D 3C 47 8D 04 42（dst/zBuf 补偿，zmap 不动）；0x00496636 = 03 C8（透明游程 zmap+=n）；0x0049664C = 41（实体像素 inc ecx）。
- Z 判定：0x004968A6 = 0F BE 01 → 0x004968B0 = 2B F8 → 0x004968B9 = 3B F8 → 0x004968BB = 7D 11（RLE）；0x00492B22 = 66 8B 10 83 C0 02 39 54 24 20 7D 24（非 RLE）。
- 调用方：0x00437AD6 = 89 84 24 98 00 00 00（EncodedLen）；0x00437C1A = 03 C2（zmap += EncodedLen）；0x00437CCC = C7 44 24 10 68 C5 89 00（零兜底）；0x00437E20 = FF 52 04（唯一出口）。
- 族计数：0x0081ED0C = 3F 24 52 4C 45 42 6C 69 74 54 72 61 6E 73 58 6C 61 74 40 47 40 40（?$RLEBlitTransXlat@G@@）；全 exe RTTI 去重 57 / 51（@G 50/39，@E 7/12）。
- 机器可读断言：out/re_work/atlas_rev/R1/claims_R1.txt（56 条，audit_bytes.py 56/56 OK）。

[3] 勘误（逐条）
1. docs/re/ARCHITECTURE_ATLAS.md:242（§1.2）｜改前：「在西木引擎的工厂函数（…）中，所有 Blitter 实例的尺寸由 push 0x0C; call operator new 分配，固定为 12 字节：」（含 L244–L249 的 12 字节布局围栏）｜改后：见 PATCH-R1-03 替换文本（4/8/12/16 四级 + 逐 vtable 尺寸矩阵 + this+0x08 越界红线）｜理由：P0 微内核实测仅 8 字节（分配点字节 + vtable 落位双向锁定）｜影响面：产品决策阻断项（结构体声明）、§11.2、§12.4。
2. docs/re/ARCHITECTURE_ATLAS.md:348（§1.6）｜改前：「…L1/L2 缓存与流水线停顿占整机耗时超 40%。」｜改后：见 PATCH-R1-06（撤回该数字 + 改用 11.55%→16.55% 口径并声明其采样作废 + 遥测无 per-func 分解）｜理由：无来源，违反 §0 准则「禁止把估算当实测」｜影响面：§0 准则、§11 速查表对 §1.6 的引用。
3. docs/re/rle_blit_family.md:792-799（§9.2，他人文档）｜复核结论：该文档所述「0x00437AE1: 2B C2 sub eax, edx」与「0x00437AE7: 89 44 24 28」两处与本流字节复算一致 ⇒ **无勘误**（记录于此以便 Lead 免于重复核查）。
4. docs/re/re_sprint_S13_report.md:4（他人文档）｜改前：「MD5: 5b6dc513e4b78ae676b7e67f08819ab2」｜改后（建议）：「MD5: 4f37486e5b0dbe2ae5f45aeee0f98367」（与 task-1 任务卡、blit_coverage_top10.md:355 及本流实测一致）｜理由：S13 所记 MD5 与本工作区基线不一致（本流实算 4f37486e5b0dbe2ae5f45aeee0f98367，4,825,360 字节）；但其地址/字节与现行基线逐条吻合（本流已复算 7 处）⇒ 判为元数据笔误，而非不同二进制｜影响面：S13 证据的基线归属声明。**本流不修改他人文档。**
5. REVERSE_ENGINEERING_AND_PATCHES.md:58（据 rle_blit_family.md:820-823 转述；**本流未直读该台账行**）｜改前：ADDR_VTABLE_RLE_BLIT_TRANS_XLAT_G = 0x007F1D00｜改后：0x007E55C0｜理由：0x7F1D00 实测为 F8 FF FF FF F8 FF FF FF（.rdata 数据，非代码指针）｜影响面：Hook 地址常量正确性。**请 Lead 复核后改，本流不改台账。**

[4] 未闭环清单
| # | 缺口 | 为何无法静态闭环 | 下一步取证方法 | 阻塞级别 |
| 1 | 「每函数调用数 × 像素」分布 | 遥测只有总量；虚表间接派发无静态 xref | 按 PATCH-R1-08 §1.8 插桩：108 个 vtable 槽 1 建 trampoline，重放 U0800_Accelerated_Skirmish + Brutal AI，核对守恒判据 | P0 |
| 2 | perf 百分比（11.55%→16.55% / 15.64%） | 采样场景真机只实例化 21/22 单位，已判作废 | 按 out/loadbench/H1_REMEASURE_RUNBOOK.md 重测后回填 | P0 |
| 3 | overshoot 缺陷的可视化复现 | 常规渲染 zmap=NULL 走全零兜底，缺陷不暴露 | 构造 zmap 非平凡 SHP（高程阴影），对拍左裁剪边界行；判定：与原版像素 bit-identical | P1 |
| 4 | RLE Alpha 族（10 个）Alpha 表构造 | Alpha 表运行时生成方式未知（this+0x08 的 512 字节行） | 反 0x0049AA00 邻近 init 路径 + 抓 aLvl/aBuf 取值域 | P2 |
| 5 | 8 位 @E 族是否在现代 16 位渲染路径出现 | 可能是死代码 | 插桩后看 calls 是否大于 0 | P2 |
| 6 | §1.2 改写后 ra2render 结构体需同步重构 | 属工程轨（ZCode），非本流作用域 | 交 Lead 与代码轨排期；验收：静态断言 sizeof 与分配尺寸一致 + 真机长时对战无堆破坏 | P1 |
| 7 | 113 处分配点中 30 处 16 字节对象未逐类映射 | vtable 落位指令距 call 较远，超出本流自动配对窗口 | 扩充配对窗口/人工逐点核对（脚本已存 out/re_work/atlas_rev/R1/scan_factory_allocs3.py） | P2 |

[5] 写作用域合规声明
- 本次改动文件（仅 3 类，均在本流作用域内）：
  - docs/re/atlas_rev/R1_render_blit.md（本文件，新建）
  - out/re_work/atlas_rev/R1/claims_R1.txt（新建，56 条断言）
  - out/re_work/atlas_rev/R1/ 下 scratch/脚本/dump（新建）
- 未触碰（已核）：docs/re/ARCHITECTURE_ATLAS.md（未写，仅只读；mtime 仍为 2026-09-27 22:22:08）、其他 docs/re/atlas_rev/*.md、ra2render/**、ra2youli/**、REVERSE_ENGINEERING_AND_PATCHES.md、任何既有 docs/re/*.md、out/re_work/atlas_rev/lead/**、out/re_work/atlas_rev/R*（非 R1）。
- 目标二进制只读：ra2youli/gamemd.exe MD5 4f37486e5b0dbe2ae5f45aeee0f98367，4,825,360 字节（本流实算，与任务卡一致）；全程只 open(path,'rb') 读取。
- 未启动游戏 / 未进程注入 / 未挂调试器 / 未改二进制。

[6] 门禁实跑输出（原文粘贴，见本文件末「门禁原文」两节）
- python tools\verify_anchors.py → 断言总数 323 | PASS 323（100.00%）| FAIL 0 | NOREAD 0 → [100% ALL PASS]
- python tools\audit_bytes.py out/re_work/atlas_rev/R1/claims_R1.txt → 合计 56 条：OK=56 MISMATCH/NOREAD=0

[7] 风险与红线提示
- ① 同步语义/命令序：不触及（未改代码、未改二进制指令）。
- ② 随机数消费序：不触及。
- ③ 存档结构：不触及。
- ④ 渲染像素等价性：触及。R1-04/R1-05 定死「原版 off-by-overshoot 缺陷必须原样复现」的像素等价红线；R1-03 会影响工程侧结构体尺寸（越界风险）。⇒ 需要 MP 门控矩阵 + 真机像素对拍验收，禁止宣称零风险/零 Desync。
- 另：S13 报告 MD5 元数据与基线不一致（见 [3]-4）⇒ 引用 S13 §2.3 的 perf 百分比前建议先按 [4]-2 重测。

[8] 交付物清单
- 新文档：docs/re/atlas_rev/R1_render_blit.md（本文件）
- 脚本：out/re_work/atlas_rev/R1/ 下 8 个 .py（verify_r1_facts / scan_factory_allocs{1,2,3} / verify_vtables_rtti / verify_cb0_names / verify_s4_anchors / verify_vtable_edges / verify_primitive_anchors / atlas_anchor_prefixes）
- 断言：out/re_work/atlas_rev/R1/claims_R1.txt（56 条，56/56 OK）
- dump：dump_anchors.txt / dump_factory_sizes.txt / dump_vtables_cb0.txt / dump_names_cb0_full.txt / dump_s4_anchors.txt / gate_verify_anchors.txt / gate_audit_bytes.txt
- 补丁块：9 个（R1-01..R1-09）

[9] 待裁决项
1. §1.2 改写口径：建议按 PATCH-R1-03 全量替换 L242–L249（含 12 字节布局图），并在 §11.2 加「对象尺寸」列。风险：改动面较大且影响 ra2render 结构体声明 ⇒ 建议与代码轨联审后落。
2. §1.6「>40%」的处理方式：建议直接撤回（本流按 §0 准则判断不可保留）；若历史文档曾引用，需全库扫一次（本流未扫全库）。
3. §6 / 附录 B / §4 的全量地址清单是否入 atlas：本流建议不入 §1，改由 HOOK_POINT_MATRIX.md / §11.2 承载；请 Lead 裁决。
4. nonrle 文档 §3/§4 三个命名簇（AboutDlgCheatCluster / BufSectorReaderClockCluster / MainMessagePump）超出 R1 作用域：请 Lead 决定是否另开任务卡（落点应为 §8/§12，非 §1）。
5. S13 报告 MD5 笔误：建议 Lead 就地加勘误（属他人文档，本流不写）。
6. 插桩与 Hook 的批次：本流认同来源文档与 Lead 附录 L1 的裁决——先插桩（只读遥测）→ 实测 → 再定序。

```

---

## 门禁原文（实跑粘贴，未概述）

### G1. python tools\verify_anchors.py

```text
（原文见 `out/re_work/atlas_rev/R1/gate_verify_anchors.txt`；关键行如下）
===================================================================================================================
  RA2/YR 二进制决定性锚点自动化回归测试套件 (verify_anchors.py)
===================================================================================================================
目标文件 : D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe (大小: 4,825,360 字节, ImageBase: 0x400000)
断言文件 : D:\Project\ra2-campaign-forge\docs\re\anchor_claims.txt
反汇编器 : Capstone x86-32 引擎已就绪
-------------------------------------------------------------------------------------------------------------------
[基线完整性审计]
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
  [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
-------------------------------------------------------------------------------------------------------------------
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
===================================================================================================================
```

```text
$ python tools\verify_anchors.py
[exit code: 0]
```

### G2. python tools\audit_bytes.py out/re_work/atlas_rev/R1/claims_R1.txt

```text
（原文见 `out/re_work/atlas_rev/R1/gate_audit_bytes.txt`；末行汇总如下，逐条 48 行均为 OK）
VA         期望字节                       实际字节                   判定     标签/上下文
--------------------------------------------------------------------------------------------------------------
0x48ebf0   53 56 8b f1 6a 08 83 7e 04 01 0f 85 54 04 00 00 53 56 8b f1 6a 08 83 7e 04 01 0f 85 54 04 00 00 OK     ConvertClass Blitter 工厂入口 + [esi+4]==1 分支 | push ebx
0x48fae8   6a 08                      6a 08                  OK     RLEBlitTransXlat@G 分配 push 8（非 12） | push 8
0x48fb05   c7 00 c0 55 7e 00          c7 00 c0 55 7e 00      OK     mov dword [eax],0x007E55C0（vtable 落位） | mov dword ptr [eax], 0x7e55c0
0x48fbfe   6a 08                      6a 08                  OK     RLEBlitTransXlatZRead@G 分配 push 8 | push 8
0x48fc55   6a 08                      6a 08                  OK     RLEBlitTransDarkenZRead@G 分配 push 8 | push 8
0x48fc70   66 89 48 04                66 89 48 04            OK     DarkenMask 以 16 位「值」写入 [this+4] | mov word ptr [eax + 4], cx
0x496164   ff 50 04                   ff 50 04               OK     CallBlit0: call dword ptr [eax+4]（转发槽 1 ⇒ 只 Hook 槽 1 足够） | call dword ptr [eax + 4]
0x496167   c2 2c 00                   c2 2c 00               OK     CallBlit0 ret 0x2c（11 DWORD = 10 参 + 1 useless） | ret 0x2c
0x492bca   c2 24 00                   c2 24 00               OK     非 RLE CallBlit0 ret 0x24（9 DWORD = 8 参 + 1 dummy） | ret 0x24
0x4965ec   f7 d8 2b d8 8d 3c 47 8d 04 42 f7 d8 2b d8 8d 3c 47 8d 04 42 OK     RLE XlatZRead overshoot: dst/zBuf += over*2；zmap(ecx) 不推进 | neg eax
0x4968a6   0f be 01                   0f be 01               OK     movsx eax,byte [ecx] ⇒ zmap 为 int8_t（有符号扩展） | movsx eax, byte ptr [ecx]
0x4968bb   7d 11                      7d 11                  OK     jge skip ⇒ 通过条件 *zBuf > zMin - *zmap | jge 0x4968ce
0x492b22   66 8b 10 83 c0 02 39 54 24 20 7d 24 66 8b 10 83 c0 02 39 54 24 20 7d 24 OK     非 RLE: *zBuf > zMin（无 zmap），jge 跳过 | mov dx, word ptr [eax]
0x437c1a   03 c2                      03 c2                  OK     zmap 指针预加 EncodedLen（故阶段 A 无需推进 zmap） | add eax, edx
0x437e20   ff 52 04                   ff 52 04               OK     Draw_SHP 唯一 Blitter 出口: call dword ptr [edx+4]（虚表槽 1） | call dword ptr [edx + 4]
0x81ed0c   3f 24 52 4c 45 42 6c 69 74 54 72 61 6e 73 58 6c 61 74 40 47 40 40 3f 24 52 4c 45 42 6c 69 74 54 72 61 6e 73 58 6c 61 74 40 47 40 40 OK     "?$RLEBlitTransXlat@G@@" | aas
0x7f1d00   f8 ff ff ff f8 ff ff ff   f8 ff ff ff f8 ff ff ff OK     历史笔误所述"虚表 0x007F1D00"实为 .rdata 数据，非代码指针 | clc
--------------------------------------------------------------------------------------------------------------
合计 56 条：OK=56  MISMATCH/NOREAD=0
```

```text
$ python tools\audit_bytes.py out/re_work/atlas_rev/R1/claims_R1.txt
[exit code: 0]
```

（以上为节选 17 条代表性行；完整 48 行原文见 `out/re_work/atlas_rev/R1/gate_audit_bytes.txt`，无一 MISMATCH/NOREAD。）

---

**声明**：本文档为流 R1 的唯一交付文档；不含任何未经运行却标为实测的结论；所有 VA 均可在 `ra2youli/gamemd.exe`（MD5 4f37486e5b0dbe2ae5f45aeee0f98367）上按 FileOffset = VA − 0x400000 复算。
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]




