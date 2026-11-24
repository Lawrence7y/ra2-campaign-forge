# C02 · UNKNOWNS（未解决项）

## 1. 无法归类 / 低置信函数（220）

`coverage_delta.tsv` 中 `source=none` 的函数 **220** 个，统一归 S22 兜底、grade=[未证]：
- **211 个真零证据**：无 vtable 槽、无已知名、无字符串、无源文件归属、无已知名亲戚、无特征导入 API。多数是 `n_callers` 很低的小转发桩（如 `0x0045E750` size=1、`0x00465CB0` size=1、`0x00465D30` size=3）或局部 helper。要在 P1 命名需逐函数线性反汇编追 this/参数来源（本卡 P0 普查不做）。完整地址见 `EVIDENCE/classification_trace.tsv` 过滤 `source==none`。
- **9 个有弱信号但未命中 S01–S22 规则**：有导入 API（如 `wsprintfA`/`WideCharToMultiByte`/`GetModuleHandleA`）或已知名亲戚但名字指向 `CRT::*` 等未映射命名空间。需要 P1 补规则或人工判读。

这 220 个不计入 high（840），也不应被合并员误当 [已证]。

## 2. atlas 空洞入口真伪（111 个候选）

`atlas_gaps.tsv` 列 111 个 owner=None 的 call/jmp rel32 目标（区间包含判据）。分级：
- **17 个 call 目标**：高置信真函数入口（call rel32 必指向入口）。
- **1 个 `0x4824D4`**：台账 §926-1 已 [已证] 的真实入口，本卡扫到引用它的指令是 `0x4824C8: jmp 0x4824d4`（见 DISAGREE.md）。
- **92 个 low(jmp-hole)**：jmp 目标且引用站点也在洞内，多数疑似线性反汇编穿越数据/对齐区产生的伪 jmp，或跳表 case 标签，**未逐个证真**。已知该批中 `0x48208A/0x482166/0x4821AF/0x482439/0x482465/0x4824D4/0x4832F0/0x4832F5` 正是台账 §926-1 列出的 8 个入口（其中 0x4824D4 已证）。其余待 P1 逐点用 boundary_check + 序言判读。
- **1 个 `0x46F5E0`**：boundary=False（落在某条指令内部），标 `reject-inside-insn`，不建议当入口。

## 3. vtable 槽的"方法语义"未证

753 个函数命中 vtable 槽，本卡只确定"属于类 X 的第 N 槽"并据类映射到 Sxx；**槽对应的具体方法名/语义未逐证**（除 144 个有 YRpp/kb 地址名者）。例如 S07 的 358 个 high 多为 Blitter 模板类槽（`T_Blit*`/`T_RLEBlit*`），只能确定"是某 Blitter 的槽"，不能仅凭槽号断言是 `Blit()` 还是 `Blit_FixedAlpha()`。P1 的 K/N 类卡需结合 YRpp `Blitters.h` 槽序逐点确认。

## 4. 归属可商榷项（已按 PLAN §1 定规则，记录分歧空间）

- `BuildingClass::*` 方法（KillOccupants/UpdateBunker/UnloadBunker…）本卡归 **S12**（建造放置/工厂），但其中"载员/驻军"语义也可论属 S05(对象模型) 或 S13(战斗)。依据：PLAN §1 S12 含"生产/经济/工厂/建造放置"，BuildingClass 为生产载体。
- `CaptureManagerClass::*` 归 S12（占领/控制属经济），亦可论属 S14(House)。
- `TransitionTimer::*` / `UI::GetResource` 归 S09，亦可论属 S01（帧时钟）。
- `T_VectorClass_*`/`T_DynamicVectorClass_*`/`T_TypeList_*` 容器按元素类型映射（如 `Vector<ConvertClass*>`→S07）；元素为纯 `H`/`PAD`/`Point3D` 时归 S22。

上述均为候选分类，不写 [已证] 语义；合并员如遇其他卡更精确名字，按 grade 优先级合入即可。
