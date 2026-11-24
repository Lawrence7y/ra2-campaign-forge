# S18-F1 · UNKNOWNS（未决 / 需真机）

> 定义：`[静态推断]`=单通道逻辑闭合但未双证；`[未证]`=静态不可定，交后续真机卡；本卡严禁联网/联机。

| # | 项 | 档 | 说明 / 交给谁 |
|---|---|---|---|
| U1 | `0xA8022C/0xA80238` 集合的类归属（Aircraft vs House） | `[静态推断→未证]` | 帧 CRC 把 `0xA8022C` 当 Items + `byte obj+0x241`；执行器 `0x4C6CB0` 也把 `0xA8022C` 当 House 指针数组（`mov edi,[ecx+ebx*4]`, ebx=HouseIndex）。两种读法并存；需真机对该全局做 RTTI/对象判定。影响：帧 CRC 到底哈希了飞机还是 House 状态 |
| U2 | 对象级 `CalculateChecksum`（v[13]）逐类覆盖 42 类目 | `[未证]` | 本卡仅验证 `AbstractClass::CalculateChecksum 0x410410`（写 `+0x10` dword、`+0x20` byte）与 Checksummer 簇入口；线索文档 `net_sync_checksum.md` §3.1 称 42 类目（含 Event/Particle/House），未逐类复核。交后续 S17/S18 深卡 |
| U3 | `0xA8E30C` 宽限阈值（帧 CRC 报告门）全局写者 | `[未证]` | 静态未找到写点；需真机观察何时启用 CRC 比对/报告。承接 `net_sync_checksum.md` §7.3 |
| U4 | `CurrentFrameCRC@0xAC51FC` 14 个写点中哪一个是每帧最终提交 | `[静态推断]` | 已见 `0x64DB4A/0x64DC0E/…` 多写；真机逐帧断点可定唯一提交语句。累加式与终值已证，提交点顺序未逐帧验证 |
| U5 | 每帧固定吃 1 次 RNG 是否与联机强契约 | `[静态推断]` | 静态见 `0x64DE3F call 0x65C780`；1 次/帧为线索文档结论，真机双端对拍 RNG 消耗计数未做（本卡禁联网） |
| U6 | 「回滚机制」是否存在独立实现 | `[静态推断→未证]` | 静态只找到**时间戳重写/挂起**机制（`0x64C3CC` 改写迟到命令 Timestamp 至 `[0xA8B1DC,0xA8B1F8)` 窗、`Ts>CurrentFrame` 挂起不执行、`0x4C7F35 LATENCYFUDGE`）。未发现状态回滚（undo）代码；按纪律 12 已查等价形式（挂起+追帧=事实上的延迟补偿），但「真回滚」是否存在需真机 |
| U7 | `EventClass` 字段名权威来源分歧（YRpp 8 字段 vs ares 5 字段 union） | `[已证布局 / 命名未证]` | 字节布局 111B、写点偏移已证；顶层字段“个数”依视角不同。核心数字取 8（YRpp 展开），ares union 为 5。真机符号（PDB/导出名）可定权威命名 |
| U8 | ~~(no-op 目标 0x4C8109 是否真空)~~ | **[已证·已闭环]** | 入口到 ret 逐条打完：`pop edi/esi/ebp/ebx; add esp,0x370; ret`（`EVIDENCE\discipline_audit.txt`）。真空成立，不再列未决 |
| U9 | 帧 CRC 中 `5×LayerClass` 的 Items 基址 `ebp-0xC` 序列 | `[静态推断]` | `ebp` 从 `0x8A0370` 步进至 `0x8A03E8`（5 次），Items=`ebp-0xC`；与 R14_COMMON §4.7 `[5]LayerClass@0x8A0360` 一致但本卡未逐一 dump 5 个 Count 值。真机可读 |
