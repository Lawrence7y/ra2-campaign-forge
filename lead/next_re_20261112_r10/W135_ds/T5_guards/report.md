# T5 guards — adversarial verification of the crash-site list

Binary: `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` — **matches** `[已证]`
ImageBase `0x400000`, `.text 0x401000..0x7E038D`, linear sweep = 1,392,527 instructions, 65 skipdata bytes `[已证]`

Reproduce with `python -X utf8 t5_guards.py` (exit 0). Artifacts: `call_sites.tsv`, `diff_vs_claim.txt`, `samples.txt`, `run_log.txt`.

---

## 0. Headline

**The list is wrong in three independent ways, and the single most important claim — that 2 of the 30 sites at `0x724730` are "guarded" — is false.** All 30 sites at `0x724730` are unguarded with respect to `this`. A NULL check applied to only the 28 "unguarded" sites would leave 2 live crash sites.

| routine | claimed unguarded | measured unguarded | delta | verdict |
|---|---:|---:|---:|---|
| `0x00724730` | 28 | **26** | −2 | **REFUTED** |
| `0x00724580` | 18 | 18 | 0 | CONFIRMED |
| `0x007241A0` | 1 | **7** | +6 | **REFUTED** |
| `0x00724520` | 1 | 1 | 0 | CONFIRMED |
| `0x00724530` | 1 | 1 | 0 | CONFIRMED |
| `0x00724540` | 1 | 1 | 0 | CONFIRMED |
| **total** | **50** | **54** | +4 | **REFUTED** |

---

## 1. The classification rule I used (stated, then attacked)

A site is **GUARDED** iff, within 12 instructions before the call, there is a pair `(T, J)` where:

1. `T` is a single-register zero test: `test r,r` | `test r,0` | `cmp r,0` | `cmp 0,r`;
2. `J` is `je` (jz) whose immediate target == `call_addr + call_size` — i.e. it skips *exactly this call* and lands on the next instruction;
3. between `T` and `J` no instruction writes `r`, and only flag-preserving instructions occur (`nop/lea/mov*/push/pop/test/cmp`).

Anything else is **UNGUARDED**, unless a near-miss exists (a skip branch with no valid zero test, or `jne`-into-call), which is reported **AMBIGUOUS** — never silently promoted to guarded. Measured: 0 AMBIGUOUS sites among all 65 sites.

This rule is deliberately *narrower* than "something nullable is checked nearby", which is what the claim evidently used.

### 1.1 Why the claim's "guarded" count is wrong — the actual defect

The 4 sites at `0x724730` that satisfy rule above are `0x6D0619`, `0x6D089D`, `0x6D1541`, `0x6D16C2`. In all four the tested register is **`eax`**, and `eax` is *not* `this`:

```
0x6D060B  85c0            test   eax, eax
0x6D060D  740f            je     0x6d061e
0x6D060F  8b4824          mov    ecx, dword ptr [eax + 0x24]   ; arg from the looked-up object
0x6D0612  51              push   ecx
0x6D0613  8b0d68738800    mov    ecx, dword ptr [0x887368]     ; <-- `this`, loaded UNCONDITIONALLY
0x6D0619  e812410500      call   0x724730
```
`[已证]`

`this` arrives in `ecx` from the global `0x887368`, **outside** the conditional arm. The `je` skips the argument fetch *and* the call together, so it does protect this call — but it protects it against a **failed lookup of the argument object**, not against a NULL `this`. The claim's own supporting note says *"The `this` pointer arrives in a register the caller loads"* — the `test` is not on that register.

Verified mechanically for all four (`site | tested reg | ecx source`):

| site | tested reg | `ecx` (this) loaded from | tested == this? |
|---|---|---|---|
| `0x6D0619` | `eax` | `mov ecx,[0x887368]` @`0x6D0613` | **NO** |
| `0x6D089D` | `eax` | `mov ecx,[0x887368]` @`0x6D0896` | **NO** |
| `0x6D1541` | `eax` | `mov ecx,[0x887368]` @`0x6D153A` | **NO** |
| `0x6D16C2` | `eax` | `mov ecx,[0x887368]` @`0x6D16BB` | **NO** |
`[已证]`

`0x724730` itself never null-tests `ecx`/`ebp` — its first act is the dereference:

```
0x724730  83ec0c          sub    esp, 0xc
0x724733  55              push   ebp
0x724734  8be9            mov    ebp, ecx        ; this
0x724736  56              push   esi
0x724737  8b8550020000    mov    eax, dword ptr [ebp + 0x250]   ; <-- FIRST deref of this
0x72473D  8db54c020000    lea    esi, [ebp + 0x24c]
0x724743  85c0            test   eax, eax
0x724745  0f845e010000    je     0x7248a9
```
`[已证]` — first deref **is** `this+0x250`, so the "first dereference `this + 0x250`" claim for `0x724730` is **CONFIRMED**.

