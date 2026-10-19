# ZCode 总实施票 v2 · R-ZC-MASTER

> **任务号**：`R-ZC-MASTER`（v2）· **读者**：ZCode（真机/补丁安装唯一写者）+ 验收方  
> **起草**：MiMo · R-TICKET-UPD · **状态**：待 Lead 派发  
> **版本**：**v2**（在 v1 九卡四批之上增补 H-20-C / ZC-SW-CHARGE / B5 联机卡 + MERGE50 挂载）；**v1 不改**，仍存 `zcode_master_implementation_ticket.md`  
> **证据基线**：`ra2youli/gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` · ImageBase `0x00400000` · `file_off = VA − 0x00400000`  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **写作用域**：本文 + `out/re_work/re_sprint/R_ticket_upd/**`（本票编排）+ 各卡既有工作区  
> **禁写**：`ra2render/**`、`gamemd.exe` / `ra2youli/**`（安装动作由 ZCode 按卡执行）、`tools/**`、台账、看板  
> **回报格式**：强制 `docs/re/AGENT_DELIVERY_FORMAT.md` §A 十节骨架

**v2 增补依据（只读）**：`h20c_private_sweep_spec.md` · `landing_pack_sw_charge.md` · `b_class_merge_zc_cards.md`（含 B5 新建与 MERGE50 挂载）

---

## 0. 一句话

把 **九份 v1 落地卡 + H-20-C 私有扫窗 + ZC-SW-CHARGE + MERGE50 挂载/新建 B5** 按 **B1 安全落地 → B2 表现层 → B3 L4/OPT-1 → B4 内存/伤害链 → B5 联机对拍与逻辑回归** 五批推进；每批独立验收门、独立回滚；**全局红线只强不松**；在 MP 握手口径裁决前 **禁止宣称「MP 可发布」**。

---

## 1. 卡片总清单（本票覆盖面）

| 批 | 卡号 / 清单 | 源文档 | 落地面 | 优先级 | DESYNC 判定 |
|---|---|---|---|---|---|
| **B1** | `ZC-GAP-P21` | `landing_pack_gap_p21.md` | P-2.1 6×NOP @ `0x568273` | **P0** | 混端 **VIOLATION**（`Cell+0x134`） |
| **B1** | `ZC-GAP-P223` | `landing_pack_gap_p223.md` | P-2.2/P-2.3 各 6×NOP | P1 | 同上 |
| **B1** | `R-GAP-MERGE` | `landing_pack_gap_merge_checklist.md` | 三点合并编排 + `installed==3` | P0 编排 | 同上 |
| **B1** | `ZC-VXL-PRE` | `landing_pack_vxl_prewarm.md` | L-VXL-1 imm8 `0x0A→0x40` @ `0x706D78` | P1 | **SAFE**（D-VXL13） |
| **B1** | `ZB1-M01` *挂载* | `b_class_merge_zc_cards.md` | gap/SpySat/裂缝玩法验收 4 条 | P1 验收 | 同 gap 面 |
| **B2** | `ZC-AUDIO-THROT` | `landing_pack_audio_throttle.md` | AT-A/B/C Play* 入口限频 | P1 | **SAFE**（D-AUDIO） |
| **B2** | `ZC-PART-FOG` | `landing_pack_particle.md` | 槽 69 粒子 Draw 剔除 | P1 | **SAFE**（D-PART；禁改逻辑字段） |
| **B2** | **`ZC-H20C`** *v2 增* | `h20c_private_sweep_spec.md` | 私有扫窗 SW-1 + 三谓词合流 + R-c 死键 | P1 表现层 | **SAFE**（纯表现；不写 Cell、不吃 RNG） |
| **B2** | `ZC-SW-CHARGE` **L-SW-2** *可选* | `landing_pack_sw_charge.md` §6 | Cameo 读 `+0x78` 缓存 5==5 | P2 可选 | **SAFE**（纯 UI；Q2 不过则放弃） |
| **B2** | `ZB2-M01..M04` *挂载* | `b_class_merge_zc_cards.md` | 音频/粒子验收 14 条 | P1 验收 | 同 B2 面 |
| **B3** | `R-L4-MERGE` | `landing_pack_l4_opt1_checklist.md` | L4 桩 + OPT-1 双钩 + ZC-P1..P5 | P1 | **SAFE**（D-L4） |
| **B3** | `ZC-SW-CHARGE` **L-SW-1** *v2 增* | `landing_pack_sw_charge.md` §1 | `0x6CBE88` 冗余二次 call 7×NOP | P2 | **SAFE**（字节级语义等价；零 CRC） |
| **B3** | `ZB3-M01..M03` *挂载* | `b_class_merge_zc_cards.md` | 渲染/雷达/SSE2 验收 12 条 | P1 验收 | 同 B3 面 |
| **B4** | `R-CRT-POOL` **L1** | `crt_pool_landing.md` §2.2 | 向量 Clear/Reserve/几何扩容 | P1 | **RISK**（启动期锁；禁热切） |
| **B4** | `R-L2-GAP` | `crt_l2_class34_fix_spec.md` | L2 class3/4 空洞（Layer A/B） | P1 | **RISK**（改 class4 生命周期须 A/B） |
| **B4** | `ZC-WPN-L1..3` | `weapons_damage_landing.md` | L-W1 池化 / L-W2 遥测 / L-W3 乘序锁 | P1 | L-W1 **安全（保序 0 PRNG）**；L-W2/3 纯读 |
| **B4** | `ZB4-M01..M02` *挂载* | `b_class_merge_zc_cards.md` | CRT 池长跑/卸载 7 条 | P1 验收 | 同 B4 面 |
| **B5** | **`ZB5-M01`** *v2 新建* | `b_class_merge_zc_cards.md` | 联机逐帧对拍 / 混联 L0（★N03/N10/N11） | **P0 联机** | 对拍面；N11 仅诊断镜像混联 |
| **B5** | **`ZB5-M02`** *v2 新建* | 同上 | 联机降级 / W 旁路 / 存档校验（★N12/N13/N17） | P0 联机 | 门控降级 + SAV 哈希 |
| **B5** | **`ZB5-M03`** *v2 新建* | 同上 | 寻路/占用/空间哈希（L01/L02/L05/L06） | P1 逻辑 | 纯逻辑回归 |
| **B5** | **`ZB5-M04`** *v2 新建* | 同上 | AI 触发/超武确定性/Timer 落盘（L07/L08/L14） | P1 逻辑 | 双端同帧确定性 |

