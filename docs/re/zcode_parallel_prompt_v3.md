# ZCode 并行总提示词 v3 · R-PROMPT-V3

> **任务号**：`R-PROMPT-V3` · **读者**：ZCode（真机/补丁安装唯一写者）+ 各轨子代理 + 验收方  
> **起草**：MiMo · **状态**：可直接粘贴派发  
> **版本**：**v3**（在 `zcode_master_implementation_ticket_v2.md` 批次骨架上，改为**四轨并行派发模型** + 10 张新落地卡完整队列 + 回执路径/红线/勘误锚点钉死）；**v1/v2 不改**，仍为历史基线  
> **证据基线**：`ra2youli/gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` · ImageBase `0x00400000` · `file_off = VA − 0x00400000`  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **写作用域**：本文 + `out/re_work/re_sprint/R_prompt_v3/**`（本编排工作区）  
> **禁写**：`ra2render/**`、`gamemd.exe` / `ra2youli/**`（安装动作由 ZCode 按卡执行）、`tools/**`、台账 `REVERSE_ENGINEERING_AND_PATCHES.md`、看板 `RE_COORDINATION.md`  
> **回报格式**：强制 `docs/re/AGENT_DELIVERY_FORMAT.md` §A 十节骨架  
> **派发节奏**：每完成一波就派出下一波并验收成果（见 §4 波次表）

**v3 队列依据（只读）**：`landing_pack_h20c_sweep.md` · `landing_pack_sw_radius_rc.md` · `landing_pack_weapons_lw.md` · `landing_pack_crt_l1.md` · `landing_pack_gap_p21_a3.md` · `landing_pack_gap_p223.md` · `landing_pack_vxl_prewarm.md` · `landing_pack_sw_charge.md` · `landing_pack_audio_throttle.md` · `landing_pack_particle.md` + `zcode_master_implementation_ticket_v2.md` + `errata_sync_master_table.md`

---

## 0. 一句话

用 **Track-R（串行 ra2render）/ Track-L（落地安装）/ Track-C（复算审计）/ Track-S（回执勘误）** 四轨并行，把 **10 张新落地卡** 按 **W1 安全收尾 → W2 表现层 → W3 内存/伤害链 → W4 联机对拍** 四波推进；每波独立验收门、独立回执、独立回滚；**全局红线 G-R1..G-R7 只强不松**；勘误锚点 **R-E01..R-E10** 全程生效；MP 握手口径裁决前 **禁止宣称「MP 可发布」**。

---

## 1. 并行模型（四轨）

### 1.1 轨道定义

| 轨 | 名称 | 执行方 | 做什么 | 写作用域（唯一） | 串行/并行 |
|---|---|---|---|---|---|
| **Track-R** | **ra2render 代码轨** | ZCode 代码子代理（**单写者**） | `ra2render` Hook/跳板/开关/遥测实现与 DETACH | **仅** `ra2render/**`（经 Lead 授权时）；否则只交规格 | **强制串行**（同一时刻只允许一个写者改 `ra2render`；禁止并行改同一文件） |
| **Track-L** | **落地安装轨** | ZCode 真机子代理 | 按 landing_pack 执行补丁安装/卸载/真机验收 | 各卡工作区 + `out/re_work/zcode_live/**` + `ra2youli/ra2render.ini`（开关） | **可并行**（互不依赖的卡）；同一 VA 点位安装仍串行 |
| **Track-C** | **复算审计轨** | 复算子代理（Antigravity / DSH / MiMo） | 字节复算、claims 核验、`verify_*.py`、门禁实跑 | `out/re_work/re_sprint/R_*_card/**`、`R_*_verify*` | **可并行**（与 R/L 同波次同时跑） |
| **Track-S** | **回执勘误轨** | 文档/汇总子代理 | 回执归档、勘误登记、波次验收汇总 | `out/re_work/re_sprint/R_prompt_v3/**`、`docs/re/zcode_parallel_prompt_v3.md`（本文） | **可并行**（每波收口时） |

### 1.2 轨间依赖（文字依赖图）

```
Track-C（复算） ──先出 MATCH──► Track-L（安装） ──装毕──► Track-S（回执）
                                      │
Track-R（代码） ◄──仅当需要改 ra2render 源码时介入──┘（单写者串行；落地卡以字节补丁为主，多数波次不触碰 R 轨）
```

- **字节补丁卡**（gap / vxl / sw_charge / crt_l1 / weapons_lw / audio / particle / h20c / sw_radius）：主路径 = C 复算 → L 安装 → S 回执；**不动 Track-R**。
- **需要改 `ra2render` 的实现**（三谓词合流、私有网格、遥测、开关解析）：走 Track-R，**串行排队**，一卡一提交；提交前该文件无其他写者。
- **撞写规则**：后到者停手，改投自己的工作区或请 Lead 裁决（同 `TRACK_BOUNDARY_MIMO_RE.md` §4）。

### 1.3 派发节奏（用户原话落地）

> 「继续派出多路子代理进行任务，每完成一波就继续派出新的一波并验收成果」

