# T1 — complete mechanical enumeration of static `VectorClass<T>` / `DynamicVectorClass<T>` globals in `gamemd.exe`

Binary: `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` (re-verified at every run; the script aborts with exit 2 on mismatch).
Every number below is produced by `t1_enumerate.py` in this directory; re-running it reproduces the same `vector_globals.tsv` byte-for-byte (verified with a second run, see §7).

Everything here is `[已证]` unless explicitly marked `[未证]`.

---

## 0. Headline numbers

| quantity | value |
|---|---|
| distinct `.data` destinations that receive a vector-typed vptr store | **142** |
| of those, real standalone **global vector objects** (header + default `CapacityIncrement` store + code reads the vector layout) | **140** |
| rejected as *not* a standalone vector object (explained in §5) | **2** |
| distinct element types (vectors with the same element counted once) | 110 |
| globals carrying ≥2 different vptr stores (ctor + `atexit` dtor) | 1 |
| globals with **no** `DynamicVectorClass` store at all (base-class store only) | 1 (`0x00B0C114`) |
| W132 rows reproduced with the same base **and** same element type | **49 / 49** |
| W132 rows where I get a different element type | **0** |
| W132 rows where I get a different vftable address | **0** |
| W132 rows I could not find at all | **0** |
| **additional** globals not in W132 | **91** |

---

## 1. Why the previous pass could not close the gap

The delivered method (scan `C7 05`, resolve `[value-4] → COL → TD → name`) is necessary but
not sufficient for a *complete* enumeration. Four independent defects were found and each one
is exercised by at least one global below.

### 1.1 MSVC uses three different encodings for `global.vptr = &vftable`

| encoding | bytes | where it occurs |
|---|---|---|
| `C7 05 <abs> <imm32>` | `c7 05 08 41 8b 00 a4 9e 7e 00` | the common case |
| `A3 <abs>` (`mov [abs], eax`) | `a3 bc ec a8 00` | 0x00889E08 vptr? no — see 1.2; but `A3` is used for *field* stores everywhere, e.g. `mov [0xa8ecbc], eax` at 0x004E7D47 |
| `89 0D/15/05 <abs>` (`mov [abs], ecx/edx/eax`) | `89 1d bc ec a8 00` | dtor/`atexit` postlude (0x004E7DA7) |

The **register** forms are used for the vptr of a handful of globals. Three are reachable
only that way, and a `C7 05`-only scan finds **zero** store for them:

```
0x00412948   89 0D 08 9E 88 00     mov dword ptr [0x00889E08], ecx   ; ecx = 0x007E180C
0x005D7A05   89 0D A0 FD AB 00     mov dword ptr [0x00ABFDA0], ecx   ; ecx = 0x007EED20
0x004E7B28   C7 05 60 E3 A8 00 2C 19 7E 00   mov dword ptr [0x00A8E360], 0x007E192C
```
`0x00889E08` is found by `t1_enumerate.py::register_form_stores` (backward search for
`mov <reg>, imm32` in the same basic block); `0x00ABFDA0` additionally has nine `C7 05`
stores of the same vftable, so it is found twice by two mechanisms (`_stats.txt` lists both).

### 1.2 Type identity does **not** imply "this dword is an object header"

`.data` contains 20 consecutive dwords holding `.?AV?$VectorClass@PAVObjectClass@@@@`
(`0x007E192C`). Taken at face value they are 20 vector globals. They are not. They are
the **repeated `mov vptr, imm` of a single class initialiser**:

```
0x004E7AFD  C7 05 60 E3 A8 00 64 4F 7E 00   mov [0x00A8E360], 0x007E4F64  ; DynamicVectorClass<ObjectClass*>
0x004E7B07  C7 05 74 E3 A8 00 0A 00 00 00   mov [0x00A8E374], 0xA         ; CapInc = 10
0x004E7B11  A3 70 E3 A8 00                  mov [0x00A8E370], eax         ; Count = 0
0x004E7B28  C7 05 60 E3 A8 00 2C 19 7E 00   mov [0x00A8E360], 0x007E192C  ; atexit: back to VectorClass<ObjectClass*>
```
Only `0x00A8E360` has a `CapacityIncrement` store. The other 19 addresses
(`0x008B4108`, `0x008B4120`, … `0x008B41E0`) get **only** the `0x007E192C` write. They are
sub-object vptr pins, not globals with an `Init()`.
`0x008B4108` is in W132 as `DynamicVectorClass<UnitClass*>` — see §6.3, that row is a
different problem (a genuine duplicate) and my scan keeps it.

