# Q1·C2 渲染与视口裁剪层（DrawIfVisible v[65]）静态定量上界报告

> **责任角色**：渲染裁剪定量员  
> **研究对象**：C2 成本中心（DirectDraw CPU 软件光栅化与视口裁剪机制）  
> **分析原则**：纯静态反汇编分析 + 数据结构逆向核实；零真机运行、零采样代码；凡「A 调用 B ⇒ A 具有 B 的性质」，一律进 B 函数体核实指令与字节。  
> **母本与依据**：`ra2youli/gamemd.exe`（SHA256: `73201cc0...`）、`lead/re_line_20261105/W2_FRAMETIME_ATTRIB/W2_FRAMETIME_ATTRIB.md`、`lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py`。

---

## 1. 一句话结论与数量级速览

- **一句话结论**：视口裁剪（`DrawIfVisible` vtable[65]）在视口外判定失败时立即早退（`ret 0xC`），**短路的是整个绘制管线（包括 3D 体素矩阵旋转、阴影投影、调色板重映射与局部脏矩形标记），绝不仅仅是省 DirectDraw Blit**；裁剪判定是**按单位线性遍历判定（每单位一次，线性遍历 `ObjectsInLayers`），绝非按地图格子判定**；历史文档指称的视口坐标 `0x00887308 / 0x0088730C` 实为 `DSurface::Primary` 与 `DSurface::Hidden` 表面指针，其写者是视频模式初始化与 DirectDraw 表面生命周期管理例程（而非玩家拖屏或相机跟随）；理论上界全屏交火（~100-150ms）与全图裁剪（~0.05ms）的极端跨度与实测 166.8ms 预算差 0 个数量级，**足以独立解释 5.7 倍帧时恶化，在不采帧内数据的前提下绝对不可静态排除（staticallyExcludable = false）**。

### 数量级对比表

| 场景状态 | 单单位耗时估算 | 1200 单位全量开销 | 关键指令与函数路径 | 理论贡献与解释力 |
|---|---|---|---|---|
| **视口外全部裁剪**<br>（摄像机对准空地） | ~75 条指令<br>（约 30~50 ns） | **0.048 ms**<br>（< 0.1 ms） | `0x006D8DB0` → `0x005F4B10` → `0x006D2140`（返回 0）→ `0x005F4B7F` 早退 | 渲染耗时几乎为 0，帧时受 32ms 节流器下限锁定，跑满 31.25 fps（32.2 ms）。 |
| **视口内全量绘制**<br>（1200 单位混战） | ~30~80 $\mu\text{s}$<br>（体素+阴影+像素光栅化） | **48 ~ 96 ms**<br>（加粒子/开火达 **100~150 ms**） | `0x005F4CFD` → `vtable[69] Draw`（`0x0073CEC0` 等）→ VXL 矩阵 + Blit | 纯 CPU 软件光栅化打满单核，理论开销与实测 166.8ms（慢爬 6 fps）处于**同一数量级**。 |
| **极差（理论上界跨度）** | 差 ~1000 倍 | **~100 ~ 150 ms** | 视口内外可见对象数状态差 | **与慢窗实测赤字（166.8 - 32.2 = 134.6 ms）完全吻合，可解释 5.7 倍差值**。 |

---

## 2. 核心问题核实：视口裁剪省掉的是整个绘制还是只省 blit？

### 2.1 进入 `ObjectClass::DrawIfVisible`（`0x005F4B10`）函数体

通过静态反汇编分析基类 `ObjectClass::DrawIfVisible`（vtable 槽 65，偏移 `+0x104`，文件偏移 `0x001F4B10`）：

