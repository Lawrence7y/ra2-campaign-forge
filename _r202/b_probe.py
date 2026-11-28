#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202-B probe: one-shot dump of every fact needed for the final b_nonehost.py."""
import sys, struct, bisect, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW
def in_text(x): return x is not None and LO <= x < HI
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n-4):
        if w[i] not in (0, 1, 2) or w[i+2] != 0: continue
        if P.where(w[i+3]) != '.data' or P.where(w[i+4]) != '.rdata': continue
        nm = P.cstr(w[i+3]+8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i] = dict(mdisp=s32(w[i+1]), name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i] = P.dw(base+4*i-4)
MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}
CLS = {vt: COL[VT[vt]]['name'] for vt in VT}
REGNAME = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
recs = []; pos = T['rawptr']; end = T['rawptr'] + T['rawsize']
while pos < end-6:
    if RAW[pos] != 0xC7: pos += 1; continue
    modrm = RAW[pos+1]; mod = modrm >> 6; reg = (modrm >> 3) & 7; rm = modrm & 7
    if reg != 0 or rm == 4 or (rm == 5 and mod == 0): pos += 1; continue
    va = LO + (pos - T['rawptr'])
    if mod == 1:
        d = struct.unpack_from('<b', RAW, pos+2)[0]; im = struct.unpack_from('<I', RAW, pos+3)[0]
        recs.append((va, REGNAME[rm], d, im)); pos += 7
    elif mod == 2:
        d = struct.unpack_from('<i', RAW, pos+2)[0]; im = struct.unpack_from('<I', RAW, pos+6)[0]
        recs.append((va, REGNAME[rm], d, im)); pos += 10
    else: pos += 1
sub = [r for r in recs if 1 <= r[2] <= 9 and r[3] in VT]
BUF = RAW[T['rawptr']:T['rawptr'] + (HI-LO)]
INS = []; CALLAT = []; p2 = 0
while p2 < len(BUF):
    got = False
    for off, sz, mn, op in md.disasm_lite(BUF[p2:p2+65536], LO+p2):
        got = True; INS.append((off, sz, mn, op))
        if mn == 'call' and op.startswith('0x'):
            t = int(op, 16)
            if in_text(t): CALLAT.append((off, t))
        p2 += sz
    if not got: p2 += 1
INS.sort(); ADDRS = [a for a, _, _, _ in INS]
REGION = []; st = LO
for a, sz, mn, op in INS:
    if mn.startswith('ret') or mn == 'int3':
        REGION.append((st, a+sz)); st = a+sz
if st < HI: REGION.append((st, HI))
RL = [r[0] for r in REGION]
def reg_of(va):
    i = bisect.bisect_right(RL, va)-1
    return REGION[i] if i >= 0 else None
SORT = sorted(set(t for _, t in CALLAT))
def host_of(c):
    i = bisect.bisect_left(SORT, c)-1
    return SORT[i] if i >= 0 else None
allsite = []; pos = T['rawptr']
while pos < end-4:
    if RAW[pos] == 0x66:
        if pos+2 < end and RAW[pos+1] == 0xC7:
            mo = RAW[pos+2] >> 6; pos += 6 if mo == 0 else (7 if mo == 1 else 11); continue
        pos += 1; continue
    if RAW[pos] != 0xC7: pos += 1; continue
    modrm = RAW[pos+1]; mod = modrm >> 6; reg = (modrm >> 3) & 7; rm = modrm & 7
    if reg != 0 or rm == 4 or (rm == 5 and mod == 0): pos += 1; continue
    va = LO + (pos - T['rawptr'])
    if mod == 1:
        d = struct.unpack_from('<b', RAW, pos+2)[0]; im = struct.unpack_from('<I', RAW, pos+3)[0]; allsite.append((va, REGNAME[rm], d, im)); pos += 7
    elif mod == 2:
        d = struct.unpack_from('<i', RAW, pos+2)[0]; im = struct.unpack_from('<I', RAW, pos+6)[0]; allsite.append((va, REGNAME[rm], d, im)); pos += 10
    else:
        im = struct.unpack_from('<I', RAW, pos+2)[0]; allsite.append((va, REGNAME[rm], 0, im)); pos += 6