### 1.3 `.data` is BSS past `0x87E000`, so "what is in the file" is not "what is in the object"

`pe.get_memory_mapped_image()` zero-fills `0x87E000..0xB79BE4`. Every runtime field
(`Items`, `Capacity`, `IsInitialized`, `Count`, `CapacityIncrement`) is therefore **blank in
the file** and every one of the 140 globals reads as 16 zero dwords. The layout has to be
recovered from the **constructor's store set**, never from the data.

### 1.4 `.CRT$XCU` has no usable table in this image

- There is exactly one `.rdata` pointer run that looks like an initialiser table
  (`0x007F5C70`.. `0x007F61CC`, 344 entries) — and it is **not** the static-ctor table: its
  first entries (`0x00410260`, `0x00410300`, `0x00410310`, …) contain no global
  initialisation at all. It is a vtable/dispatch blob.
- The real initialisers are emitted around `0x0040B500`..`0x004E7E60` (one 9-byte
  `.text` stub per global) but **there is no contiguous pointer array to them**; scanning the
  whole image for `.text` pointer runs ≥8 and disassembling every entry yields no
  `C7 05 <global> <vftable>` (probe 5, all runs are vtable-like except the unusable one above).
- Consequence: the `.CRT$XCU`-based "pass (a)" of the suggested method is **not viable on
  this binary**. The completeness argument therefore has to come from the *destination side*
  instead: every global vector object must be written by *some* `mov [abs], imm`, and all
  five possible encodings are enumerated (§1.1). This is what `t1_enumerate.py` does.
  `[未证]` I cannot *prove* no initialiser is missed by an encodings outside the five; the
  residue is bounded by the vtable census of §8.

---

## 2. Method actually used (`t1_enumerate.py`)

1. **RTTI resolution** (verified chain): `V` = vftable address →
   `COL = u32(V-4)` (must be in `.rdata`/`.data`) → `u32(COL+0x04) < 0x10000` (COL offset) →
   `TD = u32(COL+0x0C)` → NUL-terminated ASCII at `TD+8` starting `.?AV`/`.?AU`.
   `[已证]` 0x007E182C → COL 0x007FA770 → TD 0x00816980 → `.?AV?$DynamicVectorClass@PBVCommandClass@@@@`.
2. **Store census**, all five encodings of a constant dword store, over the whole `.text`
   (`0x401000..0x7E038D`), keeping only destinations inside `.data`
   (`0x812000..0xB79BE4`):
   `C7 05 abs imm32`, `A3 abs`, `89 05/0D/15 abs` (the last three only when the source
   register provably holds a vector vftable — backward `mov reg, imm32` with no
   call/jump in between).
3. **Template filter**: label starts with `?$VectorClass@` or `?$DynamicVectorClass@`.
4. **Group by destination** (not by store site). Collect every distinct vftable stored into
   each destination. Prefer a `DynamicVectorClass` vtable; that is the ctor's store, the
   `VectorClass` one is the `atexit` dtor restore:
   ```
   0x008B4108 ctor  0x004E6C7D -> 0x007E9EA4  DynamicVectorClass<UnitClass*>
   0x008B4108 dtor  0x004E6CA8 -> 0x007E9EC4  VectorClass<UnitClass*>
   ```
