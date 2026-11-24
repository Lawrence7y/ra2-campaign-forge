#!/usr/bin/env python3
"""W131h: build the (class, method) input list for FieldLayout.java.

Picks, per class, up to N LARGEST methods from the PRIMARY vtable (bigger methods
touch more fields), so the field census is cheap but representative.
"""
import collections
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.join(os.path.dirname(HERE), "W130_atlas")

WANT = {
    ".?AVTechnoClass@@": 60,
    ".?AVObjectClass@@": 60,
    ".?AVBuildingClass@@": 50,
    ".?AVGadgetClass@@": 32,
    ".?AVCCToolTip@@": 6,
    ".?AVINIClass@@": 40,      # also pulls non-primary below
    ".?AVConnectionClass@@": 10,
    ".?AVCellClass@@": 24,
    ".?AVMapClass@@": 29,
    ".?AVLocomotionClass@@": 10,
    ".?AVBSurface@@": 35,
    ".?AVHouseClass@@": 23,
    ".?AVAbstractClass@@": 23,
    ".?AVCCINIClass@@": 40,
    ".?AVWaveClass@@": 40,
}


def main():
    size = {}
    with io.open(os.path.join(ATLAS, "function_atlas.tsv"), encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            p = line.rstrip("\n").split("\t")
            d = dict(zip(hdr, p))
            size[int(d["entry"], 16)] = int(d["size"])

    canon = {}
    for r in json.load(open(os.path.join(ATLAS, "vtables_canonical.json"),
                            encoding="utf-8"))["vtables"]:
        vt = r["vt"] if isinstance(r["vt"], int) else int(r["vt"], 16)
        canon[vt] = (r["class"], r.get("col_offset"))

    # any vtable of the class (not just primary) -- many classes keep their real
    # methods on the primary, but INIClass etc. spread them
    by_class = collections.defaultdict(set)
    with io.open(os.path.join(HERE, "vtable_members.tsv"), encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            if p[4] != "1":
                continue
            by_class[p[1]].add(int(p[3], 16))

    out = []
    for cls, cap in WANT.items():
        fns = sorted(by_class.get(cls, ()), key=lambda e: -size.get(e, 0))
        pick = [e for e in fns[:cap] if size.get(e, 0) >= 16]
        print("%-28s candidates=%-4d picked=%d" % (cls, len(fns), len(pick)))
        for e in pick:
            out.append((cls, e))

    path = os.path.join(HERE, "fieldlayout_in.txt")
    with io.open(path, "w", encoding="utf-8") as f:
        f.write("# class\thex_entry\n")
        for cls, e in out:
            f.write("%s\t%08x\n" % (cls, e))
    print("\nwrote %s with %d (class,fn) pairs" % (path, len(out)))


if __name__ == "__main__":
    main()
