# R-B5-DETAIL · B5 联机对拍真机卡细化（ZB5-M01..04）

> **任务号**：`R-B5-DETAIL` · **产物**：本文件 + `out/re_work/re_sprint/R_b5_detail/**`
> **源（只读，本任务未改）**：`docs/re/b_class_merge_zc_cards.md` ZB5-M01..04 · `docs/re/b_class_live_test_index.md` §3/§4.3 N 系（B-N03/N10/N11/N12/N13/N17）· `docs/re/net_sync_desync_map.md`（三层探针 / 混端表 / H-D 钩自证口径）· `docs/re/zcode_master_implementation_ticket_v2.md` B5 节与 G-R1..R7 · `docs/re/b_class_solo_zc_cards.md` §3 边界
> **纪律**：**不伪造「实测」**；本文件只做**步骤细化与判据锚定**，全部条目状态为 `[待实测]`。真机回执由 ZCode 按 `AGENT_DELIVERY_FORMAT` 另出。禁写台账/看板/ra2render/gamemd。
> **机读映射**：`out/re_work/re_sprint/R_b5_detail/b5_detail_map.tsv` · **DUAL-LAN 预检单**：`dual_lan_preflight.md` · **对拍判据卡**：`compare_criteria.md` · **回执模板**：`receipt_template.md`

---

## 0. 总裁定

| 指标 | 值 |
|---|---|
| 覆盖子卡 | **4**（ZB5-M01 … ZB5-M04） |
| 覆盖 MERGE 条目 | **13**（N03/N10/N11 · N12/N13/N17 · L01/L02/L05/L06 · L07/L08/L14） |
| 其中 N 系（联机对拍面） | **6** |
| 硬前提 | **DUAL-LAN**（M01 全卡 · M02 全卡 · M04 的 L07/L08；M03 为单机套件五） |
| 混联授权面 | **仅 B-N11 一条**（诊断镜像 vs 原版 · net-fix L0） |
| 压缩窗口 | M01 150m + M02 80m + M03 50m + M04 55m = **335m ≈ 5.6h** |
| MP 发布宣称 | **不在本卡**。唯一门 = G-R1 握手裁决落地 + G4.1/G4.2 实装实测 |

**本细化解决什么**：把 ZB5 四卡从「五字段挂载卡」展开为**可直接开跑的真机操作卡**——DUAL-LAN 端配置清单、同种子/混联场次切分、逐条对拍判据与失败切分、证据落盘名、红线自证。**不改**索引判据、不改 MERGE 编排窗口、不碰握手协议。

---

## 1. DUAL-LAN 硬前置（全部联机场次的门）

> 来源：`b_class_live_test_index.md` §5「DUAL-LAN 双机同网段，单实例不可代」；`b_class_merge_zc_cards.md` ZB5-M01 前置；`zcode_master_implementation_ticket_v2.md` B5「顺序（强制）①」。

### 1.1 端配置总表

| 项 | A 端（主机/探针端） | B 端（对端） | 适用卡 |
|---|---|---|---|
| 硬件 | 实体机 1 | 实体机 2（**禁单实例/禁回环/禁虚拟双开代**） | M01/M02/M04(L07/L08) |
| 网段 | 同网段可互通（LAN，非 NETCOND） | 同左 | 同上 |
| 镜像（N03/N10/N12/N13/N17/L07/L08 对拍场） | **诊断镜像**（ZC-1） | **诊断镜像**（同构建） | 对拍/回归场 |
| 镜像（**仅 N11 混联探针场**） | **诊断镜像** | **原版 `gamemd.exe`（不加载 `ra2render.dll`）** | **仅 M01 步骤 3** |
| ini | 两端**逐键一致** | 同左 | 全部 |
| 种子 | 同种子（对拍场强制） | 同左 | N03/N10/N12/N13/N17 |
| 四键（N11 场强制） | `EnableSpySatRadarSweep=0` · `EnableRadarSweepWindow=0` · `EnableGapProtection=0` · `EnableMinimapFog=0` | 同左（原端无 DLL 时天然满足，A 端必须自证为 0） | **仅 N11** |
| 开关姿态 | 对拍局要求：两端同构建、同 ini、同种子（ticket v2 B5「开关」） | 同左 | 全部 |

