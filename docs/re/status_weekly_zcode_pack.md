# 状态周报 · ZCode Pack（R-WEEKLY）

> 任务 `R-WEEKLY` · 汇总口径：`landing_pack_inventory_v2` + 勘误闭环 + 各 RESULT + G-R1 备忘  
> 证据基线：`gamemd.exe` 1.001 · SHA-256 `73201CC0…FCC67476` · ImageBase `0x00400000`  
> 状态词**必须带轨名**（二进制轨 / 代码轨）；禁混称、禁写「MP 可发布」  
> 产物：本文 + `out/re_work/re_sprint/R_weekly/**`。**未改**台账/看板/landing_pack 本体。

---

## 一、本周进度

### 1. 盘点刷新 · `landing_pack_inventory_v2`（R-INV-REFRESH）

- 卡片总数 **29**（v1→v2 +1：新卡 `ZC-SW-RADIUS-RA`，R-a 数据改源 `Rules+0xFEC`）。
- **二进制轨**：已落地 **5** · 就绪 **18** · 待批 **4** · n/a **2**。
- **代码轨**：已落地 **5** · 已勘误 **1** · 未落地 **2** · n/a **21**。
- 相对 v1 关键升级：`ZC-VXL-PRE` / `ZC-SW-CHARGE-L1` 由「就绪」→ 双轨**已落地**（`_code/RESULT_*` 实证）；GAP-P21/P223 代码轨由「grep 0 命中」→ **已落地**（`ra2render.h` 三点 ADDR + `InstallGapProtectionPatch`）。
- 混称检查全过：全部状态行带轨名，未用二进制收据证明代码轨。

### 2. 勘误闭环 · R-E01～R-E10（四波）

| 波 | 条目 | 结果 |
|---|---|---|
| W1 | R-E01/E03/E08/E10（地址·机器码） | **已加注**（E01×5 文件、E03×3 锚点；E08/E10 既有包已收编） |
| W2 | R-E04/E09（语义红线） | **已加注**（死键、`OccuredEvents` 位序） |
| W3 | R-E02/E05/E07（计数·长度） | **已加注**（21B→17B；过滤对象写反；8 处→**9 处**） |
| W4 | R-E06（口径注记） | **已加注**（`_delete` 线性 4498 / 真值 ≥4499，标口径不回改历史） |

- 原则：**只加【勘误】不删原文**；四波验收（锚点可定位 / removed=0 / 台账看板哈希不变 / S15·S18 未触碰）全 **PASS**。
- 遗留：R-E03 中 `radar_sweep_sw_deep_dive.md` 行内旧文「5B」仍保留原文（勘误块已加，符合 only-add）；历史扫描报告按约定不回改。

### 3. RESULT 回执（zcode_live）

| 回执 | 要点 | 验收态 |
|---|---|---|
| `RESULT_GAP_P21` | P-2.1 @`0x568273` 等长 NOP×6；A1/A2 真机 PASS；`MpActive` 强制不装 | **A3 不可达**（见阻塞） |
| `RESULT_GAP_P223` | 三点表驱动（P-2.2/P-2.3 各 6B）；installed=3 遥测 21 次；逆序回滚 PASS | A3–A5 转战役轨 |
| `RESULT_VXL_PRE` | `0x706D78` imm8 10→64；A1/A2 PASS；DETACH 硬回滚 PASS | A3 部分 / A4 未做（计数器未实现） |
| `RESULT_SW_CHARGE` | `0x6CBE88` 7B→`90×7`；语义等价（纯读函数冗余 call）；A1/A2 PASS | A3–A5 未做（缺超武场景） |
| `RESULT_ZC1`～`ZC11` / `RESULT_H1_REMEASURE` | 门控/灰雾/雷达/稳定回归；零崩溃、ini 已还原 | 部分项如实标未测（不伪造） |

### 4. G-R1 备忘 · `docs/re/g_r1_handshake_decision_memo.md`

- 决策问题：P-2.x 落地后，联机握手是否强制校验补丁身份/配置（**甲**不加键 vs **乙** G4.1 硬握手）。
- 备忘已给依据·风险·折中·推荐：**C4 分阶段**——开发期维持甲；宣称「MP 可发布」前必须裁乙（最小键集）或 Lead 书面改判 G4.1。
- **不代裁**；§7.1 仍 open。红线重申：裁决前禁止单方面改协议，禁止出现「MP 可发布 / G4.1 已满足」类表述。

---

## 二、就绪卡列表（二进制轨「就绪」，可进下一波）

