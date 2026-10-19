# L4 脏矩形 / 视口刷新机制逆向与折中方案

> 目标：在 `gamemd.exe`（1.001，ImageBase `0x400000`，`.text` raw offset = RVA）中逆向
> `TacticalClass::Render` 的 dirty rect / 视口刷新机制，解释现有 L4 补丁
> （`0x006D3D99` jge→jmp）为何有效、代价是什么，并给出「只重绘变化格」的折中方案。
>
> 本文为纯逆向产出，不修改总档案、源码、dll。所有地址均为 VA（`0x00XXXXXX`）。
> 现有 L4 原理见 `REVERSE_ENGINEERING_AND_PATCHES.md` §五（只读）；路线背景见
> `docs/NEXT_RE_AND_MODERNIZATION.md` P0-2。

---

## 0. 结论摘要（TL;DR）

| 问题 | 答案 |
|---|---|
| 原版 `jge 0x6D3E37` 在判断什么？ | **视口滚动位移是否 ≥ 视口宽/高**（无重叠才全量）。`eax=abs(当前原点X-上次原点X)`，`edx=ViewBounds.Width` |
| 全量路径 `0x6D3E37` 做什么？ | 置 `bForceRedraw=1` + 全局 `0xB0E63C=1`，清零滚动 delta，走「填底 + 全视口重绘」 |
| 非全量路径的 dirty 结构在哪？ | 全局向量 `0xB0CE78`，条目 `0x14` 字节 `{X,Y,W,H,bFlag}`，Items=`0xB0CE7C`，Count=`0xB0CE88` |
| 谁打 dirty 标记？ | `RegisterDirtyArea(0x6D2790)` ← `CellClass::MarkForRedraw(0x486E70)` ← 迷雾字段变更回调 `0x4A9973` |
| 迷雾不退回的真正原因？ | L3 自定义迷雾画在 `Hook_CellClass_Draw`（基于 `s_visionGrid`），**不改**引擎 `Shroudedness/Foggedness`，引擎 dirty 系统看不到变化 → 静止时不重绘 |
| `+0x3598` 是什么？ | **不是 CellClass**，是 `ScenarioClass+0x3598`（YRpp `unknown_3598`）字节标志，门控每帧事件/环境队列处理，与脏矩形无直接关系 |
| 推荐折中？ | **方案 A**（视野 token 变化格 `MarkForRedraw`）＞ C（迷雾独立刷）＞ B（跳过静态 tile） |

---

## 1. `TacticalClass::Render`（`0x006D3D10`）完整逻辑

### 1.1 函数位置与调用约定

- **入口**：`0x006D3D10`（序言 `sub esp,0xF4` / `push ebx,ebp,esi,edi` / `mov ebp,ecx`）
- **this**：`TacticalClass::Instance`，全局指针 `0x00887324`
- **调用点**（每帧 3 次，`0x004F44DF` / `0x004F44F4` / `0x004F4515`）：

```text
TacticalClass::Render(Surface* pSurface, int arg2, int drawMode)
; ecx = this
; pSurface = [0x0088731c]（战术视口表面）
; drawMode ∈ {0, 1, 2}，一帧三遍（推测：地形层 / 单位层 / 覆盖物层）
; arg2    = 强制重绘标志（函数内部也会写回）
```

栈布局（序言后）：`[esp+0x108]=pSurface`，`[esp+0x10C]=arg2`，`[esp+0x110]=drawMode`。

### 1.2 关键字段（实测语义，YRpp 命名仅作参考）

| 偏移 | 语义（反汇编证实） | YRpp 对照 |
|---|---|---|
| `this+0xB0, +0xB4` | **当前**视口原点（TacticalTopLeft） | `VisibleArea` 前半（YRpp 按 RectangleStruct 解读不准确） |
| `this+0xB8, +0xBC` | **上次渲染时**视口原点 | 同上后半，Render 收尾处 `B8:=B0, BC:=B4` 同步 |
| `this+0xD64, +0xD68` | 当前某状态量（与下列对比） | `field_D64/D68` |
| `this+0xD6C, +0xD70` | 上次渲染时的状态量，收尾同步 | `field_D6C/D70` |
| `this+0xD7C` | 需要重绘标志 | `field_D7C` |
| `this+0xD7D` | 重绘中/脏标志 | `Redrawing`（YRpp 注释 cheap mutex） |
| `this+0xE0` | 可见格子数 | `VisibleCellCount` |
| `this+0xE4` | 可见格子指针数组 `[800]` | `VisibleCells[800]` |
| `this+0xDB0` | 计数器，Render 入口清零 | `field_DB0` 附近 |

全局：