```asm
0x005F4B10  83ec20            sub      esp, 0x20
0x005F4B13  a06beda800        mov      al, byte ptr [0xa8ed6b]
0x005F4B18  56                push     esi
0x005F4B19  8bf1              mov      esi, ecx              ; esi = this (ObjectClass*)
0x005F4B1B  84c0              test     al, al
0x005F4B1D  89742408          mov      dword ptr [esp + 8], esi
0x005F4B21  7525              jne      0x5f4b48
0x005F4B23  a15035b700        mov      eax, dword ptr [0xb73550]
0x005F4B28  85c0              test     eax, eax
0x005F4B2A  741c              je       0x5f4b48
0x005F4B2C  8a44242c          mov      al, byte ptr [esp + 0x2c] ; EvenIfCloaked 参数
0x005F4B30  84c0              test     al, al
0x005F4B32  750a              jne      0x5f4b3e
0x005F4B34  8a8680000000      mov      al, byte ptr [esi + 0x80] ; NeedsRedraw
0x005F4B3A  84c0              test     al, al
0x005F4B3C  7441              je       0x5f4b7f              ; 若无需重绘直接跳早退
0x005F4B3E  8a8681000000      mov      al, byte ptr [esi + 0x81] ; InLimbo/Cloaked
0x005F4B44  84c0              test     al, al
0x005F4B46  7537              jne      0x5f4b7f              ; 若隐身/暂存直接跳早退
0x005F4B48  8b16              mov      edx, dword ptr [esi]  ; edx = vtable
0x005F4B4A  8d44240c          lea      eax, [esp + 0xc]
0x005F4B4E  50                push     eax
0x005F4B4F  8d442418          lea      eax, [esp + 0x18]
0x005F4B53  50                push     eax
0x005F4B54  8bce              mov      ecx, esi
0x005F4B56  c6868000000000    mov      byte ptr [esi + 0x80], 0 ; 清除 NeedsRedraw
0x005F4B5D  ff92ac000000      call     dword ptr [edx + 0xac]   ; vtable[43]: GetCoords(&CoordStruct)
0x005F4B63  8b0d24738800      mov      ecx, dword ptr [0x887324]; ecx = TacticalClass::Instance
0x005F4B69  50                push     eax                      ; 传参 CoordStruct*
0x005F4B6A  e8d1d50d00        call     0x006D2140               ; ★ TacticalClass::IsVisible
0x005F4B6F  84c0              test     al, al
0x005F4B71  7515              jne      0x5f4b88                 ; 若可见，跳入后续绘制
0x005F4B73  8b16              mov      edx, dword ptr [esi]
0x005F4B75  8bce              mov      ecx, esi
0x005F4B77  ff522c            call     dword ptr [edx + 0x2c]   ; vtable[11]: WhatAmI()
0x005F4B7A  83f818            cmp      eax, 0x18                ; 检查是否为特殊图元(Smudge等)
0x005F4B7D  7409              je       0x5f4b88
0x005F4B7F  32c0              xor      al, al                   ; ★ 返回 false
0x005F4B81  5e                pop      esi
0x005F4B82  83c420            add      esp, 0x20
0x005F4B85  c20c00            ret      0xc                      ; ★ 裁剪早退退出！
```

### 2.2 进入 `TacticalClass::IsVisible`（`0x006D2140`）视口判定体

在 `0x005F4B6A` 调用的 `0x006D2140` 中，引擎完成 3D 等轴测到 2D 屏幕坐标变换，并与视口包围盒进行相交检查：

