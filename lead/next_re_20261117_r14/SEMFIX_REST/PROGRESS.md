补写 41 行

# SEMFIX-REST PROGRESS
- Card: SEMFIX-REST; Agent: agent-67
- Started: 2026-11-18T17:55:50+08:00; Finished: 2026-11-18T18:05+08:00
- Target: ra2youli\gamemd.exe (READ ONLY)
- Scope: 41/48 CARD rows with template semantics; 7 rows already proper (untouched).

## Scope resolution
- CARD.md lists 48 non-S10 P1 rows; SEMFIX_S10 handles 25 S10 P1 rows.
- 41 rows matched "槽语义未证|弱信号|线索|未定" in coverage.tsv col4.
- 7 excluded: 0040F0A0,0040F150,00417FE0,0041A5C0,0041FB10,0044ACF0,0064DAB0.

## D-42 ③b conditions used
① jump table/switch; ② falsifiable return/sentinel; ③ memory shape (ctor+vt+layout); ④ complete loop I/O.

## Work done
- [x] Read R14_COMMON §8.6 (D-40/41/42 six criteria; D-42 ③b four sufficient conditions).
- [x] Read CARD.md and ROW_VERDICTS.tsv criterion/byte_evidence.
- [x] Disassembled 41 functions (pefile + capstone 5.0.7) into EVIDENCE/DISASM_FULL_*.txt.
- [x] Rewrote 41 one_line_semantics into human-readable function description + key offsets.
- [x] Wrote coverage_delta.tsv (42 lines: header + 41 rows, 8 columns).

## Verification
- Rows: 41/41; semantics changed: 41/41.
- Grade `[已证]` unchanged: 41/41; name unchanged: 41/41; subsystem unchanged: 41/41.
- Grade-change column: 41/41 `[已证]→[已证]`.
- Forbidden words ("槽语义未证/弱信号/线索/未定"): 0.
- Semantics length: 84-214 chars (all >=80).
- ⑮ body-hit sampling (8 rows, >5 required): 7/7,5/5,5/5,7/7,6/6,8/8,1/1,1/1 — all 100%.

## Deliverables
- coverage_delta.tsv; EVIDENCE/DISASM_FULL_*.txt (41 files)
- work/targets_41.json, work/new_semantics.json, work/disasm_verify.py, work/disasm_full.py

## Status: DONE
