# 脏矩形深潜 P2（R-RECT-DEEP）：ABI · 并集 · 帧末消费 · L4 交互 · 残留定谳

> **文件属性**：静态逆向定谳报告（P2 收口）  
> **任务**：R-RECT-DEEP（dirty_rect 首次 sprint 深潜）  
> **基线**：`ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`（只读）  
> **对照**：YRpp `TacticalClass.h` / `BasicStructures.h`；`ra2render/blitter_hooks.cpp`（只读）  
> **前置**：`docs/re/dirty_rect_deep_dive.md`、`dirty_rect_l4.md`、`l4_dirty_safety.md`、`l4_dirty_residual_check.md`、`render_second_pass_deep_dive.md`  
> **证据**：`out/re_work/re_sprint/R_rect_deep/**`（claims 48/48 + dump_*.txt）

---

## [0] 结论摘要

| # | 问题 | 裁决 | 等级 |
|---|---|---|---|
| 1 | 脏矩形 ABI / 并集 / 帧末消费 / 与 Render 关系 | **定谳** | [实证] |
| 2 | 引擎原生 dirty vs L4 全量/折中：双算 | **存在**（force-full 下 Pass2 + Pass8 各一处） | [实证] |
| 2b | 同上：漏算 | **vision-dirty 视口窗 1 帧滞后残差**；MarkForRedraw `bFlag=0` 不刷瓦片/迷雾（既有勘误，非新漏） | [实证]+[推演] |
| 3 | 「矩形裁剪局部重绘」残留路径 | **现网 force-full 可排除**（Pass8 stage3 ViewBounds 兜底）；force-off 机制残差保留（同 T3/R-OBJ2ND） | [实证] |
| 4 | 可落地优化 | **仅 1 处真收益**：force-full 跳过 Pass2 dirty 瓦片段 + Pass8 stage2。其余 **无额外收益** | [实证]+[推演] |

---

## [1] 脏矩形 ABI（Register_Dirty_Area `0x006D2790`）

### 1.1 调用约定

```cpp
void __thiscall TacticalClass::Register_Dirty_Area(
    /* ecx = this = TacticalClass::Instance* ([0x887324]) */
    RectangleStruct Area,   // 16B 按值栈传：X,Y,Width,Height（相对 ViewBounds 原点）
    bool bFlag              // 4B：1=Pass2 可刷瓦片/迷雾；0=仅 Pass8 物体
); // ret 0x14  callee-clean 20B
```

**栈布局（函数序言 `sub esp,0x58` + 4 寄存器 push 之后）**：

| 槽位 | 内容 | 锚点 |
|---|---|---|
| `[esp+0x6C]` | Area.X | `0x6D28F0 8B 4C 24 6C` |
| `[esp+0x70]` | Area.Y | — |
| `[esp+0x74]` | Area.Width | — |
| `[esp+0x78]` | Area.Height | — |
| `[esp+0x7C]` | bFlag | `0x6D2A3C 8A 44 24 7C` |
| — | `ret 0x14` | `0x6D2AC1 C2 14 00` |

**实参构造惯用式（58 处调用点主流形态）**——注意 **bFlag 先 push，Rect 后 `sub esp,0x10` 写入**，不是 5 连 push：

```asm
push 0                  ; bFlag = 0（★第一推）
sub  esi, [0x886FA0]    ; X -= ViewBounds.X
sub  esp, 0x10          ; 16B RectangleStruct 就地构造
sub  ecx, [0x886FA4]    ; Y -= ViewBounds.Y
mov  edx, esp
mov  [edx],    esi      ; X
mov  [edx+4],  ecx      ; Y
mov  ecx, [0x887324]    ; this
mov  [edx+8],  ebx      ; W
mov  [edx+0xC], eax     ; H
call 0x6D2790
```

证据：`caller_windows.txt` 中 `MarkForRedraw 0x486FB5 6A 00` / `Anim 0x424273 6A 00` / `0x6D9B15 6A 00` / `0x6B366A 6A 00` / `0x4A1A78 6A 00`；`ObjectClass::vfunc_54 0x5F5118 6A 01`、第二站点 `0x5F4E47 6A 01`。

> **勘误（相对旧分类脚本）**：`classify_bflag.py` 取「窗口内最后一次 push」当 bFlag —— 错。末次写入多为 Rect 字段 store，bFlag 是 **arg 序列的第一推**（或在 `sub esp,0x10` 之前的 `push imm`）。`caller_bflag.txt` 的 `bFlag0=0 bFlag1=0` 是脚本失真，不是引擎无 bFlag 二分。

### 1.2 脏矩形条目与向量

```cpp
struct DirtyRectEntry {          // 20B，stride 0x14
    int32_t X, Y, Width, Height; // +0x00..0x0C，相对 ViewBounds
    uint8_t bFlag;               // +0x10
    uint8_t pad[3];
}; // lea edi,[ecx+eax*4] + rep movsd×5（0x6D2AB0/0x6D2AB3）
```

