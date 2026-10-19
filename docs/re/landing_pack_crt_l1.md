# ZCode 落地卡 · CRT L1 向量降频（VectorReuse / VectorReserve）

> **卡号**：`ZC-CRT-L1` · **批次**：B4a（仅 L1）· **优先级**：P0（向量堆震荡主因；零分配器 ABI 劫持）  
> **执行方**：ZCode（真机/补丁安装唯一写者）· **起草**：MiMo（R-CRT-CARD，依据 R-CRT-POOL 静态定谳）  
> **上游**：`docs/re/crt_pool_landing.md`（L1 VectorReuse/Reserve）· 深潜 `docs/re/crt_memory_pool_deep_dive.md` · 风险 `docs/re/crt_pool_risk_review.md` · 复算 `out/re_work/re_sprint/R_crt_pool/` · 本卡工作区 `out/re_work/re_sprint/R_crt_card/`  
> **格式对齐**：`docs/re/landing_pack_gap_p21.md`（ZC-GAP-P21）  
> **本卡范围**：**仅 L1 `0x4E97B0` 族** + 寻敌双 Clear 窗 Reserve。键 **只有** `VectorReuse` / `VectorReserve`。  
> **禁碰**：L2（`CRT::_new@0x007C8E17` / `CRT::_delete@0x007C8B3D` / `MemPoolSmall` / `MemPoolEntities` / `MemPoolClass34`）**一律不装钩、不改字节**。`VectorGeometric` **本卡不做**。  
> **证据基线**：`gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · MD5 `4f37486e…` · ImageBase `0x00400000` · `file_off = VA − 0x00400000`
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]

---

## 0. 一句话

在 `0x4E97B0` 族两处 `Clear`（`VectorClass::Clear@0x004E97B0` / `DynamicVectorClass::Clear@0x004E9A10`）装非破坏复用跳板（`VectorReuse=1`：DVC 置 `Count=0` 保留 `Items/Capacity`，析构才 `_delete`）；在 `Greatest_Threat` 双 Clear 窗 `0x006F8F8A` 装 Reserve 跳板（`VectorReserve=1`：`TechnoClass+0x458/+0x440` 首次 `SetCapacity(16)`）。总闸 `[MemoryPool] EnableMemoryPool` **启动期锁定**；默认全关 = 字节零变化；**不碰任何 L2 入口**。
> 【W3 勘误 · W3-A6/ISSUE-SECTION-MEMORYPOOL】[W3-Lead临时裁决] 改前：[MemoryPool] EnableMemoryPool；改后：[System] ; DC-01 裁决口径: 使用既有 [System] 节，零新增节 EnableMemoryPool=0；依据：docs/re/dispatch/W3_20261001_Lead_DECISION_AND_BOARD.md:40; docs/re/pending_execution_master_table.md:410-412；分级：P0

---

## 1. 执行表（字节级 + 插入方式）

### 1.1 三钩一览

| 项 | **A1 主钩（DVC Clear）** | **A2 族钩（Base Clear）** | **B 主钩（Reserve 窗）** |
|---|---|---|---|
| **步骤 ID** | `CLR-DVC` | `CLR-BASE` | `RSV-GT` |
| **函数** | `DynamicVectorClass::Clear` | `VectorClass::Clear` | `TechnoClass::Greatest_Threat` 内 DistributedFire 清窗 |
| **VA** | `0x004E9A10` | `0x004E97B0` | `0x006F8F8A` |
| **文件偏移** | `0x000E9A10` | `0x000E97B0` | `0x002F8F8A` |
| **节** | `.text` | `.text` | `.text` |
| **覆盖长度** | **6** | **6** | **6** |
| **原字节（6B）** | `53 56 8B F1 33 DB` | `53 56 8B F1 33 DB` | `8B 96 58 04 00 00` |
| **原指令** | `push ebx; push esi; mov esi,ecx; xor ebx,ebx` | 同左 | `mov edx,[esi+0x458]` |
| **本体全长** | 39B + `90`（`…5E 5B C3`） | 同左 | 窗 `0x6F8F8A..0x6F8FA7` 共 30B |
| **ABI** | `__thiscall`：`ECX=vec*`；**无栈参**；`ret` | 同左 | 无独立 ABI（窗内序列，见 1.3） |
| **装否** | `EnableMemoryPool=1 && VectorReuse=1` | 同左 | `EnableMemoryPool=1 && VectorReserve=1` |

**原函数全字节（A1/A2 自检，39B）**：

```
4E97B0  53 56 8B F1 33 DB 8B 46 04 3B C3 74 11 38 5E 0D 74 0C 50 E8 75 F3 2D 00
        83 C4 04 89 5E 04 88 5E 0D 89 5E 08 5E 5B C3
