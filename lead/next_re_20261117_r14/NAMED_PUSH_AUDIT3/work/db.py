from core import *

# locate host function start of 006C2824..006C287D by scanning back for padding
raw = read(0x006C27A0, 0x100)
print("=== bytes 006C27A0..006C28A0 ===")
for off in range(0, len(raw), 16):
    print("%08X  %s" % (0x006C27A0 + off, raw[off:off + 16].hex(" ")))
print()
print("=== disasm 006C27D0..006C28A0 ===")
for l in dis_lines(0x006C27D0, 0x006C28A0):
    print(l)
print()

# instruction count of entry
n = 0
end = None
for i in dis(0x00748190, 0x200):
    n += 1
    end = i.address + i.size
    if i.mnemonic == "ret":
        break
print("entry 00748190: %d instructions, body [%08X,%08X) = %d bytes" % (n, 0x00748190, end, end - 0x00748190))
print()

print("=== reference to 006C2824 host: who references it? ===")
import struct
blob = DATA[0x1000:0x1000 + 0x3E0000]
pat = struct.pack("<I", 0x006C2824)
i = blob.find(pat)
while i != -1:
    print("  imm ref at %08X" % (0x401000 + i))
    i = blob.find(pat, i + 1)
for sect in (".rdata", ".data"):
    pass
print()
print("=== read slot-5 host 00748010 prologue check: is 7162F0 a 'load' helper? first insn of 00748010 shown earlier ===")
