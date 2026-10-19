# net_sync 修复 Hook 字节级落地包（H-D1 / H-D2 / H-D5 / H-D6）— M-8

> **派工**：RE_COORDINATION.md 派工 v14 · MiMo · M-8  
> **读者**：**ZCode**（落地实施方）。本文是**字节级执行包**——照表写入，**不做静态推理**。  
> **基础**：`docs/re/net_sync_fix_spec.md`（规格）+ `docs/re/net_sync_checksum.md` **§11**（Hook 点表）。  
> **二进制**：`ra2youli/gamemd.exe`，**ImageBase = 0x400000**，`.text` file offset = VA − 0x400000。  
> **写作用域**：本文 + `out/re_work/landing_net_fix/**`。**禁止**改 `ra2render/**`、台账、`gamemd.exe`。  
> **机器可读编码**：`out/re_work/landing_net_fix/encodings_out.txt`（由 `calc_tramp_bytes.py` 生成，原字节已对 `gamemd.exe` 机读复核）。

**与规格版的关系**：`net_sync_fix_spec.md` 是规格（伪码/表达式）；本文把其中四条 Hook 升级为**已算好 rel32 的完整机器码**，并给出 T0≠0x01B00000 时的机械重定位表（**降为离线预备**：放弃安装是默认路径，重定位启用须三前置齐备，见附录 C）。规格中的符号约定、红线、验证思路全部继承，此处只给「能直接写进内存的字节」。

---

## 0. 一句话使用法

1. `VirtualAlloc` 固定基址 **T0 = 0x01B00000**；**分配失败 → 该项不安装**（跳过 + 红字日志 + 遥测计数），**禁止**写 `.detour` 节。附录 C 重定位**降为离线预备**，启用须三前置齐备（见附录 C 抬头）。  
2. 把附录 A 的 5 段跳板机器码原样写入 T0 槽位。  
3. 按「给 ZCode 的执行表」逐行写补丁字节、填开关/遥测/函数指针。  
4. 真机跑第 9 节验收。Remove 按 §5 精确 hex 还原。

---

## 1. 全局约定（四条 Hook 共用）

### 1.1 跳板分配（禁写 `.detour`）

```c
// 一次性。preferred-address 分配；失败 → 该项不安装（跳过 + 红字日志 + 遥测计数）
//   严禁随手换基址写死未重算 rel32 的 hex；附录 C 仅为离线预备（三前置齐备才可启用）
LPVOID cave = VirtualAlloc((LPVOID)0x01B00000, 0x1000,
                           MEM_COMMIT | MEM_RESERVE,
                           PAGE_EXECUTE_READWRITE);
// cave == 0x01B00000 即本文全部 hex 直接可用
```

**禁止**把跳板写进 gamemd 自带 `.detour` 节（VA `0xB93000`，raw 含 6980 非零字节，宿主格式 `Dtr\0`，归属不明）。

### 1.2 Cave 布局（T0 = 0x01B00000）

| 偏移 | 绝对地址 | 内容 | 宽度 |
|---|---|---|---|
| `+0x000` | `0x01B00000` | **TRAMP_HD1** | 64B 槽（实用 42B） |
| `+0x040` | `0x01B00040` | **TRAMP_HD2** | 64B 槽（实用 34B） |
| `+0x080` | `0x01B00080` | **TRAMP_HD5** | 64B 槽（实用 48B） |
| `+0x0C0` | `0x01B000C0` | **TRAMP_HD6** | 64B 槽（实用 34B） |
| `+0x100` | `0x01B00100` | **TRAMP_HD6B**（可选） | 64B 槽（实用 34B） |
| `+0x200` | `0x01B00200` | **NoopHelper**：单字节 `C3`（ret） | 1B |
| `+0x400` | `0x01B00400` | `g_SyncEarlyLog` | u32 |
| `+0x404` | `0x01B00404` | `g_SyncSnapshotOnDesync` | u32 |
| `+0x408` | `0x01B00408` | `g_SyncMirror` | u32 |
| `+0x40C` | `0x01B0040C` | `g_SyncCmdMirror` | u32 |
| `+0x410` | `0x01B00410` | `g_syncEarlyLogCount` | u32 |
| `+0x414` | `0x01B00414` | `g_syncSnapshotsWritten` | u32 |
| `+0x418` | `0x01B00418` | `g_syncSnapshotFail` | u32 |
| `+0x41C` | `0x01B0041C` | `g_syncMirrorFrames` | u32 |
| `+0x420` | `0x01B00420` | `g_syncCmdMirrorCount` | u32 |
| `+0x500` | `0x01B00500` | `p_HD1_Log`（函数指针） | u32 |
| `+0x504` | `0x01B00504` | `p_HD2_Snapshot`（函数指针） | u32 |
| `+0x50C` | `0x01B0050C` | `p_HD6_Log`（函数指针） | u32 |
| `+0x600` | `0x01B00600`…`0x01B009FF` | `g_MirrorRing[256]`（u32×256） | 1024B |

安装时 **先把 `p_HD*` 三槽填 `0x01B00200`（NoopHelper）**，再按需替换为真实助手；这样开关误开也不会因空指针崩溃。

### 1.3 只读符号（禁止写游戏对象）

| 符号 | 地址 | 用途 |
|---|---|---|
| `CurrentFrame` | `0xA8ED84` | 逻辑帧号 |
| `CurrentFrameCRC` | `0xAC51FC` | 本帧 CRC（`0x64DAB0` 产出） |
| `LatestFramesCRC[256]` | `0xB04474` | 帧 CRC 环（**只许读，镜像必须写独立环**） |
| `Queue` ring 基址 | `0x8B4204` | 0x4000 × 111B |
| `Queue` 计数 / 读游标 | `0x8B41F8` / `0x8B41FC` | |
| `ExtraSyncInfo` | `0xB04880` | 原版 Extra 开关（**勿动**） |
| `Random` 状态对象 | `*(0xA8B230)+0x218` | **只读指针，禁止调 `Random()`** |
| 阈值 `0xA8E30C` | 宽限 | **L3 禁改** |

### 1.4 `NetworkEvent` 布局（111 = 0x6F B，pack(1)）

| 偏移 | 类型 | 字段 |
|---|---|---|
| +0 | u8 | `Kind` |
| +1 | u8 | `Unused`（bit0 = 已执行） |
| +2 | i8 | `HouseIndex` |
| +3 | u32 | `Timestamp` |
| +7 | u32 | `Checksum`（FrameInfo = 发送方帧 CRC） |
| +0xB | u16 | `CommandCount` |
| +0xD | u8 | `Delay` |
| +0xE | u8[0x61] | `ExtraData` |

事件指针换算：`event = (slot * 111) + 0x8B4204`，`slot = (QueueReadCursor + i) & 0x3FFF`。  
`0x64C6E2` 前 `eax` = `slot * 37`（lea 形态），`event = eax * 3 + 0x8B4204`。

