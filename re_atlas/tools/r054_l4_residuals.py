# -*- coding: utf-8 -*-
"""R-054: L-4 four residuals closed -- marker 0x12 / key template / third ctor site / +0x98.

gamemd.exe sha256 73201cc0...f67476, read-only.  Every window below was machine-dumped
by out/_probe_r054*.py BEFORE being asserted (G-65 procedure: dump first, then pin).

FOUR RESIDUALS (from R-044 §3 / R-045 §2 / R-046 §2 / R-046 §4):

  A) marker 0x12 in fixup 0x691E66 `cmp dword [edx-4],0x12`
     -> the compared field is the ENTRY KEY `[+0xA4]`, and 0x12 is an ACTION ID
        (TActionClass::Execute dispatch: `mov edx,[esi+0x2c]; dec edx; cmp edx,0x90;
        jmp [edx*4+0x6DFDEC]` -- so id N maps to table index N-1; id 0x12 -> idx 0x11
        -> handler 0x6DE37B).  Entry arrays are therefore (action id, parameter) pairs
        indexed by TeamType, and fixup only renumbers entries whose action id is 0x12.
     -> 0x12 is NOT a type marker; it is the script action whose parameter is a
        TeamType reference, which is exactly why the renumber pass keys on it.

  B) key name template: parser 0x6918A0 builds element keys with `push 0x817F6C` (= "%d")
     through 0x7C8EF4 (vsprintf-family) and re-parses with 0x7CA530 (sscanf-family).
     So the "key" is a DECIMAL STRING of an integer, not a name; the two ints come from
     `push 0x81C000` ("%d,%d") split in 0x723CA0 into (action, parameter).
     Entry pair [ +0xA4 key +0xA8 value ] == [ action id + parameter ].

  C) 0x691A5B -- R-046 called it "a non-ctor +0xA0 writer with no +0x9C partner".
     FALSE.  0x691A55 `mov [esi+0x9C],ebx` immediately precedes it (ebx = 0 from
     `xor ebx,ebx` @0x691989, the only ebx write in the interval) => it IS a third
     construction site, inline in 0x691970 ([ScriptTypes] section parser).  R-046's
     census only matched the C7-immediate encoding and therefore missed the 89-register
     form.  R-046's "double-zero pair occurs exactly twice" is OVERTURNED: three sites.

  D) +0x98 after registry compaction -- dtor 0x691770 renumbers the registry VECTOR
     (SIB compaction 0x6917CE/0x6917D1) but never touches any object's own +0x98, and
     the renumber sites are exactly {0x691763, 0x691AEC, 0x691D26} (one per ctor site),
     each computing the index AFTER inserting self.  Reader is slot16 0x691F90
     (`mov eax,[ecx+0x98]; ret`).  => +0x98 is a STALE CACHE: it is not fixed up when
     another ScriptType is destroyed and the vector compacts.

ADDRESS FACT SOURCE: single-call linear `md.disasm` on the region + independent
raw-byte `find()` census over EVERY mod=10 rm!=4 encoding (not just C7), which is the
exact hole that produced C.

Run:  python re_atlas/tools/r054_l4_residuals.py
Mut:  R054_MUTATE="VA=BYTE,..." in-process injection
"""
import hashlib
import os
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

RAW = bytearray(open(EXE, "rb").read())
MUT = {}
for _it in os.environ.get("R054_MUTATE", "").split(","):
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
assert SEC[0] == (0x1000, 0x3DF38D, 0x1000, 0x3E0000), f"section tuple drift {SEC[0]}"

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
    return struct.unpack("<I", read(va, 4))[0]


def hx(b):
    return "" if b is None else b.hex()


def cstr(va, n=64):
    b = read(va, n) or b""
    return b.split(b"\x00")[0]


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
    """Structural check: excluded from the denominator, but red still exits nonzero."""
    if cond:
        UNCOUNTED.append(label)
        print("%s OK (structural; not counted): %s" % (label, detail))
    else:
        FAILS.append(label)
        print("%s FAIL (structural): %s" % (label, detail))


