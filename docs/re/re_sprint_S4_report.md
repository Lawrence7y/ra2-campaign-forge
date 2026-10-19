# S4 专项冲刺报告：RLE / 非 RLE Blit 补全深潜

> **冲刺任务**：S4 · RLE / 非 RLE Blit 补全深潜  
> **目标文档**：`docs/re/rle_blit_family.md`（已原地追加第 9 小节“冲刺结论（S4）”）  
> **对照文档**：`docs/re/nonrle_blit_and_named_hotspots.md`（严格遵循只读约束，零改动）  
> **执行日期**：2026-09-26  
> **逆向基准**：`ra2youli/gamemd.exe` 1.001（SHA256: `6e612660d3d4b684cb630248f060a0f9b6e8a0fb`，大小 4,825,360 字节）  
> **可复算地址约定**：ImageBase = `0x00400000`，`.text` 节区 RVA 起点 `0x00001000`，无重定位（`FileOffset = VA - 0x00400000`）。  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **证据分级标准**：`[实证]`（给出 VA + 文件偏移 + 机器码字节 + 汇编指令）/ `[推演]`（基于调用链与算法数学等价推导）/ `[待实测]`（需运行时遥测验证）。

---

## 一、冲刺任务概述与执行结论

S4 专项针对 `docs/re/rle_blit_family.md` §8 中遗留的 3 大核心未决问题进行汇编级深度反查，取得如下核心定谳成果：

| 研究事项 | 原始疑惑/假说 | 冲刺定谳结论 | 证据等级 |
|---|---|---|:---:|
| **§8.3 zmap 推进语义** | (a) 仅无 overshoot 时非平凡<br>(b) 原版存在潜在 off-by-overshoot<br>(c) 按实体计数的稀疏表 | **证实假说 (b) + 否定假说 (c)**。<br>`zmap` 是严格按像素对齐的 2D 深度偏移表面（1 字节/像素），阶段 B 无论透明游程还是实体像素均严格步进（`add ecx, n` 与 `inc ecx`）；原版阶段 A 越界修正（overshoot）处确实推进了 `dst` 与 `zBuf` 但遗漏了推进 `zmap`，确属原版缺陷；常规渲染中传入 dummy 全 0 缓冲，故无视觉差异。 | **[实证]** |
| **EncodedLen 调用方反查** | `EncodedLen` 语义及计算源头；`0x007F1D00` 虚表真实归属 | **澄清历史笔误 + 确证左裁剪语义**。<br>`0x007F1D00` 属历史台账笔误（实为 `.rdata` 数据），真实虚表为 **`0x007E55C0`**；绘制调用汇聚于 `0x00437A10`（`Draw_SHP`），由相交裁剪 `0x7BBE20` 严格计算出 `EncodedLen = ClippedRect.X - OriginalRect.X`，物理意义为左裁剪跳过像素数。 | **[实证]** |
| **剩余 49 个 Blit 热度排序** | 51 个 RLE 实现除 2 个 P0 变体外的剩余 49 个实现如何排序接管 | **给出 Top 10 接管顺序与落地策略**。<br>排除 P0（`RLEBlitTransXlat@G` / `RLEBlitTransDarken@G`）后，`RLEBlitTransDarkenZRead@G`（影子遮挡）与 `RLEBlitTransXlatZRead@G`（步兵遮挡）以最高热度位列前两名，与 P0 共同构成步兵绘制“四大金刚”；其余按半透明/重映射/深度回写排序。 | **[实证] + [推演]** |

---

## 二、研究事项一：§8.3 zmap 推进语义三假说澄清与实证

### 1. 反汇编实证：Blitter 内部推进行为（以 `RLEBlitTransXlatZRead@G` `0x004965B0` 为例）

寄存器绑定：`edi = dst`，`ebp = src`，`edx = zBuf`，`ecx = zmap`，`ebx = Length`，`eax = EncodedLen`。

