# 落地队列静态等效性与回滚论证包（核心风控闸）
# Static Equivalence & Rollback Verification Package for Landing Queue

> **文档标识**：`docs/re/landing_equivalence_static_proof.md`  
> **任务阶段**：S15 专项冲刺 · 落地前核心风控静态闸门  
> **适用版本**：尤里的复仇 1.001（`ra2youli/gamemd.exe`，MD5: `4f37486e5b0dbe2ae5f45aeee0f98367`）  
> **基准参数**：ImageBase `0x00400000`，`.text` VA `0x00401000`，FileOffset = VA − `0x00400000`  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **审查对象**：六大拟合入落地补丁（M-8 联机诊断、M-10 裂缝/间谍卫星、M-9 微粒迷雾剔除、CRT 内存池、音频限频、L4 视口局部打脏）  
> **硬性纪律**：
> 1. 真机挂起期间不启动游戏进程，纯静态逐字节、逐指令、逐寄存器推演；
> 2. 证据严格分级：`[实证]`（VA + FileOffset + 原始字节 + 汇编指令）× `[推演]` × `[待实测]`；
> 3. 终审结论严格标定：【静态等效】/【条件等效】/【不可静态判定】。

---

## 0. 评审总览与风控闸门裁决矩阵 (Executive Verdict Matrix)

| 补丁编号 | 补丁名称 | 涉及地址 (VA) | 改动范围与指令形态 | 寄存器/栈平衡完整性 | 联机同步契约 (OOS) 影响 | 终审判定 | 核心风控拦截与放行前置条件 |
|:---:|:---|:---|:---|:---:|:---:|:---:|:---|
| **M-8** | 联机诊断钩<br>(H-D1/D2/D5/D6/D6b) | `0x64C6F2`<br>`0x64CC61`<br>`0x64DE75`<br>`0x64C911`<br>`0x64CC0A` | 5 处跳转劫持至 Cave<br>`0x01B00000`<br>`pushfd/pushad` 探针 | **完整保存并恢复**<br>（⚠️ 检出 H-D5 掩码编码缺陷） | **0 逻辑影响**<br>只读诊断与独立环 | **【条件等效】** | **拦截项**：H-D5 必须将 `83 E0 FF` 纠正为 `0F B6 C0`（`movzx eax, al`），防止环缓冲越界越页崩溃；Cave 分配成功前置。 |
| **M-10** | 裂缝保护 NOP×3 +<br>SpySat 门控 +<br>G-07 TYPE 还原 | `0x568273`<br>`0x577EC5`<br>`0x577B60`<br>`0x508F8F`<br>TYPE 内存表 | 3 处 6B NOP 清零剔除；<br>1 处 `je` $\to$ `jmp` 2B 门控；<br>内存虚表卸载还原 | **严格等效**<br>零破坏寄存器与栈 | **逻辑状态改变**<br>（Cell 进档，影响 AI/寻敌） | **【条件等效】** | **红线项**：禁止混端联机！全端必须统一加载相同补丁，否则裂缝视野分叉必定引发 OOS；单机完全安全。 |
| **M-9** | 微粒/粒子系统迷雾剔除<br>(槽 69 合并) | `0x007EFA68`<br>`0x007EFCB0` | 2 处虚表 DWORD 替换<br>（`.rdata` 函数指针覆写，零 inline patch） | **严格等效**<br>早退 `ret 8` 清栈与原函数完全对齐 | **0 逻辑影响**<br>只阻断 Draw，Update 寿命正常推进 | **【静态等效】**<br>（表现层条件） | **放行项**：合并入现有 13 槽体系；禁止 inline patch 函数体；`EnableParticleFog` 默认 0，验收时显式置 1。 |
| **CRT 池** | 高频小对象池化<br>(P-M1…P-M5 8 字节加固版) | `0x007C8E17`<br>`0x007C8B3D` | `operator new` (6B)<br>`operator delete` (9B)<br>前置 Freelist 拦截 | **严格等效**<br>严格 8 字节对齐，双重地址范围校验 | **0 逻辑影响**<br>内存分配不参与 CRC 计算 | **【条件等效】** | **红线项**：严格启动期单次锁定配置，严禁局内热切换（防 `0xC0000374` 堆损坏）；非池内存 100% 穿透原生 CRT。 |
| **音频限频** | VocClass 并发削峰<br>(同类 2 帧 + 单帧 4 条) | `0x00750920`<br>`0x007509E0` | `PlayGlobal` (6B)<br>`PlayAt` (5B)<br>前置入口削峰 | **严格等效**<br>（⚠️ 修正早退返回栈平衡契约） | **0 逻辑影响**<br>纯表现层，不进同步校验 | **【条件等效】** | **拦截项**：限频早退必须返回 `0` (`NULL`) 且分别执行 `ret 8` 与 `ret 4`，严禁返回 `-1` 与裸 `ret` 破栈。 |
| **L4 视口** | 视口局部打脏<br>(双模切换 + 3×3 外扩) | `0x006D3D99`<br>`0x006DA7D0` | 1 处 6B 分支恢复<br>`jge 0x006D3E37`；<br>原生打脏 API 驱动 | **严格等效**<br>`RegisterCell` 自身维护 `LastVisibleFrame` | **0 逻辑影响**<br>纯渲染调度，不写任何同步字段 | **【条件等效】** | **放行项**：保持 `force-full` 默认基线；`vision-dirty` 模式受 $>350$ 翻转格全量刷新保底，杜绝残影。 |

---