**Correct count for `0x724730`: 30 sites total, 30 effective for NULL-`this` purposes, 0 guarded on `this`.** The claim's "28 unguarded + 2 guarded" split is an artefact of testing the wrong register.

### 1.2 `0x724580` — the "first deref `this+0x250`" claim is FALSE

```
0x724580  53              push   ebx
0x724581  55              push   ebp
0x724582  56              push   esi
0x724583  57              push   edi
0x724584  8b7c2414        mov    edi, dword ptr [esp + 0x14]   ; arg
0x724588  8bd9            mov    ebx, ecx                      ; this
0x72458A  8b07            mov    eax, dword ptr [edi]          ; <-- FIRST deref: the ARGUMENT, not this
0x72458C  8db34c020000    lea    esi, [ebx + 0x24c]            ; <-- this+0x24C, not +0x250
```
`[已证]`

Full-text scan for a `[reg+0x250]` operand finds **48** such instructions; `0x724580` is not among them (`[+0x250] uses: 0`). `0x724580` instead dereferences its **argument pointer** (`[edi]`) before touching `this` — so it can also fault on a NULL *argument*, which a guard on `this` does not cover. The supporting claim "`0x00724730` and `0x00724580` both first dereference `this + 0x250`" is **REFUTED** for `0x724580`.

### 1.3 `0x7241A0` — claim of 1 is off by 6

14 direct call sites, not 2. The list omits 6 unguarded ones:

`0x48CE5D 0x52DB04 0x55D0AB 0x55D173 0x55D202 0x5C4BE3 0x6863AF` — measured **7 unguarded**, claimed 1.

Detail worth flagging: of the 5 sites I sampled, several *look* guarded but test `ecx` against a **different register** (`cmp ecx, ebx` / `cmp ecx, esi` / `cmp [0xa8e9a0],1`), which is an identity/config compare, not a NULL test — e.g. `0x48CE52 cmp ecx,ebx` / `je 0x48CE62` (falls *through* to the call when equal). `0x683F5A test ecx,ecx` / `je 0x683F66` at `0x683F61` **is** a genuine NULL guard on `this`. `[已证]`

---

## 2. Full site inventory (all call forms)

Every `call rel32` site is resolved from the linear sweep and cross-checked (`site + 5 + rel32 == target`). `call reg`, `call [reg+disp]`, and `call [abs]` were enumerated across `.text` (3,797 / 18,903 / 3,833 instructions) and **none** resolve to any of the six routines `[已证]`.

- No `jmp rel32` (tail-jump) targets any of the six.
- **No literal 4-byte pointer** to any of the six exists in the file → no vtable / window-proc / callback registration. These routines are reachable **only** through the direct call sites enumerated here. `[已证]`

Totals: `0x724730`=30, `0x724580`=18, `0x7241A0`=14, `0x724520`=1, `0x724530`=1, `0x724540`=1 → **65**.

### 2.1 Spurious byte hits — a real corruption hazard for a byte-scanning patcher

Of 81,715 raw `E8` bytes in `.text`, **13,462 are not instruction starts `[已证]`**. Notably `0x4011DB` (`site + 5 + rel == 0x405B99`, a plausible-looking `.text` address) sits inside the immediate of `mov eax, 0x51eb851f` at `0x401193` — it is not a call. A guard-patch builder that keys on raw `E8` bytes and resolves targets arithmetically would rewrite 13,462 bytes of live code, including 4 that resolve to real in-text addresses. Full list in `diff_vs_claim.txt`.

### 2.2 Disassembly samples

`samples.txt` holds ≥4 guarded and 6 unguarded sites for each big routine, all dumped **from the authoritative linear sweep** (never by re-decoding from `site−16`). That trap is real: an early version of my own script re-decoded from arbitrary offsets and emitted garbage (`0x6D0887 ff8bcfe8b1f4 dec dword ptr [ebx-0xb4e1731]`, `0x6D0894 248b and al,0x8b`). All reported evidence therefore comes from the sweep.

---

## 3. Fall-through claim: `0x6D1744` → `0x6D1749` — **CONFIRMED** `[已证]`

