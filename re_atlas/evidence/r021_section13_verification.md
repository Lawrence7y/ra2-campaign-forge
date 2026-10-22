# R-021 verification — §13 RulesClass sections: 3 falsifications, 1 inherited error

**Date**: 2026-10-22
**Binary**: `gamemd.exe` SHA-256 `73201cc0…f67476` — GATE PASS
**Gate**: `tools/verify_r021_claims.py` — **30/30 PASS, EXIT=0**
**Method**: pointer table read as raw dwords with per-section file backing;
function extents from a head decode to the terminating `ret`, cross-checked
against every jump that leaves the extent; loader order from decoded `E8`
targets, not from the evidence text file.

## 1. Confirmed (the bulk of §13 holds)

| §13 claim | Result | Byte evidence |
|:--|:--|:--|
| `0x7F0C78` table, 4-byte stride, 31 non-empty of 32 | **CONFIRMED** | 31 strings resolved, slot 32 empty |
| Key slots `Colors`/`ColorAdd`/`General` | **CONFIRMED** | `0x7F0C94`/`98`/`9C` |
| `Read_File` head `0x668BF0`, `ret 4` | **CONFIRMED** | head bytes, `c2 04 00` at `0x668FA2` |
| `Init` head `0x6686C0`, ends `0x668BE5` `ret 4` | **CONFIRMED** | decoded extent + terminating ret |
| `Init` calls no per-section loader directly | **CONFIRMED** | intersection of Init's CALL targets with 37 loader addresses = ∅ |
| `Init` calls `Read_File` exactly 3 times | **CONFIRMED** | `0x668A27` / `0x668B05` / `0x668BAA` |
| 28 loader calls in `Read_File`, in the documented order | **CONFIRMED for the truncated window; 29 over the true extent** | 28 `E8` targets within `0x668BF0–0x668F8D`; 29 within `0x668BF0–0x668FA3` |
| Positional order of the 28 (positions 1–28) | **CONFIRMED** | sequence matches; the 29th is the cold-block AdvancedCommandBar |
| `Read_General` before all three `Read_Difficulty` | **CONFIRMED** | index 16 vs 17/18/19 |
| `Read_File` inline sections `ColorAdd`/`Countries`/`OverlayTypes`/`SuperWeaponTypes`/`SmudgeTypes`/`TerrainTypes` | **CONFIRMED** | all six referenced inline |
| `Warheads` as direct push `0x83A0D0` | **CONFIRMED** | `push 0x83a0d0` present |
| 36 of 38 readers mapped, 2 structural gaps | **CONFIRMED** | `Read_Difficulty` (section in `edx`), `Read_Difficulties` (forwards only) |
| `Read_File`'s first action is `call Read_Colors` | **CONFIRMED** | `0x668BFE call 0x66D3A0` before any `GetSection` |

## 2. ★ FALSIFICATION 1 — `Read_File` has a cold tail block; its extent is not its first `ret`

§13.5 states `Read_File` spans `0x668BF0–0x668F8D`. **Two jumps inside the main
body leave that range:**

```text
0x00668F71  je 0x668F90
0x00668F76  je 0x668F90
```

The block at `0x668F90` decodes as a second return path ending in
`0x00668FA2 c2 04 00` (`ret 4`). `Read_SpecialWeapons` starts at `0x668FB0`,
so the cold block occupies exactly the gap.

⇒ **True extent: `0x668BF0–0x668FA3`**, not `0x668BF0–0x668F8D`.
An extent derived as "first `ret`" silently drops the tail — the same class of
error as the capstone truncation trap, one address scale down.

**Why the gate initially missed it:** decoding the tail starting at `0x668F8D`
re-decodes `c2 04 00` as *a* `ret` and reports the old, wrong boundary. The
tail must be decoded from the jump **target** (`0x668F90`), not from just past
the first `ret`. Recorded as a method note in §13.7.

## 3. ★ FALSIFICATION 2 — the MP command bar section IS read

§13.3 states: `MultiplayerAdvancedCommandBar` (`0x7F0CEC`) "没有被任何 `Read_*`
当作首个节名" and concludes it is unused.

**Byte fact:** `0x7F0CEC` has exactly one reference in the whole image:

```text
0x0067465E  mov edi, dword ptr [0x7f0cec]   ; MultiplayerAdvancedCommandBar
0x00674664  jne 0x67466c
0x00674666  mov edi, dword ptr [0x7f0ce8]   ; AdvancedCommandBar
```

`Read_AdvancedCommandBar` (`0x674650`) picks its section with a **boolean
parameter**, not a fixed slot:

| arg | section used | call site |
|--:|:--|:--|
| `1` | `MultiplayerAdvancedCommandBar` | `0x00668F81` |
| `0` | `AdvancedCommandBar` | `0x00668F96` |

and `Read_File` calls it **twice**, once per branch — §13.5 lists only the
`0x668F81` call. Over the true extent the loader census is
**29 calls / 26 distinct loaders**: `Read_Difficulty` ×3 (positions 18–20) and
`Read_AdvancedCommandBar` ×2 (positions 28–29). The published "28" is exactly
the truncated-window figure — right for the window, wrong for the function.