> 附带不装（本票明确排除）：L-VXL-2/3 影跳过、降采样光核、path cache oracle、SpySat TYPE/S2/S3 旁路补装、任何新 MP 握手字段、H-20-C 的 R-a+ 解夹紧、`GetCameoChargeState` 公式/常数/clamp 变更、死代码 `0x4F9370` 清理。

---

## 2. 批次拆分与执行卡

### B1 · 安全落地（gap 三点 + VXL 预热）

| 项 | 内容 |
|---|---|
| **卡号** | `ZC-GAP-P21` → `ZC-GAP-P223`（同装）· 编排 `R-GAP-MERGE` · `ZC-VXL-PRE` · 挂载验收 `ZB1-M01` |
| **开关** | `[FogOfWar] EnableGapProtection`（默认 **0**）· `[Render] EnableVxlCachePrewarm`（默认 **0**）· 均 **init 一次锁定，禁热重载** |
| **顺序（强制）** | ① 门禁 G0.1–G0.7 全 PASS → ② P-2.1 `0x568273` → ③ P-2.2 `0x577EC5` → ④ P-2.3 `0x577B60` → ⑤ `gapProtectionPatchesInstalled` 回写（期望 **3**）→ ⑥ 真机 Q1 三点首字节复核 → ⑦ 独立装 `ZC-VXL-PRE` `0x706D78`（与 gap 无依赖，可并行但 **回执分开**）→ ⑧ 装毕跑 `ZB1-M01`（★L09/L10 优先） |
| **字节契约** | 三点各 **6==6** 等长 `90×6`；VXL **5==5** 等长仅 imm8 `0x0A→0x40`。禁 trampoline、禁 `89→8B`、禁改零常量寄存器、禁动 growstep `0x706D7F` |
| **验收门** | gap：A1 默认不装 / A2 装后字节窗 MATCH / **A3 裂缝遮挡仍在**（截图或计数，禁「没崩当成功」）/ A4 存读档缝态保持 + `except.txt` 空 / A5（可选）DestroyGap 计数回 0。VXL：A1–A2 同上 / A3 **连打两局** except 均空 / A4 遥测计数可见且 `Growths/QsortCalls` 相对键关局 **有下降方向**（无百分比承诺）。**ZB1-M01**：L09 小地图不整亮且 `House+0x577A` 不置 1；L10 扫描退去 100% 全黑且 `Cell+0x134≥1`；L15 变卖阻塞 100% 解除；R30 残影瞬时消失 |
| **MP 姿态** | gap：`MpActive` **强制不装**；全端同构建同 `EnableGapProtection` 同 `installed`（皆 3 或皆 0），**严禁混端**。VXL：可装（SAFE）；全端同键以便遥测同口径 |
| **回滚** | 软：键=0 + 重启。硬：`s_origP21/P22/P23[6]` 逆序 `P-2.3→P-2.2→P-2.1` 还原（或整组）；VXL `s_origLVxl1[5]=BB 0A 00 00 00` 还原。卸载工具 `--uninstall-gap-all` / `--uninstall-lvxl1` |
| **预计窗口** | **2–3 个执行日 / 2 个验收窗口 + ZB1-M01 60m**（安装 0.5 日 + 真机 A 系列 1–1.5 日 + 回执归档 0.5 日）[推演] |

### B2 · 表现层（audio / particle / **H-20-C 扫窗** / L-SW-2 可选）

