# S07-K2 LAYOUT — 虚表槽语义 / 对象布局 / 数组布局（字节级实测）

目标：`ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`，ImageBase `0x400000`。
工具：Python 3.12.10 + capstone 5.0.7(`skipdata=True`) + pefile 2024.8.26。
复算脚本：`work/t3t4.py`、`work/sweep_all.py`、`work/relib.py`；原始输出在 `EVIDENCE/`。

## 1. 虚表定界（从 `.rdata` 做，不用 atlas 边界反推）

方法：`vtable[-1]` = COL（`.rdata` 指针），从 `vt` 起逐 dword 读，凡落在 `.text`(`0x401000..0x7E1000`) 即算一槽，遇首个非 `.text`（下一个 COL / 0 / 浮点常量）止。RTTI 名走 **COL+0xC→TD，名字内联在 TD+8**（`.?AV…@@`），读不到 fail-closed。

| 类(RTTI) | vtable | COL | TD | 槽数(自数) | 关键槽 |
|---|---|---|---|---|---|
| LayerClass | `0x7E6060` | `0x7FFC28` | `0x816B10` | **10** | `v[4]`(+0x10)=`0x40CF00` 定位；`v[7]`(+0x1C)=`0x5519B0` Add；`v[3]`(+0x0C)=`0x40CC70` |
| Blitter | `0x7E5B88` | `0x7FF4C8` | `0x81EFF8` | **5** | `v[0]`=`0x499CC0`；`v[1..4]`=`0x4C9150` 空桩(`xor eax,eax;ret`) |
| RLEBlitter | `0x7E5BA0` | `0x7FF4F8` | `0x81EF48` | **3** | `v[0]`=`0x499DA0`；`v[1..2]`=`0x4C9150` 空桩；+0x0C=`0` 终止 |
| Surface | `0x7E2198` | `0x7FB2F8` | `0x817878` | **34** | `v[0]`=`0x4115D0`；多数=`0x4C9150` 空桩；+0x88=`0x437F0000`(浮点) 终止 |
| BSurface | `0x7E2070` | `0x7FB260` | `0x817860` | **36** | — |
| XSurface | `0x7E2104` | `0x7FB2C8` | `0x817890` | **36** | `v[28..29]`=`0x4C9150`(与 BSurface 差异点) |
| DSurface | `0x7E85D4` | `0x800260` | `0x8205D8` | **38** | — |
| VectorClass\<ObjectClass*\> | `0x7E192C` | `0x7FA9A0` | `0x816AA8` | **7** | — |
| DynamicVectorClass\<ObjectClass*\> | `0x7E4F64` | `0x7FD0B0` | `0x816AD8` | **7** | — |

- **槽号不假定**：LayerClass 的 Add 是 `v[7]`/`+0x1C`（实测 `0x5519B0`），定位是 `v[4]`/`+0x10`（实测 `0x40CF00`）——与 `R14_COMMON §4.2` 一致，但不是"槽 N 通例"。
- 110 个 `RLEBlit*`/`Blit*` 模板类（vt `0x7E5360..` 段）RTTI 名见 `vtables_canonical.json`；它们的 **slot1** = 实际 `Blit()`（①卡顿线 61.9% 的执行点），`Blitter`/`RLEBlitter` 基类的 slot1 是空桩，不能当"Blit 本体"。
- `0x4C9150` = `xor eax,eax; ret` 共用空桩（与 S11-K2 Locomotor 同款），大量槽指向它，**不是真实函数**。

## 2. `[5]LayerClass` 静态数组布局（element 0x18 B）

复算：`EVIDENCE/ev_layer_ctor_4A8630.txt`、`ev_layer_bound_4A8900.txt`、`ev_setlayer_4A9720.txt`、`ev_sort_551A30.txt`。

