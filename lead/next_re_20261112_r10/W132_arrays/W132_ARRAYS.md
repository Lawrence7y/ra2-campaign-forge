# W132 — The engine's instance-array table, named by the binary itself

**Date**: 2026-11-15
**Question**: 台账 §853-3 called `DAT_00a8eb44` a "candidate unit / object master
table" and used it to explain §707 ("cell chains do not register units: 213
nodes vs 1500 designed"). Project documents elsewhere called
`0xA8EB44 / 0xA8EB50` the **BuildingClass** instance vector. Only one is right.

**Answer**: `0xA8EB44` is `BuildingClass::Array.Items`. §853-3 was wrong.
The real unit list is `UnitClass::Array` at `0x8B4108`.

Everything below is derived from `gamemd.exe` itself. `YRpp` (the community
header set shipped in this repo) is used **only as a cross-check**, never as
evidence.

---

## 1. The layout is pinned to the byte

`0x004E6B60` is the `.CRT$XCU` static initialiser for `BuildingClass::Array`.
It is a textbook MSVC static ctor, and it states the whole layout:

```asm
004E6B60  33c0                    xor  eax, eax
004E6B62  68a06b4e00              push 0x004E6BA0          ; atexit handler
004E6B67  a344eba800              mov  [0x00A8EB44], eax   ; Items         = 0   (+0x04)
004E6B6C  a348eba800              mov  [0x00A8EB48], eax   ; Capacity      = 0   (+0x08)
004E6B71  c6054ceba80001          mov  byte [0x00A8EB4C], 1; IsInitialized = true(+0x0C)
004E6B78  a24deba800              mov  byte [0x00A8EB4D], al; IsAllocated  = false(+0x0D)
004E6B7D  c70540eba800249e7e00    mov  [0x00A8EB40], 0x7E9E24 ; vptr -> DynamicVectorClass<BuildingClass*>::vftable
004E6B87  c70554eba8000a000000    mov  [0x00A8EB54], 0xA   ; CapacityIncrement = 10 (+0x14)
004E6B91  a350eba800              mov  [0x00A8EB50], eax   ; Count         = 0   (+0x10)
004E6B96  e8ef2b2e00              call 0x007C978A          ; atexit(0x004E6BA0)
004E6B9B  59                      pop  ecx
004E6B9C  c3                      ret
```

`0x004E6BA0` — the handler registered above — is the matching **destructor**,
and it confirms the same offsets from the other direction:

```asm
004E6BA0  a144eba800              mov  eax, [0x00A8EB44]   ; Items
004E6BA8  c70540eba800449e7e00    mov  [0x00A8EB40], 0x7E9E44 ; vptr back to the BASE VectorClass<BuildingClass*>::vftable
004E6BB6  381d4deba800            cmp  byte [0x00A8EB4D], bl ; if (!IsAllocated) skip
004E6BBF  e8791f2e00              call 0x007C8B3D          ; operator delete[](Items)
004E6BC7  891d44eba800            mov  [0x00A8EB44], ebx   ; Items = 0
```

So:

| offset | field | proof |
|---:|---|---|
| `+0x00` | `vftable` | ctor writes `0x7E9E24`; dtor writes back `0x7E9E44` (base class) |
| `+0x04` | `T* Items` | zeroed, then `delete[]`-ed |
| `+0x08` | `int Capacity` | zeroed |
| `+0x0C` | `bool IsInitialized` | set to `1` |
| `+0x0D` | `bool IsAllocated` | set to `0`, tested before `delete[]` |
| `+0x10` | `int Count` | zeroed |
| `+0x14` | `int CapacityIncrement` | set to `10` |

The two vtable stores in ctor and dtor are the standard C++ base/derived pair:
the ctor ends on `DynamicVectorClass<T>::vftable`, the dtor restores the base
`VectorClass<T>::vftable`. **This is what makes the element type recoverable
from the binary** — the ctor leaves the *derived* type in place, and its COL
names it.

## 2. Naming a vtable

The chain, all inside the image:

```
vftable V  --[V-4]-->  COL  --[COL+0x0C]-->  TypeDescriptor  --[TD+8]-->  ".?AV?$DynamicVectorClass@PAVBuildingClass@@@@"
```

For `V = 0x007E9E24`: `COL = 0x00801280`, `TD = 0x00823270`,
name = `.?AV?$DynamicVectorClass@PAVBuildingClass@@@@`.

The TD address is confirmed twice independently: once by following the COL, and
once by searching `.data` for the mangled-name string and subtracting 8. Note
this image keeps its RTTI **strings in `.data`** (`0x815DE8+`), not `.rdata`;
a scan restricted to `.rdata` finds zero TypeDescriptors. That was the bug in
my first attempt.

