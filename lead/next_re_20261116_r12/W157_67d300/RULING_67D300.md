# W157 · RULING 0x67D300

> 卡：W157（R12 逆向卡）｜2026-11-16｜静态，Ghidra 12.1.4 + capstone 5.0.7 双通道｜未启动游戏/未 attach/未改任何游戏文件或台账
> 项目副本：`lead\next_re_20261116_r12\_ghidra\W157`（直接用，-noanalysis，未覆盖）

## 判决（5 行）

1. **[已证] `0x67D300` = COM/OLE 存档序列化器，不是每帧协调器。** Ghidra 反编译为 `IStream::Write(Count)` + 循环 `QueryInterface(IID_IPersistStream)` + `OleSaveToStream` + `Release`；`CALL EBP` 的目标 IAT `0x7E15F4 = OleSaveToStream`。
2. **[已证] `0x67CEF0`（父）= 存档文件构造器**：`MultiByteToWideChar → StgCreateDocfile → CreateStream("CONTENTS") → CoFileTimeNow → CoCreateInstance → OleRun → call 0x67D300`。字符串 `SAVING GAME [%s] - Complete.`、`SUN.EXE`、`CONTENTS`、`***** FAILED!`。
3. **[已证] `0x5F6250` = 逐字段序列化器**（W151 正确）：259 B，把对象字段逐个经 `0x4A1D50`（写 dword）/`0x4A1CA0`（CRC32 查表更新，表 `0x81F7B4`）写出；出现在 **8 个虚表**里（DATA 引用）。
4. **[已证] 门控把这条链挡在每帧之外**：`0x55D360` 内的唯一存档调用点 `0x55DC92` 前面是 `cmp [0xA8B238],0 / jne skip`、`test [0xABCE08],al / jne skip`、随后 `mov [0xABCE08],1`（一次性标志）。进程生命期内最多触发一次（首次进入的自动存档），**正常游戏不每帧执行**。
5. **[已证] 111 回边双通道对账**：Ghidra `BACKEDGE_ASM_COUNT=111`；capstone 从入口线性反汇编 1706 条指令、`ALL_JUMP_BACKEDGES=111`（全 `jl`）。它们是"按存档条目遍历对象数组并逐个 OleSaveToStream"的循环，上界来自各对象数组 `Count`，**不是每帧遍历全部对象做状态更新**。

**结论：W151 的"存档/COM 序列化链"成立；§882-5 / §873 的"每帧协调器"定性错误，必须改口。**

---

## 一、两条假设的证实 / 证伪

### 假设 A（§882-5 / §873）：0x67D300 是"依次驱动 7 种子系统单例的每帧协调器" → **证伪**

- **A-1 [已证]** 头部不是"驱动单例"而是"准备存档 + 写流"。原始反汇编（`EVIDENCE/w157dump.log:45-104`）：
  ```
  0067d300  SUB ESP,0x8
  0067d30f  PUSH ESI                      ; ESI = 传入的 IStream*
  0067d310  CALL 0x689310                 ; 写场景/全局元数据
  0067d31b  CALL 0x004c6340
  0067d327  CALL 0x00674730
  0067d32c  MOV EAX,[0x008b4160]           ; 数组 Count
  0067d342  CALL dword ptr [ECX+0x10]      ; IStream::Write 写 Count
  0067d35d  MOV EAX,[0x008b4154]           ; 数组 Items
  0067d36e  PUSH 0x7f7c80                  ; IID
  0067d374  CALL dword ptr [ECX]           ; QueryInterface
  0067d386  CALL EBP                       ; [0x7e15f4] = OleSaveToStream
  0067d397  CALL dword ptr [ECX+0x8]       ; Release
  0067d3a9  JL 0x67d35d                    ; 下一个对象（回边）
  ```
