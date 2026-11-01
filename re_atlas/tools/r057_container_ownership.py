# -*- coding: utf-8 -*-
"""R-057: what object is `this` for the INI-ish lookup family -- and the interleave conflict.

gamemd.exe sha256 73201cc0...f67476, read-only.  Every window machine-dumped
(out/_probe_r057*.py) BEFORE the assertion was written (G-65).

THE FINDING
-----------
The "lookup container" is a sorted associative array with a FIXED 4-field shape:

    +0x0  = element-array base     +0x4  = element count
    +0xC  = "sorted" flag byte     +0x10 = last-hit cache

That shape is verified at four DIFFERENT host offsets, so it is one container TYPE
embedded in several hosts -- not four different field layouts:

    host                         container base      fields seen
    ---------------------------  ------------------  ----------------------------
    0x52B4F0 / 0x52B620 (twins)  this + 0x00         +0 +4 +0xC +0x10
    0x52A4D0                     this + 0x2C         +0x2C +0x30 +0x38 +0x3C
    0x528A10  path A             [arg+8] + 0x2C     +0x2C(+0) +0x30(+4) +0x3C(+0x10)
    0x528A10  path B             this + 0x28         +0x28(+0) +0x2C(+4) +0x34(+0xC) +0x38(+0x10)

THE CONFLICT (reported, not papered over)
-----------------------------------------
The `this+0x28` view and the `this+0x2C` view INTERLEAVE:
    offset 0x2C is COUNT in the +0x28 view but the ARRAY BASE in the +0x2C view;
    offset 0x38 is the CACHE in the +0x28 view but the SORTED FLAG in the +0x2C view.
Two plain embedded structs cannot share those bytes.  So `0x528A10`'s `this` and
`0x52A4D0`'s `this` are DIFFERENT object types -- and since `0x52A4D0` is
UNREACHABLE (0 E8 callers, 0 E9, 0 vtable entries, verified 3 ways below), its
`this` type is UNKNOWN.  R-055 booked `0x52A4D0`'s `+0x38`/`+0x3C` semantics onto
INIClass; that attribution is therefore UNPROVEN, not refuted.

Assertions are read through `read()` so R057_MUTATE applies (G-71 cause 2: a census
that scans BLOB directly makes every disp mutation survive -- the R-056 M16 hole).

Run:  python re_atlas/tools/r057_container_ownership.py
Mut:  R057_MUTATE="VA=BYTE,..." in-process injection
"""
import hashlib
import os
import re
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

RAW = bytearray(open(EXE, "rb").read())
MUT = {}
for _it in os.environ.get("R057_MUTATE", "").split(","):
    if "=" in _it:
        _k, _v = _it.split("=", 1)
        MUT[int(_k, 0)] = int(_v, 0) & 0xFF