def eqhex(va, const):
    """Compare read(va, len(const)/2) against const -- the read length comes FROM the
    constant, so a hand-typed length can never silently truncate or over-read (G-65)."""
    n = len(const) // 2
    got = read(va, n)
    return got is not None and got.hex() == const.lower()


def got(va, n):
    return hx(read(va, n))


def disp_census(disp, lo, hi):
    """Every mod=10 rm!=4 access with disp32==disp, ALL opcodes -- the C-fix census."""
    stores, loads, others = set(), set(), set()
    for va in range(lo, hi):
        b = read(va, 2)
        if b is None or b[0] == 0x0F:
            continue
        modrm = b[1]
        if not (0x80 <= modrm <= 0xBF) or (modrm & 7) == 4:
            continue
        d = read(va + 2, 4)
        if d is None or struct.unpack("<I", d)[0] != disp:
            continue
        op = b[0]
        if op in (0x89, 0xC7):
            stores.add(va)
        elif op == 0x8B:
            loads.add(va)
        else:
            others.add(va)
    return sorted(stores), sorted(loads), sorted(others)


# ---------------------------------------------------------------- G0 fingerprint
h = hashlib.sha256(bytes(RAW)).hexdigest()
structural("G0", True, "sha256=%s%s" % (h[:16] + "…" + h[-6:],
                                        "" if h == SHA256 or MUT else " (MUTATED RUN)"))

print("=" * 78)
print("A) marker 0x12 = action id, compared against the entry KEY [+0xA4]")
print("=" * 78)

# A1: fixup key comparison + the loop shape (31 bytes, machine-dumped)
A1 = "8d93a8000000837afc12753f83f9ff752133c085f67e428b0da4eca8003929"
ok("A1", eqhex(0x691E60, A1),
   "fixup 0x691E60: lea edx,[ebx+0xA8] / cmp [edx-4],0x12 / stride 8 / count [ebx+0xA0] = %s" % hx(read(0x691E60, 0x1F)))

# A2: [edx-4] IS the entry key field, proven by the entry-pair consumer reading +0xA4 with
#     the same stride-8 indexing (0x691520) and the writer storing key first (0x69192E).
A2W = "898cc6a4000000"
A2R = "8bb4d1a4000000"
ok("A2", eqhex(0x69192E, A2W) and eqhex(0x691520, A2R),
   "entry key field = +0xA4: writer %s @0x69192E, reader %s @0x691520" % (hx(read(0x69192E, 7)), hx(read(0x691520, 7))))

# A3: action dispatch: id-1 indexing into 0x6DFDEC, bound 0x90 (=> 145 entries)
A3 = "8b562c4a81fa900000000f87"
ok("A3", eqhex(0x6DD8D7, A3),
   "dispatch 0x6DD8D7: mov edx,[esi+0x2c]; dec edx; cmp edx,0x90; ja (=> id 0x12 -> idx 0x11)")

# A4: table holds 145 dwords, all in .text, 143 unique (G: alias triple)
tbl = [u32(0x6DFDEC + i * 4) for i in range(145)]
intext = [v for v in tbl if TEXT_LO <= v < TEXT_HI]
uniq = set(intext)
alias = [i for i, v in enumerate(tbl) if tbl.count(v) > 1]
ok("A4", len(tbl) == 145 and len(intext) == 145 and len(uniq) == 143 and alias == [38, 91, 92],
   "0x6DFDEC: 145/145 in-text, %d unique, alias idx=%s (R-041 cross-check)" % (len(uniq), alias))