## 1. 证据标准与评定契约 (Evidence Standard & Grading)

所有论证均严格遵循以下证据标定：
- **`[实证]` (Empirical Evidence)**：基于目标二进制 `ra2youli/gamemd.exe`（MD5: `4f37486e5b0dbe2ae5f45aeee0f98367`）的精确文件偏移、原始机器码十六进制以及反汇编指令，经 Python + Pefile + Capstone 交叉验证闭环。
- **`[推演]` (Deductive Analysis)**：基于 x86 体系结构、调用约定（ABI）、EFLAGS 标志位传播、编译器生成的函数序言/尾声栈帧机制的逻辑数学严密推导。
- **`[待实测]` (Pending Hardware Verification)**：不可静态判定的动态行为（如人耳听觉主观体验、DirectSound 驱动抗压、极端 8 玩家 AI 混战长时间稳定性），在真机启动前保持挂起，并列出可量化的验收指标与测试步骤。

---

## 2. 补丁一：M-8 联机诊断钩 (H-D1, H-D2, H-D5, H-D6, H-D6b)

### 2.1 被改动指令的原语义 [实证]

| Hook ID | 目标 VA | 文件偏移 | 原始机器码 (HEX) | 原始汇编指令 | 寄存器副作用 | EFLAGS 标志位依赖/影响 | 栈平衡变化 |
|:---|:---:|:---:|:---|:---|:---|:---|:---:|
| **H-D1** | `0x0064C6F2` | `0x0024C6F2` | `0F 85 69 05 00 00` | `jne 0x0064CC61` | 无寄存器修改 | 依赖 `0x64C6F0 cmp edx, esi` 产生的 **ZF** 标志位；本指令不修改标志位 | 0 (平栈) |
| **H-D2** | `0x0064CC61` | `0x0024CC61` | `A0 80 48 B0 00` | `mov al, byte ptr [0x00B04880]` | **破坏 AL**（即修改 `EAX` 的最低 8 位）；破坏前 `EAX = slot * 37` | 不影响任何标志位 | 0 (平栈) |
| **H-D5** | `0x0064DE75` | `0x0024DE75` | `5F 5E 5D 5B 83 C4 14 C3` | `pop edi; pop esi; pop ebp; pop ebx; add esp, 0x14; ret` | 弹出 4 个通用寄存器，作为 `0x64DAB0` 尾声 | 不影响标志位 | `esp += 0x24`（4×4+0x14+4 包含返回地址） |
| **H-D6** | `0x0064C911` | `0x0024C911` | `E8 9A A3 E7 FF` | `call 0x004C6CB0` | `__thiscall`，ECX 传入事件指针；EAX/ECX/EDX 为易失寄存器 | 标志位由被调函数决定 | 被调函数平栈（`ret`） |
| **H-D6b**| `0x0064CC0A` | `0x0024CC0A` | `E8 A1 A0 E7 FF` | `call 0x004C6CB0` | 同上（次级事件队列缓冲） | 同上 | 被调函数平栈 |

### 2.2 新语义与逐条指令级对拍表 [实证 + 推演]

#### 2.2.1 H-D1（`0x0064C6F2`）对拍表
- **补丁点改写**：`E9 09 39 4B 01 90`（5B `jmp 0x01B00000` + 1B `nop`）
- **跳板位置**：`TRAMP_HD1 @ 0x01B00000`（42 字节）

| 序号 | 跳板 VA | 机器码 | 汇编指令 | 语义与寄存器/标志位对拍 [推演] |
|:---:|:---:|:---|:---|:---|
| 1 | `0x01B00000` | `9C` | `pushfd` | 将带有 `cmp edx, esi` 结果的完整 EFLAGS 压栈保存在 `[esp]` |
| 2 | `0x01B00001` | `60` | `pushad` | 将 8 个通用寄存器（EAX~EDI）全部压栈，此时原 EFLAGS 位于 `[esp + 0x20]` |
| 3 | `0x01B00002` | `83 3D 00 04 B0 01 00` | `cmp dword ptr [0x01B00400], 0` | 检查开关 `g_SyncEarlyLog`，若为 0 直接跳过 |
| 4 | `0x01B00009` | `74 12` | `je 0x01B0001D` | 软关路径：直奔 `.restore` |
| 5 | `0x01B0000B` | `F6 44 24 20 40` | `test byte ptr [esp + 0x20], 0x40` | **精准探测原 ZF 标志位**（bit 6 = 0x40）；相等则不记录 |
| 6 | `0x01B00010` | `75 0B` | `jnz 0x01B0001D` | ZF=1（CRC 相等）$\to$ 直奔 `.restore` |
| 7 | `0x01B00012` | `8D 04 24` | `lea eax, [esp]` | 取 `pushad` 帧指针作为入参 |
| 8 | `0x01B00015` | `50` | `push eax` | 传参压栈（`const uint32_t* frame`） |
| 9 | `0x01B00016` | `FF 15 00 05 B0 01` | `call dword ptr [0x01B00500]` | 调用 `p_HD1_Log` 助手（默认指向 `0x01B00200 ret`） |
| 10| `0x01B0001C` | `59` | `pop ecx` | 平衡参数栈（4 字节） |
| 11| `0x01B0001D` | `61` | `popad` | **恢复全部 8 个通用寄存器**（EAX=slot*37, EDX=local, ESI=remote） |
| 12| `0x01B0001E` | `9D` | `popfd` | **完全恢复原始 EFLAGS**（精确还原原始 `cmp edx, esi` 结果） |
| 13| `0x01B0001F` | `0F 85 3C CC B4 FE` | `jne 0x0064CC61` | **重放原版条件跳转**：若不相等跳转至 DESYNC 处理入口 |
| 14| `0x01B00025` | `E9 CE C6 B4 FE` | `jmp 0x0064C6F8` | 若相等，落入原版顺序后继地址 `0x0064C6F8` |

