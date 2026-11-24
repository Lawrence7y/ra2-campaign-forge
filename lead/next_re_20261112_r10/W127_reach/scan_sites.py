#!/usr/bin/env python3
"""W127a: independent re-verification of the `mov ecx,[0x887368] + call FUN_00724730`
no-check pattern (ledger §821). Cross-check against §821-2 table.

Pure capstone byte scan; no reliance on prior tooling.
"""
import pefile
import capstone
import sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
GLOBAL = 0x00887368
TARGET = 0x00724730
PATTERN = bytes([0x8B, 0x0D]) + GLOBAL.to_bytes(4, "little")  # mov ecx,[0x887368]

pe = pefile.PE(EXE, fast_load=True)
imgbase = pe.OPTIONAL_HEADER.ImageBase
secs = []
for s in pe.sections:
    name = s.Name.rstrip(b"\x00").decode(errors="replace")
    secs.append((name, imgbase + s.VirtualAddress, s.Misc_VirtualSize,
                 s.PointerToRawData, s.SizeOfRawData))
    print(f"section {name:8s} VA=0x{imgbase + s.VirtualAddress:08X} "
          f"vsize=0x{s.Misc_VirtualSize:X} raw=0x{s.SizeOfRawData:X} @0x{s.PointerToRawData:X}")

text = next(s for s in secs if s[0] == ".text")
_, tva, tvsize, traw, trawsize = text
data = pe.get_memory_mapped_image()
tstart, tend = tva, tva + tvsize
# NOTE: get_memory_mapped_image() is indexed from 0 == ImageBase, NOT from absolute VA.
tbytes = data[tstart - imgbase:tend - imgbase]

print(f"\n.text VA 0x{tstart:08X}..0x{tend:08X}  ({len(tbytes)} bytes)")

# ---- 1. all loads of the global
loads = []
i = tbytes.find(PATTERN)
while i != -1:
    loads.append(tstart + i)
    i = tbytes.find(PATTERN, i + 1)
print(f"\n[1] 'mov ecx,[0x{GLOBAL:08X}]' occurrences: {len(loads)}")

# ---- 2. which loads are followed (within 24 bytes of insn end) by call/jmp to TARGET
matched = []
for va in loads:
    off = va - tstart
    end = off + len(PATTERN)
    win = tbytes[end:end + 24]
    call_at = None
    target_hit = None
    for k in range(len(win) - 4):
        op = win[k]
        if op not in (0xE8, 0xE9):
            continue
        rel = int.from_bytes(win[k + 1:k + 5], "little", signed=True)
        src = tstart + end + k
        dst = src + 5 + rel
        if dst == TARGET:
            call_at = src
            target_hit = op
            break
    if call_at:
        matched.append((va, call_at, target_hit))

print(f"[2] loads whose next 24B contain {'E8/E9'} -> 0x{TARGET:08X}: {len(matched)}")
for n, (va, ca, op) in enumerate(matched, 1):
    print(f"   #{n:<2d} load=0x{va:08X} call=0x{ca:08X} op={'E8 call' if op == 0xE8 else 'E9 jmp'}  delta={ca - va}")

# ---- 3. cross-check vs ledger §821-2 table
LEDGER = [
    (0x00654405, 0x00654413), (0x006ABFF4, 0x006AC00B), (0x006AC031, 0x006AC03E),
    (0x006D0613, 0x006D0619), (0x006D0629, 0x006D0634), (0x006D0659, 0x006D0664),
    (0x006D0896, 0x006D089D), (0x006D08A8, 0x006D08B3), (0x006D0935, 0x006D0940),
    (0x006D09EC, 0x006D09FA), (0x006D127C, 0x006D1293), (0x006D12F1, 0x006D1308),
    (0x006D1367, 0x006D137E), (0x006D13DC, 0x006D13F3), (0x006D153A, 0x006D1541),
    (0x006D1551, 0x006D155C), (0x006D15FA, 0x006D1605), (0x006D1627, 0x006D1632),
    (0x006D16BB, 0x006D16C2), (0x006D16D2, 0x006D16DD),
]
mine = [(va, ca) for va, ca, _ in matched]
ok = 0
for i, (l, m) in enumerate(zip(LEDGER, mine), 1):
    same = (l == m)
    ok += same
    if not same:
        print(f"   MISMATCH #{i}: ledger=(0x{l[0]:08X},0x{l[1]:08X}) mine=(0x{m[0]:08X},0x{m[1]:08X})")
print(f"\n[3] cross-check vs ledger §821-2: {ok}/{len(LEDGER)} identical, "
      f"mine={len(mine)} ledger={len(LEDGER)}")

# ---- 4. confirm each load is NOT null-guarded: show preceding 12 bytes
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False
print("\n[4] context before each load (12 bytes) — looking for test/cmp on ecx")
for n, (va, ca, op) in enumerate(matched, 1):
    off = va - tstart
    ctx = tbytes[max(0, off - 12):off + 6]
    base = va - (va - tstart - max(0, off - 12))
    start_va = va - 12 if off >= 12 else tstart
    txt = " | ".join(f"{ins.mnemonic} {ins.op_str}" for ins in md.disasm(ctx, start_va))
    print(f"   #{n:<2d} 0x{va:08X}: {txt}")