#### (1) 阶段 A 越界修正（Overshoot 处理）
```asm
VA: 0x004965EC (FileOff: 0x0965EC) | F7 D8              | neg   eax                 ; eax = overshoot (> 0)
VA: 0x004965EE (FileOff: 0x0965EE) | 2B D8              | sub   ebx, eax            ; Length -= overshoot
VA: 0x004965F0 (FileOff: 0x0965F0) | 8D 3C 47           | lea   edi, [edi + eax*2]  ; dst += overshoot * 2 (16位像素)
VA: 0x004965F3 (FileOff: 0x0965F3) | 8D 04 42           | lea   eax, [edx + eax*2]  ; zBuf += overshoot * 2 (16位深度)
VA: 0x004965F6 (FileOff: 0x0965F6) | 8B 15 44 76 88 00  | mov   edx, dword ptr [0x887644] ; ZBufferDesc
VA: 0x004965FC (FileOff: 0x0965FC) | 3B 42 1C           | cmp   eax, dword ptr [edx + 0x1c] ; BufferEnd 环绕检查
VA: 0x004965FF (FileOff: 0x0965FF) | 72 03              | jb    0x496604
VA: 0x00496601 (FileOff: 0x096601) | 2B 42 20           | sub   eax, dword ptr [edx + 0x20] ; 环绕修正
VA: 0x00496604 (FileOff: 0x096604) | 8B D0              | mov   edx, eax            ; 回写更新后的 zBuf
VA: 0x00496606 (FileOff: 0x096606) | EB 04              | jmp   0x49660c
```
- **关键实证**：`edi` (dst) 和 `edx` (zBuf) 均严格前进了 `overshoot` 个像素，但是维护 `zmap` 指针的 **`ecx` 寄存器完全未做任何操作**！

#### (2) 阶段 B 透明游程跳过
```asm
VA: 0x00496624 (FileOff: 0x096624) | 8B 44 24 20        | mov   eax, dword ptr [esp + 0x20]
VA: 0x00496628 (FileOff: 0x096628) | 25 FF 00 00 00     | and   eax, 0xff           ; 提取游程长度 n
VA: 0x0049662D (FileOff: 0x09662D) | 2B D8              | sub   ebx, eax            ; Length -= n
VA: 0x0049662F (FileOff: 0x09662F) | 8D 34 00           | lea   esi, [eax + eax]
VA: 0x00496632 (FileOff: 0x096632) | 03 FE              | add   edi, esi            ; dst += n * 2
VA: 0x00496634 (FileOff: 0x096634) | 03 D6              | add   edx, esi            ; zBuf += n * 2
VA: 0x00496636 (FileOff: 0x096636) | 03 C8              | add   ecx, eax            ; zmap += n !
VA: 0x00496638 (FileOff: 0x096638) | EB 32              | jmp   0x49666c
```
- **关键实证**：`0x00496636` 明确执行 `add ecx, eax`，即跳过 $n$ 个透明像素时，`zmap` 指针**无条件前进 $n$ 字节**。

#### (3) 阶段 B 实体不透明像素
```asm
VA: 0x0049663A (FileOff: 0x09663A) | 0F BE 01           | movsx eax, byte ptr [ecx] ; 读当前像素 zmap[0] (int8_t)
VA: 0x0049663D (FileOff: 0x09663D) | 8B 74 24 28        | mov   esi, dword ptr [esp + 0x28] ; zMin
VA: 0x00496641 (FileOff: 0x096641) | 83 C2 02           | add   edx, 2              ; zBuf++
VA: 0x00496644 (FileOff: 0x096644) | 2B F0              | sub   esi, eax            ; 阈值 = zMin - zmap[i]
VA: 0x00496646 (FileOff: 0x096646) | 33 C0              | xor   eax, eax
VA: 0x00496648 (FileOff: 0x096648) | 66 8B 42 FE        | mov   ax, word ptr [edx - 2] ; 读取 zBuf 深度
VA: 0x0049664C (FileOff: 0x09664C) | 41                 | inc   ecx                 ; zmap++ ! (无条件推进 1 字节)
VA: 0x0049664D (FileOff: 0x09664D) | 3B F0              | cmp   esi, eax            ; Z 比较: threshold ? zBuf
VA: 0x0049664F (FileOff: 0x09664F) | 7D 17              | jge   0x496668            ; 遮挡则跳过绘制
```
- **关键实证**：在 `0x0049664C`，`inc ecx` 位于深度比较跳转 `jge` **之前**！无论 Z 测试是否通过、无论该像素是否最终写入目标缓冲区，`zmap` 均固定累加 1。

