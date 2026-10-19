# ZCode 总实施票 · R-ZC-MASTER

> **任务号**：`R-ZC-MASTER` · **读者**：ZCode（真机/补丁安装唯一写者）+ 验收方  
> **起草**：MiMo 汇总已就绪落地卡 · **状态**：待 Lead 派发  
> **证据基线**：`ra2youli/gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` · ImageBase `0x00400000` · `file_off = VA − 0x00400000`  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **写作用域**：本文 + `out/re_work/re_sprint/R_zc_master/**`  
> **禁写**：`ra2render/**`、`gamemd.exe` / `ra2youli/**`（安装动作由 ZCode 按卡执行）、`tools/**`、台账、看板  
> **回报格式**：强制 `docs/re/AGENT_DELIVERY_FORMAT.md` §A 十节骨架

---

## 0. 一句话

把九份已就绪落地卡/清单按 **B1 安全落地 → B2 表现层 → B3 L4/OPT-1 → B4 内存/伤害链** 四批推进；每批独立验收门、独立回滚；**全局红线只强不松**；在 MP 握手口径裁决前 **禁止宣称「MP 可发布」**。

---

## 1. 卡片总清单（本票覆盖面）

| 批 | 卡号 / 清单 | 源文档 | 落地面 | 优先级 | DESYNC 判定 |
|---|---|---|---|---|---|
| **B1** | `ZC-GAP-P21` | `landing_pack_gap_p21.md` | P-2.1 6×NOP @ `0x568273` | **P0** | 混端 **VIOLATION**（`Cell+0x134`） |
| **B1** | `ZC-GAP-P223` | `landing_pack_gap_p223.md` | P-2.2/P-2.3 各 6×NOP | P1 | 同上 |
| **B1** | `R-GAP-MERGE` | `landing_pack_gap_merge_checklist.md` | 三点合并编排 + `installed==3` | P0 编排 | 同上 |
| **B1** | `ZC-VXL-PRE` | `landing_pack_vxl_prewarm.md` | L-VXL-1 imm8 `0x0A→0x40` @ `0x706D78` | P1 | **SAFE**（D-VXL13） |
| **B2** | `ZC-AUDIO-THROT` | `landing_pack_audio_throttle.md` | AT-A/B/C Play* 入口限频 | P1 | **SAFE**（D-AUDIO） |
| **B2** | `ZC-PART-FOG` | `landing_pack_particle.md` | 槽 69 粒子 Draw 剔除 | P1 | **SAFE**（D-PART；禁改逻辑字段） |
| **B3** | `R-L4-MERGE` | `landing_pack_l4_opt1_checklist.md` | L4 桩 + OPT-1 双钩 + ZC-P1..P5 | P1 | **SAFE**（D-L4） |
| **B4** | `R-CRT-POOL` **L1** | `crt_pool_landing.md` §2.2 | 向量 Clear/Reserve/几何扩容 | P1 | **RISK**（启动期锁；禁热切） |
| **B4** | `R-L2-GAP` | `crt_l2_class34_fix_spec.md` | L2 class3/4 空洞（Layer A/B） | P1 | **RISK**（改 class4 生命周期须 A/B） |
| **B4** | `ZC-WPN-L1..3` | `weapons_damage_landing.md` | L-W1 池化 / L-W2 遥测 / L-W3 乘序锁 | P1 | L-W1 **安全（保序 0 PRNG）**；L-W2/3 纯读 |

> 附带不装（本票明确排除）：L-VXL-2/3 影跳过、降采样光核、path cache oracle、SpySat TYPE/S2/S3 旁路补装、任何新 MP 握手字段。

---

## 2. 批次拆分与执行卡

### B1 · 安全落地（gap 三点 + VXL 预热）

