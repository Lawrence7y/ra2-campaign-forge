# 落地后必须真机回归清单 · R-B-REGRESSION

> 任务号：**R-B-REGRESSION** · 产出：本文件 + `out/re_work/re_sprint/R_b_reg/**`
> **源（只读，本任务未改）**：`docs/re/errata_sync_master_table.md`（加注后口径）· `docs/re/b_class_live_test_index.md`（B 类 92 条）· `docs/re/b_class_merge_zc_cards.md`（B5 对拍）· `docs/re/b_class_solo_zc_cards.md` · `docs/re/landing_pack_gap_p21_a3.md`（gap A3/A4/A5）· `docs/re/landing_pack_l4_opt1_checklist.md`（L4 E5 / TC-L4-01）· `out/re_work/re_sprint/R_b5_detail/compare_criteria.md`
> **纪律**：不伪造「实测」；本清单只登记**落地后必须真机回归**的项与判据。可写域：`out/re_work/re_sprint/R_b_reg/**`、本文件。**禁写**台账/看板/`ra2render/**`/`gamemd*`。
> 机读全表：`out/re_work/re_sprint/R_b_reg/regression_catalog.tsv`

---

## 0. 选入原则

同时满足任一即入表：

1. **红线行为面**：补丁/落地包的硬不变量只能真机观测（像素、`+0x134`、`SYNC*.TXT`、遥测计数）。
2. **errata 加注后波及落地字节/语义**：勘误改变了写窗、字节序、位序、跳板编码，落地后必须对拍复核。
3. **B 类索引标 MERGE/SOLO 且属 Top10 / 发布闸门**：解冻后即插即用，不得以「静态关账」代替。
4. **明确点名**：gap **A3**、**A4/A5**、**B5 对拍**、**L4 E5** 为必含项。

**不入表**：B 类 STATIC 24 条（S18 离线可关账，真机仅可选烟雾）；纯文档加注本身；台账/看板项。

---

## 1. 必含四组（点名项）

| 项 | 依赖卡 | 判据 | 窗口 |
|---|---|---|---:|
| **GAP-A3** 敌方缝经开图仍在 | `ZC-GAP-P21-A3`（方案 C-战役首选 / H-诊断钩备选需审批）· 上游 `ZC-GAP-P21` · harness `tools/gap_p21_*.py` | before `gap_cells>0` 且目标格 `Cell+0x134≥1`；开图（PsychicReveal/TA17 或受控 `RevealArea2`）后目标格 **`+0x134` 不清 0**（kept 量级同 before）；对照 `EnableGapProtection=0` 应 `GAP-WIPED`；`except.txt` 空。禁「没崩当成功」 | **90m**（战役图 C1–C7 + 对照 C10） |
| **GAP-A4** 存读档不自愈 | 同卡 §4.1 · `sav_gap_cell_abi` | A3 通过后存 `.SAV`→读档→再扫：目标格 `+0x134` **与存档前逐格一致（kept=100%）**；`gap_cells` 同量级；`except.txt` 空 | **20m** |
| **GAP-A5** DestroyGap 簿记 | 同卡 §4.2 | 摧毁/断电/变卖缝建筑后覆盖格 `+0x134` **回到 0**、无悬空计数；该格可被 `ShroudCounter` 重遮；`except.txt` 空 | **20m** |
| **L4-E5** 静态镜头同帧像素对拍 | `ZC-P4` · `landing_pack_l4_opt1_checklist` [3] · 须 **P1+P2 之后** | **E5-1** force-full vs vision-dirty 同帧像素差 **D≡0**（或帧 CRC 全等）；**E5-2** `l4RedrawSkippedStatic>0`（与 E5-1 同时成立）；**E5-3** 运动无旧位残影；**E5-4** force-full 启动遥测与现网一致（`l4RedrawSkippedStatic≡0`） | **40m** |
| **TC-L4-01** 迷雾退回 0 帧（E5 配套红线） | 同上 · G4 门 | 静止视角离开直视圈**下一逻辑帧**迷雾退回，延迟恒 0 帧；OPT-1 on/off 一致；vanilla **不得**用 T2 放行 | **20m** |
| **B5-对拍 ZB5-M01** 逐帧 CRC/镜像/混联 L0 | `b_class_merge_zc_cards` ZB5-M01 · **DUAL-LAN** · ZC-1 Q6 · `compare_sync_mirrors` | **B-N03** MATCH 100%（500/500）；**B-N10** 双端 `g_MirrorRing.bin` SHA256 相同；**B-N11** 混联 ≥300 帧零 `SYNC*.TXT`、不弹 OOS（**唯一授权混联**：诊断镜像 vs 原版）；`except.txt` 空；**G-R5 禁写「MP 可发布」** | **150m** |
| **B5-对拍 ZB5-M02** 降级/W 旁路/存档校验 | ZB5-M02 · ZC-1 Q2 · DUAL-LAN | **B-N12** ONLINE→W1–W6 自动降级；**B-N13** 索敌频率回归原版逐帧不分叉；**B-N17** 打/不打补丁 SAV 核心块哈希一致且原版可读 | **80m** |
| **B5-对拍 ZB5-M03** 逻辑寻路/占用/哈希 | ZB5-M03 · 套件五 | **B-L01** `Cell+0x100` 链表双向对称 0 野指针；**B-L02** `v[73]` 3×3 全阻挡；**B-L05** 稳定打高威胁；**B-L06** 空间哈希贴边不崩 | **50m** |
| **B5-对拍 ZB5-M04** AI/超武/Timer | ZB5-M04 · DUAL-LAN（L07/08） | **B-L07** 双机同时精准触发；**B-L08** 双端秒数严格同步；**B-L14** 剩 10s 存读档精准续倒计时 | **55m** |

