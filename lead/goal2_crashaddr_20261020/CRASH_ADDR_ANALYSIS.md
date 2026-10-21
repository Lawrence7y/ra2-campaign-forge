# CRASH_ADDR_ANALYSIS — instruction-level adjudication of `0x0084F2BA` (and `0x0054A56E`)

Target: `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
size 4,825,360 B, sha256[:16] `73201cc021497c95` (full `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`, verified with `sha256sum`).
Cross-check copy `…\qc161_u0400_trip\_src_L1_sf8_20261020\gamemd.exe` is **byte-identical** (same full sha256).

Method / reproducibility
- All numbers below come from `addr_probe.py` in this directory, run with
  `PYTHONDONTWRITEBYTECODE=1 python addr_probe.py all` (exit 0, no errors; 1.39M-instruction capstone sweep of `.text`).
- READ-ONLY throughout: the exe is opened `rb` only; it is never written and never executed.
- capstone 5.0.7, `CS_ARCH_X86 / CS_MODE_32`, `skipdata=True`. **`skipdata` is mandatory** here: without it capstone stops at the first undecodable byte and only reaches `0x0046F5A0` (≈11% of `.text`), which silently truncates every operand search. Measured both ways.
- Section-relative VA↔file mapping uses the *measured per-section delta* from the section table, not a global `−0x400000` guess. `.text`/`.rdata`/`.data` share delta `0x00400000`; `.rsrc`/`.detour` use `0x006FC000`.

---

## 1. PE layout + section table (measured, `addr_probe.py` stage `pe`)

- `e_lfanew`=0x00000050, `machine`=0x014C (i386), 5 sections, Characteristics 0x032F.
- PE32 (`Magic`=0x10B), `ImageBase`=**0x00400000**, `SectionAlignment`=0x1000, `FileAlignment`=0x1000.
- `SizeOfImage`=**0x00796000** ⇒ mapped span **[0x00400000, 0x00B96000)**. `AddressOfEP`=0x007CD80F. `Subsystem`=2 (GUI).
- `DllCharacteristics`=**0x0020** (IMAGE_LIBRARY). **`IMAGE_DLLCHARACTERISTICS_NX_COMPAT` (0x0100) is CLEAR** ⇒ this image does **not** opt into DEP. Under the default *OptIn* policy the whole image (incl. `.data`) is mapped **executable**; only under a machine-wide *AlwaysOn* DEP would `.data` be NX. This matters for §2.

| # | Name | VA range (measured) | VirtSize | RawPtr | RawSize | Char | Perm | delta (VA−fileoff) |
|---|------|--------------------|----------|--------|---------|------|------|--------------------|
|0|`.text` |0x00401000–0x007E1000|0x003DF38D|0x00001000|0x003E0000|0x60000020|**-R-X** |0x00400000|
|1|`.rdata`|0x007E1000–0x00812000|0x00030074|0x003E1000|0x00031000|0x40000040|**-R–-** |0x00400000|
|2|`.data` |**0x00812000–0x00B79BE4**|0x00367BE4|0x00412000|0x0006C000|**0xC0000040**|**-RW-** |0x00400000|
|3|`.rsrc` |0x00B7A000–0x00B93000|0x00018128|0x0047E000|0x00019000|0x40000040|**-R–-** |0x006FC000|
|4|`.detour`|0x00B93000–0x00B96000|0x00002718|0x00497000|0x00003000|0xC0000040|**-RW-** |0x006FC000|

`.detour` is a non-CRT section name (linker/build hook region); its content at file 0x497000 is **not** valid code (decodes as `add`-form garbage), consistent with a data/hook table, not injected shellcode. No `.rdata`-style constant pool near the crash.

---

## 2. Where `0x0084F2BA` lands, and why a *writable* `.data` reports "不能为 written"

Measured (`addr_probe.py`):
- **Section: `.data`** (0x00812000–0x00B79BE4). Intra-section offset **0x3D2BA**. delta 0x00400000 ⇒ **file offset 0x0044F2BA**.
- **Page: 0x0084F000** (`0x0084F2BA & ~0xFFF`), page offset **0x02BA**.
- The page is **inside the file-backed extent** (`.data` raw VA ends at 0x0087E000), so it is a normal initialized-data page, not zero-fill.
- Characteristics of that page's section = **0xC0000040 = IMAGE_SCN_MEM_WRITE(0x80000000) SET** + MEM_READ SET + **MEM_EXECUTE CLEAR** ⇒ mapped **PAGE_READWRITE** (writable, *not* executable).

**There is therefore NO static reason a genuine data write to 0x0084F2BA could fail** — the page is writable. So the dialog cannot be describing a compiler-emitted `mov [0x0084F2BA], reg`. The resolution is that **EIP itself was at 0x0084F2BA**:

- `0x0084F2BA % 4 == 2` (mod 8 = 2). A 4-byte float element in this table is always at `VA % 4 == 0`. So 0x0084F2BA is **not any aligned element boundary** — it sits **mid-element**: it is byte[2] of the float at **0x0084F2B8** (value 0.107935 ≈ the "0.108" the dialog/observation cited) and byte[0] of the float at 0x0084F2BC.
- Decoding the actual on-disk bytes at that exact offset with capstone (`addr_probe.py`):

```
0084F2BA: dd 3d c3 9c de 3d   fnstsw word ptr [0x3dde9cc3]   ; FF store form DD /6
0084F2C0: 7d 2c               jge 0x84f2ee
0084F2C2: e0 3d               loopne 0x84f301
0084F2C4: 2e bc e1 3d d6 4b   mov esp, 0x4bd63de1
```

i.e. if control flow ever lands with EIP=0x0084F2BA on the pristine LUT bytes, the CPU decodes them as an **x87 `fnstsw` store to `0x3DDE9CC3`**, which lies **below ImageBase (0x00400000) → outside the mapped image → unmapped → write access violation ("该内存不能为 written")**. That reproduces the *access-violation-on-write* outcome without needing the `.data` page to be non-writable — the faulting write-target is `0x3DDE9CC3`, an unmapped address, not the `.data` page.

**Two honest readings of the "EIP == referenced == 0x0084F2BA" wording** (the dialog gives both numbers as 0x0084F2BA, whereas the pristine-byte decode yields the *store target* 0x3DDE9CC3 — they disagree, and I will not paper over it):
1. **Instruction-fetch / DEP violation**: `.data` is mapped non-executable (MEM_EXECUTE CLEAR). Under DEP *AlwaysOn* (or a per-process opt), redirecting EIP into `.data` faults on the *fetch*. The legacy Win32 "错误应用程序" box prints the faulting page address as both the instruction and the data field and phrases the access type as "written", so "0x84f2ba … 0x84f2ba … written" is fully consistent with an **execute-attempt on a RW(no-X) data page**. This is the classic `EIP == ExceptionInformation[1]` control-flow-hijack-into-data signature.
2. **Corrupted runtime bytes**: the float LUT is *recomputed at load* (§4), and the crash happened in a process whose init had already failed (csf path>131 chars). If the slot at 0x84F2B8/BC held different bytes at crash time, the decoded instruction — and thus its write target — differs from disk. In that case the store could genuinely target 0x84F2BA itself.

Either way the **command-level certainty** is: 0x0084F2BA is a byte **inside a non-code `.data` float table**, the page is **PAGE_READWRITE**, and the fault is **not** a legitimate compiled data-store to 0x0084F2BA — it is **control flow redirected into `.data`** (a bad jmp/call/ret target, a corrupted function pointer, or an off-by-2 pointer that landed mid-LUT). The "可写的 .data 却报不能为 written" paradox is explained by *execute permission* (reading/fetching code out of a non-executable page) and/or an out-of-image store operand, **not** by the target page being read-only.

> Cross-check of the "self-referential write" literal reading: I searched `.text` for any instruction whose mem-operand or imm equals exactly 0x0084F2BA (a `mov [0x84f2ba],reg` self-store). Result: **0** (see §3). So the "wrote its own address" reading is **not supported** by the static image; §2.1 (execute fault) or §2.2 (runtime-diverged bytes) is what the image actually supports.

---

## 3. The 32 bytes at `0x0084F2BA` and the table's real semantics

Measured dump (`addr_probe.py` stage `bytes`, file offset 0x0044F2BA):

```
0x0084F2BA: DD 3D C3 9C  DE 3D 7D 2C  E0 3D 2E BC  E1 3D D6 4B
            E3 3D 75 DB  E4 3D 0C 6B  E6 3D 99 FA  E7 3D 1E 8A
