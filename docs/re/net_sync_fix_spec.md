# net_sync 修复 Hook Top3 实施规格（M-5）

> 派工：RE_COORDINATION.md 派工 v8 · MiMo M-5  
> 依据：`docs/re/net_sync_checksum.md` **§11 H-D1…H-D12**、§5 红线、§10 结论表、§11.3 实施约束  
> 读者：**ZCode**（落地实施方）。本文只给规格（地址 / 原字节 / 改动字节 / 跳板 / 开关 / 回滚 / 验证），**不写 C++ 源码进 `ra2render/**`**。  
> 禁区：不得改 `ra2render/**`、台账、`gamemd.exe`。本规格文件本身与 `out/re_work/net_sync_fix/**` 为唯一写作用域。  
> 二进制：`ra2youli/gamemd.exe`，**ImageBase = 0x400000**，`.text` 的 file offset = VA − 0x400000（PE 节表实测：`.text` VA=0x1000 / raw=0x1000）。

---

## 0. Top3 选取与 ROI

§11.2 给出 H-D1…H-D12；**文档 ROI 推荐**（RE_COORDINATION 核验 v8 / M-1 上报）为：

| 序 | ID | 目的 | 风险 | 入选理由 |
|---|---|---|---|---|
| **Top-1** | **H-D1** | desync 预测旁路日志（不改分支） | **L0** | 插入点最靠近判据本体；零语义；最早可观测 |
| **Top-2** | **H-D2** | desync 现场快照（写报告前落盘） | **L1** | 只加文件写；补齐「SYNC 报告缺现场」短板 |
| **Top-3** | **H-D5 + H-D6** | 帧 CRC 镜像 + 命令流镜像（**对拍套件**） | **L0** | §11.3-5 指定为「保序是否被破坏」的验收探针；双端对拍必须 **CRC 环 + 命令流** 同时有，故合并为一条规格 |

**明确不实施**：H-D11 / H-D12（L3，同步契约本体）。H-D3/D4/D7/D8/D9/D10 不在本批（可后续按同模板扩）。

风险分级（§11 引言）：**L0** 纯旁路遥测 · **L1** 诊断增强（只加写日志/文件）· **L2** 早停/控制流 · **L3** 触碰同步契约（禁止）。

---

## 1. 全局约定（四条 Hook 共用）

### 1.1 关键符号 / 内存（只读引用，禁止写游戏对象）

| 符号 | 地址 | 说明 |
|---|---|---|
| `CurrentFrame` | `0xA8ED84` | 逻辑帧号 |
| `CurrentFrameCRC` | `0xAC51FC` | 本帧 CRC（`0x64DAB0` 产出） |
| `LatestFramesCRC[256]` | `0xB04474` | 帧 CRC 环，下标 `idx & 0xFF` |
| `Queue` ring 基址 | `0x8B4204` | 0x4000 × **111B**（`index & 0x3FFF`） |
| `Queue` 计数 / 读游标 | `0x8B41F8` / `0x8B41FC` | |
| `ExtraSyncInfo` | `0xB04880` | Extra 报告开关（原版逻辑，勿动） |
| `Random` 状态对象 | `*(0xA8B230)+0x218` | **只许读指针值，禁止调用 `Random()`** |
| 阈值 `0xA8E30C` | 宽限 | **L3 禁改**（§7.3 写入者未明） |

### 1.2 `NetworkEvent` 布局（111 = 0x6F B，`#pragma pack(1)`）

| 偏移 | 类型 | 字段 |
|---|---|---|
| +0 | u8 | `Kind` |
| +1 | u8 | `Unused`（bit0 = 已执行标志） |
| +2 | i8 | `HouseIndex` |
| +3 | u32 | `Timestamp`（排序键 = 逻辑帧号） |
| +7 | u32 | `Checksum`（FrameInfo 专用 = 发送方帧 CRC） |
| +0xB | u16 | `CommandCount` |
| +0xD | u8 | `Delay` |
| +0xE | u8[0x61] | `ExtraData` |

事件指针换算（`0x64C380` 内统一形态）：

```
slot  = (QueueReadCursor@0x8B41FC + loop_index) & 0x3FFF
scale = slot * 37                    ; lea edx,[eax+eax*8] ; lea eax,[eax+edx*4]
event = scale * 3 + 0x8B4204         ; = slot * 111 + 0x8B4204
```

### 1.3 跳板分配（ZCode 统一做一次）

```
// 伪码：进程内一次性
void* cave = VirtualAlloc(NULL, 0x1000, MEM_COMMIT|MEM_RESERVE, PAGE_EXECUTE_READWRITE);
// 记为 T0。槽位：
//   T0+0x00  TRAMP_HD1   (64B)
//   T0+0x40  TRAMP_HD2   (64B)
//   T0+0x80  TRAMP_HD5   (32B)
//   T0+0xC0  TRAMP_HD6   (64B)
//   T0+0x100 TRAMP_HD6B  (64B, 可选次站点)
//   T0+0x200 起为日志/快照助手例程（按需增长，仍须落在本页）
```

