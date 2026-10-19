# R-NET-SYNC · 同步演进 / Desync 点清单 / 诊断钩落地图（全静态）

> 逆向对象：`ra2youli/gamemd.exe`（YR 1.001，ImageBase `0x400000`，file offset = VA − `0x400000`）
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 前置：`docs/re/net_sync_checksum.md`（§0–§13）、`docs/re/net_sync_fix_spec.md`（H-D1/H-D2/H-D5/H-D6 规格）、`docs/re/mp_gate_residual_deep_dive.md` §4（混端表）、`docs/re/sav_gap_cell_abi_deep_dive.md`、`docs/re/gap_psychic_reveal_deep_dive.md`。
> 工作产物：`out/re_work/re_sprint/R_net_sync/`（claims / 演进矩阵 / desync 清单 / 钩落地顺序）。
> 写作用域：本文 + `out/re_work/re_sprint/R_net_sync/**`。**禁写** `ra2render/**`、`gamemd.exe`、`ra2youli/**`、`tools/**`、台账/看板/ATLAS、`out/reverse/**`。
> **证据三档**：`[实证]` 本轮对 `gamemd.exe` 字节/反汇编复算或既有档案实证摘录；`[前证]` 既有深潜已实证、本轮引用一致；`[待实测]` 需真机混联/双端对拍。
> **立场**：**诊断钩优先，不改演进**。本任务零补丁落地、零 `ra2render` 改动，只出可实施规格与 desync 红线图。

---

## 0. 结论速览

| # | 命题 | 结论 | 档 |
|---|---|---|---|
| 1 | **同步演进 = 锁步命令流 + 帧 CRC 轻探针 + 对象 Checksum 重探针** | 三层面各管一段；改任何一层的「输入面/次序/次数」= 改演进 | [前证] |
| 2 | **帧 CRC `0x64DAB0` 哈希面极窄** | 只混：Infantry/Unit/Building 量化坐标、Aircraft `+0x241`、5 图层对象坐标、Logic 簇坐标、每帧 1 次局内 RNG。**不哈希** HP/弹药/目标/路径/Cell 字段/粒子/超武/音频/UI | [前证] §3.2 + §13.1 |
| 3 | **对象 Checksum `*::v[13]` 面极宽，但只进 SYNC 诊断/存档** | 覆盖 42 类目含 Particle/System、House、Event；**`Cell+0x134` 不进**（`CellClass::CalculateChecksum v[13]=0x410410` 只折 `+0x10` dword + `+0x20` byte） | [前证] `sav_gap_cell_abi_deep_dive.md` |
| 4 | **漏检 ≠ 安全** | `Cell+0x134` 不进 per-object checksum，却主导索敌/可见性谓词 → 逻辑分叉 → 坐标分叉 → **帧 CRC 间接 DESYNC**。同理：路径缓存、寻敌节流、AI 时间片、RNG 消费次数 | [前证]+[推演] |
| 5 | **H-D1 / H-D2 = 诊断钩第一优先级** | H-D1 `0x64C6F2` L0 预测日志（`SyncEarlyLog`）；H-D2 `0x64CC61` L1 现场快照（`SyncSnapshotOnDesync`）。**默认全 0**；只旁路、不改 `jne` 语义 | [前证] `net_sync_fix_spec.md` §2–§3 |
| 6 | **混端必分叉改集 = gap NOP（+ SpySat/S2/S3/L2）** | particle / vxl / audio = 表现层 SAFE（无 DESYNC，可有观感分叉）；path cache = 条件安全（保序才安全）；gap `Cell+0x134` = **VIOLATION** | [前证] `mp_gate_residual_deep_dive.md` §4 |
| 7 | **可落地顺序** | ① H-D1/H-D2 诊断钩（不改演进）→ ② H-D5/H-D6 对拍套件 → ③ 混端门禁文档/降级（不碰 CRC 算法）。**明确不做** H-D11/H-D12（L3） | 本文 §5 |

---

## 1. 帧 CRC / 同步演进路径（哈希了什么、漏了什么）

### 1.1 三层探针（勿混）