| 项 | 内容 |
|---|---|
| **卡号** | `ZC-AUDIO-THROT`（AT-A `0x750920` / AT-B `0x7509E0` / AT-C `0x750E20`）· `ZC-PART-FOG`（槽 69 `0x7EFA68` / `0x7EFCB0`）· **`ZC-H20C`**（SW-1 T-b `0x6CB920`/`0x6CC390` 或 T-a **7B** `0x6CD7C4` + 私有网格 + 三谓词合流）· **L-SW-2**（可选 `0x6A99AC`）· 挂载 `ZB2-M01..M04` |
| **开关** | `[AudioThrottle] Enable=0`（默认）+ `MaxVoicePerFrame=6` / `VoiceDedupMs=80` / `MaxSamePerWindow=2` / `WhitelistPriorityMin=3` / `ThrottlePlayIndexAtPos=1` · `[FogOfWar] EnableParticleFog=0`（默认）· **`[FogOfWar] EnableRadarSweepWindow=0`（默认）** + `EnableSpySatRadarSweep` 前置闸 + `RadarSweepDurationFrames=600`（钳 60..3600）+ `RadarSweepRadiusCells=16`（R-c 私有半径，钳 4..64）· `EnableSWCameoCache=0`（默认；L-SW-2） |
| **顺序** | ① audio 三钩 trampoline（A→B→C，判定序严格按卡 §2.2）→ ② particle 两槽 69 虚表钩（**不碰**已装五槽）→ ③ **H-20-C**：LoadConfig 两新键 → 私有网格/谓词/开窗 → SW-1（**推荐 T-b** 5B 入口钩；禁在共享尾声 `0x6CDE36` 开窗）→ 三处合流（世界 `:1689/:1766/:1812/:1888` → 小地图 `:2736/:2811` → 过期环 `:1649-1664`）→ 过期/开窗置 `s_minimapForceRefresh=10` → R-c 必做 + R-b 死键文档化 → ④ （可选）L-SW-2 仅当 Q2.1/Q2.2 真机 `frame=-1` 容错通过。audio/particle/H-20-C **互不依赖可并行派工，回执分开** |
| **字节/结构契约** | audio：覆盖 6/5/5B 为 `E9 rel32`，失败出口必须 `xor eax,eax; ret 8/4`（禁裸 ret、禁 `or eax,-1`）；**禁钩** EVA `0x752700`、**零接触** `0x64DE3F`。particle：只拦 **Draw** 虚表槽 69，禁写 Update/AI/寿命/坐标/Owner。**H-20-C**：T-a **必须 7B**（`E9`+2×`90`，旧文 5B 为勘误）或 T-b 5B；**禁止**触碰路线 A 三钩 `0x655D38`(9B)/`0x655D87`(7B)/`0x65719A`(5B)；私有网格/半径/时长 **不进帧 CRC、不进 .SAV、不进 Checksum v[13]**；**禁止**写 `Cell+0x12C/0x130/0x134/0x140`；**禁止**新增 `ScenarioClass::Random/RandomRanged`；`everSeen` **优先于**扫窗。L-SW-2：**5==5** `8B 41 78 90 90`；`GetCameoChargeState` 本体与写侧不动 |
| **验收门** | audio：默认零行为差（A1）；Enable=1 后洪泛场景削峰、白名单 EVA/UI 仍出声、遥测计数可见、`except.txt` 空；两池（200 槽）压力下降方向可报。particle：雾中粒子不绘制、可见区正常、生成侧 PRNG **照常消费**（无 SYNC 异常）、两局 except 空。**H-20-C A1–A10**：死键回归 / 窗口过期 T+0·T+300·T+700 / **gap 保全裂缝仍在** / 三谓词合流 / 过期强刷 / 路线 A 回归 / 回滚字节 MATCH / 遥测三计数线性递增 **严禁恒 0** / 混联档 3 局无 desync / `verify_h20c_bytes.py` **14 MATCH / 0 MISMATCH**。L-SW-2：B1–B4（仅 Q2 过后）。挂载 `ZB2-M01..M04` 按原判据 |
| **MP 姿态** | audio/particle/H-20-C 纯 R-c / L-SW-2 均 **SAFE**（无帧 CRC 分叉）；混端可共存（观感可不一致，不构成 VIOLATION）。不新增握手键。**例外**：若同时开 `EnableSpySatRadarSweep`（Case11 原版永久开图语义）则必须全端同 DLL+ini；混联对方原版时 `EnableSpySatRadarSweep=EnableRadarSweepWindow=EnableGapProtection=EnableMinimapFog=0` 才安全 |
| **回滚** | audio：`Enable=0` 软关直通 + 卸载时还原原字节/释放跳板。particle：`EnableParticleFog=0` + 卸载时恢复原虚表 DWORD（`C0 CE 62 00` / `80 E2 62 00` LE）。**H-20-C**：`EnableRadarSweepWindow` 1→0 ⇒ `memset` 网格 + 还原 SW-1（`s_origCase11Bytes[7]` 或 `s_origClickFireBytes[5]`）；卸载 SW-1 **先于** `RemoveRadarFogHooks`；`Rules+0xFEC`（若 R-a）还原。L-SW-2：`EnableSWCameoCache=0` + 还原 `0x6A99AC` 5B |
| **预计窗口** | **5–8 个执行日 / 3–5 个验收窗口 + ZB2 挂载 ≈3.5h**（audio trampoline + 状态机 2–3 日；particle 1–2 日；**H-20-C 2–3 日**（含 A1–A10）；L-SW-2 可选 0–1 日）[推演] |

