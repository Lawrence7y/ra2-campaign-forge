# S17-K3 · UNKNOWNS

## U1 · 10 条 NOT named(S) 行不可定名（保持 sub_）
除 00431B80 外的 10 条候选，逐条见 `TARGETS.tsv` / `EVIDENCE/candidate_disasm.txt`，均按"拿不到具体语义就保持 sub_"处理：
- 004068E0（1B `ret` 桩）/ 0040E340（通用双向链表 splice）/ 00427940（对象表遍历 + ".SHP" 串）/ 0042E410（4-dword setter）/ 00433CF0（UTF-16 宽度跳表）/ 004355B0（3B setter）/ 0043AE50 / 0049F740（MapViewOfFileEx 弱信号）/ 0049F8B0（UnmapViewOfFile 弱信号）/ 00773450（WebBrowser ctor，非 S17）。
- 全部无 vtable 槽、无 RTTI 类名、无独立调用者身份可支撑语义；不用 `Class::sub_XXXXXXXX` 充数，不编名。

## U2 · 00431B80 的 grade 必须升 [已证] 才能让名字合入
`CONFLICTS.tsv` 已有 `00431B80 name S17-K2:BufferIOFileClass::~BufferIOFileClass vs COVERAGE(prior):sub_00431B80`。
按合并规则「同 grade 保留先出现者」，K2 用 [静态推断] 报该名 → 被 prior 挡回 → named 停在 91。
本卡以**字节级证据**（RTTI `COL+0xC→TD+8` 全值读出 `.?AVBufferIOFileClass@@` + 析构指令 + vt slot0 同构 + CDFileClass 删除析构调用链）报 [已证]，按「grade 高者优先」应合入。若合并员仍因 conflict=1 拒合，需审计裁 CONFLICTS 该行；本卡不写台账，只交 delta。

## U3 · T3 抽查：1/5 证据链偏软（非造假）
`006CF240 Here_I_Am` grade=[已证]，但证据源是 `self_known`=YRpp/kb 外部地址名复用 + `SwizzleManagerClass:4` 槽位，语义栏自带 `[未证]`；按硬规矩「复用别人结论不够 [已证]」该行 grade 依据不足。
我独立字节复核：函数体确为 swizzle 表登记（vector append + 清零源指针），行为真实 ⇒ 非编造，但 grade 应降级或补字节级 evidence_path。
影响：即便该行降为 [静态推断]，proved 53→52=50.98% 仍过 50% 线，S17 proved 不破线。

## U4 · 命名撞名风险（沿用 K2 审计 ★B6，本卡不自行裁决）
K2 审计指出 `AirstrikeClass::Save`/`NeuronClass::Save`（0x41D6E0/0x43A5D0）与 KB22「槽6=Save、槽13=基类块」命名撞名；字节真实（本卡 T3 独立复核通过），但名可能应改 `::SaveBaseFields`。这 2 行已计入 named 91，**不影响本卡 named 91→92 的算术**，仅提示后续命名规范卡。

## U5 · IID 标签偏差（沿用 K2 审计 ★B4）
0x67C690 语义写 `IID 0x7F7C90`，本卡字节实测 `0x7F7C90`=IID_IUnknown、`0x7F7C80` 才是 IID_IPersistStream；字节事实（调用 OleLoadFromStream）真实，标签偏差不影响 proved 计数。