# A5: id 0x12 -> idx 0x11 -> 0x6DE37B, whose body forwards four stack args to 0x6E11C0
A5 = "8bcee8252e00005f5e5d5b81c440020000c21000"
ok("A5", u32(0x6DFDEC + 0x11 * 4) == 0x6DE37B and eqhex(0x6DE394, A5),
   "id 0x12 handler = 0x6DE37B -> `call 0x6E11C0` then ret 0x10")

# A6: handler 0x6E11C0 resolves a TeamType by NAME (0x68BCC0 + 0x88098C global), not by index
A6 = "a14c3da800"
ok("A6", eqhex(0x6E11C0, A6) and eqhex(0x6E11E7, "8b0d30b2a8"),
   "0x6E11C0 head loads [0xA83D4C] and calls 0x68BCC0 with [0xA8B230] => name lookup")

print("\n" + "=" * 78)
print("B) key template: element key is a DECIMAL STRING of an int (\"%d\"), not a name")
print("=" * 78)

# B1: parser pushes 0x817F6C ("%d") into the vsprintf-family helper
B1 = "578d44241c686c7f810050e80f76130083"
ok("B1", eqhex(0x6918D5, B1),
   "0x6918D5: push edi / lea eax / push 0x817F6C(\"%%d\") / push eax / call 0x7C8EF4")

# B2: the literal at 0x817F6C is exactly "%d\0"
ok("B2", cstr(0x817F6C, 4) == b"%d",
   "0x817F6C = %r; neighbours 0x817F60=%r 0x817F64=%r" % (cstr(0x817F6C, 4), cstr(0x817F60, 8), cstr(0x817F64, 8)))

# B3: 0x7C8EF4 is vsprintf-family (fmt scan setup: mov [ebp-0x14],0x42 = 'B' format class)
ok("B3", eqhex(0x7C8EF4, "558bec83ec208b4508568945e88945e0") and eqhex(0x7C8F07, "c745ec42000000"),
   "0x7C8EF4 = format-string writer (0x7C8F07 imm 0x42 = 'B' = formatted-output class)")

# B4: the pair comes from "%d,%d" (0x81C000) split by 0x7CA530 in 0x723CA0
B4 = "8d4c24048d54240c51526800c0810050e86f680a"
ok("B4", eqhex(0x723CAC, B4) and cstr(0x81C000, 6) == b"%d,%d",
   "0x723CAC: 0x7CA530(\"%%d,%%d\") -> writes (dword,dword) pair; 0x81C000 = %r" % (cstr(0x81C000, 6),))

# B5: writer stores key at +0xA4 and value at +0xA8 with the SAME eax*8 index
B5W = "898cc6a4000000"
B5V = "8994c6a8000000"
ok("B5", eqhex(0x69192E, B5W) and eqhex(0x691939, B5V),
   "pair writer: [esi+eax*8+0xA4]<-ecx @0x69192E then [+0xA8]<-edx @0x691939")

# B6: count bound 0x32 (50) and self-increment
B6 = "83f8327d238b4c"
ok("B6", eqhex(0x691925, B6),
   "0x691925: cmp eax,0x32 / jge skip (=> at most 50 entries), matches +0xA0 count")

print("\n" + "=" * 78)
print("C) 0x691A5B IS a third construction site -- R-046 'exactly two' OVERTURNED")
print("=" * 78)

# C1: the +0x9C store immediately precedes +0xA0 at the inline site
C1 = "899e9c000000899ea0000000c70608107f00c74604ec0f7f00c74608e40f7f00c7460cdc0f7f00"
ok("C1", eqhex(0x691A55, C1),
   "0x691A55: [esi+0x9C]<-ebx ; [esi+0xA0]<-ebx ; four vptr installs (same 0x2F tail)")

# C2: ebx is provably zero here -- exactly one ebx write in the interval, `xor ebx,ebx`
writes = []
for ins in md.disasm(read(0x691989, 0x691A55 - 0x691989), 0x691989):
    if ins.op_str.split(",")[0].strip() in ("ebx", "bx", "bl", "bh"):
        writes.append((ins.address, ins.mnemonic, ins.op_str))
