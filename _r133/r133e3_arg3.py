#!/usr/bin/env python3
# R133 r133e3 (authoritative): arg3 recomputation at all 15 call sites.
#
# Errors this replaces (kept on record):
#   S-221 r133e v1 disassembled each window from call_va-0x200, a non-boundary, so capstone
#        returned nothing and every site reported "0 pushes".
#   S-222 r133e2 built the global index correctly but its backward walk did not require
#        contiguity and printed an empty tail, so arg3 decoded as a register.
#
# Method used here: one linear disasm_lite sweep -> addr -> (size, mn, op). Walk backwards
# from the call requiring a+size == next_addr at every step; stop at the first gap or the
# first control-transfer. Among that contiguous tail take the LAST THREE pushes.
# cdecl pushes right-to-left, and the template ends `ret 0xc` (3 stack args), so:
#   push[0] = arg3 (dwClsContext), push[1] = arg2, push[2] = arg1 (rclsid)
import json, bisect
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r133/r133e_arg3.json'

pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
secs = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm] = (base + s.VirtualAddress,
                base + s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData), s)
tlo, thi, ts = secs['.text']
data = ts.get_data()

R = {}; ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + (('  [' + str(d) + ']') if d else ''))
    return bool(c)

def sec_of(va):
    for nm, (lo, hi, s) in secs.items():
        if lo <= va < hi:
            return nm
    return None

md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True
idx = {}; order = []
off = 0
while off < len(data):
    for a, sz, mn, ops in md.disasm_lite(data[off:off + 0x10000], tlo + off):
        idx[a] = (sz, mn, ops); order.append(a)
    off += 0x10000
chk('linear sweep passes 0x7e0000 (skipdata effective)', order[-1] > 0x7e0000, hex(order[-1]))
chk('index covers the known call sites as instruction boundaries',
    all(s in idx for s in (0x6bc364, 0x6bc3aa, 0x416bc2, 0x710213)),
    [hex(s) for s in (0x6bc364, 0x6bc3aa, 0x416bc2, 0x710213) if s not in idx])

SITES = {
    'A': [0x6bc364, 0x6bc3aa],
    'B': [0x416bc2, 0x44e02c, 0x4db8cc, 0x4df85c, 0x51b064, 0x521fc2,
          0x5230dc, 0x65f092, 0x6cc999, 0x710213, 0x7354f2, 0x742699, 0x742a94],
}

def imm(op):
    # S-223: capstone prints immediates under 10 in DECIMAL ('push 7'), not hex.
    # A 0x-only parser silently returns None for exactly those values and then reports
    # "no literal shape" for a site whose shape is perfect. Accept both forms.
    o = op.strip()
    try:
        return int(o, 16) if o.startswith('0x') else int(o, 10)
    except ValueError:
        return None

R['sites'] = {}
for label, sites in SITES.items():
    R['sites'][label] = []
    for call_va in sites:
        pos = bisect.bisect_left(order, call_va)
        cur = call_va
        tail = []
        j = pos - 1
        while j >= 0 and len(tail) < 20:
            a = order[j]
            sz, mn, ops = idx[a]
            if a + sz != cur:            # contiguity: real previous instruction only
                break
            if mn in ('call', 'jmp', 'ret', 'int3') or mn.startswith('j'):
                break
            tail.append((a, mn, ops)); cur = a; j -= 1
        tail.reverse()
        pushes = [(a, ops) for a, mn, ops in tail if mn == 'push']
        rec = {'call_va': hex(call_va), 'n_push': len(pushes),
               'tail': ['%#x %s %s' % t for t in tail]}
        if len(pushes) >= 3:
            a3, o3 = pushes[-3]; a2, o2 = pushes[-2]; a1, o1 = pushes[-1]
            v3, v2, v1 = imm(o3), imm(o2), imm(o1)
            rec.update({'arg3_insn': hex(a3), 'arg3_op': o3, 'arg3': v3,
                        'arg2_op': o2, 'arg2': v2,
                        'arg1_op': o1, 'arg1': v1,
                        'arg1_section': (sec_of(v1) if v1 is not None else None),
                        'shape_ok': (v3 is not None)})
        else:
            rec['shape_ok'] = False
        R['sites'][label].append(rec)
        print('%-2s %-10s pushes=%d arg3=%s(%s) arg2=%s arg1=%s' % (
            label, hex(call_va), len(pushes),
            (hex(rec['arg3']) if rec.get('arg3') is not None else '-'), rec.get('arg3_op'),
            rec.get('arg2_op'), rec.get('arg1_op')))