- **A-2 [已证]** Ghidra 反编译（`EVIDENCE/callers.log:655-762`）直接给出类型：`IStream *in_ECX`、`LPPERSISTSTREAM pIStack_8`、`(*in_ECX->lpVtbl->Write)(...)`、`OleSaveToStream(pIStack_8,in_ECX)`。
- **A-3 [已证]** IAT 语义（`EVIDENCE/verify.log`）：`0x7e15f4=OleSaveToStream`、`0x7e15c8=StgCreateDocfile`、`0x7e15fc=CoCreateInstance`、`0x7e1600=OleRun`、`0x7e11c4=MultiByteToWideChar`、`0x7e15e8=CoFileTimeNow`。
- **A-4 [已证]** `0x67D300` **0 个字符串引用**（Ghidra `STRINGS(0)`，与 §881-4 "无字符串"一致），但存档语义由调用它的父函数 `0x67CEF0` 的字符串表坐实——见 B-2。协调器不应完全无字符串且满是 COM I/O。
- **A-5 [已证]** §881-4 引用的开头反汇编 `0067D308 mov ecx,[0xA8B230] / call 0x689310 / mov ecx,0x8A38E0 / call 0x4C6340 / mov ecx,[0x8871E0] / call 0x674730 / call [ecx+0x10]` 被解读为"依次驱动多个子系统单例"。实际这四条 call 是**写存档头/元数据**（`0x689310`/`0x674730` 后紧跟 `IStream::Write`），`call [ecx+0x10]` 是 `IStream` 虚槽，不是"子系统 Update 槽"。原文对同一段字节的语义误读。
- **A-6 [已证]** 所谓"唯一调用者 `0x67D1AF`" 其实是父函数 `0x67CEF0` 内部的一条指令（`CALLER_67D1AF` 的 ACTUAL_ENTRY=0x67CEF0，size=1040）；Ghidra 引用模型 `XREFS->67D300 COUNT=1 from=0x67d1af`，一致。

### 假设 B（R11 W151）：0x67D300 是存档/COM 序列化链 → **证实**

- **B-1 [已证]** `0x67D300` 核心 = `IID_IPersistStream` + `OleSaveToStream`。IID 常量 `0x7F7C80` 的 16 字节（`EVIDENCE/capstone_scan.log`）：
  ```
  007f7c80  09 01 00 00 00 00 00 00 c0 00 00 00 00 00 00 46
          = {00000109-0000-0000-C000-000000000046} = IID_IPersistStream
  ```
- **B-2 [已证]** 父 `0x67CEF0` 的字符串表（`EVIDENCE/capstone_scan.log`，VA 与内容逐条）：
  ```
  0x83D540 "seHeight"    0x83D550 "TurnRate"   （字段名）
  0x83D560 "SAVING GAME [%s] - Complete.\n\n"
  0x83D584 "***** FAILED!\n"
  0x83D598 GUID 8e d7 5c 0d 70 64 d2 11 9b 74 00 10 4b 97 2f e8
  0x83D5A8 "CONTENTS"（宽字符）   ← CreateStream 的流名
  0x83D5BC "SUN.EXE"
  0x83D5C4 "\nSAVING GAME [%s] - Complete.\n"
  0x83D5D4 "Writ..."
  ```
  `CONTENTS` 是 OLE 复合文档的标准根流名——存档格式铁证。
- **B-3 [已证]** `0x5F6250` 真相 = **逐字段序列化器**（`EVIDENCE/w157dump.log:2191-2278`）：
  - 读对象字段 `[esi+0x30]/[0x34]/[0x6c]/[0x74]/[0x80..0x90]/[0x9c]/[0xa0]/[0xa4]`；
  - byte 字段 → `0x4A1CA0`（134 B）：内含 `MOV EBX,[EBP*4+0x81F7B4]` CRC32 查表 + `NOT/XOR` 增量校验；
  - dword 字段 → `0x4A1D50`（23 B）：`PUSH 4 / PUSH &val / CALL 0x4A1DE0`（写 4 字节包装）；
  - 按 `[0xA8B238]`（模式）条件写 `[esi+0x80]/[0x83]` — 即"按游戏状态决定写哪些字段"，存档语义。
- **B-4 [已证]** `0x5F6250` 被 8 个虚表引用（`XREFS->5F6250` 的 8 条 DATA：`0x7E4718/0x7EC28C/0x7EF094/0x7EF408/0x7EF988/0x7F3330/0x7F66DC/0x7F6C28`），即它是可序列化类的虚方法（对应 IPersistStream::Save 一族），非普通工具函数。
- **B-5 [未证·需更正 W151 细节]** W151 称"槽 13 = 0x5F6250"。本卡发现 W151 的 `fn_67cef0_bulletloop.log` 把 `0x67CC30` 标成 `0x67CEF0` 的内容，而 Ghidra 实测 `0x67CC30` 的 containing fn = **NULL**（落在函数间隙），`0x67CEF0` 实际范围 `0x67CEF0..0x67D2FF`（size=1040，回边=0）。故"槽 13"这个具体编号的来源不可靠；能证实的是"0x5F6250 是虚表里的序列化方法"。**槽位编号标 [未证]，待独立复核。**

---

## 二、111 个回边：遍历什么、上界来自哪里（问题 2）

