# ZCode 落地卡 · 伤害生产链 L-W1/L-W2/L-W3（DamageGroup 池化 / 入口遥测 / Verses 乘序审计锁）

> **卡号**：`ZC-WPN-LW`（批次 **B4c** · 三步 `ZC-WPN-L1` 池化 → `ZC-WPN-L2` 遥测 → `ZC-WPN-L3` 乘序审计锁）· **优先级**：P1  
> **执行方**：ZCode（真机/补丁安装唯一写者）· **起草**：MiMo（R-WPN-CARD，依据 R-WPN-LAND 静态定谳）  
> **上游**：`docs/re/weapons_damage_landing.md`（L-W1/L-W2/L-W3）· 深潜 `docs/re/weapons_damage_production.md` · Verses `docs/re/warhead_verses_residual_p2.md` · 复算 `out/re_work/re_sprint/R_wpn_land/` · 本卡工作区 `out/re_work/re_sprint/R_wpn_card/`  
> **格式对齐**：`docs/re/landing_pack_crt_l1.md`（ZC-CRT-L1）  
> **本卡范围**：**仅** DamageGroup 四处 call 等长池化 + `ReceiveDamage` 入口遥测 + `0x48923D` 乘序审计锁。键 **只有** `EnableDamageGroupPool` / `EnableDamageTelemetry` / `EnableVersesAudit`。  
> **禁碰**：`0x48A323` / `0x48A3B1` / `0x48A3F2` / `0x48A449` 四处 op_new 地形特效分配**一律不动**；`CRT::_new@0x7C8E17` / `_delete@0x7C8B3D` **不装钩、不改字节**；`GetTotalDamage 0x48923D` 的 `fmul` **语义/乘序零改动**。  
> **证据基线**：`gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` · ImageBase `0x00400000` · `file_off = VA − 0x00400000`
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]

---

## 0. 一句话

把 `DamageArea` 阶段 A/B 的 DamageGroup 逐候选堆分配（2 处 `call CRT::_new` + 2 处 `call CRT::_delete`，共 **4 处 5B `E8 rel32` 等长**）替换成静态池（容量 256，溢出退回原堆），**只动这 4 处、禁混入另 4 处 op_new**；`ReceiveDamage 0x701900` 入口装纯读遥测；`GetTotalDamage 0x48923D` 装乘序审计锁（**不改 `fmul` 本体**）。三开关默认全 0 = 字节零变化；同步 PRNG P16–P27 **零容忍**。

---

## 1. 执行表（字节级 + 插入方式）

### 1.1 三步一览

| 项 | **L-W1 池化** | **L-W2 入口遥测** | **L-W3 乘序审计锁** |
|---|---|---|---|
| **步骤 ID** | `POOL-DG1` / `POOL-DG2` / `FREE-DG1` / `FREE-DG2` | `RD-TELEM` | `VER-AUDIT` |
| **目标** | DamageGroup alloc×2 + free×2 | `ReceiveDamage` 入口 | `GetTotalDamage` Verses 乘算点 |
| **VA** | `0x004894AB` / `0x0048975D` / `0x00489AE4` / `0x00489B33` | `0x00701900` | `0x0048923D` |
| **文件偏移** | `0x000894AB` / `0x0008975D` / `0x00089AE4` / `0x00089B33` | `0x00301900` | `0x0008923D` |
| **覆盖长度** | **5×4=20B**（每处 5B 等长） | **6** | **7** |
| **原字节** | `E8 67 F9 33 00` / `E8 B5 F6 33 00`<br>`E8 54 F0 33 00` / `E8 05 F0 33 00` | `81 EC B4 00 00 00` | `DC 8C D7 A0 00 00 00` |
| **原指令** | `call 0x7C8E17` ×2 / `call 0x7C8B3D` ×2 | `sub esp,0xb4` | `fmul qword [edi+edx*8+0xA0]` |
| **插入方式** | **等长 `E8 rel32` → `call PoolAlloc/PoolFree`**（无跳板） | `E9 rel32` + `90` 跳板，回跳 `0x701906` | `E9 rel32` + `90 90` 跳板，跳板内**原样重放 7B fmul**，回跳 `0x489244` |
| **开关** | `EnableDamageGroupPool=1` | `EnableDamageTelemetry=1` | `EnableVersesAudit=1` |
| **确定性** | **安全**（保序、0 PRNG） | **安全**（纯读+计数） | **安全**（纯读断言；乘序不变） |