| 地址 | 语义 |
|---|---|
| `0x00886FA0` | `Surface::ViewBounds`，战术视口 `{X,Y,Width,Height}`（YRpp `Surface.h`） |
| `0x00B0E63C` | 字节「sticky 全量重绘」标志，仅在 Render 内读写（3 处） |
| `0x00B0CE78` | 脏矩形向量对象（vtable `0x007F429C`，构造于 `0x6D1A60`） |
| `0x00B0CE28..0x00B0CE34` | 滚动 blit 累积矩形（`0x6D1A40` 清零） |
| `0x00A8ED84` | `CurrentFrame`（本项目 `ADDR_CURRENT_FRAME`） |

### 1.3 伪代码（Render 决策段 `0x6D3D10`–`0x6D3E9B`）

```text
Render(pSurface, arg2, drawMode):
  this+0xDB0 = 0
  localView = *(Rect*)0x886FA0          // ViewBounds 快照
  cl = this->fn_6D9B50(localView)       // 建筑是否需要绘制（遍历 Buildings 数组）
  dx = this+0xB8 - this+0xB0            // 上次原点 - 当前原点 = -scrollDX
  dy = this+0xBC - this+0xB4            // 同理 -scrollDY

  if drawMode != 0:                        // 0x6D3D84 jne 0x6D3E4B：跳过滚动阈值判定
      if 0xB0E63C != 0: arg2 = 1; dx=dy=0  // 上帧强制过 → 本帧继续强制
      // 落到公共路径 0x6D3DBB
  else:
      // ---- drawMode==0：视口位移阈值判定（原版 jge 所在）----
      if abs(dx) >= ViewBounds.Width:  goto 全量_6D3E37     // 0x6D3D97: cmp eax,edx / jge
      if abs(dy) >= ViewBounds.Height: goto 全量_6D3E37     // 0x6D3DAC: cmp eax,edx / jge
      0xB0E63C = 0

  // ---- 公共路径 0x6D3DBB ----
  if arg2 != 0: dx=dy=0                    // 强制重绘时不滚动 blit
  if drawMode == 2: goto 分模式收尾_6D4758   // 跳过主视口绘制
  if arg2 != 0: goto 进绘制

  // ---- 判脏（非全量）----
  if this+0xD7C and cl:      goto 进绘制
  if cl:                     goto 进绘制   // 建筑需要画
  if 脏矩形Count(0xB0CE88)!=0: goto 判脏2
  if this+0xD7D:             goto 进绘制
  if this+0xD64 != this+0xD6C: goto 判脏2
  if this+0xD68 == this+0xD70: goto 分模式收尾   // 主视口无事可做
  else: goto 判脏2

  判脏2:                                  // 0x6D3E69
    if this+0xD7D: goto 进绘制
    if 脏矩形Count != 0: goto 进绘制
    if this+0xB0==this+0xB8 and this+0xB4==this+0xBC: goto 分模式收尾
    // 视口原点变了 → 进绘制（滚动 blit 路径）

  全量_6D3E37:                            // ★ L4 补丁跳到这里
    arg2 = 1
    0xB0E63C = 1
    dx = dy = 0
    if drawMode == 2: goto 分模式收尾
    goto 进绘制

  进绘制_6D3E9B: ...                       // 填底 / 滚动 blit / fn_6D3870
  分模式收尾_6D4758:                       // 不是 ret！跳 0x6D4582
      同步 D64→D6C、D68→D70、B0→B8、B4→BC
      if drawMode==1 or ==3: 表面 blit（call [vtable+8], ViewBounds）
      if drawMode==2 or ==3: call 0x6D9CE0(ViewBounds)
                             + 0x6D6D60 / 0x6DA9D0 / 0x6D5030 / 0x53D850
                             + 0x6D8DB0 / 0x5FFFA0 / 0x550240 / 0x4C2830 / 0x556D40
      return
```

### 1.4 全量路径 `0x006D3E37` 之后做了什么

```asm
006D3E37: mov byte ptr [esp+0x10c], 1     ; arg2 = 1  (bForceRedraw)
006D3E3F: mov byte ptr [0xB0E63C], 1      ; sticky 全量标志
006D3E46: jmp 0x6D3DC6                    ; → xor ebx,ebx / 清零 dx,dy
006D3DD0: cmp edi, 2                      ; drawMode==2 跳过主视口绘制
006D3DD3: je  0x6D4758                    ; → 0x6D4582 分模式收尾
006D3DD9: mov al, [esp+0x10c]             ; al=1
006D3DE2: jne 0x6D3E9B                    ; → 进绘制
```

`进绘制（0x6D3E9B）`在 **dx==0 && dy==0 && arg2==1** 时走「整屏填充 + 全视口重绘」：

