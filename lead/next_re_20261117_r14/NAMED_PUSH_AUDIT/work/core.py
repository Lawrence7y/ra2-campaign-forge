"""异族审计员自写核心：PE 读取 / RTTI / 反汇编 / 持有表枚举。
不复用执行器任何代码。capstone skipdata=True。
"""
import pefile, capstone, struct, io, os, json

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

pe = pefile.PE(EXE, fast_load=True)
IB = 0x400000
sections = []
for s in pe.sections:
    nm = s.Name.rstrip(b"\x00").decode()
    va = IB + s.VirtualAddress
    sections.append((nm, va, va + s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
data = open(EXE, "rb").read()
TEXT = [s for s in sections if s[0] == ".text"][0]
TEXT_LO, TEXT_HI = TEXT[1], TEXT[2]

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True


def sec_of(va):
    for s in sections:
        if s[1] <= va < s[2]:
            return s
    return None


def read(va, n):
    s = sec_of(va)
    if not s:
        return None
    off = s[3] + (va - s[1])
    if off < 0 or off + n > len(data):
        return None
    return data[off:off + n]


def u32(va):
    b = read(va, 4)
    return None if b is None else struct.unpack("<I", b)[0]


def u16(va):
    b = read(va, 2)
    return None if b is None else struct.unpack("<H", b)[0]


def cstr(va, maxn=256):
    b = read(va, maxn)
    if b is None:
        return None
    z = b.find(b"\x00")
    if z >= 0:
        b = b[:z]
    try:
        return b.decode("latin1")
    except Exception:
        return None


def name_of_td(td):
    """TD+8 内联名串。"""
    if td is None:
        return None
    return cstr(td + 8)


def rtti_from_col(col):
    """COL -> (td, name). 失败返回 (None,None)。"""
    if col is None or sec_of(col) is None:
        return None, None
    td = u32(col + 0xC)
    if td is None:
        return None, None
    nm = name_of_td(td)
    if not nm or not nm.startswith(".?"):
        return None, None
    return td, nm


def rtti_of_vtable(vt):
    """vt-4 = COL。返回 dict 或 None。"""
    col = u32(vt - 4)
    if col is None:
        return None
    td, nm = rtti_from_col(col)
    if nm is None:
        return None
    return {"col": col, "td": td, "name": nm, "col_mangled": cstr(col)}


def holdings(entry, max_slots=200, text_only=False):
    """枚举所有 (vtable, slot) 使 vt[slot]==entry。"""
    out = []
    for s in sections:
        if s[0] not in (".rdata", ".data"):
            continue
        lo, hi = s[1], s[2]
        base_off = s[3]
        chunk = data[base_off:base_off + (hi - lo)]
        pat = struct.pack("<I", entry)
        start = 0
        while True:
            i = chunk.find(pat, start)
            if i < 0:
                break
            h = lo + i
            start = i + 1
            if i % 4:
                continue
            for slot in range(0, max_slots):
                vt = h - slot * 4
                ri = rtti_of_vtable(vt)
                if ri:
                    out.append({"vt": vt, "slot": slot, "slot_off": slot * 4,
                                "cls": ri["name"], "col": ri["col"], "td": ri["td"],
                                "sect": s[0]})
                    break
    return out


_atlas = None


def atlas():
    global _atlas
    if _atlas is None:
        _atlas = []
        with open(ATLAS) as f:
            next(f)
            for ln in f:
                p = ln.rstrip("\n").split("\t")
                if len(p) < 3:
                    continue
                try:
                    _atlas.append((int(p[0], 16), int(p[1])))
                except ValueError:
                    continue
        _atlas.sort()
    return _atlas


def func_at(va):
    """返回覆盖 va 的 atlas 函数 (entry,size) 或 None。"""
    best = None
    for e, sz in atlas():
        if e <= va < e + sz:
            if best is None or e > best[0]:
                best = (e, sz)
    return best


def disasm(va, n_instr=40, max_bytes=None):
    b = read(va, max_bytes or n_instr * 15)
    if b is None:
        return []
    res = []
    for i, ins in enumerate(md.disasm(b, va)):
        res.append(ins)
        if i + 1 >= n_instr:
            break
        if ins.address >= TEXT_HI:
            break
    return res


def disasm_bytes(va, nbytes):
    return disasm(va, 10 ** 6, nbytes)


def fmt(ins):
    bs = ins.bytes.hex(" ").upper()
    return f"{ins.address:08X}  {bs:<32} {ins.mnemonic:<8} {ins.op_str}"


def show(va, n=30, label=""):
    out = []
    if label:
        out.append(f"--- {label} @ {va:08X} ---")
    for ins in disasm(va, n):
        out.append(fmt(ins))
    return "\n".join(out)


def show_range(lo, hi, label=""):
    out = []
    if label:
        out.append(f"--- {label} [{lo:08X},{hi:08X}) ---")
    for ins in disasm_bytes(lo, hi - lo):
        out.append(fmt(ins))
    return "\n".join(out)


def body(entry):
    fa = func_at(entry)
    return fa


def dwords(va, n):
    return [u32(va + 4 * i) for i in range(n)]
