# ZCode 落地卡 · CRT L2 class3/4 扩桶（idx8/idx9 + 侧表 freelist + 毒填）

> **卡号**：`ZC-CRT-L2-C34` · **批次**：B4b（**独立于 ZC-CRT-L1，不在同批默认开**）· **优先级**：P1（崩溃面防护；改变 class-4 生命周期）  
> **执行方**：ZCode（真机/补丁安装唯一写者）· **起草**：MiMo（R-L2-CARD，依据 R-L2-GAP 静态定谳）  
> **上游**：`docs/re/crt_l2_class34_fix_spec.md`（R-L2-GAP）· T20 `docs/re/sbh_uaf_residual_deep_dive.md` · T14 `docs/re/crt_pool_landing.md` · 模板 `docs/re/landing_pack_crt_l1.md`（ZC-CRT-L1）  
> **复算**：`out/re_work/re_sprint/R_l2_gap/` · 本卡工作区 `out/re_work/re_sprint/R_l2_card/`  
> **格式对齐**：`docs/re/landing_pack_crt_l1.md`  
> **本卡范围**：**仅 L2 新桶 idx8（class3，req 41..56）/ idx9（class4，req 57..72）**。键 **只有** `MemPoolClass34`（+ 复用 `EnableMemoryPool` / `MemPoolDebug` / `OnlineSafeMode`）。  
> **禁碰**：L1（`VectorReuse`/`VectorReserve`）语义、idx0..7 桶实现、`MemPoolSmall`/`MemPoolEntities` 键、H2/H6 可见性钩、`0x6F8DF0` 现网 9B 钩、`ra2render/**`、`gamemd.exe` 字节以外写入。  
> **证据基线**：`gamemd.exe` 1.001 · MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` · ImageBase `0x00400000` · `file_off = VA − 0x00400000`
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]

---

## 0. 一句话

在 L2 `SizeToPoolIdx` 追加 **idx8（41..56B / class3）/ idx9（57..72B / class4）** 两桶，采用 **B-pref 块下标侧表 freelist + 用户区整段 `0xDEADBEEF` 毒填**（避开侵入式 freelist 与 UAF 写 user+0 的同构二次污染）；块头强制 **8B** `PoolBlockHeader{magic,poolIdx}`（存活 `0xA5A55A5A` / 释放 `0xDEADBEEF`）。二阶键 **`MemPoolClass34` 默认 0**；`OnlineSafeMode=1` / `MpActive()` **强制 L1-only**。**不在 ZC-CRT-L1 同批默认开**，须独立 A/B（含 **G-ALLOCORDER**）通过后才允许单机试开。

---

## 1. 执行表（尺寸桶 / 头 / freelist / 毒）

### 1.1 桶定义（算术 `[实证]`，设计 `[推演]`）

| 新 idx | req 窗 | elemSize | m_elemSize | 池块总长 | 用户区 | 对应 SBH | 初始 capacity | 开关 |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| **8** | 41..56 | 56 | 56 | 8+56=**64** | 56B | class 3 | **256** | `MemPoolClass34` |
| **9** | 57..72 | 72 | 72 | 8+72=**80** | 72B | class 4（**崩溃 class**） | **512** | `MemPoolClass34` |

```cpp
// SizeToPoolIdx 追加（其余分支不动）：
if (sz >= 41 && sz <= 56) return 8;   // class 3
if (sz >= 57 && sz <= 72) return 9;   // class 4
static FixedPool s_pools[10];         // 原 [8] → [10]
```

- **精确区间命中**，不做模糊范围；`new(194408)` 音频 bulk 必须 miss → 穿透（红线）。  
- 池耗尽 / miss：**透传** `_nh_malloc@0x007C9442`，失败语义与原版一致（G-FAILSEM）。

### 1.2 块头（强制，8B，继承 F-06/P-M1）`[实证]`

```cpp
#pragma pack(push, 8)
struct PoolBlockHeader {
    uint32_t magic;    // 存活 0xA5A55A5A / 释放 0xDEADBEEF
    uint32_t poolIdx;  // 0..9（独立字段，禁止与 magic 位域复用）
};
#pragma pack(pop)      // sizeof == 8；返回 pBlock+8，8 字节对齐
```

| 项 | 值 | 说明 |
|---|---|---|
| **magic 存活** | `0xA5A55A5A` | Alloc 出块后写入 |
| **magic 释放** | `0xDEADBEEF` | Free 回收时写入（双释放免疫锚点） |
| `m_elemSize` | `(elemSize+7)&~7` | 56/72 均已 8 对齐 |
| **禁止 4B 头** | — | TC-ST-04 一票否决：破坏 `double`/SSE 8B 对齐 |

### 1.3 freelist：B-pref 侧表（**唯一允许**；禁 B-min 侵入式）

| 方案 | freelist | free 行为 | UAF 写 user+0 | 裁决 |
|---|---|---|---|---|
| B-min | 侵入式（user+0=next） | magic→`0xDEADBEEF` | **污染 freelist**（与崩溃同构） | **否决** |
| **B-pref** | **块下标侧表** `uint32_t m_freeIdx[]` | magic→`0xDEADBEEF` **+ 用户区整段毒填** | 只打到毒填料，不破坏 freelist | **本卡唯一** |

**B-pref 细则（执行方照抄）**：

1. freelist = 栈式下标链（`m_freeIdx[blk] = prevFree`；`m_freeHead` CAS 更新）。  
2. `Free`：范围守卫（`pBlock ∈ [m_buffer, m_bufferEnd)`）→ `magic==0xA5A55A5A` 才回收，否则计数拒绝/透传 → `magic=0xDEADBEEF` → **`memset(user, 0xDEADBEEF, m_elemSize)`** → 下标入链。  
3. `Alloc`（`MemPoolDebug=1` 时）：出块前校验用户区仍为 `0xDEADBEEF` 整段；被改写 → `uafWriteWhileFree++` + dump（**不中断**；可选 `MemPoolDebugStrict=1` 断言）。  
4. 双释放：`magic==0xDEADBEEF` → `doubleFreeRejects++`，**不入链**（失败语义与原版 A/B 对齐）。

### 1.4 CAS 与线程 `[推演]`

- `m_freeHead` 更新一律 `InterlockedCompareExchangePointer`（或 32-bit index 的 `InterlockedCompareExchange`）。  
- 音频/网络线程可能 `new/delete`；L2 全路径 CAS 必做。若 A/B 发现撕裂 → 退化「L2 仅主线程启用」（`GetCurrentThreadId==g_mainThread` 才命中桶）。

### 1.5 钩点（与 ZC-CRT-L1 红线一致，本卡不改序言语义）`[实证]`

| 目标 | VA | 原序言 | 覆盖 | 跳板 |
|---|---|---|---:|---|
| `CRT::_new` | `0x007C8E17` | `6A 01 FF 74 24 08…` | 5B | `E9 rel32` + 原 5B + `jmp 0x007C8E1C` |
| `CRT::_delete` | `0x007C8B3D` | `FF 74 24 04 E8 A2 08 00 00 59 C3` | 5B | `E9 rel32` + 原 5B + `jmp 0x007C8B42` |

- 命中桶：完全绕开 SBH / `_lock(9)`；未命中/透传走原 `_nh_malloc`。  
- **`MemPoolClass34=0` 时 idx8/9 不注册、不分配、不改命中路径**（与全关等价于字节零差异可分层验证）。

### 1.6 遥测（`MemPoolDebug` 可局内改，只影响观测）

| 计数器 | 含义 |
|---|---|
| `poolAllocs` / `poolFrees` | idx8/9 池内分配/释放 |
| `poolFallbacks` | 耗尽/miss 透传次数 |
| `doubleFreeRejects` | 双释放拒绝 |
| `uafWriteWhileFree` | 毒填被改写（UAF 迹象） |
| `crtL2C34Installed` | 位掩码：bit0=idx8, bit1=idx9 |

启动日志一行：`MemPoolClass34=off | idx8+idx9 | forced-off-mp`。

---

## 2. 开关 · 二阶键 · OnlineSafeMode

### 2.1 节名 `[MemoryPool]`（宿主 `ra2render.ini`）

```ini
[MemoryPool]
> 【W3 勘误 · W3-M6/ISSUE-SECTION-MEMORYPOOL】[W3-Lead临时裁决] 改前：[MemoryPool]；改后：[System]（DC-01 裁决口径: 使用既有 [System] 节，零新增节，EnableMemoryPool=0）；依据：Lead 临时裁决 DC-01 与 blitter_hooks.cpp:541,544；分级：P0
; 总闸：启动期读取一次并锁定；0=不装任何 L2 钩（默认）
EnableMemoryPool=0

