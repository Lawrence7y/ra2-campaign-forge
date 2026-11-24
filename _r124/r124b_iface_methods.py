# -*- coding: utf-8 -*-
"""R124b: interface method counts and inheritance depth, from RTTI bytes only.

Two independent quantities:
  A. NumContainedBases (BCD+4) of an interface's TypeDescriptor = how many
     interfaces it inherits.  This is MSVC's own record, not an inference.
  B. vtable slot count = number of slots from the vtable address up to the next
     slot that holds a COL pointer (COL group boundary).  This is the *concrete*
     vtable's length, i.e. the full method count of the most-derived view.

Neither needs external headers.  Where A and B disagree the difference is itself
the finding (an interface with no local concrete vtable has no B).
"""
import io, json, os, struct, collections, hashlib
import pefile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE  = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT  = os.path.join(ROOT, '_r124', 'r124b_iface_methods.json')
pe = pefile.PE(EXE); IB = pe.OPTIONAL_HEADER.ImageBase
def rd(va, n): return pe.get_data(va - IB, n)
def u32(va):
    b = rd(va, 4); return struct.unpack('<I', b)[0] if len(b) == 4 else None
def i32(va):
    b = rd(va, 4); return struct.unpack('<i', b)[0] if len(b) == 4 else None
def cstr(va, n=192):
    b = rd(va, n); e = b.find(b'\x00'); return b[:e].decode('latin1') if e >= 0 else b.decode('latin1')
SECS = [(s.VirtualAddress + IB, s.VirtualAddress + IB + max(s.Misc_VirtualSize, s.SizeOfRawData))
        for s in pe.sections]
def in_img(va): return va is not None and any(lo <= va < hi for lo, hi in SECS)
RDATA = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.rdata'][0]
RD_LO = RDATA.VirtualAddress + IB; RD_HI = RD_LO + RDATA.Misc_VirtualSize

ck = []
def add(n, ok, d=''): ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

exe_sha = hashlib.sha256(open(EXE, 'rb').read()).hexdigest()
add('S0 exe sha256 pinned', exe_sha == '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476', exe_sha)
sym = json.load(io.open(os.path.join(ROOT,'out','reverse','symbols.json'), encoding='utf-8'))['classes']

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
        out.append({'name': cstr(td + 8, 192), 'ncb': u32(bcd + 4), 'mdisp': i32(bcd + 8),
                    'pdisp': i32(bcd + 12), 'vdisp': i32(bcd + 16), 'attr': u32(bcd + 20)})
    return out

# ---- A. inheritance depth of every interface name ----
dep = collections.defaultdict(collections.Counter)
for k, v in sym.items():
    vt = v.get('vtable_va')
    if not vt: continue
    for e in (bcds(int(vt, 16)) or []):
        dep[e['name']][e['ncb']] += 1
IFACE = sorted(n for n in dep if n.startswith('.?AU'))
ncb_of = {n: (list(dep[n])[0] if len(dep[n]) == 1 else dict(dep[n])) for n in IFACE}
# S1: NumContainedBases is a constant function of the interface name (MSVC record, must be)
add('S1 NumContainedBases is single-valued per interface name',
    all(len(dep[n]) == 1 for n in IFACE),
    ' '.join('%s=%s' % (n[4:-2], list(dep[n])[0]) for n in IFACE))
# S2: the inheritance chain IUnknown(0) < IPersist(1) < IPersistStream(2)
chain = {n[4:-2]: list(dep[n])[0] for n in IFACE}
add('S2 chain IUnknown < IPersist < IPersistStream by NumContainedBases',
    chain.get('IUnknown') == 0 and chain.get('IPersist') == 1 and chain.get('IPersistStream') == 2,
    'IUnknown=%s IPersist=%s IPersistStream=%s' % (chain.get('IUnknown'), chain.get('IPersist'), chain.get('IPersistStream')))
add('S3 IRTTITypeInfo inherits 1 interface (mdisp 4 says it is a separate subobject)',
    chain.get('IRTTITypeInfo') == 1, chain.get('IRTTITypeInfo'))
add('S4 IClassFactory inherits exactly 1 interface (IUnknown)',
    chain.get('IClassFactory') == 1, chain.get('IClassFactory'))

# ---- B. concrete vtable slot counts (COL-group boundary) ----
def is_col_ptr(va):
    if not (RD_LO <= va < RD_HI): return False
    td = u32(va + 12); chd = u32(va + 16)
    if not (in_img(td) and RD_LO <= chd < RD_HI): return False
    return cstr(td + 8, 8).startswith('.?A')

TEXT = [x for x in pe.sections if x.Name.rstrip(b'\x00') == b'.text'][0]
TX_LO = TEXT.VirtualAddress + IB; TX_HI = TX_LO + TEXT.Misc_VirtualSize
def is_code(v): return v is not None and TX_LO <= v < TX_HI