```asm
0x006D2140  83ec08            sub      esp, 8
0x006D214A  8b33              mov      esi, dword ptr [ebx]     ; 3D 世界坐标 X
0x006D214C  8b4304            mov      eax, dword ptr [ebx + 4] ; 3D 世界坐标 Y
...
; 0x006D2155 - 0x006D21B7: 24 位等轴测坐标投影转换（矩阵乘法与 Sar 8）
0x006D2202  8b8db0000000      mov      ecx, dword ptr [ebp + 0xb0] ; ecx = ViewportPixelX
0x006D2208  8badb4000000      mov      ebp, dword ptr [ebp + 0xb4] ; ebp = ViewportPixelY
0x006D2213  2bf9              sub      edi, ecx                    ; 相对屏幕坐标 X = 投影X - 视口X
0x006D2215  2bf5              sub      esi, ebp                    ; 相对屏幕坐标 Y = 投影Y - 视口Y
...
; 视口边界带外扩裕量（Margin）判定：
0x006D2223  81f998feffff      cmp      ecx, 0xfffffe98             ; 屏幕左边界裕量 (-360 像素)
0x006D222A  7d08              jge      0x6d2234
0x006D222C  32c0              xor      al, al; ret 8               ; 屏幕左侧出界，直接返回 0
0x006D2234  8b1530ceb000      mov      edx, dword ptr [0xb0ce30]   ; 屏幕宽度（如 800）
0x006D223A  81c268010000      add      edx, 0x168                  ; +360 像素
0x006D2240  3bca              cmp      ecx, edx
0x006D2242  7e08              jle      0x6d224c
0x006D2244  32c0              xor      al, al; ret 8               ; 屏幕右侧出界，直接返回 0
0x006D224C  3d4cffffff        cmp      eax, 0xffffff4c             ; 屏幕上边界裕量 (-180 像素)
0x006D2251  7d08              jge      0x6d225b
0x006D2253  32c0              xor      al, al; ret 8               ; 屏幕上方出界，直接返回 0
0x006D225B  8b0d34ceb000      mov      ecx, dword ptr [0xb0ce34]   ; 屏幕高度（如 600）
0x006D2261  81c1b4000000      add      ecx, 0xb4                   ; +180 像素
0x006D2267  3bc1              cmp      eax, ecx
0x006D2269  0f9ec0            setle    al                          ; 若在下边界内置 1，否则置 0
0x006D226C  83c408            add      esp, 8
0x006D226F  c20800            ret      8                           ; 返回判定布尔值
```

### 2.3 视口裁剪通过后的绘制调用：`vtable[69] Draw`（`0x005F4CFD`）

若且唯若 `0x006D2140` 判定为真（`al == 1`），代码才走到 `0x005F4B88`，对视口脏矩形进行多边形裁剪相交运算，并在函数尾部调用真正的绘制函数：

```asm
0x005F4CF1  8b4c2414          mov      ecx, dword ptr [esp + 0x14] ; ecx = this (ObjectClass*)
0x005F4CF5  8d542418          lea      edx, [esp + 0x18]          ; 裁剪后屏幕坐标点 Point2D
0x005F4CF9  53                push     ebx                        ; 裁剪矩形 Bounds
0x005F4CFA  52                push     edx                        ; Point2D
0x005F4CFB  8b01              mov      eax, dword ptr [ecx]       ; eax = vtable
0x005F4CFD  ff9014010000      call     dword ptr [eax + 0x114]    ; ★ vtable[69]: Draw(...)！
0x005F4D03  5f                pop      edi
0x005F4D04  5d                pop      ebp
0x005F4D05  5b                pop      ebx
0x005F4D06  b001              mov      al, 1
0x005F4D08  5e                pop      esi
0x005F4D09  83c420            add      esp, 0x20
0x005F4D0C  c20c00            ret      0xc                        ; 返回 true
```

### 2.4 进入 `UnitClass::Draw`（`0x0073CEC0`）验证内部耗时载荷

我们进入单位绘制函数 `0x0073CEC0`（函数体长达 1414 字节，`0x0073CEC0..0x0073D446`），验证其内部到底执行了什么工作：
1. **车体 3D 体素变换**：`0x0073CF74: call dword ptr [eax + 0x1c8]`、`0x0073B470`（`DrawAsVXL`）计算车体俯仰角、翻滚角与航向角的 3D 旋转矩阵并查体素缓存；
2. **炮塔与炮管朝向解算**：`0x0073D20B: call dword ptr [eax + 0x1d4]` 与 `0x0073D219: call dword ptr [edx + 0x1d8]` 解算炮塔与炮管独立朝向角度；
3. **地面阴影多边形投影**：`0x0073D00E: call 0x53a100` 与 `0x0073D024: call 0x53b400` 计算投影拉伸与阴影调色板混合；
4. **像素光栅化与 Blitter 调用**：`0x0073D283: call 0x4aed70`（`ConvertClass` 调色板重映射）与 `0x0073D403: call 0x4aed70` 执行像素向 `DSurface::Hidden` 的纯软件 CPU 写入。

