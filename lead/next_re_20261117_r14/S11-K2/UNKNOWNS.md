# S11-K2 UNKNOWNS（未证项 / 需后续卡）

> 三级分级：`[已证]` 字节级证据；`[静态推断]` 文档/同构推导无独立字节证；`[未证]` 无证据。本卡只把 13 条抬到 `[已证]`，其余保持原级。

1. **12 类 off=4 主表槽 0–49 中，除锚点槽 7/16/17/18/47/48/49 与 off0 slot9(GetSize)/slot3 桩外的绝大多数槽**：只有实现地址 + 首指令签名（`EVIDENCE/fresh_slots.txt`），语义名来自 YRpp 头顺序（外部文档），无本类调用点字节证据 ⇒ 保持 `[静态推断]`/`[未证]`，不按惯例猜。尤其「slot 11 = WhatAmI」**未证**：实测 off4 slot11 `0055ABD0` 是「向输出缓冲写两个 0 的 `ret 8` 函数」，与 WhatAmI 返回类型 ID 的行为不符（`EVIDENCE/fresh_slots.txt`）。

2. **WhatAmI 在 ILocomotion 表中的真实槽号未证**：全 12 类全槽常量返回扫描（`fresh_slots.txt`）只命中 off0 slot9(GetSize×11) 与基类桩 off0 slot3=`004C9150`；off4 表内无「返回小常量 ID」的函数。可能在 off24 接口或需真机 `dynamic_cast`/RTTI 判定，本卡不下结论。

3. **Teleport off=0 vtable 槽数 = 12（其余 11 类 = 10）的语义**：`EVIDENCE/fresh_core.txt` 定界确为 12 槽（end `007F50FC` delim noncode），多出的 2 槽（10/11）实现地址已记录，但语义 `[未证]`。疑为 Teleport 特有接口扩展，未追调用点。

4. **CLSID「静态 {GUID→类→工厂} 并列表」不存在**：`work/t1_clsid_check.py` 扫 `.rdata 0x7E1000..0x811074`，无任何 dword 落在工厂构造器区间 `0x6C3F40..0x6C5000`（count=0）；`0x7E9A20..0x7E9ADF` 是 11×16B 纯 GUID 数组 + 1 个基类 GUID（`4A582740`，未注册）。映射在**代码**（注册函数 `0x6BB9A0` 内 11 个 push CLSID + 工厂 new/ctor 块），由 S11-K1 已入账，本卡复核一致。⇒ 无静态表可列，「找不到」的穷举依据见 `EVIDENCE/t1_clsid_check.txt`。

5. **字段语义定名未证**：`EVIDENCE/fresh_fields.txt` 给出 Drive 类双支撑字段（写+读，读者≥3）：+0x8(6W/19R)、+0x30(2W/3R)、+0x38(1W/3R)、+0x40(1W/4R)、+0x4C(1W/3R, `fld/fstp qword` ⇒ 8B double)、+0x68(2W/4R)。这些字段的**存在性 + 读写支撑**是 `[已证]`，但**高层语义**（如「目标格」「速度」「方向」）需追全部写点的寄存器来源与调用上下文，本卡不下语义定名 ⇒ `[未证]`（LayOUT.md 中逐项标注）。遵守「字段偏移不能定语义」纪律。

6. **跨类陷阱已规避、未复用**：`+0x94`（ObjectClass 层索引 vs 别处函数指针）、`+0x184`（Anim DelayTimer vs 别处函数指针槽）、`+0x80`（精灵级脏标记）均未套用本类族；本卡字段表仅来自 Drive 类自身 vtable 函数 + ctor 的读写点，无跨类推断。

7. **虚调用剔除数**：字段扫描中 `call/jmp [reg+disp]`（虚槽调用，非数据字段读点）共剔除 **34** 处（`EVIDENCE/fresh_fields.txt` 首行），未计入任何字段读点。

8. **eip/真机**：本卡静态，无真机；所有结论为二进制字节级静态证据，不涉及运行时验证。
