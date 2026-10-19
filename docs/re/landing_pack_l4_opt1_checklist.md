# L4 + OPT-1 合并落地检查单（R-L4-MERGE）

> **任务**：R-L4-MERGE ｜ **读者**：ZCode（落地实施方）+ 验收方  
> **依据**：`docs/re/opt1_dualcompute_spec.md`（R-OPT1）+ `docs/re/l4_dirty_residual_check.md`（R-L4-RESID）+ `out/re_work/re_sprint/R_opt1/zcode_line_list.md`  
> **配套补丁清单**：`out/re_work/re_sprint/R_l4_resid/zcode_patch_list.md`（ZC-P1..P5）  
> **本卡写域**：本文 + `out/re_work/re_sprint/R_l4_merge/**`  
> **禁写**：`ra2render/**`、`gamemd.exe` / `ra2youli/**`、`tools/**`、台账、看板  
> **基线**：`ra2render/blitter_hooks.cpp`（2026-09-30 15:04，3505 行）；`ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`

**一句话**：OPT-1（force-full 去双算）与 ZC-P1（flags）**无硬依赖、可并行合入**；但 OPT-1 门必须 force-only。vision-dirty 开档仍须 ZC-P1+P2+P4。**vanilla 禁止当 v1.5.0 等价档。**

---

## [0] 合并依赖序（先读）

| 序 | 项 | 依赖 | 裁决 | 可否与 OPT-1 并行 |
|---|---|---|---|---|
| D1 | **OPT-1**（双钩跳过 Pass2 dirty 瓦片段 / Pass8 stage2） | 仅 `L4DirtyMode==force-full` 装钩；门=引擎 bForce 字节 | **可独立合入**，默认档像素不变 | — |
| D2 | **ZC-P1**（`Hook_L4FullRedraw_Stub` pushfd/popfd） | 无外部依赖 | **vision-dirty 开档硬门槛**；不阻塞 OPT-1 | **是** |
| D3 | **ZC-P2**（`s_l4RedrawSkippedStatic` 语义与机判统一） | 建议在 P1 同批 | vision-dirty 开档硬门槛 | **是** |
| D4 | **ZC-P4**（E5 + TC-L4-01 实跑） | P1+P2 落地后 | **红线**；开 vision-dirty 前必跑 | 验收并行于 OPT-1 AC |
| D5 | **ZC-P5**（vanilla 风险明示） | 文档/机判 | 必须；与代码并行 | **是** |
| D6 | **ZC-P3**（视口窗外扩 1 格 / 双帧并集） | 无 | 建议，不阻断 | **是** |
| D7 | **vision-dirty 开档放行** | **D2+D3+D4 完成** | 未完成前不得开 | 否（串在此后） |

### 依赖序裁决（合并编排用）

1. **OPT-1 ⇔ ZC-P1：无硬依赖。**  
   - P1 只改 `Hook_L4FullRedraw_Stub`（2438-2470）内 **原版 jge 是否采用**（vision-dirty/vanilla）。  
   - force-full 落 2466-2468，**不读 flags**，恒 `jmp 0x6D3E37`；OPT-1 在 **bForce 已为真之后** 去掉二次消费，控制流与 flags 无关。  
   - **建议落地顺序**：OPT-1 可先合入 force-full 默认档；P1/P2/P4 仍是 vision-dirty 开档门槛，互不阻塞。
2. **硬约束（否则与 P1/开档冲突）**：OPT-1 门必须是 **仅 force/bForce**。若写成「非 vanilla 就跳过」或无条件跳过，vision-dirty 交还 jge 的非 force 帧会丢 Pass2 瓦片与 Pass8 stage2 ⇒ **漏画**。
3. **串行唯一硬点**：`L4DirtyMode=vision-dirty` 放行（D7）必须排在 P1+P2+P4 之后；与 OPT-1 合入先后无关。
4. **DETACH 合并注意**：卸载链须同时包含 L4 点 `0x6D3D99` **与** OPT-1 两点 `0x6D378E`/`0x6D3988`，禁止只还 L4 点。

- [ ] D1 OPT-1 双钩 + 计数 + 开关 + 遥测已合入  
- [ ] D2 ZC-P1 pushfd/popfd 已合入  
- [ ] D3 ZC-P2 计数语义与 845 机判已统一  
- [ ] D4 E5 + TC-L4-01 + OPT-1 AC1–AC6 已实跑并留证  
- [ ] D5 vanilla 禁令已写入注释/ini/机判  
- [ ] D6（建议）ZC-P3 视口外扩  
- [ ] D7 vision-dirty 开档仅在 D2+D3+D4 全绿后放行  

