# -*- coding: utf-8 -*-
"""
W168 boundary validation FROM KNOWN FUNCTION ENTRIES (R12_FACTS §3/§6.2 compliant).
Also re-check the "each wildcard string appears twice in .data" claim (case-insensitive + substring).
"""
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SKIPDATA

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000
pe = pefile.PE(EXE, fast_load=False)
data = open(EXE,"rb").read()

def va2off(va): return pe.get_offset_from_rva(va-IB)

md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True

print("=== A. boundary check from function entries ===")
checks = [
    (0x52CB90, 473,  {0x52CBA1:"BATTLEMD*.INI literal", 0x52CBA9:"FindFirstFileA call",
                      0x52CCAB:"FindNextFileA call", 0x52CCBA:"FindClose call",
                      0x52CC4F:"BATTLEMD.INI literal"}),
    (0x52CD70, 1728, {0x52CD98:"RULEMD*.INI literal", 0x52CDAC:"FindFirstFileA call",
                      0x52CF19:"FindNextFileA call", 0x52CF28:"FindClose call",
                      0x52CE24:"RULESMD.INI literal", 0x52CF39:"RULESMD.INI literal"}),
]
for entry, size, targets in checks:
    code = data[va2off(entry):va2off(entry)+size]
    found = {}
    insns = 0
    for insn in md.disasm(code, entry):
        insns += 1
        for t in targets:
            if insn.address <= t < insn.address + insn.size:
                found[t] = (insn.address, insn.mnemonic, insn.op_str, insn.bytes.hex(), insn.size)
    print(f"fn 0x{entry:08X} size={size} decoded={insns}")
    for t, label in sorted(targets.items()):
        if t in found:
            a,mn,op,by,sz = found[t]
            off = t-a
            print(f"   target 0x{t:08X} [{label}] -> insn @0x{a:08X} {mn} {op} bytes={by} size={sz} (offset {off} into insn)")
        else:
            print(f"   target 0x{t:08X} [{label}] NOT FOUND from this entry (NOT necessarily non-boundary)")

print("\n=== B. .data / whole-file occurrences, case-insensitive & substring ===")
low = data.lower()
for s in [b"BATTLEMD*.INI", b"RULEMD*.INI", b"BATTLEMD", b"RULEMD", b"BATTLEMD.INI", b"RULESMD.INI"]:
    pat = s.lower()
    hits=[]; st=0
    while True:
        i=low.find(pat,st)
        if i<0: break
        hits.append(i); st=i+1
    print(f"{s.decode()!r}: {len(hits)} occurrences -> {[hex(h) for h in hits]}")

print("\n=== C. print bytes around the two wildcard strings (with neighbors) ===")
for va in [0x826180, 0x826190, 0x826250, 0x826260, 0x826268, 0x826270]:
    off=va2off(va)
    chunk=data[off:off+48]
    # show until 2nd NUL
    print(f"0x{va:08X}: {chunk[:32].hex()}  ascii={''.join(chr(c) if 32<=c<127 else '.' for c in chunk[:32])}")