> **禁止**把跳板写进 gamemd 自带 `.detour` 节（VA `0xB93000`，实测 raw 含 6980 非零字节，已有宿主格式 `Dtr\0`，归属不明）。  
> rel32 公式（`E9` 五字节）：`rel32 = target − (patch_VA + 5)`，小端写入。  
> 下文「改动字节」中的 rel32 一律写成表达式；附录 A 给 `T0 = 0x01B00000` 的数值样例供对拍。

### 1.4 寄存器契约（§11.3-3）

- 插入点若在 flag 敏感处（**尤其 `0x64C6F2` 的 `jne`**），跳板必须 **`pushfd` → `pushad` … `popad` → `popfd`** 包裹，保证 `edx/esi/eflags` 与原路径一致。
- `pushad` 栈布局：`[esp+0]=EAX, +4=ECX, +8=EDX, +0xC=EBX, +0x10=ESP, +0x14=EBP, +0x18=ESI, +0x1C=EDI`；`pushfd` 先压时 flags 在 `[esp+0x20]`（**EFLAGS bit6 = ZF**）。
- 助手例程（日志/写文件）必须是 **纯旁路**：不得写游戏内存、不得调用 `Random/RandomRanged`、不得改 `Timestamp/Kind/Checksum`。

### 1.5 ini 开关（`ra2render.ini` 或实施方约定的同级 ini，节名 `[SyncDiag]`）

| 键 | 默认 | 作用 | 随动 Hook |
|---|---|---|---|
| `SyncEarlyLog` | **0** | desync 预测旁路日志 | H-D1 |
| `SyncSnapshotOnDesync` | **0** | desync 现场快照 | H-D2 |
| `SyncMirror` | **0** | 逐帧 CRC 本地镜像环 | H-D5（及 H-D7 记账，本批不装） |
| `SyncCmdMirror` | **0** | 命令流镜像 | H-D6 / H-D6b |

**默认全 0**：发行 / 联机默认不装副作用；诊断会话再开。  
**软关**（运行时读键=0 时跳板直通原指令）与 **硬关**（Remove 还原字节）都要提供——沿 v1.5.3「装了没生效 / 卸了没还原」教训，Install/Remove **必须对称**。

### 1.6 遥测字段（建议进 `ra2render.log` 既有 2s 节流块，或独立 `sync_diag.log`）

| 字段 | 含义 |
|---|---|
| `syncEarlyLogCount` | H-D1 实际落盘条数 |
| `syncSnapshotsWritten` | H-D2 成功快照份数 |
| `syncSnapshotFail` | H-D2 写失败次数（仍进原流程） |
| `syncMirrorFrames` | H-D5 镜像帧数 |
| `syncCmdMirrorCount` | H-D6/H-D6b 命令镜像条数 |

### 1.7 红线摘要（§5 / §10 / §11.3，违反即 L3）

1. **禁止**改 `0x64DAB0` 混合式 / 量化 ÷10 / `0x650A90` 抽样次数 / `0x64C6E2` 比较宽度（H-D11）。  
2. **禁止**在 `0x4C6CB0` handler 内「本地先执行、远端后补」（H-D12）。  
3. **禁止**改命令执行序 / `Timestamp` 语义 / RNG 消费次数（§5.1、§10 #14–16）。  
4. **禁止**写任何可序列化游戏字段（只许独立缓冲 / 文件）。  
5. **禁止**占用 `SYNC%01d.TXT` / `SYNC%01d_%03d.TXT` 文件名。  
6. Hook 地址落地前过 `docs/re/HOOK_POINT_MATRIX.md`（Q2）冲突核对。

---

## 2. Top-1 · H-D1 — desync 预测旁路日志（L0）

### 2.1 Hook 地址 / 插入点

| 项 | 值 |
|---|---|
| **VA（插入点）** | **`0x64C6F2`**（`jne 0x64CC61` 整条指令，6 字节） |
| File offset | `0x24C6F2` |
| 所属 | `0x64C380` 尾部 FrameInfo 校验路径（§11.1 desync 判据） |
| 前置指令 | `0x64C6E2 mov edx,[esi*4+0xB04474]`（local）<br>`0x64C6E9 mov esi,[eax+eax*2+0x8B420B]`（remote = `event.Checksum`）<br>`0x64C6F0 cmp edx,esi` |
| 后继 | `0x64C6F8 jmp 0x64CAA8`（相等路径） / `0x64CC61`（DESYNC） |

### 2.2 原字节（gamemd.exe 实测，ImageBase=0x400000）