; L1（ZC-CRT-L1 卡负责；本卡不改）
VectorReuse=0
VectorReserve=0

; L2 小桶 / 实体桶（另卡；本卡不改键值）
MemPoolSmall=0
MemPoolEntities=0

; ★ 本卡：idx8/idx9（class3/4）—— 默认 0，不在 ZC-CRT-L1 同批默认开
MemPoolClass34=0

; 观测（可局内改，不改分配行为）
MemPoolDebug=0
```

### 2.2 键矩阵

| 键 | 节 | 默认 | 语义 | 锁定 |
|---|---|---:|---|---|
| `EnableMemoryPool` | `[MemoryPool]` | **0** | 总闸；0 → L2 两入口不装钩 | **启动期单次锁定，严禁局内热切** |
| **`MemPoolClass34`** | `[MemoryPool]` | **0** | **idx8/9 = 本卡**；独立二阶键 | 同上 |
| `MemPoolSmall` | `[MemoryPool]` | 0 | idx0..4（**不隐含 class3/4**） | 同上 |
| `MemPoolEntities` | `[MemoryPool]` | 0 | idx5..7 | 同上 |
| `MemPoolDebug` | `[MemoryPool]` | 0 | 遥测 + 毒填校验 | 可局内改（只观测） |
| `OnlineSafeMode` | `[Logic]` | 0 | =1 或 `MpActive()` → **强制 L1-only** | 启动/进局判定 |

### 2.3 门控伪码（执行方必须实现）

```text
if (!EnableMemoryPool) → 不装 L2 钩
effectiveSmall    = MemPoolSmall    && !OnlineSafeMode && !MpActive
effectiveEntities = MemPoolEntities && !OnlineSafeMode && !MpActive
effectiveClass34  = MemPoolClass34  && !OnlineSafeMode && !MpActive   // 默认关
```

| 场景 | 允许 |
|---|---|
| 单机 / 战役 | L1 +（L2 小桶/实体/**Class34** 按键；Class34 须 A/B） |
| 联机 / 混联 | **仅 L1** |
| `OnlineSafeMode=1` | **强制** `MemPoolSmall=MemPoolEntities=MemPoolClass34=0`，告警日志 |
| `MpActive()`（`0x00A8D5F8` 会话位） | 同上强制 |

> 与 `mp_autodowngrade_spec.md` 的 `MpAutoDowngrade` 语义兼容；文档口径统一为 **`OnlineSafeMode`**（见 R-L2-GAP §4.2）。

---

## 3. 安装前置（全部 PASS 才允许写）

| # | 检查 | 期望 | 失败则 |
|---|---|---|---|
| G0.1 | 目标 MD5 | `4f37486e5b0dbe2ae5f45aeee0f98367` | **拒绝安装** |
| G0.2 | `0x7C8E17` 首 5B | `6A 01 FF 74 24` | 已是 `E9` 且非本体系：停手上报；其它：**拒绝** |
| G0.3 | `0x7C8B3D` 首 5B | `FF 74 24 04 E8` | 同上 |
| G0.4 | `_delete` 全 11B | `FF 74 24 04 E8 A2 08 00 00 59 C3` | 拒绝 |
| G0.5 | 总闸 `EnableMemoryPool` | 显式 `1` 才装 L2；默认 0 | 零行为变化 |
| G0.6 | **`MemPoolClass34` 默认 0** | 缺省/0 → idx8/9 **不生效**（字节可已装钩，但桶空） | 若运行态生效而键为 0 → **拒绝合入** |
| G0.7 | `OnlineSafeMode` / `MpActive` | 任一为真 → Class34 **强制关** | 有 OOS → 强制 L1-only |
| G0.8 | 与 ZC-CRT-L1 共存 | L1 钩（0x4E97B0 族 / 0x6F8F8A）不被本卡覆盖 | 冲突 → 停手 |
| G0.9 | 音频 bulk `new(194408)` | `SizeToPoolIdx` **必须 miss** | 误接管 = 红线违规 |

---

## 4. 确定性门（合入前必须全绿）

### 4.1 复核前提（T20/T14 维持）`[实证]`

| # | 命题 | 结论 |
|---|---|---|
| D1 | CRT 分配器吃 RNG？ | **否**（`0x7C8B00..0x7D1000` 对 Random 族 0 调用） |
| D3 | 裸堆指针进档？ | **否**（.SAV = OLE/CLSID） |
| D4 | 指针进帧 CRC？ | **否**（`0x64DAB0` = 量化坐标+RNG） |
| D7 | 指针哈希进逻辑 | **禁令**（红线） |

### 4.2 G-门（class3/4 **增量门**：G-ALLOCORDER / G-SAVDIFF 为强制）

| 门 | 判据 | 失败处置 |
|---|---|---|
| **G-RNG** | 池化实现 0 次 `ScenarioClass::Random`/`RandomRanged`/`Randomizer::Global` | 不得合入 |
| **G-SAV** | 无新路径裸堆指针落盘 | 不得合入 |
| **G-CRC** | 帧 CRC 输入集不变 | 不得合入 |
| **G-PTRHASH** | 无地址哈希/枚举序进逻辑 | 不得合入（红线） |
| **G-FAILSEM** | 耗尽/miss 透传 `_nh_malloc@0x007C9442`，语义=原版 | 不得合入 |
| **G-ALLOCORDER** | 构造/析构**顺序**、虚分发、RNG 消耗次数与原版一致（单机 A/B 对拍） | **回退 `MemPoolClass34=0`** |
| **G-SAVDIFF** | 同种子同输入：开池 vs 关池 **.SAV 字节一致**（或 diff 仅未用 padding） | 池化不得进存档路径 |
| **G-MP** | OnlineSafeMode/MpActive 下 L2 全关；ExtraSyncInfo 无 OOS | 强制 L1-only |

> **裁决**：池化不改 RNG/存档；idx8/9 只改变**分配器内部复用时序** → G-ALLOCORDER/G-SAVDIFF 是本卡**必须**过的增量门（R-L2-GAP §5.3）。

---

## 5. 验收 A/B（真机；ZCode 填回执）

### 5.1 三态对拍矩阵（强制）

| 态 | 配置 | 用途 |
|---|---|---|
| **O** 原版 | 不装钩 或 `EnableMemoryPool=0` | 基线 |
| **H** 仅可见性 | H2/H6（另轨）+ `MemPoolClass34=0` | 分离「看见」与「扛住」 |
| **P** 池化 | H2/H6 + `MemPoolClass34=1` | 本卡生效 |

### 5.2 验收步骤

| ID | 步骤 | 期望 | 证据要求 |
|---|---|---|---|
| **B0** | 离线单测：1000 次 alloc `(ptr&7)==0`；二次 Free | 对齐 100%；二次 Free 拒绝且 `doubleFreeRejects` 递增 | 单测日志 |
| **B1** | `EnableMemoryPool=1` + `MemPoolClass34=1` 单机 3 局 ×≥15min | `poolAllocs≈poolFrees`；`doubleFreeRejects` 可解释；`except.txt` 零新增 | 遥测 + `except.txt` |
| **B2** | **G-SAVDIFF / G-ALLOCORDER** 对拍（O vs H vs P） | 存档字节一致；无 RNG 分叉；构造/析构序一致 | 对拍报告 |
| **B3** | 联机门：`OnlineSafeMode=1` | L2 全关；ExtraSyncInfo 无 OOS；日志 `forced-off-mp` | `SYNC*.TXT` 空 |
| **B4** | 开关往返：`MemPoolClass34=0` 重启 | 仅 idx8/9 消失；idx0..7（若开）仍在 | 遥测对照 |
| **B5** | UAF 注入观察（可选） | `uafWriteWhileFree` 能捕获毒填改写（收集不中断） | dump 文件 |

### 5.3 「没崩≠成功」——B1/B2 强制证据

1. **防护生效**：`doubleFreeRejects` 在注入二次 Free 时 >0；毒填校验路径可触发。  
2. **无逻辑漂移**：B2 三态 RNG 消耗/构造序一致；`.SAV` 字节一致。  
3. **生命周期可回退**：B4 证明二阶键单键摘除 idx8/9，不伤其它桶。

---

## 6. 回滚（三级 + 二阶键）

| 级别 | 操作 | 效果 |
|---|---|---|
| **L0 单键** | `EnableMemoryPool=0` **重启进程** | 不装钩，字节逐位 = 原版 |
| **L1 二阶（本卡）** | **`MemPoolClass34=0` 重启** | **仅摘 idx8/9**；idx0..7 仍可用 |
| **L2 二阶** | `MemPoolSmall=0` / `MemPoolEntities=0` 重启 | 分桶回退 |
| **字节级** | `_new@0x007C8E17` 写回 `6A 01 FF 74 24 08`；`_delete@0x007C8B3D` 写回 `FF 74 24 04 E8 A2 08 00 00` | 卸载路径 |
| **禁令** | **局内热切 `EnableMemoryPool`**；池存活时解钩 `_delete` | 否则跨堆释放 → `0xC0000374` |

- 原字节备份**装钩前落盘**：`out/re_work/re_sprint/R_l2_card/orig_bytes.bin`。  
- 补丁器 `--uninstall-crt-l2-c34` 仅还原两入口 5+5B；不触碰 L1 18B。  
- **回滚演练（合入前）**：`EnableMemoryPool=0` 重启 → 字节比对 `_new/_delete` 与原版一致；`MemPoolClass34=0` 重启 → 仅 idx8/9 消失。

---

## 7. 风险（执行方必读）

| ID | 风险 | 等级 | 要求 |
|---|---|---|---|
| R-1 | idx9 改变 class-4 生命周期（崩溃面） | **高** | **强制 A/B**（G-ALLOCORDER）；失败即 `MemPoolClass34=0` |
| R-2 | 侵入式 freelist 被 UAF 写 user+0 污染 | **高** | **只许 B-pref 侧表**；禁 B-min |
| R-3 | 4B 头破坏 8B 对齐 | **高** | 8B `PoolBlockHeader` 强制（TC-ST-04） |
| R-4 | 局内热切 → 跨堆释放 `0xC0000374` | **高** | 启动期锁定；改 INI 必须重启 |
| R-5 | 误接管音频 `new(194408)` | **高** | G0.9 精确区间；bulk 必须 miss |
| R-6 | 与 ZC-CRT-L1 / idx0..7 语义纠缠 | 中 | 本卡只加 idx8/9；不改既有桶 |
| R-7 | 多线程 freelist 撕裂 | 中 | 全路径 CAS；失败退化主线程-only |
| R-8 | 把「没崩」当成功 | 高 | B1/B2 强制遥测与对拍证据 |
| R-9 | 联机误开 Class34 → OOS | **高** | OnlineSafeMode/MpActive 强制关；G-MP |

---

## 8. 与 ZC-CRT-L1 的批次关系（**明确**）

| 项 | ZC-CRT-L1 | **本卡 ZC-CRT-L2-C34** |
|---|---|---|
| 批次 | B4a（可随 L1 安装） | **B4b，独立验收** |
| 默认开 | 全键默认 0 | **`MemPoolClass34` 默认 0，不在 L1 同批默认开** |
| 行为扰动 | 低（不改分配器 ABI） | **有**（生命周期；须 A/B） |
| 联机 | 可保留 L1 | **Class34 禁**；OnlineSafeMode 强制 L1 |
| 回滚 | L1 三键 | **二阶键 `MemPoolClass34=0`** 单独摘除 |

**上线顺序（R-L2-GAP §3.2）**：诊断期/联机期 = H2/H6；单机加固期 = H2/H6 + `MemPoolClass34=1` + A/B 通过。**H2/H6 与本卡不是二选一**：H2/H6 管「看见」，本卡管「扛住」。

---

## 9. 交付回执（填完交回）

```
ZC-CRT-L2-C34 RESULT
- build/md5(gamemd):
- install path: (ra2render trampoline | external patcher | ...)
- EnableMemoryPool / MemPoolClass34 / MemPoolDebug:
- MemPoolSmall / MemPoolEntities: (must stay 0 unless their own cards)
- OnlineSafeMode / MpActive observed:
- G0.1–G0.9: PASS/FAIL
- header: magic/poolIdx 8B enforced: y/n
- freelist: side-table (B-pref) confirmed: y/n
- poison fill 0xDEADBEEF on free: y/n
- initial capacity idx8/idx9: (256/512)
- G-RNG / G-SAV / G-CRC / G-PTRHASH / G-FAILSEM: PASS/FAIL
- G-ALLOCORDER (O vs H vs P): PASS/FAIL
- G-SAVDIFF: PASS/FAIL
- B0..B5: (each PASS/FAIL + evidence path)
- poolAllocs / poolFrees / poolFallbacks / doubleFreeRejects / uafWriteWhileFree:
- except.txt: empty|path
- rollback tested (L0 / MemPoolClass34=0 / byte restore): y/n
- MP: (single | forced-off-mp) + ExtraSyncInfo note
```

---

## 10. 不在本卡

- **L1 全部**（`VectorReuse`/`VectorReserve`/`VectorGeometric`）—— ZC-CRT-L1 / 另卡  
- **H1/H2/H6 可见性钩**（毒族门禁 / 周期毒扫）—— R-L2-GAP Layer A，另轨第一批  
- **idx0..7**（`MemPoolSmall`/`MemPoolEntities`）—— T14 既有卡  
- 写点根治（AddCapacity free 后清槽 / Coords 写前校验）—— Layer C，本规格不展开  
- 台账/看板登记 —— 由 Lead 收口  

---

*依据：`docs/re/crt_l2_class34_fix_spec.md`（R-L2-GAP）§2.1–2.7 / §3 / §5 / §6；`out/re_work/re_sprint/R_l2_gap/bucket_map_class34.txt`（算术复算 MATCH）；`determinism_gate.txt`（G-门状态）；T20 RC13–RC17 确定性复核；T14 F-06/P-M1 块头与回滚铁律；格式对齐 `landing_pack_crt_l1.md`。本卡 `MemPoolClass34` 默认 0，不在 ZC-CRT-L1 同批默认开。*
