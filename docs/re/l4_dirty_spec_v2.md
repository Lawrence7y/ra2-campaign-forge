# L4「视口全量刷 → 视野脏区折中」落地规格（静态取证与精确改动点清单）

[META]
task=L4-DIRTY-SPEC  executor=Antigravity(agy)  mode=read-only  conversation_id=6ee8e18f-71f5-4394-b8dd-66cff21902f6
baseline=ra2youli\gamemd.exe (MD5: 4f37486e5b0dbe2ae5f45aeee0f98367)  ra2render.dll (148,992 B / EAAA1BE9)
verification=tools/verify_anchors.py (323/323 PASS) + tools/audit_bytes.py (29/29 OK 100%)

---

## [0] 结论摘要
1. **重绘/脏区构造点 (E1)**：在 TacticalClass::Render（0x6D3D10..0x6D4B4B）内枚举出 12 处核心写入点，涵盖滚屏双脏条、VisibleCells 帧末清零及脏矩形表压缩。
2. **0x6D3D99 jge 语义 (E2)**：比较量严格为 `abs(ΔX) >= ViewportWidth` 与 `abs(ΔY) >= ViewportHeight`，纯属滚屏跨屏判据，**绝非**内容脏区判据。原版在静止视角下直接绕开全量重绘。
3. **迷雾迁移格判据 (E3)**：引擎侧无跨帧迁移标记（0x6DA7D0 仅填临时数组，0x12C 为常态位）。DLL 侧 `blitter_hooks.cpp:1483` **已原生具备** `cur != s_prevVisionGrid[i]` 逐格扫描。最小侵入方案仅需在该循环统计视口内迁移数 `s_fogViewportTransitionCount`。
4. **落地规格与相容性 (E4)**：在 `blitter_hooks.cpp` 桩函数内增设 `L4DirtyMode` 门控。视野迁移在 Render 前计算，单位移出当帧即触发迁移计数，当帧立即走 `jmp 0x006D3E37`，与「静止视角迷雾零延迟退回」100% 严格相容。
5. **对象二遍裁剪来源 (E5)**：判定为**「是」**。0x6D3870 构造 60×30 包围盒或脏矩形传给 0x6D9920，直接作为 `clip_rect` 传给 `ObjectClass::Draw`，底层 Blitter 执行像素裁剪，确认存在对象局部绘制。

---

## [1] 必答项结论总表 (E1 ~ E5)

| 项 | 核心问题 | 结论 | 证据等级 | 决定性证据 VA / 符号 |
|---|---|---|---|---|
| **E1** | Render 内 dirty / 重绘构造点 | 枚举 12 处关键写点（见 [3]） | [实证] | 0x6D3DB4, 0x6D3E37, 0x6D3EFB, 0x6D4378, 0x6D451C, 0x6D4571 |
| **E2** | 0x6D3D99 jge 比较量与原版语义 | 比较量为 `abs(ΔPixelX)` 与 `Width`；纯滚屏阈值 | [实证] | 0x6D3D8A(`mov eax,ebx`) → 0x6D3D97(`cmp eax,edx`) → 0x6D3D99(`jge`) |
| **E3** | 迷雾状态迁移格可观测判据 | 引擎无专用标志；DLL 既有循环自建统计 | [实证] | 0x6DA7D0 临时表; DLL `s_visionGrid` vs `s_prevVisionGrid` (L1483) |
| **E4** | 视野脏区折中落地规格 | 视口迁移门控 `L4DirtyMode`，零延迟相容 | [设计] | 挂载 0x6D3D99，视口有迁移走 0x6D3E37，无迁移走原版分支 |
| **E5** | 对象二遍是否可能只画局部 | **是**（裁剪矩形来自 60×30 单格或脏区） | [实证] | 0x6D394A(0x3C/0x1E) → 0x6D99F2(esp+0x4C) → 0x6D9A21(Draw) |

---