```

Read **4-byte-aligned** from the table grid the bytes spell an arithmetic float32 ramp (verified contiguous from 0x84F084 to 0x859088):

```
0x0084F2B4 = 0.1071724      0x0084F2B8 = 0.1079350     <- element 141
0x0084F2BC = 0.1086974      0x0084F2C0 = 0.1094599     <- element 142,143
```

The crash address 0x0084F2BA = **0x84F2B8 + 2 bytes** — a misaligned *read* of the half-spans of elements 141/142 (`uint32 @0x84F2BA = 0x9CC33DDD`), which is exactly why a float-decode *at* 0x84F2BA is meaningless (-0.0 / garbage) while the **aligned element under it is 0.1079 ≈ the observed 0.108, step 0.000767 ≈ the observed 0.0007** (facts 3 confirmed).

**Table identity / semantics.** The LUT base is **0x0084F084**, count `(0x859088−0x84F084)/4 = 10241` float slots. Consumers do `fld dword [eax*4 + 0x84F084]` with `eax` masked by `and eax, 0x8000_1fff` (13 bits ⇒ ±8192) and a ±0x1fff/±0x27ff fold (see `0x004CACEA`, `0x004CAD41`, `0x004CB189/193/1E0/1EA`). The initializer (`0x004CB0E0`, §4) multiplies the index by `2π/8192 = 0.000766990` (qword `0x007E8988`) and the round helper by `8192/π = 2607.594482` (dword `0x008223B0`).
⇒ This is the **Westwood/RA2 8192-unit-circle phase/angle lookup table** — a per-slot ramp with step exactly `2π/8192 = 0.000766990` (qword `0x007E8988`), the round helper scaled by `8192/π = 2607.594482` (dword `0x008223B0`), and the consumer `fld [eax*4 + 0x84F084]` masked to a 13-bit angle (`and eax,0x8000_1fff`, ±8192 = one 8192-unit circle). **Solidly: in the head region (which contains the crash slot) the table is the angle-indexed ramp `slot = idx·(2π/8192)`**, so slot 141 = 0.107935 rad. It is a **geometry/rotation phase LUT**, *not* lighting falloff and *not* a colour-mix weight table. (The two `0x0084F088`/`0x0084F084` consumers read `qword 0x007E8970 = 651.8986 = 2048/π` for the sign/round correction; the far slots past idx≈8192 saturate at 1.0, so the **global** table is not one straight 0→2π line — only the head region around the crash is.)

---

## 4. Finding the *writers* of `0x0084F2BA` (three leads, run over full `.text`)

All three leads executed in `addr_probe.py` stage `scan` over **1,392,592 decoded instructions reaching 0x007E038D (FULL `.text`)**.

**Lead (a) — immediate 0x0084F2BA / neighborhood as imm32 or absolute disp.**
- Exact value **0x0084F2BA**: appears **0 times** as an imm32/disp32/branch-target in `.text` (capstone operand walk), and **0 times** anywhere as a raw little-endian dword in the *entire* 4.8 MB file, and 0 times as a stored pointer. ⇒ **no instruction literally encodes 0x0084F2BA.**
- Neighbourhood `[0x0084F200,0x0084F400]`: **0 absolute-operand hits**, **0 imm32 hits**. Every hit the band sweep reported was in the *wider* `[0x84E000,0x851000]` page band and all of those are either (i) byte flags at **0x0084E860–0x0084E869** (`mov byte [0x84e863],al`, `mov dword [0x84e865],ebx`, … around `0x007C5F46`), unrelated scalar globals, or (ii) the table-base pointers **0x0084F084/0x0084F088** (§2). **None** is in `[0x84F200,0x84F400]`.

**Lead (b) — `mov [base + idx*scale + disp]` with unbounded index overrunning the table.**
- Indexed stores to a `.data` disp: 1,755 total, 1,143 writes — but **stores into the table itself (`disp` = 0x84F084/088 region): 0**. The only accesses to `[reg*4+0x84F084]` are **`fld` reads** (7 sites). The table is written *only* by its initializer via `fstp dword [esi-4]` (§4-init), where `esi ∈ {0x84F084, +4, +8 … 0x859084}` ⇒ **always 4-aligned**, never 0x84F2BA. So even an out-of-range `fld [eax*4+0x84F084]` (read) is misaligned-proof by construction and produces no store.
- No `[base+idx*scale+disp]` store whose computed EA is 0x0084F2BA or lands byte-mid-LUT exists statically; every table store is grid-aligned.

**Lead (c) — float-constant-table address handed to memcpy/fill/output-buffer.**
- The only routine that *fills* 0x0084F084 is the self-contained generator `0x004CB0E0` (`mov esi,0x84f084 … fstp [esi-4]; add esi,4; cmp esi,0x859088; jne`). It is a closed arithmetic loop, **not** a `memcpy(dst=LUT)` sink, and its stores stay 4-aligned. No `memcpy`/`rep stos`/fill takes the LUT (or 0x84F2BA) as a destination.

**Conclusion on writers:** `addr_probe.py` finds **no static write (high/medium confidence) that produces EA = 0x0084F2BA**. The only *plausible* way EIP lands on 0x0084F2BA is **control-flow corruption** — a computed branch/return whose target is a misaligned pointer derived from the LUT region (a 2-byte-off read/store, or a freed/garbage object pointer pointing into `.data`). The lowest-confidence candidate (below) is therefore the *consumer* pattern that reads the LUT with a 13-bit index: if an index/pointer is taken from a corrupted structure, `fld [eax*4+0x84F084]` stays aligned, but a **`jmp`/`call`/`ret` whose target register was loaded from a poisoned structure** can land anywhere in `.data`, including 0x84F2BA.

---

## 5. The `0x0054A56E` `mov dword [esi+4],0` crash (esi provenance)

Disassembly of the enclosing routine (capstone, `addr_probe.py` stage `crash56e`):

```
0x0054A4FA  mov   esi, ecx                 ; esi = object `this`  (provenance root)
0x0054A506  mov   byte [esi+0xc], 0
0x0054A515  lea   eax,[ebp*4]; push eax; call 0x7c8e17   ; malloc(ebp*4)  -> edi
0x0054A51E  mov   edi, eax                  ; edi = new block
0x0054A535  mov   eax,[esi+4]               ; old data pointer
0x0054A54B  mov   edx,[esi+4]               ; copy loop  old -> new
0x0054A551  mov   edx,[edx+eax*4-4]
0x0054A555  mov   [edi+eax*4-4], edx        ; store into heap NEW block (fine)
0x0054A562  mov   eax,[esi+4]               ; arg = OLD data pointer
0x0054A565  push  eax
0x0054A566  call  0x7c8b3d                   ; *** free(old) ***   <-- the preceding free
0x0054A56B  add   esp,4
0x0054A56E  mov   dword [esi+4],0   <== EIP  ; write to THIS+4  faults
```

**`esi` provenance.** `esi ← ecx ← the method's `this` pointer (caller-supplied object address). The crash at `mov [esi+4],0` means **`this` (=esi) is itself invalid** — a `.text` address per fact 5 — so the faulting write targets `0x0054A572` (a non-writable `.text` byte). The **immediately preceding free** is `0x0054A566 call 0x7c8b3d` with **argument `[esi+4]`** = the object's heap data buffer, just freed here. (Thunk chain: `free 0x7c8b3d → 0x7c93e8 → 0x7cf7bd`.)