| 层 | 入口 | 用途 | 比对时机 | 改动红线 |
|---|---|---|---|---|
| **A 命令流（权威）** | `Queue@0x8B4204` → `0x64C380` → `0x4C6CB0` 跳表 | 锁步本体：所有端同帧同序执行同一 `NetworkEvent` 流 | 每帧 `Timestamp==CurrentFrame` | **禁止**改序/Timestamp 语义/RNG 消费次数（H-D12） |
| **B 帧 CRC（轻探针）** | `Compute_Frame_CRC 0x64DAB0` → `CurrentFrameCRC@0xAC51FC` → `LatestFramesCRC[256]@0xB04474` | desync **早发现**；比对 `event.Checksum` @ `0x64C6E2` | FrameInfo（Kind `0x1C`）到达时 | **禁止**改混合式/量化 ÷10/`0x650A90` 抽样次数/比较宽度（H-D11） |
| **C 对象 Checksum（重探针）** | `*Class::v[13]` → `Checksummer 0x4A1C10` 簇 | **仅** desync 后 `SYNC*.TXT` 归因 + 存档自洽 | 不在线比对 | **禁止**重排/删字段；只许新魔数追加 |

> 三层关系：**A 决定演进，B 抽查演进结果的投影，C 记录演进全貌供事后归因**。混端分叉几乎总先在 A 层发生，B 层只是报警器；把报警器修成不响（改 CRC）= H-D11 = **禁止**。

### 1.2 帧 CRC 哈希面（`0x64DAB0`）——进 / 不进

**进（会 mix 进 `CurrentFrameCRC`）** [前证] §3.2 + §13.1：

| 源 | 地址/形态 | 量化 |
|---|---|---|
| Infantry 数组 `0xA83DEC` / 计数 `0xA83DF8` | `obj+0x9C..0xA4` 坐标 + `0x4C93D0(obj+0x388)` | ÷10（`0x66666667`）+ 8bit |
| Unit 数组 `0x8B410C` / `0x8B4118` | 同上 + `0x4C93D0(obj+0x3A0)` | 同上 |
| Building 数组 `0xA8EB44` / `0xA8EB50` | 同上 | 同上 |
| Aircraft 数组 `0xA8022C`(Items) / `0xA80238`(Count) | `byte obj+0x241` | 原样 |
| 5 个 `LayerClass::Objects[5]`（`0x8A0360` 起，步长 `0x18`） | 每对象 `WhatAmI()` + `obj+0x9C` 坐标 ÷10；`AnimClass` 且 Type 返回 −2 则跳过 | ÷10 |
| `LogicClass::Instance 0x87F778` 簇 | 同上坐标量化 | ÷10 |
| **每帧 1 次局内 RNG** | `0x650A90`（挂在 CRC 尾）→ `0xAFA26C = ScenarioClass::Random.Random()` | 原值 |

混合式：`acc = acc*2 + sign(acc) + term`（`0x64DB33–0x64DB4A`）[前证]。

**不进（帧 CRC 全盲区）** [前证]+[推演]：

| 盲区 | 后果 | 说明 |
|---|---|---|
| **`Cell+0x134 GapsCoveringThisCell`** | **不进 per-object checksum，也不进帧 CRC** | `CellClass::CalculateChecksum v[13]=0x410410` 只折 `cell+0x10`(dword)+`cell+0x20`(byte) [前证]；但 `+0x134` 主导「被敌方裂缝覆盖」谓词 → 索敌/可见性 → 坐标分叉 → **帧 CRC 间接 DESYNC** [推演] |
| `Cell+0x12C CopyFlags` / `+0x130 ShroudCounter` / `+0x120/0x121` Shroudedness/Foggedness | 同上间接 | 随 `CellClass` 裸块 `0x148`B 进 `.SAV`，但 CRC 面不折 |
| HP / 弹药 / 目标指针 / 任务状态 / 路径 | 路径差 → 位置差 → 才进 CRC | 帧 CRC 对「同格亚像素/微漂」不敏感 |
| 粒子 `ParticleClass` / `ParticleSystemClass` | **不进帧 CRC**（不挂 Layer/Logic） | 只进 SYNC `*** Particle CRCs ***` / `*** Particle System CRCs ***` [前证] §13.2 |
| 超武 `SuperClass` / `SuperWeaponTypeClass` | **不进帧 CRC**（非 Object，无 `+0x9C`） | 仅经 House 状态与次生对象间接映射 [前证] §13.2 |
| 音频 / UI / dirty-rect / 迷雾**显示** / FPS / Sleep | 安全 | 表现层 |
| `CurrentFrame` 本身 | 不显式进 CRC | 但 RNG 与位置隐含帧序 |

