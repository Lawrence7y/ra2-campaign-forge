# R-B-MERGE · MERGE 50 条挂总实施票批次 · ZCode 可执行子卡

> **任务号**：`R-B-MERGE` · **产物**：本文件 + `out/re_work/re_sprint/R_b_merge/**`
> **源（只读，本任务未改）**：`docs/re/b_class_live_test_index.md` §2/§4 MERGE 桶 50 条 · `docs/re/zcode_master_implementation_ticket.md` B1–B4 · `out/re_work/re_sprint/R_b_index/b92_catalog.tsv` · `buckets_top10.md` §2.2
> **纪律**：不伪造「实测」；本文件只做**编排与挂载**，判据原样引自索引，执行回执由 ZCode 真机补写。禁写台账/看板/ra2render/gamemd。
> **机读映射**：`out/re_work/re_sprint/R_b_merge/merge50_batch_map.tsv` · **派发视图**：`cards_dispatch.md`

---

## 0. 总裁定

| 指标 | 值 |
|---|---:|
| MERGE 条数（挂载覆盖） | **50 / 50** |
| 拆成 ZCode 子卡 | **14**（ZB1-M01 … ZB5-M04） |
| 并入既有批 B1 | 1 卡 · 4 条 |
| 并入既有批 B2 | 4 卡 · 14 条 |
| 并入既有批 B3 | 3 卡 · 12 条 |
| 并入既有批 B4 | 2 卡 · 7 条 |
| **新建 B5**（联机对拍/逻辑回归） | **4 卡 · 13 条** |
| 压缩后真机窗口合计 | **≈13 h**（与索引 §6 的 12–16 h 一致） |

**为何新建 B5**：B1–B4 分别对应「gap/VXL · audio/particle · L4/OPT-1 · mem/wpn」四个实施面；余下 6 条联机对拍 + 7 条核心逻辑回归（寻路/空间/AI/超武/存档）验证的是**同步确定性与玩法逻辑**，不是 B1–B4 任一补丁的直接验收面，且依赖 DUAL-LAN/套件一独立场次。故新建 **B5 联机对拍与逻辑回归批**，与 B1–B4 并行排期，但 **MP 发布宣称仍以 G-R1 裁决为唯一门**。

---

## 1. 批次归属总表（50 条全量）

| 批次 | 子卡 | 覆盖 MERGE ID | 条数 | 挂载点 |
|---|---|---|---:|---|
| **B1** 并入 | ZB1-M01 | B-L09, B-L10, B-L15, B-R30 | 4 | ZC-GAP-P21/P223 A3-A5 · 套件五 |
| **B2** 并入 | ZB2-M01 | B-A01, B-A02, B-A05, B-A08, B-A09, B-A13 | 6 | ZC-AUDIO-THROT · 套件三 |
| **B2** 并入 | ZB2-M02 | B-A10, B-A12, B-A14 | 3 | ZC-AUDIO-THROT · ZC-1 |
| **B2** 并入 | ZB2-M03 | B-R15, B-R21, B-L12, B-L13 | 4 | ZC-PART-FOG · 套件五 · Q3③ |
| **B2** 并入 | ZB2-M04 | B-R16 | 1 | ZC-PART-FOG · 套件二 |
| **B3** 并入 | ZB3-M01 | B-R01, B-R02, B-R03, B-R06, B-R11 | 5 | R-L4-MERGE · 套件二 |
| **B3** 并入 | ZB3-M02 | B-R23, B-R24, B-R26, B-R27, B-R29 | 5 | 套件二 · ZC-1 |
| **B3** 并入 | ZB3-M03 | B-R08, B-R25 | 2 | harness --ab-simd · RELOAD5 |
| **B4** 并入 | ZB4-M01 | B-M01, B-M02, B-M03, B-M07, B-M09, B-M10 | 6 | R-CRT-POOL L1 · 套件四 · EXCEPT-AB |
| **B4** 并入 | ZB4-M02 | B-M12 | 1 | ZC-1 Q5 |
| **B5** 新建 | ZB5-M01 | B-N03, B-N10, B-N11 | 3 | 套件一 · DUAL-LAN · Q6 |
| **B5** 新建 | ZB5-M02 | B-N12, B-N13, B-N17 | 3 | ZC-1 Q2 · 套件一 |
| **B5** 新建 | ZB5-M03 | B-L01, B-L02, B-L05, B-L06 | 4 | 套件五 |
| **B5** 新建 | ZB5-M04 | B-L07, B-L08, B-L14 | 3 | 套件一 · ZC-1 可加 |
| **合计** | **14 卡** | — | **50** | — |

