#!/usr/bin/env python3
"""R132 supplementary evidence: whole-file masked scan, imm-parser dual form,
capstone linear-sweep desync diagnosis, call-site raw table."""
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
t = [s for s in pe.sections if s.Name.rstrip(b"\x00") == b".text"][0]
TEXT_VA = IB + t.VirtualAddress
TEXT_SZ = min(t.Misc_VirtualSize, t.SizeOfRawData)
raw = open(EXE, "rb").read()
CODE = raw[t.PointerToRawData:t.PointerToRawData + TEXT_SZ]

A, L = 0x6BEDB0, 136
body = CODE[A - TEXT_VA: A - TEXT_VA + L]
MASK = set(range(34, 38)) | set(range(78, 82)) | set(range(112, 116))


def scan(buf, pat, mask):
    n = len(pat)
    fixed = [(i, pat[i]) for i in range(n) if i not in mask]
    return [s for s in range(len(buf) - n + 1) if all(buf[s + i] == b for i, b in fixed)]


# 1) whole-file (all sections) masked scan -> prove .text-only sweep is not missing hits
hits = scan(raw, body, MASK)
print("whole-file masked hits (file offsets):", [hex(x) for x in hits])
for off in hits:
    for s in pe.sections:
        if s.PointerToRawData <= off < s.PointerToRawData + s.SizeOfRawData:
            va = IB + s.VirtualAddress + (off - s.PointerToRawData)
            print("   off=%#x section=%s VA=%#x" % (off, s.Name.rstrip(b"\x00").decode(), va))

# 2) dual-form immediate parser
def parse_imm(s):
    s = s.strip()
    try:
        if s.lower().startswith(("0x", "-0x")):
            return int(s, 16)
        return int(s, 10)
    except ValueError:
        return None


print("parse_imm dual-form:",
      [(x, parse_imm(x)) for x in ("0x817bc0", "8485824", "0x10", "16", "0x14", "20")])

# 3) capstone linear sweep coverage + desync point
md = Cs(CS_ARCH_X86, CS_MODE_32)
count, last = 0, None
for ins in md.disasm(CODE, TEXT_VA):
    count += 1
    last = ins
print("capstone linear sweep: insns=%d last=%#x end=%#x text_end=%#x"
      % (count, last.address, last.address + last.size, TEXT_VA + TEXT_SZ))
stop = last.address + last.size
print("bytes at desync(%#x): %s" % (stop, CODE[stop - TEXT_VA - 8:stop - TEXT_VA + 16].hex(" ")))
print("disasm attempt at desync:", list(md.disasm(CODE[stop - TEXT_VA:stop - TEXT_VA + 16], stop, 1)))

# 4) raw E8 call table
targets = (0x6BEDB0, 0x41C250)
rows = []
i = CODE.find(b"\xe8")
while i >= 0:
    if i + 5 <= len(CODE):
        rel = int.from_bytes(CODE[i + 1:i + 5], "little", signed=True)
        src = TEXT_VA + i
        if src + 5 + rel in targets:
            rows.append((src, src + 5 + rel, rel))
    i = CODE.find(b"\xe8", i + 1)
print("total 0xE8 bytes in .text:", CODE.count(b"\xe8"))
print("E8-call rows (src -> target, rel32):")
for s, tg, r in rows:
    print("   %#x -> %#x  rel=%#x (%d)" % (s, tg, r & 0xFFFFFFFF, r))
print("count per target:", {hex(tg): sum(1 for _, x, _ in rows if x == tg) for tg in targets})
print("hits inside either function body:",
      [hex(s) for s, _, _ in rows
       if 0x6BEDB0 <= s < 0x6BEDB0 + L or 0x41C250 <= s < 0x41C250 + L])