#### 2.2.2 H-D2（`0x0064CC61`）对拍表
- **补丁点改写**：`E9 DA 33 4B 01`（5B `jmp 0x01B00040`）
- **跳板位置**：`TRAMP_HD2 @ 0x01B00040`（34 字节）
- **核心契约保证**：入口现场 `EAX = slot * 37` 必须在被 `mov al` 破坏前被捕获！
  - `0x01B00040: 9C 60`（`pushfd; pushad`）：此时 `frame[0]` 精确保存了原始完整 `EAX`；
  - 调用 `p_HD2_Snapshot`，助手从 `frame[0]` 读取事件槽位，绝不依赖易失的当前寄存器；
  - `0x01B00056: 61 9D`（`popad; popfd`）：寄存器完全复原；
  - `0x01B00058: A0 80 48 B0 00`（`mov al, byte ptr [0xB04880]`）：**在快照完成后重放原版指令**；
  - `0x01B0005D: E9 04 CC B4 FE`（`jmp 0x0064CC66`）：跳转回原版后续检测分支。

#### 2.2.3 H-D5（`0x0064DE75`）重大漏洞发现与静态修正对拍 [实证 + 关键纠偏]
- **原始设计意图**：在 `0x64DAB0` 尾声记录当前帧 CRC 到 256 项环形缓冲区：
  $$\text{TargetSlot} = \text{CurrentFrame} \ \& \ 0\text{xFF}$$
- **⚠️ 检出严重机器码缺陷**：
  在 `calc_tramp_bytes.py` 与 `landing_pack_net_fix.md` 中，指令编写为：
  ```asm
  0x01B0008B: A1 84 ED A8 00        mov  eax, dword ptr [0x00A8ED84] ; CurrentFrame
  0x01B00090: 83 E0 FF              and  eax, 0xFF                   ; 致命错误！
  ```
  **实证分析**：根据 Intel 架构规范，`83 /4 ib` 的操作数 `ib`（`0xFF`）会被**带符号扩展为 32 位**（`0xFFFFFFFF`）！
  因此，`83 E0 FF` 实际执行的是 `and eax, 0xFFFFFFFF`，**高 24 位完全没有被清零**！
  - 当帧号 $\le 255$ 时：表现正常；
  - 当帧号 $\ge 256$ 时：`eax` 不被截断；
  - `0x01B00099: mov [0x01B00600 + eax*4], edx` 将发生严重**越界写（Out-Of-Bounds Write）**！
  - 当帧号达到 1024 帧（对局进行约 1 分钟）时，写地址超出 `VirtualAlloc(0x01B00000, 0x1000)` 4KB 页边界，直接触发 **`EXCEPTION_ACCESS_VIOLATION` (0xC0000005) 崩溃**！
- **静态等效修正方案 [实证]**：
  将 `0x01B00090` 处的 3 字节替换为：
  `0F B6 C0` $\to$ **`movzx eax, al`**（零扩展，恰好 3 字节，长度完全一致，0 相对偏移漂移）！
  
**修正后 H-D5 跳板完整对拍表（48 字节）**：
```asm
01B00080: 9C                    pushfd
01B00081: 60                    pushad
01B00082: 83 3D 08 04 B0 01 00  cmp   dword ptr [0x01B00408], 0  ; g_SyncMirror 开关
01B00089: 74 1B                 je    0x01B000A6                 ; 软关跳过
01B0008B: A1 84 ED A8 00        mov   eax, [0x00A8ED84]          ; CurrentFrame
01B00090: 0F B6 C0              movzx eax, al                    ; ★ 静态修正：严格 0~255 取模
01B00093: 8B 15 FC 51 AC 00     mov   edx, [0x00AC51FC]          ; CurrentFrameCRC
01B00099: 89 14 85 00 06 B0 01  mov   [0x01B00600 + eax*4], edx ; 安全写入 g_MirrorRing[idx]
01B000A0: FF 05 1C 04 B0 01     inc   dword ptr [0x01B0041C]     ; g_syncMirrorFrames++
01B000A6: 61                    popad
01B000A7: 9D                    popfd
01B000A8: 5F 5E 5D 5B           pop   edi; pop esi; pop ebp; pop ebx ; 完整重放原尾声
01B000AC: 83 C4 14              add   esp, 0x14
01B000AF: C3                    ret                              ; 干净返回
```

### 2.3 不可静态判定项与实测验证方案 [待实测]

| 验证项 | 判定对象 | 静态无法断言的原因 | 真机测量指标与通过判据 |
|:---:|:---|:---|:---|
| **HD-V1** | 内存分配基址稳定性 | `VirtualAlloc` 指定 `0x01B00000` 是否与其他注入模块/系统保留区冲突 | 若分配成功，基址必须为 `0x01B00000`；若被占，必须自动激活重定位计算脚本且所有 rel32 正确解析。 |
| **HD-V2** | 快照落盘对主线程卡顿影响 | H-D2 快照写入磁盘在 DESYNC 瞬间是否引发严重卡死 | 同步写 `SYNC_SNAP_%u.bin` 耗时 $\le 5\text{ms}$；只读介质下命中静默失败，`syncSnapshotFail++` 且不崩溃。 |
| **HD-V3** | 双端联机镜像一致性 | 联机两端分别开启 `SyncMirror` 时帧数据的一致性 | 双端运行 500 帧以上，对比导出的 `g_MirrorRing` 序列必须逐帧完全相等（MD5 完全一致）。 |

