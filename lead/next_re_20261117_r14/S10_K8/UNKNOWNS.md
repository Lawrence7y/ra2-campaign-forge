# S10-K8 UNKNOWNS
| # | 项 | 状态 | 处置/下一步 |
|---|---|---|---|
| U1 | 004DFA70 / 00521760 | [静态推断] | 自身零字段写；环②由被调字段写提供且与环④同源。按 Lead-1 退静态、不进 delta、不双计。 |
| U2 | 004E0E80 子域归属 | [待裁] | RTTI/ctor 命名成立；coverage_README class_to_sub 与 D-37 指向 S22。裁决前 delta 暂留 S10，conflict=1；若归 S22，S10 99→98、S22 56→57。 |
| U3 | 队列吞请求的运行态 | [静态边界] | cur∈{4,26,27,30,31}∧[this+0x294]==0 会吞；另有 005B35E0 三处早退。语义栏已写成前置条件，静态无法判定某次运行是否实际写 +0xB4。 |
| U4 | 006B6FA0 无 caller | [已证] | 0 直接 E8、0 指针引用（死代码）；接受依据为 4-vptr→TD 00840120 + 004101C0 + 成员初始化 + ret 4，不以 caller 为必要条件。 |
| U5 | 006B6C90 原名 sub_ | [已证] | 盘上 grade 已是已证；本卡只修名为 SpawnManagerClass::SpawnManagerClass_5args，不重复计 proved。 |
| U6 | 006B7F10 | [排除] | 007F3664 为 slot5；构造 arg1(ebx) 而非 ecx=this，角色锚失败。未触碰。 |
| U7 | behavioral 名 | [口径] | 6 条队列行为名与 RTTI ctor 名分离；带字段语义的名字不得声称真方法名，name_kind 已显式标注。 |
| U8 | 命名双源强度 | [静态] | ctor 的 symbolic 名来自 RTTI 类名 + 构造角色，不等同二进制内保留原始符号；不把它当额外独立证据。 |
| U9 | 基线未并盘 | [已证] | 本卡只交 coverage_delta.tsv；COVERAGE/coverage.tsv 未被写入，mtime 仍 04:05:20+08。 |

## 复算入口
- work/baseline_k8.py → EVIDENCE/BASELINE_RECOMPUTE_K8.txt
- work/s22_baseline.py → EVIDENCE/S22_BASELINE_K8.txt
- work/build_queue_evidence.py → EVIDENCE/QUEUE_DISPATCH_AND_FALSE_KILLS.txt
- work/build_ctor_evidence.py → EVIDENCE/SPAWNMANAGER_CTORS.txt
- work/build_ownership_evidence.py → EVIDENCE/OWNERSHIP_004E0E80.txt
- work/validate_delta.py → EVIDENCE/DELTA_VALIDATE.txt
