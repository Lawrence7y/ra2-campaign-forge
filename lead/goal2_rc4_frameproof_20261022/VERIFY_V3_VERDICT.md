# VERIFY_V3 — independent re-verification verdict

Date: 2026-10-22
Binary: `ra2youli/gamemd.exe`
sha256: `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` (prefix `73201cc0` OK)
ImageBase `0x400000`, SizeOfImage `0x796000`, 5 sections, `.text` VA `0x401000`..`0x7E038D`

Script: `lead/goal2_rc4_frameproof_20261022/VERIFY_V3.py`
Output: `lead/goal2_rc4_frameproof_20261022/VERIFY_V3.txt`
Result: **checks passed: 51/51 — RESULT: ALL PASS (EXIT=0)**

---

## Verdicts

| # | Claim | Verdict |
|---|-------|---------|
| 1 | Direct `[0x887368]`-as-this calls hit exactly 4 targets, 1/4/1/1 = 7 sites | **CONFIRMED** (numbers) / **criterion wording REFUTED** |
| 2 | First this-relative offsets 0x250 / 0x24C / 0x228 / 0x22C | **CONFIRMED** (with one definitional caveat on 0x724580) |
| 3 | None of the four functions' return values is read | **CONFIRMED** |
| 4 | Prologue bytes and first-`ret` operands | **CONFIRMED** |

---

## 1. Site census — CONFIRMED numerically, but the stated criterion does not produce it

Measured, byte-level `8b 0d 68 73 88 00` scan over `.text`:

- 69 raw occurrences, all of them at instruction boundaries (0 desync).
- 50 of them reach a `call` with no intervening `mov ecx,...` and no control-flow break.
- Of those 50, **7 have the `call` as the literally next instruction** (gap = 0 insns).

Under **strict adjacency** (gap = 0):

| target | sites | site addresses |
|---|---|---|
| 0x724730 | 1 | 0x6D0613 |
| 0x724580 | 4 | 0x640431, 0x654473, 0x6AC015, 0x6AC14A |
| 0x724530 | 1 | 0x6AB994 |
| 0x724540 | 1 | 0x6AB9E3 |

Total 7 sites, target set exactly `{0x724730, 0x724580, 0x724530, 0x724540}`, counts 1/4/1/1 in the stated order. **Matches exactly.**

Guards: all 7 have an **empty** gap, so the question "is there a test/cmp guard between the mov and the call" is vacuously "no". Flag semantics were checked anyway (`mov`/`lea`/`push`/`pop` do not touch EFLAGS; nothing else is present). Zero sites are guarded locally.

### Discrepancy A (wording, material) — the stated definition of 「紧接」 yields 50 sites / 6 targets, not 7 / 4

The prompt defines 紧接 as *"mov 之后、call 之前的指令里没有其他 `mov ecx,...`"*. That criterion is much weaker than "call is the next instruction". Applying it literally:

- **50 sites**, not 7.
- **6 distinct targets**, not 4 — it additionally reaches `0x7241A0` (from 0x5C4BB8) and `0x724520` (from 0x6AB99F).
- Per-target counts become 0x724730:28, 0x724580:18, 0x724530:1, 0x724540:1, 0x7241A0:1, 0x724520:1.

So the expected numbers (7 / 4 targets / 1-4-1-1) are only reproducible with **strict zero-gap adjacency**. The parenthetical definition should read "call 紧接在 mov 之后（中间无任何指令）", not "无其他 mov ecx".

### Discrepancy B (material, safety-relevant) — the actual crash did NOT come from one of the 7 sites

`except.txt` stack dump has `00F9A358: 00654418` immediately following `00F9A354: 006543B1`, i.e. `0x654418` is the return address of the frame that crashed. `0x654418 - 5 = 0x654413`, which is a `call 0x724730` — verified. But its load is at `0x654405`, with **two register spills in between**:

```
0x654405  mov ecx, dword ptr [0x887368]
0x65440b  mov dword ptr [esp + 0x18], edx
0x65440f  mov dword ptr [esp + 0x1c], eax
0x654413  call 0x724730
0x654418  <- return address on the crashing stack
```

