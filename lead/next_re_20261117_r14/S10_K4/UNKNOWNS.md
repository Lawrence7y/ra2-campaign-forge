# S10-K4 · UNKNOWNS

| # | 未知 / 未升级项 | 状态 | 已尝试与下一步 |
|---|---|---|---|
| U1 | S10 距 50% proved 门槛仍远 | [已证] | 盘上 88/526；本卡 19 行合入后 107/526（20.3422%），门槛 263，仍差 156。若另计 K3 未重交的 4 行 GetSize/WhatAmI 则为 111/526、差 152；须由合并员避免重复。 |
| U2 | TimerStruct 第二字段 `[edi+0xCC]`／`[esi+4]` 的精确含义 | [未证] | 已证 `[edi+0xC8]=StartTime=CurrentFrame`、`[edi+0xD0]=TimeLeft=eax(return)`，`[esi+4]` 取 `[esp+8]`；本卡只需 TimeLeft 即可定语义，未把第二字段猜成已证。下一步追 `[esp+8]` 全部写入点。 |
| U3 | 005B3970 序列化/保存方法名 | [静态推断] | 逐字节见 `call 0x5F6250` + 多次 `call 0x4A1D50` 写字段/+timer remaining，直接 caller 0065AB10 亦为 stream 写出；但 Save/Serialize 名无镜像内字符串或独立调用者符号绑定，禁止仅按槽号升名。 |
| U4 | 005B3A60 析构方法名 | [静态推断] | 写 4 个 vptr（007EDCC0/7EDCA4/7EDC9C/7EDC94）、call 0x5F3B80、条件 call 0x7C8B3D、ret 4，析构形；方法名无第二独立通道。 |
| U5 | 005B3A10 谓词语义 | [未证] | 仅 `mov edx,[ecx+0xB0]; xor eax,eax; cmp edx,-1; setne al; ret`；无行为级命名证据。 |
| U6 | 005F5E80 继承字段例程 | [未证] | ObjectClass 字段加载/清零形态，不是 Mission_* 派发；未升级。 |
| U7 | 0070DD90 常量返回反例 | [未证] | `B8 01 00 00 00 C3`；imm=1 对应 AbstractType Unit，但 RTTI 是 AircraftClass，且非 off0 slot11/GetSize-closed slot12；语义冲突，保留 [静态推断]。 |
| U8 | 15 个 sub_ 占位行 | [未证] | 004B4890/004C9300/004C9680/004DB0D0/004DD890/004E0E80/006B7010/00703B10/00703E70/0070DC60/0070DCE0/0070DCF0/007107E0/00746EA0/00754BE0：无 RTTI vtable anchor，无可复算方法名。 |
| U9 | 63 个字符串命中非证行 | [未证] | 均为共享尾引用（EVA_UnitLost/Sold、EVA_StructureGarrisoned、BTN-PLUS/MINS、rule keys、Infantry/Techno/Unit.CPP assert、Tip:*），只能证明邻近共有 callee，不能唯一绑定本行虚方法名；未升级。 |
| U10 | 005B2E10 仍叫 Mission_DefaultHandler | [静态推断] | 盘上已 [已证] 且不在 K3 19 行集合；按 RTTI/派发它属 slot129（Sleep/QMove/Attack Move 共用），真名须另卡处理，本卡不越界改已入账行。 |
| U11 | 005B3060 方法名 | [已证] 语义 / [未证] 符号 | 行为是 UpdateTimer（Timer 门 + dispatch + 结果写回），但镜像无 `UpdateTimer` 符号串；语义按行为命名，不把它当字符串证据。 |

## 复算入口
- `work/baseline_recompute.py`、`work/prove_corrections.py`、`work/validate_delta.py`、`work/task3_exhaustive.py`。
- 失败关闭清单：`EVIDENCE/task3_exhaustive.txt`、`EVIDENCE/scan_nonproved_strings.txt`。