全局 `VectorClass`：`Items=0xB0CE7C`，`Count=0xB0CE88`，`CapInc=0xB0CE8C`（满则 +10 扩容）。  
坐标系：**相对 ViewBounds（`0x886FA0` = X, `0x886FA4` = Y, `0x886FA8` = W, `0x886FAC` = H）**；Pass1/Pass2/Pass8 消费时再 `+ViewBounds` 还原屏幕绝对坐标。

### 1.3 并集 / 去重算法（`0x6D2790` 全文）

按序四段（全部 [实证]）：

1. **精确去重** `0x6D28F0..0x6D2942`：与现有条目 X/Y/W/H 全等且 `!new.bFlag || existing.bFlag` ⇒ 直接丢弃。
2. **全包含剪枝** `0x6D2947..0x6D29D0`：新矩形包含旧条目且标志相容 ⇒ `rep movsd`（`0x6D29B6`）紧凑删除旧项。
3. **贪心合并** `0x6D29D2..0x6D29F5`：对每个候选算 bbox 并集（`call 0x487F40` @ `0x6D2B01`），`imul` 比较面积增量（`0x6D29D2 8B 4C 24 78 0F AF EF`），取增量最小者；合并后 `merged.bFlag = a || b`（`0x6D2B32 88 5C 24 50`）。
4. **追加** `0x6D2A28..0x6D2AB8`：无合并对象时写 `Items[Count]`，`Count++`（`0x6D2AA1`），`rep movsd×5` 入 20B 条目。

相交判定走 `Drawing::Intersect 0x421B60`（`0x6D27F6`）。

### 1.4 bFlag 二分语义（Pass2 门）

| bFlag | 典型来源 | Pass2 (`0x6D3660`) | Pass8 |
|---|---|---|---|
| **1** | `ObjectClass::vfunc_54` 移动打脏（`0x5F5118`/`0x5F4E47`） | `0x6D3812 74 38` **不跳**：clear `0x411330` + `DrawTiles 0x6D71E0` | 正常 stage2 |
| **0** | `MarkForRedraw`（`0x486FB5`）、Anim（`0x424273`）、多数 UI/特效 | **跳过瓦片/迷雾**，仅记条目 | 仍画物体 |

⇒ 既有勘误成立：`MarkForRedraw(bFlag=0)` **不能**驱动地表瓦片与 `CellClass::Draw` 迷雾；迷雾局部刷新须走 `RegisterCellAsVisible 0x6DA7D0` 或 `bFlag=1`。

---

## [2] 帧末消费与 `TacticalClass::Render 0x6D3D10..0x6D4B4B` 关系

### 2.1 决策树（静止跳过门）

```
drawMode==0 && |scrollDX|>=ViewBounds.W  ──jge 0x6D3D99──► force 0x6D3E37
                |scrollDY|>=ViewBounds.H  ──jge──────────► force
bForceRedraw!=0 ────────────────────────────────────────► 0x6D3E9B 进绘制
NeedRedraw(D7C) / 建筑需画 / Count!=0 / Redrawing(D7D) / D64↔D6C / D68↔D70
    全 0 ──je 0x6D3E2F──► 0x6D4758 收尾（跳过视口）
其余 → 0x6D3E9B 进 8 阶段
```

L4 补丁点即 `0x6D3D99`（磁盘原版 `0F 8D 98 00 00 00` = `jge 0x6D3E37`；运行期被 DLL 桩替换）。

### 2.2 八阶段中脏矩形的消费点

| Pass | 入口 | dirty 角色 |
|---|---|---|
| 1 `0x6D2B60` | `!bForce` 时 clip dirty→ViewBounds，空则删除，写回条目（`0x6D2C6B`）；随后 VisibleCells 基瓦 `0x480180` 不透明冲刷 | **预处理 + 剔除** |
| 2 `0x6D3660` | force⇒`DrawTiles(ViewBounds)`（`0x6D3744/374B`）；**随后无条件扫 dirty**（`0x6D378E`），`bFlag=1` 才 clear+DrawTiles | **瓦片/迷雾唯一消费** |
| 3–7 | 水岸/桥/Smudge/阴影/地基，遍历 VisibleCells | 不读 dirty 表 |
| 8 `0x6D3870` | stage1 VisibleCells 60×30 → `0x6D9920`；stage2 dirty∩ViewBounds → `0x6D9920`；**stage3 `bForce`⇒ViewBounds 再 `0x6D9920`** | **物体层消费 + force 兜底** |

### 2.3 帧末清空（绝不跨帧残留）

