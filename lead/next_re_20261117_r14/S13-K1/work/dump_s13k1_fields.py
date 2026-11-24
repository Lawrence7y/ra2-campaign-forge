"""S13-K1: INI key -> field offset extraction for WeaponTypeClass, WarheadTypeClass,
BulletTypeClass (slot25 LoadFromINI). Adapted from dump_typeclass_fields.py (clue only)
but: capstone skipdata=True; function boundary from terminal-ret+padding (channel A,
atlas-independent) AND atlas interval (channel B); this=first `mov reg,ecx` before call.
Writes EVIDENCE/ini_fields.tsv untruncated."""
import os, struct, sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\work")
from re_lib import MD, u32, cstr, read, ATLAS_FN, fmt_insn

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\EVIDENCE\ini_fields.tsv"
LOG = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\EVIDENCE\ini_fields_log.txt"

SECBUFS = (0x24, 0x1F8)   # section-name buffers in AbstractTypeClass
INI_ART = 0x00887180      # INI_Art global (artmd.ini)
STRINGTABLE_EMPTY = 0x00889F64
IMM_DEFAULT_LIMIT = 0x00800000
FIELD_READERS = {
    0x005276D0: ("ReadInteger", 4),
    0x005295F0: ("ReadBool", 1),
    0x00528A10: ("ReadString", 4),
    0x00528F00: ("ReadUnicodeString", 4),
    0x005283D0: ("ReadDouble", 8),
}
LOADERS = {
    "WeaponTypeClass":  0x00772080,
    "WarheadTypeClass": 0x0075D3A0,
    "BulletTypeClass":  0x0046BEE0,
}
TEXT_LO, TEXT_HI = 0x401000, 0x7E1000

log = []
def p(x=""): log.append(str(x))


def insns(entry, n):
    MD.skipdata = True
    return list(MD.disasm(read(entry, n), entry))


def extent_ret(entry, window=0x30000):
    """Channel A: terminal ret whose next 2 bytes are padding (CC/90).
    Independent of atlas. Returns (end_exclusive, ret_addr) or (None,None)."""
    last = None
    for insn in insns(entry, window):
        last = insn
        if insn.mnemonic.startswith("ret"):
            nxt = insn.address + insn.size
            b = read(nxt, 2)
            if len(b) == 2 and b[0] in (0xCC, 0x90) and b[1] in (0xCC, 0x90):
                return nxt, insn.address
    return (last.address + last.size if last else None), None


def mem(insn, base_reg):
    for i, m in enumerate(insn.operands):
        if m.type == 3 and m.mem.base == base_reg and m.mem.index == 0:  # X86_OP_MEM=3
            return i, m.mem.disp, m.size
    return None


def reg_of(insn, idx):
    op = insn.operands[idx]
    return op.reg if op.type == 1 else None  # X86_OP_REG=1


import capstone
X_ECX_CONST = capstone.x86.X86_REG_ECX
def this_register(body):
    """first `mov reg, ecx` before any call = object (thiscall this register)."""
    for insn in body:
        if insn.mnemonic == "call":
            return None
        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            d, s = insn.operands
            if d.type == 1 and s.type == 1 and s.reg == X_ECX_CONST:
                return d.reg
    return None


_wcache = {}
def is_wrapper(fn, known_readers):
    if fn in _wcache: return _wcache[fn]
    ok = False
    if TEXT_LO <= fn < TEXT_HI:
        inner = False; retimm = None
        for insn in insns(fn, 0x2000):
            if insn.mnemonic == "call" and insn.operands and insn.operands[0].type == 2:  # IMM=2
                if (insn.operands[0].imm & 0xFFFFFFFF) in known_readers:
                    inner = True
            if insn.mnemonic.startswith("ret") and insn.operands:
                retimm = insn.operands[0].imm
        ok = inner and retimm is not None and retimm >= 8
    _wcache[fn] = ok
    return ok