```asm
006D3F6C: test al,al              ; arg2
006D3F75: je   0x6D407E           ; 非强制 → 只画脏区
006D3F82: test eax,eax            ; drawMode
006D3F86: je   0x6D3F8F
006D3F89: cmp  eax,3
006D3F8D: jne  0x6D407E
006D3F8F: mov  ecx,[0x887644]     ; 表面
006D3F95: push 0xFFFF
006D3F9A: call 0x7BCF50           ; 填充 ViewBounds
006D3F9F: mov  ecx,[0x87E8A4]
006D3FA7: push 0x7F
006D3FA7: call 0x4112D0           ; 填充/清屏
```

随后调用 **`TacticalClass::fn_6D9920`**（区域重绘原语，内部先 `Drawing::Intersect(0x421B60)` 裁剪再画）。
非全量时该原语**只对脏矩形条目**调用；全量时对整个 `ViewBounds` 调用。

### 1.5 绘制收尾与脏列表清空

`0x6D457B`（绘制完成后）：

```asm
mov ecx,[ebp+0xD64] ; mov [ebp+0xD6C],ecx    ; 状态量同步
mov edx,[ebp+0xD68] ; mov [ebp+0xD70],edx
mov eax,[ebp+0xB0]  ; mov [ebp+0xB8],eax     ; 当前原点 → 上次原点
mov ecx,[ebp+0xB4]  ; mov [ebp+0xBC],ecx
```

`0x6D44FC`（Render 尾部，调用 `fn_6D3870` 画完之后）：**把脏矩形向量逐条弹空**
（`Count--` + `rep movsd` 紧凑搬移，与 `0x6DA980` 同一套清空逻辑）。

`fn_6D3870`（`0x6D3870`，Render 内 `call 0x6D44F7`）职责：

1. 遍历 `VisibleCells[0 .. VisibleCellCount)`，屏幕坐标外扩 `±0x1E`（30px）后 `fn_6D9920` 绘制；
2. 再倒序遍历脏矩形列表，`Drawing::Intersect` 裁到 `ViewBounds`，非空则 `fn_6D9920`；
3. 若某标志置位则补画整个 `ViewBounds`。

---

## 2. 脏矩形数据结构与「打 Dirty 标记」写入点

### 2.1 全局脏矩形向量（CRT 静态初始化 `0x6D1A60`）

```text
对象 0x00B0CE78:
  +0x00  vtable        = 0x007F429C
  +0x04  Items         = 0x00B0CE7C   // DirtyRectEntry*
  +0x08  Capacity      = 0x00B0CE80
  +0x0C  flags(byte×2) = 0x00B0CE84/85
  +0x10  Count         = 0x00B0CE88
  +0x14  CapIncrement  = 0x00B0CE8C   // = 10，满则 realloc
```

**条目结构 `DirtyRectEntry`（0x14 = 20 字节）**：

```c
struct DirtyRectEntry {   // 坐标为 ViewBounds 本地坐标（世界/屏幕坐标 - ViewBounds.X/Y）
    int  X, Y, Width, Height;  // +0x00 .. +0x0C
    bool bFlag;                // +0x10  RegisterDirtyArea 的 bUnk，参与合并去重
    char pad[3];
};
```

证据：删除/搬移时 `mov ecx,5 / rep movsd`（5 dword=20B）；追加时 `lea eax,[eax+eax*4] / lea edi,[ecx+eax*4]`（×20）。

### 2.2 `TacticalClass::RegisterDirtyArea`（`0x006D2790`）—— 主写入点

签名：`RegisterDirtyArea(RectangleStruct Area, bool bUnk)`，`ret 0x14`（20 字节参数：4 int + 1 bool 按栈传）。

行为：

1. 遍历现有脏矩形（Items=`0xB0CE7C`，Count=`0xB0CE88`），对每条做矩形求交/包围盒合并尝试（`sub_487F40` 做并集，`0x421B60` 做交集）；
2. 若找到**完全相同**的条目且 `bFlag` 一致 → 去重跳过；
3. 若找到**面积增量最小**的可合并条目 → 原地替换成并集（`call 0x487F40` 后 `rep movsd` 写回）；
4. 若无处合并：
   - `Count < Capacity` → 直接 `rep movsd` 追加（`0x6D2A94`）；
   - 否则 `call [vtable+8]` 扩容（`0x6D2A6B`–`0x6D2A89`）再追加。

调用者：全 exe **58 处**（`call 0x6D2790`），覆盖地形破坏、建筑、动画、overlay 等；其中 **`0x486FD1` 位于 `MarkForRedraw` 尾部**——cell 脏标记最终汇入这里。

### 2.3 `CellClass::MarkForRedraw`（`0x00486E70`）—— cell 级打脏