### 1.2 开跑前预检（不满足 = 整卡 blocked，禁降级代跑）

| # | 预检项 | 通过线 | 证据落盘 |
|---|---|---|---|
| P1 | 双机同网段连通 | 互 ping / 进房互见 | `dual_lan_preflight.md` 勾选 |
| P2 | 端配置一致（除 N11 场） | 双端镜像/ini/种子逐项一致 | 同上 |
| P3 | N11 场四键=0 自证 | A 端读 ini 四键均为 0；B 端为原版 | `hybrid_L0.md` 四键截图/摘录 |
| P4 | SyncMirror 导出可用 | 双端可导出 `g_MirrorRing.bin` | `sha256_mirror.txt` 前置 |
| P5 | `compare_sync_mirrors` 可用 | ZC-1 Q6 工具在位 | `crc500_mirror.txt` 前置 |
| P6 | DUAL-LAN 时段预约 | 与 SOLO S07/S09 错开（`b_class_solo_zc_cards.md` §3.2-4） | 排期记录 |
| P7 | `except.txt` 收尾可检 | 路径约定一致 | 每卡 `result.md` |

**单实例不可代**：任何「单机模拟双端 / 回环 / 同进程双开」**不得**充当 DUAL-LAN；无双机 = 该卡 `blocked`，回执写 `blocked: DUAL-LAN`，**禁**写「已实测」。

---

## 2. 混联边界：仅 N11（唯一授权探针）

> 来源：`b_class_merge_zc_cards.md` ZB5-M01 判据红线 · `net_sync_desync_map.md` §3 混端表 · `zcode_master_implementation_ticket_v2.md` G-R2 · `b_class_solo_zc_cards.md` §3.2-1。

### 2.1 授权范围（一锤定音）

| 项 | 裁决 |
|---|---|
| **唯一授权混联** | **B-N11**（挂在 ZB5-M01 步骤 3）：A 端诊断镜像 ↔ B 端原版，≥300 帧，**仅测 net-fix L0** |
| 混联形态 | 「诊断镜像 vs 原版」——诊断镜像**只含** net-fix L0 诊断钩（H-D1/H-D2 类旁路，零语义） |
| 四键强制 | `EnableSpySatRadarSweep=EnableRadarSweepWindow=EnableGapProtection=EnableMinimapFog=0`（任一非 0 = 本场作废） |
| 判据 | **零 `SYNC*.TXT`、不弹 OOS**；`except.txt` 空 |
| **严禁** | 把 gap / SpySat TYPE / S2 / S3 / L2 节流 / path cache 等 **VIOLATION / RISK** 面补丁混端（G-R2） |
| **严禁** | 用 N11 场「顺手」验 gap/particle 逻辑面——混联探针**只**看 net-fix L0 零 OOS |
| 其它卡 | M02/M03/M04 **一律双端同镜像**；发现混端立即停，只记录时间戳交 M01 对拍面裁决 |

### 2.2 与混端表的对应（`net_sync_desync_map.md` §3.1/§3.2）

| 改集 | 混端判定 | 本卡处置 |
|---|---|---|
| D-GAP（gap NOP×3） | **VIOLATION** | **禁混端**；N11 场 `EnableGapProtection=0` |
| D-GAP-B / D-S1 / D-S2 / D-S3 | VIOLATION | **禁混端**；不装、不测 |
| D-L2 寻敌节流 | VIOLATION（interval>1 / pointer 键） | 联机强制 interval=1；**不进** N11 场 |
| D-PATH 寻路缓存 | RISK（保序才安全） | **不进** B5 本批（待 H-D5/H-D6 对拍前置） |
| D-AI 时间片 | RISK | 同上 |
| D-RNG / D-CMD / D-CRC / D-CKSM | VIOLATION | 红线，零触碰 |
| D-PART（Draw 剔除）/ D-AUDIO / D-VXL13 / D-L4 / D-RADAR | SAFE | 可共存，但 N11 场仍按四键=0 最小面执行 |
| net-fix L0 诊断钩（H-D1/H-D2 旁路） | **零语义 · 可混联** | **N11 唯一测面** |

