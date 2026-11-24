#!/usr/bin/env python3
"""R101-T1: answer B/C and controls NC1/NC3.
Rebuilds A-sets and the objdump start pool directly from read-only inputs;
does NOT re-run the expensive capstone linear sweep. Uses r101_core.json only for
the 88 non-elided capstone-only addresses, cap_bad list and their hosts.
"""
import os, json, random, statistics, bisect, re, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import pefile

OUT = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(OUT, 'r101_core.json')))
DIS = '/tmp/r93_disasm.txt'
EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'

def parse_lines():
    ins = {}; starts = []
    with open(DIS, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if not line.startswith('  '):
                continue
            p = line.rstrip('\n').split('\t')
            if len(p) < 3:
                continue
            m = re.match(r'^\s*([0-9a-f]+):$', p[0])
            if not m:
                continue
            a = int(m.group(1), 16)
            ins[a] = (p[1].strip(), p[2].strip())
            starts.append(a)
    return ins, starts

ins, starts = parse_lines()
base = int(D['base'], 16); end = int(D['end'], 16)

pe = pefile.PE(EXE, fast_load=True)
sec = next(s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text')
raw = sec.PointerToRawData
with open(EXE, 'rb') as f:
    f.seek(raw); code = f.read(sec.SizeOfRawData)
secs = [(pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData, s.Name.rstrip(b'\x00').decode('ascii','replace'))
        for s in pe.sections]

# Rebuild A1/A2/A3 exactly as r101_core.py does (text parsing + aligned DWORDs).
jmnem = re.compile(r'^(?:j[a-z]+|call|loop[a-z]*)\b', re.I)
hexlit = re.compile(r'0x([0-9a-f]{4,8})\b', re.I)
jmps = set(); imm = set()
for a, (bs, txt) in ins.items():
    m = jmnem.match(txt)
    for h in hexlit.findall(txt):
        v = int(h, 16)
        if base <= v < end:
            imm.add(v)
            if m: jmps.add(v)
dwords = set()
with open(EXE, 'rb') as f:
    for va, vsize, rawptr, rawsize, name in secs:
        if name == '.text': continue
        n = min(vsize, rawsize) // 4 * 4
        f.seek(rawptr); buf = f.read(n)
        for off in range(0, len(buf), 4):
            v = struct.unpack_from('<I', buf, off)[0]
            if base <= v < end: dwords.add(v)
union_set = jmps | imm | dwords
union_plus1 = set(x + 1 for x in union_set)

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
def cinsn(va):
    if not (base <= va < base + len(code)): return None
    return next(md.disasm(code[va-base:va-base+15], va, count=1), None)

targets = [int(x, 16) for x in D['only_cap_ne_list']]
host_of = {int(k, 16): int(v, 16) for k, v in D['host_of_88'].items()}

classes = {f'B{i}': [] for i in range(1, 6)}
c_split = {'fill': [], 'nofill': []}
detail = []
for a in targets:
    h = host_of[a]
    raw, txt = ins[h]
    hlen = len(raw.replace(' ', '')) // 2
    hend = h + hlen
    hi = cinsn(h)
    if hi is None:
        cl = 'B1'
        ci = cinsn(a)
        (c_split['fill'] if ci is not None and a + ci.size == hend else c_split['nofill']).append(hex(a))
    else:
        p = h; reached = False
        for _ in range(64):
            x = cinsn(p)
            if x is None or not (base <= p < end): break
            p += x.size
            if p == a: reached = True; break
            if p >= hend or not (base <= p < end): break
        if not reached:
            cl = 'B5'
        else:
            ci = cinsn(a); alen = ci.size if ci else None
            if alen is not None and a + alen == hend: cl = 'B2'
            elif p > hend: cl = 'B4'
            else: cl = 'B3'
    classes[cl].append(hex(a))
    detail.append({'a': hex(a), 'host': hex(h), 'host_len': hlen, 'hend': hex(hend),
                   'class': cl, 'cap_host_len': hi.size if hi else None,
                   'cap_at_a_len': (cinsn(a).size if cinsn(a) else None)})

def rand_hits(pool, tset, n=88, reps=200, seed=20261117):
    rnd = random.Random(seed)
    return [sum(x in tset for x in rnd.sample(pool, n)) for _ in range(reps)]

def dist_stats(v):
    return {'median': statistics.median(v), 'min': min(v), 'max': max(v),
            'mean': round(statistics.mean(v), 3)}

S1 = 20261117; S2 = 87654321
rh1 = rand_hits(starts, union_set, seed=S1)
rh1p = rand_hits(starts, union_plus1, seed=S1)
rh2 = rand_hits(starts, union_set, seed=S2)

res = {
    'ref_sizes_rebuilt': {'A1': len(jmps), 'A2': len(imm), 'A3': len(dwords), 'union': len(union_set)},
    'B_classes': {k: len(v) for k, v in classes.items()},
    'B_sum': sum(len(v) for v in classes.values()),
    'B1_split': {k: len(v) for k, v in c_split.items()},
    'same_tiling_total': len(classes['B2']) + len(c_split['fill']),
    'detail': detail,
    'random_union_seed1': dist_stats(rh1),
    'random_union_plus1_seed1': dist_stats(rh1p),
    'random_union_seed2': dist_stats(rh2),
    'seeds': [S1, S2],
    'hit88_union': sum(a in union_set for a in targets),
    'hit88_jmp': sum(a in jmps for a in targets),
    'all_starts_jmp': sum(a in jmps for a in starts),
    'all_starts_jmp_rate': round(sum(a in jmps for a in starts) / len(starts), 6),
    'nc2_capbad_jmp': [hex(a) for a in [int(x,16) for x in D['cap_bad_list']] if a in jmps],
}
json.dump(res, open(os.path.join(OUT, 'r101_bc.json'), 'w'), indent=2)
print(json.dumps({k: v for k, v in res.items() if k != 'detail'}, indent=2))
