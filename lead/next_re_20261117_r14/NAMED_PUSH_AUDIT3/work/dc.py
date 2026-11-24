import struct
from core import *

blob = DATA[0x1000:0x1000 + 0x3E0000]

def scan(op, tgt, label):
    hits = []
    i = blob.find(op)
    while i != -1:
        if i + 5 <= len(blob):
            rel = struct.unpack("<i", blob[i + 1:i + 5])[0]
            if 0x401000 + i + 5 + rel == tgt:
                hits.append(0x401000 + i)
        i = blob.find(op, i + 1)
    print("%-22s -> %08X : %d 处 %s" % (label, tgt, len(hits), " ".join("%08X" % h for h in hits)))
    return hits

scan(b"\xE8", 0x00748190, "call rel32 to entry")
scan(b"\xE9", 0x00748190, "jmp rel32 to entry")
scan(b"\x0F\x84", 0x00748190, "jz rel32 to entry")

# also: is there any 6A/50 style push of 00748190 as data (e.g., vtable rebuild)?
pat = struct.pack("<I", 0x00748190)
hits = []
i = blob.find(pat)
while i != -1:
    hits.append(0x401000 + i)
    i = blob.find(pat, i + 1)
print("imm32 00748190 anywhere in .text: %d 处 %s" % (len(hits), " ".join("%08X" % h for h in hits)))