4E9A10  53 56 8B F1 33 DB 8B 46 04 3B C3 74 11 38 5E 0D 74 0C 50 E8 15 F1 2D 00
        83 C4 04 89 5E 04 88 5E 0D 89 5E 08 5E 5B C3
```

> 两函数同构，仅 `_delete` rel32 不同（均落在 `CRT::_delete@0x007C8B3D`）。字段：`Items=+0x04`、`Capacity=+0x08`、`IsInitialized=+0x0C`、`IsAllocated=+0x0D`、**DVC `Count=+0x10`、`CapacityIncrement=+0x14`**（Base VC 仅 16B，**无 +0x10**）。[实证]

### 1.2 跳板语义（必须严格）

| 跳板 | `VectorReuse=1` 时 | 说明 |
|---|---|---|
| **A1 `CLR-DVC`** | ① 若 `Items!=0 && IsAllocated`：**跳过** `call CRT::_delete`；② **`Count(+0x10)=0`**；③ **保留** `Items/Capacity/IsAllocated`；④ 析构器 `~VectorClass@0x004EF620` 仍按 `IsAllocated` 还堆 | **首要受益**：`0x006F8F96/0x006F8FA5` 每帧寻敌双 `Clear` |
| **A2 `CLR-BASE`** | ① 同样跳过 `_delete`、保留三元组；② **禁止写 +0x10**（Base 仅 16B，写 +0x10 踩邻接字段） | 无 `Count`，旧元素在 `Capacity` 视野内仍可见 → 见 R-2 |
| **B `RSV-GT`** | 见 1.3 | 仅对窗内两向量 Reserve |

**非破坏 Clear 为何必须补 `Count=0`**：原破坏性 `Clear` **不写 +0x10**（39B 内无该写），原版靠 `Capacity=0` 逼 `AddItem` 重建；本卡保留 `Capacity` 后若不置 `Count=0`，`AddItem@0x006C6400` 会按旧 `Count` 下标写入 → 逻辑错乱。[实证字节 + 推演]

### 1.3 `RSV-GT` 原 30B 窗（跳板内等价重放 + Reserve）

```
0x6F8F8A  8B 96 58 04 00 00     mov edx, [esi+0x458]     ; CurrentTargets vftable
0x6F8F90  8D 8E 58 04 00 00     lea ecx, [esi+0x458]     ; this
0x6F8F96  FF 52 0C              call [edx+0x0C]          ; v[3] Clear
0x6F8F99  8B 86 40 04 00 00     mov eax, [esi+0x440]     ; AttackedTargets vftable
0x6F8F9F  8D 8E 40 04 00 00     lea ecx, [esi+0x440]     ; this
0x6F8FA5  FF 50 0C              call [eax+0x0C]          ; v[3] Clear
0x6F8FA8  8B 8E 1C 01 00 00     mov ecx, [esi+0x11C]     ; ★ 回跳点（勿覆盖）
```

跳板逻辑（`VectorReserve=1`）：

1. `p1 = [esi+0x458]`；若 `[p1+0x08] < 16` → `SetCapacity(p1, 16, NULL)`。  
2. `p2 = [esi+0x440]`；若 `[p2+0x08] < 16` → `SetCapacity(p2, 16, NULL)`。  
3. 按原序执行两次虚 `Clear`（会进入 A1 非破坏语义，若已装）。  
4. `jmp 0x006F8FA8`。

`SetCapacity@0x004E9840` ABI：`__thiscall`（`ECX=vec*`），栈参 `newCapacity`、`pMem`，**`ret 8`**（callee 清 8B）。字节锚点：`lea eax,[ebp*4]@0x004E985A` = `newCapacity*4`。[实证]

**可选 B2**（同键 `VectorReserve`，默认 **0**）：进程初始化一次 `SetCapacity(0x00887888+0x2580, 128, NULL)` 空间查询桶。未做不影响 A/B 验收。

### 1.4 插入方式

| 方案 | 描述 | 评价 |
|---|---|---|
| **T. trampoline（本卡唯一）** | 6B 槽 → `E9 rel32 90`；DLL 内钩函数；放行/改语义后按 §1.2/1.3 重放；`jmp` 回 VA+6 | **必须**。可承载 INI、遥测、软关 |
| D. 虚表/IAT | Clear 为虚槽可劫持但影响所有实例且与现网 `0x6F8DF0` 9B 钩纠缠 | 否决 |
| E. 外部等长替换 | 无法表达 Count=0 / Reserve | 否决 |

- 覆盖：A1/A2 各 6B（`E9 rel32 90`）；B 6B（`E9 rel32 90`）。回跳 A1/A2 → `VA+6`；B → `0x006F8FA8`。  
- 保寄存器：`EBX/ESI/EDI/EBP`；A1 钩内写 `Count` 仅经 `ESI`（=`ECX` 入参副本）。  
- trampoline 页 `PAGE_EXECUTE_READWRITE`；卸载还原原字节 + 释放跳板。

### 1.5 与现网 `Greatest_Threat` 9B 钩的关系

| 点 | 结论 |
|---|---|
| `0x006F8DF0` 入口 9B Inline Hook（`Hook_Techno_Greatest_Threat`） | **不相交**：覆盖 `0x6F8DF0..0x6F8DF8`；本卡 B 钩在 `0x6F8F8A`（窗后 0x192） |
| 本卡 **禁止**改动 `0x6F8DF0` 钩、`TargetScanInterval`、Retention 短路 | 保持 MP 门控现状（`hook_gate_gap_table.md` #9） |

---

## 2. 安装前置（全部 PASS 才允许写）

| # | 检查 | 期望 | 失败则 |
|---|---|---|---|
| G0.1 | 目标文件 SHA-256 | `73201CC0…F67476` | **拒绝安装** |
| G0.2 | `0x4E9A10` 首 6B | `53 56 8B F1 33 DB` | 已是 `E9`：报告「已打」停手；其它：**拒绝** |
| G0.3 | `0x4E97B0` 首 6B | `53 56 8B F1 33 DB` | 同上 |
| G0.4 | `0x6F8F8A` 首 6B | `8B 96 58 04 00 00` | 同上 |
| G0.5 | 窗后 `0x6F8FA8` 首 6B | `8B 8E 1C 01 00 00` | 拒绝 |
| G0.6 | 两 Clear 全 39B | 见 §1.1 原函数全字节（允许尾部 `90` 填充） | 拒绝 |
| G0.7 | `CRT::_new@0x7C8E17` / `_delete@0x7C8B3D` 序言 | `6A 01 FF 74 24 08…` / `FF 74 24 04 E8 A2 08 00 00 59 C3` **原样** | 有任何改写 → **拒绝**（L2 红线） |
| G0.8 | 总闸 `[MemoryPool] EnableMemoryPool` | 显式 `1` 才装 L1；默认 **0=不装** | 零行为变化 |
| G0.9 | `MemPoolSmall` / `MemPoolEntities` / `MemPoolClass34` | 必须为 `0` 或缺省 | 若为 1：**拒绝**（本卡禁 L2） |

**Q1 真机首字节（安装前）**：读 `0x4E97B0` / `0x4E9A10` / `0x6F8F8A` 首字节 → 原版=未打；`E9`=已有外部补丁（**停手上报，禁止覆盖**）。

---

## 3. 开关 · 遥测

### 3.1 节名 `[MemoryPool]`（宿主 `ra2render.ini`）

```ini
[MemoryPool]
; 总闸：启动期读取一次并锁定；0=不装任何钩（默认）
EnableMemoryPool=0