### 1.5 寄存器契约

- `0x64C6F2` 的 `jne` 与 `0x64CC61` 的入口：`eax` = slot×37、`edx` = local CRC、`esi` = remote CRC，**EFLAGS 为 `cmp edx,esi` 结果**。  
- 跳板一律 **`pushfd` → `pushad` … `popad` → `popfd`**；保证 `edx/esi/eflags` 与原路径一致。  
- `pushad` 栈布局：`[esp+0]=EAX, +4=ECX, +8=EDX, +0xC=EBX, +0x10=ESP, +0x14=EBP, +0x18=ESI, +0x1C=EDI`。  
- **`pushfd` 在前时 EFLAGS 在 `[esp+0x20]`（bit6 = ZF）**。  
  > **勘误（相对 `net_sync_fix_spec.md` §2.4）**：规格伪码写的是 `test byte ptr [esp+0x20+4], 0x40`，与同文 §1.4「flags 在 `[esp+0x20]`」矛盾。落地包**以 §1.4 为准**，机器码用 `F6 44 24 20 40`（`test byte [esp+0x20], 0x40`）。按规格的 `+4` 会测到 `pushad` 的 EDI，必然误判。

### 1.6 ini 开关（`[SyncDiag]`，进程级装载 / 跳板帧级判定）

| 键 | 默认 | 写入槽位 | 随动 Hook |
|---|---|---|---|
| `SyncEarlyLog` | **0** | `0x01B00400` | H-D1 |
| `SyncSnapshotOnDesync` | **0** | `0x01B00404` | H-D2 |
| `SyncMirror` | **0** | `0x01B00408` | H-D5 |
| `SyncCmdMirror` | **0** | `0x01B0040C` | H-D6 / H-D6b |

**默认全 0**。软关（键=0 跳板直通）与硬关（Remove 还原字节）都要提供；Install/Remove **必须对称**。

### 1.7 遥测字段

| 字段 | 槽位 | 含义 |
|---|---|---|
| `syncEarlyLogCount` | `0x01B00410` | H-D1 实际落盘条数 |
| `syncSnapshotsWritten` | `0x01B00414` | H-D2 成功快照份数 |
| `syncSnapshotFail` | `0x01B00418` | H-D2 写失败次数（仍进原流程） |
| `syncMirrorFrames` | `0x01B0041C` | H-D5 镜像帧数 |
| `syncCmdMirrorCount` | `0x01B00420` | H-D6/H-D6b 命令镜像条数 |

### 1.8 红线摘要（违反即 L3）

1. 不改 `0x64DAB0` 混合式 / ÷10 量化 / `0x650A90` 调用次数 / `0x64C6E2` 比较宽度。  
2. 不在 `0x4C6CB0` handler 内「本地先执行、远端后补」。  
3. 不改命令执行序 / `Timestamp` 语义 / RNG 消费次数。  
4. 不写任何可序列化游戏字段；镜像环与 `0xB04474` **地址必须不同**。  
5. 不占用 `SYNC%01d.TXT` / `SYNC%01d_%03d.TXT` 文件名（快照用 `SYNC_SNAP_%u.bin`）。  
6. 不把跳板写入 `.detour` 节。  
7. 阈值 `0xA8E30C` 不改。  
8. 落地前过 `docs/re/HOOK_POINT_MATRIX.md`（Q2）冲突核对；`0x64C380` 标「严禁拦截改写」——本包四条均为**只读探针**（见各条落地备注）。

---

## 2. H-D1 — desync 预测旁路日志（L0）

### 2.1 Hook 点

| 项 | 值 | 证据 |
|---|---|---|
| **VA** | **`0x64C6F2`** | `fn_64C380_tail.txt` |
| File offset | `0x24C6F2` | PE `.text` raw=0x1000, VA=0x1000 |
| 前置 | `0x64C6E2 mov edx,[esi*4+0xB04474]`<br>`0x64C6E9 mov esi,[eax+eax*2+0x8B420B]`<br>`0x64C6F0 cmp edx,esi` | [实证] |
| 后继 | 相等 → `0x64C6F8 jmp 0x64CAA8`；不等 → `0x64CC61` | [实证] |

### 2.2 原字节（`gamemd.exe` 实测）

| VA | hex | 指令 |
|---|---|---|
| `0x64C6E2` | `8B 14 B5 74 44 B0 00` | `mov edx, [esi*4+0xB04474]` |
| `0x64C6E9` | `8B B4 40 0B 42 8B 00` | `mov esi, [eax+eax*2+0x8B420B]` |
| `0x64C6F0` | `3B D6` | `cmp edx, esi` |
| **`0x64C6F2`** | **`0F 85 69 05 00 00`** | **`jne 0x64CC61`**（rel32=+0x569，目标已复核） |
| `0x64C6F8` | `E9 AB 03 00 00` | `jmp 0x64CAA8` |

### 2.3 改动字节（T0=0x01B00000）

| VA | 长度 | 新字节 |
|---|---|---|
| `0x64C6F2` | 6 | **`E9 09 39 4B 01 90`** |

- `E9 rel32` = `jmp 0x01B00000`，`rel32 = 0x01B00000 − 0x64C6F7 = 0x014B3909`（小端 `09 39 4B 01`）  
- 第 6 字节 `90` = NOP（原 `jne` 的最后一字节）

### 2.4 跳板完整编码（TRAMP_HD1 @ `0x01B00000`，42B）

```
; 入口：EFLAGS = cmp edx,esi 的结果（jmp 不改 flags）
;       EAX=slot×37, EDX=local CRC, ESI=remote CRC
01B00000  9C                        pushfd
01B00001  60                        pushad
01B00002  83 3D 00 04 B0 01 00      cmp  dword ptr [0x01B00400], 0   ; g_SyncEarlyLog
01B00009  74 12                     je   .restore                    ; → 0x01B0001D
01B0000B  F6 44 24 20 40            test byte ptr [esp+0x20], 0x40   ; EFLAGS.bit6=ZF
01B00010  75 0B                     jnz  .restore                    ; ZF=1 相等 → 不记
01B00012  8D 04 24                  lea  eax, [esp]                  ; &pushad_frame
01B00015  50                        push eax
01B00016  FF 15 00 05 B0 01         call dword ptr [0x01B00500]      ; p_HD1_Log
01B0001C  59                        pop  ecx
01B0001D  61                        popad                            ; .restore
01B0001E  9D                        popfd
01B0001F  0F 85 3C CC B4 FE         jne  0x64CC61                    ; 原 jne（重定位）
01B00025  E9 CE C6 B4 FE            jmp  0x64C6F8                    ; 相等路径回跳
```

**连写 hex（42B）**：

```
9C 60 83 3D 00 04 B0 01 00 74 12 F6 44 24 20 40 75 0B 8D 04 24 50 FF 15 00 05 B0 01 59 61 9D 0F 85 3C CC B4 FE E9 CE C6 B4 FE
```