### B3 · L4 / OPT-1 + **L-SW-1**（`R-L4-MERGE` + `ZC-SW-CHARGE` 主项）

| 项 | 内容 |
|---|---|
| **卡号** | OPT-1 双钩（`OPT1-A` `0x6D378E` / `OPT1-B` `0x6D3988`）+ ZC-P1/P2/P5（必）+ ZC-P4 红线验收 + ZC-P3（建议）· **`ZC-SW-CHARGE` L-SW-1**（`0x6CBE88` 7×NOP）· 挂载 `ZB3-M01..M03` |
| **开关** | `L4DirtyMode`：`0=force-full`（默认，非法收敛）/ `1=vision-dirty` / `2=vanilla`（**禁止作 v1.5.0 等价档**）· `Opt1DualSkip` 默认 **1**（`0`=kill 运行期回滚）· **`EnableSWChargeOpt=0`（默认；=1 才装 L-SW-1）** |
| **顺序** | 批 A：L-05 符号 → L-06/07 两桩 → L-08/09 安装/卸载 → L-10/11 遥测+ini（OPT-1 全套，仅 `L4DirtyMode==force-full` 装钩）∥ 批 B：L-01 ZC-P1 pushfd/popfd → L-02 ZC-P2 计数语义 → L-04 ZC-P5 vanilla 禁令 ∥ **批 B′：L-SW-1**（G0.1–G0.8 全 PASS 后等长 7×NOP；可与 A/B 并行，回执分开）。批 C：E5/TC-L4-01 + OPT-1 AC1–AC6 + **L-SW-1 A1–A5**。批 D：**全绿后才**放行 `vision-dirty` |
| **硬约束** | OPT-1 门 = **仅 force/bForce**（Pass2 `[esp+0x58]`、Pass8 `[esp+0x68]`）；禁「非 vanilla 就跳过」/无条件跳过（否则 vision-dirty 非 force 帧漏画）。DETACH 必须同时还原 L4 点 `0x6D3D99` **与** OPT-1 两点。**L-SW-1 只许删冗余二次 call**（`8B CE E8 51 00 00 00` → `90×7`）；**必须保留** `0x6CBE8F` 写回与 `0x6CBE7E` 首次 call；**禁改** `GetCameoChargeState 0x6CBEE0` 公式/`54.0` 常数/clamp、`RechargeTimer`/`IsCharged` 翻转帧、`ChargeDrainState` FSM、`Set/ResetRechargeTime`；**禁跳帧/节流** `HasChargeProgressed`（7 项副作用非幂等） |
| **验收门** | E5-1 静态镜头 force-full vs vision-dirty 同帧像素 **D≡0**；E5-2 `l4RedrawSkippedStatic>0`（须 P2 修好）；E5-3 无旧位残影；OPT-1 AC1–AC6（含 kill 回归 AC4、两计数可见且 M1 含脏帧可 >0）；vanilla **不得**用 E5 证成 safe。**L-SW-1**：A1 默认 `0x6CBE88` 仍原 7B / A2 装后 `90×7` 且 `0x6CBE86/0x6CBE8F/0x6CBE7E` 未变 / **A3 充能到点帧号与基线一致**（禁「没崩当成功」）/ A4 存读档 / A5 双端 CRC + Checksum v[13] 一致。挂载 `ZB3-M01..M03` 按原判据 |
| **MP 姿态** | L4/OPT-1 **SAFE**（纯像素/控制流）；L-SW-1 **SAFE**（字节级语义等价，可联机保留，`MpActive` 不强制关）；联机建议全端同 `L4DirtyMode`/`Opt1DualSkip`/`EnableSWChargeOpt` 以便对拍。**均不进握手字段** |
| **回滚** | `Opt1DualSkip=0` 运行期恒重放；卸载写回 `s_origPass2DirtyBytes`/`s_origPass8Stage2Bytes` + L4 点原字节；`L4DirtyMode` 改回须重启。L-SW-1：软 `EnableSWChargeOpt=0`+重启；硬还原 `s_origLSW1[7]=8B CE E8 51 00 00 00`；工具 `--uninstall-l-sw-1`；备份 `out/re_work/re_sprint/R_sw_card/orig_bytes.bin` |
| **预计窗口** | **3–5 个执行日 / 2–3 个验收窗口 + ZB3 挂载 ≈3h**（L4/OPT-1 代码 1–2 日 + E5/AC 对拍 1–2 日；L-SW-1 0.5–1 日）[推演] |

