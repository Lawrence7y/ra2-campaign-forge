# T6 — Per-frame work of the in-game case of `0x006DD8B0`

Binary `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`, PE32, ImageBase `0x400000`,
SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`.
Everything below is **static**: decode + control-flow + vtable data. The game was never
run and nothing was timed.

Grade legend: **[已证]** = byte/address evidence cited. **[未证]** = inferred, or
requires runtime observation.

---

## 0. The headline finding: "case 1" is not the per-frame simulation

This *contradicts the premise in the task statement*, so it is stated first.

The task premise is that `case 1` of `switch (*(int*)(this + 0x2C))` is the in-game
path holding the per-frame simulation cost. **Statically, `case 1` is a win/lose check,
not a simulation step.** **[已证]**

The dispatcher gate, byte-for-byte at `0x006DD8D7`:

```
0x006DD8D7  mov  edx, dword ptr [esi + 0x2c]     ; state
0x006DD8DA  dec  edx                             ; table index = state - 1
0x006DD8DB  cmp  edx, 0x90                       ; 144 max
0x006DD8E1  ja   0x006DFDDD                      ; default -> shared epilogue
0x006DD8E7  jmp  dword ptr [edx*4 + 0x006DFDEC]  ; 145-entry table
```

Table entry 0 (`state == 1`) → `0x006DEA37`. That block is **14 instructions** and
terminates in `ret 0x10`: **[已证]**

```
0x006DEA37  mov  ecx, dword ptr [0xA83D4C]       ; HouseClass *current
0x006DEA3D  mov  eax, dword ptr [esi + 0x90]
0x006DEA43  push ebp
0x006DEA44  mov  edx, dword ptr [ecx + 0x34]
0x006DEA47  cmp  eax, dword ptr [edx + 0xB8]
0x006DEA4D  jne  0x006DDD9B
0x006DEA53  call 0x004FC9E0
0x006DEA58  mov  al, 1
0x006DEA5A..0x006DEA64  pop/pop/pop/pop; add esp,0x240; ret 0x10
```

It calls exactly one function and the two branches are mutually exclusive:

| branch | callee | atlas: size | strings | meaning |
|---|---|---|---|---|
| `jne` not taken → `0x006DEA53` | `0x004FC9E0` | 487 B | `TXT_SCENARIO_WON`, `EVA_MissionAccomplished`, `EVA_YouAreVictorious`, `House.CPP` | victory check |
| `jne` taken → `0x006DDD9B` | `0x004FCBD0` | 495 B | `TXT_SCENARIO_LOST`, `EVA_MissionFailed`, `EVA_YouHaveLost`, `House.CPP` | defeat check |

So `state == 1` costs **one `House.CPP` plausibly-cheap check per frame**, not a
simulation sweep. **[已证]** for the call edges and the string evidence; **[未证]** for
how much work `0x004FC9E0` does internally below its first call (see §7).

**Where the per-frame simulation actually is:** the same dispatcher, in **other**
`state` values. There are **19 loops in 13 case blocks; 14 of them resolve to a
named per-type instance array** (§3) — the other 5 are 3 loops over non-array
data, 1 inline `strcmp`, and 1 walk of an unidentified vector. The dispatcher only
runs one `case` per call, so which of those 19 run in a given frame is a runtime
question — **[未证]** statically, but see §6.

The function is called from exactly one place in `.text`: **[已证]**

```
0x00672605  call 0x006DD8B0      ; inside 0x007265C0
```

`0x007265C0` is itself reached from `0x006DF119`, **inside the `TriggerClass` loop
at `0x006DF0FF`**, per-trigger, guarded by `[TriggerClass+0x24] == [this+0x50]`.

---

## 1. Decomposition of `0x006DD8B0`

**Size / decode [已证]:** 3,071 instructions, span `0x006DD8B0 .. 0x006DFDEA`,
contiguous (no decode gaps). 145 switch entries → **143 distinct case blocks**;
a block ends at the first `ret` (all cases share the epilogue idiom
`pop edi/esi/ebp/ebx; add esp,0x240; ret 0x10`).

**Structure [已证]:** flat `switch`, no fallthrough between blocks. Only
2 backward-branch edges exist *inside a single case block* — the other 17 loops
are the *only* backward branches in the whole function. There is **one** indirect
jump (`0x006DD8E7`); every other control transfer is a direct `jcc`/`jmp`/`ret`.

### 1a. The 13 case blocks that walk a per-type instance array **[已证]**

| case block | `state` = index+1 | array iterated | loops |
|---|---|---|---|
| `0x006DDAF9` | 91 | `InfantryClass` (`0xA83DEC`/`0xA83DF8`) | 1 |
| `0x006DDBF6` | 82 | `FootClass` (`0x8B3DC4`/`0x8B3DD0`) | 1 |
| `0x006DDC71` | 83 | `FootClass` | 1 |
| `0x006DDCEC` | 84 | `TechnoClass` (`0xA8EC7C`/`0xA8EC88`) | 1 |
| `0x006DDEF5` | 60 | `BuildingClass` (`0xA8EB44`/`0xA8EB50`) | 1 |
| `0x006DDF65` | 61 | `BuildingClass` | 1 |
| `0x006DDFD9` | 62 | `BuildingClass` | 1 |
| `0x006DEFBC` | 52 | `BuildingClass` | 1 |
| `0x006DF051` | 12 | `TriggerClass` (`0xA8EAEC`/`0xA8EAF8`) | 1 |
| `0x006DF0E7` | 22 | `TriggerClass` | 1 |
| `0x006DF164` | 54 | `TriggerClass` | 1 |
| `0x006DF49E` | 89 | `ParticleSystemClass` (`0xA8020C`/`0xA80218`) | 1 |
| `0x006DF5D1` | 106 | new vector `0xA8EB04`/`0xA8EB10` **+** `HouseClass` | 3 |
| `0x006DF717` | 111 | `BuildingClass` | 1 |

Full per-case detail in `switch_cases.tsv`. **`UnitClass` (`0x8B410C`) and
`AircraftClass` (`0xA8E394`) are never touched by this dispatcher.** **[已证]** —
0 references to either in the 3,071 instructions.

### 1b. Loop-invariant vs per-object work

Every one of the 19 loops has the identical shape: **[已证]**

```
    mov  reg, dword ptr [<Vector>.Count]     ; 0xA8EB50 etc.
    ; guard: cmp count,0 / jle -> block exit
