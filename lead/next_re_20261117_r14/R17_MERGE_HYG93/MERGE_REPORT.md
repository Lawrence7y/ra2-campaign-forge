# R17-MERGE-HYG93 MERGE REPORT

## Before / After triples (bytes / mtime / sha256)

| | bytes | mtime | sha256 |
|---|---:|---|---|
| before | 4136525 | 2026-11-21T11:20:04.989272+08:00 | a07a74c173286b4d2163831022f1498f9ee903f44690702c90d05edea6d1c40c |
| after  | 4147334 | 2026-11-21T12:56:21.297199+08:00 | c2ee063fd4f61f784585ef2abcc4ff563fa09ec1b1f7f5079643076e359c744a |

sha256 prefix: before `a07a74c17328` -> after `c2ee063fd4f6`.
Baseline cross-check against `R17_LEAD_BASELINE/coverage.before_hyg.tsv` (prefix `A07A74C1`): PASS.

## Assertions N1-N8 (measured)

- **N1**: data rows before=18498 after=18498; expected 18498. Each row 8 columns. Header bytes unchanged: PASS.
- **N2**: exactly 93 data rows changed, 18405 data rows byte-identical (expected 93 / 18405, header excluded). Changed-line set == delta-line set: PASS. Only col4 differs on every changed line: PASS.
- **N3**: 91 append rows: every one has `len_after - len_before == 65` and `after == before + SENTENCE`: PASS.
- **N4**: 2 replace rows (`004AF540` @2698, `004B5AB0` @2777): old segment occurred exactly once at tail, removed; result contains no `§12.6` substring, still contains `④ direct call`: PASS.
- **N5**: grade counts unchanged: `[已证] 1654 / [静态推断] 5875 / [未证] 10969`: PASS.
- **N6**: `§12.6` hits before=234 -> after=323 (expected 234 -> 323 = 234+91-2): PASS.
- **N7**: `§12.4` before=0 after=0 (expected 0); `CLSID None` before=0 after=0 (expected 0): PASS.
- **N8**: ④ measures unchanged: A=458 (expect 458), B=291 (expect 291), wide=293 (expect 293), no-④=1196 (expect 1196): PASS.

## Changed lines (93 line numbers)

```
1444, 2698, 2777, 3231, 3942, 5291, 5360, 5443, 5445, 5446, 5447, 5448, 5449, 5450, 5465, 5466, 5467, 5468, 5473, 5474, 5475, 5476, 5478, 5506, 5507, 5873, 5875, 5876, 5877, 5878, 5879, 5880, 5955, 6291, 6292, 6309, 6399, 6400, 6401, 6402, 6424, 6425, 6434, 6435, 6436, 6439, 6440, 6442, 6450, 6451, 6452, 6453, 6454, 6699, 6704, 6711, 6713, 6715, 6716, 6717, 6719, 6721, 6724, 6725, 6726, 6728, 6729, 6730, 6735, 7895, 7899, 8523, 8778, 8808, 9535, 10870, 10871, 12206, 12207, 12212, 12213, 12215, 12216, 12217, 12218, 12219, 12220, 12224, 12225, 12226, 12227, 12228, 12229
```

Full per-line detail (line, entry, kind, len_before, len_after) is in `changed_rows.tsv`.

## Files

- `merge.py` — re-runnable script (this file's logic)
- `coverage.before.tsv` — full pre-merge copy, sha256 `a07a74c173286b4d2163831022f1498f9ee903f44690702c90d05edea6d1c40c`
- `changed_rows.tsv` — 93 rows, one per changed line
- `MERGE_REPORT.md` — this report

Readback after single atomic write: bytes=4147334, CR count=0, sha256=c2ee063fd4f61f784585ef2abcc4ff563fa09ec1b1f7f5079643076e359c744a.