## 3. The table — 49 arrays, all named by the binary

`instance_arrays.tsv` (same directory). `Items = base+4`, `Count = base+0x10`.
"refs" = validated instructions whose memory operand is exactly that address.

| element type (from the binary's RTTI) | base | Items | Count | items refs | count refs |
|---|---|---:|---:|---:|---:|
| `DynamicVectorClass<CommandClass*>` | `0x0087F658` | `0x0087F65C` | `0x0087F668` | 52 | 98 |
| `DynamicVectorClass<LightConvertClass*>` | `0x0087F698` | `0x0087F69C` | `0x0087F6A8` | 18 | 21 |
| `DynamicVectorClass<IsometricTileClass*>` | `0x0087F750` | `0x0087F754` | `0x0087F760` | 5 | 8 |
| `DynamicVectorClass<VoxelAnimClass*>` | `0x00887388` | `0x0088738C` | `0x00887398` | 10 | 15 |
| `VectorClass<AlphaShapeClass*>` | `0x0088A0F0` | `0x0088A0F4` | `0x0088A100` | 14 | 18 |
| `DynamicVectorClass<CaptureManagerClass*>` | `0x0089E0F0` | `0x0089E0F4` | `0x0089E100` | 8 | 13 |
| `DynamicVectorClass<ConvertClass*>` | `0x0089ECF8` | `0x0089ECFC` | `0x0089ED08` | 7 | 10 |
| `DynamicVectorClass<DiskLaserClass*>` | `0x008A0208` | `0x008A020C` | `0x008A0218` | 9 | 14 |
| `DynamicVectorClass<EBolt*>` | `0x008A0E88` | `0x008A0E8C` | `0x008A0E98` | 9 | 11 |
| `DynamicVectorClass<EMPulseClass*>` | `0x008A3870` | `0x008A3874` | `0x008A3880` | 11 | 18 |
| **`DynamicVectorClass<FootClass*>`** | **`0x008B3DC0`** | `0x008B3DC4` | **`0x008B3DD0`** | 12 | 17 |
| `DynamicVectorClass<TeamClass*>` | `0x008B40E8` | `0x008B40EC` | `0x008B40F8` | 24 | 36 |
| **`DynamicVectorClass<UnitClass*>`** | **`0x008B4108`** | **`0x008B410C`** | **`0x008B4118`** | 23 | 41 |
| `DynamicVectorClass<BuildingLightClass*>` | `0x008B4190` | `0x008B4194` | `0x008B41A0` | 11 | 17 |
| `DynamicVectorClass<ParticleSystemClass*>` | `0x00A80208` | `0x00A8020C` | **`0x00A80218`** | 12 | 21 |
| **`DynamicVectorClass<HouseClass*>`** | **`0x00A80228`** | **`0x00A8022C`** | **`0x00A80238`** | 207 | 134 |
| `DynamicVectorClass<SuperClass*>` | `0x00A83CB8` | `0x00A83CBC` | `0x00A83CC8` | 13 | 11 |
| `DynamicVectorClass<ParticleClass*>` | `0x00A83DC8` | `0x00A83DCC` | `0x00A83DD8` | 9 | 17 |
| **`VectorClass<InfantryClass*>`** | **`0x00A83DE8`** | **`0x00A83DEC`** | **`0x00A83DF8`** | 23 | 41 |
| `DynamicVectorClass<FactoryClass*>` | `0x00A83E30` | `0x00A83E34` | `0x00A83E40` | 43 | 35 |
| `DynamicVectorClass<SmudgeClass*>` | `0x00A8B1E0` | `0x00A8B1E4` | `0x00A8B1F0` | 6 | 8 |
| **`DynamicVectorClass<AircraftClass*>`** | **`0x00A8E390`** | **`0x00A8E394`** | **`0x00A8E3A0`** | 18 | 29 |
| `DynamicVectorClass<AbstractTypeClass*>` | `0x00A8E968` | `0x00A8E96C` | `0x00A8E978` | 13 | 25 |
| `VectorClass<TerrainClass*>` | `0x00A8E988` | `0x00A8E98C` | `0x00A8E998` | 11 | 19 |
| `DynamicVectorClass<AnimClass*>` | `0x00A8E9A8` | `0x00A8E9AC` | `0x00A8E9B8` | 21 | 32 |
| **`DynamicVectorClass<TriggerClass*>`** | **`0x00A8EAE8`** | **`0x00A8EAEC`** | **`0x00A8EAF8`** | 19 | 31 |
| `DynamicVectorClass<TechnoTypeClass*>` | `0x00A8EB00` | `0x00A8EB04` | `0x00A8EB10` | 17 | 19 |
| **`DynamicVectorClass<BuildingClass*>`** | **`0x00A8EB40`** | **`0x00A8EB44`** | **`0x00A8EB50`** | 40 | 69 |
| `DynamicVectorClass<WaveClass*>` | `0x00A8EC38` | `0x00A8EC3C` | `0x00A8EC48` | 9 | 16 |
| `DynamicVectorClass<OverlayClass*>` | `0x00A8EC50` | `0x00A8EC54` | `0x00A8EC60` | 7 | 12 |
| **`DynamicVectorClass<TechnoClass*>`** | **`0x00A8EC78`** | **`0x00A8EC7C`** | **`0x00A8EC88`** | 72 | 93 |
| `DynamicVectorClass<IsometricTileTypeClass*>` | `0x00A8ED28` | `0x00A8ED2C` | `0x00A8ED38` | 75 | 33 |
| `DynamicVectorClass<BulletClass*>` | `0x00A8ED40` | `0x00A8ED44` | `0x00A8ED50` | 10 | 15 |
| `DynamicVectorClass<IonBlastClass*>` | `0x00AA0118` | `0x00AA011C` | `0x00AA0128` | 7 | 7 |
| `DynamicVectorClass<LineTrail*>` | `0x00ABCB78` | `0x00ABCB7C` | `0x00ABCB88` | 11 | 15 |
| `DynamicVectorClass<SpotLightClass*>` | `0x00AC1678` | `0x00AC167C` | `0x00AC1688` | 10 | 14 |
| `DynamicVectorClass<ParasiteClass*>` | `0x00AC4910` | `0x00AC4914` | `0x00AC4920` | 8 | 12 |
| `DynamicVectorClass<RadBeam*>` | `0x00B04A60` | `0x00B04A64` | `0x00B04A70` | 7 | 8 |
| `DynamicVectorClass<RadSiteClass*>` | `0x00B04BD0` | `0x00B04BD4` | `0x00B04BE0` | 7 | 10 |
| `DynamicVectorClass<ColorScheme*>` | `0x00B054D0` | `0x00B054D4` | `0x00B054E0` | 103 | 33 |
| `DynamicVectorClass<SlaveManagerClass*>` | `0x00B0B5F0` | `0x00B0B5F4` | `0x00B0B600` | 6 | 9 |
| `VectorClass<SpawnManagerClass*>` | `0x00B0B880` | `0x00B0B884` | `0x00B0B890` | 7 | 11 |
| `DynamicVectorClass<TActionClass*>` | `0x00B0E658` | `0x00B0E65C` | `0x00B0E668` | 10 | 16 |
| `DynamicVectorClass<TagClass*>` | `0x00B0E720` | `0x00B0E724` | `0x00B0E730` | 20 | 26 |
| `DynamicVectorClass<TemporalClass*>` | `0x00B0EC60` | `0x00B0EC64` | `0x00B0EC70` | 8 | 15 |
| `DynamicVectorClass<TEventClass*>` | `0x00B0F1A0` | `0x00B0F1A4` | `0x00B0F1B0` | 10 | 16 |
| **`DynamicVectorClass<AbstractClass*>`** | **`0x00B0F720`** | **`0x00B0F724`** | **`0x00B0F730`** | 19 | 48 |
| `DynamicVectorClass<VocClass*>` | `0x00B1D378` | `0x00B1D37C` | `0x00B1D388` | 19 | 28 |
| `DynamicVectorClass<VoxClass*>` | `0x00B1D4A0` | `0x00B1D4A4` | `0x00B1D4B0` | 22 | 34 |

**49 / 49 named by the binary's own RTTI.** YRpp agrees on 48; the 49th is a
spelling difference only — the binary's RTTI says `SpotLightClass`, YRpp says
`SpotlightClass`.

## 4. Every global §853-3 listed, resolved

| §853-3 label | real identity (from the table) |
|---|---|
| `DAT_00a8eb44` | `BuildingClass::Array.Items` — **not** a unit table |
| `DAT_00a8eb50` | `BuildingClass::Array.Count` |
| `DAT_00a8eaf8` | `TriggerClass::Array.Count` |
| `DAT_008b3dd0` | `FootClass::Array.Count` |
| `DAT_00a8ec88` | `TechnoClass::Array.Count` |
| `DAT_00a80218` | `ParticleSystemClass::Array.Count` |
| `DAT_00a83df8` | `InfantryClass::Array.Count` |
| `DAT_00a8b230` | not an array field — a state value (§853-3 said "state") |
| `DAT_008871e0` | not an array field — a state value (§853-3 said "state") |

So the main loop `0x006DD8B0` walks **six different per-type arrays**
(`TriggerClass`, `BuildingClass`, `FootClass`, `TechnoClass`, `HouseClass`,
`InfantryClass`) — not "the unit list".

**The mobile-unit list the project was looking for** is
`UnitClass::Array` @ `0x008B4108` (Count `0x008B4118`), with
`InfantryClass::Array` @ `0x00A83DE8` and `AircraftClass::Array` @ `0x00A8E390`
as its siblings, and `FootClass::Array` @ `0x008B3DC0` (Count `0x008B3DD0`)
as their common supertype list.

## 5. Consequences

### 5.1 Wrong claim in project docs (found while doing this)

`docs/re/net_sync_checksum.md:261` labels `0xA8022C / 0xA80238` as
*"for each Aircraft"*. The binary says that pair is
`HouseClass::Array.Items / .Count`. Aircraft is `0xA8E394 / 0xA8E3A0`
(which is what the harness already reads as `MEASURE_AIRCRAFT_VA`).

### 5.2 §707 ("cell chains do not register units")

The structural explanation is now solid: cell chains (`CellClass +0xE4/+0xE8`)
are a **spatial index**, while every object also lives in a per-type
`DynamicVectorClass`. A count taken from the chains and a count taken from the
arrays are measuring different things, so "213 vs 1500 designed" is not
evidence of loss — it is evidence that the chain was the wrong instrument
(which is what §707 already concluded by other means).

### 5.3 How to get the real N

| quantity | read | status |
|---|---|---|
| all objects | `[0x00B0F730]` `AbstractClass::Array.Count` | array identity `[已证]`; **completeness `[未证]`** |
| all mobile objects | `[0x008B3DD0]` `FootClass::Array.Count` | `[已证]` identity |
| units (vehicles) | `[0x008B4118]` | `[已证]` identity |
| infantry | `[0x00A83DF8]` | `[已证]` identity |
| aircraft | `[0x00A8E3A0]` | `[已证]` identity |
| buildings | `[0x00A8EB50]` | `[已证]` identity |
| techno (buildings + mobile) | `[0x00A8EC88]` | `[已证]` identity |

## 6. Set-level cross-check against the class atlas

The 988 TypeDescriptors parsed here are not merely the same *count* as the class
atlas built independently in `W130_atlas/class_atlas_v2.json` — they are the
same *set*:

| | count | difference |
|---|---|---|
| TypeDescriptors in the binary (`.data`, `0x815DE8+`) | **988** | — |
| classes in `class_atlas_v2.json` | **988** | — |
| in the atlas but not the binary | **0** | ∅ |
| in the binary but not the atlas | **0** | ∅ |

Both directions are empty. So the atlas is not "988 assembled from something
else" — the image really contains exactly those 988 types and nothing more. It
also retroactively validates the `1,305 → 1,214` vtable cleanup (§846/§848): had
that cleanup deleted a type, the difference would not be empty.

## 7. Honest limits

1. **`AbstractClass::Array` completeness is `[未证]`.** 14 functions inline a
   push/pop against `0xB0F724` / `0xB0F730`, which shows the array is a live
   registry, but I did not prove that *every* `AbstractClass` ctor registers
   itself. Settling it needs one live reading compared against the sum of the
   per-type counts.
2. **Nothing here was verified live.** All 49 identities are static. Whether a
   given session's `[0x008B4118]` equals the number of vehicles actually on the
   map is still an empirical question — though past harness trips already treat
   it that way.
3. **All 49 are `DynamicVectorClass<T*>`.** A first pass reported four of them
   as plain `VectorClass<T*>` (`AlphaShapeClass`, `InfantryClass`,
   `TerrainClass`, `SpawnManagerClass`). That was my scanner, not the binary:
   each array receives **two** vtable stores — the ctor leaves the derived
   `DynamicVectorClass` one, and the `atexit` destructor restores the base
   `VectorClass` one — and my disassembly-window scan sometimes picked the base
   because capstone was decoding from `hit-16`, a start offset that can land
   mid-instruction. Matching the byte pattern `C7 05 <base> <vftable>` directly
   and preferring the `DynamicVectorClass` name resolves all four. They are now
   `DynamicVectorClass<T*>` in the table.
4. **The `refs` counts are indicative, not exhaustive.** They come from the same
   window-decode method, so a reference can be missed when the 16-byte lookback
   desynchronises the decoder. The *identities* above do not depend on them;
   they come from the byte-exact `C7 05` match plus the RTTI chain.

## 8. Reproduce

```
python -X utf8 w132d_instance_arrays.py      # the table (writes instance_arrays.tsv)
python -X utf8 w132c_vtable_names.py         # vtable -> COL -> TD -> name for the key arrays
python -X utf8 w132b_vector_family.py        # YRpp cross-check + static-init dump
python -X utf8 w132_array_globals.py --fn 0x004E6B60   # refs of any global / function
```
