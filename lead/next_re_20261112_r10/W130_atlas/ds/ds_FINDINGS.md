# ds-rtti-provenance — independent adversarial audit

Binary: `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe` (read-only)
SHA-256 verified = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ✅
Artifact under test: `_lead_rtti_map.json` (`vt2name`, 1305 entries)

**Layer discipline honoured:** `pefile.get_memory_mapped_image()`, index 0 == ImageBase
`0x400000`, absolute VA index = `VA - 0x400000`. Proven, not assumed:
`IMG[0:2] == b'MZ'` and `IMG[.text.va-BASE:+8] == RAW[.text.raw:+8] == 5356578bf1ba0040`.

All scripts under
`D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\ds\`.

---

## VERDICT lines

**P1: CONFIRMED** — 87 `.text` entries reproduced exactly; all are compiler-immediate
false positives inside real instructions; the COL is fabricated from the immediate itself.

**P2: REFUTED** — Neither `0x007E1F24` nor `0x007E1F2C` is a vtable *start*. There is no
systematic offset; there is an *abutting* thunk-table pair plus an inherent COL/table
aliasing. No single "remembered address" offset exists to correct.

**P3: REFUTED** — `+0x2C = WhatAmI()` is not a general rule. Only **144** (not 185) are
genuine small-ordinal WhatAmI; the other 1161 read ordinary virtual slots, adjacent
tables' COL headers, or BSS.

---

# P1 — the 87 `.text` "virtual tables"

## Reproduction
| section | entries |
|---|---|
| `.rdata` | 1212 |
| `.data` | 5 |
| `.rsrc` | 1 |
| **`.text`** | **87** |
| total | 1305 |

Exact match to the claim. `0x00443B24 → .?AVDropPodLocomotionClass@@`,
`0x0045CC44 → .?AVShapeButtonClass@@`, `0x0046C2D8 → .?AVMSPCXAnim@@` all confirmed present.

## Real nature: compiler immediates, not tables
Linear sweep of `.text` with `md.skipdata = True`:
1 392 592 instructions, 4 060 045 bytes covered == `.text` VirtualSize exactly (full coverage).

**All 87 addresses land *inside* an instruction — 0/87 are instruction boundaries.**
Control: 87 random instruction boundaries → 87/87 hit; 87 random byte offsets → 26/87
(≈ the base rate of being a boundary), so "inside an instruction" is a real signal, not an artefact.

Sample disassembly (`0x00443B24`, key for `DropPodLocomotionClass`):
```
0x00443B1C  813dc802a80080000000  cmp dword ptr [0xa802c8], 0x80
          ^^^^ 0x00443B20 = 0x00800000
                 0x00443B24 = 0x008000A8  <-- "vt address", = the imm32 of this cmp
0x00443B26  0f8d42ffffff          jge 0x443a6e
```
The 4-byte "COL" the producer inventes is the *middle of the immediate*
`00 80 00 00` = `0x00800000`, and `+0x0C` past it lands on the real `.rdata` COL
at `0x0080000C`. Other witnesses:

- `0x0045CC40: b8 ff7f 0000` `mov eax, 0x7fff` → slot `0x0045CC44` = `0x007FFFB8`
- `0x0046C2D5: 68 80000000` `push 0x80` → slot `0x0046C2D8` = `0x00806814`
- `0x0049DCCD: 68 80000000` `push 0x80` → slot `0x0049DCD0` = `0x00806808`
- `0x005FF69D: b8 80000000` `mov eax, 0x80` → slot `0x005FF6A0` = `0x0080B8C8`
- `0x005DA89A: c802a800` `enter -0x57fe, 0` → slot `0x005DA8A0` = `0x008000A8`
- `0x00659BAC: dc8e 80000000` `fmul qword ptr [esi+0x80]` → slot `0x00659BB0` = `0x00808EDC`
- `0x007CB8A0: e8 7b800000` `call 0x7d3920` → slot `0x007CB8A4` = `0x00807BE8`

## Where the COL came from — exact mechanism
The producer's loop-2 rule is *"any aligned dword whose value is a TypeDescriptor VA"*.
For a `.text` dword at `va_i`, `col_va = va_i - 0x0C`, and the fabricated COL's `pTD`
field `col_va+0x0C` == `va_i` itself. So the chain is:

```
.text immediate (e.g. 0x00806814)
   -> u32 of that .rdata COL = 0x00830158 (a TypeDescriptor)
   -> producer fabricates COL at 0x00806814, "pTD" = 0x00830158
   -> key = 0x00806818, reported as .?AVMSPCXAnim@@   ((the real COL is MSE 0x00806814))