### B4 · 内存 L1/L2 + 伤害链池化/加固

| 项 | 内容 |
|---|---|
| **卡号** | **B4a** `R-CRT-POOL` L1（`VectorReuse` / `VectorGeometric` / `VectorReserve`）→ **B4b** `R-L2-GAP`（Layer A 毒族门禁优先；Layer B `MemPoolClass34` 须 A/B）→ **B4c** `ZC-WPN-L1` DamageGroup 池 → `ZC-WPN-L2` 遥测 → `ZC-WPN-L3` 乘序审计锁 · 挂载 `ZB4-M01..M02` |
| **开关** | `[MemoryPool] EnableMemoryPool`（总闸，**启动期锁定禁热切**）+ `VectorReuse=0` / `VectorGeometric=0` / `VectorReserve=0` / `MemPoolSmall=0` / `MemPoolEntities=0` / **`MemPoolClass34=0`**（默认）· `[Logic] EnableDamageGroupPool=0` · `[Telemetry] EnableDamageTelemetry=0` / `EnableVersesAudit=0` |
> 【W3 勘误 · W3-A6/ISSUE-SECTION-MEMORYPOOL】[W3-Lead临时裁决] 改前：[MemoryPool] EnableMemoryPool；改后：[System] ; DC-01 裁决口径: 使用既有 [System] 节，零新增节 EnableMemoryPool=0；依据：docs/re/dispatch/W3_20261001_Lead_DECISION_AND_BOARD.md:40; docs/re/pending_execution_master_table.md:410-412；分级：P0
| **顺序** | ① **仅开 L1**（推荐首批默认姿态）→ ② Layer A（H2/H6 毒族 + H1 入链校验，零行为扰动）→ ③ Layer B `MemPoolClass34` **必须 A/B 三态**（原版 / +H2H6 / +H2H6+MemPoolClass34）→ ④ L-W1 四点等长 `E8 rel32` 换池（保 push 序）→ ⑤ L-W2 入口 6B 遥测 → ⑥ L-W3 `0x48923D` 前纯读插桩 → ⑦ `ZB4-M01` 长跑挂满多指标 / `ZB4-M02` 挂 ZC-1 Q5。`OnlineSafeMode=1` / 联机强制 **仅 L1** |
| **字节/语义契约** | L1 不碰分配器 ABI；L2 块头 **8B**（禁 4B 头）、`m_elemSize=(elem+7)&~7`、命中完全绕开 SBH、miss/耗尽 **穿透** 原版；音频 bulk `new(194408)` **必须 miss**（红线）。L-W1 池容量 256、溢出退回堆、**保序 0 PRNG**；地形特效四处 alloc **不池化**。L-W3 **只读** 断言 |
| **验收门** | L1：寻敌 Clear/Add 震荡下降方向 + 两局 except 空。L2 Layer A：毒值/守卫日志可见、无新增 UAF 崩溃。Layer B：A/B 三态对比 + U3 LFH/U6 毒值归因仍开。L-W1：高密度弹幕两局 except 空、PRNG 序不变（对拍或断言）。L-W2/3：计数非零、乘序哈希稳定。**禁百分比收益承诺**。挂载 `ZB4-M01`：M01/M02 **只报下降方向**、M03 两域平衡、M07 零挂死、M09 耗尽穿堆、M10 Private Bytes 220–280MB 无线性泄漏；`ZB4-M02` 干净退出零残留 |
| **MP 姿态** | L1 可开（仍禁热切）；L2 / 实体桶 **联机强制关**（`OnlineSafeMode`）；L-W1 保序安全但建议单机先行。全部 **不进握手字段** |
| **回滚** | 软：总闸=0（两入口不装钩，字节逐位相同）。硬：还原 `_new/_delete` 5B 跳板、L-W1 4×5B、L-W2 6B 序言、L-W3 插桩；`MemPoolClass34=0` 二阶回退 |
| **预计窗口** | **4–7 个执行日 / 3–4 个验收窗口 + ZB4 挂载 ≈1.7h（含 60min 长跑）**（L1 1–2 日；L2 A/B 2–3 日；L-W1..3 1–2 日）[推演] |

### B5 · 联机对拍与逻辑回归（**v2 新建**）

> **为何新建**：B1–B4 是四个补丁实施面；余下 6 条联机对拍 + 7 条核心逻辑回归（寻路/空间/AI/超武/存档）验证的是**同步确定性与玩法逻辑**，依赖 DUAL-LAN / 套件一独立场次，故独立成批。与 B1–B4 **可并行排期**，但 **MP 发布宣称仍以 G-R1 裁决为唯一门**。子卡全文见 `b_class_merge_zc_cards.md` §2（本票不改判据）。

