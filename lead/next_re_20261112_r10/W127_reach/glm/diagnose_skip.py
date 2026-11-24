# diagnose_skip.py -- inspect where/why capstone emits skipdata inside the 64B windows
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE_PATH   = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE = 0x400000

pe  = pefile.PE(EXE_PATH, fast_load=True)
img = pe.get_memory_mapped_image()

def rd(va, n):
    off = va - IMAGE_BASE
    return bytes(img[off:off + n])

md  = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True
mdn = Cs(CS_ARCH_X86, CS_MODE_32); mdn.skipdata = False

SITES = [0x48ce4c, 0x4a8b18, 0x4a8b7a, 0x4f4562, 0x55d0a0, 0x5c4bb8,
         0x5d4dbc, 0x6403a8, 0x654418, 0x683f54, 0x684010, 0x686424,
         0x6ac015, 0x6ac07f, 0x6ac0f2, 0x6ac14a, 0x6ac198,
         0x6d1298, 0x6d130d, 0x6d1383]

print("=== FUN_00724730 prologue raw bytes (0x724730, 40 bytes) ===")
print(rd(0x724730, 40).hex(" "))
print()

for v in SITES:
    raw = rd(v, 64)
    print("--- site %#x  raw64: %s" % (v, raw.hex(" ")))
    # forward decode WITH skipdata (never touch .operands)
    n_bad = 0
    stop = None
    for ins in md.disasm(raw, v):
        tag = ""
        if ins.mnemonic in (".byte", "(bad)") or not ins.mnemonic:
            tag = "   <-- SKIPDATA"
            n_bad += 1
        print("    %#x  %-20s %-8s %s%s" % (ins.address, bytes(ins.bytes).hex(" "), ins.mnemonic, ins.op_str, tag))
        if tag and n_bad >= 1 and stop is None:
            stop = ins.address
    # forward decode WITHOUT skipdata: shows the first hard failure
    cnt = 0
    last = None
    for ins in mdn.disasm(raw, v):
        cnt += 1
        last = ins
    nxt = (last.address + last.size) if last else v
    print("    [no-skipdata: %d insns, stops at %#x, byte there = %s]"
          % (cnt, nxt, rd(nxt, 8).hex(" ")))
    print()
