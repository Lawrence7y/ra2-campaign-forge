"""R-028 claims gate: independent re-derivation of the TypeClass field tables.

This does NOT import dump_typeclass_fields.py and does not reuse its state
machine. The original walks the loader forward keeping a `pending` tuple and
resolves the store on the fly. This gate anchors on the *reader call sites*
instead: collect every call to a real reader (or a cdecl wrapper that wraps
one), then for each site look FORWARD to the next reader site and take the
first `[this+disp]` store in that window. The two designs fail differently,
which is the point -- a store/first-reader ordering bug that fools one will
usually not fool the other.

Every check asserts a VALUE (count, offset, class name, byte sequence), not the
existence of an instruction. R-021 lost a whole conclusion to a
"cmp eax,5 exists" style assertion that was direction-blind.

Run: python re_atlas/tools/verify_r028_claims.py
Exit 0 only when every positive control passes and every control behaves.
"""

import os
import re
import struct
import sys

import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE = 0x400000

# (name, rva, vsize, rawptr, rawsize) -- only disk-backed sections map by
# VA - 0x400000; .data ends at 0x87E000 and anything above is BSS (no bytes).
SECTIONS = [
    (".text", 0x001000, 0x3DF38D, 0x001000, 0x3E0000),
    (".rdata", 0x3E1000, 0x030074, 0x3E1000, 0x031000),
    (".data", 0x412000, 0x367BE4, 0x412000, 0x06C000),
]
TEXT_LO, TEXT_HI = 0x401000, 0x7E1000
RDATA_LO, RDATA_HI = 0x7E1000, 0x811074

INI_ART = 0x00887180
SECNAME = (0x24, 0x1F8)

READERS = {
    0x005276D0: ("ReadInteger", 4),
    0x005295F0: ("ReadBool", 1),
    0x00528A10: ("ReadString", 4),
    0x00528F00: ("ReadUnicodeString", 4),
    0x005283D0: ("ReadDouble", 8),
}

# name, vtable, LoadFromINI, GetSize immediate (0 = abstract stub)
CHAIN = [
    ("AbstractTypeClass", 0x007E2000, 0x00410A60, 0x0000),
    ("ObjectTypeClass",   0x007EF2D8, 0x005F92D0, 0x0000),
    ("TechnoTypeClass",   0x007F4ED8, 0x00712170, 0x0000),
    ("InfantryTypeClass", 0x007EB610, 0x005240A0, 0x0ED0),
    ("UnitTypeClass",     0x007F6218, 0x00747620, 0x0E78),
    ("AircraftTypeClass", 0x007E2868, 0x0041CC20, 0x0E10),
    ("BuildingTypeClass", 0x007E4570, 0x0045FE50, 0x1798),
]

# The delegation edge each loader must have as its first call into .text.
DELEGATES = {
    "ObjectTypeClass":   0x00410A60,
    "TechnoTypeClass":   0x005F92D0,
    "InfantryTypeClass": 0x00712170,
    "UnitTypeClass":     0x00712170,
    "AircraftTypeClass": 0x00712170,
    "BuildingTypeClass": 0x00712170,
}

# Expected object register, read from each loader's prologue.
THIS_REG = {
    "AbstractTypeClass": "ebx",
    "ObjectTypeClass":   "ebx",
    "TechnoTypeClass":   "ebp",
    "InfantryTypeClass": "esi",
    "UnitTypeClass":     "edi",
    "AircraftTypeClass": "esi",
    "BuildingTypeClass": "ebp",
}

# Expected table sizes asserted by the delivery (R-028 / kb/30 19.2).
# What R-028 DELIVERED (kb/30 19.2). Kept separate from what this gate MEASURES,
# because the two disagree and the disagreement is the finding.
DELIVERED = {
    "AbstractTypeClass": (1, 1, 0),
    "ObjectTypeClass":   (20, 15, 5),
    "TechnoTypeClass":   (252, 230, 22),
    "InfantryTypeClass": (33, 28, 5),
    "UnitTypeClass":     (27, 15, 12),
    "AircraftTypeClass": (10, 6, 4),
    "BuildingTypeClass": (270, 119, 151),
}
DELIVERED_TOTAL = (613, 414, 199)

# What this gate measures with the this-register-aware `fstp` handler.
# The delta vs DELIVERED is exactly the ReadDouble rows the original tool drops:
# its `fstp` branch treats `base in (ESP, EBP)` as "staging the default argument",
# but TechnoTypeClass and BuildingTypeClass keep `this` in EBP, so every
# `fstp [ebp+off]` field store in those two classes is discarded silently.
MEASURED = {
    "AbstractTypeClass": (1, 1, 0),
    "ObjectTypeClass":   (20, 15, 5),
    "TechnoTypeClass":   (276, 255, 21),
    "InfantryTypeClass": (33, 28, 5),
    "UnitTypeClass":     (27, 15, 12),
    "AircraftTypeClass": (10, 6, 4),
    "BuildingTypeClass": (277, 126, 151),
}
MEASURED_TOTAL = (644, 446, 198)

# Rows present in MEASURED but not in the delivered table, and why. All 31 are
# ReadDouble, and every one is independently confirmed by the class's own
# constructor writing a default at the same offset (checked in P12).
EXPECTED_EXTRA_DOUBLES = 31

# Key reads that land in an inline char[] rather than a scalar field. Outside the
# scope of both tables (see P11d).
EXPECTED_NO_STORE_KEYS = 153