1. **一波 = 一张或一组互不依赖的卡**（见 §4 波次表）。
2. 波内可 **多路子代理并行**（C 轨复算可 2–4 路；L 轨安装按 VA 点位分路）。
3. **波次验收门**：该波全部回执按 §A 骨架交齐 + 门禁实跑 + 回滚实测 + Track-S 汇总 PASS → 才派下一波。
4. 波内失败：该卡打回重做，**不阻塞**同波其它独立卡；跨卡依赖失败则整波顺延。

---

## 2. 完整任务队列（10 张新卡 + 编排项）

### 2.1 卡片总表

| 波 | 轨 | 卡号 | 源文档（landing_pack） | 落地面 / VA | 优先级 | DESYNC | 回执路径 |
|---|---|---|---|---|---|---|---|
| **W1** | L+C | `ZC-GAP-P21-A3` | `landing_pack_gap_p21_a3.md` | **不改字节**；行为验收 A3/A4/A5（方案 C-战役 首选 / H-诊断钩 备选） | **P0 收尾** | gap 面（`Cell+0x134`） | `out/re_work/re_sprint/R_p21_a3/**` + `out/re_work/zcode_live/gap_p21_a3/` |
| **W1** | L+C | `ZC-GAP-P223` | `landing_pack_gap_p223.md` | P-2.2 `0x577EC5` / P-2.3 `0x577B60` 各 **6×NOP** | P1 | 同上 **VIOLATION** 混端 | `out/re_work/re_sprint/R_gap_p223/**` |
| **W1** | L+C | `ZC-VXL-PRE` | `landing_pack_vxl_prewarm.md` | L-VXL-1 imm8 `0x0A→0x40` @ `0x706D78`（**5==5**） | P1 | **SAFE**（D-VXL13） | `out/re_work/re_sprint/R_vxl_card/**` |
| **W2** | L+C+R | `ZC-H20C-SWEEP` | `landing_pack_h20c_sweep.md` | SW-1b T-b `0x6CB920`/`0x6CC390` **5B**（推荐）或 SW-1a T-a `0x6CD7C4` **必须 7B** + 私有网格 + 三谓词合流 | **P0** | **SAFE**（纯表现；0 Cell / 0 RNG / 0 CRC） | `out/re_work/re_sprint/R_h20c_card/**` |
| **W2** | L+C | `ZC-SW-RADIUS-RC` | `landing_pack_sw_radius_rc.md` | L-SWR-RC **零 .text**；`s_radarSweepRadiusCells_eff` + `SW+0xF8` UI 对齐 | **P0** | **SAFE** | `out/re_work/re_sprint/R_swr_card/**` |
| **W2** | L+C | `ZC-AUDIO-THROT` | `landing_pack_audio_throttle.md` | AT-A `0x750920`(6B) / AT-B `0x7509E0`(5B) / AT-C `0x750E20`(5B) trampoline | P1 | **SAFE**（D-AUDIO） | `out/re_work/re_sprint/R_audio_card/**` |
| **W2** | L+C | `ZC-PART-FOG` | `landing_pack_particle.md` | 槽 69 两虚表 DWORD（LE `C0 CE 62 00` / `80 E2 62 00`） | P1 | **SAFE**（D-PART；禁改逻辑字段） | `out/re_work/re_sprint/R_part_card/**` |
| **W3** | L+C | `ZC-CRT-L1` | `landing_pack_crt_l1.md` | CLR-DVC `0x4E9A10` / CLR-BASE `0x4E97B0` / RSV-GT `0x6F8F8A`（各 6B 跳板） | **P0** | **RISK**（启动期锁；禁热切） | `out/re_work/re_sprint/R_crt_card/**` |
| **W3** | L+C | `ZC-WPN-LW` | `landing_pack_weapons_lw.md` | L-W1 四点等长 `E8 rel32`（`0x4894AB/0x48975D/0x489AE4/0x489B33`）+ L-W2 `0x701900` + L-W3 `0x48923D` | P1 | L-W1 **安全（保序 0 PRNG）**；L-W2/3 纯读 | `out/re_work/re_sprint/R_wpn_card/**` |
| **W4** | L+C | `ZC-SW-CHARGE` L-SW-1 | `landing_pack_sw_charge.md` §1 | `0x6CBE88` **7×NOP**（冗余二次 call） | P2 | **SAFE**（字节级语义等价） | `out/re_work/re_sprint/R_sw_card/**` |
| **W4** | L+C | `ZC-SW-CHARGE` L-SW-2 *可选* | `landing_pack_sw_charge.md` §6 | `0x6A99AC` 5==5 `8B 41 78 90 90` | P2 可选 | **SAFE**（纯 UI；Q2 不过则放弃） | 同上 |
| **全波** | S | `R-PROMPT-V3` 编排 | 本文 | 波次汇总 / 勘误登记 / 回执归档 | P0 编排 | — | `out/re_work/re_sprint/R_prompt_v3/**` |

### 2.2 开关总表（默认全 0 = 字节零变化）