| 项 | 内容 |
|---|---|
| **卡号** | `ZC-GAP-P21` → `ZC-GAP-P223`（同装）· 编排 `R-GAP-MERGE` · `ZC-VXL-PRE` |
| **开关** | `[FogOfWar] EnableGapProtection`（默认 **0**）· `[Render] EnableVxlCachePrewarm`（默认 **0**）· 均 **init 一次锁定，禁热重载** |
| **顺序（强制）** | ① 门禁 G0.1–G0.7 全 PASS → ② P-2.1 `0x568273` → ③ P-2.2 `0x577EC5` → ④ P-2.3 `0x577B60` → ⑤ `gapProtectionPatchesInstalled` 回写（期望 **3**）→ ⑥ 真机 Q1 三点首字节复核 → ⑦ 独立装 `ZC-VXL-PRE` `0x706D78`（与 gap 无依赖，可并行但 **回执分开**） |
| **字节契约** | 三点各 **6==6** 等长 `90×6`；VXL **5==5** 等长仅 imm8 `0x0A→0x40`。禁 trampoline、禁 `89→8B`、禁改零常量寄存器、禁动 growstep `0x706D7F` |
| **验收门** | gap：A1 默认不装 / A2 装后字节窗 MATCH / **A3 裂缝遮挡仍在**（截图或计数，禁「没崩当成功」）/ A4 存读档缝态保持 + `except.txt` 空 / A5（可选）DestroyGap 计数回 0。VXL：A1–A2 同上 / A3 **连打两局** except 均空 / A4 遥测计数可见且 `Growths/QsortCalls` 相对键关局 **有下降方向**（无百分比承诺） |
| **MP 姿态** | gap：`MpActive` **强制不装**；全端同构建同 `EnableGapProtection` 同 `installed`（皆 3 或皆 0），**严禁混端**。VXL：可装（SAFE）；全端同键以便遥测同口径 |
| **回滚** | 软：键=0 + 重启。硬：`s_origP21/P22/P23[6]` 逆序 `P-2.3→P-2.2→P-2.1` 还原（或整组）；VXL `s_origLVxl1[5]=BB 0A 00 00 00` 还原。卸载工具 `--uninstall-gap-all` / `--uninstall-lvxl1` |
| **预计窗口** | **2–3 个执行日 / 2 个验收窗口**（安装 0.5 日 + 真机 A 系列 1–1.5 日 + 回执归档 0.5 日）[推演] |

### B2 · 表现层（audio / particle）

| 项 | 内容 |
|---|---|
| **卡号** | `ZC-AUDIO-THROT`（AT-A `0x750920` / AT-B `0x7509E0` / AT-C `0x750E20`）· `ZC-PART-FOG`（槽 69 `0x7EFA68` / `0x7EFCB0`） |
| **开关** | `[AudioThrottle] Enable=0`（默认）+ `MaxVoicePerFrame=6` / `VoiceDedupMs=80` / `MaxSamePerWindow=2` / `WhitelistPriorityMin=3` / `ThrottlePlayIndexAtPos=1` · `[FogOfWar] EnableParticleFog=0`（默认） |
| **顺序** | ① audio 三钩 trampoline（A→B→C，判定序严格按卡 §2.2）→ ② particle 两槽 69 虚表钩（**不碰**已装五槽）→ ③ 两卡分别跑验收。互不依赖，可并行派工但 **回执分开** |
| **字节/结构契约** | audio：覆盖 6/5/5B 为 `E9 rel32`，失败出口必须 `xor eax,eax; ret 8/4`（禁裸 ret、禁 `or eax,-1`）；**禁钩** EVA `0x752700`、**零接触** `0x64DE3F`。particle：只拦 **Draw** 虚表槽 69，禁写 Update/AI/寿命/坐标/Owner |
| **验收门** | audio：默认零行为差（A1）；Enable=1 后洪泛场景削峰、白名单 EVA/UI 仍出声、遥测计数可见、`except.txt` 空；两池（200 槽）压力下降方向可报。particle：雾中粒子不绘制、可见区正常、生成侧 PRNG **照常消费**（无 SYNC 异常）、两局 except 空 |
| **MP 姿态** | 二者均 **SAFE**（无帧 CRC 分叉）；混端可共存（观感可不一致，不构成 VIOLATION）。不新增握手键 |
| **回滚** | audio：`Enable=0` 软关直通 + 卸载时还原原字节/释放跳板。particle：`EnableParticleFog=0` + 卸载时恢复原虚表 DWORD（`C0 CE 62 00` / `80 E2 62 00` LE） |
| **预计窗口** | **3–5 个执行日 / 2–3 个验收窗口**（audio trampoline + 状态机 2–3 日；particle 1–2 日）[推演] |

