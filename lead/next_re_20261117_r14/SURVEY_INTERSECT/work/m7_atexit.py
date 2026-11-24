"""m7: atexit-registration probe (R14_COMMON §8.6 条1 / §8.1 错源 ㉓).

An `atexit`-installed vtable is NOT a live vptr. Operationally: find every
`push <imm>` whose immediate is a .text address, followed within a few
instructions by a call to the CRT atexit entry, and treat the pushed address as
an atexit-registered destructor.
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core2 as C
from capstone.x86 import X86_OP_IMM

C.build_jt()

ATEXIT = 0x7C978A
print('=== is 0x%08X the atexit entry? callers found: ===' % ATEXIT)
callers = C.DIRECT.get(ATEXIT, [])
print('  DIRECT[%08X] = %d sites %s' % (ATEXIT, len(callers), ['%08X' % s for s in callers[:10]]))

# scan for `push <text-imm>` .. `call ATEXIT`
reg = []
ins_list = list(C.MD.disasm(C.CODE, C.TVA))
for k, ins in enumerate(ins_list):
    if ins.mnemonic != 'call' or ins.size != 5 or ins.bytes[0] != 0xE8: continue
    tgt = (ins.address + 5 + int.from_bytes(ins.bytes[1:5], 'little', signed=True)) & 0xffffffff
    if tgt != ATEXIT: continue
    for j in range(max(0, k-8), k):
        p = ins_list[j]
        if p.mnemonic == 'push' and len(p.operands) == 1 and p.operands[0].type == X86_OP_IMM:
            v = int(p.operands[0].imm) & 0xffffffff
            if C.in_text(v):
                reg.append((v, p.address, ins.address))
print('  push<dtor>; call atexit  pairs =', len(reg))
for v, pa, ca in reg[:12]:
    print('    dtor=%08X pushed@%08X call@%08X' % (v, pa, ca))

ATEXIT_DTORS = {v for v, pa, ca in reg}
print('  distinct atexit-registered entries =', len(ATEXIT_DTORS))
print('  is 0040D1B0 among them?', 0x40D1B0 in ATEXIT_DTORS)

# which livevt install sites fall inside an atexit dtor body?
C.build_index()
inside = []
outside = []
dtor_bodies = []
for v in ATEXIT_DTORS:
    lo, hi, addrs, blocks = C.extent(v, cap=3000)
    dtor_bodies.append((lo, hi, v))
for e, wl in C.LIVEVT.items():
    for g, vt, slot, s1, s2 in wl:
        hit = any(lo <= s1 < hi for lo, hi, v in dtor_bodies)
        (inside if hit else outside).append((e, g, vt, slot, s1, s2))
print()
print('livevt witnesses total =', len(inside)+len(outside))
print('  install site inside an atexit dtor =', len(inside), ' => not a live vptr (㉓)')
print('  install site elsewhere             =', len(outside))
setin  = {x[0] for x in inside}
setout = {x[0] for x in outside}
print('  entries only reachable via atexit install =', len(setin - setout),
      ['%08X' % x for x in sorted(setin - setout)][:12])
print('  entries still livevt-valid after ㉓       =', len(setout))

OUT = Path(__file__).parent.parent
(OUT/'work'/'atexit.json').write_text(json.dumps(
    dict(atexit=ATEXIT, n_reg=len(reg),
         dtors=sorted('%08X' % v for v in ATEXIT_DTORS),
         bodies=[['%08X' % lo, '%08X' % hi, '%08X' % v] for lo, hi, v in dtor_bodies],
         killed=sorted('%08X' % x for x in setin - setout)), ensure_ascii=False, indent=1),
    encoding='utf-8')
print('wrote atexit.json')
