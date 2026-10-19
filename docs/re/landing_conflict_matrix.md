# 落地防冲突对照矩阵 · landing_conflict_matrix（R-ANTI-DUP）

> **任务**：R-ANTI-DUP · 历史 M-8/M-9/M-10/A-14 与新卡 gap/wpn/part/audio/crt 同面 VA/钩点对照  
> **产物**：`docs/re/landing_conflict_matrix.md` + `out/re_work/re_sprint/R_anti_dup/**`  
> **证据基线**：`gamemd.exe` 1.001 · SHA-256 `73201CC0…F67476` · MD5 `4f37486e…` · ImageBase `0x00400000` · `file_off = VA − 0x400000`  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **口径**：状态词 = **已装**（真机/静态确认已写入）/ **互斥**（同字节面，禁双装）/ **可并存**（不同面或不同钩型，可叠）  
> **只读源**：`landing_pack_inventory.md`、`cards_inventory.csv`、`landing_pack_{net_fix,particle,gap_spysat,crt_audio_particle,gap_p21,gap_p223,audio_throttle,particle_fog,crt_l1,weapons_lw}.md`、`INSTALLED_HOOKS_AUDIT.md`  
> **禁写**：ra2render / gamemd / 台账 / 看板

---

## 0. 同面总览（VA 为键）

| 同面键（VA / 钩点） | 历史卡 | 新卡 | 处置 | 说明 |
|---|---|---|---|---|
| `0x00568273` 6B NOP（RevealArea2 清 `Cell+0x134`） | M-10 **P-1 #1** | **ZC-GAP-P21** | **已装 · 互斥** | 新卡已落地（A1/A2 PASS）；**禁止**再装 M-10 P-1 该点 |
| `0x00577EC5` 6B NOP（RevealArea3 清 `Cell+0x134`） | M-10 **P-1 #2** | **ZC-GAP-P223** | **已装 · 互斥** | 新卡已落地（installed 计数）；禁重复 |
| `0x00577B60` 6B NOP（Reshroud 清 `Cell+0x134`） | M-10 **P-1 #3** | **ZC-GAP-P223** | **已装 · 互斥** | 同上；三点合并 `R-GAP-MERGE` installed==3 |
| `0x00508F8F` 2B `je→jmp`（SpySat 门控） | M-10 **P-2** | （gap 新卡不含） | **可并存** | 另面；与 P-1 三点不重叠。只在需要「干净回滚、不动 TYPE」时装 |
| TYPE 四字段备份/Remove 还原（G-07） | M-10 **P-3** | （无） | **可并存** | 数据面，无 .text 冲突；S1 改 TYPE 时必须带 P-3 |
| 槽 69 DWORD `0x007EFA68` / `0x007EFCB0` | M-9 · A-14 模三 | **ZC-PART-FOG** | **互斥** | 完全同槽同 DWORD；**只装 ZC-PART-FOG**（M-9 已被其收敛） |
| `0x00750920` 6B + `0x007509E0` 5B（PlayGlobal/PlayAt） | A-14 模二 | **ZC-AUDIO-THROT** | **互斥** | 同 VA；新卡超集（+AT-C `0x00750E20`）。A-14 原稿 PlayAt 误写 6B（F-01），**禁止按 A-14 字节装** |
| `0x00750E20` 5B（PlayIndexAtPos） | （A-14 无） | **ZC-AUDIO-THROT AT-C** | 可并存（新卡独有） | 默认 `ThrottlePlayIndexAtPos=1` |
| `0x007C8E17` / `0x007C8B3D`（CRT `_new/_delete`） | A-14 **模一**（L2 池） | ZC-CRT-**L2**-C34（待批）· **L1 不碰此面** | **互斥**（对 L2） | A-14 模一 ≡ L2 池入口。**ZC-CRT-L1 是另一面**（见下行） |
| `0x004E9A10` / `0x004E97B0` / `0x006F8F8A`（Vector Clear/Reserve） | （历史无） | **ZC-CRT-L1** | **可并存** | 向量复用面，与 A-14 CRT 池入口不同；可与 L2 池叠，但 L2 须后置 A/B |
| `0x0064C6F2` / `0x0064CC61`（H-D1/H-D2 跳板点） | M-8 | **ZC-HD-DIAG** | **互斥（同面收敛）** | ZC-HD-DIAG 为 M-8 正式卡；T0=`0x01B00000` cave 由执行方统一 |
| `0x004894AB` `0x0048975D` `0x00489AE4` `0x00489B33` `0x00701900` `0x0048923D` | （历史无） | **ZC-WPN-LW** | **可并存** | 伤害链新面；禁混地形特效 `0x48A3xx` 四点 |

