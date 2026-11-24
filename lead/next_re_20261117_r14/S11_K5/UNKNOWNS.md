# S11-K5 · UNKNOWNS

| # | 未解决 / 未升级项 | 级别 | 依据 |
|---|---|---|---|
| U1 | **grade 升级 0 行，只有 11 行语义重证；低于卡面期望的 15 行**。不是方法没跑通：双通道普查证明非已证 S11 行中 `B8 imm32 C3` 为 0，故无合法 GetSize/WhatAmI 可升。宁可报 0，不用槽归属/占位名凑数 | [已证] | EVIDENCE/candidate_census.txt；EVIDENCE/validate_delta.txt |
| U2 | 9 条静态行入口为 `B8 imm32 C2 04 00`（ret 4，imm=2/3），不是卡面允许的 `B8 imm32 C3`；且返回值不是 AbstractType 枚举语义，全部保留原级 | [已证] | EVIDENCE/candidate_census.txt；EVIDENCE/entry_shapes.txt |
| U3 | K4 的 331 行仍全部 `[静态推断]`：其证据只证明入口+槽归属，不证明 name/语义；本卡未复用其升级结论 | [已证] | S11_K4/_audit/VERDICT.md；EVIDENCE/candidate_census.txt |
| U4 | 全 RTTI 有 69 个 WhatAmI 语义闭合类，但与 S11 coverage∩atlas 交集为 0；不跨子系统把它们记入 S11，也不新增覆盖行充数 | [已证] | EVIDENCE/whatami_candidates.txt；EVIDENCE/candidate_census.txt |
| U5 | 11 个 GetSize 行本就 `[已证]`，delta 各行显式写 “Grade unchanged”；合入后 proved 仍 29/368，不得据 11 行重证宣称 proved 增加 | [已证] | coverage_delta.tsv；EVIDENCE/validate_delta.txt |
| U6 | 17 个非 vtable / 非本卡闭合 S11 行（VectorClass 7 条及 sub_* 等）保持原级；本卡未给它们构造双点行为证据 | [未证] | EVIDENCE/entry_shapes.txt；S11_K4/UNKNOWNS.md |
| U7 | 本卡为静态字节证明，未证明运行时调用频率或消费者实际按 size 使用；卡面允许的双点闭合已满足，但不外推真机行为 | [静态推断] | EVIDENCE/getsize_closure.txt |