---

## [1] 行号一张表（`blitter_hooks.cpp` + 引擎 VA + ini）

> 行号以基线 2026-09-30 15:04 / 3505 行为准。ZCode 落地只按表，不重新静态推理。

| ID | 位置 | 锚点行号 / VA | 动作 | 归属 | 开档门槛 |
|---|---|---|---|---|---|
| **L-01** | L4 桩本体 | `blitter_hooks.cpp:2438-2470` `Hook_L4FullRedraw_Stub` | **ZC-P1**：入口 `pushfd`；原版 `jge` 前 `popfd`，jge 必须建立在 **还原后 flags** 上；force-full 落 `l4_restore_and_force`（popfd 后恒全刷） | ZC-P1 | **必须** |
| **L-02** | 同上 | `2451-2455` / `2459-2465` + 机判 `843-845` | **ZC-P2**：`inc s_l4RedrawSkippedStatic` 只计真落到 `0x6D3D9F` 的帧；`845` 改为 force-full⇒≡0 / vision-dirty 静态真跳⇒>0 / vanilla 无恒>0 | ZC-P2 | **必须** |
| **L-03** | 扫描窗 | `1645-1674`（窗复位 `1672-1674`） | **ZC-P3**：视口窗外扩 1 格或 `s_viewCell*Prev ∪ 当帧` 并集 | ZC-P3 | 建议 |
| **L-04** | 注释/机判 | `51-54` + `843-845` + `ra2render.ini:202-212` | **ZC-P5**：明示 **vanilla 不满足 v1.5.0 即时性，禁止作 safe 默认/等价档** | ZC-P5 | **必须** |
| **L-05** | 新增符号块 | **`2470` 后**（L4 桩结束 与 `s_origTacticalRedrawBytes` 之间） | 新增 `s_opt1Pass2DirtySkip` / `s_opt1Pass8Stage2Skip`（`extern "C" uint32_t`）；`s_opt1DualSkipEnabled`（u8 镜像）；`g_opt1DualSkip`（bool，默认 true）；`s_origPass2DirtyBytes[5]` / `s_origPass8Stage2Bytes[5]` | OPT-1 | — |
| **L-06** | 同上 | `2470` 后 | `__declspec(naked) Hook_Pass2DirtyScan_Skip()`：`cmp [esp+0x58],0`；force≠0 ⇒ `inc s_opt1Pass2DirtySkip` + `jmp 0x6D3866`；否则重放 `A1 88 CE B0 00` + `mov ecx,0x6D3793; jmp ecx` | OPT-1 | 仅 bForce |
| **L-07** | 同上 | `2470` 后 | `__declspec(naked) Hook_Pass8Stage2_Skip()`：`cmp [esp+0x68],0`；force≠0 ⇒ `inc s_opt1Pass8Stage2Skip` + `jmp 0x6D3A4D`；否则重放原 5B + `jmp 0x6D398D` | OPT-1 | 仅 bForce |
| **L-08** | 安装 | `2585-2603`（L4 补丁安装段 `2585-2597` 之后，或 `2603` 同级独立 `InstallOpt1DualSkipHooks()`） | `VirtualProtect` + 5B `E9 rel32` 写入两钩点；**仅 `g_l4DirtyMode==0`** | OPT-1 | 装钩门 |
| **L-09** | 卸载 | `2607-2635`（仿 L4 还原 `2633-2635`）+ DETACH | 对称写回 `s_origPass2DirtyBytes`/`s_origPass8Stage2Bytes`；**F-13 卸载列表追加两地址** | OPT-1 | **必须** |
| **L-10** | 遥测行 | **`847-850` l4dirty 行之后**（仿 `870` 只追加纪律） | 新增 `[ra2render-telemetry-opt1]`：`opt1Enabled` / `Pass2DirtySkip` / `Pass8Stage2Skip`；**不改**既有字段 | OPT-1 | — |
| **L-11** | ini | `ra2render.ini` L4 段（`202-212` 旁） | `Opt1DualSkip` 默认 **1**（0=kill 运行期回滚）；`L4DirtyMode` 默认 `force-full`，非法值收敛 `force-full`（解析 `718-732`） | 共用 | — |
| **E-A** | 引擎 | `0x006D378E` 原 5B `A1 88 CE B0 00` | **OPT1-A** 装钩点（Pass2 dirty 瓦片扫描入口） | OPT-1 | — |
| **E-A2** | 引擎 | `0x006D3866` | OPT1-A skip 出口（= 原版空表 `jle` 目标 / 函数尾） | OPT-1 | — |
| **E-B** | 引擎 | `0x006D3988` 原 5B `A1 88 CE B0 00` | **OPT1-B** 装钩点（Pass8 stage2 入口） | OPT-1 | — |
| **E-B2** | 引擎 | `0x006D3A4D` | OPT1-B skip 出口（= stage3；`[esp+0x68]`=bForce） | OPT-1 | — |
| **E-L4** | 引擎 | `0x006D3D97` cmp / `0x006D3D99` 补丁 / `0x006D3D9F` 跳过全刷 / `0x006D3E37` 全量 | L4 全量/交还二分；**不改** `0x6D3D99` 补丁形状 | ZC-P1 旁 | — |
| **E-P2f** | 引擎 | `0x006D374B` `DrawTiles(ViewBounds)` | force 全量瓦片（OPT-1 去双算后**唯一**全量瓦片消费；**不变**） | OPT-1 | — |
| **E-P8s3** | 引擎 | `0x006D3A63` `fn_6D9920(clip=ViewBounds)` | stage3 后画（**不变**；bForce 时必走） | OPT-1 | — |
| **纪律** | 同文件 | `2428` 注释 | 跳板回流一律 `mov reg,imm32 + jmp reg`；勿改 | 共用 | — |