| 项 | 值 |
|---|---|
| 原指令副本 | `0F 85 3C CC B4 FE`（`jne 0x64CC61`，语义不变） |
| 回跳（相等） | **`0x64C6F8`** |
| 跳转目标（不等） | **`0x64CC61`** |
| ZF 探测 | `test byte [esp+0x20], 0x40`（**不是** `esp+0x24`，见 §1.5 勘误） |

### 2.5 助手契约（`p_HD1_Log`）

```c
// __cdecl；入参 = pushad 帧指针（8×u32：EAX ECX EDX EBX ESP EBP ESI EDI）
void Sync_HD1_Log(const uint32_t* frame);
// 必须只读游戏内存，禁止写游戏对象 / 调 Random()。
// frame[0]=EAX=slot×37 → event = frame[0]*3 + 0x8B4204
// frame[2]=EDX=local CRC；frame[6]=ESI=remote CRC
// 日志格式：
//   DESYNC_PREDICT frame=%u idx=%u local=%08x remote=%08x house=%d ts=%u delay=%u
//   idx = (event.Timestamp@+3 − event.Delay@+0xD) & 0xFF
//   house=(int8)event.HouseIndex@+2
// 成功后 inc dword [0x01B00410]（g_syncEarlyLogCount）
```

### 2.6 开关 / 遥测 / 回滚

| 项 | 值 |
|---|---|
| ini | `[SyncDiag] SyncEarlyLog=0/1`，默认 **0** |
| 遥测 | `syncEarlyLogCount` @ `0x01B00410` |
| **Remove 精确 hex** | `0x64C6F2` ← **`0F 85 69 05 00 00`**；键置 0；`p_HD1_Log` 可回填 Noop；跳板废弃/释放 |

### 2.7 验证方法

| # | 方法 | 通过判据 | 标注 |
|---|---|---|---|
| V1.1 | 字节 A/B | Install 后 dump `0x64C6F2` = `E9 09 39 4B 01 90`；Remove 后逐字节 = `0F 85 69 05 00 00` | [待实测] |
| V1.2 | 帧 CRC 序列 | 同种子 ≥500 帧：开/关 **逐帧 `CurrentFrameCRC@0xAC51FC` 完全一致** | [待实测] |
| V1.3 | 调用计数 | `0x64DAB0` 开/关次数相同；内部 `0x650A90` **恰好 1 次/帧** | [待实测] |
| V1.4 | L0 强判据 | **A 开 B 关** ≥300 帧：无 `SYNC*.TXT`、不弹 `TXT_OUT_OF_SYNC` | [待实测] |
| V1.5 | 可观测 | 人为造一次 CRC 不一致（测试镜像）：打出 1 条 `DESYNC_PREDICT`，仍进原 DESYNC 流程 | [待实测] |
| V1.6 | 寄存器契约 | `0x64C6F2` 后硬件断点：开钩前后 `edx/esi/eflags` 与基线一致 | [待实测] |

落地备注（过 HOOK_POINT_MATRIX）：**只读探针，非拦截改写**——不改 `cmp/jne` 语义，分支目标不变。

---

## 3. H-D2 — desync 现场快照（L1）

### 3.1 ⚠️ 硬性约束：EAX 必须在 `mov al` 之前快照

`0x64CC61` 的原指令是 `mov al, byte ptr [0xB04880]`（`A0 80 48 B0 00`），**会破坏 EAX 低字节**。  
而入口现场 `EAX = slot×37` 是重建 `event` 指针的唯一线索。

**落地包的跳板顺序强制保证**：

```
pushfd
pushad          ; ← EAX 在这里入栈，此时还没执行任何 mov al
; ... dump 读取 pushad_frame[0]（即原始 EAX）...
popad
popfd
mov al, [0xB04880]   ; ← 原指令在快照完成之后才重放
jmp 0x64CC66
```

助手必须从 `frame[0]` 取 `slot×37`，**不得**在助手内假设 `EAX` 仍完好。  
**验收 V2.7**：在助手入口断点，`frame[0]` 低字节必须是 `slot×37` 的低字节（≠ `0xB04880` 的装载值）。

### 3.2 Hook 点

| 项 | 值 | 证据 |
|---|---|---|
| **VA** | **`0x64CC61`**（DESYNC 处理器入口） | `fn_64C380_tail.txt` |
| File offset | `0x24CC61` | |
| 后继 | `0x64CC66 test al,al` → Extra 分支 / `0x64CCA3` 写 `SYNC%01d.TXT`（`0x64DEA0`）或 Extra 循环 `0x6516F0` | [实证] |

### 3.3 原字节（实测）

| VA | hex | 指令 |
|---|---|---|
| **`0x64CC61`** | **`A0 80 48 B0 00`** | **`mov al, [0xB04880]`** |
| `0x64CC66` | `84 C0` | `test al, al` |
| `0x64CC68` | `74 39` | `je 0x64CCA3` |

### 3.4 改动字节（T0=0x01B00000）

| VA | 长度 | 新字节 |
|---|---|---|
| `0x64CC61` | 5 | **`E9 DA 33 4B 01`** |

- `rel32 = 0x01B00040 − 0x64CC66 = 0x014B33DA`

### 3.5 跳板完整编码（TRAMP_HD2 @ `0x01B00040`，34B）

```
; 入口现场同 H-D1（jne 直达）：EAX=slot×37, EDX=local, ESI=remote, EFLAGS=cmp 结果
01B00040  9C                        pushfd
01B00041  60                        pushad                    ; ★ EAX 快照点（先于任何 mov al）
01B00042  83 3D 04 04 B0 01 00      cmp  dword ptr [0x01B00404], 0   ; g_SyncSnapshotOnDesync
01B00049  74 0B                     je   .restore             ; → 0x01B00056
01B0004B  8D 04 24                  lea  eax, [esp]
01B0004E  50                        push eax
01B0004F  FF 15 04 05 B0 01         call dword ptr [0x01B00504]      ; p_HD2_Snapshot
01B00055  59                        pop  ecx
01B00056  61                        popad                     ; .restore
01B00057  9D                        popfd
01B00058  A0 80 48 B0 00            mov  al, byte ptr [0xB04880]   ; 原指令（在快照之后）
01B0005D  E9 04 CC B4 FE            jmp  0x64CC66             ; 回跳
```

**连写 hex（34B）**：

```
9C 60 83 3D 04 04 B0 01 00 74 0B 8D 04 24 50 FF 15 04 05 B0 01 59 61 9D A0 80 48 B0 00 E9 04 CC B4 FE
```

| 项 | 值 |
|---|---|
| 原指令副本 | `A0 80 48 B0 00`（在 `popad/popfd` **之后**重放） |
| 回跳地址 | **`0x64CC66`** |
| EAX 契约 | `pushad` 先于一切；助手从 `frame[0]` 读 `slot×37` |

### 3.6 助手契约（`p_HD2_Snapshot`）

