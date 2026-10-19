# 逐格瓦片层（0x47EFE0 / CellClass::Draw 0x4801F0）相对对象层的绘制次序 —— 定谳

[META]
task=U3-P1  executor=DSH 子代理  mode=read-only  scope_declared=新建 docs/re/layer_order_fog_vs_objects.md + out/re_work/u3p1_layerorder/**
baseline=ra2youli\gamemd.exe  MD5=4F37486E5B0DBE2AE5F45AEEE0F98367（执行前后一致，未写入二进制）
快照：本会话唯一写入者；未触碰 ra2render/**、ra2youli/**、台账、docs/RE_COORDINATION.md、其他 docs
工具链：Capstone 5.0.7 / Python 3.12.10；全部地址为**当前（已被本项目 patch 过的）基线镜像**VA，段映射 off = VA − 0x400000（.text 段）

---

## [0] 结论摘要

**裁定：逐格瓦片层（含我方挂载的半透明灰雾 Draw_Fog）在「对象层之前」绘制。**

最短证据链（全部字节级、可复算）：
1. 逐格像素唯一机制 = `CellClass::Draw 0x4801F0`；`call 0x4801F0` 全 exe 仅 2 处（0x6D3716 / 0x6D751A）。
2. 两处各自属于 F1=`0x6D3660..0x6D3870`（0x6D3716）与 `0x6D71E0..0x6D755E`（0x6D751A）；后者 4 个调用点**全部**落在 F1 内。
3. **F1 全 exe 唯一调用点 = 0x6D448B**，位于 `TacticalClass::Render`（0x6D3D10..0x6D4B4B）内一条连续 8 连直呼 pass 序列的第 2 条。
4. 对象层 = `0x6D8DB0`（Object DrawIfVisible 簇），其全 exe 唯一调用点 = **0x6D465F**，同函数内、位于 0x6D448B **之后**（中间无 ret、无可跳过分支）。
5. 收口断言：`xref 0x47EFE0`（逐格 shroud/fog 瓦片合成体）=1 处（0x480230）；`xref 0x47F250`（Draw_Fog）=2 处（0x480278/0x480290），均在 CellClass::Draw 内 ⇒ 全引擎逐格雾像素写只可能发生于 F1。

**最大风险**：本结论仅覆盖 `TacticalClass::Render` 自有 pass 序；「非逐格的整层 shroud surface 于对象层之后合成」未穷举（P2，见 [4]）。

---

## [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| 1 | 逐格瓦片层在对象层之前还是之后？ | **之前** | [实证] | 0x6D448B(call 0x6D3660) < 0x6D465F(call 0x6D8DB0)，同函数 0x6D3D10..0x6D4B4B |
| 2 | `call 0x4801F0` 的外层函数是谁？ | F1=0x6D3660..0x6D3870（ret 0x10 @0x6D386D）；另一处 0x6D71E0..0x6D755E | [实证] | 0x6D3660=83 EC 38 53 55 56 57 8B F9；0x6D386D=C2 10 00 |
| 3 | 该外层函数被谁调用？ | **唯一** 0x6D448B（Render 内） | [实证] | xref(0x6D3660)=1 → 0x6D448B；xref(0x6D71E0)=4 全在 F1 内 |
| 4 | Render 的真实入口/出口？ | 入口 0x6D3D10（81 EC F4 00 00 00; sub esp,0xF4）；末尾 ret 后 0x6D4B4B..0x6D4B4F 为 90 填充 | [实证] | 0x6D3D10 / 0x6D4B4B；xref(0x6D3D10)=0x4F44DF/0x4F44F4/0x4F4515 |
| 5 | 对象层调用点在哪？ | 0x6D4656 call 0x53D850 → **0x6D465F call 0x6D8DB0** → 0x5FFFA0/0x550240/0x4C2830/0x556D40/0x6591B0/0x6DBE20 | [实证] | 0x6D465F=E8 4C 47 00 00；与 docs/re/fx_draw_chain.md:76-87 逐条吻合 |
| 6 | 我方 Draw_Fog 是否可能覆盖对象？ | **不可能**（本层在对象层之前；且雾像素写路径被 xref 收口于 F1） | [实证] | xref(0x47F250)=0x480278/0x480290；xref(0x47EFE0)=0x480230 |
| 7 | ATLAS:426 的 Pass 8 记述对否？ | **错**：CellClass::Draw 属**地形/覆盖物层**，先于对象层；Pass 8 仅对「UI 叠加」成立 | [实证] | ATLAS:426 vs 0x6D4471..0x6D44F7 与 0x6D4656..0x6D467F 的先后 |
| 8 | ATLAS:416 的 Render 区间对否？ | **错**：0x6D3870 是被 Render 在 0x6D44F7 调用的子函数；Render 实为 0x6D3D10..0x6D4B4B | [实证] | xref(0x6D3870)=1 → 0x6D44F7；既有 docs/re/dirty_rect_deep_dive.md:53-55 已写对 |
| 9 | 「半块」是否由本层解释？ | **否** | [推演] | 由 #1 ⇒ 本层无法覆盖对象；真因见 [4]-P1 |

---

## [2] 关键证据块

`TacticalClass::Render`（0x6D3D10..0x6D4B4B）内**同一连续基本块**（无 ret、无可跳过分支）的 8 连直呼 pass，及对象层起点（`VA = 原始字节 → rel32 复算目标 / 角色`）：
- `0x6D4471` = E8 EA E6 FF FF → 0x6D2B60（层 helper：0x487F20/0x45A130/0x480A30/0x480180）
- **`0x6D448B` = E8 D0 F1 FF FF → 0x6D3660（逐格瓦片/迷雾层 F1 —— 本层全 exe 唯一调用点）**
- `0x6D449D` = E8 3E E9 FF FF → 0x6D2DE0（层 helper：0x6D7560×3）
- `0x6D44AF` = E8 BC EF FF FF → 0x6D3470（层 helper：0x4D1890×3）
- `0x6D44C1` = E8 CA ED FF FF → 0x6D3290（层 helper：0x6D6D10×4）
- `0x6D44D3` = E8 E8 F5 FF FF → 0x6D3AC0（对象二遍：0x6D97D0 → `call [obj+0x104]`）
- `0x6D44E5` = E8 56 EB FF FF → 0x6D3040（层 helper：0x6D7C00×3）
- `0x6D44F7` = E8 74 F3 FF FF → 0x6D3870（对象二遍：0x6D9920 → `call [obj+0x104]`）
- **`0x6D465F` = E8 4C 47 00 00 → 0x6D8DB0（对象层 Object DrawIfVisible 簇，其后 0x5FFFA0/0x550240/0x4C2830/0x556D40/0x6591B0/0x6DBE20）**
F1 逐格循环：`0x6D3660`=83 EC 38 53 55 56 57 8B F9（入口）→ 计数 `[edi+0xE0]`、表 `[edi+0xE4]`(CellClass*) → `0x6D369B` call 0x480A30 → **`0x6D3716` = E8 D5 CA DA FF → call 0x4801F0** → `0x6D3734` jl 0x6D3693（回边）→ `0x6D386D` = C2 10 00（ret 0x10）。
旁证（复算）：`xref(0x6D3660)`=1→0x6D448B；`xref(0x6D71E0)`=4 全在 F1 内；`xref(0x6D8DB0)`=1→0x6D465F；`xref(0x47EFE0)`=1→0x480230；`xref(0x47F250)`=2→0x480278/0x480290。断言：`out/re_work/u3p1_layerorder/claims.txt`（39 条）。

## [3] 勘误（交 Lead；本卡**不**越界修改他人文档）

| 目标文件:行号 | 改前原文 | 改后文本 | 理由 | 影响面 |
|---|---|---|---|---|
| docs/re/ARCHITECTURE_ATLAS.md:426 | 「Pass 8（迷雾与 UI 叠加）：调用 `CellClass::Draw`（`0x004801F0`）在整个视口表面叠加未探索黑雾（Shroud）与已探索灰雾（Fog），最后绘制鼠标框选框与单位血条」 | 「`CellClass::Draw` 属**地形/覆盖物层**（由 `0x6D3660` 在 Render 内 `0x6D448B` 调用，**先于**对象层 `0x6D465F`）；Pass 8 仅对 **UI 叠加**（血条/框选）成立，不含迷雾瓦片」 | 字节实证：0x6D448B < 0x6D465F，且 xref 收口 | **高**：层序表、building_fog_residual_deep_dive.md:83 的裁定依据、DEF-FOGPARTIAL 归因 |
| docs/re/ARCHITECTURE_ATLAS.md:416,421,422 | 「`TacticalClass::Render`（`0x006D3870`–`0x006D4400`）」并举 Pass 5/6 在其中 | 入口改 **0x6D3D10**（`sub esp,0xF4`），末 **0x6D4B4B**；`0x6D3870` 系 Render 在 `0x6D44F7` 调用的**子函数**（0x6D3870..0x6D3A72） | 字节实证 + 既有 docs/re/dirty_rect_deep_dive.md:53-55、dirty_rect_l4.md:31 已写对 | 中：地址区间引用 |
| docs/re/building_fog_residual_deep_dive.md:83 | U3-LIGHTPERCELL 勘误句「相对对象层的先后次序未静态闭环…在定谳前不得作为结论引用」 | 可升级为「**已定谳：本层在对象层之前**，故不能覆盖对象；『半块』与本层无关」（取证件：本卡 §0/§2） | 本卡闭环该缺口 | 中：该句可定谳，无需再挂起 |
| docs/re/ARCHITECTURE_ATLAS.md:418 | 「Pass 2（地表层光栅化）：`0x006D3812`，调用 `TerrainClass` 逐瓦片绘制地形底图」 | 0x6D3812 是 `je 0x6D384C`（74 38）之前的 `test dl,dl`，并非调用点；地形/瓦片入口在 F1 内 | 反汇编：0x6D3810=84 D2，0x6D3812=74 38 | 低：Pass 2 定位 |

---

## [4] 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证方法 | 级别 |
|---|---|---|---|---|
| 1 | 「跨灰雾边界建筑半块」的真因 | 本卡只排除本层；对象侧裁剪/掩码路径未展开 | 在 `0x6D3870`（对象二遍，VisibleCells±0x1E 与脏矩形）与 `0x6D9920` 的矩形构造处下只读断点，记录每帧传入的 RectangleStruct 与原对象屏幕包围盒 | P1 |
| 2 | 是否存在**非逐格**的整层 shroud surface 在对象层之后合成 | 逐格路径已收口；整层 blit 族未穷举（未逐条复算全部 DSurface Blit 调用方） | 对 `0x6D467F`(0x6DBE20) 及其后至 0x6D4B4B 的间接调用做动态只读跟踪，看是否触及 shroud 面 | P2 |
| 3 | ATLAS Pass 8 中「UI 叠加在对象之后」部分 | 0x6D467F 之后的 UI 代码未展开 | 反汇编 0x6D4680..0x6D4B4A 并按 vtable 槽识别 UI 绘制 | P2 |
| 4 | Render 内 mode 参数（edi，来自 [esp+0x110]）语义 | 仅见 `cmp edi,1/2/3` 分支，未见赋值方 | 追 0x4F44DF/0x4F44F4/0x4F4515 三处调用点的实参 | P2 |

---

## [5] 写作用域合规声明

**改动文件清单**（全部为本卡授权作用域）：
- `docs/re/layer_order_fog_vs_objects.md`（新建；本文件）
- `out/re_work/u3p1_layerorder/`（新建目录）：`FINDINGS.md`、`claims.txt`(39 条)、`block_order.txt`、`flow_F1.txt`、`flow_F1b.txt`、`xref_analyze.py`、`probe.py`、`walk.py`、`sweep.py`、`recover.py`、`emit_claims.py`

**未触碰清单**：`ra2render/**`、`ra2youli/**`（**只读**）、台账、`docs/RE_COORDINATION.md`、其他任何 docs 文件。
**目标二进制哈希（证明只读）**：`MD5(ra2youli/gamemd.exe) = 4F37486E5B0DBE2AE5F45AEEE0F98367`。

---

## [6] 门禁实跑输出（原文）

```
> python tools\verify_anchors.py
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
> python tools\audit_bytes.py out\re_work\u3p1_layerorder\claims.txt
合计 39 条：OK=39  MISMATCH/NOREAD=0
0x6d8db0   81 ec f0 00 00 00 53 8b  =  81 ec f0 00 00 00 53 8b  OK  对象层 DrawIfVisible 簇入口
0x6d453a   f3 a5                 =  f3 a5                  OK  Render 脏矩形向量紧凑 rep movsd
0x6d4b4b   90 90 90 90 90        =  90 90 90 90 90         OK  Render 末填充
> (Get-FileHash ra2youli\gamemd.exe -Algorithm MD5).Hash
4F37486E5B0DBE2AE5F45AEEE0F98367
```

## [7] 风险与红线提示

①**同步语义/命令序**：未触及（纯渲染层静态分析，无命令序改动）。
②**随机数消费序**：未触及。
③**存档结构**：未触及。
④**渲染像素等价性**：**触及** —— 本结论直接决定 DEF-FOGPARTIAL 的归因方向与「灰雾能否覆盖对象」的产品假设。
⇒ 凡据此改动雾气/对象绘制层者，**需要 MP 门控矩阵 / 真机对拍验收**，不得宣称「零风险」。
本卡自身为**只诊断**：未启动游戏、未注入、未改二进制、未伪造任何实测（所有断点方案均标 [待实测]）。

---

## [8] 交付物清单

| 类型 | 路径 | 规模 |
|---|---|---|
| 新文档 | `docs/re/layer_order_fog_vs_objects.md` | 本文件（10 节骨架 + [META]） |
| 结论落盘 | `out/re_work/u3p1_layerorder/FINDINGS.md` | 64 行 |
| 断言 | `out/re_work/u3p1_layerorder/claims.txt` | **39 条**（audit_bytes 全 OK） |
| dump | `out/re_work/u3p1_layerorder/block_order.txt` | 176 行（0x6D4440–0x6D4690 全反汇编） |
| dump | `out/re_work/u3p1_layerorder/flow_F1.txt` / `flow_F1b.txt` | 69 / 144 行（控制流） |
| 脚本 | `xref_analyze.py` / `probe.py` / `walk.py` / `sweep.py` / `recover.py` / `emit_claims.py` | **6 个** |

---

## [9] 待裁决项

1. **ATLAS 层序表是否按 [3] 整段重写**：建议至少改 416/421/426 三处；若 Lead 只批一处，优先 **426**（其错误直接误导「迷雾盖住对象」的实现假设）。
2. **DEF-FOGPARTIAL 归因重排**：建议撤销「逐格雾层半幅覆盖」候选，改指向 [4]-P1（对象侧矩形/掩码路径），并把 P1 探针指派给具备真机只读调试的执行方。
3. **是否需要一次真机只读探针复核**：静态证据链已自洽（xref 收口），真机探针仅作为独立复算手段；若接受静态定谳，可不占用真机窗口。