**明确不改**：`2438-2470` 的 L4 控制流骨架（P1 只补 flags 纪律）、`0x6D3D99` 补丁形状、`Register_Dirty_Area` 并集、帧末 pop（`0x6D44FC+`）、`fn_6D9920` 本体、扫描侧 `1638-1667`（已解耦）。

### 建议实施串（合并编排单）

1. **批 A（可先合）**：L-05 → L-06/L-07 → L-08/L-09 → L-10/L-11（OPT-1 全套，默认档 force-full）。  
2. **批 B（与 A 并行）**：L-01（P1）→ L-02（P2）→ L-04（P5 文档）。  
3. **批 C（验收）**：L-03（建议）→ E5/TC-L4-01 + OPT-1 AC1–AC6。  
4. **批 D**：全绿后才放行 `L4DirtyMode=vision-dirty`。

---

## [2] L4DirtyMode × Opt1DualSkip 开关矩阵

> `L4DirtyMode`：`0=force-full`（默认，非法收敛至此）｜`1=vision-dirty`｜`2=vanilla`  
> `Opt1DualSkip`：`1=on`（默认）｜`0=kill`（运行期恒重放原流）  
> v1 装钩门：**仅 `L4DirtyMode==force-full` 时写入 OPT-1 两钩**；vision-dirty / vanilla **不装**。

| # | L4DirtyMode | Opt1DualSkip | OPT-1 钩 | 运行期行为 | 两跳过计数 | 验收机判 | 放行状态 |
|---|---|---|---|---|---|---|---|
| M1 | **force-full (0)** | **1 (on)** | **装** | bForce 帧跳过 Pass2 dirty 瓦片段 + Pass8 stage2；全量路径不变 | 含脏帧可 **>0** | 像素对拍 **D≡0** 且计数>0（OPT-1 AC1+AC2） | **推荐合入态** |
| M2 | force-full (0) | **0 (kill)** | 装但桩内恒重放 | ≡ 现网 force-full（未开 OPT-1） | **≡0** | kill 回归=现网（AC4）；与 M1 同路径像素 D≡0 | 一键回滚档 |
| M3 | vision-dirty (1) | 1 | **不装** | P1 修好后按原版 jge / 强制全刷二分；无 OPT-1 双算跳过 | **≡0**（v1 不装钩） | E5 + TC-L4-01（ZC-P4） | **须 P1+P2+P4 全绿** |
| M4 | vision-dirty (1) | 0 | **不装** | 同 M3（开关无意义） | ≡0 | 同 M3 | 同 M3 |
| M5 | **vanilla (2)** | 1 | **不装** | 原版 jge；静态+迷雾退回 ⇒ **E4 漏画/灰雾滞后** | ≡0 | **无等价档机判**；不得用 E5 证成「safe」 | **禁止作 v1.5.0 等价档** |
| M6 | **vanilla (2)** | 0 | **不装** | 同 M5 | ≡0 | 同 M5 | **禁止**（见 [4]） |

### 矩阵硬规则