```text
MarkForRedraw():
  rectA = sub_47FF80(this)           // 由 MapCoords(+0x24/+0x26) 算格子屏幕包围盒
  rectB = this->GetContainingRect()  // 0x47FB90，含容器对象（建筑等）的包围盒
  merge = Intersect/Union(rectA, rectB)
  merge.X -= ViewBounds.X            // 0x886FA0
  merge.Y -= ViewBounds.Y            // 0x886FA4
  TacticalClass::Instance->RegisterDirtyArea(merge, false)   // 0x486FD1
  call 0x6551C0(0x87F7E8 + 0x24)     // 旁路通知（雷达/侧栏？）
```

调用者仅 5 处：`0x43F58E`、`0x43F984`（BuildingClass）、`0x442023`、`0x48A2E9`、`0x6B60FB`。

### 2.4 `TacticalClass::RegisterCellAsVisible`（`0x006DA7D0`）—— 可见格登记

```text
if (0x87F7F4 != 0) return;                       // 某全局开关
if (cell+0x5C == CurrentFrame(0xA8ED84)) return; // 本帧已登记
if (!(cell.CopyFlags & 0x08) && !cell.VisibilityChanged) return;
                                                 // 未探索 且 可见性没变 → 不登记
cell+0x5C = CurrentFrame;
// 算格子坐标 → 加入 this->VisibleCells[]，并隐式产生脏区
```

调用者 25 处，密集区在 `0x4A9xxx`（DisplayClass 绘制/可见性）与 `0x567/0x578`（雷达侧栏）。

### 2.5 迷雾 / 黑雾相关字段与写入点

| 字段 | 偏移 | 语义 | 关键写入点 |
|---|---|---|---|
| `Shroudedness` | `+0x120` | `-2` 全遮 / `-1` 可见 / `0..48` SHROUD.SHP 帧 | `0x480207`（CellClass::Draw 内 `GetOcclusion` 回写）、`0x4A990F`（DisplayClass 重算）、构造 `0x47BD28` |
| `Foggedness` | `+0x121` | 同上，FOG.SHP 帧；`0xFE`=-2 全遮 | `0x4A9947`、`0x480207` 旁、`0x4ACC8D`（`mov [ecx+0x121],0xFE`）、构造 `0x47BD2E` |
| `CopyFlags` | `+0x12C` | bit `0x08`=`cf_Explored`（已探开）；bit `0x10`=当前可见 | `0x4A98EC` `or al,8`、`0x4A9924` `or al,0x10`、构造 `0x47BD3A` |
| `VisibilityChanged` | `+x138` | 可见性本帧是否变化 | `0x47BD4A` 清零、`0x567F3A` 置 1、`0x4A9973` 前读取 |
| `Flags` | `+x140` | `cf_Fogged=0x400000` 等 | `0x4A98E0`、`0x4A995E` |

**迷雾变更 → 打脏 的完整链**（`0x4A98E0`，DisplayClass 单格重算）：

```asm
004A98E6: mov eax,[ebp+0x12C]
004A98EC: or  al,8                      ; CopyFlags |= cf_Explored
004A98FC: call 0x6D8700                 ; TacticalClass::GetOcclusion(cell, fog=0)
004A9902: cmp al,[ebp+0x120]            ; 与 Shroudedness 比较
004A9908: je  skip
004A990A: mov [esp+0xe],1               ; local_changed = 1
004A990F: mov [ebp+0x120],al            ; 写 Shroudedness
004A9935: call 0x6D8700                 ; GetOcclusion(cell, fog=1)
004A993A: cmp al,[ebp+0x121]            ; 与 Foggedness 比较
004A9947: mov [ebp+0x121],al            ; 写 Foggedness
004A9964: mov al,[esp+0xe]
004A996A: je  skip
004A996C: mov ecx,[0x887324]            ; TacticalClass::Instance
004A9972: push ebp                      ; pCell
004A9973: call 0x6DA7D0                 ; RegisterCellAsVisible → 进 VisibleCells + 脏矩形
```

> **要点**：引擎自身的迷雾可见性变化（`GetOcclusion` 结果变）会自动打脏。
> 本项目 L3 自定义迷雾**不写**这两个字段，因此该链路对 L3 视野变化是聋的。

### 2.6 脏矩形消费路径

```text
Render
 └─ fn_6D3870 (0x6D3870)
     ├─ 遍历 VisibleCells → fn_6D9920 外扩 30px 绘制
     ├─ 遍历 DirtyRectEntry[]（倒序）
     │    └─ Drawing::Intersect(entry, ViewBounds)  ; 0x421B60
     │         └─ 非空 → fn_6D9920(clipRect)        ; 0x6D9920
     └─ (可选) fn_6D9920(整个 ViewBounds)
 └─ 0x6D44FC  清空脏矩形向量
```

`fn_6D9920`（`0x6D9920`）是**区域重绘原语**：内部先 `Drawing::Intersect` 裁剪，再按矩形画格子/单位/覆盖物。它是「按矩形重画」的唯一收口，也是折中方案 B/C 的天然 hook 点。