| VA | hex | 指令 |
|---|---|---|
| `0x64C6E2` | `8B 14 B5 74 44 B0 00` | `mov edx, dword ptr [esi*4+0xB04474]` |
| `0x64C6E9` | `8B B4 40 0B 42 8B 00` | `mov esi, dword ptr [eax+eax*2+0x8B420B]` |
| `0x64C6F0` | `3B D6` | `cmp edx, esi` |
| **`0x64C6F2`** | **`0F 85 69 05 00 00`** | **`jne 0x64CC61`**（rel32=+0x569，目标已复核） |
| `0x64C6F8` | `E9 AB 03 00 00` | `jmp 0x64CAA8` |

### 2.3 改动字节（E9 跳板 + NOP）

| VA | 改后 hex | 说明 |
|---|---|---|
| `0x64C6F2` | `E9 rel32_HD1 90` | `jmp TRAMP_HD1`；第 6 字节填 `NOP`（原 6 字节槽） |

```
rel32_HD1 = TRAMP_HD1 − (0x64C6F2 + 5) = TRAMP_HD1 − 0x64C6F7
```

### 2.4 跳板 / 原指令副本 / 回跳

```
TRAMP_HD1:                          ; 入口时 flags 仍为 cmp edx,esi 的结果（jmp 不改 flags）
    pushfd
    pushad
    cmp  dword ptr [g_SyncEarlyLog], 0
    je   .restore
    test byte ptr [esp+0x20+4], 0x40   ; [esp+0x20]=EFLAGS；bit6=ZF
    jnz  .restore                       ; ZF=1（相等）→ 非 desync，不记
    ; —— 重算 idx 与 event ——（eax/edx/esi 取自 pushad 副本）
    ;   eax_slot_scale = [esp+0]          ; = slot*37
    ;   local_crc      = [esp+8]          ; edx
    ;   remote_crc     = [esp+0x18]       ; esi
    ;   event          = eax_slot_scale*3 + 0x8B4204
    ;   idx            = (event.Timestamp@+3 − event.Delay@+0xD) & 0xFF
    ;   log("DESYNC_PREDICT frame=%u idx=%u local=%08x remote=%08x house=%d ts=%u delay=%u",
    ;       [0xA8ED84], idx, local_crc, remote_crc,
    ;       (int8)event.HouseIndex@+2, event.Timestamp@+3, event.Delay@+0xD)
    ;   inc [g_syncEarlyLogCount]
.restore:
    popad
    popfd
    ; —— 原指令副本（rel32 重定位到本跳板内）——
    jne  0x64CC61                   ; 0F 85 rel32'，rel32' = 0x64CC61 − (TRAMP_HD1_jne + 6)
    jmp  0x64C6F8                   ; 相等路径回跳（原 fallthrough）
```

| 项 | 值 |
|---|---|
| 原指令副本 | `0F 85 69 05 00 00`（语义不变；编码重定位） |
| 回跳地址（相等） | **`0x64C6F8`** |
| 跳转目标（不等） | **`0x64CC61`**（与原 jne 相同） |

### 2.5 开关 / 遥测 / 回滚

| 项 | 值 |
|---|---|
| ini | `[SyncDiag] SyncEarlyLog=0/1`，默认 **0** |
| 遥测 | `syncEarlyLogCount` |
| 日志格式 | `DESYNC_PREDICT frame=%u idx=%u local=%08x remote=%08x house=%d ts=%u delay=%u` |
| **Remove** | 把 `0x64C6F2` 还原为 `0F 85 69 05 00 00`；释放/废弃 `TRAMP_HD1`；键置 0 |

### 2.6 验证方法（同步契约不变）

| # | 方法 | 通过判据 |
|---|---|---|
| V1.1 | 字节 A/B | Install 后 dump `0x64C6F2` 为 `E9 .. 90`；Remove 后 **逐字节等于** §2.2 原字节 |
| V1.2 | 单机同种子 | 同地图/种子跑 ≥500 帧：`SyncEarlyLog` 关 vs 开，**逐帧 `CurrentFrameCRC@0xAC51FC` 序列完全一致** |
| V1.3 | 帧 CRC 不变 | 对 `0x64DAB0` 做调用计数（H-D4 思路，或断点计数）：开/关 **次数相同**；函数内 `0x650A90` 调用次数 **恰好 1 次/帧** |
| V1.4 | L0 强判据 | **A 端开 / B 端关** 双人联机 ≥300 帧：**不产生 `SYNC*.TXT`、不弹 `TXT_OUT_OF_SYNC`** → 证明零语义 |
| V1.5 | 可观测性 | 人工制造一次 CRC 不一致（仅测试镜像，例如临时改远端字节）：H-D1 必打出 1 条 `DESYNC_PREDICT`，且随后仍进原 DESYNC 流程 |
| V1.6 | 寄存器契约 | 在 `0x64C6F2` 后设硬件断点：开钩前后 `edx/esi/eflags` 与未装钩基线一致 |