; L1-A 非破坏 Clear（0x4E97B0 族）
VectorReuse=0

; L1-B Reserve（Greatest_Threat 双 Clear 窗 +0x458/+0x440 → 16）
VectorReserve=0

; （本卡不实现，键名预留勿占用）
; VectorGeometric=0
; MemPoolSmall=0
; MemPoolEntities=0
; MemPoolClass34=0
```

| 键 | 默认 | 语义 | 锁定 |
|---|---|---|---|
| `EnableMemoryPool` | **0** | 总闸；0 → 不装 A1/A2/B，字节与原版逐位相同 | **启动期单次读取，严禁局内热切** |
| `VectorReuse` | **0** | 1 → 装 A1+A2 非破坏 Clear | 同上 |
| `VectorReserve` | **0** | 1 → 装 B Reserve 窗 | 同上 |

> **键名口径**：本卡唯一采用 R-CRT-POOL 规格键名。旧文 `[System] EnableMemoryPool` 视为别名，执行方以 `[MemoryPool]` 为准（值语义一致：默认 0 + 启动期锁定）。

### 3.2 遥测（只读计数，禁热路径膨胀）

| 计数器 | 含义 |
|---|---|
| `crtL1Installed` | 位掩码：bit0=A1, bit1=A2, bit2=B |
| `clearReuseHits` | A1/A2 跳过 `_delete` 次数 |
| `reserveInjected` | B 内 `SetCapacity(16)` 注入次数 |
| `vectorAllocSkipped` | 估算：`clearReuseHits` 中原本会走 `_delete` 的部分（诊断） |

启动日志一行：`MemoryPool=off | l1-reuse | l1-reserve | l1-both`（含 `forced-off-mp` 见 §5.2）。

---

## 4. 确定性门（lockstep 安全验收）

### 4.1 为什么 L1 安全 [实证 + 推演]

| # | 事实 | 级别 |
|---|---|---|
| 1 | CRT 分配器体 `0x7C8B00..0x7D1000` 对 `Random/RandomRanged/Global` **0 调用** | [实证] `R_crt_pool/claims.txt` |
| 2 | L1 **不改**对象构造/析构顺序、虚分发、RNG 消耗次数 | [推演]（仅改缓冲何时还堆） |
| 3 | 存档 = OLE/CLSID，**无裸指针落盘** | [实证] `savegame_block_manifest.md` |
| 4 | 帧 CRC `0x64DAB0` 混合量化坐标+RNG，**非堆地址** | [实证] `net_sync_checksum.md` |
| 5 | 禁止引入 `(uintptr_t)this>>4` 一类指针哈希 | 红线（M-5） |

### 4.2 D-gate（A5 前置）

| ID | 检查 | 通过条件 |
|---|---|---|
| **D1** | 静态：L1 钩内 0 次 `Scenario::Random` / 不写 `0x64DE3F` 窗 | 装前后该窗字节一致 |
| **D2** | 静态：`0x7C8E17`/`0x7C8B3D` 序言未变 | dump 对照 G0.7 |
| **D3** | 动态：U200/U800 回放帧 CRC，`VectorReuse/Reserve=1` vs `0` vs 未打补丁 | **三者一致** |
| **D4** | 动态：对象生命周期（死亡/复活/读档）无 UAF、无 `except.txt` 新增 | 3 局 ×≥15min |

---

## 5. 验收 A1–A6（真机；ZCode 填回执）

| ID | 步骤 | 期望 | 证据要求 |
|---|---|---|---|
| **A1** | 默认配置启动（总闸 0） | 三处字节仍为原版；无崩溃；`MemoryPool=off` | 首字节/日志 |
| **A2** | `EnableMemoryPool=1` + `VectorReuse=1` 启动 | `0x4E97B0/0x4E9A10`=`E9` 跳板；`0x7C8E17/0x7C8B3D` 未变；日志 `l1-reuse` | 字节前后对照 |
| **A3** | 大规模寻敌（100+ 单位混战 ≥3min） | `clearReuseHits` 持续增长；**无**每帧 `_delete(Items)` 震荡（可对比 Enable=0 时 CRT free 计数）；无 UAF/花屏 | 遥测曲线 + `except.txt` |
| **A4** | + `VectorReserve=1` | `reserveInjected` ≥1（首场战斗）；`+0x458/+0x440` Capacity≥16 后不再注入；`0x6F8FA8` 窗未变 | 遥测 + 字节 |
| **A5** | U200/U800 回放 CRC 对拍 + 开关往返 | 帧 CRC 与未打补丁一致；`EnableMemoryPool=0` 重启后字节回原版 | `SYNC*.TXT` 空 |
| **A6** | 存 `.SAV` → 读档 → 再战 | 无崩溃；目标列表功能正常（索敌/还击） | `except.txt` 空 |

### 「没崩≠成功」——A3 强制证据

1. **复用生效**：`clearReuseHits>0` 且同场景对照 `VectorReuse=0` 时 40B 增长块 `_new(40)` 显著更高；  
2. **无逻辑漂移**：同种子回放目标选择序列与基线一致（或 D3 CRC 一致）；  
3. **析构仍还堆**：局末/换图后 RSS 不单调暴涨（防「只借不还」）。

---

## 6. 回滚 / MP

### 6.1 回滚三级

| 级别 | 操作 | 影响 |
|---|---|---|
| **L0 软关** | `EnableMemoryPool=0` **或** `VectorReuse=0`+`VectorReserve=0` + **重启进程** | 下次启动不装钩；字节逐位=原版 |
| **L1 卸钩** | 还原 6+6+6=18B 原字节（`R_crt_card/orig_bytes.bin`），释放 trampoline | 与原版等价 |
| **L2 禁区** | **禁止**回滚/修改 `0x7C8E17`/`0x7C8B3D`/SBH/`0x6F8DF0` 现网 9B 钩/`0x64DE3F` | 跨堆释放 → `0xC0000374` / 破坏 MP 门控 |

- 原字节备份**装钩前落盘**：`out/re_work/re_sprint/R_crt_card/orig_bytes.bin`（A1+A2+B 各 6B）。  
- 补丁器提供 `--uninstall-crt-l1` 仅还原上述 18B。

### 6.2 MP / 联机（R-MP-GATE 口径）

| 项 | 结论 | 依据 |
|---|---|---|
| **联机 / 混联** | **仅允许本卡 L1**（Reuse/Reserve）；L2 永远关 | `crt_pool_landing.md` §3.2 |
| **混端 DESYNC** | **SAFE**（0 同步 RNG；不改存档/帧 CRC 输入）[推演，需 A5 背书] | §4.1 |
| **是否强制 MpActive 关** | **不强制**；可选观感门：`MpActive` 时打印 `forced-off-mp` 并拒绝装（若发行要求全端字节一致） | 可选 |
| **握手字段** | **不新增** | R-MP-GATE 既定 |
| **OnlineSafeMode=1** | 仍只允许 L1（本卡范围本就 L1） | `crt_pool_landing.md` |
| **默认** | 全键 `0` —— 发行/正式联机零副作用 | 与 gap_p21 对拍基线一致 |

---

## 7. 风险（执行方必读）

| ID | 风险 | 等级 | 要求 |
|---|---|---|---|
| R-1 | 非破坏 Clear 漏写 `Count(+0x10)` → `AddItem` 下标错乱 | **高** | A1 跳板**必须** `Count=0`；A3 专测索敌 |
| R-2 | A2 Base Clear 无 Count，旧元素仍可见 | 中 | 默认装但 A/B 必测；若逻辑漂移 → 只保留 A1、A2 还原 |
| R-3 | 写 `+0x10` 踩 Base 16B 对象邻接字段 | **高** | **A2 禁止写 +0x10**（§1.2） |
| R-4 | 局内热切开关 → 状态半好半坏 | 高 | 启动期锁定；改 INI 必须重启 |
| R-5 | 误碰 L2 入口 / 外部补丁覆盖 | **高** | G0.7/G0.9/Q1；首字节 `E9` 停手 |
| R-6 | 「只借不还」内存膨胀 | 中 | 析构仍还堆；A3 第 3 条 RSS 证据 |
| R-7 | 与 `0x6F8DF0` 现网 9B 钩冲突 | 中 | 窗不相交（§1.5）；禁改该钩 |
| R-8 | Reserve 过大/全量注入 | 低 | 仅窗内两字段 + 阈值 16；B2 默认关 |
| R-9 | 把「没崩」当成功 | 高 | A3 强制遥测证据（§5） |

---

## 8. 交付回执（填完交回）

```
ZC-CRT-L1 RESULT
- build/md5(gamemd):
- install path: (ra2render trampoline | external patcher | ...)
- EnableMemoryPool / VectorReuse / VectorReserve:
- MemPoolSmall / MemPoolEntities / MemPoolClass34: (must be 0)
- G0.1–G0.9: PASS/FAIL
- Q1 first byte before @0x4E97B0 / 0x4E9A10 / 0x6F8F8A:
- bytes after (A1/A2/B):
- 0x7C8E17 / 0x7C8B3D unchanged: y/n
- 0x6F8DF0 9B hook unchanged: y/n
- D1–D4: PASS/FAIL
- A1..A6: (each PASS/FAIL + evidence path)
- clearReuseHits / reserveInjected:
- except.txt: empty|path
- rollback tested (L0/L1): y/n
- MP: (single | mp-preserved | mp-forced-off) + CRC note
```

---

## 9. 不在本卡

- **L2 全部**：`MemPoolSmall` / `MemPoolEntities` / `MemPoolClass34` / `_new`/`_delete` 钩、块头、投毒、CAS —— 另卡（B4b+）  
- **`VectorGeometric`**（`0x006C6421` 线性扩容改几何）—— 另卡  
- B2 空间查询桶 Reserve(128) —— 可选扩展，默认不做  
- `0x6F8DF0` Target Retention / 节流改造 —— 维持 R-MP-GATE  
- 台账/看板登记 —— 由 Lead 收口  

---

*依据：R-CRT-POOL `crt_pool_landing.md` §2.2/§4.2 Batch-1；`crt_memory_pool_deep_dive.md` §3.1–3.5/§4.1；本卡字节 3/3 复算 MATCH（`R_crt_card/claims.txt`）；L1 零分配器 ABI 劫持；EnableMemoryPool 默认 0 + 启动期锁定（F-02 口径）。*
