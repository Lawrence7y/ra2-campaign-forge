# R-WPN-LAND 伤害生产链落地规格（Weapons Damage Landing Spec）

> **文档标识**：`docs/re/weapons_damage_landing.md`
> **任务编号**：R-WPN-LAND（由 T21 R-WARHEAD + `weapons_damage_production.md` 收成）
> **逆向目标**：`ra2youli/gamemd.exe` YR 1.001，ImageBase `0x00400000`，`FileOffset = VA − 0x00400000`
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **本轮实测 MD5**：`4f37486e5b0dbe2ae5f45aeee0f98367` [实证]
> **证据分级**：`[实证]` = VA + FileOffset + 机器码（`out/re_work/re_sprint/R_wpn_land/claims.txt`）；`[推演]` = 相邻实证 + ABI 惯例；`[待实测]` = 需真机
> **上游深潜**：`docs/re/weapons_damage_production.md`（S24/S26）、`docs/re/warhead_verses_residual_p2.md`、`out/re_work/re_sprint/R_warhead/claims.txt`（T21）、`docs/re/telemetry_and_switches_spec.md`、`docs/re/landing_pack_particle.md`、`docs/re/landing_pack_gap_p223.md`
> **边界**：只读逆向 + 规格落地；不改 `ra2render/**`、`gamemd.exe`、`ra2youli/**`、`tools/**`、台账/看板/ATLAS

---

## 0. 一页结论

| 维度 | 结论 | 级别 |
|---|---|---|
| **可落地项数** | **3 项可落地**（L-W1 池化修复 / L-W2 插桩加固 / L-W3 乘序审计）+ **2 项交叉引用**（L-W4 音频限频、L-W5 粒子迷雾剔除） | [实证] |
| **限频可动面** | 伤害**逻辑链本体 0 个限频点**（全部触碰同步 PRNG 或改变命中帧）；仅表现层（语音/震屏，走 Global RNG）可限频，已由 R-AUDIO-LIMIT 覆盖 | [实证] |
| **加固可动面** | DamageGroup 池化（保序）+ 入口遥测 + 乘序审计锁 | [实证] |
| **修复可动面** | DamageGroup 逐候选堆分配（6 处 alloc / 4 处 free）→ 静态池 | [实证] |
| **乘序红线** | `GetTotalDamage 0x48923D` 的 `fmul [edi+edx*8+0xA0]` 与 `ReceiveDamage 0x701939` 的 `fdivr` 链**禁止改序/合并/缓存** | [实证] |
| **RNG 禁区** | 伤害链 12 处**局内同步 PRNG**（P16-P27）零容忍；另有 6 处局外 Global RNG 可安全限频 | [实证] |
| **gap/粒子/迷雾交叉** | ReceiveDamage **不受**可见性/迷雾/裂缝谓词门控；粒子迷雾剔除仅限 Draw 层，逻辑侧 PRNG 必须照常消费 | [实证] |

---

## 1. 伤害生产链落地项（限频 / 加固 / 修复）

### 1.1 落地项总表

| # | 类别 | 名称 | 目标 VA | 原字节（前 5B） | 开关（默认） | 回滚 | 确定性 |
|---|---|---|---|---|---|---|---|
| **L-W1** | 修复 | DamageGroup 池化 | `0x4894AB` / `0x48975D`（alloc）<br>`0x489AE4` / `0x489B33`（free） | `E8 67 F9 33 00` / `E8 B5 F6 33 00`<br>`E8 54 F0 33 00` / `E8 05 F0 33 00` | `EnableDamageGroupPool=0` | memcpy 还原 4×5B | **安全**（保序、0 PRNG） |
| **L-W2** | 加固 | ReceiveDamage 入口遥测 | `0x701900` | `81 EC B4 00 00 00` | `EnableDamageTelemetry=0` | 还原 6B 序言 | **安全**（纯读） |
| **L-W3** | 加固 | Verses 乘序审计锁 | `0x48923D` | `DC 8C D7 A0 00 00 00` | `EnableVersesAudit=0` | 还原 7B（或旁路 JMP） | **安全**（纯读断言） |
| L-W4 | 限频 | 伤害语音/震屏 | 见 R-AUDIO-LIMIT | — | `EnableAudioThrottle` | 见该包 | 安全（Global RNG） |
| L-W5 | 交叉 | 粒子/迷雾剔除 | 见 landing_pack_particle | — | `EnableParticleFog` | 见该包 | 安全（仅 Draw） |

