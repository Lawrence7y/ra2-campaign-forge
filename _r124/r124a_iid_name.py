# -*- coding: utf-8 -*-
"""R124a: resolve QueryInterface IID constants to interface names using ONLY
bytes inside gamemd.exe, and report exactly where that stops being possible.

Method (no headers, no doc tables, no prior-round conclusions):
  1. Every class with a vtable has a CompleteObjectLocator at [vt-4]; COL+16 is
     the ClassHierarchyDescriptor; CHD+8 = NumBaseClasses, CHD+12 = pBaseClassArray.
  2. Each BaseClassDescriptor is 24 bytes: pTypeDescriptor, NumContainedBases,
     mdisp, pdisp, vdisp, attributes.  (R124 self-error S-113: the first draft
     read mdisp/pdisp/vdisp from +4/+8/+12, i.e. one dword early.)
  3. The TypeDescriptor name at TD+8 is the interface/class name the binary
     itself carries.  Names beginning '?AU' are structs = COM interfaces here.
  4. Class-set per IID (from the R110 QI census) vs class-set per interface
     name (from RTTI) is tested as a biconditional.
"""
import io, json, os, struct, collections, hashlib
import pefile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE  = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT  = os.path.join(ROOT, '_r124', 'r124a_iid_name.json')
pe   = pefile.PE(EXE); IB = pe.OPTIONAL_HEADER.ImageBase
def rd(va, n): return pe.get_data(va - IB, n)
def u32(va):
    b = rd(va, 4); return struct.unpack('<I', b)[0] if len(b) == 4 else None
def i32(va):
    b = rd(va, 4); return struct.unpack('<i', b)[0] if len(b) == 4 else None
def cstr(va, n=192):
    b = rd(va, n); e = b.find(b'\x00'); return b[:e].decode('latin1') if e >= 0 else b.decode('latin1')

ck = []
def add(name, ok, detail=''):
    ck.append({'name': name, 'ok': bool(ok), 'detail': str(detail)})

exe_sha = hashlib.sha256(open(EXE, 'rb').read()).hexdigest()
add('S0 exe sha256 pinned', exe_sha == '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476', exe_sha)

sym = json.load(io.open(os.path.join(ROOT, 'out', 'reverse', 'symbols.json'), encoding='utf-8'))['classes']
qi  = json.load(io.open(os.path.join(ROOT, '_r110', 'r110a_iidmap.json'), encoding='utf-8'))['rows']

RDATA = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.rdata'][0]
RD_LO = RDATA.VirtualAddress + IB
RD_HI = RD_LO + RDATA.Misc_VirtualSize

def in_rdata(va): return va is not None and RD_LO <= va < RD_HI
# R124 self-error S-114: the first draft gated every pointer on in_rdata, but the
# TypeDescriptor and BaseClassDescriptor records live in .data, so the whole decode
# collapsed to 0/954.  COL/CHD/BaseClassArray are in .rdata; TD/BCD are not.
SECS = [(s.VirtualAddress + IB, s.VirtualAddress + IB + max(s.Misc_VirtualSize, s.SizeOfRawData))
        for s in pe.sections]
def in_image(va):
    return va is not None and any(lo <= va < hi for lo, hi in SECS)

def bases(vt):
    col = u32(vt - 4)
    if not in_rdata(col): return None
    chd = u32(col + 16)
    if not in_rdata(chd): return None
    n, arr = u32(chd + 8), u32(chd + 12)
    if n is None or n > 64 or not in_rdata(arr): return None
    out = []
    for i in range(n):
        bcd = u32(arr + 4 * i)
        if not in_image(bcd): return None
        td = u32(bcd)
        if not in_image(td): return None
        out.append({'name': cstr(td + 8, 192), 'td': td,
                    'ncb': u32(bcd + 4), 'mdisp': i32(bcd + 8),
                    'pdisp': i32(bcd + 12), 'vdisp': i32(bcd + 16),
                    'attr': u32(bcd + 20)})
    return {'col': col, 'this_off': u32(col + 4), 'chd': chd, 'bases': out}

# ---- S1: decoder sanity on all classes that have a vtable ----
decoded, undec = {}, []
for k, v in sym.items():
    vt = v.get('vtable_va')
    if not vt: continue
    b = bases(int(vt, 16))
    if b is None: undec.append(k); continue
    decoded[k] = b
