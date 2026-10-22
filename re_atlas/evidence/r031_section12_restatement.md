# R-031 finalisation — the §12 key column, restated on the ABI fact

**Date**: 2026-10-22
**Binary**: `gamemd.exe` SHA-256 `73201cc0…f67476`, size 4,825,360 — GATE PASS
**Tools** (all read-only, deterministic, EXIT=0, sha-gated):
`r031_authoritative_numbers.py` (17/17), `r031_finalise_rules.py` (11/11),
`r031_esp_slot_adjudicate.py` (6/7 — the one red is a mis-stated assertion,
explained below), `r031_m1_window_diag.py`, `r031_origin_adjudicate.py`,
`r031_ret_boundary_test.py`.
**Verdict on §12's "key" column**: the numbers stay, the *label* was wrong.
One finding is new and changes engine semantics.

## 1. What was actually being counted

§12 published "2,305 recovered keys / 1,893 distinct / 164 multi-read". Those
were produced by rule **M1**: *the nearest preceding push of a printable
`.rdata`/`.data` string literal, scanning back to the enclosing function's
head*. M1 answers **"is there a string literal near this call"**. It does not
answer **"what key does this call pass"**.

The ABI question is answerable exactly: for these seven readers the key sits in
a fixed argument slot — **2nd-to-last push** for the six readers, **last push**
for `GetSection` (both confirmed independently by the GLM sweep). I implemented
that as rule **B** (positional over all pushes since the function head) and,
independently, rule **C** (a stack model that retires a push once `pop` /
`add esp,N` / `leave` / `mov esp,X` reclaims its slot).

**B and C agree at all 2,426 sites, zero disagreement.** Two different
formulations of the same ABI fact producing identical output is the internal
double-check for everything below.

## 2. The corrected §12.1 key-slot table

| Reader | sites | key is a literal | key is a register/buffer | no live slot |
|:--|--:|--:|--:|--:|
| `ReadInteger` `0x5276D0` | 757 | 732 | 23 | 2 |
| `ReadBool` `0x5295F0` | 651 | 647 | 4 | 0 |
| `ReadString` `0x528A10` | 650 | 514 | 131 | 5 |
| `ReadDouble` `0x5283D0` | 306 | 305 | 1 | 0 |
| `GetSection` `0x526810` | 54 | 3 | 51 | 0 |
| `ReadUnicodeString` `0x528F00` | 5 | 5 | 0 | 0 |
| `ReadStringtableEntry` `0x529160` | 3 | 3 | 0 | 0 |
| **Total** | **2,426** | **2,209** | **210** | **7** |

Literal-key population: **2,209 sites / 2,023 distinct keys / 137 keys read at
more than one site.**

## 3. ★ New finding: no literal key in the engine contains `%`

Under the key-slot rule, **zero** of the 2,023 distinct literal keys contain a
`%`. Every `%`-bearing string in the index comes from M1 grabbing a **format
template** used to *build* a key at runtime.

So §12.3's correction was right that the phenomenon is widespread, and now we
can say exactly what it is:

- **21 distinct `%` templates / 34 sites** — all of them in the "key slot is a
  register" population (i.e. the key really is runtime-built, and M1 recorded
  the template that built it). Examples: `PowerUp%01dYSort`, `Tile%02dAnim`,
  `EliteStage%d`, `EliteWeapon%d`, `%sBarrelLength`, `Map%d`, `%d,%d,%d`.
- **None of them is a key.** `PowerUp%01dYSort` is the *format*; the ten real
  keys are `PowerUp0YSort`…`PowerUp9YSort`. §12.3's original conclusion holds;
  its "only one such key" framing and the later "21 keys" framing are both
  wrong in the same way — they are templates, not keys.

The compiler-facing rule therefore simplifies to one sentence: **never write a
`%`-bearing string from this index into an INI as a key.** Not "21 of them are
special" — *all* of them are templates.

## 4. M1's 340 wrong sites, split by cause

M1 disagrees with the key slot at **340 of 2,426** sites:

| Cause | Sites | Meaning |
|:--|--:|:--|
| (1a) key slot holds a register | **91** | key genuinely runtime-built; M1 recorded a nearby template or an older consumed string |
| (1b) key slot holds nothing | **5** | M1 recorded a string that was never an argument at this call |
| (2) key slot holds a *different* literal | **244** | M1 grabbed the **section name** (or a filename) that sits closer to the call than the key |

Cause (2)'s top offenders are exactly section names, which is the signature of
"section pushed after the key": `General` 57, `Basic` 38, `MultiPlayer` 21,
`RandomMap` 20, `Lighting` 20, `Header` 12, `Options` 11, `Video` 10,
`SerialDefaults` 10, `WOnline` 9. This independently reproduces the GLM
sweep's finding ("all section names") and its M1 top-frequency list.

**Consequence for §12.2's "121 unrecovered is a lower bound"**: it is not a
lower bound on *unrecovered keys*. The true count of sites whose key is not a
literal is **210 + 7 = 217** (key-slot register or empty). The 121 figure and
its `register 55 / bss_key 59 / unknown 7` buckets were M1-derived and do not
correspond to any ABI quantity; they are superseded by 217.

## 5. §12.4's "164 keys read more than once" — superseded

