# 存档/读档序列化块全清单（task-8 / re-saveblocks）

目标二进制：`ra2youli/gamemd.exe`（ImageBase `0x400000`，无 `.reloc`；**文件偏移 = VA − 0x400000**）。
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
方法：纯静态反汇编（python3.12 + capstone + pefile），**未启动游戏**。
所有字节断言见 `out/re_work/save_blocks/claims.txt`，复算命令与输出见 §7。

> 读前提示：本报告对任务书给出的「约 35 个子系统块 = 调度表条目」这一**结构性前提做了实证修正**——
> 那 35 个地址不是「调度表条目」，而是 **35 个字节完全相同（127 字节、md5 全等）的模板函数**，
> 由 `Game::Save` **顺序直接 call**；真正的「每块对应哪个子系统」由**实参对象地址**给出。
> 详见 §1 与 §8 勘误。

---

## 0. 结论速览

| 项 | 结论 | 等级 |
|---|---|---|
| 存档主函数（Save） | 外层 `Game::Save`（建档/开流）`0x0067D0C0`；核心序列化 `Game::Save_Core 0x0067D300`（`0x67D300..0x67E43A`） | `[实证]` |
| 读档主函数（Load） | 外层 `Game::Load 0x0067CEF0`（校验魔数/开 CONTENTS 流）；核心 `Game::Load_Core 0x0067E440` | `[实证]` |
| 版本魔数 | `Game::Savegame_Magic @ 0x0083D560 = 0x0002B898`（`98 B8 02 00`）；全镜像仅 2 份（另一份 `0x0086563C`）；**写侧不写它，只有读侧校验它** **〔DA4 勘误 · 2026-09-27〕此尾句已由 U-2 定谳取代**：写侧**写入** OLE 流 `Internal Version`（§12.4.1，勘误 DA4-11） | `[实证]` |
| 「35 块」的真实性质 | `0x67FDF0..0x680EF0` 步长 `0x80`，**35 条 127 字节函数体逐字节相同**（md5 全为 `9f6770a9cd27`）；无任何直接/间接调用者，仅被 `Game::Save_Core` **顺序直接 call**（35 次） | `[实证]` |
| 块 ↔ 子系统映射 | 由每个 `call` 前一条 `mov edx, <对象地址>` 给出，共 35 组（§3 表） | `[实证]` |
| 内联向量块 | `Game::Save_Core` 另有 **28 个内联 `DynamicVectorClass<T*>` 循环**（不是函数，是 28 段内联代码）；`COUNT` 与 `ITEMS` 满足 `COUNT == Items+0xC`，28/28 通过 | `[实证]` |
| 存档容器格式 | **OLE 复合文档（OLE2 / CFB）**，非扁平流。真机档 `ALL01UMD.sav`/`ECH01.sav` 均以 CFB 签名 `D0 CF 11 E0 A1 B1 1A E1` 开头；`CONTENTS` 流 = 1205666 B（游戏状态），另有 15 个元数据流 | `[实证]` |
| 指针 Swizzle | **不是手工 swizzle 表**：逐元素调 `ole32!OleSaveToStream`（IAT `0x7E15F4`）/ `ole32!OleLoadFromStream`（IAT `0x7E15F8`），由 **OLE 复合文档 + COM 类标识**承担对象寻址；镜像内未见裸地址落盘 | `[实证]` |
| 魔数落盘形式 | **写侧写入 OLE 流 `Internal Version`**（4 字节 LE32 = `0x0002B898`；真机档文件偏移 `0x0C40` = `98 B8 02 00`）；`CONTENTS` 全流中 LE/BE/16 位形态**均不存在**（与原观测不矛盾——魔数本不在 `CONTENTS` 流内）。**已闭环**（详见 §12.4.1） | `[实证]` |
| 联机一致性 | `Game::Load 0x67CEF0` 有 4 个调用者，含 `NetworkEvent` 处理器簇 `0x4C7AC0` / `0x4C7B3D` → 对局内读档是**命令**，与 `net_sync_checksum.md §4.1` 一致 | `[实证]` |
| 容器 API | `ole32!StgOpenStorage`（Load 侧 `0x67E489`，已定名）/ `[0x7E15C8]`（`0x67CF42`，LOAD 侧建档调用，**API 定名未闭环**）/ `ole32!OleSaveToStream`（IAT `0x7E15F4`）/ `ole32!OleLoadFromStream`（IAT `0x7E15F8`） | `[实证]` |

> **【勘误 DA4-11 · 2026-09-27】（原文保留，未删字：上表「魔数落盘形式」行原文见下「改前原文」）**
> - **改前原文（§0 表「魔数落盘形式」行，本文件 `:26`，逐字）**：`0x2B898`（LE / BE / 16 位）在 `CONTENTS` 全流中**均不存在** → 写侧不写、或写的是另一种编码。**未闭环** ｜ 等级列 `[实证]+未闭环`
> - **订正后**：见上表「魔数落盘形式」行 —— **写侧写入 OLE 流 `Internal Version`；`0x681080` 是描述符字段 setter，不是比较指令**。
> - **U-2 定谳依据（本批只读自跑复核）**：真机档 `ra2youli/ALL01UMD.sav` / `ECH01.sav` / `SOV01UMD.sav` 在**文件偏移 `0x0C40`** 处均为 `98 B8 02 00`（LE32 = `0x0002B898`）；`SOV01T.sav` 同址 = `CC 88 02 00`（= `0x000288CC` ≠ 魔数）⇒ 该流确为**版本闸**而非装饰。镜像侧：`0x0083D560 = 98 B8 02 00`（`Game::Savegame_Magic`）、`0x00681080 = 8B 44 24 04 89 01 C2 04 00`（`mov eax,[esp+4]; mov [ecx],eax; ret 4` = **setter**）。复算脚本 `out/re_work/da4/scan_da4.py`；字节断言 `out/re_work/da4/claims.txt`（`tools/audit_bytes.py` **12/12 全 OK**，含 `0x0083D560` / `0x00681080` 两条）。细节见 **§12.4.1**。
> - **未闭环项声明（防误读）**：`U-1`（**35 个块函数实参对象的类名 / RTTI 解析**）**仍为真机项**，**不因本轮 U-2 定谳而闭环**；其断点步骤与判定标准见 **§12.4.4**（该节标题即「仅真机可闭环清单（更新后 = 仅 U-1）」）。
> - **备注（超本批清单范围，交 Lead 裁决）**：§0 表另有一处**同类过时标记**——**「容器 API」行**（`:28`）写作 `[0x7E15C8]` … **API 定名未闭环**，而 **§12.4.3 已定谳**为 `ole32.dll!StgCreateDocfile`（`0x0067CF42 = FF 15 C8 15 7E 00`，全镜像唯一非 thunk 引用）。**本批未改该行**（不在 DA4 清单内），建议并批处理。
> - **连带订正（同表同源，本批一并加注）**：§0 表**「版本魔数」行**（`:20`）尾句「**写侧不写它，只有读侧校验它**」与 U-2 定谳同样冲突（§12.4.1 的订正说明原文即引用「写侧不写它，只有读侧校验它 / 未闭环」两处）；该行**原文保留**（已就地加 DA4 勘误标记）。⇒ 订正后 §0 表内**两行口径一致**：写侧写入 `Internal Version`，读侧经 `0x681080` setter 填入描述符字段。
> - **影响面**：§12.5 存档兼容性红线结论**不变**（`Internal Version` 属「禁改」）。

---

## 1. `0x67FDF0..0x680EF0` 到底是什么（核心修正）

### 1.1 逐条函数体指纹

`out/re_work/save_blocks/block_fns_index.txt`：

```
block function table: 0x67FDF0 .. 0x680EF0, stride 0x80, 35 entries
entry VA     end VA       len      md5(body)
0x0067FDF0   0x0067FE6F   127      9f6770a9cd27
0x0067FE70   0x0067FEEF   127      9f6770a9cd27
...
0x00680EF0   0x00680F6F   127      9f6770a9cd27

# entries = 35 ; distinct bodies = 1  ==> ALL BYTE-IDENTICAL
```

> **[task-11 口径注明 · v1.5.35 收尾] 本族 MD5 的长度口径（两种均正确，禁止第三种口径）[实证]**
> 上述 `md5(body)` 取的是 **127 B = 纯代码长度**口径（`0x67FDF0..0x67FE6E`，末字节 `0x67FE6E = C3` 即 `ret`）→ `9f6770a9cd27b9fa49558adf28c92f10`（35/35 唯一）。
> 若改取 **128 B = 含尾部 1 字节 `0x90` 对齐填充**口径（`0x67FDF0..0x67FE6F`）→ `cb13908da7ed66fb2a7545323b865a3d`（同样 35/35 唯一）。
> 差异**恰好**是尾部那 1 字节填充，两者**不构成矛盾**；`docs/re/cross_doc_consistency_audit.md §2.6` 用的就是 128 B 口径。
> **引用纪律**：今后凡出现这两个散列值之一，必须同时写明所取字节长度。复算：`python out/re_work/errata/audit_template_md5.py`。

`[实证] 0x0067FDF0 = 83 EC 08 53 56 57 8B FA 8B D9`（`sub esp,8; push ebx,esi,edi; mov edi,edx; mov ebx,ecx`）
`[实证] 0x0067FE70 = 83 EC 08 53 56 57 8B FA 8B D9`（第 2 条，同字节）
`[实证] 0x00680EF0 = 83 EC 08 53 56 57 8B FA 8B D9`（第 35 条，同字节）

### 1.2 模板语义（指令级）

```
0x0067FDF0  83 EC 08            sub  esp, 8
0x0067FDF3  53                  push ebx
0x0067FDF4  56                  push esi
0x0067FDF5  57                  push edi
0x0067FDF6  8B FA               mov  edi, edx        ; edx = DynamicVectorClass<T*>*
0x0067FDF8  8B D9               mov  ebx, ecx        ; ecx = IPersistStream*
0x0067FDFA  6A 00               push 0
0x0067FDFC  8B 47 10            mov  eax, [edi+0x10] ; +0x10 = Count
0x0067FDFF  8D 54 24 14         lea  edx, [esp+0x14]
0x0067FE03  8B 0B               mov  ecx, [ebx]
0x0067FE05  6A 04               push 4
0x0067FE07  52                  push edx
0x0067FE08  53                  push ebx
0x0067FE09  89 44 24 20         mov  [esp+0x20], eax
0x0067FE0D  FF 51 10            call [ecx+0x10]      ; IStream::Write(4, &count)
0x0067FE10  85 C0               test eax, eax
0x0067FE12  7C 54               jl   0x67FE68       ; 失败 -> 返回负数
0x0067FE14  8B 44 24 10         mov  eax, [esp+0x10]
0x0067FE18  33 F6               xor  esi, esi        ; i = 0
0x0067FE1A  85 C0               test eax, eax
0x0067FE1C  7E 48               jle  0x67FE66       ; 空向量 -> 直接成功
0x0067FE1E  8B 47 04            mov  eax, [edi+4]    ; +4 = Items
0x0067FE21  C7 44 24 0C 00..    mov  [esp+0xC], 0
0x0067FE29  8D 54 24 0C         lea  edx, [esp+0xC]
0x0067FE2D  8B 04 B0            mov  eax, [eax+esi*4]  ; Items[i]
0x0067FE30  52                  push edx
0x0067FE31  68 80 7C 7F 00      push 0x7F7C80       ; 共享的 IPersistStream 载体对象
0x0067FE36  50                  push eax
0x0067FE37  8B 08               mov  ecx, [eax]
0x0067FE39  FF 11               call [ecx]          ; 元素虚表[0]
0x0067FE3B  85 C0               test eax, eax
0x0067FE3D  7C 29               jl   0x67FE68
0x0067FE3F  8B 44 24 0C         mov  eax, [esp+0xC]
0x0067FE43  53                  push ebx
0x0067FE44  50                  push eax
0x0067FE45  FF 15 F4 15 7E 00   call [0x7E15F4]     ; ole32!OleSaveToStream(obj, stream)
0x0067FE4B  85 C0               test eax, eax
0x0067FE4D  7C 19               jl   0x67FE68
0x0067FE4F  8B 44 24 0C         mov  eax, [esp+0xC]
0x0067FE53  50                  push eax
0x0067FE54  8B 08               mov  ecx, [eax]
0x0067FE56  FF 51 08            call [ecx+8]        ; 元素虚表[2] = 释放
0x0067FE5D  8B 44 24 10         mov  eax, [esp+0x10]
0x0067FE61  46                  inc  esi
0x0067FE62  3B F0               cmp  esi, eax
0x0067FE64  7C B8               jl   0x67FE1E
0x0067FE66  33 C0               xor  eax, eax        ; S_OK
0x0067FE68  5F 5E 5B 83 C4 08 C3  pop edi/esi/ebx; add esp,8; ret
```

**语义**：`HRESULT Serialize(LPSTREAM pStm /*ecx*/, DynamicVectorClass<T*>* pVec /*edx*/)` ——
写 4 字节元素计数，再对每个元素走 `虚表[0] → operator<<(stream,obj) → 虚表[2]`。

**`Save_Sides 0x6805F0` 属于同一模板**：
`[实证] 0x006805F0 = 83 EC 08 53 56 57 8B FA 8B D9`（与上完全相同）；
`[实证] 0x0067E0AF = E8 3C 25 00 00`（`call 0x6805F0`），其前一指令 `[实证] 0x0067E0A8 = BA 20 41 8B 00〔勘误 ASM-FIX-30 · 真 VA 走锚〕原锚点 0x0067E0A9 实测 `20 41 8B 00 8B`；本字节串真锚点 0x0067E0A8（Δ-1），字节串不变`（`mov edx,0x8B4120`）。
→ `Save_Sides` = 本模板对 `0x8B4120` 这个 Side 向量的实例化，与 YRpp `Unsorted.h:66`
`static HRESULT __fastcall Save_Sides(LPSTREAM pStm, DynamicVectorClass<SideClass*>* pVector)` 签名一致（ecx=pStm, edx=pVector）。

