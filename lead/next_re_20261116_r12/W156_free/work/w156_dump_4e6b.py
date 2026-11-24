"""Dump raw disassembly around the 0x4E6Bxx NOFUNC write sites to [A8EB44]/[A8EB50]."""
import w156_core as C

for start, end in [(0x004E6A00, 0x004E6D00)]:
    print("="*72)
    print("RAW DISASM %08X..%08X (linear, may include data)" % (start, end))
    print("="*72)
    for ins in C.MD.disasm(C.code(start, end-start), start):
        mark = ""
        if ins.mnemonic in ('ret','retf') or ins.address in (0x004E6B67,0x004E6B91,0x004E6BC7):
            mark = "  <<<" if ins.address in (0x004E6B67,0x004E6B91,0x004E6BC7) else ""
        print("  " + C.fmt(ins) + mark)