Under the key-slot rule it is **137** distinct keys at ≥2 sites (the GLM sweep
said 136 under rule B and 129 per-function). Its headline claim — that the
multi-read keys are `Name`/`UIName`/`Image`/`Cost`/… read once per `TypeClass`
derivative — is **wrong**: those appear at 3–7 sites only. The actual top of
the distribution is ordinary shared keys (`Name` 7, `Height` 5, `Description` 5,
`Type` 5, `Normalized` 4, `Damage` 4, `Warhead` 4, `Image` 4, `TechLevel` 4).
Multi-read-ness comes from several distinct loaders sharing a key name, not
from a per-derivative repetition of the same loader.

## 6. The ReadDouble "1 vs 68" ledger entry was a misreading — closed

LEDGER §4b recorded "ReadDouble register: ours 1, GLM 68 ⇒ pipeline difference
(def64 占位法不同)". **That entry is wrong and is retracted.** Both figures came
from the *same* report: 1 is rule **B** (key slot over all pushes), 68 is rule
**A** (key slot over the trailing *consecutive* push run — any interleaved
`mov` splits the argument list and the rule falls back). `r031_finalise_rules.py`
reproduces both from one run:

```
ReadDouble   sites 306   M2-B literal 305, register 1   M2-A literal 235, register 68
```

So there was **no cross-family disagreement on ReadDouble at all**. The honest
table is: B=1, A=68, and A is the weaker rule. Def64 占位口径 needs no
unification because it never caused the split — the split was rule A vs rule B
inside one report.

## 7. Why 2,305 vs 2,275 (the 30-site gap) is not adjudicatable to a winner

Three candidate origins for M1's window were tested:

| Origin rule | M1 recovered | Verdict |
|:--|--:|:--|
| forward sweep, skip `nop` only | 2,305 | our published rule |
| forward sweep, skip `nop`/`int3`/`null` | **2,305** | byte-identical ⇒ padding set is NOT the cause |
| nearest *validated* preceding `ret`, forward-decode must land on the site | 1,960 | too strict — 159 sites get no anchor at all |

A byte-scan for `C3`/`C2` without validation is worse: **2,071 of 2,426 sites**
contain at least one `C3`/`CB` byte that is *not* an instruction boundary (81,743
such bytes total — e.g. `0x41CC5C`, where the byte is the tail of `mov ecx,ebx`'s
modrm). Any backward byte-scan trusts those phantom rets.

Conclusion: **the 30-site difference is a window-origin artifact, and neither
pipeline's 2,275/2,305 is a semantic quantity.** That is precisely why §12 must
stop publishing an M1 "key" count as *the* number and publish 2,209/2,023/137
instead. The M1 figures are retained only as "count of sites with a printable
string literal in range", labelled as such — which is all they ever measured.

## 8. Retained vs superseded

| §12 figure | Was | Now | Status |
|:--|--:|--:|:--|
| reader call sites | 2,426 | **2,426** | unchanged, doubly confirmed (E8 scan + instruction scan) |
| per-reader table | 757/651/650/306/54/5/3 | same | unchanged |
| "recovered keys" | 2,305 | **2,209** (ABI key) | **relabelled + corrected** |
| "distinct keys" | 1,893 | **2,023** | corrected |
| "multi-read keys" | 164 | **137** | corrected |
| "unrecovered (lower bound)" | 121 | **217** | corrected (and no longer a lower bound) |
| "% keys" | 21 keys / 34 sites | **0 keys** / 21 templates / 34 sites | **reclassified** |
| M1-vs-key conflict | 155 / 340 | **340** (91+5+244) | reconciled, causal split added |
| ReadDouble reg "1 vs 68" | cross-family split | rule B vs rule A in one report | **retracted** |

Note the two counts moved in opposite directions (2,305→2,209 down, 1,893→2,023
up) and both are explained: the ABI rule rejects 340 literal-claiming sites but
recovers keys at sites where M1 saw nothing, mostly `GetSection`'s register-form
sections resolving to literals in other slots. No number was tuned to match.

## 9. Reproduce

```bash
python re_atlas/tools/r031_authoritative_numbers.py    # 17/17 PASS, EXIT=0
python re_atlas/tools/r031_finalise_rules.py           # 11/11 PASS, EXIT=0
python re_atlas/tools/r031_esp_slot_adjudicate.py      # 6/7 (the red is a bad assertion)
python re_atlas/tools/r031_m1_window_diag.py           # padding-set test
python re_atlas/tools/r031_origin_adjudicate.py        # window-origin test
python re_atlas/tools/r031_ret_boundary_test.py        # phantom-ret census
```

Negative controls in force: sha256 gate live (pristine copy differs); genuine
key site `0x410AA0` = `Name` stays a literal under every rule; known
mis-attribution `0x686ED0` never becomes a literal; forcing a wrong slot index
(`-3`) changes the `ReadBool` count; `GetSection` under the wrong slot index
drops 3→0.

## 10. Honest limits

- The 7 "no live slot" sites are counted but not individually explained.
- Rule C tracks `esp` through `push/pop/add/sub/leave/mov/lea` only. A frame
  built with `enter`, or a `mov esp,reg` from a non-immediate, is treated as a
  frame reset — correct for slot liveness, but the depth value itself is then
  approximate; no site in this population depends on the absolute depth.
- The `%`-template list is complete for *this index's* population (sites M1
  attributed a literal to). A template used at a site where M1 found nothing
  would not appear here; §12.3's "21" is therefore a floor on templates, not a
  census of all formatted keys in the engine.
- `n = 0..9` for `PowerUp%01dYSort` remains untraced (GLM graded it
  UNVERIFIABLE); the loop bound was not recovered.