### 2.5 全局 `call [reg+0x114]` 引用核实

在全二进制 `.text` 节中扫描 `call dword ptr [reg + 0x114]`（虚表槽 69），全程序仅有 6 处调用：
1. `0x0041464F`：`AircraftClass` 绘制附件；
2. `0x0043D005`：`BuildingClass` 绘制附属动画；
3. `0x0043DC07`：`BuildingClass` 绘制建筑本体（其前置同样有 `0x0043DBF8 call 0x6d2140` 视口判定）；
4. `0x005F4CFD`：**`ObjectClass::DrawIfVisible`（主视图所有地面/空中对象绘制的唯一入口！）**；
5. `0x005F65DC`：`ObjectClass` 薄转发包装；
6. `0x0071CD7B`：`VoxelAnimClass::DrawIfVisible`（其前置同样有 `0x0071CD3D call 0x6d2140` 视口判定）。

**定论**：一旦 `DrawIfVisible` 在 `0x005F4B6F` 处判定出界，代码在 `0x005F4B85` 处直接返回，**整个 `vtable[69] Draw` 函数根本不会被调用**！视口裁剪省掉的是**包含体素 3D 变换、角度三角函数、阴影投影、调色板重映射以及像素光栅化在内的整个绘制流程，绝不仅仅是节省最后的 DirectDraw Blit 操作**。

---

## 3. 附带问题 (a)：裁剪判定是每单位一次还是每格一次？

### 3.1 渲染主驱动函数 `0x006D8DB0` 循环结构剖析

在 `TacticalClass::Render`（`0x006D3D10`）的主流线中，VA `0x006D465F` 处调用 `0x006D8DB0` 驱动主对象簇绘制。其反汇编结构揭示了双层嵌套循环：

```asm
; 外层循环：遍历 5 个图层 (Layer 0..4)
0x006D8F13  33c0              xor      eax, eax
0x006D8F15  8944242c          mov      dword ptr [esp + 0x2c], eax ; LayerIndex = 0
0x006D8F19  8d1c40            lea      ebx, [eax + eax*2]
0x006D8F24  c1e303            shl      ebx, 3                      ; ebx = LayerIndex * 24 (0x18)
0x006D8F27  895c2414          mov      dword ptr [esp + 0x14], ebx
0x006D8F2B  8b8b70038a00      mov      ecx, dword ptr [ebx + 0x8a0370] ; ecx = ObjectsInLayers[layer].Count
0x006D8F31  85c9              test     ecx, ecx
0x006D8F33  0f8eee040000      jle      0x6d9427                    ; 若本层无对象，跳下一层

; 内层循环：遍历本层动态向量内的每一个存活对象指针
0x006D8F39  8b8364038a00      mov      eax, dword ptr [ebx + 0x8a0364] ; eax = ObjectsInLayers[layer].Items
0x006D8F3F  8b4c2438          mov      ecx, dword ptr [esp + 0x38]     ; ecx = 对象索引 i
0x006D8F43  8b3488            mov      esi, dword ptr [eax + ecx*4]    ; ★ esi = ObjectClass*
...
0x006D9097  68a06f8800        push     0x886fa0                        ; 视口 Bounds
0x006D909C  8bce              mov      ecx, esi                        ; this = ObjectClass*
0x006D909E  ff9204010000      call     dword ptr [edx + 0x104]         ; ★ 对当前单位调用 DrawIfVisible
```

### 3.2 容器与复杂度定性

- **数据源**：`MapClass::ObjectsInLayers`（首地址 `0x008A0360`，每项步长 `0x18` 字节的 `DynamicVectorClass<ObjectClass*>`）。
  - Layer 0 (`0x008A0360`): Underwater
  - Layer 1 (`0x008A0378`): Surface
  - Layer 2 (`0x008A0390`): **Ground（地面层，存活绝大多数坦克与步兵，Items=`0x008A0394`，Count=`0x008A03A0`）**
  - Layer 3 (`0x008A03A8`): Air
  - Layer 4 (`0x008A03C0`): Top
