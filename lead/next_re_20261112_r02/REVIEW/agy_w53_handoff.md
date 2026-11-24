# Antigravity handoff

## Result

正在对 `ra2bench\gamemd.exe` 的 `.text` 段（约 4MB）执行全量 Capstone 指令解码，以提取 `MixFileClass::Find`（`0x5B4430`）、`CCFileClass::Get_File`（`0x473D10`）及 `MixFileClass` 链表头（`0xABEFE0`）的全部指令级交叉引用，完成后继续分析。
正在检索 `MixFileClass` 链表头/尾指针（`0xABEFDC`–`0xABEFF0`）与 `0x75A120` / `0x432750` 调用点的全量指令交叉引用，完成后继续核验。
正在核验三处 `rel32` 跳转指令字节及反例候选调用点（`0x432690`、`0x759260`）的字符串与调用者，完成后继续汇总。
正在核验音频流标志位函数（`0x75A790`–`0x75A8B0`）及 `0x5BFAA0` 的调用者以完成反例检验，完成后继续。
由于当前处于只读 `/plan` 约束，未向工作区写入 `lead\next_re_20261112_r02\W53_override_independent\` 目录（已生成落盘实施计划待批准）。按指令要求，以下在回复正文中完整给出 **W53 独立复核全部结论与证据**。

---

# W53 · 独立复核报告：散装文件 vs MIX 同名条目优先级

- **启动时间（系统本地时间）**：`2026-11-13T21:02:54+08:00`（`STARTED.txt` 预期内容）
- **目标镜像**：[gamemd.exe](file:///D:/Project/ra2-campaign-forge/ra2bench/gamemd.exe)
  - `[本次实测]` 大小：`4,825,360` B
  - `[本次实测]` SHA-256：`73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
  - `[本次实测]` `ImageBase = 0x00400000`，`Characteristics = 0x032F`（`RELOCS_STRIPPED = True`）
  - `[本次实测]` `.text`：`RVA = 0x00001000`，`VSize = 0x003DF38D`，`FOFF = 0x00001000`，`RSize = 0x003E0000`（⇒ `.text` 内 `FOFF = VA − 0x400000`）
  - `[本次实测]` `.detour`：`RVA = 0x00793000`，`VSize = 0x00002718`，`FOFF = 0x00497000`；PE 导入目录位于 `RVA = 0x007955C0`（首项为 `xyr.dll`），`.text` 全量解码中 **0 条指令**引用 `.detour` 地址区间 `0xB93000`–`0xB96000`。
- **核心总结论**：**「通过 `CCFileClass` 打开/读取资源时，散装（磁盘）文件严格优先于 MIX 内同名条目；MIX 列表按 FIFO（先装载者优先）遍历，首个命中即返回。」** 主体结论成立；但在全 `.text` 反例核验中发现 **1 处 `CCFileClass::Is_Available` 探测顺序相反**（仅返回 `bool`，不读数据）以及 **1 处 `0x75A120` 流式打开分支为「仅查 MIX、不回落磁盘」**（详见 Q4 与 `DISAGREE`）。

---

## 一、`CCFileClass::Get_File = 0x473D10`（实为 `CCFileClass::Open(int rights)`，vtable `0x7E16B0 +0x1C`）

### 1.1 完整反汇编（`0x473D10`–`0x473E4D`，`[本次实测]` Capstone 5.0.7）

> 注：该函数在 `0x473DF3`、`0x473DFE`、`0x473E21`、`0x473E36`、`0x473E4B` 共有 **5 个 `ret 4` 中段/尾部出口**；`0x473E4E`–`0x473E4F` 为 `90 90` 对齐填充，紧接下一函数 `0x473E50`（`CCFileClass::Get_Date_Time`）。

