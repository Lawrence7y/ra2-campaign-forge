# -*- coding: utf-8 -*-
"""Confirm 004019A0 is the out-of-line CDFileClass ctor (writes vptr on this)."""
import io, os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
IB = 0x400000
import pefile, capstone
EXE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "ra2youli", "gamemd.exe")
pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    secs.append((IB + s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData, s.get_data()))
end = max(va + max(vs, rs) for va, vs, rs, _d in secs)
buf = bytearray(end - IB + 16)
for va, vs, rs, d in secs:
    buf[va - IB:va - IB + len(d)] = d
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True
def dis(va, n):
    return list(md.disasm(bytes(buf[va - IB:va - IB + n]), va))
for start, label in ((0x4019A0, "claimed CDFileClass ctor"), (0x4011C0 + 0x2E0, "inlined tail in 004011C0")):
    print("=== %08X  %s" % (start, label))
    for x in dis(start, 0x50):
        print("   %08X: %-12s %s" % (x.address, x.mnemonic, x.op_str))
    print()
# side-by-side of the two vptr-write sequences
print("=== 004011C0 tail (inlined) ===")
for x in dis(0x4014A0, 0x40):
    print("   %08X: %-12s %s" % (x.address, x.mnemonic, x.op_str))
