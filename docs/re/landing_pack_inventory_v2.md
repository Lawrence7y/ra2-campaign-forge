# Landing Pack 落地卡盘点目录 v2 · R-INV-REFRESH

> 任务：`R-INV-REFRESH` · 基线：`docs/re/dual_track_status_note.md` + `cards_inventory` + 新落地卡  
> 机读表：`out/re_work/re_sprint/R_inv_refresh/cards_inventory_v2.json`  
> 状态词（**必须带轨名**）：二进制轨 / 代码轨分列；禁止无轨名「已落地」  
> 证据基线：`gamemd.exe` 1.001 · SHA-256 `73201CC0…FCC67476` · ImageBase `0x00400000`

## 0. v2 相对 v1 变更

| # | 变更 | 依据 |
|---|---|---|
| 1 | **新卡入库** `ZC-SW-RADIUS-RA`（R-a 数据改源 Rules+0xFEC） | `landing_pack_sw_radius_ra.md` + `R_swra_card/` |
| 2 | GAP-P21/P223 **代码轨**：旧「grep 0 命中→未落地」→ 现 **已落地** | `ra2render.h:113/116/119` 三点 ADDR + `blitter_hooks.cpp:3313 InstallGapProtectionPatch` |
| 3 | `ZC-VXL-PRE`：就绪 → **二进制轨已落地 + 代码轨已落地** | `zcode_live/_code/RESULT_VXL_PRE.md`（A2 RPM `BB 40`） |
| 4 | `ZC-SW-CHARGE-L1`：就绪 → **二进制轨已落地 + 代码轨已落地** | `zcode_live/_code/RESULT_SW_CHARGE.md`（A2 RPM `90×7`） |
| 5 | `R-L4-MERGE` 代码轨：**已勘误**（L4DirtyMode 已进 ra2render；≠ 功能全装） | PATCH-R3-08 |
| 6 | `ZC-CRT-L2-C34` / `ZC-HD-DIAG` / `ZB5` 补双轨列，状态不变 | `R_l2_card/` `R_hd_card/` `R_b5_detail/` |

## 1. 状态总览（双轨分列）

### 1.1 二进制轨（zcode_live / 进程内补丁）

| 状态 | 数 | 卡 |
|---|---:|---|
| **已落地** | 5 | `ZC-GAP-P21` · `ZC-GAP-P223` · `R-GAP-MERGE` · `ZC-VXL-PRE` · `ZC-SW-CHARGE-L1` |
| **就绪** | 18 | W1–W4 主力卡 + 历史包 + ZB1–ZB4 + `ZC-SW-RADIUS-RA`(新) + `R-PROMPT-V3` 等 |
| **待批** | 4 | `ZC-SW-CHARGE-L2`(Q2) · `ZC-CRT-L2-C34`(A/B) · `ZB5-*`(DUAL-LAN) · `R-ZC-MASTER` |
| n/a | 2 | `PREFLIGHT-AUDIT` · `A-14-CRT-AUD-PART`（规格源） |

### 1.2 代码轨（ra2render 源码）

| 状态 | 数 | 卡 |
|---|---:|---|
| **已落地** | 5 | `ZC-GAP-P21` · `ZC-GAP-P223` · `R-GAP-MERGE` · `ZC-VXL-PRE` · `ZC-SW-CHARGE-L1` |
| **已勘误** | 1 | `R-L4-MERGE`（L4DirtyMode 进码；功能安装另计） |
| **未落地** | 2 | `ZC-H20C-SWEEP`（Track-R 串行待写）· `ZC-SW-RADIUS-RC`（依赖 H20C 私有字段） |
| n/a | 21 | 纯二进制轨卡 / 验收卡 / 编排件 |

### 1.3 counts 汇总

```json
{"cards_total_rows": 29, "new_in_v2": 1,
 "binary_track": {"已落地": 5, "就绪": 18, "待批": 4, "n/a": 2},
 "code_track": {"已落地": 5, "已勘误": 1, "未落地": 2, "n/a": 21}}
```

## 2. 批次/波次一览（状态带轨名）

