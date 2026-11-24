"""Full .text linear sweep; list STORE refs to target globals (aligned decode)."""
import sys
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\x_ingame_close_20261026')
from common import IMG
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import struct

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
tb = 0x401000
data = IMG.read(tb, 0x3DF38D)

# Build set of instructions containing abs-address encodings of the globals, from correct alignment
targets = {
    0xA8EDD8: 'exitstate', 0xB73550: 'hwnd', 0x887368: 'singleton',
    0x887628: 'interceptor', 0x887640: 'scene', 0x89F978: 'guardflag',
    0xAA0444: 'rendermode', 0xA8ED84: 'a8ed84', 0xA8ED5C: 'flag5C',
    0xA8EDA0: 'sessionstate', 0xB73570: 'lastmsg_result',
}
pats = {struct.pack('<I', g): n for g, n in targets.items()}

# Use capstone jump-table aware? Simplest: disasm with a sliding alignment that respects
# ret/jmp boundaries is complex. Instead decode with cs.disasm_iter over whole buffer; capstone
# linear disasm will drift at data islands, but .text is mostly code. Filter by byte signature.
found = {g: [] for g in targets}
for ins in md.disasm(data, tb):
    for pat, nm in pats.items():
        if pat in ins.bytes:
            addr = int(nm, 16) if False else None
    # recompute per global
    for g, nm in targets.items():
        if struct.pack('<I', g) in ins.bytes:
            found[g].append((ins.address, f'{ins.mnemonic} {ins.op_str}', ins.bytes.hex().upper()))

out = sys.argv[1] if len(sys.argv) > 1 else 'stores.txt'
with open(out, 'w') as f:
    for g, nm in targets.items():
        f.write(f'== 0x{g:08X} {nm} ==\n')
        for a, s, bx in found[g]:
            # classify store: absolute appears in the destination operand part before first comma
            dst = s.split(',')[0].strip()
            store = ('[0x%x]' % g) in dst
            byte_dst = ('0x%x' % g) in dst
            f.write(f'  0x{a:08X}: [{bx:<24}] {s}  {"<==STORE" if store else ""}\n')
        f.write('\n')
print('done', sum(len(v) for v in found.values()))