---

## 1. 历史卡 × 新卡 矩阵（同面才标冲突）

| 历史 \ 新 | **gap** (P21/P223) | **wpn** (LW) | **part** (FOG) | **audio** (THROT) | **crt** (L1) |
|---|---|---|---|---|---|
| **M-8** net_fix | 可并存 | 可并存 | 可并存 | 可并存 | 可并存 |
| **M-9** particle | 可并存 | 可并存 | **互斥**（同槽69） | 可并存 | 可并存 |
| **M-10** gap_spysat | **互斥**（P-1 三点）· P-2/P-3 可并存 | 可并存 | 可并存 | 可并存 | 可并存 |
| **A-14** crt/audio/part | 可并存 | 可并存 | **互斥**（模三） | **互斥**（模二） | L1 **可并存** · 若装 L2 则与模一 **互斥** |

**新卡内部**（同批交叉）：

| | gap | wpn | part | audio | crt L1 |
|---|---|---|---|---|---|
| **gap** | — | 可并存 | 可并存 | 可并存 | 可并存 |
| **wpn** | | — | 可并存 | 可并存 | 可并存（L-W1 禁碰 `_new` 本体；与 L1 无字节重叠） |
| **part** | | | — | 可并存 | 可并存 |
| **audio** | | | | — | 可并存 |
| **crt L1** | | | | | — |

> 新卡两两**无同面字节冲突**；冲突全部在「历史包 ↔ 对应新卡」收敛关系上。

---

## 2. 钩点明细（VA 级）

### 2.1 gap 面（裂缝 `Cell+0x134`）

| 钩点 | VA | 形态 | M-10 | 新卡 | 状态 |
|---|---|---|---|---|---|
| RevealArea2 清零 | `0x568273` | 6B→`90×6` | P-1 #1 | ZC-GAP-P21 | **已装** |
| RevealArea3 清零 | `0x577EC5` | 6B→`90×6` | P-1 #2 | ZC-GAP-P223 | **已装** |
| Reshroud 清零 | `0x577B60` | 6B→`90×6` | P-1 #3 | ZC-GAP-P223 | **已装** |
| SpySat 门 | `0x508F8F` | 2B `74→EB` | P-2 | — | 可并存（按需） |
| G-07 TYPE 还原 | TYPE 4 处 | 数据备份 | P-3 | — | 可并存（S1 伴生） |

开关：`[FogOfWar] EnableGapProtection`（P21/P223 共用）· `EnableSpySatGate` · `EnableSpySatRadarSweep`  
红线：gap = **VIOLATION 禁混端**；MpActive 强制不装；禁 Super 侧叠写 `Cell+0x134`。

### 2.2 part 面（槽 69 双钩）

| 钩点 | VA | 原 DWORD (LE) | M-9 / A-14模三 | 新卡 | 状态 |
|---|---|---|---|---|---|
| ParticleClass::Draw 槽 | `0x7EFA68` | `C0 CE 62 00` | 同 | ZC-PART-FOG hook14 | **互斥→采新卡** |
| ParticleSystemClass::Draw 槽 | `0x7EFCB0` | `80 E2 62 00` | 同 | ZC-PART-FOG hook15 | **互斥→采新卡** |

禁重装五槽：Unit `0x7F5D84` / Inf `0x7EB16C` / Air `0x7E23B8` / Bld `0x7E3FD0` / Bullet `0x7E47F8`。  
开关：`[FogOfWar] EnableParticleFog` 默认 0。字节序必须 **LE**（R-E08）。

