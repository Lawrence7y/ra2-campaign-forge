# W92 离线崩溃分诊 — 崩溃签名表（2026-11-14）

工作目录 `D:\Project\ra2-campaign-forge`；分析对象镜像：`ra2youli\gamemd.exe`
（sha256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，4,825,360 B，
image base `0x00400000`，段：`.text` 0x401000–0x7E038D / `.rdata` 0x7E1000–0x811074 / `.data` 0x812000+ / `.detour` 0xB93000）。
W88 三趟与 W91 sandbox 实际运行的都是**同一份** gamemd.exe（TRIP_RESULT.json 与 pristine 副本哈希一致）。

分级约定：`[本次实测]`=原件/镜像直接读出；`[静态读码]`=镜像反汇编推得；`[静态推断]`=由寄存器/栈反推；`[转述，不可复核]`=R03 原件已丢失；`[未证]`。

## 0. 原件清点（sha256 前 16 位）

| 记录 | 原件路径 | sha256(16) | 独立性 |
|---|---|---|---|
| W88_C1 | `lead\...\W88_envelope\out\trip_C1\archived_except.txt` | `5864B767BF86D560` | 独立现场 1 |
| W88_C1_late | 同目录 `archived_late_except.txt` | 同上 | **与 C1 字节相同**（落盘两次同一现场） |
| W88_C4b | `trip_C4_b\archived_except.txt` | `AE528DD5ABD4FDBF` | 独立现场 2 |
| W88_C4b_late | 同上 late | 同上 | 与 C4b 相同 |
| W88_C7 | `trip_C7\archived_except.txt` | `BA5E4FD01D776448` | 独立现场 3 |
| W88_C7_late | 同上 late | 同上 | 与 C7 相同 |
| W91_P1 | `...\W91_approach\out\trip_P1\archived_except.txt` | `F8F6BC248039BFD3` | 独立现场 4 |
| W91_P1_late | 同上 late | 同上 | 与 P1 相同 |
| W91_P2 | `trip_P2\archived_except.txt` | `3429FF456C9CA6A0` | 独立现场 5 |
| W91_P2_late | 同上 late | 同上 | 与 P2 相同 |
| W91_sandbox | `sandbox_game\except.txt` | 同上 | **与 P2 字节相同**（同一现场被游戏目录再写一次） |
| ra2youli | `ra2youli\except.txt`（mtime 2026-11-13 06:29，非本轮产生） | `6907F3954CEEA94B` | 独立现场 6 |
| R03 dose800 | **原件丢失** | — | 仅文字转述 |

⇒ **实测独立现场 6 个** + R03 转述 1 条。解析脚本 `EVIDENCE\parse_except.py`，结构化结果 `signatures.json`。

## 1. 签名表

所有 `Bytes at CS:EIP` 与镜像同地址字节 **32/32 完全一致**（三处可读 EIP 各查 32 字节，`EVIDENCE\pe_disasm_stdout.txt`）→ **本轮三处可读崩溃点无运行态补丁迹象** `[本次实测]`。