### B3 · L4 / OPT-1（`R-L4-MERGE`）

| 项 | 内容 |
|---|---|
| **卡号** | OPT-1 双钩（`OPT1-A` `0x6D378E` / `OPT1-B` `0x6D3988`）+ ZC-P1/P2/P5（必）+ ZC-P4 红线验收 + ZC-P3（建议） |
| **开关** | `L4DirtyMode`：`0=force-full`（默认，非法收敛）/ `1=vision-dirty` / `2=vanilla`（**禁止作 v1.5.0 等价档**）· `Opt1DualSkip` 默认 **1**（`0`=kill 运行期回滚） |
| **顺序** | 批 A：L-05 符号 → L-06/07 两桩 → L-08/09 安装/卸载 → L-10/11 遥测+ini（OPT-1 全套，仅 `L4DirtyMode==force-full` 装钩）∥ 批 B：L-01 ZC-P1 pushfd/popfd → L-02 ZC-P2 计数语义 → L-04 ZC-P5 vanilla 禁令。批 C：E5/TC-L4-01 + OPT-1 AC1–AC6。批 D：**全绿后才**放行 `vision-dirty` |
| **硬约束** | OPT-1 门 = **仅 force/bForce**（Pass2 `[esp+0x58]`、Pass8 `[esp+0x68]`）；禁「非 vanilla 就跳过」/无条件跳过（否则 vision-dirty 非 force 帧漏画）。DETACH 必须同时还原 L4 点 `0x6D3D99` **与** OPT-1 两点 |
| **验收门** | E5-1 静态镜头 force-full vs vision-dirty 同帧像素 **D≡0**；E5-2 `l4RedrawSkippedStatic>0`（须 P2 修好）；E5-3 无旧位残影；OPT-1 AC1–AC6（含 kill 回归 AC4、两计数可见且 M1 含脏帧可 >0）；vanilla **不得**用 E5 证成 safe |
| **MP 姿态** | **SAFE**（纯像素/控制流）；联机建议全端同 `L4DirtyMode`/`Opt1DualSkip` 以便对拍 |
| **回滚** | `Opt1DualSkip=0` 运行期恒重放；卸载写回 `s_origPass2DirtyBytes`/`s_origPass8Stage2Bytes` + L4 点原字节；`L4DirtyMode` 改回须重启 |
| **预计窗口** | **2–4 个执行日 / 2 个验收窗口**（代码 1–2 日 + E5/AC 对拍 1–2 日）[推演] |

### B4 · 内存 L1/L2 + 伤害链池化/加固

