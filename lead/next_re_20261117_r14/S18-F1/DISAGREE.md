# S18-F1 · DISAGREE（与线索/台账的分歧）

| # | 线索来源 | 线索说法 | 本卡实测结论 | 分级 / 证据 |
|---|---|---|---|---|
| D1 | 卡正文（§942-3/S17-F1 转述） | 「`TEventClass` 的 Swizzle 字段 `+0x28/+0x30/+0x54`」暗示可能与 `EventClass` 相关，要求核对是否属 EventClass | **否证**：这 3 个偏移属 **TEventClass**（触发器事件类）ctor `0x71F8C0`，RTTI TypeDescriptor `0x8446F8`=`.?AVTEventClass@@`；网络 `EventClass`=111B `NetworkEvent`，无 vptr、无 Swizzle。两者是不同类 | `[已证]` `rtti_dump.txt`/`explore0.txt`/`ghidra_dump.log`；纪律 11（候选假设须自证） |
| D2 | 卡正文「共 476 个登记点」 | 可能读作「TEventClass 有 476 个登记点」 | **更正**：476 是 `Here_I_Am(0x6CF240)` 全镜像调用点总数（所有类），TEventClass 仅 3 处（`+0x28/+0x30/+0x54`） | `[已证]` `field_layout.py`/`callers.txt` |
| D3 | `net_sync_checksum.md` §1.4 | 跳表 `Kind 1..0x2E` 共 45 项 | **精确为 46 项**（idx 0..0x2D = Kind 1..0x2E）；`cmp eax,0x2D; ja default` ⇒ 0..0x2D 共 46 个合法 idx。引擎名表 `0x82091C` 有 47 项（含 EMPTY=0 不进表） | `[已证]` `eventtype_names.txt` 双通道 |
| D4 | `net_sync_checksum.md` §1.2 | FrameInfo Delay 索引写作 `(Timestamp−Delay)&0xFF` | **一致（本卡曾误判后撤回）**：初次从非指令边界 `0x64C6D0` 解码得伪指令 `inc edx`，误报 `(Ts−(Delay+1))&0xFF`。从真边界 `0x64C6AA` 重解：`0x64C6CC mov dl,[event+0xD]`(Delay) → `0x64C6DA sub esi,edx` → `0x64C6DC and 0xFF` ⇒ `(Ts−Delay)&0xFF`，线索正确，撤回误判 | `[已证]` `EVIDENCE\edx_trace.txt`/`EVIDENCE\decode_correction.txt`；纪律 7/13 |
| D5 | `net_sync_checksum.md` §3.2 / `MP_SAFETY_REVIEW` | 帧 CRC 含「0x8A0370 簇」与「0x8A03E8 簇」两个独立补充簇 | 反汇编显示这是**同一个 5 元素 `LayerClass[5]` 数组**（`ebp=0x8A0370`, `+=0x18`, `cmp 0x8A03E8`, `jl`）——是单一外层循环遍历 5 层，不是两个独立簇 | `[已证]` `crc_detail.txt`；与 R14_COMMON §4.7 一致 |
| D6 | `net_sync_checksum.md` §1.4 名表 / 本卡引擎名表 | 线索未列 `0x2E` 名 | 引擎自身名表 `0x82091C` 给出 `0x2E=ABANDON_ALL`（@`0x8209DC`），跳表 idx `0x2D`→`0x4C7188`（`push 1`）存在 | `[已证]` `eventtype_names.txt` |
| D7 | 卡片背景「EventClass 是命令/事件序列化单元」 | 称事件类是 `EventClass` | 本镜像 RTTI **无** `.?AVEventClass@@`（仅容器 `VectorClass<EventClass*>`/`DynamicVectorClass<EventClass*>`，`0x7EFE04/0x7EFE24`）。网络事件是 POD 结构 `NetworkEvent`（YRpp）/ typedef `EventClass`（ares），无虚表；`TEventClass` 才是有虚表的类。命名按语境区分，字节实体唯一 | `[已证]` `find_eventclass.txt`/`rtti_scan.txt` |

## 未与台账冲突（一致确认）

- `CurrentFrame@0xA8ED84` 唯一 inc `0x55DE81`、`MainLogicFrame 0x55D360`、UI 泵 `0x48C8B0` 在帧逻辑之后——与 `net_sync_checksum.md` §1.1、R14_COMMON §5 一致。
- 执行器 `0x4C6CB0`、跳表 `0x4C8114`、帧 CRC `0x64DAB0`、`LatestFramesCRC@0xB04474`、desync `0x64CC61`——地址全部复算一致。
