# CRT 池化落地规格（R-CRT-POOL）

> **任务**=R-CRT-POOL · **目标**=`gamemd.exe` 1.001（MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`，ImageBase `0x00400000`）
> **定位**：把「CRT 池化」从已逆向清单落到**可实施、可开关、可回滚**的规格；全静态，不改二进制。
> **证据分级**：`[实证]` 字节/反汇编可复算 · `[推演]` 由代码逻辑推断 · `[待实测]` 需运行时
> **复算产物**：`out/re_work/re_sprint/R_crt_pool/{claims.txt,claims_movreg.txt,site_bytes.txt}`（`verify_crt_abi.py` / `scan_sizes_movreg.py` / `dump_sites.py`）
> **上游深潜**（只读）：`docs/re/crt_memory_pool_deep_dive.md`、`docs/re/crt_callgraph.md`、`docs/re/crt_pool_risk_review.md`、`docs/re/sbh_freelist_deep_dive.md`、`docs/re/landing_pack_crt_audio_particle.md`、`docs/re/net_sync_checksum.md`、`docs/re/savegame_block_manifest.md`

---

## 0. 结论速览（Top 3 落地点）

| # | 落地点 | 手段 | 开关 | 风险 |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **L1 向量非破坏性 Clear + Reserve**（`0x004E97B0` 族 / `TechnoClass+0x440/0x458`） | 语义级降频，不碰分配器 ABI | `VectorReuse=0/1` | 低（不改 ABI；仅改变缓冲何时还堆） |
| **2** | **L2 定长 Freelist 旁路 8/12/16/24B** | Hook `CRT::_new@0x007C8E17` / `CRT::_delete@0x007C8B3D` | `MemPoolSmall=0/1` | 中（8B 头对齐 + 范围守卫 + 投毒必做） |
| **3** | **L2 实体桶 312/352/456B**（Particle/Bullet/Anim） | 同上，按尺寸命中专用桶 | `MemPoolEntities=0/1` | 中高（对象生命周期/双重释放） |

**总开关**：`[MemoryPool] EnableMemoryPool=0/1`（**启动期锁定，禁止热切换**）。默认建议：**仅开 #1**；#2/#3 作为第二阶段。
> 【W3 勘误 · FREEZE_CANDIDATE §7 C9,C23 / Lead DC-01,DC-04】[W3-Lead临时裁决] 改前：总开关：`[MemoryPool] EnableMemoryPool=0/1`；改后：依 DC-01 节名裁定归属 `[System]`（`blitter_hooks.cpp:541,544` 已存在并实读 `[System]`，零新增节、零补 ini）；依 DC-04 裁决 `PoolBlockCount` 保持未定（不入冻结面，仅 `EnableMemoryPool` 按 0 冻结）；依据：Lead 临时裁决 DC-01、DC-04；分级：[推演]

---

## 1. CRT 分配/释放路径 ABI

### 1.1 入口与邻域（`0x007C8E17`）[实证]

| 符号 | 地址 | 序言字节 | 语义 |
| :--- | :--- | :--- | :--- |
| `CRT::_new` | `0x007C8E17` | `6A 01 FF 74 24 08 E8 20 06 00 00 59 59 C3` | `push 1; push size; call _nh_malloc; pop; pop; ret`，`__cdecl` |
| `CRT::_delete` | `0x007C8B3D` | `FF 74 24 04 E8 A2 08 00 00 59 C3` | `push p; call free; pop; ret`（**薄封装 = free**） |
| `CRT::malloc` | `0x007C9430` | `FF 35 C4 82 B7 00 FF 74 24 08 E8 03 00 00 00 59 59 C3` | `_nh_malloc(size, [_newmode@0xB782C4])` |
| `CRT::free` | `0x007C93E8` | `56 8B 74 24 08 85 F6 74 3D 6A 09 ...` | NULL 早退；`_lock(9)` → SBH/HeapFree |
| `_nh_malloc` | `0x007C9442` | — | 溢出检查 `size>0xFFFFFFE0`→NULL；失败且 nhFlag→`_callnewh@0x7D06E8` 重试 |
| `heap_alloc` | `0x007C946E` | — | `size≤__sbh_threshold`→SBH；否则 16B 对齐 `HeapAlloc` |

> [实证] **地址勘误**：`0x007C8E3B` 字节 `4D 0C 3B CF` 是 `bsearch` 中段指令，**不是** `_delete`；唯一真实 `_delete=0x007C8B3D`（`claims.txt` 行 7–11）。

### 1.2 路径图与锁

```
CRT::_new (0x7C8E17)          CRT::malloc (0x7C9430)
        │ nhFlag=1                    │ nhFlag=_newmode
        └────────────┬────────────────┘
                     ▼
            _nh_malloc (0x7C9442)
                     ▼
            heap_alloc (0x7C946E)
          size ≤ 0x3F8 (1016B) ?
           /YES              \NO
          ▼                   ▼
   _lock(9)@0x7CD9F5    (size+0xF)&~0xF
   __sbh_alloc_block    HeapAlloc [0xB78B9C]
   (0x7CFB13)           IAT [0x7E1278]
   _unlock(9)@0x7CDA56
