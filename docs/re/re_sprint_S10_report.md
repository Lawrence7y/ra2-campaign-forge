# S10 专项逆向工程冲刺报告：雷达小地图点绘与侧边栏 UI 深潜

> **冲刺编号**：S10  
> **基准程序**：`ra2youli/gamemd.exe` (MD 1.001)  
> **基址与映射**：`ImageBase = 0x00400000`，`.text VA = 0x00401000`，文件偏移 `FileOffset = VA - 0x00400000`  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **核心工具**：Python 3.12 + Capstone 5.0.7 + Pefile  
> **纪律状态**：`ra2render/**` 与 `REVERSE_ENGINEERING_AND_PATCHES.md` 未改动；`docs/re/sidebar_selection_ui.md` 严格保持只读引用；`docs/re/radar_minimap_dots.md` 仅原地追加第 9 节；所有实验脚本均存放在 `out/re_work/re_sprint/S10/` 目录下。

---

## 1. 执行摘要与结论速览

| 研究课题 | 关键结论 | 证据等级 |
|---|---|---|
| **1. 小地图点绘内层物理隔离** | 雷达小地图点绘并非全图重算，而是严格分阶段：先由 `0x006571DA call 0x00655250` 更新地形缓冲并产出脏矩形 `[esi+0x1248]`；再由 `0x00657353 call [eax+8]`（`Surface::BlitRect`）将背景表面 `[esi+0x1220]` 覆写到雷达表面 `[esi+0x121C]`（抹掉旧点）；最后通过**两大循环**调用 `0x00655C50`（脏矩形逐像素扫描 `0x0065749E..` + 脏点向量逆序扫描 `0x0065750B..`）在雷达表面叠加单位色点。第三处全图调用点位于 `0x00657D77`（`0x00657CE0` 全图重建）。 | `[实证]` |
| **2. Cameo 脏门与 CanBuild 频率** | 全 exe 直呼 `0x004F7870`（`HouseClass::CanBuild`）共 13 处，渲染帧仅 `0x006A97D2`（位于 `0x006A9540`）一处。`0x006A9540` 入口受 `AllowedToDraw`（`+0x1C`）与 `NeedsRedraw`（`+0x3C`）双门控保护。在静态帧中该函数 7 条指令退出，`CanBuild` 调用为 **0 次/帧**；仅在逻辑置脏帧重绘，且仅轮询当前 Tab 可见槽（6~10 个），绝非每帧轮询 75 个或科技树。 | `[实证]` |
| **3. 点击 / 框选与迷雾交互** | ① **框选（Band Select）**：扫描 `0x00B0CEC8`，回调 `0x004AC2B0` 经 `0x0050B6F0` 铁闸硬性过滤非本地/盟军单位，**敌方隐形/灰雾/迷雾单位绝不可能被误框选中**；② **单键点选（Single Click）**：`ProcessClickCoords`（`0x00692300`）在 `IsShrouded`（`0x00586360`）时直接跳过对象查找（黑雾不可点）；虽然 `0x005865E0` 灰雾判定为空桩（`xor al,al; ret 4`），但 `0x006DA380` 仅检测当前帧实际渲染的 `0x00B0CEC8` 交互表，且在 `0x006DA409` 硬拦截无探测器的隐形单位（`CloakState==2`）。**敌方隐形单位在无探测器时绝对无法被盲点**。 | `[实证]` |

---

## 2. 课题一：雷达小地图“点绘内层”隔离定位与物理分界

### 2.1 整体调度链与物理分界总图

反汇编展开 `RadarClass::DrawMap`（`0x00656EC0`，VA: 0x00656EC0, FileOffset: 0x00256EC0）：