### 1.2 L-W1 DamageGroup 池化（修复）——仅 4 处 call 等长

**问题**：`DamageArea 0x489280` 阶段 A 对每个候选 `push 8; call 0x7C8E17`（8B DamageGroup 堆分配），阶段 B 逐个 `call 0x7C8B3D` 释放。高密度弹幕 O(弹数 × r² × 密度) 次堆操作是明确热点。

**方案**：4 处 `E8 rel32` **等长替换**为 `call PoolAlloc`（alloc）/ `call PoolFree`（free）。池 = 静态/TLS 固定池，**容量 256**，溢出**退回原堆分配**（原 `CRT::_new` 路径）。**保持 push 顺序与遍历序不变**。不需要 trampoline。

**唯一允许动的 4 处**（本卡 L-W1 等长替换白名单）[实证]：

| 点 | VA | FileOff | 原字节（5B） | 原语义 | 替换为 |
|---|---|---|---|---|---|
| alloc-1 | `0x004894AB` | `0x000894AB` | `E8 67 F9 33 00` | `call 0x7C8E17`（格子链表候选） | `call PoolAlloc` |
| alloc-2 | `0x0048975D` | `0x0008975D` | `E8 B5 F6 33 00` | `call 0x7C8E17`（空间桶候选） | `call PoolAlloc` |
| free-1 | `0x00489AE4` | `0x00089AE4` | `E8 54 F0 33 00` | `call 0x7C8B3D`（结算中释放） | `call PoolFree` |
| free-2 | `0x00489B33` | `0x00089B33` | `E8 05 F0 33 00` | `call 0x7C8B3D`（结算尾释放） | `call PoolFree` |

**严禁混入的另 4 处 op_new**（地形特效分配，非 DamageGroup 语义）[实证]：

| 点 | VA | 原字节 | 语义 | 处置 |
|---|---|---|---|---|
| terrain-A | `0x0048A323` | `E8 EF EA 33 00` | 地面残骸 15% 路径 `call 0x7C8E17` | **禁改** |
| terrain-B | `0x0048A3B1` | `E8 61 EA 33 00` | 扬尘粒子 25% 路径 `call 0x7C8E17` | **禁改** |
| terrain-C | `0x0048A3F2` | `E8 20 EA 33 00` | 弹头动画选型路径 `call 0x7C8E17` | **禁改** |
| terrain-D | `0x0048A449` | `E8 C9 E9 33 00` | 后续清理路径 `call 0x7C8E17` | **禁改** |

> **红线**：上述 4 处紧随 P20/P21/P22 同步 PRNG 判定，属**地形特效**（残骸/扬尘/弹坑动画）分配，**不属 DamageGroup**。L-W1 安装后这 4 处字节必须与原版逐位相同；`PoolAlloc/PoolFree` **绝不可**被它们调用。对应的 cleanup free（`0x48A4A4` / `0x48A4D0`）同样**禁改**。`CRT::_new@0x7C8E17` / `_delete@0x7C8B3D` 本体**禁装钩**（L2 红线，同 ZC-CRT-L1 G0.7）。

**池语义**（必须严格）：

1. `PoolAlloc`：栈上语义等价原 `call 0x7C8E17`（`push 8` 仍由调用点保留）；从固定池取 8B 槽返回；池满 → `dgPoolFallbacks++` 并走原 `CRT::_new`。
2. `PoolFree`：若指针属池 → 归还槽位（`dgPoolHits` 口径内）；否则走原 `CRT::_delete`。
3. **禁止**改变 push 顺序、遍历序、`ReceiveDamage` 调用序——这是 PRNG 序不变的唯一保证。

**确定性论证** [实证 + 推演]：DamageGroup 是临时容器 `{obj*, dist}`，指针值不进任何 PRNG、不写存档、不进帧 CRC（`0x64DAB0` 混合量化坐标+RNG，非堆地址）。池化只改「指针从哪来」，不改「按什么顺序用」→ `ReceiveDamage` 调用序不变 → P23–P27 消费序不变。

### 1.3 L-W2 `ReceiveDamage` 入口遥测（加固/插桩）

