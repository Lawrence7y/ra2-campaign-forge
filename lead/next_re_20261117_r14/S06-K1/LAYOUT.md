# S06-K1 LAYOUT — CellClass / MapClass 字段布局

> 卡号 S06-K1 · 目标 `gamemd.exe` SHA-256 `73201CC0…F67476` · ImageBase `0x400000`
> 全部证据为静态只读反汇编（capstone 5.0.7 `skipdata=True` + pefile）。类名只取自 RTTI TypeDescriptor（纪律 17）。
> 详细复跑脚本见 `work/`，未截断证据见 `EVIDENCE/`。

## 1 · 类身份与 RTTI（已证）

| 类 | TypeDescriptor | 名字 | 主 vtable (COL offset=0) | WhatAmI v[11] | GetSize v[12] | 构造器 |
|---|---|---|---|---|---|---|
| CellClass | `0x81CD70` | `.?AVCellClass@@` | `0x7E4EEC` | `0x487E60`→`11` | `0x487E70`→`B8 48 01 00 00 C3` = **0x148 (328)** | `0x47BBF0` |
| MapClass | `0x816BC0` | `.?AVMapClass@@` | `0x7ED404` | `0x4F43F0`（**非** WhatAmI 形态） | `0x4F4410`（**非** B8/C3） | `0x565090` |

- CellClass 另有 3 个从属 vtable `0x7E4ED0/0x7E4EC8/0x7E4EC0`（COL offset=4/8/12），构造器写 4 个 vptr（`+0/+4/+8/+0xC`）。
- **MapClass 无 GetSize 虚方法**：全 vtable 179 个 .text 槽，`B8 imm32 C3` 形态 **0 处**。MapClass 的基类构造器是 `0x4F4220`，**不是** AbstractClass 的 `0x410170` ⇒ MapClass 不是 AbstractClass 派生类，不适用「槽 11=WhatAmI、槽 12=GetSize」的 69 类通例。单例 `0x87F7E8` 的最终动态类型是 `PowerClass`（vtable `0x7EFF54`，RTTI `.?AVPowerClass@@`），经 `DisplayClass(:MapClass)` 链派生（ctor 链 `63F6B0→652960→4A8730→565090`）；MapClass 基子对象在偏移 0，同样无 GetSize。详见 `DISAGREE.md`。

## 2 · CellClass 字段表（已证 = 构造器写点 + 方法读点双支撑；GetSize=0x148）

> 写者/读者站点列为代表性站点；全表原始 223 条见 `EVIDENCE/cell_fields_raw.txt`。
> `§933 PROBE_TABLE` 的 `+0xFC..0x100=格坐标候选` 经构造器/析构器证明为**错误**：`+0x24/+0x26` 才是 MapCoords；`+0xFC` 是析构时 delete 的指针。见 `DISAGREE.md`。