```
0x00656EC0 (RadarClass::DrawMap)
  │
  ├─ 0x00657180 - 0x006571C3 : 帧级脏门控（视口、雷达事件、脏点数、脏格数、屏幕脏区）
  │                             若无脏区，je 0x00657872 (直接返回，0 成本)
  │
  ├─ 0x006571DA : call 0x00655250 (RadarClass::DrawTerrainCache)
  │               消费待重绘格向量 [esi+0x1228..1234]，写 RGB 缓冲 [esi+0x123C]
  │               产出脏矩形 [esi+0x1248] (RectangleStruct{X, Y, W, H})
  │
  ├─ 0x0065733E - 0x00657353 : ★ 物理基底还原（Erase to Background）
  │               call dword ptr [eax + 8] (Surface::BlitRect)
  │               源：[esi+0x1220] (静态干净背景 BSurface)
  │               目：[esi+0x121C] (雷达工作表面 DSurface)
  │               区域：[esi+0x1248] (脏矩形)
  │               --> 擦除上一帧该区域内残留的单位点、建筑块和视口白框
  │
  ├─ 0x0065749E - 0x006574F1 : ★ 循环 1（脏矩形网格逐点扫描）
  │    │  双重循环：X from Rect.X to Rect.X+Rect.W, Y from Rect.Y to Rect.Y+Rect.H
  │    └─ 0x006574C3 : call 0x00655C50 (RadarClass::DrawCell, 参数 &Point2D{X, Y})
> 【W3 勘误 · W3-A6/ISSUE-DISAMBIG-RADAR-HOOK】改前：0x006574C3；改后：0x006574C3（RadarClass::Plot_Cell 主循环调用点，见 ra2render.h:158；实际补丁下沉点位于 0x00655D38，见 blitter_hooks.cpp:150, 3016）；依据：ra2render/ra2render.h:158; ra2render/blitter_hooks.cpp:150, 2711, 2920, 3016, 3090；分级：P2
  │       循环完毕后 0x006574F9.. 清零脏矩形 [esi+0x1248..1254]
  │
  ├─ 0x0065750B - 0x00657526 : ★ 循环 2（脏点向量逐点绘制）
  │    │  逆序遍历向量 [esi+0x125C] (条目首地址 [esi+0x1260], 计数 [esi+0x126C])
  │    └─ 0x00657520 : call 0x00655C50 (RadarClass::DrawCell, 参数 &Items[ebp])
  │       遍历完毕后 0x00657534 : call [edx+0xC] (Vector::Clear, Count 置 0)
  │
  ├─ 0x00657537 : call 0x00660000 (RadarEvent 闪烁事件图标渲染)
  └─ 0x006575D1 : mov ecx, [0x00887300] (DSurface::Sidebar)
                  call dword ptr [eax + 0x78] (Blit 雷达结果至侧边栏表面)
```

另有一处独立的完整重建入口：
- `0x00657CE0`（`RadarClass::FullRedraw`）：在地图初次载入或雷达全屏重置时，若 `[0x00B73550] != 0`，双重循环全图宽高，在 `0x00657D77: call 0x00655C50`。

### 2.2 汇编实证：物理分界指令与寄存器状态

#### 1) 脏门控短路指令 `[实证]`
```x86asm
0065719A (FO:0025719A)  e891930000    call    0x660530        ; 检查是否有雷达事件更新
0065719F (FO:0025719F)  84c0          test    al, al
006571A1 (FO:002571A1)  7426          je      0x6571c9        ; 有事件 -> 进重绘
006571A3 (FO:002571A3)  8b866c120000  mov     eax, [esi+0x126c]; 待重绘脏点向量 Count
006571A9 (FO:002571A9)  85c0          test    eax, eax
006571AB (FO:002571AB)  7f1c          jg      0x6571c9        ; 脏点 > 0 -> 进重绘
006571AD (FO:002571AD)  8b8634120000  mov     eax, [esi+0x1234]; 待重绘格子列表 Count
006571B3 (FO:002571B3)  85c0          test    eax, eax
006571B5 (FO:002571B5)  7f12          jg      0x6571c9        ; 脏格 > 0 -> 进重绘
006571B7 (FO:002571B7)  b9b0c38900    mov     ecx, 0x89c3b0
006571BC (FO:002571BC)  e83fa6ddff    call    0x431800        ; 视口脏区检测
006571C1 (FO:002571C1)  84c0          test    al, al
006571C3 (FO:002571C3)  0f84a9060000  je      0x657872        ; 全部干净 -> 直接跳退出点！
```

#### 2) 地形擦除到背景物理分界 `[实证]`
```x86asm
0065733E (FO:0025733E)  8b8e1c120000  mov     ecx, [esi+0x121c]; ecx = 雷达目标 Surface*
00657344 (FO:00257344)  8b9620120000  mov     edx, [esi+0x1220]; edx = 干净背景 Surface*
0065734A (FO:0025734A)  6a01          push    1
0065734C (FO:0025734C)  6a00          push    0
0065734E (FO:0025734E)  8b01          mov     eax, [ecx]
00657350 (FO:00257350)  55            push    ebp              ; ebp = [esi+0x1248] 脏矩形
00657351 (FO:00257351)  52            push    edx              ; 源表面
00657352 (FO:00257352)  55            push    ebp              ; 目的矩形
00657353 (FO:00257353)  ff5008        call    dword ptr [eax+8]; Surface::BlitRect！
```
**物理边界分析**：此处是严格的时序截断。调用前，目标表面包含旧帧像素；调用后，脏矩形内的所有旧像素被背景地表无条件覆写。后续循环向其写入的点绘像素将覆盖在地表之上。

