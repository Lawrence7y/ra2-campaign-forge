"""diagnostics for controls: indirect jmps, jump-table shape, arm signatures"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core as C
import b3

C.build_jt()
for e in (0x00702D40, 0x00706640, 0x00708C30, 0x004D82B0, 0x004D5690, 0x004DB260, 0x004D94B0, 0x00595740):
    lo, hi, addrs, blocks = C.extent(e)
    ins = C.decode_fn(blocks)
    print('=== %08X extent %08X..%08X nins %d blocks %d' % (e, lo, hi, len(ins), len(blocks)))
    for i in ins:
        if i.mnemonic == 'jmp' and i.operands and i.operands[0].type == C.X86_OP_MEM:
            m = i.operands[0].mem
            tg = C.TGT_JT.get(i.address - C.TVA)
            print('   IJT %08X %-32s base=%d idx=%d scale=%d disp=%#x  TGT=%s' % (
                i.address, i.op_str, m.base, m.index, m.scale, m.disp,
                [hex(t) for t in (tg or [])][:14]))
    if not ins:
        print('   <no instructions decoded>  len(addrs)=%d' % len(addrs))