# Constructors: entry, end, and the ctor the first call must reach.
#
# 0x5F7090, not 0x5F7320, is ObjectTypeClass's ctor as reached from
# TechnoTypeClass. BOTH store `mov [reg],0x7EF2D8` (0x5F7251 and 0x5F73D9) and
# both have ObjectTypeClass's field-reset shape, so the delivery's claim
# "TechnoType's first call is ObjectType 0x5F7320" is off by one function: the
# real chain is BuildingType 0x45DD90 -> TechnoType 0x710AF0 -> ObjectType
# 0x5F7090 -> AbstractType 0x410800. 0x5F7320 is a second ctor of the same class
# reached from elsewhere (18 direct E8 callers); it is not on this chain.
CTORS = {
    "ObjectTypeClass":   (0x005F7090, 0x005F7317, 0x00410800),
    "TechnoTypeClass":   (0x00710AF0, 0x0071183E, 0x005F7090),
    "InfantryTypeClass": (0x005236A0, 0x00523979, 0x00710AF0),
    "UnitTypeClass":     (0x007470D0, 0x007472B7, 0x00710AF0),
    "AircraftTypeClass": (0x0041C8B0, 0x0041C9E8, 0x00710AF0),
    "BuildingTypeClass": (0x0045DD90, 0x0045E512, 0x00710AF0),
}

with open(EXE, "rb") as fh:
    BLOB = fh.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

RESULTS = []


def record(tag, ok, detail):
    RESULTS.append((tag, ok, detail))
    print("  [%s] %-6s %s" % ("PASS" if ok else "FAIL", tag, detail))


# --------------------------------------------------------------------------
# image primitives (per-section bounds; BSS returns b"")


def read_va(va, n):
    rva = va - IMAGE_BASE
    for _name, s_rva, s_vsize, raw_ptr, raw_size in SECTIONS:
        if s_rva <= rva < s_rva + max(s_vsize, raw_size):
            d = rva - s_rva
            if d >= raw_size:
                return b""
            return BLOB[raw_ptr + d: raw_ptr + d + n]
    return b""


