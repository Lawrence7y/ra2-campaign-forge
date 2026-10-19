# OPT-1 双算消除规格（R-OPT1）— force-full 跳过 Pass2 dirty 瓦片段 + Pass8 stage2

> **文件属性**：可执行落地规格（静态定谳，只读 `ra2render/**` / `gamemd.exe`）  
> **任务**：R-OPT1 ｜ **基线**：`ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`  
> **对照**：`ra2render/blitter_hooks.cpp`（只读引用行号）、`docs/re/dirty_rect_deep_dive_p2.md`（T26 唯一真收益）、`docs/re/l4_dirty_residual_check.md` + `out/re_work/re_sprint/R_l4_resid/zcode_patch_list.md`（T24 / ZC-P1）  
> **证据**：`out/re_work/re_sprint/R_opt1/**`（claims_opt1.txt、dualcompute_disasm.txt、zcode_line_list.md）  
> **实施**：ZCode（见行号清单）；本卡**不改** `ra2render/**`

---

## [0] 结论摘要

| # | 问题 | 裁决 |
|---|---|---|
| 1 | OPT-1 可执行规格 | **本文件定谳**：双钩点 + 条件（仅 force/bForce）+ 原/新语义 + 回滚 + 遥测 |
| 2 | 与 ZC-P1 依赖 | **无硬依赖**。OPT-1 不必先修 P1；但门必须是 force-only，否则与 vision-dirty 开档冲突 |
| 3 | 风险 | 漏画/E4 仅在「非 force 误跳」时发生；force-full 下双算去掉**不减像素**（后画本就覆盖） |
| 4 | 验收 | E5 式同路径像素对拍 D≡0 + 跳过计数 >0 + kill 回归 |

---

## [1] 背景与双算事实（继承 T26，已复核字节）

`L4DirtyMode=force-full`（默认）每帧 `0x6D3D99` → `0x6D3E37`，`bForceRedraw=1`。此时：

| 双算点 | 全量路径 | 冗余二次消费 | 后果 |
|---|---|---|---|
| **A. Pass2 瓦片** | `0x6D374B DrawTiles(ViewBounds)` | `0x6D378E` 起无条件扫 dirty；`bFlag=1` 条目 `0x6D3835 clear + 0x6D3841 DrawTiles` | 同区域最多 **2 次**瓦片光栅 |
| **B. Pass8 物体** | stage3 `0x6D3A63 fn_6D9920(clip=ViewBounds)`（后画） | stage2 `0x6D3A3E fn_6D9920(clip=dirty)`（先画） | stage2 **纯冗余**，像素被 stage3 覆盖 |

滚屏 strip1/2 在 force 时反被跳过（`0x6D3766/3784`）——与 dirty 双算不对称，进一步证明 dirty 扫描在 force 下是漏改的死重。

**像素不变**：两处冗余均为「多画」而非「少画」；去掉后帧末像素与保留时逐位相同（见 §4）。

---

## [2] 可执行规格

### 2.1 钩点与补丁形状

| ID | 引擎 VA | 原 5B | 跳板目标 | skip 出口 | 装/卸 |
|---|---|---|---|---|---|
| **OPT1-A** | `0x006D378E` | `A1 88 CE B0 00` | `Hook_Pass2DirtyScan_Skip` | `0x006D3866`（= 原版空表 `jle` 目标/函数尾） | `VirtualProtect` + `E9 rel32`；还原原 5B |
| **OPT1-B** | `0x006D3988` | `A1 88 CE B0 00` | `Hook_Pass8Stage2_Skip` | `0x006D3A4D`（= 原版空表 `je` 目标/stage3） | 同上 |

补丁形状沿用现网惯例（`blitter_hooks.cpp:2585-2597` / `2484-2517`）：5B `jmp rel32`，原 5B 在桩内重放后 `mov reg,imm32 + jmp reg` 回原流（**遵守 2428 标志/跳转纪律**）。

### 2.2 条件（**仅 force-full / bForce**）

