"""m6: targeted byte probes for the two controls whose literal verdict had to be settled.

P1. 004F4240 — how is global 0x87F7E8 written? The litmus is whether ANY second table is
    installed on that global (then slot 0 is not unanimous and ④-livevt fails literally).
P2. 0045A640 — dump its extent and the loop body, to check whether the loop really writes.
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core2 as C
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

C.build_jt(); C.build_index()
OUT = Path(__file__).parent.parent

WRITE_MNEMS = {'mov', 'movzx', 'movsx', 'add', 'sub', 'and', 'or', 'xor', 'inc', 'dec',
               'shl', 'shr', 'sar', 'sal', 'rol', 'ror', 'xchg', 'not', 'neg', 'sete', 'setne'}

def abs_ops(ins):
    """[absolute] memory operands"""
    out = []
    try: ops = ins.operands
    except Exception: return out
    for o in ops:
        if o.type == X86_OP_MEM and o.mem.base == 0 and o.mem.index == 0:
            out.append(('%08X' % (int(o.mem.disp) & 0xffffffff), o.size))
    return out

print('=== P1: every .text insn referencing global 0x87F7E8 ===')
G = 0x87F7E8
hits = []
MD = C.MD
for ins in MD.disasm(C.CODE, C.TVA):
    for a, sz in abs_ops(ins):
        if a == '0087F7E8':
            wr = (ins.operands[0].type == X86_OP_MEM and ins.mnemonic in WRITE_MNEMS)
            hits.append((ins.address, ins.mnemonic, ins.op_str, wr))
            break
for a, m, o, wr in hits:
    print('  %08X  %-7s %-40s %s' % (a, m, o, 'WRITE' if wr else ''))
print('  total =', len(hits), ' writes =', sum(1 for h in hits if h[3]))

print()
print('=== P1b: installs recorded by the index for this global ===')
print('  INSTALLS =', [['%08X' % v, '%08X' % s] for v, s in C.INSTALLS.get(G, [])])
print('  DISPATCH =', [['%08X' % d, '%08X' % s] for d, s in C.DISPATCHES.get(G, [])])
print('  GLOBAL_VTS =', ['%08X' % v for v in sorted(C.GLOBAL_VTS.get(G, []))])

print()
print('=== P1c: does 0x7E1964 / 0x7E195C resolve as an RTTI vtable, and what is slot0? ===')
for vt in (0x7E195C, 0x7E1964):
    print('  vt %08X cls=%s  slot0=%08X   slot1=%08X' % (
        vt, C.rtti_class_of_vt(vt), C.u32(vt) or 0, C.u32(vt+4) or 0))
print('  -> slot0 unanimity across {7E195C,7E1964} for entry 004F4240:',
      C.slot_unanimous(G, 0x7E1964, 0))

print()
print('=== P1d: ctor 0x5BDA40 head (the legitimate install witness) ===')
lo, hi, addrs, blocks = C.extent(0x5BDA40, cap=200)
for ins in C.decode_fn(blocks)[:12]:
    print('  %08X  %-7s %s' % (ins.address, ins.mnemonic, ins.op_str))
print('  extent=[%08X,%08X) span=%d' % (lo, hi, hi-lo))

print()
print('=== P1e: atexit dtor 0x40D1B0 head (㉓: not a live vptr) ===')
lo, hi, addrs, blocks = C.extent(0x40D1B0, cap=200)
for ins in C.decode_fn(blocks)[:12]:
    print('  %08X  %-7s %s' % (ins.address, ins.mnemonic, ins.op_str))
print('  extent=[%08X,%08X) span=%d' % (lo, hi, hi-lo))

print()
print('=== P2: 0045A640 full body ===')
lo, hi, addrs, blocks = C.extent(0x45A640, cap=6000)
for ins in C.decode_fn(blocks):
    print('  %08X  %-7s %s' % (ins.address, ins.mnemonic, ins.op_str))
print('  extent=[%08X,%08X) span=%d n_ins=%d  (atlas size?)' % (lo, hi, hi-lo, len(addrs)))

print()
print('=== P2b: 0045A640 writes? (non-stack) ===')
for ins in C.decode_fn(blocks):
    if ins.operands and ins.operands[0].type == X86_OP_MEM and ins.mnemonic in WRITE_MNEMS:
        m = ins.operands[0].mem
        stk = (m.base in (C.X86_REG_ESP, C.X86_REG_EBP) and m.index == 0)
        print('  %08X %-7s %-28s %s' % (ins.address, ins.mnemonic, ins.op_str,
                                        'STACK(not counted)' if stk else 'NON-STACK WRITE'))