```
0x6D44FC  Count 倒序弹出：Count--（0x6D451C）+ rep movsd 紧凑（0x6D453A）
0x6D4571  VisibleCellCount = 0（TacticalClass+0xE0）
0x6D4B30  NeedRedraw D7C = 0
0x6D4B37  Redrawing  D7D = 0
```

同帧闭环：Register → Pass1 裁剪 → Pass2/8 消费 → 帧末 pop。**无跨帧脏表**。

### 2.4 与 58 调用点 / 48 Flag_To_Redraw 的关系

- `Register_Dirty_Area` 58 处直呼（机动 `0x5F5146`、Anim `0x42428F`、Bridge/MarkForRedraw `0x486FD1`、Particle/Bullet 族…）。
- `Flag_To_Redraw 0x4F42F0` 48 处：只置 `TacticalClass+0xD7D`，**不写 dirty 表**；用于「无矩形也要进绘制」的全局唤醒。
- 二者正交：dirty 表管**区域**，D7D 管**是否画**。

---

## [3] 引擎原生 dirty vs 我方 L4 全量/折中

### 3.1 三档语义（`blitter_hooks.cpp:2438-2470`，只读）

| L4DirtyMode | 0x6D3D99 行为 | 与引擎 dirty 关系 |
|---|---|---|
| `force-full`（默认） | 恒 `jmp 0x6D3E37`，`bForceRedraw=1` | dirty 表仍被 Register 填满，**并在 force 路径上被二次消费** |
| `vision-dirty` | 迁移==0 && ramp==0 时走原版 jge | 有迁移⇒全刷（盖住 E4 雾退回洞）；静态⇒交还 dirty 闭环 |
| `vanilla` | 恒原版 jge | 雾退回无对象打脏 ⇒ **漏画**（E4）；不满足 TC-L4-01 |

### 3.2 双算（force-full 下**确定存在**）[实证]

**A. Pass2 瓦片双画**

```
0x6D3744  push ViewBounds
0x6D374B  call DrawTiles(ViewBounds)     ; force 全量瓦片
0x6D378E  mov eax, [0xB0CE88]            ; ★无条件扫 dirty（不看 bForce）
0x6D3812  je  skip                       ; 仅 bFlag=0 跳过
0x6D3835  call clear(0x411330)
0x6D3841  call DrawTiles(dirty_rect)     ; bFlag=1 条目再画一遍
```

force 路径先全量瓦片，再对 `bFlag=1` 条目 clear+DrawTiles **重做**。同区域最多 2 次瓦片光栅。

**B. Pass8 物体双画**

```
0x6D3A3E  call 0x6D9920(clip=dirty)      ; stage2
0x6D3A5F  push 1
0x6D3A63  call 0x6D9920(clip=ViewBounds) ; stage3 force 兜底（后画覆盖）
```

stage3 在 stage2 之后，以更大矩形重画 ⇒ stage2 纯冗余（只多耗 CPU，像素被覆盖）。

**双算不漏画、不多画错画**，只是填充率浪费。滚动条带 `strip1/2` 在 force 时反而被跳过（`0x6D3766/3784 jne skip`）——与 dirty 双算不对称。

### 3.3 漏算

| 洞 | 条件 | 后果 | 等级 |
|---|---|---|---|
| E4 雾/黑幕退回无对象打脏 | `vanilla` 或误放行 jge | 灰雾滞后/漏画 | [实证]（机制） |
| vision-dirty 视口窗 1 帧滞后 | `blitter_hooks.cpp:1672` `s_viewCell*` 扫描末复位 | 边界格迁移漏计⇒可能误放行 jge | [推演]（方向多刷/保守与漏计并存，见 residual P2-1） |
| `MarkForRedraw bFlag=0` | 只驱动 Pass8 | 不刷瓦片/迷雾 | [实证]（既有勘误） |
| VisibleCells 满 800 | `RegisterCellAsVisible` 仍置 D7D | 格未入表但全量门打开；局部打脏需 >350 保底 | [实证] |

**无迁移时**（L4-DIRTY-SAFETY E2/E3）：机动/Anim/Particle/Bullet/Bridge 均自打脏 ⇒ jge 路径不漏动态要素。

---

## [4] 局部重绘残留路径定谳

### 4.1 机制存在（force-off）[实证]

- `fn_6D9920 0x6D9920`：入口 `Intersect` 像素裁剪（`0x6D992F`），画完清 `Object+0x80 NeedsRedraw`（`0x6D9A27`）。
- 二遍三段 clip：VisibleCells 60×30（`0x6D3969`）/ dirty∩ViewBounds（`0x6D3A3E`）/ force ViewBounds（`0x6D3A63`）。
- 主簇 `0x6D8DB0` 系 pBounds **恒 ViewBounds**（`0x6D9076`/`0x6D9167`）⇒ 主体绘制不走小矩形。

### 4.2 现网排除（force-full）