| 项 | 内容 |
|---|---|
| **卡号** | `ZB5-M01`（★N03 对拍 500 帧 / N10 镜像 SHA256 / ★N11 混联 L0）· `ZB5-M02`（★N12 门控降级 / ★N13 索敌频率 / N17 SAV 哈希）· `ZB5-M03`（L01 寻路 / L02 基地展开 / L05 威胁等价 / L06 空间哈希）· `ZB5-M04`（L07 AITrigger 双机 / L08 超武并行倒计时 / L14 Timer 落盘续读） |
| **开关** | 本批 **不安装补丁**；消费既有开关姿态。对拍局要求：两端同构建、同 ini、同种子。N11 混联探针仅「A 诊断镜像 vs B 原版」，且 `EnableSpySatRadarSweep=EnableRadarSweepWindow=EnableGapProtection=EnableMinimapFog=0` |
| **顺序（强制）** | ① **DUAL-LAN 双机同网段就绪**（硬前提，单实例不可代）→ ② `ZB5-M01` ★N03/N11 优先 → ③ `ZB5-M02` ★N12/N13 → ④ `ZB5-M03` → ⑤ `ZB5-M04`（L07/L08 须双机；L14 可加存读档步骤）。可与 B1–B4 并行，**场次独立** |
| **契约** | 步骤与判据 **原样引用** `b_class_live_test_index.md` §4，本票不改单项分钟数；压缩仅标注「同场次可合并」。产物落 `out/re_work/re_sprint/R_b_merge/evidence/ZB5-M0X/` |
| **验收门** | N03：`compare_sync_mirrors` **MATCH 100%（500/500）**。N10：`g_MirrorRing.bin` 两端 SHA256 相同。N11：零 `SYNC*.TXT`、不弹 OOS。N12：ONLINE→W1–W6 自动降级生效。N13：索敌频率回归原版逐帧、不分叉。N17：SAV 核心块哈希一致、原版可读。L01：`Cell+0x100` 链表双向对称、0 野指针。L02：`v[73]` 3x3 全阻挡。L05：稳定攻击高威胁目标。L06：空间哈希检索正常不崩。L07：双机同时精准触发。L08：双端秒数严格同步。L14：精准从 10s 续倒计时。收尾 `except.txt` 0 字节。**禁「没崩当成功」** |
| **MP 姿态** | 本批即 MP 验证面，但 **验证 ≠ 发布放行**。唯一授权混联探针 = N11「诊断镜像 vs 原版」；**严禁**把 gap/particle 等 VIOLATION 面补丁混端。回执 **禁止**写「G4.1 已满足 / MP 可发布」 |
| **回滚** | 挂载类卡不执行安装/卸载；补丁回滚仍归 B1–B4 原卡。场次失败仅重跑，不涉字节还原 |
| **预计窗口** | **2–3 个执行日 / 3–4 个验收窗口（压缩 ≈5.5h）**（M01 150m + M02 80m + M03 50m + M04 55m；DUAL-LAN 场次协调占主要耗时）[推演] |

---

## 3. 全局红线汇总（所有批次共用，只强不松 · v2 重申）