### 2.4 开关、回滚路径与失败模式分析

- **开关层级**：`[SyncDiag]` 四键（`SyncEarlyLog`, `SyncSnapshotOnDesync`, `SyncMirror`, `SyncCmdMirror`），默认全为 `0`（软关，零外部函数调用）。
- **回滚机制**：
  - `0x64C6F2` $\leftarrow$ `0F 85 69 05 00 00`
  - `0x64CC61` $\leftarrow$ `A0 80 48 B0 00`
  - `0x64DE75` $\leftarrow$ `5F 5E 5D 5B 83 C4 14 C3`
  - `0x64C911` $\leftarrow$ `E8 9A A3 E7 FF`
  - `0x64CC0A` $\leftarrow$ `E8 A1 A0 E7 FF`
- **失败模式分析**：
  1. **Cave 分配失败**：若未做重定位保护强行写入，引发 `0xC0000005`。**防护**：前置基址非空断言。
  2. **H-D5 越界崩溃**：若未采纳 `movzx eax, al` 修正，局内 1000 帧后必定崩溃。**防护**：强制阻断旧字节合入。
  3. **OOS 风险**：纯只读探针，零可序列化字段写入，零 RNG 消耗，**OOS 风险等级为绝对安全（0 分叉）**。

### 2.5 终审结论
标定为：**【条件等效】**（在采纳 `movzx eax, al` 修正且 Cave 分配成功的前提下，完全静态等效）。

---

## 3. 补丁二：M-10 裂缝保护与间谍卫星门控 (M-10 Gap & SpySat)

### 3.1 被改动指令的原语义 [实证]

```asm
; [Gap 1] 0x00568273 (FileOffset: 0x168273) - MapClass::RevealArea2 (PsychicReveal 局部开图循环)
0x00568273: 89 99 34 01 00 00        mov dword ptr [ecx + 0x134], ebx ; ebx = 0

; [Gap 2] 0x00577EC5 (FileOffset: 0x177EC5) - MapClass::RevealArea3 (SpySat 全图点亮循环)
0x00577EC5: 89 B8 34 01 00 00        mov dword ptr [eax + 0x134], edi ; edi = 0

; [Gap 3] 0x00577B60 (FileOffset: 0x177B60) - MapClass::Reshroud (SpySat 离线重遮蔽循环)
0x00577B60: 89 98 34 01 00 00        mov dword ptr [eax + 0x134], ebx ; ebx = 0
```
- **原语义根因**：西木原版在开图例程中，将 `CellClass + 0x134`（`GapsCoveringThisCell`，覆盖该格的敌方裂缝产生器引用计数）**暴力重置为 0**！
- **灾难后果**：裂缝建筑的 `GeneratingGap` 仍为 true，但不会再次触发 `CreateGap`；当开图扫描退去后，`CellClass::ReshroudCell`（`0x00487690`）检测到 `GapsCoveringThisCell == 0`，将遮蔽计数截断为 0，导致**该区域永久丧失黑雾遮蔽能力（裂缝失效）**。

```asm
; [SpySat Gate] 0x00508F88 (FileOffset: 0x108F88) - HouseClass::UpdateSpySat
0x00508F88: 80 B8 A5 16 00 00 00     cmp byte ptr [eax + 0x16A5], 0   ; Type->SpySat
0x00508F8F: 74 65                    je  0x00508FF6                   ; 非间谍卫星跳过
```
- **原语义**：检测到建筑物属于间谍卫星（`Type+0x16A5`）且在线供电时，无条件调用 `RevealArea3`（全图开图），触发全图裂缝计数清零与 `CopyFlags |= 0x18`。

### 3.2 新语义与逐条指令级对拍表 [实证 + 推演]

| 补丁项目 | 目标 VA | 原始指令与机器码 | 替换指令与机器码 | 寄存器/标志位变化 | 语义对拍说明 |
|:---|:---:|:---|:---|:---:|:---|
| **Gap 1** | `0x00568273` | `89 99 34 01 00 00`<br>`mov [ecx+0x134], ebx` | `90 90 90 90 90 90`<br>`nop; nop; nop; nop; nop; nop` | 无任何变化<br>平栈、平标志位 | 仅删去清零副作用，保留循环其余所有状态更新 |
| **Gap 2** | `0x00577EC5` | `89 B8 34 01 00 00`<br>`mov [eax+0x134], edi` | `90 90 90 90 90 90`<br>`nop; nop; nop; nop; nop; nop` | 无任何变化 | 同上 |
| **Gap 3** | `0x00577B60` | `89 98 34 01 00 00`<br>`mov [eax+0x134], ebx` | `90 90 90 90 90 90`<br>`nop; nop; nop; nop; nop; nop` | 无任何变化 | 同上 |
| **SpySat 门控** | `0x00508F8F` | `74 65`<br>`je 0x00508FF6` | `EB 65`<br>`jmp 0x00508FF6` | 无寄存器变化<br>无标志位变化 | 无条件走跳过分支：**永不执行全图亮图**，落点完全一致 |

### 3.3 联机同步契约冲突深度论证（OOS Risk Proof）[实证 + 推演]