e = struct.unpack_from("<I", RAW, 0x3C)[0]
nsec = struct.unpack_from("<H", RAW, e + 6)[0]
optsz = struct.unpack_from("<H", RAW, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", RAW, opt + 28)[0]
tab = opt + optsz
SEC = []
for i in range(nsec):
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", RAW, tab + i * 40 + 8)
    SEC.append((vaddr, vsize, rawptr, rawsize))
assert SEC[0] == (0x1000, 0x3DF38D, 0x1000, 0x3E0000), "section tuple drift %r" % (SEC[0],)
TEXT_LO, TEXT_HI = 0x401000, 0x7E0000
BLOB = bytes(RAW)


def fileoff(va):
    rva = va - IB
    for s, vs, rp, rs in SEC:
        if s <= rva < s + vs:
            fo = rp + (rva - s)
            return fo if fo < rp + rs else None
    return None


def vaof(fo):
    for s, vs, rp, rs in SEC:
        if rp <= fo < rp + rs:
            return (fo - rp) + s + IB
    return None


_TEXT_FO_LO, _TEXT_FO_HI = fileoff(TEXT_LO), fileoff(TEXT_HI)


def read(va, n):
    out = bytearray()
    for k in range(n):
        fo = fileoff(va + k)
        if fo is None:
            return None
        out.append(MUT.get(va + k, RAW[fo]))
    return bytes(out)


def eqhex(va, const):
    """Read length comes FROM the constant (G-65: a hand-typed length cannot truncate)."""
    n = len(const) // 2
    got = read(va, n)
    return got is not None and got.hex() == const.lower()


md = Cs(CS_ARCH_X86, CS_MODE_32)
FAILS = []
NPASS = [0]
UNCOUNTED = []


def ok(label, cond, detail=""):
    if cond:
        NPASS[0] += 1
        print("%s PASS: %s" % (label, detail))
    else:
        FAILS.append(label)
        print("%s FAIL: %s" % (label, detail))


def structural(label, cond, detail=""):
    if cond:
        UNCOUNTED.append(label)
        print("%s OK (structural; not counted): %s" % (label, detail))
    else:
        FAILS.append(label)
        print("%s FAIL: (structural) %s" % (label, detail))


def insns(va, n):
    return list(md.disasm(read(va, n), va))


MEM = re.compile(r"\[(\w+)(?:\s*\+\s*(0x[0-9a-fA-F]+|\d+))?\]")


def footprint(lo, hi, base):
    """Set of displacements used against one base register.
    Accepts BOTH hex and DECIMAL displacements: capstone prints small disp as decimal
    ("[esi + 4]") and large as hex ("[esi + 0xc]").  A 0x-only regex silently drops
    every small field -- the G-73/G-74 "narrow census => false structure" trap."""
    out = set()
    for i in insns(lo, min(hi, lo + 0x400) - lo):
        for m in MEM.finditer(i.op_str):
            if m.group(1) != base:
                continue
            ds = m.group(2)
            out.add(0 if not ds else (int(ds, 16) if ds.startswith("0x") else int(ds)))
    return out


_CENSUS_CACHE = {}


def _census():
    """ONE pass over .text collecting every E8 target, E9 target and dword value.

    Why one pass: the mutation suite runs this gate ~19 times; doing four separate
    4 MB sweeps per run made the suite exceed its timeout.  Keyed on the mutation
    signature so R057_MUTATE still takes effect (G-71 cause 2)."""
    key = tuple(sorted(MUT.items()))
    if key in _CENSUS_CACHE:
        return _CENSUS_CACHE[key]
    e8, e9, dwords = {}, {}, {}
    fo, addr = _TEXT_FO_LO, TEXT_LO
    while fo < _TEXT_FO_HI:
        for i in md.disasm(BLOB[fo:fo + 16], addr):
            raw = read(i.address, 5)
            if raw is not None and i.mnemonic == "call" and raw[0] == 0xE8:
                d = struct.unpack_from("<i", raw, 1)[0]
                e8.setdefault(i.address + 5 + d, []).append(i.address)
            fo += i.size
            addr += i.size
            break
        else:
            fo += 1
            addr += 1
    for f in range(_TEXT_FO_LO, _TEXT_FO_HI - 5):
        va = vaof(f)
        if va is None:
            continue
        if BLOB[f] == 0xE9:
            raw = read(va, 5)
            if raw is not None and raw[0] == 0xE9:
                d = struct.unpack_from("<i", raw, 1)[0]
                e9.setdefault(va + 5 + d, []).append(va)
    for f in range(_TEXT_FO_LO, _TEXT_FO_HI - 4):
        va = vaof(f)
        if va is None:
            continue
        raw = read(va, 4)
        if raw is not None:
            dwords.setdefault(struct.unpack("<I", raw)[0], []).append(va)
    _CENSUS_CACHE[key] = (e8, e9, dwords)
    return _CENSUS_CACHE[key]


def e8_callers(target):
    return _census()[0].get(target, [])


def e9_jumps(target):
    return _census()[1].get(target, [])


def vtable_refs(target):
    return _census()[2].get(target, [])


# ---------------------------------------------------------------- G0 fingerprint
h = hashlib.sha256(BLOB).hexdigest()
structural("G0", True, "sha256=%s%s" % (h[:16] + "…" + h[-6:],
                                        "" if h == SHA256 or MUT else " (MUTATED RUN)"))

print("=" * 78)
print("A) the container SHAPE, at the one host where `this` IS the container (twins)")
print("=" * 78)

fp_twin = footprint(0x52B4F0, 0x52B569, "esi")
ok("A1", fp_twin == {0x0, 0x4, 0xC, 0x10},
   "0x52B4F0 footprint over esi(=this, `mov esi,ecx`) == {+0,+4,+0xC,+0x10}; got %s"
   % sorted(hex(x) for x in fp_twin))

ok("A2", eqhex(0x52B4F1, "8bf1") and eqhex(0x52B4F3, "8b4604")
   and eqhex(0x52B4FE, "8a4e0c") and eqhex(0x52B51F, "c6460c01")
   and eqhex(0x52B518, "c7461000000000"),
   "this+0x4=count (0x52B4F3 `mov eax,[esi+4]`), +0xC=sorted byte (0x52B4FE read / "
   "0x52B51F set to 1), +0x10=cache cleared on re-sort (0x52B518)")

ok("A3", eqhex(0x52B52D, "8b4e04") and eqhex(0x52B529, "8b3e")
   and eqhex(0x52B53B, "8b34c7"),
   "this+0x0=array base (0x52B529 `mov edi,[esi]`), +0x4=count again as the search "
   "bound (0x52B52D), stride 8 (0x52B53B `[edi+eax*8]`)")

print("\n" + "=" * 78)
print("B) 0x52A4D0: the SAME container shape, embedded at this+0x2C")
print("=" * 78)

ok("B1", eqhex(0x52A4DE, "8bf1"),
   "0x52A4D0 `mov esi,ecx` => esi IS this")

ok("B2", eqhex(0x52A52A, "8b462c") and eqhex(0x52A52D, "68a0b65200")
   and eqhex(0x52A532, "6a08"),
   "array base = this+0x2C (0x52A52A `mov eax,[esi+0x2C]` pushed into qsort with width 8)")

ok("B3", eqhex(0x52A545, "8b5630"),
   "count = this+0x30 (0x52A545 `mov edx,[esi+0x30]`)")

ok("B4", eqhex(0x52A525, "385e38") and eqhex(0x52A541, "c6463801"),
   "sorted flag = byte this+0x38 (0x52A525 `cmp byte [esi+0x38],bl` / 0x52A541 set to 1)")

ok("B5", eqhex(0x52A51A, "8b463c") and eqhex(0x52A53E, "895e3c")
   and eqhex(0x52A561, "89463c"),
   "cache = this+0x3C (read 0x52A51A / cleared 0x52A53E / refilled 0x52A561)")

print("\n" + "=" * 78)
print("C) 0x528A10 holds TWO containers, in two DIFFERENT objects")
print("=" * 78)

# C1: ebp == ecx (this) and ebp is never rewritten => [ebp+0x28] really is this+0x28
ebp_writes = [i for i in insns(0x528A10, 0x528BC6 - 0x528A10)
              if re.match(r"^ebp,", i.op_str) and i.mnemonic in
              ("mov", "lea", "add", "sub", "xor", "pop", "and", "or", "inc", "dec")]
ok("C1", len(ebp_writes) == 1 and ebp_writes[0].mnemonic == "mov"
   and ebp_writes[0].op_str == "ebp, ecx",
   "ebp is written exactly %d time(s) in 0x528A10 (%s) => ebp stays == this, so "
   "[ebp+disp] IS this+disp (no rebase trap here)"
   % (len(ebp_writes), [("%s %s" % (i.mnemonic, i.op_str)) for i in ebp_writes]))

# C2/C3: path B container = this+0x28
ok("C2", eqhex(0x528B16, "8d7528"),
   "path B takes its container as `lea esi,[ebp+0x28]` => this+0x28")

ok("C3", eqhex(0x528B1F, "8b4604") and eqhex(0x528B26, "8b4610")
   and eqhex(0x528B41, "894610"),
   "path B container fields: +4 = count (0x528B1F), +0x10 = cache (read 0x528B26 / "
   "refill 0x528B41) => this+0x2C and this+0x38")

# C4/C5: path A container = [arg+8]+0x2C
ok("C4", eqhex(0x528A55, "8b7508") and eqhex(0x528A86, "83c62c"),
   "path A loads esi from the STACK ARG (`mov esi,[ebp+8]`) then rebases with "
   "`add esi,0x2C` => container base is [arg+8]+0x2C, NOT this+0x2C")

ok("C5", eqhex(0x528A83, "8b4e30") and eqhex(0x528A95, "8b4e10"),
   "path A reads `[esi+0x30]` BEFORE the add (0x528A83) => that operand is "
   "[arg+8]+0x30 = container+4 (the count); the cache read 0x528A95 happens AFTER "
   "the add => [arg+8]+0x3C = container+0x10")

print("\n" + "=" * 78)
print("D) embedding offset +0x2C is PROVEN by a LIVE caller; the first draft's")
print("   'interleave conflict' compared two DIFFERENT classes and was an artifact")
print("=" * 78)

# D1: the decisive evidence -- a live caller reads the count at host+0x30, rebases to
# host+0x2C, then passes that as `this` to the twin.  0x52772C is a caller R-056 never
# inspected (R-056 only looked at 0x528A10's own two paths).
ok("D1", eqhex(0x52772C, "8b4e3083c62c85c9") and eqhex(0x52774D, "8bce")
   and eqhex(0x527750, "e89b3d0000"),
   "0x52772C: `mov ecx,[esi+0x30]` (count) -> `add esi,0x2C` (rebase) -> "
   "`mov ecx,esi; call 0x52B4F0`.  So the container sits at host+0x2C and the host "
   "reads its count at +0x30 -- exactly the map 0x52A4D0 uses.")

# D2: fold the container layout onto the host; it must land one-for-one on 0x52A4D0.
# R-059 rewrite: the first draft was `0x2C+0x0==0x2C and 0x2C+4==0x30 ...` -- arithmetic
# over LITERALS, no byte read at all, hence no mutation could ever redden it (G-77:
# a gate that cannot go red is decoration).  The fold is now COMPUTED FROM BYTES:
# the rebase imm8, the witness's container-relative cache disp, and 0x52A4D0's own
# host-level base/count/cache disps are all read from the image, and the fold must
# hold on the VALUES READ.  Mutate any one of the five bytes and D2 goes red.
_D2_rebase = read(0x527731, 1)[0]          # `add esi,0x2c` imm8  (witness1 rebase)
_D2_twinC = read(0x527740, 1)[0]           # `mov ecx,[esi+0x10]` disp (post-rebase)
_D2_hostBase = read(0x52A52C, 1)[0]        # 0x52A4D0: `mov eax,[esi+0x2C]` disp
_D2_hostCount = read(0x52A547, 1)[0]       # 0x52A4D0: `mov edx,[esi+0x30]` disp
_D2_hostCache = read(0x52A51C, 1)[0]       # 0x52A4D0: `mov eax,[esi+0x3C]` disp
ok("D2", _D2_rebase == 0x2C and _D2_twinC == 0x10
   and _D2_rebase + _D2_twinC == _D2_hostCache == 0x3C
   and _D2_hostBase == _D2_rebase and _D2_hostCount == _D2_rebase + 4,
   "fold computed FROM BYTES: rebase=%s + twin-cache-disp=%s == 0x52A4D0's cache disp=%s, "
   "and its base disp==rebase, count disp==rebase+4 => the SAME container read "
   "through the two views => ONE structure" % (hex(_D2_rebase), hex(_D2_twinC), hex(_D2_hostCache)))

# D3: record the first draft's error as an assertion about its PREMISE, so a future
# reader cannot re-derive the bogus conflict.
ok("D3", eqhex(0x528B18, "28") and eqhex(0x527731, "2c"),
   "0x528A10 path B embeds at this+0x28, the live caller embeds at host+0x2C. Both "
   "are real; they conflict ONLY IF 0x528A10's `this` and that caller's host were "
   "the same class -- and NOTHING establishes that. The first draft assumed it "
   "silently, so the 'interleave' was an artifact of comparing two different "
   "objects' field maps, NOT a property of any object.")

print("\n" + "=" * 78)
print("E) 0x52A4D0 is UNREACHABLE by all three channels => its `this` type is unknown")
print("=" * 78)

c_e8 = e8_callers(0x52A4D0)
c_e9 = e9_jumps(0x52A4D0)
c_vt = vtable_refs(0x52A4D0)
ok("E1", c_e8 == [] and c_e9 == [] and c_vt == [],
   "0x52A4D0: E8 callers=%d, E9 jumps=%d, dword refs in .text=%d  -- all zero, "
   "so this function is reachable only indirectly (or is dead); nothing pins its "
   "`this` type" % (len(c_e8), len(c_e9), len(c_vt)))

# E2 positive control: the SAME three channels DO find callers for a live neighbour,
# so E1's zeros are a real property of 0x52A4D0, not a broken census (G-13).
ok("E2", len(e8_callers(0x52B4F0)) == 22 and len(e8_callers(0x528A10)) > 100,
   "positive control on the same census code: 0x52B4F0 -> %d callers, "
   "0x528A10 -> %d callers (so the zero for 0x52A4D0 is real, not a dead scanner)"
   % (len(e8_callers(0x52B4F0)), len(e8_callers(0x528A10))))

print("\n" + "=" * 78)
print("F) INIClass ctor: the zero-init set, and what it does NOT prove")
print("=" * 78)

ok("F1", eqhex(0x52CC21, "895e28895e2c895e30885e34895e38895e3c885e40"),
   "ctor zero-init block 0x52CC21..0x52CC35: +0x28,+0x2C,+0x30,byte+0x34,+0x38,"
   "+0x3C,byte+0x40 -- i.e. the union of BOTH views, which is exactly why the ctor "
   "cannot discriminate between them (zeroing is symmetric)")

ok("F2", eqhex(0x52CC36, "c706f41a7e00"),
   "and then stamps vptr 0x7E1AF4 (the CCINIClass vtable R-055 recorded)")

ok("F3", eqhex(0x52CC0B, "8d7e0c") and eqhex(0x52CC16, "e8c5e0ffff")
   and eqhex(0x52CC1B, "c707fc1a7e00"),
   "before that it constructs an in-place member at this+0xC (`lea edi,[esi+0xC]`, "
   "call 0x52ACE0, stamp sub-vptr 0x7E1AFC) => INIClass clearly HAS embedded "
   "sub-objects, which is consistent with the container being embedded too")

print("\n" + "=" * 78)
print("S) structural cross-checks (not in the denominator; red still exits nonzero)")
print("=" * 78)
structural("S1", footprint(0x52B620, 0x52B699, "esi") == {0x0, 0x4, 0xC, 0x10},
           "twin B has the same footprint as twin A")
# S2 is an EXACT set on purpose: a `>=` superset assertion can never be killed by
# displacing a field (G-71: an assertion that cannot go red is not an assertion).
ok("S2", footprint(0x52A4D0, 0x52A5F6, "esi") == {0x0, 0x2C, 0x30, 0x38, 0x3C},
   "0x52A4D0 footprint over esi == {+0,+0x2C,+0x30,+0x38,+0x3C} -- exactly one container "
   "at this+0x2C plus the +0 slot; got %s"
   % sorted(hex(x) for x in footprint(0x52A4D0, 0x52A5F6, "esi")))
structural("S3", len(read(0x528A10, 0x528BC6 - 0x528A10)) == 0x528BC6 - 0x528A10,
           "0x528A10 window readable to its ret 0x14 boundary")

print()
if FAILS:
    print("== R-057 %d/%d PASS, %d FAIL (structural OK unused=%d) ==" %
          (NPASS[0], NPASS[0] + len(FAILS), len(FAILS), len(UNCOUNTED)))
    print("FAILED: %s" % ", ".join(FAILS))
    sys.exit(1)
print("== R-057 %d/%d 字节断言 PASS（S1..S3 结构性不入分母，红仍非零退出）==" % (NPASS[0], NPASS[0]))
print("GATE: GREEN")