| 项 | 内容 |
|---|---|
| **卡号** | **B4a** `R-CRT-POOL` L1（`VectorReuse` / `VectorGeometric` / `VectorReserve`）→ **B4b** `R-L2-GAP`（Layer A 毒族门禁优先；Layer B `MemPoolClass34` 须 A/B）→ **B4c** `ZC-WPN-L1` DamageGroup 池 → `ZC-WPN-L2` 遥测 → `ZC-WPN-L3` 乘序审计锁 |
| **开关** | `[MemoryPool] EnableMemoryPool`（总闸，**启动期锁定禁热切**）+ `VectorReuse=0` / `VectorGeometric=0` / `VectorReserve=0` / `MemPoolSmall=0` / `MemPoolEntities=0` / **`MemPoolClass34=0`**（默认）· `[Logic] EnableDamageGroupPool=0` · `[Telemetry] EnableDamageTelemetry=0` / `EnableVersesAudit=0` |
> 【W3 勘误 · W3-A6/ISSUE-SECTION-MEMORYPOOL】[W3-Lead临时裁决] 改前：[MemoryPool] EnableMemoryPool；改后：[System] ; DC-01 裁决口径: 使用既有 [System] 节，零新增节 EnableMemoryPool=0；依据：docs/re/dispatch/W3_20261001_Lead_DECISION_AND_BOARD.md:40; docs/re/pending_execution_master_table.md:410-412；分级：P0
| **顺序** | ① **仅开 L1**（推荐首批默认姿态）→ ② Layer A（H2/H6 毒族 + H1 入链校验，零行为扰动）→ ③ Layer B `MemPoolClass34` **必须 A/B 三态**（原版 / +H2H6 / +H2H6+MemPoolClass34）→ ④ L-W1 四点等长 `E8 rel32` 换池（保 push 序）→ ⑤ L-W2 入口 6B 遥测 → ⑥ L-W3 `0x48923D` 前纯读插桩。`OnlineSafeMode=1` / 联机强制 **仅 L1** |
| **字节/语义契约** | L1 不碰分配器 ABI；L2 块头 **8B**（禁 4B 头）、`m_elemSize=(elem+7)&~7`、命中完全绕开 SBH、miss/耗尽 **穿透** 原版；音频 bulk `new(194408)` **必须 miss**（红线）。L-W1 池容量 256、溢出退回堆、**保序 0 PRNG**；地形特效四处 alloc **不池化**。L-W3 **只读** 断言 |
| **验收门** | L1：寻敌 Clear/Add 震荡下降方向 + 两局 except 空。L2 Layer A：毒值/守卫日志可见、无新增 UAF 崩溃。Layer B：A/B 三态对比 + U3 LFH/U6 毒值归因仍开。L-W1：高密度弹幕两局 except 空、PRNG 序不变（对拍或断言）。L-W2/3：计数非零、乘序哈希稳定。**禁百分比收益承诺** |
| **MP 姿态** | L1 可开（仍禁热切）；L2 / 实体桶 **联机强制关**（`OnlineSafeMode`）；L-W1 保序安全但建议单机先行。全部 **不进握手字段** |
| **回滚** | 软：总闸=0（两入口不装钩，字节逐位相同）。硬：还原 `_new/_delete` 5B 跳板、L-W1 4×5B、L-W2 6B 序言、L-W3 插桩；`MemPoolClass34=0` 二阶回退 |
| **预计窗口** | **4–7 个执行日 / 3 个验收窗口**（L1 1–2 日；L2 A/B 2–3 日；L-W1..3 1–2 日）[推演] |

---

## 3. 全局红线汇总（所有批次共用，只强不松）

| # | 红线 | 内容 | 触发后果 |
|---|---|---|---|
| **G-R1** | **MP 握手冲突待裁** | `gap_merge_checklist.md` §7.1：**甲**=不加协议字段（落地卡侧暂维持）vs **乙**=握手键必须含 `EnableGapProtection` + `gapProtectionPatchesInstalled`（期望 3）且混端拒开局（`savegame_product_checklist.md` G4.1/G4.2）。**裁决前任何一方不得单方面改协议或宣称 G4.1 已满足** | 未裁即宣称 MP 就绪 = **违规** |
| **G-R2** | **混端 DESYNC** | gap 三点改 `Cell+0x134`（进 `.SAV`、不进帧 CRC 却主导索敌/可见性）→ 第一次 `RevealArea2/3/Reshroud` 后分叉 = **VIOLATION**。particle 音频 vxl L4 = 表现层 **SAFE**。path cache = **RISK**（保序才安全）。**严禁混端**（一端补丁一端原版）；全端同构建同开关同 `installed` | 混端联机必炸 / 必 DESYNC |
| **G-R3** | **禁改 GetTotalDamage 乘序** | `GetTotalDamage 0x489180` 链：`×PercentAtMax → 距离插值 → ×Verses(0x48923D fmul) → int`；`ReceiveDamage 0x701939` `fdivr` 链。**禁止**合并/交换 `fmul`/`fdivr`/`fild`/`fstp` 序、上提 Verses、缓存可变字段、整数乘替浮点。**禁止**改调用次数/调用点集合（`0x5F540F` / `0x6FDD29` / `0x701D64`） | 联机必炸（伤害分叉） |
| **G-R4** | **同步 PRNG 零容忍** | 伤害链 12 处局内同步 PRNG（P16–P27）**禁止跳过/改序/合并候选/并行化**；「看起来是视觉」的 P21/P22/P27 也必须照常消费。粒子/迷雾/GAP 谓词 **只许拦 Draw**，绝不可拦 ReceiveDamage/DamageArea/GetTotalDamage 入口 | 跳过消费 = 联机必炸 |
| **G-R5** | **禁止宣称 MP 可发布** | 在 G-R1 握手口径 **Lead 裁决完成前**，任何批次回执、文档、日志 **不得**出现「MP 可发布 / G4.1 已满足 / 联机安全可出厂」类表述。当前唯一安全混端姿势 = **本端整局不加载 `ra2render.dll`**，或全员同构建同开关（且仍需 Gate3 / M2 对拍） | 未裁即宣称 = 交付不合格 |
| **G-R6** | 门禁与证据纪律 | 每卡 G0.x 全 PASS 才写；首字节非预期 = **停手上报**（禁覆盖未知安装者）；「没崩」≠ 成功；禁伪造实测；禁热切换安装态开关；禁改零常量寄存器 / growstep / EVA / `0x64DE3F` | 违者回退重做 |
| **G-R7** | 回滚可逆 | 每批必须留原字节备份并 **实测回滚**；gap 逆序拆点；DETACH 链覆盖全部写点（含 OPT-1 两点） | 回滚不可用 = 批次不闭环 |

