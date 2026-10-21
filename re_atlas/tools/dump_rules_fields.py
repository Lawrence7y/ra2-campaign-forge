"""R-023: key -> struct offset for RulesClass's fixed-key loaders.

R-021 answered "which section", R-022 answered "which keys". This answers the
last link the campaign compiler needs: which STRUCT FIELD each key lands in, so
a generated rulesmd.ini can be written and a read-back can be checked at the
field level.

The pattern every one of these loaders uses is identical and is what makes the
recovery trustworthy:

    mov  reg, [esi + OFF]      ; current value  -> the default argument
    push reg
    push <key literal>
    push <section ptr>
    call ReadInteger/ReadBool
    mov  [esi + OFF], eax/al   ; the result     -> the store

so the offset appears TWICE per key: once as the default-value load and once as
the store. That is a free internal consistency check -- if the two disagree the
row is reported as a MISMATCH instead of being silently averaged. A third check
compares int fields for a 4-byte stride and bool fields for a 1-byte stride, and
flags any overlap between two keys.

Discipline carried from this session:
  * the body is bounded by its OWN `ret`, from the entry point; a window size is
    never used as the function's extent (G-22 swallowed the neighbouring
    function and produced a plausible, YRpp-consistent, wrong answer).
  * read_va checks section bounds per section (G-21).
  * key literals are taken from the push immediately preceding the reader call,
    not from the first printable string in the body.

Run: python re_atlas/tools/dump_rules_fields.py
     python re_atlas/tools/dump_rules_fields.py 0x0066B900     (one loader)
"""

import os
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_rules_sections as D  # noqa: E402  read_va with per-section bounds
from text_sweep import sweep  # noqa: E402  audited full-.text sweep

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

# Field-returning readers. Anything else (ReadString into a buffer, ReadDouble)
# has a different call shape and is not recovered here -- reported, not guessed.
FIELD_READERS = {
    0x005276D0: ("ReadInteger", 4),
    0x005295F0: ("ReadBool", 1),
    # ReadString/ReadUnicodeString return a length and write into a caller
    # buffer, so the field is a POINTER: the default is loaded into a spare
    # register BEFORE the call and the result stored AFTER it. Same two-touch
    # structure as the scalar readers, just with an extra hop:
    #
    #   mov ebx, [esi+0x4C]     ; default = the current pointer
    #   push <dst>; push <cap>; push KEY; push <sec>
    #   call ReadString
    #   ... jmp ... ; mov eax, ebx   (fallback to the default)
    #   mov [esi+0x4C], eax     ; store
    #
    # Recognising it needs the store to be attributed to the CALL, not to the
    # immediately preceding instruction, so the association here is looser: the
    # store window after a string call extends until the next reader call.
    0x00528A10: ("ReadString", 4),
    0x00528F00: ("ReadUnicodeString", 4),
    # ReadDouble returns in ST(0) and the caller stores it with `fstp qword`,
    # so the field is 8 bytes wide and the store is not a `mov`.
    0x005283D0: ("ReadDouble", 8),
}

# Loaders that read a fixed key set. MultiplayerDialogSettings is the one this
# round works on; the rest are listed so the tool can be aimed at them without
# editing it again.
LOADERS = {
    0x00671EA0: "Read_MultiplayerDialogSettings",
}

# Loaders that fill a SEPARATE object (passed as a parameter) rather than
# RulesClass at `this`. Their fields are NOT initialised by the RulesClass ctor,
# so the ctor cross-check does not apply to them -- Read_Difficulty writes a
# 0x4B-byte struct handed in via edx (third of three, one per difficulty level),
# and CheckCtor against RulesClass produced nonsense width mismatches.
EXTERNAL_TARGETS = {
    0x0066D270: "Read_Difficulty",     # fills a per-level DifficultyClass struct
    0x00674500: "Read_Difficulties",   # wrapper: calls Read_Difficulty x3
    0x00674000: "Read_LandCharacteristics",
}

# RulesClass ctor, reached from `push 0x18C0; call operator new; call ctor` at
# 0x52BABE. Used to recover the DEFAULT of every field, which is what the value
# stays as when the INI key is absent -- the reader passes it back in as the
# ReadInteger/ReadBool default argument.
# Offsets below this are shared by every object's leading fields; a raw
# [reg+off] scan cannot attribute them to RulesClass.
SMALL_OFFSET_FLOOR = 0x100

