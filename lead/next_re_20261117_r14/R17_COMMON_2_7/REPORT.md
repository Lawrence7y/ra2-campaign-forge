# R17-COMMON-2.7 EXECUTION REPORT

## Byte re-verification (read-only, gamemd.exe)

gamemd.exe: bytes=4825360, sha256=73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476, ImageBase=0x400000, .text=[0x401000,0x7E038D)
PE parse: .text VAddr=0x1000, RawPtr=0x1000 => file offset = VA - 0x400000.
All addresses verified by raw byte read + capstone x86-32 disassembly.
Item 2 note: an extra `89 74 24 1C` (mov [esp+0x1C],esi) exists at 0x43F50B between `cmp esi,eax` and `jl`; the four required byte patterns and their decodes are all present in order starting at 0x43F504. Recorded in byte_reverify.tsv.

PASS=6, FAIL=0

## before / after

| metric | before | after |
|---|---|---|
| bytes | 230242 | 232629 |
| mtime | 2026-11-20 23:12:37 (epoch=1795187557) | 2026-11-21 13:10:11 (epoch=1795237811) |
| sha256 | 2aa32cc23a2b3c236e2ccdd72c50878734b808250c8fabf1828bed7ae88ca36a | 6756ad050352a53483ba3391101b54fb4180ed645595d2a3fbde6d0c2e1eda07 |
| CR count | 1081 | 1081 |
| LF/line count | 1574 | 1609 |

Note on card claim: card §4.4 states the file is *bare LF*. The on-disk file actually contains 1081 pre-existing CR bytes; the operative rule (CR count unchanged, no new CR) is satisfied exactly.

## assertions

- appended bytes = 2387 (extracted byte-exact from card §3 fenced block)
- sha256(new[0:oldLen]) == sha256(old): PASS
- bytes == oldLen + appended bytes: PASS
- line-count delta == appended LF count: 35 == 35 => PASS
- CR count before/after: 1081 / 1081 => PASS
- read-back equals intended bytes: PASS
- change applied to R14_COMMON.md: YES (write performed this run: False; false = idempotent re-run)
- ALL POST-WRITE CHECKS: PASS

## Reply-mode summary

before bytes=230242 sha256[0:12]=2aa32cc23a2b | after bytes=232629 sha256[0:12]=6756ad050352 | prefix PASS=True | CR 1081->1081 | line delta=35 | reverify PASS=6 FAIL=0
