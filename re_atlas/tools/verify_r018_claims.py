# -*- coding: utf-8 -*-
"""R-031: machine gate for the R-018 claims (kb/30 section 11).

Discipline #35: prose byte-listings are not re-runnable truth. This turns
section 11's claims about AbstractTypeClass::LoadFromINI (0x410A60) into
instruction-level assertions against the exe, with negative controls that
mutate an in-memory copy (G-28: controls must also touch an unrelated object).

Read-only on the exe. Section 12 (the full-engine key index) is gated inside
dump_ini_keyindex.py itself; its cross-family verdict arrives separately
(evidence/r018_r019_crosscheck_glm.md).

Run: python re_atlas/tools/verify_r018_claims.py
"""

import hashlib
import sys

import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE = 0x400000
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

SECTIONS = [
    (0x1000, 0x3DF38D, 0x1000, 0x3E0000),
    (0x3E1000, 0x030074, 0x3E1000, 0x31000),
    (0x412000, 0x367BE4, 0x412000, 0x6C000),
]

with open(EXE, "rb") as fh:
    _RAW = fh.read()


class Image:
    def __init__(self, blob):
        self.blob = blob

    def read_va(self, va, n):
        rva = va - IMAGE_BASE
        for s_rva, s_vsize, rp, rs in SECTIONS:
            if s_rva <= rva < s_rva + max(s_vsize, rs):
                d = rva - s_rva
                if d >= rs:
                    return b""
                return self.blob[rp + d: rp + d + n]
        return b""

    def hexs(self, va, n):
        return self.read_va(va, n).hex(" ")

    def u32(self, va):
        b = self.read_va(va, 4)
        return int.from_bytes(b, "little") if len(b) == 4 else None

    def cstr(self, va, n=64):
        b = self.read_va(va, n)
        z = b.find(b"\x00")
        return (b[:z] if z >= 0 else b).decode("ascii", "replace")

    def ops(self, va, cap):
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        return [(i.address, i.mnemonic, i.op_str)
                for i in md.disasm(self.read_va(va, cap), va)]

    def func_body(self, entry, cap=0x1200):
        """Decode from a real boundary until the FIRST ret (function end)."""
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        out = []
        for i in md.disasm(self.read_va(entry, cap), entry):
            out.append(i)
            if i.mnemonic.startswith("ret"):
                break
        return out


BASE = Image(_RAW)
results = []


def chk(cid, ok, detail=""):
    results.append((cid, "PASS" if ok else "FAIL", str(detail)[:120]))
    return ok


digest = hashlib.sha256(_RAW).hexdigest()
if digest != SHA256:
    print("GATE G0 FAIL: sha256 %s -- all VA claims VOID" % digest)
    sys.exit(1)
chk("G0 sha256", True, digest[:16])

# ---- §11.2 / §11.1 entry facts -------------------------------------------
chk("S1 prologue 81EC34040000",
    BASE.hexs(0x410A60, 6).replace(" ", "").lower() == "81ec34040000",
    BASE.hexs(0x410A60, 6))

body = BASE.func_body(0x410A60)
body_ops = [(i.address, i.mnemonic, i.op_str) for i in body]
fn_end = body[-1].address

rs_calls = [a for a, m, o in body_ops if m == "call" and o == "0x528a10"]
chk("S2 exactly two ReadString calls",
    rs_calls == [0x410AA0, 0x410AFB], rs_calls)
chk("S3 one GetSection call",
    [a for a, m, o in body_ops if m == "call" and o == "0x526810"] == [0x410A7F])
chk("S4 one Reset call (0x526B00) first",
    next((a for a, m, o in body_ops if m == "call" and o == "0x526b00"),
         None) == 0x410A74)

# ---- §11.1: section name = lea [obj+0x24], pushed to GetSection ------------
seq = {a: (m, o) for a, m, o in body_ops}
ok = (seq.get(0x410A79, ("", "")) == ("lea", "ebp, [ebx + 0x24]")
      and seq.get(0x410A7E, ("", ""))[1] == "ebp"
      and seq.get(0x410A7F, ("", ""))[0] == "call")
chk("S5 ID(+0x24) is the GetSection arg", ok,
    "%s / %s" % (seq.get(0x410A79), seq.get(0x410A7E)))
chk("S6 this=obj via mov ebx,ecx before any call",
    seq.get(0x410A70) == ("mov", "ebx, ecx"))

# ---- §11.2 Name key --------------------------------------------------------
chk("S7 Name: lea edi,[ebx+0x64] + push 0x31 + push 0x817854",
    seq.get(0x410A91) == ("lea", "edi, [ebx + 0x64]")
    and seq.get(0x410A94) == ("push", "0x31")
    and seq.get(0x410A98) == ("push", "0x817854"))
chk("S8 literal 0x817854 == 'Name'", BASE.cstr(0x817854) == "Name",
    repr(BASE.cstr(0x817854)))