### 1.3 「漏检 ≠ 安全」矩阵（演进敏感但 CRC 不可见）

| 状态 | 进 `.SAV` | 进帧 CRC | 进 v[13] | 演进敏感 | 分叉路径 |
|---|---|---|---|---|---|
| **`Cell+0x134`** | **是**（Cell 裸块 `0x148`） | **否** | **否** | **是**（索敌/可见性谓词） | 开图清零/裂缝计数 → 谓词 → 开火/移动 → 坐标 → **间接 DESYNC** |
| `Cell+0x12C/+0x130` | 是 | 否 | 否 | 是（迷雾/遮蔽） | 同上（显示+判定双面） |
| RNG 流/消费次数 | 是（`ScenarioClass::Random` 整 `0x3F4`） | **是**（每帧 1 次显式 mix） | 是 | **是** | 多抽/少抽 1 次 = 全员分叉 |
| 命令序 / `Timestamp` | 是（Queue ring） | 间接 | 是（Event 类目） | **是** | 同帧 ring 下标序改 = 分叉 |
| 寻路缓存 / 空间哈希 / AI 时间片 | 间接 | **是**（路径→坐标） | 是 | **是**（条件） | 命中/未命中不同帧 = 分叉 |
| 粒子逻辑字段（寿命/位置/Owner） | 是 | **否** | **是**（Particle 节） | 是 | **帧 CRC 不报警**，SYNC 报告才可见；混端若只动绘制 = SAFE |
| 超武充能/发射帧 | 是（经 House） | 间接（次生对象） | 间接 | 是 | TYPE 补丁改充能帧 → 发射帧不同 → 分叉 |
| 音频播放头 | 否 | 否 | 否 | 否 | 无 |

> **裁决**：诊断价值排序 = **H-D1（B 层报警预测）> H-D2（现场）> H-D5/H-D6（对拍）**；而「改演进」类（gap NOP、路径缓存 TTL、节流相位）**一律不进本批**，只登记为 desync 红线。

---

## 2. H-D1 / H-D2 早退·日志钩语义与风险

> 规格正文见 `docs/re/net_sync_fix_spec.md` §2–§3；本节只做**语义/风险/开关**裁决与 R-NET-SYNC 视角补强。**不改演进、不落代码**。

### 2.1 H-D1 — desync 预测旁路日志（L0）

| 项 | 值 |
|---|---|
| 插入点 | **`0x64C6F2`**（`jne 0x64CC61`，6B `0F 85 69 05 00 00`） |
| 开关 | `[SyncDiag] SyncEarlyLog`，默认 **0** |
| 语义 | 在 `cmp edx,esi`（`0x64C6F0`）之后、原 `jne` 之前：若 ZF=0（不等）且开关开 → 打 `DESYNC_PREDICT frame/idx/local/remote/house/ts/delay`，**然后落入原 `jne`** |
| 早退/旁路 | **无早退**。只是「分支前多一句日志」；`jne` 目标恒为 `0x64CC61`，相等路径恒 `0x64C6F8` |
| 寄存器契约 | `pushfd/pushad` 包裹；`edx/esi/eflags` 与原路径一致（尤其 ZF） |
| 风险 | **L0**：唯一触碰 = 指令槽 6B；跳板内禁写游戏内存、禁 `Random()` |
| Remove | 还原 `0F 85 69 05 00 00`；废弃 TRAMP；键置 0 |

**R-NET-SYNC 裁决**：
- **采纳为第一落地钩**。它是 B 层唯一的「报警预测」——在真正进 `0x64CC61` 写 SYNC 之前就能落一条结构化日志，且**零语义**（A 层演进、B 层判据、C 层归因全不动）。
- **「早退」语义澄清**：H-D1 **不是**早退钩，是**早记**钩。真正带控制流的「早退/静默」是 H-D10（L2，跳过 `TXT_OUT_OF_SYNC` 弹窗）——**本批明确不做**（改客户端交互，仅测试镜像）。
- 单机可关：`0x647260` 在 `0xA8D5F8` bit2/4 早退时本就无对端 CRC，`SyncEarlyLog=0` 避免噪声 [前证]。
- **V1.4 强判据**（A 开 / B 关 ≥300 帧无 `SYNC*.TXT`）= 「零语义」的可执行证明；未过 V1.4 不得宣称安全 [前证]。

### 2.2 H-D2 — desync 现场快照（L1）

