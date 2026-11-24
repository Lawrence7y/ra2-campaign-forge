# S03-K2 · LAYOUT.md（T3：5 类类布局 + GetSize）

> 目标 `ra2youli\gamemd.exe` SHA256 `73201CC0…F67476`。字节证据 `EVIDENCE\E_T3_*`；复跑 `work\t3_*.py`。
> 纪律：槽号不假定（§981）；字段偏移不定语义，须该类自身写点+读点双支撑；`call [reg+disp]` 是虚调用不计数据读点（本卡排除 `call [edi+0x40]`@0x65D3D2 等 1 处虚调用）。

## 0. 继承链与 vtable（RTTI 定界，`[已证]`）

RTTI 链 `TD+8 名 → COL(COL+0xC→TD) → vft[-1]=COL`，五类全读到名（fail-closed 通过）：

| 类 | TD | COL | vft | 实槽数 | 末槽证据 |
|---|---|---|---|---|---|
| FileClass | 0x815DE0 | — | — | — | 基类 |
| RawFileClass | 0x815DF8 | 0x808790 | **0x7F0904** | 17 | slot16=0x65CA70，slot17=0x8087C0(COL)终止 |
| BufferIOFileClass | 0x815E18 | 0x7FBEF8 | **0x7E3A2C** | 17 | slot16=0x65CA70，slot18=0x7FBF40(COL)终止 |
| CDFileClass | 0x815E38 | 0x7FA4D8 | **0x7E1668** | 17 | slot16=0x65CA70，slot17=0x7FA590(COL=CCFile)终止 |
| CCFileClass | 0x815E58 | 0x7FA590 | **0x7E16B0** | 17 | slot16=0x473AB0，slot17=0 终止 |
| MixFileClass | 0x82C318 | 0x805DE0 | **0x7EDF50** | 1 | slot0=0x5B4630，slot1=0 终止 |

继承：`FileClass ← RawFileClass ← BufferIOFileClass ← CDFileClass ← CCFileClass`；`MixFileClass` 独立（仅 1 槽）。证据链：CCFile slot0 `0x4019A0` 先写 0x7E16B0 再写 0x7E1668 再 `call 0x431B80`（§990 五），CDFile slot0 `0x401950` 写 0x7E1668 + `call 0x431B80`。

## 1. GetSize：5 类全无 `B8 imm32 C3` vtable 槽（`[已证]`）

按 §981 槽契约扫五类 vtable 全槽（0..16 或 0），**无一个 `B8 imm32 C3` 立即数返回槽**：
`CDFile v[12]=0x432050`(first `83 EC 08 56`)、`BufferIO v[12]=0x432050`、`RawFile v[12]=0x65CDD0`(`83 EC 08 56`)、`CCFile v[12]=0x473AE0`(`56 8B F1 8B`)、`MixFile` 仅 1 槽。
⇒ 这些 FileClass 族**不走 `v[12]` GetSize 惯例**，对象大小改用 **分配点 `push <size>; call 0x7C8E17` ↔ 字段 max 两处对账**（弱对账，K1 审计 §3 已标注）。

分配点全 `.text` 扫描（994 处 `push imm; call 0x7C8E17` 带 size，仅统计紧随 `call <ctor>` 者）：

| 类 | ctor | 唯一分配 size | 字段 max | 闭合 |
|---|---|---|---|---|
| **CCFileClass** | 0x4739F0 | **0x6C**（0x407BF3/0x433999，另 16 处 push 0x6C 无关=噪声基线） | +0x68+4=0x6C | ✅ |
| **MixFileClass** | 0x5B3C20 | **0x28**（60 处） | +0x24+4=0x28 | ✅ |
| BufferIOFileClass | 0x431B20 | 无独立堆分配（内嵌基类，ctor 3 调用点 0x47A9D3/0x47AA03/0x47AA33 均为栈对象） | 字段见 §3 | ❌ 无独立 size |
| RawFileClass | (dtor 0x65CA00) | 无独立堆分配（内嵌基类） | 字段见 §4 | ❌ |
| CDFileClass | 0x401950(dtor) | 无独立堆分配（内嵌基类） | 字段见 §2 | ❌ |

**GetSize 闭合 = 2/5**（CCFile 0x6C、MixFile 0x28）。基线核对：`B8 imm32 C3` 全镜像 666 / `B8 imm32` 837（K1/§981 已入账），纯字节形态零特异性，本卡全靠 vtable 槽锚定。

## 2. CDFileClass 字段表（17 槽，族内实测偏移集）

| 偏移 | 宽 | 类型 | 写者 | 读者 | 语义 | 级 |
|---|---|---|---|---|---|---|
| +0x18 | 4 | ptr | 基类 | 0x401940 (1) | 文件名指针（slot1 getter `mov eax,[ecx+0x18];ret`） | 静态推断 |
| +0x24/+0x25/+0x29/+0x30 | 1/1/1/4 | flags/ptr | 0x431BA1…/0x431BA4 | 0x431B93/0x431F10/0x431F37/0x431B86 | 继承 BufferIO 的 buffer 标志与指针 | 静态推断 |
| +0x54 | 1 | byte | — | 0x47AE26/0x47AF2D (2) | CD 状态位（读 2，写点在族外） | 未证 |

