# T4 textcov — gamemd.exe uncovered .text analysis

## VERDICT: INCOMPLETE (cancelled early)

Cancelled by lead at 2026-11-15T14:23+08:00 for slot management before the candidate-recovery
phase could run. **Only the coverage recomputation was executed** (`t4_coverage_min.py`,
ran once, exit 0, wrote `uncovered_runs.tsv`). The full disassembly/validation pipeline
(`t4_textcov.py`) is **written but never executed** — [未证] it even runs; treat it as a
hand-off artifact, not a result.

## What was measured [已证]

Recomputed from `function_atlas.tsv` (12,916 rows) over `.text` 0x401000..0x7E038D
(4,060,045 bytes), interval math only, no disassembly:

| metric | value |
|---|---|
| total `.text` bytes | 4,060,045 |
| atlas-covered bytes | 3,225,835 = **79.453%** |
| uncovered bytes | 834,210 = **20.547%** |
| uncovered runs | **11,703** |
| **79.5% claim** | **RIGHT** (79.453% rounds to 79.5%) |

### Size-column interpretation [已证, important]

The task said "hex addresses". Recomputation shows the atlas **entry** column is hex but the
**size** column is **decimal**: size-as-hex makes 81.24% of functions overshoot the next
entry's start (physically impossible); size-as-dec gives 0.02% overshoot (2/12,915).
All numbers above use size-as-dec. Under size-as-hex covered would be 3,801,059 (93.6%) — wrong.

### Uncovered run size distribution [已证]

| bucket | runs |
|---|---|
| 1–15 B | 9,463 (inter-function CC padding, presumably) |
| 16–63 B | 899 |
| 64–255 B | 714 |
| 256 B–1 KB | 521 |
| 1–4 KB | 85 |
| 4–64 KB | **21** ← the interesting ones |

Largest runs (start–end:size): `614B25-61EF70:42059`, `610B44-6149B0:15980`,
`56134C-565090:15684`, `78AC02-78DB70:12142`, `45AF95-45DD20:11659`,
`68CB06-68F060:9562`, `78F6A6-791AA0:9210`, `60D519-60F4B0:8087`,
`4E62CD-4E8240:8051`, `756BA5-7568670:6859`(7,085). Full list in `uncovered_runs.tsv`.

Whether the 21 large runs (+521 mid-size) are real missed functions, jump tables, or inline
data **was not determined** — that is exactly the cancelled phase.

## What remains (pipeline ready, unexecuted)

`t4_textcov.py` implements the full method: candidate entries from call/jmp/jcc xrefs out of
atlas-decoded code, imm/disp pointers, `.rdata`/`.data` pointer scan, vtables_canonical.json
(structure recon'd: `{"vtables":[{vt,col,class,...}]}`, decimal addrs), jump-table detection
(scale-4 ref + monotonic/dense pattern), CC-preceded prologues (weak evidence), strict
decode validation (clean to ret/jmp terminator, no overlap), 3 waves, byte classification
into accepted/padding/tables/unexplained. It has never been run; first execution will likely
need a bug-fix pass.

## Files

- `t4_coverage_min.py` — ran once, deterministic, exit 0 [已证]
- `uncovered_runs.tsv` — 11,703 rows [已证]
- `t4_textcov.py` — full pipeline, UNRUN [未证]
- `report.md` — this file
- `candidates.tsv`, `new_functions.tsv`, `unexplained_runs.tsv` — **not produced** (cancelled)

Atlas SHA-256 [已证]: `4527079B8E1556F0F34BC2C16068DDAEF7681EE2B6A5E1F2AADC61A73653DB69`.