**单机**：`0x647260` 在 `0xA8D5F8` bit2/4 早退（§7.10），单机可关 `SyncEarlyLog`，避免无意义日志（§11.3-6）。  
**联机**：V1.4 必测；再测 A/B 同开：日志条数在两端应一致（同为 0 或同为 N）。

### 2.7 风险与禁止

- **风险：L0**（纯旁路；唯一触碰点是指令槽 6 字节）。
- 禁止：改 `cmp/jne` 语义；跳板内写游戏内存；把 `edx/esi` 留脏；在 ZF=1 时也刷屏日志（性能与噪声）。
- 与矩阵关系：`0x64C380` 在 HOOK_POINT_MATRIX 标「严禁拦截改写」——本 Hook **不改函数控制流/数据流**，只在分支指令前加旁路日志且分支目标不变；落地备注里写明「只读探针，非拦截改写」。

---

## 3. Top-2 · H-D2 — desync 现场快照（L1）

### 3.1 Hook 地址 / 插入点

| 项 | 值 |
|---|---|
| **VA（插入点）** | **`0x64CC61`**（DESYNC 处理器入口） |
| File offset | `0x24CC61` |
| 后继 | `0x64CC66 test al,al` → Extra 分支 / `0x64CCA3` 写 `SYNC%01d.TXT`（`0x64DEA0`）或 Extra 循环 `0x6516F0` |

### 3.2 原字节（实测）

| VA | hex | 指令 |
|---|---|---|
| **`0x64CC61`** | **`A0 80 48 B0 00`** | **`mov al, byte ptr [0xB04880]`**（ExtraSyncInfo） |
| `0x64CC66` | `84 C0` | `test al, al` |
| `0x64CC68` | `74 39` | `je 0x64CCA3` |
| `0x64CCA3` | （省略） | 进 `0x64DEA0` 写 SYNC 报告 |

### 3.3 改动字节

| VA | 改后 hex | 说明 |
|---|---|---|
| `0x64CC61` | `E9 rel32_HD2` | 5 字节整条替换（正好覆盖 `mov al,[imm32]`） |

```
rel32_HD2 = TRAMP_HD2 − (0x64CC61 + 5) = TRAMP_HD2 − 0x64CC66
```

### 3.4 跳板 / 原指令副本 / 回跳

> 入口寄存器契约：与 `0x64C6F2` 处 **同一现场**（`jne` 直达，无中间指令）：
> `eax` = slot×37、`edx` = local CRC、`esi` = remote CRC；`event = eax*3 + 0x8B4204`。  
> 首条原指令 `mov al,[0xB04880]` 会破坏 `eax` 低字节 → **快照必须在原指令之前做完**（已在跳板顺序中保证）。

```
TRAMP_HD2:
    pushfd
    pushad
    cmp  dword ptr [g_SyncSnapshotOnDesync], 0
    je   .restore
    ; dump_minimal_sync_state() —— 失败只计数并跳过，绝不改控制流
    ;   文件名：SYNC_SNAP_%u.bin   %u = CurrentFrame@0xA8ED84   （禁止 SYNC%01d.TXT）
    ;   内容（小端）：
    ;     magic  "SNAP" (4B) + version u32=1
    ;     CurrentFrame            u32 @0xA8ED84
    ;     CurrentFrameCRC         u32 @0xAC51FC
    ;     LatestFramesCRC[256]    256×u32 @0xB04474
    ;     Random_StatePtr         u32 = *(u32*)0xA8B230 + 0x218   （只存指针，不抽随机）
    ;     Queue_Count             u32 @0x8B41F8
    ;     Queue_Cursor            u32 @0x8B41FC
    ;     event_raw               111B hex/bin（event = eax*3+0x8B4204，取自 pushad 副本）
    ;     local_crc / remote_crc  2×u32（edx / esi 副本）
    ;   inc [g_syncSnapshotsWritten] 或失败 inc [g_syncSnapshotFail]
.restore:
    popad
    popfd
    ; —— 原指令副本 ——
    mov  al, byte ptr [0xB04880]
    jmp  0x64CC66                   ; 回跳
```

| 项 | 值 |
|---|---|
| 原指令副本 | `A0 80 48 B0 00` |
| 回跳地址 | **`0x64CC66`** |

### 3.5 开关 / 遥测 / 回滚

| 项 | 值 |
|---|---|
| ini | `[SyncDiag] SyncSnapshotOnDesync=0/1`，默认 **0** |
| 遥测 | `syncSnapshotsWritten` / `syncSnapshotFail` |
| **Remove** | `0x64CC61` 还原 `A0 80 48 B0 00`；废弃 `TRAMP_HD2`；键置 0 |

### 3.6 验证方法