### 1.1 归属原则

1. **测什么补丁 → 挂哪批**：gap/SpySat/裂缝玩法 → B1；音频钩与粒子雾 Draw → B2；视口/脏矩形/雷达 UI → B3；堆/池/长跑 → B4；同步对拍与纯逻辑 → B5。
2. **双面条目从主面**：B-L13（己方零误杀）兼测微粒与 gap 边缘，主面是粒子 Draw 剔除（ZC-PART-FOG）→ B2；B-L15（变卖地基）主面是 gap/建筑占格释放 → B1。
3. **不改索引判据**：本编排只做挂载与分卡，判据/步骤/窗口原文引自 `b_class_live_test_index.md` §4；压缩窗口仅标注「同场次可合并」，不改单项分钟数。
4. **Top10 优先**：索引 §3 Top10 中属 MERGE 的 9 条（B-N11/N03/N12/N13/L09/L10/L13/M07/R03）在其所属子卡内标 `★`，执行序优先。

---

## 2. 子卡全文（14 张）

> 字段固定五项：**前置 / 步骤 / 判据 / 窗口 / 产物路径**。步骤编号即执行序；`★` = Top10 优先。

### ZB1-M01 · gap/SpySat/裂缝玩法验收（并入 B1）

| 项 | 内容 |
|---|---|
| **批次** | B1（`ZC-GAP-P21`→`ZC-GAP-P223` 同装后） |
| **覆盖** | ★B-L09 · ★B-L10 · B-L15 · B-R30 |
| **前置** | ① B1 三点已装且 `gapProtectionPatchesInstalled==3`；② `[FogOfWar] EnableGapProtection=1`（init 锁定）；③ ZC-1 Q3 场景包就绪（间谍卫星/裂缝+PsychicReveal/变卖/建筑打爆）；④ 套件五可读 `House+0x577A`、`Cell+0x134` |
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0
| **步骤** | 1. ★**B-L09**：建造间谍卫星并通电 → 肉眼+遥测确认小地图不整亮；读 `House+0x577A`。<br>2. ★**B-L10**：裂缝区施放 PsychicReveal，扫描退去后观察黑雾 → 必须 100% 全黑恢复；读 `Cell+0x134≥1`。<br>3. **B-L15**：变卖裂缝生成器/建筑 → 部队可立刻驶入原地基，无隐形阻挡。<br>4. **B-R30**：迷雾内建筑打爆后再探雾 → 残影瞬时消失，无像素泄漏。 |
| **判据** | L09：小地图不整亮且 `House+0x577A` 不置 1。L10：扫描退去 100% 全黑恢复，`Cell+0x134≥1`。L15：阻塞 100% 解除。R30：残影瞬时消失。收尾 `except.txt` 0 字节。**禁「没崩当成功」**。 |
| **窗口** | 60m（单场次压缩；索引单项合计 20+25+15+15=75m） |
| **产物路径** | `out/re_work/re_sprint/R_b_merge/evidence/ZB1-M01/`（spy_sat_house.bin · gap_cell134.txt · sell_foundation.md · fog_residual.png · result.md） |

---

### ZB2-M01 · 音频通道池/限频/EVA（并入 B2）