| 项 | 值 |
|---|---|
| 插入点 | **`0x64CC61`**（DESYNC 处理器入口，5B `A0 80 48 B0 00`） |
| 开关 | `[SyncDiag] SyncSnapshotOnDesync`，默认 **0** |
| 语义 | 在读 `ExtraSyncInfo@0xB04880` **之前**（原首条 `mov al,[0xB04880]` 会毁 `eax` 低字节）写 `SYNC_SNAP_%u.bin`（%u=`CurrentFrame`），再执行原指令并 `jmp 0x64CC66` |
| 快照内容 | magic `"SNAP"`+ver、`CurrentFrame`、`CurrentFrameCRC`、`LatestFramesCRC[256]`、Random 状态指针（**只存指针、不抽**）、Queue 计数/游标、event 原文 111B、local/remote CRC |
| 早退/旁路 | **无早退**；写失败只 `syncSnapshotFail++` 并**静默跳过**，绝不改控制流 |
| 风险 | **L1**：只加文件写。禁写游戏内存、禁抽 `Random()`、禁跳过 `0x64DEA0`/`0x6516F0` 原报告、禁占用 `SYNC%01d.TXT` 原名 |
| Remove | 还原 `A0 80 48 B0 00`；废弃 TRAMP；键置 0 |

**R-NET-SYNC 裁决**：
- **采纳为第二落地钩**。它补齐「SYNC 报告缺现场」短板：原版 `0x64DEA0` 只打各类 CRC 明细，**不落 event 原文与 CRC 环**；H-D2 把 B 层报警瞬间的**全部输入面**钉死，便于事后区分「A 层命令分叉」vs「B 层量化漏报」vs「C 层字段盲区」。
- **与 `ExtraSyncInfo` 的关系**：`0xB04880` 开 = 原版循环 0x100 份 `SYNC%01d_%03d.TXT`；H-D2 **不替代**它，只在其前多一份独立 bin。两者可并存。
- **风险点**：文件名必须是 `SYNC_SNAP_%u.bin`，**禁止** `SYNC%01d.TXT`（会与原版报告互踩）[前证] §1.7-5。
- 失败安全：只读目录/磁盘满 → 计数 +1 后进原流程；**禁止 SEH 泄漏** [前证] §3.7。

### 2.3 开关矩阵与「不改演进」自证

| 开关 | 随动 | 默认 | 开=写什么 | 改演进？ | 卸载对称 |
|---|---|---|---|---|---|
| `SyncEarlyLog` | H-D1 | **0** | 日志行 | **否** | 还原 6B |
| `SyncSnapshotOnDesync` | H-D2 | **0** | `SYNC_SNAP_*.bin` | **否** | 还原 5B |
| `SyncMirror` | H-D5 | 0 | 独立 `g_MirrorRing`（**不碰** `0xB04474`） | **否** | 还原尾声 8B |
| `SyncCmdMirror` | H-D6/H-D6b | 0 | 命令镜像日志 | **否** | 还原 call 5B ×2 |
| （不做）`SyncSilentDesync` | H-D10 | 0 | — | **是（L2 控制流）** | 本批禁 |
| （禁）— | H-D11/H-D12 | — | — | **是（L3 契约）** | **禁** |

**自证口径**（任一钩装上后必须成立）[前证] §2.6/§4.5：
1. 同种子单机 ≥500 帧：开/关 **逐帧 `CurrentFrameCRC` 序列一致**；
2. `0x64DAB0` 与内部 `0x650A90` 调用次数不变（每帧恰 1 次 RNG）；
3. A 开 / B 关联机 ≥300 帧：**零 `SYNC*.TXT`、零 `TXT_OUT_OF_SYNC`**；
4. Remove 后原字节逐字节还原。

> **一句话**：H-D1/H-D2 是「**给演进装行车记录仪**」，不是「改演进」。任何要写 `Cell+0x134`、改 CRC 混合、插 RNG 调用、改 Timestamp 的「诊断」一律 L3 禁止。

---

## 3. Desync 点清单（混端必分叉改集对照表）

> 「混端」= 本端加载 `ra2render.dll`（含补丁/新卡），对端原版 `gamemd.exe`（无 DLL）。
> 判定沿用 M-4：**SAFE** = 无 DESYNC（可有观感分叉）；**RISK** = 条件成立才安全；**VIOLATION** = 混端必分叉。
> 主表综合 `mp_gate_residual_deep_dive.md` §4、`sav_gap_cell_abi_deep_dive.md`、`net_sync_checksum.md` §10/§13；本轮做同步演进视角重排。