### 1.2 L-W1 DamageGroup 池化（修复）

**问题**：`DamageArea 0x489280` 阶段 A 对每个候选对象执行 `push 8; call 0x7C8E17`（堆分配 8B DamageGroup），阶段 B 逐个 `call 0x7C8B3D` 释放。高密度弹幕场景 O(弹数 × r² × 密度) 次堆操作，是明确热点。

**方案**：替换为**静态/TLS 固定池**（容量 256，溢出退回原堆分配），保持 push 顺序与遍历序不变。

**字节锚点** [实证]：

| 点 | VA | FileOff | 原字节 | 语义 |
|---|---|---|---|---|
| alloc-1 | `0x4894AB` | `0x894AB` | `E8 67 F9 33 00` | `call 0x7C8E17`（格子链表候选） |
| alloc-2 | `0x48975D` | `0x8975D` | `E8 B5 F6 33 00` | `call 0x7C8E17`（空间桶候选） |
| free-1 | `0x489AE4` | `0x89AE4` | `E8 54 F0 33 00` | `call 0x7C8B3D`（结算中释放） |
| free-2 | `0x489B33` | `0x89B33` | `E8 05 F0 33 00` | `call 0x7C8B3D`（结算尾释放） |

> **注意**：`0x48A323` / `0x48A3B1` / `0x48A3F2` / `0x48A449` 四处 `call 0x7C8E17` 是**地形特效**（残骸/扬尘/弹坑动画）分配，**不在池化范围**——它们紧随 P20/P21/P22 PRNG 判定，改分配器不影响 PRNG 序但不属 DamageGroup 语义。

**安装**：`E8 rel32` 等长替换为 `call PoolAlloc` / `call PoolFree`（5 字节），trampoline 不需要。

**开关**：`[Logic] EnableDamageGroupPool=0`（默认关；1=安装）。

**回滚**：硬回滚 `memcpy` 还原 4 处 5 字节；软回滚 `EnableDamageGroupPool=0` + 重启进程。

**确定性论证**：池分配返回的指针不同，但 DamageGroup 是**临时容器**（`{obj*, dist}`），其指针值不进任何 PRNG、不写存档、不进帧 CRC。遍历序由 push 顺序决定，池化不改 push 顺序 → `ReceiveDamage` 调用序不变 → PRNG 序不变。[实证 + 推演]

### 1.3 L-W2 ReceiveDamage 入口遥测（加固/插桩）

**问题**：伤害结算黑盒，无可观测性。

**方案**：`0x701900` 入口 6 字节序言 `81 EC B4 00 00 00`（`sub esp, 0xb4`）等长替换为 `JMP hook`（5B）+ `NOP`（1B），hook 内记录 `{this, *pDamage, pWarhead, pAttacker}` 后跳回 `0x701906`。

**开关**：`[Telemetry] EnableDamageTelemetry=0`（默认关）。

**遥测计数器**：`rdCalls`（入口次数）、`rdTotalDamage`（累计伤害）、`rdDeaths`（Health 归零次数）、`rdHealCalls`（pDamage<0 次数）。

**回滚**：还原 6 字节原序言。

**确定性**：纯读 + 计数，不改任何参数/状态/RNG。[实证]

### 1.4 L-W3 Verses 乘序审计锁（加固）

**问题**：`GetTotalDamage 0x48923D` 的 `fmul qword [edi+edx*8+0xA0]` 是**唯一** Verses 乘算点（T21 实证 9 处读点中此为伤害主路径）。若未来优化误改乘序，联机必炸。