**问题**：伤害结算黑盒，无可观测性。

**方案**：`0x701900` 入口 6B `81 EC B4 00 00 00`（`sub esp,0xb4`）等长替换为 `E9 rel32`（5B）+ `NOP`（1B）。跳板内**只读**记录 `{this=ECX, *pDamage, pWarhead, pAttacker}` 后 `jmp 0x701906`（原 `push ebx` 起继续）。

| 点 | VA | FileOff | 原字节 | 回跳点 |
|---|---|---|---|---|
| RD-TELEM | `0x00701900` | `0x00301900` | `81 EC B4 00 00 00` | `0x00701906` |

**计数器**：`rdCalls`（入口次数）、`rdTotalDamage`（累计伤害）、`rdDeaths`（Health 归零次数）、`rdHealCalls`（pDamage<0 次数）。

**确定性**：纯读 + 计数，不改任何参数/状态/RNG。[实证]

### 1.4 L-W3 Verses 乘序审计锁（加固）——不改 `0x48923D` fmul

**问题**：`GetTotalDamage 0x48923D` 的 `fmul qword [edi+edx*8+0xA0]` 是**唯一** Verses 乘算点（T21 实证 9 处读点中此为伤害主路径）。若未来优化误改乘序，联机必炸。

**方案**：`0x48923D` 起 7B 装跳板（`E9 rel32 90 90`）；跳板内先记录 `{armor=edx, verses_val, damage_in, damage_out}` 到环形缓冲，再**逐字节重放**原 `DC 8C D7 A0 00 00 00`（`fmul qword [edi+edx*8+0xA0]`），`jmp 0x489244`（原 `call ftol`）。帧末比对乘序哈希 `versesAuditHash`。

| 点 | VA | FileOff | 原字节（7B） | 回跳点 |
|---|---|---|---|---|
| VER-AUDIT | `0x0048923D` | `0x0008923D` | `DC 8C D7 A0 00 00 00` | `0x00489244` |

**红线（本卡最高优先级）**：

- **不改** `fmul` 的操作数寻址 `[edi+edx*8+0xA0]`、不改它在 `fild→fmul→ftol` 链中的**位置与顺序**；
- **禁止**合并/交换 `GetTotalDamage 0x489180..0x48926A` 与 `ReceiveDamage 0x701939..0x701961`（`fdivr` 链）内任何 `fmul` / `fdivr` / `fild` / `fstp` 顺序；
- **禁止**把 Verses 乘算上提到 `DamageArea` / `ReceiveDamage`；
- **禁止**缓存 `WarheadTypeClass` 可变字段；**禁止**整数乘替浮点乘；
- 审计锁**只读**（读 `edx`/`[edi+edx*8+0xA0]`/栈上 damage），不写任何游戏状态。

**确定性**：纯观测。[实证]

---

## 2. 安装前置（全部 PASS 才允许写）

| # | 检查 | 期望 | 失败则 |
|---|---|---|---|
| G0.1 | 目标文件 SHA-256 | `73201CC0…F67476` | **拒绝安装** |
| G0.2 | `0x4894AB` / `0x48975D` / `0x489AE4` / `0x489B33` 首 5B | 见 §1.2 白名单表 | 已是 `E9`/非原 call：报告「已打/异常」停手；**禁止覆盖** |
| G0.3 | `0x48A323` / `0x48A3B1` / `0x48A3F2` / `0x48A449` 首 5B | `E8 …` 原版 4 处 op_new | 若被改写 → **拒绝**（禁混入红线） |
| G0.4 | `0x701900` 首 6B | `81 EC B4 00 00 00` | 已是 `E9`：停手；其它：拒绝 |
| G0.5 | `0x48923D` 首 7B | `DC 8C D7 A0 00 00 00` | 已是 `E9`：停手；其它：拒绝 |
| G0.6 | 回跳点 `0x701906` / `0x489244` | `53` / `E8 B7 CC 33 00` | 拒绝 |
| G0.7 | `CRT::_new@0x7C8E17` / `_delete@0x7C8B3D` 序言 | `6A 01 FF 74 24 08…` / `FF 74 24 04 E8 A2 08 00 00 59 C3` **原样** | 有任何改写 → **拒绝**（L2 红线） |
| G0.8 | 三开关默认 | `EnableDamageGroupPool=0` / `EnableDamageTelemetry=0` / `EnableVersesAudit=0` | 全 0 = 零行为变化 |
| G0.9 | 装前 dump | `preflight_before.bin` 落盘本工作区 | 缺失拒绝 |

