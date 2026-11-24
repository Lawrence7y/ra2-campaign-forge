import struct
from core import *

blob = DATA[0x1000:0x1000 + 0x3E0000]

def callers(tgt, label):
    hits = []
    i = blob.find(b"\xE8")
    while i != -1:
        if i + 5 <= len(blob):
            rel = struct.unpack("<i", blob[i + 1:i + 5])[0]
            if 0x401000 + i + 5 + rel == tgt:
                hits.append(0x401000 + i)
        i = blob.find(b"\xE8", i + 1)
    print("%s %08X direct callers: %d  %s" % (label, tgt, len(hits), " ".join("%08X" % h for h in hits[:12])))
    return hits

callers(0x007470D0, "big ctor")
callers(0x007472C0, "small ctor")
callers(0x00748190, "ENTRY(dtor)")
callers(0x007472F0, "dup dtor")

print()
print("=== context around 00747210..00747230 (container add path in big ctor) ===")
for l in dis_lines(0x00747203, 0x00747240):
    print(l)
print()
print("=== who calls big ctor (first 3 contexts) ===")
for c in callers(0x007470D0, "big ctor")[:3]:
    print("--- caller site %08X ---" % c)
    for l in dis_lines(c - 0x30, c + 0x30):
        print(l)
    print()