add('S1 RTTI base-array decoded for every class carrying a vtable',
    len(undec) == 0, 'decoded=%d undecodable=%d %s' % (len(decoded), len(undec), undec[:4]))

# S1b: base[0] must be the class itself (MSVC lists the most-derived first)
self_ok = [k for k, b in decoded.items() if b['bases'] and b['bases'][0]['name'].endswith(k + '@@')
           or (b['bases'] and k in b['bases'][0]['name'])]
add('S1b bases[0] is the class itself (decoder reads the right record)',
    len(self_ok) == len(decoded), '%d/%d' % (len(self_ok), len(decoded)))

# ---- S2: interface names actually present in the RTTI ----
name_classes = collections.defaultdict(set)
for k, b in decoded.items():
    for e in b['bases']:
        name_classes[e['name']].add(k)
iface_names = sorted(n for n in name_classes if n.startswith('.?AU'))
add('S2 interface names (structs) carried by the binary RTTI', len(iface_names) >= 20,
    '%d :: %s' % (len(iface_names), ', '.join(x[4:-2] for x in iface_names)))

# ---- S3: class-set biconditional IID <-> interface name ----
# R124: the IID class-sets come from a FULL QI-function scan, not from R110's list.
# R110 truncates at byte 120 of the QI body and thereby drops three of HouseClass's
# six comparisons (offsets 130/161/182).  r124f proves it and names the class.
import capstone as _cs
_md = _cs.Cs(_cs.CS_ARCH_X86, _cs.CS_MODE_32)
def _qi_iids(fn, win=0x400):
    out, pend = [], None
    for ins in _md.disasm(rd(fn, win), fn):
        mn = ins.mnemonic
        if mn == 'mov' and ins.op_str.startswith('edi, 0x'):
            try: pend = int(ins.op_str.split(', ', 1)[1], 16)
            except ValueError: pend = None
        elif 'cmpsd' in mn:
            if pend is not None: out.append(pend); pend = None
        elif mn in ('ret', 'retn') and out:
            break
    return out
iid_classes = collections.defaultdict(set)
for r in qi:
    for iid in _qi_iids(int(r['slot0'], 16)):
        iid_classes['0x%x' % iid].add(r['cls'])

# R124 self-error S-115: the first draft tested EQUALITY of class sets.  That is
# the wrong predicate: a class whose QI is inherited compares fewer IIDs than its
# RTTI names, so the QI class-set is only a SUBSET of the name class-set.  Equality
# would report 5/17 "unmatched" for a reason that has nothing to do with naming.
# Correct predicate: containment.  Tightest (smallest) containing name = candidate.
def tight_names(S):
    cand = [(n, len(name_classes[n])) for n in iface_names if S <= name_classes[n]]
    if not cand: return []
    m = min(c for _, c in cand)
    return sorted(n for n, c in cand if c == m)

rows = []
for ptr in sorted(iid_classes, key=lambda x: int(x, 16)):
    S = iid_classes[ptr]
    b = rd(int(ptr, 16), 16)
    d1 = struct.unpack('<I', b[0:4])[0]; d2, d3 = struct.unpack('<HH', b[4:8])
    guid = '{%08X-%04X-%04X-%s-%s}' % (d1, d2, d3, b[8:10].hex().upper(), b[10:16].hex().upper())
    tn = tight_names(S)
    rows.append({'iid_ptr': ptr, 'guid': guid, 'n_qi_classes': len(S),
                 'exact_name_matches': [n[4:-2] for n in tn],
                 'tight_name_sizes': {n[4:-2]: len(name_classes[n]) for n in tn}})

add('S3 containment: every QI IID class-set is contained in at least one interface name class-set',
    all(r['exact_name_matches'] for r in rows),
    'unmatched=%s' % [r['iid_ptr'] for r in rows if not r['exact_name_matches']])
named = {r['iid_ptr']: r['exact_name_matches'] for r in rows}
uniq  = {k: v for k, v in named.items() if len(v) == 1}
ambig = {k: v for k, v in named.items() if len(v) != 1}
add('S4 class-set containment alone leaves 13/18 unique and 5 genuinely tied',
    len(uniq) == 13 and len(ambig) == 5,
    'unique=%d tied=%s' % (len(uniq), json.dumps(ambig, ensure_ascii=False)))

