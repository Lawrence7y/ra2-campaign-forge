# S15-K7 DISAGREE

## D1 · baseline double-count corrected
Initial local t0 script added K3/K4 deltas to live coverage, producing 142; live coverage already contains those names. Corrected recompute returns the card baseline 141/158=89.24%, proved 98/158=62.03%, need 143, shortfall 2. See EVIDENCE/baseline_recompute.txt. No disagreement with the card after correction.

## D2 · prior cards said “no source name” for 006E6310/006F1920/00727AA0
S15-K4/K5 searched for explicit YRpp address literals or explicit FindByNameOrID names and concluded no source name. This card uses a different source-level channel: ABSTRACTTYPE_ARRAY's macro-generated FindOrAllocate, instantiated with the exact class/array address. This is the same channel shape S13-N1 used for FindIndex and its audit accepted. Prior cards were correct that no literal address exists; their “no source name” conclusion is superseded for these three entries, not silently overwritten.

## D3 · strings are sentinels, not INI keys
S15-K5 reported only <none>/none sentinel hits in finder bodies; this card reproduces that. Caller-side strings Tag/Teams and the macro's sentinel guard are used only as corroboration inside the binary channel, not as independent INI-key evidence.

## D4 · channel count
Binary body, RTTI, caller xrefs, and conflict search are one channel (same binary/repository evidence); YRpp source macro/header is the second. n_sources=2 for each row, satisfying discipline 17.

## D5 · write scope
Only lead/next_re_20261117_r14/S15_K7/ written; no COVERAGE/, ledger, ra2youli/ game file, or git commit.
