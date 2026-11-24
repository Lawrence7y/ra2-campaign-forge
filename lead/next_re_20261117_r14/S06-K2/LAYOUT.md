# S06-K2 LAYOUT（T1–T3）

卡号 **S06-K2**｜目标 `ra2youli\gamemd.exe`（SHA-256 `73201CC0…F67476`，ImageBase `0x400000`，只读）。
工具：Python 3.12.10 + capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26。所有脚本在 `work/`，原始输出在 `EVIDENCE/`。

---

## T1 · CellClass 字段表逐字段双支撑

### 方法集（来自 .rdata RTTI，不依赖 atlas 边界）
CellClass 有 4 个 COL（多重继承，offset-to-top = 0x0/0x4/0x8/0xC），对应 4 张虚表：
`0x7e4eec`(主，24 槽)、`0x7e4ed0`、`0x7e4ec8`、`0x7e4ec0`。
**权威方法集 = 4 张表全部 `.text` 槽的并集 + 10 个已知非虚函数**（ctor `0x47bbf0` / dtor `0x47bb60` / ctor2 `0x483a00` / ore `0x485020` / getcenter `0x47ff80` / attach `0x5683c0` / detach `0x5687f0` / linkadd `0x47e8a0` / linkdel `0x47ea90` / canplace `0x47c620`）= **51 个函数**。
> K1 的 "62 方法族" 用主表 `vt0..vt59`，其中 `vt24+` 已越出真表（slot24/25=0、slot26-28=浮点常量、slot30 起是别的类），故 K1 把 Logic/Layer/List/Control 类方法误扫入（audit §6 已指出）。本卡纠正。
> 证据：`EVIDENCE/foundation.txt`、`EVIDENCE/method_sets.txt`。

### 字段数 = 63（与 §958 / S06-K1 audit 一致，无 DISAGREE）
`sweep [this+disp]`、`disp∈[0x24,0x148)`、去重 ⇒ **恰好 63 个偏移**（`t1_fields.py` 自算 = 63）。
- `+0xB8`：**0 个本类写点**（全局 142 条但本类 0，§958 已删）。core_numbers 复核 writes=0。
- 补 `+0x6C/+0x70/+0x74`（ctor `0x47BC4F/5D/70`，`lea ebp,[esi+0x68]` 派生基址 `[ebp+4]/[ebp+8]/[ebp+0xC]`）。
- 两处 `rep stosd` 清零区：`+0x7C..+0xAB`、`+0xAC..+0xDB`（ctor `0x47BD80/0x47BD8D`，各 12 dword）——对应 YRpp `SensorsOfHouses[0x18]`/`DisguiseSensorsOfHouses[0x18]`。
- direct-write-only this-tracker 得 60；补 `+0x26`(dword@+0x24 覆盖)、`+0x7C`/`+0xAC`(rep stosd) 后 = 63（复算透明，见 `EVIDENCE/core_numbers.txt`）。

### 双支撑 = 17/63
每个偏移要求「本类写点全集 + ≥1 读点」。读点采集两遍：`t1_fields.py`（本类方法）与 `t1d_reads_complete.py`（**不因早退 ret 截断**，覆盖 `0x485033` 早退后 `0x48503F` 的 `+0x11E` 读）+ GetCellAt 返回 `eax` 全局窗口。
- **显式剔除虚调用** `call/jmp [reg+disp]`（vtable 槽调用非数据读）：CellClass 方法集 **51 处**，含 1439 个 GetCellAt 窗口的全扫 **4790 处**（§969 审计同类）。
- **禁止跨类套用**：`+0x94`(ObjectClass=层索引)、`+0x184`(Anim=DelayTimer)、`+0x80`(精灵脏标记) 均未套用到 CellClass；`+0x13C` 特别标注 CellClass vs MapClass 同名异类。

17 个双支撑字段（完整写点/读点见 `EVIDENCE\t1_FINAL.txt` / `t1_field_table.txt`）：

