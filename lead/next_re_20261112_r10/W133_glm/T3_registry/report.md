# T3_registry — status report (cancelled early, 2026-11-15)

**Verdict: `INCONCLUSIVE`** — subagent was cancelled by the lead before any binary
disassembly was executed. No push/pop classification has been performed yet.

## What was established before cancellation

All of the following was read from existing artifacts (function/class atlas TSVs,
calledges log). **No byte of gamemd.exe has been disassembled yet** — the analysis
script exists but was never run, so nothing below is disassembly-graded [已证]
against the binary itself; all rows are atlas/metadata facts `[已证: artifact]` and
interpretations are `[未证]`.

### 1. Target metadata [已证: class_atlas_v2.tsv]
- `.?AVAbstractClass@@` primary vtable = **0x7E1F50**; class has 4 vtables:
  0x7E1F24, 0x7E1F2C, 0x7E1F34, 0x7E1F50 (23 primary slots).
- Derived anchors: ObjectClass 0x7EF060, TechnoClass 0x7F4960, BuildingClass 0x7E3EBC,
  InfantryClass 0x7EB058, UnitClass 0x7F5C70, AircraftClass 0x7E22A4 (+ their
  secondary vtables, all listed in the atlas).

### 2. The 14 candidate functions [已证: function_atlas.tsv]
| fn | size | n_callers | is_fnptr | note |
|---|---|---|---|---|
| 00420960 | 399 | 1 | 0 | |
| 00420AF0 | 351 | 1 | 0 | |
| 00421730 | 207 | 0 | 1 | referenced only via pointer |
| 004C98B0 | 339 | 3 | 0 | |
| 004CA770 | 278 | 0 | 1 | referenced only via pointer |
| 004F54A0 | 4250 | 8 | 0 | **huge** (1023 instr, 27 callees) |
| 005F3900 | 577 | 19 | 0 | high caller count |
| 005F3B80 | 516 | 17 | 0 | high caller count |
| 0062DC50 | 705 | 21 | 0 | high caller count |
| 0062DF20 | 335 | 1 | 0 | |
| 0062E070 | 528 | 1 | 0 | |
| 006E8A90 | 833 | 5 | 0 | |
| 006E8DE0 | 616 | 1 | 0 | |
| 007258D0 | 830 | 63 | 0 | **very** high caller count |

### 3. Call-edge facts [已证: calledges.raw.log, format decoded]
Format of `calledges.raw.log` lines: `<caller> <callee> <callsite>`.
- `005F4EC0` calls `00420960` (site 005F5100); `006C6110` calls `00420AF0`
  (site 006C614C).
- Both `00420960` and `00420AF0` call `00410170` at entry+5 — consistent with an
  EH-prologue helper (`_EH_prolog`-style), typical of functions that construct
  objects with unwinding needs `[未证: helper identity not verified]`.

### 4. Interpretation so far [未证]
- The wide caller-count spread (1 … 63 callers, plus a 4250-byte monster at
  0x4F54A0 and two pointer-only-referenced functions) means the 14 sites are
  **not** a simple ctor/dtor pair picture. Some are likely shared helpers or
  non-ctor manipulation (bulk load/clear). This neither confirms nor contradicts
  the registry hypothesis.
- Nothing observed so far contradicts the claim that 0xB0F720 is a
  `DynamicVectorClass<AbstractClass*>`-style registry of game objects.

## Deliverables in this directory
- `t3_registry.py` — complete, deterministic, **never executed**. Implements:
  byte sweep of 0xB0F720/724/72C/730 over `.text`, per-function push/pop
  classification via Count-delta tracing, vftable-store extraction + RTTI name
  resolution, AbstractClass root-ctor/dtor scan (via vtable immediates), RTTI
  CHD-based coverage check over all 988 classes, `push_sites.tsv` + `evidence.json`
  + `dumps\`. Running `python -X utf8 t3_registry.py` will produce the full
  evidence set in one pass.

## What I would have done next (exact plan)
1. Run `t3_registry.py`; read `dumps\fn_00420960.asm` etc.
2. Classify the 14 as push/pop by Count delta (+1 vs −1) and identify owning
   classes via first vftable store per function.
3. Find functions storing vtable 0x7E1F50 (AbstractClass ctor/dtor candidates);
   check whether they touch 0xB0F724/0xB0F730 directly or call one of the 14.
4. Decide: root-ctor registration ⇒ `COMPLETE`; per-class ⇒ enumerate non-covered
   classes via RTTI hierarchy ⇒ `INCOMPLETE`; else `INCONCLUSIVE`.
5. Check the reverse (an AbstractClass dtor that does not unregister).

## Limits
- Everything above is static-artifact reading; zero binary code was decoded in
  this session. The verdict question remains exactly where it was: unproven.
