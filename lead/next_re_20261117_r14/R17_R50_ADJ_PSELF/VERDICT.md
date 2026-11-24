IMAGE: D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe  sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476  size 4825360  (ra2bench\gamemd.exe is byte-identical)
READ-ONLY. No process, no debugger, no disassembly. File bytes read by work.py: 24148995 dwords/bytes accounted (whole .text+.rdata+.data section raw ranges + PE header; nothing outside). Reproduce: python work.py
PE section table used for every VA->offset (see section 5). No CR in any artifact (gate scripted at end of work.py).

# R17-R50-ADJ-PSELF - VERDICT

## Ruling (four-way, one pick)

**3 = the two facts name two different dwords, and neither is the "pSelf" they claim it is.**

* This build's COL is the **5-dword** MSVC layout (0x14 bytes). **It has no self/pSelf field at all.**
  A six-dword COL (pSelf at +0x00) is structurally excluded: 0 of 1211 COLs have a valid pTD at +0x10.
* **F31 ("COL.pSelf is always 0")** - inside COL there is no such field, so the statement has no
  referent. It *is* true of the dword **just before** a 257-COL minority (all secondary structures,
  see below), not of anything inside COL.
* **F01 ("954 primary COLs, pSelf=COL-0x10")** - the count 954 and the "954" group are real, but
  the field is **at COL-0x4** (outside COL), it is **never** COL-0x10 (0 of 1211 are), and
  "primary" is being read off a secondary structure. F01 needs rewriting on three points.

Nothing was stretched to make the two agree: they agree only on the number 954, which is a
counting artifact (see section 3).

## 1) Byte offset of the field

The field that carries the "self" value sits at **COL-0x4** - i.e. **outside** the COL structure,
in the 0x10-byte record that precedes every COL.

Proved layout of COL in this image (all 1211 COLs, no exceptions):

| COL-relative | field | observed |
|---|---|---|
| +0x00 | signature | 0 for all 1211 |
| +0x04 | offset | 0..0x1000 |
| +0x08 | cdOffset | 0..0x1000 |
| +0x0C | pTypeDescriptor | absolute VA, all 1211 resolve to a real TD (988 TDs, name inline at TD+8) |
| +0x10 | pClassDescriptor | absolute VA |
| **+0x14** | **-- end of COL --** | *(first dword of next record)* |

Control that kills any pSelf-inside-COL reading: a 6-dword COL would need a TD pointer at +0x10;
**0 of 1211** have one. The 5-dword reading is the only self-consistent one.
Every COL is the target of a `mov dword ptr [vt-4], COL` style store: 1211/1211 COLs are
referenced from a dword immediately preceding a vtable whose slot 0 is in .text.

The 0x10-byte record before each COL, when it exists in the "954" form, is
`{0,0,smallInt,ptr}` (855 of 1211 have the first three dwords = 0,0,<0x1000; frequency at random
.rdata offsets over the same stride is 86/3074, so this is not noise). Its last dword is the
"self-ish" value. **This is not the standard MSVC 4-dword pSelf-bearing COL** (the 257 zero-headed
ones prove a 5-dword COL exists), so I do not name it - I only report that it is a separate
pre-COL record.

## 2) Actual value on primary COLs

Definition used (stated explicitly because "primary" is what decides the answer):

* COL set: 1211 COLs, 954 distinct class names (TD names), **91 classes own a COL that is preceded
  by an all-zero record (secondary structure); those 91 generate the 257 zero-headed COLs.**
* **primary COL of a class = its lowest-VA zero-headed COL if it has one, else its lowest-VA COL.**
  -> **954 primary COLs, exactly one per class.**

Actual value at COL-0x4, primary COLs (**954**):

| value | count |
|---|---|
| 0 | **91** |
| = COL-0x10 | **0** |
| other (= COL - 0x18/0x1C/0x20/0x24/... , always points into .rdata) | **863** |

All COLs (1211): 0 -> 257, = COL-0x10 -> **0**, other -> 954.

So on primary COLs the field is 0 only 9.5% of the time; it is *never* COL-0x10.
Delta histogram (primary, nonzero group): 0x18=51, 0x1C=205, 0x20=575, 0x24=166, 0x28=23,
plus a tail 0x30..0x60 (9). None of these equals 0x10.

## 3) 20+ cross-class samples

col_samples.tsv holds **30** primary COLs (16 evenly spaced across .rdata + 9 zero-headed + extras),
columns: COL_VA / field_offset / value / eq_zero / eq_COL_minus_0x10 / class_name.
Distribution in the file: 0 -> 9, other -> 21, COL-0x10 -> **0**.

## 4) Incidental: is 954 the number of primary COLs?

**Yes, 954 is a real and reproducible count of per-class primary COLs - but it is not "pTD/PCHD
inclusive" the way F01 implies, and it is out of a total of 1211 COLs, not 954.**
Independent corroboration of the same number: 954 = the number of distinct mangled names appearing
in whole-image TD records that are reached from a live COL.
(TD records: 988 - the 34-name gap is TDs that no vtable-COL in this image points at.)

Consequence for F31's "cannot determine the start point" prohibition: **the prohibition stays**.
The reason is not that pSelf is always 0 - it is that **there is no pSelf field inside COL at all**,
so "pSelf points at itself" can never be used, on any COL, primary or not. F31's conclusion
survives; its stated reason ("pSelf always 0") is wrong and should be replaced by
"COL has no self field (5-dword layout, pTD at +0x0C)".
The compliant-COL test F31 prescribes (signature==0 + small offset + pTD -> TD name) is exactly
what I used and it works: 1211/1211.

## 5) VA -> file offset method

Mapping used section-table only:
`off = section.PointerToRawData + (VA - (ImageBase + section.VirtualAddress))`, ImageBase 0x400000.
Sections: .text VA 0x1000/raw 0x1000, .rdata 0x3E1000/0x3E1000, .data 0x412000/0x412000,
.rsrc 0x77A000/raw 0x47E000 (**VA != raw here**), .detour 0x793000/raw 0x497000 (**VA != raw**).
The naive `va-ImageBase` shortcut would be wrong for .rsrc/.detour; it happens to be right for
.text/.rdata/.data, and all RTTI lives in .rdata/.data, so both give the same answer here - but the
script never uses the shortcut.

Coverage: every byte of .text (0x3E0000), .rdata (0x31000 raw), .data (0x6C000 raw) was scanned as
raw file bytes; the 24.1 MB figure counts dword-width reads including repeats, the file itself is
4,825,360 bytes and only those 3 sections' raw ranges plus the PE header are touched.

## 6) What each fact must become

* F01 -> "COL is 5 dwords; the record preceding a COL is {0,0,smallInt,ptr} for 855/1211 COLs; its
  final dword is 0 on 91 primary COLs and some .rdata address otherwise; **no COL has a self field,
  and no value equals COL-0x10**."
* F31 -> keep the prohibition, replace the reason: "COL has no pSelf field (5-dword layout); never
  test a vtable start by pSelf self-reference. Use signature==0 + offset<0x1000 + pTD->TD name."