| 键 | 归属卡 | 默认 | 锁定 |
|---|---|---|---|
| `[FogOfWar] EnableGapProtection` | GAP-P21 / P223 | 0 | init 一次锁定，禁热重载 |
| `[Render] EnableVxlCachePrewarm` | VXL-PRE | 0 | 同上 |
| `[FogOfWar] EnableRadarSweepWindow` | H20C-SWEEP | 0 | 进程级 |
| `[FogOfWar] EnableSpySatRadarSweep` | H20C 前置闸 | 0 | =0 时 SW-1/私有窗均不装 |
| `RadarSweepDurationFrames` | H20C | 600（钳 60..3600） | LoadConfig 定型 |
| `RadarSweepRadiusCells` | SW-RADIUS-RC | 16（R-c 钳 1..64 / 产品 4..64） | 语义复活至 `s_radarSweepRadiusCells_eff` |
| `[AudioThrottle] Enable` | AUDIO-THROT | 0 | + MaxVoicePerFrame=6 / VoiceDedupMs=80 / MaxSamePerWindow=2 / WhitelistPriorityMin=3 / ThrottlePlayIndexAtPos=1 |
| `[FogOfWar] EnableParticleFog` | PART-FOG | 0 | 进程级 |
| `[MemoryPool] EnableMemoryPool` | CRT-L1 总闸 | 0 | **启动期锁定禁热切** |
> 【W3 勘误 · W3-A6/ISSUE-SECTION-MEMORYPOOL】[W3-Lead临时裁决] 改前：[MemoryPool] EnableMemoryPool；改后：[System] ; DC-01 裁决口径: 使用既有 [System] 节，零新增节 EnableMemoryPool=0；依据：docs/re/dispatch/W3_20261001_Lead_DECISION_AND_BOARD.md:40; docs/re/pending_execution_master_table.md:410-412；分级：P0
| `VectorReuse` / `VectorReserve` | CRT-L1 | 0 / 0 | 随总闸 |
| `[Logic] EnableDamageGroupPool` | WPN-L1 | 0 | — |
| `[Telemetry] EnableDamageTelemetry` / `EnableVersesAudit` | WPN-L2/L3 | 0 / 0 | — |
| `EnableSWChargeOpt` | SW-CHARGE L-SW-1 | 0 | =1 才装 |
| `EnableSWCameoCache` | SW-CHARGE L-SW-2 | 0 | Q2 门槛 |

### 2.3 附带不装（本票明确排除）

L-VXL-2/3 影跳过、降采样光核、path cache oracle、SpySat TYPE/S2/S3 旁路补装、任何新 MP 握手字段、H-20-C 的 R-a+ 解夹紧、`GetCameoChargeState` 公式/常数/clamp 变更、死代码 `0x4F9370` 清理、L2 池（`CRT::_new/_delete` 钩、`MemPoolClass34`）、`VectorGeometric`、地形特效四处 op_new 池化。

---

## 3. 红线与勘误锚点

### 3.1 全局红线 G-R1..G-R7（只强不松 · v3 重申）

| # | 红线 | 内容 | 触发后果 |
|---|---|---|---|
| **G-R1** | **MP 握手冲突待裁** | `gap_merge_checklist.md` §7.1 甲/乙未裁。**裁决前不得单方面改协议或宣称 G4.1 已满足**。v3 全部新卡 **一律不新增握手字段** | 未裁即宣称 MP 就绪 = **违规** |
| **G-R2** | **混端 DESYNC** | gap 三点改 `Cell+0x134` = **VIOLATION**；particle/audio/vxl/L4/H-20-C(纯 R-c)/SW-CHARGE = **SAFE**。**严禁混端**。唯一例外：N11「诊断镜像 vs 原版」且四键全 0 | 混端联机必炸 |
| **G-R3** | **禁改 GetTotalDamage 乘序** | `0x489180` 链与 `ReceiveDamage 0x701939` `fdivr` 链零改动；`GetCameoChargeState 0x6CBEE0` / `54.0` / clamp 同级禁改 | 联机必炸 |
| **G-R4** | **同步 PRNG 零容忍** | P16–P27 禁跳过/改序/合并；只许拦 Draw / 临时加可见。H-20-C 禁新增 `ScenarioClass::Random*`；禁写 `Cell+0x12C/0x130/0x134/0x140` | 跳过消费 = 联机必炸 |
| **G-R5** | **禁止宣称 MP 可发布** | G-R1 裁决前任何回执/文档/日志不得出现「MP 可发布 / G4.1 已满足 / 联机安全可出厂」 | 交付不合格 |
| **G-R6** | **门禁与证据纪律** | G0.x 全 PASS 才写；首字节非预期 = 停手上报；「没崩」≠ 成功；禁伪造实测；禁热切安装态开关。**锚点**：H-20-C T-a **必须 7B**（旧文 5B 为勘误 R-E03）；SW-CHARGE G0.1–G0.8；L-SW-2 **Q2 不过则放弃** | 违者回退重做 |
| **G-R7** | **回滚可逆** | 每卡留原字节备份并实测回滚；gap 逆序拆点；DETACH 覆盖全部写点。H-20-C 卸载 SW-1 **先于** `RemoveRadarFogHooks` | 回滚不可用 = 不闭环 |

### 3.2 勘误锚点 R-E01..R-E10（来自 `errata_sync_master_table.md`，全程生效）

