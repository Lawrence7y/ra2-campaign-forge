# -*- coding: utf-8 -*-
"""Identify 004011C0 and the callees 0x43AE50 / 0x431B80."""
import io, os, sys, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
IB = 0x400000
import pefile, capstone
pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    secs.append((s.Name.rstrip(b"\x00").decode("latin-1"), IB + s.VirtualAddress,
                 s.Misc_VirtualSize, s.SizeOfRawData, s.get_data()))
end = max(va + max(vs, rs) for _nm, va, vs, rs, _d in secs)
buf = bytearray(end - IB + 16)
for nm, va, vs, rs, d in secs:
    buf[va - IB:va - IB + len(d)] = d
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True
def dis(va, n):
    return list(md.disasm(bytes(buf[va - IB:va - IB + n]), va))
def u32(va):
    return int.from_bytes(buf[va - IB:va - IB + 4], "little")
def cstr(va, n=200):
    o = va - IB
    e = buf.find(b"\x00", o, min(o + n, len(buf)))
    return bytes(buf[o:e]).decode("latin-1", "replace") if e > 0 else None

out = []
def P(s=""):
    out.append(s)

P("### full disasm of host 004011C0 (size 953 -> 0x4011C0..0x4014DE)")
for ins in dis(0x4011C0, 0x320):
    P("   %08X: %-12s %s" % (ins.address, ins.mnemonic, ins.op_str))

P()
P("### writes with base register (analysis)")
ins_all = dis(0x4011C0, 0x320)
from collections import Counter
writes = []
for i in ins_all:
    if i.mnemonic in ("mov", "movsd", "stosd", "movsb") and i.operands:
        a = i.operands[0]
        if a.type == capstone.x86.X86_OP_MEM:
            base = i.reg_name(a.mem.base) if a.mem.base else "ABS"
            writes.append((i.address, i.mnemonic, base, a.mem.disp, i.op_str))
P("   base-register histogram of memory-destination ops: %s" % Counter(w[2] for w in writes))
for w in writes:
    if w[2] in ("esi", "ecx", "edi") or w[2] == "ABS":
        P("   TO-THIS-ISH %08X %s %s disp=%X : %s" % (w[0], w[1], w[2], w[3], w[4]))

P()
P("### callees identity: 0x43AE50 (called right before site), 0x431B80 (called right after)")
for f in (0x43AE50, 0x431B80, 0x431A30, 0x43B680, 0x401170, 0x413D20, 0x4385D0):
    P("  --- %08X ---" % f)
    for ins in dis(f, 40)[:14]:
        P("     %08X: %-12s %s" % (ins.address, ins.mnemonic, ins.op_str))

io.open(os.path.join(HERE, "_explore5.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote _explore5.txt", len(out), "lines")