#### 3) 循环 1：脏矩形逐像素点绘循环 `[实证]`
```x86asm
0065749E (FO:0025749E)  8b9e4c120000  mov     ebx, [esi+0x124c]; ebx = Rect.Y
006574A4 (FO:002574A4)  8b9654120000  mov     edx, [esi+0x1254]; edx = Rect.Height
006574AA (FO:002574AA)  03d3          add     edx, ebx         ; edx = Y_end
006574AC (FO:002574AC)  3bda          cmp     ebx, edx
006574AE (FO:002574AE)  7d2b          jge     0x6574db         ; Y >= Y_end -> 下一列
006574B0 (FO:002574B0)  8b442414      mov     eax, [esp+0x14]  ; eax = X
006574B4 (FO:002574B4)  8d4c2438      lea     ecx, [esp+0x38]  ; Point2D 栈缓冲
006574B8 (FO:002574B8)  51            push    ecx              ; arg = Point2D*
006574B9 (FO:002574B9)  8bce          mov     ecx, esi         ; ecx = this (RadarClass*)
006574BB (FO:002574BB)  8944243c      mov     [esp+0x3c], eax  ; Point2D.X = X
006574BF (FO:002574BF)  895c2440      mov     [esp+0x40], ebx  ; Point2D.Y = Y
006574C3 (FO:002574C3)  e888e7ffff    call    0x655c50         ; ★ RadarClass::DrawCell
006574C8 (FO:002574C8)  8b9654120000  mov     edx, [esi+0x1254]
006574CE (FO:002574CE)  8b8e4c120000  mov     ecx, [esi+0x124c]
006574D4 (FO:002574D4)  43            inc     ebx              ; Y++
006574D5 (FO:002574D5)  03d1          add     edx, ecx
006574D7 (FO:002574D7)  3bda          cmp     ebx, edx
006574D9 (FO:002574D9)  7cd5          jl      0x6574b0         ; 继续 Y 循环
...
006574F3 (FO:002574F3)  33c0          xor     eax, eax
006574F9 (FO:002574F9)  894500        mov     [ebp], eax       ; Rect.X = 0
006574FE (FO:002574FE)  894d04        mov     [ebp+4], ecx     ; Rect.Y = 0
00657501 (FO:00257501)  895508        mov     [ebp+8], edx     ; Rect.W = 0
00657504 (FO:00257504)  895d0c        mov     [ebp+0xc], ebx   ; Rect.H = 0 (清空脏矩形)
```

#### 4) 循环 2：脏点向量逆序重绘循环 `[实证]`
```x86asm
0065750B (FO:0025750B)  8bae6c120000  mov     ebp, [esi+0x126c]; ebp = this->DirtyPoints.Count
00657511 (FO:00257511)  4d            dec     ebp              ; index = Count - 1
00657512 (FO:00257512)  7814          js      0x657528         ; Count == 0 -> 跳过
00657514 (FO:00257514)  8b9660120000  mov     edx, [esi+0x1260]; edx = Point2D* 数组首地址
0065751A (FO:0025751A)  8bce          mov     ecx, esi         ; ecx = this (RadarClass*)
0065751C (FO:0025751C)  8d04ea        lea     eax, [edx+ebp*8] ; 条目 8 字节 (int X, int Y)
0065751F (FO:0025751F)  50            push    eax              ; arg = Point2D*
00657520 (FO:00257520)  e82be7ffff    call    0x655c50         ; ★ RadarClass::DrawCell
00657525 (FO:00257525)  4d            dec     ebp
00657526 (FO:00257526)  79ec          jns     0x657514         ; 继续逆序循环
00657528 (FO:00257528)  8b965c120000  mov     edx, [esi+0x125c]; edx = Vector vtable
0065752E (FO:0025752E)  8d8e5c120000  lea     ecx, [esi+0x125c]
00657534 (FO:00257534)  ff520c        call    dword ptr [edx+0xc]; Vector::Clear (清空脏点向量)
```

### 2.3 `0x00655C50` 内层寄存器状态与无单位回退

