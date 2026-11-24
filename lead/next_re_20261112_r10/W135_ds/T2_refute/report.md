# T2 — Adversarial verification of the W132 instance-array claims

**Role**: adversarial verification subagent. Claims treated as guilty until proven innocent.
**Binary**: `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
**SHA-256**: `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` — verified on every run.
**Method**: static only. The game was never launched. Nothing outside this directory was written.
**Reproduce**: `python -X utf8 t2_refute.py` → `counter_evidence.txt` (946 lines).

## Result at a glance

| claim | verdict |
|---|---|
| C1 layout of `VectorClass<T>` | **CONFIRMED** |
| C2 `0xA8EB40` is the building vector | **CONFIRMED** |
| C3 `0x8B4108` is the vehicle vector | **CONFIRMED** |
| C4 `0xA80228` is House; aircraft is `0xA8E390` | **CONFIRMED** |
| C5 `0xB0F720` is `AbstractClass*` and an "all objects" registry | **REFUTED** (type right, registry reading wrong) |
| C6 `0x8B3DC0` is `FootClass*`, `0x8B3DD0` = total mobile | **CONFIRMED** |
| C7 `AbstractClass` has 4 vptrs; `0x4101F0` is 28 bytes, 5 insns, 0 callees, no registration | **CONFIRMED** |

**Six of seven survive. C5 does not** — and it fails on the part that matters operationally.

---

## Preliminary: an RTTI detail that invalidates naive scanners

Before trusting *any* RTTI name, I had to pin the on-disk record layouts, because two
obvious implementations silently return nothing on this image.

| record | offsets, as actually found in this binary |
|---|---|
| `TypeDescriptor` | `+0x00` type_info vftable (`0x7F9594`), `+0x04` 0, **`+0x08` the name bytes inline** |
| `CompleteObjectLocator` | `+0x00` signature (0), `+0x04` offset, `+0x08` cdOffset, `+0x0C` pTypeDescriptor, `+0x10` pClassDescriptor |
| vftable `V` | `[V-4]` → COL |

`[已证]` **The `TypeDescriptor` name at `+0x08` is an inline `char[]`, not a `char*`.**

The bytes at `TD 0x823270` are:

```
00823270  94957f00 00000000 2e3f4156 3f244479    ; .......\ .?AV?$Dy
```

`u32(TD+8) == 0x56413F2E` — that is the ASCII text `.?AV` read as an integer, not a
pointer. A scanner that does `name = read_string(u32(TD+8))` gets a garbage address,
finds no `".?AV"` prefix, and discards the record.

**This is not a claim about W132 — it is my own first bug.** I initially concluded from
"`td_name` returns `None` for every vector" that the W132 identity table might be
fabricated. It was not. The correct reading at `TD+8` yields **988** TypeDescriptors,
exactly the count W132 reports. I record this because it is the exact failure mode an
adversarial pass is supposed to catch, and it nearly produced a false REFUTED on C2–C4.

The chain that validates the reader end to end:

```
vftable 0x7E9E24 -> [V-4] = COL 0x801280 -> sig 0, off 0
                 -> pTypeDescriptor 0x823270 -> name @0x823270+8
                 = .?AV?$DynamicVectorClass@PAVBuildingClass@@@@