```text
0x00473D10: 83 EC 10                 sub esp, 0x10
0x00473D13: 53                       push ebx
0x00473D14: 56                       push esi
0x00473D15: 8B F1                    mov esi, ecx
0x00473D17: 57                       push edi
0x00473D18: 8B 06                    mov eax, dword ptr [esi]
0x00473D1A: FF 50 34                 call dword ptr [eax + 0x34]        ; this->Close() (0x473CE0)
0x00473D1D: F6 44 24 20 02           test byte ptr [esp + 0x20], 2      ; mode & 2 (写位)
0x00473D22: 0F 85 11 01 00 00        jne 0x473e39                       ; 含写位 → 直跳磁盘 Open，跳过磁盘探测与 MIX
0x00473D28: 33 DB                    xor ebx, ebx
0x00473D2A: 8B CE                    mov ecx, esi
0x00473D2C: 53                       push ebx                           ; forced = 0
0x00473D2D: E8 DE E1 FB FF           call 0x431f10                      ; BufferIOFileClass::Is_Available(0) → 磁盘尝试
0x00473D32: 84 C0                    test al, al
0x00473D34: 0F 85 FF 00 00 00        jne 0x473e39                       ; 磁盘命中 → 直跳 0x473E39，跳过整个 MIX 分支
0x00473D3A: 8D 4C 24 0C              lea ecx, [esp + 0xc]               ; &size
0x00473D3E: 8D 54 24 18              lea edx, [esp + 0x18]              ; &offset
0x00473D42: 51                       push ecx
0x00473D43: 52                       push edx
0x00473D44: 8B 16                    mov edx, dword ptr [esi]
0x00473D46: 8D 44 24 1c              lea eax, [esp + 0x1c]              ; &mixPtr
0x00473D4A: 50                       push eax
0x00473D4B: 8B CE                    mov ecx, esi
0x00473D4D: 89 5C 24 20              mov dword ptr [esp + 0x20], ebx    ; mixPtr = 0
0x00473D51: 89 5C 24 1C              mov dword ptr [esp + 0x1c], ebx    ; cachedData = 0
0x00473D55: 89 5C 24 18              mov dword ptr [esp + 0x18], ebx    ; size = 0
0x00473D59: 89 5C 24 24              mov dword ptr [esp + 0x24], ebx    ; offset = 0
0x00473D5D: 8D 7C 24 1C              lea edi, [esp + 0x1c]              ; &cachedData
0x00473D61: FF 52 04                 call dword ptr [edx + 4]           ; this->File_Name() (0x401940)
0x00473D64: 8B C8                    mov ecx, eax                       ; ecx = filename
0x00473D66: 8B D7                    mov edx, edi                       ; edx = &cachedData
0x00473D68: E8 C3 06 14 00           call 0x5b4430                      ; MixFileClass::Find
0x00473D6D: 84 C0                    test al, al
0x00473D6F: 0F 84 AF 00 00 00        je 0x473e24                        ; MIX 未命中 → 0x473E24
0x00473D75: 8B 54 24 10              mov edx, dword ptr [esp + 0x10]    ; cachedData
0x00473D79: 3B D3                    cmp edx, ebx
0x00473D7B: 0F 85 80 00 00 00        jne 0x473e01                       ; 已缓存于内存 → 0x473E01 建 Buffer
0x00473D81: 8B 44 24 14              mov eax, dword ptr [esp + 0x14]    ; mixPtr
0x00473D85: 3B C3                    cmp eax, ebx
0x00473D87: 74 78                    je 0x473e01
0x00473D89: 8B 40 0C                 mov eax, dword ptr [eax + 0xc]     ; mixPtr->Filename
0x00473D8C: 8B 16                    mov edx, dword ptr [esi]
0x00473D8E: 6A 01                    push 1
0x00473D90: 50                       push eax
0x00473D91: 8B CE                    mov ecx, esi
0x00473D93: FF 52 20                 call dword ptr [edx + 0x20]        ; this->Open(mixFilename, 1)
0x00473D96: 85 C0                    test eax, eax
0x00473D98: 74 5C                    je 0x473df6                        ; 容器打开失败 → 0x473DF6 (return 0)
0x00473D9A: 8B 16                    mov edx, dword ptr [esi]
0x00473D9C: 8B CE                    mov ecx, esi
0x00473D9E: FF 52 04                 call dword ptr [edx + 4]           ; File_Name()
0x00473DA1: 50                       push eax
0x00473DA2: E8 61 16 36 00           call 0x7d5408                      ; strdup
0x00473DA7: 83 C4 04                 add esp, 4
0x00473DAA: 8B F8                    mov edi, eax
0x00473DAC: 8B 06                    mov eax, dword ptr [esi]
0x00473DAE: 8B CE                    mov ecx, esi
0x00473DB0: 57                       push edi
0x00473DB1: C6 46 54 01              mov byte ptr [esi + 0x54], 1       ; 置标志跳过 CD 路径搜寻
0x00473DB5: FF 50 08                 call dword ptr [eax + 8]           ; Set_Name(origName)
0x00473DB8: 6A FF                    push -1
0x00473DBA: 53                       push ebx
0x00473DBB: 8B CE                    mov ecx, esi
0x00473DBD: 88 5E 54                 mov byte ptr [esi + 0x54], bl
0x00473DC0: E8 EB 94 1E 00           call 0x65d2b0                      ; RawFileClass::Bias(0, -1)
0x00473DC5: 8B 4C 24 0C              mov ecx, dword ptr [esp + 0xc]     ; size
0x00473DC9: 8B 54 24 18              mov edx, dword ptr [esp + 0x18]    ; offset
0x00473DCD: 51                       push ecx
0x00473DCE: 52                       push edx
0x00473DCF: 8B CE                    mov ecx, esi
0x00473DD1: E8 DA 94 1E 00           call 0x65d2b0                      ; RawFileClass::Bias(offset, size)
0x00473DD6: 8B 06                    mov eax, dword ptr [esi]
0x00473DD8: 53                       push ebx
0x00473DD9: 53                       push ebx
0x00473DDA: 8B CE                    mov ecx, esi
0x00473DDC: FF 50 28                 call dword ptr [eax + 0x28]        ; Seek(0, SEEK_SET)
0x00473DDF: 57                       push edi
0x00473DE0: E8 03 56 35 00           call 0x7c93e8                      ; free(edi)
0x00473DE5: 83 C4 04                 add esp, 4
0x00473DE8: B8 01 00 00 00           mov eax, 1
0x00473DED: 5F                       pop edi
0x00473DEE: 5E                       pop esi
0x00473DEF: 5B                       pop ebx
0x00473DF0: 83 C4 10                 add esp, 0x10
0x00473DF3: C2 04 00                 ret 4                            ; [出口1] MIX(未缓存)成功
0x00473DF6: 5F                       pop edi
0x00473DF7: 5E                       pop esi
0x00473DF8: 33 C0                    xor eax, eax
0x00473DFA: 5B                       pop ebx
0x00473DFB: 83 C4 10                 add esp, 0x10
0x00473DFE: C2 04 00                 ret 4                            ; [出口2] MIX容器打开失败
0x00473E01: 8D 4E 58                 lea ecx, [esi + 0x58]              ; Buffer
0x00473E04: 3B CB                    cmp ecx, ebx
0x00473E06: 74 0B                    je 0x473e13
0x00473E08: 8B 44 24 0C              mov eax, dword ptr [esp + 0xc]     ; size
0x00473E0C: 50                       push eax
0x00473E0D: 52                       push edx                           ; cachedData ptr
0x00473E0E: E8 ED 6E FC FF           call 0x43ad00                      ; Buffer::Buffer(ptr, size)
0x00473E13: 89 5E 64                 mov dword ptr [esi + 0x64], ebx    ; BufferPos = 0
0x00473E16: 5F                       pop edi
0x00473E17: 5E                       pop esi
0x00473E18: B8 01 00 00 00           mov eax, 1
0x00473E1D: 5B                       pop ebx
0x00473E1E: 83 C4 10                 add esp, 0x10
0x00473E21: C2 04 00                 ret 4                            ; [出口3] MIX(已缓存)成功
0x00473E24: 8B 4C 24 20              mov ecx, dword ptr [esp + 0x20]
0x00473E28: 51                       push ecx
0x00473E29: 8B CE                    mov ecx, esi
0x00473E2B: E8 80 6C 00 00           call 0x47aab0                      ; CDFileClass::Open(mode)
0x00473E30: 5F                       pop edi
0x00473E31: 5E                       pop esi
0x00473E32: 5B                       pop ebx
0x00473E33: 83 C4 10                 add esp, 0x10
0x00473E36: C2 04 00                 ret 4                            ; [出口4] MIX未命中回落
0x00473E39: 8B 54 24 20              mov edx, dword ptr [esp + 0x20]
0x00473E3D: 8B CE                    mov ecx, esi
0x00473E3F: 52                       push edx
0x00473E40: E8 6B 6C 00 00           call 0x47aab0                      ; CDFileClass::Open(mode)
0x00473E45: 5F                       pop edi
0x00473E46: 5E                       pop esi
0x00473E47: 5B                       pop ebx
0x00473E48: 83 C4 10                 add esp, 0x10
0x00473E4B: C2 04 00                 ret 4                            ; [出口5] 写模式/磁盘命中出口
```