---

## 2. errata 加注后 · 落地字节/语义必回归

> 口径源：`errata_sync_master_table.md` R-E01…R-E10（**加注后**）。文档加注不等于真机闭环；下列项在补丁落地后必须真机对拍/观测复核。

| 项 | 依赖卡 | 判据 | 窗口 |
|---|---|---|---:|
| **R-E01/E02** Gap 写窗 VA/上下文窗 | `ZC-GAP-P21` 安装器 · 挂 GAP-A3 场次收尾 | 收尾复核 `0x568273` 窗 `90×6`、目标指令实在 **`0x0056829A`**；上下文窗按 **17B** 口径自检；启动日志 `GapProtection=on`；与 A3 行为面同场 | **10m**（并入 A3） |
| **R-E03** T-a 7B 切断 | H20C / 雷达扫描超武卡 | `0x6CD7C4` 处 **7B** `mov al,[esp+0x1EC]`，补丁 `E9`+2×`90` 不切断指令；Sweep 动画/开图正常 | **20m** |
| **R-E04** `SW+0xF8` 死键 | SW 半径卡（UI-only） | 瞄准圈半径随 `SW+0xF8`；**开图/杀伤半径**随 `Rules+0xFEC`（`min(10,·)`），二者解耦 | **15m** |
| **R-E07** Verses 9 处施加点 | 伤害优化前置 · 武器伤害卡 | 9 站点（V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c）伤害曲线与预计算一致；禁按「8 处」裁剪 | **25m** |
> 【W3 勘误 · W3-A6/ISSUE-VERSES-SITES-COUNT】改前：Verses 9 处施加点 | 伤害优化前置 · 武器伤害卡 | 9 站点（V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c）伤害曲线与预计算一致；禁按「8 处；改后：Verses FPU 索引访存共 9 处 (V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c)；依据：errata_sync_master_table.md:22 (R-E07); warhead_verses_residual_p2.md:18, 58；分级：P1
| **R-E08** 槽 69 **LE** 写入 | 粒子/微粒落地包 · `landing_pack_particle*` | 写回值 `C0 CE 62 00` / `80 E2 62 00`（DWORD `0x0062CEC0`/`0x0062E280`）；黑雾/尾烟不崩；回滚值同 LE | **15m**（挂 B-L13/B-R20） |
| **R-E09** `OccuredEvents` 位序 | 存档/触发器敏感序 · ZC-1 存读档 | `bit i` = 事件链第 i 个 Event 已发生（与 kind 无关）；**禁重排 `[Events]`**；存档后触发进度不错位 | **25m**（挂 B-L14/B-N17） |
| **R-E10** H-D5 `0F B6 C0` | Net Fix 跳板 `+0x10` · **B5 ZB5-M01 前置** | `movzx eax,al` 非 `and`；帧>255 不越界写；与 B-N03 500 帧对拍同场闭环 | **0m**（由 ZB5-M01 覆盖） |

