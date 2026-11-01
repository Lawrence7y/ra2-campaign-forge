# -*- coding: utf-8 -*-
"""R-063a probe4: bounded residual pins (read-only).
  D1  vptr stamps near [0x887628]/[0x887640] stores -> RTTI names
  D2  sync-entry landmark ret-addrs (exact insn sizes)
  D3  alternate pump identities (0x432C.., 0x53E7xx/0x53E8xx, 0x759xxx, 0x775A70, 0x77F900)
  D4  host A SetForegroundWindow context 0x6BBE70..
  D5  WM_CREATE case block head 0x77778D + [0xA8EDA0] writers
  D6  [0xA8ED6B]/[0x884D34]/[0xB73560] writer census
"""
import hashlib
import re
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
raw = open(EXE, "rb").read()
assert hashlib.sha256(raw).hexdigest() == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e + 6)[0]
optsz = struct.unpack_from("<H", raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", raw, opt + 28)[0]
tab = opt + optsz
SEC = []
for i in range(nsec):
    name = raw[tab + i * 40: tab + i * 40 + 8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i * 40 + 8)
    SEC.append((name, IB + va, vsz, rp, rsz))
TEXT = next(s for s in SEC if s[0] == ".text")
TLO = TEXT[1]


def fo(va):
    for nm, sva, vsz, rp, rsz in SEC:
        if sva <= va < sva + vsz:
            off = rp + (va - sva)
            return off if off < rp + rsz else None
    return None


def rd(va, n):
    o = fo(va)
    return raw[o:o + n] if o is not None else b"\0" * n


def cstr(va, n=64):
    o = fo(va)
    if o is None:
        return None
    end = raw.find(b"\0", o, o + n)
    if end < 0:
        end = o + n
    s = raw[o:end]
    return s.decode("latin1") if all(32 <= c < 127 or c in (9, 10, 13) for c in s) else None


def rtti(vptr):
    if not (0x7E0000 < vptr < 0x812000):
        return None
    col = int.from_bytes(rd(vptr - 4, 4), "little")
    if not (0x7E0000 < col < 0x812000):
        return None
    td = int.from_bytes(rd(col + 0xC, 4), "little")
    if not (0x7E0000 < td < 0x812000):
        return None
    nm = rd(td + 8, 64).split(b"\0")[0].decode("latin1")
    return (col, td, nm)


MD = Cs(CS_ARCH_X86, CS_MODE_32)

print("D1 vptr stamps near singleton stores:")
for tag, around in (("[0x887640] store 0x560D67", 0x560D67), ("[0x887640] store 0x56107F", 0x56107F),
                    ("[0x887628] stamp 0x5605E6", 0x5605E6), ("[0x887628] stamp 0x685BBA", 0x685BBA),
                    ("[0x887628] stamp 0x686205", 0x686205)):
    print("   %s: ctx[-0x30..+0xC]=%s" % (tag, rd(around - 0x30, 0x3C).hex()))
    # scan window for c7 x0/x4x imm32 vptr patterns
    w = rd(around - 0x60, 0x80)
    for m in re.finditer(rb"\xc7[\x00-\x05\x40-\x47]....", w):
        imm = int.from_bytes(m.group(0)[2:6], "little")
        r = rtti(imm)
        if r:
            print("      vptr candidate %08X -> COL=%08X name=%r"
                  % (imm, r[0], r[1] and r[2]))

print("\nD2 sync-entry landmarks (exact ret addrs):")
SITES = {
    "Dispatch@pump0x5D4D50": 0x5D4E47, "Dispatch@0x432D1B": 0x432D1B,
    "Dispatch@0x53E8A1": 0x53E8A1, "Dispatch@0x759248": 0x759248,
    "Dispatch@0x759A76": 0x759A76,
    "SetActiveWindow@0x7775A9": 0x7775A9, "SetFocus-helper@0x7775B5": 0x7775B5,
    "SetFocus@create 0x777DC9": 0x777DC9, "ShowWindow@create 0x777DA9": 0x777DA9,
    "DestroyWindow@0x775B7B": 0x775B7B, "DestroyWindow@0x775CBB": 0x775CBB,
    "SetFgWindow in A @0x6BBE8B": 0x6BBE8B,
}
for tag, a in sorted(SITES.items(), key=lambda kv: kv[1]):
    for size in (2, 3, 5, 6, 7):
        ins = next(MD.disasm(rd(a, 8), a), None)
        if ins:
            break
    print("   %-28s call@%08X bytes=%s size=%d retaddr=%08X"
          % (tag, a, ins.bytes.hex() if ins else "??",
             ins.size if ins else 0, a + (ins.size if ins else 0)))

print("\nD3 alternate pumps:")
for tag, a, n in (("fn@0x432C70ish (Dispatch 0x432D1B host)", 0x432C70, 24),
                  ("fn@0x53E770 (PeekMessage wrapper)", 0x53E770, 14),
                  ("fn@0x53E860ish (Dispatch 0x53E8A1 host)", 0x53E860, 24),
                  ("fn@0x759200ish (Dispatch 0x759248 host)", 0x759200, 24),
                  ("fn@0x759940 (flag loop, Dispatch 0x759A76)", 0x759940, 30),
                  ("fn@0x775A70 (counter+?)", 0x775A70, 14),
                  ("fn@0x77F900 (counter writer)", 0x77F900, 20)):
    print("   -- %s" % tag)
    a = a
    for _ in range(n):
        ins = next(MD.disasm(rd(a, 15), a), None)
        if ins is None:
            break
        print("   %08X: %-20s %-5s %s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str))
        a += ins.size

print("\nD4 host A SetForegroundWindow context:")
a = 0x6BBE70
for _ in range(14):
    ins = next(MD.disasm(rd(a, 15), a), None)
    if ins is None:
        break
    print("   %08X: %-20s %-5s %s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    a += ins.size

print("\nD5 WM_CREATE case head 0x77778D + [0xA8EDA0] writers:")
a = 0x77778D
for _ in range(14):
    ins = next(MD.disasm(rd(a, 15), a), None)
    if ins is None:
        break
    print("   %08X: %-20s %-5s %s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    a += ins.size
text_bytes = raw[TEXT[3]: TEXT[3] + TEXT[4]]
hits = []
for pat in (b"\xc7\x05\xa0\xed\xa8\x00", b"\x89\x1d\xa0\xed\xa8\x00",
            b"\xa3\xa0\xed\xa8\x00", b"\x89\x05\xa0\xed\xa8\x00",
            b"\x89\x0d\xa0\xed\xa8\x00", b"\x89\x15\xa0\xed\xa8\x00"):
    s0 = 0
    while True:
        j = text_bytes.find(pat, s0)
        if j < 0:
            break
        hits.append((TLO + j, pat.hex()))
        s0 = j + 1
print("   [0xA8EDA0] direct-store writers: %s" % [(hex(a), p) for a, p in hits])

print("\nD6 adjacent-flag writer census:")
for g, pats in ((0xA8ED6B, [b"\xc6\x05\x6b\xed\xa8\x00", b"\x88\x1d\x6b\xed\xa8\x00",
                            b"\xa2\x6b\xed\xa8\x00", b"\x88\x05\x6b\xed\xa8\x00"]),
                (0x884D34, [b"\xc6\x05\x34\x4d\x88\x00", b"\x88\x1d\x34\x4d\x88\x00",
                            b"\xa2\x34\x4d\x88\x00", b"\xa1\x34\x4d\x88\x00",
                            b"\x8a\x05\x34\x4d\x88\x00", b"\x80\x3d\x34\x4d\x88\x00"]),
                (0xB73560, [b"\xa2\x60\x35\xb7\x00", b"\xc6\x05\x60\x35\xb7\x00",
                            b"\x88\x1d\x60\x35\xb7\x00", b"\xa0\x60\x35\xb7\x00",
                            b"\x80\x3d\x60\x35\xb7\x00"])):
    out = []
    for p in pats:
        s0 = 0
        while True:
            j = text_bytes.find(p, s0)
            if j < 0:
                break
            out.append((TLO + j, p.hex()))
            s0 = j + 1
    print("   %08X: %s" % (g, [(hex(a), p) for a, p in out]))
print("\nDONE probe4")
