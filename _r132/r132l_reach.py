#!/usr/bin/env python3
# R132 r132l: the precise reachability statement, and the R131 contradiction made explicit.
#
# R131 (R14_COMMON 2.135 §5, LEDGER §1185, LEAD_LOCK KQ) states two things that cannot
# both be true:
#   (i)  "7 & 0x14 = 4 != 0 => je 不跳"                      (je not taken)
#   (ii) "OleRun 分支 15/15 处均为死分支"                     (OleRun branch dead)
# If je is not taken, control falls through; OleRun is in the fallthrough arm; therefore
# OleRun is on the live path. This script measures which sentence the bytes support.
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r132/r132l_reach.json'

pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
for s in pe.sections:
    if s.Name.rstrip(b'\x00') == b'.text':
        tlo = base + s.VirtualAddress
        data = s.get_data()
        break
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True

insn = {}
off = 0
while off < len(data):
    for a, sz, mn, ops in md.disasm_lite(data[off:off + 0x10000], tlo + off):
        insn[a] = (sz, mn, ops)
    off += 0x10000

ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + ((' [' + str(d) + ']') if d else ''))

def walk(start):
    """return set of addresses reachable from start (inclusive), following fallthrough
    and both edges of conditional branches (over-approximation = union of arms)."""
    seen = set(); work = [start]; addrs = []
    while work and len(addrs) < 2000:
        va = work.pop()
        if va in seen or va not in insn:
            continue
        seen.add(va); addrs.append(va)
        sz, mn, ops = insn[va]
        if mn == 'ret':
            continue
        if mn in ('je','jne','jl','jle','jg','jge','jmp'):
            try: work.append(int(ops, 16))
            except ValueError: pass
        work.append(va + sz)
    return set(addrs)

def walk_constrained(start, zf_zero):
    """walk with the je at the arm split resolved: zf_zero=True => je NOT taken."""
    seen = set(); work = [start]; addrs = []
    while work and len(addrs) < 2000:
        va = work.pop()
        if va in seen or va not in insn:
            continue
        seen.add(va); addrs.append(va)
        sz, mn, ops = insn[va]
        if mn == 'ret':
            continue
        if mn == 'je':
            tgt = int(ops, 16)
            if zf_zero:
                work.append(va + sz)          # not taken
            else:
                work.append(tgt)              # taken
            continue
        if mn in ('jne','jl','jle','jg','jge','jmp'):
            try: work.append(int(ops, 16))
            except ValueError: pass
        work.append(va + sz)
    return set(addrs)

R = {'instances': {}}
for label, entry, oler, ccis_if, ccis_else in (
        ('A', 0x6bedb0, 0x6bedec, 0x6beddd, 0x6bee2b),
        ('B', 0x41c250, 0x41c28c, 0x41c27d, 0x41c2cb)):
    allr = walk(entry)
    live = walk_constrained(entry, zf_zero=True)     # arg3=7 => ZF=0 => je not taken
    dead = walk_constrained(entry, zf_zero=False)    # hypothetical arg3 whose bit2 is clear
    R['instances'][label] = {
        'entry': hex(entry),
        'olerun_site': hex(oler),
        'ccis_if_arm': hex(ccis_if),
        'ccis_else_arm': hex(ccis_else),
        'olerun_in_live_arm_zf0': oler in live,
        'olerun_in_dead_arm_zf0': oler in dead,
        'ccis_if_in_live': ccis_if in live,
        'ccis_else_in_live': ccis_else in live,
        'live_arm_size': len(live), 'dead_arm_size': len(dead),
    }
    d = R['instances'][label]
    print('[%s] live(zf=0) contains OleRun=%s CoCreateInstance(if)=%s CoCreateInstance(else)=%s'
          % (label, d['olerun_in_live_arm_zf0'], d['ccis_if_in_live'], d['ccis_else_in_live']))
    print('[%s] hypothetical zf=1 arm contains OleRun=%s' % (label, d['olerun_in_dead_arm_zf0']))

for label in ('A', 'B'):
    d = R['instances'][label]
    chk('%s with arg3=7 (ZF=0) the fallthrough arm is live' % label, d['ccis_if_in_live'])
    chk('%s OleRun lies on the LIVE path (je not taken)' % label, d['olerun_in_live_arm_zf0'])
    chk('%s the je-target CoCreateInstance is NOT on the live path' % label,
        not d['ccis_else_in_live'])
    chk('%s control: had ZF been 1 the OleRun would NOT run (arm really is conditional)' % label,
        not d['olerun_in_dead_arm_zf0'])

# the contradiction, stated as data
R['R131_contradiction'] = {
    'sentence_1': '7 & 0x14 = 4 != 0 => je not taken  [arithmetic: CORRECT]',
    'sentence_2': 'OleRun branch is dead at 15/15 sites  [measurement: INVERTED]',
    'why': 'je not taken means the fallthrough arm executes; OleRun is at +0x3c inside '
           'that fallthrough arm; the unreachable arm is the je-target (the second '
           'CoCreateInstance without OleRun).',
    'consequence': 'OleRun is reached at every wrapper invocation where CoCreateInstance '
                   'succeeds (the jl at +0x46 skips it only on failure).',
}
print()
print(json.dumps(R['R131_contradiction'], ensure_ascii=False, indent=1))

json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
json.dump(ASSERT, open(OUT.replace('.json', '_assert.json'), 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for a in ASSERT if not a['pass'])
print()
print('== assertions: %d total, %d FAIL ==' % (len(ASSERT), nf))
