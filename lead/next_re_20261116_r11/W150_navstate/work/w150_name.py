#!/usr/bin/env python3
"""W150: resolve a list of VAs to (containing function, size, subsystem, strings).

Pure table join against the milestone artifacts -- no Ghidra run needed:
  W130_atlas\\function_atlas.tsv          (entry,size,n_instr,n_callers,n_callees,
                                          is_fnptr,first_import,n_strings,strings)
  W131_subsystems\\fn_subsystem_canonical.tsv (entry,size,subsystem,tier,n_callers)

Usage:  python w150_name.py 0x52d9a0 0x5ef720 ...
        (no args -> built-in default list)
Prints one block per VA plus a compact one-line form.
"""
import sys
import os

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10"
ATLAS = os.path.join(ROOT, "W130_atlas", "function_atlas.tsv")
SUBS = os.path.join(ROOT, "W131_subsystems", "fn_subsystem_canonical.tsv")


def load_atlas():
    rows = {}
    with open(ATLAS, "r", encoding="latin-1") as f:
        hdr = f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 9:
                continue
            try:
                entry = int(p[0], 16)
                size = int(p[1])
            except ValueError:
                continue
            rows[entry] = {
                "entry": entry, "size": size, "n_instr": p[2], "n_callers": p[3],
                "n_callees": p[4], "is_fnptr": p[5], "first_import": p[6],
                "n_strings": p[7], "strings": p[8] if len(p) > 8 else "",
            }
    return rows


def load_subs():
    rows = {}
    with open(SUBS, "r", encoding="latin-1") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 4:
                continue
            try:
                entry = int(p[0], 16)
            except ValueError:
                continue
            rows[entry] = {"subsystem": p[2], "tier": p[3], "n_callers": p[4] if len(p) > 4 else ""}
    return rows


def containing(atlas, va):
    """Largest function with entry <= va < entry+size."""
    best = None
    for e, r in atlas.items():
        if e <= va < e + r["size"]:
            if best is None or r["size"] < atlas[best]["size"]:
                best = e
    return best


DEFAULT = [
    # mode-selector writers / dispatchers
    0x52D9A0, 0x48CCC0, 0x647260, 0x6475F0, 0x5EF720, 0x5EFDC3, 0x67E440, 0x77B2A0,
    # init state-machine callees
    0x531CC0, 0x5F1950, 0x5F19C0, 0x5B77E0, 0x5B49B0, 0x6AE2C0, 0x6980C0, 0x55FC80,
    0x60D380, 0x53F1F0, 0x5F0070, 0x5DA720, 0x699450, 0x6C87F0, 0x697B70,
    0x540C60, 0x540D10, 0x5424C0, 0x5D3490, 0x5FAD10, 0x5BED40, 0x5DA720,
    # frame chain
    0x55D360, 0x55CFD0, 0x48C8B0, 0x69BAB0, 0x64C380, 0x54F000, 0x54F050,
    # scenario / map
    0x683AB0, 0x684620, 0x686B20, 0x687F10, 0x689E90, 0x6851F0, 0x6BEB7D,
    # screen stack
    0x5113F0, 0x512760, 0x5117D0, 0x512680, 0x4C6CB0, 0x5B4EE0, 0x5B82F0, 0x5B5AD0,
    0x5C23B0, 0x5C34F0, 0x5C35F0, 0x599650, 0x5ADF20, 0x5AE220, 0x650A90, 0x672440,
    0x727240, 0x4E3A00, 0x5009B0, 0x475540, 0x475610, 0x49D9F0,
    # misc pointers
    0x887048, 0x887640, 0x887628,
]


def main(argv):
    atlas = load_atlas()
    subs = load_subs()
    targets = DEFAULT
    if len(argv) > 1:
        targets = [int(a, 16) for a in argv[1:]]
    print("# atlas entries=%d  subsystem entries=%d" % (len(atlas), len(subs)))
    print("#")
    print("#VA\tfnEntry\tfnSize\tsubsystem\tncallers\tfirstImport\tSTRINGS")
    for va in targets:
        fe = containing(atlas, va)
        if fe is None:
            print(f"0x{va:08X}\t-\t-\t-\t-\t-\t<no function contains this VA>")
            continue
        r = atlas[fe]
        s = subs.get(fe, {"subsystem": "-", "tier": "-"})
        strs = r["strings"].replace("\n", " ")
        print(f"0x{va:08X}\t0x{fe:08X}\t{r['size']}\t{s['subsystem']}({s['tier']})\t"
              f"{r['n_callers']}\t{r['first_import']}\t{strs}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