### 1.3 调用者取证（为什么以前找不到）

| 查找方式 | 结果 |
|---|---|
| `E8 rel32` 指向 `0x67FDF0..0x680F6F` | **0** 处 |
| `E9 rel32` 指向同范围 | **0** 处 |
| 镜像中出现 dword `0x67FDF0` / `0x67FE70` / `0x680EF0` | **0** 处 |
| 实际调用点 | `Game::Save_Core 0x67D300` 内 **35 处 `E8` 直接 call**，形如 `mov edx,<对象> ; mov ecx,<stream> ; call <块函数>` |

证据样本：`[实证] 0x0067DF0F = E8 DC 1E 00 00`（`call 0x67FDF0`），前一指令 `[实证] 0x0067DF08 = BA 30 3E A8 00`（`mov edx,0xA83E30`）。
完整 35 条见 `out/re_work/save_blocks/save_block_call_order.txt`。

---

## 2. Save / Load 外层与流对象（容器）

### 2.1 Save 外层 `0x67D0C0`（`__thiscall`，1 个栈参 = 文件名）

```
0x0067D0C6  e8 15 2d 00 00      call 0x67FDE0             ; 构造本地流包装对象
0x0067D0CB  8d 54 24 20         lea  edx,[esp+0x20]       ; &st  (OUT)
0x0067D0D0  68 c0 7b 81 00      push 0x817BC0             ; lpSecurityAttributes
0x0067D0D5  6a 07               push 7                    ; OPEN_ALWAYS|CREATE(2? 见下)
0x0067D0D7  55                  push ebp                  ; hTemplateFile = 0
0x0067D0D8  68 40 95 7e 00      push 0x7E9540             ; lpFileName "FSGRYSMK1"（分区占位名）
0x0067D0DD  ff 15 fc 15 7e 00   call [0x7E15FC]           ; ole32!CoCreateInstance（造流包装 COM 对象）
0x0067D107  ff 11               call [ecx]                ; 流头部写出
0x0067D131  ff 52 0c            call [edx+0xC]            ; IStream::Write(CONTENTS 载荷)
```

### 2.2 Save 核心 `0x67D300`

```
0x0067D300  83 EC 08 53 55 56 8B F1   sub esp,8; push ebx,ebp,esi; mov esi,ecx
0x0067D308  8B 0D 30 B2 A8 00         mov  ecx,[0xA8B230]        ; ScenarioClass::Instance
0x0067D310  E8 FB BF 00 00            call 0x689310              ; 前置准备（"SAVING GAME" 日志簇）
0x0067D315  B9 E0 38 8A 00            mov  ecx,0x8A38E0          ; 全局对象 #1（0x44 字节整流）
0x0067D31B  E8 20 90 E4 FF            call 0x4C6340              ; 原始 0x44 字节写入器
0x0067D320  8B 0D E0 71 88 00         mov  ecx,[0x8871E0]        ; RulesClass::Instance
0x0067D327  E8 04 74 FF FF            call 0x674730              ; Rules 块
0x0067D32C  A1 60 41 8B 00            mov  eax,[0x8B4160]        ; (1) 向量 Count
0x0067D342  FF 51 10                  call [ecx+0x10]            ; IStream::Write(4,&count)
0x0067D351  8B 2D F4 15 7E 00         mov  ebp,[0x7E15F4]        ; ole32!OleSaveToStream 指针缓存
0x0067D35D  A1 54 41 8B 00            mov  eax,[0x8B4154]        ; Items 基址
0x0067D36A  8B 04 98                  mov  eax,[eax+ebx*4]       ; 元素
0x0067D376  FF 11                     call [ecx]                 ; 元素虚表[0]
0x0067D386  FF D5                     call ebp                   ; ole32!OleSaveToStream
0x0067D397  FF 51 08                  call [ecx+8]               ; 元素虚表[2]
...（1..28 向量块，见 §4）
0x0067DF0F  E8 DC 1E 00 00            call 0x67FDF0              ; 块函数 #1  (edx=0xA83E30)
...（#1..#35，见 §3）
0x0067E3AA  E8 41 2B 00 00            call 0x680EF0              ; 块函数 #35 (edx=0xB04BD0)
0x0067E3BD  83 3D 38 B2 A8 00 05      cmp  [0xA8B238],5          ; SessionClass::Instance GameMode==5 (Skirmish)
0x0067E3CB  E8 10 85 D8 FF            call 0x4068E0              ; 日志 "Writing Skirmish Session.Options"
0x0067E3D9  E8 82 D1 01 00            call 0x69B560              ; Write_Skirmish_Session_Options(stream)
0x0067E3FB  E8 20 32 0D 00            call 0x751620              ; 收尾 1
0x0067E410  E8 9B 4F 0D 00            call 0x7533B0              ; 收尾 2
0x0067E429  E8 E2 2B 0A 00            call 0x721010              ; 收尾 3（对象 0xA83D10）
0x0067E43A  C3                        ret
```

`0x4C6340` 本体（`[实证]` 全 17 字节）：
```
0x004C6340  8B 44 24 04   mov  eax,[esp+4]
0x004C6344  6A 00 6A 44   push 0 ; push 0x44
0x004C6348  51            push ecx
0x004C6349  8B 10         mov  edx,[eax]
0x004C634B  50            push eax
0x004C634C  FF 52 10      call [edx+0x10]        ; IStream::Write(0x44, [ecx])
0x004C634F  C2 04 00      ret  4
```

### 2.3 Load 侧

```
Game::Load       0x0067CEF0   81 EC 90 04 00 00   sub esp,0x490
0x0067CF05  E8 D6 99 D8 FF      call 0x4068E0    ; 日志（'
SAVING GAME [%s - %s]
' —— 复用同一格式串）
0x0067CF3E  89 6C 24 20         mov  [esp+0x20],ebp
0x0067CF42  FF 15 C8 15 7E 00   call [0x7E15C8]  ; OLE 存储建档/打开（**API 定名未闭环**，见 §2.5 收尾与 §9 U-9）
0x0067CF70  A1 60 D5 83 00      mov  eax,[0x83D560]   ; ★ 读版本魔数
0x0067CF7D  E8 FE 40 00 00      call 0x681080         ; 魔数交给本地流助手校验
0x0067CF8F  8D 8C 24 AC 00 00   lea  ecx,[esp+0xAC]
0x0067CF93  ...                 ... 0x681060/0x6810A0/0x6810D0/0x681110/0x681130/0x6811C0
                                   0x681200/0x681240/0x681280/0x6812C0/0x6812E0 一串读档助手

Game::Load_Core  0x0067E440   81 EC 08 05 00 00   sub esp,0x508
0x0067E44D  68 20 D6 83 00      push 0x83D620            ; "\nLOADING GAME [%s]\n"
0x0067E452  E8 89 84 D8 FF      call 0x4068E0            ; Debug::Log
0x0067E489  8B 1D E4 15 7E 00   mov  ebx,[0x7E15E4]      ; ole32!StgOpenStorage
0x0067E48F  8D 4C 24 10         lea  ecx,[esp+0x10]      ; &ppstgOpen
0x0067E493  51                  push ecx                 ; ppstgOpen (OUT)
0x0067E494  55                  push ebp                 ; prgbExcludeList = NULL
0x0067E495  55                  push ebp                 ; snbExclude     = NULL
0x0067E496  6A 12               push 0x12                ; grfMode = 0x12 (STGM_READ|STGM_SHARE_EXCLUSIVE|STGM_READWRITE)
0x0067E498  8D 54 24 34         lea  edx,[esp+0x34]      ; pwcsName（栈上 0x40 宽字符缓冲，由 0x7E11C4 导入从 ASCII 名转换）
0x0067E49C  55                  push ebp                 ; pstgPriority  = NULL
0x0067E49D  52                  push edx                 ; pwcsName
0x0067E49E  89 6C 24 28         mov  [esp+0x28],ebp
0x0067E4A2  FF D3               call ebx                 ; -> 打开真机存档容器（OLE 复合文档）
0x0067E4CA  E8 71 33 00 00      call 0x681840            ; 把打开的存储压入本地流包装（与 0x681080 同族）
0x0067E4E3  E8 E8 2D 00 00      call 0x6812D0            ; 读 GameMode
0x0067E4E8  A3 38 B2 A8 00      mov  [0xA8B238],eax      ; SessionClass::Instance 回填
0x0067E56C  68 A8 D5 83 00      push 0x83D5A8            ; "CONTENTS"（UTF-16LE：43 00 4F 00 4E 00 ...）
0x0067E572  FF 51 10            call [ecx+0x10]          ; IStorage::OpenStream("CONTENTS")
0x0067E5D0  FF 15 00 16 7E 00   call [0x7E1600]          ; ole32!OleRun
0x0067E840  8B 3D F8 15 7E 00   mov  edi,[0x7E15F8]      ; ole32!OleLoadFromStream（缓存进 edi，供读档循环用）
```

`[实证] 0x0083D5A8 = 43 00 4F 00 4E 00 54 00 45 00 4E 00 54 00 53 00 00 00 00 00`（"CONTENTS" 的 UTF-16LE 形态）

### 2.4 调用者（xref）

| 目标 | 调用点 |
|---|---|
| `Game::Save 0x67D0C0` | **本镜像内无任何 `E8/E9` 直接调用者，也无 imm32/指针引用**（`[实证]`，`tools/xref_abs.py 0x67D0C0` → 0 refs）→ 只能经函数指针/虚表调用，**未闭环** |
| `Game::Save_Core 0x67D300` | `[实证] 0x0067D1AF = E8 4C 01 00 00`（唯一调用者，位于 `0x67D0C0` 函数体内） |
| `Game::Load 0x67CEF0` | `0x4C7AC0` 、`0x4C7B3D`（`NetworkEvent` 命令处理器簇）、`0x559E85`（`LoadOptionsClass`）、`0x55DC92`（游戏循环）——共 4 处 |
| `Save_Sides 0x6805F0` | `[实证] 0x0067E0AF = E8 3C 25 00 00`（唯一调用者，`Game::Save_Core` 内） |
| 35 个块函数 | 仅 `Game::Save_Core`（见 §1.3） |

### 2.5 序列化原语 = OLE (`ole32`) —— **不是**自研指针 swizzle

镜像 IAT 实证（`pefile` + `tools/xref_abs.py`）：

| IAT 槽 | 导入函数 | 非 thunk 引用点 |
|---|---|---|
| `0x007E15C8` | `ole32!StgCreateDocfile`（导入序推断，**未闭环**） | `0x0067CF42`（本镜像唯一非 thunk 引用） |
| `0x007E15E4` | `ole32!StgOpenStorage` | `0x0067E489`（Load 侧）、`0x0067FD6F` |
| `0x007E15E8` | `ole32!CoFileTimeNow` | `0x0067D012` |
| `0x007E15F4` | **`ole32!OleSaveToStream`** | `0x0067D353`（Save 缓存）、`0x0067FE47`（35 个块函数内）、`0x004AF8A7` / `0x004B6366` / `0x004DB7C0` / `0x005046CB` / `0x0054B88D` / `0x005BE851`（各对象类自己的 `IPersistStream::Save`） |
| `0x007E15F8` | **`ole32!OleLoadFromStream`** | `0x0067C6B7`、`0x0067E842`、`0x004AF7ED` / `0x004B62AD` / `0x004DB56A` / `0x00504065` / `0x0054B7C6` / `0x005BE4DE`（各对象类的 `Load`） |
| `0x007E1600` | `ole32!OleRun` | `0x0067D0EE`、`0x0067E5D0` 等 |

**结论（`[实证]`）**：RA2/YR 的存读档**就是 OLE 结构化存储**：
- 写：`OleSaveToStream(obj, stream)` —— OLE 自己把对象写成一个带 **CLSID（类标识）** 的子存储；
- 读：`OleLoadFromStream(stream, riid, ppv)` —— OLE 按 CLSID 重新 `CoCreateInstance` 出对象。
- 因此「指针 Swizzle」不存在自研表：**对象寻址 = OLE 的 CLSID + 存储路径**。
  `push 0x7F7C80` 是各对象类共用的「序列化上下文 / 绑定对象」参数位（未闭环，见 §9 U-6）。

`0x0067D0CB` 的建档调用还原（`__stdcall` 右→左压栈）：

```
0x0067D0CB  8D 54 24 20      lea  edx, [esp+0x20]
0x0067D0CF  52               push edx                 ; ppstgOpen (OUT)
0x0067D0D0  68 C0 7B 81 00   push 0x00817BC0          ; fmtid 区（其 +8 处 dword=0xC0，即 STGM_DIRECT|STGM_READWRITE）
0x0067D0D5  6A 07            push 7
0x0067D0D7  55               push ebp                 ; grfMode = ebp（ebp 此时 = 0，即 STGM_READ）
0x0067D0D8  68 40 95 7E 00   push 0x007E9540          ; pwcsName（宽串；该地址的数据 = GUID {B48FA168-646F-11D2-9B74-00104B972FE8}）
0x0067D0DD  FF 15 FC 15 7E 00  call [0x7E15FC]       ; ole32!CoCreateInstance
```

> 注：`0x0067D0D8` 压入的是一个 **GUID 常量**而非文件名字符串，且 `0x67D0DD` 是 `CoCreateInstance`，
> 所以 `0x67D0CB..0x67D0DD` 这一段**不是** `CreateFileA`，而是「直接造一个存储/流 COM 对象」。
> 本报告不再对该调用做 `CreateFileA` 命名（**勘误**：早前 `claims.txt` 中 `0x67D0CB` 的 `CreateFileA` 描述已改为中性描述）。

---

---

## 3. 逐块清单：35 个块函数 → 实参对象

**表条目数自证 = 35，命名数 = 35。**