### 2.3 audio 面（Play* 入口）

| 钩点 | VA | 覆盖 | A-14 模二 | ZC-AUDIO-THROT | 状态 |
|---|---|---|---|---|---|
| PlayGlobal | `0x750920` | 6B | 有 | AT-A | **互斥→采新卡** |
| PlayAt | `0x7509E0` | **5B**（A-14 误 6B） | 有（字节错） | AT-B | **互斥→采新卡** |
| PlayIndexAtPos | `0x750E20` | 5B | 无 | AT-C | 新卡独有 |

禁钩：EVA `0x752700` · 零接触 `0x64DE3F`。开关：`[AudioThrottle] Enable` 默认 0。

### 2.4 crt 面（两面切勿混谈）

| 面 | VA | 历史 | 新卡 | 关系 |
|---|---|---|---|---|
| **L2 池入口** | `0x7C8E17`（new 6B）/ `0x7C8B3D`（delete 9B） | A-14 模一 | ZC-CRT-L2-C34（**待批**） | **互斥**；L2 禁与 A-14 模一双装 |
| **L1 向量复用** | `0x4E9A10` / `0x4E97B0`（Clear 6B）+ `0x6F8F8A`（Reserve 窗 30B） | 无 | **ZC-CRT-L1** | **可并存**（不同 VA） |

开关：`[MemoryPool] EnableMemoryPool` **启动期锁**；L1 键 `VectorReuse`/`VectorReserve`；L2 键 `MemPoolClass34`。  
> 【W3 勘误 · W3-A6/ISSUE-SECTION-MEMORYPOOL】[W3-Lead临时裁决] 改前：[MemoryPool] EnableMemoryPool；改后：[System] ; DC-01 裁决口径: 使用既有 [System] 节，零新增节 EnableMemoryPool=0；依据：docs/re/dispatch/W3_20261001_Lead_DECISION_AND_BOARD.md:40; docs/re/pending_execution_master_table.md:410-412；分级：P0
红线：L1 **禁碰** L2 入口；WPN L-W1 **禁**改 `_new/_delete` 本体与 `0x48A3xx` 地形四点。

### 2.5 wpn 面（伤害生产链，历史无）

| 步 | VA | 形态 | 键 |
|---|---|---|---|
| L-W1 池化 ×4 | `0x4894AB` `0x48975D` `0x489AE4` `0x489B33` | 5B `E8 rel32` 等长 | `EnableDamageGroupPool` |
| L-W2 遥测 | `0x701900` | 6B trampoline | `EnableDamageTelemetry` |
| L-W3 乘序锁 | `0x48923D` | 7B trampoline（重放 fmul） | `EnableVersesAudit` |

卡内串序 **L1→L2→L3**。禁混 `0x48A323/0x48A3B1/0x48A3F2/0x48A449`（地形特效 op_new）。

### 2.6 M-8 / ZC-HD-DIAG 面（同步诊断）

| 钩点 | VA / 槽位 | M-8 | ZC-HD-DIAG | 状态 |
|---|---|---|---|---|
| H-D1 | `0x64C6F2` | 跳板 | 同 | **同面收敛→采 ZC-HD-DIAG** |
| H-D2 | `0x64CC61` | 跳板 | 同 | 同上 |
| H-D5/H-D6 | 对拍规格 | 有 | 承接 | 同上 |
| Cave | T0=`0x01B00000` | VirtualAlloc 固定基 | 同 | 失败→该项不装 |

开关：`[SyncDiag] SyncEarlyLog` 等，默认 0。H-D5 用 `0F B6 C0`（R-E10，禁 `83 E0 FF`）。禁写 `.detour`。

---

## 3. 安装顺序（推荐）

> 原则：**同面只装新卡**；历史包降级为「规格源/字节校验源」，不重复写入。  
> 串行键（盘点口径）：gap `installed==3` → audio/particle 钩后 → L4/OPT-1 → CRT L1 锁定 → 联机对拍。