So the crashing call site is one of the **43 non-adjacent** sites, not one of the 7. If the 7-site list is being used as the crash-risk census (or as the patch-target list), it **misses the site that actually crashed**. This is the single most important finding here.

### Non-discrepancy notes

- No indirect `call [mem]` directly follows the load (0 occurrences), so the E8-only scan does not miss a call-form.
- `.detour` (appended section) contains 0 copies of the pattern and 0 calls to the 4 targets.
- The 4 targets have **no absolute dword reference anywhere in the file** (0 occurrences each), no export table (`DataDirectory[0] = 0`), and no tail `jmp` to them — so the E8 caller enumeration is complete; there is no vtable/function-pointer path.
- 19 loads never reach a call; all are followed by `test ecx,ecx` / `cmp ecx,ebx` + `je` and bail out. Correctly excluded.
- Global is written at `0x7777B8` (`= esi`), `0x7777C3` (`= ebx`), `0x777803` (`= ebx`); `0x7777F3`-`0x777803` is the teardown path (`test ecx,ecx; je; mov eax,[ecx]; push 1; call [eax]` then store 0). The "cleared on window close" premise is structurally supported. 74 references to the global total (71 `mov` reads, 3 writes).
- Two loads use a non-`ecx` destination and then pass it as this via an alias: `0x4E1F88 mov esi,[0x887368]` → `mov ecx,esi` → `call 0x7241A0`; and `0x6ABFC4 mov eax,[0x887368]` (guarded `cmp eax,ebx; je`) → later `mov ecx,[0x887368]` → `call 0x724730`. Not part of the strict-adjacency set, listed for completeness.

---

## 2. First this-relative offset — CONFIRMED, one definitional caveat

Alias tracking: `ecx` = this; propagates through `mov reg,ecx` and `lea reg,[this+x]`; `ebp` is **not** treated as a frame pointer (the known trap), which is what makes 0x724730 resolve.

| function | first this-relative address | insn | expected | |
|---|---|---|---|---|
| 0x724730 | **+0x250** | `0x724737 mov eax,[ebp+0x250]` (after `mov ebp,ecx`) | 0x250 | CONFIRMED |
| 0x724580 | **+0x24C** | `0x72458C lea esi,[ebx+0x24C]` | 0x24C | CONFIRMED (see caveat) |
| 0x724530 | **+0x228** | `0x724530 mov eax,[ecx+0x228]` | 0x228 | CONFIRMED |
| 0x724540 | **+0x22C** | `0x724540 mov eax,[ecx+0x22C]` | 0x22C | CONFIRMED |

No `test`/`cmp` on the this-pointer occurs before the first touch in any of the four.

### Discrepancy C (wording, minor but real) — 0x724580's 0x24C is not a dereference

For 0x724580, `0x24C` is produced by `lea esi,[ebx+0x24C]` at `0x72458C` — pure address arithmetic, **no memory is accessed**. The first actual dereference of this is `0x724596 mov eax,[esi+4]` = **+0x250**. So:

- if 「解引用」 means "memory access", 0x724580's answer is **0x250**, not 0x24C (and 0x724730/0x724580 then share the same first-deref offset);
- if it means "first instruction whose address depends on ecx" (address formation), 0x24C is right.

The table is consistent only under the second reading. For 0x724730/0x724530/0x724540 the two readings coincide, so this affects only 0x724580.

---

## 3. Return value unused — CONFIRMED

Caller counts (verified two independent ways: capstone `call` imm operands, and a raw `E8 rel32` scan — both agree exactly):

| function | callers |
|---|---|
| 0x724730 | 30 |
| 0x724580 | 18 |
| 0x724530 | 1 (0x6AB99A) |
| 0x724540 | 1 (0x6AB9E9) |

For each of the 50 call sites, `eax` is classified with capstone `regs_access()` on the next instruction (immediate-next criterion) and again over a forward window that stops at the first write to `eax`, the first branch, `call`, or `ret`:

- **immediate-next true reads of eax: 0 for all four functions.**
- **forward-window true reads of eax: 0 for all four functions.**

