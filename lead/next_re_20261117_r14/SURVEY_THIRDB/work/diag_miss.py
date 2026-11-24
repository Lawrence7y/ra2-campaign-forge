import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core as C, b3
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

C.build_jt()

def show(e, rng=None, pred=None):
    fn = b3.Fn(e)
    print('=== %08X nins=%d nblk=%d' % (e, len(fn.ins), len(fn.blocks)))
    for i in fn.ins:
        if rng and not (rng[0] <= i.address <= rng[1]): continue
        if pred and not pred(i): continue
        print('  %08X %-18s %s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
    return fn

print('########## 004DB260 (expect ③b④ loop 8 offsets) ##########')
fn = b3.Fn(0x004DB260)
print(' b4 ->', b3.b4(fn))
# find back edges
for k, i in enumerate(fn.ins):
    t = b3.term_of(i)
    if t and t[0] == 'jcc' and t[1] and fn.lo <= t[1][0] < i.address:
        body = [y for y in fn.ins if t[1][0] <= y.address <= i.address]
        print(' backedge %08X -> %08X  body=%d' % (i.address, t[1][0], len(body)))
        for y in body[:40]:
            print('    %08X %-14s %s %s' % (y.address, y.bytes.hex(), y.mnemonic, y.op_str))

print('########## 004D94B0 (expect ③b② HRESULT) ##########')
fn = b3.Fn(0x004D94B0)
print(' b2 ->', b3.b2(fn))
for i in fn.ins:
    if (i.mnemonic in ('cmp','test') and any(o.type == X86_OP_IMM and (o.imm & 0xffffffff) >= 0x80000000 for o in i.operands)) \
       or i.mnemonic == 'call':
        print('  %08X %-18s %s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))

print('########## 00595740 (expect ③b③ 13 ctor + 2 vt + 0x318) ##########')
fn = b3.Fn(0x00595740)
print(' b3 ->', b3.b3(fn))
for i in fn.ins:
    if i.mnemonic == 'call' or (i.mnemonic == 'mov' and len(i.operands) > 1 and i.operands[1].type == X86_OP_IMM
                                and (int(i.operands[1].imm) & 0xffffffff) >= 0x40):
        print('  %08X %-18s %s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
