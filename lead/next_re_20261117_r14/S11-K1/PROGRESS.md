# S11-K1 · PROGRESS（Locomotor 类族 / CLSID / vtable）

> 目标 `gamemd.exe`（SHA 73201CC0…F67476）。静态卡，无真机。完成 2026-11-17。
> 交付：`LAYOUT.md`（类族/CLSID/槽语义全表）· 本文件 · `UNKNOWNS.md` · `DISAGREE.md` · `EVIDENCE\` · `work\` · `coverage_delta.tsv`

## 结论表

| # | 结论 | 级别 | 证据 |
|---|---|---|---|
| 1 | Locomotor 类族 **12 类**（基类 LocomotionClass + 11 派生），类名全部 RTTI TD 实测 | [已证] | `EVIDENCE\ch1_rtti_enum.txt`、`verify_final.txt` |
| 2 | 每类有 ILocomotion 主接口 vtable（`off=4`，50 槽）+ IPersistStream（`off=0`，10 槽）；6 类另有 `off=24`（8 槽） | [已证] | `ch1_rtti_enum.txt`、`slot_anchors.txt` |
| 3 | CLSID **11 项**，`.rdata 0x7E9A30..0x7E9AE0` 每项 16B GUID；映射为代码序列（注册函数 `0x6BB9A0`）非静态并列数据 | [已证] | `clsid_scan.txt`、`disasm_6BD130.txt`、`verify_final.txt` |
| 4 | 工厂入口 **`0x41C250 = LocomotionClass::CreateInstance`**，调用 ole32!CoCreateInstance + 可选 OleRun | [已证] | `disasm_41C250.txt`、`ghidra_corroborate.log`、`callscan.py` |
| 5 | 分发方式 = **COM 类注册表查找**（`0x6C6400`=CoRegisterClassObject，78 调用点全在 `0x6BB9A0`），非 if 比较 | [已证] | `callscan.py`、`disasm_6BD130.txt` |
| 6 | `0x4DA877` = `[FootClass+0x674]->vtable[0x40/4=16]` = **slot16 Process**；`this`=loco(ILocomotion*)，stdcall 栈传 | [已证] | `slot_anchors.txt`、`ghidra_corroborate.log` |
| 7 | `0x4DA877` 在 `fn 0x4DA530`（FootClass::AI），`frame % N` 门只跳过 `[0x4DA56E,0x4DA63B)`，派发每帧执行 | [已证] | `slot_anchors.txt`（prologue+门控） |
| 8 | slot 锚：7=Can_Enter_Cell(`0x4D9C4B`)、16=Process(`0x4DA877`)、17=Move_To(`0x4D562C`)、18=Stop_Moving(`0x4D55E0`) | [已证] | `slot_anchors.txt` |
| 9 | `IID_ILocomotion@0x817BB0=070F3290-9841-11D1-B709-00A024DDAFD1`、`IID_IUnknown@0x817BC0` | [已证] | `ghidra_corroborate.log`、`YRpp\Interfaces.h:141` |
| 10 | 类工厂 ctor 11 个 `0x6C3F40..0x6C4E40`，`CreateInstance`=ctor+0xD0（如 Walk `0x6C4790` new 0x3C→`0x75AA90` ctor）；11/11 prologue 字节级复核 | [已证] | `disasm_6BD130.txt`、`verify_final.txt`、`factory_createinstance_all11.txt` |

## 分级口径
`[已证]`：字节级 RTTI/CLSID 扫描 + 独立调用点扫描（+ Ghidra 反编译第三通道）三处收敛。
`[静态推断]`：YRpp 头顺序/同构推导，无独立调用点。`[未证]`：见 UNKNOWNS.md。
**不虚高**：槽 21–49 无调用点者标 `[静态推断]`；类工厂 `CreateInstance` 11/11 已有字节级 prologue+new+ctor 复核，标 `[已证]`。

## 核心数字（3 个）+ 复算方法

1. **类数 12**：`python work\verify_final.py`。CH1=扫全节 `.?AV*LocomotionClass@@\0` RTTI 名→12 TD；CH2=`0x6BB9A0` 内 11 个 `push <CLSID>` + 1 个无 CLSID 基类=12。两通道不同源（数据元数据 vs 代码模式）。
2. **CLSID 项数 11**：同上脚本 B 段；`work\clsid_scan.py` 独立扫 `.rdata 0x7E9A20..0x7E9B00` 得 11 个连续 16B GUID（0x7E9A30..0x7E9AD0）。
3. **工厂 0x41C250 / 槽 16**：`work\callscan.py`（13 个 E8 精确 rel32 目标，非启发式）；`work\slot_anchors.py`（`call [ecx+0x40]` → 0x40/4=16）+ Ghidra 反编译对照。

## 双通道声明（纪律 1）
- **通道 A（不依赖 atlas）**：`pefile` 字节级 RTTI/CLSID/GUID 扫描 + E8 rel32 精确目标扫描（`ch1_rtti.py`/`clsid_scan.py`/`callscan.py`）。
- **通道 B（不同源）**：Ghidra 12.1.4 `-noanalysis` 反编译（`S11K1_Corroborate.java`，用完已删副本）+ 源码 YRpp `LocomotionClass.h/Interfaces.h` 对照。
- 两通道独立实现、独立工具，非「写两份互读」。`atlas` 仅用于 §5 函数区间归属（纪律 14），非发现通道。

## 约束遵守
capstone `skipdata=True`（`pehelp.py`）；`boundary_check` 超限返 `'unknown'`（非 False）；寄存器回溯 ecx 来源（`0x4DA875 ecx=[eax]`=vtable，`this`=`[esi+0x674]` 栈传）；类名只认 TD；无 `entry_at_or_before` 归属；未改游戏文件/台账；Ghidra 副本已删。
