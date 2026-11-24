from base import u32, cstr, in_raw, blob, TEXT
rd_lo, rd_hi = 0x007E1000, 0x00811074
def is_code(v): return TEXT["va"] <= v < TEXT["va"] + TEXT["vsize"]
print("=== 0x7F1094 backward/forward context ===")
for a in range(0x7F1074, 0x7F109C, 4):
    v = u32(a)
    print("  %08X  %08X  codeptr=%s" % (a, v, is_code(v)))
print()
print("  0x7F1090 = %08X  is_code=%s" % (u32(0x7F1090), is_code(u32(0x7F1090))))
print()
print("=== 0x006922E0 indirect callers: FF /2 (call [mem]) and FF D0/FF 52 etc ===")
from base import BUF, IB, s32
tgt = 0x006922E0
# call [abs32] = FF 15 xx xx xx xx
for va in range(TEXT["va"], TEXT["va"]+TEXT["vsize"]-6):
    i = va - IB
    if BUF[i] == 0xFF and BUF[i+1] == 0x15 and u32(va+2) == tgt:
        print("  call [abs] @%08X" % va)
print("  (none printed above => no absolute indirect call to it)")
print()
print("=== .rdata 0x7EDFDC context (dword==0x6D0680) ===")
for a in range(0x7EDFC4, 0x7EDFF4, 4):
    print("  %08X  %08X" % (a, u32(a)))
print()
print("=== does 0x6D0680 appear in any run of code pointers / vtable? ===")
print("  is 0x7EDFDC inside a code-ptr run? prev=%08X next=%08X" % (u32(0x7EDFD8), u32(0x7EDFE0)))