### 3.1 主对照表

| ID | 改集 | 典型点 | 触碰面 | 进 `.SAV` | 进帧 CRC | 进 v[13] | 混端后果 | 判定 | 现网门控 | 诊断钩 |
|---|---|---|---|---|---|---|---|---|---|---|
| **D-GAP** | **gap NOP×3**（P-2.1/2.2/2.3） | `0x568273` / `0x577EC5` / `0x577B60` 各 6B→`90×6` | `Cell+0x134 GapsCoveringThisCell` 引用计数 | **是**（Cell 裸块 `0x148`） | **否**（间接经坐标） | **否** | 第一次 `RevealArea2/3/Reshroud` 后 `+0x134` 分叉 → 索敌/可见性 → 坐标 → **间接 DESYNC**；触发点是**开图事件**，非读档瞬间 | **VIOLATION** | `InstallGapProtectionPatch` 联机强制不装 ✓（L-2） | H-D1 可见「坐标先分叉」；H-D2 落 event+环 |
| **D-GAP-B** | SpySat 门 P-2（`0x508F8F` je→jmp） | 阻 `RevealArea3` 全图开 | 可见性演进 | 间接 | 间接 | 间接 | 一端门一端原版 ⇒ 开图语义分叉 | **VIOLATION** | `EnableSpySatGate` 0 命中（未落地） | 同上 |
| **D-S1** | SpySat TYPE | 写 `SW+0xB0/+0xF8`、`Bld+0x16A5/+0x16F0` | TYPE 规则数据 | TYPE 不进档，但改充能帧→`IsCharged/Granted` | 间接（发射次生对象） | 间接（House/Super） | 超武发射帧不同 → 分叉 | **VIOLATION**（混端）/ RISK（全端同 DLL） | 无 MpActive 门 ✗ | H-D5/H-D6 对拍 |
| **D-S2** | Scenario 标志 | `flags &= ~0x1000` | 可序列化全局 | **是** | 间接 | 间接 | 演进不同 → 存档/CRC 面分叉 | **RISK→VIOLATION** | 无门 ✗ | 同上 |
| **D-S3** | House+0x577A | `SpySatActive=0` | House 字段 | **是**（Save_Sides） | 间接 | 间接 | 解除裂缝锁死=玩法变更；混端分叉 | **RISK→VIOLATION** | 无门 ✗ | 同上 |
| **D-L2** | 寻敌节流 | `>>4` 指针键 + interval=8；Threat Retention | 寻敌调用时序/返回值 | 间接 | **是**（目标→开火→坐标） | 间接 | 相位不一致必 desync；指针键=禁 | **VIOLATION**（interval>1 / pointer 键）/ RISK（修键后） | 联机强制 interval=1 + position ✓ | H-D5 逐帧 CRC 环最早暴露 |
| **D-PATH** | **寻路缓存** | PathFinder 簇 / `MapClass::Cost 0x583180` / `CanEnterCell 0x5840C0` | 路径结果 | 间接 | **是**（路径→坐标） | 是（Foot/Techno） | **条件安全**：键须逻辑态；失效由逻辑事件驱动；命中/未命中须**同帧同结果**。TTL 墙钟/渲染帧失效 = 混端必分叉 | **RISK**（保序则 SAFE） | 规格约束（`path_cache_oracle_spec.md` §6）；oracle 未落地 | H-D5+H-D6 对拍是验收探针 |
| **D-AI** | AI 时间片/降频 | `CurrentFrame % 8/100`；`Weight_Current` 浮点序 | 遍历/决策时序 | 间接 | 间接 | 间接 | 分片规则须 `(CurrentFrame+index)%k` 纯函数；**只有一端提前扫到 = desync** | **RISK** | 规格约束 | H-D6 命令镜像序 |
| **D-CRT-L2** | CRT 池 L2 | 高频小对象池化 | 堆布局/指针序 | 否（指针序敏感） | 间接 | 否 | 若引入指针哈希/枚举序 → 分叉；L1 纯复用 SAFE | **RISK**(L2)/ **SAFE**(L1) | 规格：联机仅 L1 | H-D5 |
| **D-RNG** | RNG 流/次数 | `Random 0x65C780` / `RandomRanged 0x65C7E0`；每帧 `0x650A90` | 随机流 | **是** | **是** | 是 | 多抽/少抽/换 Global/`rand()`/墙钟 = **全员分叉** | **VIOLATION**（改流） | 红线 §5.1 | H-D8（本批不做）；V3.7 零 RNG |
| **D-CMD** | 命令序/Timestamp | `0x64C380` / `FillEvent_*` / `0x4C6CB0` | 命令流 | 是 | 间接 | 是 | 同帧 ring 序改 / 本地立即生效 = 分叉 | **VIOLATION** | 红线 §5.1 / H-D12 禁 | H-D6/H-D6b |
| **D-CRC** | 帧 CRC 算法 | `0x64DAB0` ÷10 / 混合式 / `0x650A90` 次数 / `0x64C6E2` 宽度 | 判据本体 | 否 | **本体** | 否 | 改了 = 假 desync 或漏报 | **VIOLATION** | H-D11 禁 | — |
| **D-CKSM** | CalculateChecksum 字段 | 全部 `*::v[13]` | 归因/存档格式 | 是 | 否 | **本体** | 重排/删 = 改存档+归因 | **VIOLATION** | 红线；只许新魔数追加 | — |
| **D-PART** | **particle 新卡** | Particle/PSys 槽 69 Draw 剔除（M-9） | 纯绘制虚表 | **否** | **否** | 否（绘制参数不动逻辑字段） | **无 DESYNC**；烟雾/尾迹可见性观感分叉 | **SAFE** | `EnableParticleFog` 0 命中；可联机保留 | 不需要（无演进） |
| **D-PART-LOGIC** | 粒子**逻辑**字段 | 寿命/位置/Owner | ParticleClass 状态 | 是 | **否** | **是** | 帧 CRC 不报警；SYNC 才可见；混端逻辑改 = 必分叉（慢报警） | **RISK→VIOLATION** | 禁改逻辑字段 | H-D2 后看 SYNC Particle 节 |
| **D-VXL13** | vxl 缓存预热 / 影缓存 | L-VXL-1/3 | 绘制缓存 | **否** | **否** | 否 | **无 DESYNC** | **SAFE** | 未落地；可联机保留 | 不需要 |
| **D-VXL2** | SHP 影强制跳过 | L-VXL-2 | 绘制 | **否** | **否** | 否 | 无 DESYNC，脚下影观感分叉 | **SAFE**（观感） | 规格 G0.5：MpActive 强制不装 | 不需要 |
| **D-AUDIO** | 音频限频 | `PlayGlobal@0x750920` / `PlayAt@0x7509E0` 入口丢弃 | 声道池调度 | **否** | **否** | 否（Play* 内 0 同步 RNG） | **无 DESYNC**；本地少放音 | **SAFE** | `EnableAudioThrottling` 0 命中；可联机保留 | 不需要 |
| **D-L4/B1B2** | L4 全量刷 / 混色桩 | `0x6D3D99` / `0x47F40F` / `0x47F4AE` | 像素 | 否 | 否 | 否 | 无 DESYNC | **SAFE** | E2 运行期总闸 | 不需要 |
| **D-RADAR** | 雷达×2 | Plot/Pending 像素 | 像素 | 否 | 否 | 否 | 无 DESYNC（缺陷1 崩溃另论） | **SAFE** | MinimapFog 联机强制 0 ✓ | 不需要 |
| **D-EVERSEEN** | everSeen 网格 | `s_everSeenGrid`（DLL 私有） | 表现 | 否 | 否 | 否 | 无 DESYNC；读档清零=体验限制 | **SAFE** | — | 不需要 |