def u32(va):
    b = read_va(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None


def cstr(va, n=64):
    b = read_va(va, n)
    return b.split(b"\x00")[0].decode("latin1")


def rtti_name(vtable_va):
    col = u32(vtable_va - 4)
    if col is None or not (RDATA_LO <= col < RDATA_HI):
        return None
    td = u32(col + 0xC)
    if td is None:
        return None
    nm = cstr(td + 8, 96)
    return nm if nm.startswith(".?AV") else None


def slot12_size(vtable_va):
    fn = u32(vtable_va + 12 * 4)
    if fn is None:
        return None
    ins = list(md.disasm(read_va(fn, 12), fn))[:2]
    if len(ins) == 2 and ins[0].mnemonic == "mov" and ins[1].mnemonic.startswith("ret"):
        o = ins[0].operands
        if len(o) == 2 and o[0].type == capstone.x86.X86_OP_REG \
                and ins[0].reg_name(o[0].reg) == "eax" \
                and o[1].type == capstone.x86.X86_OP_IMM:
            return o[1].imm & 0xFFFFFFFF
    return None


def extent(entry, window=0x30000):
    """[entry, terminal_ret) -- a ret whose successor is padding."""
    last = None
    for insn in md.disasm(read_va(entry, window), entry):
        last = insn
        if insn.mnemonic.startswith("ret"):
            b = read_va(insn.address + insn.size, 2)
            if len(b) == 2 and b[0] in (0xCC, 0x90) and b[1] in (0xCC, 0x90):
                return insn.address + insn.size
    return (last.address + last.size) if last else entry


def insns_of(entry, end):
    return list(md.disasm(read_va(entry, end - entry), entry))


# --------------------------------------------------------------------------
# wrappers: cdecl helper that calls a real reader and pops >= 8 bytes itself

_WRAP = {}


def is_wrapper(fn):
    if fn in _WRAP:
        return _WRAP[fn]
    ok = False
    if TEXT_LO <= fn < TEXT_HI:
        end = extent(fn, 0x2000)
        inner = False
        retimm = None
        for insn in insns_of(fn, end):
            if insn.mnemonic == "call" and insn.operands \
                    and insn.operands[0].type == capstone.x86.X86_OP_IMM:
                if (insn.operands[0].imm & 0xFFFFFFFF) in READERS:
                    inner = True
            if insn.mnemonic.startswith("ret") and insn.operands:
                retimm = insn.operands[0].imm
        ok = inner and retimm is not None and retimm >= 8
    _WRAP[fn] = ok
    return ok


# --------------------------------------------------------------------------
# the site-anchored parser


def prologue_this(insns, limit=64):
    """The single `mov reg, ecx` in the prologue before any call."""
    hits = []
    for insn in insns:
        if insn.address - insns[0].address > limit:
            break
        if insn.mnemonic == "call":
            break
        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            d, s = insn.operands
            if d.type == capstone.x86.X86_OP_REG and s.type == capstone.x86.X86_OP_REG \
                    and insn.reg_name(s.reg) == "ecx":
                hits.append(insn.reg_name(d.reg))
    return hits


def parse(entry, end, force_this=None):
    """Return dict(this=..., rows=[...], reader_sites=n, ambiguous=...)."""
    insns = insns_of(entry, end)

    this_name = force_this
    if this_name is None:
        hits = prologue_this(insns)
        this_name = hits[0] if hits else None
    reg_this = None
    if this_name is not None:
        reg_this = getattr(capstone.x86, "X86_REG_" + this_name.upper())

    # reg -> ('IMM', v) | ('STACK',) for the INIClass selection
    regval = {}
    for insn in insns:
        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            d, s = insn.operands
            if d.type == capstone.x86.X86_OP_REG:
                if s.type == capstone.x86.X86_OP_MEM and s.mem.base in (
                        capstone.x86.X86_REG_ESP, capstone.x86.X86_REG_EBP):
                    regval[d.reg] = ("STACK",)
                elif s.type == capstone.x86.X86_OP_IMM:
                    regval[d.reg] = ("IMM", s.imm & 0xFFFFFFFF)
                elif s.type == capstone.x86.X86_OP_REG:
                    regval[d.reg] = regval.get(s.reg)
                else:
                    regval.pop(d.reg, None)

    # string literals pushed (candidate keys) with the instruction index
    pushes = []
    for idx, insn in enumerate(insns):
        if insn.mnemonic != "push" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type != capstone.x86.X86_OP_IMM:
            continue
        va = op.imm & 0xFFFFFFFF
        s = cstr(va, 64)
        if s and 2 <= len(s) < 64 and all(0x20 < ord(c) < 0x7F for c in s):
            pushes.append((idx, va, s))

    # reader call sites
    sites = []
    for idx, insn in enumerate(insns):
        if insn.mnemonic != "call" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type != capstone.x86.X86_OP_IMM:
            continue
        tgt = op.imm & 0xFFFFFFFF
        if tgt in READERS:
            sites.append((idx, READERS[tgt][0], tgt))
        elif is_wrapper(tgt):
            sites.append((idx, "WRAP_0x%08X" % tgt, tgt))

    rows = []
    for n, (idx, rname, tgt) in enumerate(sites):
        call_insn = insns[idx]
        prev_idx = sites[n - 1][0] if n else -1
        next_idx = sites[n + 1][0] if n + 1 < len(sites) else len(insns)

        # key: nearest printable literal push in (prev site, this site)
        key = key_va = None
        for pidx, pva, ps in pushes:
            if prev_idx < pidx < idx:
                key, key_va = ps, pva

        # INIClass: last `mov ecx, src` in (prev site, this site]
        ini = None
        ini_src = None
        for j in range(prev_idx + 1, idx + 1):
            k = insns[j]
            if k.mnemonic != "mov" or len(k.operands) != 2:
                continue
            d, s = k.operands
            if d.type != capstone.x86.X86_OP_REG or k.reg_name(d.reg) != "ecx":
                continue
            if s.type == capstone.x86.X86_OP_IMM:
                ini = "ART" if (s.imm & 0xFFFFFFFF) == INI_ART else "RULES"
                ini_src = "IMM"
            elif s.type == capstone.x86.X86_OP_REG:
                v = regval.get(s.reg)
                if v == ("STACK",):
                    ini = "RULES"
                    ini_src = "STACK"
                elif v and v[0] == "IMM" and v[1] == INI_ART:
                    ini = "ART"
                    ini_src = "IMM"
                else:
                    ini = "RULES"
                    ini_src = "STACK"
            elif s.type == capstone.x86.X86_OP_MEM:
                ini = "RULES"
                ini_src = "STACK"
        if ini is None:
            # Caller-supplied INIClass. Which stack slot it came from cannot be
            # resolved by linear esp tracking here: the function keeps esp
            # moving between blocks and some callees are caller-clean while
            # others `ret N`. Measured both ways the same site comes out as
            # arg0 and as arg1+ under different trackers, so this is recorded
            # as STACK (unresolved) rather than asserted either way.
            ini = "RULES"
            ini_src = "STACK"

        # store: first `[this+disp]` write in (this site, next site)
        store_off = width = None
        for j in range(idx + 1, next_idx):
            k = insns[j]
            tgt_mem = None
            if k.mnemonic in ("mov", "fstp", "fst", "movsd", "movss") and k.operands:
                # write = destination is memory
                if k.mnemonic in ("fstp", "fst", "movsd", "movss"):
                    tgt_mem = k.operands[-1] if k.mnemonic in ("fstp", "fst") else k.operands[0]
                else:
                    if len(k.operands) == 2 and k.operands[0].type == capstone.x86.X86_OP_MEM:
                        tgt_mem = k.operands[0]
            if tgt_mem is None or tgt_mem.type != capstone.x86.X86_OP_MEM:
                continue
            if tgt_mem.mem.base != reg_this or tgt_mem.mem.index != 0:
                continue
            if tgt_mem.mem.disp in SECNAME:
                continue
            store_off = tgt_mem.mem.disp
            width = tgt_mem.size
            break

        rows.append({"key": key, "key_va": key_va, "store_off": store_off,
                     "width": width, "reader": rname, "ini": ini,
                     "ini_src": ini_src, "site": call_insn.address})

    return {"this": this_name, "rows": rows, "reader_sites": len(sites)}


# --------------------------------------------------------------------------
# evidence cross-check


def parse_evidence(path):
    """Rows from the delivered table: (class, key, store_off, width, ini)."""
    out = {}
    cur = None
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = re.match(r"^--- (\w+)\s+(\d+) 键 ---", line.strip())
            if m:
                cur = m.group(1)
                out[cur] = []
                continue
            if cur is None or not line.startswith("  ") or "小结" in line:
                continue
            # The 节缓冲 column is `+0x24` / `+0x1F8` / `?` (unresolved lease).
            # An earlier version of this gate required `+0x…|-` and therefore
            # silently dropped 107 TechnoTypeClass rows, which then showed up as
            # a 107-row "mismatch" against the delivery. Rejecting an unknown
            # marker is fine; silently dropping the row is not.
            m = re.match(
                r"^\s{2}(\S+)\s+(\S+)\s+(\S+)\s+(\+0x[0-9A-Fa-f]+|-)\s+(\S+)\s+(\d+)\s+"
                r"(RULES|ART)\s+(\+0x[0-9A-Fa-f]+|-|\?)\s*(.*)$", line.rstrip("\n"))
            if not m:
                continue
            key, dload, dimm, store, reader, width, ini, secbuf, note = m.groups()
            if store == "-":
                continue
            out[cur].append({
                "key": key if key != "!!无键名" else None,
                "store_off": int(store, 16),
                "width": int(width),
                "ini": ini,
            })
    return out


# --------------------------------------------------------------------------


def main():
    print("=== R-028 claims gate (independent re-derivation) ===")
    print("  exe sha256 = %s" % __import__("hashlib").sha256(BLOB).hexdigest())

    # ---- P1: chain identity from RTTI + slot 25 + slot 12
    print("\n--- P1 chain identity ---")
    for name, vt, ld, size in CHAIN:
        col_name = rtti_name(vt)
        slot25 = u32(vt + 25 * 4)
        got_size = slot12_size(vt)
        ok = (col_name == ".?AV%s@@" % name and slot25 == ld
              and (got_size == size if size else got_size is None))
        record("P1/%-19s" % name, ok,
               "COL=%s slot25=0x%08X(exp 0x%08X) slot12=%s(exp %s)"
               % (col_name, slot25 or 0, ld,
                  "0x%04X" % got_size if got_size else "stub",
                  "0x%04X" % size if size else "stub"))

    # ---- P2: delegation edge is called in the loader's first 20 instructions.
    # Not "the first call": every one of these loaders opens with a call to the
    # tiny `xor eax,eax; mov [ecx+4],eax; mov [ecx+8],eax; ret` field-reset
    # helper at 0x526B00, which is NOT a base-class loader. The delivery claims
    # "each of the seven loaders calls its base loader in its first few
    # instructions"; measured, the base call is call #9..#12.
    print("\n--- P2 delegation (base call inside first 20 instructions) ---")
    for name, base in DELEGATES.items():
        entry = dict((n, l) for n, _v, l, _s in CHAIN)[name]
        end = extent(entry)
        head = insns_of(entry, end)[:20]
        pos = [k for k, insn in enumerate(head)
               if insn.mnemonic == "call" and insn.operands
               and insn.operands[0].type == capstone.x86.X86_OP_IMM
               and (insn.operands[0].imm & 0xFFFFFFFF) == base]
        record("P2/%-19s" % name, len(pos) == 1,
               "base call at index %s of first 20 (exp one hit)" % pos)

    # ---- P3: object register from the prologue
    print("\n--- P3 object register ---")
    for name, _vt, ld, _s in CHAIN:
        insns = insns_of(ld, extent(ld))
        hits = prologue_this(insns)
        record("P3/%-19s" % name, hits == [THIS_REG[name]],
               "prologue mov reg,ecx = %s (exp [%s])" % (hits, THIS_REG[name]))

    # ---- P4: INI_Art identity (write site, not a direct vptr read: it is BSS)
    print("\n--- P4 INI_Art identity ---")
    reads = len(read_va(INI_ART, 4))
    writes = []
    pat = b"\xc7\x05" + struct.pack("<I", INI_ART) + b"(.{4})"
    for m in re.finditer(pat, BLOB, re.S):
        # map file offset -> VA for .text only
        fo = m.start()
        if 0x1000 <= fo < 0x1000 + 0x3E0000:
            writes.append((0x400000 + fo, struct.unpack("<I", m.group(1))[0]))
    col = u32(0x007E1AF4 - 4)
    art_name = cstr(u32(col + 0xC) + 8, 96) if col else ""
    ok = (reads == 0 and len(writes) == 1 and writes[0][1] == 0x007E1AF4
          and art_name == ".?AVCCINIClass@@")
    record("P4/iniart", ok,
           "BSS bytes=%d  writes=%s  COL(0x7E1AF4)=%s"
           % (reads, ["0x%08X<-0x%08X" % w for w in writes], art_name))

    # ---- P5: per-class tables. Two separate assertions:
    #   P5a  the gate reproduces its OWN measured values (regression lock), and
    #   P5b  the measured values differ from the delivery by exactly the set of
    #        ReadDouble rows, which is the finding. P5b is not a "fail" -- it
    #        asserts the DEFECT SHAPE, so it goes red if the gap ever changes
    #        without an explanation being added here.
    print("\n--- P5 tables and counts ---")
    parsed = {}
    for name, _vt, ld, _s in CHAIN:
        end = extent(ld)
        p = parse(ld, end)
        parsed[name] = p
        known = [r for r in p["rows"] if r["key"] and r["store_off"] is not None]
        n_rules = sum(1 for r in known if r["ini"] == "RULES")
        n_art = sum(1 for r in known if r["ini"] == "ART")
        got = (len(known), n_rules, n_art)
        exp = MEASURED[name]
        rec = sum(1 for r in known if r["reader"] == "ReadDouble")
        dl = DELIVERED[name][0]
        record("P5/%-19s" % name, got == exp,
               "keys=%d rules=%d art=%d (measured %d/%d/%d) ReadDouble=%d "
               "delivered_keys=%d delta=%+d"
               % (got + exp + (rec, dl, got[0] - dl)))

    tot = sum(len([r for r in parsed[n]["rows"] if r["key"] and r["store_off"] is not None])
              for n, _v, _l, _s in CHAIN)
    tot_rules = sum(1 for n, _v, _l, _s in CHAIN for r in parsed[n]["rows"]
                    if r["key"] and r["store_off"] is not None and r["ini"] == "RULES")
    tot_art = sum(1 for n, _v, _l, _s in CHAIN for r in parsed[n]["rows"]
                  if r["key"] and r["store_off"] is not None and r["ini"] == "ART")
    record("P5/total", (tot, tot_rules, tot_art) == MEASURED_TOTAL,
           "total=%d rules=%d art=%d (measured %d/%d/%d; delivered %d/%d/%d)"
           % ((tot, tot_rules, tot_art) + MEASURED_TOTAL + DELIVERED_TOTAL))

    # ---- P6: +0x1F8 is never read from the rules INIClass
    #
    # The section argument is the LAST push before the call (cdecl, right to
    # left: default, key, section). Leases are tracked forward with the same
    # clobber rule the ABI imposes: eax/ecx/edx die at every call, so a lease
    # living in one of those is dead afterwards.
    print("\n--- P6 section-buffer invariant ---")
    viol = []
    n_lit = 0
    n_stack = 0
    for name, _vt, ld, _s in CHAIN:
        end = extent(ld)
        insns = insns_of(ld, end)
        reg_this = getattr(capstone.x86, "X86_REG_" + THIS_REG[name].upper())
        leases = {}
        last_push = None
        cur_ini = None
        for insn in insns:
            # INIClass selection is forward-carried, mirroring parse().
            if insn.mnemonic == "mov" and len(insn.operands) == 2:
                d, s = insn.operands
                if d.type == capstone.x86.X86_OP_REG and insn.reg_name(d.reg) == "ecx":
                    if s.type == capstone.x86.X86_OP_IMM and (s.imm & 0xFFFFFFFF) == INI_ART:
                        cur_ini = "ART"
                    elif s.type in (capstone.x86.X86_OP_IMM, capstone.x86.X86_OP_MEM):
                        cur_ini = "RULES"
                    elif s.type == capstone.x86.X86_OP_REG:
                        # register-held INIClass: caller's (rules) unless it
                        # provably holds the global. Not decidable from the
                        # callee alone -> leave unresolved.
                        cur_ini = None
            if insn.mnemonic == "lea" and len(insn.operands) == 2:
                d, s = insn.operands
                if d.type == capstone.x86.X86_OP_REG and s.type == capstone.x86.X86_OP_MEM \
                        and s.mem.base == reg_this and s.mem.disp in SECNAME \
                        and s.mem.index == 0:
                    leases[d.reg] = s.mem.disp
                    continue
            # Any other write to a register kills its lease. Without this a
            # `mov esi, edi` mid-function (ObjectTypeClass 0x5F9313) left a
            # stale +0x1F8 lease on esi and produced two fake "rules read of a
            # +0x1F8 section" rows.
            if insn.operands and insn.operands[0].type == capstone.x86.X86_OP_REG \
                    and insn.mnemonic in ("mov", "xor", "add", "sub", "and", "or",
                                          "inc", "dec", "imul", "shl", "shr",
                                          "neg", "not", "pop"):
                leases.pop(insn.operands[0].reg, None)
            if insn.mnemonic == "push" and insn.operands:
                op = insn.operands[0]
                last_push = op.reg if op.type == capstone.x86.X86_OP_REG else None
                continue
            if insn.mnemonic != "call" or not insn.operands:
                continue
            op = insn.operands[0]
            tgt = (op.imm & 0xFFFFFFFF) if op.type == capstone.x86.X86_OP_IMM else None
            if tgt in READERS or (tgt is not None and is_wrapper(tgt)):
                sec = leases.get(last_push) if last_push is not None else None
                if sec == 0x1F8:
                    if cur_ini is None:
                        n_stack += 1
                    else:
                        n_lit += 1
                    # `cur_ini` is a FORWARD-carried value, not a backward scan:
                    # ObjectTypeClass sets `mov ecx,0x887180` seven instructions
                    # before the call (0x5F95BF) and then clobbers only dl/eax in
                    # between, so any fixed-width backward window misses it. The
                    # same state machine as parse() is used here on purpose.
                    if cur_ini is not None and cur_ini != "ART":
                        viol.append((name, "0x%08X" % insn.address))
            cur_ini = None
            for _r in (capstone.x86.X86_REG_EAX, capstone.x86.X86_REG_ECX,
                       capstone.x86.X86_REG_EDX):
                leases.pop(_r, None)
            last_push = None
            continue
        if insn.mnemonic == "call":
            last_push = None
    # Denominator matters: "0 violations" is only meaningful if sites were
    # actually examined. `n_lit` = +0x1F8 sites whose INIClass is a literal and
    # therefore assertable; `n_stack` = sites whose INIClass arrives as a stack
    # parameter and cannot be settled statically (recorded, not asserted).
    record("P6/+0x1F8", len(viol) == 0 and n_lit > 0,
           "rules-file reads of +0x1F8 = %d %s | sites: literal-INIClass asserted=%d, "
           "stack-parameter unresolved=%d"
           % (len(viol), viol[:5], n_lit, n_stack))

    # ---- P7: WaterBound encode sequence, asserted as an ORDERED SUBSET.
    # The delivered prose quotes `cmp eax,5 / sete / and 6 / dec` as the shape.
    # Byte measurements show two extra instructions interleaved (`mov ecx,edi`
    # setting up the reader's `this`, `push edx` staging the bool default), so
    # requiring the four to be adjacent fails on a correct program. What is
    # asserted is: the load happens first, then 5 is compared, then the
    # 6-mask/dec that yields {-1, 5}, then the store back to the same offset.
    print("\n--- P7 WaterBound encode ---")
    seq = insns_of(0x0045FF85, 0x0045FFAF)
    shape = [(i.mnemonic, i.op_str) for i in seq]
    want_in_order = [
        ("mov", "eax, dword ptr [ebp + 0x67c]"),
        ("cmp", "eax, 5"),
        ("sete", "dl"),
        ("and", "eax, 6"),
        ("dec", "eax"),
        ("mov", "dword ptr [ebp + 0x67c], eax"),
    ]
    pos = 0
    for mn, ops in shape:
        if pos < len(want_in_order) and (mn, ops) == want_in_order[pos]:
            pos += 1
    key_at = cstr(0x0081AE4C, 16)
    record("P7/waterbound", pos == len(want_in_order) and key_at == "WaterBound",
           "ordered subseq %d/%d, key@0x81AE4C=%r"
           % (pos, len(want_in_order), key_at))

    # ---- P8: ctor chain first call
    print("\n--- P8 constructor chain ---")
    for name, (ce, ch, base) in CTORS.items():
        if base is None:
            continue
        first = None
        for insn in insns_of(ce, ch):
            if insn.mnemonic == "call" and insn.operands \
                    and insn.operands[0].type == capstone.x86.X86_OP_IMM:
                t = insn.operands[0].imm & 0xFFFFFFFF
                if TEXT_LO <= t < TEXT_HI:
                    first = t
                    break
        record("P8/%-19s" % name, first == base,
               "first call 0x%08X (exp base ctor 0x%08X)" % (first or 0, base))

    # ---- P9: pointer-walking clear loop in BuildingType ctor
    #
    # Found by the (base, stride, count) triple, not by "the first lea at or
    # above +0xF00". BuildingTypeClass also has 8-byte clear loops at +0x1588,
    # +0x15D8 and +0x1664; a positional scan locks onto the first of those and
    # reports stride 0 / count None against a correct program.
    print("\n--- P9 pointer clear loop ---")
    body_ins = insns_of(*CTORS["BuildingTypeClass"][:2])
    base_disp = stride = count = None
    for i, insn in enumerate(body_ins):
        if insn.mnemonic != "lea" or len(insn.operands) != 2:
            continue
        d, src = insn.operands
        if d.type != capstone.x86.X86_OP_REG or src.type != capstone.x86.X86_OP_MEM:
            continue
        if insn.reg_name(src.mem.base) != "esi" or src.mem.disp == 0:
            continue
        ptr = d.reg
        got_stride = got_count = None
        for k in body_ins[i:i + 60]:
            if k.mnemonic == "add" and len(k.operands) == 2 \
                    and k.operands[0].type == capstone.x86.X86_OP_REG \
                    and k.operands[0].reg == ptr \
                    and k.operands[1].type == capstone.x86.X86_OP_IMM:
                got_stride = k.operands[1].imm & 0xFFFFFFFF
            if k.mnemonic == "mov" and len(k.operands) == 2 \
                    and k.operands[0].type == capstone.x86.X86_OP_REG \
                    and k.reg_name(k.operands[0].reg) == "ecx" \
                    and k.operands[1].type == capstone.x86.X86_OP_IMM and got_count is None:
                got_count = k.operands[1].imm
            if got_stride and got_count:
                break
        if got_stride == 0x44:
            base_disp, stride, count = src.mem.disp, got_stride, got_count
            break
    ok = (base_disp, stride, count) == (0x0F5C, 0x44, 0x15)
    record("P9/clearloop", ok,
           "base=+%s stride=0x%X count=%s (exp +0xF5C/0x44/0x15)"
           % ("0x%04X" % base_disp if base_disp else "?", stride or 0, count))

    # ---- P10: Speed is the only immediate default in TechnoType
    print("\n--- P10 immediate defaults ---")
    imm_defaults = []
    for name, _vt, ld, _s in CHAIN:
        end = extent(ld)
        insns = insns_of(ld, end)
        local = []
        for idx, insn in enumerate(insns):
            if insn.mnemonic != "call" or not insn.operands:
                continue
            op = insn.operands[0]
            if op.type != capstone.x86.X86_OP_IMM:
                continue
            tgt = op.imm & 0xFFFFFFFF
            if tgt not in READERS and not is_wrapper(tgt):
                continue
            rname = READERS[tgt][0] if tgt in READERS else "WRAP"
            if rname != "ReadInteger":
                continue
            # cdecl pushes arguments right-to-left, so the default comes FIRST:
            # `push -1` (default) then `push <key literal>`. Scanning backwards
            # from the call finds the key first and then mistakes whatever
            # preceded it for the default.
            win = insns[max(0, idx - 12):idx]
            for j in range(len(win) - 1):
                k = win[j]
                if k.mnemonic != "push" or not k.operands \
                        or k.operands[0].type != capstone.x86.X86_OP_IMM:
                    continue
                v = k.operands[0].imm
                if not (-0x80000000 <= v < 0):
                    continue
                nxt = win[j + 1]
                if nxt.mnemonic == "push" and nxt.operands \
                        and nxt.operands[0].type == capstone.x86.X86_OP_IMM:
                    key = cstr(nxt.operands[0].imm & 0xFFFFFFFF, 64) or None
                    local.append((key, v))
        imm_defaults.append((name, local))
    tech = [x for x in imm_defaults if x[0] == "TechnoTypeClass"][0][1]
    record("P10/speed", tech == [("Speed", -1)],
           "TechnoType neg-immediate defaults = %s (exp [('Speed', -1)])" % tech)

    # ---- P11: the delivery's deviation from this gate has ONE shape.
    #
    # This is deliberately NOT "mismatches == 0". The delivery's table is
    # missing rows, and that gap is the finding; asserting "equal" would just
    # restate the defect. What is asserted is the exact shape of the gap:
    #   * every row the delivery has, this gate also has, at the same offset,
    #   * every row this gate has that the delivery does not is a ReadDouble,
    #   * the count of those rows is EXPECTED_EXTRA_DOUBLES,
    #   * and the only INI-attribution disagreement is MovementZone.
    # If the delivery is ever repaired, this check goes RED on purpose and this
    # comment has to be updated -- a silent pass would be worse.
    print("\n--- P11 delivery-gap shape ---")
    ev_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "evidence", "typeclass_fields.txt")
    ev = parse_evidence(ev_path)
    missing_from_mine = []
    extras = []
    ini_disagree = []
    for name in parsed:
        mine = [(r["key"], r["store_off"], r["ini"])
                for r in parsed[name]["rows"]
                if r["key"] and r["store_off"] is not None]
        theirs = [(r["key"], r["store_off"], r["ini"]) for r in ev.get(name, [])]
        mine_ko = {(k, o) for k, o, _ in mine}
        their_ko = {(k, o) for k, o, _ in theirs}
        missing_from_mine += [(name,) + x for x in (their_ko - mine_ko)]
        for r in parsed[name]["rows"]:
            if r["key"] and r["store_off"] is not None \
                    and (r["key"], r["store_off"]) not in their_ko:
                extras.append((name, r["key"], r["store_off"], r["reader"], r["ini"]))

    n_extra = len(extras)
    all_double = all(e[3] == "ReadDouble" for e in extras)
    record("P11a/no-row-lost", len(missing_from_mine) == 0,
           "rows the delivery has and this gate does not = %d %s"
           % (len(missing_from_mine), missing_from_mine[:5]))
    record("P11b/extra-are-doubles", all_double and n_extra == EXPECTED_EXTRA_DOUBLES,
           "rows only in this gate = %d, all ReadDouble = %s (exp %d all-double)"
           % (n_extra, all_double, EXPECTED_EXTRA_DOUBLES))
    # INI attribution is only asserted for rows where BOTH sides rest on a
    # literal `mov ecx, 0x887180` (or its absence) at the call site. Rows whose
    # INIClass arrives as a stack parameter cannot be settled by static reading
    # of the callee alone -- the frame offset at that point depends on which
    # branch was taken. Those are reported, not asserted.
    stamped = 0
    for name in parsed:
        theirs = {(r["key"], r["store_off"]): r["ini"] for r in ev.get(name, [])}
        for r in parsed[name]["rows"]:
            if not r["key"] or r["store_off"] is None:
                continue
            if r.get("ini_src") != "IMM":
                continue
            k = (r["key"], r["store_off"])
            if k in theirs:
                stamped += 1
                if theirs[k] != r["ini"]:
                    ini_disagree.append((name, r["key"],
                                         "gate=%s delivery=%s (literal INIClass)"
                                         % (r["ini"], theirs[k])))
    record("P11c/ini-attribution", ini_disagree == [],
           "literal-INIClass rows compared=%d disagreements=%d %s"
           % (stamped, len(ini_disagree), ini_disagree[:4]))

    # ---- P11d: scope boundary, stated rather than left implicit.
    # Both this gate and the delivery report only keys that reach a FIELD store.
    # 153 key reads in these seven loaders land in an INLINE char[] buffer
    # instead (`read -> lea edx,[this+off] -> rep movsd`), e.g. the three
    # TurretAnim/TurretAnimDamaged/TurretAnimGarrisoned keys at +0x11B0..+0x11DF
    # in BuildingTypeClass. Those are real keys with real offsets, but they are
    # outside the "key -> scalar field" scope both sides use, so neither table
    # lists them. Recording the number keeps the scope from being mistaken for
    # a complete key census.
    no_store = []
    for name in parsed:
        for r in parsed[name]["rows"]:
            if r["key"] and r["store_off"] is None:
                no_store.append((name, r["key"]))
    record("P11d/scope-boundary", len(no_store) == EXPECTED_NO_STORE_KEYS,
           "key reads with no field store (inline char[] dest) = %d (measured %d); "
           "neither table lists these"
           % (len(no_store), EXPECTED_NO_STORE_KEYS))

    # ---- P12: the 31 extra rows are corroborated by the CLASS CONSTRUCTOR.
    # Independent line of evidence: the loaders and the ctors are different
    # functions reached from different call sites, so agreement cannot come from
    # a shared parsing mistake. If the extra rows were parser noise, the ctor
    # would not be writing defaults at those exact offsets.
    print("\n--- P12 constructor corroboration of the extra rows ---")
    uncorroborated = []
    for name in ("TechnoTypeClass", "BuildingTypeClass"):
        ce, ch, _base = CTORS[name]
        written = set()
        for insn in insns_of(ce, ch):
            for op in insn.operands:
                if op.type == capstone.x86.X86_OP_MEM and op.mem.base == capstone.x86.X86_REG_ESI \
                        and op.mem.index == 0:
                    written.add(op.mem.disp)
        mine = [e for e in extras if e[0] == name]
        for e in mine:
            if e[2] not in written:
                uncorroborated.append(e)
    record("P12/ctor-corrob", uncorroborated == [],
           "extra rows without a ctor default at the same offset = %d %s"
           % (len(uncorroborated), uncorroborated[:5]))

    # ---- P13: WHY the original tool loses exactly these rows.
    # The delivered tool's `fstp` handler skipped `base in (ESP, EBP)`. For
    # TechnoTypeClass/BuildingTypeClass `this` IS EBP, so every `fstp [ebp+off]`
    # field store was discarded. Counted straight from the image here (not from
    # either parser), which ties the defect to its cause.
    print("\n--- P13 mechanism of the loss ---")
    n_fstp_ebp = 0
    for name in ("TechnoTypeClass", "BuildingTypeClass"):
        ld = dict((n, l) for n, _v, l, _s in CHAIN)[name]
        body_ins = insns_of(ld, extent(ld))
        reader_sites = [
            insn.address for insn in body_ins
            if insn.mnemonic == "call" and insn.operands
            and insn.operands[0].type == capstone.x86.X86_OP_IMM
            and ((insn.operands[0].imm & 0xFFFFFFFF) in READERS
                 or is_wrapper(insn.operands[0].imm & 0xFFFFFFFF))]
        for insn in body_ins:
            if insn.mnemonic != "fstp" or not insn.operands:
                continue
            op = insn.operands[0]
            if op.type != capstone.x86.X86_OP_MEM \
                    or op.mem.base != capstone.x86.X86_REG_EBP \
                    or op.mem.index != 0 or op.mem.disp in SECNAME:
                continue
            # Only stores that DIRECTLY settle a reader call. TechnoTypeClass also
            # has two computed values (`fild [esp+..] / fmul / fadd / fstp`) at
            # +0x360 and +0x368 (0x7160F6 / 0x71611D); those are derived, not
            # read from a key, and including them would assert 33 vs a true 31.
            if any(0 < insn.address - rs <= 0x20 for rs in reader_sites):
                n_fstp_ebp += 1
    record("P13/mechanism", n_fstp_ebp == EXPECTED_EXTRA_DOUBLES,
           "`fstp [ebp+disp]` stores settling a reader call in the two "
           "EBP-this loaders = %d (exp %d = the rows the ORIGINAL delivery lacks)"
           % (n_fstp_ebp, EXPECTED_EXTRA_DOUBLES))

    # ---- N1 (negative control, DIFFERENT function): the ctor must not parse
    print("\n--- N1 negative control: constructor as input ---")
    p_n1 = parse(*CTORS["TechnoTypeClass"][:2])
    record("N1/ctor", p_n1["reader_sites"] == 0 and len(p_n1["rows"]) == 0,
           "reader sites=%d rows=%d (exp 0/0)"
           % (p_n1["reader_sites"], len(p_n1["rows"])))

    # ---- N2 (sensitivity): wrong object register must change the answer
    print("\n--- N2 sensitivity: wrong this register ---")
    name = "BuildingTypeClass"
    ld = dict((n, l) for n, _v, l, _s in CHAIN)[name]
    p_ok = parse(ld, extent(ld), force_this="ebp")
    p_bad = parse(ld, extent(ld), force_this="edi")
    ok_offs = {r["store_off"] for r in p_ok["rows"] if r["store_off"] is not None}
    bad_offs = {r["store_off"] for r in p_bad["rows"] if r["store_off"] is not None}
    overlap = len(ok_offs & bad_offs) / float(max(len(ok_offs), 1))
    record("N2/wrongreg", overlap < 0.5,
           "offset overlap=%0.1f%% (exp <50%%) ok=%d bad=%d"
           % (overlap * 100, len(ok_offs), len(bad_offs)))

    # ---- N3 (sensitivity): a 0x1000 window must truncate TechnoType
    print("\n--- N3 sensitivity: window truncation ---")
    ld = dict((n, l) for n, _v, l, _s in CHAIN)["TechnoTypeClass"]
    p_win = parse(ld, ld + 0x1000)
    n_win = len([r for r in p_win["rows"] if r["key"] and r["store_off"] is not None])
    record("N3/window", n_win < 276,
           "keys with 0x1000 window=%d (exp <276; full=276)" % n_win)

    # ---- N4 (sensitivity): an fstp-blind parser must reproduce the delivery
    print("\n--- N4 sensitivity: an fstp-blind parser must UNDERCOUNT ---")
    # Simulate the old defect on this parser: drop every row whose store is an
    # `fstp [ebp+off]` shortly after its reader call. If that lands on the
    # delivered count exactly, the defect's cause is confirmed, not merely
    # plausible.
    blind = {}
    for name in ("TechnoTypeClass", "BuildingTypeClass"):
        ld = dict((n, l) for n, _v, l, _s in CHAIN)[name]
        body_ins = insns_of(ld, extent(ld))
        keep = []
        for r in parsed[name]["rows"]:
            if not r["key"] or r["store_off"] is None:
                continue
            drop = False
            for insn in body_ins:
                if insn.address <= r["site"] or insn.address > r["site"] + 0x20:
                    continue
                if insn.mnemonic == "fstp" and insn.operands \
                        and insn.operands[0].type == capstone.x86.X86_OP_MEM \
                        and insn.operands[0].mem.base == capstone.x86.X86_REG_EBP \
                        and insn.operands[0].mem.disp == r["store_off"]:
                    drop = True
                    break
            if not drop:
                keep.append(r)
        blind[name] = len(keep)
    ok = (blind["TechnoTypeClass"] == DELIVERED["TechnoTypeClass"][0]
          and blind["BuildingTypeClass"] == DELIVERED["BuildingTypeClass"][0])
    record("N4/fstpblind", ok,
           "fstp-blind TechnoType=%d (delivered %d), BuildingType=%d (delivered %d)"
           % (blind["TechnoTypeClass"], DELIVERED["TechnoTypeClass"][0],
              blind["BuildingTypeClass"], DELIVERED["BuildingTypeClass"][0]))

    # ---- verdict
    bad = [r for r in RESULTS if not r[1]]
    print("\n=== verdict: %d/%d PASS ===" % (len(RESULTS) - len(bad), len(RESULTS)))
    if bad:
        print("FAILED:")
        for tag, _ok, detail in bad:
            print("  %s  %s" % (tag, detail))
        return 1
    print("ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
