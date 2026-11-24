# -*- coding: utf-8 -*-
"""R16-FIX-B2-1ROW read-only exploration part 2: extra non-stack sites + ctor-likeness."""
import os, sys
sys.dont_write_bytecode = True
import capstone, pefile
IB = 0x400000
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    secs.append((IB + s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData,
                 s.get_data(), s.Name.rstrip(b"\x00").decode("latin-1")))
end = max(va + max(vs, rs) for va, vs, rs, _d, _n in secs)
buf = bytearray(end - IB + 16)
for va, vs, rs, d, nm in secs:
    buf[va - IB:va - IB + len(d)] = d
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True
def dis(va, n):
    return list(md.disasm(bytes(buf[va-IB:va-IB+n]), va))
for h, n in [(0x697820,0x40),(0x759500,0x40),(0x47AA30,0x20),(0x431B20,0x30),(0x43AD00,0x20),(0x47AE10,0x20)]:
    print("== %08X ==" % h)
    for x in dis(h, n):
        print("  %08X  %-20s %s %s" % (x.address, x.bytes.hex(), x.mnemonic, x.op_str))
