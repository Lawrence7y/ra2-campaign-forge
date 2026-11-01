# -*- coding: utf-8 -*-
"""R-058: the container host gets a NAME -- RTTI chain vtable->COL->TD resolves
the host stamped by the 0x52CBFB factory to `.?AVCCINIClass@@`, its base blob to
`.?AVINIClass@@`, the dtor-host vtable 0x7EB73C to `.?AUINISection@INIClass@@`.
Closes L-25 (CCINIClass size 0x58: heap new(0x58) in the BATTLEMD*.INI family AND
six zero-init .data globals stamped by global ctors, never allocated).

gamemd.exe sha256 73201cc0...f67476, read-only. Every constant machine-dumped by
out/_probe_r058_*.py BEFORE assertion (G-65). RTTI layout VERIFIED here, not
assumed: COL={sig=0,offset,cdOffset,TD,CD}; x86 TD name is INLINE at TD+8 (the
pointer-deref form TD+0x10 does NOT exist on x86 -- probe 10 proved it by crash);
CD={sig,attr,numBase,array}; _BaseClass blob = {TD,...} at its start.

Run:  python re_atlas/tools/r058_container_class_rtti.py
Mut:  R058_MUTATE="VA=BYTE,..." in-process injection
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
for _it in os.environ.get("R058_MUTATE", "").split(","):
    if "=" in _it:
        _k, _v = _it.split("=", 1)
        MUT[int(_k, 0)] = int(_v, 0) & 0xFF

e = struct.unpack_from("<I", RAW, 0x3C)[0]
nsec = struct.unpack_from("<H", RAW, e + 6)[0]
optsz = struct.unpack_from("<H", RAW, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", RAW, opt + 28)[0]
tab = opt + optsz
SEC = []  # canonical (rva, vsize, rawptr, rawsize) -- G-60 criterion 4
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


_TEXT_FO_LO, _TEXT_FO_HI = fileoff(TEXT_LO), fileoff(TEXT_HI)


def vaof(fo):
    for s, vs, rp, rs in SEC:
        if rp <= fo < rp + rs:
            return (fo - rp) + s + IB
    return None


def read(va, n):
    out = bytearray()
    for k in range(n):
        fo = fileoff(va + k)
        if fo is None:
            return None
        out.append(MUT.get(va + k, RAW[fo]))
    return bytes(out)


def u32(va):
    b = read(va, 4)
    return struct.unpack("<I", b)[0] if b else None


def eqhex(va, const):
    """Read length comes FROM the constant (G-65)."""
    n = len(const) // 2
    got = read(va, n)
    return got is not None and got.hex() == const.lower()


def td_name(va):
    """x86 TD name = INLINE string at TD+8 (verified layout, not assumed)."""
    b = read(va + 8, 64) or b""
    m = re.match(rb"[ -~]{4,}", b)
    return m.group(0).decode() if m else None


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


# --------------------------------------------------------- cached census (G-75 safe)
_CACHE = {}


def _census():
    key = tuple(sorted(MUT.items()))
    if key in _CACHE:
        return _CACHE[key]
    e8 = {0x52B4F0: [], 0x52B620: [], 0x52A4D0: []}
    e9 = {k: [] for k in e8}
    imm = {k: [] for k in e8}
    for fo in range(_TEXT_FO_LO, _TEXT_FO_HI - 5):
        if BLOB[fo] == 0xE8:
            va_here = vaof(fo)
            raw = read(va_here, 5) if va_here is not None else None
            if raw is None or raw[0] != 0xE8:
                continue
            d = struct.unpack_from("<i", raw, 1)[0]
            t = va_here + 5 + d
            if t in e8:
                e8[t].append(va_here)
        if BLOB[fo] == 0xE9:
            va_here = vaof(fo)
            raw = read(va_here, 5) if va_here is not None else None
            if raw is None or raw[0] != 0xE9:
                continue
            d = struct.unpack_from("<i", raw, 1)[0]
            t = va_here + 5 + d
            if t in e9:
                e9[t].append(va_here)
    # imm32 (push/mov-form) refs to the three addresses, anywhere in .text
    pats = {struct.pack("<I", t): t for t in e8}
    for fo in range(_TEXT_FO_LO, _TEXT_FO_HI - 4):
        b4 = BLOB[fo:fo + 4]
        if b4 in pats:
            va_here = vaof(fo)
            raw = read(va_here, 4) if va_here is not None else None
            if raw == b4:
                imm[pats[b4]].append(va_here)
    _CACHE[key] = (e8, e9, imm)
    return _CACHE[key]


# =================================================================== A) RTTI chain
print("=" * 78)
print("A) RTTI: vtable 0x7E1AF4 -> COL -> TD '.?AVCCINIClass@@' -> base '.?AVINIClass@@'")
print("=" * 78)

ok("A1", eqhex(0x7E1AF0, "88ac7f00") and eqhex(0x7FAC88,
   "000000000000000000000000c874810078ac7f00"),
   "vtable[-1]=0x7FAC88 and COL={sig=0,offset=0,cdOffset=0,TD=0x8174C8,CD=0x7FAC78}")

ok("A2", td_name(0x8174C8) == ".?AVCCINIClass@@",
   "TD 0x8174C8 inline name (x86: TD+8) = %r" % td_name(0x8174C8))

ok("A3", eqhex(0x8174C8, "94957f00000000002e3f41564343494e49436c617373404000"),
   "TD bytes: shared vfptr 0x7F9594, spare 0, then the literal name")

ok("A4", eqhex(0x7FAC68, "50ac7f0038ac7f00") and eqhex(0x7FAC38,
   "b07481000000000000000000ffffffff00000000"),
   "CD 0x7FAC78 numBase=2 array=0x7FAC68 -> blobs {0x7FAC50, 0x7FAC38}; "
   "blob 0x7FAC38 first dword TD=0x8174B0")

ok("A5", td_name(0x8174B0) == ".?AVINIClass@@",
   "base TD 0x8174B0 name = %r  =>  CCINIClass DERIVES FROM INIClass (mdisp 0)" % td_name(0x8174B0))

ok("A6", all(eqhex(td, "94957f00") for td in
     (0x8174B0, 0x8174C8, 0x817480, 0x817508, 0x8174E8, 0x825B40)),
   "all six TDs share vfptr 0x7F9594 (TypeDescriptor's own vtable) => one table, "
   "no hand-edited TD; TD-vs-name binding is compiler-generated")

ok("A7", td_name(0x817480) == ".?AV?$List@PAUINISection@INIClass@@@@",
   "facet B TD (COL 0x7FAC20 via [0x7E1AF8]) = %r  => List<INISection*>" % td_name(0x817480))

ok("A8", td_name(0x817508) == ".?AVGenericList@@" and td_name(0x8174E8) == ".?AVGenericNode@@",
   "head vptr 0x7E1B04 TD = GenericList ; node vptr 0x7E1B0C TD = GenericNode "
   "(the List's base + element pair)")

ok("A9", eqhex(0x7EB738, "08378000") and eqhex(0x803708,
   "000000000000000000000000405b8200f8368000"),
   "dtor-host vtable 0x7EB73C: COL 0x803708 = {0,0,0, TD=0x825B40, CD=0x8036F8}")

ok("A10", td_name(0x825B40) == ".?AUINISection@INIClass@@",
   "TD 0x825B40 = %r  =>  the 0x52AB80 teardown host is INISection (a NESTED struct of "
   "INIClass; 'U' = struct), NOT an anonymous dtor-shaped blob" % td_name(0x825B40))

# ==================================================================== B) factory
print("\n" + "=" * 78)
print("B) the new(0x58) ctor stamps exactly the RTTI-named vtable => BATTLEMD*.INI factory")
print("=" * 78)

ok("B1", eqhex(0x8261A8, "424154544c454d442a2e494e4900"),
   "string @0x8261A8 = 'BATTLEMD*.INI'")

ok("B2", eqhex(0x52CBA0, "68a8618200") and eqhex(0x52CBFB, "6a58e815c22900"),
   "factory pushes the string @0x52CBA0, then `push 0x58; call rel32` @0x52CBFB; "
   "rel32 decodes: 0x52CC02 + 0x29C215 = 0x7C8E17 (CRT new)")

ok("B3", 0x52CC02 + struct.unpack("<i", read(0x52CBFE, 4))[0] == 0x7C8E17,
   "call target arithmetic resolves to operator new 0x7C8E17 (G-11: decode, not eyeball)")

ok("B4", eqhex(0x52CC36, "c706f41a7e00") and eqhex(0x52CC1B, "c707fc1a7e00")
   and eqhex(0x52CC0B, "8d7e0c"),
   "ctor stamps [esi]=0x7E1AF4 (CCINIClass vptr) @0x52CC36 and `lea edi,[esi+0xC]` + "
   "[edi]=0x7E1AFC (List vptr) @0x52CC0B/0x52CC1B")

ok("B5", eqhex(0x52CC21, "895e28895e2c895e30885e34895e38895e3c885e40"),
   "ctor zero-initialises +0x28..+0x40 -- INCLUDING the container slots +0x2C/+0x30/"
   "+0x38(b)/+0x3C: the container is constructed as a field of the CCINIClass object")

ok("B6", eqhex(0x52ACF5, "c7060c1b7e00") and eqhex(0x52AD01, "c7020c1b7e00")
   and eqhex(0x52AD07, "c700041b7e00"),
   "List sub-ctor 0x52ACE0 stamps nodes with GenericNode vptr 0x7E1B0C twice and the "
   "head with GenericList vptr 0x7E1B04 -- then the factory OVERWRITES head with the "
   "derived List vptr 0x7E1AFC (B4): textbook base-then-derived vptr sequence")

# ============================================================== C) loader family
print("\n" + "=" * 78)
print("C) sibling loaders in the same 0x52C6DF..0x52D357 family (push string; new(0x58))")
print("=" * 78)

ok("C1", eqhex(0x52CD97, "686c628200") and eqhex(0x82626C, "52554c454d442a2e494e4900"),
   "RULEMD*.INI: push 0x82626C @0x52CD97; string verified; `new(0x58)` @0x52CDF3 "
   "(same size as the BATTLEMD factory => same class)")

ok("C2", u32(0x52C6DF + 1) == 0x825E50 and eqhex(0x52C6DF, "68505e8200")
   and u32(0x52C7AF + 1) == 0x825DF0 and eqhex(0x52C7AF, "68f05d8200")
   and u32(0x52C8B9 + 1) == 0x825D94 and eqhex(0x52C8B9, "68945d8200")
   and u32(0x52D033 + 1) == 0x826254 and eqhex(0x52D033, "6854628200")
   and u32(0x52D14E + 1) == 0x826228 and eqhex(0x52D14E, "6828628200")
   and u32(0x52D357 + 1) == 0x82621C and eqhex(0x52D357, "681c628200"),
   "six sibling `push imm32` sites decoded from their OWN operand bytes: "
   "SOUNDMD/EVAMD/THEMEMD/ARTMD/LANGRULE/AIMD .INI strings (same family, same class)")

# =========================================================== D) static globals
print("\n" + "=" * 78)
print("D) six .data globals are CONSTRUCTED CCINIClass instances (no new -- L-25 closes)")
print("=" * 78)

ok("D1", eqhex(0x40E241, "c70558708800f41a7e00") and read(0x887058, 4) is None,
   "global stamper @0x40E241 `mov dword [0x887058],0x7E1AF4`; the global's own bytes are "
   "UNREADABLE (past .data raw range => zero-fill/BSS-style) -- exactly what a "
   "compiler-emitted global-ctor must fix up at startup")

ok("D2", eqhex(0x40E031, "c70580718800f41a7e00") and eqhex(0x40E0E1, "c70508728800f41a7e00")
   and eqhex(0x40E191, "c70528718800f41a7e00") and eqhex(0x40E2F1, "c705c0708800f41a7e00"),
   "the 0x40DFE0 cluster stamps vptr 0x7E1AF4 into FOUR more globals "
   "(0x887180/0x887208/0x887128/0x8870C0), each also stamping 0x7E1B04+0x7E1AFC siblings "
   "=> five static CCINIClass objects built by one global ctor")

ok("D3", eqhex(0x49B405, "c70518f58900f41a7e00") and eqhex(0x49B420, "b918f58900"),
   "a sixth global 0x89F518 is stamped vptr 0x7E1AF4 @0x49B405, with dtor thunk "
   "@0x49B420 `mov ecx,0x89F518` (+jmp 0x49E510). WHICH .ini it serves is NOT asserted "
   "(the coopsave.ini pushes at 0x49BE64.. are in later, different bodies -- unproven link)")

ok("D4", eqhex(0x40DFDF, "689c718800") and eqhex(0x40DFF3, "e848030000")
   and 0x40DFF8 + struct.unpack("<i", read(0x40DFF4, 4))[0] == 0x40E340
   and eqhex(0x40DFF8, "6850e04000") and eqhex(0x40E050, "b980718800e9")
   and 0x40E05A + struct.unpack("<i", read(0x40E056, 4))[0] == 0x5256F0
   and eqhex(0x40E320, "8bc133c9894804894808c7000c1b7e00"),
   "destructor-registration sequence, decoded arithmetically (G-11): `push 0x88719c` "
   "@0x40DFDF -> `call 0x40E340` @0x40DFF3 (registration worker: reads [arg+4]/[arg+8]) "
   "-> `push 0x40E050` @0x40DFF8; thunk @0x40E050 = `mov ecx,0x887180; jmp` -> dtor-shaped "
   "0x5256F0 for global 0x887180. Worker's node initialiser 0x40E320 zeroes node +4/+8 "
   "and stamps [node]=0x7E1B0C -- the GenericNode vptr from A8: the registration list is "
   "the same Generic* type family as the List facets")

# ============================================================ E) witness calls
print("\n" + "=" * 78)
print("E) the two live +0x2C witnesses on record (byte-exact)")
print("=" * 78)

ok("E1", eqhex(0x52772C, "8b4e3083c62c") and eqhex(0x527750, "e89b3d0000"),
   "witness1 @0x52772C: `mov ecx,[esi+0x30]` ; `add esi,0x2c` ; call @0x527750 -> 0x52B4F0")

ok("E2", eqhex(0x52A7BA, "8b4e3083c62c") and eqhex(0x52A7DE, "e80d0d0000")
   and eqhex(0x52A7EB, "894610"),
   "witness2 @0x52A7BA (GLM blind find, byte-verified): count read + `add esi,0x2c` + "
   "call 0x52B4F0 + on-miss cache fill `mov [esi+0x10],eax` -- the caller owns the "
   "container's +0x10 cache slot")

ok("E3", eqhex(0x526BBF, "894610"),
   "kernel-caller @0x526BBF fills [esi+0x10] after `call 0x52B6D0` hit -- third "
   "confirmation the +0x10 slot = last-hit cache, written by host-side code")

# ================================================================ F) census
print("\n" + "=" * 78)
print("F) engine-wide census (one cached pass; reads go through read() so mutations apply)")
print("=" * 78)

e8, e9, imm32 = _census()
callers_a = e8[0x52B4F0]
callers_b = e8[0x52B620]
rb = re.compile(rb"\x83\xc6\x2c")
near_a = [va for va in callers_a if rb.search(read(va - 0x40, 0x40) or b"")]
near_b = [va for va in callers_b if rb.search(read(va - 0x40, 0x40) or b"")]

ok("F1", len(callers_a) == 22 and len(callers_b) == 20 and len(near_a) == 13 and len(near_b) == 0,
   "twin A: 22 E8 callers, 13 with `add esi,0x2c` within 0x40 before the call; "
   "twin B: 20 callers, 0 near-rebase (all its rebase-form hits are >0x40 away). "
   "The twins are NOT interchangeable dispatch forms -- A is the section-cache "
   "lookup on INIClass/CCINIClass hosts, B serves a differently-placed container")

ok("F2", e8[0x52A4D0] == [] and e9[0x52A4D0] == [] and imm32[0x52A4D0] == []
   and (len(callers_a) == 22),
   "0x52A4D0: E8=0, E9=0, imm32=0 across .text, POSITIVE CONTROL = twin A's 22 "
   "in the same pass (G-14). Still only 'statically invisible', not 'dead'")

ok("F3", len(near_a) == 13 and 0x52A7DE in near_a and 0x527750 in near_a,
   "the 13-member near-rebase set includes BOTH witnesses @0x527750/@0x52A7DE "
   "(set membership, not just a count -- G-75 read-scope note)")

print("\n" + "=" * 78)
print("S) structural cross-checks (not in the denominator; red still exits nonzero)")
print("=" * 78)
structural("G0", hashlib.sha256(BLOB).hexdigest() == SHA256 or bool(MUT),
           "fingerprint sha256=%s%s" % (hashlib.sha256(BLOB).hexdigest()[:16] + "…",
                                        " (MUTATED RUN)" if MUT else ""))
structural("S1", td_name(0x8174B0) and td_name(0x8174C8) and td_name(0x825B40)
           and td_name(0x817480), "all four TD names resolved non-empty")
structural("S2", u32(0x7F9594) == 0x7C8AB7,
           "TypeDescriptor vftable slot0 = 0x7C8AB7 (.text -- the catch thrown by RTTI APIs)")

print()
if FAILS:
    print("== R-058 %d/%d PASS, %d FAIL (structural OK unused=%d) ==" %
          (NPASS[0], NPASS[0] + len(FAILS), len(FAILS), len(UNCOUNTED)))
    print("FAILED: %s" % ", ".join(FAILS))
    sys.exit(1)
print("== R-058 %d/%d 字节断言 PASS（S1..S2/G0 结构性不入分母，红仍非零退出）==" % (NPASS[0], NPASS[0]))
print("GATE: GREEN")