| 批次/波 | 卡号 | VA/开关要点 | 二进制轨 | 代码轨 | 回执 |
|---|---|---|---|---|---|
| B1/W1 | `ZC-GAP-P21` | `0x568273` 6×NOP · `EnableGapProtection` | **已落地** | **已落地** | `zcode_live/gap_p21/RESULT_GAP_P21.md` |
| B1/W1 | `ZC-GAP-P21-A3` | 不改字节 · A3/A4/A5 行为验收 | 就绪 | n/a | `R_p21_a3/` |
| B1/W1 | `ZC-GAP-P223` | `0x577EC5`/`0x577B60` 各 6×NOP | **已落地** | **已落地** | `zcode_live/gap_p223/RESULT_GAP_P223.md` |
| B1 编排 | `R-GAP-MERGE` | `installed==3` | **已落地** | **已落地** | `R_gap_merge/` |
| B1/W1 | `ZC-VXL-PRE` | `0x706D78` imm8 · `EnableVxlCachePrewarm` | **已落地** | **已落地** | `zcode_live/_code/RESULT_VXL_PRE.md` |
| B2/W2 | `ZC-H20C-SWEEP` | T-a `0x6CD7C4` **7B** · `EnableRadarSweepWindow` | 就绪 | **未落地** | `R_h20c_card/` |
| B2/W2 | `ZC-SW-RADIUS-RC` | 零 .text · `RadarSweepRadiusCells` | 就绪 | **未落地** | `R_swr_card/` |
| B2/W2 可选 | `ZC-SW-RADIUS-RA` | 零 .text · `Rules+0xFEC` clamp 1..10 | 就绪 | n/a | `R_swra_card/`（**新卡**） |
| B2/W2 | `ZC-AUDIO-THROT` | AT-A/B/C · `[AudioThrottle] Enable` | 就绪 | n/a | `R_audio_card/` |
| B2/W2 | `ZC-PART-FOG` | 槽69 · `EnableParticleFog` | 就绪 | n/a | `R_part_card/` |
| B2 可选 | `ZC-SW-CHARGE-L2` | `0x6A99AC` · `EnableSWCameoCache` | **待批** Q2 | n/a | `R_sw_card/` |
| B3/W3 | `ZC-CRT-L1` | `0x4E9A10` 等 · `EnableMemoryPool` | 就绪 | n/a | `R_crt_card/` |
| B3/W4 | `ZC-SW-CHARGE-L1` | `0x6CBE88` 7×NOP · `EnableSWChargeOpt` | **已落地** | **已落地** | `zcode_live/_code/RESULT_SW_CHARGE.md` |
| B3 | `R-L4-MERGE` | OPT-1 + L4 + ZC-P1..P5 | 就绪 | **已勘误** | `R_l4_merge/` |
| B4b | `ZC-CRT-L2-C34` | idx8/9 · `MemPoolClass34` | **待批** A/B | n/a | `R_l2_card/` |
| B4c/W3 | `ZC-WPN-LW` | L-W1 四点 + L-W2/3 · 三开关 | 就绪 | n/a | `R_wpn_card/` |
| W1 诊断 | `ZC-HD-DIAG` | `0x64C6F2`/`0x64CC61` · `Sync*` | 就绪 | n/a | `R_hd_card/` |
| B5 | `ZB5-M01..M04` | 联机对拍 13 条（不装补丁） | **待批** DUAL-LAN | n/a | `R_b5_detail/` + `R_b_merge/evidence/ZB5-M0X/` |

## 3. 新卡详注（v2 新增）

### 3.1 ZC-SW-RADIUS-RA（R-a 数据改源）

| 项 | 值 |
|---|---|
| 卡号 | `ZC-SW-RADIUS-RA` |
| 优先级 | P1（可选；半径 ≤10 首选原生路径） |
| 范围 | **仅 R-a**：进程内写 `Rules+0xFEC`(i32) = `clamp(RadarSweepRadiusCells,1,10)`；保留 `SW+0xF8` float 仅瞄准圈 |
| 禁区 | 不装 R-a+ 解夹紧（`0x567A4A` 附录警告）；不做 R-c 私有扫窗；不改 `.text` |
| 二进制轨 | **就绪**（`R_swra_card/card_checklist.md` 待勾） |
| 代码轨 | n/a（纯数据写） |
| 边界 | R-a MP CONDITIONAL（全端同半径）；R-c MP SAFE；两卡独立开关独立回滚 |
| 类型陷阱 | `SW+0xF8` float ≠ `Rules+0xFEC` i32；禁止把发射半径改读 `SW+0xF8` |

### 3.2 ZC-CRT-L2-C34 / ZC-HD-DIAG / ZB5 状态确认

| 卡 | 二进制轨 | 代码轨 | 备注 |
|---|---|---|---|
| `ZC-CRT-L2-C34` | **待批** A/B | n/a | `MemPoolClass34` 默认 0；联机强制 L1-only（D-CRT-L2 RISK） |
| `ZC-HD-DIAG` | 就绪 | n/a | 与 M-8 同面勿双装；`R_hd_card/receipt_template.md` 待填 |
| `ZB5-M01..M04` | **待批** DUAL-LAN | n/a | 13 条全 [待实测]；验证≠发布 |

## 4. 历史/审计包（防重复装）

| 文件 | 标识 | 二进制轨 | 处置 |
|---|---|---|---|
| `landing_pack_gap_spysat.md` | M-10 | 就绪 | P-1 与 gap 三点同面互斥；P-2 门控另面 |
| `landing_pack_particle.md` | M-9 | 就绪 | 已被 `ZC-PART-FOG` 收敛 |
| `landing_pack_net_fix.md` | M-8 | 就绪 | 与 `ZC-HD-DIAG` 同面 |
| `landing_pack_crt_audio_particle.md` | A-14 | 就绪 | 已拆三卡；勿整包重复落地 |
| `landing_pack_preflight_audit.md` | 审计 | n/a | 17/17 PASS；须先订正 E-1..E-4 |

## 5. 硬依赖与红线

- **串行锁**：ZB1 须 gap `installed==3` → ZB2 钩后 → ZB3 L4 装后 → ZB4 L1 锁定后 → ZB5 须 DUAL-LAN。
- **G-R1**：MP 握手甲/乙未裁，裁决前不得宣称「MP 可发布」。
- **代码轨串行**：`ZC-H20C-SWEEP` 需 Track-R 单写者；`ZC-SW-RADIUS-RC` 依赖其私有字段。
- **勘误**：R-E03 T-a 必须 7B；R-E08 槽69 用 LE；R-E10 用 `0F B6 C0`。
- **禁混称**：状态必须带轨名；禁止用二进制收据证明代码轨（或反向）。

*产物：`out/re_work/re_sprint/R_inv_refresh/**` + 本文。未改台账/看板/landing_pack 本体/ra2render/zcode_live。*
