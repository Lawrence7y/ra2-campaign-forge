"""R-028: key -> struct offset for the TypeClass inheritance chain.

R2-2 recovered RulesClass's own fields. The campaign compiler needs the next
layer: the per-type INI definitions that rule entries point at
(`[InfantryTypes]` -> `[E1]`, `[VehicleTypes]` -> `[HTNK]`, ...), because those
are the bulk of what a generated rulesmd.ini has to contain.

The chain, read out of the image rather than assumed:

    AbstractClass        0x007E1F50   (no INI)
    AbstractTypeClass    0x007E2000   slot25 = 0x00410A60
    ObjectTypeClass      0x007EF2D8   slot25 = 0x005F92D0
    TechnoTypeClass      0x007F4ED8   slot25 = 0x00712170
      InfantryTypeClass  0x007EB610   slot25 = 0x005240A0   size 0xED0
      UnitTypeClass      0x007F6218   slot25 = 0x00747620   size 0xE78
      AircraftTypeClass  0x007E2868   slot25 = 0x0041CC20   size 0xE10
      BuildingTypeClass  0x007E4570   slot25 = 0x0045FE50   size 0x1798

Each slot25 value is the class's own `LoadFromINI`, and each one CALLS its base
class's loader in its first few instructions, so a field's offset belongs to the
layer that writes it. Sizes come from slot 12 (GetSize), which is 0 on the four
abstract layers and an immediate on the four concrete ones.

Three things this tool does that dump_rules_fields.py could not, all of them
consequences of these being DIFFERENT CLASSES rather than RulesClass:

 1. `this` is not in a fixed register. Every one of the seven loaders does
    `mov <reg>, ecx` in its prologue and keeps the object there -- but the
    register differs per class (ebx, ebx, ebp, esi, edi, esi, ebp). detect_base
    in dump_rules_fields.py only considers edi/ebx/esi, so it picks the
    INIClass for TechnoType (ebp) and the second stack parameter for
    BuildingType (edi) and reports those two classes' fields at INIClass
    offsets. The rule used here is positional: the destination of the FIRST
    `mov reg, ecx` before any call IS the object.

 2. THE SAME LOADER READS TWO FILES. Every derived loader reads its own keys
    from the caller's INIClass (rulesmd.ini) and then some from the global
    `CCINIClass` at 0x887180, which is INI_Art (artmd.ini) -- confirmed by the
    CompleteObjectLocator of its vtable naming `.?AVCCINIClass@@`, and by
    kb/30 §0. For a compiler this is the difference between writing a key into
    the right file and silently writing it into one the engine never reads for
    that field. So every row carries which file it came from.

 3. Defaults come from the CLASS OWN CONSTRUCTOR. check_defaults used the
    RulesClass ctor (0x665650) for everything, which made every bool in
    AircraftTypeClass report "ctor wrote 4 bytes, reader reads 1" -- the ctor
    it was comparing against belongs to a different, larger object. Here each
    layer's ctor is located by the immediate store of its own vtable pointer
    (`mov [esi], <vtable>`), and only when that store is the one that follows
    the base ctor call.

Discipline carried in from R2-2 (all of these were real defects there):
  * the body is bounded by the function's OWN terminal `ret` (ret followed by
    padding), never a window size -- TechnoType is 0x3FD1 bytes and
    BuildingType 0x4C13, so a 0x1000 window would have halved both silently;
  * read_va checks section bounds per section;
  * key literals come from the push immediately preceding the reader call;
  * `lea reg,[this+0x24]` and `lea reg,[this+0x1F8]` are SECTION NAME BUFFERS,
    not fields -- treating them as default-value loads would attribute a field
    at +0x24 and +0x1F8 for every key;
  * width comes from the STORE, not from the reader.

Run: python re_atlas/tools/dump_typeclass_fields.py [--all]
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

INI_ART = 0x00887180          # CCINIClass, artmd.ini  (COL .?AVCCINIClass@@)
SECNAME_OFF = (0x24, 0x1F8)   # the two section-name buffers in AbstractTypeClass

# Readers usable by these loaders. `ret 0xC` = cdecl 3 args
# (section, key, default) for the scalar ones. ReadString/ReadUnicodeString
# take a destination buffer, so their "default" is a stack pointer, not a field.
# `push 0x889f64` is the empty-StringTable sentinel that ReadString and its
# wrappers take as the "no default text" argument. It is a POINTER, not a number,
# so treating it as an integer default printed `imm=8953700` next to every string
# key -- arithmetic on an address, which is the same class of error as reading
# BSS as file bytes (G-21). Anything at or above this is not a scalar default.
STRINGTABLE_EMPTY = 0x00889F64
IMM_DEFAULT_LIMIT = 0x00800000

FIELD_READERS = {
    0x005276D0: ("ReadInteger", 4),
    0x005295F0: ("ReadBool", 1),
    0x00528A10: ("ReadString", 4),
    0x00528F00: ("ReadUnicodeString", 4),
    0x005283D0: ("ReadDouble", 8),
}

CHAIN = [
    # name, vtable, loader(LoadFromINI), size
    ("AbstractTypeClass",   0x007E2000, 0x00410A60, 0),
    ("ObjectTypeClass",     0x007EF2D8, 0x005F92D0, 0),
    ("TechnoTypeClass",     0x007F4ED8, 0x00712170, 0),
    ("InfantryTypeClass",   0x007EB610, 0x005240A0, 0x0ED0),
    ("UnitTypeClass",       0x007F6218, 0x00747620, 0x0E78),
    ("AircraftTypeClass",   0x007E2868, 0x0041CC20, 0x0E10),
    ("BuildingTypeClass",   0x007E4570, 0x0045FE50, 0x1798),
]


# --------------------------------------------------------------------------
# image helpers


def u32(va):
    b = D.read_va(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None


def cstr(va, cap=64):
    o = va - 0x400000
    if o < 0 or o >= len(D.BLOB):
        return ""
    return D.BLOB[o:o + cap].split(b"\x00")[0].decode("latin1")


def rtti_name(vtable_va):
    """The class name from the COL just before a vtable, or None."""
    col = u32(vtable_va - 4)
    if col is None or not (RDATA_LO <= col < RDATA_HI):
        return None
    td = u32(col + 0xC)
    if td is None:
        return None
    nm = cstr(td + 8, 96)
    return nm if nm.startswith(".?AV") else None


def get_size(vtable_va):
    """slot 12 (GetSize) body: `mov eax, imm ; ret`. None when it is the stub."""
    fn = u32(vtable_va + 12 * 4)
    if fn is None:
        return None
    ins = list(md.disasm(D.read_va(fn, 12), fn))[:2]
    if len(ins) == 2 and ins[0].mnemonic == "mov" and ins[1].mnemonic.startswith("ret"):
        if ins[0].operands and ins[0].operands[0].type == capstone.x86.X86_OP_REG:
            if ins[0].reg_name(ins[0].operands[0].reg) == "eax" \
                    and ins[0].operands[1].type == capstone.x86.X86_OP_IMM:
                return ins[0].operands[1].imm & 0xFFFFFFFF
    return None


# --------------------------------------------------------------------------
# body / boundary


def extent(entry, window=0x30000):
    """[entry, end) of the function, from its own terminal `ret`.

    A `ret` is not the end by itself: these loaders have 2-3 of them, and the
    LAST one is followed by the next function or by padding. The reliable end
    is a `ret` whose successor is two more padding bytes, because MSVC pads
    between functions. A window size is never used (G-24: a 0x1000 window
    halved four loaders in R2-2 with no indication at all).
    """
    last = None
    for insn in md.disasm(D.read_va(entry, window), entry):
        last = insn
        if insn.mnemonic.startswith("ret"):
            nxt = insn.address + insn.size
            b = D.read_va(nxt, 2)
            if len(b) == 2 and b[0] in (0xCC, 0x90) and b[1] in (0xCC, 0x90):
                return nxt, insn.address
    # fall through: no padding form found. Report the conservative end and let
    # the caller flag it rather than silently using a window.
    return (last.address + last.size if last else None), None


def body(entry, hi):
    for insn in md.disasm(D.read_va(entry, hi - entry), entry):
        yield insn


def mem(insn, base_reg):
    """(operand_index, disp, size) of a [reg+disp] operand with no index."""
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
# the object register


def this_register(entry, hi):
    """Destination of the FIRST `mov reg, ecx` before any call.

    Uniform across all seven loaders and verifiable per class: AbstractType and
    ObjectType keep it in ebx, TechnoType and BuildingType in ebp, Infantry and
    Aircraft in esi, Unit in edi. The positional rule matters because
    dump_rules_fields.detect_base(), which looks only at edi/ebx/esi, picks the
    wrong register for THREE of the seven (TechnoType: esi = INIClass,
    ObjectType/AbstractType: ebx is right, BuildingType: edi = the INIClass
    parameter). Picking the wrong one produces a complete, plausible,
    internally consistent field table for the wrong object.
    """
    for insn in body(entry, hi):
        if insn.mnemonic == "call":
            return None
        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            d, s = insn.operands
            if d.type == capstone.x86.X86_OP_REG and s.type == capstone.x86.X86_OP_REG \
                    and insn.reg_name(s.reg) == "ecx":
                return d.reg
        # `push reg` before the mov is normal; only a call ends the search
    return None


def section_buffers(entry, hi, this):
    """reg -> 0x24 / 0x1F8 for the `lea reg,[this+0x24|0x1F8]` section buffers."""
    out = {}
    for insn in body(entry, hi):
        if insn.mnemonic != "lea":
            continue
        m = mem(insn, this)
        if m is None or m[0] != 1:
            continue
        if m[1] in SECNAME_OFF:
            r = reg_of(insn, 0)
            if r is not None:
                out[r] = m[1]
    return out


# --------------------------------------------------------------------------
# wrapper readers
#
# Not every key is read by a bare `Read*` call. Roughly 100 sites in these seven
# loaders go through a small cdecl helper that has the same
# `(section, key, default)` signature, calls a real reader itself, and then maps
# the string it got to an enum value -- `PipScale`, `Armor`, `Foundation`,
# `SpeedType`, `BuildCat`, `Owner`, `GuardRange`. Ignoring them produced 107
# rows whose store offset was recorded (correctly) against the wrong key, and
# one row with no key at all, because the wrapper call reset nothing and the
# NEXT store inherited the previous `pending`.
#
# The wrapper set is derived mechanically, not hand-listed:
#   * the callee's body calls one of the five real readers, AND
#   * the callee's own `ret` has an immediate argument >= 8 (cdecl, so the
#     callee pops its arguments; the helper's arg count equals the reader's).
# A converter such as `0x00428B80` (char* -> pointer) and a parser such as
# `0x007514D0` also appear at these sites but fail the first test, so they are
# not mistaken for readers: at those sites the store is the second instruction
# of a two-step conversion and the field really belongs to the earlier key.
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
    """True when `fn` is a cdecl key reader with the standard 3-argument shape."""
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


def wrapper_name(fn):
    return "WRAP_0x%08X" % fn


def recover(entry, hi):
    """rows of dicts; see the module docstring for the shape."""
    this = this_register(entry, hi)
    if this is None:
        return None, None, []
    secbufs = section_buffers(entry, hi, this)
    # the caller's INIClass registers (stack-parameter sourced)
    ini_regs = {}
    for insn in body(entry, hi):
        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            d, s = insn.operands
            if d.type == capstone.x86.X86_OP_REG and s.type == capstone.x86.X86_OP_MEM \
                    and s.mem.base in (capstone.x86.X86_REG_ESP, capstone.x86.X86_REG_EBP):
                ini_regs[d.reg] = "RULES"

    rows = []
    key = None              # last printable literal pushed
    key_sec = None          # which section buffer was pushed with it
    key_va = None
    default_off = None      # offset of the last default-value load from [this+off]
    default_imm = None      # ... or an immediate staged for the call (`push -1`)
    cur_ini = None          # ('RULES'|'ART') of the `mov ecx, ...` before the call
    default_strcap = None       # string readers: buffer capacity, not a default
    default_from_prev = False   # `push eax` after a reader call
    prev_returned = False       # the previous instruction was a reader call
    pending = None

    for insn in body(entry, hi):
        was_reader = prev_returned
        prev_returned = False
        # --- section-name buffer leases: lea r,[this+0x24|0x1F8]
        if insn.mnemonic == "lea" and len(insn.operands) == 2:
            m = mem(insn, this)
            if m is not None and m[0] == 1 and m[1] in SECNAME_OFF:
                r = reg_of(insn, 0)
                if r is not None:
                    secbufs[r] = m[1]
                continue

        # --- x87 default loads
        if insn.mnemonic in ("fld", "fild") and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base == this \
                    and op.mem.index == 0 and op.mem.disp not in SECNAME_OFF:
                default_off = op.mem.disp
                continue

        # --- movshapes
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
                    default_off = disp          # default-value load
                    default_imm = None
                    default_from_prev = False
                    continue
                # A store that is NOT pending's store, and not a field load:
                # `mov [this+off], eax` right after `push eax` is the PREVIOUS
                # key's store being hoisted below the next key's arguments.
                # It must neither create a row (there is no pending) nor clear
                # the cross-key default that `push eax` just set -- doing the
                # latter cost EliteAirstrikeRechargeTime and OccupyHeight.
                if midx == 0 and not pending and s.type == capstone.x86.X86_OP_REG:
                    continue
                if midx == 0 and pending and s.type == capstone.x86.X86_OP_REG:
                    k, doff, dimm, reader, rsize, site, src, sec, kva = pending
                    rows.append({"key": k, "default_off": doff, "default_imm": dimm,
                                 "store_off": disp, "width": msize, "reader": reader,
                                 "site": site, "ini": src, "section": sec,
                                 "key_va": kva})
                    pending = None
                    # Both accumulators are deliberately NOT reset here. The
                    # compiler hoists the NEXT key's default-value load above
                    # the previous key's store, so `mov reg,[this+off]` for key
                    # N+1 routinely sits between the call for key N and the
                    # store for key N. Clearing on store dropped 11 defaults in
                    # ObjectTypeClass and 8 in TechnoTypeClass (every
                    # AlternateArcticArt/Theater/Crushable/... bool). They ARE
                    # reset at the call, which is the point where the value has
                    # been consumed into `pending`.
                    continue
            # `mov ecx, imm` selecting the INIClass -- ART when the immediate is
            # the global object address. `mov ecx, <reg>` propagates RULES/ART
            # from that register.
            if d.type == capstone.x86.X86_OP_REG and insn.reg_name(d.reg) == "ecx":
                if s.type == capstone.x86.X86_OP_IMM and (s.imm & 0xFFFFFFFF) == INI_ART:
                    cur_ini = "ART"
                    continue
                if s.type == capstone.x86.X86_OP_REG and s.reg in ini_regs:
                    cur_ini = ini_regs[s.reg]
                    continue
            continue

        # --- push: key literal, an immediate default, or a section-name buffer
        if insn.mnemonic == "push" and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_IMM:
                s = cstr(op.imm & 0xFFFFFFFF, 64)
                if s and 2 <= len(s) < 64 and all(0x20 < ord(c) < 0x7F for c in s):
                    key = s
                    key_va = op.imm & 0xFFFFFFFF
                elif -0x80000000 <= op.imm < IMM_DEFAULT_LIMIT:
                    # A literal default -- `push -1` for Speed, `push 0` for the
                    # EliteAirstrikeTeam fields. Recorded whether or not a key
                    # has been seen yet, because MSVC does not keep one order:
                    # Speed pushes -1 FIRST and the key literal second. Gating
                    # on `key is not None` lost it. The value is only USED if it
                    # survives to a reader call with no intervening field load.
                    default_imm = op.imm
            elif op.type == capstone.x86.X86_OP_REG and was_reader \
                    and insn.reg_name(op.reg) == "eax":
                # Checked BEFORE the section-buffer lookup on purpose: eax holds
                # the reader's return value at this point, so it cannot also be
                # a live section buffer. The reorder is belt-and-braces with the
                # clobber rule below.
                #
                # `push eax` immediately after a reader call means THIS key's
                # default is the PREVIOUS key's value -- EliteAirstrikeRecharge
                # Time defaults to EliteAirstrikeTeam's result. That is a real
                # engine default and is recoverable: it is the previous row's
                # store offset. Recorded as a flag and resolved at the call.
                default_from_prev = True
            elif op.type == capstone.x86.X86_OP_REG and op.reg in secbufs:
                key_sec = secbufs[op.reg]
            continue

        # --- reader call: a bare Read*, or a cdecl wrapper that ends up in one
        if insn.mnemonic == "call" and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_IMM:
                tgt = op.imm & 0xFFFFFFFF
                if tgt in FIELD_READERS:
                    name, size = FIELD_READERS[tgt]
                    if default_imm == STRINGTABLE_EMPTY:
                        default_imm = None   # empty-StringTable pointer
                    if name in ("ReadString", "ReadUnicodeString"):
                        # For the string readers the trailing immediates are the
                        # BUFFER CAPACITY (`push 0x80`), not a default value.
                        # "DeploysInto default = 128" is not a fact about the
                        # game.
                        default_strcap = default_imm
                        default_imm = None
                    if default_from_prev and default_off is None and rows:
                        # `push eax` right after the previous reader: this key's
                        # default is the PREVIOUS key's fresh value. Resolvable
                        # exactly -- it is the last row's store offset.
                        default_off = rows[-1]["store_off"]
                    pending = (key, default_off, default_imm, name, size,
                               insn.address, cur_ini, key_sec,
                               key_va if key else None)
                    prev_returned = True
                    default_from_prev = False
                    key = None
                    key_sec = None
                    key_va = None
                    default_off = None
                    default_imm = None
                elif is_wrapper(tgt):
                    # The wrapper's ARGUMENTS are already on the stack in the
                    # same order, so everything latched for it is identical; the
                    # only difference is the reader name. Width is taken from
                    # the store either way.
                    if default_from_prev and default_off is None and rows:
                        default_off = rows[-1]["store_off"]
                    pending = (key, default_off, default_imm, wrapper_name(tgt), 4,
                               insn.address, cur_ini, key_sec,
                               key_va if key else None)
                    prev_returned = True
                    default_from_prev = False
                    key = None
                    key_sec = None
                    key_va = None
                    default_off = None
                    default_imm = None
                elif tgt in (0x00428B80, 0x00478720):
                    # Documented converters, not readers: they take the char*
                    # returned by a ReadString and produce a real pointer. The
                    # store after them belongs to the PREVIOUS key, so `pending`
                    # is deliberately left alone.
                    pass
                else:
                    # Any OTHER call invalidates what was latched: the key
                    # literal and the section buffer are stack arguments and the
                    # callee is free to have consumed them. Without this, a call
                    # to a non-reader between a key push and the next key push
                    # left a stale section buffer behind, which then produced 20
                    # fake "section/INI mismatch" rows in TechnoTypeClass
                    # (AttackFriendlies, ROT, CanBeHidden, ...) -- each one a key
                    # whose SECTION was inherited from an earlier key while its
                    # INIClass came from its own `mov ecx,...`.
                    key_sec = None
                    key_va = None
                # A call clobbers eax/ecx/edx, so any section-name buffer leased
                # into one of THOSE registers is gone. This is not pedantry:
                # BuildingTypeClass leases +0x1F8 into BOTH eax and edi, and eax
                # is also the reader's return register, so `push eax` after a
                # call was being read as "push the section buffer" and the
                # cross-key default it actually carries (OccupyHeight defaults
                # to Height) was lost. ebx/esi/edi/ebp survive a call, so their
                # leases stay.
                for _r in (capstone.x86.X86_REG_EAX, capstone.x86.X86_REG_ECX,
                           capstone.x86.X86_REG_EDX):
                    secbufs.pop(_r, None)
            continue

        # --- x87 store
        if insn.mnemonic == "fstp" and pending:
            for op2 in insn.operands:
                if op2.type != capstone.x86.X86_OP_MEM:
                    continue
                if op2.mem.base in (capstone.x86.X86_REG_ESP, capstone.x86.X86_REG_EBP):
                    continue          # staging the default argument, not a field
                if op2.mem.base == this and op2.mem.index == 0 \
                        and op2.mem.disp not in SECNAME_OFF:
                    k, doff, dimm, reader, rsize, site, src, sec, kva = pending
                    rows.append({"key": k, "default_off": doff, "default_imm": dimm,
                                 "store_off": op2.mem.disp, "width": op2.size,
                                 "reader": reader, "site": site, "ini": src,
                                 "section": sec, "key_va": kva})
                    pending = None
                    default_off = None
                    default_imm = None
                    break
            continue

    return this, secbufs, rows


# --------------------------------------------------------------------------
# per-class constructor cross-check


# Which constructor initialises which class. Located by "the function whose body
# contains a `mov dword ptr [reg], <class vtable>`", found by scanning .text for
# the vtable immediate and then resolving the enclosing function. Several vtables
# are stored per object (the multiple-inheritance secondary tables), so the
# candidates are filtered to those with more than a handful of field stores; the
# real ctor of each class is the one with the most. Verified by the fact that
# each class's ctor CALLS its base class's ctor as its first action:
#   BuildingType 0x0045DD90 calls TechnoType 0x00710AF0
#   TechnoType   0x00710AF0 calls ObjectType  0x005F7320
#   ObjectType   0x005F7320 calls Abstract   0x00410960
CTORS = {
    "ObjectTypeClass":   (0x005F7320, 0x005F73FA),
    "TechnoTypeClass":   (0x00710AF0, 0x0071183E),
    "InfantryTypeClass": (0x005236A0, 0x00523979),
    "UnitTypeClass":     (0x007470D0, 0x007472B7),
    "AircraftTypeClass": (0x0041C8B0, 0x0041C9E8),
    "BuildingTypeClass": (0x0045DD90, 0x0045E512),
}


def ctor_offsets(entry, hi, reg=None):
    """Offsets the constructor writes through its own object register."""
    reg = reg or capstone.x86.X86_REG_ESI
    out = {}
    for insn in md.disasm(D.read_va(entry, hi - entry), entry):
        if insn.mnemonic not in ("mov", "fst", "fstp", "movsd", "movss"):
            continue
        for m in insn.operands:
            if m.type == capstone.x86.X86_OP_MEM and m.mem.base == reg \
                    and m.mem.index == 0:
                out.setdefault(m.mem.disp, set()).add(insn.mnemonic)
    return out


def loop_cleared_offsets(entry, hi, reg=None):
    """Offsets cleared by a POINTER-WALKING loop inside the ctor.

    `lea eax,[esi+0xF5C]; mov ecx,0x15; ... mov [eax],edi; ... add eax,0x44`
    clears 21 x 0x44 bytes with no `[esi+off]` operand anywhere, so a naive
    offset scan sees nothing there. Recovering the (base, stride, count) triple
    turns 132 BuildingTypeClass "uninitialised" offsets into one explained
    region instead of a list of mystery gaps.
    """
    reg = reg or capstone.x86.X86_REG_ESI
    regions = []
    insns = list(md.disasm(D.read_va(entry, hi - entry), entry))
    for i, insn in enumerate(insns):
        if insn.mnemonic != "lea" or len(insn.operands) != 2:
            continue
        d, src = insn.operands
        if d.type != capstone.x86.X86_OP_REG or src.type != capstone.x86.X86_OP_MEM:
            continue
        if src.mem.base != reg or src.mem.index != 0:
            continue
        # look ahead for `add <same reg>, STRIDE` and a `mov ecx,N`
        ptr = d.reg
        stride = None
        count = None
        for j in range(i + 1, min(i + 46, len(insns))):
            k = insns[j]
            if k.mnemonic == "add" and len(k.operands) == 2 \
                    and k.operands[0].type == capstone.x86.X86_OP_REG \
                    and k.operands[0].reg == ptr \
                    and k.operands[1].type == capstone.x86.X86_OP_IMM:
                stride = k.operands[1].imm & 0xFFFFFFFF
            if k.mnemonic == "mov" and len(k.operands) == 2 \
                    and k.operands[0].type == capstone.x86.X86_OP_REG \
                    and k.reg_name(k.operands[0].reg) == "ecx" \
                    and k.operands[1].type == capstone.x86.X86_OP_IMM and count is None:
                count = k.operands[1].imm & 0xFFFFFFFF
            if stride and count:
                break
        if stride and count and 1 < count < 0x1000:
            regions.append((src.mem.disp, stride, count))
    return regions


def ctor_chain_check(info, chain):
    """Every loader-written offset should be initialised by SOME ctor in the
    chain, or by a pointer-walking clear loop.

    This is an INDEPENDENT line of evidence for the field tables: the loaders
    and the constructors are different functions reached from different call
    sites, so agreement between them cannot come from a shared parsing mistake.
    The expectation is deliberately not 100%; what matters is that every gap is
    NAMED as one of the mechanisms rather than absorbed.
    """
    per = {n: ctor_offsets(*CTORS[n]) for n in CTORS}
    loops = {n: loop_cleared_offsets(*CTORS[n]) for n in CTORS}
    order = [n for n, _, _, _ in chain]
    cumulative = set()
    for name in order:
        cumulative |= set(per.get(name, {}))
        if name not in [n for n, _, _, _ in chain[3:]]:
            continue
        rows = info[name]["rows"]
        written = {r["store_off"] for r in rows}
        unnamed = sorted(o for o in written if o not in cumulative)
        in_loop = []
        unexplained = []
        for o in unnamed:
            hit = [(b, st, c) for b, st, c in loops.get(name, [])
                   if b <= o < b + st * c]
            (in_loop if hit else unexplained).append((o, hit))
        print("  %-20s loader 写 %3d 个偏移  ctor 链覆盖 %3d  指针环清零 %3d  "
              "未解 %2d"
              % (name, len(written), len(written) - len(unnamed),
                 len(in_loop), len(unexplained)))
        # Which ctor covers what: own class vs an ancestor. A derived loader
        # writes BOTH its own fields and inherited ones (UnitTypeClass re-reads
        # SpeedType from TechnoTypeClass), and conflating the two hides who owns
        # the default value.
        own = set(per.get(name, {}))
        base_cover = {o for o in written if o in cumulative and o not in own}
        print("       归属：本类 ctor %d 个偏移，基类 ctor %d 个，"
              "指针环 %d 个，其他 %d 个"
              % (len(written & own), len(base_cover), len(in_loop),
                 len(written) - len(written & own) - len(base_cover) - len(in_loop)))
        for b, st, c in loops.get(name, []):
            n = sum(1 for o, _ in in_loop if b <= o < b + st * c)
            print("       清零环：基址 +0x%04X  步长 0x%02X  %d 项  -> 覆盖 %d 个字段偏移"
                  % (b, st, c, n))
        for o, _ in unexplained:
            keys = sorted(r["key"] for r in rows if r["store_off"] == o)
            print("       无 ctor 写：+0x%04X  %s" % (o, ",".join(keys)))


# --------------------------------------------------------------------------
# reporting


def main():
    print("=== TypeClass 继承链（slot25 = LoadFromINI，slot12 = GetSize）===")
    chain = []
    for name, vt, ld, sz in CHAIN:
        col_name = rtti_name(vt)
        slot25 = u32(vt + 25 * 4)
        slot12 = get_size(vt)
        col = u32(vt - 4)
        print("  %-20s vt=0x%08X  COL=0x%08X %-32s slot25=0x%08X size=%s"
              % (name, vt, col, col_name or "?", slot25,
                 ("0x%04X" % slot12) if slot12 else "0(stub)"))
        chain.append((name, vt, ld, sz))

    print("\n=== 每层 LoadFromINI 的边界与对象寄存器 ===")
    info = {}
    for name, vt, ld, sz in chain:
        end, last_ret = extent(ld)
        this = this_register(ld, 0x30000 if end is None else end)
        secbufs, rows = ([], [])
        if end is not None:
            this, secbufs, rows = recover(ld, end)
        print("  %-20s entry=0x%08X end=0x%08X size=0x%05X  this=%s  节名缓冲=%s  行=%d"
              % (name, ld, end or 0, (end or ld) - ld,
                 md.reg_name(this) if this is not None else "UNKNOWN",
                 ",".join("+0x%X(%s)" % (v, md.reg_name(k)) for k, v in secbufs.items()) or "-",
                 len(rows)))
        info[name] = {"end": end, "this": this, "secbufs": secbufs, "rows": rows,
                      "loader": ld, "vtable": vt, "declared": sz}

    print("\n=== 字段表 ===")
    for name, vt, ld, sz in chain:
        d = info[name]
        rows = d["rows"]
        if not rows:
            print("\n--- %s：无字段（%s）---" % (name, "抽象层" if sz == 0 else "解析失败"))
            continue
        print("\n--- %s  %d 键 ---" % (name, len(rows)))
        print("  %-26s %-9s %-10s %-9s %-13s %-3s %-6s %-8s %s"
              % ("键", "默认载入", "默认立即数", "存回", "读者", "宽", "INI", "节缓冲", "自检"))
        bad = 0
        imm_defaults = []
        for r in sorted(rows, key=lambda x: x["store_off"]):
            cons = r["default_off"] is not None and r["default_off"] == r["store_off"]
            if cons:
                mark = "一致"
            elif r["default_off"] is not None:
                mark = "跨字段(+0x%X)" % r["default_off"]
            elif r["default_imm"] is not None and not r["reader"].startswith("ReadString"):
                # Engine-designed literal default (`push -1` for Speed). Not a
                # failure: the key keeps that value when it is absent, and the
                # compiler needs exactly this number.
                mark = "立即数默认(%d)" % r["default_imm"]
                imm_defaults.append((r["key"], r["default_imm"]))
            elif r["reader"].startswith("ReadString") or r["reader"] == "ReadUnicodeString":
                mark = "栈缓冲默认"
            else:
                mark = "!! 默认=None"
                bad += 1
            # Section-buffer / INIClass agreement. The invariant is
            # ONE-DIRECTIONAL and it took a broken version to find out why:
            #
            #   +0x24  is the type's own name buffer (`[MTNK]`). That section
            #          name exists in BOTH files, so +0x24 legitimately appears
            #          with either INIClass. Requiring ART for it produced 20
            #          fake violations in TechnoTypeClass (AttackFriendlies, ROT,
            #          CanBeHidden, ...) -- 3 real +0x24/ART rows remain.
            #   +0x1F8 is the section selected by `Image=`; it is an artmd-only
            #          section by construction, so it must NEVER be read from the
            #          rules INIClass. Measured: 0 violations out of every
            #          +0x1F8 row in all seven classes.
            sec = r["section"]
            ini = r["ini"]
            if sec == 0x1F8 and ini == "RULES":
                mark += "  !!节/INI不符"
                bad += 1
            print("  %-26s %-9s %-10s %-9s %-13s %-3d %-6s %-8s %s"
                  % (r["key"] or "!!无键名",
                     ("-" if r["default_off"] is None else "+0x%04X" % r["default_off"]),
                     # an immediate default must be visible in the "default"
                     # column: leaving it "-" made four genuine engine defaults
                     # look like four parse failures
                     ("-" if r["default_imm"] is None else "imm=%d" % r["default_imm"]),
                     "+0x%04X" % r["store_off"], r["reader"], r["width"],
                     ini or "?", ("+0x%X" % sec) if sec else "?", mark))
        # hygiene: byte overlap. Two rows at the SAME offset are legitimate when
        # they are the same key read from two different sections -- BuildingType
        # reads Foundation from the artmd section selected by Image= and then
        # falls back to the type's own section, storing both into +0xEF0. That
        # is a two-source default, not a struct error, so same-key + same-offset
        # pairs are counted separately. Different keys at one offset is still an
        # error.
        seen = {}
        ov = 0
        dups = 0
        for r in rows:
            for b in range(r["store_off"], r["store_off"] + r["width"]):
                prev = seen.get(b)
                if prev is None:
                    seen[b] = r["key"]
                elif prev == r["key"]:
                    dups += 1
                else:
                    print("  !! 偏移重叠 0x%04X: %s 与 %s" % (b, prev, r["key"]))
                    ov += 1
        lo_off = min(r["store_off"] for r in rows)
        hi_off = max(r["store_off"] + r["width"] for r in rows)
        holes = [(a, b) for a, b in zip(sorted(seen), sorted(seen)[1:]) if b != a + 1]
        print("  小结：%d 键  覆盖 [+0x%04X,+0x%04X)  %d 字节  空洞 %d 段  "
              "默认缺失 %d  立即数默认 %d  同键双源 %d  %s"
              % (len(rows), lo_off, hi_off, hi_off - lo_off, len(holes), bad,
                 len(imm_defaults), dups,
                 "全部通过" if bad == 0 and ov == 0 else "见上"))
        for k, v in imm_defaults:
            print("     立即数默认：%s = %d" % (k, v))

    print("\n=== 跨层偏移复合检查 ===")
    # Every concrete class's loader delegates to TechnoType's, so the concrete
    # class's own offsets should all lie ABOVE the base class's highest field.
    # Offsets are PER-CLASS, so a violation is a real question, not an error:
    # BuildingTypeClass's `WaterBound` sits at +0x67C, inside TechnoTypeClass's
    # span, and it is a derived-class field that reuses an offset the base
    # happens not to have. What makes it legitimate is that the base class's
    # loader does NOT write +0x67C -- which is exactly the check below.
    base_hi = {}
    per = {}
    for name, vt, ld, sz in chain:
        rows = info[name]["rows"]
        per[name] = {r["store_off"] for r in rows}
        base_hi[name] = max((r["store_off"] + r["width"] for r in rows), default=0)
        print("  %-20s 最高字段止于 +0x%04X  声明尺寸 %s"
              % (name, base_hi[name], ("0x%04X" % sz) if sz else "n/a"))
    cumulative = set()
    base_keys = set()
    base_key_at = {}
    for name, vt, ld, sz in chain:
        base_keys |= {r["key"] for r in info[name]["rows"]}
        for r in info[name]["rows"]:
            base_key_at.setdefault(r["store_off"], r["key"])
        if name == "TechnoTypeClass":
            break
        cumulative |= per[name]
    cumulative |= per.get("TechnoTypeClass", set())
    for name, vt, ld, sz in chain[3:]:
        own = info[name]["rows"]
        if not own:
            continue
        below = [r for r in own if r["store_off"] < base_hi["TechnoTypeClass"]]
        # A base offset re-read by the derived loader under the SAME key is the
        # inherited field being loaded again, not a clash: UnitTypeClass reads
        # SpeedType at +0x67C, which is TechnoTypeClass's SpeedType. Excluding
        # those leaves only genuine derived-class keys occupying a base offset.
        clash = [r for r in below
                 if r["store_off"] in cumulative and r["key"] not in base_keys]
        inherited = [r for r in below if r["key"] in base_keys]
        print("  %-20s 自有 %d 键；低于 +0x%04X 的 %d 个（其中继承字段重读 %d 个），"
              "占用基类偏移的新键 %d 个 %s"
              % (name, len(own), base_hi["TechnoTypeClass"], len(below),
                 len(inherited), len(clash),
                 "OK" if not clash else
                 "△ " + ",".join("%s@+0x%X(基类同址=%s)"
                                 % (r["key"], r["store_off"],
                                    base_key_at.get(r["store_off"], "?"))
                                 for r in clash)))
        if sz and base_hi[name] >= sz:
            print("  !! %s 最高字段 +0x%04X 超出声明尺寸 0x%04X"
                  % (name, base_hi[name], sz))

    print()
    print("=== 构造器链独立交叉核对 ===")
    ctor_chain_check(info, chain)


main()
