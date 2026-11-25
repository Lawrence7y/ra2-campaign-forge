#!/usr/bin/env python3
# R132 r132e: verify the branch polarity of the template's two paths.
#
# R131 wrote: "dwClsContext 15/15 都是 7，7&0x14=4!=0 故 je 不跳、CoCreateInstance 确实被调，
#              OleRun 分支 15/15 处均为死分支"
#
# Those two clauses contradict each other. If je is NOT taken, control FALLS THROUGH into
# the if-path, and the if-path is the one that calls OleRun (at +0x3c). So the if-path
# (with OleRun) is LIVE and the ELSE block is dead -- the opposite of what was written.
#
# This script proves the polarity mechanically rather than by reading prose:
#   x86 `test al, imm8` sets ZF=1 iff (al & imm8)==0 ; `je` jumps iff ZF=1.
# So: jump-to-else happens iff (arg & 0x14)==0.
# We then walk the CFG both ways and report which basic blocks are reachable for arg=7.
import json, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r132/r132e_polarity.json'

pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
secs = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm] = (base + s.VirtualAddress,
                base + s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData), s)
tlo, thi, ts = secs['.text']
data = ts.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_32)

R = {}

def dec(va, n=1):
    out = []
    for i in md.disasm(data[va - tlo:va - tlo + 16 * n], va):
        out.append(i)
        if len(out) >= n:
            break
    return out

# ---------------- 1. the ZF rule, stated as arithmetic and tested -----------------
R['zf_rule'] = []
for arg in (0, 1, 2, 4, 5, 7, 0x13, 0x14, 0x15, 0xff):
    taken = (arg & 0x14) == 0
    R['zf_rule'].append({'arg': arg, 'al_and_0x14': arg & 0x14, 'je_taken_to_else': taken})
print('arg  arg&0x14  je->else')
for r in R['zf_rule']:
    print('%3d  0x%02x      %s' % (r['arg'], r['al_and_0x14'], r['je_taken_to_else']))

# ---------------- 2. locate the test/je in each instance -------------------------
INST = {}
for label, entry, ln in (('A', 0x6bedb0, 136), ('B', 0x41c250, 136)):
    ins = list(md.disasm(data[entry - tlo:entry - tlo + ln], entry))
    test_i = je_i = None
    for i in ins:
        if i.mnemonic == 'test' and i.op_str.replace(' ', '') == 'al,0x14':
            test_i = i
        elif i.mnemonic == 'je' and test_i is not None:
            je_i = i
            break
    d = {'entry': hex(entry),
         'test_at': hex(test_i.address) if test_i else None,
         'je_at': hex(je_i.address) if je_i else None,
         'je_target': je_i.op_str if je_i else None,
         'fallthrough_va': hex(je_i.address + je_i.size) if je_i else None}
    INST[label] = d
    print('[%s] test %s ; je %s -> %s ; fallthrough %s'
          % (label, d['test_at'], d['je_at'], d['je_target'], d['fallthrough_va']))
R['instances'] = INST

# ---------------- 3. which named API lives in which arm --------------------------
# walk fallthrough arm and the je-target arm, note CoCreateInstance / OleRun presence
def arm_report(start, stop_at_ret=True, limit=80):
    found = []
    seen = set()
    work = [start]
    while work and len(found) < limit:
        va = work.pop()
        if va in seen:
            continue
        seen.add(va)
        i = dec(va, 1)
        if not i:
            continue
        i = i[0]
        if i.mnemonic == 'call':
            if '0x7e15fc' in i.op_str:
                found.append(('CoCreateInstance', hex(i.address)))
            elif '0x7e1600' in i.op_str:
                found.append(('OleRun', hex(i.address)))
        if i.mnemonic == 'ret':
            continue
        if i.mnemonic in ('je', 'jl', 'jne', 'jmp', 'jg', 'jle'):
            try:
                work.append(int(i.op_str, 16))
            except ValueError:
                pass
        work.append(va + i.size)
    return found