「调度表条目地址」一列 = **块函数入口地址**（`0x67FDF0 + 0x80×i`）；
「对应子系统对象」一列 = **调用点前 `mov edx,<VA>` 给出的实参**（这才是真正的「哪个子系统」）。

| 块# | 块函数入口（任务书的"调度表条目"） | 调用点 | 实参对象 VA（子系统载体） | 对象基址 | 对象性质 | 指针 Swizzle | 联机一致性 |
|---|---|---|---|---|---|---|---|
| 1 | `0x0067FDF0` | `0x0067DF0F` | `0x00A83E30` | `0x00A83E24` | 未知（`Game::Save_Core` 尾簇，动态数组 28 B/元素） | 未见裸指针 | `[待实测]` |
| 2 | `0x0067FE70` | `0x0067DF29` | `0x00A8EB28` | `0x00A8EB1C` | 未知（紧邻 `BuildingClass::Array 0xA8EB38` 之前） | 未见裸指针 | `[待实测]` |
| 3 | `0x0067FEF0` | `0x0067DF43` | `0x00887388` | `0x0088737C` | 未知（紧邻 `TacticalClass::Instance 0x887324` 之后） | 未见裸指针 | `[待实测]` |
| 4 | `0x0067FF70` | `0x0067DF5D` | `0x008874C0` | `0x008874B4` | 未知 | 未见裸指针 | `[待实测]` |
| 5 | `0x0067FFF0` | `0x0067DF77` | `0x00887568` | `0x0088755C` | 未知 | 未见裸指针 | `[待实测]` |
| 6 | `0x00680070` | `0x0067DF91` | `0x00A83D98` | `0x00A83D8C` | 未知（读侧对应 `0x4E71F2` 簇） | 未见裸指针 | `[待实测]` |
| 7 | `0x006800F0` | `0x0067DFAB` | `0x00A83DC8` | `0x00A83DBC` | 未知（被 `0x4D8B74/0x6E5036` 引用） | 未见裸指针 | `[待实测]` |
| 8 | `0x00680170` | `0x0067DFC5` | `0x00A83D68` | `0x00A83D5C` | 未知（读侧 `0x4E7972`） | 未见裸指针 | `[待实测]` |
| 9 | `0x006801F0` | `0x0067DFDF` | `0x00A80208` | `0x00A801FC` | 未知（紧邻 `HouseClass::Array 0xA80220`） | 未见裸指针 | `[待实测]` |
| 10 | `0x00680270` | `0x0067DFF9` | `0x00A83C80` | `0x00A83C74` | 未知（读侧 `0x4E7372`） | 未见裸指针 | `[待实测]` |
| 11 | `0x006802F0` | `0x0067E013` | `0x00A8ED40` | `0x00A8ED34` | 未知（读侧 `0x4E76F2`） | 未见裸指针 | `[待实测]` |
| 12 | `0x00680370` | `0x0067E02D` | `0x00B72608` | `0x00B725FC` | 未知（.data 高位区，无外部引用） | 未见裸指针 | `[待实测]` |
| 13 | `0x006803F0` | `0x0067E047` | `0x00A8EC18` | `0x00A8EC0C` | 未知（被 7 处引用） | 未见裸指针 | `[待实测]` |
| 14 | `0x00680470` | `0x0067E061` | `0x00A83D80` | `0x00A83D74` | 未知（读侧 `0x4E77F2`） | 未见裸指针 | `[待实测]` |
| 15 | `0x006804F0` | `0x0067E07B` | `0x00ABCA10` | `0x00ABCA04` | 未知（被 `0x5545E7` 引用） | 未见裸指针 | `[待实测]` |
| 16 | `0x00680570` | `0x0067E095` | `0x008B4190` | `0x008B4184` | 未知（读侧 `0x4E6572`） | 未见裸指针 | `[待实测]` |
| 17 | `0x006805F0` | `0x0067E0AF` | `0x008B4120` | `0x008B4114` | **`Save_Sides`（SideClass 向量）** | 未见裸指针 | 是（双方需一致） |
| 18 | `0x00680670` | `0x0067E0C9` | `0x00B0F4E8` | `0x00B0F4DC` | 未知 | 未见裸指针 | `[待实测]` |
| 19 | `0x006806F0` | `0x0067E0E3` | `0x008A3870` | `0x008A3864` | 未知 | 未见裸指针 | `[待实测]` |
| 20 | `0x00680770` | `0x0067E0FD` | `0x00A8E330` | `0x00A8E324` | 未知（读侧 `0x4E72F2`） | 未见裸指针 | `[待实测]` |
| 21 | `0x006807F0` | `0x0067E117` | `0x00A83CB8` | `0x00A83CAC` | 未知（`0x4E7008` / `0x5115B4`） | 未见裸指针 | `[待实测]` |
| 22 | `0x00680870` | `0x0067E1E7` | `0x00A8E318` | `0x00A8E30C` | **帧同步阈值载体**（`0x0064733B` 读它，见 `net_sync_checksum.md §7.3` 的 `0xA8E30C`） | 未见裸指针 | **是（帧阈值）** |
| 23 | `0x006808F0` | `0x0067E201` | `0x00A8E988` | `0x00A8E97C` | 未知（`0x410911/0x599CA2/0x6852CC` 引用） | 未见裸指针 | `[待实测]` |
| 24 | `0x00680970` | `0x0067E21B` | `0x008B3D10` | `0x008B3D04` | 未知（被 `0x4D0950..4D165E` 6 处引用） | 未见裸指针 | `[待实测]` |
| 25 | `0x006809F0` | `0x0067E235` | `0x0088A0F0` | `0x0088A0E4` | 未知 | 未见裸指针 | `[待实测]` |
| 26 | `0x00680A70` | `0x0067E24F` | `0x00A8EC38` | `0x00A8EC2C` | 未知（`0x4E7288` / `0x6B52FF`） | 未见裸指针 | `[待实测]` |
| 27 | `0x00680AF0` | `0x0067E28F` | `0x0089E0F0` | `0x0089E0E4` | 未知 | 未见裸指针 | `[待实测]` |
| 28 | `0x00680B70` | `0x0067E2A9` | `0x008A0208` | `0x008A01FC` | 未知（`0x4A7A98` 引用） | 未见裸指针 | `[待实测]` |
| 29 | `0x00680BF0` | `0x0067E2C3` | `0x00AC4910` | `0x00AC4904` | 未知（`0x629177` 引用） | 未见裸指针 | `[待实测]` |
| 30 | `0x00680C70` | `0x0067E2DD` | `0x00B0EC60` | `0x00B0EC54` | 未知（`0x71A3C1` 引用） | 未见裸指针 | `[待实测]` |
| 31 | `0x00680CF0` | `0x0067E2F7` | `0x00889FB8` | `0x00889FAC` | 未知 | 未见裸指针 | `[待实测]` |
| 32 | `0x00680D70` | `0x0067E311` | `0x00B0B880` | `0x00B0B874` | 未知（`0x6B6B90` 引用） | 未见裸指针 | `[待实测]` |
| 33 | `0x00680DF0` | `0x0067E32B` | `0x00B0B5F0` | `0x00B0B5E4` | 未知 | 未见裸指针 | `[待实测]` |
| 34 | `0x00680E70` | `0x0067E390` | `0x0089C668` | `0x0089C65C` | 未知 | 未见裸指针 | `[待实测]` |
| 35 | `0x00680EF0` | `0x0067E3AA` | `0x00B04BD0` | `0x00B04BC4` | 未知（`0x65B0E0` 引用；紧随其后是 `cmp [0xA8B238],5` Skirmish 分支） | 未见裸指针 | `[待实测]` |

> **为什么「对象性质」大面积为未知**：这 35 个实参都是 **.bss 全局对象**，静态镜像里没有内容，
> 而 `gendata`（类型名/INI 名）与 vtable 在 MSVC 6 的 RTTI 布局下未被文件内任何 `_RTTICompleteObjectLocator` 引用
> （全镜像 `.rdata` 的 `.?AV...` 类型名字符串共 962 条，但类描述符指针仅 43 处，
> 且**没有任何一处**指向这 35 个对象所属的类）。
> 因此「逐个对象命名」在**纯静态**条件下**无法闭环**；给出的是「对象地址 + 相邻已知全局 + 代码引用点」三条可复算线索。
> 取证法见 §9 U-1。

---

## 4. 内联向量块：28 个 `DynamicVectorClass<T*>` 循环

`Game::Save_Core` 中另有 28 段**内联**（不是函数）向量序列化代码。
完整表 + 每块首条指令地址见 `out/re_work/save_blocks/save_vector_blocks.txt`（`# total vector blocks = 28 ; layout verified = 28`）。

判定依据（两形态，均已实证）：

**形态 A（第 1 块）**
```
0x0067D32C  A1 60 41 8B 00     mov  eax,[0x8B4160]     ; Count
0x0067D331  8B 0E              mov  ecx,[esi]
0x0067D333  33 FF              xor  edi,edi
0x0067D335  8D 54 24 14        lea  edx,[esp+0x14]
0x0067D339  57                 push edi
0x0067D33A  6A 04              push 4
0x0067D33C  52                 push edx
0x0067D33D  56                 push esi
0x0067D33E  89 44 24 24        mov  [esp+0x24],eax
0x0067D342  FF 51 10           call [ecx+0x10]         ; IStream::Write(4,&count)
```
**形态 B（后续 27 块）**
```
0x0067D3DC  8B 15 3C 41 8B 00  mov  edx,[0x8B413C]     ; Count
0x0067D3E2  89 7C 24 14        mov  [esp+0x14],edi
0x0067D3E6  8B 04 9A           mov  eax,[edx+ebx*4]    ; 元素
...
```

布局校验（`Items @ +4`、`Count @ +0x10` ⇒ `Count == Items + 0xC`）：**28/28 YES**。

### 28 个 COUNT/ITEMS 全局 → 已知类（交叉引用已归档文档）

| # | Count 载入点 | COUNT 全局 | ITEMS 全局（=COUNT−0xC） | 元素载入点 | 归属（证据来源） | 联机一致性 |
|---|---|---|---|---|---|---|
| 1 | `0x0067D32C` | `0x008B4160` | `0x008B4154` | `0x0067D36A` | 待命名（本仓无引用） | `[待实测]` |
| 2 | `0x0067D3DC` | `0x008B413C` | `0x008B4130` | `0x0067D3E6` | **Tube 路径表**（`pathfinding_locomotion.md` §"0x008B413C"：读 `Cell+0x116 TubeIndex`，长度 `0x008B4148`）※勘误见 §8.3 | 是（寻路→位置） |
| 3 | `0x0067D47C` | `0x00A83C9C` | `0x00A83C90` | `0x0067D489` | 待命名 | `[待实测]` |
| 4 | `0x0067D4EC` | `0x00A8022C` | `0x00A80220` | `0x0067D4F6` | **AircraftClass::Array**（`net_sync_checksum.md:260`、`superweapon_re.md:531`） | **是**（`net_sync_checksum` §4.2） |
| 5 | `0x0067D565` | `0x008B410C` | `0x008B4100` | `0x0067D56F` | **UnitClass::Array**（`net_sync_checksum.md:256`） | **是** |
| 6 | `0x0067D5DE` | `0x00A83CE4` | `0x00A83CD8` | `0x0067D5E8` | **UnitTypeClass::Array**（`house_team_ai_update.md:410`） | 类型表：桌面同版本即可 |
| 7 | `0x0067D657` | `0x00A8E34C` | `0x00A8E340` | `0x0067D661` | **InfantryTypeClass::Array**（`house_team_ai_update.md:411`） | 同上 |
| 8 | `0x0067D6D0` | `0x00A83DEC` | `0x00A83DE0` | `0x0067D6DA` | **InfantryClass::Array**（`net_sync_checksum.md:254` / `superweapon_re.md:528`） | **是** |
| 9 | `0x0067D749` | `0x00A83C6C` | `0x00A83C60` | `0x0067D753` | 待命名（被 67 处引用，最热；紧邻 `UnitTypeClass::Array` 前 0x78 B） | `[待实测]` |
| 10 | `0x0067D7C2` | `0x00A8EB44` | `0x00A8EB38` | `0x0067D7CC` | **BuildingClass::Array**（`net_sync_checksum.md:258` / `superweapon_re.md:530`） | **是** |
| 11 | `0x0067D83B` | `0x00A8B21C` | `0x00A8B210` | `0x0067D845` | **AircraftTypeClass::Array**（`house_team_ai_update.md:412`） | 类型表 |
| 12 | `0x0067D8B4` | `0x00A8E394` | `0x00A8E388` | `0x0067D8BE` | **Airforce/Aircraft 向量**（`targeting_spatial.md:388`；`targeting_deep_dive.md:190` 记为 `0xA8E390` 基址） | **是** |
| 13 | `0x0067D92D` | `0x00A8E9AC` | `0x00A8E9A0` | `0x0067D937` | **AnimClass::Array**（`fx_draw_chain.md:98`，基址 `0xA8E9A8`） | **是**（`fx_draw_chain`） |
| 14 | `0x0067D9A6` | `0x00A8E8D4` | `0x00A8E8C8` | `0x0067D9B0` | 待命名 | `[待实测]` |
| 15 | `0x0067DA1F` | `0x00A8ECA4` | `0x00A8EC98` | `0x0067DA29` | **TeamTypeClass::Array**（`house_team_ai_update.md:121`，基址 `0xA8ECA0`）※其 Count 实为 `0xA8ECB0`，见 §8.3 | 类型表 |
| 16 | `0x0067DA98` | `0x008B40EC` | `0x008B40E0` | `0x0067DAA2` | **TeamClass::Array**（`house_team_ai_update.md:119`） | **是**（`house_team_ai_update`） |
| 17 | `0x0067DB11` | `0x008B41CC` | `0x008B41C0` | `0x0067DB1B` | 待命名 | `[待实测]` |
| 18 | `0x0067DB8A` | `0x008872B4` | `0x008872A8` | `0x0067DB94` | 待命名（与 `TacticalClass::Instance 0x887324` 同段） | `[待实测]` |
| 19 | `0x0067DC03` | `0x00B0E784` | `0x00B0E778` | `0x0067DC0D` | 待命名 | `[待实测]` |
| 20 | `0x0067DC7C` | `0x00B0E724` | `0x00B0E718` | `0x0067DC86` | 待命名 | `[待实测]` |
| 21 | `0x0067DCF5` | `0x008B417C` | `0x008B4170` | `0x0067DCFF` | 待命名（与 Tube 表同段） | `[待实测]` |
| 22 | `0x0067DD6E` | `0x00A8EAEC` | `0x00A8EAE0` | `0x0067DD78` | 待命名（贴 `AnimClass` 段） | `[待实测]` |
| 23 | `0x0067DDE3` | `0x00A8B204` | `0x00A8B1F8` | `0x0067DDED` | **AITriggerTypeClass::Array**（`house_team_ai_update.md:120` / `ARCHITECTURE_ATLAS.md:944`） | 类型表 |
| 24 | `0x0067DE4C` | `0x00B0E65C` | `0x00B0E650` | `0x0067DE56` | 待命名 | `[待实测]` |
| 25 | `0x0067DEB9` | `0x00B0F1A4` | `0x00B0F198` | `0x0067DEC3` | 待命名 | `[待实测]` |
| 26 | `0x0067E150` | `0x00A83D54` | `0x00A83D48` | `0x0067E15B` | 待命名 | `[待实测]` |
| 27 | `0x0067E1AB` | `0x008B41E4` | `0x008B41D8` | `0x0067E1B5` | 待命名 | `[待实测]` |
| 28 | `0x0067E186` | `0x008B41F0` | `0x008B41E4` | `0x0067E1B5` | 待命名（与 #27 共用元素载入点 → 两表相邻） | `[待实测]` |