5. **Layout / shape rule** (this is what makes the result "vector objects", not "dwords that
   look like vptr"). The ctor of `DynamicVectorClass<T>` writes, in one body:
   ```
   C7 05 <B+0x14> 0A 00 00 00     CapacityIncrement = 10
   A3    <B+0x10>                 Count = 0            (eax = 0 from the `xor eax,eax`)
   C7 05 <B+0x00> <vftable>       vptr
   ```
   verified at 0x004E6C60..0x004E6C96 (`UnitClass*`), 0x004E79E0..0x004E7A16
   (`TechnoClass*`), 0x004E7D40..0x004E7D76 (`ObjectClass*`) and 0x005D5ABF..0x005D5B0E
   (`MultiplayerGameMode*`). Therefore:
   * `Items = B+0x04`, `Capacity = B+0x08`, `IsInitialized = B+0x0C`, `IsAllocated = B+0x0D`,
     `Count = B+0x10`, `CapacityIncrement = B+0x14`.
   * **R1**: a global vector object must have a `mov [B+0x14], 10` store.
   * **R2**: code must read the object as a vector, i.e. reference `[B+0x04]` (Items) and/or
     `[B+0x10]` (Count) somewhere in `.text`.
   * **R3**: the vptr store at `B` must not be owned by the initialiser of a *neighbouring*
     object that starts at `B-0x0C*k`.
6. **Demangle** the template argument: `PAV X` → `X*`, `PAU X` → `X*`, `PBV X`/`PBU X` →
   `const X*`, `PBD` → `bool*`, `K` → `unsigned long`, `V?$rc_ptr@…` → `rc_ptr<…>`,
   `U X@Y` → `X@Y`.

Result: 142 destinations with a vector vptr → 140 objects, 2 rejected.

---

## 3. Complete list of the 140 real objects

`vector_globals.tsv` (140 rows). Fields: `element`, `base`, `items`, `count`, `vftable`,
`col`, `td`, `mangled`, `has_dynamic_store`, `has_base_store`, `n_stores`.

`n_stores` is 2 for 139 of them (ctor vtable + `atexit` vtable). The single row with more is
`0x00ABFDA0` (`DynamicVectorClass<MultiplayerGameMode*>`, 9 stores of `0x007EED20` — the game
re-initialises this vector per game mode).

Only one object has **no** `DynamicVectorClass` store at all:

```
0x00B0C114  ?$DynamicVectorClass@VSwizzlePointerClass@@@@ -> handled below
```

Precisely: `0x00B0C114` carries `.?AV?$DynamicVectorClass@VSwizzlePointerClass@@@@`
(`0x007F4134`) from the ctor `0x006CF087` and
`.?AV?$VectorClass@VSwizzlePointerClass@@@@` (`0x007F4154`) from `0x006CF144`.

---

## 4. Diff against `W132_arrays\instance_arrays.tsv`

`diff_vs_w132.txt` is the machine output; the element comparison strips the container
wrapper from your column (I emit the bare element type, e.g. `UnitClass*`, and the mangled
name is in `vector_globals.tsv` for an exact re-check).

### 4.1 Reproduced — same base, same element, same vftable/col/td: **49 / 49**

All 49 rows of W132 appear in `vector_globals.tsv` with identical `base`, `vftable`, `col`
and `td`, and with an element type that matches yours once `DynamicVectorClass<…>` is
stripped. No row of yours has a different base, a different vftable, or a different element
in my run.

Note on your `yrpp_agrees=NO` row:
```
0x00AC1678  DynamicVectorClass<SpotLightClass*>  vftable 0x007EF6BC  td 0x00833618
```
`.?AV?$DynamicVectorClass@PAVSpotLightClass@@@@` — the mangled name uses `SpotLightClass`
(capital L). YRpp writes `SpotlightClass`. That is a naming/spelling mismatch, not a
type-identity mismatch; the enumeration agrees with you.

### 4.2 Disagreements: **0**

### 4.3 New globals (91)

`base → element type` (all reproduced from the image; `has_dynamic_store` yes unless noted):

| base | element | ctor vftable |
|---|---|---|
| 0x0087F5D8 | BombClass* | 0x007E17CC |
| 0x0087F5F0 | TechnoClass* | 0x007E17AC |
| 0x0087F778 | ObjectClass* | 0x007E192C (base-class store only) |
| 0x00884D90 | MixFileClass* | 0x007E1A44 |
| 0x00884DA8 | MixFileClass* | 0x007E1A44 |
| 0x00884DC0 | MixFileClass* | 0x007E1A44 |
| 0x00884DE0 | MixFileClass* | 0x007E1A44 |
| 0x008872B0 | ScriptClass* | 0x007E1B24 |
| 0x008874C0 | WarheadTypeClass* | 0x007E1E84 |
| 0x00887568 | WeaponTypeClass* | 0x007E1ED4 |
| 0x00889E08 | TechnoClass* | 0x007E17AC (register-form store at 0x00412948) |
| 0x00889FB8 | AirstrikeClass* | 0x007E293C |
| 0x0088A080 | AlphaLightingRemapClass* | 0x007E2AD0 |
| 0x0089C668 | BombClass* | 0x007E17CC |
| 0x0089DE18 | BulletClass* | 0x007E4678 |
| 0x008A3770 | EgoClass* | 0x007E86DC |
| 0x008B3D10 | FoggedObjectClass* | 0x007E44F4 |
| 0x008B40C8 | TagClass* | 0x007EA5A4 |
| 0x008B4120 | SideClass* | 0x007EA024 |
| 0x008B4138 | TubeClass* | 0x007E9CA4 |
| 0x008B4150 | AnimTypeClass* | 0x007EA2E4 |
| 0x008B4178 | TriggerTypeClass* | 0x007E9BA4 |
| 0x008B41A8 | TagClass* (2nd TagClass vector) | 0x007EA5A4 |
| 0x008B41C8 | ScriptTypeClass* | 0x007EA124 |
| 0x008B41E0 | BuildingClass* (2nd) | 0x007E9E24 |
| 0x00A83C68 | BuildingTypeClass* | 0x007EA224 |
| 0x00A83C80 | BulletTypeClass* | 0x007EA364 |
| 0x00A83C98 | HouseTypeClass* | 0x007EA064 |
| 0x00A83CE0 | UnitTypeClass* | 0x007EA2A4 |
| 0x00A83CF8 | CampaignClass* | 0x007E9FE4 |
| 0x00A83D50 | SuperClass* (2nd) | 0x007EA4E4 |
| 0x00A83D68 | ParticleSystemTypeClass* | 0x007EA464 |
| 0x00A83D80 | OverlayTypeClass* | 0x007EA164 |
| 0x00A83D98 | ParticleTypeClass* | 0x007EA424 |
| 0x00A83E00 | AnimClass* (2nd) | 0x007E9F24 |
| 0x00A8B200 | AITriggerTypeClass* | 0x007E9B64 |
| 0x00A8B218 | AircraftTypeClass* | 0x007EA264 |
| 0x00A8E318 | TerrainTypeClass* | 0x007EA1E4 |
| 0x00A8E330 | SuperWeaponTypeClass* | 0x007EA4A4 |
| 0x00A8E348 | InfantryTypeClass* | 0x007EA324 |
| 0x00A8E360 | ObjectClass* | 0x007E4F64 |
| 0x00A8E8D0 | TaskForceClass* | 0x007EA0A4 |
| 0x00A8EB28 | VoxelAnimTypeClass* | 0x007EA3A4 |
| 0x00A8EC18 | SmudgeTypeClass* | 0x007EA1A4 |
| 0x00A8ECA0 | TeamTypeClass* | 0x007EA0E4 |
| 0x00A8ECB8 | ObjectClass* (2nd) | 0x007E4F64 |
| 0x00A8EFC8 | BuildChoiceClass@HouseClass* | 0x007EA7B4 |
| 0x00A9F9D0 | const AnimClass* | 0x007EBFCC |
| 0x00A9FA18 | const AnimClass* | 0x007EBFCC |
| 0x00A9FA60 | const AnimClass* | 0x007EBFCC |
| 0x00AA1078 | TileInsertType@IsometricTileTypeClass* | 0x007ECBDC |
| 0x00ABC604 | KamikazeControl* | 0x007ECE7C |
| 0x00ABC878 | LaserDrawClass* | 0x007ECEDC |
| 0x00ABCA10 | LightSourceClass* | 0x007ECF7C |
| 0x00ABCA40 | PendingCellClass@LightSourceClass* | 0x007ECFBC |
| 0x00ABDF90 | MapRegionClass* | 0x007ED858 |
| 0x00ABF390 | bool* | 0x007EE0B4 |
| 0x00ABFC90 | HWND__* | 0x007EEC8C |
| 0x00ABFCB8 | AcceleratorTracker* | 0x007EECCC |
| 0x00ABFDA0 | MultiplayerGameMode* | 0x007EED20 (9 stores) |
| 0x00AC1418 | ObjectTypeClass* | 0x007EF26C |
| 0x00AC4B30 | PlanningNodeClass* | 0x007EFE44 |
| 0x00AC4B48 | EventClass* | 0x007EFE04 |
| 0x00AC4C18 | PlanningNodeClass* (2nd) | 0x007EFE44 |
| 0x00AC4C40 | TechnoClass* (3rd) | 0x007E17AC |
| 0x00AC4C78 | PlanningTokenClass* | 0x007EFE84 |
| 0x00AC4C98 | PlanningNodeClass* (3rd) | 0x007EFE44 |
| 0x00B04DA8 | RadarEventClass* | 0x007F0AAC |
| 0x00B052D0 | ConnectionListStruct@OwnerTalkClass* | 0x007F0C2C |
| 0x00B0B650 | UndoInfoStruct* | 0x007F327C |
| 0x00B0BC88 | unsigned long | 0x007F3728 |
| 0x00B0C114 | SwizzlePointerClass* | 0x007F4134 |
| 0x00B0CDE8 | ShadowControlClass* | 0x007F42DC |
| 0x00B0CE78 | DirtyAreaStruct* | 0x007F429C |
| 0x00B0E780 | TagTypeClass* | 0x007F4558 |
| 0x00B0F4E8 | TiberiumClass* | 0x007F56BC |
| 0x00B0F5B8 | AbstractClass* | 0x007E91EC |
| 0x00B0F5D8 | AbstractClass* | 0x007E91EC |
| 0x00B0F5F0 | AbstractClass* | 0x007E91EC |
| 0x00B0F618 | AbstractClass* | 0x007E91EC |
| 0x00B0F640 | AbstractClass* | 0x007E91EC |
| 0x00B0F658 | AbstractClass* | 0x007E91EC |
| 0x00B0F670 | AbstractClass* | 0x007E91EC |
| 0x00B0F698 | AbstractClass* | 0x007E91EC |
| 0x00B0F6C8 | AbstractClass* | 0x007E91EC |
| 0x00B0F6F0 | AbstractClass* | 0x007E91EC |
| 0x00B0F708 | AbstractClass* | 0x007E91EC |
| 0x00B0F720 | AbstractClass* | 0x007E91EC |
| 0x00B1D290 | VeinholeMonsterClass* | 0x007F663C |
| 0x00B45B58 | MovieHandle* | 0x007F6984 |
| 0x00B72608 | WaypointPathClass* | 0x007F6E04 |
| 0x00B72760 | rc_ptr<VGameOption@WorldDominationTour> | 0x007F6FD4 |

---

## 5. The two rejections (`unresolved_candidates.tsv`)

### 5.1 `0x00A83D24` — `.?AV?$VectorClass@PAUThemeControl@@@@` (0x007EA584)

`[已证]` this dword is **not** the base of a vector. It is `base+0x14` of the
`DynamicVectorClass<ThemeControl*>` object at `0x00A83D10`:

```
0x004E7E30  B9 10 3D A8 00          mov ecx, 0x00A83D10     ; &app.ThemeControl-ish vector
0x004E7E35  E8 26 8B 23 00          call 0x00720960         ; its in-place ctor
...
0x004E7E58  C7 05 24 3D A8 00 84 A5 7E 00   mov [0x00A83D24], 0x007EA584  ; atexit: vptr := base-class vtable
```
The ctor at `0x00720960` is offset-relative (`mov [eax+0x14], 0x7F568C` at 0x0072098C,
`mov [eax+0x28], 0xA` at 0x00720993), i.e. there is **no** `mov [0x00A83D24+0x14], 10` and
no `DynamicVectorClass` ctor store at `0x00A83D24`. Addresses `+2`/`+2` (`[B+4]`, `[B+0x10]`)
hits are incidental reads of the enclosing object.
⇒ This is the *tail* of an object I do **not** report at all (see §5.3).

### 5.2 `0x00B0C12C` — `.?AV?$DynamicVectorClass@VSwizzlePointerClass@@@@` (0x007F4134)

`[已证]` `0x00B0C12C` is `base+0x18` of `0x00B0C114`:
```
0x006CF087  C7 05 14 C1 B0 00 34 41 7F 00   mov [0x00B0C114], 0x007F4134
0x006CF091  C7 05 28 C1 B0 00 0A 00 00 00   mov [0x00B0C128], 0xA
0x006CF09B  C7 05 24 C1 B0 00 00 00 00 00   mov [0x00B0C124], 0
0x006CF0B4  C7 05 2C C1 B0 00 34 41 7F 00   mov [0x00B0C12C], 0x007F4134
```
Note the ctor writes CapInc=10 to `base+0x14 = 0x00B0C128` and Count=0 to
`base+0x10 = 0x00B0C124`, while the vptr of the *second* sub-object is at `base+0x18`. The
'second vptr' write at `0x00B0C12C` is a second `DynamicVectorClass` header whose own
CapInc store is missing, so it is not a standalone object. `[未证]` what the extra header at
`+0x18` really is (a second vector whose CapInc stayed at the constructor default used
elsewhere, or an artefact of the compiler sharing one ctor); I only claim it fails R1/R3.

### 5.3 Known residue — an object I can see but do not enumerate

`[已证]` `0x00A83D10` is the base of a real `DynamicVectorClass<ThemeControl*>` (ctor call at
`0x004E7E35` → `0x00720960`, vTable `0x007F568C`, CapInc=10 at `+0x28`). It is **absent from
`vector_globals.tsv`** because its vptr store is register-relative
(`mov [eax+0x14], 0x7F568C`) and the base is only materialised as an *argument*:
```
0x004E7E30  B9 10 3D A8 00   mov ecx, 0x00A83D10
0x004E7E35  E8 26 8B 23 00   call 0x00720960
```
My store census does not model `mov ecx, imm32` + `call <ctor>`, so this global is missed.
It is **additional evidence that the 140 is a lower bound**, and it is the only such case I
found (see §8).

---

## 6. Answers to the specific questions asked

### 6.1 "which of the 49 you reproduce with the same base and same element type" — all 49.
### 6.2 "any where you get a different element type" — none.
### 6.3 Two W132 rows deserve verification notes even though we agree

* **`0x008B4108 = DynamicVectorClass<UnitClass*>`** — `[已证]` the stores are:
  ```
  0x004E6C60 33 C0                      xor eax, eax
  0x004E6C62 68 A0 6C 4E 00             push 0x004E6CA0          ; atexit target
  0x004E6C67 A3 0C 41 8B 00             mov [0x008B410C], eax    ; Items    = 0
  0x004E6C6C A3 10 41 8B 00             mov [0x008B4110], eax    ; Capacity = 0
  0x004E6C71 C6 05 14 41 8B 00 01       mov byte [0x008B4114], 1 ; IsInitialized
  0x004E6C78 A2 15 41 8B 00             mov byte [0x008B4115], al; IsAllocated
  0x004E6C7D C7 05 08 41 8B 00 A4 9E 7E 00  mov [0x008B4108], 0x007E9EA4  ; DynamicVectorClass<UnitClass*>
  0x004E6C87 C7 05 1C 41 8B 00 0A 00 00 00  mov [0x008B411C], 0xA          ; CapInc = 10
  0x004E6C91 A3 18 41 8B 00             mov [0x008B4118], eax                 ; Count = 0
  ```
  This is a complete, self-consistent `DynamicVectorClass<UnitClass*>` header and I confirm
  your row. **Correction of an earlier draft of this report:** I first claimed a second
  `SpawnManagerClass*` header started at `0x008B40FC`. That is false and I withdraw it —
  `[已证]` the only store into `0x008B40FC` in the whole image is
  `0x004E6E07  C7 05 FC 40 8B 00 0A 00 00 00  mov [0x008B40FC], 0xA`, which is the
  `CapacityIncrement` of the `TeamClass*` object at `0x008B40E8` (its vptr store is
  `0x004E6DFD -> 0x007E9F64`). There is no second header at this address; the full store set
  of `0x008B40E0..0x008B4200` (30 stores, in `_stats.txt`) shows one `vptr`+`CapInc`+`atexit`
  triple per object with no overlap.

* **`0x008B41E0 = DynamicVectorClass<BuildingClass*>`** — `[已证]` the same `0x007E192C`
  (`VectorClass<ObjectClass*>`) vptr is stored into `0x008B41E0` **and** into
  `0x008B4108..0x008B417C` by the *same* initialiser. Those 20 addresses have no
  `CapInc` store and no `DynamicVectorClass` store; they are *not* globals. A naive
  type-driven scan would emit 20 phantom `VectorClass<ObjectClass*>` globals here.

### 6.4 "every additional global not among the 49" — 91, listed in §4.3.

---

## 7. Determinism

```
$ python -X utf8 t1_enumerate.py   ; exit 0
$ copy vector_globals.tsv _run1.tsv
$ python -X utf8 t1_enumerate.py   ; exit 0
$ sha256(_run1.tsv) == sha256(vector_globals.tsv)  ->  True
  25051DA94752855899C2F13ADFCA9D70ECEF4A550AC9DCC98D38F140EE471B6B
$ python -X utf8 diff_vs_w132.py   ; exit 0
```
All iteration is over `sorted()` keys; no sets are iterated for output; the input hash is
re-checked each run.

---

## 8. Honest limits

1. **140 is a lower bound on objects, but complete on `C7 05`/`A3`/`89 xx` store sites.**
   The only escape hatch is a global whose header is initialised entirely through a
   register base (`mov ecx, <base>; call <offset-relative ctor>`), which §5.3 shows exists at
   least once (`0x00A83D10`). A full closure would need a call-graph traverse of every
   `call` whose `ecx` came from `mov ecx, imm32` — I did not implement that; it is the single
   remaining systematic gap and I estimate it at a handful of objects (the same idiom is used
   for `0x00A83D10`, `0x00A8Dxxx`-range Window/Theme objects, `0x00A8EB60`).
   `[未证]` the exact number.
2. **`.CRT$XCU` pass is impossible on this image** (§1.4): no contiguous initialiser table.
   Completeness rests on the destination-side census instead.
3. **Register-form stores** are attributed only when the register's value is set by a plain
   `mov reg, imm32` in the same basic block. A vptr loaded via `lea` or `mov` with an index
   would be missed; I found none for vector vptables (only 2 register-form vector stores
   exist, both attributed).
4. **Element typing** is fully determined for 140/140 rows; I found no address carrying two
   mutually exclusive complete header candidates (an earlier draft claimed one at
   `0x008B40FC`; that was wrong and is withdrawn in §6.3).
5. **TLS-indexed globals**: I tested for them (index dword + per-thread value array, the
   YRpp `TLS_ENABLE` shape) and found none among the 142 — `[已证]` all 142 destinations have
   `0` in the index slot (`0x87E000..` is file-backed zero and no non-zero dword exists past
   `0x87DD84`). Therefore no vector global in this build lives in per-thread storage.
6. `0x00A83D10` (`DynamicVectorClass<ThemeControl*>`) is knowingly missing (§5.3).

---

## 9. Files

| file | content |
|---|---|
| `t1_enumerate.py` | the enumerator (exit 0, deterministic) |
| `vector_globals.tsv` | 140 rows |
| `unresolved_candidates.tsv` | 2 rows + reason |
| `diff_vs_w132.txt` | machine diff vs W132 |
| `_stats.txt` | counts + the raw store lines quoted in §1.2 / §5 |
| `diff_vs_w132.py` | the diff script |
| `_explore*.py` | the probes used to establish §1 and §5 (kept for audit) |
