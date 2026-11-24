# S12-Q2 · 取格路径（BuildingClass*/TechnoClass* → CellClass*）静态复核

> 卡号 S12-Q2｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（只读，未改）｜ImageBase `0x400000`
> 工具：Python 3.12 + capstone 5.0.7 (`skipdata=True`) + pefile；双通道 = A(capstone 线性解码) / B(裸字节 E8 rel32 扫描 + RTTI 原始解析)，两通道均不依赖 `function_atlas.tsv entry+size`。
> 分级：`[已证]`=双通道/独立复现闭合；`[静态推断]`=静态强证据未真机验；`[未证]`=无可判定样本。

## 0 · 先把 `obj+0x520` 说清（复核 W177 真机结论）

**结论：`obj+0x520` = `BuildingTypeClass*`（建筑类型对象指针），不是 `MapClass*`。W177 真机结论成立，静态证据独立闭合。** `[已证]`

| 证据类型 | 内容 | 证据路径 |
|---|---|---|
| ① RTTI（类名只认 TypeDescriptor） | 裸字节解析：vtable `0x7E4570` → `vtable[-1]`COL `0x7FC618` → TD `0x8193A8` → name `.?AVBuildingTypeClass@@`。§678 记录的"类型对象虚表 `0x7E4570`"由此 RTTI 定名 | `EVIDENCE\rtti_check.txt`、`work\rtti_check.py` |
| ② 写点 | `0x43B756 mov [esi+0x520],ecx`（BuildingClass 构造区，`esi=this`，`ecx=[esp+0x14]` 参数）；全镜像 +0x520 写点 **13 处**（含 `-1` 哨兵写），与台账 §673/§675 一致 | `EVIDENCE\w520_43B756.txt`、`q1_520_writes.txt`、`two_channel_verify.txt` |
| ③ 读者/类布局归属 | `0x459EE0`（BuildingClass 虚槽 0x88）`mov eax,[ecx+0x520]; ret` = **get type**；`0x459ED0`（槽 0x90）`mov eax,[ecx+0x520]; mov eax,[eax+0x60]; ret`。挂链包装 `0x5683C0` 内 `call [vptr+0x88]` 返回的正是该指针（随后读 `[eax+0x235]`）——与 §673/§678 一致 | `EVIDENCE\slot88_getter_459EE0.txt`、`slot90_getter_459ED0.txt`、`T2_callee_5683C0_head.txt`(W176) |
| ④ 真机一一对应 | 16 个互异指针 ↔ 15 个类型名（`+0x24` 为 ID 串 YAPOWR/YACNST/CAAIRP…），严格双射；`MapClass` 单例（`0x87F7E8`，YRpp `MapClass.h:143 Instance`）若成立则全对象共享同一指针 ⇒ 已否证 | 台账 §949 §三；`W177_live_place\_audit\VERDICT.md` §1-#6/§4 |

**⇒ 正面处理真机证据**：静态与真机同向，不推翻也不修正真机结论。`PROBE_TABLE.md` L7 把 `cell` 建在 `obj+0x520` 上是**假设错误**（卡面已标猜测），取格路径须另走下述两条。**未发现 `obj+0x520` 是别的东西的任何静态迹象**：13 写点中 5 处是 `mov [reg+0x520],0xFFFFFFFF` 无效哨兵、2 处在 BuildingClass 构造/析构区（0x43B756/0x43C022）、其余 6 处落在其它 Techno 族的 `+0x520` 同偏移（0x44EA5A/0x4DC823/0x6679AE/0x710EC7/0x7594C3/0x759EC3，抽样 0x44EA5A/0x4DC823 见 `EVIDENCE\other_520_writes.txt`）——**无任何一处呈现 MapClass 单例分配特征**（MapClass 单例 0x87F7E8 的 vptr 分配在 0x40D1B2，与 +0x520 写点无交集）。这些同偏移写点正是纪律 16「偏移不能定语义」的体现，不改变 BuildingClass 的 TypeClass 结论。

## 1 · 建筑自身存的格坐标候选偏移（全列）

