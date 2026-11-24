
## 13 · 【COMMON-TECH-3 追加，2026-11-20】镜像读法五条（RTTI 绝对 VA / `TD+8` 内联名 / 引用计数桩与真实释放路 / D-47 待裁 / ㉓ 析构重装）（只追加，上方任何既有行未改）

> **本节是技术条，不是结论条。** 只写「怎么读这个镜像」：每条给可执行判据 + 实测复现摘要，**不写「哪些行成立/不成立」**（那是并表与裁决的活）。复现脚本与原始输出在 `COMMON_TECH3\work\measure*.py` 与同名 `*_out.txt`，逐条对照见 `COMMON_TECH3\RECOMPUTE.txt`。
> 镜像：`ra2youli\gamemd.exe`，4,825,360 B，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`；ImageBase `0x00400000`、SizeOfImage `0x00796000`；段 `.text @0x00401000`、`.rdata @0x007E1000`、`.data @0x00812000`。

### 13.1 RTTI 读法：`pTD` / `pCHD` 是绝对 VA，不是 RVA

**事实**：本镜像 RTTI 的 `pTD` / `pCHD` 字段存的是**绝对虚拟地址**，不是 RVA。若按 `ImageBase + rva` 解析会**越界**，并导致 **fail-closed 误判**（把本可解的行判成「RTTI 读不到」）。

**判据（可执行，三步）**：

1. **先取对 COL 的位置**：`COL = u32(vt − 4)`——`vt[−1]` 存的是 COL 的**指针**，结构体（20 B：`sig / offset / cdOffset / pTD / pCHD`）从 `COL` 处开始。**不得把 `vt − 4` 这四个字节本身当结构体起始**（本卡首轮即踩此坑：在 `0x007E88D0` 上读出 `sig=0x800410` 一类垃圾值）。
2. **再判字段是 VA 还是 RVA**：取到字段值后先判 `值 ≥ ImageBase(0x00400000)`；**成立即已是指针，直接解引用，不得再加 ImageBase**。该判据在本镜像无歧义，因为 `SizeOfImage(0x796000) < ImageBase(0x400000)` ⇒ 任何合法 RVA 恒 `< ImageBase`。
3. **解引用失败不得直接判不可解**：按 `ImageBase + 字段值` 解释时，`pefile.get_data()` 抛 `PEFormatError: "data at RVA can't be fetched. Corrupt header?"` 是**读法错的症状**，不是「本行 RTTI 不可解」的证据。要改按绝对 VA 重解，再决定是否能解。

**实测（本卡复现，4 张表，`measure_out.txt` A 段）**：

| vt | `u32(vt−4)` → COL | `sig`/`off`/`cd` | `pTD` | `pCHD` | `ImageBase + pTD` |
|---|---|---|---|---:|---:|
| `0x007E88D0`（FactoryClass 主表） | `0x00800610` | 0/0/0 | `0x00822290` | `0x00800600` | `0x00C22290` 越界 |
| `0x007F6B30`（WarheadTypeClass 主表） | `0x0080D360` | 0/0/0 | `0x00847C18` | `0x0080D350` | `0x00C47C18` 越界 |
| `0x007F3D98`（工厂 ctor `006C5140` 的表） | `0x0080B108` | 0/0/0 | `0x00841CB8` | `0x0080B0F8` | `0x00C41CB8` 越界 |
| `0x007E1964`（MouseClass 表） | `0x007FAB38` | 0/0/0 | `0x00816C90` | `0x007FAB28` | `0x00C16C90` 越界 |

`pefile.get_data(0x00847C18)` 实跑抛 `PEFormatError`（同表 pTD 按 RVA 解释即失败），按绝对 VA 读则 `.data` 命中、名字逐字节可读（见 §13.2）。

**来源**：两批独立审计，均为实测。`NAMED_PUSH_AUDIT15\SUMMARY.md:62`（「按 `IB+pTD_rva` 解会越界（`pefile` 抛 `PEFormatError`）；后续脚本若沿用旧 `parse_col` 会 fail-closed 误判」）、`NAMED_PUSH_AUDIT15\VERDICT.md:37`/`:177`；`S05-K1\_audit\VERDICT.md:28`（「该镜像 RTTI 用绝对 VA（MSVC6 期），按 RVA 解会全盘失败」）。本卡在 4 张表上独立复现。

### 13.2 RTTI 装饰名在 `TD+8` 是内联串，不是指针

**事实**：本镜像 `TypeDescriptor` 的装饰名位于 `TD+8`，是**内联 NUL 结尾字符串**；按指针读会得到空串。实测 `TD+0 = 0x007F9594`（TD 的 vftable）、`TD+4 = 0`、`TD+8` 起即名字字节。

**判据（可执行）**：读类名前**先验 `TD+8` 起始 4 字节是否为 `2E 3F 41 56`（`.?AV`）或 `2E 3F 41 55`（`.?AU`）**；命中则按**内联串**读到 `0x00` 为止，**不要解引用**。只有不匹配时才考虑「`TD+8` 是 `char*`」的解释——本镜像按指针读必失败：`u32(TD+8) = 0x56413F2E`（即 `".?AV"` 四字节本身），不在任何段内。

**实测（本卡复现，`measure_out.txt` B 段）**：

```
TD 0x00847C18  bytes[+8:+20] = 2e3f41565761726865616454
               u32(TD+8) = 0x56413F2E ; mapped as pointer? False
               inline string = '.?AVWarheadTypeClass@@'
