# S12-K2 UNKNOWNS

| # | 未证项 | 为什么未证 | 下一步 |
|---|---|---|---|
| U1 | `0x47C620` 的 arg1=`[esp+0x1C]`、arg3=`[esp+0x24]` 的逐类语义 | 只证了取值来源与比较用途（arg1 与 -1/浮点表比较；arg3 与 `[vptr+0x3C]` 返回值比较），未追到调用者实参名 | 真机或跨函数数据流逐调用点回溯 10 个 caller |
| U2 | WhatAmI==2/6/0x24 到 RTTI 名的**字节级一一映射** | 6/0x24/2 与 Building/Terrain/Unit 的对应来自 `docs/re` 勘误表；本卡只独立证了 vtable slot11 返回常量谱系，未逐类反查 slot11→TD | 对本镜像四类 vtable 的 slot11 函数做 `mov eax,imm; ret` 逐字节闭环 |
| U3 | `0x4151E0` 的类名 | RTTI 候选 `vt 0x7E23BC → COL 0x4144B0 → TD 0x8B5655C0` 越界，读不到 ⇒ fail-closed，不乱猜 | 换其它 vtable/CHD 通道或从调用者反推 |
| U4 | `0x47C620` 中 `cell+0x124`（`test ...,0x3F`）的字段语义 | 只有读点，没定位该类自己的写点；按纪律 4 不定语义 | 扫 `byte [reg+0x124]` 全部写点，限定 CellClass 自有函数 |
| U5 | `arg2+0x16BF/0x16BE/0x16B7/0xE58/0xE54/0xCCE` 的 owner 类 | 本函数在多个 caller 中 arg2 来源不同（building/techno/cell 上下文），未逐点闭合 RTTI | 逐 caller 追 arg2 的 ecx/push 来源与类 |
| U6 | FactoryClass `GetSize=0x74` 的构造分配点 | v[12] 单边对上，`push 0x74` 全镜像 0 处；可能经池/派生类分配，未找到双支撑 | 追 `FactoryClass` 派生 RTTI 名或 `0x4CA760` 引用链 |
| U7 | “两个对象进同一格”的运行时路径是否存在 | 静态只证 worker 不查占用 + head B 旁路；真机 W177-C 仍为链长 ≤1 真阴性 | W177-D 按 `FEED_W177D.md` 构造/判证 |
| U8 | dword `[+0x80]` 905 处访问中有多少真读写 byte `+0x81` | 宽度不同，不能合并；本卡只分列计数 | 逐点看结构对齐/联合体证据，需类布局支撑 |

注：`[+0x81]` 的“Limbo 标志”语义已由写点 `0x5F4E9E` + 读点 `0x5F4D45`/`0x701664`/`0x701681` 闭合，不再是 UNKNOWNS（见 `EVIDENCE/T3_SEMANTICS.md`）。