```c
void Sync_HD2_Snapshot(const uint32_t* frame);  // __cdecl
// frame[0]=EAX=slot×37  ★ 必须用这个，不得依赖当前 EAX
// event = frame[0]*3 + 0x8B4204
// 文件名：SYNC_SNAP_%u.bin   %u = CurrentFrame@0xA8ED84   （禁止 SYNC%01d.TXT）
// 内容（小端）：
//   magic "SNAP" (4B) + version u32=1
//   CurrentFrame            u32 @0xA8ED84
//   CurrentFrameCRC         u32 @0xAC51FC
//   LatestFramesCRC[256]    256×u32 @0xB04474
//   Random_StatePtr         u32 = *(u32*)0xA8B230 + 0x218   （只存指针，不抽随机）
//   Queue_Count             u32 @0x8B41F8
//   Queue_Cursor            u32 @0x8B41FC
//   event_raw               111B
//   local_crc / remote_crc  2×u32（frame[2] / frame[6]）
// 成功 inc [0x01B00414]；失败 inc [0x01B00418]，静默跳过，绝不改控制流
// 失败路径必须静默（磁盘满/只读目录），不得 SEH 泄漏
```

### 3.7 开关 / 遥测 / 回滚

| 项 | 值 |
|---|---|
| ini | `[SyncDiag] SyncSnapshotOnDesync=0/1`，默认 **0** |
| 遥测 | `syncSnapshotsWritten` / `syncSnapshotFail` |
| **Remove 精确 hex** | `0x64CC61` ← **`A0 80 48 B0 00`**；键置 0；跳板废弃/释放 |

### 3.8 验证方法

| # | 方法 | 通过判据 | 标注 |
|---|---|---|---|
| V2.1 | 字节 A/B | Install=`E9 DA 33 4B 01`；Remove=`A0 80 48 B0 00` | [待实测] |
| V2.2 | 契约 | 同 V1.2/V1.3/V1.4：帧 CRC 序列不变、Checksum 不变、A 开 B 关不 desync | [待实测] |
| V2.3 | 快照只增不改 | 先出 `SYNC_SNAP_<frame>.bin`，随后**仍**生成原版 `SYNC*.TXT` 与 UI 弹窗 | [待实测] |
| V2.4 | 文件名隔离 | 目录内不得出现快照占用 `SYNC0.TXT` 等原名 | [待实测] |
| V2.5 | 失败安全 | 只读目录/磁盘满：`syncSnapshotFail+1`，游戏仍进 `0x64CC66` | [待实测] |
| V2.6 | 内容自洽 | `event.Checksum(+7)==remote_crc`；`LatestFramesCRC[(ts−delay)&0xFF]==local_crc` | [待实测] |
| **V2.7** | **EAX 快照时序** | 助手入口断点：`frame[0]` 低字节 = `slot×37` 低字节（**先于 `mov al`**） | [待实测] |

落地备注：**只加文件写，不改 `0xB04880` 分支、不跳过 `0x64DEA0`/`0x6516F0` 报告**。

---

## 4. H-D5 — 逐帧 CRC 镜像（L0，自包含）

### 4.1 Hook 点

| 项 | 值 | 证据 |
|---|---|---|
| 函数 | `0x64DAB0` Compute/Frame CRC | `fn_64DAB0_framecrc.txt` |
| **VA** | **`0x64DE75`**（函数尾声，最后一笔 `0xAC51FC` 写 **之后**，`0x650A90` RNG 侧信道 **已调完**） | [实证] |
| File offset | `0x24DE75` | |
| 选点理由 | ① CRC 已最终确定；② 不扰动 `0x650A90` 调用次数；③ 尾声 8B 可被 5B `E9` + 3B NOP 干净替换 | |

尾声前关键字节（对照，**不改**）：

| VA | hex | 指令 |
|---|---|---|
| `0x64DE54` | `89 0D FC 51 AC 00` | `mov [0xAC51FC], ecx` ← **最后一次 CRC 写** |
| `0x64DE5A` | `8B 0D 84 ED A8 00` | `mov ecx, [0xA8ED84]` |
| `0x64DE70` | `E8 1B 2C 00 00` | `call 0x650A90`（RNG 侧信道，**次数禁改**） |

### 4.2 原字节（插入点 8 字节）

| VA | hex | 指令 |
|---|---|---|
| **`0x64DE75`** | **`5F 5E 5D 5B 83 C4 14 C3`** | `pop edi/esi/ebp/ebx`；`add esp,0x14`；`ret` |

### 4.3 改动字节（T0=0x01B00000）

| VA | 长度 | 新字节 |
|---|---|---|
| `0x64DE75` | 8 | **`E9 06 22 4B 01 90 90 90`** |

- `rel32 = 0x01B00080 − 0x64DE7A = 0x014B2206`  
- 5B `jmp` 覆盖 `pop edi/esi/ebp/ebx` + `add` 首字节；3×NOP 覆盖 `add` 后两字节 + `ret`（**尾声 8 字节全在跳板内重放**）

### 4.4 跳板完整编码（TRAMP_HD5 @ `0x01B00080`，48B，**无助手、自包含**）

```
01B00080  9C                        pushfd
01B00081  60                        pushad
01B00082  83 3D 08 04 B0 01 00      cmp  dword ptr [0x01B00408], 0   ; g_SyncMirror
01B00089  74 1B                     je   .restore                    ; → 0x01B000A6
01B0008B  A1 84 ED A8 00            mov  eax, [0xA8ED84]             ; CurrentFrame
01B00090  0F B6 C0                  movzx eax, al                    ; ★ 勘误修复：原草案 83 E0 FF 为 no-op (and eax, 0xFFFFFFFF)，现修复为等长 3 字节 movzx eax, al 清零高位 (CurrentFrame & 0xFF)
01B00093  8B 15 FC 51 AC 00         mov  edx, [0xAC51FC]             ; CurrentFrameCRC
01B00099  89 14 85 00 06 B0 01      mov  [0x01B00600 + eax*4], edx  ; g_MirrorRing[idx]
01B000A0  FF 05 1C 04 B0 01         inc  dword ptr [0x01B0041C]      ; g_syncMirrorFrames
01B000A6  61                        popad                            ; .restore
01B000A7  9D                        popfd
01B000A8  5F                        pop  edi
01B000A9  5E                        pop  esi
01B000AA  5D                        pop  ebp
01B000AB  5B                        pop  ebx
01B000AC  83 C4 14                  add  esp, 0x14
01B000AF  C3                        ret
```

**连写 hex（48B，已采纳 0F B6 C0 修复）**：

```
9C 60 83 3D 08 04 B0 01 00 74 1B A1 84 ED A8 00 0F B6 C0 8B 15 FC 51 AC 00 89 14 85 00 06 B0 01 FF 05 1C 04 B0 01 61 9D 5F 5E 5D 5B 83 C4 14 C3
```