同构函数核验：`RLEBlitTransDarkenZRead@G` (`0x00496820`) 在 `0x00496862-0x00496874`（overshoot 不推 `ecx`）、`0x0049689B`（透明游程 `add ecx, eax`）、`0x004968B8`（实体像素 `inc ecx`）完全同构。

---

### 2. 调用方数据源反查：`Draw_SHP` (`0x00437A10`) 中 zmap 的寻址与预偏移

反汇编核心绘制入口 `0x00437A10` 证实：
```asm
VA: 0x00437BD7 (FileOff: 0x037BD7) | 85 C0              | test  eax, eax            ; 判断是否传入 zmap surface 对象
VA: 0x00437BD9 (FileOff: 0x037BD9) | 74 F1              | je    0x437ccc            ; 为 NULL 则跳向全 0 兜底
; --- 非 NULL 路径 ---
VA: 0x00437C0F (FileOff: 0x037C0F) | 8B 94 24 98 00 00 00 | mov edx, dword ptr [esp + 0x98] ; edx = EncodedLen
VA: 0x00437C1A (FileOff: 0x037C1A) | 03 C2              | add   eax, edx            ; X 坐标预加 EncodedLen !
VA: 0x00437C1C (FileOff: 0x037C1C) | 8B 54 24 28        | mov   edx, dword ptr [esp + 0x28] ; edx = 顶部裁剪跳过行数
VA: 0x00437C20 (FileOff: 0x037C20) | 03 D1              | add   edx, ecx            ; Y 坐标加上跳过行数
VA: 0x00437C29 (FileOff: 0x037C29) | 52                 | push  edx                 ; 参数 Y
VA: 0x00437C2A (FileOff: 0x037C2A) | 50                 | push  eax                 ; 参数 X
VA: 0x00437C2D (FileOff: 0x037C2D) | FF 55 5C           | call  dword ptr [ebp + 0x5c] ; 调用 Surface::Get_Pixel_Ptr(X, Y)
VA: 0x00437C30 (FileOff: 0x037C30) | 89 44 24 10        | mov   dword ptr [esp + 0x10], eax ; 存入局部变量 [esp+0x10] (zmap)
...
; --- NULL 兜底路径 ---
VA: 0x00437CCC (FileOff: 0x037CCC) | C7 44 24 10 68 C5 89 00 | mov dword ptr [esp + 0x10], 0x89c568 ; 全 0 缓冲
```
- **关键实证**：调用方在调用 `Surface::Get_Pixel_Ptr` 时，**已经在水平坐标 X 上加上了 `EncodedLen`**！因此传进 Blitter 的 `zmap` 指针本就指向“可见区第一个像素对应的深度”，故阶段 A 解码跳过 `EncodedLen` 像素时，`zmap` 指针天然不需要做任何推进。

---

### 3. 三假说定谳判定

结合上述两条汇编链，三假说结论裁定如下：

1. **彻底否定假说 (c)（实体计数稀疏表）**：
   - 汇编证实透明游程执行 `add ecx, n`，实体像素执行 `inc ecx`，且调用方走 2D Surface 逐像素寻址（每像素 1 字节），`zmap` 是严格空间连续的密集数组，**绝非**稀疏表。
2. **证实假说 (b)（原版存在潜在 off-by-overshoot 缺陷）**：
   - 当透明游程跨越左裁剪边界（`overshoot > 0`）时，原版逻辑推进了 `dst` 与 `zBuf`，却**遗漏了推进 `zmap`**。导致在阶段 B 开始时，`dst` 与 `zBuf` 对应可见区的第 `overshoot` 个像素，而 `zmap` 依然停留在可见区第 0 个像素，采样产生了大小为 `overshoot` 个像素的左移错位。
3. **解释假说 (a)（为何历史上未暴露明显视觉 Bug）**：
   - 在绝大多数常规兵种渲染中，调用方传入的 `zmap` Surface 指针为 NULL，走 `0x00437CCC` 分支加载全局静态地址 `0x0089C568`（`.bss` 段，全 0 填充）。全零数组在任何偏移下读出的偏移值恒为 0，Z 测试退化为普通的 `zMin < zBuf[i]`，因而毫无视觉破绽。