### 3.2 五类焦点裁决（gap / particle / audio / path cache / vxl）

| 焦点 | 混端裁决 | 一句话 | 落地姿态 |
|---|---|---|---|
| **gap NOP** | **VIOLATION（致命）** | `Cell+0x134` 进档、不进 per-object checksum、主导索敌谓词 → **漏检但必炸** | 联机强制不装（L-2 已落）；文档禁令；诊断靠 H-D1/H-D2 事后归因 |
| **particle** | **SAFE**（绘制）/ **VIOLATION**（逻辑字段） | 只动 Draw 剔除 = 无 DESYNC、可观感分叉；动寿命/位置/Owner = 进 v[13] 进档 = 慢分叉 | 可联机保留绘制卡；逻辑字段红线 |
| **audio** | **SAFE** | Play* 丢弃 0 同步 RNG；纯声道池 | 可联机保留；默认关更稳 |
| **path cache** | **RISK（条件安全）** | 不保序/TTL 墙钟失效 = 混端必分叉；保序+逻辑失效 = 安全 | 落地前必须 H-D5/H-D6 双端对拍 MATCH |
| **vxl** | **SAFE**（缓存/影） | L-VXL-1/3 无 DESYNC；L-VXL-2 观感分叉 | 观感一致要求时 MpActive 不装 L-VXL-2 |

