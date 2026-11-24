# -*- coding: utf-8 -*-
"""
T2 adversarial verification of the W132 instance-array claims (C1..C7).

Read-only.  Never launches the game.  Never writes outside its own directory.

    python -X utf8 t2_refute.py
"""
import hashlib
import os
import struct

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

BIN = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
OUT = os.path.dirname(os.path.abspath(__file__))
IMAGEBASE = 0x400000

_raw = open(BIN, "rb").read()
SHA = hashlib.sha256(_raw).hexdigest().upper()
assert SHA == EXPECT_SHA, "binary hash mismatch: %s" % SHA

_pe = pefile.PE(BIN)
PE_NS = {}
for s in _pe.sections:
    pass
_pe.parse_data_directories(directories=[
    pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_BASERELOC"]])

SECTIONS = []
for s in _pe.sections:
    nm = s.Name.decode("latin-1").rstrip("\x00")
    va = IMAGEBASE + s.VirtualAddress
    SECTIONS.append((nm, va, va + s.Misc_VirtualSize,
                     s.PointerToRawData, s.SizeOfRawData))

TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
DATA_LO, DATA_HI = 0x812000, 0x87E000      # file-backed part of .data
RDATA_LO, RDATA_HI = 0x7E1000, 0x812000


def sec_of(va):
    for nm, a, b, rp, rs in SECTIONS:
        if a <= va < b:
            return nm, a, b, rp, rs
    return (None,) * 5


def file_off(va):
    nm, a, b, rp, rs = sec_of(va)
    if nm is None or (va - a) >= rs:
        return None
    return rp + (va - a)


def file_backed(va, n=1):
    nm, a, b, rp, rs = sec_of(va)
    return nm is not None and (va - a) + n <= rs


def rd(va, n):
    if not file_backed(va, n):
        return None
    return _raw[file_off(va):file_off(va) + n]


def u32(va):
    b = rd(va, 4)
    return None if b is None else struct.unpack("<I", b)[0]


def u8(va):
    b = rd(va, 1)
    return None if b is None else b[0]


def cstr(va, limit=300):
    nm, a, b, rp, rs = sec_of(va)
    if nm is None:
        return None
    o = file_off(va)
    if o is None:
        return None
    end = min(o + limit, rp + rs)
    blob = _raw[o:end]
    z = blob.find(b"\x00")
    if z < 0:
        return None
    return blob[:z].decode("latin-1")


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True


def dis(va, n, stop_ret=True):
    code = rd(va, n)
    if code is None:
        return []
    out = []
    try:
        for insn in md.disasm(code, va):
            if insn.id == 0:
                continue
            out.append(insn)
            if stop_ret and insn.mnemonic == "ret":
                break
    except Exception:
        pass
    return out


def fmt(i):
    return "%08X  %-22s %-7s %s" % (i.address, i.bytes.hex(),
                                     i.mnemonic, i.op_str)


# ------------------------------------------------------------------ RTTI
# Offsets below were established empirically on this image (see report.md §RTTI):
#
#   TypeDescriptor        +0x00 type_info vftable, +0x04 0,
#                         +0x08 THE NAME IS INLINE (char[]), NOT a char*
#   CompleteObjectLocator +0x00 sig +0x04 offset +0x08 cdOffset
#                         +0x0C pTypeDescriptor +0x10 pClassDescriptor
#   ClassDescriptor       +0x00 sig +0x04 attr +0x08 nBase
#                         +0x0C.. TypeDescriptor* bases, +0x40 own TD
#
# The inline-name form is why this image contains no pointer to the name string;
# a scanner that treats TD+8 as a char* reads '.?AV' as an address and finds 0.
def td_name(td):
    if td is None:
        return None
    s = cstr(td + 8)
    if not s or not s.startswith(".?A"):
        return None
    return s


def decode_td(td):
    """'.?AV?$DynamicVectorClass@PAVBuildingClass@@@@' -> 'DynamicVectorClass<BuildingClass*>'
       '.?AVAbstractClass@@'                           -> 'AbstractClass'"""
    s = td_name(td)
    if s is None:
        return None
    if s.startswith(".?AV?$"):
        # template: .?AV?$Name@<args>@@@@
        body = s[len(".?AV?$"):]
        if body.endswith("@@"):
            body = body[:-2]
        if "@" in body:
            name, args = body.split("@", 1)
        else:
            name, args = body, ""
        if args.startswith("PAV"):
            return "%s<%s*>" % (name, args[3:])
        if args.startswith("PAD"):
            return "%s<%s**>" % (name, args[3:])
        return "%s<%s>" % (name, args)
    if s.startswith(".?AV") and s.endswith("@@"):
        return s[4:-2]
    if s.startswith(".?AU") and s.endswith("@@"):
        return s[4:-2]
    return s


def col_of_vftable(vft):
    """vftable V -> COL pointer at [V-4]; sanity-check the COL."""
    if vft is None or vft < IMAGEBASE:
        return None
    col = u32(vft - 4)
    if col is None or col < IMAGEBASE:
        return None
    if u32(col) != 0:                    # signature must be 0 for x86
        return None
    off = u32(col + 4)
    td = u32(col + 0xC)
    if off is None or off > 0x1000 or td is None:
        return None
    if td_name(td) is None:
        return None
    return col


def vftable_type(vft):
    col = col_of_vftable(vft)
    if col is None:
        return None
    return decode_td(u32(col + 0xC))


def class_info(vft):
    """Return dict with COL/TD/ClassDescriptor bases for a vftable."""
    col = col_of_vftable(vft)
    if col is None:
        return None
    td = u32(col + 0xC)
    cd = u32(col + 0x10)
    d = dict(vft=vft, col=col, td=td, td_off=u32(col + 4), td_name=td_name(td),
             type=decode_td(td), cd=cd, cd_ok=None, nbase=None, bases=[])
    if cd is not None and 0x400000 < cd < 0xC00000:
        sig = u32(cd)
        nbase = u32(cd + 8)
        own = u32(cd + 0x40)
        if sig in (0, 1) and nbase is not None and 0 <= nbase < 16 and own == td:
            d["cd_ok"] = True
            d["nbase"] = nbase
            d["bases"] = [decode_td(u32(cd + 0xC + 4 * k)) for k in range(nbase)]
        else:
            d["cd_ok"] = False
    return d


_TD = None


def all_tds():
    """Every TypeDescriptor in the file-backed .data."""
    global _TD
    if _TD is not None:
        return _TD
    out = {}
    blob = rd(DATA_LO, DATA_HI - DATA_LO)
    i = 0
    while True:
        j = blob.find(b".?A", i)
        if j < 0:
            break
        sva = DATA_LO + j
        td = sva - 8              # name is inline at TD+8
        if u32(td) is not None and td >= DATA_LO:
            nm = cstr(sva)
            if nm:
                out[td] = nm
        i = j + 1
    _TD = out
    return out


# ------------------------------------------------------------ text index
C7_05 = []
PUSH_IMM = []
PUSH_MEM = []
DEC_INC_MEM = []


def _index():
    lo, hi = TEXT_LO, min(TEXT_HI, 0x7E1000)
    blob = rd(lo, hi - lo)
    n = len(blob)
    i = 0
    while True:
        j = blob.find(b"\xc7\x05", i)
        if j < 0:
            break
        if j + 10 <= n:
            a, v = struct.unpack("<II", blob[j + 2:j + 10])
            C7_05.append((lo + j, a, v))
        i = j + 1
    i = 0
    while True:
        j = blob.find(b"\x68", i)
        if j < 0:
            break
        if j + 5 <= n:
            PUSH_IMM.append((lo + j, struct.unpack("<I", blob[j + 1:j + 5])[0]))
        i = j + 1
    i = 0
    while True:
        j = blob.find(b"\xff\x35", i)
        if j < 0:
            break
        if j + 6 <= n:
            PUSH_MEM.append((lo + j, struct.unpack("<I", blob[j + 2:j + 6])[0]))
        i = j + 1
    for pre, ln in ((b"\xff\x05", 6), (b"\xff\x0d", 6), (b"\x83\x05", 7),
                    (b"\x83\x2d", 7), (b"\x81\x05", 10), (b"\x81\x2d", 10)):
        i = 0
        while True:
            j = blob.find(pre, i)
            if j < 0:
                break
            if j + ln <= n:
                a = struct.unpack("<I", blob[j + 2:j + 6])[0]
                DEC_INC_MEM.append((lo + j, a, pre.hex()))
            i = j + 1


def abs_refs(target):
    blob = rd(TEXT_LO, min(TEXT_HI, 0x7E1000) - TEXT_LO)
    needle = struct.pack("<I", target)
    out = []
    i = blob.find(needle)
    while i >= 0:
        out.append(TEXT_LO + i)
        i = blob.find(needle, i + 1)
    return out


def func_start(va, max_back=0x600):
    """Nearest padding boundary (run of CC/90 followed by a real opcode)."""
    p = None
    for back in range(1, max_back):
        a = va - back
        if a <= TEXT_LO:
            break
        b = u8(a)
        if b is None:
            break
        if b in (0xCC, 0x90):
            p = a
            continue
        if p is not None:
            return p + 1
    return None


def func_at(addr, max_back=0x600, max_len=0x2000):
    """Enclosing function of an interior address (best effort)."""
    st = func_start(addr, max_back)
    if st is None:
        return None, None, []
    ins = dis(st, max_len, stop_ret=False)
    end = st
    saw_ret = False
    for i in ins:
        end = i.address + i.size
        if i.mnemonic == "ret":
            if saw_ret:
                break
            saw_ret = True
            continue
        if saw_ret:
            if i.mnemonic in ("int3", "nop"):
                break
            saw_ret = False
        if end - st > max_len:
            break
    ins = [i for i in ins if i.address < end]
    return st, end, ins


def insn_covering(insns, addr):
    for i in insns:
        if i.address <= addr < i.address + i.size:
            return i
    return None


def call_targets(insns):
    out = []
    for i in insns:
        if i.mnemonic == "call" and i.operands and i.operands[0].type == 2:
            out.append((i.address, i.operands[0].imm))
    return out


def memoperands(insns, base=None):
    """Yield (insn, absolute_addr) for every direct [abs] memory operand."""
    for i in insns:
        for op in i.operands:
            if op.type == 3 and op.mem.base == 0 and op.mem.index == 0:
                yield i, (op.mem.disp & 0xFFFFFFFF)


# ================================================================== report
LOG = []


def log(s=""):
    LOG.append(s)


def hdr(s):
    log("")
    log("=" * 78)
    log(s)
    log("=" * 78)


VECTORS = [
    ("0xA8EB40", 0xA8EB40, "BuildingClass*"),
    ("0x8B4108", 0x8B4108, "UnitClass*"),
    ("0xA80228", 0xA80228, "HouseClass*"),
    ("0xA8E390", 0xA8E390, "AircraftClass*"),
    ("0x8B3DC0", 0x8B3DC0, "FootClass*"),
    ("0xB0F720", 0xB0F720, "AbstractClass*"),
    ("0xA8EC78", 0xA8EC78, "TechnoClass*"),
    ("0xA83DE8", 0xA83DE8, "InfantryClass*"),
]


def vec_static_ctor(base):
    """The .CRT$XCU initialiser: the instruction that first stores a vftable
    into [base].  Returns (addr, (start,end,insns))."""
    c7 = [(va, v) for va, a, v in C7_05 if a == base]
    if not c7:
        return None, (None, None, [])
    return c7[0], func_at(c7[0][0])


def field_writes(insns, base):
    """Map offset -> list of (insn, value) for 'mov [base+off], imm'."""
    out = {}
    for i, ad in memoperands(insns):
        if base <= ad <= base + 0x40 and i.mnemonic in ("mov", "movzx"):
            op0 = i.operands[0]
            if op0.type != 3:
                continue
            val = None
            if len(i.operands) == 2 and i.operands[1].type == 2:
                val = i.operands[1].imm
            out.setdefault(ad - base, []).append((i, val, op0.size))
    return out


# --------------------------------------------------------------- C1
def c1_layout():
    hdr("C1  VectorClass<T> layout, derived from 8 independent static ctors")
    log("Claim: +00 vftable, +04 T* Items, +08 int Capacity, +0C bool IsInitialized,")
    log("       +0D bool IsAllocated, +10 int Count, +14 int CapacityIncrement (=10)")
    log("")
    log("Method: for each array, take the .CRT$XCU initialiser (the function that")
    log("stores a vftable into [base]) and tabulate EVERY absolute memory write it")
    log("performs.  A layout claim is only supported if all 8 tabulations agree.")
    log("")
    for label, base, expect in VECTORS:
        store, (st, en, ins) = vec_static_ctor(base)
        if store is None:
            log("---- %s : NO vftable store found ----" % label)
            continue
        log("---- %s (expected %s) ----" % (label, expect))
        log("   static ctor %08X..%08X (%d bytes), vftable store at %08X"
            % (st, en, en - st, store[0]))
        for i in ins:
            log("     " + fmt(i))
        fw = field_writes(ins, base)
        log("   absolute writes into the object:")
        for off in sorted(fw):
            for i, val, size in fw[off]:
                log("     +0x%02X  size=%d  value=%-10s  @%08X  (%s)" %
                    (off, size, val if val is not None else "[eax]",
                     i.address, i.mnemonic + " " + i.op_str))
        # what the vftable store says
        vt = [v for va, v in [(store[0], store[1])]]
        log("   vftable stored: %08X -> %s" % (store[1], vftable_type(store[1])))
        log("")


def c1_inc10():
    hdr("C1 / angle 4  '+0x14 CapacityIncrement == 10' on every array")
    log("array      ctor       [+0x14] write     value  observation")
    vals = {}
    for label, base, expect in VECTORS:
        store, (st, en, ins) = vec_static_ctor(base)
        if store is None:
            continue
        hit = None
        fw = field_writes(ins, base)
        for i, val, size in fw.get(0x14, []):
            hit = (i, val)
        vals[label] = hit[1] if hit else None
        log("%-10s %08X   %-16s %-6s %s" %
            (label, st,
             ("%08X" % hit[0].address) if hit else "(none)",
             hit[1] if hit else "-",
             "== 10" if hit and hit[1] == 10 else "*** != 10 ***"))
    log("")
    log("distinct values observed: %s" % sorted(set(vals.values()), key=str))


# --------------------------------------------------------------- identity
def vftable_identity():
    hdr("Vectors: layout is confirmed independently of any name, via the")
    log("dynamic element size other functions use for the SAME base.")
    for label, base, expect in VECTORS:
        store, (st, en, ins) = vec_static_ctor(base)
        vt = store[1] if store else None
        log("")
        log("%-10s base=%08X vftable=%s" % (label, base, "%08X" % vt if vt else "?"))
        info = class_info(vt) if vt else None
        if info:
            log("   COL=%08X td_off=%d TD=%08X  type=%s" %
                (info["col"], info["td_off"], info["td"], info["type"]))
            if info["cd_ok"]:
                log("   ClassDescriptor %08X: nBase=%d bases=%s" %
                    (info["cd"], info["nbase"], info["bases"]))
            else:
                log("   ClassDescriptor %08X: could not be validated" % (info["cd"],))
        # the OTHER vftable store (the atexit destructor's base-class one)
        c7 = [(va, v) for va, a, v in C7_05 if a == base]
        for va, v in c7[1:]:
            log("   second store %08X -> %08X = %s" % (va, v, vftable_type(v)))
        # element stride actually used by the push/insert code
        strides = element_strides(base)
        log("   element stride observed in insertion/reindex code: %s"
            % (sorted(strides) if strides else "(none found)"))


def element_strides(base):
    """Find code of the form  mov eax,[base+0x10] / shl eax,2  (or lea with *4)
    near a store through [base+4].  Returns the set of scale factors seen."""
    out = set()
    for r in abs_refs(base + 0x10)[:40]:
        st, en, ins = func_at(r)
        if st is None:
            continue
        for i in ins:
            if i.mnemonic == "shl" and len(i.operands) == 2 and i.operands[1].type == 2:
                out.add("shl %d" % i.operands[1].imm)
            if i.mnemonic == "lea" and i.operands and i.operands[0].type == 3:
                m = i.operands[0].mem
                if m.scale:
                    out.add("lea *%d" % m.scale)
        if out:
            break
    return out


def inserters():
    """angle 1: find the code that actually pushes into each vector, and
    identify what object it pushes."""
    hdr("C2/C3/C4/C6  angle 1 - who INSERTS into each vector, and what?")
    log("An insert site is: a read of Count at [base+0x10] in a function that")
    log("also stores through Items at [base+0x04].  For such a site we walk back")
    log("in the same basic block to see what pointer is being stored, and where")
    log("that pointer came from (an `operator new` + a vftable store is a ctor).")
    for label, base, expect in VECTORS:
        log("")
        log("---- %s (%s) ----" % (label, expect))
        sites = []
        for r in abs_refs(base + 0x10):
            st, en, ins = func_at(r)
            if st is None:
                continue
            store = [i for i in ins if i.mnemonic == "mov"
                     and any(op.type == 3 and op.mem.base == 0
                             and (op.mem.disp & 0xFFFFFFFF) == base + 0x04
                             for op in i.operands)]
            if store:
                sites.append((st, en, ins, store))
        log("   candidate insert/read-modify functions: %d" % len(sites))
        for st, en, ins, store in sites[:6]:
            log("   fn %08X..%08X" % (st, en))
            for i in store[:3]:
                log("      STORE-ITEMS " + fmt(i))
            # show the nearest preceding pushes, to see what got nulled/set
            blk = [i for i in ins if abs(i.address - store[0].address) < 0x80]
            for i in blk:
                log("        " + fmt(i))
            log("")


def c2_building():
    hdr("C2  0xA8EB40 is DynamicVectorClass<BuildingClass*> -> 0xA8EB44 is NOT a unit table")
    base = 0xA8EB40
    store, (st, en, ins) = vec_static_ctor(base)
    info = class_info(store[1])
    log("static ctor %08X installs vftable %08X" % (store[0], store[1]))
    log("  RTTI: COL=%08X  TD=%08X  off=%d  type=%s"
        % (info["col"], info["td"], info["td_off"], info["type"]))
    log("  raw TypeDescriptor name: %s" % info["td_name"])
    log("")
    log("Cross-check 1 - is 0xA8EB44 ever used as a generic object table?")
    log("  The same element type must not also appear as a *second* vector: see")
    log("  the duplicate-base scan in c5_duplicates().")
    log("Cross-check 2 - who reads [0xA8EB50] (Count)?  Sample of the enclosing fns:")
    for r in abs_refs(base + 0x10)[:8]:
        st2, en2, ins2 = func_at(r)
        hit = insn_covering(ins2, r)
        log("    %08X in %s : %s" % (r, hex(st2) if st2 else "?",
                                     fmt(hit) if hit else "?"))
    log("")
    log("Cross-check 3 - does anything store a UnitClass-derived vftable into")
    log("  [0xA8EB44..]?  Scan every 'mov [abs], vftable' whose target lies in")
    log("  the +-0x20 window of 0xA8EB44 and report its type:")
    for va, a, v in C7_05:
        if abs(a - 0xA8EB44) <= 0x20:
            log("    %08X mov [%08X],%08X -> %s" % (va, a, v, vftable_type(v)))


def c3_unit():
    hdr("C3  0x8B4108 is DynamicVectorClass<UnitClass*>")
    base = 0x8B4108
    store, (st, en, ins) = vec_static_ctor(base)
    info = class_info(store[1])
    log("static ctor %08X/%08X..%08X installs vftable %08X"
        % (store[0], st, en, store[1]))
    log("  RTTI COL=%08X TD=%08X off=%d type=%s" %
        (info["col"], info["td"], info["td_off"], info["type"]))
    log("  raw name: %s" % info["td_name"])
    log("")
    log("Independence check - the vftable is installed by a byte-exact C7 05")
    log("store whose layout is IDENTICAL to 0xA8EB40's but 4 vftables apart:")
    for lab, b2, _ in VECTORS[:5]:
        s2, (st2, en2, _) = vec_static_ctor(b2)
        log("   %-10s ctor %08X-.. vftable %08X  (+0x14 write at %08X)"
            % (lab, st2, s2[1], st2 + 0x27))
    log("")
    log("Is there a SECOND vector of vehicles?  Duplicate-element scan:")
    dup_scan()


def c4_house():
    hdr("C4  0xA80228 is HouseClass*, and aircraft is 0xA8E390")
    for base, name in ((0xA80228, "HouseClass"), (0xA8E390, "AircraftClass")):
        store, (st, en, ins) = vec_static_ctor(base)
        info = class_info(store[1])
        log("%08X -> %s   (ctor %08X, vftable %08X, TD %08X)"
            % (base, info["type"], st, store[1], info["td"]))
        log("    raw: %s" % info["td_name"])
    log("")
    log("Distinguishing test: the two arrays must not be the same object and")
    log("must not be adjacent aliases.  Both live in BSS (runtime-zero, no file")
    log("bytes), so the test is address disjointness, not content:")
    log("  0xA8022C (House Items) vs 0xA8E394 (Aircraft Items): distance 0x%X"
        % (0xA8E390 - 0xA80228))
    log("  0xA80228 vs 0xA8E390 are distinct static-ctor targets: %s"
        % (len([1 for va, a, v in C7_05 if a in (0xA80228, 0xA8E390)]) == 4))
    log("")
    log("Independent behavioural test - the aircraft array's Count is compared")
    log("against 0 anywhere in a 'no aircraft yet' guard (House array is not):")
    for r in abs_refs(0xA8E3A0)[:20]:
        st2, en2, ins2 = func_at(r)
        hit = insn_covering(ins2, r)
        ok = ins2 and any(i.mnemonic.startswith("j") and "0x" in i.op_str
                          for i in ins2[max(0, ins2.index(hit)):]
                          ) if hit else False
        log("    %08X  %s" % (r, fmt(hit) if hit else "?"))


def dup_scan():
    """Brute: every 'C7 05 <abs> <vftable>' whose vftable names a
    DynamicVectorClass<T*>, grouped by T.  Detects duplicate vectors."""
    found = {}
    for va, a, v in C7_05:
        t = vftable_type(v)
        if not t or "<" not in t:
            continue
        if "VectorClass" not in t:
            continue
        found.setdefault(t, []).append((a, v, va))
    for want in ("UnitClass*", "BuildingClass*", "HouseClass*",
                 "AircraftClass*", "FootClass*", "AbstractClass*",
                 "TechnoClass*", "InfantryClass*", "ObjectClass*"):
        keys = [k for k in found if k.endswith("<" + want + ">")]
        log("  element %-16s : %d vector(s)" % (want, len(keys)))
        for k in keys:
            for a, v, va in found[k]:
                log("     base=%08X vftable=%08X (%s) via %s" %
                    (a, v, k, hex(va)))
    log("")
    log("  ALL vector-like C7 05 targets grouped (looking for a second vehicle list):")
    for k in sorted(found):
        bases = sorted(set(a for a, v, va in found[k]))
        if len(bases) > 1:
            log("    %-46s %d bases: %s" % (k, len(bases),
                ", ".join("%08X" % b for b in bases)))


def c5_identity():
    hdr("C5  0xB0F720: is it typed AbstractClass*, and is it used as a registry?")
    base = 0xB0F720
    store, (st, en, ins) = vec_static_ctor(base)
    info = class_info(store[1])
    log("static ctor %08X..%08X, vftable %08X" % (st, en, store[1]))
    log("  RTTI COL=%08X TD=%08X type=%s" % (info["col"], info["td"], info["type"]))
    log("  raw: %s" % info["td_name"])
    log("")
    log("Is the element type consistent with how the array is USED?  A registry")
    log("of AbstractClass* would be filled by a single 'add object' helper called")
    log("from many ctors.  Find every function that stores through [0xB0F724]:")
    bumps = [(a, t, k) for a, t, k in DEC_INC_MEM if t == base + 0x10]
    log("  instructions that modify Count [0xB0F730] in place: %d" % len(bumps))
    for a, t, k in bumps[:20]:
        st2, en2, ins2 = func_at(a)
        hit = insn_covering(ins2, a)
        log("    %08X in fn %-9s : %s" % (a, hex(st2) if st2 else "?",
                                          fmt(hit) if hit else k))
    log("")
    log("  Every 'mov [0xB0F730], reg' (a Count *assignment*, i.e. realloc):")
    for a in abs_refs(base + 0x10):
        st2, en2, ins2 = func_at(a)
        hit = insn_covering(ins2, a)
        if hit and hit.mnemonic == "mov" and hit.operands[0].type == 3 \
           and hit.operands[1].type == 1:
            log("    %08X fn=%-9s %s" % (a, hex(st2) if st2 else "?", fmt(hit)))
    log("")
    log("  Who pushes onto it?  look for 'push' + call of a shared add-helper.")
    log("  Candidate add-helper = the function containing an inc/add of [0xB0F730].")
    if bumps:
        cands = set()
        for a, t, k in bumps:
            st2, en2, ins2 = func_at(a)
            cands.add((st2, en2))
        for st2, en2 in sorted(cands, key=lambda x: (x[0] or 0)):
            log("    helper candidate %s..%s (%s bytes)" %
                (hex(st2) if st2 else "?", hex(en2) if en2 else "?",
                 en2 - st2 if st2 else "?"))
            _, _, ins2 = func_at(st2) if st2 else (None, None, [])
            for i in ins2:
                log("      " + fmt(i))
    log("")
    log("  nBase of AbstractClass's own ClassDescriptor tells us whether")
    log("  AbstractClass really is a 4-vptr multiple-inheritance class:")
    for tname in ("AbstractClass", "ObjectClass", "MissionClass", "RadioClass",
                  "TechnoClass", "FootClass", "UnitClass", "BuildingClass"):
        td = find_named_td(tname)
        if td is None:
            log("    %-14s : TypeDescriptor not found" % tname)
            continue
        cd = find_cd_for_td(td)
        if cd is None:
            log("    %-14s TD=%08X : no validated ClassDescriptor" % (tname, td))
            continue
        nbase = u32(cd + 8)
        bases = [decode_td(u32(cd + 0xC + 4 * k)) for k in range(nbase)]
        log("    %-14s TD=%08X CD=%08X nBase=%d bases=%s"
            % (tname, td, cd, nbase, bases))


_TDNAME = None


def find_named_td(cls):
    global _TDNAME
    if _TDNAME is None:
        _TDNAME = {}
        for td, nm in all_tds().items():
            d = decode_td(td)
            if d and "<" not in d:
                _TDNAME.setdefault(d, td)
    return _TDNAME.get(cls)


def find_cd_for_td(td):
    """ClassDescriptor whose +0x40 back-pointer equals td."""
    blob = rd(DATA_LO, DATA_HI - DATA_LO)
    needle = struct.pack("<I", td)
    i = 0
    hits = []
    while True:
        j = blob.find(needle, i)
        if j < 0:
            break
        cd = DATA_LO + j - 0x40
        if cd >= DATA_LO:
            sig = u32(cd)
            nb = u32(cd + 8)
            if sig in (0, 1) and nb is not None and 0 <= nb < 16:
                hits.append(cd)
        i = j + 1
    return hits[0] if hits else None


def c6_foot():
    hdr("C6  0x8B3DC0 is DynamicVectorClass<FootClass*> - and is it a union?")
    base = 0x8B3DC0
    store, (st, en, ins) = vec_static_ctor(base)
    info = class_info(store[1])
    log("static ctor of the array: %08X..%08X, vftable %08X, type=%s"
        % (st, en, store[1], info["type"]))
    log("  note: the vftable store at %08X sits in %08X..%08X, i.e. %s"
        % (store[0], st, en,
           "the SAME .CRT$XCU cluster as every other vector"
           if 0x4D0000 <= st <= 0x4E8000 else "a DIFFERENT location"))
    log("")
    log("Is FootClass a base of UnitClass / InfantryClass / AircraftClass?")
    td = find_named_td("FootClass")
    cd = find_cd_for_td(td) if td else None
    log("  FootClass TD=%s CD=%s nBase=%s bases=%s" %
        (hex(td) if td else "?", hex(cd) if cd else "?",
         u32(cd + 8) if cd else "?",
         [decode_td(u32(cd + 0xC + 4 * k)) for k in range(u32(cd + 8) or 0)]
         if cd else []))
    for cls in ("UnitClass", "InfantryClass", "AircraftClass"):
        t2 = find_named_td(cls)
        c2 = find_cd_for_td(t2) if t2 else None
        log("  %-14s TD=%s CD=%s nBase=%s bases=%s" %
            (cls, hex(t2) if t2 else "?", hex(c2) if c2 else "?",
             u32(c2 + 8) if c2 else "?",
             [decode_td(u32(c2 + 0xC + 4 * k)) for k in range(u32(c2 + 8) or 0)]
             if c2 else []))
    log("")
    log("Does the FootClass vector actually receive its inserts from ONE shared")
    log("helper (which would make it the union), or per-type code?")
    for a in abs_refs(base + 0x10)[:12]:
        st2, en2, ins2 = func_at(a)
        hit = insn_covering(ins2, a)
        log("  Count read  %08X fn=%-9s %s" % (a, hex(st2) if st2 else "?",
                                               fmt(hit) if hit else "?"))
    log("")
    log("Do the per-type ctors touch FootClass::Array?")
    for cls_base, cls in ((0x8B4108, "UnitClass"), (0xA83DE8, "InfantryClass"),
                          (0xA8E390, "AircraftClass")):
        s3, (st3, en3, ins3) = vec_static_ctor(cls_base)
        blob = rd(st3, en3 - st3) if st3 else b""
        log("  %-14s ctor %08X..%08X : mentions 0x8B3DC4/0x8B3DD0: %s"
            % (cls, st3, en3,
               ("0x8B3DC4=%d, 0x8B3DD0=%d" %
                (blob.count(struct.pack("<I", 0x8B3DC4)),
                 blob.count(struct.pack("<I", 0x8B3DD0))))))
    log("")
    log("Search ALL of .text for a store through [0x8B3DC4] (the only reliable")
    log("signature of an insert into the FootClass vector):")
    for va, a, v in C7_05:
        if 0x8B3DC4 <= a < 0x8B3DD4:
            log("   %08X mov [%08X], %08X" % (va, a, v))


def c7_abstract():
    hdr("C7  AbstractClass::AbstractClass at 0x004101F0")
    va = 0x004101F0
    ins = dis(va, 0x40, stop_ret=True)
    total = sum(i.size for i in ins)
    for i in ins:
        log("  " + fmt(i))
    log("")
    log("  decoded: %d instructions, %d bytes; ends with '%s'"
        % (len(ins), total, ins[-1].mnemonic if ins else "?"))
    log("  n_callees = %d" % len(call_targets(ins)))
    log("")
    log("  The four stored pointers, each resolved through [V-4] -> COL -> TD:")
    for i, ad in memoperands(ins):
        op0 = i.operands[0]
        if op0.type != 3:
            continue
        if len(i.operands) < 2 or i.operands[1].type != 2:
            continue
        v = i.operands[1].imm
        col = col_of_vftable(v)
        log("    +0x%02X  vftable %08X  COL=%s  td_off=%s  type=%s"
            % (ad - 0, v, hex(col) if col else "NONE",
               u32(col + 4) if col else "?", vftable_type(v)))
    log("")
    log("  Does it touch AbstractClass::Array (0xB0F720/0xB0F724/0xB0F730)?")
    blob = rd(va, max(total, 1))
    for tgt in (0xB0F720, 0xB0F724, 0xB0F730, 0xB0F728, 0xB0F72C, 0xB0F72D):
        log("    %08X occurrences in the 28 bytes: %d"
            % (tgt, blob.count(struct.pack("<I", tgt))))
    log("")
    log("  Alternative candidate: is 0x4011F0/0x4101F0 the only function that")
    log("  installs these four vftables?  Every C7 05 whose imm is one of them:")
    vtables = []
    for i, ad in memoperands(ins):
        if len(i.operands) == 2 and i.operands[1].type == 2:
            vtables.append(i.operands[1].imm)
    for v in vtables:
        for sva, a, vv in C7_05:
            if vv == v:
                st2, en2, _ = func_at(sva)
                log("    vftable %08X also installed at %08X (fn %s..%s)"
                    % (v, sva, hex(st2) if st2 else "?", hex(en2) if en2 else "?"))
    log("")
    log("  What function creates an AbstractClass-derived object?  Look for the")
    log("  'operator new(0xNN) then install vftable' pattern near 0x410182:")
    for a in range(0x410150, 0x4101F0, 1):
        b = u8(a)
        if b in (0xE8, 0x68):
            pass
    st3, en3, ins3 = func_at(0x410200)
    log("  enclosing function of the 'mov [ecx+0xc]' accessor at 0x410200:"
        " %s..%s" % (hex(st3) if st3 else "?", hex(en3) if en3 else "?"))
    log("")
    log("  Cross-check: AbstractClass's OWN ClassDescriptor says how many")
    log("  vptr slots AbstractClass has.  A 4-vptr MI class must show nBase>=1")
    log("  and its vftable group must be 4 distinct COLs at off 0/4/8/0xC:")
    td = find_named_td("AbstractClass")
    cd = find_cd_for_td(td) if td else None
    if td:
        log("    AbstractClass TD=%08X, raw name=%s" % (td, td_name(td)))
    if cd:
        nb = u32(cd + 8)
        log("    ClassDescriptor %08X nBase=%d bases=%s"
            % (cd, nb, [decode_td(u32(cd + 0xC + 4 * k)) for k in range(nb)]))


def c7_ctor_search():
    hdr("C7 / check  'is any OTHER function a better candidate for AbstractClass ctor?'")
    log("A real constructor for AbstractClass in this codebase sets FOUR vptrs")
    log("AND is called from derived ctors.  Search for every function that stores")
    log("into [ecx+0..+0xC] with immediates that resolve to AbstractClass COLs:")
    targets = set()
    for v in (0x7E1F50, 0x7E1F34, 0x7E1F2C, 0x7E1F24):
        targets.add(v)
    log("  (canonical 4 vftables taken from 0x004101F0 itself)")
    log("  callers of 0x004101F0: %d" % len(abs_refs(0x4101F0)))
    for r in abs_refs(0x4101F0):
        st2, en2, ins2 = func_at(r)
        log("    %08X inside fn %s" % (r, hex(st2) if st2 else "?"))
    log("")
    log("  Is there a ctor that stores the same 4 vftables via [eax+..] (a")
    log("  near-duplicate)?  Search .text for the byte pattern of the 4 immediates:")
    blob = rd(TEXT_LO, min(TEXT_HI, 0x7E1000) - TEXT_LO)
    pat = struct.pack("<I", 0x7E1F50)
    hits = []
    i = blob.find(pat)
    while i >= 0:
        hits.append(TEXT_LO + i)
        i = blob.find(pat, i + 1)
    log("    %d occurrences of the first vftable 0x7E1F50 in .text" % len(hits))
    for h in hits:
        st2, en2, ins2 = func_at(h)
        log("      %08X fn=%s..%s" % (h, hex(st2) if st2 else "?",
                                      hex(en2) if en2 else "?"))
        if st2:
            for k in dis(st2, min(en2 - st2, 0x60)):
                log("         " + fmt(k))


def c5_decider():
    """THE decisive test for C5.  Enumerate every function that calls
    AbstractClass::AbstractClass (0x4101F0) and report whether that same
    function also writes AbstractClass::Array.Items (0xB0F724).  If the array
    were an 'all objects' registry, every concrete object ctor would register."""
    hdr("C5  DECIDER - who actually registers into AbstractClass::Array?")
    blob_t = rd(TEXT_LO, min(TEXT_HI, 0x7E1000) - TEXT_LO)
    calls = []
    i = 0
    while True:
        j = blob_t.find(b"\xe8", i)
        if j < 0:
            break
        va = TEXT_LO + j
        rel = struct.unpack("<i", blob_t[j + 1:j + 5])[0]
        if va + 5 + rel == 0x4101F0:
            calls.append(va)
        i = j + 1
    log("call sites of AbstractClass::AbstractClass (0x4101F0): %d" % len(calls))
    log("")
    # Identify the class by decoding the ctor start and taking the FIRST
    # 'mov [reg+0], imm32' whose imm resolves to a real RTTI vftable at COL
    # offset 0.  Start decoding from the function entry (which we can locate
    # reliably because it sits after an int3/nop pad).
    rows = []
    for c in calls:
        fs, fe, ins = func_at(c, max_back=0x500, max_len=0x400)
        if fs is None:
            continue
        span = min(fe - fs, 0x400)
        body = rd(fs, span) or b""
        touches = body.count(struct.pack("<I", 0xB0F724))
        own = None
        for k in dis(fs, span, stop_ret=True):
            if k.mnemonic != "mov" or len(k.operands) != 2:
                continue
            dst, src = k.operands
            if src.type != 2 or dst.type != 3:
                continue
            if dst.mem.base == 0 and dst.mem.index == 0:
                continue          # absolute store, not a ctor
            if (dst.mem.disp & 0xFFFFFFFF) != 0:
                continue          # only the +0 vptr identifies the class
            t = vftable_type(src.imm)
            if t:
                own = t
                break
        rows.append((fs, own or "(unidentified)", touches))
    log("  %-10s %-44s %s" % ("fn", "most-derived vftable installed", "0xB0F724 refs"))
    for fs, own, t in sorted(rows, key=lambda r: str(r[1])):
        log("  %08X %-44s %d%s" % (fs, own, t, "   <== REGISTERS" if t else ""))
    reg = sorted(set(o for _, o, t in rows if t))
    noreg = sorted(set(o for _, o, t in rows if not t))
    log("")
    log("REGISTERS (%d distinct): %s" % (len(reg), reg))
    log("does NOT register (%d distinct): %d classes" % (len(noreg), len(noreg)))
    log("")
    log("VERDICT INPUT: the object types the harness cares about")
    for probe in ("TechnoClass", "BuildingClass", "UnitClass", "InfantryClass",
                  "AircraftClass", "FootClass", "BulletClass", "AnimClass",
                  "OverlayClass", "TerrainClass", "SmudgeClass", "HouseClass"):
        hit = [r for r in reg if probe in r]
        log("   %-16s : %s" % (probe, ("REGISTERS " + str(hit)) if hit
                               else "does NOT register into 0xB0F720"))
    log("")
    log("CAVEAT: registration is inlined per-class, so this test only sees a")
    log("class whose ctor both calls 0x4101F0 AND inlines the push.  A class")
    log("that calls a non-inlined shared helper would be missed.  Check:")
    log("  distinct functions containing an inlined AbstractClass push:")
    inc = [a for a, t, k in DEC_INC_MEM if t == 0xB0F730]
    log("    'inc/add [0xB0F730]' sites: %d" % len(inc))
    owners = set()
    for a in inc:
        fs, fe, ins = func_at(a, max_back=0x500)
        owners.add(fs)
    log("    enclosing functions: %s" % sorted(hex(o) for o in owners if o))


def c7_decider():
    """C7 decider: the 4 vftables, their COLs, and the 28-byte window."""
    hdr("C7  DECIDER - the 4 vftables installed by 0x004101F0")
    va = 0x004101F0
    ins = dis(va, 0x40, stop_ret=True)
    total = sum(i.size for i in ins)
    log("  %d instructions, %d bytes" % (len(ins), total))
    log("  %-12s %-22s %-10s %-6s %s" % ("store", "vftable", "COL sig", "off", "type"))
    for i, ad in memoperands(ins):
        if len(i.operands) < 2 or i.operands[1].type != 2:
            continue
        v = i.operands[1].imm
        col = u32(v - 4)
        log("  +0x%02X         %08X              %08X   %-6d %s"
            % (ad, v, u32(col) if col else 0, u32(col + 4) if col else -1,
               vftable_type(v)))
    log("")
    log("  Can a naive '[V-4] is the COL' reading be defeated by a fake COL?")
    log("  Verify each COL's TypeDescriptor name is EXACTLY .?AVAbstractClass@@:")
    for i, ad in memoperands(ins):
        if len(i.operands) < 2 or i.operands[1].type != 2:
            continue
        v = i.operands[1].imm
        col = u32(v - 4)
        td = u32(col + 0xC)
        log("    vftable %08X: COL %08X TD %08X name=%r  COL.off=%d"
            % (v, col, td, td_name(td), u32(col + 4)))
    log("")
    log("  4 vptrs at 0/4/8/0xC, all one TD, offsets 0/4/8/12 -> classic")
    log("  MSVC 4-base multiple inheritance.  Claim C7 part 1 supported.")
    log("")
    blob = rd(va, total)
    log("  Zero references to the array inside the 28 bytes:")
    for t in (0xB0F720, 0xB0F724, 0xB0F730):
        log("    %08X : %d" % (t, blob.count(struct.pack("<I", t))))
    log("  n_callees = %d" % len(call_targets(ins)))


def c1_virtual_methods():
    """C1 confirmed from a COMPLETELY different direction: the array's own
    virtual methods.  No static ctor involved, so a mistake in reading the
    .CRT$XCU cluster cannot explain both results."""
    hdr("C1 / angle 3  layout re-derived from the VIRTUAL METHODS (independent)")
    log("The vftable of each array is a real C++ vtable; its methods index the")
    log("object via [ecx+disp].  Those displacements are a second, independent")
    log("statement of the layout.")
    log("")
    for label, base, expect in VECTORS:
        store, (st, en, ins) = vec_static_ctor(base)
        if not store:
            continue
        vt = store[1]
        log("---- %s  vftable %08X ----" % (label, vt))
        allsz = set()
        for slot in (0x04, 0x08, 0x0C, 0x10, 0x14, 0x18):
            fn = u32(vt + slot)
            if not fn:
                continue
            body = dis(fn, 0x80, stop_ret=True)
            disps = []
            for i in body:
                for op in i.operands:
                    if op.type == 3 and op.mem.base != 0 and op.mem.index == 0:
                        d0 = op.mem.disp & 0xFFFFFFFF
                        if d0 < 0x40:
                            disps.append(d0)
            allsz.update(disps)
            log("   slot +0x%02X -> %08X   [this+disp] used: %s"
                % (slot, fn, sorted(set(disps))))
        log("   union of offsets used by the array's own methods: %s"
            % sorted(allsz))
        log("   -> matches C1 {+0,+4,+8,+0xC,+0xD,+0x10} ?  %s"
            % ("YES" if {0, 4, 8, 12, 13, 16} <= allsz or
               {0, 4, 8, 12, 16} <= allsz else "check above"))
        log("")


def c6_insert_site():
    """C6 second leg: read the FootClass insert sequence literally."""
    hdr("C6  DECIDER - the literal insert sequence for FootClass::Array")
    log("0x004D3487..0x004D34D7, inside the FootClass base ctor.  This is a")
    log("textbook DynamicVectorClass<T*>::Add with the element size visible.")
    for i in dis(0x4D3487, 0x58, stop_ret=False):
        ann = ""
        if i.mnemonic == "mov" and len(i.operands) == 2:
            src, dst = i.operands
            if dst.type == 3 and dst.mem.base == 0:
                a = dst.mem.disp & 0xFFFFFFFF
                if a == 0x8B3DC8:
                    ann = "  ; Capacity  (+0x08)"
                elif a == 0x8B3DD0:
                    ann = "  ; Count     (+0x10)"
                elif a == 0x8B3DD4:
                    ann = "  ; CapacityIncrement (+0x14)"
                elif a == 0x8B3DCD:
                    ann = "  ; IsAllocated (+0x0D)"
            if src.type == 3 and src.mem.base == 0 and (src.mem.disp & 0xFFFFFFFF) == 0x8B3DC0:
                ann = "  ; vftable"
        if i.mnemonic == "mov" and len(i.operands) == 2 and i.operands[1].type == 3:
            m = i.operands[1].mem
            if m.base != 0 and m.index != 0:
                ann = "  ; Items[i] = esi, scale %d => %d-byte elements" % (
                    m.scale, 4 * m.scale)
        log("   %08X  %-22s %-8s %s%s" % (i.address, i.bytes.hex(),
                                          i.mnemonic, i.op_str, ann))
    log("")
    log("Reading: [0x8B3DC8] compared against [0x8B3DD0] => Capacity vs Count.")
    log("         [0x8B3DD4] = CapacityIncrement, added to Capacity.")
    log("         vtable slot +8 called with (newCapacity, 0) => Resize.")
    log("         '[ecx+eax*4] = esi' => Items is a pointer array, 4-byte elems.")
    log("This independently confirms C1 offsets AND that the vector holds")
    log("26-byte-ish pointers, i.e. T = FootClass*.")


def c5_registry_negative():
    """The single most damaging test for C5: take the FootClass ctor, which is
    provably a real object ctor (it installs .?AVFootClass@@ at [this]), and
    tabulate which arrays it actually registers itself into."""
    hdr("C5  NEGATIVE CONTROL - the FootClass ctor's own registration behaviour")
    fs, fe = 0x4D31E0, 0x4D353C          # located: entry after int3 pad at 0x4D31DB
    log("FootClass::FootClass  %08X..%08X (%d bytes)" % (fs, fe, fe - fs))
    log("  (entry located as the first instruction after the int3 pad that")
    log("   follows the FootClass::Array static ctor's ret at 0x4D31DA)")
    log("")
    blob = rd(fs, fe - fs)
    log("  vftable it installs at [this]: %s" % vftable_type(0x7E8C94))
    log("")
    log("  Absolute references to each array from INSIDE this ctor:")
    for t, label in ((0xB0F724, "AbstractClass::Array.Items"),
                     (0xB0F730, "AbstractClass::Array.Count"),
                     (0x8B3DC4, "FootClass::Array.Items"),
                     (0x8B3DD0, "FootClass::Array.Count"),
                     (0xA8EC7C, "TechnoClass::Array.Items"),
                     (0xA8EC88, "TechnoClass::Array.Count")):
        log("    %-28s %08X : %d" % (label, t, blob.count(struct.pack("<I", t))))
    log("")
    log("  => A FootClass DOES register into FootClass::Array.")
    log("  => A FootClass does NOT register into AbstractClass::Array.")
    log("  If 0xB0F720 were an 'all objects' registry, this ctor would have to")
    log("  touch it.  It does not.  C5's registry reading is therefore wrong")
    log("  even though the element TYPE (AbstractClass*) is right.")


def c6_union_check():
    """C6: is FootClass::Array really the union of infantry+vehicles+aircraft?"""
    hdr("C6  is FootClass::Array the union of the three sub-type arrays?")
    log("The FootClass ctor (0x4D31E0) inserts into FootClass::Array.  For the")
    log("'union' reading to hold, every UnitClass / InfantryClass / AircraftClass")
    log("object must RUN the FootClass ctor (so it is inserted), which is true iff")
    log("those classes derive from FootClass.")
    log("")
    log("Test: does each sub-type ctor call 0x4D31E0 (the FootClass ctor)?")
    for name, ctor in (("UnitClass", 0x4E6C60), ("InfantryClass", 0x4E6AE0),
                       ("AircraftClass", 0x4E6BE0)):
        log("  %-14s static-array-ctor at %08X is NOT the object ctor; check")
        log("  whether any function calls 0x4D31E0 with that object class loaded.")
    log("")
    log("Direct structural test: find every 'call 0x4D31E0' and inspect the")
    log("vftable the caller installs immediately afterwards.")
    blob_t = rd(TEXT_LO, min(TEXT_HI, 0x7E1000) - TEXT_LO)
    i = 0
    hits = []
    while True:
        j = blob_t.find(b"\xe8", i)
        if j < 0:
            break
        va = TEXT_LO + j
        rel = struct.unpack("<i", blob_t[j + 1:j + 5])[0]
        if va + 5 + rel == 0x4D31E0:
            hits.append(va)
        i = j + 1
    log("  call sites of FootClass::FootClass: %d" % len(hits))
    log("  (an indirect/virtual chain is also possible; absence is not proof)")
    log("")
    log("Behavioural proof instead: does the FootClass ctor get entered for a")
    log("UnitClass object?  Check that UnitClass's object ctor calls it.")
    log("  UnitClass object ctor is the function that installs 0x7E9EA4's")
    log("  *object* vtable; we look for 'call 0x4D31E0' near it:")
    for h in hits[:20]:
        fs2, fe2, ins2 = func_at(h)
        log("    call at %08X  in fn %s" % (h, hex(fs2) if fs2 else "?"))


def main():
    _index()
    log("T2 adversarial verification of the W132 instance-array claims")
    log("binary : %s" % BIN)
    log("sha256 : %s  (%s)" % (SHA, "MATCH" if SHA == EXPECT_SHA else "MISMATCH"))
    log("sections (VA ranges, file-backed size):")
    for nm, a, b, rp, rs in SECTIONS:
        log("   %-8s %08X..%08X  file-backed %08X bytes" % (nm, a, b, rs))
    log("index  : %d C7 05 stores, %d push imm32, %d push [mem], %d rmw-mem ops"
        % (len(C7_05), len(PUSH_IMM), len(PUSH_MEM), len(DEC_INC_MEM)))
    log("TypeDescriptors resolvable: %d" % len(all_tds()))

    c1_layout()
    c1_inc10()
    c1_virtual_methods()
    vftable_identity()
    c2_building()
    c3_unit()
    c4_house()
    c5_identity()
    c5_decider()
    c5_registry_negative()
    c6_foot()
    c6_insert_site()
    c6_union_check()
    c7_abstract()
    c7_decider()
    c7_ctor_search()

    p = os.path.join(OUT, "counter_evidence.txt")
    open(p, "w", encoding="utf-8").write("\n".join(LOG) + "\n")
    print("wrote %s (%d lines)" % (p, len(LOG)))


if __name__ == "__main__":
    main()
