"""异族独立审计员 core（AUDIT2 自写；不复用执行器代码，也不引用其 ROW_*.txt）。
capstone 5.0.7 skipdata=True, pefile 2024.8.26, Python 3.12.10。
"""
import pefile, capstone, struct

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
IB = 0x400000

data = open(EXE, "rb").read()
pe = pefile.PE(EXE, fast_load=True)
SEC = []
for s in pe.sections:
    nm = s.Name.rstrip(b"\x00").decode()
    va = IB + s.VirtualAddress
    SEC.append((nm, va, va + s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
TEXT = [s for s in SEC if s[0] == ".text"][0]
TLO, THI = TEXT[1], TEXT[2]

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True


def sec_of(va):
    for s in SEC:
        if s[1] <= va < s[2]:
            return s
    return None


def read(va, n):
    s = sec_of(va)
    if not s:
        return None
    off = s[3] + (va - s[1])
    if off < 0:
        return None
    b = data[off:off + n]
    return b if len(b) == n else None


def u32(va):
    b = read(va, 4)
    return None if b is None else struct.unpack("<I", b)[0]


def cstr(va, n=300):
    b = read(va, n)
    if b is None:
        b = data[(sec_of(va)[3] + va - sec_of(va)[1]):][:n] if sec_of(va) else None
        if b is None:
            return None
    z = b.find(b"\x00")
    if z >= 0:
        b = b[:z]
    return b.decode("latin1", "replace")


def rtti_of_vt(vt):
    """vt-4 -> COL -> COL+0xC -> TD -> TD+8 inline name"""
    col = u32(vt - 4)
    if col is None or sec_of(col) is None:
        return None
    td = u32(col + 0xC)
    if td is None or sec_of(td) is None:
        return None
    nm = cstr(td + 8)
    if not nm or not nm.startswith(".?"):
        return None
    return {"col": col, "td": td, "name": nm}


def holdings(entry, max_slots=400):
    """所有 (vt,slot) 使 vt[slot]==entry，且 vt 可解 RTTI。"""
    out = []
    pat = struct.pack("<I", entry)
    for s in SEC:
        if s[0] not in (".rdata", ".data"):
            continue
        lo = s[1]
        chunk = data[s[3]:s[3] + (s[2] - lo)]
        start = 0
        while True:
            i = chunk.find(pat, start)
            if i < 0:
                break
            start = i + 1
            if i % 4:
                continue
            h = lo + i
            for slot in range(max_slots):
                vt = h - slot * 4
                ri = rtti_of_vt(vt)
                if ri:
                    out.append({"vt": vt, "slot": slot, "off": slot * 4, "sect": s[0],
                                "cls": ri["name"], "col": ri["col"], "td": ri["td"]})
                    break
    return out


def slots_of_vt(vt, n=80):
    return [u32(vt + 4 * i) for i in range(n)]


_atlas = None


def atlas():
    global _atlas
    if _atlas is None:
        _atlas = []
        with open(ATLAS) as f:
            next(f)
            for ln in f:
                p = ln.rstrip("\n").split("\t")
                if len(p) < 2:
                    continue
                try:
                    _atlas.append((int(p[0], 16), int(p[1])))
                except ValueError:
                    continue
        _atlas.sort()
    return _atlas


def fn_at(va):
    best = None
    for e, sz in atlas():
        if e <= va < e + sz:
            if best is None or e > best[0]:
                best = (e, sz)
    return best


def disasm(va, n=40, nbytes=None):
    b = read(va, nbytes if nbytes else max(16, n * 15))
    if b is None:
        return []
    out = []
    for i, ins in enumerate(md.disasm(b, va)):
        out.append(ins)
        if not nbytes and i + 1 >= n:
            break
    return out


def fmt(ins):
    return f"{ins.address:08X}  {ins.bytes.hex(' ').upper():<30} {ins.mnemonic:<7} {ins.op_str}"


def show(va, n=30, label=""):
    L = []
    if label:
        L.append(f"--- {label} @ {va:08X} ---")
    for ins in disasm(va, n):
        L.append(fmt(ins))
    return "\n".join(L)


def show_range(lo, hi, label=""):
    L = [f"--- {label} [{lo:08X},{hi:08X}) ---"] if label else []
    for ins in disasm(lo, nbytes=hi - lo):
        L.append(fmt(ins))
    return "\n".join(L)


def show_fn(va, label=""):
    fa = fn_at(va)
    if not fa:
        return show(va, 40, label or "unknown-fn")
    return show_range(fa[0], fa[0] + fa[1], label or f"fn {fa[0]:08X} (size {fa[1]})")


def calls_to(target, lo=None, hi=None):
    """全 .text 单遍：所有 E8 rel32 调用 target 的站点。"""
    lo = lo or TLO
    hi = hi or THI
    res = []
    for ins in md.disasm(read(lo, hi - lo) or b"", lo):
        if ins.mnemonic == "call" and ins.address + ins.size + 0 == 0:
            pass
    # 更稳：直接扫 E8
    b = read(lo, hi - lo)
    i = 0
    pat = b"\xe8"
    while True:
        i = b.find(pat, i)
        if i < 0:
            break
        rel = struct.unpack("<i", b[i + 1:i + 5])[0]
        if (lo + i + 5 + rel) & 0xFFFFFFFF == target:
            res.append(lo + i)
        i += 1
    return res


def refs_to(target, sect_names=(".text",)):
    """4 字节小端 VA 出现位置（imm32 / 表项）。"""
    out = []
    pat = struct.pack("<I", target)
    for s in SEC:
        if s[0] not in sect_names:
            continue
        chunk = data[s[3]:s[3] + (s[2] - s[1])]
        st = 0
        while True:
            i = chunk.find(pat, st)
            if i < 0:
                break
            st = i + 1
            out.append(s[1] + i)
    return sorted(out)


def insn_at(va, n=6):
    """从 va 精确解一条指令（用于取字节）。"""
    d = disasm(va, n)
    return d


def vtable_writes(vt):
    """找 .text 里把 vt 当 imm32 写进内存的指令（C7 /0x, mov [r],imm32 等）。"""
    out = []
    for r in refs_to(vt):
        ins = disasm(r - 16, 6, nbytes=32)
        hit = None
        for i in ins:
            if i.address <= r < i.address + i.size:
                hit = i
                break
        if hit and hit.mnemonic == "mov" and len(hit.operands) == 2 and hit.operands[1].type == capstone.x86.X86_OP_IMM:
            out.append((hit, r))
    return out


def atexit_owners(lo, hi):
    """找出 [lo,hi) 内的 push imm32 ; call 0x7C978A 组合（atexit 注册）。"""
    out = []
    for ins in disasm(lo, nbytes=max(0, hi - lo)):
        pass
    prev = None
    for ins in disasm(lo, nbytes=max(0, hi - lo)):
        if ins.mnemonic == "call":
            try:
                tgt = ins.operands[0].imm
            except Exception:
                tgt = None
            if tgt in (0x7C978A, 0x7C9785) and prev and prev.mnemonic == "push":
                out.append((ins.address, prev)
                           )
        prev = ins
    return out


def xref_sites(target, kind="all"):
    """返回到 target 的引用类别：call E8 / mov imm / 表项。"""
    res = {"call": calls_to(target), "imm_or_data": []}
    for r in refs_to(target, (".text", ".data", ".rdata")):
        ins = disasm(r - 16, 6, nbytes=32)
        for i in ins:
            if i.address <= r < i.address + i.size:
                res["imm_or_data"].append((r, fmt(i), i.mnemonic))
                break
        else:
            res["imm_or_data"].append((r, "<data>", ""))
    return res