- **[已证] 双通道独立出数并一致**：
  - Ghidra 通道：`W157Dump.java` 对函数体每条 `j*` 指令取 flow target，`BACKEDGE_ASM_COUNT=111`（`EVIDENCE/w157dump.log:1751`）。
  - capstone 通道：从已知函数入口 `0x67D300` 线性反汇编 4411 B 共 1706 条，`ALL_JUMP_BACKEDGES=111`、`CONDITIONAL_JCC_BACKEDGES=111`、`UNCOND_JMP_BACKEDGES=0`（`EVIDENCE/capstone_scan.log`）。
  - 复跑命令见文末 LEAD_AUDIT。
- **[已证] 指令边界先验**：7 个关键字节命中全部落在从入口线性反汇编的指令起点上（capstone `on_boundary=True`，含 `0x67D342 ff5110`、`0x67D36e 68807c7f00`、`0x67D386 ffd5`）。符合纪律 §3。
- **[已证] 每条回边是"存档条目循环"而非"每帧状态更新"**：反编译显示循环体固定形态 `Write(Count) → for(i<Count){ QI(IPersistStream); OleSaveToStream(obj, stream); Release; }`（`callers.log:689-762`），前 200 行反编译就出现 **8 组** `IStream::Write` + `OleSaveToStream`。
- **[已证] 上界来源**：`local_4 = DAT_008b4160`（Count）、`DAT_008b4118`、`DAT_008b4148`、`pIStack_8=DAT_008b4148` 等——即各对象 `DynamicVectorClass::Count`（存档当时的实例数量），不是固定帧预算。
- **[静态推断]** 111 = 依次序列化多种对象数组（台账称 House/Unit/Infantry/Building/Aircraft/Anim/Trigger 七种）各自的循环 + 每个数组前的 `Write(Count)/HRESULT` 检查回跳。本卡只反编译了前 200 行（8 组），未逐个数满 7 种数组对应的全部循环；但性质已定死。区分"要写出的对象列表"和"全部实例数组"的结构判据：这里读的是 `Items[i]` 逐个 `QueryInterface(IPersistStream)` 写盘（有 `OleSaveToStream` 副作用 + `Release`），而每帧状态更新只会调对象 Update 虚槽、不会有 `IStream::Write` 与 IID 转换。
- **[未证]** 111 个回边的精确逐条分类（哪一个对应哪一种数组）未在预算内完成；不影响"按存档条目遍历"的定性。

---

## 三、门控条件（问题 3）：正常游戏下会不会每帧执行？

**答：不会。[已证]**

- **入口门控（`0x55D360` 内，存档分支）**（`EVIDENCE/perframe.log:112-119`）：
  ```
  0055dbcd  cmp dword ptr [0xA8B238], edi      ; 模式选择器 vs 0
  0055dbd3  jne 0x55dc99                        ; ≠0 → 跳过整个存档块
  0055dbd9  mov al, byte ptr [0xABCE08]
  0055dbde  test al, al
  0055dbe0  jne 0x55dc99                        ; 已置位 → 跳过
  0055dbee  mov byte ptr [0xABCE08], 1          ; ★ 一次性标志置位
  ... 0x55dc45 字符串 ".sav" ... 0x55dc7d CALL 0x7ca564 ...
  0055dc92  CALL 0x67CEF0                        ; 存档（唯一进 0x67D300 的路）
  ```
  `[0xABCE08]` 一旦置 1 永不复位（本卡在 `0x55D360` 内只见该一处写），因此 `0x67CEF0 → 0x67D300` 全进程最多一次。
- **四个调用者全是存档场景**（`EVIDENCE/w157dump.log:2832-2837` + `EVIDENCE/callers.log:102-212`）：
  | 调用点 | 上下文字符串 | 场景 |
  |---|---|---|
  | `0x55DC92`（在每帧更新内） | `.sav`、`0x82A05C` | 首次自动存档（受上一次性标志门控） |
  | `0x4C7AC0` | `TXT_SAVING_GAME`、`SAVEGAME.NET`、`TXT_MULTIPLAYER_GAME`、`Event.CPP` | 多人/网络存档 |
  | `0x4C7B3D` | 同上 | 多人/网络存档 |
  | `0x559E85` | `TXT_SAVING_GAME`、`LoadDlg.CPP` | 载入对话框存档 |
- **与 §882 的 SYNC 门控对照**：SYNC 转储是 `[0xA8D5F8]&2` + `-MPDEBUG`；本链是 `[0xA8B238]==0` + `[0xABCE08]==0`（一次性）。两者都把大函数挡在每帧之外，属于同类误判。
- **[未证]** `[0xABCE08]` 在 `0x55D360` 之外是否还有复位写者（本卡未做全镜像穷举）；即便有，也是"按需存档"，不改变"非每帧"结论。