| 偏移 | 宽 | 推断类型 | 写者站点（示例） | 读者站点（示例） | 语义 / 分级 |
|---|---|---|---|---|---|
| +0x00/04/08/0C | 4 | vptr×4 | ctor `47BB69/71/78/7F`, `47BD5C/62/68/79` | dtor `47BB88`, vt 多处 | 主/从 vtable 指针（4 个，多重继承）[已证] |
| +0x24 | 2 | short X | ctor `47BC02` | dtor `47BBAD`, getcenter `47FF89`, vt18 `486845` | **MapCoords.X**（格坐标）[已证] |
| +0x26 | 2 | short Y | ctor `47BC02`(dword 合写) | dtor `47BBBA`, getcenter `47FF8D`, vt18 `486849` | **MapCoords.Y** [已证] |
| +0x28 | 4 | ptr | ctor `47BC05`, dtor `47BB8E` | dtor `47BB66` | 附属对象指针，析构 delete（`call [v+0]` push 1）[已证] |
| +0x2C | 4 | dword | ctor `47BC08` | linkdel `5687…` | 保留/标志 [静态推断] |
| +0x30 | 4 | CellClass* next | ctor `47BC0B`, linkdel | attach/detach `5685…` | **格链表 next**（已知锚点，核实成立）[已证] |
| +0x34 | 4 | ptr | ctor `47BC0E`, dtor `47BBDC` | dtor `47BBC7` | 关联对象指针；非空时 `dec [obj+0x194]` [已证] |
| +0x38 | 4 | dword | ctor `47BC11`=0xFFFF | getcenter `48001F`, vt20 `4867E0`, `485060` | 地形/瓦片类型候选(=0xFFFF 无)；范围比对 [静态推断] |
| +0x3C/+0x40 | 4 | dword | ctor `47BC18/1E` | — | 保留 [静态推断] |
| +0x44 | 4 | dword ID | ctor `47BC21`=-1 | ore `485023`, vt38 `4886E9` | **覆盖物/矿石类型 ID**；-1=无，`0x5FDD20` 转索引 [已证] |
| +0x48/+0x4C | 4 | dword | ctor `47BC24/27` | — | 保留 [-1/0 初始化] [静态推断] |
| +0x50 | 4 | dword=-1 | ctor `47BC2A` | — | 保留 [静态推断] |
| +0x54 | 1(byte)/4 | flag | ctor `47BC2D`=-1 | vt41 `557E18`, vt42/43/47/56/57 | 附属对象存在性门控（非 0 则扫 +0x118/+0xB8/+0x58）[静态推断] |
| +0x58 | 4 | ptr/obj | ctor `47BC30`=-1 | vt41 `557E3F`, vt42/43/47/56/57 | 内嵌对象（虚调 `[v+0xC]`）[静态推断] |
| +0x5C..0x64 | 4 | dword=-1 | ctor `47BC33/39/3E` | — | 保留 [-1 组] [静态推断] |
| +0x68..0x74 | 4×4 | dword 数组 | ctor `47BC41/4F/5D/70`(ebp 循环) | ctor `47BC41` | 4 元状态数组（清 0）[已证存在,语义未证] |
| +0x78 | 4 | dword | ctor `47BC73` | — | 保留 [静态推断] |
| +0x7C..0xA8 | 4×12 | dword 数组 | ctor `47BD80` rep stosd×12 | ctor `47BC…` | 12 元数组（清 0）[已证存在,语义未证] |
| +0xAC..0xD8 | 4×12 | dword 数组 | ctor `47BD8D` rep stosd×12 | vt41 等读 +0xB8 | 12 元数组（清 0）；+0xB8 为内嵌对象 [部分已证] |
| +0xDC/+0xE0 | 4 | dword | ctor `47BC76/7C` | — | 保留 [静态推断] |
| +0xE4 | 4 | 链表头 A | ctor `47BC82`, dtor `47BBA7`, linkadd/linkdel | linkadd/linkdel | **格对象链表头 1**（已知锚点，核实成立）[已证] |
| +0xE8 | 4 | 链表头 B | ctor `47BC88`, linkadd/linkdel | linkadd/linkdel | **格对象链表头 2** [已证] |
| +0xEC/+0xF0/+0xF4/+0xF8 | 4 | dword | ctor `47BC93/99/CF/D5` | — | 保留/标志 [静态推断] |
| +0xFC | 4 | ptr | ctor `47BCDB`, dtor `47BBA1` | dtor `47BB91` | **附属对象指针**（析构 delete）；非格坐标 [已证] |
| +0x100 | 4 | dword | ctor `47BCE7` | — | 保留（非格坐标）[静态推断] |
| +0x104 | 4 | dword=0x10000 | ctor `47BCED` | — | 常量/标志 [已证存在] |
| +0x108..0x114 | 2×7 | word=1000 | ctor `47BC69/9F/A6/AD/B4/BB/C2` | — | 7 个 lepton 尺寸/阈值常量 [已证存在] |
| +0x116 | 2 | word=-1 | ctor `47BC48` | — | 保留 [静态推断] |
| +0x118 | 4 | 内嵌对象 vptr? | ctor `47BCF7`=0xFF(低字节) | vt41 `557E1F/25` | 内嵌对象（虚调 `[v+0xC]`）[静态推断] |
| +0x119..0x11D | 1 | byte | ctor `47BCFE..47BD16` | — | 保留字节 [静态推断] |
| +0x11B | 1 | byte level | ctor `47BD0A`=0 | getcenter `47FFE7` | **格面高度 level**：`movsx×15` 修正绘制 Y 偏移 [已证] |
| +0x11E | 1 | byte density | ctor `47BD1C`=0 | ore `48503F` | **矿石密度/等级**：ore 返回 `value×(density+1)` [已证] |
| +0x11F..0x122 | 1 | byte | ctor `47BD22/28/2E/34` | — | 保留字节（+0x120/121=0xFE）[静态推断] |
| +0x124/+0x128 | 1 | byte | ctor `47BD95/9B` | — | 标志 [静态推断] |
| +0x12C | 4 | dword flags | ctor `47BC60`(&~0x1F) | ctor `47BC52`, `6D7A4F` | **格旗标**（低 5 位被清；含迷雾/通行位）[已证] |
| +0x130 | 4 | dword=1 | ctor `47BD3A` | — | 初始化标志 [已证存在] |
| +0x134/+0x138/+0x13C/+0x140 | 4/1/4/4 | dword/byte | ctor `47BD44/4A/50/56` | attach/detach `568…` (+0x13C/+0x140) | 保留/关联 [部分已证] |

