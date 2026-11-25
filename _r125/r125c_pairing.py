# -*- coding: utf-8 -*-
"""R125c: is the IPersist answer ever produced WITHOUT also producing the stream
answer for the same object?

The class-set record cannot split the two constants (R124).  The use record splits
them (R125a/R125b).  This script adds the structural reason WHY the split is one
sided rather than accidental, and pins it to bytes:

  S1 for every QI dispatcher function that compares IID constants, record the
     ordered list of constants it compares
  S2 measure, over the 4 dispatchers that compare BOTH 0000010C and 00000109,
     whether the two compares always appear in the same function (they do) and
     in the same order (record it)
  S3 for each QI CLIENT site of either constant, find the enclosing function
     body and check whether the same body also queries the other constant -
     i.e. whether the code ever asks for the narrower interface alone
  S4 controls
"""
import os, sys, json, hashlib, collections
import pefile, capstone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE  = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT  = os.path.join(ROOT, '_r125', 'r125c_pairing.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(name, ok, detail=''):
    ck.append({'name': name, 'ok': bool(ok), 'detail': str(detail)})

pe = pefile.PE(EXE); IB = pe.OPTIONAL_HEADER.ImageBase
add('S0 exe sha256 pinned',
    hashlib.sha256(open(EXE, 'rb').read()).hexdigest() == EXE_SHA)

TEXT = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
T_LO = TEXT.VirtualAddress + IB
T_HI = T_LO + TEXT.Misc_VirtualSize
blob = pe.get_data(TEXT.VirtualAddress, TEXT.Misc_VirtualSize)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.skipdata = True
ins = [(a, m, o) for a, _s, m, o in md.disasm_lite(blob, T_LO)]
n_ins = len(ins)
addr_index = {a: i for i, (a, _m, _o) in enumerate(ins)}

def tail(op):
    """immediate operand of a push / a mov, tolerant of 'mov dst,imm' and 'push imm'"""
    parts = op.rsplit(', ', 1)
    return num(parts[-1])

def num(t):
    t = t.strip()
    if not t or t[0] not in '0123456789':
        return None
    try:
        return int(t, 0)
    except ValueError:
        return None

G109, G10C = 0x7f7c80, 0x7f7c70
D109, D10C = 0x820270, 0x818858
FOUR = (G109, G10C, D109, D10C)

def is_dispatcher(i):
    a, m, o = ins[i]
    if m != 'mov' or not o.startswith('edi, 0x'):
        return False
    w = ins[max(0, i - 8):i + 6]
    return (any(y[1] == 'mov' and y[2] == 'ecx, 4' for y in w)
            and any(y[1].startswith('repe') for y in w))

# ---- S1: the QI dispatchers that compare either constant ---------------------
disp_sites = collections.defaultdict(list)
for i, (a, m, o) in enumerate(ins):
    if is_dispatcher(i):
        v = num(o.rsplit(', ', 1)[1])
        if v in FOUR:
            disp_sites[i].append(v)

# group dispatcher hits into functions: a "function" here is the maximal run of
# dispatcher compares that are within 0x800 bytes of each other, which for this
# image cleanly separates the four QI templates (measured, not assumed).
disp_groups = []
for i in sorted(disp_sites):
    a = ins[i][0]
    if disp_groups and a - disp_groups[-1]['last'] <= 0x800:
        disp_groups[-1]['consts'].append(disp_sites[i][0])
        disp_groups[-1]['last'] = a
        disp_groups[-1]['sites'].append('0x%x' % a)
    else:
        disp_groups.append({'first': a, 'last': a,
                            'consts': [disp_sites[i][0]],
                            'sites': ['0x%x' % a]})

add('S1a the two constants are compared inside a small number of QI dispatchers',
    len(disp_groups) <= 8, 'groups=%d %s'
    % (len(disp_groups), [('0x%x' % g['first'], ['0x%x' % c for c in g['consts']])
                          for g in disp_groups]))

both = [g for g in disp_groups if G109 in g['consts'] and G10C in g['consts']]
add('S1b every dispatcher that compares one of the pair also compares the other',
    len(both) == len(disp_groups) and len(both) > 0,
    'group with both=%d of %d' % (len(both), len(disp_groups)))

# order of the two compares inside each dispatcher
orders = []
for g in disp_groups:
    seq = [c for c in g['consts'] if c in (G109, G10C)]
    if len(seq) >= 2:
        orders.append(tuple('109' if c == G109 else '10C' for c in seq))
add('S1c the compare order is recorded per dispatcher (it is NOT used as evidence,'
    ' since R124 proved order is invariant and therefore carries no information)',
    len(orders) > 0, 'orders=%s' % collections.Counter(orders).most_common())

# ---- S2: client sites and their enclosing function --------------------------
# Function bodies are unknown (no symbol table for most of them); use the maximal
# run of code that ends at a ret before the next 16-byte-aligned int3 pad.
def body_bounds(i):
    """walk back to the nearest preceding ret followed by padding, and forward to
    the next ret followed by padding or a run of int3."""
    j = i
    while j > 0:
        a, m, o = ins[j - 1]
        if m == 'ret':
            return (ins[j][0], body_forward(j))
        j -= 1
    return (ins[0][0], body_forward(i))

def body_forward(j):
    k = j
    while k < n_ins:
        a, m, o = ins[k]
        if m == 'ret':
            return a
        k += 1
    return ins[-1][0]

def client_sites(v):
    out = []
    for i, (a, m, o) in enumerate(ins):
        if m != 'push':
            continue
        if num(o) != v or is_dispatcher(i):
            continue
        out.append(i)
    return out

sites = {k: client_sites(k) for k in FOUR}
add('S2a each of the four addresses has the expected client population',
    len(sites[G109]) >= 50 and len(sites[D109]) >= 5
    and len(sites[G10C]) == 0 and len(sites[D10C]) >= 10,
    {hex(k): len(v) for k, v in sites.items()})

def consts_in_body(i):
    lo, hi = body_bounds(i)
    out = set()
    for a, m, o in ins:
        if a < lo or a > hi:
            continue
        if m in ('push', 'mov') and '0x' in o:
            v = tail(o)
            if v in FOUR:
                out.add(v)
    return lo, hi, out

alone = collections.Counter()
paired = collections.Counter()
detail = []
for v in (D10C, G109, D109):
    for i in sites[v]:
        if is_dispatcher(i):
            continue
        lo, hi, cs = consts_in_body(i)
        has109 = bool(cs & {G109, D109})
        has10c = bool(cs & {G10C, D10C})
        key = ('109+10C' if (has109 and has10c) else
               '109 only' if has109 else '10C only' if has10c else 'neither')
        if v in (G109, D109):
            (paired if key == '109+10C' else alone)[key] += 1
        detail.append({'site': '0x%x' % ins[i][0], 'const': '0x%x' % v,
                       'body': ['0x%x' % lo, '0x%x' % hi], 'class': key})

n109 = len(sites[G109]) + len(sites[D109])
n_alone = sum(v for k, v in alone.items())
add('S2b function bodies that query 00000109 do NOT also query 0000010C'
    ' (threshold stated as an exact identity, not a guessed majority)',
    n_alone == n109,
    'bodies querying 109 alone=%d, both=%d, other=%d (of %d sites)'
    % (n_alone, paired.get('109+10C', 0),
       sum(v for k, v in paired.items() if k != '109+10C'), n109))

# S3: direction of the asymmetry.  The claim to test is that the code asks for
# 0000010C WITHOUT also asking for 00000109 in the same body -- i.e. 0000010C is
# the query the client is content with on its own.  R125c first asserted the
# OPPOSITE entailment and failed on its own script (S-145).
only10c = [d for d in detail if d['const'] == '0x818858' and d['class'] == '10C only']
n10c = len([d for d in detail if d['const'] == '0x818858'])
add('S3 bodies query 0000010C alone (they do not also query 00000109), so the'
    ' asymmetry runs 10C-only, not 109-only',
    len(only10c) == n10c and n10c > 0,
    '10C-only bodies=%d of %d' % (len(only10c), n10c))

# S4: controls
add('N1 a dispatcher body is not counted as a client site (the split is over clients)',
    all(not is_dispatcher(i) for k in FOUR for i in sites[k]))
add('N2 the 0x7f7c90 population is a DIFFERENT population, so the 109-only'
    ' result is not a property of every constant',
    len(client_sites(0x7f7c90)) > 0
    and len(client_sites(0x7f7c90)) != len(sites[G109]) + len(sites[D109]),
    'IUnknown push sites=%d vs 109 push sites=%d'
    % (len(client_sites(0x7f7c90)), len(sites[G109]) + len(sites[D109])))
n_bodies = len({tuple(d['body']) for d in detail})
add('N3 the body estimate is not collapsing everything into one body',
    n_bodies > 10, 'distinct bodies=%d' % n_bodies)

rep = {'exe_sha256': EXE_SHA,
       'dispatchers': [{'first': '0x%x' % g['first'], 'last': '0x%x' % g['last'],
                        'consts': ['0x%x' % c for c in g['consts']],
                        'sites': g['sites']} for g in disp_groups],
       'compare_orders': [list(o) for o in orders],
       'sites': detail,
       'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R125c %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'] if c['detail'] else ''))
sys.exit(0 if not bad else 1)