vts = [r for r in allsite if r[3] in VT]
byreg = collections.defaultdict(list)
for r in vts: byreg[reg_of(r[0])].append(r)
def fm(r): return '%s d=%d imm=%s md=%d %s' % (hex(r[0]), r[2], hex(r[3]), MD[r[3]], CLS[r[3]])
print('COUNTS sub=%d vts=%d regions=%d COL=%d VT=%d' % (len(sub), len(vts), len(REGION), len(COL), len(VT)))
NONE = [0x5d5b80, 0x635f34, 0x637114, 0x638aa4, 0x6cf196, 0x6cf209, 0x7b1b2b, 0x7b27fb]
for target in NONE:
    r = next(x for x in sub if x[0] == target)
    reg = reg_of(target)
    print('\n=== NONE %s cls=%s md=%d base=%s region=%s..%s' % (hex(target), CLS[r[3]], MD[r[3]], r[1], hex(reg[0]), hex(reg[1])))
    for s in sorted(byreg[reg]): print('   VTS ' + fm(s))
    # call sites targeting region start
    cs = [c for c, t in CALLAT if t == reg[0]]
    print('   CALLAT->start count=%d %s' % (len(cs), [hex(x) for x in cs[:10]]))
    for c in cs[:3]:
        i0 = bisect.bisect_right(ADDRS, c)-1
        for a, sz, mn, op in INS[max(0, i0-8):i0+1]:
            print('     callctx %s %s %s' % (hex(a), mn, op))
    # other mov [base+K] field stores in region
    i0 = bisect.bisect_left(ADDRS, reg[0]); i1 = bisect.bisect_left(ADDRS, reg[1])
    nfield = 0
    for a, sz, mn, op in INS[i0:i1]:
        if mn == 'mov' and op.startswith('dword ptr [%s' % r[1]):
            print('     FIELD %s %s %s' % (hex(a), mn, op)); nfield += 1
            if nfield >= 12: break
NOTICE = [0x410174, 0x4101c2, 0x6e8008]
for target in NOTICE:
    reg = reg_of(target)
    print('\n=== NOTICE %s region=%s..%s' % (hex(target), hex(reg[0]), hex(reg[1])))
    for s in sorted(byreg[reg]): print('   VTS ' + fm(s))
    nsub = sum(1 for s in byreg[reg] if 'INoticeSink' in CLS[s[3]] and MD[s[3]] != 0)
    nall = sum(1 for s in byreg[reg] if 'INoticeSink' in CLS[s[3]])
    print('   INotice in region: all=%d sub=%d main=%d' % (nall, nsub, nall-nsub))
    # prologue
    i0 = bisect.bisect_left(ADDRS, reg[0])
    for a, sz, mn, op in INS[i0:i0+28]: print('     PRO %s %s %s' % (hex(a), mn, op))
    # window around store
    st = bisect.bisect_right(ADDRS, target-40)-1
    for a, sz, mn, op in INS[st:bisect.bisect_left(ADDRS, target+41)]:
        print('     WIN %s %s %s%s' % (hex(a), mn, op, '  <<<< STORE' if a == target else ''))
# positive-control classes
for cn in ('.?AVAirstrikeClass@@', '.?AVAlphaShapeClass@@', '.?AVBombClass@@'):
    sites = [r for r in vts if MD[r[3]] == 0 and CLS[r[3]] == cn]
    print('CTRL %s n=%d regions=%d sites=%s' % (cn, len(sites), len(set(reg_of(r[0]) for r in sites)), [hex(r[0]) for r in sites]))