| 项 | 值 |
|---|---|
| 原指令副本 | `5F 5E 5D 5B 83 C4 14 C3`（尾声 8 字节全做） |
| 回跳地址 | **无**（以原 `ret` 收尾） |
| 镜像目标 | `g_MirrorRing[256] @ 0x01B00600` — **独立内存，绝不写 `0xB04474`** |
| 镜像落盘（可选） | 跨局对拍时由宿主导出 `SYNC_MIRROR_%u.bin`；**不进 CRC** |

### 4.5 开关 / 遥测 / 回滚

| 项 | 值 |
|---|---|
| ini | `[SyncDiag] SyncMirror=0/1`，默认 **0** |
| 遥测 | `syncMirrorFrames` @ `0x01B0041C` |
| **Remove 精确 hex** | `0x64DE75` ← **`5F 5E 5D 5B 83 C4 14 C3`**；键置 0；镜像缓冲只读归档后可弃 |

### 4.6 验证方法

| # | 方法 | 通过判据 | 标注 |
|---|---|---|---|
| V3.1 | 字节 A/B | Install=`E9 06 22 4B 01 90 90 90`；Remove=原 8B | [待实测] |
| V3.2 | 帧 CRC 不变 | 开/关 `SyncMirror`：逐帧 `CurrentFrameCRC` 序列一致；`0x64DAB0` 与 `0x650A90` 调用次数不变 | [待实测] |
| V3.3 | 不碰 `0xB04474` | `g_MirrorRing` 与 `LatestFramesCRC` **地址不同**；写点仅落在 cave | [实证]（地址表）/ [待实测]（写点） |
| V3.4 | 命令序不变 | 开/关 `SyncCmdMirror`：同输入回放，战局结果一致 | [待实测] |
| **V3.5** | **双端对拍（核心）** | A、B 同开镜像：`g_MirrorRing` 逐帧 CRC + 命令镜像序列**必须逐帧一致** | [待实测] |
| V3.6 | L0 强判据 | A 开 / B 关 ≥300 帧无 `SYNC*.TXT` | [待实测] |
| V3.7 | RNG 红线 | `Random()` 消费计数与基线一致（跳板内零 RNG） | [实证]（编码内无 RNG 调用）/ [待实测]（计数） |
| V3.8 | Checksum 不变 | 同种子开/关存档哈希一致 | [待实测] |

---

## 5. H-D6 — 命令流镜像（L0，主站点）+ H-D6b（可选次站点）

### 5.1 H-D6 主站点

| 项 | 值 | 证据 |
|---|---|---|
| **VA** | **`0x64C911`**（`Timestamp==CurrentFrame` 到期后 `call 0x4C6CB0`） | `fn_64C380_tail.txt` |
| File offset | `0x24C911` | |
| 前置 | `0x64C90A lea ecx, [eax+eax*2+0x8B4204]` → **`ecx` = event 指针** | [实证] |
| 后继 | `0x64C916 jmp 0x64CAA8` | [实证] |

**原字节**：

| VA | hex | 指令 |
|---|---|---|
| `0x64C90A` | `8D 8C 40 04 42 8B 00` | `lea ecx, [eax+eax*2+0x8B4204]` |
| **`0x64C911`** | **`E8 9A A3 E7 FF`** | **`call 0x4C6CB0`**（rel32 已复核） |
| `0x64C916` | `E9 8D 01 00 00` | `jmp 0x64CAA8` |

**改动字节**（T0=0x01B00000）：

| VA | 长度 | 新字节 |
|---|---|---|
| `0x64C911` | 5 | **`E9 AA 37 4B 01`** |

- `rel32 = 0x01B000C0 − 0x64C916 = 0x014B37AA`

### 5.2 TRAMP_HD6 @ `0x01B000C0`（34B）

```
; 入口：ECX = event 指针（lea ecx 之后）
01B000C0  9C                        pushfd
01B000C1  60                        pushad                    ; frame[1]=ECX=event*
01B000C2  83 3D 0C 04 B0 01 00      cmp  dword ptr [0x01B0040C], 0   ; g_SyncCmdMirror
01B000C9  74 0B                     je   .go                  ; → 0x01B000D6
01B000CB  8D 04 24                  lea  eax, [esp]
01B000CE  50                        push eax
01B000CF  FF 15 0C 05 B0 01         call dword ptr [0x01B0050C]      ; p_HD6_Log
01B000D5  59                        pop  ecx
01B000D6  61                        popad                     ; .go（ECX 恢复为 event*）
01B000D7  9D                        popfd
01B000D8  E8 D3 6B 9C FE            call 0x4C6CB0             ; 原 call（重定位）
01B000DD  E9 C6 C9 B4 FE            jmp  0x64CAA8             ; 原后继
```

**连写 hex（34B）**：

```
9C 60 83 3D 0C 04 B0 01 00 74 0B 8D 04 24 50 FF 15 0C 05 B0 01 59 61 9D E8 D3 6B 9C FE E9 C6 C9 B4 FE
```

| 项 | 值 |
|---|---|
| 原指令副本 | `E8 D3 6B 9C FE`（`call 0x4C6CB0`，语义不变） |
| 回跳地址 | **`0x64CAA8`** |
| 寄存器 | `ecx` 必须原样传入 `0x4C6CB0`；全程只读 event |

### 5.3 H-D6b 次站点（建议同开关一并装）

MegaMission（Kind=4/5）走 `0xA83EDC` 二级缓冲后另一次执行：

| 项 | 值 |
|---|---|
| **VA** | **`0x64CC0A`** |
| 原字节 | **`E8 A1 A0 E7 FF`** = `call 0x4C6CB0`（已复核） |
| 前置 | `0x64CC03 lea ecx, [eax+eax*2+0xA83EDC]` → event 在 **`0xA83EDC` 缓冲** |
| 后继 | `0x64CC0F mov eax, [0xA83ED0]` |
| 改动 | **`E9 F1 34 4B 01`**（rel32 = `0x01B00100 − 0x64CC0F = 0x014B34F1`） |

**TRAMP_HD6B @ `0x01B00100`（34B）**：

```
01B00100  9C                        pushfd
01B00101  60                        pushad
01B00102  83 3D 0C 04 B0 01 00      cmp  dword ptr [0x01B0040C], 0   ; 同 SyncCmdMirror
01B00109  74 0B                     je   .go
01B0010B  8D 04 24                  lea  eax, [esp]
01B0010E  50                        push eax
01B0010F  FF 15 0C 05 B0 01         call dword ptr [0x01B0050C]      ; p_HD6_Log
01B00115  59                        pop  ecx
01B00116  61                        popad
01B00117  9D                        popfd
01B00118  E8 93 6B 9C FE            call 0x4C6CB0
01B0011D  E9 ED CA B4 FE            jmp  0x64CC0F
```

**连写 hex（34B）**：

```
9C 60 83 3D 0C 04 B0 01 00 74 0B 8D 04 24 50 FF 15 0C 05 B0 01 59 61 9D E8 93 6B 9C FE E9 ED CA B4 FE
```