**字段数 = 61**（`0x24 ≤ disp < 0x148` 的 distinct offset；由 `work/core_numbers.py` 复算，见 `EVIDENCE/core_numbers.txt`）。

### 关键语义锚点（重点找字段）

| 目标 | 结论 | 证据 |
|---|---|---|
| 地形类型 | `+0x38` dword，默认 0xFFFF；`vt20 4867E0`/`485060` 与全局 `0xAA0738` 做 `[g, g+0xE)` 范围判定 ⇒ 类型 ID 候选，尚无写者复读双支撑，标 [静态推断] | `EVIDENCE/cell_methods_disasm.txt` |
| 地面高度 level | `+0x11B` byte（ctor 0，getcenter `movsx×15` 修正 Y）[已证] | `EVIDENCE/cell_methods_disasm.txt` |
| 覆盖物/矿石类型 | `+0x44` dword ID（ctor -1；ore `485023` 读；vt38 `4886E9` 读）[已证] | `EVIDENCE/ore_func_disasm.txt` |
| 矿石数量/密度 | `+0x11E` byte（ctor 0；ore `48503F` 读，×（密度+1））[已证] | `EVIDENCE/ore_func_disasm.txt` |
| 是否被占用 | 未找到独立 bool 字段；占用经 `+0xE4/+0xE8` 链表（`0x47E8A0` 挂链不做校验，校验在上层 Unlimbo，R14_COMMON §2.2）[已证(机制)/未证(字段)] | `EVIDENCE/cell_fields_raw.txt`, R14_COMMON §2.2 |
| 可见性位图 | `+0x12C` 低 5 位清 0，含 fog/可通行位候选；未找到专门位图读写，标 [未证] | `EVIDENCE/cell_ctor_disasm.txt` |
| 格旗标 | `+0x12C` dword [已证存在,语义部分] | 同上 |

## 3 · MapClass 字段表（已证部分；GetSize 缺如）

| 偏移 | 宽 | 推断类型 | 写者站点 | 读者站点 | 语义 / 分级 |
|---|---|---|---|---|---|
| +0x000 | 4 | vptr | ctor `56516D`/`483A24`/`565268` | 全局 | vptr：MapClass 基 `0x7ED404`；单例最终为 PowerClass `0x7EFF54`（ctor `63F71C`）[已证] |
| +0x050 | obj | 内嵌 Vector | ctor `5650A4/A9` | — | `0x58ADB0` 构造，vft `0x7ED4C0` [已证] |
| +0x08C/0xA4/0xBC | obj×3 | 内嵌 Vector | ctor `5650C4/CD`（循环 ×3） | — | `0x58AE60` 构造，vft `0x7ED4A0` [已证] |
| +0x0D4 | obj | 内嵌对象 | ctor `5650ED/F9` | — | vft `0x7E3890` [已证] |
| +0x138 | 4 | vft ptr | ctor `56511D` | — | `0x7ED480` [已证] |
| +0x13C | 4 | CellClass** | ctor `565105`=0；`565800` 分配 | GetCellAt `5657BB` (399 abs refs) | **格数组基址**（已知锚点，核实成立）[已证] |
| +0x140 | 4 | dword | ctor `56510B` | — | 保留 [静态推断] |
| +0x144/+0x145 | 1 | byte | ctor `565111/117` | — | 标志 [静态推断] |
| +0x148 | 4 | dword=0xD | ctor `565173` | — | 常量 13 [已证] |
| +0x14C | 4 | int=0x200 | init `565819` | — | **地图宽 512** [已证] |
| +0x150 | 4 | int=0x200 | init `56581F` | — | **地图高 512** [已证] |
| +0x154 | 4 | int=0x40000 | init `565828` | — | **格总数 262144** [已证] |
| +0x115C | 4 | vft ptr | ctor `565157` | `48514D` | `0x7E3890` [已证] |
| +0x1160/0x1164/0x1168/0x1169/0x116C/0x1170 | 4/4/1/1/4/4 | dword/byte | ctor `56513F..565161` | 多处 abs | MapClass 尾段状态（关卡/计时/配置）[已证存在,语义未证] |

**字段数 = 17**（MapClass 基构造器 + GetCellAt/init 关键字段，distinct offset；`EVIDENCE/core_numbers.txt`）。
**size（派生边界法）= 0x1174 (4468)**：MapClass 基构造器末写 `+0x1170`(4B)；`DisplayClass` 派生构造器（`0x4A8730`，首个派生写 `+0x1174`）证实边界。**GetSize：无**（vtable 全扫 0 处 B8/C3；非 AbstractClass 派生）。越界写 = 0（17 字段 disp+width ≤ 0x1174）。

