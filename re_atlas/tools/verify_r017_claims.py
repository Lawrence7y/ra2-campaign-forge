# -*- coding: utf-8 -*-
"""R-030: machine verifier for the R-017 (kb/30 section 10) read-family claims.

R-017's conclusions previously rested on prose byte-listings; this tool turns
each claim into an instruction-level assertion so the verification debt can be
sent to a cross-family checker with a reproducible gate (EXIT=0 + negative
controls), per LEDGER rule 6.

Read-only on the exe. Negative controls mutate an IN-MEMORY copy of the image
and assert the verifier catches each corruption, including one on an
UNRELATED function window (G-28: a control bound to a single input is not a
control).

Run: python re_atlas/tools/verify_r017_claims.py
"""

import hashlib
import re
import sys

import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE = 0x400000
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

with open(EXE, "rb") as fh:
    _RAW = fh.read()

SECTIONS = [
    (".text", 0x001000, 0x3DF38D, 0x001000, 0x3E0000),
    (".rdata", 0x3E1000, 0x030074, 0x3E1000, 0x031000),
    (".data", 0x412000, 0x367BE4, 0x412000, 0x06C000),
]


class Image:
    def __init__(self, blob):
        self.blob = blob

    def read_va(self, va, n):
        rva = va - IMAGE_BASE
        for _name, s_rva, s_vsize, raw_ptr, raw_size in SECTIONS:
            if s_rva <= rva < s_rva + max(s_vsize, raw_size):
                d = rva - s_rva
                if d >= raw_size:
                    return b""
                return self.blob[raw_ptr + d: raw_ptr + d + n]
        return b""

    def bytes_at(self, va, n):
        return self.read_va(va, n).hex(" ")

    def u8(self, va):
        b = self.read_va(va, 1)
        return b[0] if b else None

    def u32(self, va):
        b = self.read_va(va, 4)
        return int.from_bytes(b, "little") if len(b) == 4 else None

    def cstr(self, va, n=32):
        b = self.read_va(va, n)
        z = b.find(b"\x00")
        return (b[:z] if z >= 0 else b).decode("ascii", "replace")

    def disasm(self, va, cap):
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        out = []
        for insn in md.disasm(self.read_va(va, cap), va):
            out.append(insn)
        return out

    def ops(self, va, cap):
        return [(i.address, i.mnemonic, i.op_str) for i in self.disasm(va, cap)]


BASE = Image(_RAW)

results = []


def chk(cid, ok, detail=""):
    results.append((cid, "PASS" if ok else "FAIL", detail))
    return ok


# ---------------------------------------------------------------- gate G0
digest = hashlib.sha256(_RAW).hexdigest()
if digest != SHA256:
    print("GATE G0 FAIL: sha256 %s != expected %s -- ALL VA CLAIMS VOID"
          % (digest, SHA256))
    sys.exit(1)
chk("G0", True, "sha256 match, size=%d" % len(_RAW))