| 项 | 内容 |
|---|---|
| **批次** | B2（`ZC-AUDIO-THROT` AT-A/B/C 三钩后） |
| **覆盖** | B-A01 · B-A02 · B-A05（备选） · B-A08 · B-A09 · B-A13 |
| **前置** | ① AT-A `0x750920`/AT-B `0x7509E0`/AT-C `0x750E20` 已装；② `[AudioThrottle] Enable=1`，`MaxVoicePerFrame=6`/`VoiceDedupMs=80`/`MaxSamePerWindow=2`/`WhitelistPriorityMin=3`；③ 套件三齐射/核爆/满载场景；④ 两池 200 槽压力场景 |
| **步骤** | 1. **B-A01**：套件三采样 `activeAudioChannels` 活跃曲线。<br>2. **B-A02**：持续高压压满 300 槽。<br>3. **B-A05**（备选）：齐射核爆+重机枪盲测限频听感。<br>4. **B-A08**：300 槽满载时播 EVA。<br>5. **B-A09**：核弹警报 vs 建造完成音，测打断。<br>6. **B-A13**：100 坦克决战+铁幕就绪，测战术警笛。 |
| **判据** | A01：活跃 10~50，极端≤280，无泄漏。A02：满载零卡顿无闪退。A05：无噼啪，警报无吞音。A08：EVA 100% 播报。A09：警报瞬间打断、平滑插队无杂音。A13：警笛 100% 触发播报。两池压力下降方向可报（不承诺百分比）。`except.txt` 空。 |
| **窗口** | 90m（单项合计 20+20+25+20+20+25=130m，同场次压缩） |
| **产物路径** | `out/re_work/re_sprint/R_b_merge/evidence/ZB2-M01/`（channel_pool.csv · throttle_listen.md · eva_stream.txt · alarm_trace.md · result.md） |

---

### ZB2-M02 · 音频混音/3D/失焦（并入 B2）

| 项 | 内容 |
|---|---|
| **批次** | B2（同 ZB2-M01 钩） |
| **覆盖** | B-A10 · B-A12 · B-A14 |
| **前置** | ① 同 ZB2-M01 前置；② ZC-1 任意局可进；③ ALTTAB 切换可用 |
| **步骤** | 1. **B-A10**：拖动 BGM/音效音量滑块。<br>2. **B-A12**：左/右侧爆炸听感，测 Pan+Volume 衰减。<br>3. **B-A14**：Alt-Tab 切出/切回。 |
| **判据** | A10：mB 线性平滑无突跳。A12：左爆左响，超射程无混音开销。A14：切出即停、切回无缝恢复。`except.txt` 空。 |
| **窗口** | 35m（10+15+10） |
| **产物路径** | `out/re_work/re_sprint/R_b_merge/evidence/ZB2-M02/`（mb_mix.md · pan_distance.md · alttab_mute.md · result.md） |

---

### ZB2-M03 · 粒子雾剔除/生命周期/零误杀（并入 B2）

| 项 | 内容 |
|---|---|
| **批次** | B2（`ZC-PART-FOG` 槽 69 两钩后，`EnableParticleFog=1`） |
| **覆盖** | B-R15 · B-R21 · B-L12（兼） · ★B-L13 |
| **前置** | ① 槽 69 `0x7EFA68`/`0x7EFCB0` Draw 虚表钩已装（未碰已装五槽）；② `EnableParticleFog=1`；③ ZC-1 Q3③ 黑雾边缘场景；④ 套件五粒子计数遥测可用 |
| **步骤** | 1. **B-R15**：隐形单位移动，观察 Anim 跳过绘制。<br>2. **B-R21**：敌方尾烟穿雾分界，观察裁剪边界。<br>3. **B-L12**（兼 L13）：迷雾内持续交火，采活跃粒子数。<br>4. ★**B-L13**：黑雾边缘己方/盟友开火，看尾烟。 |
| **判据** | R15：无像素泄露，倒计时正常。R21：剔除/显现边界平滑无闪烁。L12：活跃粒子稳定 50~200，无永生堆积。L13：己方尾烟 100% 清晰可见（零误杀）。生成侧 PRNG **照常消费**（无 SYNC 异常）。两局 `except.txt` 空。 |
| **窗口** | 55m（单项合计 15+15+25+20=75m，同场次压缩） |
| **产物路径** | `out/re_work/re_sprint/R_b_merge/evidence/ZB2-M03/`（anim_skip.png · fog_clip_boundary.png · particle_count.csv · friendly_trail.png · result.md） |

---

### ZB2-M04 · 特效屏外销毁（并入 B2）

| 项 | 内容 |
|---|---|
| **批次** | B2（同 ZB2-M03 钩） |
| **覆盖** | B-R16 |
| **前置** | ① ZC-PART-FOG 已装；② 套件二 `particlesCulledByFog` 遥测可读 |
| **步骤** | 1. **B-R16**：在视口外触发爆炸，计时至生命周期结束。 |
| **判据** | 生命周期结束 100% 正常销毁，无永生残留；遥测计数可见。`except.txt` 空。 |
| **窗口** | 15m |
| **产物路径** | `out/re_work/re_sprint/R_b_merge/evidence/ZB2-M04/`（offscreen_destroy.md · result.md） |

