# S10-K7 · DISAGREE

| # | 对象 | 本卡结果 | 依据 |
|---|---|---|---|
| D1 | S10_K5 UNKNOWNS U6 “无 RTTI/vtable anchor” | **对这两条不同意**。006B7010 有四张虚表回写 + COL+0xC→TD 00840120；004E0E80 有 VT 007E920C 回写 + COL+0xC→TD 008225B8。不是无锚。 | EVIDENCE/CLOSEOUT_CHECKS.txt；EVIDENCE/targeted_proof.txt |
| D2 | S10_K5/_audit/VERDICT.md E 对 004E0E80 的“疑误杀/属次级” | **确认误杀并闭合为 [已证]**。8 个 capstone 校验的直接调用点、ecx=this/两栈参/ret 8、唯一 call 007C8E17、RTTI 模板名齐全；“模板 ctor 约定”不是单源，因为构造角色由调用序列与字节独立给出。 | EVIDENCE/CLOSEOUT_004E0E80.txt；EVIDENCE/caller_and_ctor_context.txt |
| D3 | 审计基线 92 vs 本地全部 S10 行 93 | **无冲突**。审计用 S10∩atlas=526 分母；全部 S10 528 行多一个表外已证 005B3740。本卡按 ∩atlas 92 结算，字段仅读第5列。 | EVIDENCE/baseline_recompute.json |
| D4 | 006B7010 在审计文中被称“本类析构”但 U6 判不可证 | **理由错述已纠正**。它不是标量删除析构（无 flag test、ret 而非 ret 4），而是 006B8140 调用的本类普通析构；本卡按普通析构命名。 | EVIDENCE/CLOSEOUT_006B7010.txt |
| D5 | S10_K5 D8 005F3B80 陈旧名 | **无新增分歧**。本卡未引用该名作语义证据；006B7010 的 RTTI/字节链独立。 | EVIDENCE/targeted_proof.txt |

## 纪律自检
- 只读目标；未写 COVERAGE/、未 git commit、未用 Ghidra。
- 只处理卡面两条；第3条同组写回仅记 UNKNOWNS U1。