### 1.2 控制流图

```mermaid
flowchart TD
    A["0x473D10: Close()"] --> B{"0x473D1D: mode & 2 != 0?"}
    B -- "是 (含写位)" --> H["0x473E39: CDFileClass::Open(mode)<br/>直达磁盘，跳过磁盘探测与MIX"]
    B -- "否 (只读)" --> C["0x473D2D: call 0x431F10<br/>BufferIOFileClass::Is_Available(0)<br/>(若未缓存则调 RawFileClass::Is_Available → CreateFileA)"]
    C --> D{"0x473D34: al != 0 (磁盘命中)?"}
    D -- "是 (跳 0x473E39)" --> H
    D -- "否 (磁盘未命中)" --> E["0x473D68: call 0x5B4430<br/>MixFileClass::Find"]
    E --> F{"0x473D6F: al == 0 (MIX未命中)?"}
    F -- "是 (跳 0x473E24)" --> G["0x473E24: CDFileClass::Open(mode)<br/>回落结束 [出口4]"]
    F -- "否 (MIX命中)" --> I{"0x473D79: cachedData != 0?"}
    I -- "是 (跳 0x473E01)" --> J["0x473E01: 包装内存缓冲 [esi+0x58]<br/>return 1 [出口3]"]
    I -- "否 (未缓存)" --> K["0x473D93: Open(mixFilename, 1)<br/>+ Bias(offset, size) + Seek(0)<br/>[出口1/2]"]
    H --> L["ret 4 [出口5]"]
```