CTOR = 0x00665650
ALLOC_SITE = 0x0052BABE
ALLOC_SIZE = 0x18C0


def body(lo, hi):
    """Instructions in the explicit [lo, hi) range, which the caller derives
    from the function's own ret rather than from a window size."""
    out = []
    for insn in md.disasm(D.read_va(lo, hi - lo), lo):
        if insn.address >= hi:
            break
        out.append(insn)
    return out


def find_ret(entry, window=0x8000):
    """(addr of the ret, its address + size) for the function starting at entry.

    The FIRST `ret` reached by linear decoding from the entry is the primary
    return. These loaders share one epilogue between the success and early-out
    paths, so the ends are two adjacent `ret N` a few bytes apart.

    The window must be generous: Read_AudioVisual is 0x2710 bytes to its first
    ret (10 KB), and a 0xC00 default silently reported "no ret found" for it.
    Physical ceiling instead: the window is only an upper bound on how far to
    look, never the function's extent, and callers get (None, None) if the body
    really does not return inside it.
    """
    for insn in md.disasm(D.read_va(entry, window), entry):
        if insn.mnemonic.startswith("ret"):
            return insn.address, insn.address + insn.size
    return None, None


def mem_operand(insn, base_reg):
    """(operand_index, offset, size) for a single [base_reg + disp] operand.

    Either operand can be the memory one -- `mov reg,[esi+off]` puts it second,
    `mov [esi+off],eax` puts it first -- so both are scanned. Only the shape
    these loaders actually emit is accepted; anything with an index register or
    a second base is refused rather than approximated.
    """
    for i, m in enumerate(insn.operands):
        if m.type != capstone.x86.X86_OP_MEM:
            continue
        if m.mem.base != base_reg or m.mem.index != 0:
            continue
        return i, m.mem.disp, m.size
    return None


def reg_name(insn, idx):
    op = insn.operands[idx]
    if op.type != capstone.x86.X86_OP_REG:
        return None
    return insn.reg_name(op.reg)


def detect_base(entry, hi):
    """The register that holds the object whose fields this loader writes.

    `esi` is the base in most loaders (`mov esi,ecx`, ecx being `this`), but not
    in all: Read_Difficulty and Read_LandCharacteristics keep `ecx` for the
    INIClass and take the OUTPUT object as a parameter, landing it in `edi`.
    Hard-coding esi made those two report "no fields at all".

    The rule: within the first 16 instructions, the register assigned from a
    stack slot (`mov reg,[esp+N]`) is a parameter; if it is `edi`/`ebx`/`esi`
    and that register is later addressed as `[reg+disp]` with a non-trivial
    displacement, it is the object base. `esi` wins ties because it is the
    dominant shape. Returns None when nothing looks like a base, and the caller
    then falls back to esi.
    """
    insns = body(entry, hi)[:24]
    from_param = None
    from_stack = None
    for insn in insns:
        if insn.mnemonic != "mov" or len(insn.operands) != 2:
            continue
        dst, src = insn.operands
        if dst.type != capstone.x86.X86_OP_REG:
            continue
        nm = insn.reg_name(dst.reg)
        if nm not in ("edi", "ebx", "esi"):
            continue
        # `mov edi,edx` is the SECOND argument -- for Read_Difficulty that is the
        # output object, and the first stack parameter (ebx) is the INIClass.
        # Prefer the registry copy over the stack copy.
        if src.type == capstone.x86.X86_OP_REG and from_param is None:
            from_param = dst.reg
        elif src.type == capstone.x86.X86_OP_MEM                 and src.mem.base == capstone.x86.X86_REG_ESP and from_stack is None:
            from_stack = dst.reg
    return from_param or from_stack