| 批次 | 卡号 | 要点 | 代码轨 | 回执 |
|---|---|---|---|---|
| B2/W2 | `ZC-H20C-SWEEP` | T-a `0x6CD7C4` **7B**（R-E03）· `EnableRadarSweepWindow` | **未落地**（Track-R 串行） | `R_h20c_card/` |
| B2/W2 | `ZC-SW-RADIUS-RC` | 零 .text · `RadarSweepRadiusCells` | **未落地**（依赖 H20C） | `R_swr_card/` |
| B2/W2 可选 | `ZC-SW-RADIUS-RA` ★新 | `Rules+0xFEC` clamp 1..10 · 纯数据写 | n/a | `R_swra_card/` |
| B2/W2 | `ZC-AUDIO-THROT` | AT-A/B/C · `[AudioThrottle] Enable` | n/a | `R_audio_card/` |
| B2/W2 | `ZC-PART-FOG` | 槽69 LE（R-E08）· `EnableParticleFog` | n/a | `R_part_card/` |
| B3/W3 | `ZC-CRT-L1` | `0x4E9A10` 等 · `EnableMemoryPool` | n/a | `R_crt_card/` |
| B3 | `R-L4-MERGE` | OPT-1 + L4 + ZC-P1..P5 | **已勘误**（L4DirtyMode 进码 ≠ 功能全装） | `R_l4_merge/` |
| B4c/W3 | `ZC-WPN-LW` | L-W1 四点 + L-W2/3 · 三开关 | n/a | `R_wpn_card/` |
| W1 诊断 | `ZC-HD-DIAG` | `0x64C6F2`/`0x64CC61` · 与 M-8 同面勿双装 | n/a | `R_hd_card/` |
| W1 | `ZC-GAP-P21-A3` | 不改字节 · A3/A4/A5 行为验收 | n/a | `R_p21_a3/` |

**已落地（双轨 5 卡，本波不再排）**：`ZC-GAP-P21` · `ZC-GAP-P223` · `R-GAP-MERGE` · `ZC-VXL-PRE` · `ZC-SW-CHARGE-L1`。

**待批（4，非就绪）**：`ZC-SW-CHARGE-L2`(Q2) · `ZC-CRT-L2-C34`(A/B) · `ZB5-M01..M04`(DUAL-LAN) · `R-ZC-MASTER`。

---

## 三、阻塞

| # | 阻塞 | 性质 | 影响 | 破局 |
|---|---|---|---|---|
| **1** | **G-R1** MP 握手甲/乙未裁 | 流程门 · P0 | 「MP 可发布」**无合法路径**；任何批次对拍全绿均不构成发布宣称；禁止单方面改协议 | Lead 对 §7.1 落槌：裁乙→另卡最小键集实装+G4.1 实测；坚持甲→书面改判 G4.1 |
| **2** | **A3** 行为验收不可达（`ZC-GAP-P21-A3`） | 场景门 | `ra2bench` 遭遇战不实例化预置建筑（`bld_cells≡0`）、触发器不触发、AI 不起基地 → 无法造敌方 GapGenerator / 发起 RevealArea2 | 两条出路：**C-战役**（`ra2youli` gap 农场 CAFARM02/GAGAP + PsychicReveal/TA17）或 **H-诊断钩**（受控帧 `RevealArea2 0x5678E0`，默认关、仅诊断档、需 Lead 审批）。判据已定：缝仍在 + `Cell+0x134` 不清 0；对照关补丁应 `GAP-WIPED` |
| **3** | **真机窗**预算紧 | 资源窗 | MERGE 50 条 **~12–16 h** + SOLO 18 条 **~12–14 h**（合计 **~24–30 h** 不含排障）；单局包 60–90 min；压缩 MERGE ≈13 h。并行压缩后仍 10–16 执行日 | 先关 STATIC 24 条（~30 min，零真机成本）；MERGE 优先 Top10（B-N03/N12/N13/L09/L10/L13/R03）；A3 战役轨与长跑并行准备环境 |

---

## 四、下一步

1. **推就绪卡进波**（按批次）：B2 = `ZC-H20C-SWEEP`（Track-R 单写者，T-a **必须 7B**）→ `ZC-SW-RADIUS-RC`（依赖其私有字段）→ 可选 `ZC-SW-RADIUS-RA`；同步并行 B2 面 `ZC-AUDIO-THROT` / `ZC-PART-FOG`（槽69 **LE**）。
2. **A3 破局**：拍板 C-战役 vs H-诊断钩；C 路先备 gap 农场地图 + 触发脚本，H 路出 Lead 审批申请（默认关、仅诊断档、禁 RNG）。
3. **真机窗排程**：STATIC 24 先关账；MERGE 50 按 Top10 开窗；`ZC-VXL-PRE` A4 计数器 / `ZC-SW-CHARGE-L1` A3 超武场景另卡补测（缺场景不伪造）。
4. **G-R1 待裁**：备忘已呈，等 Lead §7.1；裁决前继续维持甲姿势（全员同构建同开关 + 禁混端 + `MpActive` 强制不装 + 启动日志留痕）。
5. **代码轨串行队列**：H20C → SW-RADIUS-RC；其余二进制轨卡可并行（同一 VA 点位仍串行）。
6. **红线**：状态一律带轨名；禁「MP 可发布 / G4.1 已满足」；禁写台账/看板；勘误只增不删。

---

*产物：`docs/re/status_weekly_zcode_pack.md` + `out/re_work/re_sprint/R_weekly/**`。未改台账 `REVERSE_ENGINEERING_AND_PATCHES.md`、看板 `RE_COORDINATION.md`、landing_pack 本体、`ra2render/**`、`gamemd.exe`。*