## 4 · GetSize 一致性 / 越界写扫描（双通道）

| 检查 | CellClass | MapClass |
|---|---|---|
| RTTI 主 vtable | `0x7E4EEC`(COL `0x7FD078`, offset 0) | `0x7ED404`(COL `0x8054C8`, offset 0) |
| v[12] 形态 | `B8 48 01 00 00 C3` → 0x148 | `0x4F4410` 非 B8/C3；全表 0 处 |
| 构造器 push | `push 0x148` @`5663C3/566B96/6BF9BC` → `new 0x7C8E17` → ctor `47BBF0` | 静态单例（无 new）；派生边界 `+0x1174` |
| 两处独立对上 | **是**（0x148 = 0x148） | N/A（无 GetSize 虚方法；size 由派生边界定） |
| 字段表 max(disp+width) | `0x140+4=0x144 ≤ 0x148` | `0x1170+4=0x1174 ≤ 0x1174` |
| **越界写数** | **0**（223 accesses / 96 writes 全查） | **0** |

双通道：通道 A = `function_atlas.tsv` `entry+size` 定方法边界；通道 B = capstone 全 `.text` 裸扫 E8 rel32（0x485020 得 20=20）+ RTTI COL/vtable 静态链；两通道不同源。

## 5 · 0x485020 矿石价值函数（已证）

```
485020: push esi; mov esi,ecx                ; esi = CellClass* this (ecx 溯源见下)
485023: mov ecx,[esi+0x44]                   ; ecx = ore/overlay type ID
485026: call 0x5FDD20                        ; type ID -> DynamicVector index (or -1)
48502B: cmp eax,-1; je no_ore->return 0
485034: mov ecx,[0xB0F4EC]                   ; DVC<TiberiumClass*>.Items
48503A: mov edx,[ecx+eax*4]                  ; edx = TiberiumClass* by index
48503F: mov al,[esi+0x11E]                   ; al = cell ore density byte
485048: mov eax,[edx+0xB8]                   ; eax = unit value
48504E: inc ecx                              ; density+1
48504F: imul eax,ecx                         ; return = value * (density+1)
485052: ret
```
- 读字段：cell `+0x44` (type ID)、`+0x11E` (density)；扫表：`DVC<TiberiumClass*>` @ Items `0xB0F4EC`（vft `0x7F56BC`, 静态初始化 `0x721640`）；返回：该格矿石总价值，无矿返回 0。
- **调用者数 = 20**（capstone-linear 20 == raw-byte 20；`EVIDENCE/ore_callers.txt`）。§923 所列 5 处是子集。ecx 溯源：每调用点 `mov ecx,0x87F7E8`→`push CellStruct`→`call 0x5657A0(GetCellAt)`→`mov ecx,eax(CellClass*)`→`call 0x485020`（纪律 14 满足）。
- **「每格每帧」调用计数**：静态结构证据——20 个调用点全在按格取值的循环/邻格扫描中（如 `4DD1xx` 连 4 点取最大矿价、`70F9DD..70FAFF` 连 4 点），每点一次针对一格；无 EIP 权重参与。**动态次数本身未测**（真机卡范围外），标 [静态推断]，见 `UNKNOWNS.md`。

## 6 · 格坐标 ↔ 索引 / CellStruct（已证）

```
CellStruct (4B):  +0 short X, +2 short Y     ; [esp+4]=ptr @GetCellAt
GetCellAt(this=0x87F7E8, cs):                ; 0x5657A0
  idx = ((int)(short)cs.Y << 9) + (int)(short)cs.X
  valid iff 0 <= idx < 0x40000               ; (js 5657C8 / cmp 0x40000 jge 5657C8)
  pCell = [ [this+0x13C] + idx*4 ]           ; 5657BB/5657C1, stride 4
  if pCell==NULL -> return &InvalidCell(0xABDC50), set [0xABDC74]=cs
逆: X = idx & 0x1FF (idx % 512), Y = idx >> 9 ; 地图 512×512
```
IsValidCell 判据：`idx ∈ [0,0x40000)`（`0x5657B2/B4`；另 `0x5657E0` 布尔版 `setne`）。`CellStruct` 两 short 布局亦见 `0x47FF89/8D`（GetCenterCoords）与 clue `cellclass_offsets_evidence.md`（该 clue 的勘误 E1: `0x655D38` EAX=高度非 pCell，本卡未引用）。