| 偏移 | 宽度 | 语义/类型 | 写者站点 | 读者站点 | 坐标 or 指针 |
|---|---|---|---|---|---|
| **`+0x9C`** | 4 (int32) | `ObjectClass::Location.X`（lepton，256/cell） | `0x5F6940 mov [ecx],edx`（`SetLocation`，槽 +0x1B4） | `0x41BEA0`(槽 +0x1B8 `GetMapCoords`)、`0x4544A0`、`0x453D60`、`0x4544D7` | **坐标（lepton）**，被 `sar 8` 输入，非基址 |
| **`+0xA0`** | 4 (int32) | `Location.Y`（lepton） | `0x5F694C mov [ecx+4],edx` | 同上（`[ecx+4]`/`[esi+4]`） | **坐标（lepton）**，`shl 9` 前先 `sar 8` |
| **`+0xA4`** | 4 (int32) | `Location.Z`（lepton，高度） | `0x5F6954 mov [ecx+8],eax` | `0x5657A0` 变体/`0x5F6983`（高度查询） | 坐标 Z，不参与 2D 格索引 |
| `+0xE4`/`+0xE8` | 4+4 | **CellClass 的**双链表头，**非对象字段** | `0x47E8A0`/`0x47EA90` 写 `[ebx+0xE4/E8]`（`ebx`=CellClass*） | 同二函数读 | **指针**（链表头） |
| `+0x30` | 4 | 格链元素 next（在 ObjectClass 作链节点时） | `0x47E8EB/0x47E908 mov [esi+0x30],…` | `0x47E8DB/E4`、`0x47EAC1/CC` | **指针**（next） |
| `+0x520` | 4 | BuildingTypeClass*（见 §0） | `0x43B756` 等 13 处 | `0x459EE0`、`0x43F1E9`、`0x5683C0` | **指针，但指类型，非格** |

**格坐标候选偏移数 = 3（+0x9C / +0xA0 / +0xA4，CoordStruct 三分量）；其中 2D 取格用 2 个（X/Y）。**
证据：`EVIDENCE\find_mapcoords.txt`（`0x41BEA1`/`0x4544D1`/`0x453D60` 等逐条）、`again_slots.txt`（`0x5F6940` 写者全函数）。
`CellClass.MapCoords` 自身为 `+0x24`(short X)/`+0x26`(short Y)（`docs/re/cellclass_offsets_evidence.md` §二，可作为格对象自检，不是对象侧字段）。

## 2 · 路径 A（最稳）：坐标 → MapClass 单例 → 格数组直索引 `[已证]`

**MapClass 单例** = `0x87F7E8`（YRpp `MapClass.h:143 Instance`；`mov ecx,0x87F7E8` 在 1439 个 GetCellAt 调用点前出现，双通道一致）。
**格数组基址** = `[[0x87F7E8 + 0x13C]]` = **`dword[0x87F924]`**（绝对寻址被引用 **399** 处；`0x87F7E8+0x13C=0x87F924`）。
**索引公式**（`0x5657A0` 裸反汇编逐条）：`idx = (Y<<9) + X = Y*512 + X`；`stride = 4`；数组元素 = `CellClass*`。
**越界/空槽**：`idx<0 || idx>=0x40000 || [base+idx*4]==0` → 返回 `InvalidCell = 0xABDC50`，并 `mov [0xABDC74], packed{X,Y}`。

```
obj(BuildingClass*/TechnoClass*)
  ├ Location.X = i32[obj+0x9C] ; cellX = (X + ((X>>31)&0xFF)) >> 8
  ├ Location.Y = i32[obj+0xA0] ; cellY = (Y + ((Y>>31)&0xFF)) >> 8
  ├ idx = (cellY << 9) + cellX
  ├ cellArray = dword[0x87F924]
  └ CellClass* = dword[cellArray + idx*4]        ; guard idx∈[0,0x40000), !=0 else 0xABDC50
```

**关键函数地址**：`MapClass::GetCellAt/TryGetCellAt = 0x5657A0`（atlas size 56，区间 [0x5657A0,0x5657D8)，1439 调用点双通道一致）；
`ObjectClass::GetMapCoords(CellStruct* out) = 0x41BEA0`（槽 +0x1B8，atlas size 61）；`SetLocation = 0x5F6940`（槽 +0x1B4）。
证据：`EVIDENCE\getcell_5657A0.txt`、`getcell_slots_disasm.txt`、`find_mapcoords.txt`、`again_slots.txt`。
**纯只读**：上面全部是 `ReadProcessMemory` 读整数 + 本地算术，不调用游戏函数、不写内存。

## 3 · 路径 B（引擎权威结果）：对象虚表 GetMapCoords → GetCellAt，EIP 上下文捕获 `[已证]`

第 1 跳：`obj->vtable[+0x1B8]` = `0x41BEA0`，读 `Location(+0x9C/+0xA0)` 写 `CellStruct{X,Y}` 到出参并返回该出参指针（`ret 4`，返回 `eax=out`）。实机静态调用例：`0x43F1AE`（BuildingClass slot73 内 `call [eax+0x1b8]` → `mov edx,[eax]` 取 packed 坐标）。
第 2 跳：`MapClass::GetCellAt(0x5657A0)`，`ecx=0x87F7E8`（thiscall 的 ecx 来源已逐点回溯，全部为立即数 `mov ecx,0x87f7e8`），入参 = `&CellStruct`，返回 `eax=CellClass*`。