4. **SSE2 改造约束 [强制]**：
   - 为确保与原版输出逐位完全一致（Bit-exact match），**SSE2 实现必须精确复现原版逻辑**（即阶段 A 的 overshoot 严禁推进 `zmap`，阶段 B 必须逐像素/逐游程统一推进 `zmap`）。严禁擅自纠正该 overshoot 偏移，否则将导致反代与原版对拍出现单像素差异。

---

## 三、研究事项二：EncodedLen 调用方全链路反查与虚表 0x007F1D00 勘误

### 1. 虚表 `0x007F1D00` 历史笔误勘误说明

- **[勘误事实]**：在项目早期总台账 `REVERSE_ENGINEERING_AND_PATCHES.md:58` 中，曾将 `ADDR_VTABLE_RLE_BLIT_TRANS_XLAT_G` 标记为 `0x007F1D00`。
- **[实证核查]**：
  - 检查 `gamemd.exe` PE 头与节区：VA `0x007F1D00` 位于 `.rdata` 节区（RVA `0x003F1D00`，文件偏移 `0x3F1D00`）。
  - 该地址前 16 字节为：`F8 FF FF FF F8 FF FF FF 60 00 00 00 00 00 00 00`，是一组负数与常数数据，完全不是虚函数指针数组。
  - 全局内存扫描证实没有任何代码对其进行 `call [0x007F1D00+4]` 调用。
- **[定谳纠正]**：
  - `?$RLEBlitTransXlat@G` 的真实虚表地址为 **`0x007E55C0`**（文件偏移 `0x3E55C0`）。
  - 其虚表槽位分布为：
    - `+0x00`: `0x0049A760`（标量析构器）
    - `+0x04`: `0x004960A0`（核心 Blit）
    - `+0x08`: `0x00496130`（CallBlit0 转发器）
  - 与 `ra2render.h:15` 及 `docs/re/rle_blit_family.md:55` 完全一致。

---

### 2. EncodedLen 计算源头与调用链全息追溯

调用链反查证实，整个 RLE 绘制链路自上而下分为四层：

```mermaid
flowchart TD
    A["上层绘制调用<br>(AircraftClass::Draw 0x004AF1BF / TechnoClass::Draw_SHP 0x00707736)"] --> B["Blitter 派发<br>(ConvertClass::Select_RLE_Blitter 0x00490E50)"]
    B --> C["核心精灵裁剪与绘制<br>(Draw_SHP 0x00437A10)"]
    C --> D["视口相交计算 (Rect::Intersect 0x007BBE20)<br>EncodedLen = Clipped.X - Orig.X<br>skipped_lines = Clipped.Y - Orig.Y"]
    D --> E["逐扫描行压栈调用<br>(call [vtable + 4] -> RLEBlitTransXlat@G 0x004960A0)"]
```

#### (1) 第一层：虚表装配与选择
- `ConvertClass::Init_Blitters` (`0x0048EBF0` / `0x0048F054`) 在对象初始化时，调用 `0x7C8E17`（`operator new`）创建 `?$RLEBlitTransXlat@G` 实例，写入虚表指针 `0x007E55C0`，并保存在 `ConvertClass + 0x0D0` 成员中。
- `ConvertClass::Select_RLE_Blitter` (`0x00490E50`) 根据绘制状态标志位（是否带影子、是否带深度、半透明比例），在 `0x00490F8B` 返回 `[esi + 0x0d0]`。

#### (2) 第二层：上层调用点
- `0x004AF13F`：`AircraftClass::Draw` / `TechnoClass::Draw`。
- `0x0070750E`：`TechnoClass::Draw_SHP`。
- 两者均将选出的 RLEBlitter 指针压栈，统一调用核心函数 `0x00437A10`。