| # | 红线 | 内容 | 触发后果 |
|---|---|---|---|
| **G-R1** | **MP 握手冲突待裁** | `gap_merge_checklist.md` §7.1：**甲**=不加协议字段（落地卡侧暂维持）vs **乙**=握手键必须含 `EnableGapProtection` + `gapProtectionPatchesInstalled`（期望 3）且混端拒开局（`savegame_product_checklist.md` G4.1/G4.2）。**裁决前任何一方不得单方面改协议或宣称 G4.1 已满足**。v2 增补卡（H-20-C / SW-CHARGE / B5）**一律不新增握手字段**；若裁为乙，键清单是否纳入 `EnableRadarSweepWindow` / `EnableSWChargeOpt` 由裁决一并定，**裁决前不实现** | 未裁即宣称 MP 就绪 = **违规** |
| **G-R2** | **混端 DESYNC** | gap 三点改 `Cell+0x134`（进 `.SAV`、不进帧 CRC 却主导索敌/可见性）→ 第一次 `RevealArea2/3/Reshroud` 后分叉 = **VIOLATION**。particle 音频 vxl L4 H-20-C(纯 R-c) SW-CHARGE = 表现层/语义等价 **SAFE**。path cache = **RISK**（保序才安全）。**严禁混端**（一端补丁一端原版）；全端同构建同开关同 `installed`。**唯一例外**：ZB5-M01 的 N11「诊断镜像 vs 原版」混联探针（且四键全 0） | 混端联机必炸 / 必 DESYNC |
| **G-R3** | **禁改 GetTotalDamage 乘序** | `GetTotalDamage 0x489180` 链：`×PercentAtMax → 距离插值 → ×Verses(0x48923D fmul) → int`；`ReceiveDamage 0x701939` `fdivr` 链。**禁止**合并/交换 `fmul`/`fdivr`/`fild`/`fstp` 序、上提 Verses、缓存可变字段、整数乘替浮点。**禁止**改调用次数/调用点集合（`0x5F540F` / `0x6FDD29` / `0x701D64`）。**v2 并行锚点**：`GetCameoChargeState 0x6CBEE0` 公式 / `54.0`（`0x7F4048`）/ clamp `0..0x35/0x36`、`RechargeTimer` 推进、`IsCharged` 翻转帧（`0x6CBD5D`）同级禁改——经 `+0x78` 进 `CalculateChecksum v[13]=0x6CE020` | 联机必炸（伤害分叉 / 充能分叉） |
| **G-R4** | **同步 PRNG 零容忍** | 伤害链 12 处局内同步 PRNG（P16–P27）**禁止跳过/改序/合并候选/并行化**；「看起来是视觉」的 P21/P22/P27 也必须照常消费。粒子/迷雾/GAP/扫窗谓词 **只许拦 Draw / 只许临时加可见**，绝不可拦 ReceiveDamage/DamageArea/GetTotalDamage 入口。**H-20-C 专项**：禁止新增 `ScenarioClass::Random/RandomRanged`；禁止写 `Cell+0x12C/0x130/0x134/0x140`；`SW+0xB0` CD 改写与扫窗包**分开开关**（会平移其它 case Launch 帧 ⇒ RNG 流） | 跳过消费 = 联机必炸 |
| **G-R5** | **禁止宣称 MP 可发布** | 在 G-R1 握手口径 **Lead 裁决完成前**，任何批次回执、文档、日志 **不得**出现「MP 可发布 / G4.1 已满足 / 联机安全可出厂」类表述。当前唯一安全混端姿势 = **本端整局不加载 `ra2render.dll`**，或全员同构建同开关（且仍需 Gate3 / M2 对拍）。**B5 全绿也只证明「本轮对拍通过」，不构成发布宣称** | 未裁即宣称 = 交付不合格 |
| **G-R6** | 门禁与证据纪律 | 每卡 G0.x 全 PASS 才写；首字节非预期 = **停手上报**（禁覆盖未知安装者）；「没崩」≠ 成功；禁伪造实测；禁热切换安装态开关；禁改零常量寄存器 / growstep / EVA / `0x64DE3F`。**v2 锚点**：H-20-C T-a **7B**（`0x6CD7C4`，旧文 5B 为勘误，禁 5B 切断指令）；SW-CHARGE G0.1–G0.8 + Q1 首字节；L-SW-2 **Q2 不过则放弃**；A3 类「到点帧号/计数」硬证据 | 违者回退重做 |
> 【W3 勘误 · W3-A6/ISSUE-RADAR-SWEEP-5B】改前：0x6CD7C4`，旧文 5B；改后：0x006CD7C4 处指令为 7B (8A 84 24 EC 01 00 00)；依据：ra2youli/gamemd.exe:0x2CD7C4; errata_sync_master_table.md:18 (R-E03); h20c_private_sweep_spec.md:40-43；分级：P0
| **G-R7** | 回滚可逆 | 每批必须留原字节备份并 **实测回滚**；gap 逆序拆点；DETACH 链覆盖全部写点（含 OPT-1 两点、SW-1、L-SW-1/2）。H-20-C 卸载 SW-1 **先于** `RemoveRadarFogHooks`，避免跳板悬空 | 回滚不可用 = 批次不闭环 |

---

## 4. 批次依赖与放行（v2 文字依赖图）

```
B1 (gap+VXL + ZB1) ──独立──► 可先合（P0 最大面）
B2 (audio+part+H20C+L-SW-2? + ZB2) ──表现层 SAFE──► 可与 B1 并行
      │  H-20-C 前置：路线A三钩已装（只改 C++ 谓词，不动 9B/7B/5B 补丁）
      │  H-20-C 与 gap：纯 R-c 不依赖 EnableGapProtection；若同开原版 Case11 则全端同值
      └─ L-SW-2 仅当 Q2 真机 frame=-1 容错通过，否则放弃
B3 (L4/OPT-1 + L-SW-1 + ZB3) ──独立──► 可与 B1/B2 并行
      │  vision-dirty 开档串在 P1+P2+P4 全绿后（批 D）
      └─ L-SW-1 与 L4/OPT-1 无依赖，可并行装，回执分开
B4 (mem+wpn + ZB4) ──最重──► 建议排后；Layer B 须 A/B 三态；联机仅 L1
B5 (ZB5-M01..M04) ──DUAL-LAN 硬前提──► 可与 B1–B4 并行排期，场次独立
      │  串行锁：ZB1 须 gap 三点 installed==3 后；ZB2 须 audio/particle 钩后
      │         ZB3 须 L4/OPT-1 装后；ZB4 须 L1 启动期锁定后；ZB5 须双机就绪
      ▼
  全批回执齐 ──► 仍不得宣称 MP 可发布（等 G-R1 裁决）