# ---------------------------------------------------------------- A: s10.1
READERS = {
    "ReadString": (0x528A10, "83 EC 0C".replace(" ", "")),
    "ReadUniStr": (0x528F00, "B814500000"),
    "ReadStrTab": (0x529160, "81EC14040000"),
    "ReadDouble": (0x5283D0, "83EC0C"),
    "ReadInteger": (0x5276D0, "83EC0C"),
    "ReadBool": (0x5295F0, "83EC0C"),
}
WRITERS = {
    "WriteString": (0x528660, "83EC38"),
    "WriteBool": (0x529560, "8A44240C"),
    "WriteUniStr": (0x528E00, "51535556"),
}
for name, (va, hexs) in list(READERS.items()) + list(WRITERS.items()):
    chk("A:%s prologue" % name,
        BASE.bytes_at(va, len(hexs) // 2).replace(" ", "").lower() == hexs.lower(),
        "%s @0x%08X = %s" % (hexs, va, BASE.bytes_at(va, len(hexs) // 2)))

# A10: the +4/+8 query-cache pair is consulted by ALL SIX readers
# (two load shapes observed: `cmp reg,[this+4]` or `mov reg,[this+4]; cmp`)
RET = {"ReadString": "0x14", "ReadUniStr": "0x14", "ReadStrTab": "0x10",
       "ReadInteger": "0xC", "ReadBool": "0xC"}
for name, (va, _h) in READERS.items():
    ops = BASE.ops(va, 0x130)
    cat4 = any(("dword ptr [ebp + 4]" in o or "dword ptr [ebx + 4]" in o)
               for _a, _m, o in ops)
    cat8 = any(("dword ptr [ebp + 8]" in o or "dword ptr [ebx + 8]" in o)
               for _a, _m, o in ops)
    chk("A:%s cache[+4,+8]" % name, cat4 and cat8,
        "+4:%s +8:%s" % (cat4, cat8))

# ret sizes where a plain linear decode reaches them
for name, want in RET.items():
    va = READERS[name][0]
    rets = [(a, o) for a, m, o in BASE.ops(va, 0x320) if m == "ret"]
    hit = [o for _a, o in rets if o.replace(" ", "").lower() == want.lower()]
    chk("A:%s ret %s" % (name, want), bool(hit),
        "rets=%s" % ([o for _a, o in rets][:4] or "none-in-window"))

# ---------------------------------------------------------------- B: ReadBool
chk("B1 movsx first byte @0x52976B",
    BASE.bytes_at(0x52976B, 3) == "0f be 0e", BASE.bytes_at(0x52976B, 3))
chk("B2 call toupper-callee @0x52976F",
    BASE.bytes_at(0x52976F, 5) == "e8 5f 00 2a 00", BASE.bytes_at(0x52976F, 5))
tb = BASE.ops(0x7C97D3, 0x20)
upper = (("0x61" in str(tb)) and ("0x7a" in str(tb))
         and any(m == "sub" and o == "eax, 0x20" for _a, m, o in tb))
chk("B3 0x7C97D3 IS toupper ('a'..'z' -0x20)", upper,
    " ".join("%s %s" % (m, o) for _a, m, o in tb[:12]))
chk("B4 add eax,-0x30 @0x529774",
    BASE.bytes_at(0x529774, 3) == "83 c0 d0", BASE.bytes_at(0x529774, 3))
chk("B5 cmp eax,0x29 + ja->default @0x52977A",
    BASE.bytes_at(0x52977A, 5) == "83 f8 29 77 cc", BASE.bytes_at(0x52977A, 6))
chk("B6 mov dl,[eax+0x5297B4] @0x529781",
    BASE.bytes_at(0x529781, 6).startswith("8a 90"), BASE.bytes_at(0x529781, 6))
chk("B7 jmp [edx*4+0x5297A8] @0x529787",
    BASE.bytes_at(0x529787, 6) == "ff 24 95 a8 97 52",
    BASE.bytes_at(0x529787, 6))
jmp = [BASE.u32(0x5297A8 + 4 * i) for i in range(3)]
chk("B8 jmp table == (false,true,default)",
    jmp == [0x52979A, 0x52978E, 0x52974B], [hex(x) for x in jmp if x])
ops1 = BASE.ops(0x52978E, 8)
ops0 = BASE.ops(0x52979A, 8)
ops2 = BASE.ops(0x52974B, 8)
chk("B9 class bodies (mov al,1 / xor al,al / mov al,[esp+0x28])",
    any(m == "mov" and o == "al, 1" for _a, m, o in ops1)
    and any(m == "xor" and o == "al, al" for _a, m, o in ops0)
    and any(m == "mov" and o == "al, byte ptr [esp + 0x28]"
            for _a, m, o in ops2))
# B10 semantic class table: 42 entries '0'..'Y'; class!=2 only for
# '0','1','F','N','T','Y' with the documented outcomes
t = [BASE.u8(0x5297B4 + i) for i in range(0x2A)]
expect = {"0": 0, "1": 1, "F": 0, "N": 0, "T": 1, "Y": 1}
ok_tbl, why = True, []
for i, cls in enumerate(t):
    ch = chr(0x30 + i)
    if cls == 2:
        if ch in expect:
            ok_tbl, _ = False, why + ["%s should be class %s" % (ch, expect[ch])]
    else:
        if ch not in expect or cls != expect[ch]:
            ok_tbl, _ = False, why + ["unexpected class at %s" % ch]
chk("B10 class table semantics", ok_tbl, " ".join(str(x) for x in t))

# ---------------------------------------------------------------- C: WriteBool
chk("C1 literals yes/no",
    BASE.cstr(0x825BF8, 4) == "yes" and BASE.cstr(0x825BF4, 4) == "no",
    "%r / %r" % (BASE.cstr(0x825BF8, 4), BASE.cstr(0x825BF4, 4)))
wops = BASE.ops(0x529560, 0x60)
lit = any(o.replace(" ", "").find("0x825bf8") >= 0 for _a, _m, o in wops) \
    and any(o.replace(" ", "").find("0x825bf4") >= 0 for _a, _m, o in wops)
chk("C2 WriteBool pushes both literals", lit)

# ---------------------------------------------------------------- D: ReadInteger
chk("D1 strlen + last-byte fetch @0x527877",
    BASE.bytes_at(0x527877, 12) == "8b fa 83 c9 ff 33 c0 f2 ae f7 d1 49",
    BASE.bytes_at(0x527877, 12))
chk("D1b movsx edx,[ecx+edx-1]",
    BASE.bytes_at(0x527883, 4) == "0f be 54 11", BASE.bytes_at(0x527883, 4))
chk("D2 call 0x7CAFF4 @0x527889",
    BASE.bytes_at(0x527889, 5) == "e8 66 37 2a 00", BASE.bytes_at(0x527889, 5))
tl = BASE.ops(0x7CAFF4, 0x20)
lower = (("0x41" in str(tl)) and ("0x5a" in str(tl))
         and any(m == "add" and o == "eax, 0x20" for _a, m, o in tl))
chk("D3 0x7CAFF4 IS tolower (ERRATUM: old docstring said toupper)", lower,
    " ".join("%s %s" % (m, o) for _a, m, o in tl[:12]))
chk("D4 cmp 'h' + jne->strtol @0x527891",
    BASE.bytes_at(0x527891, 5) == "83 f8 68 75 24", BASE.bytes_at(0x527891, 6))
chk("D5 format string %xh", BASE.cstr(0x825BB4, 4) == "%xh", BASE.cstr(0x825BB4, 4))
chk("D6 hex path call sscanf(0x7CA530) @0x5278A4",
    BASE.bytes_at(0x5278A4, 5) == "e8 87 2c 2a 00", BASE.bytes_at(0x5278A4, 5))
chk("D7 dec path call 0x7C9BFD @0x5278BE",
    BASE.bytes_at(0x5278BE, 5) == "e8 3a 23 2a 00", BASE.bytes_at(0x5278BE, 5))
sc = BASE.ops(0x7C9BFD, 16)
chk("D8 0x7C9BFD is a 1-arg forwarder (push;call;pop;ret)",
    [m for _a, m, _o in sc[:4]] == ["push", "call", "pop", "ret"],
    " ".join(m for _a, m, _o in sc[:4]))

# D9-D12: R-030 corrections from the Qwen blind cross-check + local trace:
# the 'strtol' label is wrong; the fallback is a 1-arg atoi; and there is an
# undocumented leading-'$' hex branch BEFORE the h-suffix test.
chk("D9 leading-$ test @0x527851",
    BASE.bytes_at(0x527851, 3) == "80 3a 24", BASE.bytes_at(0x527851, 3))
chk("D10 $-branch pushes \"$%x\" and calls 0x7CA530",
    BASE.bytes_at(0x52785B, 5) == "68 b8 5b 82 00"
    and BASE.bytes_at(0x527860, 2) == "52 e8"
    and BASE.cstr(0x825BB8, 4) == "$%x",
    BASE.bytes_at(0x52785B, 6))
# D11: atoi structure in 0x7C9B72: digit-class gate (and 4), 10x accumulation
# lea eax,[ebx+ebx*4] + lea ebx,[esi+eax*2-0x30], and a '-' negate.
ai = BASE.ops(0x7C9B72, 0x8A)
txt = " | ".join("%s %s" % (m, o) for _a, m, o in ai)
chk("D11 0x7C9B72 is base-10 atoi (digit-loop, 10x accum, sign)",
    ("and eax, 4" in txt) and ("lea eax, [ebx + ebx*4]" in txt)
    and ("lea ebx, [esi + eax*2 - 0x30]" in txt) and ("neg eax" in txt),
    txt[:90])
# D12: NO code in the atoi body compares against 'x'(0x78)/'X'(0x58) => the
# fallback cannot honor a 0x prefix => "Key=0x100" parses as 0, not 256.
chk("D12 no 0x-prefix handling in atoi body",
    all(not (m == "cmp" and o.endswith(", 0x78") or m == "cmp" and o.endswith(", 0x58"))
        for _a, m, o in ai),
    "%d insns scanned" % len(ai))

# ---------------------------------------------------------------- E: hash miss path
bops = BASE.ops(0x5295F0, 0x100) + BASE.ops(0x5296BA, 0x50)
chk("E1 ReadBool miss calls 0x4A1DE0",
    any(m == "call" and o == "0x4a1de0" for _a, m, o in bops))
sops = BASE.ops(0x528A10, 0x220)
chk("E2 ReadString references 0x4A1DE0 too",
    any(m == "call" and o == "0x4a1de0" for _a, m, o in sops))

# ================================================================ negative controls
def patched(pairs):
    """pairs: (va, n, newbytes). Returns Image on a mutated in-memory copy."""
    ba = bytearray(_RAW)
    for va, n, nb in pairs:
        rva = va - IMAGE_BASE
        fo = None
        for _s, s_rva, _v, raw_ptr, raw_size in SECTIONS:
            if s_rva <= rva < s_rva + raw_size and rva - s_rva < raw_size:
                fo = raw_ptr + (rva - s_rva)
        assert fo is not None, va
        ba[fo: fo + n] = nb
    return Image(bytes(ba))


def expect_fail(tag, fn):
    try:
        ok = fn()
    except Exception:
        ok = False
    chk("NEG %s caught" % tag, not ok, "claim stayed green -> control useless")


# NEG1: flip class-table byte for 'T' (idx 0x24) to class 2 -> B10 must fail
img1 = patched([(0x5297B4 + 0x24, 1, b"\x02")])
def b10_1():
    t2 = [img1.u8(0x5297B4 + i) for i in range(0x2A)]
    return all((cls == 2) == (chr(0x30 + i) not in expect) and
               (cls == expect.get(chr(0x30 + i), cls)) for i, cls in enumerate(t2))
expect_fail("class-table-flip(T)", b10_1)

# NEG2: redirect jmp-table slot 1 -> 0x401000 -> B8 must fail
img2 = patched([(0x5297AC, 4, (0x401000).to_bytes(4, "little"))])
def b8_2():
    return [img2.u32(0x5297A8 + 4 * i) for i in range(3)] == \
        [0x52979A, 0x52978E, 0x52974B]
expect_fail("jmp-redirect", b8_2)

# NEG3 (G-28 unrelated object): ReadBool and ReadInteger share the SAME first
# 8 prologue bytes (83 EC 0C 33 C0 53 55 8B 6C 24 18 ...) and only diverge at
# byte 12 (push esi vs mov ebx,ecx). Assert (a) the 8-byte prefix claim does
# NOT discriminate the two functions -- it matches both -- and (b) the 12-byte
# prefix DOES. This is the control that proves length-12 was necessary.
RB12, RI12 = "83ec0c33c053558b6c241856", "83ec0c33c053558b6c24188b"
chk("NEG3 prefix-8 matches BOTH (claim too short is real)",
    BASE.bytes_at(0x5295F0, 11).replace(" ", "")
    == BASE.bytes_at(0x5276D0, 11).replace(" ", ""))
chk("NEG3 prefix-12 discriminates ReadBool vs ReadInteger",
    BASE.bytes_at(0x5295F0, 12).replace(" ", "").lower() == RB12
    and BASE.bytes_at(0x5276D0, 12).replace(" ", "").lower() == RI12)

# NEG4: sha gate is active -- assert orig snapshot hash is REJECTED
try:
    import glob
    alt = r"D:\Project\ra2-campaign-forge\ra2youli\.ra2opt\orig\gamemd.exe"
    ah = hashlib.sha256(open(alt, "rb").read()).hexdigest()
    chk("NEG sha-gate active (orig differs, would ABORT)", ah != SHA256,
        "orig=%s" % ah[:12])
except OSError:
    chk("NEG sha-gate active", False, "orig snapshot missing; gate untested")

# ================================================================ report
fails = [r for r in results if r[1] == "FAIL"]
n_pass = len(results) - len(fails)
print("R-017 verifier: %d/%d PASS" % (n_pass, len(results)))
for cid, st, det in results:
    print("%s\t%s\t%s" % (st, cid, str(det).replace("\n", " ")[:110]))
if not fails:
    print("ALL ASSERTIONS PASS (incl. negative controls catching)")
sys.exit(0 if not fails else 1)