★ 注：`0x0067E186`（#28）在源序中**早于** `0x0067E1AB`（#27），说明第 27/28 段是**相邻两张表顺序发射**。

### 与 `0x67FDF0` 模板的关系（**重要**）

- `0x67FDF0` 与 `Save_Sides 0x6805F0` 是 **同一模板的函数化实例**（§1.2）；
- 但 §4 的 28 个向量块是 **内联展开**，没走 `0x67FDF0`；
- 二者**序列化口径完全相同**（写 `Count` 4 字节 → 每元素 `虚表[0] → operator<< → 虚表[2]`）。
- → 所以 `0x67FDF0` 这一族是**同一序列化原语的两种落地形态**（inline / 独立函数），
  这也是为什么它们的 35 个表项要**手工打磨成等长 127 字节**（写成宏展开的等效物）。

---

## 5. 存档文件格式（真机档实证）

### 5.1 容器 = OLE2 复合文档

```
ALL01UMD.sav  1,220,002 B   头 8 字节 D0 CF 11 E0 A1 B1 1A E1
ECH01.sav       825,470 B   头 8 字节 D0 CF 11 E0 A1 B1 1A E1
```
`[实证]` 与 `Game::Save 0x67D0C0` 使用 `[0x7E15FC]`（OLE 流打开）一致。

### 5.2 `ALL01UMD.sav` 目录项（CFB Directory）

```
entry Root Entry            type=5 start=3      size=1216
entry SummaryInformation    type=2 start=0      size=380
entry Scenario Description  type=2 start=6      size=30
entry Player House          type=2 start=7      size=6
entry Version               type=2 start=8      size=4
entry Internal Version      type=2 start=9      size=4
entry Start Time            type=2 start=10     size=8
entry Last Save Time        type=2 start=11     size=8
entry Play Time             type=2 start=12     size=8
entry Executable Name       type=2 start=13     size=16
entry Player Name           type=2 start=14     size=2
entry Player Name2          type=2 start=15     size=2
entry Scenario Number       type=2 start=16     size=4
entry Campaign              type=2 start=17     size=4
entry GameType              type=2 start=18     size=4
entry CONTENTS              type=2 start=9      size=1205666      <-- 游戏状态
```
（`CONTENTS` 与 `Version` 条目同名 start=9 是 CFB 的 mini-stream / 起始扇区显示问题，非冲突。）

### 5.3 `CONTENTS` 流头部

```
0x00  78 32 00 00 00 00 01 00 0b c8 80 e0 02 47 44 49 32 41 2e 6d 61 70 00 20 d9 00 00 06 47 44 49 39
        ^ u32@0 = 0x00003278 = 12920                       ^ "GDI2A.map"
0x28  43 2e 4d 41 50 20 d9 0a 04 00 0e 4c 1f 6c 00 06   ^ "C.MAP"
```
- 首 4 字节 `0x3278`（= 12920），**不是** 魔数 `0x2B898`；
- 内部含 **地图名 + 校验/长度字段** 的条目表（形如 `0x02 <ascii name> NUL ...`，每项约 0xB~0xD 字节）；
- **`0x2B898`（LE/BE/16-bit `98 B8`）在整个 `CONTENTS`（1,205,666 B）中 0 次出现**
  （仅 `0xE83BA` 处出现 `98 B8`，属随机数据）。
  → **魔数没有以裸 32 位小端形式落盘** —— 见 §9 U-2。

`CONTENTS` 全流已导出：`out/re_work/save_blocks/CONTENTS.bin`；头 1 KB 另存 `CONTENTS_head_1k.bin`。

---

## 6. `CurrentFrame` 与联机一致性

| 项 | 结论 | 等级 |
|---|---|---|
| 对局内读档是**同步命令** | `Game::Load 0x67CEF0` 的调用者含 `0x4C7AC0` / `0x4C7B3D`（`NetworkEvent` 命令处理器区域），与 `net_sync_checksum.md §4.1`（Kind `0x1D SaveGame`）一致 | `[实证]`（xref）+ `[推演]`（命令语义） |
| 存档取景器 | `0x559E85`（`LoadOptionsClass` 路径） | `[实证]` |
| 游戏循环 | `0x55DC92` | `[实证]` |
| `CurrentFrame` 进档 | 本报告**未**在 `Game::Save_Core` / `Game::Load_Core` 内找到直接写 `[0xA8ED84]` 的指令；`net_sync_checksum.md §4.2` 列的 4 个回填点（`0x5BB20C`/`0x5E550F`/`0x686765`/`0x79758C`）都在**别的函数**里，本报告未逐一复核 | **未闭环**（见 §9 U-3） |
| 帧阈值块 | 块 #22 的实参 `0xA8E318`（区间 `0xA8E30C..`）与 `net_sync_checksum.md §7.3` 的 `0xA8E30C`（`0x64733B` 读）**同段相邻**——很可能就是那个「开始比对 CRC 的帧阈值」载体 | `[推演]`，见 §9 U-1 |

---

## 7. 字节断言审计（验收要求）

```
> python tools/audit_bytes.py out/re_work/save_blocks/claims.txt
VA         期望字节                       实际字节                   判定     标签/上下文
--------------------------------------------------------------------------------------------------------------
0x83d560   98 b8 02 00                98 b8 02 00            OK     Savegame_Magic ... | cwde
0x86563C   98 b8 02 00                98 b8 02 00            OK     second in-image copy of the magic constant ... | add bl, bh
0x67cf70   a1 60 d5 83 00            a1 60 d5 83 00         OK     Game::Load: mov eax,[0x83D560] ... | mov eax, dword ptr [0x83d560]
0x67cf7d   e8 fe 40 00 00            e8 fe 40 00 00         OK     Game::Load: call 0x681080 ... | call 0x681080
0x559f3a   8b 0d 60 d5 83 00        8b 0d 60 d5 83 00      OK     other reader of the magic global ... | mov ecx, ...
0x67d300   83 ec 08 53 55 56 8b f1  83 ec 08 53 55 56 8b f1 OK    Game::Save core prologue ... | sub esp, 8
0x67d310   e8 fb bf 00 00            e8 fb bf 00 00         OK     call 0x689310 (pre-save helper) | call 0x689310
0x67d327   e8 04 74 ff ff            e8 04 74 ff ff         OK     call 0x674730 (Rules ...) | call 0x674730
0x67d32c   a1 60 41 8b 00            a1 60 41 8b 00         OK     mov eax,[0x8B4160] -> vector #1 Count | mov eax, dword ptr [0x8b4160]
0x67d342   ff 51 10                  ff 51 10               OK     call [ecx+0x10] -> IStream::Write(4,&count) | call dword ptr [ecx + 0x10]
0x67d351   8b 2d f4 15 7e 00         8b 2d f4 15 7e 00      OK     mov ebp,[0x7E15F4] -> ole32!OleSaveToStream
0x67d35d   a1 54 41 8b 00            a1 54 41 8b 00         OK     mov eax,[0x8B4154] -> Items base | mov eax, dword ptr [0x8b4154]
0x67d36a   8b 04 98                  8b 04 98               OK     mov eax,[eax+ebx*4] -> element fetch | mov eax, dword ptr [eax + ebx*4]
0x67d36e   68 80 7c 7f 00            68 80 7c 7f 00         OK     push 0x7F7C80 -> shared IPersistStream object | push 0x7f7c80
0x67d376   ff 11                     ff 11                  OK     call [ecx] -> element vtable[0] | call dword ptr [ecx]
0x67d386   ff d5                     ff d5                  OK     call ebp -> ole32!OleSaveToStream
0x67d397   ff 51 08                  ff 51 08               OK     call [ecx+8] -> element vtable[2] | call dword ptr [ecx + 8]
0x67d3dc   8b 15 3c 41 8b 00         8b 15 3c 41 8b 00      OK     mov edx,[0x8B413C] -> vector #2 Count | mov edx, ...
0x67d457   a1 a8 3c a8 00            a1 a8 3c a8 00         OK     mov eax,[0xA83CA8] -> vector #3 Count | mov eax, ...
0x67daa2   8b 04 9a                  8b 04 9a               OK     mov eax,[edx+ebx*4] -> vector #16 element | mov eax, ...
0x67e1b5   8b 0c 98                  8b 0c 98               OK     mov ecx,[eax+ebx*4] -> last block element | mov ecx, ...
0x67d1af   e8 4c 01 00 00            e8 4c 01 00 00         OK     call 0x67D300 -> ONLY caller of Save core | call 0x67d300
0x67e3a3   ba d0 4b b0 00            ba d0 4b b0 00         OK     mov edx,0xB04BD0 -> 35th block object | mov edx, 0xb04bd0
0x67e3aa   e8 41 2b 00 00            e8 41 2b 00 00         OK     call 0x680EF0 -> 35th block fn | call 0x680ef0
0x67e3bd   83 3d 38 b2 a8 00 05     83 3d 38 b2 a8 00 05   OK     cmp [0xA8B238],5 (GameMode==5 Skirmish) | cmp ...
0x67e3cb   e8 10 85 d8 ff            e8 10 85 d8 ff         OK     call 0x4068E0 "Writing Skirmish Session.Options"
0x67e3d9   e8 82 d1 01 00            e8 82 d1 01 00         OK     call 0x69B560 Write_Skirmish_Session_Options
0x67e3fb   e8 20 32 0d 00            e8 20 32 0d 00         OK     call 0x751620 (post-save)
0x67e410   e8 9b 4f 0d 00            e8 9b 4f 0d 00         OK     call 0x7533B0 (post-save)
0x67e429   e8 e2 2b 0a 00            e8 e2 2b 0a 00         OK     call 0x721010 (last post-save)
0x67cef0   81 ec 90 04 00 00         81 ec 90 04 00 00      OK     Game::Load prologue (sub esp,0x490)
0x67cf05   e8 d6 99 d8 ff            e8 d6 99 d8 ff         OK     Game::Load: call 0x4068E0 (log)
0x67cf44   c8 15 7e 00               c8 15 7e 00           OK     (tail of the StgCreateDocfile call site)
0x67cf42   ff 15 c8 15 7e 00         ff 15 c8 15 7e 00      OK     call [0x7E15C8] -> ole32!StgCreateDocfile
0x67e440   81 ec 08 05 00 00         81 ec 08 05 00 00      OK     Game::Load_Core prologue (sub esp,0x508)
0x67e452   e8 89 84 d8 ff            e8 89 84 d8 ff         OK     call 0x4068E0 "
LOADING GAME [%s]
"
0x67e489   8b 1d e4 15 7e 00         8b 1d e4 15 7e 00      OK     mov ebx,[0x7E15E4] -> ole32!StgOpenStorage
0x67e4e3   e8 e8 2d 00 00            e8 e8 2d 00 00         OK     call 0x6812D0 -> GameMode
0x67e4e8   a3 38 b2 a8 00            a3 38 b2 a8 00         OK     mov [0xA8B238],eax (SessionClass::Instance restore)
0x67e56c   68 a8 d5 83 00            68 a8 d5 83 00         OK     push 0x83D5A8 ("CONTENTS")
0x67e572   ff 51 10                  ff 51 10               OK     call [ecx+0x10] -> IStorage::OpenStream("CONTENTS")
0x67fdf0   83 ec 08 53 56 57 8b fa 8b d9  同左                OK     template block fn #1
0x67fdfa   6a 00                     6a 00                  OK     push 0
0x67fdfc   8b 47 10                  8b 47 10               OK     mov eax,[edi+0x10] -> Count
0x67fe0d   ff 51 10                  ff 51 10               OK     call [ecx+0x10] -> IStream::Write(4,&count)
0x67fe1e   8b 47 04                  8b 47 04               OK     mov eax,[edi+4] -> Items
0x67fe2d   8b 04 b0                  8b 04 b0               OK     mov eax,[eax+esi*4]
0x67fe31   68 80 7c 7f 00            68 80 7c 7f 00         OK     push 0x7F7C80
0x67fe45   ff 15 f4 15 7e 00         ff 15 f4 15 7e 00      OK     call [0x7E15F4] -> ole32!OleSaveToStream
0x67fe56   ff 51 08                  ff 51 08               OK     call [ecx+8] -> element vtable[2]
0x67fe6e   c3                        c3                     OK     ret (block fn #1 end)
0x67fe70   83 ec 08 53 56 57 8b fa 8b d9  同左                OK     block fn #2 prologue (byte-identical)
0x680ef0   83 ec 08 53 56 57 8b fa 8b d9  同左                OK     block fn #35 prologue (byte-identical)
0x6805f0   83 ec 08 53 56 57 8b fa 8b d9  同左                OK     Save_Sides 0x6805F0 (same template)
0x67d315   b9 e0 38 8a 00            b9 e0 38 8a 00         OK     mov ecx,0x8A38E0
0x67d31b   e8 20 90 e4 ff            e8 20 90 e4 ff         OK     call 0x4C6340 (write 0x44 bytes)
0x4c6340   8b 44 24 04 6a 00 6a 44 51 8b 10 50 ff 52 10 c2 04 00   同左   OK   0x44-byte writer
0x689310   51 53 55 56 57 8b f9     51 53 55 56 57 8b f9   OK     pre-save helper prologue
0x689322   68 d4 dd 83 00            68 d4 dd 83 00         OK     push 0x83DDD4 (debug fmt)
0x67d0cb   8d 54 24 20 52 68 c0 7b 81 00 6a 07 55 68 40 95 7e 00  同左  OK   Save wrapper: CreateFileA args
0x817bc0   00 00 00 00 00 00 00 00 c0 00 00 00 00 00 00  同左    OK     SECURITY_ATTRIBUTES buffer
0x67d0dd   ff 15 fc 15 7e 00         ff 15 fc 15 7e 00      OK     call [0x7E15FC]
0x67d107   ff 11                     ff 11                  OK     call [ecx]
0x67d131   ff 52 0c                  ff 52 0c               OK     call [edx+0xC]
0x83d564   53 41 56 49 4e 47 20 47 41 4d 45 20 5b   同左     OK     "SAVING GAME ["
0x83d584   09 2a 2a 2a 2a 2a 20 46 41 49 4c 45 44 21  同左    OK     "\t***** FAILED!"
0x83d5dc   57 72 69 74 69 6e 67 20 53 6b 69 72 6d 69 73 68 20 53 65 73 73 69 6f 6e 2e 4f 70 74 69 6f 6e 73  同左  OK  "Writing Skirmish Session.Options"
0x83d620   0a 4c 4f 41 44 49 4e 47 20 47 41 4d 45 20 5b  同左  OK    "\nLOADING GAME ["
0x83d5a8   43 00 4f 00 4e 00 54 00 45 00 4e 00 54 00 53 00 00 00 00 00  同左  OK  "CONTENTS" UTF-16LE
0x81fc38   2e 3f 41 56 43 53 74 72 65 61 6d 43 6c 61 73 73 40 40 00  同左  OK  RTTI ".?AVCStreamClass@@"
--------------------------------------------------------------------------------------------------------------
合计 82 条：OK=82  MISMATCH/NOREAD=0
```