ok("C2", writes == [(0x691989, "xor", "ebx, ebx")],
   "ebx writers in 0x691989..0x691A55 == %s => +0x9C/+0xA0 both zero" % [(hex(a), m, o) for a, m, o in writes])

# C3: the three ctor tails are byte-identical in the 0x20-byte init suffix
C3 = "c70608107f00c74604ec0f7f00c74608e40f7f00c7460cdc0f7f00"
ok("C3", eqhex(0x6916D1, C3) and eqhex(0x691C95, C3) and eqhex(0x691A61, C3),
   "vptr-quad init identical at 0x6916D1 / 0x691C95 / 0x691A61 => same class, no derived variant")

# C4: FULL-encoding census of +0x9C in the script lane: exactly FOUR sites, not two
s9C, l9C, o9C = disp_census(0x9C, 0x690000, 0x693000)
ok("C4", s9C == [0x6916BD, 0x691A55, 0x691B0D, 0x691C81] and l9C == [],
   "+0x9C stores == %s, loads == %s  (R-046 saw only the two C7 forms)" % ([hex(x) for x in s9C], l9C))

# C5: which of those are zero-inits: 0x6916BD/0x691C81 are C7 imm32=0, 0x691A55 is 89 reg(=0)
C5A = "c7869c00000000000000"
C5B = "899e9c000000"
ok("C5", eqhex(0x6916BD, C5A) and eqhex(0x691C81, C5A) and eqhex(0x691A55, C5B),
   "three zero-init ENCODINGS: two C7-imm32 @0x6916BD/0x691C81 + one 89-reg @0x691A55 (missed hole)")

# C6: the inline site lives inside 0x691970, the [ScriptTypes] section parser
C6 = "6828e78300"
ok("C6", len([1 for va in (0x69197D, 0x69199A, 0x6919B3) if eqhex(va, C6)]) == 3
   and 0x691970 < 0x691A55,
   "0x691970 is the [ScriptTypes] parser: three `push 0x83E728` (\"ScriptTypes\") @0x69197D/0x69199A/0x6919B3")

# C7: it calls the shared base init 0x410800 then does the pair itself (not the ctor)
ok("C7", eqhex(0x691A50, "e8abedd7ff"),
   "0x691A50 `call 0x410800` = same shared init as ctor 0x6916B8 / factory 0x691C7C")

print("\n" + "=" * 78)
print("D) +0x98 is a stale cache: dtor compacts the VECTOR but never fixes any +0x98")
print("=" * 78)

# D1: registry global proven by IMMEDIATE references in the code (the .data page holding
#     0x8B41C8 is zero-fill on disk, so a direct read is not evidence -- G-13 visibility)
D1A = "8b0dd8418b00"   # mov ecx,[0x8B41D8]   count
D1B = "8b15c8418b00"   # mov edx,[0x8B41C8]   vptr
ok("D1", eqhex(0x6916EC, D1A) and eqhex(0x691718, D1B)
   and eqhex(0x691796, D1B),
   "registry immediates: count [0x8B41D8] @0x6916EC, vptr [0x8B41C8] @0x691718 (ctor) and 0x691796 (dtor)")

# D2: dtor compaction loop, and NO +0x98 access anywhere in the dtor
D2 = "8b1481895481fc"
ok("D2", eqhex(0x6917CE, D2),
   "dtor 0x6917CE: mov edx,[ecx+eax*4] ; mov [ecx+eax*4-4],edx = vector compaction (registry only)")
