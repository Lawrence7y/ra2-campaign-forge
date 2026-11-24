"""Focused queries for W178 anomalies: two raw-E8 false hits and 0x6CD8CD reachability."""
import os
import struct
import capstone
import pefile

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
TEXT_VA = 0x401000


def md(skipdata=True):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.skipdata = skipdata
    m.detail = True
    return m


def read_va(pe, va, n):
    ib = pe.OPTIONAL_HEADER.ImageBase
    for s in pe.sections:
        sv = ib + s.VirtualAddress
        if sv <= va and va + n <= sv + s.SizeOfRawData:
            off = s.PointerToRawData + (va - sv)
            return pe.__data__[off:off + n]
    raise ValueError(hex(va))


def text(ins):
    return f"{ins.address:08X}  {ins.bytes.hex(' '):<24}  {ins.mnemonic} {ins.op_str}".rstrip()


def main():
    pe = pefile.PE(EXE, fast_load=True)
    s = next(x for x in pe.sections if x.Name.decode().rstrip('\x00') == '.text')
    data = pe.__data__[s.PointerToRawData:s.PointerToRawData + s.SizeOfRawData]
    targets = {0x6D15CB, 0x6D1605, 0x6CD8CD}
    covering = {}
    nearby = []
    m = md()
    for ins in m.disasm(data, TEXT_VA):
        if ins.id == 0:
            continue
        for t in targets:
            if ins.address <= t < ins.address + ins.size:
                covering[t] = text(ins)
        if 0x6D1580 <= ins.address <= 0x6D1660 or 0x6CD890 <= ins.address <= 0x6CD8F0:
            nearby.append(text(ins))
    print("COVERING")
    for t in sorted(targets):
        print(f"  {t:#x}: {covering.get(t, 'NOT COVERED')}")
    print("NEARBY")
    for x in nearby:
        print("  " + x)

    print("RAW BYTES")
    for t in sorted(targets):
        print(f"  {t:#x}: {read_va(pe, t, 16).hex(' ')}")

    print("FROM CANDIDATE ENTRIES")
    for entry in (0x6D14F0, 0x6D15F0, 0x6D1610, 0x6CC390):
        try:
            ins = list(m.disasm(read_va(pe, entry, 0x2000), entry))
            by = {i.address: k for k, i in enumerate(ins) if i.id}
            for t in targets:
                if t in by:
                    k = by[t]
                    print(f"  entry={entry:#x} target={t:#x} idx={k}")
                    for j in range(max(0, k - 6), min(len(ins), k + 3)):
                        if ins[j].id:
                            print("    " + (">> " if ins[j].address == t else "   ") + text(ins[j]))
                else:
                    print(f"  entry={entry:#x} target={t:#x} NOT_IN_LINEAR_FROM_ENTRY")
        except Exception as e:
            print(f"  entry={entry:#x} ERR {e}")


if __name__ == "__main__":
    main()