### 1.3 问题 1 逐项判定
1. **先后顺序**：`[本次实测]` 先尝试磁盘（`0x473D2D: call 0x431F10`，若 `[ecx+0x29]==0` 则调 `0x65CBF0` `RawFileClass::Is_Available` 调用 `KERNEL32!CreateFileA` 试开），仅当返回 `false` 时才进入 `0x473D3A..0x473D68` 调用 `MixFileClass::Find`（`0x5B4430`）。
2. **磁盘命中是否跳过 MIX**：`[本次实测]` **是**。`0x473D34: jne 0x473E39` 在 `al != 0` 时直接跳转到 **`0x473E39`**，完全跳过 `0x473D3A`–`0x473E38` 的 MIX 查找与读取分支，执行 `0x473E40: call 0x47AAB0`（`CDFileClass::Open(mode)` -> `0x431F70` `BufferIOFileClass::Open` -> `0x65CB50` `RawFileClass::Open`）。
3. **`mode & 2` 位的作用**：`[本次实测]` 在 `RawFileClass::Open`（`0x65CB77`–`0x65CBC1`）中，`rights=1` 为读、`2` 为写（`CREATE_ALWAYS`）、`3` 为读写（`OPEN_ALWAYS`），即 bit 1（`mode & 2`）代表**写访问位**。`0x473D1D: test byte ptr [esp+0x20], 2` 若非零，`0x473D22: jne 0x473E39` **跳过磁盘存在性检查与整个 MIX 分支**，直达 `0x473E39` 走磁盘 `CDFileClass::Open(mode)`（只读 MIX 不可写入，且新建/覆写文件不能要求先存在于磁盘或查 MIX）。
4. **是否有其它分支绕过磁盘**：`[本次实测]` 在 `CCFileClass::Get_File`（`0x473D10`–`0x473E4D`）内部，**不存在**绕过磁盘优先而先查 MIX 的路径（唯一的早退跳转 `0x473D22` 也是直接去磁盘打开，而不是去 MIX）。

---

## 二、`MixFileClass::Find = 0x5B4430`（`[本次实测]`）

1. **「首个命中返回」还是「后者覆盖」**：**首个命中返回（first-hit-wins）**。
   - `0x5B44A1`: `mov ebp, dword ptr [0xabefe0]`（读取表头 `Head.Next`）。
   - `0x5B44A9`–`0x5B44C5`: 循环守卫 `ebp != 0 && [ebp+4] != 0 && [ebp+8] != 0`（到达 `Tail` 哨兵 `0xABEFE8` 时其 `Next` `[0xABEFEC] == 0` 退出并到 `0x5B457D` 返回 `al = 0`）。
   - `0x5B44CB`–`0x5B44FB`: 在当前 `MixFileClass` 的有序 12 字节条目表 `[ebp+0x20]`（项数 `[ebp+0x14]`）内做二分查找；未找到则 `0x5B44FD`/`0x5B4507: mov ebp, [esp+0x14]`（推进到 `node->Next`）并 `jmp 0x5b44a9`。
   - 一旦二分命中（`0x5B4505: jne 0x5b450d`），`0x5B450D`–`0x5B457A` 写入输出参数并立即 **`mov al, 1; ret 0xc`** 返回，**不再继续遍历后续 MIX**。