| # | 方法 | 通过判据 |
|---|---|---|
| V2.1 | 字节 A/B | Install/Remove 后与 §3.2 原字节一致 |
| V2.2 | 契约 | 同 V1.2/V1.3/V1.4：**帧 CRC 序列不变、Checksum 不变、A 开 B 关不 desync** |
| V2.3 | 快照只增不改 | 触发 desync：先出 `SYNC_SNAP_<frame>.bin`，随后 **仍** 生成原版 `SYNC*.TXT` 与 UI 弹窗（H-D10 不在本批，弹窗不得跳过） |
| V2.4 | 文件名隔离 | 目录内 **不得** 出现快照占用 `SYNC0.TXT` 等原名 |
| V2.5 | 失败安全 | 只读目录/磁盘满时：`syncSnapshotFail+1`，游戏仍进 `0x64CC66` 原流程 |
| V2.6 | 内容自洽 | 快照中 `event.Checksum`（+7）== 记录的 `remote_crc`；`idx = (ts−delay)&0xFF` 时 `LatestFramesCRC[idx]==local_crc` |

**单机**：可关（无对端，快照意义有限）。  
**联机**：诊断局开 A+B；正式局保持 0。

### 3.7 风险与禁止

- **风险：L1**（只加文件写）。
- 禁止：写游戏内存；抽 `Random()`；改 `0xB04880` 分支；跳过 `0x64DEA0`/`0x6516F0` 报告；用墙钟做文件名主键（用 `CurrentFrame`）。
- 失败路径必须 **静默跳过**，不得 SEH 泄漏到原逻辑外。

---

## 4. Top-3 · H-D5 + H-D6 — 帧 CRC 镜像 + 命令流镜像（对拍套件，L0）

> 拆开是两条旁路探针；**合起来**才是 §11.3-5 的「保序验收探针」。同一 ini 族、同一验收脚本。

### 4.1 H-D5 · 逐帧 CRC 镜像

#### 4.1.1 Hook 地址

| 项 | 值 |
|---|---|
| 函数 | `0x64DAB0` Compute/Frame CRC（产出 `CurrentFrameCRC`） |
| **VA（插入点）** | **`0x64DE75`**（函数尾声，**最后一笔 `0xAC51FC` 写之后**，且 `0x650A90` RNG 侧信道已调完） |
| File offset | `0x24DE75` |
| 选点理由 | ① CRC 已最终确定；② 不扰动 `0x650A90` 调用次数（红线）；③ 尾声 8 字节整槽可被 5 字节 `E9` 干净替换 |

尾声前关键字节（实测，作对照）：

| VA | hex | 指令 |
|---|---|---|
| `0x64DE54` | `89 0D FC 51 AC 00` | `mov [0xAC51FC], ecx` ← **最后一次 CRC 写** |
| `0x64DE5A` | `8B 0D 84 ED A8 00` | `mov ecx, [0xA8ED84]` |
| `0x64DE70` | `E8 1B 2C 00 00` | `call 0x650A90`（RNG 侧信道，**次数禁改**） |

#### 4.1.2 原字节（插入点 8 字节）

| VA | hex | 指令 |
|---|---|---|
| **`0x64DE75`** | **`5F`** | `pop edi` |
| `0x64DE76` | `5E` | `pop esi` |
| `0x64DE77` | `5D` | `pop ebp` |
| `0x64DE78` | `5B` | `pop ebx` |
| `0x64DE79` | `83 C4 14` | `add esp, 0x14` |
| `0x64DE7C` | `C3` | `ret` |

连写：`5F 5E 5D 5B 83 C4 14 C3`

#### 4.1.3 改动字节

| VA | 改后 hex | 说明 |
|---|---|---|
| `0x64DE75` | `E9 rel32_HD5` | 5 字节 `jmp TRAMP_HD5`（覆盖 `pop edi/esi/ebp`） |
| `0x64DE7A` | `90 90 90` | 原 `83 C4 14` 三字节槽填 NOP（跳板内已还原该指令） |

```
rel32_HD5 = TRAMP_HD5 − (0x64DE75 + 5) = TRAMP_HD5 − 0x64DE7A
```

#### 4.1.4 跳板 / 原指令副本 / 回跳

```
TRAMP_HD5:
    pushfd
    pushad
    cmp  dword ptr [g_SyncMirror], 0
    je   .restore
    ; ring[CurrentFrame & 0xFF] = CurrentFrameCRC
    ;   目标缓冲 g_MirrorRing[256] —— 独立内存，绝对不许写 0xB04474
    ;   idx = [0xA8ED84] & 0xFF
    ;   g_MirrorRing[idx] = [0xAC51FC]
    ;   inc [g_syncMirrorFrames]
.restore:
    popad
    popfd
    ; —— 原指令副本（尾声 8 字节全做）——
    pop  edi
    pop  esi
    pop  ebp
    pop  ebx
    add  esp, 0x14
    ret
```