| 层 | 条件 |
|---|---|
| **语义真源** | 该帧引擎 force 非 0：OPT1-A 读 **`[esp+0x58]`**（Pass2 force 字节，`0x6D3793` 前仍有效）；OPT1-B 读 **`[esp+0x68]`**（Pass8 `ret 0xC` 第 3 参 = bForce，与 `0x6D3A4D` 同源） |
| v1 装钩门 | `g_l4DirtyMode==0`（force-full）才写入 jmp；vision-dirty/vanilla **不装** |
| kill 开关 | `Opt1DualSkip=0` ⇒ 桩内恒重放原流（运行期回滚） |
| **禁止** | bForce==0 跳过；或无条件跳过；或「非 vanilla 就跳过」 |

force-full 下 bForce 每帧为真，双算跳过恒命中；将来 vision-dirty 的 force 帧可扩展同钩（像素仍不变），**非 force 帧永不跳**。

### 2.3 原语义 vs 新语义

| 点 | 原语义 | 新语义（仅 bForce） | 非 bForce |
|---|---|---|---|
| `0x6D378E..0x6D3865` | 无条件 dirty 瓦片循环（bFlag=1 再 clear+DrawTiles） | **整段跳过**，直达 `0x6D3866` 尾声 | 原 5B 重放 + 回 `0x6D3793`，与原版逐位一致 |
| `0x6D3988..0x6D3A4C` | 无条件 stage2 dirty∩ViewBounds → `0x6D9920` | **整段跳过**，直达 `0x6D3A4D` stage3 | 原 5B 重放 + 回 `0x6D398D`，与原版逐位一致 |
| stage3 `0x6D3A4D+` | bForce⇒ViewBounds 全画 | **不变**（唯一物体全量消费） | 不变 |
| Pass2 force 全量 `0x6D374B` | DrawTiles(ViewBounds) | **不变**（唯一全量瓦片） | 不变 |

**不改**：`Register_Dirty_Area` 并集、帧末 pop（`0x6D44FC+`）、L4 桩（2438-2470）、`fn_6D9920` 本体、`0x6D3D99` 补丁。

### 2.4 回滚

1. **运行期**：`Opt1DualSkip=0` → 镜像 `s_opt1DualSkipEnabled=0`，两桩走原流。  
2. **字节还原**：`s_origPass2DirtyBytes` / `s_origPass8Stage2Bytes` 写回两钩点。  
3. **DETACH**：卸载链（`RemoveCellClassDrawHook` 对称段 + F-13）**必须**包含 `0x6D378E`/`0x6D3988`，避免只还 L4 点。  
4. **回归**：kill 后与「未开 OPT-1 现网 force-full」遥测/像素一致。

### 2.5 遥测

- 计数：`s_opt1Pass2DirtySkip`、`s_opt1Pass8Stage2Skip`（每次跳过 +1）。  
- 2 秒行**新增** `[ra2render-telemetry-opt1]`（插在 `847` l4dirty 行之后，**不改**既有字段）。  
- 机判：on+force-full ⇒ 含脏帧两计数可 >0；kill ⇒ ≡0；像素对拍 D≡0 与计数并行成立。

---

## [3] 与 ZC-P1（flags）依赖关系

| 项 | 裁决 |
|---|---|
| 是否必须先修 P1 | **否** |
| 理由 | P1 只影响 `Hook_L4FullRedraw_Stub` 内 **原版 jge 是否采用**（vision-dirty/vanilla）。force-full 落 `2466-2468`，不读 flags，恒全刷。OPT-1 在 **bForce 已为真之后** 才去掉二次消费，控制流与 flags 无关。 |
| 反例风险 | 若 OPT-1 门不严（无条件 / 误含非 force），则 vision-dirty 交还 jge 的帧会丢 Pass2 瓦片与 Pass8 stage2 ⇒ **漏画**。故 §2.2「仅 force」是硬约束。 |
| 开档门槛 | vision-dirty 仍须 **ZC-P1+P2+P4**（见 `zcode_patch_list.md`）；与 OPT-1 **正交**。OPT-1 可先合入 force-full 默认档。 |

---