---

## 3. 原版 `jge` 条件到底在判断什么

```asm
006D3D55: mov ebx,[ebp+0xB8]      ; ebx = 上次原点X
006D3D5B: mov esi,[ebp+0xB0]      ; esi = 当前原点X
006D3D6E: sub ebx,esi             ; ebx = lastX - curX = -scrollDX
006D3D70: mov esi,[ebp+0xBC]
006D3D76: sub esi,edx             ; esi = lastY - curY = -scrollDY   (edx=[ebp+0xB4])

006D3D8A: mov eax,ebx
006D3D8C: cdq
006D3D8D: xor eax,edx
006D3D8F: sub eax,edx             ; eax = abs(scrollDX)
006D3D91: mov edx,[0x886FA8]      ; edx = ViewBounds.Width
006D3D97: cmp eax,edx
006D3D99: jge 0x6D3E37            ; ★ 原版：|scrollDX| >= 视口宽 → 全量

006D3D9F: mov eax,esi
006D3DA1: cdq
006D3DA2: xor eax,edx
006D3DA4: sub eax,edx             ; eax = abs(scrollDY)
006D3DA6: mov edx,[0x886FAC]      ; edx = ViewBounds.Height
006D3DAC: cmp eax,edx
006D3DAE: jge 0x6D3E37            ; |scrollDY| >= 视口高 → 全量
```

**语义**：

- `eax` = 视口滚动位移绝对值（像素级）；
- `edx` = 战术视口 `ViewBounds` 的宽（第一次）或高（第二次）；
- `jge`（≥）含义是 **滚动距离超过一整个视口 → 新旧帧无重叠 → 无法靠 scroll-blit 复用，只能全量重绘**。

这比档案 §五「仅在检测到视口位移（滚屏）时跳转」更精确：小幅滚动（< 视口尺寸）原版走**滚动 blit 局部路径**（`0x6D3E9B` 把旧帧按位移拷贝，只画露出的条带），并非「不滚动就不画」。

**L4 补丁把 `jge` 改为无条件 `jmp`**，等价于「永远判定为无重叠」→ 每帧全视口重绘。这是迷雾零延迟退回的充分条件，也是性能回退的来源（约 800 格全刷）。

---

## 4. 折中方案（按推荐度排序）

> 不变式：**静止视角下迷雾退回零延迟**是 v1.5.0 已交付能力，任何折中不得回退它
> （见总档案 v1.5.2 末尾注意事项）。下列方案均保留该不变式。

### 方案 A（推荐）：视野 token 变化格打 dirty + 外扩 1 格

**思路**：L3 的 `UpdateVisionGrid` 已经知道本帧哪些格子视野状态翻转
（`s_visionGrid[i]` 从 `s_visionToken` 变为非 token，或反向）。只对这些格子
调用引擎现成的 `MarkForRedraw`，让 dirty 矩形机制去重绘；然后**恢复原版 jge**。

**改法**（全部落在 `ra2render/blitter_hooks.cpp`，无需新 exe hook）：

```text
UpdateVisionGrid() {
    ...现有盖印逻辑...
    // 新增：对比上一帧快照（或盖印前记录边界格），收集 changed[]:
    //   for cell in changed:
    //     pCell = *(CellClass**)(*(uint8_t**)0x87F924 + (y*512+x)*4)
    //     pCell->MarkForRedraw()          // call 0x486E70，ecx=pCell
    //     // 外扩 1 格：对 8 邻格也 MarkForRedraw（阴影/雾沿/单位脚印）
}
```

| 项 | 内容 |
|---|---|
| 新增 hook | 无需新 hook；在 `UpdateVisionGrid` 内直接 `call 0x486E70` 或写脏向量 |
| 需要的地址 | `MarkForRedraw=0x486E70`；`RegisterDirtyArea=0x6D2790`；地图格指针 `ADDR_MAP_CELLS_ARRAY=0x87F924`；`ViewBounds=0x886FA0`；`TacticalClass::Instance=0x887324` |
| 与 L4 补丁关系 | **替换**：`0x6D3D99` 恢复 `0F 8D 98 00 00 00` 原字节；或 ini 开关 `L4Mode=vision-dirty` 时才恢复 |
| 预期收益 | 静止且视野稳定时几乎零重绘；单位移动时只刷其视距圈翻转的格（典型 30–80 格） |
| 风险 | ① `MarkForRedraw` 要求 `pCell` 有效，需 `IsBadReadPtr` 守护；② 一帧大量翻转（核爆/全图 reveal）时脏矩形合并开销上升，可退化为「翻转数 > 阈值 → 本帧强制全量」；③ 自定义灰雾层依赖 `Hook_CellClass_Draw` 被调用，必须确保 MarkForRedraw 的矩形确实覆盖这些格；④ 与建筑/动画自身打的脏合并时可能产生过大包围盒（已有去重逻辑，可控） |