```
Verified: `u32(0x006AB214) = 0x00806814`; `0x00806814` is **not** a TypeDescriptor, but
`u32(0x00806820) = 0x00830180` **is** — that is the genuine next COL.

## Blast radius
Only **9 distinct class names** are polluted (0 are exclusively `.text`):

| class | `.text` bogus keys |
|---|---|
| `.?AVShapeButtonClass@@` | 40 |
| `.?AVMSPCXAnim@@` | 29 |
| `.?AVDropPodLocomotionClass@@` | 8 |
| `.?AV?$TypeList@PBVSmudgeTypeClass@@@@` | 4 |
| `.?AVScriptClass@@` | 2 |
| `.?AV?$DynamicVectorClass@PAVShadowControlClass@@@@` | 1 |
| `.?AVMSPrintAnim@@` | 1 |
| `.?AVParticleClass@@` | 1 |
| `.?AV?$BlitTransLucent25Alpha@G@@` | 1 |

**Reassuring:** all 87 classes keep their real `.rdata` tables elsewhere in the map,
so nothing is masked — the 87 are *additive* false bindings, not overwrites of correct data.

**Strict rebuild** (`sig ∈ {0, 0xFFFFFFFF}` **and** `u32(col+0x0C)` is a TypeDescriptor):
```
json keys 1305 | strict keys 1274 | both 1274 | json-only 31 (.text) | strict-only 0
name disagreements on the 1274 intersection: 0
```
→ The producer is 100% correct on non-`.text`, and 0% correct on `.text`.
A two-condition guard would have removed all 87 for free.

---

# P2 — `0x007E1F24` vs `0x007E1F2C`

## Neither is a table start
Raw window (`ds_a4_p2.py`):
```
0x007E1F20  0x007FAFD8  COL(AbstractClass)  sig=0x0 off=0x0C cd=0
0x007E1F24  0x00410590  code
0x007E1F28  0x007FAFF0  COL(AbstractClass)  sig=0x0 off=0x08 cd=0
0x007E1F2C  0x00410580  code
0x007E1F30  0x007FB008  COL(AbstractClass)  sig=0x0 off=0x04 cd=0
0x007E1F34  0x004105E0  code
0x007E1F38  0x004105F0  code
0x007E1F3C  0x00410600  code
0x007E1F40  0x00410210  code
0x007E1F44  0x00410220  code
0x007E1F48  0x00410230  code
0x007E1F4C  0x007FB118  COL(AbstractClass)  sig=0x0 off=0x00 cd=0
0x007E1F50  0x00410260  code
```
The slot-1/3 values `0x007FAFF0` / `0x007FB008` are exactly what the brief observed,
and they are **COLs**, not data. The window is an interleaved **thunk-table family** for
sub-objects with member displacements `mdisp = 0x0C, 0x08, 0x04, 0x00` — i.e. the
`[vt-4]` COL headers belong to the *other* subobject vtables physically woven through this
run. A table's "start" is `COL_addr + 4`, and several such starts sit at odd interleaving
positions. **`0x007E1F24` and `0x007E1F2C` are both interior slots of that superstructure**
(`0x007E1F28`–`4` and `0x007E1F30`–`4` respectively are their COLs).

## There is NO systematic offset
This is the part of the hypothesis that must be rejected, and the evidence is unusually
clean. The producer's three loops reproduce byte-for-byte:
```
col2name size 2193 == json col_count 2193
derived vt2name == json vt2name  (exact dict equality: True)
for all 1305 keys: u32(key-4) has u32(key-4+0x0C) ∈ TypeDescriptors  -> 1305/1305
```
So the key is *already* `COL + 4`, and `key-4` is *already* the COL. Checked directly:

```
k is a COL  with matching name : 0
k is a TABLE (k-4 is a COL)     : 1305   <-- 100%
```

Every entry is recorded at the true MSVC table start. **The "remembered address = COL
address" hypothesis is falsified for all 1305 records.** Across the 1212 `.rdata` tables,
inter-table distances in slots are `{8:335, 2:184, 6:157, 7:86, 10:69, 4:67, 12:29, ...}`
— no constant to remove.

## The real defect here is COL aliasing
Because one physical run of slots is reachable from several COLs (one per `mdisp`), and
the producer keys by address, a single table start can pick up multiple class names.
`0x007E1F24` and `0x007E1F2C` are simply two neighbouring start positions each with its
own COL — both legitimately `AbstractClass` because they are sub-object vtables of the
same class. That is *correct* MSVC layout, not a producer bug.

---

# P3 — `+0x2C = WhatAmI()`

## The 185 is not 185 genuine WhatAmI
Full classification of slot `+0x2C` across all 1305 (`ds_a11_p3proof.py`, `ds_a13_disamb.py`,
`ds_a14_outliers.py`):

| what `+0x2C` points at | n |
|---|---|
| ordinary virtual method (real `.text` prologue, not `mov eax,N;ret`) | 638 |
| **`mov eax,IMM32; ret` where IMM32 is a POINTER** (`GetType()`-style, not an ordinal) | **41** |
| genuine `mov eax,smallN; ret` (N < 200) | **144** |
| `.rdata`/`.data` data — the adjacent table's COL header | 295 (286 + 9) |
| `.data` BSS (no file bytes at all) | 134 |
| slot is `0x00000000` | 31 |
| `.text` `ret` only | 3 |
| `xor eax,eax; ret` (returns 0, not an ordinal) | 19 |
| **total (sums exactly to len(vt2name))** | **1305** |

`638 + 41 + 144 + 295 + 134 + 31 + 3 + 19 = 1305` ✅

## Evidence #1 — the 41 "large N" are pointer-returning getters, not WhatAmI
These are NOT data corruption. The bytes are a perfectly real, intentional
`mov eax, <pointer to .data>; ret`:
```
fn=0x00535EA0  bytes = 90..90 b8 4870 8200 c3 90..   ->  mov eax,0x827048 ; ret
fn=0x00535F30  bytes = ...    b8 8070 8200 c3         ->  mov eax,0x827080 ; ret
fn=0x00535DE0  bytes = ...    b8 1470 8200 c3         ->  mov eax,0x827014 ; ret
fn=0x00535D20  bytes = ...    b8 1c70 8200 c3         ->  mov eax,0x826FC8 ; ret
```
Each `IMM32` is inside `.data`, and each belongs to exactly one class:
`CreateTeamCommandClass`, `SetInfantryTabCommandClass`, `SetUnitTabCommandClass`,
`SetDefenseTabCommandClass`, `SetStructureTabCommandClass`, `VeterancyNavCommandClass`, …

The slot-offset convention itself is proven by the neighbouring entries: on
`key=0x007EB874` (`SetInfantryTabCommandClass`) the *same* `0x00535EA0` sits at `+0x04`
instead. So this family stores `GetType`-style accessors *and* the true WhatAmI at
different indices — `+0x2C` happens to land on the getter. **N ranges up to 8 551 228** —
a nonsensical class ordinal, which is what exposed this.

## Evidence #2 — the 295 data targets are the *next table's* COL header
The value at `+0x2C` is literally the `[vt-4]` COL of an abutting table. 285/286 `.rdata`
targets are COLs already present in the map. Sorted-`starts` bisect over the 1212
`.rdata` tables:
```
+0x2C lands inside table at +0x0C : 365
+0x2C lands inside table at +0x2C : 271     <- only these can be the real slot
+0x2C lands inside table at +0x14 : 157
+0x2C lands inside table at +0x04 : 115
+0x2C lands inside table at +0x08 :  99
+0x2C lands inside table at +0x00 :  97
before first table               :  87     <- the .text false keys
```
Byte witnesses:
```
key=0x007C69B8 .?AVShapeButtonClass@@  +2C=0x007FFFB8
   0x007FFFB8 bytes = 00000000 00000000 00000000 b8028200   (a COL: sig=0, off=0, cd=0, pTD)
