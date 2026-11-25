#!/usr/bin/env python3
# Task B: byte-body comparison + exact-string census + negative control.
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

text = [s for s in secs if s["name"] == ".text"][0]
TEXT_VA = IMGBASE + text["vaddr"]
blob = data[text["rawptr"]:text["rawptr"]+text["rawsize"]]
print(f".text VA={TEXT_VA:#x} len={len(blob)}")

N = 106
A_VA, B_VA = 0x6bedb0, 0x41c250
A = data[va2off(A_VA): va2off(A_VA)+N]
B = data[va2off(B_VA): va2off(B_VA)+N]
print("A_off", hex(va2off(A_VA)), "B_off", hex(va2off(B_VA)))
print("A hex:", A.hex())
print("B hex:", B.hex())

diffs = [(i, A[i], B[i]) for i in range(N) if A[i] != B[i]]
print("diff_count", len(diffs))
for i, a, b in diffs:
    print(f"  offset {i:#04x}  A={a:#04x}  B={b:#04x}")

# ---- exact-substring census of A across .text ----
def find_all(hay, needle):
    out, start = [], 0
    while True:
        j = hay.find(needle, start)
        if j < 0:
            return out
        out.append(j)
        start = j + 1

hits = find_all(blob, A)
print("bodyA_hit_count", len(hits))
for h in hits:
    print(f"  hit_va {TEXT_VA + h:#x}  off {text['rawptr'] + h:#x}")

# also: where do these hits sit relative to A_VA / B_VA?
print("A_VA", hex(A_VA), "B_VA", hex(B_VA))
print("hits_equal_A_VA", [hex(TEXT_VA+h) == hex(A_VA) for h in hits])

# ---- negative control: flip a middle byte of A to 0xff ----
mid = N // 2
A2 = bytearray(A)
old = A2[mid]
A2[mid] = 0xFF
print(f"negative_control: A[{mid}] {old:#04x} -> 0xff; changed_body==original? {bytes(A2)==A}")
hits2 = find_all(blob, bytes(A2))
print("bodyA_flipped_hit_count", len(hits2), [hex(TEXT_VA+h) for h in hits2])

# extra control: same flip at several other offsets, to rule out a lucky byte
for off in (0, 1, 26, 52, 79, 105):
    A3 = bytearray(A); prev = A3[off]
    A3[off] = 0xFF if prev != 0xFF else 0x00
    n = len(find_all(blob, bytes(A3)))
    print(f"  control flip offset {off} ({prev:#04x}->{A3[off]:#04x}) hits={n}")

# body B census too (informational, same method)
hitsB = find_all(blob, B)
print("bodyB_hit_count", len(hitsB), [hex(TEXT_VA+h) for h in hitsB])