**验收**：静止视角单位开走 → 灰雾 ≤1 帧退回；U200/U800 回放帧数 +≥2 或 CPU0 −≥5%。

---

### 方案 B：保留全量刷，但跳过「未变化且无单位」的 tile 层

**思路**：不改 `0x6D3D99`（保持 L4 全量），在 `CellClass::Draw`（`0x4801F0`，已有 trampoline hook）或 `fn_6D9920`（`0x6D9920`）里做**格级早退**：

```text
Hook_CellClass_Draw(pCell, ...):
    if (!cellHasObjects && visionTokenUnchanged && !engineDirty)
        return;                      // 跳过地形/雾绘制
    origDraw(...);                   // 否则走原版 + 自定义雾
```

| 项 | 内容 |
|---|---|
| 新增 hook | 不需要（复用 `Hook_CellClass_Draw`）；或额外拦 `fn_6D9920` 做矩形级跳过 |
| 需要的地址 | `0x4801F0`（已有）、`s_visionGrid`/`s_cellFogDrawnToken`（已有）、`CellClass+0x120/121/12C/138`、`FirstObject@+0xC4` |
| 与 L4 补丁关系 | **共存**（L4 保留，B 是其上的减负） |
| 预期收益 | 中等：仍要遍历 800 格（迭代开销在），但省掉大量 SHP 解码/blit |
| 风险 | ① **视觉正确性最难**：动画地形、水面、闪烁、阴影、单位脚印都可能被误跳过；② `s_cellFogDrawnToken` 单帧防重逻辑与跳过逻辑耦合，易出「雾丢一帧」；③ 全量路径里 `fn_6D9920` 的填充/清屏在跳过时会留下脏底。仅当 A/C 不可行时再考虑 |

---

### 方案 C：迷雾层单独刷，地形层沿用脏矩形

**思路**：把问题拆成两层——地形/单位层用**原版脏矩形**（恢复 jge），迷雾层用**独立的 fog-dirty 列表**（由 `UpdateVisionGrid` 维护），每帧末尾只对 fog 变化格调用原生 `Draw_Fog`（`0x0047F250`，`ADDR_DRAW_FOG`）叠半透明灰雾。

```text
Render 原版收尾后（或 hook fn_6D3870 末尾）:
    for cell in fogChangedThisFrame:
        Draw_Fog(pCell, loc, bounds, 15)   // 与 Hook_CellClass_Draw 步骤 6 相同
```

| 项 | 内容 |
|---|---|
| 新增 hook | 挂 `fn_6D3870` 尾部（`0x6D3A6F` `ret 0xC` 前）或 Render 尾部；也可在 `Hook_CellClass_Draw` 里只画雾不重画地形（需拆层） |
| 需要的地址 | `Draw_Fog=0x47F250`；`fn_6D3870=0x6D3870`；`fn_6D9920=0x6D9920`；混色补丁 `0x47F40F/0x47F4AE`（已有） |
| 与 L4 补丁关系 | **替换**（恢复 jge）；fog 正确性由独立通道保证 |
| 预期收益 | 地形层回到原版脏矩形效率；雾层只刷翻转格，成本接近 A |
| 风险 | ① 图层顺序：雾必须画在地形之上、单位剔除之后，若地形未重画而雾画在旧像素上，半透明混色会叠色误差（本项目 `s_cellFogDrawnToken` 已缓解重复变暗）；② 单位离开时若地形格未脏，只刷雾是对的（雾盖在旧草地上视觉可接受），但若有动画地形（水、矿）会露馅；③ 与 `RegisterCellAsVisible` 的 VisibleCells 列表不同步时，可能雾画了但该格单位层没画。适合作为 A 的补充通道（A 负责地形+雾一起脏，C 负责雾增量） |

---

### 排序与落地建议

| 优先级 | 方案 | 理由 |
|---|---|---|
| 1 | **A** | 直接利用引擎 dirty 设施，改动最小，语义与原版一致，回滚容易（恢复 jge 即可） |
| 2 | **C** | 当 A 的「外扩 1 格」仍偶发漏雾沿时，用 C 的独立雾通道补洞；两者可叠加 |
| 3 | **B** | 仅作为 A/C 上线前的临时减负，或性能仍不达标时的兜底；不建议单独作为终态 |

**推荐实施顺序**：A → 回放测帧 + 迷雾手测 → 若雾沿漏 → 叠加 C → 仍不达标再上 B。
每次只动一项，沿用 U200/U800 三局回放阈值验收。

---

## 5. `+0x3598` 在此机制中的角色