当 `0x00655C50`（`RadarClass::DrawCell`）被调用时：
- `esi` = `RadarClass*`，`[esp+0x44]` = `Point2D*`。
- `0x00655D33: call 0x578080` 反算得到 `eax = CellClass*`，在 `0x00655D38` 存入 `[esp+0x28]`。
- 提取迷雾状态：`[esp+0x44] = isShrouded`，`[esp+0x13] = isFogged`。
- RTactical 哈希查找（`0x00655D87..`）：
  - 若桶内找到该格对象并通过类型与可见性检查，跳转至 `0x00655F48`：
    - `ebp` = `TechnoClass*`；
    - `0x00655F5F: call dword ptr [edx + 0xC4]`（`Techno::v[49]` 判断特殊色）；
    - `0x00655F80 - 0x00655FD2`：从 `[ebp+0x21C]`（`HouseClass*`）的 `+0x56F9..56FB` 打包 16 位 RGB 像素值进 `ebx`；
    - `0x00656048 / 0x0065608C`：`call dword ptr [eax + 0x24]`（`Surface::SetPixel(edi=Point2D*, ebx=Color)`）。
  - 若桶内**无任何对象**，控制流 fallthrough 到 `0x00655E7E`：
    ```x86asm
    00655E7E  8a442413      mov     al, [esp+0x13]  ; al = isFogged
    00655E82  84c0          test    al, al
    00655E84  0f84ce010000  je      0x656058        ; 非雾 -> 检查是否黑雾
    ; 灰雾地表格子变暗回退：
    00655E8A  8b8e20120000  mov     ecx, [esi+0x1220]; ecx = 背景表面
    00655E90  57            push    edi              ; edi = Point2D*
    00655E93  ff5028        call    dword ptr [eax+0x28]; GetPixel(Point2D*)
    ... (RGB 各通道 shr 1，实现 50% 亮度变暗) ...
    00655F40  ff5024        call    dword ptr [eax+0x24]; SetPixel 写回雷达表面 [esi+0x121C]
    ...
    ; 0x00656058 非雾分支：
    00656058  8a442444      mov     al, [esp+0x44]  ; al = isShrouded
    0065605C  84c0          test    al, al
    0065605E  7521          jne     0x656081        ; 是未探索黑雾 -> 写 0 (纯黑)
    ; Clear 地表格子原样拷贝：
    00656060  mov ecx, [esi+0x1220]; 背景表面 GetPixel
    0065607C  call [ebx+0x24]; SetPixel 写回雷达表面 [esi+0x121C]
    ```

---

## 3. 课题二：Cameo 脏门与 CanBuild (0x004F7870) 频率与性能剖析

### 3.1 `CanBuild` (0x004F7870) 全局调用点 xref 普查

在 `gamemd.exe` 全代码段执行立即数扫描，直呼 `0x004F7870` 的指令精确为 **13 处**：

| # | 调用点 VA | 文件偏移 | 所在函数 | 模块职责 | 频次特征 |
|---|---|---|---|---|---|
| 1 | `0x004140CC` | `0x000140CC` | `0x00414080` | AITrigger 条件判据 | 触发器判定时（低频） |
| 2 | `0x00445758` | `0x00045758` | `BuildingClass::v[312]` (`0x4456D0`) | 建筑 AI / 放置限制 | AI 建造决断时（低频） |
| 3 | `0x0044579D` | `0x0004579D` | `BuildingClass::v[312]` (`0x4456D0`) | 建筑 AI / 建造上限检查 | 同上 |
| 4 | `0x004457DE` | `0x000457DE` | `BuildingClass::v[312]` (`0x4456D0`) | 建筑 AI / 工厂可用性 | 同上 |
| 5 | `0x0044581E` | `0x0004581E` | `BuildingClass::v[312]` (`0x4456D0`) | 建筑 AI / 前置科技确认 | 同上 |
| 6 | `0x004FEDB7` | `0x000FEDB7` | `0x004FEA60` | HouseClass AI 建造决策 | AI 决策帧（数秒一次） |
| 7 | `0x004FF0E1` | `0x000FF0E1` | `0x004FEEE0` | HouseClass AI 步兵生产决策 | 同上 |
| 8 | `0x004FF411` | `0x000FF411` | `0x004FF210` | HouseClass AI 载具生产决策 | 同上 |
| 9 | `0x00517DDB` | `0x00017DDB` | `0x00517D90` | 生产队列就绪回调 | 生产完成时（偶发） |
| 10 | `0x005F79A3` | `0x001F79A3` | `AircraftTypeClass::v[37]` | 机载航模科技判定 | 科技树查询时 |
| 11 | **`0x006A97D2`** | `0x002A97D2` | **`0x006A9540`** | **SidebarClass Cameo 条绘制** | **仅 Tab 脏时轮询可见槽** |
| 12 | `0x006AA781` | `0x002AA781` | `0x006AA600` | SidebarClass 槽位重排比对 | 仅逻辑置脏时调用 |
| 13 | `0x007357DF` | `0x003357DF` | `0x00735780` | 脚本/触发器 Action 执行 | 剧情脚本触发时 |

