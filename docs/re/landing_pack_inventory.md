# Landing Pack 落地卡盘点目录 · R-CARD-INV

> 任务：`R-CARD-INV` · 范围：`docs/re/landing_pack_*.md`（20）+ `zcode_*ticket/prompt*`（3）  
> 机读表：`out/re_work/re_sprint/R_card_inv/cards_inventory.csv` / `cards_inventory.json`  
> 状态词：**已落地**（真机装上且有 RESULT）/ **就绪**（静态 MATCH + 卡面齐，可派）/ **待批**（须 Lead/门禁/A-B）  
> 证据基线：`gamemd.exe` 1.001 · SHA-256 `73201CC0…FCC67476` · ImageBase `0x00400000`

## 1. 状态总览

| 状态 | 数 | 卡 |
|---|---:|---|
| **已落地** | 3 | `ZC-GAP-P21` · `ZC-GAP-P223` · `R-GAP-MERGE`（installed=3） |
| **就绪** | 20 | W1–W4 主力卡 + 历史包 + 挂载验收 ZB1–ZB4 + `R-PROMPT-V3` |
| **待批** | 4 | `ZC-SW-CHARGE-L2`(Q2) · `ZC-CRT-L2-C34`(A/B) · `ZB5-*`(DUAL-LAN) · `R-ZC-MASTER`(Lead 派发) |
| n/a | 1 | `PREFLIGHT-AUDIT`（审计件；E-1..E-4 须先订正） |

## 2. 批次/波次一览（以 v2 B1–B5 / v3 W1–W4 为准）

| 批次/波 | 卡号 | VA/开关要点 | 状态 | 回执 |
|---|---|---|---|---|
| B1 / W1 | `ZC-GAP-P21` | `0x568273` 6×NOP · `EnableGapProtection` | **已落地** | `zcode_live/gap_p21/RESULT_GAP_P21.md` |
| B1 / W1 | `ZC-GAP-P21-A3` | 不改字节 · A3/A4/A5 战役轨 C | 就绪 | `R_p21_a3/` + `zcode_live/gap_p21_a3/` |
| B1 / W1 | `ZC-GAP-P223` | `0x577EC5`/`0x577B60` 各 6×NOP | **已落地** | `zcode_live/gap_p223/RESULT_GAP_P223.md` |
| B1 编排 | `R-GAP-MERGE` | `installed==3` 三点合并 | **已落地** | `R_gap_merge/` |
| B1 / W1 | `ZC-VXL-PRE` | `0x706D78` imm8 · `EnableVxlCachePrewarm` | 就绪 | `R_vxl_card/` |
| B2 / W2 | `ZC-H20C-SWEEP` | T-b `0x6CB920`/`0x6CC390` 或 T-a `0x6CD7C4` **7B** · `EnableRadarSweepWindow` | 就绪 | `R_h20c_card/` |
| B2 / W2 | `ZC-SW-RADIUS-RC` | 零 .text · `RadarSweepRadiusCells` | 就绪 | `R_swr_card/` |
| B2 / W2 | `ZC-AUDIO-THROT` | AT-A/B/C `0x750920/0x7509E0/0x750E20` · `[AudioThrottle] Enable` | 就绪 | `R_audio_card/` |
| B2 / W2 | `ZC-PART-FOG` | 槽69 `0x7EFA68`/`0x7EFCB0` · `EnableParticleFog` | 就绪 | `R_part_card/` |
| B2 可选 | `ZC-SW-CHARGE-L2` | `0x6A99AC` · `EnableSWCameoCache` | **待批** Q2 | `R_sw_card/` |
| B3 / W3 | `ZC-CRT-L1` | `0x4E9A10`/`0x4E97B0`/`0x6F8F8A` · `EnableMemoryPool` | 就绪 | `R_crt_card/` |
| B3 / W4 | `ZC-SW-CHARGE-L1` | `0x6CBE88` 7×NOP · `EnableSWChargeOpt` | 就绪 | `R_sw_card/` |
| B3 | `R-L4-MERGE` | OPT-1 + L4 + ZC-P1..P5 · `L4DirtyMode` | 就绪 | `R_l4_merge/` |
| B4b | `ZC-CRT-L2-C34` | idx8/9 · `MemPoolClass34` | **待批** A/B | `R_l2_card/` |
| B4c / W3 | `ZC-WPN-LW` | L-W1 四点 + L-W2/3 · 三开关 | 就绪 | `R_wpn_card/` |
| W1 诊断 | `ZC-HD-DIAG` | `0x64C6F2`/`0x64CC61` · `SyncEarlyLog` 等 | 就绪 | `R_hd_card/` |
| B5 | `ZB5-M01..M04` | 联机对拍/逻辑回归（不装补丁） | **待批** DUAL-LAN | `R_b_merge/evidence/ZB5-M0X/` |

## 3. 历史/审计包（非 v3 十卡队列，防重复装）

| 文件 | 标识 | 处置 |
|---|---|---|
| `landing_pack_gap_spysat.md` | M-10（P-1/P-2/P-3） | P-1 与 gap 三点同面，勿重复装；P-2 门控另面 |
| `landing_pack_particle.md` | M-9 | 执行包，已被 `ZC-PART-FOG` 收敛 |
| `landing_pack_net_fix.md` | M-8 | 字节级执行包，与 `ZC-HD-DIAG` 同面 |
| `landing_pack_crt_audio_particle.md` | A-14 三合一 | 规格源，已拆 `ZC-CRT-L1`/`ZC-AUDIO-THROT`/`ZC-PART-FOG` |
| `landing_pack_preflight_audit.md` | 静态复核 | 17/17 字节 PASS；落地前须订正 E-1..E-4 |

## 4. 编排件

| 文件 | 卡号 | 状态 | 回执 |
|---|---|---|---|
| `zcode_master_implementation_ticket.md` | `R-ZC-MASTER` v1 | 历史基线 | — |
| `zcode_master_implementation_ticket_v2.md` | `R-ZC-MASTER` v2（B1–B5） | **待批** Lead 派发 | `R_ticket_upd/` |
| `zcode_parallel_prompt_v3.md` | `R-PROMPT-V3`（W1–W4 四轨） | 就绪·可粘贴派发 | `R_prompt_v3/` |

## 5. 硬依赖与红线（盘点口径）

- **串行锁**：ZB1 须 gap `installed==3` → ZB2 须 audio/particle 钩后 → ZB3 须 L4/OPT-1 装后 → ZB4 须 L1 锁定后 → ZB5 须 DUAL-LAN。
- **G-R1**：MP 握手甲/乙未裁，裁决前不得宣称「MP 可发布 / G4.1 已满足」。
- **G-R2**：gap = VIOLATION 禁混端；audio/particle/vxl/H20C/SW-CHARGE = SAFE。
- **勘误**：R-E03 T-a 必须 7B；R-E08 槽69 用 LE；R-E10 用 `0F B6 C0`；装卡以 `errata_sync_master_table.md` 新文为准。

*盘点产物：`out/re_work/re_sprint/R_card_inv/**` + 本文。未改任何 landing_pack 冻结源/台账/看板/ra2render。*
