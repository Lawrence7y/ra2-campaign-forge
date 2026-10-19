# CRT L2 class3/4 空洞修复落地规格（R-L2-GAP）

> [META]
> 任务=R-L2-GAP · 上游=T20 R-SBH-UAF（`docs/re/sbh_uaf_residual_deep_dive.md`）× T14 R-CRT-POOL（`docs/re/crt_pool_landing.md`）
> 目标二进制：`ra2youli/gamemd.exe`（MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`，ImageBase `0x00400000`）
> 写作用域：本文件 + `out/re_work/re_sprint/R_l2_gap/**`；二进制与 `ra2render/**` 只读
> 证据分级：`[实证]` 字节/反汇编/算术可复算 · `[推演]` 由代码逻辑推断 · `[待实测]` 需运行时

---

## [0] 结论速览（≤12 行）

1. **[实证]** T20 已定谳：CRT L2 八桶 `{≤8,≤12,≤16,≤24,≤40,312,352,456}` 映射 SBH class `{0,1,1,1,2,19,22,28}`；**class 3（req 41..56B）与 class 4（req 57..72B）完全在 L2 覆盖面外**。崩溃 class = 4。
2. **[实证]** L2 命中桶**完全绕开 SBH**（不进 `__sbh_alloc_block`，绕开 `_lock(9)`）；未命中桶穿透原版。class3/4 当前走 SBH freelist，**无 tag / 无投毒 / 无守卫**。
3. **[实证]** UAF 写点：`BasePlanningCellContainer::AddCapacity 0x510860` 的 `_delete(old Items)@0x5108BB`（cap 8/9 → 64/72B = class 4 buffer free）；写者族 `0x552335`/`0x55C643` 等 `mov word [reg],0xFFFF`（`CellStruct` 残值）。
4. **[推演]** 本规格给出两条互补路线：
   - **Layer A（首选，零行为扰动）**：H2/H6 毒族门禁 + H1 入链校验 —— **可见性**，不改分配时序。
   - **Layer B（可选，须 A/B）**：L2 新增 **idx8（class3）/ idx9（class4）** 两桶 —— **防护**（双释放+投毒+守卫），但改变 class4 生命周期。
5. **[实证]** 块头沿用 T14 F-06/P-M1：`PoolHeader{magic,poolIdx}` **8B**、`m_elemSize=(elem+7)&~7`、返回 `pBlock+8`；存活 `0xA5A55A5A` / 释放 `0xDEADBEEF`。
6. **[推演]** idx8/idx9 **推荐非侵入 freelist（块下标侧表）+ 用户区整段投毒**，避免 UAF 写 user+0 池内 freelist 头（与崩溃形态同构的二次污染）。
7. **[实证]** 开关对齐：`EnableMemoryPool` 总闸**启动期单次锁定**；新增 `MemPoolClass34`（默认 **0**）；`MemPoolSmall`/`MemPoolEntities` 不变；`OnlineSafeMode=1` / 联机强制 **仅 L1**。
8. **[实证]** 确定性复核（T20 RC13..RC17 + T14 §3.1）：CRT 体 0 次 RNG 调用；存档 OLE/CLSID 无裸堆指针；帧 CRC=量化坐标+RNG。池化**不改 RNG/存档**成立，门控见 §5。
9. **[推演]** 回滚铁律继承 T14：禁热切、卸载保护、`EnableMemoryPool=0` 两入口不装钩字节逐位相同；class3/4 桶另有单键 `MemPoolClass34=0` 二阶回退。
10. **[待实测]** Layer B 改变 class-4 生命周期 → **必须 A/B**（原版 / +H2H6 / +H2H6+MemPoolClass34）；U3 LFH、U6 毒值业务归因仍开。

---

## [1] 空洞定义与尺寸算术（`[实证]`）

### 1.1 SBH 尺寸类公式（上游 T14/T20）

```
block = (req + 0x17) & ~0xF      // 0x7CFB33
class = (block >> 4) - 1          // 0x7CFB3C，共 64 类
```

| req 窗 | block | class | 业务含义 |
|---|---:|---:|---|
| 1..8 | 16 (0x10) | 0 | 链表节点 |
| 9..24 | 32 (0x20) | 1 | 三元组/短向量（L2 idx1..3 塌缩） |
| 25..40 | 48 (0x30) | 2 | DVC 步长块 |
| **41..56** | **64 (0x40)** | **3** | **L2 空洞** |
| **57..72** | **80 (0x50)** | **4** | **L2 空洞 = 崩溃 class** |
| 73..1008 | … | 5..63 | 其余 |
| 312 / 352 / 456 | 320/368/464 | 19/22/28 | Particle/Bullet/Anim（L2 实体桶） |

### 1.2 L2 现状桶（T14 `SizeToPoolIdx`）

| idx | req 命中 | SBH class | 头 | 防护 |
|---:|---|---:|---|---|
| 0 | ≤8 | 0 | 8B | 双释放+投毒+范围守卫 |
| 1 | ≤12 | 1 | 8B | 同上 |
| 2 | ≤16 | 1 | 8B | 同上 |
| 3 | ≤24 | 1 | 8B | 同上 |
| 4 | ≤40 | 2 | 8B | 同上 |
| 5 | ==312 | 19 | 8B | 同上 |
| 6 | ==352 | 22 | 8B | 同上 |
| 7 | ==456 | 28 | 8B | 同上 |
| — | **41..56** | **3** | — | **无** |
| — | **57..72** | **4** | — | **无（崩溃面）** |

> **[实证]** 算术复算：`req=41 → block=0x40 class=3`；`req=56 → block=0x40 class=3`；`req=57 → block=0x50 class=4`；`req=72 → block=0x50 class=4`。详见 `out/re_work/re_sprint/R_l2_gap/bucket_map_class34.txt`。

---

## [2] Layer B：L2 扩桶落地规格（尺寸 / 头 / 毒 / CAS / 回滚）

### 2.1 新桶定义（`[推演]`，算术 `[实证]`）

| 新 idx | req 窗 | elemSize | m_elemSize | 池块总长 | 用户区 | 对应 SBH |
|---:|---|---:|---:|---:|---:|---|
| **8** | 41..56 | 56 | 56 | 8+56=**64** | 56B | class 3 |
| **9** | 57..72 | 72 | 72 | 8+72=**80** | 72B | class 4 |

```cpp
// SizeToPoolIdx 追加（其余分支不动）：
if (sz >= 41 && sz <= 56) return 8;   // class 3
if (sz >= 57 && sz <= 72) return 9;   // class 4
static FixedPool s_pools[10];         // 原 [8] → [10]
```

- **精确命中**（区间），不做模糊范围，避免误接管；`new(194408)` 音频 bulk 仍必须 miss → 穿透 `[实证]` 红线。
- 池耗尽 / miss：**透传** `_nh_malloc@0x007C9442`，失败语义与原版一致（确定性前提，见 §5）。

### 2.2 块头（强制，继承 F-06 / P-M1）`[实证]`

```cpp
#pragma pack(push, 8)
struct PoolBlockHeader {
    uint32_t magic;    // 存活 0xA5A55A5A / 释放 0xDEADBEEF
    uint32_t poolIdx;  // 0..9（独立字段，禁止与 magic 位域复用）
};
#pragma pack(pop)      // sizeof == 8；返回 pBlock+8，8 字节对齐
```

- `m_elemSize = (elemSize + 7) & ~7`；56/72 均已 8 对齐。
- **禁止 4B 头**（TC-ST-04 一票否决）：会破坏 `double`/SSE 8B 对齐。

### 2.3 投毒与 UAF 形态适配（idx8/9 专用）`[推演]`

崩溃形态：UAF 写 `CellStruct` 到**已 free 块 user+0**（= 侵入式 freelist 的 `next`）。

| 方案 | freelist | free 行为 | UAF 写 user+0 | 推荐 |
|---|---|---|---|---|
| **B-min** | 侵入式（user+0 = next），同 idx0..7 | magic→`0xDEADBEEF` | **污染 freelist**（与崩溃同构） | 不推荐 |
| **B-pref** | **块下标侧表**（`uint32_t m_freeIdx[]`） | magic→`0xDEADBEEF` **+ 用户区整段填 `0xDEADBEEF`** | **只打到毒填料，不破坏 freelist** | **推荐** |

**B-pref 细则**：
1. freelist = 栈式下标链（`m_freeIdx[blk] = prevFree`；`m_freeHead` 用 CAS 更新）。
2. `Free`：范围守卫 → `magic==0xA5A55A5A` 才回收，否则透传/计数拒绝（双释放免疫）→ `magic=0xDEADBEEF` → `memset(user, 0xDEADBEEF, m_elemSize)` → 下标入链。
3. `Alloc`（`MemPoolDebug=1` 时）：出块前校验用户区仍为 `0xDEADBEEF` 整段；若被改写 → 记 `uafWriteWhileFree++` + dump（**不中断**，收集为主；可选 `MemPoolDebugStrict=1` 断言）。
4. 双释放：`magic==0xDEADBEEF` → `doubleFreeRejects++`，**不入链**，透传原版 free（或直接拒绝并返回；需与原版失败语义 A/B）。

### 2.4 CAS 与线程（`[推演]`，继承 P-M4/威胁四）

- `Alloc/Free` 的 `m_freeHead` 更新一律 `InterlockedCompareExchangePointer`（或 `InterlockedCompareExchange` for 32-bit index）。
- 音频/网络线程可能 `new/delete`；L2 全路径 CAS 必做。若 A/B 发现撕裂，退化为「L2 仅主线程启用」（`GetCurrentThreadId==g_mainThread` 才命中桶）。

### 2.5 初始容量与耗尽

| 桶 | 建议初始 capacity | 理由 |
|---:|---:|---|
| idx8 (56B) | 256 | class3 站点少于 class4 |
| idx9 (72B) | 512 | 崩溃面；U0200 高 churn 需余量 |

- 耗尽 → **透传原版**（不扩容、不挪已有块），保证「一端有池一端无池」时控制流可对齐。
- 遥测：`poolAllocs/poolFrees/poolFallbacks/doubleFreeRejects/uafWriteWhileFree`。

### 2.6 开关矩阵（与总闸对齐）

| 键 | 节 | 默认 | 语义 | 锁定 |
|---|---|---:|---|---|
| `EnableMemoryPool` | `[System]` 或 `[MemoryPool]` | **0** | 总闸；0 → 两入口不装钩，字节与原版逐位相同 | **启动期单次锁定，严禁局内热切** |
| `MemPoolSmall` | `[MemoryPool]` | 0 | idx0..4（8/12/16/24/40） | 同上 |
| `MemPoolEntities` | `[MemoryPool]` | 0 | idx5..7（312/352/456） | 同上 |
| **`MemPoolClass34`** | `[MemoryPool]` | **0** | **idx8/9（41..56 / 57..72）= 本规格** | 同上 |
| `MemPoolDebug` | `[MemoryPool]` | 0 | 遥测 + 毒填料校验 | 可局内改（只影响观测，不影响分配） |
| `OnlineSafeMode` | `[Logic]` | 0 | =1 或 `MpActive()` → **强制 L1-only** | 启动/进局判定 |

**门控伪码**：
```text
if (!EnableMemoryPool) → 不装钩
effectiveSmall    = MemPoolSmall    && !OnlineSafeMode && !MpActive
effectiveEntities = MemPoolEntities && !OnlineSafeMode && !MpActive
effectiveClass34  = MemPoolClass34  && !OnlineSafeMode && !MpActive   // 默认关
```

### 2.7 回滚（继承 P-M5 / 威胁五 + 本规格二阶键）

| 层级 | 动作 | 效果 |
|---|---|---|
| L0 单键 | `EnableMemoryPool=0` **重启进程** | 不装钩，字节逐位 = 原版 |
| L1 二阶 | `MemPoolClass34=0` 重启 | 仅摘 idx8/9；idx0..7 仍可用 |
| L2 二阶 | `MemPoolSmall=0` / `MemPoolEntities=0` 重启 | 分桶回退 |
| 字节级 | `_new@0x007C8E17` 写回 `6A 01 FF 74 24 08`；`_delete@0x007C8B3D` 写回 `FF 74 24 04 E8 A2 08 00 00` | 卸载路径 |
| 禁令 | **局内热切 `EnableMemoryPool`**；池存活时解钩 `_delete` | 否则跨堆释放 → `0xC0000374` |

---

## [3] Layer A：H2/H6 可见性钩 vs 池化防护 —— 分工

| 维度 | **H2/H6（可见性）** | **L2 class3/4 池化（防护）** |
|---|---|---|
| 目的 | 发现/定谳 UAF 污染 | 阻止 UAF 伤害 + 双释放免疫 |
| 行为扰动 | **零**（只观测/断言） | **有**（生命周期改变，须 A/B） |
| 覆盖面 | **全部 SBH class**（含 3/4/其它） | 仅 idx8/9 命中窗（41..72） |
| 崩溃形态 | 毒族进 `head->next` 即 dump+断 | 毒填料使 UAF 写可检；双释放拒绝 |
| 联机 | 可开（观测不影响锁步） | **禁**（`OnlineSafeMode`/`MpActive` 强制关） |
| 上线顺序 | **第一批必装** | 第二批，`MemPoolClass34` 默认 0 |

### 3.1 H1/H2/H6 规格（继承 R-02 §7，落地钩点）`[实证]`+`[推演]`

| ID | 钩点 | 触发 | 检查 | 失败动作 |
|---|---|---|---|---|
| **H1** | `__sbh_alloc_block` `0x7CFD4C` 前 | 每次入链 | node ∈ region、16B 对齐、size 匹配 class | 记录，**不中断** |
| **H2** | `__sbh_alloc_block` `0x7CFD52` 前 | 每次 `head->next=node` | node/head 合法；**node ∉ 毒族** | 毒族 → **dump + 断** |
| **H6** | 周期（每 K 次 alloc / 每 N 帧） | 全 region head 数组 + free 节点 `next/prev` | 命中毒族白名单 | **FAIL 门禁** |

**毒族白名单**（harness `except_watch`）：
- P0 `0xFE00FFFF`（本次主毒，`CellStruct{-1,-512}`）
- P1 `0xFFFF0000`、`POIS_XYFFFFxx`（高16∈{FE00,FF00,FFFF} ∧ 低16∈{0000,FFFF,FE00}）
- P2 `0x00000001..0xFF` 非对齐指针形态；`POIS_SELFFREE`（next==self 且非 head）

### 3.2 分工结论

```text
诊断期 / 联机期：  H1+H2+H6  （可见性，零扰动）
单机加固期：      H1+H2+H6 + MemPoolClass34=1 + A/B 通过
根治（可选 C）：  写点补丁（AddCapacity free 后清旧指针槽；Coords 写前校验）——本规格不展开
存档/MP（D）：    无需动作（无堆地址进档）
```

**关键裁决**：H2/H6 与 L2 池化**不是二选一**。H2/H6 管「看见」，L2 管「扛住」。class3/4 在未开 `MemPoolClass34` 时，**H2/H6 是唯一可见性手段**（T20 U7 结论维持）。

---

## [4] 与 `MemPoolSmall` / `EnableMemoryPool` / `OnlineSafeMode` 对齐

### 4.1 总闸继承（T14 / 执行总表 / F-02）

| 条目 | 口径 | 来源 |
|---|---|---|
| `EnableMemoryPool` 默认 | **0**（启动期单次锁定） | `pending_execution_master_table.md:49,301,322`；F-02 已订正 |
| 热切禁令 | 局内动态开关 → 存活对象跨堆释放 `0xC0000374` | `crt_pool_risk_review.md` 威胁五；`execution_runbook.md` P-M5 |
| `MemPoolSmall` | 只管 idx0..4；**不隐含 class3/4** | T14 §2.3 |
| 新增 `MemPoolClass34` | 独立二阶键，默认 0 | 本规格 §2.6 |

### 4.2 联机 / OnlineSafeMode

| 场景 | 允许 |
|---|---|
| 单机 / 战役 | L1 + （L2 小桶/实体/Class34 按键） |
| 联机 / 混联 | **仅 L1**（VectorReuse/Reserve/Geometric） |
| `OnlineSafeMode=1` | 强制 `MemPoolSmall=MemPoolEntities=MemPoolClass34=0` |
| `MpActive()`（`0x00A8D5F8` 会话位） | 同上强制，并告警日志 |

> 与 `mp_autodowngrade_spec.md` 的 `MpAutoDowngrade` 语义兼容；落地时任选一名，文档需统一（本规格采用 `OnlineSafeMode`）。

### 4.3 联机风险条目（继承 D-CRT-L2）

`net_sync_desync_map.md` D-CRT-L2：L2 池化改堆布局/指针序 → **RISK**（指针序敏感）。故联机**只许 L1**；L2（含 class3/4）单机。`MemPoolDebug` 可联机开（只读观测）。

---

## [5] 确定性门控（池化不改 RNG/存档 —— 复核 + 门）

### 5.1 T20 复核结论（本轮重申，静态）`[实证]`

| # | 命题 | 结论 | 证据 |
|---|---|---|---|
| D1 | CRT 分配器吃 RNG？ | **否**。`0x7C8B00..0x7D1000` 对 `Random@0x65C780` / `RandomRanged@0x65C7E0` / `Global@0x886B88` **0 调用** | T14 claims；T20 RC16 |
| D2 | 池化改 RNG 流？ | **否**（实现不得新增 Random 调用；分配地址不参与随机） | 由 D1 `[推演]` |
| D3 | 裸堆指针进档？ | **否**。`.SAV`=OLE2/CFB，`OleSaveToStream` CLSID（IAT `0x7E15F4`）；`Save_Core` 43 处 imm 均为 `.bss` this | T20 RC13/RC14 |
| D4 | 指针进帧 CRC？ | **否**。`0x64DAB0` = 量化坐标 + RNG | T20 RC16 |
| D5 | `FillEvent_Waypoints`？ | `CellStruct` + frame 计数，无指针 | T20 RC15 |
| D6 | .SAV 字节普查 | img/heap-ptr-like 命中为 OLE 目录/UTF-16/坐标假阳性 | T20 RC17 |
| D7 | 指针哈希进逻辑 | **禁令**（M-5 / 台账 §6.2） | 红线 |

**复核状态**：`out/re_work/re_sprint/R_l2_gap/determinism_gate.txt` + `verify_l2_gap.py`（算术重放 + 标记复扫）。

### 5.2 确定性门（合入前必须全绿）

| 门 | 判据 | 失败处置 |
|---|---|---|
| **G-RNG** | 池化实现源/补丁体 0 次 `ScenarioClass::Random`/`RandomRanged`/`Randomizer::Global` 调用 | 不得合入 |
| **G-SAV** | 新增写存档路径 0 次裸堆指针落盘（只允许 CLSID/逻辑 ID/量化坐标） | 不得合入 |
| **G-CRC** | 帧 CRC 输入集不变（量化坐标 + RNG） | 不得合入 |
| **G-PTRHASH** | 池化不得引入 `(uintptr_t)p>>4` / 堆地址枚举序 / 地址哈希进逻辑或分片 | 不得合入（红线） |
| **G-FAILSEM** | 池耗尽/miss **透传原版**，NULL/`_callnewh` 语义与原版一致 | 不得合入 |
| **G-ALLOCORDER** | 构造/析构**顺序**、虚函数分发、RNG 消耗次数与原版一致（单机 A/B 对拍） | A/B 失败则回退 `MemPoolClass34=0` |
| **G-SAVDIFF** | 同种子同输入：开池 vs 关池 **.SAV 字节一致**（或 diff 仅限未使用 padding） | 不一致则池化不得进存档路径 |
| **G-MP** | `OnlineSafeMode`/`MpActive` 下 L2 全关；`ExtraSyncInfo` 对拍无 OOS | 有 OOS → 强制 L1-only |

### 5.3 确定性结论

> **[实证+推演] 池化不改 RNG、不改存档字节（OLE/CLSID + 量化 CRC），T20 无堆地址进档结论维持。**
> 前提 = 实现遵守 G-RNG/G-PTRHASH/G-FAILSEM；class3/4 扩桶不改变该前提，只改变**分配器内部复用时序**，故 G-ALLOCORDER/G-SAVDIFF 是 class3/4 的**增量门**。

---

## [6] 落地批次与验证门槛

| 批 | 内容 | 开关 | 验证 Pass |
|---|---|---|---|
| **A1** | H2 毒族门禁（`0x7CFD52` 前） | `EnableSbhGuards=1`（独立观测开关） | 注入态崩溃 → dump 命中 `0xFE00FFFF` |
| **A2** | H6 周期毒扫 + H1 收集 | 同上 | 存量污染可扫出；0 误杀 |
| **B0** | 对齐单测 / 双释放单测（离线） | — | 1000 次 `(ptr&7)==0`；二次 Free 拒绝 |
| **B1** | `MemPoolClass34=1` 单机 A/B | `EnableMemoryPool=1` | 3 局 ×≥15min：`poolAllocs≈poolFrees`、`doubleFreeRejects` 可解释、`except.txt` 零新增 |
| **B2** | G-SAVDIFF / G-ALLOCORDER | 开/关池对拍 | 存档字节一致；无 RNG 分叉 |
| **B3** | 联机门 | `OnlineSafeMode=1` | L2 全关；ExtraSyncInfo 无 OOS |

**回滚演练**（合入前）：`EnableMemoryPool=0` 重启 → 字节比对 `_new/_delete` 与原版一致；`MemPoolClass34=0` 重启 → 仅 idx8/9 消失。

---

## [7] 证据索引

| 文件 | 内容 |
|---|---|
| `out/re_work/re_sprint/R_l2_gap/claims.txt` | 本任务 claims 注册表 |
| `out/re_work/re_sprint/R_l2_gap/bucket_map_class34.txt` | 尺寸/桶/class 全表 + 算术复算 |
| `out/re_work/re_sprint/R_l2_gap/determinism_gate.txt` | 确定性复核 + G-门状态 |
| `out/re_work/re_sprint/R_l2_gap/verify_l2_gap.py` | 可复算脚本（算术 + 标记） |
| `out/re_work/re_sprint/R_sbh_uaf/crt_l2_sbh_crossmap.txt` | T20 交叉映射（上游） |
| `out/re_work/re_sprint/R_sbh_uaf/claims.txt` | T20 RC01..RC22（上游） |
| `docs/re/crt_pool_landing.md` | T14 池化落地规格（上游） |
| `docs/re/sbh_uaf_residual_deep_dive.md` | T20 残差闭环（上游） |
| `docs/re/sbh_freelist_deep_dive.md` | R-02 H1/H2/H6 草案（上游） |

**禁止写入区**（本规格遵守）：`ra2render/**`、`gamemd.exe`、`ra2youli/**`、`tools/**`、台账、看板。

**一句话**：class3/4 是 L2 与 SBH 之间的空洞且恰为崩溃面；H2/H6 负责可见、`MemPoolClass34` 桶负责防护，`EnableMemoryPool`/`OnlineSafeMode` 总闸不变，确定性以 G-RNG/G-SAV/G-PTRHASH/G-FAILSEM 门控，池化不改 RNG/存档（T20 维持）。