import capstone
X_EAX, X_ECX, X_EDX = capstone.x86.X86_REG_EAX, capstone.x86.X86_REG_ECX, capstone.x86.X86_REG_EDX
X_ESP, X_EBP = capstone.x86.X86_REG_ESP, capstone.x86.X86_REG_EBP
X_ECX_R = capstone.x86.X86_REG_ECX


def recover(entry, hi):
    body = insns(entry, hi - entry)
    this = this_register(body)
    if this is None:
        return None, [], {}
    secbufs = {}
    # registries from stack param (rulesmd INI)
    ini_regs = {}
    for insn in body:
        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            d, s = insn.operands
            if d.type == 1 and s.type == 3 and s.mem.base in (X_ESP, X_EBP):
                ini_regs[d.reg] = "RULES"
    rows = []
    key = None; key_sec = None; key_va = None
    default_off = None; default_site = None; default_imm = None
    cur_ini = None; default_from_prev = False; prev_returned = False
    pending = None
    for insn in body:
        was_reader = prev_returned
        prev_returned = False
        # section buffer leases
        if insn.mnemonic == "lea" and len(insn.operands) == 2:
            m = mem(insn, this)
            if m is not None and m[0] == 1 and m[1] in SECBUFS:
                r = reg_of(insn, 0)
                if r is not None: secbufs[r] = m[1]; continue
        # x87 default loads
        if insn.mnemonic in ("fld", "fild") and insn.operands:
            op = insn.operands[0]
            if op.type == 3 and op.mem.base == this and op.mem.index == 0 and op.mem.disp not in SECBUFS:
                default_off = op.mem.disp; default_site = insn.address; continue
        # movsx/movzx default loads
        if insn.mnemonic in ("movsx", "movzx") and len(insn.operands) == 2:
            m = mem(insn, this)
            if m is not None and m[0] == 1 and m[1] not in SECBUFS:
                default_off = m[1]; default_site = insn.address; default_imm = None; default_from_prev = False; continue
        # mov
        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            d, s = insn.operands
            m = mem(insn, this)
            if m is not None and m[1] not in SECBUFS:
                midx, disp, msize = m
                if midx == 1 and d.type == 1:
                    default_off = disp; default_site = insn.address; default_imm = None; default_from_prev = False; continue
                if midx == 0 and not pending and s.type == 1:
                    continue
                if midx == 0 and pending and s.type == 1:
                    k, doff, dsite, dimm, reader, rsize, site, src, sec, kva = pending
                    rows.append(dict(key=k, default_off=doff, default_site=dsite, default_imm=dimm,
                                     store_off=disp, width=msize, reader=reader,
                                     site=site, store_site=insn.address, ini=src, section=sec, key_va=kva))
                    pending = None; continue
            if d.type == 1 and d.reg == X_ECX_R:
                if s.type == 2 and (s.imm & 0xFFFFFFFF) == INI_ART:
                    cur_ini = "ART"; continue
                if s.type == 1 and s.reg in ini_regs:
                    cur_ini = ini_regs[s.reg]; continue
                if s.type in (3, 2):
                    cur_ini = "RULES"; continue
            continue
        # push
        if insn.mnemonic == "push" and insn.operands:
            op = insn.operands[0]
            if op.type == 2:
                s = cstr(op.imm & 0xFFFFFFFF, 64)
                if s and 2 <= len(s) < 64 and all(0x20 < ord(c) < 0x7F for c in s):
                    key = s; key_va = op.imm & 0xFFFFFFFF
                elif -0x80000000 <= op.imm < IMM_DEFAULT_LIMIT:
                    default_imm = op.imm
            elif op.type == 1 and was_reader and op.reg == X_EAX:
                default_from_prev = True
            elif op.type == 1 and op.reg in secbufs:
                key_sec = secbufs[op.reg]
            continue
        # call
        if insn.mnemonic == "call" and insn.operands:
            op = insn.operands[0]
            if op.type == 2:
                tgt = op.imm & 0xFFFFFFFF
                if tgt in FIELD_READERS:
                    name, size = FIELD_READERS[tgt]
                    if default_imm == STRINGTABLE_EMPTY: default_imm = None
                    if name in ("ReadString", "ReadUnicodeString"):
                        default_imm = None
                    if default_from_prev and default_off is None and rows:
                        default_off = rows[-1]["store_off"]
                    pending = (key, default_off, default_site, default_imm, name, size, insn.address,
                               cur_ini, key_sec, key_va if key else None)
                    prev_returned = True; default_from_prev = False
                    key = None; key_sec = None; key_va = None; default_off = None; default_site = None; default_imm = None
                elif is_wrapper(tgt, FIELD_READERS):
                    if default_from_prev and default_off is None and rows:
                        default_off = rows[-1]["store_off"]
                    pending = (key, default_off, default_site, default_imm, "WRAP_0x%08X" % tgt, 4,
                               insn.address, cur_ini, key_sec, key_va if key else None)
                    prev_returned = True; default_from_prev = False
                    key = None; key_sec = None; key_va = None; default_off = None; default_site = None; default_imm = None
                else:
                    key_sec = None; key_va = None
            for r in (X_EAX, X_ECX_R, X_EDX): secbufs.pop(r, None)
            continue
        # fstp store
        if insn.mnemonic == "fstp" and pending:
            for op2 in insn.operands:
                if op2.type != 3: continue
                if op2.mem.base == X_ESP: continue
                if op2.mem.base == this and op2.mem.index == 0 and op2.mem.disp not in SECBUFS:
                    k, doff, dsite, dimm, reader, rsize, site, src, sec, kva = pending
                    rows.append(dict(key=k, default_off=doff, default_site=dsite, default_imm=dimm,
                                     store_off=op2.mem.disp, width=op2.size, reader=reader,
                                     site=site, store_site=insn.address, ini=src, section=sec, key_va=kva))
                    pending = None; default_off = None; default_site = None; default_imm = None
                    break
            continue
    return this, secbufs, rows