L:  mov  reg2, dword ptr [<Vector>.Items]    ; hoisted? NO - re-read each iter
    mov  obj, dword ptr [reg2 + idx*4]
    ... per-object body ...
    inc  idx
    cmp  idx, dword ptr [<Vector>.Count]     ; re-read Count each iteration
    jl   L
```

Therefore:
* **Loop-invariant:** nothing is hoisted. Both `Items` and `Count` are re-read
  from memory on every iteration. The loop is a pure `for (i=0;i<Count;i++)`
  over `Items[i]` with no cached bound.
* **Per-object:** everything between `L:` and the `jl`. All direct calls and all
  virtual calls sit in this region, so their cost is `N × cost(call)`.

---

## 2. Cost-centre ranking (proxy, not time)

**Proxy used:** `proxy_score = per_frame_multiplicity × size(function in bytes)`,
where multiplicity is symbolically **N** (one enclosing vector loop ⇒ N objects).
`size` is the atlas `.text` byte extent of the callee.

**Why this proxy, and what it is not.** Size is the only per-function static
quantity available that correlates with work *without* running anything: it
bounds the instructions in the body 1:1 (median ~3.5 bytes/insn in this binary).
It is **not** executed-instruction count, not cycle count, not cache footprint.
A 575-byte function that early-outs costs far less than a 60-byte function called
in a hot inner path. **These numbers must not be read as a performance ordering.**
The defensible reading is: *"if this call runs N times per frame, the static body
that runs N times is this large."*

### Top 15 **[已证]** (address, size, loop; see `cost_centres.tsv`)

`certain?` = the call sits at a **direct** `call imm32`, so it definitely runs
once per object. `no` = the row is one of 4 vtable candidates for a virtual site;
only one of the four runs per object, and which one is **[未证]**.

| # | function | size | proxy | loop head(s) | array | certain? |
|---|---|---|---|---|---|---|
| 1 | `0x00521EB0` | 575 | N×575 | `0x006DDB0D` | `InfantryClass` | no |
| 2 | `0x00436BE0` | 433 | N×433 | `0x006DEFC7` | `BuildingClass` | **yes** |
| 3 | `0x005F4D30` | 398 | N×398 | `0x006DF4C7` | `ParticleSystemClass` | no |
| 4 | `0x004DE7B0` | 396 | N×396 | `0x006DDB0D` | `InfantryClass` | no |
| 5 | `0x00452260` | 252 | N×252 | `0x006DDFED` | `BuildingClass` | **yes** |
| 6 | `0x00447110` | 247 | N×247 | `0x006DDF09` | `BuildingClass` | no |
| 7 | `0x007012C0` | 221 | N×221 | `0x006DDC0C`,`0x006DDC87`,`0x006DDCFB` | `Foot`+`Techno` (3 loops) | no |
| 8 | `0x005F5FA0` | 180 | N×180 | same 3 loops | `Foot`+`Techno` | no |
| 9 | `0x00578290` | 178 | N×178 | `0x006DE3DA` | no array | **yes** |
| 10 | `0x00452360` | 170 | N×170 | `0x006DDF79` | `BuildingClass` | **yes** |
| 11 | `0x005F5280` | 155 | N×155 | `0x006DF4C7` | `ParticleSystemClass` | no |
| 12 | `0x007265C0` | 102 | N×102 | `0x006DF0FF` | `TriggerClass` | **yes** |
| 13 | `0x005B35E0` | 101 | N×101 | same 3 loops | `Foot`+`Techno` | no |
| 14 | `0x005F5320` | 101 | N×101 | `0x006DF4C7` | `ParticleSystemClass` | no |
| 15 | `0x00726720` | 92 | N×92 | `0x006DF06B` | `TriggerClass` | **yes** |

**If only the certain rows count**, the ranking is:
`0x00436BE0` (433) › `0x00452260` (252) › `0x00578290` (178) › `0x00452360`
(170) › `0x007265C0` (102) › `0x00726720` (92) › `0x0068BD80` (59) ›
`0x006E5380` (32) › `0x00653810` (23) › `0x0068BCC0` (20) › `0x00726900` (5) ›
`0x0050E470` (35).

Note `0x006E5380` — small (32 B) but it is a **direct** call inside **six**
different loops, so by the structural measure it is the most frequently
*reached* direct callee in the dispatcher, even though its body is tiny. Size
and reach disagree here, which is exactly why size alone must not be read as cost.

**Structural note (not a perf claim):** functions #7, #8, #13, #16, #17, #20 are
reached from **three different loops** (`FootClass` twice + `TechnoClass`), so
under the proxy their per-frame multiplicity is `N_foot + N_infantry +
N_building + N_techno`-style *additive across arrays*, not a single N. That is
the only place the proxy compounds.

**The table over-counts by construction, and this is deliberate.** Because 11 of
the 12 virtual sites resolve to a 4-candidate set (§5), *each* candidate is
listed at its own N×size. Only **one** of the four executes per object. So a row
that appears only as a virtual candidate is a *possible* contributor, not an
established one, and the 21 rows do **not** sum to anything meaningful. The rows
backed by a **direct** call are the only ones certain to run; those are
`0x006E5380`, `0x00452360`, `0x00452260`, `0x00436BE0`, `0x00653810`,
`0x00578290`, `0x0068BD80`, `0x0068BCC0`, `0x0050E470`, `0x00726720`,
`0x007265C0`, `0x00726900`.
`cost_centres.tsv` does not distinguish the two kinds row-by-row — that
limitation is recorded here rather than hidden.

---

## 3. Loops found: 19 heads — 14 over a named array, 5 not

`loops.tsv` is authoritative. Summary **[已证]**:
(the 5 non-array loops are rows 15–19)

| # | head | backedge | block | array | depth | note |
|---|---|---|---|---|---|---|
| 1 | `0x006DDB0D` | `0x006DDB56` | `0x006DDAF9` | `InfantryClass` | 1 | |
| 2 | `0x006DDC0C` | `0x006DDC60` | `0x006DDBF6` | `FootClass` | 1 | |
| 3 | `0x006DDC87` | `0x006DDCDB` | `0x006DDC71` | `FootClass` | 1 | |
| 4 | `0x006DDCFB` | `0x006DDD66` | `0x006DDCEC` | `TechnoClass` | 1 | |
| 5 | `0x006DDF09` | `0x006DDF54` | `0x006DDEF5` | `BuildingClass` | 1 | |
| 6 | `0x006DDF79` | `0x006DDFC8` | `0x006DDF65` | `BuildingClass` | 1 | |
| 7 | `0x006DDFED` | `0x006DE03D` | `0x006DDFD9` | `BuildingClass` | 1 | |
| 8 | `0x006DEFC7` | `0x006DF040` | `0x006DEFBC` | `BuildingClass` | 1 | |
| 9 | `0x006DF06B` | `0x006DF083` | `0x006DF051` | `TriggerClass` | 1 | |
| 10 | `0x006DF0FF` | `0x006DF126` | `0x006DF0E7` | `TriggerClass` | 1 | **calls the whole dispatcher** |
| 11 | `0x006DF17C` | `0x006DF19C` | `0x006DF164` | `TriggerClass` | 1 | |
| 12 | `0x006DF4C7` | `0x006DF50A` | `0x006DF49E` | `ParticleSystemClass` | 1 | |
| 13 | `0x006DF64F` | `0x006DF661` | `0x006DF5D1` | `HouseClass` | 1 | |
| 14 | `0x006DF72B` | `0x006DF768` | `0x006DF717` | `BuildingClass` | 1 | |
| 15 | `0x006DF5EB` | `0x006DF62E` | `0x006DF5D1` | **none** | 1 | walks `0xA8EB04`/`0xA8EB10` (unidentified) |
| 16 | `0x006DE3DA` | `0x006DE3FB` | `0x006DE3A8` | **none** | 1 | no table read |
| 17 | `0x006DE7C6` | `0x006DE7FE` | `0x006DE7A5` | **none** | 1 | no table read |
| 18 | `0x006DF0B2` | `0x006DF0D6` | `0x006DF094` | **none** | 1 | no table read |
| 19 | `0x006DF5F3` | `0x006DF611` | `0x006DF5D1` | **none** | 2 | **inline `strcmp`, not iteration** |

---

## 4. Nested / quadratic candidates

**Short answer: there is no statically visible loop-in-loop array sweep, but there
is one real re-entrancy that can compound.** **[已证]**

### 4a. The one structural recursion (loop #10)

```
0x006DF0FF  L:  mov  ecx, dword ptr [0xA8EAEC]    ; TriggerClass.Items
0x006DF105      mov  eax, dword ptr [esi + 0x50]
0x006DF108      mov  ecx, dword ptr [ecx + edi*4] ; Trigger
0x006DF10B      mov  edx, dword ptr [ecx + 0x24]
0x006DF10E      cmp  edx, eax
0x006DF110      jne  0x006DF11E
0x006DF112      mov  eax, dword ptr [0xB0E680]
0x006DF117      push eax
0x006DF118      push ebp
0x006DF119      call 0x007265C0        ; <-- walks TriggerClass+0x28 chain,
0x006DF11E  ...                        ;     calling 0x006DD8B0 per element
0x006DF126      jl   0x006DF0FF
```

`0x007265C0` iterates the `[+0x28]` linked list and calls the **entire dispatcher
`0x006DD8B0`** once per list node (`0x007265F7..0x00726605`). Since a
`TriggerClass` case is `state == 22` in this same dispatcher, the nesting is:

```
frame -> dispatcher(state=22) -> loop 0x006DF0FF over TriggerClass (N_triggers)
        -> 0x007265C0 -> loop over [+0x28] list (M nodes)
        -> dispatcher(state=?)  -> possibly loop 0x006DF0FF again ...