### 3.3 风险排序（混端视角，同步演进序）

1. **P0 致命**：gap 三处 NOP（`Cell+0x134`）——已被 L-2 联机不装门挡住（安装期）。
2. **P0 致命**：S1 TYPE + S2/S3 状态写——**当前无门，发布前最大残余**（L-3/L-4）。
3. **P1**：L2 节流 / Threat Retention / pointer 键——已被 L-1 强制 interval=1 + position 挡住。
4. **P1 条件**：path cache / AI 时间片 / CRT L2——保序才安全；对拍是验收探针。
5. **P2 观感**：particle / vxl 影 / audio——无 DESYNC；混端可共存。
6. **P2 卫生**：everSeen、L4/B1B2、雷达像素。

---

## 4. 同步演进「可动 / 条件 / 禁止」总表（R-NET-SYNC 裁决）

| 类 | 项 | 裁决 | 条件/理由 |
|---|---|---|---|
| **禁止（L3）** | 帧 CRC 混合式 / ÷10 / `0x650A90` 次数 / `0x64C6E2` 宽度 | **禁改** | H-D11；改=假 desync/漏报 |
| **禁止** | 命令序 / `Timestamp` / 「本地立即生效」 | **禁改** | H-D12；破坏锁步 |
| **禁止** | RNG 流与消费次数；换 Global/`rand()`/墙钟 | **禁改** | 同步契约 |
| **禁止** | CalculateChecksum 字段重排/删 | **禁改** | 存档+归因；只许新魔数追加 |
| **禁止** | `Cell+0x134` 演进（gap NOP 在混端） | **禁混端** | 不进 CRC 却主导谓词 |
| **条件** | 寻路缓存 / 空间哈希 / AI 时间片 / 命令批处理 | 保序 + `CurrentFrame` 纯函数 | H-D5/H-D6 对拍 MATCH |
| **条件** | `RandomRanged` 实现提速 | 输出序列+拒绝采样消耗逐次相同 | 红线 §5.2 |
| **可动** | Blit/RLE、dirty-rect、迷雾**显示**、雷达点、音频、FPS/Sleep、UI、日志桩 `0x4068E0` | 纯表现 | 不进同步契约 |
| **可动** | particle Draw 剔除、vxl 影/缓存、音频限频、L4/B1B2、everSeen | 表现层 SAFE | 混端可共存（观感可不一致） |
| **本批落地** | **H-D1 / H-D2 诊断钩（默认关）** | **只旁路** | 不改演进；V1.x/V2.x 验收 |
| **本批规格** | H-D5 / H-D6(+b) 对拍套件 | 只旁路 | 对拍探针；为 path/AI 类落地前置 |
| **明确不做** | H-D10 静默早停 | L2 | 改交互；仅测试镜像 |
| **明确禁止** | H-D11 / H-D12 | L3 | 同步契约本体 |

---

## 5. 可落地顺序（诊断钩优先，不改演进）

### 5.1 推荐落地波次

| 波 | 内容 | 开关 | 风险 | 验收门 |
|---|---|---|---|---|
| **W1（本批）** | **H-D1**（`0x64C6F2`）+ **H-D2**（`0x64CC61`） | `SyncEarlyLog` / `SyncSnapshotOnDesync`，默认 0 | L0 / L1 | V1.1–V1.6、V2.1–V2.6；A 开 B 关零 OOS |
| **W2** | H-D5（`0x64DE75`）+ H-D6（`0x64C911`）+ H-D6b（`0x64CC0A`） | `SyncMirror` / `SyncCmdMirror` | L0 | V3.1–V3.8；双端对拍 MATCH |
| **W3** | 混端门禁文档 + 现网残余（S2/S3/TYPE 的 `MpActive` 旁路）——**规格归 MP 轨，本任务只登记** | — | — | 混联杀手用例 [待实测] |
| **不做** | 任何改演进的「优化」（gap 混端、CRC 改宽、RNG 插桩、Timestamp 改语义） | — | L3 | — |