| # | 现场 | EIP | Access(读) | 崩坏指令（镜像实测字节） | 寄存器要点 | 坏值类型 |
|---|---|---|---|---|---|---|
| S1 | W88_C1（+C1_late） | `0x0047C538` | `0x000A0034` | `FF 50 2C` = `call [eax+0x2C]` | EAX=0x000A0008（vptr 槽），ESI=ECX=0x15EB0800（链对象） | **vptr 被小整数垃圾覆盖**（0x000A0008），读假虚表槽时 fault（0xA0034 未映射；此时 ret 尚未压栈，ESP=0x…044 可证） |
| S2 | W88_C4b | EIP=`0xEAC8D5DF` | `0xEAC8D5DF`（=EIP，取指 fault） | 无（目标未映射，`??`） | EAX=0x001E0000（vptr 槽），ESI=0x15E60800；**栈顶=0x0047C53B**（=S1 调用点下一条） | **vptr 被小整数垃圾覆盖**（0x001E0000 恰可读），取到函数指针 0xEAC8D5DF → 跳到垃圾地址取指 fault（ESP=0x…040 = 已压 ret） |
| S3 | W88_C7 | EIP=`0x00000014` | `0x00000014`（=EIP，取指 fault） | 无（`??`） | EAX=0x15FD38E8（vptr 槽，**堆地址**），ESI=ECX=0x159F7A68，EDI=0x24，EBP=0x23C5；栈顶=0x0047C500 | **vptr 被堆指针覆盖**（非 .rdata），假虚表槽 +0x2C 内容=0x14 被当函数指针 call |
| S4 | W91_P1（+P1_late） | EIP=`0x00000000` | `0x00000000`（=EIP，取指 fault） | 无（`??`） | EAX=0x10D6E7A0（vptr 槽，**堆地址**），ESI=ECX=0x15799EE0，EDI=0x24，EBP=0x22C0；栈顶=0x0047C500 | **vptr 被堆指针覆盖**，假虚表槽 +0x2C 内容=0 被当函数指针 call → EIP=0。**不是 vptr=0**（vptr 本身是非零堆地址），是"取到的函数指针=0" |
| S5 | W91_P2（+P2_late、sandbox） | `0x006F36FE` | `0x11378560` | `DD 84 C8 A0 00 00 00` = `fld qword ptr [eax+ecx*8+0xA0]` | EAX=0x0F2F54C0（数组基址=[edx+0xAC]），ECX=0x00410600（索引=[eax+0x9C]，**垃圾且值落在 .text 区间**） | **数据字段（索引）被垃圾值覆盖**：0x0F2F54C0+0x00410600×8+0xA0=0x11378560（实测复算吻合）→ 数组远越界读 |
| S6 | ra2youli（历史件） | `0x00724737` | `0x00000250` | `8B 85 50 02 00 00` = `mov eax,[ebp+0x250]` | EBP=ECX=0，EAX=0xD6（实参），调用方 `mov ecx,[0x00887368]` | **全局单例指针为 0**：`0x00887368` 处全局=NULL → this=NULL → [0x250] fault |
| S7 | R03 dose800 | `0x0051C2D3` | `0x000001D4` | `FF 90 D4 01 00 00` = `call [eax+0x1D4]`（镜像实测该地址确为此编码） | 转述 EAX=0 | **对象指针为 NULL** 传入虚调用。`[转述，不可复核]`（原件丢失；镜像侧仅能证实 0x51C2D3 处指令形态与转述一致 `[本次实测]`） |

## 2. EIP → 函数入口 → 虚表槽 三段证据

该镜像**无 MSVC RTTI**（`.rdata` 中 `.?AV` 类型描述符 0 个、COL 0 个，`EVIDENCE\pe_disasm2_stdout.txt` §A/C），
类名只能靠槽位语义实证 + 沿用项目已知信息。

### S1/S2 — 调用点 0x47C538，所属函数 0x0047C520–0x0047C54E（`ret` 无 imm，size 0x2F）`[本次实测]`

```
0x47C520: mov al,[0x00A8E9A0]      ; 全局开关
          push esi / test al,al / je 0x47C547
0x47C52A: mov esi,[ecx+0xE4]       ; ← 链头：cell+0xE4（卡片假设字段 [cell+0xE4] 字节级命中）
0x47C530: test esi,esi / je 0x47C547
0x47C534: mov eax,[esi]            ; ← 对象 vptr
0x47C536: mov ecx,esi              ; this
0x47C538: call [eax+0x2C]          ; ← WhatAmI（S1 在此读假虚表 fault；S2 跳到垃圾 fault）
0x47C53B: cmp eax,6                ; 找 RTTI id == 6
0x47C540: mov esi,[esi+0x30]       ; ← 链下一节点：obj+0x30（卡片假设字段命中）
0x47C545: jne 0x47C534
0x47C54B: mov eax,esi / pop esi / ret
```
- 调用方：`0x00439CAD: call 0x47C520`（ecx=edi，来自 FP 比较 `fsub/fcomp` 之后）`[本次实测]`。
- 函数入口无 .rdata 指针指向（155 个 vtable 阵列均不含 0x47C520）→ **非虚函数、帮助函数** `[本次实测]`。
- WhatAmI 槽实证：`.rdata` 中 155 个 ≥16 项连续 .text 指针阵列中，**69 个 vtable 的槽 11（+0x2C）目标都是 `mov eax,N; ret` 形态且 N 两两不同、每个 vtable 唯一**（N=1…69 各一次；N=6 的 vtable 在 `0x007E3EBC`）→ 槽 +0x2C 即 WhatAmI 类 ID 槽 `[本次实测]`；"6=BuildingClass" 之名沿用卡片已知信息（镜像内无名字证据）`[静态推断]`。

### S3/S4 — 调用点 0x47C4FD，所属函数 0x0047C4D0–0x0047C516（`ret 8`，size 0x47）`[本次实测]`