Every eax mention is a destination (`mov eax, [mem]` — overwrite) or absent. `xor al,al` / `mov al,1` style writes inside 0x724580 are also writes, not reads.

### Discrepancy D (nuance) — the functions *do* return values; callers just ignore them

`0x724530` / `0x724540` are `mov eax,[ecx+X]; mov [ecx+Y],eax; ret` — they leave the copied value in `eax` (arguably a real return value). `0x724580` returns a bool in `AL` (`0x724716 mov al,1` / `0x724728 xor al,al` before its `ret 4`s). So the accurate statement is "**no caller reads** the return value", not "the functions have no return value". The claim as written ("都不读返回值") is about callers and is CONFIRMED.

---

## 4. Prologue bytes and first `ret` — CONFIRMED

| function | measured first 8 bytes | disassembly | first `ret` | expected | |
|---|---|---|---|---|---|
| 0x724730 | `83 EC 0C 55 8B E9 56 8B` | `sub esp,0xc; push ebp; mov ebp,ecx; push esi` | `0x7248AE ret 4` | `83ec0c558be9`, ret 4 | CONFIRMED |
| 0x724580 | `53 55 56 57 8B 7C 24 14` | `push ebx; push ebp; push esi; push edi; mov edi,[esp+0x14]` | `0x7245CA ret 4` | `535556578b7c2414`, ret 4 | CONFIRMED |
| 0x724530 | `8B 81 28 02 00 00 89 81` | `mov eax,[ecx+0x228]; mov [ecx+0x22c],eax; ret` | `0x72453C ret` | `8b8128020000`, ret | CONFIRMED |
| 0x724540 | `8B 81 2C 02 00 00 89 81` | `mov eax,[ecx+0x22c]; mov [ecx+0x228],eax; ret` | `0x72454C ret` | `8b812c020000`, ret | CONFIRMED |

All four stated byte strings are exact prefixes (6/8/6/6 bytes).

### Discrepancy E (nuance) — 0x724580 has three `ret 4` exits, not one

`0x7245CA`, `0x724719`, `0x72472B` — all `ret 4` (`C2 04 00`). The stated "第一个 ret" is correct, but any patch that only rewrites the first `ret` / only instruments one exit would leave two exits untouched. 0x724730 has exactly one exit (`0x7248AE ret 4`); 0x724530 and 0x724540 have exactly one each.

---

## 5. Crash-site corroboration (bonus, all PASS)

- `0x724737` bytes = `8B 85 50 02 00 00` = `mov eax,[ebp+0x250]` — matches `except.txt`.
- That instruction **is** the first this-dereference of 0x724730 (+0x250), reached after `0x724734 mov ebp,ecx`; `Ecx=0` and `Ebp=0` in `except.txt` are consistent.
- `Access address: 00000250` = `0 + 0x250` — consistent.
- Return address `0x654418` maps to `call 0x724730` at `0x654413` (see Discrepancy B: that site is **not** in the 7-site list).

---

## Methodological finding worth propagating

**Plain capstone linear disassembly of this `.text` stops at `0x46F59D` after only 155,215 instructions** (it desyncs on embedded data). Every one of the 69 `mov ecx,[0x887368]` hits lies **above** `0x46F59D`, so a naive `md.disasm()` sweep finds **zero** sites and silently reports an empty census. `skipdata=True` is mandatory: it yields 1,392,592 instructions covering the full 4,060,045 bytes, and all 69 raw hits land on instruction boundaries. Any earlier census script in this repo that did not set `skipdata` should be re-checked.

## Not verified here

- Runtime behaviour (that the pointer is actually 0 at the moment of these calls) — this is static evidence only. `except.txt` is the runtime evidence and it is consistent.
- Whether `0x7241A0` / `0x724520` (reachable only under the loose reading) are crash-relevant: `0x7241A0` first touches +0xC (a byte compare), `0x724520` writes +0x228. `0x724520` is called at `0x6AB99F` immediately after `0x724530` at `0x6AB99A`, with no guard on either — that pair is an unguarded consecutive double-deref worth noting.