```

| 关键事实 | 证据 |
| :--- | :--- |
| `__sbh_threshold@0x87C584 = 0x3F8 (1016B)` | [实证] `claims.txt` |
| SBH 块公式 `block=(req+0x17)&~0xF`，`class=(block>>4)-1`，64 类 | [实证] `0x7CFB33/0x7CFB3C` |
| **每次** alloc/free 无条件 `_lock(9)/_unlock(9)`（`_HEAP_LOCK`） | [实证] `0x7C947C` / `0x7C93F1` |
| `free` 对 SBH 块：`__sbh_find_block@0x7CF7BD` 线性扫 Region 数组（步长 0x14） | [实证]（`sbh_freelist_deep_dive.md`） |
| 大块（>1016B）绕开 SBH，仍经 CRT 包装 → 仍走 `HeapAlloc/HeapFree` | [实证] |
| CRT 分配器本体（`0x7C8B00..0x7D1000`）**0 次**调用 `ScenarioClass::Random` / `RandomRanged` / `Randomizer::Global` | [实证] `claims.txt` |

### 1.3 静态调用量级 [实证]

| 入口 | 静态 `E8` 站点 | 备注 |
| :--- | ---: | :--- |
| `_delete` | **4498** | 最高；≡ `free` |

> 【勘误 2026-09-30 · R-E06 · errata_sync】计数口径注记（不改上表原值）：上表 `_delete` **4498** 为 **线性反汇编口径**；模式扫描+指令边界确认真值 **≥ 4499**（第 4499 处 = `0x0074836A`）。引用静态量级时须标口径；相对差 0.02%，不影响池化决策。权威：ARCHITECTURE_ATLAS.md:4472-4478。原文保留不删字。
| `_new` | **2832** | 次高 |
| `sprintf` | 317 | 非本规格核心（见去 sprintf 线） |
| `free` | 172 | 多数走 `_delete` |
| `malloc` | 54 | 引擎内部少用 |
| `vsprintf` | 1 | 可忽略 |

**向量模板区** `0x4E7000..0x4EF000`：`_new` 79 站点 / `_delete` 191 站点 [实证]。`0x004E97B0`（`VectorClass::Clear`）本体仅 **1 处** `_delete`（`0x004E97C3`），但该区域是全游戏 Vector 模板实例化集中带，扫描器常把 300+ 站点归到代表符号——池化收益具全局性 [实证+推演]。

### 1.4 与「游戏 Freelist / SBH」关系

| 层 | 是什么 | 与本规格关系 |
| :--- | :--- | :--- |
| **游戏内 Freelist** | 例：音频 Voice 池 `FixedPool::Init@0x004074D0` → 仅初始化一次 `call CRT::_new@0x007C8E17`（尺寸**计算得出** ≈194408B，`83 C0 08 50 E8 32 19 3C 00`）；运行时纯自管 Freelist | [实证] `site_bytes.txt`。**CRT 耦合低**：L2 池不得误接管该大块；`SizeToPoolIdx` 必须 miss → 穿透 |
| **SBH** | CRT 自带 Small Block Heap（≤1016B），64 size-class + Region 位图 + freelist | 本规格 L2 在 **`_new/_delete` 最前**旁路，命中桶后**完全不进 SBH**，也就绕开 `_lock(9)` |
| **Win32 Heap / LFH** | >1016B 或 SBH 失败兜底 | 保持原状；LFH 与专用桶可共存（LFH 管全局，专用桶管密集战斗对象）[推演] |

> 音频线结论（`audio_throttle_landing.md`）**独立成立**：L2 对 `new(194408)` 必须 miss。回滚时也只需还原 5/9 字节跳转，不影响音频 Freelist。

---

## 2. 池化 / 降频候选

### 2.1 尺寸桶（静态站点数）[实证]

| 尺寸 | 静态站点（imm） | 对象 | 措施 | 优先级 |
| ---: | ---: | :--- | :--- | :---: |
| **8** | 176 | 链表节点簇（`0x0048EBF0` 等） | **Freelist 池** | P0 |
| **12** | 132 | 三元组/记录 | Freelist 池 | P1 |
| **16** | 196 | 节点 / `VectorClass` 体 | **Freelist 池** | P0 |
| **24** | 67 | `DynamicVectorClass` 体 | Freelist 池 | P1 |
| **40** | 65 | DVC 步长 10×4B 增长块 / 对话 | 池 **或** L1 预留消灭 | P0（优先 L1） |
| **80 / 160** | 8 / 5 | DVC 20/40 指针增长块 | L1 几何扩容消灭 | P1 |
| **312 (0x138)** | 8 | `ParticleClass`（样例 `0x0062E39C`） | **实体池** | P0 |
| **352 (0x160)** | 3 | `BulletClass`（`0x006C50C1`） | **实体池** | P0 |
| **456 (0x1C8)** | 149 | `AnimClass`（`0x00414C2B` 等） | **实体池** | P0 |
| 计算尺寸 | — | 音频 bulk ≈194408 | **禁止池化，必须穿透** | 红线 |

> 尺寸提取口径：`push imm; call _new`（`scan_sizes_movreg.py`）。`lea eax,[reg*4]` 增长尺寸静态不可定值（scale=4 出现 472 次、scale=8 出现 74 次）→ 走 L1 降频而非 L2 尺寸桶 [实证]。

### 2.2 L1：向量降频（最小侵入，推荐首批）

| 项 | 原字节 / 钩点 | 做法 | 开关 | 回滚 |
| :--- | :--- | :--- | :--- | :--- |
| **非破坏性 Clear** | `0x004E97B0`：`53 56 8B F1 33 DB 8B 46 04 3B C3 74 11 38 5E 0D 74 0C 50 E8 75 F3 2D 00 83 C4 04 89 5E 04 88 5E 0D 89 5E 08 5E 5B C3` | 对「可复用」向量：仅 `Count=0`，保留 `Items/Capacity`；析构时才 `_delete`。`0x006F8F96/0x006F8FA5` 寻敌目标列表为首要受益点 | `VectorReuse=1` | 还原 5 字节 `E9` 跳板；或跳板内 `jmp` 原逻辑 |
| **几何扩容** | `0x006C6421`：`03 C1`（`add eax,ecx` = `Capacity+Increment`） | `newCap = max(Cap+Inc, Cap+(Cap>>1))` | `VectorGeometric=1` | 跳板内分支关断 |
| **Reserve 预留** | `SetCapacity@0x004E9840`；`lea eax,[ebp*4]@0x004E985A` | 构造/加载时注入：`TechnoClass+0x458` CurrentTargets=16、`+0x440` AttackedTargets=16、空间查询桶 128 | `VectorReserve=1` | 不装即回退 |

**收益机理**：战术寻敌每逻辑帧 `Clear()→_delete` + `AddItem()→SetCapacity(10)→_new(40)` 震荡；L1 直接消灭该环，覆盖 `_delete` 静态份额的约 38%（向量族）[实证计数 + 推演运行时]。

### 2.3 L2：Freelist 旁路（第二阶段）

**钩点**（均满足 5 字节 `E9 rel32`）：

| 目标 | 地址 | 原字节长度 | 跳板保留 |
| :--- | :--- | ---: | :--- |
| `CRT::_new` | `0x007C8E17` | 5 字节可用（序言 14B，取前 5） | 原 5 字节 + `jmp 0x007C8E1C` |
| `CRT::_delete` | `0x007C8B3D` | 5 字节可用（序言 9B，取前 5） | 原 5 字节 + `jmp 0x007C8B42` |

**块头（强制，来自风险评审 P-M1..M4）**：
```cpp
#pragma pack(push, 8)
struct PoolBlockHeader { uint32_t magic; /* live 0xA5A55A5A / freed 0xDEADBEEF */ uint32_t poolIdx; };
#pragma pack(pop)   // sizeof == 8；m_elemSize=(elemSize+7)&~7；返回 pBlock+8（8 字节对齐）
```
- **范围守卫**：`Free` 先判 `pBlock ∈ [m_buffer, m_bufferEnd)`，否则透传 `CRT::free@0x007C93E8`。
- **投毒**：归还即 `magic=0xDEADBEEF`（双释放免疫）。
- **CAS**：`InterlockedCompareExchangePointer` 更新 freelist 头（音频/网络线程安全）。
- **池耗尽 / 尺寸 miss**：透传 `_nh_malloc@0x007C9442`（或原 `_new` 跳板），**行为与原版一致**。

| 开关 | 值 | 语义 |
| :--- | :--- | :--- |
| `EnableMemoryPool` | 0/1 | 总闸；**装载时读取一次** |
| `MemPoolSmall` | 0/1 | 8/12/16/24B 桶 |
| `MemPoolEntities` | 0/1 | 312/352/456B 实体桶 |
| `MemPoolDebug` | 0/1 | 遥测：allocs/frees/fallbacks/double_free_rejects |

> 【W3 勘误 · FREEZE_CANDIDATE §7 C17 / Lead DC-04】[W3-Lead临时裁决] 针对拟定键 `PoolBlockCount`：依 DC-04 裁决保持未定（不入冻结面，P-4 仅 `EnableMemoryPool` 按 0 冻结）；依据：Lead 临时裁决 DC-04；分级：[推演]

**回滚铁律**（`crt_pool_risk_review.md` 威胁五）：
1. 开关**禁止局内热切换**；改 INI 后须重启进程。
2. 卸载 DLL 时若仍有池内存存活，**不得**解钩 `_delete`——必须保持钩子直到进程退出，或确认 0 存活再解。
3. 单键回退：`EnableMemoryPool=0` → 两入口不装钩，字节与原版逐位相同。

---

## 3. 确定性与 MP 策略

### 3.1 分配失败 / 指针进存档 / RNG 是否分叉

| 问题 | 结论 | 证据 |
| :--- | :--- | :--- |
| **分配器是否吃 RNG** | **否**。CRT 体（`0x7C8B00..0x7D1000`）对 `Random@0x65C780` / `RandomRanged@0x65C7E0` / `Global@0x886B88` **0 调用** | [实证] |
| **池化是否改变 RNG 流** | **否**，只要实现不新增任何 `ScenarioClass::Random` 调用。分配地址不参与随机 | [推演]（由上一条） |
| **指针是否进存档** | **否裸地址**。存档 = OLE 复合文档 + `OleSaveToStream/OleLoadFromStream`（CLSID 寻址），镜像内未见裸指针落盘 | [实证] `savegame_block_manifest.md` |
| **指针是否进帧 CRC** | **否**。帧 CRC `0x64DAB0` 混合的是量化坐标 + RNG，不是堆地址 | [实证] `net_sync_checksum.md` §1 |
| **指针是否进 CalculateChecksum** | 对象 CRC 为诊断（SYNC*.TXT），字段若含对象链接指针则各端值不同——但该 CRC **不进锁步契约**；锁步靠帧 CRC + 命令序 | [实证+推演] |
| **分配失败分支** | 原版：`_new` 失败 → `_callnewh` 循环或 NULL；调用方对 NULL 处理分散。池耗尽时必须**透传原路径**，保证失败语义与原版一致，避免一端有池一端无池时控制流分叉 | [推演] |
| **指针哈希参与逻辑** | **禁止**（台账 §6.2 / M-5）：`(uintptr_t)this>>4` 分片已判联机 OOS 风险。池化不得引入任何基于堆地址的枚举序/分片/随机 | [实证] 红线 |

### 3.2 MP 策略（建议）

| 场景 | 策略 |
| :--- | :--- |
| **联机 / 混联** | **仅允许 L1**（VectorReuse/Reserve/Geometric）：它们只改「缓冲何时还堆」，不改逻辑序、不改 RNG、不改存档格式。L2 默认 **关** |
| **单机 / 战役** | L1+L2 可全开；实体桶收益最大 |
| **OnlineSafeMode=1** | 强制 `MemPoolSmall=0`、`MemPoolEntities=0`（仅 L1） |
| **一致性论证** | 池不改变：① 对象构造/析构**顺序**；② 虚函数分发；③ RNG 消耗次数；④ 存档字节（OLE/CLSID）；⑤ 帧 CRC 输入。故锁步不受地址差异影响 [推演，需 U800 三局实测背书] |
| **残留风险** | 若某处把指针值当整数写入逻辑状态（未在静态全扫中排除），则各端池地址不同会分叉 → 首批落地前跑 `ExtraSyncInfo` 对拍 [待实测] |

---

## 4. 风险排序 + 推荐首批

### 4.1 风险排序（高 → 低）

| 序 | 风险 | 等级 | 缓解（必须做） | 来源 |
| :---: | :--- | :---: | :--- | :--- |
| R1 | **双释放 → Freelist 自环**，后续 alloc 返回同一地址 | **致命** | 归还投毒 `0xDEADBEEF`；二次释放命中校验失败并计数拒绝 | 风险评审威胁二 |
| R2 | **非原子回滚 / 热切开关** → 池指针进原版 `free` → `0xC0000374` | **致命** | 开关启动期锁定；卸载保护；禁止热切换 | 威胁五 |
| R3 | **8 字节对齐破坏**（4B 头）→ `double`/SSE 错位崩溃 | **致命** | **8B 头 + 8 对齐 + 返回 `pBlock+8`**（F-06/P-M1） | 威胁一 |
| R4 | **Tag 误判**（外部块头恰为魔数）→ 污染 freelist | **高** | **地址范围守卫** + magic 双字段 | 威胁三 |
| R5 | **跨线程撕裂**（音频/网络回调 new/delete） | **高** | 全路径 CAS；或 L2 仅主线程启用 | 威胁四/六 |
| R6 | **误接管音频 bulk `new(≈194408)`** | 中 | 尺寸精确命中（非范围模糊匹配）；大尺寸永远 miss | `audio_throttle_landing.md` |
| R7 | **联机指针语义**（若有隐藏指针哈希） | 中 | MP 默认只开 L1；`OnlineSafeMode` 门控 | M-5 / §3 |
| R8 | 与 LFH 双份分桶、碎片反噬 | 低 | 只池化极端高频同构尺寸，不与 LFH 争小标量 | 威胁七 |
| R9 | 尺寸错配归还错误桶 | 低 | `poolIdx` 存头，Free 按头回收 | 威胁八（已防） |

### 4.2 推荐首批（最小侵入）

**Batch-1（仅 L1，零 ABI 劫持）**
1. `VectorReuse=1`：`0x004E97B0` 非破坏性 Clear（保留 Items/Capacity，Count=0）。
2. `VectorReserve=1`：`TechnoClass+0x440/0x458` 构造期 Reserve(16)。
3. 回滚：两键置 0 重启；无堆 ABI 变化。

**Batch-2（L2 小桶）**
4. 仅 `MemPoolSmall=1`：8/12/16/24B + 8B 头 + 范围守卫 + 投毒 + CAS。
5. 验证：对齐 1000 次 100% 8B 对齐；双释放拒绝；U800 3×15min `except.txt` 零新增；INI 热切被拒。

**Batch-3（L2 实体桶）**
6. `MemPoolEntities=1`：312/352/456B；观察粒子/弹丸/动画 churn 遥测。
7. 联机保持关闭，直至 ExtraSyncInfo 对拍通过。

### 4.3 验证门槛（合入前）

| 步 | 手段 | Pass |
| :---: | :--- | :--- |
| 1 | 对齐单测 1000 次 | `((uintptr_t)ptr & 7)==0` 100% |
| 2 | 双释放免疫 | 第二次 Free 早退，链表无环 |
| 3 | U800 满载 3 局 ×≥15min | `poolAllocs≈poolFrees`；`except.txt` 零新增 |
| 4 | 热切换拒绝 | 日志「启动锁定项」；不出现 `0xC0000374` |
| 5 | （MP）ExtraSyncInfo 对拍 | 无 OOS；有则 `OnlineSafeMode=1` |

---

## 5. 证据索引

| 文件 | 内容 |
| :--- | :--- |
| `out/re_work/re_sprint/R_crt_pool/claims.txt` | CRT ABI 字节、阈值、静态站点、尺寸直方、向量区足迹、RNG 零调用 |
| `out/re_work/re_sprint/R_crt_pool/claims_movreg.txt` | mov/lea 尺寸路径、312/352/456 样例站点、DVC 增长公式字节 |
| `out/re_work/re_sprint/R_crt_pool/site_bytes.txt` | 音频 Init / Particle / Bullet / Anim / Clear 机器码 |
| `out/re_work/re_sprint/R_crt_pool/verify_crt_abi.py` | 可复算主扫描 |
| `out/re_work/re_sprint/R_crt_pool/scan_sizes_movreg.py` | 尺寸路径补充扫描 |
| `out/re_work/re_sprint/R_crt_pool/dump_sites.py` | 关键站点字节转储 |

**禁止写入区**（本规格遵守）：`ra2render/**`、`gamemd.exe`、`ra2youli/**`、`tools/**`、`out/loadbench/**`、台账、看板、ATLAS、`out/reverse/**`。
