# S13-K12 UNKNOWNS / method boundaries

1. C2 36 rows not evaluated: D-39 undecided. This card touches only the 17 C1 rows.
2. The 17 rows carry placeholder names (vslotN/slotN). Per card rule names/subsystem are NOT changed; only grade is raised. one_line_semantics kept verbatim from coverage.tsv. Semantic method names (SetCapacity/FindItemIndex/Clear) are recorded in EVIDENCE/four_rings.md R3 as byte-contract evidence only, NOT written into the delta name column.
3. Ring4 exact-dispatch scan recognizes mov reg,[global] + mov ecx,global + call [reg+slot] with a live install (mov [global],vt) and vt[slot]==entry. Rarer equivalent forms not enumerated; this is a conservative lower bound (misses would leave rows [静态推断], never create false positives). The S13-wide scan found exactly 17 hits == the 17 targets.
4. RTTI class names read per R14_COMMON 8.2.7: vt-4=COL -> COL+0xC=TD -> TD+8 inline ASCII; fail-closed. All 17 resolved; none read from PAU/PAV template prefix (rule 22).
5. 017 same-source non-double-count: for these virtual functions, R3 (in-body byte contract) and R4 (out-of-body exact dispatch site with global write witness) are physically disjoint byte evidence (function body vs call sites+install site), NOT the same entry->vt scan split in two. Ring2 RTTI and Ring4 install witness are separate addresses.
6. Baseline false-positive measured on same-subsystem pool (112 rows, seed 20261118), 0/17; consistent with precision=recall=100% over all 240 S13 rows. This specificity comes from slot-value==entry, unlike the weaker C2 baseline (15%).
7. No venv / no pip install used; python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26 (system).