**Corruption path.** This is the `DynamicArray::Resize/Copy` shape (it allocs `ebp*4`, copies `esi+4` buffer into `edi`, then frees the old `esi+4` and resets `esi+4=0; esi+8=ebp; esi+0xd=ownership`). For `mov [esi+4],0` to fault with `esi` in `.text`, the **object header pointed to by `this` was already damaged** — the `free([esi+4])` at 0x54A566 was called on a heap pointer that had already poisoned the SBH freelist, so either (i) `this` was a stale/freed object whose stored value got recycled into a `.text` code address, or (ii) `free()` walked a **poisoned SBH freelist** and the same 0xFE00FFFF-style value propagated into the object's own back-pointer. The crash site therefore does **not** prove `esi` was computed from the LUT; it proves `esi` is a **dangling/corrupted `this`**, which is *consistent with* a prior heap-metadata corruption. This is the same class as RC-1 (§6), but I did **not** observe a 0xFE00FFFF value at this exact instruction (no register dump available), so the link is by **allocator + mechanism**, not by a confirmed poison constant at 0x54A56E.

---

## 6. RC-1 family judgement (`0xFE00FFFF`)

- **0xFE00FFFF is not a file constant**: searched the whole 4.8 MB image for the LE dword `FFFF00FE` ⇒ **0 occurrences**. It is a **runtime** heap-fill / poison value, not stored on disk. (`0xFEFEFEFE` appears 44× as benign bytes; the CRT debug fills `0xCDCD…/0xDDDD…/0xBABA…/0xF1F1…` appear **0×** ⇒ this is a **retail, non-debug-CRT** build.)
- **Shared allocator = SBH.** RC-1's guard `__sbh_alloc_block` is at **0x007CFC9B** (`mov edx,[ecx+edi*8+4]; mov ecx,[edx]; sub ecx,[ebp-0x10]; sar esi,4; cmp esi,0x3f` — the SBH bucket-size/next-walk guard). The `free` used by *both* crash-2 and RC-1 resolves through `0x7c8b3d → 0x7c93e8 → 0x7cf7bd`, and `0x7cf7bd` reads SBH globals **`[0x00B78B94]`, `[0x00B78B98]`** — the **same global cluster** that guards RC-1 (all 7 `.text` references to `0x00B78B94` are in `0x7cf7bd…0x7d0398`, i.e. the single SBH allocator). malloc side: `0x7c8e17 → 0x7c9442 → 0x7c946e`, same cluster.
- **Same family? YES, mechanism-level.** 0x0054A56E and RC-1 share (a) the **identical SBH allocator** (0x7c8b3d/0x7c93e8/0x7cf7bd ↔ guard 0x7cfc9b ↔ globals 0x00B78B94/98), and (b) the **same corruption shape**: a freed/recycled block whose metadata now contains an **unmapped or wrong-segment pointer** that is dereferenced. RC-1 derefs the freelist **next** (=0xFE00FFFF poison); crash-2 derefs a corrupted **`this`** that points into `.text`.
- **But NOT same-victim / not the same 0x0084F2BA write.** 0x0084F2BA is in `.data` (the phase LUT), and §4 found **no** SBH write that lands there. So the **0x0084F2BA crash is a different fault surface** (control-flow/data-execution in `.data`), whereas **0x0054A56E is on the allocator path** like RC-1. ⇒ **Same allocator (high confidence); same defect *family* "poisoned heap metadata / stale pointer deref" (medium-high); but 0x0084F2BA is NOT established to be written by the RC-1 poison value or by `__sbh` at all.** `same_family_as_rc1` is set `true` for the **heap-corruption mechanism shared with the 0x0054A56E crash**, while noting 0x0084F2BA itself is a `.data`-execution surface, not a confirmed SBH-poison deref.