### 2.3 N11 场次切分（防「混联」被滥用）

```
N11 混联场（独立场次，不与 N03/N10 同场）：
  A: 诊断镜像 + 四键=0 + SyncEarlyLog/SyncSnapshotOnDesync 按诊断需要（默认 0）
  B: 原版 gamemd.exe（整局不加载 ra2render.dll）
  目标: ≥300 帧
  观察: 全程零 SYNC*.TXT、不弹 OOS、except.txt 空
  产物: hybrid_L0.md（含四键=0 自证 + 帧数 + SYNC 文件清单=空）
```

**失败切分**：出现 `SYNC*.TXT` 或 OOS → 立即停场；保存 `SYNC*.TXT`/`SYNC_SNAP_*.bin` 原件；回执标 `FAIL: N11 hybrid`，**禁**用「重启再跑好了」覆盖；归因交对拍面 + `net_sync_desync_map.md` §3 表。

---

## 3. 对拍判据（逐步可判定 · 原样引自索引）

> 判据**不改写**；下列为执行细化（怎么采、采什么、失败怎么记）。状态一律 `[待实测]`。

### 3.1 ZB5-M01 · 联机逐帧对拍 / 混联 L0（★Top10 密集）

| 项 | 内容 |
|---|---|
| **覆盖** | ★B-N03 · B-N10 · ★B-N11 |
| **窗口** | 150m（单项 60+60+70，共享双机场次压缩） |
| **产物路径** | `out/re_work/re_sprint/R_b_merge/evidence/ZB5-M01/`（`crc500_mirror.txt` · `sha256_mirror.txt` · `hybrid_L0.md` · `result.md`） |

| 步 | 条目 | 最小步骤 | **判据（原样）** | 采集与失败记法 | 窗 |
|---|---|---|---|---|---|
| 1 | ★**B-N03** 逐帧 CRC 500 | 双端同种子对局 ≥500 帧 → `compare_sync_mirrors` | **MATCH 100%（500/500）** | 输出逐帧比对表存 `crc500_mirror.txt`；任何帧 mismatch = FAIL，记首个 mismatch 帧号 | 60m |
| 2 | **B-N10** 双端镜像一致 | 双端导出 `g_MirrorRing.bin` → SHA256 比对 | **两文件哈希相同** | `sha256_mirror.txt` 写双端路径+完整哈希；不等 = FAIL | 60m |
| 3 | ★**B-N11** 混联 L0 | A 开诊断镜像、B 原版混联 ≥300 帧（**唯一授权混联探针**，仅测 net-fix L0） | **零 `SYNC*.TXT`、不弹 OOS** | `hybrid_L0.md`：帧数、四键=0 自证、SYNC 文件清单（须空）、OOS 与否 | 70m |
| 收 | — | — | `except.txt` 空 | **禁「没崩当成功」**；G-R5 禁写「MP 可发布」 | — |

**对拍口径锚点**（`net_sync_desync_map.md` §1.1/§2.3，执行时对照）：
- A 层命令流 = 锁步权威；B 层帧 CRC `0x64DAB0`/`CurrentFrameCRC@0xAC51FC`/`LatestFramesCRC[256]@0xB04474` = 轻探针；C 层对象 Checksum = 事后归因。
- **禁**改 CRC 混合式 / ÷10 / `0x650A90` 每帧 1 次 RNG / `0x64C6E2` 比较宽度（H-D11 红线）。
- 自证口径（诊断钩装上后）：同种子单机 ≥500 帧开/关逐帧 `CurrentFrameCRC` 序列一致；`0x64DAB0` 与 `0x650A90` 调用次数不变；A 开/B 关 ≥300 帧零 `SYNC*.TXT`/零 OOS；Remove 后原字节还原。

### 3.2 ZB5-M02 · 联机降级 / W 旁路 / 存档校验