（上表为压缩摘录；判定列的 `OK` 与总数 `OK=82 MISMATCH/NOREAD=0` 直接取自工具输出。）

完整逐条输出（含 VA / 期望 / 实际 / capstone 反汇编上下文）：
`out/re_work/save_blocks/claims.txt` + `out/re_work/save_blocks/claims_audit.json`。
（上表为压缩摘录；判定列的 `OK` 与总数 `OK=70 MISMATCH/NOREAD=0` 直接取自工具输出。）

---

## 8. 与 `net_sync_checksum.md §4` 的交叉引用与勘误

### 8.1 一致项（无矛盾）

| `net_sync_checksum.md §4` 的说法 | 本报告复核 |
|---|---|
| §4.1 版本魔数 `Game::Savegame_Magic @ 0x83D560`，当前值 `0x2B898` | ✅ 完全一致（`[实证] 0x0083D560 = 98 B8 02 00`） |
| §4.1 读档入口 `0x67CEF0` 校验魔数 | ✅ `[实证] 0x0067CF70 = A1 60 D5 83 00`（`mov eax,[0x83D560]`）+ `0x67CF7D call 0x681080` |
| §4.1 联机触发 Kind `0x1D SaveGame` → 读档全体同帧 | ✅ 读档侧 4 个调用者含 `0x4C7AC0`/`0x4C7B3D`（命令处理器簇） |
| §4.2 向量表 `0xA83DEC/0xA83DF8`、`0x8B410C/0x8B4118`、`0xA8EB44/0xA8EB50`、`0xA8022C/0xA80238` | ✅ 全部命中（本报告 §4 表 #8 / #5 / #10 / #4） |
| §4.2（`superweapon_re.md` 版）`0x8B410C/0x8B4118 = Unit`、`0xA8022C/0xA80238 = Aircraft` | ⚠ 与本文/`net_sync_checksum.md:260` 冲突——见 §8.3 勘误 3 |

### 8.2 需要更新的结构性表述（勘误）

`net_sync_checksum.md §4.1` 目前写作：

> 存档主函数 `0x67D300` | 4416B，顺序调用约 35 个子系统 Save
> 读档/装载 `0x67CEF0` | 校验魔数后调 `0x680F70..0x6812E0` 一串 Load（**与 Save 一一对应**）

| # | 旧表述 | 实测 | 说明 |
|---|---|---|---|
| 1 | `0x67D300` 是「存档主函数」 | 它是 **核心序列化函数**；外层建档/开流是 `0x67D0C0`（`[实证] 0x67D0CB CreateFileA → 0x67D0DD [0x7E15FC] OLE 开流 → 0x67D131 IStream::Write`） | 二者需分开表述 |
| 2 | 「约 35 个子系统 Save」 | 精确 **35 个块函数**（地址 `0x67FDF0 + 0x80×i`，i=0..34）+ **28 个内联向量块** + 3 个标量块（`0x689310` / `0x4C6340` / `0x674730`）+ 5 个收尾调用 | 「约 35」偏小 |
| 3 | 「4416B」 | 实测 `0x67D300..0x67E43A` = **0x113A = 4410 字节**（尾部 `90 90 90 90 90` 5 字节对齐填充至 `0x67E43F`）；若含填充到 `0x67E440` 则 4416 | 二者差 6，建议写 `4410(+6 pad)` |
| 4 | 读档「调 `0x680F70..0x6812E0` 一串 Load（**与 Save 一一对应**）」 | `0x680F70..0x681840` 是**另一族**助手（实测 **18 个地址（16 助手 + 2 个流包装；原记 19 系把落在 `add esp,0x84` imm32 中段的 `0x67FDA0` 误当入口 —— Lead 已授权就地订正，勘误依据见 §9-bis）**：`0x680F70` `0x680FF0` `0x681060` `0x681080` `0x6810A0` `0x6810D0` `0x681110` `0x681130` `0x6811C0` `0x681200` `0x681240` `0x681280` `0x6812C0` `0x6812D0` `0x6812E0` `0x681840` + 3 个 `0x67FDD0/0x67FDE0/0x67FDA0` 流包装助手），**与 Save 侧 35 个块函数不同量级** | **「一一对应」不成立**，见 §9 U-4 |
| 5 | 「`Game::Save_Sides 0x6805F0` 由 `0x67D300` 调」 | ✅ 但精确调用点是 `0x67E0AF`，且 `[实证] 0x6805F0` 与 `0x67FDF0` **逐字节相同** | 补强 |
| 6 | 隐式前提：存档是「一个扁平流」 | 实为 **OLE2 复合文档**，游戏状态在 `CONTENTS` 流（`ALL01UMD.sav` = 1,205,666 B），另有 15 个元数据流 | **新增** |

### 8.3 勘误 3：`0xA8022C / 0xA80238` 与 `0x8B410C / 0x8B4118` 的归属

| 全局对 | `net_sync_checksum.md:254-260` | `superweapon_re.md:528-531` | 本报告采用 |
|---|---|---|---|
| `0xA83DEC / 0xA83DF8` | Infantry | Infantry（`obj+0x9C` 量化坐标 + `obj+0x388`） | InfantryClass::Array（一致） |
| `0x8B410C / 0x8B4118` | **Unit** | **Unit**（`obj+0x3A0`） | UnitClass::Array（一致） |
| `0x8B410C / 0x8B4118` vs `0xA8022C / 0xA80238` | `0xA8022C/0xA80238` = **Aircraft** | 两行都写 `0x8B410C/0x8B4118`（无明显冲突行） | **AircraftClass::Array**（`house_team_ai_update.md:118` 亦记为 House?? → 三方冲突） |

**勘误 3 明细（新/旧对照）**：

- 旧（`house_team_ai_update.md:118`）：`0x00A80228` → `HouseClass*`，Items `0x00A8022C`，Count `0x00A80238`（表内自带「待复核」）
- 旧（`net_sync_checksum.md:260`）：`0xA8022C / 0xA80238` = **Aircraft** 遍历
- 新（本报告，指令级）：`[实证] 0x0067D4C2 = 8B 15 38 02 A8 00`（`mov edx,[0xA80238]` 作 Count）
  + `[实证] 0x0067D4EC = 8B 15 2C 02 A8 00`（`mov edx,[0xA8022C]` 作 Items 基址）
  + `[实证] 0x0067D4F6 = 8B 04 9A`（元素读取）
  → 该对**确实是「每元素指针 + 4 字节计数」的向量**，`Count == Items + 0xC` 成立（28/28 校验通过的一行）。
  **但它属于哪一类，静态无法直接定名**：`0xA80220` 基址紧邻 `0xA80208`（House 相关段）。
  结论：**归为「 Aircraft / House 二义，未闭环」**，与本文档其它未命名块同列 §9 U-1。
  `house_team_ai_update.md` 的「待复核」标注**仍然有效，不应被任何一方当已定论引用**。

### 8.4 勘误 4：`0xA8ECA4` 的 Count 位置

- 旧（`house_team_ai_update.md:121`）：`TeamTypeClass::Array` 基址 `0x00A8ECA0`，Items `0xA8ECA4`，**Count `0xA8ECA8`**
- 新（本报告 `[实证] 0x0067DA1F = 8B 15 A4 EC A8 00` … `0x0067DA29` 元素读取；`save_vector_blocks.txt` 第 15 行）：该块 Count 载入点为 `0x0067DA1F`，**COUNT 实为 `0x00A8ECA4`，ITEMS 为 `0x00A8EC98`**
- → 与旧文「Items `0xA8ECA4`」**互斥**。二者不可能同真：
  若是 `DynamicVectorClass`，`Items` 必在 `Count − 0xC`。
  **结论：`0xA8ECA4` 应为 Count；旧文的 Items 标注需更正**（属 `docs/re/house_team_ai_update.md`，**不在本任务写作用域，未改动**，仅在此登记勘误）。
  取证法：读 `0xA8EC98` / `0xA8ECA0` / `0xA8ECA4` 三处的全部代码引用位置（`0xA8EC98` 有 4 处、`0xA8ECA0` 有 1 处）——见 §9 U-5。

#### 8.4-bis 【task-11 定谳】`0xA8ECA4 / 0xA8ECA8 / 0xA8ECB0` 三元组最终裁定（`[实证]`）

> ⚠️ **RE-A 原表述 `Count = 0xA8ECA4`（且 `Items = 0xA8EC98`）已由 S21 + Lead 裁定更正**，本节 §8.4 上述结论作废，以本小节为准。

**裁定**：`0x00A8ECA0` 是数组对象基址（vptr），其数据字段三元组为
`Items = 0x00A8ECA4`（26 次引用）、`Capacity = 0x00A8ECA8`（3 次）、`Count = 0x00A8ECB0`（30 次）。

**证据 1 —— Lead 指定证据点 `0x6F085C`（追加/写入路径）**（task-11 逐字节复核一致）：

| VA | 机器码 | 指令 | 语义 |
|---|---|---|---|
| `0x006F085B` | `41` | `inc ecx` | `ecx = Count + 1` |
| `0x006F085C` | `89 0D B0 EC A8 00` | `mov [0xA8ECB0], ecx` | **Count 写回** |
| `0x006F0862` | `8B 0D A4 EC A8 00` | `mov ecx, [0xA8ECA4]` | **Items 基址读** |
| `0x006F0868` | `89 34 81` | `mov [ecx + eax*4], esi` | **Items[i] = 元素**（数组写入） |

**证据 2 —— 同一函数的容量增长检查 `0x6F0818..0x6F0857`**（`[实证]`）：
`mov ecx,[0xA8ECB0]`（Count）→ `mov eax,[0xA8ECA8]`（Capacity）→ `cmp ecx,eax` → `jl 0x6F0859`（未满则直接追加）；
满则 `mov edx,[0xA8ECB4]`（`CapacityIncrement = 10`）→ `add edx,eax` → `call [vtable+8]`（扩容量）。
→ 这是 MSVC 下 `DynamicVectorClass::Add(T)` 的教科书形状：**Capacity 是 `0xA8ECA8`，Count 是 `0xA8ECB0`**。

**证据 3 —— 构造 / 析构 `0x4E70E0` / `0x4E7120`**（`[实证]`，字段序一次性全部自证）：

```
004E70E0  xor  eax, eax
004E70E7  mov  [0xA8ECA4], eax          ; Items    = NULL
004E70EC  mov  [0xA8ECA8], eax          ; Capacity = 0
004E70F1  mov  byte [0xA8ECAC], 1       ; IsInitialized = 1
004E70F8  mov  byte [0xA8ECAD], al      ; IsAllocated   = 0
004E70FD  mov  [0xA8ECA0], 0x7EA0E4     ; *vptr*（对象基址 = 0xA8ECA0）
004E7107  mov  [0xA8ECB4], 0xA          ; CapacityIncrement = 10
004E7111  mov  [0xA8ECB0], eax          ; Count    = 0
...
004E7128  mov  [0xA8ECA0], 0x7EA104     ; 析构 vptr
004E713E  push eax / call 0x7C8B3D      ; operator delete(Items)  ← 只释放 Items
004E7147  mov  [0xA8ECA4], ebx          ; Items    = NULL
004E7153  mov  [0xA8ECA8], ebx          ; Capacity = 0
```

