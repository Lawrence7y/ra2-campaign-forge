# S11-K2 LAYOUT · Locomotor 类族布局 / COM 契约 / GetSize / 字段 / 槽语义

> 目标 `gamemd.exe` SHA `73201CC0…F67476`，ImageBase 0x400000，只读字节通道。
> 全部数据由 `work/fresh_core.py`（RTTI/vtable）、`fresh_closure.py`（GetSize+CLSID）、`fresh_fields.py`（字段）、`fresh_slots.py`（槽语义）独立重取；`capstone skipdata=True`，不依赖 `function_atlas.tsv` 做发现。
> ⚠️ **核心更正（D2，Lead 已批准）**：GetSize 在本类族是 **off=0（IPersistStream 侧）vtable 的 slot 9**，**不是** AbstractClass 惯例的 slot 12。此更正影响所有 COM 多继承类的 GetSize 取证。

## 1 · 实现类清单（RTTI 实测，12 类；类名只认 `COL+0xC→TD+8`，读不到 fail-closed）

| 类（RTTI TD 名） | TD | off=0 主 COL | off=4 主 VT / 槽数 | off=24 IPiggyback VT / 槽数 | 父类（CHD 实测） |
|---|---|---|---|---|---|
| LocomotionClass（抽象基类） | 00820228 | 008032E8 | 007EADF4 / 50 | — | IPersistStream, IPersist, IUnknown, ILocomotion, IUnknown |
| DriveLocomotionClass | 00820248 | 007FFEB0 | 007E7EB0 / 50 | 007E7E8C / 8 | LocomotionClass, …, IPiggyback |
| DropPodLocomotionClass | 008202F8 | 008000A8 | 007E8278 / 50 | 007E8254 / 8 | LocomotionClass, …, IPiggyback |
| FlyLocomotionClass | 008223E8 | 008006B8 | 007E89F4 / 50 | — | LocomotionClass（无 IPiggyback） |
| HoverLocomotionClass | 008254B8 | 00803288 | 007EACFC / 50 | — | LocomotionClass |
| JumpjetLocomotionClass | 00829648 | 00804CF0 | 007ECD68 / 50 | 007ECD44 / 8 | LocomotionClass, …, IPiggyback |
| MechLocomotionClass | 0082C228 | 00805C88 | 007EDB6C / 50 | — | LocomotionClass |
| RocketLocomotionClass | 008399C8 | 00808968 | 007F0B1C / 50 | — | LocomotionClass |
| ShipLocomotionClass | 0083F880 | 00809408 | 007F2D8C / 50 | 007F2D68 / 8 | LocomotionClass, …, IPiggyback |
| TeleportLocomotionClass | 00844538 | 0080C1E0 | 007F5000 / 50 | 007F4FDC / 8 | LocomotionClass, …, IPiggyback |
| TunnelLocomotionClass | 00844AA0 | 0080CB48 | 007F5A24 / 50 | — | LocomotionClass |
| WalkLocomotionClass | 00847BF0 | 0080D2A8 | 007F69F8 / 50 | 007F69D4 / 8 | LocomotionClass, …, IPiggyback |

- 30 张 vtable（12×off0 + 12×off4 + 6×off24），槽数合计 **770**（off4: 12×50=600；off0: 11×10+12=122；off24: 6×8=48）。定界全部从 `.rdata` 的 `COL`/`vtable[-1]`/表间边界做（纪律 7），未用 atlas 边界反推。
- off=0 表槽数：11 类 = 10；**Teleport = 12**（多出 2 槽语义 `[未证]`）。See UNKNOWNS #3。
- `vtables_v2.json` 槽数有错（13,351 vs 实测 14,044），本卡自行数，不引用 JSON 槽数。

## 2 · COM/vtable 契约与 CLSID

