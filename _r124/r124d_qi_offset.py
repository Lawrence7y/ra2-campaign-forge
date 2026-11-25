# -*- coding: utf-8 -*-
"""R124d: name the QueryInterface IID constants that the class-set alone leaves
ambiguous, using the this-pointer ADJUSTMENT each QI branch writes out.

MSVC QI template, one branch per accepted IID:
    mov ecx, 4 ; mov edi, IID ; mov esi, <riid> ; repe cmpsd
    jne  next
    [ test reg,reg ; je .zero ; lea ecx, [reg + OFF] ; jmp .store ]
  .zero:  xor ecx, ecx
  .store: mov [ppv], ecx          <-- OFF is the member displacement, 0 when absent
or simply
    mov [ppv], eax                  <-- offset 0

OFF is the interface subobject's member displacement, which RTTI independently
records as mdisp in the BaseClassDescriptor.  Two independent recordings of the
same layout fact; agreement names the IID.
"""
import io, json, os, struct, collections, hashlib
import pefile, capstone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE  = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT  = os.path.join(ROOT, '_r124', 'r124d_qi_offset.json')
pe = pefile.PE(EXE); IB = pe.OPTIONAL_HEADER.ImageBase
def rd(va, n): return pe.get_data(va - IB, n)
def u32(va):
    b = rd(va, 4); return struct.unpack('<I', b)[0] if len(b) == 4 else None
def i32(va):
    b = rd(va, 4); return struct.unpack('<i', b)[0] if len(b) == 4 else None
def cstr(va, n=192):
    b = rd(va, n); e = b.find(b'\x00'); return b[:e].decode('latin1') if e >= 0 else b.decode('latin1')
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
RDATA = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.rdata'][0]
RD_LO = RDATA.VirtualAddress + IB; RD_HI = RD_LO + RDATA.Misc_VirtualSize
SECS = [(s.VirtualAddress + IB, s.VirtualAddress + IB + max(s.Misc_VirtualSize, s.SizeOfRawData))
        for s in pe.sections]
def in_img(v): return v is not None and any(lo <= v < hi for lo, hi in SECS)

ck = []
def add(n, ok, d=''): ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})
exe_sha = hashlib.sha256(open(EXE, 'rb').read()).hexdigest()
add('S0 exe sha256 pinned', exe_sha == '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476', exe_sha)
sym = json.load(io.open(os.path.join(ROOT,'out','reverse','symbols.json'), encoding='utf-8'))['classes']
qi  = json.load(io.open(os.path.join(ROOT,'_r110','r110a_iidmap.json'), encoding='utf-8'))['rows']

def bcds(vt):
    col = u32(vt - 4)
    if not (RD_LO <= col < RD_HI): return None
    chd = u32(col + 16)
    if not (RD_LO <= chd < RD_HI): return None
    n, arr = u32(chd + 8), u32(chd + 12)
    if n is None or n > 64 or not (RD_LO <= arr < RD_HI): return None
    out = []
    for i in range(n):
        bcd = u32(arr + 4*i)
        if not in_img(bcd): return None
        td = u32(bcd)
        if not in_img(td): return None
        out.append({'name': cstr(td + 8, 192), 'ncb': u32(bcd + 4), 'mdisp': i32(bcd + 8)})
    return {'col': col, 'this_off': u32(col + 4), 'bases': out, 'name': cstr(u32(col + 12) + 8, 192)}

def _addr_of(txt):
    """Parse the displacement of 'reg + N' / 'reg + 0xN' / plain 'reg'."""
    t = txt.strip()
    if '+' not in t: return 0
    tail = t.rsplit('+', 1)[1].strip().rstrip(']').strip()
    try: return int(tail, 0)
    except ValueError: return None

def qi_branches(fn):
    """[(iid_va, adjust)] in compare order."""
    ins = list(md.disasm(rd(fn, 0x400), fn))
    out = []
    for i, x in enumerate(ins):
        if not (x.mnemonic == 'mov' and x.op_str.startswith('edi, 0x')): continue
        iid = int(x.op_str.split(', ', 1)[1], 16)
        w = ins[max(0, i-8):i+6]
        if not (any(y.mnemonic == 'mov' and y.op_str == 'ecx, 4' for y in w) and
                any(y.mnemonic.startswith('repe') for y in w)): continue
        adj = None
        for y in ins[i:i+16]:
            if y.mnemonic == 'lea' and y.op_str.startswith('ecx, [e'):
                inner = y.op_str.split('[', 1)[1].rstrip(']')
                adj = _addr_of(inner)          # R124 S-120: capstone prints small
                break                          # displacements in DECIMAL, so
            if y.mnemonic == 'mov' and y.op_str.startswith('dword ptr [e') and \
               y.op_str.rsplit(', ', 1)[1] in ('eax', 'ecx', 'edx', 'ebx'):
                adj = 0                        # '+ 0x' only matched hex -> 13
                break                          # branches were scored undecidable.
        out.append((iid, adj))
    return out