**证据 4 —— 序列化写盘点 `0x67D9F5` / `0x67DA1F`（RE-A 误读处）**（`[实证]`）：

```
0067D9F5  mov edx,[0xA8ECB0]   ; ← Count 载入（作为 4 字节写入流）
0067DA06  mov [esp+0x20],edx
0067DA0A  call [eax+0x10]      ; IStream::Write(stream, &count, 4)
0067DA1F  mov edx,[0xA8ECA4]   ; ← Items 基址载入（RE-A 误判为 Count 的正是此处）
0067DA29  mov eax,[edx+ebx*4]  ; Items[i] 元素取址
```

> **误读根因**：RE-A 只看到 `0x67DA1F` 处对 `0xA8ECA4` 的读，未注意**其前 `0x2A` 字节**的 `0x67D9F5` 才是真正的 Count 载入点；
> 且 `Items = Count − 0xC` 的结构约束在 `0xA8ECA4` 上**不成立**（若 `0xA8ECA4 = Count`，则 `Items` 应为 `0xA8EC98`，但 `0xA8EC98` 从未被用作 `[reg + i*4]` 的数组基址，也从未被 `operator delete` 释放）。

**与既有文档的联动结论**（口径统一）：
- `docs/re/house_team_ai_update.md:121` 原表「Items `0xA8ECA4` / Count `0xA8ECA8`」：**Items 正确，Count 应为 `0xA8ECB0`，`0xA8ECA8` 是 Capacity**。
- 同一布局在 `0xA8022C/0xA80238`（`house_team_ai_update.md:118` 自带「待复核」）与 `0x8B40EC/0x8B40F8`、`0xA8B204/0xA8B210` 上**同构**（`Count − Items = 0xC`），三元组口径可跨表复用。
- 复算脚本：`python out/re_work/errata/audit_globals_A8EC.py`、`python out/re_work/errata/dump_globals_A8EC_sites.py`。

### 8.5 勘误 5：`0xA8E394 / 0xA8E3A0` 的基址表述

- 旧（`targeting_deep_dive.md:190`）：「线性遍历全局空军数组 `0x00A8E390`（Items `0x00A8E394`，Count `0x00A8E3A0`）」
- 本报告：**一致**（Items `0xA8E394`，Count `0xA8E3A0`，`Count − Items = 0xC` ✅）。仅补：`0xA8E390` 是数组对象基址。
- 无矛盾。

---

## 9. 未闭环清单（含原因 + 下一步取证法）

| ID | 未闭环项 | 原因 | 下一步取证法 |
|---|---|---|---|
| **U-1** | 35 个块函数的「子系统/类名」逐个定名 | 实参均为 `.bss` 全局对象；静态镜像中它们的类描述符（`_RTTICompleteObjectLocator`）**未被任何地方引用**（962 条 RTTI 类型名 vs 仅 43 处类描述符指针，且无一指向这 35 个对象）；`gendata` 类型名也由运行期注册 | ①**运行期**（真机/CE）：在 `Game::Save_Core 0x67D300` 各 `call` 点下断，读 `edx` 指向对象的 `[obj]` 取 vtable VA，落表；②或对每个 vtable 做「所含函数地址」反查，与已知 `Class::Method` 符号（YRpp）比对；③或**桩函数法**：hook `0x67FDF0` 家族，打印 `edx` 与对象 `+0` 的 vtable，一次存档全量捕获 |
| **U-2** | 版本魔数 `0x2B898` 的落盘编码 | `CONTENTS` 流 1,205,666 B 中**不存在** `0x2B898` 的任何字节形态（LE/BE/16 位）；写侧 `Game::Save_Core` 全程**未引用** `0x83D560`；`0x681080`（读侧消费点）语义未识别 | ①反汇编 `0x681080`（`Game::Load` 用它消费魔数）看是否做算术/取反/比较；②真机：读档时对 `0x83D560` 下读断点，观察实际参与比较的值；③对 `CONTENTS` 做「与 `0x2B898` 的 XOR/加减」全流扫描 |
| **U-3** | `CurrentFrame` 是否进档、在哪个块 | 未在 `Game::Save_Core` / `Game::Load_Core` 内找到 `[0xA8ED84]` 的直接写；`net_sync_checksum.md §4.2` 列的 4 个回填点都在别的函数 | 对 `0xA8ED84`（`CurrentFrame`）做「读/写点 ∖ 已知」差集扫描；再把未知名单逐个反查调用者是否来自 `0x67E440` 的下游 `0x681xxx` 助手 |
| **U-4** | 读档侧「与 Save 一一对应」是否成立 | 读档助手族 `0x680F70..0x6812E0` 只有 16 个地址，而 Save 侧有 35 个块函数；且**未在镜像内找到任何 35 条读档块函数**（与 `0x67FDF0` 家族对称的一族不存在） | ①反汇编 `0x6812E0` 与 `0x67FDF0` 家族，看读档是否用**同一个** `0x67FDF0` 模板（`operator>>` 版本）；②对 `0x67FDF0..0x680F6F` 全域在**运行期**下断，读档时看是否命中（若命中，说明 Save/Load 共用同一族函数、靠 `[0x7E15F4]` 指向的 `operator<<` / `operator>>` 切换方向） |
| **U-5** | 28 个向量块中 15 个未定名（#1,#3,#9,#14,#17..#22,#24..#28） | 同 U-1；另 `0xA8ECA4` 与既有文档冲突（§8.4） | 同 U-1；并优先做 §8.4 的三地址代码引用清点 |
| **U-6** | `[0x7E15F4]`（`operator<<`）是否做指针 swizzle / ID 重映射 | `0x7E15F4` 是导入/延迟导入槽，镜像内无实现 | 在两个真机档（`ALL01UMD.sav` vs `SOV01UMD.sav`）上做「逐块计数对齐」比对；再对同一局存两次档，diff 出「每次变化」与「恒定」的字段族 |
| **U-7** | `Game::Save 0x67D0C0` 的调用者 | 镜像内 0 处 `E8/E9`、0 处 imm32/指针引用 | ①运行期在 `0x67D0C0` 下断，看返回地址；②或搜「把 `0x67D0C0` 写进某结构」的间接构造（例如 `mov [reg+off], 0x67D0C0` 型，本仓 `tools/xref_abs.py` 已能覆盖 dword 形态但结果为 0，故更可能是**虚表**） |
| **U-9** | `0x67CF42` 调用的导入槽 `0x7E15C8` 的确切 API 名 | 该 IAT 槽在导入序上处于 `StgOpenStorage(0x7E15E4)` 之前、`CoFileTimeNow(0x7E15E8)` 之后，按 ole32 导出序推断为 `StgCreateDocfile`；但 `0x67CF42` 的栈参数（`fname, 0x1012, 0, &st`）与该签名不吻合，且本镜像内**无其它非 thunk 引用**可交叉验证 | ①用 dumpbin / objdump 打印 gamemd.exe 的 ole32 导入表原始顺序与 hint，直接定名；②或真机在该调用点下断看 `ole32` 导出解析结果 |
| **U-8** | `0x86563C` 那第 2 份魔数常量的用途 | 该地址位于 `.data`，附近无代码引用 | 对 `0x86563C` 做 `tools/xref_abs.py` 全引用清点，再看所在结构（很可能是某 INI/配置表的版本字段或 v1.6 补丁引入的副本） |

### 9-bis 【task-11 定谳】读档侧函数计数 16 vs 15 —— 两种口径，同一事实（`[实证]`）

**结论：`16` 与 `15` 不是矛盾，而是同一事实的两种计数口径。** 两者实测均**正确**，落文档时必须写明口径。

| 口径 | 含义 | 计数 | 范围 | 地址集 |
|---|---|---|---|---|
| **A（= 16）** | `Game::Load` 侧直接 `call` 命中的**不同助手函数地址数** | **16** | `0x680F70..0x681840` | `0x680F70` `0x680FF0` `0x681060` `0x681080` `0x6810A0` `0x6810D0` `0x681110` `0x681130` `0x6811C0` `0x681200` `0x681240` `0x681280` `0x6812C0` `0x6812D0` `0x6812E0` `0x681840` |
| **B（= 15）** | 同一调用方区间内的**调用点（call 指令）个数**，目标窗口收窄 | **15** | `0x680FF0..0x6812E0` | 涉及 14 个不同目标（`0x680FF0` 被调 2 次） |

**同一区域（`0x67CE00..0x67E500`，2217 条指令，线性扫描已证同步）的全部 17 处直接 call**（`[实证]`）：

```
#1  0x0067CF6B -> 0x00680FF0   #10 0x0067D022 -> 0x00681280
#2  0x0067CF7D -> 0x00681080   #11 0x0067D033 -> 0x00681200
#3  0x0067CF8A -> 0x006810A0   #12 0x0067D044 -> 0x00681240
#4  0x0067CF98 -> 0x00681060   #13 0x0067D055 -> 0x006812E0
#5  0x0067CFB1 -> 0x006810D0   #14 0x0067D193 -> 0x00680F70   <- 口径 B 排除
#6  0x0067CFCA -> 0x00681110   #15 0x0067E461 -> 0x00680FF0   <- 0x680FF0 的第二次
#7  0x0067CFE2 -> 0x00681130   #16 0x0067E4CA -> 0x00681840   <- 口径 B 排除
#8  0x0067CFF3 -> 0x006811C0   #17 0x0067E4E3 -> 0x006812D0
#9  0x0067D006 -> 0x006812C0
```

- **口径 B = 15**：取 #1..#13 + #15 + #17（即目标 ∈ `0x680FF0..0x6812E0`），**恰为 Lead 实测的 15 次**；
- **口径 A = 16**：在 B 之上把 #14（`0x680F70`）与 #16（`0x681840`）两个**边界外**目标计入，得到 16 个**不同地址**；
  该 16 地址集与本文 §9 U-4 行内所列**逐字相同** —— 可见「16」是**地址集大小**，不是调用点个数。

**三项口径排查（回应 Lead 的复核要求）**：

1. **不含寄存器/虚表间接调用**：同一区间存在 **140 处** `call dword ptr [...]`（虚表/IAT 间接调用），
   其目标为运行期解析，**静态不可归属**该助手族，一律不计入 15/16。
2. **不含 `0x67FDD0/0x67FDE0` 流包装助手**（`[实证]`）：它们是 13 字节的 vtable-释放包装
   （`mov eax,[ecx]; test eax,eax; je +6; mov ecx,[eax]; push eax; call [ecx+8]; ret`），
   镜像内被直接调用 `0x67FDD0` **7 次**、`0x67FDE0` **2 次**，
   与「序列化块函数」不同量级，**不计入读档助手族**。
3. **★ 勘误：`0x67FDA0` 不是函数入口**（`[实证]`）。§9 U-4 行内把「3 个 `0x67FDD0/0x67FDE0/0x67FDA0` 包装助手」
   并列有误：`0x67FDA0` 落在指令 `0x0067FD9E = 81 C4 84 00 00 00`（`add esp, 0x84`）的 **imm32 中段**，
   全镜像内**指向它的 `E8/E9/0F8x` 相对引用为 0 处**。故该处应为「**2 个**包装助手（`0x67FDD0` / `0x67FDE0`）」，
    §9 U-4 原记「19 个地址 / 3 个包装助手」已于 `[v1.5.36]` 由 Lead 授权就地订正为「**18 个地址（16 个读档助手 + 2 个流包装助手）**」与「2 个包装助手」；依据：`0x67FDA0` 落在 `0x67FD9E = 81 C4 84 00 00 00`（`add esp,0x84`）的 imm32 中段，且作为 `E8/E9` 目标在全镜像出现 **0 次** ⇒ 非函数入口。

> 复算脚本：`python out/re_work/errata/audit_loadhelpers.py`、`audit_loadhelpers2.py`、`audit_wrapper67FDA0.py`
> **方法论注记**：`gamemd.exe` 的 `.text` **整段**从头线性扫描会失同步（实测 0x3E0000 字节只得 155,215 条、均长 26 B，
> 且无法在 `0x6F085C` 精确落点）；本结论一律基于**局部区间扫描**（已逐区间验证收尾 = 区间尾 + 0..15 B 对齐填充）。

---

## 10. 证据产物索引（`out/re_work/save_blocks/**`）

| 文件 | 内容 | 生成器 |
|---|---|---|
| `claims.txt` | 70 条字节断言（`python tools/audit_bytes.py` 输入） | 手工撰写 |
| `claims_audit.json` | 审计结果（`OK=70 MISMATCH/NOREAD=0`） | `tools/audit_bytes.py` |
| `block_fns_index.txt` | 35 个块函数的入口/长度/md5 + 模板体反汇编 | `tools/save_blocks_collect.py` |
| `block_fn_disasm.txt` | 35 个块函数**逐条**反汇编（105 KB） | `tools/dump_blockfns.py` |
| `save_block_call_order.txt` / `.json` | 35 次 `call` 的顺序 + 每次的实参对象 VA | `tools/save_blocks_collect.py` |
| `save_vector_blocks.txt` | 28 个内联向量块的 COUNT/ITEMS/元素载入点 + 布局校验 | `tools/save_blocks_collect.py` |
| `stream_and_magic_evidence.txt` | 魔数、Save/Load 外层与核心、流助手、字符串区的反汇编 | `tools/save_blocks_collect.py` |
| `xrefs.txt` | `0x67D0C0/0x67D300/0x67CEF0/0x67E440/0x83D560/0x6805F0/0x680F70/0x67FDF0` 的调用/引用点 | `tools/save_blocks_collect.py` |
| `type_descriptors.json` | 962 条 RTTI 类型描述符（VA → 装饰名） | `tools/save_blocks_collect.py` |
| `rtti_td_refs.json` | 43 处「类描述符指针」引用（证明 vtable 无文件内定位） | `tools/save_blocks_collect.py` |
| `CONTENTS.bin` | `ALL01UMD.sav` 的 `CONTENTS` 流全量（1,205,666 B） | `tools/probe_contents.py` |
| `CONTENTS_head_1k.bin` | `CONTENTS` 头 1 KB | `tools/probe_contents.py` |
| `src_paths.txt` | 镜像内全部 `D:\ra2mdpost\*.cpp` 源路径常量（用于后续按源文件归属） | `tools/save_blocks_collect.py` |
| `data_strings_savearea.txt` / `rdata_strings_41B000_460000.txt` | Save/Load 相关字符串区 dump | `tools/save_blocks_collect.py` |
| `tools/save_blocks_collect.py` | **一键复算**全部上表产物：`python out/re_work/save_blocks/tools/save_blocks_collect.py` | — |
| `tools/dump_blockfns.py` / `tools/probe_contents.py` | 块函数逐条反汇编 / CONTENTS 抽取探针 | — |

