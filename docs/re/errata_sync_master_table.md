# 勘误总表 · R-ERRATA-SYNC

> [META]
> 任务=R-ERRATA-SYNC · 日期 2026-09-30 · 性质=**只登记不就地改**（docs/re 冻结源不动）
> 上游散落勘误来源：deep_dive / landing_pack / fix_spec / sprint 报告 / errata_* 既有补丁块
> 可写域：本文 + `out/re_work/re_sprint/R_errata_sync/**`
> 禁写：台账 / 看板 / 已有 deep_dive 本体 / 台账 `REVERSE_ENGINEERING_AND_PATCHES.md`
> 状态列含义：**已加注** = 源文档或其紧邻文档已有【勘误】块；**未加注** = 仅在下游报告登记，冻结源仍写旧文；**代码轨已勘误** = 现码/落地包已用新值

---

## 一、勘误主表

| ID | 主题 | 源文档:行 | 旧文 | 新文 | 证据 | 已就地加注 | 优先级 | 波及文件 |
|:---:|:---|:---|:---|:---|:---|:---|:---:|:---|
| **R-E01** | `0x568297`→`0x56829A` | `landing_pack_gap_p21.md:39,47`；`gap_psychic_reveal_deep_dive.md` §3.3；`landing_pack_gap_merge_checklist.md:37`；`gap_protection_install_spec.md:39` | `0x568297` = `or [ecx+0x12C],0x10` | 实际 VA **`0x0056829A`**；`0x568297` 处是 `50 DC AB 00`（`mov ecx,0xABDC50` 尾巴） | `RESULT_GAP_P21.md` §5 E-1；`p223_readiness_check.md:105`；`landing_pack_gap_p21_a3.md:205` | **未加注**（冻结卡）；**代码轨已勘误**（`ra2render.h:96` / `ra2render.ini:140` / 日志 `:591` 均 0x56829A） | P0 | 同左 4 文件；G0 门禁不引用此 VA，无落地风险 |
| **R-E02** | 上下文窗 21B→17B | `landing_pack_gap_p21.md:32`「共 21B」；`gap_protection_install_spec.md:31`「21B 自检」 | 上下文窗共 **21B** | 指令对齐合计 **17B**（2+6+2+7）；首末跨度另计 45B，不可混用 | `RESULT_GAP_P21.md` §5 E-2；`p223_readiness_check.md:106` | **未加注** | P1 | 同左 2 文件 |
| **R-E03** | T-a 指令长度 5B→7B | `radar_sweep_sw_deep_dive.md:120,140,204`（写「5B」） | `0x6CD7C4` 处 5B 补丁点 | 该指令为 **7B** `mov al,[esp+0x1EC]`（`8A 84 24 EC 01 00 00`）；T-a **必须 7B**（`E9`+2×`90`），禁 5B 切断指令 | `h20c_private_sweep_spec.md:40-43`（已自带勘误）；`R_h20c/EVIDENCE_INDEX.md:18`；`zcode_master_implementation_ticket_v2.md:73` | **部分**：`h20c_private_sweep_spec` / ticket v2 已注「旧文 5B 为勘误」；`radar_sweep_sw_deep_dive.md` **仍写 5B 未加注** | P0 | `radar_sweep_sw_deep_dive.md`；`s_origCase11Bytes[5]`→`[7]` |
> 【W3 勘误 · W3-A6/ISSUE-RADAR-SWEEP-5B】改前：0x6CD7C4` 处 5B；改后：0x006CD7C4 处指令为 7B (8A 84 24 EC 01 00 00)；依据：ra2youli/gamemd.exe:0x2CD7C4; errata_sync_master_table.md:18 (R-E03); h20c_private_sweep_spec.md:40-43；分级：P0
| **R-E04** | `SW+0xF8` 死键 | `sw_radius_deadkey_fix_spec.md:14,44-45,133`；`radar_sweep_sw_deep_dive.md:13,80,92-94` | `RadarSweepRadiusCells` 写 `SW+0xF8` 可改开图/杀伤半径 | **死写**：12/12 发射 case 均不读 `+0xF8`；唯一活消费 = 鼠标瞄准圈 `fld [edi+0xF8]@0x6DC1C6`。真实开图半径 = `Rules+0xFEC`（i32），被 `min(10,·)` 夹紧。`SW+0xF8`=float ≠ `Rules+0xFEC`=i32 | `sw_radius_deadkey_fix_spec.md` §1/§2（定谳）；`radar_sweep_sw_deep_dive.md` §3.1；`gap_psychic_reveal_deep_dive.md:124`（C-4） | **已加注**（fix_spec 本身就是勘误定谳文档；deep_dive 亦已写「死写」） | P1 | `ra2render.ini:93` 注释需改「瞄准圈显示半径（UI-only）」 |
| **R-E05** | `fx_draw_chain:91` 过滤对象写反 | `fx_draw_chain.md:91` | 「`0x6D97D0`/`0x6D9920` 过滤 `WhatAmI==0x24`」 | **反了**：`0x6D9920` 滤 **Building(6)**（`cmp eax,6`@`0x6D997C`）；`0x6D97D0` 滤 **Terrain(0x24)**（`cmp eax,0x24`@`0x6D982A`） | `render_second_pass_deep_dive.md:93-95,237` | **未加注**（fx_draw_chain 本体冻结；render_second_pass 有勘误块） | P1 | `fx_draw_chain.md:91`；Hook 覆盖面描述 |
> 【W3 勘误 · W3-A6/ISSUE-FX-FILTER-REVERSED】改前：0x6D97D0`/`0x6D9920` 过滤 `WhatAmI==0x24；改后：0x6D9920 滤 Building(6)；0x6D97D0 滤 Terrain(0x24)；依据：ra2youli/gamemd.exe:0x2D997C, 0x2D982A; errata_sync_master_table.md:20 (R-E05)；分级：P1
| **R-E06** | `_delete@0x7C8B3D` 计数口径 Δ=1 | 旧文多处写 `_delete` 调用 **4498** 处（线性口径） | 线性反汇编 4498 | 模式扫描真值 **≥ 4499**；多出的第 4499 处 = **`0x0074836A`**（`E8 CE 07 08 00`，全局指针单例释放）。线性口径在 `0x0074835A` 相位脱节漏记 | `ARCHITECTURE_ATLAS.md:4472-4478`（Δ=1 定谳）；`atlas_rev/R8_ui_crt.md:330` | **已加注**（ATLAS 内已有定谳注记） | P2 | 引用静态量级时须标口径（相对差 0.02%，不影响池化决策） |
| **R-E07** | Verses 施加点 8 处→**9 处** | `warhead_abi_verses_deform_deep_dive.md:19,110`（「8 处」）；`errata_from_rtrack.md:14,24`（「8 处」）；`iface_mimo_re.md:141`（「8 处」） | Verses FPU 索引访存 **8 处** | **9 处**（V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c）。R-03 §0 写「8」但 §3.2 表实列 9 行，系汇总笔误 | `warhead_verses_residual_p2.md:18,58`（计数勘误）；同文 §1.2 九处站点总表 | **未加注**（deep_dive 仍写 8；residual_p2 已更正） | P1 | 伤害优化前置口径；E-2-S 补丁块「8 处」字样需同步改 9 |
> 【W3 勘误 · W3-A6/ISSUE-VERSES-SITES-COUNT】改前：Verses 施加点 8 处；改后：Verses FPU 索引访存共 9 处 (V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c)；依据：errata_sync_master_table.md:22 (R-E07); warhead_verses_residual_p2.md:18, 58；分级：P1
| **R-E08** | 槽 69 原 DWORD 字节序 BE→LE | `landing_pack_particle.md:66,67`（曾写 BE `00 62 CE C0`/`00 62 E2 80`） | `00 62 CE C0` / `00 62 E2 80`（大端书写） | **LE** `C0 CE 62 00` / `80 E2 62 00`（= DWORD `0x0062CEC0` / `0x0062E280`）。BE 照抄会写入 `0xC0CE6200` → 崩 | `gamemd.exe` 机读；`anchor_claims.txt:72-73`；`FIXPACK_F01-F13_report.md` F-04；`landing_pack_particle_fog.md:35`（字节序红线） | **已加注**（F-04 订正 9 处，含勘误块） | P0 | `landing_pack_particle.md`；`landing_pack_particle_fog.md`；回滚写回值 |
> 【W3 勘误 · W3-A6/ISSUE-PARTICLE-BE-BYTES】改前：00 62 CE C0；改后：C0 CE 62 00 / 80 E2 62 00 (小端 LE)；依据：errata_sync_master_table.md:23 (R-E08); FIXPACK_F01-F13_report.md F-04；分级：P0
| **R-E09** | `OccuredEvents` 位序 = 事件链位次 | 早期文档未钉死位序语义；`trigger_system_manifest.md:55` 另有字段名双重错误（DA2-T1 已勘误） | （隐含）位序或与 event kind 号相关 / 未明确 | **硬不变量**：`bit i` = 事件链中第 i 个 Event 是否已发生（**与 kind 数值无关**，`ebx` 逐轮 `inc`）。`[Events]` 序重排 = 位图整体错位 | `trigger_runtime_deep_dive.md:161`；`trigger_save_pollution.md:121-123`（G6）；`ARCHITECTURE_ATLAS.md:2758`（C10）；`0x72650B = D3 E5`（`1<<eventIndex`） | **已加注**（新文档均已钉死；`trigger_system_manifest` DA2-T1 已修字段名） | P0 | 存档敏感序三元组；禁重排 `[Events]` |
| **R-E10** | H-D5 取模 `83 E0 FF`→`0F B6 C0` | 旧落地包 `landing_pack_net_fix.md` 草案 / `calc_tramp_bytes.py` / S15 TRAMP_HD5 草案 | `83 E0 FF`（注释写 `and eax,0xFF`） | **`0F B6 C0`**（`movzx eax,al`）。`83 /4 ib` 立即数符号扩展 ⇒ `and eax,0xFFFFFFFF` = **no-op**，高位不清零 → 帧>255 越界写 → 1024 帧 `0xC0000005` | `landing_equivalence_static_proof.md:90-93`；`cross_doc_consistency_audit.md:291-293,401`；`ARCHITECTURE_ATLAS.md:315,2172`；Lead v20-v22 裁决 | **已加注**（`landing_pack_net_fix.md:400` 已含勘误修复注；多份报告已写） | P0 | 跳板 `+0x10`；TC-ST-01 一票否决；`pending_execution_master_table.md:41` |

---

## 二、按「是否可加注」分组（给 Lead 的清单）

### A. 建议就地加注（冻结源解冻后粘贴）— 优先

| ID | 目标文件 | 建议动作 |
|:---:|:---|:---|
| R-E01 | `landing_pack_gap_p21.md:39,47` + 3 处波及 | 行内改 VA 或加【勘误】块：`0x568297`→`0x0056829A` |
| R-E02 | `landing_pack_gap_p21.md:32` + `gap_protection_install_spec.md:31` | 「21B」→「指令对齐 17B（2+6+2+7）」 |
| R-E03 | `radar_sweep_sw_deep_dive.md:120,140,204` | 5B→7B 加勘误块（参照 `h20c_private_sweep_spec.md:40-43` 格式） |
| R-E05 | `fx_draw_chain.md:91` | 加勘误块：两处过滤对象写反 |
| R-E07 | `warhead_abi_verses_deform_deep_dive.md:19,110` 等 | 「8 处」→「9 处」+ 计数勘误注 |

### B. 已自带加注 / 不必再动

| ID | 状态 |
|:---:|:---|
| R-E04 | `sw_radius_deadkey_fix_spec.md` 即定谳文档 |
| R-E06 | ATLAS Δ=1 定谳注已在 |
| R-E08 | F-04 已订正 9 处 |
| R-E09 | 新文档 + DA2-T1 已钉 |
| R-E10 | `landing_pack_net_fix.md:400` 已含修复注 |

### C. 仅登记不改（历史产物 / 口径说明）

| ID | 说明 |
|:---:|:---|
| R-E06 | 引用 4498 时标口径即可，不回改历史扫描报告 |
| R-E10 | S15/S18 历史报告保留原样作时间线 |

---

## 三、建议批量执行顺序

> 原则：**先 P0 机器码/地址级 → 再 P0 语义不变量 → 再 P1 计数/长度 → 最后 P2 口径**。
> 同一波内按「同一文件多条合并一次加注」减少冻结源开封次数。

| 批次 | 内容 | 条目 | 理由 |
|:---:|:---|:---|:---|
| **W1** | 地址/机器码级勘误（落地风险最高） | R-E01, R-E03, R-E08, R-E10 | 直接影响补丁写窗/回滚；代码轨多已勘误，文档补齐即可闭环 |
| **W2** | 语义不变量 / 红线 | R-E04, R-E09 | 死键与位序是产品/存档红线，错用必炸 |
| **W3** | 计数与长度 | R-E02, R-E05, R-E07 | 不影响落地字节，但影响阅读与优化前置口径 |
| **W4** | 口径注记（可选） | R-E06 | 仅需「标口径」，不改历史 |

**每批验收**：① 补丁块前 40 字符锚点可定位；② 原文保留不删字；③ 波及文件全覆盖；④ 不触碰台账/看板。

---

## 四、与既有补丁包的关系

| 既有包 | 覆盖条目 | 本表增量 |
|:---|:---|:---|
| `errata_patch_blocks_E1E2.md`（E-1~E-9+T1） | Blitter 12B、Verses +0xB0→+0xA0、Deform、ATLAS mermaid 等 | **不重叠**（本表 10 条均为其后新发现） |
| `errata_from_rtrack.md`（E-8-D / E-2-S / E-ABI-AC） | Deform 定谳、Verses 施加点补记 | R-E07 修正其「8 处」→「9 处」 |
| `errata_result_zc11.md`（E-ZC11-7a~d） | ZC11 零崩溃宣称订正 | 不重叠 |
| `R_p223_ready/errata_sync.md`（E-1~E-3） | 0x56829A / 17B / 挂点行号 | **收编为 R-E01/R-E02**（R-E03 挂点行号不在本轮 10 条内，保留原表） |
| `FIXPACK_F01-F13`（F-04） | 槽 69 LE | **收编为 R-E08** |

---

## 五、产物索引

| 产物 | 路径 |
|:---|:---|
| 本总表 | `docs/re/errata_sync_master_table.md` |
| 工作副本 + 逐条证据摘录 | `out/re_work/re_sprint/R_errata_sync/evidence_index.md` |
| 建议可加注清单（Lead 用） | `out/re_work/re_sprint/R_errata_sync/annotate_list_for_lead.md` |
| 批量执行顺序卡 | `out/re_work/re_sprint/R_errata_sync/batch_order.md` |