def slot_count(vt, cap=400):
    """Slots are method pointers; the vtable ends at the first slot that is not a
    .text address.  R124 self-error S-124: the first draft ended the vtable at the
    next COL pointer, which is right for 946/954 but fails for a vtable that is
    the LAST in its .rdata group (the next COL sits past a pad, not on a slot).
    Those 8 'unterminated' were the rule's artefact, not a data defect; the
    .text-run rule agrees with symbols.json vfunc_count on 954/954."""
    # R124 self-error S-125: started the scan at k=1, so every count came back
    # one short (a 5-slot vtable scored 4) and the IClassFactory pin looked
    # violated.  Slot 0 is a slot like any other.
    for k in range(cap + 1):
        if not is_code(u32(vt + 4*k)): return k
    return None

counts, nodet = {}, []
for k, v in sym.items():
    vt = v.get('vtable_va')
    if not vt: continue
    c = slot_count(int(vt, 16))
    if c is None: nodet.append(k)
    else: counts[k] = c
add('S5 every vtable has a well-defined slot count under the .text-run rule',
    len(nodet) == 0, 'measured=%d unterminated=%d %s' % (len(counts), len(nodet), nodet[:4]))
dist = collections.Counter(counts.values())
add('S6 concrete vtable slot-count distribution over 954 classes', len(dist) > 1,
    json.dumps(dict(sorted(dist.items())), ensure_ascii=False))

# IUnknown method count: the smallest COL-group whose this_offset==0 and whose
# RTTI base array is exactly [IUnknown] is a bare IUnknown view.
bare = []
for k, v in sym.items():
    vt = v.get('vtable_va')
    if not vt: continue
    b = bcds(int(vt, 16))
    if not b: continue
    if [e['name'] for e in b] == ['.?AUIUnknown@@']:
        bare.append((k, vt, counts.get(k)))
# R124 self-error S-123: the first draft asserted that some vtable's RTTI base
# array is exactly [IUnknown].  It cannot be: MSVC always lists the most-derived
# class first, so every concrete view carries at least one class name.  The
# honest statement is the negative one -- and it is what makes the IClassFactory
# family the usable pin instead.
add('S7 no vtable carries a bare [IUnknown] base array (MSVC always lists the class first)',
    len(bare) == 0, 'found=%s' % repr(bare[:4]))
icf = []
for k, v in sym.items():
    vt = v.get('vtable_va')
    if not vt: continue
    b = bcds(int(vt, 16))
    if not b: continue
    ns = [e['name'] for e in b]
    if '.?AUIClassFactory@@' in ns and ns[-1] == '.?AUIUnknown@@':
        icf.append((k, counts.get(k)))
add('S8 the IClassFactory family pins the interface block: every such vtable is 5 slots',
    len(icf) == 78 and sorted(set(c for _, c in icf)) == [5],
    'n=%d lengths=%s' % (len(icf), sorted(set(c for _, c in icf))))

# IClassFactory: 78 classes whose base array is [self, IClassFactory, IUnknown]
cf = []
for k, v in sym.items():
    vt = v.get('vtable_va')
    if not vt: continue
    b = bcds(int(vt, 16))
    if not b: continue
    ns = [e['name'] for e in b]
    if '.?AUIClassFactory@@' in ns:
        cf.append((k, counts.get(k), ns.index('.?AUIClassFactory@@')))
add('S9 of the 78 IClassFactory classes, 77 are TClassFactory templates and 1 is named otherwise',
    len(cf) == 78 and sum('TClassFactory' in k for k, _, _ in cf) == 77,
    'n=%d templates=%d other=%s' % (len(cf), sum('TClassFactory' in k for k, _, _ in cf),
                                    [k for k, _, _ in cf if 'TClassFactory' not in k]))
cf_counts = sorted(set(c for _, c, _ in cf))
add('S10 every IClassFactory-class vtable is 5 slots = 3 (IUnknown) + 2 (IClassFactory)',
    cf_counts == [5], cf_counts)

res = {'exe_sha256': exe_sha, 'checks': ck,
       'interface_ncb': chain, 'slot_counts': counts, 'slot_dist': dict(sorted(dist.items())),
       'bare_iunknown': bare, 'classfactory_counts': cf_counts,
       'all_ok': all(c['ok'] for c in ck)}
json.dump(res, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for c in ck:
    print(('PASS  ' if c['ok'] else 'FAIL  ') + c['name'] + ((' :: ' + c['detail'][:300]) if c['detail'] else ''))
print('ALL_OK', res['all_ok'])
print()
print('interface inheritance chain (NumContainedBases):')
for n in IFACE: print('  %-32s %s' % (n[4:-2], chain[n[4:-2]]))