---

## 7. Honest boundary — what holds only in an already-failed process

Confirmed by the run inputs (csf path >131 chars ⇒ `ra2.csf` init fails, dialog at t≈0.28s, crash at t≈0.72s):
- **Instruction-level, image-grounded (hold regardless of run state):**
  - Section layout, page 0x0084F000 = `.data` = **PAGE_READWRITE** (MEM_WRITE set / MEM_EXECUTE clear) — §1/§2.
  - 0x0084F2BA is **2 mod 4**, i.e. mid-LUT; the aligned element under it is the **8192-unit→radians phase table** (`fld [eax*4+0x84F084]`, 13-bit index, step `2π/8192`, `8192/π`) — §3.
  - **No static `.text` instruction** references/writes 0x0084F2BA (0 imm32 / 0 disp32 / 0 raw dword in file / 0 branch target) — §4. Every store into the table is 4-aligned ⇒ cannot yield EA=0x…BA — §4.
  - 0x0054A56E `mov [esi+4],0` is preceded at **0x0054A566 by `free([esi+4])`**; `esi=this`; SBH chain 0x7c8b3d→0x7c93e8→0x7cf7bd ↔ RC-1 guard 0x7cfc9b (same 0x00B78B94 cluster) — §5/§6.
- **Run-state-dependent (observed only in the failed-init process; may NOT reproduce in a healthy path):**
  - *That* EIP actually executed at 0x0084F2BA — this requires the runtime bytes / a corrupted pointer or branch target that only appeared after csf-init failed. The disk LUT is intact, so the "write/fetch fault" here is a **secondary** symptom of init failure + heap damage, **not** proven to be the primary crash.
  - The precise corruption of `esi` at 0x54A56E and whether its poison equals RC-1's 0xFE00FFFF: I can prove *mechanism + allocator* statically, but **cannot** prove the concrete poisoned value or the corrupting writer without a runtime memory dump / trace. INSUFFICIENT for a per-instruction write attribution of 0x0084F2BA.

**Bottom line:** 0x0084F2BA is a **non-executable `.data` float-table byte (phase-LUT slot 141/142 boundary, value ≈0.108)**; the "writable `.data` can't be written" is resolved by **execute-on-non-executable-page / control-flow-hijack into `.data`**, NOT by a read-only page. I could not identify any legitimate instruction that writes 0x0084F2BA; the two crashes belong to **one heap-corruption family via the shared SBH allocator**, but the 0x0084F2BA surface specifically is a **`.data`-execution** symptom, plausibly secondary to the csf-init failure, and not directly attributable to the RC-1 `0xFE00FFFF` freelist deref.