| ID | 锚点（禁用旧文） | 新文（唯一正确） | 波及卡 |
|---|---|---|---|
| **R-E01** | `0x568297` | 实际 VA **`0x0056829A`**（P-2.1 关联描述） | GAP-P21-A3 引用 |
| **R-E02** | 上下文窗「21B」 | 指令对齐合计 **17B**（2+6+2+7） | GAP 系 |
| **R-E03** | T-a 「5B」 | `0x6CD7C4` 为 **7B** `mov al,[esp+0x1EC]`；T-a 必须 `E9`+2×`90` | **H20C-SWEEP** |
| **R-E04** | `SW+0xF8` 可改开图半径 | **死写**；唯一活消费 = 瞄准圈 `fld [edi+0xF8]@0x6DC1C8`；真实开图半径 = `Rules+0xFEC` 被 `min(10)` 夹紧 | **SW-RADIUS-RC** |
| **R-E05** | `fx_draw_chain:91` 过滤对象 | **写反**：`0x6D9920` 滤 Building(6)；`0x6D97D0` 滤 Terrain(0x24) | 表现层引用 |
> 【W3 勘误 · W3-A6/ISSUE-FX-FILTER-REVERSED】改前：0x6D9920` 滤 Building(6)；`0x6D97D0` 滤 Terrain(0x24；改后：0x6D9920 滤 Building(6)；0x6D97D0 滤 Terrain(0x24)；依据：ra2youli/gamemd.exe:0x2D997C, 0x2D982A; errata_sync_master_table.md:20 (R-E05)；分级：P1
| **R-E06** | `_delete` 调用 4498 处 | 真值 **≥4499**（第 4499 = `0x74836A`）；引用须标口径 | CRT-L1 / WPN |
| **R-E07** | Verses 施加「8 处」 | **9 处**（V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c） | **WPN-LW** |
> 【W3 勘误 · W3-A6/ISSUE-VERSES-SITES-COUNT】改前：Verses 施加「8 处；改后：Verses FPU 索引访存共 9 处 (V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c)；依据：errata_sync_master_table.md:22 (R-E07); warhead_verses_residual_p2.md:18, 58；分级：P1
| **R-E08** | 槽 69 DWORD 书写 `00 62 CE C0`（BE） | **LE** `C0 CE 62 00` / `80 E2 62 00`（BE 照抄会崩） | **PART-FOG** |
> 【W3 勘误 · W3-A6/ISSUE-PARTICLE-BE-BYTES】改前：00 62 CE C0；改后：C0 CE 62 00 / 80 E2 62 00 (小端 LE)；依据：errata_sync_master_table.md:23 (R-E08); FIXPACK_F01-F13_report.md F-04；分级：P0
| **R-E09** | `OccuredEvents` 位序 | `bit i` = 事件链第 i 个 Event；**禁重排 `[Events]`** | 联机/触发器 |
| **R-E10** | H-D5 `83 E0 FF` | **`0F B6 C0`**（`movzx eax,al`）；`83 /4 ib` 是 no-op | net_fix 引用 |

> 装卡时若 landing_pack 冻结源仍写旧文：**以本表新文为准**，并在回执 `[3] 勘误` 节登记「源文档未加注」；**禁止就地改冻结源**。

---

## 4. 波次执行卡（可直接派发）

### W1 · 安全收尾（gap A3 + P223 + VXL）

| 项 | 内容 |
|---|---|
| **卡** | `ZC-GAP-P21-A3` ∥ `ZC-GAP-P223` ∥ `ZC-VXL-PRE`（三卡互不依赖，**回执分开**） |
| **轨** | C 复算三路并行 → L 安装（P21-A3 不装字节；P223 两点；VXL 一点）→ S 汇总 |
| **顺序** | ① C 轨：`verify_p223_bytes.py` / `vxl_cache_bytes_report` 复跑 MATCH → ② L 轨：P-2.2 `0x577EC5` → P-2.3 `0x577B60` → `installed` 回写（期望 3）→ VXL `0x706D78` 独立装（回执分开）→ ③ P21-A3 跑方案 C（战役图 `ECHGAP.MAP` + PsychicReveal/TA17）或方案 H（需审批）→ ④ `ZB1-M01` 挂载验收 |
| **字节契约** | P223 各 **6==6** `90×6`；VXL **5==5** 仅 imm8 `0x0A→0x40`。禁 trampoline、禁改 growstep `0x706D7F`、禁动 `0x577B60/0x577EC5` 邻接非目标写 |
| **验收门** | P21-A3：**缝仍在 + `Cell+0x134` 不清 0** + A4 存读档缝态保持 + A5 DestroyGap 回落 + `except.txt` 空。P223：字节窗 MATCH + SpySat 开/关缝不废。VXL：两局 except 空 + `Growths/QsortCalls` 下降方向 |
| **MP 姿态** | gap：`MpActive` 强制不装；全端同构建同键同 `installed`。VXL：可装（SAFE） |
| **回滚** | P223 逆序 `P-2.3→P-2.2` 还原 `s_origP22/P23[6]`；VXL `s_origLVxl1[5]=BB 0A 00 00 00` |
| **窗口** | 2–3 执行日 / 2 验收窗 [推演] |

### W2 · 表现层（H20C + SW-RADIUS-RC + audio + particle）

| 项 | 内容 |
|---|---|
| **卡** | `ZC-H20C-SWEEP`（P0）∥ `ZC-SW-RADIUS-RC`（依赖 H20C 私有字段）∥ `ZC-AUDIO-THROT` ∥ `ZC-PART-FOG` |
| **轨** | H20C 需 **Track-R**（三谓词合流/私有网格写入 `ra2render`，**串行**）；其余 C+L 并行 |
| **顺序** | ① audio 三钩 A→B→C → ② particle 两槽 69（**不碰**已装五槽）→ ③ **H20C**：LoadConfig 两新键 → 私有网格/谓词/开窗 → SW-1（**推荐 T-b 5B**；禁共享尾声 `0x6CDE36` 开窗）→ 三处合流（`:1689/:1766/:1812/:1888` → `:2736/:2811` → `:1649-1664`）→ 过期强刷 → ④ **SW-RADIUS-RC**：`s_radarSweepRadiusCells_eff = clamp(RadarSweepRadiusCells,1,64)` + `SW+0xF8` 同值 float **仅瞄准圈** + R-b 死键日志勘误 |
| **字节契约** | audio：覆盖为 `E9 rel32`，失败出口 `xor eax,eax; ret 8/4`（禁裸 ret / 禁 `or eax,-1`）；**禁钩** EVA `0x752700`、**零接触** `0x64DE3F`。particle：只拦 Draw 槽 69；回滚写回 **LE**（R-E08）。H20C：T-a **必须 7B**（R-E03）或 T-b 5B；禁触碰路线 A 三钩 `0x655D38/0x655D87/0x65719A`；私有网格/半径/时长 **不进帧 CRC / 不进 .SAV / 不进 Checksum v[13]**。SW-RADIUS-RC：**零 .text** |
| **验收门** | audio：默认零行为差 + Enable=1 洪泛削峰 + 白名单 EVA/UI 仍出声。particle：雾中粒子不绘制 + 生成侧 PRNG 照常消费 + 两局 except 空。H20C **A1–A10**：死键回归 / 窗口过期 T+0·T+300·T+700 / **gap 保全裂缝仍在** / 三谓词合流 / 过期强刷 / 路线 A 回归 / 回滚字节 MATCH / 遥测三计数线性递增 **严禁恒 0** / 混联 3 局无 desync / `verify_h20c_bytes.py` **14 MATCH / 0 MISMATCH**。SW-RADIUS-RC **A1–A5**：瞄准圈直径 vs 实际扫窗直径；`EnableRadarSweepWindow=0` 时日志不得报「探测半径生效」 |
| **MP 姿态** | 四卡均 **SAFE**；混端可共存（观感不一致不构成 VIOLATION）。不新增握手键。若同开 `EnableSpySatRadarSweep` 则必须全端同 DLL+ini |
| **回滚** | audio：`Enable=0` + 还原三钩；particle：`EnableParticleFog=0` + 恢复原虚表 DWORD；H20C：`EnableRadarSweepWindow` 1→0 ⇒ `memset` 网格 + 还原 SW-1（**先于** `RemoveRadarFogHooks`）；SW-RADIUS-RC：键回落仅瞄准圈 |
| **窗口** | 5–8 执行日 / 3–5 验收窗 [推演]（H20C A1–A10 最重） |

### W3 · 内存 / 伤害链（CRT-L1 + WPN-LW）

| 项 | 内容 |
|---|---|
| **卡** | `ZC-CRT-L1`（P0）→ `ZC-WPN-LW`（L1→L2→L3 串序） |
| **轨** | C 复算 + L 安装；CRT 跳板与 WPN 池**不共享写点**，可同波不同日 |
| **顺序** | ① 仅开 L1（`EnableMemoryPool=1` + `VectorReuse/VectorReserve`）→ ② WPN-L1 四点等长 `E8` 换池（保 push 序）→ ③ WPN-L2 入口 6B 遥测 → ④ WPN-L3 `0x48923D` 前纯读插桩 → ⑤ `ZB4-M01` 长跑 / `ZB4-M02` Q5 |
| **字节契约** | CRT-L1：三钩各 6B 跳板；A2 **禁止写 +0x10**（Base VC 仅 16B）；A1 必须补 `Count=0`；**禁碰 L2 入口** `0x7C8E17/0x7C8B3D`。WPN-L1：**只动 4 处** `0x4894AB/0x48975D/0x489AE4/0x489B33`；**严禁混入**地形特效四处 `0x48A323/0x48A3B1/0x48A3F2/0x48A449` 及 cleanup `0x48A4A4/0x48A4D0`；池容量 256、溢出退堆、**保序 0 PRNG**。WPN-L3：只读断言，**fmul 乘序零改动**（G-R3） |
| **验收门** | CRT-L1：寻敌 Clear/Add 震荡下降方向 + 两局 except 空 + A2 不踩邻接。WPN-L1：高密度弹幕两局 except 空 + PRNG 序不变。L-W2/3：计数非零、乘序哈希稳定。**禁百分比收益承诺**。`ZB4-M01`：M01/M02 只报下降方向 / M07 零挂死 / M09 耗尽穿堆 / M10 Private Bytes 220–280MB 无线性泄漏 |
| **MP 姿态** | CRT-L1 可开（禁热切）；L2/实体桶联机强制关；WPN-L1 建议单机先行。全部不进握手字段 |
| **回滚** | CRT-L1：总闸=0（两入口不装钩）+ 还原三跳板；WPN-L1：还原 4×5B；L-W2/L-W3 还原序言/插桩 |
| **窗口** | 4–7 执行日 / 3–4 验收窗 + ZB4 ≈1.7h [推演] |

### W4 · 可选微优化（SW-CHARGE）

| 项 | 内容 |
|---|---|
| **卡** | `ZC-SW-CHARGE` L-SW-1（主项）∥ L-SW-2（可选，Q2 门槛） |
| **顺序** | G0.1–G0.8 全 PASS → L-SW-1 `0x6CBE88` 7×NOP → A1–A5；L-SW-2 仅当 Q2.1/Q2.2 真机 `frame=-1` 容错通过 |
| **字节契约** | L-SW-1：**只许删冗余二次 call**（`8B CE E8 51 00 00 00` → `90×7`）；**必须保留** `0x6CBE8F` 写回与 `0x6CBE7E` 首次 call；禁改 `GetCameoChargeState` 公式/`54.0`/clamp、`RechargeTimer`/`IsCharged` 翻转帧、`ChargeDrainState` FSM；禁跳帧节流 `HasChargeProgressed`。L-SW-2：5==5 `8B 41 78 90 90` |
| **验收门** | L-SW-1 A1–A5：**A3 充能到点帧号与基线一致**（禁「没崩当成功」）+ A5 双端 CRC + Checksum v[13] 一致。L-SW-2 B1–B4（仅 Q2 过后） |
| **MP 姿态** | L-SW-1 **SAFE**（字节级语义等价，`MpActive` 不强制关） |
| **回滚** | 软 `EnableSWChargeOpt=0`+重启；硬还原 `s_origLSW1[7]=8B CE E8 51 00 00 00` |
| **窗口** | 0.5–1 执行日 [推演] |

---

## 5. 统一交付回执（每卡一份，按 `AGENT_DELIVERY_FORMAT` §A）

```text
[META]
task=<卡号>  executor=<执行方/会话ID>  elapsed=<秒>  mode=<read-only|accept-edits>
scope_declared=<提示词给定的写作用域>

