from base import BUF, IB, TEXT, u32, s32, cstr
tlo = TEXT["va"]; thi = TEXT["va"] + TEXT["vsize"]
from collections import defaultdict
edges = []
for va in range(tlo, thi - 5):
    i = va - IB
    if BUF[i] in (0xE8, 0xE9):
        t = va + 5 + s32(va + 1)
        if tlo <= t < thi:
            edges.append((va, t))
print("edges in .text:", len(edges))
# which functions call the function that CONTAINS 0x4F8F82?
# find function start containing 0x4F8F82 by scanning back for prologue
def starts(limit=0x800):
    out = []
    a = 0x004F8F82
    while a > 0x004F8F82 - limit and a > tlo:
        if BUF[a-IB]==0x55 and BUF[a+1-IB]==0x8B and BUF[a+2-IB]==0xEC:
            out.append(a)
            if len(out)>=6: break
        a -= 1
    return out
print("prologue candidates before 0x4F8F82:", ["%08X"%x for x in starts()])