- 每个类是 **多接口 COM 对象**：`IPersistStream`@off0（GetSize 在 slot9）+ `ILocomotion`@off4（50 槽，主派发接口）+ `IPiggyback`@off24（8 槽，6 类有）；CHD 如实列出。
- `ILocomotion` 走**手工 vtable + 栈传 this**（非标准 thiscall）：`mov eax,[this+0x674]`→`push eax`(this)→`mov ecx,[eax]`(vtable)→`call [ecx+0x40]`。
- **CLSID 11 项**：`.rdata 0x7E9A30..0x7E9ADF`，每项 16B GUID（`4A582741`..`4A582747` + 4 个其它），`0x7E9A20` 是基类 GUID `4A582740`（未注册）。**无静态 {GUID→类→工厂} 并列表**（.rdata 无 dword 落工厂 ctor 区间，count=0，`EVIDENCE/t1_clsid_check.txt`）；映射在注册函数 `0x6BB9A0` 代码内（S11-K1 已入账，本卡复核一致）。

## 3 · GetSize 双向核对（核心数字，11/11 闭合）

| 类 | 工厂 CI | A: off0 slot9 字节 | imm=sizeof | B: 工厂 `push<size>;call new` 编码 | 闭合 |
|---|---|---|---|---|---|
| Drive | 006C4010 | 004B4CF0 B8 70..C3 | 0x70 | 6A 70 (imm8) | ✓ |
| DropPod | 006C4910 | 004B66E0 B8 30..C3 | 0x30 | 6A 30 | ✓ |
| Fly | 006C4A90 | 004D0390 B8 60..C3 | 0x60 | 6A 60 | ✓ |
| Hover | 006C4310 | 005172B0 B8 78..C3 | 0x78 | 6A 78 | ✓ |
| Jumpjet | 006C4190 | 0054DF90 B8 98..C3 | 0x98 | **68 98 00 00 00 (imm32)** | ✓ |
| Mech | 006C4D90 | 005B1B40 B8 34..C3 | 0x34 | 6A 34 | ✓ |
| Rocket | 006C4490 | 006635B0 B8 60..C3 | 0x60 | 6A 60 | ✓ |
| Ship | 006C4F10 | 006A42A0 B8 70..C3 | 0x70 | 6A 70 | ✓ |
| Teleport | 006C4C10 | 0071A120 B8 4C..C3 | 0x4C | 6A 4C | ✓ |
| Tunnel | 006C4610 | 0072A200 B8 3C..C3 | 0x3C | 6A 3C | ✓ |
| Walk | 006C4790 | 0075CBD0 B8 3C..C3 | 0x3C | 6A 3C | ✓ |

- **判据不特异已处理**：`.text` raw `B8 imm32 C3` = 666（全文件 668）；叠加「值确在本类 off0 slot9」后仅 11 命中。⇒ 单扫裸字节无区分力，必须叠加 vtable 槽归属（D2/D3）。
- **§972 陷阱复现**：`6A imm8` = 10/11，`68 imm32` = 1/11（Jumpjet）；只扫 imm32 会漏 10 个。
- **§971 排除**：基类桩 `004C9150`（`xor eax,eax;ret`，出现在 off0 slot3 与 off4 slot29）是多抽象类共用，不当作任何具体类 GetSize。

## 4 · 字段布局（增量，DriveLocomotionClass 自身写点+读点双支撑）

列：`偏移 | 宽度 | 类型 | 写者全集(计数) | 读者≥3(计数) | 语义 | 分级`