| 项 | 值 |
|---|---|
| 原指令副本 | `5F 5E 5D 5B 83 C4 14 C3` |
| 回跳地址 | **无**（以原 `ret` 收尾） |
| 镜像落盘（可选） | 跨局对拍时把 `g_MirrorRing` 与帧号导出 `SYNC_MIRROR_%u.bin`（%u=CurrentFrame 或局号）；**不进 CRC** |

### 4.2 H-D6 · 命令流镜像（主站点）

#### 4.2.1 Hook 地址

| 项 | 值 |
|---|---|
| **VA（插入点）** | **`0x64C911`**（`Timestamp==CurrentFrame` 到期后 `call 0x4C6CB0`） |
| File offset | `0x24C911` |
| 前置 | `0x64C90A lea ecx, [eax+eax*2+0x8B4204]` → **`ecx` = event 指针** |
| 后继 | `0x64C916 jmp 0x64CAA8`（本轮事件收尾） |

#### 4.2.2 原字节（实测）

| VA | hex | 指令 |
|---|---|---|
| `0x64C90A` | `8D 8C 40 04 42 8B 00` | `lea ecx, [eax+eax*2+0x8B4204]` |
| **`0x64C911`** | **`E8 9A A3 E7 FF`** | **`call 0x4C6CB0`**（rel32 已复核 → `0x4C6CB0`） |
| `0x64C916` | `E9 8D 01 00 00` | `jmp 0x64CAA8` |

#### 4.2.3 改动字节

| VA | 改后 hex | 说明 |
|---|---|---|
| `0x64C911` | `E9 rel32_HD6` | 原 `call` 改为 `jmp TRAMP_HD6`（等长 5 字节） |

```
rel32_HD6 = TRAMP_HD6 − (0x64C911 + 5) = TRAMP_HD6 − 0x64C916
```

#### 4.2.4 跳板 / 原指令副本 / 回跳

```
TRAMP_HD6:
    pushfd
    pushad
    cmp  dword ptr [g_SyncCmdMirror], 0
    je   .go
    ; ecx_saved = [esp+4]
    ; log_cmd(CurrentFrame@0xA8ED84,
    ;         kind=event.Kind@+0, house=(int8)event.HouseIndex@+2,
    ;         ts=event.Timestamp@+3, extra=event+0xE 前 16B hex)
    ; inc [g_syncCmdMirrorCount]
.go:
    popad
    popfd
    ; —— 原指令副本 ——
    call 0x4C6CB0                   ; E8 rel32''，rel32'' = 0x4C6CB0 − (TRAMP_HD6_call + 5)
    jmp  0x64CAA8                   ; 原后继
```

| 项 | 值 |
|---|---|
| 原指令副本 | `E8 9A A3 E7 FF`（语义不变，重定位） |
| 回跳地址 | **`0x64CAA8`** |
| 寄存器 | `ecx` 必须原样传入 `0x4C6CB0`（事件指针）；全程只读 event |

### 4.3 H-D6b · 命令流镜像（次站点，建议同开关一并装）

MegaMission（Kind=4/5）走二级缓冲后另一次执行：

| 项 | 值 |
|---|---|
| **VA** | **`0x64CC0A`** |
| 原字节 | `E8 A1 A0 E7 FF` = `call 0x4C6CB0`（已复核） |
| 前置 | `0x64CC03 lea ecx, [eax+eax*2+0xA83EDC]` → event 在 **`0xA83EDC` 缓冲** |
| 后继 | `0x64CC0F mov eax, [0xA83ED0]` |
| 改动 | `E9 rel32_HD6B`；跳板：同 H-D6 逻辑，`call 0x4C6CB0` 后 `jmp 0x64CC0F` |
| 原指令副本 | `E8 A1 A0 E7 FF`；回跳 **`0x64CC0F`** |

> 不装 H-D6b 时，命令镜像会缺 MegaMission 痕迹——对拍脚本须知晓该缺口，或强制成对安装。

### 4.4 开关 / 遥测 / 回滚（H-D5/H-D6 共用表）

| 项 | 值 |
|---|---|
| ini | `SyncMirror=0/1`、`SyncCmdMirror=0/1`，默认 **0** |
| 遥测 | `syncMirrorFrames` / `syncCmdMirrorCount` |
| **Remove** | `0x64DE75` 还原 `5F 5E 5D 5B 83 C4 14 C3`；`0x64C911` 还原 `E8 9A A3 E7 FF`；（若装）`0x64CC0A` 还原 `E8 A1 A0 E7 FF`；镜像缓冲只读归档后可弃 |

### 4.5 验证方法（同步契约不变 + 对拍）