allrows = []
for cls, entry in LOADERS.items():
    retend, retaddr = extent_ret(entry)
    at = ATLAS_FN.get(entry)
    atlas_end = entry + at[0] if at else None
    p(f"=== {cls} loader {hex(entry)} ===")
    p(f"  channel A (ret+pad, atlas-independent): end={hex(retend) if retend else None} ret={hex(retaddr) if retaddr else None}")
    p(f"  channel B (atlas): size={at[0] if at else None} end={hex(atlas_end) if atlas_end else None} n_instr={at[1] if at else None} n_callees={at[3] if at else None}")
    hi = retend if retend else atlas_end
    this, secbufs, rows = recover(entry, hi)
    p(f"  this register = {MD.reg_name(this) if this is not None else None}; secbufs={ {MD.reg_name(k):hex(v) for k,v in secbufs.items()} }; rows={len(rows)}")
    for r in rows:
        allrows.append((cls, r))

with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("class\tkey\tkey_va\tstore_off\twidth\treader\tsite\tstore_site\tdefault_site\tini\tsection\tdefault_off\tdefault_imm\n")
    for cls, r in allrows:
        f.write("%s\t%s\t%s\t0x%X\t%d\t%s\t0x%08X\t0x%08X\t%s\t%s\t%s\t%s\t%s\n" % (
            cls, r["key"] or "", ("0x%08X" % r["key_va"]) if r["key_va"] else "",
            r["store_off"], r["width"], r["reader"], r["site"], r["store_site"],
            ("0x%08X" % r["default_site"]) if r.get("default_site") else "",
            r["ini"] or "", r["section"] or "",
            ("0x%X" % r["default_off"]) if r["default_off"] is not None else "",
            r["default_imm"] if r["default_imm"] is not None else ""))
open(LOG, "w", encoding="utf-8").write("\n".join(log))
print("rows", len(allrows), "->", OUT)
print("\n".join(log))