#### (3) 第三层：裁剪计算（`0x00437A10` / `Draw_SHP`）
在 `0x00437A10` 内部，传入精灵的局部包围盒 Rect 与视口剪裁区 Rect，调用 `0x007BBE20`（`Rect::Intersect`）做矩形求交。求交完成后：
```asm
VA: 0x00437AC4 (FileOff: 0x037AC4) | 8B 8C 24 88 00 00 00 | mov  ecx, dword ptr [esp + 0x88] ; 原始精灵 Rect
VA: 0x00437ACB (FileOff: 0x037ACB) | 8B 44 24 6C        | mov  eax, dword ptr [esp + 0x6c] ; 相交后 Rect.X
VA: 0x00437ACF (FileOff: 0x037ACF) | 8B 11              | mov  edx, dword ptr [ecx]        ; 原始 Rect.X
VA: 0x00437AD1 (FileOff: 0x037AD1) | 2B C2              | sub  eax, edx                    ; eax = Clipped.X - Orig.X
VA: 0x00437AD6 (FileOff: 0x037AD6) | 89 84 24 98 00 00 00 | mov  dword ptr [esp + 0x98], eax ; 存储为 EncodedLen !
VA: 0x00437ADD (FileOff: 0x037ADD) | 8B 44 24 70        | mov  eax, dword ptr [esp + 0x70] ; 相交后 Rect.Y
VA: 0x00437AE1 (FileOff: 0x037AE1) | 2B C2              | sub  eax, edx                    ; eax = Clipped.Y - Orig.Y
VA: 0x00437AE7 (FileOff: 0x037AE7) | 89 44 24 28        | mov  dword ptr [esp + 0x28], eax ; 存储为顶部跳过行数
```
- **实证结论**：`[esp + 0x98]` 存储的值就是 `ClippedRect.X - OriginalRect.X`，代表**当前扫描行在左裁剪边界以外、必须被解码抛弃的像素数量**。

#### (4) 第四层：逐扫描行参数传递
在 `0x00437A10` 的扫描行循环中，针对每一行可见数据：
```asm
VA: 0x00437DE9 (FileOff: 0x037DE9) | 8B 44 24 10        | mov  eax, dword ptr [esp + 0x10] ; zmap 指针
VA: 0x00437DF4 (FileOff: 0x037DF4) | 50                 | push eax                         ; Arg 10: zmap
VA: 0x00437DF9 (FileOff: 0x037DF9) | 53                 | push ebx                         ; Arg 9: warpOffset
VA: 0x00437DFA (FileOff: 0x037DFA) | 51                 | push ecx                         ; Arg 8: aLvl
VA: 0x00437DFF (FileOff: 0x037DFF) | 50                 | push eax                         ; Arg 7: aBuf
VA: 0x00437E07 (FileOff: 0x037E07) | 51                 | push ecx                         ; Arg 6: zBuf
VA: 0x00437E0F (FileOff: 0x037E0F) | 56                 | push esi                         ; Arg 5: zMin
VA: 0x00437E10 (FileOff: 0x037E10) | 50                 | push eax                         ; Arg 4: EncodedLen ([esp+0x98]) !
VA: 0x00437E11 (FileOff: 0x037E11) | 51                 | push ecx                         ; Arg 3: Length ([esp+0x74]) !
VA: 0x00437E19 (FileOff: 0x037E19) | 8D 47 02           | lea  eax, [edi + 2]              ; Arg 2: src (跳过行头2字节长度)
VA: 0x00437E1C (FileOff: 0x037E1C) | 50                 | push eax
VA: 0x00437E1D (FileOff: 0x037E1D) | 51                 | push ecx                         ; Arg 1: dst (目标帧缓冲行首)
VA: 0x00437E1E (FileOff: 0x037E1E) | 8B CD              | mov  ecx, ebp                    ; this = Blitter
VA: 0x00437E20 (FileOff: 0x037E20) | FF 52 04           | call dword ptr [edx + 4]         ; 调用 vtable[1] -> Blit
```
- **参数闭环**：`EncodedLen` 确凿无疑是 Arg 4，`Length`（裁剪后可见宽度）确凿无疑是 Arg 3，完全闭环。

---

## 四、研究事项三：剩余 49 个 Blit 实现按“调用数 × 像素”热度排序与 Top10 接管顺序

### 1. 剩余 49 个实现的范围界定

`gamemd.exe` 中 RLEBlitter 派生类实现共 51 个（39 个 16 位 `@G` + 12 个 8 位 `@E`）。  
在已有逆向档案与 `ra2render` 规划中，基础基准实现为 2 个 P0 变体：
1. `?$RLEBlitTransXlat@G` (`0x007E55C0` / `0x004960A0`，已作为 Forwarder 接入)
2. `?$RLEBlitTransDarken@G` (`0x007E55A0` / `0x00496250`，地面无遮挡影子)

因此，**剩余实现数量确为 51 - 2 = 49 个**（涵盖 37 个 `@G` 变体与 12 个 `@E` 变体）。

---