---

## 4. 批次依赖与放行

```
B1 (gap+VXL) ──独立──► 可先合（P0 最大面）
B2 (audio+part) ──独立──► 可与 B1 并行（表现层 SAFE）
B3 (L4/OPT-1) ──独立──► 可与 B1/B2 并行；vision-dirty 开档串在 P1+P2+P4 后
B4 (mem+wpn) ──最重──► 建议排后；Layer B 须 A/B；联机仅 L1
        │
        ▼
  全批回执齐 ──► 仍不得宣称 MP 可发布（等 G-R1 裁决）
```

| 放行门 | 条件 |
|---|---|
| 批内闭环 | 该批全部卡回执按 `AGENT_DELIVERY_FORMAT` 交齐 + 门禁实跑 + 回滚实测 |
| 跨批混装 | 允许（互不依赖）；异常归因 **先关后装键** |
| MP 发布宣称 | **唯一门** = Lead 对 §7.1 握手口径裁决落地 + G4.1/G4.2 实装/实测 |

---

## 5. 统一交付回执（每批一份，附在各卡回执后）

```text
R-ZC-MASTER BATCH RESULT · B?
- cards: (ZC-… list)
- switches set: (key=value …)
- install order + G0 gates: PASS/FAIL
- acceptance: (each case PASS/FAIL + evidence path)
- rollback tested: y/n + method
- except.txt: empty|path
- MP stance: (forced-off-mp | same-build-only | SAFE-keep)
- red-line touch: G-R1..G-R7 which, and mitigation
- forbidden-claim check: 「未宣称 MP 可发布」 y/n
```

---

## 6. 预计窗口总表 [推演]

| 批 | 执行日 | 验收窗口 | 累计（串行） | 备注 |
|---|---:|---:|---:|---|
| B1 | 2–3 | 2 | 2–3 日 | gap 机械替换 + VXL 两局 |
| B2 | 3–5 | 2–3 | 5–8 日 | audio 状态机最重 |
| B3 | 2–4 | 2 | 7–12 日 | E5 像素对拍占验收 |
| B4 | 4–7 | 3 | 11–19 日 | Layer B A/B 三态 |
| **合计** | **11–19** | **9–10** | — | 可并行压缩至约 **8–12 日**（B1∥B2∥B3，B4 收尾） |

> 窗口为排期估算，**不是**承诺；以真机验收实际耗时为准。单次真机验收参考 ZC-1：60–90 分钟/局包。

---

## 7. 不在本票

- P-2.2/2.3 独立键（已裁同键 `EnableGapProtection`）
- L-VXL-2/3、降采样光核、path cache 落地、SpySat TYPE/S2/S3 补门
- MP 握手字段扩展实现（待 §3 G-R1 裁决后另卡）
- `ra2render` 源码重构 / 台账 / 看板登记（Lead 收口）
- 任何「性能百分比」承诺（只验收字节装上 + 计数方向 + except 空）

---

*依据：九份已就绪落地卡/清单交叉汇总；红线取自 `landing_pack_gap_merge_checklist.md` §7.1、`net_sync_desync_map.md`、`weapons_damage_landing.md` §3、`mp_gate_residual_deep_dive.md`。窗口与批序为编排建议 [推演]，字节与开关均引自原卡 [实证]。*