---

## 3. B 类索引 · Top10 真机必回归（解冻后）

| 项 | 依赖卡 | 判据 | 窗口 |
|---|---|---|---:|
| **B-N11** 混联 L0 | ZB5-M01 · DUAL-LAN | 零 `SYNC*.TXT`、不弹 OOS（≥300 帧） | 70m→**并入 ZB5-M01** |
| **B-N03** 逐帧 CRC 500 | ZB5-M01 · ZC-1 Q6 | MATCH 100%（500/500） | 60m→**并入** |
| **B-N12/N13** 降级/旁路 | ZB5-M02 · ZC-1 Q2 | W1–W6 自动降级；索敌逐帧不分叉 | 40+40→**并入 ZB5-M02** |
| **B-L09** SpySat 不全图开 | ZC-GAP-P21 · 套件五 · B-05 | 小地图不整亮；`House+0x577A` 不置 1 | **20m** |
| **B-L10** 裂缝黑雾恢复 | ZC-GAP-P21 · 套件五 · B-04 | 扫描退去 100% 全黑；`Cell+0x134≥1` | **25m** |
| **B-L13** 己方零误杀 | ZC-1 Q3③ · 套件五 · B-07 | 尾烟 100% 可见（兼 B-L12 无永生） | **25m** |
| **B-M07** CRT CAS 并发 | 套件四 · ZC-11/EXCEPT-AB · B-09 | 30–60min 高压零互锁；`except.txt` 0 字节 | **70m** |
| **B-R03** L4 350 格保底 | 套件二 · L4 落地包 · B-11 | `fullRedrawTriggered==1`；零残影黑块 | **20m** |
| **B-L11** TYPE 跨战局还原 | RELOAD5 独立卡 · B-06 | 进出×5 备份表=首次原值，无 600/16.0 污染 | **35m** |

---

## 4. 窗口汇总与执行序

| 批 | 内容 | 窗口 | 硬前提 |
|---|---|---:|---|
| **W0 前置** | R-E10 跳板字节 + R-E01/E02 安装窗自检 | 15m | 补丁已装 |
| **W1 红线** | GAP-A3 + A4 + A5（同局） | 130m | 战役 gap 农场图；`EnableGapProtection=1` |
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0
| **W2 红线** | L4-E5 + TC-L4-01 | 60m | **P1+P2 已修**；vision-dirty 可开 |
| **W3 B5 对拍** | ZB5-M01→M02→M03→M04 | 335m | DUAL-LAN 错开预约；ZB5-M01 含 R-E10 |
| **W4 B 类 Top10 余项** | B-L09/L10/L13/R03/M07/L11 | 195m | 套件二/四/五；RELOAD5 |
| **W5 errata 余波** | R-E03/E04/E07/E08/E09 | 100m | 对应落地包 |
| **合计** | — | **≈14 h**（不含排障/审批） | 与 MERGE 12–16h 口径兼容 |

**串行锁**：GAP-A3 先于 A4/A5；L4-E5 必须 P1+P2 后；ZB5-M01 先于依赖其结论的混端宣称；B-M07 可与 W3 并行（场地不冲突）。

**红线（全程）**：G-R2 仅 ZB5-M01 的 B-N11 允许混联探针，gap/particle 面禁混端；G-R5 禁写「MP 可发布 / G4.1 已满足」；`except.txt` 0 字节收尾；禁伪造成实测。

---

## 5. 交付物

| 路径 | 内容 |
|---|---|
| `docs/re/b_regression_required.md` | 本清单（项/依赖卡/判据/窗口） |
| `out/re_work/re_sprint/R_b_reg/regression_catalog.tsv` | 机读全表 |
| `out/re_work/re_sprint/R_b_reg/errata_to_b_map.md` | errata R-E0x → B 类/落地卡映射 |
| `out/re_work/re_sprint/R_b_reg/README.md` | 目录说明 |

**未改**：errata 总表、B 类索引、merge/solo 卡、landing_pack_*、台账、看板、`ra2render/**`、`gamemd*`。

---

*R-B-REGRESSION 编制完成 · 点名四组全覆盖（A3 / A4-A5 / B5 对拍 / L4 E5）· errata 加注波及 7 项 · B 类 Top10 余项 6 项 · 预算 ≈14h*