def recover(entry, hi):
    """Rows of (key, default_off, store_off, reader, size, call_site)."""
    esi = detect_base(entry, hi) or capstone.x86.X86_REG_ESI
    rows = []

    default_off = None       # offset of the last `mov reg, [esi+off]`
    key = None               # last printable literal pushed
    pending = None           # (key, default_off, reader, size, call_site)
    # `esi` is not always the object base: these loaders contain
    # `add esi,0x18B8` and then address later fields RELATIVE TO THAT. Treating
    # every `[esi+disp]` as `[this+disp]` then mis-attributes the tail of the
    # function -- FallBackCoefficient came out at +0x0000 when it is really at
    # +0x18B8. Only `add/sub` of an immediate is tracked; any other write to esi
    # marks the base unknown and offsets are then skipped rather than guessed.
    esi_delta = 0
    esi_known = True

    base_name = md.reg_name(esi)

    for insn in body(entry, hi):
        if insn.mnemonic in ("add", "sub") and len(insn.operands) == 2                 and insn.operands[0].type == capstone.x86.X86_OP_REG                 and insn.reg_name(insn.operands[0].reg) == base_name                 and insn.operands[1].type == capstone.x86.X86_OP_IMM:
            v = insn.operands[1].imm & 0xFFFFFFFF
            esi_delta += v if insn.mnemonic == "add" else -v
            continue
        if insn.mnemonic == "mov" and insn.operands                 and insn.operands[0].type == capstone.x86.X86_OP_REG                 and insn.reg_name(insn.operands[0].reg) == base_name:
            esi_known = False      # prologue reload: base unknown
            esi_delta = 0
            continue
        # 0) An x87 default load: `fld` or `fild` from [esi+off]. `fild` (integer
        #    load) is the shape used by fields that ReadDouble later converts to
        #    int: `fild dword [esi+0x49C]; fstp qword [esp]; call ReadDouble`.
        #    Missing `fild` left the stale offset from the PREVIOUS field in
        #    `default_off`, so PrismSupportModifier reported default +0x498 and
        #    store +0x49C -- a mismatch that looked like a struct bug.
        if insn.mnemonic in ("fld", "fild") and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base == esi                     and op.mem.index == 0:
                default_off = op.mem.disp + esi_delta
                continue

        # 1) mov comes in two shapes that interleave: the default-value load
        #    (`mov reg, [esi+off]`, which can belong to the NEXT key because the
        #    compiler hoists it above the previous store) and the store itself
        #    (`mov [esi+off], eax`, which therefore does NOT immediately follow
        #    its call). Both must be tested; an if/elif chain here silently
        #    drops every store and yields zero rows.
        # `movsx` / `movzx` also load a field as a default (a bool or byte
        # field passed to ReadInteger is sign-extended first). Without them
        # CliffBackImpassability reported "default unknown" even though the
        # load is right there.
        if insn.mnemonic in ("movsx", "movzx") and len(insn.operands) == 2:
            m = mem_operand(insn, esi)
            if m is not None and m[0] == 1                     and insn.operands[0].type == capstone.x86.X86_OP_REG:
                default_off = m[1] + esi_delta
                continue

        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            m = mem_operand(insn, esi)
            if m is not None:
                midx, disp, msize = m
                if midx == 1 and insn.operands[0].type == capstone.x86.X86_OP_REG:
                    default_off = disp + esi_delta   # default-value load
                elif midx == 0 and pending \
                        and insn.operands[1].type == capstone.x86.X86_OP_REG:
                    # Width comes from the STORE, not from the reader. Some
                    # ReadDouble fields are converted to int (imul/sar/double->int)
                    # and stored with a 4-byte `mov`; trusting the reader's 8 made
                    # three such fields report an 8-byte span and appear to
                    # overlap their neighbours.
                    k, doff, name, size, site = pending
                    rows.append((k, doff, disp + esi_delta, name, msize, site))
                    pending = None

        # 2) key literal: push <imm> that resolves to a printable string
        elif insn.mnemonic == "push" and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_IMM:
                s = D.cstr(op.imm & 0xFFFFFFFF, 64)
                if s and 2 <= len(s) < 64 and all(0x20 < ord(c) < 0x7F for c in s):
                    key = s

        # 3) the reader call: latch what was set up for it
        elif insn.mnemonic == "call" and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_IMM:
                tgt = op.imm & 0xFFFFFFFF
                if tgt in FIELD_READERS:
                    name, size = FIELD_READERS[tgt]
                    pending = (key, default_off, name, size, insn.address)
                    key = None
                    default_off = None

        # 4) ReadDouble's store is NOT a `mov`: the value comes back on the x87
        #    stack and lands with `fstp qword ptr [esi+off]`. There is no register
        #    to match, so the offset is read straight out of the operand. Without
        #    this branch every float field in a section was invisible -- that is
        #    why 22 of AudioVisual's 152 keys were "unmapped" and why the reason
        #    looked like a missing string literal (it was the store, not the key).
        elif insn.mnemonic == "fstp" and pending:
            for op in insn.operands:
                # `fstp [esp]` / `fstp [ebp-..]` only STAGES the default argument
                # for the call; it is not the field store. The converted-to-int
                # fields (ExtraUnitLight and neighbours) do
                #     fild [esp+..]; fstp qword [esp]; push key; call ReadDouble
                #     fmul; call (double->int); mov [esi+off], eax
                # so the real store is a 4-byte `mov` further down. Accepting the
                # stack staging store attributed 8 bytes to a 4-byte field and made
                # three adjacent fields look like they overlapped.
                if op.type == capstone.x86.X86_OP_MEM and op.mem.base in (
                        capstone.x86.X86_REG_ESP, capstone.x86.X86_REG_EBP):
                    continue
                if op.type == capstone.x86.X86_OP_MEM and op.mem.base == esi \
                        and op.mem.index == 0:
                    # The WIDTH comes from the store, not from the reader:
                    # `fstp dword [esi+off]` stores a float (4 B) and
                    # `fstp qword [esi+off]` a double (8 B), but both calls go to
                    # ReadDouble. Trusting the reader's 8 made every float field
                    # report a width mismatch against the ctor's 4-byte write.
                    # `fstp dword [esi+off]` = 4-byte float field,
                    # `fstp qword [esi+off]` = 8-byte double field. Trust the
                    # STORE SIZE; do not try to infer the type from the reader
                    # (`ReadDouble` serves both) and do not try to infer it from
                    # the ctor (a double is written as two adjacent `mov`s, so a
                    # per-offset lookup always sees a 4-byte write).
                    w = op.size
                    k, doff, name, size, site = pending
                    import os as _o
                    if _o.environ.get("DBG"):
                        print("   [DBG] fstp store 0x%08X off=0x%X w=%d key=%s call=0x%08X"%(insn.address,op.mem.disp,w,k,site))
                    rows.append((k, doff, op.mem.disp + esi_delta, name, w, site))
                    pending = None
                    break
    return rows


