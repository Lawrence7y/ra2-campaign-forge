# r018/r019 Cross-Family Independent Verification — gamemd.exe INI subsystem (blind → grade)

Target: `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe` — SHA-256 `73201cc0…f67476`, size 4825360. **GATE PASS**.
Method: python + capstone 5.0.7 (detail=True; imm from `operands[].imm`, never decimal op_str). Full `.text` linear decode with byte-resync: **1,392,508 instructions** (>1.3M OK). The documented trap was reproduced exactly: a single `md.disasm` over all `.text` stops at **0x46F5A0** after **155,215** instrs; bytes there are the jump table (`04040404…04 03 8d | 49 00 c5 e4 46 00 04 e6 46 00 …` starting ~0x46F590). Global-stream membership was found unreliable (desync swallows E8 bytes: only 65/2426 sites reached in-stream), so per-site analysis used **real boundaries**: walk back ≤0x3000 to every `C3`/`C2 xx` ret, boundary = first non-{90,CC,00} byte after it, forward-decode from boundary must land on the site as `call <reader>`. **2426/2426 sites anchored, 0 failures.**
Empirical layouts confirmed: KEY slot = **2nd-to-last push** for all six readers, **last push** for GetSection; `ret` sizes 0x14/0xC/0xC/0x14/0x14/0x10/0x4. ReadDouble arg count varies (4–6 pushes; key still 2nd-from-last, e.g. `…push 'Damage', push section; call` at 0x427FAF).
Two M2 slot rules kept: **A** = 2nd-to-last of *consecutive* push-run (interleaved setup splits args -> fallback), **B** = 2nd-to-last push before the call across any interleaving (faithful; primary below).

## BLIND PHASE (derived and written before reading KB §11/§12)

### B1. 0x410A60 (`AbstractTypeClass::LoadFromINI`, thiscall: this=ecx? — ecx moved to esi, this kept in ebx; record-ID field used as section name)
(a) **2** ReadString calls: **0x410AA0** and **0x410AFB** (plus GetSection 0x526810 at 0x410A7F, Reset 0x526B00 at 0x410A74, 0x7C91D0 strncpy-ish at 0x410ABF/0x410B1A, 0x734E60 at 0x410B52). Function extent 0x410A60–0x410B8B (`ret 4`; head `81 EC 34 04 00 00`; 0x410B8B..+ = nops).
(b) 0x410AA0: key **0x817854 "Name"**, dst `lea edi,[ebx+0x64]`, cap **0x31 (49)**; copy loop 12×dword+1 = 0x31. 0x410AFB: key **0x81784C "UIName"**, dst `lea ebp,[ebx+0x3D]`, cap **0x20 (32)**; copy 8×dword = 0x20. Scratch [esp+0x44] is the def/dst staging buffer (push order: cap, def, dst, key, section).
(c) GetSection arg = `lea ebp,[ebx+0x24]` — **base = this-object, offset +0x24** (record-ID string doubles as INI section name; 0x526B00 zeroes [arg+4],[arg+8] beforehand).
(d) After key#2: `test byte[ebp]` → if UIName empty store **0x887734** (BSS, no disk bytes) at [this+0x60]; else `push 0xD7(215); push 0x817830("D:\ra2mdpost\AbsType.cpp"); ecx=UIName buf; call 0x734E60`; **result stored at [this+0x60]**. 0x734E60 = string→entry lookup over runtime table: count dword[**0xB1CF74**], nodes [0xB1CF6C], compare-fn 0x7C8D20, value arrays [0xB1CF7C]/[0xB1CF78], optional out-param via edx, `ret 8`.
(e) If dword[0xB1CF74]==0: `mov eax,0x84583C; ret 8` → returns pointer to literal **"*"** at 0x84583C (not NULL).

### B2. Field accesses in 0x410A60
| base+off | use | size |
|---|---|---|
| +0x24 | section/ID string (lea→GetSection, ReadString arg) | 0x18 observed span 0x24..0x3B |
| +0x3C | not touched here (gap) | 1 |
| +0x3D | UINameLabel dst | 0x20 → ends +0x5D |
| +0x5D..5F | gap (no byte touched) | 3 |
| +0x60 | store: 0x734E60 result or 0x887734 | dword |
| +0x64 | Name dst | **0x31 → boundary +0x95** |
Highest char array = Name@+0x64, size 0x31, end boundary **+0x95**. Naive sum (0x24+0x18+1+0x20+4)=**+0x61** ≠ observed +0x64; the 3-byte gap is real (YRpp alignment label = interpretation).