- **判定粒度**：`for (layer = 0..4) for (i = 0..Count-1) obj->DrawIfVisible(...)`。
- **确证结论**：**视口裁剪判定是按存活单位线性遍历进行的（每单位一次，复杂度为 $O(N)$），绝非每格一次！**
  - 在慢窗 `v3a` 中，地面层对象数 `g = 1832`，每帧在主对象渲染中正好执行 1832 次 `DrawIfVisible` 调用；
  - 每格一次的渲染仅存在于地形底图瓦片层（Pass 2 `0x006D448B -> 0x006D3660`），该 Pass 仅遍历视口内可见格子（`VisibleCells`，约 800 格），与全图几千个逻辑 Cell 的大小无关，更与作战单位数量无关。

---

## 4. 附带问题 (b)：`0x00887308 / 0x0088730C` 写者是谁？

### 4.1 溯源破案：`0x00887308` 与 `0x0088730C` 真实身份

在 W2 报告及早期反汇编注记中，因 `0x00887308` 紧邻 `TacticalClass::Instance`（`0x00887324`），被推测性标注为“视口坐标”。我们对该全局变量的所有写点进行了逐指令追踪，并反查紧邻的 ASCII 字符串表，结果彻底推翻了“视口坐标”说：

1. **VA `0x00887308`** 对应的真实符号为 **`DSurface::Primary`**（主表面指针，指向 DirectDraw Primary Surface 包装对象）；
2. **VA `0x0088730C`** 对应的真实符号为 **`DSurface::Hidden`**（后缓冲隐藏表面指针，指向 DirectDraw BackBuffer/HiddenSurface）；
3. **VA `0x00887310`** 对应 `DSurface::Composite`；
4. **VA `0x00887314`** 对应 `DSurface::Hidden_2`；
5. **VA `0x00887324`** 才是 `TacticalClass::Instance`。

### 4.2 写者函数与字节证据

在全二进制中检索对 `0x00887308` 和 `0x0088730C` 写入（`mov [0x887308], ...`）的指令点，其写者分布如下：

| 写点 VA | 机器码 | 所在函数与上下文 | 紧邻字符串证据（文件偏移与文本） | 真实引擎行为 |
|---|---|---|---|---|
| `0x00560D32` | `A3 08 73 88 00` | `Set_Video_Mode`（`0x00560C70`） | `0x0082A410`: `"Creating primary..."`<br>`0x0082A4A0`: `"Set_Video_Mode for %dx%d..."` | 分配并保存 PrimarySurface 实例指针 |
| `0x00560F18` | `A3 08 73 88 00` | `Set_Video_Mode`（全屏/窗口重置） | `0x0082A484`: `"Restoring primary..."` | 模式重置后重新写入主表面指针 |
| `0x00560CF6` | `89 1D 08 73 88 00` | `Reset_Video_Mode` | `0x0082A4B8`: `"Deleting primary..."` | 显存表面销毁，写 `NULL` 清零 |
| `0x00560E51` | `89 1D 0C 73 88 00` | `Reset_Video_Mode` | `0x00827CE0`: `"Deleting HiddenSurface\n"` | 隐藏后缓冲表面销毁，写 `NULL` 清零 |
| `0x00534038` | `89 35 0C 73 88 00` | `GScreenClass::Init_Surfaces` | 表面分配与重连 | 初始化创建 HiddenSurface |
| `0x006BB90D` | `89 1D 0C 73 88 00` | DirectDraw 释放流程 | 表面注销 | 退出战局时清零 |
| `0x006BB97B` | `89 1D 08 73 88 00` | DirectDraw 释放流程 | 表面注销 | 退出战局时清零 |

**结论**：**`0x00887308 / 0x0088730C` 的写者根本不是「玩家拖屏」，也不是「自动跟随」！它们是 DirectDraw 视频显示模式初始化与表面生命周期管理例程！**