```
0x47C4D0: mov al,[0x00A8E9A0] / push esi / push edi
0x47C4EB: mov esi,[ecx+0xE4]       ; 同上：cell+0xE4
0x47C4F5: mov edi,[esp+0xC]        ; arg1 = 要找的 WhatAmI id（两现场 EDI 均=0x24=36）
0x47C4F9: mov eax,[esi]            ; vptr ← S3/S4 中是堆地址
0x47C4FD: call [eax+0x2C]          ; WhatAmI ← 崩溃调用点（ret 0x47C500 = 两现场栈顶）
0x47C500: cmp eax,edi / mov esi,[esi+0x30] / jne 0x47C4F9
          ... ret 8
```
- 与 S1/S2 是**同族链走查**（同一 `[cell+0xE4]`→`[obj]`→`call [vptr+0x2C]`→`[obj+0x30]` 体），带参版 `ret 8` `[静态读码]`。
- 入口同样无 .rdata 指针 → 帮助函数 `[本次实测]`。
- **S4（EIP=0）判决**：`call [eax+0x2C]` 取指 fault 于 0。EAX（=vptr 槽值）=0x10D6E7A0 ≠ 0 且不在 .rdata → **假 vptr 是堆指针，"假虚表"+0x2C 处内容恰为 0**。vtable 内容被清零说排除（真虚表全在 0x7E1000+）；对象 vptr 被清零说同样排除。判：**vptr 槽被堆指针覆盖 + 假虚表槽读到 0** `[静态读码]`。S3 同理，只是槽内容=0x14。

### S5 — 0x006F36FE，所属函数含 0x6F36DB 起的块（其上游函数 0x6F36?? 以 `ret 4` 结束，0x6F36DB 为其共用尾/入口候选）`[静态读码]`

```
0x6F36E3: mov eax,[ebp]            ; ebp=this(0x15B6AA98，与 EDI 同值，堆对象)
0x6F36E8: call [eax+0x84]          ; 虚 getter（vptr 有效，未崩）
0x6F36F2: mov ecx,[eax+0x9C]       ; ← 索引字段 = 0x00410600（垃圾，值落在 .text 区间）
0x6F36F8: mov eax,[edx+0xAC]       ; edx=[esp+0x10]；数组基址=0x0F2F54C0
0x6F36FE: fld [eax+ecx*8+0xA0]     ; ← 崩：0x11378560 = EAX+ECX*8+0xA0 实测复算吻合
          fcomp [0x7E2800] / fnstsw ax / test ah,0x40  ; 浮点比较
0x6F371B: call [edx+0x84]
```
- 调用方：`0x6F7CBE: call [edx+0x2E4]`（edx=[edi]，edi=0x15B6AA98）→ 返回地址 0x6F7CC4 在栈 `[本次实测]`。
- 索引 0x00410600 位于 .text 范围（0x401000–0x7E038D）→ 该字段像是被**代码地址/残留值**覆盖 `[静态推断]`。
- 无 .rdata 指针指向入口候选 → 非虚函数或证据不足 `[本次实测]`。

### S6 — 0x00724737，函数 0x00724730–0x007248AE（`ret 4`，size 0x181）`[本次实测]`

```
0x724730: sub esp,0xC / push ebp / mov ebp,ecx   ; this 经 ECX
0x724737: mov eax,[ebp+0x250]      ; ← EBP=ECX=0 → 读 0x250 fault
```
- 调用方 0x6D169E 起的循环 `[本次实测]`：
```
0x6D169E: mov eax,[esi]            ; ESI 遍历 0xB0CB78..0xB0CBDC 的 dword 表（.data）
          cmp eax,0x19 / jge skip
          lea eax,[eax+eax*2] / shl eax,5 / add eax,0xB0C1C0   ; elem = 0xB0C1C0 + id*96
          mov eax,[eax+0x24]       ; 实参（崩时 =0xD6）
0x6D16BB: mov ecx,[0x00887368]     ; ← this 来自全局单例；崩时 =0
          push eax / call 0x724730
```
- 判决：**全局 0x00887368 被清 0（或未初始化）**，与对象字段破坏无关 `[本次实测]`。

### S7 — R03 转述地址核对 `[本次实测]`（仅核对代码，崩溃本身 `[转述，不可复核]`）

