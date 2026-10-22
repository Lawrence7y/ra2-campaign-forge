# r017 Cross-Check — Independent Byte Verification (verifier: qwen family)

GATE: PASS — SHA-256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`, size 4825360, match. Read-only; never launched. Tooling: Python312 + capstone 5.0.7, operands parsed from `operands[].imm` (not op_str).

# BLIND PHASE (derived before reading any claim set)

## B1. Function 0x5295F0 — bool/logical reader (thiscall, `ret 0xc`)

Value-block at 0x529759..0x5297A3 (reached via 0x529759: `mov esi,0xb78830` → 0x52975E):

```
0x52975E mov esi,[0xb78830]; test esi,esi; je 0x52974B
0x529764 mov esi,[esi+0x10]; test esi,esi; je 0x52974B
0x52976B movsx ecx, byte ptr [esi]     ; FIRST byte of value string
0x52976E push ecx; call 0x7c97d3       ; helper H1
0x529774 add eax,-0x30 ; add esp,4
0x52977A cmp eax,0x29  ; ja 0x52974b   ; bounds test 0..0x29
0x529781 mov dl,[eax+0x5297b4]         ; 42-byte class table
0x529787 jmp dword [edx*4+0x5297a8]    ; 3-way jump table
```

Jump table (raw at 0x5297A8): `9a 97 52 00 | 8e 97 52 00 | 4b 97 52 00`
→ class 0 = 0x52979A, class 1 = 0x52978E, class 2 = 0x52974B.

Dispatch bodies (raw):
- 0x52979A: `pop edi; pop esi; pop ebp; xor al,al; pop ebx; add esp,0xc; ret 0xc` → returns **FALSE**.
- 0x52978E: `pop edi; pop esi; pop ebp; mov al,1; pop ebx; add esp,0xc; ret 0xc` → returns **TRUE**.
- 0x52974B: `mov al,[esp+0x28]; pop…; ret 0xc` → loads the **default byte argument** (also target of `ja` out-of-range and every cache-miss/jz path).

Class table 0x5297B4 (42 bytes, ASCII 0x30–0x59), raw:
`00 01 02×20 00 02×7 00 02×5 01 02×5 01 02×4 01` — full: `00010202020202020202020202020202020202020002020202020202000202020202010202020201`

| idx | char | class | meaning |
|---|---|---|---|
| 0 | '0' | **0** | FALSE |
| 1 | '1' | **1** | TRUE |
| 22 | 'F' | **0** | FALSE |
| 30 | 'N' | **0** | FALSE |
| 36 | 'T' | **1** | TRUE |
| 41 | 'Y' | **1** | TRUE |
| others (36 of 42) | ':'..'E','G'..'M','O'..'S','U'..'W','X','Z' | 2 | default arg |

Exactly **6 non-2 chars**: 0→F(0), 1→T(1), F→F(0), N→F(0), T→T(1), Y→T(1).

Helper H1 @ 0x7C97D3 (fast path): `cmp eax,0x61; jl pass; cmp eax,0x7a; jg pass; sub eax,0x20; ret` (slow path = CRT locale table via [0xb782a0] flag / 0x7C9842). Range **a–z (0x61–0x7a)**, **subtracts 0x20** → maps lowercase to uppercase → this is **TOUPPER** (named by bytes, not habit). Combined with the table: lookup is case-insensitive; an unrecognized first byte yields the caller's default, **not** a hardcoded false.

## B2. Function 0x5276D0 — integer reader (thiscall, `ret 0xc`)

strlen block 0x527877: `repne scasb; not ecx; dec ecx; movsx edx, byte ptr [ecx+edx-1]` (LAST byte, via ecx=len, edx=base ptr) → `push edx; call 0x7caff4; add esp,4; cmp eax,0x68; jne 0x5278ba`.

- (b) Helper @ **0x7CAFF4** (fast path): `cmp eax,0x41; jl pass; cmp eax,0x5a; jg pass; add eax,0x20; ret` (locale slow path as H1). Range **A–Z (0x41–0x5A)**, **adds 0x20** → maps uppercase to lowercase → this is **TOLOWER**. Result compared to 0x68 = **'h'**.
- (a) Taken branch (last byte is h/H), 0x527896: pushes out-slot `[esp+0x28]`, **format string 0x825BB4 = "%xh"**, value-string ptr `[esi+0x10]`; `call 0x7ca530` (3-arg cdecl sscanf wrapper: sets state 0x49, calls 0x7D15A0/0x7D170D = CRT input core); result `mov eax,[esp+0x34]`; `ret 0xc`. So "…h"/"…H" suffix ⇒ parsed as hex with literal 'h' in the format → "100H"-style works (case-insensitive via tolower).
- Preceding branch 0x527851: if FIRST byte == '$' (0x24): `push [esp+0x28]; push 0x825BB8; push edx; call 0x7ca530` — format **"$%x"** ⇒ Westwood '$' hex literal form.
- (c) Not-taken branch 0x5278BA: `mov edx,[esi+0x10]; push edx; call 0x7c9bfd`. 0x7C9BFD is a **1-arg forwarder**: `push [esp+4]; call 0x7c9b72; pop ecx; ret` → target 0x7C9B72 = hand-rolled decimal atoi: strips whitespace (ctype table [0x87C590] bit 8 / call 0x7D1311), handles +/- (0x2d/0x2b), digit loop `lea eax,[ebx+ebx*4]; lea ebx,[esi+eax*2-0x30]` (n = n*10 + d - '0', bit 4 = digit), final `neg eax` if '-'. No hex/0x prefix handling ⇒ pure base-10 fallback (strtol-decimal equivalent).

## B3. Function 0x529560 — bool writer (WriteBool family, `ret 0xc`)

- 0x529560: `al=[esp+0xc]; test; je→0x825BF4 else→0x825BF8`; pushes literal + 2 args; `call 0x528660`.
  - **0x825BF4 = "no"**, **0x825BF8 = "yes"** (raw .data bytes: `6e 6f 00 00 79 65 73 00`).
- Adjacent 0x5295A0 (thiscall variant, calls CRT dup 0x7B5440) pushes the same two literals to 0x528660. ⇒ true writes "yes", false writes "no" (0x528660 = string writer).

## B4. Six readers — shared cache preamble `[this+4]` hash / `[this+8]` cached section ptr

| VA | role (bytes-derived) | cmp key vs [x+4] | cache load [x+8] | verdict |
|---|---|---|---|---|
| 0x528A10 | ansi string reader (`ret 0x14`) | 0x528A4D `cmp ebx,[ebp+4]` | 0x528A55 `mov esi,[ebp+8]` | **yes** |
| 0x528F00 | wide/comma-hex list reader (`ret 0x14`) | 0x528F3C `cmp ebx,[ebp+4]` | 0x528F45 `mov esi,[ebp+8]` | **yes** |
| 0x529160 | wide array reader (`ret 0x10`) | 0x529198 `cmp ebx,[ebp+4]` | 0x5291A1 `mov esi,[ebp+8]` | **yes** |
| 0x5283D0 | double reader (`ret 0x10`) | 0x5283F5 `cmp ebp,ecx` (ecx=[ebx+4]) | 0x5283FE `mov esi,[ebx+8]` | **yes** |
| 0x5276D0 | integer reader (`ret 0xc`) | 0x5276F5 `cmp ebp,ecx` (ecx=[ebx+4]) | 0x5276FE `mov esi,[ebx+8]` | **yes** |
| 0x5295F0 | bool reader (`ret 0xc`) | 0x529613 `cmp ebp,[ebx+4]` | 0x52961C `mov esi,[ebx+8]` | **yes** |

On miss all re-fill via 0x4A1DE0 (hash fn) + map insert 0x52B4F0/0x52B620/0x52B170/0x52B390 and store `[this+4]=key,[this+8]=section`. Globals: cache chain head [0xB78830], not-found singleton [0xB7882C].

Prologue byte-identity: 0x5295F0 (ReadBool) vs 0x5276D0 (ReadInteger) share **11 identical leading bytes** `83 EC 0C 33 C0 53 55 8B 6C 24 18` (sub esp,0xC; xor eax,eax; push ebx; push ebp; mov ebp,[esp+0x18]); diverge at offset 0xB (ReadBool `push esi`=56 vs ReadInteger `mov ebx,ecx`=8B D9). 0x5276D0 vs 0x5283D0 share 17 bytes (differ only in 2 jump displacements — same generated preamble). 0x528A10/0x528F00/0x529160 share zero literal entry bytes (alloca `b8 14 50 00 00 e8…` at 0x528F00; `sub esp,0x414` at 0x529160).

Other bytes-of-note for later grading:
- 0x5283D0 returns double in ST(0): every ret path ends `fld qword ptr [esp+…]` (0x528525/0x528588/0x528596); parses via `sscanf("%f")` (0x825BD8) + `strchr('.')`-style tail; applies `fmul qword [0x7E3808]` = **0.01** in one path.
- 0x528F00 frame: `mov eax,0x5014; call 0x7CA650` (__alloca_probe) ⇒ **0x5014 (20500) byte frame**, 0x5000 buffer; stores `mov word ptr [esi],dx` ⇒ **16-bit/wide writes**.
- CSF: no reference to any "csf" text inside the six readers; ASCII 'ra2.csf'/'.csf'/'***NO_STRING*' exist elsewhere (.data 0x840C72/0x8457ED). Source string "D:\ra2mdpost\Ini.CPP" (0x825BDC) is debug-assert context in 0x529160/0x528F00.

# COMPARISON PHASE (claim set read only after BLIND above; kb 30_ini_subsystem.md ## 10 → ## 10.4)

| # | Claim (§) | Verdict | Byte evidence (mine) |
|---|---|---|---|
| 1 | 10.1 table: entry bytes + ret sizes for 9 VAs (0x528A10 `83 EC 0C`/ret 0x14; 0x528F00 `B8 14 50 00 00`/ret 0x14; 0x529160 `81 EC 14 04 00 00`/ret 0x10; 0x5283D0 `83 EC 0C`/ret 0x10; 0x5276D0 & 0x5295F0 `83 EC 0C`/ret 0xC; 0x528660 `83 EC 38`; 0x529560 `8A 44 24 0C`/ret 0xC; 0x528E00 `51 53 55 56`) | CONFIRMED | Raw bytes + ret scan: 528A10 `83ec0c`→ret 0x14; 528F00 `b814500000e8`→ret 0x14; 529160 `81ec14040000`→ret 0x10; 5283D0 `83ec0c`→ret 0x10; 5276D0/5295F0 `83ec0c`→ret 0xC; 528660 `83ec38`; 529560 `8a44240c`→ret 0xC; 528E00 `51535556`. "0x14KB"=0x5014B (20500B) and "1KB"=0x414B: consistent with my B4/§10.4 checks. |
| 2 | 10.1: all six readers share preamble `cmp` key vs `[this+4]` then cached section via `[this+8]` | CONFIRMED | B4 table — yes for all six: 0x528A4D, 0x528F3C, 0x529198, 0x5283F1+F5, 0x5276F1+F5, 0x529613; each followed within ≤8 bytes by the `[this+8]` load. ReadBool/ReadInteger byte-identical prologue prefix = 11 bytes (`83 EC 0C 33 C0 53 55 8B 6C 24 18`), diverge at 0xB (register allocation only). |
| 3 | 10.2: ReadBool uses only FIRST byte (`movsx ecx,[esi]`) | CONFIRMED | 0x52976B exactly as quoted. |
| 4 | 10.2: call helper, then `add eax,-0x30`, `cmp eax,0x29`, OOB→default path | CONFIRMED | 0x52976F call 0x7C97D3; 0x529774 `add eax,-0x30`; 0x52977A `cmp eax,0x29`; 0x52977D ja→0x52974B. |
| 5 | 10.2: 42-entry class table @0x5297B4; exactly 6 non-default entries: 0→false, 1→true, F→false, N→false, T→true, Y→true | CONFIRMED | Raw table hex in B1; non-2 set = {'0':0, '1':1, 'F':0, 'N':0, 'T':1, 'Y':1}; classes map onto false/true bodies via jump table. |
| 6 | 10.2: 3-way table @0x5297A8: class0→0x52979A `xor al,al` (false), class1→0x52978E `mov al,1` (true), class2→0x52974B `mov al,[esp+0x28]` (caller default) | CONFIRMED | Jump table raw `9a975200 8e975200 4b975200`; bodies byte-verified. |
| 7 | 10.2: 0x7C97D3 = toupper ('a'..'z' → −0x20) | CONFIRMED | Fast path: cmp 0x61 jl / cmp 0x7a jg / sub eax,0x20 (B1). Named independently from range bytes; identical to claim. |
| 8 | 10.2: case-insensitive first-letter recognition (y/n/t/f etc. by first char) | CONFIRMED | toupper pre-table ⇒ 'f','n','t','y' fold onto F/N/T/Y; single-byte table lookup means only the first char is consulted ("YesPlease"/"Nonsense" follow the first letter). |
| 9 | 10.2: any other first char (e.g. '2') ⇒ caller default, silently, NOT false | CONFIRMED | class-2 body 0x52974B loads [esp+0x28]; 36/42 slots class 2; out-of-range `ja` and all miss paths also route to 0x52974B. |
| 10 | 10.2: WriteBool@0x529560 writes literal "yes"@0x825BF8 / "no"@0x825BF4 ⇒ read/write vocabularies differ | CONFIRMED | B3: al≠0 pushes 0x825BF8="yes", al==0 pushes 0x825BF4="no", then 0x528660 (WriteString). Raw .data bytes `79657300` / `6e6f00`. |
| 11 | 10.3: strlen via `repne scasb`, then LAST byte `movsx edx,[ecx+edx-1]` | CONFIRMED | 0x527877–0x527883 exactly. |
| 12 | 10.3: helper @0x7CAFF4 = tolower ('A'..'Z' → +0x20), compared to 0x68 ('h') | CONFIRMED | Fast path cmp 0x41/0x5A + add 0x20; `cmp eax,0x68` @0x527891. Named independently from bytes; matches claim. |
| 13 | 10.3: taken branch pushes format @0x825BB4 = "%xh", calls sscanf-like @0x7CA530 (value, fmt, dest-slot) | CONFIRMED | 0x527896–0x5278A4; 0x825BB4 raw bytes `%xh`; 0x7CA530 wraps CRT input core (0x7D15A0/0x7D170D). (Unmentioned bonus branch: first byte '$' → "%x" style fmt "$%x"@0x825BB8.) |
| 14 | 10.3: `100h` ⇒ hex 0x100; suffix case-insensitive so `100H` works too | CONFIRMED | tolower(last byte) before 'h' compare ⇒ H folds to h; both reach the `%xh` sscanf path; result read from dest slot @0x5278A9. |
| 15 | 10.3: "`Key=0x100` also accepted by %xh" | UNVERIFIABLE | Requires runtime behavior of CRT `%x` 0x-prefix handling inside 0x7D170D's format engine; call-site bytes only establish the "%xh" shape. Statically undecidable from this window (for `0x100` the last byte is '0' ≠ 'h', so it routes to the decimal fallback anyway; whether fallback then yields 0 at 'x' is a strtol-semantics question, not bytes here). Not reconciled toward claim. |
| 16 | 10.3: not-taken branch calls @0x7C9BFD as strtol(Value) | CONFIRMED | 0x7C9BFD = 1-arg forwarder (`push [esp+4]; call 0x7C9B72; pop ecx; ret`); 0x7C9B72 = in-binary base-10 atoi (whitespace strip, +/-, `n*10+d−0x30` loop, neg). strtol-decimal equivalent (structurally the forwarder→worker shape). |
| 17 | 10.4: ReadDouble@0x5283D0 — 8-byte default arg; result returned in ST0 | CONFIRMED | ret 0x10 (key+value+8-byte default); every ret path ends `fld qword ptr [esp+…]` (0x528525/0x528588/0x528596 = ST0). Parses via sscanf "%f"@0x825BD8. (Extra `fmul [0x7E3808]`=0.01 percent path exists; non-conflicting.) |
| 18 | 10.4: ReadUnicodeString@0x528F00 frame 0x5014 ≈ 20KB; buffers value before writing caller buffer | CONFIRMED | `mov eax,0x5014; call 0x7CA650` (__alloca_probe) @0x528F00; epilogue `add esp,0x5014`; copies into 0x5000-byte local via 0x7C91D0 (memcpy), splits on ','@0x817F70, per-token `sscanf %x`@0x825BD4, wide stores `mov word[esi],dx`. |
| 19 | 10.4: ReadStringtableEntry@0x529160 frame 0x414 (1KB); reads value then CSF string-table lookup producing wide ptr | CONFIRMED | `sub esp,0x414`; cache preamble @0x529198; tail calls 0x734E60 = string-table resolver keyed off globals 0xB1CF74/0xB1CF6C (entry size 0x28; returns wide ptr from 0xB1CF78/0xB1CF7C; sentinel 0x84583C when table uninitialized — matches kb §11.2 note; miss path formats "MISSING:"@0x845820). |

Traps handled: immediates parsed via `operands[].imm` (e.g. 0x529774 = `add eax,-0x30`, decimal rendering noted); 0x5297A8/0x5297B4 read as raw data, not disassembled from mid-stream; last-byte block anchored at real start 0x527877 (0x527878 offset would produce the pseudo-`cli`); all function starts used as disasm anchors.

No blind-vs-claim conflict on items 1–14 and 16–19. Item 15 not statically decidable; left UNVERIFIABLE rather than reconciled.

VERDICT: CONFIRMED 18 REFUTED 0 UNVERIFIABLE 1