| 项 | 内容 |
|---|---|
| **覆盖** | ★B-N12 · ★B-N13 · B-N17 |
| **窗口** | 80m（40+40+25 压缩） |
| **产物路径** | `.../R_b_merge/evidence/ZB5-M02/`（`gate_rows.txt` · `targeting_freq.csv` · `sav_checksum.txt` · `result.md`） |

| 步 | 条目 | 最小步骤 | **判据（原样）** | 采集与失败记法 | 窗 |
|---|---|---|---|---|---|
| 1 | ★**B-N12** 降级状态机 | 进联机房读门控行，触发降级 | **ONLINE→W1–W6 自动降级生效** | `gate_rows.txt` 抄门控行原文+降级后档位 | 40m |
| 2 | ★**B-N13** W1–W6 旁路 | 联机局内观察索敌频率 | **索敌频率回归原版逐帧，不分叉** | `targeting_freq.csv` 双端采样；分叉 = FAIL | 40m |
| 3 | **B-N17** 存档 Checksum | 同种子打/不打补丁各存读档，比核心块哈希 | **SAV 核心块哈希一致，原版可读** | `sav_checksum.txt` 两份哈希+原版读档结果 | 25m |
| 收 | — | — | `except.txt` 空 | 同上 | — |

### 3.3 ZB5-M03 · 逻辑寻路 / 占用 / 空间哈希（套件五 · 非 DUAL-LAN）

| 项 | 内容 |
|---|---|
| **覆盖** | B-L01 · B-L02 · B-L05 · B-L06 |
| **窗口** | 50m（20+15+15+15 压缩） |
| **产物路径** | `.../R_b_merge/evidence/ZB5-M03/`（`cell_list.md` · `foundation_3x3.md` · `threat_equiv.md` · `spatial_edge.md` · `result.md`） |

| 步 | 条目 | 最小步骤 | **判据（原样）** | 采集与失败记法 | 窗 |
|---|---|---|---|---|---|
| 1 | **B-L01** | 狭小路口大量单位穿插 | **`Cell+0x100` 链表双向对称，0 野指针** | `cell_list.md` 链表抽查 | 20m |
| 2 | **B-L02** | 基地车展开为基地 | **`v[73]` 3x3 全阻挡** | `foundation_3x3.md` | 15m |
| 3 | **B-L05** | 防御塔+天启进射程 | **稳定攻击高威胁目标** | `threat_equiv.md` | 15m |
| 4 | **B-L06** | 基洛夫沿最上边缘飞 | **空间哈希检索正常不崩** | `spatial_edge.md` | 15m |
| 收 | — | — | `except.txt` 空 | 同上 | — |

> 注：M03 为单机套件五逻辑回归，**不**要求 DUAL-LAN；但若顺手看到 `SYNC*.TXT` 只记录不裁决（裁决归 M01 对拍面）。

### 3.4 ZB5-M04 · AI 触发 / 超武确定性 / Timer 落盘

| 项 | 内容 |
|---|---|
| **覆盖** | B-L07 · B-L08 · B-L14 |
| **窗口** | 55m（30+25+20 压缩） |
| **产物路径** | `.../R_b_merge/evidence/ZB5-M04/`（`aitrigger_dual.md` · `superarray_sync.csv` · `timer_reload.md` · `result.md`） |

| 步 | 条目 | 最小步骤 | **判据（原样）** | 采集与失败记法 | 窗 |
|---|---|---|---|---|---|
| 1 | **B-L07** | 拍核弹井，双机观察小队调派 | **双机同时精准触发** | `aitrigger_dual.md` 双端时间戳/帧号 | 30m |
| 2 | **B-L08** | 闪电风暴+铁幕并行倒计时 | **双端秒数严格同步** | `superarray_sync.csv` 逐秒对照 | 25m |
| 3 | **B-L14** | 超武剩 10s 存档再读档 | **精准从 10s 续倒计时，平滑发射** | `timer_reload.md` | 20m |
| 收 | — | — | `except.txt` 空 | L07/L08 须 DUAL-LAN；L14 可单机 | — |

---

## 4. 禁止伪造成实测（证据纪律 · 只强不松）