## [2] 关键证据链与字节断言 (audit_bytes 29/29 OK)
- 断言账本：`out/re_work/agy_l4dirty/claims.txt`（29 条 VA / 字节完全覆盖 E1~E5 全链路）。
- 自动化审计：`python tools/audit_bytes.py out/re_work/agy_l4dirty/claims.txt` 判定全部 OK（0 错 0 漏）。
- 镜像回归：`python tools/verify_anchors.py` 达成 323/323 100% 全绿，基线 .text 哈希严格一致。

---

## [3] TacticalClass::Render (0x6D3D10..0x6D4B4B) 脏区/重绘构造点清单 (E1)

| 序号 | VA | 原字节 (gamemd.exe) | 汇编指令 | 语义与打脏作用 |
|---|---|---|---|---|
| 1 | 0x006D3DB4 | C6 05 3C E6 B0 00 00 | mov byte ptr [0xb0e63c], 0 | 清除全局静止全刷标记 |
| 2 | 0x006D3DC6 | 33 DB 89 5C 24 18 89 5C 24 14 | xor ebx,ebx; mov [esp+18],ebx; mov [esp+14],ebx | 全刷触发时清空滚动增量 ΔX/ΔY |
| 3 | 0x006D3E37 | C6 84 24 0C 01 00 00 01 | mov byte ptr [esp + 0x10c], 1 | **全量重绘主入口**：置位栈局部 full_redraw=1 |
| 4 | 0x006D3E3F | C6 05 3C E6 B0 00 01 | mov byte ptr [0xb0e63c], 1 | 置位全局 static_redraw 并跳 0x6D3DC6 |
| 5 | 0x006D3EFB | 89 84 24 C4 00 00 00 | mov dword ptr [esp + 0xc4], eax | 构造滚屏暴露脏矩形 Rect 1.X（及其后 Y/W/H） |
| 6 | 0x006D3F2F | 89 94 24 D4 00 00 00 | mov dword ptr [esp + 0xd4], edx | 构造滚屏暴露脏矩形 Rect 2.X（及其后 Y/W/H） |
| 7 | 0x006D40D3 | 89 02 89 4A 04 89 42 08 89 4A 0C | mov [edx..+0xC], reg | 构造扩展视口矩形 (X-64,Y-64,W+128,H+128) 调 0x6D9A50 |
| 8 | 0x006D4378 | 33 C0 89 44 24 24..40 | xor eax,eax; mov [esp+0x24..40], 0 | 初始化双脏条矩形数组并按滚屏方向写入有效边界 |
| 9 | 0x006D451C | 89 0D 88 CE B0 00 | mov dword ptr [0xb0ce88], ecx | 扣减并压缩脏矩形表 `0xb0ce7c`（配合 0x6D453A rep movsd） |
| 10 | 0x006D4571 | C7 85 E0 00 00 00 00 00 00 00 | mov dword ptr [ebp + 0xe0], 0 | **帧末清零 VisibleCells 计数**（`TacticalClass+0xE0`） |
| 11 | 0x006D458E | 89 85 B8 00 00 00 89 8D BC 00 00 00 | mov [ebp+B8],eax; mov [ebp+BC],ecx | 将当前视口像素同步为上一帧位置（终止滚屏差） |
| 12 | 0x006D4B30 | C6 85 7C 0D 00 00 00 C6 85 7D 0D 00 00 00 | mov byte ptr [ebp+D7C/D7D], 0 | 帧末清空 TacticalClass 失效/脏标记 |

---

## [4] 0x6D3D99 jge 比较量与原版控制流语义审计 (E2)
1. **操作数寻址还原**：
   - 0x6D3D55: `ebx = [ebp+0xB8] - [ebp+0xB0]` = `CurrentPixelX - LastPixelX`（水平滚动位移）。
   - 0x6D3D8A..0x6D3D8F: `eax = abs(ebx)`。
   - 0x6D3D91: `edx = [0x886fa8]`（`TacticalRect.Width`，视口宽度）。
   - 0x6D3D97: `cmp eax, edx`；0x6D3D99: `jge 0x6d3e37`（越屏则全刷）。
   - 垂直方向（0x6D3DA6..0x6D3DAE）对 `abs(ΔY)` 与 `TacticalRect.Height` 执行完全相同的判定。
