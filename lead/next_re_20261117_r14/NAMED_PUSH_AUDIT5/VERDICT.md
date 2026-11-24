# NAMED_PUSH_AUDIT5 — S06_B1(4) + S20_B1(7) = 11 行 异族独立审计（VERDICT）

审计员：异族独立审计（非 S06 / S20 执行器）。**本文件一切地址与字节均为本人用 capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26 从 `ra2youli\gamemd.exe` 独立反汇编所得**；执行器 `EVIDENCE\ROW_*.txt`、`REPORT.md`、`base_rate.tsv` 未作任何证据引用（只在 §0 用于确认"要审哪些行"）。

镜像校验：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
SHA-256 = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（= 卡面期望，实测相符）。
ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`。

---

## 0. 11 个 entry 的取法（卡面要求先交代）

```text
NAMED_PUSH_S06_B1\delta.tsv   表头 6 列：entry subsystem name one_line_semantics grade evidence_path
NAMED_PUSH_S20_B1\delta.tsv   同表头
取法：跳表头，取第 1 列（entry）非空的全部数据行，逐目录全取，不做 grade/名过滤。
```

| 来源目录 | 取到的 entry | 行数 |
|---|---|---:|
| `NAMED_PUSH_S06_B1\delta.tsv` | `004839F0` `00483C10` `005F92D0` `005FC570` | 4 |
| `NAMED_PUSH_S20_B1\delta.tsv` | `00423AC0` `00428EA0` `004A7C90` `004C5A30` `004C5AC0` `005F44A0` `0062D7A0` | 7 |
| 合计 | | **11** |

> **与卡面模板的偏差（先声明）**：卡面（`_cards\a-NAMED-PUSH-2.md`）正文写的是 `S14_B2`(6)+`S05_B1`(3)+`S05_B2`(2)，派单消息与输出目录已改为 `S06_B1`(4)+`S20_B1`(7)。本审计**按派单消息的来源与行数执行**（11 行 = 4+7），卡面 §"本批要特别回答的一件事"所述"S14 那 4 行标量析构"在本批对应为 `00428EA0` `004A7C90` `004C5AC0`（标量删除析构）+ `005F44A0`（非析构注销方法）这 4 个"容器 Find 返 -1"行，专项结论见 SUMMARY §5。

---

## 1. `004839F0` — S06 `CellClass::slot5` ｜ **PASS**（3b2）

### ② 类身份（独立成立）
- 槽地址 `007E4F00` = 表基 `007E4EEC` + `0x14`（slot#5），4B 值实测 = `004839F0`（本 entry）✓
- RTTI 链：`[007E4EEC-4]=007FD078`(COL, sig=0) → `[007FD078+0xC]=0081CD70`(TD) → `0081CD70+8` 内联串 = `. ?AVCellClass@@`（实测 `56 41 3F 2E` = `.?AV`）
- ⇒ 类名 `CellClass`，槽号 5 与 name 栏 `slot5` 自洽；本 entry 在 `.rdata` 中**只被 1 张表持有**（全表枚举：1/1）

### ③b 形态 = ③b②（可伪证错误码/返回约定）
| 环节 | 字节（实测） |
|---|---|
| 站点 | `004839FF E8 7C C9 F8 FF` `call 0x410380`（`0x483A04+0xFFF8C97C=0x410380`） |
| 判 | `00483A04 33 DB` `xor ebx,ebx`（不碰 eax）→ `00483A06 3B C3` `cmp eax,ebx`（≡`cmp eax,0`） |
| 分支 | `00483A08 0F 8C F2 01 00 00` `jl 0x483C00`（`0x483A0E+0x1F2`） |
| 失败返 | 被调空参 `00410385 85 FF test edi,edi` / `00410387 75 09 jne` → `00410389 B8 03 40 00 80 mov eax,0x80004003`（`E_POINTER`）；流读失败 `004103A3 7C 31 jl 0x4103D6` 原样外传负值；唯一出口 `004103D7 C2 08 00 ret 8` |
| 成功返 | 正路 `0041039E FF 50 0C call [eax+0xC]`（= 流 **Read** 槽）后 `004103A1 85 C0 test eax,eax` 非负 → 走到 `004103D6` 时 eax=0 |
| 调用方两路 | 失败路 `00483C00 5F 5E 5D 5B 59 C2 08 00`（pop edi/esi/ebp/ebx/ecx; ret 8）**跳过 `00483BFE 33 C0`**，eax 原样返负 HRESULT；成功路 `00483A0E` 起 `00483A19 call 0x4101C0` 构造基类子对象、`00483A24 C7 06 EC 4E 7E 00` 起装 4 张表、`00483A84 FF 51 0C` / `00483AAB FF 50 0C` 经 Read 槽逐项读入，`00483BFE 33 C0` 归一返 0 |

- `test/cmp` 与 `jl` 之间零指令、无 eax 覆写 ✓；本机关**单 call 站点**，非"多路汇入同一 call" ✓
- 方向：`+0xC = Read`（`0x410380` 内部 `push 0; lea ecx,[esp+0x10]; push 4; push ecx; push edi; call [eax+0xC]` = `Read(this, pv, 4, pcb=NULL)`），与"流读入"语义一致 ✓

### ④ 使用见证（活虚表装表点，行外）
- `0047B36F C7 06 EC 4E 7E 00 mov [esi],0x7E4EEC`，宿主 `0047B360`：`0047B360 8B 44 24 04 mov eax,[esp+4]` → `0047B368 E8 53 4E F9 FF call 0x4101C0`（基类构造，与本 entry 体内 `00483A19` 同一个基类 ctor）→ 装 4 张表 → `0047B390 8B C6 mov eax,esi` / `0047B393 C2 04 00 ret 4`（返 this）⇒ **构造器装活表**，装表在**行外**、与 ② 站点不共用 ✓
- ㉓ 排除项（我另行核对，非引用执行器）：`0047BB69 C7 06 EC 4E 7E 00` 所在 `0047BB60` 是**析构器**（体内 `0047BBE1 E8 0A 46 F9 FF call 0x4101F0` 基类析构、无返 this），故**不得**作 ④；「同一 (site,slot) 活死两表争抢」情形不存在（该表另两处写点 `0047BD5C`/`00483A24` 分别为另一 ctor 与本 entry 行内自重装）

### ④ 与 ② 不同源 = `no`（不同源）
② 走 `.rdata` 数据链（COL→TD→内联串），④ 走 `.text` 装表指令；不是同一虚表槽既证身份又证使用 ✓

### ⑤ 语义与实测
第 4 列逐项实测相符（见上表）；**读写方向正确**（Read=+0xC）；子型 ③b② 正确。**判 PASS。**

---

## 2. `00483C10` — S06 `CellClass::slot6` ｜ **PASS**（3b2）

### ② 类身份
- 槽 `007E4F04` = `007E4EEC`+`0x18`（slot#6），4B 值 = `00483C10` ✓；RTTI 同上：`007FD078` → `0081CD70` → `. ?AVCellClass@@`（同一张表，槽号 6 与 `slot6` 自洽）✓；全表枚举 1/1 ✓

### ③b 形态 = ③b②
| 环节 | 字节（实测） |
|---|---|
| 站点 | `00483C22 E8 F9 C6 F8 FF` `call 0x410320`（`0x483C27+0xFFF8C6F9=0x410320`） |
| 判/分支 | `00483C27 85 C0 test eax,eax` → `00483C29 7C 4E jl 0x483C79`（`0x483C2B+0x4E`）零间隔、无 eax 覆写 |
| 失败返 | 空参 `00410325 85 F6 test esi,esi` / `00410328 75 0A jne` → `0041032B B8 03 40 00 80 mov eax,0x80004003`（`E_POINTER`）+ `00410331 C2 0C 00 ret 0xC`；写失败 `0041034D 7C 23 jl 0x410372`、`00410364 7C 0C jl 0x410372` 原样外传 |
| 成功返 | 正路 `00410348 FF 50 10 call [eax+0x10]`（= 流 **Write** 槽）；成功路尾 `0041036A 85 C9 test ecx,ecx`/`je` 后到 `00410374 C2 0C 00 ret 0xC`，eax=0 |
| 调用方两路 | 失败路 `00483C79 5F 5E 5B C2 0C 00`（pop edi/esi/ebx; ret 0xC）eax 原样为负；成功路 `00483C2B` 起经 `00483C45 FF 52 10`、`00483C67 FF 51 10` 写计数与逐元素（`00483C56..00483C75` 为计数循环，`00483C73 3B F8 cmp edi,eax` / `00483C75 7C DF jl`），`00483C77 33 C0` 归一返 0 |

- 方向：`+0x10 = Write`（`0x410320` 内部同样的 COM stdcall 形态 `Write(this, pv, 4, pcb)`），与"流写出"语义一致 ✓
- 子型 ③b② 正确；**判 PASS。**

### ④ 使用见证
- `0047B36F`（同 §1 的 ctor `0047B360`，行外、活装表、返 this）✓；㉓ 排除项同 §1。

### ④②不同源 = `no` ✓
### ⑤ 语义：方向（Write=+0x10）、两路动作、常量字节全部相符 ✓

---

## 3. `005F92D0` — S06 `IsometricTileTypeClass::slot25` ｜ **PASS**（3b2，附 2 条需账）

### ② 类身份
- 槽 `007ECCAC` = `007ECC48`+`0x64`（slot#25），4B 值 = `005F92D0` ✓
- RTTI：`[007ECC48-4]=00804BC0`(COL, sig=0) → `[COL+0xC]=008290C8`(TD) → `TD+8` 内联串 `. ?AVIsometricTileTypeClass@@` ✓（与 name 栏同族、槽号自洽；CHD=`00804BB0`）
- **全表枚举（COMMON-R12 判据 1）**：本 entry 在 `.rdata` 中被 **2** 张表持有，同为 slot#25：
  - `007ECC48`（`IsometricTileTypeClass`，40 槽）
  - `007EF2D8`（RTTI 实测 `. ?AVObjectTypeClass@@`，40 槽）——两表 slot24/25/26 依次相同（`00410C20` / `005F92D0` / `00410B90`）
  - ⇒ 属**继承共享**（派生类未覆写该槽），非跨类误挂。见 §3-需账(b)。

### ③b 形态 = ③b②（Find 返 -1 哨兵；模板级、低信息量）
| 环节 | 字节（实测） |
|---|---|
| 站点 | `005F93B5 E8 16 81 15 00` `call 0x7514D0`（`0x5F93BA+0x158116`），调用点前 `005F93AD 85 C0 test eax,eax` / `005F93AF 74 10 je` 为 sscanf 是否命中的前置守卫 |
| 判 | `005F93BA 83 F8 FF cmp eax,-1`（紧随 call，零间隔） |
| 分支 | `005F93BD 74 02 je 0x5F93C1`（跳过 `005F93BF 8B F8 mov edi,eax`） |
| 失败返 | `00751515 5F pop edi` → `00751516 83 C8 FF or eax,-1` → `00751519 5E pop esi` → `0075151A C3 ret` ⇒ **返 -1** |
| 成功返 | `0075151B 8B C6 mov eax,esi` → `0075151F C3 ret` ⇒ **返下标** |
| 调用方两路 | `edi` 在分支前已由 `005F938B 8B BB F0 01 00 00 mov edi,[ebx+0x1f0]` 装入旧值；`je` 命中（eax=-1）→ 跳过 `mov edi,eax`，`edi` 保持旧值；未命中（eax=下标）→ `edi=下标`；两路汇合于 `005F93C1`，由 `005F93D5 89 BB F0 01 00 00 mov [ebx+0x1f0],edi` 落库 ⇒ 效果为"未命中保留旧默认 / 命中改写为新下标" |
| 同型第二站点 | `005F93F1 call 0x7514D0` / `005F93F6 83 F8 FF cmp` / `005F93F9 75 02 jne 0x5F93FD` / `005F93FB 8B C7 mov eax,edi`（旧值）→ `005F9403 mov [ebx+0x1f4],eax`（+0x1f4 同型）✓ |

- 零间隔分支、无 eax 覆写 ✓；每站点单 call、非多路汇入 ✓
- 非流 I/O，无读写方向问题 ✓

### ④ 使用见证（活虚表装表点，行外）
- `00544A42 C7 06 48 CC 7E 00 mov [esi],0x7ECC48`，宿主 `00544A00`：`mov eax,[esp+4]` → `00544A08 E8 13 29 0B 00 call 0x5F7320`（基类构造）→ 装 `00544A42`–`00544A56` 4 张表 → `00544A5D 8B C6 mov eax,esi` / `00544A60 C2 04 00 ret 4`（返 this）⇒ 构造器活装表 ✓
- ㉓ 排除：`00544A70`+ 的 `00544A77 C7 06 48 CC 7E 00` 位于 `push ecx; push ebx; push esi; mov esi,ecx; mov dl,1` 之后（delete 标志形态）= **析构器**，不作 ④ ✓

### 需账（不影响 PASS 结论，但必须由执行器改字）
- **(a)「两路动作真不同」表述过强**：两路**汇合后执行同一条** `005F93D5 mov [ebx+0x1f0],edi`，指令序列相同，差异仅在 `edi` 的值（旧值 vs 新下标）。因此本行不满足"两路动作（指令级）不同"，只满足"效果不同"。③b② 的判据（失败返什么/成功返什么/调用方哪条指令分支）**仍然成立**，故不判 FAIL，但该措辞须收窄。
- **(b) 归属为派生类**：本 entry 同时驻 `ObjectTypeClass` 表 `007EF2D8` slot#25（同址），说明该槽由基类定义、派生类未覆写；name 写作 `IsometricTileTypeClass::slot25` 只是"对象解析结果"，非"定义处"。② 的操作化（表+槽号→entry、RTTI 名与行名一致）成立，故不 FAIL，但归属须标注。
- **(c) 分支标签"je 命中"易误读**：`je` 在 eax==**-1**（未命中）时成立。执行器同句后文"否则 edi=下标"动作映射正确、括号"（保留旧默认）"亦正确，判为措辞歧义而非方向写反。

---

## 4. `005FC570` — S06 `OverlayClass::slot73` ｜ **PASS**（3b2）

### ② 类身份
- 槽 `007EF4F8` = `007EF3D4`+`0x124`（slot#73），4B 值 = `005FC570` ✓（该表 122 槽）
- RTTI：`[007EF3D4-4]=00807638`(COL, sig=0) → `[COL+0xC]=00833458`(TD) → `TD+8` 内联串 `. ?AVOverlayClass@@` ✓（与 name 栏同族、槽号自洽；CHD=`00807628`）；全表枚举 **1/1** ✓

### ③b 形态 = ③b②
| 环节 | 字节（实测） |
|---|---|
| 站点 | `005FD1BB E8 50 7E E8 FF` `call 0x485010`（`0x5FD1C0+0xFFE87E50`） |
| 转发桩 | `00485010 8B 49 44 mov ecx,[ecx+0x44]` → `00485013 E9 08 8D 17 00 jmp 0x5FDD20`（this 调整后的尾跳） |
| 判/分支 | `005FD1C0 83 F8 FF cmp eax,-1` / `005FD1C3 74 35 je 0x5FD1FA`（零间隔、无 eax 覆写） |
| 失败返 | `005FDDD5 5F 5E 5D` → `005FDDD8 83 C8 FF or eax,-1` → `005FDDDB 5B 59 C3` ⇒ **返 -1** |
| 成功返 | `005FDDC1 33 C0 xor eax,eax` → `005FDDC8 C3 ret`（返 0）；或 `005FDDC9 8B 80 98 00 00 00 mov eax,[eax+0x98]` → `005FDDD4 C3 ret`（返字段值） |
| 调用方两路（真不同） | 未命中 → 直跳 `005FD1FA`，**整块跳过**；命中 → `005FD1C5 8B 15 EC F4 B0 00 mov edx,[0xB0F4EC]` / `005FD1CB 8B 04 82 mov eax,[edx+eax*4]` 取表项（`005FD1CE 85 C0 test eax,eax` / `005FD1D0 74 28 je` 再判空）→ `005FD1E7 89 86 D4 00 00 00 mov [esi+0xD4],eax` 落库，另 `005FD1F4 mov [esi+0xFC],ecx` |

- 被调语义旁证（我另读）：`005FDD20` 以 `0xB0F4EC`/`0xB0F4F8`（count）遍历，命中区间判据 `cmp ecx,edx` / `jl`、`005FDD76 7C 51 jl 0x5FDDC9`，未命中 `or eax,-1` ⇒ 确为"表内定位，未命中 -1"✓；非流 I/O，无方向问题 ✓

### ④ 使用见证（活虚表装表点，行外）
- `005FC38F C7 06 D4 F3 7E 00 mov [esi],0x7EF3D4`，宿主 `005FC380`：`sub esp,0xC; push esi; mov esi,ecx` → `005FC386 E8 75 75 FF FF call 0x5F3900`（基类构造）→ 装表 ⇒ 构造器活装表，行外 ✓
- ㉓ 核查：本 entry 体内 `005FDD...` 的 `or eax,-1` 属**被调**返回约定，执行器已显式声明不作 ④（正确，避免 ④ 与被调同源）；`atexit` 装表点未采用 ✓

### ④②不同源 = `no` ✓（`.rdata` RTTI 链 vs `005FC38F` 装表指令）
### ⑤ 语义：判"未命中跳过 / 命中取表项写 `this+0xD4`"与实测逐条相符；无方向问题 ✓ **判 PASS。**

---

## 5. `00423AC0` — S20 `AnimClass::vslot23` ｜ **PASS**（3b4）

### ② 类身份
- 槽 `007E33B0` = `007E3354`+`0x5C`（slot#23，表 124 槽），4B 值 = `00423AC0` ✓
- RTTI：`COL=007FBA60`(sig=0) → `TD=008182C8` → `. ?AVAnimClass@@` ✓；槽号 23 与 `vslot23` 自洽；全表枚举 **1/1** ✓

### ③b 形态 = ③b④（完整循环 I/O + 边界检查 + 循环体内非栈写）
| 要素 | 字节（实测） |
|---|---|
| 半径来源 | `00423FF6 8B 80 3C 03 00 00 mov eax,[eax+0x33C]`（eax 来自 `00423ADC 8B 86 C8 00 00 00 mov eax,[esi+0xC8]` = 类型对象） |
| 外层循环 | 顶点 `0042400C 8B C8 mov ecx,eax` / `0042400E F7 D9 neg ecx` / `00424010 3B C8 cmp ecx,eax`；回边 `00424269 0F 8E 9D FD FF FF jle 0x42400C`（`0x42426F+0xFFFFFD9D`）✓ |
| 内层循环 | 顶点 `0042402A DB 44 24 18 fild [esp+0x18]`；回边 `0042424C 0F 8E D8 FD FF FF jle 0x42402A` ✓ |
| 边界检查 | `00424051 3B 82 3C 03 00 00 cmp eax,[edx+0x33C]` → `00424057 0F 8F D8 01 00 00 jg 0x424235`（`0x42405D+0x1D8`）= 越界跳过本格 ✓ |
| 读 | `004240BB E8 E0 16 14 00 call 0x5657A0`（取格内对象）→ `004240C0 8B F8 mov edi,eax` |
| 判 | `004240C4 8B CF mov ecx,edi` / `004240C6 E8 15 F8 05 00 call 0x4838E0` → `004240CB 84 C0 test al,al` / `004240CD 0F 84 62 01 00 00 je 0x424235`（无效对象亦跳过） |
| **循环体内非栈写** | `00424155 88 87 1E 01 00 00 mov byte ptr [edi+0x11E],al`（写回 `edi` = 刚查到的**对象**，非 `[esp+*]` 栈槽；紧接 `00424160 8B CF mov ecx,edi` / `00424162 call 0x47FB90` 再次以该对象为 this ⇒ 对象指针确证） |
| 推进 | `0042423F 40 inc eax` / `00424240 8B 91 3C 03 00 00 mov edx,[ecx+0x33C]` / `0042424A 3B C2 cmp eax,edx` / `0042424C jle` ✓ |

- 四要素（读→判→写→推进）齐备、写落在**循环体内**且非栈 ✓；不属 ③a，不属"多路汇入同一 call" ✓

### ④ 使用见证（活虚表装表点，行外）
- `0042201C C7 06 54 33 7E 00 mov [esi],0x7E3354`，宿主 `00421EA0`：`push ebp; mov ebp,esp; and esp,-8; sub esp,0x54; push ebx/esi/edi; mov esi,ecx` → `00421EAE E8 4D 1A 1D 00 call 0x5F3900`（基类构造）→ …装表 ⇒ 构造器活装表 ✓（`atexit` 装表点未采用）
- ㉓ 对照：`004228EB C7 06 54 33 7E 00`（`mov dl,1` + 复位 4 表 = 析构器形态）与 `004252BB` 均**未**用作 ④ ✓

### ④②不同源 = `no` ✓
### ⑤ 语义：`[Type+0x33C]` 半径 / 内外双层循环 / 越界跳过 / 写回被查对象 +0x11E —— 逐项相符；无读写方向问题（写口确为对象字段）✓ **判 PASS。**

---

## 6. `00428EA0` — S20 `AnimTypeClass::vslot8`（标量删除析构）｜ **PASS**（3b2，附专项说明）

### ② 类身份
- 槽 `007E3628` = `007E3608`+`0x20`（slot#8），4B 值 = `00428EA0` ✓
- RTTI：`COL=007FBBB0`(sig=0) → `TD=00818330` → `. ?AVAnimTypeClass@@` ✓；槽号与 `vslot8` 自洽；全表枚举 **1/1** ✓

### ③b 形态 = ③b②（容器 `Find` 未命中返 -1）
| 环节 | 字节（实测） |
|---|---|
| 容器 1 活表 | `[0xB0F670]` 运行时值 = `007E91EC`（`. ?AV?$DynamicVectorClass@PAVAbstractClass@@@@`）：init `00725350 33 C0` / `00725352 68 90 53 72 00 push 0x725390`（atexit dtor）→ `0072536D C7 05 70 F6 B0 00 EC 91 7E 00` 装活表 → `00725386 E8 FF 43 0A 00 call 0x7C978A` 注册 → `ret`；被注册的 dtor `00725390` 在 `00725398 C7 05 70 F6 B0 00 0C 92 7E 00` 写**死表** `007E920C`(`?$VectorClass@PAVAbstractClass@@@`) ⇒ **活/死按 ㉓ 已分清，本行取的是活表** |
| 站点 1 | `00428EC8 8B 15 70 F6 B0 00 mov edx,[0xB0F670]` / `00428ED3 FF 52 10 call [edx+0x10]`（`vt[4]`） |
| 判/分支 | `00428ED6 83 F8 FF cmp eax,-1`（零间隔）/ `00428ED9 74 2D je 0x428F08`（`0x428EDB+0x2D`） |
| 失败返 | 被调 `004E0550`：`004E056F 83 C8 FF or eax,-1` → `004E0573 C2 04 00 ret 4` ⇒ **-1** |
| 成功返 | 命中 `004E0565 74 0B je 0x4E0572` → `004E0573 ret 4`（eax=下标） |
| 调用方两路（真不同） | 未命中 → 直跳 `00428F08` 做**第二个注册表**；命中 → `00428EDB`–`00428EE8` 计数减一 `mov [0xB0F680],ecx` + `00428EF0`–`00428F06` 前移压缩循环（`00428EFA 89 54 81 FC mov [ecx+eax*4-4],edx` 非栈写、`00428F04 3B C1 cmp eax,ecx` 边界、`00428F06 7C E8 jl` 回边） |
| 站点 2 | `00428F08 8B 15 50 41 8B 00 mov edx,[0x8B4150]`（活表 `007EA2E4`=`?$DynamicVectorClass@PAVAnimTypeClass@@@`，`vt[4]=004EE1B0`；死表 `007EA304` 由 atexit 装）/ `00428F1C FF 52 10` / `00428F1F 83 F8 FF cmp` / `00428F22 74 2D je 0x428F51` |
| 收尾 | `00428F51 8B CE mov ecx,esi` / `00428F53 E8 A8 E4 1C 00 call 0x5F7400`（基类析构）/ `00428F58 F6 44 24 0C 01 test byte [esp+0xC],1` / `00428F60 E8 D8 FB 39 00 call 0x7C8B3D`（free）/ `00428F6C C2 04 00 ret 4` |

### ④ 使用见证（活虚表装表点，行外）
- `00427731 C7 06 08 36 7E 00 mov [esi],0x7E3608`，宿主 `00427530`：`mov eax,[esp+4]; push ebx/esi/edi; mov esi,ecx; push eax` → `0042753A E8 51 FB 1C 00 call 0x5F7090`（基类构造）→ 装表 ⇒ 构造器活装表 ✓
- ㉓：本 entry 体内 `00428EAD C7 06 08 36 7E 00` 的**行内自重装**已排除（不作为 ④）；`0042788D`（`mov ecx,0xB0F670` 起 = 同族删除析构）亦未采用 ✓

### ④②不同源 = `no` ✓
### ⑤ 语义：`复位 4 表 / 两注册表摘链 / 基类析构 / 按标志释放` 与字节逐项相符；无读写方向问题 ✓

> **形态信息量声明**（专项见 SUMMARY §5）：该 ③b② 只证明"从容器 X 自摘链"这一层的可伪证返回约定，属**模板级、低信息量**；本行证明力主要来自 ②（哪张表哪个类）与 ④/⑤ 的逐字节吻合，**不应**据此单独扩域。同族 `Save` 语义另见 ⑤ 核对。

---

## 7. `004A7C90` — S20 `DiskLaserClass::slot8`（标量删除析构）｜ **PASS**（3b2）

### ② 类身份
- 槽 `007E5FD8` = `007E5FB8`+`0x20`（slot#8），4B 值 = `004A7C90` ✓；RTTI `. ?AVDiskLaserClass@@`（COL `007FFBF0` → TD `0081FF90`）✓；全表枚举 **1/1** ✓

### ③b 形态 = ③b②
| 环节 | 字节（实测） |
|---|---|
| 容器活表 | `[0x8A0208]` = `007E5EDC`（`. ?AV?$DynamicVectorClass@PAVDiskLaserClass@@@@`），装表 `004A6C8D C7 05 08 02 8A 00 DC 5E 7E 00`，紧随 `004A6CA6 E8 DF 2A 32 00 call 0x7C978A` 注册 atexit dtor `004A6CB0`；该 dtor 在 `004A6CB8` 写死表 `007E5EFC`(`?$VectorClass@PAVDiskLaserClass@@@`) ⇒ 活/死分清 ✓ |
| 站点 | `004A7CB8 8B 15 08 02 8A 00 mov edx,[0x8A0208]` / `004A7CC3 FF 52 10 call [edx+0x10]`（`vt[4]=004A7FB0`，实测 `[0x7E5EDC+0x10]=004A7FB0`） |
| 判/分支 | `004A7CC6 83 F8 FF cmp eax,-1` / `004A7CC9 74 2D je 0x4A7CF8`（零间隔、无 eax 覆写） |
| 失败返 | 被调尾 `004A7FCF 83 C8 FF or eax,-1` → `004A7FD3 C2 04 00 ret 4` ⇒ **-1** |
| 成功返 | 命中 `004A7FC5 74 0B je 0x4A7FD2` → `ret 4`（eax=下标） |
| 调用方两路（真不同） | 未命中 → 跳 `004A7CF8` 收尾；命中 → `004A7CD8 89 0D 18 02 8A 00 mov [0x8A0218],ecx`（计数减一）+ 压缩循环 `004A7CE0`–`004A7CF6`（`004A7CEA 89 54 81 FC mov [ecx+eax*4-4],edx`、`004A7CF4 3B C1 cmp`、`004A7CF6 7C E8 jl`） |
| 收尾 | `004A7CFA E8 F1 84 F6 FF call 0x4101F0`（基类析构）/ `004A7CFF F6 44 24 0C 01 test byte [esp+0xC],1` / `004A7D07 E8 31 0E 32 00 call 0x7C8B3D` / `004A7D13 C2 04 00 ret 4` |

### ④ 使用见证
- `004A7A3A C7 06 B8 5F 7E 00 mov [esi],0x7E5FB8`，宿主 `004A7A30`：`push esi; mov esi,ecx` → `004A7A33 E8 38 87 F6 FF call 0x410170`（基类构造）→ 装表 ⇒ 构造器活装表，行外 ✓
- ㉓：行内 `004A7C9D C7 06 B8 5F 7E 00` 自重装已排除 ✓

### ④②不同源 = `no` ✓
### ⑤ 语义：`复位 4 表 / 0x8A0208 摘链（计数 0x8A0218、数组 0x8A020C）/ 基类析构 / 按标志释放` 与字节相符 ✓ **判 PASS。**

---

## 8. `004C5A30` — S20 `EMPulseClass::slot5`（流**读入**构造）｜ **PASS**（3b2）

### ② 类身份
- 槽 `007E87BC` = `007E87A8`+`0x14`（slot#5），4B 值 = `004C5A30` ✓；RTTI `. ?AVEMPulseClass@@`（COL `008004D8` → TD `008208D0`）✓；全表枚举 **1/1** ✓

### ③b 形态 = ③b②（**本函数自身**返回错误码 —— 最干净的 ③b② 读法也成立）
| 环节 | 字节（实测） |
|---|---|
| 站点 | `004C5A3B E8 40 A9 F4 FF call 0x410380`（`0x4C5A40+0xFFF4A940`） |
| 判/分支 | `004C5A40 85 C0 test eax,eax` / `004C5A42 7C 2D jl 0x4C5A71`（零间隔、无 eax 覆写） |
| 失败返 | 失败直落 `004C5A71 5E C2 08 00`（pop esi; ret 8），eax 原样为**负 HRESULT**（被调空参 `00410389 B8 03 40 00 80 mov eax,0x80004003`=`E_POINTER`；流读失败经 `004103A3 7C 31 jl` 外传） |
| 成功返 | `004C5A44 85 F6 test esi,esi` / `004C5A46 74 27 je 0x4C5A6F`；成功路 `004C5A4F E8 6C A7 F4 FF call 0x4101C0`（构造基类子对象）→ `004C5A54 C7 06 A8 87 7E 00` 起装 `007E87A8/007E878C/007E8784/007E877C` 4 表 → `004C5A6F 33 C0` 归一返 0 |
| 方向 | 被调 `0041039E FF 50 0C call [eax+0xC]` = **Read**（`Read(this,pv,4,pcb=NULL)` 形态）；与 `0x410320` 的 `FF 50 10`(**Write**) 方向相反 —— 本行"流读入"标注**正确** |

### ④ 使用见证
- `004C537D C7 06 A8 87 7E 00 mov [esi],0x7E87A8`，宿主 `004C5370`：`push esi; mov esi,ecx` → `004C5373 E8 F8 AD F4 FF call 0x410170`（基类构造）→ 装表 ⇒ 构造器活装表，行外 ✓
- ㉓：行内 `004C5A54` 自重装已排除；`004C52DA`/`004C53BD`/`004C53E4` 未用作 ④ ✓

### ④②不同源 = `no` ✓
### ⑤ 语义：`流读入 → 失败原样返回错误码 / 成功构造基类子对象 + 装 4 表 + 返 0` 逐项相符 ✓ **判 PASS。**

---

## 9. `004C5AC0` — S20 `EMPulseClass::slot8`（标量删除析构）｜ **PASS**（3b2）

### ② 类身份
- 槽 `007E87C8` = `007E87A8`+`0x20`（slot#8），4B 值 = `004C5AC0` ✓；RTTI `. ?AVEMPulseClass@@`（同表）✓；全表枚举 **1/1** ✓

### ③b 形态 = ③b②
| 环节 | 字节（实测） |
|---|---|
| 容器活表 | `[0x8A3870]` = `007E873C`（`. ?AV?$DynamicVectorClass@PAVEMPulseClass@@@@`），装表 `004C522D C7 05 70 38 8A 00 3C 87 7E 00`，随后 `004C5246 E8 3F 45 30 00 call 0x7C978A` 注册 atexit dtor `004C5250`；该 dtor 在 `004C525E` 写死表 `007E875C`(`?$VectorClass@PAVEMPulseClass@@@`) ⇒ 活/死分清 ✓ |
| 站点 | `004C5AF6 8B 15 70 38 8A 00 mov edx,[0x8A3870]` / `004C5B0A FF 52 10 call [edx+0x10]`（`vt[4]`，实测 `[0x7E873C+0x10]=004C5DF0`） |
| 判/分支 | `004C5B0D 83 F8 FF cmp eax,-1` / `004C5B10 74 2D je 0x4C5B3F`（零间隔） |
| 失败返 | 被调 `004C5DF0`：`004C5E0F 83 C8 FF or eax,-1` → `004C5E13 C2 04 00 ret 4` ⇒ **-1** |
| 成功返 | 命中 `004C5E05 74 0B je 0x4C5E12` → `ret 4`（eax=下标） |
| 调用方两路（真不同） | 未命中 → `004C5B3F` 收尾；命中 → `004C5B12`–`004C5B1F` 计数减一 `mov [0x8A3880],ecx` + `004C5B27`–`004C5B3D` 压缩循环（`004C5B31 89 54 81 FC mov [ecx+eax*4-4],edx`、`004C5B3B 3C C1 cmp`、`004C5B3D 7C E8 jl`） |
| 前段（我另核） | `004C5AC4` 起装 4 表（行内）→ `004C5ADF A0 A0 E9 A8 00 mov al,[0xA8E9A0]` / `004C5AE4 84 C0 test al,al` / `004C5AE6 74 05 je` → `004C5AE8 E8 D3 FD FF FF call 0x4C58C0`（格子占用清理，受全局开关控制）→ `004C5AED B2 01 mov dl,1` / `004C5AEF 8B CE mov ecx,esi` / `004C5AF1 E8 DA FD 25 00 call 0x7258D0`（单例解引用） |
| 收尾 | `004C5B41 E8 AA A6 F4 FF call 0x4101F0` / `004C5B46 F6 44 24 0C 01 test byte [esp+0xC],1` / `004C5B4E E8 EA 2F 30 00 call 0x7C8B3D` / `004C5B5A C2 04 00 ret 4` |

### ④ 使用见证
- `004C537D`（ctor `004C5370`，基类 `0x410170`，行外、返 this 由 `004C5383` 起继续初始化）✓；行内 `004C5AC4` 自重装已排除 ✓

### ④②不同源 = `no` ✓
### ⑤ 语义：`4 表复位 / 0xA8E9A0 开关决定格子清理 / 0x7258D0 单例解除 / 容器摘链（计数 0x8A3880、数组 0x8A3874）/ 基类析构 + 按标志释放` —— 逐项相符 ✓ **判 PASS。**

---

## 10. `005F44A0` — S20 `AnimClass::slot84`（非析构：注册注销方法）｜ **PASS**（3b2，附 1 条需账）

### ② 类身份
- 槽 `007E34A4` = `007E3354`+`0x150`（slot#84），4B 值 = `005F44A0` ✓
- RTTI：`COL=007FBA60`(sig=0) → `TD=008182C8` → `. ?AVAnimClass@@` ✓
- **全表枚举（判据 1）**：本 entry 共驻 **21** 张表，**全部** slot#84 同址，类名依次为
  `AircraftClass`(341) `AnimClass`(124) `BuildingLightClass`(122) `BuildingClass`(322) `BulletClass`(125) `FootClass`(341) `InfantryClass`(343) `IsometricTileClass`(122) `MissionClass`(157) `ObjectClass`(122) `OverlayClass`(122) `ParticleClass`(123) `ParticleSystemClass`(122) `RadioClass`(161) `SmudgeClass`(122) `TechnoClass`(309) `TerrainClass`(122) `UnitClass`(344) `VoxelAnimClass`(122) `VeinholeMonsterClass`(122) `WaveClass`(122)
  ⇒ 属**继承共享**（派生类未覆写 slot#84），非跨类误挂；取 `AnimClass` 表与 name 栏同族，合理 ✓

### ③b 形态 = ③b②
| 环节 | 字节（实测） |
|---|---|
| 前置守卫 | `005F44A4 8A 86 83 00 00 00 mov al,[esi+0x83]` / `005F44AA 84 C0 test al,al` / `005F44AC 74 6A je 0x5F4518`（`0x5F44AE+0x6A`） |
| 容器活表 | `[0xA8ECB8]` = `007E4F64`（`. ?AV?$DynamicVectorClass@PAVObjectClass@@@@`，装表 `004E7D5D`，随后 `004E7D76 call 0x7C978A` 注册 atexit dtor `004E7D80`，该 dtor 在 `004E7D88` 写死表 `007E192C`）⇒ 本行取活表 ✓ |
| 站点 | `005F44AE 8B 15 B8 EC A8 00 mov edx,[0xA8ECB8]` / `005F44C2 FF 52 10 call [edx+0x10]`（`vt[4]`，实测 `[0x7E4F64+0x10]=0040CF00`） |
| 判/分支 | `005F44C5 83 F8 FF cmp eax,-1` / `005F44C8 74 2D je 0x5F44F7`（零间隔） |
| 失败返 | 被调 `0040CF00`：`0040CF1F 83 C8 FF or eax,-1` → `0040CF23 C2 04 00 ret 4` ⇒ **-1** |
| 成功返 | 命中 `0040CF15 74 0B je 0x40CF22` → `ret 4`（eax=下标） |
| 调用方两路（真不同） | 未命中 → `005F44F7`；命中 → `005F44CA`–`005F44D7` 计数减一 `mov [0xA8ECC8],ecx` + `005F44DF`–`005F44F5` 压缩循环（`005F44E9 89 54 81 FC mov [ecx+eax*4-4],edx`、`005F44F3 3B C1 cmp`、`005F44F5 7C E8 jl`） |
| 后续 | `005F44FC C6 86 83 00 00 00 00 mov byte [esi+0x83],0`（清标志）/ `005F4503 E8 08 A6 EB FF call 0x4AEB10`（读管理器当前对象，this=`0x87F7E8`，见 `005F44F7 B9 E8 F7 87 00 mov ecx,0x87F7E8`）/ `005F4508 3B C6 cmp eax,esi` / `005F450A 75 0C jne 0x5F4518` / `005F450C 6A 00 push 0` + `005F4513 E8 18 A6 EB FF call 0x4AEB30`（命中则清空） |
| 出口 | `005F4518 5E 59 C3 ret`（无 delete 标志、无 free）⇒ **非析构**，与 name 栏"注册注销方法"一致 ✓ |

### ④ 使用见证
- `0042201C C7 06 54 33 7E 00 mov [esi],0x7E3354`，宿主 ctor `00421EA0`（`00421EAE call 0x5F3900` 基类构造后装表，行外、活表）✓；本 entry 体内无自重装，`005F44A0` 亦非 dtor ⇒ 无 ㉓ 争抢 ✓

### ④②不同源 = `no` ✓
### ⑤ 语义
- 与字节相符的部分：`Find 自身 → 压缩摘链 → 清 [this+0x83] → 管理器当前对象是 this 则置空`，逐项成立 ✓
- **需账（须改字）**：第 4 列写 `DynamicVectorClass<AnimClass*>`（`0xA8ECB8`），实测该全局装的是 **`DynamicVectorClass<ObjectClass*>`**（活表 `007E4F64` 的 RTTI 内联串 `. ?AV?$DynamicVectorClass@PAVObjectClass@@@@`）。地址、计数 `0xA8ECC8`、数组 `0xA8ECBC`、偏移与哨兵全部正确，**唯模板实参写错**（`ObjectClass*` → 写作 `AnimClass*`）。判为语义细节错、非读写方向反转或子型标错，故判 **PASS + 需账**。

---

## 11. `0062D7A0` — S20 `ParticleClass::slot5`（流**读入**构造）｜ **PASS**（3b2）

### ② 类身份
- 槽 `007EF968` = `007EF954`+`0x14`（slot#5），4B 值 = `0062D7A0` ✓；RTTI `. ?AVParticleClass@@`（COL `00807BE8` → TD `008366E8`）✓；全表枚举 **1/1** ✓

### ③b 形态 = ③b②（**本函数自身**返回错误码）
| 环节 | 字节（实测） |
|---|---|
| 站点 | `0062D7AB E8 D0 86 FC FF call 0x5F5E80`（`0x62D7B0+0xFFFC86D0`） |
| 包装层 | `005F5E8B E8 F0 A4 E1 FF call 0x410380`（流读封装；内部 `0041039E FF 50 0C call [eax+0xC]` = **Read**）；其失败路 `005F5E90 85 C0 test eax,eax` / `005F5E92 7C 65 jl 0x5F5EF9` 原样外传负值；成功路尾 `005F5EF7 33 C0` 返 0 |
| 判/分支 | `0062D7B0 85 C0 test eax,eax` / `0062D7B2 7C 4F jl 0x62D803`（`0x62D7B4+0x4F`，零间隔、无 eax 覆写） |
| 失败返 | `0062D803 5E C2 08 00`（pop esi; ret 8），eax 保持负值（空参时 `E_POINTER`=`0x80004003`） |
| 成功返 | `0062D7B4 85 F6 test esi,esi` / `0062D7B6 74 27 je 0x62D7DF`；成功路 `0062D7BF E8 8C 63 FC FF call 0x5F3B50`（构造基类）→ `0062D7C4 C7 06 54 F9 7E 00` 起装 `007EF954/007EF938/007EF930/007EF928` 4 表 → `0062D7EB E8 50 1A 0A 00 call 0x6CF240`（构造 `[esi+0xAC]`）→ `0062D7FC E8 3F 1A 0A 00 call 0x6CF240`（构造 `[esi+0x124]`）→ `0062D801 33 C0` 归一返 0 |
| 方向 | Read=+0xC（与 `0x410320` 的 Write=+0x10 相反）⇒ "流读入"标注正确 ✓ |

### ④ 使用见证
- `0062B767 C7 06 54 F9 7E 00 mov [esi],0x7EF954`，宿主 `0062B5E0`：`sub esp,0x18; push ebx/ebp/esi/edi; mov esi,ecx` → `0062B5E9 E8 12 83 FC FF call 0x5F3900`（基类构造）→ 装 4 表（`0062B767`–`0062B77A`）⇒ 构造器活装表，行外 ✓
- ㉓：行内 `0062D7C4` 自重装已排除；`0062D9A4`（`push ecx; push esi; mov esi,ecx` 后装表 = 析构形态）未用作 ④ ✓

### ④②不同源 = `no` ✓
### ⑤ 语义：`先经 0x5F5E80 从流读入并构造成员 → 失败原样返回错误码 / 成功构造基类 + 装 4 表 + 构造两个成员（+0xAC、+0x124）+ 返 0` 逐项相符 ✓ **判 PASS。**

---

## 12. 五项结论汇总表

| entry | subsystem | ② | ③b 形态 | ④ | 不同源 | ⑤ | 判定 |
|---|---|---|---|---|---|---|---|
| `004839F0` | S06 | `007E4F00`→`.?AVCellClass@@` slot5 | 3b2 `call 0x410380` @`004839FF` | `0047B36F`（ctor `0047B360`） | no | 符 | PASS |
| `00483C10` | S06 | `007E4F04`→同表 slot6 | 3b2 `call 0x410320` @`00483C22` | `0047B36F` | no | 符 | PASS |
| `005F92D0` | S06 | `007ECCAC`→`.?AVIsometricTileTypeClass@@` slot25 | 3b2 `call 0x7514D0` @`005F93B5` | `00544A42`（ctor `00544A00`） | no | 符(2 需账) | PASS |
| `005FC570` | S06 | `007EF4F8`→`.?AVOverlayClass@@` slot73 | 3b2 `call 0x485010` @`005FD1BB` | `005FC38F`（ctor `005FC380`） | no | 符 | PASS |
| `00423AC0` | S20 | `007E33B0`→`.?AVAnimClass@@` slot23 | 3b4 双层循环 @`0042400C`/`0042402A` | `0042201C`（ctor `00421EA0`） | no | 符 | PASS |
| `00428EA0` | S20 | `007E3628`→`.?AVAnimTypeClass@@` slot8 | 3b2 Find(-1) @`00428ED3` | `00427731`（ctor `00427530`） | no | 符 | PASS |
| `004A7C90` | S20 | `007E5FD8`→`.?AVDiskLaserClass@@` slot8 | 3b2 Find(-1) @`004A7CC3` | `004A7A3A`（ctor `004A7A30`） | no | 符 | PASS |
| `004C5A30` | S20 | `007E87BC`→`.?AVEMPulseClass@@` slot5 | 3b2 `call 0x410380` @`004C5A3B` | `004C537D`（ctor `004C5370`） | no | 符 | PASS |
| `004C5AC0` | S20 | `007E87C8`→同表 slot8 | 3b2 Find(-1) @`004C5B0A` | `004C537D` | no | 符 | PASS |
| `005F44A0` | S20 | `007E34A4`→`.?AVAnimClass@@` slot84 | 3b2 Find(-1) @`005F44C2` | `0042201C` | no | 符(1 需账) | PASS |
| `0062D7A0` | S20 | `007EF968`→`.?AVParticleClass@@` slot5 | 3b2 `call 0x5F5E80` @`0062D7AB` | `0062B767`（ctor `0062B5E0`） | no | 符 | PASS |

**11 行 11 PASS / 0 FAIL**；需账 3 条（`005F92D0` 2 条、`005F44A0` 1 条），均不影响四环结论成立。