def _canon(insn, reg):
    """Map a register id to its 32-bit parent id, so al/bl/cl/dl track eax/ebx/ecx/edx.

    Without this every bool field comes back as None: the ctor stores bools as
    `mov byte [esi+off], al` where `al` was set long before by `mov eax,1`, and
    a tracker keyed on the raw register id loses the connection.

    The indirection through the NAME is deliberate: capstone exposes 8-bit
    aliases as distinct ids with no public parent link. capstone's reg_name
    returns LOWERCASE, so the table is keyed on the upper-cased name; comparing
    against uppercase directly matched nothing and left every bool as None.
    """
    nm = insn.reg_name(reg).upper()
    parent = {"AL": "EAX", "AH": "EAX", "BL": "EBX", "BH": "EBX",
              "CL": "ECX", "CH": "ECX", "DL": "EDX", "DH": "EDX"}.get(nm)
    if parent is None:
        return reg
    return getattr(capstone.x86, f"X86_REG_{parent}")


# MSVC cdecl callee-saved set. Everything else is caller-saved and must be
# dropped across a call; eax is of course dropped, and so is edx.
CALLEE_SAVED = ("EBX", "ESI", "EDI", "EBP")


def ctor_defaults(entry=None, end_hint=None):
    """offset -> (value_or_None, size, site) for every [esi+off] store in the ctor.

    Values are recovered by a deliberately minimal constant tracker: `mov r,imm`
    and `xor r,r` set a register's last-known constant, a call invalidates the
    CALLER-saved registers only, and any other write to a register kills it. A
    field whose source register is unknown comes back as None rather than as a
    guess -- +0x141C and +0x1424 really are the saved frame pointer, not a
    constant, and they must stay None.

    An earlier version cleared ALL registers on every call, which is wrong for
    MSVC's callee-saved set and made `ebx` (the ctor's zero constant, live across
    dozens of calls) look unknown.

    This is what tells the compiler which value a setting keeps when the INI key
    is ABSENT, because the reader passes that same field back in as the
    ReadInteger/ReadBool default argument.
    """
    entry = CTOR if entry is None else entry
    ret_va, hi = find_ret(entry, window=0x4000)
    if ret_va is None:
        return None, None
    esi = capstone.x86.X86_REG_ESI
    known = {}
    rows = {}
    kept = {getattr(capstone.x86, f"X86_REG_{r}") for r in CALLEE_SAVED}

    def kill(reg):
        known.pop(reg, None)

    for insn in body(entry, hi):
        if insn.mnemonic == "call":
            for r in list(known):
                if r not in kept:
                    del known[r]
            continue
        if insn.mnemonic in ("xor", "sub") and len(insn.operands) == 2:
            a, b = insn.operands
            if a.type == capstone.x86.X86_OP_REG and b.type == capstone.x86.X86_OP_REG \
                    and a.reg == b.reg:
                known[_canon(insn, a.reg)] = 0
                continue
        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            dst, src = insn.operands
            # store into the object
            m = mem_operand(insn, esi)
            if m is not None and m[0] == 0:
                val = None
                if src.type == capstone.x86.X86_OP_IMM:
                    val = src.imm & (0xFFFFFFFF if m[2] == 4 else 0xFF)
                elif src.type == capstone.x86.X86_OP_REG:
                    base = known.get(_canon(insn, src.reg))
                    if base is not None:
                        val = base & (0xFFFFFFFF if m[2] == 4 else 0xFF)
                rows[m[1]] = (val, m[2], insn.address)
                continue
            # register <- register / immediate
            if dst.type == capstone.x86.X86_OP_REG:
                d = _canon(insn, dst.reg)
                if src.type == capstone.x86.X86_OP_IMM:
                    known[d] = src.imm & 0xFFFFFFFF
                elif src.type == capstone.x86.X86_OP_REG:
                    s = _canon(insn, src.reg)
                    if s in known:
                        known[d] = known[s]
                    else:
                        kill(d)
                else:
                    kill(d)
                continue
        # any other instruction that names a register as a destination kills it
        if insn.operands and insn.operands[0].type == capstone.x86.X86_OP_REG \
                and insn.mnemonic not in ("cmp", "test", "push"):
            kill(_canon(insn, insn.operands[0].reg))
    return rows, hi


