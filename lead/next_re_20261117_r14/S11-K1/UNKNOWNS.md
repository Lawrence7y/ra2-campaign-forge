# S11-K1 · UNKNOWNS（未决 / 未证）

| # | 项 | 状态 | 说明 / 下一步 |
|---|---|---|---|
| 1 | 10 个非 Drive 类工厂的 `CreateInstance` 实函地址（ctor+0xD0 推导值） | **[已证]**（原为 [静态推断]） | 11/11 已字节级复核 identical prologue + new+ctor（`EVIDENCE\factory_createinstance_all11.txt`）；Walk `0x6C4790` new 0x3C→`0x75AA90`。无需再跟进。 |
| 2 | `off=24`（8 槽）子接口的语义 | [未证] | 仅 6 类（Drive/DropPod/Jumpjet/Ship/Teleport/Walk）有。按 slot 数像第 3 个 COM 接口，但无 RTTI 名直接绑定、无独立调用点锚；RTTI 只确认是同一类的 `COL.offset=24` 子表。 |
| 3 | 槽 21–49（除 29/30/31/32/39/42/43/47-49）的独立调用点 | [静态推断] | 语义来自 YRpp `LocomotionClass.h:108-179` 声明顺序 + vtable 位置自洽，未在 `.text` 找到唯一调用点锚。 |
| 4 | `0x6C6400` 是否严格等于 `CoRegisterClassObject` | [静态推断] | 78 调用点全在注册函数 `0x6BB9A0`、形态 `(ecx=0xB0BC88, edx=GUID结构, push factory)` 与 COM 注册一致；未逐个查 IAT 名（该函数是内部包装）。 |
| 5 | 注册函数 `0x6BB9A0` 在 `0x6BD3BE`（Ship CLSID）之后还注册了 `0x7E96E0`/`0x7E9820` 等 CLSID | [已证但非本卡范围] | 这些是非 Locomotor COM 类（GUID 不同族），本卡只数 11 个 Locomotion CLSID（0x7E9A30..0x7E9AD0）。 |
| 6 | `IPersistStream` 接口 10 槽的具体方法名 | [静态推断] | `off=0` 表 10 槽（Teleport 12），按 `IPersistStream` 继承链推；未逐槽找调用点。 |
| 7 | Locomotion 对象内存大小（各派生类 new 的字节数） | [部分已证] | Drive `new(0x70)` 于工厂 `0x6C4010`（W164 线索 + 本卡）；其余 10 类未逐个读工厂 `push <size>`。 |
| 8 | Ghidra 反编译对 `FUN_006bb9a0` 给出的警告「Globals starting with '_' overlap smaller symbols」 | [已证为良性] | 局部变量重叠警告，不影响 `CoCreateInstance`/CLSID 结论；注意别把 `param_2` 误当 CLSID。 |