## 3. BufferIOFileClass 字段表（ctor 0x431B20 / dtor 0x431B80 / vft COL 0x7FBEF8）

| 偏移 | 宽 | 写者(全) | 读者 | 语义 | 级 |
|---|---|---|---|---|---|
| +0x04..+0x1E | 4/2 | 0x431B27..0x431B41 (各 1) | 0 | ctor 初始化（基类 FileClass 字段） | 静态推断 |
| +0x20 | 1 | 0x431B45 | 0 | ctor 清零 | 静态推断 |
| **+0x24** | 1 | 0x432631/0x431B48/0x431BA1 (3) | 0x432623/0x431B93 (2) | buffer-own 标志 | 静态推断 |
| +0x25 | 1 | 6 处 (0x431B4B/0x431BAC/0x43263C/0x431F9B/0x431FAA/0x432035) | 0 | dirty/alloc 标志（写 6 读 0） | 静态推断 |
| +0x26 | 1 | 5 处 | 0x431F80 (1) | buffer 状态 | 静态推断 |
| **+0x29** | 1 | 7 处 | 0x431E91/0x431F76/0x431FB4 (3) | buffer 模式标志（读写均≥3） | **已证**（该类自身 7W/3R） |
| +0x2C | 4 | 0x431B5A/0x431FC6 | 0x432014 (1) | buffer 长度 | 静态推断 |
| **+0x30** | 4 | 0x432634/0x431B5D/0x431BA4 (3) | 0x432616/0x431B86 (2) | buffer 指针（dtor 0x432623 读后 free via 0x7C8B3D） | **已证** |
| **+0x34** | 4 | 0x432639/0x431B60/0x431BA9 (3) | 0x431FCE (1) | buffer 容量/偏移 | 静态推断 |
| +0x38..+0x4C | 4 | 各 2 处 | 0/1 | ctor 初始化区，读点不足 | 未证 |
| +0x50 | 4 | 0x431B75/0x431FF3 | 0x431F85/0x431FF6 | 状态字（2W/2R） | 静态推断 |

> §990 五条 dtor 证据独立复现：slot0 `0x432610` 与 `0x431B80` 61/64 字节全等（仅 2 处 call rel32 异），尾部 `test [esp+0xC],1`→delete→`ret 4`。本卡 vtable dump 确认 slot0=0x432610、COL=0x7FBEF8。

## 4. RawFileClass 字段表（vft 0x7F0904，dtor 0x65CA00）

| 偏移 | 宽 | 写者(全) | 读者 | 语义 | 级 |
|---|---|---|---|---|---|
| +0x0C | 4 | — | 6 (0x65CF22/0x65CF3B/0x65CFA8/0x65CFF1/0x65D019/0x65D10E) | 只读状态（写点在族外/未定位） | 静态推断 |
| +0x10 | 4 | 0x65D116 | 3 (0x65CF04/0x65CFF6/0x65D0D6) | 文件位置/长度 | 静态推断 |
| **+0x14** | 4 | 0x65D3D6/0x65CCCF/0x65CA36 (3) | 7 (0x65D3B3/0x65D420/0x65CF83/0x65CF55…) | 文件句柄（CreateFileA 写，Open/Close 读） | **已证** |
| **+0x18** | 4 | 0x65D3F4/0x65CADB/0x65CA54 (3) | 14 (0x65D3C1/0x65D3E4/0x65CAC4/0x65CBF4…) | 文件名指针（strdup 写，多处读） | **已证** |
| +0x20 | 1 | 0x65D3FB/0x65CAE2/0x65CA5B (3) | 3 (0x65D3DD/0x65CACB/0x65CA3D) | 打开/读写标志 byte | **已证**（3W/3R） |

> 排除：`call [edi+0x40]`@0x65D3D2、`call [eax+0x34]`@0x473D1A 为**虚调用**，不计数据字段读点（显式剔除 2 处）。`0x65CA00` 与 `0x65D3A0` 前 16 字节逐字相同（`56 8B F1 C7 06 04 09 7F 00 FF 15 1C 09 7F 00`），均写 RawFileClass vft。

## 5. CCFileClass / MixFileClass（K1 已证，本卡复核）

- **CCFileClass** vft 0x7E16B0，size 0x6C，12 字段（K1 口径 12 of 31），文件名指针 +0x18(strdup)，无持久化 MIX 指针；越界写 0 处（K1 审计 §5）。
- **MixFileClass** vft 0x7EDF50，size 0x28，12 字段完整（偏移集 00,04,08,0C,10,11,12,14,18,1C,20,24），+0x0C=strdup 名、`+0x14`=count、`+0x20`=index(new num*12)、`+0x24`=datastart；越界写 0 处。