2. **遍历顺序是 FIFO 还是 LIFO**：**FIFO（先装载者优先）**。指令级依据：
   - 全局链表 `List<MixFileClass*>`（vtable `0x7EDF38`）在静态构造 `0x5B3AC0` 中初始化：`Head`（`0xABEFDC`）的 `Next`（`0xABEFE0`）指向 `Tail`（`0xABEFE8`），`Tail` 的 `Prev`（`0xABEFF0`）指向 `Head`（`0xABEFDC`）。
   - `MixFileClass` 构造函数 `0x5B3C20` 在 **`0x5B3DE2`–`0x5B3E00`** 执行**尾插（`Add_Tail`）**：
     ```text
     0x005B3DE2: mov edi, dword ptr [0xabeff0]   ; edi = Tail.Prev (最后一个已装载节点，或 &Head)
     0x005B3DE8: call 0x5b4590                   ; this->Unlink()
     0x005B3DED: mov edx, dword ptr [edi + 4]    ; edx = &Tail
     0x005B3DF0: mov dword ptr [esi + 8], edi    ; this->Prev = old Tail.Prev
     0x005B3DF3: mov dword ptr [esi + 4], edx    ; this->Next = &Tail
     0x005B3DFD: mov dword ptr [eax + 8], esi    ; Tail.Prev = this
     0x005B3E00: mov dword ptr [edi + 4], esi    ; (old Tail.Prev)->Next = this
     ```
   - 全 `.text` 对 `0xABEFDC`–`0xABEFF0` 的全部指令级引用均已核验（`0xABEFDC` 4 处、`0xABEFE0` 8 处、`0xABEFE4` 4 处、`0xABEFE8` 4 处、`0xABEFEC` 4 处、`0xABEFF0` 5 处），**不存在任何头插（`Add_Head`）操作**。
   - 因此链表从 `Head.Next`（`0xABEFE0`）到 `Tail` 严格按**装载时间由早到晚（FIFO）**排列；`Find` 从 `0xABEFE0` 出发沿 `node->Next` 遍历且首个命中即返回 ⇒ **先装载的 MIX 优先**。

---

## 三、三处 `rel32` 目标独立复算（`[本次实测]`）

`.text` 内 `FOFF = VA − 0x400000`；x86 相对偏移目标公式：`Target = Next_EIP + int32_le(rel32)`。

| 指令 VA / FOFF | 实测字节 | 长度 / Next_EIP | `rel32` 小端有符号解码 | 复算目标 VA | 核对结果 |
|---|---|---|---|---|---|
| `0x473D2D` (`FOFF=0x073D2D`) | `E8 DE E1 FB FF` | `5` / `0x473D32` | `0xFFFBE1DE` = `-0x00041E22` | `0x473D32 - 0x41E22 = 0x431F10` | **一致**（`0x431F10`，`BufferIOFileClass::Is_Available`） |
| `0x473D68` (`FOFF=0x073D68`) | `E8 C3 06 14 00` | `5` / `0x473D6D` | `0x001406C3` = `+0x001406C3` | `0x473D6D + 0x1406C3 = 0x5B4430` | **一致**（`0x5B4430`，`MixFileClass::Find`） |
| `0x473D34` (`FOFF=0x073D34`) | `0F 85 FF 00 00 00` | `6` / `0x473D3A` | `0x000000FF` = `+0x000000FF` | `0x473D3A + 0xFF = 0x473E39` | **一致**（`0x473E39`，`CDFileClass::Open` 磁盘读分支） |

---

## 四、反例检验：是否存在「先查 MIX 再查磁盘」的代码路径？

### 4.1 检索方法与覆盖度（`[本次实测]`，非简单字节扫描）
1. **全 `.text` 指令级解码 xref**：使用 Capstone 32 位 x86 解码器（`detail=True`）自 `0x401000` 完整扫描至 `0x7E038D`（共解码 **1,392,527 条指令**，仅跳过 65 字节非指令跳转表/填充），提取所有立即数/内存操作数引用 `0x5B4430`（`MixFileClass::Find`）与 `0xABEFE0`（`MixFileClass::List.Head.Next`）的指令；并对 `.detour` 节验证 `.text` 0 引用。
2. **全镜像 32 位小端指针扫描**：在全部 4,825,360 B 中搜索 `0x005B4430` 的 4 字节小端编码，结果为 **0 命中**（确认 `MixFileClass::Find` 不在任何 vtable 或函数指针表内，不存在通过函数指针间接调用 `0x5B4430` 的未覆盖路径）。
3. **文件类 vtable 核验**：通过 `.rdata` RTTI `CompleteObjectLocator` + `TypeDescriptor` 确认 `CCFileClass`（`0x7E16B0`）与 `CDFileClass`（`0x7E1668`）虚表各槽位；对 `0x5B4430` 的全部 **7 处**调用点逐一反汇编上下文确认。

### 4.2 `MixFileClass::Find`（`0x5B4430`）全部 7 处调用点逐一核验