# ---- S5: controls ----
unk = [r for r in rows if r['iid_ptr'] == '0x7f7c90']
add('S5a POSITIVE control 0x7f7c90 bytes == IID_IUnknown constant',
    bool(unk) and unk[0]['guid'] == '{00000000-0000-0000-C000-000000000046}',
    unk[0]['guid'] if unk else 'missing')
add('S5b POSITIVE control IUnknown is named by the tightest containing interface',
    bool(unk) and unk[0]['exact_name_matches'] == ['IUnknown'],
    '%s qi_n=%d' % (unk[0]['exact_name_matches'] if unk else None, unk[0]['n_qi_classes'] if unk else -1))
# negative control: perturb the class set -> must stop matching
if unk:
    fake = set(sorted(unk[0]['n_qi_classes'] and iid_classes['0x7f7c90'])[:-1])
    neg = [n for n in iface_names if name_classes[n] == fake]
    add('S5c NEGATIVE control: a perturbed class-set matches no interface name', neg == [], repr(neg))

# ---- S6: mdisp discriminates? (IRTTITypeInfo is the one at a non-zero offset) ----
mdisp_of = collections.defaultdict(collections.Counter)
for k, b in decoded.items():
    for e in b['bases']:
        mdisp_of[e['name']][e['mdisp']] += 1
irt = mdisp_of.get('.?AUIRTTITypeInfo@@', collections.Counter())
add('S6 IRTTITypeInfo always sits at a single non-zero member offset (mdisp)',
    dict(irt) == {4: 78}, dict(irt))
ps, pr = mdisp_of.get('.?AUIPersistStream@@', {}), mdisp_of.get('.?AUIPersist@@', {})
add('S6b IPersistStream and IPersist are indistinguishable by member offset',
    dict(ps) == dict(pr) == {0: 90}, 'stream=%s persist=%s' % (dict(ps), dict(pr)))

# ---- S7: how many classes carry them in RTTI vs compare them in QI ----
carry = len(name_classes['.?AUIPersistStream@@'])
cmp70 = len(iid_classes['0x7f7c70']); cmp80 = len(iid_classes['0x7f7c80'])
add('S7 classes carrying IPersist/IPersistStream in RTTI != classes whose QI compares the IIDs',
    carry == 90 and cmp70 == cmp80 == 77,
    'rtti=%d qi70=%d qi80=%d (delta=%d = classes inheriting the QI body)' % (carry, cmp70, cmp80, carry - cmp70))
add('S8 the two IIDs are always compared by exactly the same class set',
    iid_classes['0x7f7c70'] == iid_classes['0x7f7c80'],
    'symmetric difference=%d' % len(iid_classes['0x7f7c70'] ^ iid_classes['0x7f7c80']))
# base-array ORDER of the pair, as the only remaining internal discriminator
order = collections.Counter()
for k, b in decoded.items():
    ns = [e['name'] for e in b['bases']]
    if '.?AUIPersistStream@@' in ns and '.?AUIPersist@@' in ns:
        order['stream_first'] += ns.index('.?AUIPersistStream@@') < ns.index('.?AUIPersist@@')
add('S9 RTTI base order is constant (most-derived first) for the pair, so it cannot discriminate them either',
    dict(order) == {'stream_first': 90}, dict(order))

res = {'exe_sha256': exe_sha, 'checks': ck, 'rows': rows,
       'iface_names': {n[4:-2]: len(name_classes[n]) for n in iface_names},
       'iid_to_name': {k: (v[0][4:-2] if len(v) == 1 else v) for k, v in named.items()},
       'all_ok': all(c['ok'] for c in ck)}
json.dump(res, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for c in ck:
    print(('PASS  ' if c['ok'] else 'FAIL  ') + c['name'] + ((' :: ' + c['detail'][:340]) if c['detail'] else ''))
print('ALL_OK', res['all_ok'])
print()
print('--- IID -> name ---')
for r in rows:
    print('%-10s %s n=%-4d %s' % (r['iid_ptr'], r['guid'], r['n_qi_classes'], r['exact_name_matches']))