for label, entry in (('A', 0x6bedb0), ('B', 0x41c250)):
    ft = INST[label]['fallthrough_va']
    tg = INST[label]['je_target']
    fa = arm_report(int(ft, 16))
    ga = arm_report(int(tg, 16))
    R['instances'][label]['fallthrough_arm_calls'] = fa
    R['instances'][label]['je_target_arm_calls'] = ga
    print('[%s] fallthrough arm calls: %s' % (label, fa))
    print('[%s] je-target (else) arm calls: %s' % (label, ga))

# ---------------- 4. the 15 wrapper callers: what dwClsContext do they pass? ------
def callers(target):
    out = []
    i = 0
    while True:
        i = data.find(b'\xe8', i)
        if i < 0 or i + 5 > len(data):
            break
        rel = struct.unpack('<i', data[i + 1:i + 5])[0]
        if tlo + i + 5 + rel == target:
            out.append(tlo + i)
        i += 1
    return out

# build a linear instruction map (lite) for backward walking
mdl = Cs(CS_ARCH_X86, CS_MODE_32)
mdl.skipdata = True
insn = {}
off = 0
while off < len(data):
    for a, sz, mn, ops in mdl.disasm_lite(data[off:off + 0x10000], tlo + off):
        insn[a] = (sz, mn, ops)
    off += 0x10000

def prev_pushes(site, k=6):
    out = []
    va = site
    for _ in range(k):
        cand = None
        for b in range(1, 16):
            if (va - b) in insn:
                cand = va - b
                break
        if cand is None:
            break
        if insn[cand][1] == 'push':
            out.append((cand, insn[cand][2]))
        va = cand
    out.reverse()
    return out

R['wrapper_callers'] = {}
allargs = []
for label, entry in (('A', 0x6bedb0), ('B', 0x41c250)):
    cs = callers(entry)
    R['wrapper_callers'][label] = []
    for c in cs:
        ps = prev_pushes(c, 6)
        last3 = ps[-3:]
        R['wrapper_callers'][label].append(
            {'call': hex(c), 'pushes': [{'at': hex(a), 'op': o} for a, o in last3]})
        allargs.append((label, hex(c), [o for _, o in last3]))
    print('[%s] %d callers' % (label, len(cs)))
    for e in R['wrapper_callers'][label]:
        print('    %s  pushes: %s' % (e['call'], [p['op'] for p in e['pushes']]))

# arg3 = dwClsContext is the LAST push before the call (rightmost arg, pushed last)
R['arg3_values'] = []
for label, c, ops in allargs:
    v = ops[-1] if ops else None
    R['arg3_values'].append({'instance': label, 'call': c, 'arg3': v})
print()
print('arg3 (dwClsContext) passed by each wrapper caller:')
from collections import Counter
cnt = Counter(x['arg3'] for x in R['arg3_values'])
for x in R['arg3_values']:
    print('   %s %s -> %s' % (x['instance'], x['call'], x['arg3']))
print('distribution:', dict(cnt))
R['arg3_distribution'] = dict(cnt)

ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + ((' [%s]' % d) if d else ''))
zf = {r['arg']: r['je_taken_to_else'] for r in R['zf_rule']}
chk('arg=0 takes the else arm', zf[0] is True)
chk('arg=7 does not take the else arm', zf[7] is False)
chk('arg=1 takes the else arm (bit2 clear)', zf[1] is True)
chk('arg=4 does not (bit2 set)', zf[4] is False)
for lbl in ('A','B'):
    d = R['instances'][lbl]
    names_ft = [n for n,_ in d['fallthrough_arm_calls']]
    names_tg = [n for n,_ in d['je_target_arm_calls']]
    chk('%s fallthrough arm calls OleRun' % lbl, 'OleRun' in names_ft, names_ft)
    chk('%s je-target arm does not call OleRun' % lbl, 'OleRun' not in names_tg, names_tg)
chk('15 wrapper callers total',
    sum(len(v) for v in R['wrapper_callers'].values()) == 15,
    sum(len(v) for v in R['wrapper_callers'].values()))
json.dump(ASSERT, open(OUT.replace('.json','_assert.json'),'w'), ensure_ascii=False, indent=1)
print('assertions:', len(ASSERT), 'FAIL', sum(1 for a in ASSERT if not a['pass']))
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('wrote', OUT)