- `0x0051BF90` 确为函数入口：`sub esp,0x24 / push ebx / push ebp / mov ebp,ecx`。
- `0x0051C2D3` 确为 `FF 90 D4 01 00 00` = `call [eax+0x1D4]`，且随后 `test al,al` —— 与转述指令形态一致。
- `.text` 内 `[eax+0x1D4]` 调用共 25 处 `[本次实测]`。

## 3. 机制归并

**支持 cell-list（`[cell+0xE4]`/`[obj+0x30]`）假设的：**
- **S1、S2（W88_C1/C4b）**：100% 支持 `[本次实测]`。两现场崩在**同一个调用点**（C4b 栈顶返回地址 0x47C53B = S1 调用点的下一条；ESP 0x…040/0x…044 的 4 字节差精确对应"已压 ret/未压 ret"两种 fault 时机）。链走查代码正是读 `[cell+0xE4]` 链头与 `[obj+0x30]` 下一节点；坏值全在**链上对象的 vptr 槽（[obj+0]）**。
- **S3、S4（W88_C7/W91_P1）**：**同族支持，但机制细节修正** `[静态读码]`。崩的是同族 `ret 8` 链走查函数（0x47C4D0，同一 WhatAmI 槽 +0x2C），仍然能被「链上出现了坏对象」解释——但坏值不是"vptr 清 0"，而是 **vptr 槽被堆地址覆盖**（C7: 0x15FD38E8 → 假虚表槽值 0x14；P1: 0x10D6E7A0 → 假虚表槽值 0x0）。即链上挂了内容已被写坏（首 dword 指向堆）的对象/节点。

**不支持 cell-list 假设、须另找机制的：**
- **S5（W91_P2）**：崩在浮点坐标/威胁比较的数组读，坏值是**索引字段**（[retobj+0x9C]=0x00410600，值像代码地址），调用链是 `call [edx+0x2E4]` 的另一条路径，全程未触 `cell+0xE4`/`obj+0x30` 字段。**另立机制**：某对象数据字段被垃圾覆盖（破坏面不同：数据区而非对象头）。`[静态读码]`
- **S6（ra2youli 历史件）**：全局单例 `0x00887368` 为 0 → NULL this。**另立机制**（且该现场非本轮产生，环境/时点不同）。
- **S7（R03 转述）**：EAX=0 是 **NULL 对象指针**直接传进虚调用，与 S1 的"小整数垃圾覆盖"不同型；与 cell-list 假设**相容**（IsCellOccupied 本就工作在 cell 上下文）但**不可复核**，不得作为假设的实测支点。

## 4. 与 Lead 补充判据的对照

- Lead 要求区分「vtable 指针本身为 0」vs「取到的函数指针为 0」：S4 判为**后者**，且附加事实——假 vptr 是**堆指针**（非 0、非 .rdata），故两个原始选项都不完整，真实机制是「**vptr 槽被堆指针覆盖**」。
- Lead 担心"三个不同槽 ⇒ 不同类"：实测 S1–S4 **全部撞在同一个 +0x2C（WhatAmI）槽**，不存在"整个 vtable 被毁"的迹象；坏的是**对象头第一个 dword**，不是 vtable 内容。
- P1/P2 轻场景（仅建筑、~220 对象）崩、P3（1522 对象）不崩：S5（P2）与 S1–S4 属不同破坏面，若同一上游 bug 同时写坏对象头与数据字段可统一，但目前**无证据**，列为未证。

## 5. 未证项

1. R03 原件丢失：EAX=0、Access=0x1D4 仅转述；镜像核对只能证实代码形态。`[转述，不可复核]`
2. "N=6 的 vtable 0x007E3EBC 属 BuildingClass"：镜像无 RTTI 名字，仅沿用项目已知 RTTI 表。`[静态推断]`
3. 覆盖 vptr/索引字段的**写入者**是谁（哪个系统写穿）：本卡只证"哪些字段坏、坏成什么值"，写者未定位。`[未证]`
4. S5 的 `[eax+0x9C]`/`[edx+0xAC]` 字段语义（索引/数组各属于什么结构）无符号名，仅按形态描述。`[未证]`
5. archived 与 archived_late 逐字节相同：无法判断是"同一现场落盘两次"还是"处理流程复制"，取后者保守解释不影响签名。
6. W88_C7 与 W91_P1 的 wanted-id 参数均为 0x24（36）：两趟不同战役输入却同参数，是否巧合未证。`[未证]`
7. EIP=0x000A0008/0x001E0000/0x15FD38E8/0x10D6E7A0 各自的具体来源（哪个堆块/什么写入）需内存取证，离线不可得。`[未证]`
