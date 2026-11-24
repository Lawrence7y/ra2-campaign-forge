# S17-K6 · PROGRESS（≤50 行）

> 卡号 S17-K6｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（现场复算一致）｜Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26｜未用 Ghidra。
> 时点 2026-11-18T08:1x+08:00｜写域仅 `lead\next_re_20261117_r14\S17_K6\`｜未写台账/游戏文件/未 git commit。

## 基线与结论
- 盘上复算：S17∩atlas=102，named(S)=92（90.20%），proved=54（52.94%），门槛 92，余量 0；与卡面一致。
- 交 **2 行 delta**：`0043AE50→MemoryBuffer::Clear`、`004355B0→ColorStruct::ColorStruct`，均 `[静态推断]`（POD 源码级名，不声称 RTTI 类归属）。K6 单独并入后 named=**94/102=92.16%**，余量 **+2**；proved 仍 54。K5+K6 且保留 4068E0：95/102=93.14%。
- 若把 `004068E0` 移出 S17：按盘上真值应为 **92/101**（原 92 named 不含该行），K6 后 **94/101=93.07%**，门槛 91，余量 +3；卡面写的 91/101 与盘上不一致，见 DISAGREE D1。

## 10 条残行逐条取证（换通道：RTTI 调用者 + POD 源声明 + 全镜像串/vt 排除）
| entry | 取证过程 | 判定 |
|---|---|---|
| `004068E0` | 单 `C3`；K5 的 body+caller 同属通道 A，审计退 `[静态推断]`；`docs/re/audio_input_hotspots.md:458` 另有 `WWDebug_Printf`；调用者跨 22 子系统，S17 仅 0.9%。 | **不重交**；归属待 D-37。 |
| `0040E340` | 75B 双向链摘/挂；dword refs=0，无 vptr/RTTI/串；33 调用点跨 S04/S07/S09/S21/S22。 | 不可定：通用 `GenericNode` 链接行为，无唯一类锚。 |
| `00427940` | 315B；镜像串仅 `TEM`(0x7E1BC6) / `.SHP`(0x81834C)；调 LoadFile；调用者 S09/S21，非 S17。 | 不可定：无 SAVE/.SAV/.SED/SWIZZLE 串，类/域锚缺失。 |
| `0042E410` | 32B 四 dword setter `[0..0xC]`；dword refs=0；25 调用点跨 S06/S07/S09/S20/S22。 | 不可定：矩形/POD 构造候选但类型无区分力。 |
| `00433CF0` | 437B UTF-16 逐字 + `jmp [0x433EA8]` 宽度/折行表；27 调用点集中 UI/Drawing。 | 不可定：文本 walker，非存档；无 RTTI/唯一域锚。 |
| `004355B0` | 25B 全 ret：3 个 byte 栈参写 `[this+0..2]`，`ret 0xC`，eax=this；`668C51`(RulesClass::Read_File，盘上[已证]) 以 0,0,0 构造局部并传 eax；YRpp `BasicStructures.h:10,38` 的 ColorStruct(BYTE,BYTE,BYTE)/R,G,B 同形。 | **可定** `ColorStruct::ColorStruct`；结构名来自源声明，非 RTTI 类。 |
| `0043AE50` | 40B 全 ret：`[+8]` 为真则 `CRT::_delete([0])`，再清 `[0]/[4]/[8]`；RTTI TD 证 `004019A0`∈`.?AVCCFileClass@@`，`4019A3 lea ecx,[esi+0x58]; 4019B3 call`；YRpp `CCFileClass.h:213` Buffer=`MemoryBuffer`、`YRAllocator.h:8,63` 同布局/Clear。BufferStraw/BufferPipe RTTI 调用者以 `this+0xC` 同形。 | **可定** `MemoryBuffer::Clear`；POD 源码级名，非 RTTI 类。 |
| `0049F740` | 审计已证 COPYPROTECTION launcher IPC/`MapViewOfFileEx`，非 S17。 | 不碰。 |
| `0049F8B0` | 审计已证 COPYPROTECTION shutdown/`WChat\SysID` 注册表清理，非 S17。 | 不碰。 |
| `00773450` | RTTI `.?AVWebBrowser@@`，审计已证非 S17。 | 不碰。 |

## 通道与纪律
- 全镜像 RTTI/vt 普查：1212 张表；六个候选残行 dword refs=0 ⇒ 均非虚表槽，不能靠 slot 定名。
- FileClass 族 vt：`007E3A28`(BufferIOFileClass)/`007E1664`(CDFileClass)/`007E16AC`(CCFileClass) 的槽值均不含六候选；`00431B80` 是析构链 helper，不是残行。
- 镜像串路：SAVE/LOAD/GAME/.SAV/.SED/MAP/SWIZZLE 引用未落到六个残行体内；唯一命中是 00427940 的 TEM/.SHP（非存档）。
- SwizzleManagerClass vt（`007F4104`，9 槽）全为 006CFxxx，六候选 0 命中；调用者语义反推路中六候选均无 `[已证] S17` 直接调用者。
- 环①：每条引用地址均在对应体内真出现；环④：引用调用点均真存在并回盘查 grade；查冲突按地址+新名双路（见 `EVIDENCE/conflict_address_scan.txt`）。
- 新名不是 `sub_`/`slotN`/占位名；grade 保守取 `[静态推断]`，不把 POD 源名冒充 RTTI TD。

## 证据入口
- 基线/复算：`EVIDENCE/baseline_recompute.txt`、`EVIDENCE/final_recompute.txt`。
- 命名证据：`EVIDENCE/naming_proof.txt`、`EVIDENCE/caller_context.txt`、`EVIDENCE/rtti_vtables_relevant.txt`。
- 排除证据：`EVIDENCE/targets_recon.txt`、`EVIDENCE/conflict_address_scan.txt`；脚本在 `work/`。