> 来源：`b_class_merge_zc_cards.md` §5 G-R6 · `b_class_live_test_index.md` §0/§2 · `b_class_solo_zc_cards.md` §3.2-6 · ticket v2 G-R5。

| # | 禁令 | 落地 |
|---|---|---|
| 1 | **禁止**在本文件、回执、日志写「已实测 / 实测通过 / 已验收」 | 本文件全部条目 `[待实测]`；真机回执另出 |
| 2 | **禁止**把「没崩 / 能进房 / 看着正常」当成功 | 判据以 §3 原文为准；`except.txt` 0 字节是底线不是上限 |
| 3 | **禁止**伪造成帧数（「≥500 帧」写成「跑了一会儿」） | 回执必填**实际帧号/实际条数**（N03=500/500 或实际 mism 数；N11=实际帧数） |
| 4 | **禁止**伪造哈希/CRC（手填 MATCH） | `sha256_mirror.txt`/`crc500_mirror.txt` 附工具原始输出 |
| 5 | **禁止**单实例代 DUAL-LAN 后写「双机通过」 | 无双机 = `blocked` |
| 6 | **禁止**用 N11 混联成功冒充「MP 安全 / gap 安全 / 可发布」 | N11 **只**证明 net-fix L0 零 OOS |
| 7 | **禁止**写「MP 可发布 / G4.1 已满足 / 联机安全可出厂」 | G-R5；违者交付不合格 |
| 8 | **禁止**SOLO 场出现 `SYNC*.TXT` 时写「同步通过/失败」 | 只记录时间戳与文件名，交 B5 对拍面裁决 |
| 9 | **禁止**跳步后仍按全量窗口出回执 | 实际步覆盖写清「跳过 X，原因 Y」 |
| 10 | **禁止**本任务改索引判据 / MERGE 窗口 / 握手协议 | 只细化，不改判 |

**回执必填（B5 额外，ticket v2）**：`DUAL-LAN 端配置` · `N11 混联范围（仅诊断镜像 vs 原版）` · `四键=0 自证` · 每步**实际**帧数/哈希/条数 · `except.txt` 状态 · 红线触碰（G-R1..R7 which）。

---

## 5. 与 G-R1 握手待裁边界

> 来源：`landing_pack_gap_merge_checklist.md` §7.1 · ticket v2 G-R1/G-R5 · `b_class_merge_zc_cards.md` §5。

### 5.1 待裁现状（甲/乙未裁）

| 方 | 主张 | 出处 |
|---|---|---|
| **甲（不加键）** | 不把 `EnableGapProtection`/`EnableSpySatGate` 纳入联机握手；策略 = 全员强制同值 + 禁混端（文档级） | `gap_protection_install_spec.md` §4.3 / P21 §7、P223 §7 |
| **乙（要握手）** | 握手键**必须含** `EnableGapProtection` + `gapProtectionPatchesInstalled`（期望 3）；混端**拒绝开局** | `savegame_product_checklist.md` G4.1/G4.2 |
| **裁决状态** | **open**（Lead 未裁） | §7.1「冲突待裁决 · Lead」 |

### 5.2 B5 与 G-R1 的边界（本卡严守）

| 项 | 边界 |
|---|---|
| **B5 可做** | 对拍 MATCH、混联 L0 零 OOS、降级/旁路/SAV/逻辑回归——证明「本轮对拍通过」 |
| **B5 不可做** | ① 新增/修改任何握手字段；② 宣称「G4.1 已满足」；③ 用对拍全绿替代 G-R1 裁决门；④ 代裁甲/乙 |
| **裁决前唯一门** | MP 发布宣称 = **Lead 对 §7.1 握手口径裁决落地 + G4.1/G4.2 实装/实测**；B5 对拍 MATCH **不是**替代门 |
| **若裁为乙** | 需**另卡**补握手字段设计（键清单是否纳入 `EnableRadarSweepWindow`/`EnableSWChargeOpt` 由裁决一并定）；**裁决前不实现** |
| **当前唯一安全混端姿势** | 本端整局不加载 `ra2render.dll`，或全员同构建同开关（且仍需 Gate3 / M2 对拍）；N11 探针是**测试例外**，不是产品姿势 |

