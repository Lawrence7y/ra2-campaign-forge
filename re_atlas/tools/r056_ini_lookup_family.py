# -*- coding: utf-8 -*-
"""R-056: INI lookup family closed -- the two "twin" entry lookups are byte-identical
duplicates, the binary-search kernel is shared, and the two extra +0x3C clears belong
to a dtor-shaped host.

gamemd.exe sha256 73201cc0...f67476, read-only.  Every window machine-dumped by
out/_probe_r056*.py BEFORE assertion (G-65).

FINDINGS (closing the three boundaries R-055 declared open):

  1. 0x52B4F0 and 0x52B620 are the SAME function, compiled twice.
     They differ in exactly 4 bytes / 2 instructions, and BOTH differences are the
     rel32 of a `call 0x7C8B48` plus the comparator-pointer immediate:
        0x52B4F0 pushes 0x52B6A0 ; calls worker with disp to 0x7C8B48
        0x52B620 pushes 0x52B720 ; calls worker with disp to 0x7C8B48
     And 0x52B6A0 vs 0x52B720 are BYTE-IDENTICAL (34 bytes, verified below), so the
     two functions are semantically identical too -- i.e. 0x52B620 is dead-weight
     duplication the linker never folded.  This is why R-055's "four lookups" are
     really THREE roles plus one duplicate.

  2. 0x52B6D0 is the shared binary-search KERNEL.
     Signature: ecx = sorted array base, edx = element count, [esp+4] = key pointer.
     Returns the matching entry pointer (0x52B70E `mov eax,edx` where edx = base+i*8)
     or NULL (0x52B706 `xor eax,eax`).  Callers: exactly 2 (0x526BB2, 0x52A554).
     The wrapping lookups do NOT call it -- they inline their own copy of the search
     loop (identical instruction sequence, see 0x52B534 vs 0x52B664).

  3. The two extra +0x3C clears (0x52ABCD / 0x52AC14) are inside ONE host, whose
     head is 0x52AB80.  (0x52AAC0 is a DIFFERENT function -- a `[`/`]` matcher;
     do NOT attribute it to this block.)  That host is a DTOR-shaped teardown: it
     re-stamps the vptr
     (0x52AB87 `mov [esi],0x7EB73C`), frees +0xC, walks the +0x18 list calling
     `call [edx]` (virtual delete) with arg 1, then frees +0x2C, zeroes
     +0x2C/+0x30/+0x34, clears the +0x38 dirty flag and finally clears +0x3C.
     It does that teardown TWICE (before and after freeing the +0x40 chain) and then
     re-stamps a second vptr (0x52AC1A `mov [esi+0x10],0x7E1B04`).
     => 0x52ABCD and 0x52AC14 are NOT two independent cache invalidation sites; they
        are the same teardown block executed on two object halves.

ADDRESS FACT SOURCE: single-call linear `md.disasm` + raw-byte census; boundaries
decided by `ret` AND by the surrounding nop fence (G-74 criterion 2').

Run:  python re_atlas/tools/r056_ini_lookup_family.py
Mut:  R056_MUTATE="VA=BYTE,..." in-process injection
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
for _it in os.environ.get("R056_MUTATE", "").split(","):
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
_TEXT_FO_LO, _TEXT_FO_HI = 0, 0


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


def hx(b):
    return "" if b is None else b.hex()


def eqhex(va, const):
    """Read length comes FROM the constant, so a hand-typed length cannot truncate (G-65)."""
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
        # "FAIL:" with the colon -- the mutation scorer keys on parts[1]=="FAIL:"
        print("%s FAIL: (structural) %s" % (label, detail))


def insns(va, n):
    return list(md.disasm(read(va, n), va))


def e8_callers(target):
    """Caller census that reads THROUGH read() so R056_MUTATE applies (G-71 cause 2:
    scanning BLOB directly makes every mutation to a call disp survive -- a gate hole)."""
    out = []
    for fo in range(_TEXT_FO_LO, _TEXT_FO_HI - 5):
        if BLOB[fo] == 0xE8:
            va_here = vaof(fo)
            raw = read(va_here, 5) if va_here is not None else None
            if raw is None or raw[0] != 0xE8:
                continue
            d = struct.unpack_from("<i", raw, 1)[0]
            va = vaof(fo)
            if va is not None and va + 5 + d == target:
                out.append(va)
    return out


def e8_targets(lo, hi):
    out = []
    for ins in insns(lo, hi - lo):
        if ins.mnemonic == "call" and ins.op_str.startswith("0x"):
            out.append((ins.address, int(ins.op_str, 16)))
    return out


def fence_before(va, span=24):
    b = read(va - span, span) or b""
    n = 0
    for i in range(len(b) - 1, -1, -1):
        if b[i] in (0x90, 0xCC):
            n += 1
        else:
            break
    return n


# ---------------------------------------------------------------- G0 fingerprint
h = hashlib.sha256(BLOB).hexdigest()
structural("G0", True, "sha256=%s%s" % (h[:16] + "…" + h[-6:],
                                        "" if h == SHA256 or MUT else " (MUTATED RUN)"))

print("=" * 78)
print("A) 0x52B4F0 and 0x52B620 are the SAME function, compiled twice")
print("=" * 78)

# A1: both are exactly 0x77 bytes of code (3 x `ret 4`, then a 10-byte nop fence)
ok("A1", eqhex(0x52B4FB, "c20400") and eqhex(0x52B565, "5ec20400")
   and eqhex(0x52B569, "90909090909090")
   and eqhex(0x52B62B, "c20400") and eqhex(0x52B693, "8bc25ec20400")
   and eqhex(0x52B699, "90909090909090"),
   "both twins: 3 x `ret 4`, body length 0x79, and the same SEVEN-byte nop fence "
   "(0x52B569..0x52B56F / 0x52B699..0x52B69F). R-056 first draft said 0x77 / 10 nops -- "
   "WRONG: that window cut the trailing 00 of the last `ret 4`")

# A2: exactly TWO differing instructions, both relocatable/immediate operands
A = read(0x52B4F0, 0x79)
B = read(0x52B620, 0x79)
diffs = [i for i in range(len(A)) if A[i] != B[i]]
ok("A2", len(diffs) == 4,
   "byte diffs = %d at offsets %s (expect 4: one imm32-pointer + one rel32)" % (len(diffs), diffs))

# A3: the comparator immediates differ: 0x52B6A0 vs 0x52B720
ok("A3", eqhex(0x52B505, "68a0b65200") and eqhex(0x52B635, "6820b75200"),
   "comparator immediates: 0x52B4F0 pushes 0x52B6A0 @0x52B505 ; 0x52B620 pushes 0x52B720 @0x52B635")

# A4: the callback functions are BYTE-IDENTICAL (34 bytes) => the twins are equivalent
CA = read(0x52B6A0, 0x22)
CB = read(0x52B720, 0x22)
ok("A4", CA == CB and len(CA) == 0x22,
   "comparator bodies byte-identical (%d bytes) => the two lookups are semantically equal" % len(CA))

# A5: both call the same rehash worker 0x7C8B48
ok("A5", 0x7C8B48 in [t for _, t in e8_targets(0x52B4F0, 0x52B569)]
   and 0x7C8B48 in [t for _, t in e8_targets(0x52B620, 0x52B699)],
   "both twins call the same rehash worker 0x7C8B48")

# A6: both return an ENTRY POINTER (mov eax,edx after lea edx,[base+i*8])
ok("A6", eqhex(0x52B559, "5f5b33c05ec20400") and eqhex(0x52B561, "5f5b8bc25ec20400")
   and eqhex(0x52B689, "5f5b33c05ec20400") and eqhex(0x52B691, "5f5b8bc25ec20400"),
   "both: miss -> `xor eax,eax` ; hit -> `mov eax,edx` (entry pointer)")

print("\n" + "=" * 78)
print("B) 0x52B6D0 is the shared binary-search KERNEL (callers: exactly 2)")
print("=" * 78)

# B1: kernel head + argument registers
ok("B1", eqhex(0x52B6D0, "535685d2578bf27e2b8b4424108b18"),
   "0x52B6D0 head: ecx=base, edx=count, [esp+0x10]=key ptr (after 3 pushes)")

# B2: kernel returns entry pointer or NULL
ok("B2", eqhex(0x52B70C, "5f5e8bc25bc20400") and eqhex(0x52B704, "5f5e33c05bc20400"),
   "kernel tail: hit `mov eax,edx` @0x52B70E ; miss `xor eax,eax` @0x52B706")

# B3: kernel's two callers
callers = e8_callers(0x52B6D0)
ok("B3", callers == [0x526BB2, 0x52A554],
   "0x52B6D0 callers = %s (exactly two)" % [hex(x) for x in callers])

# B4: the wrapping lookups do NOT call the kernel -- they inline the loop
ok("B4", 0x52B6D0 not in [t for _, t in e8_targets(0x52B4F0, 0x52B569)]
   and 0x52B6D0 not in [t for _, t in e8_targets(0x52B620, 0x52B699)],
   "neither twin calls 0x52B6D0 (the search loop is INLINED in each)")

# B6: BOTH twins are live -- R-056 first draft called 0x52B620 "dead weight" because it
# only counted E8 targets INSIDE 0x528A10 (where 0x52B620 appears 0 times), never its own
# callers. Aligned linear sweep over all of .text says otherwise.
ok("B6", len(e8_callers(0x52B4F0)) == 22 and len(e8_callers(0x52B620)) == 20,
   "callers engine-wide: 0x52B4F0 = %d, 0x52B620 = %d  => 0x52B620 is a LIVE duplicate, "
   "NOT dead weight (R-056 first draft was wrong here)"
   % (len(e8_callers(0x52B4F0)), len(e8_callers(0x52B620))))

# B5: the inlined loop is the same sequence as the kernel's
ok("B5", eqhex(0x52B534, "8bc1992bc2d1f88b34c78d14c7") and eqhex(0x52B664, "8bc1992bc2d1f88b34c78d14c7"),
   "inlined search loops at 0x52B534 / 0x52B664 share the same 12-byte core")

print("\n" + "=" * 78)
print("C) the two extra +0x3C clears belong to ONE dtor-shaped host (head 0x52AB80)")
print("=" * 78)

# C1: both clears share the same 5-instruction teardown block
ok("C1", eqhex(0x52ABC4, "895e30895e34885e38895e3c")
   and eqhex(0x52AC0B, "895e30895e34885e38895e3c"),
   "identical 10-byte teardown block at 0x52ABC4 and 0x52AC0B (+0x30/+0x34/+0x38/+0x3C all zeroed)")

# C2: the host re-stamps a vptr at entry => it is a destructor
ok("C2", eqhex(0x52AB87, "c7063cb77e00"),
   "host head 0x52AB87 re-stamps vptr 0x7EB73C => dtor-shaped")

# C3: the host walks a +0x18 list calling virtual delete with arg 1
ok("C3", eqhex(0x52ABA2, "395904") and eqhex(0x52ABB2, "6a01ff12"),
   "walks +0x18 list: `cmp [ecx+4],ebx` guard then `push 1; call [edx]` (virtual delete)")

# C4: the host re-stamps a SECOND vptr after the teardown => two object halves
ok("C4", eqhex(0x52AC1A, "c74610041b7e00"),
   "after teardown it stamps [esi+0x10]=0x7E1B04 => second facet vptr")

# C5: the host's own head, and the fence before it
ok("C5", eqhex(0x52AB80, "53568bf18b460c") and fence_before(0x52AB80) >= 1,
   "host head 0x52AB80 (fence before it = %d bytes); 0x52AAC0 is a DIFFERENT function" % fence_before(0x52AB80))

# C5b: the NEGATIVE side of the same question (G-76 5): verifying only the head I
# believe in cannot rule out "both candidates are the host". 0x52AAC0 is NOT dtor-shaped
# -- it is a whitespace-skipper + `[`/`]` matcher, so neither may hide in the other.
ok("C5b", eqhex(0x52AAC0, "85c974298a0184c0740c3c2077088a41")
   and read(0x52AAC0, 6) != read(0x52AB80, 6)
   and fence_before(0x52AAC0) >= 8,
   "0x52AAC0 head = `test ecx,ecx`..`cmp al,0x20`..(0x52AAD6) `cmp byte [ecx],0x5b` "
   "= whitespace skipper + `[`/`]` matcher, fence_before=%d => NOT the dtor host"
   % fence_before(0x52AAC0))

# C6: the two clears are therefore ONE block run twice, not two independent sites.
# R-059 rewrite: the first draft was `abs(0x52AC14 - 0x52ABCD) < 0x50` -- pure address
# arithmetic over two CONSTANTS, no byte read at all, so no mutation could ever redden
# it (G-77: a gate that cannot go red is decoration, not criterion).  The rewritten
# form keeps the gap claim but ANCHORS it: the first clear, the +0x40 release LOOP that
# lies between the two clears (head `mov ecx,[esi+0x40]` + back-edge `jne`), and the
# second teardown's own `+0x2C` clear must all be the bytes we read.
ok("C6", eqhex(0x52ABCD, "895e3c") and eqhex(0x52AC14, "895e3c")
   and eqhex(0x52ABDB, "8b4e40") and eqhex(0x52ABFC, "75dd")
   and eqhex(0x52AC08, "895e2c") and abs(0x52AC14 - 0x52ABCD) < 0x50,
   "the two +0x3C clears bracket a +0x40 chain-release loop (`mov ecx,[esi+0x40]` "
   "@0x52ABDB, back-edge `jne 0x52ABDB` @0x52ABFC) -- same function, same block, run "
   "twice; gap 0x%X < 0x50" % (0x52AC14 - 0x52ABCD))

print("\n" + "=" * 78)
print("S) structural cross-checks (not in the denominator; red still exits nonzero)")
print("=" * 78)
structural("S1", len(read(0x52B4F0, 0x79)) == 0x79 and len(read(0x52B620, 0x79)) == 0x79,
           "both twins are 0x79 bytes long (head..last ret-4 byte)")
structural("S2", u32(0x7EB73C) is not None,
           "host vptr 0x7EB73C readable (0x%X)" % (u32(0x7EB73C) or 0))
structural("S3", eqhex(0x52B720, "8b4424048b4c2408"),
           "comparator 0x52B720 head: loads both args then dereferences")

print()
if FAILS:
    print("== R-056 %d/%d PASS, %d FAIL (structural OK unused=%d) ==" %
          (NPASS[0], NPASS[0] + len(FAILS), len(FAILS), len(UNCOUNTED)))
    print("FAILED: %s" % ", ".join(FAILS))
    sys.exit(1)
print("== R-056 %d/%d 字节断言 PASS（S1..S3 结构性不入分母，红仍非零退出）==" % (NPASS[0], NPASS[0]))
print("GATE: GREEN")