---

### ZB3-M01 · 渲染核心/脏矩形/L4 保底（并入 B3）

| 项 | 内容 |
|---|---|
| **批次** | B3（`R-L4-MERGE` L4 桩 + OPT-1 双钩后） |
| **覆盖** | B-R01 · B-R02 · ★B-R03 · B-R06 · B-R11 |
| **前置** | ① L4 桩 + OPT-1 两点已装；② `L4DirtyMode` 按批 D 放行前固定 `force-full`，对照组 `vision-dirty` 须批 D 全绿后才可测；③ 套件二遥测三指标（`ddrawLockCountPerFrame`/`tacticalFullRedrawFrames`/`fullRedrawTriggered`）；④ `bench_metrics` 可用 |
| **步骤** | 1. **B-R01**：套件二遥测采样 DDraw Lock 争用。<br>2. **B-R02**：大范围翻转+卷屏，采 `tacticalFullRedrawFrames`。<br>3. ★**B-R03**：SpySat/心灵探测/快速卷屏，看 `fullRedrawTriggered` 与残影。<br>4. **B-R06**：右边界贴边单位压测 zmap。<br>5. **B-R11**：`bench_metrics` 采帧时抖动序列。 |
| **判据** | R01：`ddrawLockCountPerFrame≤2`，无撕裂。R02：超阈值帧单调递增。R03：`fullRedrawTriggered==1`，零残影黑块。R06：右边界 0 崩溃、无越界读。R11：抖动 std<1.5ms，无垂直撕裂。`except.txt` 空。 |
| **窗口** | 70m（单项合计 15+15+20+20+20=90m，含对照压缩） |
| **产物路径** | `out/re_work/re_sprint/R_b_merge/evidence/ZB3-M01/`（ddraw_lock.csv · full_redraw.csv · l4_350.png · zmap_edge.md · vsync_jitter.csv · result.md） |

---

### ZB3-M02 · 雷达/Cameo/CanBuild/光标（并入 B3）

| 项 | 内容 |
|---|---|
| **批次** | B3（同 ZB3-M01 钩；纯渲染 UI 回归） |
| **覆盖** | B-R23 · B-R24 · B-R26 · B-R27 · B-R29 |
| **前置** | ① 套件二可读雷达绘制耗时；② ZC-1 任意局；③ 平民 1000+ 与单位>1500 压力场景 |
| **步骤** | 1. **B-R23**：单位>1500 雷达全开，采绘制耗时。<br>2. **B-R24**：建造/资金变化，观察 Cameo 重绘。<br>3. **B-R26**：平民 1000+，观察雷达标志。<br>4. **B-R27**：断电/恢复供电。<br>5. **B-R29**：日常光标移动。 |
| **判据** | R23：雷达绘制<0.1ms。R24：进度平滑，无多余全量重绘。R26：无关点零上屏，帧率无抖动。R27：实时变黑/点亮。R29：无拖尾黑框。`except.txt` 空。 |
| **窗口** | 50m（单项合计 20+15+15+10+10=70m，压缩） |
| **产物路径** | `out/re_work/re_sprint/R_b_merge/evidence/ZB3-M02/`（radar_dots.csv · cameo_dirty.md · civ_filter.md · canbuild.md · cursor_ghost.md · result.md） |

---

### ZB3-M03 · SSE2 等价 + 地基 22 槽（并入 B3）

| 项 | 内容 |
|---|---|
| **批次** | B3（渲染等价/多局稳定性） |
| **覆盖** | B-R08 · B-R25 |
| **前置** | ① ZC-1 harness `bench_replay --ab-simd` + `bench_diff` 可用；② RELOAD5 进出战局协议可执行 |
| **步骤** | 1. **B-R08**：`--ab-simd` A/B 对拍 + `bench_diff` 逐位比对。<br>2. **B-R25**：连续 5 次进出战局，采地基 22 槽向量尺寸。 |
| **判据** | R08：画面 100% 一致；Blit 耗时下降方向可见（≥50% 为索引原判据指标，**非本票新增性能承诺**）。R25：向量尺寸稳定，无越界。`except.txt` 空。 |
| **窗口** | 55m（30+25） |
| **产物路径** | `out/re_work/re_sprint/R_b_merge/evidence/ZB3-M03/`（simd_ab_diff.txt · reload5_foundation.csv · result.md） |