| 项 | 值 |
|---|---|
| 原指令副本 | `E8 93 6B 9C FE`；回跳 **`0x64CC0F`** |
| 不装 H-D6b 时 | 命令镜像会缺 MegaMission 痕迹——对拍脚本须知晓该缺口，或强制成对安装 |

### 5.4 助手契约（`p_HD6_Log`）

```c
void Sync_HD6_Log(const uint32_t* frame);  // __cdecl
// frame[1]=ECX=event 指针（H-D6：0x8B4204 环；H-D6b：0xA83EDC 缓冲）
// log_cmd(CurrentFrame@0xA8ED84,
//         kind=event.Kind@+0, house=(int8)event.HouseIndex@+2,
//         ts=event.Timestamp@+3, extra=event+0xE 前 16B hex)
// 成功 inc dword [0x01B00420]
// 只读 event；禁止改写 Timestamp/Kind/Checksum
```

### 5.5 开关 / 遥测 / 回滚（H-D5/H-D6 共用）

| 项 | 值 |
|---|---|
| ini | `SyncMirror=0/1`、`SyncCmdMirror=0/1`，默认 **0** |
| 遥测 | `syncMirrorFrames` / `syncCmdMirrorCount` |
| **Remove 精确 hex** | `0x64C911` ← **`E8 9A A3 E7 FF`**；`0x64CC0A` ← **`E8 A1 A0 E7 FF`**；键置 0 |

### 5.6 验证方法

| # | 方法 | 通过判据 | 标注 |
|---|---|---|---|
| V4.1 | 字节 A/B | Remove 后与 §5.x 原字节**完全一致** | [待实测] |
| V4.2 | 调用语义不变 | `call 0x4C6CB0` 次数、`ecx` 参数、后继地址均不变 | [实证]（跳板重放原 call）/ [待实测]（次数） |
| V4.3 | 命令执行序不变 | 开/关 `SyncCmdMirror`：同输入回放，战局结果一致；镜像日志 `(frame,kind,house,ts)` 单调按帧 | [待实测] |
| **V4.4** | **双端对拍** | A、B 同开：CRC 环 + 命令镜像逐帧一致 | [待实测] |
| V4.5 | L0 强判据 | A 开 / B 关 ≥300 帧无 `SYNC*.TXT` | [待实测] |
| V4.6 | Checksum 不变 | 同种子开/关存档哈希一致 | [待实测] |

落地备注（过 HOOK_POINT_MATRIX「`0x64C380` 严禁拦截改写」）：H-D6 **只把既有的 `call 0x4C6CB0` 等长改写为 `jmp→(log)→call→jmp 后继`**，调用次数、参数 `ecx`、后继地址均不变——**只读命令镜像，非拦截改写**。

---

## 6. 回滚总表（Install / Remove 对称）

| Hook | Install 写入 | **Remove 还原（精确 hex）** | 跳板 |
|---|---|---|---|
| H-D1 | `0x64C6F2`: `E9 09 39 4B 01 90` | **`0F 85 69 05 00 00`** | 废弃 `TRAMP_HD1` |
| H-D2 | `0x64CC61`: `E9 DA 33 4B 01` | **`A0 80 48 B0 00`** | 废弃 `TRAMP_HD2` |
| H-D5 | `0x64DE75`: `E9 06 22 4B 01 90 90 90` | **`5F 5E 5D 5B 83 C4 14 C3`** | 废弃 `TRAMP_HD5` |
| H-D6 | `0x64C911`: `E9 AA 37 4B 01` | **`E8 9A A3 E7 FF`** | 废弃 `TRAMP_HD6` |
| H-D6b | `0x64CC0A`: `E9 F1 34 4B 01` | **`E8 A1 A0 E7 FF`** | 废弃 `TRAMP_HD6B` |

规则：

1. 每条独立 ini 键；**开关关不干净 = 缺陷**。  
2. Remove 必须还原原指令字节并撤销 trampoline（或标记废弃且不再执行）。  
3. 卸载顺序：键置 0（软关）→ 字节还原（硬关）→ 释放 cave。  
4. 还原后跑 `python out/re_work/net_sync_fix/verify_hook_bytes.py` → 全部 `RESTORED_OK`。

---

## 7. 风险分级与禁止事项

| ID | 风险 | 一句话 |
|---|---|---|
| H-D1 | **L0** | 只加预测日志，分支目标不变 |
| H-D2 | **L1** | 只加快照文件，失败旁路 |
| H-D5 | **L0** | 只写独立镜像环 |
| H-D6/H-D6b | **L0** | 只读事件并记录，call 语义不变 |
| **H-D11/H-D12** | **L3 禁止** | 碰同步契约 / 破坏锁步 |

**禁止 checklist**：

- [ ] 不改 `0x64DAB0` 混合式、÷10 量化、`0x650A90` 调用次数、`0x64C6E2` 比较宽度  
- [ ] 不改 `Random` 流与消费次数；镜像/日志/快照内 **零** RNG  
- [ ] 不改命令执行序、`Timestamp` 语义；不「本地立即生效」  
- [ ] 不写可序列化游戏字段；不写 `0xB04474`（镜像必须独立）  
- [ ] 不占用 `SYNC%01d.TXT` / `SYNC%01d_%03d.TXT`  
- [ ] 不把跳板写入 `.detour` 节  
- [ ] 不改 `ra2render/**`、台账、`gamemd.exe`  
- [ ] 阈值 `0xA8E30C` 不改  
- [ ] 落地前过 `HOOK_POINT_MATRIX.md` 冲突核对  

---

## 8. 验收清单（ZCode / 复核方）

1. `python out/re_work/net_sync_fix/verify_hook_bytes.py` → 全部 `ORIG_OK`（未装钩时）[实证]  
2. 逐条 Install → dump 表内 VA = 「改动字节」[待实测]  
3. 单机同种子 A/B：帧 CRC 序列一致 + 存档哈希一致（V1.2 / V3.8）[待实测]  
4. 联机 A 开 B 关：无 `SYNC*.TXT`（V1.4 / V3.6 / V4.5）[待实测]  
5. 联机 A/B 同开镜像：对拍输出 `MATCH`（V3.5 / V4.4）[待实测]  
6. Remove → `verify_hook_bytes.py` → 全部 `RESTORED_OK` [待实测]  
7. 遥测非零当且仅当对应键=1 且发生了事件 [待实测]  
8. **V2.7 EAX 快照时序**（H-D2）[待实测]  

---

## 9. 给 ZCode 的执行表

> 照表写入，不做静态推理。`T0 = 0x01B00000`；**若分配失败（cave != T0）→ 本包四条 Hook 全部不安装**（跳过 + 红字日志 + 遥测计数），**严禁**换基址写死未重算 rel32 的 hex（附录 C 三前置齐备才可走重定位，且须先离线重算整表）。  
> 标注：**[实证]** = 已对 `gamemd.exe` / 反汇编机读复核；**[待实测]** = 须真机行为验证。