**Q1 真机首字节（安装前）**：读 4 处池化点 + `0x701900` + `0x48923D` + 4 处 op_new 首字节 → 全原版=未打；任一 `E9` = 已有外部补丁（**停手上报，禁止覆盖**）。

---

## 3. 开关 · 遥测

### 3.1 键名（宿主 `ra2render.ini`）

```ini
[Logic]
; L-W1 DamageGroup 池化（4 处等长 call）；0=不装（默认）
EnableDamageGroupPool=0

[Telemetry]
; L-W2 ReceiveDamage 入口遥测；0=不装（默认）
EnableDamageTelemetry=0

; L-W3 Verses 乘序审计锁；0=不装（默认）
EnableVersesAudit=0
```

| 键 | 节 | 默认 | 语义 | 锁定 |
|---|---|---|---|---|
| `EnableDamageGroupPool` | `[Logic]` | **0** | 1 → 装 POOL-DG1/2 + FREE-DG1/2 | **启动期单次读取，严禁局内热切** |
| `EnableDamageTelemetry` | `[Telemetry]` | **0** | 1 → 装 RD-TELEM | 同上 |
| `EnableVersesAudit` | `[Telemetry]` | **0** | 1 → 装 VER-AUDIT | 同上 |

> **键名口径**：与 `weapons_damage_landing.md` §5 一致；与 `zcode_master_implementation_ticket_v2.md` B4c 一致。本卡**不新增**其它键。

### 3.2 遥测（只读计数，禁热路径膨胀）

| 计数器 | 归属 | 含义 |
|---|---|---|
| `dgPoolHits` | L-W1 | 池成功供给次数 |
| `dgPoolFallbacks` | L-W1 | 池满退回原堆次数 |
| `rdCalls` / `rdTotalDamage` / `rdDeaths` / `rdHealCalls` | L-W2 | 入口次数 / 累计伤害 / 死亡数 / 治疗数 |
| `versesAuditHash` | L-W3 | 帧末乘序哈希（`armor,verses,din,dout` 串） |

启动日志一行：`WpnLW=off | pool | telem | audit | <组合>`。

---

## 4. 同步 PRNG 零容忍红线（lockstep 安全验收）

### 4.1 为什么 L-W1/L-W2/L-W3 安全 [实证 + 推演]

| # | 事实 | 级别 |
|---|---|---|
| 1 | L-W1 仅换分配来源；push/遍历/`ReceiveDamage` 调用序不变 → P23–P27 消费序不变 | [实证字节 + 推演] |
| 2 | L-W2/L-W3 纯读 + 计数，不改参数/状态/RNG | [实证] |
| 3 | 存档无裸指针落盘；帧 CRC `0x64DAB0` 混合量化坐标+RNG，**非堆地址** | [实证] `net_sync_checksum.md` |
| 4 | `0x7C8E17`/`0x7C8B3D` 本体不动 → 无跨堆/ABI 劫持 | [实证] |
| 5 | 禁止引入 `(uintptr_t)this>>4` 一类指针哈希进 CRC/审计入参以外路径 | 红线 |

### 4.2 同步 PRNG 禁区 P16–P27（零容忍）[实证]

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

- 跳过任何一处上述调用（**包括「看起来是视觉」的 P21/P22/P27**）；
- 改变 `ReceiveDamage` 对目标的调用顺序（= 改变 P23–P27 消费序）；
- 合并多个 `DamageArea` 候选枚举；并行化阶段 B；
- 在 `ReceiveDamage` / `DamageArea` / `GetTotalDamage` 加「不可见则跳过」谓词（迷雾/GAP/粒子只许拦 Draw，见 `weapons_damage_landing.md` §2）；
- 新增任何 `ScenarioClass::Random/RandomRanged` 调用。

**局外 Global RNG**（`Randomizer::Global @ 0x886B88`，`0x702174`/`0x7021E4`/`0x7026B8`/`0x7026DE` 语音类）本卡**不碰**——限频归 R-AUDIO-LIMIT。

### 4.3 D-gate（A5 前置）