### 5.1 身份更正

反汇编 `0x48D000` 热点（两处读）：

```asm
0048CFFC: mov eax, dword ptr [0xA8B230]     ; ScenarioClass::Instance
0048D001: mov cl,  byte ptr [eax + 0x3598]  ; ★ 读
0048D007: test cl, cl
0048D009: je   0x48D073

0048D0EA: mov eax, dword ptr [0xA8B230]
0048D0EF: mov cl,  byte ptr [eax + 0x3598]  ; ★ 读（第二个消费者 0x48D080）
```

写入点全在 ScenarioClass 方法簇：

| 地址 | 指令 | 上下文 |
|---|---|---|
| `0x6833E2` | `mov [ebp+0x3598], bl`（bl=0） | `ScenarioClass` 构造（YRpp `THISCALL(0x6832C0)`） |
| `0x684675` | `mov [ecx+0x3598], 1` | 开局初始化：同时 `CurrentFrame(0xA8ED84):=0`、`[0xA8E7AC]++` |
| `0x684A71` | `mov [eax+0x3598], bl` | ScenarioClass 其它方法 |
| `0x684BDE` | `mov [eax+0x3598], 0` | 同上 |

YRpp `ScenarioClass.h:224` 标注 `DWORD unknown_3598`，位于 `InitTime`/`Stage` 附近。
**结论：`+0x3598` 是 `ScenarioClass` 的字节标志，不是 CellClass 字段**；总档案 v1.5.1 里「地图格子标志 +0x3598」应理解为「地图/场景对象上的标志」，本轮回读更正为 ScenarioClass。

### 5.2 语义

构造置 0、开局置 1，且被两个**每帧更新函数**读取作门控：

- `0x48CFD0`：`[0xA8B238]==2 || ([0xA8DAB8]&1)` 时，若 `+0x3598!=0`，遍历 `0xA8EA70` 列表（`0x5F1C30` 取项），处理 `type==0x6C` 的项并回调 `0x643C50`；
- `0x48D080`：按游戏状态 `[0xA8B238]∈{1,2,3,4}` 分支后同样遍历 `0xA8EA70`，同样以 `+0x3598` 为门。

语义上等价于 **「场景已进入运行态，允许推进每帧事件/环境效果队列」**（Loading/菜单阶段为 0）。

### 5.3 与 L4 / 脏矩形的关系

- **不是**脏标记位，**不写** `RegisterDirtyArea`，**不参与** `DirtyRectEntry`；
- 它门控的队列处理可能间接产生视觉变化（光效、粒子、环境动画），那些变化若走原版 API（如 `MarkForRedraw`）才会进脏矩形；
- 与 L4 全量刷的「正相关」是**性能采样层面**的：全量刷使视口内更多格子/效果被重绘，`0x48D000` 桶（256B 对齐，含 `0x48CFD0`–`0x48D0EF` 及邻近 Theater/资源查询）采样占比上升，因为每帧被触发的环境效果绘制变多。折中方案 A 落地后，该热点应回落到与「视野变化频率」相当的水平。

**在折中方案中的角色**：可作为「本帧是否有环境效果活动」的旁路信号——若 `+0x3598!=0` 且事件队列非空，可临时放宽折中（本帧强制全量），避免环境特效残影。这是可选增强，不是必需。

---

## 6. 与现有 `0x6D3D99` 补丁的共存 / 替换矩阵

| 方案 | `0x6D3D99` 字节 | `Hook_CellClass_Draw` | `UpdateVisionGrid` | ini 开关建议 |
|---|---|---|---|---|
| 现状 L4 | `E9 99 00 00 00 90`（jmp） | 保留 | 保留 | `L4FullRedraw=1` |
| A | **恢复** `0F 8D 98 00 00 00`（jge） | 保留 | **扩展**：翻转格 `MarkForRedraw` | `L4Mode=vision-dirty` |
| B | 保留 jmp | **扩展**：早退条件 | 不变 | `L4Mode=full-skip-tiles` |
| C | **恢复** jge | 可选拆雾 | **扩展**：维护 fog-dirty | `L4Mode=fog-layer` |
| A+C | 恢复 jge | 保留（作兑底） | 扩展双列表 | `L4Mode=vision-dirty+fog` |

回滚约定：任何新逻辑失败时，ini 切回 `L4FullRedraw=1` 即恢复 v1.5.0 行为（补丁字节由 `s_origTacticalRedrawBytes` 保存，卸载路径已在 `0x6D3D99` 附近实现）。

---

## 7. 附录：地址速查表

### 7.1 Render 与视口

