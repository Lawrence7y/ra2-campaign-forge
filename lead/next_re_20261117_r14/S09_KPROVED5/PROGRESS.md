# S09-KPROVED5 PROGRESS

Card: S09-KPROVED5. Target: `ra2youli\gamemd.exe` RO — SHA-256 `73201CC0…F67476` (full value verified on disk).
Task: 8 rows only, from S09 A-set (A=103, strict direct-call caliber 102) not yet merged.

## Read (mandatory)
- R14_COMMON §1/§6/§7/§8.1/§8.5/§8.6(6条)/§8.7(9条) — all read.
- D-40 / D-41 / D-42 (PENDING_DECISIONS.md) — all read. SURVEY_RING24/PROGRESS.md — read.

## Key numbers
- S09 A set (②仅RTTI ∩ ④严格档) = **103 rows**: direct-call **102**, livevt-only **1** (`004F4240`, not selected — no direct site).
- Prior 4 deltas = **27** entries; of those **22** are `[已证]` (really merged) + **5** still `[静态推断]`. Excluded ALL 27 (superset) + `00654320`(③a) + `0069DEB0`(细则#1 fail). Eligible pool = **74** rows (all `[静态推断]`, direct-call caliber).
- ③b BASE RATE (population 629 S09 rows, seed 20261119, 2000 draws of 8, no replacement):
  strict = **123/629 = 0.195548** (19.55%); loose = **144/629 = 0.228935** (22.89%).
  strict mean/draw 1.594, loose 1.867. `K=8×mean_per_row` is an identity, not a validation (M3).

## The 8 rows (all four rings solid → all into delta)
| entry | ② 归属(common base, all holding tables enumerated) | ③b 档 | ④ direct sites |
|---|---|---|---|
| 006D0270 | TabClass::slot50 (3 tables) | ③b④ 完整有界I/O循环(+0x000E..+0x003A, 显式写) | 2 ok |
| 006D04F0 | TabClass::slot54 (3 tables) | ③b① 互斥闸链+③b④ 双有界循环 | 4 ok |
| 00653850 | RadarClass::slot10 (1 table) | ③b① 多域互斥闸链 | 1 ok |
| 004F4480 | GScreenClass::slot15 (9 tables) | ③b① 多状态互斥闸链 | 26 ok |
| 004A8960 | DisplayClass::slot42 (7 tables) | ③b① 多状态互斥闸链 | 2 ok |
| 006C6680 | StaticButtonClass::slot33 (1 table) | ③b① 三态互斥闸链 | 1 ok |
| 004F4320 | GScreenClass::slot9 (9 tables) | ③b① 双域互斥分派 | 4 ok |
| 006AC210 | SidebarClass::slot33 (1 table) | ③b① switch状互斥值分派 | 1 ok |

## Verification / disciplines
- ② full 1214 RTTI tables enumerated (14044 slots, independent of atlas); 2+ tables at same slot → base-level (错源⑯/M1); name column = ② class (M2) — selfcheck PASS.
- ③b each manually verified against DISASM (rejected S4 false-positive `0063F730`=③a clear; rejected `006A5BF0`/`0069DE00` same-action gates fail 细则#1) — see UNKNOWNS U3 / DISAGREE D3/D4.
- ④ full .text E8 sweep (1,392,592 instructions / 68,253 E8@boundary); site containment by self-written CFG extent (function interval, not entry_at_or_before); all sites out-of-body, non-self, site+5+rel32==entry.
- Offsets entry-relative +0xNN, identical to EVIDENCE/DISASM (M5) — selfcheck PASS.
- one_line_semantics carry ③b-level whole contract, no self-declared-unproven tokens (M8) — selfcheck PASS.
- delta rows = self-reported = 8 (M6/判据7). ②∧④ selection rate (103/629) NOT used as baseline (判据4).

## Deliverables
`coverage_delta.tsv` (8 rows + header) | `UNKNOWNS.md` | `DISAGREE.md` |
`EVIDENCE/`: VTABLES_ALL8.tsv, CLASS_ATTRIB8.tsv, CONTRACT_3B.tsv, DIRECT_SITES_8.tsv,
BASELINE_3B.{json,txt}, BASELINE_3B_FEATURES.tsv, DISASM_<entry>.txt (74 candidates), VTABLES_ALL.tsv |
`work/`: extract_A.py, build_pool.py, s09lib.py, analyze_all.py, detect_cfg.py, fix_attrib.py,
baseline.py, gen_final.py, selfcheck.py + JSON intermediates.

## Result
8 of 8 candidates four-ring complete → delta = **8 rows**.
All 16 disciplines + 9 §8.7 criteria self-check PASS. No game files changed, no venv/pip, no git commit, no ledger/status edits.
