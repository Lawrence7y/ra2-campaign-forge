"""W176 Task 1: function ownership of all [+0x81] sites via atlas interval containment.

Channel A (EVIDENCE/T1_byte81_all.json) is atlas-independent.  This script uses
function_atlas.tsv ONLY for function-interval ownership labeling (discipline 17:
interval containment, not entry_at_or_before), and disassembles key functions.
"""
import json, os, bisect, capstone, pefile

ROOT = r"D:\Project\ra2-campaign-forge"
OUT = os.path.join(ROOT, r"lead\next_re_20261117_r14\W176_place81\EVIDENCE")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")


def load_atlas():
    rows = []
    with open(ATLAS, "r", encoding="utf-8", errors="replace") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            p = line.rstrip("\n").split("\t")
            if not p or not p[0]:
                continue
            try:
                e = int(p[0], 16)
            except ValueError:
                continue
            rec = dict(zip(hdr, p))
            rows.append((e, rec))
    rows.sort(key=lambda x: x[0])
    return rows, hdr


def contain(rows, va):
    """Function interval containment; returns (entry,size,rec) or None."""
    entries = [r[0] for r in rows]
    i = bisect.bisect_right(entries, va) - 1
    if i >= 0:
        e, rec = rows[i]
        try:
            sz = int(rec.get("size", "0"))
        except ValueError:
            sz = 0
        if e <= va < e + sz:
            return (e, sz, rec)
    return None


def md():
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = True
    return m


def read_va(pe, va, n):
    ib = pe.OPTIONAL_HEADER.ImageBase
    for s in pe.sections:
        v = ib + s.VirtualAddress
        if v <= va and va+n <= v + s.SizeOfRawData:
            off = s.PointerToRawData + (va-v)
            return pe.__data__[off:off+n]
    raise ValueError(hex(va))


def disasm(pe, start, nbytes):
    m = md()
    out = []
    for ins in m.disasm(read_va(pe, start, nbytes), start):
        if ins.id != 0:
            out.append(ins)
    return out


def main():
    rows, hdr = load_atlas()
    pe = pefile.PE(EXE, fast_load=True)
    A = json.load(open(os.path.join(OUT, "T1_byte81_all.json"), encoding="utf-8"))["hits"]
    # stats by function containment
    byfn = {}
    for h in A:
        fn = contain(rows, h["va"])
        key = "%08X" % fn[0] if fn else "NO_CONTAIN"
        byfn.setdefault(key, []).append(h)
    lines = []
    lines.append("W176 T1 · function-interval ownership of [+0x81] sites")
    lines.append("total sites=%d, functions with >=1 site=%d" % (len(A), len(byfn)))
    lines.append("ownership via atlas interval containment (entry<=site<entry+size); channel A is atlas-independent")
    lines.append("")
    for key in sorted(byfn):
        hs = byfn[key]
        w = sum(1 for h in hs if h["write"])
        r = sum(1 for h in hs if h["read"])
        fn = rows[bisect.bisect_left([x[0] for x in rows], int(key,16))] if key != "NO_CONTAIN" else None
        extra = ""
        if fn:
            extra = " size=%s n_instr=%s" % (fn[1].get("size"), fn[1].get("n_instr"))
        lines.append("fn %s%s : sites=%d write=%d read=%d" % (key, extra, len(hs), w, r))
        for h in hs:
            lines.append("    %08X %-58s base=%-5s %s" %
                         (h["va"], h["text"], h["base"], "W" if h["write"] else "R"))
        lines.append("")
    with open(os.path.join(OUT, "T1_byte81_by_function.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines)+"\n")

    # key functions full disasm
    targets = {
        0x43F180: ("BuildingClass slot73 dispatcher", 0x2000),
        0x7014A0: ("TechnoClass::SetOwner slot245", 0x1000),
        0x5F4D30: ("Limbo", 0x180),
        0x5F4EC0: ("Unlimbo", 0x180),
        0x5F5850: ("predicate +0x81/+0x74", 0x200),
        0x43CEA0: ("Building slot65 (visibility cull)", 0x400),
        0x5F4B10: ("generic slot65 (visibility cull)", 0x400),
        0x71CC50: ("Terrain slot65", 0x400),
    }
    for va, (label, nbytes) in targets.items():
        insns = disasm(pe, va, nbytes)
        fn = contain(rows, va)
        limit = va + (int(fn[1]) if fn else nbytes)
        s = []
        s.append("W176 T1 disasm: %s @ %08X (atlas %s)" %
                 (label, va, ("entry=%08X size=%s" % (fn[0], fn[1])) if fn else "no-atlas"))
        s.append("linear skipdata=True from %08X, up to %08X (atlas end)" % (va, limit))
        for ins in insns:
            if ins.address >= limit:
                break
            s.append("  %08X %-9s %s" % (ins.address, ins.mnemonic, ins.op_str))
        s.append("instructions emitted=%d" % sum(1 for i in insns if i.address < limit))
        path = os.path.join(OUT, "T1_disasm_%08X.txt" % va)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(s)+"\n")
        print("wrote", os.path.basename(path), "insns", sum(1 for i in insns if i.address < limit))


if __name__ == "__main__":
    main()
