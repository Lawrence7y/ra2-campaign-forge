# S10-KPROVED DISAGREE

1. 本环境 capstone 5.0.7 x86 operand 无 `op.index` 属性、但 `op.mem.index=0`；全程不用 `index is None` 过滤。
2. 自算 58 行过同一 C1 判据，按卡面只交 40；其余 18 行只列 `EVIDENCE/unselected_c1_pass.tsv`，保持 `[静态推断]`。
3. `004CBBA0` 无可复算 vtable/RTTI 槽证据但有 instruction-boundary 外部 direct call；交付明示 atlas-only，未借 vtable/RTTI 冒充第二通道。
4. `coverage_delta.tsv` 40 行 name/subsystem 与盘上逐字一致，只把 grade 从 `[静态推断]` 改为 `[已证]`。