### 5.3 红线对照（G-R1..R7 · B5 触点）

| 红线 | B5 触点 | 处置 |
|---|---|---|
| **G-R1** 握手待裁 | 全卡 | 回执**禁止**写「G4.1 已满足」；不碰协议 |
| **G-R2** 混端 DESYNC | N11 | 仅诊断镜像 vs 原版；gap 等 VIOLATION 面**严禁**混端 |
| **G-R3/R4** 乘序/PRNG | M03/M04 | 步骤不含改乘序/跳 PRNG；生成侧 PRNG 照常消费 |
| **G-R5** 禁宣称 MP 可发布 | 全卡 | B5 全绿也只证明「本轮对拍通过」 |
| **G-R6** 证据纪律 | 全卡 | 判据原样引用；禁伪实测 |
| **G-R7** 回滚 | — | B5 不安装补丁；回滚归 B1–B4 原卡 |

---

## 6. 执行顺序与 DUAL-LAN 排期

```
硬前提锁：DUAL-LAN 双机同网段就绪（预检 P1–P7 全过）──► 否则 M01/M02/M04(L07/L08) 全 blocked

DUAL-LAN 互斥串行（与 SOLO 共享台，见 b_class_solo_zc_cards §3.2-4）：
  ZB5-M01 ★N03/N11 ─► ZB5-M02 ★N12/N13 ─► ZB-S07 ─► ZB-S09 ─► ZB5-M04(L07/L08)

并行轴（无 DUAL-LAN 依赖）：
  ZB5-M03（套件五）∥ B1/B2/B3/B4 相应套件
```

1. **场次切分**：N03/N10（双端同镜像对拍场）与 N11（混联场）**独立开局**，不复用同一局。
2. **串行锁**：M01 未出对拍回执前，M02 的 N13 索敌频率可并行准备但**不**开混联；M04 的 L14 可与双机台并行。
3. **收尾统一**：每卡 `except.txt` 0 字节 + `result.md` + 按 `AGENT_DELIVERY_FORMAT` 回执；G-R5 全程生效。

---

## 7. 交付物

| 路径 | 内容 |
|---|---|
| `docs/re/b5_mp_card_details.md` | 本文件（B5 四卡真机细化 · DUAL-LAN 前置 · 混联仅 N11 · 对拍判据 · 证据纪律 · G-R1 边界） |
| `out/re_work/re_sprint/R_b5_detail/b5_detail_map.tsv` | 13 条机读映射（ID→卡→判据摘要→产物→硬前提） |
| `out/re_work/re_sprint/R_b5_detail/dual_lan_preflight.md` | DUAL-LAN 预检单 P1–P7 |
| `out/re_work/re_sprint/R_b5_detail/compare_criteria.md` | 对拍判据速查（原样引用） |
| `out/re_work/re_sprint/R_b5_detail/receipt_template.md` | B5 回执模板（含必填三项） |
| `out/re_work/re_sprint/R_b5_detail/README.md` | 目录说明 |
| `out/re_work/re_sprint/R_b5_detail/evidence/` | 真机证据预留目录（ZCode 落盘） |

**未改**：`b_class_live_test_index.md`、`b_class_merge_zc_cards.md`、`net_sync_desync_map.md`、`zcode_master_implementation_ticket_v2.md`、`b_class_solo_zc_cards.md`、`landing_pack_gap_merge_checklist.md`、台账、看板、`ra2render/**`、`gamemd*`。

---

## 8. 状态声明

- 本文件为 **R-B5-DETAIL 细化产物**：步骤/判据/边界锚定完成；**无任何真机执行**。
- 全部 13 条状态 = `[待实测]`；DUAL-LAN 未预检通过前相关卡 = `blocked`。
- **MP 发布宣称不在本卡射程**；等待 G-R1 Lead 裁决。

---

*R-B5-DETAIL 细化完成 · ZB5-M01..04 四卡 13 条 · DUAL-LAN 硬前置 P1–P7 · 混联仅 N11（四键=0）· 对拍判据原样锚定 · 禁伪实测 10 条 · G-R1 边界严守（甲/乙仍 open）*
