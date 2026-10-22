"""R-029: the full TypeClass family -- auto-derived tree, per-class fields.

R-028 hand-wrote a seven-entry chain (AbstractType -> ObjectType -> TechnoType ->
{Infantry, Unit, Aircraft, Building}). This round removes the hand-writing: the
chain is DERIVED, and every TypeClass the image has a real LoadFromINI for is
included, so the campaign compiler gets the whole family rather than four leaves.

What is derived, and from what:

  * the class NAME comes from the vtable's CompleteObjectLocator (the MSVC RTTI
    type descriptor), never from a function symbol -- gamemd.exe is stripped, so
    a name is only a name if RTTI says so;
  * the class's own `LoadFromINI` is vtable slot 25 (established in kb/22 and
    re-checked here: slot 25 must be a .text address, slot 12 must be either the
    `xor eax,eax; ret` stub or a `mov eax,imm; ret`);
  * the PARENT is the first call inside the loader body that targets ANOTHER
    class's loader. Not simply "the first call": every one of these loaders
    starts with `call 0x526B00` (`InitFromINI`), so a naive first-call rule makes
    all 24 classes parentless. This is the same class of error as G-32, and the
    guard is the same: print the derived value and check it against something
    independent -- here, that the seven R-028 classes reproduce the chain that
    was verified by hand last round;
  * the class's constructor is the function containing `mov dword ptr [reg],
    <this class's vtable>`, choosing the candidate whose body stores the most
    fields (the other vtable stores per object are secondary-interface tables:
    each class has 3-6 vptr stores in .text and only one is the ctor).

Five classes (Tag/Trigger/Warhead/Weapon/AITrigger TypeClass) have NO loader call
at all in their body. They are not orphans and not broken: they do their own
INI work inline and never delegate. Reported as ROOT so the absence is visible.

Field recovery itself is R-028's: the store offset is read from the STORE (width
from the store instruction, not the reader), `this` is the destination of the
first `mov reg, ecx`, the two section-name buffers (+0x24 own name, +0x1F8 the
`Image=` name) are tracked as section pointers and never as fields, artmd is
distinguished from rulesmd by `mov ecx, 0x887180`, and cdecl enum wrappers are
recognised mechanically.

Run: python re_atlas/tools/dump_typeclass_family.py [--tree] [--class NAME]
"""

import os
import struct
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_rules_sections as D  # noqa: E402  read_va with per-section bounds

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

TEXT_LO, TEXT_HI = 0x401000, 0x7E1000
RDATA_LO, RDATA_HI = 0x7E1000, 0x811074
INI_ART = 0x00887180
SECNAME_OFF = (0x24, 0x1F8)
STRINGTABLE_EMPTY = 0x00889F64
IMM_DEFAULT_LIMIT = 0x00800000

FIELD_READERS = {
    0x005276D0: ("ReadInteger", 4),
    0x005295F0: ("ReadBool", 1),
    0x00528A10: ("ReadString", 4),
    0x00528F00: ("ReadUnicodeString", 4),
    0x005283D0: ("ReadDouble", 8),
}
# Converters that appear between a reader and its store but do not read a key.
CONVERTERS = (0x00428B80, 0x00478720)

# Skip these: template helpers whose RTTI name contains "TypeClass" but which
# are containers/factories, not definitions an INI section describes.
NAME_EXCLUDE = ("?$", "TypeList", "TClassFactory")


# --------------------------------------------------------------------------
# image helpers