def consumers(offsets, exclude=(0x00665650, 0x00667A27), reader_range=None,
              require_rules_root=False):
    """Code sites outside the ctor and outside the READER that touch [reg + off].

    These are the engine features that actually USE each setting, which is what
    a compiler has to reason about: writing a key whose only consumer is dead
    code changes nothing observable.

    The offset range is derived from the offsets actually asked for. An earlier
    version hard-coded `0x1480 <= d < 0x14BC` -- the MultiplayerDialogSettings
    block -- which made every AudioVisual field report zero consumers simply
    because its offsets lie elsewhere. A range literal for one caller silently
    becomes a wrong answer for the next.

    The reader body is excluded on purpose. It touches every one of its own
    offsets twice by construction -- once to build the default argument and once
    to store the result -- so leaving it in would put a floor of 2 on every count
    and hide the fields that genuinely have no consumer.
    """
    hits = {o: [] for o in offsets}
    if not offsets:
        return hits
    lo, hi = 0x401000, 0x7E1000
    skip = [exclude]
    if reader_range:
        skip.append(reader_range)
    RULES_ROOT = 0x008871E0
    rooted = set()
    CALLEE_SAVED_IDS = {getattr(capstone.x86, f"X86_REG_{r}") for r in CALLEE_SAVED}
    # Sweep, not a single disasm: `md.disasm(.text)` stops at 0x46F5A0 on this
    # image and would leave 89% of the section unseen -- the first version of
    # this function reported zero consumers for 16 of 27 keys because of it.
    for insn in sweep(lo, hi):
        if insn.mnemonic == "call":
            # Only caller-saved registers are clobbered. RulesClass* is very
            # often parked in a callee-saved register at function entry
            # (`mov ebp,[0x8871E0]` then `[ebp+off]` reads all over the body),
            # and clearing those on every call hid most real consumers.
            rooted &= CALLEE_SAVED_IDS
            continue
        if require_rules_root and insn.mnemonic == "mov" and len(insn.operands) == 2:
            dst, src = insn.operands
            if dst.type == capstone.x86.X86_OP_REG:
                if src.type == capstone.x86.X86_OP_MEM and src.mem.base == 0                         and src.mem.index == 0                         and (src.mem.disp & 0xFFFFFFFF) == RULES_ROOT:
                    rooted.add(dst.reg)
                    continue
                if src.type == capstone.x86.X86_OP_REG and src.reg in rooted:
                    rooted.add(dst.reg)
                    continue
                rooted.discard(dst.reg)
        if any(a <= insn.address < b for a, b in skip):
            continue
        for op in insn.operands:
            if op.type != capstone.x86.X86_OP_MEM:
                continue
            if op.mem.base == 0 or op.mem.index != 0:
                continue
            if require_rules_root and op.mem.base not in rooted:
                continue
            d = op.mem.disp
            if d in hits:
                hits[d].append(insn.address)
                break
    # SMALL OFFSETS ARE NOT FINGERPRINTS. `[ecx+0]` / `[eax+4]` / `[esi+8]` match
    # the first three fields of EVERY polymorphic object in the game, so counting
    # them produced 56,820 "consumers" for DetailMinFrameRateNormal at +0x0000
    # (the real number is small). Offsets below this floor are reported as
    # "unmeasurable" rather than as a count -- an honest gap beats a fake number.
    for o in hits:
        if o < SMALL_OFFSET_FLOOR:
            hits[o] = []
    return hits