| 规则 | 内容 |
|---|---|
| R1 | OPT-1 **禁止**在 bForce==0 跳过；**禁止**无条件跳过；**禁止**「非 vanilla 就跳过」。门=引擎 force 字节（Pass2 `[esp+0x58]`、Pass8 `[esp+0x68]`）。 |
| R2 | v1 装钩门 = `g_l4DirtyMode==0`。M3–M6 两计数恒 ≡0 是**预期**，不是故障。 |
| R3 | `Opt1DualSkip=0` 运行期回滚：`s_opt1DualSkipEnabled=0` ⇒ 两桩恒重放原流；字节级仍保留，卸载才写回原 5B。 |
| R4 | force-full 下 bForce 每帧为真，双算跳过恒命中；**去掉冗余不减像素**（后画本就覆盖）。 |
| R5 | 将来 vision-dirty 的 **force 帧**可扩展同钩（像素仍不变）；**非 force 帧永不跳**。 |
| R6 | **vanilla 不在任何「等价/安全」机判列**；详见 [4]。 |

---

## [3] 验收：E5 / TC-L4-01 / OPT-1 AC（R-L4-MERGE-AC）

### 3.1 E5（L4 静态镜头同帧像素对拍）— ZC-P4 红线

| # | 判据 | 级别 | 状态 |
|---|---|---|---|
| E5-1 | 静态镜头，`L4DirtyMode=force-full` vs `vision-dirty` 同帧像素差 **D≡0**（或帧 CRC 全等） | 红线 | [ ] |
| E5-2 | 同帧遥测 `l4RedrawSkippedStatic > 0`（须 P2 修好后才可能与 E5-1 同时成立） | 红线 | [ ] |
| E5-3 | 对象运动无旧位残影（bFlag=1 机动路径，`0x4DF639→0x5F4EC0→0x5F5146→0x6D2790`） | 红线 | [ ] |
| E5-4 | `L4DirtyMode=force-full` 启动日志/遥测与现网件一致（`l4RedrawSkippedStatic≡0`） | 必须 | [ ] |

> **注意**：P1 未修时 vision-dirty 静态也恒全刷且计数虚增 ⇒ E5-1 与 E5-2 **永远无法同时成立**（l4_dirty_residual_check §P0-2）。故 E5 实跑排在 P1+P2 之后。

### 3.2 TC-L4-01（迷雾退回 0 帧延迟）— 红线

| # | 判据 | 级别 | 状态 |
|---|---|---|---|
| T1 | 坦克前压开图后原路后撤，**主视角完全静止** | 场景 | [ ] |
| T2 | 离开直视圈的**下一逻辑帧**迷雾立即退回，延迟 **恒 0 帧** | 红线 | [ ] |
| T3 | vision-dirty 由「视口迁移>0 或渐变活跃 ⇒ 强制全刷」通过（2447-2450 联检） | 红线 | [ ] |
| T4 | OPT-1 on/off 下 TC-L4-01 表现一致（force-full 默认档本就全刷，应 0 帧） | 必须 | [ ] |
| T5 | **vanilla 档不得以「通过 T2」放行**：E4 退回格不进脏表也不进全刷 ⇒ 必挂 | 禁令 | [ ] |

### 3.3 OPT-1 像素对拍（R-OPT1-AC / E5 同路径工具）

| # | 判据 | 级别 | 状态 |
|---|---|---|---|
| AC1 | 同路径双跑：force-full，`Opt1DualSkip=0` vs `=1`，同地图同操作序列 **N≥120 帧**，主视图逐帧像素差 **D≡0** | 红线 | [ ] |
| AC2 | 含 **bFlag=1 机动打脏** + **Pass8 有脏** 帧时 `Pass2DirtySkip`/`Pass8Stage2Skip` **>0**，且 AC1 仍成立 | 红线 | [ ] |
| AC3 | **E4 雾退回镜头**：开图后单位撤离，静止视角 **0 帧**灰滞后；OPT-1 on/off 一致 | 红线 | [ ] |
| AC4 | **kill 回归**：`Opt1DualSkip=0` 启动日志/遥测与现网 force-full 一致（两计数≡0） | 必须 | [ ] |
| AC5 | 滚屏 strip、建筑损伤、动画/粒子/炮弹、小地图：无残影、无半幅 | 必须 | [ ] |
| AC6 | 卸载还原后 `0x6D378E`/`0x6D3988` = `A1 88 CE B0 00`；`0x6D3D99` = `0F 8D 98 00 00 00` | 必须 | [ ] |

**建议操作序列**（AC 与 E5 共用）：静止待机 → 单位移动（bFlag=1）→ 建筑开火/受击 → 开/合迷雾 → 大幅滚屏 → 小地图点击。  
**对拍工具**：复用 `out/re_work/re_sprint/R_rect_deep` / E5 既有帧 CRC 流程。

### 3.4 遥测机判（合并态）

