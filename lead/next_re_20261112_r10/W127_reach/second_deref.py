#!/usr/bin/env python3
"""W127e: is FUN_00724580 a second unguarded dereference of [0x887368]?

The ledger's core fix for ②-a is a guard at FUN_00724730's entry (0x724730).
But FUN_006d1660 -- the function containing the real crash site -- also calls
0x724580 with the SAME global in ECX (at 0x6D174C). If 0x724580 dereferences
`this` unguarded, the single-point fix does not cover that path.

This dumps both routines from raw bytes so the first accesses are visible.
"""
import pefile
import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False


def dump(lo, hi, title):
    print("\n===== %s  0x%08X .. 0x%08X =====" % (title, lo, hi))
    for ins in md.disasm(img[lo - ib:hi - ib], lo):
        print("  %08X  %-22s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))


dump(0x00724580, 0x00724660, "FUN_00724580 (head)")
dump(0x00724730, 0x00724780, "FUN_00724730 (head, crash site)")
dump(0x00724780, 0x007248C0, "FUN_00724730 (rest)")

print("\n===== all loads of 0x887368 followed by call 0x724580 within 40 bytes =====")
TEXT_VA, TEXT_END = 0x00401000, 0x007E038D
text = img[TEXT_VA - ib:TEXT_END - ib]
pat = bytes([0x8B, 0x0D]) + (0x00887368).to_bytes(4, "little")
i = text.find(pat)
n = 0
while i != -1:
    va = TEXT_VA + i
    win = text[i + 6:i + 6 + 40]
    for k in range(len(win) - 4):
        if win[k] in (0xE8, 0xE9):
            src = TEXT_VA + i + 6 + k
            rel = int.from_bytes(win[k + 1:k + 5], "little", signed=True)
            if src + 5 + rel == 0x00724580:
                print("  load=0x%08X call=0x%08X  ctx=%s"
                      % (va, src, text[i:i + 6 + k + 5].hex(" ")))
                n += 1
                break
    i = text.find(pat, i + 1)
print("  total -> 0x724580 sites: %d" % n)