| 偏移 | 宽度 | 类型 | 写者 | 读者 | 语义（字节层） | 分级 |
|---|---|---|---|---|---|---|
| +0x4 | 4 | vptr | 11（ctor+10 槽） | 2 | off4 主 vtable 指针槽（写入多次=构造/析构回退） | [已证] 存在；[未证] 定名 |
| +0x8 | 4 | ptr | 6 | 19 | 宿主对象指针（`[this+8]`→`[host]`→`call [vt+0x1C8]`，19 读） | [已证] 存在+解引用形态；[未证] 精确类型 |
| +0x30 | 4 | ptr/int | 2 | 3 | 坐标/状态缓冲（`lea [this+0x30]` 被读） | [已证] 双支撑；[未证] 语义 |
| +0x38 | 4 | ptr | 1 | 3 | 宿主派生指针（`ReadOnly` 解引用） | [已证] 双支撑；[未证] 语义 |
| +0x40 | 4 | int | 1 | 4 | 状态量（ctor 写 + 槽6/18 读） | [已证] 双支撑；[未证] 语义 |
| +0x4C | 8 | **double** | 1 | 3 | `fld/fstp qword [this+0x4C]` ⇒ 8B 浮点 | [已证] 类型+双支撑；[未证] 语义 |
| +0x54 | 4 | int | 1 | 2 | 已入账前提：`!=-1` 有目标（槽47 getter 返此值） | [已证]（已入账） |
| +0x58 | 4 | int | 1 | 2 | 槽48 getter 返此值（与 +0x54 配对） | [已证] 双支撑；[未证] 语义 |
| +0x68 | 4 | int | 2 | 4 | 状态标志（off0 slot5 写 0 / 多槽读） | [已证] 双支撑；[未证] 语义 |

- 扫描 69 个函数（Drive ctor + 3 接口全部槽），`call/jmp [reg+disp]` 虚槽调用 **剔除 34 处**（`EVIDENCE/fresh_fields.txt` 首行），不计入数据字段读点（纪律：§969/§972）。
- 只扫本类自身函数，无跨类套用；`+0x94`/`+0x184`/`+0x80` 未套用本族。字段偏移不定语义（只标字节层事实，高层语义列 `[未证]`）。
- 已入账前提沿用：`loco+0x54`（`!=-1` 有目标）、`loco+0x5F`（`!=0` 移动中）——后者本扫描未落在 Drive 区间（+0x5F 属基类/别类），不重开。

## 5 · 虚表槽语义（优先 off=4 锚点；其余保守）

| 槽 | Drive off4 实现 | 语义 | 分级 |
|---|---|---|---|
| off4 7 | 0055ABF0 | Can_Enter_Cell：调用点 004D9C4B `ff 51 1c`，基桩 `xor eax,eax;ret 8` | [已证] 槽↔调用点 |
| off4 16 | 004B0500 | Process：调用点 004DA877 `ff 51 40`（每帧派发，K1 已入账） | [已证] 槽↔调用点 |
| off4 17 | 004AFD40 | Move_To：调用点 004D562C `ff 51 44`，基桩 `ret 0x10` | [已证] 槽↔调用点 |
| off4 18 | 004AFE00 | Stop_Moving：调用点 004D55E0 `ff 51 48`，基桩 `ret 4` | [已证] 槽↔调用点 |
| off4 47/48/49 | 004B4C00/10/20 | getter：分别返 `[this+0x54]/[this+0x58]/[this+0x48]` | [已证] 字节 |
| off0 9 | 各类 B8imm32C3 | GetSize（见 §3，11/11 闭合） | [已证] |
| off0 3 / off4 29 | 004C9150 | 抽象基类共用桩 `xor eax,eax;ret`（§971） | [已证] 为桩，非 GetSize |
| off4 其余槽 | 见 `EVIDENCE/fresh_slots.txt` | 仅实现地址+首指令；语义按 YRpp 顺序（外部文档），无本类调用点证 | [静态推断]/[未证] |
| off4 11 | 0055ABD0 | 向输出缓冲写两个 0 的 `ret 8` 函数，**非 WhatAmI** | [已证] 字节行为；WhatAmI 归属 [未证] |

- 4 个锚点调用字节直接读取复核：`004D9C4B ff 51 1c`、`004DA877 ff 51 40`、`004D562C ff 51 44`、`004D55E0 ff 51 48`（`EVIDENCE/fresh_slots.txt`）。
- `ret 0xC` 判据不特异（§969 记 672 次命中），本卡**不用**它定虚表槽语义；改用调用点 `ff 51 disp` + 槽号 = disp/4 的直接映射。
