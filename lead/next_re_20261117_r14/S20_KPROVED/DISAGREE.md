# S20-KPROVED DISAGREE

1. **与纪律 ⑲ 的措辞差异**：卡面称 capstone `op.index` 对无 index 操作数返回 0；本环境 5.0.7 的 x86 operand 实测**没有 `op.index` 属性**（`EVIDENCE/capstone_index_selfcheck.json`）。本卡未据此否定任何行，反而完全避免 index 过滤；两者结论方向一致，只是 API 表现不同。
2. **与“目标 40 行”的处理**：扫描发现 65 行 S20 静态行有 direct/exact 环④，交付按卡面上限选 40；其余 25 行列 `EVIDENCE/unselected_c1_pass.tsv`，不并入 delta，也不写成 C2。
3. **无 grade/name/subsystem 分歧**：delta 40 行名字与 subsystem 逐行等于盘上 coverage；只按卡面把 grade 从 `[静态推断]` 改为 `[已证]`。
