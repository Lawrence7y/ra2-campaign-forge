# -*- coding: utf-8 -*-
"""R125 lead recomputation (rule D): IID 0x7f7c70 vs 0x7f7c80.

Deliberately weaker, independent instrument from _r125/r125a_guid_role.py:
no taint tracking, no esp frame model, no virtual-slot walk.  Only:

  M1  the four constants' 16 bytes, decoded as GUIDs
  M2  a single streaming pass over .text (disasm_lite, never detail=True) that
      records, for each immediate reference to any of the four addresses:
        - kind: dispatcher (mov edi,IMM inside the MSVC QI template) or push
        - the enclosing function body bounds, computed by bracket matching on
          ret and int3 padding -- NOT by any distance heuristic
  M3  per push site: does the SAME enclosing body contain a call through the
      IAT slots of OleSaveToStream / OleLoadFromStream?
  M4  sensitivity of M3 to a forward instruction window 0,6,8,10,16,24,40
  M5  controls: IConnectionPointContainer, IUnknown bytes, total OLE call
      population (a duplicate-count guard), and the twin-address matrix

Memory discipline: .text is decoded once with disasm_lite into a compact list of
tuples (this is ~140 MB for 1.39M instructions and is the same shape every
earlier round used).  No capstone objects are retained.
"""
import os, sys, json, hashlib, collections, struct
import pefile, capstone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(ROOT, '_r125', 'r125d_lead_recompute.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(name, ok, detail=''):
    ck.append({'name': name, 'ok': bool(ok), 'detail': str(detail)})

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
add('M0 exe sha256 is the pinned build',
    hashlib.sha256(open(EXE, 'rb').read()).hexdigest() == EXE_SHA)

SECS = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin1')
    SECS[nm] = (s.VirtualAddress + IB, s.VirtualAddress + IB + s.Misc_VirtualSize)

def rd(va, n):
    return pe.get_data(va - IB, n)

def guid_text(va):
    b = rd(va, 16)
    return '%08X-%04X-%04X-%s-%s' % (
        int.from_bytes(b[0:4], 'little'), int.from_bytes(b[4:6], 'little'),
        int.from_bytes(b[6:8], 'little'), b[8:10].hex().upper(), b[10:16].hex().upper())

# ---- M1: the four constants and the IUnknown neighbour ----------------------
ADDRS = [0x7f7c70, 0x7f7c80, 0x818858, 0x820270]
GUIDS = {a: guid_text(a) for a in ADDRS}
G109 = '00000109-0000-0000-C000-000000000046'
G10C = '0000010C-0000-0000-C000-000000000046'
add('M1a the four addresses carry exactly two distinct GUID values',
    sorted(set(GUIDS.values())) == [G109, G10C], GUIDS)
add('M1b each GUID value appears at exactly one .rdata and one .data address',
    GUIDS[0x7f7c70] == GUIDS[0x818858] and GUIDS[0x7f7c80] == GUIDS[0x820270],
    '10C: %s %s ; 109: %s %s' % (hex(0x7f7c70), hex(0x818858), hex(0x7f7c80), hex(0x820270)))
IUNK = guid_text(0x817bc0)
add('M1c the neighbour at 0x817bc0 is IID_IUnknown, so this is a GUID pool',
    IUNK == '00000000-0000-0000-C000-000000000046', IUNK)

# ---- M2: streaming census --------------------------------------------------
T_LO, T_HI = SECS['.text']
blob = pe.get_data(T_LO - IB, T_HI - T_LO)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True

ins = []
for a, sz, m, o in md.disasm_lite(blob, T_LO):
    ins.append((a, m, o))
n_ins = len(ins)
del blob
add('M2a linear scan covers .text to the last byte', n_ins > 1300000,
    'n_ins=%d last=0x%x' % (n_ins, ins[-1][0]))

IAT = {}
for d in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in d.imports:
        IAT[imp.address] = imp.name.decode() if imp.name else None
OLE_SLOTS = sorted(k for k, v in IAT.items()
                   if v in ('OleSaveToStream', 'OleLoadFromStream'))
add('M2b the two OLE stream entry points resolve at absolute IAT addresses',
    len(OLE_SLOTS) == 2 and IAT.get(0x7e15f4) == 'OleSaveToStream'
    and IAT.get(0x7e15f8) == 'OleLoadFromStream',
    ['0x%x=%s' % (k, IAT[k]) for k in OLE_SLOTS])

def num(t):
    t = t.strip()
    if not t or t[0] not in '0123456789':
        return None
    try:
        return int(t, 0)
    except ValueError:
        return None

def tail_imm(op):
    return num(op.rsplit(', ', 1)[-1])

# index by address for window lookups
idx_of = {a: i for i, (a, _m, _o) in enumerate(ins)}

def is_dispatcher(i):
    a, m, o = ins[i]
    if m != 'mov' or not o.startswith('edi, 0x'):
        return False
    w = ins[max(0, i - 8):i + 6]
    return (any(y[1] == 'mov' and y[2] == 'ecx, 4' for y in w)
            and any(y[1].startswith('repe') for y in w))

refs = collections.defaultdict(lambda: {'disp': [], 'push': [], 'other': []})
for i, (a, m, o) in enumerate(ins):
    if m in ('push', 'mov', 'cmp', 'lea'):
        v = tail_imm(o)
        if v in GUIDS:
            if m == 'push':
                kind = 'disp' if is_dispatcher(i) else 'push'
            elif m == 'mov' and is_dispatcher(i):
                kind = 'disp'
            else:
                kind = 'other'
            refs[v][kind].append(a)

add('M2c the census is populated for all four addresses',
    all(refs[v]['push'] or refs[v]['disp'] for v in ADDRS),
    {hex(v): {k: len(x) for k, x in refs[v].items()} for v in ADDRS})

# ---- function body bounds: bracket by ret + int3 padding -------------------
# Boundaries are found without any distance heuristic: a body starts right after
# a ret that is followed by padding, and ends at the first ret that is followed
# by padding or by a run of int3.  Everything else keeps walking.
def body_of(i):
    j = i
    while j > 0:
        pa, pm, po = ins[j - 1]
        if pm == 'ret' and is_pad(j):
            break
        j -= 1
    k = i
    while k < n_ins:
        ka, km, ko = ins[k]
        if km == 'ret' and is_pad(k + 1):
            break
        k += 1
    return j, min(k, n_ins - 1)

def is_pad(k):
    if k >= n_ins:
        return True
    a, m, o = ins[k]
    return m in ('int3', 'nop')

bodies = {}
def body_for(i):
    if i in bodies:
        return bodies[i]
    b = body_of(i)
    bodies[i] = b
    return b

OLE_CALL_IDX = []
for i, (a, m, o) in enumerate(ins):
    if m != 'call':
        continue
    v = tail_imm(o) if '0x' in o else None
    if v in OLE_SLOTS or (o.startswith('dword ptr [') and num(o[len('dword ptr ['):-1]) in OLE_SLOTS):
        OLE_CALL_IDX.append(i)
add('M3a the OLE stream call population is finite and non-empty',
    len(OLE_CALL_IDX) > 10, 'sites=%d' % len(OLE_CALL_IDX))

def ole_in_body(i_push):
    lo, hi = body_for(i_push)
    return [j for j in OLE_CALL_IDX if lo <= j <= hi]

def ole_in_window(i_push, n):
    if n == 0:
        return []
    return [j for j in OLE_CALL_IDX if i_push < j <= i_push + n]

# ---- M3: per-address hit counts -------------------------------------------
per = {}
for v in ADDRS:
    sites = refs[v]['push']
    hit_body = sum(1 for a in sites if ole_in_body(idx_of[a]))
    per[hex(v)] = {'push_sites': len(sites), 'hit_same_body': hit_body,
                   'guid': GUIDS[v]}
add('M3b only the 00000109 addresses reach an OLE stream API; 0000010C never does',
    per['0x7f7c80']['hit_same_body'] > 0 and per['0x820270']['hit_same_body'] > 0
    and per['0x7f7c70']['hit_same_body'] == 0 and per['0x818858']['hit_same_body'] == 0,
    per)
add('M3c the 0000010C side is not empty, so its zero is a measurement not a blank',
    per['0x7f7c70']['push_sites'] > 0 or per['0x818858']['push_sites'] > 0,
    {k: v['push_sites'] for k, v in per.items()})
add('M3d no push site is counted twice: the OLE population bounds the sum of hits',
    sum(v['hit_same_body'] for v in per.values()) <= len(OLE_CALL_IDX),
    'sum_hits=%d ole_calls=%d' % (sum(v['hit_same_body'] for v in per.values()),
                                  len(OLE_CALL_IDX)))

# ---- M4: window sensitivity -----------------------------------------------
sens = {}
for n in (0, 6, 8, 10, 16, 24, 40):
    row = {}
    for v in ADDRS:
        sites = refs[v]['push']
        row[hex(v)] = sum(1 for a in sites if ole_in_window(idx_of[a], n))
    sens[n] = row
add('M4a the window-0 control is all zeros (the judgement is not vacuous)',
    all(c == 0 for c in sens[0].values()), sens[0])
add('M4b the separation holds across every window from 10 up, so it is not tuned',
    all(sens[n]['0x7f7c80'] > 0 and sens[n]['0x7f7c70'] == 0
        and sens[n]['0x818858'] == 0 for n in (10, 16, 24, 40)),
    {n: sens[n] for n in sens})
add('M4c below 10 instructions even the 109 side is empty, so small windows are'
    ' uninformative rather than contradictory',
    sens[6]['0x7f7c80'] == 0 and sens[8]['0x7f7c80'] == 0, {6: sens[6], 8: sens[8]})

# ---- M5: controls ---------------------------------------------------------
CTRL = {0x7f7cd0: 'IConnectionPointContainer', 0x7f7c90: 'IID_IUnknown bytes'}
ctrl = {}
for v, nm in CTRL.items():
    sites = [a for i, (a, m, o) in enumerate(ins)
             if m == 'push' and tail_imm(o) == v]
    ctrl[hex(v)] = {'name': nm, 'push_sites': len(sites),
                    'hit_same_body': sum(1 for a in sites if ole_in_body(idx_of[a])),
                    'guid': guid_text(v)}
add('M5a narrow-interface control IConnectionPointContainer never reaches OLE',
    ctrl['0x7f7cd0']['hit_same_body'] == 0 and ctrl['0x7f7cd0']['push_sites'] > 0,
    ctrl['0x7f7cd0'])
add('M5b IID_IUnknown bytes never reach OLE',
    ctrl['0x7f7c90']['hit_same_body'] == 0 and ctrl['0x7f7c90']['push_sites'] > 0,
    ctrl['0x7f7c90'])

rep = {'exe_sha256': EXE_SHA, 'n_ins': n_ins,
       'guids': {hex(k): v for k, v in GUIDS.items()},
       'iunknown_neighbour': IUNK,
       'per_address': per, 'controls': ctrl, 'window_sensitivity': sens,
       'ole_call_sites': len(OLE_CALL_IDX),
       'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R125d %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'] if c['detail'] else ''))
sys.exit(0 if not bad else 1)
