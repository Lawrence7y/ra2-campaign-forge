# 对象二遍（0x6D3870 / 0x6D9920）局部绘制链 —— DEF-FOGPARTIAL 候选定谳

> [META]
> task=R-OBJ2ND  executor=DSH 子代理  mode=read-only（静态）
> 基线：`ra2youli/gamemd.exe` 4,825,360 B / MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`（执行前后一致）
> 作用域：新建本文件 + `out/re_work/re_sprint/R_obj2nd/**`；未触碰 `ra2render/**`、`gamemd.exe`、`ra2youli/**`、台账、其他 docs
> 工具链：Capstone 5.0.7 / Python 3.12.10；VA 映射 file_off = VA − 0x400000（.text）
> 复算：`python out/re_work/re_sprint/R_obj2nd/recompute_obj2nd.py`（37/37 PASS）；`tools/audit_bytes.py claims_gamemd.txt`（47 条）

---

## [0] 结论摘要

**DEF-FOGPARTIAL「灰雾区敌方建筑只画出一半」的「对象二遍半幅/脏矩形部分绘制」候选：在现网部署（L4DirtyMode=force-full）下可静态排除；在原版/恢复 jge 语义下机制上存在、但与已观测截图像素几何不吻合，降为低优先级残差。**

四问一句话：

| # | 问题 | 答案 | 等级 |
|---|---|---|---|
| ① | 二遍是否对同一对象再画一次？ | **是**。`0x6D3870→0x6D9920`（仅 Building）与主簇 `0x6D8DB0` 均 `call DrawIfVisible`；二遍在前（0x6D44F7）主簇在后（0x6D465F） | [实证] |
| ② | 裁剪是整对象丢弃还是像素部分绘制？ | **两者都有**：bbox∩clip=∅ → 整对象跳过；有交 → `DrawSHP(0x4AED70)` 内 `Intersect` **像素裁剪** | [实证] |
| ③ | 是否存在「只画中心格/只画一格」路径？ | **无中心格专属绘制路径**。stage1 是「每个 VisibleCell 一个 60×30 盒」；中心格只用于光照清零。多格地基（Type+0xDFC/+0xEF0）不参与二遍裁剪 | [实证] |
| ④ | 与 `0x43D539 call 0x487950` 的关系？ | **正交**。中心格 `IsShrouded` 只清打包 RGB 光照色（edi），对象仍完整绘出（可全黑）；不产生几何半幅 | [实证] |

---

## [1] 必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| Q1 | 二遍是否对同一对象再画一次 | 是。二遍 `0x6D9920` 与主簇 `0x6D8DB0` 均收口到 `DrawIfVisible` v[65]；数据源不同（`0x8A0394/0x8A03A0` vs 主簇 `0x8A0370` 计数），同一 Building 若同时在两表则同帧双路径 | [实证] | 0x6D3969/0x6D3A3E/0x6D3A63 → 0x6D9920；0x6D909E/0x6D916C/0x6D93FA → v[65]；0x6D9A21 |
| Q2 | 裁剪粒度 | **整对象丢弃**（bbox 不交）+ **像素/矩形部分绘制**（有交则 `DrawSHP` 按 bounds Intersect 裁像素） | [实证] | 0x6D99D0/0x6D99EA/0x6D99F0 拒绝分支；0x5F4B10 写回裁剪后 bounds → 0x43D290 → 0x705E00 → 0x4AED70 → 0x421B60 |
| Q3 | 只画中心格/一格 | 无「仅中心格绘制」路径。stage1 = 每 VisibleCell 60×30（屏幕轴对齐盒）；`RegisterCellAsVisible` 现网 DLL **0 命中** ⇒ VisibleCells 通常为空。地基多格（`GetFoundationData` Type+0xDFC / `eFoundation` Type+0xEF0）只用于 GetCoords 中心与放置判定 | [实证] | 0x6D3879/0x6D394A/0x6D394F；0x6DA7D0 0-hit（既有）；0x45EC20/0x45EC90/0x45ECA0 |
| Q4 | 与 0x43D539/0x487950 关系 | 中心格 IsShrouded → `xor edi,edi` 清**打包 RGB 光照色**（0x43D38C 初始化，0x43D3E4/0x43D3EB 6/5/5 位合成）。**不跳过绘制、不裁几何**。与二遍 clip 正交 | [实证] | 0x43D4F4 GetCoords → 0x43D504 sar 8 → 0x43D532 GetCellAt → 0x43D539 IsShrouded → 0x43D542 xor edi,edi → 0x43D683 call 0x705E00 |
| R | DEF-FOGPARTIAL 本候选 | **现网 force-full 可静态排除**；原版 force-off 机制残差 + 与截图几何不符 ⇒ 不足以定谳真因 | 见 [5] | 见 [5] |

---

## [2] TacticalClass::Render 调用序与对象二遍边界

### 2.1 Render 内对象相关直呼序（同函数 0x6D3D10..0x6D4B4B）

| 序 | VA | 目标 | 角色 |
|---|---|---|---|
| 1 | 0x6D4471 | 0x6D2B60 | Pass1 脏矩形预处理 + 基础瓦片 |
| 2 | 0x6D448B | 0x6D3660 | Pass2 逐格瓦片/迷雾 F1（`CellClass::Draw 0x4801F0`） |
| 3 | 0x6D449D | 0x6D2DE0 | Pass3 水岸 |
| 4 | 0x6D44AF | 0x6D3470 | Pass4 桥/覆盖物 |
| 5 | 0x6D44C1 | 0x6D3290 | Pass5 Smudge |
| 6 | 0x6D44D3 | 0x6D3AC0 | Pass6 → 0x6D97D0，**WhatAmI==0x24 Terrain**（非建筑） |
| 7 | 0x6D44E5 | 0x6D3040 | Pass7 建筑地基/底座 |
| 8 | **0x6D44F7** | **0x6D3870** | **对象二遍（VisibleCells + DirtyRect + Force）** |
| — | 0x6D4656 | 0x53D850 | 表面/调色板准备 |
| 9 | **0x6D465F** | **0x6D8DB0** | **主对象簇 DrawIfVisible（pBounds=ViewBounds）** |

**顺序硬事实**：二遍（#8）**先于**主簇（#9）。瓦片/迷雾层（#2）**先于**两者（U3-P1 已定谳，本卡复核一致）。

### 2.2 fn_6D3870 三段结构 [实证]

```
fn_6D3870(this, strip1*, strip2*, bForceRedraw)   ret 0xC @ 0x6D3A6F/0x6D3AB3
  stage1  VisibleCells[0..count)  @ [this+0xE0] 计数 / [this+0xE4] 表
          每格: screen = world−viewportOrigin; X -= 30
                clip = {X, Y, W=60, H=30}          ← 0x6D394A/0x6D394F
                call 0x6D9920(this, 1, clip, clip)
  stage2  DirtyRect 向量 0xB0CE7C/0xB0CE88 倒序
          clip = Intersect(entry, ViewBounds)       ← 0x421B60 @ 0x6D39EB
          若 W>0 且 H>0: call 0x6D9920(this, 1, clip, clip)
  stage3  若 bForceRedraw:
          call 0x6D9920(this, 1, ViewBounds, ViewBounds)  ← 0x6D3A55/0x6D3A63
          ret 0xC
          否则: strip1/strip2 非空再各 call 0x6D9920（0x6D3A8A/0x6D3AA7）
```

**stage3 是最后一笔**：即便 stage1/2 以 60×30 或小脏矩形画过局部，force 路径仍以 **ViewBounds 全视口**再画一遍。

### 2.3 fn_6D9920（区域建筑重绘原语）[实证]

```
fn_6D9920(this, flag, rectA, rectB)                 ret 0xC @ 0x6D9A4C
  clip = Intersect(rectA, rectB)                    ← 0x421B60 @ 0x6D9934
  for i in MapClass::ObjectsInLayer (Items=0x8A0394, Count=0x8A03A0):
      obj = Items[i]
      if obj->WhatAmI() != 6:        continue       ← 0x6D997C cmp eax,6  ★ Building
      if obj+0x6E7 && !0xA8ED6B:     continue
      bbox = obj->GetRenderRect()    // v[75] +0x12c
      bbox += ViewportOrigin
      if bbox ∩ clip == ∅:           continue       ← 0x6D99D0/0x6D99EA/0x6D99F0
      obj->DrawIfVisible(clip, flag, 0)             ← 0x6D9A21 v[65] +0x104
      obj+0x80 = 0                                  ← 0x6D9A27 NeedsRedraw 清零
```

**过滤器勘误**：`fx_draw_chain.md:91` 写「0x6D97D0/0x6D9920 过滤 WhatAmI==0x24」——**错**。实测：
> 【W3 勘误 · W3-A6/ISSUE-FX-FILTER-REVERSED】改前：0x6D97D0/0x6D9920 过滤 WhatAmI==0x24；改后：0x6D9920 滤 Building(6)；0x6D97D0 滤 Terrain(0x24)；依据：ra2youli/gamemd.exe:0x2D997C, 0x2D982A; errata_sync_master_table.md:20 (R-E05)；分级：P1
- `0x6D9920` = `cmp eax,6` → **Building**
- `0x6D97D0` = `cmp eax,0x24` → **Terrain**（Pass6 阴影/地形）

### 2.4 DrawIfVisible 0x5F4B10 → Draw v[69] [实证]

```
bool __stdcall DrawIfVisible(RectangleStruct* pBounds, bool EvenIfCloaked, DWORD dwUnk3)
  若 [0xA8ED6B]==0 且 Game::hWnd!=0:
      若 EvenIfCloaked==0 且 [this+0x80](NeedsRedraw)==0 → return false
      若 [this+0x81](InLimbo)!=0 → return false
  [this+0x80] = 0                                  ← 进绘制路径即清锁存
  视口相交测试 0x6D2140（WhatAmI==0x18 特例放行）
  ★ pBounds := Intersect(pBounds, ViewBounds)       ← 0x5F4B88..0x5F4CBE 写回调用方矩形
  Draw(pLocation, pBounds)                         ← 0x5F4CFD v[69] +0x114
  return true
```

二遍以 `EvenIfCloaked=1` 调用（0x6D3870 `push 1`）⇒ **不受 NeedsRedraw 门限制，必画**；主簇两站点（0x6D909E `push 0` / 0x6D916C `push 1` 的 dwUnk3 不同，EvenIfCloaked 取局部）且 **pBounds 恒 = ViewBounds（0x886FA0）**。

### 2.5 像素裁剪收口 [实证]

```
BuildingClass::Draw(pLoc, pBounds)     ret 8 @ 0x43D68F
  edi := 打包 RGB 光照（0x43D38C..0x43D42E）
  中心格 IsShrouded → edi:=0          （0x43D539/0x43D542）
  call 0x705E00(shape core)           （0x43D683）
    → call 0x4AED70 Surface::DrawSHP  （0x706458 / 0x70652D / 0x7065FD 三处）
      → Drawing::Intersect(bounds)    （0x4AEE1A）   ★ 像素级裁到 bounds
```

`YRpp/Surface.h:205-210` 签名 `DrawSHP(..., RectangleStruct const& bounds, ...)` 与字节链一致。

**⇒ 二遍的 60×30 / 脏矩形 clip 会真实切掉建筑 sprite 的一部分像素。** 机制成立。

---

## [3] 与「中心格光照 / 多格地基」的关系

| 机制 | 粒度 | 作用 | 能否产生几何半幅 |
|---|---|---|---|
| 二遍 clip_rect | 60×30 / 脏矩形 / ViewBounds | 像素裁剪 | **能**（矩形边界） |
| 0x43D539 IsShrouded | **仅中心格** | 清 edi（打包 RGB 光照） | **不能**（整对象全黑/全彩） |
| 0x7063E0 xor eax,eax | 主体核心内第二次清亮度 | 同上 | 不能 |
| 地基 Type+0xDFC/+0xEF0 | W×H 格 | GetCoords 中心、CanPlaceHere | 不参与二遍 |
| Hook_Building_Draw（DLL） | 整 v[69] 入口 | 门控整对象画/不画 | 不能（整粒度） |
| VisibleCells±0x1E | 每格 60×30 | 二遍 stage1 clip | 能（轴对齐矩形） |

任务所称「Building 多格地基 0x78」：实测 **+0x78 为 vtable 槽 30 `InWhichLayer`**（`call [eax+0x78]`），多格地基数据在 **Type+0xDFC（FoundationData）/ Type+0xEF0（eFoundation）**，均**不在**二遍裁剪链上。

---

## [4] 关键证据块（节选）

```asm
; --- 二遍 stage1 构造 60x30 并调用 ---
006D3928  83 C1 E2              add  ecx, -0x1E          ; screenX-30
006D394A  BA 3C 00 00 00        mov  edx, 0x3C           ; W=60
006D394F  BB 1E 00 00 00        mov  ebx, 0x1E           ; H=30
006D3969  E8 B2 5F 00 00        call 0x006D9920

; --- 二遍仅 Building ---
006D997C  83 F8 06              cmp  eax, 6              ; AbstractType::Building
006D997F  0F 85 A9 00 00 00     jne  0x6D9A2E            ; 非建筑跳过
006D9A21  FF 92 04 01 00 00     call dword ptr [edx+0x104] ; DrawIfVisible
006D9A27  C6 86 80 00 00 00 00  mov  byte ptr [esi+0x80], 0

; --- DrawIfVisible 写回裁剪 bounds 后调 Draw ---
005F4B56  C6 86 80 00 00 00 00  mov  byte ptr [esi+0x80], 0
005F4CFD  FF 90 14 01 00 00     call dword ptr [eax+0x114] ; Draw v[69]

; --- 像素裁剪收口 ---
00706458  E8 13 89 DA FF        call 0x004AED70          ; Surface::DrawSHP
004AEE1A  E8 41 2D F7 FF        call 0x00421B60          ; Intersect(bounds)

; --- 中心格光照（正交，不裁几何） ---
0043D539  E8 12 A4 04 00        call 0x00487950          ; IsShrouded
0043D542  33 FF                 xor  edi, edi            ; light:=0
```

断言账本：`out/re_work/re_sprint/R_obj2nd/claims_gamemd.txt`（47 条）。
复算脚本：`recompute_obj2nd.py`（37 项谓词全 PASS）。

---

## [5] DEF-FOGPARTIAL 候选裁决

### 5.1 现网部署（L4DirtyMode=force-full）——**可静态排除** [实证 + 推演]

1. `ra2render/blitter_hooks.cpp:2416-2447` 的 `Hook_L4FullRedraw_Stub` 在默认 `L4DirtyMode=force-full`（`ra2render.ini:186`）下**恒** `jmp 0x6D3E37`。
2. `0x6D3E37` 置 `bForceRedraw=1` ⇒ `fn_6D3870` **stage3 必走**，以 `clip=ViewBounds` 调 `0x6D9920`。
3. 二遍 `EvenIfCloaked=1` 不受 NeedsRedraw 门 ⇒ stage3 **必画完整视口内建筑**。
4. stage3 位于 stage1/2 **之后**，后画覆盖先画的局部切片。
5. 主簇 `0x6D8DB0` 另以 `pBounds=ViewBounds` 再画一次。
6. 且 `RegisterCellAsVisible 0x6DA7D0` 在部署 DLL **0 命中** ⇒ stage1 的 60×30 路径通常根本进不去。

**⇒ 现网每帧建筑最终以 ViewBounds 全视口像素裁剪绘出，「二遍半幅」不能作为 DEF-FOGPARTIAL 的现网真因。**

### 5.2 原版 / L4DirtyMode=vanilla（force-off）——机制残差 [推演]

- stage1（60×30×可见格）与 stage2（小脏矩形）确实可只覆盖多格建筑的一部分像素。
- 之后主簇以 ViewBounds 补全——**除非**主簇 `DrawIfVisible` 因 `NeedsRedraw(+0x80)` 已被二遍清零且 `EvenIfCloaked==0` 而早退，或对象不在主簇列表。
- 该残差依赖「二遍有、主簇无/跳过」的不对称，静态无法证伪/证实**运行期列表内容**。

### 5.3 与已观测截图几何不吻合 [实证（像素统计）+ 推演（几何匹配）]

- 既有像素定谳（`fog_partial_building_rootcause.md` F1）：缺失边界沿 **sprite 自身 extent**、西/东 3.9× 分裂，**非屏幕轴对齐条带**。
- 60×30 / 脏矩形 / ViewBounds 均为**屏幕轴对齐矩形**；像素裁剪留下的边界必为轴对齐。
- **观测几何与 clip 矩形裁剪的预测形状矛盾** ⇒ 即便机制存在，也不是截图那一帧的解释。
- 与 H1（中心格 shroud → 整对象零光照全黑 + 透明孔洞透地形 = 黑白马赛克）的「sprite 空间东西分裂」预测更吻合。

### 5.4 综合裁决

| 子候选 | 现网 force-full | 原版 force-off | 截图几何匹配 | DEF-FOGPARTIAL 定谳 |
|---|---|---|---|---|
| 二遍 60×30 半幅 | **排除** | 机制存在（低概率残差） | **不匹配** | **排除为现网真因** |
| 脏矩形部分重绘 | **排除**（stage3 兜底） | 机制存在 | **不匹配** | 同上 |
| 只画中心格/一格 | 排除（无此路径） | 排除 | — | 排除 |
| 与 0x43D539 光照 | 正交，不裁几何 | 同左 | 可解释「全黑」不解释「半」 | 不作为半幅真因 |

**最终：DEF-FOGPARTIAL 的「对象二遍只画一部分」候选，在现网可静态闭合并排除；不建议继续投入。若未来启用 `L4DirtyMode=vanilla/vision-dirty`，需按 [6] 探针复验残差。**

---

## [6] 最小真机断点探针（仅当启用 force-off 或要独立复算时）

> [待实测] 未执行。只读断点，不改像素/不注入逻辑。

| 探针 | 断点 | 记录 | 判据 |
|---|---|---|---|
| P1 二遍 clip 尺寸 | `0x6D3969` / `0x6D3A3E` / `0x6D3A63` 前 | 栈上 RectangleStruct 的 X/Y/W/H + 当时 `bForceRedraw` | force-on 时应恒见 stage3 的 W/H=ViewBounds |
| P2 同一建筑双路径 | `0x6D9A21` 与 `0x6D909E/0x6D916C` | `esi`（对象指针）+ 返回后表面像素 | 同 `esi` 同帧出现次数、后画是否补全 |
| P3 DrawSHP 实际 bounds | `0x4AED70` 入口 | 入参 bounds 与 SHP 帧包围盒 | bounds ⊂ SHP 盒 ⇒ 确认像素被裁 |
| P4 NeedsRedraw 锁存 | 对目标建筑 `+0x80` 下写断点 | 谁置位/清零、清零后主簇是否跳过 | 若主簇跳过且 clip≠ViewBounds ⇒ 半幅成立 |
| P5 几何对拍 | 同帧截「完整 vs 半缺」 | 边缘是否轴对齐 | 轴对齐 ⇒ clip 真因；sprite-extent ⇒ 否 |

**最小集 = P1+P3+P5**（一次真机窗口可完成）。

---

## [7] 勘误（交 Lead，本卡不改他人文档）

| 目标 | 改前 | 改后 | 理由 |
|---|---|---|---|
| `docs/re/fx_draw_chain.md:91` | 「0x6D97D0 / 0x6D9920 … 过滤 WhatAmI==0x24」 | **0x6D9920 滤 Building(6)；0x6D97D0 滤 Terrain(0x24)** | 0x6D997C=`83 F8 06`；0x6D982A=`83 F8 24` |
| `docs/re/l4_dirty_spec_v2.md:15` E5「对象二遍局部绘制=是」 | 未区分现网 force-full 兜底 | 补注：**机制是；现网每帧 stage3 ViewBounds 兜底 ⇒ 不会留下半幅** | 0x6D3A53/0x6D3A63 控制流 |
| 既有文档「L4DirtyMode 键不存在」 | 见 `fog_partial_building_rootcause.md:18,73` | **已过时**：源码 `blitter_hooks.cpp:696-707,2416-2447` 与 `ra2render.ini:186` 均有 `L4DirtyMode`（force-full\|vision-dirty\|vanilla） | 本轮只读源码/ini 实证 |
> 【W3 勘误 · W3-A6/ISSUE-STALE-L4-EXIST】改前：L4DirtyMode 键不存在；改后：L4DirtyMode 已在 blitter_hooks.cpp:757 读取并支持 force-full / vision-dirty 模式；三处 ini 均已配置出厂值。；依据：ra2render/blitter_hooks.cpp:757; ra2render/ra2render.ini:251; ra2youli/ra2render.ini:186; ra2bench/ra2render.ini:186；分级：P1
| 任务卡「Building 多格地基 0x78」 | — | +0x78=InWhichLayer；地基在 Type+0xDFC/+0xEF0 | YRpp + 0x45EC20 链 |

**附带发现（非本卡范围，仅登记）**：`Hook_L4FullRedraw_Stub` 的 `vanilla`/`vision-dirty` 分支在 `cmp [g_l4DirtyMode],…` 之后 `jge`，**并未**按注释 `popfd` 还原 `0x6D3D97 cmp` 的 flags——`jge` 吃到的是桩内 `cmp/inc` 的 flags。默认 `force-full` 不受影响；若启用其余两档，滚动全刷判据可能错。建议单独立卡。

---

## [8] 写作用域与只读证明

* **新增**：`docs/re/render_second_pass_deep_dive.md`（本文件）；`out/re_work/re_sprint/R_obj2nd/`（`disasm_obj2nd.py`、`dump_strip.py`、`dump_drawifvisible.py`、`recompute_obj2nd.py`、`claims_gamemd.txt`、`FINDINGS.md`）。
* **未触碰**：`ra2render/**`（仅 grep/read）、`ra2youli/**`（只读）、`tools/**`、台账、其他 `docs/**`、任何二进制。
* **哈希**：`gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`（= 基线）。
* **未启动游戏 / 未注入 / 未改字节。**

## [9] 交付物清单

| 类型 | 路径 |
|---|---|
| 文档 | `docs/re/render_second_pass_deep_dive.md` |
| 断言 | `out/re_work/re_sprint/R_obj2nd/claims_gamemd.txt`（47 条，audit 47/47 OK） |
| 复算 | `out/re_work/re_sprint/R_obj2nd/recompute_obj2nd.py`（37/37 PASS） |
| 反汇编脚本 | `disasm_obj2nd.py` / `dump_strip.py` / `dump_drawifvisible.py` |
| 过程 | `out/re_work/re_sprint/R_obj2nd/FINDINGS.md` |
