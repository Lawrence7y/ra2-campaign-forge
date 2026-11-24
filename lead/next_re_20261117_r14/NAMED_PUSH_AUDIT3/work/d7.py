import struct
from core import *

print("=== diff 00748190 vs 007472F0 ===")
a = read(0x00748190, 0x8D)
b = read(0x007472F0, 0x8D)
for i in range(0, len(a)):
    if a[i] != b[i]:
        print("  diff at %08X (offset %d): %02X vs %02X" % (0x00748190 + i, i, a[i], b[i]))
print()

print("=== writers/readers of container globals 0xA83CE0 (vt) / 0xA83CE4 (array) / 0xA83CE8 / 0xA83CF0 (count) ===")
blob = DATA[0x1000:0x1000 + 0x3E0000]
for name, gva in (("0xA83CE0", 0xA83CE0), ("0xA83CE4", 0xA83CE4), ("0xA83CE8", 0xA83CE8), ("0xA83CF0", 0xA83CF0)):
    pat = struct.pack("<I", gva)
    hits = []
    i = blob.find(pat)
    while i != -1:
        hits.append(0x401000 + i)
        i = blob.find(pat, i + 1)
    print("  %s referenced %d times: %s" % (name, len(hits), " ".join("%08X" % h for h in hits[:20])))
print()

print("=== disasm 00748010 .. 007480F0 (slot5 host) ===")
for l in dis_lines(0x00748010, 0x007480F0):
    print(l)