2. **语义定谳**：
   - 该 `jge` 纯粹处理「镜头滚屏是否超过一屏」，超过则底图无法平移 blit 复用，必须全量重绘。
   - 原版在静止视角（`ΔX=0, ΔY=0`）下，绝不会走 0x6D3D99 全刷；若无单位/动画/脏区（0x6D3E95 `je 0x6D4758`），甚至直接跳过瓦片地形层。
   - v1.5.0 将其强改为 `jmp 0x6D3E37`，本质是用「每帧强制视口全重绘」粗暴掩盖了 DLL 迷雾系统未打脏的问题。

---

## [5] 迷雾状态迁移格可观测判据与最小侵入方案 (E3)
1. **引擎侧现状**：
   - `0x006DA7D0 RegisterCellAsVisible`：原版通过此处将变动格推入 `TacticalClass+0xE4`，但在 DLL 渲染管线下为 0 命中。
   - `CellClass+0x12C`：仅维护可见性状态（bit 3），不包含「本帧是否刚刚发生迁移」的时钟沿状态。
   - `TacticalClass+0xE0`（VisibleCellsCount）：在 0x6D4571 被帧末硬清零，且容量上限仅 0x31F（799 格），易溢出。
2. **DLL 最小侵入方案**：
   - `ra2render/blitter_hooks.cpp`（L1482-1491）在每帧视线扫描后，已存在完整的逐格扫描：
     `cur = (s_visionGrid[i] == s_visionToken) ? 1 : 0; if (cur != s_prevVisionGrid[i]) ...`
   - **自建方案**：无需修改引擎结构，在该现有循环内增加视口包围盒裁剪：
     若 `cur != s_prevVisionGrid[i]` 且 cellX/cellY 落在当前战术视口内，则递增 `s_fogViewportTransitionCount`。
   - 若渐变启用（`g_fadeFogTransition`），则同时统计 `s_fogRampFrame[i] > 0` 落在视口内的数量。

---

## [6] L4「视口全量刷 → 视野脏区折中」落地规格 (E4)

### 改动点清单表

| 目标文件 / VA | 原基线内容 | 拟替换规格（模式/伪码） | 作用与控制流 |
|---|---|---|---|
| `ra2render/blitter_hooks.cpp` (Hook_L4FullRedraw_Stub) | `mov ecx, 0x6D3E37; jmp ecx` | 注入 `ShouldForceTacticalRedraw()` 判定 | 运行时门控全刷分支 |
| `gamemd.exe:0x006D3D99` (6 字节) | `0F 8D 98 00 00 00` (原) / `E9 rel32 90` (现) | 保持 6 字节 `jmp Hook_L4FullRedraw_Stub + nop` | 劫持战术刷新决定点 |
| `ra2render.ini` | [Renderer] 无该字段 | 新增 `L4DirtyMode=1`（0=全刷基线, 1=视口迷雾脏区门控, 2=格级注入） | 生产环境开关与降级通道 |

### 核心桩伪代码
```cpp
bool ShouldForceTacticalRedraw() {
    if (g_L4DirtyMode == 0) return true; // Baseline: v1.5.0 全量刷
    if (s_fogViewportTransitionCount > 0 || s_fogViewportRampActive > 0) return true; // 视口内迷雾有变动/渐变中
    return false; // 视口内迷雾稳定
}

__declspec(naked) void Hook_L4FullRedraw_Stub() {
    __asm {
        pushfd
        pushad
        call ShouldForceTacticalRedraw
        test al, al
        popad
        popfd
        jnz  _force_full_redraw
        // 未命中迷雾脏区：恢复原始 jge 逻辑（检查滚动量）
        jge  _force_full_redraw
        mov  ecx, 0x006D3D9F
        jmp  ecx
    _force_full_redraw:
        mov  ecx, 0x006D3E37
        jmp  ecx
    }
}
```