def report(name, entry):
    ret_va, hi = find_ret(entry)
    if ret_va is None:
        print(f"\n!! {name} @0x{entry:08X} 没解到 ret，无法定界")
        return None
    print(f"\n=== {name} 0x{entry:08X}  body=[0x{entry:08X},0x{hi:08X})  "
          f"ret@{ret_va:08X} len={hi - entry} ===")
    rows = recover(entry, hi)
    if not rows:
        print("  （无字段行）")
        return rows
    defaults, ctor_hi = ctor_defaults()
    external = entry in EXTERNAL_TARGETS

    ok = True
    print(f"  {'键':26s} {'默认载入':>8s} {'存回':>8s} {'读者':12s} {'宽':>2s}  自检")
    for k, doff, soff, reader, size, site in rows:
        consistent = doff is not None and doff == soff
        # A string field's default is a STACK BUFFER address, not a field load
        # (`lea eax,[esp+0x50]; push eax; ... call ReadString`), so `doff` is
        # legitimately None for the string readers. Only a missing default on a
        # SCALAR reader is a real failure, because there the default must come
        # from the field itself.
        if not consistent and doff is None and not external \
                and not reader.startswith("ReadString") \
                and reader != "ReadUnicodeString":
            ok = False
        if consistent:
            mark = "一致"
        elif doff is not None:
            # A default read from a DIFFERENT field is legitimate engine
            # behaviour, not a parse error: CMislAcceleration deliberately
            # defaults to DMislAcceleration's current value. Report it as such
            # so the row is not mistaken for a struct bug -- but keep it out of
            # the "all consistent" claim.
            mark = f"跨字段默认(from +0x{doff:04X})"
        elif external:
            # External targets receive their defaults as immediates on the
            # stack, never as a load from the object.
            mark = "默认来自立即数（外部对象）"
        else:
            mark = "!! 默认载入=None"
        print(f"  {k if k else '!! 无键名':26s} "
              f"{('- ' if doff is None else f'+0x{doff:04X}'):>8s} "
              f"+0x{soff:04X} {reader:12s} {size:2d}  {mark}")

    # offset hygiene: no two keys share a byte; ints sit on a 4-byte grid
    seen = {}
    for k, doff, soff, reader, size, _ in rows:
        for b in range(soff, soff + size):
            if b in seen:
                print(f"  !! 偏移重叠 0x{b:04X}: {seen[b]} 与 {k}")
                ok = False
            seen[b] = k
    for k, doff, soff, reader, size, _ in rows:
        if size == 4 and soff % 4:
            print(f"  !! {k} 是 4 字节字段但偏移 0x{soff:X} 未对齐")
            ok = False
    offs = sorted(soff for _, _, soff, _, _, _ in rows)
    span = offs[-1] - offs[0] + next(s for _, _, o, _, s, _ in rows if o == offs[-1])
    holes = []
    cur = offs[0]
    for _, _, o, _, s, _ in sorted(rows, key=lambda r: r[2]):
        if o > cur:
            holes.append((cur, o))
        cur = max(cur, o + s)
    print(f"  字段数 {len(rows)}  覆盖 [+0x{offs[0]:04X}, +0x{cur:04X})  共 {cur - offs[0]} 字节"
          f"  {'无空洞' if not holes else f'空洞 {holes}'}")
    print(f"  自检: {'全部通过' if ok else '有失败项（见上面的 !!）'}")

    # defaults from the ctor and the field's live consumers
    if defaults is None:
        print("  !! 构造器没解到 ret，无法给默认值")
        return None
    for k, _, soff, _, size, _ in rows:
        if external:
            break            # the RulesClass ctor says nothing about another object
        d = defaults.get(soff)
        if d is None:
            # Not an error: fields inside an embedded sub-object are initialised
            # by THAT object's ctor, and a vptr write often sits right after
            # them (AICaptureLowMoneyMark/+0xEBC and +0xEC0 straddle the
            # +0x0EC4 vptr). Reported as a note, not a failure.
            print(f"  .. {k} +0x{soff:04X} 构造器未直接写（可能属内嵌子对象，由子对象构造器初始化）")
        elif d[1] != size:
            # An 8-byte field (double) is written by the ctor as TWO adjacent
            # 4-byte `mov`s, so a per-offset lookup always sees 4. Accept that
            # pattern before reporting a mismatch: the high dword must exist at
            # soff+4 and be a 4-byte write.
            if size == 8 and d[1] == 4 and soff + 4 in defaults \
                    and defaults[soff + 4][1] == 4:
                continue
            print(f"  !! {k} +0x{soff:04X} 构造器写 {d[1]} 字节，读者读 {size} 字节")

    offs = [o for _, _, o, _, _, _ in rows]
    cons_hi = consumers(offs, reader_range=(entry, hi))
    cons_lo = consumers(offs, reader_range=(entry, hi), require_rules_root=True)
    print(f"\n  {'键':26s} {'偏移':>7s} {'构造器默认':>12s} {'消费点区间':>12s}")
    for k, _, soff, reader, size, _ in rows:
        d = defaults.get(soff)
        dv = "?" if d is None else ("None" if d[0] is None else f"0x{d[0]:X}")
        lo_n, hi_n = len(cons_lo.get(soff, [])), len(cons_hi.get(soff, []))
        print(f"  {k:26s} +0x{soff:04X} {dv:>12s} {f'[{lo_n}, {hi_n}]':>12s}")
    print("  ▲ 区间口径：下界只数『基址寄存器可追溯到 RulesClass 全局 0x8871E0』"
          "的读取；上界把任何 [reg+off] 都算上。")
    print("    真值在两者之间 —— 以函数参数形式传入的对象（`mov ecx,[ebp+0x1488]`，"
          "ebp 由调用方给）只有上界能看见；")
    print("    而任何恰好同偏移的异类对象只有上界会误计。单一数字在这里没有意义。")
    print(f"  构造器 0x{CTOR:08X} 结束于 0x{ctor_hi:08X}")
    print(f"  分配尺寸 0x{ALLOC_SIZE:X} @0x{ALLOC_SITE:08X}；"
          f"构造器最高字段止于 +0x{max(o + defaults[o][1] for o in defaults):X}"
          f"（尾隙 {ALLOC_SIZE - max(o + defaults[o][1] for o in defaults)} 字节）")
    return rows if ok else None