[0] 结论摘要（≤5 行）
[1] 逐条必答项结论表（证据等级三档 + 文件:行/VA 锚点）
[2] 关键证据块（VA / FileOffset / 原始字节 / 反汇编 / xref）+ claims.txt
[3] 勘误（含 R-E01..R-E10 命中情况；无勘误须显式写「无勘误」）
[4] 未闭环清单
[5] 写作用域合规声明（改动清单 + 未触碰清单 + 目标二进制哈希）
[6] 门禁实跑输出（verify_anchors.py / audit_bytes.py / 卡内 verify_*.py 原文粘贴）
[7] 风险与红线提示（同步语义 / RNG 序 / 存档结构 / 像素等价性 四问）
[8] 交付物清单
[9] 待裁决项
```

**波次汇总（Track-S 每波一份，落 `out/re_work/re_sprint/R_prompt_v3/wave_W<N>_result.md`）**：

```text
R-PROMPT-V3 WAVE RESULT · W<N>
- cards: (ZC-… list)
- tracks: R/L/C/S 各自完成项
- switches set: (key=value …)
- install order + G0 gates: PASS/FAIL
- acceptance: (each case PASS/FAIL + evidence path)
- rollback tested: y/n + method
- except.txt: empty|path
- MP stance: (forced-off-mp | same-build-only | SAFE-keep | b5-verify-only)
- red-line touch: G-R1..G-R7 which, and mitigation
- errata hit: R-E01..R-E10 which, resolved y/n
- forbidden-claim check: 「未宣称 MP 可发布」 y/n
- next wave ready: y/n
```

---

## 6. 可直接粘贴的主提示词全文

> 以下为 **ZCode 并行总提示词 v3** 正文。派发时整段粘贴；子代理回执强制 §A 骨架。

```text
【ZCode 并行总提示词 v3 · R-PROMPT-V3】

