# W177-KA · DISAGREE.md

> 引用格式：台账节号 / P0_GATE_B 文件节号 / R14_COMMON §。均非「新增台账结论」，只记录本卡与既有说法的不一致。

| # | 对象 | 不一致内容 | 本卡裁决 / 依据 |
|---|---|---|---|
| D1 | P0_GATE_B\UNKNOWNS.md U2（及 §994 表述「HouseClass 标志」） | U2 称 arg2「疑为 HouseClass*」 | **推翻该静态猜测**：j_run RTTI 证 arg2=BuildingTypeClass*（0x7E4570→0x7FC618→0x8193A8）；台账 §678 早已证 +0x520=BuildingTypeClass。真 owner HouseClass 四标志亦全 0，不影响选支。分级 [已证]。 |
| D2 | W177-J\EVIDENCE\branch_recompute.txt (b) | 「E58!=0 → 0x47C76B 表查（不查 head A）」 | **过简**：字节层 0x47C79E 读 [edi+0xE4] 并按 A8E9A0 扫 WhatAmI 6；准确说法是「不经 0x47C738 的类型无关 [obj+0x14]&1 闸」。依据 `EVIDENCE\ka_47c620_disasm.txt`。 |
| D3 | W177-J\j_run.json sampling.rate_per_s=15517.5 / branch_recompute.txt 沿用 | 该值是 n/duration 的**均值** | 本卡按任务要求用时间戳差分**中位数**：dt=49 µs ⇒ 20,408.2/s；均值 15,517.6/s 并列，不视为数据造假，但不得称「采样率」而不标口径。依据 R14_COMMON §8.1 ⑨/⑩。 |
| D4 | 台账 §994「闭合只剩真机一次断点（0x47C853）」 | 未说明授权边界 | 本卡不否定该结论，但指出：在「不写进程内存 + 只读上下文 + 无软断点/无 Hook」下断点不可做（软断点写 0xCC、硬件断点写 Dr0–Dr7），需扩权；在扩权前闭合保持 [未证]。 |
| D5 | R14_COMMON §8.1 ⑫ / 台账 §988 L3 | 颜色判据必须配对无 ghost 基线 | W177-J 有 j_ingame（无 ghost、同地图区）但非同帧且 UI 状态不同；j_hover_anchor 与 j_after_click 前后同色。本卡只把颜色作为 ghost 存在辅助，不支持 can-place 语义。 |
| D6 | P0_GATE_B\UNKNOWNS.md U8 / 台账 §988 | 「0x47C853 未落盘」 | 本卡再次确认：W177-J 亦未观测 EIP/al；不把「静态选到 0x47C738」升格为「闸命中」。 |