```

| 放行门 | 条件 |
|---|---|
| 批内闭环 | 该批全部卡回执按 `AGENT_DELIVERY_FORMAT` 交齐 + 门禁实跑 + 回滚实测（B5 为对拍/逻辑证据齐） |
| 跨批混装 | 允许（互不依赖）；异常归因 **先关后装键** |
| MP 发布宣称 | **唯一门** = Lead 对 §7.1 握手口径裁决落地 + G4.1/G4.2 实装/实测。B5 对拍 MATCH **不是**替代门 |
| H-20-C 放行 | A1–A10 全 PASS 且 `verify_h20c_bytes.py` 14/14；R-b 死键文档/日志勘误已做 |
| L-SW-1 放行 | A1–A5 全 PASS，A3 有「到点帧号不变」硬证据 |
| L-SW-2 放行 | **先过 Q2.1/Q2.2**（`frame=-1` 容错），否则整体放弃 |

---

## 5. 统一交付回执（每批一份，附在各卡回执后）

```text
R-ZC-MASTER BATCH RESULT · B?
- cards: (ZC-… / ZB-… list)
- switches set: (key=value …)
- install order + G0 gates: PASS/FAIL
- acceptance: (each case PASS/FAIL + evidence path)
- rollback tested: y/n + method
- except.txt: empty|path
- MP stance: (forced-off-mp | same-build-only | SAFE-keep | b5-verify-only)
- red-line touch: G-R1..G-R7 which, and mitigation
- forbidden-claim check: 「未宣称 MP 可发布」 y/n
```

> B5 额外必填：`DUAL-LAN 端配置` · `N11 混联范围（仅诊断镜像 vs 原版）` · `四键=0 自证`。

---

## 6. 预计窗口总表 [推演]（v2 含增补与 MERGE 挂载）

| 批 | 执行日 | 验收窗口 | MERGE 挂载 | 累计（串行） | 备注 |
|---|---:|---:|---:|---:|---|
| B1 | 2–3 | 2 | ZB1 60m | 2–3 日 | gap 机械替换 + VXL 两局 |
| B2 | 5–8 | 3–5 | ZB2 ≈195m | 7–11 日 | audio 状态机 + **H-20-C A1–A10** 最重 |
| B3 | 3–5 | 2–3 | ZB3 ≈175m | 10–16 日 | E5 像素对拍 + L-SW-1 A3 帧号 |
| B4 | 4–7 | 3–4 | ZB4 ≈100m | 14–23 日 | Layer B A/B 三态 + 60min 长跑 |
| B5 | 2–3 | 3–4 | （本体）≈335m | 16–26 日 | DUAL-LAN 场次协调 |
| **合计** | **16–26** | **13–18** | **≈13h** | — | 可并行压缩至约 **10–16 日**（B1∥B2∥B3∥B5，B4 收尾） |

> 窗口为排期估算，**不是**承诺；以真机验收实际耗时为准。单次真机验收参考 ZC-1：60–90 分钟/局包。MERGE 压缩窗口 ≈13h 与 `b_class_live_test_index.md` §6 的 12–16h 一致，**不是**新增性能承诺。

---

## 7. 不在本票

- P-2.2/2.3 独立键（已裁同键 `EnableGapProtection`）
- L-VXL-2/3、降采样光核、path cache 落地、SpySat TYPE/S2/S3 补门
- MP 握手字段扩展实现（待 §3 G-R1 裁决后另卡）
- H-20-C 的 **R-a+ 解夹紧**（`0x567A4A`，默认禁止）；R-a 改 `Rules+0xFEC` 仅当产品同时启用原版 `RevealArea2` 时可选叠加
- `GetCameoChargeState` 公式重写 / `54.0` 映射 / clamp 变更；`RechargeTimer` 折叠 / `IsCharged` 翻转时机 / `ChargeDrainState` FSM 重做；跳帧节流 `HasChargeProgressed`
- 死代码 `0x4F9370` 清理、`Type+0xF8` 假说验证
- `ra2render` 源码重构 / 台账 / 看板登记（Lead 收口）
- 任何「性能百分比」承诺（只验收字节装上 + 计数方向 + except 空）

---

## 8. v1 → v2 变更摘要

| 项 | v1 | v2 |
|---|---|---|
| 批次数 | B1–B4 | **B1–B5**（B5 联机对拍与逻辑回归） |
| 卡面 | 九份落地卡/清单 | + **H-20-C**（B2）· **ZC-SW-CHARGE**（L-SW-1→B3 / L-SW-2→B2 可选）· **ZB5-M01..M04**（B5）· MERGE50 挂载 ZB1–ZB4 |
| 窗口合计 | 11–19 执行日 / 9–10 验收窗 | **16–26 / 13–18** + MERGE ≈13h；并行压缩 **10–16 日** |
| 红线 | G-R1..R7 | 重申并锚定 H-20-C 7B 勘误 / SW 公式禁区 / N11 唯一混联例外 / B5 非发布门 |
| v1 文件 | 本体 | **不改**，仍为历史基线 |

---

*v2 依据：`zcode_master_implementation_ticket.md`（v1）+ `h20c_private_sweep_spec.md` + `landing_pack_sw_charge.md` + `b_class_merge_zc_cards.md` 交叉汇总；红线只强不松；窗口与批序为编排建议 [推演]，字节与开关均引自原卡 [实证]。v1 保持只读。*