### 3.2 渲染帧入口脏门控证据 `[实证]`

反汇编 `0x006A9540`（`SidebarClass::DrawStrip`，ecx = `TabDataStruct*`）：
```x86asm
006A9540 (FO:002A9540)  81ec7c040000  sub     esp, 0x47c
006A9546 (FO:002A9546)  56            push    esi
006A9547 (FO:002A9547)  8bf1          mov     esi, ecx        ; esi = TabDataStruct* (&Tabs[ActiveTab])
006A9549 (FO:002A9549)  89742418      mov     [esp+0x18], esi
006A954D (FO:002A954D)  8a461c        mov     al, [esi+0x1c]  ; ★ 门控 1: AllowedToDraw
006A9550 (FO:002A9550)  84c0          test    al, al
006A9552 (FO:002A9552)  0f8450100000  je      0x6aa5a8        ; 为 0 直接退出！
006A9558 (FO:002A9558)  8a463c        mov     al, [esi+0x3c]  ; ★ 门控 2: NeedsRedraw
006A955B (FO:002A955B)  84c0          test    al, al
006A955D (FO:002A955D)  750f          jne     0x6a956e        ; 脏 -> 放行进绘制循环
006A955F (FO:002A955F)  8a842484040000 mov    al, [esp+0x484] ; ★ 门控 3: force argument (SidebarNeedsRedraw)
006A9566 (FO:002A9566)  84c0          test    al, al
006A9568 (FO:002A9568)  0f843a100000  je      0x6aa5a8        ; 未置脏且未强制 -> 立即退出！
...
006A9571 (FO:002A9571)  c6463c00      mov     byte ptr [esi+0x3c], 0 ; 清除 NeedsRedraw = false
```

### 3.3 绘制循环中 CanBuild 调用频次分析

在突破门控后：
1. 循环范围：`0x006A9607 - 0x006A9640` 计算分辨率对应的行数与列数（通常为 2 列 × 3~5 行，总计 6~10 个可见槽位）。
2. 在槽位循环中（`0x006A9773..`）：
   - `0x006A9773: je 0x6a98d3`：超武图标（`ItemType == 0x1F`）直接跳转到独立的 `SuperClass` 充能状态绘制分支，**不调用 CanBuild**；
   - `0x006A97AA: call dword ptr [eax + 0x94]`：先做前置科技粗检，未通过则跳过；
   - `0x006A97BE: call 0x48DCD0`（`GetTechnoType`）；
   - `0x006A97D2: call 0x4F7870`（`HouseClass::CanBuild`），仅对可见槽位的合法 TechnoType 调 1 次；
   - 根据返回值判定：`-1` 为暂时不可建（黑幕遮罩），`0` 为完全不可建，`1` 为可建。

**结论**：
- **常态渲染帧**：`NeedsRedraw == 0`，`CanBuild` 调用频率为 **0 次/帧**。
- **状态变更帧**：`HouseClass::v[23]` 逻辑节拍置脏后，仅对当前激活 Tab 的 **6~10 个可见槽位**各调用 1 次 `CanBuild`。
- **性能瓶颈推论**：侧边栏的真正每帧固定开销是电力条与雷达小地图链（`0x0063FB20 → 0x00653100`）；Cameo 区被脏门牢牢锁住。优化侧边栏 UI 时，无需尝试改写 `CanBuild` 的前置检查逻辑，而应避免业务逻辑层非必要地高频将 `NeedsRedraw` 置 1。

---

## 4. 课题三：点击 / 框选与迷雾交互未决

### 4.1 框选（Band Select）与迷雾交互分析 `[实证]`