ev   = collections.defaultdict(collections.Counter)
percls = {}
for r in qi:
    b = qi_branches(int(r['slot0'], 16))
    percls[r['cls']] = b
    for iid, adj in b:
        ev['0x%x' % iid][adj] += 1
und = [(cls, '%x' % i) for cls, v in percls.items() for i, a in v if a is None]
add('S1 the undecodable QI branches are a small, named minority (reported, not hidden)',
    0 < len(und) < 20, 'undecoded=%d %s' % (len(und), und[:6]))

iid_mdisp = {k: v for k, v in ev.items()}
squ = {k: dict(v) for k, v in iid_mdisp.items() if len(set(x for x in v if x is not None)) > 1}
add('S2 no IID has two DIFFERENT decodable offsets (None entries are decode gaps, counted separately)',
    len(squ) == 0, 'contradictory=%s' % json.dumps(squ, ensure_ascii=False))

# ---- RTTI name class-sets ----
name_classes = collections.defaultdict(set)
cls_bases = {}
for k, v in sym.items():
    if not v.get('vtable_va'): continue
    b = bcds(int(v['vtable_va'], 16))
    if not b: continue
    cls_bases[k] = b['bases']
    for e in b['bases']:
        name_classes[e['name']].add(k)
# R124: build the IID class-sets from a FULL function scan, not from R110's list.
# R110 drops every comparison past byte 120 of the QI function (r124f proves it:
# HouseClass compares 6 GUIDs at offsets 47/68/99/130/161/182 and R110 recorded 3),
# which undercounts 0x7f7c70 and 0x7f7c80 by one class each.
def qi_iids_full(fn, win=0x400):
    out = []
    for iid, adj in qi_branches(fn):
        out.append(iid)
    return out
iid_classes = collections.defaultdict(set)
for r in qi:
    for iid in qi_iids_full(int(r['slot0'], 16)):
        iid_classes['0x%x' % iid].add(r['cls'])

# ---- S3: QI offset must be recorded by RTTI for that class (independent records agree)
incons = []
for cls, brs in percls.items():
    bases = cls_bases.get(cls)
    if not bases: continue
    disps = set(e['mdisp'] for e in bases)
    for iid, adj in brs:
        if adj is not None and adj not in disps:
            incons.append((cls, '0x%x' % iid, adj, sorted(disps)))
add('S3 every QI this-offset is a member displacement RTTI records for that class',
    len(incons) == 0, 'violations=%s' % incons[:4])

def resolve(ptr):
    """Two independent records must agree:
       record A (QI code): the this-offset written out for this IID
       record B (RTTI):    the member displacement of that interface subobject
    Order: filter on OFFSET first, then take the TIGHTEST surviving class-set.
    - Filtering by tightest class-set first is wrong (S-121): a tighter name at a
      different offset beats a looser name at the offset the code actually writes.
    - Not taking the tightest afterwards is also wrong (S-122): IUnknown is
      carried by every class, so it is a supertype of any answer, never a rival.
    Restricted to ?AU (struct = COM interface) names; a class at the same offset
    is a different kind of entity, not a competing explanation.
    """
    S = iid_classes[ptr]
    cnt = collections.Counter({k: v for k, v in iid_mdisp[ptr].items() if k is not None})
    if len(cnt) != 1:
        return None, 'offset not decodable/single-valued: %s' % dict(iid_mdisp[ptr])
    off = list(cnt)[0]
    def mdisp_ok(n):
        for cls in S:
            hit = [e for e in cls_bases.get(cls, []) if e['name'] == n]
            if not hit or all(e['mdisp'] != off for e in hit): return False
        return True
    cand = [n for n in name_classes
            if n.startswith('.?AU') and S <= name_classes[n] and mdisp_ok(n)]
    if not cand:
        return None, 'offset %d matches no interface that carries the class-set' % off
    tight = min(len(name_classes[n]) for n in cand)
    win = sorted(n for n in cand if len(name_classes[n]) == tight)
    if len(win) == 1:
        return win[0][4:-2], 'unique'
    return None, ('TIED between %s (identical on both records)'
                  % [w[4:-2] for w in win])

