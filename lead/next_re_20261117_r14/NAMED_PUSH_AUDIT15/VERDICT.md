# NAMED_PUSH_AUDIT15 — 异族独立审计 VERDICT（2 行）

## 身份与工具

- 审计员：异族独立审计员（`agent-220`）。两行均产自执行器 **Hy4**（`NAMED_PUSH_S18_B4` / `NAMED_PUSH_S09_B1`），本审计员不属该家。
- 镜像：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`，本地 SHA-256 **`73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`**（与卡片期望一致）。
- ImageBase `0x400000`；`.text=[0x401000, 0x7E038D)`。实测段表：`.text` VS 0x3DF38D、`.rdata` VA 0x3E1000、`.data` VA 0x412000 / VS 0x367BE4、SizeOfImage 0x796000。
- Python 3.12.10 + capstone **5.0.7**（`skipdata=True`）+ pefile **2024.8.26**，无 venv、未 pip install。
- `delta.tsv` / `REPORT.md` / `EVIDENCE\ROW_*.txt` **只当地址线索**，一处未引用为证据。以下全部字节结论来自本审计员自己的反汇编（`work/auditlib.py`、`work/r1_*.py`、`work/r2_*.py`、`work/final.py`）。

## 取行法

- 行 1：`NAMED_PUSH_S18_B4/delta.tsv` 6 列（`entry subsystem name one_line_semantics grade evidence_path`），第 2 行取 `007B10C0`。
- 行 2：`NAMED_PUSH_S09_B1/delta.tsv` 同 6 列，第 2 行取 `004F45B0`。
- 两文件各只含 1 个数据行（表头不计），与任务给的两个 entry 一致。

## 判据口径（照 `R14_COMMON.md` §8.6 条 3 / §8.8 条 4、5 / 错源 ㉓）

- **③b②**（`R14_COMMON.md:611`）：可证伪的错误码 / 返回约定。**D-46 (A)**（`:749`）：只认错误码/返回约定，**bool 主输出不算**。`MEASURE_F3A\EVIDENCE\CONTROLS.md:28-34` 的操作化：`cmp …,−1` 哨兵驱动分支/setcc，**或字面 −1 返回**。
- **④**（`:594`、§8.8 条 4 D-43(A)）：活 vtable 槽位＝**构造器装的活表 + `vt[slot]==entry` + 写点在行外 + site 不共用**；`atexit`/析构器写的表不算活 vptr（㉓，`:504`）。
- **②**（`:602`）：`[vt-4]=COL → [COL+0xC]=TD → TD+8 内联串`，且 `vt[slot]==entry`。
- **㉓**（`:504`、`:711`）：同表的「派生活表 + 基类死表」会成对出现，`vt[slot]==entry` 在**死表**上也凑得上；**每行必须核该 vt 是否由构造器装入**，且 `(site,slot)` 不得被一活一死两行争抢。

---

## ROW 007B10C0 — `IPXInterfaceClass::slot15`（S18）— **PASS**

### ② 类身份独立成立（主虚表，非小成员表）✓

| 项 | 实测 |
|---|---|
| 虚表基址 | `0x007F794C`（`.rdata`）；`[vt-0x04]` @`0x007F7948` = `0x0080EA60`（COL 指针） |
| 槽号 | slot15 = `vt+0x3C` @`0x007F7988`，内容 `C0 10 7B 00` = **`0x007B10C0`**（= 本 entry）✓ |
| COL | @`0x0080EA60` raw `00 00 00 00\|00 00 00 00\|00 00 00 00\|F8 D8 84 00\|50 EA 80 00`：`sig=0, offset=0, cdOffset=0, pTD=0x0084D8F8, pCHD=0x0080EA50` |
| TD | @`0x0084D8F8` raw `94 95 7F 00\|00 00 00 00\|2E 3F 41 56 49 50 58 49 6E 74 65 72 66 61 63 65 43 6C 61 73 73 40 40`，名串 = **`.?AVIPXInterfaceClass@@`** ✓ |

> 注：本镜像 RTTI 的 `pTD`/`pCHD` 字段存的是**绝对 VA**（非 RVA）：`0x84D8F8-0x400000=0x44D8F8` ∈ `.data`，`0x80EA50-0x400000=0x40EA50` ∈ `.rdata`，两者均在 SizeOfImage 0x796000 内，解引有效。若按 RVA 解会越界（`pefile` 直接抛 `PEFormatError`），故此处判定不采信「RVA 读不到」这种 fail-closed 路径，而是按绝对 VA 读出并逐字节核名。

- **主表判定（② 的关键）**：`COL.offset=0` ✓ ——零偏移即完整对象主虚表。构造器 `0x7B0D90` 在 `0x7B0DA4`（`C7 06 4C 79 7F 00` = `mov dword [esi],0x7F794C`）装到 **`[this+0]`** ✓。整表 24 槽（`+0x00`..`+0x5C`，末槽 `+0x5C`=0），槽值全落在 `0x7B1xxx` 一段，是成建制的类虚表，**不是小成员表**。
- 类层次旁证：CHD 的 BaseClassArray @`0x0080EA40` = `{0x0080EA28, 0x0080EA10}`；两个 BCD 的 `pTypeDescriptor` 分别解出 **`.?AVIPXInterfaceClass@@`**（`0x0084D8F8`）与 **`.?AVWinsockInterfaceClass@@`**（`0x0084D8D0`）⇒ `IPXInterfaceClass : WinsockInterfaceClass`。同一 `TD 0x0084D8F8` 在全镜像只出现在「本 COL 的 pTD 字段 0x80EA6C」与「BCD 0x80EA28」两处，**不存在第二张同 TD 的 COL**；`COL 指针 0x0080EA60` 全镜像只出现 1 次（`0x007F7948`）⇒ 该类只有这一张虚表。
- entry 唯一性：`0x007B10C0` 作为 4 字节指针全镜像**仅 1 处**（`0x007F7988`）⇒ `slot15` 归属唯一，name 栏的类名与槽号与字节一致。

### ③b 具体形态 = ③b②（可伪证错误码 / 返回约定）✓

**被调方是 Winsock 导入（IAT 独立解出，非引用执行器）**：`0x7C899E` = `jmp dword [0x7E157C]`，`[0x7E157C]` = `WSOCK32.dll!socket`；`0x7C8998`→`[0x7E1580]`=`bind`；`0x7C89A4`→`[0x7E1554]`=`setsockopt`；`0x7C897A`→`[0x7E1574]`=`WSAGetLastError`；`0x7C8992`→`[0x7E1584]`=`closesocket`；`0x7C8968`→`[0x7E1548]`=`htons`。

**失败返回什么 / 成功返回什么**：失败 = `INVALID_SOCKET = -1`（`cmp eax,-1` 哨兵）；成功 = 有效 `SOCKET` 句柄（多值，非 {0,1} 布尔）。

**调用方哪条指令拿它分支**（4 处哨兵检查，逐字节核过，cmp→taken 之间**无 eax/标志覆写**）：

| # | call | cmp eax,-1 | 分支指令 | 目标 |
|---|---|---|---|---|
| 1 | `0x7B1147 E8 52 78 01 00` → socket | `0x7B114C 83 F8 FF` | `0x7B1156 75 28` jne | `0x7B1180` |
| 2 | `0x7B126B E8 28 77 01 00` → bind | `0x7B1270 83 F8 FF` | `0x7B1273 75 28` jne | `0x7B129D` |
| 3 | `0x7B12D9 E8 C6 76 01 00` → setsockopt | `0x7B12DE 83 F8 FF` | `0x7B12E1 75 15` jne | `0x7B12F8` |
| 4 | `0x7B132A E8 75 76 01 00` → setsockopt | `0x7B132F 83 F8 FF` | `0x7B1332 75 15` jne | `0x7B1349` |
| 5 | `0x7B137B E8 24 76 01 00` → setsockopt | `0x7B1380 83 F8 FF` | `0x7B1383 75 15` jne | `0x7B139A` |

- 第 1 处 cmp 与 jne 之间插了 `0x7B114F 89 86 6C F0 03 00`（`mov [esi+0x3f06c],eax`，写内存不动 eax/标志）与 `0x7B1155 5F`（`pop edi`，不动 eax/标志）⇒ **不是 eax 覆写陷阱**，flags 存活到 `0x7B1156 jne`。
- **两路动作真不同**（socket / bind 两处）：失败路 `0x7B1158 call WSAGetLastError` → 日志串 → `0x7B1179 32 C0` `xor al,al` → `0x7B117D C2 04 00` `ret 4`；成功路继续拼地址结构（`0x7B1244 lea eax,[esi+0x3f306]; 0x7B124F mov [eax],ecx; 0x7B1251 mov [eax+4],dx`）后进 bind/setsockopt 建链。
- 全函数收尾：`0x7B13BD B0 01` `mov al,1` → `0x7B13C3 C2 04 00` `ret 4`（成功返 1）；各失败路返 `al=0`。
- **非 ③a**：体内 5 处分叉 + 大量构造写，非「单次调用+单次写 / 纯转发桩 / 无分支线性流程」。
- 语义旁证（强）：`0x7B113E/1143/1145` 压 `0x3E8(1000) / 2 / 6` → `socket(6,2,1000)` = **AF_IPX(=6) / SOCK_DGRAM / IPX 协议**，与 `IPXInterfaceClass` 类身份互相印证。
- ⚠ **口径备注（不构成 FAIL，须入账）**：第 3/4/5 处（三个 setsockopt）的两臂只差推入的日志串，随后在 `0x7B1305` / `0x7B1356` 汇合 ⇒ 属「同一 call 仅差参数」的弱臂。③b② 的成立靠第 1、2 处（socket / bind，两路动作实质不同）；第 3~5 处只算数量加成，不算独立支撑。执行器第 4 列的「非同一 call 仅差参数」在**函数级**成立（socket / bind / setsockopt 是三个不同导入），在**三处 setsockopt 内部**不成立。

### ④ 使用见证独立成立 ✓ —— 且 ㉓ 在本行**不存在**

- **构造器**：`0x7B0D90`：`56` push esi → `8B F1` mov esi,ecx → `E8 28 0C 00 00` call `0x7B19C0`（基类 ctor）→ `0x7B0DA4 C7 06 4C 79 7F 00` **`mov dword [esi],0x7F794C`** → 置 `[esi+0x3f2fc]/[+0x3f300]/[+0x3f306]` = `-1` → `0x7B0DCC 8B C6` `mov eax,esi` → `0x7B0DCF C3` `ret`。
  - **判构造器（不是析构器）的四条独立依据**：① 返回 `this`（`mov eax,esi; ret`）；② 装的是**本类自己的主虚表** `0x7F794C`，没有向基类表回退；③ 全函数**无** `call 0x7C8B3D`（operator delete）、**无** `test byte [esp+8],1` 删除标志；④ 字段是**置初值**（`-1`）而非释放。
- **活对象链**（`new` + ctor）：5 处 `push 0x3F310`(=对象尺寸 259,344) → `call 0x7C8E17`(operator new，实测 `6A 01 | FF 74 24 08 | E8 20 06 00 00 | 59 | 59 | C3`) → `cmp eax,ebx` → `mov ecx,eax` → `call 0x7B0D90`：
  `0x52E3E3/0x52E3F1`、`0x540918/0x540926`、`0x560525/0x560533`、`0x685B13/0x685B21`、`0x68617B/0x686189`。⇒ 堆上活对象，表是真活的。
- **写点在行外**：`0x7B0DA4` 不在本 entry 体 `[0x7B10C0, 0x7B13C3]` 内 ✓。
- **㉓ 专项：本行无成对陷阱。** 全镜像对 `0x7F794C` 的 imm32 写点**恰好 1 处**，即 `0x7B0DA4`（`find_u32_va` 命中 `0x7B0DA6`＝该指令 imm 字段偏移，同一条 `C7 06 4C 79 7F 00`）。**没有任何析构器写这张表**（该类的 deleting dtor 写的是基类 `WinsockInterfaceClass` 的表，属 ㉓ 所述正常回退），故不存在「活表+死表成对争抢」。
- **direct-only 排除**：`find_rel_calls(0x007B10C0)` = **0**，全镜像无 `call/jmp` 直达本 entry ⇒ ④ 不可能建立在 direct call 上，只能来自活虚表安装，符合「direct-only 不足」的排除意图。
- 旁证（不用于判 ④，仅记）：`call/jmp dword ptr [rX+0x3C]` 全 `.text` 实测 **119** 处（与控制台声明数字一致，首例 `0x0040A6FD FF 52 3C`、`0x00411FD5 FF 56 3C`）——但无法把任一站点逐点归属到 `IPXInterfaceClass` 对象，因此**不以它当 ④ 依据**。

### ④ 与 ② 不同源 ⇒ `same_source = no` ✓

② 用 `.rdata` 的槽 `0x007F7988` + COL `0x0080EA60` + TD `0x0084D8F8`；④ 用 `.text` 的构造函数写点 `0x007B0DA4` + `new` 链 `0x7C8E17`。地址、节、证据物件全不同，非同一槽既证身份又证使用。

### ⑤ 语义与实测相符 ✓

第 4 列的形态（③b②、Winsock `cmp eax,-1`→`jne`、失败 `WSAGetLastError`+`xor al,al`+`ret`、成功继续 `bind/setsockopt` 建链）、② 地址（`007F794C` / `+0x3C` / `007F7988`）、④ 地址（`007B0DA4`，宿主 `007B0D90`）、`dispatch sites=119`、以及「主虚表非小成员表」**逐项与实测一致**；读写方向无涉（无流 I/O），子型标注正确。仅第 3~5 处 setsockopt 的臂差异被写得强于实测（见 ③b 口径备注）。

---

## ROW 004F45B0 — `MouseClass::slot17`（S09）— **PASS**（附 5 条入账备注）

> ⚠ 本行 delta 的 `one_line_semantics` **完全没给 ② 和 ④ 的地址**（只给了 ③b 的站点与被调方返回字节）。按卡面「②…给地址」「④ 使用见证独立成立」，以下 ②/④ 由本审计员独立取证并给地址；这不是「沿用执行器」，而是补证。

### ② 类身份独立成立（主虚表，非小成员表 / 非副表）✓

| 项 | 实测 |
|---|---|
| 虚表基址 | `0x007E1964`；`[vt-0x04]` @`0x007E1960` = `0x007FAB38`（COL 指针） |
| 槽号 | slot17 = `vt+0x44` @`0x007E19A8`，内容 `B0 45 4F 00` = **`0x004F45B0`**（= 本 entry）✓ |
| COL | @`0x007FAB38` raw `00 00 00 00\|00 00 00 00\|00 00 00 00\|90 6C 81 00\|28 AB 7F 00`：`sig=0, offset=0, cdOffset=0, pTD=0x00816C90, pCHD=0x007FAB28` |
| TD | @`0x00816C90` 名串 = **`.?AVMouseClass@@`** ✓ |

- **主表判定**：`COL.offset=0` ✓；该表由真构造器装到 `[this+0]`（见 ④）✓。
- **同时排掉「副表（基类子对象表）」**：MouseClass 还有一张 `0x007E195C`，其 COL @`0x007FA9B8` 为 `sig=0, **offset=0x5518**, cdOffset=0`，TD 同为 `.?AVMouseClass@@`；它的 slot17 = `0x004F4480`（**不是**本 entry）。本行取的是 `offset=0` 的 `0x7E1964`，**不是**副表 ⇒ 与上一批 `006BFF90/006C0A10`（内嵌成员表误当主虚表）那类错误不同。
- **entry 是共享槽（须入账）**：`0x004F45B0` 作为指针全镜像出现 **9 处**，全部是 slot17，分别属 `MouseClass 0x7E1964`、`DisplayClass 0x7E6114`、`GScreenClass 0x7EA6FC`、`MapClass 0x7ED404`、`TabClass 0x7EDFB4`、`PowerClass 0x7EFF54`、`RadarClass 0x7F0344`、`ScrollClass 0x7F1094`、`SidebarClass 0x7F3058`（9 张表 COL.offset 全为 0）。⇒ 「MouseClass::slot17」是**该 entry 的 9 个成立命名之一**，字节上成立，但它不是 MouseClass 独有实现（是族内共享/继承槽）。按 §8.7 判据 1（必须枚举全部持有表）已枚举；判据 2（② 栏类名须与 name 栏一致）本就无从核，因为 delta 没写 ②。
- 旁证：MouseClass 的基类析构器 `0x652C00` 在 `0x652C0C` 把 `[edi]` 回退成 `0x007F0344`（= RadarClass 主表）⇒ `MouseClass : RadarClass`，故 RadarClass::slot17 与本行同函数，属继承未覆写，与 9 表共享一致。

### ③b 具体形态 = ③b②（可伪证错误码 / 返回约定）✓（附口径强度备注）

**站点与被调方，逐字节核过（与 delta 所写完全一致）**：

- 站点 1：`0x4F45EA E8 B1 ED FA FF` = `call 0x4A33A0`（`ecx=[0x8A0E08]`，push 0）→ `0x4F45EF 85 C0` `test eax,eax` → `0x4F45F1 0F 85 4C 01 00 00` `jne 0x4F4743`。call→test 相邻，**零 eax 覆写**。
- 站点 2：`0x4F4602 E8 99 ED FA FF` = `call 0x4A33A0`（`ecx=[0x8A0E0C]`）→ `0x4F4607 85 C0` → `0x4F4609 0F 85 34 01 00 00` `jne 0x4F4743`。同上，零覆写。

**被调 `0x4A33A0` 的返回约定（实测五条返回路径）**：

| 返回值 | 字节 | 语义 |
|---|---|---|
| `-1` | `0x4A33BC 83 C8 FF` `or eax,-1` → `0x4A33C6 C2 04 00` | `[this+0x70]==0` 失败 |
| `1` | `0x4A3465 B8 01 00 00 00` `mov eax,1` → `0x4A3471 C2 04 00` | 内层 `call [eax+0x64]` 返回非 0 |
| `2` | `0x4A3581 F7 D8` `neg eax` / `0x4A3585 1B C0` `sbb eax,eax` / `0x4A3588 83 E0 02` `and eax,2` → `0x4A3592 C2 04 00` | 公共尾 `call [ecx+0x80]` 返回非 0 |
| `0` | 同上三点 | 公共尾 `call [ecx+0x80]` 返回 0 |
| 透传 | `0x4A3434 C2 04 00` | `[this]==2` 分支，eax = `call [eax+0x14]` 的返回值，**不保证是 0** |

⇒ 返回域 **{-1, 1, 2, 0}** 加一条透传，**不是 {0,1} 布尔**；含**字面 −1 返回**（`0x4A33BC`），命中 `MEASURE_F3A\EVIDENCE\CONTROLS.md` 的「字面 −1 返回」档。

**两路动作是否真不同**：`jne` 落点 `0x4F4743`（`A1 F8 0D 8A 00` mov eax,[0x8A0DF8] → `FF 51 2C` call [ecx+0x2c]）后接收尾 `0x4F474E`；fall-through `0x4F45F7` 起再做第二次取源校验（`0x4F4602` 第二站点）并执行 `0x4F462A`..`0x4F473E` 大段构造：`call 0x4A35A0`×2、`call 0x4A35F0`×4、`call 0x4A3840`×2、`call 0x4A3660`（写颜色/显示状态）。**差异实质存在**（失败臂整段跳过约 0x340 字节的工作体）。

**非 ③a**：体内多处分叉 + 大量构造写，非「单次调用+单次写 / 纯转发 / 无分支线性」。

⚠ **两条口径强度备注（不构成 FAIL，但须入账，供 Lead 定政策）**：

1. **消费侧是布尔坍缩**：`test eax,eax` + `jne` 只判「零 / 非零」，把 `-1/1/2` 三种失败**坍缩成同一臂**。若后续把 ③b② 收紧到「必须 `cmp eax,-1` 级哨兵比较」，本行将落回「字面 −1 返回」单腿站立。本行成立依赖 `CONTROLS.md` 的第二档（字面 −1 返回），不是第一档（`cmp …,−1` 驱动分支）。对照：同批 `007B10C0` 用的是第一档（`83 F8 FF`+`jne`），两行强度不同档。
2. **`jne` 目标是成功路的汇合点**：`0x4F473E call 0x4A3660` 之后顺序执行即 `0x4F4743`，与 `jne` 目标**同一地址**。即失败路与「成功走完」共用收尾段。这与上一批被判死的 `007276A0`（`je` 目标为两路径公共续点、唯一差异仅 `sprintf("%d")`）**形态同类**，区别在于本行两臂差异是整段工作体（约 0x340 B、7 次调用）而非单条参数差异 ⇒ 本审计判「两路动作真不同」成立，但**披露该形态同类性**。

### ④ 使用见证独立成立 ✓ —— 但本行 **㉓ 成对陷阱真实存在**

`0x007E1964` 全镜像 imm32 写点 **4 处**，逐处定性：

| # | 写点 | 宿主函数 | 定性 |
|---|---|---|---|
| 1 | `0x40D1B2` `C7 05 E8 F7 87 00 64 19 7E 00` | `0x40D1B0` | **atexit 全局析构器（死表写点）** |
| 2 | `0x40D295` `C7 03 64 19 7E 00` | `0x40D290` | **标量删除析构器（死表写点）** |
| 3 | `0x5BDA4A` `C7 06 64 19 7E 00` | `0x5BDA40` | **真构造器（活表写点）← 本行 ④ 用此** |
| 4 | `0x5BE0AE` `C7 45 00 64 19 7E 00` | 流 Load 函数体内（先 `call [ecx+0xC]` 再装） | 构造侧（placement），非析构 |

**定性依据（逐字节）**：

- 写点 1 宿主 `0x40D1B0`：装配点 `0x40D190 B9 E8 F7 87 00`(`mov ecx,0x87F7E8`) → `0x40D195 E8 A6 08 1B 00`(`call 0x5BDA40` 构造器) → **`0x40D19A 68 B0 D1 40 00` + `0x40D19F E8 E6 C5 3B 00`(`push 0x40D1B0; call 0x7C978A` = atexit)** → `ret`。`0x7C978A` 的 atexit 身份本审计独立核过（未照抄语料）：`FF 74 24 04 | E8 79 FF FF FF`(call `0x7C970C`)`| F7 D8 | 1B C0 | 59 | F7 D8 | 48 | C3` —— 成功返 0、失败返 −1 的 `_onexit` 语义；紧邻的 `0x7C979C` 分配 **0x80(128) 项**函数表并存入 `0xB78BC0`/`0xB78BBC`，即 atexit 表初始化。而 `0x40D1B0` 本体：`mov [0x87F7E8],0x7E1964` + `mov [0x884D00],0x7E195C`（**MI 析构器的 vptr 前奏**）→ 循环 4 次销毁子对象（`call 0x40AFD0` / `call 0x40D300`）→ `0x40D1F2 mov ecx,0x87F7E8` + `0x40D1F7 call 0x652C00`（基类析构器）→ `ret`（无返回值、无 free）⇒ **全局非删除析构器**，正是 ㉓ 定义的「死表」。
- 写点 2 宿主 `0x40D290`：装两张自身的表后同样循环 4 次销毁子对象 → `0x40D2D4 call 0x652C00`（基类析构器）→ **`0x40D2D9 F6 44 24 10 01`(`test byte [esp+0x10],1`)** → **`0x40D2E1 E8 57 B8 3B 00`(`call 0x7C8B3D` operator delete)** → `ret 4` ⇒ **标量删除析构器**。
- 写点 3 宿主 `0x5BDA40`：`push esi` → `mov esi,ecx` → `0x5BDA43 E8 48 48 0D 00`(`call 0x692290` 基类 ctor) → `0x5BDA4A mov [esi],0x7E1964` → `0x5BDA68 mov [esi+0x5518],0x7E195C` → 清零 `[esi+0x555c..0x5568]` → **`0x5BDA72 8B C6` `mov eax,esi`** → `0x5BDA75 C3` `ret` ⇒ **真构造器**（返 this、置初值、无 delete、无基类表回退）。唯一调用点 `0x40D195`，`ecx=0x87F7E8`（全局 MouseClass 实例；该全局在全镜像被引用 **3700** 次 ⇒ 是真活对象）。
- **写点在行外**：`0x5BDA4A` 不在 `[0x4F45B0, 0x4F4773]` 内 ✓。

⇒ **④ = `0x5BDA4A`（构造器活表安装）成立**；同时**明确剔除** `0x40D1B2`（atexit 析构器）与 `0x40D295`（scalar deleting dtor）—— 若 ④ 取这两处任一处，即按 ㉓ 判 FAIL。

- **direct-only 排除**：`find_rel_calls(0x004F45B0)` = **0**，全镜像无 `call/jmp` 直达本 entry。
- **同源争抢(§8.8 ㉓ 后半条)**：`(site,slot)` = `(0x5BDA4A, +0x44)` 仅本行使用，未被另一行争抢 ✓。

### ④ 与 ② 不同源 ⇒ `same_source = no` ✓

② 用 `.rdata` 槽 `0x007E19A8` + COL `0x007FAB38` + TD `0x00816C90`；④ 用 `.text` 构造器写点 `0x005BDA4A` + 全局实例链 `0x40D190→0x40D195`。不同地址、不同节、不同证据物件。

### ⑤ 语义与实测相符 ✓（附 1 处引证错误）

- 「鼠标显示准备」方向与形态相符：`0x4A33A0` 走 `[this+0x70]` 所指对象，按 `[this]` 类型（0/1/2）分派 `call [eax+0x14]`（当 `[this]==2`）、`call [eax+0x64]`（否则）、公共尾 `call [ecx+0x80]`，并有 `rep movsd/rep movsb` 行拷贝；本 entry 随后 `call 0x4A35A0`(置色 `/or eax,0xffffff00` 等)、`call 0x4A35F0`(索引色)、`call 0x4A3840`、`call 0x4A3660` 写显示状态。**无读写方向反转**，子型 ③b② 标注正确。
- ⚠ **引证错误（不判 FAIL，须入账）**：delta 写「以及成功路 `0x4A3434 ret` ⇒ 失败返多值非 0 码 {-1,1,2}、**成功返 0**」。实测 `0x4A3434` 是 `[this]==2` 分支的出口，`eax` 是 `call [eax+0x14]` 的**透传返回值**，**不保证为 0**；真正「成功返 0」的字节在 `0x4A3581..0x4A3592`（`neg/sbb/and eax,2` 三点，内层调用返 0 时得 0）。⇒ 「失败 {-1,1,2} / 成功 0」的结论本身成立，但所引地址张冠李戴。

---

## 逐行判定汇总

| entry | subsystem | ② 主虚表 | ③b 形态 | ④ 独立成立 | ④≠② | ㉓ | ⑤ | verdict |
|---|---|---|---|---|---|---|---|---|
| `007B10C0` | S18 | ✓ `0x7F794C` slot15→`0x7F7988` | 3b2 ✓（`83 F8 FF`+`jne`） | ✓ ctor `0x7B0DA4` | no ✓ | 不适用（全镜像仅 1 写点） | ✓ | **PASS** |
| `004F45B0` | S09 | ✓ `0x7E1964` slot17→`0x7E19A8` | 3b2 ✓（`test`+`jne`，被调 4 值域） | ✓ ctor `0x5BDA4A` | no ✓ | **真陷阱存在**，已避开 `0x40D1B2`/`0x40D295` | ✓（1 处引证错） | **PASS** |

## 须入账备注（不改变 PASS/FAIL）

1. `007B10C0`：第 3~5 处 setsockopt 的两臂只差日志串后汇合，属弱臂；③b② 由第 1、2 处（socket/bind）实质支撑。
2. `007B10C0`：本镜像 RTTI 的 `pTD`/`pCHD` 存**绝对 VA**，按 RVA 解会越界——后续脚本若走 `IB+pTD_rva` 会 fail-closed 误判。
3. `004F45B0`：delta **未给 ②/④ 地址**；②/④ 由本审计独立补证（`0x7E19A8`、`0x5BDA4A`）。
4. `004F45B0`：`0x7E1964` 的 4 写点中 **2 处是析构器**（`0x40D1B2` atexit / `0x40D295` deleting）；④ 若取错即 FAIL。
5. `004F45B0`：③b② 消费侧 `test eax,eax` 是布尔坍缩；`jne` 目标 `0x4F4743` 同时是成功路汇合点（与 `007276A0` 形态同类，差异量级更大）。
6. `004F45B0`：delta 把 `0x4A3434` 当「成功返 0」依据不实；真值在 `0x4A3592`。
7. `004F45B0`：该 entry 位于 **9 张表**的 slot17，`MouseClass::slot17` 只是成立命名之一。