⇒ The surviving true part of §13.3 is narrower: the MP slot is never a loader's
*primary* (first) section. "Never used" is **refuted**.

## 4. ★ FALSIFICATION 3 — the MP branch is gated on GameMode, and the mapping is the opposite of the intuition

The branch condition is not incidental. It is:

```text
0x00668F6A  mov eax, dword ptr [0xa8b238]   ; GameMode
0x00668F6F  test eax, eax
0x00668F71  je 0x668f90                     ; GameMode == 0 -> xor eax,eax path (arg 0)
0x00668F73  cmp eax, 5
0x00668F76  je 0x668f90                     ; GameMode == 5 -> same path (arg 0)
0x00668F78  mov eax, 1                      ; fallthrough: arg = 1
0x00668F81  call 0x674650                   ; F3(arg=1)
0x00668F90  xor eax, eax                    ; arg = 0
0x00668F96  call 0x674650                   ; F3(arg=0)
```

and `Read_AdvancedCommandBar` (F3) selects the section by that flag:

```text
0x00674650  mov al, byte ptr [esp + 8]      ; arg
0x0067465A  test al, al
0x0067465E  mov edi, dword ptr [0x7f0cec]   ; MultiplayerAdvancedCommandBar
0x00674664  jne 0x67466c                    ; arg != 0 -> keep the MP slot
0x00674666  mov edi, dword ptr [0x7f0ce8]   ; arg == 0 -> AdvancedCommandBar
```

Composing the two blocks:

| GameMode | meaning | arg | section read |
|--:|:--|--:|:--|
| 0 | Campaign | 0 | **`AdvancedCommandBar`** |
| 3 | LAN | 1 | `MultiplayerAdvancedCommandBar` |
| 4 | Internet | 1 | `MultiplayerAdvancedCommandBar` |
| 5 | Skirmish | 0 | **`AdvancedCommandBar`** |

`0xA8B238` is `SessionClass::Instance.GameMode` (cross-confirmed:
`docs/re/anchor_claims.txt:126`; `ARCHITECTURE_ATLAS.md:1908`
`{0=Campaign, 3=LAN, 4=Internet, 5=Skirmish}`).

⇒ **Single-player (campaign and skirmish) reads `AdvancedCommandBar`;
multiplayer (LAN/Internet) reads `MultiplayerAdvancedCommandBar`.**

**This is the direction the first draft of this very section had backwards.**
An earlier revision of this file asserted "campaign/skirmish read the MP
section". That was wrong: the two `je`s land on the `arg=0` path, and `arg=0`
resolves to `AdvancedCommandBar`. `verify_r021_claims.py` now asserts the
mapping per GameMode so the error cannot silently return. Caught by the
independent cross-check, not by the local gate — the local gate had asserted
only "a gate exists", which was too weak.

**Honest limit:** whether `GameMode==0` and `==5` also means the section's
*contents* are applied at runtime (vs parsed and discarded) is not traced here.
The read happens; the effect is a separate question.

## 5. Inherited error found in H-014 (not in the KB)

H-014 line says `Read_Difficulties` calls `Read_Difficulty` with
`Easy` / `Normal` / **`Hard`**.
**Byte fact:** `0x83A0C4` = **`Difficult`**, not `Hard`:

```text
0x818134  'Easy'
0x81BB60  'Normal'
0x83A0C4  'Difficult'
```

§13.4 was correct; **H-014 carried the wrong third name.** A compiler writing
`Hard=` would read nothing. Recorded so the handoff is not used as-is.

H-014 also still says "载入顺序取自 `RulesClass::Init`（`0x6686C0`）的 32 个内部调用",
which is the **withdrawn** version (R-021's first attempt leaked into `Read_File`
via a 0x1600 window). The KB retracted it; the handoff did not.

## 6. Negative controls

| Control | Purpose | Result |
|:--|:--|:--|
| head of a *different* function vs Init's end | extent rule is not vacuous | `Read_File` head gives `0x668F8D`, **not** `0x668BE5` |
| mid-Init head `0x6686C5` | shows why in-function starts are useless as controls | shares Init's `ret` — recorded, not used as a control |
| "Init has 32 direct Read_* calls" | withdrawn claim must fail | 0 per-section loaders ⇒ claim false |
| sha256 vs pristine copy | gate liveness | differs (`db264…`) |

## 7. What this changes for goal ③

1. **`[MultiplayerAdvancedCommandBar]` is read in campaign/skirmish**
   (`GameMode ∈ {0,5}`), not only in multiplayer. Any patch that edits it
   for single-player **does** take effect on the parse path.
2. **`Read_AdvancedCommandBar` is called twice per `Read_File` pass**, so its
   section is resolved twice per pass; and `Read_File` runs three times ⇒ six
   resolutions per load. A patch assuming one resolution is wrong.
3. **The third difficulty key is `Difficult`, not `Hard`.** Writing `Hard=`
   writes a key nothing reads.
4. The 3-pass overwrite rule (later INI wins) is unaffected and stands.

## 8. Reproduce

```bash
python re_atlas/tools/verify_r021_claims.py     # 30/30 PASS, EXIT=0
```

Prints the pointer table, both function extents (including the cold tail),
the 28-call sequence, the two AdvancedCommandBar call sites with their flags,
and the GameMode gate.