| 序 | 卡 | 面 | 前置 | 默认 | 装否 |
|---:|---|---|---|---|---|
| 0 | ~~M-10 P-1~~ / ~~M-9~~ / ~~A-14 整包~~ | — | — | — | **不装**（被新卡收敛） |
| 1 | **ZC-GAP-P21** | `0x568273` | G0.1–G0.6 | 键=1 才装 | **已装** |
| 2 | **ZC-GAP-P223** | `0x577EC5` `0x577B60` | P21 后（G0.7 推荐） | 同键 | **已装** |
| 2b | R-GAP-MERGE | 三点合并校验 | 1+2 | — | **已装**（installed==3） |
| 3 | **ZC-HD-DIAG**（M-8 正式面） | `0x64C6F2` `0x64CC61` + cave | 无（可与 1–2 并行） | 默认 0 | 就绪 |
| 4 | **ZC-AUDIO-THROT** | `0x750920` `0x7509E0` `0x750E20` | gap 已装（ZB2 键） | Enable=0 | 就绪 |
| 5 | **ZC-PART-FOG** | 槽69 ×2 | 同上；不碰五槽 | Enable=0 | 就绪 |
| 6 | （可选）M-10 **P-2** SpySat 门 | `0x508F8F` | 与 S1 二选一策略 | EnableSpySatGate | 按需 |
| 6b | （可选）M-10 **P-3** G-07 | TYPE 数据 | 仅当 S1 动 TYPE | 随既有键 | 按需 |
| 7 | **ZC-CRT-L1** | `0x4E9A10` `0x4E97B0` `0x6F8F8A` | 建议 L4/OPT-1 后（ZB3 键） | 启动期锁，默认全关 | 就绪 |
| 8 | **ZC-WPN-LW** | 六点伤害链 | 卡内 L1→L2→L3；与 CRT 无字节争用，可紧随 7 | 三键默认 0 | 就绪 |
| 9 | ZC-CRT-L2-C34 | `0x7C8E17`/`0x7C8B3D` 族 | **必须** L1 后；A/B 三态 | 待批 | 待批 |
| 10 | ZB5 联机对拍 | 不装补丁 | 1–8 锁定 + DUAL-LAN | — | 待批 |

**回滚序**：逆安装序；gap 三点逆序回滚已有实测 PASS（P223 RESULT）。CRT L1/L2 均启动期锁，**禁热切**。

---

## 4. 装机前门禁（防重复写入检查单）

1. 读 `0x168273`/`0x177EC5`/`0x177B60`：若已是 `90×6` → 报「gap 已打」跳过，**不得**再按 M-10 装。  
2. 读 `0x7EFA68`/`0x7EFCB0` DWORD：若已指向 Hook_* → part 已装，禁 M-9/新卡双写。  
3. 读 `0x750920` 首 6B / `0x7509E0` 首 5B：匹配原字节才允许 AT 装；若见 `E9` 则已装。  
4. CRT：确认 L1 跳板未覆盖 `0x7C8E17`；L2 未与 A-14 模一并存。  
5. WPN：安装后 `0x48A323/0x48A3B1/0x48A3F2/0x48A449` 必须逐位等于原版。  
6. 全部开关默认 0；显式置 1 才写入。gap 在 MpActive 下强制不装。

---

## 5. 结论摘要

- **互斥 4 组**：gap 三点（M-10 P-1 ↔ ZC-GAP-P21/P223）· 槽69（M-9/A-14模三 ↔ ZC-PART-FOG）· Play*（A-14模二 ↔ ZC-AUDIO-THROT）· CRT 池入口（A-14模一 ↔ ZC-CRT-L2）。  
- **可并存**：M-10 P-2/P-3 · ZC-CRT-L1（与 A-14 CRT 非同面）· ZC-WPN-LW（全新面）· M-8 面与 gap/wpn/crt 无争用。  
- **已装**：ZC-GAP-P21 + ZC-GAP-P223（installed==3）。  
- **历史包处置**：M-8/M-9/M-10 P-1/A-14 → **只读规格源**；落地一律走新卡，防止同面双写与 A-14 PlayAt 6B 错字节。