当玩家在屏幕上拉出拖拽框并松开左键时，执行 `DisplayClass::LMBUp`（`0x004AB9B0`）的 `DraggingRectangle`（`ebp+0x11CF`）分支：
- 调用 `TacticalClass::ForEachInRect`（`0x006DA5C0`），遍历 `0x00B0CEC8` 交互列表，对框内每个对象执行回调 `0x004AC2B0`。
- 回调 `0x004AC2B0` 源码级反汇编：
```x86asm
004AC2B0 (FO:000AC2B0)  56            push    esi
004AC2B1 (FO:000AC2B1)  8bf1          mov     esi, ecx        ; esi = Object*
004AC2B3 (FO:000AC2B3)  8b06          mov     eax, [esi]
004AC2B5 (FO:000AC2B5)  ff503c        call    dword ptr [eax+0x3c]; Object::GetOwningHouse()
004AC2B8 (FO:000AC2B8)  85c0          test    eax, eax
004AC2BA (FO:000AC2BA)  7446          je      0x4ac302
004AC2BC (FO:000AC2BC)  8bc8          mov     ecx, eax        ; ecx = HouseClass*
004AC2BE (FO:000AC2BE)  e82df40500    call    0x50b6f0        ; ★ HouseClass::RadarVisible / IsControlledByPlayer
004AC2C3 (FO:000AC2C3)  84c0          test    al, al
004AC2C5 (FO:000AC2C5)  743b          je      0x4ac302        ; ★ 非己方/盟军 -> 立即无条件抛弃！
004AC2C7 (FO:000AC2C7)  8b16          mov     edx, [esi]
004AC2CB (FO:000AC2CB)  ff9238010000  call    dword ptr [edx+0x138]; Object::v[78] (CanBeSelected)
004AC2D1 (FO:000AC2D1)  84c0          test    al, al
004AC2D3 (FO:000AC2D3)  742d          je      0x4ac302
004AC2D5 (FO:000AC2D5)  8b06          mov     eax, [esi]
004AC2D9 (FO:000AC2D9)  ff903c010000  call    dword ptr [eax+0x13c]; Object::v[79] (CanBeCommanded)
004AC2DF (FO:000AC2DF)  84c0          test    al, al
004AC2E1 (FO:000AC2E1)  741f          je      0x4ac302
004AC2ED (FO:000AC2ED)  8b16          mov     edx, [esi]
004AC2F1 (FO:000AC2F1)  ff924c010000  call    dword ptr [edx+0x14c]; Object::v[83] (Select)
```
- **结论**：
  1. 框选回调内部**完全没有**调用 `IsShrouded`（`0x00586360`）或 `IsFogged`（`0x005864A0`）；
  2. 但第 1 道门控是 `0x0050B6F0`。对敌方单位，`0x0050B6F0` 恒返回 0，直接 `je 0x4ac302` 过滤。因此，**无论敌方单位处于明处、灰雾还是黑雾，也无论是否隐形，玩家画框绝对不可能将其选中**。
  3. 己方或盟军单位若停留在黑雾或灰雾区域，只要其屏幕坐标落在拉框矩形内，因属于己方（`0x0050B6F0` 返回 1），将被正常框选。

### 4.2 单键点选（Single Click）与迷雾交互分析 `[实证]`

单键点击时，坐标解析经由 `ProcessClickCoords`（`0x00692300`）：

#### 1) 黑雾拦截逻辑（`0x00692480 - 0x0069250E`）
```x86asm
00692480 (FO:00292480)  e8db3eefff    call    0x586360        ; MapClass::IsShrouded(cell)
00692485 (FO:00292485)  84c0          test    al, al
00692487 (FO:00292487)  7410          je      0x692499
00692489 (FO:00292489)  a15035b700    mov     eax, [0xb73550] ; 迷雾检查开关
0069248E (FO:0029248E)  85c0          test    eax, eax
00692490 (FO:00292490)  7407          je      0x692499
00692492 (FO:00292492)  b801000000    mov     eax, 1
00692497 (FO:00292497)  eb02          jmp     0x69249b
00692499 (FO:00292499)  33c0          xor     eax, eax
0069249B (FO:0029249B)  8b742440      mov     esi, [esp+0x40] ; esi = outShrouded 指针
0069249F (FO:0029249F)  8806          mov     [esi], al       ; *outShrouded = 1
...
006924D5 (FO:002924D5)  8d542410      lea     edx, [esp+0x10]
006924DF (FO:002924DF)  e8fc40efff    call    0x5865e0        ; ★ 灰雾判定调用
...
006924FC (FO:002924FC)  803e00        cmp     byte ptr [esi], 0; 检查 *outShrouded
006924FF (FO:002924FF)  0f85eb000000  jne     0x6925f0        ; ★ 为 1 直接跳过鼠标下对象解析！
00692505 (FO:00292505)  803f00        cmp     byte ptr [edi], 0; 检查 *outFogged
00692508 (FO:00292508)  0f85e2000000  jne     0x6925f0        ; 为 1 直接跳过
0069250E (FO:0029250E)  8b0d24738800  mov     ecx, [0x887324] ; ecx = TacticalClass*
00692514 (FO:00292514)  55            push    ebp              ; 鼠标屏幕坐标
00692515 (FO:00292515)  e8667e0400    call    0x6da380        ; ★ TacticalClass::ObjectUnderCursor
0069251A (FO:0029251A)  8b7c2438      mov     edi, [esp+0x38]
0069251E (FO:0029251E)  8bc8          mov     ecx, eax
00692520 (FO:00292520)  8907          mov     [edi], eax      ; *outObject = eax
```
- **黑雾判定结果**：若格子处于未探索黑雾，`*outShrouded = 1`，指令在 `0x006924FF` 直接跳转到 `0x006925F0`，彻底绕过了 `0x006DA380`，输出对象恒为 NULL。**玩家在黑雾中无法点中任何单位**。