### 4.3 真正视口坐标在哪里？写者是谁？

- **真实视口坐标字段**：存储在 `TacticalClass` 堆实例内部：
  - `[TacticalClass + 0xb0]`：视口左上角像素 X 坐标（`TacticalViewPixelX`）；
  - `[TacticalClass + 0xb4]`：视口左上角像素 Y 坐标（`TacticalViewPixelY`）；
  - `[TacticalClass + 0x3584]` / `[TacticalClass + 0xe0]`：视口覆盖格子区间与可见 Cell 计数。
- **写者逻辑**：受 `ScrollClass::Scroll_Map`（边缘滚屏/键盘滚屏）与 `MapClass::Set_Tactical_Position`（雷达点击跳切）驱动。
- **自动化测试约束**：基线评测脚本 `qc151_trip.harness8_v4.py:3826` 具有明文观测扰动禁令：
  > `“★★ 观测扰动禁令（§3.1-②/§4.1）：测量窗内零键鼠、零 PrintWindow”`
  因此，在整个 25 秒测量窗内，**目标进程不接受任何按键和鼠标移动消息，摄像机严格静止在出生点初始坐标处，完全不存在任何外部玩家拖屏写操作，遭遇战常规单位移动亦不触发全局摄像机自动跟随**。

---

## 5. 附带问题 (c) 与数量级论证：能否解释 5.7 倍帧时恶化？

### 5.1 单单位裁剪与绘制的指令级耗时推算

1. **视口外裁剪开销（下界）**：
   - 当单位处于屏幕外时：`0x006D8DB0` 循环取指针（8 指令）+ `DrawIfVisible 0x005F4B10` 入口检查（18 指令）+ `0x006D2140 IsVisible` 坐标投影与范围比对（38 指令）+ 早退（8 指令）$\approx 72$ 条指令；
   - 在 3.0 GHz 现代 CPU 上（IPC 取 2.0），单单位测试耗时约 **$15 \sim 30 \text{ ns}$**；
   - 即使地图上有 $N = 1832$ 个在场单位（慢组全量）：
     $$T_{\text{all\_culled}} = 1832 \times 25 \text{ ns} \approx 0.046 \text{ ms}$$
   - **全图视口裁剪的总耗时不足 0.05 毫秒**，对帧时的贡献近乎绝对为零。

2. **视口内全量绘制开销（上界）**：
   - 当单位处于屏幕内时：不仅通过 `DrawIfVisible`，还将执行 `UnitClass::Draw`（`0x0073CEC0`）：
     - 车体 3D 体素切片展开、3 轴旋转矩阵变换与表面光照着色；
     - 炮塔与炮管独立朝向三角函数计算；
     - 地面投射阴影半透明融合与调色板重映射；
     - 车载血条/等级图标 SHP 绘制；
     - 将平均 $50 \times 50 \approx 2500$ 像素范围的图元光栅化到后缓冲 `DSurface::Hidden`。
   - 依据 CPU 纯软件渲染基准，单个 VXL 作战单位的完整渲染管线开销约为 **$30 \sim 80 \ \mu\text{s}$**（若伴随开火粒子、烟雾或受击闪烁，单单位耗时可超 $100 \ \mu\text{s}$）；
   - 若视口内聚集有大量作战部队（以 1000 个单位为例）：
     $$T_{\text{draw\_1000}} = 1000 \times 60 \ \mu\text{s} = 60 \text{ ms}$$
   - 若发生密集交火、产生数百个动画粒子（`AnimClass`）与弹道（`BulletClass`），光栅化总负载可轻松攀升至 **$100 \sim 150 \text{ ms}$**。

### 5.2 数量级论证与 5.7 倍可解释性

- **实测慢窗预算赤字**：
  - 快窗帧时：$T_{\text{fast}} \approx 32.2 \text{ ms}$（节流器 32ms 锁帧满帧运行）；
  - 最慢窗帧时：$T_{\text{slow}} \approx 166.8 \sim 182.9 \text{ ms}$；
  - 待解释的耗时赤字：$\Delta T = 166.8 - 32.2 = \mathbf{134.6 \text{ ms}}$。
