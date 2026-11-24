import struct
from core import *

print("=== byte-identical check 00748190 vs 007472F0 ===")
a = read(0x00748190, 0x8D)
b = read(0x007472F0, 0x8D)
print("same 0x8D bytes:", a == b, " len", len(a), len(b))

print()
print("=== .rdata pointers to 00748190 / 007472F0 ===")
for nm, sva, rva, vs, rs, rp in SECS:
    if nm not in (".rdata", ".data"):
        continue
    blob = DATA[rp:rp + rs]
    for tgt in (0x00748190, 0x007472F0):
        pat = struct.pack("<I", tgt)
        i = blob.find(pat)
        while i != -1:
            print("  %s ref to %08X at VA %08X" % (nm, tgt, sva + i))
            i = blob.find(pat, i + 1)

print()
print("=== direct call rel32 to 00748190 ===")
blob = DATA[0x1000:0x1000 + 0x3E0000]
cnt = 0
i = blob.find(b"\xE8")
while i != -1:
    if i + 5 <= len(blob):
        rel = struct.unpack("<i", blob[i + 1:i + 5])[0]
        tva = 0x401000 + i + 5 + rel
        if tva == 0x00748190:
            print("  call at %08X" % (0x401000 + i))
            cnt += 1
    i = blob.find(b"\xE8", i + 1)
print("  total direct calls:", cnt)

print()
print("=== direct call rel32 to 007472F0 ===")
cnt = 0
i = blob.find(b"\xE8")
while i != -1:
    if i + 5 <= len(blob):
        rel = struct.unpack("<i", blob[i + 1:i + 5])[0]
        tva = 0x401000 + i + 5 + rel
        if tva == 0x007472F0:
            print("  call at %08X" % (0x401000 + i))
            cnt += 1
    i = blob.find(b"\xE8", i + 1)
print("  total direct calls:", cnt)

print()
print("=== ff /2-style [reg+0x20] vtable dispatch candidates (ff 5x 20) ===")
pats = []
for modrm in range(0x50, 0x58):
    pats.append(bytes([0xFF, modrm, 0x20]))
tot = 0
hits = []
for p in pats:
    i = blob.find(p)
    while i != -1:
        hits.append(0x401000 + i)
        i = blob.find(p, i + 1)
hits.sort()
print("  total:", len(hits))
print("  first 15:", " ".join("%08X" % h for h in hits[:15]))