| ID | 检查 | 通过条件 |
|---|---|---|
| **D1** | 静态：三钩内 0 次 `Scenario::Random` / 不写 `0x64DE3F` 窗 | 装前后该窗字节一致 |
| **D2** | 静态：`0x7C8E17`/`0x7C8B3D` 序言 + 4 处 op_new 字节未变 | dump 对照 G0.3/G0.7 |
| **D3** | 动态：U200/U800 回放帧 CRC，三开关组合 vs 全 0 vs 未打补丁 | **三者一致** |
| **D4** | 动态：高密度弹幕（>256 候选）无 UAF、`dgPoolFallbacks>0`、PRNG 序不变 | 回放帧末 Randomizer 状态一致 |

---

## 5. 验收 A1–A7（真机；ZCode 填回执）

| ID | 步骤 | 期望 | 证据要求 |
|---|---|---|---|
| **A1** | 默认配置启动（三键全 0） | 全部字节仍为原版；无行为变化 | `scan_calls.py` / 字节 dump 与 claims 一致 |
| **A2** | `EnableDamageGroupPool=1` | 4 处 call 目标变 PoolAlloc/PoolFree；`dgPoolHits>0`；**4 处 op_new 未变** | 字节前后对照 + 日志 |
| **A3** | 池溢出压测（>256 候选） | `dgPoolFallbacks>0`；不崩溃；PRNG 序不变 | 回放帧末 Randomizer 状态一致 |
| **A4** | `EnableDamageTelemetry=1` | 计数器递增；游戏逻辑不变 | 回放 CRC 一致 |
| **A5** | `EnableVersesAudit=1` | `versesAuditHash` 稳定；人为篡改乘序 → 哈希变/告警 | 哈希对照 |
| **A6** | gap/粒子/迷雾全开（表现层包同时启用） | 伤害数值不变；粒子被剔除但 PRNG 序不变 | 回放 CRC 一致 |
| **A7** | 硬回滚 | memcpy 还原后字节 = 原版 | `scan_calls.py` / dump 一致 |

### 「没崩≠成功」——A3 强制证据

1. **池化生效**：`dgPoolHits>0` 且同场景对照 `EnableDamageGroupPool=0` 时 `CRT::_new(8)` 计数显著下降；
2. **无逻辑漂移**：同种子回放伤害序列/P23–P27 消费序与基线一致（或 D3 CRC 一致）；
3. **溢出安全**：`dgPoolFallbacks>0` 时不崩溃、不混用池/堆指针（`PoolFree` 双路径正确）。

---

## 6. 回滚 / MP

### 6.1 回滚三级

| 级别 | 操作 | 影响 |
|---|---|---|
| **L0 软关** | 三键全 `0` + **重启进程** | 下次启动不装钩；字节逐位=原版 |
| **L1 硬回滚** | memcpy 还原：4×5B（L-W1）+ 6B（L-W2）+ 7B（L-W3）= **33B**（`R_wpn_card/orig_bytes.bin`），释放 trampoline | 与原版等价 |
| **L2 禁区** | **禁止**回滚/修改 `0x7C8E17`/`0x7C8B3D`/4 处 op_new/`0x48923D` fmul 语义/任何 P16–P27 调用点 | 跨堆释放 → `0xC0000374`；改乘序/跳 PRNG → 联机必炸 |

- 原字节备份**装钩前落盘**：`out/re_work/re_sprint/R_wpn_card/orig_bytes.bin`。
- 补丁器提供 `--uninstall-wpn-lw` 仅还原上述 33B（按 POOL→TELEM→AUDIT 逆序）。

### 6.2 MP / 联机（R-MP-GATE 口径）

| 项 | 结论 | 依据 |
|---|---|---|
| **L-W1 联机** | **可动，但全端必须同构建同开关**（池分配指针布局不同，虽不进 CRC，异常行为需一致） | `weapons_damage_landing.md` §5 |
| **L-W2/L-W3 联机** | **可动**（纯读观测）；单端可开 | 同上 |
| **混端 DESYNC** | L-W2/L-W3 **SAFE**；L-W1 仅在「全端同开关」下 SAFE，混开=**拒绝混联** | [推演，需 A3/A6 背书] |
| **是否强制 MpActive 关** | **不强制**；L-W1 建议 `MpActive` 时校验对端开关一致性，不一致打印 `forced-off-mp` 并拒装 | 可选观感门 |
| **握手字段** | **不新增** | R-MP-GATE 既定 |
| **默认** | 三键全 `0` —— 发行/正式联机零副作用 | 与 gap_p21 / ZC-CRT-L1 对拍基线一致 |

