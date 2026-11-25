#!/usr/bin/env python3
# Task C: two GUID constants, their sections, and imm32 occurrences in .text.
import struct

PATH = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
IMGBASE = 0x400000
data = open(PATH, "rb").read()
u16 = lambda o: struct.unpack_from("<H", data, o)[0]
u32 = lambda o: struct.unpack_from("<I", data, o)[0]

e_lfanew = u32(0x3C); coff = e_lfanew + 4
nsec = u16(coff + 2); optsz = u16(coff + 16); opt = coff + 20
sectab = opt + optsz
secs = []
for i in range(nsec):
    o = sectab + i * 40
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o+8)
    secs.append(dict(name=data[o:o+8].rstrip(b"\0").decode("latin1"),
                     vsize=vsize, vaddr=vaddr, rawsize=rawsize, rawptr=rawptr))

def va2off(va):
    for s in secs:
        base = IMGBASE + s["vaddr"]
        if base <= va < base + s["rawsize"]:
            return s["rawptr"] + (va - base)
    return None

def sec_of(va):
    for s in secs:
        base = IMGBASE + s["vaddr"]
        if base <= va < base + max(s["vsize"], s["rawsize"]):
            return s["name"], base, base + s["vsize"]
    return None, None, None

def guid_str(va):
    b = data[va2off(va): va2off(va)+16]
    d1 = struct.unpack_from("<I", b, 0)[0]
    d2 = struct.unpack_from("<H", b, 4)[0]
    d3 = struct.unpack_from("<H", b, 6)[0]
    d4 = b[8:16]                       # Data4 is a byte array, printed as-is
    s = "{%08X-%04X-%04X-%02X%02X-%s}" % (
        d1, d2, d3, d4[0], d4[1], "".join("%02X" % x for x in d4[2:8]))
    return b, s, (d1, d2, d3, list(d4))

for va in (0x817bb0, 0x817bc0):
    b, s, parts = guid_str(va)
    name, lo, hi = sec_of(va)
    print(f"VA {va:#010x}  off {va2off(va):#010x}  bytes {b.hex()}")
    print(f"   Data1/2/3 = {parts[0]:#010x} / {parts[1]:#06x} / {parts[2]:#06x}  Data4 = {bytes(parts[3]).hex()}")
    print(f"   GUID = {s}")
    print(f"   section = {name}  (range {lo:#x}..{hi:#x})")
    # full 16 bytes also as raw little-endian words, for cross-check
    print(f"   raw 4 dwords LE: {[hex(x) for x in struct.unpack_from('<4I', b, 0)]}")

print()
print("section list for reference:")
for s in secs:
    print(f"  {s['name']:8s} {IMGBASE+s['vaddr']:#010x} .. {IMGBASE+s['vaddr']+s['vsize']:#010x}  (rawsize {s['rawsize']:#x})")

# ---- imm32 search: 0x817bc0 as little-endian 4-byte constant inside .text ----
text = [s for s in secs if s["name"] == ".text"][0]
TEXT_VA = IMGBASE + text["vaddr"]
blob = data[text["rawptr"]:text["rawptr"]+text["rawsize"]]

for val, label in ((0x817bc0, "0x817bc0"), (0x817bb0, "0x817bb0")):
    pat = struct.pack("<I", val)
    hits, start = [], 0
    while True:
        j = blob.find(pat, start)
        if j < 0:
            break
        hits.append(TEXT_VA + j)
        start = j + 1
    print(f"\nimm32 {label} in .text: count={len(hits)}")
    for h in hits:
        print(f"   at {h:#x}")