```
0x6D1728  8b0d68738800    mov    ecx, dword ptr [0x887368]
0x6D172E  50              push   eax
0x6D172F  c644242000      mov    byte ptr [esp + 0x20], 0
0x6D1734  89442408        mov    dword ptr [esp + 8], eax
0x6D1738  c744241c38288400 mov   dword ptr [esp + 0x1c], 0x842838
0x6D1740  89542418        mov    dword ptr [esp + 0x18], edx
0x6D1744  e8e72f0500      call   0x724730          ; size 5, ends 0x6D1749
0x6D1749  8b0d68738800    mov    ecx, dword ptr [0x887368]
0x6D174F  8d442404        lea    eax, [esp + 4]
0x6D1753  50              push   eax
0x6D1754  e8272e0500      call   0x724580
0x6D1759  8b17            mov    edx, dword ptr [edi]
```
`0x6D1744 + 5 == 0x6D1749` exactly; there is no branch between them; the intervening instructions are `mov`/`lea`/`push` only. Control reaches `call 0x724580` unconditionally. **Guarding only `0x724730` does move the crash** here. Same shape repeats at `0x6D059B`→`0x6D05AB`, `0x6D1318`/`0x6D12A3` etc. — the pairs are adjacent throughout the `0x6D0xxx`/`0x6D1xxx` family. `[已证]`

---

## 4. The three `0x6F3F40` sites — **CONFIRMED** `[已证]`

All three are instruction starts in the sweep, and all three **dereference the result of an immediately preceding virtual call** (`call dword ptr [eax+0x3f8]`), then store it in `ecx`/`eax`, then dereference `+0xAC`:

```
0x6F409A  8b08              mov  ecx, dword ptr [eax]        ; result of call [eax+0x3f8]
0x6F409C  8b91ac000000      mov  edx, dword ptr [ecx + 0xac]
0x6F40A2  8a8255010000      mov  al, byte ptr [edx + 0x155]  ; this+0x155
0x6F40A8  84c0              test al, al
```
`0x6F4124  8b91ac000000  mov edx,[ecx+0xac]` → `0x6F412A  8a8259010000 mov al,[edx+0x159]` → `0x6F4130 test al,al`
`0x6F4173  8b88ac000000  mov ecx,[eax+0xac]` → `0x6F4179  8a815a010000 mov al,[ecx+0x15a]` → `0x6F417F test al,al`

- `0x6F409C` is the `mov edx,[ecx+0xac]` form — claim **CONFIRMED**.
- `0x6F4124` is the `mov edx,[ecx+0xac]` form — claim **CONFIRMED**.
- `0x6F4173` is genuinely `8b 88 ac 00 00 00` = `mov ecx,[eax+0xAC]`, the **`ecx`/`eax` form, not `edx`** — claim **CONFIRMED**. (The preceding `mov` at `0x6F4171` is `8b00` = `mov eax,[eax]`, hence the `eax` base.)

Caveat on the "+12 bytes" part of the claim: `test al,al` sits at `+0xC`, `+0xC`, and `+0xC` respectively relative to the site — consistent. But note these faults are on the **result of a virtual call**, so NULL-guarding the site alone is insufficient; the fault surface includes `eax` being a stale/garbage return (see §6).

---

## 5. Missed routines (§6 of the task)

Nothing else in the binary has the "first deref is `this+0x250`" shape — only `0x724730` qualifies `[已证]`. But three **unclaimed, unguarded `[reg+0x250]` dereferences of a global/returned pointer** are worth review, because they are the same *class* of defect (deref of an unchecked pointer) even though they are not `this+0x250`:

| site | instr | situation |
|---|---|---|
| `0x6CD8CD` | `mov ecx,[eax+0x250]` | `eax` = `[0x8871E0]`, loaded at `0x6CD8C2` with **no NULL test** on the path |
| `0x4FD7A0` | `mov eax,[ebx+0x250]` | `ebx` is `this`; reached only after a `jl` from a `cmp` — no `this` NULL test on this arm |
| `0x59A5B0` | `mov eax,[edi+0x250]` | unguarded deref in fn `0x599650` |

Also `0x5B32CA` is `call dword ptr [edx+0x250]` — an **indirect call through an unchecked vtable slot**, which will `E9`/`FF` fault identically. `[已证]`

None of these are in the claim list. I am **not** asserting they are crashes — only that the list's selection criterion ("first deref at `this+0x250`") does not pick them up, so if the criterion is meant to enumerate the defect class, the list is incomplete. Deciding requires the crash dump's faulting address, which I do not have.

---

## 6. Is a caller-side NULL guard even *sufficient*? — **No, on the evidence available.** `[未证]` for the dangling case specifically

Evidence gathered:

1. **`this` is a global, not a parameter.** 26 of the 30 `0x724730` call sites and 4 of 18 `0x724580` sites load `ecx` as `mov ecx, dword ptr [0x887368]` `[已证]`. That global has exactly **3** writers: `0x7777B8` (`mov [0x887368], esi`), `0x7777C3` (`mov [0x887368], ebx` — i.e. **store `ebx`, which is the NULL in this routine**), and `0x777803`.

