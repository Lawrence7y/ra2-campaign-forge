# SEMFIX-6 PROGRESS

- Status: complete
- Scope: 6 rows only; write domain = SEMFIX_6
- Skeleton landed first; R14_COMMON §8.6 and CARD.md read

## Done

- Disassembled six bodies with Python 3.12.10 + capstone 5.0.7; gamemd.exe read-only.
- Verified jump tables: 10 slots and 11 slots, all targets in .text.
- Rewrote only one_line_semantics for six rows.
- Built coverage_delta.tsv (8 cols, 6 rows, last col [已证]→[已证]).
- Evidence: DISASM_FULL_*, JUMP_TARGETS_*, D42_SEMANTICS.md, OFFSET_HITS.tsv, GRADE_NAME_ZERO_CHANGE.tsv.

## Numbers

- 补写行数: 6
- Semantic chars: 220/232/198/245/298/236 (all >=80)
- Offset hits: 45/45
- grade/name/subsystem zero-change: 6/6