| 地址 | 符号 | 说明 |
|---|---|---|
| `0x006D3D10` | `TacticalClass::Render` | 视口渲染主协调器 |
| `0x006D3D97` | `cmp eax,edx` | 原版 jge 条件比较 |
| `0x006D3D99` | L4 补丁点 | 原 `0F 8D 98 00 00 00` → `E9 99 00 00 00 90` |
| `0x006D3E37` | 全量路径入口 | `arg2=1`、`0xB0E63C=1`、清零 delta |
| `0x006D3E9B` | 进绘制 | 滚动 blit / 填底 / 分层绘制 |
| `0x006D3870` | `fn_DrawVisibleAndDirty` | VisibleCells + 脏矩形消费 |
| `0x006D9920` | `fn_DrawRect` | 区域重绘原语（Intersect 后画） |
| `0x006D9B50` | `fn_BuildingsNeedDraw` | 遍历 Buildings 判是否需画 |
| `0x006D4758` | 分模式收尾跳板 | 跳 `0x6D4582`：同步原点 + 按 drawMode 做表面 blit / 附加绘制 |
| `0x006D8700` | `TacticalClass::GetOcclusion` | 算 Shroudedness/Foggedness |
| `0x00886FA0` | `Surface::ViewBounds` | 战术视口 `{X,Y,W,H}` |
| `0x00887324` | `TacticalClass::Instance` | this |
| `0x00B0E63C` | sticky 全量标志 | 仅 Render 内 3 处访问 |

### 7.2 脏矩形

| 地址 | 符号 | 说明 |
|---|---|---|
| `0x00B0CE78` | DirtyRect 向量对象 | vtable `0x7F429C`，构造 `0x6D1A60` |
| `0x00B0CE7C` | Items | `DirtyRectEntry*`，条目 0x14 字节 |
| `0x00B0CE88` | Count | 追加/删除/清空均写此 |
| `0x006D2790` | `RegisterDirtyArea` | 合并去重后写入，58 处调用 |
| `0x00486E70` | `CellClass::MarkForRedraw` | cell 包围盒 → RegisterDirtyArea |
| `0x006DA7D0` | `RegisterCellAsVisible` | 可见格登记（含脏） |
| `0x006DA980` | DirtyRect 清空 | Count 归零 + 紧凑搬移 |
| `0x00421B60` | `Drawing::Intersect` | 矩形求交 |
| `0x00487F40` | 矩形并集 | RegisterDirtyArea 合并用 |
| `0x0047FF80` | 格子屏幕包围盒 | 由 MapCoords 计算 |
| `0x0047FB90` | `GetContainingRect` | YRpp 具名，含容器对象 |

### 7.3 迷雾字段与写入

| 地址 | 说明 |
|---|---|
| `CellClass+0x120` | Shroudedness（-2/-1/0..48） |
| `CellClass+0x121` | Foggedness |
| `CellClass+0x12C` | CopyFlags：`0x08` 已探索 / `0x10` 当前可见 |
| `CellClass+0x138` | VisibilityChanged |
| `CellClass+0x140` | Flags：`cf_Fogged=0x400000` |
| `0x004A98E0` | DisplayClass 单格迷雾重算（变更→RegisterCellAsVisible） |
| `0x004801F0` | `CellClass::Draw`（L3 hook 点） |
| `0x0047F250` | `Draw_Fog`（原生 FOG.SHP） |
| `0x0047F40F/0x47F4AE` | 50% 灰雾混色（L3 补丁） |
| `0x0087F924` | 地图格子指针数组基址 |

### 7.4 `ScenarioClass+0x3598`

| 地址 | 说明 |
|---|---|
| `0x00A8B230` | `ScenarioClass::Instance` |
| `+0x3598` | 场景运行标志（YRpp `unknown_3598`），构造清 0 / 开局置 1 |
| `0x0048CFD0` / `0x0048D080` | 每帧消费者（门控 `0xA8EA70` 事件队列） |
| `0x006833E2` / `0x00684675` | 写入点（构造 / 开局） |
| `0x00A8EA70` | 事件/效果队列对象 |

---

## 8. 逆向方法备忘

- 工具：`tools/xref_scan.py`（capstone 5.0.7 线性扫描）+ 按 VA 直接反汇编指定区间；
- PE：ImageBase `0x400000`，`.text` raw offset = RVA（可直接 `file_off = va - 0x400000`）；
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
- 交叉验证：YRpp 头文件 `JMP_THIS/JMP_STD` 具名地址 + `RegisterDirtyArea`/`GetContainingRect`/`GetOcclusion`/`ViewBounds` 等符号；
- 未尽事项：`this+0xD64/D68` 与 `D6C/D70` 的精确语义（观测到「当前 vs 上次」同步，疑似 cell 坐标下的视口/脏范围原点）；`fn_6D9B50` 建筑标志 `+0x74/+0x80/+0x90` 的字段名；`0xA8EA70` 队列项 `type==0x6C` 的类型枚举。