**方案**：在 `0x48923D` 前插桩，记录 `{armor=edx, verses_val, damage_in, damage_out}` 到环形缓冲；每次帧末比对乘序哈希。**只读不写**，不改指令流。

**开关**：`[Telemetry] EnableVersesAudit=0`（默认关）。

**回滚**：移除插桩跳板。

**确定性**：纯观测。[实证]

---

## 2. 与 gap / 粒子 / 迷雾剔除交叉（ReceiveDamage 谓词）

### 2.1 核心契约

```
┌─────────────────────────────────────────────────────────────┐
│                    逻辑层（确定性红线）                        │
│  DamageArea → [候选枚举] → ReceiveDamage → GetTotalDamage     │
│       │              │            │              │           │
│       │              │            │              └─ Verses   │
│       │              │            │                 乘算点    │
│       │              │            └─ 5 处同步 PRNG (P23-P27)  │
│       │              └─ 7 处同步 PRNG (P16-P22)               │
│       └─ 候选序 = CellClass 链表序 + 空间桶序                   │
│                                                              │
│  ★ 不受迷雾/可见性/裂缝(GAP)任何谓词门控 ★                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ 派生视觉对象
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    表现层（可安全剔除）                        │
│  粒子系统 / 残骸 / 爆炸动画 / 冒烟                             │
│       │                                                      │
│       ├─ landing_pack_particle: ShouldDrawParticle（Draw 时） │
│       ├─ landing_pack_gap_p223: GAP 裂缝视觉保护              │
│       └─ EnableStarCraftFog: 迷雾三态剔除（Draw 时）           │
│                                                              │
│  ★ 只拦 Draw，绝不拦生成/Update/AI ★                          │
│  ★ 生成时的 PRNG 消费（P21/P27 等）必须照常执行 ★              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 ReceiveDamage 谓词与可见性谓词的隔离

| 谓词族 | 所属层 | 字段/地址 | 可否被迷雾/GAP 影响 |
|---|---|---|---|
| `AffectsAllies` | 逻辑 | `Warhead+0x178` | **否** |
| `EMEffect` / EMP | 逻辑 | `Warhead+0x156` / `Techno.IsUnderEMP` | **否** |
| `Temporal` / `MindControl` | 逻辑 | `Warhead+0x14E` / `+0x16C` | **否** |
| Health>0 / InLimbo | 逻辑 | `obj+0x6C` / `obj+0x74` | **否** |
| GAP 裂缝覆盖 | 表现 | `Cell+0x134` | 仅影响 Draw |
| 迷雾/黑雾 | 表现 | `IsCellShrouded 0x5865E0`（空桩） | 仅影响 Draw |
| 粒子归属可见性 | 表现 | `PSys+0xE0/+0xFC` | 仅影响 Draw |

**红线**：任何在 `ReceiveDamage` / `DamageArea` / `GetTotalDamage` 入口或内部加入「不可见则跳过」的谓词，都会**跳过同步 PRNG 消费** → 联机必炸。[实证]

### 2.3 交叉落地约束

| 交叉项 | 约束 | 依据 |
|---|---|---|
| 粒子迷雾剔除（landing_pack_particle） | `ShouldDrawParticle` **只挂 Draw 虚表槽 69**；粒子**生成**（P21/P27）不设门 | [实证] |
| GAP 裂缝保护（landing_pack_gap_p223） | 只清 `Cell+0x134` 覆盖计数；不触伤害链 | [实证] |
| 星际三态迷雾（EnableStarCraftFog） | 只拦 Unit/Inf/Air/Bld/Cell Draw | [实证] |
| 音频限频（R-AUDIO-LIMIT） | 只拦 `VocClass::Play*`；不触 PRNG | [实证] |

---

## 3. 确定性红线

### 3.1 乘序禁区（不改乘序）

**GetTotalDamage 乘算链**（`0x489180`..`0x48926A`）[实证]：

```
fild  damage                          ; 0x4891C6
fmul  [warhead+0x12C]                 ; 0x4891CE  PercentAtMax 缩放
...插值...
fild  clamped_damage                  ; 0x489239
fmul  [warhead+0xA0 + armor*8]        ; 0x48923D  ★ Verses[armor] ★ 禁止改序
call  ftol                            ; 0x489244
clamp to Rules.MaxDamage              ; 0x48924F..0x489260
```

**ReceiveDamage 火力归一化链**（`0x701939`..`0x701961`）[实证]：

```
fild  damage                          ; 0x701939
call  HouseType::GetFirepowerCoeff    ; 0x701952  (0x50BD30)
fmul  [techno+0x158]                  ; 0x701957  FirepowerMultiplier
fdivr original_damage                 ; 0x70195D  ★ 禁止改序（除法非交换）★
call  ftol                            ; 0x701961
```

**禁止操作**：
- 合并/交换上述任何 `fmul` / `fdivr` / `fild` / `fstp` 的顺序
- 把 Verses 乘算上提到 `DamageArea` 或 `ReceiveDamage` 内
- 缓存 `WarheadTypeClass` 的可变字段（运行期可被改写）
- 用整数乘替代浮点乘（精度路径不同）

### 3.2 RNG 禁区

**局内同步 PRNG**（`ScenarioClass::Random` @ `*(0xA8B230)+0x218`）——**零容忍**：

| 函数 | VA | 序 | 语义 |
|---|---|---|---|
| DamageArea | `0x489FF5` | P16 | 弹坑概率 |
| DamageArea | `0x48A179` | P17 | 焦痕概率 |
| DamageArea | `0x48A245` | P18 | 围墙掷骰 1 |
| DamageArea | `0x48A29F` | P19 | 桥梁掷骰 2 |
| DamageArea | `0x48A394` | P20 | 地面残骸 15% |
| DamageArea | `0x48A3E3` | P21 | 扬尘粒子 25% |
| DamageArea | `0x48A5D7` | P22 | 弹头动画选型 |
| ReceiveDamage | `0x7022C8` | P23 | 残骸件数 |
| ReceiveDamage | `0x70232B` | P24 | 残骸速度（循环） |
| ReceiveDamage | `0x702473` | P25 | 残骸模型 |
| ReceiveDamage | `0x70253A` | P26 | 残骸动画 |
| ReceiveDamage | `0x7029D7` | P27 | 冒烟粒子选型 |

**禁止操作**：
- 跳过任何一处上述调用（包括"看起来是视觉"的 P21/P22/P27）
- 改变 `ReceiveDamage` 对目标的调用顺序（= 改变 P23-P27 消费序）
- 合并多个 `DamageArea` 的候选枚举
- 并行化阶段 B

**局外 Global RNG**（`Randomizer::Global @ 0x886B88`）——**可安全限频**：

| VA | 语义 |
|---|---|
| `0x702174` | 受创语音选型 |
| `0x7021E4` | 惨叫语音选型 |
| `0x7026B8` | 红血求救 30% 判定 |
| `0x7026DE` | 求救语音选型 |

→ 限频方案见 R-AUDIO-LIMIT（`docs/re/audio_throttle_landing.md`）。

---

## 4. 纯收口 + 可测插桩点（不可落地项）

以下优化点经评估**不可落地**（触碰确定性红线），仅收口 + 标注插桩点供未来验证：

| # | 原优化设想 | 不可落地原因 | 可测插桩点 |
|---|---|---|---|
| X-W1 | 环表扫描空格早退 | 跳格可能改变 `ReceiveDamage` 调用序 → P23-P27 序分叉 | `0x489342` 后记录每格 `ObjectCount`；对比优化前后调用序哈希 |
| X-W2 | `Bullet::Update` 命中检测限频 | 改变爆炸帧 → 后续全部 PRNG 序错位 | `0x4666E0` 入口计数器（`bulletsUpdated/frame`） |
| X-W3 | 粒子生成限频（P21/P27） | P21/P27 消费**同步** PRNG，跳过=desync | `0x48A3E3` / `0x7029D7` 调用计数 |
| X-W4 | Verses 乘算缓存/合并 | 乘序红线（§3.1） | L-W3 审计锁 |
| X-W5 | 合并多弹 DamageArea | `ReceiveDamage` 内有 PRNG + 写共享状态 | `0x489280` 入口调用计数 + 栈深 |
| X-W6 | 并行化阶段 B | 写共享 House/Techno 状态 + PRNG 序 | 不适用 |

**收口结论**：伤害生产链的**逻辑层**在当前确定性契约下**无更多限频/加速空间**；可动面仅剩：
1. 堆分配池化（L-W1，不改语义）
2. 纯观测插桩（L-W2/L-W3）
3. 表现层限频（L-W4/L-W5，已有独立包）

---

## 5. 开关 · 遥测 · 回滚四要素

| # | 开关 | 默认 | 遥测计数器 | 卸载还原 | 回滚判据 | 联机 |
|---|---|---|---|---|---|---|
| L-W1 | `EnableDamageGroupPool` | **0** | `dgPoolHits` / `dgPoolFallbacks`（溢出退回堆） | memcpy 还原 4×5B | 池溢出率 >10% 或崩溃 → 置 0 | 可动（0 PRNG） |
| L-W2 | `EnableDamageTelemetry` | **0** | `rdCalls` / `rdTotalDamage` / `rdDeaths` / `rdHealCalls` | 还原 6B 序言 | 遥测开销 >1% 帧时 → 置 0 | 可动（纯读） |
| L-W3 | `EnableVersesAudit` | **0** | `versesAuditHash`（帧末哈希） | 移除插桩 | 哈希不一致告警 → 开审计排查 | 可动（纯读） |

> **联机约束**：L-W1 若启用，**全端必须同构建同开关**（池分配器替换后指针布局不同，虽不进 CRC，但异常行为需一致）。L-W2/L-W3 为纯观测，单端可开。

---

## 6. 验收清单

| # | 用例 | 期望 | 判据 |
|---|---|---|---|
| A1 | 默认配置（全键=0） | 字节仍为原版；无行为变化 | `scan_calls.py` 输出与 claims 一致 |
| A2 | `EnableDamageGroupPool=1` | 4 处 call 目标变为 PoolAlloc/PoolFree；`dgPoolHits>0` | 字节比对 + 日志 |
| A3 | 池溢出压测（>256 候选） | `dgPoolFallbacks>0`；不崩溃；PRNG 序不变 | 回放帧末 Randomizer 状态一致 |
| A4 | `EnableDamageTelemetry=1` | 计数器递增；游戏逻辑不变 | 回放 CRC 一致 |
| A5 | `EnableVersesAudit=1` | `versesAuditHash` 稳定；异常时告警 | 篡改乘序 → 哈希变 |
| A6 | gap/粒子/迷雾全开 | 伤害数值不变；粒子被剔除但 PRNG 序不变 | 回放 CRC 一致 |
| A7 | 硬回滚 | memcpy 还原后字节 = 原版 | `scan_calls.py` 一致 |

---

## 7. 与既有落地包的关系

| 既有包 | 关系 | 冲突面 |
|---|---|---|
| `landing_pack_particle.md` | 表现层剔除（Draw）；与 L-W5 同域 | **无**（逻辑/表现分离） |
| `landing_pack_gap_p223.md` | GAP 裂缝视觉保护 | **无**（不触伤害链） |
| `audio_throttle_landing.md` | L-W4 的实现载体 | **无**（Global RNG） |
| `telemetry_and_switches_spec.md` | L-W2/L-W3 的四要素模板 | 无 |
| T21 `R_warhead` | Verses 乘算点实证来源 | 无 |

---

## 8. claims 索引

字节锚点：`out/re_work/re_sprint/R_wpn_land/claims.txt`（42 条，本轮 `scan_calls.py` 复算）。

可复现扫描：`python out/re_work/re_sprint/R_wpn_land/scan_calls.py [gamemd_path]`

---

*本文地址均以 ImageBase `0x400000` 计；文件偏移 = VA − `0x400000`。*
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