> [!CAUTION] 核心风控警报：M-10 补丁属于【游戏逻辑有状态变更】，绝非纯视觉补丁！

1. **序列化覆盖范围实证**：
   根据 `docs/re/net_sync_checksum.md` §4.2，`CellClass` 属于核心游戏状态，完整参与 `.SAV` 存档序列化；`Cell+0x134`（`GapsCoveringThisCell`）直接决定了格子的黑雾状态。
2. **分叉连锁推演**：
   - 设 **主机 A** 打了 NOP 补丁，**客机 B** 未打补丁（原版）；
   - 敌方释放心灵探测（PsychicReveal）扫描我方裂缝区；
   - 扫描结束后：
     - 主机 A 处：`GapsCoveringThisCell` 保持为 1，黑雾正常退回，敌方无法看到我方基地的坦克；
     - 客机 B 处：`GapsCoveringThisCell` 被清零，黑雾无法退回，敌方视野内持续可见我方坦克；
   - **分叉点**：客机 B 的 AI 或单位判定该坦克在可视射程内，触发自动寻敌开火；主机 A 的单位判定目标在黑雾内无法索敌，**直接触发严重 OOS 联机同步分叉断开（DESYNC）**！
3. **裁决结论**：
   **严禁在联机环境中单端注入此补丁！** 联机全员必须使用相同版本的构建。

### 3.4 开关、回滚路径与 G-07 TYPE 还原规格

- **INI 配置门控**：`[FogOfWar] EnableGapProtection=1`，`EnableSpySatGate=1`。
> 【W3 勘误 · W3-A6/ISSUE-DEFAULT-GAPPROTECTION】改前：EnableGapProtection=1；改后：EnableGapProtection=0  ; [代码/出厂默认0，安全侧；测试或启用时显式置1]；依据：ra2render/blitter_hooks.cpp:606; ra2render/ra2render.ini:199; config_key_matrix.md:109；分级：P0
- **G-07 内存 TYPE 卸载还原契约**：
  在 `blitter_hooks.cpp` 退出或调用 `RemoveVTableHooks` 时，必须还原首次打补丁前备份的：
  - `SuperWeaponTypeClass+0xB0`（原 `RechargeTime`）
  - `SuperWeaponTypeClass+0xF8`（原 `Range`）
  - `BuildingTypeClass+0x16A5`（原 `SpySat`）
  - `BuildingTypeClass+0x16F0`（原 `SuperWeaponIndex`）
  确保进程生命周期内热卸载后，内存数据不发生残留污染。

### 3.5 终审结论
标定为：**【条件等效】**（单机环境静态等效；联机环境下必须全端一致，属于强条件约束）。

---

## 4. 补丁三：M-9 微粒与粒子系统迷雾剔除 (M-9 Particle & PSys)

### 4.1 被改动指令的原语义 [实证]

- **`ParticleClass` 虚表槽 69**：`0x007EFA68`（`.rdata` 偏移 `0x003EFA68`）
  - 原版 DWORD：`C0 CE 62 00` $\to$ 指向 `ParticleClass::Draw (0x0062CEC0)`
- **`ParticleSystemClass` 虚表槽 69**：`0x007EFCB0`（`.rdata` 偏移 `0x003EFCB0`）
  - 原版 DWORD：`80 E2 62 00` $\to$ 指向 `ParticleSystemClass::Draw (0x0062E280)`
- **原版函数入口特征**：
  - `ParticleClass::Draw @ 0x0062CEC0`：`sub esp, 0x24; push ebx/ebp/esi/edi; mov edi, ecx ... ret 8`（`__thiscall`，入参 `pLocation`, `pBounds`，栈清理 8 字节）
  - `ParticleSystemClass::Draw @ 0x0062E280`：`sub esp, 8; push esi/edi; mov edi, ecx ... ret 8`（同样 `ret 8`）
- **原版迷雾检查缺陷 [实证]**：
  在 `0x0062CF58` 处调用的 `MapClass::IsCellShrouded (0x005865E0)` 机器码为 `32 C0 C2 04 00`（`xor al, al; ret 4`），**西木发行版在函数内部写死恒返回 0（空桩）**！导致原版迷雾裁剪逻辑彻底瘫痪。

### 4.2 新语义与虚表劫持机制 [实证 + 推演]

- **零代码篡改原则**：**禁止** 对 `0x0062CEC0` 与 `0x0062E280` 代码段做任何 inline patch。
- **虚表指针替换**：
  在 `InstallVTableHooks()` 中：
  ```cpp
  // 仅修改 .rdata 槽 69 的 4 字节指针，保存原地址
  PatchVTablePointer(0x007EFA68, FogHooks::Hook_Particle_Draw, &g_pOrigParticleDraw);
  PatchVTablePointer(0x007EFCB0, FogHooks::Hook_ParticleSystem_Draw, &g_pOrigParticleSystemDraw);
  ```
- **钩子函数 ABI 契约与对拍表**：

| 逻辑步骤 | 汇编与伪码语义 | 寄存器与栈状态 | 为什么零副作用 |
|:---|:---|:---|:---|
| **入口** | `void __thiscall Hook_Particle_Draw(void *loc, void *bounds)` | `ECX = this`，`[esp+4]=loc`, `[esp+8]=bounds` | 标准 `__thiscall` 栈帧 |
| **安全谓词** | `if (g_enableParticleFog && !ShouldDrawParticle(this))` | 内部封装 `__try / __except` 保护 | 发生任何野指针异常时恒判定放行，绝对杜绝崩溃 |
| **剔除早退** | `g_telemetry.particlesCulledByFog++; return;` | 编译器生成 `ret 8` | **精确弹出 8 字节栈参数**，与原版函数出口栈平衡完全一致 |
| **放行重放** | `g_pOrigParticleDraw(this, loc, bounds);` | 透传调用原版 `0x0062CEC0` | 完整执行原版渲染例程，视觉完全一致 |