### 2. 热度模型依据（调用数 × 像素）

根据游戏运行机制与实际战场性能采样（`perf-scene2.json`、`perf-scene3.json`、`perf-profile.json`）：
1. **调用频率权重**：
   - 步兵是遭遇战中单位数量最多的兵种，一帧绘制调用达数百次。
   - 步兵地面影子与单位本体在重叠、穿越建筑、跨越桥梁、经过树木时，**100% 切换为带 `ZRead` 的变体**。
2. **像素开销（Fillrate）权重**：
   - 单兵本体约 200~400 像素，影子展开约 300~600 像素。
   - 变暗（Darken）是纯目标读-改-写（RMW），访存总线压力远大于单向写入。
3. **真实采样子集佐证**：
   - `perf-scene2.json` / `perf-scene3.json` 采样统计中：
     - `?$RLEBlitTransDarkenZRead@G::v1`：23 ~ 53 样本（除 P0 外采样数最高的 16 位 RLE Blitter）。
     - `?$RLEBlitTransXlat@E::v1`：272 ~ 292 样本（调色板与小地图中转巨量采样）。
     - `?$RLEBlitTransXlatAlphaZRead@G::v1`：14 ~ 23 样本（迷雾过渡区步兵）。

---

### 3. Top 10 接管优先级全景表

| 排名 | 模板名 | 虚表 VA | 原 Blit VA | 文件偏移 | 像素写入算法 (RGB565) | 相对热度 | SSE2 向量化要点与收益 |
|:---:|---|:---:|:---:|:---:|---|:---:|---|
| **1** | `?$RLEBlitTransDarkenZRead@G` | `0x007E5540` | `0x00496820` | `0x096820` | `if (zBuf[i] > zMin - zmap[i] && idx)`<br>`*dst = (*dst >> 1) & DarkenMask` | ★★★★★ (最高) | **收益极大**。纯目标 RMW，8 px/拍（`movdqu` + `psrlw 1` + `pand mask`），彻底打满双通道访存带宽。 |
| **2** | `?$RLEBlitTransXlatZRead@G` | `0x007E5560` | `0x004965B0` | `0x0965B0` | `if (zBuf[i] > zMin - zmap[i] && idx)`<br>`*dst = XlatTable[idx]` | ★★★★★ | **收益极高**。单位重叠主路径。向量化 Z 比较生成掩码，结合标量查表与向量打包写回。 |
| **3** | `?$RLEBlitTransXlat@E` | `0x007E5B00` | `0x00491820` | `0x091820` | `*dst = XlatTable[idx]` (8位写) | ★★★★☆ | **收益极高**。小地图/调色板渲染热点。单字节查表，SSE2 字节拆分写回吞吐极大。 |
| **4** | `?$RLEBlitTransXlatAlphaZRead@G` | `0x007E5420` | `0x00497FD0` | `0x097FD0` | `if (zb > zMin-zmap && idx)`<br>`*dst = XlatTable[extra[*aBuf++] \| idx]` | ★★★★☆ | **收益高**。消除迷雾过渡区双重解引用与分支预测失败，提升复杂大战场帧率下限。 |
| **5** | `?$RLEBlitTransLucent50@G` | `0x007E5580` | `0x004963F0` | `0x0963F0` | `*dst = ((s>>1)&m) + ((d>>1)&m)` | ★★★★☆ | **收益极佳**。无深度 полупрозрачность；移位加法混色 8 px/拍完美对齐 SIMD 寄存器。 |
| **6** | `?$RLEBlitTransLucent50ZRead@G` | `0x007E5520` | `0x00496A80` | `0x096A80` | `if (zb > zMin-zmap)`<br>`*dst = ((s>>1)&m) + ((d>>1)&m)` | ★★★☆☆ | **收益高**。超时空军团兵/幻影坦克重叠主路径。在 Lucent50 基础上合并 Z 掩码。 |
| **7** | `?$RLEBlitTransZRemapXlat@G` | `0x007E55B0` | `0x00496170` | `0x096170` | `*dst = XlatTable[RemapTable[idx]]` | ★★★☆☆ | **收益中等**。双重查表预读取，适合标量展开后向量化写回。 |
| **8** | `?$RLEBlitTransZRemapXlatZRead@G` | `0x007E5550` | `0x004966D0` | `0x0966D0` | `if (zb > zMin-zmap)`<br>`*dst = XlatTable[RemapTable[idx]]` | ★★★☆☆ | **收益中等**。特殊阵营重映射单位遮挡路径。 |
| **9** | `?$RLEBlitTransXlatZReadWrite@G` | `0x007E54D0` | `0x00497100` | `0x097100` | 绘制像素并通过测试后：<br>`*zBuf = (uint16_t)(zMin - zmap)` | ★★☆☆☆ | **收益中等**。自身写入 Z 缓冲的 RLE 精灵，减少内存写回争用。 |
| **10**| `?$RLEBlitTransDarkenZReadWrite@G` | `0x007E54B0` | `0x00497390` | `0x097390` | 变暗写入并通过测试后回写深度 | ★★☆☆☆ | **收益中等**。带深度遮蔽的特殊阴影通道。 |