**只读探针用法（EIP 上下文采样）**：在 `EIP==0x5657D5`（GetCellAt 的 `ret 4` 前汇聚点）采 `eax` 即引擎算出的 `CellClass*`；或 `EIP==0x41BEDA`（GetMapCoords 返回前）读出参指针 `[esp+…]` 再读 `CellStruct`。放置期必经调用点（BuildingClass slot73 `0x43F180` 内）：`0x43F210 / 0x43F2A7 / 0x43F2C5 / 0x43F2EF / 0x43F39C / 0x43F3BF`（W176 `T1_disasm_0043F180.txt` 逐行核对）。
关键函数地址：**0x41BEA0**（GetMapCoords）→ **0x5657A0**（GetCellAt）；与路径 A 共用，但**获取方式不同**（A=纯内存重算，B=引擎调用点捕获），故为两条独立可用路径。
证据：`EVIDENCE\getcell_slots_disasm.txt`、`find_getcell_impl.txt`、`two_channel_verify.txt`。

### 3.1 多格建筑 foundation 偏移（路径 B 的引擎内扩展）`[静态推断]`
挂链包装 `0x5683C0`：槽 `+0x88` 得 Type（+0x520）→ 读 `[type+0x235]`；槽 `+0x78`（WhatAmI）==2；槽 `+0x108` 取 foundation CellStruct 数组；逐项 `X+=base.X, Y+=base.Y`（`0x568446..0x568468`），`idx=Y*512+X`，`[ebx+0x13C]` 取格，`call 0x47E8A0` 挂链。=> 单格建筑路径 A 足够；多格格表须叠加 foundation 偏移。证据 `T2_callee_5683C0_head.txt`、`getcell_5657A0.txt`。

## 4 · CellClass 链复核（当前 atlas 真实函数区间）

用 atlas 区间包含（非 entry_at_or_before）归属：
- `0x47E8A0` size 489 → `[0x47E8A0,0x47EA8D)` = 挂链；读 `[ebx+0xE8]`/`[ebx+0xE4]`（`ebx`=cell），`[esi+0x30]` next，写 `[ebx+0xE8/E4]=新元素`、`[新元素+0x30]=旧头`。
- `0x47EA90` size 263 → `[0x47EA90,0x47EB97)` = 摘链；改 `[edi+0xE8/E4]` 与 `[esi+0x30]`，尾结点写 `[esi+0x30]=0`。
- => 链头 `cell+0xE4`/`cell+0xE8`、元素 `next=+0x30` 复核成立；与 R14_COMMON §2.2 一致。证据 `EVIDENCE\cellchain_47E8A0.txt`、`cellchain_47EA90.txt`。

## 5 · 真机探针配方（只读）

| 项 | 地址/公式 | 读宽度 | 分级 | 说明 |
|---|---|---|---|---|
| MapClass 单例 | `0x87F7E8`（对象；vptr 写点 `0x40D1B2`） | 4 | `[已证]` |YRpp `Instance`；thiscall ecx 来源 |
| 格数组基址（绝对，可直接读） | `dword[0x87F924]` = `[[0x87F7E8+0x13C]]` | 4 | `[已证]` | 399 处绝对引用；省去先读单例 |
| 索引公式 / stride | `idx=(Y<<9)+X`；`stride=4`；`CellClass*=dword[base+idx*4]` | 4 | `[已证]` | `0x5657A0` 逐条反汇编 |
| 格坐标来源（对象侧） | `cellX = (i32[obj+0x9C]+((i32[obj+0x9C]>>31)&0xFF))>>8`；Y 同（+0xA0） | 4 | `[已证]` | `0x41BEA0`/`0x4544D1`；多格见 §3.1 |
| CellClass 坐标自检 | `short[cell+0x24]=X`、`short[cell+0x26]=Y` | 2 | `[静态推断]` | `docs/re/cellclass_offsets_evidence.md` §二（带勘误，取格前自检用） |
| 格内链表头 A | `dword[cell+0xE4]` | 4 | `[已证]` | `0x47E8A0`/`0x47EA90` |
| 格内链表头 B | `dword[cell+0xE8]` | 4 | `[已证]` | 同上 |
| 链表元素 next | `dword[elem+0x30]`（elem 初值 = 上述链表头；0=尾） | 4 | `[已证]` | 同上；遍历时抓全部占用对象 |
| InvalidCell 哨兵 | `0xABDC50`（越界/空槽返回；`[0xABDC74]`=查询坐标） | 4 | `[已证]` | `0x5657C8` 分支 |
| 引擎取格调用点（EIP 采样） | `EIP==0x5657D5` → `eax`=CellClass*；`EIP==0x41BEDA` → 出参 CellStruct | — | `[已证]` | 路径 B |
| 类型指针（鉴定用） | `obj+0x520` → `+0x24` ID 串；vtable `0x7E4570`=BuildingTypeClass | 4 | `[已证]` | §0；勿用作取格基址 |

**使用顺序**：G0/G1/G2 确认局内 → 枚举 `AbstractClass::Array` 取 BuildingClass（`vt==0x7E3EBC` RTTI 已证）→ 按路径 A 算 `cell` → 读 `cell+0xE4/E8` + 遍历 `+0x30` → 得"该格是否已被占用"，从而真正检验 ②-b。全程只读，不写进程内存、不注入、不改 `ra2youli\`。
