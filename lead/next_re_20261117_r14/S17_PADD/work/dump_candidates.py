"""Dump disassembly + holder/RTTI context for S17-PADD candidate entries."""
import sys
import re_lib as R

CANDS = {
    # Line C candidate: [已证] with [未证] semantics
    "006CF240": ("Here_I_Am (SwizzleManagerClass slot4) - LINE C", 0x006CF240, 0x90),
    # Line A candidates: sub_ rows
    "004068E0": ("sub_004068E0", 0x004068E0, 0x40),
    "0040E340": ("sub_0040E340", 0x0040E340, 0x80),
    "00427940": ("sub_00427940", 0x00427940, 0x80),
    "0042E410": ("sub_0042E410", 0x0042E410, 0x80),
    "00433CF0": ("sub_00433CF0", 0x00433CF0, 0x80),
    "0049F740": ("sub_0049F740", 0x0049F740, 0x40),
    "0049F8B0": ("sub_0049F8B0", 0x0049F8B0, 0x40),
    "00773450": ("sub_00773450", 0x00773450, 0x80),
    # Line B candidates: [静态推断] rows with rich bodies
    "00539AE0": ("Load_StreamFields", 0x00539AE0, 0x40),
    "0055AAC0": ("Load_SwizzledObject", 0x0055AAC0, 0x40),
    "004355B0": ("ColorStruct::ColorStruct", 0x004355B0, 0x30),
    "0043AE50": ("MemoryBuffer::Clear", 0x0043AE50, 0x40),
}

only = sys.argv[1] if len(sys.argv) > 1 else None
for key, (label, va, n) in CANDS.items():
    if only and key != only:
        continue
    print("=" * 100)
    print(f"[{key}] {label} @ 0x{va:08X}  (off=0x{R.va_to_off(va):X})")
    b = R.read_bytes(va, n)
    print("bytes:", b.hex() if b else None)
    print("--- disasm ---")
    for a, mn, op, sz, bh in R.disasm(va, n):
        print(f"  {a:08X}  {bh:<20} {mn:<8} {op}")
    holders = R.holder_scan(va)
    print("holder dwords (whole file):", [hex(h) for h in holders])