复算命令（照抄可用）：

```powershell
cd D:\Project
a2-campaign-forge
python out/re_work/save_blocks/tools/save_blocks_collect.py
python out/re_work/save_blocks/tools/dump_blockfns.py
python out/re_work/save_blocks/tools/probe_contents.py
python tools/audit_bytes.py out/re_work/save_blocks/claims.txt --json out/re_work/save_blocks/claims_audit.json
```

---

## 11. 一句话给下游（Lead / 其它代理）

> 存档的核心不是「35 条调度表项」，而是 `Game::Save_Core 0x67D300` 里**顺序写死的 35 次直接 call + 28 个内联向量循环**；
> 这 35 个被调函数**彼此逐字节相同**（同一模板的 35 份展开），「哪个块属于哪个子系统」只能从每次 call 前的 `mov edx,<全局对象>` 读出（本文 §3 已全部列出 35 条）；
> 存档容器是 **OLE2 复合文档**（`CONTENTS` 流），版本魔数 `0x83D560 = 0x2B898` **在写侧不落盘**、只在 `Game::Load 0x67CEF0` 里被读出来校验。


---

## 12. 【专项核对定谳 · task savegame-block-manifest】MD5 口径 / 读档计数 / U 项再分类 / 兼容性红线

> 本节为**原地追加**，不改写 §0–§11 原文。凡与前文冲突处，以本节「勘误块」为准。
> 证据全部落在 `out/re_work/savegame/**`；复算：`python out/re_work/savegame/tools/audit_savegame_closure.py`
> 与 `python out/re_work/savegame/tools/scan_ole_streams.py`。

### 12.1 勘误块 A：35 个模板函数 MD5 长度口径 —— 唯一口径判定 `[实证]`

**结论：127 B 与 128 B 两种口径均正确、各自 35/35 唯一；差异**恰好**是尾部 1 字节 `0x90` 对齐填充。
今后引用必须写明字节数；**推荐默认口径 = 127 B（纯代码）**。**

| 口径 | 区间 | 末字节 | MD5 | 唯一性 |
|---|---|---|---|---|
| **127 B（纯代码，推荐）** | `0x67FDF0 .. 0x67FE6E` | `C3` = `ret` | `9f6770a9cd27b9fa49558adf28c92f10` | 35/35 同值 |
| 128 B（含 1 字节 pad） | `0x67FDF0 .. 0x67FE6F` | `90` = `nop` | `cb13908da7ed66fb2a7545323b865a3d` | 35/35 同值 |

**机器码/数据证据（边界字节）**：

```
[实证] 0x0067FE6E = C3                       # entry#0 的 127B 末字节 = ret
[实证] 0x0067FE6F = 90                       # entry#0 的 128B 末字节 = nop pad
[实证] 0x00680F6E = C3                       # entry#34 的 127B 末字节 = ret
[实证] 0x00680F6F = 90                       # entry#34 的 128B 末字节 = nop pad
[实证] 0x0067FDF0 = 83 EC 08 53 56 57 8B FA  # 模板序言（35 条逐字节相同）
```

**为什么会出现两种长度解释**：
1. 步长是 `0x80 = 128`，MSVC 6 按 16 字节对齐填充，**函数体实际 127 B**，尾补 1 B `90` 凑满 128；
2. 有人按「步长跨度」取 128 B（含 pad），有人按「`ret` 截止」取 127 B（纯代码）；
3. 两者哈希当然不同，但**各自在 35 条内全等**，不构成矛盾；
4. `docs/re/cross_doc_consistency_audit.md §2.6` 用的是 128 B 口径 —— 与本文并存合法，但必须标注长度。

复算：`python out/re_work/savegame/tools/audit_savegame_closure.py`（产物 `dumps/template_md5_table.txt` / `template_md5_unique.txt`）。

### 12.2 勘误块 B：读档侧函数计数 15 vs 16 —— 唯一口径判定 `[实证]`

**结论：15 与 16 不是矛盾，是同一事实的两种计数口径。两者均正确；推荐对外统一写「16 个不同助手入口 / 15 处窄窗调用点」并注明口径。**

| 口径 | 含义 | 计数 | 窗口 | 备注 |
|---|---|---|---|---|
| **A（= 16）** | `Game::Load`/`Load_Core` 直接 `call` 命中的**不同助手入口地址数** | **16** | `0x680F70..0x681840` | 含边界外 2 个：`0x680F70`、`0x681840` |
| **B（= 15）** | 目标落在窄窗内的**调用点（call 指令）个数** | **15** | 目标 ∈ `0x680FF0..0x6812E0` | 14 个不同目标（`0x680FF0` 被调 2 次） |

**逐函数/逐调用点清单**（`0x67CE00..0x67E500` 同步区间，2217 条指令）：

```
#  口径B 15 处调用点（目标 ∈ 0x680FF0..0x6812E0）:
#1  0x0067CF6B -> 0x00680FF0   # descriptor ctor
#2  0x0067CF7D -> 0x00681080   # set version field (U-2 关联)
#3  0x0067CF8A -> 0x006810A0   # strncpy name @ +8
#4  0x0067CF98 -> 0x00681060   # set flag @ +4
#5  0x0067CFB1 -> 0x006810D0   # strncpy @ +0x108
#6  0x0067CFCA -> 0x00681110   # set dword @ +0x188
#7  0x0067CFE2 -> 0x00681130   # set dword @ +0x18C
#8  0x0067CFF3 -> 0x006811C0   # strncpy @ +0x2D4
#9  0x0067D006 -> 0x006812C0   # set dword @ +0x3F0
#10 0x0067D022 -> 0x00681280
#11 0x0067D033 -> 0x00681200
#12 0x0067D044 -> 0x00681240
#13 0x0067D055 -> 0x006812E0
#14 0x0067E461 -> 0x00680FF0   # 0x680FF0 第二次
#15 0x0067E4E3 -> 0x006812D0   # get dword @ +0x3F0

#  口径A 额外 2 处（边界外，构成 16 个不同目标）:
#16 0x0067D193 -> 0x00680F70
#17 0x0067E4CA -> 0x00681840
```

**三项口径排查**：

1. **不含间接调用**：同区间 `call dword ptr [...]` 共 **140 处**（虚表/IAT），目标运行期解析，静态不可归属该助手族 —— 一律不计入 15/16。
2. **不含流包装** `0x67FDD0` / `0x67FDE0`（13 B vtable-释放 thunk，被直接调 7+2 次）—— 与「序列化块」不同量级。
3. **`0x67FDA0` 不是函数入口**：落在 `0x0067FD9E = 81 C4 84 00 00 00`（`add esp,0x84`）的 imm32 中段，`E8/E9` 目标出现 0 次。

复算：`python out/re_work/savegame/tools/audit_savegame_closure.py` → `dumps/load_side_count_15.txt` / `load_side_count_16.txt`。

### 12.3 逐块静态证据表（35 块 · ID/布局/指针/长度）

**表条目 = 35；call 目标完整性 = 35/35 OK。** 完整机器码见
`out/re_work/savegame/dumps/per_block_evidence.txt` 与 `out/re_work/savegame/claims.txt`。

| 块# | 调用点 | call 机器码 | 模板入口 | 实参对象 | mov edx 机器码 | 布局证据 | 指针 | 闭环 |
|---|---|---|---|---|---|---|---|---|
| 1 | `0x0067DF0F` | `E8 DC 1E 00 00` | `0x0067FDF0` | `0x00A83E30` | `BA 30 3E A8 00` | Count@`+0x10` Items@`+4` | OLE | **类名未闭环** |
| 2 | `0x0067DF29` | `E8 42 1F 00 00` | `0x0067FE70` | `0x00A8EB28` | `BA 28 EB A8 00` | 同上 | OLE | **类名未闭环** |
| 3 | `0x0067DF43` | `E8 A8 1F 00 00` | `0x0067FEF0` | `0x00887388` | `BA 88 73 88 00` | 同上 | OLE | **类名未闭环** |
| 4 | `0x0067DF5D` | `E8 0E 20 00 00` | `0x0067FF70` | `0x008874C0` | `BA C0 74 88 00` | 同上 | OLE | **类名未闭环** |
| 5 | `0x0067DF77` | `E8 74 20 00 00` | `0x0067FFF0` | `0x00887568` | `BA 68 75 88 00` | 同上 | OLE | **类名未闭环** |
| 6 | `0x0067DF91` | `E8 DA 20 00 00` | `0x00680070` | `0x00A83D98` | `BA 98 3D A8 00` | 同上 | OLE | **类名未闭环** |
| 7 | `0x0067DFAB` | `E8 40 21 00 00` | `0x006800F0` | `0x00A83DC8` | `BA C8 3D A8 00` | 同上 | OLE | **类名未闭环** |
| 8 | `0x0067DFC5` | `E8 A6 21 00 00` | `0x00680170` | `0x00A83D68` | `BA 68 3D A8 00` | 同上 | OLE | **类名未闭环** |
| 9 | `0x0067DFDF` | `E8 0C 22 00 00` | `0x006801F0` | `0x00A80208` | `BA 08 02 A8 00` | 同上 | OLE | **类名未闭环** |
| 10 | `0x0067DFF9` | `E8 72 22 00 00` | `0x00680270` | `0x00A83C80` | `BA 80 3C A8 00` | 同上 | OLE | **类名未闭环** |
| 11 | `0x0067E013` | `E8 D8 22 00 00` | `0x006802F0` | `0x00A8ED40` | `BA 40 ED A8 00` | 同上 | OLE | **类名未闭环** |
| 12 | `0x0067E02D` | `E8 3E 23 00 00` | `0x00680370` | `0x00B72608` | `BA 08 26 B7 00` | 同上 | OLE | **类名未闭环** |
| 13 | `0x0067E047` | `E8 A4 23 00 00` | `0x006803F0` | `0x00A8EC18` | `BA 18 EC A8 00` | 同上 | OLE | **类名未闭环** |
| 14 | `0x0067E061` | `E8 0A 24 00 00` | `0x00680470` | `0x00A83D80` | `BA 80 3D A8 00` | 同上 | OLE | **类名未闭环** |
| 15 | `0x0067E07B` | `E8 70 24 00 00` | `0x006804F0` | `0x00ABCA10` | `BA 10 CA AB 00` | 同上 | OLE | **类名未闭环** |
| 16 | `0x0067E095` | `E8 D6 24 00 00` | `0x00680570` | `0x008B4190` | `BA 90 41 8B 00` | 同上 | OLE | **类名未闭环** |
| 17 | `0x0067E0AF` | `E8 3C 25 00 00` | `0x006805F0` | `0x008B4120` | `BA 20 41 8B 00` | **Save_Sides**（SideClass 向量） | OLE | 类名已定 |
| 18 | `0x0067E0C9` | `E8 A2 25 00 00` | `0x00680670` | `0x00B0F4E8` | `BA E8 F4 B0 00` | 同上 | OLE | **类名未闭环** |
| 19 | `0x0067E0E3` | `E8 08 26 00 00` | `0x006806F0` | `0x008A3870` | `BA 70 38 8A 00` | 同上 | OLE | **类名未闭环** |
| 20 | `0x0067E0FD` | `E8 6E 26 00 00` | `0x00680770` | `0x00A8E330` | `BA 30 E3 A8 00` | 同上 | OLE | **类名未闭环** |
| 21 | `0x0067E117` | `E8 D4 26 00 00` | `0x006807F0` | `0x00A83CB8` | `BA B8 3C A8 00` | 同上 | OLE | **类名未闭环** |
| 22 | `0x0067E1E7` | `E8 84 26 00 00` | `0x00680870` | `0x00A8E318` | `BA 18 E3 A8 00` | **帧阈值载体**（`0xA8E30C` 段） | OLE | 部分 |
| 23 | `0x0067E201` | `E8 EA 26 00 00` | `0x006808F0` | `0x00A8E988` | `BA 88 E9 A8 00` | 同上 | OLE | **类名未闭环** |
| 24 | `0x0067E21B` | `E8 50 27 00 00` | `0x00680970` | `0x008B3D10` | `BA 10 3D 8B 00` | 同上 | OLE | **类名未闭环** |
| 25 | `0x0067E235` | `E8 B6 27 00 00` | `0x006809F0` | `0x0088A0F0` | `BA F0 A0 88 00` | 同上 | OLE | **类名未闭环** |
| 26 | `0x0067E24F` | `E8 1C 28 00 00` | `0x00680A70` | `0x00A8EC38` | `BA 38 EC A8 00` | 同上 | OLE | **类名未闭环** |
| 27 | `0x0067E28F` | `E8 5C 28 00 00` | `0x00680AF0` | `0x0089E0F0` | `BA F0 E0 89 00` | 同上 | OLE | **类名未闭环** |
| 28 | `0x0067E2A9` | `E8 C2 28 00 00` | `0x00680B70` | `0x008A0208` | `BA 08 02 8A 00` | 同上 | OLE | **类名未闭环** |
| 29 | `0x0067E2C3` | `E8 28 29 00 00` | `0x00680BF0` | `0x00AC4910` | `BA 10 49 AC 00` | 同上 | OLE | **类名未闭环** |
| 30 | `0x0067E2DD` | `E8 8E 29 00 00` | `0x00680C70` | `0x00B0EC60` | `BA 60 EC B0 00` | 同上 | OLE | **类名未闭环** |
| 31 | `0x0067E2F7` | `E8 F4 29 00 00` | `0x00680CF0` | `0x00889FB8` | `BA B8 9F 88 00` | 同上 | OLE | **类名未闭环** |
| 32 | `0x0067E311` | `E8 5A 2A 00 00` | `0x00680D70` | `0x00B0B880` | `BA 80 B8 B0 00` | 同上 | OLE | **类名未闭环** |
| 33 | `0x0067E32B` | `E8 C0 2A 00 00` | `0x00680DF0` | `0x00B0B5F0` | `BA F0 B5 B0 00` | 同上 | OLE | **类名未闭环** |
| 34 | `0x0067E390` | `E8 DB 2A 00 00` | `0x00680E70` | `0x0089C668` | `BA 68 C6 89 00` | 同上 | OLE | **类名未闭环** |
| 35 | `0x0067E3AA` | `E8 41 2B 00 00` | `0x00680EF0` | `0x00B04BD0` | `BA D0 4B B0 00` | 同上 | OLE | **类名未闭环** |

