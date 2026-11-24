# S18-K2 · PROGRESS（≤60 行）

> 卡号 S18-K2｜纯只读静态｜通道：自写 pefile+capstone 5.0.7 `skipdata=True`（`work/peutil.py`，**不依赖 atlas**）+ 自建全镜像 RTTI 索引（988 TD）+ CRC 表逐项复算。三腿独立字节自证，不冒称"第二解码器通道"。
> 目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（全串实测一致），4,825,360 B，ImageBase `0x400000`。
> 分级：`[已证]`=本卡字节级独立复算；`[静态推断]`=单通道逻辑闭合；`[未证]`=需真机/未穷举。

## 核心数字（给审计）

| # | 数字 | 本卡值 | 复算方法 |
|---|---|---|---|
| N1 | S18 atlas 分母 / named / proved | **659 / 496(75.27%) / 53(8.04%)**；50% 差 **277** | `python work\t1_targets.py`（coverage∩atlas 实算）；PANEL.md L50 同值 |
| N2 | 111 B / 46 项 / CRC 第4集合 | 111B ✅ / 46 EventType ✅ / **HouseClass** ✅ | `EVIDENCE/alloc_and_desync.txt`(push 0x6f,17处)、`eventtype_full_table.txt`(46)、`rtti_container_types.txt`(House TD) |
| N3 | 两套 CRC | 帧CRC `0x64DAB0`=**加法哈希非CRC32**；对象CRC `0x4A1C10`=**标准CRC32表0x81F7B4(256/256匹配,poly 0xEDB88320)** | `EVIDENCE/crc_region_raw*.txt` / `checksummer_probe.txt` |

## 结论表

| 项 | 结论 | 等级 | 证据路径 |
|---|---|---|---|
| 「EventClass」RTTI 定名 | 无 `.?AVEventClass@@` 自身 TD（988 TD 全扫）；仅指针容器 TD `Vector/DynamicVector<EventClass*>`；网络事件是 **111B POD 非多态**。TEventClass(`0x8446F8`) 是触发器类，无关 | `[已证]` | `EVIDENCE/rtti_event_scan.txt` |
| 事件记录布局 | 8 字段 +0 Kind/+1 执行标志/+2 HouseIndex/+3 Timestamp/+7 Checksum/+0xB Count/+0xD Delay/+0xE.. 载荷；写序 House→Kind→载荷→Timestamp(末)；写者/读者双点 | `[已证]` | `EVIDENCE/fillevent_place.txt`/`dispatch_entry.txt`/`execute_gate.txt` |
| 事件队列容器 | **非 DynamicVectorClass**：QueuedEvents `0xA802D4`=128×111B 裸环形数组(Count`0xA802C8`/游标`0xA802D0`)；网络环 `0x8B4204`=0x4000×111B；MegaMission `0xA83EDC` | `[已证]` | `EVIDENCE/enqueue_idiom.txt`；LAYOUT.md §3 |
| 入队/溢出 | 无单一 Add（内联惯用式）；`new(0x6F)`@`0x637C85`/`0x63862C`；**溢出 Count≥0x80 静默丢弃**(`0x48CA48 jge`) | `[已证]` | `EVIDENCE/enqueue_idiom.txt`/`alloc_and_desync.txt` |
| 执行链 | `0x4C6CB0` thiscall ecx=event，`dec Kind;cmp 0x2D;jmp [eax*4+0x4C8114]` 46 项；三门 HouseIndex/Ts≤CF/+1&1；`or [event+1],1` 后置 | `[已证]` | `EVIDENCE/dispatch_entry.txt`/`eventtype_full_table.txt`/`execute_gate.txt` |
| 帧 CRC 本体 | `0x64DAB0`→`0xAC51FC`，初值0，`acc=rol1(acc)+term`（**非标准 CRC32**）；6 集合(第4=House)+1 RNG；量化 ×0x66666667=÷10、坐标>>8拼字节 | `[已证]` | `EVIDENCE/crc_region_raw*.txt`/`rtti_container_types.txt` |
| desync 比对 | `idx=(Ts−Delay)&0xFF`；`LatestFramesCRC[idx]@0xB04474` vs `event+7`；`jne 0x64CC61` 写 SYNC*.TXT+弹 TXT_OUT_OF_SYNC | `[已证]` | `EVIDENCE/alloc_and_desync.txt` |
| 对象 CRC / Checksummer | `0x4A1C10`=**标准 CRC32**：表 `0x81F7B4`(poly 0xEDB88320, 256/256 匹配)、首尾 not；v[13] `CalculateChecksum` 进档口；**存档/诊断校验** | `[已证]` | `EVIDENCE/checksummer_probe.txt` |
| 同步 vs 存档判定 | 帧CRC=**同步校验(防不同步)**(每帧×2 `0x64731C`/`0x647684`，失败弹 STOP)；对象CRC=**存档/诊断校验**(仅 SYNC*.TXT) | `[已证]` | `EVIDENCE/crc_callers.txt`；CRC.md §1 |
| T4 同步函数(调用点级) | `Waiting for 'GO'` xref `0x5BB031`；`Timeout! %d ticks` xref `0x5B6608`/`0x5BA528`；`Frame sync stalls` xref `0x48E215`/`0x64E18F`/`0x6519EA`；协议细节不展开 | 调用点`[已证]`/协议`[未证]` | `EVIDENCE/sync_string_xrefs.txt` |

## 46 项落地（CRC.md §3）
- **46 个 EventType 逐项落地**（handler+事件字段偏移/宽度，Kind 1..0x2E）✅；**帧 CRC 字段贡献表**（对象/字段/宽度/term 位）✅；**标准 CRC32 本体+表地址** ✅。卡面「46 项」与 CRC 字段的口径混淆已记 DISAGREE D2，未凑数。

## delta
- `coverage_delta.tsv` 4 行（S18 已存在函数的 grade 升级：`0x64DAB0`/`0x64C380`/`0x4A1C10`/`0x4C93D0` → `[已证]`，字节支撑）；未新增函数入口（call 站点不冒充入口）；未改 `COVERAGE\coverage.tsv`。

## 未闭环
见 `UNKNOWNS.md`（U1 分母、U2 46项口径、U3 无RTTI TD、U4 helper语义、U5 term位序、U6 331 Add 未逐类、U7/U8 联机协议）。