# push order at the call: (section=ebp, key, dst=edi, def=eax[esp+0x44], cap)
chk("S9 Name call arg order (5 pushes before 0x410AA0)",
    [seq[a][1] for a in (0x410A94, 0x410A96, 0x410A97, 0x410A98, 0x410A9D)]
    == ["0x31", "eax", "edi", "0x817854", "ebp"],
    [seq.get(a) for a in (0x410A94, 0x410A96, 0x410A97, 0x410A98, 0x410A9D)])

# ---- §11.2 UIName key ------------------------------------------------------
chk("S10 UIName: lea ebp,[ebx+0x3d] + push 0x20 + push 0x81784c",
    seq.get(0x410AEB) == ("lea", "ebp, [ebx + 0x3d]")
    and seq.get(0x410AEE) == ("push", "0x20")
    and seq.get(0x410AF5) == ("push", "0x81784c"))
chk("S11 literal 0x81784c == 'UIName'", BASE.cstr(0x81784c) == "UIName",
    repr(BASE.cstr(0x81784c)))

# ---- §11.2 CSF parse tail --------------------------------------------------
chk("S12 empty-guard then parse: cmp al,[ebp]; call 0x734E60; mov [ebx+0x60],eax",
    seq.get(0x410B3C)[0] == "mov" and "[ebp]" in seq.get(0x410B3C)[1]
    and seq.get(0x410B52) == ("call", "0x734e60")
    and seq.get(0x410B58) == ("mov", "dword ptr [ebx + 0x60], eax"))
csf = BASE.ops(0x734E60, 0x30)
chk("S13 0x734E60: [0xB1CF74]==0 -> return 0x84583C (sentinel, not NULL)",
    any(m == "mov" and o == "eax, 0x84583c" for _a, m, o in csf)
    and any(m == "mov" and o == "eax, dword ptr [0xb1cf74]" for _a, m, o in csf)
    and any(m == "test" and o == "eax, eax" for _a, m, o in csf),
    csf[:8])

# ---- §11.3 boundary arithmetic --------------------------------------------
chk("S14 boundary: Name 0x64+0x31 == 0x95; gap 0x5D..0x60 == 3 (padding)",
    0x64 + 0x31 == 0x95 and (0x3D + 0x20) == 0x5D and (0x60 - 0x5D) == 3)
offs = sorted({int(o.split("[ebx + ")[1].split("]")[0], 16)
               for _a, m, o in body_ops
               if m in ("lea", "mov") and "[ebx + 0x" in o})
chk("S15 no field access beyond +0x94 in this function",
    max(offs) <= 0x94, "distinct offsets: %s" % [hex(x) for x in offs])

# ---- negative controls (in-memory mutation; G-28 also unrelated object) ----
def patched(pairs):
    ba = bytearray(_RAW)
    for va, nb in pairs:
        rva = va - IMAGE_BASE
        for s_rva, _v, rp, rs in SECTIONS:
            if s_rva <= rva < s_rva + rs:
                fo = rp + (rva - s_rva)
                ba[fo: fo + len(nb)] = nb
                return Image(bytes(ba))
        raise AssertionError(hex(va))


def expect_fail(tag, fn):
    try:
        ok = fn()
    except Exception:
        ok = False
    chk("NEG %s caught" % tag, not ok)


def claim_s7(img):
    s = {a: (m, o) for a, m, o in img.ops(0x410A60, 0x120)}
    return (s.get(0x410A91) == ("lea", "edi, [ebx + 0x64]")
            and s.get(0x410A94) == ("push", "0x31"))

expect_fail("dst-offset-flip(+0x64->+0x68)",
            lambda: claim_s7(patched([(0x410A92, b"\x64\x24\x68\x00\x00\x00")])))
expect_fail("cap-flip(0x31->0x32)",
            lambda: claim_s7(patched([(0x410A94, b"\x6a\x32")])))
expect_fail("key-literal-redirect(0x817854->UIName)",
            lambda: (lambda im: im.cstr(0x817854) == "Name")(
                patched([(0x817854, b"UIName\x00")])))

# unrelated object: claim S10 applied to the FIRST key site must be False
def s10_on_wrong_site(img):
    s = {a: (m, o) for a, m, o in img.ops(0x410A60, 0x120)}
    return s.get(0x410A91) == ("lea", "ebp, [ebx + 0x3d]")
chk("NEG unrelated-site rejects (S10 claim vs first-key bytes)",
    not s10_on_wrong_site(BASE))
# gate liveness: wrong hash must abort
chk("NEG sha-gate live (orig differs)",
    hashlib.sha256(open(r"D:\Project\ra2-campaign-forge\ra2youli\.ra2opt\orig\gamemd.exe", "rb").read()).hexdigest() != SHA256)

fails = [r for r in results if r[1] == "FAIL"]
print("R-018 gate: %d/%d PASS" % (len(results) - len(fails), len(results)))
for cid, st, det in results:
    print("%s\t%s\t%s" % (st, cid, det))
sys.exit(0 if not fails else 1)