```

**This is the quadratic candidate.** Depth is **2 statically visible** and
**unbounded at runtime** — whether the inner dispatcher call re-selects the same
`state == 22` case cannot be decided statically. That is the
*highest-value thing to measure*, and it is exactly what static analysis cannot
settle. **[未证]**

### 4b. False positive, recorded so it is not re-found

Loop #19 (`0x006DF5F3` → `0x006DF611`) looks nested inside loop #15
(`0x006DF5EB` → `0x006DF62E`) with depth 2. It is **not** an array walk: it is
GCC/MSVC's inline `strcmp` idiom comparing two `char*` byte-by-byte. **[已证]**
by the body (`mov bl,[eax]` / `cmp bl,[edi]` / `add eax,2` / `add edi,2` /
`test cl,cl` / `jne`). Treating it as iteration would be wrong.

### 4c. Arrays that are *not* nested with each other

The 13 case blocks are mutually exclusive alternatives of a flat `switch`, so
e.g. the `InfantryClass` loop and the `BuildingClass` loops never nest.
**[已证]** — `switch` case blocks share no code and each ends in `ret`.

---

## 5. Virtual calls

12 `call dword ptr [reg+disp]` sites inside loop bodies. For each, the vtable
pointer is loaded from `[obj+0]` and the slot is read out of `.rdata`.

**Important correction to first impressions:** in 11 of 12 cases the slot does
*not* yield one address. Reading the slot from **every** vtable whose RTTI is a
class related to the loop's element type gives **4 distinct candidates** per
site — i.e. the site dispatches to a base-class slot, and the concrete override
varies with the derived type of the object. Reporting a single "resolved target"
would have been an over-claim, so `unresolved_virtuals.tsv` lists **all**
candidates and the script emits no single-address resolution. **[已证]** for the
slot values; **[未证]** for which override runs.

| call site | loop | slot | class walked | candidates |
|---|---|---|---|---|
| `0x006DDB46` | `0x006DDB0D` | `+0x514` | `InfantryClass` | `0x004D9FF0`, `0x004DE7B0`, `0x00521EB0`, `0x005220F0` |
| `0x006DDC19` | `0x006DDC0C` | `+0x184` | `FootClass` | `0x0041BF40`, `0x005B3040`, `0x007012C0`, `0x0070E340` |
| `0x006DDC52` | `0x006DDC0C` | `+0x1E8` | `FootClass` | `0x005B35E0`, `0x005F5FA0`, `0x005F6960`, `0x005F6A10` |
| `0x006DDC93` | `0x006DDC87` | `+0x184` | `FootClass` | same as `0x006DDC19` |
| `0x006DDCCD` | `0x006DDC87` | `+0x1E8` | `FootClass` | same as `0x006DDC52` |
| `0x006DDD18` | `0x006DDCFB` | `+0x184` | `TechnoClass` | same as `0x006DDC19` |
| `0x006DDD26` | `0x006DDCFB` | `+0x184` | `TechnoClass` | same as `0x006DDC19` |
| `0x006DDD58` | `0x006DDCFB` | `+0x1E8` | `TechnoClass` | same as `0x006DDC52` |
| `0x006DDF44` | `0x006DDF09` | `+0x1A0` | `BuildingClass` | `0x00447110`, `0x005B3040`, `0x005F43A0`, `0x005F43C0` |
| `0x006DF0CA` | `0x006DF0B2` | `+0x20`  | **unresolved** | — (object from global `0xA8B230`) |
| `0x006DF4E7` | `0x006DF4C7` | `+0x1B8` | `ParticleSystemClass` | `0x0041BEA0`, `0x004264B0`, `0x005F43F0`, `0x005F5320` |
| `0x006DF4FC` | `0x006DF4C7` | `+0xF8`  | `ParticleSystemClass` | `0x0041BE60`, `0x005F4D30`, `0x005F5280`, `0x006301E0` |

### Unresolved virtuals **[未证]**

1. **`0x006DF0CA`, slot `[eax+0x20]`** — the object comes from global `0xA8B230`,
   not from a type array, so the concrete class is not inferable from the loop.
2. **11 of 12 sites are only narrowed to a 4-candidate set.** The vtable atlas
   holds 1,214 vtables for 954 classes, so most classes expose only a primary
   vtable and the derived overrides are not enumerated. Narrowing to one address
   needs either a full vtable dump per class or runtime type observation.
3. **Call-graph blindness.** None of these 12 sites appears as an edge in
   `calledges.raw.log`, because a vtable call has no static edge. So
   `n_callers = 0` in `function_atlas.tsv` is **not** evidence of dead code.
4. **The cost-centre table is therefore a lower bound on the call set** for those
   loops: it includes the direct calls exactly, and the virtual candidates as a
   *set of four* (each contributes its own N×size term if it is the live one, and
   only one of the four runs per object).

---

## 6. What static analysis cannot tell you

Stated plainly, because the previous rounds failed by measuring the wrong thing.

1. **Cycle counts / wall time.** No timing was collected and none can be derived
   from bytes. "Structurally largest static body" ≠ "slowest".
2. **Which of the 143 cases actually runs this frame.** `state` is a field of the
   `this` object; the dispatcher runs one case per call. Whether a given frame
   reaches the `InfantryClass` case, the `BuildingClass` cases, both, or neither
   is decided by runtime state. **[未证]**
3. **Whether a loop is skipped by a dirty/valid flag.** Every array loop's
   *guard* is `cmp Count,0 / jle` — so an **empty** array skips. But per-object
   early-outs are data-dependent (see §6.4).
4. **Data-dependent branches inside loop bodies.** Several bodies test flags on
   each object before doing work — e.g. `0x006DDB16` tests `[obj+0x90]`,
   `[obj+0x74]`, `[obj+0x81]` and `[obj+0x34]` in sequence before reaching the
   `+0x514` virtual call **[已证]**. Whether those tests pass for any given
   object is runtime-only. **The most expensive-looking call in a loop may never
   execute for most objects.** This is the single most likely reason earlier
   "many units ⇒ slow" measurements disagreed with each other.
5. **Cache / memory effects.** Objects are `Items[i]` — a pointer array indexing
   heap allocations. Spatial locality across the `N` objects is a property of the
   allocator at runtime, invisible to this analysis.
6. **N values.** The `Count` fields live in BSS (`.data` is file-backed only to
   `0x87E000`, and all ten vector blocks are above that). **[已证]** by reading
   zero from the mapped image. No N is claimed anywhere in this report.
7. **The `state == 1` cost.** `0x004FC9E0` (487 B) and `0x004FCBD0` (495 B) are
   *resolved and bounded*, but their internal work below their first callee is
   not expanded here. They are `House.CPP` scenario checks, so the prior that
   they are cheap is plausible — and **plausible is not proven**. **[未证]**
8. **The identity of vector `0xA8EB00`/`0xA8EB04`/`0xA8EB10`** touched by loop
   `0x006DF5EB` (case 106). It was not in the task's table. It has the same
   `base/Items=+4/Count=+0x10` layout, so it is *a* `DynamicVectorClass<T*>`, but
   **which** `T` is **unresolved**. Its `Count` read is at `0x006DF5D1`, `Items`
   at `0x006DF5E2`.
9. **Whether `0x006DD8B0` is itself re-entered** (the §4a quadratic). Depth ≥ 2 is
   certain; ≥ 3 requires observing `state` at runtime.

---

## 7. Artifacts

| file | contents |
|---|---|
| `t6_frame.py` | re-runnable, deterministic analyzer |
| `switch_cases.tsv` | 145 cases → block, extent, size, arrays touched, loop count |
| `loops.tsv` | 19 loop heads: backedge, owning case block, state, array, direct calls, depth, note |
| `cost_centres.tsv` | 35 ranked callees, N×size proxy, plus `reach_kind` / `certain_to_run` |
| `virtual_calls.tsv` | 12 vcall sites, one row per (site, candidate class) |
| `unresolved_virtuals.tsv` | the 12 sites with *why* each is not a single address |
| `run.log` | console transcript |

Determinism was checked by running the script twice and diffing
`cost_centres.tsv` — byte-identical.

Reproduce: `python -X utf8 t6_frame.py` (writes only into this directory).