| 相对元素基址 | 含义 | 字节证据 |
|---|---|---|
| `+0` | vftable (`0x7E6060`) | ctor `0x4A8648/4A864F/4A8660` 写 `0x7E192C→0x7E4F64→0x7E6060`（三层基类链，末值 LayerClass）|
| `+4` | Items（对象指针数组） | 遍历器 `mov ecx,[0x8A0394]; mov esi,[ecx+eax*4]`（`0x6D981A/0x6D9972/0x6D9A6F`）|
| `+0xC`/`+0xD` | 两个 byte | ctor `mov byte [eax+4],1` / `mov byte [eax+5],cl`（eax=`0x8A0368`=元素0的+8 偏移基准）|
| `+0x10` | Count | ctor `mov [eax+8],0`（=元素`+0x10`）；遍历器 `mov eax,[0x8A03A0]`/`dec`/`jl`；sort `mov eax,[ebp+0x10];dec`（只读）|
| `+0x14` | 10（GrowthStep） | ctor `mov [eax+0xC],0xA`（=元素`+0x14`）|

- **数组基址** `0x8A0360`，**5 元素**，**stride 0x18**：ctor 循环 `mov eax,0x8A0368; mov edx,5; … add eax,0x18; dec edx; jne`（`0x4A8630`）；范围 `0x8A0360..0x8A03D8`，与 `cmp esi,0x8A03D8`（`0x4A8918`）吻合。
- **同一数组**：元素索引公式 `lea edx,[edi+edi*2]; lea ecx,[edx*8+0x8A0360]`（SetLayer `0x4A974A/0x4A9752`，edx=idx*3 ⇒ `idx*0x18`）。故 `0x8A0390`=元素2基址（=0x8A0360+2*0x18），`0x8A0364`=元素0的 Items 字段地址 —— **不是两个容器**。
- 排序：`0x55DBC3 mov ecx,0x8A0390 / call 0x551A30`；`0x551A30` 对相邻元素各 `call [vptr+0xB8]` 取键比较/交换（bubble），全程只 `[ebp+0x10]` 读 Count、不写。

## 3. ObjectClass 字段

| 偏移 | 语义 | 字节证据要点 |
|---|---|---|
| `+0x94` | 层索引（`-1`=无层） | SetLayer `cmp [esi+0x94],-1` / `mov [esi+0x94],edi`（`0x4A972A`/`0x4A9762`）；RemoveFromLayer `mov eax,[edi+0x94]` / `mov [edi+0x94],0xFFFFFFFF`（`0x4A977E`/`0x4A97D2`）。写点分布见 PROGRESS（49 对象字段 /112 栈）。|
| `+0x80` | 精灵级脏标记（byte） | 置 1：`0x438E3C`（有 cmp 比较）；消费清 0：`0x43CEFD`/`0x6D98EF`/`0x6D9A27`/`0x6D9B1A`；读过滤：`0x43CEC3`/`0x6D9A88`。|
| `+0x74` | 在格中标记 | slot65 `mov al,[edi+0x74];test;je 0x43D017`；列表层 `0x482887`。|
| `+0x81` | 抑制/隐藏 | slot65 `mov al,[edi+0x81];test;jne 0x43D017`。|
| `+0x104` | slot65 虚调用偏移（`DrawIfVisible`） | `call [edx+0x104]`（`0x6D98E9`/`0x6D9A21`）。|
| `+0x114` / `+0x4E4` | Draw 本体 / 绘制后半 | `call [edx+0x114]`（`0x43D005`）/ `call [edx+0x4E4]`（`0x43CFE9`）。|

## 4. T4 GetSize / 分配点（Blitter 族）

- **基线**：全 `.text` 裸字节 `B8 imm32 C3` = **666**（与 `R14_COMMON` 基线 666 精确一致）；`B8 imm32`（不要求 C3）裸字节 = 10,578（R14 的 837 是"指令边界过滤后"口径，两者非同口径，见 DISAGREE）。
- **Blitter/RLEBlitter/Surface 族槽扫描：`B8 imm32 C3` 命中 0**（`EVIDENCE/t4_getsize_hits.tsv` 为空表）。这些族的槽多为 `0x4C9150` 空桩或真实 Blit 函数，没有 `mov eax,imm32; ret` 形态的 GetSize ⇒ **对它们做"imm32+push size 双点闭合"不适用**（与 Locomotor COM 族的 slot9 情形不同）。
- 结论：T4 对 Blitter 族**升不动**——缺"该类确有 `B8 imm32 C3` 槽"这一前提；不是证据不足，是该形态不存在。