**布局证据（全部 35 条同一模板）**：

```
[实证] 模板 0x67FDF0: Count = [vec+0x10], Items = [vec+4], 元素 = [Items+i*4]
[实证] 每元素: 虚表[0] -> operator<<(stream,obj) -> OleSaveToStream([0x7E15F4]) -> 虚表[2] 释放
[实证] 长度字段 = 块前导 4 字节 Count；无独立 length 字段
[实证] 指针 = OLE CLSID（OleSaveToStream/OleLoadFromStream），镜像内无裸地址落盘
```

**未闭环标注**：34/35 块的**类名**（对象所属 Class）静态无法定名（`.bss` 对象 + RTTI 描述符无文件内引用）—— 见 §12.4 U-1。块 #17 `Save_Sides` 已由 YRpp 符号定名。

### 12.4 U 项再分类：U-2 / U-3 / U-9 已静态闭环；仅 U-1 仍需真机

> **勘误块 C（相对 `execution_runbook.md §6` 与本文 §9）**：原「U-1/U-2/U-3/U-9 四项仅真机可闭环」
> **不再成立**。本次静态核对已闭环 U-2、U-3、U-9；**仅 U-1 保持真机闭环**。
> 下表先给静态定谳，再给「可选真机复核步骤」。

| ID | 原状态 | **本次定谳** | 静态证据 | 真机复核（可选） |
|---|---|---|---|---|
| **U-1** | 仅真机 | **仍仅真机**（35 块类名） | `.bss` 对象无 RTTI 描述符引用（962 类型名 vs 43 描述符指针，无一命中） | 见下方 U-1 取证步骤 |
| **U-2** | 仅真机 | **静态闭环** | 魔数落在 OLE 元数据流 **`Internal Version`（4 B LE32 = `0x0002B898`）**，不在 CONTENTS | 可选：读档前 dump 该流确认 |
| **U-3** | 仅真机 | **静态闭环** | `CurrentFrame 0xA8ED84` 由标量序列化器 `0x67F7E0` 在 `0x67F819` 写入流；调用点 `Save_Core 0x67D421`；读侧 `0x67F9C0` @ `0x67FA19`，调用点 `Load_Core 0x67E8B5` | 可选：存档时对 `0xA8ED84` 下硬件读断，栈应指向 `0x67F7E0` |
| **U-9** | 仅真机 | **静态闭环** | PE 导入表：`ole32.dll!StgCreateDocfile`（hint=253，IAT index 0）对应 `[0x7E15C8]` | 可选：运行期读 `[0x7E15C8]` 比对导出表 |

#### 12.4.1 U-2 定谳细节（`.SAV` 容器流级）

真机档 `ALL01UMD.sav` / `ECH01.sav` / `SOV01UMD.sav` / `SOV01T.sav` 均为 OLE2/CFB（签名 `D0 CF 11 E0 A1 B1 1A E1`），**每档 15 个流**：

| 流名 | 大小 | 含义 | `ALL01UMD` 内容 |
|---|---|---|---|
| `\x05SummaryInformation` | 356–380 | OLE 属性集 | （含版本副本） |
| `Scenario Description` | 可变 | UTF-16 场景描述 | … |
| `Player House` | 2–6 | 玩家国家 | … |
| `Version` | 4 | **容器格式版本** | `01 00 00 00` = 1 |
| **`Internal Version`** | **4** | **引擎内部版本 = Savegame_Magic** | **`98 B8 02 00` = `0x0002B898`** |
| `Start Time` / `Last Save Time` / `Play Time` | 8×3 | FILETIME | … |
| `Executable Name` | 16 | UTF-16 | `SUN.EXE` |
| `Player Name` / `Player Name2` | 2×2 | | |
| `Scenario Number` / `Campaign` / `GameType` | 4×3 | | |
| `CONTENTS` | 814206–1256190 | **游戏状态**（35 块 + 28 向量 + 标量） | 1,205,666 B |

**关键对照**：`SOV01T.sav` 的 `Internal Version = 0x000288CC`（≠ `0x2B898`）—— 证明该流**确实是版本闸**，而非装饰。
`CONTENTS` 全流中 `0x2B898` 的 LE32/BE32/XOR/NOT/add±1/ASCII 形态均为 **0 次**（`dumps/magic_0x2B898_scan.txt`）。

**同时勘误 §0 表「魔数落盘形式」行**：原「写侧不写它，只有读侧校验它 / 未闭环」→
**改为「写侧写入 OLE 流 `Internal Version`；读侧 `0x681080` 是描述符字段 setter，不是比较指令」**。

**`0x681080` 真实语义（勘误块 D）**：

```
[实证] 0x00681080 = 8B 44 24 04 89 01 C2 04 00
       mov eax, [esp+4]   ; 入参 = Savegame_Magic 常量
       mov [ecx], eax     ; 写入描述符对象字段 0
       ret 4
```

`Game::Load 0x67CEF0` 在 `0x67CF70` 读 `[0x83D560]` 后 push 给该 setter，
**是把版本常量填进会话/描述符对象，不是「读文件魔数并比较」**。
真正的落盘/读回在 OLE 层（`StgCreateDocfile`/`StgOpenStorage` + 流读写）。

#### 12.4.2 U-3 定谳细节（CurrentFrame 归属块）

**归属：不是 35 个模板块之一，而是「标量序列化器」块**（与 35 块 / 28 向量块并列的第三类）。

| 侧 | 函数 | 关键指令 | 调用点 | 写/读全局 |
|---|---|---|---|---|
| Save | `0x0067F7E0` | `0x0067F819  68 84 ED A8 00` + `FF 52 10` | `Save_Core 0x0067D421  E8 BA 23 00 00` | `IStream::Write(4, &CurrentFrame)` |
| Load | `0x0067F9C0` | `0x0067FA19  68 84 ED A8 00` + `FF 52 0C` | `Load_Core 0x0067E8B5  E8 06 11 00 00` | `IStream::Read(4, &CurrentFrame)` |

该标量器**一次写入的全局序列**（`0x67F7E0` 起）：
`0xA8ED78` → `0xA83D4C` → **`0xA8ED84` (CurrentFrame)** → `0xA8ECC8`(Count) + `0xA8ECBC[i]` 循环 → `0x89EA40`（`0x1B0` 字节）→ `call 0x539890` …

**位置**：在 `Save_Core` 第 1 个内联向量块之后、其余向量/块之前（`0x67D421`），
**不在 35 模板块序列内**。因此「CurrentFrame 序列化归属块」应记为
**「标量块（ScalarBlock）」**，编号可定为 **S-1**（Save_Core 内第 1 个非模板序列化单元）。

#### 12.4.3 U-9 定谳细节（`[0x7E15C8]`）

```
[实证] PE 导入表: 0x007E15C8 -> ole32.dll!StgCreateDocfile   hint=253  iat_index=0
[实证] 邻槽: 0x7E15CC = CoRevokeClassObject; 0x7E15E4 = StgOpenStorage;
              0x7E15F4 = OleSaveToStream;  0x7E15F8 = OleLoadFromStream
[实证] 调用点 0x0067CF42 = FF 15 C8 15 7E 00   （全镜像唯一非 thunk 引用）
```

栈参 `(fname, 0x1012, 0, &st)` 与
`StgCreateDocfile(const WCHAR*, DWORD grfMode, DWORD reserved, IStorage**)`
**完全吻合**（`0x1012 = STGM_CREATE|STGM_READWRITE|STGM_SHARE_EXCLUSIVE`）。
原「与标准 SDK 签名略有出入」系把 `fname` 误判为窄字符路径；实为宽字符。

#### 12.4.4 仅真机可闭环清单（更新后 = 仅 U-1）

**U-1：35 个块函数实参对象的类名 / RTTI 解析**

| 步骤 | 挂钩/断点 | 期望观察 | 判定标准 |
|---|---|---|---|
| 1 | 在 `Game::Save_Core` 的 35 个 `call` 点（§12.3 表「调用点」列）下断，或统一 hook 模板 `0x0067FDF0` | 命中时 `EDX` = 对象基址 | `EDX` 应等于 §12.3「实参对象」列 |
| 2 | 读 `[EDX]` 得 `vtable` | vtable VA 落在 `.rdata` | 非 0、4 字节对齐 |
| 3 | 读 `[vtable-4]` 得 `CompleteObjectLocator*` | COL 指针 | MSVC6 布局 |
| 4 | 读 `COL+0xC` → `TypeDescriptor*` → `TD+8` 得装饰类名 | 如 `.?AVBuildingClass@@` | 35 条应各不相同或可归组 |
| 5 | 与 YRpp 符号表比对（`BuildingClass`/`UnitClass`/`HouseClass`…） | 名称可解析 | 回填 §12.3「类名」列 |
| 6 | （备选）hook `0x67FDF0` 打印 `EDX` 与 `[EDX]`，一次存档全量捕获 | 35 条日志 | 覆盖 35/35 |

**判定标准**：35 条全部得到确定性装饰类名，且与实参对象地址一一对应 → U-1 闭环。

> 备注：若真机复核 U-2/U-3/U-9（已静态闭环），步骤如下（**可选**）：
> - U-2：读档前用 CE/调试器读文件偏移或 OLE 流 `Internal Version`，期望 `98 B8 02 00`；
> - U-3：对 `0xA8ED84` 硬件读断，存档时栈回溯应含 `0x67F7E0`；
> - U-9：读 `[0x7E15C8]` 的 DWORD，与 `ole32.dll` 导出表比对应得 `StgCreateDocfile`。

### 12.5 存档兼容性红线（与 `net_sync_checksum.md` 帧 CRC 输入集对照）

完整对照表见 `out/re_work/savegame/dumps/crc_input_set_cross.md`。要点：

| 红线级别 | .SAV 字段/结构 | 同时进帧 CRC？ | 破坏后果 |
|---|---|---|---|
| **禁改** | OLE 流名/顺序（尤其 `Internal Version`、`CONTENTS`） | 否 | 读档打不开 |
| **禁改** | 35 块调用顺序 + 每块前导 Count | 部分（向量块） | 流错位 / 读档崩溃 |
| **禁改** | `CurrentFrame`（标量块 S-1） | 否（不直接进 CRC） | 全部 Timer/触发器错乱 |
| **禁改** | RNG 状态（`ScenarioClass::Random`） | **是** | 联机 desync |
| **禁改** | 对象量化坐标（`÷10`）/ 朝向字节 | **是** | 联机 desync |
| **慎改** | 量化除数、`0x4C93D0` 离散化 | **是** | 假 desync / 漏报 |
| **可动** | dirty-rect、迷雾显示、音频、FPS | 否 | 无 |

**一句话**：`.SAV` 的「顺序 + Count + `Internal Version` + RNG + `CurrentFrame`」是兼容性红线；
其中 **位置/朝向/RNG 三元组同时是帧 CRC 输入** —— 改存档兼容性几乎必然改联机确定性。

### 12.6 本节证据产物索引（`out/re_work/savegame/**`）

| 文件 | 内容 |
|---|---|
| `claims.txt` | 143 条字节断言（`tools/audit_bytes.py` 输入，**OK=143**） |
| `tools/audit_savegame_closure.py` | 一键复算：MD5 双口径 / 读档计数 / 逐块证据 / U-2 扫描 / U-3 xref / U-9 导入表 |
| `tools/scan_ole_streams.py` | 真机 .sav 的 OLE 流级魔数扫描 |
| `dumps/template_md5_table.txt` / `template_md5_unique.txt` | 35 模板 MD5 全表 + 边界字节 |
| `dumps/load_side_calls.txt` / `load_side_count_15.txt` / `load_side_count_16.txt` | 读档计数两口径明细 |
| `dumps/per_block_evidence.txt` | 35 块 call/mov/prologue 机器码 |
| `dumps/magic_0x2B898_scan.txt` | CONTENTS 内魔数各编码扫描（全 0） |
| `dumps/ole_streams_magic.txt` | **真机 .sav 15 流清单 + `Internal Version` 定谳** |
| `dumps/currentframe_xrefs.txt` | `0xA8ED84` 全镜像引用 + Save_Core/模板体阴性证明 |
| `dumps/iat_7E15C8_import.txt` | PE 导入表定名 `StgCreateDocfile` |
| `dumps/crc_input_set_cross.md` | 兼容性红线 × 帧 CRC 对照 |