resolved, unresolved = {}, {}
for ptr in sorted(iid_classes, key=lambda x: int(x, 16)):
    nm, why = resolve(ptr)
    if nm: resolved[ptr] = nm
    else: unresolved[ptr] = why
add('S4 offset + class-set resolves groups that the class-set alone left ambiguous',
    'IHouse' in resolved.values() and 'IRTTITypeInfo' in resolved.values()
    and 'IClassFactory' in resolved.values(),
    json.dumps(resolved, ensure_ascii=False))
add('S5 the offset record resolves 12 of 18; the 6 residuals are a specific named set',
    len(resolved) == 12 and len(unresolved) == 6,
    'resolved=%d/%d residual=%s' % (len(resolved), len(iid_classes), json.dumps(unresolved, ensure_ascii=False)))
add('S6a POSITIVE control 0x7f7c90 resolves to IUnknown', resolved.get('0x7f7c90') == 'IUnknown', resolved.get('0x7f7c90'))
add('S6b POSITIVE control 0x7f7ca0 resolves to IClassFactory', resolved.get('0x7f7ca0') == 'IClassFactory', resolved.get('0x7f7ca0'))
add('S6c POSITIVE control 0x7f7cb0/0x7f7cc0/0x7f7ce0 resolve to the three connection-point interfaces',
    [resolved.get(p) for p in ('0x7f7cb0', '0x7f7cc0', '0x7f7ce0')] ==
    ['IEnumConnections', 'IConnectionPoint', 'IEnumConnectionPoints'],
    [resolved.get(p) for p in ('0x7f7cb0', '0x7f7cc0', '0x7f7ce0')])

# negative control: perturb one class's offset evidence and require degradation
_save = dict(iid_classes)
iid_classes['0x7ea768'] = set()          # pretend nothing compares it
nm_neg, _ = resolve('0x7ea768')
iid_classes.clear(); iid_classes.update(_save)
add('S6d NEGATIVE control: emptying the evidence set destroys the resolution',
    nm_neg != 'IHouse', repr(nm_neg))

# ---- S7: the pair that stays undecidable, and why ----
pair = {}
for p in ('0x7f7c70', '0x7f7c80'):
    pair[p] = {'offset': {str(k): v for k, v in iid_mdisp[p].items()},
               'n_classes': len(iid_classes[p]),
               'classset_sha': hashlib.sha256('\n'.join(sorted(iid_classes[p])).encode()).hexdigest()[:16]}
add('S7 IPersist and IPersistStream are identical on every internal record (not separable)',
    pair['0x7f7c70']['offset'].get('0') == 77 and pair['0x7f7c80']['offset'].get('0') == 77
    and pair['0x7f7c70']['classset_sha'] == pair['0x7f7c80']['classset_sha'],
    json.dumps(pair, ensure_ascii=False))
add('S8 both sit at member offset 0 and both are compared by the same 77 classes',
    pair['0x7f7c70']['n_classes'] == pair['0x7f7c80']['n_classes'] == 77,
    '%d / %d (R110 said 76 -- r124f proves the missing class is HouseClass)'
    % (pair['0x7f7c70']['n_classes'], pair['0x7f7c80']['n_classes']))
# their RTTI order is constant, so ordering cannot break the tie either
orders = collections.Counter()
for k in iid_classes['0x7f7c70']:
    ns = [e['name'] for e in cls_bases.get(k, [])]
    if '.?AUIPersistStream@@' in ns and '.?AUIPersist@@' in ns:
        orders[ns.index('.?AUIPersistStream@@') < ns.index('.?AUIPersist@@')] += 1
add('S9 their RTTI base order is constant too (no ordering signal)', dict(orders) == {True: 77}, dict(orders))

res = {'exe_sha256': exe_sha, 'checks': ck, 'resolved': resolved, 'unresolved': unresolved,
       'iid_mdisp': {k: dict(v) for k, v in iid_mdisp.items()}, 'pair': pair,
       'all_ok': all(c['ok'] for c in ck)}
json.dump(res, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for c in ck:
    print(('PASS  ' if c['ok'] else 'FAIL  ') + c['name'] + ((' :: ' + c['detail'][:340]) if c['detail'] else ''))
print('ALL_OK', res['all_ok'])
print()
for p in sorted(resolved, key=lambda x: int(x, 16)): print('  %-10s %-28s %s' % (p, resolved[p], dict(iid_mdisp[p])))
print('  UNRESOLVED:', json.dumps(unresolved, ensure_ascii=False))