#### 2) 灰雾空桩缺陷分析
在 `0x006924DF` 处调用的 `0x005865E0`，反汇编其实体代码为：
```x86asm
005865E0 (FO:001865E0)  32c0    xor     al, al
005865E2 (FO:001865E2)  c20400  ret     4
```
该函数恒返回 0，导致 `*outFogged` 永远为 0。**原版引擎在点击分支中对灰雾的拦截是失效的**。

#### 3) 屏幕交互列表（0xB0CEC8）与隐形拦截（0x006DA380）
尽管灰雾未在 `ProcessClickCoords` 中拦截，但进入 `0x006DA380`（`TacticalClass::ObjectUnderCursor`）后存在底层物理约束与隐形检测：
1. **列表来源物理约束**：
   - 逆向全代码段对 `0x00B0CEC8` 写入函数的普查确认，仅有 `0x006D9EF0` 向该表插入条目；
   - `0x006D9EF0` 的所有调用者均为 `AircraftClass::v[69]`（`0x004148CC`）、`InfantryClass::v[69]`（`0x005192E6`）、`UnitClass::v[69]`（`0x0073CF6B`）；
   - 在每帧世界视图渲染前，`TacticalClass::Draw`（`0x006D3D21: mov dword ptr [ebp+0xDB0], 0`）清空列表；
   - **推论**：只有在当前帧被渲染管线实际执行了 `Draw` 的单位，才会进入 `0x00B0CEC8`。若敌方单位因视野受限未被世界视图渲染，则其不在该列表中，点击该位置将返回 NULL。
2. **隐形单位显式硬拦截 `[实证]`**：
   在 `0x006DA380`（`ObjectUnderCursor`）内部，对候选对象进行显式隐形状态检验：
   ```x86asm
   006DA409 (FO:002DA409)  83b82002000002 cmp dword ptr [eax+0x220], 2 ; CloakState == Cloaked?
   006DA410 (FO:002DA410)  752c          jne 0x6da43e                 ; 非隐形 -> 允许选中 (bl=1)
   006DA412 (FO:002DA412)  8b0d4c3da800  mov ecx, [0xa83d4c]          ; ecx = PlayerHouse*
   006DA418 (FO:002DA418)  8b5130        mov edx, [ecx+0x30]          ; edx = PlayerHouse 掩码
   006DA425 (FO:002DA425)  ff5248        call dword ptr [edx+0x48]    ; 获取坐标
   006DA42E (FO:002DA42E)  e8fdb2e8ff    call 0x565730                ; 取 MapCell
   006DA435 (FO:002DA435)  e896ccdaff    call 0x4870d0                ; ★ CellClass::Sensors (探测器检查)
   006DA43A (FO:002DA43A)  84c0          test al, al
   006DA43C (FO:002DA43C)  7402          je  0x6da440                 ; 无探测器覆盖 -> bl=0 (抛弃该单位！)
   006DA43E (FO:002DA43E)  b301          mov bl, 1                    ; 有探测器 -> bl=1 (允许选中)
   ```
   **结论**：即使处于已探索区域，**敌方隐形单位在玩家没有探测器覆盖该格时，绝对不可能被鼠标单键盲点选中**。

---

## 5. 关键地址与数据结构总账

