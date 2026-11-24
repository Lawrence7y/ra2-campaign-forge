升了 8 行 / 最多 8 行

# S08-KPROVED2 PROGRESS

- Card: S08-KPROVED2 · target 8 rows · status: complete
- Write domain used: card directory + `_ghidra\S08-KPROVED2\` only; `ra2youli\gamemd.exe` read-only.
- Toolchain: system Python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26; no venv, no pip install.

## ① Upgraded rows (8)
`0045A680` · `0045A730` · `0045AB50` · `0045AC30` · `004D24A0` · `004D2510` · `004D27D0` · `004D2810`
All rows: name unchanged, only grade `[静态推断]→[已证]` and one_line_semantics changed.

## ② Per-row ② channel + ③b condition
- `0045A680` / `0045A730`: RTTI vt `007E44F4` slot2/slot4; ③b = 6-guard + copy loop + falsifiable bool / -1.
- `0045AB50` / `0045AC30`: inherited slots vt `007E44F4` slot10/slot12; ③b = same SetCapacity / FindItemIndex contracts.
- `004D24A0` / `004D2510`: FoggedObjectClass vt `007E8B38` slot6/slot5; ③b = ≥3 guards + 16-byte stream loops + negative error return.
- `004D27D0`: vt `007E8B38` slot3; ③b = E_POINTER `0x80004003` + 4-field write.
- `004D2810`: vt `007E8B38` slot13; ③b = 14 field layout assertions (`+0x24..+0x6C`) ≥10.

## ③ ④ use witness
- Direct E8 hits to all 8 entries = 0 (`EVIDENCE/DIRECT_CALLS.tsv`).
- Dynamic vector live vtable: ctor site `00457BFD` writes `007E44F4`; slot sites `007E44FC/4504/451C/4524`.
- FoggedObject live vtable: ctor `004D0860` / site `004D088D` writes `007E8B38`; slot sites `007E8B50/8B4C/8B44/8B6C`.
- No atexit destructor table used for ④; `0x7C978A` at `004D0810` is outside ctor `004D0860`.

## ④ Random baseline / weak vs strong
- Population = S08 `[静态推断]` candidate pool n=19; draw k=8 rows.
- Weak (④ only): 19/19 → random mean 8.000; strong (④+③b): 8/19 → random mean 3.3684.
- Weak−strong mean gap = 4.6316 rows; row diff = 11 entries (listed in `EVIDENCE/weak_vs_strong.tsv`).
- Exact P(all 8 strong by random draw) = 1/C(19,8) = 1.323e-5 (75582 denominator); 4×20k seeds in `EVIDENCE/baseline.json`.

## ⑤ Counts / ⑨ recompute
- Disk before merge: S08 n=22 / proved=3 / `[静态推断]`=19 / `[未证]`=0.
- After applying `coverage_delta.tsv`: n=22 / proved=11 / `[静态推断]`=11 / `[未证]`=0; named(L)=20 unchanged.
- ⑱ conflict scan: 8 entries, 6-digit and 8-digit forms checked; no subsystem/name/grade conflict (`EVIDENCE/conflict18.tsv`).
- ⑲ Capstone selfcheck: no `op.index`; `op.mem.index` on memory operand without index = 0 (`EVIDENCE/scan_stats_v2.json`).
- `.text` VirtualSize `0x401000..0x7E038D`; rooted scan selfcheck 1,377,695 instructions / 67,154 `E8`@boundary; card baseline 1,392,592 / 68,253 recorded in `DISAGREE.md`.

## Deliverables
- `coverage_delta.tsv` (8 rows, 8 columns), `UNKNOWNS.md`, `DISAGREE.md`, `PROGRESS.md`, `EVIDENCE\`, `work\`.
- Key evidence: `EVIDENCE/PROOFS.md`, `S08_RTTI_FIXED.tsv`, `VT_SLOT_MAP.tsv`, `VT_BROAD.tsv`, `baseline.json`, `conflict18.tsv`, `DISASM_FN_*.txt`.