仓库：D:\Project\ra2-campaign-forge
你是 ZCode 执行方（真机/补丁安装唯一写者）或多轨子代理。先读：
  docs/re/AGENT_DELIVERY_FORMAT.md（回执 §A 十节，强制）
  docs/re/zcode_parallel_prompt_v3.md（本文，队列/红线/勘误锚点）
  docs/re/zcode_master_implementation_ticket_v2.md（批次背景，只读）
  docs/re/errata_sync_master_table.md（R-E01..R-E10，全程生效）
  docs/re/TRACK_BOUNDARY_MIMO_RE.md（写作用域冲突规则）

■ 0. 证据基线（引用时原样复制）
gamemd.exe 1.001 · SHA-256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476
MD5 4f37486e5b0dbe2ae5f45aeee0f98367 · ImageBase 0x00400000 · file_off = VA − 0x00400000
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]

■ 1. 写作用域
可写：out/re_work/re_sprint/R_prompt_v3/**（编排）+ 本卡指定工作区 + 各卡 landing_pack 声明的范围
禁写：ra2render/**（Track-R 单写者除外且须串行）、gamemd.exe/ra2youli/**（安装动作按卡执行）、
      tools/**、台账 REVERSE_ENGINEERING_AND_PATCHES.md、看板 RE_COORDINATION.md、他人 docs
撞写：后到者停手，改投自己工作区或上报 Lead。

■ 2. 并行模型（四轨）
Track-R  ra2render 代码轨 —— 单写者、强制串行；一卡一提交；提交前确认无其他写者。
Track-L  落地安装轨 —— 按 landing_pack 安装/卸载/真机验收；互不依赖的卡可并行；同一 VA 点位串行。
Track-C  复算审计轨 —— 字节复算、claims 核验、verify_*.py、门禁实跑；与 R/L 同波并行。
Track-S  回执勘误轨 —— 回执归档、勘误登记、波次汇总；每波收口。
派发节奏：每完成一波就派出下一波并验收成果。波内多路并行；波次验收门全绿才放行下一波。

■ 3. 任务队列（按波执行；卡内细节以 landing_pack 为准）
W1  ZC-GAP-P21-A3  landing_pack_gap_p21_a3.md   行为验收 A3/A4/A5（方案 C-战役首选）  回执→R_p21_a3/
    ZC-GAP-P223   landing_pack_gap_p223.md    P-2.2 0x577EC5 / P-2.3 0x577B60 各 6×NOP  回执→R_gap_p223/
    ZC-VXL-PRE    landing_pack_vxl_prewarm.md L-VXL-1 0x706D78 imm8 0x0A→0x40 (5==5)     回执→R_vxl_card/
W2  ZC-H20C-SWEEP landing_pack_h20c_sweep.md  SW-1b T-b 5B（推荐）或 SW-1a T-a 必须 7B
                                              + 私有网格 + 三谓词合流 + R-c 半径          回执→R_h20c_card/
    ZC-SW-RADIUS-RC landing_pack_sw_radius_rc.md L-SWR-RC 零 .text；s_radarSweepRadiusCells_eff
                                              + SW+0xF8 仅瞄准圈对齐                      回执→R_swr_card/
    ZC-AUDIO-THROT landing_pack_audio_throttle.md AT-A 0x750920 / AT-B 0x7509E0 / AT-C 0x750E20  回执→R_audio_card/
    ZC-PART-FOG   landing_pack_particle.md    槽 69 虚表 DWORD（LE C0 CE 62 00 / 80 E2 62 00）  回执→R_part_card/
W3  ZC-CRT-L1     landing_pack_crt_l1.md      CLR-DVC 0x4E9A10 / CLR-BASE 0x4E97B0 / RSV-GT 0x6F8F8A  回执→R_crt_card/
    ZC-WPN-LW     landing_pack_weapons_lw.md  L-W1 四点 0x4894AB/0x48975D/0x489AE4/0x489B33
                                              + L-W2 0x701900 + L-W3 0x48923D               回执→R_wpn_card/
W4  ZC-SW-CHARGE  landing_pack_sw_charge.md   L-SW-1 0x6CBE88 7×NOP（主项）
                                              L-SW-2 0x6A99AC 5==5（可选，Q2 不过则放弃）    回执→R_sw_card/
全波 Track-S 波次汇总 → out/re_work/re_sprint/R_prompt_v3/wave_W<N>_result.md

■ 4. 字节契约（违反即回退）
- gap P223：各 6==6 90×6；禁 trampoline；禁动邻接非目标写。
- VXL：5==5 仅 imm8；禁动 growstep 0x706D7F。
- H20C：T-a 必须 7B（E9+2×90）或 T-b 5B；禁共享尾声 0x6CDE36 开窗；禁触碰路线 A 三钩
  0x655D38(9B)/0x655D87(7B)/0x65719A(5B)；私有网格/半径/时长不进帧 CRC/.SAV/Checksum v[13]。
- audio：E9 rel32 trampoline；失败出口 xor eax,eax; ret 8/4；禁钩 EVA 0x752700；零接触 0x64DE3F。
- particle：只拦 Draw 槽 69；禁写 Update/AI/寿命/坐标/Owner；回滚值用 LE（禁 BE 照抄）。
- CRT-L1：A2 禁止写 +0x10；A1 必须补 Count=0；禁碰 L2 入口 0x7C8E17/0x7C8B3D。
- WPN-L1：只动 4 处白名单；严禁混入地形特效 0x48A323/0x48A3B1/0x48A3F2/0x48A449；
  池 256 溢出退堆；保序 0 PRNG。L-W3 只读断言，fmul 乘序零改动。
- L-SW-1：只许删冗余二次 call（8B CE E8 51 00 00 00 → 90×7）；必须保留 0x6CBE8F 写回与
  0x6CBE7E 首次 call；禁改 GetCameoChargeState 公式/54.0/clamp/RechargeTimer/IsCharged/FSM。
- L-SW-2：5==5 8B 41 78 90 90；GetCameoChargeState 本体与写侧不动。

■ 5. 红线（G-R1..G-R7 只强不松）
G-R1 MP 握手甲/乙未裁：裁决前不得改协议、不得宣称 G4.1 已满足；本队列一律不新增握手字段。
G-R2 严禁混端；gap=VIOLATION；particle/audio/vxl/H20C(纯R-c)/SW-CHARGE=SAFE；
     唯一例外 N11「诊断镜像 vs 原版」且 EnableSpySatRadarSweep=EnableRadarSweepWindow=
     EnableGapProtection=EnableMinimapFog=0。
G-R3 禁改 GetTotalDamage 乘序 / ReceiveDamage fdivr 链 / GetCameoChargeState 公式与 54.0。
G-R4 同步 PRNG P16–P27 零容忍；只许拦 Draw/临时加可见；禁写 Cell+0x12C/0x130/0x134/0x140；
     禁新增 ScenarioClass::Random/RandomRanged。
G-R5 禁止在任何回执/文档/日志出现「MP 可发布 / G4.1 已满足 / 联机安全可出厂」。
G-R6 G0.x 全 PASS 才写；首字节非预期=停手上报（禁覆盖未知安装者）；「没崩」≠成功；
     禁伪造实测；禁热切安装态开关；A3 类硬证据（到点帧号/计数）必须有。
G-R7 每卡原字节备份 + 实测回滚；gap 逆序拆点；H20C 卸载 SW-1 先于 RemoveRadarFogHooks。

■ 6. 勘误锚点（以新文为准；禁用旧文）
R-E01 0x568297 → 0x0056829A
R-E02 上下文窗 21B → 指令对齐 17B（2+6+2+7）
R-E03 T-a 5B → 必须 7B（0x6CD7C4 = mov al,[esp+0x1EC]）
R-E04 SW+0xF8 死写；开图半径=Rules+0xFEC 被 min(10) 夹紧；SW+0xF8 仅瞄准圈
R-E05 0x6D9920 滤 Building(6)；0x6D97D0 滤 Terrain(0x24)（旧文写反）
R-E06 _delete 调用 ≥4499（第 4499=0x74836A）；引用标口径
R-E07 Verses 施加 9 处（非 8）
R-E08 槽 69 DWORD 用 LE：C0 CE 62 00 / 80 E2 62 00（禁 BE 照抄）
R-E09 OccuredEvents bit i = 事件链第 i 个 Event；禁重排 [Events]
R-E10 H-D5 用 0F B6 C0（movzx eax,al）；禁 83 E0 FF

■ 7. 开关纪律
默认全 0 = 字节零变化。安装态开关 init 一次锁定，禁热重载/热切换。
MpActive 下 gap 强制不装。联机强制仅 CRT-L1（禁 L2/实体桶）。
L-SW-2 仅当 Q2.1/Q2.2 真机 frame=-1 容错通过，否则整体放弃。

■ 8. 回执（缺节即不合格）
按 docs/re/AGENT_DELIVERY_FORMAT.md §A 十节逐条填写；证据锚点必须给 文件:行 或 VA；
证据等级只用 [实证]/[推演]/[待实测]；门禁输出原文粘贴；勘误命中 R-E0x 须逐条登记。
波次收口由 Track-S 写 wave_W<N>_result.md（模板见 zcode_parallel_prompt_v3.md §5）。

■ 9. 验收红线（禁「没崩当成功」）
gap：缝仍在 + Cell+0x134 不清 0 + 存读档缝态保持 + except.txt 空。
H20C：A1–A10 全 PASS + verify_h20c_bytes.py 14 MATCH / 0 MISMATCH + 遥测计数线性递增严禁恒 0。
VXL/AUDIO/PART/CRT/WPN：两局 except 空 + 计数/方向可见 + 字节窗 MATCH。
L-SW-1：A3 充能到点帧号与基线一致。
性能只验收「字节装上 + 计数方向 + except 空」，禁百分比收益承诺。

■ 10. 不在本票
L-VXL-2/3、path cache、SpySat TYPE/S2/S3 补装、MP 握手字段扩展实现、H20C R-a+ 解夹紧、
GetCameoChargeState 重写、L2 池、VectorGeometric、地形特效池化、死代码清理、
台账/看板登记（Lead 收口）、任何性能百分比承诺。

—— 完 ——
```

---

## 7. 不在本票 / 与 v2 的关系

| 项 | 说明 |
|---|---|
| v1 / v2 文件 | **不改**，仍为历史基线；批次骨架（B1–B5）继续有效，v3 在其上做**派发模型与队列展开** |
| 新增 | 四轨并行模型 · 10 张新卡完整队列 · 回执路径钉死 · R-E01..R-E10 勘误锚点 · 波次 W1–W4 派发卡 · 可粘贴主提示词 |
| 窗口 | 沿 v2：并行压缩约 10–16 执行日 [推演]；以真机验收实际耗时为准 |
| MP 发布宣称 | 唯一门 = Lead 对 G-R1 握手口径裁决落地 + G4.1/G4.2 实装实测；**任何波次全绿都不构成发布宣称** |

---

*v3 依据：zcode_master_implementation_ticket_v2.md + 10 张 landing_pack 新卡 + errata_sync_master_table.md + TRACK_BOUNDARY_MIMO_RE.md 交叉汇总；红线只强不松；窗口为编排建议 [推演]，字节与开关均引自原卡 [实证]。*
