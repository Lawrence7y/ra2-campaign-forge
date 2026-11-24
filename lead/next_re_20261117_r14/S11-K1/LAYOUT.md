# S11-K1 · Locomotor 类族（COM 接口）布局 / CLSID / vtable 槽语义

> 目标 `ra2youli\gamemd.exe`（SHA 73201CC0…F67476, ImageBase 0x400000）。纯静态，未改游戏文件。
> 证据在 `EVIDENCE\`，可复跑脚本在 `work\`。类名一律来自 RTTI TypeDescriptor（实测 `.?AVLocomotionClass@@` 等），非按文件名/偏移猜测。
> 分级：`[已证]`=二进制字节+调用点双通道（其中一通道为 Ghidra 反编译）；`[静态推断]`=结构自洽但无独立调用点；`[未证]`=未定。

## 0 · 核心数字（给审计）

| 量 | 值 | 复算 |
|---|---|---|
| Locomotor 类数 | **12**（含基类 LocomotionClass；11 派生类各有 CLSID） | `work\verify_final.py`：CH1 RTTI TD 名扫描 =12；CH2 代码 CLSID 注册 11 + 无 CLSID 基类 1 =12（两通道不同源） |
| CLSID 表项数 | **11** | `work\verify_final.py`：注册函数 `0x6BB9A0` 内 `push <CLSID>` 11 次 + `.rdata 0x7E9A30..0x7E9AD0` 11 个 16B GUID |
| 工厂函数地址 | **`0x41C250`**（`LocomotionClass::CreateInstance`） | `work\callscan.py` 13 个 E8 调用点；Ghidra 反编译见 `EVIDENCE\ghidra_corroborate.log` |
| `0x4DA877` 派发槽号 | **slot 16**（`[vtable+0x40]` = `ILocomotion::Process`） | `work\slot_anchors.py` + Ghidra: `CALL dword ptr [ECX+0x40]`，`ECX=[EAX]`,`EAX=[ESI+0x674]` |

## 1 · Locomotor 类族（RTTI TypeDescriptor 实测）

RTTI 链：`vtable[-1] = COL` → `COL+0xC = TD` → `TD+8 = ".?AV<Name>LocomotionClass@@"`（TD 在 `.data`，COL/vtable 在 `.rdata`）。
每个派生类族有 2–3 张子表：`off=4`（**ILocomotion 主接口，50 槽**，对象 `+4` 处的接口指针指向它）、`off=0`（IPersistStream 接口，10 槽；Teleport=12）、部分类另有 `off=24`（8 槽）。下表列 `off=4` 主接口 vtable（含 RTTI COL 地址）：

| 类（RTTI 名去掉 `.?AV@@`） | TD | COL(off4) | ILocomotion vtable(off4) | slot16=Process | CLSID |
|---|---|---|---|---|---|
| LocomotionClass（基类，无 CLSID） | 0x820228 | 0x8032A0 | **0x7EADF4** | 0x55AC60（桩） | — |
| DriveLocomotionClass | 0x820248 | 0x7FFDE8 | **0x7E7EB0** | 0x4B0500 | 0x7E9A30 |
| DropPodLocomotionClass | 0x8202F8 | 0x800040 | **0x7E8278** | 0x4B5B70 | 0x7E9A70 |
| FlyLocomotionClass | 0x8223E8 | 0x800658 | **0x7E89F4** | 0x4CCB40 | 0x7E9A80 |
| HoverLocomotionClass | 0x8254B8 | 0x803228 | **0x7EACFC** | 0x514310 | 0x7E9A40 |
| JumpjetLocomotionClass | 0x829648 | 0x804C88 | **0x7ECD68** | 0x54AEC0 | 0x7E9AC0 |
| MechLocomotionClass | 0x82C228 | 0x805C28 | **0x7EDB6C** | 0x5B0060 | 0x7E9AA0 |
| RocketLocomotionClass | 0x8399C8 | 0x808908 | **0x7F0B1C** | 0x6622C0 | 0x7E9AD0 |
| ShipLocomotionClass | 0x83F880 | 0x8093A0 | **0x7F2D8C** | 0x69FC10 | 0x7E9AB0 |
| TeleportLocomotionClass | 0x844538 | 0x80C178 | **0x7F5000** | 0x7192F0 | 0x7E9A90 |
| TunnelLocomotionClass | 0x844AA0 | 0x80CAE8 | **0x7F5A24** | 0x728E30 | 0x7E9A50 |
| WalkLocomotionClass | 0x847BF0 | 0x80D240 | **0x7F69F8** | 0x75AC80 | 0x7E9A60 |

`[已证]` 依据：`EVIDENCE\ch1_rtti_enum.txt`（12 个 TD 全表）、`EVIDENCE\verify_final.txt`（双通道）。
`off=0` 表：`LocomotionClass 0x7EAEC0`、Drive `0x7E7F7C`、Walk `0x7F6AC4` 等（10 槽）；`off=24`（8 槽）仅 Drive/DropPod/Jumpjet/Ship/Teleport/Walk 有。
⚠️ `.data` 中 `0x877000/0x877010/0x87B17C/0x87B18C` 是 DropPod COL@0x800040 的复用假表（slot0 非 `.text`），排除（台账 §849-1）。

## 2 · CLSID 表（11 项，位于 `.rdata 0x7E9A30..0x7E9AE0`，每项 16B GUID）

GUID 标准序 `{Data1-Data2-Data3-Data4}`，按内存小端 dword 读。映射来自注册函数 `0x6BB9A0`（含 `0x6BD15C..0x6BD3BE` 的 11 个 0x3D 字节块；每块 `new(8)`→`call <factory_ctor>`→`push CLSID`→`call 0x6C6400(RegisterClassObject)`）。

| CLSID 地址 | GUID | 类 | 类工厂 ctor | `CreateInstance` 实函 |
|---|---|---|---|---|
| 0x7E9A30 | 4A582741-9839-11D1-B709-00A024DDAFD1 | Drive | 0x6C3F40 | 0x6C4010 |
| 0x7E9AC0 | 92612C46-F71F-11D1-AC9F-006008055BB5 | Jumpjet | 0x6C40C0 | 0x6C41D0 |
| 0x7E9A40 | 4A582742-9839-11D1-B709-00A024DDAFD1 | Hover | 0x6C4240 | 0x6C4310 |
| 0x7E9AD0 | B7B49766-E576-11D3-9BD9-00104B972FE8 | Rocket | 0x6C43C0 | 0x6C4490 |
| 0x7E9A50 | 4A582743-9839-11D1-B709-00A024DDAFD1 | Tunnel | 0x6C4540 | 0x6C4610 |
| 0x7E9A60 | 4A582744-9839-11D1-B709-00A024DDAFD1 | Walk | 0x6C46C0 | 0x6C4790 |
| 0x7E9A70 | 4A582745-9839-11D1-B709-00A024DDAFD1 | DropPod | 0x6C4840 | 0x6C4910 |
| 0x7E9A80 | 4A582746-9839-11D1-B709-00A024DDAFD1 | Fly | 0x6C49C0 | 0x6C4A90 |
| 0x7E9A90 | 4A582747-9839-11D1-B709-00A024DDAFD1 | Teleport | 0x6C4B40 | 0x6C4C10 |
| 0x7E9AA0 | 55D141B8-DB94-11D1-AC98-006008055BB5 | Mech | 0x6C4CC0 | 0x6C4D90 |
| 0x7E9AB0 | 2BEA74E1-7CCA-11D3-BE14-00104B62A16C | Ship | 0x6C4E40 | 0x6C4F10 |

`CreateInstance` 实函 = ctor+0xD0（类工厂对象 vtable slot0）。**11/11 已字节级复核**：`EVIDENCE\factory_createinstance_all11.txt` 显示 11 个地址均有 identical prologue `push esi/edi; mov edi,[esp+0x18]; test edi,edi; ... new(<size>); call <派生ctor>; QueryInterface`（如 Walk `0x6C4790`: `push 0x3C`→`call 0x7C8E17(new)`→`call 0x75AA90(Walk ctor)`）。`[已证]`。
⚠️ 本表**不是**「GUID 与工厂指针在数据段并列」的静态结构，而是**注册函数里的代码序列**（逐个 `new` 工厂 + `RegisterClassObject`）。GUID 本身连续在 `.rdata`；工厂指针由 `0x6BB9A0` 的代码给出。

## 3 · 创建路径（工厂入口）

- **工厂入口 `0x41C250 = LocomotionClass::CreateInstance`**（YRpp `LocomotionClass.h:205-206` 直接 `CALL(0x41C250)`，`[已证]`）。签名 `__thiscall HRESULT CreateInstance(ILocomotion** ppv, const CLSID* rclsid, LPUNKNOWN pUnkOuter, DWORD dwClsContext)`：ecx=out、栈 `[esp+4]=rclsid, +8=pUnkOuter, +0xC=dwClsContext`；`ret 0xC`。
- **分发方式 = 表查找（COM 运行时类注册表），不是 if 比较**：Ghidra 反编译（`ghidra_corroborate.log`）显示 `0x41C250` 直接 `CoCreateInstance(rclsid, pUnkOuter, dwClsContext, IID=&0x817BB0=IID_ILocomotion, ppv)`；若 `dwClsContext & 0x14` 则先 `CoCreateInstance(..., IID=&0x817BC0=IID_IUnknown, &tmp)` → `OleRun` → `QueryInterface(IID_ILocomotion)`。类注册表由 `0x6BB9A0` 在启动时填 11 个 CLSID→类工厂（`0x6C6400`=`CoRegisterClassObject` 包装，78 调用点全在此函数内）。
- 工厂对象 `CreateInstance`（如 Drive `0x6C4010`）`new(0x70)` → `call 0x4AF540`（Drive 构造器）→ `QueryInterface`（槽 0）→ 返回 `ILocomotion*`。
- `IID_ILocomotion = 070F3290-9841-11D1-B709-00A024DDAFD1 @0x817BB0`（`YRpp\Interfaces.h:141` + 字节实测）；`IID_IUnknown @0x817BC0`。
- `13` 个直接 E8 调用 `0x41C250` 的点中，`0x44E02C` 明确 `push 0x7E9A30(Drive CLSID)`。

## 4 · ILocomotion vtable 槽语义（off=4 主接口，前 20 槽 + 关键槽）

顺序来自 YRpp `LocomotionClass.h`（`IPersistStream, ILocomotion` 双继承，off=4=ILocomotion）并用调用点锚定；`[已证]`=有调用点/Ghidra 锚，其余转写为 `[静态推断]`。
**★ = 寻路 / 移动 / 转向 / 停止相关**。每槽给出基类桩地址与 Drive/Walk 实现（完整 12 类 × 50 槽见 `EVIDENCE\slot_anchors.txt`）。

| 槽 | 偏移 | 语义 | 基类桩 | Drive | Walk | 证据级别 |
|---|---|---|---|---|---|---|
| 0 | +0x00 | QueryInterface | 4D0510 | 4B4D90 | 75CC30 | [已证] 工厂 `CreateInstance` 内 `[vt+0]` 调用 |
| 1 | +0x04 | AddRef | 4D0520 | 4B4DA0 | 75CC40 | [静态推断] |
| 2 | +0x08 | Release | 4D0530 | 4B4DB0 | 75CC50 | [已证] `0x41C25D call [vt+8]` |
| 3 | +0x0C | Link_To_Object | 55A710 | 55A710 | 55A710 | [静态推断] YRpp.h:51 |
| 4 ★ | +0x10 | Is_Moving | 55ACD0 | 4AFB80 | 75AB30 | [静态推断] |
| 5 ★ | +0x14 | Destination(pCoord) | 55AC70 | 4AFC90 | 75ABA0 | [静态推断] |
| 6 ★ | +0x18 | Head_To_Coord | 55ACA0 | 4AFCC0 | 75AC00 | [静态推断] |
| 7 ★ | +0x1C | Can_Enter_Cell | 55ABF0 | 55ABF0 | 55ABF0 | [已证] `0x4D9C4B call [vt+0x1C]` |
| 8 | +0x20 | Is_To_Have_Shadow | 55ABE0 | 55ABE0 | 55ABE0 | [静态推断] |
| 9 | +0x24 | Draw_Matrix | 55A730 | 4AFF60 | 55A730 | [静态推断] |
| 10 | +0x28 | Shadow_Matrix | 55A7D0 | 4B0410 | 55A7D0 | [静态推断] |
| 11 | +0x2C | Draw_Point | 55ABD0 | 55ABD0 | 55ABD0 | [静态推断] |
| 12 | +0x30 | Shadow_Point | 55A8C0 | 55A8C0 | 55A8C0 | [静态推断] |
| 13 | +0x34 | Visual_Character | 55ABC0 | 55ABC0 | 55ABC0 | [静态推断] |
| 14 | +0x38 | Z_Adjust | 55ABA0 | 4B4870 | 55ABA0 | [静态推断] |
| 15 | +0x3C | Z_Gradient | 55ABB0 | 4B4880 | 55ABB0 | [静态推断] |
| 16 ★ | +0x40 | **Process**（每帧推进/寻路） | 55AC60 | **4B0500** | **75AC80** | [已证] `0x4DA877 call [vt+0x40]` + 类族全表 |
| 17 ★ | +0x44 | **Move_To(CoordStruct)** | 55AC50 | 4AFD40 | 75ACB0 | [已证] `0x4D562C call [vt+0x44]` |
| 18 ★ | +0x48 | **Stop_Moving** | 55AC40 | 4AFE00 | 75ADA0 | [已证] `0x4D55E0 call [vt+0x48]` |
| 19 ★ | +0x4C | **Do_Turn(DirStruct)** | 55AC30 | 4B0EF0 | 75AE00 | [静态推断] YRpp.h:107 |
| 20 | +0x50 | Unlimbo | 55AC20 | 4B04D0 | 55AC20 | [静态推断] |
| 29 | +0x74 | In_Which_Layer | 4C9150 | 4B4820 | 75C7E0 | [静态推断] |
| 30 ★ | +0x78 | Force_Immediate_Destination | 55AC00 | 55AC00 | 75AE30 | [静态推断] |
| 31 ★ | +0x7C | Force_New_Slope | 55ACE0 | 4AFB40 | 55ACE0 | [静态推断] |
| 32 ★ | +0x80 | Is_Moving_Now | 4B6610 | 4AFC20 | 75AB40 | [静态推断] |
| 39 | +0x9C | Mark_All_Occupation_Bits | 4B6620 | 4B48D0 | 75CA30 | [静态推断] |
| 42 ★ | +0xA8 | Is_Really_Moving_Now | 4B4C50 | 4B4C50 | 75CB20 | [静态推断] |
| 43 ★ | +0xAC | Stop_Movement_Animation | 4B4C90 | 4B4C90 | 75CBC0 | [静态推断] |
| 47–49 | +0xBC..C4 | Get_Track_Number/Index/Speed_Accum | — | — | — | [静态推断] |

其余 21–49 槽（Power_On/Off、Push/Shove、Force_Track、Apparent_Speed、Drawing_Code、Can_Fire、Get_Status、Is_Surfacing、Lock/Unlock、ILocomotion_B8 等）语义见 YRpp.h:108-179，无独立调用点锚 `[静态推断]`。

## 5 · 与 `0x4DA877`（每帧 locomotion 派发）的关系

- **所在函数**：`fn 0x4DA530 = FootClass::AI`（atlas interval 包含：`0x4DA530..0x4DAF08`，size 2520）。`esi=ecx`（0x4DA537，this=FootClass*）。
- **派发槽 = 16**：`0x4DA86E mov eax,[esi+0x674]`（取 loco=`ILocomotion*`）→ `0x4DA874 push eax`（stdcall this 作首栈参）→ `0x4DA875 mov ecx,[eax]`（取 vtable）→ `0x4DA877 call [ecx+0x40]`（slot16=Process）。Ghidra 同结论。
- **`this` = `[FootClass+0x674]`** = 该单位的 `ILocomotion*`（台账 §905-1 已证偏移）；注意是 stdcall 接口（this 在栈），不是 thiscall；`ecx` 此处是 vtable 指针而非 this。
- **每帧执行**：`frame % [[0x8871E0]+0x1808]` 门在 `0x4DA560`，`jne 0x4DA63B` 只跳过 `[0x4DA56E,0x4DA63B)` 的应答/声音块；`0x4DA877 > 0x4DA63B`，**不受节流**（与 R14_COMMON §1 / 台账 §916 一致）。
- 派发实例：Drive→`0x4B0500`、Walk→`0x75AC80`、Fly→`0x4CCB40`、Hover→`0x514310`、Ship→`0x69FC10`、Mech→`0x5B0060`（全表见 §1/`slot_anchors.txt`）。
