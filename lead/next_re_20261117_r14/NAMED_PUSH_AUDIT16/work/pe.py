"""Independent PE + capstone harness for NAMED_PUSH_AUDIT16.
Self-written; does not import or reuse NAMED_PUSH_S13_B1\_work.
"""
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGEBASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D

pe = pefile.PE(EXE, fast_load=True)
pe.parse_data_directories()
with open(EXE, "rb") as f:
    RAW = f.read()
assert pe.OPTIONAL_HEADER.ImageBase == IMAGEBASE

SECTIONS = []
for s in pe.sections:
    name = s.Name.rstrip(b"\x00").decode("latin1")
    SECTIONS.append(dict(
        name=name,
        va=IMAGEBASE + s.VirtualAddress,
        vsize=s.Misc_VirtualSize,
        rawptr=s.PointerToRawData,
        rawsize=s.SizeOfRawData,
        ch=s.Characteristics,
    ))


def sec_of(va):
    for s in SECTIONS:
        if s["va"] <= va < s["va"] + max(s["vsize"], s["rawsize"]):
            return s
    return None


def read(va, n):
    """Read n bytes at VA following section raw mapping; None if unmapped."""
    s = sec_of(va)
    if s is None:
        return None
    off = va - s["va"]
    if off < 0 or off >= s["rawsize"]:
        return None
    start = s["rawptr"] + off
    if start + n > len(RAW):
        return None
    return RAW[start:start + n]


def u32(va):
    b = read(va, 4)
    return None if b is None else struct.unpack("<I", b)[0]


def u16(va):
    b = read(va, 2)
    return None if b is None else struct.unpack("<H", b)[0]


def cstr(va, maxn=200):
    out = []
    for i in range(maxn):
        b = read(va + i, 1)
        if not b or b == b"\x00":
            break
        out.append(b)
    return b"".join(out).decode("latin1")


def va_ok(va):
    return va is not None and 0x400000 <= va < IMAGEBASE + pe.OPTIONAL_HEADER.SizeOfImage


# ---- full .text linear disassembly (skipdata) ----
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True

# second engine, detail on, used only for small windows
MD2 = Cs(CS_ARCH_X86, CS_MODE_32)
MD2.skipdata = True
MD2.detail = True
text_raw = RAW[
    sec_of(TEXT_LO)["rawptr"] + (TEXT_LO - sec_of(TEXT_LO)["va"]):
    sec_of(TEXT_LO)["rawptr"] + (TEXT_HI - sec_of(TEXT_LO)["va"])
]
INSNS = list(md.disasm(text_raw, TEXT_LO))
BY_ADDR = {}
ORDER = []
for i in INSNS:
    BY_ADDR[i.address] = i
    ORDER.append(i.address)
ORDER.sort()


def ins_at(va):
    return BY_ADDR.get(va)


def next_addr(va):
    i = BY_ADDR.get(va)
    return None if i is None else va + i.size


def fmt(i):
    return "%08X  %-24s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str)


def dis_range(lo, hi, limit=4000):
    out = []
    a = lo
    while a < hi:
        i = BY_ADDR.get(a)
        if i is None:
            a += 1
            continue
        out.append(i)
        a += i.size
        if len(out) >= limit:
            break
    return out


def find_imm32_occurrences(value):
    """All VAs where 4-byte LE `value` appears in the raw file, mapped back to VA."""
    pat = struct.pack("<I", value)
    hits = []
    idx = RAW.find(pat)
    while idx != -1:
        # map raw offset -> VA
        for s in SECTIONS:
            if s["rawptr"] <= idx < s["rawptr"] + s["rawsize"]:
                hits.append(s["va"] + (idx - s["rawptr"]))
                break
        idx = RAW.find(pat, idx + 1)
    return hits


def rtti_of_table(vt_va):
    """vt_va -> dict(COL, TD, name) via MSVC RTTI: [vt-4]=COL, [COL+0xC]=TD, TD+8=name."""
    col = u32(vt_va - 4)
    info = dict(vt=vt_va, col=col)
    if not va_ok(col):
        info["err"] = "COL unreadable"
        return info
    info["col_sig"] = u32(col)
    td = u32(col + 0xC)
    info["td"] = td
    if not va_ok(td):
        info["err"] = "TD unreadable"
        return info
    # MSVC TypeDescriptor: vfptr(+0), spare(+4), then the decorated name is INLINE at +8
    info["name_ptr"] = td + 8
    info["name"] = cstr(td + 8, 300)
    info["td_ncols"] = u32(td + 4)
    return info


def slots_of_table(vt_va, maxslots=400):
    """Read consecutive code pointers; stop at first non-.text pointer."""
    out = []
    for k in range(maxslots):
        p = u32(vt_va + 4 * k)
        if p is None or not (TEXT_LO <= p < TEXT_HI):
            break
        out.append(p)
    return out


if __name__ == "__main__":
    print("sections:")
    for s in SECTIONS:
        print("  %-8s va=%08X vsize=%08X rawptr=%08X rawsize=%08X ch=%08X" % (
            s["name"], s["va"], s["vsize"], s["rawptr"], s["rawsize"], s["ch"]))
    print("insns=%d  first=%08X last=%08X" % (len(INSNS), INSNS[0].address, INSNS[-1].address))