| # | 调用点 VA | 所在函数 | 实际顺序（指令级） | 是否为「先 MIX 再磁盘」反例？ |
|---|---|---|---|---|
| 1 | `0x473D68` | `CCFileClass::Open` / `Get_File` (`0x473D10`) | 磁盘 `0x431F10` → MIX `0x5B4430` → `CDFileClass::Open` | **否**（严格磁盘优先） |
| 2 | `0x473C3A` | `CCFileClass::Size` (`0x473C00`) | 内存缓冲 `[esi+0x58]` → 磁盘 `0x431F10` + `0x4325A0` → MIX `0x5B4430` | **否**（严格磁盘优先） |
| 3 | `0x473E7F` | `CCFileClass::Get_Date_Time` (`0x473E50`) | 磁盘 `0x65D1F0` → MIX `0x5B4430` | **否**（严格磁盘优先） |
| 4 | `0x473F35` | `CCFileClass::Set_Date_Time` (`0x473F00`) | 磁盘 `0x65D240` → MIX `0x5B4430` | **否**（严格磁盘优先） |
| 5 | `0x432803` | Bink 视频打开路径 (`0x432750`，引用 `"Bink Error: %s\n"`) | 磁盘 `RawFileClass::Is_Available` (`0x4327CD`) → MIX `0x5B4430` (`0x432803`) | **否**（严格磁盘优先） |
| 6 | `0x473C8B` | `CCFileClass::Is_Available` (`0x473C50`, `vtbl +0x14`) | **先 `0x5B4430`（MIX）后 `0x431F10`（磁盘）** | **顺序相反但仅探测布尔存在性**：仅写缓存位 `[esi+0x68]=1` 并返回 `bool`，**不加载数据、不选源**，且 `Get_File` (`0x473D10`) 不读取 `[esi+0x68]`。 |
| 7 | `0x75A157` | 流式媒体 IO 回调 `0x75A120` `case 1`（由 `0x5BFAA0` → `0x759260` 在 `0xB45BA8` bit0 置位时安装 `0x75A2B0`） | 调用 `0x5B4430`；若 `al == 0` (`0x75A15E: je 0x75A1B6`) 直接返回 `1`（失败），**无磁盘打开回落**；若 `al == 1` 直接打开 MIX 容器文件 | **需警惕的特例（MIX-only）**：不是「先 MIX 再回落磁盘」，而是该子系统在 `0x75A810(0)==1` 时**只读 MIX、不看磁盘**（注意 `0x52C649` 与 `0x52F617` 确实调用 `0x75A7D0(0)` 置位 `0xB45BA8` bit0；其调用方 `0x5BFAA0` 包含视频/VQA 类播放如 `0x5BEF6E` 宽度检查 `0x140`）。 |

**Q4 结论**：
- 在通用资源读取主链（`CCFileClass::Open`/`Get_File`、`Size`、`Get_Date_Time`、`Set_Date_Time` 及 Bink 打开 `0x432750`）中，**不存在任何「先查 MIX 再查磁盘」的路径**（`[本次实测]`，全 `.text` 覆尽）。
- 唯一顺序反转的 `CCFileClass::Is_Available`（`0x473C50`）仅作布尔探测，不影响实际读取优先级；但 **非 `CCFileClass::Get_File` 通道的流式媒体打开器 `0x75A120`** 存在 **MIX-only（不读散装）** 分支，若未来涉及该流式媒体类型（VQA 等），不能套用「散装必然覆盖 MIX」的假设（`[本次实测]` + `[静态推断]` 具体场景受 `0xB45BA8` bit0 状态制约）。

---

## 五、与 `W29_override_order\OVERRIDE_ORDER.md` 及 `REVIEW\LEAD_VERDICT_CSF_live.md` 对照（`[本次读码]`）