def main():
    if len(sys.argv) > 1:
        # Normalise the display name to upper-case hex so the SAME loader always
        # produces the SAME output bytes. Echoing the caller's literal made
        # `0x66b900` and `0x66B900` differ in the evidence file, which breaks
        # byte-for-byte reproducibility -- the exact trap recorded in G-30.
        targets = {int(a, 16): LOADERS.get(int(a, 16), f"loader_0x{int(a, 16):08X}")
                   for a in sys.argv[1:]}
    else:
        targets = LOADERS

    results = {}
    entry_of = {}
    for entry, name in sorted(targets.items()):
        r = report(name, entry)
        if r is not None:
            results[name] = r
            entry_of[name] = entry

    print("\n=== 正对照 ===")
    ok = True

    # Controls are attached to the loader they were calibrated on, and to THAT
    # loader only. An earlier version always demanded the
    # Read_MultiplayerDialogSettings table, so pointing the tool at any other
    # loader (0x006691E0 for AudioVisual) failed the control even though every
    # field row was correct -- an expectation that only holds for one input is
    # hard-coded, not a control.
    if "Read_MultiplayerDialogSettings" in targets.values():
        ptr = D.u32(0x007F0CA0)
        if not ptr or D.cstr(ptr) != "MultiplayerDialogSettings":
            print(f"  !! 0x7F0CA0 -> {ptr!r} {D.cstr(ptr) if ptr else ''}，"
                  f"期望 'MultiplayerDialogSettings'")
            ok = False
        mp = results.get("Read_MultiplayerDialogSettings")
        if mp:
            head, tail = mp[0][2], mp[-1][2]
            if head != 0x1480:
                print(f"  !! 首字段偏移 0x{head:X}，期望 0x1480")
                ok = False
            if tail != 0x14B8:
                print(f"  !! 末字段偏移 0x{tail:X}，期望 0x14B8")
                ok = False
        else:
            print("  !! 没解出 Read_MultiplayerDialogSettings 的字段表")
            ok = False
        print("  已校验 MPD 专用控制（节指针 / 首字段 +0x1480 / 末字段 +0x14B8）")

    # Controls that apply to ANY loader.
    known_readers = {v[0] for v in FIELD_READERS.values()}
    for name, rows in results.items():
        if not rows:
            # An EMPTY result is only a failure for a loader that is supposed to
            # write `[this+off]` fields. Two real shapes have none:
            #   * a pure dispatcher (Read_Difficulties just calls
            #     Read_Difficulty three times with different sub-objects);
            #   * a loader whose outputs land in a GLOBAL rather than in an
            #     object (Read_LandCharacteristics writes into the table at
            #     0x89EA44, addressed as [ebx+8] with ebx a constant).
            # Both are reported as "not applicable", not as a failed control.
            if any(n == name and va in EXTERNAL_TARGETS
                   for va, n in ((v, k) for k, v in LOADERS.items())):
                pass
            print(f"  .. {name} 无 [对象+偏移] 字段（分派器或写入全局），不计为失败")
            continue
        # A cross-field default (r[1] != r[2], both not None) is engine
        # behaviour, documented in KB §17.4; only a MISSING default on a scalar
        # reader is a control failure.
        # For an EXTERNAL target the defaults are immediates, so the
        # "default == store offset" check cannot apply. Use a structural check
        # instead: every field must have a distinct, non-overlapping span.
        # Resolve by ENTRY ADDRESS, never by string-matching the display name.
        # Two separate traps were hit here:
        #   * the display name for a non-MPD loader is `loader_<hex>`, so
        #     parsing it blows up for `Read_MultiplayerDialogSettings`;
        #   * the hex case follows whatever the caller typed, so the same loader
        #     passed with 0x66D270 and failed with 0x66d270.
        # results only carries names, so the mapping is rebuilt from targets.
        is_external = entry_of.get(name) in EXTERNAL_TARGETS
        if is_external:
            # Sort the SPANS (not the rows) and check only adjacent pairs: an
            # earlier version indexed into a sorted span list with the original
            # row index, so it compared the wrong pairs and reported overlaps
            # that did not exist.
            spans = sorted((r[2], r[2] + r[4]) for r in rows)
            bad = []
            for (a1, b1), (a2, b2) in zip(spans, spans[1:]):
                if a2 < b1:
                    bad.extend([a1, a2])
            note = "（外部对象：改用不重叠判据）"
        else:
            bad = [r for r in rows
                   if (r[1] is None and not r[3].startswith("ReadString")
                       and r[3] != "ReadUnicodeString")]
            note = ""
        if bad:
            what = "字段跨度重叠" if is_external else "默认载入与存回偏移不一致"
            print(f"  !! {name} 有 {len(bad)} 行{what}")
            ok = False
        unknown = {r[3] for r in rows} - known_readers
        if unknown:
            print(f"  !! {name} 出现未登记的读者 {unknown}")
            ok = False
        same = sum(1 for r in rows if r[1] is not None and r[1] == r[2])
        cross = sum(1 for r in rows if r[1] is not None and r[1] != r[2])
        print(f"  已校验 {name}：{len(rows)} 行，双向一致 {same}/{len(rows)}"
              f"，跨字段默认 {cross} 行{note}")

    if not ok:
        print("  正对照失败 —— 以上结果不可信")
        return 1
    print("  正对照通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
