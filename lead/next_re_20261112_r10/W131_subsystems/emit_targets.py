#!/usr/bin/env python3
"""W131c: emit the address list of undefined vtable targets for Ghidra to create."""
import bisect
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.join(os.path.dirname(HERE), "W130_atlas", "function_atlas.tsv")

ent = []
rng = {}
with io.open(ATLAS, encoding="utf-8") as f:
    f.readline()
    for ln in f:
        p = ln.rstrip("\n").split("\t")
        e = int(p[0], 16)
        ent.append(e)
        rng[e] = (e, e + int(p[1]))
ent.sort()

tg = set()
with io.open(os.path.join(HERE, "vtable_members.tsv"), encoding="utf-8") as f:
    f.readline()
    for ln in f:
        p = ln.rstrip("\n").split("\t")
        if p[4] == "1":
            tg.add(int(p[3], 16))

todo = []
for a in sorted(tg):
    if a in rng:
        continue
    i = bisect.bisect_right(ent, a) - 1
    if i >= 0 and rng[ent[i]][0] < a < rng[ent[i]][1]:
        continue          # interior: not a function entry
    todo.append(a)

out = os.path.join(HERE, "vtable_targets_undefined.txt")
with io.open(out, "w", encoding="utf-8") as f:
    f.write("# vtable slot targets with no Ghidra function; each is proof of a code entry\n")
    for a in todo:
        f.write("0x%08X\n" % a)
print("wrote %s with %d addresses" % (out, len(todo)))