### 5.1 「一致」项
1. **镜像标识**：[OVERRIDE_ORDER.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W29_override_order/OVERRIDE_ORDER.md#L4-L8) 所载 `4,825,360 B`、SHA-256 `73201cc0...`、`ImageBase=0x400000`、`RELOCS_STRIPPED`、`.text` `RVA=FOFF=0x1000` —— **完全一致**。
2. **`Get_File = 0x473D10` 主逻辑与顺序**：先 `mode&2` 判断直跳 `0x473E39`、再 `0x473D2D call 0x431F10` 试磁盘、命中由 `0x473D34 jne 0x473E39` 跳过 MIX、未命中才 `0x473D68 call 0x5B4430` —— **完全一致**。
3. **三处 `rel32` 目标**：`0x473D2D -> 0x431F10`、`0x473D68 -> 0x5B4430`、`0x473D34 -> 0x473E39` —— **完全一致**。
4. **`MixFileClass::Find = 0x5B4430` 语义**：`strupr` + `CRC32`、自 `0xABEFE0` 起沿 `node->Next` 遍历二分、首个命中即返回（FIFO / 先装载者优先） —— **完全一致**（且 W53 补齐了 `0x5B3DE2..0x5B3E00` 构造函数尾插指令证据）。
5. **与 [LEAD_VERDICT_CSF_live.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_CSF_live.md#L30-L81) 真机结论一致**：散装 `ra2md.csf` 在 `Get_File` 主链下覆盖 MIX 成立；`LEAD_VERDICT_CSF_live.md` 已独立纠正 W29 关于「不完整 CSF 会启动失败」的静态误判（区分魔数非法与标签不全）。

### 5.2 「不一致 / 需修订」项（`DISAGREE` 摘要）
1. **函数命名误标（[OVERRIDE_ORDER.md §1.4](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W29_override_order/OVERRIDE_ORDER.md#L96-L106)）**：
   - W29 把 `0x473C50`（`CCFileClass` vtable `+0x14`）写作 `CCFileClass::Open`，把其内部 `0x431F10` 与 `0x65CBF0` 写作 `磁盘 Open` / `RawFileClass::Open(0)`。
   - **W53 实测**：通过 RTTI 核验 `CCFileClass`（`0x7E16B0`）、`CDFileClass`（`0x7E1668`）、`BufferIOFileClass`（`0x7E3A40`）及 `RawFileClass`（`0x7F0918` 属槽 `+0x14`）：
     - `vtable +0x14` 是 **`Is_Available(int forced)`**（`0x473C50`、`0x431F10`、`0x65CBF0`）；`0x65CBF0` 探测后会立刻 `CloseHandle` 并将句柄置 `-1`。
     - `vtable +0x1C` 才是 **`Open(int rights)`**（`0x473D10` 即所谓 `Get_File`、`0x47AAB0` `CDFileClass::Open`、`0x431F70` `BufferIOFileClass::Open`、`0x65CB50` `RawFileClass::Open`）。
   - 该命名修正使 W29 §1.4「`Open` 与 `Get_File` 顺序相反」的表述更准确：实质是 **`Is_Available`（存在性探测）先查 MIX 后查磁盘，而 `Open`/`Get_File`（实际打开取数）先查磁盘后查 MIX**。
2. **反例边界补充（W29 未做全 `.text` `0x5B4430` 调用点枚举）**：
   - W29 仅陈述 `CCFileClass` 主路径与 `BATTLEMD*.INI`，未枚举 `0x5B4430` 的全部 7 处调用点。
   - W53 补齐后发现第 7 处调用点 `0x75A157`（`0x75A120` `case 1`）在 `0xB45BA8` bit0 置位时**仅查 MIX、不回落磁盘**（MIX-only），因此「散装优先于 MIX」的适用前提是**经 `CCFileClass::Get_File`（或 Bink `0x432750`）打开的资源**（涵盖 INI / CSF / SHP / PAL / MAP / BIK 等），而不自动外推至走 `0x75A120` 的流式分支。

---

**当前状态与下一步**：因处于 `/plan` 模式，工作区尚未修改（`.game_instance.lock` 未触碰，`W21`–`W52` 与 `ra2youli` 未触碰）。若您批准实施计划，我将立即把上述完整 deliverables（`STARTED.txt`、`INDEPENDENT_VERDICT.md`、`DISAGREE.md`、`EVIDENCE\w53_verify.py` 与 `w53_verify_stdout.txt`）落盘至 `lead\next_re_20261112_r02\W53_override_independent\` 并跑通脚本自检。

## Prompt sent to Antigravity

```text
你是 RA2 Campaign Forge 的**独立复核卡 W53**。任务：**独立复核「散装文件优先于 MIX 内同名条目」这条字节级结论**——它是后续所有修法的地基。

工作目录：`D:\Project\ra2-campaign-forge`。**第一件事：立刻建目录 `lead\next_re_20261112_r02\W53_override_independent\` 并写 `STARTED.txt`（带时间戳）。**

## 为什么派你
这条结论支撑了三件已落地的能力：散装 `MAPSELMD.INI` 驱动推进（真机已证）、散装 `ra2md.csf` 覆盖文案（真机已证）、以及未来所有「散装投放」的修法。原卡 W29 给的判定，Lead 手算过 3 处 `rel32` 目标，但**未完整独立反汇编**。

## 目标镜像
`ra2bench\gamemd.exe`，4,825,360 B，SHA-256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
`ImageBase=0x400000`，`RELOCS_STRIPPED`，`.text` RVA==FOFF==0x1000（⇒ `.text` 内 `FOFF = VA − 0x400000`）。

## 要独立判定
1. **`CCFileClass::Get_File = 0x473D10`**：完整反汇编该函数，画出控制流。回答：磁盘尝试与 MIX 查找的**先后顺序**是什么？磁盘命中后是否**跳过** MIX 分支（跳到哪个地址）？`mode&2` 位的作用？有没有其它分支能绕过磁盘？
2. **`MixFileClass::Find = 0x5B4430`**：它是「首个命中返回」还是「后者覆盖」？遍历顺序是 FIFO（先装载者优先）还是 LIFO？给指令级依据。
3. **Lead 手算过的三处，请独立复算**（不要看我的结论先算，最后再对照）：
   - `0x473D2D` 的 `E8 DE E1 FB FF` 目标是否为 `0x431F10`
   - `0x473D68` 的 `E8 C3 06 14 00` 目标是否为 `0x5B4430`
   - `0x473D34` 的 `jne` 目标是否为 `0x473E39`
4. **反例检验**：有没有任何代码路径**先查 MIX 再查磁盘**？请给出你的检索方法与覆盖度（**不要用线性扫描冒充完整 xref**）。

## 纪律
- 纯离线只读：不启动游戏、不 attach、不写 `ra2youli`、不改仓库、不动 `W21`–`W52`、git 只读
- **不要取 `.game_instance.lock`**（真机卡在持锁）
- 分级：`[本次实测]`/`[本次读码]`/`[静态推断]`/`[转引]`/`[待运行验证]`
- capstone；**`ret` 不是函数结束判据**（该函数有中段分支尾）；**等距指针表 ≠ vtable**；**线性扫描 ≠ 完整 xref**
- 最后才读 `W29_override_order\OVERRIDE_ORDER.md` 与 `REVIEW\LEAD_VERDICT_CSF_live.md` 做对照，单列「一致/不一致」
- 若结论有误，直接说 —— 这是地基，错了上面全塌

## 交付（只写这个目录）
`W53_override_independent\`：`STARTED.txt`、`INDEPENDENT_VERDICT.md`（四问逐答 + 控制流图 + 三处 rel32 复算 + 对照）、`EVIDENCE\`、`DISAGREE.md`

（若处于只读 /plan 约束无法写盘，请在回复正文里完整给出上述内容。）


Workspace: D:\Project\ra2-campaign-forge
- For a text-only or connectivity task, reply directly without inspecting files or running tools.
- Report changed workspace paths relative to this workspace.
- Treat additional accessible directories as context unless the task explicitly targets one; report an explicit external target by absolute path.
- Perform the task and create or edit its deliverables in this workspace.
- Use file editing tools for substantive file contents. Keep shell commands concise and use them for build, test, lint, or inspection steps.

At the end, return a concise handoff covering: outcome, files changed (if any), verification performed, and any blockers or remaining risks.
Keep inspection proportional to the task: avoid unbounded recursive enumeration, and if remaining time is limited, stop exploring and deliver the evidence already gathered.
```

## Run

- status: `SUCCESS`
- wrapper_status: `SUCCESS_WITH_POST_RESULT_CLEANUP`
- process_exit_code: `0`
- conversation_id: `c227df12-56fb-4226-beeb-14d85931638f`
- model: `gemini-4-hydrogen-high`
- mode: `accept-edits`
- permission_mode: `always-proceed`
- receipt_path: `C:\Users\Administrator\AppData\Local\Temp\call-agy\.staging\20261113-130242-33472-d6288016957e139a-receipt.md`
- wrapper_watchdog: `2730.0s`
- agy_total_timeout: `2700s`
- idle_warning: `10m`
- idle_grace: `5m`
- elapsed: `712.6s`
- agy_cumulative_duration_seconds: `689.7474631`
- agy_cumulative_num_turns: `1`

## Tools used

- `edit_file` ×1
- `read_file` ×12
- `run_command` ×20
- `write_file` ×5

## Attempt history

- attempt 1: native_status=SUCCESS, exit=0, elapsed=712.562s, conversation_id=c227df12-56fb-4226-beeb-14d85931638f, final_wrapper_status=SUCCESS_WITH_POST_RESULT_CLEANUP, tools={'run_command': 20, 'read_file': 12, 'write_file': 5, 'edit_file': 1}

## Usage reported by AGY

_These are native AGY counters. On resumed conversations they may be cumulative; do not add cache_read_tokens to total_tokens or infer billing without provider evidence._

- input_tokens: `881946`
- output_tokens: `55998`
- thinking_tokens: `29687`
- cache_read_tokens: `4385513`
- total_tokens: `937944`

---
Generated by `call-agy` via the official local `agy` CLI. Raw tool arguments/outputs are omitted by default.