| 步骤 | 地址 | 原字节 | 新字节 | 开关 | 回滚 | 验收 | 标注 |
|---|---|---|---|---|---|---|---|
| **0. 分配 cave** | `VirtualAlloc(0x01B00000, 0x1000, RWX)` | — | 4K 页全零；`+0x200` 写 `C3` | — | `VirtualFree` | 分配成功；**失败 → 不安装**（红字日志 + 遥测计数） | [实证] |
| **1. 写 TRAMP_HD1** | `0x01B00000` | — | `9C 60 83 3D 00 04 B0 01 00 74 12 F6 44 24 20 40 75 0B 8D 04 24 50 FF 15 00 05 B0 01 59 61 9D 0F 85 3C CC B4 FE E9 CE C6 B4 FE` | `SyncEarlyLog` | 废弃 | 反汇编与 §2.4 一致 | [实证] |
| **2. 写 TRAMP_HD2** | `0x01B00040` | — | `9C 60 83 3D 04 04 B0 01 00 74 0B 8D 04 24 50 FF 15 04 05 B0 01 59 61 9D A0 80 48 B0 00 E9 04 CC B4 FE` | `SyncSnapshotOnDesync` | 废弃 | 反汇编与 §3.5 一致；**`mov al` 在 `popad` 之后** | [实证] |
| **3. 写 TRAMP_HD5** | `0x01B00080` | — | `9C 60 83 3D 08 04 B0 01 00 74 1B A1 84 ED A8 00 0F B6 C0 8B 15 FC 51 AC 00 89 14 85 00 06 B0 01 FF 05 1C 04 B0 01 61 9D 5F 5E 5D 5B 83 C4 14 C3` | `SyncMirror` | 废弃 | 反汇编与 §4.4 一致（含 0F B6 C0 修复） | [实证] |
| **4. 写 TRAMP_HD6** | `0x01B000C0` | — | `9C 60 83 3D 0C 04 B0 01 00 74 0B 8D 04 24 50 FF 15 0C 05 B0 01 59 61 9D E8 D3 6B 9C FE E9 C6 C9 B4 FE` | `SyncCmdMirror` | 废弃 | 反汇编与 §5.2 一致 | [实证] |
| **5. 写 TRAMP_HD6B** | `0x01B00100` | — | `9C 60 83 3D 0C 04 B0 01 00 74 0B 8D 04 24 50 FF 15 0C 05 B0 01 59 61 9D E8 93 6B 9C FE E9 ED CA B4 FE` | `SyncCmdMirror` | 废弃 | 反汇编与 §5.3 一致 | [实证] |
| **6. 填函数指针** | `0x01B00500/504/50C` | 0 | 各填 `0x01B00200`（Noop）或真实助手 | — | 回填 Noop | 非空 | [实证] |
| **7. 装 H-D1** | `0x64C6F2` | `0F 85 69 05 00 00` | `E9 09 39 4B 01 90` | `SyncEarlyLog=0/1` | `0F 85 69 05 00 00` | V1.1–V1.6 | [实证]字节 / [待实测]行为 |
| **8. 装 H-D2** | `0x64CC61` | `A0 80 48 B0 00` | `E9 DA 33 4B 01` | `SyncSnapshotOnDesync=0/1` | `A0 80 48 B0 00` | V2.1–V2.7（**V2.7 EAX 时序必测**） | [实证]字节 / [待实测]行为 |
| **9. 装 H-D5** | `0x64DE75` | `5F 5E 5D 5B 83 C4 14 C3` | `E9 06 22 4B 01 90 90 90` | `SyncMirror=0/1` | `5F 5E 5D 5B 83 C4 14 C3` | V3.1–V3.8 | [实证]字节 / [待实测]行为 |
| **10. 装 H-D6** | `0x64C911` | `E8 9A A3 E7 FF` | `E9 AA 37 4B 01` | `SyncCmdMirror=0/1` | `E8 9A A3 E7 FF` | V4.1–V4.6 | [实证]字节 / [待实测]行为 |
| **11. 装 H-D6b** | `0x64CC0A` | `E8 A1 A0 E7 FF` | `E9 F1 34 4B 01` | `SyncCmdMirror=0/1` | `E8 A1 A0 E7 FF` | V4.1–V4.6 | [实证]字节 / [待实测]行为 |
| **12. 装后 dump** | 5 处补丁点 | — | 与步骤 7–11「新字节」一致 | — | — | hex 逐字节比对 | [待实测] |
| **13. 单机 A/B** | — | — | — | 开/关各一次 | — | 帧 CRC 序列一致、存档哈希一致 | [待实测] |
| **14. 联机 A开B关** | — | — | — | 仅 A 开 | — | 无 `SYNC*.TXT`、无弹窗 | [待实测] |
| **15. 联机 A/B 同开镜像** | — | — | — | 双端开 | — | `g_MirrorRing` + 命令镜像逐帧 `MATCH` | [待实测] |
| **16. Remove** | 5 处补丁点 | 见步骤 7–11「新字节」 | 见「回滚」列精确 hex | 键置 0 | — | `verify_hook_bytes.py` → `RESTORED_OK` | [实证]脚本 / [待实测]还原 |

---

## 附录 A · 跳板机器码连写（拷贝即用，T0=0x01B00000）

```
TRAMP_HD1  @ 0x01B00000  (42B)
9C 60 83 3D 00 04 B0 01 00 74 12 F6 44 24 20 40 75 0B 8D 04 24 50 FF 15 00 05 B0 01 59 61 9D 0F 85 3C CC B4 FE E9 CE C6 B4 FE

TRAMP_HD2  @ 0x01B00040  (34B)
9C 60 83 3D 04 04 B0 01 00 74 0B 8D 04 24 50 FF 15 04 05 B0 01 59 61 9D A0 80 48 B0 00 E9 04 CC B4 FE

TRAMP_HD5  @ 0x01B00080  (48B)
9C 60 83 3D 08 04 B0 01 00 74 1B A1 84 ED A8 00 0F B6 C0 8B 15 FC 51 AC 00 89 14 85 00 06 B0 01 FF 05 1C 04 B0 01 61 9D 5F 5E 5D 5B 83 C4 14 C3

TRAMP_HD6  @ 0x01B000C0  (34B)
9C 60 83 3D 0C 04 B0 01 00 74 0B 8D 04 24 50 FF 15 0C 05 B0 01 59 61 9D E8 D3 6B 9C FE E9 C6 C9 B4 FE

TRAMP_HD6B @ 0x01B00100  (34B)
9C 60 83 3D 0C 04 B0 01 00 74 0B 8D 04 24 50 FF 15 0C 05 B0 01 59 61 9D E8 93 6B 9C FE E9 ED CA B4 FE

NoopHelper @ 0x01B00200  (1B)
C3
```

**补丁点连写**：