```

which is precisely what `instance_arrays.tsv` row 29 records. `[已证]`

---

## C1 — `VectorClass<T>` layout — **CONFIRMED**

Claim: `+0x00` vftable, `+0x04` `T* Items`, `+0x08` `int Capacity`,
`+0x0C` `bool IsInitialized`, `+0x0D` `bool IsAllocated`, `+0x10` `int Count`,
`+0x14` `int CapacityIncrement` (default 10).

The task told me not to trust the one array the original pass used, so I derived the
layout **three independent ways across eight arrays**.

### (a) Eight independent `.CRT$XCU` initialisers, byte-exact

Not disassembly windows — I indexed every `C7 05 <abs> <imm32>` byte pattern in `.text`
(1971 of them) and grouped by absolute target, so decoder desynchronisation cannot
contaminate the result.

| array | static ctor | `+0x00` vftable | `+0x04` | `+0x08` | `+0x0C` | `+0x0D` | `+0x10` | `+0x14` |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `0xA8EB40` | `004E6B60` | `0x7E9E24` | 0 | 0 | 1 | 0 | 0 | **10** |
| `0x8B4108` | `004E6C60` | `0x7E9EA4` | 0 | 0 | 1 | 0 | 0 | **10** |
| `0xA80228` | `004E6CE0` | `0x7E9EE4` | 0 | 0 | 1 | 0 | 0 | **10** |
| `0xA8E390` | `004E6BE0` | `0x7E9E64` | 0 | 0 | 1 | 0 | 0 | **10** |
| `0x8B3DC0` | `004D3174` | `0x7E8C28` | 0 | 0 | 1 | 0 | 0 | **10** |
| `0xB0F720` | `007252D0` | `0x7E91EC` | 0 | 0 | 1 | 0 | 0 | **10** |
| `0xA8EC78` | `004E79E0` | `0x7E17AC` | 0 | 0 | 1 | 0 | 0 | **10** |
| `0xA83DE8` | `004E6AE0` | `0x7E43C8` | 0 | 0 | 1 | 0 | 0 | **10** |

`[已证]` All seven field offsets agree across all eight arrays, and `+0x14 == 10`
everywhere (angle 4 asked specifically; the answer is a clean single-valued set `{10}`).

### (b) The arrays' own virtual methods — a path sharing no code with (a)

This is the check that makes C1 hard to break. The vftables are real C++ vtables; their
methods index the object through `[ecx+disp]`. Those displacements are an independent
statement of the layout.

| slot | `FootClass::Array` fn | `[this+disp]` used |
|---|---|---|
| `+0x04` | `0x4E0580` | 0, 4, 8, 16 |
| `+0x08` | `0x4E0700` | 4, 8, 12, 24 |
| `+0x0C` | `0x4E01F0` | 4, 8, 13, 16 |
| `+0x10` | `0x4E07B0` | 0, 4, 8, 16 |
| `+0x14` | `0x4E0220` | 12 |
| `+0x18` | `0x4E0240` | 0, 4 |

`[已证]` Union of offsets used = `{0, 4, 8, 12, 13, 16}` — exactly C1's field set, on all
eight arrays. Notably `+0x0D` (the odd offset) appears, which no natural misreading of the
static ctors would produce.

Two of these are worth quoting because they are unambiguous:

```asm
; operator[](int)  --  Items @ +0x04, 4-byte elements
004E0240  8b4104        mov eax, [ecx+4]
004E0243  8b4c2404      mov ecx, [esp+4]
004E0247  8b0488        mov eax, [eax+ecx*4]
004E024A  c20400        ret 4