| 偏移 | 宽度 | 语义 | 分级 | #W | #R |
|---|---|---|---|---|---|
| +0x24 | word | MapCoords.X | 已证 | 1 | 17 |
| +0x26 | word | MapCoords.Y | 已证 | 1(cover) | 6 |
| +0x28 | ptr | FoggedObjects | 静态推断 | 2 | 1 |
| +0x2C | ptr | BridgeOwnerCell | 静态推断 | 1 | 2 |
| +0x34 | ptr | LightConvert | 静态推断 | 2 | 1 |
| +0x38 | dword | IsoTileTypeIndex（地形类型） | 静态推断 | 1 | 13 |
| +0x44 | dword | OverlayTypeIndex（覆盖物/矿类型） | 已证 | 1 | 24 |
| +0xE4 | ptr | FirstObject（占格链 HEAD A） | 已证 | 4 | 2 |
| +0xE8 | ptr | AltObject（桥上链 HEAD B） | 已证 | 3 | 2 |
| +0xFC | dword | unknown_FC | 静态推断 | 2 | 1 |
| +0x100 | dword | OccupyHeightsCoveringMe | 静态推断 | 1 | 3 |
| +0x11A | byte | Height | 静态推断 | 1 | 15 |
| +0x11B | byte(signed) | Level（高度 level） | 已证 | 1 | 5 |
| +0x11E | byte | Powerup/矿石密度 | 已证 | 1 | 9 |
| +0x12C | dword | CopyFlags（低5位 infantry subpos） | 静态推断 | 1 | 1 |
| +0x13C | dword | unknown_13C（**CellClass 自有**） | 静态推断 | 1 | 2 |
| +0x140 | dword | Flags/OccupationFlags | 静态推断 | 1 | 32 |

字段语义以「写点值 + 读点上下文」为主，YRpp `CellClass.h`/`ObjectClass.h`（`ref/yrpp/`）仅作语义标签线索， BYTE 证据见 EVIDENCE。特别：K1 曾证伪 `+0xFC..+0x100`=坐标（实为 delete 指针/OccupyHeights），本卡维持。

---

## T2 · GetSize 双向核对（闭合）

**Channel A（v[12]）**：主表 `0x7E4EEC` 的 `v[12]=0x487E70`，字节 `B8 48 01 00 00 C3` ⇒ **0x148 (328)**。
辅助 3 张表 `v[12]` 分别为 `0x410300`(B8 imm C2)、`0x485200`、`0x4839F0`，均非 B8/C3 —— 只有主表是 GetSize（多重继承的偏移表 v[12] 不是同一函数）。
**Channel B（构造分配点）**：`push 0x148` 全镜像 12 处，其中 `0x5663C3`、`0x566B96` 紧接 `call 0x7C8E17`(operator new) → `call 0x47BBF0`(CellClass ctor)（`EVIDENCE/t2_getsize.txt` 上下文逐条打印）。两处独立对上 ⇒ **闭合**。

**基线（§969 纪律 1，先测基线）**：`.text` 内 `B8 imm32 C3` 裸候选 **666** 处（whole-file raw 668；§969 记 ~837，口径/范围不同，见 DISAGREE），其中 **597** 处不在任何 RTTI 虚表 slot12 —— 判据不特异，**必须叠加「值确在本类 vtable 槽 12」**。叠加后 size-0x148 的 B8/C3 全镜像仅 2 处，落在 CellClass 主表 v[12] 的唯一一处即 `0x487E70`。
**0x4C9150 陷阱**：字节 `33 C0 C3`（xor eax,eax; ret）是抽象基类共用桩；MapClass v[18..21] 指向它，**不是**任何类的真 GetSize。证据：`EVIDENCE/t2_getsize.txt`。

---

## T3 · MapClass 深化（确认 30 槽，不重开 179 之争）

### 30 槽定界（确认 §958）
TD `0x816BC0`(.?AVMapClass@@) → COL `0x8054C8` → 主表 `0x7ED404`，连续 **30 个 `.text` 槽**（0..29，止于 `0x7ED478`），终止符 `0x7ED47C = 0x8055E0`（下一张 VectorClass 表的 COL）。第 30 项已是 `.rdata`，**不是函数**。`EVIDENCE/foundation.txt` 逐槽打印。
槽 18/19/20/21 = `0x4C9150` 共享桩（非 GetSize）；v[12]=`0x4F4410` 为 thunk，整表无 B8/C3 ⇒ **MapClass 无 GetSize**（确认 audit，非 AbstractClass 派生）。