---

## 7. 风险（执行方必读）

| ID | 风险 | 等级 | 要求 |
|---|---|---|---|
| R-1 | 混入 4 处 op_new 地形分配 → 池被特效对象污染/误释放 | **高** | §1.2 禁碰表；G0.3；A2 专测字节 |
| R-2 | 池 Free 混用堆/池指针 → 跨堆释放 `0xC0000374` | **高** | `PoolFree` 判归属；A3 溢出专测 |
| R-3 | 改 `0x48923D` fmul 乘序/上提/缓存 → 伤害分叉联机必炸 | **高** | §1.4 红线；A5 篡改对照 |
| R-4 | 跳过/合并 P16–P27（含「视觉」P21/P22/P27）→ RNG 流分叉 | **高** | §4.2 零容忍；D3 CRC |
| R-5 | 在 ReceiveDamage/DamageArea 加可见性谓词 → 跳 PRNG | **高** | §4.2；只许拦 Draw |
| R-6 | 局内热切开关 → 状态半好半坏 | 高 | 启动期锁定；改 INI 必须重启 |
| R-7 | 误碰 `0x7C8E17`/`0x7C8B3D`（L2） | **高** | G0.7；首字节停手 |
| R-8 | L-W1 混端开关不一致 | 中 | §6.2 全端同开关 |
| R-9 | 把「没崩」当成功 | 高 | A3 强制遥测证据（§5） |

---

## 8. 交付回执（填完交回）

```
ZC-WPN-LW RESULT
- build/md5(gamemd):
- install path: (ra2render trampoline | external patcher | ...)
- EnableDamageGroupPool / EnableDamageTelemetry / EnableVersesAudit:
- G0.1–G0.9: PASS/FAIL
- Q1 first bytes before @0x4894AB/0x48975D/0x489AE4/0x489B33/0x701900/0x48923D:
- bytes after (POOL-DG1/2, FREE-DG1/2, RD-TELEM, VER-AUDIT):
- 4x op_new (0x48A323/0x48A3B1/0x48A3F2/0x48A449) unchanged: y/n
- 0x7C8E17 / 0x7C8B3D unchanged: y/n
- 0x48923D fmul semantic unchanged (replayed byte-identical): y/n
- D1–D4: PASS/FAIL
- A1..A7: (each PASS/FAIL + evidence path)
- dgPoolHits / dgPoolFallbacks / rdCalls / rdTotalDamage / rdDeaths / rdHealCalls / versesAuditHash:
- except.txt: empty|path
- rollback tested (L0/L1): y/n
- MP: (single | mp-preserved | mp-forced-off) + CRC note
```

---

## 9. 不在本卡

- **4 处 op_new 地形特效分配**（`0x48A323/0x48A3B1/0x48A3F2/0x48A449`）及其 cleanup free（`0x48A4A4/0x48A4D0`）—— **禁碰**  
- **CRT L2 全部**：`CRT::_new`/`_delete` 钩、MemPool*、块头、投毒 —— 另卡（B4a/B4b）  
- L-W4 伤害语音/震屏限频 —— R-AUDIO-LIMIT（`docs/re/audio_throttle_landing.md`）  
- L-W5 粒子/迷雾剔除 —— `landing_pack_particle` / gap_p223（只拦 Draw）  
- X-W1..X-W6 不可落地优化（环表早退/命中限频/粒子限频/Verses 缓存/合并 DamageArea/并行阶段 B）—— 纯收口，不实现  
- 台账/看板登记 —— 由 Lead 收口  

---

*依据：`weapons_damage_landing.md` §1.2–1.4/§3/§5–6；`zcode_master_implementation_ticket_v2.md` B4c / G-R3 / G-R4；本卡字节 19/19 复算 MATCH（`R_wpn_card/claims.txt`）；L-W1 仅 4 处 5B 等长 call、禁混入 4 处 op_new；L-W3 不改 `0x48923D` fmul；三开关默认 0 + 启动期锁定。*