| # | 方法 | 通过判据 |
|---|---|---|
| V3.1 | 字节 A/B | 三处（或两处）原字节在 Remove 后与 §4.x 实测 hex **完全一致** |
| V3.2 | 帧 CRC 不变 | 开/关 `SyncMirror`：逐帧 `CurrentFrameCRC` 序列一致；`0x64DAB0` 与内部 `0x650A90` 调用次数不变 |
| V3.3 | 不碰 `0xB04474` | 镜像开启后扫描 `g_MirrorRing` 与 `LatestFramesCRC`：**地址不同**；用调试器确认写点仅落在 DLL 私有缓冲 |
| V3.4 | 命令执行序不变 | 开/关 `SyncCmdMirror`：同一局输入回放，战局结果（存档 CRC / 胜负关键事件帧）一致；镜像日志中的 `(frame, kind, house, ts)` **单调按帧、同帧按下标序** |
| V3.5 | **双端对拍（核心）** | A、B 同开 `SyncMirror+SyncCmdMirror`：对拍脚本比对 ① `g_MirrorRing` 逐帧 CRC ② 命令镜像序列 → **必须逐帧一致**。任一分叉 = 保序被破坏（§11.3-5） |
| V3.6 | L0 强判据 | A 开 / B 关 双端 ≥300 帧无 `SYNC*.TXT` |
| V3.7 | RNG 红线 | 全程 `Random()` 消费计数与基线一致（镜像函数内 **零** RNG 调用） |
| V3.8 | Checksum 不变 | 同种子单机两次（开/关）存档 `CalculateChecksum` 归因或整档哈希一致（§3.1 禁改字段） |

**单机**：可开镜像做本机环自检；命令镜像在单机 `0x647260` 早退时可能稀疏——属预期。  
**联机**：V3.5/V3.6 必测。若同步启用空间哈希/时间片（§6），**V3.5 是验收探针，不过不对齐则禁止合入**。

### 4.6 风险与禁止

- **风险：L0**（只读事件 + 写独立环）。
- 禁止：写 `0xB04474` / `event.*` / `Timestamp` / `Kind`；重排或跳过 `call 0x4C6CB0`；把镜像环与 `LatestFramesCRC` 混用；在 `0x4C6CB0` 内做任何「先本地后远端」逻辑（H-D12）。
- HOOK_POINT_MATRIX 对 `0x64C380` 的「严禁拦截改写」：H-D6 只把 **既有的** `call 0x4C6CB0` 等长改写为 `jmp→(log)→call→jmp 后继`，**调用次数、参数 `ecx`、后继地址均不变**；落地备注写明「只读命令镜像，非拦截改写」。

---

## 5. 回滚总表（Install / Remove 对称）

| Hook | Install 写入 | Remove 还原（精确 hex） | 跳板 |
|---|---|---|---|
| H-D1 | `0x64C6F2`: `E9 rel32 90` | `0F 85 69 05 00 00` | 释放 `TRAMP_HD1` |
| H-D2 | `0x64CC61`: `E9 rel32` | `A0 80 48 B0 00` | 释放 `TRAMP_HD2` |
| H-D5 | `0x64DE75`: `E9 rel32 90 90 90` | `5F 5E 5D 5B 83 C4 14 C3` | 释放 `TRAMP_HD5` |
| H-D6 | `0x64C911`: `E9 rel32` | `E8 9A A3 E7 FF` | 释放 `TRAMP_HD6` |
| H-D6b | `0x64CC0A`: `E9 rel32` | `E8 A1 A0 E7 FF` | 释放 `TRAMP_HD6B` |

规则（§11.3-2）：

1. 每条独立 ini 键；**开关关不干净 = 缺陷**（审计 A6 教训）。  
2. Remove 必须还原 **原指令字节** 并撤销 trampoline（或标记废弃且不再执行）。  
3. 卸载顺序建议：先键置 0（软关）→ 再字节还原（硬关）→ 再释放 cave。  
4. 还原后用 `out/re_work/net_sync_fix/verify_hook_bytes.py` 复验原字节。

---

## 6. 风险分级与禁止事项（汇总）

| ID | 风险 | 一句话 |
|---|---|---|
| H-D1 | **L0** | 只加预测日志，分支目标不变 |
| H-D2 | **L1** | 只加快照文件，失败旁路 |
| H-D5 | **L0** | 只写独立镜像环 |
| H-D6/H-D6b | **L0** | 只读事件并记录，call 语义不变 |
| （本批不做）H-D10 | L2 | 静默早停改交互，仅测试镜像 |
| **H-D11/H-D12** | **L3 禁止** | 碰同步契约 / 破坏锁步 |

**禁止事项（再列一遍，落地 checklist）**

