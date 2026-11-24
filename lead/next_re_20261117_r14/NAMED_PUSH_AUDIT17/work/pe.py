"""Independent PE + capstone harness for NAMED_PUSH_AUDIT17 (agent-233, alien auditor).

Written from scratch for this audit. Does not import any executor work dir.
Facts relied on:
  - RTTI: pTD / pCHD are ABSOLUTE VAs (not RVAs).
  - The decorated name lives INLINE at TD+8, it is not a pointer.
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
    SECTIONS.append(dict(
        name=s.Name.rstrip(b"\x00").decode("latin1"),
        va=IMAGEBASE + s.VirtualAddress,
        vsize=s.Misc_VirtualSize,
        rawptr=s.PointerToRawData,
        rawsize=s.SizeOfRawData,
        ch=s.Characteristics,
    ))

IMG_HI = IMAGEBASE + pe.OPTIONAL_HEADER.SizeOfImage


def sec_of(va):
    for s in SECTIONS:
        if s["va"] <= va < s["va"] + max(s["vsize"], s["rawsize"]):
            return s
    return None


def read(va, n):
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


def u8(va):
    b = read(va, 1)
    return None if b is None else b[0]


def cstr(va, maxn=300):
    out = []
    for i in range(maxn):
        b = read(va + i, 1)
        if not b or b == b"\x00":
            break
        out.append(b)
    return b"".join(out).decode("latin1")


def va_ok(va):
    return va is not None and IMAGEBASE <= va < IMG_HI


def in_text(va):
    return va is not None and TEXT_LO <= va < TEXT_HI


# ---------------- disassembly ----------------
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True

MDD = Cs(CS_ARCH_X86, CS_MODE_32)   # windows, detail on
MDD.skipdata = True
MDD.detail = True

_t = sec_of(TEXT_LO)
text_raw = RAW[_t["rawptr"] + (TEXT_LO - _t["va"]): _t["rawptr"] + (TEXT_HI - _t["va"])]
INSNS = list(md.disasm(text_raw, TEXT_LO))
BY = {}
for i in INSNS:
    BY[i.address] = i
ORDER = sorted(BY)


def ins_at(va):
    return BY.get(va)


def dis(lo, hi, limit=6000):
    out = []
    a = lo
    while a < hi and len(out) < limit:
        i = BY.get(a)
        if i is None:
            a += 1
            continue
        out.append(i)
        a += i.size
    return out


def fmt(i):
    return "%08X  %-22s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str)


def win(lo, hi):
    """Raw-bytes disassembly of a small window (independent of linear .text walk)."""
    b = read(lo, hi - lo)
    if b is None:
        return []
    return list(MDD.disasm(b, lo))


def find_imm32(value):
    """Every VA in the image where the 4-byte LE dword == value."""
    pat = struct.pack("<I", value)
    hits = []
    idx = RAW.find(pat)
    while idx != -1:
        for s in SECTIONS:
            if s["rawptr"] <= idx < s["rawptr"] + s["rawsize"]:
                hits.append(s["va"] + (idx - s["rawptr"]))
                break
        idx = RAW.find(pat, idx + 1)
    return hits


# ---------------- RTTI ----------------
def rtti(vt):
    """[vt-4] = COL(CompleteObjectLocator, absolute VA); [COL+0xC] = pTD (absolute VA);
    decorated name is INLINE at TD+8."""
    info = dict(vt=vt)
    col = u32(vt - 4)
    info["col"] = col
    if not va_ok(col):
        info["err"] = "COL unreadable"
        return info
    info["col_sig"] = u32(col)
    info["col_off"] = u32(col + 4)     # offset of vftable within object
    info["col_cd"] = u32(col + 8)      # pCHD (absolute VA)
    td = u32(col + 12)
    info["td"] = td
    if not va_ok(td):
        info["err"] = "TD unreadable"
        return info
    info["td_name_at"] = td + 8       # INLINE, not a pointer
    info["name"] = cstr(td + 8, 300)
    return info


def slots(vt, maxs=400):
    out = []
    for k in range(maxs):
        p = u32(vt + 4 * k)
        if p is None or not in_text(p):
            break
        out.append(p)
    return out


def tables_holding(entry, limit=400):
    """Every candidate vtable base whose slot value == entry.
    A candidate is accepted when [base-4] reads as a valid COL with a TD whose
    inline name starts with '.?' (MSVC decorated) or 'AV'/'AU' style."""
    out = []
    for occ in find_imm32(entry):
        base = occ          # slot address; base = occ - 4*k for some k
        for k in range(0, 64):
            b = occ - 4 * k
            if b < IMAGEBASE:
                break
            r = rtti(b)
            if r.get("name", "").startswith(".?"):
                # sanity: slots 0..k must all be code
                sl = slots(b)
                if len(sl) > k and sl[k] == entry:
                    out.append(dict(base=b, slot=k, slot_at=occ, rtti=r))
                break
    # de-dup by base
    seen = {}
    for o in out:
        seen.setdefault(o["base"], o)
    return sorted(seen.values(), key=lambda x: x["base"])


def _build_function_starts():
    """Union of every code pointer that appears as a dword in .rdata/.data.
    These are the vtable slot values = function entry points. Used only as
    extent boundaries, never as identity evidence."""
    st = set()
    for s in SECTIONS:
        if s["ch"] & 0x20000000:      # executable
            continue
        blob = RAW[s["rawptr"]: s["rawptr"] + s["rawsize"]]
        n = len(blob) // 4
        for k in range(n):
            v = struct.unpack_from("<I", blob, 4 * k)[0]
            if TEXT_LO <= v < TEXT_HI:
                st.add(v)
    return st


FUNC_STARTS = None


def func_extent(entry, cap=8000):
    """Linear decode from entry. Stop when we reach a known function start AND the
    previous instruction was a terminator (ret) or padding -- so interior addresses
    that merely happen to also be vtable slot values do not cut the body short."""
    global FUNC_STARTS
    if FUNC_STARTS is None:
        FUNC_STARTS = _build_function_starts()
    a = entry
    out = []
    bad = 0
    while a < TEXT_HI and len(out) < cap:
        if out and a in FUNC_STARTS:
            prev = out[-1]
            if prev.mnemonic in ("ret", "retn", "int3", "nop") or prev.mnemonic.startswith("ret"):
                break
        i = BY.get(a)
        if i is None:
            bad += 1
            a += 1
            if bad >= 8:
                break
            continue
        bad = 0
        out.append(i)
        a += i.size
    while out and out[-1].mnemonic in ("nop", "int3"):
        out.pop()
    return out


def is_ret(i):
    return i.mnemonic in ("ret", "retn") or i.mnemonic.startswith("ret")


if __name__ == "__main__":
    print("sections:")
    for s in SECTIONS:
        print("  %-8s va=%08X vsize=%08X rawptr=%08X rawsize=%08X ch=%08X" % (
            s["name"], s["va"], s["vsize"], s["rawptr"], s["rawsize"], s["ch"]))
    print("insns=%d  [%08X..%08X]  coverage=%.2f%%" % (
        len(INSNS), INSNS[0].address, INSNS[-1].address,
        100.0 * sum(i.size for i in INSNS) / (TEXT_HI - TEXT_LO)))
