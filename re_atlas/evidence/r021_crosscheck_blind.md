# R-021 blind cross-check (independent derivation from bytes)

## 1. Environment and integrity gate

| item | value |
|---|---|
| target | `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe` |
| size | 4825360 bytes |
| SHA-256 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` |
| expected prefix | `73201cc021497c95` |
| gate | **PASS** (full digest shown above; prefix matches) |
| tooling | Python 3 + capstone 5.0.7; `read_va`/`cstr` from `re_atlas/tools/dump_rules_sections.py`, `sweep` from `re_atlas/tools/text_sweep.py` |
| read-only | no writes to the exe, no execution of it; only this report was created |

Whole-.text sweep result (own run): **1,389,579 instructions**, span `0x401000`–`0x7E0FFD`,
40 resync records, first stop exactly at `0x46F5A0 -> 0x46F621` (the documented trap),
last stop `0x7E0FFF` with no resync target (true end of `.text`). All address-order
attribution below is from that sweep, not from a single `md.disasm()` pass.

---

## 2. BLIND PHASE

### A1. Pointer table at 0x007F0C78

Contiguous dword table `0x7F0C78` .. `0x7F0CF4` = **32 slots** (span `0x7F0C78`–`0x7F0CF7`);
**31 resolve to non-empty printable strings**. Slot `0x7F0CF4` -> `0x00889F64`, which lies in
`.data` BSS (RVA 0x489F64, no raw backing) and reads empty; it is used as a *default-value*
argument by F3, not as a section name. The next dword `0x7F0CF8` -> `0x00808A80` (zero/BSS)
and beyond that the values are code addresses (`0x0067AA30` …), i.e. the table ends.

Requested entries (pointer, string, hex of string):

| slot | pointer | bytes | string |
|---|---|---|---|
| 0x7F0C94 | 0x00839E5C | `43 6F 6C 6F 72 73 00` | `"Colors"` |
| 0x7F0C98 | 0x00839E50 | `43 6F 6C 6F 72 41 64 64 00` | `"ColorAdd"` |
| 0x7F0C9C | 0x00826278 | `47 65 6E 65 72 61 6C 00` | `"General"` |
| 0x7F0CE8 | 0x00839D3C | `41 64 76 61 6E 63 65 64 43 6F 6D 6D 61 6E 64 42 61 72 00` | `"AdvancedCommandBar"` |
| 0x7F0CEC | 0x00839D1C | `4D 75 6C 74 69 70 6C 61 79 65 72 41 64 76 61 6E 63 65 64 43 6F 6D 6D 61 6E 64 42 61 72 00` | `"MultiplayerAdvancedCommandBar"` |
| 0x7F0CF0 | 0x00839D10 | `42 75 74 74 6F 6E 4C 69 73 74 00` | `"ButtonList"` |

Full table order: SpecialWeapons, AudioVisual, CrateRules, CombatDamage, Radiation,
ElevationModel, WallModel, Colors, ColorAdd, General, MultiplayerDialogSettings, Maximums,
InfantryTypes, Countries, VehicleTypes, AircraftTypes, Sides, SuperWeaponTypes, BuildingTypes,
TerrainTypes, Teams, SmudgeTypes, OverlayTypes, AI, Powerups, IQ, JumpjetControls, Movies,
AdvancedCommandBar, MultiplayerAdvancedCommandBar, ButtonList.

Slot-reference census over the whole sweep: slots `0x7F0C78`–`0x7F0CF4` are referenced only from
`.text` `0x668B13`–`0x6746A4`; **0x7F0CEC has exactly one reference in the entire image**
(`0x0067465E`), **0x7F0CE8 exactly one** (`0x00674666`).

### A2. F1 = 0x006686C0

```
006686C0  81 EC D0 00 00 00      sub esp, 0xD0
006686C6  A1 E0 54 B0 00         mov eax,[0xB054E0]
006686CB  53 / 55 / 8B E9 / 56 / 57 / 85 C0 / 89 6C 24 14 / 74 24 ...
```
- TRUE extent **0x006686C0 – 0x00668BE7** (last instruction start `0x668BE5`).
- Terminating `ret`: **`0x00668BE5`, `C2 04 00` = `ret 4`** (operand 4). Function end `0x668BE8`.
- Padding `90`×8 at `0x668BE8`–`0x668BEF`, next function starts `0x668BF0`.
- Highest in-function jump target = `0x668BAF` (`jmp` at `0x668AF7`), so no detached tail.
- 430 instructions to the ret.
- Calls to `0x00668BF0` (F2): **3**, at `0x00668A27`, `0x00668B05`, `0x00668BAA`.
- Direct calls to the four named loaders:
  - `0x66D3A0` — **no** (not present in F1's 24 direct call targets)
  - `0x66D530` — **no**
  - `0x674650` — **no**
  - `0x66B900` — **no**
- F1 makes 24 direct `call rel32` and 20 **indirect** `call dword ptr [edx+0x20]`
  (`0x66872F` … `0x6689DB`, a loop over an object array). The indirect sites are not statically
  resolvable and are therefore not excluded by direct-target analysis.

### A3. F2 = 0x00668BF0

```
00668BF0  83 EC 2C               sub esp, 0x2C
00668BF3  53 55 56 8B 74 24 3C   push ebx/ebp/esi ; mov esi,[esp+0x3C]
00668BFA  57 8B F9 56            push edi ; mov edi,ecx ; push esi
00668BFE  E8 9D 47 00 00         call 0x66D3A0
```
- First `ret` (linear scan): `0x00668F8D`, `C2 04 00` = `ret 4`.
- **Jumps whose target lands beyond that ret:**

| jump addr | insn | target |
|---|---|---|
| 0x00668F71 | `74 1D` `je` | `0x00668F90` |
| 0x00668F76 | `74 18` `je` | `0x00668F90` |

- **Detached tail block: yes, begins at `0x00668F90`** (decoded from the jump target, not from
  `first_ret+3`). Contents:
  ```
  00668F90  33 C0            xor eax,eax
  00668F92  8B CF            mov ecx,edi
  00668F94  50               push eax
  00668F95  56               push esi
  00668F96  E8 B5 B6 00 00   call 0x674650
  00668F9B  5F 5E 5D 5B      pop edi/esi/ebp/ebx
  00668F9F  83 C4 2C         add esp,0x2C
  00668FA2  C2 04 00         ret 4
  ```
  Its epilogue (`pop edi/esi/ebp/ebx; add esp,0x2C`) matches F2's own prologue frame
  (`sub esp,0x2C` + 4 pushes), confirming it is a second exit of F2, not a new function.
- **Real terminating `ret`: `0x00668FA2`, `ret 4` (operand 4).** TRUE extent
  **0x00668BF0 – 0x00668FA4**. Padding `90`×11 at `0x668FA5`–`0x668FAF`; next function
  (`0x668FB0`, `mov eax,[0x7F0C78]`) starts at `0x668FB0`.
- Note: `0x668F8D` is *not* the function boundary — it is the fall-through exit of the
  `eax ∉ {0,5}` path; the two `je` at `0x668F71`/`0x668F76` jump over it into the tail.
- No indirect `call`/`jmp` anywhere in F2's true extent; all 60 calls are direct `rel32`.

### A4. Loader calls inside F2's TRUE extent (0x668BF0–0x668FA4)

F2 contains **60 direct `call rel32`** in total (no indirect calls). **29 of them target a `Read_*`
section loader** (target in the 0x668FB0–0x674xxx loader range: 0x66B900, 0x66BBB0, 0x66CF70,
0x66D150, 0x66D1F0, 0x66D270, 0x66D3A0, 0x66D530, 0x668FB0, 0x6691E0, 0x671EA0 … 0x674650);
**26 distinct loader targets**. Address-ordered loader calls:

| # | call site | target | section loader |
|---|---|---|---|
| 1 | 0x00668BFE | 0x0066D3A0 | Read_Colors |
| 2 | 0x00668CDE | 0x00672440 | Read_Sides |
| 3 | 0x00668E78 | 0x00672660 | Read_BuildingTypes |
| 4 | 0x00668E80 | 0x00672360 | Read_VehicleTypes |
| 5 | 0x00668E88 | 0x006723D0 | Read_AircraftTypes |
| 6 | 0x00668E90 | 0x00672280 | Read_InfantryTypes |
| 7 | 0x00668E98 | 0x006728B0 | Read_Animations |
| 8 | 0x00668EA0 | 0x00672920 | Read_VoxelAnims |
| 9 | 0x00668EA8 | 0x00672A00 | Read_Particles |
| 10 | 0x00668EB0 | 0x00672A70 | Read_ParticleSystems |
| 11 | 0x00668EB8 | 0x006743D0 | Read_JumpjetControls |
| 12 | 0x00668EC0 | 0x00671EA0 | Read_MultiplayerDialogSettings |
| 13 | 0x00668EC8 | 0x00672AE0 | Read_AI |
| 14 | 0x00668ED0 | 0x00673E80 | Read_Powerups |
| 15 | 0x00668ED8 | 0x00674000 | Read_LandCharacteristics |
| 16 | 0x00668EE0 | 0x00674240 | Read_IQ |
| 17 | 0x00668EE8 | 0x0066D530 | Read_General |
| 18 | 0x00668F02 | 0x0066D270 | Read_Difficulty ("Easy") |
| 19 | 0x00668F14 | 0x0066D270 | Read_Difficulty ("Normal") |
| 20 | 0x00668F26 | 0x0066D270 | Read_Difficulty ("Difficult") |
| 21 | 0x00668F2E | 0x0066B900 | Read_CrateRules |
| 22 | 0x00668F36 | 0x0066BBB0 | Read_CombatDamage |
| 23 | 0x00668F3E | 0x0066CF70 | Read_Radiation |
| 24 | 0x00668F46 | 0x0066D150 | Read_ElevationModel |
| 25 | 0x00668F4E | 0x0066D1F0 | Read_WallModel |
| 26 | 0x00668F56 | 0x006691E0 | Read_AudioVisual |
| 27 | 0x00668F5E | 0x00668FB0 | Read_SpecialWeapons |
| 28 | 0x00668F81 | 0x00674650 | Read_AdvancedCommandBar (flag=1 path) |
| 29 | 0x00668F96 | 0x00674650 | Read_AdvancedCommandBar (flag=0 path, tail) |

The remaining 31 calls are engine helpers, in address order:
`0x526960` GetKeyCount ×7 (0x668C1F, 0x668C93, 0x668CEC, 0x668D3D, 0x668D8D, 0x668DDB, 0x668E2C),
`0x526CC0` ×7 (0x668C3E, 0x668CB6, 0x668D0E, 0x668D60, 0x668DAE, 0x668DFD, 0x668E4F),
`0x528A10` GetString ×6 (0x668CC4, 0x668D1D, 0x668D6F, 0x668DBB, 0x668E0C, 0x668E5E), then
one each: 0x668C0D→0x679F40, 0x668C51→0x4355B0, 0x668C6A→0x474B50, 0x668CD1→0x512680,
0x668D2A→0x5FEC70, 0x668D7C→0x6CEEF0, 0x668DC8→0x75E3B0, 0x668E19→0x6B5910,
0x668E6B→0x71E2A0, 0x668EF0→0x679A10, 0x668F65→0x721D10.
(7 + 7 + 6 + 11 = 31; 31 + 29 loaders = 60 total calls.)
Two of these — `0x679F40` and `0x679A10` — live above 0x674xxx and are not section loaders;
`0x679A10` walks object arrays via `[vtbl+0x64]`.

**Totals:** loader calls = **29**, distinct targets = **26**. Targets called more than once:
**`0x66D270` ×3** (0x668F02, 0x668F14, 0x668F26) and **`0x674650` ×2** (0x668F81, 0x668F96,
mutually exclusive branches — see A6/A7).
28 is the count obtained if the window stops at the first `ret` (0x668F8D), which drops call #29.

### A5. Inline (non-loader) section references inside F2's true extent

Direct table-slot reads / literal pushes, address order — **7 distinct sections**:

| addr | insn | slot / literal | section |
|---|---|---|---|
| 0x668C03 | `mov eax,[0x7F0C98]` | 0x7F0C98 | ColorAdd |
| 0x668C16 | `mov ecx,[0x7F0C98]` | 0x7F0C98 | ColorAdd |
| 0x668C34 | `mov edx,[0x7F0C98]` | 0x7F0C98 | ColorAdd |
| 0x668C56 | `mov ecx,[0x7F0C98]` | 0x7F0C98 | ColorAdd |
| 0x668C8B | `mov eax,[0x7F0CAC]` | 0x7F0CAC | Countries |
| 0x668CA0 | `mov edx,[0x7F0CAC]` | 0x7F0CAC | Countries |
| 0x668CBC | `mov eax,[0x7F0CAC]` | 0x7F0CAC | Countries |
| 0x668CE3 | `mov ecx,[0x7F0CD0]` | 0x7F0CD0 | OverlayTypes |
| 0x668CF9 | `mov eax,[0x7F0CD0]` | 0x7F0CD0 | OverlayTypes |
| 0x668D13 | `mov ecx,[0x7F0CD0]` | 0x7F0CD0 | OverlayTypes |
| 0x668D34 | `mov edx,[0x7F0CBC]` | 0x7F0CBC | SuperWeaponTypes |
| 0x668D4A | `mov ecx,[0x7F0CBC]` | 0x7F0CBC | SuperWeaponTypes |
| 0x668D65 | `mov edx,[0x7F0CBC]` | 0x7F0CBC | SuperWeaponTypes |
| **0x668D86** | `push 0x83A0D0` | 0x83A0D0 | **Warheads** |
| 0x668DA7 | `push 0x83A0D0` | 0x83A0D0 | Warheads |
| 0x668DB4 | `push 0x83A0D0` | 0x83A0D0 | Warheads |
| 0x668DD2 | `mov ecx,[0x7F0CCC]` | 0x7F0CCC | SmudgeTypes |
| 0x668DE8 | `mov eax,[0x7F0CCC]` | 0x7F0CCC | SmudgeTypes |
| 0x668E02 | `mov ecx,[0x7F0CCC]` | 0x7F0CCC | SmudgeTypes |
| 0x668E23 | `mov edx,[0x7F0CC4]` | 0x7F0CC4 | TerrainTypes |
| 0x668E39 | `mov ecx,[0x7F0CC4]` | 0x7F0CC4 | TerrainTypes |
| 0x668E54 | `mov edx,[0x7F0CC4]` | 0x7F0CC4 | TerrainTypes |

**Direct `push 0x83a0d0`: present, three times (0x668D86 / 0x668DA7 / 0x668DB4).**
Bytes at 0x83A0D0: `57 61 72 68 65 61 64 73 00` = **`"Warheads"`**. `0x7F0CCC`
("SmudgeTypes") is read immediately after it, so Warheads is a literal-pushed section that has no
slot in the pointer table.

### A6. F3 = 0x00674650

```
00674650  8A 44 24 08            mov al, byte ptr [esp+8]     ; arg2 = flag
00674654  81 EC 00 02 00 00      sub esp, 0x200
0067465A  84 C0                  test al, al
0067465C  53                     push ebx
0067465D  57                     push edi
0067465E  8B 3D EC 0C 7F 00      mov edi, [0x7F0CEC]          ; default = MultiplayerAdvancedCommandBar
00674664  75 06                  jne 0x67466C                 ; flag != 0 -> keep 0x7F0CEC
00674666  8B 3D E8 0C 7F 00      mov edi, [0x7F0CE8]          ; flag == 0 -> AdvancedCommandBar
0067466C  8B 9C 24 0C 02 00 00   mov ebx, [esp+0x20C]         ; arg1 = INI file
00674673  57 8B CB               push edi ; mov ecx, ebx
00674676  E8 95 21 EB FF         call 0x526810                ; GetSection(section)
```

- References **both** 0x7F0CE8 and 0x7F0CEC: yes (`0x674666`, `0x67465E`).
- The decider is **`test al,al` at `0x67465A`** on the value loaded by
  **`mov al, byte ptr [esp+8]` at `0x674650`** — i.e. the second argument (declared `F3(ini, flag)`).
  `0x7F0CEC` is loaded unconditionally first (fall-through value) and `jne 0x67466C` at `0x674664`
  keeps it when the flag is non-zero; only `flag == 0` overwrites it with `0x7F0CE8`.
  So: **flag != 0 -> "MultiplayerAdvancedCommandBar", flag == 0 -> "AdvancedCommandBar".**
- Extent: first `ret` `0x67471B` (`ret 8`); one jump beyond it — `0x674682 je 0x67471E` — a
  detached tail `0x67471E`–`0x674728` (`pop edi; xor al,al; pop ebx; add esp,0x200; ret 8`).
  Real terminating `ret`: **`0x674728`, `ret 8`**.
- **Integer arguments passed to F3 from inside F2:**
  - `0x668F78` `mov eax,1` -> `0x668F7F` `push eax` -> `0x668F80 push esi` -> **`0x668F81 call 0x674650`**
    (arg2 = **1**)
  - `0x668F90` `xor eax,eax` -> `0x668F94` `push eax` -> `0x668F95 push esi` -> **`0x668F96 call 0x674650`**
    (arg2 = **0**)
  Both sites pass only 1/0; the first arg is always the INI object in `esi`.
  Which one executes is decided by the 0xA8B238 test immediately before (A7).

### A7. Global 0xA8B238

- Whole-.text sweep (resynced): **790** instruction references. Raw byte scan of `.text` finds
  **791** occurrences of `38 B2 A8 00`; the one extra (`0x5098F1`) lies inside an embedded
  data/jump-table run beginning `0x5098DC` (`ab 98 50 00 4f 97 50 00 86 97 50 00 90 90 90 90 a1 38 b2 a8 00 …`)
  and is not an instruction boundary — an artefact, not a reference.
- Immediate values compared against: **4** (117 sites), **5** (4), **1** (5), **3** (3), **2** (1);
  the remaining `cmp [0xA8B238], reg` sites compare against `ebx` (16), `ebp` (16), `esi` (10),
  `edi` (8), `eax` (1) — registers that are zeroed in the enclosing straight-line code at every
  site inspected, i.e. effectively `== 0` tests.
- Writers: `mov [0xA8B238],4` (0x52DD61), `3` (0x52DD7F, 0x52E3C6), **`5` (0x52E10F)**,
  **`0` (0x5EFDC3)**, plus register stores at 0x48CF94, 0x52E175/0x52E1FE/0x52E213/0x52E2B3/
  0x52E2FA/0x52E337/0x52E42B/0x52E553/0x52E577/0x52E599/0x52E5B6/0x52E5D4, 0x5EF720/0x5EF73A/
  0x5EF842/0x5EF85A/0x5EFDAB/0x5EFDE3/0x5EFDF6, 0x67E4E8, 0x77B532/0x77B562/0x77B585/0x77B5D2.

**Inside F2 (bytes only):**

```
00668F6A  A1 38 B2 A8 00        mov eax,[0xA8B238]
00668F6F  85 C0                  test eax,eax
00668F71  74 1D                  je  0x668F90        ; == 0  -> tail branch
00668F73  83 F8 05               cmp eax,5
00668F76  74 18                  je  0x668F90        ; == 5  -> same tail branch
00668F78  B8 01 00 00 00         mov eax,1
00668F7D  8B CF / 50 56         mov ecx,edi ; push eax ; push esi
00668F81  E8 CA B6 00 00         call 0x674650      ; F3(ini, 1)
00668F86  5F 5E 5D 5B 83 C4 2C C2 04 00   -> ret 4
00668F90  33 C0                  xor eax,eax        ; tail
00668F94  50 56                  push eax ; push esi  (arg2 = 0)
00668F96  E8 B5 B6 00 00         call 0x674650      ; F3(ini, 0)
```

So in F2: value **0** and value **5** take the identical path — `F3(ini, 0)`, i.e. section
`"AdvancedCommandBar"`. Any other value takes `F3(ini, 1)` -> `"MultiplayerAdvancedCommandBar"`.
The two paths have separate epilogues (0x668F86 vs 0x668F9B) and separate `ret 4`s
(0x668F8D vs 0x668FA2).

**Inside F1:** `0x668B8E  cmp dword ptr [0xA8B238], esi` / `0x668B94 je 0x668BAF`, with
`esi = 0` (zeroed at `0x668B8C xor esi,esi` when the ColorAdd loop is skipped/completes);
when the global equals that value the third `call 0x668BF0` at `0x668BAA` is skipped
(jump straight to `0x668BAF`).

**Other `cmp ...,5` sites (the remaining three):**
- `0x5D614F cmp [0xA8B238],5` -> `0x5D6156 sete byte ptr [esp+0x13]` (materialises a bool).
- `0x67E3BD cmp ...,5` / `0x67E3C4 jne 0x67E3F9`; equal path pushes `0x83D5DC`
  `"Writing Skirmish Session.Options\n"` and calls the logger at `0x4068E0` (a stub `ret`).
- `0x67F72E cmp ...,5` / `0x67F735 jne 0x67F76A`; equal path pushes `0x83D634`
  `"Reading Skirmish Session.Options\n"` before the same logger.
- `0x687B18 cmp ...,5` / `0x687B1F jne 0x687B7B`; equal path additionally gates on
  `byte [0xA8ED91]` and builds a string that includes `0x83DB90` = `"TMCJ4F.INI"`.
  (The failure path string in the two 0x67Exxx sites is `0x83D584` = `"\t***** FAILED!\n"`.)

### A8. Verbatim strings

| VA | bytes | string |
|---|---|---|
| 0x818134 | `45 61 73 79 00` | `Easy` |
| 0x81BB60 | `4E 6F 72 6D 61 6C 00` | `Normal` |
| 0x83A0C4 | `44 69 66 66 69 63 75 6C 74 00` | `Difficult` |

Neighbourhood evidence for the difficulty triple: `0x818124` = `"Hard"`, `0x81812C` =
`"Medium"`, `0x818134` = `"Easy"`. **`0x818124` ("Hard") has 0 references anywhere in `.text`.**
The three difficulty calls in F2 push `0x818134`, `0x81BB60`, `0x83A0C4`
(`0x668EF5`, `0x668F07`, `0x668F19`), each followed by `lea edx,[edi+0x1538 / 0x1588 / 0x15D8]`
and `call 0x66D270` (Read_Difficulty). The same triple is pushed again in F3's sibling reader
`0x674500` at `0x674508`, `0x67451A`, `0x67452C`.

---

## 3. GRADE TABLE

| # | claim | verdict | byte evidence |
|---|---|---|---|
| C1 | F1 extent 0x6686C0–0x668BE5, `ret 4` | **CONFIRMED** | head `81 EC D0 00 00 00` at `0x6686C0`; `81 C4 D0 00 00 00` at `0x668BDF`; `C2 04 00` at `0x668BE5` = `ret 4`; end `0x668BE8`, `90`×8 padding to `0x668BF0`; max jump target inside range = `0x668BAF` |
| C2 | F1 calls F2 exactly 3× and no per-section loader directly | **CONFIRMED** | `call 0x668BF0` at `0x668A27`, `0x668B05`, `0x668BAA`; F1's 24 direct call targets contain none of 0x66D3A0/0x66D530/0x674650/0x66B900. Caveat: F1 also has 20 indirect `call [edx+0x20]` sites (not statically resolvable), which do not contradict the count of the direct F2 calls |
| C3 | F2 extent 0x668BF0–0x668F8D, `ret 4` | **REFUTED** | `je 0x668F90` at `0x668F71` and `0x668F76` land beyond `0x668F8D`. Detached tail `0x668F90`–`0x668FA4` (same frame: `add esp,0x2C` + 4 pops) with real terminator `ret 4` at **`0x668FA2`**. True extent 0x668BF0–0x668FA4; padding starts `0x668FA5` |
| C4 | F2 contains exactly 28 loader calls | **REFUTED** (as stated) | 28 is only the count in the truncated 0x668BF0–0x668F8D window. In the true extent there are **29** loader-entry calls (26 distinct): the 28 plus `call 0x674650` at `0x668F96`. Repeated targets: `0x66D270` ×3, `0x674650` ×2 |
| C5 | 0x7F0CEC ("MultiplayerAdvancedCommandBar") never used by any Read_* | **REFUTED** | `0x67465E  mov edi,[0x7F0CEC]` inside `Read_AdvancedCommandBar` (0x674650); pushed to `GetSection` at `0x674673`/`0x674676`. It is the non-zero-flag branch, taken from F2 via `0x668F81` when 0xA8B238 ∉ {0,5} |
| C6 | difficulty key names are "Easy", "Normal", "Hard" | **REFUTED** | F2 pushes `0x818134` ("Easy"), `0x81BB60` ("Normal"), **`0x83A0C4` ("Difficult")** at `0x668EF5`/`0x668F07`/`0x668F19`. "Hard" exists at `0x818124` but has zero `.text` references |
| C7 | F2 inline section order ColorAdd, Countries, OverlayTypes, SuperWeaponTypes, Warheads, SmudgeTypes, TerrainTypes | **CONFIRMED** | first inline refs at `0x668C03` (0x7F0C98), `0x668C8B` (0x7F0CAC), `0x668CE3` (0x7F0CD0), `0x668D34` (0x7F0CBC), `0x668D86` (`push 0x83A0D0`), `0x668DD2` (0x7F0CCC), `0x668E23` (0x7F0CC4) — exactly that order, 7 distinct sections |

---

## 4. Surprises, caveats, and what was not verified

1. **The "28 loaders" figure is an artefact of the truncated boundary.** It is simultaneously the
   correct count for `0x668BF0–0x668F8D` and the wrong count for the function. Any tool that
   stops at the first `ret` reproduces 28 and silently reports the wrong extent — which is exactly
   the C3/C4 pair of claims.
2. **A second, same-shaped tail exists in F3 (0x674650)**: first `ret 8` at `0x67471B`, tail at
   `0x67471E`, real `ret 8` at `0x674728`. The task statement's instruction to decode from the
   jump target is not a one-off at 0x668BF0; it is the same MSVC `if/else` epilogue-merging shape.
   F3's first-ret extent (`0x67471B`) is likewise wrong.
3. **Decoy "Hard" string.** `0x818124` = "Hard" and `0x81812C` = "Medium" sit immediately before
   `0x818134` = "Easy", so adjacency alone suggests a Hard/Medium/Easy triple. The code does not
   use them: "Hard" has 0 references. The actual triple is Easy / Normal / Difficult.
4. **"Warheads" is not in the pointer table.** It is pushed as a literal `0x83A0D0`. A tool that
   only follows `dword ptr [0x7F0C..]` operands will report 6 inline sections, not 7.
5. **`0x7F0CF4` is not a section pointer.** It holds `0x00889F64`, an address in `.data` BSS with
   no raw backing; F3 reads it as a *key/default-value* argument (`0x67469E`). Counting the table
   as 32 entries gives 31 names; counting only printable names gives 31 either way.
6. **`push 0x889F64` inside F2** (`0x668CF2`, `0x668DA1`, `0x668DF4`, `0x668E46`) is the same BSS
   address used as an empty default string argument, not a section name.
7. **Not verified / out of scope:**
   - The 20 indirect `call dword ptr [edx+0x20]` sites in F1 — targets are vtable-dependent and
     were not resolved; they do not affect C2's *direct*-call claims but mean "F1 calls nothing
     else that loads a section" is not proven for indirect calls.
   - Runtime semantics of `0xA8B238` values (which game mode each integer means). Only the
     byte-level comparisons and the branches they take are reported.
   - Whether `0x674650`'s two call sites are reachable in the same session (they are mutually
     exclusive by the 0xA8B238 test, but that is a static reading of one branch pair).
   - The subroutine at `0x668FB0` (Read_SpecialWeapons) and the fact that F2 calls it at
     `0x668F5E` *after* the loop of seven inline sections: it is a loader call, so it is counted
     in A4, but its own internals were not audited.
   - The exact identity of helper `0x679A10` (called at `0x668EF0`); it is not a `Read_*` entry
     point (prologue `mov eax,[0xA83CA8]`, iterates object arrays calling `[vtbl+0x64]`), and was
     listed but not classified.