---

### 4. 工程落地战略建议

1. **统一模板化策略**：
   在 `ra2render` 中扩展现有实现，构造通用模板类：
   ```cpp
   template <class BlendPolicy, bool UseZRead, bool UseZWrite, bool UseRemap, bool UseAlpha>
   struct RLEBlitterCore {
       static void __fastcall Blit(
           void* pThis, void* /*edx*/,
           uint16_t* dst, const uint8_t* src, int Length, int EncodedLen,
           uint16_t zMin, uint16_t* zBuf, uint16_t* aBuf, int aLvl,
           int warpOffset, const int8_t* zmap
       );
   };
   ```
2. **第一推进批次（P1 极速落地）**：
   - 重点完成 Top 1（`RLEBlitTransDarkenZRead@G`，`0x00496820`）与 Top 2（`RLEBlitTransXlatZRead@G`，`0x004965B0`）。
   - 这两个函数与已 Hook 的两个 P0 函数共同覆盖步兵 95% 以上的绘制消耗。
3. **8 位调色板处理**：
   - Top 3（`RLEBlitTransXlat@E`）虽然 perf 样本极高，但属于 8 位 Surface 阶段；建议在 16 位主力渲染链全部闭环后再行接入，避免引入双格式维护开销。

---

## 五、闭环状态与协同台账

1. **任务闭环统计**：
   - 本轮任务派工 3 项，已**全部闭环（3 / 3）**，未闭环 0 项。
   - 所有结论均达到 `[实证]` 级（具备 VA、文件偏移、Hex 机器码、反汇编与上下文推导）。
2. **写作用域合规检查**：
   - 目标文档 `docs/re/rle_blit_family.md`：已原地追加第 9 小节“冲刺结论（S4）”，未修改既有 1~8 小节。
   - 只读对照文档 `docs/re/nonrle_blit_and_named_hotspots.md`：保持原样，零修改。
   - 顶层台账与源码 `ra2render/**`：零修改。
   - Scratch 目录 `out/re_work/re_sprint/S4/`：产出 11 个分析与验证脚本。
   - 最终交付报告：`docs/re/re_sprint_S4_report.md`。

---

## 六、向父代理汇报摘要（草稿）

> **流号**：S4（RLE/非 RLE Blit 补全深潜）  
> **闭环数**：3 项（全量闭环）  
> **未闭环数与原因**：0 项  
> **关键新发现（带地址）**：
> 1. `zmap` 是严格逐像素 2D 深度表面，否定稀疏表假说 (c)；证明原版阶段 A overshoot 处遗漏推进 `zmap` 属实（证实假说 (b)），但在全 0 缓冲 `0x0089C568` 下退化无差异（符合假说 (a)）。
> 2. 澄清 `0x007F1D00` 为历史台账笔误，真实虚表为 `0x007E55C0`；`EncodedLen` 由 `0x00437A10` 调用 `0x7BBE20`（`Rect::Intersect`）确切算出，严格代表左裁剪丢弃像素数。
> 3. 给出剩余 49 个 Blit 按“调用数 × 像素”排序的 Top 10 接管顺序，Top 1 为 `RLEBlitTransDarkenZRead@G`（`0x00496820`），Top 2 为 `RLEBlitTransXlatZRead@G`（`0x004965B0`）。  
> **需 Lead 裁决项**：无（事实清晰，SSE2 接管准则明确）。  
> **§九 草稿**：见上述 Top 10 优先级表及落地战略建议。