---

### ZB4-M01 · CRT 池化长跑/并发/耗尽（并入 B4）

| 项 | 内容 |
|---|---|
| **批次** | B4a（`R-CRT-POOL` L1：`VectorReuse`/`VectorGeometric`/`VectorReserve`） |
| **覆盖** | ★B-M01 · B-M02 · B-M03 · ★B-M07 · B-M09 · B-M10 |
| **前置** | ① L1 三键已装且 `EnableMemoryPool=1`（**启动期锁定禁热切**）；② 套件四 60min/8AI 场景；③ EXCEPT-AB（收尾检 `except.txt`）；④ `OnlineSafeMode` 姿态确认（联机仅 L1） |
| **步骤** | 1. ★**B-M01**：长跑对比帧率方差（对照原版）。<br>2. **B-M02**：长跑遥测 pool 命中率。<br>3. **B-M03**：频繁析构观察 delete 分流。<br>4. ★**B-M07**：多线程高压挂机 30–60min。<br>5. **B-M09**：极端微粒海压池耗尽。<br>6. **B-M10**：1h 采 Private Bytes 斜率。 |
| **判据** | M01：帧率标准方差相对对照有下降方向（索引原判据 40%，**禁百分比收益承诺**，只报方向）。M02：小对象入池方向≥95%（同上只报方向）。M03：两域各自平衡，零野指针。M07：零互锁挂死，CPU 平稳，`except.txt` 0 字节。M09：耗尽自动穿堆不闪退。M10：Private Bytes 稳定 220~280MB 无线性泄漏。 |
| **窗口** | 90m（单项名义 6×70m，**同一次 60min 长跑挂满多指标**） |
| **产物路径** | `out/re_work/re_sprint/R_b_merge/evidence/ZB4-M01/`（frame_var.csv · pool_hit.csv · delete_balance.md · cas_hang.md · pool_exhaust.md · private_bytes.csv · except.txt · result.md） |

---

### ZB4-M02 · DLL 卸载释放（并入 B4）

| 项 | 内容 |
|---|---|
| **批次** | B4a（池卸载路径） |
| **覆盖** | B-M12 |
| **前置** | ① ZC-1 Q5 可用；② L1 已装（或总闸=0 对照） |
| **步骤** | 1. **B-M12**：点退出按钮，观察卸载过程。 |
| **判据** | 干净退出零残留、零弹窗、零挂死。`except.txt` 空。 |
| **窗口** | 10m |
| **产物路径** | `out/re_work/re_sprint/R_b_merge/evidence/ZB4-M02/`（dll_unload.md · result.md） |

---

### ZB5-M01 · 联机逐帧对拍/混联 L0（新建 B5）★Top10 密集

| 项 | 内容 |
|---|---|
| **批次** | **B5 新建**（联机对拍与逻辑回归） |
| **覆盖** | ★B-N03 · B-N10 · ★B-N11 |
| **前置** | ① **DUAL-LAN** 双机同网段（硬前提，单实例不可代）；② A 端诊断镜像、B 端原版（仅 B-N11 的 L0 探针）；③ ZC-1 Q6 + `compare_sync_mirrors`；④ SyncMirror 导出可用 |
| **步骤** | 1. ★**B-N03**：双端同种子对局≥500 帧 → `compare_sync_mirrors`。<br>2. **B-N10**：双端导出 `g_MirrorRing.bin` → SHA256 比对。<br>3. ★**B-N11**：A 开诊断镜像、B 原版混联≥300 帧（**唯一授权混联探针**，仅测 net-fix L0）。 |
| **判据** | N03：MATCH 100%（500/500）。N10：两文件哈希相同。N11：零 `SYNC*.TXT`、不弹 OOS。`except.txt` 空。**红线**：G-R2 严禁把 gap/particle 等 VIOLATION 面补丁混端；本卡混联范围仅限诊断镜像 vs 原版。**G-R5：禁宣称「MP 可发布」**。 |
| **窗口** | 150m（单项 60+60+70=190m，共享双机场次压缩） |
| **产物路径** | `out/re_work/re_sprint/R_b_merge/evidence/ZB5-M01/`（crc500_mirror.txt · sha256_mirror.txt · hybrid_L0.md · result.md） |