### B3. Raw `E8 rel32` scan, full .text, seven readers — total **2426**
ReadString 650 · ReadInteger 757 · ReadBool 651 · ReadDouble 306 · ReadUnicodeString 5 · ReadStringtableEntry 3 · GetSection 54.

### B4. M1 vs M2 (M1 = last push-imm in [0x7E1000,0xB79BE4) decoding to printable ASCII len>=2, scanned back from site to anchored fnstart; M2 = push sitting in KEY slot)
| reader | sites | M1 | M2-B literal | M2-B reg | M2-B imm-nonstr | M2-B none | M2-A literal | M2-A reg | M2-A imm-nonstr |
|---|---|---|---|---|---|---|---|---|---|
| ReadString | 650 | 567 | 514 | 131 | 5 | 0 | 509 | 130 | 11(+0 none) |
| ReadInteger | 757 | 737 | 720 | 23 | 2 | 12 | 720 | 23 | 2 (none 12) |
| ReadBool | 651 | 643 | 639 | 4 | 0 | 8 | 634 | 9 | 0 |
| ReadDouble | 306 | 304 | 304 | 1 | 0 | 1 | 235 | 68 | 2 |
| ReadUnicodeString | 5 | 5 | 5 | 0 | 0 | 0 | 4 | 0 | 1 |
| ReadStringtableEntry | 3 | 2 | 2 | 0 | 0 | 1 | 2 | 0 | 0 |
| GetSection | 54 | 17 | 3 | 51 | 0 | 0 | 3 | 51 | 0 |
| **TOTAL** | **2426** | **2275** | **2187** | **210** | **7** | **22** | 2107 | 281 | 16 |
M1-vs-M2 agreement where both literal: 2187 sites, M1==M2 **1943**, M1≠M2 **244** (when section is an immediate push it is closer to the call than the key ⇒ M1 grabs the **section** literal: top "General" 56×/57×, "Basic", "MultiPlayer"…). M1 len>=1 variant: 2278/1876 (adds single-char keys `X` 2, `Y` 2, `1` 1, `*` 1).

### B5. Sites where M1 recovered a literal but M2 KEY slot is a REGISTER
Rule B: **83 sites** — ReadString 48, GetSection 14, ReadInteger 17, ReadBool 4, ReadDouble 1. (Rule A: 155 — the extra 72 are ReadDouble cases where setup between def-pairs breaks the consecutive run.)
Register provenance (traced back ≤24 instrs): **34 = prior call's return** — of which **25 → 0x526CC0** (key-name getter: sites read `Warheads`×3, `Animations`, `VoxelAnims`, `Particles`, `ParticleSystems`, `TeamTypes`, `ScriptTypes`, `InitStrings`, `PhoneBook`, `MultiMaps`, `Battles`, `Campaigns`, `Houses`, `<none>`×2, `undefined`…), 4 → 0x7B5440, 3 → 0x7C9BFD (`VariableNames`×3), rest misc; **23 = `lea reg,[esp+N]`** (stack buffer = sprintf-built key); **10 = `add reg,[global]+N` / `lea reg,[base(+idx)]`** (field/element address, e.g. `[0xA8B230]+0x125C`, `[edi*4+…]`); **4 = `mov reg, imm`** into BSS buffer (0x887180, 0x889F64); 5 reg-moves; 6 from memory; 3 untraced.
Classification of M1 strings at these 83 (rule B; rule A in []):
- (i) **format strings (contain %): 29 sites / 21 distinct** [27/20] — `%d,%d,%d`(2), `%d`(2), `%s%d`(2), `EliteWeapon%d`(2), `EliteStage%d`(2), `%sBarrelLength`(2), `%sBarrelThickness`(2), `%sTurretLocked`(2), `%03d`, `Map%d`, `%sSounds`, `Tile%02d{Anim,XOffset,YOffset,AttachesTo,ZAdjust}`(5), `TV%d`, `LV%d`, `FiringSyncFrame%d`, `BurstDelay%d`, **`PowerUp%01dYSort`**(1 @0x4647ED).
- (ii) **source-file path (backslash): 1 site / 1 distinct** — `D:\ra2mdpost\Scenario.CPP` @0x686ED0 (GetSection; key = eax ← `add eax,0x125C` of [0xA8B230]; the literal had been consumed by `call 0x734E60` only **18** instrs earlier with push 0xC5F/0x83D838).
- (iii) **other: 53 sites / 40 distinct** [127/113] — section names & filenames mis-grabbed: `Warheads`(4), `VariableNames`(3), `MultiMaps`(3), `Waypoints`(3), `TaskForces`(2), `TeamTypes`(2), `Volume`(2), `<none>`(2), `undefined`(2), `ShadowTiles`, `LANGRULE.INI`, `MISSIONMD.INI`, `wolinfoMD.ini`, `Name`, `UIName`, `Sequence`, `Image`, `Digest`, `Campaigns`, `CellTags`, `Animations`, `VoxelAnims`, `Particles`, `ParticleSystems`, `ScriptTypes`, `InitStrings`, `PhoneBook`, `Basic`, `Themes`, `Houses`, `Battles`, `0,NONE`… ⇒ **in every conflict, M1's "key" is not the key**: it is a format template for a runtime-built key, or a section-name/older literal near the key-builder call.