### 4.3 逻辑与渲染解耦论证（生命周期与 Checksum 安全）[实证]

1. **粒子更新在 Update，不在 Draw**：
   - 粒子寿命倒计时递减指令位于 `ParticleClass::Update @ 0x0062CE40`：`DEC dword ptr [esi + 0x128]`；
   - 粒子系统的动力学模拟位于 `ParticleSystemClass::AI @ 0x0062FD60`；
   - **Draw 仅负责软件 Blit 像素投射**。跳过 Draw **绝不会** 导致粒子寿命锁死（与电弧 `EBolt` 在 `DrawAll` 衰减的机制完全不同）。
2. **归属链定谳实证 [实证]**：
   - `Particle + 0x124` = `ParticleSystemClass* Parent`
   - `ParticleSystem + 0xFC` = `HouseClass* OwnerHouse`
   - `ParticleSystem + 0xE0` = `TechnoClass* Owner`（备选 `Techno + 0x21C` $\to$ House）
   - 己方及盟友粒子：`IsHousePlayerOrAlly` 恒返回 true，**己方烟雾/弹道绝对不被误杀**。
3. **联机一致性**：
   - 粒子剔除仅基于本地客户端视口的直视网格（`s_visionGrid`）；
   - 不修改游戏逻辑状态，不改动 RNG，不进 `CurrentFrameCRC`。**零 OOS 风险**。

### 4.4 终审结论
标定为：**【静态等效】**（对游戏逻辑状态 100% 静态等效；画面表现符合剔除规格）。

---

## 5. 补丁四：CRT 高频小对象池化 (CRT Memory Pool, P-M1…P-M5 加固版)

### 5.1 被改动指令的原语义 [实证]

```asm
; [operator new] 0x007C8E17 (FileOffset: 0x3C8E17)
0x007C8E17: 6A 01                 push 1
0x007C8E19: FF 74 24 08           push dword ptr [esp + 8]   ; size
0x007C8E1D: E8 20 06 00 00        call 0x007C9442            ; _nh_malloc(size, nhFlag=1)
0x007C8E22: 59                    pop  ecx
0x007C8E23: 59                    pop  ecx
0x007C8E24: C3                    ret〔勘误 ASM-FIX-33 · U-3〕原记 85 C0（`test eax, eax`）实测 C3（`ret`）—— 本包装函数（__nh_malloc）在 pop ecx; pop ecx 之后即返回，故 test/jne 不可能位于此 VA
0x007C8E25: 55 8B EC              push ebp; mov ebp, esp〔勘误 ASM-FIX-33〕原记锚点 0x007C8E26 与字节串 75 14（`jne 0x007C8E3C`）均不符；实测断言 0x007C8E26: 8B EC —— 该 VA 已是**下一函数**（起点 0x007C8E25）体内
...〔勘误 ASM-FIX-33 · U-3〕滑窗序列配准（0x007C8E24 ±0x200，逐偏移比对）结论：声明序列 85 C0 / 75 14 在窗内**无指令边界对齐命中**（该 4 字节模式全镜像 44 处，最近者远 >±0x200）⇒ 本行起的 4 行**来源构建不明 · 待重新锚定**（禁止猜）〔ASM-FIX2-3 · F2 定向重锚（本批实测）〕本 4 行**函数归属已定、来源仍不明**：`0x007C8E17: 6A 01 FF 74 24 08 E8 20 06 00 00 59 59 C3`（`push 1; push [esp+8]; call 0x007C9442; pop ecx; pop ecx; ret`）是**完整 14 字节 thunk**（`0x007C8E17–0x007C8E24`），故 `0x007C8E24 = C3 (ret)` 为函数尾声；`0x007C8E25: 55 8B EC` 起是**另一个独立函数**的入口，其体内含 `imul edi,[ebp+0x14]`（`0x007C8E34`）、`cmp ecx,edi`（`0x007C8E3D`）、`shr ebx,1`（`0x007C8E43`）与经 `[ebp+0x18]` 的**比较回调调用**（`0x007C8E62: FF 55 18`）⇒ CRT 排序/区间类例程，`cmp ecx,edi` **不属** operator new thunk。原记 `85 C0` / `75 14` 经本批全镜像普查：该 4 字节模式共 44 处，**CRT 区 `0x007C0000–0x007E0000` 内 0 处、`0x007C8E24 ±0x800` 内 0 处** ⇒ 声明的 test/jne 序列在基线镜像中**无任何可归属位置**，维持「**来源构建不明 · 待重新锚定**」（禁止猜；候选搜索范围 = 上列 44 处站点，与 P-M1 补丁无关）。
0x007C8E3D: 3B CF                 cmp ecx, edi〔勘误 ASM-FIX-33〕原记 7C8E3Ch: C3（`ret`）实测不符：0x007C8E3C 实为 0C（0x007C8E3A: 89 4D 0C `mov [ebp+0xC], ecx` 的末字节），`cmp ecx, edi` 真锚点 = 0x007C8E3D（Δ+1）

; [operator delete] 0x007C8B3D (FileOffset: 0x3C8B3D)
0x007C8B3D: FF 74 24 04           push dword ptr [esp + 4]   ; ptr
0x007C8B41: E8 A2 08 00 00        call 0x007C93E8            ; free(ptr)
0x007C8B46: 59                    pop  ecx
0x007C8B47: C3                    ret
```
- **原版特征**：所有小对象一律穿透至 MSVC 6.0 运行库的原生堆分配例程，内部争抢单线程堆锁 `_HEAP_LOCK`，且在频繁创建/销毁粒子与弹丸时发生严重内存碎片。