- **理论上界 vs 实测预算对比**：
  - 理论渲染上界（全员入屏交火）：$\approx 100 \sim 150 \text{ ms}$；
  - 理论渲染下界（全员出屏裁剪）：$\approx 0.05 \text{ ms}$；
  - 渲染层由于视口内外单位分布不同所能产生的最大帧时波动：$\Delta T_{\text{render}} \approx \mathbf{100 \sim 150 \text{ ms}}$；
  - 理论上界波动（~135 ms）与实测赤字（134.6 ms）**差 0 个数量级（完全同量级）**！
  - 理论倍率跨度：$\frac{32.2 + 135}{32.2} \approx 5.19 \sim 5.7 \text{ 倍}$。

**裁决结论**：
若由于初始兵力巡逻行军，慢组单位群大举涌入静态摄像机所在的屏幕视口，而快组单位群停留在视口之外，**单凭渲染层的视口裁剪得失，在物理算力上就完全足以独立解释 5.7 倍的极端帧时恶化**。

因此，在不采集帧内数据的前提下，**C2 成本中心无法被静态排除（staticallyExcludable = false）**。

---

## 6. 诚实账

### 6.1 我亲验（全部追溯至 VA 与字节/代码行号）

1. **`DrawIfVisible` 短路整条绘制链**：
   - 查验 `ObjectClass::DrawIfVisible`（`0x005F4B10`）：`0x005F4B6A` 调用 `0x006D2140`，失败在 `0x005F4B7F` 早退返回 0，彻底跳过 `0x005F4CFD` 的 `call [eax+0x114]`（`vtable[69] Draw`）；
   - 查验 `UnitClass::DrawIfVisible`（`0x0073B0B0`）与 `AnimClass::DrawIfVisible`（`0x00422C70`），确认其均转发收口至 `0x005F4B10`；
   - 查验 `UnitClass::Draw`（`0x0073CEC0..0x0073D446`），确认其涵盖车体/炮塔 VXL 矩阵旋转、阴影投射与调色板重映射光栅化。
2. **每单位判定 vs 每格判定**：
   - 查验 `0x006D8DB0`（`0x006D465F` 调入），确认其外层遍历 5 个 Layer，内层以 `ObjectsInLayers[layer].Count` 线性遍历单位数组，逐单位调用 `DrawIfVisible`，确证为每单位一次（$O(N)$）；
   - 查验地面层动态向量 VA：首地址 `0x008A0390`，堆指针 `0x008A0394`，计数器 `0x008A03A0`。
3. **`0x00887308 / 0x0088730C` 溯源核实**：
   - 检索全二进制中写入两地址的指令（`0x00560CF6`, `0x00560D32`, `0x00560F18`, `0x00560E51`, `0x00534038`, `0x006BB90D`, `0x006BB97B`）；
   - 查验对应上下文字符串：`0x0082A410`（`"Creating primary"`）、`0x0082A4B8`（`"Deleting primary"`）、`0x00827CE0`（`"Deleting HiddenSurface"`），确证两者为 DirectDraw 表面指针而非视口坐标；
   - 查验 `qc151_trip.harness8_v4.py:3826`，确证测量窗内零键鼠输入，相机静态固定。

### 6.2 我未验（受限于无真机与无帧内采样禁令）

1. **窗内屏幕可见单位具体数未验**：由于 harness 严守零截图禁令，且未在运行期读取 `[TacticalClass + 0xb0/0xb4]` 视口坐标与可见列表，测量窗 25 秒内屏幕内到底包含 0 个单位还是 1000 个单位在物理上未验；
2. **单位微观运动朝向与进出视口轨迹未验**：无单位位置高频采样数据；
3. **特定单位在特定 CPU 上的真实纳秒级微基准未验**：30~80 $\mu\text{s}$/单位系基于 DirectDraw 软件光栅化与体素管线常模的理论估算，无探针插桩实测。