### B6. Distinct keys under M1
Recovered sites 2275; **distinct 1873**; **distinct with >=2 occurrences 160** (len1: 2278/1876/160). Distinct under M2-B-literal: 2187 sites / **2003** distinct / >=2: **136**. Global union of M1∪M2 strings: 2049 distinct. M1 top multi-occurrence: General 57, Basic 38, MultiPlayer 21, RandomMap 20, Lighting 20, Header 12, Options 11, SerialDefaults 10, Video 10, WOnline 9 — **all section names**; Name=5, UIName=3, Image=4, Cameo=3, TechLevel=4, Cost=3, ROF=3, Armor=2, Strength=2, Range=2, Speed=2, Power=2.

## COMPARISON PHASE (KB §11–12.5 read only after the above was written)

| # | Claim (as in KB) | Grade | Byte evidence |
|---|---|---|---|
| 1 | 11.1 `+0x24` is ID and used as GetSection section name; section==ID, not display name | **CONFIRMED** | 0x410A79 `lea ebp,[ebx+0x24]`; 0x410A7F `call 0x526810`; 0x410AF2 re-lea at ReadString section slot |
| 2 | 11.2 exactly 2 ReadString calls, 0x410AA0/0x410AFB | **CONFIRMED** | B1(a) |
| 3 | 11.2 Name→+0x64 cap 0x31, evidence 0x410A91/94/98 | **CONFIRMED** | bytes match exactly; "Name"@0x817854 |
| 4 | 11.2 UIName→+0x3D cap 0x20, evidence 0x410AEB/EE/F5 | **CONFIRMED** | bytes match; "UIName"@0x81784C |
| 5 | 11.2 UIName parsed via 0x734E60 → stored +0x60 (snippet 0x410B3C/42/50/52/58) | **CONFIRMED** | all five addresses byte-exact |
| 6 | 11.2 0x734E60 returns constant 0x84583C (not NULL) when table uninitialized | **CONFIRMED** | `mov eax,0x84583C; ret 8` under `dword[0xB1CF74]==0`; 0x84583C = "*" |
| 7 | 11.3 layout +0x24/+0x3C/+0x3D(0x20)/pad3/+0x60/+0x64(0x31)/end +0x95 | **CONFIRMED** | all offsets/gaps observed (B2); "alignment" cause = label |
| 8 | 11.4 dual positive control `81 EC 34 04 00 00` + 0x817854=="Name" | **CONFIRMED** | bytes verified |
| 9 | 12.0 truncation mechanism: single disasm stops at 0x46F5A0 (jump table, `49 00 c5 e4 46 00…`, prior run of 04s), 155,215 instrs | **CONFIRMED** | reproduced stop at exactly 0x46F5A0, count 155,215; cited table bytes at 0x46F59E/0x46F590 |
| 10 | 12.0 "covered only the first 9% of .text" | **REFUTED** | 155,215/1,392,508 = **11.1%** (bytes: 0x6E5A0/0x3DF38D = 11.1%); same conclusion, wrong number |
| 11 | 12.0 total reader call points = 2,426 | **CONFIRMED** | B3 (independent E8 scan) |
| 12 | 12.0 recovered-key sites = 2,305 | **REFUTED** | blind M1(len>=2)=**2,275** (len1 2,278; strict key-slot M2-B=2,187). No variant reproduces 2,305 |
| 13 | 12.0 distinct keys = 1,893 | **REFUTED** | M1=**1,873** (len1 1,876; M2-B 2,003; union 2,049). None is 1,893 |
| 14 | 12.0 E8 scan == instruction scan, per-site zero-diff | **CONFIRMED** | all 2,426 E8 targets verified as `call reader` from real boundaries (0 FP, 0 FN); spot windows 0x410000-0x430000/0x520000-0x540000/0x700000-0x730000 diff=0 |
| 15 | 12.0 old 478/473/427 figures void | **UNVERIFIABLE** | historical prior-tool-run numbers, not derivable from bytes |
| 16 | 12.1 per-reader table 757/651/650/306/54/5/3 | **CONFIRMED** | identical to B3, all seven rows |
| 17 | 12.2 "121 unrecovered sites" | **REFUTED** | M1-unrecovered=**151**; true no-literal-key (M2-B reg+imm-nonstr+none)=**239**; 121 only "lower bound" per their own addendum |
| 18 | 12.2 buckets register 55 / bss_key 59 / unknown 7 | **REFUTED** | M1-unrecovered classes: reg-key **126**, imm-into-BSS **3**, slot-none **22**; M2-B: reg **210**, imm-nonstr **7** (0x889F64×5,0x831898×4…). No reading yields 55/59/7 |
| 19 | 12.2 three unrecoverable classes: key-from-GetKeyName-0x526CC0 / key-in-BSS / key=field-address | **CONFIRMED** | 25 sites reg←`call 0x526CC0`; BSS bufs 0x889F64/0x887180/0x887734 (va2off=None) in slots; `lea [ebx+0x24]` at 0x410A7F |
| 20 | 12.2 "编译器不能假设索引里没有=不读" | **CONFIRMED** | 210 register-built keys + 239 no-literal sites prove index≠complete |
| 21 | 12.2 addendum: M1 mis-attributes register-key sites; Scenario.CPP@0x686ED0 is a confirmed mis-attribution (class-2) | **CONFIRMED** | B5: exactly **1** path-class conflict = 0x686ED0 GetSection, key=`[0xA8B230]+0x125C`, literal 0x83D838 consumed by 0x734E60 just before |
| 22 | 12.2 addendum: that consumption happened "51 instructions" before the site | **REFUTED** | measured **18** instructions between `call 0x734E60` (0x686E85) and site (0x686ED0) |
| 23 | 12.3 corrected: %-keys = 21 distinct | **CONFIRMED** | M1 %-distinct = **21** (rule B) |
| 24 | 12.3 corrected: %-sites = 34 | **REFUTED** | measured **29** (rule B) / 27 (rule A); len1 variant also 29 |
| 25 | 12.3 `PowerUp%01dYSort` template real, key via sprintf | **CONFIRMED** | fmt @0x8194D4 pushed 0x4647BF, sprintf → stack buf, key slot ecx=`lea [esp+0x268]`, site 0x4647ED; M1 grabs template exactly |
| 26 | 12.3 "n = 0..9" loop bound | **UNVERIFIABLE** | not traced; `%01d` consistent with 0..9 |
| 27 | 12.4 "164 keys read at multiple sites" | **REFUTED** | M1 >=2 = **160** (len1 also 160; excl GetSection 149; per-function 129; M2-B 136). None equals 164 |
| 28 | 12.4 high-frequency = Name/UIName/Image/Cameo/Armor/Cost/Strength/TechLevel/Range/ROF/Speed/Power ("every TypeClass reads each once") | **REFUTED** | actual top multi-read keys are **section names** (General 57, Basic 38, MultiPlayer 21, RandomMap 20, Lighting 20…); Name only **5** sites (one of them = 0x410AA0), UIName **3** — and derived classes do *not* each read a literal "Name": the ID-as-section mechanism (11.1) replaces it |
| 29 | 12.5 control 1 (E8==instr-scan, 2426==2426 zero-diff) | **CONFIRMED** | #14 |
| 30 | 12.5 control 2 (≥1 Name/UIName site inside 0x410A60) | **CONFIRMED** | 0x410AA0, 0x410AFB |
| 31 | 12.5 control 3 (total ≥ 2000) | **CONFIRMED** | 2426, with 1,392,508-instr full decode |
| 32 | 12.1 sub-claim: ReadUnicodeString "zero sites" overturned → 5 | **CONFIRMED** | 5 sites: 0x597B0C, 0x597E51, 0x5FABC1, 0x686DE7, 0x6982C9 |

### Does B5 REFUTE or merely QUALIFY claim 12.2?
**Both, split by sub-claim.** The *structural* claim 12.2 (three unrecoverable classes; absence-from-index ≠ not-read; addendum that M1 mis-attributes) is **corroborated** — B5's 83 conflict sites are exactly the mis-attribution population it predicts. But the *numbers* of 12.2 are **refuted outright**: "121 unrecovered / register 55" undercounts a full ~2× — my independent count of sites whose key is a register (210), BSS-imm (7) or absent (22) is 239, of which 83-155 still hand M1 a non-key literal. So 12.2's headline figures are REFUTED, while the corrected "lower bound" caveat added in R-031 survives: true unrecovered ≈ 239, not "121+". The KB's own tooling (its len-agnostic M1 + looser window) also inflates "recovered" to 2,305 vs my 2,275 — same methodological leak, larger by ~30 sites.

INCOMPLETE: none.

VERDICT: CONFIRMED 21 REFUTED 9 UNVERIFIABLE 2