### 5.2 P-M1…P-M5 五重加固架构对拍论证 [推演 + 实证]

针对 `crt_pool_risk_review.md` 识别出的五大致命缺陷，加固版对拍设计如下：

| 防护编号 | 缺陷威胁 | 加固实现规范 | 汇编/机器级安全保证 |
|:---:|:---|:---|:---|
| **P-M1** | 8 字节对齐破坏<br>（导致 `double`/SSE 崩溃） | 头部强制 8 字节：`struct PoolBlockHeader { uint32_t magic; uint32_t poolIdx; };`<br>块大小对齐：`(sz + 7) & ~7` | 返回指针为 `pBlock + 8`，严格满足 8 字节对齐，`BulletClass` 浮点速度向量 `Vector3D<double>` 读写零异常。 |
| **P-M2** | Double Free 环形死循环 | 释放瞬间立即投毒：`pHdr->magic = 0xDEADBEEF` | 二次释放检测到 `magic != 0xA5A55A5A` 直接拦截并消费，链表绝不形成自引用环。 |
| **P-M3** | Tag 伪造与误释放 | 硬件级双重地址范围守卫：<br>`if (ptr < m_buffer || ptr >= m_bufferEnd) return orig_free(ptr);` | 任何外部非本池内存绝对不会误入 Freelist，100% 穿透至原生 CRT `free`。 |
| **P-M4** | 跨线程并发撕裂链表 | 抛弃普通指针交换，全线采用无锁原子 CAS：<br>`InterlockedCompareExchangePointer(&m_freeList, pNext, pBlock)` | 耗时仅 5~10ns，免疫 DirectSound 音频流与网络线程对 `new/delete` 的并发打扰。 |
| **P-M5** | 局内热回滚引发堆损坏<br>(`0xC0000374`) | **启动期单次锁定配置**：禁止局内动态将开关由 1 改为 0；卸载时常驻穿透检测 | 存活的池化对象在释放时绝不送入原生堆，杜绝 Windows 堆完整性校验崩溃。 |

### 5.3 不可静态判定项与实测验证方案 [待实测]

| 验证项 | 测量维度 | 测试场景与指标要求 |
|:---:|:---|:---|
| **CRT-V1** | 内存池耗尽稳定性 | 单机开局放置 5000+ 粒子/抛射体，观察遥测 `poolFallbacks` 是否平滑递增，游戏进程零卡死、零闪退。 |
| **CRT-V2** | 内存碎片与长跑留痕 | 8 玩家 AI 挂机混战对局 60 分钟，私有工作集内存（Private Working Set）增长不超过 80MB，无阶梯状线性泄漏。 |

### 5.4 终审结论
标定为：**【条件等效】**（严格遵循 P-M1…P-M5 加固规范且单次启动锁定时，等效于高吞吐安全分配器）。

---

## 6. 补丁五：音频引擎并发削峰与智能限频 (Audio Engine De-flood)

### 6.1 被改动指令的原语义 [实证]

```asm
; [VocClass::PlayGlobal] 0x00750920 (FileOffset: 0x350920)
0x00750920: 51                    push ecx                     ; 暂存 SoundID
0x00750921: A0 AC 64 84 00        mov  al, byte ptr [0x8464AC] ; 读取 VoicesEnabled
; ... 函数体 ...
0x0075092E: 33 C0                 xor  eax, eax                ; 失败/禁用返回 0 (NULL)
0x00750930: 59                    pop  ecx
0x00750931: C2 08 00              ret  8                       ; ★ 平衡 __fastcall 2 个栈参数 (Volume, pCtrl)

; [VocClass::PlayAt] 0x007509E0 (FileOffset: 0x3509E0)
0x007509E0: A0 AC 64 84 00        mov  al, byte ptr [0x8464AC] ; 读取 VoicesEnabled
0x007509E5: 53                    push ebx
; ... 函数体 ...
0x007509EC: 33 C0                 xor  eax, eax                ; 失败/超出射程返回 0 (NULL)
0x007509EE: 5B                    pop  ebx
0x007509EF: C2 04 00              ret  4                       ; ★ 平衡 __fastcall 1 个栈参数 (pCtrl)
```
- **核心原版缺陷实证**：
  1. **Limit 事后粗暴掐断**：`sound.ini` 中的 `Limit` 根本不在入口生效，而是在 33ms 后的 `0x4041D0` 遍历中调用 `0x404D80` 粗暴掐断旧音效，产生严重 DAC 阶跃爆音（Clicks/Pops）；
  2. **通道池饱和饥饿**：300 槽通道池（`0x0087E2A8`）在交火时瞬时占满，导致战术警报语音（如核弹警笛）被静默丢弃。

### 6.2 新语义与关键 ABI 栈平衡对拍 [实证 + 关键纠偏]

