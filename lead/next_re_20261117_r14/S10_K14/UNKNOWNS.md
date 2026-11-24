# S10-K14 UNKNOWNS
- 环①缺口：[vt+0x184]=005B3040 的返回值（[this+0xAC]，-1 回退 [this+0xB4]）在目标内与 0x15/0x0B/0x01/0x0F 比较，但本卡未找到该类字段写点+读点的语义双支撑；覆盖表 005B3040 名 AircraftClass::slot97，语义栏自注“槽语义未证”。补足条件见 PROGRESS.md 环①段。
- 0x816CAC 位于运行时数据区，文件内无内容可静态读出；本卡只证明目标 0 引用、全局 12 处中 11 处 dword[idx*4]、1 处 mov esi,base 后 dword[esi]，未给表项命名。
- 0x89F688 仅由 8 次 stride-4 的 word-pair 访问证明为 8 项 (short dx,short dy) 结构；表内容不可静态读，未冒充 YRpp 字段名。
- 005657A0 覆盖行 conflict=1（TryGetCellAt / GetCellAt 名称争议）；本卡只用其地址与 [已证] grade 作环④，名字合并请走 CONFLICTS 流程。
- 006F5090 覆盖行 grade 为 [静态推断]，两次“收尾”调用不能补环④；0056BC50/0070F6A0/0070F670 等直接被调同样非 [已证]，未计入。
- 0x5B3740 不在 atlas（S10 表外两点之一）；其 0x816CAC 引用在 jne 目标 0x5B374D，与 0x5B374C 的第一条 ret 构成同函数双返回形态，未扩大为“32 项名字表”。
- 本行保持 [静态推断]：没有运行时观测，也没有把 +0x184 升格为已证 mission 枚举的独立证据。