---

### ZB5-M02 · 联机降级/W 旁路/存档校验（新建 B5）

| 项 | 内容 |
|---|---|
| **批次** | **B5 新建** |
| **覆盖** | ★B-N12 · ★B-N13 · B-N17 |
| **前置** | ① ZC-1 Q2 门控行可读；② 套件一 + DUAL-LAN；③ 同种子打/不打补丁各可存读档 |
| **步骤** | 1. ★**B-N12**：进联机房读门控行，触发降级。<br>2. ★**B-N13**：联机局内观察索敌频率。<br>3. **B-N17**：同种子打/不打补丁各存读档，比核心块哈希。 |
| **判据** | N12：ONLINE→W1–W6 自动降级生效。N13：索敌频率回归原版逐帧，不分叉。N17：SAV 核心块哈希一致，原版可读。`except.txt` 空。 |
| **窗口** | 80m（40+40+25 压缩） |
| **产物路径** | `out/re_work/re_sprint/R_b_merge/evidence/ZB5-M02/`（gate_rows.txt · targeting_freq.csv · sav_checksum.txt · result.md） |

---

### ZB5-M03 · 逻辑寻路/占用/空间哈希（新建 B5）

| 项 | 内容 |
|---|---|
| **批次** | **B5 新建** |
| **覆盖** | B-L01 · B-L02 · B-L05 · B-L06 |
| **前置** | ① 套件五场景包（狭路/基地车/塔+天启/基洛夫贴边）；② 链表与检索遥测可读 |
| **步骤** | 1. **B-L01**：狭小路口大量单位穿插。<br>2. **B-L02**：基地车展开为基地。<br>3. **B-L05**：防御塔+天启进射程。<br>4. **B-L06**：基洛夫沿最上边缘飞。 |
| **判据** | L01：`Cell+0x100` 链表双向对称，0 野指针。L02：`v[73]` 3x3 全阻挡。L05：稳定攻击高威胁目标。L06：空间哈希检索正常不崩。`except.txt` 空。 |
| **窗口** | 50m（20+15+15+15 压缩） |
| **产物路径** | `out/re_work/re_sprint/R_b_merge/evidence/ZB5-M03/`（cell_list.md · foundation_3x3.md · threat_equiv.md · spatial_edge.md · result.md） |

---

### ZB5-M04 · AI 触发/超武确定性/Timer 落盘（新建 B5）

| 项 | 内容 |
|---|---|
| **批次** | **B5 新建** |
| **覆盖** | B-L07 · B-L08 · B-L14 |
| **前置** | ① 套件一 + DUAL-LAN（L07/L08）；② ZC-1 可加存读档步骤（L14） |
| **步骤** | 1. **B-L07**：拍核弹井，双机观察小队调派。<br>2. **B-L08**：闪电风暴+铁幕并行倒计时。<br>3. **B-L14**：超武剩 10s 存档再读档。 |
| **判据** | L07：双机同时精准触发。L08：双端秒数严格同步。L14：精准从 10s 续倒计时，平滑发射。`except.txt` 空。 |
| **窗口** | 55m（30+25+20 压缩） |
| **产物路径** | `out/re_work/re_sprint/R_b_merge/evidence/ZB5-M04/`（aitrigger_dual.md · superarray_sync.csv · timer_reload.md · result.md） |

---

## 3. 执行顺序与并行建议

```
第一批（Top10 窗口）  ZB5-M01 ★N03/N11 ─┬─ ZB1-M01 ★L09/L10 ─┬─ ZB4-M01 ★M07
                          DUAL-LAN      │     套件五           │     套件四长跑
                                        ▼                     ▼
第二批（批内扫尾）    ZB5-M02 ★N12/N13 ─► ZB5-M03 ─► ZB5-M04
                      ZB2-M01 ★A05 ─► ZB2-M02 ─► ZB2-M03 ★L12/L13 ─► ZB2-M04
                      ZB3-M01 ★R03 ─► ZB3-M02 ─► ZB3-M03
                      ZB4-M02（挂 ZC-1 Q5 顺手）
```