- [ ] 不改 `0x64DAB0` 混合式、÷10 量化、`0x650A90` 调用次数、`0x64C6E2` 比较宽度  
- [ ] 不改 `Random` 流与消费次数；镜像/日志/快照内 **零** RNG  
- [ ] 不改命令执行序、`Timestamp` 语义；不「本地立即生效」  
- [ ] 不写可序列化游戏字段；不写 `0xB04474`（镜像必须独立）  
- [ ] 不占用 `SYNC%01d.TXT` / `SYNC%01d_%03d.TXT`（快照用 `SYNC_SNAP_%u.bin`）  
- [ ] 不把跳板写入 gamemd `.detour` 节  
- [ ] 不改 `ra2render/**`、台账、`gamemd.exe`（本任务写作用域仅本文 + `out/re_work/net_sync_fix/**`）  
- [ ] 阈值 `0xA8E30C` 不改（L3）  
- [ ] 落地前过 `HOOK_POINT_MATRIX.md` 冲突核对  

---

## 7. 验收清单（给 ZCode / 复核方）

1. `python out/re_work/net_sync_fix/verify_hook_bytes.py` → 全部 `ORIG_OK`（未装钩时）。  
2. 逐条 Install → dump 表内 VA，与「改动字节」一致。  
3. 单机同种子 A/B：帧 CRC 序列一致 + 存档哈希一致（V1.2 / V3.8）。  
4. 联机 A 开 B 关：无 `SYNC*.TXT`（V1.4 / V3.6）。  
5. 联机 A/B 同开镜像：对拍脚本 `compare_mirror.py` 输出 `MATCH`（V3.5）。  
6. Remove → 再跑 `verify_hook_bytes.py` → 全部 `RESTORED_OK`。  
7. 遥测字段非零当且仅当对应键=1 且发生了事件（避免审计 A5 死字段）。

---

## 附录 A · rel32 数值样例（`T0 = 0x01B00000`）

> 仅作编码自检；实装以 VirtualAlloc 实地址重算。

| Hook | patch VA | TRAMP | rel32 表达式 | 样例 rel32 | 样例改动字节 |
|---|---|---|---|---|---|
| H-D1 | `0x64C6F2` | `T0+0x00=0x01B00000` | `T−0x64C6F7` | `0x014B3909` | `E9 09 39 4B 01 90` |
| H-D2 | `0x64CC61` | `T0+0x40=0x01B00040` | `T−0x64CC66` | `0x014B33DA` | `E9 DA 33 4B 01` |
| H-D5 | `0x64DE75` | `T0+0x80=0x01B00080` | `T−0x64DE7A` | `0x014B2206` | `E9 06 22 4B 01 90 90 90` |
| H-D6 | `0x64C911` | `T0+0xC0=0x01B000C0` | `T−0x64C916` | `0x014B37AA` | `E9 AA 37 4B 01` |
| H-D6b | `0x64CC0A` | `T0+0x100=0x01B00100` | `T−0x64CC0F` | `0x014B34F1` | `E9 F1 34 4B 01` |

校验：`sign_extend(rel32) + (patch_VA+5) == TRAMP`。

## 附录 B · 证据来源

| 来源 | 用途 |
|---|---|
| `ra2youli/gamemd.exe` PE 节表 + 直读 hex | 全部「原字节」 |
| `out/re_work/net_sync/fn_64C380_tail.txt` | H-D1 判据 / H-D2 入口反汇编 |
| `out/re_work/net_sync/fn_64C380.txt` | H-D6 调用点 / event 寻址形态 |
| `out/re_work/net_sync/fn_64DAB0_framecrc.txt` | H-D5 尾声与 `0x650A90` 调用 |
| `docs/re/net_sync_checksum.md` §1.2/§5/§10/§11 | 布局、红线、Hook 表、实施约束 |
| `docs/re/HOOK_POINT_MATRIX.md` §2.12 | `0x64C380` 严禁拦截改写 → 本规格只读探针定位 |
| `docs/re/INSTALLED_HOOKS_AUDIT.md` §5 | Install/Remove 对称、开关关干净、遥测非死区 |
| `out/re_work/net_sync_fix/verify_hook_bytes.py` | 原字节/还原字节机读复核 |
| `out/re_work/net_sync_fix/_dump_hook_bytes.py` | 本规格 hex 的可重复提取脚本 |

## 附录 C · 伪码总装顺序（ZCode）

```
LoadConfig() → 读 [SyncDiag] 四键
if any key:
    cave = VirtualAlloc RWX 0x1000
    if SyncEarlyLog:        Install_HD1()   // 改 0x64C6F2
    if SyncSnapshotOnDesync:Install_HD2()   // 改 0x64CC61
    if SyncMirror:          Install_HD5()   // 改 0x64DE75
    if SyncCmdMirror:       Install_HD6()   // 改 0x64C911
    if SyncCmdMirror:       Install_HD6B()  // 改 0x64CC0A（建议）
Shutdown / RemoveAll():
    keys = 0
    Restore_HD6B(); Restore_HD6(); Restore_HD5(); Restore_HD2(); Restore_HD1()
    VirtualFree(cave)
    verify_hook_bytes.py → RESTORED_OK
```