| 符号 / 功能 | VA | FileOffset | 说明 |
|---|---|---|---|
| `RadarClass::DrawMap` | `0x00656EC0` | `0x00256EC0` | 小地图顶层绘制（帧级脏门控、地形擦除、双重点绘循环） |
| `RadarClass::DrawTerrainCache` | `0x00655250` | `0x00255250` | 消费 `[esi+0x1228..1234]` 脏格，写 `+0x123C` 缓冲与 `+0x1248` 脏矩形 |
| `RadarClass::DrawCell` | `0x00655C50` | `0x00255C50` | 小地图单像素/格点绘内层（查 RTactical、House 颜色、SetPixel） |
| `RadarClass::FullRedraw` | `0x00657CE0` | `0x00257CE0` | 全图小地图重建（全图双重循环，第三处调用 `0x655C50`） |
| `HouseClass::CanBuild` | `0x004F7870` | `0x000F7870` | 科技树与建造许可核心判定（全 exe 共 13 处调用） |
| `SidebarClass::DrawStrip` | `0x006A9540` | `0x002A9540` | 侧边栏 Cameo 条绘制（受 `AllowedToDraw` 与 `NeedsRedraw` 门控） |
| `SidebarClass::RecalcCameos` | `0x006AA600` | `0x002AA600` | 侧边栏 Cameo 重排与脏标记置位助手 |
| `HouseClass::UpdateCameos` | `0x006A7D20` | `0x002A7D20` | 逻辑节拍驱动的侧边栏置脏入口（由 `HouseClass::v[23]` 调用） |
| `DisplayClass::LMBUp` | `0x004AB9B0` | `0x000AB9B0` | 鼠标左键抬起总收口（区分 `DraggingRectangle` 框选与单键点选） |
| `BandSelectCallback` | `0x004AC2B0` | `0x000AC2B0` | 框选对象过滤回调（经 `0x0050B6F0` 铁闸硬过滤敌方） |
| `ProcessClickCoords` | `0x00692300` | `0x00292300` | 点击坐标解析（`IsShrouded` 硬拦截，灰雾空桩漏洞） |
| `TacticalClass::ObjectUnderCursor`| `0x006DA380` | `0x002DA380` | 鼠标下对象查找（扫 `0xB0CEC8`，硬拦截未探测隐形单位） |
| `TacticalClass::InteractiveObjects`| `0x00B0CEC8` | - | 视口当前帧交互对象表（条目 12B: `{Object*, X, Y}`，上限 500） |
| `TacticalClass::InteractiveCount` | `Tactical+0xDB0` | - | 交互表当前条目计数（每帧 `0x006D3D21` 清零，单位 `Draw` 时累加） |
| `RegisterObjectForSelection` | `0x006D9EF0` | `0x002D9EF0` | 单位 `Draw` 函数向 `0x00B0CEC8` 登记的核心接口 |
| `IsShrouded` | `0x00586360` | `0x00186360` | 格子未探索判定（`Cell+0x12C` bit3 清 -> 1） |
| `IsFogged` | `0x005864A0` | `0x001864A0` | 格子灰雾判定（`Cell+0x13C > 0` -> 1） |
| `FogClickStub` | `0x005865E0` | `0x001865E0` | 点击分支中的灰雾空桩（`xor al,al; ret 4`） |
| `HouseClass::RadarVisible` | `0x0050B6F0` | `0x0010B6F0` | 本地玩家/盟军可控所有权判定（框选/点选/雷达共用闸门） |

---

## 6. S10 交付物完整性自查

1. **写作用域合规**：
   - 目标文档：`docs/re/radar_minimap_dots.md` 仅追加第 9 节“冲刺结论（S10）”，既有第 1~8 节未发生任何删改。
   - 参考文档：`docs/re/sidebar_selection_ui.md` 全程只读，未修改任何字符。
   - 顶层台账与源码：`REVERSE_ENGINEERING_AND_PATCHES.md` 与 `ra2render/**` 严格零改动。
2. **Scratch 脚本留存**：
   - `out/re_work/re_sprint/S10/disasm_tool.py`：反汇编精准转储工具。
   - `out/re_work/re_sprint/S10/find_pattern.py` / `find_db0.py` / `search_bytes.py`：特征字节与立即数/位移全镜像搜索工具。
   - `out/re_work/re_sprint/S10/check_symbols.py`：虚表槽位自动化验证工具。
3. **证据分级合规**：
   - 关键结论全部带有 `[实证]` 标识，标明了十六进制 VA、FileOffset、原始字节与对应汇编指令；
   - 逻辑推导标注为 `[推演]`。