---

## [7] 与「静止视角迷雾零延迟退回」硬约束的相容性论证 (E4)
1. **时序无死角**：
   - 引擎每帧执行序列：`游戏逻辑更新 → 视线范围计算 (s_visionGrid) → TacticalClass::Render (0x6D3D10)`。
   - 迷雾状态由 DLL 在 Render 之前完成计算并写入 `s_visionGrid`。
2. **零延迟判定**：
   - 无论单位以何种速度移出视线，当它离开格子的瞬间，`s_visionGrid[cellIdx]` 在当帧立即脱落为非当前 token。
   - 当帧视野扫描循环立刻发现 `cur != s_prevVisionGrid[cellIdx]`，`s_fogViewportTransitionCount` 在当帧 Render 前递增。
   - 当帧执行到 0x6D3D99 时，`ShouldForceTacticalRedraw()` 必返回 `true`，控制流 100% 跳转 0x6D3E37 触发全量重绘。
   - **延迟严格为 0 帧**，退回表现与 v1.5.0 逐像素全量刷完全一致。
3. **收益区间**：
   - 当画面静止且视口内无单位视野变化时，`s_fogViewportTransitionCount == 0`，跳过全量重绘，消除静止视角的冗余 Blit 开销。

---

## [8] 对象二遍裁剪矩形来源与局部绘制判定 (E5)
1. **裁定结论**：**「是」**（对象二遍完全具备只画对象局部的底层机制）。
2. **取证链路**：
   - `0x006D3870` 第一段（VisibleCells 遍历，0x6D388F..0x6D3982）：
     0x6D394A / 0x6D394F 显式向栈构造宽 60 (0x3C)、高 30 (0x1E) 的单元格菱形像元包围盒 `[esp+0x4C]`。
     0x6D3969 调用 `0x6D9920(..., clip_rect=[esp+0x4C])`。
   - `0x006D3870` 第二段（DirtyRects 遍历，0x6D3988..0x6D3A47）：
     0x6D39EB 调用 0x421B60 截取脏区与战术视口交集，0x6D3A3E 调用 `0x6D9920(..., clip_rect=dirty_rect)`。
   - `0x006D9920` 内部（0x6D99F2..0x6D9A21）：
     0x6D99F2 从参数取出 `clip_rect` 拷至 `[esp+0x24]`，并在 0x6D9A1E 压入该矩形指针，直接调用 `ObjectClass::Draw(clip_rect, ...)`（虚表 +0x104）。
3. **DEF-FOGPARTIAL 服务判定**：
   - 底层 Blitter 严格按传入的 `clip_rect` 裁剪像素。若大尺寸对象仅有单格被标记为脏格，对象二遍仅重绘位于该 60×30 矩形内部的局部切片。

---

## [9] 门控裁决、遥测字段与回滚预案
1. **门控充分性裁决**：
   - 裁定：**「视口内迁移计数门控完全充分」**。由于迷雾渐变过渡在 `blitter_hooks.cpp` 包含 4 帧 ramp，门控必须同时检查 `s_fogViewportTransitionCount > 0 || s_fogViewportRampActive > 0`，以杜绝渐变中途因无新迁移而骤停全刷。
2. **遥测字段（Telemetry）**：
   - `l4_redraw_forced_fog`：因迷雾视口脏区触发全刷的帧数。
   - `l4_redraw_skipped_static`：因静止且无迷雾变动成功跳过全刷的帧数。
   - `l4_fog_transition_cells`：当帧视口内变动格子数。
3. **回滚预案**：
   - 若线上发现边缘残影或异常闪烁，将 `ra2render.ini` 中 `L4DirtyMode=0`，瞬间切回 v1.5.0 绝对无条件全量刷新，0 代码回滚成本。