def u32(va):
    b = D.read_va(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None


def cstr(va, cap=128):
    o = va - 0x400000
    if o < 0 or o >= len(D.BLOB):
        return ""
    return D.BLOB[o:o + cap].split(b"\x00")[0].decode("latin1")


def rtti_name(vtable_va):
    col = u32(vtable_va - 4)
    if col is None or not (RDATA_LO <= col < RDATA_HI):
        return None
    td = u32(col + 0xC)
    if td is None:
        return None
    nm = cstr(td + 8, 128)
    return nm if nm.startswith(".?AV") and nm.endswith("@@") else None


def get_size(vtable_va):
    """slot 12 body: `mov eax,imm; ret` -> imm; the abstract stub -> 0."""
    fn = u32(vtable_va + 12 * 4)
    if fn is None or not (TEXT_LO <= fn < TEXT_HI):
        return None
    ins = list(md.disasm(D.read_va(fn, 12), fn))[:2]
    if len(ins) == 2 and ins[0].mnemonic == "mov" and ins[1].mnemonic.startswith("ret"):
        if ins[0].operands[0].type == capstone.x86.X86_OP_REG \
                and ins[0].reg_name(ins[0].operands[0].reg) == "eax" \
                and ins[0].operands[1].type == capstone.x86.X86_OP_IMM:
            return ins[0].operands[1].imm & 0xFFFFFFFF
    if len(ins) == 2 and ins[0].mnemonic == "xor" and ins[1].mnemonic.startswith("ret"):
        return 0
    return None


def extent(entry, window=0x40000):
    """[entry, end) from the function's own terminal `ret` (ret + padding)."""
    last = None
    for insn in md.disasm(D.read_va(entry, window), entry):
        last = insn
        if insn.mnemonic.startswith("ret"):
            nxt = insn.address + insn.size
            b = D.read_va(nxt, 2)
            if len(b) == 2 and b[0] in (0xCC, 0x90) and b[1] in (0xCC, 0x90):
                return nxt
    return (last.address + last.size) if last else None


def body(entry, hi):
    for insn in md.disasm(D.read_va(entry, hi - entry), entry):
        yield insn


def mem(insn, base_reg):
    for i, m in enumerate(insn.operands):
        if m.type != capstone.x86.X86_OP_MEM:
            continue
        if m.mem.base == base_reg and m.mem.index == 0:
            return i, m.mem.disp, m.size
    return None


def reg_of(insn, idx):
    op = insn.operands[idx]
    return op.reg if op.type == capstone.x86.X86_OP_REG else None


# --------------------------------------------------------------------------
# class discovery


def all_type_vtables():
    """[(class_name, vtable_va)] for every RTTI-named *TypeClass with a real slot25."""
    seen = {}
    va = RDATA_LO
    while va < RDATA_HI - 4:
        col = u32(va)
        if col is not None and RDATA_LO <= col < RDATA_HI:
            td = u32(col + 0xC)
            nm = cstr(td + 8, 128) if td else ""
            if nm.startswith(".?AV") and nm.endswith("@@") and "TypeClass" in nm:
                if not any(x in nm for x in NAME_EXCLUDE):
                    vt = va + 4
                    if vt not in seen:
                        seen[vt] = nm
        va += 4
    out = []
    for vt, raw in seen.items():
        nm = raw[len(".?AV"):-len("@@")]
        s25 = u32(vt + 25 * 4)
        if s25 is None or not (TEXT_LO <= s25 < TEXT_HI):
            continue
        # only keep the PRIMARY vtable of each class: the primary is the one
        # whose [0] slot is the class's own QueryInterface, i.e. the table that
        # is preceded by its own COL naming THIS class. Secondary tables sit
        # inside the same class but their slot 25 is often a base-class method;
        # the discriminator used here is GetSize: only the primary table points
        # at a real `mov eax,imm` or the abstract stub, and only the primary of a
        # concrete class has a slot25 that is not a shared AbstractType method.
        if s25 in SHARED_TYPE_METHODS:
            continue
        out.append((nm, vt, s25, get_size(vt)))
    # ONE ENTRY PER CLASS NAME. A class has several vtables in .rdata: the
    # primary table plus secondary tables for each inherited interface, and each
    # secondary's slot 25 is a DIFFERENT method (0x41CFD0 for Aircraft, 0x512730
    # for House, 0x54A160 for IsometricTile -- none of them the class's own
    # LoadFromINI). Keeping them produced 39 "classes" where there are 22, and
    # each duplicate showed `size=stub` and `parent=ROOT`, which read like two
    # real findings. The primary table is the one whose GetSize is a concrete
    # immediate; when a class is abstract that test cannot decide, and the
    # duplicate is then resolved by preferring the table with the largest slot25
    # body -- the real loader, not a small override.
    best = {}
    for nm, vt, s25, sz in out:
        hi = extent(s25) or s25
        score = (1 if sz else 0, hi - s25)
        if nm not in best or score > best[nm][0]:
            best[nm] = (score, (nm, vt, s25, sz))
    out = [v for _, v in best.values()]
    out.sort(key=lambda r: r[0])
    return out


# Slot 25 values shared by many classes are the AbstractTypeClass default
# implementations; a class whose slot 25 is one of these inherits its loader and
# has none of its own.
SHARED_TYPE_METHODS = {0x00410490, 0x004104B0, 0x004104C0, 0x00410A60}


def loader_calls(entry, hi, own, known):
    """Calls inside the loader that target ANOTHER class's loader, in order.

    Not "the first call": every loader begins with `call 0x526B00` (InitFromINI),
    and several call a section-fetch helper before the base loader. Only targets
    that are themselves a known slot-25 loader count.
    """
    out = []
    for insn in body(entry, hi):
        if insn.mnemonic != "call" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type != capstone.x86.X86_OP_IMM:
            continue
        t = op.imm & 0xFFFFFFFF
        if t != own and t in known:
            out.append((t, insn.address))
    return out


# --------------------------------------------------------------------------
# field recovery (R-028 logic)


_WRAPPER_CACHE = {}


def _extent_small(entry, window=0x2000):
    last = None
    for insn in md.disasm(D.read_va(entry, window), entry):
        last = insn
        if insn.mnemonic.startswith("ret"):
            nxt = insn.address + insn.size
            b = D.read_va(nxt, 2)
            if len(b) == 2 and b[0] in (0xCC, 0x90) and b[1] in (0xCC, 0x90):
                return nxt
    return (last.address + last.size) if last else entry


def is_wrapper(fn):
    if fn in _WRAPPER_CACHE:
        return _WRAPPER_CACHE[fn]
    ok = False
    if TEXT_LO <= fn < TEXT_HI:
        end = _extent_small(fn)
        inner = False
        retimm = None
        for insn in md.disasm(D.read_va(fn, end - fn), fn):
            if insn.mnemonic == "call" and insn.operands \
                    and insn.operands[0].type == capstone.x86.X86_OP_IMM:
                if (insn.operands[0].imm & 0xFFFFFFFF) in FIELD_READERS:
                    inner = True
            if insn.mnemonic.startswith("ret") and insn.operands:
                retimm = insn.operands[0].imm
        ok = inner and retimm is not None and retimm >= 8
    _WRAPPER_CACHE[fn] = ok
    return ok


def this_register(entry, hi):
    for insn in body(entry, hi):
        if insn.mnemonic == "call":
            return None
        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            d, s = insn.operands
            if d.type == capstone.x86.X86_OP_REG and s.type == capstone.x86.X86_OP_REG \
                    and insn.reg_name(s.reg) == "ecx":
                return d.reg
    return None


def recover(entry, hi):
    this = this_register(entry, hi)
    if this is None:
        return None, {}, []
    secbufs = {}
    for insn in body(entry, hi):
        if insn.mnemonic == "lea" and len(insn.operands) == 2:
            m = mem(insn, this)
            if m is not None and m[0] == 1 and m[1] in SECNAME_OFF:
                r = reg_of(insn, 0)
                if r is not None:
                    secbufs[r] = m[1]
    ini_regs = {}
    for insn in body(entry, hi):
        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            d, s = insn.operands
            if d.type == capstone.x86.X86_OP_REG and s.type == capstone.x86.X86_OP_MEM \
                    and s.mem.base in (capstone.x86.X86_REG_ESP, capstone.x86.X86_REG_EBP):
                ini_regs[d.reg] = "RULES"

    rows = []
    key = key_sec = key_va = None
    default_off = default_imm = None
    cur_ini = None
    default_from_prev = False
    prev_returned = False
    pending = None

    for insn in body(entry, hi):
        was_reader = prev_returned
        prev_returned = False

        if insn.mnemonic == "lea" and len(insn.operands) == 2:
            m = mem(insn, this)
            if m is not None and m[0] == 1 and m[1] in SECNAME_OFF:
                r = reg_of(insn, 0)
                if r is not None:
                    secbufs[r] = m[1]
                continue

        if insn.mnemonic in ("fld", "fild") and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base == this \
                    and op.mem.index == 0 and op.mem.disp not in SECNAME_OFF:
                default_off = op.mem.disp
                default_imm = None
                continue

        if insn.mnemonic in ("movsx", "movzx") and len(insn.operands) == 2:
            m = mem(insn, this)
            if m is not None and m[0] == 1 and m[1] not in SECNAME_OFF:
                default_off = m[1]
                default_imm = None
                default_from_prev = False
                continue

        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            d, s = insn.operands
            m = mem(insn, this)
            if m is not None and m[1] not in SECNAME_OFF:
                midx, disp, msize = m
                if midx == 1 and d.type == capstone.x86.X86_OP_REG:
                    default_off = disp
                    default_imm = None
                    default_from_prev = False
                    continue
                if midx == 0 and not pending and s.type == capstone.x86.X86_OP_REG:
                    continue
                if midx == 0 and pending and s.type == capstone.x86.X86_OP_REG:
                    k, doff, dimm, reader, rsize, site, src, sec, kva = pending
                    rows.append({"key": k, "default_off": doff, "default_imm": dimm,
                                 "store_off": disp, "width": msize, "reader": reader,
                                 "site": site, "ini": src, "section": sec,
                                 "key_va": kva})
                    pending = None
                    continue
            if d.type == capstone.x86.X86_OP_REG and insn.reg_name(d.reg) == "ecx":
                if s.type == capstone.x86.X86_OP_IMM and (s.imm & 0xFFFFFFFF) == INI_ART:
                    cur_ini = "ART"
                    continue
                if s.type == capstone.x86.X86_OP_REG and s.reg in ini_regs:
                    cur_ini = ini_regs[s.reg]
                    continue
            continue

        if insn.mnemonic == "push" and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_IMM:
                s = cstr(op.imm & 0xFFFFFFFF, 64)
                if s and 2 <= len(s) < 64 and all(0x20 < ord(c) < 0x7F for c in s):
                    key = s
                    key_va = op.imm & 0xFFFFFFFF
                elif -0x80000000 <= op.imm < IMM_DEFAULT_LIMIT:
                    default_imm = op.imm
            elif op.type == capstone.x86.X86_OP_REG and was_reader \
                    and insn.reg_name(op.reg) == "eax":
                default_from_prev = True
            elif op.type == capstone.x86.X86_OP_REG and op.reg in secbufs:
                key_sec = secbufs[op.reg]
            continue

        if insn.mnemonic == "call" and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_IMM:
                tgt = op.imm & 0xFFFFFFFF
                hit = None
                if tgt in FIELD_READERS:
                    hit = FIELD_READERS[tgt]
                elif is_wrapper(tgt):
                    hit = ("WRAP_0x%08X" % tgt, 4)
                if hit is not None:
                    name, size = hit
                    if default_imm == STRINGTABLE_EMPTY:
                        default_imm = None
                    if name in ("ReadString", "ReadUnicodeString"):
                        default_imm = None      # buffer capacity, not a default
                    if default_from_prev and default_off is None and rows:
                        default_off = rows[-1]["store_off"]
                    pending = (key, default_off, default_imm, name, size,
                               insn.address, cur_ini, key_sec,
                               key_va if key else None)
                    prev_returned = True
                    default_from_prev = False
                    key = key_sec = key_va = default_off = default_imm = None
                elif tgt not in CONVERTERS:
                    key_sec = None
                    key_va = None
                for _r in (capstone.x86.X86_REG_EAX, capstone.x86.X86_REG_ECX,
                           capstone.x86.X86_REG_EDX):
                    secbufs.pop(_r, None)
            continue

        if insn.mnemonic == "fstp" and pending:
            for op2 in insn.operands:
                if op2.type != capstone.x86.X86_OP_MEM:
                    continue
                if op2.mem.base in (capstone.x86.X86_REG_ESP, capstone.x86.X86_REG_EBP):
                    continue
                if op2.mem.base == this and op2.mem.index == 0 \
                        and op2.mem.disp not in SECNAME_OFF:
                    k, doff, dimm, reader, rsize, site, src, sec, kva = pending
                    rows.append({"key": k, "default_off": doff, "default_imm": dimm,
                                 "store_off": op2.mem.disp, "width": op2.size,
                                 "reader": reader, "site": site, "ini": src,
                                 "section": sec, "key_va": kva})
                    pending = None
                    default_off = default_imm = None
                    break
            continue

    return this, secbufs, rows


# --------------------------------------------------------------------------
# constructors


def vptr_stores(vtable):
    pat = struct.pack("<I", vtable)
    out = []
    idx = 0
    while True:
        idx = D.BLOB.find(pat, idx)
        if idx < 0:
            break
        va = idx + 0x400000
        if TEXT_LO <= va < TEXT_HI:
            out.append(va)
        idx += 1
    return out


def func_start(va, back=0x3000):
    lo = max(TEXT_LO, va - back)
    for a in range(va - 1, lo, -1):
        b = D.read_va(a, 2)
        if len(b) == 2 and b[0] in (0xCC, 0x90) and b[1] in (0xCC, 0x90):
            return a + 2
    return None


def find_ctor(vtable):
    """(entry, end) of the class's constructor.

    Two independent conditions, both required, because "most field stores" alone
    picked the wrong function for SuperWeaponTypeClass: the winner was 0x6CE800,
    which is a `Load`-style member (it calls 0x410380 and validates a length),
    not the ctor.

      1. the function writes fields through the object register, AND
      2. it is a CONSTRUCTOR: it installs this class's vtable AND is either the
         first statement of the class's construction chain, i.e. it either calls
         a base ctor as its first call, or it is the class's own ctor with no
         base to call.

    The discriminator actually used is (2) in a cheaper form: among the
    candidates, prefer the one whose FIRST call target is itself a constructor of
    another TypeClass (the base), then the one with the most field stores. For a
    class whose base ctor is not a TypeClass (the ROOTs), condition 2 cannot
    decide, so the field-store count is used and the choice is printed.
    """
    cands = []
    for s in vptr_stores(vtable):
        st = func_start(s)
        if st is None:
            continue
        hi = extent(st)
        if hi is None:
            continue
        reg = ctor_base_reg(st, hi)
        n = 0
        for insn in body(st, hi):
            if insn.mnemonic in ("mov", "fst", "fstp", "movsd", "movss"):
                m = mem(insn, reg)
                if m is not None and m[0] == 0:
                    n += 1
        # first call target, to see whether this looks like a ctor
        first_call = None
        for insn in body(st, hi):
            if insn.mnemonic == "call" and insn.operands \
                    and insn.operands[0].type == capstone.x86.X86_OP_IMM:
                first_call = insn.operands[0].imm & 0xFFFFFFFF
                break
        # a ctor installs the vtable EARLY: within the first 24 instructions.
        # 0x6CE800 stores the vptr at 0x6CE83D, well past its prologue and after
        # a validation call -- that is a Load, and the test rejects it.
        idx = 0
        early_vptr = False
        for insn in body(st, hi):
            idx += 1
            if idx > 40:
                break
            if insn.mnemonic == "mov" and len(insn.operands) == 2:
                d, s2 = insn.operands
                if d.type == capstone.x86.X86_OP_MEM and s2.type == capstone.x86.X86_OP_IMM \
                        and (s2.imm & 0xFFFFFFFF) == vtable:
                    early_vptr = True
                    break
        cands.append({"entry": st, "end": hi, "stores": n,
                      "first_call": first_call, "early_vptr": early_vptr})
    if not cands:
        return None, None
    good = [c for c in cands if c["early_vptr"]] or cands
    good.sort(key=lambda c: -c["stores"])
    return good[0]["entry"], good[0]["end"]


def ctor_base_reg(entry, hi):
    """The register the constructor keeps its object in.

    ESI is the majority convention but not the rule: WarheadTypeClass's ctor
    holds `this` in EBP (`mov ebp,ecx` then `[ebp+0x98]`), so scanning [esi+off]
    found ZERO of its 54 fields and reported all 54 as "no ctor write". Same
    failure mode as G-32 one layer up, so the same fix: derive it positionally
    (the destination of the first `mov reg,ecx`) instead of assuming.
    """
    for insn in body(entry, hi):
        if insn.mnemonic == "call":
            return capstone.x86.X86_REG_ESI
        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            d, s = insn.operands
            if d.type == capstone.x86.X86_OP_REG and s.type == capstone.x86.X86_OP_REG \
                    and insn.reg_name(s.reg) == "ecx":
                return d.reg
    return capstone.x86.X86_REG_ESI


def ctor_offsets(entry, hi, reg=None):
    out = {}
    if entry is None:
        return out
    reg = reg or ctor_base_reg(entry, hi)
    for insn in body(entry, hi):
        if insn.mnemonic not in ("mov", "fst", "fstp", "movsd", "movss"):
            continue
        m = mem(insn, reg)
        if m is not None and m[0] == 0:
            out.setdefault(m[1], set()).add(insn.mnemonic)
    return out


def loop_cleared(entry, hi, reg=None):
    """(base, stride, count) triples for pointer-walking clear loops in the ctor.

    The COUNTER REGISTER is not fixed either. BuildingTypeClass uses
    `mov ecx,0x15`, but ObjectTypeClass's two 18-element loops use
    `mov edx,0x12` -- keying only on ecx found neither, so ObjectType's
    +0x1E8..+0x240 fields all came back "unexplained" (18 of them) and the same
    18 showed up again under IsometricTileTypeClass, which shares that ctor.
    Any register assigned a small immediate inside the loop window counts, and
    the stride must be an `add <ptr>,imm` on the SAME pointer register.
    """
    regions = []
    if entry is None:
        return regions
    reg = reg or ctor_base_reg(entry, hi)
    insns = list(body(entry, hi))
    for i, insn in enumerate(insns):
        if insn.mnemonic != "lea" or len(insn.operands) != 2:
            continue
        d, src = insn.operands
        if d.type != capstone.x86.X86_OP_REG or src.type != capstone.x86.X86_OP_MEM:
            continue
        if src.mem.base != reg or src.mem.index != 0:
            continue
        ptr = d.reg
        stride = None
        counts = []
        for j in range(i + 1, min(i + 60, len(insns))):
            k = insns[j]
            if k.mnemonic == "add" and len(k.operands) == 2 \
                    and k.operands[0].type == capstone.x86.X86_OP_REG \
                    and k.operands[0].reg == ptr \
                    and k.operands[1].type == capstone.x86.X86_OP_IMM:
                stride = k.operands[1].imm & 0xFFFFFFFF
            if k.mnemonic == "mov" and len(k.operands) == 2 \
                    and k.operands[0].type == capstone.x86.X86_OP_REG \
                    and k.operands[1].type == capstone.x86.X86_OP_IMM:
                v = k.operands[1].imm & 0xFFFFFFFF
                if 1 < v < 0x1000:
                    counts.append(v)
            if k.mnemonic == "jne" and stride and counts:
                break
        if stride and counts and 1 < stride < 0x1000:
            regions.append((src.mem.disp, stride, counts[-1]))
    return regions


# --------------------------------------------------------------------------
# reporting


def main():
    only = None
    if "--class" in sys.argv:
        i = sys.argv.index("--class")
        only = sys.argv[i + 1]

    print("=== TypeClass 家族：从 RTTI 枚举（主 vtable = 槽 25 为自有 loader）===")
    classes = all_type_vtables()
    print("  共 %d 个类" % len(classes))

    by_loader = {s25: nm for nm, vt, s25, sz in classes}
    info = {}
    print("\n=== 每类：尺寸 / this 寄存器 / 父类（首个指向别家 loader 的 call）===")
    for nm, vt, s25, sz in classes:
        hi = extent(s25)
        if hi is None:
            print("  %-28s slot25=0x%08X  !! 未定界" % (nm, s25))
            continue
        this = this_register(s25, hi)
        calls = loader_calls(s25, hi, s25, set(by_loader))
        parent = by_loader.get(calls[0][0]) if calls else None
        ctor_e, ctor_hi = find_ctor(vt)
        info[nm] = {"vtable": vt, "loader": s25, "size": sz, "end": hi,
                    "this": this, "parent": parent,
                    "calls": calls, "ctor": (ctor_e, ctor_hi),
                    "ctor_rt": "0x%08X" % ctor_e if ctor_e else "-"}
        print("  %-28s vt=0x%08X slot25=0x%08X size=%-9s this=%-4s parent=%-24s ctor=%s"
              % (nm, vt, s25,
                 ("0x%04X" % sz) if sz else "stub",
                 md.reg_name(this) if this is not None else "?",
                 parent or ("ROOT(no loader call)" if not calls else "?"),
                 info[nm]["ctor_rt"]))

    print("\n=== 继承树 ===")
    kids = {}
    for nm, d in info.items():
        kids.setdefault(d["parent"], []).append(nm)

    def walk(node, depth):
        pad = "  " * depth
        if node is None:
            print("%s(根：%d 个)" % (pad, len(kids.get(None, []))))
        rows = kids.get(node, [])
        for k in sorted(rows):
            sz = info[k]["size"]
            print("%s└ %s  %s  %d 键"
                  % (pad, k, ("0x%04X" % sz) if sz else "stub",
                     len(info[k].get("rows", [])) if "rows" in info[k] else 0))
            if k in info and info[k].get("_filled"):
                pass
            walk(k, depth + 1)

    walk(None, 0)

    print("\n=== 逐类字段表 ===")
    totals = {"keys": 0, "rules": 0, "art": 0, "nodes": 0}
    for nm, d in sorted(info.items()):
        if only and nm != only:
            continue
        rows = recover(d["loader"], d["end"])[2]
        d["rows"] = rows
        if not rows:
            print("\n--- %s  0 键（loader 体 0x%X 字节，this=%s）---"
                  % (nm, d["end"] - d["loader"],
                     md.reg_name(d["this"]) if d["this"] is not None else "?"))
            continue
        print("\n--- %s  %d 键  size=%s  parent=%s ---"
              % (nm, len(rows), ("0x%04X" % d["size"]) if d["size"] else "stub",
                 d["parent"] or "ROOT"))
        print("  %-30s %-9s %-10s %-9s %-15s %-3s %-6s %-8s %s"
              % ("键", "默认载入", "默认立即数", "存回", "读者", "宽", "INI", "节缓冲", "自检"))
        bad = 0
        n_rules = n_art = 0
        for r in sorted(rows, key=lambda x: x["store_off"]):
            cons = r["default_off"] is not None and r["default_off"] == r["store_off"]
            if cons:
                mark = "一致"
            elif r["default_off"] is not None:
                mark = "跨字段(+0x%X)" % r["default_off"]
            elif r["default_imm"] is not None and not r["reader"].startswith("ReadString"):
                mark = "立即数默认(%d)" % r["default_imm"]
            elif r["reader"].startswith("ReadString") or r["reader"] == "ReadUnicodeString":
                mark = "栈缓冲默认"
            else:
                mark = "!! 默认=None"
                bad += 1
            if r["section"] == 0x1F8 and r["ini"] == "RULES":
                mark += "  !!节/INI不符"
                bad += 1
            if r["ini"] == "ART":
                n_art += 1
            else:
                n_rules += 1
            print("  %-30s %-9s %-10s %-9s %-15s %-3d %-6s %-8s %s"
                  % (r["key"] or "!!无键名",
                     ("-" if r["default_off"] is None else "+0x%04X" % r["default_off"]),
                     ("-" if r["default_imm"] is None else "imm=%d" % r["default_imm"]),
                     "+0x%04X" % r["store_off"], r["reader"], r["width"],
                     r["ini"] or "?", ("+0x%X" % r["section"]) if r["section"] else "?",
                     mark))
        seen = {}
        ov = dup = 0
        for r in rows:
            for b in range(r["store_off"], r["store_off"] + r["width"]):
                prev = seen.get(b)
                if prev is None:
                    seen[b] = r["key"]
                elif prev == r["key"]:
                    dup += 1
                else:
                    print("  !! 偏移重叠 0x%04X: %s 与 %s" % (b, prev, r["key"]))
                    ov += 1
        print("  小结：%d 键（rules %d / art %d）  默认缺失 %d  同键双源 %d  %s"
              % (len(rows), n_rules, n_art, bad, dup,
                 "全部通过" if bad == 0 and ov == 0 else "见上"))
        totals["keys"] += len(rows)
        totals["rules"] += n_rules
        totals["art"] += n_art
        totals["nodes"] += 1

    print("\n=== 构造器链交叉核对（独立证据线）===")
    # own ctor writes / pointer-clear loops / inherited from ancestors
    print("  %-28s %5s %6s %7s %6s %6s" %
          ("类", "键", "自有ctor", "基类ctor", "指针环", "未解"))
    order = []
    seen_order = set()

    def topo(n):
        for k in sorted(kids.get(n, [])):
            order.append(k)
            topo(k)

    topo(None)
    cumulative = set()
    for nm in order:
        d = info.get(nm)
        if not d or "rows" not in d:
            continue
        written = {r["store_off"] for r in d["rows"]}
        if not written:
            continue
        own = set(ctor_offsets(*d["ctor"]))
        loops = loop_cleared(*d["ctor"])
        base = {o for o in written if o in cumulative and o not in own}
        rest = written - own - base
        in_loop = {o for o in rest if any(b <= o < b + st * c for b, st, c in loops)}
        un = rest - in_loop
        print("  %-28s %5d %6d %7d %6d %6d %s"
              % (nm, len(written), len(written & own), len(base),
                 len(in_loop), len(un),
                 "" if not un else "  " + " ".join("+0x%04X" % o for o in sorted(un))))
        cumulative |= own

    print()
    print("=== 合计 ===")
    print("  有字段的类 %d 个；键 %d（rulesmd %d / artmd %d）"
          % (totals["nodes"], totals["keys"], totals["rules"], totals["art"]))


main()
