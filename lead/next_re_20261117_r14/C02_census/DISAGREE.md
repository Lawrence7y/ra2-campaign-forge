# C02 · DISAGREE（与台账 / R13_COMMON 的冲突或措辞差异）

## D-1（低）`0x4824D4` 的发现通道措辞

- 台账 `lead\GOAL_THREE_TARGETS_20261018.md` **§926-1 / §926** 原文："真实入口 `0x4824D4` 只能靠 **call 目标通道**找到"，并列 8 个入口 `0x48208A/0x482166/0x4821AF/0x482439/0x482465/0x4824D4/0x4832F0/0x4832F5`。
- 本卡全 .text skipdata=True 扫描结果：引用 `0x4824D4` 的指令是 `0x004824C8: jmp 0x4824d4`（**jmp rel32**，不是 call）。`0x4824D4` 本身第一条指令是 `call 0x4F9950`（函数体）。`sweep_targets.json` 中 `0x4824D4 ∈ jmps`、`∉ calls`。
- 判读：**入口身份不冲突**（8 个入口本卡全部复现于 `atlas_gaps.tsv`），仅为"call/jmp 通道"措辞差异（台账把 call/jmp 合称"目标通道"）。不推翻 §926，仅记录供书记员措辞留意。

## D-2（低）atlas 空洞范围与 §926 一致，无 Expansion 冲突

- R13_COMMON §6-17 与台账 §926 均称 `0x482000..0x483400` 整段 atlas 无函数。本卡 `owner()` 区间包含判据复算：`0x4824D4` 及 8 个入口均 `owner==None`，一致。无分歧。

## D-3（低）S07 占比高非与 §917/§918 冲突

- 本片 S07=377（27.8%），源于地址区间覆盖大量 Blitter 模板 vtable 槽；台账 §917/§918 的"Blitter slot 1 占 EIP 61.9%"是**真机 EIP 权重**，与普查的"函数条目数"是两个量纲（R13_COMMON 纪律 10：EIP 权重 ≠ 调用频率）。本卡未引用 §917 数字，无冲突。

## D-4（无分歧）已证名一致性

- 本卡 [已证] 的 143 个函数名与 YRpp 头文件 `JMP_THIS/INI_READ` 地址名及 `re_atlas\kb\*` 一致；抽查 `BulletClass::Detonate@0x4690B0`（与 `re_line` Q1_C3C4 文档 §270 一致）、`CellClass::CanThisExistHere@0x47C620`（与 W108_TRAVERSAL_AUDIT §151 一致）、`CCINIClass::*` 系列（与 kb/30 一致）。未发现与本片地址重叠的作废索引项（R13_COMMON §1 的作废节均落在 0x43xxxx/0x4Bxxxx/0x55xxxx–0x70xxxx，不在本片 0x456E00–0x4A60CB）。

> 结论：无实质性技术冲突；仅 D-1 一处措辞差异需登记。