| 模式 | 机判 |
|---|---|
| M1 force-full+on | 含脏帧两 opt1 计数可 >0；像素 D≡0；`l4RedrawSkippedStatic≡0` |
| M2 force-full+kill | 两 opt1 计数≡0；行为=现网 |
| M3 vision-dirty（P1+P2 后） | 两 opt1 计数≡0（不装钩）；静态真跳时 `l4RedrawSkippedStatic>0` 且 E5 D≡0 |
| M5/M6 vanilla | 两 opt1 计数≡0；**不以计数/像素证成安全**；T2 预期失败 |

---

## [4] vanilla 禁止当等价档（强制条款）

| # | 条款 | 依据 |
|---|---|---|
| V1 | **vanilla 不满足 v1.5.0 灰雾即时性**，**禁止**作为 safe 默认或「与现网等价」档放行。 | l4_dirty_residual_check §3；ZC-P5 |
| V2 | 根因：E4——迷雾/黑幕退回是**逐格底层状态、无对象标脏**；vanilla 恒还原原版 jge 后，静止镜头+雾退回既不进脏表也不进全刷 ⇒ **漏画/灰雾滞后**，直接违反 TC-L4-01（0 帧延迟）与 L4 视觉铁律。 | E4；TC-L4-01 |
| V3 | v1.5.0 无条件全刷**正是**为掩盖 E4；把 vanilla 当等价档 = 倒退回已知漏画洞。 | l4_dirty_residual_check §3 |
| V4 | 文档/注释/ini/机判四处同步明示：`51-54`、`ra2render.ini:202-212`、`843-845`；默认保持 `force-full`；新档位推荐 `vision-dirty` 而非 `vanilla`。 | ZC-P5 |
| V5 | vanilla **仅**适用于「另有退回打脏机制」或「书面接受灰雾即时性下降」的场景；**不得**写入验收等价表、**不得**用 E5/AC 数字为它背书。 | 本卡矩阵 M5/M6 |
| V6 | OPT-1 **禁止**接到 vanilla/非 force 路径（否则非 force 误跳 ⇒ E4 扩大 + 漏画瓦片/物体）。 | opt1 §2.2/§4 |
| V7 | 开档门槛三元组只认 **ZC-P1+P2+P4 → vision-dirty**；vanilla 不在门槛通过名单内。 | opt1 §3；zcode_patch_list 开档判定表 |

- [ ] V1–V7 已写入交付物（L-04）且验收表无 vanilla 等价行  

---

## [5] 回滚与卸载（合并态必查）

| # | 路径 | 动作 | 状态 |
|---|---|---|---|
| R-1 | 运行期 OPT-1 | `Opt1DualSkip=0` ⇒ 两桩恒重放原流 | [ ] |
| R-2 | 字节级 OPT-1 | `s_origPass2DirtyBytes`/`s_origPass8Stage2Bytes` 写回 `0x6D378E`/`0x6D3988` | [ ] |
| R-3 | 字节级 L4 | `0x6D3D99` 写回 `0F 8D 98 00 00 00`（F-13 既有） | [ ] |
| R-4 | DETACH | 卸载链**同时**含 `0x6D378E`/`0x6D3988`/`0x6D3D99`，禁止只还 L4 点 | [ ] |
| R-5 | 回归 | kill 后与「未开 OPT-1 现网 force-full」遥测/像素一致（AC4） | [ ] |

---

## [6] 写域合规

- **触碰**：`docs/re/landing_pack_l4_opt1_checklist.md`（本文）、`out/re_work/re_sprint/R_l4_merge/**`
- **未触碰**：`ra2render/**`、`gamemd.exe`、`ra2youli/**`、`tools/**`、台账、看板、ATLAS、`out/reverse/**`
- 本文为**合并编排/检查单**，不替代 ZCode 行号清单原文；实施细节以 `zcode_line_list.md` + `zcode_patch_list.md` 为准。

---

## [7] 合并门禁总表（签字用）

| 门 | 条件 | 阻断对象 | ☐ |
|---|---|---|---|
| G1 | OPT-1 门=仅 bForce；v1 仅 force-full 装钩 | OPT-1 合入 | [ ] |
| G2 | DETACH 三点齐还 | 任一合入 | [ ] |
| G3 | AC1+AC2+AC3 全绿 | OPT-1 合入 | [ ] |
| G4 | E5-1..4 + TC-L4-01 全绿 | vision-dirty 放行 | [ ] |
| G5 | ZC-P1+P2+P5 已合入 | vision-dirty 放行 | [ ] |
| G6 | vanilla 未出现在任何等价/safe 机判 | 发布 | [ ] |
| G7 | `Opt1DualSkip=0` 可一键回滚（R-1..5） | 发布 | [ ] |
