# DISAGREE.md — S02B-GATE 与既有结论的分歧/更正建议

## D1 — 对 R14_COMMON §2.5 / 台账 §995「bit0 过滤点是 InfantryClass 专属」的更正（核心分歧）
- 既有（§2.5、§995 一）：「构造链 `0x6F322F or al,1 → 0x6F3237` 使**在册 InfantryClass** bit0 恒 1」，并以此解释「目标格有步兵被拒」。
- 本卡字节结论：该写点宿主是 **`0x6F2B40` = TechnoClass 构造体**（体内写 `.?AVTechnoClass@@` vt 0x7F4960/0x7F4944/0x7F493C/0x7F4934）。Infantry(0x517A50)、Aircraft(0x413D20)、Unit(0x7353C0) 三者构造体都经 FootClass 构造体 0x4D31E0 → `0x4D31EA call 0x6F2B40` 继承**同一** bit0=1；Building 构造体 0x43B740 也直接 `0x43B74B call 0x6F2B40`。⇒ bit0 恒 1 是**全体 TechnoClass 派生对象**属性，非步兵专属。
- 影响：LIVE-L2「己方车辆 5/5 全拒」只有在此更正下才自洽；旧表述会错误预测车辆放行。建议 §2.5 改为「目标格有任意 bit0=1 的 TechnoClass 派生对象（步兵/车辆/飞行器/建筑）即拒」。证据：EVIDENCE/ctor_rtti_chain.txt、unit_class_ctors.txt、bit0_write_points_global.txt。

## D2 — 对 §2.5「`[S+0xE4]` 是否=目标格占用表缺直接证据、`{0,0}` 疑点」的更新（非推翻，是补证）
- 既有：路径 `[已证]`、总判断 `[静态推断]`，两条残留 = S+0xE4 语义未定 + `0x47C72F` 传 `{0,0}`。
- 本卡补证：`this(ecx)=CellClass*`（调用方 0x43F2A7 GetCellAt → 0x43F2AC）；`0x47C3D0` 的 `0x47C40F [ecx+0xE4]` / `0x47C407 [ecx+0xE8]` 是格对象**双链头**、`next=+0x30`（0x47C4A7），与 §2.2 挂链结构一致。`{0,0}` 只是 arg1 距离基准（存在性测试用），格身份由 `this` 携带。⇒ 「同格」前提字节闭合。
- 保留：总判断升 `[已证]` 仍需 D-36 真机命中闸；本卡**不**单方抬级、不越界。证据：EVIDENCE/q1_q4_evidence.txt（0x43F180 段）、fresh_47C3D0.txt。

## D3 — 对 Q3 备择「按 WhatAmI 判」的明确否证
- 若按 WhatAmI（Infantry=15/Unit=1/Aircraft=...）判，闸内应见 `cmp eax,0xF`/`cmp eax,1` 等立即数。本卡全扫：`0x47C620` 的 WhatAmI 比较集 = `{6 Building, 0x24 Terrain, 2 Aircraft}`（0x47C668/694/723/7B3/7EA/825），`0x47C3D0` 闸核**无任何 WhatAmI 比较**，只有 `and al,1`。⇒ WhatAmI 假设被字节否证；判据是 bit0。与 §2.4 比较集事实一致，无冲突。

## D4 — 无分歧项（记录以免后续误读）
- arg2 = `.?AVBuildingTypeClass@@`（非 HouseClass）：本卡 RTTI 独立复算 COL 0x7FC618→TD 0x8193A8→内联名串逐字符读，与 §995 三一致，**无分歧**。
- `[0xA8E9A0]` 23W/100R：本卡全 .text abs-form 实扫得 123 访问（100R+23W+0 inc-dec），与 §995 二一致，**无分歧**。
- slot 73 四类不对称（§2.1）：本卡实测 0x43F180 有 `call 0x47C620`、0x4D3780/0x6F4A70 无，一致，**无分歧**。
