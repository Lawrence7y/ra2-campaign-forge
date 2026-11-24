"""S9: reverse vtable lookup for the latch / veto writers and the predicate.

For every one of the 1,214 canonical vtables, read its slot array from the file
and report which (class, slot, offset) points at a watched function.  This turns
anonymous functions into "BuildingClass slot N (offset 0x...)" statements.

Run: python s9_slots.py > ..\\EVIDENCE\\s9_slots.log 2>&1
"""
import json
import w152_core as C

ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json"

WATCH = {
    0x005F5850: "occupancy predicate (latch gate)",
    0x005F4D10: "sets +0x80=1",
    0x005F4D30: "sets +0x81=1, +0x80=0",
    0x005F4EC0: "toggles +0x81/+0x80",
    0x005FC570: "sets +0x74=0 AND +0x81=1  <-- hard-veto + unplace",
    0x005F3900: "clears/sets +0x81,+0x74,+0x80 (reset)",
    0x00543780: "clears +0x81",
    0x00543A10: "clears +0x81",
    0x00543A40: "sets +0x81=1, +0x80=0",
    0x00543B10: "sets +0x81=1, +0x80=0",
    0x00581140: "clears +0x81, sets +0x74=1",
    0x005F5B90: "slot 0x108 coord-list getter",
    0x0045EC20: "type slot 0x90 footprint getter",
    0x005683C0: "attach wrapper",
    0x005687F0: "detach wrapper",
    0x0047E8A0: "CellClass::AddObject",
    0x0047EA90: "CellClass::RemoveObject",
    0x0043F180: "BuildingClass slot73 dispatcher",
    0x004D3780: "mobile slot73 dispatcher",
    0x0071BFB0: "Terrain slot73 dispatcher",
    0x0040DD70: "called from the predicate",
    0x0041BEA0: "anchor getter (slot 0x1B8)",
}

KNOWN_CONST = {0x404E0000, 0xA2529D39, 0x3F91DF46}


def slots_of(vt):
    out = []
    for i in range(400):
        try:
            v = C.u32(vt + 4 * i)
        except Exception:
            break
        if v in KNOWN_CONST or v == 0:
            break
        nm, _, _, _ = C.sec_of(v)
        if nm != '.text':
            break
        out.append(v)
    return out


def main():
    d = json.load(open(ATLAS, encoding='utf-8'))
    vts = d['vtables']
    index = {k: [] for k in WATCH}
    for ent in vts:
        vt = ent['vt']
        cls = ent['class']
        off = ent.get('col_offset', 0)
        for i, t in enumerate(slots_of(vt)):
            if t in index:
                index[t].append((cls, off, i, 4 * i, vt))
    print("scanned vtables = %d" % len(vts))
    print("")
    for f, label in sorted(WATCH.items()):
        appears = index[f]
        print("=== %08X  %s ===" % (f, label))
        if not appears:
            print("     (no canonical vtable slot points here)")
        for cls, off, i, boff, vt in sorted(appears, key=lambda x: (x[0], x[2]))[:24]:
            print("     %-42s colOff=%-6d slot %3d (0x%03X) vt=%08X" % (
                cls, off, i, boff, vt))
        if len(appears) > 24:
            print("     ... %d more" % (len(appears) - 24))
        print("")


main()