---

## 四、台账处置建议（问题 4）

- **§882-5 / §873 / §883 / R11_COMMON §3.4 中"每帧主要候选 = 0x67D300（111 回边、7 种数组）"必须改口**：它是存档序列化器，不是每帧工作。建议台账新增一条"§89x W157 判决"并 line-through 旧定性，保持 append-only。
- **W151 §889-6 从 `[静态推断·待复验]` 升级为 `[已证]`**（本卡独立复现其 COM 序列化定性），但其"槽 13"细节标注待复核（见 B-5）。
- **"每帧主要候选"应改成什么**（从 `0x55D360` 深度 ≤4 内选）：
  - **首选 `[静态推断]`：`0x647260 → 0x6474C7 → 0x64C380`（事件泵链）**。依据：`0x55D360` 在 `0x55DE40` 直接调 `0x647260`（`perframe.log:86`）；`0x647260` 入口 `test [0xA8D5F8],2; je 0x6474C7`，正常游戏 `&2==0` ⇒ 走 `0x6474C7` 事件泵；`0x6474C7` 尾部 `0x6475AE call 0x64C380`（`perframe.log:195`），`0x64C380` 是遍历 16,384 项环形缓冲的消费者（R11 §883）。这是当前已知**每帧必走且带全场事件遍历**的最强候选。
  - **次选 `[静态推断]`：`0x55AFB0`（House×2，深度1，1901 B）** — `0x55D360` 直接 callee 之一（`0x55DC9E`），但范围仅 House。
  - **[未证]** 真机"ms/帧与子弹数相关（配对中位 +40 ms）"的成本归属仍未定位到单一函数——事件泵处理子弹事件只是推测，需计时/动态证据，本卡不下结论。
  - 明确排除：`0x64DEA0`/`0x6516F0`（SYNC 转储，§882 已排除）、`0x6DD8B0`（TAction，§880 已排除）、`0x67D300`（本卡排除）。

---

## LEAD_AUDIT（独立脚本可抽验的 3 条核心数字）

> 全部基于磁盘静态字节，命令可直接粘贴。ImageBase `0x400000`，文件 `ra2youli\gamemd.exe`。

1. **[已证] 111 回边双通道**（地址 + 反汇编命令复跑）
   ```
   python lead\next_re_20261116_r12\W157_67d300\work\w157_capstone.py
   # 期望: instructions=1706  ALL_JUMP_BACKEDGES=111  CONDITIONAL_JCC_BACKEDGES=111
   D:\ghidra\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat <卡>\..\_ghidra\W157 gamemd_auto -process gamemd.exe -noanalysis -scriptPath <卡>\work -postScript W157Dump.java *> a.log
   # 期望: ### FN_67D300 BACKEDGE_ASM_COUNT=111
   ```
   回边样例地址（capstone 输出逐条列全）：`0x67D3A9 jl 0x67D35D`、`0x67D41D jl 0x67D3DC`、`0x67D470 jl 0x67D42A`。

2. **[已证] IID_IPersistStream 字节 + OleSaveToStream 字节命中（先验边界）**
   ```
   python lead\next_re_20261116_r12\W157_67d300\work\w157_capstone.py
   # 007f7c80  09 01 00 00 00 00 00 00 c0 00 00 00 00 00 00 46  (= IID_IPersistStream)
   # 检查: 0x0067d342 bytes=ff5110 on_boundary=True  call [ecx+0x10]
   #       0x0067d386 bytes=ffd5    on_boundary=True  call ebp ; ebp=[0x7e15f4]=OleSaveToStream
   # Ghidra 符号: IAT 007e15f4 sym=PTR_OleSaveToStream_007e15f4  (EVIDENCE/verify.log)
   ```

3. **[已证] 门控一次性标志（反汇编地址 + 字节）**
   ```
   capstone 线性反汇编 0x55DB90..0x55DC95 (脚本 w157_perframe.py 第"save branch lead-in"节):
   0055dbcd  393d38b2a800  cmp dword ptr [0xa8b238], edi
   0055dbd3  0f85c0000000  jne 0x55dc99
   0055dbd9  a008ceab00    mov al, [0xabce08]
   0055dbe0  0f85b3000000  jne 0x55dc99
   0055dbee  c60508ceab0001  mov byte ptr [0xabce08], 1
   0055dc92  e859f21100    call 0x67cef0
   # 引用计数: XREFS->67D300 COUNT=1 from=0x67d1af ; XREFS->67CEF0 COUNT=4 ; XREFS->5F6250 COUNT=14 (含8 DATA)
   ```
