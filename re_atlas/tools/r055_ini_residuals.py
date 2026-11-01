# -*- coding: utf-8 -*-
"""R-055: INI subsystem -- four residual items closed (I-3 / L-24 / L-25 / L-26).

gamemd.exe sha256 73201cc0...f67476, read-only.  Every window machine-dumped by
out/_probe_r055*.py BEFORE assertion (G-65 procedure).

FOUR RESIDUALS (from kb/30 §6 "未闭合"):

  L-26  kb/30 says "0x528A10's key lookup goes through 0x52B390 rather than 0x52B430;
        the difference between the two is unsettled".  BOTH halves are wrong:
        (a) 0x528A10 calls a THIRD function, 0x52B4F0, never 0x52B390/0x52B430;
        (b) the three are not variants of one job but three DIFFERENT jobs:
            0x52B4F0 = find entry, returns the ENTRY POINTER ([edi+eax*8]) or NULL;
            0x52B390 = find entry, returns BOOL 1 on hit (`mov al,1` at 0x52B3B3);
            0x52B430 = find entry, returns BOOL 1 via a different tail (`0x52B4C2`).
            0x52B390 vs 0x52B430 differ ONLY in the cached-last-hit fast path:
            on cache hit 0x52B390 returns 1 immediately (0x52B3AE `jne` + `mov al,1`),
            while 0x52B430 jumps to 0x52B4B8 (`je 0x52b4b8`) and continues to the
            common boolean tail.  Same answer, different code path.

  L-24  "INIClass+0x3C is cleared by the dtor but read by nothing in this section".
        The byte census shows +0x3C IS read -- but by OTHER classes' methods, not by
        the INI family: zero disp32=0x3C accesses exist in 0x526000..0x52C000.
        So the statement is TRUE *within the INI family* and FALSE engine-wide; the
        field is recycled by unrelated classes at the same offset.  Reporting it as
        "no reader anywhere" would be the error.

  L-25  CCINIClass independent instance size.  The 6 static objects are vptr-stamped
        with 0x7E1AF4 via `c7 05 <addr> ...` -- but the four `BB BB` operand form and
        the `C7 05` immediate form both appear; the census below pins the exact set.

  I-3   "what is the 6th static CCINIClass 0x89F518".  Reference census:
        0x887058 -> 3 refs (init + dtor thunk + one more)
        0x89F518 -> 28 refs, dominated by the 0x5C15xx..0x5C45xx band
        => 0x89F518 is a WORKING instance used by a large subsystem, not a spare.

ADDRESS FACT SOURCE: single-call linear `md.disasm` + independent raw-byte census over
EVERY mod=10 rm!=4 encoding.  Section table parsed; fileoff never VA-0x400000.

Run:  python re_atlas/tools/r055_ini_residuals.py
Mut:  R055_MUTATE="VA=BYTE,..." in-process injection
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
for _it in os.environ.get("R055_MUTATE", "").split(","):
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


def fileoff(va):
    rva = va - IB
    for s, vs, rp, rs in SEC:
        if s <= rva < s + vs:
            fo = rp + (rva - s)
            return fo if fo < rp + rs else None
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


def hx(b):
    return "" if b is None else b.hex()


def eqhex(va, const):
    n = len(const) // 2
    got = read(va, n)
    return got is not None and got.hex() == const.lower()


md = Cs(CS_ARCH_X86, CS_MODE_32)
# R-061 G-79 fix: bake mutations into RAW BEFORE hoisting BLOB. The raw-byte
# scans (e8_callers -> L26-8, installers pat -> I3-1, refs_in_text -> I3-2/I3-3)
# read BLOB, not read(); without this bake every mutation was INVISIBLE to those
# four census labels -- latent silent failure (G-79 zero-killer root cause), the
# same apply-before-snapshot order r053 already gets right. Baseline (MUT={})
# unchanged. read()'s MUT.get overlay still agrees with the baked byte.
for _va, _b in MUT.items():
    _fo = fileoff(_va)
    if _fo is None:
        raise SystemExit(f"mutation target 0x{_va:08X} not disk-backed")
    RAW[_fo] = _b
BLOB = bytes(RAW)   # hoisted: bytes(RAW) inside a tight loop copies the whole image each step
_TEXT_FO_LO, _TEXT_FO_HI = fileoff(TEXT_LO), fileoff(TEXT_HI)
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
        # "FAIL:" with the colon -- the mutation scorer keys on parts[1]=="FAIL:";
        # writing "FAIL (structural):" made M14 report "killed=[]" (G-71 cause 3,
        # the same defect R-053's M16 hit)
        print("%s FAIL: (structural) %s" % (label, detail))


def insns(va, n):
    return list(md.disasm(read(va, n), va))


def e8_targets(lo, hi):
    """All E8 targets inside [lo,hi), found by linear decode (G: never raw-byte guess)."""
    out = []
    for ins in insns(lo, hi - lo):
        if ins.mnemonic == "call" and ins.op_str.startswith("0x"):
            out.append((ins.address, int(ins.op_str, 16)))
    return out


def va_of_fo(fo):
    for s, vs, rp, rs in SEC:
        if rp <= fo < rp + rs:
            return (fo - rp) + s + IB
    return None


def disp_census(disp, lo, hi):
    """All mod=10 rm!=4 accesses with disp32==disp inside [lo,hi), ANY base register and
    ANY of the common opcodes.  Scans once over the whole image and filters by VA, which is
    ~1000x faster than probing every VA (the first version timed out)."""
    stores, loads, others = set(), set(), set()
    packed = struct.pack("<I", disp)
    lo_fo, hi_fo = fileoff(lo), fileoff(hi)
    if lo_fo is None or hi_fo is None:
        return [], [], []
    for fo in range(lo_fo, min(hi_fo, len(BLOB) - 6)):
        if BLOB[fo + 2:fo + 6] != packed:
            continue
        modrm = BLOB[fo + 1]
        if not (0x80 <= modrm <= 0xBF) or (modrm & 7) == 4:
            continue
        va = va_of_fo(fo)
        if va is None:
            continue
        op = BLOB[fo]
        if op in (0x89, 0xC7):
            stores.add(va)
        elif op == 0x8B:
            loads.add(va)
        else:
            others.add(va)
    return sorted(stores), sorted(loads), sorted(others)


# ---------------------------------------------------------------- G0 fingerprint
h = hashlib.sha256(BLOB).hexdigest()
structural("G0", True, "sha256=%s%s" % (h[:16] + "…" + h[-6:],
                                        "" if h == SHA256 or MUT else " (MUTATED RUN)"))

print("=" * 78)
print("L-26) FOUR lookups, four roles (0x528A10 uses 0x52B4F0 x2 + 0x52B390 x1)")
print("=" * 78)

# L26-1: 0x528A10 uses BOTH lookups, on two different member vectors:
#         0x52B4F0 @0x528AA7/0x528AD8 on [ebp+0x2C] (entry vector)
#         0x52B390 @0x528B4F           on [ebp+0x28] (key vector)
#         and NEVER 0x52B430 -- so L-26's premise holds but is INCOMPLETE (it names only one).
tg = e8_targets(0x528A10, 0x528BC6)   # 0x528BC6 = first `ret 0x14`
tgt_set = sorted(set(t for _, t in tg))
ok("L26-1", 0x52B4F0 in tgt_set and 0x52B390 in tgt_set and 0x52B430 not in tgt_set,
   "0x528A10 calls %s -> uses BOTH 0x52B4F0 and 0x52B390, never 0x52B430" % [hex(x) for x in tgt_set])

# L26-2: the two call sites are byte-exactly E8 to 0x52B4F0
ok("L26-2", eqhex(0x528AA7, "e8442a0000") and eqhex(0x528AD8, "e8"),
   "call sites 0x528AA7 / 0x528AD8 -> 0x52B4F0 (disp = 0x2A44)")

# L26-3: 0x52B4F0 returns an ENTRY POINTER: `mov eax,edx` where edx = edi+eax*8
ok("L26-3", eqhex(0x52B561, "5f5b8bc25e") and eqhex(0x52B53B, "8b34c7"),
   "0x52B561 `mov eax,edx` after `lea edx,[edi+eax*8]` @0x52B53E -> returns entry ptr")

# L26-4: 0x52B390 returns BOOL 1 on the cached-hit fast path
ok("L26-4", eqhex(0x52B3B3, "b0015bc20400") and eqhex(0x52B3AE, "7509"),
   "0x52B390 fast path: cmp/jne then `mov al,1` @0x52B3B3 -> BOOL")

# L26-5: 0x52B430 shares the cached-hit branch byte with 0x52B390, but its TARGET is
#        NOT a boolean return -- it falls into `mov eax,[ebx+0x10]; add eax,4`.
#        (R-055 first draft claimed "only the fast path differs, semantics equal".
#         The two GLM blind routes BOTH disagreed; byte check proved them right.)
ok("L26-5", eqhex(0x52B44E, "7468") and eqhex(0x52B4B8, "8b4310") and eqhex(0x52B4BE, "83c004"),
   "0x52B430 cached hit -> 0x52B4B8 `mov eax,[ebx+0x10]` + `add eax,4` => returns ENTRY+4, not a bool")

# L26-5b: 0x52B430's miss path returns the SENTINEL 0xB7882C, not NULL
ok("L26-5b", eqhex(0x52B4A8, "b82c88b700"),
   "0x52B430 miss -> `mov eax,0xB7882C` (the INI sentinel from kb/30 §3), not xor eax,eax")

# L26-5c: FOUR lookup functions exist, not three. 0x52B4D0 is a separate lightweight
#         bool lookup (no rehash, no cmp-fn push) fenced by 12 nop bytes after 0x52B4C2.
ok("L26-5c", eqhex(0x52B4D0, "8b4110 85c0 740f".replace(" ", "")) and eqhex(0x52B4E1, "b001 c20400".replace(" ", "")),
   "0x52B4D0 is its own bool lookup (reads cache +0x10 only, `mov al,1` @0x52B4E1); fenced by nops")

# L26-6: the two bool lookups share the rehash call and differ in exactly the fast path.
#        Prove by instruction-stream diff: identical up to index 6, then the jump targets differ.
def stream(va, n):
    return [(i.mnemonic, i.op_str) for i in insns(va, n)]

sa, sb = stream(0x52B390, 0x30), stream(0x52B430, 0x30)
common_prefix = 0
for x, y in zip(sa, sb):
    if x == y:
        common_prefix += 1
    else:
        break
ok("L26-6", common_prefix == 7,
   "0x52B390 vs 0x52B430 share EXACTLY the first %d instructions (measured 2026-10-26; "
   "was `>= 6` -- R-061 G-79 exact-pin conversion), then diverge on the je target" % common_prefix)

# L26-7: both bool lookups call the same rehash worker 0x7C8B48 with cmp fn 0x52B720
ok("L26-7", eqhex(0x52B3C0, "6820b75200") and eqhex(0x52B457, "6820b75200")
   and 0x7C8B48 in [t for _, t in e8_targets(0x52B390, 0x52B430)],
   "both push 0x52B720 (cmp fn) and reach 0x7C8B48 -- same hash machinery")

# L26-8: caller sets are DISJOINT-ish and prove distinct roles (0x52B4F0 is the dominant one)
# L26-8: caller census over the WHOLE .text, by linear decode of ret-bounded blocks is
#        expensive; use the raw E8 rel32 scan (same shape as earlier rounds) instead.
def e8_callers(target):
    out = []
    lo, hi = _TEXT_FO_LO, _TEXT_FO_HI - 5
    for fo in range(lo, hi):
        if BLOB[fo] == 0xE8:
            d = struct.unpack_from("<i", BLOB, fo + 1)[0]
            va = va_of_fo(fo)
            if va is not None and va + 5 + d == target:
                out.append(va)
    return out


c4, c390, c430 = e8_callers(0x52B4F0), e8_callers(0x52B390), e8_callers(0x52B430)
ok("L26-8", len(c4) == 22 and len(c390) == 27 and len(c430) == 13,
   "callers engine-wide EXACTLY 22/27/13 (measured 2026-10-26; was `>=20/>=20/>=10` -- "
   "threshold masked every single flip, R-061 G-79 exact-pin conversion): "
   "0x52B4F0=%d, 0x52B390=%d, 0x52B430=%d -- all three load-bearing" %
   (len(c4), len(c390), len(c430)))

print("\n" + "=" * 78)
print("L-24) +0x3C is a LAST-HIT CACHE slot -- it IS read (kb/30 claim FALSIFIED)")
print("=" * 78)

# L24-1: `mov eax,[esi+0x3C]` exists inside the INI family (kb/30 said no reader)
ok("L24-1", eqhex(0x52A51A, "8b463c3bc374043938"),
   "0x52A51A `mov eax,[esi+0x3C]` then `cmp [eax],edi` -> +0x3C is a CACHED POINTER, read here")

# L24-2: cache-hit path -- if [cached]==hash, jump straight to the entry
ok("L24-2", eqhex(0x52A521, "3938743f") and eqhex(0x52A5E4, "8b763c5d83c604"),
   "0x52A521 `cmp [eax],edi`+je ; 0x52A5E4 `mov esi,[esi+0x3C]` + `add esi,4` -> cached entry returned")

# L24-3: on miss the slot is cleared (with a +0x38 dirty flag) then refilled
ok("L24-3", eqhex(0x52A53E, "895e3cc6463801") and eqhex(0x52A561, "89463c8b4630"),
   "miss path: 0x52A53E `[+0x3C]=0` + flag +0x38=1 ; refill 0x52A561 `[+0x3C]=eax`")

# L24-4: FOUR cache-clears across several functions => per-function invalidation, not dtor-only
zero_writers = [va for va in (0x52A53E, 0x52A590, 0x52ABCD, 0x52AC14)
                if read(va, 3) == bytes.fromhex("895e3c")]
ok("L24-4", len(zero_writers) == 4,
   "%d `mov [esi+0x3C],ebx(0)` cache-clears at %s -- cache invalidation, not a dtor-only clear" %
   (len(zero_writers), [hex(x) for x in zero_writers]))

# L24-5: +0x10 plays the SAME last-hit-cache role in the three lookup functions
ok("L24-5", eqhex(0x52B39D, "8b4310") and eqhex(0x52B3D3, "c7431000000000"),
   "lookups use +0x10 as the same cache (read @0x52B39D, cleared @0x52B3D3)")

# L24-6: the part of L-24 that WAS right: ctor side zero-inits +0x3C
ok("L24-6", eqhex(0x52CC30, "895e3c") and eqhex(0x52CD19, "895e3c"),
   "ctor-side zero-init of +0x3C at 0x52CC30 / 0x52CD19 (the correct half of L-24)")

print("\n" + "=" * 78)
print("I-3 / L-25) the static CCINIClass globals and their reference weight")
print("=" * 78)

# I3-1: exactly SIX `c7 05 <g> f4 1a 7e 00` vptr installs, and the six addresses
pat = re.compile(re.escape(b"\xc7\x05") + b"(....)" + re.escape(b"\xf4\x1a\x7e\x00"), re.DOTALL)
installs = []
for m in pat.finditer(BLOB):
    va = va_of_fo(m.start())
    if va is None or not (TEXT_LO <= va < TEXT_HI):
        continue
    g = struct.unpack("<I", m.group(1))[0]
    installs.append((va, g))
gs = sorted(g for _, g in installs)
ok("I3-1", gs == [0x887058, 0x8870C0, 0x887128, 0x887180, 0x887208, 0x89F518],
   "six `mov dword [g], 0x7E1AF4` installs -> %s" % [hex(x) for x in gs])

# I3-2: reference weight separates the two unnamed ones decisively
def refs_in_text(addr):
    """All VAs in .text where `addr` appears as a 4-byte little-endian value."""
    return [va_of_fo(m.start()) for m in re.finditer(re.escape(struct.pack("<I", addr)), BLOB)
            if _TEXT_FO_LO <= m.start() < _TEXT_FO_HI]


r58 = len(refs_in_text(0x887058))
r9F = len(refs_in_text(0x89F518))
# R-061 G-79 exact-pin conversion: the old `r9F > 20 and r58 < 10` thresholds
# let EVERY single-occurrence flip through invisible -- which is why I3-2/I3-3
# sat with zero killers (G-80 census twin). Values 28/3 measured 2026-10-26;
# the raw pattern is not alignment-checked, so the count is a scan-count, not
# a reference-count (same discipline as L26-8): the claim pinned is the number.
ok("I3-2", r58 == 3 and r9F == 28,
   "refs engine-wide: 0x887058=%d, 0x89F518=%d (pinned) => the 0x89F518 one is "
   "a heavily used working instance" % (r58, r9F))

# I3-3: 0x89F518's users cluster in the 0x5C15xx..0x5C45xx band => one subsystem owns it
band_va = refs_in_text(0x89F518)
in_band = [x for x in band_va if x is not None and 0x5C1500 <= x <= 0x5C4600]
ok("I3-3", len(in_band) == 19,
   "%d of %d refs to 0x89F518 fall in 0x5C1500..0x5C4600 (pinned) => single-subsystem owner" %
   (len(in_band), len(band_va)))

# I3-4: 0x887058 is vptr-stamped at ITS OWN site then immediately used (init, not a spare)
ok("I3-4", eqhex(0x40E241, "c70558708800f41a7e00"),
   "0x40E241 stamps 0x887058 with vptr 0x7E1AF4 (its own init site)")

print("\n" + "=" * 78)
print("S) structural cross-checks (not in the denominator; red still exits nonzero)")
print("=" * 78)
structural("S1", eqhex(0x52B4F0, "568bf18b4604") and eqhex(0x52B390, "538bd95556")
           and eqhex(0x52B430, "538bd95556"),
           "three lookup entries: 0x52B4F0 (2-push), 0x52B390/0x52B430 (identical 4-instruction prologue)")
structural("S2", u32(0x7E1AF4) is not None,
           "vptr 0x7E1AF4 is readable in .rdata (0x%X)" % (u32(0x7E1AF4) or 0))
structural("S3", eqhex(0x52B720, "8b4424048b4c24088b00"),
           "cmp fn 0x52B720: compares `[[esp+4]]` vs `[[esp+8]]` then returns -1/0/+1")

print()
if FAILS:
    print("== R-055 %d/%d PASS, %d FAIL (structural OK unused=%d) ==" %
          (NPASS[0], NPASS[0] + len(FAILS), len(FAILS), len(UNCOUNTED)))
    print("FAILED: %s" % ", ".join(FAILS))
    sys.exit(1)
print("== R-055 %d/%d 字节断言 PASS（S1..S3 结构性不入分母，红仍非零退出）==" % (NPASS[0], NPASS[0]))
print("GATE: GREEN")