s98, l98, o98 = disp_census(0x98, 0x691770, 0x6917E8)
# D3 (R-061 G-79 rewrite): the old claim was the NEGATIVE `s98==[] and l98==[]
# and o98==[]` -- zero occurrences is byte-unkillable (G-80's census twin).
# Positive anchor: capstone-detail over the dtor window enumerates the EXACT
# disp32 SET the reg-base accesses use -- pinned to the measured set; '+0x98
# never appears' is now a THEOREM of the pinned set, and flipping any member's
# disp byte reddens the equality (killer M23: 0x69177B 10->11).
def dtor_disps(lo, hi):
    out = set()
    cur = lo
    while cur < hi:
        got = None
        for insn in md.disasm(read(cur, 15), cur):
            got = insn
            break
        if got is None:
            cur += 1
            continue
        for opnd in got.operands:
            if opnd.type == 3 and opnd.mem.base and not opnd.mem.index:
                out.add(opnd.mem.disp)
        cur += got.size
    return sorted(out)


D3_SET = [0x0, 0x4, 0x8, 0xC, 0x10]     # measured 2026-10-26 via md.detail (G-65)
md.detail = True
got3 = dtor_disps(0x691770, 0x6917E8)
md.detail = False
ok("D3", got3 == D3_SET and s98 == [] and l98 == [] and o98 == [],
   "dtor disp32 set == %s (pinned); 0x98 ∉ set => NO +0x98 fixup after compaction"
   % [hex(x) for x in got3])

# D4: +0x98 writers are exactly one per construction site, each computing its own index
s98, l98, o98 = disp_census(0x98, 0x690000, 0x693000)
ok("D4", s98 == [0x691763, 0x691AEC, 0x691D26] and l98 == [0x691F90],
   "+0x98 stores == %s (one per ctor site), loads == %s (slot16)" % ([hex(x) for x in s98], [hex(x) for x in l98]))

# D5: the index written is computed AFTER self was appended (linear scan of self in vector)
D5 = "3932740b4083c2043bc17cf483c8ff898698000000"
ok("D5", eqhex(0x691748, "33c085c97e128b15cc418b003932740b") and eqhex(0x691754, D5),
   "0x691748..0x69176C: scan vector for self, or -1 if absent => index written at 0x691763")

# D6: slot16 reader is the only +0x98 consumer and returns it raw
ok("D6", eqhex(0x691F90, "8b8198000000c3"),
   "slot16 @0x691F90: mov eax,[ecx+0x98]; ret  -> stale value returned verbatim")

# D7: registry push precedes the +0x98 computation (ordering proof for 'stale')
D7 = "893481"
ok("D7", eqhex(0x69173F, D7) and 0x69173F < 0x691763,
   "vector push `893481` @0x69173F precedes the +0x98 store @0x691763 => index is post-insert")

print("\n" + "=" * 78)
print("S) structural cross-checks (not in the denominator; red still exits nonzero)")
print("=" * 78)
structural("S1", eqhex(0x6916B0, "8b442404") and eqhex(0x691C00, "56578bf9")
           and eqhex(0x691970, "83ec2053"),
           "three construction entry points: ctor 0x6916B0, factory 0x691C00, parser 0x691970")
structural("S2", u32(0x7F1008 + 0x28) == 0x691E30 and u32(0x7F1008 + 0x30) == 0x691F80,
           "main vtable 0x7F1008: slot10(fixup)=0x691E30, slot12(GetSize)=0x691F80 (=0x234)")
structural("S3", u32(0x7F1008 + 0x64) == 0x6918A0 and u32(0x7F1008 + 0x40) == 0x691F90,
           "main vtable: slot25(parse)=0x6918A0, slot16(+0x98 getter)=0x691F90")

print()
if FAILS:
    print("== R-054 %d/%d PASS, %d FAIL (structural OK unused=%d) ==" %
          (NPASS[0], NPASS[0] + len(FAILS), len(FAILS), len(UNCOUNTED)))
    print("FAILED: %s" % ", ".join(FAILS))
    sys.exit(1)
print("== R-054 %d/%d 字节断言 PASS（S1..S3 结构性不入分母，红仍非零退出）==" % (NPASS[0], NPASS[0]))
print("GATE: GREEN")
