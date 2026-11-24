# S18-F1 · PROGRESS（≤60 行）

> 卡号 S18-F1｜静态只读｜双通道：① capstone 5.0.7 `skipdata=True`+pefile 自写 PE（不依赖 atlas）；② Ghidra 12.1.4 SLEIGH `-noanalysis`（`EVIDENCE\ghidra_dump.log`）。两通道逐指令一致。
> 目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（实测全串 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`），4,825,360 B，ImageBase `0x400000`。
> 分级：`[已证]`=双通道字节/反汇编一致或引擎自身数据表直读；`[静态推断]`=单通道逻辑闭合；`[未证]`=需真机。

## 核心数字（给审计）

| # | 数字 | 值 | 复算方法（`python work\...`） |
|---|---|---|---|
| N1 | 网络事件结构字段数 | **8**（Kind+0/Unused+1/HouseIndex+2/Timestamp+3/Checksum+7/CommandCount+0xB/Delay+0xD/ExtraData+0xE，共 111B）；ares union 视图为 5 字段 | `field_layout.py`：11 个 FillEvent 体写点偏移集合 {+2,+3,+7,+9,+0xB,+0xC,+0xD,+0xF,+0x13,+0x15}+Kind(`mov [esi],bl`)；`YRpp\NetworkEvents.h` |
| N2 | EventType 跳表项数 | **46**（Kind 1..0x2E，idx 0..0x2D；引擎名表 0x82091C 有 47 名含 EMPTY=0） | `eventtype_names.py`：跳表 `0x4C8114+4*i` i=0..45 全 46 目标 `boundary=True`；两通道均读 `cmp eax,0x2D / ja default` |
| N3 | 帧 CRC 遍历对象数 | **6 个对象集合 + 1 次 RNG**（Infantry/Unit/Building/Aircraft/5×LayerClass/LogicClass + `Random()`） | `crc_detail.txt`：Count/Items 对 `0xA83DF8/EC`、`0x8B4118/0C`、`0xA8EB50/44`、`0xA80238/2C`、`0x8A0370(-0xC)`×5、`0x87F788/7C`；RNG `0x64DE3F` |
| N4 | 入队 / 执行入口 | 入队 `0xA802D4`（内联惯用式，无单一函数）；执行 `0x4C6CB0`（队列消费 `0x64C380`→2 处 call） | `enqueue_add.txt` / `callers.txt`（`Exec_dispatch` 2 调用者 `0x64C911/0x64CC0A`） |

## 结论表

| 项 | 结论 | 等级 | 证据路径 |
|---|---|---|---|
| 「EventClass」身份 | 网络语境=111B 结构 `NetworkEvent`（YRpp）/ `EventClass`（ares mod）；**非** RTTI 的 `TEventClass`（触发器事件） | `[已证]` | `find_eventclass.txt`；`YRpp\NetworkEvents.h`；RTTI `.?AVTEventClass@@` @`0x844700` |
| Swizzle 偏移归属 | `+0x28/+0x30/+0x54` 的 3 个 `Here_I_Am` 登记点属 **TEventClass ctor `0x71F8C0`**（vptr 全指向 TD `0x8446F8`=TEventClass），**不属网络 EventClass** | `[已证]` | `explore0.txt`/`rtti_dump.txt`/`ghidra_dump.log`；`rtti_decode.py` |
| 476 登记点 | `Here_I_Am(0x6CF240)` 全镜像调用点 = **476**（含全部类）；TEventClass 仅贡献其中 3 处 | `[已证]` | `field_layout.py`/`callers.txt`（两通道扫描一致） |
| 字段写序 | HouseIndex(+2)→Kind(+0, `mov [esi],bl`)→Payload→Timestamp(+3, 末写, `CurrentFrame` 直引)；错误支 HouseIndex=0xFF/Kind=0 | `[已证]` | `field_layout.txt`；`ghidra_dump.log`(FillEvent_Place 全) |
| 入队容器 | `QueuedEvents@0xA802D4` = 128×111B；Count `0xA802C8`(<0x80)、写游标 `0xA802D0`(&0x7F)、时戳 `0xA83A54` | `[已证]` | `enqueue_add.txt`（`0x48CA48..9C` 等复数同构） |
| 网络收包环 | `Queue@0x8B4204` = 0x4000×111B（slot&0x3FFF）；Count `0x8B41F8` / 读游标 `0x8B41FC` | `[已证]` | `explore0.txt`/`enqueue_trace.txt` |
| 帧同步位置 | `MainLogicFrame 0x55D360` 尾 `0x55DE40 call 0x647260`（唯一）；`CurrentFrame++` 在 `0x55DE73..81`（同步**之后**）；UI 泵 `0x48C8B0` 在 MainLogicFrame **之后**（`0x48CE9C`）⇒ 本地命令 ≥1 帧延迟 | `[已证]` | `crc_frame.txt`/`final_verify.txt` |
| 执行门控 | `Ts<=CurrentFrame`（`0x64C563 cmp; jl skip`）∧ `[event+1]&1==0`（`0x64C56B`）∧ HouseIndex 匹配（`0x64C549`）；执行后 `or [event+1],1`（`0x64CAC7`） | `[已证]` | `crc_frame.txt`/`execflag.txt` |
| 分派入口 | `0x4C6CB0`（thiscall ecx=event）；`dec Kind; cmp 0x2D; ja 0x4C8109; jmp [eax*4+0x4C8114]` | `[已证]` | `explore0.txt`/`ghidra_dump.log` |
| 跳表项 | 46 项 Kind 1..0x2E；0x1C FRAMEINFO/0x19 FRAMESYNC/0x1A MESSAGE/0x25 MEGAFRAMEINFO/0x26 PACKETTIMING → no-op `0x4C8109`；3 项 PLAN* → `0x4C6CDE` | `[已证]` | `eventtype_names.txt` |
| CRC 算法 | `acc=acc*2+sign(acc)+term`（`0x64DB3B..41`），量化 ×`0x66666667`>>2=÷10、坐标 >>7 拼 32B；结果 `0xAC51FC` | `[已证]` | `crc_detail.txt` |
| CRC 与帧号 | 结果存 `LatestFramesCRC[CurrentFrame&0xFF]@0xB04474`；比对 `idx=(Ts-Delay)&0xFF`（`0x64C6CC mov dl,[event+0xD]`→`0x64C6DA sub; and 0xFF`，边界对齐解码）；不等→`0x64CC61` SYNC 报告 | `[已证]` | `edx_trace.txt`/`decode_correction.txt`（一次误判已撤回） |
| 两套校验和 | 帧CRC（逐帧、轻、联机判据）+ 对象 Checksum（`*::CalculateChecksum v[13]`→`Checksummer 0x4A1C10` 簇，仅 SYNC*.TXT/存档） | `[静态推断]` | `crc_detail.txt`（`0x410410` 写点）；`docs\re\net_sync_checksum.md` §3（线索） |
| 延迟/回滚 | Build_FrameInfo `0x649CA0`：Kind=0x1C、Checksum=CRC、Delay=参、Timestamp=`mode==2` 时对齐 `FrameSendRate(0xA8B554)` 否则 `CurrentFrame+参`；迟到命令时间戳重写窗 `[0xA8B1DC,0xA8B1F8)`（`0x64C3CC`）；LATENCYFUDGE→`0x4C7F35` | `[静态推断]` | `enqueue_add.txt`/`explore0.txt`；`net_sync_fix_spec.md` §1.2（线索） |

## 纪律落实 / 未闭环

- 双通道不同源：通道 1 自写 pefile+capstone；通道 2 Ghidra SLEIGH，均不依赖 `function_atlas.tsv`。atlas 未用于任何定论。
- `skipdata=True` 全程；`boundary_check` 超限返 `'unknown'`（`work\pe_util.py`）；跳表 46 目标全 `boundary=True`（无 False 误判）。
- 寄存器/操作数溯源：`0x4C6CB0` ecx=event（`mov esi,ecx`）、HouseIndex `movsx [esi+2]`、Kind `mov al,[esi]` 全回溯。栈参数（纪律 6）：Build_FrameInfo `[esp+N]` 集合 {0x10,0x18,0x1C,0x20,0x24,0x28,0x34,0x38}，max=**0x38**（=CommandCount 入参；prologue `sub esp,0x1C`+4 push 使原 arg 区在 `[esp+0x34]` 起），`mov ecx,[esp+0x34]`=Delay 入参；FillEvent_Place 集合 {0xC,0x14,0x18,0x1C,0x20}，max=0x20。证据 `EVIDENCE\discipline_audit.txt`。
- 字段写点穷举（纪律 15）：FillEvent_Place/SellCell 全部内存写逐条打印（含无偏移 `mov [esi],bl` 的 Kind、op1 内存 `mov dx,[eax]`），偏移集合完整，无遗漏。no-op `0x4C8109` 入口到 ret 逐条打完（`pop edi/esi/ebp/ebx; add esp,0x370; ret`），确认真空。同上证据。
- 站点归属用区间包含；「全 True」有鉴别力（46 目标逐一验证、5 no-op 目标显式列出）。
- 未闭环：`0xAC51FC` 精确写者全表（14 写需真机逐帧确认提交点）；对象 Checksum 42 类目逐类验证（本卡未穷举）；`0xA8E30C` 宽限阈值写者；Aircraft 集合 `0xA8022C` 类归属（Aircraft vs House）二义。见 `UNKNOWNS.md`。