## [4] 风险与像素不变

| 风险 | 触发条件 | 后果 | 缓解 |
|---|---|---|---|
| **漏画瓦片/迷雾** | 误在 bForce=0 跳过 Pass2 | bFlag=1 条目不刷；迷雾/地表残留 | 门=引擎 force 字节；v1 仅 force-full 装钩 |
| **漏画物体** | 误在 bForce=0 跳过 stage2 且 stage3 不走 | 脏物体不画、NeedsRedraw 不清 | stage3 仅 bForce 走；跳过**只**在 bForce=1（此时 stage3 必走） |
| **E4 迷雾退回** | 非 force 路径 + 无对象打脏（vanilla/误放行 jge） | 灰雾滞后/漏画 | **OPT-1 不扩大 E4**：force 下全量已画；禁止把 OPT-1 接到 vanilla/非 force |
| 性能收益落空 | Count 为空的帧也计 skip | 计数虚增 | 计数在真正跳过循环体时 +1；空表本就走同一出口 |

**像素不变论证**（force 帧）：Pass2 已 `DrawTiles(ViewBounds)` 覆盖全部 dirty∪视口；Pass8 stage3 以 ViewBounds 重画并清 `Object+0x80`（`0x6D9A27`）。去掉先画/重画不改变帧末缓冲。

---

## [5] 验收像素对拍判据（E5 / R-OPT1-AC）

| # | 判据 | 级别 |
|---|---|---|
| AC1 | **同路径双跑**：force-full，`Opt1DualSkip=0` vs `=1`，同地图同操作序列 N≥120 帧，主视图 **逐帧像素差 D≡0**（或帧 CRC 全等） | 红线 |
| AC2 | 含 **bFlag=1 机动打脏** + **Pass8 有脏** 帧时 `Pass2DirtySkip`/`Pass8Stage2Skip` **>0**，且 AC1 仍成立 | 红线 |
| AC3 | **E4 雾退回镜头**：开图后单位撤离，静止视角 0 帧灰滞后；OPT-1 on/off 一致 | 红线 |
| AC4 | **kill 回归**：`Opt1DualSkip=0` 启动日志/遥测与现网 force-full 一致（两计数≡0） | 必须 |
| AC5 | 滚屏 strip、建筑损伤、动画/粒子/炮弹、小地图：无残影、无半幅 | 必须 |
| AC6 | 卸载还原后字节 `0x6D378E`/`0x6D3988` = `A1 88 CE B0 00` | 必须 |

**建议操作序列**：静止待机 → 单位移动（bFlag=1）→ 建筑开火/受击 → 开/合迷雾 → 大幅滚屏 → 小地图点击。对拍工具可复用 `out/re_work/re_sprint/R_rect_deep` / E5 既有帧 CRC 流程。

---

## [6] 给 ZCode 的行号级清单

全文见 `out/re_work/re_sprint/R_opt1/zcode_line_list.md`。摘要：

| 步 | `blitter_hooks.cpp` 锚点 | 动作 |
|---|---|---|
| 1 | **2470 后** | 计数 `s_opt1*`、开关 `g_opt1DualSkip`、两 naked 桩 |
| 2 | **2585-2603** | 安装两钩（0x6D378E / 0x6D3988）；仅 `g_l4DirtyMode==0` |
| 3 | **2607-2635** | 对称卸载 + DETACH |
| 4 | **847 后** | `[ra2render-telemetry-opt1]` 独立遥测行 |
| 5 | ini | `Opt1DualSkip`（默认 1；0=kill） |
| 6 | 验收 | §5 AC1–AC6 |

**明确不改**：`2438-2470` L4 桩（P1 另卡）、`0x6D3D99` 补丁形状、Register/并集、帧末 pop。

---

## [7] 写域合规

- 触碰：`docs/re/opt1_dualcompute_spec.md`（本文）、`out/re_work/re_sprint/R_opt1/**`
- 未触碰：`ra2render/**`、`gamemd.exe`、`ra2youli/**`、`tools/**`、台账、看板、ATLAS、`out/reverse/**`