### 5.2 实施约束（摘自 `net_sync_fix_spec.md` §1.7 / §11.3，作 checklist）

- [ ] 不改 `0x64DAB0` 混合式、÷10 量化、`0x650A90` 调用次数、`0x64C6E2` 比较宽度
- [ ] 不改 `Random` 流与消费次数；镜像/日志/快照内 **零** RNG
- [ ] 不改命令执行序、`Timestamp` 语义；不「本地立即生效」
- [ ] 不写可序列化游戏字段；不写 `0xB04474`（镜像必须独立）
- [ ] 不占用 `SYNC%01d.TXT` / `SYNC%01d_%03d.TXT`（快照用 `SYNC_SNAP_%u.bin`）
- [ ] 不把跳板写入 gamemd `.detour` 节
- [ ] Install/Remove **对称**；开关关不干净 = 缺陷
- [ ] 阈值 `0xA8E30C` 不改（L3）
- [ ] 落地前过 `HOOK_POINT_MATRIX.md` 冲突核对
- [ ] 本任务写作用域仅本文 + `out/re_work/re_sprint/R_net_sync/**`

### 5.3 与 SyncEarlyLog / SyncSnapshotOnDesync 的运维口径

| 场景 | `SyncEarlyLog` | `SyncSnapshotOnDesync` | 说明 |
|---|---|---|---|
| 发行 / 正式联机 | 0 | 0 | 默认零副作用 |
| 诊断联机（怀疑 desync） | 1 | 1 | 双端同开；对拍 `DESYNC_PREDICT` 条数应一致 |
| 单机回归 | 0（或 1 做噪声统计） | 0 | `0x647260` 早退，无对端 |
| 排障复现 | 1 | 1 | 快照 bin + 原版 SYNC*.TXT 并存 |

---

## 6. 未决 / 待实测

| # | 项 | 档 | 归属 |
|---|---|---|---|
| 1 | 混联杀手用例（一端 DLL+门控、一端原版）≥2 局零 OOS | [待实测] | MP 轨 / Gate3 |
| 2 | H-D1/H-D2 装上后 V1.4 / V2.3 真机通过 | [待实测] | 实施方 |
| 3 | path cache oracle 命中率与 MP 零 DESYNC | [待实测] | `path_cache_oracle_spec.md` §4 |
| 4 | `0xA8E30C` 写入者（宽限阈值） | [待复核] | `net_sync_checksum.md` §7.3 |
| 5 | Aircraft 簇 `0xA8022C` 类归属（Aircraft vs House） | [待复核] | `savegame_block_manifest.md` §8.4-bis |
| 6 | `0x4C93D0` 字段语义（速度/朝向/血量档？） | [待复核] | §7.1 |
| 7 | S2/S3/TYPE 的 `MpActive` 旁路落地状态 | [待实测] | Gate2 未闭环 |

---

## 7. 附：关键地址速查（R-NET-SYNC 增量）

| 地址 | 名 | 本任务角色 |
|---|---|---|
| `0x64DAB0` / `0xAC51FC` | Compute_Frame_CRC / CurrentFrameCRC | 演进 B 层；**禁改算法** |
| `0x64C6E2–0x64C6F2` | desync 判据 `cmp/jne` | H-D1 插入点 |
| `0x64CC61` | DESYNC 处理器入口 | H-D2 插入点 |
| `0x64DE75` | `0x64DAB0` 尾声 | H-D5 插入点 |
| `0x64C911` / `0x64CC0A` | `call 0x4C6CB0` 主/次站点 | H-D6/H-D6b |
| `0x650A90` | 每帧 RNG 侧信道 | 消费次数红线 |
| `0xB04474` | `LatestFramesCRC[256]` | 只读；镜像禁写 |
| `0xB04880` | `ExtraSyncInfo` | 原版多份 SYNC 开关 |
| `0xA8E30C` | 报告阈值 | L3 禁改 |
| `0x568273` / `0x577EC5` / `0x577B60` | gap 清 `Cell+0x134` 三点 | 混端 VIOLATION 源 |
| `0x410410` | `CellClass::CalculateChecksum v[13]` | 只折 `+0x10`/`+0x20`；**漏 `+0x134`** |
| `0x87F778` / `0x8A0360` | LogicClass / LayerClass::Objects[5] | 帧 CRC 尾部簇 |