TD 0x00815E18  bytes[+8:+20] = 2e3f4156427566666572494f
               inline string = '.?AVBufferIOFileClass@@'
```

**为什么危险**：`TD+8` 按指针读得到的不是空指针而是**名字首 4 字节**，解引用必失败或落到无关数据；这与 §965 错源⑧ 同一形态（字段偏移读错 ⇒ 静默得空/垃圾名），不会报错。

**来源**：本卡实测；同结论另见 `R14_COMMON.md` §990 行（`COL 0x7FBEF8 +0xC → TD 0x815E18`，名在 `TD+8` 内联读出，`.?AVBufferIOFileClass@@` 逐字节命中）。

### 13.3 `AddRef` / `Release` 桩与「失败清理」的真实路径

**事实（S22_B4 工厂族 11 行实测）**：该批产品类的 `AddRef` / `Release` 是 `mov eax,1; ret 4` **桩**，`Release` **实际不释放**；「失败时 Release 新建对象」的真实路径走的是 **`vt+0x20`（slot8 删除析构器，`push 1`）**，不是 `Release`。

**判据（可执行，三条）**：

1. **见到 `B8 01 00 00 00 C2 04 00`（`mov eax,1; ret 4`）形态的引用计数方法**，按「返回值常量桩」处理：该槽**不改变对象状态**，**不得据此推断对象生命周期、所有权或引用计数**；也不得以「这里调了 `Release`」为由认定对象已销毁。
2. **要判「释放」，必须找 `vt+0x20`（slot8）的调用点**，并核目标函数体内同时具备三件事：重装 vptr、`test byte ptr [esp+X],1`（消费 delete 标志）、`call 0x7C8B3D`（operator delete），且以 `ret 4` 收尾。
3. **语义措辞**：写「`vt+0x20` 删除析构器（flag=1）」，**不写「Release 释放」**。

**实测（本卡复现）**：

```
0x00410300 = b8 01 00 00 00 c2 04 00   (slot1 AddRef 桩)
0x00410310 = b8 01 00 00 00 c2 04 00   (slot2 Release 桩)
全文件扫 imm32：0x00410300 命中 74 次、0x00410310 命中 74 次，全部落在 .rdata（各 74 个槽位）
```

失败路（`TClassFactory<V>::CreateInstance 0x006C5210`）：

```
006C5270  7d09    jge 0x6c527b
006C5272  8b16    mov edx, dword ptr [esi]        ; edx = 新对象 vptr
006C5274  6a01    push 1                          ; delete 标志
006C5276  8bce    mov ecx, esi                    ; this
006C5278  ff5220  call dword ptr [edx + 0x20]     ; vt[8]
```

`vt[8]` 确为删除析构器（表 `0x007E88D0` slot8 = `0x004CA770`）：

```
004CA776  mov [esi], 0x7e88d0          ; 重装 vptr（4 张表 +0/+4/+8/+0xC）
004CA791  call 0x7258d0                ; 解单例
004CA7AA  call dword ptr [edx+0x10]    ; 从 0xA83E30 注册表摘除
004CA86F  test byte ptr [esp+0xc], 1   ; ← 消费 delete 标志
004CA877  call 0x7c8b3d                ; operator delete
004CA883  ret 4
```

**边界（防「族属性」式外推，本卡新增反例）**：桩是 **per-table 属性，不是族属性**。同一 S22 区内：

- 工厂对象**自己**的表 `0x007F3D98` 的 slot1/slot2 = `0x006C51C0` / `0x006C51E0`，二者分别转发 `[0x7E11C8]` / `[0x7E11CC]`（后者失败时 `call 0x7C8B3D` 真释放），**不是桩**；
- 另一子族（M70 / `NAMED_PUSH_AUDIT11`）的 `0x006C2AC0` 是 `mov eax,[esp+4] / add eax,4 / push eax / call [0x7E11C8] / ret 4`，即对 `[this+4]` 调 `InterlockedIncrement` 的**真实 AddRef**。

⇒ 必须**逐表读 slot1/slot2 字节**再判，不得按族的名字套用。

**来源**：`NAMED_PUSH_AUDIT12\SUMMARY.md:36`（`slot2 = 0x00410310` 为 `mov eax,1; ret 4` 桩、Release 不释放）、`:139`（「失败侧 `call [reg+0x20]` + `push 1` 是删除析构器，**不要写成 Release**」）；`_cards\M71-MERGE.md:45`；`COVERAGE\PANEL.md:159`（M71 披露原文，逐字入库）。本卡复现全部字节与两条反例。

### 13.4 待裁项 **D-47**：D-43(A) 与 §12.3 正面冲突（未解）

**冲突本身（照录，不裁谁对）**：

- **D-43(A)**（`R14_COMMON.md` §8.8 条 4）：把 `vt[slot] == entry` 写进了 **④ 使用见证**的定义（活 vtable 槽位形态）。
- **§12.3**：禁止 **②（类身份）与 ④（使用见证）共用同一虚表槽**。
- ⇒ 凡「活 vtable 槽位」形态的 ④，**必然同时满足 D-43(A)、违反 §12.3**。这不是个案。

**实测独立性只到一半**：

- 「表是活的」（`.text` 构造器写点）**独立**——它锚在 `.text`，与 ② 的 `.rdata` 数据链不同段；
- 「entry 占该表第 N 槽」**必须**读 `.rdata` 的 `mem[vt+4N] == entry`，**与 ② 判类用的是同一条数据**；
- 且存在**两对行共用同一条安装指令**，两行间唯一可区分信息只剩槽号（即 ② 的槽）。

**本卡复现（`measure5.py`）**：

```
vt 0x007F6B30 : slot5=0x0075E0C0  slot6=0x0075E2C0
install: 0075D0BA  c74500306b7f00  mov dword ptr [ebp], 0x7f6b30   ← 一条指令装整表
vt 0x007F73B8 : slot5=0x00772CD0  slot6=0x00772EB0
install: 00771E77  c706b8737f00  mov dword ptr [esi], 0x7f73b8     ← 一条指令装整表
```

安装指令写的是**表基址**（不是槽），故两行共享同一 `.text` 站点。

**受影响面（已测，供裁决时估量；数字引自既有成文，本卡未重算翻转行数）**：

| 组 | 行数 | 来源 |
|---|---:|---|
| `S13_B1`（`0075E0C0`/`0075E2C0`/`00772CD0`/`00772EB0`/`004684E0`/`00629FD0`） | **6** | §12.3 逐行清单；`_cards\M74-MERGE.md:49` |
| `NAMED_PUSH_AUDIT2` PASS | **10** | `NAMED_PUSH_AUDIT2\VERDICT.md`；`_cards\M74-MERGE.md:49` |
| M71 所述「④ 严格读法会翻转」 | **≥21** | `COVERAGE\PANEL.md:157`、`:163` |
| **合计** | **≥37** | `_cards\M74-MERGE.md:49`（「撤销将连带翻转 ≥37 行」） |

盘上现状（本卡只读核 `COVERAGE\coverage.tsv`，未改一行）：上述 6 + 10 = **16 行当前 grade 全为 `[已证]`**，`evidence_path` 分别指 `NAMED_PUSH_AUDIT16/VERDICT.md`（6 行）与 `NAMED_PUSH_AUDIT2/VERDICT.md`（10 行）⇒ 「按 D-43(A) 先行」已落盘，不是纸面口径。

**现行处置**：Lead 按 **D-43(A) 先行、§12.3 让位**，并在 `COVERAGE\PANEL.md:160–166` 披露（M74 第四条披露，逐字入库）。**任何一方胜出都必须一次性整批处置，不得零散改判。**

**本卡不做的事**：不判两规则谁对、不改任何行的 grade、不动 `PANEL.md` / `coverage.tsv` / 台账 / `STATUS_BOARD.md`。D-47 若裁，落地形态只能是「一次性整批 + 披露段同步更新」。

### 13.5 ㉓（析构重装陷阱）已实测为真判据

**事实**：㉓（`R14_COMMON.md:504`）定「活 vptr 必须是构造器写的；`push <dtor>; call 0x7C978A`（atexit）注册的函数写入的同类 `mov` 不算活」，并警告成对行必有一行是假。本卡复现两处真触发 + 一处四写点：

- `S07_B1` 两行的表确实被**析构器**也写入（只因 ④ 锚点取在行外构造器而未触雷）；
- `004F45B0` 的表 `0x007E1964` 有 **4 个写点**，其中 2 个属 ㉓ 排除类。

**判据（照卡面成文，可执行）**：**㉓ 不是形式检查。判 ④ 前必须枚举该虚表的全部写点**（全镜像扫该表基址的 imm32，再定位承载它的指令，含行自身函数体内），**并排除两类写点**：(a) `push <fn>; call 0x7C978A`（atexit）注册的全局析构器体内的写；(b) 删除析构器体内的写（特征：`test byte ptr [esp+X],1` + `call 0x7C8B3D` + `ret 4`）。

**实测（本卡复现，`measure_out.txt` E 段 + `measure2_out.txt` E2 + `measure4_out.txt` N）**：

| 行 | 表 | 全部写点（指令地址；立即数地址） | 性质 |
|---|---|---|---|
| `00491210`（ConvertClass） | `0x007E5358` | `0048E93B` / `00490404`（imm `00490406`）/ `00491214`（行自身体内） | 构造器侧 + 析构器侧（`00490400` 无 flag 测试 ⇒ 非删除析构器，但仍是析构器写点）+ 行自身 |
| `006DBD20`（Tactical） | `0x007F4348` | `006D1D54` / `006D1E58` / `006D1E80` / `006DC473`（imm `006DC475`） | 构造器侧 + `006DC470` 删除析构器（该表 slot8，flag 测试 + `call 0x7C8B3D` + `ret 4`） |
| `004F45B0`（MouseClass::slot17） | `0x007E1964` | `0040D1B2` / `0040D295` / `005BDA4A` / `005BE0AD` | `0040D1B2` ∈ atexit 注册的 `0040D1B0`；`0040D295` ∈ 删除析构器 `0040D290`；`005BDA4A` = 构造器 `005BDA40` 侧；`005BE0AD` 本卡未判性质 |

atexit 注册点的字节证据（`0040D190` 体内）：

```
0040D195  call 0x5bda40        ; MouseClass 构造
0040D19A  push 0x40d1b0
0040D19F  call 0x7c978a        ; ← atexit 注册 0x40D1B0
```

**反例方向（可机械排除）**：S22_B4 工厂族 11 行，每行工厂构造器 = `entry − 0xD0`，其 vt 字面量在**全镜像计数恒为 1**（`measure4_out.txt` K2：`006C5140→007F3D98` / `006C52C0→007F3DB0` / … 11/11 = 1），且同型 4 指令工厂构造器在 `[0x006BEE42, 0x006C6042]` 共 49 个、逐个计数全为 1 ⇒ **该族不存在第二个写点，㉓ 可机械排除**。

**边界（防外推，本卡新增）**：不可把「该族表唯一」外推成「所有表唯一」。同镜像 `0x007E88D0`（FactoryClass 主表）计数 = **4**：`004C991C` / `004C9A18` / `004CA2C9` / `004CA778`，其中 `004CA778` 恰在删除析构器 `004CA770` 体内 ⇒ 这张表正是「构造器 + 析构器成对写」形态。**㉓ 必须逐表计数。**

**来源**：`NAMED_PUSH_AUDIT13\SUMMARY.md:44–45,99`（2 行真触发㉓）；`_cards\M72-MERGE.md:42`；`COVERAGE\PANEL.md:161`（M72 ㉓ 正向记录，逐字入库）；`AUDIT_ATEXIT\PROGRESS.md:47–49`（`0x40D1B2` 全局锚定写点唯一、`0x40D1B0` 为销毁例程）。本卡复现写点枚举、两类死表写点字节、以及 49 个工厂构造器的唯一性计数。

## 本轮刷新记录（COMMON-TECH-3，卡号 COMMON-TECH-3，改前 202,159 B / SHA-256 24CC87B84FDC4A59E6416036956EBE5F006A163E6731A2F677800C85DA4083D7）

| # | 改了什么 | 来源 |
|---|---|---|
| 1 | 新 §13.1：RTTI `pTD`/`pCHD` 是**绝对 VA 非 RVA**（三步判据：`COL=u32(vt−4)` 不是 `vt−4` 本身 / 字段 ≥ ImageBase 即按 VA / 解引用失败不等于不可解）+ 4 张表实测（`0x007E88D0`/`0x007F6B30`/`0x007F3D98`/`0x007E1964`，按 RVA 解一律落 `0x00C1~0x00C4` 越界、`pefile` 抛 `PEFormatError`） | `NAMED_PUSH_AUDIT15\SUMMARY.md:62`/`VERDICT.md:37,177`；`S05-K1\_audit\VERDICT.md:28`；本卡实测（`measure_out.txt` A） |
| 2 | 新 §13.2：装饰名在 `TD+8` 是**内联串**（判据：先验 `2E 3F 41 56`/`2E 3F 41 55` = `.?AV`/`.?AU`）+ 两个 TD 逐字节实测（`.?AVWarheadTypeClass@@` / `.?AVBufferIOFileClass@@`；`u32(TD+8)=0x56413F2E` 不是可映射指针）+ 与 §965 错源⑧ 同形态 | 本卡实测（`measure_out.txt` B）；`R14_COMMON.md` §990 行 |
| 3 | 新 §13.3：`AddRef`/`Release` 桩与真实失败清理路（桩字节 `B8 01 00 00 00 C2 04 00` 各被 74 个 `.rdata` 槽引用；失败路 `006C5274 push 1` + `006C5278 call [edx+0x20]` → slot8 `004CA770`，`test byte ptr [esp+0xc],1` + `call 0x7C8B3D` + `ret 4`）+ **两条边界反例**（工厂自身表 `007F3D98` slot1/2 = `006C51C0`/`006C51E0` 非桩；同族 M70 的 `006C2AC0` 是 `InterlockedIncrement` 真 AddRef） | `NAMED_PUSH_AUDIT12\SUMMARY.md:36,139`；`_cards\M71-MERGE.md:45`；`COVERAGE\PANEL.md:159`；本卡实测（`measure{,2,3,4}_out.txt` C/C2/C3/E2/H/I/J/M） |
| 4 | 新 §13.4：待裁项 **D-47** —— D-43(A) 与 §12.3 正面冲突（冲突四条照录、不判谁对；实测独立性只到一半；两对行共用同一条安装指令 `0075D0BA`/`00771E77`；受影响面 6 + 10 + ≥21 = ≥37；盘上核 16 行现状全 `[已证]`；现行处置 D-43(A) 先行 + PANEL 披露；一次性整批处置要求） | `_cards\M74-MERGE.md:41–51`；`COVERAGE\PANEL.md:157,160–166`；`NAMED_PUSH_AUDIT16\VERDICT.md:162`；`R14_COMMON.md` §8.8 条 4 / §12.3；本卡实测（`measure5_out.txt`）+ 只读核 `coverage.tsv` |
| 5 | 新 §13.5：㉓ 已实测为真判据（`00491210` 表 3 写点含 `00490404`、`006DBD20` 表 4 写点含删除析构器 `006DC470`、`004F45B0` 表 `007E1964` 恰 4 写点含 atexit `0040D1B0` 与删除析构器 `0040D290`；atexit 注册点 `0040D19A/19F` 字节；S22_B4 11/11 工厂 vt 全镜像计数 = 1、同型 49 个构造器同结论；**边界：`007E88D0` 计数 4，不可外推**） | `NAMED_PUSH_AUDIT13\SUMMARY.md:44–45,99`；`_cards\M72-MERGE.md:42`；`COVERAGE\PANEL.md:161`；`AUDIT_ATEXIT\PROGRESS.md:47–49`；本卡实测（`measure{,2,4}_out.txt` E/E2/N + `measure2_out.txt` F） |
| — | **改前 202,159 B / SHA-256 24CC87B84FDC4A59E6416036956EBE5F006A163E6731A2F677800C85DA4083D7**；改后字节与 SHA 见 `COMMON_TECH3\HASH.txt` 与本卡完成回报。追加为**纯尾部新增**，旧行 0 变更（**前缀逐字节校验**：新文件前 202,159 字节的 sha256 必须等于改前 sha256，结论见 `HASH.txt`）。 | 本卡实测 |
| — | **卡面措辞精度订正（不改判）**：卡面写「同一虚表也被析构器写入 `00490406` / `006DC475`」，实测这两个数是**立即数地址**，承载它的指令分别在 `0x00490404` / `0x006DC473`；§13.5 两处并列写「指令地址（立即数地址）」。**数字类 0 处冲突**：`004F45B0` 表恰 4 写点、2 个属排除类、S07_B1 两行、四张 RTTI 表、74 个桩槽、11/11 vt 计数 1 全部复核命中。**新增边界 3 条**（`vt−4` 是 COL 指针不是结构体 / 工厂自身表 slot1-2 非桩 / `007E88D0` 计数 4 不可外推），均为本卡实测所得，非推翻卡面。 | 本卡复算 |
| — | 未改：§0–§12 与文末各轮刷新记录既有行；未改 `COVERAGE\coverage.tsv`、`COVERAGE\PANEL.md`、`STATUS_BOARD.md`、台账、`CONFLICTS.tsv`；未 git commit；未建 venv、未 pip install。 | — |