### 字段布局与格数组
- **+0x13C 指针字段 = `0x87F924`**（= singleton `0x87F7E8` + 0x13C，§961）：绝对寻址 `[0x87F924]` **399 处全为读**（raw `A1` 7 处 + SIB 形式）；**0 处绝对写**（raw 搜 `A3/C705/8915` 全 0）。写点在 MapClass 基 ctor `0x565090` 内 `0x565105 mov [esi+0x13C],ebx`（初始化 0），后续格数组基址经 `[reg+0x13C]` base+disp 形式维护（全镜像 54 处 write，但多数属别的类同偏移字段——offset≠semantics，未强行归属）。证据 `EVIDENCE/t3_map.txt`/`t3c`/`t3e`/`t3f`。
- **stride = 4 字节证据**：`GetCellAt 0x5657A0`：`0x5657AC shl eax,9`（Y×512）、`0x5657AF add eax,esi`（+X）、`0x5657B4 cmp eax,0x40000`（上界）、`0x5657BB mov ecx,[ecx+0x13C]`、`0x5657C1 mov eax,[ecx+eax*4]`（字节 `8B 04 81`，**×4**）、NULL 回退 InvalidCell `0xABDC50`（`+0x24` 写请求坐标）。即 `cell=[[MapClass+0x13C]+idx*4]`，`idx=(short)Y<<9+(short)X∈[0,0x40000)`。证据 `EVIDENCE/map_getcellat.txt`。
- **维度**：`shl 9` ⇒ 2^9=512 宽；`cmp 0x40000` ⇒ 512×512=0x40000 格。全局单例 0x87F7E8 的最终动态类型是 PowerClass（vft 0x7EFF54），MapClass 基子对象在偏移 0。
- **视口/滚动原点** `0x886FA0`(+X)/`0x886FA4`(+Y)：R14 §4.4 已证（各 2 写），本卡只引用不复证。

---

## T4 · 两条格链表（静态，服务 ②-b，独立于 S12-K2）

### 读写点全集（`EVIDENCE/t4_lists.txt`，cell* 归属：CellClass 方法 + 1439 GetCellAt 窗口）
- **HEAD A / `+0xE4`（FirstObject，ground 占格对象链）**：W=4 (`0x47BBA7` dtor, `0x47BC82` ctor, `0x47E91F` linkadd, `0x47EACF` linkdel)；R=7 (`0x47E8B8` linkadd, `0x47EAB3` linkdel, `0x47C657/683/712/79E/7D9` can-place `0x47C620`)。**write+read 双支撑 ✓**
- **HEAD B / `+0xE8`（AltObject，桥上对象链）**：W=3 (`0x47BC88` ctor, `0x47E90B` linkadd, `0x47EAC4` linkdel)；R=2 (`0x47E8B0` linkadd, `0x47EAAB` linkdel)。**write+read 双支撑 ✓**
- **元素 `+0x30` = next**：这是链表**元素（ObjectClass）**的 `NextObject`，在 linkadd/linkdel 中大量 R/W（`0x47E8DB/E4/EB`、`0x47E908/E91C`、`0x47EAC1/E2/ED`）；`CellClass+0x30` 自身无本类读点（audit 异常，非 next）。

### 语义判定（双支撑）
- `0x47E8A0 = CellClass::AddContent(Content, onBridge)`、`0x47EA90 = RemoveContent`（YRpp 地址交叉确认 `0x47E8A0`/`0x47EA90`）。链头选择：`linkadd` 参数 arg2（`[esp+8]`）为 0→HEAD A、非 0→HEAD B；`linkdel` 参数（`[esp+0x1C]`）同。
- 上游 wrapper `0x5683C0`(attach)/`0x5687F0`(detach) 在调用前 `mov dl,[edi+0x8C]`（`0x5684B1`/`0x5688E1`）—— **`[obj+0x8C]=OnBridge`** 决定入哪条链。
- **HEAD A = FirstObject = 占格对象链（ground）**：`0x47C620`（can-place 逐格校验，R14 §2）**只扫此头**，遇 WhatAmI==6(Building) 特判。
- **HEAD B = AltObject = 桥上对象链（onBridge 层）**：仅由 onBridge 对象使用，can-place 不扫。
- `GetContent() = ContainsBridge() ? AltObject : FirstObject`（YRpp CellClass.h:227-228）——与字节证据一致。

### 与 S12-K2（审计中、未采信）对照——**独立验证，结论一致，无 DISAGREE**
| S12-K2 声称 | 本卡独立复核 | 结论 |
|---|---|---|
| `0x47C620` 只扫 head A(`+0xE4`) | `0x47C657/683/712/79E/7D9` 全为 `[edi+0xE4]`，全文无 `[edi+0xE8]` | ✅ 一致 |
| `0x47E8A0` 按对象 `[+0x8C]` byte 选头 | `linkadd` arg2 选头，wrapper `0x5684B1 mov dl,[edi+0x8C]` 送入 | ✅ 一致 |

证据：`EVIDENCE/t4_wrappers.txt`、`t4_lists.txt`、`cell_methods.txt`、`t4_wrappers.txt`。

---

## 与 §958 / §961 / K1 的一致性
- 字段数 63：一致（无 DISAGREE）。MapClass 30 槽：一致。0x87F924 是**指针字段地址**：一致。
- 基线计数 666 vs §969 的 ~837：口径差异，已记 `DISAGREE.md`（不推翻结论）。
- S12-K2 两条链结论：本卡**独立验证一致**（见上 T4），未采信其结论当事实。
