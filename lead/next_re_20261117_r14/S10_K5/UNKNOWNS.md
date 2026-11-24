# S10-K5 · UNKNOWNS

| # | 未知 / 未升级项 | 状态 | 已尝试与下一步 |
|---|---|---|---|
| U1 | S10 距 DoD 50% 门槛仍远 | [已证] | 初读 111/526，但在 03:52:48 外部把 K4 19 行降为静态后，现读 92/526=17.4905%，门槛 263，差 171；本卡 +7 后模拟 99/526=18.8213%，仍差 164。 |
| U2 | 盘上 19 行 K4 单源命名 grade | [已证] 已由外部更正 | 03:51 初读仍 111；03:53 复读 coverage 已降该 19 行为 [静态推断]，与 S10_K4/_audit/VERDICT.md 一致。初读快照与现读快照分别存 EVIDENCE/baseline_recompute.txt、EVIDENCE/baseline_after_change.txt。 |
| U3 | 005B3A10 谓词语义 | [未证] | 仅 mov edx,[ecx+0xB0]; cmp edx,-1; setne al; ret；无直接 caller、无被调语义、无第二命名通道；未升。 |
| U4 | 005F5E80 字段加载/清零例程 | [未证] | 有 0x6CF240 Here_I_Am 与多字段清零，但缺关键枚举常量与命名闭环，不能给出 Save/Load 真名；未升。 |
| U5 | 0070DD90 | [未证] 反例 | B8 imm=1 对应 AbstractType Unit，但 RTTI 是 AircraftClass；无 GetSize/WhatAmI 双点闭合；未升。 |
| U6 | K4 遗留 63 字符串命中与 15 个 sub_ 占位 | [未证] | 均为共享尾引用或无 RTTI/vtable anchor；本卡未重扫出新闭合，沿用失败关闭。 |
| U7 | MissionControl 类属 | [未证] | 镜像 RTTI 无 MissionControl TD；coverage 中 005B3700 名 MissionClass::MissionControlClass 且已 [已证]，字节是常量初始化，不是析构；Mission 家族无第二标量删除析构。 |
| U8 | 0x4A1DE0 无正式符号名 | [静态推断] | 4A1D50 的字节证明“push 4 + push &value + call 4A1DE0”，4A1DE0 内部逐字节循环；语义锚定依赖盘上已证 00410410 AbstractClass::Save 与同原语的调用链，不把 4A1DE0 当已证符号名。 |
| U9 | 005F3B80 盘上名 ObjectClass::ObjectClass 陈旧 | [已证] 分歧 | 本卡只用其字节（同组基类 vptr 写 + 数组反注册 + 无 delete/ret4）判“基类析构形”，不采用该名作语义证据。 |
| U10 | 5 条非 Mission 同型 dtor 是否超严格任务2范围 | [已证] 决策登记 | 任务2字面只点 MissionClass/MissionControl；本卡按“同族清扫”判据把 S10 内 5 条非 Mission 同型 RTTI/slot8 行一并入 delta。若 lead 要求严格只留 Mission，则删这 5 行，按现基线 proved 为 94/526=17.8722%，仍不影响 005B3A60 与 005B3970。 |

## 复算入口
- work/baseline_recompute.py：读盘基线/时点/目标行；EVIDENCE/baseline_recompute.txt 为初读 111，EVIDENCE/baseline_after_change.txt 为现读 92。
- work/mission_sweep_strict.py：Mission RTTI/虚表 + 入口到首 ret 的严格删除析构窗。
- work/probe_s10_dtors.py、work/probe_vptr_writers.py：6 条 dtor 逐行字节/RTTI/ctor 写 vptr。
- work/probe_mission_fields.py、work/behavior_disasm.py、work/probe_stream_callees.py、work/make_save_evidence.py：005B3970 四环。
- work/finalize.py：delta 生成与 0 重复/0 占位名/证据存在性校验（按现读 92 基线）。
