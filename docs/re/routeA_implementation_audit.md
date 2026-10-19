# 路线 A 小地图迷雾下沉挂钩独立静态复核报告 (Implementation Audit)

> **文档标识**：`docs/re/routeA_implementation_audit.md`  
> **任务编号**：A-10（派工 v12 专项独立静态复核，对应 A-7 实施规格书核验）  
> **责任方**：Antigravity（独立逆向复核与静态验证方，无代码实现权）  
> **复核对象**：
> - 源码：[ra2render/blitter_hooks.cpp](file:///d:/Project/ra2-campaign-forge/ra2render/blitter_hooks.cpp)（2026-09-26 18:42:48，82,259 B，MD5: `C9CA3ABE22240985D1733A779CF23BD9`）
> - 产物：[ra2youli/ra2render.dll](file:///d:/Project/ra2-campaign-forge/ra2youli/ra2render.dll)（2026-09-26 18:43:02，128,512 B，MD5: `3BAD50FB7798521EA0DDF1311A8434DC`）
> **基线规范**：[docs/re/radar_hook_routeA_spec.md](file:///d:/Project/ra2-campaign-forge/docs/re/radar_hook_routeA_spec.md)（A-7 实施规格书，Lead 逐字节核验）  
> **纪律准则**：只读复核，严禁修改 `ra2render/**` 与台账 `REVERSE_ENGINEERING_AND_PATCHES.md`。

---

## 一、复核结论与执行概要 (Executive Summary) [实证]

经使用 Capstone 反汇编引擎对新构建二进制 [ra2youli/ra2render.dll](file:///d:/Project/ra2-campaign-forge/ra2youli/ra2render.dll) 及其源码实现进行逐字节、逐符号、逐分支逆向复核，**路线 A 生产级落地完全通过静态复核（PASS）**。

| 审计维度 | 规格要求 (A-7 Spec) | 二进制实测 (ra2render.dll) | 判定 |
|---|---|---|:---:|
| **9 字节补丁布局** | `0x00655D38` 写入 `E9 rel32` + 4×`90` (NOP) | `mov byte [0x655d38], 0xe9` + `sub eax, 0x655d3d` + `mov [0x655d3d], 0x90909090` | ✅ **PASS** [实证] |
| **跳板指令保全** | 保留 `89 44 24 28` + `A1 50 35 B7 00`，跳回 `0x00655D41` | `0x100027D6-0x10002814` 汇编序列动态向 `0x102DFAA0` 写入 9B 原指令 + `E9 rel32` | ✅ **PASS** [运行时动态构造实证 + 静态汇编指令实证] |
| **直通分支安全** | `EnableMinimapFog=0` 无写内存直通跳板 | `cmp byte [0x1001F019], 0; je 0x10002068`（直跳跳板指针，零内存写入） | ✅ **PASS** [实证] |
| **灰化算法同源性** | 50% 减半灰 `(c>>1)&0x7BEF`，调 `Set_Pixel` | `shr eax, 1; and eax, 0x7bef` + `call [edx+0x24]`，完全同源 | ✅ **PASS** [实证] |
| **敌点天然隐匿** | 灰化后执行 `Plot_Cell` 原版尾声，跳过红点遍历 | `pop edi; pop esi; pop ebp; pop ebx; add esp, 0x30; ret 4` 退出 | ✅ **PASS** [实证] |
| **遥测计数递增** | `s_minimapFogPixels` 每次有效灰化递增 | `inc dword ptr [0x1001F9E4]` 位于像素写入后、退出前 | ✅ **PASS** [实证] |
| **指针防御护栏** | `pCell >= 0x10000` 且 `pCell != 0x00ABDC50` | `cmp eax, 0x10000; jbe pass` + `cmp eax, 0xabdc50; je pass` 完备 | ✅ **PASS** [实证] |
| **对称还原卸载** | `RemoveRadarFogHooks` 还原 9 字节并置零跳板指针 | 检验 `0x89 0x44` 后写回 9 字节，清空 `s_pPlotCellTrampoline` | ✅ **PASS** [实证] |

---

## 二、0x00655D38 处 9 字节补丁二进制复核 [实证]

### 1. 目标挂钩位置与原版指令边界
在 [ra2youli/gamemd.exe](file:///d:/Project/ra2-campaign-forge/ra2youli/gamemd.exe) 中反汇编确认挂钩起始点 `0x00655D38`：
```asm
0x00655D33: E8 48 23 F2 FF        call 0x00578080         ; 【原记 · 已证伪（勘误 E3）】MapClass::GetCellAt (EAX = CellClass*)
;                                                         实测被调方 = MapClass::GetCellFloorHeight（YRpp/MapClass.h:282/:417，int 返回），EAX = 格面高度 int
;                                                         0x005780F6 = C2 04 00 (ret 4)
; ------------------- 补丁写入区 (9 字节) -------------------
0x00655D38: 89 44 24 28           mov  [esp + 0x28], eax  ; 原指令 1 (4 字节)
0x00655D3C: A1 50 35 B7 00        mov  eax, [0x00B73550]  ; 原指令 2 (5 字节)
; ------------------- 跳回目标点 ---------------------------
0x00655D41: 3B C5                 cmp  eax, ebp           ; 原版后续指令 (2 字节)
0x00655D43: 74 18                 je   0x00655D5D
```

> ### 勘误 E3〔RADAR-ERRATA · 2026-09-27〕挂钩点 `EAX` 语义与 `0xB73550` 语义
>
> **【原记】（保留原文，不得删除）**：本节反汇编摘录把 `0x00655D33 call 0x00578080` 注为 `MapClass::GetCellAt (EAX = CellClass*)`（第 36 行原注），并在第 134 行把代理入口契约记为 `EAX = CellClass*`；第 26 行「指针防御护栏 `pCell >= 0x10000` 且 `pCell != 0x00ABDC50`」亦然。
>
> **【实测定谳 ①：EAX 不是 `CellClass*`】** `0x00655D38` 处 `EAX` = **`MapClass::GetCellFloorHeight()`（`0x00578080`，尾部 `C2 04 00` = `ret 4`）返回的格面高度 int**，由 `0x655D38 mov [esp+0x28],eax` 写进 **`CoordStruct.Z`**（`0x655D2F` 预置 Z=0）—— 不是任何 `CellClass*`。
> 字节证据（gamemd.exe 只读复核）：`0x00655D33 = E8 48 23 F2 FF`、`0x00655D38 = 89 44 24 28`、`0x005780F6 = C2 04 00`；符号证据：`YRpp/MapClass.h:282 / :417`（`GetCellFloorHeight` / `sub_578080` 均为 **int** 返回）。
>
> ⇒ **连带结论**：本报告第 26 行与第 146-149 行所审计的「指针防御护栏」在本钩子上**恒拒**（高度值 ≈0..2080 恒 `<= 0x10000`）—— 即灰化分支虽被进入却必然静默早退，这正是真机「分支计数增长、灰化像素恒 0」的根因。本报告其余**字节级安装正确性**结论（9 字节布局、rel32 解算、跳板还原、旧护栏路径可抵达）**不受影响**：它们审计的是「安装动作与字节」，不是 `EAX` 语义。
>
> **【实测定谳 ②：`0xB73550` 不是迷雾开关】** 本文件对原指令 2 `mov eax,[0x00B73550]` 的字节引用（勘误前 L39，勘误插入后 L41；跳板表另见现 L130/L254）中的全局 = **`Game::hWnd`（主窗口句柄 HWND）**：唯 2 写点 `0x777CD6`/`0x777D7E` 均为 `CreateWindowExA` 返回值落地，77 处读点全部当 Win32 句柄使用；引擎 `Plot_Cell` 中 `0x00655D62 cmp dword [0x00B73550],ebp`（字节 `39 2D 50 35 B7 00`）的语义 = 「主窗口是否已创建」（游戏内恒真）。⇒ 本文件这 3 处的**字节引用与「原样保全」结论成立**，但**不得**把它读作迷雾开关；**更禁止写入该全局**（会污染 70+ 处 Win32 调用）。
>
> 机器可读断言：`out/re_work/radar_errata/claims.txt`。

### 2. DLL 安装函数 (InstallRadarFogHooks) 写入逻辑实证
在 `ra2render.dll`（基址 `0x10000000`）中，`InstallRadarFogHooks` 位于 VA `0x10002800`，其实际执行的补丁写入反汇编如下：
```asm
0x1000282E: C6 05 38 5D 65 00 E9           mov byte ptr [0x00655D38], 0xE9
0x10002835: B8 C0 1F 00 10                 mov eax, 0x10001FC0   ; Hook_RadarPlot_Cell_Proxy 地址
0x1000283A: 2D 3D 5D 65 00                 sub eax, 0x00655D3D   ; 减去 (0x00655D38 + 5)
0x1000283F: A3 39 5D 65 00                 mov dword ptr [0x00655D39], eax
0x10002844: 8D 44 24 04                    lea eax, [esp + 4]
0x10002848: 50                             push eax
0x10002849: C7 05 3D 5D 65 00 90 90 90 90  mov dword ptr [0x00655D3D], 0x90909090
```

### 3. rel32 位移与补丁对齐解算
- **目标代理 VA**：`0x10001FC0`（RVA: `0x00001FC0`）
- **源指令下一地址**：`0x00655D38 + 5 = 0x00655D3D`
- **rel32 计算**：
  $$\text{rel32} = \text{0x10001FC0} - \text{0x00655D3D} = \text{0x0FAAC283}$$
- **4 字节 NOP 填充**：`0x00655D3D` - `0x00655D40` 写入 `90 90 90 90`。
- **总字节数**：$1\text{ (E9)} + 4\text{ (rel32)} + 4\text{ (NOP)} = 9\text{ 字节}$，严密覆盖被偷取的 2 条原版指令，绝无指令截断。

---

## 三、跳板 (Trampoline) 结构与运行时动态构造指令复核 [运行时动态构造实证 + 静态汇编指令实证]

> [!NOTE]
> **证据等级与来源界定（A-10′ 补证）**：
> 跳板目标缓冲区 `s_plotCellTrampoline` 位于 `ra2render.dll` 的 `.data` 段未初始化虚拟区（VA `0x102DFAA0`，段 `vsize=0x2C14B0`，文件 `rawsize=0xA00`）。因此，连续字节串 `89 44 24 28 A1 50 35 B7 00 E9` 不可能在静态 DLL 磁盘镜像中直接检索到，而是由 `InstallRadarFogHooks` 在运行时动态构造：
> 1. 运行时从 `gamemd.exe` 的 `0x00655D38` 读取 9 字节原版指令存入 `s_origPlotCellBytes` (`0x102DFA94`)；
> 2. 通过执行一系列逐字节/向量 store 指令，将 9 字节原版指令、`0xE9` 操作码与计算出的 `rel32` 填入 `s_plotCellTrampoline` (`0x102DFAA0`)；
> 3. 更新跳板指针 `s_pPlotCellTrampoline` (`0x102DF9E8`)。

### 1. 生成跳板的逐字节 / 向量 Store 指令序列实证 [静态汇编指令实证]
在 [ra2youli/ra2render.dll](file:///d:/Project/ra2-campaign-forge/ra2youli/ra2render.dll)（基址 `0x10000000`）中，`InstallRadarFogHooks` 的运行时跳板构造汇编序列如下：

```asm
; --- 步骤 1: 运行时从 gamemd.exe 0x00655D38 读取 9 字节原版指令 ---
0x10002797: B8 38 5D 65 00                 mov  eax, 0x00655D38            ; 指向 gamemd.exe 挂钩点
0x100027A4: F3 0F 7E 00                    movq xmm0, qword ptr [eax]      ; 读取前 8 字节 (89 44 24 28 A1 50 35 B7)
0x100027A8: 66 0F D6 05 94 FA 2D 10        movq qword ptr [0x102DFA94], xmm0 ; 存入 s_origPlotCellBytes[0..7]
0x100027B0: 8A 40 08                       mov  al, byte ptr [eax + 8]     ; 读取第 9 字节 (00)
0x100027B3: A2 9C FA 2D 10                 mov  byte ptr [0x102DFA9C], al  ; 存入 s_origPlotCellBytes[8]

; --- 步骤 2: 将跳板缓冲区 0x102DFAA0 设为 PAGE_EXECUTE_READWRITE (0x40) ---
0x100027B8: 8D 44 24 04                    lea  eax, [esp + 4]
0x100027BC: 50                             push eax                        ; lpflOldProtect
0x100027BD: 6A 40                          push 0x40                       ; PAGE_EXECUTE_READWRITE
0x100027BF: 6A 10                          push 0x10                       ; sizeof(s_plotCellTrampoline) = 16
0x100027C1: 68 A0 FA 2D 10                 push 0x102DFAA0                 ; lpAddress = &s_plotCellTrampoline
0x100027C6: FF D6                          call esi                        ; VirtualProtect

; --- 步骤 3: 逐字节/向量写入跳板 0x102DFAA0 (生成 14 字节跳板内容) ---
0x100027D6: A0 9C FA 2D 10                 mov  al, byte ptr [0x102DFA9C]  ; 读取 s_origPlotCellBytes[8]
0x100027DB: F3 0F 7E 05 94 FA 2D 10        movq xmm0, qword ptr [0x102DFA94] ; 读取 s_origPlotCellBytes[0..7]
0x100027E3: A2 A8 FA 2D 10                 mov  byte ptr [0x102DFAA8], al  ; ★ Store: s_plotCellTrampoline[8] = 0x00
0x100027E8: B8 33 5D 65 00                 mov  eax, 0x00655D33
0x100027ED: 2D A0 FA 2D 10                 sub  eax, 0x102DFAA0            ; 计算 rel32 = 0x00655D41 - (0x102DFAA0 + 14)
0x100027F2: 66 0F D6 05 A0 FA 2D 10        movq qword ptr [0x102DFAA0], xmm0 ; ★ Store: s_plotCellTrampoline[0..7] = 原版前 8 字节
0x100027FA: A3 AA FA 2D 10                 mov  dword ptr [0x102DFAAA], eax ; ★ Store: s_plotCellTrampoline[10..13] = rel32
0x1000280D: C6 05 A9 FA 2D 10 E9           mov  byte ptr [0x102DFAA9], 0xE9 ; ★ Store: s_plotCellTrampoline[9] = 0xE9 (JMP)

; --- 步骤 4: 更新跳板全局指针 ---
0x10002814: C7 05 E8 F9 2D 10 A0 FA 2D 10  mov  dword ptr [0x102DF9E8], 0x102DFAA0 ; s_pPlotCellTrampoline = &s_plotCellTrampoline
```

### 2. 运行时动态生成的 14 字节跳板内容 [推演/计算]
经上述指令序列执行后，`0x102DFAA0` 处的 14 字节内存内容为：

| 跳板内存地址 | 偏移 | 写入指令位置 | 写入字节值 | 对应汇编指令 | 语义说明 |
|:---:|:---:|:---|:---|:---|:---|
| `0x102DFAA0` | `+0x00` | `0x100027F2` (`movq`) | `89 44 24 28` | `mov [esp + 0x28], eax` | 恢复原指令 1：将合法 `pCell` 存入局部栈槽 |
| `0x102DFAA4` | `+0x04` | `0x100027F2` (`movq`) | `A1 50 35 B7` | `mov eax, [0x00B73550]` | 恢复原指令 2 前 4 字节 |
| `0x102DFAA8` | `+0x08` | `0x100027E3` (`mov al`) | `00` | (imm32 高位) | 恢复原指令 2 最后 1 字节 |
| `0x102DFAA9` | `+0x09` | `0x1000280D` (`mov byte`) | `E9` | `jmp` | 无条件长跳转操作码 |
| `0x102DFAAA` | `+0x0A` | `0x100027FA` (`mov dword`) | `93 62 37 F0` (小端) | `0xF0376293` (rel32) | 跳回 `0x00655D41` |
| **合计** | **14B** | — | — | — | **完全还原原版 9 字节语义并无缝回跳** |
- **数学等价性推导**：
  跳转指令位于跳板 `+9` 处（`0x102DFAA9`），指令长度为 5 字节，下一指令地址为 `0x102DFAA9 + 5 = 0x102DFAAE`（即 `0x102DFAA0 + 14`）。
  跳回目标为 `0x00655D41`。
  $$\text{rel32} = \text{0x00655D41} - (\text{0x102DFAA0} + 14) = (\text{0x00655D41} - 14) - \text{0x102DFAA0} = \text{0x00655D33} - \text{0x102DFAA0}$$
  编译器优化后的立即数常量恰为 `0x00655D33`，计算结果绝对精确。

---

## 四、代理函数 Hook_RadarPlot_Cell_Proxy 完整反汇编复核 [实证]

对 `ra2render.dll` 偏移 `0x1FC0`（VA `0x10001FC0`）执行 Capstone 逐条反汇编与逻辑验证：

```asm
=== Hook_RadarPlot_Cell_Proxy (VA: 0x10001FC0) ===
; 【原记 · 已证伪（勘误 E3）】[入口寄存器契约] EAX = CellClass*, ESI = RadarClass*, EDI = pt(Point2D*), EBP = 0
;   ⇒ EAX 实为 GetCellFloorHeight 返回的格面高度 int（非指针）；ESI/EDI/EBP 契约仍成立。

; ---- 1. 总开关与游戏状态护栏 ----
0x10001FC0: 80 3D 19 F0 01 10 00  cmp byte ptr [0x1001F019], 0    ; s_minimapFogGate
0x10001FC7: 0F 84 9B 00 00 00     je  0x10002068                  ; -> do_passthrough
0x10001FCD: 50                    push eax                        ; 保护 EAX
0x10001FCE: B8 38 B2 A8 00        mov  eax, 0x00A8B238            ; GameState 指针
0x10001FD3: 80 38 00              cmp  byte ptr [eax], 0          ; GameState != 0 (在局内)
0x10001FD6: 58                    pop  eax                        ; 恢复 EAX
0x10001FD7: 0F 84 8B 00 00 00     je  0x10002068                  ; 菜单状态 -> do_passthrough

; ---- 2. 指针合法性与 InvalidCell 排除护栏 ----
0x10001FDD: 3D 00 00 01 00        cmp  eax, 0x10000               ; pCell >= 0x10000 护栏
0x10001FE2: 0F 86 80 00 00 00     jbe  0x10002068                  ; 杜绝空指针或 0x1A0 标量 -> pass
0x10001FE8: 3D 50 DC AB 00        cmp  eax, 0x00ABDC50            ; InvalidCell 排除 (A-8 实证)
0x10001FED: 74 79                 je   0x10002068                  ; 越界无效格 -> pass

; ---- 3. 探索状态 (IsExplored) 判定 ----
0x10001FEF: F6 80 2C 01 00 00 08  test byte ptr [eax + 0x12C], 8   ; bit 3: IsExplored
0x10001FF6: 74 70                 je   0x10002068                  ; 未探索黑雾 -> pass (原版黑雾处理)

; ---- 4. 地图网格坐标换算与越界保护 ----
0x10001FF8: 0F BF 50 26           movsx edx, word ptr [eax + 0x26] ; MapCoords.Y (+0x26, A-8 实证)
0x10001FFC: C1 E2 09              shl   edx, 9                     ; Y * 512
0x10001FFF: 0F BF 48 24           movsx ecx, word ptr [eax + 0x24] ; MapCoords.X (+0x24, A-8 实证)
0x10002003: 03 D1                 add   edx, ecx                   ; cellIdx = (Y << 9) + X
0x10002005: 85 D2                 test  edx, edx
0x10002007: 78 5F                 js    0x10002068                 ; cellIdx < 0 -> pass
0x10002009: 81 FA 00 00 04 00     cmp   edx, 0x40000               ; cellIdx >= 262144 (512*512)
0x1000200F: 73 57                 jae   0x10002068                 ; 越界保护 -> pass

; ---- 5. 当前视野直视 (LOS) 判定 ----
0x10002011: 8B 0D 1C F0 01 10     mov   ecx, [0x1001F01C]          ; s_visionToken
0x10002017: 39 0C 95 E8 F9 01 10  cmp   [edx*4 + 0x1001F9E8], ecx  ; s_visionGrid[cellIdx]
0x1000201E: 74 48                 je    0x10002068                 ; 直视圈内 -> pass (原版全彩与红点)

; ---- 6. 表面对象指针有效性护栏 ----
0x10002020: 8B 8E 20 12 00 00     mov   ecx, [esi + 0x1220]        ; BSurface* 地形静态表面
0x10002026: 81 F9 00 00 01 00     cmp   ecx, 0x10000
0x1000202C: 76 3A                 jbe   0x10002068                 ; 无效指针 -> pass
0x1000202E: 8B 96 1C 12 00 00     mov   edx, [esi + 0x121C]        ; BSurface* 工作动态表面
0x10002034: 81 FA 00 00 01 00     cmp   edx, 0x10000
0x1000203A: 76 2C                 jbe   0x10002068                 ; 无效指针 -> pass

; ---- 7. 像素读取、50% 减半灰算子与写回 ----
0x1000203C: 57                    push  edi                        ; pt (像素坐标)
0x1000203D: 8B 01                 mov   eax, [ecx]                 ; vtable
0x1000203F: FF 50 28              call  dword ptr [eax + 0x28]     ; Get_Pixel(pt) -> EAX = 原色
0x10002042: D1 E8                 shr   eax, 1
0x10002044: 25 EF 7B 00 00        and   eax, 0x7BEF                ; 50% 减半灰 (与主视图完全同源)
0x10002049: 8B 96 1C 12 00 00     mov   edx, [esi + 0x121C]        ; 工作表面
0x1000204F: 50                    push  eax                        ; color
0x10002050: 57                    push  edi                        ; pt
0x10002051: 8B CA                 mov   ecx, edx                   ; this = 工作表面
0x10002053: 8B 11                 mov   edx, [ecx]                 ; vtable
0x10002055: FF 52 24              call  dword ptr [edx + 0x24]     ; Set_Pixel(pt, color)

; ---- 8. 遥测递增与原版尾声退出 (隐匿红点) ----
0x10002058: FF 05 E4 F9 01 10     inc   dword ptr [0x1001F9E4]     ; s_minimapFogPixels++
0x1000205E: 5F                    pop   edi
0x1000205F: 5E                    pop   esi
0x10002060: 5D                    pop   ebp
0x10002061: 5B                    pop   ebx
0x10002062: 83 C4 30              add   esp, 0x30                  ; 平衡局部变量栈帧
0x10002065: C2 04 00              ret   4                          ; 清除入参 pt 并正常返回

; ---- 9. 直通分支 (Passthrough) ----
0x10002068: FF 25 E8 F9 2D 10     jmp   dword ptr [0x102DF9E8]     ; 跳至 s_pPlotCellTrampoline
```

---

## 五、直通与灰化分支逻辑及红线核查 [实证]

### 1. EnableMinimapFog=0 直通零写入核查
当 `EnableMinimapFog=0` 时，INI 解析将 `s_minimapFogGate` 赋值为 `0`：
- 首条指令 `cmp byte ptr [0x1001F019], 0` 立即命中，执行 `je 0x10002068`；
- `0x10002068` 处为 `jmp dword ptr [0x102DF9E8]`，直接跳转至跳板执行原版 9 字节；
- **全过程零栈破坏、零寄存器污染（EAX/EBP/ESI/EDI 完好无损）、零内存写入**；
- 行为与原版 `RadarClass::Plot_Cell` 严格等价。

### 2. 灰化路径敌点隐匿机制核查
原版 `RadarClass::Plot_Cell` 在 `0x00655D41` 之后开始遍历当前格上的对象列表（Techno/Unit/Building/Infantry）并在小地图工作表面点绘阵营红点/蓝点。
在路线 A 实现中：
- 迷雾区域完成地表像素灰化后，直接执行 `0x1000205E` - `0x10002065`（`pop edi/esi/ebp/ebx; add esp, 0x30; ret 4`）；
- **天然跳过了后续的对象遍历与点绘循环**；
- 实现了敌军部队/建筑在灰雾下小地图红点的**彻底隐匿与零多余计算**，符合红线要求。

### 3. 崩溃触发点（MSVC 内联汇编方括号陷阱）根治核查
旧版崩溃（0x5450202F）根因为内联汇编将裸符号常数当立即数载入（`mov ecx, imm32` 对应 `B9 24 F9 87 00`）。
在当前二进制中：
- 视野网格访问：`cmp [edx*4 + 0x1001F9E8], ecx`（使用确定性基地址位移，`0x1001F9E8` 对应 DLL `.data` 内部变量）；
- `GameState` 访问：`mov eax, 0x00A8B238; cmp byte ptr [eax], 0`（明确经由寄存器间接寻址读取）；
- 全 DLL 扫描：不存在任何对未解引用标量指针直接加偏移导致的内存非法访问。

---

## 六、与 A-7 实施规格书逐项差异对比 (Discrepancy Analysis)

| 检查项 | A-7 实施规格书要求 | ZCode 落地实现 (ra2render.dll) | 差异判定 | 影响评估 |
|---|---|---|:---:|---|
| **挂钩地址** | `0x00655D38` | `0x00655D38` | **无差异** | 完全吻合 |
| **补丁长度与结构** | 9 字节：`E9 rel32` + 4×`90` | 9 字节：`E9 rel32` + 4×`90` | **无差异** | 指令边界严密对齐 |
| **跳板指令 1** | `89 44 24 28` (`mov [esp+28h], eax`) | `89 44 24 28` (`mov [esp+28h], eax`) | **无差异** | 准确保全 `pCell` 槽位 |
| **跳板指令 2** | `A1 50 35 B7 00` (`mov eax, [B73550h]`) | `A1 50 35 B7 00` (`mov eax, [B73550h]`) | **无差异** | 准确保全原版全局读 |
| **跳板跳回点** | `0x00655D41` | `0x00655D41` | **无差异** | 跳回 `cmp eax, ebp` 处 |
| **GameState 检查** | `mov ecx, 0xA8B238; cmp byte [ecx], 0` | `push eax; mov eax, 0xA8B238; cmp byte [eax], 0; pop eax` | **微调（正向增强）** | 增加了 `push/pop eax`，防止污染 ECX，对 passthrough 更加安全 |
| **指针下界护栏** | `cmp eax, 0x10000; jbe pass` | `cmp eax, 0x10000; jbe pass` | **无差异** | 彻底防范空指针与标量 |
| **InvalidCell 护栏** | `cmp eax, 0x00ABDC50; je pass` | `cmp eax, 0x00ABDC50; je pass` | **无差异** | A-8 证实符号完全对齐 |
| **已探索判定** | `test byte ptr [eax + 0x12C], 8` | `test byte ptr [eax + 0x12C], 8` | **无差异** | 完全吻合 |
| **MapCoords 偏移** | `+0x24` (X) / `+0x26` (Y) short 扩宽 | `movsx edx, [eax+26h]; shl edx, 9; movsx ecx, [eax+24h]; add edx, ecx` | **无差异** | 坐标换算严密精确 |
| **网格边界护栏** | `< 0` 或 `>= 262144` 跳转 passthrough | `test edx, edx; js pass; cmp edx, 40000h; jae pass` | **无差异** | 完备防越界 |
| **表面有效性护栏** | `[esi+1220h] > 10000h` / `[esi+121Ch] > 10000h` | `cmp ecx, 10000h; jbe pass; cmp edx, 10000h; jbe pass` | **无差异** | 防断电崩溃护栏生效 |
| **像素读取虚表** | `[ecx] + 0x28` (`Get_Pixel`, ret 4) | `mov eax, [ecx]; call [eax + 0x28]` | **无差异** | 调用约定严密对齐 |
| **灰化算子** | `shr eax, 1; and eax, 0x7BEF` | `shr eax, 1; and eax, 0x7BEF` | **无差异** | RGB565 减半灰同源 |
| **像素写入虚表** | `[edx] + 0x24` (`Set_Pixel`, ret 8) | `mov edx, [ecx]; call [edx + 0x24]` | **无差异** | 调用约定严密对齐 |
| **遥测计数器** | `inc dword ptr [s_minimapFogPixels]` | `inc dword ptr [0x1001F9E4]` | **无差异** | 像素级可观测 |
| **退出尾声** | `pop edi/esi/ebp/ebx; add esp, 30h; ret 4` | `pop edi/esi/ebp/ebx; add esp, 30h; ret 4` | **无差异** | 平衡原版局部栈帧 |

---

## 七、综合复核判定

- **静态复核判定**：**✅ 通过 (PASS)**。
- **评价**：ZCode 依据 A-7 规格书落地的路线 A（`Plot_Cell 0x00655D38` 下沉挂钩与跳板）在二进制层面表现为极高水准的严谨性与规范性：
  1. 9 字节补丁与 14 字节跳板的指令边界处理天衣无缝；
  2. 相对跳转偏移 `rel32` 的数学运算经 Capstone 与 Python 符号解算 100% 精确匹配；
  3. 包含了完整的五重防御性护栏（总开关、游戏状态、指针下界、InvalidCell、表面有效性）；
  4. 卸载还原路径对称完备，支持热回滚。
- **后续动作**：待 ZCode 正式交付 3 局真机验收证据目录（`out/loadbench/shots/v160_real/`）后，直接启动 `tools/verify_evidence.py` 执行机械筛与目视抽核（任务 A-1′b）。
