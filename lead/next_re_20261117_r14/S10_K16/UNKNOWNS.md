# S10-K16 UNKNOWNS
- [this+0x328]/+0x32C/+0x330/+0x334 只称“成对 float 状态与增量”，由读写、加减、clamp 与常量边界支撑；未冒充 YRpp 官方成员名。
- [this+0x220]==2 只称 mode-2 门控（沿用 K14/K15 已用口径），未给字段官方名；[this+0xA83D4C] 全局对象只按地址引用，不命名 HouseClass::CurrentPlayer。
- +0x6C/+0x70=[type+0xA0] 的“声音/类型缓存”由 body 写、外部 00519630 读比较与 007509E0 VocClass::PlayAt 支撑；未观测运行时声音播放，未给 type+0xA0 官方成员名。
- 004C93D0 盘面 [已证]，当前 coverage 名为 FrameCRC_quant_helper；本卡只用其“真被调用且 grade=[已证]”作环④，不借该名推断 slot263 语义。
- 00754BE0 从 0xB44318 复制 0xC dwords 到 ecx，被 BulletClass::Draw 真调用；因无 RTTI 类归属/字段写读，不交严格 behavioral 行，不等于证明其无语义。
- 005F5E80 只由析构族 vslot5 调用；K5/K8 已扫完标量/普通析构 body，本轮不重复。
- coverage.tsv 并发窗口以 07:43:09 现场读盘为准；不追改共享表。