2. `0x7777F3`–`0x777803` shows the teardown pattern:
```
0x7777F3  8b0d68738800    mov  ecx, dword ptr [0x887368]
0x7777F9  3bcb            cmp  ecx, ebx            ; compare with NULL
0x7777FB  740c            je   0x777809           ; skip if already NULL
0x7777FD  8b01            mov  eax, dword ptr [ecx]
0x7777FF  6a01            push 1
0x777801  ff10            call dword ptr [eax]     ; virtual dtor
0x777803  891d68738800    mov  dword ptr [0x887368], ebx   ; <-- global := NULL after DESTROY
```
`[已证]` — this is a **destroy-then-NULL** sequence, which is the safe ordering. It *reduces* but does not *exclude* a dangling window.

3. **A NULL check cannot detect a non-NULL dangling pointer**, and the game has no refcounting visible at the stores. If any path writes `[0x887368]` with a freed object, or a caller caches `ecx` from `[0x887368]` and the object is destroyed on another path before the call, the guard passes and the `[ebp+0x250]` at `0x724737` still faults.

**What would distinguish the two cases:**
- The exception record from the crash: `ExceptionAddress` + `Access violation reading address 0x00000250` (offset `0x250` of a NULL `this`) ⇒ genuine NULL-`this`, guard is sufficient. `Access violation reading address 0x????????` where the address is *not* ≈`0x250` or `0x24C` ⇒ dangling/stale, guard insufficient. I have no crash dump here, so this is `[未证]`.
- A watchpoint on `0x887368` in a running process confirming the value is NULL (not garbage) at fault time. Not run — I am prohibited from launching the game.
- Presence of a *free* path that sets `[0x887368]` without the `cmp ecx,ebx` precheck. Only 3 writers exist and the one I examined does precheck, which is mild evidence *for* the NULL hypothesis.

**Recommendation:** the guard is worth adding, but it should be coupled with a sentinel/validity check rather than a bare `test ecx,ecx`, and the `0x724580` argument dereference (`[edi]` at `0x72458A`) needs its own guard, since a guard on `this` cannot cover it.

---

## 7. Honest limits

- **Static analysis only.** No dynamic confirmation; no crash dump supplied. Every "this faults" inference is from code shape, not from a reproduced fault. `[未证]`
- **`containing_fn` is an approximation.** It is the nearest preceding address that is a call target, a `push ebp/mov ebp,esp` prologue, or one of the six. Functions with no prologue and no callers in-text will be attributed to their predecessor. This affects only the `containing_fn` column, not site counts or classification. For the six routines I used the *declared entry address* directly, so their counts are unaffected. `[已证]`
- **`classify()` searches ≤12 instructions and stops at `ret`/`jmp`/`call`.** A guard placed further away, or across a branch, would be misreported as unguarded. I chose this bias deliberately (a false "unguarded" costs a redundant guard; a false "guarded" leaves a crash). It found 0 AMBIGUOUS sites, which suggests no near-misses were truncated.
- **Handling of `jne`-into-call:** flagged AMBIGUOUS, never guarded. None found.
- **`0x7241A0`'s 14 vs 2:** I could not construct any reading of the claim that yields 1 unguarded. Even if every `cmp reg,reg` were counted as a guard (which would be wrong), the count would not be 1. **REFUTED** regardless of interpretation.
- I did **not** verify that a guard patch preserves stack balance, instruction-length budget for inline hooks, or that the patched bytes fit a 5-byte `E8`. That is a separate concern for the patcher and is not addressed here.
- I did not read or modify the ledger; I only read the GLM partial `recon.py` / `recon_out.txt`.

---

## 8. Verdict summary

| claim | verdict |
|---|---|
| `0x724730` has 28 unguarded | **REFUTED** — 26 by the stated rule, but **30** are unguarded w.r.t. `this`; the 4 rule-matching sites test the *argument* (`eax`), not `this` |
| `0x724580` has 18 unguarded | CONFIRMED |
| `0x7241A0` has 1 unguarded | **REFUTED** — 14 sites, 7 unguarded |
| `0x724520` / `0x724530` / `0x724540` have 1 each | CONFIRMED each |
| **total 50** | **REFUTED** — 54 |
| `0x724730` has 30 direct call sites | CONFIRMED |
| `0x724730` and `0x724580` both first-deref `this+0x250` | **REFUTED** — true only for `0x724730`; `0x724580` first derefs its *argument* `[edi]` and uses `this+0x24C` |
| "guarded" = `test`/`cmp` + cond-jump skipping the call | **REFUTED as stated** — the rule as written does not require the tested register be the `this` register, which is precisely how 2 sites were misclassified |
| `0x6D1744` falls through unconditionally into `0x6D1749` | **CONFIRMED** |
| Three `0x6F3F40` sites, `0x6F4173` is `mov ecx,[eax+0xAC]` | **CONFIRMED** |
| No other routine first-derefs `this+0x250` | CONFIRMED — but 4 same-class unguarded `[reg+0x250]` sites omitted (§5) |
| NULL guard is sufficient | **INCONCLUSIVE** — cannot exclude a dangling pointer statically |
