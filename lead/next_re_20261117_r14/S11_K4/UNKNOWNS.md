# S11-K4 · UNKNOWNS

| # | 未解决 / 未升级项 | 级别 | 依据 |
|---|---|---|---|
| U1 | 17 个 S11 行未升级：7 个 VectorClass::USubzoneConn* vslot、00415C60、00442D90、004AF5E0、004B5B00、0054AD00、0055A6F0、005AE860、005AF1A0、0069ECF0、007559B0、0075AB00 等（以 EVIDENCE/nonvtable_classification.txt 全表为准） | [未证] | 本卡只要求 vtable/RTTI 直指或工厂 push/new/ctor 闭合；这些入口无本卡可独立复算的上述证据 |
| U2 | 二级构造/委托桩（如 004AF5E0/004B5B00/0054AD00/0069ECF0/0075AB00）写入 canonical vtables，但本卡未证明其完整调用契约与高层语义，不把“写 vptr”当“已证构造” | [静态推断] | EVIDENCE/nonvtable_classification.txt；EVIDENCE/closure.txt |
| U3 | WhatAmI 未升级：Locomotor 是 COM/多继承族；off0 slot9 是 Size，off4 slot11=0055ABD0（写两 0）、slot12=0055A8C0（Shadow_Point）。未发现可映射到 AbstractType 枚举的 WhatAmI 槽；不猜名 | [未证] | EVIDENCE/layout.txt；台账 §981；R14_COMMON §8.2 技术② |
| U4 | Teleport off0 表 12 槽，其中 slot10/slot11 语义未定；本卡只证明槽归属，不证明高层语义 | [未证] | EVIDENCE/layout.txt；EVIDENCE/entry_evidence.txt |
| U5 | 绝大多数 off4 槽只证明 RTTI 类/接口/slot/字节结构事实；Process/Move_To 等高层语义未按本卡字节证据逐条闭合，故语义名沿用 coverage 现值 | [静态推断] | EVIDENCE/entry_evidence.txt；coverage_delta.tsv |
| U6 | 006C41D0 仍标 JumpjetClassFactory::CreateInstance；本卡重扫的工厂 RTTI vtable slot3 指向 006C4190。本卡不擅自改一个已 [已证] 行的名字/证据，登记冲突见 DISAGREE D3 | [未证] | EVIDENCE/layout.txt；EVIDENCE/closure.txt |
| U7 | 本卡为纯静态；未证明任何运行时调用频率或“被当 size 使用”的消费者 | [静态推断] | 卡面范围限制；台账 §981 保留项 |