1. 桩恒 `jmp 0x6D3E37` ⇒ `bForceRedraw=1`。
2. Pass8 **stage3 必走** ViewBounds 全画，后画覆盖 stage1/2 局部切片。
3. `EvenIfCloaked=1`（`0x6D3955`）不受 NeedsRedraw 门。
4. 部署 DLL `RegisterCellAsVisible 0x6DA7D0` **0 命中** ⇒ stage1 通常空。

⇒ **「矩形裁剪只画半幅」在现网不能残留**。与 T3 对象二遍、R-OBJ2ND 结论一致：截图半幅非矩形 clip 真因。

### 4.3 残差条件（保留，不升优先级）

仅当 **force-off（vision-dirty/vanilla）且主簇被跳过** 时，stage1/2 小 clip 画不完整多格建筑——机制残差，需真机 P1/P3/P5 探针（见 `render_second_pass_deep_dive.md` [6]）。与本卡「半幅现网排除」不冲突。

---

## [5] 可落地优化点 / 「无额外收益」

### 5.1 真收益（唯一）[实证+推演]

**OPT-1 force-full 去双算**（改 DLL 侧，不动 gamemd）：

- Pass2：`bForceRedraw==1` 时 **跳过 `0x6D378E` 起的 dirty 瓦片扫描**（或等价：扫描前 `if (force) goto end`）。
- Pass8：force 时 **跳过 stage2**，直进 stage3。

收益：去掉与全量路径重叠的二次光栅；像素语义不变（后画本就覆盖）。  
风险：极低——两处均为「多画」而非「少画」；须回归 force-full 与现网逐位等价（E5 像素对拍）。

### 5.2 无额外收益（明确不做）

| 候选 | 为何无收益 |
|---|---|
| 手动补打脏（机动/Anim/…） | 引擎 58 点 Register 已闭环（L4-DIRTY-SAFETY） |
| 改 Register 合并策略 | 贪心+包含+去重已是最小侵入；改合并易面积膨胀 |
| 帧末提前 pop | 现行同帧消费完即清，无跨帧残留可省 |
| Pass3–7 读 dirty | 这些 Pass 本就不吃 dirty 表；改架构风险 > 收益 |
| 局部打脏 3×3 外扩 + >350 保底 | 已是 `l4_vision_dirty_final_spec.md` 既定最优（`RegisterCellAsVisible`）；**未实现不阻塞**，且不属于 dirty ABI 本体 |
| 强行给 `MarkForRedraw` 抬 `bFlag=1` | 会触发瓦片 clear+DrawTiles，**增加**双算面；且语义被 20 年调用方依赖 |

### 5.3 开档前置（引用，不重复实施）

`l4_dirty_residual_check.md` P0-1 flags 纪律（`pushfd/popfd`）、P0-2 E5 像素对拍、P1-1 遥测语义、P2-1 视口窗外扩 —— 仍是 vision-dirty 放行门槛；本卡不改 `ra2render/**`。

---

## [6] 证据锚点索引

| 主题 | 锚点 |
|---|---|
| ABI / 入参 | `0x6D2790` 入口 `83 EC 58 8B 0D 88 CE B0 00`；`0x6D2A3C` bFlag；`0x6D2AC1 ret 0x14` |
| 并集 | `0x6D27F6` Intersect；`0x6D29B6 rep movsd`；`0x6D2B01` union；`0x6D2B32` bFlag\| |
| bFlag=1 | `0x5F5118 6A 01` / `0x5F4E47 6A 01` |
| bFlag=0 | `0x486FB5 6A 00` / `0x424273 6A 00` |
| Pass2 门 | `0x6D380C/3812 74 38`；force DrawTiles `0x6D3744/374B`；无条件脏扫 `0x6D378E` |
| Pass8 三段 | `0x6D3969` / `0x6D3A3E` / `0x6D3A63` |
| 帧末 | `0x6D44FC` / `0x6D451C` / `0x6D453A` / `0x6D4571` / `0x6D4B30` / `0x6D4B37` |
| L4 点 | `0x6D3D99` 原版 `jge`；force 入口 `0x6D3E37`；跳过出口 `0x6D3E2F→0x6D4758` |
| 残留 clip | `0x6D9920` / `0x6D9A27` 清 NeedsRedraw |

claims：`out/re_work/re_sprint/R_rect_deep/claims_gamemd.txt`（48 条，`recompute_rect_deep.py` 复算 48/48 PASS；本环境 bash 受限未重跑，字节序列与 dump 交叉一致）。

---

## [7] 写域合规

- 触碰：`docs/re/dirty_rect_deep_dive_p2.md`（本文）、`out/re_work/re_sprint/R_rect_deep/**`
- 未触碰：`ra2render/**`、`gamemd.exe`、`ra2youli/**`、`tools/**`、台账、看板、ATLAS、`out/reverse/**`
