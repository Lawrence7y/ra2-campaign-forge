# S11-K4 · PROGRESS（Locomotor 批量静态提级）

> 只读目标 gamemd.exe（SHA-256 自算 73201CC0…F67476）；纯静态，未用 Ghidra。写域仅 S11_K4\。
> 方法：重扫 RTTI COL+0xC→TD+8（TD+8 为内联名串）+ .rdata vtable 定界 + capstone 5.0.7 skipdata=True；不从 atlas 反推表边界。

## 结论表

| # | 结论 | 级别 | 证据 |
|---|---|---|---|
| 1 | 盘上卡前值：S11 coverage 379 行；coverage∩atlas（大小写归一）368；proved 29（7.8804%），named 358；DoD 50% 门槛 184，尚差 155 | [已证] | EVIDENCE/baseline_recompute.txt |
| 2 | 本卡独立重扫得 23 TD（1 基类+11 具体+11 工厂）、41 COL、41 表/825 槽；其中 Locomotion 30 表/770 槽，工厂 11 表/55 槽；表边界全由 .rdata 的 COL/vtable[-1] 与表间停止条件给出 | [已证] | EVIDENCE/layout.txt |
| 3 | 11 个具体类 RTTI 类名与 off=0/4/24 接口偏移全部实测；读不到即 fail-closed；TD+8 为内联串非指针 | [已证] | EVIDENCE/layout.txt |
| 4 | GetSize 在 off0 主表 slot9（非 slot12）：770 槽仅 11 处 B8 imm32 C3，全在该槽；11 个 B8<size>C3 与工厂 push<size>;call 7C8E17 双点闭合 11/11，且 ctor 写本类 canonical vtables | [已证] | EVIDENCE/closure.txt；EVIDENCE/shape_scan.txt |
| 5 | 编码陷阱复现：6A imm8=10 / 68 imm32=1（Jumpjet 0x98） | [已证] | EVIDENCE/closure.txt |
| 6 | 共用桩 004C9150=33 C0 C3 已排除，未计为任何具体类 GetSize，也未写入 delta | [已证] | EVIDENCE/closure.txt；work/validate_delta.log |
| 7 | 裸 B8 imm32 C3：.text 666；锚定 Locomotion 770 槽仅 11 且全为 GetSize。全 RTTI 表复扫得 1,214 表/14,044 槽，确认 vtables_v2.json 槽数错；五类 slot35/36 非尺寸反例（0x7FFFFFFF / 0x8182E0）已复现，裸形态判据不特异 | [已证] | EVIDENCE/shape_scan.txt；EVIDENCE/shape_counterexamples.txt |
| 8 | 批量提级：331 行 [静态推断]/[未证]→[已证]（atlas 内 322、atlas 外 9）；证明类型均为 RTTI+.rdata vtable 槽直指（entry、VT、COL、TD、槽字节、入口字节可复算）。GetSize 11 行本就 [已证]，本卡重算但未重复计数 | [已证] | coverage_delta.tsv；EVIDENCE/entry_evidence.txt；work/validate_delta.log |
| 9 | 合入模拟：atlas proved 29→351 = 95.3804%，named 保持 358/368=97.28%；DoD 第 1 条双线跨过 | [已证] | work/validate_delta.log |
| 10 | 17 个非 vtable 且非本卡闭合的 S11 行保持原级；WhatAmI 未升级（本 COM 族无 AbstractType WhatAmI 槽可证） | [未证] | EVIDENCE/nonvtable_classification.txt；UNKNOWNS.md |

## 核心数字与复算

1. 卡前/门槛：368 分母、proved 29、named 358、门槛 184、需增 155。复算：python work/baseline_recompute.py > EVIDENCE/baseline_recompute.txt。
2. 本卡增量/闭合：新升 [已证] 331（atlas 322/外 9），证明类型=RTTI+vtable 直指 331；GetSize 双点闭合 11/11（重算，非新增），6A=10/68=1；排除共用桩 1、反例类 5。复算：python work/rebuild_layout.py → python work/fresh_proof.py → python work/shape_counterexamples.py → python work/build_delta.py → python work/validate_delta.py。
3. 合入后：351/368=95.3804%，named 358/368=97.28%，delta 331 行/0 坏行/0 共用桩声明。复算：python work/validate_delta.py（不写 coverage.tsv）。
