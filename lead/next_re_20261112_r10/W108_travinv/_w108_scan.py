"""W108 step5: independent raw-byte scan of gamemd.exe .text for call rel32 / jmp rel32
targets among the traversers and the unlink function. No Ghidra, no capstone —
pure PE parsing + byte arithmetic, so the numbers are reproducible standalone.

Usage: python _w108_scan.py > EVIDENCE/step5_rawscan.txt
"""
import struct
import sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

TARGETS = {
    0x0047C520: "TRAV_find6_chainA",
    0x0047C4D0: "TRAV_findWanted_argchain",
    0x0047C550: "TRAV_find0x24_chainAB",
    0x0047EA90: "UNLINK_node",
}


def load_pe(path):
    data = open(path, "rb").read()
    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[pe_off:pe_off + 4] == b"PE\0\0", "not PE"
    nsec = struct.unpack_from("<H", data, pe_off + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe_off + 0x14)[0]
    opt_off = pe_off + 0x18
    magic = struct.unpack_from("<H", data, opt_off)[0]
    image_base = struct.unpack_from("<I", data, opt_off + 0x1C)[0]
    sec_tab = opt_off + opt_size
    secs = []
    for i in range(nsec):
        o = sec_tab + i * 40
        name = data[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, va, rsize, rptr = struct.unpack_from("<IIII", data, o + 8)
        secs.append(dict(name=name, va=va, vsize=vsize, rsize=rsize, rptr=rptr))
    return data, image_base, secs, magic


def main():
    data, image_base, secs, magic = load_pe(EXE)
    print("PE magic=0x%X  ImageBase=0x%08X  filesize=0x%X" % (magic, image_base, len(data)))
    for s in secs:
        print("  %-8s VA=0x%08X VSize=0x%-7X RPtr=0x%-7X RSize=0x%X"
              % (s["name"], image_base + s["va"], s["vsize"], s["rptr"], s["rsize"]))

    text = next(s for s in secs if s["name"] == ".text")
    # Clamp to what is actually present in the file.
    n = min(text["rsize"], len(data) - text["rptr"], text["vsize"])
    base_va = image_base + text["va"]
    rp = text["rptr"]
    print("\n.text covered: VA 0x%08X .. 0x%08X  (%d bytes)" % (base_va, base_va + n, n))

    calls = {t: [] for t in TARGETS}
    jmps = {t: [] for t in TARGETS}
    for i in range(n - 5):
        op = data[rp + i]
        if op not in (0xE8, 0xE9):
            continue
        rel = struct.unpack_from("<i", data, rp + i + 1)[0]
        insn_va = base_va + i
        tgt = insn_va + 5 + rel
        if tgt in TARGETS:
            (calls if op == 0xE8 else jmps)[tgt].append(insn_va)

    print("\n=== call rel32 (E8) counts ===")
    total = 0
    for t, label in TARGETS.items():
        lst = calls[t]
        total += len(lst)
        print("0x%08X  %-24s  %d" % (t, label, len(lst)))
    print("TOTAL E8 call sites to the 4 targets = %d" % total)

    print("\n=== jmp rel32 (E9) counts (tail-calls / thunks) ===")
    for t, label in TARGETS.items():
        print("0x%08X  %-24s  %d  %s" % (t, label, len(jmps[t]),
                                         " ".join("0x%08X" % a for a in jmps[t][:20])))

    print("\n=== detail: UNLINK 0x0047EA90 call/jmp sites ===")
    for a in calls[0x0047EA90]:
        print("  E8 call @ 0x%08X" % a)
    for a in jmps[0x0047EA90]:
        print("  E9 jmp  @ 0x%08X" % a)

    # address-of / literal occurrences of the 4 target VAs anywhere in file
    print("\n=== literal dword occurrences (address-taken / stored as data) ===")
    for t, label in TARGETS.items():
        pat = struct.pack("<I", t)
        hits = []
        idx = data.find(pat)
        while idx >= 0 and len(hits) < 20:
            hits.append(idx)
            idx = data.find(pat, idx + 1)
        print("0x%08X  %-24s  %d%s" % (t, label, len(hits),
              ("  first@" + " ".join("file0x%X" % h for h in hits[:6])) if hits else ""))


if __name__ == "__main__":
    main()