; clear()  --  Items @+4, IsAllocated @+0x0D, Capacity @+8, Count @+0x10
004E01F0  8b4604        mov eax, [esi+4]        ; Items
004E01F9  895e10        mov [esi+0x10], ebx     ; Count = 0
004E0200  385e0d        cmp [esi+0x0d], bl      ; if (IsAllocated)
004E020E  895e04        mov [esi+4], ebx        ;   Items = 0
004E0214  895e08        mov [esi+8], ebx        ; Capacity = 0
```

### (c) A literal inline insert sequence

`0x4D3487..0x4D34D7` (inside `FootClass::FootClass`) is a textbook
`DynamicVectorClass<T*>::Add`, and it names every field:

```asm
004D3487  a1c83d8b00      mov eax, [0x8B3DC8]   ; Capacity  (+0x08)
004D348C  8b0dd03d8b00    mov ecx, [0x8B3DD0]   ; Count     (+0x10)
004D3492  3bc8            cmp ecx, eax
004D3494  7c2c            jl  short ok
004D3496  381dcd3d8b00    cmp [0x8B3DCD], bl    ; IsAllocated (+0x0D)
004D34A2  8b0dd43d8b00    mov ecx, [0x8B3DD4]   ; CapacityIncrement (+0x14)
004D34AC  8b15c03d8b00    mov edx, [0x8B3DC0]   ; vftable
004D34B2  03c8            add ecx, eax          ; newCap = inc + cap
004D34B5  51              push ecx
004D34B6  b9c03d8b00      mov ecx, 0x8B3DC0
004D34BB  ff5208          call [edx+8]          ; Resize(newCap, 0)
004D34C2  8b0dd03d8b00    mov ecx, [0x8B3DD0]   ; Count
004D34CA  41              inc ecx
004D34CB  890dd03d8b00    mov [0x8B3DD0], ecx   ; store new Count
004D34D1  8b0dc43d8b00    mov ecx, [0x8B3DC4]   ; Items
004D34D7  893481          mov [ecx+eax*4], esi  ; Items[Count] = this
```

`[已证]` Three unrelated derivations agree. **C1 CONFIRMED.**

---

## C2 — `0xA8EB40` is the building vector — **CONFIRMED**

```
004E6B7D  c705 40eba800 249e7e00   mov [0xA8EB40], 0x7E9E24
0x7E9E24 -> [V-4] = 0x801280 -> TD 0x823270 -> .?AV?$DynamicVectorClass@PAVBuildingClass@@@@
```

`[已证]` `0xA8EB44 = Items`, `0xA8EB50 = Count`, element type `BuildingClass*`.

The stronger half of C2 is the *negative*: `0xA8EB44` is not a unit/object table. I
checked every `mov [abs], vftable` within ±0x20 of `0xA8EB44`:

```
004E6B7D mov [00A8EB40],007E9E24 -> DynamicVectorClass<BuildingClass*>
004E6BA8 mov [00A8EB40],007E9E44 -> VectorClass<BuildingClass*>      (base dtor)
004E767D mov [00A8EB28],007EA3A4 -> DynamicVectorClass<VoxelAnimTypeClass*>
004E76A8 mov [00A8EB28],007EA3C4 -> VectorClass<VoxelAnimTypeClass*>
```

`[已证]` No `UnitClass`-derived type is ever installed near `0xA8EB44`. **C2 CONFIRMED.**

---

## C3 — `0x8B4108` is the vehicle vector — **CONFIRMED**

```
004E6C60..004E6C9E   static ctor
004E6C7D  c705 08418b00 a49e7e00   mov [0x8B4108], 0x7E9EA4
0x7E9EA4 -> COL 0x8013B0 -> TD 0x823340 -> .?AV?$DynamicVectorClass@PAVUnitClass@@@@
004E6C87  mov [0x8B411C], 0xA   ; CapacityIncrement
004E6C91  mov [0x8B4118], eax   ; Count = 0
004E6CA8  mov [0x8B4108], 0x7E9EC4  ; base dtor -> VectorClass<UnitClass*>
```

`[已证]` `0x8B410C / 0x8B4118` = vehicle `Items / Count`.

I attacked this by looking for a **second** vehicle vector. A brute scan of all 1971
`C7 05` stores whose immediate resolves to a `*VectorClass<...>` TypeDescriptor, grouped
by element type, produced exactly **one** base per element type for `UnitClass`,
`BuildingClass`, `HouseClass`, `AircraftClass`, `FootClass`, `AbstractClass`,
`TechnoClass`, `InfantryClass`. `[已证]` There is no second vehicle list. **C3 CONFIRMED.**

---

## C4 — `0xA80228` is House; aircraft is `0xA8E390` — **CONFIRMED**

| base | static ctor | vftable | COL | TD | RTTI name |
|---|---|---|---|---|---|
| `0xA80228` | `0x4E6CE0` | `0x7E9EE4` | `0x801448` | `0x8233A8` | `.DynamicVectorClass<HouseClass*>` |
| `0xA8E390` | `0x4E6BE0` | `0x7E9E64` | `0x801318` | `0x8232D8` | `.DynamicVectorClass<AircraftClass*>` |

`[已证]` The two arrays are 0xE168 apart, are separate static-ctor targets (4 stores
total between them), and the RTTI names are unambiguous. The project document labelling
`0xA8022C / 0xA80238` as "Aircraft" is wrong; the correct aircraft pair is
`0xA8E394 / 0xA8E3A0`. **C4 CONFIRMED.**

---

## C5 — `0xB0F720` — **REFUTED**

C5 has two halves. They land on opposite verdicts, and the task correctly told me to
attack the second.

### Half 1 — the element type. Right.

```
007252ED  c705 20f7b000 ec917e00   mov [0xB0F720], 0x7E91EC
0x7E91EC -> COL 0x8009B0 -> TD 0x8225E8 -> .?AV?$DynamicVectorClass@PAVAbstractClass@@@@
```

`[已证]` It really is `DynamicVectorClass<AbstractClass*>`.

### Half 2 — "used as an all-objects registry". **REFUTED.**

W132 itself graded completeness `[未证]`. I did not attack completeness as
"does every object register" — I attacked the stronger, more damaging question: **does
this array function as a registry at all?** The answer is no.

**Negative control.** `FootClass::FootClass` at `0x4D31E0` is provably an object ctor: it
installs `.?AVFootClass@@` at `[this]`. Its 860 bytes contain:

| array | refs inside the ctor |
|---|---:|
| `AbstractClass::Array.Items` `0xB0F724` | **0** |
| `AbstractClass::Array.Count` `0xB0F730` | **0** |
| `FootClass::Array.Items` `0x8B3DC4` | 1 |
| `FootClass::Array.Count` `0x8B3DD0` | 3 |

`[已证]` A `FootClass` registers itself into **its own** type array and **does not touch**
`AbstractClass::Array`. If `0xB0F720` were an all-objects registry, this ctor would have to
touch it.

**Census.** Of the 47 direct call sites of `AbstractClass::AbstractClass` at `0x4101F0`,
only these classes ever inline a push into the array:

- `AlphaShapeClass` (`0x420C7F`, `0x4216B2`)
- `FactoryClass` (`0x4C9A04`, `0x4CA767`)
- one `AnimClass` destructor family (`0x6E8E50`, which *removes* — it decrements Count
  and shifts elements down)

`[已证]` These do **not** register:

`TechnoClass`, `BuildingClass`, `UnitClass`, `InfantryClass`, `AircraftClass`,
`FootClass`, `BulletClass`, `AnimClass` (ctor), `OverlayClass`, `TerrainClass`,
`SmudgeClass`, `HouseClass`

A 47-class census where the gameplay-relevant object types are absent is not a registry.
**C5 REFUTED.**

**Caveat I am obliged to state.** Registration is inlined per-class. A class that
delegated to a non-inlined shared helper would be missed by the "does the ctor contain the
push" test. Two things bound this risk: (i) I searched for *any* in-place
`inc/add dword [0xB0F730]`, found **zero** — every push is inlined, so the inlining
picture is complete; (ii) the `FootClass` ctor result stands on its own and
does not depend on the census at all. What would *settle* it beyond doubt is one live
reading of `[0xB0F730]` compared against the sum of the per-type counts — that is a
runtime experiment, which I did not and cannot run offline.

**Operational consequence.** Anything downstream that treats `[0xB0F730]` as "total
objects on the map" is reading a number that omits every building, vehicle, infantryman
and aircraft. Use `0x8B3DD0` (`FootClass`) for mobile objects and `0xA8EC88`
(`TechnoClass`) for buildings+mobile.

---

## C6 — `0x8B3DC0` is the mobile-object vector — **CONFIRMED**

```
004D317D  c705 c03d8b00 288c7e00   mov [0x8B3DC0], 0x7E8C28
0x7E8C28 -> COL 0x800868 -> TD 0x822580 -> .?AV?$DynamicVectorClass@PAVFootClass@@@@
004D31A8  mov [0x8B3DC0], 0x7E8C48   ; base dtor -> VectorClass<FootClass*>
```

`[已证]` Element type `FootClass*`. The insert site quoted under C1(c) is *inside this
vector's own plumbing*, writing `Items[Count] = this` with 4-byte pointer elements. So
`0x8B3DD0` counts `FootClass`-derived objects — infantry + vehicles + aircraft — and is a
defensible "total mobile object" count.

**What I could not fully close, stated honestly.** The task asked whether `FootClass::Array`
is *really* the union. The RTTI `ClassDescriptor` records for this image do not validate
under my parser (the `+0x40` back-pointer self-check fails for every class), so I could
**not** confirm `FootClass` is a base of `UnitClass` / `InfantryClass` / `AircraftClass`
from the hierarchy data. My parser reports `nBase`/`bases` as unavailable for all of them.

What I *can* say: `FootClass::FootClass` (`0x4D31E0`) exists, is 860 bytes, installs
`.?AVFootClass@@`, and has only **3** direct call sites (`0x413D2B`, `0x517A5B`,
`0x7353CE`). Three call sites is few, but derived ctors typically reach the base ctor
through several wrappers, and a static call-count is not a proof of absence.

`[已证]` identity and element type. `[未证]` that the union is exhaustive. C6 graded
**CONFIRMED** on the statement actually made (`FootClass*` vector, `0x8B3DD0` counts
mobile objects) with that limit recorded.

---

## C7 — `AbstractClass` 4 vptrs and the `0x4101F0` ctor — **CONFIRMED**

Full disassembly, nothing elided:

```asm
004101F0  c701 501f7e00      mov dword ptr [ecx],   0x7E1F50
004101F6  c74104 341f7e00    mov dword ptr [ecx+4], 0x7E1F34
004101FD  c74108 2c1f7e00    mov dword ptr [ecx+8], 0x7E1F2C
00410204  c7410c 241f7e00    mov dword ptr [ecx+0xC],0x7E1F24
0041020B  c3                 ret
```

`[已证]` **5 instructions, 28 bytes, `n_callees = 0`.** Exactly as claimed.

Resolving each stored vftable through `[V-4]`:

| store | vftable | COL | COL.off | TD | name |
|---|---|---|---:|---|---|
| `[ecx]` | `0x7E1F50` | `0x7FB118` | **0** | `0x8177C8` | `.?AVAbstractClass@@` |
| `[ecx+4]` | `0x7E1F34` | `0x7FB008` | **4** | `0x8177C8` | `.?AVAbstractClass@@` |
| `[ecx+8]` | `0x7E1F2C` | `0x7FAFF0` | **8** | `0x8177C8` | `.?AVAbstractClass@@` |
| `[ecx+0xC]` | `0x7E1F24` | `0x7FAFD8` | **12** | `0x8177C8` | `.?AVAbstractClass@@` |

`[已证]` Four distinct COLs, all signature 0, all pointing at the **same** TypeDescriptor
`0x8177C8`, with base offsets 0 / 4 / 8 / 12 — the canonical MSVC x86 4-base
multiple-inheritance layout. The vftables are live (each slot 0 is real `.text`: e.g.
`0x7E1F50 -> 0x410260`, `0x7E1F34 -> 0x4105E0`, `0x7E1F2C -> 0x410580`,
`0x7E1F24 -> 0x410590`).

Zero references to the array in those 28 bytes:

```
0xB0F720 : 0 occurrences
0xB0F724 : 0 occurrences
0xB0F730 : 0 occurrences
```

`[已证]` `0x4101F0` does not register itself. **C7 CONFIRMED**, and it does contradict
an assumption that "the vptr is at `+0`" — for `AbstractClass` there are four of them,
and a dereference must pick the right sub-object.

**"Is there a better candidate ctor?"** `0x4101F0` has **47 direct call sites**, which is
what a base-class ctor looks like. I found no near-duplicate that installs the same four
vftables through a different register. `[已证]` It is the real `AbstractClass` ctor.

---

## Does any of this disturb the other verdicts?

Deliberately checked, because a shared-mistake explanation is the usual way a clean
verdict sheet is wrong:

- C1 was derived from static ctors **and** from virtual methods **and** from an inline
  insert. Three code paths, no shared machinery.
- C2/C3/C4 each resolve their own vftable; the same reading yields the same answer for a
  `VectorClass` base-dtor store (`0x7E9E44`, `0x7E9EC4`, `0x7E9F04`) that is a *different*
  COL — so the reading is not just returning the same string everywhere.
- The 988-TypeDescriptor count matches W132's independent figure, which cross-validates
  my reader against theirs without sharing code.

## Summary

**Six confirmed, one refuted.** The refutation is C5's registry reading — the array is
genuinely `AbstractClass*`, but it does not hold buildings, vehicles, infantry or aircraft,
so `[0xB0F730]` is not a total-object count. C6's union exhaustiveness remains `[未证]`;
settling it needs either a working `ClassDescriptor` parser for this image's RTTI dialect,
or one live reading.