1. **并行轴**：B5（双机）∥ B1（套件五）∥ B4（套件四长跑）∥ B2（套件三）∥ B3（套件二）——五套件场地互不冲突即可并行。
2. **串行锁**：ZB1-M01 必须在 B1 gap 三点装完且 `installed==3` 后；ZB2-* 必须在 audio/particle 钩装完后；ZB3-M01 必须在 L4/OPT-1 装完后；ZB4-M01 必须在 L1 装完且启动期锁定后。
3. **跨批混装**：允许（总实施票 §4），异常归因先关后装键。
4. **收尾统一动作**：每卡结束检 `except.txt` 0 字节 + 按 `AGENT_DELIVERY_FORMAT` 出回执；**G-R5 全程禁写「MP 可发布」**。

---

## 4. 窗口预算

| 卡 | 名义合计(min) | 压缩后(min) | 依赖硬前提 |
|---|---:|---:|---|
| ZB1-M01 | 75 | 60 | B1 装完 |
| ZB2-M01 | 130 | 90 | B2 audio 钩 |
| ZB2-M02 | 35 | 35 | 同上 |
| ZB2-M03 | 75 | 55 | B2 particle 钩 |
| ZB2-M04 | 15 | 15 | 同上 |
| ZB3-M01 | 90 | 70 | B3 装完 |
| ZB3-M02 | 70 | 50 | — |
| ZB3-M03 | 55 | 55 | harness/RELOAD5 |
| ZB4-M01 | 420* | 90 | B4a L1 + 长跑场 |
| ZB4-M02 | 10 | 10 | — |
| ZB5-M01 | 190 | 150 | DUAL-LAN |
| ZB5-M02 | 105 | 80 | DUAL-LAN |
| ZB5-M03 | 65 | 50 | 套件五 |
| ZB5-M04 | 75 | 55 | DUAL-LAN(L07/08) |
| **合计** | — | **≈13 h** | 与索引 MERGE 预算 12–16 h 吻合 |

\* ZB4-M01 六条名义各 70m，但共用同一次 60min 长跑会话，故压缩为 90m。

---

## 5. 红线与合规

| 红线 | 本编排落地 |
|---|---|
| **G-R1 MP 握手待裁** | 本文件不碰握手协议；B5 卡回执**禁止**写「G4.1 已满足」 |
| **G-R2 混端 DESYNC** | 仅 ZB5-M01 的 B-N11 允许「诊断镜像 vs 原版」混联探针；gap 等 VIOLATION 面**严禁**混端 |
| **G-R3/G-R4 乘序/PRNG** | 粒子卡（ZB2-M03/04）只验 Draw 剔除；步骤不含改乘序/跳 PRNG |
| **G-R5 禁宣称 MP 可发布** | 全部 14 卡判据/回执均禁此表述 |
| **G-R6 证据纪律** | 判据原样引用索引；本文件无「已实测」标记 |
| **G-R7 回滚** | 挂载类卡不执行安装/回滚；回滚仍归 B1–B4 原卡 |

---

## 6. 交付物

| 路径 | 内容 |
|---|---|
| `docs/re/b_class_merge_zc_cards.md` | 本文件（14 张 ZCode 子卡 · 50 条挂批次） |
| `out/re_work/re_sprint/R_b_merge/merge50_batch_map.tsv` | 50 行机读映射（ID→卡→批→窗口→产物） |
| `out/re_work/re_sprint/R_b_merge/cards_dispatch.md` | 14 卡派发视图（五字段精简） |
| `out/re_work/re_sprint/R_b_merge/README.md` | 目录说明 |

**未改**：`b_class_live_test_index.md`、`zcode_master_implementation_ticket.md`、`open_items_sweep.md`、`offline_verification_alternatives.md`、台账、看板、`ra2render/**`、`gamemd*`。

---

*R-B-MERGE 编排完成 · MERGE 50 条 100% 挂载 · 14 张 ZCode 子卡 · B1=4 / B2=14 / B3=12 / B4=7 / B5(新建)=13 · 压缩窗口 ≈13h*