key=0x00669608 .?AVMSPCXAnim@@         +2C=0x00806814
   0x00806814 bytes = 58018300 f8678000 00000000 80018300   (a COL header)
```
**When the table is too short, `+0x2C` does not "return nothing" — it reads the next
structure's header and silently produces a garbage "method".**

## Evidence #3 — the 134 BSS targets have no bytes at all
```
key=0x00443B24 .?AVDropPodLocomotionClass@@  +2C=0x00D00D8B00   (= "mov ebx,0x...", is code)
key=0x0045CC44 .?AVShapeButtonClass@@        +2C=0x24448B12
key=0x0048CA50 .?AVDropPodLocomotionClass@@  +2C=0x8900A802
key=0x006AB20C .?AVDropPodLocomotionClass@@  +2C=0x00A802C8   (real .data BSS >= 0x0087E000)
key=0x00877000 .?AVDropPodLocomotionClass@@  +2C=0x00A00060   (real .data BSS)
key=0x0087B17C .?AVDropPodLocomotionClass@@  +2C=0x00A00060   (real .data BSS)
```
For the `.text`-derived keys these are *instruction bytes* reinterpreted as a pointer
(`0x00D00D8B00` is the LE encoding of `8B 0D D0 02 A8 00` = `mov ecx,[0xa802d0]`).
Resolved `offset_in_section < RawSize` first: `.data` has file bytes only to `0x0087E000`.

## Evidence #4 — `+0x2C` is real but *not canonical* (offset sweep)
At the 144 genuine keys, `+0x2C` does win, but not by a margin that justifies "普遍规律":
```
+0x04  88   +0x08  88   +0x20  73   +0x24  86   +0x28  76
+0x2C 144   +0x30 105   +0x34  82   +0x00   0
```
Any slot `0x00`–`0x3C` yields *some* `mov eax,N;ret` for **348/1305** keys, and 322 of those
have 2–4 such slots. "The first slot that looks like `mov eax,N;ret`" is a coin flip among
neighbours for most tables.

## Sampling requirement — 8 concrete witnesses
Already given above; consolidated list of 8 distinct, each with bytes:
1. `0x00535EA0` `b848708200c3` — real fn, returns a *pointer* (`+0x2C` of `CreateTeamCommandClass`)
2. `0x00535F30` `b880708200c3` — ditto (`SetInfantryTabCommandClass`)
3. `0x007C69B8` `+0x2C → 0x007FFFB8` — `.rdata` COL (`00000000 00000000 00000000 b8028200`)
4. `0x00669608` `+0x2C → 0x00806814` — next table's COL (`58018300 f8678000 ...`)
5. `0x007E1B44` `+0x2C → 0x0081758C` — string table in `.data` (`417469720057657374` = `"Air\0West"`)
6. `0x007E4C30` `+0x2C → 0x00816E34` — `"Enter\0\0\0Sticky"` (`.data` string)
7. `0x007EF3CC` `+0x2C → 0x00410470` — `c3909090` bare `ret` (no WhatAmI at all)
8. `0x007E1F50` `+0x2C → 0x004C9150` — `33c0c3` `xor eax,eax; ret` (returns **0**, not an ordinal)

So the answer to "what does `+0x2C` point at for the unparseable ones" is **all four of the
proposed categories**: ordinary methods (majority), pure data (strings/COL headers), BSS
(no bytes), and code that isn't WhatAmI.

---

# Sections where my findings differ from the brief

1. **The `185` decomposes as `144 genuine + 41 pointer-returning getters`.** The brief treats
   185 as the conforming population. 41 of them are `mov eax,IMM32; ret` where IMM32 is a
   `.data` pointer and the "class ID" reaches 8 551 228 — a valid `GetType`/typeinfo getter,
   but not WhatAmI. Conformance is worse than stated, not better.

2. **`0x007E1F24`/`0x007E1F2C` are neither tables nor COLs** — they are *interior slots* of a
   thunk-superstructure whose COLs (`0x007E1F20`, `0x007E1F28`, `0x007E1F30`, `0x007E1F4C`)
   all carry `.?AVAbstractClass@@` with `mdisp = 0x0C, 0x08, 0x04, 0x00`. The brief's
   "slot 1/3 are data" observation is right, but they are *COL headers*, not data — which
   changes the diagnosis from "bad entry" to "sub-object vtables interleaved".

3. **No systematic offset exists at all.** This is a *negative* finding the brief asked for but
   did not expect: 1305/1305 are already at `COL+4`. The brief's "if it's remembered address =
   COL address" branch is closed. The 8-byte pairs are an artefact of sub-object vtables, not of
   an address-capture bug.

4. **The `.data` BSS boundary matches exactly** (`0x0087E000`, 3 128 292 bytes of BSS) — the
   brief was right. But note the last 16 file bytes of `.data` are **all zero**, so the final
   populated qword ends before that boundary; a naive reader could mistake tail padding for data.

5. **`col_count = 2193` is not a meaningful "COL count".** It is `|{aligned dword whose value is
   a TypeDescriptor}|` and it *over*-counts: 704 of the 2193 have a signature outside
   `{0, -1}` (garbage), including 7 inside `.text`. A stricter rule gives 1489, and a rule
   requiring a *table start* gives 1274. Reporting 2193 as "COLs found" inflates the evidence
   base by ~40%.

6. **`per_section` in the JSON reports `{'.data': 962, others: 0}` for TypeDescriptors** — this is
   *correct* per the producer's own note, but it silently omits that the *keys* derived from
   those TDs land in `.rdata` (1212), `.data` (5), `.rsrc` (1) and `.text` (87). The section
   histogram in the JSON describes the TypeDescriptors, not the vtables; a reader can easily
   misread it as a vtable section distribution.

7. **`0x00B8E0D4` is keyed as a vtable start but lies in `.rsrc`.** Verified chain:
   `[key-4] = 0x008001A8`, `sig=0x0`, `off=0`, `cd=0`, `pTD=0x00820420 → .?AV?$VectorClass@PAUButtonFadeEffect@@@@`.
   So the COL itself is structurally valid and lives in `.rdata`. **The false step is the key**:
   the producer assumes the dword at `0x00B8E0D0` points to that COL, but
   `bytes at 0x00B8E0D0 = a8018000 6c001700 2105ffff 80004700` — that dword is `0x008001A8`
   only because it is coincidental resource bytes. The following "slots"
   (`0x0017006C`, `0xFFFF0521`, `0x00470080`, `0x00490055`) are pure resource data, not code
   pointers. Same false-positive class as P1, just in `.rsrc` instead of `.text`.
   **Not mentioned in the brief; should be dropped from the map.**

8. **`md.skipdata = True` matters here**: without it, `.text` linear sweep stalls at the first
   undecodable byte. With it, coverage is *exactly* `0x3DF38D` bytes — a good self-check that
   the sweep saw the whole section (I used this as a sanity gate).

---

## Reproduce

```powershell
cd D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\ds
python ds_a1_repro.py      # layer sanity + 87/1305/185 reproduction
python ds_a3_p1code.py     # skipdata sweep, 87/87 inside instructions
python ds_a9_clean.py      # strict rebuild: 87 -> 0, 1274 reserved intact
python ds_a17_final.py     # P1 mechanism, BSS boundary
python ds_a4_p2.py         # 0x007E1F24/2C window
python ds_a10_p3.py        # +0x2C classification + byte witnesses
python ds_a11_p3proof.py   # bisect proof of adjacent-table reads
python ds_a13_disamb.py    # 185 -> 144 genuine + 41 pointer getters
python ds_a14_outliers.py  # the N up to 8.5M outliers
```

`ds_a12_layout.py` (via `ds_a16_mask.py`) additionally confirms the 87 mask nothing.