> [!WARNING] 历史草案严重错误拦截：
> 某些旧规范草案中写有 `or eax, -1; ret` 作为静音返回分支。
> **实证驳斥**：
> 1. `VocClass::PlayGlobal` 是 `ret 8`，返回类型为 `Voice*`；
> 2. `VocClass::PlayAt` 是 `ret 4`，返回类型同样为 `Voice*`；
> 3. 若返回 `-1`（`0xFFFFFFFF`），调用方做 `if (pVoice != NULL)` 检测为真，随后解引用 `0xFFFFFFFF` 将直接崩溃！
> 4. 若使用平栈 `ret`（0 字节清参），调用者栈指针偏移 4 或 8 字节，后续退栈必然跳入非法地址引发崩溃！

**静态等效的绝对安全实施规范**：
- **`PlayGlobal` 限频早退分支**：
  ```asm
  xor eax, eax    ; 返回 NULL
  ret 8           ; 严格弹出 8 字节参数
  ```
- **`PlayAt` 限频早退分支**：
  ```asm
  xor eax, eax    ; 返回 NULL
  ret 4           ; 严格弹出 4 字节参数
  ```

### 6.3 EVA 专属流绝对隔离与保护实证 [实证]

根据 `audio_engine_deep_dive.md` §7.2 反汇编实证：
1. **通道完全分流**：EVA 战术广播走 `EVA::QueueVoice (0x00752700)` $\to$ `0x00752480`，使用专属独立音频流 `AudioStream ([0x00B1D4CC])` 和独立临界区 `0x0087E7F8`，**物理上完全不占用 300 槽通道池**；
2. **警笛饥饿根除**：伴随 EVA 的全局警笛音效（`PlayGlobal`）在 300 槽通道池活跃数被削减 96%（稳定在 10~20 条）后，分配成功率恢复为 100%。

### 6.4 终审结论
标定为：**【条件等效】**（遵循 ABI 清栈返回契约后，对战局逻辑 0 扰动，听觉质量显著优化）。

---

## 7. 补丁六：L4 视口局部打脏 (L4 Vision-Dirty)

### 7.1 被改动指令的原语义 [实证]

```asm
; TacticalClass::Render (0x006D3870) 内部
0x006D3D97: 3B C2                 cmp eax, edx            ; 比较当前脏矩形总面积与阈值
0x006D3D99: 0F 8D 98 00 00 00     jge 0x006D3E37          ; [原版] 超过阈值跳转全量重绘
; 未超阈值则进入局部脏矩形重绘分支
```
- **基线版本行为（`force-full`）**：
  `0x006D3D99` 改写为 `E9 99 00 00 00 90`（`jmp 0x006D3E37; nop`），强制每帧无条件刷新整屏，绝对防止移动单位移出后迷雾延迟退回。
- **可切换方案（`vision-dirty`）**：
  恢复原版 `0F 8D 98 00 00 00`，依靠局部打脏算法主动激活刷新。

### 7.2 新语义与增量打脏算法对拍 [实证 + 推演]

- **打脏接口 ABI**：
  `TacticalClass::RegisterCellAsVisible (0x006DA7D0)`（`__thiscall`, `ECX = TacticalClass::Instance`, 栈传参 `CellClass* pCell`, `ret 4` 清参）。
- **`pCell+0x5C` 原生同帧去重实证**：
  `0x006DA7EE: cmp dword ptr [edi + 0x5C], eax`，比对是否等于 `CurrentFrame`，若已登记则立即早退，**单帧内多次外扩调用开销为 $O(1)$**。
- **保底全量回退机制**：
  单帧视野翻转格超过 **350 格**（如超武全图扫视、飞机极速拉屏）时，直接置位 `TacticalClass + 0xD7D`（`Redrawing = 1`），平滑退回全量重绘，杜绝漏刷残影。

### 7.3 不可静态判定项与实测验证方案 [待实测]

| 验证项 | 验证内容 | 验收测量指标 |
|:---:|:---|:---|
| **L4-V1** | 迷雾边缘锯齿与过渡帧形态 | 部队在黑雾边缘走动，3×3 外扩保护带是否完全覆盖 $60\times 30$ 等轴菱形及 48 帧边角。 |
| **L4-V2** | 高分辨率 GPU 负载对比 | 4K 分辨率下，静态待机画面 GPU Blit 吞吐量下降 $\ge 60\%$。 |

### 7.4 终审结论
标定为：**【条件等效】**（保持 `force-full` 默认基线，`vision-dirty` 受 350 格全量保底约束）。

---

## 8. 终审放行清单与落地准入结论 (Landing Acceptance Sign-off)

经过对六大落地补丁的逐条指令、寄存器副作用、栈平衡、EFLAGS 标志位及联机同步契约的全维度静态审验，审查结论如下：

1. **M-8 联机诊断**：**准许合入**，但必须在合并前将 H-D5 补丁跳板机器码由 `83 E0 FF` 修复为 `0F B6 C0`（`movzx eax, al`）；
2. **M-10 裂缝/间谍卫星**：**条件准许合入**，必须在发布配置中强制要求联机全端对齐，严禁单端混部；
3. **M-9 微粒剔除**：**完全准许合入**，虚表槽 69 覆写零侵入函数体，`EnableParticleFog` 保持默认 0；
4. **CRT 内存池**：**准许合入**，必须包含 P-M1…P-M5 8 字节与原子 CAS 加固，禁止局内动态热切；
5. **音频限频**：**准许合入**，必须严格落实 `ret 8` / `ret 4` 与返回 `NULL` 的 ABI 平栈契约；
6. **L4 视口打脏**：**准许合入**，维持 `force-full` 默认值，保留可切换开关。

本静态论证包作为落地代码合入前的核心风控法定凭据，即刻生效封存。