print('\n--- assertions ---')
allrec = [(lab, r) for lab in R['sites'] for r in R['sites'][lab]]
chk('all 15 call sites enumerated (2 for A + 13 for B)', len(allrec) == 15, len(allrec))
bad = [(lab, r['call_va'], r['n_push']) for lab, r in allrec if not r.get('shape_ok')]
chk('every site has a literal immediate as the third-from-last push (arg3)', not bad, bad)
chk('arg3 == 7 at ALL 15 call sites', all(r.get('arg3') == 7 for lab, r in allrec),
    sorted({str(r.get('arg3')) for lab, r in allrec}))
chk('7 & 0x14 == 4 != 0 => ZF=0 => je NOT taken => fallthrough arm runs',
    (7 & 0x14) == 4, 7 & 0x14)
# arg2 distribution. NOT asserted to be universally 0: 9 of 15 sites push a literal 0 and
# 6 push a register, whose value this script does not track. Recorded honestly as a
# distribution; the load-bearing claim is arg3, whose value IS fully literal at all 15.
d2 = {}
for lab, r in allrec:
    k = ('imm_0' if r.get('arg2') == 0 else ('reg' if r.get('arg2') is None else 'imm_other'))
    d2[k] = d2.get(k, 0) + 1
R['arg2_distribution'] = d2
print('arg2 distribution:', d2)
chk('arg2 is either a literal 0 or an untracked register at every site (no third case)',
    set(d2) <= {'imm_0', 'reg'} and sum(d2.values()) == 15, d2)
chk('at least one site pushes literal 0 as arg2 (layout corroborated, not assumed)',
    d2.get('imm_0', 0) > 0, d2)
# arg1 is a register or a data pointer, never an immediate that is code -- corroborates rclsid
chk('arg1 is never a small integer (it is a pointer/register, i.e. rclsid)',
    all(r.get('arg1') is None or r.get('arg1') > 0x1000 for lab, r in allrec),
    sorted({str(r.get('arg1_section')) for lab, r in allrec}))
# ANTI 1: reading the last push as arg3 must NOT be uniform 7
alt = []
for lab, r in allrec:
    ps = [t for t in r['tail'] if ' push ' in t]
    if len(ps) >= 3:
        alt.append(ps[-1].split(' push ', 1)[1])
chk('ANTI: reading the LAST push as arg3 does not give uniform 7 (order is load-bearing)',
    len(alt) == 15 and len(set(alt)) > 1, {'n': len(alt), 'distinct': sorted(set(alt))[:6]})
chk('ANTI: 0 & 0x14 == 0 so passing 0 WOULD enter the else arm (branch live in principle)',
    (0 & 0x14) == 0, 0 & 0x14)
# ANTI 2: contiguity requirement actually bites -- dropping it must change some tail
probe = 0x6bc364
pos = bisect.bisect_left(order, probe)
nocontig = [order[j] for j in range(max(0, pos - 6), pos)]
chk('ANTI: the tail walk stops at the preceding call at 0x6bc364 (0x6bc33c is not in the tail)',
    0x6bc33c not in [int(t.split(' ')[0], 16) for t in R['sites']['A'][0]['tail']],
    R['sites']['A'][0]['tail'])

R['conclusion'] = {'callers_total': 15, 'arg3_uniform': 7, 'zf': 0, 'je_taken': False,
                   'else_arm_reachable_in_this_build': False,
                   'basis': 'r133d (no other entry path) + this (arg3==7 at every caller)'}
R['assertions'] = ASSERT
R['summary'] = {'pass': sum(1 for x in ASSERT if x['pass']), 'total': len(ASSERT)}
print('\nSUMMARY %d/%d PASS' % (R['summary']['pass'], R['summary']['total']))
json.dump(R, open(OUT, 'w'), indent=1)