```
0x64C6F2 : E9 09 39 4B 01 90           ; H-D1
0x64CC61 : E9 DA 33 4B 01              ; H-D2
0x64DE75 : E9 06 22 4B 01 90 90 90     ; H-D5
0x64C911 : E9 AA 37 4B 01              ; H-D6
0x64CC0A : E9 F1 34 4B 01              ; H-D6b
```

## 附录 B · 内部 rel32 / rel8 清单（重定位用）

> `rel32 = target − (指令VA + 指令长度)`；小端写入。下列为 T0=0x01B00000 时的**已算值**。

| 所在 | 指令 | 指令 VA | 目标 | rel32/rel8 | 编码（LE） |
|---|---|---|---|---|---|
| HD1 跳板 | `jne` | `0x01B0001F` | `0x64CC61` | `0xFEB4CC3C` | `3C CC B4 FE` |
| HD1 跳板 | `jmp` | `0x01B00025` | `0x64C6F8` | `0xFEB4C6CE` | `CE C6 B4 FE` |
| HD2 跳板 | `jmp` | `0x01B0005D` | `0x64CC66` | `0xFEB4CC04` | `04 CC B4 FE` |
| HD6 跳板 | `call` | `0x01B000D8` | `0x4C6CB0` | `0xFE9C6BD3` | `D3 6B 9C FE` |
| HD6 跳板 | `jmp` | `0x01B000DD` | `0x64CAA8` | `0xFEB4C9C6` | `C6 C9 B4 FE` |
| HD6b 跳板 | `call` | `0x01B00118` | `0x4C6CB0` | `0xFE9C6B93` | `93 6B 9C FE` |
| HD6b 跳板 | `jmp` | `0x01B0011D` | `0x64CC0F` | `0xFEB4CAED` | `ED CA B4 FE` |
| 各跳板 | `je/jnz` rel8 | 见附录 A | `.restore` | 见编码 | 已内嵌 |
| 补丁点 | `E9` | §9 步骤 7–11 | 对应 TRAMP | 见 §9 | 已内嵌 |

## 附录 C · T0 ≠ 0x01B00000 时的机械重定位（**离线预备，非运行期回退路径**）

> **【F-07 订正 · 2026-09-26 · task-14】** 改前：本附录是「分配失败 → 换基址 → 重定位重写」的**运行期回退路径**（`:16` / `:28` / `:639` / `:644` / `:741` 全链咬合）。改后：**降为离线预备**——运行期分配失败一律「该项不安装」（跳过 + 红字日志 + 遥测计数），本附录只在**离线预排**（方案评审/预置镜像）时使用，且启用须**三前置同时满足**：
> ① **整表 rel32 重算**：第 3、5 条列出的每一条 `call`/`jmp`/`rel8`/`E9` 全部按新基址重算并回填，**不允许**只重算「看得见的那几条」；
> ② **装后 5 处 `E9` 自检**：§9 步骤 7–11 五处补丁点的实际落点逐字节比对 == 新 TRAMP 地址；
> ③ **槽可执行**：新页 `PAGE_EXECUTE_READWRITE` 且 `FlushInstructionCache` 后反汇编 == 附录 A 预期序列。
> **任一不满足 → 该项不安装**（跳过 + 红字日志 + 遥测计数），**禁止带病写入**。依据：Lead [v1.5.37] 硬要求 + `docs/re/z3_troubleshoot_net_fix_gap.md:25,37-44`（T1）`[推演]`。

1. 记 `T = VirtualAlloc` 返回值；`delta = T − 0x01B00000`。  
2. 拷贝附录 A 五段字节到 `T+0x000/040/080/0C0/100`。  
3. 按附录 B **每一条**重算 `rel32 = target − (新指令VA + len)` 并回填（`target` 是 gamemd 固定 VA，不随 T0 变）。  
4. 跳板内的绝对立即数（`83 3D` / `FF 15` / `A1` / `8B 15` / `89 14 85` / `FF 05` / `A0` 的 imm32）全部 **+= delta**。  
5. 补丁点的 5 处 `E9` rel32 同样按 `target − (patchVA+5)` 重算（`target` = 新 TRAMP 地址）。  
6. 机器可读参考：`out/re_work/landing_net_fix/calc_tramp_bytes.py`（改 `T0` 常量后重跑即可打印新 hex）。

## 附录 D · 证据来源

| 来源 | 用途 | 标注 |
|---|---|---|
| `ra2youli/gamemd.exe` PE 节表 + 直读 hex | 全部「原字节」（本包已机读复核） | [实证] |
| `out/re_work/net_sync/fn_64C380_tail.txt` | H-D1 判据 / H-D2 入口 / H-D6 调用点 | [实证] |
| `out/re_work/net_sync/fn_64DAB0_framecrc.txt` | H-D5 尾声与 `0x650A90` 调用 | [实证] |
| `docs/re/net_sync_checksum.md` §11 | Hook 表、风险分级、实施约束 | [实证] |
| `docs/re/net_sync_fix_spec.md` | 规格基础（符号/红线/验证思路） | [实证] |
| `docs/re/HOOK_POINT_MATRIX.md` §2.12 | `0x64C380` 严禁拦截改写 → 只读探针定位 | [实证] |
| `out/re_work/landing_net_fix/calc_tramp_bytes.py` | 本包全部 hex 的可重复生成脚本 | [实证] |
| `out/re_work/landing_net_fix/encodings_out.txt` | 生成输出（原字节 ORIG OK + 全编码） | [实证] |
| `out/re_work/net_sync_fix/verify_hook_bytes.py` | 原字节/还原字节机读复核 | [实证] |

## 附录 E · 伪码总装顺序（ZCode）

```
LoadConfig() → 读 [SyncDiag] 四键
if any key:
    cave = VirtualAlloc((LPVOID)0x01B00000, 0x1000, MEM_COMMIT|MEM_RESERVE, PAGE_EXECUTE_READWRITE)
    if cave != 0x01B00000:  该项不安装（跳过 + 红字日志 + 遥测计数）  // F-07：禁止带病写入
    写 NoopHelper C3 @ cave+0x200
    写五段 TRAMP（附录 A）
    p_HD1_Log / p_HD2_Snapshot / p_HD6_Log ← NoopHelper 或真实助手
    开关/遥测槽清零
    if SyncEarlyLog:         Install_HD1()   // 0x64C6F2
    if SyncSnapshotOnDesync: Install_HD2()   // 0x64CC61
    if SyncMirror:           Install_HD5()   // 0x64DE75
    if SyncCmdMirror:        Install_HD6()   // 0x64C911
    if SyncCmdMirror:        Install_HD6B()  // 0x64CC0A（建议）
Shutdown / RemoveAll():
    keys = 0
    Restore_HD6B(); Restore_HD6(); Restore_HD5(); Restore_HD2(); Restore_HD1()
    VirtualFree(cave)
    verify_hook_bytes.py → RESTORED_OK
```
